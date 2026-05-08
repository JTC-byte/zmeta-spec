# ZMeta Release Notes Template

Release ID: `explicit_release_input_required`

Release state: `explicit_release_input_required`

Git commit: `explicit_release_input_required`

Git tag: `explicit_release_input_required`

Release manifest hash: `explicit_release_input_required`

## Summary

Describe the release purpose, governed baseline, and intended use.

## Included Artifacts

- `release/zmeta-release-manifest.yaml`
- `release/package/zmeta-release-package.yaml`
- `release/package/ATTESTATION.yaml`
- `release/package/SHA256SUMS.txt`

## Validation Summary

List the exact validation and test commands run for the release.

## Verification

1. Verify any detached signatures published with the release.
2. Verify package checksums.
3. Validate the release manifest.
4. Validate the release package.
5. Run conformance validation when source and test dependencies are available.

## Known Open Issues

- D-003 remains roadmap-planned until future semantic branches are tracked
  separately or closed by maintainers.

## Notes

This template is an example. It does not contain real release signatures, real
signer identities, operational data, credentials, or secrets.
