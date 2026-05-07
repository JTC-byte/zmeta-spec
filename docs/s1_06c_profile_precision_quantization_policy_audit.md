# S1-06C Profile Precision / Quantization Policy Audit

Status: COMPLETE
Date: 2026-05-07
Scope: Audit S1-06B implementation. No schemas, semantic contract text,
extension registry artifacts, gateway runtime behavior, codecs, adapters,
release hashes, or event vocabulary were changed.

## Summary

S1-06B implemented a reference conformance default profile precision policy for
Profile H/M/L exports. The implementation added a human-readable policy guide,
a machine-readable policy artifact, source/projected precision fixtures, a
standalone validator, focused tests, an opt-in conformance runner flag, and
profile/projection conformance-class evidence.

The audit verifies that precision policy is treated as profile/export policy,
not schema. It constrains conservative projection of already-valid events and
does not create semantics, mutate stored source events, alter compact/protobuf
codec semantics, or make future vocabulary valid.

## Files Inspected

- S1-06B diff at `ecd049f61335d67d28972757bf90a2edc535ac10`
- `docs/s1_06_profile_precision_quantization_policy_plan.md`
- `spec/profile-precision-policy.md`
- `policy/profile-precision.yaml`
- `conformance/profile-precision/README.md`
- `conformance/profile-precision/context.jsonl`
- `conformance/profile-precision/must-pass.jsonl`
- `conformance/profile-precision/must-fail.jsonl`
- `tools/validate_precision_policy.py`
- `gateway/tests/test_profile_precision_policy.py`
- `tools/validate_conformance.py`
- `spec/profile-compatibility.md`
- `spec/profile-projection-field-catalog.md`
- `conformance/profile_projection_field_catalog.yaml`
- `tools/validate_projection.py`
- `spec/compact-binary-mapping.md`
- `spec/protobuf-encoding.md`
- `tools/validate_encoding_negative.py`
- `conformance/conformance_classes.yaml`
- `conformance/claims/example-reference-gateway.yaml`
- `conformance/claims/example-core-producer.yaml`
- `tools/validate_conformance_classes.py`
- `spec/conformance-classes.md`
- `spec/semantics-contract.md`
- `schema/README.md`
- `schema/zmeta-event.schema.json`
- `schema/zmeta-event-1.0.schema.json`
- `schema/zmeta-event-1.1.0.schema.json`
- `spec/extension-registry.md`
- `spec/extension-registry.yaml`
- `policy/profiles.yaml`
- `policy/semantics.yaml`
- `policy/timing-freshness.yaml`
- `policy/lineage.yaml`
- `policy/routing.yaml`
- `gateway/src/gateway.py`
- `gateway/src/validators.py`
- `zmeta_compact.py`
- `zmeta_cbor.py`
- `zmeta_proto.py`
- `conformance/README.md`
- `spec/README.md`
- `docs/zmeta_refinement_worklog.md`
- `docs/zmeta_refinement_handoff.md`
- Existing profile, projection, encoding, gateway tests, and Profile H/M/L
  examples.

## Files Changed During S1-06C

- `docs/s1_06c_profile_precision_quantization_policy_audit.md`
- `docs/zmeta_refinement_worklog.md`
- `docs/zmeta_refinement_handoff.md`

No implementation cleanup was required.

## Drift Checks

Schema drift: none. The S1-06B diff did not include
`schema/zmeta-event.schema.json`, `schema/zmeta-event-1.0.schema.json`, or
`schema/zmeta-event-1.1.0.schema.json`.

Semantic contract drift: none. `spec/semantics-contract.md` was not changed.

Extension registry drift: none. `spec/extension-registry.yaml` was not changed.

Conformance class manifest validity: valid. The manifest and example claims
validate after the precision evidence updates.

New vocabulary check: no new event vocabulary became valid. No v1.1.0 concept
was promoted from experimental to adopted, and no reserved or future registry
concept became valid vocabulary.

## Human-Readable Spec Review

