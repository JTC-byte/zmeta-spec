import copy
import math
from collections.abc import Mapping, Sequence
from collections.abc import Set as AbstractSet
from datetime import datetime, timezone
from decimal import Decimal

# Text leaves are Sequences, so they have to be excluded before the Sequence
# branch or every string becomes a walk over its own characters - and a
# one-character string yields itself, so that walk never terminates.
_TEXT_LEAF_TYPES = (str, bytes, bytearray)

# Canonical altitude field names a COMMAND_EVENT must never carry (semantics
# contract 7.8). COMMAND_EVENT SHALL NOT specify altitude - the receiving
# autonomy/drone deconflicts vertical internally. This egress guard rejects a
# command whose projected geometry (target_geo, geometry) carries an altitude
# field at any depth within those objects, so no vertical intent reaches the
# mission-intent output. The authoritative, whole-payload altitude gate is the
# gateway validator (COMMAND_HAS_ALTITUDE); this set is kept a superset of, and
# in sync with, policy/semantics.yaml command_event.payload_must_not_contain.
_ALTITUDE_FIELDS = frozenset({
    "alt", "alt_m", "altitude", "altitude_m", "alt_hae_m", "alt_msl_m",
    "agl_m", "target_alt_m", "target_altitude",
})


def _walk_containers(root):
    """Yield every value reachable from `root`, once per distinct container.

    Shared by both guards below so neither can drift back to the narrower
    traversal the other has. Iterative with a seen-set for the reason both
    guards were written iterative in the first place: geometry is copied
    verbatim from the payload, so sender-controlled nesting must be a memory
    cost, never a RecursionError - and CBOR value-sharing tags make the
    decoded structure possibly cyclic, so an unbounded walk would be a hang
    (R1-11 R2-07).

    Container coverage is by abstract type, not by dict/list: the gateway's
    cbor2 fallback backend decodes CBOR tag 258 into a `set`, a map used as a
    map key into a Mapping that is not a dict, and an unrecognised tag into a
    tag object whose `.value` still reaches the wire. A dict/list-only walk
    sees none of them.
    """
    stack = [root]
    seen = set()
    while stack:
        current = stack.pop()
        yield current
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


def _contains_altitude(value):
    # Contract 7.8: COMMAND_EVENT SHALL NOT specify altitude. This is
    # defence in depth behind the gateway's COMMAND_HAS_ALTITUDE validator,
    # so its failure mode matters: the recursive dict/list version raised
    # RecursionError on deep geometry (a crash where the documented signal is
    # None/ValueError) and never looked inside a Mapping that is not a dict,
    # a tuple, a set or a CBOR tag wrapper - so an altitude key one container
    # off the beaten path reached an autonomy stack unremarked.
    for current in _walk_containers(value):
        if isinstance(current, Mapping):
            for key in current:
                # strip+casefold so whitespace-/case-padded altitude keys
                # cannot slip the guard (matches the gateway validator's key
                # normalization).
                if str(key).strip().casefold() in _ALTITUDE_FIELDS:
                    return True
    return False


def _has_non_finite(value):
    # Value scoped, not field scoped: NaN/inf anywhere in the projected
    # mission is a number that is not a number, and a per-field list only
    # closes the fields someone thought of (R1-11 A-01). geometry is copied
    # verbatim from the payload, so a vertex deep inside it is reachable.
    # float and Decimal are the only decoded types that can be non-finite; a
    # Python int is never converted, because math.isfinite() on an int
    # outside float64 range raises OverflowError, which would trade this
    # guard for a crash.
    for current in _walk_containers(value):
        if isinstance(current, float) and not math.isfinite(current):
            return True
        if isinstance(current, Decimal) and not current.is_finite():
            return True
    return False


def _risk_adjudication_records(payload):
    """Read the gateway's own soft-acceptance stamp,
    payload.extensions.risk_adjudication (gateway/src/validators.py
    _append_risk_adjudication, docstring: "warn forwards the command
    unmodified beside its diagnostic ... degrade additionally stamps the
    command's own payload.extensions.risk_adjudication"). A non-empty list
    there is written only onto a command the gateway did NOT forward clean,
    so its mere presence is the soft flag - independent of which use tokens
    the records carry.

    Returns the record list to refuse on (and, under the caller's opt-in, to
    stamp into MissionIntent), or None when nothing was ever stamped. A
    field present but not the documented list shape is unreadable, and
    reading it as "no flag" would be the exact laundering the gateway's own
    UNADJUDICABLE_RISK_SHAPE convention exists to prevent, so it fails
    closed as a flag with no readable records ([]).
    """
    if not isinstance(payload, Mapping):
        return None
    extensions = payload.get("extensions")
    if not isinstance(extensions, Mapping):
        return None
    records = extensions.get("risk_adjudication")
    if records is None:
        return None
    if isinstance(records, list):
        return records if records else None
    return []


def _parse_utc(ts):
    # A copy of the SAPIENT command egress's reader, _parse_utc in
    # adapters/egress/sapient/zmeta_command_to_sapient_task.py. The adapters
    # do not import each other, so the reader is copied, and
    # test_mavlink_intent.py holds the two egresses to the same refusals of
    # a validity window. A change to one copy belongs in the other.
    if not isinstance(ts, str):
        # TypeError so the caller's documented None-refusal path handles a
        # non-string ts; bare .endswith would raise AttributeError past it.
        raise TypeError(f"ts must be a string, got {type(ts).__name__}")
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    parsed = datetime.fromisoformat(ts)
    if parsed.tzinfo is None:
        # Gate-clean does not mean offset-carrying: "1969-12-31Z" and
        # "2026-W01-1Z" satisfy the schema's `Z$` pattern yet parse NAIVE,
        # and `.astimezone()` on a naive datetime asks the PLATFORM -
        # silent host-local reinterpretation (a fabricated instant) or
        # OSError pre-epoch on Windows. ValueError so the caller's
        # documented None-refusal path handles it (same closure as the
        # CoT/JREAP siblings, 2026-07-27).
        raise ValueError(f"ts parses without a UTC offset: {ts!r}")
    return parsed.astimezone(timezone.utc)


