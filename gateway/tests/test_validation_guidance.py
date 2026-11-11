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


def _policy_line_references():
    """Every line reference into policy/semantics.yaml in the guidance file.

    Each is (first, last, note, guidance line). The note is the text in
    parentheses that follows the citation on its own line, where there is one.
    """
    import re

    cite = re.compile(r"policy/semantics\.yaml:(\d+(?:-\d+)?(?:,\s*:?\d+(?:-\d+)?)*)")
    ref = re.compile(r"(\d+)(?:-(\d+))?")
    text = GUIDANCE_PATH.read_text(encoding="utf-8")
    out = []
    for match in cite.finditer(text):
        guidance_line = text.count("\n", 0, match.start()) + 1
        rest = text[match.end():text.find("\n", match.end())]
        note = rest[2:] if rest.startswith(" (") else ""
        for r in ref.finditer(match.group(1)):
            first = int(r.group(1))
            last = int(r.group(2)) if r.group(2) else first
            out.append((first, last, note, guidance_line))
    return out


def _policy_misplaced(references, policy_lines):
    """References that no longer sit on the policy text they were written for.

    Four readings, each a tripwire and none a proof. A range begins on a
    key, or on the comment above one, and never inside a list or on a
    `key: value` line. A range does not stop one line short of the end of
    the list it ends in, which is where it stands after a value is added
    to a list it cited whole. A reference to one line names a line of
    text. Where the citation carries a note that names a policy key or
    code, the first such name is in the cited lines, or is the key whose
    block holds them. A policy edit that inserts a line above the
    citations breaks one of these for most of them. A single line cited
    without a note can still drift unseen, and so can a range that lands
    on another key.
    """
    import re

    def indent(line):
        return len(line) - len(line.lstrip(" "))

    where_named, block_end = {}, {}
    for number, line in enumerate(policy_lines, start=1):
        named = re.match(r"\s*(?:- )?([A-Za-z][A-Za-z0-9_]*)(:)?", line)
        if not named or line.lstrip().startswith("#"):
            continue
        where_named.setdefault(named.group(1), []).append(number)
        if named.group(2):
            end = number
            for later in range(number + 1, len(policy_lines) + 1):
                text = policy_lines[later - 1]
                if text.strip() and indent(text) <= indent(line):
                    break
                end = later
            block_end[number] = end

    bad = []
    for first, last, note, where in references:
        if first < 1 or first > last or last > len(policy_lines):
            bad.append((first, last, where, "outside the policy file"))
            continue
        head = policy_lines[first - 1].strip()
        if first == last:
            if not head:
                bad.append((first, last, where, "one blank line"))
                continue
        elif not (head.endswith(":") or head.startswith("#")):
            bad.append((first, last, where, "a range begins off a key"))
            continue
        else:
            holders = [start for start, end in block_end.items() if start < last <= end]
            if holders and block_end[max(holders)] == last + 1 and policy_lines[last].lstrip().startswith("- "):
                bad.append((first, last, where, "stops one line short of its list"))
                continue
        names = [name for name in re.findall(r"[A-Za-z][A-Za-z0-9]*(?:_[A-Za-z0-9]+)+", note) if name in where_named]
        if names:
            lines = where_named[names[0]]
            inside = any(start <= first and last <= block_end.get(start, start) for start in lines)
            if not inside and not any(first <= number <= last for number in lines):
                bad.append((first, last, where, f"does not hold {names[0]}"))
    return bad


def test_policy_citations_sit_on_their_text():
    # 32 of the 60 references named other text from 2026-11-02, when two
    # commits added five lines to the policy file without moving them, until
    # 2026-11-10. Nothing read the cited lines. On the file as it stood, this
    # reports 21 of the 32.
    policy_lines = (ROOT / "policy" / "semantics.yaml").read_text(encoding="utf-8").splitlines()
    references = _policy_line_references()
    assert len(references) >= 55, "the guidance file's policy citations are no longer found"
    assert _policy_misplaced(references, policy_lines) == []


