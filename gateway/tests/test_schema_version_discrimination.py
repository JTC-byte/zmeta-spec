import json
import importlib.util
import unittest
from copy import deepcopy
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012
from zmeta_uuid import uuid7


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = ROOT / "schema"
VALIDATORS_PATH = ROOT / "gateway" / "src" / "validators.py"
spec = importlib.util.spec_from_file_location("zmeta_validators", VALIDATORS_PATH)
validators = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validators)


def load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def load_unified_validator():
    schema_v1_0 = load_json(SCHEMA_DIR / "zmeta-event-1.0.schema.json")
    schema_v1_1_0 = load_json(SCHEMA_DIR / "zmeta-event-1.1.0.schema.json")
    unified_schema = load_json(SCHEMA_DIR / "zmeta-event.schema.json")

    registry = Registry().with_resources(
        [
            (
                schema_v1_0["$id"],
                Resource.from_contents(schema_v1_0, default_specification=DRAFT202012),
            ),
            (
                schema_v1_1_0["$id"],
                Resource.from_contents(schema_v1_1_0, default_specification=DRAFT202012),
            ),
        ]
    )
    return Draft202012Validator(
        unified_schema,
        registry=registry,
        format_checker=FormatChecker(),
    )


def valid_rf_observation(version="1.0"):
    return {
        "zmeta_version": version,
        "event": {
            "event_id": str(uuid7()),
            "event_type": "OBSERVATION_EVENT",
            "event_subtype": "RF",
            "ts": "2025-01-17T14:32:10Z",
        },
        "source": {
            "platform_id": "sensor-node-01",
            "node_role": "EDGE",
            "producer": "sensorops",
        },
        "profile": "H",
        "payload": {
            "modality": "RF",
            "features": {
                "center_freq_hz": 2450000000,
                "bandwidth_hz": 20000000,
                "power_dbm": -35.2,
            },
            "timing_quality": {
                "time_source": "GPS_PPS",
                "sync_state": "LOCKED",
                "est_error_ms": 1,
                "last_sync_ts": "2025-01-17T14:29:59Z",
            },
        },
    }


def valid_acoustic_observation(version="1.1.0"):
    return {
        "zmeta_version": version,
        "event": {
            "event_id": str(uuid7()),
            "event_type": "OBSERVATION_EVENT",
            "event_subtype": "ACOUSTIC",
            "ts": "2025-01-17T14:32:10Z",
        },
        "source": {
            "platform_id": "mic-node-01",
            "node_role": "EDGE",
            "producer": "acoustic-sensor",
        },
        "profile": "H",
        "payload": {
            "modality": "ACOUSTIC",
            "features": {
                "center_freq_hz": 2500.0,
                "spl_db": 72.3,
            },
            "timing_quality": {
                "time_source": "GPS_PPS",
                "sync_state": "LOCKED",
                "est_error_ms": 1,
                "last_sync_ts": "2025-01-17T14:29:59Z",
            },
        },
    }


def valid_eo_observation(version="1.1.0"):
    return {
        "zmeta_version": version,
        "event": {
            "event_id": str(uuid7()),
            "event_type": "OBSERVATION_EVENT",
            "event_subtype": "EO",
            "ts": "2025-01-17T14:32:10Z",
        },
        "source": {
            "platform_id": "camera-node-01",
            "node_role": "EDGE",
            "producer": "eo-camera",
            "sensor_id": "cam-01",
        },
        "profile": "H",
        "payload": {
            "modality": "EO",
            "features": {
                "roi_px": {"x": 320, "y": 180, "w": 64, "h": 48},
                "resolution_px": {"width": 1280, "height": 720},
            },
            "timing_quality": {
                "time_source": "GPS_PPS",
                "sync_state": "LOCKED",
                "est_error_ms": 1,
                "last_sync_ts": "2025-01-17T14:29:59Z",
            },
        },
    }


def system_status(system_type, state, metrics, version="1.1.0"):
    return {
        "zmeta_version": version,
        "event": {
            "event_id": str(uuid7()),
            "event_type": "SYSTEM_EVENT",
            "event_subtype": system_type,
            "ts": "2025-01-17T14:32:10Z",
        },
        "source": {
            "platform_id": "gateway-01",
            "node_role": "GATEWAY",
            "producer": "sensorops",
        },
        "profile": "H",
        "payload": {
            "system_type": system_type,
            "state": state,
            "metrics": metrics,
        },
    }


def command_event(task_type, payload_updates=None, version="1.1.0"):
    payload = {
        "task_id": f"task-{task_type.lower()}",
        "task_type": task_type,
        "valid_for_ms": 60000,
        "requires_deconfliction": True,
    }
    if payload_updates:
        payload.update(payload_updates)

    return {
        "zmeta_version": version,
        "event": {
            "event_id": str(uuid7()),
            "event_type": "COMMAND_EVENT",
            "event_subtype": task_type,
            "ts": "2025-01-17T14:32:10Z",
        },
        "source": {
            "platform_id": "gateway-01",
            "node_role": "GATEWAY",
            "producer": "sensorops",
        },
        "profile": "H",
        "payload": payload,
    }


def inference_event(inference_type, version="1.0"):
    parent_id = str(uuid7())
    return {
        "zmeta_version": version,
        "event": {
            "event_id": str(uuid7()),
            "event_type": "INFERENCE_EVENT",
            "event_subtype": inference_type,
            "ts": "2025-01-17T14:32:10Z",
        },
        "source": {
            "platform_id": "analytics-01",
            "node_role": "GATEWAY",
            "producer": "torch",
        },
        "profile": "H",
        "payload": {
            "inference_type": inference_type,
            "claim": {"label": "test"},
            "model": {"name": "test-model", "version": "1.0.0"},
            "based_on": [parent_id],
        },
        "confidence": 0.75,
        "lineage": {"based_on": [parent_id]},
    }


