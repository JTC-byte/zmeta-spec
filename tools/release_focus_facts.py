#!/usr/bin/env python3
"""Machine-checkable facts about what this release changed.

The v1.1.19 pre-cut review found the first content-currency guard defeated by
two one-word edits: backticking the version number satisfied "names something
this release introduced", and rewording a sentence to "Schema, policy, and
event vocabulary are unchanged" evaded a regex that only knew one phrasing.
Both rules tried to infer truth from prose, which is the wrong altitude.

Semantics-contract gate 5 already says how this goes: **structure is
authoritative, free-text is a human projection.** Semantically load-bearing
data lives in structured fields and the human sentence is RENDERED from it.
A release's governance status is load-bearing data that had been living only
in an author's paragraph.

So this module computes the facts and generates the sentence. The README must
carry that sentence **verbatim**. That is an allowlist, and the difference
matters: a blocklist of forbidden phrasings has to be re-derived every time
someone writes a new one, which is the B-01 lesson from the compact mapping.

TREE-LOCAL BY REQUIREMENT. CI checks out with `actions/checkout@v6` and no
`fetch-depth`, so tags are absent there. Anything reading `git show v1.1.18:`
would pass vacuously in CI, which is the very failure class being fixed. The
previous release's state is therefore committed, in
`release/governed-baseline.yaml`, and every check here reads only the tree.

Usage:
    python tools/release_focus_facts.py                    # print the facts
    python tools/release_focus_facts.py --write-baseline --from-manifest PATH
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "release" / "zmeta-release-manifest.yaml"
BASELINE_PATH = ROOT / "release" / "governed-baseline.yaml"

# The artifact families whose change makes a release governed rather than
# advisory. Kept as path prefixes rather than manifest group names because a
# new group must not silently escape the check by being unlisted.
GOVERNED_PREFIXES = (
    "schema/",
    "policy/",
    "spec/semantics-contract.md",
    "spec/extension-registry.yaml",
    "spec/compact-binary-mapping.md",
    "spec/protobuf-encoding.md",
    "conformance/conformance_classes.yaml",
)

# Documentation inside a governed directory is not governed data. `policy/`
# holds both the YAML that IS policy and a README that describes it.
GOVERNED_EXCEPTIONS = ("policy/README.md",)


def _hashes(manifest: dict) -> dict[str, str]:
    return {entry["path"]: entry["hash"] for entry in manifest["artifact_hashes"]}


def load_manifest(path: Path = MANIFEST_PATH) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_baseline(path: Path = BASELINE_PATH) -> dict:
    if not path.is_file():
        raise FileNotFoundError(
            f"{path} is missing. It records the published release this tree is "
            f"measured against; without it no release-content claim can be checked. "
            f"Regenerate with --write-baseline --from-manifest <previous manifest>."
        )
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def is_governed(path: str) -> bool:
    if path in GOVERNED_EXCEPTIONS:
        return False
    return any(path.startswith(prefix) for prefix in GOVERNED_PREFIXES)


def added_paths(baseline: dict, manifest: dict) -> set[str]:
    return set(_hashes(manifest)) - set(baseline["artifact_hashes"])


def changed_paths(baseline: dict, manifest: dict) -> set[str]:
    old, new = baseline["artifact_hashes"], _hashes(manifest)
    return {path for path, digest in new.items() if path in old and old[path] != digest}


def governed_changes(baseline: dict, manifest: dict) -> list[str]:
    """Governed artifact paths added or changed since the baseline release."""
    touched = added_paths(baseline, manifest) | changed_paths(baseline, manifest)
    return sorted(path for path in touched if is_governed(path))


def introduced_paths(baseline: dict, manifest: dict) -> set[str]:
    """What this release can honestly claim to have introduced or altered.

    Added artifacts if there are any, otherwise changed ones. A release-focus
    bullet must name one of these, and a version literal is not among them --
    which is the specific evasion that defeated the previous rule.
    """
    added = added_paths(baseline, manifest)
    return added or changed_paths(baseline, manifest)


def governance_sentence(baseline: dict, manifest: dict) -> str:
    """The one canonical sentence a release-facing document may carry.

    Generated, never authored. A document must contain it verbatim; any
    paraphrase is absent and therefore fails, which is the whole point.
    """
    changes = governed_changes(baseline, manifest)
    baseline_id = baseline["baseline_release_id"]
    if not changes:
        return (
            f"No governed artifact changed in this release: schema, policy data, "
            f"the semantic contract and the extension registry are byte-identical "
            f"to {baseline_id}."
        )
    return (
        f"Governed artifacts changed in this release, relative to {baseline_id}: "
        + ", ".join(changes)
        + "."
    )


def write_baseline(from_manifest: Path, path: Path = BASELINE_PATH) -> dict:
    """Snapshot a published release's artifact hashes as the new baseline.

    Run at cut time against the manifest as it stood for the PREVIOUS release.
    Generation may use git or a published asset; verification never does.
    """
    source = yaml.safe_load(from_manifest.read_text(encoding="utf-8"))
    data = {
        "baseline_release_id": source["release_id"],
        "generated_by": "tools/release_focus_facts.py --write-baseline",
        "purpose": (
            "The published release this working tree is measured against. Committed "
            "because CI checks out without tags, so a git-based comparison would "
            "pass vacuously there."
        ),
        "artifact_hashes": dict(sorted(_hashes(source).items())),
    }
    text = yaml.safe_dump(data, sort_keys=False, default_flow_style=False, width=1000)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--write-baseline", action="store_true")
    parser.add_argument("--from-manifest", type=Path)
    args = parser.parse_args(argv)

    if args.write_baseline:
        if not args.from_manifest:
            print("--write-baseline requires --from-manifest", file=sys.stderr)
            return 2
        data = write_baseline(args.from_manifest)
        print(f"baseline written: {data['baseline_release_id']} "
              f"artifacts={len(data['artifact_hashes'])}")
        return 0

    baseline, manifest = load_baseline(), load_manifest()
    print(f"baseline        : {baseline['baseline_release_id']}")
    print(f"current         : {manifest['release_id']}")
    print(f"added           : {len(added_paths(baseline, manifest))}")
    print(f"changed         : {len(changed_paths(baseline, manifest))}")
    print(f"governed changes: {governed_changes(baseline, manifest) or 'none'}")
    print(f"sentence        : {governance_sentence(baseline, manifest)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
