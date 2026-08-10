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

import math
import struct

from adapters.ingress.time_utils import coerce_timing_quality, epoch_ms_to_utc_z, utc_now_z
from zmeta_uuid import uuid7

ADAPTER_VERSION = "1.3.0"
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


def _assert_true_north_bearing_frame(bearing_frame):
    if bearing_frame is None:
        return None
    if bearing_frame != "TRUE_NORTH":
        raise ValueError("bearing_frame must be TRUE_NORTH when provided")
    return bearing_frame


def _record_unknown_frame_bearing(features, *, az_deg, error_deg=None, el_deg=None):
    features["bearing_frame_unknown_deg"] = az_deg
    if error_deg is not None:
        features["bearing_frame_unknown_error_deg"] = error_deg
    if el_deg not in (None, 0):
        features["bearing_frame_unknown_el_deg"] = el_deg


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


def _resolve_sensor_geo(position):
    """Apply the altitude-datum boundary (contract 6.2, doctrine C1-01) to a
    caller-supplied sensor position dict.

    Only a vertical declared WGS-84 HAE (``alt_hae_m``) may occupy canonical
    ``geo.alt_m``. The legacy ``alt_m`` key asserts no datum -- in this
    adapter's documented Z-ISR UAS origin the natural position source is
    autopilot telemetry, whose MAVLink global-position altitude is MSL -- so
    it never reaches ``alt_m``: the position degrades to the declared 2-D
    form (doctrine A1-02) with the value preserved non-canonically. This is
    the discipline the bearing axis already gets via the TRUE_NORTH gate: a
    frame or datum claim is asserted only on explicit evidence. A position
    with no vertical of any kind stays omitted (absence is refused, not
    degraded).

    Returns ``(geo_or_None, preserved_alt_or_None, needs_1_1_0)``.
    """
    if not position:
        return None, None, False
    lat = position.get("lat")
    lon = position.get("lon")
    if lat is None or lon is None:
        return None, None, False
    alt_hae_m = position.get("alt_hae_m")
    if alt_hae_m is not None:
        return {"lat": lat, "lon": lon, "alt_m": alt_hae_m}, None, False
    alt_unspecified_m = position.get("alt_m")
    if alt_unspecified_m is not None:
        return {"lat": lat, "lon": lon, "dimensionality": "2D"}, alt_unspecified_m, True
    return None, None, False


def _apply_sensor_geo(event, geo, preserved_alt_m, needs_1_1_0):
    """Attach the resolved position, its status, and the version stamp.

    The declared 2-D branch stamps 1.1.0 (``dimensionality`` is v1.1.0
    vocabulary; the locked v1.0 geo def is additionalProperties:false over
    lat/lon/alt_m) and cannot sit beside ``geo_status: AVAILABLE`` (A1-02
    coherence arm 2), so the status says VERTICAL_UNAVAILABLE and the
    undeclared-datum vertical rides along as
    ``quality.moth_sensor_alt_unspecified_datum_m``.
    """
    quality = event["payload"].setdefault("quality", {})
    if geo:
        event["payload"]["geo"] = geo
        if needs_1_1_0:
            event["zmeta_version"] = "1.1.0"
            quality["geo_status"] = "VERTICAL_UNAVAILABLE"
            quality["moth_sensor_alt_unspecified_datum_m"] = preserved_alt_m
        else:
            quality["geo_status"] = "AVAILABLE"
    else:
        quality["geo_status"] = "UNAVAILABLE"


