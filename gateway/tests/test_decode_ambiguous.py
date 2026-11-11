"""The reference gateway refuses a decode it would otherwise have to repair (DECODE_AMBIGUOUS).

Doctrine F7-01 (2026-11-02), the rebuild ruling's hazards 1 and 3: a JSON object
with a duplicate key, or a protobuf message with an unknown field number, a
known field carrying a wire type the schema does not use for it, or a
non-repeatable field twice, is refused with the governed code DECODE_AMBIGUOUS
rather than decoded to the last value or to a message missing the member.
Written before the code; the refusal tests were seen failing first (the
clean-event and malformed-JSON tests are controls that passed throughout).
"""

import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import zmeta_proto  # noqa: E402

VALIDATORS_PATH = ROOT / "gateway" / "src" / "validators.py"
spec = importlib.util.spec_from_file_location("zmeta_validators_da", VALIDATORS_PATH)
validators = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validators)
GATEWAY_PATH = ROOT / "gateway" / "src" / "gateway.py"
spec_gw = importlib.util.spec_from_file_location("zmeta_gateway_da", GATEWAY_PATH)
gateway = importlib.util.module_from_spec(spec_gw)
spec_gw.loader.exec_module(gateway)

SCHEMA_VALIDATOR = validators.load_schema(ROOT / "schema" / "zmeta-event-1.0.schema.json")
POLICY = validators.load_policy(ROOT / "policy")


def _event():
    return {
        "zmeta_version": "1.0",
        "event": {
            "event_id": "019c2b5c-c051-70e1-b6aa-34bf14c8b1d1",
            "event_type": "STATE_EVENT",
            "event_subtype": "TRACK_STATE",
            "ts": "2025-01-17T14:30:00Z",
        },
        "source": {"platform_id": "fusion-node-01", "node_role": "GATEWAY", "producer": "fusion-engine"},
        "profile": "L",
        "payload": {"track_id": "track-1", "geo": {"lat": 34.0, "lon": -118.0, "alt_m": 100.0}, "valid_for_ms": 1000},
        "confidence": 0.8,
        "lineage": {"based_on": ["019c2b5c-c051-70e1-b6aa-34bf14c8b1d0"]},
    }


def _run(message, encoding):
    return gateway.process_message(message, SCHEMA_VALIDATOR, POLICY, "L", gateway.TaskDedupeCache(), encoding)


def _codes(outputs):
    """The minted code of each diagnostic: metrics.diagnostic_code on the v1.0 wire
    (the post-lock route: the wire reason_code keeps the legacy SCHEMA_INVALID), else
    the reason_code itself."""
    codes = []
    for out in outputs:
        if out.get("event", {}).get("event_type") != "SYSTEM_EVENT":
            continue
        metrics = out.get("payload", {}).get("metrics", {})
        codes.append(metrics.get("diagnostic_code") or metrics.get("reason_code"))
    return codes


def _wire_codes(outputs):
    return [
        out.get("payload", {}).get("metrics", {}).get("reason_code")
        for out in outputs
        if out.get("event", {}).get("event_type") == "SYSTEM_EVENT"
    ]


class JsonDuplicateKeyTest(unittest.TestCase):
    def test_duplicate_top_level_key_is_refused_with_the_governed_code(self):
        text = json.dumps(_event())
        # two `confidence` members in one object: json.loads would keep 0.1
        text = text.replace('"confidence": 0.8', '"confidence": 0.8, "confidence": 0.1')
        outputs = _run(text.encode("utf-8"), "json")
        self.assertEqual(["DECODE_AMBIGUOUS"], _codes(outputs))
        # the v1.0 wire keeps the legacy decode-stage code; the minted one rides
        # metrics.diagnostic_code (the post-lock route of 2026-08-09)
        self.assertEqual(["SCHEMA_INVALID"], _wire_codes(outputs))
        self.assertEqual("1.0", outputs[0]["zmeta_version"])
        self.assertIn("duplicate key", outputs[0]["payload"]["metrics"]["error"])

    def test_duplicate_nested_key_is_refused(self):
        text = json.dumps(_event())
        text = text.replace('"track_id": "track-1"', '"track_id": "track-1", "track_id": "track-2"')
        outputs = _run(text.encode("utf-8"), "json")
        self.assertEqual(["DECODE_AMBIGUOUS"], _codes(outputs))

    def test_duplicate_key_on_the_auto_lane_is_refused_too(self):
        text = json.dumps(_event()).replace('"profile": "L"', '"profile": "L", "profile": "H"')
        outputs = _run(text.encode("utf-8"), "auto")
        self.assertEqual(["DECODE_AMBIGUOUS"], _codes(outputs))

    def test_malformed_json_stays_schema_invalid_with_no_minted_code(self):
        outputs = _run(b'{"zmeta_version": "1.0", ', "json")
        self.assertEqual(["SCHEMA_INVALID"], _wire_codes(outputs))
        self.assertNotIn("diagnostic_code", outputs[0]["payload"]["metrics"])

    def test_a_clean_event_still_passes(self):
        outputs = _run(json.dumps(_event()).encode("utf-8"), "json")
        self.assertEqual([], _codes(outputs))
        self.assertEqual("STATE_EVENT", outputs[0]["event"]["event_type"])


