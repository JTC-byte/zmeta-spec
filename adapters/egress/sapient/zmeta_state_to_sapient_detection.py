"""ZMeta STATE_EVENT to SAPIENT (BSI Flex 335 v2.0) DetectionReport egress adapter.

Produces a plain dict shaped like a proto3-JSON SapientMessage carrying a
DetectionReport, for a SAPIENT DMM/fusion consumer. Wire protobuf encoding
is out of scope — a downstream SAPIENT transport encodes the dict
(consistent with the JREAP/KLV egress projections).

This is a lossy projection (SAPIENT_EGRESS_LOSS_NOTES below enumerates the
dropped concerns). What must NOT be lossy is the honesty context:

  - An event a policy quarantined (or rejected) never exports at all —
    quarantine means a bounded consumer set, and a coalition SAPIENT feed
    is outside it (semantics contract 3.3).
  - An event whose risk adjudication or caller-supplied use labels
    prohibit the export path (default use label COALITION_EXPORT) is
    refused, not exported clean.
  - A warn/degrade adjudication or degraded timing travels WITH the data
    as `object_info` self-labels (`zmeta.risk` / `zmeta.timing_quality`)
    per the label-not-launder doctrine (contract 3.3). Stock SAPIENT DMMs
    ignore unknown object_info types, so the labels are safe-to-ignore for
    consumers that cannot read them and filterable for those that can.
"""

import json
import math
from datetime import datetime, timezone

from adapters.egress.sapient.ulid_util import is_ulid, ulid_from_ts_ms

# Policy decisions that bound an event to a restricted consumer set; a
# coalition SAPIENT export is outside every such set (semantics contract
# 3.3). Vocabulary matches tools/filter_risk.py DECISION_RANKS.
_REFUSING_POLICY_DECISIONS = frozenset({"QUARANTINE_ACCEPT", "REJECTED"})

# Soft-accept decisions that must stay visible on the exported detection as
# a zmeta.risk self-label (contract 3.3: soft acceptance must not make
# risky data look clean).
_SELF_LABEL_POLICY_DECISIONS = frozenset({"WARN_ACCEPT", "DEGRADED_ACCEPT"})

# The complete governed decision vocabulary (tools/filter_risk.py
# DECISION_RANKS). filter_risk maps any OTHER decision string — including
# deployment-local labels, which contract 3.3 explicitly permits — to max
# rank (REJECTED) and blocks it; this egress fails closed the same way
# rather than exporting the record clean to the coalition feed.
_KNOWN_POLICY_DECISIONS = frozenset({
    "IGNORED",
    "WARN_ACCEPT",
    "DEGRADED_ACCEPT",
    "QUARANTINE_ACCEPT",
    "REJECTED",
})

# Risk-record keys that travel in the zmeta.risk self-label. Identity and
# scope keys are dropped: the label constrains use, it does not re-export
# the whole diagnostic.
_RISK_LABEL_KEYS = (
    "risk_dimension",
    "reason_code",
    "policy_decision",
    "policy_ref",
    "allowed_uses",
    "prohibited_uses",
)

# Dropped-concern register for this projection. ZMeta remains the source of
# truth; the SAPIENT detection is a one-directional projection and a
# re-import of it is never equal to the original (semantics contract 4.5.1).
SAPIENT_EGRESS_LOSS_NOTES = {
    "lineage": (
        "lineage.based_on and lineage.transform are dropped; the SAPIENT "
        "DetectionReport has no lineage carrier. Recover provenance through "
        "the originating ZMeta event, never from the SAPIENT side."
    ),
    "timing_quality": (
        "payload.timing_quality is dropped except when degraded "
        "(sync_state != LOCKED), where it travels as the "
        "zmeta.timing_quality object_info self-label. A clean LOCKED "
        "timing claim does not export at all."
    ),
    "risk_adjudication": (
        "warn/degrade adjudication records travel only as the zmeta.risk "
        "object_info self-label (compact JSON); quarantined/rejected "
        "events are refused outright."
    ),
    "valid_for_ms": (
        "the ZMeta staleness contract is dropped; DetectionReport has no "
        "TTL/stale field. SAPIENT consumers apply their own aging."
    ),
    "source_summary": "dropped; no honest DetectionReport carrier.",
    "geo_uncertainty": (
        "geo.error_ellipse_m is dropped; SAPIENT Location x/y/z_error are "
        "per-axis scalars and projecting an oriented ellipse onto them "
        "would misstate the error model."
    ),
    "stability_last_seen": (
        "payload.stability and payload.last_seen_ts are dropped; no "
        "DetectionReport carrier."
    ),
    "extensions": (
        "payload.extensions (beyond the risk self-label above) are "
        "dropped; vendor extension content is not re-exported across an "
        "external boundary."
    ),
}


