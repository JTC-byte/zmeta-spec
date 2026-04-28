import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from adapters.ingress.mavlink.mavlink_to_zmeta_template import mavlink_decoded_to_zmeta_system_events


ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = ROOT / "schema" / "zmeta-event-1.0.schema.json"
SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
VALIDATOR = Draft202012Validator(SCHEMA, format_checker=FormatChecker())


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
