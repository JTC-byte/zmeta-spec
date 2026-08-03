"""Decoded AIS position reports -> ZMeta OBSERVATION_EVENT.

AIS is a **cooperative broadcast**, like ADS-B: a vessel transmits its own
identity, position and motion on VHF and a receiver decodes it. Almost nothing
here is our measurement, and that shapes every decision in this file.

Input is a decoded message dict, as produced by AIS-catcher's JSON output (the
common RTL-SDR decoder, same dongle as ADS-B). Raw NMEA `!AIVDM` sentences are
out of scope: decode first. See the adapter README for the field mapping.

THE ALTITUDE PROBLEM, WHICH WAS THE WHOLE STORY UNDER v1.0
----------------------------------------------------------
Canonical `payload.geo` under the locked v1.0 kernel requires `lat`, `lon` AND
`alt_m` together (contract 6.8, all-or-nothing). **A vessel has no altitude.**
Not "missing", not "not reported": a surface vessel has no meaningful height
above the ellipsoid, and the AIS message has no field for one.

Substituting zero would be the worst option available. `alt_m` is height above
the WGS-84 ellipsoid (contract 6.1/6.2), and the geoid departs from the
ellipsoid by up to about 100 m, so "sea level" is not ellipsoid zero anywhere on
Earth. Writing 0.0 would assert a geometric height nobody measured, in a field a
consumer is entitled to read as measured.

That was doctrine A1-02's wall, and this adapter was its independent second
implementation: every AIS observation with a usable position demoted that exact
position to native features and omitted canonical geo entirely, because v1.0
had no honest way to say "horizontal fix, no vertical" in the canonical field.
It was not an edge case the way barometric-only ADS-B is an edge case. It was
every vessel, every message, always.

`schema/zmeta-event-1.1.0.schema.json` removed the wall. `geo.dimensionality`
declares a position `"2D"` (absent means 3D), which prohibits `alt_m` outright
and pairs with `quality.geo_status: "VERTICAL_UNAVAILABLE"`. A vessel's
position is exactly that shape, a real, exact horizontal fix with no
geometric vertical to assert, ever, and a message with a usable position now
gets a canonical home for it: `payload.geo` as the declared 2-D form, with the
event stamped `zmeta_version "1.1.0"`. A message with no usable position still
omits `geo` entirely and stays on the locked v1.0 branch (`geo_status:
UNAVAILABLE`, no `geo` key), because nothing 1.1.0-only is being asserted and
nothing forces the newer stamp. A deployment validating strictly against the
locked v1.0 kernel rather than the 1.1.0 schema never sees the 2-D form and
keeps the full demotion this section used to describe unconditionally.

`ais_lat_deg`/`ais_lon_deg` are still carried natively on every positioned
message, on both branches: they are the exact as-broadcast record, independent
of what canonical geo says, and existing consumers already read them there.

A CONSEQUENCE WORTH SEEING: the position accuracy AIS declares still has
nowhere canonical to go. The accuracy bit is a real, standard-defined statement
(better or worse than 10 m), but it is one bit, not a radius category, and
`quality.error_ellipse_m` (schema/zmeta-event-1.1.0.schema.json) requires a
formal radius this adapter is not willing to invent from a boolean, so it stays
`ais_position_accuracy_high`, a native feature, whether or not the position
next to it is now canonical.

ON `geo_status`
---------------
When canonical geo is omitted, this sets `quality.geo_status = "UNAVAILABLE"`:
there is no canonical geo object to describe, matching the ADS-B adapter's
positionless case. When a usable position is present, this sets
`quality.geo_status = "VERTICAL_UNAVAILABLE"` (doctrine A1-02, coherence arm 1,
schema/zmeta-event-1.1.0.schema.json): the horizontal fix is real, canonical
and two-dimensional, and the vertical component genuinely does not exist for a
surface vessel rather than being merely unmeasured. `AVAILABLE` is never used
here: a vessel's canonical geo is never three-dimensional, so the token that
pairs with a full 3-D position never applies.

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

from datetime import datetime

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
# Message 27 packs speed and course into smaller fields with their own
# not-available encodings: 63 for speed, 511 for course. 63 kt is a real
# speed in a Class A report, so these are checked only for type 27.
TYPE27_SOG_NOT_AVAILABLE = 63.0
TYPE27_COG_NOT_AVAILABLE = 511.0
# The fields themselves bound what a real report can say: speed 0 to 102.2 kt,
# course 0 to 359.9 degrees, and for message 27 speed 0 to 62 kt, because its
# speed field is six bits. A decoded value outside the sending field's bounds
# is not an AIS claim, it is corruption, and it is dropped rather than carried.
SOG_MAX_KT = 102.2
TYPE27_SOG_MAX_KT = 62.0
# A number under `timestamp` is read as epoch seconds only when it could be
# one. Below this floor it is some other quantity that leaked in under that
# name (an AIS second-of-minute is the live example), and reading it as epoch
# seconds would date the event near 1970-01-01.
EPOCH_FLOOR_S = 946_684_800.0  # 2000-01-01T00:00:00Z
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

    Returns a (lat, lon) pair. It is the same pair `_geo` builds the declared
    2-D canonical position from, and that `_native_features` carries as
    `ais_lat_deg`/`ais_lon_deg` regardless: the native keys are the exact
    as-broadcast record, independent of what canonical geo says.
    """
    lat = _finite(msg.get("lat"))
    lon = _finite(msg.get("lon"))
    if lat is None or lon is None:
        return None
    # The standard's own not-available encodings. They would also fail the
    # bounds check below, but they are refused here by name: 91.0 and 181.0
    # mean "not reported", which is a different fact from decoder garbage
    # that happens to be out of range.
    if abs(lat - LAT_NOT_AVAILABLE) < 1e-6 or abs(lon - LON_NOT_AVAILABLE) < 1e-6:
        return None
    if not (-90.0 <= lat <= 90.0) or not (-180.0 <= lon <= 180.0):
        return None
    return lat, lon


