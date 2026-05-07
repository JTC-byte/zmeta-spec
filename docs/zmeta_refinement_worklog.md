# ZMeta Refinement Worklog

## Current Resume Note

- Last updated: 2026-05-07
- Quick handoff: `docs/zmeta_refinement_handoff.md`
- Current next work item: S1-03C - Extension Registry Post-Implementation
  Audit.
- Current decision: S1-03B implemented the extension registry as spec-owned
  human and machine-readable artifacts with standalone validation, tests, and
  optional conformance runner integration. v1.1.0 concepts remain
  experimental, future concepts remain reserved/proposed, and no schemas,
  semantic contract text, examples, fixtures, adapters, encodings, or event
  vocabulary were changed.

## S0-01 - Semantic Contract Lockdown Audit

- Status: COMPLETE
- Date completed: 2026-05-07
- Output: `docs/zmeta_semantic_contract_lockdown_audit.md`
- Scope: Audited the current semantic contract against schemas, policy packs,
  encoding specs, adapters, examples, conformance files, and gateway validation
  surfaces.
- Notes: Documentation-only task. No schemas, adapters, protobuf files, compact
  mappings, validators, policy packs, examples, or tests were modified.

## S0-02 - Semantic Contract Rewrite and Hardening

- Status: COMPLETE
- Date completed: 2026-05-07
- Output: `spec/semantics-contract.md`
- Scope: Rewrote the primary semantic contract as the authoritative north-star
  document for v1.0 locked semantics, v1.1.0 compatibility extensions, future
  candidates, enforcement surfaces, edge AI provenance, raw-data-absent mode,
  compute and bandwidth degradation, mesh trust, UAS identity, coalition export,
  data nutrition labels, extension governance, conformance classes, and
  implementation mapping.
- Notes: Contract-only task. No JSON schemas, adapters, code, protobuf files,
  compact mappings, validators, policy packs, examples, or tests were modified.

## S0-03 - Contract-to-Stack Crosswalk

- Status: COMPLETE
- Date completed: 2026-05-07
- Output: `docs/zmeta_contract_to_stack_crosswalk.md`
- Scope: Crosswalked the hardened semantic contract against the canonical
  dispatcher schema, v1.0 schema, v1.1.0 schema, policy pack, reference gateway,
  validation CLIs, compact CBOR mapping, protobuf projection, CoT/JREAP-style
  adapters, examples, and conformance tests.
- Notes: Documentation-only task. No JSON schemas, adapters, code, protobuf
  files, compact mappings, validators, policy packs, examples, or tests were
  modified.

## S1-01A - v1.0 Baseline Verification and Targeted Schema Gap Plan

- Status: COMPLETE
- Date completed: 2026-05-07
- Output: `docs/s1_01_v1_baseline_verification_plan.md`
- Scope: Verified the locked v1.0 schema, policy, gateway, adapter, encoding,
  example, and conformance baseline against the hardened semantic contract and
  S0-03 crosswalk.
- Decision: No targeted v1.0 schema implementation task is needed. S1-01B is
  not opened. Proceed directly to S1-02.
- Verification: Ran `python tools\validate_conformance.py --strict`; result was
  `conformance ok`.
- Notes: Documentation-only task. No JSON schemas, adapters, code, protobuf
  files, compact mappings, validators, policy packs, examples, tests, semantic
  contract text, or release hashes were modified.

## S1-02 - Profile Projection Preservation Field Catalog and Conformance Suite

- Status: COMPLETE
- Scope: Define H/M/L projection field catalog and conformance fixtures proving
  projection preservation: same event identity where required, no confidence or
  TTL increase, no precision increase, no unit changes, allowed optional field
  omissions only, source-authored fields not rewritten, lineage preserved or
  unresolved according to profile policy, and Profile L compact expansion
  equivalence.
- Notes: S1-02A planning, S1-02B implementation, and S1-02C audit are complete.

## S1-02A - Profile Projection Preservation Field Catalog and Conformance Plan

