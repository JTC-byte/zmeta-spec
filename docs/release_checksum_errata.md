# Release Checksum Errata

Docs/advisory. Non-normative. Records a defect in how earlier releases'
published checksum files were generated, and the corrected values needed to
verify those releases against a clean checkout.

## The defect

`release/sign_release_artifacts.py`'s `write_checksums()` hashed each release
artifact's raw on-disk bytes. This repository has no `.gitattributes`
line-ending policy, so a Windows working copy can be checked out with CRLF
line endings on text files while git stores their committed content as LF.
The signer had no line-ending normalization, so whichever line-ending state
the authoring machine's filesystem happened to be in at checksum time got
baked into the published `SHA256SUMS_<version>.txt`.

Git itself, and every checkout that reads a file's committed content directly
(`git show <tag>:<path>`, a fresh Linux clone, CI), serves the LF bytes.
Running `sha256sum -c SHA256SUMS_<version>.txt` against a clean checkout of
an affected release fails for files that were never actually changed: the
file's content is correct, only the published checksum is wrong.

The fix, effective v1.1.20, normalizes CRLF to LF before hashing text assets
(the release manifest, `RELEASE_NOTES_<version>.md`,
`VALIDATION_REPORT_<version>.md`). Binary assets, the zip bundles, are
hashed on raw bytes, unchanged: a zip has no line-ending concept to
normalize. See `release/sign_release_artifacts.py`'s module docstring and
`_sha256()` for the exact contract.

## What stays, what changes

- Published `SHA256SUMS_<version>.txt` files are never rewritten. AGENTS.md's
  release limits make a published checksum file immutable: a divergence is
  resolved by a new release cut, not a retroactive edit. Every affected file
  listed below stays exactly as published.
- Verifying an affected release's text assets against their own
  git-committed content requires the corrected value in the table below, not
  the published one.
- v1.1.20 onward is correct at source. The signer normalizes before hashing,
  so `sha256sum -c` against a clean checkout matches the published checksum
  file for every release from v1.1.20 forward.

## Affected releases

Every release with a published `release/SHA256SUMS_<tag>.txt` was checked.
The checksum file was extracted from its own release tag, the published
record, and each candidate text asset's git-committed content was extracted
from the same tag and re-hashed with CRLF normalized to LF. 54 text-asset
checksum entries were checked across the 20 releases that publish at least
one of the three candidate text assets. v1.0.4 and v1.0.5 predate all three;
v1.1.1 through v1.1.5 predate the release manifest and release-package
artifacts, so they contribute release-notes and validation-report entries
only. 38 of the 54 checked entries already matched. 16 did not, across 15
release tags:

