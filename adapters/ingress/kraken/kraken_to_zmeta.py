"""KrakenSDR DOA to ZMeta OBSERVATION_EVENT translator.

Translates KrakenSDR direction-of-arrival CSV output into ZMeta RF
OBSERVATION_EVENTs (LOBs). The KrakenSDR is a 5-channel coherent SDR
receiver that produces bearing estimates via DOA algorithms.

Input formats:
  - CSV row: epoch_sec, doa_deg, confidence_0_99, rssi_db, freq_hz
  - JSON dict (replay): {bearing_deg, power_dbm, center_freq_hz, ...}

Source: Z-ISR edge/edge/sensors/kraken_rf.py
"""

from datetime import datetime, timezone
from zmeta_uuid import uuid7

ADAPTER_VERSION = "1.0.0"
SCHEMA_ID = "krakensdr-doa"
DEFAULT_SENSOR_ID = "krakensdr_rf"


def _utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _confidence_to_error_deg(conf_0_99):
    """Map Kraken confidence (0-99) to a conservative angular error estimate.

    At confidence 99 the error is 5 deg (Kraken's best case with UCA-5).
    At confidence 0 the error is 45 deg (omnidirectional uncertainty).
    """
    c = max(0.0, min(99.0, conf_0_99))
    return max(5.0, 45.0 * (1.0 - c / 99.0))


def detect(input_bytes):
    """Inspect raw input and return schema_id if it looks like Kraken DOA CSV."""
    text = input_bytes.decode("utf-8", errors="replace").strip()
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("<") or line.startswith("#"):
            continue
        parts = line.split(",")
        if len(parts) >= 5:
            try:
                float(parts[0])
                float(parts[1])
                float(parts[2])
                return SCHEMA_ID
            except ValueError:
                continue
    return None


def translate_csv_row(fields, *, platform_id, sensor_geo=None, sensor_id=None):
    """Translate a single Kraken DOA CSV row into a ZMeta OBSERVATION_EVENT.

    Args:
        fields: List of string values from one CSV row. Minimum 5 columns:
            [0] epoch seconds (float, or 13-digit ms)
            [1] DOA azimuth degrees
            [2] confidence 0-99
            [3] RSSI dB
            [4] centre frequency Hz
        platform_id: Platform identifier string.
        sensor_geo: Optional dict {lat, lon, alt_m} for sensor position.
        sensor_id: Optional sensor identifier (defaults to "krakensdr_rf").

    Returns:
        ZMeta event dict, or None if the row cannot be parsed.
    """
    if len(fields) < 5:
        return None
    try:
        ts_raw = float(fields[0].strip())
        az_deg = float(fields[1].strip()) % 360.0
        conf = float(fields[2].strip())
        rssi_db = float(fields[3].strip())
        freq_hz = float(fields[4].strip())
    except (ValueError, IndexError):
        return None

    if ts_raw > 1e12:
        ts_ms = int(ts_raw)
    else:
        ts_ms = int(ts_raw * 1000)
    if ts_ms <= 0:
        return None

    err_deg = _confidence_to_error_deg(conf)
    ts_iso = datetime.fromtimestamp(
        ts_ms / 1000.0, tz=timezone.utc
    ).isoformat(timespec="milliseconds")

    geo = dict(sensor_geo) if sensor_geo else None
    sid = sensor_id or DEFAULT_SENSOR_ID

    event = {
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
            "producer": "krakensdr-adapter",
            "sensor_id": sid,
        },
        "payload": {
            "modality": "RF",
            "bearing": {"az_deg": az_deg},
            "features": {
                "center_freq_hz": freq_hz,
                "bandwidth_hz": 0.0,
                "power_dbm": rssi_db,
                "angular_error_deg": err_deg,
                "kraken_confidence_0_99": conf,
                "sensor_hw": "krakensdr",
            },
            "quality": {
                "measurement_error": err_deg,
                "error_metric": "1_SIGMA",
                "snr_db": rssi_db + 100.0,
                "calibration_state": "CALIBRATED",
                "geo_status": "AVAILABLE" if geo else "UNAVAILABLE",
            },
        },
        "lineage": {
            "based_on": [str(uuid7())],
            "transform": f"translate:{SCHEMA_ID}@{ADAPTER_VERSION}",
        },
    }
    if geo:
        event["payload"]["geo"] = geo
    return event


