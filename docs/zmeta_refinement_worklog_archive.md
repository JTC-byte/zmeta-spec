# ZMeta Refinement Worklog Archive

Completed task sections archived from `docs/zmeta_refinement_worklog.md` per the
release-checklist retention pass. Append-move only: sections are moved here
verbatim once no longer current operating context. The active worklog keeps the
Current Resume Note, recent sessions, and the Deferred Issue Register.

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

- Status: COMPLETE
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

- Status: COMPLETE
- Date completed: 2026-05-07
- Output: `docs/s1_03c_extension_registry_audit.md`
- Scope: Audit the S1-03B implementation for registry correctness, validation
  coverage, docs alignment, schema/contract non-drift, and reserved/proposed
  vocabulary isolation.
- Cleanup:
  - `tools/validate_extension_registry.py` now checks unregistered reserved
    schema values, currently `TAKEOFF`, so the crosswalk stray mention cannot
    become current schema vocabulary unnoticed.
  - `gateway/tests/test_extension_registry.py` covers `TAKEOFF` invalidity under
    v1.0/v1.1.0 and the new schema leakage failure.
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
    `12 passed`
  - `python -m pytest` -> `254 passed`
  - `git diff --check` -> passed with CRLF conversion warnings only.
- Decision: S1-03B is verified. D-006 is closed. D-007 remains partially
  covered, not closed. D-010 and D-011 remain open.

## S1-04A - Conformance Class Manifest Plan Only

- Status: COMPLETE
- Date completed: 2026-05-07
- Output: `docs/s1_04_conformance_class_manifest_plan.md`
- Scope: Plan a machine-readable conformance class manifest and claim/test
  matrix for ZMETA-CORE, ZMETA-PROFILE-L/M/H, ZMETA-ADAPTER, ZMETA-GATEWAY,
  ZMETA-COT-PROJECTION, ZMETA-AI-PROVENANCE, ZMETA-COALITION-EXPORT,
  ZMETA-MESH-TRUST, and ZMETA-REPLAY.
- Recommended artifact paths:
  - `spec/conformance-classes.md`
  - `conformance/conformance_classes.yaml`
  - `conformance/claims/example-reference-gateway.yaml`
  - `conformance/claims/example-core-producer.yaml`
  - `tools/validate_conformance_classes.py`
  - `gateway/tests/test_conformance_classes.py`
- Decisions:
  - Conformance classes organize implementation claims and evidence; they do not
    create semantics.
  - Current classes should default to `implemented` in S1-04B unless maintainers
    explicitly promote them to externally claimable `active`.
  - Future/reserved classes cannot be claimed by current implementations.
  - Claims must record test commands, results, supported ZMeta versions,
    registry/catalog versions, commit hash, and limitations.
- Notes: Planning only. No manifest, claim examples, validators, tests, schemas,
  adapters, encodings, policy files, examples, semantic contract text, extension
  registry entries, release hashes, or event vocabulary were changed.
- Verification:
  - `python tools\validate_conformance.py --strict` -> `conformance ok`
  - `python tools\validate_conformance.py --strict --profile-projection` ->
    `projection conformance ok total=33`, `conformance ok`
  - `python tools\validate_conformance.py --strict --profile-projection --extension-registry` ->
    `projection conformance ok total=33`, `extension registry ok entries=63`,
    `conformance ok`
  - `python -m pytest` -> `254 passed`
  - `git diff --check` -> passed with CRLF conversion warnings only.

## S1-04B - Conformance Class Manifest Implementation

- Status: COMPLETE
- Date completed: 2026-05-07
- Scope: Implemented the human-readable conformance class specification,
  machine-readable class manifest, example claim files, standalone class
  validator, focused tests, optional conformance runner integration, and docs.
- Outputs:
  - `spec/conformance-classes.md`
  - `conformance/conformance_classes.yaml`
  - `conformance/claims/example-reference-gateway.yaml`
  - `conformance/claims/example-core-producer.yaml`
  - `tools/validate_conformance_classes.py`
  - `gateway/tests/test_conformance_classes.py`
- Integration: `tools/validate_conformance.py --conformance-classes` validates
  the class manifest and example claims explicitly without changing default
  strict conformance behavior.
- Decisions:
  - Class records organize implementation claims and evidence; they do not
    create semantics or make future vocabulary valid.
  - Current implemented classes use `implemented`; `ZMETA-COT-PROJECTION` is
    `partially_implemented` pending a shared adapter conformance harness.
  - Future, reserved, and planned classes are not claimable by current example
    claim files.
  - D-002 remains open; example claim files record `contract_hash:
    pending_D-002`.
  - No schema, semantic contract, adapter, encoding, policy, extension registry,
    example event vocabulary, release hash, or event-vocabulary changes were
    made.
- Verification:
  - `python tools\validate_conformance_classes.py --manifest conformance\conformance_classes.yaml` ->
    `conformance classes ok classes=30 claims=0`
  - `python tools\validate_conformance_classes.py --manifest conformance\conformance_classes.yaml --claims conformance\claims\example-reference-gateway.yaml conformance\claims\example-core-producer.yaml` ->
    `conformance classes ok classes=30 claims=2`
  - `python -m pytest -q gateway\tests\test_conformance_classes.py` ->
    `19 passed` after S1-04C audit cleanup
  - `python tools\validate_conformance.py --strict` -> `conformance ok`
  - `python tools\validate_conformance.py --strict --profile-projection` ->
    `projection conformance ok total=33`, `conformance ok`
  - `python tools\validate_conformance.py --strict --profile-projection --extension-registry` ->
    `projection conformance ok total=33`, `extension registry ok entries=63`,
    `conformance ok`
  - `python tools\validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes` ->
    `projection conformance ok total=33`, `extension registry ok entries=63`,
    `conformance classes ok classes=30 claims=2`, `conformance ok`
  - `python -m pytest` -> `269 passed`
  - `git diff --check` -> passed with CRLF conversion warnings only.

## S1-04C - Conformance Class Manifest Post-Implementation Audit

- Status: COMPLETE
- Date completed: 2026-05-07
- Output: `docs/s1_04c_conformance_class_manifest_audit.md`
- Scope: Audit S1-04B for class record correctness, claim validation behavior,
  docs alignment, schema/contract non-drift, and future/reserved class
  non-claimability.
- Cleanup:
  - `gateway/tests/test_conformance_classes.py` now covers dependency cycle
    rejection, partial-class full-claim rejection, failed required test-result
    rejection, and optional `--conformance-classes` conformance runner success.
- Verification:
  - `python tools\validate_conformance_classes.py --manifest conformance\conformance_classes.yaml` ->
    `conformance classes ok classes=30 claims=0`
  - `python tools\validate_conformance_classes.py --manifest conformance\conformance_classes.yaml --claims conformance\claims\example-reference-gateway.yaml conformance\claims\example-core-producer.yaml` ->
    `conformance classes ok classes=30 claims=2`
  - `python tools\validate_conformance.py --strict` -> `conformance ok`
  - `python tools\validate_conformance.py --strict --profile-projection` ->
    `projection conformance ok total=33`, `conformance ok`
  - `python tools\validate_conformance.py --strict --profile-projection --extension-registry` ->
    `projection conformance ok total=33`, `extension registry ok entries=63`,
    `conformance ok`
  - `python tools\validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes` ->
    `projection conformance ok total=33`, `extension registry ok entries=63`,
    `conformance classes ok classes=30 claims=2`, `conformance ok`
  - `python -m pytest -q gateway\tests\test_conformance_classes.py` ->
    `19 passed`
  - `python -m pytest` -> `273 passed`
  - `git diff --check` -> passed with CRLF conversion warnings only.
- Decision: S1-04B is verified. D-008 is closed. D-007 remains partially
  covered, not closed. D-010, D-011, and D-002 remain open.

## S1-05A - Encoding Negative Validation Plan Only

- Status: COMPLETE
- Date completed: 2026-05-07
- Output: `docs/s1_05_encoding_negative_validation_plan.md`
- Scope: Plan broader compact/protobuf gateway and CLI invalid-after-decode
  negative tests for D-007.
- Plan summary:
  - Separates decode-level, decoded schema-invalid, decoded policy-invalid,
    decoded projection-invalid, and gateway/CLI path rejection categories.
  - Recommends `conformance/encoding-negative/` JSONL fixtures with short
    malformed bytes as hex/base64 and generated-at-test-time encoded events for
    semantic failures.
  - Recommends standalone `tools/validate_encoding_negative.py`, optional
    `tools/validate_conformance.py --encoding-negative`, and focused
    compact/protobuf/gateway pytest coverage.
  - Preserves compact/protobuf as encoding projections only; decoded canonical
    JSON remains authoritative.
- Verification:
  - `python tools\validate_conformance.py --strict` -> `conformance ok`
  - `python tools\validate_conformance.py --strict --profile-projection`
    -> `projection conformance ok total=33`, `conformance ok`
  - `python tools\validate_conformance.py --strict --profile-projection --extension-registry`
    -> `projection conformance ok total=33`, `extension registry ok entries=63`,
    `conformance ok`
  - `python tools\validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes`
    -> `projection conformance ok total=33`, `extension registry ok entries=63`,
    `conformance classes ok classes=30 claims=2`, `conformance ok`
  - `python -m pytest` -> `273 passed`
  - `git diff --check` -> passed with CRLF conversion warnings only.
- Decision: Plan only. D-007 remains open until S1-05B implements the
  encoding-negative suite and S1-05C audits it.

## S1-05B - Encoding Negative Validation Implementation

- Status: COMPLETE
- Date completed: 2026-05-07
- Output:
  - `conformance/encoding-negative/README.md`
  - `conformance/encoding-negative/compact-must-fail.jsonl`
  - `conformance/encoding-negative/protobuf-must-fail.jsonl`
  - `conformance/encoding-negative/gateway-must-fail.jsonl`
  - `conformance/encoding-negative/context.jsonl`
  - `tools/validate_encoding_negative.py`
  - `gateway/tests/test_encoding_negative_validation.py`
  - `gateway/tests/test_compact_negative_decode.py`
  - `gateway/tests/test_protobuf_negative_decode.py`
- Scope: Implement compact/protobuf invalid-after-decode fixture suites,
  standalone validator CLI, optional conformance runner flag, and focused
  gateway/CLI/codec negative tests.
- Coverage:
  - Decode-level compact/protobuf failures, including malformed CBOR/protobuf,
    unsupported compact version, compact shape/enum/UUID errors, protobuf field
    and wire-type errors, payload size/depth/UTF-8 errors, and payload-not-object
    checks.
  - Decoded schema-invalid compact/protobuf cases, including UUIDv4, non-UTC
    timestamp, missing required fields, Profile L illegal event types, v1.1-only
    `SENSOR_STATUS` under v1.0, and reserved/future vocabulary.
  - Decoded policy-invalid cases for producer authority, command origin, and
    lineage parent type mismatch with fixture context.
  - Decoded projection-invalid compact/protobuf pairs using the existing
    projection preservation validator semantics.
  - Gateway and conversion/validation path cases for explicit compact/proto and
    stable `auto` detection cases.
  - Optional `tools/validate_conformance.py --encoding-negative` integration.
  - `ZMETA-COMPACT-CBOR` and `ZMETA-PROTOBUF-PROJECTION` evidence now references
    the encoding-negative validator command; no new conformance class was added.
- Audit: S1-05C verified fixture breadth, validator behavior, gateway/CLI
  parity, conformance-class evidence, and absence of schema/contract/registry
  drift. D-007 is closed.

## S1-05C - Encoding Negative Validation Post-Implementation Audit

- Status: COMPLETE
- Date completed: 2026-05-07
- Output: `docs/s1_05c_encoding_negative_validation_audit.md`
- Scope: Audited S1-05B for decoded validation authority, gateway/CLI parity,
  fixture quality, conformance integration, conformance-class evidence, and
  absence of schema/contract/registry drift.
- Coverage verified:
  - 49 encoding-negative fixtures: 20 compact, 21 protobuf, and 8 gateway/CLI.
  - Decode-level compact/protobuf rejection.
  - Decoded schema-invalid compact/protobuf rejection.
  - Stable decoded policy-invalid rejection for producer authority, command
    origin, and lineage parent type mismatch.
  - Decoded projection-invalid compact/protobuf pairs routed through the
    projection validator after canonical decode.
  - Explicit compact/proto gateway rejection, conversion/validation rejection,
    and stable auto-detection rejection.
  - Optional `tools/validate_conformance.py --encoding-negative` integration.
- Verification:
  - `python tools\validate_encoding_negative.py --compact conformance\encoding-negative\compact-must-fail.jsonl --protobuf conformance\encoding-negative\protobuf-must-fail.jsonl --gateway conformance\encoding-negative\gateway-must-fail.jsonl` ->
    `encoding negative ok total=49`
  - `python tools\validate_conformance.py --strict` -> `conformance ok`
  - `python tools\validate_conformance.py --strict --profile-projection` ->
    `projection conformance ok total=33`, `conformance ok`
  - `python tools\validate_conformance.py --strict --profile-projection --extension-registry` ->
    `projection conformance ok total=33`, `extension registry ok entries=63`,
    `conformance ok`
  - `python tools\validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes` ->
    `projection conformance ok total=33`, `extension registry ok entries=63`,
    `conformance classes ok classes=30 claims=2`, `conformance ok`
  - `python tools\validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative` ->
    `projection conformance ok total=33`, `extension registry ok entries=63`,
    `conformance classes ok classes=30 claims=2`,
    `encoding negative ok total=49`, `conformance ok`
  - `python tools\validate_conformance_classes.py --manifest conformance\conformance_classes.yaml` ->
    `conformance classes ok classes=30 claims=0`
  - `python tools\validate_conformance_classes.py --manifest conformance\conformance_classes.yaml --claims conformance\claims\example-reference-gateway.yaml conformance\claims\example-core-producer.yaml` ->
    `conformance classes ok classes=30 claims=2`
  - `python -m pytest -q gateway\tests\test_encoding_negative_validation.py gateway\tests\test_compact_negative_decode.py gateway\tests\test_protobuf_negative_decode.py` ->
    `22 passed`
  - `python -m pytest` -> `295 passed`
  - `git diff --check` -> passed with CRLF conversion warnings only.
- Decision: S1-05B is verified. D-007 is closed. D-010, D-011, and D-002 remain
  open.

## S1-06A - Profile Precision / Quantization Policy Floors Plan Only

- Status: COMPLETE
- Date completed: 2026-05-07
- Output: `docs/s1_06_profile_precision_quantization_policy_plan.md`
- Scope: Planned mission/profile-specific precision ceilings, utility floors,
  quantization steps, conservative rounding directions, packet-budget
  interaction, projection-validator interaction, gateway/exporter behavior,
  fixtures, standalone validator, and optional conformance integration for
  Profile L/M/H exports.
- Plan summary:
  - Precision policy remains profile/export policy, not a schema change.
  - Candidate artifacts: `spec/profile-precision-policy.md`,
    `policy/profile-precision.yaml`, `conformance/profile-precision/`,
    `tools/validate_precision_policy.py`, and
    `gateway/tests/test_profile_precision_policy.py`.
  - Candidate policy covers immutable identity/source/lineage fields,
    optional metadata, geospatial values, motion/direction, time/TTL, RF
    features, confidence/quality, and display/string fields.
  - Conservative rounding recommendations: confidence down, TTL down, error
    bounds and timing uncertainty up, units preserved, and coordinate
    quantization deterministic.
  - S1-06B should prefer a standalone precision-policy validator with optional
    `tools/validate_conformance.py --precision-policy`; default strict remains
    unchanged.
  - Numeric values in the plan are candidate defaults requiring human review,
    not final operational policy.
- Verification:
  - `python tools\validate_conformance.py --strict` -> `conformance ok`
  - `python tools\validate_conformance.py --strict --profile-projection` ->
    `projection conformance ok total=33`, `conformance ok`
  - `python tools\validate_conformance.py --strict --profile-projection --extension-registry` ->
    `projection conformance ok total=33`, `extension registry ok entries=63`,
    `conformance ok`
  - `python tools\validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes` ->
    `projection conformance ok total=33`, `extension registry ok entries=63`,
    `conformance classes ok classes=30 claims=2`, `conformance ok`
  - `python tools\validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative` ->
    `projection conformance ok total=33`, `extension registry ok entries=63`,
    `conformance classes ok classes=30 claims=2`,
    `encoding negative ok total=49`, `conformance ok`
  - `python tools\validate_projection.py --catalog conformance\profile_projection_field_catalog.yaml --must-pass conformance\profile-projection\must-pass.jsonl --must-fail conformance\profile-projection\must-fail.jsonl --quiet` ->
    `projection conformance ok total=33`
  - `python tools\validate_extension_registry.py --registry spec\extension-registry.yaml` ->
    `extension registry ok entries=63`
  - `python tools\validate_conformance_classes.py --manifest conformance\conformance_classes.yaml --claims conformance\claims\example-reference-gateway.yaml conformance\claims\example-core-producer.yaml` ->
    `conformance classes ok classes=30 claims=2`
  - `python tools\validate_encoding_negative.py --compact conformance\encoding-negative\compact-must-fail.jsonl --protobuf conformance\encoding-negative\protobuf-must-fail.jsonl --gateway conformance\encoding-negative\gateway-must-fail.jsonl --quiet` ->
    `encoding negative ok total=49`
  - `python -m pytest` -> `295 passed`
  - `git diff --check` -> passed with CRLF conversion warnings only.
- Decision: Plan only. D-010 remains open until S1-06B implements precision
  policy and S1-06C audits it.

## S1-06B - Profile Precision / Quantization Policy Floors Implementation

- Status: COMPLETE
- Date completed: 2026-05-07
- Scope: Implemented the profile precision policy artifacts, source/projected
  fixtures, standalone precision validator, focused tests, optional conformance
  runner integration, docs, and conformance class evidence updates using the
  S1-06A plan. D-010 remains open until S1-06C audits the implementation.
- Outputs:
  - `spec/profile-precision-policy.md`
  - `policy/profile-precision.yaml`
  - `conformance/profile-precision/README.md`
  - `conformance/profile-precision/context.jsonl`
  - `conformance/profile-precision/must-pass.jsonl`
  - `conformance/profile-precision/must-fail.jsonl`
  - `tools/validate_precision_policy.py`
  - `gateway/tests/test_profile_precision_policy.py`
- Integration: `tools/validate_conformance.py --precision-policy` runs the
  precision policy suite explicitly without changing default strict conformance
  behavior.
- Decisions:
  - The policy is a `reference_conformance_default` and has
    `requires_mission_review: true`.
  - Precision policy is profile/export policy, not schema, release policy,
    trust policy, emergency mode, UI policy, or transport semantics.
  - Identity, source, lineage, discriminator fields, event time, track identity,
    and units are immutable.
  - Confidence and TTL may be preserved or rounded/lowered conservatively, but
    not increased.
  - Error/timing uncertainty bounds may be preserved or rounded upward, but not
    decreased.
  - Packet-budget pressure cannot strip required semantic fields.
  - No schema, semantic contract, extension registry, gateway runtime, codec,
    adapter, release hash, or event-vocabulary changes were made.
- Verification:
  - `python tools\validate_precision_policy.py --policy policy\profile-precision.yaml --must-pass conformance\profile-precision\must-pass.jsonl --must-fail conformance\profile-precision\must-fail.jsonl` ->
    `profile precision policy ok total=32`
  - `python tools\validate_conformance.py --strict` -> `conformance ok`
  - `python tools\validate_conformance.py --strict --profile-projection` ->
    `projection conformance ok total=33`, `conformance ok`
  - `python tools\validate_conformance.py --strict --profile-projection --extension-registry` ->
    `projection conformance ok total=33`, `extension registry ok entries=63`,
    `conformance ok`
  - `python tools\validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes` ->
    `projection conformance ok total=33`, `extension registry ok entries=63`,
    `conformance classes ok classes=30 claims=2`, `conformance ok`
  - `python tools\validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative` ->
    `projection conformance ok total=33`, `extension registry ok entries=63`,
    `conformance classes ok classes=30 claims=2`,
    `encoding negative ok total=49`, `conformance ok`
  - `python tools\validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative --precision-policy` ->
    `projection conformance ok total=33`, `extension registry ok entries=63`,
    `conformance classes ok classes=30 claims=2`,
    `encoding negative ok total=49`, `profile precision policy ok total=32`,
    `conformance ok`
  - `python tools\validate_projection.py --catalog conformance\profile_projection_field_catalog.yaml --must-pass conformance\profile-projection\must-pass.jsonl --must-fail conformance\profile-projection\must-fail.jsonl --quiet` ->
    `projection conformance ok total=33`
  - `python tools\validate_extension_registry.py --registry spec\extension-registry.yaml` ->
    `extension registry ok entries=63`
  - `python tools\validate_conformance_classes.py --manifest conformance\conformance_classes.yaml --claims conformance\claims\example-reference-gateway.yaml conformance\claims\example-core-producer.yaml` ->
    `conformance classes ok classes=30 claims=2`
  - `python tools\validate_encoding_negative.py --compact conformance\encoding-negative\compact-must-fail.jsonl --protobuf conformance\encoding-negative\protobuf-must-fail.jsonl --gateway conformance\encoding-negative\gateway-must-fail.jsonl --quiet` ->
    `encoding negative ok total=49`
  - `python -m pytest -q gateway\tests\test_profile_precision_policy.py` ->
    `11 passed`
  - `python -m pytest` -> `306 passed`
  - `git diff --check` -> passed with CRLF conversion warnings only.

## S1-06C - Profile Precision / Quantization Policy Floors Post-Implementation Audit

- Status: COMPLETE
- Date completed: 2026-05-07
- Output: `docs/s1_06c_profile_precision_quantization_policy_audit.md`
- Scope: Audited S1-06B for conservative rounding, utility-floor behavior,
  packet-budget interaction, projection preservation compatibility, validator
  behavior, conformance-class impact, documentation alignment, and absence of
  schema/contract/registry/vocabulary drift.
- Findings:
  - Precision policy is correctly treated as profile/export policy, not schema.
  - Reference defaults remain `reference_conformance_default` and require
    mission review.
  - Immutable identity/source/lineage/discriminator paths, units, confidence,
    TTL, timing/error bounds, utility floors, command target floors, hidden
    defaults, and packet-budget required-field stripping are covered by
    validator logic and fixtures.
  - The validator reuses projection preservation; precision policy does not
    replace same-event projection invariants.
  - No schemas, semantic contract text, extension registry artifacts, gateway
    runtime behavior, codecs, adapters, release hashes, or event vocabulary were
    changed.
  - Conformance class manifest and example claims remain valid.
- Decision: S1-06B is verified. D-010 is closed. D-011, D-002, D-001, D-003,
  and D-004 remain open.

## S1-07A - Crosswalk TAKEOFF Mention Cleanup

- Status: COMPLETE
- Date completed: 2026-05-07
- Output: `docs/s1_07a_takeoff_crosswalk_cleanup.md`
- Scope: Resolved D-011 with a narrow documentation cleanup for the stray
  `TAKEOFF` mention in `docs/zmeta_contract_to_stack_crosswalk.md`.
- Cleanup:
  - Corrected the v1.1.0 expanded-tasking crosswalk row to list the actual
    supported task values: `RETURN_TO_BASE`, `LAND`, `LOITER`, `SCAN_RF`,
    `TRACK_TARGET`, and `CHANGE_SENSOR_MODE`.
  - Kept existing invalidity and leakage-guard references proving `TAKEOFF`
    remains invalid current vocabulary.
- Notes: No schemas, semantic contract text, extension registry artifacts,
  validators, gateway runtime behavior, codecs, adapters, conformance class
  definitions, examples, fixtures, release hashes, or event vocabulary were
  changed.
- Verification:
  - `git grep -n -i "takeoff"` -> remaining references are invalidity guards,
    historical planning/audit notes, or S1-07A closure notes.
  - `python tools\validate_extension_registry.py --registry spec\extension-registry.yaml` ->
    `extension registry ok entries=63`
  - `python tools\validate_conformance.py --strict` -> `conformance ok`
  - `python tools\validate_conformance.py --strict --profile-projection` ->
    `projection conformance ok total=33`, `conformance ok`
  - `python tools\validate_conformance.py --strict --profile-projection --extension-registry` ->
    `projection conformance ok total=33`, `extension registry ok entries=63`,
    `conformance ok`
  - `python tools\validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes` ->
    `projection conformance ok total=33`, `extension registry ok entries=63`,
    `conformance classes ok classes=30 claims=2`, `conformance ok`
  - `python tools\validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative` ->
    `projection conformance ok total=33`, `extension registry ok entries=63`,
    `conformance classes ok classes=30 claims=2`, `encoding negative ok total=49`,
    `conformance ok`
  - `python tools\validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative --precision-policy` ->
    `projection conformance ok total=33`, `extension registry ok entries=63`,
    `conformance classes ok classes=30 claims=2`, `encoding negative ok total=49`,
    `profile precision policy ok total=32`, `conformance ok`
  - `python tools\validate_conformance_classes.py --manifest conformance\conformance_classes.yaml --claims conformance\claims\example-reference-gateway.yaml conformance\claims\example-core-producer.yaml` ->
    `conformance classes ok classes=30 claims=2`
  - `python tools\validate_encoding_negative.py --compact conformance\encoding-negative\compact-must-fail.jsonl --protobuf conformance\encoding-negative\protobuf-must-fail.jsonl --gateway conformance\encoding-negative\gateway-must-fail.jsonl --quiet` ->
    `encoding negative ok total=49`
  - `python tools\validate_precision_policy.py --policy policy\profile-precision.yaml --must-pass conformance\profile-precision\must-pass.jsonl --must-fail conformance\profile-precision\must-fail.jsonl --quiet` ->
    `profile precision policy ok total=32`
  - `python -m pytest` -> `306 passed`
  - `git diff --check` -> passed with CRLF conversion warnings only.
- Decision: S1-07A is complete. D-011 is closed. D-001, D-002, D-003, and
  D-004 remain open.

## S1-08A - MAVLink Adapter README State Payload Drift Cleanup

- Status: COMPLETE
- Date completed: 2026-05-07
- Output: `docs/s1_08a_mavlink_state_payload_drift_cleanup.md`
- Scope: Resolve D-001 with a narrow documentation cleanup for MAVLink adapter
  README state payload drift. Do not change schemas, gateway runtime behavior,
  validators, codecs, adapters, or event vocabulary unless a later prompt
  explicitly opens implementation scope.
- Cleanup:
  - Replaced the stale `payload.features.*` MAVLink STATE_EVENT mapping table
    with guidance that distinguishes state-safe fields, `payload.quality`,
    SYSTEM_EVENT status, OBSERVATION_EVENT observation modality contracts, and
    lineage.
  - Clarified that `payload.extensions` is not a loophole for raw telemetry or
    measurements.
  - Corrected the low-GPS-fix note to reference `payload.quality.geo_status`
    instead of a raw feature.
- Code behavior: `translate_platform_state()` already emits state-safe fields
  and `payload.quality`; it does not emit raw `payload.features.*` in
  STATE_EVENT. No code changes were required, and D-012 was not added.
- Notes: No schemas, semantic contract text, extension registry artifacts,
  validators, gateway runtime behavior, codecs, adapters, conformance class
  definitions, examples, fixtures, release hashes, or event vocabulary were
  changed.
- Verification:
  - `git grep -n "payload.features" adapters/ingress/mavlink adapters README.md spec schema policy gateway tools conformance` ->
    MAVLink README references are now prohibition or "incorrect mapping to
    avoid" examples; other hits are observation, extension, projection, or
    precision policy surfaces.
  - `git grep -n -i "mavlink" adapters/ingress/mavlink adapters README.md docs spec conformance gateway/tests` ->
    MAVLink references are adapter docs/tests, egress command projection, or S1
    governance notes.
  - `git grep -n "raw_features\|measurement\|measurements\|modality\|data_ref\|data_refs" adapters/ingress/mavlink adapters README.md docs spec conformance gateway/tests` ->
    MAVLink README references are raw-field prohibitions; schema/conformance/test
    references preserve existing observation and state raw-field boundaries.
  - `python tools\validate_conformance.py --strict` -> `conformance ok`
  - `python tools\validate_conformance.py --strict --profile-projection` ->
    `projection conformance ok total=33`, `conformance ok`
  - `python tools\validate_conformance.py --strict --profile-projection --extension-registry` ->
    `projection conformance ok total=33`, `extension registry ok entries=63`,
    `conformance ok`
  - `python tools\validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes` ->
    `projection conformance ok total=33`, `extension registry ok entries=63`,
    `conformance classes ok classes=30 claims=2`, `conformance ok`
  - `python tools\validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative` ->
    `projection conformance ok total=33`, `extension registry ok entries=63`,
    `conformance classes ok classes=30 claims=2`, `encoding negative ok total=49`,
    `conformance ok`
  - `python tools\validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative --precision-policy` ->
    `projection conformance ok total=33`, `extension registry ok entries=63`,
    `conformance classes ok classes=30 claims=2`, `encoding negative ok total=49`,
    `profile precision policy ok total=32`, `conformance ok`
  - `python tools\validate_projection.py --catalog conformance\profile_projection_field_catalog.yaml --must-pass conformance\profile-projection\must-pass.jsonl --must-fail conformance\profile-projection\must-fail.jsonl --quiet` ->
    `projection conformance ok total=33`
  - `python tools\validate_extension_registry.py --registry spec\extension-registry.yaml` ->
    `extension registry ok entries=63`
  - `python tools\validate_conformance_classes.py --manifest conformance\conformance_classes.yaml --claims conformance\claims\example-reference-gateway.yaml conformance\claims\example-core-producer.yaml` ->
    `conformance classes ok classes=30 claims=2`
  - `python tools\validate_encoding_negative.py --compact conformance\encoding-negative\compact-must-fail.jsonl --protobuf conformance\encoding-negative\protobuf-must-fail.jsonl --gateway conformance\encoding-negative\gateway-must-fail.jsonl --quiet` ->
    `encoding negative ok total=49`
  - `python tools\validate_precision_policy.py --policy policy\profile-precision.yaml --must-pass conformance\profile-precision\must-pass.jsonl --must-fail conformance\profile-precision\must-fail.jsonl --quiet` ->
    `profile precision policy ok total=32`
  - `python -m pytest` -> `306 passed`
  - `git diff --check` -> passed with CRLF conversion warnings only.
- Decision: S1-08A is complete. D-001 is closed. D-002, D-003, and D-004
  remain open.

## S1-09A - Contract Hash / Release Hash Follow-Up Plan Only

- Status: COMPLETE
- Date completed: 2026-05-07
- Output: `docs/s1_09_contract_release_hash_plan.md`
- Scope: Planned D-002 contract hash and release hash follow-up. No hashes were
  recomputed, and no release manifest or release tooling was implemented.
