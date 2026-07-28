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
- `command-evidence.yaml` upstream use-limit checks for commands citing lineage evidence
- `profile-precision.yaml` reference profile precision and quantization defaults
- `violation-codes.yaml` reason codes with severity tiers (advisory for reference implementations)

Normative compliance is defined by the semantic contract and schema; this policy pack
drives reference enforcement behavior.

## Reading this pack without a YAML parser

`export/policy/*.json` is a generated, verbatim JSON projection of every file
above, with the same names and the same data, nothing renamed or interpreted. It exists so a
consumer outside the Python stack does not have to vendor a YAML parser or,
as has happened in the field, hand-copy the rules into its own source.

**The YAML here is the source of truth.** The projection is one-directional:
editing a JSON file does not change policy, it produces a stale file that
`python tools/export_policy_json.py --check` fails on. Regenerate with
`python tools/export_policy_json.py` whenever a file above changes; the test
suite enforces it either way. See `export/README.md`.

Rule-class posture:
- `LOCKED` semantics are not policy knobs. Policy must not make invalid event
  vocabulary, layer collapse, unit changes, confidence misuse, lineage gaps,
  profile reinterpretation, command safety violations, or version mismatches
  valid.
- `TUNABLE` behavior belongs here or in deployment config. Examples include
  timing freshness, unresolved-lineage tolerance, producer allowlists, routing
  gates, external-promotion response, confidence/TTL caps, and degraded-link
  handling.
- `ADVISORY` checks may guide display, diagnostics, or recommended quality
  targets, but they are not structural validity unless promoted by a versioned
  schema or policy decision.
- `FUTURE_EXTENSION` concepts remain invalid current vocabulary until the
  version branch, schema/policy behavior, adapter/gateway guidance, encoding
  handling, and conformance evidence exist.

Notes:
- `producer-authority.yaml` uses case-insensitive shell-style producer patterns
  (for example, `rf-sensor-*`) to enforce semantic authority boundaries without
  hard-coding local IDs into the JSON Schema.
- `routing.yaml` producer rules support `allowed_event_types` and `allowed_event_subtypes`
  for fine-grained gating, plus `forbidden_event_types` for hard blocks.
- `routing.yaml`'s `command_event` keys (`required_origin`,
  `must_pass_through`, `allowed_producers`) express the intended command
  topology, but v1.0 enforcement flattens all three into a single
  origin-name allowlist (`gateway/src/validators.py::_is_comms_producer`).
  Per-event transit-path verification is not possible in v1.0, because events carry
  no route metadata, so the machine check is origin gating, not path
  verification.
- `semantics.yaml` enforces TASK_ACK lifecycle rules (required metrics, allowed states,
  and reason_code requirements), LINK_STATUS health metrics, and SCHEMA_VIOLATION
  reason_code requirements.
- `violation-codes.yaml` is the canonical diagnostic vocabulary for
  SCHEMA_VIOLATION reporting. TASK_ACK reason codes remain task-specific and
  are intentionally narrower than the full violation-code list. Versioned
  schemas may expose only the diagnostic codes applicable to that version's
  governed vocabulary.
- `timing-freshness.yaml` defines profile-specific maximum TIME_STATUS age,
  negative-age tolerance, and whether stale, missing, or clock-anomalous timing
  status is rejected, warned, or used to degrade confidence. Its `use_limits`
  labels define what degraded timing data may and may not be used for when a
  deployment chooses soft acceptance.
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
  quarantine. `trust_ref` is a policy-scoped reference, not cryptographic proof
  of producer authenticity.
- Tunable policy modes must not bypass the semantic contract. Soft acceptance
  should carry `risk_dimension`, `policy_mode`, `policy_decision`, policy
  reference, allowed/prohibited uses, and applied effects when data is still
  forwarded.
- Use `python tools/lint_policy_risk_modes.py` after policy edits. The lint
  flags `ignore` on material timing, lineage, external-promotion, command,
  trust, or safety risk; the reference policy only allows `ignore` for the
  Profile L unresolved-parent case where profile thinning can make parent
  references unavailable by design.
  The same lint also checks the STRUCTURE of `producer_authority` and of the
  whole `routing` block (`producers`, `producer_enforcement`,
  `command_event`): unknown key names, and the value TYPE of every key the
  enforcement reads (including the entries inside a by-profile map). Omitting
  a key is legal and means "no constraint"; a key that is present must carry
  its declared shape, because a wrong-typed value is read as "no constraint"
  and silently stops that check from refusing. A key written with no value
  under it (`require_match_for_event_types:` with the items deleted) is a
  wrong-typed value, not an empty list.
  Three further structural checks close the same defect at the levels a
  key-by-key check cannot reach:
  - the BLOCK itself. `producer_authority:` or `routing:` with nothing under
    it is reported rather than skipped over; the container that holds the keys is
    subject to the same mangle as the keys.
  - the ENTRIES of every event-type list
    (`require_match_for_event_types`, `require_allowlist_for_event_types`,
    `allowed_event_types`, `forbidden_event_types`). An entry that is a
    well-formed string but not an event type the schema declares
    (`STATE_EVEN`, `state_event`) can never match, so it drops silently out
    of the gate exactly like a non-string entry. The event-type vocabulary is
    read from `schema/*.schema.json`, never restated in the validator.
    `allowed_event_subtypes` entries are deliberately not checked this way:
    the subtype vocabulary is open through the extension registry.
  - the DOCUMENT's top-level wrapper key. `load_policy` unwraps each file with
    `.get("<wrapper>", <default>)`, so `routng:` loads as the permissive
    default and no in-memory check can tell it apart from an empty block.
    `routing.yaml` and `producer-authority.yaml` are checked for their
    wrapper key directly.
- `routing.producer_enforcement.require_allowlist_for_event_types` is reserved
  for routing-layer allowlists such as COMMAND_EVENT origin gates. It and
  `producer_authority.require_match_for_event_types` fail CLOSED at runtime if
  their value is malformed: an unmatched producer is refused with
  `PRODUCER_NOT_ALLOWED` and a `policy_error` detail naming the defect, rather
  than the gate quietly admitting everything.
- An operator who never runs the lint is still covered at runtime, for the
  same reason. A `routing`, `producer_authority`, `producers`, or per-producer
  rule block that is present but not a mapping, and a producer rule whose
  event-type list has collapsed to "no constraint", are refused with a
  `policy_error` detail naming the file and key. It is never read as "no policy" and
  never raised as an `AttributeError` the receive loop reports as
  `INTERNAL_ERROR`. A refusal caused by broken policy always says so. A bare
  scalar (`allowed_event_types: FUSION_EVENT`) is read as a one-item list and
  loses nothing, so it keeps working at runtime; the lint still reports its
  shape.

Default reference allowlist:
- `torch`: INFERENCE_EVENT + FUSION_EVENT + STATE_EVENT analytics/fusion examples.
- `sensorops`: legacy/reference OBSERVATION/STATE/SYSTEM examples plus
  COMMAND_EVENT gateway examples.

Operational note:
- The same `sensorops` producer ID appears in several reference examples. Command
  events should only originate from a gateway-authorized producer. If you need hard
  tier separation, use distinct producer IDs per tier and allowlist them explicitly.
