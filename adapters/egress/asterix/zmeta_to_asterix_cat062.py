"""ZMeta STATE_EVENT/TRACK_STATE to ASTERIX CAT062 egress adapter.

Encodes one ZMeta track state as one CAT062 system track record, and wraps
records in a CAT062 data block. CAT062 is EUROCONTROL's surveillance data
exchange category for system track data; this adapter follows edition 1.21
(EUROCONTROL-SPEC-0149-9), and the section and page citations below are to
that edition. The adapter opens no connection.

This is a lossy projection. ASTERIX_EGRESS_LOSS_NOTES below names every
concern a CAT062 record has no carrier for. ZMeta remains the source of truth,
and a re-import of the record is never equal to the event (semantics contract
4.5.1). Two rules decide every item:

  - No bit or item states a claim the event does not make. Where the format
    forces a value and every value is a claim, the caller declares it in the
    configuration, with no default.
  - Where the event states a value an item cannot carry, the event is refused
    with a reason the caller can count, and nothing is clamped. Where the
    rules leave an item out (a course without a speed, an ellipse that is not
    1_SIGMA, an ellipse at a pole), and where the format has no item for a
    member, the loss is named in the loss register.

The encoder is self-contained: the standard library's `struct` and integer
arithmetic. The timestamp parse is the CoT egress adapter's own, so the egress
adapters share one reading of `event.ts`.
"""

import math
import struct
from collections.abc import Mapping

from adapters.egress.cot.zmeta_to_cot import _parse_utc

ADAPTER_VERSION = "1.0.0"
CATEGORY = 62
EDITION = "1.21"

# The refusal reasons written to a caller's `refusal` dict. Each is written
# only by the refusal that fired.
REFUSAL_NOT_TRACK_STATE = "CAT062_NOT_TRACK_STATE"
REFUSAL_CONFIG_INVALID = "CAT062_CONFIG_INVALID"
REFUSAL_SIMULATED_UNSUPPORTED = "CAT062_SIMULATED_UNSUPPORTED"
REFUSAL_RISK_UNREADABLE = "CAT062_RISK_UNREADABLE"
REFUSAL_RISK_REJECTED = "CAT062_RISK_REJECTED"
REFUSAL_RISK_UNKNOWN_DECISION = "CAT062_RISK_UNKNOWN_DECISION"
REFUSAL_RISK_QUARANTINE_ACCEPT = "CAT062_RISK_QUARANTINE_ACCEPT"
REFUSAL_RISK_DEGRADED_ACCEPT = "CAT062_RISK_DEGRADED_ACCEPT"
REFUSAL_RISK_WARN_ACCEPT = "CAT062_RISK_WARN_ACCEPT"
REFUSAL_RISK_USE_RESTRICTED = "CAT062_RISK_USE_RESTRICTED"
REFUSAL_TIMING_HOLDOVER = "CAT062_TIMING_HOLDOVER"
REFUSAL_TIMING_UNSYNCED = "CAT062_TIMING_UNSYNCED"
REFUSAL_TIMING_ABSENT = "CAT062_TIMING_ABSENT"
REFUSAL_TIMING_MALFORMED = "CAT062_TIMING_MALFORMED"
REFUSAL_TIME_UNPARSEABLE = "CAT062_TIME_UNPARSEABLE"
REFUSAL_TRACK_UNMAPPED = "CAT062_TRACK_UNMAPPED"
REFUSAL_TRACK_NUMBER_INVALID = "CAT062_TRACK_NUMBER_INVALID"
REFUSAL_POSITION_INVALID = "CAT062_POSITION_INVALID"
REFUSAL_ALTITUDE_INVALID = "CAT062_ALTITUDE_INVALID"
REFUSAL_ALTITUDE_OUT_OF_RANGE = "CAT062_ALTITUDE_OUT_OF_RANGE"
REFUSAL_VELOCITY_INVALID = "CAT062_VELOCITY_INVALID"
REFUSAL_VELOCITY_OUT_OF_RANGE = "CAT062_VELOCITY_OUT_OF_RANGE"
REFUSAL_ACCURACY_INVALID = "CAT062_ACCURACY_INVALID"

