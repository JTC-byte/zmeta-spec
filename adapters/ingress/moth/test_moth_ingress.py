import json
import struct
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from adapters.ingress.moth.moth_to_zmeta import (
    translate_custom_mavlink,
    translate_json_replay,
    translate_serial_line,
    translate_tunnel_payload,
)


ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = ROOT / "schema" / "zmeta-event-1.0.schema.json"
SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
VALIDATOR = Draft202012Validator(SCHEMA, format_checker=FormatChecker())

TS_MS = 1737127200123
GEO = {"lat": 34.0, "lon": -118.0, "alt_m": 120.0}

# bearing_deg, bearing_err_deg, freq_hz, bw_hz, power_dbm, snr_db, el_deg, confidence
TUNNEL_BYTES = struct.pack(
    "<8f", 123.4, 5.0, 2437000000.0, 1000000.0, -45.2, 12.0, 2.0, 0.9
)

# MAVLink v2 frame: 10-byte header (byte 1 = payload length), 6-byte payload, 2-byte CRC
_CUSTOM_PAYLOAD = struct.pack("<fh", 2437.0, -45)
CUSTOM_FRAME = bytes([0xFD, len(_CUSTOM_PAYLOAD), 0, 0, 0, 1, 1, 0xFA, 0x3C, 0x00]) + _CUSTOM_PAYLOAD + b"\x00\x00"

REPLAY_WITH_BEARING = {
    "timestamp_ms": TS_MS,
    "bearing": {"az_deg": 123.4, "el_deg": 2.0},
    "frequency": {"center_hz": 2437000000.0, "bandwidth_hz": 1000000.0},
    "power": {"rssi_dbm": -45.2},
    "bearing_error_deg": 7.5,
}

REPLAY_WITHOUT_BEARING = {
    "timestamp_ms": TS_MS,
    "frequency": {"center_hz": 2437000000.0},
    "power": {"rssi_dbm": -45.2},
}


def _serial_event(line="2437.0,-45.2", **kwargs):
    kwargs.setdefault("timestamp_ms", TS_MS)
    return translate_serial_line(line, platform_id="uav-01", **kwargs)


def test_serial_csv_omits_fabricated_bearing():
    event = _serial_event()

    assert "bearing" not in event["payload"]
    assert "angular_error_deg" not in event["payload"]["features"]


def test_serial_json_omits_fabricated_bearing():
    event = _serial_event('{"peakDbm": -45.2, "peakFreqMhz": 2437.0}')

    assert "bearing" not in event["payload"]
    assert "angular_error_deg" not in event["payload"]["features"]


def test_serial_features_and_geo_intact():
    event = _serial_event(sensor_geo=GEO)

    features = event["payload"]["features"]
    assert features["center_freq_hz"] == pytest.approx(2437000000.0)
    assert features["power_dbm"] == pytest.approx(-45.2)
    assert features["peak_freq_mhz"] == pytest.approx(2437.0)
    assert features["sensor_hw"] == "moth"
    assert features["source_format"] == "serial"
    assert event["payload"]["geo"] == GEO
    assert event["payload"]["quality"]["geo_status"] == "AVAILABLE"


def test_serial_without_geo_marks_unavailable():
    event = _serial_event()

    assert "geo" not in event["payload"]
    assert event["payload"]["quality"]["geo_status"] == "UNAVAILABLE"


def test_custom_mavlink_omits_fabricated_bearing():
    event = translate_custom_mavlink(
        CUSTOM_FRAME, platform_id="uav-01", timestamp_ms=TS_MS
    )

    assert "bearing" not in event["payload"]
    assert "angular_error_deg" not in event["payload"]["features"]
    assert event["payload"]["features"]["center_freq_hz"] == pytest.approx(2437000000.0)
    assert event["payload"]["features"]["power_dbm"] == pytest.approx(-45.0)


def test_tunnel_unknown_frame_omits_canonical_bearing_and_preserves_raw():
    event = translate_tunnel_payload(
        TUNNEL_BYTES, platform_id="uav-01", timestamp_ms=TS_MS
    )

    features = event["payload"]["features"]
    assert "bearing" not in event["payload"]
    assert "angular_error_deg" not in features
    assert "measurement_error" not in event["payload"]["quality"]
    assert features["bearing_frame_unknown_deg"] == pytest.approx(123.4)
    assert features["bearing_frame_unknown_el_deg"] == pytest.approx(2.0)
    assert features["bearing_frame_unknown_error_deg"] == pytest.approx(5.0)


