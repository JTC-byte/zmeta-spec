import json
import importlib.util
import math
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

import pytest

from adapters.ingress.mavlink.mavlink_to_zmeta_template import (
    decode_attitude,
    decode_global_position_int,
    decode_gps_raw_int,
    decode_sys_status,
    mavlink_decoded_to_zmeta_system_events,
    translate_link_status,
    translate_platform_state,
    translate_time_status,
)


ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = ROOT / "schema" / "zmeta-event-1.0.schema.json"
SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
VALIDATOR = Draft202012Validator(SCHEMA, format_checker=FormatChecker())
VALIDATORS_PATH = ROOT / "gateway" / "src" / "validators.py"
spec = importlib.util.spec_from_file_location("zmeta_validators", VALIDATORS_PATH)
validators = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validators)
POLICY = validators.load_policy(ROOT / "policy")


_PARENT_EVENT_ID = "019c2b5c-c053-70e1-b6aa-340000000001"

# The three link measurements the v1.0 schema requires on a LINK_STATUS
# payload. They are caller-supplied because the adapter refuses to fabricate
# them (see test_mavlink_link_status_refuses_to_fabricate_link_health).
_LINK_METRICS = {
    "latency_ms": 42.0,
    "packet_loss_pct": 1.5,
    "throughput_bps": 250000,
}


def test_mavlink_platform_state_promotion_authority_valid():
    event = translate_platform_state(
        {
            "lat": 34.0,
            "lon": -118.0,
            "alt_m": 120.0,
            "heading_deg": 90.0,
            "speed_mps": 12.0,
            "gps_fix_type": 3,
            "satellites_visible": 10,
            "source_event_uid": "mavlink:sysid-1:seq-1",
            "based_on": [_PARENT_EVENT_ID],
            "loop_status": "CHECKED_NOT_REFLECTION",
        },
        platform_id="uav-1",
        producer="mavlink-adapter",
        ts="2025-01-17T15:20:00+00:00",
    )

    assert event["event"]["event_type"] == "STATE_EVENT"
    assert event["payload"]["extensions"]["external_promotion"]["promotion_policy_id"] == (
        "PROMOTE-MAVLINK-STATE-V1"
    )
    assert (
        event["payload"]["extensions"]["external_promotion"]["loop_status"]
        == "CHECKED_NOT_REFLECTION"
    )
    assert event["lineage"]["transform"].startswith("promote:mavlink-telemetry@")
    assert event["lineage"]["based_on"] == [_PARENT_EVENT_ID]
    VALIDATOR.validate(event)
    ok, violations = validators.validate_producer_authority(
        event, POLICY["producer_authority"], POLICY["violation_severities"]
    )
    assert ok, violations


_BASE_STATE = {
    "lat": 34.0,
    "lon": -118.0,
    "alt_m": 120.0,
    "speed_mps": 12.0,
    "gps_fix_type": 3,
    "satellites_visible": 10,
    "source_event_uid": "mavlink:sysid-1:seq-1",
    "based_on": [_PARENT_EVENT_ID],
    # Message-carried reflection verdict: the template never self-asserts
    # it (contract 4.5.1) — see the refusal test below.
    "loop_status": "CHECKED_NOT_REFLECTION",
}


def _state_event(**overrides):
    translator_kwargs = {}
    if "heading_frame" in overrides:
        translator_kwargs["heading_frame"] = overrides.pop("heading_frame")
    if "heading_source" in overrides:
        translator_kwargs["heading_source"] = overrides.pop("heading_source")
    state = dict(_BASE_STATE)
    state.update(overrides)
    return translate_platform_state(
        state,
        platform_id="uav-1",
        producer="mavlink-adapter",
        ts="2025-01-17T15:20:00+00:00",
        **translator_kwargs,
    )


def test_mavlink_known_heading_without_frame_omits_canonical_heading():
    # GLOBAL_POSITION_INT.hdg does not declare a true-vs-magnetic reference,
    # so the adapter must not emit canonical payload.heading_deg by default.
    event = _state_event(heading_deg=90.0)

    assert "heading_deg" not in event["payload"]
    assert event["payload"]["quality"]["mavlink_hdg_frame_unknown_deg"] == 90.0
    assert "heading_source" not in event["payload"]["quality"]
    VALIDATOR.validate(event)


def test_mavlink_true_north_heading_frame_emits_canonical_heading():
    event = _state_event(
        heading_deg=90.0,
        heading_frame="TRUE_NORTH",
        heading_source="AHRS_TRUE",
    )

    assert event["payload"]["heading_deg"] == 90.0
    assert event["payload"]["quality"]["heading_source"] == "AHRS_TRUE"
    assert "mavlink_hdg_frame_unknown_deg" not in event["payload"]["quality"]
    VALIDATOR.validate(event)


def test_mavlink_invalid_heading_frame_rejected():
    import pytest

    with pytest.raises(ValueError, match="heading_frame"):
        _state_event(heading_deg=90.0, heading_frame="MAGNETIC_NORTH")


def test_mavlink_unknown_heading_omitted_not_fabricated():
    # decode_global_position_int yields heading_deg=None for hdg=UINT16_MAX;
    # the translator must omit heading_deg, never emit None or a 0.0 default.
    event = _state_event(heading_deg=None)

    assert "heading_deg" not in event["payload"]
    assert "mavlink_hdg_frame_unknown_deg" not in event["payload"]["quality"]
    VALIDATOR.validate(event)


def test_mavlink_absent_heading_omitted_not_defaulted_to_zero():
    event = _state_event()

    assert "heading_deg" not in event["payload"]
    VALIDATOR.validate(event)


def test_decode_global_position_int_unknown_hdg_yields_none():
    decoded = decode_global_position_int(
        {"lat": 340000000, "lon": -1180000000, "alt": 120000, "hdg": 65535}
    )

    assert decoded["heading_deg"] is None


def test_decode_global_position_int_missing_lat_lon_yields_none():
    # A GLOBAL_POSITION_INT without lat/lon must not decode to (0, 0); absent
    # coordinates decode to None so downstream refuses to fabricate a position.
    decoded = decode_global_position_int({"alt": 120000, "hdg": 65535})

    assert decoded["lat"] is None
    assert decoded["lon"] is None


def test_decode_global_position_int_present_lat_lon_preserved():
    decoded = decode_global_position_int(
        {"lat": 340000000, "lon": -1180000000, "alt": 120000, "hdg": 9000}
    )

    assert decoded["lat"] == 34.0
    assert decoded["lon"] == -118.0


def test_mavlink_refuses_null_island_without_fix():
    # ArduPilot emits lat=0, lon=0 before GPS lock (fix types 0/1). The adapter
    # must refuse to fabricate a null-island TRACK_STATE position.
    assert _state_event(lat=0.0, lon=0.0, gps_fix_type=0) is None
    assert _state_event(lat=0.0, lon=0.0, gps_fix_type=1) is None


def test_mavlink_refuses_absent_lat_lon():
    state = {k: v for k, v in _BASE_STATE.items() if k not in ("lat", "lon")}
    event = translate_platform_state(
        state,
        platform_id="uav-1",
        producer="mavlink-adapter",
        ts="2025-01-17T15:20:00+00:00",
    )

    assert event is None


def test_mavlink_refuses_missing_lineage_instead_of_fabricating():
    # STATE_EVENT lineage is mandatory (contract 4.8) and must reference real
    # events. Without caller-supplied based_on or source_zmeta_event_id, the
    # adapter refuses to emit rather than fabricating a parent id.
    state = {k: v for k, v in _BASE_STATE.items() if k != "based_on"}
    event = translate_platform_state(
        state,
        platform_id="uav-1",
        producer="mavlink-adapter",
        ts="2025-01-17T15:20:00+00:00",
    )

    assert event is None


def test_mavlink_source_zmeta_event_id_used_as_lineage_fallback():
    state = {k: v for k, v in _BASE_STATE.items() if k != "based_on"}
    state["source_zmeta_event_id"] = _PARENT_EVENT_ID
    event = translate_platform_state(
        state,
        platform_id="uav-1",
        producer="mavlink-adapter",
        ts="2025-01-17T15:20:00+00:00",
    )

    assert event["lineage"]["based_on"] == [_PARENT_EVENT_ID]
    VALIDATOR.validate(event)


def test_mavlink_system_events_omit_lineage_by_default():
    from adapters.ingress.mavlink.mavlink_to_zmeta_template import (
        translate_link_status,
        translate_time_status,
    )

    link = translate_link_status(
        platform_id="uav-1",
        ts="2025-01-17T15:20:00+00:00",
        **_LINK_METRICS,
    )
    time_status = translate_time_status(
        platform_id="uav-1",
        est_error_ms=1.0,
        last_sync_ts="2025-01-17T15:19:59+00:00",
        ts="2025-01-17T15:20:00+00:00",
    )

    assert "lineage" not in link
    assert "lineage" not in time_status
    VALIDATOR.validate(link)
    VALIDATOR.validate(time_status)


