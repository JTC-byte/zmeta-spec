import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from adapters.egress.sapient.ulid_util import is_ulid
from adapters.egress.sapient.zmeta_command_to_sapient_task import zmeta_command_to_sapient_task
from adapters.egress.sapient.zmeta_state_to_sapient_detection import (
    SAPIENT_EGRESS_LOSS_NOTES,
    zmeta_state_to_sapient_detection,
)

# --- real gateway pipeline, for the A1-02 declared-2D-geo tests below -------
# The interop finding this file's geo tests exist to close: every prior test
# here proved a shape against schema-only validate(), and the SAPIENT
# boundary defect (silently dropping a doctrine A1-02 declared 2-D
# STATE_EVENT) was schema-VALID the whole time, so a schema-only pin would
# reproduce the exact vacuous verification that hid it. `_assert_gateway_valid`
# below runs gateway/src/validators.py against policy/*.yaml -- the same
# checks tools/validate.py runs -- and only that full pipeline can say a
# fixture is real.
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adapters.ingress.ais.ais_to_zmeta import translate_message as _ais_translate_message  # noqa: E402
from adapters.projector.track.track_projector import TrackProjector  # noqa: E402

_VALIDATORS_PATH = ROOT / "gateway" / "src" / "validators.py"
_validators_spec = importlib.util.spec_from_file_location(
    "zmeta_gateway_validators_sapient_geo", _VALIDATORS_PATH
)
gateway_validators = importlib.util.module_from_spec(_validators_spec)
_validators_spec.loader.exec_module(gateway_validators)

_GATEWAY_SCHEMA = gateway_validators.load_schema(ROOT / "schema" / "zmeta-event.schema.json")
_GATEWAY_POLICY = gateway_validators.load_policy(ROOT / "policy")
_GATEWAY_SEVERITY = _GATEWAY_POLICY["violation_severities"]

NODE_ID = "0f2c8b4e-9f1d-4e6a-8a3b-1c5d7e9f0a2b"
DEST_ID = "7a1b3c5d-2e4f-4a6b-8c0d-9e1f3a5b7c9d"

# Canonical ULIDs (SAPIENT proto is_ulid discipline; Apex strictIdFormat).
TASK_ULID = "01ARZ3NDEKTSV4RRFFQ69G5FAV"
TRACK_ULID = "01BX5ZZKBKACTAV9WEVGEMMVRZ"
OBJECT_ULID = "01HQRS7M4VXW2YZDNEKTAVB3CF"

_CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def _ulid_ts_ms(ulid_value):
    # Decode the 48-bit timestamp component (first 10 base32 chars).
    value = 0
    for ch in ulid_value[:10]:
        value = (value << 5) | _CROCKFORD.index(ch)
    return value


def _command_event(task_type="GOTO", **payload_overrides):
    payload = {
        "task_id": TASK_ULID,
        "task_type": task_type,
        "valid_for_ms": 600000,
        "requires_deconfliction": True,
    }
    if task_type == "GOTO":
        payload["target_geo"] = {"lat": 34.0, "lon": -118.0}
    payload.update(payload_overrides)
    return {
        "event": {
            "event_type": "COMMAND_EVENT",
            "event_subtype": task_type,
            "ts": "2026-07-17T12:00:00Z",
        },
        "payload": payload,
    }


def _state_event(**payload_overrides):
    payload = {
        "track_id": TRACK_ULID,
        "geo": {"lat": 34.0, "lon": -118.0, "alt_m": 120.0},
        "class": "UAV",
        "valid_for_ms": 5000,
    }
    payload.update(payload_overrides)
    return {
        "event": {
            "event_type": "STATE_EVENT",
            "event_subtype": "TRACK_STATE",
            "ts": "2026-07-17T12:00:00Z",
        },
        "payload": payload,
        "confidence": 0.8,
    }


def _task(event, **kwargs):
    kwargs.setdefault("node_id", NODE_ID)
    kwargs.setdefault("destination_id", DEST_ID)
    return zmeta_command_to_sapient_task(event, **kwargs)


def _detection(event, **kwargs):
    kwargs.setdefault("node_id", NODE_ID)
    return zmeta_state_to_sapient_detection(event, **kwargs)


def _assert_gateway_valid(event, gateway_state, profile="H"):
    """Run `event` through the REAL gateway pipeline and fail loudly on any
    FAIL-severity violation, mirroring the exact check list tools/validate.py
    runs (schema, role, profile, timing, semantics, lineage, producer
    authority, routing). A warn-only violation is accepted the same way the
    reference gateway accepts one -- and still recorded, so a later event's
    lineage citation of this one resolves the way it would in a real gateway
    process.
    """
    checks = [
        gateway_validators.validate_schema(event, _GATEWAY_SCHEMA, _GATEWAY_SEVERITY),
        gateway_validators.validate_role(
            event,
            {"roles": _GATEWAY_POLICY["roles"], "deny": _GATEWAY_POLICY["deny"]},
            _GATEWAY_SEVERITY,
        ),
        gateway_validators.validate_profile(event, profile, _GATEWAY_POLICY["profiles"], _GATEWAY_SEVERITY),
        gateway_validators.validate_timing_quality(
            event,
            _GATEWAY_POLICY["semantics"],
            state=gateway_state,
            severity_map=_GATEWAY_SEVERITY,
            timing_freshness_policy=_GATEWAY_POLICY.get("timing_freshness", {}),
            profile=profile,
        ),
        gateway_validators.validate_semantics(event, _GATEWAY_POLICY["semantics"], _GATEWAY_SEVERITY),
        gateway_validators.validate_lineage(
            event,
            _GATEWAY_POLICY.get("lineage", {}),
            state=gateway_state,
            profile=profile,
            severity_map=_GATEWAY_SEVERITY,
        ),
        gateway_validators.validate_producer_authority(
            event, _GATEWAY_POLICY.get("producer_authority", {}), _GATEWAY_SEVERITY
        ),
        gateway_validators.validate_routing(event, _GATEWAY_POLICY["routing"], _GATEWAY_SEVERITY),
    ]
    fails = [
        violation
        for _ok, violations in checks
        for violation in violations
        if violation.get("severity") != "warn"
    ]
    assert fails == [], fails
    gateway_state.record(event)


