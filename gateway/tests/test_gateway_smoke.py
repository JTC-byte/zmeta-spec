import importlib.util
import json
import unittest
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VALIDATORS_PATH = ROOT / "gateway" / "src" / "validators.py"
spec = importlib.util.spec_from_file_location("zmeta_validators", VALIDATORS_PATH)
validators = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validators)

GATEWAY_PATH = ROOT / "gateway" / "src" / "gateway.py"
spec_gw = importlib.util.spec_from_file_location("zmeta_gateway", GATEWAY_PATH)
gateway = importlib.util.module_from_spec(spec_gw)
spec_gw.loader.exec_module(gateway)


class GatewaySmokeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        schema_path = ROOT / "schema" / "zmeta-event-1.0.schema.json"
        policy_dir = ROOT / "policy"
        cls.validator = validators.load_schema(schema_path)
        cls.policy = validators.load_policy(policy_dir)

    def test_valid_state_event(self):
        event = {
            "zmeta_version": "1.0",
            "event": {
                "event_id": str(uuid.uuid4()),
                "event_type": "STATE_EVENT",
                "event_subtype": "TEST",
                "ts": "2025-01-17T14:32:10Z",
            },
            "source": {
                "platform_id": "platform-1",
                "node_role": "GATEWAY",
                "producer": "sensorops",
            },
            "payload": {
                "track_id": "track-1",
                "geo": {"lat": 40.0, "lon": -75.0, "alt_m": 120.5},
                "valid_for_ms": 1000,
            },
            "confidence": 0.9,
            "lineage": {"based_on": [str(uuid.uuid4())]},
        }

        ok, violations = validators.validate_schema(event, self.validator, self.policy["violation_severities"])
        self.assertTrue(ok)
        ok, violations = validators.validate_role(
            event, {"roles": self.policy["roles"], "deny": self.policy["deny"]}, self.policy["violation_severities"]
        )
        self.assertTrue(ok)
        ok, violations = validators.validate_profile(event, "H", self.policy["profiles"], self.policy["violation_severities"])
        self.assertTrue(ok)
        ok, violations = validators.validate_semantics(event, self.policy["semantics"], self.policy["violation_severities"])
        self.assertTrue(ok)
        ok, violations = validators.validate_routing(event, self.policy["routing"], self.policy["violation_severities"])
        self.assertTrue(ok)

    def test_observation_with_track_id_is_rejected(self):
        event = {
            "zmeta_version": "1.0",
            "event": {
                "event_id": str(uuid.uuid4()),
                "event_type": "OBSERVATION_EVENT",
                "event_subtype": "TEST",
                "ts": "2025-01-17T14:32:10Z",
            },
            "source": {
                "platform_id": "platform-1",
                "node_role": "EDGE",
                "producer": "sensorops",
            },
            "payload": {
                "modality": "RF",
                "features": {},
                "track_id": "track-1",
            },
        }

        ok, violations = validators.validate_schema(event, self.validator, self.policy["violation_severities"])
        self.assertTrue(ok)
        ok, violations = validators.validate_semantics(event, self.policy["semantics"], self.policy["violation_severities"])
        self.assertFalse(ok)
        self.assertEqual(violations[0]["code"], "OBSERVATION_HAS_IDENTITY")

    def test_state_with_features_is_rejected(self):
        event = {
            "zmeta_version": "1.0",
            "event": {
                "event_id": str(uuid.uuid4()),
                "event_type": "STATE_EVENT",
                "event_subtype": "TRACK_STATE",
                "ts": "2025-01-17T14:32:10Z",
            },
            "source": {
                "platform_id": "fusion-node-01",
                "node_role": "GATEWAY",
                "producer": "fusion-engine",
            },
            "payload": {
                "track_id": "track-1",
                "geo": {"lat": 40.0, "lon": -75.0, "alt_m": 120.5},
                "features": {"center_freq_hz": 2450000000},
                "valid_for_ms": 1000,
            },
            "confidence": 0.9,
            "lineage": {"based_on": [str(uuid.uuid4())]},
        }

        ok, violations = validators.validate_schema(event, self.validator, self.policy["violation_severities"])
        self.assertTrue(ok)
        ok, violations = validators.validate_semantics(event, self.policy["semantics"], self.policy["violation_severities"])
        self.assertFalse(ok)
        self.assertEqual(violations[0]["code"], "STATE_HAS_RAW_FEATURES")

    def test_profile_l_rejects_observation_event(self):
        event = {
            "zmeta_version": "1.0",
            "event": {
                "event_id": str(uuid.uuid4()),
                "event_type": "OBSERVATION_EVENT",
                "event_subtype": "RF_OBSERVATION",
                "ts": "2025-01-17T14:32:10Z",
            },
            "source": {
                "platform_id": "sensor-node-01",
                "node_role": "EDGE",
                "producer": "rf-sensor",
            },
            "payload": {
                "modality": "RF",
                "features": {"center_freq_hz": 2450000000, "power_dbm": -35.2},
                "geo": {"lat": 34.0522, "lon": -118.2437, "alt_m": 120.5},
            },
        }

        ok, violations = validators.validate_schema(event, self.validator, self.policy["violation_severities"])
        self.assertTrue(ok)
        ok, violations = validators.validate_profile(
            event, "L", self.policy["profiles"], self.policy["violation_severities"]
        )
        self.assertFalse(ok)
        self.assertEqual(violations[0]["code"], "EVENT_TYPE_NOT_ALLOWED_FOR_PROFILE")

    def test_edge_fusion_event_rejected_by_role(self):
        event = {
            "zmeta_version": "1.0",
            "event": {
                "event_id": str(uuid.uuid4()),
                "event_type": "FUSION_EVENT",
                "event_subtype": "TRACK_FUSION",
                "ts": "2025-01-17T14:32:10Z",
            },
            "source": {
                "platform_id": "edge-node-01",
                "node_role": "EDGE",
                "producer": "fusion-engine",
            },
            "payload": {
                "track_id": "track-1",
                "members": [str(uuid.uuid4())],
                "stability": 0.5,
                "last_seen_ts": "2025-01-17T14:32:09Z",
            },
            "confidence": 0.8,
            "lineage": {"based_on": [str(uuid.uuid4())]},
        }

        ok, violations = validators.validate_schema(event, self.validator, self.policy["violation_severities"])
        self.assertTrue(ok)
        ok, violations = validators.validate_role(
            event, {"roles": self.policy["roles"], "deny": self.policy["deny"]}, self.policy["violation_severities"]
        )
        self.assertFalse(ok)
        self.assertEqual(violations[0]["code"], "EVENT_TYPE_NOT_ALLOWED_FOR_ROLE")

    def test_command_requires_deconfliction_false_fails_schema(self):
        event = {
            "zmeta_version": "1.0",
            "event": {
                "event_id": str(uuid.uuid4()),
                "event_type": "COMMAND_EVENT",
                "event_subtype": "MISSION_TASK",
                "ts": "2025-01-17T14:32:10Z",
            },
            "source": {
                "platform_id": "comms-node-1",
                "node_role": "GATEWAY",
                "producer": "sensorops",
            },
            "payload": {
                "task_id": "task-1",
                "task_type": "GOTO",
                "target_geo": {"lat": 34.0102, "lon": -118.0102},
                "valid_for_ms": 600000,
                "requires_deconfliction": False,
            },
        }

        ok, violations = validators.validate_schema(event, self.validator, self.policy["violation_severities"])
        self.assertFalse(ok)
        self.assertEqual(violations[0]["code"], "SCHEMA_INVALID")

    def test_task_ack_missing_task_id_severity(self):
        event = {
            "zmeta_version": "1.0",
            "event": {
                "event_id": str(uuid.uuid4()),
                "event_type": "SYSTEM_EVENT",
                "event_subtype": "TASK_ACK",
                "ts": "2025-01-17T14:32:10Z",
            },
            "source": {
                "platform_id": "uav-07",
                "node_role": "EDGE",
                "producer": "autonomy",
            },
            "payload": {
                "system_type": "TASK_ACK",
                "state": "RECEIVED",
                "metrics": {},
            },
        }

        ok, violations = validators.validate_schema(event, self.validator, self.policy["violation_severities"])
        self.assertTrue(ok)
        ok, violations = validators.validate_semantics(event, self.policy["semantics"], self.policy["violation_severities"])
        self.assertFalse(ok)
        self.assertEqual(violations[0]["code"], "TASK_ACK_MISSING_TASK_ID")
        self.assertEqual(violations[0]["severity"], "warn")

    def test_command_event_deduped(self):
        event = {
            "zmeta_version": "1.0",
            "event": {
                "event_id": str(uuid.uuid4()),
                "event_type": "COMMAND_EVENT",
                "event_subtype": "MISSION_TASK",
                "ts": "2025-01-17T15:05:00Z",
            },
            "source": {
                "platform_id": "comms-node-1",
                "node_role": "GATEWAY",
                "producer": "sensorops",
            },
            "payload": {
                "task_id": "task-dedupe-0001",
                "task_type": "GOTO",
                "target_geo": {"lat": 34.0105, "lon": -118.0105},
                "valid_for_ms": 600000,
                "requires_deconfliction": True,
            },
        }

        dedupe_cache = gateway.TaskDedupeCache()
        raw = json.dumps(event).encode("utf-8")

        first = gateway.process_message(raw, self.validator, self.policy, "L", dedupe_cache)
        self.assertEqual(len(first), 1)
        self.assertEqual(first[0]["event"]["event_type"], "COMMAND_EVENT")

        second = gateway.process_message(raw, self.validator, self.policy, "L", dedupe_cache)
        self.assertEqual(len(second), 1)
        self.assertEqual(second[0]["event"]["event_type"], "SYSTEM_EVENT")
        self.assertEqual(second[0]["event"]["event_subtype"], "TASK_ACK")
        self.assertEqual(second[0]["payload"]["system_type"], "TASK_ACK")
        self.assertEqual(second[0]["payload"]["state"], "DUPLICATE_IGNORED")
        self.assertEqual(second[0]["payload"]["metrics"]["reason_code"], "TASK_DUPLICATE")
        self.assertEqual(second[0]["payload"]["metrics"]["task_id"], event["payload"]["task_id"])
        self.assertEqual(second[0]["payload"]["metrics"]["original_event_id"], event["event"]["event_id"])


if __name__ == "__main__":
    unittest.main()
