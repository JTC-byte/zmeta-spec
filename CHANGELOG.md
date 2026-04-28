# Changelog

## [Unreleased]

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