def _ais_class_a_message(**overrides):
    msg = {
        "type": 1, "mmsi": 366123456, "lat": 33.7405, "lon": -118.2712,
        "speed": 12.4, "course": 271.3, "heading": 270, "status": 0,
        "accuracy": True, "second": 42, "signalpower": -31.2,
        "rxtime": "20260731120000", "shipname": "EVER GIVEN@@@@@@",
        "callsign": "H3RC@@@", "shiptype": 70,
    }
    msg.update(overrides)
    return msg


def _real_2d_state_event():
    """A gateway-valid, doctrine A1-02 declared 2-D STATE_EVENT, built the
    honest way: a decoded AIS position report through the real ingress
    adapter (`adapters/ingress/ais`) and the real track projector
    (`adapters/projector/track`), not a hand-rolled fixture. Every AIS
    vessel produces exactly this shape -- a real, exact horizontal fix with
    no geometric altitude to assert, ever -- which is the class of event the
    first independent SAPIENT interop run found this egress silently
    dropping.

    Returns the STATE_EVENT, already proven gateway-valid (via
    `_assert_gateway_valid`) alongside the FUSION_EVENT it cites as lineage
    parent.
    """
    observation = _ais_translate_message(
        _ais_class_a_message(), platform_id="ais-node-01", receiver_id="rtlsdr-01"
    )
    projector = TrackProjector(platform_id="ais-node-01", confidence=0.9)
    fusion_event, state_event = projector.observe(observation)

    gateway_state = gateway_validators.ValidationState()
    _assert_gateway_valid(fusion_event, gateway_state)
    _assert_gateway_valid(state_event, gateway_state)
    return state_event


# --- command egress: happy paths -------------------------------------------


def test_goto_maps_move_to():
    message = _task(_command_event())

    assert message["timestamp"] == "2026-07-17T12:00:00Z"
    assert message["node_id"] == NODE_ID
    assert message["destination_id"] == DEST_ID

    task = message["task"]
    assert task["task_id"] == TASK_ULID
    assert task["control"] == "CONTROL_START"
    assert task["task_end_time"] == "2026-07-17T12:10:00Z"

    locations = task["command"]["move_to"]["locations"]
    assert len(locations) == 1
    location = locations[0]
    assert location["x"] == -118.0
    assert location["y"] == 34.0
    assert location["coordinate_system"] == "LOCATION_COORDINATE_SYSTEM_LAT_LNG_DEG_M"
    assert location["datum"] == "LOCATION_DATUM_WGS84_E"
    assert set(location) == {"x", "y", "coordinate_system", "datum"}


def test_track_target_maps_follow():
    event = _command_event("TRACK_TARGET", target_track_id="trk-9")
    message = _task(event, track_to_object={"trk-9": OBJECT_ULID})

    command = message["task"]["command"]
    assert command == {"follow": {"follow_object_id": OBJECT_ULID}}


def test_change_sensor_mode_maps_mode_change():
    event = _command_event("CHANGE_SENSOR_MODE", sensor_id="cam-1", sensor_mode="IR_WIDE")
    message = _task(event)

    assert message["task"]["command"] == {"mode_change": "IR_WIDE"}


def test_priority_never_crosses():
    message = _task(_command_event(priority="HIGH"))

    assert "priority" not in json.dumps(message)


# --- command egress: refusals ----------------------------------------------


def test_non_command_event_refuses():
    assert _task({"event": {"event_type": "STATE_EVENT"}, "payload": {}}) is None


def test_undeconflicted_command_refuses():
    assert _task(_command_event(requires_deconfliction=False)) is None
    event = _command_event()
    del event["payload"]["requires_deconfliction"]
    assert _task(event) is None


@pytest.mark.parametrize(
    "task_type",
    ["ORBIT", "HOLD", "SEARCH_BOX", "LOITER", "SCAN_RF", "RETURN_TO_BASE", "LAND"],
)
def test_unmapped_task_types_refuse(task_type):
    event = _command_event(task_type, target_geo={"lat": 34.0, "lon": -118.0})
    assert _task(event) is None


def test_missing_required_command_fields_refuse():
    for field in ("task_id", "task_type", "valid_for_ms"):
        event = _command_event()
        del event["payload"][field]
        assert _task(event) is None


def test_non_ulid_task_id_refuses():
    # The idempotency key is minted by the SAPIENT-bridged command
    # producer; the adapter refuses rather than rewriting it.
    for bad_id in ("task-1", TASK_ULID[:-1], TASK_ULID + "0", "01ARZ3NDEKTSV4RRFFQ69G5FIL"):
        assert _task(_command_event(task_id=bad_id)) is None


def test_missing_ts_refuses():
    event = _command_event()
    del event["event"]["ts"]
    assert _task(event) is None


def test_missing_node_identity_refuses():
    assert _task(_command_event(), node_id=None) is None
    assert _task(_command_event(), destination_id=None) is None


def test_goto_without_target_geo_refuses():
    event = _command_event()
    del event["payload"]["target_geo"]
    assert _task(event) is None


def test_track_target_without_map_refuses():
    event = _command_event("TRACK_TARGET", target_track_id="trk-9")
    assert _task(event) is None
    assert _task(event, track_to_object={"other-track": "01HOTHEROBJECT000000000000"}) is None


def test_change_sensor_mode_without_mode_refuses():
    event = _command_event("CHANGE_SENSOR_MODE", sensor_id="cam-1")
    assert _task(event) is None


# --- command egress: altitude never crosses --------------------------------


