# S1-03A Extension Registry Plan

Status: COMPLETE
Date: 2026-05-07
Scope: Planning only. No schemas, validators, adapters, encodings, examples,
fixtures, semantic contract text, or event vocabulary are changed by this work
item.

## A. Current Extension Governance Summary

The current stack already has several governance surfaces, but they are split
across prose, schemas, tests, and policy files.

- v1.0 locked vocabulary: `schema/zmeta-event-1.0.schema.json` accepts exactly
  `zmeta_version: "1.0"` and contains the locked event types, subtypes,
  payload discriminators, profile compatibility rules, UUIDv7 identity rules,
  confidence/lineage requirements, state raw-field prohibitions, and command
  altitude prohibitions.
- v1.1.0 experimental extension vocabulary:
  `schema/zmeta-event-1.1.0.schema.json` accepts exactly
  `zmeta_version: "1.1.0"` and adds version-selected structured quality,
  `error_ellipse_m`, formal `data_ref` / `data_refs` behavior, EO/IR/ACOUSTIC/
  NETWORK feature contracts, `SENSOR_STATUS`, `PLATFORM_STATUS`, and expanded
  bounded command task types.
- Future candidate vocabulary: `spec/semantics-contract.md`,
  `schema/README.md`, the lockdown audit, and the crosswalk reserve future
  trust, signing, UAS identity, release, PNT integrity, replay, data nutrition,
  emergency/L0, projection metadata, AI assurance, and lifecycle concepts by
  prose only.
- Exact version dispatch: `schema/zmeta-event.schema.json` uses `oneOf` to
  dispatch to the v1.0 or v1.1.0 schema by exact `zmeta_version`. Aliases such
  as `1.1` are not canonical schema values.
- Schema branch isolation: v1.1.0-only system subtypes, command subtypes, and
  `error_ellipse_m` do not validate as v1.0. v1.0 intentionally allows generic
  observation extension surfaces such as `payload.quality`, `payload.data_ref`,
  `payload.data_refs`, and generic features, but those do not adopt the v1.1.0
  formal contracts unless the v1.1.0 branch is selected.
- Prose-based reserved names: RADAR, LIDAR, MAGNETIC, SEISMIC, CYBER, and
  SIGINT are documented and tested as rejected observation modalities until a
  future feature contract is adopted. Additional future concepts are reserved in
  contract prose but not yet listed in a durable registry.
- Profile projection preservation: S1-02B/S1-02C added a sidecar field catalog,
  source/projected fixtures, standalone projection validator, and opt-in
  conformance runner integration. Projection preservation is not a schema
  mutation.
- Compact/protobuf projection rules: compact CBOR and protobuf remain encoding
  projections only. They must decode to canonical JSON before schema, policy,
  and projection checks.
- Conformance fixtures: existing JSONL fixtures prove single-event schema and
  policy behavior; profile projection fixtures prove source/projected thinning
  behavior. There is not yet a registry-specific conformance artifact.

## B. Problem Statement

Prose-only reservation is not durable enough for the next phase of ZMeta
extension work. The repository already distinguishes locked v1.0 vocabulary,
experimental v1.1.0 vocabulary, and future candidates, but that distinction is
not yet captured as a machine-checkable governance artifact.

Risks:

- Vocabulary collision: future prompts can reuse names already held by v1.0,
  v1.1.0, or another proposed extension.
- Accidental v1.0/v1.1 leakage: extension fields can be added to the wrong
  schema branch or interpreted under the wrong exact `zmeta_version`.
- Vendor namespace drift: free-form payload and `extensions` objects can carry
  core-looking semantics without a registered namespace, owner, status, or
  ignorable-by-default rule.
- Extensions that are not safe to ignore: a producer can hide required meaning
  in an optional-looking field, forcing downstream consumers to treat undefined
  data as operationally significant.
- Hidden semantic changes: schema shape can change without a matching semantic
  definition, policy rule, adapter/gateway behavior, encoding note, or
  conformance case.
- Implementation without tests: a field can appear in examples or adapters
  before positive and negative fixtures prove its behavior.
- Future concepts before version approval: trust, signing, release, replay,
  emergency/L0, AI assurance, or lifecycle names can become de facto vocabulary
  simply because an adapter emits them.

## C. Proposed Registry Artifacts

Recommended S1-03B artifacts:

- Human-readable registry: `spec/extension-registry.md`
- Machine-readable registry: `spec/extension-registry.yaml`

