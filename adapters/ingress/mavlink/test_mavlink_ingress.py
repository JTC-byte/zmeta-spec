import json
from pathlib import Path

from jsonschema import Draft202012Validator

from adapters.ingress.mavlink.mavlink_to_zmeta_template import mavlink_decoded_to_zmeta_system_events


ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = ROOT / "schema" / "zmeta-event-1.0.schema.json"
SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
VALIDATOR = Draft202012Validator(SCHEMA)


def test_mavlink_task_ack_schema_valid():
    msg = {"msg_type": "MISSION_ACK", "task_id": "task-1", "state": "RECEIVED"}
    events = mavlink_decoded_to_zmeta_system_events(
        msg,
        platform_id="uav-1",
        producer="mavlink",
        ts="2025-01-17T15:20:00Z",
    )

    assert len(events) == 1
    event = events[0]
    assert event["event"]["event_type"] == "SYSTEM_EVENT"
    assert event["payload"]["system_type"] == "TASK_ACK"
    VALIDATOR.validate(event)