def test_goto_altitude_in_target_geo_raises():
    event = _command_event(target_geo={"lat": 34.0, "lon": -118.0, "alt_m": 120.0})
    with pytest.raises(ValueError):
        _task(event)


def test_goto_altitude_adjacent_extension_keys_do_not_leak():
    # Keys chosen to dodge the canonical-altitude denylist: proof that the
    # guard is whitelist construction, not denylist stripping.
    event = _command_event(
        extensions={"alt_hint_m": 4567.0, "z": 8901.0, "flight_level": "FL045"}
    )
    message = _task(event)

    serialized = json.dumps(message)
    assert "alt_hint_m" not in serialized
    assert "4567" not in serialized
    assert '"z"' not in serialized
    assert "8901" not in serialized
    assert "flight_level" not in serialized
    assert "z" not in message["task"]["command"]["move_to"]["locations"][0]


# --- state egress: happy paths ---------------------------------------------


def test_state_maps_detection_report():
    message = _detection(_state_event())

    assert message["timestamp"] == "2026-07-17T12:00:00Z"
    assert message["node_id"] == NODE_ID

    detection = message["detection_report"]
    assert detection["object_id"] == TRACK_ULID
    assert is_ulid(detection["report_id"])

    location = detection["location"]
    assert location["x"] == -118.0
    assert location["y"] == 34.0
    assert location["z"] == 120.0
    assert location["coordinate_system"] == "LOCATION_COORDINATE_SYSTEM_LAT_LNG_DEG_M"
    assert location["datum"] == "LOCATION_DATUM_WGS84_E"

    assert detection["classification"] == [{"type": "UAV", "confidence": 0.8}]
    assert "object_info" not in detection


def test_state_without_class_omits_classification():
    event = _state_event()
    del event["payload"]["class"]
    detection = _detection(event)["detection_report"]

    assert "classification" not in detection


def test_state_velocity_from_heading_speed():
    event = _state_event(heading_deg=90.0, speed_mps=10.0)
    velocity = _detection(event)["detection_report"]["enu_velocity"]

    assert velocity["east_rate"] == pytest.approx(10.0)
    assert velocity["north_rate"] == pytest.approx(0.0, abs=1e-9)
    # No fabricated up-rate: ZMeta TrackStatePayload carries no climb rate.
    assert set(velocity) == {"east_rate", "north_rate"}


def test_state_velocity_needs_both_heading_and_speed():
    assert "enu_velocity" not in _detection(_state_event())["detection_report"]
    event = _state_event(speed_mps=10.0)
    assert "enu_velocity" not in _detection(event)["detection_report"]
    event = _state_event(heading_deg=45.0)
    assert "enu_velocity" not in _detection(event)["detection_report"]


# --- state egress: declared 2-D geo (doctrine A1-02) ------------------------
#
# The MAJOR defect the first independent SAPIENT interop run found: this
# adapter's geo gate was all-or-nothing (lat AND lon AND alt_m all finite),
# so a real, gateway-valid, doctrine A1-02 declared 2-D STATE_EVENT -- every
# AIS vessel, every barometric-only aircraft -- silently returned None. No
# counter, no log, no loss note: invisible to a SAPIENT consumer with
# nothing to filter on.
#
# The proto fact that decides the fix, read from the dstl DetectionReport
# proto in the SAPIENT harness clone
# (proto/sapient_msg/bsi_flex_335_v2_0/location.proto, BSI Flex 335 v2.0):
#
#   message Location {
#       optional double x = 1 [(field_options) = {is_mandatory: true}];
#       optional double y = 2 [(field_options) = {is_mandatory: true}];
#       optional double z = 3;
#       ...
#   }
#
# `x` (longitude) and `y` (latitude) are marked `is_mandatory: true`; `z`
# (altitude) carries no such marker anywhere in the message. SAPIENT's own
# wire format permits an x-y position with no z at all, so a declared 2-D
# STATE is an honest DetectionReport WITHOUT z, not an unrepresentable one --
# the same shape this adapter's own GOTO->move_to command projection already
# emits (`test_goto_maps_move_to` above: no `z` key, ever).


def test_declared_2d_state_from_real_ais_pipeline_must_export():
    """The headline pin: a real AIS vessel, ingested and projected through
    the real gateway-side components, must reach the SAPIENT boundary.

    `_real_2d_state_event` proves gateway-validity through the actual
    validator pipeline first (schema, role, profile, timing, semantics,
    lineage, producer authority, routing) -- exactly the pipeline a
    schema-only test never runs, and exactly the gap the interop finding
    named. Before the fix this asserts red: `message` is `None`.
    """
    state_event = _real_2d_state_event()
    track_id = state_event["payload"]["track_id"]
    geo = state_event["payload"]["geo"]
    assert geo["dimensionality"] == "2D"
    assert "alt_m" not in geo

    message = _detection(state_event, object_map={track_id: OBJECT_ULID})

    assert message is not None, (
        "a gateway-valid declared-2D STATE_EVENT must export a "
        "DetectionReport: SAPIENT z is optional (location.proto), never "
        "mandatory"
    )
    location = message["detection_report"]["location"]
    assert location["x"] == geo["lon"]
    assert location["y"] == geo["lat"]
    assert "z" not in location, (
        "no fabricated altitude: the event never claimed one, and the "
        "proto never requires one"
    )
    assert location["coordinate_system"] == "LOCATION_COORDINATE_SYSTEM_LAT_LNG_DEG_M"
    assert location["datum"] == "LOCATION_DATUM_WGS84_E"


def test_declared_2d_geo_exports_without_z_unit_level():
    # A lighter-weight companion to the real-pipeline pin above: the same
    # disposition, isolated from the AIS/projector machinery.
    event = _state_event(geo={"lat": 34.0, "lon": -118.0, "dimensionality": "2D"})
    message = _detection(event)

    assert message is not None
    location = message["detection_report"]["location"]
    assert location["x"] == -118.0
    assert location["y"] == 34.0
    assert "z" not in location
    assert location["coordinate_system"] == "LOCATION_COORDINATE_SYSTEM_LAT_LNG_DEG_M"
    assert location["datum"] == "LOCATION_DATUM_WGS84_E"


