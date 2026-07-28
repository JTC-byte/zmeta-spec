"""The policy JSON projection must stay a projection.

`export/policy/*.json` exists so a consumer outside the Python stack can read
the governed policy without vendoring a YAML parser and without hand-copying
it (P2-01). That only helps if it is true, and a derived artifact that can
drift from its source is worse than no artifact at all: it becomes a second
source of truth that looks authoritative, which is the private-dialect
failure the projection was built to prevent.

So the checks here are the whole value of the feature, not hygiene around it:

- FRESH. Regenerating from `policy/*.yaml` reproduces the committed bytes.
  A policy change that forgets the export fails here rather than shipping a
  projection that quietly describes the previous release.
- VERBATIM. Every export equals `yaml.safe_load` of its source. Not "carries
  the same fields" -- equal. Nothing renamed, filtered, or interpreted.
- COMPLETE, both directions. Every governed policy file has an export, and no
  export exists without a source.
- PINNED. Every generated file is hashed in the release manifest, so a
  consumer can verify what it fetched against the release.

The drift pins are exercised against a synthetic repo root rather than
asserted on the live tree, because a check that only ever sees the good state
cannot tell you it would notice the bad one. Four pins in the R1-11 cycle
passed on reverted trees for exactly that reason.
"""

import json
import re
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import build_release_manifest  # noqa: E402
import export_policy_json  # noqa: E402


def _fake_repo(tmp_path: Path) -> Path:
    """A minimal repo root with two governed policy files."""
    (tmp_path / "policy").mkdir()
    (tmp_path / "policy" / "alpha.yaml").write_text(
        "alpha:\n  payload_must_not_contain: [features, raw_features]\n  limit: 3\n",
        encoding="utf-8",
    )
    (tmp_path / "policy" / "beta.yaml").write_text(
        "beta:\n  enabled: true\n",
        encoding="utf-8",
    )
    return tmp_path


def test_export_is_fresh():
    stale = export_policy_json.stale_exports(ROOT)
    assert stale == [], (
        f"the policy JSON projection is stale in {stale}; regenerate with "
        f"'python tools/export_policy_json.py'. The export is derived -- "
        f"policy/*.yaml is the source of truth and was changed without it."
    )


def test_export_is_a_verbatim_projection_of_its_source():
    sources = export_policy_json.policy_sources(ROOT)
    assert sources, "no governed policy sources found; this check would be vacuous"
    for source in sources:
        target = ROOT / export_policy_json.export_relpath(source, ROOT)
        assert target.is_file(), f"{source.name} has no exported projection at {target}"
        source_data = yaml.safe_load(source.read_text(encoding="utf-8"))
        export_data = json.loads(target.read_text(encoding="utf-8"))
        assert export_data == source_data, (
            f"{target.relative_to(ROOT).as_posix()} is not a verbatim projection of "
            f"{source.relative_to(ROOT).as_posix()}; the export must carry the source's "
            f"data model unchanged, with nothing renamed, filtered, or interpreted"
        )


def test_every_policy_source_is_exported_and_nothing_is_orphaned():
    expected = {
        export_policy_json.export_relpath(source, ROOT)
        for source in export_policy_json.policy_sources(ROOT)
    }
    index_rel = f"{export_policy_json.EXPORT_DIR}/{export_policy_json.INDEX_NAME}"
    present = {
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / export_policy_json.EXPORT_DIR).glob("*.json")
    } - {index_rel}
    assert present == expected, (
        f"policy sources and their exports have diverged; "
        f"missing {sorted(expected - present)}, orphaned {sorted(present - expected)}"
    )


def test_index_source_hashes_match_the_release_manifest_canonicalization():
    """The generator's hash function must agree with the manifest's.

    export_policy_json duplicates the LF-normalizing hash rather than
    importing it (tools/ is not a package). Duplication is fine; silent
    divergence is not, so the agreement is pinned rather than trusted.
    """
    index = json.loads(
        (ROOT / export_policy_json.EXPORT_DIR / export_policy_json.INDEX_NAME).read_text(
            encoding="utf-8"
        )
    )
    assert index["sources"], "index names no sources; this check would be vacuous"
    for entry in index["sources"]:
        expected = build_release_manifest.file_hash(entry["source"], ROOT)
        assert entry["source_sha256"] == expected, (
            f"index source hash for {entry['source']} is {entry['source_sha256']}, "
            f"but the release manifest canonicalization gives {expected}; the two "
            f"hash functions have drifted"
        )


