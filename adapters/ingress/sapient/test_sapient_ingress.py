import importlib.util
import json
from pathlib import Path

import pytest

from adapters.ingress.sapient.registration_state import RegistrationStore
from adapters.ingress.sapient.sapient_to_zmeta import (
    SCHEMA_ID,
    detect,
    translate,
    validate,
)
from zmeta_uuid import uuid7

NODE = "3fa4a34c-b9a1-4f6e-8f2a-0d3f5f8f2a11"
TS = "2026-07-20T10:00:00Z"

_PARENT_ID = str(uuid7())

# Real gateway validators + policy, loaded the same way the mavlink/jreap/cot
# ingress suites do (adapters/ingress/mavlink/test_mavlink_ingress.py): the
# defect class this file exists to catch is exactly an event that passes
# schema-only validate() above but never ran through gateway/src/validators.py
# + policy/*.yaml at all, which is how the identity-laundering and role
# defects below survived every adapter test suite until the first
# independent-implementation interop run found them.
_ROOT = Path(__file__).resolve().parents[3]
_VALIDATORS_PATH = _ROOT / "gateway" / "src" / "validators.py"
_spec = importlib.util.spec_from_file_location("zmeta_validators", _VALIDATORS_PATH)
gateway_validators = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gateway_validators)
GATEWAY_POLICY = gateway_validators.load_policy(_ROOT / "policy")


def _assert_valid(event):
    status, violations = validate(event)
    assert status == "pass", violations


def _assert_gateway_valid(event):
    """Run one emitted event through the real gateway pipeline.

    Schema-only ``validate()`` cannot see producer-authority or role gates,
    or a denylisted key nested inside a vendor extension block (the
    OBSERVATION_HAS_IDENTITY walk is recursive; a top-level-only assertion
    would not see it). This is the coverage whose absence hid both the
    identity-laundering and node_role defects from every prior adapter test.
    """
    ok, violations = gateway_validators.validate_producer_authority(
        event, GATEWAY_POLICY["producer_authority"], GATEWAY_POLICY["violation_severities"]
    )
    assert ok, ("producer_authority", event["event"]["event_type"], violations)

    ok, violations = gateway_validators.validate_role(
        event,
        {"roles": GATEWAY_POLICY["roles"], "deny": GATEWAY_POLICY["deny"]},
        GATEWAY_POLICY["violation_severities"],
    )
    assert ok, ("role", event["event"]["event_type"], violations)

    ok, violations = gateway_validators.validate_semantics(
        event, GATEWAY_POLICY["semantics"], GATEWAY_POLICY["violation_severities"]
    )
    assert ok, ("semantics", event["event"]["event_type"], violations)


# ---------------------------------------------------------------------------
# Fixture builders (inline SAPIENT v2 protobuf-JSON dicts)
# ---------------------------------------------------------------------------


def _rf_registration_msg(node_id=NODE, **config_overrides):
    registration = {
        "node_definition": [{"node_type": "NODE_TYPE_PASSIVE_RF"}],
        "icd_version": "BSI Flex 335 v2.0",
        "config_data": [
            {
                "manufacturer": "Acme",
                "model": "RFSense-9",
                "software_version": "4.2.1",
            }
        ],
        "mode_definition": [
            {
                "mode_name": "scan",
                "mode_type": "MODE_TYPE_DEFAULT",
                "settle_time": {"units": "TIME_UNITS_SECONDS", "value": 1.0},
                "maximum_latency": {"units": "TIME_UNITS_SECONDS", "value": 0.5},
                "tracking_type": "TRACKING_TYPE_TRACKLET",
                "detection_definition": [
                    {
                        "location_type": {
                            "location_units": "LOCATION_COORDINATE_SYSTEM_LAT_LNG_DEG_M",
                            "location_datum": "LOCATION_DATUM_WGS84_E",
                        },
                        "detection_report": [
                            {
                                "category": "DETECTION_REPORT_CATEGORY_SIGNAL",
                                "type": "centre_frequency",
                                "units": "MHz",
                            },
                            {
                                "category": "DETECTION_REPORT_CATEGORY_SIGNAL",
                                "type": "start_frequency",
                                "units": "MHz",
                            },
                            {
                                "category": "DETECTION_REPORT_CATEGORY_SIGNAL",
                                "type": "stop_frequency",
                                "units": "MHz",
                            },
                            {
                                "category": "DETECTION_REPORT_CATEGORY_SIGNAL",
                                "type": "amplitude",
                                "units": "dBm",
                            },
                        ],
                        "velocity_type": {
                            "enu_velocity_units": {
                                "east_north_rate_units": "SPEED_UNITS_MS"
                            }
                        },
                        "geometric_error": {
                            "type": "Standard Deviation",
                            "units": "metres",
                            "variation_type": "Linear with Range",
                        },
                    }
                ],
            }
        ],
    }
    registration.update(config_overrides)
    return {"timestamp": TS, "node_id": node_id, "registration": registration}


def _camera_registration_msg(node_id=NODE):
    # Registration WITHOUT config_data and WITHOUT declared signal units:
    # node type is known (CAMERA) but model identity and units are not.
    return {
        "timestamp": TS,
        "node_id": node_id,
        "registration": {
            "node_definition": [{"node_type": "NODE_TYPE_CAMERA"}],
            "icd_version": "BSI Flex 335 v2.0",
            "mode_definition": [
                {
                    "mode_name": "stare",
                    "settle_time": {"units": "TIME_UNITS_SECONDS", "value": 1.0},
                }
            ],
        },
    }


def _fusion_registration_msg(node_id=NODE):
    return {
        "timestamp": TS,
        "node_id": node_id,
        "registration": {
            "node_definition": [{"node_type": "NODE_TYPE_FUSION_NODE"}],
            "icd_version": "BSI Flex 335 v2.0",
            "config_data": [{"manufacturer": "Acme", "model": "Fuse-1"}],
            "mode_definition": [{"mode_name": "default"}],
        },
    }


def _store(*messages):
    store = RegistrationStore()
    for msg in messages:
        store.ingest(msg)
    return store


def _location(**overrides):
    location = {
        "x": -112.04,
        "y": 43.49,
        "z": 1450.0,
        "coordinate_system": "LOCATION_COORDINATE_SYSTEM_LAT_LNG_DEG_M",
        "datum": "LOCATION_DATUM_WGS84_E",
    }
    location.update(overrides)
    return location


def _detection_msg(**overrides):
    body = {
        "report_id": "01J00000000000000000000001",
        "object_id": "01J00000000000000000000002",
        "location": _location(),
        "detection_confidence": 0.83,
        "signal": [
            {
                "amplitude": -57.0,
                "centre_frequency": 433.0,
                "start_frequency": 432.9,
                "stop_frequency": 433.1,
            }
        ],
        "classification": [
            {
                "type": "UAV",
                "confidence": 0.9,
                "sub_class": [{"type": "quadcopter", "level": 1}],
            }
        ],
        "behaviour": [{"type": "loitering", "confidence": 0.6}],
        "enu_velocity": {"east_rate": 3.0, "north_rate": -1.0},
    }
    body.update(overrides)
    return {"timestamp": TS, "node_id": NODE, "detection_report": body}


def _status_msg(**overrides):
    body = {
        "report_id": "01J00000000000000000000003",
        "system": "SYSTEM_OK",
        "info": "INFO_NEW",
        "mode": "scan",
        "power": {
            "level": 87,
            "source": "POWERSOURCE_INTERNAL_BATTERY",
            "status": "POWERSTATUS_OK",
        },
        "field_of_view": {
            "range_bearing": {
                "azimuth": 90.0,
                "horizontal_extent": 30.0,
                "coordinate_system": "RANGE_BEARING_COORDINATE_SYSTEM_DEGREES_M",
                "datum": "RANGE_BEARING_DATUM_TRUE",
            }
        },
        "status": [
            {
                "status_level": "STATUS_LEVEL_INFORMATION_STATUS",
                "status_type": "STATUS_TYPE_WEATHER",
                "status_value": "Raining",
            }
        ],
    }
    body.update(overrides)
    return {"timestamp": TS, "node_id": NODE, "status_report": body}


def _alert_msg(**overrides):
    body = {
        "alert_id": "01J00000000000000000000004",
        "alert_type": "ALERT_TYPE_WARNING",
        "description": "perimeter breach",
        "region_id": "01J00000000000000000000005",
        "confidence": 0.7,
        "location": _location(),
        "priority": "DISCRETE_PRIORITY_HIGH",
        "ranking": 0.4,
    }
    body.update(overrides)
    return {"timestamp": TS, "node_id": NODE, "alert": body}


def _task_ack_msg(**overrides):
    body = {"task_id": "01J00000000000000000000006", "task_status": "TASK_STATUS_ACCEPTED"}
    body.update(overrides)
    return {"timestamp": TS, "node_id": NODE, "task_ack": body}


# ---------------------------------------------------------------------------
# RegistrationStore
# ---------------------------------------------------------------------------


def test_registration_store_captures_model_modes_and_units():
    store = _store(_rf_registration_msg())

    assert store.model_identity(NODE) == {"name": "Acme RFSense-9", "version": "4.2.1"}
    assert store.max_latency_ms(NODE, mode="scan") == 500.0
    assert store.max_latency_ms(NODE) == 500.0
    assert store.is_fusion(NODE) is False
    assert store.node_types(NODE) == ["PASSIVE_RF"]
    assert store.signal_units(NODE)["centre_frequency"] == "MHz"
    assert store.signal_units(NODE)["amplitude"] == "dBm"
    assert store.velocity_factor_mps(NODE) == 1.0
    assert store.geometric_error(NODE)["type"] == "Standard Deviation"


def test_registration_store_model_without_software_version_is_unknown():
    msg = _rf_registration_msg(
        config_data=[{"manufacturer": "Acme", "model": "RFSense-9"}]
    )
    store = _store(msg)

    assert store.model_identity(NODE) == {"name": "Acme RFSense-9", "version": "unknown"}


def test_registration_store_missing_config_data_means_no_model():
    store = _store(_camera_registration_msg())

    assert store.model_identity(NODE) is None


def test_registration_store_unknown_duration_units_yield_none():
    msg = _rf_registration_msg()
    msg["registration"]["mode_definition"][0]["maximum_latency"] = {
        "units": "TIME_UNITS_FORTNIGHTS",
        "value": 2.0,
    }
    store = _store(msg)

    assert store.max_latency_ms(NODE) is None


def test_registration_store_kph_velocity_factor():
    msg = _rf_registration_msg()
    msg["registration"]["mode_definition"][0]["detection_definition"][0][
        "velocity_type"
    ] = {"enu_velocity_units": {"east_north_rate_units": "SPEED_UNITS_KPH"}}
    store = _store(msg)

    assert store.velocity_factor_mps(NODE) == pytest.approx(1.0 / 3.6)


def test_registration_store_conflicting_units_are_poisoned_not_first_wins():
    msg = _rf_registration_msg()
    definition = msg["registration"]["mode_definition"][0]["detection_definition"][0]
    conflicting = dict(definition)
    conflicting["detection_report"] = [
        {
            "category": "DETECTION_REPORT_CATEGORY_SIGNAL",
            "type": "centre_frequency",
            "units": "GHz",
        }
    ]
    msg["registration"]["mode_definition"][0]["detection_definition"] = [
        definition,
        conflicting,
    ]
    store = _store(msg)

    assert store.signal_units(NODE)["centre_frequency"] is None


def test_registration_store_ignores_message_without_node_id():
    store = RegistrationStore()
    msg = _rf_registration_msg()
    msg["node_id"] = None

    assert store.ingest(msg) is None
    assert store.model_identity(NODE) is None


# ---------------------------------------------------------------------------
# detect()
# ---------------------------------------------------------------------------


def test_detect_accepts_sapient_message():
    assert detect(json.dumps(_detection_msg()).encode()) == SCHEMA_ID


def test_detect_accepts_camel_case_keys():
    msg = {"nodeId": NODE, "timestamp": TS, "statusReport": {"system": "SYSTEM_OK"}}
    assert detect(json.dumps(msg)) == SCHEMA_ID


def test_detect_rejects_missing_identity_timestamp_or_content():
    assert detect(json.dumps({"timestamp": TS, "detection_report": {}})) is None
    assert detect(json.dumps({"node_id": NODE, "detection_report": {}})) is None
    assert detect(json.dumps({"node_id": NODE, "timestamp": TS})) is None
    bad = {"node_id": NODE, "timestamp": TS, "alert": {}, "error": {}}
    assert detect(json.dumps(bad)) is None
    assert detect(b"not json") is None


# ---------------------------------------------------------------------------
# Envelope refusals and no-event content
# ---------------------------------------------------------------------------


def test_translate_refuses_missing_or_unparseable_timestamp():
    msg = _detection_msg()
    msg.pop("timestamp")
    assert translate(msg, SCHEMA_ID, registration=_store(_rf_registration_msg())) == []

    msg["timestamp"] = "not-a-time"
    assert translate(msg, SCHEMA_ID, registration=_store(_rf_registration_msg())) == []


def test_translate_refuses_null_node_id():
    # Identity is never fabricated: a null node_id refuses the message.
    msg = _detection_msg()
    msg["node_id"] = None
    assert translate(msg, SCHEMA_ID, registration=_store(_rf_registration_msg())) == []


def test_translate_refuses_wrong_schema_id():
    assert translate(_detection_msg(), "vendor:other:v1") == []


def test_registration_content_feeds_store_and_emits_nothing():
    store = RegistrationStore()
    assert translate(_rf_registration_msg(), SCHEMA_ID, registration=store) == []
    assert store.model_identity(NODE) is not None


def test_ack_and_task_content_emit_nothing():
    for key in ("registration_ack", "alert_ack", "task"):
        msg = {"timestamp": TS, "node_id": NODE, key: {}}
        assert translate(msg, SCHEMA_ID) == []


def test_protobuf_timestamp_dict_is_normalized():
    msg = _status_msg()
    msg["timestamp"] = {"seconds": 1784541600, "nanos": 0}
    events = translate(msg, SCHEMA_ID)
    assert events and events[0]["event"]["ts"].endswith("Z")


def test_out_of_range_protobuf_timestamp_refuses_not_raises():
    # Hostile/corrupt wire data must fail closed like any unparseable
    # timestamp — never crash the ingest loop.
    for seconds in (1e20, -62135596801, float("nan")):
        msg = _detection_msg()
        msg["timestamp"] = {"seconds": seconds, "nanos": 0}
        assert (
            translate(msg, SCHEMA_ID, registration=_store(_rf_registration_msg()))
            == []
        )


# ---------------------------------------------------------------------------
# DetectionReport -> OBSERVATION_EVENT + INFERENCE_EVENTs
# ---------------------------------------------------------------------------


