"""Compact encoding fail-closed tests (R1-11 R11-01).

The compact wire has no zmeta_version key and enumerated field tables, so a
lossy encode silently relabels events as locked-v1.0 and destroys fields
(witnessed live: geo.error_ellipse_m). The honesty rule is refusal over
reduction: dumps()/verify_representable must reject any event that does not
round-trip byte-identically, the gateway compact egress must replace the
event with an ENCODING_UNSUPPORTED diagnostic instead of reducing it, and
that diagnostic must itself be compact-representable and schema/semantics
valid (the GEO_ZERO_FILL_SUSPECTED destroyed-diagnostic lesson).
"""

import importlib.util
import json
import subprocess
import sys
import unittest
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import zmeta_compact  # noqa: E402

VALIDATORS_PATH = ROOT / "gateway" / "src" / "validators.py"
spec_val = importlib.util.spec_from_file_location("zmeta_validators_cfc", VALIDATORS_PATH)
validators = importlib.util.module_from_spec(spec_val)
spec_val.loader.exec_module(validators)

GATEWAY_PATH = ROOT / "gateway" / "src" / "gateway.py"
spec_gw = importlib.util.spec_from_file_location("zmeta_gateway_cfc", GATEWAY_PATH)
gateway = importlib.util.module_from_spec(spec_gw)
spec_gw.loader.exec_module(gateway)


def _load_jsonl(path):
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _v1_1_examples():
    return _load_jsonl(ROOT / "examples" / "zmeta-v1.1-examples.jsonl")


def _all_v1_0_example_events():
    events = []
    for path in sorted((ROOT / "examples").glob("*.jsonl")):
        for event in _load_jsonl(path):
            if event.get("zmeta_version") == "1.0":
                events.append((path.name, event))
    return events


class CompactFailClosedTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.validator = validators.load_schema(ROOT / "schema" / "zmeta-event.schema.json")
        cls.policy = validators.load_policy(ROOT / "policy")

    def test_every_v1_1_example_refuses_compact_encode(self):
        examples = _v1_1_examples()
        self.assertGreaterEqual(len(examples), 13, "v1.1 example corpus shrank")
        for idx, event in enumerate(examples):
            with self.subTest(index=idx, subtype=event["event"].get("event_subtype")):
                with self.assertRaises(zmeta_compact.CompactUnrepresentableError):
                    zmeta_compact.dumps(event)

    def test_v1_0_example_corpus_still_roundtrips(self):
        events = _all_v1_0_example_events()
        self.assertGreaterEqual(len(events), 30, "v1.0 example corpus shrank")
        for name, event in events:
            with self.subTest(corpus=name, event_id=event["event"]["event_id"]):
                restored = zmeta_compact.loads(zmeta_compact.dumps(event))
                self.assertEqual(restored, event)

    def test_refusal_message_names_version_or_lossy_path(self):
        state = next(
            e for e in _v1_1_examples()
            if "error_ellipse_m" in e.get("payload", {}).get("geo", {})
        )
        with self.assertRaises(zmeta_compact.CompactUnrepresentableError) as ctx:
            zmeta_compact.verify_representable(state)
        self.assertIn("1.0", str(ctx.exception))

        lossy = {
            "zmeta_version": "1.0",
            "event": {
                "event_id": "019c2b5d-4cd9-770e-b02d-55d71e516898",
                "event_type": "STATE_EVENT",
                "event_subtype": "TRACK_STATE",
                "ts": "2025-01-17T14:31:05Z",
            },
            "source": {
                "platform_id": "fusion-node-01",
                "node_role": "FUSION",
                "producer": "fusion-engine",
            },
            "payload": {
                "track_id": "trk-001",
                "geo": {
                    "lat": 34.05,
                    "lon": -118.24,
                    "alt_m": 120.0,
                    "error_ellipse_m": {"semi_major": 150.0, "semi_minor": 75.0},
                },
            },
        }
        with self.assertRaises(zmeta_compact.CompactUnrepresentableError) as ctx:
            zmeta_compact.verify_representable(lossy)
        self.assertIn("error_ellipse_m", str(ctx.exception))
        self.assertIn("dropped", str(ctx.exception))

        # A ts whose canonical epoch-ms formatting differs byte-wise (".000Z")
        # is likewise refused with the exact path named: the wire stores epoch
        # milliseconds and cannot reproduce the original string.
        millis = json.loads(json.dumps(lossy))
        del millis["payload"]["geo"]["error_ellipse_m"]
        millis["event"]["ts"] = "2025-01-17T14:31:05.000Z"
        with self.assertRaises(zmeta_compact.CompactUnrepresentableError) as ctx:
            zmeta_compact.verify_representable(millis)
        self.assertIn("$.event.ts", str(ctx.exception))

    def test_gateway_encode_message_compact_refuses_v1_1(self):
        state = _v1_1_examples()[0]
        with self.assertRaises(zmeta_compact.CompactUnrepresentableError):
            gateway._encode_message(state, "compact")
        # json/cbor/proto remain version-preserving for the same event.
        for encoding in ("json", "cbor", "proto"):
            self.assertTrue(gateway._encode_message(state, encoding))

    def test_encoding_unsupported_diagnostic_survives_the_full_chain(self):
        original = next(
            e for e in _v1_1_examples()
            if "error_ellipse_m" in e.get("payload", {}).get("geo", {})
        )
        diagnostic = gateway.build_violation_event(
            "ENCODING_UNSUPPORTED",
            original=original,
            details={"error": "compact encoding would lose payload.geo.error_ellipse_m"},
            force_schema_violation=True,
        )
        self.assertEqual(diagnostic["event"]["event_subtype"], "SCHEMA_VIOLATION")
        self.assertEqual(
            diagnostic["payload"]["metrics"]["original_event_id"],
            original["event"]["event_id"],
        )
        # The replacement diagnostic must itself be compact-representable...
        zmeta_compact.verify_representable(diagnostic)
        self.assertEqual(
            zmeta_compact.loads(zmeta_compact.dumps(diagnostic)), diagnostic
        )
        # ...and must not be destroyed by outgoing validation.
        self.assertEqual(list(self.validator.iter_errors(diagnostic)), [])
        ok, violations = validators.validate_semantics(
            diagnostic,
            self.policy["semantics"],
            self.policy["violation_severities"],
        )
        self.assertTrue(ok, violations)
        self.assertEqual([], violations)

    def test_command_original_stays_schema_violation_when_forced(self):
        command = {
            "zmeta_version": "1.0",
            "event": {
                "event_id": "019c2b5d-4cd9-770e-b02d-55d63910a2e7",
                "event_type": "COMMAND_EVENT",
                "event_subtype": "GOTO",
                "ts": "2025-01-17T14:31:00Z",
            },
            "source": {
                "platform_id": "comms-node-1",
                "node_role": "GATEWAY",
                "producer": "sensorops",
            },
            "payload": {"task_id": "task-001", "task_type": "GOTO"},
        }
        forced = gateway.build_violation_event(
            "ENCODING_UNSUPPORTED", original=command, force_schema_violation=True
        )
        self.assertEqual(forced["event"]["event_subtype"], "SCHEMA_VIOLATION")
        self.assertEqual(list(self.validator.iter_errors(forced)), [])
        # Default TASK_ACK selection for commands is unchanged for task codes.
        acked = gateway.build_violation_event("TASK_REJECTED", original=command)
        self.assertEqual(acked["event"]["event_subtype"], "TASK_ACK")

    def test_convert_encoding_cli_refuses_v1_1_to_compact(self):
        tmp = ROOT / "pytest-work" / f"compact-refuse-{uuid.uuid4().hex}"
        tmp.mkdir(parents=True, exist_ok=False)
        try:
            src = tmp / "event.json"
            dst = tmp / "event.compact"
            src.write_text(json.dumps(_v1_1_examples()[0]), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "tools" / "convert_encoding.py"),
                    "--from", "json",
                    "--to", "compact",
                    "--input", str(src),
                    "--output", str(dst),
                ],
                capture_output=True,
                text=True,
                cwd=str(ROOT),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("conversion refused", result.stderr)
            self.assertFalse(dst.exists(), "refused conversion must not write output")
        finally:
            import shutil

            shutil.rmtree(tmp, ignore_errors=True)
            try:
                (ROOT / "pytest-work").rmdir()
            except OSError:
                pass


if __name__ == "__main__":
    unittest.main()
