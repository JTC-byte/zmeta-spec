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

from datetime import datetime, timedelta, timezone

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
    if isinstance(value, dict):
        for key, item in value.items():
            # strip+casefold so whitespace-/case-padded altitude keys cannot
            # slip the guard (matches the gateway validator's key normalization).
            key_lc = str(key).strip().casefold()
            if key_lc in _ALTITUDE_FIELDS:
                return True
            if _contains_altitude(item):
                return True
    elif isinstance(value, list):
        for item in value:
            if _contains_altitude(item):
                return True
    return False


def _parse_utc(ts):
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    return datetime.fromisoformat(ts).astimezone(timezone.utc)


def _utc_z(dt):
    return dt.isoformat().replace("+00:00", "Z")


def zmeta_command_to_sapient_task(event, *, node_id, destination_id, track_to_object=None):
    """Convert a ZMeta COMMAND_EVENT into a SAPIENT Task message dict.

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
        deconflicted, missing required fields, or a task type with no
        SAPIENT verb).

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
        if _contains_altitude(target_geo):
            raise ValueError("target_geo must be 2D (lat/lon only)")
        target_lat = target_geo.get("lat")
        target_lon = target_geo.get("lon")
        if target_lat is None or target_lon is None:
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

    time_dt = _parse_utc(ts)
    end_dt = time_dt + timedelta(milliseconds=int(valid_for_ms))

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
