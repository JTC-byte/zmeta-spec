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
