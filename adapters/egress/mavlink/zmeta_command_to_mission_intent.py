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


def zmeta_command_to_mission_intent(event):
    """
    Convert a ZMeta COMMAND_EVENT to a MissionIntent dict.
    Returns None if the input is not a COMMAND_EVENT or missing required fields.
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
        "priority": payload.get("priority") or "MED",
        "requires_deconfliction": True,
    }
    if target_lat is not None and target_lon is not None:
        mission["target_lat"] = target_lat
        mission["target_lon"] = target_lon

    geometry = payload.get("geometry")
    if geometry is not None:
        if _contains_altitude(geometry):
            raise ValueError("command geometry must not include altitude")
        mission["geometry"] = geometry

    return mission