Rationale: the registry governs semantic vocabulary and version adoption, so it
belongs under `spec/` rather than only under `conformance/`. Conformance should
consume the registry, not own it. A future `conformance/extension-registry/`
directory may hold registry validation fixtures, but the source of truth should
remain in `spec/`.

Recommended supporting artifacts for S1-03B:

- Registry validator: `tools/validate_extension_registry.py`
- Optional registry record schema: `schema/extension-registry.schema.json`
- Tests: `gateway/tests/test_extension_registry.py`
- Documentation integration updates:
  `spec/README.md`, `schema/README.md`, `conformance/README.md`,
  `docs/zmeta_refinement_worklog.md`, and
  `docs/zmeta_refinement_handoff.md`

## D. Registry Record Model

Each registry record should contain these fields:

- `name`: stable machine identifier, uppercase token for core vocabulary or a
  namespaced key for vendor/private vocabulary.
- `display_name`: human-readable name.
- `category`: one of the governed registry categories.
- `status`: `reserved`, `proposed`, `experimental`, `adopted`, `deprecated`,
  `rejected`, or `superseded`.
- `version_branch`: version branch that owns the concept, or `null` for
  reserved/proposed concepts without branch approval.
- `introduced_in`: exact schema/contract version where the concept first became
  valid, or `null` until valid.
- `owner`: responsible project owner, working group, vendor namespace owner, or
  `TBD`.
- `semantic_definition`: concise statement of meaning and boundaries.
- `rationale`: why the extension exists.
- `allowed_event_types`: event families where the concept may appear.
- `allowed_event_subtypes`: specific subtype values or payload discriminators,
  when applicable.
- `payload_scope`: allowed payload paths or structural scope.
- `profile_scope`: allowed profiles or profile-export constraints.
- `schema_status`: `none`, `planned`, `implemented`, `not_applicable`, or
  equivalent controlled value.
- `policy_status`: policy enforcement state.
- `adapter_gateway_status`: adapter/gateway behavior state.
- `encoding_status`: encoding and decode-to-JSON requirements.
- `conformance_status`: positive/negative fixture state.
- `ignorable_by_default`: boolean. Defaults to true except when a versioned
  subtype contract explicitly makes the field part of that subtype.
- `collision_rules`: rule text or references to namespace constraints.
- `security_release_notes`: trust, signing, release, or export implications.
- `migration_notes`: compatibility and deprecation notes.
- `references`: links to spec sections, schemas, issues, plans, or tests.
- `date_added`: ISO date.
- `review_state`: `draft`, `ready_for_review`, `approved`, `blocked`, or
  `deferred`.
- `supersedes`: list of older registry names.
- `superseded_by`: replacement name, if any.
- `notes`: additional constraints and open questions.

S1-03B should keep the machine-readable model strict enough for validation but
allow `notes` and `references` to carry explanatory detail.

## E. Status Definitions

- `reserved`: The name is held to prevent collision. It is not valid event
  vocabulary and must not appear in valid current events unless another already
  adopted branch defines the same concept.
- `proposed`: The concept has enough definition for review but is not yet valid
  vocabulary. It may have draft schema or policy text, but producers must not
  emit it as current ZMeta vocabulary.
- `experimental`: The concept is valid only in a named experimental or
  compatibility branch, such as v1.1.0, and only when that exact branch is
  selected by `zmeta_version`.
- `adopted`: The concept is valid in an approved version branch with semantic
  definition, schema or policy coverage where needed, adapter/gateway guidance,
  encoding notes, documentation, and conformance tests.
- `deprecated`: The concept remains valid for compatibility but should not be
  used for new producers. A migration path and removal horizon must be named.
- `rejected`: The concept was reviewed and should not be implemented. Producers
  must not emit it as valid vocabulary.
- `superseded`: The concept has been replaced by another registered concept.
  The record must name `superseded_by`.

Required rule: `reserved` and `proposed` entries must never be treated as valid
event vocabulary. A registry entry is not enough to make an event valid; validity
requires an approved version branch and the applicable schema, policy, adapter,
encoding, and conformance surfaces.

## F. Category Definitions

Initial category set:

- `observation_modality`: event subtype or payload modality vocabulary for
  OBSERVATION_EVENT.
- `observation_feature_contract`: modality-specific required and optional
  feature fields.
- `inference_type`: inference subtype or payload discriminator vocabulary.
- `fusion_extension`: track fusion, association, state-estimation, or
  multi-source continuity additions.
- `state_extension`: operator-facing state payload additions that do not carry
  raw observations.
