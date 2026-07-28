#!/usr/bin/env python3
"""Machine-checkable facts about what this release changed.

The v1.1.19 pre-cut review found the first content-currency guard defeated by
two one-word edits: backticking the version number satisfied "names something
this release introduced", and rewording a sentence to "Schema, policy, and
event vocabulary are unchanged" evaded a regex that only knew one phrasing.
Both rules tried to infer truth from prose, which is the wrong altitude.

Design gate 5 (`CLAUDE.md`, advisory) already says how this goes: **structure
is authoritative, free-text is a human projection.** Note the citation: the
design gates live in CLAUDE.md, which is advisory and non-normative. The
semantics contract defines no numbered gates, and citing it as though it did
is the exact defect this release's errata is about. Semantically load-bearing
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

# WHICH GROUPS ARE GOVERNED, taken from the manifest's own group names rather
# than guessed from path prefixes.
#
# The first version of this hand-listed path prefixes, and the second panel
# found it narrower than the manifest's own definition: `configs/policy-variants/
# *.yaml` feed `policy_bundle_hash` while the prefix list called them ungoverned,
# and `zmeta_compact.py` sits in `encoding_projection_specs` beside the two
# encoding specs that WERE governed -- so the codec could change wire behaviour
# while the sentence reported clean. The comment on that list claimed prefixes
# were used so a new group could not escape by being unlisted. It achieved the
# opposite. Classifying by group name, with a completeness assertion below,
# actually delivers what that comment promised.
GOVERNED_GROUPS = frozenset({
    "semantic_contract",
    "schema_bundle",
    "policy_bundle",
    "extension_registry",
    "conformance_classes",
    "encoding_projection_specs",
    "core_conformance",
    "bad_event_corpus",
    "adapter_conformance",
    "encoding_negative",
    "profile_projection",
    "profile_precision",
})

# Explicitly NOT governed, each for a stated reason. Listed rather than
# defaulted so that a NEW group is in neither set and fails loudly.
UNGOVERNED_GROUPS = frozenset({
    "process_governance",    # how we work, not what conforms
    "release_policy",        # release mechanics
    "release_packaging",     # release mechanics
    "release_tools",         # tooling source
    "conformance_tools",     # tooling source
    "claims",                # example claims, regenerated every cut
    "policy_json_export",    # DERIVED from policy_bundle; never a source of truth
    "future_branch_roadmap", # future-only; not valid current vocabulary
})


def governed_paths(manifest: dict) -> set[str]:
    """Every artifact path belonging to a governed group.

    Raises if a group is classified in neither set: an unclassified group must
    not default to ungoverned, because defaulting to ungoverned is how a
    governed change gets reported clean.
    """
    groups = manifest["artifact_groups"]
    unclassified = sorted(set(groups) - GOVERNED_GROUPS - UNGOVERNED_GROUPS)
    if unclassified:
        raise ValueError(
            f"artifact groups are classified as neither governed nor ungoverned: "
            f"{unclassified}. Add each to GOVERNED_GROUPS or UNGOVERNED_GROUPS in "
            f"tools/release_focus_facts.py with a reason; leaving a group "
            f"unclassified would let a governed change report clean."
        )
    return {
        path
        for name in GOVERNED_GROUPS
        if name in groups
        for path in groups[name]["paths"]
    }


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


def added_paths(baseline: dict, manifest: dict) -> set[str]:
    return set(_hashes(manifest)) - set(baseline["artifact_hashes"])


def changed_paths(baseline: dict, manifest: dict) -> set[str]:
    old, new = baseline["artifact_hashes"], _hashes(manifest)
    return {path for path, digest in new.items() if path in old and old[path] != digest}


def removed_paths(baseline: dict, manifest: dict) -> set[str]:
    """Artifacts present at the baseline and absent now.

    The first version could not see these at all: `added` was new-minus-old and
    `changed` iterated the new set, so a DELETED governed artifact produced
    "No governed artifact changed."
    """
    return set(baseline["artifact_hashes"]) - set(_hashes(manifest))


def governed_changes(baseline: dict, manifest: dict) -> list[str]:
    """Governed artifact paths added, changed, or removed since the baseline.

    Removal is judged against the BASELINE's classification, since a path that
    no longer exists has no current group.
    """
    governed_now = governed_paths(manifest)
    touched = {
        path
        for path in added_paths(baseline, manifest) | changed_paths(baseline, manifest)
        if path in governed_now
    }
    baseline_governed_prefixes = ("schema/", "policy/", "spec/", "conformance/")
    touched |= {
        path
        for path in removed_paths(baseline, manifest)
        if path.startswith(baseline_governed_prefixes)
    }
    return sorted(touched)


def expected_baseline_release(root: Path = ROOT) -> str | None:
    """The release the baseline SHOULD name: the newest published one before current.

    Derived from the release-notes files present in the tree, so it is
    tree-local like everything else here. Without this the baseline could sit
    two releases stale and every check would still pass -- which is how the
    whole v1.1.19 bullet would have survived the next cut unedited, the very
    defect class this module exists for, one release later.
    """
    import re

    current = load_manifest(root / "release" / "zmeta-release-manifest.yaml")["release_id"]
    current_v = current.removeprefix("zmeta-")

    def key(tag: str) -> tuple[int, ...]:
        return tuple(int(part) for part in tag.lstrip("v").split("."))

    published = []
    for path in (root / "release").glob("RELEASE_NOTES_v*.md"):
        match = re.search(r"RELEASE_NOTES_(v\d+\.\d+\.\d+)\.md", path.name)
        if match and key(match.group(1)) < key(current_v):
            published.append(match.group(1))
    if not published:
        return None
    return "zmeta-" + max(published, key=key)


def governance_sentence(baseline: dict, manifest: dict) -> str:
    """The one canonical sentence a release-facing document may carry.

    Generated, never authored. A document must contain it verbatim; any
    paraphrase is absent and therefore fails, which is the whole point.
    """
    changes = governed_changes(baseline, manifest)
    baseline_id = baseline["baseline_release_id"]
    if not changes:
        return (
            f"No governed artifact changed in this release: the semantic contract, "
            f"the schemas, policy data, the extension registry, the conformance "
            f"corpora and the encoding projections are byte-identical to "
            f"{baseline_id}."
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
