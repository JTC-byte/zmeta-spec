# Release Artifacts

Before preparing release artifacts, follow the repository change-governance
process in `AGENTS.md` and `docs/zmeta_change_governance.md`. Release
publication requires an explicit release-authority decision for tags, uploads,
and detached signatures.

For industry sharing, cite a tagged release, the release notes, validation
report, release manifest hash, conformance evidence, and
`docs/zmeta_defensive_publication.md`. `IP_POLICY.md`, `CONTRIBUTING.md`,
`CONFORMANCE.md`, and `TRADEMARK.md` define the advisory contribution,
compatibility, private-dialect, and name-use posture for the public baseline.

Current formal release: `v1.1.19`. `RELEASE_CHECKLIST.md` is the authoritative
release procedure; the commands below describe artifact building generically.

Build release artifacts from the repo root (substitute the release version for
`<version>`, e.g. `v1.1.19`):

```powershell
python tools/build_release_manifest.py --output release/zmeta-release-manifest.yaml
python tools/validate_release_manifest.py --manifest release/zmeta-release-manifest.yaml
python release/build_mvp_packages.py --version <version>
python release/build_release_bundle.py --version <version-number>
python tools/build_release_package.py --manifest release/zmeta-release-manifest.yaml --output-dir release/package-<version> --release-id zmeta-<version> --release-state formal_release --no-signatures --release-notes release/RELEASE_NOTES_<version>.md
python tools/validate_release_package.py --manifest release/zmeta-release-manifest.yaml --package-dir release/package-<version>
python release/sign_release_artifacts.py --version <version> --write-checksums --verify-checksums
```

The `zmeta-release-package-<version>.zip` asset is built automatically from
`release/package-<version>` by `sign_release_artifacts.py --write-checksums`
when it is missing — never assemble it by hand.

The release package builder defaults to no-signature mode. It does not create a
git tag, call GPG/cosign/minisign, or generate detached signatures unless a
release authority performs signing outside the repository process.

Create detached PGP signatures for the checksum manifest and every release
asset:

```powershell
python release/sign_release_artifacts.py --version <version> --sign --target all --gpg-key-id <fingerprint>
```

Verify before upload:

```powershell
python release/sign_release_artifacts.py --version <version> --verify-checksums --verify-signatures --target all
```

Dry-run the signing commands when GPG is not available on the current machine:

```powershell
python release/sign_release_artifacts.py --version <version> --sign --target all --dry-run
```

Upload the release zips, `zmeta-release-manifest.yaml`, the release package
zip, `SHA256SUMS_<version>.txt`, release notes, validation report, and any
`.asc` detached signatures to the GitHub Release. Publish the signing key
fingerprint, or the Sigstore identity if a deployment uses Sigstore/cosign
instead of detached PGP, in the release notes or another stable channel.

`SHA256SUMS_<version>.txt` verifies artifact integrity. Detached signatures
authenticate who produced the manifest/assets.

Recommended GitHub release verification text:

```text
1. Import or otherwise trust the documented release signing key/fingerprint.
2. Verify the checksum manifest signature:
   gpg --verify SHA256SUMS_<version>.txt.asc SHA256SUMS_<version>.txt
3. Verify each release asset signature:
   gpg --verify <asset>.asc <asset>
4. Verify asset hashes against the manifest:
   python release/sign_release_artifacts.py --version <version> --verify-checksums
```

The release is not authenticity-complete until the `.asc` files, signing
fingerprint or Sigstore identity, and verification instructions are published
with the assets.

Do not commit private keys, credentials, tokens, certificates with private
material, or signing secrets.