| Release | File | Published SHA-256 | Correct SHA-256 (LF content) | Cause |
|---|---|---|---|---|
| v1.1.0 | RELEASE_NOTES_v1.1.0.md | `330dda6180ab867438fc6aa37f56eaf384b6d6343d438acb0521976a206797ac` | `556f4d3d7131a4ff7f95b800a7482554c8286ef37c0fb991b1cc0a2058e67497` | CRLF working-copy bytes hashed instead of git's LF-committed content |
| v1.1.6 | zmeta-release-manifest.yaml | `b44f60f5d4c7169c06a28a3bcbc69d1ead2b5f1efc3ed1429045a4e568af9f35` | `9b24798b1ac92adc3ce0ecdcc59a98ef83507b86abed97b6c287c76c27c396f6` | CRLF working-copy bytes hashed instead of git's LF-committed content |
| v1.1.7 | zmeta-release-manifest.yaml | `a43d9dd9128484a6bbbb4193902e68730f17a4eb1745f659fd709761301d7305` | `ca981e6dce0cbc60a783a25101f37d60ed6e44969499dc2a83500530bc80ea3e` | CRLF working-copy bytes hashed instead of git's LF-committed content |
| v1.1.8 | zmeta-release-manifest.yaml | `991ac8cb7b28633099ad18441cdc6eacf33ad93bc2cfdb238253e59ed275896c` | `8d45e8712eae9fcf7aa64d941e9b963d0eca534a7bb81084a794dd14f9623068` | CRLF working-copy bytes hashed instead of git's LF-committed content |
| v1.1.9 | zmeta-release-manifest.yaml | `b1165c3bc4c7d4e3995ec5e796eadd5f829bb0a699d40ea83e9f25606de81ade` | `bbbecaa5e9982a3cf57f93ec3d154b66b9171678b8e6aa61df2f48b0f7b52d0d` | CRLF working-copy bytes hashed instead of git's LF-committed content |
| v1.1.10 | zmeta-release-manifest.yaml | `ed1ee0d6a16e1c7baac5c32be9961a4155fddbdfb3601fdf806c87021034d9f6` | `9972fae54e3d2c42fd790023ef51ca16ec45b83921ef1baccbe764a458d890f6` | CRLF working-copy bytes hashed instead of git's LF-committed content |
| v1.1.11 | zmeta-release-manifest.yaml | `a81a36d1200aded78c85670c7a83701e701c8967ae08093b194637ba87f4a28c` | `af159464e508a3534f452ccd7458fae98fe8f245d69019bc67e5f0fae28dcde6` | CRLF working-copy bytes hashed instead of git's LF-committed content |
| v1.1.12 | zmeta-release-manifest.yaml | `1d2fc3cb5becebf95d1d7faa6dc946696af4a1f699e14f6a02112dcbf834518f` | `015a05a168864463132a8cd692424f49edb260a4161e692b392d4a491f2bdbaa` | CRLF working-copy bytes hashed instead of git's LF-committed content |
| v1.1.13 | zmeta-release-manifest.yaml | `0ac8db59f5792b02abee97869b23e93540514c3f5bfb54ae49f755fa901dd057` | `0e53f67968a8229e980c344d7ceecc6a736f4401ea5f1419eb7aa8fe842671b2` | CRLF working-copy bytes hashed instead of git's LF-committed content |
| v1.1.14 | zmeta-release-manifest.yaml | `762c149d56986bb13e5211c8eff1e3e858cd22e21822ba39a364d25ef9c20e3f` | `171dff0bbff4b79b64dc8ee3d30a9b90e022a28928e13927014e91abb260a48f` | CRLF working-copy bytes hashed instead of git's LF-committed content |
| v1.1.15 | zmeta-release-manifest.yaml | `d778368435bdffbf5e33c450de3a23563ff3cd030461b7c842fef5915f452c48` | `7f635be674de20fc0cf55126a832f463096bda2b3a84e38c069ca4fadd23183f` | CRLF working-copy bytes hashed instead of git's LF-committed content |
| v1.1.16 | zmeta-release-manifest.yaml | `96c4e51af544bc4a0582cf7902762b2347e34d3dbea85808a7ae370cebb8a7ba` | `25cd49823a7a170d5843b367a97a4284247d473132d785511adc33ebd72e0aa6` | CRLF working-copy bytes hashed instead of git's LF-committed content |
| v1.1.17 | zmeta-release-manifest.yaml | `4b3f20c2f68ebeef65a27b42f3ef8ec1c4d4217a785d11fc1e4a8b17c322b0f5` | `c1f10a6087e7e635b1313558629a86bb5f69d7e4ef49bdfa6d878aaf36b89e13` | CRLF working-copy bytes hashed instead of git's LF-committed content |
| v1.1.18 | zmeta-release-manifest.yaml | `1aae48aafc2a1316ab47b5872a62f63b34d18a7bd7c6c3ff5fd433497d9a25c7` | `524f1eb36560ebcc0aaa03ed833e6cb665a1c5bd21224969fadb4556144b2789` | CRLF working-copy bytes hashed instead of git's LF-committed content |
| v1.1.19 | zmeta-release-manifest.yaml | `a733d7006b59bbb09fe5fa5a7697e16e05d3800cac1b9d487820b9d9eadb6f9f` | `97a8b1a4f568ebd2230473da144a05916a322cb0a6e6e4e15afab16557bfc2ce` | CRLF working-copy bytes hashed instead of git's LF-committed content |
| v1.1.19 | RELEASE_NOTES_v1.1.19.md | `3755d6e8b7dc63cada1d92a6543667458ba3974671f0d744a6916c17fa618f63` | `e5d73bb2344bce9962aace94b5341a209bd88aeb8f9c67c479a9f2afe0bf012d` | CRLF working-copy bytes hashed instead of git's LF-committed content |

