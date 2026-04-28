# ZMeta v1.1.3 Release Notes

Release tag: `v1.1.3`

## Summary

ZMeta v1.1.3 is a CI compatibility patch for the v1.1.2 release. It does not
change the schema contract or event vocabulary.

The release fixes the GitHub Actions `validate` job failure where the gateway
self-test used the optional `cbor2` package in CI and reported
`CBOR round-trip mismatch`, while local validation without `cbor2` used the
built-in deterministic CBOR implementation and passed.

## Changes

- Gateway CBOR encode/decode now prefers the repository's built-in
  deterministic `zmeta_cbor` implementation when it is available, with `cbor2`
  retained as a fallback.
- Compact CBOR packaging now uses the same preference order, keeping gateway
  and compact transport behavior aligned.
- Added regression tests that simulate `cbor2` being present and fail if the
  gateway or compact path stops preferring `zmeta_cbor`.
- CI now sets `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24=true` so GitHub JavaScript
  actions run under Node.js 24 ahead of the hosted runner Node.js 20 removal.

## Validation

- The failing gateway self-test now passes locally.
- Targeted gateway/encoding tests pass.
- Full adapter/gateway pytest suite passes.
- Strict example validation and conformance validation pass.
- Release checksums and detached signatures verify.

## Release Authenticity

The v1.1.3 artifacts are signed with the ZMeta release signing key:

- UID: `Incept.IO ZMeta Release Signing <justintylercarr@gmail.com>`
- Fingerprint: `A3B150AF2A0E1CA413C4B7F112BE81F54654B96E`
- Public key asset: `ZMETA_RELEASE_SIGNING_KEY_v1.1.3.asc`

Recommended verification flow:

1. Import or otherwise trust the documented public key/fingerprint.
1. Verify `SHA256SUMS_v1.1.3.txt.asc` against `SHA256SUMS_v1.1.3.txt`.
1. Verify each detached asset signature.
1. Verify release asset hashes against `SHA256SUMS_v1.1.3.txt`.

## Artifacts

- `zmeta-v1.1.3-dist.zip`
- `zmeta-edge-v1.1.3.zip`
- `zmeta-gateway-v1.1.3.zip`
- `SHA256SUMS_v1.1.3.txt`
- Detached `.asc` signatures for the checksum manifest and release assets
- `ZMETA_RELEASE_SIGNING_KEY_v1.1.3.asc`