def test_mavlink_system_events_carry_caller_lineage_when_supplied():
    from adapters.ingress.mavlink.mavlink_to_zmeta_template import translate_link_status

    link = translate_link_status(
        platform_id="uav-1",
        ts="2025-01-17T15:20:00+00:00",
        based_on=[_PARENT_EVENT_ID],
        **_LINK_METRICS,
    )

    assert link["lineage"]["based_on"] == [_PARENT_EVENT_ID]
    VALIDATOR.validate(link)


def test_mavlink_null_island_with_2d_fix_still_emits():
    # A claimed 2D+ fix at exactly (0, 0) is not the no-fix signature; the
    # adapter keeps the position and lets quality/confidence carry the doubt.
    event = _state_event(lat=0.0, lon=0.0, gps_fix_type=2)

    assert event is not None
    assert event["payload"]["geo"]["lat"] == 0.0
    assert event["payload"]["geo"]["lon"] == 0.0
    VALIDATOR.validate(event)


def test_mavlink_no_fix_with_nonzero_coords_still_emits_degraded():
    # Stale-but-real coordinates without a current fix remain emitted with
    # geo_status STALE and floor confidence; only fabricated (0, 0) is refused.
    event = _state_event(gps_fix_type=0)

    assert event is not None
    assert event["payload"]["quality"]["geo_status"] == "STALE"
    assert event["confidence"] == 0.2
    VALIDATOR.validate(event)


def test_mavlink_task_ack_schema_valid():
    msg = {
        "msg_type": "MISSION_ACK",
        "task_id": "task-1",
        "original_event_id": "019c3ef3-98c4-7c99-8daf-3643ed0bc8ef",
        "state": "RECEIVED",
    }
    events = mavlink_decoded_to_zmeta_system_events(
        msg,
        platform_id="uav-1",
        producer="mavlink",
        ts="2025-01-17T15:20:00+00:00",
    )

    assert len(events) == 1
    event = events[0]
    assert event["event"]["event_type"] == "SYSTEM_EVENT"
    assert event["event"]["ts"] == "2025-01-17T15:20:00Z"
    assert event["payload"]["system_type"] == "TASK_ACK"
    VALIDATOR.validate(event)


def test_mavlink_time_status_normalizes_last_sync_ts():
    msg = {
        "msg_type": "SYSTEM_TIME",
        "state": "UP",
        "time_source": "GPS_PPS",
        "sync_state": "LOCKED",
        "est_error_ms": 1,
        "last_sync_ts": "2025-01-17T15:19:59+00:00",
    }
    events = mavlink_decoded_to_zmeta_system_events(
        msg,
        platform_id="uav-1",
        producer="mavlink",
        ts="2025-01-17T15:20:00+00:00",
    )

    event = events[0]
    assert event["event"]["ts"] == "2025-01-17T15:20:00Z"
    assert event["payload"]["metrics"]["last_sync_ts"] == "2025-01-17T15:19:59Z"
    VALIDATOR.validate(event)


def test_mavlink_without_loop_status_refuses_promotion():
    # The reflection verdict is never self-asserted (R1-11 R11-07): a
    # telemetry dict that does not carry loop_status refuses the promotion.
    state = {k: v for k, v in _BASE_STATE.items() if k != "loop_status"}
    event = translate_platform_state(
        state,
        platform_id="uav-1",
        producer="mavlink-adapter",
        ts="2025-01-17T15:20:00+00:00",
    )
    assert event is None


# ---------------------------------------------------------------------------
# R1-11 A-06: the fabricate-a-sentinel class.
#
# Contract 6.8 is an explicit MUST: "If any of lat, lon, or alt_m is missing,
# omit geo entirely. Missing values MUST be omitted, not zero-filled" and
# "Adapters MUST NOT emit zero-filled geospatial data to satisfy schema
# shape." The defect was `alt_m = _get("alt_m", 0.0)`, which projected an
# airborne platform reporting no altitude as being at exactly 0 m AMSL,
# labelled AVAILABLE at confidence 0.8, through every gate.
#
# These tests pin the whole family, not the one exemplar: every never-reported
# numeric this module could restate as a definite value, on the translator, on
# each of the four raw-message decoders, and on the composition of the two (a
# decoder that zero-fills defeats a translator-only guard entirely).
# ---------------------------------------------------------------------------


def test_mavlink_refuses_missing_alt_m_instead_of_zero_filling():
    # A-06, the reported exemplar: a real lat/lon with no altitude must not
    # become a concrete 0 m AMSL claim. geo is all-or-nothing and the v1.0
    # schema requires geo on TRACK_STATE, so the event refuses.
    state = {k: v for k, v in _BASE_STATE.items() if k != "alt_m"}
    assert translate_platform_state(
        state, platform_id="uav-1", ts="2025-01-17T15:20:00+00:00"
    ) is None


def test_mavlink_refuses_explicit_none_alt_m():
    # A decoder that maps an invalid-altitude flag to None reaches the same
    # refusal as an absent key - the guard is value-scoped, not key-scoped.
    assert _state_event(alt_m=None) is None


def test_mavlink_absent_speed_omitted_not_asserted_stationary():
    # payload.speed_mps is schema-optional; a 0.0 default asserts "stationary"
    # for a platform whose speed was never reported.
    state = {k: v for k, v in _BASE_STATE.items() if k != "speed_mps"}
    event = translate_platform_state(
        state, platform_id="uav-1", ts="2025-01-17T15:20:00+00:00"
    )

    assert "speed_mps" not in event["payload"]
    VALIDATOR.validate(event)


def test_mavlink_absent_gps_quality_omitted_but_still_degrades():
    # An unreported fix type / satellite count is omitted from quality rather
    # than restated as "no GPS / 0 satellites" - and the omission must still
    # drive the conservative decisions, never a cleaner-looking event.
    state = {
        k: v for k, v in _BASE_STATE.items()
        if k not in ("gps_fix_type", "satellites_visible")
    }
    event = translate_platform_state(
        state, platform_id="uav-1", ts="2025-01-17T15:20:00+00:00"
    )

    assert "gps_fix_type" not in event["payload"]["quality"]
    assert "satellites_visible" not in event["payload"]["quality"]
    assert event["payload"]["quality"]["geo_status"] == "STALE"
    assert event["confidence"] == 0.2
    VALIDATOR.validate(event)


def test_mavlink_unreported_fix_still_refuses_null_island():
    # The conservative floor must also hold for the refusal itself: with no
    # fix type reported, (0, 0) is still the no-fix signature and is refused.
    state = {k: v for k, v in _BASE_STATE.items() if k != "gps_fix_type"}
    state["lat"] = 0.0
    state["lon"] = 0.0
    assert translate_platform_state(
        state, platform_id="uav-1", ts="2025-01-17T15:20:00+00:00"
    ) is None


_GENERATED = object()
_INPUT_TS = "2025-01-17T15:20:00+00:00"
_EVENT_TS_Z = "2025-01-17T15:20:00Z"


def _reported_scalars(inputs):
    """Every scalar the caller actually supplied, as (type-name, value) pairs.

    Typed so that ``True`` cannot be satisfied by a reported ``1``.
    """
    out = set()

    def _collect(node):
        if isinstance(node, dict):
            for value in node.values():
                _collect(value)
        elif isinstance(node, list):
            for value in node:
                _collect(value)
        else:
            out.add((type(node).__name__, node))

    _collect(inputs)
    return out


def _undeclared_leaves(event, inputs, declared):
    """Scalar leaves of ``event`` that neither the inputs nor a declaration explains.

    Path-scoped and type-complete, both deliberately:

    - **Path-scoped.** A value-scoped allowlist authorises a literal
      *everywhere at once*: allowlisting 30000 for ``payload.valid_for_ms``
      would silently bless a brand-new fabricated 30000 at any other path,
      forever - and 30000 is this module's own house constant, exactly the
      number a future author reaches for when defaulting a duration field.
      Here a declaration authorises one value at one path; a value at any
      other path is still a finding, and a *different* value at a declared
      path is a finding too.
    - **Type-complete.** Strings, bools and None are checked as well as
      numbers. This module's promotion block wraps every default in
      ``str(...)`` - that is the house idiom - and every categorical verdict
      it emits (``payload.state``, ``quality.geo_status``,
      ``metrics.sync_state``) is a string. A numbers-only sweep is
      structurally unable to see a fabricated verdict, which is the more
      dangerous half of the class: an operator reads "UP" before they read a
      latency number.

    Declaring a path is the point of the guard, not an escape hatch from it:
    a value that is not telemetry has to be written down, with a reason, by
    whoever adds it. ``_GENERATED`` marks the few leaves whose value cannot
    be pinned (a uuid7, a version-bearing transform label); it exempts the
    value, never the path, so a new field still has to be declared.

    Deliberately written out here rather than derived from the module under
    test: a check that re-ran the adapter's own defaulting logic to build its
    expectation would be blind to that logic by construction.

    Stated limit: acceptance of *reported* values is value-scoped, not
    path-scoped - a fabricated value that happens to equal something the
    telemetry carried at another path is invisible to a single sweep. That is
    why the sweeps come in pairs: the minimum-telemetry case carries only a
    handful of deliberately distinctive inputs, so a fabrication that hides
    behind a reported value in the fully-populated case is still caught there
    (verified by mutation). A fabrication equal to a *declared* value at its
    own declared path is invisible by definition - that is what declaring it
    means - and a fabricated sub-object whose every leaf traces to an input is
    invisible too; neither is what this guard is for.

    Returns a list of ``(path, emitted, declared_or_None)`` findings.
    """
    reported = _reported_scalars(inputs)
    findings = []

    def _walk(node, path):
        if isinstance(node, dict):
            for key, value in node.items():
                _walk(value, f"{path}.{key}")
            return
        if isinstance(node, list):
            for index, value in enumerate(node):
                _walk(value, f"{path}[{index}]")
            return
        if path in declared:
            expected = declared[path]
            if expected is not _GENERATED and node != expected:
                findings.append((path, node, expected))
            return
        if (type(node).__name__, node) in reported:
            return
        findings.append((path, node, None))

    _walk(event, "$")
    return findings