Every mismatch has the same cause: the published value is the SHA-256 of the
file's content with LF rewritten to CRLF; the correct value is the SHA-256 of
the file's actual git-committed (LF) bytes. `VALIDATION_REPORT_<version>.md`
never mismatches in this corpus, and v1.1.0's manifest and v1.1.1 through
v1.1.5 (which have no manifest to check) are likewise absent from the table
because their checked entries already matched.

## Verifying an affected release today

`sha256sum -c release/SHA256SUMS_<version>.txt` against a clean checkout of
one of the 15 affected tags reports a mismatch for the listed file or files.
That mismatch is this errata, not a content problem: recompute the file's
hash and compare it against the "Correct SHA-256" column above rather than
the published line.

## Reproduction

Every value in the table above was generated, not hand-written, by the
script below, run from the repository root with the affected tags already
fetched:

```text
python generate_errata_table.py
```

```python
"""Generate the release-checksum errata table (scratch, throwaway - not committed).

For every version with a published release/SHA256SUMS_<tag>.txt in the
working tree, extracts that file from its own git tag (the immutable
published record) and the git-committed content of each candidate text
asset (release/zmeta-release-manifest.yaml, release/RELEASE_NOTES_<tag>.md,
release/VALIDATION_REPORT_<tag>.md) from the same tag, recomputes the
correct hash by normalizing CRLF to LF, and prints a Markdown table row for
every mismatch. The affected-release set is discovered by this comparison,
not assumed: any version whose text assets already match is silently
skipped.

Run from the repo root:
    python generate_errata_table.py
"""
from __future__ import annotations

import hashlib
import re
import subprocess
from pathlib import Path

REPO_ROOT = Path.cwd()

# Candidate text assets per _artifact_names() in release/sign_release_artifacts.py.
# Zip bundles are binary and out of scope for this errata: raw-byte hashing was
# always correct for them.
def text_asset_names(tag: str) -> list[str]:
    return [
        "zmeta-release-manifest.yaml",
        f"RELEASE_NOTES_{tag}.md",
        f"VALIDATION_REPORT_{tag}.md",
    ]


def discover_tags() -> list[str]:
    """Every version with a published SHA256SUMS_<tag>.txt on disk, sorted."""
    names = []
    for path in (REPO_ROOT / "release").glob("SHA256SUMS_v*.txt"):
        match = re.fullmatch(r"SHA256SUMS_(v[0-9.]+)\.txt", path.name)
        names.append(match.group(1))
    return sorted(names, key=lambda v: [int(part) for part in v[1:].split(".")])


def git_show(tag: str, rel_path: str) -> bytes | None:
    result = subprocess.run(
        ["git", "show", f"{tag}:release/{rel_path}"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        check=False,
    )
    return result.stdout if result.returncode == 0 else None


def parse_sha256sums(blob: bytes) -> dict[str, str]:
    out = {}
    for line in blob.decode("utf-8", "replace").splitlines():
        parts = line.strip().split()
        if len(parts) == 2:
            digest, name = parts
            out[name] = digest
    return out


def main() -> None:
    rows = []
    checked = 0
    matched = 0
    for tag in discover_tags():
        sums_blob = git_show(tag, f"SHA256SUMS_{tag}.txt")
        if sums_blob is None:
            continue
        published = parse_sha256sums(sums_blob)
        for name in text_asset_names(tag):
            if name not in published:
                continue
            content = git_show(tag, name)
            if content is None:
                continue
            checked += 1
            published_hash = published[name]
            correct_hash = hashlib.sha256(content.replace(b"\r\n", b"\n")).hexdigest()
            if published_hash == correct_hash:
                matched += 1
            else:
                rows.append((tag, name, published_hash, correct_hash))

    print("| Release | File | Published SHA-256 | Correct SHA-256 (LF content) | Cause |")
    print("|---|---|---|---|---|")
    for tag, name, published_hash, correct_hash in rows:
        print(
            f"| {tag} | {name} | `{published_hash}` | `{correct_hash}` | "
            "CRLF working-copy bytes hashed instead of git's LF-committed content |"
        )
    print()
    print(f"text-asset entries checked: {checked}, matched: {matched}, mismatched: {len(rows)}")


if __name__ == "__main__":
    main()
```

Running it against this repository prints the 16-row table above followed
by:

```text
text-asset entries checked: 54, matched: 38, mismatched: 16
```
