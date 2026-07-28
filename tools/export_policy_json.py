#!/usr/bin/env python3
"""Emit the governed policy YAML as a verbatim JSON projection.

ZMeta's governed policy ships as `policy/*.yaml`. A consumer that cannot read
YAML -- a Cloudflare Worker, a browser client, anything outside the Python
stack -- has had two options: vendor a YAML parser alongside the raw files, or
hand-copy the parts it needs into its own source. Hand-copying is what
actually happens. P2-01 surfaced a fielded consumer mirroring the semantics
contract 7.7 STATE denylist in TypeScript and re-verifying that alignment BY
HAND at every pin advance. A hand-copy of governed data is a private dialect
forming around the honesty primitives, and the burden grows with every
consumer.

This projection removes the reason to copy. It is:

- DERIVED. `policy/*.yaml` is the source of truth. This output is regenerated
  from it and is never edited by hand.
- VERBATIM. The JSON carries the YAML's data model unchanged -- nothing
  renamed, filtered, flattened, merged, or interpreted. `yaml.safe_load` of
  the source and `json.load` of the export compare equal, and a test pins
  that per file.
- ONE-DIRECTIONAL IN AUTHORITY, per semantics-contract gate 4. Authority runs
  YAML -> JSON and never back. A JSON file edited by hand is not policy; it
  is a stale file, and the freshness pin fails on it.

Deliberately NOT a curated bundle. Merging the schema's controlled
vocabularies in alongside the policy data would mean deciding what a consumer
needs, which is a judgement, which is a second source of truth that can drift
from both parents. One file per governed policy file, same name, same data.

Output is deterministic: sorted keys, two-space indent, LF newlines, UTF-8,
trailing newline. The LF normalization matters -- this repo has twice shipped
a hash pin that held on one platform and failed on the other.

Usage:
    python tools/export_policy_json.py            # regenerate
    python tools/export_policy_json.py --check    # verify, exit 1 if stale
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SOURCE_GLOB = "policy/*.yaml"
EXPORT_DIR = "export/policy"
INDEX_NAME = "index.json"
GENERATOR = "tools/export_policy_json.py"


def _canonical_sha256(path: Path) -> str:
    """LF-normalized SHA-256, matching tools/build_release_manifest.py.

    Deliberately duplicated rather than imported: tools/ is not a package and
    a path-manipulating import is a fragility this file does not need. The
    agreement is pinned instead -- gateway/tests/test_policy_json_export.py
    asserts these values equal build_release_manifest.file_hash, so the two
    cannot drift silently.
    """
    text = path.read_bytes().decode("utf-8")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def policy_sources(root: Path = ROOT) -> list[Path]:
    """Every governed policy YAML file, sorted by repo-relative path."""
    return sorted(
        (path for path in root.glob(SOURCE_GLOB) if path.is_file()),
        key=lambda item: item.relative_to(root).as_posix(),
    )


def export_relpath(source: Path, root: Path = ROOT) -> str:
    return f"{EXPORT_DIR}/{source.stem}.json"


def render_json(data: object) -> str:
    """Deterministic JSON text: sorted keys, 2-space indent, trailing LF."""
    return json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def build_exports(root: Path = ROOT) -> dict[str, str]:
    """Every generated file as {repo_relative_path: text}, index included."""
    sources = policy_sources(root)
    if not sources:
        raise FileNotFoundError(f"no policy sources matched {SOURCE_GLOB}")

    outputs: dict[str, str] = {}
    entries: list[dict[str, str]] = []
    for source in sources:
        source_rel = source.relative_to(root).as_posix()
        target_rel = export_relpath(source, root)
        data = yaml.safe_load(source.read_text(encoding="utf-8"))
        outputs[target_rel] = render_json(data)
        entries.append(
            {
                "export": target_rel,
                "source": source_rel,
                "source_sha256": _canonical_sha256(source),
            }
        )

    index = {
        "authority": (
            "policy/*.yaml is the source of truth. This directory is a derived, "
            "verbatim JSON projection of it and is never edited by hand."
        ),
        "generated_by": GENERATOR,
        "canonicalization": "sorted keys, 2-space indent, LF newlines, UTF-8, trailing newline",
        "source_hash_canonicalization": "text_lf, matching release manifest file hashes",
        "regenerate": "python tools/export_policy_json.py",
        "verify": "python tools/export_policy_json.py --check",
        "sources": entries,
    }
    outputs[f"{EXPORT_DIR}/{INDEX_NAME}"] = render_json(index)
    return outputs


def _read_lf(path: Path) -> str | None:
    if not path.is_file():
        return None
    text = path.read_bytes().decode("utf-8")
    return text.replace("\r\n", "\n").replace("\r", "\n")


def stale_exports(root: Path = ROOT) -> list[str]:
    """Generated paths whose committed content does not match a fresh build.

    Compares LF-normalized, so a CRLF working copy on Windows is not reported
    as drift. Missing files and orphans both count as stale.
    """
    expected = build_exports(root)
    stale = [rel for rel, text in expected.items() if _read_lf(root / rel) != text]

    export_root = root / EXPORT_DIR
    if export_root.is_dir():
        for path in export_root.glob("*.json"):
            rel = path.relative_to(root).as_posix()
            if rel not in expected:
                stale.append(rel)
    return sorted(stale)


def write_exports(root: Path = ROOT) -> list[str]:
    """Regenerate the projection; returns the paths written."""
    outputs = build_exports(root)
    (root / EXPORT_DIR).mkdir(parents=True, exist_ok=True)

    expected = set(outputs)
    for path in (root / EXPORT_DIR).glob("*.json"):
        if path.relative_to(root).as_posix() not in expected:
            path.unlink()

    for rel, text in sorted(outputs.items()):
        target = root / rel
        with open(target, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
    return sorted(outputs)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify the committed projection matches the policy sources; do not write",
    )
    args = parser.parse_args(argv)

    if args.check:
        stale = stale_exports()
        if stale:
            print("policy JSON export is stale:", file=sys.stderr)
            for rel in stale:
                print(f"  {rel}", file=sys.stderr)
            print(f"regenerate with: python {GENERATOR}", file=sys.stderr)
            return 1
        print(f"policy JSON export ok files={len(build_exports())}")
        return 0

    written = write_exports()
    print(f"policy JSON export written files={len(written)}")
    for rel in written:
        print(f"  {rel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
