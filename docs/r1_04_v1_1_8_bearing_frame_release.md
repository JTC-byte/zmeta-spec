# R1-04 v1.1.8 Bearing-Frame Release Audit

Status: release audit for v1.1.8.

Date: 2026-06-12

## Scope

v1.1.8 adopts the partner bearing-frame integrity stack and the local
P1-04R review fixes. It publishes:

- the true-north bearing/heading convert-or-omit rule;
- optional v1.1.0 `payload.bearing.frame = "TRUE_NORTH"`;
- adapter hardening for Kraken, Moth, SignalHunter, and MAVLink;
- adapter-harness value pins for bearing/heading behavior;
- gateway runtime guard improvements;
- professional overview documentation and generated overview figures.

## Semantic Boundary

- The v1.0 schema remains locked and unchanged.
- No v1.1.0 or future vocabulary became valid under `zmeta_version: "1.0"`.
- Unknown-frame Moth bearings and MAVLink headings are no longer emitted as
  canonical ZMeta fields by default.
- Explicit deployment assertions are required before Moth tunnel/replay
  bearings or MAVLink `hdg` values become canonical true-north fields.

## Release Artifacts

Expected v1.1.8 artifacts:

- `release/zmeta-v1.1.8-dist.zip`
- `release/zmeta-edge-v1.1.8.zip`
- `release/zmeta-gateway-v1.1.8.zip`
- `release/zmeta-release-package-v1.1.8.zip`
- `release/zmeta-release-manifest.yaml`
- `release/RELEASE_NOTES_v1.1.8.md`
- `release/VALIDATION_REPORT_v1.1.8.md`
- `release/SHA256SUMS_v1.1.8.txt`

Detached signatures are not generated unless an approved release signing key is
available through the release authority.

## Validation

The final validation command output is recorded in
`release/VALIDATION_REPORT_v1.1.8.md` and summarized in
`docs/zmeta_refinement_worklog.md`.
