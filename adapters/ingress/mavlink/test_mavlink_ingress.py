import json
import importlib.util
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from adapters.ingress.mavlink.mavlink_to_zmeta_template import (
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
    VALIDATOR.validate(event)
    ok, violations = validators.validate_producer_authority(
        event, POLICY["producer_authority"], POLICY["violation_severities"]
    )
    assert ok, violations


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
