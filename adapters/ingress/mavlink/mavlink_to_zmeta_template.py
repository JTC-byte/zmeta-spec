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

# The v1.0 schema's LINK_STATUS metrics.reason_code vocabulary, mirrored from
# schema/zmeta-event-1.0.schema.json $defs/SystemPayload. Mirrored rather than
# loaded because this file is a template meant to be copied into a bridge with
# no ZMeta repo alongside it; the schema remains authoritative, and a drift
# between the two is a schema-refusal at the gateway, never a silent pass.
_LINK_STATUS_REASON_CODES = (
    "LINK_LOSS",
    "LOW_RSSI",
    "HIGH_LATENCY",
    "HIGH_PACKET_LOSS",
    "LOW_THROUGHPUT",
    "INTERFERENCE",
    "JAMMED",
    "BACKHAUL_DOWN",
    "NO_ROUTE",
    "CONFIG_ERROR",
    "POWER_SAVE",
    "UNKNOWN_CAUSE",
)

# The v1.0 schema's TASK_ACK state vocabulary, mirrored the same way and for
# the same reason. There is deliberately no "unknown" member: an unknown
# acknowledgement is not a state a task can be in, it is the absence of an ack,
# so a message that carries no interpretable verdict is refused rather than
# reported (doctrine review log R1-11-05, HELD).
_TASK_ACK_STATES = (
    "RECEIVED",
    "ACCEPTED",
    "REJECTED",
    "EXECUTING",
    "COMPLETED",
    "FAILED",
    "CANCELLED",
    "EXPIRED",
    "DUPLICATE_IGNORED",
)

# The v1.0 schema's TASK_ACK metrics.reason_code vocabulary, mirrored the same
# way and for the same reason as the LINK_STATUS codes above.
_TASK_ACK_REASON_CODES = (
    "SCHEMA_INVALID",
    "EVENT_TYPE_NOT_ALLOWED_FOR_ROLE",
    "EVENT_TYPE_NOT_ALLOWED_FOR_PROFILE",
    "PRODUCER_NOT_ALLOWED",
    "COMMAND_NOT_DECONFLICTED",
    "COMMAND_HAS_ALTITUDE",
    "TASK_DUPLICATE",
    "TASK_EXPIRED",
    "TASK_CANCELLED",
    "TASK_FAILED",
    "TASK_ABORTED",
    "TASK_REJECTED",
)

# The conditional obligation attached to that vocabulary: the v1.0 schema
# requires metrics.reason_code on exactly these five verdicts - the negative
# acks a commander most needs. Absent a message-carried cause, each is paired
# with the code that restates the verdict itself (the same pairing the SAPIENT
# ingress makes). A restatement, not a diagnosis: it adds no cause the message
# did not carry, so nothing is fabricated - and without it every negative
# verdict this branch emits is gateway-refused, so the commander sees a
# SCHEMA_VIOLATION diagnostic instead of the REJECTED.
_TASK_ACK_REASON_REQUIRED = {
    "REJECTED": "TASK_REJECTED",
    "FAILED": "TASK_FAILED",
    "CANCELLED": "TASK_CANCELLED",
    "EXPIRED": "TASK_EXPIRED",
    "DUPLICATE_IGNORED": "TASK_DUPLICATE",
}

# The three keys a decoded MISSION_ACK / COMMAND_ACK dict may carry the verdict
# under. Presence is tested by key, never by truthiness: MAV_MISSION_ACCEPTED
# and MAV_RESULT_ACCEPTED are both the integer 0, so a truthiness test destroys
# precisely the successful acknowledgements.
_TASK_ACK_CARRIER_KEYS = ("state", "mission_state", "ack")

# TIME_STATUS payload.state, ordered least-degraded to most. The v1.0 schema
# does NOT enum-constrain this field (only the LINK_STATUS and TASK_ACK
# branches of $defs/SystemPayload constrain `state`), so there is no governed
# enum to derive from and nothing downstream that would catch an
# out-of-vocabulary verdict - which is exactly why the vocabulary has to be
# declared and enforced here. An ordering, not a whitelist: "more conservative"
# has to be a comparison, or the guard degenerates into a list of the two
# labels its author happened to think of.
_TIME_STATUS_STATE_SEVERITY = {"UP": 0, "DEGRADED": 1, "DOWN": 2}

# "SYNCED" is the MAVLink-side spelling of a locked clock - the same rename
# _normalize_sync_state performs on the metrics side, not an extra verdict.
_TIME_STATUS_STATE_SYNONYMS = {"SYNCED": "UP"}

