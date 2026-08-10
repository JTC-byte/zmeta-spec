"""bladeRF / ROS2 EW rf_detection to ZMeta OBSERVATION_EVENT translator.

Translates the structured ``rf_detection`` records emitted by an edge-comms
bladeRF EW payload (ROS2 ``ros2_ew`` topics ``sdr/orbit_spectrum`` and
``spectrum_fft``) into ZMeta RF ``OBSERVATION_EVENT``s. These are decoded
detections (centre frequency, power, SNR, noise floor, bearing metadata), not
raw IQ -- the DSP/FFT stage runs upstream of ZMeta (AUTHORING section 1).

Reference implementation for the ``adapters/mapping-packs/edge-comms-bladerf``
mapping pack. Per ``adapters/mapping-packs/README.md`` no runtime engine
executes ``mapping.yaml``; this module is the hand-written translation the pack
describes, written to the ``adapters/AUTHORING.md`` requirements and pinned to
the pack's two real-capture fixture pairs.

Honesty decisions (each cites its governing authority; see README for detail):

* **Frame-unlabeled bearing is demoted, never promoted** (contract 6.4,
  AUTHORING rule 2). The native ``bearing_deg`` is heading-derived (UAS heading
  plus a fixed antenna offset) and the capture asserts no reference frame --
  ``metadata.heading_source`` ("interpolated") names a sampling method, not a
  datum. So the raw value travels only in the explicitly named
  ``features.native_bearing_deg`` / ``features.native_bearing_error_deg`` and
  the canonical ``payload.bearing`` is omitted in BOTH cases. A minted
  ``TRUE_NORTH`` assertion the producer never made would launder an unprovable
  bearing (AUTHORING section 3, "A frame-unlabeled native bearing is the mirror
  case").
* **Canonical geo is all-or-nothing** (contract 6.8, AUTHORING rule 9). Null or
  null-island ``(0,0)`` sensor positions refuse canonical geo: ``payload.geo``
  is omitted and ``quality.geo_status`` is ``UNAVAILABLE`` rather than
  zero-filling a coordinate.
* **Nothing is fabricated** (AUTHORING rules 3, 8). Quality metrics, bearings,
  positions and lineage are emitted only from real source values. The raw
  ``bearing_error_deg`` bound declares no statistical metric, so it stays a
  feature and no ``quality.measurement_error`` is claimed. ``snr_db`` is
  emitted only when the source reports it.
* **Degraded timing stays visible** (contract 5.3, AUTHORING rule 5). The
  ``rf_detection`` format carries no clock-sync metadata, so timing falls to the
  deliberately degraded ``UNKNOWN`` / ``UNSYNCED`` / 60 s fallback from
  ``coerce_timing_quality``; ``features.timestamp_source`` records whether
  ``event.ts`` came from embedded telemetry or adapter receive time.
* **Original observations omit lineage** (contract 4.8, AUTHORING rule 1). With
  no ZMeta parent, ``lineage`` is omitted entirely; a ``translate:`` transform
  is stamped only when a caller supplies real parent event ids.

Source archive: Z-ISR ``flight-artifacts-2026-05-14_v22rfpayload-edge-comms``.
"""

import math

from adapters.ingress.time_utils import (
    coerce_timing_quality,
    epoch_ms_to_utc_z,
    normalize_utc_z,
)
from zmeta_uuid import uuid7


def _finite_number(value):
    """True only for a real, finite numeric (not bool, not NaN/inf).

    A non-finite float is in the JSON value model by type and outside it by
    value (RFC 8259) -- so it is never an honest measurement. Screening it
    at the adapter boundary keeps a NaN out of a canonical field HERE,
    rather than relying on the gateway's non-finite gate to catch what this
    reference adapter should never have emitted.
    """
    return (
        not isinstance(value, bool)
        and isinstance(value, (int, float))
        and math.isfinite(value)
    )

ADAPTER_VERSION = "1.0.0"
SCHEMA_ID = "vendor:edge_comms_bladerf:v1"
PRODUCER = "rf-sensor-bladerf"
NODE_ROLE = "EDGE"

# Native detection keys used to recognise a bladeRF rf_detection record.
_SIGNATURE_KEYS = ("detection_id", "center_freq_hz", "power_dbm", "metadata")

# Schema-required RF feature set (contract 7.4 / locked schema RF minimum):
# a reading missing any of these is refused, never emitted schema-invalid
# (AUTHORING rule 10).
_REQUIRED_RF_FEATURES = ("center_freq_hz", "bandwidth_hz", "power_dbm")