# The policy decisions of `tools/filter_risk.py` DECISION_RANKS other than
# IGNORED. A CAT062 record has no carrier for a self-label, so every one of
# them is refused (semantics contract 3.3: soft acceptance must not make risky
# data look clean). Any other decision text, or none, ranks with REJECTED in
# that tool and is refused here as unknown.
_DECISION_REFUSALS = {
    "WARN_ACCEPT": REFUSAL_RISK_WARN_ACCEPT,
    "DEGRADED_ACCEPT": REFUSAL_RISK_DEGRADED_ACCEPT,
    "QUARANTINE_ACCEPT": REFUSAL_RISK_QUARANTINE_ACCEPT,
    "REJECTED": REFUSAL_RISK_REJECTED,
}
# The reason a refused event reports when several records refuse it: the most
# severe, in this order.
_RISK_SEVERITY = (
    REFUSAL_RISK_UNREADABLE,
    REFUSAL_RISK_REJECTED,
    REFUSAL_RISK_UNKNOWN_DECISION,
    REFUSAL_RISK_QUARANTINE_ACCEPT,
    REFUSAL_RISK_DEGRADED_ACCEPT,
    REFUSAL_RISK_WARN_ACCEPT,
    REFUSAL_RISK_USE_RESTRICTED,
)

# Field Reference Numbers of the items this adapter writes (§5.3, Table 1,
# pp. 131 and 132).
_FRN_010 = 1
_FRN_015 = 3
_FRN_070 = 4
_FRN_105 = 5
_FRN_185 = 7
_FRN_040 = 12
_FRN_080 = 13
_FRN_130 = 18
_FRN_500 = 27

# I062/070: 1/128 s since the last UTC midnight (§5.2.5, p. 11).
_TIME_COUNTS_PER_S = 128
# I062/105 and I062/500 APW: 180/2^25 degrees (§5.2.8, p. 24; §5.2.26, p. 126).
_POSITION_LSB_DEG = 180.0 / 2**25
# I062/105's ranges: -90 <= latitude <= 90 and -180 <= longitude < 180 (p. 24).
_LON_COUNT_LIMIT = 2**25
# I062/185: 0.25 m/s, two's complement, -8192 to 8191.75 m/s (§5.2.14, p. 39).
_VELOCITY_LSB_MPS = 0.25
_INT16_MIN = -(2**15)
_INT16_MAX = 2**15 - 1
# Above this speed one component exceeds 23,000 m/s whatever the course, far
# beyond the item, so the event is refused before arithmetic that could
# overflow. Below it the nearest-count range check decides.
_SPEED_LIMIT_MPS = 2.0**15
# I062/130: 6.25 ft, two's complement, -1,500 ft to 150,000 ft (§5.2.11, p. 36).
_ALTITUDE_LSB_M = 6.25 * 0.3048
_ALTITUDE_COUNT_MIN = -240
_ALTITUDE_COUNT_MAX = 24000
# I062/500 APW: unsigned; the maximum means that value or above (p. 126).
_APW_COUNT_MAX = 2**16 - 1

# The WGS-84 ellipsoid.
_WGS84_A = 6378137.0
_WGS84_F = 1.0 / 298.257223563
_WGS84_E2 = _WGS84_F * (2.0 - _WGS84_F)

# I062/080's first octet (§5.2.6, p. 12): MON in bit 8, SPI in bit 7, MRH in
# bit 6, SRC in bits 5 to 3, CNF in bit 2 and FX in bit 1. SPI is 0, its
# default value; MRH is 1, geometric altitude, ZMeta's only canonical height
# (contract 6.2); SRC is 000, no source, since the event does not state how its
# altitude was obtained; FX is 0, so no extent follows.
_TRACK_STATUS_MONOSENSOR = 0x80
_TRACK_STATUS_GEOMETRIC = 0x20
_TRACK_STATUS_TENTATIVE = 0x02

