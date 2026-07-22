"""Release-currency pins: current-facing surfaces must match the manifest.

The release manifest's release_id is the single source of truth for what the
current release is. Every surface that presents itself as "current" must agree
with it, so a release bump cannot leave stale current-facing text behind
(the stale-defaults failure class from the R1-10 audit).

Covered surfaces (enumerated, current-facing only):
- README.md current-release line AND the bundle-builders worked commands
- spec/installation-guide.md baseline line AND the worked release commands
- docs/zmeta_professional_overview.md release-context line, plus a body
  guard against present-tense "currently vX.Y.Z" claims (the R1-11 R11-11
  class: body text steering adopters onto a stale baseline while only the
  header was machine-pinned)
- release/README.md "Current formal release" line
- CHANGELOG.md first versioned heading
- tools/check_compat.py TARGETS list
- docs/zmeta_refinement_handoff.md "Use tag" current-release pointer (the
  one forward-looking line in an otherwise-excluded rolling record)

Deliberately EXCLUDED: the rolling narrative content of the session records
(docs/zmeta_refinement_worklog.md, docs/zmeta_refinement_handoff.md body,
and the worklog archive). Those entries narrate past sessions, so
historical version text in them is legitimate and pinning it would force
rewriting history on every release.

Each check helper takes the file text as an argument so the assertion logic
can be exercised against doctored copies without touching the real files.
"""

import re
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "release" / "zmeta-release-manifest.yaml"


def manifest_release_version() -> str:
    """Current release tag from the manifest release_id (zmeta-vX.Y.Z -> vX.Y.Z)."""
    manifest = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
    release_id = str(manifest.get("release_id", ""))
    assert release_id.startswith("zmeta-v"), (
        f"release/zmeta-release-manifest.yaml release_id must look like zmeta-vX.Y.Z, got {release_id!r}"
    )
    return release_id[len("zmeta-"):]


def _read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


def readme_has_current_release(text: str, version: str) -> bool:
    return f"- Current release: `{version}`" in text


def installation_guide_has_baseline(text: str, version: str) -> bool:
    return f"current `{version}` release baseline" in text


def overview_has_release_context(text: str, version: str) -> bool:
    return f"Current release context: ZMeta {version}." in text


def release_readme_has_current_formal(text: str, version: str) -> bool:
    return f"Current formal release: `{version}`" in text


def changelog_first_versioned_heading(text: str) -> str | None:
    """First '## [X.Y.Z]' heading, skipping the '## [Unreleased]' section."""
    match = re.search(r"^## \[(\d+\.\d+\.\d+)\]", text, re.MULTILINE)
    return match.group(1) if match else None


def check_compat_targets(text: str) -> list[str]:
    match = re.search(r"TARGETS\s*=\s*\((.*?)\)", text, re.DOTALL)
    if not match:
        return []
    return re.findall(r'"(v\d+\.\d+\.\d+)"', match.group(1))


def test_readme_current_release_line_matches_manifest():
    version = manifest_release_version()
    assert readme_has_current_release(_read("README.md"), version), (
        f"README.md current-release line does not name {version}; "
        f"expected '- Current release: `{version}`'"
    )


def test_installation_guide_baseline_matches_manifest():
    version = manifest_release_version()
    assert installation_guide_has_baseline(_read("spec/installation-guide.md"), version), (
        f"spec/installation-guide.md baseline line does not name {version}; "
        f"expected 'current `{version}` release baseline'"
    )


def test_professional_overview_release_context_matches_manifest():
    version = manifest_release_version()
    assert overview_has_release_context(_read("docs/zmeta_professional_overview.md"), version), (
        f"docs/zmeta_professional_overview.md release-context line does not name {version}; "
        f"expected 'Current release context: ZMeta {version}.'"
    )


def test_release_readme_current_formal_release_matches_manifest():
    version = manifest_release_version()
    assert release_readme_has_current_formal(_read("release/README.md"), version), (
        f"release/README.md 'Current formal release' line does not name {version}; "
        f"expected 'Current formal release: `{version}`'"
    )


def test_changelog_first_versioned_heading_matches_manifest():
    version = manifest_release_version()
    bare_version = version.lstrip("v")
    first = changelog_first_versioned_heading(_read("CHANGELOG.md"))
    assert first == bare_version, (
        f"CHANGELOG.md first versioned heading is [{first}], expected [{bare_version}] "
        f"to match the release manifest"
    )


def test_check_compat_targets_include_current_release():
    version = manifest_release_version()
    targets = check_compat_targets(_read("tools/check_compat.py"))
    assert targets, "tools/check_compat.py TARGETS tuple not found or empty"
    assert version in targets, (
        f"tools/check_compat.py TARGETS does not include the current release {version}; "
        f"extend TARGETS when the release manifest is regenerated"
    )


def _stale_version_literals(text: str, version: str) -> list[str]:
    """Version literals in a worked-command block that disagree with current."""
    bare = version.lstrip("v")
    found = re.findall(r"v?(\d+\.\d+\.\d+)", text)
    return [item for item in found if item != bare]


def test_readme_bundle_builder_commands_match_manifest():
    # R1-11 R11-18: the bundle-builders list sat three releases stale while
    # the adjacent sibling line was bumped every cycle - the block is now
    # machine-pinned as a whole.
    version = manifest_release_version()
    text = _read("README.md")
    match = re.search(r"- Bundle builders:\n(( {4,}- .+\n)+)", text)
    assert match, "README.md bundle-builders block not found"
    stale = _stale_version_literals(match.group(1), version)
    assert stale == [], (
        f"README.md bundle-builders commands carry stale version literals {stale}; "
        f"re-baseline them to {version}"
    )


def test_installation_guide_worked_commands_match_manifest():
    # R1-11 R11-17: line-level history showed one worked command surviving
    # three doc-currency passes because only the baseline line was pinned.
    version = manifest_release_version()
    text = _read("spec/installation-guide.md")
    blocks = re.findall(r"```text\n(.*?)```", text, re.DOTALL)
    release_blocks = [b for b in blocks if "build_release_bundle.py" in b]
    assert release_blocks, "installation-guide worked release-command block not found"
    stale = []
    for block in release_blocks:
        stale.extend(_stale_version_literals(block, version))
    assert stale == [], (
        f"spec/installation-guide.md worked commands carry stale version literals {stale}; "
        f"re-baseline them to {version}"
    )


def test_overview_body_carries_no_stale_currently_claims():
    # R1-11 R11-11: 'Pin to a release, currently v1.1.9' survived four
    # release passes because only the header line was machine-pinned.
    text = _read("docs/zmeta_professional_overview.md")
    stale_claims = re.findall(r"currently v\d+\.\d+\.\d+", text)
    assert stale_claims == [], (
        f"docs/zmeta_professional_overview.md body carries present-tense version "
        f"claims {stale_claims}; keep body guidance version-agnostic (the header "
        f"release-context line is the pinned current-version statement)"
    )


def test_handoff_use_tag_pointer_matches_manifest():
    # R1-1 exclusion refined (R11-15): the handoff's 'Use tag' line is the
    # one forward-looking current-release pointer in the rolling record and
    # is now pinned; narrative history remains excluded.
    version = manifest_release_version()
    text = _read("docs/zmeta_refinement_handoff.md")
    match = re.search(r"Use tag `(v\d+\.\d+\.\d+)`", text)
    assert match, "handoff 'Use tag' current-release pointer not found"
    assert match.group(1) == version, (
        f"docs/zmeta_refinement_handoff.md 'Use tag' points at {match.group(1)}, "
        f"expected {version}"
    )
