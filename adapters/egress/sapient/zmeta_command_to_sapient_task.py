"""ZMeta COMMAND_EVENT to SAPIENT (BSI Flex 335 v2.0) Task egress adapter.

Produces a plain dict shaped like a proto3-JSON SapientMessage carrying a
Task. Wire protobuf encoding is out of scope — a downstream SAPIENT
transport encodes the dict (consistent with the JREAP/KLV egress
projections).

Only three ZMeta task types have an honest SAPIENT Task.Command verb:

  GOTO               -> command.move_to (single 2D Location, never a z)
  TRACK_TARGET       -> command.follow (via the caller's track->object map)
  CHANGE_SENSOR_MODE -> command.mode_change

Every other task type (ORBIT, HOLD, SEARCH_BOX, LOITER, SCAN_RF,
RETURN_TO_BASE, LAND) returns None: SAPIENT has no command verb that
carries their semantics without reinterpretation (region tasking and
discrete thresholds are a different contract), and inventing a mapping
would change what the receiving node is being asked to do. The residue is
documented in this adapter's README.

ZMeta `payload.priority` is dropped everywhere: the SAPIENT Task message
has no priority field and smuggling it through task_name/description
free-text would make free-text load-bearing.
"""

import math
from collections.abc import Mapping, Sequence
from collections.abc import Set as AbstractSet
from datetime import datetime, timedelta, timezone

from adapters.egress.sapient.ulid_util import is_ulid

# Text leaves are Sequences, so they have to be excluded before the Sequence
# branch or every string becomes a walk over its own characters - and a
# one-character string yields itself, so that walk never terminates.
_TEXT_LEAF_TYPES = (str, bytes, bytearray)

# Canonical altitude field names a COMMAND_EVENT must never carry (semantics
# contract 7.8). COMMAND_EVENT SHALL NOT specify altitude - the receiving
# autonomy/sensor node deconflicts vertical internally. This egress guard
# rejects a command whose projected geometry (target_geo) carries an altitude
# field at any depth, so no vertical intent reaches the SAPIENT Location
# (whose optional z is additionally never populated by construction). The
# authoritative, whole-payload altitude gate is the gateway validator
# (COMMAND_HAS_ALTITUDE); this set is kept a superset of, and in sync with,
# policy/semantics.yaml command_event.payload_must_not_contain.
_ALTITUDE_FIELDS = frozenset({
    "alt", "alt_m", "altitude", "altitude_m", "alt_hae_m", "alt_msl_m",
    "agl_m", "target_alt_m", "target_altitude",
})


def _contains_altitude(value):
    # Contract 7.8: COMMAND_EVENT SHALL NOT specify altitude. This is
    # defence in depth behind the gateway's COMMAND_HAS_ALTITUDE validator,
    # so its failure mode matters: the recursive dict/list version raised
    # RecursionError on deep geometry (a crash where the documented signal
    # is None/ValueError) and never looked inside a Mapping that is not a
    # dict, a tuple, a set or a CBOR tag wrapper - so an altitude key one
    # container off the beaten path reached the tasked node unremarked.
    #
    # Iterative with a seen-set, same discipline as the MAVLink sibling
    # (zmeta_command_to_mission_intent._walk_containers) and the gateway
    # kernel walk (gateway/src/validators.py _child_entries): target_geo is
    # sender-controlled, so nesting depth must be a memory cost, never a
    # RecursionError, and CBOR value-sharing tags make the decoded structure
    # possibly cyclic, so an unbounded walk would be a hang (R1-11 R2-07).
    # Container coverage is by abstract type: cbor2 decodes CBOR tag 258
    # into a `set`, a map used as a map key into a Mapping that is not a
    # dict, and an unrecognised tag into a tag object whose `.value` still
    # reaches the wire. Mapping keys are walked as values too - a key can
    # itself be a frozendict carrying an altitude key inside it.
    stack = [value]
    seen = set()
    while stack:
        current = stack.pop()
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
            for key in current:
                # strip+casefold so whitespace-/case-padded altitude keys
                # cannot slip the guard (matches the gateway validator's key
                # normalization).
                if str(key).strip().casefold() in _ALTITUDE_FIELDS:
                    return True
            stack.extend(current.keys())
            stack.extend(current.values())
        elif isinstance(current, (AbstractSet, Sequence)):
            stack.extend(current)
        elif hasattr(current, "tag") and hasattr(current, "value"):
            stack.append(current.value)
    return False


def _parse_utc(ts):
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


def _is_finite_number(value):
    # Finite only: a NaN/inf coordinate is not an honest target claim.
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        # ``math.isfinite`` RAISES on a Python int outside the float64
        # range, and ``json.loads`` builds exactly such an int from a
        # plain integer literal — so a 400-digit target_lat would raise
        # out of this projection instead of refusing. The altitude
        # tripwire stays the only deliberate raise here (see docstring).
        return False


def _utc_z(dt):
    return dt.isoformat().replace("+00:00", "Z")


