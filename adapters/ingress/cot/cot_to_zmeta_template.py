from datetime import datetime

from adapters.ingress.time_utils import coerce_timing_quality, normalize_utc_z, utc_now_z
from zmeta_uuid import uuid7


DEFAULT_VALID_FOR_MS = 5000
PROMOTION_POLICY_ID = "PROMOTE-COT-STATE-V1"

# CoT's documented unknown-value convention for point@hae (the same 9999999.0
# this repo's egress sibling emits for ce/le/hae when a value is unknown).
# point@hae is a required numeric attribute with no way to be absent, so
# "altitude unknown" arrives as this number and must never be promoted into
# canonical payload.geo.alt_m as a real 9,999,999 m HAE claim: alt_m carries
# no upper bound in the v1.0 schema, so the sentinel is present, finite, and
# schema-clean, which is the altitude-datum laundering shape (doctrine C1-01).
COT_UNKNOWN_ALTITUDE = 9999999.0


def _iso_now():
    return utc_now_z()


def _parse_ts(value):
    if not value or not isinstance(value, str):
        return None
    if value.endswith("Z"):
        value = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _compute_valid_for_ms(start_ts, stale_ts):
    start_dt = _parse_ts(start_ts)
    stale_dt = _parse_ts(stale_ts)
    if start_dt and stale_dt:
        delta_ms = int((stale_dt - start_dt).total_seconds() * 1000)
        if delta_ms > 0:
            return delta_ms
    return DEFAULT_VALID_FOR_MS


def _extract_confidence(cot):
    if "confidence" in cot:
        return cot["confidence"]
    detail = cot.get("detail")
    if isinstance(detail, dict) and "confidence" in detail:
        return detail["confidence"]
    return None


def _detail_value(cot, key, default=None):
    if key in cot:
        return cot.get(key)
    detail = cot.get("detail")
    if isinstance(detail, dict) and key in detail:
        return detail.get(key)
    return default


def _declared_2d_marker(cot):
    """Read the egress sibling's <geo_dimensionality value="2D"> detail marker.

    The egress emits the marker (with an optional geo_status attribute) so a
    consumer can tell a declared horizontal-only fix apart from the ambiguous
    absent-altitude case, both of which carry the same point@hae sentinel on
    the wire. Parsers deliver the element either as a bare string ("2D") or as
    an attribute dict ({"value": "2D", "geo_status": ...}); both shapes are
    accepted here.

    Returns (declared_2d, carried_geo_status).
    """
    marker = _detail_value(cot, "geo_dimensionality")
    if isinstance(marker, str):
        return marker == "2D", None
    if isinstance(marker, dict):
        return marker.get("value") == "2D", marker.get("geo_status")
    return False, None