def translate_json(raw, *, platform_id, sensor_geo=None, sensor_id=None):
    """Translate a Kraken JSON replay dict into a ZMeta OBSERVATION_EVENT.

    Args:
        raw: Dict with keys like bearing_deg, power_dbm, center_freq_hz,
            timestamp_ms, bearing_error_deg, metadata, etc.
        platform_id: Platform identifier string.
        sensor_geo: Optional dict {lat, lon, alt_m}.
        sensor_id: Optional sensor identifier.

    Returns:
        ZMeta event dict.
    """
    import time

    ts_ms = int(raw.get("timestamp_ms", int(time.time() * 1000)))
    bearing = float(raw["bearing_deg"]) % 360.0
    err = float(raw.get("bearing_error_deg", 15.0))
    power = float(raw.get("power_dbm", -80.0))
    freq_hz = float(raw.get("center_freq_hz", 0.0))
    bw_hz = float(raw.get("bandwidth_hz", 0.0))
    snr = raw.get("snr_db")
    conf = raw.get("bearing_confidence")
    meta = raw.get("metadata", {})

    ts_iso = datetime.fromtimestamp(
        ts_ms / 1000.0, tz=timezone.utc
    ).isoformat(timespec="milliseconds")

    geo = dict(sensor_geo) if sensor_geo else None
    sid = sensor_id or meta.get("zmeta_sensor_id", DEFAULT_SENSOR_ID)

    features = {
        "center_freq_hz": freq_hz,
        "bandwidth_hz": bw_hz,
        "power_dbm": power,
        "angular_error_deg": err,
        "sensor_hw": "krakensdr",
    }
    if meta.get("kraken_confidence_0_99") is not None:
        features["kraken_confidence_0_99"] = meta["kraken_confidence_0_99"]
    if meta.get("hardware_model"):
        features["hardware_model"] = meta["hardware_model"]

    quality = {
        "measurement_error": err,
        "error_metric": "1_SIGMA",
        "calibration_state": "CALIBRATED",
    }
    if snr is not None:
        quality["snr_db"] = snr
    if conf is not None:
        quality["bearing_confidence"] = conf

    event = {
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
            "producer": "krakensdr-adapter",
            "sensor_id": sid,
        },
        "payload": {
            "modality": "RF",
            "bearing": {"az_deg": bearing},
            "features": features,
            "quality": quality,
        },
        "lineage": {
            "based_on": [str(uuid7())],
            "transform": f"translate:{SCHEMA_ID}@{ADAPTER_VERSION}",
        },
    }
    quality["geo_status"] = "AVAILABLE" if geo else "UNAVAILABLE"
    if geo:
        event["payload"]["geo"] = geo
    return event


def translate_http_body(body, *, platform_id, sensor_geo=None, sensor_id=None):
    """Translate a full Kraken DOA HTTP response body into ZMeta events.

    Parses all CSV rows in the body, returns the latest valid detection
    as a ZMeta event (Kraken typically returns one active row).

    Returns:
        List of ZMeta event dicts (usually 0 or 1).
    """
    events = []
    for raw_line in body.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("<") or line.startswith("#"):
            continue
        if "," not in line:
            continue
        parts = [p.strip() for p in line.split(",")]
        evt = translate_csv_row(
            parts,
            platform_id=platform_id,
            sensor_geo=sensor_geo,
            sensor_id=sensor_id,
        )
        if evt is not None:
            events = [evt]
    return events
