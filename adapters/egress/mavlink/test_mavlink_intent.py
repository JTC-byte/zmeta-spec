from adapters.egress.mavlink.zmeta_command_to_mission_intent import zmeta_command_to_mission_intent


def test_command_event_success():
    event = {
        "event": {"event_type": "COMMAND_EVENT"},
        "payload": {
            "task_id": "task-1",
            "task_type": "GOTO",
            "target_geo": {"lat": 34.0, "lon": -118.0},
            "valid_for_ms": 600000,
            "requires_deconfliction": True,
        },
    }

    result = zmeta_command_to_mission_intent(event)
    assert result["task_id"] == "task-1"
    assert result["target_lat"] == 34.0
    assert result["target_lon"] == -118.0


def test_command_event_altitude_raises():
    event = {
        "event": {"event_type": "COMMAND_EVENT"},
        "payload": {
            "task_id": "task-1",
            "task_type": "GOTO",
            "target_geo": {"lat": 34.0, "lon": -118.0, "alt_m": 120.0},
            "valid_for_ms": 600000,
            "requires_deconfliction": True,
        },
    }

    try:
        zmeta_command_to_mission_intent(event)
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_non_command_event_returns_none():
    event = {"event": {"event_type": "STATE_EVENT"}, "payload": {}}
    assert zmeta_command_to_mission_intent(event) is None


# R1-11 A-01: a fly-to command with a NaN destination passes every structural
# check above it. geometry is copied verbatim, so a vertex deep inside it is
# reachable too - hence a value-scoped check on the built mission.
NON_FINITE = (float("nan"), float("inf"), float("-inf"))


def _command_event():
    return {
        "event": {"event_type": "COMMAND_EVENT"},
        "payload": {
            "task_id": "task-1",
            "task_type": "GOTO",
            "target_geo": {"lat": 34.0, "lon": -118.0},
            "valid_for_ms": 600000,
            "requires_deconfliction": True,
        },
    }


def test_non_finite_target_refuses():
    for key in ("lat", "lon"):
        for value in NON_FINITE:
            event = _command_event()
            event["payload"]["target_geo"][key] = value
            assert zmeta_command_to_mission_intent(event) is None, (key, value)


def test_non_finite_valid_for_ms_refuses():
    for value in NON_FINITE:
        event = _command_event()
        event["payload"]["valid_for_ms"] = value
        assert zmeta_command_to_mission_intent(event) is None, value


def test_non_finite_geometry_vertex_refuses():
    for value in NON_FINITE:
        event = _command_event()
        event["payload"]["geometry"] = {
            "type": "POLYGON",
            "vertices": [{"lat": 34.0, "lon": -118.0}, {"lat": value, "lon": -118.1}],
        }
        assert zmeta_command_to_mission_intent(event) is None, value


def test_clean_command_still_projects():
    import json

    result = zmeta_command_to_mission_intent(_command_event())
    assert result is not None
    json.dumps(result, allow_nan=False)


# R1-11, third pass (R2-07). Both walks in this adapter descended dict/list
# only; the altitude walk was additionally recursive, so it raised
# RecursionError on deep geometry - a crash where the documented signal is
# None/ValueError, in the guard that keeps vertical intent out of a mission.


class _CborTag:
    """Stand-in for cbor2.CBORTag: an unrecognised tag decodes to an object
    whose `.value` still reaches the consumer."""

    def __init__(self, tag, value):
        self.tag = tag
        self.value = value


def _deep(leaf, depth=3000):
    node = leaf
    for _ in range(depth):
        node = {"n": node}
    return node


def test_non_finite_walk_terminates_on_cyclic_geometry():
    from adapters.egress.mavlink.zmeta_command_to_mission_intent import _has_non_finite

    loop = {"lat": 34.0}
    loop["self"] = loop
    assert _has_non_finite(loop) is False
    poisoned = {"lat": float("nan")}
    poisoned["self"] = poisoned
    assert _has_non_finite(poisoned) is True


