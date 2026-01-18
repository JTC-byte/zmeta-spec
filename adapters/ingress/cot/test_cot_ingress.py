import json
from pathlib import Path

from jsonschema import Draft202012Validator

from adapters.ingress.cot.cot_to_zmeta_template import cot_dict_to_zmeta_track_state


ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = ROOT / "schema" / "zmeta-event-1.0.schema.json"
SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
VALIDATOR = Draft202012Validator(SCHEMA)


def test_cot_to_track_state_schema_valid():
    cot = {
        "uid": "cot-1",
        "type": "a-f-G-U-C",
        "time": "2025-01-17T15:20:00Z",
        "stale": "2025-01-17T15:20:05Z",
        "point": {"lat": 34.0, "lon": -118.0, "hae": 120.0},
        "confidence": 0.7,
    }

    event = cot_dict_to_zmeta_track_state(cot)
    assert event["event"]["event_type"] == "STATE_EVENT"
    assert event["event"]["event_subtype"] == "TRACK_STATE"
    VALIDATOR.validate(event)
