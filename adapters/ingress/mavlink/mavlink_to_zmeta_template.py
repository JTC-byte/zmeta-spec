"""MAVLink telemetry to ZMeta event translator.

Translates decoded MAVLink messages into ZMeta events:
  - GLOBAL_POSITION_INT + GPS_RAW_INT + ATTITUDE -> STATE_EVENT (TRACK_STATE)
  - SYS_STATUS / BATTERY_STATUS -> SYSTEM_EVENT (LINK_STATUS)
  - SYSTEM_TIME / TIMESYNC -> SYSTEM_EVENT (TIME_STATUS)
  - COMMAND_ACK / MISSION_ACK -> SYSTEM_EVENT (TASK_ACK)

Platform state translation is extracted from the Z-ISR edge module
(edge/edge/zmeta_builder.py and edge/edge/mavlink/bridge.py).

Source: Z-ISR edge/edge/mavlink/bridge.py and edge/edge/zmeta_builder.py
"""

import math

from adapters.ingress.time_utils import coerce_timing_quality, normalize_utc_z, utc_now_z
from zmeta_uuid import uuid7

ADAPTER_VERSION = "1.0.0"
SCHEMA_ID = "mavlink-telemetry"
PROMOTION_POLICY_ID = "PROMOTE-MAVLINK-STATE-V1"


def _utc_now():
    return utc_now_z()


def _gps_fix_confidence(gps_fix_type):
    """Map MAVLink GPS fix type to a conservative track-state confidence.

    ArduPilot fix types: 0=no GPS, 1=no fix, 2=2D, 3=3D, 4=DGPS, 5=RTK float, 6=RTK fixed
    """
    if gps_fix_type >= 3:
        return 0.8
    if gps_fix_type == 2:
        return 0.5
    return 0.2


