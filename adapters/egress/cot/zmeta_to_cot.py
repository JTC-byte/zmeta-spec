"""ZMeta STATE_EVENT to Cursor-on-Target (CoT) XML egress adapter.

Converts ZMeta STATE_EVENT track states into CoT v2.0 XML for TAK
(ATAK, WinTAK, TAK Server) interoperability.

Supports:
  - CE from geo.error_ellipse_m semi_major (the conservative circular bound:
    a circle of that radius covers the whole ellipse); when the event
    carries no uncertainty, CoT's documented unknown-value convention
    (9999999.0) is emitted rather than an invented accuracy figure. LE is
    NEVER derived from the ellipse - CoT le is linear (vertical/HAE) error
    and error_ellipse_m is purely horizontal, so le is always the unknown
    convention unless the deployment overrides default_le with a real
    vertical error model. Absent geo.alt_m gets the same treatment for
    point@hae - never a fabricated 0 m altitude claim
  - Heading/speed track element (directional arrows on TAK map)
  - PrecisionLocation for MIL-STD-2525 elliptical uncertainty, emitted only
    when the config explicitly asserts geopointsrc/altsrc - the event model
    carries no geo-source field, so source pedigree is never defaulted to
    "GPS" on positions that may be RF-triangulated fusion products
  - ATAK team coloring (__group element) for friendly platforms
  - Hostile emitter callsign fallback logic
  - Persistent labels for hostile tracks
  - Source summary, confidence, and error ellipse details in remarks
  - Custom icon support for drone platforms
  - Event-authoritative timestamps by default; explicit opt-in wall-clock
    replay-display mode (use_wall_clock=True) re-stamps CoT time to now so
    TAK shows fresh markers during historical replay (contract section 9.5).
    An event with no ts - or a ts that does not parse as an RFC3339
    instant, which passes the schema gate because jsonschema does not
    enforce format without a FormatChecker - is refused (returns None)
    unless wall-clock mode is on - the adapter never fabricates freshness
    for malformed input

Source: Z-ISR zisr/transport/publisher.py (_builtin_zmeta_to_cot)
"""

import math
from collections.abc import Mapping, Sequence
from collections.abc import Set as AbstractSet
from datetime import datetime, timedelta, timezone
from decimal import Decimal

# Text leaves are Sequences, so they have to be excluded before the Sequence
# branch or every string becomes a walk over its own characters.
_TEXT_LEAF_TYPES = (str, bytes, bytearray)


DEFAULT_COT_TYPE = "a-u-G"

# CoT's documented unknown-value convention for point@ce / point@le.
# Emitted when the event carries no uncertainty so absent accuracy is
# never rendered as invented precision (contract sections 4.7 / 12.2).
COT_UNKNOWN_ACCURACY = 9999999.0
STATE_PROHIBITED_PAYLOAD_FIELDS = {
    "features",
    "raw_features",
    "modality",
    "measurement",
    "measurements",
    "t_start",
    "t_end",
    "data_ref",
    "data_refs",
}


def _parse_utc(ts):
    """Parse an RFC3339/ISO-8601 `ts` to an aware UTC datetime, or None.

    The schema types `event.ts` as `format: date-time`, but jsonschema does
    not enforce `format` without an explicitly installed FormatChecker, so a
    gate-clean event can still carry a string `fromisoformat` rejects (e.g.
    "2026-07-27T99:99:99Z"). That used to escape this adapter as a raw
    ValueError. The disposition for "this cannot be projected" is the
    documented refusal signal (None) - the same one a missing ts gets -
    never a fabricated timestamp and never a traceback out of the caller's
    event loop (see _stale_time for the same rule on the stale arithmetic).
    OverflowError covers astimezone() on edge-of-range instants; TypeError /
    AttributeError cover a ts that is not a string at all; OSError covers
    the platform delegate on hosts where a conversion is out of range.

    A parse that yields a NAIVE datetime is refused outright: shapes like
    "1969-12-31Z" or "2026-W01-1Z" satisfy the schema's `Z$` pattern yet
    carry no offset after parsing, and `.astimezone()` on a naive datetime
    asks the PLATFORM - silently reinterpreting the instant as host-local
    time (a UTC claim the event never made) or raising OSError pre-epoch on
    Windows. No offset, no instant.
    """
    try:
        if ts.endswith("Z"):
            ts = ts[:-1] + "+00:00"
        parsed = datetime.fromisoformat(ts)
        if parsed.tzinfo is None:
            return None
        return parsed.astimezone(timezone.utc)
    except (ValueError, OverflowError, TypeError, AttributeError, OSError):
        return None