def _envelope_declarations(event_type, event_subtype, node_role):
    """The envelope values every emitter in this module writes itself."""
    return {
        "$.zmeta_version": "1.0",
        "$.event.event_id": _GENERATED,  # uuid7, minted per event
        "$.event.event_type": event_type,
        "$.event.event_subtype": event_subtype,
        "$.event.ts": _EVENT_TS_Z,  # the caller's ts, normalized to Z
        "$.source.node_role": node_role,
    }


_PROMOTION_DECLARATIONS = {
    # Policy-scoped boundary evidence for the promotion decision. Every one of
    # these is an adapter constant, not telemetry, and is pinned by value.
    "$.payload.extensions.external_promotion.state_category": "PROMOTED_EXTERNAL_STATE",
    "$.payload.extensions.external_promotion.origin_kind": "EXTERNAL_REPORT",
    "$.payload.extensions.external_promotion.projection_id": "mavlink",
    "$.payload.extensions.external_promotion.promotion_policy_id": "PROMOTE-MAVLINK-STATE-V1",
    "$.payload.extensions.external_promotion.trust_ref": "producer-authority:mavlink-adapter",
    "$.payload.extensions.external_promotion.lineage_status": "EXTERNAL_SOURCE",
    "$.payload.extensions.external_promotion.confidence_basis": "GPS_FIX_CONFIDENCE",
    "$.payload.extensions.external_promotion.source_event_uid": f"mavlink:uav-1:{_EVENT_TS_Z}",
    "$.payload.extensions.external_promotion.freshness_ms": 30000,
}


def test_mavlink_minimum_state_emits_no_undeclared_leaf_anywhere():
    # Family-wide sweep rather than a per-field check: with every optional
    # telemetry field absent, no value anywhere in the emitted event may be one
    # the telemetry never carried and this test did not declare. This catches a
    # newly added default in a field no per-field assertion above names -
    # including a non-zero one (a zeros-only sweep cannot see it), one that
    # reuses a house constant at a new path (a value-scoped allowlist cannot
    # see it), and a categorical or str()-wrapped one (a numeric-only sweep
    # cannot see it).
    state = {
        "lat": 34.0517,
        "lon": -118.2437,
        "alt_m": 412.5,
        "based_on": [_PARENT_EVENT_ID],
        "loop_status": "CHECKED_NOT_REFLECTION",
    }
    kwargs = {
        "platform_id": "uav-1",
        "producer": "mavlink-adapter",
        "ts": _INPUT_TS,
    }
    declared = {
        **_envelope_declarations("STATE_EVENT", "TRACK_STATE", "GATEWAY"),
        **_PROMOTION_DECLARATIONS,
        # Composed from producer + platform_id, both caller-supplied.
        "$.payload.track_id": "mavlink-adapter-uav-1-platform-position",
        "$.payload.valid_for_ms": 30000,  # adapter policy constant
        # The conservative verdict for an unreported fix - never AVAILABLE.
        "$.payload.quality.geo_status": "STALE",
        # coerce_timing_quality's conservative unknown-timing block
        # (adapters/ingress/time_utils.py, not this module): an explicit
        # UNSYNCED / UNKNOWN source with a 60 s error bound.
        "$.payload.timing_quality.time_source": "UNKNOWN",
        "$.payload.timing_quality.sync_state": "UNSYNCED",
        "$.payload.timing_quality.est_error_ms": 60000,
        "$.payload.timing_quality.last_sync_ts": _EVENT_TS_Z,
        # _gps_fix_confidence floor for an unreported fix.
        "$.confidence": 0.2,
        # Carries ADAPTER_VERSION; its prefix is pinned by
        # test_mavlink_platform_state_promotion_authority_valid.
        "$.lineage.transform": _GENERATED,
    }
    event = translate_platform_state(state, **kwargs)

    undeclared = _undeclared_leaves(event, {**state, **kwargs}, declared)
    assert undeclared == [], f"values with no source in the telemetry: {undeclared}"
    VALIDATOR.validate(event)


def test_mavlink_every_emitted_leaf_traces_to_input_or_declaration():
    # The same provenance rule over a fully populated telemetry dict, so the
    # carry-through paths are covered too, not only the omission paths. Input
    # values are deliberately distinctive so a fabricated value cannot collide
    # with a real one.
    state = {
        "lat": 34.0517,
        "lon": -118.2437,
        "alt_m": 412.5,
        "speed_mps": 18.25,
        "heading_deg": 137.5,
        "gps_fix_type": 4,
        "satellites_visible": 17,
        "roll_deg": 2.75,
        "pitch_deg": -1.25,
        "yaw_deg": 137.5,
        "vx": 12.5,
        "vy": 13.25,
        "vz": -0.75,
        "battery_voltage": 22.4,
        "battery_remaining_pct": 63,
        "custom_mode": 5,
        "timing_quality": {
            "time_source": "GPS_PPS",
            "sync_state": "LOCKED",
            "est_error_ms": 3.5,
            "last_sync_ts": "2025-01-17T15:19:59+00:00",
        },
        "based_on": [_PARENT_EVENT_ID],
        "loop_status": "CHECKED_NOT_REFLECTION",
    }
    kwargs = {
        "platform_id": "uav-1",
        "producer": "mavlink-adapter",
        "ts": _INPUT_TS,
    }
    declared = {
        **_envelope_declarations("STATE_EVENT", "TRACK_STATE", "GATEWAY"),
        **_PROMOTION_DECLARATIONS,
        "$.payload.track_id": "mavlink-adapter-uav-1-platform-position",
        "$.payload.valid_for_ms": 30000,
        "$.payload.quality.geo_status": "AVAILABLE",
        "$.payload.quality.heading_source": "MAVLINK_GLOBAL_POSITION_INT_TRUE_NORTH",
        # Reported last_sync_ts, normalized to Z.
        "$.payload.timing_quality.last_sync_ts": "2025-01-17T15:19:59Z",
        # _gps_fix_confidence table value for a 3D+ fix.
        "$.confidence": 0.8,
        "$.lineage.transform": _GENERATED,
    }

    event = translate_platform_state(state, heading_frame="TRUE_NORTH", **kwargs)

    undeclared = _undeclared_leaves(event, {**state, **kwargs}, declared)
    assert undeclared == [], f"values with no source in the telemetry: {undeclared}"
    VALIDATOR.validate(event)


class _AttributeState:
    """A non-dict telemetry carrier, the other branch of the module's _get."""

    def __init__(self, **fields):
        self.__dict__.update(fields)


def test_mavlink_attribute_state_refuses_missing_alt_m():
    # translate_platform_state accepts an object as well as a dict, and the
    # object branch uses a different accessor (getattr, not dict.get). A guard
    # that only holds on the dict branch is half a guard.
    fields = {k: v for k, v in _BASE_STATE.items() if k != "alt_m"}
    assert translate_platform_state(
        _AttributeState(**fields), platform_id="uav-1", ts="2025-01-17T15:20:00+00:00"
    ) is None

    event = translate_platform_state(
        _AttributeState(**_BASE_STATE),
        platform_id="uav-1",
        ts="2025-01-17T15:20:00+00:00",
    )
    assert event["payload"]["geo"]["alt_m"] == 120.0
    VALIDATOR.validate(event)


def test_mavlink_attribute_state_omits_unreported_optional_numerics():
    fields = {
        k: v for k, v in _BASE_STATE.items()
        if k not in ("speed_mps", "gps_fix_type", "satellites_visible")
    }
    event = translate_platform_state(
        _AttributeState(**fields),
        platform_id="uav-1",
        ts="2025-01-17T15:20:00+00:00",
    )

    assert "speed_mps" not in event["payload"]
    assert "gps_fix_type" not in event["payload"]["quality"]
    assert "satellites_visible" not in event["payload"]["quality"]
    assert event["payload"]["quality"]["geo_status"] == "STALE"


