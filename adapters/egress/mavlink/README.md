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
| An altitude field anywhere inside `target_geo` or `geometry` | `ValueError`; semantics contract 7.8: a `COMMAND_EVENT` carries no vertical intent, the receiving autonomy deconflicts vertical internally |
| Not a `COMMAND_EVENT`, missing `task_id`/`task_type`/`valid_for_ms`/`requires_deconfliction`, or `requires_deconfliction` is not `True` | `None` |
| `payload.extensions.risk_adjudication` is a non-empty list (see Risk adjudication below) and `allow_flagged` is not passed | `None` |
| Non-finite (`NaN`/`inf`) number anywhere in the projected mission | `None`; a non-finite target is a fly-to command with no destination, and it satisfies every structural check |

The authoritative altitude gate is the gateway validator
(`COMMAND_HAS_ALTITUDE`); the check here is defence in depth and keeps its key
set a superset of `policy/semantics.yaml`
`command_event.payload_must_not_contain`.

### Risk adjudication (fail-closed by default)

The gateway can soft-accept a `COMMAND_EVENT` instead of rejecting it outright
(`warn`/`degrade` command-evidence dispositions, `policy/command-evidence.yaml`
`prohibited_use_mode`), for example when a command cites motivating evidence
whose own risk adjudication prohibits `COMMAND_BASIS` or `AUTONOMY_TASKING`
use. A `degrade` disposition stamps that adjudication onto the command's own
`payload.extensions.risk_adjudication` (`gateway/src/validators.py`
`_append_risk_adjudication`); a non-empty list there means the gateway did not
forward this command clean.

This translator refuses such a command by default, returning `None`, the same
signal as every other refusal above. Operators wire their own autonomy policy
on this stream; ZMeta does not adjudicate it. A soft-accepted command that
translates clean would silently drop the gateway's flag, and a flag that
vanishes at translation is laundering a safety signal.

Pass `allow_flagged=True` to opt in explicitly. The command is translated and
the `risk_adjudication` records are copied onto the `MissionIntent` output
under the same key, so the disposition travels with the command instead of
disappearing:

```
zmeta_command_to_mission_intent(event, allow_flagged=True)
```

An empty `risk_adjudication` list, or its absence, is not a flag: nothing was
ever stamped, so the command projects normally either way.

`priority` maps only when the command carries one. It is optional in the
schema with no declared default, so a priority-less command projects a
mission with no `priority` key. An unstated tasking priority is omitted,
never defaulted.

Both walks descend containers by abstract type (`Mapping`, `Set`, `Sequence`,
CBOR tag wrappers), not just `dict`/`list`, and share one iterative traversal
with a seen-set: `geometry` is copied verbatim from a sender-controlled
payload, so nesting depth must be a bounded memory cost rather than a
`RecursionError`, and a cyclic structure, reachable via CBOR value-sharing
tags on a `cbor2`-only install, must terminate rather than hang.

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
