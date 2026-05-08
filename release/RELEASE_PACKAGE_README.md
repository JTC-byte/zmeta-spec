# ZMeta Release Package Template

This directory-level template describes the files produced by
`tools/build_release_package.py` when a release package is built.

Default package build mode is no-signature. The builder does not create git
tags, invoke signing tools, or generate detached signatures unless a future
approved release process adds that behavior explicitly.

Expected generated package files:

- `zmeta-release-package.yaml`: package metadata.
- `RELEASE_NOTES.md`: release notes copied from the template or supplied file.
- `ATTESTATION.yaml`: attestation populated from the release manifest.
- `SHA256SUMS.txt`: SHA-256 checksums for generated package artifacts.

Validate templates only:

```powershell
python tools/validate_release_package.py --manifest release/zmeta-release-manifest.yaml --templates-only
```

Dry-run a package build:

```powershell
python tools/build_release_package.py --manifest release/zmeta-release-manifest.yaml --output-dir release/package --dry-run --no-signatures
```

Validate generated package output:

```powershell
python tools/validate_release_package.py --manifest release/zmeta-release-manifest.yaml --package-dir release/package
```

The release package wraps the governed release manifest. It does not change
ZMeta schemas, semantics, validation behavior, extension registry status, or
event vocabulary.
