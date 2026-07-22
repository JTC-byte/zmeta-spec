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

ADAPTER_VERSION = "1.2.0"
SCHEMA_ID = "mavlink-telemetry"
PROMOTION_POLICY_ID = "PROMOTE-MAVLINK-STATE-V1"

# The v1.0 schema's LINK_STATUS state vocabulary. "UNKNOWN" is the honest label
# for a link whose health verdict nobody supplied; DEGRADED/DOWN additionally
# require metrics.reason_code.
_LINK_STATUS_STATES = ("UP", "DEGRADED", "DOWN", "UNKNOWN")


def _utc_now():
    return utc_now_z()


def _normalize_sync_state(sync_state):
    """Map the MAVLink-side "SYNCED" label onto the v1.0 sync_state vocabulary.

    ``LOCKED``/``HOLDOVER``/``UNSYNCED`` is the schema's enum; "SYNCED" and
    "LOCKED" are the same claim in two vocabularies, so this is a rename, not
    a promotion - nothing is made cleaner than the message reported.
    """
    return "LOCKED" if sync_state == "SYNCED" else sync_state


def _time_status_payload_state(sync_state, carried_state=None):
    """Derive TIME_STATUS ``payload.state`` from the carried sync verdict.

    ``payload.state`` must not assert a locked clock a message never reported:
    a SYSTEM_TIME dict that says nothing about sync is UNSYNCED, and UNSYNCED
    is DEGRADED, not SYNCED. Both TIME_STATUS emitters in this module share
    this one derivation so identical telemetry can never yield two opposite
    verdicts in the same field.

    A message-carried ``state`` is honoured only when it is *more* conservative
    than the derived verdict: an upstream that already knows its clock is
    degraded keeps that verdict, while an optimistic "UP"/"SYNCED" label never
    overrides an UNSYNCED metrics block. The event therefore never contradicts
    itself and never launders a caller's degraded claim into a clean one.
    """
    derived = "UP" if _normalize_sync_state(sync_state) == "LOCKED" else "DEGRADED"
    if carried_state and str(carried_state).upper() not in ("UP", "SYNCED"):
        return str(carried_state)
    return derived