# Optional top-level detection features, copied only when the source carries a
# non-null value. bandwidth_hz on the spectrum_fft product is the FFT bin width
# (sample_rate_hz / fft_size) -- a documented resolution artifact the source
# reports, not a measured emitter bandwidth (pack README); it is passed through
# verbatim, never reinterpreted.
_OPTIONAL_TOP_FEATURES = ("snr_db", "noise_floor_dbm", "detection_id")

# Whitelisted metadata -> feature mappings. Only these keys cross into features;
# unmapped metadata (antenna_left, baseline_m, scan_state, ...) is intentionally
# dropped so the canonical event carries only consumer-relevant provenance.
_METADATA_FEATURES = {
    "sensor_hw": "sensor_hw",
    "source": "source",
    "source_topic": "source_topic",
    "bearing_source": "bearing_source",
    "heading_source": "heading_source_native",
    "uas_heading_deg": "uas_heading_deg",
    "timestamp_source": "timestamp_source",
    "orbit_spectrum_bin": "orbit_spectrum_bin",
    "orbit_spectrum_bins": "orbit_spectrum_bins",
    "fft_bin": "fft_bin",
    "fft_size": "fft_size",
    "bin_width_hz": "bin_width_hz",
    "sample_rate_hz": "sample_rate_hz",
    "fft_center_freq_hz": "fft_center_freq_hz",
}


def detect(input_bytes):
    """Return the schema_id when the payload looks like a bladeRF rf_detection.

    Recognises a JSON object carrying the bladeRF detection signature keys and
    ``metadata.sensor_hw == "bladerf"``; anything else returns ``None`` so the
    caller can try another adapter (fail closed on ambiguous input).
    """
    import json

    if isinstance(input_bytes, (bytes, bytearray)):
        text = bytes(input_bytes).decode("utf-8", errors="replace")
    elif isinstance(input_bytes, str):
        text = input_bytes
    else:
        return None
    try:
        obj = json.loads(text)
    except (ValueError, TypeError):
        return None
    if not isinstance(obj, dict):
        return None
    if not all(key in obj for key in _SIGNATURE_KEYS):
        return None
    meta = obj.get("metadata")
    if not isinstance(meta, dict) or meta.get("sensor_hw") != "bladerf":
        return None
    return SCHEMA_ID


def _resolve_ts(timestamp_ms):
    """Normalize the mapped ``event.ts`` source, or return ``None`` to refuse.

    The pack maps ``event.ts`` from ``input.timestamp_ms`` alone
    (``mapping.yaml``); the paired human-readable ``timestamp`` string is a
    rendering of the same instant, not an alternate authority, so it never
    rescues a record whose mapped source is missing or unparseable (refuse
    rather than guess an alternate mapping; AUTHORING section 9).
    """
    if isinstance(timestamp_ms, bool) or not isinstance(timestamp_ms, (int, float)):
        return None
    try:
        return epoch_ms_to_utc_z(timestamp_ms)
    except (ValueError, OverflowError, OSError):
        return None


def _resolve_geo(lat, lon, alt_hae_m, alt_native_m):
    """Apply the all-or-nothing geo rule (contract 6.8) and the altitude-datum
    boundary (contract 6.2, doctrine C1-01).

    The horizontal fix must be present, finite numerics, and not the
    null-island ``(0,0)`` sentinel, or geo is omitted entirely. Missing,
    non-finite, or uninterpretable components are never zero-filled and never
    guessed -- a NaN/inf coordinate is not a position, so it refuses geo like
    any other unusable fix rather than shipping under ``geo_status:
    AVAILABLE``.

    The vertical is datum-gated. ``sensor_alt_hae_m`` is a deployment
    assertion of WGS-84 HAE and is the only value that may occupy canonical
    ``alt_m`` (a full 3-D geo, 1.0 stamp). The native ``sensor_alt_m``
    asserts no datum -- the rf_detection position is UAS flight-telemetry
    derived, where the natural altitude source (MAVLink global position) is
    MSL -- so it never reaches ``alt_m``: a real fix publishes as the
    declared 2-D form (doctrine A1-02) and the caller preserves the native
    value under ``features.native_sensor_alt_m``, the same demotion this
    adapter applies to its frame-unlabeled bearing. A fix with no vertical of
    any kind stays omitted (absence is refused, not degraded; same
    disposition as the MAVLink reference implementation).

    Returns ``(geo_or_None, needs_1_1_0)``; the 2-D branch needs the 1.1.0
    stamp because ``dimensionality`` is v1.1.0 vocabulary and the locked v1.0
    geo def is additionalProperties:false over lat/lon/alt_m.
    """
    if lat is None or lon is None:
        return None, False
    if not all(_finite_number(value) for value in (lat, lon)):
        return None, False
    if float(lat) == 0.0 and float(lon) == 0.0:
        return None, False
    if alt_hae_m is not None and _finite_number(alt_hae_m):
        return {"lat": float(lat), "lon": float(lon), "alt_m": float(alt_hae_m)}, False
    if alt_native_m is not None and _finite_number(alt_native_m):
        return {"lat": float(lat), "lon": float(lon), "dimensionality": "2D"}, True
    return None, False