# I062/500's primary subfield with subfield #3, APW, alone (§5.2.26, p. 123).
_ACCURACY_APW_ONLY = 0x20

_CONFIG_REQUIRED = ("sac", "sic", "monosensor", "tentative", "simulated")
_CONFIG_OPTIONAL = ("service_id",)

# Dropped-concern register for this projection, as the SAPIENT and JREAP
# egress adapters keep theirs.
ASTERIX_EGRESS_LOSS_NOTES = {
    "date": (
        "I062/070 counts 1/128 s from the last UTC midnight (§5.2.5), so the "
        "record does not carry the date of event.ts; a receiver dates it by "
        "its own clock."
    ),
    "time_resolution": (
        "event.ts is floored to 1/128 s (7.8125 ms), so I062/070 never reads "
        "later than the state's time."
    ),
    "event_identity": (
        "event.event_id has no item; a record is traced to its event only "
        "through its track number and time."
    ),
    "source_identity": (
        "the source block (platform_id, node_role, producer, sensor_id, "
        "sw_version) has no item. I062/010 names the ASTERIX sender, which "
        "the caller declares."
    ),
    "confidence": (
        "the event's confidence has no item. I062/080 CNF states track "
        "confirmation as the deployment declares it and is not derived from "
        "confidence."
    ),
    "lineage": (
        "lineage.based_on and lineage.transform have no item. Recover "
        "provenance through the originating ZMeta event, never from the "
        "record."
    ),
    "timing_quality": (
        "payload.timing_quality has no item, and a locked claim does not "
        "export either: CAT062 ed. 1.21 has no item for the quality of the "
        "time source (I062/070, §5.2.5). An event whose timing is not locked "
        "is refused unless the caller allows degraded timing; with the "
        "allowance, I062/070 reads as an ordinary time, with no notice that "
        "the source clock was unsynchronized, in holdover or undeclared."
    ),
    "valid_for_ms": (
        "payload.valid_for_ms has no item. The encoder has no clock and "
        "encodes a state whose validity has ended like any other, so the "
        "sending deployment must stop sending a track when its validity "
        "ends; the receiver ages a track by I062/070 under its own rules."
    ),
    "class": (
        "payload.class has no item: I062/300 is a fixed table of airport "
        "vehicle types, and I062/380's emitter category is derived from the "
        "aircraft."
    ),
    "source_summary": "payload.source_summary has no item.",
    "provenance_and_quality": (
        "payload-scoped provenance and payload.quality have no item; a "
        "declared 2-D position shows only as the absence of I062/130."
    ),
    "extensions": (
        "payload.extensions have no item; vendor extension content is not "
        "re-exported across an external boundary."
    ),
    "risk_adjudication": (
        "no item carries a self-label, so an event with a warn, degrade, "
        "quarantine, rejected or unknown decision, or with a use restriction "
        "on the export use, is refused rather than exported clean."
    ),
    "geo_uncertainty": (
        "I062/500 carries APW alone: the north and east standard deviations "
        "of a 1_SIGMA ellipse, in degrees, each rounded up, so neither axis "
        "is stated smaller than the source's. The orientation and the "
        "cross-correlation are lost, so a receiver reads an ellipse aligned "
        "with north and east, which along an oblique major axis is up to "
        "sqrt(2) smaller than the source's deviation in that direction. An "
        "ellipse with another probability, or none, writes no accuracy, and "
        "at a latitude of exactly 90 degrees north or south no accuracy is "
        "written."
    ),
    "altitude_source": (
        "I062/080 SRC is 000, no source: the event does not state how alt_m "
        "was obtained."
    ),
    "height_reliability": (
        "I062/080 MRH is always 1, geometric altitude, ZMeta's only canonical "
        "height. On a declared 2-D track no altitude item follows, and the bit "
        "still reads geometric altitude as more reliable, although such a "
        "source may have had only a barometric height."
    ),
    "track_status_declarations": (
        "I062/080 MON (monosensor) and CNF (tentative) are the deployment's "
        "statements, declared by the caller; the event states neither."
    ),
    "lifecycle": (
        "I062/080's extents are not written, so the first and last messages "
        "for a track (TSB, TSE) and coasting (CST) are not signalled."
    ),
    "simulation": (
        "the SIM bit is in I062/080's first extent, which is not written, so "
        "a receiver reads its absence as an actual track. A caller that "
        "declares simulated true is refused."
    ),
    "course_or_speed_alone": (
        "I062/185 needs both components, so a course without a speed, or a "
        "speed without a course, has no item."
    ),
    "callsign": (
        "a callsign has no item: ed. 1.21 says I062/245 shall not be used, "
        "I062/380 subfield #2 states a downlink from the aircraft, and "
        "I062/390 subfield #2 states a flight plan correlation."
    ),
    "cartesian_position": (
        "I062/100 is not written: the adapter has no system reference point "
        "or projection, so a receiver that reads only the Cartesian position "
        "finds none."
    ),
}


