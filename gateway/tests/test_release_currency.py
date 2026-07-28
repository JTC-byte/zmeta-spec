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

Beyond literals, one CONTENT pin (P2-01, at the end of this file): the
README's release-focus bullet must actually describe the current release,
and any governance claim it makes must be carried by that release's notes.
A version literal is machine-visible and a paragraph of prose is not, which
is how the focus bullet described v1.1.16 through two later cuts with every
literal pin above green.

Each check helper takes the file text as an argument so the assertion logic
can be exercised against doctored copies without touching the real files.
"""

import re
from fnmatch import fnmatch
from pathlib import Path

import yaml

from vacuity import mutate


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
    "docs/zmeta_track_lifecycle_pattern.md",
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


def test_tools_readme_worked_commands_match_manifest():
    # PC-11 (v1.1.19 pre-cut): the fourth member of the worked-command family.
    # README, the installation guide and the governance doc were pinned;
    # tools/README.md carries the same `build_release_package.py` formal-build
    # line and was not. It went stale during this very cut and was caught only
    # because a DIFFERENT pin counts how many current-facing formal builds it
    # can see and refuses to run on fewer than four — the stale file dropped
    # out of that count instead of being flagged directly.
    version = manifest_release_version()
    text = _read("tools/README.md")
    blocks = re.findall(r"```[a-z]*\n(.*?)```", text, re.DOTALL)
    release_blocks = [b for b in blocks if "build_release_package.py" in b or "build_mvp_packages.py" in b]
    assert release_blocks, "tools/README.md worked release-command block not found"
    stale = []
    for block in release_blocks:
        stale.extend(_stale_version_literals(block, version))
    assert stale == [], (
        f"tools/README.md worked commands carry stale version literals {stale}; "
        f"re-baseline them to {version}"
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


# ---------------------------------------------------------------------------
# Unpinned current-release literals found by the v1.1.19 pre-cut range review
# (PC-01..04). Everything above pins a surface someone once noticed going
# stale. These four were never noticed, and one of them degrades verification
# rather than prose:
#
# - the README's TITLE LINE, which is the single most-read current-release
#   claim in the repository and was anchored by nothing;
# - `.github/workflows/ci.yml`'s `--target` literal. A cut that forgets it
#   leaves CI testing migration compatibility against the PREVIOUS release
#   while reporting green — a guard that quietly stops guarding, which is the
#   P2-D1 class arriving in CI configuration rather than in a test;
# - the README Tools block's own `--target`, a sibling of the bundle-builders
#   block that was pinned while this one was not;
# - `release/README.md`'s worked example version.
# ---------------------------------------------------------------------------


def readme_title_release(text: str) -> str | None:
    """The version named in the README's H1, which is line 1 of the repo."""
    match = re.search(
        r"^# ZMeta Specification \(v1\.0 Locked, current release (v\d+\.\d+\.\d+)\)",
        text,
        re.MULTILINE,
    )
    return match.group(1) if match else None


def compat_target_literals(text: str) -> list[str]:
    """Every `--target vX.Y.Z` literal in a file."""
    return re.findall(r"--target (v\d+\.\d+\.\d+)", text)


# Every file carrying a worked `--target`. Enumerated rather than globbed so a
# new carrier is a deliberate addition; the completeness of the list is itself
# checked below.
COMPAT_TARGET_CARRIERS = (
    "README.md",
    "adapters/README.md",
    "tools/README.md",
    ".github/workflows/ci.yml",
)


def test_readme_title_line_names_the_current_release():
    version = manifest_release_version()
    named = readme_title_release(_read("README.md"))
    assert named, (
        "README.md H1 no longer matches the pinned "
        "'# ZMeta Specification (v1.0 Locked, current release vX.Y.Z)' shape"
    )
    assert named == version, (
        f"README.md title line names {named}, but the release manifest says {version}. "
        f"This is the first line of the repository and the most-read current-release "
        f"claim in it."
    )


def test_every_compat_target_literal_matches_manifest():
    version = manifest_release_version()
    stale = {}
    for path in COMPAT_TARGET_CARRIERS:
        found = [item for item in compat_target_literals(_read(path)) if item != version]
        if found:
            stale[path] = found
    assert stale == {}, (
        f"worked `--target` literals name superseded releases {stale}; re-baseline to "
        f"{version}. In .github/workflows/ci.yml this is not cosmetic — a stale target "
        f"means CI keeps checking migration compatibility against the previous release "
        f"and still reports green."
    )