class ProtobufUnknownFieldTest(unittest.TestCase):
    def test_unknown_top_level_field_is_refused(self):
        wire = zmeta_proto.dumps(_event())
        # field 9, wire type 2 (length-delimited), one byte: the schema has no field 9
        wire += zmeta_proto._field_key(9, zmeta_proto.WIRE_LEN) + b"\x01A"
        with self.assertRaises(ValueError) as ctx:
            zmeta_proto.loads(wire)
        self.assertTrue(getattr(ctx.exception, "decode_ambiguous", False))
        self.assertIn("field 9", str(ctx.exception))
        outputs = _run(wire, "proto")
        self.assertEqual(["DECODE_AMBIGUOUS"], _codes(outputs))

    def test_known_field_with_the_wrong_wire_type_is_refused(self):
        # field 1 is zmeta_version, a string (wire type 2); here it arrives as a varint
        wire = zmeta_proto._field_key(1, zmeta_proto.WIRE_VARINT) + b"\x05" + zmeta_proto.dumps(_event())
        with self.assertRaises(ValueError) as ctx:
            zmeta_proto.loads(wire)
        self.assertTrue(getattr(ctx.exception, "decode_ambiguous", False))
        outputs = _run(wire, "proto")
        self.assertEqual(["DECODE_AMBIGUOUS"], _codes(outputs))

    def test_unknown_field_inside_a_nested_block_is_refused(self):
        event = _event()
        block = zmeta_proto._encode_source(event["source"]) + zmeta_proto._field_key(9, zmeta_proto.WIRE_VARINT) + b"\x01"
        wire = (
            zmeta_proto._field_string(1, "1.0")
            + zmeta_proto._field_message(2, zmeta_proto._encode_event_block(event["event"]))
            + zmeta_proto._field_message(3, block)
            + zmeta_proto._field_bytes(4, zmeta_proto._payload_to_bytes(event["payload"]))
            + zmeta_proto._field_double(5, 0.8)
            + zmeta_proto._field_message(6, zmeta_proto._encode_lineage(event["lineage"]))
            + zmeta_proto._field_string(7, "L")
        )
        with self.assertRaises(ValueError) as ctx:
            zmeta_proto.loads(wire)
        self.assertTrue(getattr(ctx.exception, "decode_ambiguous", False))

    def test_duplicate_key_in_the_protobuf_payload_json_is_refused(self):
        event = _event()
        payload = json.dumps(event["payload"]).replace('"track_id": "track-1"', '"track_id": "track-1", "track_id": "track-2"')
        wire = (
            zmeta_proto._field_string(1, "1.0")
            + zmeta_proto._field_message(2, zmeta_proto._encode_event_block(event["event"]))
            + zmeta_proto._field_message(3, zmeta_proto._encode_source(event["source"]))
            + zmeta_proto._field_bytes(4, payload.encode("utf-8"))
            + zmeta_proto._field_double(5, 0.8)
            + zmeta_proto._field_message(6, zmeta_proto._encode_lineage(event["lineage"]))
            + zmeta_proto._field_string(7, "L")
        )
        with self.assertRaises(ValueError) as ctx:
            zmeta_proto.loads(wire)
        self.assertTrue(getattr(ctx.exception, "decode_ambiguous", False))

    def test_a_repeated_non_repeatable_field_is_refused(self):
        # a second source block, and a repeated scalar: last-wins was the behaviour
        # before the branch (b5eec25 kept the later value)
        event = _event()
        wire = zmeta_proto.dumps(event) + zmeta_proto._field_message(3, zmeta_proto._encode_source({"platform_id": "other"}))
        with self.assertRaises(ValueError) as ctx:
            zmeta_proto.loads(wire)
        self.assertTrue(getattr(ctx.exception, "decode_ambiguous", False))
        self.assertIn("repeated", str(ctx.exception))
        wire2 = zmeta_proto.dumps(event) + zmeta_proto._field_double(5, 0.1)
        with self.assertRaises(ValueError):
            zmeta_proto.loads(wire2)
        outputs = _run(wire2, "proto")
        self.assertEqual(["DECODE_AMBIGUOUS"], _codes(outputs))

    def test_a_repeated_field_inside_a_block_is_refused_and_based_on_stays_repeatable(self):
        event = _event()
        event["lineage"]["based_on"] = ["019c2b5c-c051-70e1-b6aa-34bf14c8b1d0", "019c2b5c-c051-70e1-b6aa-34bf14c8b1d3"]
        decoded = zmeta_proto.loads(zmeta_proto.dumps(event))
        self.assertEqual(2, len(decoded["lineage"]["based_on"]))
        block = zmeta_proto._encode_event_block(event["event"]) + zmeta_proto._field_string(2, "COMMAND_EVENT")
        wire = (
            zmeta_proto._field_string(1, "1.0")
            + zmeta_proto._field_message(2, block)
            + zmeta_proto._field_message(3, zmeta_proto._encode_source(event["source"]))
            + zmeta_proto._field_bytes(4, zmeta_proto._payload_to_bytes(event["payload"]))
            + zmeta_proto._field_double(5, 0.8)
            + zmeta_proto._field_message(6, zmeta_proto._encode_lineage(event["lineage"]))
            + zmeta_proto._field_string(7, "L")
        )
        with self.assertRaises(ValueError) as ctx:
            zmeta_proto.loads(wire)
        self.assertTrue(getattr(ctx.exception, "decode_ambiguous", False))

    def test_an_ambiguous_protobuf_message_on_the_auto_lane_is_reported_as_such(self):
        wire = zmeta_proto.dumps(_event()) + zmeta_proto._field_key(9, zmeta_proto.WIRE_LEN) + b"\x01A"
        outputs = _run(wire, "auto")
        self.assertEqual(["DECODE_AMBIGUOUS"], _codes(outputs))
        self.assertIn("ambiguous protobuf", outputs[0]["payload"]["metrics"]["error"])

    def test_skip_mode_reads_a_payload_with_a_duplicate_key_last_wins(self):
        # the forensic mode reads what the gateway refuses, all of it
        event = _event()
        payload = json.dumps(event["payload"]).replace('"track_id": "track-1"', '"track_id": "track-1", "track_id": "track-2"')
        wire = (
            zmeta_proto._field_string(1, "1.0")
            + zmeta_proto._field_message(2, zmeta_proto._encode_event_block(event["event"]))
            + zmeta_proto._field_message(3, zmeta_proto._encode_source(event["source"]))
            + zmeta_proto._field_bytes(4, payload.encode("utf-8"))
            + zmeta_proto._field_double(5, 0.8)
            + zmeta_proto._field_message(6, zmeta_proto._encode_lineage(event["lineage"]))
            + zmeta_proto._field_string(7, "L")
        )
        decoded = zmeta_proto.loads(wire, unknown_fields="skip")
        self.assertEqual("track-2", decoded["payload"]["track_id"])

    def test_skip_mode_keeps_the_old_behaviour_for_callers_that_ask(self):
        wire = zmeta_proto.dumps(_event()) + zmeta_proto._field_key(9, zmeta_proto.WIRE_LEN) + b"\x01A"
        decoded = zmeta_proto.loads(wire, unknown_fields="skip")
        self.assertEqual("STATE_EVENT", decoded["event"]["event_type"])

    def test_a_clean_protobuf_message_still_passes(self):
        outputs = _run(zmeta_proto.dumps(_event()), "proto")
        self.assertEqual([], _codes(outputs))


