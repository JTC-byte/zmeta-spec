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
        if any(key in target_geo for key in ("alt", "alt_m", "altitude")):
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
        mission["geometry"] = geometry

    return mission
