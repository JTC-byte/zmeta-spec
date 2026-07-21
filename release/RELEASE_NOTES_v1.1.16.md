# ZMeta v1.1.16 Release Notes

Release date: 2026-07-21
Release type: external real-capture corpus (PR #7 edge-comms bladeRF
mapping pack, merged with maintainer honesty fixes)

## Summary

ZMeta v1.1.16 ships the repository's first external real-capture
corpus: `adapters/mapping-packs/edge-comms-bladerf/` (PR #7,
bkershner-torch) — two real bladeRF / ROS2 EW `rf_detection` records
from a 2026-05-14 edge-comms flight blackbox, paired with schema-valid
ZMeta v1.0 RF `OBSERVATION_EVENT` expected outputs for adapter authors
to diff against. It is a second independent RF telemetry source
alongside the maintainer deployments, and the contribution's honesty
handling was strong as submitted: null and zero-island sensor
positions refuse canonical geo with `geo_status: UNAVAILABLE`, the
no-DOA case omits canonical bearing, the degraded timing fallback
matches the repository convention exactly, and no lineage is
fabricated.

The merge applied maintainer fixes from an adversarial review — the
notable one being a doctrine call the machine gates cannot make:
case-02's canonical bearing was provably heading-derived (azimuth
equals the UAS heading plus a fixed antenna offset) with no reference
frame asserted anywhere in the capture, so it is demoted to explicitly
named native features per contract 6.4 and the authoring guide's
frame rule. The pack documents the frame-provenance route
(`quality.bearing_frame` + `quality.heading_source`) for deployments
that can assert their heading reference.

No schema, policy, or event-vocabulary changes; the locked v1.0
kernel's semantics are unchanged.

## Changes

- New pack `adapters/mapping-packs/edge-comms-bladerf/`
  (schema_id `vendor:edge_comms_bladerf:v1`): README with provenance,
  `mapping.yaml`, `pack.json`, and two input/expected fixture pairs
  (VHF orbit-spectrum detection; C-band FFT detection), both passing
  `tools/validate.py --profile H --strict`.
- Maintainer review fixes applied on merge: frame-unlabeled bearing
  demoted to `features.native_bearing_deg`/`native_bearing_error_deg`
  (both cases now omit `payload.bearing`); the unasserted `1_SIGMA`
  measurement-error metric dropped; `features.timestamp_source`
  preserves receive-time vs embedded-telemetry timestamp provenance;
  `mapping.yaml` reconciled with the fixtures; the FFT-bin-width
  `bandwidth_hz` convention documented.
- Governance records for the review and merge are maintainer-authored
  (worklog P1-08 entry); the PR's own record hunks were not merged,
  per the contribution-intake doctrine.

## Compatibility

- No event-vocabulary, schema, or policy changes; nothing new becomes
  valid under any `zmeta_version`.
- Deployments using release or contract hash gates should update
  expected hashes from the v1.1.16 release manifest.

## Validation

The full command battery and results are in
`release/VALIDATION_REPORT_v1.1.16.md`. Headline: full kernel gate
green with all flags, strict examples 51/51, full pytest suite green
with zero failures, both pack fixtures pass strict H-profile
validation, compat sweep 9/9 at the v1.1.16 target.

## Assets and Verification

Assets: `zmeta-v1.1.16-dist.zip`, `zmeta-edge-v1.1.16.zip`,
`zmeta-gateway-v1.1.16.zip`, `zmeta-release-package-v1.1.16.zip`,
`zmeta-release-manifest.yaml`, `RELEASE_NOTES_v1.1.16.md`,
`VALIDATION_REPORT_v1.1.16.md`, `SHA256SUMS_v1.1.16.txt`.

Verify asset integrity:

```bash
sha256sum -c SHA256SUMS_v1.1.16.txt
# or, from a repo checkout:
python release/sign_release_artifacts.py --version v1.1.16 --verify-checksums
```

Signing decision: this is a checksums-only release — no detached
signatures are attached. Signature generation remains the maintainer's
external release-authority process.
