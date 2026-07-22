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


# Every doc carrying the 'Current release context' header, not just the
# overview. R1-11 verification pass 2: only the overview was machine-pinned,
# so three siblings with the identical header sat five releases stale
# (v1.1.11 at a v1.1.16 baseline). A guard that covers one member of a family
# does not protect the family.
RELEASE_CONTEXT_DOCS = (
    "docs/zmeta_professional_overview.md",
    "docs/zmeta_correlation_pattern.md",
    "docs/zmeta_mqtt_binding_guidance.md",
    "docs/zmeta_vocabulary_crosswalk.md",
)


def test_every_release_context_line_matches_manifest():
    version = manifest_release_version()
    stale = [
        path
        for path in RELEASE_CONTEXT_DOCS
        if not overview_has_release_context(_read(path), version)
    ]
    assert stale == [], (
        f"release-context lines do not name {version} in {stale}; "
        f"expected 'Current release context: ZMeta {version}.' in each"
    )


def _carries_release_context_header(path: Path) -> bool:
    """True when a doc opens with the pinned release-context header.

    Header position, not mere mention: audit records and worklogs discuss the
    pattern in prose and are not themselves carriers.
    """
    head = path.read_text(encoding="utf-8").splitlines()[:10]
    return any(line.startswith("Current release context: ZMeta") for line in head)