def test_decode_global_position_int_absent_alt_and_velocity_yield_none():
    # The decoder half of the same class. A translator-only guard is defeated
    # by a decoder that zero-fills, because the state dict then carries a
    # definite 0.0 the translator cannot tell from a measurement.
    decoded = decode_global_position_int({"lat": 340000000, "lon": -1180000000})

    assert decoded["alt_m"] is None
    assert decoded["vx"] is None
    assert decoded["vy"] is None
    assert decoded["vz"] is None
    assert decoded["speed_mps"] is None


def test_decode_global_position_int_to_translate_refuses_without_alt():
    # End-to-end composition: the documented decode -> translate pipeline must
    # refuse, not emit 0 m AMSL. This is the pin an exemplar-only fix fails.
    state = decode_global_position_int(
        {"lat": 340000000, "lon": -1180000000, "hdg": 65535}
    )
    state.update(decode_gps_raw_int({"fix_type": 3, "satellites_visible": 12}))
    state["based_on"] = [_PARENT_EVENT_ID]
    state["loop_status"] = "CHECKED_NOT_REFLECTION"

    assert translate_platform_state(
        state, platform_id="uav-1", ts="2025-01-17T15:20:00+00:00"
    ) is None


def test_decode_global_position_int_reported_values_preserved():
    # The refusal must not cost the honest path: reported values still decode,
    # including a genuinely measured zero.
    decoded = decode_global_position_int(
        {"lat": 340000000, "lon": -1180000000, "alt": 120000,
         "vx": 500, "vy": 0, "vz": -100, "hdg": 9000}
    )

    assert decoded["alt_m"] == 120.0
    assert decoded["vx"] == 5.0
    assert decoded["vy"] == 0.0
    assert decoded["vz"] == -1.0
    assert decoded["speed_mps"] == 5.0
    assert decoded["heading_deg"] == 90.0


def test_decode_attitude_reports_unreported_axes_as_none():
    # A 0.0-degree default asserts a measured level attitude; an *omitted* key
    # is the other half of the same problem and is pinned separately below.
    assert decode_attitude({}) == {
        "roll_deg": None,
        "pitch_deg": None,
        "yaw_deg": None,
    }
    assert decode_attitude({"roll": 0.5}) == {
        "roll_deg": math.degrees(0.5),
        "pitch_deg": None,
        "yaw_deg": None,
    }

    full = decode_attitude({"roll": 0.0, "pitch": 0.1, "yaw": 3.0})
    assert full["roll_deg"] == 0.0
    assert full["yaw_deg"] == math.degrees(3.0) % 360


def test_decode_gps_raw_int_omits_unreported_fix_quality():
    assert decode_gps_raw_int({}) == {}
    assert decode_gps_raw_int({"fix_type": 3}) == {"gps_fix_type": 3}
    assert decode_gps_raw_int({"fix_type": 0, "satellites_visible": 0}) == {
        "gps_fix_type": 0,
        "satellites_visible": 0,
    }


def test_decode_gps_raw_int_drops_satellites_unknown_sentinel():
    # The fourth member of the same "not sent" sentinel family as
    # GLOBAL_POSITION_INT.hdg = 65535 and the two SYS_STATUS sentinels.
    # MAVLink common.xml: GPS_RAW_INT.satellites_visible is uint8, "if
    # unknown, set to UINT8_MAX". 255 is not a 255-satellite measurement -
    # which would read downstream as the best fix quality ever observed.
    assert decode_gps_raw_int({"fix_type": 3, "satellites_visible": 255}) == {
        "gps_fix_type": 3
    }
    # A real count, including a genuinely measured 0, still decodes.
    assert decode_gps_raw_int({"fix_type": 3, "satellites_visible": 12}) == {
        "gps_fix_type": 3,
        "satellites_visible": 12,
    }


def test_mavlink_satellites_unknown_sentinel_never_becomes_quality():
    # Both sides of the boundary, the same way the battery sentinels are
    # guarded in the decoder and again in the translator: a state dict can be
    # assembled by any MAVLink bridge, so a decoder-only guard is half a guard.
    event = _state_event(satellites_visible=255)
    assert "satellites_visible" not in event["payload"]["quality"]
    VALIDATOR.validate(event)

    # End-to-end through the documented decode -> translate pipeline.
    state = decode_global_position_int(
        {"lat": 340000000, "lon": -1180000000, "alt": 120000, "hdg": 65535}
    )
    state.update(decode_gps_raw_int({"fix_type": 3, "satellites_visible": 255}))
    state["based_on"] = [_PARENT_EVENT_ID]
    state["loop_status"] = "CHECKED_NOT_REFLECTION"
    piped = translate_platform_state(
        state, platform_id="uav-1", ts=_INPUT_TS
    )
    assert "satellites_visible" not in piped["payload"]["quality"]
    # The omission must not clean the event up elsewhere: the reported 3D fix
    # still carries its own quality and confidence.
    assert piped["payload"]["quality"]["gps_fix_type"] == 3
    VALIDATOR.validate(piped)


def test_decode_sys_status_omits_absent_and_sentinel_battery_values():
    # MAVLink SYS_STATUS documents voltage_battery = UINT16_MAX and
    # battery_remaining = -1 as "not sent by autopilot". Neither may become a
    # measurement: not a 0 V flat battery, and not a 65.535 V reading.
    assert decode_sys_status({}) == {}
    assert decode_sys_status({"voltage_battery": 65535, "battery_remaining": -1}) == {}
    assert decode_sys_status({"voltage_battery": 12600, "battery_remaining": 75}) == {
        "battery_voltage": 12.6,
        "battery_remaining_pct": 75,
    }


def test_mavlink_link_status_refuses_to_fabricate_link_health():
    # latency_ms / packet_loss_pct / throughput_bps were hard-coded 0 / 0.0 / 0
    # on every LINK_STATUS this template ever emitted: a perfect, fully
    # measured link reported by a node that measured nothing.
    with pytest.raises(ValueError, match="never fabricated"):
        translate_link_status(platform_id="uav-1", ts="2025-01-17T15:20:00+00:00")
    with pytest.raises(ValueError, match="never fabricated"):
        translate_link_status(
            platform_id="uav-1", latency_ms=42.0, packet_loss_pct=1.5
        )


def test_mavlink_link_status_omits_unreported_optional_metrics():
    link = translate_link_status(
        platform_id="uav-1", ts="2025-01-17T15:20:00+00:00", **_LINK_METRICS
    )
    metrics = link["payload"]["metrics"]

    assert "battery_voltage" not in metrics
    assert "battery_remaining_pct" not in metrics
    assert "rc_rssi" not in metrics
    assert metrics["latency_ms"] == 42.0
    assert metrics["packet_loss_pct"] == 1.5
    assert metrics["throughput_bps"] == 250000
    VALIDATOR.validate(link)


def test_mavlink_link_status_carries_reported_optional_metrics():
    link = translate_link_status(
        platform_id="uav-1",
        ts="2025-01-17T15:20:00+00:00",
        battery_voltage=12.6,
        battery_pct=75,
        rc_rssi=-70,
        **_LINK_METRICS,
    )
    metrics = link["payload"]["metrics"]

    assert metrics["battery_voltage"] == 12.6
    assert metrics["battery_remaining_pct"] == 75
    assert metrics["rc_rssi"] == -70
    VALIDATOR.validate(link)


def test_mavlink_link_status_drops_not_sent_battery_sentinel():
    link = translate_link_status(
        platform_id="uav-1",
        ts="2025-01-17T15:20:00+00:00",
        battery_pct=-1,
        **_LINK_METRICS,
    )

    assert "battery_remaining_pct" not in link["payload"]["metrics"]


# ---------------------------------------------------------------------------
# R1-11 A-06 residuals (b), (c): the fabricated *categorical* half of the same
# class. payload.state is the field a consumer reads first - "UP", "SYNCED",
# "RECEIVED" - and it was hard-coded or defaulted on three of the four
# emitters, below three metrics blocks that had just been made honest.
# ---------------------------------------------------------------------------


def test_mavlink_link_status_never_asserts_up_by_default():
    # The link-health verdict is not a by-product of measuring latency. A
    # caller honestly reporting 92 % loss and 5 s latency must not emit an
    # event whose first field says the link is UP.
    link = translate_link_status(
        platform_id="uas-1",
        latency_ms=5000.0,
        packet_loss_pct=92.0,
        throughput_bps=0,
        ts=_INPUT_TS,
    )

    assert link["payload"]["state"] == "UNKNOWN"
    # Refusing the verdict must not cost the measurements: everything the
    # caller did measure still travels, so the consumer adjudicates.
    assert link["payload"]["metrics"]["packet_loss_pct"] == 92.0
    assert link["payload"]["metrics"]["latency_ms"] == 5000.0
    VALIDATOR.validate(link)


def test_mavlink_link_status_carries_caller_supplied_verdict():
    for state in ("UP", "UNKNOWN"):
        link = translate_link_status(
            platform_id="uas-1", state=state, ts=_INPUT_TS, **_LINK_METRICS
        )
        assert link["payload"]["state"] == state
        VALIDATOR.validate(link)

    degraded = translate_link_status(
        platform_id="uas-1",
        state="DEGRADED",
        reason_code="HIGH_PACKET_LOSS",
        ts=_INPUT_TS,
        **_LINK_METRICS,
    )
    assert degraded["payload"]["state"] == "DEGRADED"
    assert degraded["payload"]["metrics"]["reason_code"] == "HIGH_PACKET_LOSS"
    VALIDATOR.validate(degraded)