def test_2d_geo_carrying_an_altitude_is_a_contradiction_and_refuses():
    # A "2D" token paired with an alt_m is schema-incoherent upstream
    # (schema/zmeta-event-1.1.0.schema.json coherence arm 1): the geo makes
    # two claims that cannot both be true. The adapter refuses rather than
    # silently picking one to believe.
    event = _state_event(geo={"lat": 34.0, "lon": -118.0, "alt_m": 120.0, "dimensionality": "2D"})
    assert _detection(event) is None


def test_explicit_3d_dimensionality_still_requires_altitude():
    # Absent dimensionality means 3D (doctrine A1-02); an explicit "3D"
    # token is the same claim spelled out, so it needs alt_m exactly like
    # the absent-token case does -- never a reason to relax the gate.
    event = _state_event(geo={"lat": 34.0, "lon": -118.0, "dimensionality": "3D"})
    assert _detection(event) is None


def test_unknown_dimensionality_token_still_requires_altitude():
    # An unrecognised token ("2.5D") is schema-invalid upstream and should
    # never reach this adapter from a real gateway, but a direct embedder
    # call can hand one in regardless (same defense-in-depth reasoning as
    # every other refusal in this file). Only the literal "2D" token grants
    # the no-altitude disposition; anything else stays on the historical
    # all-or-nothing side of the gate.
    event = _state_event(geo={"lat": 34.0, "lon": -118.0, "dimensionality": "2.5D"})
    assert _detection(event) is None


def test_2d_geo_with_non_finite_lat_lon_still_refuses():
    # The finite-number gate on lat/lon applies identically whether or not
    # the geo is declared 2-D: a NaN/inf horizontal fix is not a real fix
    # of any dimensionality.
    for bad in (float("nan"), float("inf"), float("-inf")):
        event = _state_event(geo={"lat": bad, "lon": -118.0, "dimensionality": "2D"})
        assert _detection(event) is None
        event = _state_event(geo={"lat": 34.0, "lon": bad, "dimensionality": "2D"})
        assert _detection(event) is None


# --- state egress: refusals ------------------------------------------------


def test_non_state_event_refuses():
    assert _detection({"event": {"event_type": "OBSERVATION_EVENT"}, "payload": {}}) is None
    event = _state_event()
    event["event"]["event_subtype"] = "PLATFORM_STATE"
    assert _detection(event) is None


def test_state_missing_ts_refuses():
    event = _state_event()
    del event["event"]["ts"]
    assert _detection(event) is None


def test_state_missing_node_id_refuses():
    assert _detection(_state_event(), node_id=None) is None


def test_state_missing_track_id_refuses():
    event = _state_event()
    del event["payload"]["track_id"]
    assert _detection(event) is None


def test_state_partial_geo_refuses():
    # None of these carry an explicit "2D" dimensionality token, so this is
    # the historical ambiguous case doctrine A1-02 leaves refused: an
    # incomplete geo that never declares itself two-dimensional does not get
    # the no-altitude disposition by default (see the declared-2-D section
    # above for the case that does).
    for field in ("lat", "lon", "alt_m"):
        event = _state_event()
        del event["payload"]["geo"][field]
        assert _detection(event) is None
    event = _state_event()
    del event["payload"]["geo"]
    assert _detection(event) is None


def test_quarantined_event_refuses():
    event = _state_event(
        extensions={
            "risk_adjudication": [
                {"risk_dimension": "external_promotion", "policy_decision": "QUARANTINE_ACCEPT"}
            ]
        }
    )
    assert _detection(event) is None


def test_rejected_event_refuses():
    event = _state_event(
        extensions={"risk_adjudication": [{"policy_decision": "REJECTED"}]}
    )
    assert _detection(event) is None


def test_prohibited_export_use_refuses():
    event = _state_event(
        extensions={
            "risk_adjudication": [
                {"policy_decision": "WARN_ACCEPT", "prohibited_uses": ["COALITION_EXPORT"]}
            ]
        }
    )
    assert _detection(event) is None


def test_grant_list_omitting_export_refuses():
    event = _state_event(
        extensions={
            "risk_adjudication": [
                {"policy_decision": "WARN_ACCEPT", "allowed_uses": ["DISPLAY", "AAR_ONLY"]}
            ]
        }
    )
    assert _detection(event) is None


def test_caller_use_labels_prohibiting_export_refuse():
    assert _detection(_state_event(), use_labels={"prohibited_uses": ["COALITION_EXPORT"]}) is None
    assert _detection(_state_event(), use_labels={"allowed_uses": ["DISPLAY"]}) is None


def test_export_use_parameter_scopes_the_refusal():
    event = _state_event(
        extensions={
            "risk_adjudication": [
                {"policy_decision": "WARN_ACCEPT", "prohibited_uses": ["COALITION_EXPORT"]}
            ]
        }
    )
    # The same event exports on a path the labels do not prohibit, and the
    # warn adjudication still travels as a self-label.
    message = _detection(event, export_use="DISPLAY")
    assert message is not None
    info = message["detection_report"]["object_info"]
    assert info[0]["type"] == "zmeta.risk"


# --- state egress: id discipline --------------------------------------------


def test_report_id_is_ulid_stamped_with_event_time():
    report_id = _detection(_state_event())["detection_report"]["report_id"]

    assert is_ulid(report_id)
    event_ts_ms = int(datetime(2026, 7, 17, 12, 0, 0, tzinfo=timezone.utc).timestamp() * 1000)
    # The embedded 48-bit timestamp is the event's own ts, never the
    # translate-time wall clock.
    assert _ulid_ts_ms(report_id) == event_ts_ms