- `command_task_type`: bounded command/tasking subtype or task payload contract.
- `system_status_type`: SYSTEM_EVENT subtype or system status payload contract.
- `profile_export_control`: profile, projection, thinning, redaction, omission,
  or export-control metadata.
- `trust_integrity`: signing, key identity, trust, anti-replay, spoof,
  quarantine, and route integrity concepts.
- `coalition_release`: releasability, markings, redaction, export audit, and
  cross-domain guard concepts.
- `ai_model_provenance`: model card, model package, runtime, drift, OOD,
  confidence decomposition, and assurance concepts.
- `pnt_integrity`: navigation integrity, jam/spoof suspicion, PNT source, and
  uncertainty concepts beyond v1.0 timing quality.
- `replay_test`: replay, synthetic, red-team, exercise, or test labels.
- `adapter_vendor_namespace`: vendor/private namespace definitions and allowed
  payload locations.
- `companion_artifact`: manifests, scorecards, replay bundles, adapter manifests,
  or artifacts referenced by events without becoming event payload bloat.
- `encoding_projection`: compact/protobuf/CBOR mapping extensions and wire
  compatibility concepts.
- `conformance_class`: named conformance claims and required test surfaces.

## G. Collision and Namespace Rules

Registry rules should be conservative:

- No extension may collide with v1.0 names.
- No extension may collide with v1.1.0 names unless it is the same registered
  concept in the same version lineage.
- Vendor extensions must use namespaced keys, such as `vendor.<name>.<field>` or
  another registry-approved prefix.
- Vendor extensions must be safe to ignore unless selected by a versioned
  subtype contract.
- No extension may alter the ZMeta envelope.
- No extension may collapse observation, inference, fusion, and state layers.
- No extension may redefine units, geodesy, timing, lineage, confidence,
  profile behavior, event identity, or authority boundaries.
- No extension may become valid without schema, policy, and conformance review
  when it changes structure or runtime behavior.
- Extension names must not encode release domain, trust state, emergency mode,
  or UI role into existing fields such as `profile`, `event_id`, or
  `event_subtype`.
- `additionalProperties: true` surfaces remain compatibility escape hatches,
  not adoption mechanisms. A schema-permitted free-form object does not make a
  field semantically registered.

## H. Adoption Requirements

Before an extension can move to `adopted`, it must have:

- Semantic definition.
- Approved version branch.
- Schema shape if structural.
- Policy rules if contextual.
- Adapter/gateway requirements.
- Encoding notes if wire behavior changes.
- Positive fixtures.
- Negative fixtures.
- Conformance class impact.
- Migration guidance.
- Release/security review where applicable.
- Documentation.
- Test command coverage.

Adoption should require evidence, not intent. A record should not become
`adopted` while schema, policy, gateway behavior, encoding guidance, or
conformance tests remain `planned` for any required surface.

## I. Initial Registry Population Plan

S1-03B should populate the registry without making new vocabulary valid. Initial
records should reflect what is already valid in existing branches and what is
only reserved for future branches.

### Group 1 - Existing v1.1.0 Experimental Extension Entries

Recommended status: `experimental`
Recommended `version_branch`: `"1.1.0"`

These are valid only when the current v1.1.0 schema branch is selected:

- Structured quality block.
- `error_ellipse_m`.
- Formal `data_ref` / `data_refs` behavior.
- Modality-specific feature contracts for EO, IR, ACOUSTIC, and NETWORK.
- `SENSOR_STATUS`.
- `PLATFORM_STATUS`.
- Expanded command task types:
  - `RETURN_TO_BASE`
  - `LAND`
  - `LOITER`
  - `SCAN_RF`
  - `TRACK_TARGET`
  - `CHANGE_SENSOR_MODE`

Inspection note: `schema/zmeta-event-1.1.0.schema.json`,
`schema/README.md`, examples, and schema tests agree on these entries. The
crosswalk currently mentions `TAKEOFF` in one expanded-task row, but the schema
does not define `TAKEOFF`. S1-03B should treat the schema and schema README as
authority unless a separate typo cleanup is approved.

### Group 2 - Reserved Observation Modality Candidates

Recommended status: `reserved`
Recommended `version_branch`: `null`

Not valid current OBSERVATION_EVENT vocabulary:

- `RADAR`
- `LIDAR`
- `MAGNETIC`
- `SEISMIC`
- `CYBER`
- `SIGINT`
- `ENVIRONMENTAL`
- `MARITIME`