def _geo(position):
    """Canonical geo, or None to omit it entirely.

    A vessel never has a geometric altitude to assert, so canonical geo is
    never the 3-D form here; when the message carries a usable position, it
    is emitted as the declared 2-D form (`dimensionality: "2D"`, no `alt_m`,
    doctrine A1-02) rather than withheld. Geo is omitted entirely only when
    there is no honest position at all -- mirrors the ADS-B adapter's `_geo`
    (adapters/ingress/adsb/adsb_to_zmeta.py), which reaches the same 2-D form
    from the opposite direction (a real fix with no usable geometric
    altitude, rather than a subject with none to give).
    """
    if position is None:
        return None
    lat, lon = position
    return {"lat": lat, "lon": lon, "dimensionality": "2D"}


def _quality(geo):
    """Declared quality, carrying only what the message actually asserts."""
    if geo is None:
        # A real detection with no position. Say so rather than stay silent.
        return {"geo_status": "UNAVAILABLE"}
    # Canonical geo is present and, for a vessel, always two-dimensional: the
    # horizontal fix is real and the vertical component does not exist to
    # measure. Coherence arm 1 (schema/zmeta-event-1.1.0.schema.json, doctrine
    # A1-02) requires this token to pair with a declared 2-D geo; `_geo` never
    # produces any other shape, so the pairing always holds.
    return {"geo_status": "VERTICAL_UNAVAILABLE"}


def _epoch_s_to_utc_z(epoch_s):
    """Epoch seconds to UTC-Z, or None when the number cannot be a moment."""
    if epoch_s < EPOCH_FLOOR_S:
        return None
    try:
        return epoch_ms_to_utc_z(epoch_s * 1000.0)
    except (OverflowError, OSError, ValueError):
        return None


