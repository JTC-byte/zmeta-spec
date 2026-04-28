from adapters.ingress.klv.klv_to_zmeta_template import klv_decoded_to_zmeta_observation


def test_klv_ingress_observation():
    decoded = {"lat": 34.0, "lon": -118.0, "alt_m": 120.0, "sensor_mode": "EO"}
    event = klv_decoded_to_zmeta_observation(
        decoded,
        platform_id="platform-1",
        sensor_id="sensor-1",
        producer="klv:misb:0601",
        ts="2025-01-17T15:20:00+00:00",
    )

    assert event["event"]["event_type"] == "OBSERVATION_EVENT"
    assert event["event"]["event_subtype"] == "EO"
    assert event["event"]["ts"] == "2025-01-17T15:20:00Z"
    assert "features" in event["payload"]
    assert event["payload"]["timing_quality"]["sync_state"] == "UNSYNCED"
    assert "confidence" not in event