def test_report_ids_are_fresh_per_report():
    event = _state_event()
    first = _detection(event)["detection_report"]["report_id"]
    second = _detection(event)["detection_report"]["report_id"]

    assert first != second


def test_non_ulid_track_id_without_object_map_refuses():
    assert _detection(_state_event(track_id="trk-9")) is None


def test_object_map_resolves_non_ulid_track_id():
    message = _detection(_state_event(track_id="trk-9"), object_map={"trk-9": OBJECT_ULID})

    assert message["detection_report"]["object_id"] == OBJECT_ULID


def test_non_ulid_object_map_entry_refuses():
    # A mapped identity that is not itself a ULID is refused, never
    # passed through to the wire.
    assert _detection(_state_event(track_id="trk-9"), object_map={"trk-9": "obj-9"}) is None


def test_ulid_track_id_passes_through_unmapped():
    message = _detection(_state_event(), object_map={TRACK_ULID: OBJECT_ULID})

    # A track_id that is already a ULID is caller-owned identity; the
    # map is not consulted and the id crosses unchanged.
    assert message["detection_report"]["object_id"] == TRACK_ULID


# --- state egress: self-labels ---------------------------------------------


def test_warn_risk_attaches_self_label():
    record = {
        "risk_dimension": "timing",
        "reason_code": "TIMING_STALE",
        "policy_decision": "WARN_ACCEPT",
        "prohibited_uses": ["COMMAND_BASIS"],
    }
    event = _state_event(extensions={"risk_adjudication": [record]})
    detection = _detection(event)["detection_report"]

    info = detection["object_info"]
    assert len(info) == 1
    assert info[0]["type"] == "zmeta.risk"
    labels = json.loads(info[0]["value"])
    assert labels == [
        {
            "risk_dimension": "timing",
            "reason_code": "TIMING_STALE",
            "policy_decision": "WARN_ACCEPT",
            "prohibited_uses": ["COMMAND_BASIS"],
        }
    ]


def test_caller_use_labels_travel_in_self_label():
    message = _detection(
        _state_event(),
        use_labels={"allowed_uses": ["COALITION_EXPORT", "DISPLAY"]},
    )
    info = message["detection_report"]["object_info"]
    labels = json.loads(info[0]["value"])
    assert labels == [{"allowed_uses": ["COALITION_EXPORT", "DISPLAY"]}]


def test_degraded_timing_attaches_self_label():
    timing = {
        "time_source": "NTP",
        "sync_state": "HOLDOVER",
        "est_error_ms": 250,
        "last_sync_ts": "2026-07-17T11:00:00Z",
    }
    event = _state_event(timing_quality=timing)
    info = _detection(event)["detection_report"]["object_info"]

    assert len(info) == 1
    assert info[0]["type"] == "zmeta.timing_quality"
    assert json.loads(info[0]["value"]) == timing


def test_locked_timing_attaches_no_self_label():
    timing = {
        "time_source": "GPS_PPS",
        "sync_state": "LOCKED",
        "est_error_ms": 1,
        "last_sync_ts": "2026-07-17T11:59:00Z",
    }
    event = _state_event(timing_quality=timing)
    assert "object_info" not in _detection(event)["detection_report"]


# --- loss documentation -----------------------------------------------------


def test_loss_notes_cover_dropped_concerns():
    for concern in ("lineage", "timing_quality", "risk_adjudication", "valid_for_ms"):
        assert concern in SAPIENT_EGRESS_LOSS_NOTES
        assert SAPIENT_EGRESS_LOSS_NOTES[concern]


# --- fail-closed decision vocabulary (R1-11 R11-02) --------------------------
# tools/filter_risk.py maps unknown/local/missing decisions to max rank
# (REJECTED) and blocks them; the coalition egress must never be more
# permissive than the operator's own filter on the identical record.


@pytest.mark.parametrize(
    "decision", ["SITE_QUARANTINE", "LOCAL_HOLD", "quarantine_accept_v2", ""]
)
def test_unknown_or_local_policy_decision_refuses(decision):
    event = _state_event(
        extensions={"risk_adjudication": [{"policy_decision": decision}]}
    )
    assert _detection(event) is None


def test_risk_record_without_decision_refuses():
    event = _state_event(
        extensions={"risk_adjudication": [{"risk_dimension": "external_promotion"}]}
    )
    assert _detection(event) is None


def test_ignored_decision_without_restrictions_exports_clean():
    # IGNORED ranks 0 in filter_risk: parity means it exports, and with no
    # use restrictions there is nothing to self-label.
    event = _state_event(
        extensions={"risk_adjudication": [{"policy_decision": "IGNORED"}]}
    )
    detection = _detection(event)["detection_report"]
    assert "object_info" not in detection


def test_ignored_decision_with_restrictions_keeps_the_label():
    event = _state_event(
        extensions={
            "risk_adjudication": [
                {"policy_decision": "IGNORED", "prohibited_uses": ["COMMAND_BASIS"]}
            ]
        }
    )
    detection = _detection(event)["detection_report"]
    labels = json.loads(
        next(
            info["value"]
            for info in detection["object_info"]
            if info["type"] == "zmeta.risk"
        )
    )
    assert labels[0]["prohibited_uses"] == ["COMMAND_BASIS"]


# --- documented None-refusal on malformed fields (R1-11 R11-20/R11-04) ------


def test_state_malformed_ts_refuses_not_raises():
    event = _state_event()
    event["event"]["ts"] = "not-a-time"
    assert _detection(event) is None


def test_non_string_ts_refuses_not_raises():
    # R11-20 completion (R1-11 verification pass 2): a non-string ts hit
    # .endswith and escaped as AttributeError past the (ValueError,
    # TypeError) guard, instead of taking the documented None refusal.
    for bad_ts in (1752969600000, None, {"seconds": 1752969600}):
        state = _state_event()
        state["event"]["ts"] = bad_ts
        assert _detection(state) is None
        command = _command_event()
        command["event"]["ts"] = bad_ts
        assert _task(command) is None