def _event_ts(msg, now_epoch_s):
    """The receiver's time of reception, or None to refuse the message.

    The AIS `second` field is a second-of-minute, not a timestamp: it cannot
    date a message on its own and is carried natively instead. Reception time
    comes from the decoder (`rxtime`) or from the caller.

    A time channel that is present but impossible refuses the message rather
    than sliding to the next clock. The `rxtime` channel is recognised by its
    AIS-catcher shape, fourteen digits: a recognised shape that does not parse
    as a calendar moment refuses the message, and any other shape under that
    key is not this adapter's channel and is treated as absent. A `timestamp`
    that is present but cannot be a moment refuses the message rather than
    sliding to the caller's clock.
    """
    rxtime = msg.get("rxtime")
    if isinstance(rxtime, str) and len(rxtime) == 14 and rxtime.isdigit():
        # AIS-catcher's rxtime is YYYYMMDDHHMMSS in UTC. Fourteen digits are
        # not necessarily a date: month 88 would slice into a string the
        # schema accepts as a timestamp, so the digits must parse as a
        # calendar moment before they are formatted as one.
        try:
            datetime.strptime(rxtime, "%Y%m%d%H%M%S")
        except ValueError:
            return None
        return (f"{rxtime[0:4]}-{rxtime[4:6]}-{rxtime[6:8]}T"
                f"{rxtime[8:10]}:{rxtime[10:12]}:{rxtime[12:14]}.000Z")
    epoch = _finite(msg.get("timestamp"))
    if epoch is not None:
        return _epoch_s_to_utc_z(epoch)
    epoch = _finite(now_epoch_s)
    if epoch is not None:
        return _epoch_s_to_utc_z(epoch)
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
        # The exact as-broadcast position, carried here regardless of what
        # canonical geo does with it: it is the same fix `_geo` may also emit
        # as the declared 2-D form, kept native so existing consumers of
        # these two keys keep reading them unchanged.
        features["ais_lat_deg"], features["ais_lon_deg"] = position

    sog = _finite(msg.get("speed"))
    if sog is not None:
        not_reported = abs(sog - SOG_NOT_AVAILABLE) < 1e-6 or (
            msg_type == 27 and abs(sog - TYPE27_SOG_NOT_AVAILABLE) < 1e-6
        )
        sog_max = TYPE27_SOG_MAX_KT if msg_type == 27 else SOG_MAX_KT
        if not not_reported and 0.0 <= sog <= sog_max:
            features["ais_sog_kt"] = sog
    cog = _finite(msg.get("course"))
    if cog is not None:
        not_reported = abs(cog - COG_NOT_AVAILABLE) < 1e-6 or (
            msg_type == 27 and abs(cog - TYPE27_COG_NOT_AVAILABLE) < 1e-6
        )
        if not not_reported and 0.0 <= cog < 360.0:
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
        # It still has no canonical home: quality.error_ellipse_m needs a
        # formal radius, and one bit is not a radius category, so this stays
        # native whether or not the position next to it is now canonical.
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
        reception time, where a time channel that is present but impossible
        counts as unusable rather than falling through to another clock.
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
    geo = _geo(position)
    # A usable position always uses v1.1.0-only geo vocabulary (the declared
    # 2-D form, doctrine A1-02): the locked v1.0 canonical geo def is
    # additionalProperties:false with only lat/lon/alt_m, so declaring
    # `dimensionality` on it is schema-invalid under v1.0. A positionless
    # message never touches that vocabulary and stays on the locked v1.0
    # branch, byte-for-byte what it always was.
    needs_1_1_0 = geo is not None

    features = _native_features(msg, mmsi, receiver_id, position)
    if needs_1_1_0:
        # The locked v1.0 kernel's NETWORK ObservationPayload imposes no
        # feature vocabulary of its own, but v1.1.0's does, and requires
        # `protocol` (schema/zmeta-event-1.1.0.schema.json). A positionless
        # message never leaves the v1.0 branch, so it never gains this key.
        features["protocol"] = "AIS"

    payload = {
        "modality": "NETWORK",
        "features": features,
        "timing_quality": coerce_timing_quality(timing_quality, event_ts=event_ts),
        # UNAVAILABLE describes the canonical geo object, not our knowledge of
        # position: when a position exists it is in the native features
        # above regardless, and now also canonically as the declared 2-D form
        # (see `_geo`/`_quality`) whenever it is usable.
        "quality": _quality(geo),
    }
    if geo is not None:
        payload["geo"] = geo

    source = {"platform_id": platform_id, "node_role": "EDGE", "producer": producer}
    if sensor_id is not None:
        source["sensor_id"] = str(sensor_id)

    return {
        "zmeta_version": "1.1.0" if needs_1_1_0 else "1.0",
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

    Any iterable of message dicts works, a generator included. A non-iterable
    raises, and so do the iterables that read as an accidental empty sea: a
    single message dict (which iterates as its keys) and a string (which
    iterates as its characters). Zero events from a miswired call must not
    look identical to zero events from an empty sea.

    Messages that cannot honestly become events are dropped, not patched. The
    count of refusals is the caller's to observe: an adapter that invents a
    position to keep its yield up is the failure mode this file exists to
    avoid.
    """
    if isinstance(messages, (dict, str, bytes)):
        raise TypeError(
            "translate_stream takes an iterable of decoded messages, not a "
            f"single {type(messages).__name__}; wrap one message in a list"
        )
    events = []
    for msg in messages:
        event = translate_message(msg, platform_id=platform_id, **kwargs)
        if event is not None:
            events.append(event)
    return events
