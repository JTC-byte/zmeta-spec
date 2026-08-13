"""Records- and teaching-surface claim pins (R1-11 A-13 / A-17 / A-18 classes).

These guard three *documentation defect classes* that the R1-11 cycle
reproduced repeatedly. None of them is about code behaviour; all three are
about a doc making a claim that reality does not keep.

COUPLING, recorded per the apparatus audit's maintainer call (2026-08-13):
this file's non-vacuity floors are satisfied by figures inside the r1_11
process records, so the records and this check retire in pairs. Anyone
moving or archiving an r1_11 record must re-derive the floors here in the
same commit, or this guard goes vacuous while staying green.

- **A-13 — frozen counts attributed to a moving ref.** Five separate
  recurrences: a record froze ``NN files, +NNNN / -NNN`` for
  ``origin/main..HEAD``, and the very commit that wrote the figure moved
  ``HEAD`` past it. The durable rule is not "keep the number correct" (it
  cannot be kept correct) but "never attribute a frozen total to a moving
  ref": either tell the reader to measure, or anchor the figure to an
  immutable commit.
- **A-17 — a worked command pair that cannot succeed.** The documented
  build-then-validate sequence built a ``formal_release`` package without
  ``--release-notes``, so the builder copied the unpopulated notes template
  and the validator on the very next line refused it with
  ``RELEASE_PACKAGE_NOTES_PLACEHOLDER``. Four teaching surfaces carried the
  pair; only ``RELEASE_CHECKLIST.md`` had been updated.
- **A-18 — a currency sweep converting a historical record into a
  present-tense claim.** The handoff's validation-command inventory was
  re-labelled "unchanged in shape since", which the repo's own release
  reports falsify (the command set moved at v1.1.14 and again at v1.1.16).

Every check enumerates its family from the tree rather than naming the
exemplar, and every check asserts a non-vacuity floor first: an oracle that
passes because it found nothing to inspect proves nothing, which is the
failure mode this cycle already shipped once.

Helpers take text as an argument so the assertion logic can be exercised
against doctored copies without touching real files.
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
        "release/zmeta-release-manifest.yaml release_id must look like "
        f"zmeta-vX.Y.Z, got {release_id!r}"
    )
    return release_id[len("zmeta-"):]

# Snapshot / duplicate trees are not the canonical stack (CLAUDE.md).
# The list itself is single-sourced in snapshot_exclusions.py: this walker
# and the profile-claims walker had diverged in mechanism and content, and
# a stale worktree tripped this guard while the other stayed immune.
from snapshot_exclusions import is_snapshot_path


def _read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


def _markdown_surfaces() -> list[Path]:
    out = []
    for path in ROOT.rglob("*.md"):
        rel = path.relative_to(ROOT)
        if is_snapshot_path(rel):
            continue
        if rel.parts[0] == "release" and rel.parts[-1].startswith("VALIDATION_REPORT_"):
            # Historical run records. They document what WAS run, so they must
            # not be rewritten - doing so is the A-18 defect, not a fix.
            continue
        out.append(path)
    return sorted(out)


# --------------------------------------------------------------------------
# A-13: no diff total attributed to a moving ref
# --------------------------------------------------------------------------

# "+4920 / -392", "+4802/-392". Unicode minus is what the records actually use.
_DIFF_TOTAL = re.compile(r"\+\d{3,}\s*/\s*[-−–]\s*\d+")
# A git object name is an immutable anchor; a symbolic ref is not.
_IMMUTABLE_ANCHOR = re.compile(r"\b[0-9a-f]{7,40}\b")
_MOVING_REF = re.compile(r"\bHEAD\b")

def unanchored_diff_totals(text: str) -> list[str]:
    """Lines stating a diff total against a moving ref with no immutable anchor.

    A total is acceptable if the same line either carries a commit-id anchor
    (so the figure stays true forever) or does not mention a moving ref at all.
    """
    offenders = []
    for line in text.splitlines():
        if not _DIFF_TOTAL.search(line):
            continue
        if not _MOVING_REF.search(line):
            continue
        if _IMMUTABLE_ANCHOR.search(line):
            continue
        offenders.append(line.strip())
    return offenders


def test_record_diff_totals_are_not_attributed_to_a_moving_ref():
    # Swept over every markdown surface rather than an enumerated record list:
    # a new record file is exactly where the sixth recurrence would land.
    inspected = 0
    offenders: list[tuple[str, str]] = []
    for path in _markdown_surfaces():
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(ROOT).as_posix()
        inspected += len(_DIFF_TOTAL.findall(text))
        offenders.extend((rel, line) for line in unanchored_diff_totals(text))

    # Non-vacuity: if the pattern matches nothing the check is asserting
    # nothing. The records DO carry diff totals; a zero here means the regex
    # rotted, not that the defect is gone.
    assert inspected >= 2, (
        "no diff totals found in the R1-11 records - this pin has gone vacuous; "
        f"inspected={inspected}, update _DIFF_TOTAL"
    )
    assert offenders == [], (
        "a record states a diff total against a moving ref with no immutable "
        "anchor (R1-11 A-13, five recurrences): the figure is false the moment "
        "another commit lands. Either tell the reader to run "
        "`git diff --shortstat`, or anchor the number to a commit id. "
        f"Offenders: {offenders}"
    )


# Deliberately narrow: only a total presented as the OUTPUT OF A NAMED
# COMMAND against a named commit. Widening this to "any total near any hex
# token" was tried and produced two false positives on legitimate content -
# a `git show <sha> --stat` per-commit figure, and the A-13 finding's own
# quotation of the wrong figure it exists to document. A check that cries
# wolf on a correct record is worse than one with a stated blind spot.
# A-13 closure (2026-07-27): a literal-SHA base is accepted alongside
# origin/main, so records can anchor figures to a base that survives the
# push that moves origin/main - and those figures stay verified here.
_COMMAND_TOTAL = re.compile(
    r"git diff --shortstat (origin/main|[0-9a-f]{7,40})\.\.([0-9a-f]{7,40})`?\s*[=→:-]*\s*"
    r"(\d+) files?,?\s*\+(\d+)\s*/\s*[-−–]\s*(\d+)"
)


def anchored_totals(text: str) -> list[tuple[str, str, str, str]]:
    """Totals a doc presents as the output of ``git diff --shortstat``."""
    return _COMMAND_TOTAL.findall(text)


def test_anchored_diff_totals_still_measure_what_they_claim():
    """Anchoring alone is not honesty - the anchored number must also be right.

    Blind spot this closes: ``unanchored_diff_totals`` only checks that a total
    is attributed to an immutable ref, not that it is correct. A wrong number
    frozen against a real commit would pass that check forever.
    """
    import subprocess

    checked = 0
    for path in _markdown_surfaces():
        for base, anchor, files, ins, dels in anchored_totals(
            path.read_text(encoding="utf-8")
        ):
            proc = subprocess.run(
                ["git", "diff", "--shortstat", f"{base}..{anchor}"],
                cwd=ROOT, capture_output=True, text=True,
            )
            if proc.returncode != 0:
                # No git, shallow clone, or origin/main absent. Announce it -
                # a check that silently no-ops is the R2-32 shape.
                import pytest

                pytest.skip(
                    f"cannot resolve {base}..{anchor} in this checkout "
                    f"({proc.stderr.strip()[:120]}); anchored-total correctness "
                    "not verified here"
                )
            got = re.search(
                r"(\d+) files? changed, (\d+) insertions?\(\+\), (\d+) deletions?",
                proc.stdout,
            )
            assert got, f"unparsed shortstat for {anchor}: {proc.stdout!r}"
            assert (files, ins, dels) == got.groups(), (
                f"{path.relative_to(ROOT).as_posix()} states "
                f"{files} files, +{ins}/-{dels} for {base}..{anchor}, but "
                f"git measures {got.group(1)} files, +{got.group(2)}/-{got.group(3)}"
            )
            checked += 1

    assert checked >= 1, (
        "no anchored diff totals found - this pin has gone vacuous; if the "
        "records stopped quoting totals entirely that is fine, but confirm it "
        "rather than letting the regex rot silently"
    )


def test_unanchored_diff_total_detector_actually_fires():
    """The A-13 oracle must reject the exact shape the records used to carry."""
    bad = "surface: **77 files, +4802 / −392** across `origin/main..HEAD`."
    assert unanchored_diff_totals(bad) == [bad]
    anchored = "`git diff --shortstat origin/main..eb41794` = 77 files, +4920 / −392"
    assert unanchored_diff_totals(anchored) == []
    measured = "Run `git diff --shortstat origin/main..HEAD` for the live total."
    assert unanchored_diff_totals(measured) == []


# --------------------------------------------------------------------------
# A-17: documented formal-release build must pass --release-notes
# --------------------------------------------------------------------------

# Capture the COMMAND, not the line. Terminating on a backtick matters: in
# README.md the command sits inline in a bullet whose surrounding prose also
# mentions --release-notes, and a line-scoped oracle was satisfied by that
# prose while the command itself was still broken (caught by revert-simulating
# this very pin).
_BUILD_CMD = re.compile(r"(?:python\s+)?tools[\\/]build_release_package\.py[^\n`]*")
_VERSION_LITERAL = re.compile(r"\d+\.\d+\.\d+")


def _is_historical_command(line: str, current_version: str) -> bool:
    """True when a worked command is pinned to a release other than the current one.

    A command written for an older release is a *record of what was run*, not a
    teaching surface. Rewriting it would falsify history - exactly the A-18
    defect - so it is out of scope here. Placeholder forms (``<version>``) carry
    no literal and stay in scope, because they are always current-facing.
    """
    literals = set(_VERSION_LITERAL.findall(line))
    return bool(literals) and current_version.lstrip("v") not in literals


def formal_builds_without_notes(text: str, current_version: str) -> list[str]:
    """Worked build commands that ask for a formal package but no real notes."""
    offenders = []
    for line in _BUILD_CMD.findall(text):
        if "--release-state formal_release" not in line:
            continue
        if "--release-notes" in line:
            continue
        if _is_historical_command(line, current_version):
            continue
        offenders.append(line.strip())
    return offenders


def test_documented_formal_package_builds_pass_release_notes():
    current_version = manifest_release_version()
    inspected = 0
    offenders: list[tuple[str, str]] = []
    for path in _markdown_surfaces():
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(ROOT).as_posix()
        for line in _BUILD_CMD.findall(text):
            if "--release-state formal_release" not in line:
                continue
            if _is_historical_command(line, current_version):
                continue
            inspected += 1
        offenders.extend(
            (rel, line) for line in formal_builds_without_notes(text, current_version)
        )

    # Non-vacuity floor: README, spec/installation-guide, release/README and
    # tools/README each carry one. Fewer means the locator stopped finding them.
    assert inspected >= 4, (
        "fewer than four documented formal_release build commands found - this "
        f"pin has gone vacuous (inspected={inspected}); update _BUILD_CMD"
    )
    assert offenders == [], (
        "a documented build-then-validate sequence builds a formal_release "
        "package without --release-notes (R1-11 A-17). build_release_package.py "
        "then copies RELEASE_NOTES_TEMPLATE.md verbatim and "
        "validate_release_package.py refuses it with "
        "RELEASE_PACKAGE_NOTES_PLACEHOLDER, so the documented pair cannot "
        f"succeed as written. Offenders: {offenders}"
    )


def test_formal_build_detector_actually_fires():
    current = manifest_release_version()
    bare = current.lstrip("v")
    bad = (
        "python tools/build_release_package.py --manifest release/zmeta-release-manifest.yaml "
        f"--output-dir release/package-{current} --release-id zmeta-{current} "
        "--release-state formal_release --no-signatures"
    )
    assert formal_builds_without_notes(bad, current) == [bad]
    fixed = bad + f" --release-notes release/RELEASE_NOTES_{current}.md"
    assert formal_builds_without_notes(fixed, current) == []
    # A non-formal (dry-run / template) build is out of scope and must not trip.
    dry = (
        "python tools/build_release_package.py --manifest release/zmeta-release-manifest.yaml "
        "--output-dir release/package --dry-run --no-signatures"
    )
    assert formal_builds_without_notes(dry, current) == []
    # A worked command pinned to an OLDER release is a historical record and is
    # deliberately not rewritten (A-18); it must not be reported.
    historical = bad.replace(bare, "1.1.12").replace(current, "v1.1.12")
    assert formal_builds_without_notes(historical, current) == []


# --------------------------------------------------------------------------
# A-18: a diverged command inventory must stay labelled historical
# --------------------------------------------------------------------------

_TOOL_INVOCATION = re.compile(r"tools[\\/]([a-z_0-9]+)\.py")
_HANDOFF = "docs/zmeta_refinement_handoff.md"


def _newest_validation_report() -> Path:
    reports = sorted(
        (ROOT / "release").glob("VALIDATION_REPORT_v*.md"),
        key=lambda p: [int(n) for n in re.findall(r"\d+", p.stem)],
    )
    assert reports, "no release/VALIDATION_REPORT_v*.md found"
    return reports[-1]


def _tool_set(text: str) -> set[str]:
    return set(_TOOL_INVOCATION.findall(text))


def handoff_inventory_block(text: str) -> tuple[str, str]:
    """Return (preamble, block) for the handoff's validation command inventory.

    The inventory is the FIRST fenced block after the marker that actually runs
    the conformance validator - anchoring on the fence language would break the
    moment a reproduction snippet is added above it, which is exactly what
    happened while writing this pin. The preamble is everything between the
    marker and that fence: the place the historical label has to live for a
    reader to see it before the block.
    """
    start = text.find("Validation command inventory")
    assert start != -1, "handoff validation command inventory marker not found"
    tail = text[start:]
    for match in re.finditer(r"```[a-z]*\n(.*?)```", tail, re.DOTALL):
        block = match.group(1)
        if "validate_conformance" not in block:
            continue
        return tail[: match.start()], block
    raise AssertionError(
        "handoff validation command inventory block not found (no fenced block "
        "after the marker runs tools/validate_conformance.py)"
    )


def inventory_divergence_is_unlabelled(text: str, current_report_text: str) -> list[str]:
    """Non-empty when a diverged inventory is not labelled historical."""
    preamble, block = handoff_inventory_block(text)
    drift = sorted(_tool_set(block) - _tool_set(current_report_text))
    if not drift:
        return []
    if "historical" in preamble.lower():
        return []
    return drift


def test_handoff_validation_inventory_labelled_historical_while_it_diverges():
    text = _read(_HANDOFF)
    report = _newest_validation_report()
    report_text = report.read_text(encoding="utf-8")

    preamble, block = handoff_inventory_block(text)
    # Non-vacuity: the block must actually contain commands, otherwise the
    # divergence set is empty for the wrong reason and the check is hollow.
    assert len(_tool_set(block)) >= 5, (
        "handoff validation inventory block parsed to fewer than five tool "
        f"invocations ({sorted(_tool_set(block))}) - this pin has gone vacuous"
    )

    drift = inventory_divergence_is_unlabelled(text, report_text)
    assert drift == [], (
        f"{_HANDOFF}'s validation command inventory runs tools that "
        f"{report.name} does not ({drift}), so it is NOT the current per-release "
        "inventory - it must stay labelled 'historical' in the prose directly "
        "above the block (R1-11 A-18: a doc-currency sweep replaced a true "
        "historical label with a false present-tense claim)."
    )


def test_inventory_divergence_detector_actually_fires():
    """The A-18 oracle must reject the exact re-labelling that caused A-18."""
    diverged_block = (
        "Validation command inventory (run per release; version literals track "
        "the release being cut - unchanged in shape since):\n\n"
        "```powershell\n"
        "python tools\\validate_conformance.py --strict\n"
        "python tools\\validate_examples.py --strict --require-all\n"
        "python tools\\lint_policy_risk_modes.py\n"
        "python tools\\validate_future_roadmap.py\n"
        "python tools\\check_compat.py --target v1.1.12 --strict\n"
        "python tools\\measure_packet_size.py --summary-only\n"
        "```\n"
    )
    report = (
        "python tools/validate_conformance.py --strict\n"
        "python tools/validate_examples.py --strict --require-all\n"
        "python tools/lint_policy_risk_modes.py\n"
        "python tools/check_compat.py --target v1.1.16 --strict\n"
        "python tools/measure_packet_size.py --summary-only\n"
        "python tools/compute_contract_hash.py\n"
    )
    assert inventory_divergence_is_unlabelled(diverged_block, report) == [
        "validate_future_roadmap"
    ]
    labelled = diverged_block.replace(
        "unchanged in shape since", "historical; superseded by the current report"
    )
    assert inventory_divergence_is_unlabelled(labelled, report) == []
