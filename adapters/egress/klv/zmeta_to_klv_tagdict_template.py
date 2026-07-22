import math


def _has_non_finite(value):
    # Value scoped, not field scoped: NaN/inf anywhere in the projected tag
    # dict is a number that is not a number, and a per-field list only closes
    # the fields someone thought of (R1-11 A-01). Iterative so
    # sender-controlled nesting is a memory cost, never a RecursionError.
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


def zmeta_observation_to_klv_tagdict(event: dict) -> dict | None:
    """
    Template: Convert ZMeta OBSERVATION_EVENT into a decoded KLV tag dict.
    """
    if not isinstance(event, dict):
        raise ValueError("event must be a dict")

    event_block = event.get("event") or {}
    if event_block.get("event_type") != "OBSERVATION_EVENT":
        return None

    source = event.get("source") or {}
    payload = event.get("payload") or {}

    tagdict = {
        "timestamp": event_block.get("ts"),
        "platform_id": source.get("platform_id"),
        "sensor_id": source.get("sensor_id"),
        "geo": payload.get("geo"),
        "features": payload.get("features", {}),
    }

    tagdict = {k: v for k, v in tagdict.items() if v is not None}

    # Refuse rather than emit a sensor footprint or feature measurement that
    # is NaN/inf. geo and features are copied wholesale from the payload, so
    # the check is on the built output rather than a field list (R1-11 A-01).
    if _has_non_finite(tagdict):
        return None

    return tagdict
