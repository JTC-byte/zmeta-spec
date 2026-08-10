import math
from collections.abc import Mapping, Sequence
from collections.abc import Set as AbstractSet
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

    Value scoped, not field scoped: NaN/inf anywhere in the projected tag
    dict is a number that is not a number, and a per-field list only closes
    the fields someone thought of (R1-11 A-01). `payload.features` is copied
    wholesale, so the reachable shapes are whatever the decoder produced.

    Container coverage is by abstract type, not by dict/list: the gateway's
    cbor2 fallback backend decodes CBOR tag 258 into a `set`, a map used as a
    map key into a Mapping that is not a dict, an unrecognised tag into a tag
    object whose `.value` still reaches the wire, and tag 4/5 into a Decimal
    that carries its own NaN. The dict/list-only version of this walk saw
    none of them (R1-11 R2-07).

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


def zmeta_observation_to_klv_tagdict(event: dict) -> dict | None:
    """
    Template: Convert ZMeta OBSERVATION_EVENT into a decoded KLV tag dict.

    Altitude datum at the handoff (contract 6.2): the output's geo.alt_m is
    WGS-84 HAE, copied unconverted from canonical payload.geo. An MISB ST
    0601 embedder must map it to an HAE-defined tag (Tag 75 Sensor Ellipsoid
    Height, or Tag 78 for a frame-center referent), never to the MSL-defined
    Tag 15 / Tag 25 / Tag 42 without an explicit geoid conversion, which
    this template does not ship. features values stay source-native and
    carry no such guarantee. See the README for the full disposition.
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
