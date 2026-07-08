# ZMeta Refinement Worklog

## Current Resume Note

- Last updated: 2026-07-07
- Quick handoff: `docs/zmeta_refinement_handoff.md`
- Current next work item: S1-24 prepared the v1.1.10 fielded-safety enforcement
  release on current `main` — command-altitude denylist completion to the full
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
  `v1.1.10` baseline without touching any published release assets. Optional
  future work remains S1-11B future-branch roadmap artifact, adapter-harness
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
- Current decision: ZMeta v1.1.10 is the current formal release target for the
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

## Deferred Issue Register

### D-001 - MAVLink Adapter README State Payload Drift

- Status: CLOSED
- Discovered during: S0-01 / S0-02 review
- Issue: `adapters/ingress/mavlink/README.md` describes several platform-state
  telemetry values as mapping to `payload.features.*`, while STATE_EVENT
  semantics prohibit raw `features` and the current implementation uses
  quality-style metadata.
- Impact: Documentation drift can encourage future adapter authors to place raw
  telemetry features in STATE_EVENT payloads.
- Proposed follow-up: Docs/adapter cleanup task. Do not change during S0-02
  because this work item is semantic-contract-only.
- S1-08A cleanup: Corrected the MAVLink ingress README to prohibit raw
  `payload.features.*`, raw measurements, observation modality fields,
  observation time windows, and raw data references in STATE_EVENT payloads.
  The README now maps MAVLink state inputs to state-safe fields,
  `payload.quality`, SYSTEM_EVENT status, OBSERVATION_EVENT where a true
  supported modality applies, and lineage. Implementation inspection found no
  STATE_EVENT raw-feature emission, so no D-012 follow-up was needed. D-001 is
  closed.

### D-002 - Contract Hash / Release Hash Follow-Up

- Status: CLOSED
- Discovered during: S0-02
- Issue: Rewriting `spec/semantics-contract.md` changes the normative contract
  hash used by gateway/deployment hash gates.
- Impact: Deployments with `require_contract_hash` or release validation assets
  will need an intentional hash update in a later release task.
- Proposed follow-up: Recompute contract hashes and update release/checklist
  artifacts only when the stack-hardening branch is ready.
- S1-09A coverage: Planned a release-hash strategy that keeps the narrow
  semantic contract hash separate from schema, policy, registry, conformance,
  projection, encoding, precision, release-manifest, and release-bundle hashes.
  The plan recommends `release/zmeta-release-manifest.yaml`, deterministic
  build/validation tooling, deployment gate behavior, and conformance claim hash
  integration. No hashes were recomputed and D-002 remains open pending
  implementation.
- S1-09B coverage: Implemented `spec/release-hash-policy.md`,
  `release/zmeta-release-manifest.yaml`, deterministic build and validation
  tooling, focused tests, optional `--release-manifest` conformance integration,
  and claim hash updates. D-002 remained open pending S1-09C audit.
- S1-09C audit: Verified the release hash policy, manifest structure, artifact
  groups, canonicalization, builder/validator behavior, claim integration,
  gateway-compatible hash behavior, optional conformance integration, and tests.
  Fixed post-checkpoint manifest reproducibility by replacing default current
  git metadata with stable placeholders for committed reference manifests.
  D-002 is closed.

### D-003 - Future Semantics Require Versioned Implementation Branches

- Status: OPEN - ROADMAP PLANNED
- Discovered during: S0-02
- Issue: The rewritten contract defines future candidates for markings,
  integrity, anti-replay, trust, MODEL_STATUS/ASSURANCE_EVENT, PNT integrity,
  UAS identity, coalition export, projection metadata, data nutrition labels,
  and emergency/L0 behavior.
- Impact: These concepts are intentionally not valid event vocabulary yet.
- Proposed follow-up: Create dedicated versioned prompts for schema, policy,
  adapter/gateway, encoding, examples, and conformance implementation after
  approval of each extension branch.
- S1-11A coverage: Planned the future versioned semantic branch roadmap,
  candidate inventory, sequencing, dependency map, extension-registry
  interaction, conformance-class interaction, release/hash impact, and standard
  Sx-A/Sx-B/Sx-C implementation pattern. No branch was implemented and no
  future vocabulary became valid.

### D-004 - Out-of-Scope Artifact Set

- Status: CLOSED - REMOVED FROM ZMETA SCOPE
- Discovered during: S0-02 research review alignment
- Issue: D-004 was determined to be outside the ZMeta semantic standard.
- Impact: Keeping this issue active would risk pulling organizational artifact
  scope into a semantic data standard.
- Resolution: S1-10P removed D-004 from active ZMeta scope. ZMeta will remain
  focused on event semantics, profiles, adapters, encodings, validation,
  conformance, and release baselines.

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

- Status: CLOSED
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
- S1-03C audit: Confirmed registry shape, status/category semantics, version
  boundary checks, reserved/proposed invalidity, tests, documentation, and
  optional conformance integration. D-006 is closed.

### D-007 - Encoding Negative Validation Gap

