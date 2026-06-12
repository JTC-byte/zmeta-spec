# Changelog

## [Unreleased]
- Clarified v1.1.8 current-main upgrade guidance for Moth tunnel/replay
  bearings, MAVLink headings, Kraken heading compensation, and Kraken CSV SNR
  omission. The docs now also state explicitly that `bearing.frame`,
  `quality.bearing_frame`, and `quality.heading_source` are producer
  assertions/provenance, not proof of calibration, authenticity, or correctness.
- Added advisory industry-sharing and open-specification posture docs:
  `IP_POLICY.md`, `CONTRIBUTING.md`, `CONFORMANCE.md`, `TRADEMARK.md`, and
  `docs/zmeta_defensive_publication.md`. These clarify Apache-2.0 baseline
  limits, contributor authority, private dialects, conformance claims, ZMeta
  name use, and public defensive-publication guidance without changing schemas,
  policy behavior, event vocabulary, or the locked v1.0 kernel.
- Closed D-013 by adding `TIMING_STATUS_AGE_NEGATIVE`, profile-specific
  `max_negative_age_ms`, default warn-mode policy handling, risk-adjudication
  support, schema/policy diagnostic vocabulary coverage, and tests/conformance
  for event timestamps that predate the latest applicable TIME_STATUS beyond
  tolerance.
- Closed D-014 by specifying that unknown compact integer keys are rejected at
  decode, preserving string extension keys, adding decoder enforcement, and
  extending encoding-negative fixtures for the unknown-key path.
- Aligned post-release current-facing documentation, tool examples, CI
  compatibility target, and the compatibility CLI test with the published
  `v1.1.8` release after the stack audit. Historical `v1.1.7` release records
  and published checksums remain unchanged.

## [1.1.8] - 2026-06-12
- Added a machine-checkable bearing reference-frame marker: optional
  `payload.bearing.frame` with single-value enum `["TRUE_NORTH"]` in the
  v1.1.0 schema, a normative semantics-contract section 6.4 (canonical
  bearings SHALL be degrees true north; sensor-native frames convert or omit;
  `quality.bearing_frame`/`quality.heading_source` provenance path for v1.0
  producers), and an experimental `BEARING_FRAME` extension-registry entry.
  The locked v1.0 schema is untouched and still rejects the `frame` key.
- Enforced the bearing reference-frame contract in governed conformance
  corpora: new `observation-bearing-frame-mislabeled` bad-event entry (corpus
  total 10) and an adapter-harness `expected_values` mechanism that pins exact
  output values per fixture (1e-6 numeric tolerance, distinct
  missing/mismatch codes, boolean pins never match numeric output). The
  kraken fixture now pins the rotation math, a no-heading fixture proves
  convert-or-omit, and Moth/MAVLink fixtures pin unknown-frame omission
  behavior (harness total 10).
- Hardened the Kraken adapter (1.1.0): optional platform-heading compensation
  emits true-north `bearing.az_deg` as `(doa + heading + offset) % 360` with
  frame/heading-source provenance, omits the canonical bearing when no heading
  is supplied, always preserves raw DOA in
  `features.doa_array_relative_deg`, and no longer fabricates CSV
  `quality.snr_db` from RSSI.
- Hardened the Moth adapter (1.1.0): serial and custom-MAVLink omnidirectional
  detections no longer fabricate a `bearing.az_deg 0.0` /
  `angular_error_deg 180.0` placeholder, JSON replay no longer invents a
  bearing when the input carries none, and tunnel/replay measured bearings
  emit canonical `payload.bearing` only when the caller explicitly asserts
  `bearing_frame="TRUE_NORTH"`; otherwise raw unknown-frame bearings are
  preserved under explicit `features.bearing_frame_unknown_*` keys.
- Audited remaining bearing/heading producers: SignalHunter (1.0.1) gradient
  LOBs now assert `TRUE_NORTH`/`GPS_COURSE` provenance (true north by
  geodesic construction); the MAVLink adapter (1.1.0) omits
  `payload.heading_deg` when `hdg` is 65535 (unknown), absent, or present
  without explicit `heading_frame="TRUE_NORTH"` instead of emitting an invalid
  or fabricated canonical heading, while preserving unasserted values under
  `payload.quality.mavlink_hdg_frame_unknown_deg`; CoT egress frame behavior is
  documented; eo-cv, CoT ingress, and JREAP have no bearing/heading exposure.
- Added runtime fabrication and resource guards: MAVLink platform state
  refuses null-island `(0, 0)` TRACK_STATE fabrication when position is
  absent or pre-fix, the gateway gained an opt-in `warn_datagram_bytes`
  oversize-datagram observability setting (default off, send behavior
  unchanged), and the producer rate limiter purges stale windows without
  changing accept/reject decisions.
- Regenerated the release manifest and example claim hashes for the governed
  changes. No event vocabulary became valid under `zmeta_version: "1.0"`.
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