def test_state_non_numeric_heading_refuses_not_raises():
    event = _state_event(heading_deg="90", speed_mps=12.0)
    assert _detection(event) is None


def test_state_non_finite_values_refuse():
    assert _detection(_state_event(heading_deg=float("nan"), speed_mps=12.0)) is None
    nan_geo = _state_event(geo={"lat": float("nan"), "lon": -118.0, "alt_m": 120.0})
    assert _detection(nan_geo) is None
    nan_confidence = _state_event()
    nan_confidence["confidence"] = float("nan")
    assert _detection(nan_confidence) is None


def test_command_malformed_ts_refuses_not_raises():
    event = _command_event()
    event["event"]["ts"] = "not-a-time"
    assert _task(event) is None


def test_command_non_integer_valid_for_ms_refuses_not_raises():
    assert _task(_command_event(valid_for_ms="soon")) is None


def test_command_non_finite_target_refuses():
    event = _command_event(target_geo={"lat": float("inf"), "lon": -118.0})
    assert _task(event) is None


# --- R1-11 A-10: the ts guard must cover the mint, not just the parse -------
# The refusal guard wrapped only _parse_utc; ulid_from_ts_ms on the very next
# statement raises ValueError for any negative epoch-ms, so a schema-valid
# pre-1970 event.ts raised out of the public entry point past the None
# contract this module and its README both document.


@pytest.mark.parametrize(
    "bad_ts",
    [
        "1969-12-31T23:59:59.500Z",  # half a second before the epoch
        "1969-07-20T20:17:00Z",
        "1900-01-01T00:00:00Z",
        "1970-01-01T00:00:00+01:00",  # positive offset lands pre-epoch in UTC
    ],
)
def test_pre_epoch_ts_refuses_not_raises(bad_ts):
    # Pre-epoch timestamps are the canonical bad-clock symptom on an
    # unsynced edge node — precisely the degraded-timing events whose
    # export honesty this adapter exists to preserve.
    state = _state_event()
    state["event"]["ts"] = bad_ts
    assert _detection(state) is None


@pytest.mark.parametrize(
    "naive_ts",
    [
        "1969-12-31T23:59:59.500",  # no zone designator
        "1900-01-01T00:00:00",
        "0001-01-01T00:00:00",
    ],
)
def test_naive_pre_epoch_ts_refuses_in_both_projections(naive_ts):
    # Second member of the same class, found while pinning the first and
    # NOT covered by the original (ValueError, TypeError) guard in either
    # file: _parse_utc calls .astimezone(), which delegates to the
    # platform for a naive datetime and raises OSError(EINVAL) on Windows
    # for a pre-1970 instant. Portable assertion — on a platform where
    # astimezone succeeds the value is still pre-epoch and refuses at the
    # ULID mint (state) or projects an honest pre-epoch task (command),
    # so only the state adapter's disposition is asserted as None here.
    state = _state_event()
    state["event"]["ts"] = naive_ts
    assert _detection(state) is None

    command = _command_event()
    command["event"]["ts"] = naive_ts
    # The command projection mints no ULID, so its only requirement is
    # that it does not raise: None or a message, never a traceback.
    result = _task(command)
    assert result is None or result["timestamp"]


@pytest.mark.parametrize(
    "good_ts",
    [
        "1970-01-01T00:00:00Z",  # the exact boundary still projects
        "1970-01-01T00:00:00.001Z",
        "9999-12-31T23:59:59Z",  # 2**48 ms runs to year 10889: no upper clip
    ],
)
def test_representable_ts_still_projects(good_ts):
    # Non-vacuity for the guard above: it must refuse the unrepresentable
    # instants only, not blunt-refuse every unusual one.
    state = _state_event()
    state["event"]["ts"] = good_ts
    message = _detection(state)
    assert message is not None
    assert is_ulid(message["detection_report"]["report_id"])


# --- R1-11 A-11: no non-finite inside an honesty self-label -----------------
# The self-labels ride as JSON *inside* a JSON string, so an outer
# json.dumps(message, allow_nan=False) cannot see a bare NaN/Infinity token
# in them (RFC 8259 s6 has no such literals). zmeta.timing_quality is
# attached only when sync_state != LOCKED — it exists solely on the events
# whose degradation it reports — so a label a strict consumer drops or
# rejects launders the detection clean (contract 3.3, design gates 3/4).


def _strict_reparse(value):
    """json.loads that refuses NaN/Infinity/-Infinity, unlike the default."""

    def _reject(constant):
        raise AssertionError(f"non-JSON constant {constant!r} inside a self-label")

    return json.loads(value, parse_constant=_reject)


# (label carrier, poisoned event kwargs, clean event kwargs, label type)
_SELF_LABEL_CARRIERS = [
    (
        "timing_quality.est_error_ms",
        {"timing_quality": {"sync_state": "HOLDOVER", "est_error_ms": float("nan")}},
        {"timing_quality": {"sync_state": "HOLDOVER", "est_error_ms": 250}},
        "zmeta.timing_quality",
    ),
    (
        "timing_quality.est_error_ms inf",
        {"timing_quality": {"sync_state": "UNSYNCED", "est_error_ms": float("inf")}},
        {"timing_quality": {"sync_state": "UNSYNCED", "est_error_ms": 60000}},
        "zmeta.timing_quality",
    ),
    (
        "risk.reason_code",
        {
            "extensions": {
                "risk_adjudication": [
                    {"policy_decision": "WARN_ACCEPT", "reason_code": float("nan")}
                ]
            }
        },
        {
            "extensions": {
                "risk_adjudication": [
                    {"policy_decision": "WARN_ACCEPT", "reason_code": "STALE_SOURCE"}
                ]
            }
        },
        "zmeta.risk",
    ),
    (
        "risk.policy_ref",
        {
            "extensions": {
                "risk_adjudication": [
                    {"policy_decision": "DEGRADED_ACCEPT", "policy_ref": float("-inf")}
                ]
            }
        },
        {
            "extensions": {
                "risk_adjudication": [
                    {"policy_decision": "DEGRADED_ACCEPT", "policy_ref": "pol-7"}
                ]
            }
        },
        "zmeta.risk",
    ),
]