def test_detection_rf_happy_path():
    events = translate(
        _detection_msg(), SCHEMA_ID, registration=_store(_rf_registration_msg())
    )

    # observation, classification, behaviour, existence claim — in order.
    assert [e["event"]["event_type"] for e in events] == [
        "OBSERVATION_EVENT",
        "INFERENCE_EVENT",
        "INFERENCE_EVENT",
        "INFERENCE_EVENT",
    ]
    obs = events[0]
    assert obs["zmeta_version"] == "1.0"
    assert obs["event"]["event_subtype"] == "RF"
    assert obs["source"] == {
        "platform_id": NODE,
        "node_role": "EDGE",
        "producer": "sapient-ingress",
        "sensor_id": NODE,
    }
    features = obs["payload"]["features"]
    assert features["center_freq_hz"] == pytest.approx(433.0e6)
    assert features["power_dbm"] == -57.0
    assert features["bandwidth_hz"] == pytest.approx(0.2e6, rel=1e-6)
    assert features["velocity_enu_mps"] == {"east": 3.0, "north": -1.0}
    assert obs["payload"]["geo"] == {"lat": 43.49, "lon": -112.04, "alt_m": 1450.0}
    assert obs["payload"]["quality"]["geo_status"] == "AVAILABLE"
    assert "confidence" not in obs
    for event in events:
        _assert_valid(event)


def test_detection_camel_case_input_is_equivalent():
    msg = {
        "timestamp": TS,
        "nodeId": NODE,
        "detectionReport": {
            "reportId": "01J00000000000000000000001",
            "objectId": "01J00000000000000000000002",
            "detectionConfidence": 0.83,
            "location": {
                "x": -112.04,
                "y": 43.49,
                "z": 1450.0,
                "coordinateSystem": "LOCATION_COORDINATE_SYSTEM_LAT_LNG_DEG_M",
                "datum": "LOCATION_DATUM_WGS84_E",
            },
            "signal": [
                {
                    "amplitude": -57.0,
                    "centreFrequency": 433.0,
                    "startFrequency": 432.9,
                    "stopFrequency": 433.1,
                }
            ],
        },
    }
    events = translate(msg, SCHEMA_ID, registration=_store(_rf_registration_msg()))

    obs = events[0]
    assert obs["payload"]["features"]["center_freq_hz"] == pytest.approx(433.0e6)
    assert obs["payload"]["geo"]["lat"] == 43.49


def test_detection_timing_widened_by_registration_latency():
    events = translate(
        _detection_msg(), SCHEMA_ID, registration=_store(_rf_registration_msg())
    )

    # UNSYNCED fallback 60000 ms + declared 0.5 s maximum_latency.
    for event in events:
        assert event["payload"]["timing_quality"]["est_error_ms"] == 60500.0
        assert event["payload"]["timing_quality"]["sync_state"] == "UNSYNCED"


def test_caller_timing_quality_is_also_widened():
    events = translate(
        _detection_msg(),
        SCHEMA_ID,
        registration=_store(_rf_registration_msg()),
        timing_quality={
            "time_source": "NTP",
            "sync_state": "LOCKED",
            "est_error_ms": 50,
        },
    )

    timing = events[0]["payload"]["timing_quality"]
    assert timing["time_source"] == "NTP"
    assert timing["est_error_ms"] == 550.0


def test_detection_active_mode_scopes_the_widen():
    msg = _rf_registration_msg()
    msg["registration"]["mode_definition"].append(
        {
            "mode_name": "track",
            "maximum_latency": {"units": "TIME_UNITS_MILLISECONDS", "value": 80.0},
        }
    )
    store = _store(msg)

    scoped = translate(
        _detection_msg(), SCHEMA_ID, registration=store, active_mode="track"
    )
    unscoped = translate(_detection_msg(), SCHEMA_ID, registration=store)

    assert scoped[0]["payload"]["timing_quality"]["est_error_ms"] == 60080.0
    # mode=None takes the conservative max across declared modes.
    assert unscoped[0]["payload"]["timing_quality"]["est_error_ms"] == 60500.0


def test_detection_unknown_active_mode_takes_conservative_widen():
    # A mode name the registration did not declare (caller typo, or a mode
    # re-declared away) must never yield a smaller error bound than no mode
    # at all: the cross-mode maximum applies.
    events = translate(
        _detection_msg(),
        SCHEMA_ID,
        registration=_store(_rf_registration_msg()),
        active_mode="scam",
    )

    assert events[0]["payload"]["timing_quality"]["est_error_ms"] == 60500.0


def test_detection_vendor_extension_carries_native_fields_without_denylist():
    events = translate(
        _detection_msg(id="G-ABCD", task_id="01J00000000000000000000007"),
        SCHEMA_ID,
        registration=_store(_rf_registration_msg()),
    )

    ext = events[0]["payload"]["extensions"]["vendor.sapient"]
    assert ext["report_id"] == "01J00000000000000000000001"
    assert ext["object_id"] == "01J00000000000000000000002"
    assert ext["task_id"] == "01J00000000000000000000007"
    assert ext["id"] == "G-ABCD"
    assert ext["detection_confidence"] == 0.83
    assert ext["native_classification"][0]["type"] == "UAV"
    assert ext["native_behaviour"][0]["type"] == "loitering"
    # Each entry's own confidence is preserved, renamed, not dropped.
    assert ext["native_classification"][0]["native_confidence"] == 0.9
    assert ext["native_behaviour"][0]["native_confidence"] == 0.6
    # Denylist names stay out of features and the extension block -- at
    # EVERY nesting depth, not just the top level. A top-level-only
    # `set(ext)` check here is exactly what let a per-entry "confidence"
    # inside native_classification reach an interop run: the gateway's own
    # OBSERVATION_HAS_IDENTITY walk is recursive
    # (gateway/src/validators.py._find_forbidden_key), so the test must be
    # too.
    denylist = {"confidence", "classification", "track_id", "entity_class", "label", "class_name"}
    assert not denylist & set(ext)
    assert not denylist & set(events[0]["payload"]["features"])
    assert gateway_validators._find_forbidden_key(ext, denylist) is None


def test_detection_inference_events_carry_model_lineage_and_claims():
    events = translate(
        _detection_msg(), SCHEMA_ID, registration=_store(_rf_registration_msg())
    )
    obs_id = events[0]["event"]["event_id"]

    classification = events[1]
    assert classification["event"]["event_subtype"] == "CLASSIFICATION"
    assert classification["payload"]["claim"]["type"] == "UAV"
    assert classification["payload"]["claim"]["sub_class"][0]["type"] == "quadcopter"
    assert classification["payload"]["model"] == {
        "name": "Acme RFSense-9",
        "version": "4.2.1",
    }
    assert classification["confidence"] == 0.9
    assert classification["lineage"]["based_on"] == [obs_id]
    assert classification["lineage"]["transform"].startswith("translate:vendor:sapient_bsi335:v2@")

    behaviour = events[2]
    assert behaviour["event"]["event_subtype"] == "BEHAVIOR"
    assert behaviour["payload"]["claim"]["type"] == "loitering"
    assert behaviour["confidence"] == 0.6

    existence = events[3]
    assert existence["payload"]["claim"] == {"claim_type": "object_present"}
    assert existence["confidence"] == 0.83
    assert existence["lineage"]["based_on"] == [obs_id]


def test_detection_classification_entry_without_confidence_is_refused():
    msg = _detection_msg(
        classification=[{"type": "UAV"}, {"type": "bird", "confidence": 0.4}]
    )
    events = translate(msg, SCHEMA_ID, registration=_store(_rf_registration_msg()))

    claims = [
        e["payload"]["claim"].get("type")
        for e in events
        if e["event"]["event_type"] == "INFERENCE_EVENT"
        and e["event"]["event_subtype"] == "CLASSIFICATION"
        and "type" in e["payload"]["claim"]
    ]
    assert claims == ["bird"]
    # Refused entry stays visible as native provenance.
    ext = events[0]["payload"]["extensions"]["vendor.sapient"]
    assert ext["native_classification"][0] == {"type": "UAV"}


def test_detection_without_registration_is_fully_refused():
    # No registration: no node type (no modality), no units (no canonical
    # RF), no model (no inference) — nothing can be honestly emitted.
    assert translate(_detection_msg(), SCHEMA_ID) == []


def test_detection_camera_without_model_emits_observation_only():
    events = translate(
        _detection_msg(), SCHEMA_ID, registration=_store(_camera_registration_msg())
    )

    assert len(events) == 1
    obs = events[0]
    assert obs["event"]["event_subtype"] == "EO"
    assert obs["payload"]["modality"] == "EO"
    # Undeclared signal units: the whole signal block is extension-only.
    ext = obs["payload"]["extensions"]["vendor.sapient"]
    assert ext["signal"][0]["centre_frequency"] == 433.0
    assert "center_freq_hz" not in obs["payload"]["features"]
    assert ext["native_classification"][0]["type"] == "UAV"
    # Velocity factor undeclared: extension-only, never canonical.
    assert ext["enu_velocity"] == {"east_rate": 3.0, "north_rate": -1.0}
    assert "velocity_enu_mps" not in obs["payload"]["features"]
    _assert_valid(obs)


def test_detection_camera_colour_maps_to_eo_features():
    events = translate(
        _detection_msg(colour="red", signal=None),
        SCHEMA_ID,
        registration=_store(_camera_registration_msg()),
    )

    assert events[0]["payload"]["features"]["colour"] == "red"


def test_detection_unmappable_node_type_emits_inference_only_with_caller_lineage():
    msg = _rf_registration_msg()
    msg["registration"]["node_definition"] = [{"node_type": "NODE_TYPE_RADAR"}]
    store = _store(msg)
    detection = _detection_msg(signal=None)

    refused = translate(detection, SCHEMA_ID, registration=store)
    assert refused == []

    events = translate(
        detection, SCHEMA_ID, registration=store, based_on=[_PARENT_ID]
    )
    assert [e["event"]["event_subtype"] for e in events] == [
        "CLASSIFICATION",
        "BEHAVIOR",
    ]
    assert events[0]["lineage"]["based_on"] == [_PARENT_ID]
    for event in events:
        _assert_valid(event)


def test_detection_caller_based_on_becomes_observation_lineage():
    events = translate(
        _detection_msg(), SCHEMA_ID,
        registration=_store(_rf_registration_msg()),
        based_on=[_PARENT_ID],
    )

    obs = events[0]
    assert obs["lineage"]["based_on"] == [_PARENT_ID]
    assert obs["lineage"]["transform"] == "translate:vendor:sapient_bsi335:v2@1.0.0"


# ---------------------------------------------------------------------------
# Geo eligibility (all-or-nothing, contract 6.8)
# ---------------------------------------------------------------------------


def _obs_for_location(location):
    events = translate(
        _detection_msg(location=location),
        SCHEMA_ID,
        registration=_store(_rf_registration_msg()),
    )
    return events[0]


def test_geo_zero_fill_suspect_is_omitted():
    obs = _obs_for_location(_location(x=0, y=0))

    assert "geo" not in obs["payload"]
    assert obs["payload"]["quality"]["geo_status"] == "UNAVAILABLE"
    ext = obs["payload"]["extensions"]["vendor.sapient"]
    assert ext["location"]["omitted_reason"] == "ZERO_FILL_SUSPECT"
    _assert_valid(obs)


def test_geo_geoid_datum_is_omitted():
    obs = _obs_for_location(_location(datum="LOCATION_DATUM_WGS84_G"))

    assert "geo" not in obs["payload"]
    ext = obs["payload"]["extensions"]["vendor.sapient"]
    assert ext["location"]["omitted_reason"] == "GEOID_DATUM"


def test_geo_unspecified_coordinate_system_emits_documented_tag():
    # Pins the omitted_reason tag to the mapping-pack vocabulary
    # (enums.yaml / pack README: COORDINATE_SYSTEM_UNSPECIFIED). The code
    # emitted UNITS_UNSPECIFIED for this disposition while the docs said
    # otherwise, so a consumer filtering on the documented tag never
    # matched; this test keeps the two from drifting again.
    obs = _obs_for_location(
        _location(coordinate_system="LOCATION_COORDINATE_SYSTEM_UNSPECIFIED")
    )

    assert "geo" not in obs["payload"]
    ext = obs["payload"]["extensions"]["vendor.sapient"]
    assert ext["location"]["omitted_reason"] == "COORDINATE_SYSTEM_UNSPECIFIED"


def test_geo_missing_altitude_is_omitted():
    location = _location()
    location.pop("z")
    obs = _obs_for_location(location)

    assert "geo" not in obs["payload"]
    ext = obs["payload"]["extensions"]["vendor.sapient"]
    assert ext["location"]["omitted_reason"] == "NO_ALTITUDE"


def test_geo_utm_is_omitted():
    obs = _obs_for_location(
        _location(coordinate_system="LOCATION_COORDINATE_SYSTEM_UTM_M", utm_zone="30N")
    )

    assert "geo" not in obs["payload"]
    ext = obs["payload"]["extensions"]["vendor.sapient"]
    assert ext["location"]["omitted_reason"] == "UTM_UNSUPPORTED"


def test_readme_omitted_reason_list_matches_the_source():
    """README.md's omitted_reason tag list must match _canonical_geo exactly.

    The list previously said UNITS_UNSPECIFIED where the code emits
    COORDINATE_SYSTEM_UNSPECIFIED (fixed alongside this test); this pins the
    whole list, not just that one tag, so the two cannot drift again in
    either direction.
    """
    import re

    readme = (_ROOT / "adapters" / "ingress" / "sapient" / "README.md").read_text(
        encoding="utf-8"
    )
    tag_list_text = readme.split("omitted_reason", 1)[1].split(").", 1)[0]
    documented = set(re.findall(r"`([A-Z_]+)`", tag_list_text))

    source = (_ROOT / "adapters" / "ingress" / "sapient" / "sapient_to_zmeta.py").read_text(
        encoding="utf-8"
    )
    canonical_geo_body = source.split("def _canonical_geo(", 1)[1].split("\ndef ", 1)[0]
    implemented = set(re.findall(r'return None, "([A-Z_]+)"', canonical_geo_body))

    assert implemented, "no omitted_reason tags found in _canonical_geo; parser broke"
    assert documented == implemented, (
        "adapters/ingress/sapient/README.md's omitted_reason tag list diverges "
        "from _canonical_geo's actual return values: "
        f"documented-but-not-implemented={sorted(documented - implemented)}, "
        f"implemented-but-not-documented={sorted(implemented - documented)}"
    )


def test_geo_radians_are_converted_to_degrees():
    import math

    obs = _obs_for_location(
        _location(
            x=math.radians(-112.04),
            y=math.radians(43.49),
            coordinate_system="LOCATION_COORDINATE_SYSTEM_LAT_LNG_RAD_M",
        )
    )

    assert obs["payload"]["geo"]["lat"] == pytest.approx(43.49)
    assert obs["payload"]["geo"]["lon"] == pytest.approx(-112.04)
    _assert_valid(obs)


def test_geo_errors_map_to_measurement_error_only_with_std_dev_labeling():
    obs = _obs_for_location(_location(x_error=3.0, y_error=4.0))

    assert obs["payload"]["quality"]["measurement_error"] == {
        "value": 4.0,
        "unit": "m",
        "metric": "1_SIGMA",
    }
    # Raw per-axis errors stay visible as provenance.
    ext = obs["payload"]["extensions"]["vendor.sapient"]
    assert ext["location_errors"] == {"x_error": 3.0, "y_error": 4.0}


