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


def promotion_metadata(**overrides):
    metadata = {
        "state_category": "PROMOTED_EXTERNAL_STATE",
        "origin_kind": "EXTERNAL_REPORT",
        "projection_id": "cot",
        "promotion_policy_id": "PROMOTE-COT-STATE-V1",
        "trust_ref": "producer-authority:cot-ingress",
        "lineage_status": "EXTERNAL_SOURCE",
        "loop_status": "CHECKED_NOT_REFLECTION",
        "confidence_basis": "EXPLICIT_EXTERNAL_CONFIDENCE",
        "source_event_uid": "cot:external-1",
        "freshness_ms": 5000,
    }
    metadata.update(overrides)
    return metadata


def state_event(profile="H", metadata=None, transform="promote:cot@template:PROMOTE-COT-STATE-V1"):
    parent_id = str(uuid7())
    event = {
        "zmeta_version": "1.0",
        "event": {
            "event_id": str(uuid7()),
            "event_type": "STATE_EVENT",
            "event_subtype": "TRACK_STATE",
            "ts": "2025-01-17T14:30:00Z",
        },
        "source": {
            "platform_id": "cot-gateway-1",
            "node_role": "GATEWAY",
            "producer": "cot-ingress",
        },
        "profile": profile,
        "payload": {
            "track_id": "external-track-1",
            "geo": {"lat": 34.0, "lon": -118.0, "alt_m": 100.0},
            "valid_for_ms": 1000,
            "timing_quality": {
                "time_source": "GPS_PPS",
                "sync_state": "LOCKED",
                "est_error_ms": 1,
                "last_sync_ts": "2025-01-17T14:29:59Z",
            },
        },
        "confidence": 0.7,
        "lineage": {"based_on": [parent_id], "transform": transform},
    }
    if metadata is not None:
        event["payload"]["extensions"] = {"external_promotion": metadata}
    return event


class ExternalStatePromotionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = validators.load_policy(ROOT / "policy")
        cls.severity_map = cls.policy["violation_severities"]
        cls.authority = cls.policy["producer_authority"]
        cls.schema = validators.load_schema(ROOT / "schema" / "zmeta-event-1.0.schema.json")

    def validate_authority(self, event):
        return validators.validate_producer_authority(event, self.authority, self.severity_map)

    def authority_with_promotion_mode(self, mode, **overrides):
        authority = copy.deepcopy(self.authority)
        promotion = authority["external_state_promotion"]
        promotion["mode"] = mode
        promotion.update(overrides)
        return authority

    def test_external_state_requires_promotion_metadata(self):
        event = state_event(metadata=None)

        ok, violations = validators.validate_schema(event, self.schema, self.severity_map)
        self.assertTrue(ok, violations)

        ok, violations = self.validate_authority(event)

        self.assertFalse(ok)
        self.assertEqual("PRODUCER_NOT_ALLOWED", violations[0]["code"])
        self.assertEqual(
            "payload.extensions.external_promotion",
            violations[0]["details"]["metadata_path"],
        )

    def test_profile_l_allows_compact_promotion_handles(self):
        metadata = {
            "state_category": "PROMOTED_EXTERNAL_STATE",
            "promotion_policy_id": "PROMOTE-COT-STATE-V1",
            "trust_ref": "producer-authority:cot-ingress",
            "lineage_status": "UNRESOLVED_PROFILED",
            "loop_status": "CHECKED_NOT_REFLECTION",
        }
        event = state_event(profile="L", metadata=metadata)

        ok, violations = validators.validate_schema(event, self.schema, self.severity_map)
        self.assertTrue(ok, violations)

        ok, violations = self.validate_authority(event)

        self.assertTrue(ok, violations)
        self.assertEqual([], violations)

    def test_profile_h_requires_full_promotion_detail(self):
        metadata = {
            "state_category": "PROMOTED_EXTERNAL_STATE",
            "promotion_policy_id": "PROMOTE-COT-STATE-V1",
            "trust_ref": "producer-authority:cot-ingress",
            "lineage_status": "EXTERNAL_SOURCE",
            "loop_status": "CHECKED_NOT_REFLECTION",
        }
        event = state_event(profile="H", metadata=metadata)

        ok, violations = self.validate_authority(event)

        self.assertFalse(ok)
        self.assertEqual("PRODUCER_NOT_ALLOWED", violations[0]["code"])
        self.assertIn("source_event_uid", violations[0]["details"]["missing"])
        self.assertIn("freshness_ms", violations[0]["details"]["missing"])

    def test_external_state_loop_status_is_rejected(self):
        event = state_event(
            metadata=promotion_metadata(loop_status="REFLECTION_DETECTED")
        )

        ok, violations = self.validate_authority(event)

        self.assertFalse(ok)
        self.assertEqual("PRODUCER_NOT_ALLOWED", violations[0]["code"])
        self.assertEqual("REFLECTION_DETECTED", violations[0]["details"]["loop_status"])

    def test_external_state_requires_promotion_transform(self):
        event = state_event(
            metadata=promotion_metadata(),
            transform="translate:cot@template",
        )

        ok, violations = self.validate_authority(event)

        self.assertFalse(ok)
        self.assertEqual("PRODUCER_NOT_ALLOWED", violations[0]["code"])
        self.assertEqual("translate:cot@template", violations[0]["details"]["transform"])

    def test_warn_mode_reports_promotion_warning_without_rejecting(self):
        event = state_event(metadata=None)
        authority = self.authority_with_promotion_mode("warn")

        ok, violations = validators.validate_producer_authority(
            event, authority, self.severity_map
        )

        self.assertTrue(ok, violations)
        self.assertEqual("PRODUCER_NOT_ALLOWED", violations[0]["code"])
        self.assertEqual("warn", violations[0]["severity"])
        self.assertEqual("warn", violations[0]["details"]["policy_mode"])
        self.assertEqual("external_promotion", violations[0]["details"]["risk_dimension"])
        self.assertEqual("WARN_ACCEPT", violations[0]["details"]["policy_decision"])
        self.assertIn("COMMAND_BASIS", violations[0]["details"]["prohibited_uses"])
        self.assertNotIn("action", violations[0]["details"])

    def test_producer_rule_can_override_global_promotion_mode(self):
        event = state_event(metadata=None)
        authority = self.authority_with_promotion_mode("reject")
        authority["producers"]["cot-ingress"]["external_state_promotion"]["mode"] = "warn"

        ok, violations = validators.validate_producer_authority(
            event, authority, self.severity_map
        )

        self.assertTrue(ok, violations)
        self.assertEqual("warn", violations[0]["severity"])
        self.assertEqual("warn", violations[0]["details"]["policy_mode"])
        self.assertEqual("WARN_ACCEPT", violations[0]["details"]["policy_decision"])

    def test_degrade_mode_lowers_confidence_and_ttl(self):
        event = state_event(metadata=None)
        event["confidence"] = 0.8
        event["payload"]["valid_for_ms"] = 2000
        authority = self.authority_with_promotion_mode("degrade")

        ok, violations = validators.validate_producer_authority(
            event, authority, self.severity_map
        )
        changed = validators.apply_external_promotion_policy_action(
            event, violations, authority
        )

        self.assertTrue(ok, violations)
        self.assertTrue(changed)
        self.assertEqual("warn", violations[0]["severity"])
        self.assertEqual("degrade", violations[0]["details"]["action"])
        self.assertAlmostEqual(0.4, event["confidence"])
        self.assertEqual(1000, event["payload"]["valid_for_ms"])
        metadata = event["payload"]["extensions"]["external_promotion"]
        self.assertEqual("degrade", metadata["policy_mode"])
        self.assertEqual("DEGRADED_ACCEPT", metadata["policy_decision"])
        self.assertEqual("PRODUCER_NOT_ALLOWED", metadata["policy_reason_code"])
        risk = event["payload"]["extensions"]["risk_adjudication"][0]
        self.assertEqual("external_promotion", risk["risk_dimension"])
        self.assertEqual("PRODUCER_NOT_ALLOWED", risk["reason_code"])
        self.assertEqual("DEGRADED_ACCEPT", risk["policy_decision"])
        self.assertIn("FUSION_INPUT", risk["prohibited_uses"])
        self.assertEqual(
            {
                "confidence_reduction_factor": 2.0,
                "valid_for_ms_reduction_factor": 2.0,
            },
            risk["effects"],
        )

    def test_quarantine_mode_caps_confidence_and_ttl(self):
        event = state_event(
            metadata=promotion_metadata(),
            transform="translate:cot@template",
        )
        event["confidence"] = 0.8
        event["payload"]["valid_for_ms"] = 2000
        authority = self.authority_with_promotion_mode("quarantine")

        ok, violations = validators.validate_producer_authority(
            event, authority, self.severity_map
        )
        changed = validators.apply_external_promotion_policy_action(
            event, violations, authority
        )

        self.assertTrue(ok, violations)
        self.assertTrue(changed)
        self.assertEqual("warn", violations[0]["severity"])
        self.assertEqual("quarantine", violations[0]["details"]["action"])
        self.assertAlmostEqual(0.25, event["confidence"])
        self.assertEqual(1000, event["payload"]["valid_for_ms"])
        metadata = event["payload"]["extensions"]["external_promotion"]
        self.assertEqual("quarantine", metadata["policy_mode"])
        self.assertEqual("QUARANTINE_ACCEPT", metadata["policy_decision"])
        risk = event["payload"]["extensions"]["risk_adjudication"][0]
        self.assertEqual("QUARANTINE_ACCEPT", risk["policy_decision"])
        self.assertIn("AAR_ONLY", risk["allowed_uses"])
        self.assertEqual(
            {"confidence_cap": 0.25, "valid_for_ms_cap": 1000},
            risk["effects"],
        )

    def test_loop_risk_stays_rejected_by_default_in_warn_mode(self):
        event = state_event(
            metadata=promotion_metadata(loop_status="REFLECTION_DETECTED")
        )
        authority = self.authority_with_promotion_mode("warn")

        ok, violations = validators.validate_producer_authority(
            event, authority, self.severity_map
        )

        self.assertFalse(ok)
        self.assertEqual("fail", violations[0]["severity"])
        self.assertEqual("reject", violations[0]["details"]["policy_mode"])
        self.assertEqual("REJECTED", violations[0]["details"]["policy_decision"])

    def test_operator_can_explicitly_soften_loop_risk_guardrail(self):
        event = state_event(
            metadata=promotion_metadata(loop_status="REFLECTION_DETECTED")
        )
        authority = self.authority_with_promotion_mode(
            "warn", always_reject_loop_risk=False
        )

        ok, violations = validators.validate_producer_authority(
            event, authority, self.severity_map
        )

        self.assertTrue(ok, violations)
        self.assertEqual("warn", violations[0]["severity"])
        self.assertEqual("warn", violations[0]["details"]["policy_mode"])
        self.assertEqual("WARN_ACCEPT", violations[0]["details"]["policy_decision"])


if __name__ == "__main__":
    unittest.main()
