"""KrakenSDR DOA to ZMeta OBSERVATION_EVENT translator.

Translates KrakenSDR direction-of-arrival CSV output into ZMeta RF
OBSERVATION_EVENTs (LOBs). The KrakenSDR is a 5-channel coherent SDR
receiver that produces bearing estimates via DOA algorithms.

Input formats:
  - CSV row: epoch_sec, doa_deg, confidence_0_99, rssi_db, freq_hz
  - JSON dict (replay): {bearing_deg, power_dbm, center_freq_hz, ...}

Source: Z-ISR edge/edge/sensors/kraken_rf.py
"""

import math

from adapters.ingress.time_utils import coerce_timing_quality, epoch_ms_to_utc_z, utc_now_z
from zmeta_uuid import uuid7

ADAPTER_VERSION = "1.3.0"
SCHEMA_ID = "krakensdr-doa"
DEFAULT_SENSOR_ID = "krakensdr_rf"


def _finite(value):
    """A real finite number, or None. Bools are not numbers here.

    Mirrors the adsb/ais `_finite()` helper: a NaN/inf reading is not a
    measurement, and Python's own `float()` and `json.loads()` both accept
    non-finite literals ("nan", "inf") as valid syntax, so parsing success
    alone does not mean a value is usable.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value) if math.isfinite(value) else None


def _utc_now():
    return utc_now_z()


def _apply_bearing_frame(payload, doa_deg, platform_heading_deg, array_offset_deg, heading_source):
    """Apply the convert-or-omit bearing rule (semantics contract section 6.4).

    The Kraken DOA azimuth is array-relative. With a platform heading it is
    rotated into degrees true north and emitted as canonical ``bearing.az_deg``
    with frame provenance in ``quality``. Without a heading the canonical
    ``bearing`` is omitted entirely and the raw angle travels only in the
    explicitly named ``features.doa_array_relative_deg`` field.
    """
    payload["features"]["doa_array_relative_deg"] = doa_deg
    if platform_heading_deg is None:
        return
    az_true = (doa_deg + float(platform_heading_deg) + float(array_offset_deg)) % 360.0
    payload["bearing"] = {"az_deg": az_true}
    payload["quality"]["bearing_frame"] = "TRUE_NORTH"
    if heading_source is not None:
        payload["quality"]["heading_source"] = heading_source


def _resolve_sensor_geo(sensor_geo):
    """Apply the altitude-datum boundary (contract 6.2, doctrine C1-01) to the
    caller-supplied sensor position.

    Only a vertical declared WGS-84 HAE (``alt_hae_m``) may occupy canonical
    ``geo.alt_m``. The legacy ``alt_m`` key asserts no datum -- a typical
    caller has a GPS-derived or surveyed site elevation, which is
    MSL-referenced, not HAE -- so it never reaches ``alt_m``: the position
    degrades to the declared 2-D form (doctrine A1-02) with the value
    preserved non-canonically. This is the vertical instance of the
    discipline the bearing already gets from the heading-frame gate: no
    evidence, no canonical claim. A position with no vertical of any kind
    stays omitted (absence is refused, not degraded).

    Returns ``(geo_or_None, preserved_alt_or_None, needs_1_1_0)``.
    """
    if not sensor_geo:
        return None, None, False
    lat = sensor_geo.get("lat")
    lon = sensor_geo.get("lon")
    if lat is None or lon is None:
        return None, None, False
    alt_hae_m = sensor_geo.get("alt_hae_m")
    if alt_hae_m is not None:
        return {"lat": lat, "lon": lon, "alt_m": alt_hae_m}, None, False
    alt_unspecified_m = sensor_geo.get("alt_m")
    if alt_unspecified_m is not None:
        return {"lat": lat, "lon": lon, "dimensionality": "2D"}, alt_unspecified_m, True
    return None, None, False


def _apply_sensor_geo(event, geo, preserved_alt_m, needs_1_1_0):
    """Attach the resolved position, its status, and the version stamp.

    The declared 2-D branch stamps 1.1.0 (``dimensionality`` is v1.1.0
    vocabulary) and cannot sit beside ``geo_status: AVAILABLE`` (A1-02
    coherence arm 2), so the status says VERTICAL_UNAVAILABLE and the
    undeclared-datum vertical rides along as
    ``quality.kraken_sensor_alt_unspecified_datum_m``.
    """
    quality = event["payload"]["quality"]
    if geo:
        event["payload"]["geo"] = geo
        if needs_1_1_0:
            event["zmeta_version"] = "1.1.0"
            quality["geo_status"] = "VERTICAL_UNAVAILABLE"
            quality["kraken_sensor_alt_unspecified_datum_m"] = preserved_alt_m
        else:
            quality["geo_status"] = "AVAILABLE"
    else:
        quality["geo_status"] = "UNAVAILABLE"


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


def translate_csv_row(
    fields,
    *,
    platform_id,
    sensor_geo=None,
    sensor_id=None,
    platform_heading_deg=None,
    array_offset_deg=0.0,
    heading_source=None,
    calibration_state="UNCALIBRATED",
    based_on=None,
):
    """Translate a single Kraken DOA CSV row into a ZMeta OBSERVATION_EVENT.

    Args:
        fields: List of string values from one CSV row. Minimum 5 columns:
            [0] epoch seconds (float, or 13-digit ms)
            [1] DOA azimuth degrees (array-relative)
            [2] confidence 0-99
            [3] RSSI dB
            [4] centre frequency Hz
        platform_id: Platform identifier string.
        sensor_geo: Optional sensor-position dict. ``{lat, lon, alt_hae_m}``
            when the deployment can assert WGS-84 HAE (contract 6.2); the
            legacy ``alt_m`` key asserts no datum and never reaches
            canonical ``alt_m`` (the position degrades to the declared 2-D
            form with the value preserved as
            ``quality.kraken_sensor_alt_unspecified_datum_m``).
        sensor_id: Optional sensor identifier (defaults to "krakensdr_rf").
        platform_heading_deg: Platform heading in degrees true north. When
            provided, the array-relative DOA is rotated to true north and
            emitted as canonical bearing.az_deg. When None (default), the
            canonical bearing is omitted and the raw DOA travels only in
            features.doa_array_relative_deg.
        array_offset_deg: Fixed clockwise mounting offset of the array
            reference relative to platform heading.
        heading_source: Optional heading reference label recorded in
            quality.heading_source (e.g. "AHRS_TRUE", "GPS_COURSE",
            "FIXED_MOUNT_SURVEYED").
        based_on: Optional list of real parent ZMeta event ids (UUIDv7
            strings). When provided, an envelope lineage block is emitted;
            when None (default), lineage is omitted because this row is an
            original observation with no ZMeta parent. Parent ids are never
            fabricated.

    Returns:
        ZMeta event dict, or None if the row cannot be parsed.
    """
    if len(fields) < 5:
        return None
    try:
        ts_raw = float(fields[0].strip())
        doa_deg = float(fields[1].strip()) % 360.0
        conf = float(fields[2].strip())
        rssi_db = float(fields[3].strip())
        freq_hz = float(fields[4].strip())
    except (ValueError, IndexError):
        return None
    # float() parses "nan"/"inf" without raising, so a non-finite value in
    # any of the five required columns is not caught by the try/except above.
    # The CSV path's own convention is to refuse whatever it cannot parse
    # (see README); a non-finite column is exactly as unusable as text that
    # fails float() outright, so the whole row is refused rather than one
    # field silently carrying NaN into the event (or, for ts_raw, crashing
    # the int() conversion below).
    if not all(math.isfinite(v) for v in (ts_raw, doa_deg, conf, rssi_db, freq_hz)):
        return None

    if ts_raw > 1e12:
        ts_ms = int(ts_raw)
    else:
        ts_ms = int(ts_raw * 1000)
    if ts_ms <= 0:
        return None

    err_deg = _confidence_to_error_deg(conf)
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
            "producer": "krakensdr-adapter",
            "sensor_id": sid,
        },
        "payload": {
            "modality": "RF",
            "features": {
                "center_freq_hz": freq_hz,
                "bandwidth_hz": 0.0,
                "power_dbm": rssi_db,
                "angular_error_deg": err_deg,
                "kraken_confidence_0_99": conf,
                "sensor_hw": "krakensdr",
            },
            "quality": {
                "measurement_error": {
                    "value": err_deg,
                    "unit": "deg",
                    "metric": "1_SIGMA",
                },
                "calibration_state": calibration_state,
            },
            "timing_quality": coerce_timing_quality(event_ts=ts_iso),
        },
    }
    if based_on:
        event["lineage"] = {
            "based_on": [str(item) for item in based_on],
            "transform": f"translate:{SCHEMA_ID}@{ADAPTER_VERSION}",
        }
    _apply_bearing_frame(
        event["payload"], doa_deg, platform_heading_deg, array_offset_deg, heading_source
    )
    _apply_sensor_geo(event, geo, preserved_alt_m, needs_1_1_0)
    return event


def translate_json(
    raw,
    *,
    platform_id,
    sensor_geo=None,
    sensor_id=None,
    platform_heading_deg=None,
    array_offset_deg=0.0,
    heading_source=None,
    calibration_state="UNCALIBRATED",
    based_on=None,
):
    """Translate a Kraken JSON replay dict into a ZMeta OBSERVATION_EVENT.

    The replay producer is the same physical sensor as the CSV path, so the
    input `bearing_deg` is array-relative DOA and follows the same
    convert-or-omit bearing-frame rule as the CSV path.

    Args:
        raw: Dict with keys like bearing_deg, power_dbm, center_freq_hz,
            timestamp_ms, bearing_error_deg, metadata, etc.
        platform_id: Platform identifier string.
        sensor_geo: Optional sensor-position dict; same altitude-datum
            boundary as ``translate_csv_row`` (only ``alt_hae_m`` reaches
            canonical ``alt_m``; the legacy ``alt_m`` key degrades to the
            declared 2-D form).
        sensor_id: Optional sensor identifier.
        platform_heading_deg: Platform heading in degrees true north
            (None omits the canonical bearing; see translate_csv_row).
        array_offset_deg: Fixed clockwise array mounting offset relative to
            platform heading.
        heading_source: Optional heading reference label recorded in
            quality.heading_source.
        based_on: Optional list of real parent ZMeta event ids (UUIDv7
            strings). When None (default), lineage is omitted; parent ids
            are never fabricated.

    Returns:
        ZMeta event dict, or None if the input is missing a measured RF
        field (``center_freq_hz`` or ``power_dbm``) or the field is present
        but non-finite (NaN/inf is not a measurement either). The KrakenSDR
        measures both, so an unusable value means broken input -- the
        adapter refuses rather than fabricating a value; the same applies to
        ``bearing_deg``, the DOA measurement itself. ``bandwidth_hz`` is
        different: the sensor physically cannot measure emitter bandwidth,
        so a missing value takes the same documented 0.0 sentinel as the CSV
        path (unconditionally, this rule is not touched by NaN screening). A
        missing or non-finite ``bearing_error_deg`` omits
        ``features.angular_error_deg`` and ``quality.measurement_error``
        entirely (both are schema-optional; an error bound is never
        invented). ``snr_db`` and ``bearing_confidence`` follow the same
        optional-field rule.
    """
    import time

    ts_ms = int(raw.get("timestamp_ms", int(time.time() * 1000)))
    doa_deg_raw = _finite(raw.get("bearing_deg"))
    if doa_deg_raw is None:
        return None
    doa_deg = doa_deg_raw % 360.0
    if raw.get("center_freq_hz") is None or raw.get("power_dbm") is None:
        return None
    freq_hz = _finite(raw.get("center_freq_hz"))
    power = _finite(raw.get("power_dbm"))
    if freq_hz is None or power is None:
        return None
    bw_hz = float(raw.get("bandwidth_hz", 0.0))
    err = _finite(raw.get("bearing_error_deg"))
    snr = _finite(raw.get("snr_db"))
    conf = _finite(raw.get("bearing_confidence"))
    meta = raw.get("metadata", {})

    ts_iso = epoch_ms_to_utc_z(ts_ms)

    geo, preserved_alt_m, needs_1_1_0 = _resolve_sensor_geo(sensor_geo)
    sid = sensor_id or meta.get("zmeta_sensor_id", DEFAULT_SENSOR_ID)

    features = {
        "center_freq_hz": freq_hz,
        "bandwidth_hz": bw_hz,
        "power_dbm": power,
        "sensor_hw": "krakensdr",
    }
    if err is not None:
        features["angular_error_deg"] = err
    if meta.get("kraken_confidence_0_99") is not None:
        features["kraken_confidence_0_99"] = meta["kraken_confidence_0_99"]
    if meta.get("hardware_model"):
        features["hardware_model"] = meta["hardware_model"]

    quality = {
        "calibration_state": calibration_state,
    }
    if err is not None:
        quality["measurement_error"] = {
            "value": err,
            "unit": "deg",
            "metric": "1_SIGMA",
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
            "event_subtype": "RF",
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
            "features": features,
            "quality": quality,
            "timing_quality": coerce_timing_quality(raw.get("timing_quality"), event_ts=ts_iso),
        },
    }
    if based_on:
        event["lineage"] = {
            "based_on": [str(item) for item in based_on],
            "transform": f"translate:{SCHEMA_ID}@{ADAPTER_VERSION}",
        }
    _apply_bearing_frame(
        event["payload"], doa_deg, platform_heading_deg, array_offset_deg, heading_source
    )
    _apply_sensor_geo(event, geo, preserved_alt_m, needs_1_1_0)
    return event


def translate_http_body(
    body,
    *,
    platform_id,
    sensor_geo=None,
    sensor_id=None,
    platform_heading_deg=None,
    array_offset_deg=0.0,
    heading_source=None,
    calibration_state="UNCALIBRATED",
    based_on=None,
):
    """Translate a full Kraken DOA HTTP response body into ZMeta events.

    Parses all CSV rows in the body, returns the latest valid detection
    as a ZMeta event (Kraken typically returns one active row). The
    bearing-frame parameters are passed through to translate_csv_row.

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
            platform_heading_deg=platform_heading_deg,
            array_offset_deg=array_offset_deg,
            heading_source=heading_source,
            calibration_state=calibration_state,
            based_on=based_on,
        )
        if evt is not None:
            events = [evt]
    return events
