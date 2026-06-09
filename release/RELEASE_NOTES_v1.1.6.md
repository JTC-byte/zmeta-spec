# ZMeta v1.1.6 Release Notes

Release date: 2026-06-09
Release type: semantic risk governance, operator adaptability, kernel protection, and runtime validation

## Summary

ZMeta v1.1.6 hardens the live stack around the finalized semantic contract while
preserving the core interoperability guarantees of the v1.0 baseline.

This release does not add new event vocabulary, does not make future-extension
concepts valid, and does not claim literal raw IQ support. SDR-derived RF
adapter workflows are validated through existing reduced sensor outputs and
SignalHunter PSD capture handling. Literal raw IQ support remains future work
pending real sensor data and approved adapter semantics.

## Major Work Completed

### Risk Adjudication And Operator Adaptability

- Added the semantic baseline for locked, tunable, advisory, and
  future-extension rules.
- Preserved strict formatting and semantic interoperability while allowing
  policy-controlled reject, warn, degrade, quarantine, and ignore behavior for
  tunable operational risks.
- Required accepted-risk data to remain honestly labeled and filterable instead
  of being rewritten as clean data.
- Added consumer-side accepted-risk filtering through `tools/filter_risk.py`.
- Added presets for display, fusion, state, command, autonomy, AAR, and audit
  intake posture.

### Kernel Protection Doctrine

- Added the completeness-without-exhaustiveness doctrine to prevent uncontrolled
  core-contract growth.
- Defined a concrete threshold for future core semantic changes.
- Kept future-extension concepts visible for governance but non-claimable until
  versioned schema, policy, adapter, encoding, and conformance evidence exists.
- Wired full kernel-protection conformance into local validation, CI, and
  release checklist usage.

### Semantic Bad Events And Adapter Harness

- Added a semantic bad-event corpus for dishonest or unsafe events that must not
  be accepted as clean data.
- Added a shared adapter conformance harness for schema/policy validity, layer
  separation, lineage, timing, and external promotion evidence.
- Promoted generic adapter and CoT projection evidence while keeping broader
  native sensor-adapter certification as future breadth work.

### Adapter Boundary Hardening

- Hardened direct CoT egress so malformed `STATE_EVENT` payloads carrying raw
  observation/evidence fields fail closed.
- Documented the CoT egress precondition that state projections must not carry
  `features`, `raw_features`, `modality`, raw measurement fields, observation
  timestamps, or raw data references.

### End-to-End Runtime Validation

- Completed a folder-by-folder stack audit against the semantic contract.
- Ran strict examples, compatibility checks, full kernel conformance, focused
  validators, gateway self-tests, full pytest, live UDP workflow sweeps, packet
  size checks, risk-filter checks, release package checks, MVP bundle smoke
  checks, and Docker Compose config rendering.
- Exercised disposable gateway containers across Profile H, Profile M, and
  Profile L compact output with a simulated SignalHunter PSD capture converted
  through the real adapter into ZMeta RF observation, then through ZMeta state,
  CoT output, and MAVLink MissionIntent conversion.

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
validation, strict full-kernel conformance, examples, compatibility checks,
focused projection/registry/class/encoding/precision/bad-event/adapter
validators, full pytest, gateway self-tests, live profile and encoding workflow
sweeps, Profile L packet-size checks, risk-filter checks, package smoke tests,
and containerized SDR-derived RF workflow checks.

See `release/VALIDATION_REPORT_v1.1.6.md` for command details.

## Release Assets

Expected release assets:

- `zmeta-v1.1.6-dist.zip`
- `zmeta-edge-v1.1.6.zip`
- `zmeta-gateway-v1.1.6.zip`
- `zmeta-release-package-v1.1.6.zip`
- `zmeta-release-manifest.yaml`
- `RELEASE_NOTES_v1.1.6.md`
- `VALIDATION_REPORT_v1.1.6.md`
- `SHA256SUMS_v1.1.6.txt`

No detached `.asc` signatures are attached unless the release authority signs
the artifacts with an approved external signing process. No private keys,
credentials, tokens, certificates, or signing secrets are stored in this
repository.

## Upgrade Notes

- Consumers pinned to v1.0 schema validation should not need event payload
  changes.
- Deployments using release or contract hash gates should update expected
  hashes from the v1.1.6 release manifest.
- Consumers should continue to reject v1.1.0 or future vocabulary in v1.0
  validation paths.
- Operators can now use `tools/filter_risk.py` to select accepted-risk intake
  posture without mutating events or bypassing semantics.
