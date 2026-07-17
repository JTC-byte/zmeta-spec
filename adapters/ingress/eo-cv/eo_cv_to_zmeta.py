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
    - altitude (float): altitude in metres. Canonical geo is
      all-or-nothing (contract 6.8), so a detection position without an
      altitude yields no ``claim.geo`` — never a zero-filled ``alt_m``.
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
_GEO_KEYS = ("lat", "lon", "alt_m")


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

    Canonical geo is all-or-nothing (contract 6.8): a resolved position
    missing any of lat, lon, or alt_m — for example a detection GPS with
    no altitude — is never zero-filled; ``claim.geo`` is omitted entirely
    and geo_source is set to "unavailable".

    Args:
        detection: Raw detection dict. Supports both wrapped envelope
            ({"type": "detection", "payload": {...}}) and flat format.
        platform_id: Platform identifier string.
        sensor_geo: Optional FC/platform GPS position {lat, lon, alt_m}.
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

    # Resolve geo position with fallback logic
    gps = payload.get("gps")
    altitude = payload.get("altitude")
    geo: Dict[str, Any]
    geo_source = "detection"

    if gps and isinstance(gps, (list, tuple)) and len(gps) >= 2:
        lat, lon = gps[0], gps[1]
        if lat == 0 and lon == 0:
            if sensor_geo:
                geo = dict(sensor_geo)
                geo_source = "fc_fallback"
            else:
                geo = {}
                geo_source = "unavailable"
        else:
            detection_geo = {"lat": lat, "lon": lon, "alt_m": altitude}
            if (
                sensor_geo
                and _geo_distance_m(detection_geo, sensor_geo) > _GEO_MAX_SENSOR_DELTA_M
            ):
                geo = dict(sensor_geo)
                geo_source = "fc_fallback"
            else:
                geo = detection_geo
    elif sensor_geo:
        geo = dict(sensor_geo)
        geo_source = "fc_fallback"
    else:
        geo = {}
        geo_source = "unavailable"

    # Canonical geo is all-or-nothing (contract 6.8): if any of lat, lon,
    # or alt_m is missing, omit geo entirely — never zero-fill.
    if geo and any(geo.get(key) is None for key in _GEO_KEYS):
        geo = {}
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

    return {
        "zmeta_version": "1.0",
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
        "payload": {
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
        },
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