- Plan summary:
  - Defines separate hash categories for semantic contract, schema bundle,
    policy bundle, extension registry, conformance class manifest, profile
    projection catalog, encoding-negative suite, profile precision policy,
    encoding projection specs, release manifest, and release bundle.
  - Classifies normative semantic, schema, policy, governance, conformance,
    encoding projection, and advisory documentation artifacts.
  - Recommends `release/zmeta-release-manifest.yaml` as the machine-readable
    release manifest path because the repo already uses `release/` for release
    notes, validation reports, bundle builders, checksums, signatures, and
    release assets.
  - Recommends keeping `tools/compute_contract_hash.py` narrow for current
    gateway-compatible schema/policy/semantic contract gates while adding
    separate release-manifest build and validation tooling in S1-09B.
  - Plans deployment gate behavior that can keep existing
    `require_schema_hash`, `require_policy_hash`, and `require_contract_hash`
    while allowing future release-manifest validation to verify broader
    registry, conformance, projection, encoding, and precision baselines.
  - Plans conformance claim integration so `pending_D-002` can be replaced only
    after actual release hashes exist and validate.
- Notes: Plan-only task. No schemas, semantic contract text, policy files,
  extension registry artifacts, conformance class manifests, validators,
  gateway runtime behavior, codecs, adapters, release hashes, release manifests,
  conformance fixtures, or event vocabulary were changed.
- Verification:
  - `python tools\validate_conformance.py --strict` -> `conformance ok`
  - `python tools\validate_conformance.py --strict --profile-projection` ->
    `projection conformance ok total=33`, `conformance ok`
  - `python tools\validate_conformance.py --strict --profile-projection --extension-registry` ->
    `projection conformance ok total=33`, `extension registry ok entries=63`,
    `conformance ok`
  - `python tools\validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes` ->
    `projection conformance ok total=33`, `extension registry ok entries=63`,
    `conformance classes ok classes=30 claims=2`, `conformance ok`
  - `python tools\validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative` ->
    `projection conformance ok total=33`, `extension registry ok entries=63`,
    `conformance classes ok classes=30 claims=2`, `encoding negative ok total=49`,
    `conformance ok`
  - `python tools\validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative --precision-policy` ->
    `projection conformance ok total=33`, `extension registry ok entries=63`,
    `conformance classes ok classes=30 claims=2`, `encoding negative ok total=49`,
    `profile precision policy ok total=32`, `conformance ok`
  - `python tools\validate_projection.py --catalog conformance\profile_projection_field_catalog.yaml --must-pass conformance\profile-projection\must-pass.jsonl --must-fail conformance\profile-projection\must-fail.jsonl --quiet` ->
    `projection conformance ok total=33`
  - `python tools\validate_extension_registry.py --registry spec\extension-registry.yaml` ->
    `extension registry ok entries=63`
  - `python tools\validate_conformance_classes.py --manifest conformance\conformance_classes.yaml --claims conformance\claims\example-reference-gateway.yaml conformance\claims\example-core-producer.yaml` ->
    `conformance classes ok classes=30 claims=2`
  - `python tools\validate_encoding_negative.py --compact conformance\encoding-negative\compact-must-fail.jsonl --protobuf conformance\encoding-negative\protobuf-must-fail.jsonl --gateway conformance\encoding-negative\gateway-must-fail.jsonl --quiet` ->
    `encoding negative ok total=49`
  - `python tools\validate_precision_policy.py --policy policy\profile-precision.yaml --must-pass conformance\profile-precision\must-pass.jsonl --must-fail conformance\profile-precision\must-fail.jsonl --quiet` ->
    `profile precision policy ok total=32`
  - `python -m pytest` -> `306 passed`
  - `git diff --check` -> passed.
- Decision: S1-09A is complete. D-002 remains open pending S1-09B
  implementation. D-003 and D-004 remain open.

## S1-09B - Contract Hash / Release Hash Implementation

- Status: COMPLETE
- Date completed: 2026-05-07
- Scope: Implemented the release hash policy, reference release manifest,
  deterministic manifest build and validation tooling, focused tests, optional
  conformance runner integration, documentation, and claim hash updates as
  defined by S1-09A.
- Outputs:
  - `spec/release-hash-policy.md`
  - `release/zmeta-release-manifest.yaml`
  - `tools/build_release_manifest.py`
  - `tools/validate_release_manifest.py`
  - `gateway/tests/test_release_manifest.py`
- Integration: `tools/validate_conformance.py --release-manifest` validates the
  structured release manifest explicitly without changing default strict
  conformance behavior.
- Decisions:
  - `contract_hash` in example claims now records the narrow
    `semantic_contract_hash`, not the whole stack.
  - The release manifest records broader category hashes and excludes the
    manifest file itself from `release_bundle_hash`.
  - Protobuf remains an experimental encoding projection, not v1.0 semantic
    authority.
  - `tools/compute_contract_hash.py` remains the existing gateway-compatible
    schema/policy/semantic hash helper and was not overloaded.
  - No schema, semantic contract, extension registry, event vocabulary, codec,
    adapter, or gateway runtime behavior changed.
- Verification:
  - `python tools\build_release_manifest.py --output release\zmeta-release-manifest.yaml` -> wrote reference manifest
  - `python tools\validate_release_manifest.py --manifest release\zmeta-release-manifest.yaml` -> `release manifest ok groups=14 artifacts=49`
  - `python tools\compute_contract_hash.py` -> gateway-compatible schema, policy, semantics, and combined contract hashes printed successfully
  - `python tools\validate_conformance.py --strict` -> `conformance ok`
  - `python tools\validate_conformance.py --strict --profile-projection` -> `projection conformance ok total=33`, `conformance ok`
  - `python tools\validate_conformance.py --strict --profile-projection --extension-registry` -> `projection conformance ok total=33`, `extension registry ok entries=63`, `conformance ok`
  - `python tools\validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes` -> `projection conformance ok total=33`, `extension registry ok entries=63`, `conformance classes ok classes=30 claims=2`, `conformance ok`
  - `python tools\validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative` -> `encoding negative ok total=49`, `conformance ok`
  - `python tools\validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative --precision-policy` -> `profile precision policy ok total=32`, `conformance ok`
  - `python tools\validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative --precision-policy --release-manifest` -> `conformance ok`
  - `python tools\validate_projection.py --catalog conformance\profile_projection_field_catalog.yaml --must-pass conformance\profile-projection\must-pass.jsonl --must-fail conformance\profile-projection\must-fail.jsonl --quiet` -> `projection conformance ok total=33`
  - `python tools\validate_extension_registry.py --registry spec\extension-registry.yaml` -> `extension registry ok entries=63`
  - `python tools\validate_conformance_classes.py --manifest conformance\conformance_classes.yaml --claims conformance\claims\example-reference-gateway.yaml conformance\claims\example-core-producer.yaml` -> `conformance classes ok classes=30 claims=2`
  - `python tools\validate_encoding_negative.py --compact conformance\encoding-negative\compact-must-fail.jsonl --protobuf conformance\encoding-negative\protobuf-must-fail.jsonl --gateway conformance\encoding-negative\gateway-must-fail.jsonl --quiet` -> `encoding negative ok total=49`
  - `python tools\validate_precision_policy.py --policy policy\profile-precision.yaml --must-pass conformance\profile-precision\must-pass.jsonl --must-fail conformance\profile-precision\must-fail.jsonl --quiet` -> `profile precision policy ok total=32`
  - `python -m pytest -q gateway\tests\test_release_manifest.py` -> `15 passed`
  - `python -m pytest` -> `321 passed`

## S1-09C - Contract Hash / Release Hash Post-Implementation Audit

- Status: COMPLETE
- Date completed: 2026-05-07
- Output: `docs/s1_09c_contract_release_hash_audit.md`
- Scope: Audited S1-09B release hash implementation for deterministic hashing,
  manifest correctness, deployment gate alignment, conformance claim
  integration, documentation, and absence of semantic/schema/registry drift.
- Cleanup:
  - `tools/build_release_manifest.py` now uses stable placeholder `git_commit`
    and `branch` metadata by default, so committed reference manifests do not
    change only because the repo head moved after a checkpoint commit.
  - Formal release generation can still pass explicit metadata with
    `--git-commit` and `--branch`.
  - `release/zmeta-release-manifest.yaml` was rebuilt with stable metadata and
    no D-002 open-issue entry.
  - D-012 was added for formal release tag, signature, and attestation
    packaging.
- Verification:
  - `python tools\build_release_manifest.py --output release\zmeta-release-manifest.yaml` -> wrote reference manifest
  - `python tools\validate_release_manifest.py --manifest release\zmeta-release-manifest.yaml` -> `release manifest ok groups=14 artifacts=49`
  - Manifest rebuild idempotence check -> unchanged file hash after immediate rebuild
  - `python tools\compute_contract_hash.py` -> gateway-compatible schema, policy, semantics, and combined contract hashes printed successfully
  - `python tools\validate_conformance.py --strict` -> `conformance ok`
  - `python tools\validate_conformance.py --strict --profile-projection` -> `projection conformance ok total=33`, `conformance ok`
  - `python tools\validate_conformance.py --strict --profile-projection --extension-registry` -> `projection conformance ok total=33`, `extension registry ok entries=63`, `conformance ok`
  - `python tools\validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes` -> `projection conformance ok total=33`, `extension registry ok entries=63`, `conformance classes ok classes=30 claims=2`, `conformance ok`
  - `python tools\validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative` -> `encoding negative ok total=49`, `conformance ok`
  - `python tools\validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative --precision-policy` -> `profile precision policy ok total=32`, `conformance ok`
  - `python tools\validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative --precision-policy --release-manifest` -> `conformance ok`
  - `python tools\validate_projection.py --catalog conformance\profile_projection_field_catalog.yaml --must-pass conformance\profile-projection\must-pass.jsonl --must-fail conformance\profile-projection\must-fail.jsonl --quiet` -> `projection conformance ok total=33`
  - `python tools\validate_extension_registry.py --registry spec\extension-registry.yaml` -> `extension registry ok entries=63`
  - `python tools\validate_conformance_classes.py --manifest conformance\conformance_classes.yaml --claims conformance\claims\example-reference-gateway.yaml conformance\claims\example-core-producer.yaml` -> `conformance classes ok classes=30 claims=2`
  - `python tools\validate_encoding_negative.py --compact conformance\encoding-negative\compact-must-fail.jsonl --protobuf conformance\encoding-negative\protobuf-must-fail.jsonl --gateway conformance\encoding-negative\gateway-must-fail.jsonl --quiet` -> `encoding negative ok total=49`
  - `python tools\validate_precision_policy.py --policy policy\profile-precision.yaml --must-pass conformance\profile-precision\must-pass.jsonl --must-fail conformance\profile-precision\must-fail.jsonl --quiet` -> `profile precision policy ok total=32`
  - `python -m pytest -q gateway\tests\test_release_manifest.py` -> `16 passed`
  - `python -m pytest` -> `322 passed`
- Decision: S1-09B is verified. D-002 is closed. D-003, D-004, and D-012 remain
  open.

## S1-10A - Out-of-Scope Artifact Roadmap Plan Only

- Status: SUPERSEDED / CANCELLED BY S1-10P
- Date completed: 2026-05-07
- Output: deleted during S1-10P
- Scope correction: User review determined that the broad plan was outside
  ZMeta's semantic-standard scope. The plan file was removed during S1-10P.

## S1-10P - Purge FORGE-Derived Scope Contamination from ZMeta

- Status: COMPLETE
- Date completed: 2026-05-07
- Output: `docs/s1_10p_forge_scope_purge.md`
- Scope: Removed FORGE-derived organizational artifact scope from the semantic
  contract, extension registry, release metadata, worklog, handoff, and related
  governance docs.
- Summary:
  - S1-10B was stopped before commit, and no stopped S1-10B files remain.
  - ZMeta remains focused on semantic interoperability, bandwidth-aware
    profiles, lineage, adapters, encodings, validation, conformance, release
    manifests, and implementation discipline.
  - The contaminated semantic-contract boundary section was removed.
  - The extension registry now contains only ZMeta vocabulary/governance
    concepts.
  - Release metadata was rebuilt after hash updates.
- Notes: No schemas, gateway runtime behavior, adapters, codecs, or event
  vocabulary were changed.
- Decision: D-004 is closed as `CLOSED - REMOVED FROM ZMETA SCOPE`. D-003 and
  D-012 remain open.

## S1-10B - Stopped Out-of-Scope Artifact Implementation

- Status: CANCELLED / STOPPED BEFORE COMMIT
- Scope correction: The stopped S1-10B prompt attempted to implement artifacts
  outside the ZMeta baseline. No checkpoint commit was created. The uncommitted
  files were rolled back before S1-10P edits began.

## S1-10C - Cancelled Out-of-Scope Artifact Audit

- Status: NOT OPENED / CANCELLED BY S1-10P
- Scope correction: No S1-10B implementation remains to audit.

## S1-11A - Future Versioned Semantic Branch Roadmap Plan Only

- Status: COMPLETE
- Date completed: 2026-05-07
- Output: `docs/s1_11_future_versioned_semantic_branch_roadmap_plan.md`
- Scope: Plan D-003 versioned implementation branches for future semantic
  concepts, including markings, integrity, anti-replay, trust, AI assurance,
  PNT integrity, UAS identity, coalition export, data nutrition, emergency/L0,
  and related conformance surfaces.
- Summary:
  - Classified current v1.0 vocabulary, v1.1.0 experimental vocabulary,
    reserved/proposed future vocabulary, and out-of-scope concepts.
  - Defined branch lifecycle statuses and adoption gates.
  - Inventoried PNT integrity, signing/key identity/anti-replay, mesh trust,
    UAS identity, AI model assurance, raw-data-absent evidence status,
    coalition export, projection metadata, track lifecycle, future modalities,
    semantic quality summaries, compute degradation, and emergency/L0.
  - Recommended sequencing and dependency order without approving or
    implementing any branch.
- Notes: Documentation-only task. No schemas, semantic contract text,
  extension registry, conformance class manifest, validators, gateway runtime,
  adapters, codecs, policies, release manifest, or event vocabulary were
  changed.
- Decision: D-003 remains `OPEN - ROADMAP PLANNED`. D-004 remains closed as
  removed from ZMeta scope. D-012 remains open.

## S1-11B - Future Branch Roadmap Machine-Readable Artifact

- Status: PENDING IMPLEMENTATION
- Scope: If maintainers approve, create a machine-readable future branch
  roadmap artifact that records candidate branch status, dependencies, required
  implementation surfaces, and rejection/defer decisions. It must not modify
  schemas, the extension registry, conformance classes, or event vocabulary, and
  it must not make any future candidate valid.

## S1-12A - Formal Release Tag / Signature / Attestation Plan Only

- Status: COMPLETE
- Date completed: 2026-05-07
- Output: `docs/s1_12_formal_release_tag_signature_attestation_plan.md`
- Scope: Plan D-012 formal release tag, signature, checksum, validation report,
  and post-release attestation packaging without reopening D-002 or changing
  semantics.
- Summary:
  - Defined release artifact, release state, tagging, signing, attestation,
    key-handling, formal release workflow, verification workflow, tooling, and
    test strategy.
  - Connected the S1-09 release manifest and category hashes to existing
    release asset checksum/signature tooling without making release signing a
    semantic gate.
  - Confirmed signatures and attestations are release governance artifacts only.
- Notes: Documentation-only task. No schemas, semantic contract text,
  extension registry, conformance class manifest, validators, gateway runtime,
  adapters, codecs, policies, release manifest, signatures, keys, tags, or
  event vocabulary were changed.
- Decision: D-012 remains open pending S1-12B implementation and S1-12C audit.
  D-003 remains `OPEN - ROADMAP PLANNED`. D-004 remains closed as removed from
  ZMeta scope.

## S1-12B - Formal Release Tag / Signature / Attestation Packaging Implementation

- Status: COMPLETE
- Date completed: 2026-05-07
- Outputs:
  - `spec/release-signing-attestation.md`
  - `release/RELEASE_NOTES_TEMPLATE.md`
  - `release/ATTESTATION_TEMPLATE.yaml`
  - `release/RELEASE_PACKAGE_README.md`
  - `tools/build_release_package.py`
  - `tools/validate_release_package.py`
  - `gateway/tests/test_release_package.py`
- Scope: Implemented release package specification, templates,
  no-signature/dry-run package builder, release package validator, no-secret
  scanning, focused tests, release manifest grouping, and optional
  `--release-package` conformance integration.
- Summary:
  - Added package-level release notes and attestation templates with explicit
    placeholders only.
  - Added a no-signature builder that validates the release manifest, supports
    dry-run output, and writes deterministic package metadata, attestation,
    release notes, and checksums only when explicitly run without `--dry-run`.
  - Added a validator that validates templates or package output, checks
    package metadata, attestation hashes, checksums, missing artifacts, D-003
    and D-012 open-issue references, and obvious secret/key material.
  - Added optional conformance integration through
    `tools/validate_conformance.py --release-package`.
  - Added `release_packaging` to the governed release manifest artifact groups.
- Notes: No real release tag, signature, key, certificate, credential, token,
  secret, generated package output, schema change, semantic contract change,
  extension registry change, conformance class status change, gateway runtime
  change, adapter change, codec change, or event vocabulary change was made.
- Decision: S1-12C later audited this implementation and closed D-012. D-003
  remains `OPEN - ROADMAP PLANNED`. D-004 remains closed as removed from ZMeta
  scope.

## S1-12C - Formal Release Tag / Signature / Attestation Post-Implementation Audit

- Status: COMPLETE
- Date completed: 2026-05-07
- Output: `docs/s1_12c_formal_release_packaging_audit.md`
- Scope: Audit S1-12B for clean-checkout reproducibility, checksum integrity,
  signature verification behavior, attestation correctness, no-secret handling,
  release manifest compatibility, docs alignment, and absence of semantic or
  vocabulary drift.
- Summary:
  - Verified S1-12B touched only expected release packaging files.
  - Verified release package spec, templates, no-signature builder, validator,
    no-secret checks, optional conformance flag, release manifest integration,
    and focused tests.
  - Built and validated a temporary package output, then removed it before
    commit.
  - Classified existing `.asc`, checksum, release note, validation report, and
    release zip files as pre-existing release assets; S1-12C did not modify or
    regenerate them.
  - Removed D-012 from generated package open-issue defaults after audit
    closure; D-003 remains the only known open issue in the reference manifest.
- Notes: No real release tag, signature, key, certificate, credential, token,
  secret, schema change, semantic contract change, extension registry change,
  conformance class status change, gateway runtime change, adapter change,
  codec change, or event vocabulary change was made.
- Decision: D-012 is closed. D-003 remains `OPEN - ROADMAP PLANNED`. D-004
  remains closed as removed from ZMeta scope.

## R1-01 - v1.1.5 Release Publication

- Status: COMPLETE
- Date completed: 2026-05-08 UTC / 2026-05-07 local
- Release URL: `https://github.com/JTC-byte/zmeta-spec/releases/tag/v1.1.5`
- Tag: `v1.1.5`
- Tagged commit: `d4d406b43a705ca5b7a314e1d5388c3ca39c750a`
- Scope: Updated the local README surface and release notes, pushed the
  hardened baseline to `origin/main`, created the annotated `v1.1.5` tag, and
  published the GitHub release with release assets.
- README/docs update:
  - Audited every repo README and removed stale `v1.1.4` release references
    from active README guidance.
  - Updated `README.md`, `release/README.md`, `tools/README.md`,
    `adapters/README.md`, `RELEASE_CHECKLIST.md`, and release helper defaults
    for `v1.1.5`.
  - Added `release/RELEASE_NOTES_v1.1.5.md` and
    `release/VALIDATION_REPORT_v1.1.5.md`.
- Published assets:
  - `zmeta-v1.1.5-dist.zip`
  - `zmeta-edge-v1.1.5.zip`
  - `zmeta-gateway-v1.1.5.zip`
  - `zmeta-release-package-v1.1.5.zip`
  - `zmeta-release-manifest.yaml`
  - `RELEASE_NOTES_v1.1.5.md`
  - `VALIDATION_REPORT_v1.1.5.md`
  - `SHA256SUMS_v1.1.5.txt`
- Verification:
  - `python tools\validate_release_manifest.py --manifest release\zmeta-release-manifest.yaml`
    -> `release manifest ok groups=15 artifacts=55`
  - `python tools\validate_release_package.py --manifest release\zmeta-release-manifest.yaml --templates-only`
    -> `release package ok mode=templates`
  - `python tools\validate_release_package.py --manifest release\zmeta-release-manifest.yaml --package-dir release\package-v1.1.5`
    -> `release package ok mode=package` before zipping package output
  - `python release\sign_release_artifacts.py --version v1.1.5 --verify-checksums`
    -> `checksums ok: SHA256SUMS_v1.1.5.txt`
  - `python tools\compute_contract_hash.py` -> schema, policy, semantics, and
    combined contract hashes printed successfully
  - `python tools\validate_conformance.py --strict` -> `conformance ok`
  - `python tools\validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative --precision-policy --release-manifest --release-package`
    -> projection, registry, conformance classes, encoding-negative,
    precision-policy, release-manifest, release-package, and conformance checks
    passed
  - `python -m pytest -q gateway\tests\test_release_package.py` -> `11 passed`
  - `python -m pytest` -> `333 passed`
  - `git diff --check` -> passed
- Signature status: GPG is installed, but no usable local secret signing key was
  available. No `.asc` signatures, private keys, tokens, credentials,
  certificates, or signing secrets were created or committed. The release body
  documents that v1.1.5 is verified through SHA-256 checksums, the structured
  release manifest, and the release package checksum file.
- Decision: The ZMeta baseline hardening and release-prep workstream is
  complete for v1.1.5. Remaining active work is D-003 future versioned semantic
  branch governance. Optional future release operations may add detached
  signatures only through an approved external signing-key process.

## S1-13A - Stack Conformance And Stale File Audit

- Status: COMPLETE
- Date completed: 2026-06-08
- Output: `docs/s1_13a_stack_conformance_and_stale_file_audit.md`
- Scope: Audited tracked and ignored workspace state, current release/version
  references, schema/policy/conformance boundary coverage, adapter/runtime
  semantic posture, and validation surfaces for rogue or stale files.
- Findings:
  - No untracked non-ignored files were present.
  - Ignored local artifacts were expected local/generated state:
    `LOCAL_NOTES.md`, `.gitconfig-local`, Python caches, generated release zip
    files, `release/bundles/`, `release/dist/`, and smoke extraction folders.
  - Active README/release surfaces identify `v1.1.5` as the current release.
  - `tools/check_compat.py` and CI still targeted `v1.1.4`; this was live
    tooling drift and was corrected to `v1.1.5`.
  - Historical `v1.1.4`, `TAKEOFF`, and FORGE references remain release
    history, invalidity guards, or audit history.
- Changes:
  - Updated `tools/check_compat.py` to accept and default to `--target v1.1.5`.
  - Updated `.github/workflows/ci.yml` migration compatibility checks to target
    `v1.1.5`.
  - Added a regression test for the documented `--target v1.1.5` invocation.
  - Added explicit D-009 boundary tests proving v1.0 generic observation
    extension structures do not adopt v1.1.0 formal feature, quality, or
    data-reference contracts.
- Notes: No semantic contract, schema, policy, extension registry, conformance
  class manifest, adapter, codec, release manifest, or event vocabulary changed.
- Decision: D-009 is closed. D-003 remains `OPEN - ROADMAP PLANNED`.

## S1-14 - External Projection Promotion Contract

- Status: COMPLETE
- Date completed: 2026-06-08
- Output: `docs/s1_14_external_projection_promotion_contract.md`
- Scope: Hardened the boundary where CoT/JREAP/MAVLink or other external
  tactical track reports re-enter ZMeta as `STATE_EVENT`.
- Changes:
  - Added normative semantic contract language stating that external/lossy
    projections require explicit promotion policy, freshness, lineage status,
    confidence basis, trust reference, and loop/reflection status before they
    become authoritative ZMeta state.
  - Added producer-authority policy gates for `cot-ingress`, `jreap-ingress`,
    `mavlink`, `mavlink-adapter`, and `mavlink-*` state producers.
  - Added validator enforcement that rejects schema-valid external
    `STATE_EVENT`s without valid `payload.extensions.external_promotion`
    evidence as `PRODUCER_NOT_ALLOWED`.
  - Added operator-tunable external promotion modes: `reject` (reference
    default), `warn`, `degrade`, and `quarantine`. Non-reject modes emit
    diagnostics; degrade/quarantine mode also reduces confidence and/or
    shortens `payload.valid_for_ms`.
  - Updated CoT, JREAP, and MAVLink ingress templates to emit promotion metadata
    and `promote:*` lineage transforms.
  - Added focused unit tests and conformance fixtures for missing promotion
    evidence, compact Profile L evidence, full Profile H evidence, loop risk,
    and accidental `translate:*` promotion transforms.
- Bandwidth decision: Profile L promotion evidence is limited to compact policy,
  trust, lineage, and loop-status handles. Full audit detail is reserved for
  Profile H, so the hardening does not require raw data, full ancestry, or large
  audit blocks on constrained links. Degrade/quarantine annotations are compact
  policy decisions, not expanded provenance.
- Notes: No new event type, schema branch, top-level event field, v1.0/v1.1.0
  version-discrimination change, extension-registry promotion, trust/signing
  vocabulary, or same-event profile projection metadata was added.
- Verification:
  - `python -m pytest -q gateway\tests\test_external_state_promotion.py gateway\tests\test_gateway_smoke.py` -> `25 passed`
  - `python tools\validate_conformance.py --strict` -> `conformance ok`
  - `python tools\validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative --precision-policy --release-manifest --release-package` -> all opt-in suites passed
  - `python tools\validate_examples.py --strict --require-all` -> `overall total=40 passed=40 failed=0 warnings=0`
  - `python tools\validate_release_manifest.py --manifest release\zmeta-release-manifest.yaml` -> `release manifest ok groups=15 artifacts=55`
  - `python tools\validate_release_package.py --manifest release\zmeta-release-manifest.yaml --templates-only` -> `release package ok mode=templates`
  - `python -m pytest -q` -> `349 passed, 106 subtests passed`
  - `python tools\compute_contract_hash.py` -> `contract_hash=de57a50ccd28d1d89a1d78abcc6ecb2c322a8be9cf8bb257c171e4782d915049`
  - `git diff --check` -> passed with normal Windows CRLF conversion warnings

## S1-15A - Risk Adjudication Semantic Baseline

- Status: COMPLETE
- Date completed: 2026-06-08
- Output: `spec/semantics-contract.md`
- Scope: Established the semantic baseline for configurable operational risk
  response without loosening interoperability or semantic truth.
- Changes:
  - Added `Risk Adjudication and Operator-Tunable Policy` to the enforcement
    model.
  - Classified rules as `locked`, `tunable`, or `advisory`.
  - Defined bounded policy actions: `reject`, `warn`, `degrade`, `quarantine`,
    and narrowly scoped `ignore`.
  - Required soft acceptance to remain filterable through accepted-event labels,
    same-stream diagnostics keyed by `original_event_id`, or both.
  - Added allowed/prohibited operational use labels so policy can accept data
    for display/AAR while blocking use in fusion, state update, command basis, or
    autonomy tasking when risk conditions require it.
  - Clarified that SCHEMA_VIOLATION is the v1.0 diagnostic envelope for schema
    and policy validation outcomes, not a domain trust/quarantine/lifecycle
    state.
  - Clarified that quarantine is currently a policy action, while schema-level
    trust/quarantine vocabulary remains future versioned work.
- Stack follow-up: S1-15B should audit/update policy, validators, gateway
  warning/degrade paths, conformance, and docs to emit consistent
  `risk_dimension`, `policy_mode`, `policy_decision`, policy reference, scope,
  allowed/prohibited uses, and effect details.
- Verification:
  - `python tools\validate_release_manifest.py --manifest release\zmeta-release-manifest.yaml` -> `release manifest ok groups=15 artifacts=55`
  - `python tools\validate_conformance.py --strict` -> `conformance ok`
  - `python tools\compute_contract_hash.py` -> `contract_hash=7bd2206319ca85b93455d4ad1e28b011111824c10a5c108ab8cebc0f86a7bf84`
  - `git diff --check` -> passed with normal Windows CRLF conversion warnings

## S1-15B - Risk Adjudication Stack Conformance Pass

- Status: COMPLETE
- Date completed: 2026-06-08
- Output: `docs/s1_15b_risk_adjudication_stack_conformance_audit.md`
- Scope: Audited the stack folder-by-folder against the S1-15A semantic
  baseline and conformed policy, gateway validators, runtime degradation,
  conformance fixtures, tests, schemas, and docs to filterable accepted-risk
  behavior.
- Changes:
  - Added normalized risk diagnostics for timing freshness, lineage warnings,
    and external promotion policy decisions.
  - Added event-side `payload.extensions.risk_adjudication` labels when accepted
    events are degraded or quarantined.
  - Added `use_limits` policy labels to timing freshness, lineage, and external
    promotion policy surfaces.
  - Added governed `TIMING_STATUS_UNSYNCED` diagnostic vocabulary for gateway
    runtime timing-loss degradation.
  - Added tests and a conformance fixture proving soft-accepted risk remains
    filterable without duplicating source payloads.
  - Documented the stack audit, operator-tunable behavior, and ignored local
    generated/cache artifacts.
- Notes: Quarantine remains a policy action, not a schema-level trust/lifecycle
  state. No future domain vocabulary was promoted.
- Verification:
  - `python -m pytest -q gateway\tests\test_timing_freshness.py gateway\tests\test_external_state_promotion.py gateway\tests\test_lineage_semantics.py gateway\tests\test_gateway_smoke.py` -> `43 passed`
  - `python tools\validate_conformance.py --strict` -> `conformance ok`
  - `python -m pytest -q` -> `350 passed, 108 subtests passed`
  - `python tools\validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative --precision-policy --release-manifest --release-package` -> all opt-in suites passed
  - `python tools\validate_examples.py --strict --require-all` -> `overall total=40 passed=40 failed=0 warnings=0`
  - `python tools\validate_release_manifest.py --manifest release\zmeta-release-manifest.yaml` -> `release manifest ok groups=15 artifacts=55`
  - `python tools\validate_release_package.py --manifest release\zmeta-release-manifest.yaml --templates-only` -> `release package ok mode=templates`
  - `python tools\compute_contract_hash.py` -> `contract_hash=46b41356f980305e031a41f9aba72e73c99d616bdf977ba4a0eb0c4dadd9b9c4`
  - `git diff --check` -> passed with normal Windows CRLF conversion warnings

## S1-15C - Semantic Contract Feedback Cleanup

- Status: COMPLETE
- Date completed: 2026-06-08
- Output: `docs/s1_15c_semantic_contract_feedback_cleanup.md`
- Scope: Applied feedback on the risk-governance contract without adding
  runtime behavior or promoting future vocabulary.
