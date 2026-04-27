import importlib.util
import unittest
from pathlib import Path

from zmeta_uuid import uuid7


ROOT = Path(__file__).resolve().parents[2]
VALIDATORS_PATH = ROOT / "gateway" / "src" / "validators.py"
spec = importlib.util.spec_from_file_location("zmeta_validators", VALIDATORS_PATH)
validators = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validators)


def schema_violation_event(reason_code, version="1.0"):
    return {
        "zmeta_version": version,
        "event": {
            "event_id": str(uuid7()),
            "event_type": "SYSTEM_EVENT",
            "event_subtype": "SCHEMA_VIOLATION",
            "ts": "2025-01-17T14:30:00Z",
        },
        "source": {
            "platform_id": "zmeta-gateway",
            "node_role": "GATEWAY",
            "producer": "zmeta-gateway",
        },
        "payload": {
            "system_type": "SCHEMA_VIOLATION",
            "state": "REJECTED",
            "metrics": {
                "reason_code": reason_code,
                "original_event_id": str(uuid7()),
            },
        },
    }


def task_ack_event(reason_code):
    return {
        "zmeta_version": "1.0",
        "event": {
            "event_id": str(uuid7()),
            "event_type": "SYSTEM_EVENT",
            "event_subtype": "TASK_ACK",
            "ts": "2025-01-17T14:30:00Z",
        },
        "source": {
            "platform_id": "zmeta-gateway",
            "node_role": "GATEWAY",
            "producer": "zmeta-gateway",
        },
        "payload": {
            "system_type": "TASK_ACK",
            "state": "FAILED",
            "metrics": {
                "task_id": "task-001",
                "original_event_id": str(uuid7()),
                "reason_code": reason_code,
            },
        },
    }


class ReasonCodeTest(unittest.TestCase):
    V1_1_ONLY_SCHEMA_VIOLATION_CODES = {
        "SENSOR_STATUS_STATE_MISMATCH",
        "PLATFORM_STATUS_POWER_MISSING",
    }

    @classmethod
    def setUpClass(cls):
        cls.validator = validators.load_schema(ROOT / "schema" / "zmeta-event.schema.json")
        cls.policy = validators.load_policy(ROOT / "policy")
        cls.severity_map = cls.policy["violation_severities"]
        cls.schema_violation_codes = cls.policy["semantics"]["system_event"][
            "schema_violation_allowed_reason_codes"
        ]

    def assert_schema_valid(self, event):
        errors = list(self.validator.iter_errors(event))
        self.assertEqual(errors, [])

    def assert_schema_invalid(self, event):
        errors = list(self.validator.iter_errors(event))
        self.assertNotEqual(errors, [])

    def test_all_policy_schema_violation_codes_validate_in_schema_and_semantics(self):
        for code in self.schema_violation_codes:
            with self.subTest(version="1.1.0", code=code):
                event = schema_violation_event(code, version="1.1.0")
                self.assert_schema_valid(event)

                ok, violations = validators.validate_semantics(
                    event, self.policy["semantics"], self.severity_map
                )
                self.assertTrue(ok, violations)
                self.assertEqual([], violations)

        for code in self.schema_violation_codes:
            event = schema_violation_event(code, version="1.0")
            with self.subTest(version="1.0", code=code):
                if code in self.V1_1_ONLY_SCHEMA_VIOLATION_CODES:
                    self.assert_schema_invalid(event)
                    continue

                self.assert_schema_valid(event)

                ok, violations = validators.validate_semantics(
                    event, self.policy["semantics"], self.severity_map
                )
                self.assertTrue(ok, violations)
                self.assertEqual([], violations)

    def test_unknown_schema_violation_code_fails_schema(self):
        self.assert_schema_invalid(schema_violation_event("NOT_A_REASON_CODE"))

    def test_task_ack_reason_codes_remain_task_limited(self):
        self.assert_schema_valid(task_ack_event("TASK_DUPLICATE"))
        self.assert_schema_invalid(task_ack_event("INVALID_GEO_FIELD"))
        self.assert_schema_invalid(task_ack_event("LINEAGE_PARENT_TYPE_INVALID"))

    def test_new_diagnostic_reason_codes_are_available_for_schema_violation(self):
        for code in (
            "VERSION_SEMANTICS_MISMATCH",
            "EVENT_SUBTYPE_MISMATCH",
            "INVALID_COMMAND_GEOMETRY",
            "INVALID_QUALITY_UNITS",
            "INVALID_GEO_FIELD",
            "RF_WINDOW_PAIRING_INVALID",
            "RF_WINDOW_MIDPOINT_INVALID",
            "LINEAGE_MISMATCH",
        ):
            with self.subTest(code=code):
                self.assert_schema_valid(schema_violation_event(code))

    def test_v1_1_only_diagnostic_codes_do_not_leak_into_v1_0(self):
        for code in self.V1_1_ONLY_SCHEMA_VIOLATION_CODES:
            with self.subTest(code=code):
                self.assert_schema_invalid(schema_violation_event(code, version="1.0"))
                self.assert_schema_valid(schema_violation_event(code, version="1.1.0"))


if __name__ == "__main__":
    unittest.main()
