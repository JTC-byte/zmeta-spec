"""EO (Computer Vision) detection to ZMeta OBSERVATION_EVENT translator.

Translates CV inference service JSON detections into ZMeta EO
OBSERVATION_EVENTs. Handles GPS destructuring, confidence filtering,
sensor geo fallback, and plausibility checks.

Input format:
  JSON from a CV inference service. Two envelope styles supported:
    - Wrapped:  {"type": "detection", "payload": {...detection...}}
    - Flat:     {...detection...}

  Required detection fields:
    - class_name (str): detected object class
    - confidence (float): detection confidence 0.0-1.0

  Optional detection fields:
    - gps ([lat, lon]): detection position array
    - altitude (float): altitude in metres
    - bbox ([x1, y1, x2, y2]): bounding box in image coordinates
    - track_id (str|int): object tracker ID
    - stream_id (str): camera/stream identifier
    - timestamp (str): ISO 8601 timestamp

Source: Z-ISR edge/edge/sensors/eo_consumer.py and edge/edge/zmeta_builder.py
"""

import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from zmeta_uuid import uuid7

ADAPTER_VERSION = "1.0.0"
SCHEMA_ID = "eo-cv-detection"
DEFAULT_SENSOR_ID = "eo_camera"

_GEO_MAX_SENSOR_DELTA_M = 10000.0


def _utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


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
) -> Optional[dict]:
    """Translate a CV detection JSON into a ZMeta EO OBSERVATION_EVENT.

    Handles the full GPS resolution logic from the Z-ISR edge:
      1. If detection has GPS [lat, lon] and it's not (0, 0) sentinel,
         use it as the geo position.
      2. If detection GPS is (0, 0) or missing, fall back to sensor_geo
         (e.g. from flight controller).
      3. If detection GPS is implausibly far from sensor_geo (>10km),
         fall back to sensor_geo.
      4. If neither is available, use (0, 0, 0) with geo_source="unavailable".

    Args:
        detection: Raw detection dict. Supports both wrapped envelope
            ({"type": "detection", "payload": {...}}) and flat format.
        platform_id: Platform identifier string.
        sensor_geo: Optional FC/platform GPS position {lat, lon, alt_m}.
        confidence_floor: Minimum confidence to accept (default 0.0).
        strip_thumbnail: Remove heavyweight thumbnail field (default True).
        strip_embedding: Remove heavyweight embedding field (default True).

    Returns:
        ZMeta event dict, or None if detection is invalid or below threshold.
    """
    # Unwrap envelope if present
    msg_type = detection.get("type", "")
    if msg_type in ("subscribed", "ping", "pong"):
        return None

    payload = detection.get("payload", detection)

    if "class_name" not in payload:
        return None

    confidence = payload.get("confidence", 0.0)
    if confidence < confidence_floor:
        return None

    # Strip heavyweight fields
    if strip_thumbnail:
        payload.pop("thumbnail", None)
    if strip_embedding:
        payload.pop("embedding", None)

    # Resolve geo position with fallback logic
    gps = payload.get("gps")
    altitude = payload.get("altitude", 0.0)
    geo: Dict[str, Any]
    geo_source = "detection"

    if gps and isinstance(gps, (list, tuple)) and len(gps) >= 2:
        lat, lon = gps[0], gps[1]
        if lat == 0 and lon == 0:
            if sensor_geo:
                geo = dict(sensor_geo)
                geo_source = "fc_fallback"
            else:
                geo = {"lat": 0.0, "lon": 0.0, "alt_m": 0.0}
                geo_source = "unavailable"
        else:
            detection_geo = {"lat": lat, "lon": lon, "alt_m": altitude or 0.0}
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
        geo = {"lat": 0.0, "lon": 0.0, "alt_m": 0.0}
        geo_source = "unavailable"

    features: Dict[str, Any] = {
        "class_name": payload.get("class_name", "unknown"),
        "confidence": confidence,
        "geo_source": geo_source,
    }

    bbox = payload.get("bbox")
    if bbox:
        features["bbox"] = bbox

    track_id = payload.get("track_id")
    if track_id is not None:
        features["track_id"] = str(track_id)

    stream_id = payload.get("stream_id")
    if stream_id:
        features["sensor_id"] = stream_id

    if sensor_geo:
        features["sensor_geo"] = sensor_geo

    ts = payload.get("timestamp", _utc_now())
    sid = stream_id or DEFAULT_SENSOR_ID

    return {
        "zmeta_version": "1.0",
        "event": {
            "event_id": str(uuid7()),
            "event_type": "OBSERVATION_EVENT",
            "event_subtype": "EO_DETECTION",
            "ts": ts,
        },
        "source": {
            "platform_id": platform_id,
            "node_role": "EDGE",
            "producer": "eo-cv-adapter",
            "sensor_id": sid,
        },
        "payload": {
            "modality": "EO",
            "geo": geo,
            "features": features,
        },
        "lineage": {
            "based_on": [str(uuid7())],
            "transform": f"translate:{SCHEMA_ID}@{ADAPTER_VERSION}",
        },
    }


def translate_batch(
    messages: List[Dict[str, Any]],
    *,
    platform_id: str,
    sensor_geo: Optional[Dict[str, float]] = None,
    confidence_floor: float = 0.0,
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
        )
        if evt is not None:
            events.append(evt)
    return events