- Changes:
  - Revised Section 14 so CoT/TAK ingress is external report evidence unless
    active Section 4.5.1 promotion policy authorizes `STATE_EVENT` output.
  - Strengthened material-risk self-label requirements when diagnostics may not
    travel with accepted data.
  - Clarified degradation effects by event type so confidence-prohibited events
    do not gain top-level confidence.
  - Strengthened operator override requirements for material, command,
    trust, promotion, safety, and external-boundary softening.
  - Added future-only notes for external-report parent evidence,
    `POLICY_ADJUDICATION` diagnostics, and projection-origin/instance metadata.
  - Added conformance classes and example-claim evidence for policy
    adjudication, external promotion, risk filtering, and future projection
    origin.
  - Updated the implementation mapping, semantic delta, and crosswalk rows.
- Notes: `OBSERVATION_EVENT/NETWORK_REPORT`, `SYSTEM_EVENT/POLICY_ADJUDICATION`,
  and projection-origin fields remain future branch work, not valid v1.0
  vocabulary.
- Verification:
  - `python -m pytest -q gateway\tests\test_timing_freshness.py gateway\tests\test_external_state_promotion.py gateway\tests\test_lineage_semantics.py gateway\tests\test_gateway_smoke.py` -> `43 passed`
  - `python -m pytest -q gateway\tests\test_external_state_promotion.py adapters\ingress\cot\test_cot_ingress.py adapters\ingress\jreap\test_jreap_ingress.py adapters\ingress\mavlink\test_mavlink_ingress.py` -> `18 passed`
  - `python tools\validate_conformance_classes.py --manifest conformance\conformance_classes.yaml --claims conformance\claims\example-reference-gateway.yaml conformance\claims\example-core-producer.yaml` -> `conformance classes ok classes=34 claims=2`
  - `python tools\validate_conformance.py --strict` -> `conformance ok`
  - `python -m pytest -q` -> `350 passed, 108 subtests passed`
  - `python tools\validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative --precision-policy --release-manifest --release-package` -> all opt-in suites passed
  - `python tools\validate_examples.py --strict --require-all` -> `overall total=40 passed=40 failed=0 warnings=0`
  - `python tools\validate_release_manifest.py --manifest release\zmeta-release-manifest.yaml` -> `release manifest ok groups=15 artifacts=55`
  - `python tools\validate_release_package.py --manifest release\zmeta-release-manifest.yaml --templates-only` -> `release package ok mode=templates`
  - `python tools\compute_contract_hash.py` -> `contract_hash=3b6c8a264f43b1aa2f36c8a62972e2b523bee46277e03ac7f2de7e124d1c71db`
  - `git diff --check` -> passed with normal Windows CRLF conversion warnings.

## S1-16A - Bad-Event Corpus And Adapter Harness

- Status: COMPLETE
- Date completed: 2026-06-08
- Output: `docs/s1_16a_bad_event_adapter_harness.md`
- Scope: Added opt-in conformance evidence for semantic bad events and
  representative adapter outputs without changing schemas, policy semantics,
  encodings, profile behavior, the semantic contract, or event vocabulary.
- Changes:
  - Added `conformance/bad-events/must-fail.jsonl` and
    `tools/validate_bad_events.py`.
  - Added `conformance/adapter-harness/must-pass.jsonl` and
    `tools/validate_adapter_conformance.py`.
  - Added `--bad-events` and `--adapter-harness` to
    `tools/validate_conformance.py`.
  - Updated KLV ingress to emit `lineage.transform` per adapter template
    guidance.
  - Promoted `ZMETA-ADAPTER` and `ZMETA-COT-PROJECTION` to implemented with
    explicit harness evidence; left broader `ZMETA-SENSOR-ADAPTER` planned.
  - Updated example claims, release manifest governance, crosswalk, tool docs,
    adapter docs, and handoff notes.
- Notes: The adapter harness is representative, not exhaustive. It does not
  certify every native-message variant for every adapter.
- Verification:
  - `python tools\validate_bad_events.py --must-fail conformance\bad-events\must-fail.jsonl` -> `bad-event corpus ok total=9`
  - `python tools\validate_adapter_conformance.py --fixtures conformance\adapter-harness\must-pass.jsonl` -> `adapter conformance ok total=8`

## S1-16B - Kernel Protection Contract Alignment

- Status: COMPLETE
- Date completed: 2026-06-08
- Output: `docs/s1_16b_kernel_protection_contract_alignment.md`
- Scope: Aligned the semantic contract and stack-facing governance docs around
  the standard-protection posture that ZMeta is complete enough to prevent
  semantic corruption without becoming an exhaustive mission ontology.
- Changes:
  - Added `Completeness Without Exhaustiveness` to the semantic contract.
  - Added `Core Semantic Change Threshold` to prevent future core edits unless
    a concrete interoperability ambiguity, implementation failure, safety/audit
    risk, or validated operational requirement cannot be solved through policy,
    profiles, adapters, extension branches, conformance classes, or mission
    logic.
  - Expanded rule classes to `LOCKED`, `TUNABLE`, `ADVISORY`, and
    `FUTURE_EXTENSION`.
  - Updated the implementation mapping, semantic delta, contract-to-stack
    crosswalk, conformance class guide, conformance README, class manifest
    notes, handoff, and S1-16A adapter-harness note.
  - Rebuilt the release manifest and example claim hashes.
- Notes: No schemas, event vocabulary, policy behavior, runtime code, adapters,
  encodings, profile behavior, or future-extension terms were added.
- Verification:
  - `python tools\compute_contract_hash.py` ->
    `semantics_hash=0e3aef770a22120fe905d3d9afe8c860c7f356ec9b5bb45592154742ec9ed18f`,
    `contract_hash=b6f2546b9f56bf021e834e5b0405c58d53ae50e4593d85cc2545e4dedea7140d`
  - `python tools\validate_release_manifest.py --manifest release\zmeta-release-manifest.yaml` ->
    `release manifest ok groups=17 artifacts=59`
  - `python tools\validate_conformance_classes.py --manifest conformance\conformance_classes.yaml --claims conformance\claims\example-reference-gateway.yaml conformance\claims\example-core-producer.yaml` ->
    `conformance classes ok classes=34 claims=2`
  - `python tools\validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative --precision-policy --release-manifest --release-package --bad-events --adapter-harness` ->
    `projection conformance ok total=33`, `extension registry ok entries=56`,
    `conformance classes ok classes=34 claims=2`, `encoding negative ok total=49`,
    `profile precision policy ok total=32`, `bad-event corpus ok total=9`,
    `adapter conformance ok total=8`, `conformance ok`
  - `python -m pytest -q` -> `358 passed, 108 subtests passed`
  - `python tools\validate_examples.py --strict --require-all` ->
    `overall total=40 passed=40 failed=0 warnings=0`
  - `python tools\validate_release_package.py --manifest release\zmeta-release-manifest.yaml --templates-only` ->
    `release package ok mode=templates`
  - `git diff --check` -> passed with normal Windows CRLF conversion warnings

## S1-17A - Kernel Protection Stack Audit

- Status: COMPLETE
- Date completed: 2026-06-08
- Output: `docs/s1_17a_kernel_protection_stack_audit.md`
- Scope: Audited the tracked repository stack against S1-16B kernel protection:
  locked semantics, tunable policy/config boundaries, advisory guidance,
  `FUTURE_EXTENSION` non-claimability, and conformance evidence that protects
  without claiming exhaustive mission coverage.
- Changes:
  - Added full kernel-protection conformance to GitHub CI.
  - Added `make validate-kernel` for the same local validation path.
  - Updated the release checklist and conformance README with the canonical
    full-kernel command.
  - Clarified rule-class posture in `policy/README.md`.
  - Clarified that policy variants are tunable overlays, not semantic
    exceptions, in `configs/policy-variants/README.md`.
  - Updated handoff and worklog notes.
- Findings:
  - Tracked inventory reviewed: 284 files.
  - No live schema, policy YAML, gateway runtime, adapter, encoding, example, or
    conformance-fixture drift was found.
  - Ignored local artifacts include release bundles/zips, smoke output,
    `LOCAL_NOTES.md`, `.gitconfig-local`, Python caches, and pytest cache/output
    folders. These are not tracked or release-governed semantic authority.
- Notes: No schemas, event vocabulary, policy YAML semantics, gateway runtime
  behavior, adapters, encodings, examples, or conformance fixtures were changed.
- Verification:
  - `python tools\validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative --precision-policy --release-manifest --release-package --bad-events --adapter-harness` ->
    `projection conformance ok total=33`, `extension registry ok entries=56`,
    `conformance classes ok classes=34 claims=2`, `encoding negative ok total=49`,
    `profile precision policy ok total=32`, `bad-event corpus ok total=9`,
    `adapter conformance ok total=8`, `conformance ok`
  - `python tools\validate_release_manifest.py --manifest release\zmeta-release-manifest.yaml` ->
    `release manifest ok groups=17 artifacts=59`
  - `python tools\validate_examples.py --strict --require-all` ->
    `overall total=40 passed=40 failed=0 warnings=0`
  - `python -m pytest -q` -> `358 passed, 108 subtests passed`
  - `git diff --check` -> passed with normal Windows CRLF conversion warnings

## S1-18A - Operator Risk Filter Tooling

- Status: COMPLETE
- Date completed: 2026-06-08
- Output: `docs/s1_18a_operator_risk_filter_tooling.md`
- Scope: Added consumer-side filtering for accepted-risk ZMeta streams so
  operators can tune intake posture using existing risk labels without changing
  semantic truth.
- Changes:
  - Added `tools/filter_risk.py`.
  - Added presets for `display`, `fusion`, `state`, `command`, `autonomy`,
    `aar`, and `audit`.
  - Added focused tests in `gateway/tests/test_risk_filter_cli.py`.
  - Documented filter usage in tool, gateway, config, conformance, root README,
    and release checklist surfaces.
  - Updated `ZMETA-RISK-FILTERING` conformance evidence and example
    reference-gateway claim.
  - Added the filter tool to governed release manifest conformance tooling and
    rebuilt release/claim hashes.
- Notes:
  - The filter reads event-side `payload.extensions.risk_adjudication` and
    same-stream `SYSTEM_EVENT/SCHEMA_VIOLATION` diagnostic metrics.
  - It writes passing events unchanged and can write dropped-event reasons to a
    sidecar.
  - No schemas, event vocabulary, policy YAML semantics, gateway runtime
    mutation, adapters, encodings, examples, or future-extension terms were
    added.
- Verification:
  - `python -m pytest -q gateway\tests\test_risk_filter_cli.py` -> `6 passed`
  - `python tools\validate_conformance_classes.py --manifest conformance\conformance_classes.yaml --claims conformance\claims\example-reference-gateway.yaml conformance\claims\example-core-producer.yaml` ->
    `conformance classes ok classes=34 claims=2`
  - `python tools\validate_release_manifest.py --manifest release\zmeta-release-manifest.yaml` ->
    `release manifest ok groups=17 artifacts=60`
  - `python tools\validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative --precision-policy --release-manifest --release-package --bad-events --adapter-harness` ->
    `projection conformance ok total=33`, `extension registry ok entries=56`,
    `conformance classes ok classes=34 claims=2`, `encoding negative ok total=49`,
    `profile precision policy ok total=32`, `bad-event corpus ok total=9`,
    `adapter conformance ok total=8`, `conformance ok`
  - `python tools\validate_examples.py --strict --require-all` ->
    `overall total=40 passed=40 failed=0 warnings=0`
  - `python -m pytest -q` -> `364 passed, 108 subtests passed`
  - `git diff --check` -> passed with normal Windows CRLF conversion warnings

## S1-18B - End-to-End Stack and Runtime Audit

- Status: COMPLETE
- Date completed: 2026-06-08
- Output: `docs/s1_18b_end_to_end_stack_runtime_audit.md`
- Scope: Audited the tracked stack folder by folder against the semantic
  contract and ran a local runtime sweep across validators, examples,
  compatibility checks, gateway self-tests, live UDP workflows, encodings,
  risk filtering, packet-size checks, release-package planning, Docker Compose
  config rendering, MVP bundle build, and extracted bundle smoke tests.
- Cleanup:
  - Hardened `adapters/egress/cot/zmeta_to_cot.py` so direct CoT egress refuses
    malformed `STATE_EVENT` payloads that carry raw observation/evidence fields
    such as `features`, `raw_features`, `modality`, `data_ref`, or `data_refs`.
  - Added focused CoT egress coverage in
    `adapters/egress/cot/test_zmeta_to_cot.py`.
  - Documented the CoT egress precondition in `adapters/egress/cot/README.md`.
  - Added `.tmp/` to `.gitignore` for generated local smoke-test extraction
    directories.
- Findings:
  - No blocking semantic-contract drift or stale tracked file was found after
    the CoT egress hardening.
  - Historical older-version references remain in release notes, checksum
    files, prior audit docs, or compatibility history by design.
  - Ignored local artifacts are expected local state and are not part of the
    governed repo baseline.
  - Direct Docker container boot was left for a future deployment-specific
    audit because live runtime paths were exercised directly and compose configs
    rendered successfully.
- Verification:
  - `python -m pytest -q adapters\egress\cot` -> `9 passed`
  - `python tools\validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative --precision-policy --release-manifest --release-package --bad-events --adapter-harness` ->
    `projection conformance ok total=33`, `extension registry ok entries=56`,
    `conformance classes ok classes=34 claims=2`,
    `encoding negative ok total=49`, `profile precision policy ok total=32`,
    `bad-event corpus ok total=9`, `adapter conformance ok total=8`,
    `conformance ok`
  - `python tools\validate_examples.py --strict --require-all` ->
    `overall total=40 passed=40 failed=0 warnings=0`
  - `python tools\validate_release_manifest.py --manifest release\zmeta-release-manifest.yaml` ->
    `release manifest ok groups=17 artifacts=60`
  - `python tools\validate_release_package.py --manifest release\zmeta-release-manifest.yaml --templates-only` ->
    `release package ok mode=templates`
  - Focused projection, extension-registry, conformance-class,
    encoding-negative, precision-policy, bad-event, and adapter-harness
    validators all passed.
  - All seven example JSONL streams passed strict `v1.1.5` compatibility
    checks.
  - Gateway Profile H, gateway config, and edge config self-tests all passed.
  - Live workflow tools passed Profile H/M/L JSON, Profile H CBOR, Profile L
    compact, Profile H protobuf, command duplicate ACK, state forwarding, and
    CoT output paths.
  - `python tools\measure_packet_size.py --file examples\zmeta-profile-L-examples.jsonl --encodings compact,proto --max-bytes 240 --max-bytes-encoding compact --summary-only` ->
    `COMPACT max=150`, `PROTO max=301`
  - `python tools\filter_risk.py --input examples\zmeta-command-examples.jsonl --preset command --fail-on-drop --quiet` ->
    passed without drops
  - `python tools\compute_contract_hash.py` ->
    `contract_hash=9aa997d264d71575eb24c21ba93935a4d4165a24aef07bae0e6ced7e40949590`
  - `python -m pytest -q` -> `365 passed, 108 subtests passed`
  - `python tools\build_release_package.py --manifest release\zmeta-release-manifest.yaml --output-dir release\package-audit --release-id zmeta-audit-runtime --release-state audit_runtime_sweep --dry-run --no-signatures` ->
    dry-run planned expected release-package outputs
  - `docker compose -f deploy\gateway\docker-compose.yml config` and
    `docker compose -f deploy\edge\docker-compose.yml config` -> rendered
    successfully with local Docker config access warnings only
  - `python release\build_mvp_packages.py --version vci` -> produced edge and
    gateway ZIPs
  - Extracted edge and gateway ZIPs each passed `gateway.py --self-test`

## R1-02 - v1.1.6 Release Publication

- Status: COMPLETE
- Date completed: 2026-06-09 UTC / 2026-06-08 local
- Release URL: `https://github.com/JTC-byte/zmeta-spec/releases/tag/v1.1.6`
- Tag: `v1.1.6`
- Tagged commit: `a42f1b1d538cf2f2318a81203f28d7c656c22ce8`
- Scope: Published the v1.1.6 semantic-risk, kernel-protection,
  adapter-boundary, and runtime validation release after S1-18B.
- Published assets:
  - `zmeta-v1.1.6-dist.zip`
  - `zmeta-edge-v1.1.6.zip`
  - `zmeta-gateway-v1.1.6.zip`
  - `zmeta-release-package-v1.1.6.zip`
  - `zmeta-release-manifest.yaml`
  - `RELEASE_NOTES_v1.1.6.md`
  - `VALIDATION_REPORT_v1.1.6.md`
  - `SHA256SUMS_v1.1.6.txt`
- Notes: No detached `.asc` signatures were attached because no approved
  release signing key/process was available. The published release preserves
  v1.0/v1.1.0 isolation and does not claim literal raw IQ support.

## P1-01 - Post-v1.1.6 Partner Feedback Cleanup

- Status: COMPLETE
- Date completed: 2026-06-09
- Commit: `fe4634b` - `Add post-v1.1.6 risk policy guidance and lint`
- Scope: Addressed partner review feedback after v1.1.6 without changing
  schemas, event vocabulary, policy YAML semantics, release assets, or
  published checksum files.
- Changes:
  - Added current integration guidance for external state promotion metadata in
    `README.md`.
  - Clarified in adapter and policy docs that `external_promotion.trust_ref` is
    a policy-scoped reference, not a signature, credential, or standalone proof
    of authenticity.
  - Strengthened downstream consumer responsibility language for honoring
    `allowed_uses`, `prohibited_uses`, and `policy_decision`, or running an
    equivalent accepted-risk filter.
  - Added `tools/lint_policy_risk_modes.py` and
    `gateway/tests/test_policy_risk_mode_lint.py`.
- Verification:
  - `python tools\lint_policy_risk_modes.py` -> `policy risk mode lint ok`
  - `python -m pytest -q gateway\tests\test_policy_risk_mode_lint.py` ->
    `5 passed`
  - Focused risk/promotion/lineage/timing pytest -> `34 passed`
  - Full kernel conformance -> `conformance ok`
  - `git diff --check` -> passed with normal Windows CRLF conversion warnings
  - `python -m pytest -q` -> `370 passed, 108 subtests passed`
  - GitHub CI on `main` -> success, run `27228915360`
- Decision: This stack is closed for the current downstream integration
  baseline. Use `v1.1.6` for formal release pinning and current `main` for the
  latest guidance/lint baseline.

## P1-02 - Post-v1.1.6 Projection And Registry Hardening

- Status: COMPLETE
- Date completed: 2026-06-10
- Scope: Applied downstream live-use feedback that accepted-risk labels,
  policy use limits, and external-promotion evidence must remain
  machine-checkable through profile projection and future extension registry
  work.
- Changes:
  - Added projection catalog rules for
    `payload.extensions.risk_adjudication` and
    `payload.extensions.external_promotion`.
  - Added profile-projection pass/fail fixtures proving Profile L projection
    preserves accepted-risk labels and compact external-promotion policy,
    trust, lineage, and loop evidence.
  - Added explicit projection failure codes for removed risk labels and removed
    external-promotion evidence.
  - Strengthened `spec/extension-registry.yaml` defaults and
    `tools/validate_extension_registry.py` validation for
    `profile_projection_behavior`, `risk_relevant`,
    `must_preserve_when_used_for_policy`, `security_privacy_notes`, and
    `fixture_references`.
  - Updated `spec/extension-registry.md`,
    `spec/profile-projection-field-catalog.md`, and
    `spec/semantics-contract.md` to align with the implemented registry and
    projection contract.
  - Rebuilt `release/zmeta-release-manifest.yaml` and example claim hashes for
    the current working baseline. Published `v1.1.6` release assets and
    `SHA256SUMS_v1.1.6.txt` remain historical release outputs, not regenerated
    by this post-release hardening pass.
- Verification:
  - `python tools\validate_projection.py --catalog conformance\profile_projection_field_catalog.yaml --must-pass conformance\profile-projection\must-pass.jsonl --must-fail conformance\profile-projection\must-fail.jsonl --quiet` ->
    `projection conformance ok total=37`
  - `python tools\validate_extension_registry.py --registry spec\extension-registry.yaml` ->
    `extension registry ok entries=56`
  - `python tools\validate_release_manifest.py --manifest release\zmeta-release-manifest.yaml` ->
    `release manifest ok groups=17 artifacts=60`
  - `python tools\validate_release_package.py --manifest release\zmeta-release-manifest.yaml --templates-only` ->
    `release package ok mode=templates`
  - `python tools\validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative --precision-policy --release-manifest --release-package --bad-events --adapter-harness` ->
    `projection conformance ok total=37`, `extension registry ok entries=56`,
    `conformance classes ok classes=34 claims=2`, `encoding negative ok
    total=49`, `profile precision policy ok total=32`, `bad-event corpus ok
    total=9`, `adapter conformance ok total=8`, `conformance ok`
  - `python -m pytest -q gateway\tests\test_profile_projection_preservation.py gateway\tests\test_extension_registry.py gateway\tests\test_release_manifest.py gateway\tests\test_conformance_classes.py gateway\tests\test_policy_risk_mode_lint.py` ->
    `64 passed`
  - `python tools\lint_policy_risk_modes.py` -> `policy risk mode lint ok`

## P1-03 - Human And AI Agent Change Governance

- Status: COMPLETE
- Date completed: 2026-06-10
- Scope: Added a formal internal process for human maintainers and AI agents to
  propose, implement, validate, document, and publish changes to the ZMeta
  stack without over-specializing the semantic kernel or bypassing release
  governance.
- Changes:
  - Added `AGENTS.md` as the root quick-start guide for agents and maintainers.
  - Added `docs/zmeta_change_governance.md` with authority order, left/right
    limits, change classes, documentation matrix, versioning rules, validation
    gates, release publication workflow, and human/agent responsibility splits.
  - Added downstream clone guidance that permits local integrations around a
    pinned ZMeta release while classifying local schema, vocabulary, version,
    projection, risk, or command-authority changes as private dialect/fork
    work unless governed and versioned.
  - Linked the process from `README.md`, `release/README.md`, and
    `RELEASE_CHECKLIST.md`.
  - Added a governed `process_governance` release-manifest artifact group and
    top-level `process_governance_hash`.
  - Updated `spec/release-hash-policy.md`,
    `tools/build_release_manifest.py`, and
    `tools/validate_release_manifest.py` to include the process governance
    category.
  - Rebuilt `release/zmeta-release-manifest.yaml` and example claim hashes for
    the current working baseline.
- Verification:
  - `python tools\build_release_manifest.py --release-id zmeta-v1.1.6 --release-name "ZMeta v1.1.6" --release-status formal_release --release-date 2026-06-09 --git-commit a42f1b1d538cf2f2318a81203f28d7c656c22ce8 --branch main --update-claims` ->
    wrote `release/zmeta-release-manifest.yaml`
  - `python tools\validate_release_manifest.py --manifest release\zmeta-release-manifest.yaml` ->
    `release manifest ok groups=18 artifacts=62`
  - `python tools\validate_release_package.py --manifest release\zmeta-release-manifest.yaml --templates-only` ->
    `release package ok mode=templates`
  - `python tools\validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative --precision-policy --release-manifest --release-package --bad-events --adapter-harness` ->
    `projection conformance ok total=37`, `extension registry ok entries=56`,
    `conformance classes ok classes=34 claims=2`, `encoding negative ok
    total=49`, `profile precision policy ok total=32`, `bad-event corpus ok
    total=9`, `adapter conformance ok total=8`, `conformance ok`
  - `python -m pytest -q gateway\tests\test_release_manifest.py gateway\tests\test_release_package.py gateway\tests\test_profile_projection_preservation.py gateway\tests\test_extension_registry.py` ->
    `51 passed`
  - After the downstream clone guidance refresh,
    `python -m pytest -q gateway\tests\test_release_manifest.py gateway\tests\test_release_package.py` ->
    `27 passed`
  - `python -m pytest -q` -> `375 passed, 108 subtests passed`
  - `git diff --check` -> passed with normal Windows CRLF conversion warnings

## R1-03 - v1.1.7 Stack Audit And Release

- Status: COMPLETE
- Date completed: 2026-06-10
- Release URL: `https://github.com/JTC-byte/zmeta-spec/releases/tag/v1.1.7`
- Tag: `v1.1.7`
- Tagged commit: `e7b014f` - `Prepare v1.1.7 release`
- GitHub CI: run `27246838717` passed for `main` push on 2026-06-10.
- Scope: Audited the full tracked stack for stale current-release references,
  ignored local release residue, tracked-source secret risk, generated release
  artifact residue, and release-target drift; promoted the post-v1.1.6
  projection, registry, policy-risk lint, process governance, and downstream
  clone compatibility work into the v1.1.7 patch release.
- Outputs:
  - `docs/r1_03_v1_1_7_stack_audit_release.md`
  - `release/RELEASE_NOTES_v1.1.7.md`
  - `release/VALIDATION_REPORT_v1.1.7.md`
  - `release/SHA256SUMS_v1.1.7.txt`
  - `release/zmeta-release-manifest.yaml`
  - `zmeta-v1.1.7-dist.zip`
  - `zmeta-edge-v1.1.7.zip`
  - `zmeta-gateway-v1.1.7.zip`
  - `zmeta-release-package-v1.1.7.zip`
- Audit:
  - Active current-release references and compatibility defaults now target
    v1.1.7.
  - Historical v1.1.5/v1.1.6 release notes, validation reports, checksums, and
    audit docs remain intentionally preserved.
  - Ignored local generated directories `release/bundles/`,
    `release/smoke-edge/`, `release/smoke-gateway/`, and
    `release/package-v1.1.6/` were confirmed untracked and removed before
    rebuilding v1.1.7 artifacts.
  - Tracked-source scans found no secret-like filenames, private key blocks,
    token markers, credential markers, or tracked release ZIP/signature residue.
- Verification:
  - `python tools\validate_release_manifest.py --manifest release\zmeta-release-manifest.yaml` ->
    `release manifest ok groups=18 artifacts=62`
  - `python tools\validate_release_package.py --manifest release\zmeta-release-manifest.yaml --templates-only` ->
    `release package ok mode=templates`
  - `python tools\validate_examples.py --strict --require-all` ->
    `overall total=40 passed=40 failed=0 warnings=0`
  - `python tools\validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative --precision-policy --release-manifest --release-package --bad-events --adapter-harness` ->
    `projection conformance ok total=37`, `extension registry ok entries=56`,
    `conformance classes ok classes=34 claims=2`, `encoding negative ok
    total=49`, `profile precision policy ok total=32`, `bad-event corpus ok
    total=9`, `adapter conformance ok total=8`, `conformance ok`
  - Focused projection, registry, conformance-class, encoding-negative,
    precision-policy, bad-event, adapter-harness, and policy-risk lint
    validators passed.
  - All example streams passed `python tools\check_compat.py --target v1.1.7
    --strict`.
  - Gateway self-tests passed for Profile H, `configs/gateway-config.json`, and
    `configs/edge-config.json`.
  - End-to-end workflow checks passed for Profile H, Profile M command/system,
    Profile L, CBOR, compact, and protobuf variants after rerunning sequentially
    with unique ports to avoid local UDP port collisions.
  - Live gateway tests passed for Profile H JSON, Profile L compact, and
    Profile H protobuf paths.
  - Docker Compose gateway and edge config rendering passed with local Docker
    config access warnings.
  - `python -m pytest -q` -> `375 passed, 108 subtests passed`
  - `python tools\validate_release_package.py --manifest release\zmeta-release-manifest.yaml --package-dir release\package-v1.1.7` ->
    `release package ok mode=package`
  - `python release\sign_release_artifacts.py --version v1.1.7 --write-checksums --verify-checksums` ->
    `checksums ok: SHA256SUMS_v1.1.7.txt`
  - `git diff --check` -> passed with normal Windows CRLF conversion warnings
- Signature status: No detached `.asc` signatures were generated because no
  approved local signing identity was provided. Integrity is covered by
  `SHA256SUMS_v1.1.7.txt` and the structured release manifest.

## P1-04 - Bearing Reference-Frame Integrity Pass

- Status: COMPLETE
- Date completed: 2026-06-11
- Branch: `worktree-bearing-frame-fixes` (10 commits on top of `develop`)
- Change class: Class B governed baseline (contract section 6.4, v1.1.0
  schema, extension registry, conformance corpora, adapter-harness validator,
  release manifest/claims) with Class C adapter/runtime fallout (kraken, moth,
  signalhunter, mavlink, gateway runtime guards).
- Scope: Closed the bearing reference-frame ambiguity. Array-relative DOA
  mislabeled as canonical true-north bearing was schema-valid and
  machine-undetectable, and several adapters fabricated bearings, SNR,
  headings, or positions instead of omitting unavailable data.
- What changed:
  - `spec/semantics-contract.md` section 6.4 is now normative: canonical
    `payload.bearing.az_deg` SHALL be degrees true north; sensor-native
    frames must convert or omit; v1.0 producers may carry
    `quality.bearing_frame`/`quality.heading_source` provenance.
  - `schema/zmeta-event-1.1.0.schema.json` adds optional `bearing.frame`
    with single-value enum `["TRUE_NORTH"]`; the locked v1.0 schema is
    untouched and still rejects the `frame` key.
  - `spec/extension-registry.yaml` adds the experimental `BEARING_FRAME`
    entry (category `observation_feature_contract`).
  - `conformance/bad-events/must-fail.jsonl` adds
    `observation-bearing-frame-mislabeled` (corpus total 10).
  - `tools/validate_adapter_conformance.py` adds the per-fixture
    `expected_values` value-pinning mechanism (1e-6 numeric tolerance,
    `ADAPTER_EXPECTED_VALUE_MISSING`/`ADAPTER_EXPECTED_VALUE_MISMATCH`,
    and a boolean type guard so a boolean pin never matches numeric output).
  - `conformance/adapter-harness/must-pass.jsonl` pins the kraken rotation
    math (doa 123.4 + heading 90.0 -> az 213.4) and adds a no-heading
    convert-or-omit fixture (harness total 9).
  - Kraken adapter 1.1.0: keyword-only `platform_heading_deg` /
    `array_offset_deg` / `heading_source`; emits true-north bearing as
    `(doa + heading + offset) % 360` with provenance, omits the canonical
    bearing without a heading, always carries raw DOA in
    `features.doa_array_relative_deg`, and no longer fabricates CSV
    `quality.snr_db`.
  - Moth adapter 1.1.0: serial/custom-MAVLink omnidirectional paths no
    longer fabricate `az_deg 0.0` / `angular_error_deg 180.0`; replay omits
    bearings absent from input; tunnel/replay measured bearings emit
    canonical `payload.bearing` only when callers explicitly assert
    `bearing_frame="TRUE_NORTH"`, otherwise raw unknown-frame bearings are
    preserved under explicit `features.bearing_frame_unknown_*` keys.
  - SignalHunter 1.0.1: gradient LOBs assert `TRUE_NORTH`/`GPS_COURSE`
    (true north by geodesic construction). MAVLink 1.1.0: `hdg=65535`,
    absent, or present without explicit `heading_frame="TRUE_NORTH"` omits
    canonical `payload.heading_deg`; unasserted known headings are preserved
    as `payload.quality.mavlink_hdg_frame_unknown_deg`.
  - Runtime guards: MAVLink platform state returns `None` instead of
    fabricating a null-island `(0, 0)` TRACK_STATE; gateway gained opt-in
    `warn_datagram_bytes` oversize-datagram observability (default 0 =
    disabled, send behavior unchanged); `ProducerRateLimiter` purges stale
    windows without changing accept/reject decisions.
  - Closeout review fixes: the kraken rotation-proof test now loads the
    `kraken-csv-rf-observation` corpus entry by name instead of duplicating
    it inline, and the harness validator gained the boolean expected-value
    type guard with a focused test.
  - Docs: CHANGELOG, schema README, adapter READMEs, configs README,
    `tools/README.md`, `conformance/adapter-harness/README.md`, this
    worklog, and the handoff updated; release manifest and example claim
    hashes regenerated.
