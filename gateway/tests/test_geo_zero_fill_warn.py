"""Zero-fill geo heuristic tests (contract 6.8).

Contract 6.8 prohibits zero-filled geospatial data, but (0, 0) is also a
legitimate coordinate (null island), so a hard reject is impossible. The
check therefore emits GEO_ZERO_FILL_SUSPECTED at warn severity - the
documented ceiling for this heuristic - and the event stays accepted. See
adapters/ingress/mavlink/README.md for the ingress-side precedent of the
same ambiguity (the ArduPilot pre-lock null-island signature).
"""

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VALIDATORS_PATH = ROOT / "gateway" / "src" / "validators.py"
spec = importlib.util.spec_from_file_location("zmeta_validators", VALIDATORS_PATH)
validators = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validators)


def state_event(geo):
    return {
        "zmeta_version": "1.0",
        "event": {
            "event_id": "019f70b1-0000-7000-8000-000000000001",
            "event_type": "STATE_EVENT",
            "event_subtype": "TRACK_STATE",
            "ts": "2026-07-16T10:00:00Z",
        },
        "source": {
            "platform_id": "fusion-node-01",
            "node_role": "GATEWAY",
            "producer": "fusion-engine",
        },
        "profile": "H",
        "payload": {
            "track_id": "TRACK-GEO-WARN-001",
            "geo": geo,
            "valid_for_ms": 1000,
            "timing_quality": {
                "time_source": "GPS_PPS",
                "sync_state": "LOCKED",
                "est_error_ms": 1,
                "last_sync_ts": "2026-07-16T09:59:59Z",
            },
        },
        "confidence": 0.7,
        "lineage": {"based_on": ["019c2b5c-c053-70e1-b6aa-34bf14c8a402"]},
    }


def inference_event(claim_geo):
    return {
        "zmeta_version": "1.0",
        "event": {
            "event_id": "019f70b1-0000-7000-8000-000000000002",
            "event_type": "INFERENCE_EVENT",
            "event_subtype": "CLASSIFICATION",
            "ts": "2026-07-16T10:00:01Z",
        },
        "source": {
            "platform_id": "analytics-node-01",
            "node_role": "GATEWAY",
            "producer": "classifier-alpha",
        },
        "profile": "H",
        "payload": {
            "inference_type": "CLASSIFICATION",
            "claim": {"label": "person", "geo": claim_geo},
            "model": {"name": "yolo-detector", "version": "8.2.0"},
            "based_on": ["019c2b5c-c053-70e1-b6aa-34bf14c8a401"],
            "timing_quality": {
                "time_source": "NTP",
                "sync_state": "LOCKED",
                "est_error_ms": 25,
                "last_sync_ts": "2026-07-16T09:59:00Z",
            },
        },
        "confidence": 0.87,
        "lineage": {"based_on": ["019c2b5c-c053-70e1-b6aa-34bf14c8a401"]},
    }


class GeoZeroFillWarnTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.validator = validators.load_schema(ROOT / "schema" / "zmeta-event.schema.json")
        cls.policy = validators.load_policy(ROOT / "policy")
        cls.severity_map = cls.policy["violation_severities"]

    def run_semantics(self, event):
        # The fixtures must be schema-valid so the semantic layer is what is
        # exercised, not a schema rejection upstream of it.
        self.assertEqual([], list(self.validator.iter_errors(event)))
        return validators.validate_semantics(event, self.policy["semantics"], self.severity_map)

    def test_zero_zero_geo_warns_but_event_stays_accepted(self):
        ok, violations = self.run_semantics(state_event({"lat": 0.0, "lon": 0.0, "alt_m": 100.0}))
        self.assertTrue(ok, violations)
        codes = [(v["code"], v["severity"]) for v in violations]
        self.assertIn(("GEO_ZERO_FILL_SUSPECTED", "warn"), codes)
        warn = next(v for v in violations if v["code"] == "GEO_ZERO_FILL_SUSPECTED")
        self.assertEqual({"path": "payload.geo"}, warn["details"])
        # Never reject: warn severity only, no fail-severity violations.
        self.assertEqual([], [v for v in violations if v["severity"] == "fail"])

    def test_real_coordinates_do_not_warn(self):
        ok, violations = self.run_semantics(state_event({"lat": 34.0522, "lon": -118.2437, "alt_m": 100.0}))
        self.assertTrue(ok, violations)
        self.assertEqual([], [v for v in violations if v["code"] == "GEO_ZERO_FILL_SUSPECTED"])

    def test_zero_zero_with_zero_altitude_warns(self):
        ok, violations = self.run_semantics(state_event({"lat": 0.0, "lon": 0.0, "alt_m": 0.0}))
        self.assertTrue(ok, violations)
        self.assertIn("GEO_ZERO_FILL_SUSPECTED", [v["code"] for v in violations])

    def test_zero_zero_claim_geo_warns_with_claim_path(self):
        ok, violations = self.run_semantics(inference_event({"lat": 0.0, "lon": 0.0, "alt_m": 90.0}))
        self.assertTrue(ok, violations)
        warn = next(v for v in violations if v["code"] == "GEO_ZERO_FILL_SUSPECTED")
        self.assertEqual("warn", warn["severity"])
        self.assertEqual({"path": "payload.claim.geo"}, warn["details"])

    def test_single_zero_axis_does_not_warn(self):
        # Only the (0, 0) pair is the zero-fill signature; a real coordinate
        # on one zero axis (e.g. the equator) must not warn.
        ok, violations = self.run_semantics(state_event({"lat": 0.0, "lon": -118.2437, "alt_m": 100.0}))
        self.assertTrue(ok, violations)
        self.assertEqual([], [v for v in violations if v["code"] == "GEO_ZERO_FILL_SUSPECTED"])


if __name__ == "__main__":
    unittest.main()