def fusion_event(version="1.0"):
    parent_id = str(uuid7())
    return {
        "zmeta_version": version,
        "event": {
            "event_id": str(uuid7()),
            "event_type": "FUSION_EVENT",
            "event_subtype": "TRACK_FUSION",
            "ts": "2025-01-17T14:32:10Z",
        },
        "source": {
            "platform_id": "fusion-01",
            "node_role": "GATEWAY",
            "producer": "torch",
        },
        "profile": "H",
        "payload": {
            "track_id": "track-test-001",
            "members": [parent_id],
            "stability": 0.6,
            "last_seen_ts": "2025-01-17T14:32:09Z",
        },
        "confidence": 0.7,
        "lineage": {"based_on": [parent_id]},
    }


def state_event(version="1.0"):
    parent_id = str(uuid7())
    return {
        "zmeta_version": version,
        "event": {
            "event_id": str(uuid7()),
            "event_type": "STATE_EVENT",
            "event_subtype": "TRACK_STATE",
            "ts": "2025-01-17T14:32:10Z",
        },
        "source": {
            "platform_id": "fusion-01",
            "node_role": "GATEWAY",
            "producer": "torch",
        },
        "profile": "H",
        "payload": {
            "track_id": "track-test-001",
            "geo": {"lat": 34.0, "lon": -118.0, "alt_m": 100.0},
            "valid_for_ms": 1000,
        },
        "confidence": 0.7,
        "lineage": {"based_on": [parent_id]},
    }


def valid_v1_0_system_event(system_type):
    metrics_by_type = {
        "LINK_STATUS": {
            "link_id": "mesh-01",
            "latency_ms": 10,
            "packet_loss_pct": 0,
            "throughput_bps": 1000000,
        },
        "TIME_STATUS": {
            "time_source": "GPS_PPS",
            "sync_state": "LOCKED",
            "est_error_ms": 1,
            "last_sync_ts": "2025-01-17T14:29:59Z",
        },
        "SCHEMA_VIOLATION": {
            "reason_code": "SCHEMA_INVALID",
            "original_event_id": str(uuid7()),
        },
        "TASK_ACK": {
            "task_id": "task-001",
            "original_event_id": str(uuid7()),
        },
    }
    state_by_type = {
        "LINK_STATUS": "UP",
        "TIME_STATUS": "LOCKED",
        "SCHEMA_VIOLATION": "REJECTED",
        "TASK_ACK": "RECEIVED",
    }
    return system_status(system_type, state_by_type[system_type], metrics_by_type[system_type], version="1.0")


class SchemaVersionDiscriminationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.validator = load_unified_validator()

    def assert_valid(self, event):
        errors = list(self.validator.iter_errors(event))
        self.assertEqual(errors, [])

    def assert_invalid(self, event):
        errors = list(self.validator.iter_errors(event))
        self.assertNotEqual(errors, [])

    def test_v1_0_rf_observation_passes(self):
        self.assert_valid(valid_rf_observation("1.0"))

    def test_utc_z_timestamp_passes(self):
        for version in ["1.0", "1.1.0"]:
            event = valid_rf_observation(version)
            event["event"]["ts"] = "2025-01-17T14:30:00Z"

            self.assert_valid(event)

    def test_utc_z_fractional_timestamp_passes(self):
        for version in ["1.0", "1.1.0"]:
            event = valid_rf_observation(version)
            event["event"]["ts"] = "2025-01-17T14:30:00.123Z"

            self.assert_valid(event)

    def test_timestamp_with_offset_fails(self):
        for version in ["1.0", "1.1.0"]:
            event = valid_rf_observation(version)
            event["event"]["ts"] = "2025-01-17T09:30:00-05:00"

            self.assert_invalid(event)

    def test_timestamp_without_timezone_fails(self):
        for version in ["1.0", "1.1.0"]:
            event = valid_rf_observation(version)
            event["event"]["ts"] = "2025-01-17T14:30:00"

            self.assert_invalid(event)

    def test_invalid_timestamp_string_fails(self):
        for version in ["1.0", "1.1.0"]:
            event = valid_rf_observation(version)
            event["event"]["ts"] = "not-a-timestamp"

            self.assert_invalid(event)

    def test_nested_timestamps_require_utc_z(self):
        event = valid_rf_observation("1.0")
        event["payload"]["timing_quality"]["last_sync_ts"] = "2025-01-17T09:29:59-05:00"

        self.assert_invalid(event)

        event = command_event(
            "GOTO",
            {
                "target_geo": {"lat": 34.0, "lon": -118.0},
                "valid_from_ts": "2025-01-17T09:30:00-05:00",
            },
            version="1.0",
        )

        self.assert_invalid(event)

    def test_rf_observation_without_window_passes(self):
        for version in ["1.0", "1.1.0"]:
            event = valid_rf_observation(version)

            self.assert_valid(event)

    def test_rf_observation_with_complete_window_passes(self):
        for version in ["1.0", "1.1.0"]:
            event = valid_rf_observation(version)
            event["event"]["ts"] = "2025-01-17T14:32:10Z"
            event["payload"]["t_start"] = "2025-01-17T14:32:09Z"
            event["payload"]["t_end"] = "2025-01-17T14:32:11Z"

            self.assert_valid(event)

    def test_rf_observation_with_only_t_start_fails(self):
        for version in ["1.0", "1.1.0"]:
            event = valid_rf_observation(version)
            event["payload"]["t_start"] = "2025-01-17T14:32:09Z"

            self.assert_invalid(event)

    def test_rf_observation_with_only_t_end_fails(self):
        for version in ["1.0", "1.1.0"]:
            event = valid_rf_observation(version)
            event["payload"]["t_end"] = "2025-01-17T14:32:11Z"

            self.assert_invalid(event)

        event = valid_rf_observation("1.1.0")
        event["payload"]["data_ref"] = {
            "ref_id": "capture-001",
            "t_start": "2025-01-17T09:29:58-05:00",
        }

        self.assert_invalid(event)

    def test_profile_l_allows_state_system_and_command(self):
        event = state_event()
        event["profile"] = "L"
        self.assert_valid(event)

        event = valid_v1_0_system_event("TIME_STATUS")
        event["profile"] = "L"
        self.assert_valid(event)

        event = command_event("GOTO", {"target_geo": {"lat": 34.0, "lon": -118.0}}, version="1.0")
        event["profile"] = "L"
        self.assert_valid(event)

    def test_profile_l_rejects_observation_inference_and_fusion(self):
        event = valid_rf_observation("1.0")
        event["profile"] = "L"
        self.assert_invalid(event)

        event = inference_event("CLASSIFICATION")
        event["profile"] = "L"
        self.assert_invalid(event)

        event = fusion_event()
        event["profile"] = "L"
        self.assert_invalid(event)

    def test_profile_m_rejects_inference_event(self):
        event = inference_event("CLASSIFICATION")
        event["profile"] = "M"

        self.assert_invalid(event)

    def test_profile_m_allows_profile_m_export_types(self):
        events = [
            valid_rf_observation("1.0"),
            fusion_event(),
            state_event(),
            valid_v1_0_system_event("LINK_STATUS"),
            command_event("GOTO", {"target_geo": {"lat": 34.0, "lon": -118.0}}, version="1.0"),
        ]
        for event in events:
            event["profile"] = "M"
            self.assert_valid(event)

    def test_profile_h_allows_all_valid_event_types(self):
        events = [
            valid_rf_observation("1.0"),
            inference_event("CLASSIFICATION"),
            fusion_event(),
            state_event(),
            command_event("GOTO", {"target_geo": {"lat": 34.0, "lon": -118.0}}, version="1.0"),
            valid_v1_0_system_event("TASK_ACK"),
        ]
        for event in events:
            event["profile"] = "H"
            self.assert_valid(event)

    def test_omitted_profile_does_not_apply_export_restrictions(self):
        event = inference_event("CLASSIFICATION")
        event.pop("profile", None)

        self.assert_valid(event)

    def test_valid_v1_0_observation_subtypes_pass(self):
        for modality in ["RF", "EO", "IR", "ACOUSTIC", "NETWORK"]:
            event = deepcopy(valid_rf_observation("1.0"))
            event["event"]["event_subtype"] = modality
            event["payload"]["modality"] = modality
            if modality != "RF":
                event["payload"]["features"] = {}

            self.assert_valid(event)

    def test_v1_0_generic_observation_features_do_not_adopt_v1_1_contracts(self):
        event = deepcopy(valid_rf_observation("1.0"))
        event["event"]["event_subtype"] = "EO"
        event["payload"]["modality"] = "EO"
        event["payload"]["features"] = {"bbox": {"x": 320, "y": 180, "w": 64, "h": 48}}

        self.assert_valid(event)

        event["zmeta_version"] = "1.1.0"
        self.assert_invalid(event)

        event = deepcopy(valid_rf_observation("1.0"))
        event["event"]["event_subtype"] = "ACOUSTIC"
        event["payload"]["modality"] = "ACOUSTIC"
        event["payload"]["features"] = {"source_type": "rotor"}

        self.assert_valid(event)

        event["zmeta_version"] = "1.1.0"
        self.assert_invalid(event)

    def test_v1_0_generic_quality_and_data_refs_do_not_adopt_v1_1_contracts(self):
        event = valid_rf_observation("1.0")
        event["payload"]["quality"] = {
            "measurement_error": 8.5,
            "error_metric": "1_SIGMA",
        }
        event["payload"]["data_ref"] = {
            "ref_id": "capture-001",
            "raw_blob": "AAEC",
        }

        self.assert_valid(event)

        event["zmeta_version"] = "1.1.0"
        self.assert_invalid(event)

    def test_valid_v1_0_inference_subtypes_pass(self):
        for inference_type in ["CLASSIFICATION", "ASSOCIATION", "ANOMALY", "BEHAVIOR"]:
            self.assert_valid(inference_event(inference_type))

    def test_valid_classification_inference_claim_passes(self):
        event = inference_event("CLASSIFICATION")
        event["payload"]["claim"] = {
            "class_name": "vehicle",
            "score": 0.82,
        }

        self.assert_valid(event)

    def test_v1_1_acoustic_observation_with_measured_features_passes(self):
        event = valid_acoustic_observation("1.1.0")
        event["payload"]["features"].update(
            {
                "bandwidth_hz": 800.0,
                "duration_ms": 3500,
                "spectral_centroid_hz": 2750.0,
                "harmonic_count": 4,
                "signature_hash": "sha256:abc123",
            }
        )

        self.assert_valid(event)

    def test_v1_1_acoustic_observation_rejects_source_type(self):
        event = valid_acoustic_observation("1.1.0")
        event["payload"]["features"]["source_type"] = "rotor"

        self.assert_invalid(event)

    def test_v1_1_acoustic_observation_rejects_generic_power_db(self):
        event = valid_acoustic_observation("1.1.0")
        del event["payload"]["features"]["spl_db"]
        event["payload"]["features"]["power_db"] = 72.3

        self.assert_invalid(event)

    def test_v1_1_acoustic_classification_as_inference_passes(self):
        observation = valid_acoustic_observation("1.1.0")
        event = inference_event("CLASSIFICATION", version="1.1.0")
        event["payload"]["claim"] = {
            "class_name": "rotor",
            "source_modality": "ACOUSTIC",
        }
        event["payload"]["based_on"] = [observation["event"]["event_id"]]
        event["lineage"] = {"based_on": [observation["event"]["event_id"]]}

        self.assert_valid(event)

    def test_v1_1_acoustic_observation_with_confidence_fails(self):
        event = valid_acoustic_observation("1.1.0")
        event["confidence"] = 0.8

        self.assert_invalid(event)

    def test_v1_1_eo_observation_with_roi_px_passes(self):
        event = valid_eo_observation("1.1.0")

        self.assert_valid(event)

    def test_v1_1_eo_observation_with_bbox_fails(self):
        event = valid_eo_observation("1.1.0")
        event["payload"]["features"]["bbox"] = {"x": 320, "y": 180, "w": 64, "h": 48}

        self.assert_invalid(event)

    def test_v1_1_eo_observation_with_class_name_fails(self):
        event = valid_eo_observation("1.1.0")
        event["payload"]["features"]["class_name"] = "vehicle"

        self.assert_invalid(event)

    def test_v1_1_eo_inference_claim_bbox_passes(self):
        observation = valid_eo_observation("1.1.0")
        event = inference_event("CLASSIFICATION", version="1.1.0")
        event["payload"]["claim"] = {
            "class_name": "vehicle",
            "bbox": [100, 200, 300, 400],
            "source_modality": "EO",
        }
        event["payload"]["based_on"] = [observation["event"]["event_id"]]
        event["lineage"] = {"based_on": [observation["event"]["event_id"]]}

        self.assert_valid(event)

    def test_v1_1_eo_roi_px_missing_width_or_height_fails(self):
        for field in ["w", "h"]:
            event = valid_eo_observation("1.1.0")
            del event["payload"]["features"]["roi_px"][field]

            self.assert_invalid(event)

    def test_v1_1_eo_roi_px_negative_coordinates_fail(self):
        for field in ["x", "y"]:
            event = valid_eo_observation("1.1.0")
            event["payload"]["features"]["roi_px"][field] = -1

            self.assert_invalid(event)

    def test_v1_1_eo_roi_px_non_positive_dimensions_fail(self):
        for field in ["w", "h"]:
            event = valid_eo_observation("1.1.0")
            event["payload"]["features"]["roi_px"][field] = 0

            self.assert_invalid(event)

    def test_v1_1_eo_resolution_px_is_strict(self):
        event = valid_eo_observation("1.1.0")
        del event["payload"]["features"]["resolution_px"]["height"]
        self.assert_invalid(event)

        event = valid_eo_observation("1.1.0")
        event["payload"]["features"]["resolution_px"]["channels"] = 3
        self.assert_invalid(event)

    def test_inference_payload_rejects_track_authority_fields(self):
        for version in ["1.0", "1.1.0"]:
            for field, value in [
                ("track_id", "track-test-001"),
                ("members", [str(uuid7())]),
                ("estimated_state", {"geo": {"lat": 34.0, "lon": -118.0}}),
            ]:
                event = inference_event("CLASSIFICATION", version=version)
                event["payload"][field] = value

                self.assert_invalid(event)

    def test_inference_claim_rejects_track_authority_fields(self):
        for version in ["1.0", "1.1.0"]:
            for field, value in [
                ("track_id", "track-test-001"),
                ("members", [str(uuid7())]),
                ("estimated_state", {"geo": {"lat": 34.0, "lon": -118.0}}),
            ]:
                event = inference_event("CLASSIFICATION", version=version)
                event["payload"]["claim"][field] = value

                self.assert_invalid(event)

    def test_inference_without_lineage_fails(self):
        event = inference_event("CLASSIFICATION")
        del event["lineage"]

        self.assert_invalid(event)

    def test_inference_without_confidence_fails(self):
        event = inference_event("CLASSIFICATION")
        del event["confidence"]

        self.assert_invalid(event)

    def test_valid_v1_0_fusion_and_state_subtypes_pass(self):
        self.assert_valid(fusion_event())
        self.assert_valid(state_event())

    def test_valid_state_event_with_extensions_passes(self):
        for version in ["1.0", "1.1.0"]:
            event = state_event(version)
            event["payload"]["extensions"] = {
                "display_color": "amber",
                "symbol_hint": "unknown-ground-track",
            }

            self.assert_valid(event)

    def test_geo_lat_lon_alt_passes(self):
        for version in ["1.0", "1.1.0"]:
            event = state_event(version)
            event["payload"]["geo"] = {"lat": 34.0, "lon": -118.0, "alt_m": 100.0}

            self.assert_valid(event)

    def test_geo_requires_alt_m_when_present(self):
        for version in ["1.0", "1.1.0"]:
            event = state_event(version)
            del event["payload"]["geo"]["alt_m"]

            self.assert_invalid(event)

    def test_geo_rejects_alternate_altitude_references(self):
        for version in ["1.0", "1.1.0"]:
            event = state_event(version)
            event["payload"]["geo"]["alt_msl_m"] = 100.0

            self.assert_invalid(event)

    def test_geo_rejects_datum_or_crs_fields(self):
        for version in ["1.0", "1.1.0"]:
            for field in ["datum", "crs"]:
                event = state_event(version)
                event["payload"]["geo"][field] = "EPSG:4979"

                self.assert_invalid(event)

    def test_v1_1_0_geo_error_ellipse_passes(self):
        event = state_event("1.1.0")
        event["payload"]["geo"]["error_ellipse_m"] = {
            "semi_major": 150.0,
            "semi_minor": 75.0,
            "orientation_deg": 45.0,
            "probability": "CE_90",
        }

        self.assert_valid(event)

    def test_v1_0_geo_error_ellipse_fails(self):
        event = state_event("1.0")
        event["payload"]["geo"]["error_ellipse_m"] = {
            "semi_major": 150.0,
            "semi_minor": 75.0,
            "orientation_deg": 45.0,
        }

        self.assert_invalid(event)

    def test_state_speed_mps_zero_and_positive_pass(self):
        for version in ["1.0", "1.1.0"]:
            for speed in [0, 12.5]:
                event = state_event(version)
                event["payload"]["speed_mps"] = speed

                self.assert_valid(event)

    def test_state_speed_mps_negative_fails(self):
        for version in ["1.0", "1.1.0"]:
            event = state_event(version)
            event["payload"]["speed_mps"] = -0.1

            self.assert_invalid(event)

    def test_fusion_estimated_state_speed_mps_negative_fails(self):
        for version in ["1.0", "1.1.0"]:
            event = fusion_event(version)
            event["payload"]["estimated_state"] = {
                "geo": {"lat": 34.0, "lon": -118.0, "alt_m": 100.0},
                "speed_mps": -0.1,
            }

            self.assert_invalid(event)

    def test_heading_deg_360_passes(self):
        for version in ["1.0", "1.1.0"]:
            event = state_event(version)
            event["payload"]["heading_deg"] = 360

            self.assert_valid(event)

    def test_bearing_az_deg_360_passes(self):
        for version in ["1.0", "1.1.0"]:
            event = valid_rf_observation(version)
            event["payload"]["bearing"] = {"az_deg": 360}

            self.assert_valid(event)

    def test_v1_1_bearing_frame_true_north_passes(self):
        event = valid_rf_observation("1.1.0")
        event["payload"]["bearing"] = {"az_deg": 123.4, "frame": "TRUE_NORTH"}

        self.assert_valid(event)

    def test_v1_1_bearing_frame_array_relative_fails(self):
        event = valid_rf_observation("1.1.0")
        event["payload"]["bearing"] = {"az_deg": 123.4, "frame": "ARRAY_RELATIVE"}

        self.assert_invalid(event)

    def test_v1_0_bearing_frame_key_fails(self):
        event = valid_rf_observation("1.0")
        event["payload"]["bearing"] = {"az_deg": 123.4, "frame": "TRUE_NORTH"}

        self.assert_invalid(event)

    def test_v1_1_quality_measurement_error_scalar_fails(self):
        event = valid_rf_observation("1.1.0")
        event["payload"]["quality"] = {
            "measurement_error": 8.5,
            "geo_status": "AVAILABLE",
        }

        self.assert_invalid(event)

    def test_v1_1_quality_measurement_error_object_passes(self):
        event = valid_rf_observation("1.1.0")
        event["payload"]["quality"] = {
            "measurement_error": {
                "value": 8.5,
                "unit": "deg",
                "metric": "1_SIGMA",
            },
            "geo_status": "AVAILABLE",
        }

        self.assert_valid(event)

    def test_v1_1_quality_measurement_error_missing_unit_fails(self):
        event = valid_rf_observation("1.1.0")
        event["payload"]["quality"] = {
            "measurement_error": {
                "value": 8.5,
                "metric": "1_SIGMA",
            }
        }

        self.assert_invalid(event)

    def test_v1_1_quality_measurement_error_unsupported_unit_fails(self):
        event = valid_rf_observation("1.1.0")
        event["payload"]["quality"] = {
            "measurement_error": {
                "value": 8.5,
                "unit": "feet",
                "metric": "1_SIGMA",
            }
        }

        self.assert_invalid(event)

    def test_v1_1_quality_legacy_error_metric_fails(self):
        event = valid_rf_observation("1.1.0")
        event["payload"]["quality"] = {
            "measurement_error": {
                "value": 8.5,
                "unit": "deg",
                "metric": "1_SIGMA",
            },
            "error_metric": "1_SIGMA",
        }

        self.assert_invalid(event)

    def test_v1_1_quality_snr_and_calibration_state_still_pass(self):
        event = valid_rf_observation("1.1.0")
        event["payload"]["quality"] = {
            "snr_db": 12.0,
            "calibration_state": "CALIBRATED",
            "geo_status": "AVAILABLE",
        }

        self.assert_valid(event)

    def test_state_payload_rejects_raw_observation_fields(self):
        banned_fields = [
            ("features", {"center_freq_hz": 2450000000}),
            ("raw_features", {"iq_sample_ref": "capture-001"}),
            ("modality", "RF"),
            ("measurement", -35.2),
            ("measurements", [-35.2, -34.9]),
            ("t_start", "2025-01-17T14:32:09Z"),
            ("t_end", "2025-01-17T14:32:10Z"),
            ("data_ref", {"ref_id": "capture-001"}),
            ("data_refs", [{"ref_id": "capture-001"}]),
        ]
        for version in ["1.0", "1.1.0"]:
            for field, value in banned_fields:
                event = state_event(version)
                event["payload"][field] = value

                self.assert_invalid(event)

    def test_state_extensions_reject_raw_observation_fields(self):
        for version in ["1.0", "1.1.0"]:
            for field, value in [
                ("features", {"center_freq_hz": 2450000000}),
                ("raw_features", {"iq_sample_ref": "capture-001"}),
                ("modality", "RF"),
                ("measurement", -35.2),
                ("measurements", [-35.2]),
                ("t_start", "2025-01-17T14:32:09Z"),
                ("t_end", "2025-01-17T14:32:10Z"),
                ("data_ref", {"ref_id": "capture-001"}),
                ("data_refs", [{"ref_id": "capture-001"}]),
            ]:
                event = state_event(version)
                event["payload"]["extensions"] = {field: value}

                self.assert_invalid(event)

    def test_state_without_confidence_fails(self):
        event = state_event()
        del event["confidence"]

        self.assert_invalid(event)

    def test_state_without_lineage_fails(self):
        event = state_event()
        del event["lineage"]

        self.assert_invalid(event)

    def test_valid_v1_0_command_subtypes_pass(self):
        command_cases = [
            ("GOTO", {"target_geo": {"lat": 34.0, "lon": -118.0}}),
            (
                "ORBIT",
                {
                    "target_geo": {"lat": 34.0, "lon": -118.0},
                    "geometry": {"pattern": "circle", "radius_m": 100},
                },
            ),
            ("HOLD", {}),
            (
                "SEARCH_BOX",
                {
                    "geometry": {
                        "bbox": {
                            "min_lat": 33.9,
                            "min_lon": -118.1,
                            "max_lat": 34.1,
                            "max_lon": -117.9,
                        }
                    }
                },
            ),
        ]
        for task_type, payload_updates in command_cases:
            self.assert_valid(command_event(task_type, payload_updates, version="1.0"))

    def test_goto_command_with_2d_target_geo_passes(self):
        for version in ["1.0", "1.1.0"]:
            event = command_event(
                "GOTO",
                {"target_geo": {"lat": 34.0, "lon": -118.0}},
                version=version,
            )

            self.assert_valid(event)

    def test_command_with_extensions_passes(self):
        for version in ["1.0", "1.1.0"]:
            event = command_event(
                "GOTO",
                {
                    "target_geo": {"lat": 34.0, "lon": -118.0},
                    "extensions": {"operator_note": "route through safe lane"},
                },
                version=version,
            )

            self.assert_valid(event)

    def test_goto_command_rejects_target_geo_altitude(self):
        for version in ["1.0", "1.1.0"]:
            event = command_event(
                "GOTO",
                {"target_geo": {"lat": 34.0, "lon": -118.0, "alt_m": 100.0}},
                version=version,
            )

            self.assert_invalid(event)

    def test_goto_command_requires_target_geo(self):
        for version in ["1.0", "1.1.0"]:
            self.assert_invalid(command_event("GOTO", {}, version=version))

    def test_goto_command_rejects_orbit_geometry(self):
        for version in ["1.0", "1.1.0"]:
            event = command_event(
                "GOTO",
                {
                    "target_geo": {"lat": 34.0, "lon": -118.0},
                    "geometry": {"pattern": "circle", "radius_m": 100},
                },
                version=version,
            )

            self.assert_invalid(event)

    def test_orbit_command_requires_orbit_geometry(self):
        for version in ["1.0", "1.1.0"]:
            event = command_event(
                "ORBIT",
                {"target_geo": {"lat": 34.0, "lon": -118.0}},
                version=version,
            )

            self.assert_invalid(event)

    def test_search_box_command_requires_search_box_geometry(self):
        for version in ["1.0", "1.1.0"]:
            self.assert_invalid(command_event("SEARCH_BOX", {}, version=version))

    def test_command_payload_rejects_altitude_fields(self):
        altitude_fields = [
            "alt_m",
            "altitude_m",
            "alt_hae_m",
            "alt_msl_m",
            "agl_m",
            "target_alt_m",
            "altitude",
            "target_altitude",
        ]
        for version in ["1.0", "1.1.0"]:
            for field in altitude_fields:
                event = command_event(
                    "GOTO",
                    {
                        "target_geo": {"lat": 34.0, "lon": -118.0},
                        field: 100.0,
                    },
                    version=version,
                )

                self.assert_invalid(event)

    def test_command_geometry_rejects_altitude_fields(self):
        for version in ["1.0", "1.1.0"]:
            event = command_event(
                "ORBIT",
                {
                    "target_geo": {"lat": 34.0, "lon": -118.0},
                    "geometry": {"pattern": "circle", "radius_m": 100, "alt_m": 100.0},
                },
                version=version,
            )

            self.assert_invalid(event)

    def test_command_extensions_reject_altitude_fields(self):
        for version in ["1.0", "1.1.0"]:
            event = command_event(
                "GOTO",
                {
                    "target_geo": {"lat": 34.0, "lon": -118.0},
                    "extensions": {"target_altitude": 100.0},
                },
                version=version,
            )

            self.assert_invalid(event)

    def test_command_rejects_unknown_top_level_payload_fields(self):
        event = command_event(
            "GOTO",
            {
                "target_geo": {"lat": 34.0, "lon": -118.0},
                "vendor_note": "must use extensions",
            },
            version="1.0",
        )

        self.assert_invalid(event)

    def test_command_requires_deconfliction_true(self):
        event = command_event(
            "GOTO",
            {"target_geo": {"lat": 34.0, "lon": -118.0}},
            version="1.0",
        )
        event["payload"]["requires_deconfliction"] = False

        self.assert_invalid(event)

    def test_command_with_confidence_fails(self):
        event = command_event(
            "GOTO",
            {"target_geo": {"lat": 34.0, "lon": -118.0}},
            version="1.0",
        )
        event["confidence"] = 0.8

        self.assert_invalid(event)

    def test_command_valid_for_ms_must_be_positive(self):
        event = command_event(
            "GOTO",
            {"target_geo": {"lat": 34.0, "lon": -118.0}},
            version="1.0",
        )
        event["payload"]["valid_for_ms"] = 0

        self.assert_invalid(event)

    def test_v1_1_return_to_base_minimal_task_passes(self):
        self.assert_valid(command_event("RETURN_TO_BASE", {}, version="1.1.0"))

    def test_v1_1_land_with_altitude_fails(self):
        event = command_event(
            "LAND",
            {"target_geo": {"lat": 34.0, "lon": -118.0, "alt_m": 100.0}},
            version="1.1.0",
        )

        self.assert_invalid(event)

    def test_v1_1_track_target_requires_target_track_id(self):
        self.assert_invalid(command_event("TRACK_TARGET", {}, version="1.1.0"))

        event = command_event(
            "TRACK_TARGET",
            {"target_track_id": "track-test-001"},
            version="1.1.0",
        )

        self.assert_valid(event)

    def test_valid_v1_0_system_subtypes_pass(self):
        for system_type in ["LINK_STATUS", "TIME_STATUS", "SCHEMA_VIOLATION", "TASK_ACK"]:
            self.assert_valid(valid_v1_0_system_event(system_type))

    # The four subtype-consistency pins below run against the 1.1.0 stamp:
    # the 2026-08-02 lock restoration removed the consistency machinery from
    # the v1.0 schema (it was added post-lock by the v1.1.0 release), and
    # whether the locked v1.0 CONTRACT text independently mandates the
    # subtype/payload-discriminator match is a recorded open adjudication.
    # Until that is decided, the rules are pinned where they lawfully live.
    def test_system_subtype_must_match_payload_system_type(self):
        event = valid_v1_0_system_event("TIME_STATUS")
        event["zmeta_version"] = "1.1.0"
        event["payload"] = {
            "system_type": "LINK_STATUS",
            "state": "UP",
            "metrics": {
                "link_id": "mesh-01",
                "latency_ms": 10,
                "packet_loss_pct": 0,
                "throughput_bps": 1000000,
            },
        }

        self.assert_invalid(event)

    def test_command_subtype_must_match_payload_task_type(self):
        event = command_event("ORBIT", {"target_geo": {"lat": 34.0, "lon": -118.0}}, version="1.0")
        event["event"]["event_subtype"] = "GOTO"

        self.assert_invalid(event)

    def test_inference_subtype_must_match_payload_inference_type(self):
        event = inference_event("ANOMALY", version="1.1.0")
        event["event"]["event_subtype"] = "CLASSIFICATION"

        self.assert_invalid(event)

    def test_observation_subtype_must_match_payload_modality(self):
        event = valid_rf_observation("1.1.0")
        event["payload"]["modality"] = "EO"
        event["payload"]["features"] = {}

        self.assert_invalid(event)

    def test_state_subtype_must_be_track_state(self):
        event = state_event(version="1.1.0")
        event["event"]["event_subtype"] = "POSITION"

        self.assert_invalid(event)

    def test_v1_0_sensor_status_fails(self):
        event = system_status(
            "SENSOR_STATUS",
            "ACTIVE",
            {"sensor_id": "rf-01", "operational_state": "ACTIVE"},
            version="1.0",
        )

        self.assert_invalid(event)

    def test_v1_0_platform_status_fails(self):
        event = system_status(
            "PLATFORM_STATUS",
            "NOMINAL",
            {"battery_pct": 87},
            version="1.0",
        )

        self.assert_invalid(event)

    def test_v1_0_radar_modality_fails(self):
        event = valid_rf_observation("1.0")
        event["payload"]["modality"] = "RADAR"

        self.assert_invalid(event)

    def test_v1_1_0_sensor_status_passes(self):
        event = system_status(
            "SENSOR_STATUS",
            "ACTIVE",
            {"sensor_id": "radar-01", "modality": "RADAR"},
        )

        self.assert_valid(event)

    def test_v1_1_0_sensor_status_rejects_operational_state_metric(self):
        event = system_status(
            "SENSOR_STATUS",
            "ACTIVE",
            {"sensor_id": "radar-01", "operational_state": "OFFLINE"},
        )

        self.assert_invalid(event)

    def test_v1_1_0_sensor_status_degraded_passes(self):
        event = system_status(
            "SENSOR_STATUS",
            "DEGRADED",
            {"sensor_id": "radar-01", "mode": "STANDBY"},
        )

        self.assert_valid(event)

    def test_v1_1_0_sensor_status_unknown_passes(self):
        event = system_status(
            "SENSOR_STATUS",
            "UNKNOWN",
            {"sensor_id": "radar-01"},
        )

        self.assert_valid(event)

    def test_v1_1_0_sensor_status_requires_sensor_id(self):
        event = system_status(
            "SENSOR_STATUS",
            "ACTIVE",
            {"sensor_type": "KrakenSDR", "modality": "RF"},
        )

        self.assert_invalid(event)

    def test_v1_1_0_platform_status_passes(self):
        event = system_status(
            "PLATFORM_STATUS",
            "NOMINAL",
            {"battery_pct": 87, "platform_type": "MULTIROTOR"},
        )

        self.assert_valid(event)

    def test_v1_1_0_platform_status_with_fuel_remaining_passes(self):
        event = system_status(
            "PLATFORM_STATUS",
            "NOMINAL",
            {"fuel_remaining_pct": 55.5, "platform_type": "MARITIME"},
        )

        self.assert_valid(event)

    def test_v1_1_0_platform_status_with_endurance_remaining_ms_passes(self):
        event = system_status(
            "PLATFORM_STATUS",
            "NOMINAL",
            {"endurance_remaining_ms": 1800000, "platform_type": "FIXED"},
        )

        self.assert_valid(event)

    def test_v1_1_0_platform_status_with_power_state_passes(self):
        event = system_status(
            "PLATFORM_STATUS",
            "NOMINAL",
            {"power_state": "EXTERNAL_POWER", "platform_type": "FIXED"},
        )

        self.assert_valid(event)

    def test_v1_1_0_platform_status_requires_power_signal(self):
        event = system_status(
            "PLATFORM_STATUS",
            "NOMINAL",
            {"platform_type": "FIXED", "flight_mode": "IDLE"},
        )

        self.assert_invalid(event)

    def test_v1_1_0_platform_status_rejects_endurance_remaining_sec(self):
        event = system_status(
            "PLATFORM_STATUS",
            "NOMINAL",
            {"endurance_remaining_sec": 1800, "platform_type": "MULTIROTOR"},
        )

        self.assert_invalid(event)

    def test_v1_1_0_reserved_observation_modalities_fail(self):
        for modality in ["RADAR", "LIDAR", "MAGNETIC", "SEISMIC", "CYBER", "SIGINT"]:
            event = valid_rf_observation("1.1.0")
            event["event"]["event_subtype"] = modality
            event["payload"]["modality"] = modality

            self.assert_invalid(event)

    def test_v1_1_0_data_refs_passes(self):
        event = valid_rf_observation("1.1.0")
        event["payload"]["data_refs"] = [
            {
                "ref_id": "iq-capture-001",
                "store": "local",
                "kind": "RAW",
                "format": "iq",
                "hash": "sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
                "size_bytes": 1024,
            }
        ]

        self.assert_valid(event)

    def test_v1_1_0_data_ref_passes(self):
        event = valid_rf_observation("1.1.0")
        event["payload"]["data_ref"] = {
            "ref_id": "iq-capture-001",
            "store": "local",
            "kind": "RAW",
            "format": "iq",
            "size_bytes": 1024,
            "t_start": "2025-01-17T14:32:09Z",
            "t_end": "2025-01-17T14:32:11Z",
        }

        self.assert_valid(event)

    def test_v1_1_0_data_ref_and_data_refs_together_fail(self):
        event = valid_rf_observation("1.1.0")
        event["payload"]["data_ref"] = {"ref_id": "iq-capture-001"}
        event["payload"]["data_refs"] = [{"ref_id": "iq-capture-002"}]

        self.assert_invalid(event)

    def test_v1_1_0_data_refs_empty_array_fails(self):
        event = valid_rf_observation("1.1.0")
        event["payload"]["data_refs"] = []

        self.assert_invalid(event)

    def test_v1_1_0_data_ref_without_ref_id_fails(self):
        event = valid_rf_observation("1.1.0")
        event["payload"]["data_ref"] = {"store": "local", "kind": "RAW"}

        self.assert_invalid(event)

    def test_v1_1_0_data_ref_window_must_be_paired(self):
        event = valid_rf_observation("1.1.0")
        event["payload"]["data_ref"] = {
            "ref_id": "iq-capture-001",
            "t_start": "2025-01-17T14:32:09Z",
        }

        self.assert_invalid(event)

    def test_v1_1_0_data_ref_rejects_raw_data_fields(self):
        for field in ["raw_blob", "blob", "bytes", "payload_data"]:
            event = valid_rf_observation("1.1.0")
            event["payload"]["data_ref"] = {
                "ref_id": "iq-capture-001",
                field: "AAEC",
            }

            self.assert_invalid(event)

    def test_v1_1_0_data_ref_hash_must_be_sha256(self):
        event = valid_rf_observation("1.1.0")
        event["payload"]["data_ref"] = {
            "ref_id": "iq-capture-001",
            "hash": "md5:deadbeef",
        }

        self.assert_invalid(event)

    def test_v1_1_0_scan_rf_requires_contract_fields(self):
        self.assert_invalid(command_event("SCAN_RF"))

        event = command_event(
            "SCAN_RF",
            {
                "sensor_id": "rf-01",
                "freq_range_hz": {"min": 24000000, "max": 1766000000},
                "dwell_ms": 1000,
            },
        )

        self.assert_valid(event)

    def test_v1_1_0_change_sensor_mode_requires_sensor_mode(self):
        self.assert_invalid(command_event("CHANGE_SENSOR_MODE", {"sensor_id": "rf-01"}))

        event = command_event(
            "CHANGE_SENSOR_MODE",
            {"sensor_id": "rf-01", "sensor_mode": "DF"},
        )

        self.assert_valid(event)

    def test_v1_1_alias_fails(self):
        self.assert_invalid(valid_rf_observation("1.1"))

    def test_missing_zmeta_version_fails(self):
        event = valid_rf_observation("1.0")
        del event["zmeta_version"]

        self.assert_invalid(event)

    def test_unknown_zmeta_version_fails(self):
        self.assert_invalid(valid_rf_observation("2.0"))

    def test_v1_1_0_schema_rejects_v1_0_claim(self):
        event = system_status(
            "SENSOR_STATUS",
            "ACTIVE",
            {"sensor_id": "radar-01", "modality": "RADAR"},
            version="1.0",
        )

        schema = load_json(SCHEMA_DIR / "zmeta-event-1.1.0.schema.json")
        validator = Draft202012Validator(schema, format_checker=FormatChecker())

        self.assertNotEqual(list(validator.iter_errors(event)), [])

    def test_v1_1_only_vocabulary_absent_from_v1_0_schema(self):
        schema = json.dumps(load_json(SCHEMA_DIR / "zmeta-event-1.0.schema.json"))
        v1_1_only_tokens = [
            "SENSOR_STATUS",
            "PLATFORM_STATUS",
            "RETURN_TO_BASE",
            "LAND",
            "LOITER",
            "SCAN_RF",
            "TRACK_TARGET",
            "CHANGE_SENSOR_MODE",
            "error_ellipse_m",
        ]

        for token in v1_1_only_tokens:
            self.assertNotIn(token, schema)

    def test_reference_gateway_loads_canonical_schema(self):
        validator = validators.load_schema(SCHEMA_DIR / "zmeta-event.schema.json")

        self.assertEqual(list(validator.iter_errors(valid_rf_observation("1.0"))), [])

    def test_v1_1_examples_pass_canonical_schema(self):
        path = ROOT / "examples" / "zmeta-v1.1-examples.jsonl"
        with open(path, "r", encoding="utf-8") as handle:
            for line in handle:
                event = json.loads(line)
                self.assert_valid(event)


if __name__ == "__main__":
    unittest.main()