def test_geo_errors_without_std_dev_labeling_stay_raw():
    msg = _rf_registration_msg()
    msg["registration"]["mode_definition"][0]["detection_definition"][0][
        "geometric_error"
    ] = {"type": "CEP", "units": "metres", "variation_type": "Linear"}
    events = translate(
        _detection_msg(location=_location(x_error=3.0)),
        SCHEMA_ID,
        registration=_store(msg),
    )

    obs = events[0]
    assert "measurement_error" not in obs["payload"]["quality"]
    assert obs["payload"]["extensions"]["vendor.sapient"]["location_errors"] == {
        "x_error": 3.0
    }


# ---------------------------------------------------------------------------
# Bearings (convert-or-omit, contract 6.4)
# ---------------------------------------------------------------------------


def test_true_north_range_bearing_becomes_canonical():
    msg = _detection_msg(
        location=None,
        range_bearing={
            "azimuth": 135.0,
            "elevation": 10.0,
            "range": 2.5,
            "coordinate_system": "RANGE_BEARING_COORDINATE_SYSTEM_DEGREES_KM",
            "datum": "RANGE_BEARING_DATUM_TRUE",
        },
    )
    del msg["detection_report"]["location"]
    events = translate(msg, SCHEMA_ID, registration=_store(_rf_registration_msg()))

    obs = events[0]
    assert obs["payload"]["bearing"] == {"az_deg": 135.0, "el_deg": 10.0}
    assert obs["payload"]["quality"]["bearing_frame"] == "TRUE_NORTH"
    assert obs["payload"]["features"]["range_m"] == 2500.0
    assert "geo" not in obs["payload"]
    _assert_valid(obs)


def test_grid_bearing_stays_in_named_native_features():
    msg = _detection_msg()
    del msg["detection_report"]["location"]
    msg["detection_report"]["range_bearing"] = {
        "azimuth": 200.0,
        "range": 850.0,
        "coordinate_system": "RANGE_BEARING_COORDINATE_SYSTEM_DEGREES_M",
        "datum": "RANGE_BEARING_DATUM_GRID",
    }
    events = translate(msg, SCHEMA_ID, registration=_store(_rf_registration_msg()))

    obs = events[0]
    assert "bearing" not in obs["payload"]
    assert obs["payload"]["features"]["bearing_native_deg"] == 200.0
    assert obs["payload"]["features"]["bearing_native_datum"] == "GRID"
    assert obs["payload"]["features"]["range_m"] == 850.0
    assert "bearing_frame" not in obs["payload"]["quality"]
    _assert_valid(obs)


def test_radian_range_bearing_is_converted():
    import math

    msg = _detection_msg()
    del msg["detection_report"]["location"]
    msg["detection_report"]["range_bearing"] = {
        "azimuth": math.radians(90.0),
        "range": 1.2,
        "coordinate_system": "RANGE_BEARING_COORDINATE_SYSTEM_RADIANS_KM",
        "datum": "RANGE_BEARING_DATUM_TRUE",
    }
    events = translate(msg, SCHEMA_ID, registration=_store(_rf_registration_msg()))

    obs = events[0]
    assert obs["payload"]["bearing"]["az_deg"] == pytest.approx(90.0)
    assert obs["payload"]["features"]["range_m"] == pytest.approx(1200.0)


def test_unspecified_bearing_units_stay_raw_in_extension():
    msg = _detection_msg()
    del msg["detection_report"]["location"]
    msg["detection_report"]["range_bearing"] = {
        "azimuth": 45.0,
        "coordinate_system": "RANGE_BEARING_COORDINATE_SYSTEM_UNSPECIFIED",
        "datum": "RANGE_BEARING_DATUM_TRUE",
    }
    events = translate(msg, SCHEMA_ID, registration=_store(_rf_registration_msg()))

    obs = events[0]
    assert "bearing" not in obs["payload"]
    assert "bearing_native_deg" not in obs["payload"]["features"]
    assert obs["payload"]["extensions"]["vendor.sapient"]["range_bearing"]["azimuth"] == 45.0


# ---------------------------------------------------------------------------
# Signal units (registration codex, contract 6.5/6.7)
# ---------------------------------------------------------------------------


def test_signal_without_band_edges_takes_bandwidth_sentinel():
    msg = _detection_msg(
        signal=[{"amplitude": -57.0, "centre_frequency": 433.0}]
    )
    events = translate(msg, SCHEMA_ID, registration=_store(_rf_registration_msg()))

    assert events[0]["payload"]["features"]["bandwidth_hz"] == 0.0
    _assert_valid(events[0])


def test_signal_non_dbm_amplitude_is_never_power_dbm():
    msg = _rf_registration_msg()
    reports = msg["registration"]["mode_definition"][0]["detection_definition"][0][
        "detection_report"
    ]
    for report in reports:
        if report["type"] == "amplitude":
            report["units"] = "dBFS"
    events = translate(_detection_msg(), SCHEMA_ID, registration=_store(msg))

    # No canonical RF possible and PASSIVE_RF has no other modality: no
    # observation, and without an observation or caller lineage no
    # inference can ride either — full refusal.
    assert events == []


def test_signal_ghz_units_convert_to_hz():
    msg = _rf_registration_msg()
    reports = msg["registration"]["mode_definition"][0]["detection_definition"][0][
        "detection_report"
    ]
    for report in reports:
        if report["type"] != "amplitude":
            report["units"] = "GHz"
    events = translate(
        _detection_msg(signal=[{"amplitude": -57.0, "centre_frequency": 2.4}]),
        SCHEMA_ID,
        registration=_store(msg),
    )

    assert events[0]["payload"]["features"]["center_freq_hz"] == pytest.approx(2.4e9)


def test_additional_signal_entries_are_preserved_not_dropped():
    # Canonical RF features map from signal[0] only; further entries are
    # additional emitters and must survive as vendor-extension provenance.
    events = translate(
        _detection_msg(
            signal=[
                {"amplitude": -40.0, "centre_frequency": 100.0},
                {"amplitude": -55.0, "centre_frequency": 200.0},
                {"amplitude": -61.0, "centre_frequency": 300.0},
            ]
        ),
        SCHEMA_ID,
        registration=_store(_rf_registration_msg()),
    )

    obs = events[0]
    assert obs["payload"]["features"]["center_freq_hz"] == pytest.approx(100.0e6)
    ext = obs["payload"]["extensions"]["vendor.sapient"]
    assert ext["signal_additional"] == [
        {"amplitude": -55.0, "centre_frequency": 200.0},
        {"amplitude": -61.0, "centre_frequency": 300.0},
    ]
    _assert_valid(obs)


def test_single_mapped_signal_entry_has_no_additional_block():
    events = translate(
        _detection_msg(), SCHEMA_ID, registration=_store(_rf_registration_msg())
    )
    ext = events[0]["payload"]["extensions"]["vendor.sapient"]
    assert "signal_additional" not in ext
    assert "signal" not in ext


# ---------------------------------------------------------------------------
# Fusion-node promotion (contract 4.5.1)
# ---------------------------------------------------------------------------


def test_fusion_detection_without_promotion_is_refused_not_downgraded():
    events = translate(
        _detection_msg(), SCHEMA_ID, registration=_store(_fusion_registration_msg())
    )
    assert events == []


def test_fusion_promotion_refusals():
    store = _store(_fusion_registration_msg())
    promotion = {"loop_status": "CHECKED_NOT_REFLECTION"}

    # No caller loop_status: the reflection check is a verification the
    # adapter never performs, so its verdict is never self-asserted — an
    # empty promotion dict refuses.
    assert (
        translate(
            _detection_msg(), SCHEMA_ID, registration=store, promotion={},
            based_on=[_PARENT_ID],
        )
        == []
    )
    # No caller lineage: STATE lineage is mandatory, never invented.
    assert (
        translate(_detection_msg(), SCHEMA_ID, registration=store, promotion=promotion)
        == []
    )
    # No explicit external confidence: STATE requires confidence.
    msg = _detection_msg()
    del msg["detection_report"]["detection_confidence"]
    assert (
        translate(
            msg, SCHEMA_ID, registration=store, promotion=promotion, based_on=[_PARENT_ID]
        )
        == []
    )
    # No full canonical geo: TrackStatePayload requires geo.
    msg = _detection_msg(location=_location(x=0, y=0))
    assert (
        translate(
            msg, SCHEMA_ID, registration=store, promotion=promotion, based_on=[_PARENT_ID]
        )
        == []
    )


def test_promotion_unknown_keys_refuse():
    # Promotion metadata is allowlisted (contract 4.5.1): a raw feature or
    # any unenumerated key refuses the promotion outright — never merged
    # into external_promotion, never silently dropped (R1-11 R11-12).
    store = _store(_fusion_registration_msg())
    for extra in (
        {"signal_snapshot": {"power_dbm": -57.0}},
        {"not_a_promotion_key": True},
    ):
        promotion = {"loop_status": "CHECKED_NOT_REFLECTION"}
        promotion.update(extra)
        assert (
            translate(
                _detection_msg(),
                SCHEMA_ID,
                registration=store,
                promotion=promotion,
                based_on=[_PARENT_ID],
            )
            == []
        )


def test_nan_confidence_refuses_promotion_and_never_emits():
    # NaN passes jsonschema min/max vacuously, so the adapter must refuse
    # it at the guard (R1-11 R11-04): a NaN detection_confidence refuses
    # the promotion, and a NaN classification confidence never reaches an
    # emitted event.
    store = _store(_fusion_registration_msg())
    msg = _detection_msg()
    msg["detection_report"]["detection_confidence"] = float("nan")
    assert (
        translate(
            msg,
            SCHEMA_ID,
            registration=store,
            promotion={"loop_status": "CHECKED_NOT_REFLECTION"},
            based_on=[_PARENT_ID],
        )
        == []
    )

    events = translate(
        _detection_msg(classification=[{"type": "UAV", "confidence": float("nan")}]),
        SCHEMA_ID,
        registration=_store(_rf_registration_msg()),
    )
    assert events, "NaN classification confidence must not refuse the whole message"
    assert "NaN" not in json.dumps(events)
    for emitted in events:
        _assert_valid(emitted)


def test_non_finite_vendor_values_dropped_on_every_translation_path():
    # R11-04 applied _drop_non_finite to the detection path only; NaN riding
    # a verbatim vendor block through status/alert/task_ack/error produced
    # events with no RFC-8259 wire form (R1-11 verification pass 2). Every
    # emitted event must serialize with allow_nan=False.
    nan = float("nan")
    status_events = translate(
        _status_msg(
            info=None,
            coverage={"snr_db": nan, "range_m": 1200.0},
            status=[
                {
                    "status_level": "STATUS_LEVEL_INFORMATION_STATUS",
                    "status_type": "STATUS_TYPE_WEATHER",
                    "status_value": "Raining",
                    "reading": nan,
                }
            ],
        ),
        SCHEMA_ID,
    )
    assert status_events
    alert_events = translate(
        _alert_msg(ranking=nan, additional_information={"score": nan, "kept": 1.0}),
        SCHEMA_ID,
        registration=_store(_rf_registration_msg()),
        based_on=[_PARENT_ID],
    )
    assert alert_events
    ack_events = translate(
        _task_ack_msg(associated_file=[{"url": "file://x", "size": nan}]),
        SCHEMA_ID,
        task_index={"01J00000000000000000000006": str(uuid7())},
    )
    assert ack_events
    error_events = translate(
        {
            "timestamp": TS,
            "node_id": NODE,
            "error": {"packet": {"weird": nan}, "error_message": ["bad"]},
        },
        SCHEMA_ID,
    )
    assert error_events

    # The PLATFORM_STATUS event passes the raw `power` block through
    # verbatim — a sixth NaN sink the "five ingress paths" framing missed.
    platform_events = translate(
        _status_msg(
            power={
                "level": 87,
                "source": "POWERSOURCE_INTERNAL_BATTERY",
                "status": "POWERSTATUS_OK",
                "voltage": nan,
            }
        ),
        SCHEMA_ID,
    )
    platform = [
        e for e in platform_events
        if e["payload"].get("system_type") == "PLATFORM_STATUS"
    ]
    assert platform, "PLATFORM_STATUS event must still be emitted"
    assert "voltage" not in platform[0]["payload"]["extensions"]["vendor.sapient"]["power"]

    for events in (
        status_events,
        alert_events,
        ack_events,
        error_events,
        platform_events,
    ):
        for emitted in events:
            json.dumps(emitted, allow_nan=False)

    # The dropped key is gone, not zeroed: no fabricated measurement.
    vendor = alert_events[0]["payload"]["extensions"]["vendor.sapient"]
    assert "ranking" not in vendor
    assert vendor["additional_information"] == {"kept": 1.0}


def test_every_vendor_block_is_dropped_at_point_of_use():
    # The guard must sit at each point of use, not once earlier in the
    # function: the detection path used to drop first and then assign
    # vendor_ext["colour"], so any later mutation could silently bypass it.
    #
    # This used to regex `VENDOR_EXTENSION_KEY:\s*`, which sees ONLY the
    # dict-literal form — R1-11 A-02 showed that blindness is not
    # theoretical: it is also why the check never covered the canonical
    # claim sink at all. The scan is now AST-based, so `d[KEY] = ...`,
    # `d.update({KEY: ...})` and a dict literal are all seen. A structural
    # scan is still form-scoped by nature; the form-INDEPENDENT pin is
    # test_non_finite_never_survives_translate_on_any_path below, which
    # drives the public API and cannot miss a site however it is written.
    import ast
    from pathlib import Path

    source = Path(
        Path(__file__).resolve().parent / "sapient_to_zmeta.py"
    ).read_text(encoding="utf-8")
    tree = ast.parse(source)

    def _is_key(node):
        return isinstance(node, ast.Name) and node.id == "VENDOR_EXTENSION_KEY"

    def _guarded(node):
        return (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "_drop_non_finite"
        )

    uses = []
    for node in ast.walk(tree):
        # {VENDOR_EXTENSION_KEY: <value>}
        if isinstance(node, ast.Dict):
            for key, value in zip(node.keys, node.values):
                if _is_key(key):
                    uses.append((node.lineno, value))
        # target[VENDOR_EXTENSION_KEY] = <value>
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Subscript) and _is_key(target.slice):
                    uses.append((node.lineno, node.value))

    assert len(uses) >= 6, "vendor-extension assignment sites vanished"
    unguarded = [line for line, value in uses if not _guarded(value)]
    assert not unguarded, f"vendor block used without the guard at lines: {unguarded}"


def test_non_finite_in_positional_array_drops_the_whole_array():
    # Position carries meaning in a bare numeric array, so removing one
    # element would silently re-index the rest and the consumer could never
    # tell [1.0, NaN, 3.0] from a genuine two-element array. An absent key is
    # honestly absent; a silently shortened array is laundering.
    from adapters.ingress.sapient import sapient_to_zmeta as s2z

    nan = float("nan")
    assert s2z._drop_non_finite({"coords": [1.0, nan, 3.0], "keep": 2.0}) == {
        "keep": 2.0
    }
    # A list of objects has no positional coupling: every element survives,
    # cleaned in place, so no index moves.
    assert s2z._drop_non_finite({"sig": [{"a": nan, "b": 1.0}, {"c": 2.0}]}) == {
        "sig": [{"b": 1.0}, {"c": 2.0}]
    }
    # Clean structures are returned untouched.
    clean = {"a": [1.0, 2.0], "b": {"c": 3.0}}
    assert s2z._drop_non_finite(clean) == clean


