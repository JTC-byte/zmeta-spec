"""Frame-provenance warn + non-finite confidence checks (R1-11 R11-21/R11-04).

Contract 6.4: a canonical bearing SHOULD carry frame provenance. v1.0
tolerates legacy-unlabeled bearings, so warn is the enforcement ceiling —
the check makes assertively-labeled vs legacy-unlabeled machine-visible
without breaking legacy producers. Contract 8.1: jsonschema min/max
comparisons are vacuous against NaN, so non-finite confidence must fail at
the semantics layer.
"""

import importlib.util
import unittest
from pathlib import Path

from zmeta_uuid import uuid7

ROOT = Path(__file__).resolve().parents[2]
VALIDATORS_PATH = ROOT / "gateway" / "src" / "validators.py"
spec = importlib.util.spec_from_file_location("zmeta_validators_bfw", VALIDATORS_PATH)
validators = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validators)


def rf_observation(version="1.0", bearing=None, quality=None):
    payload = {
        "modality": "RF",
        "features": {
            "center_freq_hz": 462600000.0,
            "bandwidth_hz": 0.0,
            "power_dbm": -62.0,
        },
        "quality": {"calibration_state": "UNCALIBRATED"},
    }
    if bearing is not None:
        payload["bearing"] = bearing
    if quality:
        payload["quality"].update(quality)
    return {
        "zmeta_version": version,
        "event": {
            "event_id": str(uuid7()),
            "event_type": "OBSERVATION_EVENT",
            "event_subtype": "RF",
            "ts": "2025-01-17T14:30:00Z",
        },
        "source": {
            "platform_id": "sensor-01",
            "node_role": "EDGE",
            "producer": "rf-sensor-01",
        },
        "payload": payload,
    }


class BearingFrameWarnTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = validators.load_policy(ROOT / "policy")
        cls.severity_map = cls.policy["violation_severities"]

    def semantics(self, event):
        return validators.validate_semantics(
            event, self.policy["semantics"], self.severity_map
        )

    def codes(self, violations):
        return [violation["code"] for violation in violations]

    def test_unlabeled_canonical_bearing_warns_but_is_accepted(self):
        for version in ("1.0", "1.1.0"):
            with self.subTest(version=version):
                event = rf_observation(version=version, bearing={"az_deg": 135.2})
                ok, violations = self.semantics(event)
                self.assertTrue(ok, violations)
                self.assertIn("BEARING_FRAME_UNLABELED", self.codes(violations))
                warn = next(
                    v for v in violations if v["code"] == "BEARING_FRAME_UNLABELED"
                )
                self.assertEqual("warn", warn["severity"])

    def test_quality_channel_provenance_silences_the_warn(self):
        event = rf_observation(
            bearing={"az_deg": 135.2},
            quality={"bearing_frame": "TRUE_NORTH", "heading_source": "GPS_COURSE"},
        )
        ok, violations = self.semantics(event)
        self.assertTrue(ok, violations)
        self.assertNotIn("BEARING_FRAME_UNLABELED", self.codes(violations))

    def test_v1_1_bearing_frame_channel_silences_the_warn(self):
        event = rf_observation(
            version="1.1.0", bearing={"az_deg": 135.2, "frame": "TRUE_NORTH"}
        )
        ok, violations = self.semantics(event)
        self.assertTrue(ok, violations)
        self.assertNotIn("BEARING_FRAME_UNLABELED", self.codes(violations))

    def test_event_without_bearing_never_warns(self):
        ok, violations = self.semantics(rf_observation())
        self.assertTrue(ok, violations)
        self.assertNotIn("BEARING_FRAME_UNLABELED", self.codes(violations))

    def test_shipped_valid_corpora_carry_no_unlabeled_bearings(self):
        # The warn-check's corpus impact was exactly the two teaching
        # examples fixed in this wave; this pins that no shipped valid
        # corpus regresses to an unlabeled canonical bearing.
        import json

        offenders = []
        for path in sorted((ROOT / "examples").glob("*.jsonl")):
            for line_no, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), start=1
            ):
                if not line.strip():
                    continue
                event = json.loads(line)
                _ok, violations = self.semantics(event)
                if "BEARING_FRAME_UNLABELED" in self.codes(violations):
                    offenders.append(f"{path.name}:{line_no}")
        self.assertEqual([], offenders)


class NonFiniteConfidenceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = validators.load_policy(ROOT / "policy")
        cls.severity_map = cls.policy["violation_severities"]

    def semantics(self, event):
        return validators.validate_semantics(
            event, self.policy["semantics"], self.severity_map
        )

    def test_nan_and_inf_confidence_fail(self):
        for bad in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(value=repr(bad)):
                event = rf_observation()
                event["confidence"] = bad
                ok, violations = self.semantics(event)
                self.assertFalse(ok)
                self.assertEqual("NON_FINITE_CONFIDENCE", violations[0]["code"])

    def test_nan_claim_confidence_fails(self):
        event = {
            "zmeta_version": "1.0",
            "event": {
                "event_id": str(uuid7()),
                "event_type": "INFERENCE_EVENT",
                "event_subtype": "CLASSIFICATION",
                "ts": "2025-01-17T14:30:00Z",
            },
            "source": {
                "platform_id": "node-01",
                "node_role": "EDGE",
                "producer": "eo-cv",
            },
            "payload": {
                "inference_type": "CLASSIFICATION",
                "claim": {"type": "UAV", "confidence": float("nan")},
            },
            "confidence": 0.7,
        }
        ok, violations = self.semantics(event)
        self.assertFalse(ok)
        self.assertEqual("NON_FINITE_CONFIDENCE", violations[0]["code"])

    def test_finite_confidence_passes(self):
        event = rf_observation()
        event["confidence"] = 0.0
        ok, violations = self.semantics(event)
        self.assertTrue(ok, violations)


if __name__ == "__main__":
    unittest.main()
