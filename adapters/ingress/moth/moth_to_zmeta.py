"""Heaviside Moth RF sensor to ZMeta OBSERVATION_EVENT translator.

Translates Moth RF readings into ZMeta RF OBSERVATION_EVENTs (LOBs).
The Moth is a compact RF sensor that produces peak frequency and power
readings via serial, MAVLink TUNNEL messages, or custom MAVLink dialect.

Input formats:
  - Serial CSV: freq_mhz, power_dbm
  - Serial JSON: {"peakDbm": -45.2, "peakFreqMhz": 2437.0}
  - MAVLink TUNNEL: 32-byte struct with bearing, freq, power, SNR, etc.
  - MAVLink custom msg (ID 15610): 6-byte struct with freq_mhz + power_dbm
  - JSON replay: {bearing: {az_deg, ...}, frequency: {center_hz, ...}, ...}

The Moth hardware outputs peak signal readings (no antenna array), so
raw serial/custom-message detections are omnidirectional: they have no
bearing, and per the convert-or-omit rule (semantics contract section
6.4) the canonical ``bearing`` block is omitted entirely. True LOBs are
derived later by correlating power with UAS heading during a yaw scan.

Source: Z-ISR edge/edge/sensors/moth_rf.py and edge/edge/zmeta_builder.py
"""

import struct

from adapters.ingress.time_utils import coerce_timing_quality, epoch_ms_to_utc_z, utc_now_z
from zmeta_uuid import uuid7

ADAPTER_VERSION = "1.1.0"
SCHEMA_ID_SERIAL = "moth-serial"
SCHEMA_ID_MAVLINK = "moth-mavlink"
SCHEMA_ID_TUNNEL = "moth-tunnel"
DEFAULT_SENSOR_ID = "moth_rf"

# Binary struct for MAVLink TUNNEL payload:
#   bearing_deg, bearing_err_deg, freq_hz, bw_hz,
#   power_dbm, snr_db, el_deg, confidence
_TUNNEL_STRUCT = struct.Struct("<8f")
_TUNNEL_FIELDS = (
    "bearing_deg", "bearing_err_deg", "freq_hz", "bw_hz",
    "power_dbm", "snr_db", "el_deg", "confidence",
)

# Moth custom MAVLink message (freq_mhz float32 + power_dbm int16)
_MOTH_CUSTOM_STRUCT = struct.Struct("<fh")


def _utc_now():
    return utc_now_z()


def detect(input_bytes):
    """Inspect raw input and return a schema_id if it looks like Moth data.

    Attempts to distinguish:
      - Serial JSON (peakDbm/peakFreqMhz keys)
      - Serial CSV (two comma-separated floats)
      - Binary TUNNEL payload (32 bytes of float32s)
    """
    if len(input_bytes) == _TUNNEL_STRUCT.size:
        return SCHEMA_ID_TUNNEL

    text = input_bytes.decode("utf-8", errors="replace").strip()
    if not text:
        return None

    if text.startswith("{"):
        import json
        try:
            obj = json.loads(text)
            if "peakDbm" in obj or "peak_dbm" in obj or "peakFreqMhz" in obj:
                return SCHEMA_ID_SERIAL
        except (ValueError, TypeError):
            pass
    else:
        parts = text.split(",")
        if len(parts) == 2:
            try:
                float(parts[0])
                float(parts[1])
                return SCHEMA_ID_SERIAL
            except ValueError:
                pass
    return None


def translate_serial_line(line, *, platform_id, sensor_geo=None, sensor_id=None,
                          timestamp_ms=None):
    """Translate a single Moth serial output line into a ZMeta event.

    Supports two formats:
      - JSON: {"peakDbm": -45.2, "peakFreqMhz": 2437.0}
      - CSV:  2437.0,-45.2  (freq_mhz, power_dbm)

    Serial readings are omnidirectional (no bearing information), so the
    canonical ``bearing`` block is omitted and no angular error is claimed.
    Bearing is derived later by correlating with UAS heading during scans.

    Returns:
        ZMeta event dict, or None if unparseable.
    """
    import time

    line = line.strip()
    if not line:
        return None

    peak_dbm = None
    peak_freq_mhz = None

    if line.startswith("{"):
        import json
        try:
            obj = json.loads(line)
            peak_dbm = obj.get("peakDbm", obj.get("peak_dbm"))
            peak_freq_mhz = obj.get("peakFreqMhz", obj.get("peak_freq_mhz"))
        except (ValueError, TypeError):
            return None
    else:
        parts = line.split(",")
        if len(parts) >= 2:
            try:
                peak_freq_mhz = float(parts[0])
                peak_dbm = float(parts[1])
            except (ValueError, IndexError):
                return None

    if peak_dbm is None or peak_freq_mhz is None:
        return None

    ts_ms = timestamp_ms or int(time.time() * 1000)
    ts_iso = epoch_ms_to_utc_z(ts_ms)

    geo = dict(sensor_geo) if sensor_geo else None
    sid = sensor_id or DEFAULT_SENSOR_ID

    event = {
        "zmeta_version": "1.0",
        "event": {
            "event_id": str(uuid7()),
            "event_type": "OBSERVATION_EVENT",
            "event_subtype": "RF",
            "ts": ts_iso,
        },
        "source": {
            "platform_id": platform_id,
            "node_role": "EDGE",
            "producer": "moth-adapter",
            "sensor_id": sid,
        },
        "payload": {
            "modality": "RF",
            "features": {
                "center_freq_hz": peak_freq_mhz * 1e6,
                "bandwidth_hz": 0.0,
                "power_dbm": peak_dbm,
                "sensor_hw": "moth",
                "source_format": "serial",
                "peak_freq_mhz": peak_freq_mhz,
            },
            "quality": {
                "geo_status": "AVAILABLE" if geo else "UNAVAILABLE",
            },
            "timing_quality": coerce_timing_quality(event_ts=ts_iso),
        },
        "lineage": {
            "based_on": [str(uuid7())],
            "transform": f"translate:{SCHEMA_ID_SERIAL}@{ADAPTER_VERSION}",
        },
    }
    if geo:
        event["payload"]["geo"] = geo
    return event


