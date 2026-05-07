# S1-04A Conformance Class Manifest Plan

Status: COMPLETE
Date: 2026-05-07
Scope: Planning only. No schemas, validators, adapters, encodings, tests,
policy files, examples, extension registry entries, semantic contract text,
release hashes, or event vocabulary were changed.

## A. Current Conformance Landscape

The repository already proves several important ZMeta behaviors, but the proof
surfaces are spread across schemas, policy, tools, examples, and tests.

Current proof surfaces:

- Schema validation: `schema/zmeta-event.schema.json` dispatches by exact
  `zmeta_version`; `schema/zmeta-event-1.0.schema.json` defines locked v1.0
  vocabulary; `schema/zmeta-event-1.1.0.schema.json` defines experimental
  v1.1.0 compatibility vocabulary.
- Policy validation: `policy/*.yaml` plus `gateway/src/validators.py` enforce
  roles, profile legality, timing quality, lineage, producer authority, routing,
  command governance, dedupe, and violation code severity.
- Strict version dispatch: canonical validation uses the dispatcher schema, and
  version discrimination tests prove v1.1.0-only vocabulary does not validate
  under v1.0.
- Profile/event-type legality: schema `profileExportConsistency`, policy
  `profiles.yaml`, and `validate_profile` enforce allowed event types for
  Profile L/M/H.
- Profile projection preservation: `conformance/profile_projection_field_catalog.yaml`,
  `conformance/profile-projection/*.jsonl`, `tools/validate_projection.py`, and
  focused gateway tests prove same-event H/M/L thinning preserves identity,
  source, lineage, units, semantic layer, confidence monotonicity, TTL
  monotonicity, and encoding-decoded equivalence.
- Extension registry validation: `spec/extension-registry.yaml`,
  `tools/validate_extension_registry.py`, and `gateway/tests/test_extension_registry.py`
  prove registry record shape, status/category rules, version boundary checks,
  reserved/proposed invalidity, and unregistered `TAKEOFF` leakage protection.
- Compact CBOR: `zmeta_compact.py`, `zmeta_cbor.py`,
  `spec/compact-binary-mapping.md`, and `gateway/tests/test_encoding_roundtrip.py`
  prove deterministic roundtrip and bounded decoder behavior. Projection tests
  additionally compare decoded compact Profile L JSON against projection rules.
- Protobuf: `zmeta_proto.py`, `spec/protobuf-encoding.md`,
  `schema/proto/zmeta_event_v1.proto`, conversion tooling, and encoding tests
  prove roundtrip and decoder bounds. Projection tests verify decoded protobuf
  JSON is validated as canonical semantic input.
- CoT/TAK adapter tests: CoT egress tests prove STATE_EVENT-only projection and
  mapping of track, geo, TTL, confidence, and display metadata; CoT ingress tests
  prove state emission with required confidence/lineage and UTC normalization.
- Gateway runtime validation: `gateway/src/gateway.py` decodes input encoding,
  validates schema and policy, enforces profile/export behavior, handles dedupe,
  emits diagnostic SYSTEM_EVENT/TASK_ACK outputs, and checks schema/policy/
  contract hashes when configured.
- Conformance fixtures: `conformance/must-pass.jsonl` and
  `conformance/must-fail.jsonl` form the core schema/policy corpus;
  projection fixtures provide pairwise source/projected cases.

What remains ambiguous without class claims:

- Whether "ZMeta compliant" means schema-only, schema plus policy, gateway
  runtime behavior, profile projection preservation, adapter projection, or
  encoding support.
- Whether a producer supports all event families or only a subset.
- Whether a gateway supports Profile L/M/H legality only, or also projection
  preservation.
- Whether compact/protobuf support includes decoded canonical JSON validation.
- Whether adapter conformance covers semantic layer separation, timestamp/unit
  normalization, and rejection of ambiguous inputs.
- Whether future vocabulary claims are blocked until extension registry and
  version-branch adoption allow them.

## B. Problem Statement

Generic "ZMeta compliant" claims are insufficient because ZMeta is a semantic
standard, not only a JSON Schema. A producer, gateway, adapter, or transport
component can pass one surface while failing another.

Risks without conformance classes:

- Schema-only compliance can be mistaken for full semantic compliance.
- Profile support can be claimed without projection preservation.
- Encoding support can be claimed without decoded validation.
- Adapter support can be claimed without semantic layer-separation tests.
- Future concepts can be claimed before versioned adoption.
- Vendor/private implementations can claim compliance without recording
  evidence, commit hashes, policy versions, or test results.
- Integrators cannot compare implementations cleanly across profiles, adapters,
  encodings, and gateway behavior.

The conformance class manifest should become the bridge between the semantic
contract and repeatable operational certification.

## C. Proposed Artifacts

Recommended S1-04B artifacts:

- Human-readable class spec: `spec/conformance-classes.md`
- Machine-readable class manifest: `conformance/conformance_classes.yaml`
- Example implementation claims:
  - `conformance/claims/example-reference-gateway.yaml`
  - `conformance/claims/example-core-producer.yaml`
- Validator: `tools/validate_conformance_classes.py`
- Tests: `gateway/tests/test_conformance_classes.py`

These paths follow current repo conventions:

- `spec/` owns human-readable normative guidance.
- `conformance/` owns runnable conformance fixtures and machine-readable
  conformance artifacts.
- `tools/` owns standalone validators.
- `gateway/tests/` already contains validator and conformance CLI regression
  tests.

## D. Conformance Class Model

Each class record should include:

- `class_id`: stable identifier such as `ZMETA-CORE`.
- `display_name`: human-readable name.
- `status`: one of the class status values.
- `version_scope`: exact ZMeta versions or branches covered.
- `description`: concise class purpose.
- `semantic_contract_sections`: section IDs or headings from
  `spec/semantics-contract.md`.
- `required_schema_surfaces`: schema files or schema branches required.
- `required_policy_surfaces`: policy YAML files or policy checks required.
- `required_gateway_surfaces`: gateway/runtime behavior required.
- `required_adapter_surfaces`: adapter paths or adapter behavior required.
- `required_encoding_surfaces`: encoding modules/specs required.
- `required_conformance_fixtures`: fixture files and named fixture groups.
- `required_test_commands`: commands that must pass for the class.
- `dependencies`: other class IDs required before this class is claimable.
- `exclusions`: explicit unsupported or out-of-scope behavior.
- `allowed_claimants`: implementation types allowed to claim the class, such as
  `producer`, `gateway`, `adapter`, `encoding`, `reference_stack`, or `tooling`.
- `claim_evidence_required`: required evidence fields for claims.
- `current_repo_support`: `implemented`, `partial`, `not_applicable`, or
  `future`.
- `future_or_reserved_notes`: branching or registry constraints.
- `references`: relevant docs, schemas, policies, tools, fixtures, tests, and
  issues.

The manifest should also include top-level metadata:

- `manifest_version`
- `authority`
- `generated_for_zmeta_versions`
- `status_values`
- `claim_status_values`
- `class_records`
- `claim_schema`

## E. Class Status Definitions

Proposed class statuses:

- `active`: class is defined, claimable, and supported by required validation
  surfaces.
- `implemented`: reference repo has implementation/test support, but maintainers
  have not yet decided whether to label the class externally claimable as
  `active`.
- `partially_implemented`: some required surfaces exist, but evidence is not yet
  complete.
- `planned`: implementation path is defined but not implemented.
- `reserved`: class name is held for future semantics and cannot be claimed.
- `future`: class depends on future vocabulary, version branches, or companion
  artifacts and cannot be claimed by current implementations.
- `deprecated`: class was previously claimable but is discouraged or superseded.

Required rule: a `future` or `reserved` class cannot be claimed by current
implementations.

Recommended S1-04B default: use `implemented` for current classes where the
reference repo already has tests and tools, and leave the `active` promotion
decision for maintainers. This avoids over-certifying the first manifest while
still making current support visible.

## F. Claim Model

An implementation claim file should record:

- `implementation_name`
- `implementation_type`
- `implementation_version`
- `zmeta_versions_supported`
- `classes_claimed`
- `class_claims`
- `test_commands_run`
- `test_results`
- `schema_versions`
- `policy_pack_versions`
- `extension_registry_version`
- `projection_catalog_version`
- `contract_hash`
- `commit_hash`
- `date`
- `claim_owner`
- `limitations`
- `exceptions`