def test_mavlink_link_status_refuses_unusable_verdicts():
    # A state outside the v1.0 vocabulary, and a DEGRADED/DOWN with no
    # reason_code, are refused loudly rather than emitted schema-invalid.
    with pytest.raises(ValueError, match="never fabricated"):
        translate_link_status(platform_id="uas-1", state="GREEN", **_LINK_METRICS)
    for state in ("DEGRADED", "DOWN"):
        with pytest.raises(ValueError, match="reason_code"):
            translate_link_status(
                platform_id="uas-1", state=state, **_LINK_METRICS
            )


def test_mavlink_time_status_emitters_agree_on_identical_telemetry():
    # Same telemetry, two code paths, one verdict. The decoded-message path
    # defaulted payload.state to "SYNCED" one line above a metrics block that
    # said UNSYNCED, while the sibling called the same input DEGRADED.
    msg = {
        "msg_type": "SYSTEM_TIME",
        "time_usec": 1700000000000000,
        "est_error_ms": 3.5,
        "last_sync_ts": "2025-01-17T15:19:00Z",
    }
    decoded = mavlink_decoded_to_zmeta_system_events(
        msg, platform_id="uav-1", producer="mavlink-adapter", ts=_INPUT_TS
    )[0]
    sibling = translate_time_status(
        platform_id="uav-1",
        est_error_ms=3.5,
        last_sync_ts="2025-01-17T15:19:00Z",
        ts=_INPUT_TS,
    )

    assert decoded["payload"]["state"] == sibling["payload"]["state"] == "DEGRADED"
    # The event must not contradict itself: an UNSYNCED metrics block cannot
    # sit under a payload.state that asserts a locked clock.
    assert decoded["payload"]["metrics"]["sync_state"] == "UNSYNCED"
    assert decoded["payload"]["state"] != "SYNCED"
    VALIDATOR.validate(decoded)
    VALIDATOR.validate(sibling)


def test_mavlink_time_status_reported_lock_still_reads_up():
    # The conservative default must not cost the honest path.
    reported = mavlink_decoded_to_zmeta_system_events(
        {
            "msg_type": "SYSTEM_TIME",
            "time_source": "GPS_PPS",
            "sync_state": "LOCKED",
            "est_error_ms": 1,
            "last_sync_ts": "2025-01-17T15:19:59+00:00",
        },
        platform_id="uav-1",
        producer="mavlink-adapter",
        ts=_INPUT_TS,
    )[0]

    assert reported["payload"]["state"] == "UP"
    assert reported["payload"]["metrics"]["sync_state"] == "LOCKED"
    VALIDATOR.validate(reported)


def test_mavlink_time_status_never_launders_a_carried_degraded_verdict():
    # The derivation must not run the other way either: an upstream that has
    # already judged its clock degraded keeps that verdict, and an optimistic
    # carried label never overrides an UNSYNCED metrics block.
    carried_bad = mavlink_decoded_to_zmeta_system_events(
        {
            "msg_type": "SYSTEM_TIME",
            "state": "DOWN",
            "sync_state": "LOCKED",
            "est_error_ms": 1,
            "last_sync_ts": "2025-01-17T15:19:59+00:00",
        },
        platform_id="uav-1",
        producer="mavlink-adapter",
        ts=_INPUT_TS,
    )[0]
    assert carried_bad["payload"]["state"] == "DOWN"

    carried_clean = mavlink_decoded_to_zmeta_system_events(
        {
            "msg_type": "SYSTEM_TIME",
            "state": "SYNCED",
            "est_error_ms": 1,
            "last_sync_ts": "2025-01-17T15:19:59+00:00",
        },
        platform_id="uav-1",
        producer="mavlink-adapter",
        ts=_INPUT_TS,
    )[0]
    assert carried_clean["payload"]["metrics"]["sync_state"] == "UNSYNCED"
    assert carried_clean["payload"]["state"] == "DEGRADED"


def test_mavlink_task_ack_refuses_to_fabricate_an_acknowledgement():
    # The third member of the same categorical family: a MISSION_ACK dict
    # carrying no verdict was reported as "RECEIVED", and a commander reads
    # that as the vehicle having taken the task. The v1.0 TASK_ACK state enum
    # has no "unknown" member to degrade into, so this one refuses.
    with pytest.raises(ValueError, match="never fabricated"):
        mavlink_decoded_to_zmeta_system_events(
            {
                "msg_type": "MISSION_ACK",
                "task_id": "task-1",
                "original_event_id": "019c3ef3-98c4-7c99-8daf-3643ed0bc8ef",
            },
            platform_id="uav-1",
            producer="mavlink",
            ts=_INPUT_TS,
        )
    # An empty/None carried verdict is the same non-answer, not a "RECEIVED".
    with pytest.raises(ValueError, match="never fabricated"):
        mavlink_decoded_to_zmeta_system_events(
            {
                "msg_type": "MISSION_ACK",
                "task_id": "task-1",
                "original_event_id": "019c3ef3-98c4-7c99-8daf-3643ed0bc8ef",
                "ack": "",
            },
            platform_id="uav-1",
            producer="mavlink",
            ts=_INPUT_TS,
        )
    # A carried verdict still emits, from any of the three carrier keys.
    for key in ("state", "mission_state", "ack"):
        msg = {
            "msg_type": "MISSION_ACK",
            "task_id": "task-1",
            "original_event_id": "019c3ef3-98c4-7c99-8daf-3643ed0bc8ef",
            key: "ACCEPTED",
        }
        event = mavlink_decoded_to_zmeta_system_events(
            msg, platform_id="uav-1", producer="mavlink", ts=_INPUT_TS
        )[0]
        assert event["payload"]["state"] == "ACCEPTED"
        VALIDATOR.validate(event)


def test_mavlink_system_events_emit_no_undeclared_leaf_anywhere():
    # The same path-scoped, type-complete provenance sweep as on the state
    # translator, over the SYSTEM_EVENT emitters - the ones that carried the
    # fabricated categorical verdicts. A declaration here pins the value at
    # that path, so re-hardcoding "UP" or "SYNCED" is a failure, not a pass.
    link_kwargs = {
        "platform_id": "uav-1",
        "producer": "mavlink-adapter",
        "ts": _INPUT_TS,
        **_LINK_METRICS,
    }
    link = translate_link_status(**link_kwargs)
    assert _undeclared_leaves(
        link,
        link_kwargs,
        {
            **_envelope_declarations("SYSTEM_EVENT", "LINK_STATUS", "EDGE"),
            "$.payload.system_type": "LINK_STATUS",
            # No verdict was supplied, so none is asserted.
            "$.payload.state": "UNKNOWN",
            "$.payload.metrics.link_id": "edge-comms-uav-1",
            # The declared default for an unnamed interface.
            "$.payload.metrics.active_link": "unknown",
        },
    ) == []
    VALIDATOR.validate(link)

    time_kwargs = {
        "platform_id": "uav-1",
        "producer": "mavlink-adapter",
        "est_error_ms": 1.0,
        "last_sync_ts": "2025-01-17T15:19:59+00:00",
        "ts": _INPUT_TS,
    }
    time_status = translate_time_status(**time_kwargs)
    assert _undeclared_leaves(
        time_status,
        time_kwargs,
        {
            **_envelope_declarations("SYSTEM_EVENT", "TIME_STATUS", "EDGE"),
            "$.payload.system_type": "TIME_STATUS",
            # Derived from the UNSYNCED default below, never "UP"/"SYNCED".
            "$.payload.state": "DEGRADED",
            "$.payload.metrics.time_source": "UNKNOWN",
            "$.payload.metrics.sync_state": "UNSYNCED",
            "$.payload.metrics.last_sync_ts": "2025-01-17T15:19:59Z",
        },
    ) == []
    VALIDATOR.validate(time_status)

    ack_msg = {
        "msg_type": "MISSION_ACK",
        "task_id": "task-1",
        "original_event_id": "019c3ef3-98c4-7c99-8daf-3643ed0bc8ef",
        "state": "ACCEPTED",
    }
    ack_kwargs = {"platform_id": "uav-1", "producer": "mavlink", "ts": _INPUT_TS}
    ack = mavlink_decoded_to_zmeta_system_events(ack_msg, **ack_kwargs)[0]
    assert _undeclared_leaves(
        ack,
        {**ack_msg, **ack_kwargs},
        {
            **_envelope_declarations("SYSTEM_EVENT", "TASK_ACK", "EDGE"),
            "$.payload.system_type": "TASK_ACK",
        },
    ) == []
    VALIDATOR.validate(ack)

    decoded_time_msg = {
        "msg_type": "SYSTEM_TIME",
        "time_usec": 1700000000000000,
        "est_error_ms": 3.5,
        "last_sync_ts": "2025-01-17T15:19:00Z",
    }
    decoded_time = mavlink_decoded_to_zmeta_system_events(
        decoded_time_msg, **ack_kwargs
    )[0]
    assert _undeclared_leaves(
        decoded_time,
        {**decoded_time_msg, **ack_kwargs},
        {
            **_envelope_declarations("SYSTEM_EVENT", "TIME_STATUS", "EDGE"),
            "$.payload.system_type": "TIME_STATUS",
            "$.payload.state": "DEGRADED",
            "$.payload.metrics.time_source": "UNKNOWN",
            "$.payload.metrics.sync_state": "UNSYNCED",
        },
    ) == []
    VALIDATOR.validate(decoded_time)

    # The catch-all LINK_STATUS branch, swept for provenance and - since the
    # CR-05 fix - schema-validated like every other emitter in this file: the
    # link_id / latency_ms / packet_loss_pct / throughput_bps the v1.0 schema
    # requires are message-carried (and refused when absent; see the CR-05
    # pins below). What stays pinned here is that with no verdict supplied,
    # none is asserted.
    fallback_msg = {"msg_type": "RADIO_STATUS", "rssi": -70, **_LINK_METRICS}
    fallback = mavlink_decoded_to_zmeta_system_events(fallback_msg, **ack_kwargs)[0]
    assert _undeclared_leaves(
        fallback,
        {**fallback_msg, **ack_kwargs},
        {
            **_envelope_declarations("SYSTEM_EVENT", "LINK_STATUS", "EDGE"),
            "$.payload.system_type": "LINK_STATUS",
            "$.payload.state": "UNKNOWN",
            # The same declared default translate_link_status writes above:
            # an identifier the adapter assigns, not a measurement.
            "$.payload.metrics.link_id": "edge-comms-uav-1",
        },
    ) == []
    VALIDATOR.validate(fallback)


