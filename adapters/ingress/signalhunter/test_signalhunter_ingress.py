import json
import struct
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from adapters.ingress.signalhunter.signalhunter_to_zmeta import (
    BINS_PER_FRAME,
    FILE_HEADER_SIZE,
    compute_gradient_bearing,
    iter_bin_frames,
    translate_bin_file,
)


ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = ROOT / "schema" / "zmeta-event-1.0.schema.json"
SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
VALIDATOR = Draft202012Validator(SCHEMA, format_checker=FormatChecker())

START_LAT = 34.0
START_LON = -118.0
# ~111 m due north of the start position (> min_displacement_m default of 3).
MOVED_LAT = 34.001
MOVED_LON = -118.0


def _header(n_frames, lat=START_LAT, lon=START_LON):
    header = bytearray(FILE_HEADER_SIZE)
    struct.pack_into("<f", header, 0, 2400.0)   # start_freq_mhz
    struct.pack_into("<f", header, 4, 2500.0)   # end_freq_mhz
    struct.pack_into("<I", header, 8, n_frames)
    struct.pack_into("<I", header, 12, BINS_PER_FRAME)
    struct.pack_into("<f", header, 32, lat)
    struct.pack_into("<f", header, 36, lon)
    header[40:44] = b"test"
    return bytes(header)


def _psd_frame(peak_dbm, peak_bin=400, baseline_dbm=-100.0):
    values = [baseline_dbm] * BINS_PER_FRAME
    values[peak_bin] = peak_dbm
    return struct.pack(f"<{BINS_PER_FRAME}f", *values)


def _gps_frame(lat, lon):
    values = [lat, lon] * (BINS_PER_FRAME // 2)
    return struct.pack(f"<{BINS_PER_FRAME}f", *values)


def _capture_with_gradient_lob():
    """Build a capture whose persistent peak strengthens after a GPS move north."""
    frames = [
        _psd_frame(-50.0),  # persistence 1
        _psd_frame(-50.0),  # persistence 2
        _psd_frame(-50.0),  # persistence 3 -> establishes gradient state
        _gps_frame(MOVED_LAT, MOVED_LON),
        _psd_frame(-45.0),  # +5 dB after moving north -> LOB toward travel dir
    ]
    return _header(len(frames)) + b"".join(frames)


def test_gradient_bearing_is_travel_direction_when_power_increases():
    bearing = compute_gradient_bearing(
        START_LAT, START_LON, -50.0, MOVED_LAT, MOVED_LON, -45.0
    )
    assert bearing == pytest.approx(0.0, abs=0.01)


def test_gradient_lob_asserts_true_north_frame_provenance():
    events = translate_bin_file(_capture_with_gradient_lob(), platform_id="foot-patrol-01")

    assert len(events) == 1
    payload = events[0]["payload"]
    # Geodesic travel direction over GPS positions is true north by construction.
    assert payload["bearing"]["az_deg"] == pytest.approx(0.0, abs=0.1)
    assert payload["quality"]["bearing_frame"] == "TRUE_NORTH"
    assert payload["quality"]["heading_source"] == "GPS_COURSE"
    assert payload["features"]["angular_error_deg"] == pytest.approx(75.0)


def test_no_event_without_meaningful_power_delta():
    frames = [
        _psd_frame(-50.0),
        _psd_frame(-50.0),
        _psd_frame(-50.0),
        _gps_frame(MOVED_LAT, MOVED_LON),
        _psd_frame(-50.2),  # |delta| < 0.5 dB -> discarded as noise
    ]
    raw = _header(len(frames)) + b"".join(frames)

    assert translate_bin_file(raw, platform_id="foot-patrol-01") == []


def test_events_validate_against_v1_0_schema():
    for event in translate_bin_file(_capture_with_gradient_lob(), platform_id="foot-patrol-01"):
        VALIDATOR.validate(event)


# --- GPS no-lock sentinel (R1-11 R11-06) ------------------------------------
# A no-lock header reports (0, 0). Consuming it as a position produced a
# null-island geodesic asserted as a TRUE_NORTH/GPS_COURSE bearing that
# passed strict-H clean; the sentinel must never seed the gradient tracker
# (contract 6.8: the (0,0,0) sentinel is not evidence of position).


def test_no_lock_header_never_yields_null_island_bearing():
    frames = [
        _psd_frame(-70.0),
        _psd_frame(-70.0),
        _psd_frame(-70.0),
        _gps_frame(34.05, -118.24),  # first real fix, mid-file
        _psd_frame(-65.0),           # stronger peak at the real fix
    ]
    raw = _header(len(frames), lat=0.0, lon=0.0) + b"".join(frames)

    # Pre-fix this produced az ~307 deg with displacement_m ~12,574 km.
    assert translate_bin_file(raw, platform_id="foot-patrol-01") == []


def test_first_bearing_after_no_lock_uses_only_real_fixes():
    frames = [
        _psd_frame(-50.0),
        _psd_frame(-50.0),
        _psd_frame(-50.0),
        _gps_frame(START_LAT, START_LON),  # first real fix seeds here
        _psd_frame(-50.0),
        _gps_frame(MOVED_LAT, MOVED_LON),  # ~111 m due north
        _psd_frame(-45.0),
    ]
    raw = _header(len(frames), lat=0.0, lon=0.0) + b"".join(frames)

    events = translate_bin_file(raw, platform_id="foot-patrol-01")
    assert len(events) == 1
    payload = events[0]["payload"]
    assert payload["bearing"]["az_deg"] == pytest.approx(0.0, abs=0.1)
    assert payload["features"]["displacement_m"] == pytest.approx(111.2, abs=1.0)
    position = payload["quality"]["sensor_position_2d"]
    assert position["lat"] == pytest.approx(MOVED_LAT, abs=1e-4)
    assert position["lon"] == pytest.approx(MOVED_LON, abs=1e-4)


def test_gps_frames_carry_no_fabricated_altitude():
    frames = [_gps_frame(START_LAT, START_LON)]
    raw = _header(len(frames)) + b"".join(frames)
    _header_dict, parsed = iter_bin_frames(raw)
    gps = parsed[0][2]
    assert set(gps.keys()) == {"lat", "lon"}