def test_promotion_kwarg_reaches_promotion_path_without_registration():
    # A DMM feed the caller vouches for (promotion kwarg) promotes even
    # when its Registration was never captured.
    events = translate(
        _detection_msg(),
        SCHEMA_ID,
        promotion={"loop_status": "CHECKED_NOT_REFLECTION"},
        based_on=[_PARENT_ID],
    )

    assert len(events) == 1
    assert events[0]["event"]["event_type"] == "STATE_EVENT"
    _assert_valid(events[0])


def test_promotion_kwarg_is_ignored_for_a_registered_sensor_node():
    # Registration knowledge wins: a known PASSIVE_RF sensor splits into
    # observation + inferences even when a promotion dict is supplied.
    events = translate(
        _detection_msg(),
        SCHEMA_ID,
        registration=_store(_rf_registration_msg()),
        promotion={"loop_status": "CHECKED_NOT_REFLECTION"},
        based_on=[_PARENT_ID],
    )

    assert events[0]["event"]["event_type"] == "OBSERVATION_EVENT"
    assert all(e["event"]["event_type"] != "STATE_EVENT" for e in events)


def test_fusion_promotion_happy_path():
    events = translate(
        _detection_msg(),
        SCHEMA_ID,
        registration=_store(_fusion_registration_msg()),
        promotion={
            "trust_ref": "producer-authority:site-a",
            "loop_status": "CHECKED_NOT_REFLECTION",
        },
        based_on=[_PARENT_ID],
    )

    assert len(events) == 1
    state = events[0]
    assert state["event"]["event_type"] == "STATE_EVENT"
    assert state["event"]["event_subtype"] == "TRACK_STATE"
    assert state["source"]["node_role"] == "GATEWAY"
    assert state["payload"]["track_id"] == "01J00000000000000000000002"
    assert state["payload"]["class"] == "UAV"
    assert state["payload"]["valid_for_ms"] == 5000
    assert state["confidence"] == 0.83
    promotion = state["payload"]["extensions"]["external_promotion"]
    assert promotion["state_category"] == "PROMOTED_EXTERNAL_STATE"
    assert promotion["projection_id"] == "sapient"
    assert promotion["promotion_policy_id"] == "PROMOTE-SAPIENT-STATE-V1"
    assert promotion["trust_ref"] == "producer-authority:site-a"
    # loop_status is the caller's supplied verdict, never an adapter default.
    assert promotion["loop_status"] == "CHECKED_NOT_REFLECTION"
    assert promotion["source_event_uid"] == "01J00000000000000000000002"
    assert state["lineage"]["based_on"] == [_PARENT_ID]
    assert state["lineage"]["transform"] == (
        "promote:sapient@1.0.0:PROMOTE-SAPIENT-STATE-V1"
    )
    # STATE carries no raw artifacts: compact native ids only.
    vendor = state["payload"]["extensions"]["vendor.sapient"]
    assert "signal" not in vendor and "track_info" not in vendor
    _assert_valid(state)


# ---------------------------------------------------------------------------
# StatusReport -> SENSOR_STATUS / PLATFORM_STATUS (zmeta 1.1.0)
# ---------------------------------------------------------------------------


def test_status_report_happy_path():
    events = translate(
        _status_msg(), SCHEMA_ID, registration=_store(_rf_registration_msg())
    )

    assert len(events) == 2
    sensor, platform = events
    assert sensor["zmeta_version"] == "1.1.0"
    assert sensor["event"]["event_subtype"] == "SENSOR_STATUS"
    assert sensor["payload"]["state"] == "ACTIVE"
    assert sensor["payload"]["metrics"]["sensor_id"] == NODE
    assert sensor["payload"]["metrics"]["mode"] == "scan"
    assert sensor["payload"]["metrics"]["fov_deg"] == 30.0
    ext = sensor["payload"]["extensions"]["vendor.sapient"]
    assert ext["status"][0]["status_value"] == "Raining"

    assert platform["zmeta_version"] == "1.1.0"
    assert platform["event"]["event_subtype"] == "PLATFORM_STATUS"
    assert platform["payload"]["state"] == "NOMINAL"
    assert platform["payload"]["metrics"]["battery_pct"] == 87
    assert platform["payload"]["metrics"]["power_state"] == "BATTERY"
    for event in events:
        _assert_valid(event)


def test_status_state_mapping_and_fault_degrade():
    assert (
        translate(_status_msg(system="SYSTEM_WARNING"), SCHEMA_ID)[0]["payload"]["state"]
        == "DEGRADED"
    )
    assert (
        translate(_status_msg(system="SYSTEM_ERROR"), SCHEMA_ID)[0]["payload"]["state"]
        == "DEGRADED"
    )
    assert (
        translate(_status_msg(system="SYSTEM_GOODBYE"), SCHEMA_ID)[0]["payload"]["state"]
        == "OFFLINE"
    )
    assert (
        translate(_status_msg(system="SYSTEM_UNSPECIFIED"), SCHEMA_ID)[0]["payload"][
            "state"
        ]
        == "UNKNOWN"
    )

    faulted = _status_msg(
        status=[
            {
                "status_level": "STATUS_LEVEL_ERROR_STATUS",
                "status_type": "STATUS_TYPE_INTERNAL_FAULT",
                "status_value": "sensor head offline",
            }
        ]
    )
    assert translate(faulted, SCHEMA_ID)[0]["payload"]["state"] == "DEGRADED"


def test_status_non_true_fov_is_extension_only():
    msg = _status_msg(
        field_of_view={
            "range_bearing": {
                "azimuth": 90.0,
                "horizontal_extent": 30.0,
                "coordinate_system": "RANGE_BEARING_COORDINATE_SYSTEM_DEGREES_M",
                "datum": "RANGE_BEARING_DATUM_MAGNETIC",
            }
        }
    )
    events = translate(msg, SCHEMA_ID)

    sensor = events[0]
    assert "fov_deg" not in sensor["payload"]["metrics"]
    assert "field_of_view" in sensor["payload"]["extensions"]["vendor.sapient"]
    _assert_valid(sensor)


def test_status_node_location_never_becomes_canonical_geo():
    msg = _status_msg(node_location=_location())
    events = translate(msg, SCHEMA_ID)

    sensor = events[0]
    assert "geo" not in sensor["payload"]
    assert "node_location" in sensor["payload"]["extensions"]["vendor.sapient"]


def test_status_without_power_emits_no_platform_status():
    msg = _status_msg()
    del msg["status_report"]["power"]
    events = translate(msg, SCHEMA_ID)

    assert [e["event"]["event_subtype"] for e in events] == ["SENSOR_STATUS"]


def test_status_power_fault_and_mains_mapping():
    msg = _status_msg(
        power={
            "level": 42,
            "source": "POWERSOURCE_MAINS",
            "status": "POWERSTATUS_FAULT",
        }
    )
    events = translate(msg, SCHEMA_ID)

    platform = events[1]
    assert platform["payload"]["state"] == "WARNING"
    assert platform["payload"]["metrics"]["power_state"] == "EXTERNAL_POWER"
    _assert_valid(platform)


def test_status_unmappable_power_is_refused_not_padded():
    msg = _status_msg(power={"source": "POWERSOURCE_SOLAR_PV"})
    events = translate(msg, SCHEMA_ID)

    assert [e["event"]["event_subtype"] for e in events] == ["SENSOR_STATUS"]


# ---------------------------------------------------------------------------
# Alert -> INFERENCE_EVENT / ANOMALY
# ---------------------------------------------------------------------------


def test_alert_happy_path():
    events = translate(
        _alert_msg(),
        SCHEMA_ID,
        registration=_store(_rf_registration_msg()),
        based_on=[_PARENT_ID],
    )

    assert len(events) == 1
    alert = events[0]
    assert alert["event"]["event_subtype"] == "ANOMALY"
    assert alert["payload"]["inference_type"] == "ANOMALY"
    assert alert["payload"]["claim"]["alert_type"] == "WARNING"
    assert alert["payload"]["claim"]["description"] == "perimeter breach"
    assert alert["payload"]["claim"]["geo"]["lat"] == 43.49
    assert alert["confidence"] == 0.7
    assert alert["lineage"]["based_on"] == [_PARENT_ID]
    ext = alert["payload"]["extensions"]["vendor.sapient"]
    assert ext["priority"] == "DISCRETE_PRIORITY_HIGH"
    assert ext["ranking"] == 0.4
    _assert_valid(alert)


def test_alert_refusals():
    # No registration model identity: fabricating one is prohibited.
    assert translate(_alert_msg(), SCHEMA_ID, based_on=[_PARENT_ID]) == []
    # No confidence: inference confidence is schema-required.
    msg = _alert_msg()
    del msg["alert"]["confidence"]
    assert (
        translate(
            msg,
            SCHEMA_ID,
            registration=_store(_rf_registration_msg()),
            based_on=[_PARENT_ID],
        )
        == []
    )
    # No caller lineage: mandatory-lineage family refuses, never invents.
    assert (
        translate(_alert_msg(), SCHEMA_ID, registration=_store(_rf_registration_msg()))
        == []
    )


def test_alert_ineligible_location_stays_in_extension():
    msg = _alert_msg(location=_location(x=0, y=0))
    events = translate(
        msg,
        SCHEMA_ID,
        registration=_store(_rf_registration_msg()),
        based_on=[_PARENT_ID],
    )

    alert = events[0]
    assert "geo" not in alert["payload"]["claim"]
    ext = alert["payload"]["extensions"]["vendor.sapient"]
    assert ext["location"]["omitted_reason"] == "ZERO_FILL_SUSPECT"


# ---------------------------------------------------------------------------
# TaskAck -> SYSTEM_EVENT / TASK_ACK
# ---------------------------------------------------------------------------


def test_task_ack_accepted_with_task_index():
    original = str(uuid7())
    events = translate(
        _task_ack_msg(),
        SCHEMA_ID,
        task_index={"01J00000000000000000000006": original},
    )

    assert len(events) == 1
    ack = events[0]
    assert ack["event"]["event_subtype"] == "TASK_ACK"
    assert ack["payload"]["state"] == "ACCEPTED"
    assert ack["payload"]["metrics"] == {
        "task_id": "01J00000000000000000000006",
        "original_event_id": original,
    }
    _assert_valid(ack)


def test_task_ack_rejected_and_failed_carry_reason_codes():
    original = str(uuid7())
    index = {"01J00000000000000000000006": original}

    rejected = translate(
        _task_ack_msg(
            task_status="TASK_STATUS_REJECTED", reason=["busy", "out of range"]
        ),
        SCHEMA_ID,
        task_index=index,
    )[0]
    assert rejected["payload"]["state"] == "REJECTED"
    assert rejected["payload"]["metrics"]["reason_code"] == "TASK_REJECTED"
    assert rejected["payload"]["metrics"]["error"] == "busy; out of range"
    _assert_valid(rejected)

    failed = translate(
        _task_ack_msg(task_status="TASK_STATUS_FAILED"), SCHEMA_ID, task_index=index
    )[0]
    assert failed["payload"]["state"] == "FAILED"
    assert failed["payload"]["metrics"]["reason_code"] == "TASK_FAILED"
    _assert_valid(failed)


def test_task_ack_without_resolution_is_refused():
    # The task_id -> COMMAND event correlation is never fabricated.
    assert translate(_task_ack_msg(), SCHEMA_ID) == []
    assert translate(_task_ack_msg(), SCHEMA_ID, task_index={"other": str(uuid7())}) == []


def test_task_ack_null_or_empty_index_value_is_refused():
    # A present key whose value is None/empty is as unresolvable as a
    # missing one; str()-coercion would fabricate the literal "None" as
    # the correlation id (R1-11 R11-03, the R1-10 A1 class).
    assert (
        translate(_task_ack_msg(), SCHEMA_ID, task_index={"01J00000000000000000000006": None})
        == []
    )
    assert (
        translate(_task_ack_msg(), SCHEMA_ID, task_index={"01J00000000000000000000006": ""})
        == []
    )


def test_task_ack_unspecified_status_is_refused():
    events = translate(
        _task_ack_msg(task_status="TASK_STATUS_UNSPECIFIED"),
        SCHEMA_ID,
        task_index={"01J00000000000000000000006": str(uuid7())},
    )
    assert events == []


# ---------------------------------------------------------------------------
# Error -> SYSTEM_EVENT / SCHEMA_VIOLATION
# ---------------------------------------------------------------------------


def test_error_becomes_schema_violation_with_unknown_original_id():
    msg = {
        "timestamp": TS,
        "node_id": NODE,
        "error": {
            "packet": "QkFEUEFDS0VU",
            "error_message": ["unknown field: foo", "bad enum value"],
        },
    }
    events = translate(msg, SCHEMA_ID)

    assert len(events) == 1
    violation = events[0]
    assert violation["event"]["event_subtype"] == "SCHEMA_VIOLATION"
    assert violation["payload"]["state"] == "REJECTED"
    assert violation["payload"]["metrics"]["reason_code"] == "SCHEMA_INVALID"
    assert violation["payload"]["metrics"]["original_event_id"] == "UNKNOWN"
    assert violation["payload"]["metrics"]["error"] == (
        "unknown field: foo; bad enum value"
    )
    assert violation["payload"]["extensions"]["vendor.sapient"]["packet"] == "QkFEUEFDS0VU"
    _assert_valid(violation)


# ---------------------------------------------------------------------------
# Version-aware validate()
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# R1-11 A-02: non-finite PRODUCTS and verbatim vendor->canonical copies
# ---------------------------------------------------------------------------

_BIG = 1e308


def _find_non_finite(value):
    """Independent NaN/inf finder, written for the test.

    Deliberately does NOT call the adapter's ``_has_non_finite``/``_finite``:
    a self-check that runs the same code on both sides is blind by
    construction. Every assertion below is additionally backed by
    ``json.dumps(allow_nan=False)``, a third, C-level oracle.
    """
    import math as _math

    hits = []
    stack = [(value, "$")]
    while stack:
        item, where = stack.pop()
        if isinstance(item, float):
            if not _math.isfinite(item):
                hits.append(where)
        elif isinstance(item, dict):
            for key, child in item.items():
                if isinstance(key, float) and not _math.isfinite(key):
                    hits.append(f"{where}.<non-finite key>")
                stack.append((child, f"{where}.{key}"))
        elif isinstance(item, (list, tuple)):
            for index, child in enumerate(item):
                stack.append((child, f"{where}[{index}]"))
    return hits