def cot_dict_to_zmeta_track_state(cot: dict) -> dict:
    """
    Template: Convert a parsed CoT dict into a ZMeta TRACK_STATE event.

    Altitude datum (contract 6.2, doctrine C1-01): CoT point@hae is WGS-84 HAE
    by the CoT specification, so a real hae value maps to canonical
    payload.geo.alt_m unconverted under the 1.0 stamp. Two inputs never reach
    alt_m: the 9999999.0 unknown-value convention (CoT's only way to say
    "altitude unknown" in a required numeric attribute), and any input whose
    <geo_dimensionality value="2D"> detail marker declares a horizontal-only
    fix. Both degrade to the declared 2-D form (doctrine A1-02: geo without
    alt_m plus dimensionality "2D" and quality.geo_status, under a forced
    1.1.0 stamp, since dimensionality is v1.1.0 vocabulary). A "2D" marker
    beside a real hae is the A1-02 coherence contradiction and refuses, the
    same rule the egress applies before emission. An absent hae still refuses
    the whole promotion: absence is ambiguous where the sentinel is an
    explicit "unknown" claim.
    """
    if not isinstance(cot, dict):
        raise ValueError("cot must be a dict")

    uid = cot.get("uid") or cot.get("id") or "cot-unknown"
    point = cot.get("point") or {}
    lat = point.get("lat")
    lon = point.get("lon")
    hae = point.get("hae")
    if lat is None or lon is None or hae is None:
        raise ValueError("cot point must include lat/lon/hae")

    # The sentinel comparison happens after float coercion because a lenient
    # upstream parser can deliver point attributes as strings. A non-numeric
    # hae keeps the legacy path and is refused by the schema gate downstream,
    # unchanged from before this guard existed.
    try:
        hae_value = float(hae)
    except (TypeError, ValueError):
        hae_value = None
    hae_is_unknown = hae_value is not None and hae_value == COT_UNKNOWN_ALTITUDE

    declared_2d, carried_geo_status = _declared_2d_marker(cot)
    if declared_2d and not hae_is_unknown:
        # The egress refuses to build a "2D" marker beside a real altitude
        # (A1-02 coherence), so this shape only arrives hand-built or
        # corrupted; promoting either half would assert a claim the message
        # contradicts.
        raise ValueError(
            "cot declares geo_dimensionality 2D but point.hae carries a real altitude"
        )

    if hae_is_unknown or declared_2d:
        # Horizontal-only promotion: the fix is real, the vertical is an
        # explicit "unknown", so the declared 2-D form travels instead of a
        # fabricated or laundered altitude. dimensionality is v1.1.0
        # vocabulary, so this branch must stamp 1.1.0 (the locked v1.0 geo
        # def is additionalProperties:false over lat/lon/alt_m).
        geo = {"lat": lat, "lon": lon, "dimensionality": "2D"}
        zmeta_version = "1.1.0"
        # A declared 2-D geo cannot sit beside geo_status AVAILABLE (A1-02
        # coherence arm 2), so a carried marker status is honored only when
        # it asserts something else, e.g. STALE from the source event.
        if carried_geo_status and str(carried_geo_status) != "AVAILABLE":
            geo_status = str(carried_geo_status)
        else:
            geo_status = "VERTICAL_UNAVAILABLE"
    else:
        geo = {"lat": lat, "lon": lon, "alt_m": hae}
        zmeta_version = "1.0"
        geo_status = None

    base_ts = cot.get("time") or cot.get("start")
    ts = normalize_utc_z(base_ts) or _iso_now()
    valid_for_ms = _compute_valid_for_ms(base_ts, cot.get("stale"))

    confidence = _extract_confidence(cot)
    if confidence is None:
        raise ValueError("cot must include confidence for STATE_EVENT")

    based_on = cot.get("based_on")
    detail = cot.get("detail")
    if based_on is None and isinstance(detail, dict):
        based_on = detail.get("based_on")
    if not based_on:
        raise ValueError("cot must include based_on lineage event ids")

    # The reflection check is a verification this template never performs,
    # so its verdict must arrive message-carried — never self-asserted
    # (contract 4.5.1; same rule the SAPIENT ingress enforces).
    loop_status = _detail_value(cot, "loop_status")
    if not loop_status:
        raise ValueError("cot must carry loop_status (detail.loop_status)")

    source_event_uid = str(_detail_value(cot, "source_event_uid", uid))
    promotion = {
        "state_category": "PROMOTED_EXTERNAL_STATE",
        "origin_kind": str(_detail_value(cot, "origin_kind", "EXTERNAL_REPORT")),
        "projection_id": "cot",
        "promotion_policy_id": str(_detail_value(cot, "promotion_policy_id", PROMOTION_POLICY_ID)),
        "trust_ref": str(_detail_value(cot, "trust_ref", "producer-authority:cot-ingress")),
        "lineage_status": str(_detail_value(cot, "lineage_status", "EXTERNAL_SOURCE")),
        "loop_status": str(loop_status),
        "confidence_basis": str(
            _detail_value(cot, "confidence_basis", "EXPLICIT_EXTERNAL_CONFIDENCE")
        ),
        "source_event_uid": source_event_uid,
        "freshness_ms": valid_for_ms,
    }
    source_zmeta_event_id = _detail_value(cot, "source_zmeta_event_id")
    if source_zmeta_event_id:
        promotion["source_zmeta_event_id"] = str(source_zmeta_event_id)

    payload = {
        "track_id": str(uid),
        "geo": geo,
        "valid_for_ms": valid_for_ms,
        "timing_quality": coerce_timing_quality(cot.get("timing_quality"), event_ts=ts),
        "extensions": {"external_promotion": promotion},
    }
    if geo_status is not None:
        payload["quality"] = {"geo_status": geo_status}
    cot_type = cot.get("type")
    if cot_type:
        payload["class"] = str(cot_type)

    event_id = str(uuid7())
    event = {
        "zmeta_version": zmeta_version,
        "event": {
            "event_id": event_id,
            "event_type": "STATE_EVENT",
            "event_subtype": "TRACK_STATE",
            "ts": ts,
        },
        "source": {
            "platform_id": str(cot.get("platform_id") or uid),
            "node_role": "GATEWAY",
            "producer": str(cot.get("producer") or "cot-ingress"),
        },
        "payload": payload,
        "confidence": confidence,
        "lineage": {
            "based_on": [str(item) for item in based_on],
            "transform": f"promote:cot@template:{promotion['promotion_policy_id']}",
        },
    }

    return event
