"""The advisory guidance file: coverage, shape, and the advisory guarantee.

Field evidence (doctrine log F1-04) showed an author hitting a bare code
roughly five times out of six, and the code naming their exact failure never
speaking because the schema fired first with a raw internal message. The
guidance file closes that gap, under one hard constraint: guidance may never
become a compliance surface. These tests pin the three properties that keep
that true. The coverage test also forces every future minted code to arrive
with its hint, because a bare code is the defect this system exists to
remove.

The line citations. The guidance file cites other files by line, and an
edit that adds lines to a cited file moves the text out from under its
citations. Three readers hold three families. The contract citations and
the policy citations sit on their text. Every citation into the code
registry names the whole block of a code its entry is about, and an entry
that cites the registry cites its own code's block; an entry that makes no
line reference into the registry is outside the rule. Four references that
stand as part of a block or begin on a comment are listed in
REGISTRY_PARTIAL_CITATIONS, each pinned to its exact range and to the text
of the line it begins on, and one whose line no longer holds that text is
reported. Against the registry rule, every whole-range shift of any
distance inside the registry and every end-only change of one to three
lines is reported except one class: a second reference in an entry moved
onto the entry's own block, or onto the block of a code the entry's text
names (the one such shift found is COMMAND_TASK_TYPE_INVALID's
EVENT_SUBTYPE_MISMATCH reference moved onto its own code).

No general rule reads the citations into gateway/src/validators.py,
gateway/src/gateway.py, the schemas, the tools or the adapters. Twelve
named rows read the first cited line of a chosen few, and only a substring
of it; a row whose text stands at more than one place in its file passes
when the citation moves to another copy, and a change to the end of a
range is invisible to every row. Any other shift of those citations,
including a whole function's citation moved by a few lines, passes these
tests. The seeded review of 2026-11-14 measured this on the first six
rows: of 219 mutants that shift a validators.py or gateway.py citation by
two lines, three were caught. Those 219 citations carry 223 line
references, since three of them hold more than one; measured again on
2026-11-16, with each reference shifted two lines down, or two lines up, 3
of the 223 are caught by the first six rows. The six rows added since read
six more citations and leave the class as it was: all twelve catch 9 of the
223.
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


def _registry_line_references(text=None):
    """Every line reference into policy/violation-codes.yaml, with the entry that makes it.

    Each is (first, last, entry code, the entry's whole text, guidance line).
    The entry is a `- code:` entry of the guidance list or a `- id:` entry of
    the structural rules; for an `- id:` entry the code is None. With text,
    the references are read from that text instead of the guidance file.
    """
    import re

    cite = re.compile(r"policy/violation-codes\.yaml:(\d+(?:-\d+)?(?:,\s*:?\d+(?:-\d+)?)*)")
    ref = re.compile(r"(\d+)(?:-(\d+))?")
    if text is None:
        text = GUIDANCE_PATH.read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    entries = {}
    for section in ("guidance", "structural_rules"):
        for entry in data.get(section) or []:
            entries[entry.get("code") or entry.get("id")] = " ".join(_strings_of(entry))
    starts = [(m.start(), m.group(1), m.group(2)) for m in re.finditer(r"^  - (code|id): *(\S+)", text, re.M)]
    out = []
    for match in cite.finditer(text):
        owner = [(kind, key) for start, kind, key in starts if start < match.start()]
        if not owner:
            continue
        kind, key = owner[-1]
        guidance_line = text.count("\n", 0, match.start()) + 1
        for r in ref.finditer(match.group(1)):
            first = int(r.group(1))
            last = int(r.group(2)) if r.group(2) else first
            out.append((first, last, key if kind == "code" else None, entries[key], guidance_line))
    return out


def _strings_of(node):
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for value in node.values():
            yield from _strings_of(value)
    elif isinstance(node, list):
        for value in node:
            yield from _strings_of(value)


def _registry_blocks(registry_lines):
    """Each code's block in the registry: code -> (its `- code:` line, the block's last line).

    A block is the `- code:` line and the lines under it indented deeper,
    up to the next code, comment or blank line.
    """
    import re

    blocks = {}
    current = None
    for number, line in enumerate(registry_lines, 1):
        match = re.match(r"^(\s*)- code: *(\S+)", line)
        if match:
            current = (match.group(2), len(match.group(1)))
            blocks[current[0]] = [number, number]
        elif (
            current
            and line.strip()
            and not line.lstrip().startswith("#")
            and len(line) - len(line.lstrip()) > current[1]
        ):
            blocks[current[0]][1] = number
        else:
            current = None
    return {code: tuple(span) for code, span in blocks.items()}


# Registry references that, as they stand, name part of a block or begin on
# the comment above a code. Each is (entry code, first, last), pinned to its
# exact range and to the stripped text of the line it begins on, with the
# reason it is partial beside it. Once its numbers change, the rule reads it
# like any other; once the registry moves its text, the rule reports it; and
# once it is put right it must leave this list.
REGISTRY_PARTIAL_CITATIONS = {
    ("INFERENCE_HAS_FUSION_STATE", 28, 28):  # the code line only, without its severity line
        "- code: INFERENCE_HAS_FUSION_STATE",
    ("RF_WINDOW_PAIRING_INVALID", 56, 56):  # the code line only, without its severity line
        "- code: RF_WINDOW_PAIRING_INVALID",
    ("RF_WINDOW_MIDPOINT_INVALID", 114, 114):  # RF_WINDOW_MIDPOINT_MISMATCH's code line only
        "- code: RF_WINDOW_MIDPOINT_MISMATCH",
    ("NON_FINITE_VALUE", 122, 129):  # begins on the comment above the code
        "# R1-11-01 Class B batch, maintainer-adjudicated 2026-08-09 at occurrence",
}


def _registry_misplaced(references, registry_lines, partial=()):
    """References into the code registry that do not name a whole block the entry is about.

    The rule, from the seeded review of 2026-11-14. A reference begins on a
    `- code:` line and ends on the last line of a code's block. A reference
    that holds the entry's own code names exactly that code's block, and an
    entry that cites the registry cites its own code's block; an entry that
    makes no line reference into the registry is outside the rule. A
    reference that does not hold the entry's code holds only codes the
    entry's text names.

    `partial` maps (entry code, first, last) to the stripped text of the line
    `first`, from a reading of the tests on 2026-11-16. A listed reference is
    read for its bounds, then for that text, which the line must equal, and,
    when it spans more than one line, for ending on the last line of a code's
    block. One that fails any of these is reported and earns its entry no
    credit for its own block; one that passes counts as its entry's own block
    when it holds that code's line. Each listed reference must still be found.

    The rule replaces a weaker reader that read only a reference's first line
    and whether one of its codes was the entry's. On the guidance file before
    the re-anchoring, 33 of the 56 registry references sat below the two
    lines DECODE_AMBIGUOUS added on 2026-11-02 and stood two lines high; the
    weaker reader reported 31 of those 33, and this rule reports all 33.
    """
    import re

    blocks = _registry_blocks(registry_lines)
    ends = {last for _first, last in blocks.values()}
    bad = []
    first_reference = {}
    cites_own = set()
    found_partial = set()
    for first, last, code, entry_text, where in references:
        if code is not None:
            first_reference.setdefault(code, where)
        if (code, first, last) in partial:
            found_partial.add((code, first, last))
            if first < 1 or first > last or last > len(registry_lines):
                bad.append((first, last, where, "outside the registry"))
            elif registry_lines[first - 1].strip() != partial[(code, first, last)]:
                bad.append((first, last, where, "a listed partial reference is off its text"))
            elif first < last and last not in ends:
                bad.append((first, last, where, "ends inside a code's block"))
            elif code in blocks and first <= blocks[code][0] <= last:
                cites_own.add(code)
            continue
        if first < 1 or first > last or last > len(registry_lines):
            bad.append((first, last, where, "outside the registry"))
            continue
        if not registry_lines[first - 1].lstrip().startswith("- code:"):
            bad.append((first, last, where, "begins off a code"))
            continue
        if last not in ends:
            bad.append((first, last, where, "ends inside a code's block"))
            continue
        named = re.findall(r"^\s*- code: *(\S+)", "\n".join(registry_lines[first - 1:last]), re.M)
        if code in named:
            if (first, last) == blocks[code]:
                cites_own.add(code)
            else:
                bad.append((first, last, where, "holds the entry's code with other codes"))
        elif not all(re.search(rf"\b{n}\b", entry_text) for n in named):
            bad.append((first, last, where, "names a code the entry is not about"))
    for code, where in first_reference.items():
        if code in blocks and code not in cites_own:
            bad.append((None, None, where, "the entry does not cite its own code's block"))
    for code, first, last in sorted(set(partial) - found_partial):
        bad.append((first, last, None, "a listed partial reference is no longer found"))
    return bad


def test_registry_citations_name_the_entrys_code():
    # From the pre-cut range review of 2026-11-14: the two lines the
    # DECODE_AMBIGUOUS code added to the registry on 2026-11-02 moved every
    # citation below them two lines off its code. Nothing read them. The
    # whole-block rule is from the seeded review of 2026-11-14.
    registry_lines = CODES_PATH.read_text(encoding="utf-8").splitlines()
    references = _registry_line_references()
    assert len(references) >= 50, "the guidance file's registry citations are no longer found"
    assert _registry_misplaced(references, registry_lines, REGISTRY_PARTIAL_CITATIONS) == []


def test_the_registry_citation_reader_reports_a_reference_moved_off_its_code():
    registry = [
        "violation_codes:",
        "  - code: FIRST_CODE",
        "    severity: fail",
        "  # a note on the second code",
        "  - code: SECOND_CODE",
        "    severity: warn",
        "  - code: THIRD_CODE",
        "    severity: fail",
    ]
    placed = [
        (2, 3, "FIRST_CODE", "about FIRST_CODE", 1),
        (5, 6, "SECOND_CODE", "about SECOND_CODE", 2),
        (4, 6, "SECOND_CODE", "about SECOND_CODE", 3),
        (5, 6, "OTHER_CODE", "OTHER_CODE reaches the producer as SECOND_CODE", 4),
        (7, 8, "THIRD_CODE", "THIRD_CODE follows FIRST_CODE", 5),
        (2, 3, "THIRD_CODE", "THIRD_CODE follows FIRST_CODE", 6),
    ]
    assert _registry_misplaced(placed, registry, {("SECOND_CODE", 4, 6): "# a note on the second code"}) == []
    own = "the entry does not cite its own code's block"
    cases = [
        ([(3, 4, "FIRST_CODE", "about FIRST_CODE", 1)], set(), ["begins off a code", own]),
        ([(5, 6, "FIRST_CODE", "FIRST_CODE reaches the producer as SECOND_CODE", 1)], set(), [own]),
        ([(2, 2, "FIRST_CODE", "about FIRST_CODE", 1)], set(), ["ends inside a code's block", own]),
        (
            [(2, 6, "FIRST_CODE", "FIRST_CODE and SECOND_CODE", 1)],
            set(),
            ["holds the entry's code with other codes", own],
        ),
        (
            [(2, 3, "FIRST_CODE", "about FIRST_CODE", 1), (5, 6, "FIRST_CODE", "about FIRST_CODE", 2)],
            set(),
            ["names a code the entry is not about"],
        ),
        ([(7, 9, "FIRST_CODE", "about FIRST_CODE", 1)], set(), ["outside the registry", own]),
        (
            [(2, 3, "FIRST_CODE", "about FIRST_CODE", 1)],
            {("FIRST_CODE", 2, 2): "- code: FIRST_CODE"},
            ["a listed partial reference is no longer found"],
        ),
    ]
    for references, partial, expected in cases:
        found = _registry_misplaced(references, registry, partial)
        assert [why for _first, _last, _where, why in found] == expected, references


def test_the_registry_rule_reports_a_doctored_guidance_file():
    # The two classes of change the first form of the reader let through,
    # made on a copy of the guidance file's text: a whole shift onto a
    # neighbouring code that the entry's text names, and an end-only change.
    text = GUIDANCE_PATH.read_text(encoding="utf-8")
    registry_lines = CODES_PATH.read_text(encoding="utf-8").splitlines()
    own = "the entry does not cite its own code's block"
    doctored = [
        (
            '"policy/violation-codes.yaml:72-73 (code SCHEMA_VIOLATION_MISSING_ORIGINAL_EVENT_ID',
            '"policy/violation-codes.yaml:70-71 (code SCHEMA_VIOLATION_MISSING_ORIGINAL_EVENT_ID',
            [own],
        ),
        (
            '      - "policy/violation-codes.yaml:4-5"\n',
            '      - "policy/violation-codes.yaml:4-4"\n',
            ["ends inside a code's block", own],
        ),
    ]
    for old, new, expected in doctored:
        assert text.count(old) == 1, old
        references = _registry_line_references(text.replace(old, new))
        found = _registry_misplaced(references, registry_lines, REGISTRY_PARTIAL_CITATIONS)
        assert [why for _first, _last, _where, why in found] == expected, new


# Listed partial references, from a reading of the tests on 2026-11-16. A
# listed reference is pinned to the text of the line it begins on, read for
# its bounds before that text, held to end on the last line of a code's block
# when it spans more than one line, and given no credit for its entry's own
# block once it is reported. Each row is a label, a synthetic registry, the
# references, the listed references with the text each begins on, and the
# reasons the rule gives.
_LISTED_REGISTRY = [
    "violation_codes:",
    "  - code: FIRST_CODE",
    "    severity: fail",
    "  # a note on the second code",
    "  - code: SECOND_CODE",
    "    severity: warn",
    "  - code: THIRD_CODE",
    "    severity: fail",
]
LISTED_PARTIAL_CASES = [
    (
        "a line added above the note moves a listed range off its text",
        _LISTED_REGISTRY[:3] + ["  # a line added"] + _LISTED_REGISTRY[3:],
        [(4, 6, "SECOND_CODE", "about SECOND_CODE", 1)],
        {("SECOND_CODE", 4, 6): "# a note on the second code"},
        ["a listed partial reference is off its text", "the entry does not cite its own code's block"],
    ),
    (
        "a line added above every code moves a listed code line onto other text",
        _LISTED_REGISTRY[:1] + ["  # a line added"] + _LISTED_REGISTRY[1:],
        [
            (3, 4, "FIRST_CODE", "FIRST_CODE reaches the producer as THIRD_CODE", 1),
            (7, 7, "FIRST_CODE", "FIRST_CODE reaches the producer as THIRD_CODE", 2),
        ],
        {("FIRST_CODE", 7, 7): "- code: THIRD_CODE"},
        ["a listed partial reference is off its text"],
    ),
    (
        "a blank line added above a listed code line leaves it on a blank line",
        _LISTED_REGISTRY[:6] + [""] + _LISTED_REGISTRY[6:],
        [
            (2, 3, "FIRST_CODE", "FIRST_CODE reaches the producer as THIRD_CODE", 1),
            (7, 7, "FIRST_CODE", "FIRST_CODE reaches the producer as THIRD_CODE", 2),
        ],
        {("FIRST_CODE", 7, 7): "- code: THIRD_CODE"},
        ["a listed partial reference is off its text"],
    ),
    (
        "a listed reference past the registry's end is read for its bounds first",
        _LISTED_REGISTRY,
        [(2, 3, "FIRST_CODE", "about FIRST_CODE", 1), (9, 9, "FIRST_CODE", "about FIRST_CODE", 2)],
        {("FIRST_CODE", 9, 9): "- code: FIRST_CODE"},
        ["outside the registry"],
    ),
    (
        "a listed range of several lines ends inside a code's block",
        _LISTED_REGISTRY,
        [(4, 5, "SECOND_CODE", "about SECOND_CODE", 1)],
        {("SECOND_CODE", 4, 5): "# a note on the second code"},
        ["ends inside a code's block", "the entry does not cite its own code's block"],
    ),
]


@pytest.mark.parametrize(
    "registry,references,partial,expected",
    [case[1:] for case in LISTED_PARTIAL_CASES],
    ids=[case[0] for case in LISTED_PARTIAL_CASES],
)
def test_the_registry_rule_reads_a_listed_partial_reference_at_its_text(registry, references, partial, expected):
    found = _registry_misplaced(references, registry, partial)
    assert [why for _first, _last, _where, why in found] == expected


def test_the_registry_rule_reports_a_listed_reference_that_a_registry_edit_moved():
    # From a reading of the tests on 2026-11-16: the incident of 2026-11-02
    # was lines added to the registry under fixed citations. A maintainer who
    # repairs what this rule reports moves the references it reads and leaves
    # the listed ones as written, so each listed reference below the edit must
    # still be reported, whatever text the edit left on the line it begins on.
    text = GUIDANCE_PATH.read_text(encoding="utf-8")
    registry_lines = CODES_PATH.read_text(encoding="utf-8").splitlines()
    references = _registry_line_references(text)
    top = next(n for n, line in enumerate(registry_lines, 1) if line.lstrip().startswith("- code:"))
    listed = [
        (first, last, where)
        for first, last, code, _entry_text, where in references
        if (code, first, last) in REGISTRY_PARTIAL_CITATIONS and first >= top
    ]
    assert listed, "no listed partial reference stands below the registry's first code; this test reads nothing"
    for added in (["  # a line added above every code"], ["  - code: A_NEW_CODE", "    severity: fail"]):
        edited = registry_lines[:top - 1] + added + registry_lines[top - 1:]
        moved = [
            (first, last, code, entry_text, where)
            if (code, first, last) in REGISTRY_PARTIAL_CITATIONS or first < top
            else (first + len(added), last + len(added), code, entry_text, where)
            for first, last, code, entry_text, where in references
        ]
        found = _registry_misplaced(moved, edited, REGISTRY_PARTIAL_CITATIONS)
        for first, last, where in listed:
            assert (first, last, where, "a listed partial reference is off its text") in found, (first, last, added)
        assert [f for f in found if f[0] is not None and (f[0], f[1], f[2]) not in listed] == [], added


# Citations the pre-cut range review of 2026-11-14 read at both ends: each was
# on its text at v1.1.27 and off it after the range. Each row is the entry's
# code, the cited file, which of the entry's references into that file, and
# text its first cited line holds.
NAMED_CITATIONS = [
    ("SCHEMA_INVALID", "gateway/src/validators.py", 0, "def validate_schema("),
    ("INVALID_TIME_FORMAT", "policy/violation-codes.yaml", 0, "- code: INVALID_TIME_FORMAT"),
    ("COMMAND_TASK_TYPE_INVALID", "spec/field-dictionary.md", 0, "`RETURN_TO_BASE`"),
    ("LINK_STATUS_INVALID_REASON_CODE", "adapters/ingress/mavlink/mavlink_to_zmeta_template.py", 0,
     'carried_reason = msg.get("reason_code")'),
    ("PRODUCER_NOT_ALLOWED", "gateway/src/validators.py", 0, "def validate_producer_authority("),
    ("PRODUCER_NOT_ALLOWED", "gateway/src/validators.py", 2, "def _matches_pattern("),
    # From the seeded review of 2026-11-14: citations whose text stands at
    # more than one place now, moved where git's own line mapping from
    # v1.1.27 lands on one of those places. Each first line repeats in its
    # file, so a row here does not tell one copy from another.
    ("SCHEMA_INVALID", "gateway/src/gateway.py", 2, "checks.extend("),
    ("SCHEMA_INVALID", "gateway/src/gateway.py", 3, "fails, warns = _split_violations(violations)"),
    ("TASK_ACK_MISSING_ORIGINAL_EVENT_ID", "gateway/src/validators.py", 2,
     'code = "TASK_ACK_MISSING_ORIGINAL_EVENT_ID"'),
    ("TASK_ACK_MISSING_ORIGINAL_EVENT_ID", "gateway/src/validators.py", 3,
     'code = "TASK_ACK_MISSING_ORIGINAL_EVENT_ID"'),
    ("PROFILE_MISMATCH", "gateway/src/gateway.py", 6, "contract_hashes=contract_hashes,"),
    ("COMMAND_EVIDENCE_UNRESOLVED", "gateway/src/gateway.py", 0, "if timing_state is not None:"),
]


def _first_cited_lines(code, path):
    import re

    cite = re.compile(re.escape(path) + r":(\d+(?:-\d+)?(?:,\s*:?\d+(?:-\d+)?)*)")
    entry = next(entry for entry in _guidance_entries() if entry["code"] == code)
    found = []
    for text in _strings_of(entry):
        for match in cite.finditer(" ".join(text.split())):
            found.extend(int(r.group(1)) for r in re.finditer(r"(\d+)(?:-\d+)?", match.group(1)))
    return found


@pytest.mark.parametrize("code,path,which,expected", NAMED_CITATIONS)
def test_named_citations_sit_on_their_text(code, path, which, expected):
    lines = (ROOT / path).read_text(encoding="utf-8").splitlines()
    firsts = _first_cited_lines(code, path)
    assert len(firsts) > which, f"{code} no longer cites {path}"
    assert expected in lines[firsts[which] - 1], (
        f"{code} cites {path}:{firsts[which]}, which reads {lines[firsts[which] - 1]!r}"
    )