def _parse_utc(ts):
    if not isinstance(ts, str):
        # TypeError so the caller's documented None-refusal path handles a
        # non-string ts; bare .endswith would raise AttributeError past it.
        raise TypeError(f"ts must be a string, got {type(ts).__name__}")
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    return datetime.fromisoformat(ts).astimezone(timezone.utc)


def _is_finite_number(value):
    # Finite only: a NaN/inf coordinate, confidence, or rate is not an
    # honest claim and must refuse, not project (contract 8.1 / 6.8).
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        # ``math.isfinite`` RAISES on a Python int outside the float64
        # range, and ``json.loads`` builds exactly such an int from a
        # plain integer literal — so a 400-digit number in geo, confidence
        # or heading/speed would raise out of this projection instead of
        # refusing, past the documented None contract. A value with no
        # float64 form is not a claim a SAPIENT float field can carry.
        # Mirrors the ingress guard (adapters/ingress/sapient/
        # sapient_to_zmeta.py _is_number), same reasoning, same answer.
        return False


def _honest_label_json(value):
    """Compact JSON for an ``object_info`` self-label, or None if it cannot
    be stated honestly.

    ``allow_nan=False`` is the load-bearing argument. Python's default
    emits the bare tokens ``NaN``/``Infinity``, which are not JSON
    (RFC 8259 s6), and because a self-label rides INSIDE a JSON string an
    outer ``allow_nan=False`` over the whole message cannot see them —
    the corruption is invisible to every check upstream of the consumer's
    own parse.

    Refusing the event is the proportionate disposition rather than
    dropping the offending field or the whole label: these labels are the
    only channel carrying risk/degradation context across the coalition
    boundary (contract 3.3, label-don't-launder), so a detection exported
    with the label dropped, or with the timing bound silently omitted
    (contract 5.3/5.9 — ``est_error_ms`` MUST NOT be omitted), is exactly
    the laundering the labels exist to prevent. Same answer this module
    already gives a non-finite geo, confidence or rate.
    """
    try:
        return json.dumps(
            value, separators=(",", ":"), sort_keys=True, allow_nan=False
        )
    except (ValueError, TypeError):
        # ValueError: a non-finite float anywhere in the label.
        # TypeError: a value with no JSON form, or mixed key types that
        # sort_keys cannot order. Both mean the label cannot be stated.
        return None


def _utc_z(dt):
    return dt.isoformat().replace("+00:00", "Z")


def _normalized_uses(value):
    # Mirrors tools/filter_risk.py _list_values so egress and the operator
    # risk-filter tooling adjudicate the same labels the same way.
    if isinstance(value, list):
        return [str(item).strip().upper() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip().upper()]
    return []


def _risk_records(payload):
    extensions = payload.get("extensions", {})
    if not isinstance(extensions, dict):
        return []
    records = extensions.get("risk_adjudication", [])
    if not isinstance(records, list):
        return []
    return [record for record in records if isinstance(record, dict)]


def _blocks_export(record, export_use):
    prohibited = _normalized_uses(record.get("prohibited_uses"))
    if export_use in prohibited:
        return True
    # allowed_uses is a positive grant list (tools/filter_risk.py
    # use_not_allowed): when present, any use it omits is not granted.
    allowed = _normalized_uses(record.get("allowed_uses"))
    if allowed and export_use not in allowed:
        return True
    return False


def _risk_label_entry(record):
    entry = {key: record[key] for key in _RISK_LABEL_KEYS if key in record}
    if "allowed_uses" in entry:
        entry["allowed_uses"] = _normalized_uses(entry["allowed_uses"])
    if "prohibited_uses" in entry:
        entry["prohibited_uses"] = _normalized_uses(entry["prohibited_uses"])
    return entry


