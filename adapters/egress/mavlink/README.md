## ZMeta Command to Mission Intent (Reference)

ZMeta is not a control protocol. This adapter produces a minimal MissionIntent
payload that the Comms/Deconfliction Node (SensorOps) can translate to MAVLink/Swarm API
out-of-band.

Input: ZMeta COMMAND_EVENT
Output: autonomy-agnostic MissionIntent JSON

### Example

Input (ZMeta COMMAND_EVENT):

```
{"event":{"event_type":"COMMAND_EVENT","event_subtype":"MISSION_TASK"},"payload":{"task_id":"task-1","task_type":"GOTO","target_geo":{"lat":34.0,"lon":-118.0},"valid_for_ms":600000,"requires_deconfliction":true}}
```

Output (MissionIntent):

```
{"task_id":"task-1","task_type":"GOTO","target_lat":34.0,"target_lon":-118.0,"valid_for_ms":600000,"priority":"MED","requires_deconfliction":true}
```

### Smoke test

```
python - <<'PY'
from adapters.egress.mavlink.zmeta_command_to_mission_intent import zmeta_command_to_mission_intent

event = {
  "event": {"event_type": "COMMAND_EVENT"},
  "payload": {
    "task_id": "task-1",
    "task_type": "GOTO",
    "target_geo": {"lat": 34.0, "lon": -118.0},
    "valid_for_ms": 600000,
    "requires_deconfliction": True
  }
}
print(zmeta_command_to_mission_intent(event))
PY
```