def _degraded_timing(ts_iso, supplied=None):
    """Build timing_quality, preserving event-ts precision on the fallback.

    The governed degraded fallback (``UNKNOWN`` / ``UNSYNCED`` / 60 s) comes
    straight from ``coerce_timing_quality``. When ``last_sync_ts`` is filled
    from the event timestamp (the fallback path), it is re-expressed at the
    event timestamp's millisecond precision so the two stay aligned (contract
    5.3); a caller-supplied ``last_sync_ts`` is kept as normalized by the
    shared helper, never re-rendered. ``supplied`` carries real source
    GPS/NTP/PTP metadata when a deployment has it -- the rf_detection format
    does not, so the fallback path is what these captures take.
    """
    supplied_last_sync = (
        isinstance(supplied, dict) and supplied.get("last_sync_ts") is not None
    )
    timing = coerce_timing_quality(supplied, event_ts=ts_iso)
    if not supplied_last_sync:
        timing["last_sync_ts"] = normalize_utc_z(
            timing["last_sync_ts"], timespec="milliseconds"
        )
    return timing


def translate_detection(
    raw,
    *,
    platform_id=None,
    sensor_id=None,
    based_on=None,
    timing_quality=None,
):
    """Translate one bladeRF ``rf_detection`` dict into a ZMeta event.

    Returns a ZMeta ``OBSERVATION_EVENT`` dict, or ``None`` when a schema
    obligation cannot be met honestly (fail closed; contract 3.4):

    * a missing/null/empty ``platform_id`` (deployment identity is never
      fabricated),
    * a missing/unparseable ``timestamp_ms`` (the pack's only mapped
      ``event.ts`` source; the paired ``timestamp`` string is a rendering,
      not an alternate authority), or
    * any missing required RF feature -- ``center_freq_hz``, ``bandwidth_hz`` or
      ``power_dbm`` (contract 7.4 / AUTHORING rule 10).

    ``sensor_id`` defaults to ``metadata.zmeta_sensor_id``; when neither is
    present the schema-optional ``source.sensor_id`` is omitted, not invented.
    ``based_on`` is caller-supplied real parent event ids; with none, ``lineage``
    is omitted entirely (contract 4.8).
    """
    if not isinstance(raw, dict):
        return None
    if platform_id is None or (isinstance(platform_id, str) and not platform_id.strip()):
        return None

    ts_iso = _resolve_ts(raw.get("timestamp_ms"))
    if ts_iso is None:
        return None

    # Required RF feature set: refuse rather than emit schema-invalid. A
    # non-finite required feature (NaN center frequency, inf power) is not a
    # detection any more than a NaN coordinate is a position, so it fails
    # closed here too (contract 7.4 / 8.1, AUTHORING rule 10) -- 0.0
    # bandwidth stays valid, the documented FFT-bin-width convention.
    for key in _REQUIRED_RF_FEATURES:
        if raw.get(key) is None or not _finite_number(raw[key]):
            return None

    meta = raw.get("metadata")
    if not isinstance(meta, dict):
        meta = {}

    features = {key: raw[key] for key in _REQUIRED_RF_FEATURES}
    for key in _OPTIONAL_TOP_FEATURES:
        if raw.get(key) is not None:
            # A non-finite optional numeric (snr, noise floor) is omitted,
            # not laundered into features; detection_id is a non-numeric
            # identity and passes through as-is.
            if key == "detection_id" or _finite_number(raw[key]):
                features[key] = raw[key]
    for src_key, feat_key in _METADATA_FEATURES.items():
        value = meta.get(src_key)
        if value is None:
            continue
        # Same value-honesty screen as the top-level features (pre-cut
        # review): a non-finite numeric metadata value is not a
        # measurement, so it is omitted rather than copied into features.
        # Non-numeric metadata (identifiers, labels) passes through.
        if isinstance(value, (int, float)) and not _finite_number(value):
            continue
        features[feat_key] = value

    # Frame-unlabeled native bearing: demote to explicitly named features; the
    # raw error bound declares no statistical metric, so no canonical bearing
    # and no quality.measurement_error is emitted (contract 6.4, AUTHORING
    # rule 2 + section 3 mirror case).
    if raw.get("bearing_deg") is not None and _finite_number(raw["bearing_deg"]):
        # The demoted native bearing is still a measurement claim, so it
        # takes the same non-finite screen as every other feature: a NaN
        # bearing is omitted, never carried under an explicitly-named
        # field that implies a real observation (pre-cut review).
        features["native_bearing_deg"] = raw["bearing_deg"]
        if raw.get("bearing_error_deg") is not None and _finite_number(
            raw["bearing_error_deg"]
        ):
            features["native_bearing_error_deg"] = raw["bearing_error_deg"]

    alt_native_m = raw.get("sensor_alt_m")
    geo, needs_1_1_0 = _resolve_geo(
        raw.get("sensor_lat"),
        raw.get("sensor_lon"),
        raw.get("sensor_alt_hae_m"),
        alt_native_m,
    )
    if needs_1_1_0:
        # The datum-unlabeled native vertical survives as an explicitly named
        # feature (the bearing demotion's sibling), never as canonical alt_m.
        features["native_sensor_alt_m"] = float(alt_native_m)

    quality = {}
    if raw.get("snr_db") is not None:
        if not _finite_number(raw["snr_db"]):
            # A non-finite SNR is not a measurement; refuse the whole event
            # rather than launder NaN/inf into a canonical quality field
            # (same value-honesty rule as geo above).
            return None
        quality["snr_db"] = raw["snr_db"]
    # A declared 2-D geo cannot sit beside geo_status AVAILABLE (A1-02
    # coherence arm 2): the horizontal fix is real, the vertical is not
    # canonically statable, and the status says so.
    if geo is None:
        quality["geo_status"] = "UNAVAILABLE"
    elif needs_1_1_0:
        quality["geo_status"] = "VERTICAL_UNAVAILABLE"
    else:
        quality["geo_status"] = "AVAILABLE"
    quality["calibration_state"] = "UNCALIBRATED"

    sid = sensor_id or meta.get("zmeta_sensor_id")

    source = {
        "platform_id": platform_id,
        "node_role": NODE_ROLE,
        "producer": PRODUCER,
    }
    if sid is not None:
        source["sensor_id"] = sid

    payload = {
        "modality": "RF",
        "features": features,
        "quality": quality,
        "timing_quality": _degraded_timing(ts_iso, timing_quality),
    }
    if geo:
        payload["geo"] = geo

    event = {
        "zmeta_version": "1.1.0" if needs_1_1_0 else "1.0",
        "event": {
            "event_id": str(uuid7()),
            "event_type": "OBSERVATION_EVENT",
            "event_subtype": "RF",
            "ts": ts_iso,
        },
        "source": source,
        "payload": payload,
    }
    if based_on:
        # Caller-supplied real parent ids pass through uncoerced -- a
        # non-UUIDv7 entry is left for schema validation to reject rather
        # than silently reshaped into a plausible-looking lineage id.
        event["lineage"] = {
            "based_on": list(based_on),
            "transform": f"translate:{SCHEMA_ID}@{ADAPTER_VERSION}",
        }
    return event