- Status: COMPLETE
- Date completed: 2026-05-07
- Output: `docs/s1_02_profile_projection_preservation_plan.md`
- Scope: Planned a Profile L/M/H projection preservation system that uses a
  field catalog and pairwise conformance fixtures to prove profile thinning
  preserves identity, source, lineage, units, semantic layer, confidence
  monotonicity, TTL monotonicity, timing exposure, and compact expansion
  equivalence.
- Decision: Do not change v1.0 schemas for projection preservation. Use a
  sidecar field catalog and source/projected fixture pairs so v1.0 remains
  locked while conformance proves profile meaning preservation.
- Notes: Documentation-only task. No JSON schemas, adapters, code, protobuf
  files, compact mappings, validators, policy packs, examples, tests, semantic
  contract text, or release hashes were modified.

## S1-02B - Profile Projection Preservation Field Catalog and Conformance Suite Implementation

- Status: COMPLETE
- Date completed: 2026-05-07
- Scope: Add the projection field catalog, source/projected conformance fixture
  format, projection validator, positive and negative projection fixtures,
  gateway/tool tests, and compact/protobuf decoded-equivalence tests.
- Outputs:
  - `conformance/profile_projection_field_catalog.yaml`
  - `spec/profile-projection-field-catalog.md`
  - `conformance/profile-projection/README.md`
  - `conformance/profile-projection/must-pass.jsonl`
  - `conformance/profile-projection/must-fail.jsonl`
  - `conformance/profile-projection/context.jsonl`
  - `tools/validate_projection.py`
  - `gateway/tests/test_profile_projection_preservation.py`
  - `gateway/tests/test_profile_projection_encoding.py`
- Integration: `tools/validate_conformance.py --profile-projection` runs the
  projection suite explicitly without changing default strict conformance
  behavior.
- Verification:
  - `python tools\validate_conformance.py --strict` -> `conformance ok`
  - `python tools\validate_conformance.py --strict --profile-projection` ->
    `projection conformance ok total=33`, `conformance ok`
  - `python tools\validate_projection.py --catalog conformance\profile_projection_field_catalog.yaml --must-pass conformance\profile-projection\must-pass.jsonl --must-fail conformance\profile-projection\must-fail.jsonl --quiet` ->
    `projection conformance ok total=33`
  - `python -m pytest` -> `241 passed`
- Notes: v1.0 schema, v1.0 vocabulary, and semantic contract text were not
  changed.

## S1-02C - Post-Implementation Audit and Cleanup

- Status: COMPLETE
- Date completed: 2026-05-07
- Output: `docs/s1_02c_projection_preservation_audit.md`
- Scope: Audit the S1-02B implementation for fixture breadth, field catalog
  clarity, projection validator edge cases, optional omission coverage, and
  documentation consistency before moving into broader backlog cleanup.
- Cleanup:
  - `tools/validate_projection.py` now fails explicitly when a fixture file is
    missing instead of silently skipping it.
  - `gateway/tests/test_profile_projection_preservation.py` covers the missing
    fixture failure path.
  - `conformance/profile-projection/README.md` documents stable projection
    failure codes and clarifies `PROJECTION_FIELD_CHANGED` as a fallback.
- Verification:
  - `python tools\validate_conformance.py --strict` -> `conformance ok`
  - `python tools\validate_conformance.py --strict --profile-projection` ->
    `projection conformance ok total=33`, `conformance ok`
  - `python tools\validate_projection.py --catalog conformance\profile_projection_field_catalog.yaml --must-pass conformance\profile-projection\must-pass.jsonl --must-fail conformance\profile-projection\must-fail.jsonl --quiet` ->
    `projection conformance ok total=33`
  - `python -m pytest -q gateway\tests\test_profile_projection_preservation.py gateway\tests\test_profile_projection_encoding.py` ->
    `11 passed`
  - `python -m pytest` -> `242 passed`
  - `git diff --check` -> passed with CRLF conversion warnings only.
