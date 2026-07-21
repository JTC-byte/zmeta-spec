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

from zmeta_uuid import uuid7

# Policy decisions that bound an event to a restricted consumer set; a
# coalition SAPIENT export is outside every such set (semantics contract
# 3.3). Vocabulary matches tools/filter_risk.py DECISION_RANKS.
_REFUSING_POLICY_DECISIONS = frozenset({"QUARANTINE_ACCEPT", "REJECTED"})

# Soft-accept decisions that must stay visible on the exported detection as
# a zmeta.risk self-label (contract 3.3: soft acceptance must not make
# risky data look clean).
_SELF_LABEL_POLICY_DECISIONS = frozenset({"WARN_ACCEPT", "DEGRADED_ACCEPT"})

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
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    return datetime.fromisoformat(ts).astimezone(timezone.utc)


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


def zmeta_state_to_sapient_detection(event, *, node_id, use_labels=None, export_use="COALITION_EXPORT"):
    """Convert a ZMeta STATE_EVENT/TRACK_STATE into a SAPIENT DetectionReport dict.

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

    Returns:
        Proto3-JSON-shaped SapientMessage dict carrying a DetectionReport,
        or None if the event cannot be honestly projected (wrong
        type/subtype, missing ts/track_id, partial geo, quarantined or
        rejected by policy, or export-path use prohibited).
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

    # All-or-nothing geo: DetectionReport's location oneof is mandatory and
    # SAPIENT z is an explicit claim — a partial position cannot be
    # exported without inventing the missing axis (contract 6.8).
    geo = payload.get("geo") or {}
    lat = geo.get("lat")
    lon = geo.get("lon")
    alt_m = geo.get("alt_m")
    if lat is None or lon is None or alt_m is None:
        return None

    risk_records = _risk_records(payload)
    caller_records = [use_labels] if isinstance(use_labels, dict) else []

    for record in risk_records:
        decision = str(record.get("policy_decision", "")).strip().upper()
        if decision in _REFUSING_POLICY_DECISIONS:
            return None
    for record in risk_records + caller_records:
        if _blocks_export(record, str(export_use).strip().upper()):
            return None

    detection = {
        "report_id": str(uuid7()),
        "object_id": track_id,
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
        # an event without one exports no classification confidence claim.
        confidence = event.get("confidence")
        if confidence is not None:
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
    label_records = [
        _risk_label_entry(record)
        for record in risk_records
        if str(record.get("policy_decision", "")).strip().upper() in _SELF_LABEL_POLICY_DECISIONS
    ]
    for record in caller_records:
        entry = _risk_label_entry(record)
        if entry.get("allowed_uses") or entry.get("prohibited_uses"):
            label_records.append(entry)
    if label_records:
        object_info.append({
            "type": "zmeta.risk",
            "value": json.dumps(label_records, separators=(",", ":"), sort_keys=True),
        })

    timing_quality = payload.get("timing_quality")
    if isinstance(timing_quality, dict) and timing_quality.get("sync_state") != "LOCKED":
        object_info.append({
            "type": "zmeta.timing_quality",
            "value": json.dumps(timing_quality, separators=(",", ":"), sort_keys=True),
        })

    if object_info:
        detection["object_info"] = object_info

    return {
        "timestamp": _utc_z(_parse_utc(ts)),
        "node_id": node_id,
        "detection_report": detection,
    }