def _note_refusal(refusal, reason):
    """Record why the event was refused, for a caller that passed a dict, and
    return None, the projection's refusal value."""
    if isinstance(refusal, dict):
        refusal["reason"] = reason
    return None


def _finite(value):
    """A real number with a float64 form: not a bool, NaN or an infinity.

    `math.isfinite` raises on a Python int beyond the float64 range, which
    `json.loads` builds from a long integer literal, so such an int counts as
    not finite here instead of raising out of the projection.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def _octet(value):
    return isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= 255


def _declarations(asterix_config):
    """(declarations, None, None), or (None, reason, message)."""
    if not isinstance(asterix_config, Mapping):
        return None, REFUSAL_CONFIG_INVALID, "the ASTERIX configuration must be a mapping"
    known = _CONFIG_REQUIRED + _CONFIG_OPTIONAL
    unknown = sorted(str(key) for key in asterix_config if key not in known)
    if unknown:
        return None, REFUSAL_CONFIG_INVALID, f"the ASTERIX configuration does not know the key(s) {', '.join(unknown)}"
    missing = [key for key in _CONFIG_REQUIRED if key not in asterix_config]
    if missing:
        return None, REFUSAL_CONFIG_INVALID, f"the ASTERIX configuration must declare {', '.join(missing)}"
    for key in ("sac", "sic"):
        if not _octet(asterix_config[key]):
            return None, REFUSAL_CONFIG_INVALID, f"{key} must be an integer from 0 to 255"
    service_id = asterix_config.get("service_id")
    if service_id is not None and not _octet(service_id):
        return None, REFUSAL_CONFIG_INVALID, "service_id must be an integer from 0 to 255, or be left out"
    for key in ("monosensor", "tentative", "simulated"):
        if type(asterix_config[key]) is not bool:
            return None, REFUSAL_CONFIG_INVALID, f"{key} must be true or false"
    if asterix_config["simulated"]:
        return None, REFUSAL_SIMULATED_UNSUPPORTED, (
            "simulated true is refused: marking a track simulated needs I062/080's first extent, "
            "whose KOS subfield no ZMeta state can fill"
        )
    declarations = {key: asterix_config[key] for key in _CONFIG_REQUIRED}
    if service_id is not None:
        declarations["service_id"] = service_id
    return declarations, None, None


def validate_asterix_config(asterix_config):
    """Return the declarations, or raise ValueError for a configuration the
    adapter cannot run.

    A deployment calls this when it reads its configuration, as the reference
    gateway calls `validate_cot_config`, so a missing or impossible declaration
    shows at startup rather than as a refusal of every track at egress.

    The configuration declares:
        sac, sic (int, 0 to 255, required): I062/010, the System Area Code and
            System Identification Code of the sender.
        monosensor (bool, required): I062/080 MON. True writes "monosensor
            track", false "multisensor track".
        tentative (bool, required): I062/080 CNF. True writes "tentative
            track", false "confirmed track".
        simulated (bool, required): whether the tracks are simulated. True is
            refused: marking a simulated track needs I062/080's first extent,
            which the adapter does not write.
        service_id (int, 0 to 255, optional): I062/015, written only when
            declared.
    No key has a default, and an unknown key is an error.
    """
    declarations, reason, message = _declarations(asterix_config)
    if reason is not None:
        raise ValueError(message)
    return declarations


def _uses(value):
    """A record's use labels, normalized as `tools/filter_risk.py` normalizes
    them, or None for a shape the gate cannot read."""
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip().upper() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [value.strip().upper()] if value.strip() else []
    return None


def _risk_refusal(payload, export_use):
    """The refusal reason of the risk gate, or None to export.

    An event exports when it carries no risk record, or when every record is
    an IGNORED decision with no use restriction on `export_use`. Records live
    at payload.extensions.risk_adjudication, as `tools/filter_risk.py` reads
    them. A container or a record the gate cannot read is refused: a
    restriction the gate cannot adjudicate is never adjudicated as none.
    """
    extensions = payload.get("extensions")
    if extensions is None:
        return None
    if not isinstance(extensions, Mapping):
        return REFUSAL_RISK_UNREADABLE
    records = extensions.get("risk_adjudication")
    if records is None:
        return None
    if not isinstance(records, list):
        return REFUSAL_RISK_UNREADABLE
    found = set()
    for record in records:
        if not isinstance(record, Mapping):
            found.add(REFUSAL_RISK_UNREADABLE)
            continue
        decision = str(record.get("policy_decision") or "UNKNOWN").strip().upper() or "UNKNOWN"
        if decision != "IGNORED":
            found.add(_DECISION_REFUSALS.get(decision, REFUSAL_RISK_UNKNOWN_DECISION))
            continue
        allowed = _uses(record.get("allowed_uses"))
        prohibited = _uses(record.get("prohibited_uses"))
        if allowed is None or prohibited is None:
            found.add(REFUSAL_RISK_UNREADABLE)
        elif export_use in prohibited or (allowed and export_use not in allowed):
            found.add(REFUSAL_RISK_USE_RESTRICTED)
    for reason in _RISK_SEVERITY:
        if reason in found:
            return reason
    return None


def _timing_refusal(payload):
    """None when the event's timing is locked, otherwise the reason it is not.

    Locked means `payload.timing_quality` is a mapping whose `sync_state` is
    exactly "LOCKED", the boundary the SAPIENT egress adapter uses for its
    timing label. HOLDOVER and UNSYNCED each have their own reason; an absent
    `timing_quality` has one; a `timing_quality` that is not a mapping, or a
    `sync_state` outside the schema's three tokens, has one. No reason echoes
    an input value, and `est_error_ms` is not read: a timing threshold is
    deployment policy, which reaches this adapter through the risk gate.
    """
    if "timing_quality" not in payload:
        return REFUSAL_TIMING_ABSENT
    timing = payload["timing_quality"]
    if not isinstance(timing, Mapping):
        return REFUSAL_TIMING_MALFORMED
    state = timing.get("sync_state")
    if state == "LOCKED":
        return None
    if state == "HOLDOVER":
        return REFUSAL_TIMING_HOLDOVER
    if state == "UNSYNCED":
        return REFUSAL_TIMING_UNSYNCED
    return REFUSAL_TIMING_MALFORMED


def _time_count(ts):
    """I062/070's count for `ts`, floored, or None when `ts` is not an instant."""
    instant = _parse_utc(ts)
    if instant is None:
        return None
    seconds = (instant.hour * 60 + instant.minute) * 60 + instant.second
    microseconds = seconds * 1_000_000 + instant.microsecond
    return microseconds * _TIME_COUNTS_PER_S // 1_000_000