def _assert_true_north_heading_frame(heading_frame):
    if heading_frame is None:
        return None
    if heading_frame != "TRUE_NORTH":
        raise ValueError("heading_frame must be TRUE_NORTH when provided")
    return heading_frame


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
    heading_frame=None,
    heading_source=None,
):
    """Translate a MAVLink platform state into a ZMeta STATE_EVENT.

    Args:
        state: Dict (or object with attributes) containing MAVLink-derived
            platform telemetry. Expected fields:
              lat (float): degrees; absent/None refuses emission (no default)
              lon (float): degrees; absent/None refuses emission (no default)
              alt_m (float): metres AMSL; absent/None refuses emission
                (no default). Canonical geo is all-or-nothing (contract 6.8).
              heading_deg (float, optional): 0-360; None or absent means
                unknown and omits payload.heading_deg (no 0.0 default).
                A known value is canonical only when heading_frame is
                explicitly "TRUE_NORTH".
              speed_mps (float, optional): ground speed m/s; None or absent
                omits payload.speed_mps (no 0.0 "stationary" default)
              gps_fix_type (int, optional): ArduPilot fix type 0-6; absent
                means unreported and omits payload.quality.gps_fix_type
              satellites_visible (int, optional): absent, or the MAVLink
                UINT8_MAX "satellite count unknown" sentinel (255), means
                unreported and omits payload.quality.satellites_visible
              vx, vy, vz (float): velocity components m/s (optional)
              roll_deg, pitch_deg, yaw_deg (float): attitude (optional)
              battery_voltage (float): volts (optional)
              battery_remaining_pct (int): 0-100 (optional)
              custom_mode (int): ArduPilot flight mode (optional)
        platform_id: Platform identifier string.
        producer: Producer string (default "mavlink-adapter").
        ts: ISO timestamp (default: current UTC).
        heading_frame: Optional heading reference-frame assertion. Only
            "TRUE_NORTH" is accepted; absent keeps MAVLink hdg out of the
            canonical payload.heading_deg field.
        heading_source: Optional quality.heading_source label to record when
            heading_frame is "TRUE_NORTH".

    Returns:
        ZMeta STATE_EVENT dict, or None when no usable position exists
        (any of lat/lon/alt_m absent, or the ArduPilot no-fix null-island
        signature: gps_fix_type < 2 with lat == 0.0 and lon == 0.0), or when
        no real lineage is available. STATE_EVENT lineage is mandatory (semantic
        contract 4.8) and must reference real events: supply
        ``state["based_on"]`` (list of parent ZMeta event ids, UUIDv7) or
        ``state["source_zmeta_event_id"]``. Neither a position nor a lineage
        parent is ever fabricated (convert or refuse, never invent).
    """
    if isinstance(state, dict):
        _get = state.get
    else:
        _get = lambda k, d=None: getattr(state, k, d)

    heading_frame = _assert_true_north_heading_frame(heading_frame)
    lat = _get("lat")
    lon = _get("lon")
    alt_m = _get("alt_m")
    # heading_deg comes from GLOBAL_POSITION_INT.hdg, which reports the value
    # as unknown (UINT16_MAX -> None after decode). An unknown heading is
    # omitted from the payload, never fabricated as a 0.0 (due-north) default.
    # MAVLink does not declare a true-vs-magnetic reference for hdg, so a known
    # heading is canonical only when deployment config explicitly asserts
    # heading_frame="TRUE_NORTH"; otherwise the raw value is retained only as
    # quality context.
    heading_deg = _get("heading_deg")
    # An unreported ground speed is omitted, never fabricated as a 0.0
    # ("stationary") default: payload.speed_mps is schema-optional, and
    # asserting that a platform is not moving is a claim the telemetry never
    # made. Same rule as heading above.
    speed_mps = _get("speed_mps")
    # Unreported GPS quality is omitted from payload.quality rather than
    # restated as "0 satellites / no GPS", which the sensor never said either.
    # The decisions below (confidence floor, geo_status, the null-island
    # refusal) still treat an unreported fix as the no-fix floor, so the
    # missing value degrades the event and never cleans it up.
    gps_fix_type = _get("gps_fix_type")
    satellites_visible = _get("satellites_visible")
    fix_for_decisions = 0 if gps_fix_type is None else gps_fix_type

    # Refuse to fabricate a position. The v1.0 schema requires payload.geo on
    # TRACK_STATE and geo is all-or-nothing (contract 6.8: "If any of lat,
    # lon, or alt_m is missing, omit geo entirely. Missing values MUST be
    # omitted, not zero-filled"), so an event without a complete usable
    # position must not be emitted:
    # - absent lat/lon must not default to (0, 0);
    # - absent alt_m must not default to 0.0 m AMSL - a fabricated 0 is read
    #   downstream as a concrete altitude claim (CoT re-projects it as one)
    #   and drives deconfliction, terrain masking and 3D fusion;
    # - ArduPilot reports lat=0, lon=0 before GPS lock (fix types 0/1), the
    #   "null island" no-fix signature.
    if lat is None or lon is None or alt_m is None:
        return None
    if fix_for_decisions < 2 and lat == 0.0 and lon == 0.0:
        return None

    geo = {"lat": lat, "lon": lon, "alt_m": alt_m}
    confidence = _gps_fix_confidence(fix_for_decisions)

    quality = {}
    if gps_fix_type is not None:
        quality["gps_fix_type"] = gps_fix_type
    # GPS_RAW_INT.satellites_visible is uint8 with UINT8_MAX documented as
    # "if unknown"; 255 is the sentinel, never a 255-satellite measurement.
    # Guarded here as well as in decode_gps_raw_int because the state dict can
    # be assembled by any MAVLink bridge, the same way the battery sentinels
    # below are guarded on both sides.
    if satellites_visible is not None and satellites_visible != 255:
        quality["satellites_visible"] = satellites_visible
    if fix_for_decisions < 3:
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
    # The reflection check is a verification this template never performs,
    # so its verdict must arrive message-carried — never self-asserted
    # (contract 4.5.1; same rule the SAPIENT ingress enforces). Refuse to
    # promote rather than stamp a verdict for a check that never ran.
    loop_status = _get("loop_status")
    if not loop_status:
        return None

    promotion = {
        "state_category": "PROMOTED_EXTERNAL_STATE",
        "origin_kind": str(_get("origin_kind", "EXTERNAL_REPORT")),
        "projection_id": "mavlink",
        "promotion_policy_id": str(_get("promotion_policy_id", PROMOTION_POLICY_ID)),
        "trust_ref": str(_get("trust_ref", f"producer-authority:{producer}")),
        "lineage_status": str(_get("lineage_status", "EXTERNAL_SOURCE")),
        "loop_status": str(loop_status),
        "confidence_basis": str(_get("confidence_basis", "GPS_FIX_CONFIDENCE")),
        "source_event_uid": str(source_event_uid),
        "freshness_ms": 30000,
    }
    source_zmeta_event_id = _get("source_zmeta_event_id")
    if source_zmeta_event_id:
        promotion["source_zmeta_event_id"] = str(source_zmeta_event_id)

    # STATE_EVENT lineage is mandatory and must reference real events.
    # Refuse to emit rather than fabricate a parent id (same refusal rule as
    # the position handling above and the CoT/JREAP ingress templates).
    based_on = _get("based_on")
    if not based_on and source_zmeta_event_id:
        based_on = [source_zmeta_event_id]
    if not based_on:
        return None

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
            "quality": quality,
            "timing_quality": coerce_timing_quality(_get("timing_quality"), event_ts=event_ts),
            "extensions": {"external_promotion": promotion},
        },
        "confidence": confidence,
        "lineage": {
            "based_on": [str(item) for item in based_on],
            "transform": f"promote:{SCHEMA_ID}@{ADAPTER_VERSION}:{promotion['promotion_policy_id']}",
        },
    }
    if speed_mps is not None:
        event["payload"]["speed_mps"] = speed_mps
    if heading_deg is not None and heading_frame == "TRUE_NORTH":
        event["payload"]["heading_deg"] = heading_deg
        event["payload"]["quality"]["heading_source"] = (
            heading_source or "MAVLINK_GLOBAL_POSITION_INT_TRUE_NORTH"
        )
    elif heading_deg is not None:
        event["payload"]["quality"]["mavlink_hdg_frame_unknown_deg"] = heading_deg
    return event