@pytest.mark.parametrize(
    "carrier,poisoned,clean,label_type",
    _SELF_LABEL_CARRIERS,
    ids=[case[0] for case in _SELF_LABEL_CARRIERS],
)
def test_non_finite_in_a_self_label_refuses_never_launders(
    carrier, poisoned, clean, label_type
):
    # The clean arm is what makes this non-vacuous: the ONLY difference
    # between the two events is the non-finite value, so a blanket refusal
    # (or a refusal for some unrelated reason) fails the test.
    message = _detection(_state_event(**clean))
    assert message is not None, f"{carrier}: clean control must still export"
    labels = message["detection_report"]["object_info"]
    assert [info["type"] for info in labels] == [label_type]
    _strict_reparse(labels[0]["value"])

    assert _detection(_state_event(**poisoned)) is None, (
        f"{carrier}: a non-finite value must refuse the export, never ride "
        f"inside the {label_type} label string"
    )


def test_caller_use_labels_non_finite_refuses():
    # use_labels enters from the caller, not the event, so it bypasses every
    # event-side validator: the adapter is the only gate on this path.
    clean = _detection(
        _state_event(), use_labels={"allowed_uses": ["COALITION_EXPORT"]}
    )
    assert clean is not None
    assert (
        _detection(
            _state_event(),
            use_labels={
                "allowed_uses": ["COALITION_EXPORT"],
                "reason_code": float("nan"),
            },
        )
        is None
    )


def test_unserializable_self_label_refuses_not_raises():
    # Same sink, non-float arm: a value with no JSON form, and mixed key
    # types sort_keys cannot order. Both raise out of json.dumps and must
    # take the None contract, not escape the projection.
    assert _detection(_state_event(timing_quality={"sync_state": "HOLDOVER", 1: "x"})) is None
    assert (
        _detection(_state_event(timing_quality={"sync_state": "HOLDOVER", "x": {"y"}}))
        is None
    )


def test_no_self_label_serializer_permits_non_json_constants():
    # Source-level oracle, deliberately sharing no runtime machinery with
    # the behavioural pins above: every json.dumps in this egress package
    # must pass allow_nan=False. Catches a future self-label carrier added
    # without the guard — the failure mode the behavioural pins cannot see
    # because they only know today's carriers.
    import ast
    import pathlib

    package = pathlib.Path(__file__).resolve().parent
    checked = 0
    for source_path in sorted(package.glob("*.py")):
        if source_path.name.startswith("test_"):
            continue
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if not (isinstance(func, ast.Attribute) and func.attr == "dumps"):
                continue
            checked += 1
            allow_nan = [kw for kw in node.keywords if kw.arg == "allow_nan"]
            assert allow_nan, (
                f"{source_path.name}:{node.lineno} json.dumps without "
                f"allow_nan=False can emit bare NaN/Infinity inside a label"
            )
            assert allow_nan[0].value.value is False, (
                f"{source_path.name}:{node.lineno} allow_nan must be False"
            )
    # Non-vacuity floor: the package serializes its self-labels through a
    # single helper today, so one site is the true count. A rename or a
    # deleted module drops this to zero and the assert fires.
    assert checked >= 1, "no json.dumps found — the scan is looking at nothing"


# --- R1-11 A-10 family: no numeric guard may raise on a huge int ------------
# math.isfinite RAISES OverflowError on a Python int outside float64 range,
# and json.loads builds exactly such an int from a plain integer literal.
# Same class as the ingress guard (sapient_to_zmeta._is_number).


@pytest.mark.parametrize("huge", [10**400, -(10**400)])
def test_unrepresentable_int_refuses_not_raises(huge):
    assert _detection(_state_event(geo={"lat": huge, "lon": -118.0, "alt_m": 120.0})) is None
    assert _detection(_state_event(heading_deg=huge, speed_mps=12.0)) is None
    confidence_event = _state_event()
    confidence_event["confidence"] = huge
    assert _detection(confidence_event) is None
    assert _task(_command_event(target_geo={"lat": huge, "lon": -118.0})) is None


# --- R1-11 CR-09: an unadjudicable use_labels fails CLOSED -------------------
# The adapter treated any non-dict use_labels as NO restriction: a caller
# export prohibition passed as a LIST (the natural mistake — event-carried
# risk_adjudication records are a list) was dropped and the detection
# exported to the coalition feed clean; no refusal, no self-label. That was
# the fail-open polarity on the one parameter whose whole purpose is
# restricting the export path, in a function every other arm of which fails
# closed (unknown decisions, unserializable labels, partial geo).


def test_list_shaped_use_labels_prohibition_refuses_never_drops():
    # Controls first, for non-vacuity: no use_labels exports, and the
    # identical prohibition in the documented dict shape refuses — so the
    # list arm below can only pass by adjudicating the SHAPE, not via a
    # blanket refusal or some unrelated defect in the event.
    assert _detection(_state_event()) is not None
    prohibition = {"prohibited_uses": ["COALITION_EXPORT"]}
    assert _detection(_state_event(), use_labels=prohibition) is None
    assert _detection(_state_event(), use_labels=[prohibition]) is None