# MAVLink's uint8 "invalid/unknown" sentinel. GPS_RAW_INT.satellites_visible,
# RC_CHANNELS(_RAW).rssi and RADIO_STATUS.rssi all document "Values: [0-254],
# UINT8_MAX: invalid/unknown".
_UINT8_UNKNOWN = 255

# SYS_STATUS.voltage_battery is uint16 millivolts with UINT16_MAX documented as
# "voltage not sent by autopilot". decode_sys_status drops it in millivolts;
# this is the same sentinel in the volts a caller-assembled state dict carries,
# because a bridge copied from an older template divides before handing it over.
_UINT16_UNKNOWN_VOLTAGE_V = 65535 / 1000.0


def _utc_now():
    return utc_now_z()


def _is_real_number(value):
    """True for a value the range guards below can actually compare.

    Needed because those guards use ordered comparisons: without it a caller
    handing a string voltage or heading - which every one of these emitters
    accepts as an opaque keyword - would get a bare ``TypeError`` out of the
    adapter instead of the documented disposition. ``bool`` is excluded on
    purpose: ``True`` is an ``int`` in Python, and a boolean is not a
    measurement in any of these fields.
    """
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _is_kernel_business(value):
    """True for a non-finite, which these guards deliberately do not swallow.

    A NaN/Inf in a canonical or quality field is refused by the kernel's
    value-honesty gate, loudly and with a reason code the operator can filter
    on. Dropping it here instead would trade that filterable refusal for a
    silent omission - the operator would lose both the value and the signal
    that anything was wrong. Range and sentinel guards stop at their own
    question; non-finiteness belongs to the gate that owns it.
    """
    return isinstance(value, float) and not math.isfinite(value)


def _uint8_measurement_or_none(value):
    """Drop MAVLink's uint8 UINT8_MAX "invalid/unknown" sentinel.

    255 on a documented 0-254 scale is not a measurement; forwarded verbatim it
    reads downstream as the strongest signal ever observed, i.e. the sentinel
    becomes the best possible reading. Callers that report RSSI in dBm are
    unaffected - a dBm scale never reaches +255 either, so 255 is unusable in
    both readings this adapter accepts.
    """
    if value is None or value == _UINT8_UNKNOWN:
        return None
    return value


def _battery_voltage_or_none(volts):
    """Drop a battery voltage that is a sentinel or a fabricated zero.

    Two values are refused. ``UINT16_MAX / 1000`` is SYS_STATUS's "voltage not
    sent by autopilot" after the conversion any bridge performs, and publishing
    it is the 65.535 V measurement ``decode_sys_status`` already refuses to
    manufacture one layer down. ``<= 0`` is the fabricated-default shape: an
    autopilot with no battery monitor configured reports 0, and a flying
    vehicle cannot be at 0 V, so a zero here is "not measured", not a flat
    battery. Guarded on both sides of the boundary because a state dict, and
    every ``translate_link_status`` keyword, can be assembled by any bridge -
    a decoder-only guard is half a guard.

    Stated cost: a genuine reading of exactly 65.535 V - reachable on a 16S
    pack - is omitted for that sample. An omitted optional quality field
    degrades the event; a sentinel published as a healthy-battery measurement
    launders it, and the two are indistinguishable at this boundary.
    """
    if not _is_real_number(volts):
        return None
    if _is_kernel_business(volts):
        return volts
    if volts <= 0 or volts == _UINT16_UNKNOWN_VOLTAGE_V:
        return None
    return volts


def _heading_deg_or_none(heading_deg):
    """Drop a heading that is outside the only range a heading can occupy.

    GLOBAL_POSITION_INT.hdg = UINT16_MAX is "unknown"; a bridge that divides
    before handing the value over produces 655.35 deg. That is not a bearing in
    any frame, and on the non-canonical ``quality`` path nothing downstream
    catches it (only ``payload.heading_deg`` carries the schema's 0-360 bound).
    Omitted, never clamped: clamping would invent a direction.
    """
    if not _is_real_number(heading_deg):
        return None
    if _is_kernel_business(heading_deg):
        return heading_deg
    if not 0 <= heading_deg <= 360:
        return None
    return heading_deg


def _normalize_sync_state(sync_state):
    """Map the MAVLink-side "SYNCED" label onto the v1.0 sync_state vocabulary.

    ``LOCKED``/``HOLDOVER``/``UNSYNCED`` is the schema's enum; "SYNCED" and
    "LOCKED" are the same claim in two vocabularies, so this is a rename, not
    a promotion - nothing is made cleaner than the message reported.
    """
    return "LOCKED" if sync_state == "SYNCED" else sync_state


