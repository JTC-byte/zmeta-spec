import math
from collections.abc import Mapping, Sequence
from collections.abc import Set as AbstractSet
from datetime import datetime, timedelta, timezone
from decimal import Decimal

# Text leaves are Sequences, so they have to be excluded before the Sequence
# branch or every string becomes a walk over its own characters - and a
# one-character string yields itself, so that walk never terminates.
_TEXT_LEAF_TYPES = (str, bytes, bytearray)


def _is_non_finite(value):
    # float and Decimal are the only decoded types that can be non-finite. A
    # Python int is never converted: math.isfinite() on an int outside float64
    # range raises OverflowError, which would trade this guard for a crash.
    if isinstance(value, float):
        return not math.isfinite(value)
    if isinstance(value, Decimal):
        return not value.is_finite()
    return False


def _has_non_finite(value):
    """True when NaN/inf appears anywhere inside `value`.

    Value scoped, not field scoped: NaN/inf anywhere in the projected track
    is a number that is not a number, and a per-field list only closes the
    fields someone thought of (R1-11 A-01).

    Container coverage is by abstract type, not by dict/list: the gateway's
    cbor2 fallback backend decodes CBOR tag 258 into a `set`, a map used as a
    map key into a Mapping that is not a dict, an unrecognised tag into a tag
    object whose `.value` still reaches the wire, and tag 4/5 into a Decimal
    that carries its own NaN. The dict/list-only version of this walk saw
    none of them (R1-11 R2-07); the CoT sibling already carried this shape,
    so the three remaining egress walks are brought to it rather than left as
    the degraded copy.

    Iterative, with a seen-set: recursing would tie the process stack to
    sender-controlled nesting depth, and CBOR value-sharing tags make the
    decoded structure possibly cyclic, so an unbounded walk here would be a
    hang on the egress path rather than the RecursionError it was written to
    avoid.
    """
    stack = [value]
    seen = set()
    while stack:
        current = stack.pop()
        if _is_non_finite(current):
            return True
        if isinstance(current, _TEXT_LEAF_TYPES):
            continue
        if isinstance(current, (Mapping, AbstractSet, Sequence)) or (
            hasattr(current, "tag") and hasattr(current, "value")
        ):
            marker = id(current)
            if marker in seen:
                continue
            seen.add(marker)
        if isinstance(current, Mapping):
            stack.extend(current.keys())
            stack.extend(current.values())
        elif isinstance(current, (AbstractSet, Sequence)):
            stack.extend(current)
        elif hasattr(current, "tag") and hasattr(current, "value"):
            stack.append(current.value)
    return False


def _parse_utc(ts):
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    return datetime.fromisoformat(ts).astimezone(timezone.utc)


def _stale_time(time_dt, valid_for_ms):
    """`time_dt + valid_for_ms` as a datetime, or None when unrepresentable.

    Same class as the CoT sibling (R1-11 R2-05), reached through the same
    unbounded `{"type": "integer", "minimum": 1}` schema: `10**400` ms raises
    OverflowError "Python int too large to convert to C int", `10**15` ms and
    an ordinary 300000 ms window on `ts="9999-12-31T23:59:59Z"` both raise
    OverflowError "date value out of range".

    JREAP carries one extra arm the CoT sibling does not: the `int()`
    coercion ran BEFORE the non-finite guard below, so a non-finite
    `valid_for_ms` raised ValueError/OverflowError out of the adapter instead
    of reaching the guard written to refuse it. Both coercion and addition
    are inside the same guarded expression now, so the ordering cannot
    regress.

    Refusal, not substitution: `stale_time` is the consumer's freshness
    bound, and the adapter has no honest value to put there for a window it
    cannot express. None is this adapter's documented "not applicable"
    signal.
    """
    try:
        return time_dt + timedelta(milliseconds=int(valid_for_ms))
    except (OverflowError, ValueError, TypeError):
        return None


def zmeta_state_to_jreap_track_json(event):
    """
    Convert a ZMeta STATE_EVENT/TRACK_STATE into a minimal tactical track JSON.
    Returns None if the input is not applicable: wrong event type/subtype,
    missing track_id/geo/ts/valid_for_ms, a validity window whose stale
    timestamp is not representable (see _stale_time), or any non-finite
    (NaN/inf) number in the projected track.
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
    stale_dt = _stale_time(time_dt, valid_for_ms)
    if stale_dt is None:
        return None

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
