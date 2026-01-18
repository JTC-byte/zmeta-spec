import uuid


def _make_event(system_type, state, *, platform_id, producer, ts, metrics=None):
    event = {
        "zmeta_version": "1.0",
        "event": {
            "event_id": str(uuid.uuid4()),
            "event_type": "SYSTEM_EVENT",
            "event_subtype": system_type,
            "ts": ts,
        },
        "source": {
            "platform_id": platform_id,
            "node_role": "EDGE",
            "producer": producer,
        },
        "payload": {
            "system_type": system_type,
            "state": state,
        },
    }

    if metrics:
        event["payload"]["metrics"] = metrics
    return event


def mavlink_decoded_to_zmeta_system_events(
    msg: dict,
    *,
    platform_id: str,
    producer: str,
    ts: str,
) -> list[dict]:
    """
    Template: Convert decoded MAVLink message dicts into minimal SYSTEM_EVENTs.
    """
    if not isinstance(msg, dict):
        raise ValueError("msg must be a dict")

    msg_type = str(msg.get("type") or msg.get("msg_type") or msg.get("name") or "").upper()

    if "task_id" in msg or "mission_ack" in msg or "mission_state" in msg or "ack" in msg:
        state = msg.get("state") or msg.get("mission_state") or msg.get("ack") or "RECEIVED"
        metrics = {}
        if "task_id" in msg and msg["task_id"] is not None:
            metrics["task_id"] = msg["task_id"]
        return [
            _make_event("TASK_ACK", state, platform_id=platform_id, producer=producer, ts=ts, metrics=metrics or None)
        ]

    if "time_usec" in msg or "gps_time" in msg or msg_type in {"SYSTEM_TIME", "TIMESYNC"}:
        state = msg.get("state") or "SYNCED"
        metrics = {}
        if "time_usec" in msg:
            metrics["time_usec"] = msg["time_usec"]
        if "gps_time" in msg:
            metrics["gps_time"] = msg["gps_time"]
        return [
            _make_event("TIME_STATUS", state, platform_id=platform_id, producer=producer, ts=ts, metrics=metrics or None)
        ]

    metrics = {}
    if "rssi" in msg:
        metrics["rssi"] = msg["rssi"]
    if "snr" in msg:
        metrics["snr"] = msg["snr"]
    if "drop_rate" in msg:
        metrics["drop_rate"] = msg["drop_rate"]

    state = msg.get("state") or msg.get("link_state") or "UNKNOWN"
    return [
        _make_event("LINK_STATUS", state, platform_id=platform_id, producer=producer, ts=ts, metrics=metrics or None)
    ]