def translate_tunnel_payload(payload_bytes, *, platform_id, sensor_geo=None,
                              sensor_id=None, timestamp_ms=None):
    """Translate a MAVLink TUNNEL payload (32 bytes) into a ZMeta event.

    The TUNNEL message contains a full LOB with bearing, frequency, power,
    SNR, elevation, and confidence from the Moth ICD.

    Returns:
        ZMeta event dict, or None if payload is invalid.
    """
    import time

    if len(payload_bytes) < _TUNNEL_STRUCT.size:
        return None

    values = _TUNNEL_STRUCT.unpack_from(payload_bytes)
    raw = dict(zip(_TUNNEL_FIELDS, values))

    ts_ms = timestamp_ms or int(time.time() * 1000)
    ts_iso = epoch_ms_to_utc_z(ts_ms)

    geo = dict(sensor_geo) if sensor_geo else None
    sid = sensor_id or DEFAULT_SENSOR_ID

    bearing = {"az_deg": raw["bearing_deg"]}
    if raw["el_deg"] != 0:
        bearing["el_deg"] = raw["el_deg"]

    features = {
        "center_freq_hz": raw["freq_hz"],
        "bandwidth_hz": raw["bw_hz"],
        "power_dbm": raw["power_dbm"],
        "angular_error_deg": raw["bearing_err_deg"],
        "sensor_hw": "moth",
        "source_format": "tunnel",
    }

    quality = {
        "measurement_error": {
            "value": raw["bearing_err_deg"],
            "unit": "deg",
            "metric": "1_SIGMA",
        },
        "calibration_state": "CALIBRATED",
    }
    if raw["snr_db"] != 0:
        features["snr_db"] = raw["snr_db"]
        quality["snr_db"] = raw["snr_db"]

    event = {
        "zmeta_version": "1.0",
        "event": {
            "event_id": str(uuid7()),
            "event_type": "OBSERVATION_EVENT",
            "event_subtype": "RF",
            "ts": ts_iso,
        },
        "source": {
            "platform_id": platform_id,
            "node_role": "EDGE",
            "producer": "moth-adapter",
            "sensor_id": sid,
        },
        "payload": {
            "modality": "RF",
            "bearing": bearing,
            "features": features,
            "quality": quality,
            "timing_quality": coerce_timing_quality(event_ts=ts_iso),
        },
        "lineage": {
            "based_on": [str(uuid7())],
            "transform": f"translate:{SCHEMA_ID_TUNNEL}@{ADAPTER_VERSION}",
        },
    }
    if geo:
        event["payload"]["geo"] = geo
        quality["geo_status"] = "AVAILABLE"
    else:
        quality["geo_status"] = "UNAVAILABLE"

    if raw["confidence"] > 0:
        quality["sensor_confidence"] = min(1.0, raw["confidence"])

    return event


