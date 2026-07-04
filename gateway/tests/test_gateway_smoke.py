import importlib.util
import json
import copy
import unittest
from zmeta_uuid import uuid7
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
                "event_id": str(uuid7()),
                "event_type": "STATE_EVENT",
                "event_subtype": "TRACK_STATE",
                "ts": "2025-01-17T14:32:10Z",
            },
            "source": {
                "platform_id": "platform-1",
                "node_role": "GATEWAY",
                "producer": "torch",
            },
            "payload": {
                "track_id": "track-1",
                "geo": {"lat": 40.0, "lon": -75.0, "alt_m": 120.5},
                "valid_for_ms": 1000,
            },
            "confidence": 0.9,
            "lineage": {"based_on": [str(uuid7())]},
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
                "event_id": str(uuid7()),
                "event_type": "OBSERVATION_EVENT",
                "event_subtype": "RF",
                "ts": "2025-01-17T14:32:10Z",
            },
            "source": {
                "platform_id": "platform-1",
                "node_role": "EDGE",
                "producer": "sensorops",
            },
            "payload": {
                "modality": "RF",
                "features": {
                    "center_freq_hz": 2450000000,
                    "bandwidth_hz": 20000000,
                    "power_dbm": -35.2,
                },
                "track_id": "track-1",
            },
        }

        ok, violations = validators.validate_schema(event, self.validator, self.policy["violation_severities"])
        self.assertFalse(ok)
        self.assertEqual(violations[0]["code"], "SCHEMA_INVALID")
        ok, violations = validators.validate_semantics(event, self.policy["semantics"], self.policy["violation_severities"])
        self.assertFalse(ok)
        self.assertEqual(violations[0]["code"], "OBSERVATION_HAS_IDENTITY")

    def test_state_with_features_is_schema_rejected(self):
        event = {
            "zmeta_version": "1.0",
            "event": {
                "event_id": str(uuid7()),
                "event_type": "STATE_EVENT",
                "event_subtype": "TRACK_STATE",
                "ts": "2025-01-17T14:32:10Z",
            },
            "source": {
                "platform_id": "fusion-node-01",
                "node_role": "GATEWAY",
                "producer": "torch",
            },
            "payload": {
                "track_id": "track-1",
                "geo": {"lat": 40.0, "lon": -75.0, "alt_m": 120.5},
                "features": {"center_freq_hz": 2450000000},
                "valid_for_ms": 1000,
            },
            "confidence": 0.9,
            "lineage": {"based_on": [str(uuid7())]},
        }

        ok, violations = validators.validate_schema(event, self.validator, self.policy["violation_severities"])
        self.assertFalse(ok)
        self.assertEqual(violations[0]["code"], "SCHEMA_INVALID")

    def test_state_with_nested_raw_features_is_semantically_rejected(self):
        # raw_features buried >=2 levels deep is schema-valid (extensions is
        # additionalProperties:true), so it slips past the schema and must be
        # caught by the recursive semantic check. The former top-level-only
        # STATE check would have missed this laundering path.
        event = {
            "zmeta_version": "1.0",
            "event": {
                "event_id": str(uuid7()),
                "event_type": "STATE_EVENT",
                "event_subtype": "TRACK_STATE",
                "ts": "2025-01-17T14:32:10Z",
            },
            "source": {
                "platform_id": "fusion-node-01",
                "node_role": "GATEWAY",
                "producer": "torch",
            },
            "payload": {
                "track_id": "track-1",
                "geo": {"lat": 40.0, "lon": -75.0, "alt_m": 120.5},
                "valid_for_ms": 1000,
                "extensions": {"render": {"raw_features": {"center_freq_hz": 2450000000}}},
            },
            "confidence": 0.9,
            "lineage": {"based_on": [str(uuid7())]},
        }

        ok, violations = validators.validate_schema(event, self.validator, self.policy["violation_severities"])
        self.assertTrue(ok)
        ok, violations = validators.validate_semantics(event, self.policy["semantics"], self.policy["violation_severities"])
        self.assertFalse(ok)
        self.assertEqual(violations[0]["code"], "STATE_HAS_RAW_FEATURES")
        self.assertEqual(violations[0]["details"]["field"], "raw_features")
        self.assertEqual(violations[0]["details"]["path"], "extensions/render/raw_features")

    def test_command_with_nested_altitude_is_semantically_rejected(self):
        # alt_hae_m buried in a free-form extension object is schema-valid but
        # must be rejected: COMMAND_EVENT SHALL NOT specify altitude at any
        # depth; the receiving autonomy deconflicts vertical internally.
        event = {
            "zmeta_version": "1.0",
            "event": {
                "event_id": str(uuid7()),
                "event_type": "COMMAND_EVENT",
                "event_subtype": "GOTO",
                "ts": "2025-01-17T14:32:10Z",
            },
            "source": {
                "platform_id": "gateway-node-01",
                "node_role": "GATEWAY",
                "producer": "sensorops",
            },
            "payload": {
                "task_id": "task-1",
                "task_type": "GOTO",
                "target_geo": {"lat": 40.0, "lon": -75.0},
                "valid_for_ms": 60000,
                "requires_deconfliction": True,
                "extensions": {"waypoint": {"alt_hae_m": 120.0}},
                "timing_quality": {
                    "time_source": "GPS_PPS",
                    "sync_state": "LOCKED",
                    "est_error_ms": 1,
                    "last_sync_ts": "2025-01-17T14:29:59Z",
                },
            },
        }

        ok, violations = validators.validate_schema(event, self.validator, self.policy["violation_severities"])
        self.assertTrue(ok)
        ok, violations = validators.validate_semantics(event, self.policy["semantics"], self.policy["violation_severities"])
        self.assertFalse(ok)
        self.assertEqual(violations[0]["code"], "COMMAND_HAS_ALTITUDE")
        self.assertEqual(violations[0]["details"]["field"], "alt_hae_m")

    def test_rf_window_midpoint_mismatch_is_rejected(self):
        event = {
            "zmeta_version": "1.0",
            "event": {
                "event_id": str(uuid7()),
                "event_type": "OBSERVATION_EVENT",
                "event_subtype": "RF",
                "ts": "2025-01-17T14:32:11Z",
            },
            "source": {
                "platform_id": "sensor-node-01",
                "node_role": "EDGE",
                "producer": "sensorops",
            },
            "payload": {
                "modality": "RF",
                "features": {
                    "center_freq_hz": 2450000000,
                    "bandwidth_hz": 20000000,
                    "power_dbm": -35.2,
                },
                "t_start": "2025-01-17T14:32:09Z",
                "t_end": "2025-01-17T14:32:11Z",
                "timing_quality": {
                    "time_source": "GPS_PPS",
                    "sync_state": "LOCKED",
                    "est_error_ms": 1,
                    "last_sync_ts": "2025-01-17T14:29:59Z",
                },
            },
        }

        ok, violations = validators.validate_schema(event, self.validator, self.policy["violation_severities"])
        self.assertTrue(ok)
        ok, violations = validators.validate_semantics(event, self.policy["semantics"], self.policy["violation_severities"])
        self.assertFalse(ok)
        self.assertEqual(violations[0]["code"], "RF_WINDOW_MIDPOINT_MISMATCH")

    def test_profile_l_rejects_observation_event(self):
        event = {
            "zmeta_version": "1.0",
            "event": {
                "event_id": str(uuid7()),
                "event_type": "OBSERVATION_EVENT",
                "event_subtype": "RF",
                "ts": "2025-01-17T14:32:10Z",
            },
            "source": {
                "platform_id": "sensor-node-01",
                "node_role": "EDGE",
                "producer": "rf-sensor",
            },
            "payload": {
                "modality": "RF",
                "features": {
                    "center_freq_hz": 2450000000,
                    "bandwidth_hz": 20000000,
                    "power_dbm": -35.2,
                },
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
                "event_id": str(uuid7()),
                "event_type": "FUSION_EVENT",
                "event_subtype": "TRACK_FUSION",
                "ts": "2025-01-17T14:32:10Z",
            },
            "source": {
                "platform_id": "edge-node-01",
                "node_role": "EDGE",
                "producer": "torch",
            },
            "payload": {
                "track_id": "track-1",
                "members": [str(uuid7())],
                "stability": 0.5,
                "last_seen_ts": "2025-01-17T14:32:09Z",
            },
            "confidence": 0.8,
            "lineage": {"based_on": [str(uuid7())]},
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
                "event_id": str(uuid7()),
                "event_type": "COMMAND_EVENT",
                "event_subtype": "GOTO",
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

    def test_task_ack_missing_reason_code_severity(self):
        event = {
            "zmeta_version": "1.0",
            "event": {
                "event_id": str(uuid7()),
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
                "state": "FAILED",
                "metrics": {
                    "task_id": "task-1",
                    "original_event_id": str(uuid7()),
                },
            },
        }

        ok, violations = validators.validate_schema(event, self.validator, self.policy["violation_severities"])
        self.assertFalse(ok)
        self.assertEqual(violations[0]["code"], "SCHEMA_INVALID")

    def test_command_event_deduped(self):
        event = {
            "zmeta_version": "1.0",
            "event": {
                "event_id": str(uuid7()),
                "event_type": "COMMAND_EVENT",
                "event_subtype": "GOTO",
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

        first = gateway.process_message(raw, self.validator, self.policy, "L", dedupe_cache, "json")
        self.assertEqual(len(first), 1)
        self.assertEqual(first[0]["event"]["event_type"], "COMMAND_EVENT")

        second = gateway.process_message(raw, self.validator, self.policy, "L", dedupe_cache, "json")
        self.assertEqual(len(second), 1)
        self.assertEqual(second[0]["event"]["event_type"], "SYSTEM_EVENT")
        self.assertEqual(second[0]["event"]["event_subtype"], "TASK_ACK")
        self.assertEqual(second[0]["payload"]["system_type"], "TASK_ACK")
        self.assertEqual(second[0]["payload"]["state"], "DUPLICATE_IGNORED")
        self.assertEqual(second[0]["payload"]["metrics"]["reason_code"], "TASK_DUPLICATE")
        self.assertEqual(second[0]["payload"]["metrics"]["task_id"], event["payload"]["task_id"])
        self.assertEqual(second[0]["payload"]["metrics"]["original_event_id"], event["event"]["event_id"])

    def test_external_promotion_degrade_mode_forwards_warning(self):
        policy = copy.deepcopy(self.policy)
        policy["producer_authority"]["external_state_promotion"]["mode"] = "degrade"
        event = {
            "zmeta_version": "1.0",
            "event": {
                "event_id": str(uuid7()),
                "event_type": "STATE_EVENT",
                "event_subtype": "TRACK_STATE",
                "ts": "2025-01-17T15:05:00Z",
            },
            "source": {
                "platform_id": "cot-gateway-1",
                "node_role": "GATEWAY",
                "producer": "cot-ingress",
            },
            "profile": "H",
            "payload": {
                "track_id": "external-track-1",
                "geo": {"lat": 34.0, "lon": -118.0, "alt_m": 100.0},
                "valid_for_ms": 2000,
                "timing_quality": {
                    "time_source": "GPS_PPS",
                    "sync_state": "LOCKED",
                    "est_error_ms": 1,
                    "last_sync_ts": "2025-01-17T15:04:59Z",
                },
            },
            "confidence": 0.8,
            "lineage": {
                "based_on": [str(uuid7())],
                "transform": "promote:cot@template:PROMOTE-COT-STATE-V1",
            },
        }

        outgoing = gateway.process_message(
            json.dumps(event).encode("utf-8"),
            self.validator,
            policy,
            "H",
            None,
            "json",
        )

        self.assertEqual(2, len(outgoing))
        self.assertEqual("STATE_EVENT", outgoing[0]["event"]["event_type"])
        self.assertAlmostEqual(0.4, outgoing[0]["confidence"])
        self.assertEqual(1000, outgoing[0]["payload"]["valid_for_ms"])
        metadata = outgoing[0]["payload"]["extensions"]["external_promotion"]
        self.assertEqual("DEGRADED_ACCEPT", metadata["policy_decision"])
        risk = outgoing[0]["payload"]["extensions"]["risk_adjudication"][0]
        self.assertEqual("external_promotion", risk["risk_dimension"])
        self.assertEqual("DEGRADED_ACCEPT", risk["policy_decision"])
        self.assertIn("COMMAND_BASIS", risk["prohibited_uses"])
        self.assertEqual("SYSTEM_EVENT", outgoing[1]["event"]["event_type"])
        self.assertEqual("WARNING", outgoing[1]["payload"]["state"])
        self.assertEqual(
            "PRODUCER_NOT_ALLOWED",
            outgoing[1]["payload"]["metrics"]["reason_code"],
        )
        self.assertEqual(
            "external_promotion",
            outgoing[1]["payload"]["metrics"]["risk_dimension"],
        )
        self.assertEqual(
            "DEGRADED_ACCEPT",
            outgoing[1]["payload"]["metrics"]["policy_decision"],
        )

    def test_failure_mode_timing_loss_stamps_risk_adjudication(self):
        timing_state = validators.ValidationState()
        timing_state.record_timing(
            {
                "zmeta_version": "1.0",
                "event": {
                    "event_id": str(uuid7()),
                    "event_type": "SYSTEM_EVENT",
                    "event_subtype": "TIME_STATUS",
                    "ts": "2025-01-17T15:04:59Z",
                },
                "source": {
                    "platform_id": "fusion-node-01",
                    "node_role": "GATEWAY",
                    "producer": "fusion-engine",
                },
                "payload": {
                    "system_type": "TIME_STATUS",
                    "state": "UNSYNCED",
                    "metrics": {
                        "time_source": "GPS_PPS",
                        "sync_state": "UNSYNCED",
                        "est_error_ms": 500,
                        "last_sync_ts": "2025-01-17T15:04:00Z",
                    },
                },
            }
        )
        event = {
            "zmeta_version": "1.0",
            "event": {
                "event_id": str(uuid7()),
                "event_type": "STATE_EVENT",
                "event_subtype": "TRACK_STATE",
                "ts": "2025-01-17T15:05:00Z",
            },
            "source": {
                "platform_id": "fusion-node-01",
                "node_role": "GATEWAY",
                "producer": "fusion-engine",
            },
            "profile": "L",
            "payload": {
                "track_id": "track-1",
                "geo": {"lat": 34.0, "lon": -118.0, "alt_m": 100.0},
                "valid_for_ms": 1000,
            },
            "confidence": 0.8,
            "lineage": {"based_on": [str(uuid7())]},
        }

        changed = gateway._apply_failure_mode_degradation(
            event,
            {"timing_loss": {"enabled": True, "confidence_reduction_factor": 2.0}},
            timing_state,
            self.policy["timing_freshness"],
        )

        self.assertTrue(changed)
        self.assertAlmostEqual(0.4, event["confidence"])
        risk = event["payload"]["extensions"]["risk_adjudication"][0]
        self.assertEqual("timing", risk["risk_dimension"])
        self.assertEqual("TIMING_STATUS_UNSYNCED", risk["reason_code"])
        self.assertEqual("DEGRADED_ACCEPT", risk["policy_decision"])
        self.assertIn("COMMAND_BASIS", risk["prohibited_uses"])

    def test_cot_skip_reason_reports_missing_track_id(self):
        event = {
            "event": {
                "event_id": str(uuid7()),
                "event_type": "STATE_EVENT",
                "event_subtype": "TRACK_STATE",
                "ts": "2025-01-17T15:05:00Z",
            },
            "source": {
                "platform_id": "fusion-node-01",
                "node_role": "GATEWAY",
                "producer": "torch",
            },
            "payload": {
                "geo": {"lat": 34.0, "lon": -118.0, "alt_m": 100.0},
                "valid_for_ms": 1000,
            },
        }

        self.assertEqual("MISSING_TRACK_ID", gateway._cot_skip_reason(event))

    def test_cot_skip_metric_records_reason(self):
        metrics = gateway.GatewayMetrics(interval_sec=30, emit=False)

        metrics.record_cot_skipped(
            "MISSING_TRACK_ID",
            event_id="019c2b5c-c051-70e1-b6aa-34bf14c8a999",
            producer="torch",
        )

        self.assertEqual(1, metrics.window["cot_skipped"])
        self.assertEqual(1, metrics.total["cot_skipped"])
        self.assertEqual(1, metrics.window["cot_skip_reasons"]["MISSING_TRACK_ID"])

    def test_timing_quality_metrics_distinguish_source_and_fallback(self):
        metrics = gateway.GatewayMetrics(interval_sec=30, emit=False)

        metrics.record_timing_quality(
            "GPS_PPS",
            "LOCKED",
            event_id="019c2b5c-c051-70e1-b6aa-34bf14c8a998",
            producer="torch",
        )
        metrics.record_timing_quality(
            "UNKNOWN",
            "UNSYNCED",
            event_id="019c2b5c-c051-70e1-b6aa-34bf14c8a999",
            producer="torch",
        )

        self.assertEqual(1, metrics.window["timing_quality_source"])
        self.assertEqual(1, metrics.total["timing_quality_source"])
        self.assertEqual(1, metrics.window["timing_quality_fallback"])
        self.assertEqual(1, metrics.total["timing_quality_fallback"])
        self.assertEqual(1, metrics.window["timing_quality_modes"]["GPS_PPS/LOCKED"])
        self.assertEqual(1, metrics.window["timing_quality_modes"]["UNKNOWN/UNSYNCED"])

    def test_gateway_cbor_prefers_builtin_when_cbor2_is_present(self):
        class ExplodingCbor2:
            @staticmethod
            def dumps(*_args, **_kwargs):
                raise AssertionError("gateway should prefer zmeta_cbor for deterministic CBOR")

            @staticmethod
            def loads(*_args, **_kwargs):
                raise AssertionError("gateway should prefer zmeta_cbor for deterministic CBOR")

        original_cbor2 = gateway.cbor2
        try:
            gateway.cbor2 = ExplodingCbor2
            sample = {"b": 1, "a": 2.0, "nested": {"z": True, "y": None}}

            encoded = gateway._encode_cbor(sample)
            decoded = gateway._decode_cbor(encoded)

            self.assertEqual(sample, decoded)
        finally:
            gateway.cbor2 = original_cbor2


if __name__ == "__main__":
    unittest.main()
