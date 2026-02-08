# Profile Compatibility Matrix

This page summarizes **which event types are allowed per profile** and the
MVP **producer allowlists**. The authoritative rules live in:
- `policy/profiles.yaml`
- `policy/roles.yaml`
- `policy/routing.yaml`

## Profile vs Event Types

| Profile | Allowed Event Types |
| --- | --- |
| L | STATE_EVENT, SYSTEM_EVENT, COMMAND_EVENT |
| M | STATE_EVENT, FUSION_EVENT, SYSTEM_EVENT, COMMAND_EVENT, OBSERVATION_EVENT |
| H | OBSERVATION_EVENT, INFERENCE_EVENT, FUSION_EVENT, STATE_EVENT, COMMAND_EVENT, SYSTEM_EVENT |

## Recommended Encodings (Wire)

| Profile | Recommended Encoding | Notes |
| --- | --- | --- |
| L | `compact` | Smallest wire format; intended for bandwidth‑constrained links. |
| M | `cbor` or `json` | CBOR reduces size with modest CPU cost. |
| H | `json` | Best for debug and interoperability; size is less constrained. |

## MVP Producer Allowlists

| Producer | Allowed Event Types | Notes |
| --- | --- | --- |
| `sensorops` | OBSERVATION, INFERENCE, FUSION, STATE, COMMAND, SYSTEM | Required origin for COMMAND_EVENT. |
| `torch` | INFERENCE, FUSION, STATE | COMMAND_EVENT forbidden. |

Command routing rules (MVP):
- `COMMAND_EVENT` must originate from `sensorops`.
- `COMMAND_EVENT` must pass through `sensorops`.

## Node Role Constraints (Policy)

| Node Role | Allowed Event Types |
| --- | --- |
| EDGE | OBSERVATION_EVENT, SYSTEM_EVENT |
| GATEWAY | OBSERVATION_EVENT, INFERENCE_EVENT, FUSION_EVENT, STATE_EVENT, COMMAND_EVENT, SYSTEM_EVENT |
| APEX | FUSION_EVENT, STATE_EVENT, SYSTEM_EVENT |
| DMZ | SYSTEM_EVENT, STATE_EVENT |
| CLOUD | SYSTEM_EVENT, STATE_EVENT |

Use this matrix for quick compatibility checks; always defer to the policy
files for enforcement and release decisions.