def test_every_exported_file_is_hash_pinned_in_the_release_manifest():
    manifest = yaml.safe_load(
        (ROOT / "release" / "zmeta-release-manifest.yaml").read_text(encoding="utf-8")
    )
    pinned = {entry["path"] for entry in manifest["artifact_hashes"]}
    generated = set(export_policy_json.build_exports(ROOT))
    missing = sorted(generated - pinned)
    assert missing == [], (
        f"generated policy exports are not hash-pinned in the release manifest: "
        f"{missing}. An unpinned projection cannot be verified by the consumer "
        f"that fetched it; add them to the policy_json_export artifact group and "
        f"regenerate the manifest."
    )


def test_policy_readme_lists_every_governed_policy_file():
    """The governed policy set is enumerated in more than one place now.

    The glob in `export_policy_json`, the export directory, and the human
    file list in `policy/README.md`. When this check was written that list
    was missing `command-evidence.yaml` and `profile-precision.yaml` -- two
    governed files a reader of the pack would not know existed, one of them
    the newest thing in it.

    Same machine-invisible class as P2-01: nothing pinned the prose, so it
    fell behind the directory it describes while every hash and version pin
    stayed green. Checked one direction only -- every governed file must be
    named -- so that mentioning a variant or an example elsewhere in the doc
    is not a failure.
    """
    text = (ROOT / "policy" / "README.md").read_text(encoding="utf-8")
    listed = set(re.findall(r"`([A-Za-z0-9._-]+\.yaml)`", text))
    actual = {source.name for source in export_policy_json.policy_sources(ROOT)}
    assert actual, "no governed policy sources found; this check would be vacuous"
    missing = sorted(actual - listed)
    assert missing == [], (
        f"policy/README.md does not name governed policy files {missing}; a reader "
        f"of the pack cannot discover what it contains"
    )


def test_freshness_pin_catches_a_changed_policy_source(tmp_path):
    root = _fake_repo(tmp_path)
    export_policy_json.write_exports(root)
    assert export_policy_json.stale_exports(root) == []

    (root / "policy" / "alpha.yaml").write_text(
        "alpha:\n  payload_must_not_contain: [features, raw_features, modality]\n  limit: 3\n",
        encoding="utf-8",
    )
    assert export_policy_json.stale_exports(root) == [
        "export/policy/alpha.json",
        "export/policy/index.json",
    ], "a changed policy source did not mark its projection stale"


def test_freshness_pin_catches_a_hand_edited_export(tmp_path):
    root = _fake_repo(tmp_path)
    export_policy_json.write_exports(root)

    target = root / "export" / "policy" / "beta.json"
    target.write_text('{\n  "beta": {\n    "enabled": false\n  }\n}\n', encoding="utf-8")
    assert export_policy_json.stale_exports(root) == ["export/policy/beta.json"], (
        "a hand-edited export was not caught; the projection is one-directional "
        "in authority and an edited JSON file is a stale file, not policy"
    )


def test_freshness_pin_catches_an_orphaned_export(tmp_path):
    root = _fake_repo(tmp_path)
    export_policy_json.write_exports(root)

    (root / "export" / "policy" / "gamma.json").write_text("{}\n", encoding="utf-8")
    assert export_policy_json.stale_exports(root) == ["export/policy/gamma.json"], (
        "an export with no governed source was not caught; a consumer would read "
        "it as policy"
    )


def test_regeneration_removes_an_orphaned_export(tmp_path):
    root = _fake_repo(tmp_path)
    export_policy_json.write_exports(root)
    orphan = root / "export" / "policy" / "gamma.json"
    orphan.write_text("{}\n", encoding="utf-8")

    export_policy_json.write_exports(root)
    assert not orphan.exists(), (
        "regeneration left an orphaned export in place; a deleted policy file must "
        "not leave its projection behind"
    )
    assert export_policy_json.stale_exports(root) == []