def _track_number(payload, track_numbers):
    """(I062/040's number, None), or (None, reason). The number comes only from
    the caller's map; none is minted."""
    track_id = payload.get("track_id")
    if (
        not isinstance(track_id, str)
        or not track_id
        or not isinstance(track_numbers, Mapping)
        or track_id not in track_numbers
    ):
        return None, REFUSAL_TRACK_UNMAPPED
    number = track_numbers[track_id]
    if isinstance(number, bool) or not isinstance(number, int) or not 0 <= number <= 0xFFFF:
        return None, REFUSAL_TRACK_NUMBER_INVALID
    return number, None


def _position_counts(geo):
    """I062/105's (latitude, longitude) counts, to the nearest LSB, or None."""
    lat = geo.get("lat")
    lon = geo.get("lon")
    if not (_finite(lat) and _finite(lon)) or not -90.0 <= lat <= 90.0 or not -180.0 <= lon <= 180.0:
        return None
    lat_count = round(lat / _POSITION_LSB_DEG)
    lon_count = round(lon / _POSITION_LSB_DEG)
    if lon_count == _LON_COUNT_LIMIT:
        # The item's longitude stops short of +180 (p. 24). A longitude that
        # quantizes to +180 is written as -180, the same meridian.
        lon_count = -_LON_COUNT_LIMIT
    return lat_count, lon_count


