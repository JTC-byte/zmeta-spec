"""Zero-fill RF heuristic tests (the geo check's feature-family analogue).

Minted 2026-08-13 from field evidence: an external line-of-bearing mapping
zero-filled `bandwidth_hz` and `power_dbm` its source records never
carried, and the events passed with no RF-shaped signal. The predicate is
the PAIR both exactly 0.0, and only the pair, re-adjudicated by the
maintainer after the pre-cut verification pass surfaced the collision the
first draft missed: the documented receiver-class sentinel
(adapters/AUTHORING.md, "declared-sentinel conventions to keep distinct
from fabrication") emits `bandwidth_hz` 0.0 beside a measured power and
must stay sanctioned, and `power_dbm` 0.0 alone is one milliwatt, a
legitimate reading. The co-present pair also scopes the check to the RF
family without a modality gate, because no other feature family carries
`power_dbm`. Coverage walks the same three containers as the geo
analogue (payload, claim, estimated_state), per the recorded R1-11 A-16
lesson. Warn is the ceiling by construction (the locked contract states
the zero-fill prohibition for geo only) and the event stays accepted:
the consumer adjudicates.
"""

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VALIDATORS_PATH = ROOT / "gateway" / "src" / "validators.py"
spec = importlib.util.spec_from_file_location("zmeta_validators", VALIDATORS_PATH)
validators = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validators)

CODE = "RF_ZERO_FILL_SUSPECTED"


def rf_observation(features):
    return {
        "zmeta_version": "1.0",
        "event": {
            "event_id": "019f70b2-0000-7000-8000-000000000001",
            "event_type": "OBSERVATION_EVENT",
            "event_subtype": "RF",
            "ts": "2026-08-13T10:00:00Z",
        },
        "source": {
            "platform_id": "sensor-node-01",
            "node_role": "EDGE",
            "producer": "rf-sensor",
        },
        "profile": "H",
        "payload": {
            "modality": "RF",
            "features": features,
            "timing_quality": {
                "time_source": "GPS_PPS",
                "sync_state": "LOCKED",
                "est_error_ms": 1,
                "last_sync_ts": "2026-08-13T09:59:59Z",
            },
        },
    }


def rf_inference(claim_features):
    return {
        "zmeta_version": "1.0",
        "event": {
            "event_id": "019f70b2-0000-7000-8000-000000000002",
            "event_type": "INFERENCE_EVENT",
            "event_subtype": "CLASSIFICATION",
            "ts": "2026-08-13T10:00:01Z",
        },
        "source": {
            "platform_id": "analytics-node-01",
            "node_role": "GATEWAY",
            "producer": "classifier-alpha",
        },
        "profile": "H",
        "payload": {
            "inference_type": "CLASSIFICATION",
            "claim": {"class_name": "emitter", "features": claim_features},
            "model": {"name": "rf-classifier", "version": "1.0.0"},
            "based_on": ["019c2b5c-c053-70e1-b6aa-34bf14c8a401"],
            "timing_quality": {
                "time_source": "NTP",
                "sync_state": "LOCKED",
                "est_error_ms": 25,
                "last_sync_ts": "2026-08-13T09:59:00Z",
            },
        },
        "confidence": 0.8,
        "lineage": {"based_on": ["019c2b5c-c053-70e1-b6aa-34bf14c8a401"]},
    }


