# ZMeta v1.1.7 Release Notes

Release date: 2026-06-10
Release type: projection/registry hardening, process governance, downstream interoperability guidance, and release audit cleanup

## Summary

ZMeta v1.1.7 publishes the post-v1.1.6 hardening work on current `main` as a
formal patch release. It makes extension, risk, projection, and contributor
process expectations more machine-checkable and easier for downstream
integrators to follow without changing the locked v1.0 semantic kernel.

This release does not add event vocabulary, does not make future-extension
concepts valid, does not change v1.0 schema semantics, and does not claim
literal raw IQ support.

## Major Work Completed

### Profile Projection Risk Preservation

- Added machine-checkable projection catalog entries for
  `payload.extensions.risk_adjudication`.
- Added compact external-promotion preservation behavior for
  `payload.extensions.external_promotion`.
- Added pass/fail fixtures proving lower-profile projections must not silently
  strip risk/use labels or external-promotion evidence when those fields affect
  display, fusion, command basis, autonomy, TAK/coalition export, TTL,
  confidence, or routing.
- Added explicit projection failure codes for removed policy/risk labels and
  external-promotion evidence.

### Extension Registry Contract Hardening

- Strengthened registry entries with validated projection behavior, risk
  relevance, policy-preservation, security/privacy, and fixture-reference
  fields.
- Updated registry docs and tests so vendor and edge extensions declare whether
  they matter to projection, policy, and accepted-risk handling.
- Clarified that the machine-readable registry exists now and is no longer
  future work.

### Process Governance And Downstream Clone Limits

- Added `AGENTS.md` as the root guide for human maintainers and AI agents.
- Added `docs/zmeta_change_governance.md` with authority order, change classes,
  documentation requirements, validation gates, release limits, and publication
  workflow.
- Added governed `process_governance_hash` release-manifest coverage.
- Added downstream clone guidance: local adapters, policy/config, profiles, and
  namespaced extensions are expected integration paths; local changes to core
  schema, event vocabulary, version dispatch, projection semantics, risk
  labels, or command authority create a private dialect/fork unless governed,
  versioned, documented, and covered by conformance evidence.

### Release Audit Cleanup

- Updated active current-release pointers and compatibility defaults to
  v1.1.7.
- Confirmed ignored local release build directories were untracked and rebuilt
  from the current source.
- Confirmed no tracked generated release ZIP/signature residue or tracked
  source secret findings were present during the audit.

## Issue Status At Release

- D-001: CLOSED
- D-002: CLOSED
- D-003: OPEN - ROADMAP PLANNED
- D-004: CLOSED - REMOVED FROM ZMETA SCOPE
- D-005: CLOSED
- D-006: CLOSED
- D-007: CLOSED
- D-008: CLOSED
- D-009: CLOSED
- D-010: CLOSED
- D-011: CLOSED
- D-012: CLOSED

## Validation Summary

The release was validated with release manifest validation, release package
validation, strict examples, full kernel conformance, focused projection,
registry, conformance class, encoding-negative, precision-policy, bad-event,
and adapter validators, compatibility checks, gateway self-tests, risk-filter
checks, full pytest, release artifact builds, checksum generation and
verification, and `git diff --check`.

See `release/VALIDATION_REPORT_v1.1.7.md` for command details.

## Release Assets

Expected release assets:

- `zmeta-v1.1.7-dist.zip`
- `zmeta-edge-v1.1.7.zip`
- `zmeta-gateway-v1.1.7.zip`
- `zmeta-release-package-v1.1.7.zip`
- `zmeta-release-manifest.yaml`
- `RELEASE_NOTES_v1.1.7.md`
- `VALIDATION_REPORT_v1.1.7.md`
- `SHA256SUMS_v1.1.7.txt`

No detached `.asc` signatures are attached unless the release authority signs
the artifacts with an approved external signing process. No private keys,
credentials, tokens, certificates, or signing secrets are stored in this
repository.

## Upgrade Notes

- Consumers pinned to v1.0 schema validation should not need event payload
  changes.
- Deployments using release or contract hash gates should update expected
  hashes from the v1.1.7 release manifest.
- Consumers should continue to reject v1.1.0 or future vocabulary in v1.0
  validation paths.
- Downstream clones should prefer adapters, policy/config, profile selection,
  and namespaced extensions over local core schema or semantic changes.
