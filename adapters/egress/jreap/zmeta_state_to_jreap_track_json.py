import math
from datetime import datetime, timedelta, timezone


def _has_non_finite(value):
    # Value scoped, not field scoped: NaN/inf anywhere in the projected track
    # is a number that is not a number, and a per-field list only closes the
    # fields someone thought of (R1-11 A-01). Iterative so sender-controlled
    # nesting is a memory cost, never a RecursionError.
    stack = [value]
    while stack:
        current = stack.pop()
        if isinstance(current, float) and not math.isfinite(current):
            return True
        if isinstance(current, dict):
            stack.extend(current.keys())
            stack.extend(current.values())
        elif isinstance(current, (list, tuple)):
            stack.extend(current)
    return False


def _parse_utc(ts):
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    return datetime.fromisoformat(ts).astimezone(timezone.utc)


def zmeta_state_to_jreap_track_json(event):
    """
    Convert a ZMeta STATE_EVENT/TRACK_STATE into a minimal tactical track JSON.
    Returns None if the input is not applicable.
    """
    if event.get("event", {}).get("event_type") != "STATE_EVENT":
        return None
    if event.get("event", {}).get("event_subtype") != "TRACK_STATE":
        return None

    payload = event.get("payload", {})
    geo = payload.get("geo", {})
    track_id = payload.get("track_id")
    ts = event.get("event", {}).get("ts")
    valid_for_ms = payload.get("valid_for_ms")

    if not track_id or not geo or not ts or valid_for_ms is None:
        return None

    time_dt = _parse_utc(ts)
    stale_dt = time_dt + timedelta(milliseconds=int(valid_for_ms))

    track = {
        "track_id": track_id,
        "lat": geo.get("lat"),
        "lon": geo.get("lon"),
        "hae_m": geo.get("alt_m"),
        "timestamp": time_dt.isoformat().replace("+00:00", "Z"),
        "stale_time": stale_dt.isoformat().replace("+00:00", "Z"),
        "track_type": payload.get("class") or "UNKNOWN",
    }

    if event.get("confidence") is not None:
        track["confidence"] = event.get("confidence")

    # Refuse rather than project a track position, altitude or confidence that
    # is NaN/inf: the consumer would plot a symbol at a non-position, and the
    # JSON it is handed is not RFC 8259 so a non-Python decoder rejects the
    # whole message instead. Checked on the built output so no field can be
    # added later without inheriting the guard.
    if _has_non_finite(track):
        return None

    return track