# ---------------------------------------------------------------------------
# Raw MAVLink messages -> platform state dict
# ---------------------------------------------------------------------------


def decode_global_position_int(msg_dict):
    """Extract platform position from GLOBAL_POSITION_INT fields.

    ArduPilot sends lat/lon as int32 (degE7), alt as int32 (mm),
    velocities as int16 (cm/s), heading as uint16 (cdeg, 65535=unknown).

    The MAVLink common message definition describes ``hdg`` only as
    "vehicle heading (yaw angle)" in centidegrees; it does not declare a
    true-vs-magnetic north reference. The decoded ``heading_deg`` therefore
    remains non-canonical until translate_platform_state receives an explicit
    heading_frame="TRUE_NORTH" assertion. Unknown heading decodes to None
    (omitted downstream, never defaulted).

    Every absent field decodes to None rather than to a zero: absent
    ``lat``/``lon``/``alt`` so the translator can refuse to fabricate a
    position (contract 6.8 - a missing altitude is omitted, never zero-filled),
    and absent ``vx``/``vy``/``vz`` so an unreported velocity is not restated
    as a measured standstill. ``speed_mps`` is derived only when both
    horizontal components were actually reported.
    """
    lat_raw = msg_dict.get("lat")
    lon_raw = msg_dict.get("lon")
    alt_raw = msg_dict.get("alt")
    vx_raw = msg_dict.get("vx")
    vy_raw = msg_dict.get("vy")
    vz_raw = msg_dict.get("vz")
    lat = lat_raw / 1e7 if lat_raw is not None else None
    lon = lon_raw / 1e7 if lon_raw is not None else None
    alt_m = alt_raw / 1000.0 if alt_raw is not None else None
    vx = vx_raw / 100.0 if vx_raw is not None else None
    vy = vy_raw / 100.0 if vy_raw is not None else None
    vz = vz_raw / 100.0 if vz_raw is not None else None
    hdg_cdeg = msg_dict.get("hdg", 65535)
    heading_deg = hdg_cdeg / 100.0 if hdg_cdeg != 65535 else None
    speed_mps = math.sqrt(vx ** 2 + vy ** 2) if vx is not None and vy is not None else None
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
    """Extract attitude from ATTITUDE fields (radians -> degrees).

    An axis the message does not report is omitted from the decoded state
    dict rather than decoded as 0.0 degrees, which would assert a measured
    level attitude the autopilot never reported. Omitted keys also leave any
    previously accumulated value in the caller's state dict intact.
    """
    decoded = {}
    for field, key in (("roll", "roll_deg"), ("pitch", "pitch_deg"), ("yaw", "yaw_deg")):
        value = msg_dict.get(field)
        if value is None:
            continue
        degrees = math.degrees(value)
        decoded[key] = degrees % 360 if key == "yaw_deg" else degrees
    return decoded


