# ZMeta v1.1.9 Release Notes

Release date: 2026-06-18
Release type: documentation freshness, governance hygiene, timing/compact
follow-up, and current-main release hygiene patch

## Summary

ZMeta v1.1.9 publishes the post-v1.1.8 current-main cleanup and documentation
freshness work as a formal patch release. It preserves the locked v1.0 kernel
and does not make v1.1.0 or future vocabulary valid under
`zmeta_version: "1.0"`.

The release updates active documentation and release tooling around the current
baseline, refreshes the README-linked installation guidance, closes the
previously deferred D-013 and D-014 follow-ups, and records advisory governance
and industry-sharing posture docs.

## Major Work Completed

### Documentation Freshness And Release Hygiene

- Refreshed `spec/installation-guide.md` so new deployments start from the
  maintained `configs/` templates instead of older code-local examples.
- Audited README-linked documentation and adjacent detail docs for broken
  relative links, stale release/current-main wording, rogue untracked files,
  and generated-output tracking risk.
- Corrected stale handoff/worklog/local-note references that treated
  `beffed3` as the final pushed integration closeout. The current final
  closeout baseline before this release was `c814d95`.
- Updated current-release pointers, release tooling defaults, and package
  examples for `v1.1.9`.

### Timing And Compact Follow-Up Closure

- Closed D-013 by adding governed negative TIME_STATUS age diagnostics through
  `TIMING_STATUS_AGE_NEGATIVE`, profile-specific `max_negative_age_ms`, default
  warn-mode policy handling, risk-adjudication support, and conformance/tests.
- Closed D-014 by rejecting unknown compact integer keys at decode while still
  preserving allowed string extension keys.

### Governance And Industry-Sharing Posture

- Added advisory open-specification, contributor-authority, conformance,
  name-use, and defensive-publication docs:
  `IP_POLICY.md`, `CONTRIBUTING.md`, `CONFORMANCE.md`, `TRADEMARK.md`, and
  `docs/zmeta_defensive_publication.md`.
- Clarified that these docs do not create legal advice, a trademark
  registration, a patent opinion, or a standards-body patent policy.

### Adapter Upgrade Guidance

- Clarified Moth tunnel/replay bearing and MAVLink heading upgrade
  responsibilities for explicit `TRUE_NORTH` assertions.
- Documented that `bearing.frame`, `quality.bearing_frame`, and
  `quality.heading_source` are producer/configuration provenance, not proof of
  calibration, authenticity, or correctness.

## Issue Status At Release

- D-003: OPEN - ROADMAP PLANNED for future versioned semantic branch work.
- D-013: CLOSED in current `main` and included in this release.
- D-014: CLOSED in current `main` and included in this release.

Future work remains optional and should be driven by real sensor captures, a
versioned semantic branch decision, release-authority signing process, formal
legal review, standards-body adoption, or broader deployment/container runtime
needs.

## Validation Summary

The release was validated with release manifest validation, release package
validation, strict examples, full kernel conformance, focused projection,
registry, conformance class, encoding-negative, precision-policy, bad-event,
adapter validators, risk-filter checks, gateway self-tests, full pytest,
release artifact builds, checksum generation and verification, and
`git diff --check`.

See `release/VALIDATION_REPORT_v1.1.9.md` for command details.

## Release Assets

Expected release assets:

- `zmeta-v1.1.9-dist.zip`
- `zmeta-edge-v1.1.9.zip`
- `zmeta-gateway-v1.1.9.zip`
- `zmeta-release-package-v1.1.9.zip`
- `zmeta-release-manifest.yaml`
- `RELEASE_NOTES_v1.1.9.md`
- `VALIDATION_REPORT_v1.1.9.md`
- `SHA256SUMS_v1.1.9.txt`

No detached `.asc` signatures are attached unless the release authority signs
the artifacts with an approved external signing process. No private keys,
credentials, tokens, certificates, or signing secrets are stored in this
repository.

## Upgrade Notes

- Consumers pinned to v1.0 schema validation should not need event payload
  changes.
- Deployments using release or contract hash gates should update expected
  hashes from the v1.1.9 release manifest.
- Adapter callers should continue to honor the v1.1.8 bearing-frame rules:
  Moth tunnel/replay bearings and MAVLink headings become canonical only when
  deployment configuration explicitly asserts `TRUE_NORTH`, and Kraken DOA
  requires platform heading compensation before canonical bearing emission.
