"""Decoded AIS position reports -> ZMeta OBSERVATION_EVENT.

AIS is a **cooperative broadcast**, like ADS-B: a vessel transmits its own
identity, position and motion on VHF and a receiver decodes it. Almost nothing
here is our measurement, and that shapes every decision in this file.

Input is a decoded message dict, as produced by AIS-catcher's JSON output (the
common RTL-SDR decoder, same dongle as ADS-B). Raw NMEA `!AIVDM` sentences are
out of scope: decode first. See the adapter README for the field mapping.

THE ALTITUDE PROBLEM, WHICH IS THE WHOLE STORY HERE
---------------------------------------------------
Canonical `payload.geo` requires `lat`, `lon` AND `alt_m` together (contract
6.8, all-or-nothing). **A vessel has no altitude.** Not "missing", not "not
reported": a surface vessel has no meaningful height above the ellipsoid, and
the AIS message has no field for one.

Substituting zero would be the worst option available. `alt_m` is height above
the WGS-84 ellipsoid (contract 6.1/6.2), and the geoid departs from the
ellipsoid by up to about 100 m, so "sea level" is not ellipsoid zero anywhere on
Earth. Writing 0.0 would assert a geometric height nobody measured, in a field a
consumer is entitled to read as measured.

So **every AIS observation omits canonical geo**, and the real horizontal
position is demoted to explicitly named native features. This is not an edge
case the way barometric-only ADS-B is an edge case. It is every vessel, every
message, always. Recorded as doctrine A1-02, for which this adapter is the
independent second implementation.

A CONSEQUENCE WORTH SEEING: the position accuracy AIS declares has nowhere to
go either. The accuracy bit is a real, standard-defined statement (better or
worse than 10 m), and `quality.error_ellipse_m` attaches to a canonical geo that
does not exist here. It is carried natively and cannot be canonical.

ON `geo_status`
---------------
When canonical geo is omitted, this sets `quality.geo_status = "UNAVAILABLE"`,
matching the ADS-B adapter. Read it as the status of the canonical geo object,
which is genuinely unavailable, and not as a claim that the position is unknown,
because it is not: it is in the native features, exact as broadcast. The
contract's vocabulary (`AVAILABLE`, `UNAVAILABLE`, `ESTIMATED`, `STALE`,
`CONFIGURED`) has no token for "horizontally known, vertically absent", so the
least-wrong one is used and the ambiguity is recorded rather than papered over.

WHY MODALITY IS `NETWORK` AND NOT `RF`
--------------------------------------
Same reasoning as the ADS-B adapter, and the same modelling judgement rather
than a settled rule. Contract 7.4 gives RF a normative minimum feature set
including `power_dbm`, and a decoder reports received signal power in
uncalibrated dB relative to its own chain. Emitting that as `power_dbm` is the
laundering the contract forbids, so the observation is modelled as the decoded
`NETWORK` message and signal power is carried as `ais_signal_power_db`.

WHY `OBSERVATION_EVENT` AND NOT `STATE_EVENT`
---------------------------------------------
STATE_EVENT lineage is mandatory and must reference real parents; an AIS
receiver has no ZMeta parent, it is an original observation of a broadcast.
`adapters/projector/track` is what turns these into tracks, and its `mmsi`
identity path exists for this adapter.

WHAT IS NEVER INFERRED
----------------------
MMSI encodes country and service in its leading digits, `shiptype` is a declared
code, and navigation status is a declared enum. None of them becomes a ZMeta
classification or identity here: an OBSERVATION_EVENT carrying identity or
classification is an authority-boundary violation the kernel refuses. They are
the vessel's own claims, carried natively, for an inference stage to adjudicate.
"""

from __future__ import annotations

from adapters.ingress.time_utils import coerce_timing_quality, epoch_ms_to_utc_z

ADAPTER_VERSION = "1.0.0"
DEFAULT_PRODUCER = "rf-sensor-ais-01"

# AIS marine band. Carried natively as context, never as an RF measurement.
AIS_CHANNEL_A_HZ = 161975000
AIS_CHANNEL_B_HZ = 162025000

# Message types that carry a position report. Static and voyage data (5, 24)
# carry name and dimensions but no position, so they produce no observation on
# their own; a decoder that merges them into a position report is welcome to,
# and the merged fields are carried natively.
POSITION_REPORT_TYPES = frozenset({1, 2, 3, 18, 19, 27})