Each `class_claims` entry should include:

- `class_id`
- `claim_status`: `claimed`, `not_claimed`, `partial`, or `not_applicable`
- `evidence`
- `commands`
- `result_summary`
- `limitations`
- `exceptions`

Rule: a class claim is not valid unless all required test commands for that
class pass and the claim records the results, commit hash, relevant schema/policy
versions, registry version, and catalog version where applicable.

Claims should be reproducible from source. A claim should not rely on prose such
as "supports ZMeta" without command output or structured evidence.

## G. Initial Conformance Classes

Current or baseline classes proposed for the initial manifest:

- `ZMETA-CORE`: v1.0 envelope, event families, subtype/payload discriminator
  consistency, UUIDv7, UTC-Z timestamps, units, confidence placement, lineage,
  and layer separation.
- `ZMETA-VERSION-DISPATCH`: exact version branch dispatch and v1.0/v1.1.0
  isolation.
- `ZMETA-V1-0-SCHEMA`: locked v1.0 schema vocabulary and payload constraints.
- `ZMETA-V1-1-EXPERIMENTAL`: experimental v1.1.0 compatibility branch only,
  not adopted vocabulary.
- `ZMETA-POLICY-BASELINE`: roles, profiles, semantics, lineage, timing,
  producer authority, routing, and violation-code policy.
- `ZMETA-PROFILE-L`: Profile L event-type legality, timing exposure, lineage
  tolerance, and state/system/command export constraints.
- `ZMETA-PROFILE-M`: Profile M event-type legality and selected observation/
  fusion/state/system/command support.
- `ZMETA-PROFILE-H`: full-fidelity profile allowing all valid event families.
- `ZMETA-PROJECTION-PRESERVATION`: source/projected H/M/L projection
  preservation with monotonic confidence/TTL/precision and allowed omission
  rules.
- `ZMETA-EXTENSION-REGISTRY`: registry shape, status/category semantics,
  reserved/proposed invalidity, and version-boundary protection.
- `ZMETA-COMPACT-CBOR`: compact Profile L wire projection that decodes to
  canonical JSON before validation.
- `ZMETA-PROTOBUF-PROJECTION`: experimental protobuf wire projection that
  decodes to canonical JSON before validation.
- `ZMETA-GATEWAY-REFERENCE`: reference gateway schema/policy/profile/dedupe/
  timing/hash behavior.
- `ZMETA-COT-PROJECTION`: CoT/TAK state projection and CoT ingress state
  conversion boundaries.
- `ZMETA-COMMAND-GOVERNANCE`: bounded tasking, deconfliction, altitude
  prohibition, task IDs, TTL, TASK_ACK lifecycle, and command routing.
- `ZMETA-TIMING-QUALITY`: UTC-Z event time, per-event timing quality or
  TIME_STATUS fallback, freshness, and holdover monotonicity.
- `ZMETA-LINEAGE-POLICY`: mandatory lineage, payload provenance subset,
  parent-type checks, unresolved parent policy, and Profile L tolerance.

Future or reserved classes:

- `ZMETA-ADAPTER`
- `ZMETA-SENSOR-ADAPTER`
- `ZMETA-AI-PROVENANCE`
- `ZMETA-COALITION-EXPORT`
- `ZMETA-MESH-TRUST`
- `ZMETA-REPLAY`
- `ZMETA-UAS-IDENTITY`
- `ZMETA-PNT-INTEGRITY`
- `ZMETA-DATA-NUTRITION`
- `ZMETA-COMPUTE-ELASTICITY`
- `ZMETA-EMERGENCY-L0`
- `ZMETA-CROSS-DOMAIN-EXPORT`
- `ZMETA-VENDOR-EXTENSION`

Recommended merge/rename notes:

- Keep `ZMETA-COT-PROJECTION` adapter-specific because CoT/TAK has a specific
  STATE_EVENT-only semantic boundary.
- Keep `ZMETA-ADAPTER` generic and future/reserved until a shared adapter
  harness exists; use adapter-specific classes for CoT, JREAP, MAVLink, KLV, or
  sensor families as concrete tests mature.