def _normalize_vocabulary_token(value, vocabulary, synonyms=None):
    """Fold a caller-supplied label onto a declared vocabulary, or return None.

    Normalisation is surrounding whitespace and case only, and it happens
    *before* the comparison. ``"UP "`` renders as ``UP`` in every operator UI,
    so a guard that compares the raw string lets the exact label it was written
    to catch escape on one space. Non-strings normalise to nothing: they are
    not spellings of a verdict, and coercing them with ``str()`` would turn an
    uninterpretable value into a schema-valid one.
    """
    if not isinstance(value, str):
        return None
    token = value.strip().upper()
    if synonyms:
        token = synonyms.get(token, token)
    return token if token in vocabulary else None


def _time_status_payload_state(sync_state, carried_state=None):
    """Derive TIME_STATUS ``payload.state`` from the carried sync verdict.

    ``payload.state`` must not assert a locked clock a message never reported:
    a SYSTEM_TIME dict that says nothing about sync is UNSYNCED, and UNSYNCED
    is DEGRADED, not SYNCED. Both TIME_STATUS emitters in this module share
    this one derivation so identical telemetry can never yield two opposite
    verdicts in the same field.

    A message-carried ``state`` is honoured only when it is *more* conservative
    than the derived verdict, compared on the declared severity ordering
    ``_TIME_STATUS_STATE_SEVERITY``: an upstream that already knows its clock
    is degraded keeps that verdict, while an optimistic "UP"/"SYNCED" label
    never overrides an UNSYNCED metrics block.

    A carried value that is not a member of that vocabulary is **refused**
    (ValueError), not silently replaced by the derived verdict. Replacing it
    would be the laundering this function exists to prevent, running the other
    way: an unrankable label may be *more* degraded than the derivation
    ("FAULT", "DRIFTING", a raw numeric code), and quietly publishing the
    derived "UP" over it would clean up an upstream that said something was
    wrong. Since the label cannot be ranked, it cannot be honoured and it
    cannot be dropped - so the event that carries it is refused, the same
    disposition this module already applies to a TIME_STATUS missing
    ``est_error_ms`` and to an out-of-vocabulary LINK_STATUS ``state``.

    An absent verdict is not an uninterpretable one: ``None`` and a blank
    string mean "this message said nothing about clock health" and take the
    derived verdict.
    """
    derived = "UP" if _normalize_sync_state(sync_state) == "LOCKED" else "DEGRADED"
    if carried_state is None or (isinstance(carried_state, str) and not carried_state.strip()):
        return derived
    carried = _normalize_vocabulary_token(
        carried_state, _TIME_STATUS_STATE_SEVERITY, _TIME_STATUS_STATE_SYNONYMS
    )
    if carried is None:
        raise ValueError(
            "TIME_STATUS carried a state this adapter cannot rank: "
            f"{carried_state!r}. A clock verdict must be one of "
            f"{'/'.join(_TIME_STATUS_STATE_SEVERITY)} (or the synonym "
            f"{'/'.join(_TIME_STATUS_STATE_SYNONYMS)}); map the upstream label "
            "in the bridge. It is neither honoured nor discarded here - a "
            "verdict that cannot be ranked is never fabricated away"
        )
    if _TIME_STATUS_STATE_SEVERITY[carried] > _TIME_STATUS_STATE_SEVERITY[derived]:
        return carried
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
              alt_hae_m (float): metres above the WGS-84 ellipsoid, from
                GPS_RAW_INT.alt_ellipsoid. This is the only altitude datum
                contract 6.2 permits in canonical geo, so it is the only one
                that becomes payload.geo.alt_m. Present means a full 3-D
                position under the 1.0 stamp.
              alt_msl_m (float): metres above mean sea level, from
                GLOBAL_POSITION_INT.alt. Never written to payload.geo.alt_m.
                MSL is not HAE, and no geoid model ships with this template,
                so contract 6.2 leaves two lawful options: convert, or omit
                canonical geo. Present without alt_hae_m yields the declared
                2-D form (dimensionality "2D", no alt_m) under a 1.1.0 stamp,
                with the reported value preserved as non-canonical
                quality.mavlink_alt_msl_m.
              alt_m (float): legacy input key, read as MSL. It was documented
                as AMSL and written straight into canonical payload.geo.alt_m,
                which published a wrong-datum value as though it were HAE. An
                existing caller now degrades to the honest 2-D form instead.
                Absent altitude of every kind still refuses emission
                (no default). Canonical geo is all-or-nothing (contract 6.8).
              heading_deg (float, optional): 0-360; None, absent, or outside
                0-360 (655.35 is the UINT16_MAX "hdg unknown" sentinel a
                bridge produces by dividing before handing it over) means
                unknown and omits both heading destinations (no 0.0 default,
                and no clamp). A known value is canonical only when
                heading_frame is explicitly "TRUE_NORTH".
              speed_mps (float, optional): ground speed m/s; None or absent
                omits payload.speed_mps (no 0.0 "stationary" default)
              gps_fix_type (int, optional): ArduPilot fix type 0-6; absent
                means unreported and omits payload.quality.gps_fix_type
              satellites_visible (int, optional): absent, or the MAVLink
                UINT8_MAX "satellite count unknown" sentinel (255), means
                unreported and omits payload.quality.satellites_visible
              vx, vy, vz (float): velocity components m/s (optional)
              roll_deg, pitch_deg, yaw_deg (float): attitude (optional)
              battery_voltage (float): volts (optional); a non-positive value
                or the SYS_STATUS UINT16_MAX "voltage not sent" sentinel in
                volts (65.535) is omitted, never published as a measurement
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
    # Altitude datum is load-bearing, so the two datums are read into separate
    # names and only one of them can reach canonical geo. Contract 6.2: "All
    # altitude values SHALL be Height Above Ellipsoid (HAE) in meters ... MSL,
    # AGL, terrain-relative, pressure altitude, or local-frame altitude are not
    # permitted in canonical ZMeta v1.0 `geo`. If an adapter ingests such
    # values, it must convert them or omit canonical `geo`."
    alt_hae_m = _get("alt_hae_m")
    alt_msl_m = _get("alt_msl_m")
    if alt_msl_m is None:
        # The legacy `alt_m` key was documented as "metres AMSL" and written
        # unconverted into payload.geo.alt_m. That is the altitude-datum
        # laundering class the ADS-B ingress already refuses at the source
        # (alt_baro never becomes alt_m); this template carried the same defect
        # for GLOBAL_POSITION_INT.alt, which MAVLink defines as MSL. Reading
        # the legacy key as MSL degrades an existing caller to the honest 2-D
        # form rather than leaving it publishing a wrong-datum HAE claim.
        alt_msl_m = _get("alt_m")
    # heading_deg comes from GLOBAL_POSITION_INT.hdg, which reports the value
    # as unknown (UINT16_MAX -> None after decode). An unknown heading is
    # omitted from the payload, never fabricated as a 0.0 (due-north) default.
    # MAVLink does not declare a true-vs-magnetic reference for hdg, so a known
    # heading is canonical only when deployment config explicitly asserts
    # heading_frame="TRUE_NORTH"; otherwise the raw value is retained only as
    # quality context.
    # A heading outside 0-360 is not a bearing in any frame: the commonest
    # arrival is 655.35, the UINT16_MAX "hdg unknown" sentinel divided by 100
    # by a bridge that does the conversion itself. Guarded here as well as in
    # decode_global_position_int, and on both destinations - the canonical
    # payload.heading_deg is schema-bounded to 0-360, but the non-canonical
    # quality.mavlink_hdg_frame_unknown_deg is not, so an unguarded sentinel
    # lands there schema-clean.
    heading_deg = _heading_deg_or_none(_get("heading_deg"))
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
    if lat is None or lon is None:
        return None
    if alt_hae_m is None and alt_msl_m is None:
        return None
    if fix_for_decisions < 2 and lat == 0.0 and lon == 0.0:
        return None

    # Only an ellipsoidal altitude may occupy canonical geo.alt_m. When the
    # telemetry carried MSL instead, the horizontal fix is still real and is
    # published as the declared 2-D form (doctrine A1-02) rather than withheld
    # or given an invented vertical. `dimensionality` is v1.1.0 vocabulary and
    # the locked v1.0 geo def is additionalProperties:false over lat/lon/alt_m,
    # so that branch must stamp 1.1.0 or it is schema-invalid. A full 3-D
    # position keeps the 1.0 stamp unchanged.
    if alt_hae_m is not None:
        geo = {"lat": lat, "lon": lon, "alt_m": alt_hae_m}
        needs_1_1_0 = False
    else:
        geo = {"lat": lat, "lon": lon, "dimensionality": "2D"}
        needs_1_1_0 = True
    confidence = _gps_fix_confidence(fix_for_decisions)

    quality = {}
    if gps_fix_type is not None:
        quality["gps_fix_type"] = gps_fix_type
    # GPS_RAW_INT.satellites_visible is uint8 with UINT8_MAX documented as
    # "if unknown"; 255 is the sentinel, never a 255-satellite measurement.
    # Guarded here as well as in decode_gps_raw_int because the state dict can
    # be assembled by any MAVLink bridge, the same way the battery sentinels
    # below are guarded on both sides.
    if _uint8_measurement_or_none(satellites_visible) is not None:
        quality["satellites_visible"] = satellites_visible
    # Coherence arm 2 (schema/zmeta-event-1.1.0.schema.json, doctrine A1-02)
    # refuses a declared 2-D geo beside geo_status AVAILABLE, so a status-only
    # consumer cannot read a horizontal-only fix as a full one. STALE keeps
    # priority on the degraded branch because staleness has no other carrier in
    # this payload, while the 2-D fact still travels in geo.dimensionality.
    if fix_for_decisions < 3:
        quality["geo_status"] = "STALE"
    elif needs_1_1_0:
        quality["geo_status"] = "VERTICAL_UNAVAILABLE"
    else:
        quality["geo_status"] = "AVAILABLE"
    if alt_hae_m is None and alt_msl_m is not None:
        # The reported vertical is preserved as non-canonical source context
        # rather than discarded, the same treatment a heading with no declared
        # frame gets in quality.mavlink_hdg_frame_unknown_deg below. A consumer
        # that knows its own geoid model can still use it; nothing downstream
        # can mistake it for canonical HAE.
        quality["mavlink_alt_msl_m"] = alt_msl_m

    # Optional attitude fields
    for attr in ("roll_deg", "pitch_deg", "yaw_deg", "vx", "vy", "vz"):
        val = _get(attr)
        if val is not None:
            quality[attr] = val

    # Optional battery/mode fields
    battery_v = _battery_voltage_or_none(_get("battery_voltage"))
    if battery_v is not None:
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
        "zmeta_version": "1.1.0" if needs_1_1_0 else "1.0",
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

    The decoded altitude is named ``alt_msl_m``, not ``alt_m``. MAVLink defines
    GLOBAL_POSITION_INT.alt as height above mean sea level, and contract 6.2
    permits only Height Above Ellipsoid in canonical geo, so this value is not
    eligible for ``payload.geo.alt_m`` and the name says so at the boundary.
    A caller wanting a canonical 3-D position supplies ``alt_hae_m``, which
    decode_gps_raw_int derives from GPS_RAW_INT.alt_ellipsoid.

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
    # GLOBAL_POSITION_INT.alt is documented by MAVLink as "Altitude (MSL)", so
    # it decodes to alt_msl_m and never to the canonical alt_m name. HAE comes
    # from GPS_RAW_INT.alt_ellipsoid, decoded in decode_gps_raw_int.
    alt_msl_m = alt_raw / 1000.0 if alt_raw is not None else None
    vx = vx_raw / 100.0 if vx_raw is not None else None
    vy = vy_raw / 100.0 if vy_raw is not None else None
    vz = vz_raw / 100.0 if vz_raw is not None else None
    hdg_cdeg = msg_dict.get("hdg", 65535)
    heading_deg = hdg_cdeg / 100.0 if hdg_cdeg != 65535 else None
    speed_mps = math.sqrt(vx ** 2 + vy ** 2) if vx is not None and vy is not None else None
    return {
        "lat": lat,
        "lon": lon,
        "alt_msl_m": alt_msl_m,
        "heading_deg": heading_deg,
        "speed_mps": speed_mps,
        "vx": vx,
        "vy": vy,
        "vz": vz,
    }