- New deferred issues at P1-04 closeout: D-013 (timing-freshness
  negative-age clamp) and D-014 (compact codec unknown integer payload keys)
  recorded below as verified-but-deferred findings needing a maintainer
  semantics decision. S1-19 later closed both findings on current `main`.
  Two follow-up notes recorded in the handoff: unhandled `OSError` on
  oversize outgoing UDP datagrams, and ingress adapters fabricating
  `lineage.based_on` with fresh random UUIDv7 values.
- Verification (2026-06-11, macOS, Python 3.12):
  - `python3.12 tools/build_release_manifest.py --release-id zmeta-v1.1.7 --release-name "ZMeta v1.1.7" --release-status formal_release --release-date 2026-06-10 --branch main --update-claims` -> manifest and claims rebuilt
  - `python3.12 tools/validate_release_manifest.py --manifest release/zmeta-release-manifest.yaml` -> `release manifest ok groups=18 artifacts=62`
  - `python3.12 tools/validate_release_package.py --manifest release/zmeta-release-manifest.yaml --templates-only` -> `release package ok mode=templates`
  - `python3.12 tools/validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative --precision-policy --release-manifest --release-package --bad-events --adapter-harness` -> `projection conformance ok total=37`, `extension registry ok entries=57`, `conformance classes ok classes=34 claims=2`, `encoding negative ok total=49`, `profile precision policy ok total=32`, `bad-event corpus ok total=10`, `adapter conformance ok total=9`, `conformance ok`
  - `python3.12 -m pytest -q` -> `430 passed, 108 subtests passed`
  - `git diff --check` -> clean

## P1-04R - Partner Review Frame-Gap Closure