def decode_gps_raw_int(msg_dict):
    """Extract GPS fix quality from GPS_RAW_INT fields.

    An unreported ``fix_type`` or ``satellites_visible`` is omitted rather
    than decoded as 0, which would assert a measured "no GPS / 0 satellites"
    the receiver never reported. ``translate_platform_state`` still treats an
    absent fix type as the no-fix floor for confidence, geo_status and the
    null-island refusal, so the omission only ever degrades the event.

    MAVLink common.xml declares ``satellites_visible`` as uint8 with "if
    unknown, set to UINT8_MAX", so 255 is the same class of "not sent"
    sentinel as ``GLOBAL_POSITION_INT.hdg = 65535`` and the two SYS_STATUS
    sentinels: it decodes to an omitted key, never to a 255-satellite
    measurement that would read downstream as the best fix ever observed.
    """
    decoded = {}
    fix_type = msg_dict.get("fix_type")
    if fix_type is not None:
        decoded["gps_fix_type"] = fix_type
    satellites_visible = msg_dict.get("satellites_visible")
    if satellites_visible is not None and satellites_visible != 255:
        decoded["satellites_visible"] = satellites_visible
    return decoded


def decode_sys_status(msg_dict):
    """Extract battery info from SYS_STATUS fields.

    MAVLink SYS_STATUS documents ``voltage_battery = UINT16_MAX`` as "voltage
    not sent by autopilot" and ``battery_remaining = -1`` as "battery
    remaining not sent". Both sentinels, and an absent field, decode to an
    omitted key - never to a fabricated 0 V flat battery, and never to a
    65.535 V measurement laundered out of the unknown sentinel.
    """
    decoded = {}
    voltage_mv = msg_dict.get("voltage_battery")
    if voltage_mv is not None and voltage_mv != 65535:
        decoded["battery_voltage"] = voltage_mv / 1000.0
    remaining_pct = msg_dict.get("battery_remaining")
    if remaining_pct is not None and remaining_pct >= 0:
        decoded["battery_remaining_pct"] = remaining_pct
    return decoded


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

    ``payload.state`` is never invented on any of the three branches. The
    acknowledgement verdict must be message-carried (the v1.0 TASK_ACK state
    vocabulary has no "unknown" member, so a message with no verdict is
    refused rather than reported as RECEIVED); the TIME_STATUS verdict is
    derived from the carried sync state by the same ``_time_status_payload_state``
    ``translate_time_status`` uses, so the two never disagree; and the
    LINK_STATUS fallback stays "UNKNOWN".
    """
    if not isinstance(msg, dict):
        raise ValueError("msg must be a dict")

    msg_type = str(msg.get("type") or msg.get("msg_type") or msg.get("name") or "").upper()

    if "task_id" in msg or "mission_ack" in msg or "mission_state" in msg or "ack" in msg:
        # The acknowledgement verdict is the whole point of a TASK_ACK: a
        # commander reading "RECEIVED" believes the vehicle took the task.
        # It is never defaulted - the v1.0 TASK_ACK state enum offers no
        # "unknown" member to degrade into, so a message that carries no
        # verdict is refused (convert or refuse, never invent). Nothing is
        # lost: the task_id and original_event_id are already the commander's.
        state = msg.get("state") or msg.get("mission_state") or msg.get("ack")
        task_id = msg.get("task_id")
        original_event_id = (
            msg.get("original_event_id")
            or msg.get("command_event_id")
            or msg.get("event_id")
        )
        if task_id is None or original_event_id is None:
            raise ValueError("TASK_ACK requires task_id and original_event_id")
        if not state:
            raise ValueError(
                "TASK_ACK requires a message-carried ack state; an "
                "acknowledgement verdict is never fabricated"
            )
        metrics = {
            "task_id": task_id,
            "original_event_id": original_event_id,
        }
        return [
            _make_event("TASK_ACK", state, platform_id=platform_id, producer=producer, ts=ts, metrics=metrics)
        ]

    if "time_usec" in msg or "gps_time" in msg or msg_type in {"SYSTEM_TIME", "TIMESYNC"}:
        metrics = {}
        metrics["time_source"] = msg.get("time_source") or "UNKNOWN"
        metrics["sync_state"] = _normalize_sync_state(msg.get("sync_state") or "UNSYNCED")
        # payload.state is derived from the sync verdict this same payload
        # carries, never defaulted to "SYNCED": a SYSTEM_TIME dict that said
        # nothing about sync cannot assert a locked clock one line above a
        # metrics block that says UNSYNCED.
        state = _time_status_payload_state(metrics["sync_state"], msg.get("state"))
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
    latency_ms=None,
    packet_loss_pct=None,
    throughput_bps=None,
    state=None,
    reason_code=None,
    battery_voltage=None,
    battery_pct=None,
    rc_rssi=None,
    active_link="unknown",
    producer="mavlink-adapter",
    ts=None,
    based_on=None,
):
    """Build a LINK_STATUS SYSTEM_EVENT from MAVLink SYS_STATUS / battery data.

    ``latency_ms``, ``packet_loss_pct`` and ``throughput_bps`` are the three
    link measurements the v1.0 schema requires on a LINK_STATUS payload. They
    are caller-supplied and never defaulted: hard-coding ``0 ms / 0.0 % / 0
    bps`` would report a perfect, fully-measured link on a node whose comms
    were never measured at all. A caller without the measurements gets a
    refusal (ValueError), the same rule ``mavlink_decoded_to_zmeta_system_events``
    applies to TIME_STATUS - convert or refuse, never invent.

    ``state`` is the link-health verdict a consumer reads first, so it is not
    hard-coded either. It is caller-supplied and defaults to the v1.0 schema's
    own "UNKNOWN" rather than to "UP": measuring latency, loss and throughput
    is not the same as adjudicating that the link is healthy, and an adapter
    that reports UP alongside 92 % packet loss has laundered the one field the
    operator reads first. UNKNOWN keeps every measured metric on the event and
    filterable, so the consumer adjudicates. "DEGRADED"/"DOWN" additionally
    require ``reason_code`` (the v1.0 schema requires metrics.reason_code for
    those states); supplying a state outside UP/DEGRADED/DOWN/UNKNOWN, or a
    DEGRADED/DOWN with no reason, is refused rather than emitted invalid.

    ``battery_voltage``, ``battery_pct`` and ``rc_rssi`` are optional; when
    unreported they are omitted rather than emitted as 0 V / -1 % / 0 RSSI.

    ``based_on`` may carry real parent ZMeta event ids (UUIDv7 strings); when
    None (default), lineage is omitted (SYSTEM_EVENT lineage is optional and
    parent ids are never fabricated).
    """
    if latency_ms is None or packet_loss_pct is None or throughput_bps is None:
        raise ValueError(
            "LINK_STATUS requires measured latency_ms, packet_loss_pct and "
            "throughput_bps; link health is never fabricated"
        )
    if state is None:
        state = "UNKNOWN"
    if state not in _LINK_STATUS_STATES:
        raise ValueError(
            "LINK_STATUS state must be one of "
            f"{'/'.join(_LINK_STATUS_STATES)}; link health is never fabricated"
        )
    if state in ("DEGRADED", "DOWN") and not reason_code:
        raise ValueError(
            "LINK_STATUS state DEGRADED/DOWN requires metrics.reason_code"
        )
    metrics = {
        "link_id": f"edge-comms-{platform_id}",
        "active_link": active_link,
        "latency_ms": latency_ms,
        "packet_loss_pct": packet_loss_pct,
        "throughput_bps": throughput_bps,
    }
    if battery_voltage is not None:
        metrics["battery_voltage"] = battery_voltage
    if battery_pct is not None and battery_pct >= 0:
        metrics["battery_remaining_pct"] = battery_pct
    if rc_rssi is not None:
        metrics["rc_rssi"] = rc_rssi
    if reason_code is not None:
        metrics["reason_code"] = reason_code
    event = {
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
            "state": state,
            "metrics": metrics,
        },
    }
    if based_on:
        event["lineage"] = {
            "based_on": [str(item) for item in based_on],
            "transform": f"translate:{SCHEMA_ID}@{ADAPTER_VERSION}",
        }
    return event


def translate_time_status(
    *,
    platform_id,
    time_source="UNKNOWN",
    sync_state="UNSYNCED",
    est_error_ms=None,
    last_sync_ts=None,
    producer="mavlink-adapter",
    ts=None,
    based_on=None,
):
    """Build a TIME_STATUS SYSTEM_EVENT from MAVLink SYSTEM_TIME data.

    ``est_error_ms`` and ``last_sync_ts`` are caller-supplied and never
    defaulted. ``est_error_ms = 0.0`` would assert a perfectly accurate clock
    for a node that reported no timing error at all - and would do it in the
    uncertainty field consumers read to decide how far to trust the timeline -
    while defaulting ``last_sync_ts`` to the event timestamp would assert a
    sync that just happened. Both refuse instead (ValueError), the same rule
    ``mavlink_decoded_to_zmeta_system_events`` already applies to TIME_STATUS.

    ``based_on`` may carry real parent ZMeta event ids (UUIDv7 strings); when
    None (default), lineage is omitted (SYSTEM_EVENT lineage is optional and
    parent ids are never fabricated).
    """
    event_ts = normalize_utc_z(ts) or _utc_now()
    normalized_sync_state = _normalize_sync_state(sync_state)
    normalized_last_sync_ts = normalize_utc_z(last_sync_ts)
    if est_error_ms is None or normalized_last_sync_ts is None:
        raise ValueError(
            "TIME_STATUS requires est_error_ms and last_sync_ts; timing "
            "uncertainty and sync time are never fabricated"
        )
    event = {
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
            "state": _time_status_payload_state(normalized_sync_state),
            "metrics": {
                "time_source": time_source,
                "sync_state": normalized_sync_state,
                "est_error_ms": est_error_ms,
                "last_sync_ts": normalized_last_sync_ts,
            },
        },
    }
    if based_on:
        event["lineage"] = {
            "based_on": [str(item) for item in based_on],
            "transform": f"translate:{SCHEMA_ID}@{ADAPTER_VERSION}",
        }
    return event
