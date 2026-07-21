import json
import uuid

import pytest

from adapters.egress.sapient.zmeta_command_to_sapient_task import zmeta_command_to_sapient_task
from adapters.egress.sapient.zmeta_state_to_sapient_detection import (
    SAPIENT_EGRESS_LOSS_NOTES,
    zmeta_state_to_sapient_detection,
)

NODE_ID = "0f2c8b4e-9f1d-4e6a-8a3b-1c5d7e9f0a2b"
DEST_ID = "7a1b3c5d-2e4f-4a6b-8c0d-9e1f3a5b7c9d"


def _command_event(task_type="GOTO", **payload_overrides):
    payload = {
        "task_id": "task-1",
        "task_type": task_type,
        "valid_for_ms": 600000,
        "requires_deconfliction": True,
    }
    if task_type == "GOTO":
        payload["target_geo"] = {"lat": 34.0, "lon": -118.0}
    payload.update(payload_overrides)
    return {
        "event": {
            "event_type": "COMMAND_EVENT",
            "event_subtype": task_type,
            "ts": "2026-07-17T12:00:00Z",
        },
        "payload": payload,
    }


def _state_event(**payload_overrides):
    payload = {
        "track_id": "trk-9",
        "geo": {"lat": 34.0, "lon": -118.0, "alt_m": 120.0},
        "class": "UAV",
        "valid_for_ms": 5000,
    }
    payload.update(payload_overrides)
    return {
        "event": {
            "event_type": "STATE_EVENT",
            "event_subtype": "TRACK_STATE",
            "ts": "2026-07-17T12:00:00Z",
        },
        "payload": payload,
        "confidence": 0.8,
    }


def _task(event, **kwargs):
    kwargs.setdefault("node_id", NODE_ID)
    kwargs.setdefault("destination_id", DEST_ID)
    return zmeta_command_to_sapient_task(event, **kwargs)


def _detection(event, **kwargs):
    kwargs.setdefault("node_id", NODE_ID)
    return zmeta_state_to_sapient_detection(event, **kwargs)


# --- command egress: happy paths -------------------------------------------


def test_goto_maps_move_to():
    message = _task(_command_event())

    assert message["timestamp"] == "2026-07-17T12:00:00Z"
    assert message["node_id"] == NODE_ID
    assert message["destination_id"] == DEST_ID

    task = message["task"]
    assert task["task_id"] == "task-1"
    assert task["control"] == "CONTROL_START"
    assert task["task_end_time"] == "2026-07-17T12:10:00Z"

    locations = task["command"]["move_to"]["locations"]
    assert len(locations) == 1
    location = locations[0]
    assert location["x"] == -118.0
    assert location["y"] == 34.0
    assert location["coordinate_system"] == "LOCATION_COORDINATE_SYSTEM_LAT_LNG_DEG_M"
    assert location["datum"] == "LOCATION_DATUM_WGS84_E"
    assert set(location) == {"x", "y", "coordinate_system", "datum"}


def test_track_target_maps_follow():
    event = _command_event("TRACK_TARGET", target_track_id="trk-9")
    message = _task(event, track_to_object={"trk-9": "01HSAPIENTOBJECT0000000000"})

    command = message["task"]["command"]
    assert command == {"follow": {"follow_object_id": "01HSAPIENTOBJECT0000000000"}}


def test_change_sensor_mode_maps_mode_change():
    event = _command_event("CHANGE_SENSOR_MODE", sensor_id="cam-1", sensor_mode="IR_WIDE")
    message = _task(event)

    assert message["task"]["command"] == {"mode_change": "IR_WIDE"}


def test_priority_never_crosses():
    message = _task(_command_event(priority="HIGH"))

    assert "priority" not in json.dumps(message)


# --- command egress: refusals ----------------------------------------------


def test_non_command_event_refuses():
    assert _task({"event": {"event_type": "STATE_EVENT"}, "payload": {}}) is None


def test_undeconflicted_command_refuses():
    assert _task(_command_event(requires_deconfliction=False)) is None
    event = _command_event()
    del event["payload"]["requires_deconfliction"]
    assert _task(event) is None


@pytest.mark.parametrize(
    "task_type",
    ["ORBIT", "HOLD", "SEARCH_BOX", "LOITER", "SCAN_RF", "RETURN_TO_BASE", "LAND"],
)
def test_unmapped_task_types_refuse(task_type):
    event = _command_event(task_type, target_geo={"lat": 34.0, "lon": -118.0})
    assert _task(event) is None


