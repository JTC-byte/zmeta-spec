"""The advisory guidance file: coverage, shape, and the advisory guarantee.

Field evidence (doctrine log F1-04) showed an author hitting a bare code
roughly five times out of six, and the code naming their exact failure never
speaking because the schema fired first with a raw internal message. The
guidance file closes that gap, under one hard constraint: guidance may never
become a compliance surface. These tests pin the three properties that keep
that true. The coverage test also forces every future minted code to arrive
with its hint, because a bare code is the defect this system exists to
remove.
"""

import json
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[2]
TMP_ROOT = ROOT / "pytest-work"

GUIDANCE_PATH = ROOT / "tools" / "validation_guidance.yaml"
CODES_PATH = ROOT / "policy" / "violation-codes.yaml"

DONOR_EXAMPLES = ROOT / "examples" / "zmeta-examples-1.0.jsonl"
DONOR_PROFILE = "H"


@pytest.fixture
def workdir():
    path = TMP_ROOT / f"guidance-{uuid.uuid4().hex}"
    path.mkdir(parents=True)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)
        try:
            TMP_ROOT.rmdir()
        except OSError:
            pass


def _registry_codes():
    data = yaml.safe_load(CODES_PATH.read_text(encoding="utf-8"))
    codes = []

    def walk(node):
        if isinstance(node, dict):
            if isinstance(node.get("code"), str):
                codes.append(node["code"])
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(data)
    return set(codes)


def _guidance_entries():
    data = yaml.safe_load(GUIDANCE_PATH.read_text(encoding="utf-8"))
    return data["guidance"]


def _donor_event():
    with open(DONOR_EXAMPLES, encoding="utf-8") as handle:
        first = handle.readline().strip()
    event = json.loads(first)
    assert event["zmeta_version"] == "1.0", "donor drifted; pick a 1.0 line"
    return event


def _run_validate(path, *extra):
    return subprocess.run(
        [
            sys.executable,
            "tools/validate.py",
            "--file",
            str(path),
            "--profile",
            DONOR_PROFILE,
            *extra,
        ],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
    )


def _failing_event():
    # A prohibited top-level confidence on an observation: the field-evidenced
    # failure shape, guaranteed to violate the 1.0 schema arm.
    event = _donor_event()
    event["confidence"] = 0.9
    return event


def _write_jsonl(workdir, events):
    path = workdir / "events.jsonl"
    path.write_text(
        "".join(json.dumps(event) + "\n" for event in events), encoding="utf-8"
    )
    return path


def test_every_violation_code_has_guidance_and_no_orphans():
    registry = _registry_codes()
    guided = {entry["code"] for entry in _guidance_entries()}
    assert registry - guided == set(), (
        "codes without guidance (a newly minted code must arrive with its "
        f"hint): {sorted(registry - guided)}"
    )
    assert guided - registry == set(), (
        f"guidance for codes the registry does not define: {sorted(guided - registry)}"
    )


def test_guidance_entries_are_well_formed():
    entries = _guidance_entries()
    seen = set()
    for entry in entries:
        code = entry["code"]
        assert code not in seen, f"duplicate guidance entry: {code}"
        seen.add(code)
        assert str(entry["remediation"]).strip(), f"empty remediation: {code}"
        citations = entry.get("citations")
        assert citations and all(str(c).strip() for c in citations), (
            f"guidance without citations: {code}"
        )


def test_guidance_is_advisory_only(workdir):
    path = _write_jsonl(workdir, [_failing_event()])
    with_guidance = _run_validate(path)
    without_guidance = _run_validate(path, "--no-guidance")

    assert with_guidance.returncode == without_guidance.returncode == 1

    def verdict_lines(proc):
        return [
            line
            for line in proc.stdout.splitlines()
            if not line.startswith("  guidance: ")
        ]

    # Identical output apart from the guidance lines: guidance changed no
    # verdict, no count, and no diagnostic it did not add.
    assert verdict_lines(with_guidance) == verdict_lines(without_guidance)
    assert any(
        line.startswith("  guidance: ") for line in with_guidance.stdout.splitlines()
    ), "expected at least one guidance line on a failing event"
    assert not any(
        line.startswith("  guidance: ") for line in without_guidance.stdout.splitlines()
    )


def test_guidance_prints_once_per_code_per_run(workdir):
    path = _write_jsonl(workdir, [_failing_event(), _failing_event()])
    proc = _run_validate(path)
    guidance_lines = [
        line for line in proc.stdout.splitlines() if line.startswith("  guidance: ")
    ]
    fail_lines = [line for line in proc.stdout.splitlines() if line.startswith("FAIL ")]
    assert len(fail_lines) >= 2, "both events should fail"
    assert len(guidance_lines) == len({line for line in guidance_lines}), (
        "the same guidance text printed more than once in one run"
    )


def _contract_line_references():
    """Every contract line reference in the guidance file: (first, last, guidance line)."""
    import re

    cite = re.compile(r"spec/semantics-contract\.md:(\d+(?:-\d+)?(?:,\s*:?\d+(?:-\d+)?)*)")
    ref = re.compile(r"(\d+)(?:-(\d+))?")
    text = GUIDANCE_PATH.read_text(encoding="utf-8")
    out = []
    for match in cite.finditer(text):
        guidance_line = text.count("\n", 0, match.start()) + 1
        for r in ref.finditer(match.group(1)):
            first = int(r.group(1))
            last = int(r.group(2)) if r.group(2) else first
            out.append((first, last, guidance_line))
    return out