def test_json_replay_unknown_frame_omits_canonical_bearing_and_preserves_raw():
    event = translate_json_replay(dict(REPLAY_WITH_BEARING), platform_id="uav-01")

    features = event["payload"]["features"]
    assert "bearing" not in event["payload"]
    assert "angular_error_deg" not in features
    assert "measurement_error" not in event["payload"]["quality"]
    assert features["bearing_frame_unknown_deg"] == pytest.approx(123.4)
    assert features["bearing_frame_unknown_el_deg"] == pytest.approx(2.0)
    assert features["bearing_frame_unknown_error_deg"] == pytest.approx(7.5)


def test_tunnel_bearing_carries_no_frame_assertion():
    # The Moth tunnel ICD does not declare a reference frame for bearing_deg,
    # so the adapter must not fabricate quality.bearing_frame/heading_source
    # provenance (semantics contract section 6.4 convert-or-omit).
    event = translate_tunnel_payload(
        TUNNEL_BYTES, platform_id="uav-01", timestamp_ms=TS_MS
    )

    assert "bearing_frame" not in event["payload"]["quality"]
    assert "heading_source" not in event["payload"]["quality"]


def test_json_replay_bearing_carries_no_frame_assertion():
    event = translate_json_replay(dict(REPLAY_WITH_BEARING), platform_id="uav-01")

    assert "bearing_frame" not in event["payload"]["quality"]
    assert "heading_source" not in event["payload"]["quality"]


def test_tunnel_true_north_frame_emits_canonical_bearing():
    event = translate_tunnel_payload(
        TUNNEL_BYTES,
        platform_id="uav-01",
        timestamp_ms=TS_MS,
        bearing_frame="TRUE_NORTH",
    )

    assert event["payload"]["bearing"]["az_deg"] == pytest.approx(123.4)
    assert event["payload"]["bearing"]["el_deg"] == pytest.approx(2.0)
    assert event["payload"]["features"]["angular_error_deg"] == pytest.approx(5.0)
    assert event["payload"]["quality"]["measurement_error"]["value"] == pytest.approx(5.0)
    assert event["payload"]["quality"]["bearing_frame"] == "TRUE_NORTH"
    assert "bearing_frame_unknown_deg" not in event["payload"]["features"]


def test_json_replay_true_north_frame_emits_canonical_bearing():
    event = translate_json_replay(
        dict(REPLAY_WITH_BEARING),
        platform_id="uav-01",
        bearing_frame="TRUE_NORTH",
    )

    assert event["payload"]["bearing"]["az_deg"] == pytest.approx(123.4)
    assert event["payload"]["bearing"]["el_deg"] == pytest.approx(2.0)
    assert event["payload"]["features"]["angular_error_deg"] == pytest.approx(7.5)
    assert event["payload"]["quality"]["measurement_error"]["value"] == pytest.approx(7.5)
    assert event["payload"]["quality"]["bearing_frame"] == "TRUE_NORTH"
    assert "bearing_frame_unknown_deg" not in event["payload"]["features"]


def test_moth_invalid_bearing_frame_rejected():
    with pytest.raises(ValueError, match="bearing_frame"):
        translate_tunnel_payload(
            TUNNEL_BYTES,
            platform_id="uav-01",
            timestamp_ms=TS_MS,
            bearing_frame="MAGNETIC_NORTH",
        )


def test_json_replay_without_bearing_omits_bearing_and_error():
    event = translate_json_replay(dict(REPLAY_WITHOUT_BEARING), platform_id="uav-01")

    assert "bearing" not in event["payload"]
    assert "angular_error_deg" not in event["payload"]["features"]
    assert "measurement_error" not in event["payload"]["quality"]
    assert event["payload"]["features"]["center_freq_hz"] == pytest.approx(2437000000.0)
    assert event["payload"]["features"]["power_dbm"] == pytest.approx(-45.2)


def test_events_validate_against_v1_0_schema():
    for event in (
        _serial_event(sensor_geo=GEO),
        _serial_event('{"peakDbm": -45.2, "peakFreqMhz": 2437.0}'),
        translate_custom_mavlink(CUSTOM_FRAME, platform_id="uav-01", timestamp_ms=TS_MS),
        translate_tunnel_payload(TUNNEL_BYTES, platform_id="uav-01", timestamp_ms=TS_MS),
        translate_tunnel_payload(
            TUNNEL_BYTES,
            platform_id="uav-01",
            timestamp_ms=TS_MS,
            bearing_frame="TRUE_NORTH",
        ),
        translate_json_replay(dict(REPLAY_WITH_BEARING), platform_id="uav-01"),
        translate_json_replay(
            dict(REPLAY_WITH_BEARING),
            platform_id="uav-01",
            bearing_frame="TRUE_NORTH",
        ),
        translate_json_replay(dict(REPLAY_WITHOUT_BEARING), platform_id="uav-01"),
    ):
        VALIDATOR.validate(event)
