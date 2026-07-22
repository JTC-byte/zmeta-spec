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


# R1-11 A-01: a non-finite number must refuse, not project. Value scoped -
# every number that reaches the projected track, not a list of the ones
# someone remembered.
NON_FINITE = (float("nan"), float("inf"), float("-inf"))


def _track_state_event():
    return {
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
        "confidence": 0.9,
    }


def test_non_finite_track_values_refuse():
    import copy
    import json

    for path in (
        ("payload", "geo", "lat"),
        ("payload", "geo", "lon"),
        ("payload", "geo", "alt_m"),
        ("confidence",),
    ):
        for value in NON_FINITE:
            event = _track_state_event()
            node = event
            for part in path[:-1]:
                node = node[part]
            node[path[-1]] = value
            assert zmeta_state_to_jreap_track_json(event) is None, (path, value)

    # The clean case still projects, and what it projects is RFC 8259.
    result = zmeta_state_to_jreap_track_json(_track_state_event())
    assert result is not None
    json.dumps(result, allow_nan=False)
