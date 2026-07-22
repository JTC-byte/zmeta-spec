from datetime import datetime

from adapters.ingress.time_utils import coerce_timing_quality, normalize_utc_z, utc_now_z
from zmeta_uuid import uuid7


DEFAULT_VALID_FOR_MS = 5000
PROMOTION_POLICY_ID = "PROMOTE-COT-STATE-V1"


def _iso_now():
    return utc_now_z()


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


def _detail_value(cot, key, default=None):
    if key in cot:
        return cot.get(key)
    detail = cot.get("detail")
    if isinstance(detail, dict) and key in detail:
        return detail.get(key)
    return default


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
    ts = normalize_utc_z(base_ts) or _iso_now()
    valid_for_ms = _compute_valid_for_ms(base_ts, cot.get("stale"))

    confidence = _extract_confidence(cot)
    if confidence is None:
        raise ValueError("cot must include confidence for STATE_EVENT")

    based_on = cot.get("based_on")
    detail = cot.get("detail")
    if based_on is None and isinstance(detail, dict):
        based_on = detail.get("based_on")
    if not based_on:
        raise ValueError("cot must include based_on lineage event ids")

    # The reflection check is a verification this template never performs,
    # so its verdict must arrive message-carried — never self-asserted
    # (contract 4.5.1; same rule the SAPIENT ingress enforces).
    loop_status = _detail_value(cot, "loop_status")
    if not loop_status:
        raise ValueError("cot must carry loop_status (detail.loop_status)")

    source_event_uid = str(_detail_value(cot, "source_event_uid", uid))
    promotion = {
        "state_category": "PROMOTED_EXTERNAL_STATE",
        "origin_kind": str(_detail_value(cot, "origin_kind", "EXTERNAL_REPORT")),
        "projection_id": "cot",
        "promotion_policy_id": str(_detail_value(cot, "promotion_policy_id", PROMOTION_POLICY_ID)),
        "trust_ref": str(_detail_value(cot, "trust_ref", "producer-authority:cot-ingress")),
        "lineage_status": str(_detail_value(cot, "lineage_status", "EXTERNAL_SOURCE")),
        "loop_status": str(loop_status),
        "confidence_basis": str(
            _detail_value(cot, "confidence_basis", "EXPLICIT_EXTERNAL_CONFIDENCE")
        ),
        "source_event_uid": source_event_uid,
        "freshness_ms": valid_for_ms,
    }
    source_zmeta_event_id = _detail_value(cot, "source_zmeta_event_id")
    if source_zmeta_event_id:
        promotion["source_zmeta_event_id"] = str(source_zmeta_event_id)

    payload = {
        "track_id": str(uid),
        "geo": {"lat": lat, "lon": lon, "alt_m": hae},
        "valid_for_ms": valid_for_ms,
        "timing_quality": coerce_timing_quality(cot.get("timing_quality"), event_ts=ts),
        "extensions": {"external_promotion": promotion},
    }
    cot_type = cot.get("type")
    if cot_type:
        payload["class"] = str(cot_type)

    event_id = str(uuid7())
    event = {
        "zmeta_version": "1.0",
        "event": {
            "event_id": event_id,
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
        "confidence": confidence,
        "lineage": {
            "based_on": [str(item) for item in based_on],
            "transform": f"promote:cot@template:{promotion['promotion_policy_id']}",
        },
    }

    return event