def test_mavlink_time_status_refuses_to_fabricate_timing_uncertainty():
    # est_error_ms = 0.0 asserts a perfectly accurate clock in the very field
    # consumers read to decide how far to trust the timeline, and defaulting
    # last_sync_ts to the event ts asserts a sync that just happened.
    with pytest.raises(ValueError, match="never fabricated"):
        translate_time_status(
            platform_id="uav-1",
            last_sync_ts="2025-01-17T15:19:59+00:00",
            ts="2025-01-17T15:20:00+00:00",
        )
    with pytest.raises(ValueError, match="never fabricated"):
        translate_time_status(
            platform_id="uav-1",
            est_error_ms=1.0,
            ts="2025-01-17T15:20:00+00:00",
        )

# ---------------------------------------------------------------------------
# R1-11 second-pass pins (B-04 / R2-01, R2-08, R2-09, R2-10, R2-20, R2-21,
# R1-23, R1-26). Each closes a defect that a *previous* fix introduced or left
# behind, so each is written to fail on the code as it stood before this pass -
# not merely to describe the code as it stands now.
#
# Deliberate construction note: every vocabulary below is written out as a
# literal here rather than imported from the module under test. A pin that
# asserted the module's tuple equals the module's tuple would be satisfied by
# any vocabulary at all, which is the shape of oracle this cycle already
# shipped once.
# ---------------------------------------------------------------------------


def _time_status_msg(**overrides):
    msg = {
        "msg_type": "SYSTEM_TIME",
        "est_error_ms": 1.0,
        "last_sync_ts": "2025-01-17T15:19:59+00:00",
    }
    msg.update(overrides)
    return msg


def _time_status_event(**overrides):
    return mavlink_decoded_to_zmeta_system_events(
        _time_status_msg(**overrides),
        platform_id="uav-1",
        producer="mavlink-adapter",
        ts=_INPUT_TS,
    )[0]


def test_mavlink_time_status_carried_verdict_is_a_vocabulary_not_a_whitelist():
    # B-04 / R2-01. The guard compared the carried label against the two
    # literals its author thought of ("UP", "SYNCED"), so every other
    # optimistic label - including this module's own sync vocabulary, and
    # including the targeted exemplar with one trailing space - was published
    # verbatim over an UNSYNCED metrics block.
    #
    # Normalisation happens before the comparison: these all render as "UP" in
    # an operator UI, so none of them may escape it.
    for carried in ("UP ", " UP", "up", " Up ", "SYNCED", "synced", "Synced "):
        event = _time_status_event(state=carried)
        assert event["payload"]["metrics"]["sync_state"] == "UNSYNCED"
        assert event["payload"]["state"] == "DEGRADED", carried
        VALIDATOR.validate(event)

    # An unrankable label is refused, not published and not silently replaced
    # by the derived verdict. Replacing it would launder in the other
    # direction: "FAULT" may be *more* degraded than the derivation, and
    # quietly emitting the derived verdict over it would clean up an upstream
    # that said something was wrong.
    for carried in ("LOCKED", "NOMINAL", "OK", "GOOD", "HEALTHY", "TRUE", "FAULT"):
        with pytest.raises(ValueError, match="cannot rank"):
            _time_status_event(state=carried)

    # A genuinely more-conservative carried verdict is still honoured, and the
    # honest clean path still reads UP - the refusal must not cost either.
    degraded = _time_status_event(state="DOWN", sync_state="LOCKED")
    assert degraded["payload"]["state"] == "DOWN"
    VALIDATOR.validate(degraded)
    locked = _time_status_event(state="UP", sync_state="LOCKED")
    assert locked["payload"]["state"] == "UP"
    VALIDATOR.validate(locked)


def test_mavlink_time_status_absent_verdict_is_not_an_unrankable_one():
    # The refusal above must stay proportionate: a message that simply says
    # nothing about clock health is not carrying a verdict this adapter cannot
    # interpret, and it still emits on the derived verdict.
    for absent in (None, "", "   "):
        event = _time_status_event(state=absent)
        assert event["payload"]["state"] == "DEGRADED"
        VALIDATOR.validate(event)
    assert _time_status_event()["payload"]["state"] == "DEGRADED"


def test_mavlink_time_status_non_string_verdict_is_refused_not_stringified():
    # R2-08. str(carried_state) turned three verdicts the gateway used to
    # refuse as SCHEMA_INVALID into clean, schema-valid payload.state values
    # reading '1' / 'True' / '3.5' over an UNSYNCED metrics block - an event a
    # consumer cannot interpret and nothing downstream will reject.
    for carried in (1, 0, True, False, 3.5, ["UP"], {"state": "UP"}):
        with pytest.raises(ValueError, match="cannot rank"):
            _time_status_event(state=carried)


def test_mavlink_task_ack_zero_is_a_carried_verdict_not_a_missing_one():
    # R2-10. `state or mission_state or ack` collapsed every falsy value to
    # None and the guard then reported "no verdict carried". Both MAVLink
    # acceptance codes are the integer 0, so the truthiness test destroyed
    # precisely the successful acknowledgements while REJECTED/FAILED kept
    # emitting - and told the operator something false about why.
    base = {
        "msg_type": "MISSION_ACK",
        "task_id": "task-1",
        "original_event_id": "019c3ef3-98c4-7c99-8daf-3643ed0bc8ef",
    }

    def _emit(**overrides):
        return mavlink_decoded_to_zmeta_system_events(
            {**base, **overrides}, platform_id="uav-1", producer="mavlink", ts=_INPUT_TS
        )

    # A carrier that is present says so, whatever it carries. The two failures
    # are distinguishable, and neither message is false: this one may not claim
    # the message carried no verdict.
    for key in ("ack", "mission_state", "state"):
        with pytest.raises(ValueError) as absent_claim:
            _emit(**{key: 0})
        message = str(absent_claim.value)
        assert "not one of the v1.0 TASK_ACK states" in message
        assert repr(key) in message and " 0," in message
        assert "requires a message-carried ack state" not in message

    # No carrier key at all is the genuinely missing verdict, and keeps the
    # original message.
    with pytest.raises(ValueError, match="requires a message-carried ack state"):
        _emit(mission_ack=True)

    # An unmappable non-zero code is refused at ingress rather than emitted as
    # a schema-invalid event for the gateway to reject.
    for carried in (1, 4, "GOOD", ""):
        with pytest.raises(ValueError, match="not one of the v1.0 TASK_ACK states"):
            _emit(ack=carried)

    # Every real verdict still emits, from any carrier, in any spelling.
    for state in (
        "RECEIVED",
        "ACCEPTED",
        "REJECTED",
        "EXECUTING",
        "COMPLETED",
        "FAILED",
        "CANCELLED",
        "EXPIRED",
        "DUPLICATE_IGNORED",
    ):
        for key in ("state", "mission_state", "ack"):
            event = _emit(**{key: state})[0]
            assert event["payload"]["state"] == state
    assert _emit(ack="accepted ")[0]["payload"]["state"] == "ACCEPTED"


