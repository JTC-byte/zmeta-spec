# ZMeta v1.1.2 Release Notes

Release tag: `v1.1.2`

## Summary

ZMeta v1.1.2 closes the remaining integration and operational follow-ons from
the v1.1.1 feedback pass. It does not change the schema contract or vocabulary:
`zmeta_version: "1.0"` and `zmeta_version: "1.1.0"` remain the supported event
envelope versions.

This release focuses on migration diagnostics, timing observability, protobuf
decoder hardening tests, release-signing operations, and documentation needed to
operate deployment policy variants safely.

## Compatibility and Migration

- Added `tools/check_compat.py`, a migration-oriented JSON/JSONL checker that
  reports timestamp format, subtype vocabulary, v1.1-only vocabulary without
  `zmeta_version: "1.1.0"`, missing or degraded timing quality,
  producer-authority misses, profile violations, policy violations, and CoT
  projection blockers as separate categories.
- The checker defaults to the canonical version-discriminated schema and
  reference policy directory, and supports text or JSON output.
- The local examples and carried documentation examples were validated against
  the checker with zero reported issues.

## Runtime Observability

- Gateway metrics now distinguish source-provided timing from degraded fallback
  timing with `timing_quality_source`, `timing_quality_fallback`, and
  `timing_quality_modes`.
- `UNKNOWN` / `UNSYNCED` timing remains schema-valid fallback timing, but is
  explicitly observable so operators do not confuse it with high-quality timing.

## Protobuf Hardening

- Added malformed protobuf regression coverage for oversized varints, truncated
  length-delimited fields, huge declared field lengths, invalid UTF-8 string
  fields, truncated fixed fields, deterministic malformed samples, and seeded
  random byte fuzzing.

## Documentation and Release Operations

- Documented how policy variants interact with deployment policy and contract
  hashes.
- Documented supported adapter invocation style for package imports from the
  repository root.
- Documented degraded fallback timing semantics for adapters, configs, and
  gateway metrics.
- Added explicit GitHub release verification text covering the public key,
  detached signatures, checksum signature, and asset checksum verification.
- Hardened `release/sign_release_artifacts.py` so Gpg4win installs are found on
  Windows even before the current shell sees the updated PATH.

## Z-ISR Breakpoint Validation

The local stack was rechecked against the integration breakpoints called out in
the feedback email:

- Active examples/docs serialize UTC timestamps with trailing `Z`.
- Legacy subtype names such as `PLATFORM_POSITION`, `EDGE_HEALTH`,
  `RF_OBSERVATION`, `TRIANGULATION`, and `RETASK_SUGGESTION` are not present in
  active event examples.
- Active `PLATFORM_STATUS` events use `zmeta_version: "1.1.0"`.
- Active operational events expose per-event timing quality or valid
  `TIME_STATUS` timing.
- Active `source.producer` values are represented by the reference
  producer-authority policy.

## Release Authenticity

The v1.1.2 artifacts are signed with the ZMeta release signing key:

- UID: `Incept.IO ZMeta Release Signing <justintylercarr@gmail.com>`
- Fingerprint: `A3B150AF2A0E1CA413C4B7F112BE81F54654B96E`
- Public key asset: `ZMETA_RELEASE_SIGNING_KEY_v1.1.2.asc`

Recommended verification flow:

1. Import or otherwise trust the documented public key/fingerprint.
1. Verify `SHA256SUMS_v1.1.2.txt.asc` against `SHA256SUMS_v1.1.2.txt`.
1. Verify each detached asset signature.
1. Verify release asset hashes against `SHA256SUMS_v1.1.2.txt`.

## Artifacts

- `zmeta-v1.1.2-dist.zip`
- `zmeta-edge-v1.1.2.zip`
- `zmeta-gateway-v1.1.2.zip`
- `SHA256SUMS_v1.1.2.txt`
- Detached `.asc` signatures for the checksum manifest and release assets
- `ZMETA_RELEASE_SIGNING_KEY_v1.1.2.asc`