def decode_attitude(msg_dict):
    """Extract attitude from ATTITUDE fields (radians -> degrees).

    An axis the message does not report decodes to explicit ``None``, never to
    0.0 degrees (which would assert a measured level attitude the autopilot
    never reported) and never to an omitted key.

    The omitted-key form was the earlier behaviour and it was wrong in the
    documented accumulation pattern (``state.update(decode_attitude(...))``,
    README): an omitted key leaves the *previous* message's roll in the state
    dict, and ``translate_platform_state`` then publishes it in
    ``payload.quality.roll_deg`` as a current reading with no per-field
    staleness marker. Stale-presented-as-current is the same laundering class
    as fabricated-as-measured. Explicit ``None`` clobbers instead - the value
    is dropped from the emitted quality block, which degrades the event and
    never cleans it up - and it makes this decoder agree with
    ``decode_global_position_int``, which already returns ``None`` per absent
    field for exactly this reason.
    """
    decoded = {}
    for field, key in (("roll", "roll_deg"), ("pitch", "pitch_deg"), ("yaw", "yaw_deg")):
        value = msg_dict.get(field)
        if value is None:
            decoded[key] = None
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
    satellites_visible = _uint8_measurement_or_none(msg_dict.get("satellites_visible"))
    if satellites_visible is not None:
        decoded["satellites_visible"] = satellites_visible
    # GPS_RAW_INT.alt_ellipsoid is documented by MAVLink as "Altitude (above
    # WGS84, EGM96 ellipsoid)", which is the HAE datum contract 6.2 requires,
    # so it is the only MAVLink altitude that may reach canonical geo.alt_m.
    # An absent field decodes to an omitted key, never to 0.0, on the same rule
    # as every other value in this module: translate_platform_state then falls
    # back to the declared 2-D form rather than inventing a vertical.
    alt_ellipsoid_raw = msg_dict.get("alt_ellipsoid")
    if alt_ellipsoid_raw is not None:
        decoded["alt_hae_m"] = alt_ellipsoid_raw / 1000.0
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

    ``payload.state`` is never invented on any of the three branches, and it is
    never accepted uninterpreted either.

    The acknowledgement verdict must be message-carried *and* be a member of
    the v1.0 TASK_ACK vocabulary. Presence is tested by carrier key, so a
    carried MAVLink code of 0 - MAV_MISSION_ACCEPTED / MAV_RESULT_ACCEPTED - is
    not mistaken for a missing verdict; it is refused as unmappable, with a
    message that says so. The vocabulary has no "unknown" member to degrade
    into, so both failures refuse rather than report a RECEIVED nobody sent.
    The five negative verdicts carry the ``metrics.reason_code`` the v1.0
    schema requires on them: the message's own when it carried a vocabulary
    member, else the code that restates the verdict itself (``TASK_REJECTED``
    for REJECTED, and so on - a restatement, not a diagnosis). An
    out-of-vocabulary carried cause, or a cause under a clean verdict, is
    refused - never silently dropped and never emitted schema-invalid.

    The TIME_STATUS verdict is derived from the carried sync state by the same
    ``_time_status_payload_state`` ``translate_time_status`` uses, so the two
    never disagree, and a carried verdict outside that function's declared
    ordering is refused rather than published over a metrics block it may
    contradict.

    The LINK_STATUS fallback verdict stays "UNKNOWN" - the schema's honest
    label for a message that said nothing about link health - but a carried
    ``state``/``link_state`` is normalised onto the v1.0 vocabulary and
    refused when uninterpretable. The three link measurements the schema
    requires (``latency_ms``/``packet_loss_pct``/``throughput_bps``) are
    message-carried and refused when absent, and ``reason_code`` follows the
    same rules ``translate_link_status`` enforces (a declared vocabulary,
    required under DEGRADED/DOWN, contradictory under UP).
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
        carried_key = None
        carried_state = None
        for key in _TASK_ACK_CARRIER_KEYS:
            if key in msg and msg[key] is not None:
                carried_key = key
                carried_state = msg[key]
                break
        task_id = msg.get("task_id")
        original_event_id = (
            msg.get("original_event_id")
            or msg.get("command_event_id")
            or msg.get("event_id")
        )
        if task_id is None or original_event_id is None:
            raise ValueError("TASK_ACK requires task_id and original_event_id")
        if carried_key is None:
            raise ValueError(
                "TASK_ACK requires a message-carried ack state; an "
                "acknowledgement verdict is never fabricated"
            )
        state = _normalize_vocabulary_token(carried_state, _TASK_ACK_STATES)
        if state is None:
            # Presence is tested by key above and interpretability here, so the
            # two failures get two different, true messages. Truthiness cannot
            # do this job: MAV_MISSION_ACCEPTED and MAV_RESULT_ACCEPTED are
            # both the integer 0, so a falsy test reports "no verdict carried"
            # about precisely the successful acknowledgements and destroys them.
            #
            # A raw MAVLink result code is refused rather than mapped, and that
            # is deliberate: 0 means ACCEPTED under MISSION_ACK.type and
            # COMMAND_ACK.result but UNKNOWN under MISSION_CURRENT.mission_state,
            # and this dict does not say which enum the integer came from.
            # Guessing an acceptance is the one direction that must never be
            # guessed - a commander reads it as the vehicle having taken the
            # task. The bridge holds the message type; it maps the code.
            raise ValueError(
                f"TASK_ACK carrier {carried_key!r} carried {carried_state!r}, which is "
                f"not one of the v1.0 TASK_ACK states ({'/'.join(_TASK_ACK_STATES)}); "
                "map the MAVLink result code to a ZMeta verdict in the bridge - an "
                "acknowledgement verdict is never fabricated and never guessed"
            )
        # The five negative verdicts require metrics.reason_code (the
        # conditional obligation attached to the state enum the tuple above
        # mirrors). A message-carried cause is never silently dropped: a
        # vocabulary member beats the restating default because it says more
        # than the verdict does, an out-of-vocabulary one refuses, and a
        # failure cause under a clean verdict refuses as self-contradictory -
        # the TASK_ACK spelling of "UP cannot carry a cause of degradation".
        carried_reason = msg.get("reason_code")
        reason_code = None
        if carried_reason is not None:
            reason_code = _normalize_vocabulary_token(carried_reason, _TASK_ACK_REASON_CODES)
            if reason_code is None:
                raise ValueError(
                    f"TASK_ACK carried reason_code {carried_reason!r}, which is "
                    f"not one of the v1.0 TASK_ACK reason codes "
                    f"({'/'.join(_TASK_ACK_REASON_CODES)}); map the MAVLink "
                    "failure cause in the bridge - a carried cause is never "
                    "silently dropped and never emitted schema-invalid"
                )
            if state not in _TASK_ACK_REASON_REQUIRED:
                raise ValueError(
                    f"TASK_ACK state {state} cannot carry metrics.reason_code "
                    f"({reason_code!r}): the v1.0 reason vocabulary is causes of "
                    "non-execution, and a clean verdict with a failure cause "
                    "contradicts itself. Which half the message meant is not "
                    "adjudicable here, so neither half is silently corrected"
                )
        if reason_code is None and state in _TASK_ACK_REASON_REQUIRED:
            reason_code = _TASK_ACK_REASON_REQUIRED[state]
        metrics = {
            "task_id": task_id,
            "original_event_id": original_event_id,
        }
        if reason_code is not None:
            metrics["reason_code"] = reason_code
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

    # The three link measurements the v1.0 schema requires on every
    # LINK_STATUS payload are message-carried and never defaulted - the same
    # refusal translate_link_status applies to its keyword arguments
    # (hard-coding 0 ms / 0.0 % / 0 bps would report a perfect, fully-measured
    # link on a node whose comms were never measured at all).
    latency_ms = msg.get("latency_ms")
    packet_loss_pct = msg.get("packet_loss_pct")
    throughput_bps = msg.get("throughput_bps")
    if latency_ms is None or packet_loss_pct is None or throughput_bps is None:
        raise ValueError(
            "LINK_STATUS requires measured latency_ms, packet_loss_pct and "
            "throughput_bps; link health is never fabricated"
        )

    # A message-carried verdict is normalised onto the v1.0 vocabulary and
    # refused when uninterpretable - never forwarded verbatim for the
    # gateway's schema enum to catch. An absent or blank verdict is not an
    # uninterpretable one: it means the message said nothing about link
    # health, and "UNKNOWN" is the schema's own honest label for that, so the
    # fallback stays "UNKNOWN".
    carried_state = None
    for key in ("state", "link_state"):
        value = msg.get(key)
        if value is None or (isinstance(value, str) and not value.strip()):
            continue
        carried_state = value
        break
    if carried_state is None:
        state = "UNKNOWN"
    else:
        state = _normalize_vocabulary_token(carried_state, _LINK_STATUS_STATES)
        if state is None:
            raise ValueError(
                f"LINK_STATUS carried state {carried_state!r}, which is not one "
                f"of the v1.0 LINK_STATUS states ({'/'.join(_LINK_STATUS_STATES)}); "
                "map the upstream label in the bridge - link health is never "
                "accepted uninterpreted and never guessed"
            )

    # Same reason_code rules as translate_link_status: a declared vocabulary,
    # required under DEGRADED/DOWN, contradictory under UP - and still
    # permitted under UNKNOWN ("I observed this and I am not adjudicating
    # health" is an honest pair).
    carried_reason = msg.get("reason_code")
    reason_code = None
    if carried_reason is not None:
        reason_code = _normalize_vocabulary_token(carried_reason, _LINK_STATUS_REASON_CODES)
        if reason_code is None:
            raise ValueError(
                f"LINK_STATUS carried reason_code {carried_reason!r}; "
                f"metrics.reason_code must be one of "
                f"{'/'.join(_LINK_STATUS_REASON_CODES)}; link health is never fabricated"
            )
        if state == "UP":
            raise ValueError(
                "LINK_STATUS state UP cannot carry metrics.reason_code "
                f"({reason_code!r}): a healthy link has no cause of degradation. "
                "Supply DEGRADED/DOWN, or UNKNOWN to report the observation "
                "without adjudicating link health"
            )
    if state in ("DEGRADED", "DOWN") and reason_code is None:
        raise ValueError(
            "LINK_STATUS state DEGRADED/DOWN requires metrics.reason_code"
        )

    # The link identity is the message's own when it carried a usable one,
    # else the same declared default translate_link_status writes - an
    # identifier this adapter assigns, not a measurement it invents.
    link_id = msg.get("link_id")
    if not (isinstance(link_id, str) and link_id.strip()):
        link_id = f"edge-comms-{platform_id}"

    metrics = {
        "link_id": link_id,
        "latency_ms": latency_ms,
        "packet_loss_pct": packet_loss_pct,
        "throughput_bps": throughput_bps,
    }
    # RADIO_STATUS.rssi carries the same uint8 UINT8_MAX "invalid/unknown"
    # convention as RC_CHANNELS.rssi and GPS_RAW_INT.satellites_visible.
    # (snr and drop_rate below are left as carried: neither SYS_STATUS
    # drop_rate_comm nor any common-message snr field declares a sentinel.)
    if _uint8_measurement_or_none(msg.get("rssi")) is not None:
        metrics["rssi"] = msg["rssi"]
    if "snr" in msg:
        metrics["snr"] = msg["snr"]
    if "drop_rate" in msg:
        metrics["drop_rate"] = msg["drop_rate"]
    if reason_code is not None:
        metrics["reason_code"] = reason_code

    return [
        _make_event("LINK_STATUS", state, platform_id=platform_id, producer=producer, ts=ts, metrics=metrics)
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

    ``reason_code`` is checked against the v1.0 vocabulary, not merely for
    presence, and it may not accompany ``state="UP"`` - a healthy link with a
    cause of degradation contradicts itself in the field the operator reads
    first. Both are refusals, not silent corrections.

    ``battery_voltage``, ``battery_pct`` and ``rc_rssi`` are optional; when
    unreported they are omitted rather than emitted as 0 V / -1 % / 0 RSSI,
    and each is guarded against its documented MAVLink sentinel on this side
    too (``rc_rssi = 255`` is UINT8_MAX "invalid/unknown", ``battery_voltage =
    65.535`` is UINT16_MAX "voltage not sent"), because these are bare keyword
    arguments with no decoder in front of them.

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
    if reason_code is not None:
        # Presence was enforced and the value was not, on a path that only
        # became reachable when `state` stopped being hard-coded - so a
        # DEGRADED could still be emitted schema-invalid. Same treatment as
        # `state` above: a declared vocabulary, refused rather than emitted.
        if reason_code not in _LINK_STATUS_REASON_CODES:
            raise ValueError(
                f"LINK_STATUS metrics.reason_code must be one of "
                f"{'/'.join(_LINK_STATUS_REASON_CODES)}; link health is never fabricated"
            )
        # A cause of degradation under a state that says the link is healthy is
        # the same self-contradiction as a SYNCED clock over an UNSYNCED
        # metrics block, and the operator reads the state first. Which of the
        # two the caller meant is not adjudicable here, so neither is silently
        # dropped. UNKNOWN is deliberately still permitted: "I observed high
        # latency and I am not adjudicating health" is an honest pair.
        if state == "UP":
            raise ValueError(
                "LINK_STATUS state UP cannot carry metrics.reason_code "
                f"({reason_code!r}): a healthy link has no cause of degradation. "
                "Supply DEGRADED/DOWN, or UNKNOWN to report the observation "
                "without adjudicating link health"
            )
    metrics = {
        "link_id": f"edge-comms-{platform_id}",
        "active_link": active_link,
        "latency_ms": latency_ms,
        "packet_loss_pct": packet_loss_pct,
        "throughput_bps": throughput_bps,
    }
    # Every optional metric below is guarded on this side too: these are bare
    # keyword arguments with no decoder in front of them, so this is the only
    # side there is.
    if _battery_voltage_or_none(battery_voltage) is not None:
        metrics["battery_voltage"] = battery_voltage
    if battery_pct is not None and battery_pct >= 0:
        metrics["battery_remaining_pct"] = battery_pct
    if _uint8_measurement_or_none(rc_rssi) is not None:
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