def test_mavlink_uint8_max_rssi_sentinel_never_becomes_a_measurement():
    # R2-09. The sentinel family was declared enumerated and closed at
    # satellites_visible; RC_CHANNELS(_RAW).rssi and RADIO_STATUS.rssi carry
    # the identical uint8 "Values: [0-254], UINT8_MAX: invalid/unknown"
    # documentation and were emitted verbatim. 255 on a 0-254 scale reads
    # downstream as the strongest signal ever observed.
    sentinel = translate_link_status(
        platform_id="uav-1", ts=_INPUT_TS, rc_rssi=255, **_LINK_METRICS
    )
    assert "rc_rssi" not in sentinel["payload"]["metrics"]
    VALIDATOR.validate(sentinel)

    # The top of the real scale, and the dBm convention this template's own
    # tests use, both still travel: the guard drops the sentinel, not the
    # measurement next to it.
    for reported in (254, 0, -70):
        link = translate_link_status(
            platform_id="uav-1", ts=_INPUT_TS, rc_rssi=reported, **_LINK_METRICS
        )
        assert link["payload"]["metrics"]["rc_rssi"] == reported

    # The same sentinel on the decoded-message path. The link measurements
    # ride along because since the CR-05 fix the branch refuses to emit
    # without them (they are schema-required), and a refusal would hide this
    # pin's actual question.
    kwargs = {"platform_id": "uav-1", "producer": "mavlink", "ts": _INPUT_TS}
    dropped = mavlink_decoded_to_zmeta_system_events(
        {"msg_type": "RADIO_STATUS", "rssi": 255, **_LINK_METRICS}, **kwargs
    )[0]
    assert "rssi" not in dropped["payload"]["metrics"]
    VALIDATOR.validate(dropped)
    kept = mavlink_decoded_to_zmeta_system_events(
        {"msg_type": "RADIO_STATUS", "rssi": -70, **_LINK_METRICS}, **kwargs
    )[0]
    assert kept["payload"]["metrics"]["rssi"] == -70
    VALIDATOR.validate(kept)


def test_mavlink_battery_voltage_sentinel_dropped_by_every_emitter():
    # R2-21 + R1-23, as a class rather than as the named exemplar. The comment
    # justifying the repeated satellites guard claimed the battery sentinels
    # were "guarded on both sides"; the voltage was guarded in the decoder
    # only, and translate_link_status - which has no decoder in front of it at
    # all - published both 0 V and the 65.535 V UINT16_MAX "voltage not sent"
    # sentinel as measurements.
    #
    # 65535 mV is the sentinel in the units decode_sys_status sees; 65.535 V is
    # the same sentinel in the units a bridge that converts before handing over
    # produces, which is what the pre-fix template in this very module did.
    def _quality(volts):
        return _state_event(battery_voltage=volts)["payload"]["quality"]

    def _metrics(volts):
        return translate_link_status(
            platform_id="uav-1", ts=_INPUT_TS, battery_voltage=volts, **_LINK_METRICS
        )["payload"]["metrics"]

    for emitted in (_quality, _metrics):
        for refused in (65535 / 1000.0, 65.535, 0.0, -1.0):
            assert "battery_voltage" not in emitted(refused), (emitted, refused)
        # A real measurement, including one just either side of the sentinel,
        # is untouched: this drops one exact value, not a range.
        for reported in (12.6, 65.534, 65.536, 50.4):
            assert emitted(reported)["battery_voltage"] == reported
        # These guards compare, so they must not turn a caller's wrong-typed
        # value into a bare TypeError out of the adapter: before this pass the
        # link emitter took `is not None` and a string voltage travelled to a
        # loud gateway refusal. A crash is not a refusal.
        for wrong_typed in ("12.6", True, None):
            assert "battery_voltage" not in emitted(wrong_typed), wrong_typed
        # A non-finite is deliberately NOT swallowed here. The kernel's
        # value-honesty gate refuses it loudly and with a filterable reason
        # code; dropping it in the adapter would trade that signal for a
        # silent omission, which is the trade this whole pass exists to undo.
        assert math.isnan(emitted(float("nan"))["battery_voltage"])
    assert decode_sys_status({"voltage_battery": 65535}) == {}

    poisoned = _state_event(battery_voltage=float("nan"))
    ok, violations = validators.validate_semantics(
        poisoned, POLICY["semantics"], POLICY.get("violation_severities")
    )
    assert ok is False and violations, "the kernel gate must still see the NaN"


def test_mavlink_unknown_heading_sentinel_never_reaches_either_destination():
    # Enumerated from the code rather than from the register: the fifth member
    # of the same sentinel family. GLOBAL_POSITION_INT.hdg = UINT16_MAX
    # divided by 100 by a bridge is 655.35 deg. On the canonical path the
    # schema's 0-360 bound catches it; quality.mavlink_hdg_frame_unknown_deg
    # has no such bound, so it landed there schema-clean.
    # Wrong-typed headings take the same route, and take it without raising:
    # the guard compares, so a string heading must drop, not crash the adapter.
    for sentinel in (655.35, 720.0, -1.0, "090", True):
        uncertain = _state_event(heading_deg=sentinel)
        assert "mavlink_hdg_frame_unknown_deg" not in uncertain["payload"]["quality"]
        VALIDATOR.validate(uncertain)

        canonical = _state_event(heading_deg=sentinel, heading_frame="TRUE_NORTH")
        assert "heading_deg" not in canonical["payload"]
        assert "heading_source" not in canonical["payload"]["quality"]
        VALIDATOR.validate(canonical)

    # A non-finite heading is left for the kernel's value-honesty gate, which
    # refuses it loudly with a reason code. Swallowing it here would cost the
    # operator the signal as well as the value.
    nan_heading = _state_event(heading_deg=float("nan"))
    assert math.isnan(
        nan_heading["payload"]["quality"]["mavlink_hdg_frame_unknown_deg"]
    )
    ok, violations = validators.validate_semantics(
        nan_heading, POLICY["semantics"], POLICY.get("violation_severities")
    )
    assert ok is False and violations, "the kernel gate must still see the NaN"

    # A real heading, at both ends of the legal range, still travels.
    for reported in (0.0, 90.0, 359.9, 360.0):
        assert (
            _state_event(heading_deg=reported)["payload"]["quality"][
                "mavlink_hdg_frame_unknown_deg"
            ]
            == reported
        )


def test_mavlink_link_status_reason_code_is_a_vocabulary_and_must_agree():
    # R2-20. Only presence was enforced, on a path that became reachable only
    # when `state` stopped being hard-coded "UP" - so a DEGRADED could still be
    # emitted schema-invalid, and an UP could carry a cause of degradation.
    with pytest.raises(ValueError, match="reason_code must be one of"):
        translate_link_status(
            platform_id="uav-1",
            ts=_INPUT_TS,
            state="DEGRADED",
            reason_code="NOT_A_CODE",
            **_LINK_METRICS,
        )
    with pytest.raises(ValueError, match="cannot carry metrics.reason_code"):
        translate_link_status(
            platform_id="uav-1",
            ts=_INPUT_TS,
            state="UP",
            reason_code="JAMMED",
            **_LINK_METRICS,
        )

    # Every code in the v1.0 vocabulary is accepted under a degraded verdict,
    # and the schema agrees - so the mirrored tuple cannot silently drift into
    # refusing a code the kernel allows.
    for code in (
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
    ):
        link = translate_link_status(
            platform_id="uav-1",
            ts=_INPUT_TS,
            state="DOWN",
            reason_code=code,
            **_LINK_METRICS,
        )
        assert link["payload"]["metrics"]["reason_code"] == code
        VALIDATOR.validate(link)

    # UNKNOWN keeps carrying an observed cause: "I measured this and I am not
    # adjudicating link health" is an honest pair, and refusing it would cost
    # the operator a real observation.
    unknown = translate_link_status(
        platform_id="uav-1",
        ts=_INPUT_TS,
        state="UNKNOWN",
        reason_code="HIGH_LATENCY",
        **_LINK_METRICS,
    )
    assert unknown["payload"]["metrics"]["reason_code"] == "HIGH_LATENCY"
    VALIDATOR.validate(unknown)


def test_decode_attitude_unreported_axis_clobbers_rather_than_carrying_stale():
    # R1-26. decode_attitude omitted an unreported axis, and its docstring sold
    # that as a feature. In the README's documented accumulation pattern an
    # omitted key leaves the *previous* message's roll in the state dict, and
    # the translator then publishes it as a current reading with no per-field
    # staleness marker. Stale-presented-as-current is the same class as
    # fabricated-as-measured, and the sibling decoder already clobbers.
    state = {
        "lat": 34.0517,
        "lon": -118.2437,
        "alt_m": 412.5,
        "gps_fix_type": 3,
        "based_on": [_PARENT_EVENT_ID],
        "loop_status": "CHECKED_NOT_REFLECTION",
    }
    state.update(decode_attitude({"roll": 0.5, "pitch": 0.1, "yaw": 3.0}))
    first = translate_platform_state(state, platform_id="uav-1", ts=_INPUT_TS)
    assert first["payload"]["quality"]["roll_deg"] == math.degrees(0.5)

    # Ten seconds later, the same accumulating state dict, roll not reported.
    state.update(decode_attitude({"pitch": 0.1, "yaw": 3.0}))
    later = translate_platform_state(state, platform_id="uav-1", ts=_INPUT_TS)
    assert "roll_deg" not in later["payload"]["quality"]
    # Dropping the stale axis must not cost the axes that were reported.
    assert later["payload"]["quality"]["pitch_deg"] == math.degrees(0.1)
    VALIDATOR.validate(later)