def _misplaced(references, contract_lines):
    """References whose edges show they no longer sit on the text they were written for.

    A reference to one line names a line of text, never a blank line. A range
    begins on text, or on the blank line before a code fence it then covers.
    It ends on text, or on the blank line that closes a section it began at the
    heading of. A contract edit that inserts lines above a citation moves the
    citation off its text, and its edges land on blank lines. That is what
    this reads for.
    """
    bad = []
    for first, last, where in references:
        if first < 1 or first > last or last > len(contract_lines):
            bad.append((first, last, where, "outside the contract"))
            continue
        head, tail = contract_lines[first - 1], contract_lines[last - 1]
        if first == last:
            if not head.strip():
                bad.append((first, last, where, "one blank line"))
            continue
        if not head.strip() and not contract_lines[first].startswith("```"):
            bad.append((first, last, where, "begins on a blank line"))
        if not tail.strip() and not head.startswith("#"):
            bad.append((first, last, where, "ends on a blank line"))
    return bad


def test_contract_citations_sit_on_text():
    # 196 of the 219 references sat 1, 7 or 10 lines above their text from
    # 2026-11-02, when three contract sentences were added without moving
    # them, until 2026-11-10. Nothing read the cited lines. This reads their
    # edges, which is where that drift showed.
    contract_lines = (ROOT / "spec" / "semantics-contract.md").read_text(encoding="utf-8").splitlines()
    references = _contract_line_references()
    assert len(references) >= 200, "the guidance file's contract citations are no longer found"
    assert _misplaced(references, contract_lines) == []


def test_the_citation_reader_reports_a_reference_moved_off_its_text():
    contract = ["### 1 A heading", "", "First sentence.", "Second sentence.", "", "```text", "code", "```", ""]
    assert _misplaced([(3, 4, 1), (1, 5, 1), (5, 8, 1), (3, 3, 1)], contract) == []
    moved = _misplaced([(2, 3, 7), (3, 5, 8), (2, 2, 9), (9, 12, 10)], contract)
    assert [(first, last, why) for first, last, _where, why in moved] == [
        (2, 3, "begins on a blank line"),
        (3, 5, "ends on a blank line"),
        (2, 2, "one blank line"),
        (9, 12, "outside the contract"),
    ]


def _bare_contract_line_numbers(strings):
    """Line numbers written after a contract citation in a form the reader above cannot see.

    The reader takes `spec/semantics-contract.md:` followed by line references,
    with continuations written `, :N` or `, N-M`. A number written as prose
    after such a citation ("and 1047-1051", "at 783", "at line 939") is a
    contract line number too, and nothing moved it when the contract moved:
    eight of them sat wrong on 2026-11-10. This finds a three or four digit
    number, or range, that follows "and", "at", "at line", a comma, a bracket
    or a colon, when the citation nearest before it in the same string is a
    contract citation and not another file's.
    """
    import re

    contract = re.compile(r"spec/semantics-contract\.md:(\d+(?:-\d+)?(?:,\s*:?\d+(?:-\d+)?)*)")
    other = re.compile(r"[\w./-]+\.(?:json|yaml|yml|py|md|proto|jsonl):\d+(?:-\d+)?(?:,\s*:?\d+(?:-\d+)?)*")
    token = re.compile(
        r"CONTRACTCITE|FILECITE|(?:\band |\bat |\bat line |, |\(|:)(:?\d{3,4}(?:-\d{3,4})?)\b(?![-\d])"
    )
    found = []
    for text in strings:
        flat = " ".join(text.split())
        stripped = other.sub("FILECITE", contract.sub("CONTRACTCITE", flat))
        last = None
        for match in token.finditer(stripped):
            if match.group(0) in ("CONTRACTCITE", "FILECITE"):
                last = match.group(0)
            elif last == "CONTRACTCITE":
                found.append(match.group(1))
    return found


def _guidance_strings():
    def walk(node):
        if isinstance(node, str):
            yield node
        elif isinstance(node, dict):
            for value in node.values():
                yield from walk(value)
        elif isinstance(node, list):
            for value in node:
                yield from walk(value)

    return list(walk(yaml.safe_load(GUIDANCE_PATH.read_text(encoding="utf-8"))))


def test_no_bare_line_number_follows_a_contract_citation():
    # Every contract line number is written in the form the edge test reads,
    # so a later contract edit moves it with the others or the edge test says so.
    assert _bare_contract_line_numbers(_guidance_strings()) == []


def test_the_bare_number_reader_tells_contract_numbers_from_another_files():
    found = _bare_contract_line_numbers(
        [
            "the rule (spec/semantics-contract.md:1226-1229 for the rule, 1206-1207 and 1867-1884 for the reason)",
            "the schema (schema/zmeta-event-1.1.0.schema.json:1170-1174), IR requires band (line 1250)",
            "written right (spec/semantics-contract.md:1038-1039, :1058-1062; policy/semantics.yaml:4-10) in 2026",
            "a tolerance of 1 ms at 5.6 (spec/semantics-contract.md:788-796)",
        ]
    )
    assert found == ["1206-1207", "1867-1884"]