`RADAR`, `LIDAR`, `MAGNETIC`, `SEISMIC`, `CYBER`, and `SIGINT` are already
documented and tested as rejected observation modalities. `ENVIRONMENTAL` and
`MARITIME` should be registered as reserved candidates if the project wants to
hold those names before feature contracts exist. `MARITIME` currently appears as
a v1.1.0 platform-type metric value, not as an observation modality.

### Group 3 - Reserved System/Status and Assurance Candidates

Recommended status: `reserved` or `proposed`
Recommended `version_branch`: `null`

Not valid current vocabulary:

- `PNT_STATUS`
- `MODEL_STATUS`
- `ASSURANCE_EVENT`
- `TRUST_STATUS`
- `QUARANTINE_STATUS`
- `RELEASE_STATUS`
- `EXPORT_AUDIT`
- `REPLAY_STATUS`

These names require careful category assignment because some are likely
SYSTEM_EVENT subtypes, while `ASSURANCE_EVENT` may imply a new event family or
an inference/system subtype. The registry should prevent either choice from
being assumed before version review.

### Group 4 - Reserved Trust, Identity, Release, and Replay Concepts

Recommended status: `reserved` or `proposed`
Recommended `version_branch`: `null`

Not valid current vocabulary:

- `EVENT_SIGNATURE`
- `KEY_IDENTITY`
- `ANTI_REPLAY_NONCE`
- `TRUST_SCORE`
- `MESH_ROUTE_TRUST`
- `SUSPECT_EVENT`
- `QUARANTINED_EVENT`
- `UAS_IDENTITY`
- `BEHAVIORAL_IDENTITY`
- `RELEASE_LABEL`
- `REDACTION_PROFILE`
- `DATA_NUTRITION_LABEL`
- `RAW_DATA_ABSENT_STATUS`
- `PROJECTION_METADATA`
- `EMERGENCY_L0_PROFILE`
- `REPLAY_LABEL`
- `SYNTHETIC_EVENT`
- `RED_TEAM_INJECTION`

These concepts must remain separate from confidence, profile, schema validity,
and ordinary source identity until adopted by a version branch.

### Group 5 - Reserved Track Lifecycle Concepts

Recommended status: `reserved` or `proposed`
Recommended `version_branch`: `null`

Not valid current vocabulary:

- `TRACK_NEW`
- `TRACK_ACTIVE`
- `TRACK_STALE`
- `TRACK_LOST`
- `TRACK_MERGED`
- `TRACK_SPLIT`
- `TRACK_RETIRED`

The registry should keep these from becoming ad hoc state or fusion labels.
Future adoption must define whether lifecycle is represented as fusion/state
payload extension, system status, companion track manifest, or a new versioned
subtype contract.

## J. Machine-Readable Registry Validation Plan

S1-03B should add registry validation that checks both record shape and semantic
governance.

Recommended checks:

- YAML or JSON Schema validation for registry record fields.
- Duplicate-name checks across all registry entries.
- Duplicate display name and alias checks where aliases are introduced.
- Status transition checks, such as prohibiting direct `reserved` to `adopted`
  without required surfaces.
- Version-branch checks:
  - `experimental` and `adopted` entries must name a branch.
  - `reserved` and `proposed` entries must not claim `introduced_in`.
  - exact branch values must match known schema branches unless intentionally
    future/planned.
- Collision checks against v1.0 and v1.1.0 schemas:
  - Event type enums.
  - Event subtype enums.
  - Payload discriminator enums.
  - Known task types, system types, observation modalities, profile labels,
    reason codes, and profile projection catalog paths.
- Tests proving `reserved` and `proposed` entries do not validate as event
  vocabulary.
- Tests proving existing v1.1.0 experimental entries validate only under
  `zmeta_version: "1.1.0"` when the schema supports them.
- Checks that every `adopted` structural extension has positive and negative
  conformance fixtures or an explicit non-structural policy-only rationale.
- Checks that encoding-affecting extensions name compact/protobuf/CBOR behavior
  or explicitly say no wire mapping change.

Recommended command for S1-03B:

```powershell
python tools\validate_extension_registry.py --registry spec\extension-registry.yaml
```

Future conformance runner integration should be explicit at first, for example:

```powershell
python tools\validate_conformance.py --strict --extension-registry
```

Do not make registry validation part of default `--strict` until the registry is
stable and maintainers decide it is a release gate.

## K. Documentation Integration Plan

Docs that should eventually reference the registry:

- `spec/semantics-contract.md`: cite the registry as the durable index of
  future candidates and adopted extensions, without changing the contract in
  S1-03A.
- `spec/versioning.md`: reference status transitions and version-branch
  requirements.
