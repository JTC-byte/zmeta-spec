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
