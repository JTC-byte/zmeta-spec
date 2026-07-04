# ZMeta v1.1.10 Release Notes

Release date: 2026-07-03
Release type: fielded-safety enforcement patch (command-altitude and STATE
laundering enforcement, adapter calibration honesty)

## Summary

ZMeta v1.1.10 hardens the reference enforcement of two locked-contract safety
invariants and closes an adapter honesty gap. It aligns the policy and reference
implementation with the already-normative semantics contract (sections 7.7 and
7.8); it adds no schema changes and makes no v1.1.0 or future vocabulary valid
under `zmeta_version: "1.0"`. The locked v1.0 kernel is unchanged.

The tightened enforcement rejects only events that were always
contract-violating (raw sensor content laundered into a STATE projection, or
altitude specified on a COMMAND_EVENT). Producers and consumers that already
honor the contract are unaffected.

## Major Work Completed

### Command Altitude Enforcement (section 7.8)

- Expanded `policy/semantics.yaml` `command_event.payload_must_not_contain` from
  `[alt, alt_m, altitude]` to the full section 7.8 altitude set (`altitude_m`,
  `alt_hae_m`, `alt_msl_m`, `agl_m`, `target_alt_m`, `target_altitude`, with bare
  `alt` retained as a defensive superset). A `COMMAND_EVENT` must not specify
  altitude at any nesting depth in the payload, `target_geo`, `geometry`, or
  `extensions`; the receiving autonomy deconflicts vertical internally.
- Aligned the egress MAVLink command guard
  (`adapters/egress/mavlink/zmeta_command_to_mission_intent.py`) to the same
  altitude set so the command-to-mission-intent projection refuses altitude at
  any depth in the projected geometry.

### STATE Laundering Enforcement (section 7.7)

- Expanded `policy/semantics.yaml` `state_event.payload_must_not_contain` from
  `[features, raw_features]` to the full section 7.7 set (adds `modality`,
  `measurement`, `measurements`, `t_start`, `t_end`, `data_ref`, `data_refs`).
- Made the STATE semantic check in `gateway/src/validators.py` recursive via the
  shared `_find_forbidden_key` helper (matching the observation, inference, and
  command branches), so nested raw features, measurements, observation
  timestamps, and raw-artifact pointers can no longer launder into a STATE
  projection through free-form objects or lists.

### Denylist Key Normalization

- The semantic forbidden-key check and the egress altitude guard now normalize
  keys (strip surrounding whitespace, casefold) before matching, so
  whitespace- or case-padded copies of a reserved name (for example
  `"features "` or `"alt_hae_m "`) can no longer evade the exact-name denylists
  that the schema pins only for the exact bytes.

### Adapter Calibration Honesty

- The Kraken and Moth reference adapters no longer hardcode
  `quality.calibration_state: CALIBRATED`. `calibration_state` is now a keyword
  parameter that defaults to the conservative, honest `UNCALIBRATED` (enum
  `CALIBRATED`/`UNCALIBRATED`/`DEGRADED`); a deployment asserts `CALIBRATED` or
  `DEGRADED` only when it can substantiate it, mirroring the existing
  convert-or-config pattern used for `platform_heading_deg`. SignalHunter was
  already honest.

## Known Enforcement Limitation

The section 7.7/7.8 enforcement is a reserved-key denylist, not a value
classifier. Raw content or altitude re-keyed under an arbitrary, non-reserved
name (for example `z_m`) inside a free-form object passes both the schema and
the semantic check. This is the inherent limit of a name denylist; the
mitigation is closed payload schemas plus producer conformance, not denylist
growth. This limitation is unchanged from prior releases and is documented here
for completeness.

## Issue Status At Release

- D-003: OPEN - ROADMAP PLANNED for future versioned semantic branch work.

## Validation Summary

The release was validated with release manifest and package validation, strict
examples, full kernel conformance (projection, registry, conformance class,
encoding-negative, precision-policy, release-manifest, release-package,
bad-event, and adapter validators), full pytest, release artifact builds,
checksum generation and verification, and `git diff --check`. The tightened
enforcement was additionally verified with an adversarial pass of 100+ empirical
bypass attempts against the real validators and egress guard.

See `release/VALIDATION_REPORT_v1.1.10.md` for command details.

## Release Assets

Expected release assets:

- `zmeta-v1.1.10-dist.zip`
- `zmeta-edge-v1.1.10.zip`
- `zmeta-gateway-v1.1.10.zip`
- `zmeta-release-package-v1.1.10.zip`
- `zmeta-release-manifest.yaml`
- `RELEASE_NOTES_v1.1.10.md`
- `VALIDATION_REPORT_v1.1.10.md`
- `SHA256SUMS_v1.1.10.txt`

No detached `.asc` signatures are attached unless the release authority signs the
artifacts with an approved external signing process. This release is published
checksums-only, consistent with v1.1.5 through v1.1.9. No private keys,
credentials, tokens, certificates, or signing secrets are stored in this
repository.

## Upgrade Notes

- Consumers pinned to v1.0 schema validation need no event payload changes.
- Producers that emitted altitude on a `COMMAND_EVENT` under a section 7.8 field
  name other than `alt`/`alt_m`/`altitude`, or that carried raw observation
  fields nested inside a STATE payload, were already violating the contract and
  will now be rejected. Move altitude out of commands (the receiving autonomy
  owns vertical deconfliction) and keep STATE projections free of raw sensor
  content, using `lineage.based_on` for traceability.
- Adapter integrators relying on the Kraken/Moth reference adapters should pass
  `calibration_state="CALIBRATED"` (or `"DEGRADED"`) explicitly only when the
  deployment can substantiate calibration; the default is now `UNCALIBRATED`.
- Deployments using release or contract hash gates should update expected hashes
  from the v1.1.10 release manifest.