def test_missing_required_command_fields_refuse():
    for field in ("task_id", "task_type", "valid_for_ms"):
        event = _command_event()
        del event["payload"][field]
        assert _task(event) is None


def test_missing_ts_refuses():
    event = _command_event()
    del event["event"]["ts"]
    assert _task(event) is None


def test_missing_node_identity_refuses():
    assert _task(_command_event(), node_id=None) is None
    assert _task(_command_event(), destination_id=None) is None


def test_goto_without_target_geo_refuses():
    event = _command_event()
    del event["payload"]["target_geo"]
    assert _task(event) is None


def test_track_target_without_map_refuses():
    event = _command_event("TRACK_TARGET", target_track_id="trk-9")
    assert _task(event) is None
    assert _task(event, track_to_object={"other-track": "01HOTHEROBJECT000000000000"}) is None


def test_change_sensor_mode_without_mode_refuses():
    event = _command_event("CHANGE_SENSOR_MODE", sensor_id="cam-1")
    assert _task(event) is None


# --- command egress: altitude never crosses --------------------------------


def test_goto_altitude_in_target_geo_raises():
    event = _command_event(target_geo={"lat": 34.0, "lon": -118.0, "alt_m": 120.0})
    with pytest.raises(ValueError):
        _task(event)


def test_goto_altitude_adjacent_extension_keys_do_not_leak():
    # Keys chosen to dodge the canonical-altitude denylist: proof that the
    # guard is whitelist construction, not denylist stripping.
    event = _command_event(
        extensions={"alt_hint_m": 4567.0, "z": 8901.0, "flight_level": "FL045"}
    )
    message = _task(event)

    serialized = json.dumps(message)
    assert "alt_hint_m" not in serialized
    assert "4567" not in serialized
    assert '"z"' not in serialized
    assert "8901" not in serialized
    assert "flight_level" not in serialized
    assert "z" not in message["task"]["command"]["move_to"]["locations"][0]


# --- state egress: happy paths ---------------------------------------------


def test_state_maps_detection_report():
    message = _detection(_state_event())

    assert message["timestamp"] == "2026-07-17T12:00:00Z"
    assert message["node_id"] == NODE_ID

    detection = message["detection_report"]
    assert detection["object_id"] == "trk-9"
    assert uuid.UUID(detection["report_id"]).version == 7

    location = detection["location"]
    assert location["x"] == -118.0
    assert location["y"] == 34.0
    assert location["z"] == 120.0
    assert location["coordinate_system"] == "LOCATION_COORDINATE_SYSTEM_LAT_LNG_DEG_M"
    assert location["datum"] == "LOCATION_DATUM_WGS84_E"

    assert detection["classification"] == [{"type": "UAV", "confidence": 0.8}]
    assert "object_info" not in detection


def test_state_without_class_omits_classification():
    event = _state_event()
    del event["payload"]["class"]
    detection = _detection(event)["detection_report"]

    assert "classification" not in detection


def test_state_velocity_from_heading_speed():
    event = _state_event(heading_deg=90.0, speed_mps=10.0)
    velocity = _detection(event)["detection_report"]["enu_velocity"]

    assert velocity["east_rate"] == pytest.approx(10.0)
    assert velocity["north_rate"] == pytest.approx(0.0, abs=1e-9)
    # No fabricated up-rate: ZMeta TrackStatePayload carries no climb rate.
    assert set(velocity) == {"east_rate", "north_rate"}


def test_state_velocity_needs_both_heading_and_speed():
    assert "enu_velocity" not in _detection(_state_event())["detection_report"]
    event = _state_event(speed_mps=10.0)
    assert "enu_velocity" not in _detection(event)["detection_report"]
    event = _state_event(heading_deg=45.0)
    assert "enu_velocity" not in _detection(event)["detection_report"]


# --- state egress: refusals ------------------------------------------------


def test_non_state_event_refuses():
    assert _detection({"event": {"event_type": "OBSERVATION_EVENT"}, "payload": {}}) is None
    event = _state_event()
    event["event"]["event_subtype"] = "PLATFORM_STATE"
    assert _detection(event) is None


def test_state_missing_ts_refuses():
    event = _state_event()
    del event["event"]["ts"]
    assert _detection(event) is None


def test_state_missing_node_id_refuses():
    assert _detection(_state_event(), node_id=None) is None


def test_state_missing_track_id_refuses():
    event = _state_event()
    del event["payload"]["track_id"]
    assert _detection(event) is None


