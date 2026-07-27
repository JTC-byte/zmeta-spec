## ZMeta Command to Mission Intent (Reference)

Overview: see `adapters/README.md`.

ZMeta is not a control protocol. This adapter produces a minimal MissionIntent
payload that the Comms/Deconfliction Node (SensorOps) can translate to MAVLink/Swarm API
out-of-band.

Input: ZMeta COMMAND_EVENT
Output: autonomy-agnostic MissionIntent JSON

### Guards

| Condition | Disposition |
|-----------|-------------|
| An altitude field anywhere inside `target_geo` or `geometry` | `ValueError` — semantics contract 7.8: a `COMMAND_EVENT` carries no vertical intent, the receiving autonomy deconflicts vertical internally |
| Not a `COMMAND_EVENT`, missing `task_id`/`task_type`/`valid_for_ms`/`requires_deconfliction`, or `requires_deconfliction` is not `True` | `None` |
| Non-finite (`NaN`/`inf`) number anywhere in the projected mission | `None` — a non-finite target is a fly-to command with no destination, and it satisfies every structural check |

The authoritative altitude gate is the gateway validator
(`COMMAND_HAS_ALTITUDE`); the check here is defence in depth and keeps its key
set a superset of `policy/semantics.yaml`
`command_event.payload_must_not_contain`.

`priority` maps only when the command carries one. It is optional in the
schema with no declared default, so a priority-less command projects a
mission with no `priority` key — an unstated tasking priority is omitted,
never defaulted.

Both walks descend containers by abstract type (`Mapping`, `Set`, `Sequence`,
CBOR tag wrappers), not just `dict`/`list`, and share one iterative traversal
with a seen-set: `geometry` is copied verbatim from a sender-controlled
payload, so nesting depth must be a bounded memory cost rather than a
`RecursionError`, and a cyclic structure — reachable via CBOR value-sharing
tags on a `cbor2`-only install — must terminate rather than hang.

### Example

Input (ZMeta COMMAND_EVENT):

```
{"event":{"event_type":"COMMAND_EVENT","event_subtype":"GOTO"},"payload":{"task_id":"task-1","task_type":"GOTO","target_geo":{"lat":34.0,"lon":-118.0},"valid_for_ms":600000,"requires_deconfliction":true}}
```

Output (MissionIntent):

```
{"task_id":"task-1","task_type":"GOTO","target_lat":34.0,"target_lon":-118.0,"valid_for_ms":600000,"requires_deconfliction":true}
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