- Status: COMPLETE
- Date completed: 2026-06-12
- Branch: `review/pr2-frame-fixes` (local review branch on top of PR #2)
- Change class: Class C adapter behavior and tests, with governed docs and
  release-manifest refresh because manifest-listed artifacts changed.
- Scope: Closed the two adoption blockers found during review of PR #2:
  Moth tunnel/replay bearings and MAVLink `hdg` values documented an unknown
  reference frame but still emitted canonical ZMeta bearing/heading fields.
- What changed:
  - `translate_tunnel_payload()` and `translate_json_replay()` now omit
    canonical `payload.bearing` by default for Moth tunnel/replay inputs whose
    frame is not asserted. The native values are preserved under explicit
    `features.bearing_frame_unknown_*` keys.
  - Moth tunnel/replay callers may pass `bearing_frame="TRUE_NORTH"` only when
    upstream ICD or deployment configuration guarantees a true-north bearing.
    In that mode the adapter emits canonical `payload.bearing` and records
    `quality.bearing_frame = "TRUE_NORTH"`.
  - `translate_platform_state()` now omits canonical `payload.heading_deg` for
    known MAVLink `hdg` values unless the caller passes
    `heading_frame="TRUE_NORTH"`. Unasserted headings are preserved as
    `payload.quality.mavlink_hdg_frame_unknown_deg`.
  - MAVLink callers may pass `heading_source` with the true-north assertion;
    otherwise the adapter records
    `MAVLINK_GLOBAL_POSITION_INT_TRUE_NORTH`.
  - Moth/MAVLink README guidance, adapter tests, CHANGELOG, handoff, and this
    worklog were updated; `release/zmeta-release-manifest.yaml` was rebuilt.
- Verification (2026-06-12, Windows, Python):
  - `python -m pytest -q adapters\ingress\moth\test_moth_ingress.py adapters\ingress\mavlink\test_mavlink_ingress.py` -> `29 passed`
  - `python tools\validate_adapter_conformance.py --quiet` -> `adapter conformance ok total=10`
  - `python tools\build_release_manifest.py --release-id zmeta-v1.1.7 --release-name "ZMeta v1.1.7" --release-status formal_release --release-date 2026-06-10 --branch main --update-claims` -> manifest rebuilt
  - `python tools\validate_release_manifest.py --manifest release\zmeta-release-manifest.yaml` -> `release manifest ok groups=18 artifacts=62`
  - `python tools\validate_release_package.py --manifest release\zmeta-release-manifest.yaml --templates-only` -> `release package ok mode=templates`
  - `python tools\validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative --precision-policy --release-manifest --release-package --bad-events --adapter-harness` -> `projection conformance ok total=37`, `extension registry ok entries=57`, `conformance classes ok classes=34 claims=2`, `encoding negative ok total=49`, `profile precision policy ok total=32`, `bad-event corpus ok total=10`, `adapter conformance ok total=10`, `conformance ok`
  - `python -m pytest -q` -> `435 passed, 108 subtests passed`
  - `git diff --check` -> clean; Git reported normal Windows LF-to-CRLF working-copy warnings.

## R1-04 - v1.1.8 Bearing-Frame Integrity Release

- Status: COMPLETE
- Target release date: 2026-06-12
- Target tag: `v1.1.8`
- Change class: Class E release publication for the adopted P1-04/P1-04R
  governed baseline and runtime/reference changes.
- Scope: Publish the partner bearing-frame integrity stack and local
  frame-gap closure as the current formal release baseline. Release artifacts
  include the source distribution, edge bundle, gateway bundle, no-signature
  release package, release manifest, release notes, validation report, and
  `SHA256SUMS_v1.1.8.txt`.
- Semantic boundary:
  - v1.0 schema remains locked and unchanged.
  - v1.1.0 `bearing.frame` remains optional and single-valued.
  - Unknown-frame Moth bearings and MAVLink headings are no longer canonical
    by default; explicit `TRUE_NORTH` assertions are required.
  - At v1.1.8 release publication time, D-013 and D-014 remained deferred
    for maintainer semantics decisions. S1-19 later closed both findings on
    current `main`.
- Validation: final command output is recorded in
  `release/VALIDATION_REPORT_v1.1.8.md`.
  Summary: release manifest, package templates, strict examples, full kernel
  conformance, focused validators, policy-risk lint, full pytest, gateway
  self-tests, packet-size budget, risk filter, compatibility checks,
  end-to-end workflows, live gateway checks, Docker Compose config rendering,
  package validation, checksum generation/verification, and whitespace checks
  passed. Docker reported local access warnings for
  `C:\Users\User\.docker\config.json` during config rendering, but both
  compose commands exited successfully.

## R1-04A - v1.1.8 Post-Release Reference Cleanup

- Status: COMPLETE
- Date completed: 2026-06-12
- Pushed cleanup commit: `9fc526e` - `Align current-release references with
  v1.1.8`
- Change class: Docs/advisory plus CI compatibility-target alignment.
- Scope: Full-stack audit found current-facing `v1.1.7` drift after the
  v1.1.8 release. Updated active guidance and examples in `README.md`,
  `tools/README.md`, `docs/zmeta_professional_overview.md`, the handoff and
  worklog notes, `.github/workflows/ci.yml`, and
  `gateway/tests/test_check_compat_cli.py` to use `v1.1.8`.
- Boundary: Historical v1.1.7 release notes, validation report, checksum
  manifest, and audit records were intentionally left unchanged. No schemas,
  policy YAML, adapters, runtime code, release package assets, tags,
  signatures, or published checksum files were changed.
- Verification:
  - `python tools\validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative --precision-policy --release-manifest --release-package --bad-events --adapter-harness` -> `conformance ok`
  - `python -m pytest -q` -> `435 passed, 108 subtests passed`
  - `python tools\validate_examples.py --strict --require-all` -> `overall total=40 passed=40 failed=0 warnings=0`
  - `python tools\validate_release_manifest.py --manifest release\zmeta-release-manifest.yaml` -> `release manifest ok groups=18 artifacts=62`
  - `python tools\validate_release_package.py --manifest release\zmeta-release-manifest.yaml --templates-only` -> `release package ok mode=templates`
  - `python tools\validate_release_package.py --manifest release\zmeta-release-manifest.yaml --package-dir release\package-v1.1.8` -> `release package ok mode=package`
  - `python release\sign_release_artifacts.py --version v1.1.8 --verify-checksums` -> `checksums ok: SHA256SUMS_v1.1.8.txt`
  - `python -m pytest -q gateway\tests\test_check_compat_cli.py` -> `4 passed`
  - All seven `examples/*.jsonl` streams passed `python tools\check_compat.py --target v1.1.8 --strict`.
  - End-to-end workflow, live gateway, packet-size, risk-filter, gateway
    self-test, and Docker Compose config checks passed during the audit.
    Docker Compose emitted only the known local
    `C:\Users\User\.docker\config.json` access warning while exiting 0.
  - `git diff --check` -> clean with normal Windows LF-to-CRLF warnings.

## S1-19 - Timing Negative-Age And Compact Unknown-Key Closure

- Status: COMPLETE
- Date completed: 2026-06-12
- Change class: Governed baseline plus runtime/reference conformance
  alignment.
- Scope: Close D-013 and D-014 instead of deferring them.
- D-013 implementation:
  - Added `TIMING_STATUS_AGE_NEGATIVE` to governed diagnostic vocabulary,
    v1.0/v1.1.0 SCHEMA_VIOLATION reason-code enums, policy allowlists, and
    compact reason-code mapping.
  - Added `max_negative_age_ms` and `negative_age_mode` to
    `policy/timing-freshness.yaml`; the reference default warns beyond
    profile tolerance and still allows deployments to reject or degrade.
  - Updated timing freshness validation to compare raw event-vs-TIME_STATUS
    age, emit the new timing risk label beyond tolerance, and avoid clamping
    negative age to zero.
  - Added focused tests plus a core conformance must-fail fixture with
    TIME_STATUS preload.
- D-014 implementation:
  - Added compact spec text requiring unknown integer keys in governed compact
    maps to fail decode.
  - Updated `zmeta_compact.py` to reject unknown integer keys while preserving
    string extension keys.
  - Added a compact encoding-negative generated fixture for unknown integer
    payload keys.
- Boundary: This is a current-main governed change after v1.1.8 publication.
  It does not rewrite historical v1.1.8 release notes, validation report,
  GitHub release assets, or `SHA256SUMS_v1.1.8.txt`.
- Verification: focused timing, policy lint, encoding roundtrip,
  encoding-negative, reason-code, and strict conformance checks passed before
  manifest regeneration.

## S1-20 - Industry Sharing And Open-Specification IP Posture

- Status: COMPLETE
- Date completed: 2026-06-12
- Change class: Advisory documentation plus governed process-manifest coverage.
- Scope: Make the public sharing posture explicit before broader industry
  conversations.
- What changed:
  - Added `IP_POLICY.md` for Apache-2.0 baseline limits, open-specification
    intent, contributor authority, public feedback boundaries, and defensive
    publication references.
  - Added `CONTRIBUTING.md` with Apache-2.0 contribution default, `Not a
    Contribution` handling, DCO-style sign-off guidance, semantic boundaries,
    and validation expectations.
  - Added `CONFORMANCE.md` defining ZMeta-conformant, compatible, derived,
    private dialect, and experimental extension claims.
  - Added `TRADEMARK.md` with advisory name-use guidance for compatibility and
    conformance statements.
  - Added `docs/zmeta_defensive_publication.md` as a public technical
    disclosure of the open architecture: event-family separation, semantic
    authority, version dispatch, timing/lineage/confidence, accepted risk,
    producer authority, profile projection, units/geodesy/reference frames,
    command safety, encoding projections, release hashes, and adapters.
  - Linked the new posture from README, AGENTS, change governance, release
    README, handoff, and changelog.
  - Added the new docs to `process_governance` release-manifest coverage.
- Boundary: Advisory process/governance change only. This does not create legal
  advice, a formal patent covenant, a trademark registration, standards-body
  approval, schema changes, policy behavior changes, event vocabulary changes,
  or release publication changes.
- Recommended next step before broad industry push: attorney review for formal
  defensive publication venue, trademark filing, contributor agreement choice,
  and any standards-body patent policy.

## S1-21 - v1.1.8 Adapter Upgrade And Frame-Provenance Clarification

- Status: COMPLETE
- Date completed: 2026-06-12
- Change class: Advisory documentation plus semantic-contract clarification.
- Scope: Incorporate post-release feedback on v1.1.7/v1.1.8 hardening.
- What changed:
  - Added current-main README upgrade guidance that Moth tunnel/replay
    bearings and MAVLink headings require explicit `TRUE_NORTH` assertions
    before canonical emission, Kraken emits no canonical bearing without
    heading compensation, and Kraken CSV no longer fabricates `quality.snr_db`.
  - Added adapter overview guidance for frame assertions and anti-fabrication.
  - Clarified semantics-contract section 6.4 so `bearing.frame`,
    `quality.bearing_frame`, and `quality.heading_source` are treated as
    producer/configuration provenance, not independent proof of calibration,
    authenticity, or correctness.
  - Recorded the frame-provenance trust boundary as future trust/PNT/integrity
    work rather than a current release blocker.
- Boundary: Documentation and contract clarification only. No schema, policy,
  adapter runtime, event vocabulary, or published v1.1.8 release artifact
  changes.

## S1-22 - Final Baseline Audit And Closeout Notes

- Status: COMPLETE
- Date completed: 2026-06-12
- Pushed cleanup commit: `beffed3` - `Finalize baseline audit guidance cleanup`
- Final pushed audit closeout commit: `c814d95` - `Record final baseline audit
  closeout`
- Change class: Docs/advisory audit closeout plus current-main manifest/claim
  hash refresh for a process-governance guidance correction.
- Scope: Perform one final full inspection of the current stack before moving
  future work to roadmap-only status. The audit covered tracked inventory,
  ignored/local residue, stale current-facing release references, TODO/FIXME
  style markers, secret/key markers, generated-artifact tracking risk,
  semantic/governance alignment, conformance surfaces, package/build tooling,
  runtime smoke paths, Docker Compose config rendering, and GitHub queue/CI
  status.
- Cleanup performed:
  - Corrected the adapter `check_compat` example to target `v1.1.8`.
  - Corrected the change-governance release-manifest rebuild example to target
    `v1.1.8`.
  - Rebuilt `release/zmeta-release-manifest.yaml` and example claim hashes
    because `docs/zmeta_change_governance.md` is a manifest-covered
    process-governance artifact.
  - Recorded the audit result in `CHANGELOG.md`, this worklog, the handoff,
    and ignored `LOCAL_NOTES.md`.
- Validation summary:
  - Full governed kernel gate passed: projection `37`, extension registry `57`,
    conformance classes `34` with `2` claims, encoding-negative `50`,
    precision policy `32`, bad-event corpus `10`, adapter harness `10`, and
    final `conformance ok`.
  - Strict examples passed: `40/40`.
  - Release manifest passed: `groups=18 artifacts=67`.
  - Release package templates and a throwaway no-signature package under
    `.tmp/audit-package-v1.1.8-20260612` both validated.
  - Full pytest passed: `442 passed, 110 subtests passed`.
  - End-to-end workflow checks passed for H/M/L and command/system paths after
    rerunning profile checks sequentially on separate ports; the first parallel
    attempt hit expected localhost UDP port conflicts.
  - Live gateway smoke checks passed for JSON, CBOR, compact, and protobuf
    paths.
  - Focused validators for projection, extension registry, conformance
    classes, bad events, adapter harness, encoding-negative, precision policy,
    risk-mode lint, compatibility, packet size, schema validation, conversion,
    and contract hash computation passed.
  - Source, edge, and gateway bundle builders completed; generated zips and
    bundle directories remain ignored local build outputs.
  - Docker Compose config rendering passed for `gateway/docker-compose.yml`,
    `deploy/edge/docker-compose.yml`, and `deploy/gateway/docker-compose.yml`;
    Docker reported only local `C:\Users\User\.docker\config.json` access
    warnings.
  - GitHub PR and issue queues returned no open items. GitHub CI passed for
    `c814d95` as run `27447655568`.
  - `git diff --check` passed and final `git status --short --branch` was
    clean against `origin/main`.
- Boundary: No schemas, policy behavior, adapter/runtime behavior, event
  vocabulary, release tags, GitHub release assets, detached signatures, or
  published `SHA256SUMS_v1.1.8.txt` were changed. Remaining work is future
  roadmap only: D-003 versioned semantic branch planning, real sensor-capture
  adapter breadth, release-authority signatures/Sigstore process, and broader
  deployment/container runtime coverage.

## S1-23 - README-Linked Documentation Freshness Audit

- Status: COMPLETE
- Date completed: 2026-06-18
- Change class: Docs/advisory freshness audit.
- Scope: Audit root README-linked documentation and adjacent detail docs for
  stale install guidance, broken relative links, stale release/current-main
  wording, rogue untracked files, and generated/local output tracking risk.
- Cleanup performed:
  - Refreshed `spec/installation-guide.md` to direct new installs to the
    maintained `configs/` templates, document wizard output as a local option,
    cover Docker Compose deployment, map-pack replacement flags, validation
    gates, and release-package boundaries.
  - Corrected stale handoff/worklog/local-note references that treated
    `beffed3` as the latest final closeout commit; the current pushed
    integration closeout is `c814d95` with CI run `27447655568`.
  - Recorded this audit in `CHANGELOG.md`, this worklog, the handoff, and
    ignored `LOCAL_NOTES.md`.
- Audit results:
  - Tracked Markdown/TXT relative-link audit returned no missing paths.
  - `git ls-files --others --exclude-standard` returned no rogue untracked
    files.
  - `git ls-files` found no tracked generated release bundle/package/zip or
    cache outputs from the ignored local residue set.
  - `git check-ignore -v` confirmed expected ignore coverage for
    `LOCAL_NOTES.md`, `.tmp/`, `release/dist/`, `release/bundles/`,
    `release/package-v1.1.8/`, release zip outputs, and `__pycache__/`.
- Boundary: Documentation-only. No schemas, policy behavior, adapters,
  runtime code, event vocabulary, release tags, GitHub release assets, detached
  signatures, published checksum files, or release-manifest-governed artifacts
  were changed.

## R1-05 - v1.1.9 Documentation Freshness Release

- Status: COMPLETE
- Date completed: 2026-06-18
- Target tag: `v1.1.9`
- Change class: Release/publication for post-v1.1.8 current-main docs,
  governance, timing/compact, and release-hygiene work.
- Scope: Publish the accumulated post-v1.1.8 current-main changes as a formal
  patch release: README-linked documentation freshness, maintained install
  template guidance, stale closeout-reference cleanup, advisory
  IP/contribution/conformance/name-use posture, D-013 negative TIME_STATUS age
  diagnostics, D-014 compact unknown-integer-key rejection, adapter
  frame-provenance clarification, release tooling default updates, and release
  package/checksum artifacts.
- Release artifacts:
  - `release/RELEASE_NOTES_v1.1.9.md`
  - `release/VALIDATION_REPORT_v1.1.9.md`
  - `release/SHA256SUMS_v1.1.9.txt`
  - `release/zmeta-release-manifest.yaml`
  - `zmeta-v1.1.9-dist.zip`
  - `zmeta-edge-v1.1.9.zip`
  - `zmeta-gateway-v1.1.9.zip`
  - `zmeta-release-package-v1.1.9.zip`
- Validation summary:
  - Release manifest validation: `release manifest ok groups=18 artifacts=67`.
  - Release package templates and generated package validation passed.
  - Strict examples passed: `40/40`.
  - Full governed kernel gate passed with projection `37`, extension registry
    `57`, conformance classes `34` with `2` claims, encoding-negative `50`,
    precision policy `32`, bad-event corpus `10`, adapter harness `10`, and
    final `conformance ok`.
  - Full pytest passed: `442 passed, 110 subtests passed`.
  - Gateway self-tests, Profile L packet-size check, risk-filter command
    preset, compatibility checks, workflow/live-gateway checks, Docker Compose
    config rendering, checksum generation/verification, tracked-doc link audit,
    and rogue-file/generated-residue checks passed.
- Boundary: No private keys, credentials, tokens, certificates with private
  material, signing secrets, or detached signatures are included. Detached
  signatures remain future work until an approved signing key/process is
  supplied. Historical `v1.1.8` release notes, validation report, assets, and
  `SHA256SUMS_v1.1.8.txt` remain unchanged.

## Resume-note entries archived 2026-08-13

Dated resume-note entries from 2026-08-03 back through the v1.1.9 era,
moved verbatim from `zmeta_refinement_worklog.md` (retention pass,
2026-08-13). The live resume note keeps the current release family
(2026-08-10 onward).

- **2026-08-03 (session closeout; fire shifts to the deployment).** The
  post-publish closeout verified the final state by hand: tree clean and
  synced at the records commit, CI green on main and develop, the battery
  re-run green at the closeout tree, no running containers (three exited
  audit containers from the readiness-audit cycle were removed; the two
  keep-or-prune artifacts, the `backup-pre-scrub` branch and the
  `.tmp/review-pr-2` worktree, still stand for the maintainer). The
  session's live-run guidance is condensed into
  `docs/zmeta_live_test_checklist.md` section E as a pre-flight card and a
  break-report card, so it survives as a standing artifact rather than a
  conversation. Maintainer direction recorded: ZMeta runs live as
  published and enters maintenance mode; field telemetry drives the next
  scoped waves; the maintainer's development focus moves to the Praesens
  deployment. The below-floor queue, the section C gates (SITL before
  live GCS-originated tasking; the TAK render check), and the doctrine
  log all stand unchanged.
- **2026-08-03 (v1.1.20 published).** The tag, upload and publish ran at
  the maintainer's direction after an independent verification session,
  fresh eyes separate from the range's authors, re-derived the prepared
  cut's claims: the panel register re-executed end to end with every
  entry matching its expected output; the checksum errata confirmed on
  all sixteen rows by two independent methods with the generated table
  reproducing byte-identically; a first-run stranger walk through the
  README, tools reference, deployment checklist and release verification
  walkthrough with every documented command working as written; battery
  1727 passed plus 1081 subtests at `887446f`, kernel gates exit 0,
  examples 51/51, release package valid in package mode, checksums
  verified raw and normalized. The annotated tag `v1.1.20` was then
  created on `887446f`, pushed, and the GitHub release published with
  eight assets; the published assets were downloaded back and every
  checksum verified against the published `SHA256SUMS_v1.1.20.txt`.
  `develop` fast-forwarded to `main`. Three below-floor observations
  from the verification are queued, deliberately not fixed pre-tag: the
  combined conformance command prints no success line for its
  `--release-manifest` and `--release-package` flags (both run and fail
  loudly; success is silent, indistinguishable from not-wired-up); the
  dist and release-package zip builders copy working-tree text with the
  builder machine's line endings while the edge and gateway builders
  normalize (the v1.1.20 checksums match the actual published bytes, so
  this release is unaffected; it is the signer defect's class one layer
  deeper); and the errata prose glosses absent-manifest tags as "already
  matched" where the generator actually skips them as nonexistent. One
  hygiene act pre-tag: a stray gitignored `__pycache__` bytecode file
  left by the red-proof testing was cleared.
- **2026-08-03 (phase 5, panel and fix wave).** The cut opened per the
  playbook ordering. Currency pass first (`869af74`): manifest rebuilt
  with the explicit v1.1.20 identity, eighteen stale surfaces flipped by
  the currency suite's enumeration, governance sentence regenerated. Then
  the whole-range fresh-eyes panel over v1.1.19..HEAD, 45 commits as one
  surface: eight independent cold lenses, dedup against the fix floor,
  one adversarial verifier per floor-passing finding, 23 subagents in
  all. Nineteen raw findings, eight confirmed, four downgraded but real,
  two refuted with evidence (one refuter re-ran the battery in a worktree
  at the checkpoint commit and reproduced the disputed 1720 exactly, so
  that record stands), three minors. The panel also confirmed the range's
  load-bearing positives cold: the locked v1.0 schema byte-identical
  across the range, the A1-02 vocabulary spelled consistently everywhere,
  the checksum errata table reproducing byte-for-byte. Fix wave landed
  red-first (`050704a`), then the attack pass on the fix wave found four
  defects in the fixes themselves, all fixed in the same commit; the
  full finding-by-finding record with standalone verification commands
  is `docs/v1_1_20_precut_panel_register.md`, written so a separate
  session can re-run every check without this session's context.
  Notable for the AAR: the attack pass caught the lesson-applied-once
  class occurring inside the wave that was fixing other instances of it
  (the citation fix covered the two named surfaces and missed four
  sibling instances), and the content-currency guard caught the panel
  register itself as an unpinned compat-target carrier the same day it
  was written. Battery at the fix-wave tip: 1726 passed plus 1081
  subtests, gates exit 0, examples 51/51, the one red being
  test_release_artifact_completeness by design until the release
  artifacts exist. Remaining in phase 5: release notes, validation
  report, manifest last, package-mode validation and checksum
  verification before any tag; tag, sign, publish are the maintainer's.
  Maintainer direction for after the cut: verify local, develop, and
  main match (develop is 192 commits behind main, zero ahead, a clean
  fast-forward; the three other remote branches are fully merged into
  main and are keep-or-prune calls listed for him).
- **2026-08-03 (checkpoint closeout).** Final state verified by hand: main
  and origin synced at 1714866, CI green on the last two pushes, kernel
  gate all flags exit 0, examples 51/51, pytest 1720 passed plus 1081
  subtests with the exit code checked, all lints and validators exit 0, no
  stray worktrees, branches or containers. The v1.1.20 campaign stands at
  four phases complete: the governed waves, the boundary fixes, the
  validations including the first independent-implementation acceptance,
  and the documentation refresh from a certified green state. The whole
  remaining board is phase 5, the cut: currency pass first, the
  whole-range fresh-eyes panel over the roughly twenty-three commits since
  v1.1.19 [Corrected 2026-08-03, found by the panel it was sizing: the
  range v1.1.19..HEAD held 44 commits when this was written and 45 at
  panel time, roughly double the stated figure; the panel was scoped to
  the measured range, not this sentence], package validation, release
  notes, manifest last, and the tag,
  sign and publish steps at the maintainer's direction. Deliberately held
  for a fresh session so the heaviest review of the cycle gets a full
  window and a stable tip.
- **2026-08-03 (pat-down and phase 4).** The pre-refresh pat-down certified
  green from three angles: battery and every gate by hand, a cross-wave
  seam probe, and a doc-claims sweep. The seam probe earned its cost: arm 3
  carried the same estimated_state blind spot arm 2b had closed twenty-two
  minutes after arm 3 was written, the general lesson recorded in a comment
  and applied to one arm; both arms now walk both containers, pinned
  red-first. The doc sweep produced five verified-stale claims, all fixed
  in phase 4, led by the README attributing the working tree's governed
  delta to the published v1.1.19 tag, the P2-01 class pointed the other
  way. JREAP gains the loss-notes register its siblings had. Battery 1720
  passed plus 1081 subtests, gate exit 0. Only the cut remains.
- **2026-08-03 (fix wave) — the boundary paid its debts, and the harness
  ruled on the proto question.** Both ingress blockers and the egress MAJOR
  closed red-first, every red demonstrated through the real gateway
  validators rather than the schema-only path that hid them; that coverage
  now lives permanently in the SAPIENT suites, mirroring what
  mavlink/jreap/cot already had [Corrected 2026-08-03 by the pre-cut
  panel: they did not have it. No cot/jreap/mavlink/klv egress test loads
  the gateway validators; all four exercise the pure conversion function
  only. The SAPIENT suites are the first with real gateway-pipeline
  coverage, and the sibling sweep stays on the non-blocking queue]. The egress fix rests on a verified fact,
  not a reading: the dstl Location proto marks x and y mandatory and z
  not, and the attack pass then serialized a z-less DetectionReport from
  the real AIS chain through the shim to the live Java harness, which
  printed VALID DETECTION_REPORT. A bonus laundering defect died en route:
  the old gate exported a z for the contradictory 2D-plus-alt_m shape,
  which now refuses. JREAP tightened to distinguish declared 2-D from the
  ambiguous no-token shape; KLV verified as honest wholesale pass-through
  and pinned. The idle-gateway metrics fix (produced by a separate agent
  session, verified and kept on its merits) makes the summary timer-driven.
  Attack pass on the whole commit: CLEAN, no vacuous pins (2, 3, 2, 1 reds
  across the four reverts), one informational note (whitespace-padded
  denylist keys ride on the snake_keys lowercasing and fail closed at the
  gateway regardless). Battery 1718 passed plus 1081 subtests, gate exit
  0, examples 51/51. Ripples queued, not lost: JREAP has no lat/lon
  presence check at all (a geo of only alt_m emits a null-position track),
  and the ingress suites for kraken, moth, signalhunter and adsb should
  get the same gateway-pipeline coverage sweep the SAPIENT suite just
  gained. The push follows this record; phases 4 and 5 remain.
- **2026-08-03 (phase 3) — the first interop against an implementation we
  did not write, and it paid both ways.** Four validation streams ran
  read-only against 720774e. The headline positive: the independent Java
  SAPIENT harness (BSI Flex 335 v2, dstl protobufs) accepted a
  DetectionReport built by the real chain, ADS-B entry through the track
  projector through the SAPIENT egress and the Python shim over framed
  TCP: VALID DETECTION_REPORT from a validator nobody here wrote. The
  headline findings, all at the SAPIENT boundary, all queued cut-blocking:
  (1) BLOCKER, ingress: a detection with any classification entry emits an
  OBSERVATION whose vendor extension carries the per-entry confidence key
  verbatim, and the gateway's recursive identity denylist rightly refuses
  it (OBSERVATION_HAS_IDENTITY); the adapter README claims the rename
  avoids denylist keys, which is false for confidence, and the adapter
  test suite never runs its output through the gateway validators, the
  vacuous-verification class again. (2) BLOCKER, ingress: every
  INFERENCE_EVENT the adapter emits is hardcoded node_role EDGE, which
  policy/roles.yaml forbids for inference; producer authority grants what
  role stamping then always refuses. (3) MAJOR, egress: a 2-D STATE (every
  AIS vessel, every baro-only aircraft) returns None from the SAPIENT
  egress with no counter and no loss note; the A1-02 rollout never swept
  the egress adapters, and grep shows no egress adapter knows
  dimensionality exists. Elsewhere: containers PASS through the rewritten
  deploy README followed verbatim by a stranger, which closes the
  readiness audit containers BLOCKER on the record, with a real MAJOR
  observation that the metrics summary line is datagram-driven rather than
  timer-driven, so an idle gateway goes silent; sims PASS with throughput
  consistent with the ~422 events/s datum, plus the pleasing note that
  every replayed 2025-era synthetic event now trips the new ts-plausibility
  warning, the instrument working exactly as shipped; retask PASS, 24 of
  24 checks, both fielded shapes on the promoted lane, TIMING_STATUS_MISSING
  and the fail-closed MAVLink refusal both confirmed live. Full results
  archived with the session prep artifacts. The three SAPIENT fixes open
  the next session, before the docs refresh and the cut.
- **2026-08-03 (later) — wave 2, and the doctrine that opened this cycle
  closes in the right direction.** Four workstreams landed the 2-D form end
  to end: AIS and barometric-only ADS-B emit declared 2-D canonical geo
  with VERTICAL_UNAVAILABLE under conditional 1.1.0 stamping, positionless
  output byte-stable v1.0 with payload-equality pins; the track projector
  produces 2-D FUSION and STATE pairs, so A1-02's measured zero-tracks
  consequence now measures two-dimensional tracks; X1-01 closed at both
  lawful layers (v1.1.0 structural timestamp shape, gateway plausibility
  window as EVENT_TS_IMPLAUSIBLE); the contract carries sections 21.1 and
  21.8 per its own adoption checklist; the registry adopts ERROR_ELLIPSE_M
  and GEO_DIMENSIONALITY as formal, risk-relevant vocabulary. One process
  interruption mid-wave (an app restart) was recovered from the workflow
  journal: two workstreams replayed from cache, two re-ran on cleanly
  reverted scopes. The cold attack pass verified the end-to-end maritime
  chain through to CoT (hae renders the unknown convention, never zero),
  byte-stability claims against the pre-wave adapters, both hash anchors by
  tampering, and every pin non-vacuous by reverts. It found one MEDIUM gap:
  the coherence arms ignored payload.estimated_state.geo, so the arm-2 lie
  validated one container over, and my registry entry had claimed that
  scope as fixture-pinned when nothing pinned it. Closed red-first the same
  hour: arm 2b refuses a 2-D estimated_state.geo beside AVAILABLE, two pins
  substantiate the registry claim (with the schema-path check proving the
  arm itself is the refuser), and the registry note records the tripwire:
  an estimated_state producer arriving without arm-1 extension reopens
  A1-02. My first draft of those pins was itself vacuous, failing on
  missing required fields rather than the lie, caught by running the
  honest control; the corrected helper's docstring keeps that lesson.
  Battery 1706 passed plus 1081 subtests, gate exit 0, examples 51/51,
  harness 53/53. The push follows this record.
- **2026-08-03 — wave 1 of the push, and the lock's second, final
  adjudication.** Four Sonnet workstreams plus the A1-02 schema centerpiece
  landed as three commits, every behavior change red-first. A1-02:
  declared dimensionality and VERTICAL_UNAVAILABLE with two coherence arms
  on the v1.1.0 schema, nine pins. Signer: text assets hash on
  line-ending-normalized content; the generated errata found the true
  blast radius, sixteen wrong entries across fifteen published tags, three
  times the sampled estimate. Ellipse: relocated to geo with formal
  spellings under conditional 1.1.0 stamping, CoT zero-fill fabrication
  ended. Conformance: two AIS fixtures, four jreap/mavlink negative pins,
  the Profile L table regenerated, the ADS-B fixture re-pinned on the
  conditional stamp. The contract scout then surfaced section 7.3 and
  forensics dated the lock: the 2026-04-26 stamp was premature, the
  2026-05-07 lockdown audit is the baseline everything verifies against,
  and the maintainer adjudicated it so. Yesterday's restoration reversed
  forward: schema byte-exact to its enforcing form, the pre-lock record
  pinned INVALID, contract and schema both hash-anchored in
  test_v1_lock_baseline.py, the contract opening with its own lock
  provenance note. L1-01 records the lesson; X1-02 closed TERMINAL with
  the executed inventory's result on the entry. A cold attack pass on all
  three commits came back CLEAN: no bypass held (the null-alt_m probe
  confirmed presence-blocking), no vacuous pin among the four reverts, two
  errata rows independently recomputed, byte identity confirmed through
  git. One LOW pre-existing gap queued for wave 2: UNAVAILABLE with geo
  present has never been schema-blocked despite the description. Battery
  1655 passed plus 1074 subtests, gate exit 0, harness 53/53. The push
  follows this record.
- **2026-08-02 (late) — the lock breach, found and repaired the same day.**
  The X1-02 one-time gate inventory ran the stronger forms that had never
  been run and surfaced five defects, two severe: every published release's
  SHA256SUMS carries wrong manifest checksums (CRLF hashing in the signer;
  adjudicated: fix the signer, publish errata, correct from v1.1.20), and
  the locked v1.0 schema had been narrowed by the v1.1.0 release
  (adjudicated: restore). The restoration shipped red-first the same
  evening: the v1.0.5-era record validates again and is pinned verbatim,
  the whole v1.0.5 corpus validates 3 for 3, the vocabulary still binds
  under the 1.1.0 stamp, the byte-identity pin re-anchors at the restored
  bytes, and the saturation blind spot this exposed in the
  governance-sentence test's mutation arm is fixed symmetrically. Left
  open on the record rather than resolved in the dark: whether the locked
  contract text independently mandates the subtype-discriminator match for
  v1.0. Also this session: SAPIENT interop prerequisites completed and
  live-verified end to end (templates, cross-language wire proof, both
  shim directions), and the A1-02 shape approved with rationale. Battery
  1639 passed plus 1074 subtests, gate exit 0. The push follows this
  record.
- **2026-08-02 (checkpoint closeout).** Final state verified by hand rather
  than accepted: main and origin synced at f0f875e, CI green on the last two
  pushes, kernel gate all flags exit 0, examples 51/51, pytest 1636 passed
  plus 1074 subtests with the exit code checked, both adapter lints and the
  roadmap validator exit 0, no stray worktrees, branches or containers. A
  second adjudication round closed the last three gate decisions, recorded
  in the handoff: contract 4.5.1 keeps its semantics and teaches the
  refusal, the default gateway config will preserve data_ref at Profile H,
  and zmeta_uuid imports converge on the plain top-level form. The handoff
  top now carries the whole big-push campaign; the only open decision
  anywhere in the stack is the X1-02 terminal call.
  *[Superseded the same evening, and the checkpoint was not the end: the
  session continued through the X1-02 terminal call (one-time gate
  inventory, e0ccf9a), the ellipse promotion's four sub-decisions
  (1a99a59), the A1-02 shape approval with rationale (9c102a1), the prep
  scouts (SAPIENT harness built and smoke-verified, interop templates and
  shim live-proven, idahopulse brief), and the gate inventory's stronger
  forms actually running, which surfaced the two severe findings the
  2026-08-02 (late) entry records, one of which, the v1.0 lock breach, was
  adjudicated and repaired the same night at 69a14a7. Fourteen maintainer
  adjudications plus the A1-02 approval in one day. Final verified state at
  session end: battery 1639 passed plus 1074 subtests, gate exit 0, CI
  green, tree clean, synced.]*
- **2026-08-02 — the readiness audit's verdicts landed as work the same
  day.** Ten axes ran their paths live rather than reading them: encoding
  READY; normalize-rf, visualize, retask, lineage and zero-shot
  READY_WITH_GAPS; normalize-tactical, containers, redact and operator-debug
  GAPPED. The retask axis reproduced both fielded command workflows end to
  end. The maintainer adjudicated four decisions the same day, each recorded
  on its doctrine entry: A1-02 goes to declared dimensionality plus a
  geo_status token in v1.1.20; error_ellipse_m promotes into v1.1.20 with
  the spelling reconciliation; MAVLink command translation is fail-closed
  with an explicit override, shipped; and the state-projector-* wildcard is
  removed, shipped as its own governed commit with the JSON export
  regenerated and the manifest rebuilt with its v1.1.19 identity preserved.
  The confirmed small fixes shipped as a four-fixer wave, every fix
  demonstrated red first, 45 new tests: the ADS-B altitude plausibility
  band and coordinate-demotion parity, isfinite screens for kraken, moth
  and signalhunter including the NaN bin that silently flipped a bearing
  180 degrees, gateway metrics details with event and producer attribution,
  cot_enabled on the metrics line, diagnostic truncation, the CoT banner
  line, the deploy README rewritten around the override path the compose
  files actually use, AUTHORING.md teaching the residue classes and the
  mapping-pack route, and convert_encoding refusing hostile decode input
  with a one-line diagnostic. A cold attack pass on both commits came back
  CLEAN: nothing reopened, no vacuous pin among the 45 (three files
  reverted one at a time went 4, 9 and 4 red), manifest identity
  byte-identical outside seven hash lines. Two of my own instruments failed
  in the X1-02 shape and are recorded in the after-action log: a piped exit
  code under a green echo, and a bare manifest rebuild that reset the
  release identity, caught by thirty release-currency pins. Battery 1636
  passed plus 1074 subtests, kernel gate all flags exit 0, examples 51/51.
  The push follows this record.
- **2026-07-31 (later) — the pre-push cold read, and it was not green.** The
  maintainer's sequencing: review the four unpushed commits cold, push on
  green, then tier 2. Eight independent lenses read the range with the
  producing context gone, every finding adversarially verified: 31 findings,
  16 verified, none refuted. Three MAJOR, all in the AIS adapter: message 27's
  own not-available sentinels (speed 63, course 511) carried as clean motion
  data, with no course range guard at all; a finite but out-of-range
  `timestamp` killing the whole `translate_stream` batch with an uncaught
  OSError; and the timing pin asserting only `sync_state != "LOCKED"`, which a
  fabricated HOLDOVER claim also satisfies. All fixed red-first: 14 new tests
  demonstrated failing on the unfixed adapter, 64 colocated tests green after.
  Also closed: `rxtime` digits must now parse as a calendar moment, because
  month 88 produced a schema-passing lie; a sub-2000 epoch under `timestamp`
  refuses rather than dating the event 1970; `translate_stream` takes any
  iterable and raises on a non-iterable instead of silently returning nothing;
  and the changelog check's red demonstration moved from a commit-message
  attestation into an in-tree mutation canary, with its residual holes written
  into the check's docstring as known limits and onto X1-02 as terminal-call
  input. Records corrected with markers: the SIM1-05 "silence" claim was wrong
  on both paths, the A1 experiment paragraph was overtaken by the AIS landing,
  the recv=722 count was a hand count inside a paragraph applying the counting
  rule, and the closeout's "three commits unpushed" was written inside the
  fourth. The rename audit came back exact, and the records lens verified
  every other enumeration it recounted. Discipline 6 is answered for this
  range: the cold panel found what the author's read did not.
  **The attack pass on the fix wave itself** ran cold in a worktree: no
  original defect reopened across 16 probes, and no vacuous pin, with all 14
  new tests demonstrated red on the reverted adapter. Its residue closed in a
  follow-up commit: a single message dict or a string passed to
  `translate_stream` read as an empty sea, message 27's speed bound was still
  the Class A 102.2 when its own field stops at 62, the rxtime docstring
  claimed a refusal broader than the code performs, and this record asserted
  the push before any push existed, which is the same self-referential class
  this session corrected twice in others' records. The push follows this
  record.
- **2026-07-31 — an outside comparative survey, fact-checked against the stack,
  and the second implementation A1-02 was waiting for.** An external agent
  reviewed ZMeta against SAPIENT, OGC O&M, CloudEvents, C2PA, PROV-O and the
  STANAGs without repository access. Treated as gap exposure rather than
  direction, and every claim about ZMeta that could be checked was checked.
  **The most useful result was a correction to us, not to them.** The survey and
  the previous day's rep independently agreed that ZMeta cannot carry positional
  uncertainty on a track, and the agreement made it feel settled. Both were
  wrong: `ERROR_ELLIPSE_M` is a registered, approved, schema-implemented
  extension allowed on `STATE_EVENT`, on the v1.1.0 branch, with a probability
  level attached. Only the locked v1.0 kernel carries none, which makes it an
  adoption-path question rather than an expressibility gap. Corrected in six
  places. Rule earned: **when an external claim matches your own, that is the
  moment to verify it, not the moment to stop.**
  **Survived the correction:** the ADS-B adapter writes `semi_major_m` inside
  the free-form v1.0 quality object and the v1.1.0 formal contract spells
  `semi_major`, which is what the CoT reader looks for. *[Corrected 2026-07-31
  by the pre-push cold read: the mismatch is real and its failure mode is not
  silence. A validating path refuses the wrong spelling loudly, and the
  non-validating CoT path renders remarks and precisionlocation from zero
  defaults, a fabricated zero-size ellipse. The fabrication is queued in the
  handoff as its own defect.]*
  **The doctrine cycle was renamed S1 to SIM1**, 33 references, because
  `S1-01`..`S1-05` collided with the historical `S1-01A`..`S1-19` work-item
  series including a real completed S1-05. History untouched, verified per file.
  **AIS ingress shipped** (`adapters/ingress/ais/`, 49 tests) and clears the
  A1-02 promotion bar as the second independent implementation. It is the total
  case rather than a variation: every vessel, every message, because a surface
  vessel has no height above the ellipsoid. Measured consequence, pinned in a
  test: a schema-valid AIS observation with a clean identity and an exact
  position projects to zero tracks. A third facet surfaced with it, the
  `geo_status` vocabulary having no token for "horizontally known, vertically
  absent", which is the cheapest of the three A1-02 fixes.
  Also documented from running the ZMeta to SAPIENT round trip: the egress needs
  a caller-supplied `object_map` for non-ULID track ids, and it fills
  `classification[].confidence` but never `detection_confidence`.
- **2026-07-30 (closeout).** Three commits reviewed against the intent that drove
  them, battery verified by hand, records reconciled across every surface. Four
  findings. The CHANGELOG's `[Unreleased]` was empty after three commits of
  user-facing work, which is the fourth instance of records lagging commits and
  the one the v1.1.19 scoring had pre-committed to fixing with a mechanism, so
  `gateway/tests/test_changelog_keeps_up.py` now asserts the description exists
  without judging what it says. X1-02 is past the N=3 lifecycle threshold at five
  instances and still OPEN, which is a rule firing and being overridden by
  judgement; recorded on the entry for the maintainer. Discipline 6 went unmet,
  because no independent panel read this cycle at all. And the repeated
  `recv=722` measurement was considered and cleared: six assertions, all framed
  in the past tense as a corrected defect, so all six stay true. *[Corrected
  2026-07-31: the clearance holds, the count did not. A generated recount finds
  nine places asserting the measurement and two more asserting this count of
  places. Six was a hand count inside a paragraph applying the counting rule.]*
- **2026-07-30 (later) — `adapters/projector/track/`.** The simulation reps
  earlier the same day found that CoT projects `STATE_EVENT` only, so five clean
  ADS-B observations reached a consumer and produced zero CoT while the example
  corpus produced one because it happens to contain a `STATE_EVENT`. The
  rehearsal passed and the real sensor showed nothing. This closes that for
  sources whose subjects broadcast an identity: the same snapshot now produces
  two tracks on the CoT wire, verified through two live gateway nodes, 9 of 9
  events forwarded with zero diagnostics.
  **A third adapter category.** A projector is ZMeta in and ZMeta out. It
  changes what an event is rather than what format it is in, which is neither
  ingress nor egress.
  **Fusion, not external promotion, and the constraints agree with the
  semantics.** Promotion imports a track another system computed; fusion is a
  track you associated. `policy/lineage.yaml` permits a `STATE_EVENT` to cite
  only `FUSION_EVENT` or `STATE_EVENT` parents, so a state citing an observation
  is refused with `LINEAGE_PARENT_TYPE_INVALID`, and `FusionPayload.members` is
  `minItems: 1`, so a single-member association needs no invented lineage. Both
  were confirmed by running them rather than by reading the policy.
  **The finding underneath the component:** `confidence` is required by the
  kernel on both emitted types and a cooperative broadcast supplies none, so the
  projector refuses to construct without an operator-asserted value. Deriving it
  from `sil` was rejected as an unadjudicated modelling decision.
  **Doctrine log SIM1-05, kernel-shaped:** a v1.0 `STATE_EVENT` has nowhere to
  carry positional uncertainty, so a measured 30 m ADS-B ellipse reaches TAK as
  the unknown-accuracy sentinel. Nothing overstated, a real measurement
  unavailable, and every outer-ring workaround worse than the gap.
  29 colocated tests. Battery 1518 + 1074.
- **2026-07-30 — internal simulation reps while field feedback is pending.**
  The stack was run rather than read: two gateway nodes, the shipped containers,
  the ADS-B adapter on a synthetic `aircraft.json`, the command-evidence loop in
  four cases, a throughput sweep, and an X1-01 reproduction. Every rep carried a
  control defined before the run, which caught three bad measurements of my own
  before they became findings: a false "node did not come up" from a
  block-buffered pipe, a throughput figure that was measuring duplicate
  suppression rather than capacity, and a command corpus in which all four cases
  failed for an unrelated reason (`TIMING_STATUS_MISSING`, because the node had
  not published `TIME_STATUS`).
  **Two real breaks in the deployment path, both fixed and both verified by
  re-running.** The containerized nodes could not deliver anything: `forward.host`
  and `cot.host` are `127.0.0.1`, which inside a container is the container's own
  loopback, so the send succeeds and the datagram is unreadable. Measured at
  `recv=722 fwd=722` in the container against zero on the host. And the two
  Compose files both published `5555:5555/udp`, so the pair could not co-host.
  The Compose files now override both egress hosts on the command line and take
  host-port overrides; the corrected pair was run end to end on one machine, with
  ZMeta JSON arriving on the host's 5556 and CoT on 6969 where both had
  previously measured zero.
  **The finding that matters most for a live event.** CoT projects `STATE_EVENT`
  only, so five clean ADS-B observations produced zero CoT while the example
  corpus produces one because it contains a `STATE_EVENT`. The documented
  rehearsal passes and the real sensor then shows nothing, which is the worst
  available ordering. Recorded as SIM1-03: a fixture chosen to demonstrate every
  feature is not a fixture representative of the input.
  **Confirmed rather than assumed:** X1-01 accepts six of six nonsense
  timestamps including `banana-Z`, with both controls behaving, and those events
  reach a downstream ZMeta consumer with no violation while CoT egress refuses
  them. Left untouched, since it is adjudicated for v1.1.20. Also verified
  working: the command-evidence gate refuses a prohibited-parent citation with
  `LINEAGE_MISMATCH` while an identical command on a clean parent forwards;
  Profile L compact maxes at 150 bytes against the 240-byte budget; contract
  hashes are byte-identical across host and Linux container.
  **Measured for the first time:** 100% delivery at 400 events/s, saturation
  near 422/s, and 44% delivery at 1000/s offered while the node reported
  `drops=0`, because loss above capacity happens upstream of the process.
  **The harnesses were then committed to `tools/sim/` under a structural
  boundary.** The maintainer named the risk in the same breath as the value:
  operational tooling is invaluable and a data standard that accumulates it
  stops being readable as a standard. Recorded as doctrine SIM1-04 with an
  extraction criterion and a trigger, and enforced by
  `gateway/tests/test_sim_boundary.py`, which asserts that nothing governed
  imports or invokes anything under `tools/sim`. The dependency runs one
  direction only, so extraction stays a directory move rather than a refactor.
  That test's own detector-fires check caught a gap in its detector on the day
  it was written: a Windows path in Python source carries an escaped separator
  and the first pattern missed it.
- **2026-07-28 (later session) — v1.1.19 PUBLISHED; documentation voice pass;
  X1-01; two verification gaps closed.** Four strands.
  **(1) The house voice.** An outside reader called the README machine-written.
  40 current-facing files rewritten, 300 em dashes to 1, prose only — verified
  by a structural invariant check (headings, tables, fences, links, code spans
  identical except seven intentional heading rewordings; zero broken links).
  Word count rose slightly, so it was not compression wearing a voice-pass
  label. Scope set by measurement: `docs/README.md` was worst in the repository
  at 52 dashes per 1k words, while `zmeta_professional_overview.md` was already
  clean at 0.5 — the opposite of what the handoff predicted. Governed and
  manifest-hashed files computed and excluded, not judged by eye. Adopted as the
  repo standard in `CLAUDE.md`, which was itself brought to the standard in the
  same commit because a style rule stated in the one file that breaks it is the
  exemplar-violates-its-own-rule defect `adapters/AUTHORING.md` §9 already names.
  **(2) A cross-repo exchange with the fielded consumer.** Two findings raised
  against their deployment (calendar-invalid `ts` silently shifting a CoT
  timestamp; a declared vertical datum read and discarded), each reproduced
  independently on both sides. Their observation about JSON Schema `format`
  semantics then found **X1-01 in our own kernel**: `event.ts` is unconstrained
  beyond a trailing `Z`, and the mitigation named in two adapter READMEs cannot
  work as shipped. Recorded, escalated, not fixed.
  **(3) The cut, made twice.** The first tag was created before the publish-path
  validations had run; `--package-dir` then failed on a package built at the
  prepare commit against a manifest that had moved four hours later. Tagging is
  what makes checksums immutable, so the fix was correctly refused in place and
  the tag was deleted before anything was published. **Rule: run every
  publish-path validation before the tag exists.**
  **(4) Two verification gaps closed by checks rather than checklists** — release
  artifact completeness, and package-mode validation at checksum time. With
  X1-01 that is three instances in one day of a stronger check existing while
  something cheaper ran in its place. Logged as an observation; not minted.
  **Published and verified:** tag on `0eebb43`, 8 assets, CI green, published
  assets downloaded back and re-verified against published checksums.
  Battery 1477 + 1070.
- **2026-07-28 (checkpoint after the session closeout) — three commits landed
  after `b8385ef`, reconciled here.** The closeout is the tier that catches
  exactly this, so the drift is recorded rather than folded in silently.
  **Doctrine log cycle X1 now carries three OPEN entries**, none minted:
  **X1-01** `event.ts` unconstrained beyond a trailing `Z`, sequenced for
  v1.1.20 which is therefore behaviour-changing rather than additive;
  **X1-02** a weaker check standing in for a stronger one; **X1-03** our own
  retirement rule reading silence as death, which inverts for constitutional
  rules — a spec repo is mostly those, so a naive earn-your-place pass would
  remove the wrong half.
  **X1-02 was sharpened by the fielded consumer and the count reached five
  across two repositories.** Their mechanism, better than the three
  coincidences originally recorded: *a check that exists gets substituted by a
  cheaper one that shares its name or its neighbourhood, and the substitution
  survives precisely because the cheaper check passes.* In all five instances
  the cheaper check was green, and the greenness is what stopped anyone asking.
  The detection question — *for each gate we cite, what stronger check is it
  standing in for, and when did we last run that one?* — is deliberately
  unstarted on both sides. Starting a sweep off the back of a closeout is how
  the previous cycle grew an apparatus it then had to apologise for.
  **Three items queued for the v1.1.20 cut**, grouped because being free at the
  next manifest rebuild is the only property they share: X1-01 enforcement, the
  conformance summary legibility line, and a five-dash voice sweep across four
  manifest-hashed files. Doing any now would diverge `main` from the published
  `SHA256SUMS_v1.1.19.txt` for no reader benefit (the A-12 pattern).
  **A false credit was corrected, and it is the entry worth reading.** The queue
  credited the consumer with finding a test constraint that was found here, and
  the wording they *had* proposed breaks both assertions that test makes — so
  the entry carried a fix that would turn a test red under a credit belonging to
  the party who did not supply the constraint. Both halves corrected; the
  replacement line is verified against both assertions rather than proposed.
  The rule, theirs: **credit is a claim too** — verify attributions in your
  favour at least as carefully as ones against you, because nobody else is
  incentivised to. The hazard, named against ourselves: **an invented provenance
  is more convincing than the truth, which is why it survives review.**
  **Downstream:** the consumer advanced their pin to v1.1.19 (reviewed GO,
  additive, full battery green) and reports `ahead 0 behind 0` for the first
  time in this arc. Their hand-mirrored §7.7 denylist is verified as a drop-in
  replacement for `export/policy/semantics.json` and retires when their W1 wave
  closes. Battery unchanged at 1477 + 1070; no hashed artifact touched, so the
  published manifest and checksums stay valid.
- **2026-07-28 — P2 + A1 CYCLE, v1.1.19 PREPARED, CLOSED OUT.** Opened by a
  downstream consumer's pin-advance report (P2-01: a stale README release-focus
  bullet asserting a governance negative that was false in two published tags)
  and closed with the first cooperative-broadcast adapter. Four independent
  panels ran across the cycle; a fifth pass verified the fourth's fixes.
  **What the panels found that internal passes had not:** the content guard
  built for P2-01 did not work — a carried-forward bullet passed both rules
  after two one-word edits — and its replacement had four MAJORs of its own, so
  the rule that tried to judge whether prose was about the right release was
  **removed** rather than patched a third time. What survives is the part two
  panels confirmed sound: a governance sentence COMPUTED from the manifest
  against a committed `release/governed-baseline.yaml` and required verbatim.
  **The first-run lens paid best**, and it is the one I would have skipped: the
  documented two-node path delivered zero events (edge L, gateway H, exact
  profile matching), the "adapter in about an hour" claim hid a 30–90 minute
  producer-authority wall, contract hashes differed between Windows and Linux
  clones **in two independent ways**, and `requirements-dev.txt` produced a
  broken environment. All long-standing — the hash defect dates to the
  repository's first day, 2026-01-17.
  **Churn diagnosis, measured not asserted:** the code converged (no test,
  fixture or conformance expectation regressed across the whole cycle); the
  *claims about* the code did not. Every late-cycle defect was an enumeration
  or measurement written into prose without being run — three separate places
  once carried three different counts of the same thing. The durable rule that
  came out of it: **when a claim enumerates, generate it.** Applied in three
  places now (the governance sentence, the conformance flag list, the dist
  bundle's tool list).
  **ADS-B adapter landed** (`adapters/ingress/adsb/`, 17 tests, 3 fixtures)
  and produced doctrine-log cycle **A1** — three alphabet gaps, each with a
  second instance so no fix accommodates one source, and the shipped `kraken`
  adapter shown to be laundering uncalibrated RSSI into `power_dbm` because the
  spec leaves no third option. Recommendation for all: a declaration, not a
  subtype. **Maintainer adopted playbook discipline 10** (validate before
  hardening; otherwise write the question down) and
  `docs/zmeta_live_test_checklist.md` now carries the deferred questions.
- Quick handoff: `docs/zmeta_refinement_handoff.md`
- **2026-07-27 — P2 CYCLE + v1.1.19 PREPARED.** Opened by a downstream
  consumer's pin-advance review, not by an internal pass. **P2-01**: the
  published v1.1.17 and v1.1.18 trees carry a README release-focus bullet
  held over from v1.1.16 asserting "No schema, policy, or event-vocabulary
  changes" — false for both. Errata recorded; published checksums untouched;
  the currency guard now pins release-focus CONTENT, not only version
  literals (`bdd02a5`, `05106b8`). **Item 10 shipped** (`31ac80e`):
  `export/policy/*.json`, a verbatim JSON projection of the governed policy
  with `tools/export_policy_json.py`, hash-pinned under a new
  `policy_json_export` manifest group — built because that consumer had been
  hand-mirroring the §7.7 STATE denylist for want of any other option.
  **P2-D1** (`508aafe`): seven instances of the vacuous-verification class
  (five test pins, one in shipped tooling, one hand-run probe; the
  audit-evidence case is adjacent to the class, not one of the seven) forced
  playbook discipline
  5 to change — a guard's red demonstration must now be an artifact in the
  repo, not a session act; `gateway/tests/vacuity.py` supports it. The
  **pre-cut whole-range review** then produced **eleven** findings (PC-01..11;
  PC-10 and PC-11 surfaced while fixing the first nine), and an independent
  five-lens panel afterwards found the content guard itself did not work,
  two of them live defects: `adapters/README.md` had pointed at
  `--target v1.1.16` for two releases, and the manifest hashed eleven
  `export/policy` artifacts that NEITHER bundle builder carried. Four
  previously-unpinned current-release literals are now covered, including
  the README title line and the CI workflow's compat target. **PC-09 was CLOSED 2026-07-28** — this sentence recorded it as deferred and
  was missed by the first correction pass, which is the sibling-claim defect
  the second panel named. Original statement: **PC-09 is
  deferred to the maintainer**: the bundles omit `docs/` (and the dist zip
  also omits `conformance/`) though both are hashed, and README directs
  bundle users to governance docs their bundle does not contain — a
  packaging-scope judgement, not a mechanism.
- **2026-07-27 — v1.1.18 PUBLISHED + SESSION CLOSEOUT.** Publication
  facts (previously recorded only in commit messages — the CR-03 class):
  annotated tag `v1.1.18` on release commit `157d41f`, pushed with
  `main`; GitHub release live with all **eight** assets
  (`zmeta-v1.1.18-dist.zip`, edge, gateway, release-package,
  `zmeta-release-manifest.yaml`, `RELEASE_NOTES_v1.1.18.md`,
  `VALIDATION_REPORT_v1.1.18.md`, `SHA256SUMS_v1.1.18.txt`);
  **checksums-only** per the standing signing decision (consistent
  v1.1.5 onward); **CI green on BOTH the tag and `main` runs** — a first
  for this cycle, v1.1.17 having gone red on publish. Post-tag:
  `dd5def7` swept the interruption-affected edits and closed two
  cosmetic defects (a stranded parenthesis in the CHANGELOG entry, a
  stray lint directive in `validators.py`), regenerating
  manifest/claims — so `main` diverges from the published v1.1.18
  assets by design (A-12 roll-forward pattern; **deploy from the tag**).
  **CLOSEOUT (this bullet's commit):** a four-lens read of every
  standing record produced 36 actions, all applied — the AAR gained its
  cycle entry; the doctrine log's lifecycle fired for the first time
  (eight terminal entries archived to one-liners, the legend reconciled
  with the Lifecycle vocabulary, and three tensions at the N=3
  recurrence threshold forced out of indefinite OPEN and put to the
  maintainer: R1-11-07 → HELD-FIRM, R1-11-01/H1-08 and R1-11-14/19
  escalated); the playbook gained a full rule-scoring block (no rule
  scored out; the one-third cap has never fired and is named as a
  watch-item) and the cut tier was amended to a whole-range fresh-eyes
  review on the evidence that three pre-cut findings survived their own
  per-wave attacks; README's release focus and integration notes were
  rewritten (they had carried **v1.1.16 content verbatim** through two
  cuts — invisible to the currency guard, which pins version literals
  only, and the v1.1.16 text is now re-homed under its own heading);
  the CHANGELOG gained the waves it was missing (both CI hotfixes, the
  ARM64/Docker verification, the `cot.config` knob, the quickstart, the
  pre-cut review) plus the v1.1.17 publication note; the cold re-read
  record gained the honest CR-01..30 disposition ledger (10 fixed / 1
  adjudicated final / 8 records-corrected / 2 closed at closeout / 9
  open by design) that existed nowhere before; the audit record closed
  A-13 and A-12/A-29 with the roll-forward pattern named; and this
  worklog took the retention pass below. Battery unchanged and green
  throughout: **1420 + 1070 subtests**, gate all flags exit 0.
  **README pass after the closeout (`a8fcc7b`, `4cb3f3c`, both CI green):**
  front-loaded the value proposition with the three graphics that already
  existed in `docs/img/` but were reachable only from inside the
  professional overview (now linked directly for evaluators); reordered to
  pitch → field evidence → framing → proof → routing → reference; merged the
  two duplicate quickstart blocks; and moved six historical per-release
  Integration Notes sections verbatim to `CHANGELOG.md` — they were 39% of
  the README and sat between the pitch and all reference material (598 → 395
  lines, nothing lost, links and images verified). Added the one-time Windows
  long-paths fix after a test clone into a deep path failed checkout on the
  260-character limit; the repo's own deepest path is 79 chars, so normal
  clone locations have headroom. That test also settled a question worth
  recording: **a fresh clone of `main` runs clean for a new user** — the
  in-repo manifest is regenerated to be self-consistent with `main`, so the
  earlier "deploy from the tag" guidance was over-cautious and is retracted;
  the tag matters only for byte-exact verification against published assets.
- **2026-07-27 (post-publish) — PRE-CUT REVIEW + v1.1.18 CUT.**
  Bounded four-lens fresh-eyes review of the whole post-v1.1.17 range
  (9 commits, 33 files) at release stakes, every finding independently
  verified: **13 confirmed, 0 refuted**, all closed before the cut. Three
  had survived their per-wave attacks: (a) MODERATE — a re-sent clean
  copy of an already-seen parent ERASED its recorded command prohibition
  and the citing command then forwarded with no diagnostic (dedupe is
  time-bounded, the evidence index only cardinality-bounded); closed by
  making recorded labels STICKY (union, never downgrade) plus an
  unadjudicable-shape marker for unreadable risk blocks; (b) MODERATE —
  the new policy block had mode-value and wrapper-key lints but nothing
  checking key NAMES or value TYPES, so a one-character typo silently
  reverted a knob to its permissive default with the lint green; closed
  with a key/type lint; (c) MODERATE — the bladeRF non-finite screen
  missed the bearing-demotion and metadata arms. Also closed: the
  quickstart's wire path was WRONG (edge forwards 5556, GCS listens
  5555 — stock two-node path silently went nowhere), the 4096-cap memory
  rationale overstated what it bounds (ValidationState.events is
  unbounded — corrected in place rather than smuggling a behavior
  change), CoT team-name config could crash the projection, and three
  records claims (the superseded ~40 min figure, a 44-vs-42 commit
  count, a stale handoff block). **v1.1.18 CUT:** currency pass first,
  manifest last; notes + validation report written (incl. the honest
  not-exercised list: real-Pi throughput, TAK display, SAPIENT enclave,
  SITL); bundles + package + `SHA256SUMS_v1.1.18.txt` written and
  verified; battery **1420 + 1070 subtests**, gate all flags exit 0,
  harness 48/48, all lints + roadmap validator clean, packet max
  150/240.
- **2026-07-27 (post-publish) — THE COMMAND-LOOP PAIR LANDED
  (maintainer-directed).** Wave A, attack verdict CLEAN: the
  command-evidence lineage check — `policy/command-evidence.yaml` (S1-15
  risk-model shape, lint-covered) + `validate_command_evidence` +
  bounded ValidationState evidence index (4096, eviction=unresolved) +
  gateway wiring beside the command machinery; refusals reuse
  LINEAGE_MISMATCH / LINEAGE_PARENT_UNRESOLVED / LINEAGE_PARENT_TYPE_INVALID
  (zero minted vocabulary), degrade stamps the S1-15 risk record, bare
  commands default-legal, `require_evidence` strict knob for automations;
  29 red-first pins. Wave B: `docs/zmeta_track_lifecycle_pattern.md`
  expresses the lifecycle + command-grade criteria in current vocabulary
  only; roadmap candidate stays RESERVED with evidence legs recorded
  honestly (n=1 + awaited event); three attack doc-accuracy findings
  fixed same-sitting (preset default boundary stated precisely,
  per-code dispositions, policy enumeration). Banked: H1-08 (wanted
  evidence codes), VW-16 (flood-eviction tradeoff, documented in
  policy), VW-17 (seams). Battery: **1410 + 1070 subtests**, gate all
  flags exit 0, risk-mode lint ok, roadmap validator ok, corpus 51/51.
  Event queue: all agent-executable items DONE — remaining items await
  hardware/access (real-Pi throughput, TAK display validation with the
  cot.config knob, SAPIENT live-enclave, SITL end-to-end).
- **2026-07-27 (post-publish) — VIRTUAL-PI VERIFICATION, THE
  cot.config KNOB, AND THE TWO-NODE QUICKSTART.** Docker build+run — the
  one checklist item the cut could not exercise — is now verified both
  ways: x86 native (stock compose, corpus replayed end-to-end,
  violations=0) and **arm64 under QEMU emulation as the virtual Pi**
  (deps install from wheels, gateway starts, corpus forwarded clean, and
  the schema/policy/semantics/contract hashes are BYTE-IDENTICAL to the
  x86 run — the interop guarantee demonstrated across architectures).
  Platform pins ran on arm64: 98 + 232 subtests green; one failure was
  environmental only (a test wants a scratch dir under the read-only
  deployment mount). Honest scope notes: cbor2 resolves to its
  pure-Python build on that wheel set (the C-extension class stays
  covered by Linux x86 CI), and real-Pi throughput awaits hardware.
  NEW KNOB (outer-ring, red-first pinned in
  gateway/tests/test_gateway_cot_config.py): the gateway config's
  `cot.config` block now passes deployment-asserted projection knobs
  (geopointsrc/altsrc/how, team names, default_ce/le) through to
  zmeta_to_cot — previously the serve loop called the projection bare,
  so no deployment could EVER assert a pedigree and the
  `<precisionlocation>` ellipse detail was unreachable (found while
  writing the quickstart; the TAK-ellipse story depends on it).
  Unasserted stays omitted — the honest default is unchanged.
  `docs/zmeta_two_node_quickstart.md` (advisory) ties it together:
  topology, both node configs, the wire check, hash-match rule, the
  honesty-signal cheat-sheet, and the per-team pre-event checklist.
  Battery: pytest **1381 + 1060 subtests**, kernel gate all flags exit 0.
- **2026-07-27 (post-publish) — BLADERF REFERENCE ADAPTER LANDED
  (the maintainer-directed "NEXT" item, timed).** The merged
  `edge-comms-bladerf` pack now has its runnable reference
  implementation at `adapters/ingress/bladerf/`, authored along the
  documented path exactly (AUTHORING.md end-to-end -> pack primaries ->
  contract 3.4/4.4/4.8/6/7.1/7.3/7.4 -> sibling references), as the
  repo's receipt that the authoring guide takes a new RF sensor from
  recorded output to a verified adapter in one sitting. **Timed receipt
  (commit `71f8e18`), orchestrator external wall-clock: **~13 min
  zero-shot authoring** (12:48->13:01), **~25 min full verified cycle**
  to 13:13 (the agent self-estimated ~40 min of effort; the external
  wall-clock is the honest receipt). Then an
  independent adversarial attack (verdict CLEAN on the semantics; one
  value-honesty finding — finite-blind geo/feature guards) and
  same-sitting hardening.** The guide's "run this guide as a checklist"
  step did real work: the in-sitting review caught four fail-closed
  gaps before landing — an unmapped alternate `event.ts` source (the
  `timestamp` rendering could rescue a missing `timestamp_ms`; now
  mapped-source-only), crash-not-refusal arms (non-numeric/boolean
  `timestamp_ms`, non-dict `metadata`, non-numeric geo), a
  `platform_id` TypeError where a refusal belongs, and `str()`
  coercion of caller lineage ids (now pass-through, schema rejects).
  The `quality.geo_status AVAILABLE/UNAVAILABLE` convention was
  verified against the SAPIENT reference + v1.1.0 quality vocabulary
  before adoption, not assumed. Non-finite values are screened at the
  boundary (NaN/inf SNR refuses the event; a non-finite coordinate
  refuses geo; NaN `timestamp_ms` refuses), red-first pinned. Landed
  together (Class C set): module + README (both declared conventions
  documented: FFT bin-width `bandwidth_hz`, native-bearing demotion) +
  67 colocated tests (both capture pairs reproduced exactly; one
  refusal per schema-required field), 8 `bladerf-` harness fixtures,
  README table row (Reference legend widened to real-capture corpora),
  pack README cross-link, manifest/claims regenerated under the current
  identity (A-12 interim pattern; next cut re-baselines). Evidence
  (each run where it could fail): `pytest adapters/ingress/bladerf -q`
  = 67 passed; `tools/validate.py --profile H --strict` on emitted
  events = 2/2; `tools/check_compat.py --target v1.1.17` = 0 failed (2
  deliberate `timing_quality_fallback` warnings); `tools/check_adapter.py
  --fixtures` = lint + harness 48/48; kernel gate all flags exit 0;
  examples 51/51; full pytest **1377 + 1060 subtests**;
  `git diff --check` clean. Adapter core + fixtures committed as
  `71f8e18`; this registration set (README row, pack cross-link,
  manifest/claims, records) rides the follow-up commit — whether it
  cuts is the maintainer's call per the commit=release policy.
- **2026-07-27 (post-publish, later) — KERNEL-ADJACENT RESIDUALS CLOSED
  (VW-01, H1-07).** Scoped wave per the playbook (fix + attack per item).
  VW-01: naive-ts refused at `_parse_utc_z`/`_format_utc_z`; the attack
  pass caught the first fix converting a loud crash into silent
  participation in a PRE-EXISTING fail-open (any unparseable recorded
  TIME_STATUS made freshness silently pass for that source) — repaired at
  the record seam: unorderable statuses are never recorded, the source
  keeps the loud MISSING arm. H1-07 → CHANGED: `_decode_cbor_envelope`
  runs the fail-closed value-model scan on the plain-`cbor` envelope on
  both backends, pre-decode depth bound probed (never version-guessed);
  two legacy pins updated to clause semantics with their locatability
  property preserved. Banked: VW-14 (event-side silent freshness arm +
  env-dependent `date-time` gate strictness), VW-15 (auto/compact-branch
  bare pre-decode, resource-knob parity, scanner-absent combo, three
  inconsistent naive-datetime doctrines repo-wide). Battery: pytest
  **1310 + 1060 subtests**, kernel gate all flags exit 0. NEXT (maintainer
  direction): the bladeRF reference adapter, timed, per AUTHORING.md.
- **2026-07-27 (post-publish) — v1.1.17 PUBLISHED; two CI hotfixes; CI
  GREEN.** Release published with explicit maintainer direction (tag on
  `7302073`, eight assets, checksums-only). The release commit's CI — the
  first CI contact for the entire 42-commit held range — caught two
  platform-dependent defects no local run could see (local cbor2 is
  pure-Python on 3.14; the runner's is the C extension): (1) the compact
  ENCODE path handed hostile-depth structures to the backend before
  refusing — segfault on C-extension installs; fixed in `8175aa7` (depth
  guard in the iterative scan, sentinel-pinned pre-backend refusal;
  shipped gateway/edge bundles unaffected — they bundle and prefer
  zmeta_cbor; noted honestly on the GitHub release body, assets
  untouched); (2) the v1.0 byte-identity pin hashed raw checkout bytes,
  which differ under autocrlf — fixed in `1fb6fa3` (LF-normalized digest).
  The A-13 anchored-totals pin also fired exactly as designed the moment
  the push moved origin/main, catching three remaining unanchored figure
  sites — anchored in `8175aa7`. The repo manifest again diverges from the
  published v1.1.17 manifest asset (hotfix regeneration; published
  checksums immutable; next cut resolves — the documented A-12 pattern).
  NEXT: the event-readiness queue (bladeRF adapter as the timed
  hour-proof, Pi/Docker verification, two-node quickstart, TAK display
  validation, UxS-roadmap command-evidence lineage + track-lifecycle +
  SITL gate).
- **2026-07-27 (later) — GOVERNED WAVES, RECORDS WAVE, v1.1.17 CUT PREPARED
  (HELD).** The two adjudicated governed waves landed with attack passes:
  `40be64a` (compact fail-closed value-model clause — no tags incl. 28/29,
  declared nesting max 64, declared expansion bound 2^20; spec-sync-pinned;
  doctrine 02/03/18 → CHANGED) and `2a00ef2` (TIME_STATUS.state enum in
  v1.1.0, Class B; B-04 now schema-visible; v1.0 pinned byte-identical;
  doctrine 15 → MINTED). Records wave `ae42a4d` closed A-13 (figures
  anchored to literal base `09118b3`, currency pin extended) and corrected
  the six frozen-record counts (CR-04/13/14/15/24/25) with dated notes;
  health-wave verifier candidates banked as VW-01..13. Cut prep: manifest
  rebuilt under `zmeta-v1.1.17` with explicit provenance and claims
  update, release notes + validation report written, dist/edge/gateway
  bundles + release package built, `SHA256SUMS_v1.1.17.txt` written and
  verified, doc-currency re-baselined (README, installation guide,
  overview, release/tools READMEs, guidance docs, CI target, compat
  TARGETS, manifest pins, signer example). Battery at hold: kernel gate
  all flags exit 0, examples 51/51, pytest **1284 + 1051 subtests**,
  packet check max 150/240, checksums verified. **PUBLISHED 2026-07-27 with explicit maintainer
  direction after review**: `main` pushed (`09118b3..7302073`, the full
  42-commit held range), annotated tag `v1.1.17` on `7302073`, GitHub
  release live with all eight assets incl. `SHA256SUMS_v1.1.17.txt`.
  Checksums-only. Not exercised locally: Docker build/run; CI runs
  post-push (status recorded at publish in this note's session).
- **2026-07-27 — HEALTH FIX WAVE + ADJUDICATION (resume session 2).**
  Maintainer adjudicated four decisions in-session (doctrine log
  "Adjudication pass"): governed vocabulary = the event model only;
  compact fail-closed clause approved (own governed wave pending);
  `TIME_STATUS.state` Class B enum approved for the next cut; round-3
  register loss recorded as final. Fix wave per the playbook — nine
  disjoint-surface clusters, red-first pins, an independent attacker per
  cluster, a verifier-driven completion round — commits
  `25bb5fa`/`ede9bb6`/`dcabcc8` plus this records commit. Closed: CR-01
  and CR-02 (both MAJOR, both live in published v1.1.16), the banked
  `_parse_utc` MAJOR as a CLASS (CoT/JREAP/SAPIENT twins; unparseable AND
  gate-clean naive shapes refuse — "1969-12-31Z" parses naive on Python
  3.14 and used to localize silently), CR-05/06/08/09/10/11/12/16, the
  unblocked R2-30 skip token, and the R1-11-16 vocabulary lint (which
  would have caught CR-05/06 mechanically). Introduced-at-MODERATE+
  across the whole batch: 1, fixed same-day — the one-third cap held.
  Battery: kernel gate all flags exit 0, examples 51/51 strict, pytest
  **1262 passed + 1021 subtests**, vocabulary lint ok. Six new tensions
  banked (H1-01..06); the audit record's falsified "Refuted 3/3" ts
  disposition carries a dated correction. **NEXT: the records wave (A-13,
  CR-13/14/15/23/24/25, verifier register candidates), the compact-clause
  governed wave, then the v1.1.17 cut.**
- **2026-07-26 — R1-11 resume queue P1 COMPLETE (refresh + cold re-read);
  next is P2, the maintainer's doctrine adjudication.** Battery re-verified
  live (kernel gate all flags exit 0, examples 51/51 strict, pytest 1200
  passed + 1021 subtests). `7eaea97` closed the doctrine-log numbering
  collision (the disposition addendum had restarted at 14; renumbered
  15–21, cross-references swept — the log holds **21** tensions, and the
  adjudication clusters are now R1-11-09/15/16 (governed-vocabulary
  boundary) and R1-11-02/03/18 (compact-mapping clause)). `e524c8c`
  recorded the cold re-read: nine independent lenses (the six playbook
  wave surfaces plus commit-truth, vacuous-pin, and half-applied-fix),
  adversarial verification of every candidate, three-lens panels for
  MAJORs — 48 candidates, 47 confirmed, 1 refuted, merged to **30
  distinct findings in `docs/r1_11_cold_reread_findings.md`, RECORDED not
  fixed** (the round-3 stop decision and the P2 bottleneck stand).
  Headlines: **CR-01 MAJOR** — SAPIENT ingress, a negative declared
  `maximum_latency` *narrows* `est_error_ms` (sign member of the
  R1-03/B-03 class, unswept, **also live in published v1.1.16**);
  **CR-02 MAJOR** — CoT egress stamps the horizontal ellipse `semi_minor`
  into `point@le`, fabricating vertical certainty (**also live in
  v1.1.16**); **CR-03 MAJOR** — the 44 open sub-MAJOR and round-3 attack
  findings are recorded nowhere in the tree (the fix-pass register ends
  at round 2), so queue item P4 must reconstruct its own input; **CR-04**
  — the cycle-wide "no governed artifact touched / no `reason_code`
  minted" claim is false as written (three additive reason codes were
  minted by the early waves) — the live handoff surface is corrected; the
  frozen records keep their count/claim defects banked (CR-13..15,
  CR-23..25) for a scoped records wave. Completeness critic's top gap:
  the ~7.8k lines of new test mass were deep-read below 15% — candidate
  surface for the next scoped wave. Process note (maintainer direction
  2026-07-26): ultracode stays on with lean-vs-heavy judgment delegated —
  heavy fan-outs reserved for passes where independent eyes are
  load-bearing (fresh audits, fresh-eyes re-reads, pre-cut verification);
  records work and scoped waves run lean.
- **HOLD (2026-07-22): the R1-11 cycle is COMPLETE and FROZEN pending a
  fresh full-stack audit.** Held range `118f0b9`..`HEAD` — the entire
  cycle, none of it pushed (`git log --oneline origin/main..HEAD` gives
  the live set; last code commit `6ea9888`, anything after it is records
  only). Tree clean; nothing pushed, tagged, or signed, so no consumer
  has seen any of it and the published v1.1.16 assets remain the only
  downstream truth. The maintainer's
  release decision stays OPEN behind that audit. **The cycle was
  executed across four sessions broken by usage limits, plus a model
  switch and a full chat reset — the interruption ledger, the residue
  checks that were run, and a targeted checklist for the fresh audit are
  recorded in `docs/r1_11_full_stack_audit.md` ("HOLD state" and
  "Execution continuity").** The single most important item there:
  interruption 2 left a **half-applied two-layer fix** (compact codec
  layer applied, gateway backstop layer missing) that looked complete
  and was caught only because the resuming session read the working diff
  instead of trusting the narrative — **resume from the tree, never from
  the transcript.** **What was touched: measure it live with
  `git diff --shortstat origin/main..HEAD` — no total is frozen here,
  because the range grows with every record commit and the frozen figure
  was falsified by the commit that wrote it (A-13); at the fresh audit's
  anchor, `git diff --shortstat 09118b3..eb41794` = 77 files,
  +4920 / −392, over 18 commits. The
  record's "What was touched — validation inventory" maps it (governed
  surfaces first: `schema/`+`policy/` took only three additive
  `reason_code` enum entries, `spec/semantics-contract.md` took +6/−1 in
  §5.3; the release manifest and conformance claims are BUILD OUTPUTS,
  verify by regenerating and diffing, not reading), and "Order of events"
  gives the chronology with interruption points marked. The audit's FIRST
  deliverable is "Step 0" in that record: a finding → code → test map,
  17 rows (`V1-01`..`V1-03`, `V2-01`..`V2-14`), derived from the code
  rather than copied from the record — it does not exist yet, every later
  check depends on it, and a row that cannot be filled is a live
  finding.**
- Current state (2026-07-22, fifth closeout): the **R1-11 cycle is
  COMPLETE through both post-fix verification passes.** The fix pass
  (seven waves) and verification pass 1 (`d955cd0`) were followed by
  verification pass 2, which closed **14 findings — 2 MAJOR (a
  process-killing crash class and a cross-backend laundering/interop
  hole), 7 MODERATE, 5 MINOR**; the findings record
  `docs/r1_11_full_stack_audit.md` now carries the disposition, the
  cycle outcome, and both verification passes. Final battery: kernel
  gate all flags (bad-events 29, harness 40), examples 51/51 strict,
  packet size compact max=150 of 240 (unchanged), pytest **785+316**
  zero failures, `git diff --check` clean. **Post-release divergence
  record (per the AGENTS.md rule): the fix-pass and verification-pass
  commits regenerate the manifest and claims under the v1.1.16
  identity, so current main diverges from the published v1.1.16
  SHA256SUMS manifest/package pins; published checksums stay
  immutable; resolution is the next release cut.** NEXT: **a fresh
  full-stack audit over the held cycle** (targeted checklist in the
  findings record: partial-application residue, commit-truth across the
  interrupted boundaries, the new guards as unreviewed code,
  blind-by-construction self-checks, record counts, doc-currency
  judgement calls), THEN the maintainer release-cut decision (v1.1.17
  recommended — the cycle includes a MAJOR honesty fix, two MAJOR crash
  classes, a MAJOR cross-backend laundering/interop hole, and two
  Class B vocabulary batches). **Carry-forward lesson: a fix has
  introduced or exposed the next defect more than a dozen times across
  R1-10, the R1-11 fix pass, and both verification passes — the
  verification pass produced most of this cycle's real findings and
  should stay mandatory after any pass touching honesty-critical
  paths. Two sharper forms earned in pass 2: a new guard is itself
  unreviewed code (two fresh pins reproduced the exact defect class
  they were written to prevent), and a self-check running the same
  machinery on both sides is blind by construction (V2-09).**
  Prior closeout state follows.
- Previous state (2026-07-21, first closeout): the SAPIENT lane is
  FULLY CLOSED — P1-07 mapping pack + reference adapters, the end-to-end
  wire validation against official Dstl tooling (PASSED; ULID findings
  fixed pre-release), and **v1.1.15 PUBLISHED** (release commit
  `bbd4c89`, publication record `f1c249a`, tag pushed, GitHub release
  live with eight assets marked Latest, CI green, checksums-only).
  Tree clean and in sync with origin at closeout.
  **Maintainer decision 2026-07-21 (closes the 2026-07-17 open item):
  a FULL fresh stack audit — not a scoped one — is the NEXT WORK ITEM
  (R1-11), to be run safely in a fresh session before any queued
  backlog resumes.** Inputs and method precedent are recorded in the
  handoff Next Work Queue item 1. Queued behind R1-11: the v1.1.0
  adoption-decision session (holding fielded command-loop evidence
  context and the SAPIENT evidence legs), the five deferred P1-06
  maintainer decisions, PR #4 status, and signing.
  Lane lessons worth carrying into R1-11 (recorded here so the audit
  can use them as lenses, per the R1-09/R1-10 pattern): (1)
  counterparty-official end-to-end validation catches a defect class
  that colocated tests AND adversarial code review both missed —
  wire-level id-format discipline (the ULID findings) surfaced only
  against Dstl's own validator; prefer official-tooling validation
  for every future mapping pack. (2) The release-currency machine
  check caught stale installation-guide pins mid-cut — the
  R1-10-built checking machinery is earning its keep. (3) The
  session-limit interruption recovery (resume with verify-and-complete
  prompts + a dedicated interruption-integrity review) left zero
  half-done state, twice validated as a working pattern.
- R1-11 execution continuity + HOLD (2026-07-22): the cycle ran across
  **four sessions broken by usage limits**, plus a mid-cycle model
  switch (Fable 5 → Opus 4.8, twice, from safeguards spuriously
  flagging routine work on this defensive ISR codebase) and one **full
  chat reset**. Recorded because interrupted work is its own defect
  surface. (1) The first post-fix verification audit was killed with
  **1 of 6 slices complete** — that lone slice had already found two
  defects the fix pass introduced; on resume its result was re-read
  rather than re-run, both were independently reproduced before fixing,
  and a third surfaced during the fix (→ `d955cd0`). (2) The next limit
  hit **mid-edit on a two-layer fix**, leaving the compact codec layer
  applied and the gateway backstop layer missing, uncommitted. **This
  is the dangerous class: a partial fix looks finished** — syntactically
  complete, imports clean, reads as deliberate. It was caught only
  because the resuming session started from `git status` and the real
  working diff. **Resume from the tree, never from the transcript.**
  (3) After the chat reset the recovering session had zero in-context
  memory and rebuilt state purely from the repo (git log, working diff,
  findings record, worklog) with the prior transcript supplied as data;
  everything in `6ea9888` was produced under that reconstruction.
  Residue checks run at freeze: full working-diff read before any new
  edit (caught the partial fix), full battery after every change set,
  finding list re-derived from audit output rather than memory,
  counts re-measured, UTF-8/mojibake scan on every edited doc (clean,
  no BOM), manifest regenerated and re-validated after every code
  change. **HOLD: held range `118f0b9`..`HEAD` (entire cycle, last code
  commit `6ea9888`), tree clean, nothing pushed/tagged/signed — a fresh
  full-stack audit runs before any release decision, with a targeted
  checklist in `docs/r1_11_full_stack_audit.md`.** This is the third validation of
  the interruption-recovery pattern (R1-09, R1-10, now R1-11), and the
  first under a full context reset — the pattern held, but only
  because state was reconstructed from artifacts rather than narrative.
- R1-11 post-fix verification passes (2026-07-21/22): **BOTH COMPLETE.**
  The R1-10 lesson — the fix pass is itself an audit surface — paid out
  twice more. Pass 1 (`d955cd0`) found three defects wave 1 had
  introduced or caused: (V1-01 MAJOR crash) the recovery path guarded
  only the FIRST encode, and because the diagnostic inherits the
  original's `event_id` as `original_event_id`, an event whose
  `event_id` was the unrepresentable part poisoned its own diagnostic —
  with `main()` catching only `KeyboardInterrupt`, one packet could kill
  a compact-output gateway for every producer; fixed with a fallback
  ladder ending at the `UNKNOWN` sentinel. (V1-02 MODERATE laundering)
  `verify_representable` compared an in-memory key remap that PRESERVES
  OBJECT IDENTITY, and Python container equality short-circuits on
  identity, so NaN — not equal to itself — passed verification and
  reached the wire with no RFC-8259 form; verification now runs through
  the real serialization boundary. (V1-03 MODERATE over-refusal) the
  byte-wise check refused SCHEMA-VALID events — **both bladeRF
  real-capture fixtures, this repo's own v1.1.16 corpus, were refused by
  compact egress over `.876Z` vs `.876000Z`, the same instant.** Wave
  1's tests used only whole-second timestamps. The check now recognizes
  exactly the two declared normalizations (UUID hex case; timestamp
  formatting at ms resolution); the `.000Z` refusal pin deliberately
  flipped to a normalization, with the sub-millisecond case replacing it
  as the honest refusal pin.
  Pass 2 (seven slices, 24 agents, every finding adversarially refuted
  before acceptance; 2 refuted) opened with these, and the second sweep
  below extended it to **14 findings total — 2 MAJOR, 7 MODERATE,
  5 MINOR**: (V2-01 MAJOR crash) the ladder catches only
  `CompactUnrepresentableError`, but the codec itself raises
  `OverflowError` (int ≥ 2**64), `ValueError` (nesting past CBOR decode
  depth — pass 1's real-serialization decode ADDED this path), and
  `OSError`/`RecursionError` on schema-valid input, each escaping and
  killing the process; fixed at two layers (codec converts its own
  failures; receive loop gained a per-datagram backstop) with the
  backstop's scope pinned by test — `recvfrom` stays OUTSIDE it so a
  dead listener still terminates, and `except Exception` never catches
  the `SystemExit` that reports an unusable config, so resilience never
  becomes concealment. (V2-02 MODERATE crash) `_find_forbidden_key`
  recursed, so deeply nested schema-valid JSON killed the gateway at
  INGRESS before egress on any encoding; now iterative breadth-first.
  (V2-03 MODERATE laundering) the R11-04 non-finite drop ran on 1 of 5
  SAPIENT ingress paths; a structural pin written to stop the guard
  drifting then showed **"five paths" was itself undercounted — there
  are SIX vendor-block sinks**, the missed one being the PLATFORM_STATUS
  event's verbatim `power` block (a non-finite `voltage` reached the
  wire even though `battery_pct` derived from that same block was
  guarded); all six now guard at the POINT OF USE, not once earlier in
  the function (the detection path dropped first and then assigned
  `vendor_ext["colour"]`, safe only by string-guard accident), with the
  invariant pinned by a source-level test. **Fixing this surfaced a
  second hole in the same helper — three cycles deep on this one class
  now** — dropping a bare non-finite LIST ELEMENT silently re-indexed
  positional numeric arrays (`[1.0, NaN, 3.0]` arriving as a clean
  two-element array); a non-finite element now drops the containing key. (V2-04 MODERATE
  enforcement) the R11-05 lint covered only per-producer rules, not the
  GLOBAL promotion block where most enforcement keys live — the same
  failure mode one block over — and additionally blessed per-producer
  overrides of global-only keys that enforcement never reads
  (`always_reject_loop_risk: false` on a producer changed nothing);
  **stress-testing the new lint caught it committing the same sin** —
  present-but-mistyped `degrade`/`quarantine`/`use_limits` sub-blocks
  were skipped, and a non-mapping there reverts the action to its
  built-in default, so they now fail (absence stays legal).
  (V2-05 MINOR over-refusal) compact epoch-ms routed through float
  seconds, landing 1 ms off for a date-banded fraction of schema-valid
  timestamps (480 of 8000 swept) and raising `OSError` on Windows for
  out-of-range instants; now exact `timedelta` integer arithmetic.
  (V2-06 MINOR honesty) non-string `ts` raised `AttributeError` past the
  documented None-refusal in both SAPIENT egress adapters, and the
  compact drop reason was the lone lowercase entry in a
  `SCREAMING_SNAKE` `drop_reasons` vocabulary that operators filter on.
  (V2-07 MINOR checking machinery) the overview currency guard matched
  one literal phrasing (`currently vX.Y.Z`) — shaped around the sentence
  the last regression happened to use — so `as of today, v1.1.9` / `pin
  to release v1.1.14` passed clean; replaced with a phrasing-independent
  superseded-release check, and **the first cut of the replacement was
  itself wrong** (lookahead rejected any version ending a sentence, the
  exact target shape), so the matcher now self-tests both directions.
  (V2-08 MINOR release machinery) `RELEASE_NOTES_TEMPLATE.md` still
  shipped the retired "D-003 remains roadmap-planned" line into every
  packaged note four releases after closure — R11-14 fixed the
  *validator* enforcing the claim but not the *template* emitting it;
  the same claim had two producers.
  A second nine-lens sweep over the RESULTING FIXES (85 agents, 29
  findings surviving adversarial refutation of 75 judged) added six
  more, headlined by **the most serious finding of the cycle: (V2-09
  MAJOR laundering/interop) compact representability depended on WHICH
  CBOR LIBRARY WAS INSTALLED.** The mapping's integer limit was left to
  the backend; `zmeta_cbor` correctly refuses an integer outside
  `[-(2**64), 2**64-1]`, but `cbor2` silently emits a bignum tag that a
  `zmeta_cbor` consumer decodes as raw BYTES — two conforming nodes
  disagreeing about the same event's meaning over a local install
  detail. **The round-trip self-check is structurally blind to this**:
  it encodes and decodes with the same library, so the corruption only
  appears on the receiving node. The codec now enforces the range
  itself on every backend, boundary pinned exactly, both regression
  tests run against both backends. Also: (V2-10) `_same_instant`
  compared two values already truncated identically at microseconds, so
  a 100-nanosecond instant compared equal to its ms round-trip while
  the codec claimed to refuse truncation; (V2-11) `_format_ts` crashed
  the PUBLIC decode path on a hostile epoch-ms value, outside the
  encode-side guard; (V2-12) four docs carry the identical pinned
  "Current release context" header but only the overview was guarded,
  so **three sat five releases stale** — the family is pinned now, plus
  a test that the pinned list still names every carrier; (V2-13) the
  package builder copied the notes TEMPLATE verbatim as each package's
  `RELEASE_NOTES.md` and nothing read its content, so the published
  v1.1.16 package ships "ZMeta Release Notes Template" with placeholder
  provenance beside `release_state: formal_release` while the real
  notes never entered the package (builder `--release-notes` +
  validator `RELEASE_PACKAGE_NOTES_PLACEHOLDER` + checklist step;
  published checksums untouched, effective next cut); (V2-14)
  `spec/release-signing-attestation.md`, a manifest-hash-pinned artifact
  validated every release, still asserted "D-003 remains the roadmap"
  for an item closed at v1.1.12, plus assorted stale literals — the
  compat CLI test's "current release target" now derives from the
  manifest rather than a pin.
  Live re-probe at close: the gateway survives every poison class
  (2**64 int, 300-deep nesting, 20k-deep raw JSON) with honest
  `ENCODING_UNSUPPORTED`/`SCHEMA_INVALID` diagnostics on the wire, the
  uppercase-UUID + millisecond-ts event forwards normally, and normal
  traffic still flows afterward — process alive throughout. Validation:
  kernel gate all flags (bad-events 29, harness 40), examples 51/51
  strict, packet size compact max=150 of 240 unchanged, pytest
  **742+237 → 785+316** zero failures, `git diff --check` clean.
  Governed regeneration: manifest + claims under the v1.1.16 identity
  (divergence record above continues to apply).
- R1-11 fix pass (2026-07-21): **ALL SEVEN WAVES COMPLETE** under the
  maintainer directive "give me a list... then lets work down that
  list" (R11-24 bladerf disclosure inventory cleared: "the bladerf
  stuff is good"). Wave -> commit map: (1) `74d92e1` compact
  fail-closed (R11-01 MAJOR; verify_representable self-check, gateway
  ENCODING_UNSUPPORTED in-band diagnostic, spec Scope section, CLI
  refusal; live UDP re-probe shows the diagnostic on the wire where
  the laundered STATE used to be); (2) `88b527e` SAPIENT adapter
  honesty (R11-02/-03/-04/-12/-20; sapient suites 117 -> 133 — the
  new NaN test caught a residual the audit probes missed:
  native_classification carried NaN verbatim, poisoning RFC-8259
  serialization; fixed with _drop_non_finite on native blocks);
  (3) `e3203ad` signalhunter no-lock + three-template loop_status
  (R11-06/-07; harness fixtures now pin the message-carried verdict
  VALUE); (4) `545fe0b` checking machinery (R11-05/-08/-09 + the
  SHA256SUMS immutability pytest pin; bad-events 27 -> 29, harness
  self-lints its corpus); (5) `c1eb9d0` machine-encoded semantics
  (R11-13/-21 + R11-04 validator side; Class B batch
  BEARING_FRAME_UNLABELED warn + NON_FINITE_CONFIDENCE fail, both
  enums, sanctioned); (6) `33230af` release machinery
  (R11-10/-14/-16; root-cause find during the fix:
  validate_release_package MACHINE-ENFORCED the stale "D-003 OPEN"
  claim — "known_open_issues must include D-003" — which is why it
  survived four releases; replaced with an attestation-mirrors-
  manifest check); (7) `05ad9a8` doc currency + teaching
  (R11-11/-15/-17/-18/-19/-23/-25; currency test extended to the
  body/worked-command surfaces that escaped one-line pins; contract
  5.3 last_sync_ts reading rule, Class B). Wave 1 additionally
  recorded the ENCODING_UNSUPPORTED Class B addition; wave 1's
  strict round-trip equality also surfaced the honest ".000Z"
  ts-normalization refusal case (pinned in tests). Not fixed by
  design: R11-22 (governed deviation, registration entry point stays
  queued in handoff 1a); R11-24 (cleared). **Divergence record (per
  the AGENTS.md rule this pass added): waves 1/3/4/5/6/7 regenerate
  the manifest/claims (and waves 6/7 the release package) under the
  v1.1.16 identity — current main diverges from the published
  v1.1.16 SHA256SUMS manifest/package pins; published checksums are
  immutable; resolution is the next release cut.** Validation at
  every wave boundary and final: kernel gate all flags green,
  examples 51/51 strict, pytest 687+172 -> 742+237 zero failures,
  git diff --check clean. Post-fix verification audit and the
  release-cut decision follow.
- R1-11 (2026-07-21): **FULL STACK AUDIT COMPLETE — findings record
  `docs/r1_11_full_stack_audit.md`, maintainer disposition RECORDED
  (fix pass directed and executed; see the fix-pass entry above).**
  Audited tree `09118b3`, strictly read-only. Method: green baseline
  (kernel gate all flags, examples 51/51, pytest 687+172 zero
  failures), then seven independent finder lenses (SAPIENT pack
  honesty; bladerf/external-fixture discipline + harness
  expressiveness; staged residuals/second-glance status; R1-10 +
  2026-07-01 regression; release/commit-truth 2a1e9ce..09118b3; doc
  currency/teaching; fresh-eyes core sweep), dedup, one adversarial
  verifier per substantive finding (sixteen), a DOC/OBSERVATION batch
  check, and a completeness critic whose two real gaps were closed by
  direct probes (B3 regression HOLDS via the 12-test checksum-floor
  family; R11-01 witnessed at live gateway process level, three
  legs). Verification changed severity in only 2 of 16 findings
  (R11-14 upgraded MINOR->MODERATE — the stale "D-003 OPEN" claim
  ships in manifests AND package attestations/release notes; R11-12
  reclassified same-severity), zero refuted — vs 7 of 16 changed in
  R1-10; refutation-first finder prompts removed the false-alarm mass
  before verification. Headline: **R11-01 (MAJOR) — the compact codec
  silently relabels v1.1.0 events as locked-v1.0 and destroys
  geo.error_ellipse_m; live-witnessed as a laundering bypass of the
  default gateway's own schema gate (honest JSON 1.1.0 event refused
  SCHEMA_VIOLATION; the identical event compact-encoded accepted,
  laundered, forwarded clean with zero diagnostics).** Remaining
  mass: R1-10 defect classes surviving as siblings where the fix
  pinned one exemplar (TaskAck 'None' coercion R11-03; loop_status
  self-assert in THREE templates R11-07; harness events-kind vacuity
  R11-08 + unlinted shipped corpus R11-09; one-line doc-currency pins
  R11-11/15/17/18), enforcement arriving after new governed surfaces
  (sapient policy block zero negative coverage R11-05; NaN confidence
  vacuity R11-04; fail-open egress risk set R11-02), signalhunter
  no-lock exposure worse than recorded (R11-06 — fabricated
  TRUE_NORTH bearing from null island), and formal-release manifests
  carrying placeholder provenance vs the hash-policy MUST (R11-10).
  Positive assurance: ALL R1-10 fixes and ALL 2026-07-01
  fielded-safety fixes hold (54+36+8 probe families, full refusal
  matrices); v1.1.15/v1.1.16 published assets verified to
  cryptographic digests with SHA256SUMS never modified post-release;
  every numeric claim in all ten commits of the stretch reproduces
  (the commit-truth discipline working); proto/CBOR codecs faithful
  on their claimed surfaces; SAPIENT honesty spine held under 20+
  adversarial probes; diagnostic emission set enum-complete in all
  four registries. Maintainer attention flags: R11-24 (bladerf pack
  public-disclosure inventory — already in git history and published
  assets, scrubbing main would not retract publication) and the
  R11-01 fix-priority call. Disposition and any fix pass to be
  recorded here when directed.