def test_altitude_walk_terminates_on_cyclic_and_deep_geometry():
    # The recursive version raised RecursionError here. geometry is copied
    # verbatim from a sender-controlled payload.
    from adapters.egress.mavlink.zmeta_command_to_mission_intent import _contains_altitude

    loop = {"lat": 34.0}
    loop["self"] = loop
    assert _contains_altitude(loop) is False
    assert _contains_altitude(_deep({"lat": 34.0})) is False
    assert _contains_altitude(_deep({"alt_m": 100.0})) is True


def test_altitude_walk_sees_every_decoded_container():
    # Contract 7.8 is a fielded-safety rule: a COMMAND_EVENT must carry no
    # vertical intent. An altitude key one container off dict/list reached an
    # autonomy stack unremarked.
    from collections import OrderedDict

    from adapters.egress.mavlink.zmeta_command_to_mission_intent import _contains_altitude

    for blob in (
        ({"alt_m": 100.0},),
        [[{"ALT_M ": 100.0}]],
        OrderedDict({"vertices": [{"altitude": 100.0}]}),
        _CborTag(4242, {"agl_m": 50.0}),
        {"outer": {"inner": ({"target_alt_m": 1.0},)}},
    ):
        assert _contains_altitude(blob) is True, blob
    for clean in (({"lat": 1.0},), [[{"lon": 2.0}]], "alt_m", {"altimeter_note": "x"}):
        assert _contains_altitude(clean) is False, clean


def test_altitude_in_an_exotic_container_still_raises_at_the_boundary():
    event = _command_event()
    event["payload"]["geometry"] = {"type": "POLYGON", "vertices": ({"alt_m": 100.0},)}
    try:
        zmeta_command_to_mission_intent(event)
    except ValueError:
        pass
    else:
        raise AssertionError("altitude in a tuple-borne vertex was projected")


def test_non_finite_walk_sees_every_decoded_container():
    from collections import OrderedDict
    from decimal import Decimal

    from adapters.egress.mavlink.zmeta_command_to_mission_intent import _has_non_finite

    for blob in (
        {float("nan")},
        frozenset({float("inf")}),
        (1.0, float("-inf")),
        _CborTag(4242, [float("nan")]),
        OrderedDict({"lat": float("nan")}),
        Decimal("NaN"),
        {"nested": [{"deep": (Decimal("Infinity"),)}]},
    ):
        assert _has_non_finite({"geometry": blob}) is True, blob
    assert _has_non_finite({float("nan"): "x"}) is True
    assert _has_non_finite({"a": "x", "b": ["y"], "c": 1.0, "d": b"z"}) is False


def test_non_finite_in_an_exotic_geometry_container_refuses_the_mission():
    from decimal import Decimal

    for blob in ({1.0, float("nan")}, (float("inf"),), Decimal("NaN")):
        event = _command_event()
        event["payload"]["geometry"] = {"type": "POLYGON", "vertices": blob}
        assert zmeta_command_to_mission_intent(event) is None, blob


def test_clean_command_with_exotic_but_finite_containers_still_projects():
    event = _command_event()
    event["payload"]["geometry"] = {
        "type": "POLYGON",
        "vertices": ({"lat": 34.0, "lon": -118.0},),
    }
    assert zmeta_command_to_mission_intent(event) is not None


# R1-11 CR-08: CommandPayload.priority is OPTIONAL with no declared default -
# an omitted priority is the absence of a priority claim. This egress stamped
# priority=MED on commands that carried none, a fabricated tasking-priority
# claim reaching an autonomy consumer clean. Refuse-or-omit: map only what is
# present.


def test_priority_less_command_omits_priority():
    event = _command_event()
    assert "priority" not in event["payload"]
    result = zmeta_command_to_mission_intent(event)
    assert result is not None
    assert "priority" not in result, result
    # the omission touches nothing else in the projection
    assert result["task_id"] == "task-1"
    assert result["task_type"] == "GOTO"
    assert result["valid_for_ms"] == 600000
    assert result["requires_deconfliction"] is True
    assert result["target_lat"] == 34.0
    assert result["target_lon"] == -118.0


