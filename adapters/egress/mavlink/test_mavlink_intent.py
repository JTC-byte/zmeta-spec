import pytest

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


# Contract 7.8 (2026-11-02): a command's validity window begins at
# payload.valid_from_ts when present, otherwise at event.ts, and ends
# valid_for_ms after that start. The MissionIntent carries valid_for_ms and
# no anchor, so a receiver can only start the duration at receipt, and a
# window that opens after event.ts would start early. On the maintainer's
# selection of 2026-11-16 this egress refuses such a command by the SAPIENT
# egress's rule: the comparison is strict, and a valid_from_ts it cannot
# read, or one whose event.ts it cannot read, is refused the same way. A
# command without valid_from_ts reads no time and goes out as before.
#
# Every case is a GOTO valid for 600 s; the issue time is
# 2026-11-14T12:00:00Z unless the case says otherwise. Case letters:
#   A  the window opens after issue: refused. The offset form is the same
#      instant written another way, so a comparison of the two texts would
#      project it; the 1999 case is in the past for any clock, so only the
#      comparison with event.ts refuses it.
#   B  no valid_from_ts: the intent as before.
#   C  the start equals the issue time: the intent (the comparison is
#      strict). The 2099 case is in the future for any clock.
#   D  the start is before issue and the window is still open: the intent.
#   E  the window closed before issue: the intent, unchanged. Whether that
#      is refused is outside this rule.
#   F  the start is 1 ms after issue: refused.
#   G  valid_from_ts cannot be read: refused. "naive-day-before" has no
#      offset and is a day before issue, so read as host-local time it
#      opens before issue in every zone and only the offset rule refuses it.
#      "date-only" ends in Z, as the schema's pattern asks, yet parses with
#      no offset; read as host-local midnight it opens at or before issue in
#      every zone. The number (11:50:00Z as epoch seconds) and the list's
#      one element (11:58:00Z) are before issue too, so a reader that took a
#      number as epoch seconds or unwrapped a list would project them.
#   H  valid_from_ts is present and event.ts is absent or cannot be read:
#      refused. "naive" and "date-only" are a day or more after the start
#      for the same reason.
#   I  no valid_from_ts and no readable event.ts: the intent as before, the
#      way the README example and the tests above carry no event.ts.
#   A null valid_from_ts is read as absent, as the SAPIENT egress reads it;
#   the schemas refuse a null, so only a caller wired past the gateway sends
#   one.
_ISSUE = "2026-11-14T12:00:00Z"
_ABSENT = object()
# A ULID task_id, so the SAPIENT egress's own ULID rule does not refuse
# first in the parity test below.
_WINDOW_TASK_ID = "01ARZ3NDEKTSV4RRFFQ69G5FAV"
# What this module returned for every one of these commands before the rule.
_WINDOW_INTENT = {
    "task_id": _WINDOW_TASK_ID,
    "task_type": "GOTO",
    "valid_for_ms": 600000,
    "requires_deconfliction": True,
    "target_lat": 34.0101,
    "target_lon": -118.0101,
}
_REFUSED_WINDOWS = [
    ("A", "2026-11-14T12:10:00Z", _ISSUE),
    ("A-offset", "2026-11-14T07:10:00-05:00", _ISSUE),
    ("A-1999", "1999-01-01T00:10:00Z", "1999-01-01T00:00:00Z"),
    ("F", "2026-11-14T12:00:00.001Z", _ISSUE),
    ("G-text", "not-a-time", _ISSUE),
    ("G-empty", "", _ISSUE),
    ("G-number", 1794657000, _ISSUE),
    ("G-list", ["2026-11-14T11:58:00Z"], _ISSUE),
    ("G-naive-after", "2026-11-14T12:10:00", _ISSUE),
    ("G-naive-day-before", "2026-11-13T12:00:00", _ISSUE),
    ("G-date-only", "2026-11-14Z", _ISSUE),
    ("G-out-of-range", "0001-01-01T00:00:00+01:00", _ISSUE),
    ("H-absent", "2026-11-14T11:58:00Z", _ABSENT),
    ("H-null", "2026-11-14T11:58:00Z", None),
    ("H-text", "2026-11-14T11:58:00Z", "not-a-time"),
    ("H-empty", "2026-11-14T11:58:00Z", ""),
    ("H-number", "2026-11-14T11:58:00Z", 1794880770),
    ("H-naive", "2026-11-14T11:58:00Z", "2026-11-15T12:00:00"),
    ("H-date-only", "2026-11-14T11:58:00Z", "2026-11-16Z"),
]
_PROJECTED_WINDOWS = [
    ("B", _ABSENT, _ISSUE),
    ("C", "2026-11-14T12:00:00Z", _ISSUE),
    ("C-offset", "2026-11-14T07:00:00-05:00", _ISSUE),
    ("C-2099", "2099-01-01T00:00:00Z", "2099-01-01T00:00:00Z"),
    ("D", "2026-11-14T11:58:00Z", _ISSUE),
    ("E", "2026-11-14T11:00:00Z", _ISSUE),
    ("I", _ABSENT, _ABSENT),
    ("I-text-ts", _ABSENT, "not-a-time"),
    ("I-naive-ts", _ABSENT, "2026-11-14T12:00:00"),
    ("I-number-ts", _ABSENT, 1794880770),
    ("null-start", None, _ISSUE),
    ("null-start-no-ts", None, _ABSENT),
]


