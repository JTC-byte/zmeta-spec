import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from adapters.ingress.cot.cot_to_zmeta_template import cot_dict_to_zmeta_track_state
from zmeta_uuid import uuid7


ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = ROOT / "schema" / "zmeta-event-1.0.schema.json"
SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
VALIDATOR = Draft202012Validator(SCHEMA, format_checker=FormatChecker())


def test_cot_to_track_state_schema_valid():
    cot = {
        "uid": "cot-1",
        "type": "a-f-G-U-C",
        "time": "2025-01-17T15:20:00Z",
        "stale": "2025-01-17T15:20:05Z",
        "point": {"lat": 34.0, "lon": -118.0, "hae": 120.0},
        "confidence": 0.7,
        "based_on": [str(uuid7())],
    }

    event = cot_dict_to_zmeta_track_state(cot)
    assert event["event"]["event_type"] == "STATE_EVENT"
    assert event["event"]["event_subtype"] == "TRACK_STATE"
    VALIDATOR.validate(event)


def test_cot_ingress_normalizes_utc_offset_timestamp():
    cot = {
        "uid": "cot-1",
        "type": "a-f-G-U-C",
        "time": "2025-01-17T15:20:00+00:00",
        "stale": "2025-01-17T15:20:05+00:00",
        "point": {"lat": 34.0, "lon": -118.0, "hae": 120.0},
        "confidence": 0.7,
        "based_on": [str(uuid7())],
    }

    event = cot_dict_to_zmeta_track_state(cot)

    assert event["event"]["ts"] == "2025-01-17T15:20:00Z"
    assert event["payload"]["valid_for_ms"] == 5000
    assert event["payload"]["timing_quality"]["last_sync_ts"] == "2025-01-17T15:20:00Z"
    VALIDATOR.validate(event)