def _assert_clean(events, label):
    """Assert every emitted event is clean — and that some were emitted.

    The empty-list guard is the whole point. Without it this helper is
    ``for event in []: ...``, which asserts NOTHING: reverting a per-field
    guard does not make poison escape, it makes the emit-boundary backstop
    refuse the whole event, so the list goes empty and a cleanliness-only
    oracle passes. That is the same mis-scoping as the defect this file
    pins — guarding the product instead of the disposition. Callers that
    genuinely expect a refusal assert ``== []`` themselves; nothing here
    may be satisfied by absence.
    """
    assert events, f"{label}: nothing was emitted, so nothing was checked"
    for event in events:
        assert not _find_non_finite(event), (
            f"{label}: non-finite survived at {_find_non_finite(event)}"
        )
        json.dumps(event, allow_nan=False)
        assert validate(event)[0] == "pass", f"{label}: {validate(event)[1]}"


def _hz_registration_msg():
    # Same node, band edges declared in Hz: two FINITE edges whose
    # difference still overflows (1e308 - -1e308), which no operand guard
    # can see.
    msg = _rf_registration_msg()
    for report in msg["registration"]["mode_definition"][0]["detection_definition"][0][
        "detection_report"
    ]:
        if report["type"] != "amplitude":
            report["units"] = "Hz"
    return msg


def _camera_signal_registration_msg():
    """CAMERA node type, WITH the signal units codex declared.

    Needed to reach the frequency arithmetic at all. ``_rf_registration_msg``
    declares the units but its PASSIVE_RF node type has no
    ``_node_modality``, so once the canonical RF features refuse there is no
    observation left to inspect; ``_camera_registration_msg`` supplies the
    modality but declares no signal units, so ``_canonical_rf_features``
    returns on its FIRST line and ``_freq_hz`` — and therefore the guard
    under test — is never called. Only the combination puts an emitted
    observation and an executed frequency conversion in the same event.
    """
    msg = _rf_registration_msg()
    msg["registration"]["node_definition"] = [{"node_type": "NODE_TYPE_CAMERA"}]
    return msg


def _latency_registration_msg(value, units="TIME_UNITS_SECONDS"):
    msg = _rf_registration_msg()
    msg["registration"]["mode_definition"][0]["maximum_latency"] = {
        "units": units,
        "value": value,
    }
    return msg


_NON_FINITE_CASES = [
    # (label, message, translate kwargs, expected event count) -- every
    # operand below passes the adapter's own _is_number; it is the PRODUCT
    # that leaves float64.
    #
    # The count is load-bearing, not decoration. Cleanliness alone is
    # satisfied by an empty list, and reverting a per-field guard empties
    # the list rather than leaking poison: the emit-boundary backstop
    # refuses the whole event instead. Pinning the DISPOSITION -- how many
    # events survive, not merely that survivors are clean -- is what makes
    # each case fail when the guard it names is removed. Measured collapses
    # under revert: rows 2-5 go 4/1/1/1 -> 0 with `_finite` reverted to
    # identity, rows 6-7 go 4 -> 0 with the registration duration guard
    # reverted. Both were fully invisible to the previous oracle.
    (
        "centre_frequency MHz scaling overflows",
        _detection_msg(
            signal=[{"amplitude": -57.0, "centre_frequency": _BIG,
                     "start_frequency": 1.0, "stop_frequency": 2.0}]
        ),
        # CAMERA + declared signal units on purpose: with the PASSIVE_RF
        # registration a refused centre frequency also removes the node's
        # only modality, so the whole observation vanishes for an unrelated
        # reason and the case cannot see its own guard revert.
        {"registration": _store(_camera_signal_registration_msg())},
        4,
    ),
    (
        "band-edge difference overflows between two finite edges",
        _detection_msg(
            signal=[{"amplitude": -57.0, "centre_frequency": 433.0,
                     "start_frequency": -_BIG, "stop_frequency": _BIG}]
        ),
        {"registration": _store(_hz_registration_msg())},
        4,
    ),
    (
        "TRUE-datum azimuth radians->degrees overflows, then % 360 is NaN",
        _detection_msg(
            signal=None,
            range_bearing={
                "azimuth": _BIG,
                "elevation": 0.0,
                "coordinate_system": "RANGE_BEARING_COORDINATE_SYSTEM_RADIANS_M",
                "datum": "RANGE_BEARING_DATUM_TRUE",
            },
        ),
        {"registration": _store(_camera_registration_msg())},
        1,
    ),
    (
        "MAGNETIC-datum native azimuth/elevation overflow",
        _detection_msg(
            signal=None,
            range_bearing={
                "azimuth": _BIG,
                "elevation": _BIG,
                "coordinate_system": "RANGE_BEARING_COORDINATE_SYSTEM_RADIANS_M",
                "datum": "RANGE_BEARING_DATUM_MAGNETIC",
            },
        ),
        {"registration": _store(_camera_registration_msg())},
        1,
    ),
    (
        "range km->m scaling overflows",
        _detection_msg(
            signal=None,
            range_bearing={
                "range": _BIG,
                "azimuth": 10.0,
                "coordinate_system": "RANGE_BEARING_COORDINATE_SYSTEM_DEGREES_KM",
                "datum": "RANGE_BEARING_DATUM_TRUE",
            },
        ),
        {"registration": _store(_camera_registration_msg())},
        1,
    ),
    (
        "declared maximum_latency overflows the est_error_ms widen",
        _detection_msg(),
        {"registration": _store(_latency_registration_msg(_BIG))},
        4,
    ),
    (
        "declared maximum_latency is NaN",
        _detection_msg(),
        {"registration": _store(_latency_registration_msg(float("nan")))},
        4,
    ),
    (
        "verbatim vendor sub_class copied into the canonical claim",
        _detection_msg(
            classification=[
                {"type": "UAV", "confidence": 0.9,
                 "sub_class": [{"type": "quadcopter", "confidence": float("nan")}]}
            ]
        ),
        {"registration": _store(_rf_registration_msg())},
        3,
    ),
    (
        "non-finite nested deep inside the canonical claim taxonomy",
        _detection_msg(
            classification=[
                {"type": "UAV", "confidence": 0.9,
                 "sub_class": [{"type": "quad",
                                "sub_class": [{"type": "fpv", "score": float("inf")}]}]}
            ]
        ),
        {"registration": _store(_rf_registration_msg())},
        3,
    ),
    (
        "promotion metadata carries a non-finite freshness bound",
        _detection_msg(),
        {
            "registration": _store(_fusion_registration_msg()),
            "based_on": [_PARENT_ID],
            "promotion": {"loop_status": "NOT_REFLECTED",
                          "freshness_ms": float("inf")},
        },
        0,
    ),
    (
        "caller-supplied est_error_ms is already non-finite",
        _detection_msg(),
        {
            "registration": _store(_rf_registration_msg()),
            "timing_quality": {"time_source": "GPS", "sync_state": "SYNCED",
                               "est_error_ms": float("inf")},
        },
        0,
    ),
    (
        "status report power level and fov are non-finite",
        _status_msg(
            power={"level": float("nan"), "source": "POWERSOURCE_MAINS",
                   "status": "POWERSTATUS_OK"},
            field_of_view={"range_bearing": {
                "horizontal_extent": float("inf"),
                "coordinate_system": "RANGE_BEARING_COORDINATE_SYSTEM_DEGREES_M",
                "datum": "RANGE_BEARING_DATUM_TRUE",
            }},
        ),
        {"registration": _store(_rf_registration_msg())},
        2,
    ),
    (
        "alert location and ranking are non-finite",
        _alert_msg(ranking=float("nan"), location=_location(z=float("inf"))),
        {"registration": _store(_rf_registration_msg()), "based_on": [_PARENT_ID]},
        1,
    ),
]


@pytest.mark.parametrize(
    "label,msg,kwargs,expected_events",
    _NON_FINITE_CASES,
    ids=[case[0] for case in _NON_FINITE_CASES],
)
def test_non_finite_never_survives_translate_on_any_path(
    label, msg, kwargs, expected_events
):
    # Form-independent pin for R1-11 A-02: the check drives the PUBLIC API,
    # so it sees a site however that site is written -- unlike the
    # VENDOR_EXTENSION_KEY structural scan, which by construction could
    # only ever see one syntactic shape and therefore could not see the
    # canonical `claim` sink or any arithmetic product at all.
    #
    # Two-sided by construction. The count catches a guard that stopped
    # refusing at the FIELD and let the backstop refuse the EVENT instead
    # (survivors drop to zero and a cleanliness-only oracle never notices);
    # the cleanliness check catches poison that actually escaped. Neither
    # half is sufficient alone -- that asymmetry is what made this pin
    # vacuous for 7 of these rows.
    events = translate(msg, SCHEMA_ID, **kwargs)
    assert len(events) == expected_events, (
        f"{label}: disposition changed -- expected {expected_events} event(s), "
        f"got {len(events)}: "
        f"{[e['event']['event_subtype'] for e in events]}"
    )
    if expected_events:
        _assert_clean(events, label)


def test_non_finite_bearing_product_never_stamps_true_north():
    # The sharp end of A-02: az_deg = inf % 360.0 = NaN was written into
    # payload.bearing while quality.bearing_frame = "TRUE_NORTH" was still
    # stamped beside it -- a geolocation claim that validated clean. The
    # canonical carrier must be absent, and so must the frame assertion.
    events = translate(
        _detection_msg(
            signal=None,
            range_bearing={
                "azimuth": _BIG,
                "coordinate_system": "RANGE_BEARING_COORDINATE_SYSTEM_RADIANS_M",
                "datum": "RANGE_BEARING_DATUM_TRUE",
            },
        ),
        SCHEMA_ID,
        registration=_store(_camera_registration_msg()),
    )
    assert events, "the observation itself must still be emitted"
    payload = events[0]["payload"]
    assert "bearing" not in payload
    assert "bearing_frame" not in payload["quality"]
    # The raw block is preserved as provenance -- refusal, not deletion.
    assert "range_bearing" in payload["extensions"]["vendor.sapient"]
    _assert_clean(events, "bearing product")


def test_non_finite_rf_product_leaves_the_signal_block_as_provenance():
    # A refused canonical frequency must not silently vanish: the signal
    # block falls back to verbatim vendor provenance, the same disposition
    # as unresolvable units.
    #
    # The registration MUST declare signal units. This pin previously used
    # _camera_registration_msg(), which declares none, so
    # _canonical_rf_features returned on its first line and _freq_hz --
    # the `float(value) * factor` overflow this test exists to pin -- was
    # never called even once. Both assertions passed for unrelated reasons:
    # features was the empty dict, and the signal block reached the vendor
    # extension because the UNITS were unresolved, not because the guard
    # fired. The first assertion below fails without the units, which is
    # what keeps that regression from returning silently.
    registration = _store(_camera_signal_registration_msg())
    assert registration.signal_units(NODE)["centre_frequency"] == "MHz", (
        "the frequency arithmetic is unreachable without declared units"
    )
    events = translate(
        _detection_msg(
            signal=[{"amplitude": -57.0, "centre_frequency": _BIG}],
            range_bearing={
                "azimuth": 10.0,
                "coordinate_system": "RANGE_BEARING_COORDINATE_SYSTEM_DEGREES_M",
                "datum": "RANGE_BEARING_DATUM_TRUE",
            },
        ),
        SCHEMA_ID,
        registration=registration,
    )
    assert events
    payload = events[0]["payload"]
    # The units resolved, the amplitude is dBm, the bearing is a clean
    # TRUE-datum azimuth -- so every reason for an absent center_freq_hz
    # OTHER than the overflow guard is excluded here.
    assert payload["bearing"]["az_deg"] == 10.0
    assert "center_freq_hz" not in payload["features"]
    assert "power_dbm" not in payload["features"]
    assert payload["extensions"]["vendor.sapient"]["signal"][0]["centre_frequency"] == _BIG
    _assert_clean(events, "rf product")


def test_the_cleanliness_oracle_is_not_satisfied_by_an_empty_list():
    # Meta-pin. _assert_clean was `for event in events: assert ...`, which
    # checks nothing at all when translate() refuses everything -- and
    # reverting a per-field guard is precisely what empties the list. Seven
    # of the thirteen parametrized cases above passed with the fix they
    # name reverted because of this one line. The oracle itself has to be
    # unable to pass on absence.
    with pytest.raises(AssertionError):
        _assert_clean([], "empty")


def test_freq_guard_is_actually_reached_and_is_the_only_thing_refusing():
    # Companion to the pin above, and the reason it can be trusted: with a
    # centre frequency that does NOT overflow, the identical registration
    # and message shape produce the canonical RF triple. So the absence of
    # center_freq_hz above is attributable to the overflow and to nothing
    # else in the fixture.
    events = translate(
        _detection_msg(
            signal=[{"amplitude": -57.0, "centre_frequency": 433.0}],
            range_bearing={
                "azimuth": 10.0,
                "coordinate_system": "RANGE_BEARING_COORDINATE_SYSTEM_DEGREES_M",
                "datum": "RANGE_BEARING_DATUM_TRUE",
            },
        ),
        SCHEMA_ID,
        registration=_store(_camera_signal_registration_msg()),
    )
    features = events[0]["payload"]["features"]
    assert features["center_freq_hz"] == 433.0 * 1e6
    assert features["power_dbm"] == -57.0
    assert "signal" not in events[0]["payload"]["extensions"]["vendor.sapient"]
    _assert_clean(events, "rf control")


def test_non_finite_claim_refuses_only_that_inference():
    # Refusing the poisoned classification must not take the honest
    # siblings with it (the behaviour inference and the detection-existence
    # claim are unaffected), and the raw entry stays visible as provenance.
    events = translate(
        _detection_msg(
            classification=[
                {"type": "UAV", "confidence": 0.9,
                 "sub_class": [{"type": "quadcopter", "confidence": float("nan")}]},
                {"type": "BIRD", "confidence": 0.2,
                 "sub_class": [{"type": "gull", "confidence": 0.4}]},
            ]
        ),
        SCHEMA_ID,
        registration=_store(_rf_registration_msg()),
    )
    claims = [
        event["payload"]["claim"]
        for event in events
        if event["event"]["event_type"] == "INFERENCE_EVENT"
    ]
    assert {"type": "BIRD", "sub_class": [{"type": "gull", "confidence": 0.4}]} in claims
    assert not any(claim.get("type") == "UAV" for claim in claims)
    assert any(claim.get("type") == "loitering" for claim in claims)
    native = events[0]["payload"]["extensions"]["vendor.sapient"]["native_classification"]
    assert [entry["type"] for entry in native] == ["UAV", "BIRD"]
    _assert_clean(events, "claim sub_class")


def test_validate_reports_a_non_finite_jsonschema_cannot_see():
    # jsonschema min/max comparisons against NaN are all vacuously False,
    # so validate() used to return ("pass", []) for an event with no
    # RFC-8259 wire form. Built by hand, NOT through translate(), so this
    # exercises validate() independently of the emit-boundary guard.
    event = translate(
        _detection_msg(), SCHEMA_ID, registration=_store(_rf_registration_msg())
    )[0]
    assert validate(event) == ("pass", [])
    for path, value in (
        (("payload", "geo", "lat"), float("nan")),
        (("payload", "features", "center_freq_hz"), float("inf")),
        (("payload", "timing_quality", "est_error_ms"), float("-inf")),
    ):
        poisoned = json.loads(json.dumps(event))
        target = poisoned
        for part in path[:-1]:
            target = target[part]
        target[path[-1]] = value
        status, violations = validate(poisoned)
        assert status == "fail", f"{path} validated clean"
        assert any("non-finite" in violation for violation in violations)