def test_the_policy_citation_reader_reports_a_reference_moved_off_its_text():
    policy = [
        "semantics:",
        "  alpha_event:",
        "    # why the list exists",
        "    must_not_contain:",
        "      - raw_features",
        "      - data_ref",
        "  codes:",
        "    allowed_reason_codes:",
        "      - CODE_ONE",
        "      - CODE_TWO",
        "    fallback:",
        "      CODE_TWO: CODE_ONE",
        "",
    ]
    placed = [
        (2, 6, "alpha_event.must_not_contain: raw_features, data_ref)", 1),
        (3, 6, "", 2),
        (9, 9, "CODE_ONE listed in allowed_reason_codes)", 3),
        (10, 10, "listed under allowed_reason_codes)", 4),
        (8, 10, "allowed_reason_codes, both values)", 5),
        (12, 12, "", 6),
    ]
    assert _policy_misplaced(placed, policy) == []
    moved = _policy_misplaced(
        [
            (5, 6, "", 7),
            (12, 13, "", 8),
            (10, 10, "CODE_ONE listed in allowed_reason_codes)", 9),
            (11, 12, "allowed_reason_codes, both values)", 10),
            (6, 6, "listed under allowed_reason_codes)", 11),
            (13, 13, "", 12),
            (12, 14, "", 13),
            (8, 9, "allowed_reason_codes, both values)", 14),
        ],
        policy,
    )
    assert [(first, last, why) for first, last, _where, why in moved] == [
        (5, 6, "a range begins off a key"),
        (12, 13, "a range begins off a key"),
        (10, 10, "does not hold CODE_ONE"),
        (11, 12, "does not hold allowed_reason_codes"),
        (6, 6, "does not hold allowed_reason_codes"),
        (13, 13, "one blank line"),
        (12, 14, "outside the policy file"),
        (8, 9, "stops one line short of its list"),
    ]


def _bare_policy_line_numbers(strings):
    """Policy line numbers written after a policy citation in a form the reader above cannot see.

    The reader takes `policy/semantics.yaml:` followed by line references. A
    number written as prose after such a citation ("at :120", "ends at line
    140") is a policy line number too, and nothing moves it when the policy
    file moves: two of them sat wrong on 2026-11-10. This finds a number of
    one to three digits, or a range, that follows "at", "at line", "line",
    "lines" or a colon, when the citation nearest before it in the same
    string is a policy citation and not another file's.
    """
    import re

    policy = re.compile(r"policy/semantics\.yaml:(\d+(?:-\d+)?(?:,\s*:?\d+(?:-\d+)?)*)")
    other = re.compile(r"[\w./-]+\.(?:json|yaml|yml|py|md|proto|jsonl):\d+(?:-\d+)?(?:,\s*:?\d+(?:-\d+)?)*")
    token = re.compile(r"POLICYCITE|FILECITE|(?:\bat |\bat line |\blines? |:)(:?\d{1,3}(?:-\d{1,3})?)\b(?![-\d:]|\.\d)")
    found = []
    for text in strings:
        flat = " ".join(text.split())
        stripped = other.sub("FILECITE", policy.sub("POLICYCITE", flat))
        last = None
        for match in token.finditer(stripped):
            if match.group(0) in ("POLICYCITE", "FILECITE"):
                last = match.group(0)
            elif last == "POLICYCITE":
                found.append(match.group(1))
    return found


def test_no_bare_line_number_follows_a_policy_citation():
    # Every policy line number is written in the form the reader above takes,
    # so a later policy edit moves it with the others or that test says so.
    assert _bare_policy_line_numbers(_guidance_strings()) == []


def test_the_bare_number_reader_tells_policy_numbers_from_another_files():
    found = _bare_policy_line_numbers(
        [
            "the list (policy/semantics.yaml:79-141, the full vocabulary; the list ends at line 141)",
            "allowed codes (policy/semantics.yaml:178-190; code registered in the violation list at :121)",
            "the rule (spec/semantics-contract.md:788-796) allows a tolerance of 1 ms at line 794",
            "one key (policy/semantics.yaml:1-3, rf_window_midpoint_tolerance_ms: 1) at 5.6 of the contract",
            "both (policy/semantics.yaml:137,185) and the schema (schema/zmeta-event-1.1.0.schema.json:1958) at line 12",
        ]
    )
    assert found == ["141", ":121"]