def _altitude_count(geo):
    """(I062/130's count or None for no item, None), or (None, reason)."""
    dimensionality = geo.get("dimensionality", "3D")
    if dimensionality == "2D":
        if "alt_m" in geo:
            # A declared 2-D geo prohibits alt_m (contract 21.8); the pair is
            # schema-incoherent, and picking one claim to believe is refused.
            return None, REFUSAL_ALTITUDE_INVALID
        return None, None
    if dimensionality != "3D":
        return None, REFUSAL_ALTITUDE_INVALID
    alt_m = geo.get("alt_m")
    if not _finite(alt_m):
        return None, REFUSAL_ALTITUDE_INVALID
    count = round(alt_m / _ALTITUDE_LSB_M)
    if not _ALTITUDE_COUNT_MIN <= count <= _ALTITUDE_COUNT_MAX:
        return None, REFUSAL_ALTITUDE_OUT_OF_RANGE
    return count, None


def _velocity_counts(payload):
    """(I062/185's (Vx, Vy) counts or None for no item, None), or (None, reason).

    Vx is the east component and Vy the north component at the target (the
    item's note on p. 39 and §4.3.2, p. 6), from the course over ground in
    degrees true north (contract 6.4) and the speed.
    """
    heading = payload.get("heading_deg")
    speed = payload.get("speed_mps")
    if heading is None or speed is None:
        return None, None
    if not (_finite(heading) and _finite(speed)) or not 0.0 <= heading <= 360.0 or speed < 0.0:
        return None, REFUSAL_VELOCITY_INVALID
    if speed > _SPEED_LIMIT_MPS:
        return None, REFUSAL_VELOCITY_OUT_OF_RANGE
    course = math.radians(heading)
    vx = round(speed * math.sin(course) / _VELOCITY_LSB_MPS)
    vy = round(speed * math.cos(course) / _VELOCITY_LSB_MPS)
    if not (_INT16_MIN <= vx <= _INT16_MAX and _INT16_MIN <= vy <= _INT16_MAX):
        return None, REFUSAL_VELOCITY_OUT_OF_RANGE
    return (vx, vy), None


def _apw_count(deviation_deg):
    """A standard deviation in degrees as APW counts, rounded up, saturating."""
    if not math.isfinite(deviation_deg):
        return _APW_COUNT_MAX
    counts = deviation_deg / _POSITION_LSB_DEG
    if counts >= _APW_COUNT_MAX:
        return _APW_COUNT_MAX
    return math.ceil(counts)