def _esc(text):
    """Escape XML special characters."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _stale_time(time_obj, valid_for_ms):
    """`time_obj + valid_for_ms` as a datetime, or None when unrepresentable.

    CoT `stale` is an absolute timestamp, so a validity window the datetime
    module cannot add is a window CoT has no way to express. Three raising
    modes reach here on input the kernel forwards clean, because
    `payload.valid_for_ms` is `{"type": "integer", "minimum": 1}` with **no
    upper bound** (schema/zmeta-event-1.0.schema.json):

      * `10**400` ms  -> OverflowError "Python int too large to convert to
        C int" (the arm R1-11 R2-05 names)
      * `10**15` ms   -> OverflowError "date value out of range"
      * an ordinary `300000` ms stale on `ts="9999-12-31T23:59:59Z"` ->
        OverflowError "date value out of range", from a timestamp and a
        window that are each individually unremarkable

    All three previously escaped as a raw exception out of an adapter whose
    documented failure signal is None - the same defect the non-finite arm of
    this expression already had closed (`default_valid_for_ms = NaN`), left
    open on the integer arm. TypeError is caught for the same reason: the
    disposition for "this cannot be projected" is the documented None, not a
    traceback out of the caller's event loop.

    Refusal, not substitution. Falling back to `default_valid_for_ms` would
    publish a freshness bound the event never claimed, and clamping to
    `datetime.max` would publish "this track never goes stale". CoT has no
    unknown-value convention for `stale` the way it has 9999999.0 for
    ce/le, and a CoT event without `stale` is not a CoT event - so this is
    the case where the event genuinely is unusable without the bad datum,
    and whole-event refusal is proportionate rather than escalatory.
    """
    try:
        return time_obj + timedelta(milliseconds=valid_for_ms)
    except (OverflowError, ValueError, TypeError):
        return None


def _has_state_prohibited_payload_fields(payload):
    if not isinstance(payload, dict):
        return True
    return any(field in payload for field in STATE_PROHIBITED_PAYLOAD_FIELDS)


def _is_non_finite(value):
    # float and Decimal are the only decoded types that can be non-finite. A
    # Python int is never converted: math.isfinite() on an int outside float64
    # range raises OverflowError, which would trade this guard for a crash.
    if isinstance(value, float):
        return not math.isfinite(value)
    if isinstance(value, Decimal):
        return not value.is_finite()
    return False


def _has_non_finite(value):
    """True when NaN/inf appears anywhere inside `value`.

    Value scoped, not field scoped. The guard this replaced was a list of nine
    candidate numbers, which is the same structural mistake A-01 names as the
    defect: it closes the fields someone thought of. Its list was already
    incomplete - a non-finite in payload.source_summary rendered into
    <remarks> as the token "nan", and a non-finite cot_config default escaped
    as a raw ValueError/OverflowError out of an adapter whose documented
    refusal signal is None.

    Container coverage is by abstract type, not by dict/list: the gateway's
    cbor2 fallback backend decodes CBOR tag 258 into a `set`, a map used as a
    map key into a Mapping that is not a dict, and an unrecognised tag into a
    tag object whose `.value` still reaches the wire.

    Iterative, with a seen-set: recursing would tie the process stack to
    sender-controlled nesting depth, and CBOR value-sharing tags make the
    decoded structure possibly cyclic, so an unbounded walk here would be a
    hang on the egress path.
    """
    stack = [value]
    seen = set()
    while stack:
        current = stack.pop()
        if _is_non_finite(current):
            return True
        if isinstance(current, _TEXT_LEAF_TYPES):
            continue
        if isinstance(current, (Mapping, AbstractSet, Sequence)) or (
            hasattr(current, "tag") and hasattr(current, "value")
        ):
            marker = id(current)
            if marker in seen:
                continue
            seen.add(marker)
        if isinstance(current, Mapping):
            stack.extend(current.keys())
            stack.extend(current.values())
        elif isinstance(current, (AbstractSet, Sequence)):
            stack.extend(current)
        elif hasattr(current, "tag") and hasattr(current, "value"):
            stack.append(current.value)
    return False


def zmeta_to_cot(event, cot_config=None):
    """Convert a ZMeta STATE_EVENT into CoT XML.

    Args:
        event: ZMeta event dict. Must have event_type=STATE_EVENT.
        cot_config: Optional dict with configuration overrides:
            - default_type (str): Default CoT type (default "a-u-G")
            - default_valid_for_ms (int): Stale interval (default 300000)
            - default_ce (float): Circular error metres when the event
                carries no uncertainty (default 9999999.0, CoT's
                unknown-value convention; override only when the
                deployment has a real error model)
            - default_le (float): Linear (vertical/HAE) error metres
                (default 9999999.0, as above). Always the emitted le: the
                event model carries no vertical-error field, and the
                horizontal error ellipse must never masquerade as one
            - geopointsrc (str): Position-source pedigree for
                <precisionlocation> (e.g. "GPS"), asserted by the operator
                who knows how the deployment derives positions. Default
                None - the element is omitted rather than stamped with a
                source the event never claimed
            - altsrc (str): Altitude-source pedigree, same rule as
                geopointsrc (default None - omitted, never defaulted)
            - friendly_team_name (str): ATAK team name (default "Cyan")
            - friendly_team_role (str): ATAK team role (default "Team Member")
            - use_wall_clock (bool): Explicit replay-display mode — re-stamp
                CoT timestamps to the current time so TAK shows fresh
                markers during replay of historical data. Off by default:
                event time is authoritative, and replayed data must not
                render as live unless the operator explicitly selected
                replay mode (contract section 9.5). With the mode off, an
                event missing event.ts is refused (returns None) instead of
                being silently stamped with the current time.

    Returns:
        CoT XML string, or None if the event cannot be converted (wrong
        event type, prohibited raw payload fields, missing geo/track_id,
        missing or unparseable event.ts outside wall-clock mode - see
        _parse_utc, any non-finite (NaN/inf) number that would become a CoT
        attribute, or a validity window whose stale timestamp is not
        representable - see _stale_time).
    """
    if event.get("event", {}).get("event_type") != "STATE_EVENT":
        return None

    cot_config = cot_config or {}
    payload = event.get("payload", {})
    if _has_state_prohibited_payload_fields(payload):
        return None

    geo = payload.get("geo")
    if not geo or geo.get("lat") is None or geo.get("lon") is None:
        return None

    track_id = payload.get("track_id")
    if not track_id:
        return None

    # Refuse rather than render a position that is not a position. NaN/inf
    # reach a CoT attribute as the literal tokens "nan"/"inf", which ATAK
    # draws as an ordinary marker carrying no uncertainty label, no violation
    # code and nothing an operator can filter on - the sharp end of design
    # gate 3 (R1-11 A-01). The kernel refuses such an event before it ever
    # gets here, so this closes the same hole for callers that project
    # directly without going through the gateway's outgoing gate. Refusal is
    # this adapter's documented signal (None), the same one used for missing
    # geo/track_id/ts, and the gateway buckets it as a counted, reason-tagged
    # cot_skipped record - so the refusal stays visible to the operator.
    #
    # Scope: every canonical field of the event, plus the operator's config,
    # walked by VALUE. The list-of-numbers version this replaced was field
    # scoped, which is the structure A-01 names as the defect, and its list
    # was already short by at least three (payload.source_summary, whose
    # members render into <remarks>; any error_ellipse_m key added later; and
    # cot_config.default_valid_for_ms, which escaped as a raw ValueError /
    # OverflowError rather than the documented None).
    #
    # payload.extensions is the one deliberate exclusion. It is namespaced
    # vendor content this adapter never reads and never renders, so refusing
    # the operator's track because a provenance blob carried a NaN would
    # destroy good canonical data over content CoT does not project - the
    # escalation this repo had to repair in the SAPIENT ingress adapter in
    # this same audit. Everything CoT can render, and everything a future
    # field could render, is covered without editing a list.
    if _has_non_finite(cot_config):
        return None
    for key, value in event.items():
        if key == "payload":
            continue
        if _has_non_finite(value):
            return None
    for key, value in payload.items():
        if key == "extensions":
            continue
        if _has_non_finite(value):
            return None

    # Timestamps: event-authoritative by default (contract section 9.5 —
    # replay must not be indistinguishable from live). use_wall_clock=True
    # is an explicit replay-display opt-in that re-stamps CoT time to now.
    use_wall_clock = cot_config.get("use_wall_clock", False)
    if use_wall_clock:
        time_obj = datetime.now(timezone.utc)
    else:
        ts = event.get("event", {}).get("ts")
        if not ts:
            # Fail closed: an event with no ts carries no time claim, and
            # stamping the current wall clock would fabricate freshness for
            # malformed input (contract section 9.5). The explicit
            # use_wall_clock replay-display mode is the only sanctioned
            # now-stamping path.
            return None
        time_obj = _parse_utc(ts)
        if time_obj is None:
            # Same refusal as a missing ts: an unparseable time claim is no
            # time claim, and CoT time/start/stale cannot be derived from it.
            return None

    default_valid_for_ms = cot_config.get("default_valid_for_ms", 300000)
    valid_for_ms = payload.get("valid_for_ms", default_valid_for_ms)
    stale_obj = _stale_time(time_obj, valid_for_ms)
    if stale_obj is None:
        return None

    time_str = time_obj.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    stale_str = stale_obj.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    default_type = cot_config.get("default_type", DEFAULT_COT_TYPE)
    cot_type = payload.get("class", default_type)
    lat = geo["lat"]
    lon = geo["lon"]
    # Absent altitude is emitted as CoT's unknown-value convention (the same
    # treatment ce/le get below), never rendered as a concrete 0 m claim.
    # A legitimate alt_m of 0.0 passes through unchanged.
    alt_m = geo.get("alt_m")
    hae = COT_UNKNOWN_ACCURACY if alt_m is None else alt_m

    # Circular error resolution:
    # 1. geo.error_ellipse_m semi_major — the only schema-valid uncertainty
    #    source on geo (v1.1.0 $defs/geo; v1.0 geo carries none). semi_major
    #    is the CONSERVATIVE circular bound: a circle of that radius covers
    #    the whole ellipse, so ce never understates the horizontal error.
    # 2. Config default — 9999999.0, CoT's unknown-value convention, unless
    #    the deployment overrides with a real error model
    #
    # le is NEVER derived from the ellipse (R1-11 CR-02). CoT point@le is
    # LINEAR error — the vertical/HAE uncertainty — while error_ellipse_m is
    # purely horizontal (contract section 21.2: orientation_deg is degrees
    # true north; the schema carries no vertical-uncertainty field at all).
    # Mapping semi_minor onto le told TAK "altitude known to ±semi_minor m",
    # a vertical bound the event never claimed. Since the event model has no
    # vertical error to project, le is always the adapter's unknown
    # convention (default_le), ellipse or no ellipse.
    default_ce = cot_config.get("default_ce", COT_UNKNOWN_ACCURACY)
    le = cot_config.get("default_le", COT_UNKNOWN_ACCURACY)
    error_ellipse = geo.get("error_ellipse_m")

    if error_ellipse and isinstance(error_ellipse, dict):
        ce = error_ellipse.get("semi_major", default_ce)
    else:
        ce = default_ce

    # Callsign with hostile emitter fallback: never show raw track IDs
    # on TAK for hostile markers. Use "RF Emitter" or "Detection" instead.
    callsign = payload.get("callsign", f"Track {track_id}")
    if cot_type.startswith("a-h-"):
        if (
            not callsign
            or callsign == track_id
            or callsign.startswith("Track ")
            or callsign.startswith("torchai-track-")
        ):
            callsign = "RF Emitter"

    # Remarks: source_summary, then confidence (whenever the event carries
    # one — never dropped because other remarks are present), then error
    # ellipse details.
    source_summary = payload.get("source_summary", [])
    if isinstance(source_summary, list):
        remarks_text = "; ".join(str(s) for s in source_summary)
    else:
        remarks_text = str(source_summary) if source_summary else ""

    confidence = event.get("confidence")
    if confidence is not None:
        confidence_str = f"confidence={confidence}"
        remarks_text = f"{remarks_text}; {confidence_str}" if remarks_text else confidence_str

    # A member absent from `error_ellipse` renders as an omitted fragment,
    # never a fabricated `0`: `.get(key, 0)` used to turn "this deployment
    # never asserted an orientation" into "this ellipse has 0 degrees of
    # orientation", a claim nobody made. `semi_major` anchors the whole
    # claim -- without it (absent, or under a wrong-spelled/legacy key like
    # ADS-B's old `semi_major_m`) there is no ellipse this adapter can
    # honestly describe, so no ellipse text is rendered at all, the same way
    # `ce` above already falls back to `default_ce` rather than reading a `0`
    # out of it.
    ellipse_semi_major = (
        error_ellipse.get("semi_major") if isinstance(error_ellipse, dict) else None
    )
    if error_ellipse and isinstance(error_ellipse, dict) and ellipse_semi_major is not None:
        ellipse_parts = [f"{ellipse_semi_major:.0f}m"]
        semi_min = error_ellipse.get("semi_minor")
        if semi_min is not None:
            ellipse_parts.append(f"x {semi_min:.0f}m")
        orient = error_ellipse.get("orientation_deg")
        if orient is not None:
            ellipse_parts.append(f"@ {orient:.0f}deg")
        ellipse_str = "Error ellipse: " + " ".join(ellipse_parts)
        if remarks_text:
            remarks_text += f"; {ellipse_str}"
        else:
            remarks_text = ellipse_str

    remarks_xml = ""
    if remarks_text:
        remarks_xml = f"\n    <remarks>{_esc(remarks_text)}</remarks>"

    # <track> element for heading/speed (TAK renders directional arrows).
    # Frame note: CoT track@course is degrees true north by convention, and
    # ZMeta payload.heading_deg is contractually degrees true north
    # (semantics contract section 6.4), so this is a frame-preserving 1:1
    # projection. When only speed is known, course is emitted as the "0.0"
    # placeholder TAK requires; it is a rendering artifact, not a heading
    # claim (see README).
    track_xml = ""
    heading = payload.get("heading_deg")
    speed = payload.get("speed_mps")
    if heading is not None or speed is not None:
        course = f"{heading:.1f}" if heading is not None else "0.0"
        spd = f"{speed:.1f}" if speed is not None else "0.0"
        track_xml = f'\n    <track course="{course}" speed="{spd}" />'

    # <precisionlocation> for MIL-STD-2525 elliptical uncertainty.
    # geopointsrc/altsrc are source-provenance pedigree attributes TAK
    # consumers read as "how this position/altitude was derived". The event
    # model carries no geo-source field, so the adapter cannot know — the
    # old unconditional geopointsrc="GPS" altsrc="GPS" stamped a GPS
    # pedigree on positions that may be RF-triangulated fusion products
    # (R1-11 CR-11). Refuse-or-omit: the element is emitted only when the
    # operator's config explicitly asserts a source, and only the asserted
    # attribute(s) are stamped. Nothing defaults to "GPS". The ellipse
    # detail still projects unconditionally as the conservative point@ce
    # above and as human-readable remarks text.
    precision_xml = ""
    geopointsrc = cot_config.get("geopointsrc")
    altsrc = cot_config.get("altsrc")
    if (
        error_ellipse
        and isinstance(error_ellipse, dict)
        and (geopointsrc is not None or altsrc is not None)
        and ellipse_semi_major is not None
    ):
        # Same honest-absence rule as the remarks text above: a member this
        # dict never asserted is an omitted attribute, never `0.0`.
        src_attrs = ""
        if geopointsrc is not None:
            src_attrs += f' geopointsrc="{_esc(str(geopointsrc))}"'
        if altsrc is not None:
            src_attrs += f' altsrc="{_esc(str(altsrc))}"'
        ellipse_attrs = f' ellipse_major="{ellipse_semi_major:.1f}"'
        semi_min = error_ellipse.get("semi_minor")
        if semi_min is not None:
            ellipse_attrs += f' ellipse_minor="{semi_min:.1f}"'
        orient = error_ellipse.get("orientation_deg")
        if orient is not None:
            ellipse_attrs += f' ellipse_angle="{orient:.1f}"'
        precision_xml = f'\n    <precisionlocation{src_attrs}{ellipse_attrs} />'

    # <__group> for ATAK team coloring on friendly platforms
    group_xml = ""
    if cot_type.startswith("a-f-"):
        # str() like every other cot_config value that reaches _esc: a YAML
        # scalar that parses as a number or bool would otherwise raise
        # inside _esc and drop the whole event at the gateway backstop
        # (pre-cut review).
        group_name = str(cot_config.get("friendly_team_name", "Cyan"))
        group_role = str(cot_config.get("friendly_team_role", "Team Member"))
        group_xml = f'\n    <__group name="{_esc(group_name)}" role="{_esc(group_role)}" />'

    # Persistent labels for hostile tracks (CE readout always visible)
    labels_xml = ""
    if cot_type.startswith("a-h-"):
        labels_xml = '\n    <labels_on value="true" />'

    # Custom icon for drone/sensor platforms
    usericon_xml = ""
    if cot_type == "a-f-A-M-F-Q":
        usericon_xml = (
            '\n    <usericon iconsetpath='
            '"a1b2c3d4-e5f6-7890-abcd-ef1234567890'
            '/Torch Drones/quadcopter.png" />'
        )

    # CoT `how` is a position-derivation pedigree claim (m-g = machine/GPS
    # derived). Same rule as geopointsrc/altsrc above: the event model
    # carries no geo-source field, so `how` is emitted only when the
    # deployment asserts one via cot_config - never a hardcoded "m-g" on
    # positions that may be RF-triangulated fusion products.
    how_value = cot_config.get("how")
    how_attr = f' how="{_esc(str(how_value))}"' if how_value is not None else ""
    cot_xml = (
        f'<event version="2.0" type="{_esc(cot_type)}" uid="{_esc(track_id)}"'
        f' time="{time_str}" start="{time_str}" stale="{stale_str}"{how_attr}>\n'
        f'  <point lat="{lat}" lon="{lon}" hae="{hae}" le="{le}" ce="{ce}" />\n'
        f"  <detail>\n"
        f'    <contact callsign="{_esc(callsign)}" />'
        f"{labels_xml}{remarks_xml}{track_xml}{precision_xml}{group_xml}{usericon_xml}\n"
        f"  </detail>\n"
        f"</event>"
    )
    return cot_xml


def zmeta_to_cot_uncertainty_circle(zmeta_state_event, radius_m, cot_config=None):
    """Convert a ZMeta STATE_EVENT into CoT with an explicit uncertainty ring.

    Args:
        zmeta_state_event: ZMeta STATE_EVENT dict.
        radius_m: Uncertainty radius in metres.
        cot_config: Optional config dict (see zmeta_to_cot).

    Returns:
        CoT XML string with <circle> element, or None.
    """
    import xml.etree.ElementTree as ET

    cot_xml = zmeta_to_cot(zmeta_state_event, cot_config=cot_config)
    if not cot_xml:
        return None

    try:
        radius = float(radius_m)
    except (TypeError, ValueError):
        return None

    # NaN fails every comparison, so `radius <= 0` alone lets NaN through and
    # draws <circle radius="nan"> - an uncertainty ring that states no
    # uncertainty. inf passes the same test (R1-11 A-01).
    if _is_non_finite(radius) or radius <= 0:
        return None

    root = ET.fromstring(cot_xml)
    detail = root.find("detail")
    if detail is None:
        detail = ET.SubElement(root, "detail")

    ET.SubElement(detail, "circle", attrib={"radius": str(radius)})
    return ET.tostring(root, encoding="unicode")
