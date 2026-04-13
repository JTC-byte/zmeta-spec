"""SignalHunter PSD spectrum analyzer to ZMeta OBSERVATION_EVENT translator.

Translates SignalHunter .bin capture files into ZMeta RF OBSERVATION_EVENTs
using power-gradient analysis to derive synthetic LOBs.

The SignalHunter has no antenna array. Bearing is estimated by comparing
consecutive PSD sweeps taken at different GPS positions: if signal power
increases, the operator is moving toward the emitter and the bearing is
the travel direction. These synthetic LOBs carry large angular error
(~75 deg) but converge through WLS fusion when many observations accumulate.

Input format:
  - Binary .bin capture file with 1060-byte header followed by 822-bin
    float32 PSD frames. GPS is encoded in trailing fill frames.

Source: Z-ISR edge/edge/sensors/signalhunter_rf.py
"""

import math
import struct
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from zmeta_uuid import uuid7

ADAPTER_VERSION = "1.0.0"
SCHEMA_ID = "signalhunter-psd"
DEFAULT_SENSOR_ID = "signalhunter_rf"

FILE_HEADER_SIZE = 1060
BINS_PER_FRAME = 822
FRAME_SIZE_BYTES = BINS_PER_FRAME * 4  # float32


def _utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


# ---------------------------------------------------------------------------
# Binary file parser
# ---------------------------------------------------------------------------


def parse_bin_header(data: bytes) -> dict:
    """Parse the 1060-byte SignalHunter .bin file header.

    Returns:
        Dict with start_freq_mhz, end_freq_mhz, n_frames, lat, lon, location.
    """
    if len(data) < FILE_HEADER_SIZE:
        raise ValueError(f"Header too short: {len(data)} < {FILE_HEADER_SIZE}")
    start_freq = struct.unpack_from("<f", data, 0)[0]
    end_freq = struct.unpack_from("<f", data, 4)[0]
    n_frames = struct.unpack_from("<I", data, 8)[0]
    n_bins = struct.unpack_from("<I", data, 12)[0]
    lat = struct.unpack_from("<f", data, 32)[0]
    lon = struct.unpack_from("<f", data, 36)[0]
    raw_loc = data[40:128]
    location = raw_loc.split(b"\x00")[0].decode("ascii", errors="replace").strip()
    return {
        "start_freq_mhz": start_freq,
        "end_freq_mhz": end_freq,
        "n_frames": n_frames,
        "n_bins": n_bins,
        "lat": lat,
        "lon": lon,
        "location": location,
    }


def _looks_like_gps_frame(values: List[float]) -> bool:
    """Heuristic: detect GPS-fill frames (repeating lat/lon pairs)."""
    if len(values) < 10:
        return False
    v0, v1 = values[0], values[1]
    if not (-90 <= v0 <= 90 and -180 <= v1 <= 180):
        return False
    if abs(v0 - v1) < 1.0:
        return False
    for i in range(0, min(20, len(values)), 2):
        if abs(values[i] - v0) > 0.1 or abs(values[i + 1] - v1) > 0.1:
            return False
    return True


def iter_bin_frames(raw: bytes) -> Tuple[dict, List[Tuple[int, List[float], Optional[dict]]]]:
    """Parse all PSD frames from raw .bin file bytes.

    Returns:
        (header_dict, frames) where each frame is
        (frame_index, psd_dbm_list, gps_dict_or_none).
    """
    header = parse_bin_header(raw)
    frames = []
    for idx in range(header["n_frames"]):
        offset = FILE_HEADER_SIZE + idx * FRAME_SIZE_BYTES
        if offset + FRAME_SIZE_BYTES > len(raw):
            break
        values = list(struct.unpack_from(f"<{BINS_PER_FRAME}f", raw, offset))
        if _looks_like_gps_frame(values):
            frames.append((idx, [], {"lat": values[0], "lon": values[1], "alt_m": 0.0}))
        else:
            frames.append((idx, values, None))
    return header, frames


# ---------------------------------------------------------------------------
# Peak detection
# ---------------------------------------------------------------------------