def test_state_partial_geo_refuses():
    for field in ("lat", "lon", "alt_m"):
        event = _state_event()
        del event["payload"]["geo"][field]
        assert _detection(event) is None
    event = _state_event()
    del event["payload"]["geo"]
    assert _detection(event) is None


def test_quarantined_event_refuses():
    event = _state_event(
        extensions={
            "risk_adjudication": [
                {"risk_dimension": "external_promotion", "policy_decision": "QUARANTINE_ACCEPT"}
            ]
        }
    )
    assert _detection(event) is None


def test_rejected_event_refuses():
    event = _state_event(
        extensions={"risk_adjudication": [{"policy_decision": "REJECTED"}]}
    )
    assert _detection(event) is None


def test_prohibited_export_use_refuses():
    event = _state_event(
        extensions={
            "risk_adjudication": [
                {"policy_decision": "WARN_ACCEPT", "prohibited_uses": ["COALITION_EXPORT"]}
            ]
        }
    )
    assert _detection(event) is None


def test_grant_list_omitting_export_refuses():
    event = _state_event(
        extensions={
            "risk_adjudication": [
                {"policy_decision": "WARN_ACCEPT", "allowed_uses": ["DISPLAY", "AAR_ONLY"]}
            ]
        }
    )
    assert _detection(event) is None


def test_caller_use_labels_prohibiting_export_refuse():
    assert _detection(_state_event(), use_labels={"prohibited_uses": ["COALITION_EXPORT"]}) is None
    assert _detection(_state_event(), use_labels={"allowed_uses": ["DISPLAY"]}) is None


def test_export_use_parameter_scopes_the_refusal():
    event = _state_event(
        extensions={
            "risk_adjudication": [
                {"policy_decision": "WARN_ACCEPT", "prohibited_uses": ["COALITION_EXPORT"]}
            ]
        }
    )
    # The same event exports on a path the labels do not prohibit, and the
    # warn adjudication still travels as a self-label.
    message = _detection(event, export_use="DISPLAY")
    assert message is not None
    info = message["detection_report"]["object_info"]
    assert info[0]["type"] == "zmeta.risk"


# --- state egress: self-labels ---------------------------------------------


def test_warn_risk_attaches_self_label():
    record = {
        "risk_dimension": "timing",
        "reason_code": "TIMING_STALE",
        "policy_decision": "WARN_ACCEPT",
        "prohibited_uses": ["COMMAND_BASIS"],
    }
    event = _state_event(extensions={"risk_adjudication": [record]})
    detection = _detection(event)["detection_report"]

    info = detection["object_info"]
    assert len(info) == 1
    assert info[0]["type"] == "zmeta.risk"
    labels = json.loads(info[0]["value"])
    assert labels == [
        {
            "risk_dimension": "timing",
            "reason_code": "TIMING_STALE",
            "policy_decision": "WARN_ACCEPT",
            "prohibited_uses": ["COMMAND_BASIS"],
        }
    ]


def test_caller_use_labels_travel_in_self_label():
    message = _detection(
        _state_event(),
        use_labels={"allowed_uses": ["COALITION_EXPORT", "DISPLAY"]},
    )
    info = message["detection_report"]["object_info"]
    labels = json.loads(info[0]["value"])
    assert labels == [{"allowed_uses": ["COALITION_EXPORT", "DISPLAY"]}]


def test_degraded_timing_attaches_self_label():
    timing = {
        "time_source": "NTP",
        "sync_state": "HOLDOVER",
        "est_error_ms": 250,
        "last_sync_ts": "2026-07-17T11:00:00Z",
    }
    event = _state_event(timing_quality=timing)
    info = _detection(event)["detection_report"]["object_info"]

    assert len(info) == 1
    assert info[0]["type"] == "zmeta.timing_quality"
    assert json.loads(info[0]["value"]) == timing


def test_locked_timing_attaches_no_self_label():
    timing = {
        "time_source": "GPS_PPS",
        "sync_state": "LOCKED",
        "est_error_ms": 1,
        "last_sync_ts": "2026-07-17T11:59:00Z",
    }
    event = _state_event(timing_quality=timing)
    assert "object_info" not in _detection(event)["detection_report"]


# --- loss documentation -----------------------------------------------------


def test_loss_notes_cover_dropped_concerns():
    for concern in ("lineage", "timing_quality", "risk_adjudication", "valid_for_ms"):
        assert concern in SAPIENT_EGRESS_LOSS_NOTES
        assert SAPIENT_EGRESS_LOSS_NOTES[concern]
