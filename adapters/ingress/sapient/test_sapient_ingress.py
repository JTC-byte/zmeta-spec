import json

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


def _assert_valid(event):
    status, violations = validate(event)
    assert status == "pass", violations


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
    # Denylist names stay out of features and the extension block.
    denylist = {"confidence", "classification", "track_id", "entity_class", "label"}
    assert not denylist & set(ext)
    assert not denylist & set(events[0]["payload"]["features"])


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
