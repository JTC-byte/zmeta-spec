"""The reference gateway refuses a decode it would otherwise have to repair (DECODE_AMBIGUOUS).

Doctrine F7-01 (2026-11-02), the rebuild ruling's hazards 1 and 3: a JSON object
with a duplicate key, or a protobuf message with an unknown field number or a
known field carrying a wire type the schema does not use for it, is refused
with the governed code DECODE_AMBIGUOUS rather than decoded to the last value
or to a message missing the member. Written before the code; seen failing first.
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
        # a second source block, and a repeated scalar: last wins today
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
        self.assertTrue(all("DECODE_AMBIGUOUS" not in e for e in enum_of(v10)), "the locked v1.0 enum must not grow")
        self.assertTrue(enum_of(v11) and all("DECODE_AMBIGUOUS" in e for e in enum_of(v11)))
        guidance = (ROOT / "tools" / "validation_guidance.yaml").read_text(encoding="utf-8")
        self.assertIn("- code: DECODE_AMBIGUOUS", guidance)


if __name__ == "__main__":
    unittest.main()
