# Release Checklist

Use this as the template for each release.

- [ ] Semantic contract finalized for target version
- [ ] Contract hash recomputed
- [ ] Release manifest built and validated
- [ ] Release package templates or generated package output validated
- [ ] Schema validates against examples
- [ ] Policy pack validation run locally
- [ ] Examples and conformance corpus validate locally
- [ ] Full kernel-protection conformance passes:
      `python tools/validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative --precision-policy --release-manifest --release-package --bad-events --adapter-harness`
- [ ] Gateway self-test passes locally
- [ ] Adapter and gateway pytest suite passes locally
- [ ] Profile L packet-size check passes locally
- [ ] Reference distribution bundle built
- [ ] Edge deployment bundle built
- [ ] Gateway deployment bundle built
- [ ] Formal release package metadata built in no-signature mode
- [ ] No private keys, credentials, tokens, or signing secrets are present in release package paths
- [ ] Release notes updated
- [ ] Changelog updated
- [ ] SHA256SUMS generated for release assets
- [ ] SHA256SUMS verified
- [ ] Detached signatures generated for SHA256SUMS and release assets
- [ ] Detached signatures verified
- [ ] Signing key fingerprint or Sigstore identity documented in release notes
- [ ] Release manifest and release package artifact attached or otherwise published
- [ ] GitHub Release body includes checksum/signature verification instructions
- [ ] GitHub CI passes for the release commit
- [ ] Gateway Docker build + run verified
- [ ] Tag created
- [ ] GitHub Release created with zips, SHA256SUMS, and signatures
