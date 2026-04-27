import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VALIDATORS_PATH = ROOT / "gateway" / "src" / "validators.py"
spec = importlib.util.spec_from_file_location("zmeta_validators", VALIDATORS_PATH)
validators = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validators)


def event_for(producer, event_type, event_subtype):
    return {
        "event": {
            "event_type": event_type,
            "event_subtype": event_subtype,
        },
        "source": {
            "platform_id": "test-platform",
            "node_role": "GATEWAY",
            "producer": producer,
        },
        "payload": {},
    }


class ProducerAuthorityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = validators.load_policy(ROOT / "policy")
        cls.severity_map = cls.policy["violation_severities"]
        cls.authority = cls.policy["producer_authority"]
        cls.routing = cls.policy["routing"]

    def assert_authorized(self, producer, event_type, event_subtype):
        ok, violations = validators.validate_producer_authority(
            event_for(producer, event_type, event_subtype),
            self.authority,
            self.severity_map,
        )
        self.assertTrue(ok, violations)
        self.assertEqual([], violations)

    def assert_rejected(self, producer, event_type, event_subtype):
        ok, violations = validators.validate_producer_authority(
            event_for(producer, event_type, event_subtype),
            self.authority,
            self.severity_map,
        )
        self.assertFalse(ok)
        self.assertEqual("PRODUCER_NOT_ALLOWED", violations[0]["code"])

    def test_rf_sensor_observation_passes(self):
        self.assert_authorized("rf-sensor-01", "OBSERVATION_EVENT", "RF")

    def test_rf_sensor_fusion_fails(self):
        self.assert_rejected("rf-sensor-01", "FUSION_EVENT", "TRACK_FUSION")

    def test_classifier_inference_passes(self):
        self.assert_authorized("classifier-main", "INFERENCE_EVENT", "CLASSIFICATION")

    def test_classifier_command_fails(self):
        self.assert_rejected("classifier-main", "COMMAND_EVENT", "GOTO")

    def test_fusion_event_passes_for_fusion_producer(self):
        self.assert_authorized("fusion-alpha", "FUSION_EVENT", "TRACK_FUSION")

    def test_fusion_observation_fails(self):
        self.assert_rejected("fusion-alpha", "OBSERVATION_EVENT", "RF")

    def test_comms_deconfliction_command_passes_authority_and_routing(self):
        event = event_for("comms-deconfliction-1", "COMMAND_EVENT", "GOTO")
        ok, violations = validators.validate_producer_authority(
            event,
            self.authority,
            self.severity_map,
        )
        self.assertTrue(ok, violations)

        ok, violations = validators.validate_routing(event, self.routing, self.severity_map)
        self.assertTrue(ok, violations)

    def test_unknown_producer_fails_when_event_type_requires_match(self):
        self.assert_rejected("unknown-producer", "STATE_EVENT", "TRACK_STATE")

    def test_legacy_reference_producers_remain_authorized(self):
        self.assert_authorized("torch", "INFERENCE_EVENT", "CLASSIFICATION")
        self.assert_authorized("torch", "FUSION_EVENT", "TRACK_FUSION")
        self.assert_authorized("sensorops", "COMMAND_EVENT", "GOTO")
        self.assert_authorized("sensorops", "SYSTEM_EVENT", "LINK_STATUS")


if __name__ == "__main__":
    unittest.main()
