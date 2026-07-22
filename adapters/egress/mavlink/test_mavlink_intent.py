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