def test_refusing_a_parent_refuses_its_dependents_too(monkeypatch):
    # Found by attacking the A-02 guard itself: refusing the observation
    # for a non-finite left the inference events citing it as `based_on`,
    # i.e. asserting lineage to an event that was never emitted. A
    # fabricated parent is exactly what contract 4.8 forbids, so the
    # refusal has to cascade.
    #
    # The poison has to land on the OBSERVATION ONLY, or the cascade is
    # never exercised. This used to use a non-finite vendor dict KEY, which
    # only worked because _drop_non_finite had a hole there -- and that
    # hole was itself a defect (one weird provenance key destroyed four
    # good events). With the hole closed there is no wire-reachable input
    # that poisons the observation and spares its inferences, so the
    # injection is what the backstop exists for in the first place: a
    # canonical site with no per-field guard. Reverting `_finite` to
    # identity simulates exactly that, and the bearing product
    # (inf % 360.0 = NaN) then lands in payload.bearing of the observation
    # while the inferences stay clean.
    from adapters.ingress.sapient import sapient_to_zmeta as s2z

    monkeypatch.setattr(s2z, "_finite", lambda value: value)
    msg = _detection_msg(
        signal=None,
        range_bearing={
            "azimuth": _BIG,
            "coordinate_system": "RANGE_BEARING_COORDINATE_SYSTEM_RADIANS_M",
            "datum": "RANGE_BEARING_DATUM_TRUE",
        },
    )
    events = translate(msg, SCHEMA_ID, registration=_store(_camera_signal_registration_msg()))

    emitted = {event["event"]["event_id"] for event in events}
    for event in events:
        cited = set(event.get("lineage", {}).get("based_on") or ())
        cited |= set(event["payload"].get("based_on") or ())
        assert not cited - emitted, f"dangling parent: {cited - emitted}"
    # The observation carried the poison, so nothing in this call survives.
    assert events == []

    # And prove the dependents really were at stake: without the cascade
    # the three inferences survive citing an observation that was refused.
    monkeypatch.setattr(s2z, "_refuse_non_finite", lambda events: events)
    orphaned = translate(msg, SCHEMA_ID, registration=_store(_camera_signal_registration_msg()))
    assert len(orphaned) == 4
    survivors = {event["event"]["event_id"] for event in orphaned[1:]}
    assert orphaned[0]["event"]["event_id"] not in survivors


def test_cascade_control_emits_the_full_set_with_intact_lineage():
    # Control for the cascade above: the same detection with no poison at
    # all emits the full set, so the cascade is not simply refusing
    # everything it touches.
    clean_msg = _detection_msg()
    clean_msg["detection_report"]["track_info"] = [{"ok": 1.0}]
    clean_events = translate(
        clean_msg, SCHEMA_ID, registration=_store(_rf_registration_msg())
    )
    assert len(clean_events) == 4
    emitted = {event["event"]["event_id"] for event in clean_events}
    for event in clean_events:
        cited = set(event.get("lineage", {}).get("based_on") or ())
        cited |= set(event["payload"].get("based_on") or ())
        assert not cited - emitted
    _assert_clean(clean_events, "cascade control")


# ---------------------------------------------------------------------------
# R1-11 A-02 residuals: an unresolvable declaration must never read cleaner
# than a resolvable one, wire data must never crash, and a defect confined
# to a provenance blob must not destroy canonical data
# ---------------------------------------------------------------------------


_SANE_TIMING = {"time_source": "GPS_PPS", "sync_state": "LOCKED", "est_error_ms": 5.0}


@pytest.mark.parametrize(
    "label,latency_kwargs",
    [
        ("value overflows the ms scale", {"value": _BIG}),
        ("value is NaN", {"value": float("nan")}),
        ("value is Infinity", {"value": float("inf")}),
        ("value has no float64 form", {"value": 10 ** 400}),
        ("units are undeclarable", {"value": 2.0, "units": "TIME_UNITS_FORTNIGHTS"}),
        ("value is strictly negative", {"value": -0.5}),
    ],
)
def test_unresolvable_declared_latency_never_narrows_est_error_ms(label, latency_kwargs):
    # THE laundering this closes: `duration_ms` returned None for an
    # unusable declaration, `max_latency_ms` therefore returned None, and
    # `_timing` skipped the widen -- shipping the caller's un-widened bound
    # with no marker anywhere. Measured before the fix, caller timing held
    # constant at est_error_ms 5.0: a sane 0.5 s declaration produced 505.0
    # and a NaN declaration produced 5.0. The worse the node's input, the
    # TIGHTER the uncertainty it published, which is the one thing an
    # uncertainty field must never do.
    sane = translate(
        _detection_msg(),
        SCHEMA_ID,
        registration=_store(_latency_registration_msg(0.5)),
        timing_quality=dict(_SANE_TIMING),
    )[0]["payload"]["timing_quality"]
    assert sane["est_error_ms"] == 505.0
    assert sane["sync_state"] == "LOCKED"

    broken = translate(
        _detection_msg(),
        SCHEMA_ID,
        registration=_store(_latency_registration_msg(**latency_kwargs)),
        timing_quality=dict(_SANE_TIMING),
    )
    assert len(broken) == 4, f"{label}: the detection itself must still be carried"
    timing = broken[0]["payload"]["timing_quality"]
    # Never narrower than the resolvable case ...
    assert timing["est_error_ms"] >= sane["est_error_ms"], label
    # ... and never narrower than the caller's own bound.
    assert timing["est_error_ms"] >= _SANE_TIMING["est_error_ms"], label
    # ... and the degradation is stated in the canonical, filterable field,
    # not left implicit: a consumer gating on sync_state drops this event.
    assert timing["sync_state"] == "UNSYNCED", label
    assert timing["time_source"] == "UNKNOWN", label
    _assert_clean(broken, label)


def test_declared_latency_states_are_not_collapsed_by_the_store():
    # The store-level half of the same class. `max_latency_ms` returns None
    # for BOTH "never declared" and "declared, unusable"; a caller reading
    # only that cannot tell the quiet node from the broken one.
    never = _store(_camera_registration_msg())
    assert never.max_latency_ms(NODE) is None
    assert never.latency_unresolved(NODE) is False

    broken = _store(_latency_registration_msg(float("nan")))
    assert broken.max_latency_ms(NODE) is None
    assert broken.latency_unresolved(NODE) is True

    sane = _store(_latency_registration_msg(0.5))
    assert sane.max_latency_ms(NODE) == 500.0
    assert sane.latency_unresolved(NODE) is False


def test_a_negative_declared_latency_is_unresolvable_not_a_narrowing():
    # R1-11 CR-01: the SIGN member of the same unresolvable-declaration
    # class. A negative maximum_latency is physically impossible (capture
    # before send) — exactly the malformed-wire threat model this module
    # states for itself — yet `duration_ms` guarded units, numeric-ness and
    # finiteness, never sign, so the declaration resolved as a REAL latency
    # and was ADDED. Measured before the fix, caller LOCKED at 5000.0 ms: a
    # declared -0.5 s published est_error_ms 4500.0, narrower than the
    # caller's own un-widened bound, sync_state still LOCKED, validate()
    # "pass". The disposition is the same as NaN/overflow/unknown-units:
    # unresolvable, degraded UNKNOWN/UNSYNCED, floored — never subtracted.
    store = _store(_latency_registration_msg(-0.5))
    assert store.max_latency_ms(NODE) is None
    assert store.latency_unresolved(NODE) is True

    timing = translate(
        _detection_msg(), SCHEMA_ID, registration=store,
        timing_quality={"time_source": "GPS_PPS", "sync_state": "LOCKED",
                        "est_error_ms": 5000.0},
    )[0]["payload"]["timing_quality"]
    # max(caller 5000, unknown-clock fallback 60000) — never 4500.
    assert timing["est_error_ms"] == 60000.0
    assert timing["sync_state"] == "UNSYNCED"
    assert timing["time_source"] == "UNKNOWN"


def test_a_negative_declared_latency_cannot_eat_the_unknown_clock_floor():
    # CR-01, the no-caller-timing half: with no timing_quality at all the
    # labels are ALREADY UNKNOWN/UNSYNCED, so the number is the only channel
    # left — a declared -55 s ate 55 s off the module's own 60000 ms
    # unknown-clock floor (60000 -> 5000) with zero compensating loudness.
    timing = translate(
        _detection_msg(), SCHEMA_ID,
        registration=_store(_latency_registration_msg(-55.0)),
    )[0]["payload"]["timing_quality"]
    assert timing["est_error_ms"] == 60000.0
    assert timing["sync_state"] == "UNSYNCED"
    assert timing["time_source"] == "UNKNOWN"


def test_a_zero_declared_latency_stays_a_valid_resolvable_bound():
    # The boundary of the sign guard: zero is a physically expressible
    # declaration (no capture->send gap worth stating), so it must keep
    # resolving — the guard is strictly-negative only, never "non-positive".
    store = _store(_latency_registration_msg(0.0))
    assert store.max_latency_ms(NODE) == 0.0
    assert store.latency_unresolved(NODE) is False

    timing = translate(
        _detection_msg(), SCHEMA_ID, registration=store,
        timing_quality=dict(_SANE_TIMING),
    )[0]["payload"]["timing_quality"]
    assert timing["est_error_ms"] == 5.0
    assert timing["sync_state"] == "LOCKED"


def test_a_resolvable_active_mode_is_not_degraded_by_another_broken_mode():
    # Scoping mirrors max_latency_ms exactly: when the ACTIVE mode carries
    # a usable bound that IS the bound, so a different mode's broken
    # declaration must not degrade it. Without this the guard would be a
    # blunt node-wide kill switch and would itself overstate uncertainty.
    msg = _latency_registration_msg(0.5)
    msg["registration"]["mode_definition"].append(
        {"mode_name": "sweep",
         "maximum_latency": {"units": "TIME_UNITS_SECONDS", "value": float("nan")}}
    )
    store = _store(msg)
    assert store.latency_unresolved(NODE, mode="scan") is False
    # No active mode named: the cross-mode maximum applies, and a broken
    # mode makes that maximum not a maximum.
    assert store.latency_unresolved(NODE) is True

    scoped = translate(
        _detection_msg(), SCHEMA_ID, registration=store,
        timing_quality=dict(_SANE_TIMING), active_mode="scan",
    )[0]["payload"]["timing_quality"]
    assert scoped["est_error_ms"] == 505.0
    assert scoped["sync_state"] == "LOCKED"


def test_degradation_never_substitutes_a_clean_value_for_a_poisoned_one():
    # The trap on the other side of this fix: the degradation must not
    # "repair" a caller bound that is already non-finite. Replacing it with
    # the honest-unknown default would trade one laundering for a quieter
    # one -- the event would validate clean while the caller's timing was
    # meaningless. It stays non-finite and the emit boundary refuses.
    events = translate(
        _detection_msg(),
        SCHEMA_ID,
        registration=_store(_latency_registration_msg(float("nan"))),
        timing_quality={"time_source": "GPS_PPS", "sync_state": "LOCKED",
                        "est_error_ms": float("inf")},
    )
    assert events == []
    # A caller bound WIDER than the unknown-clock default is kept, never
    # narrowed down to it.
    wide = translate(
        _detection_msg(),
        SCHEMA_ID,
        registration=_store(_latency_registration_msg(float("nan"))),
        timing_quality={"time_source": "GPS_PPS", "sync_state": "LOCKED",
                        "est_error_ms": 100_000.0},
    )[0]["payload"]["timing_quality"]
    assert wide["est_error_ms"] == 100_000.0


def _leaf_paths(node, path=()):
    if isinstance(node, dict):
        for key, child in node.items():
            yield from _leaf_paths(child, path + (key,))
    elif isinstance(node, list):
        for index, child in enumerate(node):
            yield from _leaf_paths(child, path + (index,))
    else:
        yield path


@pytest.mark.parametrize("huge", [10 ** 400, -(10 ** 400)])
@pytest.mark.parametrize(
    "content,kwargs",
    [
        ("detection", {}),
        ("status", {}),
        ("alert", {"based_on": [_PARENT_ID]}),
        ("task_ack", {"task_index": {"01J00000000000000000000006": _PARENT_ID}}),
    ],
)
def test_an_integer_with_no_float64_form_refuses_instead_of_crashing(
    huge, content, kwargs
):
    # `math.isfinite` RAISES OverflowError on a Python int outside the
    # float64 range, and json.loads builds exactly such an int from a plain
    # integer literal -- so a 400-digit number anywhere in a DetectionReport
    # aborted translate() rather than refusing. Wire data must never crash
    # the ingest loop (fail closed).
    #
    # The sweep covers EVERY leaf of EVERY content branch, not one
    # hand-picked field: the arm the original overflow sweep never injected
    # was missed precisely because it enumerated float shapes (proto3 JSON
    # "NaN"/"Infinity") and never a bare integer literal.
    base = {
        "detection": _detection_msg(),
        "status": _status_msg(),
        "alert": _alert_msg(),
        "task_ack": _task_ack_msg(),
    }[content]

    paths = list(_leaf_paths(base))
    assert len(paths) >= 4, "the sweep must actually cover the message"
    for path in paths:
        msg = json.loads(json.dumps(base))
        target = msg
        for part in path[:-1]:
            target = target[part]
        target[path[-1]] = huge
        # No try/except on purpose: a raise here IS the failure.
        events = translate(
            msg, SCHEMA_ID, registration=_store(_rf_registration_msg()), **kwargs
        )
        if events:
            _assert_clean(events, f"huge int at {path}")


@pytest.mark.parametrize("huge", [10 ** 400, -(10 ** 400)])
def test_a_registration_with_an_unscalable_duration_does_not_take_the_node_down(huge):
    # The same shape sits on the line duration_ms scales, inside
    # RegistrationStore.ingest -- so one malformed Registration aborted the
    # capture for the WHOLE node, losing units, model identity and taxonomy
    # that parsed perfectly well.
    store = _store(_latency_registration_msg(huge))
    assert store.max_latency_ms(NODE) is None
    assert store.latency_unresolved(NODE) is True
    # Everything else in that same registration survived.
    assert store.model_identity(NODE) == {"name": "Acme RFSense-9", "version": "4.2.1"}
    assert store.signal_units(NODE)["centre_frequency"] == "MHz"
    assert store.velocity_factor_mps(NODE) == 1.0