def _windowed_goto(valid_from_ts, ts):
    event = {
        "zmeta_version": "1.0",
        "event": {
            "event_id": "019c2b5c-c047-73ea-8f1a-302fc3049334",
            "event_type": "COMMAND_EVENT",
            "event_subtype": "GOTO",
        },
        "source": {"platform_id": "comms-node-1", "node_role": "GATEWAY", "producer": "sensorops"},
        "profile": "L",
        "payload": {
            "task_id": _WINDOW_TASK_ID,
            "task_type": "GOTO",
            "target_geo": {"lat": 34.0101, "lon": -118.0101},
            "valid_for_ms": 600000,
            "requires_deconfliction": True,
        },
    }
    if ts is not _ABSENT:
        event["event"]["ts"] = ts
    if valid_from_ts is not _ABSENT:
        event["payload"]["valid_from_ts"] = valid_from_ts
    return event


@pytest.mark.parametrize(
    ("valid_from_ts", "ts"),
    [case[1:] for case in _REFUSED_WINDOWS],
    ids=[case[0] for case in _REFUSED_WINDOWS],
)
def test_a_window_not_open_at_issue_or_not_readable_is_refused(valid_from_ts, ts):
    assert zmeta_command_to_mission_intent(_windowed_goto(valid_from_ts, ts)) is None


@pytest.mark.parametrize(
    ("valid_from_ts", "ts"),
    [case[1:] for case in _PROJECTED_WINDOWS],
    ids=[case[0] for case in _PROJECTED_WINDOWS],
)
def test_a_window_opened_by_issue_or_no_start_projects_as_before(valid_from_ts, ts):
    assert zmeta_command_to_mission_intent(_windowed_goto(valid_from_ts, ts)) == _WINDOW_INTENT


def test_a_later_start_beside_an_altitude_still_raises():
    # The window check runs after every other guard, so a command that
    # raised before the rule still raises: an altitude in target_geo is a
    # ValueError whatever its window says.
    event = _windowed_goto("2026-11-14T12:10:00Z", _ISSUE)
    event["payload"]["target_geo"]["alt_m"] = 120.0
    with pytest.raises(ValueError):
        zmeta_command_to_mission_intent(event)


def test_the_two_egresses_read_a_time_with_the_same_code():
    # This module's _parse_utc is a copy of the SAPIENT egress's, since the
    # adapters do not import each other. Comments aside, the two must stay
    # the same code, so a change to one copy fails here until the other
    # follows.
    import ast
    import inspect

    from adapters.egress.mavlink import zmeta_command_to_mission_intent as mavlink
    from adapters.egress.sapient import zmeta_command_to_sapient_task as sapient

    def code_of(function):
        return ast.dump(ast.parse(inspect.getsource(function)))

    assert code_of(mavlink._parse_utc) == code_of(sapient._parse_utc)


def test_the_mavlink_and_sapient_egresses_refuse_the_same_windows():
    # The two reference command egresses refuse the same windows among cases
    # A to H that carry an event.ts key (unreadable in H). They differ by
    # design on a command without valid_from_ts whose event.ts is absent or
    # cannot be read: the SAPIENT egress refuses it and this egress sends it
    # as before, so the I cases and the cases with no event.ts stay out.
    from adapters.egress.sapient.zmeta_command_to_sapient_task import zmeta_command_to_sapient_task

    node_id = "0f2c8b4e-9f1d-4e6a-8a3b-1c5d7e9f0a2b"
    destination_id = "7a1b3c5d-2e4f-4a6b-8c0d-9e1f3a5b7c9d"
    cases = [
        case
        for case in _REFUSED_WINDOWS + _PROJECTED_WINDOWS
        if case[2] is not _ABSENT and not case[0].startswith("I")
    ]
    mavlink_refused = set()
    sapient_refused = set()
    for name, valid_from_ts, ts in cases:
        if zmeta_command_to_mission_intent(_windowed_goto(valid_from_ts, ts)) is None:
            mavlink_refused.add(name)
        task = zmeta_command_to_sapient_task(
            _windowed_goto(valid_from_ts, ts), node_id=node_id, destination_id=destination_id
        )
        if task is None:
            sapient_refused.add(name)
    assert mavlink_refused == sapient_refused
    # The SAPIENT egress refuses exactly the refused cases and projects the
    # others, so the equality above cannot hold by both refusing everything
    # or both refusing nothing.
    assert sapient_refused == {name for name, _, ts in _REFUSED_WINDOWS if ts is not _ABSENT}
    assert len(cases) - len(sapient_refused) == 7
