# ZMeta v1.1.4 Release Notes

Release tag: `v1.1.4`

## Summary

ZMeta v1.1.4 is a release-packaging patch. It does not change the schema
contract, event vocabulary, policy hash, or runtime semantics.

Published-bundle verification of `v1.1.3` found that the edge/gateway packages
included runnable tools and tests but omitted two paths those tools/tests need:

- `conformance/`
- `release/sign_release_artifacts.py`

That meant `python gateway/src/gateway.py --profile H --self-test` and the
release-signing tests could fail when run from inside the downloaded bundle even
though the repository checkout and GitHub CI passed.

## Changes

- Edge and gateway release bundles now include `conformance/`.
- Edge and gateway release bundles now include release verification helper docs
  and `release/sign_release_artifacts.py`.
- Added regression coverage so package self-test dependencies remain part of
  future edge/gateway bundles.

## Validation

- Downloaded-package verification was rerun against rebuilt v1.1.4 artifacts.
- Edge and gateway bundle self-tests pass from inside extracted release zips.
- Edge and gateway bundle test suites pass from inside extracted release zips.
- Repository pytest, strict examples, conformance, compatibility checks,
  checksum verification, and detached signature verification pass.

## Release Authenticity

The v1.1.4 artifacts are signed with the ZMeta release signing key:

- UID: `Incept.IO ZMeta Release Signing <justintylercarr@gmail.com>`
- Fingerprint: `A3B150AF2A0E1CA413C4B7F112BE81F54654B96E`
- Public key asset: `ZMETA_RELEASE_SIGNING_KEY_v1.1.4.asc`

Recommended verification flow:

1. Import or otherwise trust the documented public key/fingerprint.
1. Verify `SHA256SUMS_v1.1.4.txt.asc` against `SHA256SUMS_v1.1.4.txt`.
1. Verify each detached asset signature.
1. Verify release asset hashes against `SHA256SUMS_v1.1.4.txt`.

## Artifacts

- `zmeta-v1.1.4-dist.zip`
- `zmeta-edge-v1.1.4.zip`
- `zmeta-gateway-v1.1.4.zip`
- `SHA256SUMS_v1.1.4.txt`
- Detached `.asc` signatures for the checksum manifest and release assets
- `ZMETA_RELEASE_SIGNING_KEY_v1.1.4.asc`