def translate_custom_mavlink(frame_bytes, *, platform_id, sensor_geo=None,
                              sensor_id=None, timestamp_ms=None):
    """Translate a Moth custom MAVLink message (UNKNOWN_15610) into ZMeta.

    The Moth firmware sends freq_mhz (float32) + power_dbm (int16) as a
    6-byte payload. Without the dialect XML, pymavlink reports these as
    UNKNOWN_NNNNN with raw frame data. These readings are omnidirectional
    (no bearing information), so the canonical ``bearing`` block is omitted.

    Args:
        frame_bytes: Full MAVLink v2 frame bytes (10-byte header + payload + CRC).

    Returns:
        ZMeta event dict, or None if frame is invalid.
    """
    import time

    if len(frame_bytes) < 12:
        return None
    payload_len = frame_bytes[1]
    if payload_len != _MOTH_CUSTOM_STRUCT.size:
        return None
    payload = frame_bytes[10:10 + payload_len]
    if len(payload) != _MOTH_CUSTOM_STRUCT.size:
        return None

    freq_mhz, power_dbm = _MOTH_CUSTOM_STRUCT.unpack(payload)
    if freq_mhz <= 0 or freq_mhz > 10000 or power_dbm > 10 or power_dbm < -200:
        return None

    ts_ms = timestamp_ms or int(time.time() * 1000)
    ts_iso = epoch_ms_to_utc_z(ts_ms)

    geo = dict(sensor_geo) if sensor_geo else None
    sid = sensor_id or DEFAULT_SENSOR_ID

    event = {
        "zmeta_version": "1.0",
        "event": {
            "event_id": str(uuid7()),
            "event_type": "OBSERVATION_EVENT",
            "event_subtype": "RF",
            "ts": ts_iso,
        },
        "source": {
            "platform_id": platform_id,
            "node_role": "EDGE",
            "producer": "moth-adapter",
            "sensor_id": sid,
        },
        "payload": {
            "modality": "RF",
            "features": {
                "center_freq_hz": freq_mhz * 1e6,
                "bandwidth_hz": 0.0,
                "power_dbm": float(power_dbm),
                "sensor_hw": "moth",
                "source_format": "mavlink_custom",
                "peak_freq_mhz": freq_mhz,
            },
            "quality": {
                "geo_status": "AVAILABLE" if geo else "UNAVAILABLE",
            },
            "timing_quality": coerce_timing_quality(event_ts=ts_iso),
        },
        "lineage": {
            "based_on": [str(uuid7())],
            "transform": f"translate:{SCHEMA_ID_MAVLINK}@{ADAPTER_VERSION}",
        },
    }
    if geo:
        event["payload"]["geo"] = geo
    return event


def translate_json_replay(raw, *, platform_id, sensor_geo=None, sensor_id=None):
    """Translate a Moth JSON replay dict into a ZMeta event.

    Used for offline replay / bench testing. Accepts the structured dict
    format with bearing, frequency, power sub-objects. The input bearing,
    when present, is passed through as measured. When the input carries no
    bearing.az_deg the reading is omnidirectional and the canonical
    ``bearing`` block (and any angular error) is omitted.

    Args:
        raw: Dict with keys like bearing.az_deg, frequency.center_hz,
            power.rssi_dbm, etc.

    Returns:
        ZMeta event dict.
    """
    import time

    bearing_obj = raw.get("bearing", {})
    freq_obj = raw.get("frequency", {})
    power_obj = raw.get("power", {})
    sensor_pos = raw.get("sensor_position", {})
    ts_ms = raw.get("timestamp_ms", int(time.time() * 1000))

    ts_iso = epoch_ms_to_utc_z(ts_ms)

    geo = sensor_geo or (
        {"lat": sensor_pos["lat"], "lon": sensor_pos["lon"],
         "alt_m": sensor_pos.get("alt_m", 0.0)}
        if sensor_pos.get("lat") is not None
        else None
    )

    sid = sensor_id or DEFAULT_SENSOR_ID

    bearing = None
    if bearing_obj.get("az_deg") is not None:
        bearing = {"az_deg": bearing_obj["az_deg"]}
        if bearing_obj.get("el_deg") is not None:
            bearing["el_deg"] = bearing_obj["el_deg"]

    features = {
        "center_freq_hz": freq_obj.get("center_hz", 0.0),
        "bandwidth_hz": freq_obj.get("bandwidth_hz", 0.0),
        "power_dbm": power_obj.get("rssi_dbm", -100.0),
        "sensor_hw": "moth",
        "source_format": "json_replay",
    }

    quality = {
        "calibration_state": "CALIBRATED",
    }
    if bearing is not None:
        err = raw.get("bearing_error_deg", 10.0)
        features["angular_error_deg"] = err
        quality["measurement_error"] = {
            "value": err,
            "unit": "deg",
            "metric": "1_SIGMA",
        }
    if power_obj.get("snr_db") is not None:
        features["snr_db"] = power_obj["snr_db"]
        quality["snr_db"] = power_obj["snr_db"]

    classification = raw.get("classification")
    if classification:
        quality["source_classification"] = classification

    event = {
        "zmeta_version": "1.0",
        "event": {
            "event_id": str(uuid7()),
            "event_type": "OBSERVATION_EVENT",
            "event_subtype": "RF",
            "ts": ts_iso,
        },
        "source": {
            "platform_id": platform_id,
            "node_role": "EDGE",
            "producer": "moth-adapter",
            "sensor_id": sid,
        },
        "payload": {
            "modality": "RF",
            "features": features,
            "quality": quality,
            "timing_quality": coerce_timing_quality(raw.get("timing_quality"), event_ts=ts_iso),
        },
        "lineage": {
            "based_on": [str(uuid7())],
            "transform": f"translate:{SCHEMA_ID_SERIAL}@{ADAPTER_VERSION}",
        },
    }
    if bearing is not None:
        event["payload"]["bearing"] = bearing
    if geo:
        event["payload"]["geo"] = geo
        quality["geo_status"] = "AVAILABLE"
    else:
        quality["geo_status"] = "UNAVAILABLE"

    if bearing_obj.get("confidence") is not None:
        quality["sensor_confidence"] = bearing_obj["confidence"]

    return event