def translate_serial_line(line, *, platform_id, sensor_geo=None, sensor_id=None,
                          timestamp_ms=None, based_on=None):
    """Translate a single Moth serial output line into a ZMeta event.

    Supports two formats:
      - JSON: {"peakDbm": -45.2, "peakFreqMhz": 2437.0}
      - CSV:  2437.0,-45.2  (freq_mhz, power_dbm)

    Serial readings are omnidirectional (no bearing information), so the
    canonical ``bearing`` block is omitted and no angular error is claimed.
    Bearing is derived later by correlating with UAS heading during scans.

    ``based_on`` may carry real parent ZMeta event ids (UUIDv7 strings); when
    None (default), lineage is omitted because this reading is an original
    observation with no ZMeta parent. Parent ids are never fabricated.

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
    # A NaN/inf reading is not a measurement. The CSV branch's own float()
    # calls accept "nan"/"inf" as valid syntax, and a JSON payload can carry a
    # literal NaN, so neither branch's success alone means the value is real.
    for value in (peak_dbm, peak_freq_mhz):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None
        if not math.isfinite(value):
            return None

    ts_ms = timestamp_ms or int(time.time() * 1000)
    ts_iso = epoch_ms_to_utc_z(ts_ms)

    geo, preserved_alt_m, needs_1_1_0 = _resolve_sensor_geo(sensor_geo)
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
                # 0.0 is the documented sentinel: the Moth reports no
                # emitter bandwidth (see README, "Bandwidth sentinel").
                "bandwidth_hz": 0.0,
                "power_dbm": peak_dbm,
                "sensor_hw": "moth",
                "source_format": "serial",
                "peak_freq_mhz": peak_freq_mhz,
            },
            "quality": {},
            "timing_quality": coerce_timing_quality(event_ts=ts_iso),
        },
    }
    if based_on:
        event["lineage"] = {
            "based_on": [str(item) for item in based_on],
            "transform": f"translate:{SCHEMA_ID_SERIAL}@{ADAPTER_VERSION}",
        }
    _apply_sensor_geo(event, geo, preserved_alt_m, needs_1_1_0)
    return event


def translate_tunnel_payload(payload_bytes, *, platform_id, sensor_geo=None,
                              sensor_id=None, timestamp_ms=None,
                              bearing_frame=None, calibration_state="UNCALIBRATED",
                              based_on=None):
    """Translate a MAVLink TUNNEL payload (32 bytes) into a ZMeta event.

    The TUNNEL message contains a full LOB with bearing, frequency, power,
    SNR, elevation, and confidence from the Moth ICD.

    The ICD field is named ``bearing_deg`` but does not state a reference
    frame. By default the raw value is preserved only in explicitly named
    ``features.bearing_frame_unknown_*`` fields and no canonical ``bearing``
    block is emitted. Pass ``bearing_frame="TRUE_NORTH"`` only when deployment
    configuration or upstream ICD evidence guarantees degrees true north.

    Returns:
        ZMeta event dict, or None if payload is invalid.
    """
    import time

    if len(payload_bytes) < _TUNNEL_STRUCT.size:
        return None

    bearing_frame = _assert_true_north_bearing_frame(bearing_frame)
    values = _TUNNEL_STRUCT.unpack_from(payload_bytes)
    raw = dict(zip(_TUNNEL_FIELDS, values))

    ts_ms = timestamp_ms or int(time.time() * 1000)
    ts_iso = epoch_ms_to_utc_z(ts_ms)

    geo, preserved_alt_m, needs_1_1_0 = _resolve_sensor_geo(sensor_geo)
    sid = sensor_id or DEFAULT_SENSOR_ID

    features = {
        "center_freq_hz": raw["freq_hz"],
        "bandwidth_hz": raw["bw_hz"],
        "power_dbm": raw["power_dbm"],
        "sensor_hw": "moth",
        "source_format": "tunnel",
    }

    quality = {
        "calibration_state": calibration_state,
    }
    bearing = None
    if bearing_frame == "TRUE_NORTH":
        bearing = {"az_deg": raw["bearing_deg"]}
        if raw["el_deg"] != 0:
            bearing["el_deg"] = raw["el_deg"]
        features["angular_error_deg"] = raw["bearing_err_deg"]
        quality["measurement_error"] = {
            "value": raw["bearing_err_deg"],
            "unit": "deg",
            "metric": "1_SIGMA",
        }
        quality["bearing_frame"] = "TRUE_NORTH"
    else:
        _record_unknown_frame_bearing(
            features,
            az_deg=raw["bearing_deg"],
            error_deg=raw["bearing_err_deg"],
            el_deg=raw["el_deg"],
        )
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
            "features": features,
            "quality": quality,
            "timing_quality": coerce_timing_quality(event_ts=ts_iso),
        },
    }
    if based_on:
        event["lineage"] = {
            "based_on": [str(item) for item in based_on],
            "transform": f"translate:{SCHEMA_ID_TUNNEL}@{ADAPTER_VERSION}",
        }
    _apply_sensor_geo(event, geo, preserved_alt_m, needs_1_1_0)

    if bearing is not None:
        event["payload"]["bearing"] = bearing

    if raw["confidence"] > 0:
        quality["sensor_confidence"] = min(1.0, raw["confidence"])

    return event


def translate_custom_mavlink(frame_bytes, *, platform_id, sensor_geo=None,
                              sensor_id=None, timestamp_ms=None, based_on=None):
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
    # freq_mhz is wire-encoded as float32 and can carry a NaN bit pattern; NaN
    # fails every comparison below (`<= 0`, `> 10000`), so isfinite must run
    # first or a corrupted reading passes the sanity bounds unchallenged.
    if not math.isfinite(freq_mhz):
        return None
    if freq_mhz <= 0 or freq_mhz > 10000 or power_dbm > 10 or power_dbm < -200:
        return None

    ts_ms = timestamp_ms or int(time.time() * 1000)
    ts_iso = epoch_ms_to_utc_z(ts_ms)

    geo, preserved_alt_m, needs_1_1_0 = _resolve_sensor_geo(sensor_geo)
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
                # 0.0 is the documented sentinel: the Moth reports no
                # emitter bandwidth (see README, "Bandwidth sentinel").
                "bandwidth_hz": 0.0,
                "power_dbm": float(power_dbm),
                "sensor_hw": "moth",
                "source_format": "mavlink_custom",
                "peak_freq_mhz": freq_mhz,
            },
            "quality": {},
            "timing_quality": coerce_timing_quality(event_ts=ts_iso),
        },
    }
    if based_on:
        event["lineage"] = {
            "based_on": [str(item) for item in based_on],
            "transform": f"translate:{SCHEMA_ID_MAVLINK}@{ADAPTER_VERSION}",
        }
    _apply_sensor_geo(event, geo, preserved_alt_m, needs_1_1_0)
    return event


def translate_json_replay(raw, *, platform_id, sensor_geo=None, sensor_id=None,
                          bearing_frame=None, calibration_state="UNCALIBRATED",
                          based_on=None):
    """Translate a Moth JSON replay dict into a ZMeta event.

    Used for offline replay / bench testing. Accepts the structured dict
    format with bearing, frequency, power sub-objects. The replay format does
    not guarantee a reference frame. By default input bearings are preserved
    only under explicitly named ``features.bearing_frame_unknown_*`` fields.
    Pass ``bearing_frame="TRUE_NORTH"`` only when the replay source is known
    to carry degrees true north; otherwise the canonical ``bearing`` block is
    omitted.

    Schema-required RF measurements are never fabricated: a replay record
    missing ``frequency.center_hz`` or ``power.rssi_dbm`` is refused.
    ``frequency.bandwidth_hz`` alone may be absent -- it defaults to the
    documented 0.0 "no emitter bandwidth measured" sentinel (see README).
    In TRUE_NORTH mode a missing ``bearing_error_deg`` omits
    ``features.angular_error_deg`` and ``quality.measurement_error``
    entirely (both are schema-optional; an error bound is never invented).

    Canonical ``geo`` is all-or-nothing (contract 6.8) and datum-gated
    (contract 6.2): ``sensor_position`` yields a full 3-D ``payload.geo``
    only when ``lat``, ``lon``, and a declared-HAE ``alt_hae_m`` are all
    present. The replay format never declares an altitude datum, so a
    legacy ``alt_m`` vertical degrades the position to the declared 2-D
    form (``dimensionality: "2D"``, 1.1.0 stamp) with the value preserved
    as ``quality.moth_sensor_alt_unspecified_datum_m``; no vertical of any
    kind omits ``geo`` entirely with ``quality.geo_status: UNAVAILABLE``.
    Missing values are never zero-filled.

    Args:
        raw: Dict with keys like bearing.az_deg, frequency.center_hz,
            power.rssi_dbm, etc.

    Returns:
        ZMeta event dict, or None if a schema-required RF measurement
        (frequency.center_hz or power.rssi_dbm) is missing.
    """
    import time

    bearing_frame = _assert_true_north_bearing_frame(bearing_frame)
    bearing_obj = raw.get("bearing", {})
    freq_obj = raw.get("frequency", {})
    power_obj = raw.get("power", {})
    sensor_pos = raw.get("sensor_position", {})

    center_freq_hz = freq_obj.get("center_hz")
    power_dbm = power_obj.get("rssi_dbm")
    if center_freq_hz is None or power_dbm is None:
        return None

    ts_ms = raw.get("timestamp_ms", int(time.time() * 1000))

    ts_iso = epoch_ms_to_utc_z(ts_ms)

    # Canonical geo is all-or-nothing (contract 6.8) and datum-gated
    # (contract 6.2, doctrine C1-01): the caller's sensor_geo takes
    # precedence over the replay record's sensor_position, and both go
    # through the same boundary -- only a declared-HAE alt_hae_m becomes
    # canonical alt_m, a legacy alt_m degrades to the declared 2-D form
    # with the value preserved, no vertical of any kind omits geo. The
    # replay format never declares an altitude datum, so its sensor_position
    # gets the same treatment the format's bearing already gets from the
    # bearing_frame gate: no evidence, no claim.
    geo, preserved_alt_m, needs_1_1_0 = _resolve_sensor_geo(
        sensor_geo if sensor_geo else sensor_pos
    )

    sid = sensor_id or DEFAULT_SENSOR_ID

    features = {
        "center_freq_hz": center_freq_hz,
        # 0.0 is the documented sentinel: the Moth reports no emitter
        # bandwidth (see README, "Bandwidth sentinel").
        "bandwidth_hz": freq_obj.get("bandwidth_hz", 0.0),
        "power_dbm": power_dbm,
        "sensor_hw": "moth",
        "source_format": "json_replay",
    }

    quality = {
        "calibration_state": calibration_state,
    }
    bearing = None
    if bearing_obj.get("az_deg") is not None and bearing_frame == "TRUE_NORTH":
        bearing = {"az_deg": bearing_obj["az_deg"]}
        if bearing_obj.get("el_deg") is not None:
            bearing["el_deg"] = bearing_obj["el_deg"]
        err = raw.get("bearing_error_deg")
        if err is not None:
            features["angular_error_deg"] = err
            quality["measurement_error"] = {
                "value": err,
                "unit": "deg",
                "metric": "1_SIGMA",
            }
        quality["bearing_frame"] = "TRUE_NORTH"
    elif bearing_obj.get("az_deg") is not None:
        _record_unknown_frame_bearing(
            features,
            az_deg=bearing_obj["az_deg"],
            error_deg=raw.get("bearing_error_deg"),
            el_deg=bearing_obj.get("el_deg"),
        )
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
    }
    if based_on:
        event["lineage"] = {
            "based_on": [str(item) for item in based_on],
            "transform": f"translate:{SCHEMA_ID_SERIAL}@{ADAPTER_VERSION}",
        }
    if bearing is not None:
        event["payload"]["bearing"] = bearing
    _apply_sensor_geo(event, geo, preserved_alt_m, needs_1_1_0)

    if bearing_obj.get("confidence") is not None:
        quality["sensor_confidence"] = bearing_obj["confidence"]

    return event