# ---------------------------------------------------------------------------
# CR-05 / CR-06 pins (R1-11 cold re-read). Both defects had the same shape:
# the mirrored vocabulary imported a schema enum without the emission
# obligations attached to it, so a documented emitter path produced only
# gateway-refused events. Fail-closed, not laundering - but a whole advertised
# message family went dark, and the docstring's "never accepted uninterpreted"
# claim was false on the LINK_STATUS branch. Vocabularies and pairings are
# written out as literals here, per the construction note above.
# ---------------------------------------------------------------------------


def _task_ack_event(**overrides):
    msg = {
        "msg_type": "MISSION_ACK",
        "task_id": "task-1",
        "original_event_id": "019c3ef3-98c4-7c99-8daf-3643ed0bc8ef",
    }
    msg.update(overrides)
    return mavlink_decoded_to_zmeta_system_events(
        msg, platform_id="uav-1", producer="mavlink", ts=_INPUT_TS
    )[0]


def test_mavlink_task_ack_negative_verdicts_validate_with_restating_reason():
    # CR-06. The mirror imported the TASK_ACK state enum but not the
    # conditional obligation attached to it: the v1.0 schema requires
    # metrics.reason_code on the five negative verdicts, and the metrics
    # literal carried only task_id/original_event_id - so the negative acks a
    # commander most needs were 100% gateway-refused (the commander saw a
    # SCHEMA_VIOLATION diagnostic, never the REJECTED). Each negative verdict
    # now carries the code that restates the verdict itself - the same pairing
    # the SAPIENT ingress makes. A restatement, not a diagnosis: it adds no
    # cause the message did not carry.
    for verdict, restated in (
        ("REJECTED", "TASK_REJECTED"),
        ("FAILED", "TASK_FAILED"),
        ("CANCELLED", "TASK_CANCELLED"),
        ("EXPIRED", "TASK_EXPIRED"),
        ("DUPLICATE_IGNORED", "TASK_DUPLICATE"),
    ):
        event = _task_ack_event(ack=verdict)
        assert event["payload"]["state"] == verdict
        assert event["payload"]["metrics"]["reason_code"] == restated
        VALIDATOR.validate(event)

    # The four clean verdicts keep emitting without a reason_code: the schema
    # attaches no obligation there, and stamping a failure cause under a clean
    # verdict would be a fabricated diagnosis.
    for verdict in ("RECEIVED", "ACCEPTED", "EXECUTING", "COMPLETED"):
        event = _task_ack_event(ack=verdict)
        assert event["payload"]["state"] == verdict
        assert "reason_code" not in event["payload"]["metrics"]
        VALIDATOR.validate(event)


def test_mavlink_task_ack_carried_reason_code_is_never_silently_dropped():
    # CR-06, second half. A message-carried reason_code - including a legal
    # member of the schema's 12-value TASK_ACK vocabulary - was read by
    # nothing and silently dropped: the exact silent-drop the refusal paths in
    # this same branch were rebuilt to avoid (R2-10). A carried cause beats
    # the restating default, because it says more than the verdict does.
    carried = _task_ack_event(ack="REJECTED", reason_code="COMMAND_NOT_DECONFLICTED")
    assert carried["payload"]["metrics"]["reason_code"] == "COMMAND_NOT_DECONFLICTED"
    VALIDATOR.validate(carried)
    # Message-carried tokens are normalised (whitespace/case) before the
    # comparison, like every other verdict this function reads.
    assert (
        _task_ack_event(ack="FAILED", reason_code=" task_aborted ")["payload"][
            "metrics"
        ]["reason_code"]
        == "TASK_ABORTED"
    )

    # An out-of-vocabulary carried cause refuses at ingress - neither dropped
    # (silent) nor emitted (schema-invalid for the gateway to reject).
    with pytest.raises(ValueError, match="not one of the v1.0 TASK_ACK reason codes"):
        _task_ack_event(ack="REJECTED", reason_code="BECAUSE")
    # A failure cause under a clean verdict is the TASK_ACK spelling of "UP
    # cannot carry a cause of degradation": which half the message meant is
    # not adjudicable here, so neither half is silently corrected.
    with pytest.raises(ValueError, match="cannot carry metrics.reason_code"):
        _task_ack_event(ack="ACCEPTED", reason_code="TASK_REJECTED")


def _link_status_event(**overrides):
    msg = {"msg_type": "RADIO_STATUS", **_LINK_METRICS}
    msg.update(overrides)
    return mavlink_decoded_to_zmeta_system_events(
        msg, platform_id="uav-1", producer="mavlink", ts=_INPUT_TS
    )[0]


def test_mavlink_decoded_link_status_every_advertised_state_validates():
    # CR-05. The branch emitted only the optional rssi/snr/drop_rate keys -
    # never the link_id / latency_ms / packet_loss_pct / throughput_bps the
    # v1.0 schema requires on every LINK_STATUS, and with no metric keys at
    # all it omitted `metrics` entirely - so 100% of this documented emitter
    # path's output was refused at the gateway. The measurements are
    # message-carried (see the refusal pin below); what this pin holds is
    # that every advertised state now emits an event the schema accepts.
    for state, reason_code in (
        ("UP", None),
        ("DEGRADED", "LOW_RSSI"),
        ("DOWN", "LINK_LOSS"),
        ("UNKNOWN", None),
    ):
        overrides = {"state": state}
        if reason_code is not None:
            overrides["reason_code"] = reason_code
        event = _link_status_event(**overrides)
        assert event["payload"]["state"] == state
        assert event["payload"]["metrics"]["link_id"] == "edge-comms-uav-1"
        assert event["payload"]["metrics"]["latency_ms"] == 42.0
        assert event["payload"]["metrics"]["packet_loss_pct"] == 1.5
        assert event["payload"]["metrics"]["throughput_bps"] == 250000
        if reason_code is not None:
            assert event["payload"]["metrics"]["reason_code"] == reason_code
        VALIDATOR.validate(event)

    # An absent verdict stays the honest "UNKNOWN" - and now validates.
    absent = _link_status_event()
    assert absent["payload"]["state"] == "UNKNOWN"
    VALIDATOR.validate(absent)
    # The alternate carrier key, and the spelling rule: "up " renders as UP
    # in every operator UI, so it must not escape the comparison.
    alt_key = _link_status_event(link_state="up ")
    assert alt_key["payload"]["state"] == "UP"
    VALIDATOR.validate(alt_key)
    normalised = _link_status_event(state=" down ", reason_code="LINK_LOSS")
    assert normalised["payload"]["state"] == "DOWN"
    VALIDATOR.validate(normalised)
    # The optional carried metrics still travel next to the required ones,
    # and a message-carried link identity is kept, not overwritten.
    carried = _link_status_event(rssi=-70, snr=20, drop_rate=0.1, link_id="sik-1")
    assert carried["payload"]["metrics"]["rssi"] == -70
    assert carried["payload"]["metrics"]["snr"] == 20
    assert carried["payload"]["metrics"]["drop_rate"] == 0.1
    assert carried["payload"]["metrics"]["link_id"] == "sik-1"
    VALIDATOR.validate(carried)


def test_mavlink_decoded_link_status_refuses_rather_than_emits_invalid():
    # CR-05, second half. `state or link_state or "UNKNOWN"` forwarded any
    # truthy carried string verbatim - payload.state = 'HEALTHY' emitted, with
    # only the gateway's schema enum to catch it - making the docstring's
    # "never accepted uninterpreted" claim false on this branch. And the
    # branch fabricated nothing but also refused nothing: a message without
    # the schema-required measurements emitted schema-invalid instead of
    # refusing loudly at ingress like every sibling branch.
    for uninterpretable in ("HEALTHY", "OK", "NOMINAL", 1, True):
        with pytest.raises(ValueError, match="not one of the v1.0 LINK_STATUS states"):
            _link_status_event(state=uninterpretable)

    # The three schema-required measurements are message-carried, never
    # fabricated - the same refusal translate_link_status applies.
    for missing in ("latency_ms", "packet_loss_pct", "throughput_bps"):
        msg = {"msg_type": "RADIO_STATUS", "rssi": -70, **_LINK_METRICS}
        del msg[missing]
        with pytest.raises(ValueError, match="never fabricated"):
            mavlink_decoded_to_zmeta_system_events(
                msg, platform_id="uav-1", producer="mavlink", ts=_INPUT_TS
            )

    # reason_code follows the same rules as translate_link_status: required
    # under DEGRADED/DOWN, a declared vocabulary, contradictory under UP.
    with pytest.raises(ValueError, match="requires metrics.reason_code"):
        _link_status_event(state="DEGRADED")
    with pytest.raises(ValueError, match="reason_code must be one of"):
        _link_status_event(state="DOWN", reason_code="BROKEN")
    with pytest.raises(ValueError, match="cannot carry metrics.reason_code"):
        _link_status_event(state="UP", reason_code="JAMMED")