def test_release_context_doc_list_is_complete():
    # The list above is only protective if it names every doc that carries the
    # header — a new doc with the same line must not silently escape the pin.
    carriers = sorted(
        path.relative_to(ROOT).as_posix()
        for path in ROOT.glob("docs/*.md")
        if _carries_release_context_header(path)
    )
    assert carriers == sorted(RELEASE_CONTEXT_DOCS), (
        "docs carrying a 'Current release context' line have drifted from the "
        f"pinned list; found {carriers}, pinned {sorted(RELEASE_CONTEXT_DOCS)}"
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


# The zmeta_version identifiers are semantic-branch names, not release pins.
# v1.1.0 is unfortunately BOTH a published release tag and the experimental
# schema branch, so it is excluded here — otherwise every legitimate mention
# of the experimental branch would trip the guard.
_SEMANTIC_BRANCH_LITERALS = {"v1.1.0"}

# Guard against matching a prefix of a longer version (v1.1.1 inside v1.1.16)
# WITHOUT losing a version that ends a sentence ("...currently v1.1.9.") — the
# exact shape of the R11-11 regression this check exists to catch. So: reject
# only a following digit, or a dot that is itself followed by a digit.
_NOT_LONGER_VERSION = r"(?!\.?\d)"


def superseded_release_versions(current: str) -> list[str]:
    """Published release versions other than the current one."""
    published = {
        match.group(1)
        for path in (ROOT / "release").glob("RELEASE_NOTES_v*.md")
        if (match := re.search(r"RELEASE_NOTES_(v[\d.]+)\.md", path.name))
    }
    return sorted(published - {current} - _SEMANTIC_BRANCH_LITERALS)


def test_superseded_release_matcher_is_phrasing_independent():
    # The guard below is only as good as this matcher, and the first cut of
    # it silently failed on a version ending a sentence ('...v1.1.9.') - the
    # exact regression shape it was written to catch. Pin both directions.
    version = manifest_release_version()
    superseded = superseded_release_versions(version)
    assert superseded, "no superseded releases found; matcher would be vacuous"

    def names_superseded(text: str) -> bool:
        return any(
            re.search(re.escape(item) + _NOT_LONGER_VERSION, text)
            for item in superseded
        )

    must_catch = [
        "Pin to a release, currently v1.1.9.",
        "Pin to a release — as of today, v1.1.9.",
        "Pin to release v1.1.14 for production.",
        "We are on v1.1.15 at time of writing.",
    ]
    for text in must_catch:
        assert names_superseded(text), f"stale claim slipped through: {text!r}"

    must_not_catch = [
        # zmeta_version semantic branches, not release pins
        "A v1.1.0 event validates on the experimental branch.",
        "validated as v1.0.",
        "schema/zmeta-event-1.1.0.schema.json",
        # R1-11 A-25: the `v` prefix is the discriminator that separates a
        # release pin from the many non-release dotted triples in these
        # docs (contract section numbers like 4.5.1, vendor semvers like
        # translate:kraken@1.0.0, schema filenames like 1.1.0). Matching
        # the bare form here would false-positive on "Section 1.1.2" in the
        # very documents this guard protects, so the bound is deliberate
        # and pinned: bare version literals inside narrowly-scoped worked
        # command blocks are covered by _stale_version_literals, which does
        # use `v?` precisely because its scope is a single command block.
        "See Section 1.1.9 of the contract.",
        "translate:kraken@1.1.9",
        # the current release, in any phrasing
        f"Current release context: ZMeta {version}.",
        f"ZMeta {version} is current",
    ]
    for text in must_not_catch:
        assert not names_superseded(text), f"false positive on: {text!r}"


def test_overview_body_names_no_superseded_release():
    # R1-11 verification pass 2: the guard above matches one exact phrasing
    # ('currently vX.Y.Z'), so a reworded but equally stale claim - 'as of
    # today, v1.1.9', 'pin to release v1.1.9' - passed it clean. This check
    # is phrasing-independent: the overview body may name the current
    # release (the pinned header line) and the semantic branches, never a
    # superseded release.
    version = manifest_release_version()
    text = _read("docs/zmeta_professional_overview.md")
    stale = {
        superseded: len(re.findall(re.escape(superseded) + _NOT_LONGER_VERSION, text))
        for superseded in superseded_release_versions(version)
    }
    stale = {name: count for name, count in stale.items() if count}
    assert stale == {}, (
        f"docs/zmeta_professional_overview.md names superseded releases {stale}; "
        f"keep body guidance version-agnostic — the header release-context line "
        f"is the single pinned current-version statement (now {version})"
    )


def test_change_governance_worked_commands_match_manifest():
    # R1-11 A-28: the third member of the worked-command family. README and
    # the installation guide were pinned; the governance doc's build-then-
    # validate block carries the same `--release-id zmeta-vX.Y.Z` literal and
    # was re-baselined by hand every cycle, so it could go stale with no
    # signal - the failure the other two pins already exist to prevent.
    version = manifest_release_version()
    text = _read("docs/zmeta_change_governance.md")
    blocks = re.findall(r"```[a-z]*\n(.*?)```", text, re.DOTALL)
    release_blocks = [block for block in blocks if "build_release_manifest.py" in block]
    assert release_blocks, (
        "docs/zmeta_change_governance.md worked manifest-rebuild block not found"
    )
    stale = []
    for block in release_blocks:
        stale.extend(_stale_version_literals(block, version))
    assert stale == [], (
        f"docs/zmeta_change_governance.md worked commands carry stale version "
        f"literals {stale}; re-baseline them to {version}"
    )


def test_signer_version_help_example_matches_manifest():
    # R1-11 A-28. RELEASE_CHECKLIST.md's doc-currency pass already names this
    # file as a surface to re-baseline, so the obligation exists either way;
    # this makes it machine-checked instead of remembered. The `--version`
    # default is manifest-derived, so a stale example is not a silent wrong
    # signature - but an operator who copies it passes an explicit --version
    # for a PUBLISHED release, and the checksum-immutability guard is then
    # the only thing between that and a rewritten published record.
    version = manifest_release_version()
    text = _read("release/sign_release_artifacts.py")
    examples = re.findall(r"e\.g\. (v\d+\.\d+\.\d+)", text)
    assert examples, (
        "release/sign_release_artifacts.py --version help no longer carries an "
        "'e.g. vX.Y.Z' example"
    )
    stale = [item for item in examples if item != version]
    assert stale == [], (
        f"release/sign_release_artifacts.py --version help names {stale}; "
        f"re-baseline the example to {version}"
    )


def test_compat_cli_test_derives_its_target_rather_than_hardcoding_it():
    """The compat CLI test must not pin a release literal in executable code.

    R1-11 A-28: the target had been hardcoded to `v1.1.14` while the manifest
    read `v1.1.16`, so a test named "accepts current release target" quietly
    stopped exercising the current release. The fix derives the target from the
    manifest - a real improvement that was reversible with no signal, because
    `check_compat.py` TARGETS still lists the older release and a revert to the
    literal therefore still passes.

    Docstrings and comments are exempt: this file's own docstring has to be
    able to name the versions that produced the defect. Only the `v` prefixed
    form is a release pin, which is the same discriminator
    `_NOT_LONGER_VERSION` above is built on - bare dotted triples are
    zmeta_version semantic branches.
    """
    import ast

    path = ROOT / "gateway" / "tests" / "test_check_compat_cli.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.body and isinstance(node.body[0], ast.Expr):
                value = node.body[0].value
                if isinstance(value, ast.Constant) and isinstance(value.value, str):
                    docstrings.add(id(value))
    hardcoded = [
        (node.lineno, literal)
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and id(node) not in docstrings
        for literal in re.findall(r"\bv\d+\.\d+\.\d+", node.value)
    ]
    assert hardcoded == [], (
        f"gateway/tests/test_check_compat_cli.py hardcodes release literals "
        f"{hardcoded}; derive the target from the release manifest so the test "
        "cannot quietly stop exercising the current release"
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
