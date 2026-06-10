# Changelog

## [Unreleased]
- Added `docs/zmeta_professional_overview.md`, an advisory overview for
  engineers, operators, and leadership covering ZMeta purpose, architecture,
  schemas, adapters, gateway deployment, profiles, encodings, data governance,
  AI provenance, and RF-to-tasking workflows.

## [1.1.7] - 2026-06-10
- Added formal human/AI agent change governance through `AGENTS.md` and
  `docs/zmeta_change_governance.md`, including change classes, documentation
  requirements, validation gates, release limits, and publication workflow.
- Added downstream clone guidance distinguishing local integration freedom from
  compatibility-breaking private ZMeta dialect or fork changes.
- Added governed `process_governance_hash` release-manifest coverage for
  process guidance.
- Added a release audit record for stale/current-release references, ignored
  local build residue, generated artifact handling, and tracked-source secret
  scans.
- Added machine-checkable profile-projection preservation rules and fixtures for
  `payload.extensions.risk_adjudication` and
  `payload.extensions.external_promotion`, preventing lower-profile exports
  from stripping accepted-risk labels or compact external-promotion evidence.
- Strengthened the extension registry contract with validated projection
  behavior, risk relevance, policy-preservation, security/privacy, and fixture
  reference fields.
- Added post-v1.1.6 integration guidance for external state promotion metadata,
  `trust_ref` limits, and consumer responsibility for accepted-risk labels.
- Added `tools/lint_policy_risk_modes.py` to flag unsafe `ignore` settings on
  material timing, lineage, external-promotion, command, trust, or safety risk.

## [1.1.6] - 2026-06-09
- Added the semantic risk-adjudication baseline: locked, tunable, advisory, and
  future-extension rule classes with bounded reject, warn, degrade, quarantine,
  and ignore behavior.
- Added explicit operator-side accepted-risk filtering with display, fusion,
  state, command, autonomy, AAR, and audit presets.
- Added semantic bad-event fixtures and a shared adapter conformance harness.
- Added kernel-protection doctrine and full kernel-protection validation across
  projection, registry, conformance classes, encoding negatives, precision
  policy, release manifest/package, bad-event corpus, and adapter harness.
- Hardened direct CoT egress so malformed state payloads carrying raw
  observation/evidence fields fail closed.
- Completed an end-to-end stack and runtime audit covering examples,
  compatibility, gateway self-tests, live UDP workflows, Profile L packet size,
  release/package smoke tests, and containerized SDR-derived RF workflow checks.
- Preserved v1.0/v1.1.0 version isolation; no future vocabulary became valid
  and literal raw IQ support remains future work pending real sensor samples.

## [1.1.5] - 2026-05-07
- Hardened the ZMeta semantic-governance baseline through S0/S1 audits covering
  contract lockdown, contract-to-stack alignment, release hashing, and formal
  release packaging.
- Added structured release manifest hashing with category hashes, release bundle
  hash, release manifest hash, builder, validator, tests, and conformance
  integration.
- Added formal release package documentation, templates, package builder,
  package validator, no-secret checks, release-package tests, and optional
  conformance integration.
- Added or audited profile projection preservation, extension registry
  validation, conformance class manifests and claims, encoding-negative
  validation, and profile precision policy validation.
- Preserved strict `zmeta_version` dispatch and v1.0/v1.1.0 vocabulary
  isolation; no new event vocabulary became valid.
- Removed out-of-scope organizational artifact language from active ZMeta scope;
  D-004 is closed as removed from the ZMeta baseline.
- Added the D-003 future versioned semantic branch roadmap while keeping future
  concepts invalid until adopted through versioned implementation and audit.

## [1.1.4]
- Fixed edge/gateway release bundles so downloaded packages include
  `conformance/` and `release/sign_release_artifacts.py`, allowing bundle-local
  gateway self-tests and release-signing tests to run.
- Added regression coverage for release bundle self-test dependencies.

## [1.1.3]
- Fixed GitHub Actions gateway self-test failure by preferring the built-in
  deterministic CBOR encoder/decoder when available, keeping `cbor2` as a
  fallback.
- Added regression coverage for gateway and compact CBOR behavior when `cbor2`
  is present.
- Opted CI into Node.js 24 JavaScript actions to address the hosted runner
  Node.js 20 deprecation warning.

## [1.1.2]
- Added `tools/check_compat.py` for migration-oriented JSON/JSONL diagnostics.
- Added malformed protobuf decoder regression tests for varints, length fields,
  truncated fixed fields, invalid UTF-8, and random byte samples.
- Added gateway timing-quality metrics that distinguish source-provided timing
  from degraded `UNKNOWN`/`UNSYNCED` fallback timing.
- Clarified deployment policy variant hash behavior, adapter invocation style,
  degraded fallback timing interpretation, and release verification instructions.
- Hardened release signing helper GPG discovery for Gpg4win installs and
  signature refreshes.

## [1.1.1]
- Normalized ingress adapter timestamps to the strict UTC trailing-Z schema form.
- Added explicit fallback timing quality to ingress adapter operational events.
- Hardened protobuf decoding with message, field, payload, JSON-depth, and nested-message bounds.
- Added optional strict producer-authority and Profile L timing-degrade policy variants.
- Added CoT skip metrics so unpublishable state events are visible at the gateway boundary.
- Added release checksum/signature helper tooling and refreshed release checklist guidance.
- Tightened pytest collection to ignore generated release/cache directories.

