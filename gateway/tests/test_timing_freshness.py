import copy
import importlib.util
import unittest
from pathlib import Path

from zmeta_uuid import uuid7


ROOT = Path(__file__).resolve().parents[2]
VALIDATORS_PATH = ROOT / "gateway" / "src" / "validators.py"
spec = importlib.util.spec_from_file_location("zmeta_validators", VALIDATORS_PATH)
validators = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validators)


def time_status(ts, *, sync_state="LOCKED", est_error_ms=1, source=None):
    return {
        "zmeta_version": "1.0",
        "event": {
            "event_id": str(uuid7()),
            "event_type": "SYSTEM_EVENT",
            "event_subtype": "TIME_STATUS",
            "ts": ts,
        },
        "source": source
        or {
            "platform_id": "node-01",
            "node_role": "GATEWAY",
            "producer": "sensorops",
        },
        "payload": {
            "system_type": "TIME_STATUS",
            "state": sync_state,
            "metrics": {
                "time_source": "GPS_PPS",
                "sync_state": sync_state,
                "est_error_ms": est_error_ms,
                "last_sync_ts": ts,
            },
        },
    }


def state_event(ts, *, source=None, confidence=0.8):
    return {
        "zmeta_version": "1.0",
        "event": {
            "event_id": str(uuid7()),
            "event_type": "STATE_EVENT",
            "event_subtype": "TRACK_STATE",
            "ts": ts,
        },
        "source": source
        or {
            "platform_id": "node-01",
            "node_role": "GATEWAY",
            "producer": "sensorops",
        },
        "profile": "H",
        "payload": {
            "track_id": "track-1",
            "geo": {"lat": 34.0, "lon": -118.0, "alt_m": 100.0},
            "valid_for_ms": 1000,
        },
        "confidence": confidence,
        "lineage": {"based_on": [str(uuid7())]},
    }


class TimingFreshnessTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = validators.load_policy(ROOT / "policy")
        cls.severity_map = cls.policy["violation_severities"]
        cls.semantics = cls.policy["semantics"]
        cls.freshness = cls.policy["timing_freshness"]
        cls.schema = validators.load_schema(ROOT / "schema" / "zmeta-event-1.0.schema.json")

    def test_fresh_time_status_passes(self):
        state = validators.ValidationState()
        state.record_timing(time_status("2025-01-17T14:30:00Z"))

        ok, violations = validators.validate_timing_quality(
            state_event("2025-01-17T14:30:05Z"),
            self.semantics,
            state=state,
            severity_map=self.severity_map,
            timing_freshness_policy=self.freshness,
            profile="H",
        )

        self.assertTrue(ok, violations)
        self.assertEqual([], violations)

    def test_stale_time_status_rejects_by_default(self):
        state = validators.ValidationState()
        state.record_timing(time_status("2025-01-17T14:30:00Z"))

        ok, violations = validators.validate_timing_quality(
            state_event("2025-01-17T14:30:11Z"),
            self.semantics,
            state=state,
            severity_map=self.severity_map,
            timing_freshness_policy=self.freshness,
            profile="H",
        )

        self.assertFalse(ok)
        self.assertEqual("TIMING_STATUS_STALE", violations[0]["code"])
        self.assertEqual("fail", violations[0]["severity"])

    def test_small_negative_time_status_age_passes_within_tolerance(self):
        state = validators.ValidationState()
        state.record_timing(time_status("2025-01-17T14:30:00Z"))

        ok, violations = validators.validate_timing_quality(
            state_event("2025-01-17T14:29:59.500Z"),
            self.semantics,
            state=state,
            severity_map=self.severity_map,
            timing_freshness_policy=self.freshness,
            profile="H",
        )

        self.assertTrue(ok, violations)
        self.assertEqual([], violations)

    def test_negative_time_status_age_warns_by_default(self):
        state = validators.ValidationState()
        state.record_timing(time_status("2025-01-17T14:30:00Z"))

        ok, violations = validators.validate_timing_quality(
            state_event("2025-01-17T14:29:58Z"),
            self.semantics,
            state=state,
            severity_map=self.severity_map,
            timing_freshness_policy=self.freshness,
            profile="H",
        )

        self.assertTrue(ok)
        self.assertEqual("TIMING_STATUS_AGE_NEGATIVE", violations[0]["code"])
        self.assertEqual("warn", violations[0]["severity"])
        self.assertEqual("WARN_ACCEPT", violations[0]["details"]["policy_decision"])
        self.assertEqual(2000.0, violations[0]["details"]["negative_age_ms"])
        self.assertEqual(1000, violations[0]["details"]["max_negative_age_ms"])

    def test_negative_time_status_age_can_reject_by_policy(self):
        policy = copy.deepcopy(self.freshness)
        policy["negative_age_mode"] = "reject"
        state = validators.ValidationState()
        state.record_timing(time_status("2025-01-17T14:30:00Z"))

        ok, violations = validators.validate_timing_quality(
            state_event("2025-01-17T14:29:58Z"),
            self.semantics,
            state=state,
            severity_map=self.severity_map,
            timing_freshness_policy=policy,
            profile="H",
        )

        self.assertFalse(ok)
        self.assertEqual("TIMING_STATUS_AGE_NEGATIVE", violations[0]["code"])
        self.assertEqual("fail", violations[0]["severity"])

    def test_missing_time_status_rejects_by_default(self):
        ok, violations = validators.validate_timing_quality(
            state_event("2025-01-17T14:30:05Z"),
            self.semantics,
            state=validators.ValidationState(),
            severity_map=self.severity_map,
            timing_freshness_policy=self.freshness,
            profile="H",
        )

        self.assertFalse(ok)
        self.assertEqual("TIMING_STATUS_MISSING", violations[0]["code"])

    def test_warn_mode_does_not_reject_stale_status(self):
        policy = copy.deepcopy(self.freshness)
        policy["mode"] = "warn"
        state = validators.ValidationState()
        state.record_timing(time_status("2025-01-17T14:30:00Z"))

        ok, violations = validators.validate_timing_quality(
            state_event("2025-01-17T14:30:11Z"),
            self.semantics,
            state=state,
            severity_map=self.severity_map,
            timing_freshness_policy=policy,
            profile="H",
        )

        self.assertTrue(ok)
        self.assertEqual("TIMING_STATUS_STALE", violations[0]["code"])
        self.assertEqual("warn", violations[0]["severity"])
        self.assertEqual("timing", violations[0]["details"]["risk_dimension"])
        self.assertEqual("WARN_ACCEPT", violations[0]["details"]["policy_decision"])
        self.assertIn("COMMAND_BASIS", violations[0]["details"]["prohibited_uses"])

    def test_degrade_mode_reduces_confidence(self):
        policy = copy.deepcopy(self.freshness)
        policy["mode"] = "degrade"
        event = state_event("2025-01-17T14:30:11Z", confidence=0.8)
        state = validators.ValidationState()
        state.record_timing(time_status("2025-01-17T14:30:00Z"))

        ok, violations = validators.validate_timing_quality(
            event,
            self.semantics,
            state=state,
            severity_map=self.severity_map,
            timing_freshness_policy=policy,
            profile="H",
        )
        changed = validators.apply_timing_freshness_degradation(event, violations, policy)

        self.assertTrue(ok)
        self.assertTrue(changed)
        self.assertEqual("warn", violations[0]["severity"])
        self.assertEqual("timing", violations[0]["details"]["risk_dimension"])
        self.assertEqual("DEGRADED_ACCEPT", violations[0]["details"]["policy_decision"])
        self.assertEqual("degrade", violations[0]["details"]["action"])
        self.assertEqual(
            {"confidence_reduction_factor": 2.0},
            violations[0]["details"]["effects"],
        )
        self.assertAlmostEqual(0.4, event["confidence"])
        risk = event["payload"]["extensions"]["risk_adjudication"][0]
        self.assertEqual("timing", risk["risk_dimension"])
        self.assertEqual("TIMING_STATUS_STALE", risk["reason_code"])
        self.assertEqual("DEGRADED_ACCEPT", risk["policy_decision"])
        self.assertEqual(
            {"confidence_reduction_factor": 2.0},
            risk["effects"],
        )
        self.assertIn("COMMAND_BASIS", risk["prohibited_uses"])

    def test_negative_time_status_age_can_degrade_by_policy(self):
        policy = copy.deepcopy(self.freshness)
        policy["negative_age_mode"] = "degrade"
        event = state_event("2025-01-17T14:29:58Z", confidence=0.8)
        state = validators.ValidationState()
        state.record_timing(time_status("2025-01-17T14:30:00Z"))

        ok, violations = validators.validate_timing_quality(
            event,
            self.semantics,
            state=state,
            severity_map=self.severity_map,
            timing_freshness_policy=policy,
            profile="H",
        )
        changed = validators.apply_timing_freshness_degradation(event, violations, policy)

        self.assertTrue(ok)
        self.assertTrue(changed)
        self.assertEqual("TIMING_STATUS_AGE_NEGATIVE", violations[0]["code"])
        self.assertEqual("DEGRADED_ACCEPT", violations[0]["details"]["policy_decision"])
        self.assertAlmostEqual(0.4, event["confidence"])
        risk = event["payload"]["extensions"]["risk_adjudication"][0]
        self.assertEqual("TIMING_STATUS_AGE_NEGATIVE", risk["reason_code"])

    def test_profile_specific_degrade_mode_applies_to_profile_l(self):
        policy = copy.deepcopy(self.freshness)
        policy["mode_by_profile"] = {"L": "degrade", "M": "reject", "H": "reject"}
        event = state_event("2025-01-17T14:31:30Z", confidence=0.8)
        event["profile"] = "L"
        state = validators.ValidationState()
        state.record_timing(time_status("2025-01-17T14:30:00Z"))

        ok, violations = validators.validate_timing_quality(
            event,
            self.semantics,
            state=state,
            severity_map=self.severity_map,
            timing_freshness_policy=policy,
            profile="L",
        )
        changed = validators.apply_timing_freshness_degradation(event, violations, policy)

        self.assertTrue(ok)
        self.assertTrue(changed)
        self.assertEqual("TIMING_STATUS_STALE", violations[0]["code"])
        self.assertEqual("warn", violations[0]["severity"])
        self.assertEqual("degrade", violations[0]["details"]["policy_mode"])
        self.assertEqual("DEGRADED_ACCEPT", violations[0]["details"]["policy_decision"])
        self.assertAlmostEqual(0.4, event["confidence"])
        self.assertEqual(
            "DEGRADED_ACCEPT",
            event["payload"]["extensions"]["risk_adjudication"][0]["policy_decision"],
        )

    def test_profile_specific_degrade_does_not_apply_to_profile_h(self):
        policy = copy.deepcopy(self.freshness)
        policy["mode_by_profile"] = {"L": "degrade", "M": "reject", "H": "reject"}
        event = state_event("2025-01-17T14:30:11Z", confidence=0.8)
        state = validators.ValidationState()
        state.record_timing(time_status("2025-01-17T14:30:00Z"))

        ok, violations = validators.validate_timing_quality(
            event,
            self.semantics,
            state=state,
            severity_map=self.severity_map,
            timing_freshness_policy=policy,
            profile="H",
        )

        self.assertFalse(ok)
        self.assertEqual("TIMING_STATUS_STALE", violations[0]["code"])
        self.assertEqual("fail", violations[0]["severity"])

    def test_sensor_id_event_can_use_node_level_time_status(self):
        state = validators.ValidationState()
        state.record_timing(time_status("2025-01-17T14:30:00Z"))
        event = state_event(
            "2025-01-17T14:30:05Z",
            source={
                "platform_id": "node-01",
                "node_role": "GATEWAY",
                "producer": "sensorops",
                "sensor_id": "rf-01",
            },
        )

        ok, violations = validators.validate_timing_quality(
            event,
            self.semantics,
            state=state,
            severity_map=self.severity_map,
            timing_freshness_policy=self.freshness,
            profile="H",
        )

        self.assertTrue(ok, violations)

    def test_time_status_missing_est_error_fails_schema(self):
        event = time_status("2025-01-17T14:30:00Z")
        del event["payload"]["metrics"]["est_error_ms"]

        ok, violations = validators.validate_schema(event, self.schema, self.severity_map)

        self.assertFalse(ok)
        self.assertEqual("SCHEMA_INVALID", violations[0]["code"])

    def test_holdover_est_error_decrease_warns(self):
        state = validators.ValidationState()
        state.record_timing(
            time_status("2025-01-17T14:30:00Z", sync_state="HOLDOVER", est_error_ms=250)
        )

        ok, violations = validators.validate_timing_quality(
            time_status("2025-01-17T14:30:05Z", sync_state="HOLDOVER", est_error_ms=100),
            self.semantics,
            state=state,
            severity_map=self.severity_map,
            timing_freshness_policy=self.freshness,
            profile="H",
        )

        self.assertTrue(ok)
        self.assertEqual("TIMING_STATUS_HOLDOVER_NON_MONOTONIC", violations[0]["code"])
        self.assertEqual("warn", violations[0]["severity"])
        self.assertEqual("timing", violations[0]["details"]["risk_dimension"])
        self.assertEqual("WARN_ACCEPT", violations[0]["details"]["policy_decision"])


if __name__ == "__main__":
    unittest.main()