- Decision: S1-02B is verified. D-005 remains closed. D-007 remains partially
  covered, not closed. D-010 added for Profile M/L precision floors.

## S1-03A - Extension Registry Plan Only

- Status: COMPLETE
- Date completed: 2026-05-07
- Output: `docs/s1_03_extension_registry_plan.md`
- Scope: Planned a durable extension registry artifact with status, ownership,
  collision rules, reserved-name governance, adoption requirements, initial
  population groups, and machine-readable validation expectations.
- Recommended artifact paths:
  - `spec/extension-registry.md`
  - `spec/extension-registry.yaml`
  - `tools/validate_extension_registry.py`
  - `gateway/tests/test_extension_registry.py`
- Decision: Existing v1.1.0 concepts should be treated as `experimental` by
  default until a version/release decision promotes them. Future trust, signing,
  release, replay, PNT, UAS identity, data nutrition, projection metadata,
  emergency/L0, and track lifecycle concepts remain reserved/proposed and are
  not valid current event vocabulary.
- Notes: Planning only. No schemas, validators, adapters, encodings, policy
  packs, examples, fixtures, semantic contract text, release hashes, or event
  vocabulary were changed.

## S1-03B - Extension Registry Implementation

- Status: IMPLEMENTED - PENDING S1-03C AUDIT
- Date completed: 2026-05-07
- Scope: Implemented the human-readable and machine-readable extension
  registry, registry validation CLI, tests, and optional conformance runner
  integration using the S1-03A plan.
- Outputs:
  - `spec/extension-registry.md`
  - `spec/extension-registry.yaml`
  - `tools/validate_extension_registry.py`
  - `gateway/tests/test_extension_registry.py`
- Integration: `tools/validate_conformance.py --extension-registry` runs the
  extension registry validator explicitly without changing default strict
  conformance behavior.
- Decisions:
  - Existing v1.1.0 concepts are recorded as `experimental`, not `adopted`.
  - Future concepts are recorded as `reserved` or `proposed` and remain invalid
    current event vocabulary.
  - Registry validation is opt-in for conformance.
  - No schema, semantic contract, adapter, encoding, example, fixture, policy,
    or event-vocabulary changes were made.
- Verification:
  - `python tools\validate_extension_registry.py --registry spec\extension-registry.yaml` ->
    `extension registry ok entries=63`
  - `python tools\validate_conformance.py --strict` -> `conformance ok`
  - `python tools\validate_conformance.py --strict --profile-projection` ->
    `projection conformance ok total=33`, `conformance ok`
  - `python tools\validate_conformance.py --strict --profile-projection --extension-registry` ->
    `projection conformance ok total=33`, `extension registry ok entries=63`,
    `conformance ok`
  - `python -m pytest -q gateway\tests\test_extension_registry.py` ->
    `11 passed`
  - `python -m pytest` -> `253 passed`
  - `git diff --check` -> passed with CRLF conversion warnings only.

## S1-03C - Extension Registry Post-Implementation Audit

- Status: PENDING
- Scope: Audit the S1-03B implementation for registry correctness, validation
  coverage, docs alignment, schema/contract non-drift, and reserved/proposed
  vocabulary isolation.
- Notes: Audit only. Do not promote experimental entries or make reserved future
  concepts valid.

## S1-04A - Conformance Class Manifest Plan Only

- Status: FUTURE / PENDING
- Scope: Plan a machine-readable conformance class manifest and claim/test
  matrix for ZMETA-CORE, ZMETA-PROFILE-L/M/H, ZMETA-ADAPTER, ZMETA-GATEWAY,
  ZMETA-COT-PROJECTION, ZMETA-AI-PROVENANCE, ZMETA-COALITION-EXPORT,
  ZMETA-MESH-TRUST, and ZMETA-REPLAY.
- Notes: Plan only. Do not implement conformance class artifacts until S1-03B is
  complete or maintainers explicitly reprioritize the work.

## Deferred Issue Register

### D-001 - MAVLink Adapter README State Payload Drift