class RfZeroFillWarnTest(unittest.TestCase):
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

    def codes(self, violations):
        return [v["code"] for v in violations]

    def test_the_field_signature_warns_but_event_stays_accepted(self):
        """The exact fabrication signature from the field case: both fields
        exactly 0.0 because the source records carried neither."""
        ok, violations = self.run_semantics(
            rf_observation({"center_freq_hz": 462562500, "bandwidth_hz": 0.0, "power_dbm": 0.0})
        )
        self.assertTrue(ok, violations)
        warn = next(v for v in violations if v["code"] == CODE)
        self.assertEqual("warn", warn["severity"])
        self.assertEqual({"path": "payload.features"}, warn["details"])
        self.assertEqual([], [v for v in violations if v["severity"] == "fail"])

    def test_the_declared_bandwidth_sentinel_stays_sanctioned(self):
        """The re-adjudication case: receiver-class sensors emit the
        documented bandwidth_hz 0.0 sentinel beside a MEASURED power
        (AUTHORING.md declared-sentinel convention; kraken, moth,
        signalhunter). The pair predicate must leave it unlabeled."""
        ok, violations = self.run_semantics(
            rf_observation({"center_freq_hz": 462562500, "bandwidth_hz": 0.0, "power_dbm": -41.5})
        )
        self.assertTrue(ok, violations)
        self.assertNotIn(CODE, self.codes(violations))

    def test_one_milliwatt_alone_never_warns(self):
        """power_dbm 0.0 is a legitimate reading beside a real bandwidth."""
        ok, violations = self.run_semantics(
            rf_observation({"center_freq_hz": 2450000000, "bandwidth_hz": 20000000, "power_dbm": 0.0})
        )
        self.assertTrue(ok, violations)
        self.assertNotIn(CODE, self.codes(violations))

    def test_a_real_measurement_does_not_warn(self):
        ok, violations = self.run_semantics(
            rf_observation({"center_freq_hz": 2450000000, "bandwidth_hz": 20000000, "power_dbm": -35.2})
        )
        self.assertTrue(ok, violations)
        self.assertNotIn(CODE, self.codes(violations))

    def test_a_zero_filled_claim_features_block_warns_with_the_claim_path(self):
        """The R1-11 A-16 lesson: the geo analogue walks payload, claim, and
        estimated_state, and this check walks the same three."""
        ok, violations = self.run_semantics(
            rf_inference({"center_freq_hz": 462562500, "bandwidth_hz": 0.0, "power_dbm": 0.0})
        )
        self.assertTrue(ok, violations)
        warn = next(v for v in violations if v["code"] == CODE)
        self.assertEqual({"path": "payload.claim.features"}, warn["details"])

    def test_a_zero_filled_estimated_state_features_block_warns_too(self):
        """The A-16 container specifically: the fused, promoted state is the
        one a consumer acts on, and it was the geo class's recorded blind
        spot. Proven in-repo per P2-D1, not as a session act."""
        event = {
            "zmeta_version": "1.0",
            "event": {
                "event_id": "019f70b2-0000-7000-8000-000000000003",
                "event_type": "FUSION_EVENT",
                "event_subtype": "TRACK_FUSION",
                "ts": "2026-08-13T10:00:03Z",
            },
            "source": {
                "platform_id": "fusion-node-01",
                "node_role": "GATEWAY",
                "producer": "fusion-engine",
            },
            "profile": "H",
            "payload": {
                "track_id": "TRACK-RF-ZF-001",
                "members": ["019c2b5c-c053-70e1-b6aa-34bf14c8a401"],
                "stability": 0.62,
                "last_seen_ts": "2026-08-13T10:00:02Z",
                "estimated_state": {
                    "features": {
                        "center_freq_hz": 462562500,
                        "bandwidth_hz": 0.0,
                        "power_dbm": 0.0,
                    }
                },
                "timing_quality": {
                    "time_source": "GPS_PPS",
                    "sync_state": "LOCKED",
                    "est_error_ms": 1,
                    "last_sync_ts": "2026-08-13T10:00:02Z",
                },
            },
            "confidence": 0.9,
            "lineage": {
                "based_on": ["019c2b5c-c053-70e1-b6aa-34bf14c8a401"],
            },
        }
        ok, violations = self.run_semantics(event)
        self.assertTrue(ok, violations)
        warn = next(v for v in violations if v["code"] == CODE)
        self.assertEqual({"path": "payload.estimated_state.features"}, warn["details"])

    def test_negative_zero_and_integer_zero_are_the_same_signature(self):
        """Real JSON producers emit -0.0 and bare 0; both equal 0.0 and both
        are the fabrication shape, not a measurement."""
        for pair in ((-0.0, 0.0), (0, 0)):
            ok, violations = self.run_semantics(
                rf_observation(
                    {"center_freq_hz": 462562500, "bandwidth_hz": pair[0], "power_dbm": pair[1]}
                )
            )
            self.assertTrue(ok, violations)
            self.assertIn(CODE, self.codes(violations), pair)

    def test_wire_shaped_junk_never_triggers_or_crashes(self):
        """Shape junk is schema's job: booleans equal zero in Python, and a
        missing half of the pair is honest absence, not the signature.
        Schema-invalid on purpose; the check runs directly on wire-shaped
        input."""
        for features in (
            {"center_freq_hz": 462562500, "bandwidth_hz": False, "power_dbm": False},
            {"center_freq_hz": 462562500, "bandwidth_hz": 0.0},
            {"center_freq_hz": 462562500, "power_dbm": 0.0},
            {"center_freq_hz": 462562500, "bandwidth_hz": "0.0", "power_dbm": 0.0},
        ):
            event = rf_observation(features)
            _, violations = validators.validate_semantics(
                event, self.policy["semantics"], self.severity_map
            )
            self.assertNotIn(CODE, self.codes(violations), features)


if __name__ == "__main__":
    unittest.main()