def test_a_non_finite_vendor_key_drops_its_entry_and_keeps_the_detection():
    # A defect confined to a verbatim provenance blob must be cleaned where
    # the pass-through doctrine lives, not escalated into total loss. Before
    # this, one non-finite KEY in a vendor block turned four good events
    # into zero -- silently discarding geo, bearing, RF features and the
    # classification the adapter had resolved correctly.
    msg = _detection_msg()
    # Three placements at once: a key inside a list-of-dicts, a key at the
    # top of a vendor block, and a key nested two levels down -- so the fix
    # cannot be a special case for the one shape that was reported.
    msg["detection_report"]["track_info"] = [
        {float("nan"): "dropped", "ok": 1.0},
        {"kept": 2.0},
    ]
    msg["detection_report"]["object_info"] = {
        float("inf"): "dropped",
        "nested": {float("-inf"): "dropped", "deep": {float("nan"): "dropped",
                                                      "leaf": 3.0}},
    }
    events = translate(msg, SCHEMA_ID, registration=_store(_rf_registration_msg()))

    assert len(events) == 4, "canonical data survives a bad provenance key"
    payload = events[0]["payload"]
    assert payload["geo"]["lat"] == 43.49
    assert payload["features"]["center_freq_hz"] == 433.0 * 1e6
    # The entry is gone; its siblings and its list position are not.
    vendor = payload["extensions"]["vendor.sapient"]
    assert vendor["track_info"] == [{"ok": 1.0}, {"kept": 2.0}]
    assert vendor["object_info"] == {"nested": {"deep": {"leaf": 3.0}}}
    _assert_clean(events, "vendor key")


def test_a_non_finite_vendor_value_still_drops_and_a_list_still_drops_whole():
    # Guard the pre-existing half of the doctrine while changing it: adding
    # the KEY rule must not disturb the VALUE rule, nor the deliberate
    # asymmetry that a bare non-finite inside a numeric array drops the
    # whole array (removing one element silently re-indexes the rest).
    from adapters.ingress.sapient import sapient_to_zmeta as s2z

    assert s2z._drop_non_finite({"a": float("nan"), "b": 1.0}) == {"b": 1.0}
    assert s2z._drop_non_finite({"s": [1.0, float("nan"), 3.0]}) == {}
    assert s2z._drop_non_finite({"s": [{"v": float("nan")}, {"v": 2.0}]}) == {
        "s": [{}, {"v": 2.0}]
    }
    assert s2z._drop_non_finite([1.0, float("inf")]) == []


def test_the_emit_boundary_backstop_is_still_behind_the_vendor_cleaner():
    # Closing the vendor-key gap must not weaken the module-wide backstop:
    # it is what covers canonical sites the per-field guards do not reach.
    from adapters.ingress.sapient import sapient_to_zmeta as s2z

    clean = _envelope_stub("a")
    poisoned = _envelope_stub("b")
    poisoned["payload"]["metrics"] = {"x": float("nan")}
    assert s2z._refuse_non_finite([clean, poisoned]) == [clean]
    # A non-finite dict KEY at a canonical site is caught too -- the
    # cleaner only runs on vendor blocks.
    keyed = _envelope_stub("c")
    keyed["payload"]["metrics"] = {float("inf"): 1.0}
    assert s2z._refuse_non_finite([keyed]) == []


def _envelope_stub(event_id):
    return {
        "zmeta_version": "1.0",
        "event": {"event_id": event_id, "event_type": "SYSTEM_EVENT",
                  "event_subtype": "SENSOR_STATUS", "ts": TS},
        "payload": {},
    }


def test_non_finite_scan_is_iterative_not_recursive():
    # The scan walks wire-shaped structures whose nesting depth is
    # producer-controlled. A recursive walk would only trade a laundered
    # value for a RecursionError (the R1-11 A-04 shape), so depth well past
    # sys.getrecursionlimit() must still return an answer.
    from adapters.ingress.sapient import sapient_to_zmeta as s2z

    deep = {"leaf": float("nan")}
    for _ in range(50_000):
        deep = {"vendor": deep}
    assert s2z._has_non_finite(deep) is True
    clean = {"leaf": 1.0}
    for _ in range(50_000):
        clean = {"vendor": clean}
    assert s2z._has_non_finite(clean) is False


def test_validate_selects_schema_per_zmeta_version():
    obs = translate(
        _detection_msg(), SCHEMA_ID, registration=_store(_rf_registration_msg())
    )[0]
    sensor = translate(_status_msg(), SCHEMA_ID)[0]

    assert validate(obs) == ("pass", [])
    assert validate(sensor) == ("pass", [])


def test_validate_fails_unsupported_version_and_broken_events():
    status, violations = validate({"zmeta_version": "2.0"})
    assert status == "fail" and "unsupported" in violations[0]

    obs = translate(
        _detection_msg(), SCHEMA_ID, registration=_store(_rf_registration_msg())
    )[0]
    broken = json.loads(json.dumps(obs))
    broken["payload"]["features"].pop("power_dbm")
    status, violations = validate(broken)
    assert status == "fail" and violations

    # A 1.1.0-only subtype relabeled as 1.0 must fail against the locked
    # 1.0 schema — proof the dispatch actually selects per version.
    sensor = translate(_status_msg(), SCHEMA_ID)[0]
    relabeled = json.loads(json.dumps(sensor))
    relabeled["zmeta_version"] = "1.0"
    status, violations = validate(relabeled)
    assert status == "fail" and violations


# ---------------------------------------------------------------------------
# R1-11 B-03: the degradation must be a FLOOR over the honest widen, never a
# substitute for it. The property is monotonicity, so it is tested as a
# property: worse input must never produce a cleaner event.
# ---------------------------------------------------------------------------


def _two_mode_registration_msg(broken_value, units="TIME_UNITS_SECONDS",
                               sane_seconds=0.5):
    """One mode with a RESOLVABLE latency, plus one the store cannot resolve.

    This is the shape no previous pin built at the EVENT level. The
    single-mode fixtures cannot express the defect: the discarded term is
    the surviving cross-mode bound, and a node with only a broken mode has
    no surviving bound to discard.
    """
    msg = _latency_registration_msg(sane_seconds)
    msg["registration"]["mode_definition"].append(
        {"mode_name": "sweep",
         "maximum_latency": {"units": units, "value": broken_value}}
    )
    return msg


_BROKEN_LATENCY_DECLARATIONS = [
    ("NaN value", {"broken_value": float("nan")}),
    ("Infinity value", {"broken_value": float("inf")}),
    ("value overflows the ms scale", {"broken_value": _BIG}),
    ("integer with no float64 form", {"broken_value": 10 ** 400}),
    ("undeclarable units", {"broken_value": 2.0, "units": "TIME_UNITS_FORTNIGHTS"}),
    ("strictly negative value", {"broken_value": -0.5}),
]

_CALLER_TIMINGS = [
    # The default path is listed FIRST because it is the one the previous
    # pins could not see: with no caller timing the labels are ALREADY
    # UNKNOWN/UNSYNCED, so the degradation adds no loudness and the number
    # is the only channel left. That is exactly where the regression lived.
    ("caller supplies nothing (module default 60000)", None),
    ("caller LOCKED at 59900 ms (just under the fallback)",
     {"time_source": "GPS_PPS", "sync_state": "LOCKED", "est_error_ms": 59900.0}),
    ("caller LOCKED at 5 ms", dict(_SANE_TIMING)),
    ("caller UNSYNCED at 120000 ms (wider than the fallback)",
     {"time_source": "UNKNOWN", "sync_state": "UNSYNCED", "est_error_ms": 120000.0}),
]


def _published_timing(store, timing_quality):
    events = translate(
        _detection_msg(), SCHEMA_ID, registration=store,
        **({} if timing_quality is None else {"timing_quality": dict(timing_quality)}),
    )
    # Indexing an empty list raises: this oracle cannot be satisfied by a
    # refusal, which is how the previous non-finite oracle went vacuous.
    return events[0]["payload"]["timing_quality"], events


@pytest.mark.parametrize("broken_label,broken_kwargs", _BROKEN_LATENCY_DECLARATIONS)
@pytest.mark.parametrize("caller_label,caller_timing", _CALLER_TIMINGS)
def test_adding_a_broken_mode_never_narrows_the_published_est_error_ms(
    broken_label, broken_kwargs, caller_label, caller_timing
):
    # THE B-03 laundering, stated as the invariant rather than as an
    # exemplar: take a node, add a second mode whose maximum_latency this
    # adapter cannot resolve, change NOTHING else. The node now knows
    # strictly LESS about its own latency, so the number it publishes must
    # not go down. Measured before this was closed, caller supplying
    # nothing: sane-only 60500.0 -> sane+broken 60000.0, with sync_state
    # identical in both, i.e. zero compensating loudness.
    #
    # The degraded branch returned before the widen, so it substituted
    # max(caller, 60000) for caller + the cross-mode bound the store STILL
    # held and still returned from max_latency_ms(). The fix computes the
    # widen first and applies the degradation as a floor on top.
    sane_only = _store(_latency_registration_msg(0.5))
    plus_broken = _store(_two_mode_registration_msg(**broken_kwargs))

    # Precondition: the store really does still hold a resolvable bound on
    # the degraded node. Without this the test could pass vacuously on a
    # node that has nothing left to discard.
    assert plus_broken.max_latency_ms(NODE) == 500.0, broken_label
    assert plus_broken.latency_unresolved(NODE) is True, broken_label
    assert sane_only.latency_unresolved(NODE) is False

    good, good_events = _published_timing(sane_only, caller_timing)
    degraded, degraded_events = _published_timing(plus_broken, caller_timing)
    label = f"{broken_label} / {caller_label}"

    assert len(good_events) == 4, label
    assert len(degraded_events) == 4, label
    assert degraded["est_error_ms"] >= good["est_error_ms"], label
    # The floor is a floor, and the widen still happened underneath it.
    assert degraded["est_error_ms"] >= 60000.0, label
    # The degradation is stated where a consumer can filter on it.
    assert degraded["sync_state"] == "UNSYNCED", label
    assert degraded["time_source"] == "UNKNOWN", label
    _assert_clean(degraded_events, label)


def test_the_degraded_bound_still_includes_the_resolvable_latency():
    # The specific arithmetic, pinned as a value rather than an inequality,
    # so a future "simplification" back to max(caller, DEFAULT) fails here
    # with the number in the message. 59900 + 500 = 60400 > 60000, so the
    # surviving latency term is the only thing that can produce this.
    store = _store(_two_mode_registration_msg(float("nan")))
    timing = translate(
        _detection_msg(), SCHEMA_ID, registration=store,
        timing_quality={"time_source": "GPS_PPS", "sync_state": "LOCKED",
                        "est_error_ms": 59900.0},
    )[0]["payload"]["timing_quality"]
    assert timing["est_error_ms"] == 60400.0
    assert timing["sync_state"] == "UNSYNCED"

    # And with no caller timing at all: 60000 (module fallback) + 500.
    default = translate(
        _detection_msg(), SCHEMA_ID, registration=store,
    )[0]["payload"]["timing_quality"]
    assert default["est_error_ms"] == 60500.0


def test_the_degradation_floor_survives_the_widen_reorder():
    # The other side of the reorder: a node whose ONLY mode is broken has
    # no resolvable bound to fold in, so the floor is all there is. This is
    # the case the original remediation got right and the reorder must keep.
    store = _store(_latency_registration_msg(float("nan")))
    assert store.max_latency_ms(NODE) is None
    timing = translate(
        _detection_msg(), SCHEMA_ID, registration=store,
        timing_quality=dict(_SANE_TIMING),
    )[0]["payload"]["timing_quality"]
    assert timing["est_error_ms"] == 60000.0
    assert timing["sync_state"] == "UNSYNCED"


# ---------------------------------------------------------------------------
# R1-11 R2-11 / R2-12: a DECLARED value this adapter cannot carry to a
# canonical field must survive as provenance. Deleting it is indistinguishable
# from a producer that never declared it.
# ---------------------------------------------------------------------------

_UNMAPPABLE_HUGE = int("7" * 400)          # no float64 form; distinctive digits
_UNMAPPABLE_STR = "ZZ_NOT_A_NUMBER_ZZ"     # a wire type this adapter cannot map

_RB_TRUE = {"coordinate_system": "RANGE_BEARING_COORDINATE_SYSTEM_DEGREES_M",
            "datum": "RANGE_BEARING_DATUM_TRUE"}

# (label, detection_report override builder, vendor key that must appear).
# Enumerated from the code, not from the report: every site where a wire key
# is read through a gate that can decline it without leaving a marker. Four
# functions, eight keys -- the register named three gates in one function.
_DECLARED_BUT_UNMAPPABLE = [
    ("range_bearing.range",
     lambda v: {"range_bearing": dict(_RB_TRUE, range=v, azimuth=10.0)},
     "range_bearing"),
    ("range_bearing.azimuth",
     lambda v: {"range_bearing": dict(_RB_TRUE, range=100.0, azimuth=v)},
     "range_bearing"),
    ("range_bearing.elevation",
     lambda v: {"range_bearing": dict(_RB_TRUE, azimuth=10.0, elevation=v)},
     "range_bearing"),
    ("range_bearing.range_error",
     lambda v: {"range_bearing": dict(_RB_TRUE, azimuth=10.0, range_error=v)},
     "range_bearing"),
    ("range_bearing.azimuth_error",
     lambda v: {"range_bearing": dict(_RB_TRUE, azimuth=10.0, azimuth_error=v)},
     "range_bearing"),
    ("range_bearing.elevation_error",
     lambda v: {"range_bearing": dict(_RB_TRUE, azimuth=10.0, elevation_error=v)},
     "range_bearing"),
    ("enu_velocity.up_rate",
     lambda v: {"enu_velocity": {"east_rate": 1.0, "north_rate": 2.0, "up_rate": v}},
     "enu_velocity"),
    ("enu_velocity.east_rate_error",
     lambda v: {"enu_velocity": {"east_rate": 1.0, "north_rate": 2.0,
                                 "east_rate_error": v}},
     "enu_velocity"),
    ("location.x_error",
     lambda v: {"location": dict(_location(), x_error=v)},
     "location_errors"),
    ("signal.start_frequency",
     lambda v: {"signal": [{"amplitude": -57.0, "centre_frequency": 433.0,
                            "start_frequency": v, "stop_frequency": 200.0}]},
     "signal"),
    ("signal.stop_frequency",
     lambda v: {"signal": [{"amplitude": -57.0, "centre_frequency": 433.0,
                            "start_frequency": 100.0, "stop_frequency": v}]},
     "signal"),
]


@pytest.mark.parametrize("poison,poison_label",
                         [(_UNMAPPABLE_HUGE, "integer with no float64 form"),
                          (_UNMAPPABLE_STR, "non-numeric wire value")])
@pytest.mark.parametrize("label,build,vendor_key", _DECLARED_BUT_UNMAPPABLE)
def test_a_declared_value_this_adapter_cannot_map_is_preserved_not_deleted(
    poison, poison_label, label, build, vendor_key
):
    # The disposition the module states for itself (`_is_number`: "it
    # refuses here and stays verbatim in the vendor provenance block like
    # every other unmappable value"; README: "the raw block is preserved as
    # provenance") was true for some gates and false for these. The FALSE
    # branch of an `_is_number` gate left `fully_carried` True, so the raw
    # block was never written and the producer's declaration vanished from
    # the event entirely -- no canonical field, no provenance, no marker,
    # indistinguishable from a producer that never declared it.
    #
    # Both poison shapes matter. The float twin (1e308) already took the
    # `_finite`-is-None path and WAS preserved, which is why the asymmetry
    # went unnoticed: the two are the same magnitude family on the wire and
    # took opposite paths in the adapter.
    msg = _detection_msg(**build(poison))
    events = translate(
        msg, SCHEMA_ID, registration=_store(_camera_signal_registration_msg())
    )
    assert events, f"{label}: the detection itself must still be carried"
    vendor = events[0]["payload"]["extensions"]["vendor.sapient"]
    assert vendor_key in vendor, (
        f"{label} ({poison_label}): declared and then deleted -- "
        f"vendor keys were {sorted(vendor)}"
    )
    # And the value itself is really there, not just the container.
    blob = json.dumps(events)
    needle = str(poison) if poison is _UNMAPPABLE_HUGE else poison
    assert needle in blob, f"{label} ({poison_label}): container kept, value lost"
    _assert_clean(events, f"{label} / {poison_label}")