- Status: CLOSED
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
- S1-05A coverage: Planned a dedicated encoding-negative fixture strategy,
  validator/tooling approach, compact/protobuf negative categories,
  gateway/CLI path coverage, policy/context model, and conformance-class impact
  recommendations.
- S1-05B coverage: Implemented `conformance/encoding-negative/` fixtures,
  standalone validator CLI, opt-in conformance runner integration, focused
  compact/protobuf/gateway tests, and class evidence updates for compact CBOR
  and protobuf projection.
- S1-05C audit: Verified fixture breadth, stable failure codes, validator
  behavior, gateway/CLI parity, opt-in conformance integration,
  conformance-class evidence, and absence of schema/contract/registry drift.
  D-007 is closed.

### D-008 - Conformance Class Manifest Missing

- Status: CLOSED
- Discovered during: S0-03
- Issue: The semantic contract defines ZMETA-CORE, ZMETA-PROFILE-L/M/H,
  ZMETA-ADAPTER, ZMETA-GATEWAY, ZMETA-COT-PROJECTION,
  ZMETA-AI-PROVENANCE, ZMETA-COALITION-EXPORT, ZMETA-MESH-TRUST, and
  ZMETA-REPLAY classes, but the repo does not yet provide a machine-readable
  class claim/test matrix.
- Impact: Implementations can run tests, but they cannot yet make precise,
  repeatable conformance claims by class.
- S1-04A coverage: Planned `spec/conformance-classes.md`,
  `conformance/conformance_classes.yaml`, example claim files, standalone
  validation tooling, focused tests, optional conformance runner integration,
  class status model, claim model, dependencies, required test mappings, and
  S1-04B implementation path.
- S1-04B coverage: Implemented `spec/conformance-classes.md`,
  `conformance/conformance_classes.yaml`, example claim files, standalone
  validation tooling, focused tests, optional conformance runner integration,
  class status model, claim model, dependencies, and required test mappings.
- S1-04C audit: Verified class record shape, status semantics, claim
  dependency/evidence enforcement, future/reserved/planned non-claimability,
  partial-class overclaim protection, docs alignment, optional conformance
  integration, and absence of schema/contract/registry drift. D-008 is closed.

### D-009 - v1.0/v1.1 Observation Extension Boundary Needs Explicit Tests

- Status: CLOSED
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
- S1-13A coverage: Added explicit
  `gateway/tests/test_schema_version_discrimination.py` cases proving that
  structurally valid generic v1.0 observation extension fields do not adopt the
  stricter v1.1.0 EO/ACOUSTIC feature contracts, structured quality contract,
  or formal data-reference contract. D-009 is closed without schema,
  contract, policy, registry, adapter, encoding, or vocabulary changes.

### D-010 - Profile Precision / Quantization Policy Floors

- Status: CLOSED
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
- S1-06A coverage: Planned precision ceilings, utility floors, quantization
  steps, conservative rounding directions, packet-budget interaction, policy
  artifacts, fixtures, validator behavior, gateway/exporter approach, optional
  conformance integration, and S1-06B/S1-06C path. D-010 remains open until
  implementation and audit.
- S1-06B coverage: Implemented the reference precision policy artifact,
  source/projected fixture suite, standalone validator, focused tests, optional
  `--precision-policy` conformance runner flag, and class/claim evidence
  updates. D-010 remains open as `OPEN - IMPLEMENTED PENDING S1-06C AUDIT`.
- S1-06C audit: Verified policy quality, field-family coverage, Profile H/M/L
  behavior, conservative rounding, fixture coverage, validator behavior,
  packet-budget guardrails, projection interaction, optional conformance
  integration, conformance-class evidence, and absence of schema/contract/
  registry/vocabulary drift. D-010 is closed.

### D-011 - Crosswalk TAKEOFF Mention Cleanup

- Status: CLOSED
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
- S1-03C audit: Added validator and test coverage proving `TAKEOFF` remains
  invalid under v1.0/v1.1.0 and fails registry validation if it appears in a
  current schema enum/const. The crosswalk typo itself remains open for a narrow
  docs cleanup task.
- S1-07A cleanup: Corrected the crosswalk row to remove `TAKEOFF` and list only
  the actual supported v1.1.0 expanded task values. The remaining `TAKEOFF`
  references are invalidity guards or historical cleanup notes. `TAKEOFF`
  remains invalid current vocabulary, and no schema or extension registry
  artifacts were changed. D-011 is closed.

### D-012 - Formal Release Tag, Signature, and Attestation Packaging

- Status: CLOSED
- Discovered during: S1-09C
- Issue: The S1-09B/S1-09C reference hardening-baseline manifest is
  reproducible and sufficient to close D-002, but it is not a formal tagged
  release package with signed artifacts, post-release claim attestations, and
  final release commit metadata.
- Impact: Deployments can validate the governed reference baseline now, but a
  public or operational release may still need a tagged release, release notes,
  validation report, checksums, signatures, and post-release claim attestations.
