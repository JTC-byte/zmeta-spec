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


def source(producer="torch", role="GATEWAY"):
    return {"platform_id": "node-01", "node_role": role, "producer": producer}


def observation(event_id=None):
    event_id = event_id or str(uuid7())
    return {
        "zmeta_version": "1.0",
        "event": {
            "event_id": event_id,
            "event_type": "OBSERVATION_EVENT",
            "event_subtype": "RF",
            "ts": "2025-01-17T14:30:00Z",
        },
        "source": source("rf-sensor", "EDGE"),
        "profile": "H",
        "payload": {
            "modality": "RF",
            "features": {
                "center_freq_hz": 2450000000,
                "bandwidth_hz": 20000000,
                "power_dbm": -35.2,
            },
        },
    }


def inference(parent_id, event_id=None):
    event_id = event_id or str(uuid7())
    return {
        "zmeta_version": "1.0",
        "event": {
            "event_id": event_id,
            "event_type": "INFERENCE_EVENT",
            "event_subtype": "CLASSIFICATION",
            "ts": "2025-01-17T14:30:01Z",
        },
        "source": source(),
        "profile": "H",
        "payload": {
            "inference_type": "CLASSIFICATION",
            "claim": {"label": "drone"},
            "model": {"name": "rf-classifier", "version": "1.0.0"},
            "based_on": [parent_id],
        },
        "confidence": 0.82,
        "lineage": {"based_on": [parent_id]},
    }


def fusion(parent_ids, member_ids=None, event_id=None):
    event_id = event_id or str(uuid7())
    member_ids = member_ids if member_ids is not None else list(parent_ids)
    return {
        "zmeta_version": "1.0",
        "event": {
            "event_id": event_id,
            "event_type": "FUSION_EVENT",
            "event_subtype": "TRACK_FUSION",
            "ts": "2025-01-17T14:30:02Z",
        },
        "source": source(),
        "profile": "H",
        "payload": {
            "track_id": "track-1",
            "members": member_ids,
            "stability": 0.6,
            "last_seen_ts": "2025-01-17T14:30:02Z",
        },
        "confidence": 0.76,
        "lineage": {"based_on": parent_ids},
    }


def state_event(parent_ids, profile="H"):
    return {
        "zmeta_version": "1.0",
        "event": {
            "event_id": str(uuid7()),
            "event_type": "STATE_EVENT",
            "event_subtype": "TRACK_STATE",
            "ts": "2025-01-17T14:30:03Z",
        },
        "source": source("sensorops" if profile == "L" else "torch"),
        "profile": profile,
        "payload": {
            "track_id": "track-1",
            "geo": {"lat": 34.0, "lon": -118.0, "alt_m": 100.0},
            "valid_for_ms": 1000,
        },
        "confidence": 0.7,
        "lineage": {"based_on": parent_ids},
    }


class LineageSemanticsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = validators.load_policy(ROOT / "policy")
        cls.severity_map = cls.policy["violation_severities"]
        cls.lineage_policy = cls.policy["lineage"]
        cls.schema = validators.load_schema(ROOT / "schema" / "zmeta-event-1.0.schema.json")

    def test_inference_payload_based_on_subset_passes(self):
        obs = observation()
        event = inference(obs["event"]["event_id"])
        state = validators.ValidationState()
        state.record(obs)

        ok, violations = validators.validate_lineage(
            event, self.lineage_policy, state=state, profile="H", severity_map=self.severity_map
        )

        self.assertTrue(ok, violations)
        self.assertEqual([], violations)

    def test_inference_payload_based_on_not_in_lineage_fails(self):
        parent_id = str(uuid7())
        event = inference(parent_id)
        event["lineage"]["based_on"] = [str(uuid7())]

        ok, violations = validators.validate_lineage(
            event, self.lineage_policy, state=None, profile="H", severity_map=self.severity_map
        )

        self.assertFalse(ok)
        self.assertEqual("LINEAGE_PAYLOAD_BASED_ON_NOT_SUBSET", violations[0]["code"])
        self.assertEqual("lineage", violations[0]["details"]["risk_dimension"])
        self.assertEqual("REJECTED", violations[0]["details"]["policy_decision"])

    def test_state_without_lineage_fails_schema(self):
        event = state_event([str(uuid7())])
        del event["lineage"]

        ok, violations = validators.validate_schema(event, self.schema, self.severity_map)

        self.assertFalse(ok)
        self.assertEqual("SCHEMA_INVALID", violations[0]["code"])

    def test_profile_l_unresolved_lineage_can_warn_without_rejecting(self):
        policy = copy.deepcopy(self.lineage_policy)
        policy["unresolved_parent_mode"] = {"L": "warn"}

        ok, violations = validators.validate_lineage(
            state_event([str(uuid7())], profile="L"),
            policy,
            state=validators.ValidationState(),
            profile="L",
            severity_map=self.severity_map,
        )

        self.assertTrue(ok)
        self.assertEqual("LINEAGE_PARENT_UNRESOLVED", violations[0]["code"])
        self.assertEqual("warn", violations[0]["severity"])
        self.assertEqual("lineage", violations[0]["details"]["risk_dimension"])
        self.assertEqual("WARN_ACCEPT", violations[0]["details"]["policy_decision"])
        self.assertIn("COMMAND_BASIS", violations[0]["details"]["prohibited_uses"])

    def test_parent_type_mismatch_fails_when_parent_store_is_available(self):
        obs = observation()
        inf = inference(obs["event"]["event_id"])
        state = validators.ValidationState()
        state.record(obs)
        state.record(inf)

        ok, violations = validators.validate_lineage(
            state_event([inf["event"]["event_id"]]),
            self.lineage_policy,
            state=state,
            profile="H",
            severity_map=self.severity_map,
        )

        self.assertFalse(ok)
        self.assertEqual("LINEAGE_PARENT_TYPE_INVALID", violations[0]["code"])
        self.assertEqual("REJECTED", violations[0]["details"]["policy_decision"])

    def test_fusion_member_missing_from_lineage_warns(self):
        obs = observation()
        inf = inference(obs["event"]["event_id"])
        event = fusion([inf["event"]["event_id"]], member_ids=[obs["event"]["event_id"]])
        state = validators.ValidationState()
        state.record(obs)
        state.record(inf)

        ok, violations = validators.validate_lineage(
            event, self.lineage_policy, state=state, profile="H", severity_map=self.severity_map
        )

        self.assertTrue(ok)
        self.assertEqual("LINEAGE_FUSION_MEMBERS_NOT_IN_BASED_ON", violations[0]["code"])
        self.assertEqual("warn", violations[0]["severity"])
        self.assertEqual("lineage", violations[0]["details"]["risk_dimension"])
        self.assertEqual("WARN_ACCEPT", violations[0]["details"]["policy_decision"])

    def test_state_from_fusion_parent_passes(self):
        obs = observation()
        inf = inference(obs["event"]["event_id"])
        fus = fusion([obs["event"]["event_id"], inf["event"]["event_id"]], member_ids=[obs["event"]["event_id"]])
        state = validators.ValidationState()
        state.record(obs)
        state.record(inf)
        state.record(fus)

        ok, violations = validators.validate_lineage(
            state_event([fus["event"]["event_id"]]),
            self.lineage_policy,
            state=state,
            profile="H",
            severity_map=self.severity_map,
        )

        self.assertTrue(ok, violations)
        self.assertEqual([], violations)


if __name__ == "__main__":
    unittest.main()
