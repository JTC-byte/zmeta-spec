import json
import importlib.util
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from adapters.ingress.mavlink.mavlink_to_zmeta_template import (
    decode_global_position_int,
    mavlink_decoded_to_zmeta_system_events,
    translate_platform_state,
)


ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = ROOT / "schema" / "zmeta-event-1.0.schema.json"
SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
VALIDATOR = Draft202012Validator(SCHEMA, format_checker=FormatChecker())
VALIDATORS_PATH = ROOT / "gateway" / "src" / "validators.py"
spec = importlib.util.spec_from_file_location("zmeta_validators", VALIDATORS_PATH)
validators = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validators)
POLICY = validators.load_policy(ROOT / "policy")


_PARENT_EVENT_ID = "019c2b5c-c053-70e1-b6aa-340000000001"


def test_mavlink_platform_state_promotion_authority_valid():
    event = translate_platform_state(
        {
            "lat": 34.0,
            "lon": -118.0,
            "alt_m": 120.0,
            "heading_deg": 90.0,
            "speed_mps": 12.0,
            "gps_fix_type": 3,
            "satellites_visible": 10,
            "source_event_uid": "mavlink:sysid-1:seq-1",
            "based_on": [_PARENT_EVENT_ID],
        },
        platform_id="uav-1",
        producer="mavlink-adapter",
        ts="2025-01-17T15:20:00+00:00",
    )

    assert event["event"]["event_type"] == "STATE_EVENT"
    assert event["payload"]["extensions"]["external_promotion"]["promotion_policy_id"] == (
        "PROMOTE-MAVLINK-STATE-V1"
    )
    assert event["lineage"]["transform"].startswith("promote:mavlink-telemetry@")
    assert event["lineage"]["based_on"] == [_PARENT_EVENT_ID]
    VALIDATOR.validate(event)
    ok, violations = validators.validate_producer_authority(
        event, POLICY["producer_authority"], POLICY["violation_severities"]
    )
    assert ok, violations


_BASE_STATE = {
    "lat": 34.0,
    "lon": -118.0,
    "alt_m": 120.0,
    "speed_mps": 12.0,
    "gps_fix_type": 3,
    "satellites_visible": 10,
    "source_event_uid": "mavlink:sysid-1:seq-1",
    "based_on": [_PARENT_EVENT_ID],
}


def _state_event(**overrides):
    translator_kwargs = {}
    if "heading_frame" in overrides:
        translator_kwargs["heading_frame"] = overrides.pop("heading_frame")
    if "heading_source" in overrides:
        translator_kwargs["heading_source"] = overrides.pop("heading_source")
    state = dict(_BASE_STATE)
    state.update(overrides)
    return translate_platform_state(
        state,
        platform_id="uav-1",
        producer="mavlink-adapter",
        ts="2025-01-17T15:20:00+00:00",
        **translator_kwargs,
    )


def test_mavlink_known_heading_without_frame_omits_canonical_heading():
    # GLOBAL_POSITION_INT.hdg does not declare a true-vs-magnetic reference,
    # so the adapter must not emit canonical payload.heading_deg by default.
    event = _state_event(heading_deg=90.0)

    assert "heading_deg" not in event["payload"]
    assert event["payload"]["quality"]["mavlink_hdg_frame_unknown_deg"] == 90.0
    assert "heading_source" not in event["payload"]["quality"]
    VALIDATOR.validate(event)


def test_mavlink_true_north_heading_frame_emits_canonical_heading():
    event = _state_event(
        heading_deg=90.0,
        heading_frame="TRUE_NORTH",
        heading_source="AHRS_TRUE",
    )

    assert event["payload"]["heading_deg"] == 90.0
    assert event["payload"]["quality"]["heading_source"] == "AHRS_TRUE"
    assert "mavlink_hdg_frame_unknown_deg" not in event["payload"]["quality"]
    VALIDATOR.validate(event)


def test_mavlink_invalid_heading_frame_rejected():
    import pytest

    with pytest.raises(ValueError, match="heading_frame"):
        _state_event(heading_deg=90.0, heading_frame="MAGNETIC_NORTH")


def test_mavlink_unknown_heading_omitted_not_fabricated():
    # decode_global_position_int yields heading_deg=None for hdg=UINT16_MAX;
    # the translator must omit heading_deg, never emit None or a 0.0 default.
    event = _state_event(heading_deg=None)

    assert "heading_deg" not in event["payload"]
    assert "mavlink_hdg_frame_unknown_deg" not in event["payload"]["quality"]
    VALIDATOR.validate(event)


def test_mavlink_absent_heading_omitted_not_defaulted_to_zero():
    event = _state_event()

    assert "heading_deg" not in event["payload"]
    VALIDATOR.validate(event)


def test_decode_global_position_int_unknown_hdg_yields_none():
    decoded = decode_global_position_int(
        {"lat": 340000000, "lon": -1180000000, "alt": 120000, "hdg": 65535}
    )

    assert decoded["heading_deg"] is None


def test_decode_global_position_int_missing_lat_lon_yields_none():
    # A GLOBAL_POSITION_INT without lat/lon must not decode to (0, 0); absent
    # coordinates decode to None so downstream refuses to fabricate a position.
    decoded = decode_global_position_int({"alt": 120000, "hdg": 65535})

    assert decoded["lat"] is None
    assert decoded["lon"] is None


def test_decode_global_position_int_present_lat_lon_preserved():
    decoded = decode_global_position_int(
        {"lat": 340000000, "lon": -1180000000, "alt": 120000, "hdg": 9000}
    )

    assert decoded["lat"] == 34.0
    assert decoded["lon"] == -118.0


