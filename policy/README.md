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
- `semantics.yaml` enforces TASK_ACK lifecycle rules (required metrics, allowed states,
  and reason_code requirements), LINK_STATUS health metrics, and SCHEMA_VIOLATION
  reason_code requirements.
- When you introduce new producers, update `routing.yaml` allowlists to keep
  authority boundaries enforced.
- `producer_enforcement.require_allowlist_for_event_types` can require that
  certain event types only originate from allowlisted producers.

Default reference allowlist:
- `torch`: INFERENCE_EVENT + FUSION_EVENT + STATE_EVENT analytics/fusion examples.
- `sensorops`: OBSERVATION/INFERENCE/FUSION/STATE/SYSTEM examples plus COMMAND_EVENT
  gateway examples.

Operational note:
- The same `sensorops` producer ID appears in several reference examples. Command
  events should only originate from a gateway-authorized producer. If you need hard
  tier separation, use distinct producer IDs per tier and allowlist them explicitly.