# ITU-R M.1371 "not available" sentinels. These are not missing data, they are
# the standard's explicit way of saying the field is not being reported, and
# carrying them as values would fabricate a vessel stopped dead on a due-north
# heading.
SOG_NOT_AVAILABLE = 102.3
COG_NOT_AVAILABLE = 360.0
HEADING_NOT_AVAILABLE = 511
LAT_NOT_AVAILABLE = 91.0
LON_NOT_AVAILABLE = 181.0
# `second` 60 means the timestamp is unavailable; 61-63 encode positioning-system
# states (manual, dead reckoning, inoperative) rather than a second-of-minute.
SECOND_NOT_A_TIME = frozenset({60, 61, 62, 63})


def _finite(value):
    """A real number, or None. Bools are not numbers here."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if value != value or value in (float("inf"), float("-inf")):
        return None
    return float(value)


def _positive_int(value):
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value if value > 0 else None


def _clean_text(value):
    """AIS pads text fields with @ and spaces; neither is content."""
    if not isinstance(value, str):
        return None
    text = value.replace("@", " ").strip()
    return text or None


def _position(msg):
    """The broadcast horizontal position, or None.

    Returns a (lat, lon) pair. It is deliberately NOT canonical geo: see the
    module docstring. A vessel has no altitude, so `payload.geo` is never built.
    """
    lat = _finite(msg.get("lat"))
    lon = _finite(msg.get("lon"))
    if lat is None or lon is None:
        return None
    # The standard's own not-available encodings, which are in range for a
    # naive bounds check and would otherwise place a vessel at the north pole.
    if abs(lat - LAT_NOT_AVAILABLE) < 1e-6 or abs(lon - LON_NOT_AVAILABLE) < 1e-6:
        return None
    if not (-90.0 <= lat <= 90.0) or not (-180.0 <= lon <= 180.0):
        return None
    return lat, lon


def _event_ts(msg, now_epoch_s):
    """The receiver's time of reception, or None to refuse the message.

    The AIS `second` field is a second-of-minute, not a timestamp: it cannot
    date a message on its own and is carried natively instead. Reception time
    comes from the decoder (`rxtime`) or from the caller.
    """
    rxtime = msg.get("rxtime")
    if isinstance(rxtime, str) and len(rxtime) == 14 and rxtime.isdigit():
        # AIS-catcher's rxtime is YYYYMMDDHHMMSS in UTC.
        return (f"{rxtime[0:4]}-{rxtime[4:6]}-{rxtime[6:8]}T"
                f"{rxtime[8:10]}:{rxtime[10:12]}:{rxtime[12:14]}.000Z")
    epoch = _finite(msg.get("timestamp"))
    if epoch is not None:
        return epoch_ms_to_utc_z(epoch * 1000.0)
    epoch = _finite(now_epoch_s)
    if epoch is not None:
        return epoch_ms_to_utc_z(epoch * 1000.0)
    return None


def _native_features(msg, mmsi, receiver_id, position):
    """Everything AIS asserts, under explicitly named native keys."""
    features = {
        "ais_mmsi": mmsi,
        "ais_channel_a_hz": AIS_CHANNEL_A_HZ,
        "ais_channel_b_hz": AIS_CHANNEL_B_HZ,
    }
    if receiver_id is not None:
        features["ais_receiver_id"] = str(receiver_id)

    msg_type = msg.get("type")
    if isinstance(msg_type, int) and not isinstance(msg_type, bool):
        features["ais_message_type"] = msg_type

    if position is not None:
        # The real position, demoted rather than discarded. Canonical geo
        # cannot hold it because a vessel has no altitude.
        features["ais_lat_deg"], features["ais_lon_deg"] = position

    sog = _finite(msg.get("speed"))
    if sog is not None and abs(sog - SOG_NOT_AVAILABLE) > 1e-6:
        features["ais_sog_kt"] = sog
    cog = _finite(msg.get("course"))
    if cog is not None and abs(cog - COG_NOT_AVAILABLE) > 1e-6:
        features["ais_cog_deg_true"] = cog
    heading = msg.get("heading")
    if isinstance(heading, int) and not isinstance(heading, bool) and heading != HEADING_NOT_AVAILABLE:
        if 0 <= heading <= 359:
            features["ais_heading_deg_true"] = heading

    status = msg.get("status")
    if isinstance(status, int) and not isinstance(status, bool) and 0 <= status <= 15:
        # The vessel's declared navigation status, as a code. Not translated
        # into a ZMeta behaviour or classification: that is an inference.
        features["ais_nav_status_code"] = status

    accuracy = msg.get("accuracy")
    if isinstance(accuracy, bool):
        # A one-bit declaration: better than 10 m, or not. Carried as declared.
        # It has no canonical home, because quality.error_ellipse_m attaches to
        # a geo object this adapter never builds.
        features["ais_position_accuracy_high"] = accuracy

    second = msg.get("second")
    if isinstance(second, int) and not isinstance(second, bool):
        if second in SECOND_NOT_A_TIME:
            features["ais_second_status"] = second
        elif 0 <= second <= 59:
            features["ais_second_of_minute"] = second

    power = _finite(msg.get("signalpower"))
    if power is not None:
        # Uncalibrated, receiver-relative. Never power_dbm (contract 7.4).
        features["ais_signal_power_db"] = power

    for key, field in (("shipname", "ais_shipname"), ("callsign", "ais_callsign")):
        text = _clean_text(msg.get(key))
        if text:
            features[field] = text
    shiptype = msg.get("shiptype")
    if isinstance(shiptype, int) and not isinstance(shiptype, bool) and shiptype > 0:
        features["ais_shiptype_code"] = shiptype

    return features


def translate_message(
    msg,
    *,
    platform_id,
    now_epoch_s=None,
    producer=DEFAULT_PRODUCER,
    receiver_id=None,
    sensor_id=None,
    timing_quality=None,
):
    """Translate one decoded AIS message into a ZMeta OBSERVATION_EVENT.

    Args:
        msg: one decoded AIS message dict (AIS-catcher JSON shape).
        platform_id: the deployment's platform identifier.
        now_epoch_s: fallback reception time when the message carries none.
        producer: must satisfy producer-authority policy; the reference
            wildcards include ``rf-sensor-*``.
        receiver_id: optional receiver identifier, recorded natively.
        sensor_id: optional ZMeta ``source.sensor_id``; omitted when absent
            rather than invented.
        timing_quality: real clock metadata when the deployment has it.
            Absent, the governed degraded fallback is used.

    Returns:
        The event dict, or ``None`` when the message cannot honestly become
        one: not a position report, no MMSI (no subject), or no usable
        reception time.
    """
    if not isinstance(msg, dict):
        return None

    msg_type = msg.get("type")
    if not isinstance(msg_type, int) or isinstance(msg_type, bool):
        return None
    if msg_type not in POSITION_REPORT_TYPES:
        return None

    # MMSI is the subject. Without it there is nothing to observe about.
    mmsi = _positive_int(msg.get("mmsi"))
    if mmsi is None:
        return None

    event_ts = _event_ts(msg, now_epoch_s)
    if event_ts is None:
        return None

    position = _position(msg)

    payload = {
        "modality": "NETWORK",
        "features": _native_features(msg, mmsi, receiver_id, position),
        "timing_quality": coerce_timing_quality(timing_quality, event_ts=event_ts),
        # Canonical geo is never built: a vessel has no alt_m. UNAVAILABLE
        # describes the canonical geo object, not our knowledge of position,
        # which is in the native features above.
        "quality": {"geo_status": "UNAVAILABLE"},
    }

    source = {"platform_id": platform_id, "node_role": "EDGE", "producer": producer}
    if sensor_id is not None:
        source["sensor_id"] = str(sensor_id)

    return {
        "zmeta_version": "1.0",
        "event": {
            "event_id": _new_event_id(),
            "event_type": "OBSERVATION_EVENT",
            "event_subtype": "NETWORK",
            "ts": event_ts,
        },
        "source": source,
        "payload": payload,
    }


def _new_event_id():
    from zmeta_uuid import uuid7
    return str(uuid7())


def translate_stream(messages, *, platform_id, **kwargs):
    """Translate an iterable of decoded AIS messages.

    Messages that cannot honestly become events are dropped, not patched. The
    count of refusals is the caller's to observe: an adapter that invents a
    position to keep its yield up is the failure mode this file exists to
    avoid.
    """
    if not isinstance(messages, (list, tuple)):
        return []
    events = []
    for msg in messages:
        event = translate_message(msg, platform_id=platform_id, **kwargs)
        if event is not None:
            events.append(event)
    return events
