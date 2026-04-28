# Release Artifacts

Build release artifacts from the repo root:

```powershell
python release/build_mvp_packages.py
python release/build_release_bundle.py
python release/sign_release_artifacts.py --version v1.1.2 --write-checksums --verify-checksums
```

Create detached PGP signatures for the checksum manifest and every release
asset:

```powershell
python release/sign_release_artifacts.py --version v1.1.2 --sign --target all --gpg-key-id <fingerprint>
```

Verify before upload:

```powershell
python release/sign_release_artifacts.py --version v1.1.2 --verify-checksums --verify-signatures --target all
```

Dry-run the signing commands when GPG is not available on the current machine:

```powershell
python release/sign_release_artifacts.py --version v1.1.2 --sign --target all --dry-run
```

Upload the release zips, `SHA256SUMS_<version>.txt`, and all `.asc` detached
signatures to the GitHub Release. Publish the signing key fingerprint, or the
Sigstore identity if a deployment uses Sigstore/cosign instead of detached PGP,
in the release notes or another stable channel.

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
