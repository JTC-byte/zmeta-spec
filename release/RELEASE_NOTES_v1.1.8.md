# ZMeta v1.1.8 Release Notes

Release date: 2026-06-12
Release type: bearing-frame integrity, adapter hardening, gateway runtime guard, and professional overview release

## Summary

ZMeta v1.1.8 adopts the partner bearing-frame integrity stack and closes the
review blockers found before adoption. The release makes canonical bearing and
heading fields harder to misuse: sensor-native or unknown-frame values must be
converted to true north before canonical emission, or retained only in
explicitly named non-canonical fields.

The locked v1.0 schema remains unchanged. The v1.1.0 schema gains only an
optional `payload.bearing.frame` marker whose single valid value is
`TRUE_NORTH`.

## Major Work Completed

### Bearing Reference-Frame Contract

- Added normative semantics-contract section 6.4 language requiring canonical
  `payload.bearing.az_deg` and `payload.heading_deg` to be degrees true north.
- Added optional v1.1.0 `payload.bearing.frame = "TRUE_NORTH"` as a
  machine-checkable assertion. Other frame labels are schema-invalid.
- Added the experimental `BEARING_FRAME` extension-registry entry.
- Added bad-event coverage for a mislabeled sensor-native bearing frame.

### Adapter Hardening

- Kraken DOA now converts array-relative bearings to true north only when a
  platform heading is supplied, preserves raw DOA under
  `features.doa_array_relative_deg`, and no longer fabricates CSV SNR from
  RSSI.
- Moth serial and custom MAVLink omnidirectional readings no longer fabricate a
  due-north bearing or 180-degree angular error.
- Moth tunnel/replay bearings now emit canonical `payload.bearing` only when
  callers explicitly pass `bearing_frame="TRUE_NORTH"`; otherwise native
  bearing values are preserved under `features.bearing_frame_unknown_*`.
- SignalHunter gradient LOBs assert `TRUE_NORTH`/`GPS_COURSE` because their
  bearings are geodesic course bearings.
- MAVLink `hdg` values now emit canonical `payload.heading_deg` only when
  callers explicitly pass `heading_frame="TRUE_NORTH"`; otherwise the native
  value is preserved as `payload.quality.mavlink_hdg_frame_unknown_deg`.

### Runtime And Conformance

- MAVLink platform-state ingress now refuses fabricated null-island state when
  lat/lon are absent or pre-fix `(0, 0)`.
- Gateway runtime metrics gained opt-in `warn_datagram_bytes` observability and
  bounded per-producer rate-limiter state cleanup without changing send
  behavior.
- Adapter conformance fixtures now support exact expected-value pins and cover
  the unknown-frame Moth/MAVLink behavior that blocked adoption.

### Documentation

- Added the professional ZMeta overview and generated overview figures.
- Updated adapter READMEs, schema README, tools/config docs, changelog,
  worklog, and handoff notes for the new bearing-frame behavior.

## Issue Status At Release

- D-013: OPEN - NEEDS MAINTAINER SEMANTICS DECISION
- D-014: OPEN - NEEDS MAINTAINER SEMANTICS DECISION

D-013 covers timing-freshness negative-age handling. D-014 covers compact-codec
unknown integer payload keys. Both remain deferred because they require new
governed semantic or encoding surface.

## Validation Summary

The release was validated with release manifest validation, release package
validation, strict examples, full kernel conformance, focused projection,
registry, conformance class, encoding-negative, precision-policy, bad-event,
adapter validators, risk-filter checks, gateway self-tests, full pytest,
release artifact builds, checksum generation and verification, and
`git diff --check`.

See `release/VALIDATION_REPORT_v1.1.8.md` for command details.

## Release Assets

Expected release assets:

- `zmeta-v1.1.8-dist.zip`
- `zmeta-edge-v1.1.8.zip`
- `zmeta-gateway-v1.1.8.zip`
- `zmeta-release-package-v1.1.8.zip`
- `zmeta-release-manifest.yaml`
- `RELEASE_NOTES_v1.1.8.md`
- `VALIDATION_REPORT_v1.1.8.md`
- `SHA256SUMS_v1.1.8.txt`

No detached `.asc` signatures are attached unless the release authority signs
the artifacts with an approved external signing process. No private keys,
credentials, tokens, certificates, or signing secrets are stored in this
repository.

## Upgrade Notes

- Consumers pinned to v1.0 schema validation should not need event payload
  changes.
- Adapter callers that previously consumed Moth tunnel/replay bearings or
  MAVLink headings as canonical must now provide an explicit `TRUE_NORTH`
  frame assertion before those values are emitted as canonical ZMeta fields.
- Deployments using release or contract hash gates should update expected
  hashes from the v1.1.8 release manifest.
