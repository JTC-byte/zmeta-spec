# Policy Pack

Policy-as-config rules used by the reference gateway for enforcement.

Files:
- `roles.yaml` allowed event types per node_role
- `profiles.yaml` allowed event types per profile
- `semantics.yaml` cross-field semantic constraints
- `routing.yaml` routing/source constraints
- `violation-codes.yaml` reason codes with severity tiers (advisory for reference implementations)

Normative compliance is defined by the semantic contract and schema; this policy pack
drives reference enforcement behavior.

Notes:
- `routing.yaml` producer rules support `allowed_event_types` and `allowed_event_subtypes`
  for fine-grained gating, plus `forbidden_event_types` for hard blocks.
- When you introduce new producers, update `routing.yaml` allowlists to keep
  authority boundaries enforced.
- `producer_enforcement.require_allowlist_for_event_types` can require that
  certain event types only originate from allowlisted producers.

MVP allowlist (demo):
- `torch`: INFERENCE_EVENT + FUSION_EVENT + STATE_EVENT (gateway analytics/fusion)
- `sensorops`: OBSERVATION/INFERENCE/FUSION/STATE/SYSTEM on edge export, COMMAND on gateway

Operational note:
- The same `sensorops` producer ID is used at edge and gateway in the MVP. Command
  events should only originate from the gateway `sensorops` instance. If you need
  hard enforcement, use distinct producer IDs per tier and allowlist them explicitly.
- `swarmint` is the drone/payload platform vendor in the MVP and is not a ZMeta producer.
