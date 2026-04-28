# Release Checklist

Use this as the template for each release.

- [ ] Semantic contract finalized for target version
- [ ] Contract hash recomputed
- [ ] Schema validates against examples
- [ ] Policy pack validation run locally
- [ ] Examples and conformance corpus validate locally
- [ ] Gateway self-test passes locally
- [ ] Adapter and gateway pytest suite passes locally
- [ ] Profile L packet-size check passes locally
- [ ] Reference distribution bundle built
- [ ] Edge deployment bundle built
- [ ] Gateway deployment bundle built
- [ ] Release notes updated
- [ ] Changelog updated
- [ ] SHA256SUMS generated for release assets
- [ ] SHA256SUMS verified
- [ ] Detached signatures generated for SHA256SUMS and release assets
- [ ] Detached signatures verified
- [ ] Signing key fingerprint or Sigstore identity documented in release notes
- [ ] GitHub Release body includes checksum/signature verification instructions
- [ ] GitHub CI passes for the release commit
- [ ] Gateway Docker build + run verified
- [ ] Tag created
- [ ] GitHub Release created with zips, SHA256SUMS, and signatures