def test_priority_present_maps_exactly():
    for value in ("LOW", "MED", "HIGH"):
        event = _command_event()
        event["payload"]["priority"] = value
        result = zmeta_command_to_mission_intent(event)
        assert result is not None
        assert result["priority"] == value, value


# Maintainer decision 2026-08-02: this translator had zero awareness of
# payload.extensions.risk_adjudication, so a COMMAND_EVENT the gateway
# soft-flagged (gateway/src/validators.py _append_risk_adjudication, the
# S1-15 soft-acceptance stamp) still became a clean MissionIntent. The
# record shape below is copied from the gateway's own stamp
# (gateway/tests/test_command_evidence.py
# test_prohibited_use_degrade_mode_stamps_the_command), not guessed: a
# non-empty payload.extensions.risk_adjudication list is only ever written
# onto a command the gateway did NOT forward clean.
RISK_ADJUDICATION_RECORD = {
    "risk_dimension": "lineage",
    "reason_code": "LINEAGE_MISMATCH",
    "policy_mode": "degrade",
    "policy_decision": "DEGRADED_ACCEPT",
    "policy_ref": "policy/command-evidence.yaml#prohibited_use_mode",
    "allowed_uses": ["DISPLAY", "LOCAL_AWARENESS", "ALERTING"],
    "prohibited_uses": ["AUTONOMY_TASKING"],
}


def _flagged_command_event():
    event = _command_event()
    event["payload"]["extensions"] = {
        "risk_adjudication": [dict(RISK_ADJUDICATION_RECORD)]
    }
    return event


def test_risk_flagged_command_refused_by_default():
    assert zmeta_command_to_mission_intent(_flagged_command_event()) is None


def test_risk_flagged_command_with_override_translates_and_stamps():
    result = zmeta_command_to_mission_intent(_flagged_command_event(), allow_flagged=True)
    assert result is not None
    assert result["task_id"] == "task-1"
    assert result["risk_adjudication"] == [RISK_ADJUDICATION_RECORD]


def test_altitude_inside_risk_record_refused_even_under_override():
    # The copied risk_adjudication records were the one conduit the module's
    # "no vertical intent reaches the mission-intent output" guarantee did
    # not cover: under allow_flagged=True they were deep-copied verbatim
    # with no _contains_altitude walk, so an altitude key inside a record
    # projected despite contract 7.8's whole-payload prohibition. The
    # whole-mission walk now refuses it.
    event = _command_event()
    record = dict(RISK_ADJUDICATION_RECORD)
    record["target_alt_m"] = 120.0
    event["payload"]["extensions"] = {"risk_adjudication": [record]}
    try:
        zmeta_command_to_mission_intent(event, allow_flagged=True)
    except ValueError:
        pass
    else:
        raise AssertionError(
            "an altitude key inside a risk_adjudication record must refuse"
        )


def test_unflagged_command_unchanged_by_allow_flagged_param():
    default_result = zmeta_command_to_mission_intent(_command_event())
    override_result = zmeta_command_to_mission_intent(_command_event(), allow_flagged=True)
    assert default_result == override_result
    assert "risk_adjudication" not in default_result


def test_malformed_risk_adjudication_shape_refuses_by_default():
    # Present but not the documented list shape: unreadable, and an
    # unreadable label set may well be prohibiting command basis, so it
    # must not be read as "no flag" (mirrors the gateway's own
    # UNADJUDICABLE_RISK_SHAPE precedent).
    event = _command_event()
    event["payload"]["extensions"] = {"risk_adjudication": dict(RISK_ADJUDICATION_RECORD)}
    assert zmeta_command_to_mission_intent(event) is None


def test_empty_risk_adjudication_list_is_not_a_flag():
    # An empty list means nothing was ever stamped; it must not by itself
    # refuse a command that otherwise projects cleanly.
    event = _command_event()
    event["payload"]["extensions"] = {"risk_adjudication": []}
    result = zmeta_command_to_mission_intent(event)
    assert result is not None
    assert "risk_adjudication" not in result