def detect_peaks(
    psd: List[float],
    freq_start_mhz: float,
    freq_end_mhz: float,
    noise_floor_dbm: float = -95.0,
    min_prominence_db: float = 6.0,
    min_peak_spacing_bins: int = 10,
) -> List[dict]:
    """Find local-maximum peaks in a PSD sweep above the noise floor.

    Returns:
        List of dicts with freq_hz, power_dbm, bin_index.
    """
    if not psd:
        return []
    n = len(psd)
    freq_step_hz = (freq_end_mhz - freq_start_mhz) * 1e6 / max(n - 1, 1)

    peaks = []
    for i in range(1, n - 1):
        val = psd[i]
        if val < noise_floor_dbm:
            continue
        if val <= psd[i - 1] or val <= psd[i + 1]:
            continue
        lo = max(0, i - min_peak_spacing_bins)
        hi = min(n, i + min_peak_spacing_bins + 1)
        local_min = min(psd[lo:hi])
        if val - local_min < min_prominence_db:
            continue
        freq_hz = (freq_start_mhz + i * freq_step_hz / 1e6) * 1e6
        peaks.append({"freq_hz": freq_hz, "power_dbm": val, "bin_index": i})

    if not peaks:
        return []

    peaks.sort(key=lambda p: p["power_dbm"], reverse=True)
    kept = []
    used_bins = set()
    for p in peaks:
        if any(abs(p["bin_index"] - u) < min_peak_spacing_bins for u in used_bins):
            continue
        kept.append(p)
        used_bins.add(p["bin_index"])
    return kept


# ---------------------------------------------------------------------------
# Power-gradient bearing estimation
# ---------------------------------------------------------------------------


def _haversine_bearing(lat1, lon1, lat2, lon2):
    """Initial bearing (degrees, 0=N, 90=E) from point 1 to point 2."""
    lat1_r, lon1_r = math.radians(lat1), math.radians(lon1)
    lat2_r, lon2_r = math.radians(lat2), math.radians(lon2)
    dlon = lon2_r - lon1_r
    x = math.sin(dlon) * math.cos(lat2_r)
    y = math.cos(lat1_r) * math.sin(lat2_r) - math.sin(lat1_r) * math.cos(lat2_r) * math.cos(dlon)
    return math.degrees(math.atan2(x, y)) % 360.0


def _haversine_distance_m(lat1, lon1, lat2, lon2):
    """Great-circle distance in metres."""
    R = 6_371_000.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def compute_gradient_bearing(lat_prev, lon_prev, power_prev, lat_curr, lon_curr, power_curr):
    """Derive a bearing toward the emitter from a power gradient.

    If power increased (closer to emitter), bearing = travel direction.
    If power decreased (moving away), bearing = reverse of travel direction.
    Returns None if power delta < 0.5 dB (too small to be meaningful).
    """
    power_delta = power_curr - power_prev
    if abs(power_delta) < 0.5:
        return None
    travel_bearing = _haversine_bearing(lat_prev, lon_prev, lat_curr, lon_curr)
    if power_delta > 0:
        return travel_bearing
    return (travel_bearing + 180.0) % 360.0


# ---------------------------------------------------------------------------
# Full .bin file translator
# ---------------------------------------------------------------------------


def detect_file(file_bytes: bytes) -> Optional[str]:
    """Inspect raw bytes and return schema_id if it looks like a SignalHunter .bin file."""
    if len(file_bytes) < FILE_HEADER_SIZE:
        return None
    try:
        header = parse_bin_header(file_bytes)
        if header["start_freq_mhz"] > 0 and header["end_freq_mhz"] > header["start_freq_mhz"]:
            return SCHEMA_ID
    except (ValueError, struct.error):
        pass
    return None


