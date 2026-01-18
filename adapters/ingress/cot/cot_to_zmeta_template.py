import uuid
from datetime import datetime, timezone


DEFAULT_VALID_FOR_MS = 5000


def _iso_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_ts(value):
    if not value or not isinstance(value, str):
        return None
    if value.endswith("Z"):
        value = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _compute_valid_for_ms(start_ts, stale_ts):
    start_dt = _parse_ts(start_ts)
    stale_dt = _parse_ts(stale_ts)
    if start_dt and stale_dt:
        delta_ms = int((stale_dt - start_dt).total_seconds() * 1000)
        if delta_ms > 0:
            return delta_ms
    return DEFAULT_VALID_FOR_MS


def _extract_confidence(cot):
    if "confidence" in cot:
        return cot["confidence"]
    detail = cot.get("detail")
    if isinstance(detail, dict) and "confidence" in detail:
        return detail["confidence"]
    return None


def cot_dict_to_zmeta_track_state(cot: dict) -> dict:
    """
    Template: Convert a parsed CoT dict into a ZMeta TRACK_STATE event.
    """
    if not isinstance(cot, dict):
        raise ValueError("cot must be a dict")

    uid = cot.get("uid") or cot.get("id") or "cot-unknown"
    point = cot.get("point") or {}
    lat = point.get("lat")
    lon = point.get("lon")
    hae = point.get("hae")
    if lat is None or lon is None or hae is None:
        raise ValueError("cot point must include lat/lon/hae")

    base_ts = cot.get("time") or cot.get("start")
    ts = base_ts or _iso_now()
    valid_for_ms = _compute_valid_for_ms(base_ts, cot.get("stale"))

    payload = {
        "track_id": str(uid),
        "geo": {"lat": lat, "lon": lon, "alt_m": hae},
        "valid_for_ms": valid_for_ms,
    }
    cot_type = cot.get("type")
    if cot_type:
        payload["class"] = str(cot_type)

    event = {
        "zmeta_version": "1.0",
        "event": {
            "event_id": str(uuid.uuid4()),
            "event_type": "STATE_EVENT",
            "event_subtype": "TRACK_STATE",
            "ts": ts,
        },
        "source": {
            "platform_id": str(cot.get("platform_id") or uid),
            "node_role": "GATEWAY",
            "producer": str(cot.get("producer") or "cot-ingress"),
        },
        "payload": payload,
        "lineage": {"based_on": [], "transform": "translate:cot@template"},
    }

    confidence = _extract_confidence(cot)
    if confidence is not None:
        event["confidence"] = confidence

    return event
