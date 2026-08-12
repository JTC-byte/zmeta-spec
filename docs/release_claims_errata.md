# Release Claims Errata

Docs/advisory. Non-normative. Records a defect in the example conformance
claims shipped with v1.1.22: their `release_hashes` blocks disagree with
the release manifest published beside them.

## The defect

`tools/build_release_manifest.py` refreshes the two example conformance
claims (`conformance/claims/example-core-producer.yaml` and
`conformance/claims/example-reference-gateway.yaml`) only when invoked
with `--update-claims`. The v1.1.22 release sequence rebuilt the manifest
without refreshing the claims, so both files carry `release_hashes`
entries computed against an earlier tree state. Two of the thirteen
entries in each file disagree with the manifest at the published tag:
`adapter_conformance_hash` and `process_governance_hash`. v1.1.21 has no
divergence; the drift entered at the first v1.1.22 cut commit (`f0f5134`)
and persisted through the tag.

## Impact

- The example claims are reference documents for claim authors. A reader
  copying a v1.1.22 example's `release_hashes` block inherits two wrong
  hashes.
- Validation is unaffected. The kernel gate pins the claim files by hash,
  which certifies that their bytes are intact; it cannot certify that
  their contents are current, and nothing in the repository reads
  `release_hashes` back against the manifest, which is why no gate caught
  the drift.
- Every published v1.1.22 bundle ships the stale claims beside the current
  manifest.

## Affected values

Both claim files carry the same two stale entries at tag `v1.1.22`:

| File | Key | Value in the claim (stale) | Value in the manifest at the same tag |
|---|---|---|---|
| example-core-producer.yaml | adapter_conformance_hash | `sha256:d97db4ca864fce4a9f4546175c93f40947083c77d5e19ef1357e285d7bdd181c` | `sha256:b1c8ff49878facbd699a5ab323c3ab3bbadfbf4a3fafc606816240b191191a97` |
| example-core-producer.yaml | process_governance_hash | `sha256:1198e125cef662bcf16d03c464fa3f0dd10b908eeec5c2a2e9a6325a39eb0202` | `sha256:a87cca88fd9fb9adb3883b1ec68fb55400f91c0aa43b07ddfbcbe30af3115911` |
| example-reference-gateway.yaml | adapter_conformance_hash | `sha256:d97db4ca864fce4a9f4546175c93f40947083c77d5e19ef1357e285d7bdd181c` | `sha256:b1c8ff49878facbd699a5ab323c3ab3bbadfbf4a3fafc606816240b191191a97` |
| example-reference-gateway.yaml | process_governance_hash | `sha256:1198e125cef662bcf16d03c464fa3f0dd10b908eeec5c2a2e9a6325a39eb0202` | `sha256:a87cca88fd9fb9adb3883b1ec68fb55400f91c0aa43b07ddfbcbe30af3115911` |

The manifest's values are authoritative at the tag. The manifest is
rebuilt and validated at every cut, while the claims are refreshed only by
`--update-claims`.

## What stays, what changes

- Published release assets are never rewritten. AGENTS.md's release limits
  resolve a divergence with a new release cut, not a retroactive edit, so
  the v1.1.22 bundles stay exactly as published and this document is the
  correction of record.
- The claim files are corrected at source in the next release cut, and
  `RELEASE_CHECKLIST.md` now names `--update-claims` as an explicit step.
- A machine check that reads `release_hashes` back against the manifest is
  queued; until it lands, the checklist step is the only control.

## How this was found

During the review of an external contribution against v1.1.22 (PR #8),
whose manifest regeneration silently repaired the drift in its own tree;
the repair made the pre-existing defect visible. An earlier audit had
refuted this exact finding class on grounds that did not hold; the dated
correction sits on that refutation in `docs/r1_11_full_stack_audit.md`,
and the tension is logged as X2-01 in `docs/zmeta_doctrine_review_log.md`.

## Reproduction

Every value in the table above was generated, not hand-written, by the
script below, run from the repository root with the v1.1.21 and v1.1.22
tags fetched:

```python
"""Compare example-claim release_hashes against the manifest at a tag.

For each ref, reads the git-committed content of the release manifest and
both example conformance claims, extracts every 'sha256:'-prefixed hash
entry, and prints a Markdown table row for every claim entry that
disagrees with the manifest value under the same key. Divergence is
discovered by the comparison, not assumed.

Run from the repo root:
    python compare_claim_hashes.py
"""
from __future__ import annotations

import re
import subprocess

REFS = ["v1.1.21", "v1.1.22"]
CLAIMS = [
    "conformance/claims/example-core-producer.yaml",
    "conformance/claims/example-reference-gateway.yaml",
]
MANIFEST = "release/zmeta-release-manifest.yaml"


def show(ref: str, path: str) -> str | None:
    result = subprocess.run(
        ["git", "show", f"{ref}:{path}"], capture_output=True, check=False
    )
    return result.stdout.decode("utf-8", "replace") if result.returncode == 0 else None


def hashes(text: str | None) -> dict[str, str]:
    out: dict[str, str] = {}
    for match in re.finditer(
        r"^\s*([a-z_]*hash):\s*sha256:([0-9a-f]{64})", text or "", re.M
    ):
        out.setdefault(match.group(1), match.group(2))
    return out


def main() -> None:
    print("| Ref | File | Key | Value in the claim | Value in the manifest |")
    print("|---|---|---|---|---|")
    for ref in REFS:
        manifest = hashes(show(ref, MANIFEST))
        checked = 0
        divergent = 0
        for path in CLAIMS:
            claim = hashes(show(ref, path))
            for key in sorted(claim):
                if key not in manifest:
                    continue
                checked += 1
                if claim[key] != manifest[key]:
                    divergent += 1
                    print(
                        f"| {ref} | {path.split('/')[-1]} | {key} | "
                        f"`sha256:{claim[key]}` | `sha256:{manifest[key]}` |"
                    )
        print(f"\n{ref}: {divergent} divergent of {checked} claim hash entries checked\n")


if __name__ == "__main__":
    main()
```

Running it against this repository prints the four rows above for
v1.1.22 and zero rows for v1.1.21, with:

```text
v1.1.21: 0 divergent of 26 claim hash entries checked
v1.1.22: 4 divergent of 26 claim hash entries checked
```