def test_the_provenance_marker_is_precise_not_blanket():
    # The trap on the other side: marking everything not-fully-carried
    # would satisfy the test above while making the vendor block a verbatim
    # copy of the wire on every event -- which is its own dishonesty, since
    # "not fully carried" would then be asserted about data that was. A
    # fully mappable report must carry NONE of these provenance keys.
    msg = _detection_msg(
        range_bearing=dict(_RB_TRUE, range=100.0, azimuth=10.0, elevation=5.0),
        enu_velocity={"east_rate": 1.0, "north_rate": 2.0},
        signal=[{"amplitude": -57.0, "centre_frequency": 433.0,
                 "start_frequency": 100.0, "stop_frequency": 200.0}],
    )
    events = translate(
        msg, SCHEMA_ID, registration=_store(_camera_signal_registration_msg())
    )
    vendor = events[0]["payload"]["extensions"]["vendor.sapient"]
    for key in ("range_bearing", "enu_velocity", "signal", "location_errors"):
        assert key not in vendor, f"{key} preserved for a fully-carried report"
    payload = events[0]["payload"]
    assert payload["bearing"] == {"az_deg": 10.0, "el_deg": 5.0}
    assert payload["features"]["range_m"] == 100.0
    assert payload["features"]["bandwidth_hz"] == 100.0 * 1e6


def test_an_absent_band_edge_keeps_the_sentinel_and_preserves_nothing():
    # The sentinel's original, honest case must not be disturbed: a Signal
    # that never declared band edges cannot state bandwidth, the declared
    # 0.0 "not measured" sentinel marks that, and there is no declaration to
    # preserve. Only a DECLARED-but-unresolvable edge preserves the block.
    events = translate(
        _detection_msg(signal=[{"amplitude": -57.0, "centre_frequency": 433.0}]),
        SCHEMA_ID,
        registration=_store(_camera_signal_registration_msg()),
    )
    payload = events[0]["payload"]
    assert payload["features"]["bandwidth_hz"] == 0.0
    assert "signal" not in payload["extensions"]["vendor.sapient"]


def test_an_inverted_band_declaration_is_preserved_beside_the_sentinel():
    # stop < start resolves both edges and still yields no bandwidth. The
    # sentinel alone would state "not measured" about a producer that did
    # measure, and the raw block was dropped because features was non-None
    # -- destroying the only evidence a consumer could use to disagree.
    events = translate(
        _detection_msg(signal=[{"amplitude": -57.0, "centre_frequency": 433.0,
                                "start_frequency": 200.0, "stop_frequency": 100.0}]),
        SCHEMA_ID,
        registration=_store(_camera_signal_registration_msg()),
    )
    payload = events[0]["payload"]
    assert payload["features"]["bandwidth_hz"] == 0.0
    signal = payload["extensions"]["vendor.sapient"]["signal"]
    assert signal[0]["start_frequency"] == 200.0
    assert signal[0]["stop_frequency"] == 100.0


def test_an_elevation_with_no_azimuth_is_preserved():
    # Elevation is only ever mapped alongside a usable azimuth, so a
    # declared elevation on its own reaches no canonical carrier at all.
    # This member is not reachable by poisoning a leaf of any shipped
    # fixture -- it needs a message shape the fixtures do not build -- which
    # is why a leaf sweep alone cannot enumerate this class.
    events = translate(
        _detection_msg(range_bearing=dict(_RB_TRUE, elevation=5.0)),
        SCHEMA_ID,
        registration=_store(_camera_signal_registration_msg()),
    )
    payload = events[0]["payload"]
    assert "bearing" not in payload
    assert payload["extensions"]["vendor.sapient"]["range_bearing"]["elevation"] == 5.0


def test_a_power_block_that_maps_to_nothing_is_preserved_not_erased():
    # Same class as the detection-report gates, in the status branch. A
    # PLATFORM_STATUS with no power fact in it is not a status, so refusing
    # the EVENT is right -- but the raw block was that declaration's only
    # carrier, so refusing the datum with it erased the node's own report
    # of its power state. Refuse the datum a canonical field; do not erase
    # it.
    for label, power in (
        ("level out of range, source unmapped",
         {"level": 150, "source": "POWERSOURCE_SOLAR", "status": "POWERSTATUS_OK"}),
        ("non-numeric level, source unmapped",
         {"level": "LOW", "source": "POWERSOURCE_SOLAR"}),
        ("integer level with no float64 form",
         {"level": 10 ** 400, "source": "POWERSOURCE_SOLAR"}),
    ):
        events = translate(_status_msg(power=power), SCHEMA_ID)
        assert len(events) == 1, label          # no PLATFORM_STATUS, correctly
        vendor = events[0]["payload"]["extensions"]["vendor.sapient"]
        assert vendor["power"] == power, label
        _assert_clean(events, label)

    # And when the block DOES map, it rides the PLATFORM_STATUS event as
    # before -- not duplicated onto the sensor status.
    mapped = translate(
        _status_msg(power={"level": 55, "source": "POWERSOURCE_MAINS"}), SCHEMA_ID
    )
    assert len(mapped) == 2
    assert "power" not in mapped[0]["payload"]["extensions"]["vendor.sapient"]
    assert mapped[1]["payload"]["metrics"]["battery_pct"] == 55
    assert mapped[1]["payload"]["extensions"]["vendor.sapient"]["power"]["level"] == 55


def test_the_provenance_marker_is_precise_on_the_native_datum_branch_too():
    # The precision oracle above uses the TRUE-datum branch. The
    # MAGNETIC/GRID/PLATFORM branch carries elevation through a DIFFERENT
    # canonical field (features.bearing_native_el_deg), so a marker that is
    # correct on one branch can be wrong on the other -- and a mutation
    # confined to the native branch would be invisible to a TRUE-only pin.
    native = dict(_RB_TRUE, datum="RANGE_BEARING_DATUM_MAGNETIC")
    events = translate(
        _detection_msg(range_bearing=dict(native, range=100.0, azimuth=10.0,
                                          elevation=5.0)),
        SCHEMA_ID,
        registration=_store(_camera_signal_registration_msg()),
    )
    payload = events[0]["payload"]
    assert payload["features"]["bearing_native_deg"] == 10.0
    assert payload["features"]["bearing_native_el_deg"] == 5.0
    assert payload["features"]["range_m"] == 100.0
    assert "bearing" not in payload
    assert "range_bearing" not in payload["extensions"]["vendor.sapient"], (
        "a fully-carried native-datum report needs no provenance copy"
    )

    # ... and an unmappable elevation on the SAME branch still preserves.
    poisoned = translate(
        _detection_msg(range_bearing=dict(native, azimuth=10.0,
                                          elevation=_UNMAPPABLE_STR)),
        SCHEMA_ID,
        registration=_store(_camera_signal_registration_msg()),
    )
    assert (poisoned[0]["payload"]["extensions"]["vendor.sapient"]
            ["range_bearing"]["elevation"] == _UNMAPPABLE_STR)


def test_the_canonical_claim_guard_refuses_on_its_own_not_via_the_backstop(monkeypatch):
    # R1-11 R1-27(2) recorded the A-02(a) fix -- the canonical
    # `payload.claim.sub_class` refusal -- as UNPINNABLE, because removing
    # it produces a byte-identical event list: the emit-boundary backstop
    # drops the same inference one layer later. That is true of any
    # end-to-end oracle, and it is exactly how a defence-in-depth layer
    # rots unnoticed.
    #
    # It is pinnable by ISOLATING the layer. With the backstop neutralized,
    # the claim guard is the only thing standing between a NaN inside a
    # vendor taxonomy and a canonical `claim` presented to a consumer as
    # adjudicable evidence. Remove the guard and this test emits the
    # poisoned inference; keep it and only the clean sibling survives.
    from adapters.ingress.sapient import sapient_to_zmeta as s2z

    monkeypatch.setattr(s2z, "_refuse_non_finite", lambda events: events)

    msg = _detection_msg(
        classification=[
            {"type": "UAV", "confidence": 0.9,
             "sub_class": [{"type": "quadcopter", "level": float("nan")}]},
            {"type": "GROUND_VEHICLE", "confidence": 0.7,
             "sub_class": [{"type": "truck", "level": 2}]},
        ]
    )
    events = translate(msg, SCHEMA_ID, registration=_store(_rf_registration_msg()))

    # The trailing detection-existence claim carries no `type`, so read the
    # taxonomy claims specifically rather than every CLASSIFICATION event.
    claims = [
        event["payload"]["claim"].get("type")
        for event in events
        if event["event"]["event_subtype"] == "CLASSIFICATION"
    ]
    assert "UAV" not in claims, (
        "the poisoned taxonomy reached a canonical claim with the backstop "
        f"neutralized; claims were {claims}"
    )
    assert "GROUND_VEHICLE" in claims, (
        f"the clean sibling entry was collateral damage; claims were {claims}"
    )
    # The refused entry is not lost -- it stays verbatim in the observation's
    # provenance block, which is the whole point of refusing the CLAIM
    # rather than the report.
    native = events[0]["payload"]["extensions"]["vendor.sapient"]
    assert [entry["type"] for entry in native["native_classification"]] == [
        "UAV", "GROUND_VEHICLE"
    ]


def test_unnamed_mode_latency_declaration_never_silently_drops():
    # Attack-pass completion (2026-07-27): a maximum_latency declared in a
    # mode_definition entry with no usable mode_name was skipped whole -
    # no widen for a sane bound, no latency_unresolved for a broken one -
    # while the named twin adjudicated both. Pin parity, both directions.
    tq = {"time_source": "GPS_PPS", "sync_state": "LOCKED", "est_error_ms": 5000.0}

    def _unnamed(msg):
        del msg["registration"]["mode_definition"][0]["mode_name"]
        return msg

    named_sane = translate(
        _detection_msg(), SCHEMA_ID,
        registration=_store(_latency_registration_msg(0.5)),
        timing_quality=dict(tq),
    )[0]["payload"]["timing_quality"]
    unnamed_sane = translate(
        _detection_msg(), SCHEMA_ID,
        registration=_store(_unnamed(_latency_registration_msg(0.5))),
        timing_quality=dict(tq),
    )[0]["payload"]["timing_quality"]
    assert unnamed_sane == named_sane
    assert unnamed_sane["est_error_ms"] == 5500.0

    named_broken = translate(
        _detection_msg(), SCHEMA_ID,
        registration=_store(_latency_registration_msg(float("nan"))),
        timing_quality=dict(tq),
    )
    unnamed_broken = translate(
        _detection_msg(), SCHEMA_ID,
        registration=_store(_unnamed(_latency_registration_msg(float("nan")))),
        timing_quality=dict(tq),
    )
    assert [e["payload"]["timing_quality"] for e in unnamed_broken] == [
        e["payload"]["timing_quality"] for e in named_broken
    ]


def test_wire_mode_named_like_the_synthetic_key_cannot_collide():
    # Verifier finding (2026-07-27, introduced-by-batch, closed same day):
    # the unnamed-mode entry first used a STRING synthetic key, so a wire
    # mode literally named "__unnamed_mode_0" overwrote it - silently
    # dropping the unnamed 9 s bound (the exact laundering the fix
    # exists to prevent). The tuple key cannot equal any wire string.
    tq = {"time_source": "GPS_PPS", "sync_state": "LOCKED", "est_error_ms": 5000.0}
    msg = _latency_registration_msg(9.0)
    del msg["registration"]["mode_definition"][0]["mode_name"]
    msg["registration"]["mode_definition"].append(
        {
            "mode_name": "__unnamed_mode_0",
            "maximum_latency": {"units": "TIME_UNITS_SECONDS", "value": 0.1},
        }
    )
    timing = translate(
        _detection_msg(), SCHEMA_ID,
        registration=_store(msg),
        timing_quality=dict(tq),
    )[0]["payload"]["timing_quality"]
    # max(9000, 100) widens by the unnamed bound; the string-key collision
    # produced 5100.0 here.
    assert timing["est_error_ms"] == 14000.0


# ---------------------------------------------------------------------------
# Real gateway pipeline (first independent-implementation interop run):
# schema-only validate() cannot see producer-authority, role, or a
# denylisted key nested inside a vendor extension block, and both of the
# defects below reached that blind spot -- every adapter test suite up to
# this one only ran schema-only validate(), never gateway/src/validators.py.
# ---------------------------------------------------------------------------


def test_detection_events_pass_the_real_gateway_pipeline_not_schema_only():
    # Interop-run finding: a realistic DetectionReport with a classification
    # entry (each entry carries its own "confidence") passed schema-only
    # validate() while the REAL gateway refused it on two independent
    # grounds:
    #
    # 1. native_classification/native_behaviour copied each entry VERBATIM,
    #    confidence included. policy/semantics.yaml's observation identity
    #    denylist (track_id, entity_class, classification, label,
    #    class_name, confidence) is enforced recursively at every nesting
    #    depth (gateway/src/validators.py._find_forbidden_key), so the
    #    verbatim copy fails OBSERVATION_HAS_IDENTITY even though the
    #    top-level extension keys are all clean.
    # 2. Every INFERENCE_EVENT defaulted to node_role EDGE via _envelope's
    #    default, and policy/roles.yaml permits INFERENCE_EVENT only from
    #    GATEWAY -- so every inference this adapter emits failed
    #    EVENT_TYPE_NOT_ALLOWED_FOR_ROLE even though producer-authority
    #    grants sapient-ingress the INFERENCE_EVENT type.
    events = translate(
        _detection_msg(), SCHEMA_ID, registration=_store(_rf_registration_msg())
    )
    assert [e["event"]["event_type"] for e in events] == [
        "OBSERVATION_EVENT",
        "INFERENCE_EVENT",
        "INFERENCE_EVENT",
        "INFERENCE_EVENT",
    ]

    for event in events:
        # Schema-only: passes today for every event, on both defects -- the
        # exact vacuous-verification shape that hid them from every prior
        # adapter test suite (neither defect is a schema violation).
        _assert_valid(event)
        # Real gateway pipeline: red on today's code for the OBSERVATION_EVENT
        # (identity laundering) and every INFERENCE_EVENT (role).
        _assert_gateway_valid(event)

    # An observation is an edge measurement; an inference is a gateway-layer
    # claim. Only the latter moves role.
    obs, classification, behaviour, existence = events
    assert obs["source"]["node_role"] == "EDGE"
    for inference in (classification, behaviour, existence):
        assert inference["source"]["node_role"] == "GATEWAY"