def test_mavlink_refuses_null_island_without_fix():
    # ArduPilot emits lat=0, lon=0 before GPS lock (fix types 0/1). The adapter
    # must refuse to fabricate a null-island TRACK_STATE position.
    assert _state_event(lat=0.0, lon=0.0, gps_fix_type=0) is None
    assert _state_event(lat=0.0, lon=0.0, gps_fix_type=1) is None


def test_mavlink_refuses_absent_lat_lon():
    state = {k: v for k, v in _BASE_STATE.items() if k not in ("lat", "lon")}
    event = translate_platform_state(
        state,
        platform_id="uav-1",
        producer="mavlink-adapter",
        ts="2025-01-17T15:20:00+00:00",
    )

    assert event is None


def test_mavlink_refuses_missing_lineage_instead_of_fabricating():
    # STATE_EVENT lineage is mandatory (contract 4.8) and must reference real
    # events. Without caller-supplied based_on or source_zmeta_event_id, the
    # adapter refuses to emit rather than fabricating a parent id.
    state = {k: v for k, v in _BASE_STATE.items() if k != "based_on"}
    event = translate_platform_state(
        state,
        platform_id="uav-1",
        producer="mavlink-adapter",
        ts="2025-01-17T15:20:00+00:00",
    )

    assert event is None


def test_mavlink_source_zmeta_event_id_used_as_lineage_fallback():
    state = {k: v for k, v in _BASE_STATE.items() if k != "based_on"}
    state["source_zmeta_event_id"] = _PARENT_EVENT_ID
    event = translate_platform_state(
        state,
        platform_id="uav-1",
        producer="mavlink-adapter",
        ts="2025-01-17T15:20:00+00:00",
    )

    assert event["lineage"]["based_on"] == [_PARENT_EVENT_ID]
    VALIDATOR.validate(event)


def test_mavlink_system_events_omit_lineage_by_default():
    from adapters.ingress.mavlink.mavlink_to_zmeta_template import (
        translate_link_status,
        translate_time_status,
    )

    link = translate_link_status(platform_id="uav-1", ts="2025-01-17T15:20:00+00:00")
    time_status = translate_time_status(
        platform_id="uav-1",
        est_error_ms=1.0,
        last_sync_ts="2025-01-17T15:19:59+00:00",
        ts="2025-01-17T15:20:00+00:00",
    )

    assert "lineage" not in link
    assert "lineage" not in time_status
    VALIDATOR.validate(link)
    VALIDATOR.validate(time_status)


def test_mavlink_system_events_carry_caller_lineage_when_supplied():
    from adapters.ingress.mavlink.mavlink_to_zmeta_template import translate_link_status

    link = translate_link_status(
        platform_id="uav-1",
        ts="2025-01-17T15:20:00+00:00",
        based_on=[_PARENT_EVENT_ID],
    )

    assert link["lineage"]["based_on"] == [_PARENT_EVENT_ID]
    VALIDATOR.validate(link)


def test_mavlink_null_island_with_2d_fix_still_emits():
    # A claimed 2D+ fix at exactly (0, 0) is not the no-fix signature; the
    # adapter keeps the position and lets quality/confidence carry the doubt.
    event = _state_event(lat=0.0, lon=0.0, gps_fix_type=2)

    assert event is not None
    assert event["payload"]["geo"]["lat"] == 0.0
    assert event["payload"]["geo"]["lon"] == 0.0
    VALIDATOR.validate(event)


def test_mavlink_no_fix_with_nonzero_coords_still_emits_degraded():
    # Stale-but-real coordinates without a current fix remain emitted with
    # geo_status STALE and floor confidence; only fabricated (0, 0) is refused.
    event = _state_event(gps_fix_type=0)

    assert event is not None
    assert event["payload"]["quality"]["geo_status"] == "STALE"
    assert event["confidence"] == 0.2
    VALIDATOR.validate(event)


def test_mavlink_task_ack_schema_valid():
    msg = {
        "msg_type": "MISSION_ACK",
        "task_id": "task-1",
        "original_event_id": "019c3ef3-98c4-7c99-8daf-3643ed0bc8ef",
        "state": "RECEIVED",
    }
    events = mavlink_decoded_to_zmeta_system_events(
        msg,
        platform_id="uav-1",
        producer="mavlink",
        ts="2025-01-17T15:20:00+00:00",
    )

    assert len(events) == 1
    event = events[0]
    assert event["event"]["event_type"] == "SYSTEM_EVENT"
    assert event["event"]["ts"] == "2025-01-17T15:20:00Z"
    assert event["payload"]["system_type"] == "TASK_ACK"
    VALIDATOR.validate(event)


def test_mavlink_time_status_normalizes_last_sync_ts():
    msg = {
        "msg_type": "SYSTEM_TIME",
        "state": "UP",
        "time_source": "GPS_PPS",
        "sync_state": "LOCKED",
        "est_error_ms": 1,
        "last_sync_ts": "2025-01-17T15:19:59+00:00",
    }
    events = mavlink_decoded_to_zmeta_system_events(
        msg,
        platform_id="uav-1",
        producer="mavlink",
        ts="2025-01-17T15:20:00+00:00",
    )

    event = events[0]
    assert event["event"]["ts"] == "2025-01-17T15:20:00Z"
    assert event["payload"]["metrics"]["last_sync_ts"] == "2025-01-17T15:19:59Z"
    VALIDATOR.validate(event)