def _accuracy_counts(geo):
    """(I062/500 APW's (latitude, longitude) counts or None for no item, None),
    or (None, reason).

    Only a 1_SIGMA ellipse is written, since the edition defines every
    accuracy as a standard deviation (pp. 125 to 128). The north and east
    standard deviations are the ellipse's exact marginals, converted to
    degrees with the WGS-84 radii of curvature at the target's latitude.
    """
    ellipse = geo.get("error_ellipse_m")
    if ellipse is None:
        return None, None
    if not isinstance(ellipse, Mapping):
        return None, REFUSAL_ACCURACY_INVALID
    if ellipse.get("probability") != "1_SIGMA":
        return None, None
    a = ellipse.get("semi_major")
    b = ellipse.get("semi_minor")
    theta = ellipse.get("orientation_deg")
    if not (_finite(a) and _finite(b) and _finite(theta)) or a < 0 or b < 0 or not 0.0 <= theta <= 360.0:
        return None, REFUSAL_ACCURACY_INVALID
    lat = geo["lat"]
    if abs(lat) == 90.0:
        # The longitude deviation is undefined at a pole.
        return None, None
    orientation = math.radians(theta)
    sin_t = math.sin(orientation)
    cos_t = math.cos(orientation)
    # sqrt(a² cos²θ + b² sin²θ) and sqrt(a² sin²θ + b² cos²θ), computed with
    # hypot on floats so that a long integer or a very large semi-axis
    # saturates the item instead of overflowing.
    a = float(a)
    b = float(b)
    sigma_north = math.hypot(a * cos_t, b * sin_t)
    sigma_east = math.hypot(a * sin_t, b * cos_t)
    phi = math.radians(lat)
    w = 1.0 - _WGS84_E2 * math.sin(phi) ** 2
    meridional = _WGS84_A * (1.0 - _WGS84_E2) / (w * math.sqrt(w))
    prime_vertical = _WGS84_A / math.sqrt(w)
    lat_deviation = math.degrees(sigma_north / meridional)
    lon_deviation = math.degrees(sigma_east / (prime_vertical * math.cos(phi)))
    return (_apw_count(lat_deviation), _apw_count(lon_deviation)), None