def translate_bin_file(
    file_bytes: bytes,
    *,
    platform_id: str,
    sensor_id: Optional[str] = None,
    noise_floor_dbm: float = -95.0,
    min_peak_prominence_db: float = 6.0,
    min_displacement_m: float = 3.0,
    bearing_error_deg: float = 75.0,
    peak_persistence_count: int = 3,
    peak_persistence_window: int = 5,
) -> List[dict]:
    """Translate a complete SignalHunter .bin capture into ZMeta events.

    Processes all PSD frames, detects persistent peaks, and generates
    power-gradient LOBs for each peak where the operator has moved far
    enough to establish a meaningful gradient.

    Args:
        file_bytes: Raw bytes of the .bin file.
        platform_id: Platform identifier string.
        sensor_id: Optional sensor identifier.
        noise_floor_dbm: Noise floor threshold for peak detection.
        min_peak_prominence_db: Minimum prominence for peak selection.
        min_displacement_m: Minimum operator displacement between comparisons.
        bearing_error_deg: Angular error assigned to gradient LOBs (default 75).
        peak_persistence_count: Minimum peak appearances in the window.
        peak_persistence_window: Sliding window size for persistence check.

    Returns:
        List of ZMeta event dicts.
    """
    import time

    header, frames = iter_bin_frames(file_bytes)
    sid = sensor_id or DEFAULT_SENSOR_ID
    events = []

    # Track state for gradient computation: freq_key -> (power_dbm, lat, lon)
    prev_state: Dict[float, Tuple[float, float, float]] = {}
    # Peak persistence: freq_key -> list of booleans
    peak_history: Dict[float, List[bool]] = {}
    current_lat = header["lat"]
    current_lon = header["lon"]

    for frame_idx, psd, gps in frames:
        if gps:
            current_lat = gps["lat"]
            current_lon = gps["lon"]
            continue

        if not psd:
            continue

        peaks = detect_peaks(
            psd,
            header["start_freq_mhz"],
            header["end_freq_mhz"],
            noise_floor_dbm=noise_floor_dbm,
            min_prominence_db=min_peak_prominence_db,
        )

        all_peak_freqs = set()
        for peak in peaks:
            key = round(peak["freq_hz"] / 1000) * 1000
            all_peak_freqs.add(key)
            if key not in peak_history:
                peak_history[key] = []
            peak_history[key].append(True)
            if len(peak_history[key]) > peak_persistence_window:
                peak_history[key] = peak_history[key][-peak_persistence_window:]

        for key in list(peak_history.keys()):
            if key not in all_peak_freqs:
                peak_history[key].append(False)
                if len(peak_history[key]) > peak_persistence_window:
                    peak_history[key] = peak_history[key][-peak_persistence_window:]

        for peak in peaks:
            key = round(peak["freq_hz"] / 1000) * 1000
            history = peak_history.get(key, [])
            if sum(history) < peak_persistence_count:
                continue

            prev = prev_state.get(key)
            if prev is None:
                prev_state[key] = (peak["power_dbm"], current_lat, current_lon)
                continue

            prev_power, p_lat, p_lon = prev
            dist = _haversine_distance_m(p_lat, p_lon, current_lat, current_lon)
            if dist < min_displacement_m:
                continue

            bearing = compute_gradient_bearing(
                p_lat, p_lon, prev_power,
                current_lat, current_lon, peak["power_dbm"],
            )
            prev_state[key] = (peak["power_dbm"], current_lat, current_lon)

            if bearing is None:
                continue

            ts_ms = int(time.time() * 1000)
            ts_iso = datetime.fromtimestamp(
                ts_ms / 1000.0, tz=timezone.utc
            ).isoformat(timespec="milliseconds")

            events.append({
                "zmeta_version": "1.0",
                "event": {
                    "event_id": str(uuid7()),
                    "event_type": "OBSERVATION_EVENT",
                    "event_subtype": "LOB",
                    "ts": ts_iso,
                },
                "source": {
                    "platform_id": platform_id,
                    "node_role": "EDGE",
                    "producer": "signalhunter-adapter",
                    "sensor_id": sid,
                },
                "payload": {
                    "modality": "RF",
                    "geo": {
                        "lat": current_lat,
                        "lon": current_lon,
                        "alt_m": 0.0,
                    },
                    "bearing": {"az_deg": bearing},
                    "features": {
                        "center_freq_hz": peak["freq_hz"],
                        "bandwidth_hz": 0.0,
                        "power_dbm": peak["power_dbm"],
                        "angular_error_deg": bearing_error_deg,
                        "sensor_hw": "signalhunter",
                        "gradient_method": True,
                        "displacement_m": round(dist, 1),
                        "power_delta_db": round(peak["power_dbm"] - prev_power, 2),
                    },
                    "quality": {
                        "measurement_error": bearing_error_deg,
                        "error_metric": "1_SIGMA",
                        "calibration_state": "UNCALIBRATED",
                    },
                },
                "lineage": {
                    "based_on": [str(uuid7())],
                    "transform": f"translate:{SCHEMA_ID}@{ADAPTER_VERSION}",
                },
            })

    return events
