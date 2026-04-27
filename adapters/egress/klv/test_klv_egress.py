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
