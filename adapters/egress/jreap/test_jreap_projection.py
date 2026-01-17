from adapters.egress.jreap.zmeta_state_to_jreap_track_json import zmeta_state_to_jreap_track_json


def test_track_state_projection():
    event = {
        "event": {
            "event_type": "STATE_EVENT",
            "event_subtype": "TRACK_STATE",
            "ts": "2025-01-17T15:20:00Z",
        },
        "payload": {
            "track_id": "track-1",
            "geo": {"lat": 34.0, "lon": -118.0, "alt_m": 120.0},
            "valid_for_ms": 1000,
        },
    }

    result = zmeta_state_to_jreap_track_json(event)
    assert result["track_id"] == "track-1"
    assert result["stale_time"] == "2025-01-17T15:20:01Z"


def test_non_state_event_returns_none():
    event = {"event": {"event_type": "OBSERVATION_EVENT"}, "payload": {}}
    assert zmeta_state_to_jreap_track_json(event) is None
