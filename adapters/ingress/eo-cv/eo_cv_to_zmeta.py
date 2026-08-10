"""EO (Computer Vision) detection to ZMeta INFERENCE_EVENT translator.

Translates CV inference service JSON detections into ZMeta EO
INFERENCE_EVENTs. Handles GPS destructuring, confidence filtering,
sensor geo fallback, and plausibility checks.

Input format:
  JSON from a CV inference service. Two envelope styles supported:
    - Wrapped:  {"type": "detection", "payload": {...detection...}}
    - Flat:     {...detection...}

  Required detection fields:
    - class_name (str): detected object class
    - confidence (float): detection confidence 0.0-1.0. INFERENCE_EVENT
      schema-requires top-level confidence and quality metrics are never
      fabricated, so a detection with confidence absent, null, or
      non-numeric is refused rather than emitted with a defaulted value.

  Optional detection fields:
    - gps ([lat, lon]): detection position array
    - altitude_hae_m (float): altitude in metres above the WGS-84
      ellipsoid. The only detection vertical that reaches canonical
      ``claim.geo.alt_m`` (contract 6.2).
    - altitude (float): legacy altitude in metres with no declared datum.
      Never canonical: the position degrades to the declared 2-D form
      (doctrine A1-02, 1.1.0 stamp) with the value preserved as
      ``quality.eo_cv_alt_unspecified_datum_m``. Canonical geo stays
      all-or-nothing (contract 6.8): a detection position without any
      vertical yields no ``claim.geo`` — never a zero-filled ``alt_m``.
    - bbox ([x1, y1, x2, y2]): bounding box in image coordinates
    - track_id (str|int): object tracker ID
    - stream_id (str): camera/stream identifier
    - timestamp (str): ISO 8601 timestamp

Source: Z-ISR edge/edge/sensors/eo_consumer.py and edge/edge/zmeta_builder.py
"""

import math
import re
from typing import Any, Dict, List, Optional

from adapters.ingress.time_utils import coerce_timing_quality, normalize_utc_z, utc_now_z
from zmeta_uuid import uuid7

ADAPTER_VERSION = "1.1.0"
SCHEMA_ID = "eo-cv-detection"
DEFAULT_SENSOR_ID = "eo_camera"

# Mirrors schema $defs/uuid (UUIDv7 per RFC 9562). INFERENCE_EVENT lineage
# must reference real parent events, so only schema-valid parent ids are
# accepted; nothing is ever fabricated to satisfy the requirement.
_UUID7_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-7[0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"
)

_GEO_MAX_SENSOR_DELTA_M = 10000.0


def _utc_now():
    return utc_now_z()


def _geo_distance_m(geo_a: Dict[str, float], geo_b: Dict[str, float]) -> float:
    """Approximate great-circle distance between two lat/lon points in metres."""
    lat1 = float(geo_a.get("lat", 0.0))
    lon1 = float(geo_a.get("lon", 0.0))
    lat2 = float(geo_b.get("lat", 0.0))
    lon2 = float(geo_b.get("lon", 0.0))

    r = 6371000.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    )
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def detect(input_bytes: bytes) -> Optional[str]:
    """Inspect raw JSON and return schema_id if it looks like a CV detection."""
    import json

    try:
        raw = json.loads(input_bytes)
    except (ValueError, UnicodeDecodeError):
        return None

    payload = raw.get("payload", raw)
    if "class_name" in payload:
        return SCHEMA_ID
    return None