- P1-09 (2026-07-21): **PR #4 RESOLVED — closed unmerged with credit;
  harvest confirmed complete** (maintainer direction: stop waiting for
  contributor revisions; "review it and merge it... if we haven't
  already done so" — the review established we already had). Full
  re-review of the PR against main at v1.1.16: every component is
  HARVESTED (correlation pattern doc + 7-event corpus + crosswalk +
  corrected MQTT guidance, all crediting PR #4), REJECTED-RECORDED
  (payload_schema_uri "not re-litigated"; snapshot container;
  1.2.0 dispatcher — empirically breaks 13/40 v1.1.0 events), or a
  recorded evidence-gated candidate carrying the contributor's
  deployment as n=1 evidence (data-ref-media-metadata,
  correlation-identity, aggregate-state-snapshot). No contributor
  revisions ever arrived after the 2026-07-08 review (single commit,
  2026-07-01) — the v1.1.0 adoption session's "check PR #4 for
  revisions" input resolves to: none. Mechanical finding worth the
  record: the branch merges TEXTUALLY CLEAN into v1.1.16 (zero
  conflicts; 8 of 11 files new, the governed files it edits untouched
  since its branch point) and would be semantically catastrophic — the
  1.2.0 oneOf arm double-matches every v1.1.0 event and the 1.2.0
  stamp exempts producers from every locked invariant. A clean merge
  with no conflicts to force human review is the most dangerous
  dialect shape; recorded as an R1-11 lens. Residue implemented (the
  entire unharvested remainder of 1,053 lines): legacy-topic
  enumeration in the MQTT guidance legacy-paths section; a
  preview-thumbnail exclusion scope note on DATA_REF_MEDIA_METADATA
  (the exclusion is now a decision, not an omission); a Class D
  encoding-surface consequence note on the correlation-identity
  roadmap candidate. Manifest regenerated (v1.1.16 identity kept),
  full battery green (687+172, gate all flags, examples 51/51,
  roadmap candidates=18). PR closed with a credit comment pointing
  the contributor at the four registry entries and roadmap tripwires
  their telemetry seeded.
- P1-08 (2026-07-21): **v1.1.16 PUBLISHED** — release commit `f8951ee`,
  annotated tag pushed, GitHub release live with all eight assets
  marked Latest, CI green (run 29805064763), checksums-only (signing
  decision in the release notes). Contributor notified on PR #7 with
  the full fix rationale and an invitation to restore the canonical
  bearing with a producer frame assertion. Battery results in
  `release/VALIDATION_REPORT_v1.1.16.md`, including the verified-benign
  CRLF policy-hash print observation (canonicalized
  `policy_bundle_hash` byte-identical across v1.1.15/v1.1.16).
- P1-08 (2026-07-21): **PR #7 (edge-comms-bladerf real-capture pack)
  reviewed and MERGED with maintainer fixes** (maintainer-directed
  "run a full review on it and if it is all good, merge it"). Review
  method: close maintainer read + independent adversarial review
  attempting refutation against contract/validator/reference-adapter
  precedent, with every fixture field walked back to an input field or
  documented convention. Verdict: mergeable-with-maintainer-fixes —
  the contribution's honesty handling was strong as submitted (geo
  refusal incl. zero-island, case-01 bearing omission, repo-exact
  timing fallback, lineage omission, calibration default, producer
  matches the committed `rf-sensor-*` pattern; both fixtures pass
  strict H validation), and it is the first EXTERNAL real-capture
  corpus (second independent RF telemetry source — promotion-evidence
  relevant). Findings fixed on merge: (MAJOR) case-02 emitted a
  frame-unlabeled canonical bearing that is provably heading-derived
  (az == uas_heading + 56.0 exactly) with `heading_source:
  "interpolated"` naming a sampling method, not a frame — the machine
  gates pass it because the bearing_frame check is value-when-present
  (contract 6.4 tolerates legacy-unlabeled v1.0 bearings), so this was
  review-caught, not machine-caught; demoted to
  features.native_bearing_deg per AUTHORING rule 2 (we cannot mint a
  TRUE_NORTH assertion the producer did not make), with the
  frame-provenance route documented for deployments that can assert
  it. (MODERATE) undocumented 1_SIGMA metric dropped — raw bound kept
  as features.native_bearing_error_deg; timestamp_source provenance
  preserved (receive-time vs embedded-telemetry); mapping.yaml
  reconciled with fixtures (unconditional bearing row removed,
  conditional rules + missing entries added). (MINOR) FFT-bin-width
  bandwidth convention documented. Governance-record hunks
  (CHANGELOG/worklog/handoff, written against pre-v1.1.15 main) were
  NOT merged — re-derived maintainer-side per the intake doctrine.
  Disclosure note for the maintainer: the pack README publishes
  internal flight-artifact names, the platform identity, and detection
  frequencies with precise timestamps — retained as provenance
  evidence on the contributor's own initiative; flag if any of it
  should be scrubbed. Second-glance addition: the bearing_frame
  presence gap (canonical bearing without frame provenance passes all
  machine gates) is a candidate warn-check for R1-11.
- P1-07 (2026-07-21): **v1.1.15 PUBLISHED** (maintainer-directed "once
  the end to end validation is good, cut the release per the
  documentation"; agent-executed per RELEASE_CHECKLIST). Release
  commit `bbd4c89`, annotated tag `v1.1.15` pushed, GitHub release
  live with all eight assets and marked Latest, CI green for the
  release commit (run 29802675100), checksums-only (signing decision
  recorded in the release notes; signing remains the maintainer's
  external process). Doc-currency pass covered README, installation
  guide (5 pins — caught by test_release_currency, which is the
  machine check working as designed), professional overview, tools
  README, release README, check_compat TARGETS, CI compat target, and
  the release-manifest test pins. Retention pass: no worklog archival
  this cut (the archive last ran at P1-06; the resume-note retention
  extension remains an open maintainer decision). Full battery
  results in `release/VALIDATION_REPORT_v1.1.15.md`.
- P1-07 e2e follow-up (2026-07-21, maintainer-directed "run the follow
  up first then once the end to end validation is good, cut the
  release"): **end-to-end wire validation against official Dstl tooling
  PASSED** — Apex-SAPIENT-Middleware v4.2.0 (commit 0c8591a), its
  shipped BSI Flex 335 v2.0 pb2 modules + validator, stock strict
  config, Python 3.11/protobuf 4.25.1 per Apex pins. Egress: strict
  ParseDict + byte round-trip + validator clean for all mapped Task
  types and DetectionReport projections incl. the zmeta.risk/
  zmeta.timing_quality self-labels; live Apex accepted Registration
  (acked) and egress detections as-is, zero error records, zero Error
  replies. Ingress: official-pb2-built messages (validator-clean, both
  JSON spellings) → schema-valid ZMeta events, zero findings. The
  validation's first pass found a MAJOR + two MODERATEs, all fixed
  pre-release and re-verified clean: egress report_id was UUIDv7 where
  the proto demands ULID (now ULID minted from the event's own ts —
  new ulid_util.py, no wall clock); object_id/task_id pass-throughs
  now validate-or-refuse with a caller-owned object_map escape hatch
  (idempotency keys are never rewritten). Honest skip record: C# BSI
  Flex 335 v2 test harness (no .NET SDK on host) and multi-node Apex
  routing not exercised — open integration targets, recorded in the
  pack README Validation section. Egress tests 41→48; adapters suite
  243.
- P1-07 (2026-07-20): **SAPIENT / BSI Flex 335 v2.0 mapping pack +
  reference adapters** (maintainer-directed after a verified spec-level
  comparison and ecosystem review of SAPIENT — the UK MOD C-sUAS
  standard, NATO C-UAS standard per STANREC 4869/AEDP-4869, and the
  compliance baseline in NATO ACT's 2025 C-UAS RFI; analysis records
  held maintainer-side, outside the repo). What landed (Class A/C
  reference surface + two sanctioned governed touches):
  `adapters/mapping-packs/sapient-bsi-flex-335/` (declarative pack,
  schema_id `vendor:sapient_bsi335:v2`),
  `adapters/ingress/sapient/` (SapientMessage protobuf-JSON ingress:
  DetectionReport -> OBSERVATION + per-claim INFERENCE with
  registration-derived model identity; fusion-node -> STATE promotion
  gated on caller promotion metadata incl. caller-owned loop_status;
  StatusReport -> SENSOR_STATUS/PLATFORM_STATUS on the 1.1.0 branch;
  TaskAck -> TASK_ACK; Error -> SCHEMA_VIOLATION; RegistrationStore as
  the units-and-error codex), `adapters/egress/sapient/`
  (COMMAND_EVENT->Task for GOTO/TRACK_TARGET/CHANGE_SENSOR_MODE only,
  altitude structurally excluded; STATE->DetectionReport with
  zmeta.risk/zmeta.timing_quality self-labels and quarantine/
  prohibited-use export refusal), 12 adapter-harness fixtures
  (27 -> 39), the `sapient-ingress` producer-authority block (governed
  policy touch, mirrors cot-ingress), adapters/README rows, release
  manifest regen (governed; v1.1.14 identity kept). SAPIENT Task
  ingress (external DMM tasking ZMeta platforms) deliberately OUT of
  v1 — command-safety escalation avoided by scope.
  **Session-limit interruption + integrity audit:** a usage limit killed
  the wire/verify agents mid-pass (after the policy/README edits, before
  any lint). On resume, a dedicated interruption-integrity review passed
  all nine checks (sanctioned surfaces only; byte-level append-only
  proof for harness fixtures; hunk-by-hunk truncation hunt on the two
  interrupted files; claimed-vs-on-disk file reconciliation; no stray
  artifacts; locked kernel untouched; style/pack/policy conventions
  faithful; no CRLF/mojibake; clean pytest collection). The
  adversarial honesty review then found four real defects, all fixed
  with tests: (1) unknown active_mode silently dropped the
  maximum_latency est_error_ms widen -> conservative cross-mode
  fallback; (2) signal[] entries past the first vanished -> preserved
  as vendor.sapient.signal_additional; (3) the promotion path
  self-asserted loop_status CHECKED_NOT_REFLECTION -> now refused
  unless caller-supplied (deliberate divergence from the CoT template,
  which can receive it message-carried); (4) out-of-range protobuf
  Timestamp raised out of translate() -> fail-closed refusal.
  **Accepted deviations (adjudicated at closeout):** unregistered-node
  detections refuse entirely (the build-spec's obs-still-emitted
  variant would have required fabricating a modality — refusal over
  fabrication ratified); four registration-dependent harness fixtures
  are structurally inexpressible (the harness passes JSON-only kwargs
  and cannot construct a RegistrationStore) — coverage lives in the 110
  colocated pytest tests; ingress ships without __init__.py per the
  klv-pair precedent.
  **Second-glance register additions:** (a) cot_to_zmeta_template still
  defaults promotion loop_status to CHECKED_NOT_REFLECTION — same
  pattern the SAPIENT fix removed; should sync with the paused CoT
  egress findings cluster. (b) Harness gap: fixtures cannot construct
  non-JSON objects; a module-level entry point taking registration
  message dicts (e.g. translate_with_registration_msgs) would make the
  four missing fixtures one-liners — candidate, not built. (c) SAPIENT
  branch-evidence items recorded, not implemented: RADAR-family
  modality feature contracts (roadmap-queued; radar/lidar/seismic
  ingress currently degrades to inference/promotion paths),
  track-lifecycle vocabulary (SAPIENT evidence thin: free-text state
  only), tasking verbs (LOOK_AT, multi-waypoint patrol, task-cancel).
  (d) Egress detection projection emits full proto enum names
  (proto3-JSON wire form) — protobuf wire encoding itself remains
  out-of-scope, documented.
  **Validation:** full kernel gate green all flags, examples 51/51,
  full pytest 680 passed + 172 subtests zero failures (570 -> 680),
  adapter harness 39/39, policy lint ok, manifest regenerated +
  validated (groups=19 artifacts=70), git diff --check clean.
- R1-10 AAR (2026-07-17), maintainer side — the full audit -> fix ->
  verify -> release cycle as an exercise of the R1-09 AAR's own
  lessons. **What happened:** the R1-10 stack audit ran the R1-09
  lessons as lenses (teaching artifacts, prose-only vs machine-pinned,
  falsifiable evidence, doc currency) plus a 2026-07-01 defect
  regression check — five independent finder passes, then sixteen
  adversarial verifiers, one per substantive finding, each instructed
  to refute with live probes. Verified findings: seven MAJOR, four
  MODERATE, eight MINOR plus the doc-currency list; three initial
  HIGHs dissolved to MINOR because the governance record documented
  the deferral. The maintainer directed fix-every-finding then
  re-audit. The fix pass ran as six dependency-ordered waves
  (adapters; harness+validators/policy/schema; tools; contract; docs;
  governed regen) with disjoint file ownership, committed at wave
  boundaries. A session usage limit killed the doc-sweep agent
  mid-pass; the relaunched wave completed, and a six-slice
  verification audit afterward (interrupted-wave item-by-item, live
  re-probes of every original audit probe, commit-truth verification
  of every commit message, findings-coverage critic) confirmed the
  interruption left zero half-done file state. That verification
  audit also caught two MAJOR residues the fix pass itself introduced
  — the GEO_ZERO_FILL_SUSPECTED warn code was omitted from the
  diagnostic enums, so the gateway destroyed its own zero-fill
  warning diagnostic before egress (proven live); and the manifest
  regeneration diverged from the published SHA256SUMS_v1.1.13 pin —
  plus commit-evidence inaccuracies. Residues were fixed (6f47237),
  the divergence was resolved by the maintainer-directed v1.1.14 cut
  (f9241c4), run strictly per RELEASE_CHECKLIST with the full battery
  green. Eleven commits total, b826445..0cb5407. **Why the defects
  existed:** the v1.1.13 refusal doctrine was machine-pinned on
  example-vendor only — the same fabrication class survived in every
  other reference adapter because fix-plus-fixture ran once, not
  per-surface; honesty invariants stated in the contract but
  schema-inexpressible had no policy/validator encoding; the checking
  tools trusted their inputs (empty-file vacuity); and current-facing
  doc claims lived only in prose. **What held under stress:** the
  locked kernel (byte-stable minus sanctioned diagnostic enums, all
  2026-07-01 fielded-safety fixes re-verified by fresh probes);
  the governance record — three findings dissolved precisely because
  deferrals were documented where an auditor would look; the manifest
  hash gates (every governed drift caught, honest regen forced); the
  release checklist (run literally, its new currency test made an
  incomplete doc pass impossible — 26 pinned-surface tests gated the
  release commit); and wave-boundary commits with disjoint ownership,
  which is why a hard mid-pass interruption cost nothing. **Lessons:**
  (1) Machine-pinning one exemplar does not propagate — when a
  doctrine lands, the fix-plus-fixture loop must run per reference
  surface, and the harness must be able to EXPRESS the doctrine for
  every callable shape (the None-refusal register gap blocked refusal
  fixtures for single-event adapters until fixed). (2) Adversarial
  verification pays twice: it kills false positives AND calibrates
  severity — unverified severity did not survive in seven of sixteen
  findings, every change downward or refuted-as-framed: exactly the
  false-alarm mass verification exists to remove before a maintainer
  spends attention on it. (3) The fix pass is itself an audit surface:
  both post-fix MAJORs were introduced BY the fixes (one by the
  auditor's own wrong adjudication that warn codes are never cited in
  diagnostics); fix work gets the same falsifiable-evidence discipline
  as releases, including an end-to-end probe of each new check's
  emission path, not just its detection path. (4) Recorded evidence
  must be counted, not estimated: three commit messages carried
  numeric claims that do not reproduce ("35 tests" vs 30 collected;
  "917" vs 916 lines; "21 tests" unreproducible) — corrections
  recorded here per the falsifiable-evidence rule; commit messages are
  immutable, so the worklog carries the corrections. (5)
  Forward-looking status claims in committed docs are interruption
  hazards — the one cutoff artifact was a "queued, landing in later
  commits" CHANGELOG bullet the later commits never flipped; write
  past-tense records, or flip forward references in the commit that
  lands them. (6) Environment honesty: Windows CRLF materialization
  made container and local gateway startup hash prints diverge on
  identical content — the manifest's canonicalized hashes are the
  authoritative gate; a .gitattributes LF pin would retire the whole
  class (maintainer decision, flagged below). Net enforcement growth
  across the cycle: pytest 485 -> 570 (subtests 110 -> 172), harness
  fixtures 15 -> 27, bad-events 23 -> 27, four governed diagnostic
  codes, and five new test families (release-currency, input floors,
  inverse coverage, strip guard, zero-fill warn). Nothing in the
  cycle touched locked-kernel semantics; every fix landed in the
  outer rings — the design working as claimed, again.
- Second-glance register from the R1-10 closeout (recorded so nothing
  lives only in session context; none are defects, all are candidates
  for the next audit or maintainer decisions): (a) unencoded
  SHOULD-level conventions found by the audit's conventions lens but
  below the findings bar — fusion/state confidence exceeding the
  weakest material input (contract 8.3) has no warn-check;
  gateway-backfilled `t_publish` carries no gateway-supplied marker
  (contract 5.2); `lineage.transform` prefix shape
  (`translate:`/`promote:`) is harness-checked only when a fixture
  opts in; published historical `SHA256SUMS_*.txt` immutability has
  no pytest pin. (b) signalhunter residuals (flagged in the fix-pass
  entry above). (c) a pre-existing worktree at `.tmp/review-pr-2`
  (branch `review/pr2-frame-fixes`) — outside the canonical tree,
  keep-or-prune is a maintainer call. *(Still open 2026-07-27: the
  worktree still exists; re-homed to the handoff's live maintainer
  queue so it is not buried by archival.)* (d) `.gitattributes` LF
  normalization would retire the CRLF materialization class (container
  hash prints, historical checksum-entry caveat) — governance-adjacent
  because it changes working-copy bytes for hashed files; escalated,
  not applied. (e) the worklog resume note is growing and the archive
  policy covers completed task sections only — a retention-policy
  extension for superseded resume-note bullets is a maintainer
  decision. **RESOLVED 2026-07-27 (maintainer-directed at closeout:
  "do any updates, edits and pruning needed"): the policy is extended
  to cover superseded resume-note bullets of COMPLETED, PUBLISHED
  cycles — append-moved VERBATIM to
  `docs/zmeta_refinement_worklog_archive.md`, never deleted, never
  summarized away.** Two guards, both from this cycle's own lessons:
  a bullet is only movable once its cycle is published (so no live
  context is archived), and any still-open pointer inside a bullet is
  re-homed to the handoff's live queue BEFORE the move (so archiving
  never buries an open item — the CR-03 class in reverse). (f) UxS command-loop fielding roadmap (maintainer
  discussion, 2026-07-17): display loop fieldable now; GCS-originated
  tasking needs the command-evidence lineage check (commands citing
  motivating inference/fusion parents, gateway-checked against
  upstream `use_limits`) plus a SITL end-to-end gate;
  platform-to-platform retasking additionally needs authenticated
  transport (deployment-side) and the track-lifecycle promotion (this
  deployment is the roadmap tripwire evidence); the v1.1.0 adoption
  session should take the command-loop evidence as input. *(Status
  2026-07-27: the command-evidence lineage check SHIPPED in v1.1.18
  (`policy/command-evidence.yaml` + gateway enforcement), and the
  track-lifecycle work landed as a current-vocabulary pattern doc with
  the roadmap candidate deliberately left RESERVED — the multi-UxS
  deployment is the awaited second evidence leg. Still open and
  re-homed to the handoff's live queue: the SITL end-to-end gate and
  authenticated transport, both deployment-side.)*
- R1-10 (2026-07-17): **v1.1.14 released** (maintainer-directed,
  agent-executed) — the audit-driven honesty hardening cut, run
  strictly per RELEASE_CHECKLIST. Content: the seven R1-10 fix-pass
  commits plus the verification-audit fixes (see the fix-pass entry
  below). Validation battery all green: manifest regenerated and
  validated for zmeta-v1.1.14 (groups=19, artifacts=70; claims synced
  and verified with --verify-contract-hash), full kernel gate with all
  flags (bad-events 27, adapter harness 27), strict examples 51/51,
  policy risk lint, future-roadmap validation, full pytest 570+172
  zero failures, risk-filter presets, workflow end-to-end (H and M —
  CoT output now carries event-authoritative time, the honest default
  visible on the wire), live gateway (JSON and compact-L), three
  gateway self-tests, compat sweep 9/9 corpora at v1.1.14, packet-size
  max=150 of 240, bundles + release package built and validated
  (package zip auto-built at checksum time), containerized gateway
  verified (build, run, replay received, no violations; the
  container-vs-Windows startup hash print difference is CRLF
  materialization — the manifest's canonicalized hashes are the
  authoritative gate and pass identically), SHA256SUMS_v1.1.14.txt
  written LF and verified with full coverage, git diff --check clean.
  Doc-currency pass executed per the checklist (README release section
  + v1.1.14 integration notes, installation guide, professional
  overview, tools README, release/README, check_compat TARGETS +
  v1.1.14, CI compat target, compat CLI test, release-manifest test
  pins; test_release_currency green against the v1.1.14 manifest).
  Signing decision: checksums-only, stated in the release notes.
  Retention: nothing newly archivable (fix-pass records are current
  context). Publication confirmed (2026-07-17): release commit
  `f9241c4`, annotated tag `v1.1.14` pushed, GitHub release live with
  all eight assets and marked Latest
  (<https://github.com/JTC-byte/zmeta-spec/releases/tag/v1.1.14>),
  GitHub CI passed for the release commit, body carries the release
  notes including checksum verification instructions. Checksums-only;
  signing remains the maintainer's external process.
- R1-10 fix pass + verification (2026-07-17, maintainer-directed "fix
  every issue found, then re-audit"): every audit finding fixed or
  documented-deferred across nine commits — ddd0252 (audit record),
  06a576f (reference-adapter honesty pass: null-identity refusal,
  eo-cv confidence/geo fixes, kraken+moth JSON-replay refusal matrices
  including the contract 6.8 moth alt_m fix, CoT honest defaults,
  template lineage docstring, plus two same-class in-pass finds),
  cf4e7da (checking machinery: empty-input floors in all eight gate
  tools, checksum coverage cross-check + LF endings, manifest-derived
  defaults, release-currency test, claims-validator residues,
  kernel-gate examples wiring), e07af84 (machine-encoded honesty:
  v1.1 quality bearing_frame/heading_source constraints with
  version-agnostic checks, INFERENCE fused-state denylist completion,
  zero-fill warn heuristic, protected strip paths, harness refusal
  register + surplus-expectation guard, refusal-fixture rollout
  15 -> 27, bad-events 23 -> 27, three governed diagnostic codes added
  to both schema enums per the D-013 pattern), ef08974 (doc
  currency/retention sweep, ten items), a1bfa1f (contract 2.1/5.7
  clarifications, Class B), 0da1a5c and the closeout commit (manifest
  + claims regenerated, release identity preserved), 6f47237
  (verification-audit fixes). The session-limit interruption mid-pass
  left no half-done file state (verified hunk-by-hunk). Post-fix
  verification audit (six adversarial slices: interrupted-wave
  item-by-item, live re-probes of every original audit probe at HEAD,
  commit-truth verification of all messages, findings-coverage
  critic): the pass held; residues found were fixed in 6f47237 —
  GEO_ZERO_FILL_SUSPECTED diagnostic coherence (the gateway's own
  zero-fill warning diagnostic was schema-invalid and destroyed before
  egress; now in both enums + allowed list with an inverse-coverage
  test), CoT point@hae unknown-convention on absent alt_m and
  missing-ts refusal outside wall-clock mode, sign-script
  manifest-derived default, and a --verify-contract-hash zero-claims
  floor. Commit-evidence corrections recorded per the
  falsifiable-evidence rule (messages are immutable history; the
  record is corrected here): cf4e7da says "35 tests added" — 30
  collect; ef08974 says handoff "917 -> 727 lines" — the before-count
  is 916; e07af84 says "reason-code sync suite 21 tests, 116
  subtests" — the file collects 5 tests, 116 subtests (the 21 does
  not reproduce). Recorded, maintainer decision pending: the
  regenerated in-repo manifest diverges from the manifest entry pinned
  in the published SHA256SUMS_v1.1.13.txt (published checksums are
  immutable; resolution is the next release cut or an explicit
  accepted-divergence record). Flagged residuals for the next audit
  (in-pass observations, deliberately not fixed this pass):
  signalhunter .bin replay stamps wall-clock ts at translation time
  (honestly labeled UNSYNCED, but an A4 sibling class); signalhunter
  GPS no-lock (0,0) passes into quality.sensor_position_2d unguarded
  (the new zero-fill warn covers canonical geo, not
  sensor_position_2d); signalhunter's internal GPS-frame dict carries
  a dead alt_m 0.0. Final validation: full kernel gate green with all
  flags (bad-events 27, adapter harness 27, claims=2 including
  --verify-contract-hash), strict examples 51/51, full pytest 570
  passed + 172 subtests with zero failures, diff-check clean. Net
  enforcement growth across the pass: pytest 485 -> 570 tests
  (subtests 110 -> 172), harness fixtures 15 -> 27, bad-events
  23 -> 27, plus the release-currency, input-floor, inverse-coverage,
  strip-guard, and zero-fill test families.
- R1-10 (2026-07-16): full stack audit executed per the queued
  direction, applying the R1-09 AAR lessons as audit lenses (teaching
  artifacts, prose-only vs machine-pinned conventions, falsifiable
  evidence, doc currency/retention) plus a regression check of the
  2026-07-01 audit defects and governed-artifact integrity. Method:
  verified-green baseline first (kernel gate, pytest 485+110 zero
  failures, diff-check clean at `b826445`), five independent finder
  passes, then every substantive finding adversarially verified by an
  independent skeptic pass with live probes — post-verification
  severities recorded; three findings dissolved to MINOR precisely
  because the governance record documented the deferral (command-
  altitude synonym residual per the v1.1.10 Known Enforcement
  Limitation; track-lifecycle per the s1-01 do-not-add decision and
  roadmap branch; locked-schema diagnostic enum additions per their
  Class B record). Audit was read-only; tree untouched. **Verdict: the
  kernel and governance apparatus held** — 2026-07-01 fielded-safety
  defects re-verified fixed by fresh probes, manifest tamper detection
  witnessed, locked v1.0 schema byte-stable since v1.1.10, all
  machine-pinned release surfaces correct. **The defect mass is in the
  outer rings, exactly where the AAR predicted:** the reference
  adapters the authoring guide routes authors to carry unfixed
  instances of the fabrication class v1.1.13 machine-pinned on
  example-vendor only (null-identity coercion in the worked exercise;
  eo-cv fabricated confidence 0.0 / null-confidence crash / alt_m
  zero-fill; kraken+moth JSON-replay fabricated RF defaults; moth geo
  alt_m zero-fill — a contract 6.8 MUST violation; CoT egress
  fabricated ce/le accuracy and wall-clock-fresh timestamps live by
  default on the gateway --emit-cot path). Latent honesty gaps with no
  machine check: quality.bearing_frame/heading_source unconstrained in
  both schemas (the only v1.0 frame-provenance channel),
  gateway strip config can silently delete risk_adjudication (declared
  never_mutable; shipped configs clean, so latent), INFERENCE nested
  estimated_state/members laundering residue (policy denylist never
  expanded when STATE/COMMAND were), zero-fill geo passes clean.
  Checking-machinery vacuities: all eight JSONL gate tools pass on
  empty input (manifest pinning backstops conformance/** in CI; the
  unprotected surface is examples/*.jsonl — unpinned, unfloored,
  absent from the local kernel-gate command), harness expect.events
  overhang silently unevaluated with event_count optional, checksum
  verification accepts empty/partial files. Doc currency: every defect
  prose-side, none machine-pinned — installation guide stale at
  v1.1.12 (a checklist-NAMED surface, the item's second confirmed
  miss), release/README at v1.1.11 and contradicting the reconciled
  never-hand-zip rule, professional overview stale, handoff internally
  inconsistent about the current release with under-executed
  retention, check_compat CLI default three releases stale, two bundle
  builders with stale version constants (the sign-script default's
  unenumerated siblings). Full tiered findings, evidence anchors,
  refuted items, and positive-assurance record:
  `docs/r1_10_full_stack_audit.md`. **Maintainer disposition: fix every
  finding (six-part fix pass recorded in the audit doc's disposition
  section), then a follow-up audit.**
- Previously queued (2026-07-08, now queue item 2): the all-fourteen
  v1.1.0 adoption-decision session — worksheet plus decisions in one
  session, promotion evidence bar as the standard, check PR #4 for
  contributor revisions first.
- R1-09 AAR (2026-07-16), maintainer side — the PR #5/#6 -> v1.1.13
  exchange as a red-team exercise against the standard's own claims,
  agent-guidance docs, and workflows. **What happened:** two
  onboarding PRs from the external-adopter thread (P1-05/P1-06, authored
  maintainer-side; driver: a multi-sensor drone/COP team onboarding
  through an AI coding agent — the first adopter cohort onboarding from
  scratch through the authoring path) were red-teamed maintainer-side,
  with every finding adversarially verified before posting; the review
  record, including refuted findings, lives on the PR #5/#6 threads.
  Surviving findings clustered exactly where the standard predicts risk:
  the teaching adapter emitted schema-invalid output instead of refusing
  (bandwidth_hz), the canonical EO example taught a bounding-box dialect
  contradicting the reference adapter it mirrored, one commit message
  recorded validation evidence that did not reproduce, and one intake
  template misparaphrased the governed promotion evidence bar. Rework
  came back as fix commit (#5) + rebase (#6, because a false validation
  claim must not become immutable history) + an additive commit
  institutionalizing the lessons (AUTHORING §3 rule 10, §9 failure
  modes); the delta re-verification (recorded on the PR #6 thread)
  confirmed zero drift beyond the approved fix list and that every
  commit-message validation claim reproduced at review time. Then,
  maintainer-directed: fast-forward merges preserving
  the reviewed SHAs, intake labels, the AAR's machine-encoding candidate
  implemented (harness `event_count` refusal pins, corpus 11 -> 15,
  lint-schema sync test), and the v1.1.13 cut run strictly per
  RELEASE_CHECKLIST — which itself got red-teamed by being run: it was
  missing the release-manifest test pins (found by pytest mid-release,
  item amended), the package zip had no producing script (now auto-built
  by `sign_release_artifacts.py`, tested both directions), the signature
  items were unskippable-yet-always-skipped (now conditional behind an
  explicit signing-decision line), and `sign_release_artifacts.py`
  carried a stale VERSION default (bumped; added to doc-currency).
  **Why:** green-path authoring (schema requiredness lives per-subtype in
  the schema; the guide didn't say to read it); secondhand summaries
  instead of primary sources (the example mirrored a description of the
  eo-cv adapter, not its code); evidence recorded as ritual rather than
  as commands run where they could fail; checklist items written before
  ever being exercised. **What held under stress:** every
  schema/policy-checkable dishonesty was caught mechanically the moment
  failing input was exercised; everything that escaped lived only in
  prose — the exact boundary the refusal fixtures now move; dialect
  drift was caught in the canonical imitation source before external
  agents could learn it; the manifest-hash gates enforced the
  governed/advisory boundary mechanically all the way through (nothing
  hashed moved without maintainer direction, and when directed, the gate
  forced honest regen); authority order and release limits held — agent
  execution, human decision at every irreversible gate (merge, publish,
  cut). Net enforcement growth across the exchange: harness fixtures
  11 -> 15, strict examples 47 -> 51, pytest 465 -> 485 tests (+110
  subtests). **Lessons, zmeta side:** (1) teaching artifacts are the
  highest-leverage defect surface — agents copy them verbatim; red-team
  them before merge, always. (2) When review catches a prose-only
  convention violation, the fix is two-part: correct it AND ask what
  fixture/test would have caught it — that loop is what produced
  `event_count`; conventions encoded as fixtures get caught, conventions
  living in prose escape. (3) Validation evidence must be falsifiable:
  name the exact command, run where it can fail (now practiced by the
  release commit itself). (4) The release checklist is a living gate:
  its first honest end-to-end exercise found four gaps — one amended
  mid-run (the test pins), three reconciled in the immediate post-release
  follow-up — keep running it literally every release. (5) The
  cross-session pattern that worked: PR threads for the durable review
  record, direct session messages for awareness; rebase-vs-fix-commit
  decided by whether a false claim would become immutable. (6)
  Maintainer-side tooling (first bite, recorded): two Windows-shell
  text-processing near-misses in one cycle (a WinPS Get-Content/
  Set-Content round-trip mojibake'd README UTF-8, caught and reverted
  before commit; a quote-mangled `git commit -m` that loudly failed) —
  prose edits belong in file tools or python, commit messages in
  `git commit -F`; one hygiene bullet added to CLAUDE.md. Nothing in
  this exchange required touching the locked kernel: the outer rings
  (docs, examples, fixtures, tooling, policy-adjacent conformance)
  absorbed all of it, which is the design working as claimed. Meta-note:
  this AAR entry was itself fact-checked against the repository record
  before commit; the check found and corrected five inaccuracies in the
  draft — including an overclaim inside lesson (4), the lesson about
  falsifiable evidence — which is lesson (3) demonstrating itself.
- R1-09 follow-up (2026-07-16): intake funnel closed
  (`blank_issues_enabled: false` + a fourth "General question or report"
  template labeled `question`) and the two release-flow friction points
  from the v1.1.13 retrospective reconciled — the package zip is now
  auto-built at checksum time by `release/sign_release_artifacts.py`
  (tested both directions: builds when missing, never overwrites), and
  the checklist marks signature items signed-releases-only with an
  explicit signing-decision line. Maintainer-directed.
- R1-09 publication confirmed (2026-07-16): release commit `1117bc6`,
  annotated tag `v1.1.13` pushed, GitHub release live with all eight assets
  and marked Latest, CI green on the release commit (2/2 runs), body
  includes checksum verification instructions. Checksums-only; signing
  remains the maintainer's external process.
- R1-09 (2026-07-16): **v1.1.13 released** — merged PR #5 then PR #6
  (fast-forward, no squash, reviewed SHAs preserved), created the three
  intake labels (`adapter-authoring`, `field-telemetry`,
  `semantic-ambiguity`), and cut the release per RELEASE_CHECKLIST
  (maintainer-directed, agent-executed). Release content beyond the merged
  PRs (Class B, maintainer-directed): the adapter harness gains
  `expect.event_count` (0 pins fail-closed refusal — the P1-06 AAR's
  machine-encoding candidate, now implemented); must-pass corpus 11 -> 15
  (example-vendor emission fixture + one refusal fixture per
  schema-required RF input field, negative-probed non-vacuous);
  `fixture.schema.json` learns `event_count` and
  `gateway/tests/test_fixture_schema_sync.py` pins lint-schema/harness
  sync. Doc-currency pass run per the new checklist item (README release
  section + v1.1.13 integration notes, tools README, CI compat target,
  compat CLI test, check_compat TARGETS + v1.1.13, release-manifest test
  pins); the checklist item itself was improved mid-pass — it did not name
  the `gateway/tests/test_release_manifest.py` `release_id`/`release_date`
  pins, which full pytest caught (checklist-usefulness verdict: the new
  items work; first exercise found and closed one gap). Validation: full
  kernel gate green (harness 15), 51/51 strict examples, pytest 483+110
  zero failures, compat sweep of all nine corpora at v1.1.13 clean,
  self-tests/e2e/live/packet-size ok, containerized gateway verified
  (recv/fwd, zero violations), manifest + claims regenerated for
  zmeta-v1.1.13, checksums written and verified — checksums-only, signing
  remains the maintainer's external process. Retention pass: P1-05/P1-06
  resume-note entries retained as current context (most recent sessions);
  nothing newly archivable ahead of this release.
- P1-06 AAR (2026-07-16): the maintainer review of PRs #5/#6 doubled as the
  first external red-team pass of the authoring guide, and the findings are
  institutionalized rather than just fixed. Finding: every caught defect's
  rule already existed in-repo — the in-repo normative docs were sufficient
  (the guide itself had one gap, closed as the section 3 rule below), the
  validators flagged every schema-checkable issue instantly once the failing
  input was exercised, and the escapes were prose-only conventions (bbox
  dialect) plus author-workflow failures. Actions: the four review-proven
  failure modes are now
  AUTHORING.md §9 agent guidance (primaries-not-summaries; refusal tests per
  required field; guide-as-checklist against your own exemplar; exact
  evidence commands), and the one true doc gap is closed as §3 rule 10
  (schema minimums are per-subtype; requiredness from the schema, never
  from sample inputs). Candidate machine-encoding follow-up recorded, not
  implemented: "refusal fixtures" for the adapter harness (callable must
  return an empty result for a given input) so fail-closed behavior is
  pinned the way must-pass pins emission — conventions encoded as fixtures
  get caught, conventions living only in prose escape.
- P1-06 (2026-07-15): onboarding batch on current `main` (Class A docs +
  Class C reference; no governed-artifact change). Follows P1-05 from the
  same external-adopter thread. (1) README restructured for first contact —
  ten-minute proof path, Start Here By Role, ZMeta In The Field (fielded
  EO/CV + RF provenance of the Production adapters, deployments unnamed
  pending maintainer decision); (2) worked exercise
  `adapters/ingress/example-vendor/` implementing the example-vendor pack to
  the AUTHORING.md requirements (12 tests; adapters README table gains this
  row plus the missing JREAP row); (3) `tools/check_adapter.py` one-command
  ladder wrapper + advisory `conformance/adapter-harness/fixture.schema.json`
  (all 11 existing fixtures lint clean); (4) GitHub issue templates
  (authoring friction / semantic ambiguity / deployment field report) + PR
  template; (5) retention: worklog S0-01..R1-05 archived verbatim to
  `docs/zmeta_refinement_worklog_archive.md`, new `docs/README.md`
  guidance-vs-process index, RELEASE_CHECKLIST doc-currency + retention
  items. Deferred to maintainer: naming the fielded deployments; the
  `mavlink_to_zmeta_template.py` rename (governed fixture + classes refs);
  physical `docs/process/` move (5 governed refs in conformance_classes);
  mechanical claim generator; v1.1.0 adoption decision (already queued).
  Maintainer-review fixes folded in the rebase: bandwidth_hz is now
  fail-closed with a refusal test (the schema's RF minimum feature set made
  the optional-bandwidth path emit schema-invalid events — the teaching
  adapter violated the rule it teaches); the profile kwarg/stamp dropped
  (gateway-added export metadata, contract 3.4); check_adapter gained an
  empty-input guard, flushed step headers, and honestly scoped wording;
  fixture-schema `expect.events` made exclusive of silently-ignored sibling
  keys; the field-report template points at the evidence bar instead of
  paraphrasing it; handoff pointers updated for the worklog/archive split;
  the archive's trailing blank line stripped (verbatim-move separator, not
  section content).
  Validation: example-vendor tests 12/12, check_adapter full ladder PASS,
  strict examples 51/51, full kernel gate green, pytest failure set
  unchanged vs clean main (Windows MAX_PATH tmp-path artifact), git diff
  --check clean against the merge base.
- P1-05 (2026-07-15): adapter-author onboarding consolidation on current
  `main` (Class A docs + examples; no schema, policy, vocabulary, or
  validation-behavior change). Driven by external-adopter demand (a
  multi-sensor drone/COP team onboarding via an AI coding agent): (1) new
  `adapters/AUTHORING.md` — the single consolidated authoring entry point
  (orientation, decoded-input floor, layer-choice table with nearest
  reference per input kind, the anti-fabrication non-negotiables with
  contract cites, the exact validation command ladder, a formal
  adapter-harness fixture-key reference, producer-authority and
  definition-of-done notes, AI-agent guardrails), linked from
  `adapters/README.md`; (2) new `examples/zmeta-eo-chain-examples.jsonl` — a
  worked EO full chain (OBSERVATION -> INFERENCE -> FUSION -> STATE, genuine
  chained lineage, policy-allowed producers `eo-camera`/`eo-cv-adapter`/
  `fusion-engine`, local mp4 `data_ref` pointer, no raw features on STATE)
  as the EO companion to the core RF chain, registered in
  `tools/validate_examples.py` (corpus 47 -> 51) and the examples README.
  Validation: new corpus 4/4 strict, full strict examples pass, full kernel
  gate, and full pytest green (results in the handoff).
  Classification note (maintainer review): the `tools/validate_examples.py`
  registration edit is a validator change — Class B under the governance
  taxonomy, not plain Class A — and it grows what CI `--require-all`
  enforces (47 -> 51). Its Class B requirements (docs, fixture-by-example,
  full kernel gate, pytest) were met in this same change and the file is not
  manifest-hashed; future corpus additions should classify as Class B rather
  than cite this entry as Class A precedent.
- S1-26 (2026-07-08): prepared v1.1.12 (governance and honesty closeout) on
  current `main` per explicit maintainer direction to work the full
  relock-gap list. Delivered: (1) promotion evidence bar in
  `spec/extension-registry.md` + change-governance Class D — moving
  reserved/proposed concepts into a version branch now requires two or more
  independent implementations demonstrating the need plus a documented
  contract Section 2.6 failure condition the outer rings cannot solve;
  (2) S1-11B implemented — `spec/future-branch-roadmap.yaml`/`.md` (18
  candidates with evidence + tripwires, 3 recorded rejections/deferrals,
  including the PR #4 tranche-3 candidates and honesty-primitive schema
  standing), `tools/validate_future_roadmap.py`, tests, and a new
  `future_branch_roadmap` release-manifest group (groups=19, artifacts=70);
  D-003 closure condition met, closure recommended (maintainer call);
  (3) lineage honesty — kraken/moth/signalhunter/klv/mavlink/eo-cv no longer
  fabricate `lineage.based_on` with random UUIDv7s: observation/system
  outputs omit lineage unless callers pass real `based_on`;
  mandatory-lineage events refuse to emit without real parents (mavlink
  STATE needs `based_on`/`source_zmeta_event_id`; eo-cv INFERENCE needs
  `parent_event_ids` or a UUIDv7 `source_event_id`); adapter versions
  bumped; harness fixtures updated + 1 new caller-lineage fixture (total
  11); new eo-cv test file; ingress template README never-fabricate rule;
  (4) gateway UDP send containment — `_send_datagram` catches OSError
  (oversize ~65507-byte sends), drops with new `send_failure`
  metrics/diagnostics instead of crashing the main loop; real-socket
  oversize test proves it; (5) truth-in-advertising — mapping-packs README
  states no runtime engine executes `mapping.yaml` (declarative packs +
  adapter code + test evidence); (6) honesty-primitive enforcement home
  documented in the professional overview (policy + conformance is the
  intended home; schema standing parked as an evidence-gated roadmap
  candidate); (7) handoff human-decision list resolved to standing defaults
  with two genuinely open items (signing process — maintainer generating a
  signature 2026-07-08; v1.1.0 adopted-vs-experimental). Validation: full
  kernel gate green (projection 37, registry 61, classes 34/2,
  encoding-negative 50, precision 32, bad-events 23, adapter 11), roadmap
  validator ok (18/3), examples 47/47, policy lint ok, pytest 465 + 110
  subtests, workflow end-to-end H/M, live gateway JSON/compact, gateway
  self-tests x3, check_compat v1.1.12 for all 8 corpora, packet-size
  max=150/240, release package ok, checksums ok. Release commit carries
  notes/report/SHA256SUMS_v1.1.12.txt; annotated tag created locally;
  publication (push, GitHub release, optional signatures) remains with the
  release authority.
- R1-08 (2026-07-08): `v1.1.12` published per explicit release-authority
  direction — `main` and the annotated tag pushed (release commit `e5a88b1`),
  GitHub CI green for the pushed commit, GitHub release created with all
  eight assets including `SHA256SUMS_v1.1.12.txt`, marked Latest. Published
  checksums-only per the maintainer's direction; he is standing up the
  signing process for the next release. Post-publication alignment updated
  current-facing docs (README, installation guide, tools README,
  professional overview), the CI compatibility target, and the compatibility
  CLI test to `v1.1.12`. **D-003 closed by maintainer decision** in the same
  pass: the roadmap artifact + registry + evidence bar now track future
  branch work individually (register entry updated). The deferred issue
  register is now fully closed — D-001 through D-014 all resolved.
- S1-24 session record (at the time, the current next work item): S1-24
  prepared the v1.1.10 fielded-safety enforcement
  release on then-current `main` — command-altitude denylist completion to the full
  §7.8 set, a recursive STATE laundering check with whitespace/case key
  normalization plus the full §7.7 list, adapter calibration honesty
  (Kraken/Moth stop hardcoding `CALIBRATED`; default conservative
  `UNCALIBRATED`), and egress MAVLink altitude-guard alignment — with eleven new
  deep-nested bad-event fixtures, two direct `validate_semantics` unit tests,
  adversarial bypass verification, and a regenerated release manifest and
  claims. The full kernel gate and pytest are green.
- R1-06 publication note: the release authority published `v1.1.10` on
  2026-07-04 — annotated tag on release commit `6ce4f29`, GitHub release with
  all seven expected assets plus `SHA256SUMS_v1.1.10.txt`, CI green.
  Published checksums-only, consistent with v1.1.5 through v1.1.9; detached
  signatures remain an optional release-authority step. A post-publication
  alignment pass (2026-07-07) updated current-facing docs, tool examples, the
  CI compatibility target, and the compatibility CLI test to the published
  `v1.1.10` baseline without touching any published release assets.
- S1-25 (2026-07-07): prepared v1.1.11 (field-driven adoption guidance).
  Upstream PR #4 — a v1.2.0 proposal from a live at-scale ZMeta deployment
  (multi-node drones/sensors, fusion engine, custom COP, TAK bridges) — was
  reviewed against the locked kernel and NOT merged: empirically verified
  that its v1.2.0 schema arm breaks oneOf dispatch for all v1.1.0 events and
  drops every locked invariant (command altitude, STATE laundering,
  confidence placement, UUIDv7, UTC-Z all accepted under a "1.2.0" label);
  review with evidence posted on the PR. The legitimate fielded needs were
  re-derived from the kernel outward: three advisory docs (MQTT binding
  guidance, vocabulary crosswalk, correlation pattern), four
  extension-registry entries (CORRELATION_HINT proposed,
  DATA_REF_MEDIA_METADATA proposed, AGGREGATE_STATE_SNAPSHOT reserved,
  PAYLOAD_SCHEMA_URI rejected), a 7-event runnable correlation example
  corpus, and two bad-event anti-laundering fixtures (corpus 23). No schema,
  policy-behavior, or vocabulary change. R1-07: published 2026-07-08 with
  explicit release-authority direction — annotated tag `v1.1.11` on `922f0ca`,
  GitHub release with all eight assets including `SHA256SUMS_v1.1.11.txt`,
  CI green; checksums-only, consistent with v1.1.5 through v1.1.10. Optional
  future work remains S1-11B future-branch roadmap artifact (now informed by
  PR #4's data_ref-enrichment and correlation requirements), adapter-harness
  breadth from real sensor captures, or deployment/container runtime breadth.
- Current-main audit note: the final baseline audit corrected two missed
  current-facing guidance examples to the `v1.1.8` target: the adapter
  `check_compat` invocation and the change-governance manifest rebuild command.
  Published `SHA256SUMS_v1.1.8.txt` and release assets remain unchanged.
- Final closeout note: S1-22 completed a full baseline audit and notes/log
  refresh. Current `main` is clean and pushed at `c814d95`; GitHub CI passed;
  local validation covered the governed kernel gate, examples, release
  manifest/package validation, full pytest, workflow/live gateway smoke tests,
  direct focused validators, package/bundle builders, Docker Compose config
  rendering, stale/secret/generated-artifact scans, and GitHub PR/issue queue
  checks. No baseline blockers remain.
- Documentation freshness note: S1-23 audited the README-linked documentation
  surface on 2026-06-18, refreshed `spec/installation-guide.md` around the
  maintained `configs/` templates and current validation gates, corrected stale
  `beffed3` final-closeout references to `c814d95`, verified tracked
  Markdown/TXT relative links, and found no rogue untracked files outside
  expected ignored local/build outputs.
- Decision of record at the time of S1-24: ZMeta v1.1.10 was the then-current
  formal release target for the
  fielded-safety enforcement baseline (command-altitude denylist completion,
  recursive STATE laundering enforcement with key normalization, adapter
  calibration honesty). It preserves the locked v1.0 schema and does not make
  v1.1.0 concepts valid under `zmeta_version: "1.0"`.
  S1-12C audited the D-012 formal release
  packaging framework and closed D-012. S1-13A audited the stack for semantic
  conformance and stale files, corrected the live compatibility checker and CI
  target to `v1.1.5`, added explicit v1.0/v1.1.0 observation extension boundary
  tests, and closed D-009.
  S1-14 implemented external projection promotion hardening for CoT/JREAP/
  MAVLink state ingress through producer-authority policy, adapter metadata,
  conformance/tests, and operator-tunable reject/warn/degrade/quarantine
  enforcement while preserving Profile L compact handles.
  S1-15A added the risk adjudication semantic baseline: locked/tunable/advisory
  rule classes, bounded policy actions, filterable risk diagnostics, and
  operator override constraints.
  S1-15B conformed the stack to that baseline across policy use limits,
  validator diagnostics, gateway runtime degradation labels, conformance
  fixtures, tests, and audit docs.
  S1-15C cleaned up semantic-contract feedback: Section 14 now defers lossy
  tactical ingress promotion to Section 4.5.1, material risk self-labels and
  safety/promotion override evidence are stronger, and conformance classes now
  cover policy adjudication, external promotion, and risk filtering.
  S1-16A added semantic bad-event fixtures and the shared adapter conformance
  harness, promoted `ZMETA-ADAPTER` and `ZMETA-COT-PROJECTION` to implemented,
  and left broader `ZMETA-SENSOR-ADAPTER` certification planned.
  S1-16B added the kernel-protection doctrine: complete without exhaustive
  mission ontology, a high threshold for future core semantic changes, and
  `FUTURE_EXTENSION` as the non-claimable class for future/reserved/planned
  semantics.
  S1-17A audited the tracked stack against that doctrine, found no live
  schema/runtime/adapter/encoding/vocabulary drift, and promoted full
  kernel-protection conformance to CI, Makefile, and release checklist usage.
  S1-18A added consumer-side accepted-risk filtering with operator presets for
  display, fusion, state, command, autonomy, AAR, and audit intake posture.
  S1-18B completed an end-to-end stack and runtime audit, hardened direct CoT
  egress against malformed state payloads carrying raw observation/evidence
  fields, and verified schema/policy/conformance/examples/gateway/live
  workflow/release-package/bundle-smoke paths.
  R1-02 published `v1.1.6` with source, edge, gateway, release package,
  manifest, notes, validation report, and checksum assets. P1-01 addressed
  partner feedback by documenting external-promotion upgrade responsibilities,
  clarifying that `trust_ref` is policy-scoped evidence rather than
  authenticity proof, strengthening downstream consumer responsibility for
  accepted-risk labels, and adding a policy lint that flags unsafe `ignore`
  settings on material risk. P1-02 added machine-checkable profile-projection
  preservation for `payload.extensions.risk_adjudication` and compact
  `payload.extensions.external_promotion` evidence, strengthened the extension
  registry entry contract with validated projection/risk/security/fixture
  fields, and rebuilt the current-main release manifest and example claim
  hashes. P1-03 added formal human/AI agent change governance through
  `AGENTS.md` and `docs/zmeta_change_governance.md`, linked it from public
  entry points, added downstream clone interoperability limits, and added
  governed release-manifest coverage for process guidance. R1-03 audited the
  current stack for stale release references, ignored local build residue, and
  tracked-source secret/generated-artifact risk; updated active release
  surfaces to v1.1.7; built source, edge, gateway, release package, manifest,
  notes, validation report, and checksum assets for publication.
  P1-04 closed the bearing reference-frame ambiguity: a normative section 6.4
  true-north rule with convert-or-omit, an optional v1.1.0 `bearing.frame`
  marker, the experimental `BEARING_FRAME` registry entry, bad-event and
  adapter-harness enforcement with value-level `expected_values` pinning,
  Kraken heading compensation plus fabricated-SNR removal, Moth fabricated
  omnidirectional-bearing removal, SignalHunter/MAVLink frame-provenance
  audit fixes, and MAVLink null-island, gateway oversize-datagram, and
  rate-limiter runtime guards. The locked v1.0 schema is untouched.
  R1-04A completed the post-release current-reference cleanup after the full
  stack audit: `README.md`, tool examples, the CI compatibility target,
  professional overview, compatibility CLI test, handoff, and worklog now
  point current-facing guidance at `v1.1.8`; historical `v1.1.7` release
  records and published checksum files remain unchanged.
  D-003 remains `OPEN - ROADMAP PLANNED`. D-004 remains closed as removed from
  ZMeta scope. S1-19 closed D-013 and D-014 by adding negative TIME_STATUS age
  diagnostics and compact unknown-integer-key rejection. S1-20 added advisory
  industry-sharing, contributor-authority, conformance, name-use, and
  defensive-publication posture without changing schemas, policy behavior,
  event vocabulary, or the locked v1.0 kernel. S1-21 incorporated post-release
  feedback by clarifying current-main adapter upgrade guidance and recording
  that frame assertions are producer provenance, not proof. S1-22 completed
  the final baseline audit/closeout and updated durable plus local notes.
  S1-23 refreshed README-linked documentation and install guidance. R1-05
  publishes those current-main updates as the v1.1.9 formal patch release.