- Status: OPEN
- Discovered during: S0-01 / S0-02 review
- Issue: `adapters/ingress/mavlink/README.md` describes several platform-state
  telemetry values as mapping to `payload.features.*`, while STATE_EVENT
  semantics prohibit raw `features` and the current implementation uses
  quality-style metadata.
- Impact: Documentation drift can encourage future adapter authors to place raw
  telemetry features in STATE_EVENT payloads.
- Proposed follow-up: Docs/adapter cleanup task. Do not change during S0-02
  because this work item is semantic-contract-only.

### D-002 - Contract Hash / Release Hash Follow-Up

- Status: OPEN
- Discovered during: S0-02
- Issue: Rewriting `spec/semantics-contract.md` changes the normative contract
  hash used by gateway/deployment hash gates.
- Impact: Deployments with `require_contract_hash` or release validation assets
  will need an intentional hash update in a later release task.
- Proposed follow-up: Recompute contract hashes and update release/checklist
  artifacts only when the stack-hardening branch is ready.

### D-003 - Future Semantics Require Versioned Implementation Branches

- Status: OPEN
- Discovered during: S0-02
- Issue: The rewritten contract defines future candidates for markings,
  integrity, anti-replay, trust, MODEL_STATUS/ASSURANCE_EVENT, PNT integrity,
  UAS identity, coalition export, projection metadata, data nutrition labels,
  and emergency/L0 behavior.
- Impact: These concepts are intentionally not valid event vocabulary yet.
- Proposed follow-up: Create dedicated versioned prompts for schema, policy,
  adapter/gateway, encoding, examples, and conformance implementation after
  approval of each extension branch.

### D-004 - Companion Artifact Set Needed

- Status: OPEN
- Discovered during: S0-02 research review alignment
- Issue: Vendor-neutral scorecards, replay bundle manifests, adapter manifests,
  data-rights/IP governance, DevSecOps evidence, lessons-learned graphs, and
  TTP/training materials are important but should not bloat core ZMeta events.
- Impact: Without companion artifacts, ZMeta may be semantically strong but
  operationally harder to certify and migrate.
- Proposed follow-up: Define a companion artifact roadmap and decide which
  artifacts need stable IDs referenced by future ZMeta events.

### D-005 - Profile Projection Preservation Coverage Gap

- Status: CLOSED
- Discovered during: S0-03
- Issue: The stack enforces profile event-type legality and supports optional
  field stripping, compact Profile L encoding, and timing-based confidence
  degradation, but there is not yet a conformance suite proving that H/M/L
  projections preserve identity, lineage, units, confidence monotonicity, TTL,
  and semantic meaning across thinning.
- Impact: Profile L/M/H exporters could accidentally pass schema validation
  while still reinterpreting or over-trusting thinned state.
- Resolution: S1-02B added a sidecar field catalog, source/projected projection
  fixtures, standalone validator CLI, compact/protobuf decoded-equivalence
  fixture coverage, opt-in conformance runner integration, and regression tests.
- Audit: S1-02C verified fixture breadth, validator behavior, failure code
  stability, docs alignment, and absence of schema/contract drift.

### D-006 - Extension Registry Artifact Missing

- Status: OPEN - IMPLEMENTED PENDING S1-03C AUDIT
- Discovered during: S0-03
- Issue: The contract and schema README reserve future subtype and modality
  names by prose, but the repository does not yet contain a durable extension
  registry artifact with status, ownership, collision rules, and adoption
  requirements.
- Impact: Future prompts could add extension vocabulary inconsistently or make
  reserved names appear valid before a version branch is approved.
- S1-03A coverage: Planned `spec/extension-registry.md`,
  `spec/extension-registry.yaml`, validation tooling, initial entries, status
  model, category model, collision rules, and adoption requirements.
- S1-03B coverage: Implemented the human-readable registry, machine-readable
  registry, validator CLI, optional conformance flag, tests, and docs
  integration. Existing v1.1.0 entries are experimental; future entries are
  reserved/proposed.
- Proposed follow-up: Run S1-03C audit before fully closing D-006.

