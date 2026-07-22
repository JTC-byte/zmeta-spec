from adapters.egress.klv.zmeta_to_klv_tagdict_template import zmeta_observation_to_klv_tagdict


def test_observation_to_klv_tagdict():
    event = {
        "zmeta_version": "1.0",
        "event": {
            "event_id": "019c2b5d-0ba0-7536-ad67-ba859248dc5c",
            "event_type": "OBSERVATION_EVENT",
            "event_subtype": "RF",
            "ts": "2025-01-17T15:20:00Z",
        },
        "source": {
            "platform_id": "platform-1",
            "node_role": "EDGE",
            "producer": "rf-sensor",
            "sensor_id": "sensor-1",
        },
        "payload": {
            "modality": "RF",
            "features": {
                "center_freq_hz": 2450000000,
                "bandwidth_hz": 20000000,
                "power_dbm": -35.2,
            },
            "geo": {"lat": 34.0, "lon": -118.0, "alt_m": 120.0},
        },
    }

    tagdict = zmeta_observation_to_klv_tagdict(event)
    assert tagdict["timestamp"] == "2025-01-17T15:20:00Z"
    assert tagdict["platform_id"] == "platform-1"
    assert tagdict["features"]["center_freq_hz"] == 2450000000


def test_non_observation_returns_none():
    event = {"event": {"event_type": "STATE_EVENT"}}
    assert zmeta_observation_to_klv_tagdict(event) is None


# R1-11 A-01: geo and features are copied wholesale from the payload, so a
# non-finite value anywhere inside them reaches the tag dict. Refuse instead.
NON_FINITE = (float("nan"), float("inf"), float("-inf"))


def _observation_event():
    return {
        "zmeta_version": "1.0",
        "event": {
            "event_id": "019c2b5d-0ba0-7536-ad67-ba859248dc5c",
            "event_type": "OBSERVATION_EVENT",
            "event_subtype": "RF",
            "ts": "2025-01-17T15:20:00Z",
        },
        "source": {
            "platform_id": "platform-1",
            "node_role": "EDGE",
            "producer": "rf-sensor",
            "sensor_id": "sensor-1",
        },
        "payload": {
            "modality": "RF",
            "features": {"center_freq_hz": 2450000000.0, "bandwidth_hz": 20000000.0},
            "geo": {"lat": 34.0, "lon": -118.0, "alt_m": 120.0},
        },
    }


def test_non_finite_tag_values_refuse():
    import json

    for path in (
        ("payload", "geo", "lat"),
        ("payload", "geo", "lon"),
        ("payload", "geo", "alt_m"),
        ("payload", "features", "center_freq_hz"),
        ("payload", "features", "bandwidth_hz"),
    ):
        for value in NON_FINITE:
            event = _observation_event()
            node = event
            for part in path[:-1]:
                node = node[part]
            node[path[-1]] = value
            assert zmeta_observation_to_klv_tagdict(event) is None, (path, value)

    result = zmeta_observation_to_klv_tagdict(_observation_event())
    assert result is not None
    json.dumps(result, allow_nan=False)