def _fspec(frns):
    """The FSPEC for the present FRNs: seven item bits per octet, FX set on
    every octet but the last."""
    octets = [0] * ((max(frns) - 1) // 7 + 1)
    for frn in frns:
        octets[(frn - 1) // 7] |= 0x80 >> ((frn - 1) % 7)
    for index in range(len(octets) - 1):
        octets[index] |= 0x01
    return bytes(octets)


def zmeta_state_to_asterix_cat062(
    event,
    asterix_config,
    *,
    track_numbers,
    export_use="COALITION_EXPORT",
    allow_degraded_timing=False,
    refusal=None,
):
    """Encode a ZMeta STATE_EVENT/TRACK_STATE as one CAT062 ed. 1.21 record.

    Args:
        event: the ZMeta event dict.
        asterix_config: the deployment's declarations (see
            `validate_asterix_config`).
        track_numbers: the caller-owned mapping of `track_id` to I062/040's
            track number, 0 to 65,535. Track numbering is deployment state:
            the adapter never mints a number, and an unmapped track is refused.
        export_use: the use label this export path consumes under (default
            "COALITION_EXPORT", semantics contract 3.3 vocabulary), as in the
            SAPIENT egress adapter.
        allow_degraded_timing: only the boolean True exports an event whose
            timing is not locked (see `_timing_refusal`); any other value
            that is not a boolean refuses the call. With it, the record's
            time reads as an ordinary time, with no notice of the clock's
            state, and the deployment that sets it is the party telling its
            receivers so. It never opens the risk gate.
        refusal: an optional dict; a refusal writes its reason under "reason".

    Returns:
        The record (FSPEC and items) as bytes, or None. The record carries
        I062/010, I062/070, I062/105, I062/040 and I062/080 always; I062/015
        when declared; I062/185 when the event carries both a course and a
        speed; I062/130 when the geo is 3-D; I062/500 when the ellipse is
        1_SIGMA and the latitude is not a pole. None, with the reason, for an
        event that is not a track state, a configuration or argument the
        adapter cannot run, a risk record the gate refuses, timing that is not
        locked (unless allowed), an `event.ts` that is not an instant, an
        unmapped track or a number outside 0 to 65,535, a missing
        or impossible position, an incoherent or impossible altitude, an
        impossible course or speed, a 1_SIGMA ellipse with impossible members,
        and an altitude or velocity beyond its item's range. This projection
        never raises.
    """
    header = event.get("event") if isinstance(event, Mapping) else None
    payload = event.get("payload") if isinstance(event, Mapping) else None
    if (
        not isinstance(header, Mapping)
        or not isinstance(payload, Mapping)
        or header.get("event_type") != "STATE_EVENT"
        or header.get("event_subtype") != "TRACK_STATE"
    ):
        return _note_refusal(refusal, REFUSAL_NOT_TRACK_STATE)

    if not isinstance(export_use, str) or not export_use.strip():
        return _note_refusal(refusal, REFUSAL_CONFIG_INVALID)
    if type(allow_degraded_timing) is not bool:
        # Only the boolean True allows: the string "false" must not read as true.
        return _note_refusal(refusal, REFUSAL_CONFIG_INVALID)
    declarations, reason, _message = _declarations(asterix_config)
    if reason is not None:
        return _note_refusal(refusal, reason)

    # The risk gate comes first and the allowance never opens it: an event
    # with a timing risk record is refused for risk, allowed or not.
    reason = _risk_refusal(payload, export_use.strip().upper())
    if reason is not None:
        return _note_refusal(refusal, reason)
    if not allow_degraded_timing:
        reason = _timing_refusal(payload)
        if reason is not None:
            return _note_refusal(refusal, reason)

    time_count = _time_count(header.get("ts"))
    if time_count is None:
        return _note_refusal(refusal, REFUSAL_TIME_UNPARSEABLE)

    number, reason = _track_number(payload, track_numbers)
    if reason is not None:
        return _note_refusal(refusal, reason)

    geo = payload.get("geo")
    position = _position_counts(geo) if isinstance(geo, Mapping) else None
    if position is None:
        return _note_refusal(refusal, REFUSAL_POSITION_INVALID)
    altitude, reason = _altitude_count(geo)
    if reason is not None:
        return _note_refusal(refusal, reason)
    velocity, reason = _velocity_counts(payload)
    if reason is not None:
        return _note_refusal(refusal, reason)
    accuracy, reason = _accuracy_counts(geo)
    if reason is not None:
        return _note_refusal(refusal, reason)

    status = _TRACK_STATUS_GEOMETRIC
    if declarations["monosensor"]:
        status |= _TRACK_STATUS_MONOSENSOR
    if declarations["tentative"]:
        status |= _TRACK_STATUS_TENTATIVE

    items = [
        (_FRN_010, struct.pack(">BB", declarations["sac"], declarations["sic"])),
        (_FRN_070, time_count.to_bytes(3, "big")),
        (_FRN_105, struct.pack(">ii", *position)),
        (_FRN_040, struct.pack(">H", number)),
        (_FRN_080, bytes([status])),
    ]
    if "service_id" in declarations:
        items.append((_FRN_015, struct.pack(">B", declarations["service_id"])))
    if velocity is not None:
        items.append((_FRN_185, struct.pack(">hh", *velocity)))
    if altitude is not None:
        items.append((_FRN_130, struct.pack(">h", altitude)))
    if accuracy is not None:
        items.append((_FRN_500, bytes([_ACCURACY_APW_ONLY]) + struct.pack(">HH", *accuracy)))
    # Items go in FRN order (§4.7, p. 7).
    items.sort(key=lambda item: item[0])
    return _fspec([frn for frn, _data in items]) + b"".join(data for _frn, data in items)


def cat062_data_block(records):
    """Wrap one or more CAT062 records in a data block (§4.6, p. 7).

    CAT is one octet, 62; LEN is two octets, the length of the whole block in
    octets, CAT and LEN included; the records follow. Raises ValueError for no
    records, a record that is not non-empty bytes, or a block longer than LEN
    can state (65,535 octets); a sender splits its records across blocks.
    """
    if not isinstance(records, (list, tuple)) or not records:
        raise ValueError("a data block needs a list or tuple of one or more records")
    for record in records:
        if not isinstance(record, (bytes, bytearray)) or not record:
            raise ValueError("every record must be non-empty bytes")
    body = b"".join(bytes(record) for record in records)
    length = 3 + len(body)
    if length > 0xFFFF:
        raise ValueError(f"a data block of {length} octets is longer than LEN can state (65,535)")
    return bytes([CATEGORY]) + length.to_bytes(2, "big") + body