def zmeta_command_to_mission_intent(event, allow_flagged=False):
    """
    Convert a ZMeta COMMAND_EVENT to a MissionIntent dict.
    Returns None if the input is not a COMMAND_EVENT or missing required fields.
    Also returns None for a command whose validity window the intent cannot
    hand on (contract 7.8; see the check before the return): a
    payload.valid_from_ts later than event.ts, a valid_from_ts this egress
    cannot read, or a valid_from_ts beside an event.ts that is absent or
    cannot be read. A command without valid_from_ts is translated as before.

    Fail-closed by default: a COMMAND_EVENT carrying a gateway-stamped
    payload.extensions.risk_adjudication record (a soft-accepted command,
    warn/degrade disposition - see _risk_adjudication_records) is refused,
    the same None signal as every other refusal in this module. Passing
    allow_flagged=True is an explicit opt-in that translates the command
    anyway and stamps the risk_adjudication records into the MissionIntent
    output, so the operator who wires their own autonomy on this stream
    still sees what the gateway flagged rather than it vanishing at
    translation.
    """
    if event.get("event", {}).get("event_type") != "COMMAND_EVENT":
        return None

    payload = event.get("payload", {})
    target_geo = payload.get("target_geo")

    task_id = payload.get("task_id")
    task_type = payload.get("task_type")
    valid_for_ms = payload.get("valid_for_ms")
    requires_deconfliction = payload.get("requires_deconfliction")

    if not task_id or not task_type or valid_for_ms is None or requires_deconfliction is None:
        return None

    if requires_deconfliction is not True:
        return None

    risk_records = _risk_adjudication_records(payload)
    if risk_records is not None and not allow_flagged:
        return None

    target_lat = None
    target_lon = None
    if target_geo is not None:
        if _contains_altitude(target_geo):
            raise ValueError("target_geo must be 2D (lat/lon only)")
        target_lat = target_geo.get("lat")
        target_lon = target_geo.get("lon")
        if target_lat is None or target_lon is None:
            return None

    mission = {
        "task_id": task_id,
        "task_type": task_type,
        "valid_for_ms": valid_for_ms,
        "requires_deconfliction": True,
    }
    # priority is OPTIONAL with no declared default: an omitted priority is
    # the absence of a priority claim, so it projects as an absent key - never
    # a fabricated MED reaching an autonomy consumer clean (R1-11 CR-08). Map
    # only what is present.
    priority = payload.get("priority")
    if priority is not None:
        mission["priority"] = priority
    if target_lat is not None and target_lon is not None:
        mission["target_lat"] = target_lat
        mission["target_lon"] = target_lon

    geometry = payload.get("geometry")
    if geometry is not None:
        if _contains_altitude(geometry):
            raise ValueError("command geometry must not include altitude")
        mission["geometry"] = geometry

    # allow_flagged is the explicit override for a command the gateway did
    # not forward clean (see _risk_adjudication_records above): stamp what
    # was flagged into the output rather than let it vanish at translation.
    # Deep-copied so the returned mission shares no mutable state with the
    # input event's payload.
    if risk_records is not None and allow_flagged:
        mission["risk_adjudication"] = copy.deepcopy(risk_records)

    # Refuse rather than hand an autonomy stack a waypoint, boundary vertex or
    # duration that is NaN/inf. This is the sharpest end of the class: a
    # non-finite target is a fly-to command with no destination, and it
    # validates against every structural check above (R1-11 A-01).
    if _has_non_finite(mission):
        return None

    # The altitude walk covers the whole built mission, mirroring the
    # _has_non_finite placement above, so the verbatim-copy paths
    # (risk_adjudication records, geometry contents beyond the top-level
    # walk) share the same guarantee as target_geo: no vertical intent
    # reaches the mission-intent output (contract 7.8 forbids altitude
    # fields anywhere in a command payload, extensions included). The
    # gateway's whole-payload COMMAND_HAS_ALTITUDE gate is the authoritative
    # screen; this module documents itself as defence-in-depth for the
    # direct-wired case, and until this walk existed the copied records were
    # the one conduit that guarantee did not cover.
    if _contains_altitude(mission):
        raise ValueError("mission intent must not carry altitude fields")

    # Contract 7.8: a command's validity window begins at
    # payload.valid_from_ts when present, otherwise at event.ts, and ends
    # valid_for_ms after that start. The intent carries valid_for_ms and no
    # anchor, so a receiver can only start the duration at receipt, and a
    # window that opens after event.ts would start before it opens. Such a
    # command is refused (None) by the SAPIENT sibling's rule: the
    # comparison is strict, so a start equal to event.ts goes out. A
    # valid_from_ts this egress cannot read, or one beside an event.ts it
    # cannot read, is a window it cannot place, refused the same way. A
    # command without valid_from_ts reads no time and goes out as before,
    # and no clock is read. A window that opened at or before event.ts goes
    # out with valid_for_ms and no anchor, a window that closed before
    # event.ts included. The check runs last, so a command that raises above
    # still raises.
    valid_from_ts = payload.get("valid_from_ts")
    if valid_from_ts is not None:
        try:
            start_dt = _parse_utc(valid_from_ts)
            time_dt = _parse_utc(event.get("event", {}).get("ts"))
        except (ValueError, TypeError, OverflowError, OSError):
            return None
        if start_dt > time_dt:
            return None

    return mission