class GovernedCodeTest(unittest.TestCase):
    def test_the_code_takes_the_post_lock_route(self):
        import yaml
        codes = yaml.safe_load((ROOT / "policy" / "violation-codes.yaml").read_text(encoding="utf-8"))["violation_codes"]
        entry = [e for e in codes if e["code"] == "DECODE_AMBIGUOUS"]
        self.assertEqual([{"code": "DECODE_AMBIGUOUS", "severity": "fail"}], entry)
        semantics = yaml.safe_load((ROOT / "policy" / "semantics.yaml").read_text(encoding="utf-8"))["semantics"]
        system = semantics["system_event"]
        self.assertIn("DECODE_AMBIGUOUS", json.dumps(system))
        # the v1.0 wire fallback: the locked enum does not grow (adjudication of 2026-08-09)
        self.assertEqual("SCHEMA_INVALID", system["schema_violation_v1_0_wire_fallback"]["DECODE_AMBIGUOUS"])
        v10 = json.loads((ROOT / "schema" / "zmeta-event-1.0.schema.json").read_text(encoding="utf-8"))
        v11 = json.loads((ROOT / "schema" / "zmeta-event-1.1.0.schema.json").read_text(encoding="utf-8"))
        def enum_of(schema):
            found = []
            def walk(node):
                if isinstance(node, dict):
                    if isinstance(node.get("enum"), list) and "ENCODING_UNSUPPORTED" in node["enum"]:
                        found.append(node["enum"])
                    for v in node.values():
                        walk(v)
                elif isinstance(node, list):
                    for v in node:
                        walk(v)
            walk(schema)
            return found
        # finding 16 of the second refuter: the `all` passes on an empty list; the walk
        # must have found the v1.0 enum for the assertion to say anything
        self.assertTrue(enum_of(v10), "the v1.0 reason-code enum was not found")
        self.assertTrue(all("DECODE_AMBIGUOUS" not in e for e in enum_of(v10)), "the locked v1.0 enum must not grow")
        self.assertIn("DECODE_AMBIGUOUS", system["schema_violation_allowed_reason_codes"])
        self.assertTrue(enum_of(v11) and all("DECODE_AMBIGUOUS" in e for e in enum_of(v11)))
        guidance = (ROOT / "tools" / "validation_guidance.yaml").read_text(encoding="utf-8")
        self.assertIn("- code: DECODE_AMBIGUOUS", guidance)