def zmeta_command_to_sapient_task(event, *, node_id, destination_id, track_to_object=None):
    """Convert a ZMeta COMMAND_EVENT into a SAPIENT Task message dict.

    Id discipline (SAPIENT proto is_ulid; Apex strictIdFormat rejects
    violations): `payload.task_id` must already be a valid ULID or the
    event is refused. The caller contract is that SAPIENT-bridged command
    producers mint ULID task_ids; the adapter never rewrites the
    idempotency key — a derived id would break idempotent re-issue across
    the bridge and TaskAck correlation.

    Args:
        event: ZMeta event dict. Must have event_type=COMMAND_EVENT with
            requires_deconfliction true.
        node_id: SAPIENT node UUID of the ZMeta gateway sending the task.
        destination_id: SAPIENT node UUID of the node being tasked.
            Required — a SAPIENT task without a destination is undeliverable.
        track_to_object: Optional dict mapping ZMeta target_track_id to the
            SAPIENT object_id observed from that node's detections. Required
            for TRACK_TARGET; a target with no known SAPIENT object identity
            is refused rather than given a fabricated correlation.

    Returns:
        Proto3-JSON-shaped SapientMessage dict carrying a Task, or None if
        the event cannot be honestly projected (wrong event type, not
        deconflicted, missing required fields, non-ULID task_id, or a
        task type with no SAPIENT verb).

    Raises:
        ValueError: if target_geo carries an altitude field (semantics
            contract 7.8 — altitude must never cross into a command).
    """
    if event.get("event", {}).get("event_type") != "COMMAND_EVENT":
        return None

    payload = event.get("payload", {})

    task_id = payload.get("task_id")
    task_type = payload.get("task_type")
    valid_for_ms = payload.get("valid_for_ms")
    requires_deconfliction = payload.get("requires_deconfliction")

    if not task_id or not task_type or valid_for_ms is None or requires_deconfliction is None:
        return None

    # task_id is the idempotency key minted by the SAPIENT-bridged command
    # producer (see docstring); a non-ULID id is refused, never rewritten.
    if not is_ulid(task_id):
        return None

    if requires_deconfliction is not True:
        return None

    # Envelope timestamp is the event's own ts: stamping translate-time wall
    # clock would fabricate freshness (semantics contract 9.5). No ts, no
    # honest time claim — refuse.
    ts = event.get("event", {}).get("ts")
    if not ts:
        return None

    if not node_id or not destination_id:
        return None

    if task_type == "GOTO":
        target_geo = payload.get("target_geo")
        if target_geo is None:
            return None
        if not isinstance(target_geo, Mapping):
            # A LIST of waypoint dicts is the natural producer mistake; the
            # documented contract is ValueError/None, never AttributeError.
            raise ValueError("target_geo must be a mapping (lat/lon)")
        if _contains_altitude(target_geo):
            raise ValueError("target_geo must be 2D (lat/lon only)")
        target_lat = target_geo.get("lat")
        target_lon = target_geo.get("lon")
        if not (_is_finite_number(target_lat) and _is_finite_number(target_lon)):
            return None
        # Location is built field-by-field from lat/lon only; the optional
        # SAPIENT z is never populated and no payload dict is ever copied
        # through, so altitude-adjacent keys cannot leak (contract 7.8).
        command = {
            "move_to": {
                "locations": [
                    {
                        "x": target_lon,
                        "y": target_lat,
                        "coordinate_system": "LOCATION_COORDINATE_SYSTEM_LAT_LNG_DEG_M",
                        "datum": "LOCATION_DATUM_WGS84_E",
                    }
                ]
            }
        }
    elif task_type == "TRACK_TARGET":
        target_track_id = payload.get("target_track_id")
        if not target_track_id:
            return None
        # follow_object_id must be a SAPIENT object_id the destination node
        # actually reported; without a caller-supplied correlation the id
        # would be fabricated — refuse.
        follow_object_id = (track_to_object or {}).get(target_track_id)
        if not follow_object_id:
            return None
        command = {"follow": {"follow_object_id": follow_object_id}}
    elif task_type == "CHANGE_SENSOR_MODE":
        sensor_mode = payload.get("sensor_mode")
        if not sensor_mode:
            return None
        command = {"mode_change": sensor_mode}
    else:
        # No honest SAPIENT verb for the remaining ZMeta task types
        # (documented residue — see module docstring and README).
        return None

    # Malformed ts or a non-integer valid_for_ms is refused per the
    # documented None contract; the altitude tripwire above remains the
    # only deliberate raise in this projection.
    #
    # OSError is in the tuple because `_parse_utc` calls `.astimezone()`,
    # which delegates to the platform for a NAIVE datetime and raises
    # OSError(EINVAL) on Windows for any pre-1970 instant. A naive
    # pre-epoch ts is the bad-clock symptom arriving without a zone —
    # without this arm it escapes the guard and the projection raises.
    try:
        time_dt = _parse_utc(ts)
        end_dt = time_dt + timedelta(milliseconds=int(valid_for_ms))
    except (ValueError, TypeError, OverflowError, OSError):
        return None

    return {
        "timestamp": _utc_z(time_dt),
        "node_id": node_id,
        "destination_id": destination_id,
        "task": {
            "task_id": task_id,
            "control": "CONTROL_START",
            "task_end_time": _utc_z(end_dt),
            "command": command,
        },
    }