def zmeta_state_to_sapient_detection(event, *, node_id, use_labels=None, export_use="COALITION_EXPORT", object_map=None):
    """Convert a ZMeta STATE_EVENT/TRACK_STATE into a SAPIENT DetectionReport dict.

    Id discipline (SAPIENT proto is_ulid; Apex strictIdFormat rejects
    violations): `report_id` is adapter-derived — a fresh ULID whose
    48-bit timestamp component is the event's own `event.ts`, never the
    wall clock. `object_id` is caller-owned identity: a ULID `track_id`
    passes through unchanged; a non-ULID `track_id` must resolve through
    `object_map` to a caller-owned SAPIENT ULID or the event is refused.
    Object identity continuity is deployment state — the adapter never
    mints a fresh identity per report, which would shred track continuity
    on the SAPIENT side.

    Args:
        event: ZMeta event dict. Must have event_type=STATE_EVENT and
            event_subtype=TRACK_STATE.
        node_id: SAPIENT node UUID of the ZMeta gateway emitting the
            detection.
        use_labels: Optional caller-supplied use-label dict
            ({"allowed_uses": [...], "prohibited_uses": [...]}) for policy
            adjudication that rides outside the event. Adjudicated exactly
            like an event-carried risk record, and any use restriction it
            carries travels in the zmeta.risk self-label.
        export_use: The use label this export path consumes under (default
            "COALITION_EXPORT", semantics contract 3.3 vocabulary). An
            event whose labels prohibit — or whose grant list omits — this
            use is refused.
        object_map: Optional dict mapping ZMeta track_id to the
            caller-owned SAPIENT object_id ULID for that track. Consulted
            only when `track_id` is not itself a ULID; a mapped value that
            is not a valid ULID is refused, never passed through.

    Returns:
        Proto3-JSON-shaped SapientMessage dict carrying a DetectionReport,
        or None if the event cannot be honestly projected (wrong
        type/subtype, missing ts/track_id, an unparseable ts or one
        outside the ULID timestamp range, no ULID object identity,
        partial or non-finite geo, quarantined or rejected by policy,
        export-path use prohibited, or an honesty self-label that cannot
        be serialized as honest JSON). This projection never raises.
    """
    if event.get("event", {}).get("event_type") != "STATE_EVENT":
        return None
    if event.get("event", {}).get("event_subtype") != "TRACK_STATE":
        return None

    payload = event.get("payload", {})

    # Envelope timestamp is the event's own ts: stamping translate-time wall
    # clock would fabricate freshness (semantics contract 9.5).
    ts = event.get("event", {}).get("ts")
    if not ts:
        return None

    if not node_id:
        return None

    track_id = payload.get("track_id")
    if not track_id:
        return None

    # object_id is caller-owned identity (see docstring): ULID track_ids
    # pass through; anything else must resolve through object_map to a
    # valid ULID or the event is refused — never a freshly minted id.
    if is_ulid(track_id):
        object_id = track_id
    else:
        object_id = (object_map or {}).get(track_id)
        if not is_ulid(object_id):
            return None

    # All-or-nothing geo: DetectionReport's location oneof is mandatory and
    # SAPIENT z is an explicit claim — a partial position cannot be
    # exported without inventing the missing axis (contract 6.8).
    geo = payload.get("geo") or {}
    lat = geo.get("lat")
    lon = geo.get("lon")
    alt_m = geo.get("alt_m")
    if not (_is_finite_number(lat) and _is_finite_number(lon) and _is_finite_number(alt_m)):
        return None

    risk_records = _risk_records(payload)
    caller_records = [use_labels] if isinstance(use_labels, dict) else []

    for record in risk_records:
        decision = str(record.get("policy_decision", "")).strip().upper()
        if decision in _REFUSING_POLICY_DECISIONS:
            return None
        if decision not in _KNOWN_POLICY_DECISIONS:
            # Unknown, local, or missing decision labels rank as REJECTED
            # in tools/filter_risk.py (_decision_rank); fail closed here
            # too — never export an unadjudicable record clean.
            return None
    for record in risk_records + caller_records:
        if _blocks_export(record, str(export_use).strip().upper()):
            return None

    # report_id timestamp component is the event's own ts (never wall
    # clock — same honesty rule as the envelope timestamp below). A ts
    # that does not parse, OR that parses to an instant a ULID cannot
    # carry, is refused per the documented None contract, never raised
    # out of the projection.
    #
    # The mint MUST stay inside this guard: ulid_from_ts_ms raises
    # ValueError for any epoch-ms outside [0, 2**48), and a pre-1970
    # event.ts — the canonical bad-clock symptom on an unsynced edge
    # node, and schema-valid — lands there. Refusal is the only honest
    # answer: the ULID's timestamp component is a claim about the event,
    # so clamping it to 0 (or reading the wall clock) would fabricate a
    # time this event does not have. Since the whole message is keyed to
    # that instant, the event is unusable across this projection without
    # it. The upper bound is unreachable from an ISO-8601 datetime
    # (2**48 ms runs to year 10889, past datetime.max).
    #
    # OSError is in the tuple for the second member of the same class:
    # `_parse_utc` calls `.astimezone()`, which delegates to the platform
    # for a NAIVE datetime and raises OSError(EINVAL) on Windows for any
    # pre-1970 instant — so a zone-less pre-epoch ts escaped the original
    # (ValueError, TypeError) guard before it ever reached the mint.
    try:
        time_dt = _parse_utc(ts)
        report_id = ulid_from_ts_ms(round(time_dt.timestamp() * 1000))
    except (ValueError, TypeError, OverflowError, OSError):
        return None

    detection = {
        "report_id": report_id,
        "object_id": object_id,
        "location": {
            "x": lon,
            "y": lat,
            "z": alt_m,
            "coordinate_system": "LOCATION_COORDINATE_SYSTEM_LAT_LNG_DEG_M",
            "datum": "LOCATION_DATUM_WGS84_E",
        },
    }

    track_class = payload.get("class")
    if track_class:
        classification = {"type": track_class}
        # Confidence is projected as-is, never increased (contract 4.5.1);
        # an event without one exports no classification confidence claim,
        # and a present-but-non-finite one refuses the event outright.
        confidence = event.get("confidence")
        if confidence is not None:
            if not _is_finite_number(confidence):
                return None
            classification["confidence"] = confidence
        detection["classification"] = [classification]

    # ENU velocity only when both heading and speed are real claims.
    # heading_deg is contractually degrees true north (contract 6.4), so
    # east/north decomposition is frame-preserving math, not fabrication.
    # up_rate is always omitted: TrackStatePayload carries no climb rate
    # and SAPIENT's optional up_rate left absent is an honest "unknown".
    heading_deg = payload.get("heading_deg")
    speed_mps = payload.get("speed_mps")
    if heading_deg is not None and speed_mps is not None:
        if not (_is_finite_number(heading_deg) and _is_finite_number(speed_mps)):
            return None
        heading_rad = math.radians(heading_deg)
        detection["enu_velocity"] = {
            "east_rate": speed_mps * math.sin(heading_rad),
            "north_rate": speed_mps * math.cos(heading_rad),
        }

    # Label-not-launder self-labels (contract 3.3): soft-accepted risk and
    # degraded timing stay visible on the exported detection. object_info
    # is SAPIENT's free type/value channel; stock DMMs ignore unknown
    # types, honesty-aware consumers filter on them.
    object_info = []
    label_records = []
    for record in risk_records:
        decision = str(record.get("policy_decision", "")).strip().upper()
        entry = _risk_label_entry(record)
        if decision in _SELF_LABEL_POLICY_DECISIONS:
            label_records.append(entry)
        elif entry.get("allowed_uses") or entry.get("prohibited_uses"):
            # An accepted record (e.g. IGNORED) that still carries use
            # restrictions: the restriction must stay visible downstream,
            # not vanish with the dropped extensions.
            label_records.append(entry)
    for record in caller_records:
        entry = _risk_label_entry(record)
        if entry.get("allowed_uses") or entry.get("prohibited_uses"):
            label_records.append(entry)
    if label_records:
        # _risk_label_entry normalizes only allowed_uses/prohibited_uses;
        # risk_dimension, reason_code, policy_decision and policy_ref are
        # copied verbatim, so a non-finite float reaches this dump too.
        risk_value = _honest_label_json(label_records)
        if risk_value is None:
            return None
        object_info.append({"type": "zmeta.risk", "value": risk_value})

    timing_quality = payload.get("timing_quality")
    if isinstance(timing_quality, dict) and timing_quality.get("sync_state") != "LOCKED":
        # This label exists ONLY when timing is degraded, so it is the one
        # channel keeping the events that need it most honest. A verbatim
        # pass-through of an event sub-object: est_error_ms is the field a
        # broken clock corrupts, and NaN is not a worst-case upper bound.
        timing_value = _honest_label_json(timing_quality)
        if timing_value is None:
            return None
        object_info.append({"type": "zmeta.timing_quality", "value": timing_value})

    if object_info:
        detection["object_info"] = object_info

    return {
        "timestamp": _utc_z(time_dt),
        "node_id": node_id,
        "detection_report": detection,
    }
