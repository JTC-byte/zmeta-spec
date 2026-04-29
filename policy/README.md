# Policy Pack

Policy-as-config rules used by the reference gateway for enforcement.

Files:
- `roles.yaml` allowed event types per node_role
- `profiles.yaml` allowed event types per profile
- `semantics.yaml` cross-field semantic constraints
- `producer-authority.yaml` producer identity authority rules
- `lineage.yaml` context-aware lineage consistency rules
- `timing-freshness.yaml` runtime TIME_STATUS freshness rules
- `routing.yaml` routing/source constraints
- `violation-codes.yaml` reason codes with severity tiers (advisory for reference implementations)

Normative compliance is defined by the semantic contract and schema; this policy pack
drives reference enforcement behavior.

Notes:
- `producer-authority.yaml` uses case-insensitive shell-style producer patterns
  (for example, `rf-sensor-*`) to enforce semantic authority boundaries without
  hard-coding local IDs into the JSON Schema.
- `routing.yaml` producer rules support `allowed_event_types` and `allowed_event_subtypes`
  for fine-grained gating, plus `forbidden_event_types` for hard blocks.
- `semantics.yaml` enforces TASK_ACK lifecycle rules (required metrics, allowed states,
  and reason_code requirements), LINK_STATUS health metrics, and SCHEMA_VIOLATION
  reason_code requirements.
- `violation-codes.yaml` is the canonical diagnostic vocabulary for
  SCHEMA_VIOLATION reporting. TASK_ACK reason codes remain task-specific and
  are intentionally narrower than the full violation-code list. Versioned
  schemas may expose only the diagnostic codes applicable to that version's
  governed vocabulary.
- `timing-freshness.yaml` defines profile-specific maximum TIME_STATUS age and
  whether stale or missing timing status is rejected, warned, or used to degrade
  confidence.
- `lineage.yaml` defines payload/envelope lineage consistency, permitted parent
  event types when a local event store is available, and unresolved-parent
  handling by profile.
- When you introduce new producers, update `producer-authority.yaml` first.
  Update `routing.yaml` only for command-path or transport-specific routing
  constraints.
- `producer_authority.require_match_for_event_types` can require that event
  types only originate from matching producer authority rules.
- `routing.producer_enforcement.require_allowlist_for_event_types` is reserved
  for routing-layer allowlists such as COMMAND_EVENT origin gates.

Default reference allowlist:
- `torch`: INFERENCE_EVENT + FUSION_EVENT + STATE_EVENT analytics/fusion examples.
- `sensorops`: legacy/reference OBSERVATION/STATE/SYSTEM examples plus
  COMMAND_EVENT gateway examples.

Operational note:
- The same `sensorops` producer ID appears in several reference examples. Command
  events should only originate from a gateway-authorized producer. If you need hard
  tier separation, use distinct producer IDs per tier and allowlist them explicitly.