def translate(
    detection: Dict[str, Any],
    *,
    platform_id: str,
    sensor_geo: Optional[Dict[str, float]] = None,
    confidence_floor: float = 0.0,
    strip_thumbnail: bool = True,
    strip_embedding: bool = True,
    parent_event_ids: Optional[List[str]] = None,
) -> Optional[dict]:
    """Translate a CV detection JSON into a ZMeta EO INFERENCE_EVENT.

    Handles the full GPS resolution logic from the Z-ISR edge:
      1. If detection has GPS [lat, lon] and it's not (0, 0) sentinel,
         use it as the geo position.
      2. If detection GPS is (0, 0) or missing, fall back to sensor_geo
         (e.g. from flight controller).
      3. If detection GPS is implausibly far from sensor_geo (>10km),
         fall back to sensor_geo.
      4. If neither is available, omit geo and set geo_source="unavailable".

    Altitude datum (contract 6.2, doctrine C1-01): only a vertical the
    caller declared WGS-84 HAE may occupy canonical ``claim.geo.alt_m``.
    The datum-qualified keys are ``altitude_hae_m`` on the detection and
    ``alt_hae_m`` in ``sensor_geo``. The legacy keys carry no HAE claim:
    the detection's ``altitude`` declares no datum at all, and
    ``sensor_geo["alt_m"]`` is read as MSL because its documented source
    is a flight controller GPS position, whose global-position altitude
    MAVLink defines as MSL. A legacy-only vertical degrades the position
    to the declared 2-D form (doctrine A1-02: ``dimensionality: "2D"``,
    no ``alt_m``, forced 1.1.0 stamp) with the value preserved under
    ``quality.eo_cv_alt_unspecified_datum_m`` or
    ``quality.eo_cv_sensor_alt_msl_m``.

    Canonical geo is all-or-nothing (contract 6.8): a resolved position
    missing lat, lon, or every vertical is never zero-filled;
    ``claim.geo`` is omitted entirely and geo_source is set to
    "unavailable".

    Args:
        detection: Raw detection dict. Supports both wrapped envelope
            ({"type": "detection", "payload": {...}}) and flat format.
        platform_id: Platform identifier string.
        sensor_geo: Optional FC/platform GPS position. ``{lat, lon,
            alt_hae_m}`` when the deployment can assert WGS-84 HAE (e.g.
            from GPS_RAW_INT.alt_ellipsoid); the legacy ``alt_m`` key is
            read as MSL and never reaches canonical ``alt_m``.
        confidence_floor: Minimum confidence to accept (default 0.0).
        strip_thumbnail: Remove heavyweight thumbnail field (default True).
        strip_embedding: Remove heavyweight embedding field (default True).
        parent_event_ids: Optional list of real parent ZMeta event ids
            (UUIDv7 strings) identifying the source observation events.
            When absent, the detection's ``source_event_id`` is used if it
            is a schema-valid UUIDv7.

    Returns:
        ZMeta event dict, or None when the detection is refused (fail
        closed). Refusal covers:
          - missing class_name;
          - confidence absent, null, or non-numeric — INFERENCE_EVENT
            schema-requires confidence and a quality metric is never
            fabricated to satisfy it, so the confidence_floor filter
            applies only to real numeric values;
          - confidence below confidence_floor;
          - no schema-valid parent event id: INFERENCE_EVENT lineage must
            reference the real input observations (semantic contract 4.8
            and 11.3); a parent id is never fabricated, so a detection
            without one is refused rather than emitted with invented
            lineage.
        Other invalid value types (for example a string altitude) are left
        to schema validation (ladder step 2) by design.
    """
    # Unwrap envelope if present
    msg_type = detection.get("type", "")
    if msg_type in ("subscribed", "ping", "pong"):
        return None

    payload = detection.get("payload", detection)

    if "class_name" not in payload:
        return None

    # INFERENCE_EVENT schema-requires top-level confidence, and a quality
    # metric is never fabricated to satisfy it: refuse when confidence is
    # absent, null, or non-numeric rather than defaulting. The floor filter
    # below adjudicates real numeric values only.
    confidence = payload.get("confidence")
    if not isinstance(confidence, (int, float)) or isinstance(confidence, bool):
        return None
    if confidence < confidence_floor:
        return None

    # Strip heavyweight fields
    if strip_thumbnail:
        payload.pop("thumbnail", None)
    if strip_embedding:
        payload.pop("embedding", None)

    # Resolve the position source with the existing fallback logic, keeping
    # the vertical inputs separate so the altitude datum can be gated below
    # (contract 6.2, doctrine C1-01).
    gps = payload.get("gps")
    geo_source = "detection"
    position = None  # (lat, lon, alt_hae_m, alt_other_m, preserved_key)

    def _sensor_position():
        # sensor_geo carries the FC/platform GPS position. alt_hae_m is a
        # deployment assertion of WGS-84 HAE (e.g. GPS_RAW_INT.alt_ellipsoid)
        # and is the only vertical that may reach canonical alt_m. The legacy
        # alt_m key is read as MSL: the documented source is a flight
        # controller, whose global-position altitude MAVLink defines as MSL
        # (see adapters/ingress/mavlink/mavlink_to_zmeta_template.py).
        return (
            sensor_geo.get("lat"),
            sensor_geo.get("lon"),
            sensor_geo.get("alt_hae_m"),
            sensor_geo.get("alt_m"),
            "eo_cv_sensor_alt_msl_m",
        )

    if gps and isinstance(gps, (list, tuple)) and len(gps) >= 2:
        lat, lon = gps[0], gps[1]
        if lat == 0 and lon == 0:
            if sensor_geo:
                position = _sensor_position()
                geo_source = "fc_fallback"
            else:
                geo_source = "unavailable"
        else:
            if (
                sensor_geo
                and _geo_distance_m({"lat": lat, "lon": lon}, sensor_geo)
                > _GEO_MAX_SENSOR_DELTA_M
            ):
                position = _sensor_position()
                geo_source = "fc_fallback"
            else:
                # The detection's own vertical: altitude_hae_m is the
                # datum-qualified key; the legacy generic `altitude` key
                # asserts no datum at all and never reaches canonical alt_m.
                position = (
                    lat,
                    lon,
                    payload.get("altitude_hae_m"),
                    payload.get("altitude"),
                    "eo_cv_alt_unspecified_datum_m",
                )
    elif sensor_geo:
        position = _sensor_position()
        geo_source = "fc_fallback"
    else:
        geo_source = "unavailable"

    # Altitude-datum gate plus the all-or-nothing rule (contracts 6.2, 6.8):
    # only a vertical the caller declared HAE occupies canonical alt_m; a
    # vertical under a legacy or unlabeled key yields the declared 2-D form
    # (doctrine A1-02, forced 1.1.0 stamp, since dimensionality is v1.1.0
    # vocabulary) with the value preserved under a datum-named non-canonical
    # quality key; no vertical of any kind omits geo entirely, never
    # zero-filled. Building geo field-by-field here also stops extra caller
    # keys riding into claim.geo, which the old dict(sensor_geo) copy allowed.
    # Invalid value types stay left to schema validation (ladder step 2) by
    # design.
    geo: Dict[str, Any] = {}
    quality: Dict[str, Any] = {}
    needs_1_1_0 = False
    if position is not None:
        lat, lon, alt_hae_m, alt_other_m, preserved_key = position
        if lat is None or lon is None:
            geo_source = "unavailable"
        elif alt_hae_m is not None:
            geo = {"lat": lat, "lon": lon, "alt_m": alt_hae_m}
        elif alt_other_m is not None:
            # The 2-D fact travels in claim.geo.dimensionality alone: the
            # A1-02 geo_status token VERTICAL_UNAVAILABLE is coupled to
            # payload.geo by the adjudicated schema coherence rule (arm 1),
            # and this event's geo is claim-scoped, so asserting the token
            # here would be schema-invalid rather than honest.
            geo = {"lat": lat, "lon": lon, "dimensionality": "2D"}
            needs_1_1_0 = True
            quality[preserved_key] = alt_other_m
        else:
            geo_source = "unavailable"

    claim: Dict[str, Any] = {
        "label": payload.get("class_name", "unknown"),
        "geo_source": geo_source,
    }
    if geo:
        claim["geo"] = geo

    bbox = payload.get("bbox")
    if bbox:
        claim["bbox"] = bbox

    source_object_id = payload.get("track_id")
    if source_object_id is not None:
        claim["source_object_id"] = str(source_object_id)

    stream_id = payload.get("stream_id")

    ts = normalize_utc_z(payload.get("timestamp")) or _utc_now()
    sid = stream_id or DEFAULT_SENSOR_ID

    source_event_id = payload.get("source_event_id")
    if source_event_id:
        claim["source_event_id"] = str(source_event_id)

    if parent_event_ids:
        parents = [str(item) for item in parent_event_ids]
    elif source_event_id and _UUID7_RE.match(str(source_event_id)):
        parents = [str(source_event_id)]
    else:
        parents = []
    if not parents or not all(_UUID7_RE.match(item) for item in parents):
        return None

    payload_out: Dict[str, Any] = {
        "inference_type": "CLASSIFICATION",
        "claim": claim,
        "model": {
            "name": str(payload.get("model_name") or "eo-cv"),
            "version": str(payload.get("model_version") or ADAPTER_VERSION),
        },
        "based_on": parents,
        "timing_quality": coerce_timing_quality(
            payload.get("timing_quality"),
            event_ts=ts,
        ),
    }
    if quality:
        payload_out["quality"] = quality

    return {
        "zmeta_version": "1.1.0" if needs_1_1_0 else "1.0",
        "event": {
            "event_id": str(uuid7()),
            "event_type": "INFERENCE_EVENT",
            "event_subtype": "CLASSIFICATION",
            "ts": ts,
        },
        "source": {
            "platform_id": platform_id,
            "node_role": "GATEWAY",
            "producer": "eo-cv-adapter",
            "sensor_id": sid,
        },
        "payload": payload_out,
        "confidence": confidence,
        "lineage": {
            "based_on": parents,
            "transform": f"translate:{SCHEMA_ID}@{ADAPTER_VERSION}",
        },
    }


def translate_batch(
    messages: List[Dict[str, Any]],
    *,
    platform_id: str,
    sensor_geo: Optional[Dict[str, float]] = None,
    confidence_floor: float = 0.0,
    parent_event_ids: Optional[List[str]] = None,
) -> List[dict]:
    """Translate a batch of CV detection messages into ZMeta events.

    Convenience wrapper that filters None results.

    Returns:
        List of ZMeta event dicts.
    """
    events = []
    for msg in messages:
        evt = translate(
            msg,
            platform_id=platform_id,
            sensor_geo=sensor_geo,
            confidence_floor=confidence_floor,
            parent_event_ids=parent_event_ids,
        )
        if evt is not None:
            events.append(evt)
    return events