# Narrative surfaces name past releases legitimately, and re-baselining them
# would falsify history rather than keep it current. Two families, both with a
# reason that is not "it was inconvenient":
#
# - `CHANGELOG.md` and the frozen per-release records under `release/`
#   (RELEASE_NOTES_v*, VALIDATION_REPORT_v*) describe a specific past release.
#   `CHANGELOG.md` carries `--target v1.1.17` in a historical entry.
# - everything `docs/README.md` itself classifies as a process record.
#
# The docs half is DERIVED from that file rather than restated here, so a doc
# reclassified for readers is reclassified for this guard in the same edit.
# Hand-maintaining a second copy of a classification the repo already
# publishes is the exact defect P2-01 was about.
_FROZEN_RELEASE_RECORD_PATTERNS = (
    "release/RELEASE_NOTES_v*.md",
    "release/VALIDATION_REPORT_v*.md",
)
_NARRATIVE_FILES = ("CHANGELOG.md",)


def docs_process_records() -> tuple[str, ...]:
    """Doc paths the repo's own `docs/README.md` calls process records.

    Returns fnmatch patterns — the classification legitimately uses wildcards
    (`s1_*.md`, `r1_*.md`) for the dated per-task record families.
    """
    text = _read("docs/README.md")
    section = re.search(r"^## Process records.*?(?=^## |\Z)", text, re.MULTILINE | re.DOTALL)
    assert section, (
        "docs/README.md no longer has a '## Process records' section; this guard "
        "derives its exclusions from that classification and cannot proceed without it"
    )
    names = re.findall(r"`([A-Za-z0-9_*.-]+\.md)`", section.group(0))
    assert names, "docs/README.md process-records section names no files"
    return tuple(f"docs/{name}" for name in names)


def _is_narrative(path: str) -> bool:
    if path in _NARRATIVE_FILES:
        return True
    patterns = _FROZEN_RELEASE_RECORD_PATTERNS + docs_process_records()
    return any(fnmatch(path, pattern) for pattern in patterns)