### D-007 - Encoding Negative Validation Gap

- Status: OPEN - PARTIALLY COVERED BY S1-02B/S1-02C
- Discovered during: S0-03
- Issue: Compact and protobuf roundtrip coverage exists, and the gateway
  decodes binary encodings before validation, but there are not explicit
  invalid-after-decode fixtures for compact and protobuf inputs.
- Impact: The "encoding is not semantic authority" rule is harder to regression
  test across future encoding changes.
- S1-02B coverage: Added compact/protobuf projection fixtures where decoded JSON
  is schema-valid but projection-invalid, proving encoding does not override
  projection semantics.
- S1-02C audit: Confirmed compact/protobuf remain encoding projections only and
  decoded JSON is the validation authority.
- Remaining follow-up: Add broader gateway/CLI negative tests that encode
  schema-invalid or policy-invalid events, decode them, and prove schema/policy
  validation rejects them outside the projection-pair fixture path.

### D-008 - Conformance Class Manifest Missing

- Status: OPEN
- Discovered during: S0-03
- Issue: The semantic contract defines ZMETA-CORE, ZMETA-PROFILE-L/M/H,
  ZMETA-ADAPTER, ZMETA-GATEWAY, ZMETA-COT-PROJECTION,
  ZMETA-AI-PROVENANCE, ZMETA-COALITION-EXPORT, ZMETA-MESH-TRUST, and
  ZMETA-REPLAY classes, but the repo does not yet provide a machine-readable
  class claim/test matrix.
- Impact: Implementations can run tests, but they cannot yet make precise,
  repeatable conformance claims by class.
- Proposed follow-up: Add a conformance class manifest and map each class to
  required schema, policy, adapter, encoding, and test suites.

### D-009 - v1.0/v1.1 Observation Extension Boundary Needs Explicit Tests

- Status: OPEN
- Discovered during: S1-01A
- Issue: v1.0 intentionally allows EO, IR, ACOUSTIC, and NETWORK observation
  subtype names with generic `features`, and also allows generic `quality`,
  `data_ref`, and `data_refs` structures. v1.1.0 formalizes stricter feature,
  quality, and data-reference contracts for some of those same field names.
- Impact: Integrators may confuse "structurally valid generic v1.0 extension"
  with "semantically adopted v1.1.0 feature contract" unless tests/docs make the
  boundary explicit.
- Proposed follow-up: Add boundary documentation/tests during extension registry
  or conformance-class work. Do not treat this as a v1.0 schema defect.

### D-010 - Profile Precision / Quantization Policy Floors

- Status: OPEN
- Discovered during: S1-02C
- Issue: S1-02B enforces precision non-increase for profile projection, but it
  does not define operational precision floors or quantization requirements for
  Profile M/L by field, mission, or packet budget.
- Impact: Projection conformance prevents invented precision, but exporters do
  not yet have a normative target for how coarse Profile M/L latitude,
  longitude, altitude, heading, speed, bearing, RF metrics, or timing values
  should become under specific operational budgets.
- Proposed follow-up: Define mission/profile-specific quantization floors and
  packet-budget policy after representative Profile L/M traffic and operational
  requirements are available.

### D-011 - Crosswalk TAKEOFF Mention Cleanup

- Status: OPEN
- Discovered during: S1-03A / S1-03B registry planning and implementation
- Issue: `docs/zmeta_contract_to_stack_crosswalk.md` mentions `TAKEOFF` in one
  v1.1.0 expanded-tasking row, but the v1.1.0 schema, schema README, examples,
  tests, and extension registry do not define `TAKEOFF`.
- Impact: The typo could confuse future tasking-extension prompts into treating
  `TAKEOFF` as existing or planned vocabulary.
- Proposed follow-up: Clean up the crosswalk row in a narrow docs task or
  during S1-03C audit if maintainers want audit cleanup to include confirmed
  typo fixes. Do not add `TAKEOFF` to current schemas or registry unless a
  future versioned task explicitly proposes it.
