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
  confidence. Its `use_limits` labels define what degraded timing data may and
  may not be used for when a deployment chooses soft acceptance.
- `lineage.yaml` defines payload/envelope lineage consistency, permitted parent
  event types when a local event store is available, and unresolved-parent
  handling by profile. Its `use_limits` keep unresolved-lineage warnings
  filterable without making Profile L links fail by default.
- When you introduce new producers, update `producer-authority.yaml` first.
  Update `routing.yaml` only for command-path or transport-specific routing
  constraints.
- `producer_authority.require_match_for_event_types` can require that event
  types only originate from matching producer authority rules.
- `producer_authority.external_state_promotion` requires CoT/JREAP/MAVLink and
  other explicitly marked external ingress producers to attach valid promotion
  evidence before their `STATE_EVENT` output is accepted as authoritative ZMeta
  state. This prevents schema-valid lossy projections from re-entering as
  laundered state. The default mode is `reject`; deployments may tune this to
  `warn`, `degrade`, or `quarantine` for edge conditions. Non-reject modes still
  emit diagnostics, and degrade/quarantine modes lower confidence and/or shorten
  `payload.valid_for_ms` so accepted state does not look equivalent to clean
  promoted state. Mode may be set globally, by profile with `mode_by_profile`,
  or on a specific producer's `external_state_promotion` rule. Its `use_limits`
  declare which downstream uses remain allowed under warn, degrade, or
  quarantine.
- Tunable policy modes must not bypass the semantic contract. Soft acceptance
  should carry `risk_dimension`, `policy_mode`, `policy_decision`, policy
  reference, allowed/prohibited uses, and applied effects when data is still
  forwarded.
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