## [1.1.0]
- Added experimental protobuf transport projection with schema, pure-Python codec,
  gateway/tool support, docs, and round-trip tests.
- Added a single-event encoding conversion CLI for JSON, CBOR, compact CBOR, and
  protobuf.
- Hardened CBOR output to use deterministic/canonical map ordering.
- Updated encoding compatibility guidance for JSON, CBOR, compact CBOR, and protobuf.
- Added a canonical version-discriminated JSON schema and tightened v1.1.0
  validation so v1.1-only vocabulary cannot validate under `zmeta_version: "1.0"`.
- Added v1.1.0 semantic extension governance, reserved uncontracted observation
  modalities, and enforced minimum validation for expanded task types.
- Defined `event_subtype` as a normative semantic discriminator and enforced
  subtype/payload discriminator consistency across v1.0 and v1.1.0 schemas.
- Enforced claimed Profile L/M/H export event-type rules in the schemas while
  keeping `profile` optional.
- Prohibited inference payloads and claims from carrying track/fusion authority
  fields (`track_id`, `members`, `estimated_state`).
- Prohibited STATE_EVENT payloads from carrying raw observation features,
  measurements, modalities, timestamps, or raw data references.
- Hardened COMMAND_EVENT payloads against altitude/vertical-control fields and
  moved arbitrary command metadata behind `payload.extensions`.
- Added task-specific COMMAND_EVENT validation for GOTO, ORBIT, HOLD,
  SEARCH_BOX, RETURN_TO_BASE, LAND, LOITER, SCAN_RF, TRACK_TARGET, and
  CHANGE_SENSOR_MODE.
- Added strict UTC-Z timestamp validation across envelope, payload, data
  reference, command, fusion, and timing-status timestamp fields.
- Enforced paired observation windows and RF window midpoint semantic
  validation.
- Tightened geodesy, speed, quality-unit, EO/ACOUSTIC observation, data reference,
  SENSOR_STATUS, and PLATFORM_STATUS semantics.
- Added producer-authority, timing-freshness, and lineage policy packs with
  runtime validators and focused tests.
- Expanded violation reason codes while keeping TASK_ACK reason codes
  task-specific.
- Added conformance fixtures for valid and invalid hardened-schema behavior.
- Added non-normative compatibility normalizer tooling for opt-in adapter-side
  migration from selected legacy wire forms.
- Updated README, adapter guidance, examples, and validation tools to use the
  canonical version-discriminated schema.

## [1.0.5]
- Clarified immutable source-authored events versus profile/export projections.
- Clarified UUIDv7 timestamp bits as identity-generation time, not event time.
- Added TIME_STATUS freshness guidance and stale timing behavior.
- Clarified authoritative envelope lineage versus payload-local provenance.
- Tightened authority-boundary, observation-quality, deduplication, system-event extensibility, confidence-degradation, and merge/split lifecycle wording.

## [1.0.4]
- Added UUIDv7 event identity requirements and aligned schema validation.
- Made timing quality metadata mandatory across all profiles.
- Added normative track persistence, deduplication, and edge failure-mode configuration guidance.
- Clarified confidence semantics and Profile L compact stripping rules.
- Aligned schema, policy, validators, adapters, configs, examples, conformance tests, and CI with the locked semantic contract.
- Added timing-quality enforcement, profile mismatch checks, event/TASK_ACK dedupe checks, and semantic-contract hashing in the reference gateway tooling.

## [1.0.3]
- Added compact binary mapping for Profile L plus reference CBOR/compact encoders and size tooling.
- Expanded schema/policy to cover Observation/Inference/Fusion payloads and SystemEvent requirements.
- Enhanced gateway with JSON/CBOR/compact I/O, strict validation, rate limiting/metrics logs,
  contract-hash gating, and COMMAND_EVENT dedupe.
- Added conformance pack, example validators, and encoding roundtrip examples/tests.
- Added new documentation for compact mapping, field dictionary, profile compatibility, and refreshed specs.
- Fixed MAVLink TASK_ACK ingress to require original_event_id in metrics.
- Set pytest cache to repo-local path to avoid teardown hangs in restricted environments.

## [1.0.2]
- Expanded installation docs with bundle-based step-by-step guidance, prerequisites,
  config references, verification, and troubleshooting.
- Added deployment helpers and configs for edge/gateway installs (Docker Compose + config templates).
- Added end-to-end workflow test tooling with profile variants.
- Tightened routing policy and validator enforcement (producer allowlists, TASK_ACK required fields).
- Updated semantics contract and examples for operating model, lineage, and data_ref guidance.
- Release artifacts refreshed; obsolete Compose `version` removed.

## [1.0.1]
- Added optional timing fields (`t_publish`, `t_receive`) to schema and docs.
- Clarified observation quality vs confidence; tightened role/profile guidance.
- Updated policy/routing enforcement and producer rules; EDGE role restricted to observation + system.
- Added live gateway UDP test tool and Makefile target; expanded README/quickstart instructions.

## [1.0.0]
- Initial public release of the ZMeta specification
