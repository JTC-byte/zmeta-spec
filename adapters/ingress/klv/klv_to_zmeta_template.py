import uuid


def klv_decoded_to_zmeta_observation(
    decoded_klv: dict,
    *,
    platform_id: str,
    sensor_id: str | None,
    producer: str,
    ts: str,
) -> dict:
    """
    Template: Convert decoded KLV tags into a single OBSERVATION_EVENT.
    """
    lat = decoded_klv.get("lat")
    lon = decoded_klv.get("lon")
    alt_m = decoded_klv.get("alt_m")

    event = {
        "zmeta_version": "1.0",
        "event": {
            "event_id": str(uuid.uuid4()),
            "event_type": "OBSERVATION_EVENT",
            "event_subtype": "KLV_OBSERVATION",
            "ts": ts,
        },
        "source": {
            "platform_id": platform_id,
            "node_role": "EDGE",
            "producer": producer,
        },
        "payload": {
            "modality": "EO",
            "features": {
                "klv": decoded_klv
            },
        },
    }

    if sensor_id is not None:
        event["source"]["sensor_id"] = sensor_id
    if lat is not None and lon is not None and alt_m is not None:
        event["payload"]["geo"] = {"lat": lat, "lon": lon, "alt_m": alt_m}

    return event
