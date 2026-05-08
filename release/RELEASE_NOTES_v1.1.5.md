# ZMeta v1.1.5 Release Notes

Release date: 2026-05-07
Release type: hardened baseline, release governance, and formal packaging framework

## Summary

ZMeta v1.1.5 is the hardened baseline release for the current ZMeta stack. It does not add new
event vocabulary and does not promote v1.1.0 experimental concepts into the v1.0 baseline. The
release focuses on semantic-governance hardening, conformance coverage, deterministic release
hashing, release manifest validation, and formal release packaging support.

The core guardrails remain intact:

- v1.0 events validate only against v1.0 vocabulary.
- v1.1.0 remains an isolated experimental branch.
- Future concepts remain invalid until adopted through a versioned branch with schema, policy,
  adapter, encoding, documentation, and conformance coverage.
- ZMeta remains a semantic data standard focused on ISR interoperability, profiles, adapters,
  encodings, validation, conformance, and release baselines.

## Major Work Completed

### Semantic Contract And Baseline Governance

- Audited the v1.0 semantic baseline and tightened contract-to-stack alignment.
- Preserved the distinction between authoritative semantics and implementation surfaces.
- Confirmed schemas, policies, adapters, encodings, examples, and conformance fixtures preserve the
  semantic contract rather than redefining it.
- Removed out-of-scope organizational artifact language from the active ZMeta baseline.

### Strict Version Isolation

- Preserved strict schema dispatch by `zmeta_version`.
- Confirmed v1.0 validation does not accept v1.1.0 or future vocabulary.
- Kept v1.1.0 experimental semantics isolated pending future branch governance.

### Profile Projection Preservation

- Added profile projection field catalog validation.
- Added must-pass and must-fail profile projection fixtures.
- Added projection validation tooling and conformance integration.
- Reinforced that profile thinning must not change event meaning.

### Extension Registry Governance

- Added extension registry validation.
- Clarified status handling for future or reserved concepts.
- Confirmed registry entries do not become valid event vocabulary until adopted by a versioned schema
  and conformance path.

### Conformance Class Manifest And Claims

- Added a machine-readable conformance class manifest.
- Added example reference-gateway and core-producer claims.
- Added conformance class validation and conformance-runner integration.
- Preserved narrower core-producer claims relative to gateway behavior.

### Encoding Negative Validation

- Added compact, protobuf, and gateway negative-validation fixture suites.
- Added validation tooling to prevent encodings from bypassing schema, policy, or semantic checks.
- Confirmed protobuf remains an encoding projection, not an independent semantic contract.

### Profile Precision And Quantization Policy

- Added profile precision policy validation.
- Added profile precision must-pass and must-fail fixtures.
- Clarified precision floors for bandwidth-aware profile export behavior.

### Adapter Documentation Cleanup

- Cleaned TAKEOFF crosswalk wording.
- Cleaned MAVLink adapter README state payload drift.
- Reinforced that adapter documentation must not imply raw-field drift for STATE_EVENT payloads.

### Contract Hash And Release Hash System

- Kept semantic contract hashing narrow.
- Added structured release manifest hashing for the broader governed baseline.
- Added deterministic SHA-256 canonicalization with LF-normalized text hashing.
- Added category hashes, release bundle hash, release manifest hash, builder, validator, tests, and
  optional conformance-runner integration.

### Formal Release Packaging Framework

- Added release signing and attestation specification.
- Added release notes, attestation, and release package README templates.
- Added release package builder and validator.
- Added no-secret checks for private-key, token, credential, and signing-secret patterns.
- Added release package tests and optional `--release-package` conformance integration.
- Confirmed release signatures and attestations do not create ZMeta semantics and do not make future
  vocabulary valid.

### Future Semantic Branch Roadmap

- Added a roadmap for future versioned semantic branches under D-003.
- Classified future candidates such as PNT integrity, event signing, mesh trust, AI assurance,
  track lifecycle, projection metadata, modality contracts, and emergency/L0 profile behavior.
- Kept those concepts future-only until approved through versioned implementation and audit.

## Issue Status At Release

- D-001: CLOSED
- D-002: CLOSED
- D-003: OPEN - ROADMAP PLANNED
- D-004: CLOSED - REMOVED FROM ZMETA SCOPE
- D-005: CLOSED
- D-006: CLOSED
- D-007: CLOSED
- D-008: CLOSED
- D-010: CLOSED
- D-011: CLOSED
- D-012: CLOSED

## Validation Summary

The release baseline was validated with release manifest validation, release package template
validation, contract hash computation, strict conformance validation, projection validation,
extension registry validation, conformance class validation, encoding-negative validation,
precision-policy validation, focused release package tests, and full pytest.

See `release/VALIDATION_REPORT_v1.1.5.md` for command details.

## Release Assets

Expected release assets:

- `zmeta-v1.1.5-dist.zip`
- `zmeta-edge-v1.1.5.zip`
- `zmeta-gateway-v1.1.5.zip`
- `zmeta-release-package-v1.1.5.zip`
- `zmeta-release-manifest.yaml`
- `RELEASE_NOTES_v1.1.5.md`
- `VALIDATION_REPORT_v1.1.5.md`
- `SHA256SUMS_v1.1.5.txt`

Detached signatures may be attached if the release authority signs the artifacts with an approved
external signing process. No private keys, credentials, tokens, certificates, or signing secrets are
stored in this repository.

## Upgrade Notes

- Consumers pinned to v1.0 schema validation should not need event payload changes.
- Deployments using release or contract hash gates should update expected hashes from the v1.1.5
  release manifest.
- Consumers should continue to reject v1.1.0 or future vocabulary in v1.0 validation paths.