def _make_event(system_type, state, *, platform_id, producer, ts, metrics=None):
    event = {
        "zmeta_version": "1.0",
        "event": {
            "event_id": str(uuid7()),
            "event_type": "SYSTEM_EVENT",
            "event_subtype": system_type,
            "ts": normalize_utc_z(ts) or _utc_now(),
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


# ---------------------------------------------------------------------------
# Platform state -> STATE_EVENT
# ---------------------------------------------------------------------------


def translate_platform_state(
    state,
    *,
    platform_id,
    producer="mavlink-adapter",
    ts=None,
):
    """Translate a MAVLink platform state into a ZMeta STATE_EVENT.

    Args:
        state: Dict (or object with attributes) containing MAVLink-derived
            platform telemetry. Expected fields:
              lat (float): degrees
              lon (float): degrees
              alt_m (float): metres AMSL
              heading_deg (float): 0-360
              speed_mps (float): ground speed m/s
              gps_fix_type (int): ArduPilot fix type 0-6
              satellites_visible (int)
              vx, vy, vz (float): velocity components m/s (optional)
              roll_deg, pitch_deg, yaw_deg (float): attitude (optional)
              battery_voltage (float): volts (optional)
              battery_remaining_pct (int): 0-100 (optional)
              custom_mode (int): ArduPilot flight mode (optional)
        platform_id: Platform identifier string.
        producer: Producer string (default "mavlink-adapter").
        ts: ISO timestamp (default: current UTC).

    Returns:
        ZMeta STATE_EVENT dict.
    """
    if isinstance(state, dict):
        _get = state.get
    else:
        _get = lambda k, d=None: getattr(state, k, d)

    lat = _get("lat", 0.0)
    lon = _get("lon", 0.0)
    alt_m = _get("alt_m", 0.0)
    heading_deg = _get("heading_deg", 0.0)
    speed_mps = _get("speed_mps", 0.0)
    gps_fix_type = _get("gps_fix_type", 0)
    satellites_visible = _get("satellites_visible", 0)

    geo = {"lat": lat, "lon": lon, "alt_m": alt_m}
    confidence = _gps_fix_confidence(gps_fix_type)

    quality = {
        "gps_fix_type": gps_fix_type,
        "satellites_visible": satellites_visible,
    }
    if gps_fix_type < 3:
        quality["geo_status"] = "STALE"
    else:
        quality["geo_status"] = "AVAILABLE"

    # Optional attitude fields
    for attr in ("roll_deg", "pitch_deg", "yaw_deg", "vx", "vy", "vz"):
        val = _get(attr)
        if val is not None:
            quality[attr] = val

    # Optional battery/mode fields
    battery_v = _get("battery_voltage")
    if battery_v is not None and battery_v > 0:
        quality["battery_voltage"] = battery_v
    battery_pct = _get("battery_remaining_pct")
    if battery_pct is not None and battery_pct >= 0:
        quality["battery_remaining_pct"] = battery_pct
    custom_mode = _get("custom_mode")
    if custom_mode is not None:
        quality["custom_mode"] = custom_mode

    event_ts = normalize_utc_z(ts) or _utc_now()
    source_event_uid = (
        _get("source_event_uid")
        or _get("message_uid")
        or _get("msg_id")
        or f"mavlink:{platform_id}:{event_ts}"
    )
    promotion = {
        "state_category": "PROMOTED_EXTERNAL_STATE",
        "origin_kind": str(_get("origin_kind", "EXTERNAL_REPORT")),
        "projection_id": "mavlink",
        "promotion_policy_id": str(_get("promotion_policy_id", PROMOTION_POLICY_ID)),
        "trust_ref": str(_get("trust_ref", f"producer-authority:{producer}")),
        "lineage_status": str(_get("lineage_status", "EXTERNAL_SOURCE")),
        "loop_status": str(_get("loop_status", "CHECKED_NOT_REFLECTION")),
        "confidence_basis": str(_get("confidence_basis", "GPS_FIX_CONFIDENCE")),
        "source_event_uid": str(source_event_uid),
        "freshness_ms": 30000,
    }
    source_zmeta_event_id = _get("source_zmeta_event_id")
    if source_zmeta_event_id:
        promotion["source_zmeta_event_id"] = str(source_zmeta_event_id)

    event = {
        "zmeta_version": "1.0",
        "event": {
            "event_id": str(uuid7()),
            "event_type": "STATE_EVENT",
            "event_subtype": "TRACK_STATE",
            "ts": event_ts,
        },
        "source": {
            "platform_id": platform_id,
            "node_role": "GATEWAY",
            "producer": producer,
        },
        "payload": {
            "track_id": f"{producer}-{platform_id}-platform-position",
            "geo": geo,
            "valid_for_ms": 30000,
            "heading_deg": heading_deg,
            "speed_mps": speed_mps,
            "quality": quality,
            "timing_quality": coerce_timing_quality(_get("timing_quality"), event_ts=event_ts),
            "extensions": {"external_promotion": promotion},
        },
        "confidence": confidence,
        "lineage": {
            "based_on": [str(uuid7())],
            "transform": f"promote:{SCHEMA_ID}@{ADAPTER_VERSION}:{promotion['promotion_policy_id']}",
        },
    }
    return event


# ---------------------------------------------------------------------------
# Raw MAVLink messages -> platform state dict
# ---------------------------------------------------------------------------


def decode_global_position_int(msg_dict):
    """Extract platform position from GLOBAL_POSITION_INT fields.

    ArduPilot sends lat/lon as int32 (degE7), alt as int32 (mm),
    velocities as int16 (cm/s), heading as uint16 (cdeg, 65535=unknown).
    """
    lat = msg_dict.get("lat", 0) / 1e7
    lon = msg_dict.get("lon", 0) / 1e7
    alt_m = msg_dict.get("alt", 0) / 1000.0
    vx = msg_dict.get("vx", 0) / 100.0
    vy = msg_dict.get("vy", 0) / 100.0
    vz = msg_dict.get("vz", 0) / 100.0
    hdg_cdeg = msg_dict.get("hdg", 65535)
    heading_deg = hdg_cdeg / 100.0 if hdg_cdeg != 65535 else None
    speed_mps = math.sqrt(vx ** 2 + vy ** 2)
    return {
        "lat": lat,
        "lon": lon,
        "alt_m": alt_m,
        "heading_deg": heading_deg,
        "speed_mps": speed_mps,
        "vx": vx,
        "vy": vy,
        "vz": vz,
    }


def decode_attitude(msg_dict):
    """Extract attitude from ATTITUDE fields (radians -> degrees)."""
    return {
        "roll_deg": math.degrees(msg_dict.get("roll", 0.0)),
        "pitch_deg": math.degrees(msg_dict.get("pitch", 0.0)),
        "yaw_deg": math.degrees(msg_dict.get("yaw", 0.0)) % 360,
    }


def decode_gps_raw_int(msg_dict):
    """Extract GPS fix quality from GPS_RAW_INT fields."""
    return {
        "gps_fix_type": msg_dict.get("fix_type", 0),
        "satellites_visible": msg_dict.get("satellites_visible", 0),
    }


def decode_sys_status(msg_dict):
    """Extract battery info from SYS_STATUS fields."""
    return {
        "battery_voltage": msg_dict.get("voltage_battery", 0) / 1000.0,
        "battery_remaining_pct": msg_dict.get("battery_remaining", -1),
    }


# ---------------------------------------------------------------------------
# System events (original template, preserved)
# ---------------------------------------------------------------------------


def mavlink_decoded_to_zmeta_system_events(
    msg: dict,
    *,
    platform_id: str,
    producer: str,
    ts: str,
) -> list[dict]:
    """
    Convert decoded MAVLink message dicts into SYSTEM_EVENTs.

    Handles TASK_ACK, TIME_STATUS, and LINK_STATUS based on message content.
    """
    if not isinstance(msg, dict):
        raise ValueError("msg must be a dict")

    msg_type = str(msg.get("type") or msg.get("msg_type") or msg.get("name") or "").upper()

    if "task_id" in msg or "mission_ack" in msg or "mission_state" in msg or "ack" in msg:
        state = msg.get("state") or msg.get("mission_state") or msg.get("ack") or "RECEIVED"
        task_id = msg.get("task_id")
        original_event_id = (
            msg.get("original_event_id")
            or msg.get("command_event_id")
            or msg.get("event_id")
        )
        if task_id is None or original_event_id is None:
            raise ValueError("TASK_ACK requires task_id and original_event_id")
        metrics = {
            "task_id": task_id,
            "original_event_id": original_event_id,
        }
        return [
            _make_event("TASK_ACK", state, platform_id=platform_id, producer=producer, ts=ts, metrics=metrics)
        ]

    if "time_usec" in msg or "gps_time" in msg or msg_type in {"SYSTEM_TIME", "TIMESYNC"}:
        state = msg.get("state") or "SYNCED"
        metrics = {}
        metrics["time_source"] = msg.get("time_source") or "UNKNOWN"
        metrics["sync_state"] = msg.get("sync_state") or "UNSYNCED"
        metrics["est_error_ms"] = msg.get("est_error_ms")
        metrics["last_sync_ts"] = normalize_utc_z(msg.get("last_sync_ts"))
        if metrics["est_error_ms"] is None or metrics["last_sync_ts"] is None:
            raise ValueError("TIME_STATUS requires est_error_ms and last_sync_ts")
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


# ---------------------------------------------------------------------------
# Link status / edge health
# ---------------------------------------------------------------------------


def translate_link_status(
    *,
    platform_id,
    battery_voltage=0.0,
    battery_pct=-1,
    rc_rssi=0,
    active_link="unknown",
    producer="mavlink-adapter",
    ts=None,
):
    """Build a LINK_STATUS SYSTEM_EVENT from MAVLink SYS_STATUS / battery data."""
    return {
        "zmeta_version": "1.0",
        "event": {
            "event_id": str(uuid7()),
            "event_type": "SYSTEM_EVENT",
            "event_subtype": "LINK_STATUS",
            "ts": normalize_utc_z(ts) or _utc_now(),
        },
        "source": {
            "platform_id": platform_id,
            "node_role": "EDGE",
            "producer": producer,
        },
        "payload": {
            "system_type": "LINK_STATUS",
            "state": "UP",
            "metrics": {
                "link_id": f"edge-comms-{platform_id}",
                "battery_voltage": battery_voltage,
                "battery_remaining_pct": battery_pct,
                "rc_rssi": rc_rssi,
                "active_link": active_link,
                "latency_ms": 0,
                "packet_loss_pct": 0.0,
                "throughput_bps": 0,
            },
        },
        "lineage": {
            "based_on": [str(uuid7())],
            "transform": f"translate:{SCHEMA_ID}@{ADAPTER_VERSION}",
        },
    }


def translate_time_status(
    *,
    platform_id,
    time_source="UNKNOWN",
    sync_state="UNSYNCED",
    est_error_ms=0.0,
    last_sync_ts=None,
    producer="mavlink-adapter",
    ts=None,
):
    """Build a TIME_STATUS SYSTEM_EVENT from MAVLink SYSTEM_TIME data."""
    event_ts = normalize_utc_z(ts) or _utc_now()
    normalized_sync_state = "LOCKED" if sync_state == "SYNCED" else sync_state
    normalized_last_sync_ts = normalize_utc_z(last_sync_ts) or event_ts
    return {
        "zmeta_version": "1.0",
        "event": {
            "event_id": str(uuid7()),
            "event_type": "SYSTEM_EVENT",
            "event_subtype": "TIME_STATUS",
            "ts": event_ts,
        },
        "source": {
            "platform_id": platform_id,
            "node_role": "EDGE",
            "producer": producer,
        },
        "payload": {
            "system_type": "TIME_STATUS",
            "state": "UP" if normalized_sync_state == "LOCKED" else "DEGRADED",
            "metrics": {
                "time_source": time_source,
                "sync_state": normalized_sync_state,
                "est_error_ms": est_error_ms,
                "last_sync_ts": normalized_last_sync_ts,
            },
        },
        "lineage": {
            "based_on": [str(uuid7())],
            "transform": f"translate:{SCHEMA_ID}@{ADAPTER_VERSION}",
        },
    }