class ThirdPassTest(unittest.TestCase):
    """The second seeded refuter's findings (2026-11-02, pass 2); written before the code."""

    def _tool(self, name):
        spec_t = importlib.util.spec_from_file_location(f"zmeta_tool_{name}", ROOT / "tools" / f"{name}.py")
        module = importlib.util.module_from_spec(spec_t)
        spec_t.loader.exec_module(module)
        return module

    def _duplicate_text(self):
        return json.dumps(_event()).replace('"confidence": 0.8', '"confidence": 0.8, "confidence": 0.1')

    def test_explain_reports_a_duplicate_key_without_a_traceback(self):
        # finding 2: the explainer's second read of the file escaped as a traceback
        import subprocess
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "dup.jsonl"
            path.write_text(self._duplicate_text() + "\n", encoding="utf-8")
            proc = subprocess.run(
                [sys.executable, str(ROOT / "tools" / "explain.py"), "--file", str(path), "--profile", "L"],
                capture_output=True, text=True, cwd=str(ROOT),
            )
        self.assertNotIn("Traceback", proc.stderr + proc.stdout)
        self.assertIn("FAIL DECODE_AMBIGUOUS", proc.stdout)
        self.assertEqual(1, proc.returncode)

    def test_a_truncated_repeated_field_is_reported_as_malformed_first(self):
        # finding 5: the repeat was refused before the bytes were read
        wire = zmeta_proto.dumps(_event()) + zmeta_proto._field_key(7, zmeta_proto.WIRE_LEN) + b"\x09A"
        with self.assertRaises(ValueError) as ctx:
            zmeta_proto.loads(wire)
        self.assertFalse(getattr(ctx.exception, "decode_ambiguous", False), str(ctx.exception))
        self.assertIn("unexpected end", str(ctx.exception))

    def test_a_repeated_field_with_the_wrong_wire_type_is_reported_as_mistyped(self):
        # finding 5: field 5 (confidence, fixed64) arriving a second time as a varint
        wire = zmeta_proto.dumps(_event()) + bytes([0x28, 0x05])
        with self.assertRaises(ValueError) as ctx:
            zmeta_proto.loads(wire)
        self.assertTrue(getattr(ctx.exception, "decode_ambiguous", False))
        self.assertIn("wire type 0", str(ctx.exception))
        self.assertNotIn("repeated", str(ctx.exception))

    def test_a_repeated_field_message_names_the_field_and_its_wire_type(self):
        wire = zmeta_proto.dumps(_event()) + zmeta_proto._field_string(7, "M")
        with self.assertRaises(ValueError) as ctx:
            zmeta_proto.loads(wire)
        self.assertTrue(getattr(ctx.exception, "decode_ambiguous", False))
        self.assertIn("field 7 (wire type 2) repeated in the message", str(ctx.exception))

    def test_a_repeated_block_field_is_reported_the_same_way(self):
        event = _event()
        wire = zmeta_proto.dumps(event) + zmeta_proto._field_message(3, zmeta_proto._encode_source(event["source"]))
        with self.assertRaises(ValueError) as ctx:
            zmeta_proto.loads(wire)
        self.assertIn("field 3 (wire type 2) repeated in the message", str(ctx.exception))
        block = zmeta_proto._encode_source(event["source"]) + zmeta_proto._field_string(1, "other")
        wire = zmeta_proto._field_string(1, "1.0") + zmeta_proto._field_message(3, block)
        with self.assertRaises(ValueError) as ctx:
            zmeta_proto.loads(wire)
        self.assertIn("field 1 (wire type 2) repeated in source", str(ctx.exception))

    def test_udp_sender_refuses_a_duplicate_key_before_a_binary_re_encode(self):
        # finding 11: the sender read last-wins and sent a clean binary message
        udp_sender = self._tool("udp_sender")
        with self.assertRaises(SystemExit) as ctx:
            udp_sender.encode_payload(self._duplicate_text(), "proto")
        self.assertIn("duplicate key", str(ctx.exception))
        # the JSON lane sends the bytes verbatim; the gateway is the decoder there
        self.assertEqual(self._duplicate_text().encode("utf-8"), udp_sender.encode_payload(self._duplicate_text(), "json"))

    def test_replay_refuses_a_duplicate_key_line(self):
        replay = self._tool("replay")
        with self.assertRaises(ValueError) as ctx:
            replay.load_message(self._duplicate_text())
        self.assertTrue(getattr(ctx.exception, "decode_ambiguous", False))
        self.assertIsNone(replay.load_message("{not json"))
        self.assertEqual("STATE_EVENT", replay.load_message(json.dumps(_event()))["event"]["event_type"])

    def test_the_fixture_tool_reports_a_gateway_exception_against_the_expected_code(self):
        # finding 15: an exception out of process_message returned the fixture's
        # expected code before expect_gateway_code was read
        tool = self._tool("validate_encoding_negative")
        fixtures = [
            json.loads(line)
            for line in (ROOT / "conformance" / "encoding-negative" / "gateway-must-fail.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        fixture = [f for f in fixtures if f["name"] == "gateway-json-duplicate-key-refused"][0]
        schema_validator = tool.validators.load_schema(ROOT / "schema" / "zmeta-event.schema.json")
        policy = tool.validators.load_policy(ROOT / "policy")
        contexts = tool.load_contexts(ROOT / "conformance" / "encoding-negative" / "context.jsonl")
        original = tool.gateway.process_message

        def boom(*args, **kwargs):
            raise RuntimeError("gateway crashed")

        tool.gateway.process_message = boom
        try:
            result = tool._evaluate_gateway_fixture(fixture, schema_validator, policy, contexts)
            self.assertEqual("ENCODE_NEGATIVE_GATEWAY_CODE_MISMATCH", result["code"], result)
            self.assertIn("gateway crashed", result["message"])
            plain = dict(fixture)
            plain.pop("expect_gateway_code")
            result = tool._evaluate_gateway_fixture(plain, schema_validator, policy, contexts)
            self.assertEqual("ENCODE_NEGATIVE_DECODE_AMBIGUOUS", result["code"], result)
        finally:
            tool.gateway.process_message = original


class ContractSentenceTest(unittest.TestCase):
    """2026-11-10, on the maintainer's selection: contract 3.5 states the JSON
    duplicate-key rule, and four more reference tools read JSON through the
    refusing reader. Written before the change; the six refusal tests were
    seen failing, and the control passed throughout. The tests for the
    must-fail file of the conformance tool, for a repeat below the top level
    and for a document with a clean sibling were added after the change, and
    so were the checks of the category, of the single FAIL line and of the
    paragraph's place; each fails against a mutant of what it checks."""

    SENTENCES = (
        "A JSON text in which one object repeats a member name, at any depth, does not "
        "decode to one canonical event and is not a valid encoded event.",
        "A decoder that keeps one of the repeated values chooses a reading the text does not state.",
    )

    def _section_3_5(self):
        lines = (ROOT / "spec" / "semantics-contract.md").read_text(encoding="utf-8").splitlines()
        start = next(i for i, line in enumerate(lines) if line.startswith("### 3.5 "))
        end = next(i for i in range(start + 1, len(lines)) if lines[i].startswith("#"))
        return " ".join(" ".join(lines[start:end]).split())

    def _first_line(self, relative):
        return next(line for line in (ROOT / relative).read_text(encoding="utf-8").splitlines() if line.strip())

    def _repeated(self, line, key, wrong):
        """`line` with one top-level member repeated: a wrong value first, the
        shipped value last, so a reader that keeps the last value reads the
        shipped text."""
        shipped = json.loads(line)
        self.assertIn(key, shipped)
        self.assertNotEqual(wrong, shipped[key])
        return "{" + json.dumps(key) + ": " + json.dumps(wrong) + ", " + line.strip()[1:]

    def _repeated_at_depth(self, line):
        """`line` with the innermost `event_id` repeated, a wrong value first."""
        self.assertIn('"event_id"', line)
        repeated = line.replace('"event_id"', '"event_id": "00000000-0000-7000-8000-000000000000", "event_id"', 1)
        self.assertEqual(json.loads(line), json.loads(repeated))
        self.assertFalse(repeated.lstrip().startswith('{"event_id"'))
        return repeated

    def _clean_event_line(self):
        # A shipped Profile L example that the tools accept as it stands.
        return self._first_line("examples/zmeta-profile-L-examples.jsonl")

    def _repeating_event_line(self):
        return self._repeated(self._clean_event_line(), "zmeta_version", "9.9")

    def _tool_run(self, tool, *argv):
        import subprocess

        return subprocess.run(
            [sys.executable, str(ROOT / "tools" / tool), *argv], capture_output=True, text=True, cwd=str(ROOT)
        )

    def _validate_examples_file(self, path):
        import contextlib
        import io

        spec_t = importlib.util.spec_from_file_location(
            "zmeta_tool_validate_examples_da", ROOT / "tools" / "validate_examples.py"
        )
        tool = importlib.util.module_from_spec(spec_t)
        spec_t.loader.exec_module(tool)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            result = tool.validate_file(path, "L", SCHEMA_VALIDATOR, POLICY, POLICY.get("violation_severities", {}), False)
        return result, out.getvalue()

    def test_the_contract_states_the_rule_the_reference_decoder_applies(self):
        # The two cannot drift apart silently: the contract carries the
        # sentences, and the reference decoder refuses a repeat at depth two.
        section = self._section_3_5()
        for sentence in self.SENTENCES:
            self.assertIn(sentence, section)
        # between the validity paragraph and the paragraph on encoding versions
        self.assertIn(
            "are not semantic. " + " ".join(self.SENTENCES) + " Encoding versions, such as", section
        )
        text = json.dumps(_event()).replace('"lat": 34.0', '"lat": 34.0, "lat": 35.0')
        self.assertEqual(["DECODE_AMBIGUOUS"], _codes(_run(text.encode("utf-8"), "json")))

    def test_check_compat_refuses_a_line_that_repeats_a_member(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "repeat.jsonl"
            path.write_text(self._repeating_event_line() + "\n", encoding="utf-8")
            proc = self._tool_run("check_compat.py", "--json", "--profile", "L", str(path))
        self.assertNotIn("Traceback", proc.stderr + proc.stdout)
        self.assertEqual(1, proc.returncode, proc.stdout[:400])
        issues = json.loads(proc.stdout)["issues"]
        self.assertEqual(["decode"], [issue["category"] for issue in issues])
        self.assertIn("DECODE_AMBIGUOUS", issues[0]["message"])
        self.assertIn("duplicate key", issues[0]["message"])

    def test_check_compat_refuses_a_whole_document_for_one_repeat(self):
        # A .json document is one JSON text. With a clean item beside the
        # repeating one, the document is still refused whole, at line 1.
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "siblings.json"
            path.write_text(
                "[\n" + self._clean_event_line() + ",\n" + self._repeating_event_line() + "\n]\n", encoding="utf-8"
            )
            proc = self._tool_run("check_compat.py", "--json", "--profile", "L", str(path))
        self.assertNotIn("Traceback", proc.stderr + proc.stdout)
        self.assertEqual(1, proc.returncode, proc.stdout[:400])
        report = json.loads(proc.stdout)
        self.assertEqual(0, report["events"])
        self.assertEqual([("decode", 1)], [(issue["category"], issue["line"]) for issue in report["issues"]])

    def test_each_tool_refuses_a_repeat_below_the_top_level(self):
        # The contract says "at any depth". The repeated member sits inside
        # the inner `event` object: depth two in an event line, three in a fixture.
        import tempfile

        event_line = self._repeated_at_depth(self._clean_event_line())
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "depth.jsonl"
            path.write_text(event_line + "\n", encoding="utf-8")
            with self.subTest(tool="check_compat"):
                proc = self._tool_run("check_compat.py", "--json", "--profile", "L", str(path))
                self.assertEqual(1, proc.returncode, proc.stdout[:400])
                self.assertEqual(["decode"], [issue["category"] for issue in json.loads(proc.stdout)["issues"]])
            with self.subTest(tool="validate_examples"):
                result, printed = self._validate_examples_file(path)
                self.assertEqual({"total": 1, "passed": 0, "failed": 1, "warnings": 0}, result, printed)
                self.assertIn("FAIL DECODE_AMBIGUOUS", printed)
            with self.subTest(tool="validate_bad_events"):
                fixture = Path(tmp) / "bad-depth.jsonl"
                fixture.write_text(
                    self._repeated_at_depth(self._first_line("conformance/bad-events/must-fail.jsonl")) + "\n",
                    encoding="utf-8",
                )
                proc = self._tool_run("validate_bad_events.py", "--must-fail", str(fixture))
                self.assertNotIn("Traceback", proc.stderr + proc.stdout)
                self.assertEqual(1, proc.returncode, proc.stdout[:400])
                self.assertIn("DECODE_AMBIGUOUS", proc.stdout)
            with self.subTest(tool="validate_conformance"):
                fixture = Path(tmp) / "pass-depth.jsonl"
                fixture.write_text(
                    self._repeated_at_depth(self._first_line("conformance/must-pass.jsonl")) + "\n", encoding="utf-8"
                )
                proc = self._tool_run("validate_conformance.py", "--pass-file", str(fixture))
                self.assertNotIn("Traceback", proc.stderr + proc.stdout)
                self.assertEqual(1, proc.returncode, proc.stdout[:400])
                self.assertIn("DECODE_AMBIGUOUS", proc.stdout)

    def test_check_compat_refuses_a_json_document_that_repeats_a_member(self):
        # A .json file takes the tool's whole-document path, which parsed the
        # text and wrote each item out again before the per-item read.
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "repeat.json"
            path.write_text("[\n" + self._repeating_event_line() + "\n]\n", encoding="utf-8")
            proc = self._tool_run("check_compat.py", "--json", "--profile", "L", str(path))
        self.assertNotIn("Traceback", proc.stderr + proc.stdout)
        self.assertEqual(1, proc.returncode, proc.stdout[:400])
        messages = [issue["message"] for issue in json.loads(proc.stdout)["issues"]]
        self.assertTrue(any("DECODE_AMBIGUOUS" in m and "duplicate key" in m for m in messages), messages)

    def test_validate_examples_refuses_a_line_that_repeats_a_member(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "repeat.jsonl"
            path.write_text(self._repeating_event_line() + "\n", encoding="utf-8")
            result, printed = self._validate_examples_file(path)
        self.assertEqual({"total": 1, "passed": 0, "failed": 1, "warnings": 0}, result, printed)
        self.assertIn("FAIL DECODE_AMBIGUOUS", printed)

    def test_validate_bad_events_refuses_a_fixture_line_that_repeats_a_member(self):
        import tempfile

        line = self._repeated(self._first_line("conformance/bad-events/must-fail.jsonl"), "expect_code", "NOT_A_CODE")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "repeat.jsonl"
            path.write_text(line + "\n", encoding="utf-8")
            proc = self._tool_run("validate_bad_events.py", "--must-fail", str(path))
        self.assertNotIn("Traceback", proc.stderr + proc.stdout)
        self.assertEqual(1, proc.returncode, proc.stdout[:400])
        self.assertIn("DECODE_AMBIGUOUS", proc.stdout)
        self.assertIn("duplicate key", proc.stdout)
        self.assertEqual(1, sum(1 for line in proc.stdout.splitlines() if line.startswith("FAIL ")), proc.stdout)
        self.assertNotIn("contains no fixtures", proc.stdout)

    def test_validate_conformance_refuses_a_fixture_line_that_repeats_a_member(self):
        import tempfile

        line = self._repeated(self._first_line("conformance/must-pass.jsonl"), "profile", "Z")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "repeat.jsonl"
            path.write_text(line + "\n", encoding="utf-8")
            proc = self._tool_run("validate_conformance.py", "--pass-file", str(path))
        self.assertNotIn("Traceback", proc.stderr + proc.stdout)
        self.assertEqual(1, proc.returncode, proc.stdout[:400])
        self.assertIn("DECODE_AMBIGUOUS", proc.stdout)
        self.assertIn("duplicate key", proc.stdout)
        # the refused file counts once, and is not also reported as empty
        self.assertEqual(1, sum(1 for line in proc.stdout.splitlines() if line.startswith("FAIL ")), proc.stdout)
        self.assertNotIn("contains no fixtures", proc.stdout)

    def test_validate_conformance_refuses_a_must_fail_line_that_repeats_a_member(self):
        import tempfile

        line = self._repeated(self._first_line("conformance/must-fail.jsonl"), "expect_code", "NOT_A_CODE")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "repeat.jsonl"
            path.write_text(line + "\n", encoding="utf-8")
            proc = self._tool_run("validate_conformance.py", "--fail-file", str(path))
        self.assertNotIn("Traceback", proc.stderr + proc.stdout)
        self.assertEqual(1, proc.returncode, proc.stdout[:400])
        self.assertIn("DECODE_AMBIGUOUS", proc.stdout)
        self.assertIn("duplicate key", proc.stdout)
        self.assertEqual(1, sum(1 for line in proc.stdout.splitlines() if line.startswith("FAIL ")), proc.stdout)
        self.assertNotIn("contains no fixtures", proc.stdout)

    def test_the_four_tools_accept_the_same_texts_without_the_repeat(self):
        # The controls: each input above, without its repeated member, is
        # accepted, so each refusal belongs to the repeat and to nothing else.
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            clean = Path(tmp) / "clean.jsonl"
            clean.write_text(self._clean_event_line() + "\n", encoding="utf-8")
            proc = self._tool_run("check_compat.py", "--json", "--profile", "L", str(clean))
            self.assertEqual(0, proc.returncode, proc.stdout[:400])
            self.assertEqual([], json.loads(proc.stdout)["issues"])

            document = Path(tmp) / "clean.json"
            document.write_text("[\n" + self._clean_event_line() + "\n]\n", encoding="utf-8")
            self.assertEqual(0, self._tool_run("check_compat.py", "--json", "--profile", "L", str(document)).returncode)

            result, printed = self._validate_examples_file(clean)
            self.assertEqual({"total": 1, "passed": 1, "failed": 0, "warnings": 0}, result, printed)

            bad = Path(tmp) / "bad.jsonl"
            bad.write_text(self._first_line("conformance/bad-events/must-fail.jsonl") + "\n", encoding="utf-8")
            self.assertEqual(0, self._tool_run("validate_bad_events.py", "--must-fail", str(bad)).returncode)

            good = Path(tmp) / "pass.jsonl"
            good.write_text(self._first_line("conformance/must-pass.jsonl") + "\n", encoding="utf-8")
            self.assertEqual(0, self._tool_run("validate_conformance.py", "--pass-file", str(good)).returncode)

            must_fail = Path(tmp) / "fail.jsonl"
            must_fail.write_text(self._first_line("conformance/must-fail.jsonl") + "\n", encoding="utf-8")
            self.assertEqual(0, self._tool_run("validate_conformance.py", "--fail-file", str(must_fail)).returncode)


if __name__ == "__main__":
    unittest.main()