def translate(
    input_obj,
    schema_id=SCHEMA_ID,
    *,
    platform_id=None,
    sensor_id=None,
    based_on=None,
    timing_quality=None,
):
    """Translate one bladeRF detection into a list of ZMeta events.

    Returns ``[event]`` on success or ``[]`` on fail-closed refusal (contract
    3.4). Mirrors the ``example-vendor`` worked-exercise entry point so the
    adapter harness can pin both emission and refusal with ``result: "events"``
    plus an ``event_count`` pin.
    """
    if schema_id != SCHEMA_ID:
        return []
    event = translate_detection(
        input_obj,
        platform_id=platform_id,
        sensor_id=sensor_id,
        based_on=based_on,
        timing_quality=timing_quality,
    )
    return [event] if event is not None else []


def validate(zmeta_event):
    """Validate one event against the locked v1.0 schema.

    Returns ``("pass", [])`` or ``("fail", [violation strings])``.
    """
    import json
    from pathlib import Path

    import jsonschema

    schema_path = (
        Path(__file__).resolve().parents[3] / "schema" / "zmeta-event-1.0.schema.json"
    )
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    # No format_checker is installed. `date-time` is the only `format`
    # assertion in the ZMeta schemas, and jsonschema registers no `date-time`
    # checker without an RFC 3339 checker library, which this stack does not
    # depend on. The `utcDateTime` `pattern` is the real gate on timestamps;
    # `format` is annotation-only here.
    validator = jsonschema.Draft202012Validator(schema)
    violations = [
        f"{'/'.join(str(p) for p in error.absolute_path)}: {error.message}"
        for error in validator.iter_errors(zmeta_event)
    ]
    return ("pass", []) if not violations else ("fail", violations)
