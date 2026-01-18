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


def _compute_valid_for_ms(ts, stale_ts):
    ts_dt = _parse_ts(ts)
    stale_dt = _parse_ts(stale_ts)
    if ts_dt and stale_dt:
        delta_ms = int((stale_dt - ts_dt).total_seconds() * 1000)
        if delta_ms > 0:
            return delta_ms
    return DEFAULT_VALID_FOR_MS


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

    ts = track.get("timestamp") or track.get("time") or track.get("ts") or _iso_now()
    valid_for_ms = _compute_valid_for_ms(ts, track.get("stale_time") or track.get("stale"))

    payload = {
        "track_id": str(track_id),
        "geo": {"lat": lat, "lon": lon, "alt_m": hae_m},
        "valid_for_ms": valid_for_ms,
    }
    track_type = track.get("track_type")
    if track_type:
        payload["class"] = str(track_type)

    event = {
        "zmeta_version": "1.0",
        "event": {
            "event_id": str(uuid.uuid4()),
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
        "lineage": {"based_on": [], "transform": "translate:jreap@template"},
    }

    if "confidence" in track and track["confidence"] is not None:
        event["confidence"] = track["confidence"]

    return event