- Treat `ZMETA-V1-1-EXPERIMENTAL` as implemented but experimental, not as a
  promotion of v1.1.0 concepts to adopted status.

## H. Class Dependency Model

Dependency examples:

- `ZMETA-V1-0-SCHEMA` depends on `ZMETA-CORE`.
- `ZMETA-VERSION-DISPATCH` depends on `ZMETA-CORE`.
- `ZMETA-POLICY-BASELINE` depends on `ZMETA-CORE` and `ZMETA-V1-0-SCHEMA`.
- `ZMETA-PROFILE-L`, `ZMETA-PROFILE-M`, and `ZMETA-PROFILE-H` depend on
  `ZMETA-CORE`, `ZMETA-V1-0-SCHEMA`, and profile legality checks.
- `ZMETA-PROJECTION-PRESERVATION` depends on `ZMETA-PROFILE-L`,
  `ZMETA-PROFILE-M`, `ZMETA-PROFILE-H`, and projection fixture validation.
- `ZMETA-COMPACT-CBOR` depends on `ZMETA-PROFILE-L`, decoded canonical JSON
  validation, and compact roundtrip tests.
- `ZMETA-PROTOBUF-PROJECTION` depends on `ZMETA-CORE`, decoded canonical JSON
  validation, and protobuf roundtrip/decoder-bound tests.
- `ZMETA-COT-PROJECTION` depends on STATE_EVENT behavior, lineage, confidence,
  timing quality, and CoT adapter tests.
- `ZMETA-COMMAND-GOVERNANCE` depends on `ZMETA-CORE`, `ZMETA-V1-0-SCHEMA`, and
  `ZMETA-POLICY-BASELINE`.
- `ZMETA-TIMING-QUALITY` depends on `ZMETA-CORE` and timing policy tests.
- `ZMETA-LINEAGE-POLICY` depends on `ZMETA-CORE` and lineage policy tests.
- `ZMETA-EXTENSION-REGISTRY` depends on registry YAML, registry validator, and
  schema leakage tests.
- Future classes cannot be claimable until their extension registry entries are
  no longer `reserved` or `proposed`, a version branch supports them, and their
  required schema/policy/conformance evidence exists.

The validator should reject dependency cycles and unknown dependency IDs.

## I. Required Test Mapping

Recommended required commands by class:

| Class | Required commands and evidence |
| --- | --- |
| `ZMETA-CORE` | `python tools/validate_conformance.py --strict`; `conformance/must-pass.jsonl`; `conformance/must-fail.jsonl`; schema dispatcher and v1.0 schema. |
| `ZMETA-VERSION-DISPATCH` | `python -m pytest -q gateway/tests/test_schema_version_discrimination.py gateway/tests/test_compat_normalizer.py gateway/tests/test_check_compat_cli.py`; dispatcher schema; v1.1 examples/conformance fixtures. |
| `ZMETA-V1-0-SCHEMA` | `python tools/validate_conformance.py --strict`; `schema/zmeta-event-1.0.schema.json`; v1.0 examples and conformance corpus. |
| `ZMETA-V1-1-EXPERIMENTAL` | `python -m pytest -q gateway/tests/test_schema_version_discrimination.py`; `python tools/validate_conformance.py --strict`; `schema/zmeta-event-1.1.0.schema.json`; `examples/zmeta-v1.1-examples.jsonl`. |
| `ZMETA-POLICY-BASELINE` | `python tools/validate_conformance.py --strict`; policy files; `gateway/tests/test_producer_authority.py`, `test_lineage_semantics.py`, `test_timing_freshness.py`, and `test_gateway_smoke.py`. |
| `ZMETA-PROFILE-L` | `python tools/validate_conformance.py --strict`; Profile L examples; profile policy; compact Profile L examples when compact is claimed. |
| `ZMETA-PROFILE-M` | `python tools/validate_conformance.py --strict`; Profile M examples; profile policy. |
| `ZMETA-PROFILE-H` | `python tools/validate_conformance.py --strict`; Profile H examples; profile policy. |
| `ZMETA-PROJECTION-PRESERVATION` | `python tools/validate_projection.py --catalog conformance/profile_projection_field_catalog.yaml --must-pass conformance/profile-projection/must-pass.jsonl --must-fail conformance/profile-projection/must-fail.jsonl --quiet`; `python -m pytest -q gateway/tests/test_profile_projection_preservation.py gateway/tests/test_profile_projection_encoding.py`. |
| `ZMETA-EXTENSION-REGISTRY` | `python tools/validate_extension_registry.py --registry spec/extension-registry.yaml`; `python -m pytest -q gateway/tests/test_extension_registry.py`. |
| `ZMETA-COMPACT-CBOR` | `python -m pytest -q gateway/tests/test_encoding_roundtrip.py gateway/tests/test_profile_projection_encoding.py`; `spec/compact-binary-mapping.md`; `zmeta_compact.py`; `zmeta_cbor.py`. |
| `ZMETA-PROTOBUF-PROJECTION` | `python -m pytest -q gateway/tests/test_encoding_roundtrip.py gateway/tests/test_profile_projection_encoding.py`; `spec/protobuf-encoding.md`; `zmeta_proto.py`; `schema/proto/zmeta_event_v1.proto`. |
| `ZMETA-GATEWAY-REFERENCE` | `python -m pytest -q gateway/tests/test_gateway_smoke.py gateway/tests/test_timing_freshness.py gateway/tests/test_producer_authority.py gateway/tests/test_lineage_semantics.py`; `gateway/src/gateway.py`; `gateway/src/validators.py`. |
| `ZMETA-COT-PROJECTION` | `python -m pytest -q adapters/egress/cot adapters/ingress/cot`; CoT adapter READMEs and tests. |
| `ZMETA-COMMAND-GOVERNANCE` | `python tools/validate_conformance.py --strict`; `python -m pytest -q adapters/egress/mavlink gateway/tests/test_gateway_smoke.py`; command fixtures and policy files. |
| `ZMETA-TIMING-QUALITY` | `python -m pytest -q gateway/tests/test_timing_freshness.py adapters/ingress/test_timestamp_normalization.py`; timing policy and adapters that normalize timestamps. |
| `ZMETA-LINEAGE-POLICY` | `python -m pytest -q gateway/tests/test_lineage_semantics.py`; lineage policy and projection fixtures. |

Combined reference-stack command:

```powershell
python tools\validate_conformance.py --strict --profile-projection --extension-registry
python -m pytest
```

S1-04B should decide whether each class stores one combined command, a list of
atomic commands, or both.

## J. Machine-Readable Manifest Validation Plan

`tools/validate_conformance_classes.py` should check:

- YAML loads.
- Required top-level keys exist.
- Required class fields exist.
- `class_id` values are unique.
- Status values are valid.
- Dependencies refer to known classes.
- Dependency graph has no cycles.
- `future` and `reserved` classes cannot be claimed.
- `active` and `implemented` classes have required test mappings.
- Classes referencing future extension registry entries cannot be active unless
  registry status and version branch allow them.
- Required schema, policy, tool, fixture, adapter, and test paths exist.
- Required test commands are present and non-empty.
- Claim files load and reference known classes.
- Claim files cannot claim `future`, `reserved`, or unknown classes.
- Claim files cannot claim classes whose required test commands are missing.
- Claim files record test results, command status, commit hash, and relevant
  schema/policy/registry/catalog versions.
- The manifest does not make future concepts valid event vocabulary.

The validator should support:

```powershell
python tools\validate_conformance_classes.py --manifest conformance\conformance_classes.yaml
python tools\validate_conformance_classes.py --manifest conformance\conformance_classes.yaml --claims conformance\claims
```

The validator should be deterministic and should print stable failure codes so
future tests can assert exact failures.

## K. Optional Conformance Runner Integration Plan

S1-04B may integrate class validation into `tools/validate_conformance.py` with
an explicit flag:

```powershell
python tools\validate_conformance.py --strict --conformance-classes
python tools\validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes
```

Preferred behavior:

- Default `--strict` remains unchanged.
- `--conformance-classes` validates only the manifest unless claim paths are
  supplied by an additional flag.
- It can run with `--profile-projection` and `--extension-registry`.
- Missing manifest or missing required paths are failures, not silent skips.

Do not implement this in S1-04A.