@pytest.mark.parametrize(
    "malformed",
    [
        [{"prohibited_uses": ["COALITION_EXPORT"]}],  # list of label dicts
        [{"allowed_uses": ["DISPLAY"]}],  # grant list omitting the export use
        ({"prohibited_uses": ["COALITION_EXPORT"]},),  # tuple wrapper
        '{"prohibited_uses": ["COALITION_EXPORT"]}',  # JSON-encoded, not decoded
        "COALITION_EXPORT",  # bare string
        [],  # empty list: shape gate, not content gate — intent unknowable
    ],
)
def test_undocumented_use_labels_shape_refuses(malformed):
    # Fail closed on shape, not content: the adapter cannot know whether a
    # non-dict was a restriction, so it must never adjudicate one as no
    # restriction. Refusing is recoverable; a dropped prohibition is not.
    assert _detection(_state_event(), use_labels=malformed) is None


# --- R1-11 CR-10: altitude tripwire crash/blindness past the contract -------
# The recursive dict/list-only _contains_altitude raised RecursionError on
# deep target_geo — a third exception class where the documented contract is
# ValueError/None only — and never looked inside a Mapping that is not a
# dict, a tuple, a set or a CBOR tag wrapper: the identical guard-shape
# defect the MAVLink sibling fixed in this same held range (R2-07 family).


class _CborTag:
    """Stand-in for cbor2.CBORTag: an unrecognised tag decodes to an object
    whose `.value` still reaches the consumer."""

    def __init__(self, tag, value):
        self.tag = tag
        self.value = value


def _nested_geo(leaf, depth=2000):
    node = leaf
    for _ in range(depth):
        node = {"n": node}
    return {"lat": 34.0, "lon": -118.0, "meta": node}


def test_deep_target_geo_takes_the_documented_contract_not_recursionerror():
    # Clean deep nesting projects: no altitude key anywhere, and Location is
    # built field-by-field from lat/lon so none of the nest leaks (2000 deep
    # is past the default interpreter recursion limit of 1000).
    message = _task(_command_event(target_geo=_nested_geo({"note": "x"})))
    assert message is not None
    location = message["task"]["command"]["move_to"]["locations"][0]
    assert set(location) == {"x", "y", "coordinate_system", "datum"}
    # An altitude key at the BOTTOM of the same nest still trips the one
    # deliberate raise — never a stack crash before the guard finds it.
    with pytest.raises(ValueError, match="target_geo must be 2D"):
        _task(_command_event(target_geo=_nested_geo({"alt_m": 120.0})))


def test_altitude_in_a_non_dict_container_still_raises():
    # Contract 7.8 is a fielded-safety rule: no vertical intent may cross.
    # An altitude key one container off dict/list must trip the same
    # ValueError, not project silently past the tripwire.
    from collections import OrderedDict
    from types import MappingProxyType

    for meta in (
        ({"alt_m": 500},),  # tuple-wrapped dict (the CR-10 live probe)
        MappingProxyType({"agl_m": 50.0}),  # a Mapping that is not a dict
        [[{" ALT_M ": 100.0}]],  # case/whitespace padding still normalized
        _CborTag(4242, {"target_alt_m": 1.0}),  # tag wrapper's .value
        OrderedDict({"altitude": 100.0}),  # concrete-dict subclass dispatch
    ):
        event = _command_event(target_geo={"lat": 34.0, "lon": -118.0, "meta": meta})
        with pytest.raises(ValueError, match="target_geo must be 2D"):
            _task(event)


def test_altitude_walk_terminates_on_cyclic_target_geo():
    # CBOR value-sharing tags (28/29) make decoded structure possibly
    # cyclic, so the walk needs a seen-set to terminate — and a cycle must
    # not hide an altitude key sitting beside it.
    loop = {"lat": 34.0, "lon": -118.0}
    loop["self"] = loop
    assert _task(_command_event(target_geo=loop)) is not None
    poisoned = {"lat": 34.0, "lon": -118.0}
    poisoned["self"] = poisoned
    poisoned["deep"] = {"alt_m": 100.0}
    with pytest.raises(ValueError, match="target_geo must be 2D"):
        _task(_command_event(target_geo=poisoned))


def test_tuple_shaped_prohibition_refuses_one_container_down():
    # Attack-pass completion (2026-07-27): the top-level shape gate refused
    # a non-dict use_labels, but a dict whose restriction VALUE is a tuple
    # or set normalised to [] in _normalized_uses and exported clean - the
    # same dropped prohibition one container down. Refuse the shape.
    for key in ("prohibited_uses", "allowed_uses"):
        for value in (("COALITION_EXPORT",), {"COALITION_EXPORT"}):
            assert _detection(_state_event(), use_labels={key: value}) is None
    # Control that separates shape-refusal from adjudication: the
    # documented LIST shape still adjudicates - an allowed_uses list
    # granting the export use exports.
    granted = _detection(
        _state_event(), use_labels={"allowed_uses": ["COALITION_EXPORT"]}
    )
    assert granted is not None


def test_list_target_geo_raises_valueerror_not_attributeerror():
    # Attack-pass completion (2026-07-27): a LIST of waypoint dicts walked
    # _contains_altitude clean and then crashed on .get("lat") - an
    # AttributeError outside the documented ValueError/None contract.
    event = _command_event()
    event["payload"]["target_geo"] = [{"lat": 34.0, "lon": -118.0}]
    with pytest.raises(ValueError, match="must be a mapping"):
        _task(event)


def test_gate_clean_naive_ts_refuses_in_both_sapient_egress_twins():
    # Verifier carry-forward (2026-07-27): the CoT/JREAP naive-timestamp
    # closure had its template in THESE twins, which still reinterpreted
    # gate-clean "2026-W01-1Z" as host-local time - a silently shifted
    # instant on the wire (and a skewed report_id ULID time component in
    # the detection). Both refuse now, per each module's None contract.
    for ts in ("1969-12-31Z", "2026-W01-1Z"):
        state = _state_event()
        state["event"]["ts"] = ts
        assert _detection(state) is None
        command = _command_event()
        command["event"]["ts"] = ts
        assert _task(command) is None
