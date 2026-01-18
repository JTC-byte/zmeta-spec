import json
from pathlib import Path

from jsonschema import Draft202012Validator

from adapters.ingress.jreap.jreap_track_to_zmeta_template import jreap_track_dict_to_zmeta_track_state


ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = ROOT / "schema" / "zmeta-event-1.0.schema.json"
SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
VALIDATOR = Draft202012Validator(SCHEMA)


def test_jreap_track_to_state_schema_valid():
    track = {
        "track_id": "track-1",
        "lat": 34.0,
        "lon": -118.0,
        "hae_m": 120.0,
        "timestamp": "2025-01-17T15:20:00Z",
        "stale_time": "2025-01-17T15:20:05Z",
        "track_type": "UNKNOWN",
        "confidence": 0.6,
    }

    event = jreap_track_dict_to_zmeta_track_state(track)
    assert event["event"]["event_type"] == "STATE_EVENT"
    assert event["event"]["event_subtype"] == "TRACK_STATE"
    VALIDATOR.validate(event)