def _tracked_files(patterns: tuple[str, ...]) -> set[str]:
    """Repo-tracked paths matching git pathspecs.

    Tracked, not globbed. The first version of the check below walked the
    working tree and picked up `LOCAL_NOTES.md`, which is gitignored — so it
    failed on a maintainer's machine and would have passed on CI, where the
    file does not exist. An environment-dependent guard is a guard that
    reports on the wrong thing.
    """
    import subprocess

    result = subprocess.run(
        ["git", "ls-files", "-z", *patterns],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result.returncode == 0, (
        f"git ls-files failed, so tracked-file enumeration is unavailable and this "
        f"check cannot mean anything: {result.stderr.strip()}"
    )
    return {item for item in result.stdout.split("\0") if item}


def test_compat_target_carrier_list_is_complete():
    """A new file with a worked `--target` must not escape the pin above.

    The same failure the release-context doc list already had: a guard that
    covers some members of a family does not protect the family.
    """
    candidates = _tracked_files(("*.md", ".github/workflows/*.yml"))
    assert candidates, "no tracked candidates found; this check would be vacuous"
    carriers = {
        path
        for path in candidates
        if not _is_narrative(path)
        and compat_target_literals((ROOT / path).read_text(encoding="utf-8"))
    }
    assert carriers == set(COMPAT_TARGET_CARRIERS), (
        f"files carrying a worked `--target` have drifted from the pinned list; "
        f"found {sorted(carriers)}, pinned {sorted(COMPAT_TARGET_CARRIERS)}. Add a new "
        f"carrier to COMPAT_TARGET_CARRIERS, or to the narrative exclusions if it "
        f"legitimately names past releases."
    )


def test_release_readme_example_version_matches_manifest():
    version = manifest_release_version()
    examples = re.findall(r"e\.g\. `(v\d+\.\d+\.\d+)`", _read("release/README.md"))
    assert examples, "release/README.md worked-example version no longer present"
    stale = [item for item in examples if item != version]
    assert stale == [], (
        f"release/README.md worked example names {stale}; re-baseline to {version}"
    )


def test_pc_pins_demonstrate_red_on_a_superseded_literal():
    """Red demonstration for all four, per the amended discipline 5.

    Each pin is shown failing on content doctored to the previous release,
    using the real files so the demonstration cannot pass against a shape the
    live documents no longer have. `mutate` refuses a no-op.
    """
    version = manifest_release_version()
    superseded = superseded_release_versions(version)
    assert superseded, "no superseded release to doctor with; the demonstration would be vacuous"
    older = superseded[-1]

    title_text = _read("README.md")
    doctored = mutate(
        title_text,
        f"current release {version})",
        f"current release {older})",
        what="roll the README title line back one release",
    )
    assert readme_title_release(doctored) == older, (
        "the title-line matcher does not see a rolled-back version, so the pin "
        "could not catch one"
    )

    ci_text = _read(".github/workflows/ci.yml")
    doctored_ci = mutate(
        ci_text,
        f"--target {version}",
        f"--target {older}",
        what="roll the CI compat target back one release",
    )
    assert compat_target_literals(doctored_ci) == [older], (
        "the compat-target matcher does not see a rolled-back CI target"
    )

    release_readme = _read("release/README.md")
    doctored_rr = mutate(
        release_readme,
        f"e.g. `{version}`",
        f"e.g. `{older}`",
        what="roll the release/README example back one release",
    )
    assert re.findall(r"e\.g\. `(v\d+\.\d+\.\d+)`", doctored_rr) == [older]


# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Content currency, SECOND DESIGN (P2-01, redesigned after the v1.1.19 pre-cut
# review defeated the first one).
#
# THE FIRST DESIGN DID NOT WORK, and how it failed is the point. Two rules
# tried to infer truth from prose:
#
#   * "the bullet must name something this release introduced" was implemented
#     as "a backticked string present in the current release notes and in no
#     earlier notes". Backticking the version number satisfied it. So did
#     `policy/*.yaml`, which predates the release by many cuts.
#   * "a governance claim must be carried by the notes" was a regex that knew
#     one phrasing. "Schema, policy, and event vocabulary are unchanged" evaded
#     it, as did five other natural paraphrases, and the matcher's own fixture
#     blessed the whole "unchanged" family by construction.
#
# Together they passed a bullet carried forward WHOLESALE from v1.1.16 -- the
# exact defect the pins exist for -- after two one-word edits.
#
# The redesign follows semantics-contract gate 5: structure is authoritative,
# free text is a projection. A release's governance status is load-bearing
# data, so it is COMPUTED from the manifest against a committed baseline,
# rendered into one canonical sentence, and the document must carry that
# sentence verbatim. That is an ALLOWLIST. A blocklist of forbidden phrasings
# must be re-derived every time somebody writes a new one -- the B-01 lesson
# from the compact mapping, arrived at again by the same road.
#
# The "introduced" rule now reads real artifact paths added or changed since
# the baseline release, so a version literal cannot satisfy it.
#
# STATED LIMIT, so this is not mistaken for total coverage: if an author keeps
# the generated sentence AND writes a contradicting paraphrase beside it, the
# contradiction ships. This catches the defect that actually occurred -- a
# wholesale carried-forward bullet, where the generated sentence is absent --
# not an author deliberately writing two conflicting statements.
# ---------------------------------------------------------------------------

import sys

_TOOLS = ROOT / "tools"
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

import release_focus_facts as facts  # noqa: E402


def _normalize_ws(text: str) -> str:
    return " ".join(text.split())


def readme_release_focus_block(text: str) -> str | None:
    """The '- Release focus:' bullet body.

    Bounded by the next top-level bullet OR the next heading. The first cut
    stopped only at '- ', so moving the bullet to the end of its list made the
    block swallow the following section heading and the prose under it, which
    would leave the content rules evaluating unrelated text.
    """
    match = re.search(
        r"^- Release focus:(.*?)(?=^- |^#|\Z)", text, re.MULTILINE | re.DOTALL
    )
    return match.group(1) if match else None


def paths_named_in(block: str, candidates: set[str]) -> list[str]:
    """Which of `candidates` the block actually names.

    Substring rather than token matching: these are paths written inside prose
    and code spans. A path is a concrete thing that either appears or does
    not, unlike the previous rule's "any backticked string" -- which a version
    number satisfied.
    """
    return sorted(path for path in candidates if path in block)


_STALE_FOCUS_BLOCK_AT_v1_1_18_TAG = """ the first external real-capture corpus,
  `adapters/mapping-packs/edge-comms-bladerf/` (PR #7), two real
  bladeRF / ROS2 EW `rf_detection` flight captures paired with
  schema-valid RF `OBSERVATION_EVENT` expected outputs, merged after
  adversarial review with maintainer honesty fixes (a frame-unlabeled
  heading-derived bearing demoted to explicitly named native features
  per contract 6.4; an unasserted statistical metric dropped;
  timestamp-source provenance preserved; pack mapping reconciled with
  its fixtures). No schema, policy, or event-vocabulary changes; the
  locked v1.0 kernel's semantics are unchanged.
"""


def test_readme_release_focus_names_something_this_release_touched():
    block = readme_release_focus_block(_read("README.md"))
    assert block, "README.md '- Release focus:' bullet not found"
    introduced = facts.introduced_paths(facts.load_baseline(), facts.load_manifest())
    assert introduced, "nothing added or changed since the baseline; check would be vacuous"
    named = paths_named_in(block, introduced)
    assert named, (
        f"README.md release-focus bullet names none of the {len(introduced)} artifact "
        f"paths this release added or changed. A bullet carried forward from an "
        f"earlier cut cannot name any of them, which is exactly the defect this "
        f"catches. Name at least one, e.g. {sorted(introduced)[0]}."
    )


def test_readme_release_focus_carries_the_generated_governance_sentence():
    block = readme_release_focus_block(_read("README.md"))
    assert block, "README.md '- Release focus:' bullet not found"
    sentence = facts.governance_sentence(facts.load_baseline(), facts.load_manifest())
    assert _normalize_ws(sentence) in _normalize_ws(block), (
        f"README.md release-focus bullet does not carry the generated governance "
        f"sentence verbatim. It is computed from the release manifest against "
        f"release/governed-baseline.yaml and must not be paraphrased:\n\n  {sentence}\n\n"
        f"Print it with `python tools/release_focus_facts.py`."
    )


def test_content_rules_reject_the_attacks_that_defeated_the_first_design():
    """Red demonstration against the panel's ACTUAL evasions, not invented ones.

    Every input below passed the first design. All must fail this one.
    """
    baseline, manifest = facts.load_baseline(), facts.load_manifest()
    introduced = facts.introduced_paths(baseline, manifest)
    sentence = _normalize_ws(facts.governance_sentence(baseline, manifest))
    version = manifest_release_version()

    # Attack 1: the carried-forward bullet with the two one-word edits that
    # defeated the first design -- a reworded claim and a backticked version.
    attacked = _STALE_FOCUS_BLOCK_AT_v1_1_18_TAG.replace(
        "No schema, policy, or event-vocabulary changes;",
        "Schema, policy, and event vocabulary are unchanged;",
    ) + "  See `" + version + "`.\n"
    assert paths_named_in(attacked, introduced) == [], (
        "a backticked version literal is again satisfying the introduced rule"
    )
    assert sentence not in _normalize_ws(attacked), (
        "the carried-forward bullet is being credited with the generated sentence"
    )

    # Attack 2: every paraphrase the reviewer found. None may substitute for
    # the generated sentence. This is what an allowlist buys.
    for paraphrase in (
        "None of the schema, policy, or event-vocabulary changed.",
        "Neither the schema nor the policy pack changed.",
        "Zero schema, policy, or vocabulary changes.",
        "The schema, policy pack, and event vocabulary are unchanged.",
        "Nothing in the schema, policy, or event vocabulary changed.",
        "This cut mints no new reason codes.",
        "No schema, policy, or event-vocabulary changes.",
    ):
        assert sentence not in _normalize_ws(paraphrase), (
            "paraphrase accepted as the generated sentence: " + repr(paraphrase)
        )

    # Attack 3: a scoped claim must not license an unscoped one. The old carry
    # check was a substring test, so notes saying "no governed change IN THE
    # ADAPTERS" licensed a bare "no governed change" in the README.
    scoped = sentence.replace("in this release", "in the gateway adapters")
    assert scoped != sentence
    assert sentence not in _normalize_ws(scoped), "a scoped variant still matches"

    # The live bullet must pass the same rules these attacks fail.
    live = readme_release_focus_block(_read("README.md"))
    assert paths_named_in(live, introduced), "the live bullet fails the introduced rule"
    assert sentence in _normalize_ws(live), "the live bullet lacks the generated sentence"


def test_governance_sentence_tracks_the_actual_governed_state():
    """The sentence must be derived, not decorative.

    If a governed artifact's hash moves, the sentence must change -- otherwise
    the README could carry a stale-but-verbatim sentence forever and the
    allowlist would be pinning a fossil.
    """
    baseline, manifest = facts.load_baseline(), facts.load_manifest()
    clean = facts.governance_sentence(baseline, manifest)
    assert "No governed artifact changed" in clean, (
        "this release is governed-clean by independent check; the sentence should say so"
    )

    doctored = dict(manifest)
    doctored["artifact_hashes"] = [
        dict(entry, hash="sha256:deadbeef")
        if entry["path"] == "schema/zmeta-event-1.0.schema.json"
        else entry
        for entry in manifest["artifact_hashes"]
    ]
    moved = facts.governance_sentence(baseline, doctored)
    assert moved != clean, "moving the locked v1.0 schema hash did not change the sentence"
    assert "schema/zmeta-event-1.0.schema.json" in moved, (
        "the changed governed artifact is not named in the sentence: " + moved
    )


def test_baseline_is_present_and_describes_a_published_release():
    baseline = facts.load_baseline()
    assert baseline["baseline_release_id"].startswith("zmeta-v")
    assert baseline["artifact_hashes"], "baseline records no artifacts"
    current = facts.load_manifest()["release_id"]
    assert baseline["baseline_release_id"] != current, (
        "the baseline names the CURRENT release (" + current + "); it must name the "
        "previously published one, or every comparison is trivially empty"
    )
