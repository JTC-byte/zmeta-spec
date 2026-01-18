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

    return {k: v for k, v in tagdict.items() if v is not None}