`spec/profile-precision-policy.md` clearly states that precision policy:

- does not create semantics;
- constrains conservative projection of already-valid ZMeta events;
- is profile/export policy, not schema;
- is not release policy, trust policy, emergency mode, UI policy, or transport
  semantics;
- uses reference conformance defaults that require mission review;
- does not mutate source events;
- applies at explicit export/projection time;
- requires rejection or omission rather than misleading export when utility
  floors cannot be met;
- preserves units, identity, source, lineage, semantic layer, event time, and
  discriminator paths;
- only permits confidence preservation or reduction;
- only permits TTL preservation or shortening;
- only permits error/timing uncertainty preservation or upward rounding;
- forbids packet-budget pressure from stripping required semantic fields;
- keeps compact CBOR and protobuf as encoding projections.

## Machine-Readable Policy Review

`policy/profile-precision.yaml` includes the required top-level sections:

- `policy_version`
- `policy_name`
- `policy_status`
- `requires_mission_review`
- `zmeta_versions`
- `profiles`
- `field_families`
- `immutable_paths`
- `unit_locked_paths`
- `rounding_modes`
- `utility_floors`
- `precision_ceilings`
- `packet_budget_guidance`
- `notes`

The policy uses `policy_status: reference_conformance_default` and
`requires_mission_review: true`. Profile H, M, and L are present. Candidate
numeric values are documented as reference defaults, not final operational
mandates.

Immutable paths include the required identity, source, lineage, event time,
track identity, and payload discriminator paths:

- `zmeta_version`
- `event.event_id`
- `event.event_type`
- `event.event_subtype`
- `event.ts`
- `source.platform_id`
- `source.node_role`
- `source.producer`
- `lineage.based_on`
- `lineage.transform`
- `payload.track_id`
- `payload.modality`
- `payload.inference_type`
- `payload.task_type`
- `payload.system_type`

## Field-Family Coverage Review

Covered by policy and fixtures:

- immutable identity, source, lineage, and discriminator paths;
- geospatial state and command target fields;
- altitude, heading, speed, bearing field families in policy;
- TTL and timing/error-bound fields;
- RF center frequency, bandwidth, and power;
- top-level confidence;
- display strings `payload.class` and `payload.source_summary` through preserve
  or cataloged omission behavior.

Intentionally limited or future/mission-specific:

- `event.t_receive`, `event.t_publish`, and `profile` remain export metadata
  governed primarily by the projection catalog and gateway policy.
- `payload.t_start` and `payload.t_end` are observation timing fields; current
  precision-policy fixtures focus on state/command/system/RF projection and do
  not add new observation timing semantics.
- `payload.features.signature_hash` is preserved in RF fixtures and is not
  quantized; changing it would be a non-precision semantic change.
- General `payload.quality` and v1.1.0 structured quality remain branch- or
  mission-specific. The policy covers timing-quality error fields that exist in
  current v1.0 examples.
- UI/rendering `extensions` are not quantified by the reference policy and
  remain governed by schema/profile policy and future mission rules.

These limitations do not block D-010 closure because the reference policy now
defines the core current precision floors and conservative rounding behavior
needed for Profile L/M/H conformance. Broader field-family tuning remains a
mission-review decision.

## Profile H/M/L Policy Review

Profile H preserves source precision by default and does not force unnecessary
quantization.

Profile M defines moderate ceilings for geospatial, motion, timing, confidence,
and RF fields. It keeps observations, fusion, state, system, and command exports
aligned with profile legality.

Profile L defines coarser ceilings, preserves required state/system/command
semantics, protects minimum operator utility, and treats command target
geometry more strictly than ordinary state display precision. If a source has
less precision than the reference utility floor, the fixture or policy context
must explicitly acknowledge source-limited precision; the validator does not
invent detail.

## Conservative Rounding Review

The validator and fixtures enforce:

- confidence can preserve or decrease only;
- confidence must obey profile decimal ceilings;
- `payload.valid_for_ms` can preserve or shorten only;
- TTL must align to configured profile steps where configured;
- error and timing uncertainty fields can preserve or increase only;
- error and timing uncertainty must align to configured upward steps;
- lat/lon cannot gain decimal precision;
- geospatial fields cannot be over-thinned below utility floors;
- command target geometry cannot be over-thinned below the command floor;
- RF values preserve units and must stay within configured quantization
  tolerance;
- hidden defaults and implicit zero-filled geo are rejected.

## Fixture Review

Fixture count: 32 total, with 11 must-pass and 21 must-fail cases.

Must-pass coverage includes:

- H to M state lat/lon precision reduction;
- M to L state lat/lon precision reduction;
- H to L coarser state precision;
- confidence rounded down;
- `valid_for_ms` shortened or rounded down;
- timing error rounded up;
- allowed `source_summary` omission;
- Profile M RF frequency, bandwidth, and power quantization;
- command target geometry retained at the stricter floor;
- compact Profile L roundtrip after policy-compliant quantization;
- source-limited precision explicitly acknowledged.

Must-fail coverage includes:

- confidence increase and invalid confidence rounding;
- TTL increase and invalid TTL rounding;
- timing error decrease;
- lat/lon precision increase;
- unit rescale;
- immutable event time, event ID, source producer, and track ID changes;
- lineage and required field removal;
- state geo over-thinning;
- command target over-thinning;
- RF quantization outside tolerance;
- implicit zero-filled geo;
- hidden default insertion;
- projection-invalid semantic change;
- packet-budget required-field stripping;
- undeclared source-limited precision.

## Validator Behavior Review

`tools/validate_precision_policy.py` loads the policy and fixture files, fails
on missing files, validates policy shape, validates source/projected events
through canonical schema and policy via projection validation, reuses projection
preservation checks, and adds precision-specific checks for:

- immutable paths;
- required field removal;
- hidden defaults;
- confidence non-increase and rounding ceilings;
- TTL non-increase and rounding steps;
- error-bound/timing uncertainty non-decrease and rounding steps;
- lat/lon precision ceilings and utility floors;
- source-limited precision acknowledgement;
- RF quantization tolerance;
- step alignment for configured numeric fields;
- packet-budget required-field stripping;
- compact/protobuf roundtrip requests where fixtures specify them.

The validator supports `--quiet`, returns nonzero on unexpected pass/fail, and
uses deterministic failure codes.

## Failure Code Review

All required stable failure codes are present:

- `PRECISION_POLICY_SCHEMA_INVALID_SOURCE`
- `PRECISION_POLICY_SCHEMA_INVALID_PROJECTED`
- `PRECISION_POLICY_POLICY_INVALID_SOURCE`
- `PRECISION_POLICY_POLICY_INVALID_PROJECTED`
- `PRECISION_POLICY_PROJECTION_INVALID`
- `PRECISION_POLICY_IMMUTABLE_CHANGED`
- `PRECISION_POLICY_UNIT_CHANGED`
- `PRECISION_POLICY_PRECISION_INCREASE`
- `PRECISION_POLICY_CONFIDENCE_INCREASE`
- `PRECISION_POLICY_CONFIDENCE_ROUNDING_INVALID`
- `PRECISION_POLICY_TTL_INCREASE`
- `PRECISION_POLICY_TTL_ROUNDING_INVALID`
- `PRECISION_POLICY_ERROR_BOUND_DECREASE`
- `PRECISION_POLICY_ERROR_BOUND_ROUNDING_INVALID`
- `PRECISION_POLICY_UTILITY_FLOOR_VIOLATION`
- `PRECISION_POLICY_COMMAND_GEOMETRY_TOO_COARSE`
- `PRECISION_POLICY_RF_QUANTIZATION_INVALID`
- `PRECISION_POLICY_REQUIRED_FIELD_REMOVED`
- `PRECISION_POLICY_OPTIONAL_OMISSION_NOT_ALLOWED`
- `PRECISION_POLICY_HIDDEN_DEFAULT`
- `PRECISION_POLICY_PACKET_BUDGET_STRIPPED_REQUIRED`
- `PRECISION_POLICY_SOURCE_LIMITED_PRECISION_UNDECLARED`

