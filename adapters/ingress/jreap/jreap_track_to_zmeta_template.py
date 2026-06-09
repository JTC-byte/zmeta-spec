from datetime import datetime

from adapters.ingress.time_utils import coerce_timing_quality, normalize_utc_z, utc_now_z
from zmeta_uuid import uuid7


DEFAULT_VALID_FOR_MS = 5000
PROMOTION_POLICY_ID = "PROMOTE-JREAP-STATE-V1"


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


def _compute_valid_for_ms(ts, stale_ts):
    ts_dt = _parse_ts(ts)
    stale_dt = _parse_ts(stale_ts)
    if ts_dt and stale_dt:
        delta_ms = int((stale_dt - ts_dt).total_seconds() * 1000)
        if delta_ms > 0:
            return delta_ms
    return DEFAULT_VALID_FOR_MS


def _detail_value(track, key, default=None):
    if key in track:
        return track.get(key)
    detail = track.get("detail")
    if isinstance(detail, dict) and key in detail:
        return detail.get(key)
    return default


def jreap_track_dict_to_zmeta_track_state(track: dict) -> dict:
    """
    Template: Convert a decoded JREAP-like track dict into a ZMeta TRACK_STATE event.
    """
    if not isinstance(track, dict):
        raise ValueError("track must be a dict")

    track_id = track.get("track_id") or track.get("id") or track.get("uid")
    if not track_id:
        raise ValueError("track_id is required")

    lat = track.get("lat")
    lon = track.get("lon")
    hae_m = track.get("hae_m")
    if hae_m is None:
        hae_m = track.get("alt_m")
    if lat is None or lon is None or hae_m is None:
        raise ValueError("track must include lat/lon/hae_m")

    base_ts = track.get("timestamp") or track.get("time") or track.get("ts")
    ts = normalize_utc_z(base_ts) or _iso_now()
    valid_for_ms = _compute_valid_for_ms(ts, track.get("stale_time") or track.get("stale"))

    confidence = track.get("confidence")
    if confidence is None:
        raise ValueError("track must include confidence")

    based_on = track.get("based_on") or track.get("lineage")
    if not based_on:
        raise ValueError("track must include based_on lineage event ids")

    source_event_uid = str(_detail_value(track, "source_event_uid", track_id))
    promotion = {
        "state_category": "PROMOTED_EXTERNAL_STATE",
        "origin_kind": str(_detail_value(track, "origin_kind", "EXTERNAL_REPORT")),
        "projection_id": "jreap",
        "promotion_policy_id": str(_detail_value(track, "promotion_policy_id", PROMOTION_POLICY_ID)),
        "trust_ref": str(_detail_value(track, "trust_ref", "producer-authority:jreap-ingress")),
        "lineage_status": str(_detail_value(track, "lineage_status", "EXTERNAL_SOURCE")),
        "loop_status": str(_detail_value(track, "loop_status", "CHECKED_NOT_REFLECTION")),
        "confidence_basis": str(
            _detail_value(track, "confidence_basis", "EXPLICIT_EXTERNAL_CONFIDENCE")
        ),
        "source_event_uid": source_event_uid,
        "freshness_ms": valid_for_ms,
    }
    source_zmeta_event_id = _detail_value(track, "source_zmeta_event_id")
    if source_zmeta_event_id:
        promotion["source_zmeta_event_id"] = str(source_zmeta_event_id)

    payload = {
        "track_id": str(track_id),
        "geo": {"lat": lat, "lon": lon, "alt_m": hae_m},
        "valid_for_ms": valid_for_ms,
        "timing_quality": coerce_timing_quality(track.get("timing_quality"), event_ts=ts),
        "extensions": {"external_promotion": promotion},
    }
    track_type = track.get("track_type")
    if track_type:
        payload["class"] = str(track_type)

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
            "platform_id": str(track.get("platform_id") or track_id),
            "node_role": "GATEWAY",
            "producer": str(track.get("producer") or "jreap-ingress"),
        },
        "payload": payload,
        "confidence": confidence,
        "lineage": {
            "based_on": [str(item) for item in based_on],
            "transform": f"promote:jreap@template:{promotion['promotion_policy_id']}",
        },
    }

    return event