- Proposed follow-up: Plan and implement formal release tag, signature, and
  attestation packaging when the hardened stack is ready for a published
  release. Do not reopen D-002 for this packaging work.
- S1-12A coverage: Planned the formal release artifact model, release state
  model, tag naming, signing strategy, attestation/provenance contents, key and
  secret handling rules, formal workflow, consumer verification workflow,
  S1-12B tooling path, S1-12B test strategy, and S1-12C closure strategy. No
  signatures, keys, tags, schemas, release manifests, validators, runtime code,
  or vocabulary were changed.
- S1-12B coverage: Implemented the release signing/attestation specification,
  release package templates, no-signature package builder, package validator,
  no-secret scanner, optional conformance flag, focused tests, docs updates,
  and release manifest `release_packaging` group. No real tags, signatures,
  keys, secrets, schemas, semantic contract text, extension registry entries,
  conformance class status, gateway runtime behavior, adapters, codecs, or
  event vocabulary were changed.
- S1-12C audit: Verified release packaging behavior, template safety,
  no-secret checks, generated package validation, optional conformance
  integration, release manifest validity, and absence of semantic/vocabulary
  drift. Removed D-012 from open-issue defaults after closure. D-012 is closed.
- R1-01 publication: Published `v1.1.5` from commit
  `d4d406b43a705ca5b7a314e1d5388c3ca39c750a` with release notes, validation
  report, release manifest, release package zip, edge/gateway/source bundles,
  and checksum manifest. No detached signatures were attached because no
  approved local signing key was available. D-012 remains closed because the
  packaging framework is implemented and audited; future detached signatures are
  a release-authority operation, not a reopened baseline-hardening issue.

### D-013 - Timing-Freshness Negative-Age Clamp Hides Producer Clock Anomalies

- Status: CLOSED
- Discovered during: P1-04 code-review lead verification (verified line by
  line; deferred because the fix needs new semantic surface)
- Issue: `gateway/src/validators.py:1430` clamps the event-versus-TIME_STATUS
  age with `max(0.0, ...)`, so a negative age (event timestamp earlier than
  the TIME_STATUS reference would allow) validates as "fresh". This conflates
  benign out-of-order delivery with producer clock anomalies. Freshness
  validation compares only producer-supplied timestamps with each other, so a
  self-consistently wrong producer clock validates cleanly. No existing
  violation code covers negative age (current codes:
  `TIMING_STATUS_MISSING`/`STALE`/`UNSYNCED`/`HOLDOVER_NON_MONOTONIC`), and
  contract section 5.10 locks timing semantics in v1.0.
- Impact: A producer with a skewed or manipulated clock can present stale or
  future-dated observations as fresh, and the gateway has no diagnostic label
  for the anomaly.
- Proposed follow-up: New `TIMING_STATUS_AGE_NEGATIVE` warn code, a
  `max_negative_age_ms` policy knob, and an optional `t_receive` plausibility
  check, implemented as a governed Class B/D change with conformance fixtures.
  Not implemented in P1-04 because it adds violation-code vocabulary and
  policy surface to locked v1.0 timing semantics.
- S1-19 closure: Implemented the governed diagnostic and policy surface.
  Validators now preserve raw negative age, tolerate only profile-configured
  small negative intervals, and emit `TIMING_STATUS_AGE_NEGATIVE` with timing
  risk labels beyond tolerance. Default reference policy warns; deployments may
  tune to reject or degrade. Added schema/policy reason-code coverage, compact
  reason-code mapping, focused tests, and core conformance coverage. The
  optional `t_receive` plausibility check was not added because gateway
  `t_receive` stamping happens after inbound validation and is latency/AAR
  metadata rather than producer timing authority.

### D-014 - Compact Codec Degrades Unknown Integer Payload Keys on Re-Encode

- Status: CLOSED
- Discovered during: P1-04 code-review lead verification (verified line by
  line; deferred because the fix needs spec text and a fixture decision)
- Issue: `zmeta_compact.py` decode converts unknown integer payload keys to
  `str(key)`, while encode passes string keys through unchanged. A
  decode-then-re-encode cycle therefore degrades a future integer key `99` to
  the string key `"99"` on the wire. `spec/compact-binary-mapping.md` is
  silent on unknown integer keys, and no encoding-negative fixture covers the
  path.
- Impact: Future compact-mapping key assignments silently lose their compact
  form through any decode/re-encode relay, and the degradation cannot be
  distinguished from a producer that genuinely sent the string key `"99"`.
- Proposed follow-up: Add spec text stating unknown integer keys MUST be
  rejected at decode, add a compact must-fail encoding-negative fixture, and
  align the decoder, as a governed Class B change. Rejection is preferred over
  re-mapping because re-mapping cannot disambiguate a genuine string key
  `"99"` from a degraded integer key 99.
- S1-19 closure: Implemented compact v1 decode rejection for unknown integer
  keys in governed compact maps, added spec text, preserved string extension
  keys, and added a generated encoding-negative fixture that fails before
  schema/policy validation as `ENCODE_NEGATIVE_UNKNOWN_COMPACT_KEY`.