## L. Relationship To Extension Registry

The extension registry and conformance class manifest govern different things:

- Extension registry governs vocabulary lifecycle.
- Conformance class manifest governs implementation claims and evidence.
- A future semantic feature may be listed in the registry as `reserved`,
  `proposed`, or `experimental` before it has a claimable class.
- A conformance class cannot make registry-reserved vocabulary valid.
- A future class may depend on an adopted or experimental registry entry, but it
  must still require schema/policy/adapter/gateway/encoding/docs/conformance
  evidence before it is claimable.

S1-04B should make this relationship machine-checkable by allowing class records
to reference extension registry entries and requiring the class validator to load
`spec/extension-registry.yaml`.

## M. Relationship To Contract Hash / Release Hash

D-002 remains open. S1-04A does not recompute hashes.

Future release artifacts should record:

- semantic contract hash;
- canonical dispatcher schema hash;
- v1.0 and v1.1.0 schema hashes;
- policy pack hash;
- extension registry hash;
- conformance class manifest hash;
- projection field catalog hash;
- conformance fixture corpus hash.

Claim files should record the contract hash when available, but S1-04B should
allow `contract_hash: null` or `pending_d002` until D-002 is resolved. The claim
validator should warn or mark the claim incomplete if hashes are absent in a
release/certification mode.

## N. Implementation Plan For S1-04B

Recommended S1-04B file-by-file plan:

- `spec/conformance-classes.md`: human-readable class model, status
  definitions, claim rules, dependency model, registry relationship, hash
  relationship, and class summaries.
- `conformance/conformance_classes.yaml`: machine-readable class manifest with
  metadata, class records, dependencies, required paths, and required commands.
- `conformance/claims/example-reference-gateway.yaml`: example claim for the
  current reference stack, using current commands and known limitations.
- `conformance/claims/example-core-producer.yaml`: minimal producer claim
  example for schema/policy/core surfaces.
- `tools/validate_conformance_classes.py`: standalone manifest/claim validator.
- `gateway/tests/test_conformance_classes.py`: tests for YAML load, required
  fields, duplicate IDs, bad dependencies, future/reserved claim rejection,
  missing command rejection, bad claim references, and current manifest success.
- `tools/validate_conformance.py`: optional `--conformance-classes` flag.
- `spec/README.md`: list conformance class spec and validation command.
- `conformance/README.md`: document manifest and claim examples.
- `docs/zmeta_refinement_worklog.md`: mark S1-04B implementation status and
  update D-008 after implementation.
- `docs/zmeta_refinement_handoff.md`: update next task and human decisions.

Implementation guardrails:

- Do not change schemas.
- Do not add event vocabulary.
- Do not promote future registry entries.
- Keep default strict conformance behavior stable.
- Keep claim examples as examples, not certification records.

## O. Risks And Open Questions

Open decisions before S1-04B:

- Should class IDs use hyphens exactly as `ZMETA-CORE`, or should YAML also
  allow underscore aliases? Recommended default: use hyphenated canonical IDs
  only; optional aliases can wait.
- Should current classes be `implemented` or `active`? Recommended default:
  `implemented` for current repo support, with `active` reserved for a later
  maintained certification decision.
- Should `ZMETA-V1-1-EXPERIMENTAL` be claimable? Recommended default: claimable
  only as experimental and only when exact v1.1.0 tests pass.
- Should claim manifests require captured test output files? Recommended
  default: require command result summaries now; add optional artifact paths.
- Should claim manifests include contract hash now or wait for D-002?
  Recommended default: include nullable hash fields and mark release-grade
  claims incomplete until D-002 is resolved.
- Should adapter-specific classes be generic or adapter-specific? Recommended
  default: keep generic `ZMETA-ADAPTER` reserved and define concrete
  adapter-specific classes where tests exist.
- Do vendor/private claims need separate policy? Recommended default: yes,
  require namespace/owner and extension registry references before any
  `ZMETA-VENDOR-EXTENSION` claim is allowed.
- Should conformance class validation ever join default strict? Recommended
  default: keep opt-in until the manifest and claim format stabilize.

## Recommended Next Work Item

Proceed to S1-04B - Conformance Class Manifest Implementation.