Fixture expectations use specific codes rather than catch-all behavior.

## Packet-Budget Interaction Review

Docs and policy state that exporters should omit cataloged optional fields
before reducing required precision, then validate projection and precision
policy before measuring packet size. The packet-budget fixture rejects stripping
required lineage. The compact Profile L fixture proves a policy-compliant
projection remains valid after compact roundtrip. If packet budget and utility
floor conflict, the required behavior is reject, omit, or make a reviewed
policy decision rather than silently corrupting semantics.

## Projection Interaction Review

Precision policy does not replace projection preservation. The precision
validator invokes the projection validator and maps projection failures into
precision-policy failure codes where appropriate. A Profile L event that changes
non-precision semantic content fails. Same-event projection identity remains
governed by projection preservation; semantic payload changes still require a
new event with appropriate lineage.

## Gateway And Exporter Posture Review

S1-06B did not change gateway runtime export behavior. The docs instruct
gateways and exporters to apply precision policy only at explicit export or
profile projection time. Stored source events remain immutable. Deterministic
rounding is recommended for future exporters, and failure or omission is
required when utility floor and packet budget cannot both be satisfied.

## Conformance Integration Review

`tools/validate_conformance.py --precision-policy` is opt-in. Default
`python tools/validate_conformance.py --strict` behavior is unchanged.

The precision-policy flag can run with:

- `--profile-projection`
- `--extension-registry`
- `--conformance-classes`
- `--encoding-negative`

The precision validator fails on missing policy or fixture files and does not
require encoding-negative or conformance-class validation unless those flags are
explicitly passed.

## Conformance-Class Impact Review

The conformance class manifest remains valid. Evidence for
`ZMETA-PROFILE-L`, `ZMETA-PROFILE-M`, `ZMETA-PROFILE-H`, and
`ZMETA-PROJECTION-PRESERVATION` was strengthened with precision-policy surfaces,
fixtures, and commands. No new conformance class was added. The reference
gateway claim records precision-policy evidence for claimed profile/projection
classes. The core producer claim remains narrower and does not claim
gateway/export precision behavior. D-008 remains closed.

## Documentation Review

The updated docs explain:

- where the precision policy spec, policy artifact, and fixtures live;
- how to run the standalone validator;
- how to run optional conformance integration;
- that precision policy is profile/export policy, not schema;
- that reference defaults require mission review;
- that source events remain immutable;
- that projection preservation still governs same-event identity;
- that compact/protobuf remain encoding projections;
- that packet-budget pressure cannot strip required semantic fields;
- that no schema changes or new vocabulary were introduced;
- that D-010 remained implemented pending S1-06C audit before this audit.

## Verification

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

## D-010 Closure Recommendation

D-010 should be closed. The implementation provides the required reference
policy artifact, validator, fixtures, tests, documentation, optional conformance
runner integration, and conformance-class evidence. The remaining decisions are
mission-default tuning and future field-family expansion, not blockers to the
current profile precision policy floors gap.

## Open Issue Status

- D-010: close as COMPLETE after this audit.
- D-011: OPEN.
- D-002: OPEN.
- D-001: OPEN.
- D-003: OPEN.
- D-004: OPEN.

## Unresolved Governance Decisions

- Exact operational precision defaults still require mission review.
- Deployments may need mission-specific overrides for geography, RF, timing,
  and command geometry.
- Future work can decide whether `--precision-policy` should remain opt-in or
  join release strict conformance.
- v1.1.0 structured quality and future profile/release semantics require
  versioned branch treatment before becoming normative.

## Recommended Next Work Item

S1-07A - Crosswalk TAKEOFF Mention Cleanup.