- `schema/README.md`: explain which schema branch owns which experimental or
  adopted extension vocabulary.
- `spec/profile-compatibility.md`: reference any profile/export-control
  extension records.
- `conformance/README.md`: document registry validation commands and fixture
  expectations after S1-03B.
- Future extension branch docs: require each branch to update registry entries
  as part of adoption.

S1-03A intentionally does not edit those docs except the running worklog and
handoff. S1-03B should perform the documentation integration after the registry
artifact exists.

## L. Implementation Plan for S1-03B

Recommended S1-03B file-by-file plan:

- `spec/extension-registry.md`: human-readable registry guide, status model,
  category model, collision rules, adoption requirements, and initial registry
  entries.
- `spec/extension-registry.yaml`: machine-readable initial registry populated
  with existing v1.1.0 experimental entries and reserved/proposed future
  concepts.
- `schema/extension-registry.schema.json`: optional strict schema for registry
  records if the validation tool should use JSON Schema.
- `tools/validate_extension_registry.py`: CLI that validates record shape,
  duplicate names, status rules, version branch rules, and collisions with
  current schemas.
- `gateway/tests/test_extension_registry.py`: tests for duplicate detection,
  reserved/proposed invalidity, v1.1.0 experimental branch isolation, and
  collision rules.
- `conformance/README.md`: add explicit registry validation command.
- `spec/README.md`: list the registry docs.
- `schema/README.md`: reference the registry for experimental and reserved
  vocabulary governance.
- `docs/zmeta_refinement_worklog.md`: mark S1-03B complete when implemented and
  update D-006 only after registry artifacts and validation exist.
- `docs/zmeta_refinement_handoff.md`: update the next work item and human
  decisions.

S1-03B should not adopt future concepts unless the prompt explicitly authorizes
schema, policy, adapter/gateway, encoding, and conformance changes for a named
version branch.

## M. Risks and Open Questions

Human review decisions before S1-03B:

- Should existing v1.1.0 concepts remain `experimental`, or should any become
  `adopted` in the registry? Recommended default: keep them `experimental`
  until a release/version decision promotes them.
- Should the machine-readable registry live under `spec/` or
  `conformance/`? Recommended default: `spec/extension-registry.yaml`, because
  it governs semantics rather than only tests.
- Should registry validation become part of strict conformance by default?
  Recommended default: opt-in until the registry format stabilizes.
- How should vendor/private namespace entries be represented? Recommended
  default: namespaced records with explicit owner and `ignorable_by_default:
  true`.
- How should classified or restricted extension names be handled? Recommended
  default: allow opaque namespaced placeholders that reserve collisions without
  revealing sensitive definitions.
- Should companion artifacts be a registry category or a separate manifest?
  Recommended default: start with `companion_artifact` category, then split to a
  dedicated manifest if records become too artifact-specific.
- Should `ENVIRONMENTAL` and `MARITIME` be reserved as observation modality
  names immediately? Recommended default: yes, as reserved candidates, while
  noting that `MARITIME` already appears as a platform type metric value.
- Should the crosswalk's `TAKEOFF` mention be corrected before S1-03B?
  Recommended default: treat it as a documentation cleanup, not a schema or
  registry adoption item.

## Files Inspected

- `spec/semantics-contract.md`
- `schema/README.md`
- `schema/zmeta-event.schema.json`
- `schema/zmeta-event-1.0.schema.json`
- `schema/zmeta-event-1.1.0.schema.json`
- `spec/versioning.md`
- `spec/profile-compatibility.md`
- `spec/profile-projection-field-catalog.md`
- `spec/compact-binary-mapping.md`
- `spec/protobuf-encoding.md`
- `docs/zmeta_semantic_contract_lockdown_audit.md`
- `docs/zmeta_contract_to_stack_crosswalk.md`
- `docs/s1_01_v1_baseline_verification_plan.md`
- `docs/s1_02_profile_projection_preservation_plan.md`
- `docs/s1_02c_projection_preservation_audit.md`
- `docs/zmeta_refinement_worklog.md`
- `docs/zmeta_refinement_handoff.md`
- `conformance/README.md`
- `conformance/profile_projection_field_catalog.yaml`
- `examples/README.md`
- `examples/zmeta-v1.1-examples.jsonl`
- `gateway/tests/test_schema_version_discrimination.py`

## Final Recommendation

Proceed to S1-03B - Extension Registry Implementation. Implement the human and
machine-readable registry, validation CLI, tests, and documentation references,
but keep future concepts reserved/proposed unless a separate versioned schema
branch task explicitly adopts them.
