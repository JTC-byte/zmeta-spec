"""Forward-facing governed documents must not make claims the tree denies.

R1-11 A-28, the release-surface half. Three layers of this cycle's fix set
landed in prose that no test reads, so a silent revert leaves the whole suite
green and ships the false claim:

- ``release/RELEASE_NOTES_TEMPLATE.md`` hardcoded ``D-003 remains
  roadmap-planned`` under "Known Open Issues". D-003 was closed at the v1.1.12
  cut, so every packaged release note afterwards asserted an open register
  issue that the maintainers had closed. Every consumer checked at audit time
  was existence-only; the manifest pin at ``test_release_manifest.py`` guards
  the *other* producer of that claim.
- ``spec/release-signing-attestation.md`` said ``D-003 remains the roadmap``
  in a governed spec. ``validate_templates`` checks existence and secrets
  only, and the release-manifest hash detects an *unregenerated* edit, never a
  *stale claim*: regenerate the manifest and the lie ships checksummed.
- ``RELEASE_CHECKLIST.md`` gained the step that stops a formal package
  shipping the notes template. A repo-wide grep for ``RELEASE_CHECKLIST``
  across ``*.py`` returned zero hits.

The authority for what is open is the release manifest's
``known_open_issues`` - the machine-readable companion the template itself
names, and the field the package attestation must mirror. So the rule is not
"never say D-003": it is "do not assert an issue is open unless the manifest
says it is".

Scope is deliberately forward-facing. Published release notes, validation
reports, the changelog and the rolling session records under ``docs/`` all
contain true statements about what was open at the time they were written;
rewriting them would falsify history, which is the same exclusion
``test_release_currency.py`` already documents.

Every check asserts a non-vacuity floor before it asserts anything else, and
every matcher is self-tested against the exact text it was written to catch.

What this file cannot see: the open-status matcher is lexical, so a claim
worded around it ("D-003 has not been closed", a bare "D-003: OPEN" table row)
passes. The two guards are deliberately different in kind for that reason -
the template check is structural (any list item at all, whatever it says) and
therefore catches the shape a reintroduced issue list actually takes, while
the lexical one catches the prose sentence. Neither is a substitute for the
manifest's ``known_open_issues``, which remains the authority.
"""

import json
import re
from pathlib import Path

import yaml

from snapshot_exclusions import is_snapshot_path


ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "release" / "zmeta-release-manifest.yaml"
NOTES_TEMPLATE = "release/RELEASE_NOTES_TEMPLATE.md"
CHECKLIST = "RELEASE_CHECKLIST.md"


def _read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


def manifest_open_issues() -> set[str]:
    """Register identifiers the manifest declares open at this baseline."""
    manifest = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
    raw = manifest.get("known_open_issues") or []
    ids = set()
    for entry in raw:
        ids.update(re.findall(r"D-\d{3}", str(entry)))
    return ids


# --------------------------------------------------------------------------
# A register issue may not be asserted open unless the manifest says it is
# --------------------------------------------------------------------------

# Forward-facing surfaces only: things a reader consults to learn the CURRENT
# state. Historical records are excluded above and enumerated here so the
# exclusion is visible rather than implicit in a glob.
def forward_facing_surfaces() -> list[Path]:
    paths = sorted((ROOT / "spec").glob("*.md"))
    paths += sorted(
        path
        for path in (ROOT / "release").glob("*.md")
        if "TEMPLATE" in path.name or path.name == "README.md"
    )
    paths += [
        ROOT / CHECKLIST,
        ROOT / "AGENTS.md",
        ROOT / "README.md",
    ]
    return [path for path in paths if path.is_file()]


# A present-tense assertion that the issue is OPEN. Keyed on the verb that
# governs the identifier, not on other words in the sentence: the reverted
# template line ends "...or closed by maintainers", so a matcher that let a
# closure word anywhere in the sentence rescue the claim was defeated by the
# exact text it existed to catch (verified by revert-simulation).
_OPEN_CLAIM = re.compile(
    r"(D-\d{3})\s+(?:"
    r"remains(?!\s+(?:closed|removed|resolved|out of scope))"
    r"|(?:is|are)\s+(?:still\s+)?(?:open|roadmap[- ]planned)"
    r"|(?:is|are)\s+the\s+roadmap"
    r")[^.]{0,80}",
    re.IGNORECASE,
)
_MENTION = re.compile(r"D-\d{3}")


def _flat(text: str) -> str:
    """One line, so a wrapped sentence matches the same as an unwrapped one."""
    return " ".join(text.split())


def open_status_claims(text: str) -> list[tuple[str, str]]:
    """(identifier, claim text) for every present-tense open-status assertion."""
    return [
        (match.group(1).upper(), match.group(0).strip())
        for match in _OPEN_CLAIM.finditer(_flat(text))
    ]


def test_no_forward_facing_doc_asserts_a_closed_register_issue_is_open():
    open_issues = manifest_open_issues()
    mentions = 0
    offenders: list[tuple[str, str]] = []
    for path in forward_facing_surfaces():
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(ROOT).as_posix()
        mentions += len(_MENTION.findall(text))
        for identifier, claim in open_status_claims(text):
            if identifier in open_issues:
                continue
            offenders.append((rel, claim))

    # Non-vacuity floor: the release-signing spec alone names three register
    # issues and the notes template names one. Fewer means the surface list
    # stopped reaching the documents this guard exists for.
    assert mentions >= 4, (
        "fewer than four register-issue mentions found across the forward-facing "
        f"surfaces (found {mentions}); this guard has gone vacuous - check "
        "forward_facing_surfaces()"
    )
    assert offenders == [], (
        "a forward-facing governed document asserts a register issue is open "
        "that release/zmeta-release-manifest.yaml does not list in "
        f"known_open_issues ({sorted(open_issues) or 'none open'}). State the "
        "closure in the past tense, or list the issue in the manifest. "
        f"Offenders: {offenders}"
    )


def test_open_status_matcher_catches_the_exact_reverted_text():
    # Both retired claims verbatim, plus the phrasings a re-introduction would
    # plausibly use. A matcher that misses these takes the guard above with it.
    must_catch = [
        "- D-003 remains roadmap-planned until future semantic branches are\n"
        "  tracked separately or closed by maintainers.",
        "D-003 remains the roadmap for future versioned semantic branches. A "
        "signed release cannot make future branch candidates valid.",
        "D-003 remains open as roadmap-planned future versioned semantic branches.",
        "D-003 remains `OPEN - ROADMAP PLANNED`.",
        "D-003 is still open pending the roadmap artifact.",
        "D-014 is roadmap-planned.",
    ]
    for text in must_catch:
        assert open_status_claims(text), f"open-status claim slipped through: {text!r}"

    must_not_catch = [
        # The current template and spec text, verbatim in shape.
        "a template that hardcodes an issue keeps asserting it after the "
        "maintainers close it (D-003 was closed at the v1.1.12 cut and shipped "
        'as "roadmap-planned" in every packaged note afterwards).',
        "`spec/future-branch-roadmap.yaml` is the machine-readable roadmap for "
        "future versioned semantic branches; D-003 was closed once that "
        "artifact existed.",
        "D-004 was removed from ZMeta scope.",
        "D-012 should close only after the package framework is verified.",
        "D-003 remains closed as of the v1.1.12 cut.",
        "D-004 remains removed from ZMeta scope.",
    ]
    for text in must_not_catch:
        assert not open_status_claims(text), f"false positive on: {text!r}"


# --------------------------------------------------------------------------
# The notes template must instruct, never enumerate
# --------------------------------------------------------------------------


def known_open_issues_section(text: str) -> str:
    start = text.find("## Known Open Issues")
    assert start != -1, (
        "release/RELEASE_NOTES_TEMPLATE.md no longer has a 'Known Open Issues' "
        "section; the packaged note then states nothing at all about the "
        "register, which the manifest's known_open_issues is supposed to mirror"
    )
    tail = text[start + len("## Known Open Issues") :]
    end = tail.find("\n## ")
    return tail if end == -1 else tail[:end]


def enumerated_issues(section: str) -> list[str]:
    """List items inside the section - i.e. a carried-forward issue list."""
    return [
        line.strip()
        for line in section.splitlines()
        if re.match(r"\s*(?:[-*+]\s|\d+[.)]\s)", line)
    ]


def test_notes_template_known_open_issues_enumerates_nothing():
    section = known_open_issues_section(_read(NOTES_TEMPLATE))
    # Non-vacuity: the section must still carry the instruction, or an empty
    # section would satisfy this check while telling the cutter nothing.
    assert "register" in section.lower(), (
        "the Known Open Issues section no longer tells the cutter to read the "
        "register; an empty section passes the enumeration check while "
        "restoring exactly the silence that let the stale claim survive"
    )
    listed = enumerated_issues(section)
    assert listed == [], (
        "release/RELEASE_NOTES_TEMPLATE.md enumerates issues under 'Known Open "
        "Issues'. A TEMPLATE cannot know what is open at a future cut, so any "
        "list there is by construction a previous release's list carried "
        f"forward - which is how D-003 shipped as open for four releases. {listed}"
    )


def test_enumeration_detector_actually_fires():
    retired = (
        "## Known Open Issues\n\n"
        "- D-003 remains roadmap-planned until future semantic branches are\n"
        "  tracked separately or closed by maintainers.\n\n"
        "## Notes\n"
    )
    section = known_open_issues_section(retired)
    assert enumerated_issues(section)
    # ...and the current instruction-only shape is not reported.
    assert enumerated_issues(known_open_issues_section(_read(NOTES_TEMPLATE))) == []


# --------------------------------------------------------------------------
# The release checklist must name only things that exist
# --------------------------------------------------------------------------

_CHECKLIST_ITEM = re.compile(r"\n(?=- \[[ x]\])")
_SCRIPT = re.compile(r"((?:tools|release)[\\/][a-z_0-9]+\.py)")
_LONG_FLAG = re.compile(r"--[a-z][a-z0-9-]+")
# A violation/failure code: SCREAMING_SNAKE with at least three segments, so
# filenames (SHA256SUMS) and single identifiers (TARGETS) are not swept in.
_FAILURE_CODE = re.compile(r"`([A-Z][A-Z0-9]*(?:_[A-Z0-9]+){2,})`")


def _tool_sources() -> str:
    parts = []
    for folder in ("tools", "gateway/src", "release"):
        parts.extend(
            path.read_text(encoding="utf-8") for path in (ROOT / folder).glob("*.py")
        )
    return "\n".join(parts)


def undeclared_checklist_flags(text: str) -> list[tuple[str, str]]:
    """Flags a checklist item asks for that no script it names declares."""
    offenders = []
    for item in _CHECKLIST_ITEM.split(text):
        scripts = {script.replace("\\", "/") for script in _SCRIPT.findall(item)}
        flags = sorted(set(_LONG_FLAG.findall(item)))
        if not scripts or not flags:
            continue
        declared: set[str] = set()
        for script in scripts:
            path = ROOT / script
            if path.is_file():
                declared.update(_LONG_FLAG.findall(path.read_text(encoding="utf-8")))
        for flag in flags:
            if flag not in declared:
                offenders.append((sorted(scripts)[0], flag))
    return offenders


def test_every_checklist_flag_exists_in_the_script_it_is_given_to():
    text = _read(CHECKLIST)
    inspected = sum(
        len(set(_LONG_FLAG.findall(item)))
        for item in _CHECKLIST_ITEM.split(text)
        if _SCRIPT.search(item)
    )
    # Floor recalibrated 2026-08-10: the kernel gate collapsed from a
    # ten-flag string to the single --kernel-gate alias (apparatus audit,
    # battery single-sourcing), so the checklist legitimately carries fewer
    # literal flags. The floor still guards this test's own vacuity: the
    # alias, the package-build flags, and the examples flags must keep it
    # comfortably above zero.
    assert inspected >= 10, (
        f"only {inspected} checklist flags inspected; the release checklist "
        "carries the --kernel-gate alias plus the package-build and examples "
        "flags, so a count this low means the item parser or the checklist "
        "has broken and this guard has gone vacuous"
    )
    offenders = undeclared_checklist_flags(text)
    assert offenders == [], (
        "RELEASE_CHECKLIST.md tells the cutter to pass a flag the named script "
        f"does not declare, so the documented step cannot run: {offenders}"
    )


def test_checklist_flag_detector_actually_fires():
    doctored = (
        "- [ ] Full kernel-protection conformance passes:\n"
        "      `python tools/validate_conformance.py --strict --no-such-flag`\n"
    )
    assert undeclared_checklist_flags(doctored) == [
        ("tools/validate_conformance.py", "--no-such-flag")
    ]
    real = (
        "- [ ] Full kernel-protection conformance passes:\n"
        "      `python tools/validate_conformance.py --strict --bad-events`\n"
    )
    assert undeclared_checklist_flags(real) == []


def test_every_failure_code_the_checklist_cites_exists_in_the_tooling():
    codes = sorted(set(_FAILURE_CODE.findall(_read(CHECKLIST))))
    assert codes, (
        "the release checklist cites no failure code at all; it used to cite "
        "RELEASE_PACKAGE_NOTES_PLACEHOLDER as the reason the --release-notes "
        "step exists, and without it the step reads as optional housekeeping"
    )
    sources = _tool_sources()
    missing = [code for code in codes if code not in sources]
    assert missing == [], (
        f"RELEASE_CHECKLIST.md cites failure codes that no tool can emit: {missing}"
    )


def test_checklist_still_requires_real_release_notes_on_a_formal_package():
    # Anti-deletion pin for the step itself. It is the human half of a defect
    # the tooling can only catch AFTER the package is built: without
    # --release-notes the builder copies RELEASE_NOTES_TEMPLATE.md verbatim
    # into a package whose metadata claims formal_release.
    text = _read(CHECKLIST)
    assert "--release-notes" in text, (
        "RELEASE_CHECKLIST.md no longer tells the cutter to pass "
        "--release-notes to tools/build_release_package.py; the packaged "
        "RELEASE_NOTES.md then reads 'ZMeta Release Notes Template' with "
        "placeholder provenance beside metadata claiming formal_release"
    )
    assert "RELEASE_PACKAGE_NOTES_PLACEHOLDER" in text, (
        "the checklist no longer names the code the validator refuses with, so "
        "a cutter who hits it has nothing to search for"
    )


# ---------------------------------------------------------------------------
# A doc that names a shipped config and a profile must agree with the file.
#
# `configs/README.md` described `edge-config.json` as a "Profile L edge relay"
# after the file had been changed to H. An operator following that line would
# set the node back to L and reproduce the exact defect the change fixed: a
# 100% silent drop, because profile matching is exact equality -- and L also
# excludes OBSERVATION_EVENT, so no ingress adapter could point at it.
#
# It was found by an independent review AFTER a closeout that had already
# corrected the sibling claims in two other files. That is the fourth instance
# of one claim living in several places and being fixed in some of them, which
# is why this is a check rather than another sweep.
# ---------------------------------------------------------------------------

_PROFILE_CLAIM = re.compile(r"\bProfile\s+([HML])\b")


def _shipped_config_profiles() -> dict[str, str]:
    profiles = {}
    for path in sorted((ROOT / "configs").glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        profile = data.get("profile")
        if isinstance(profile, str):
            profiles[path.name] = profile
    return profiles


def _profile_claims_in_docs():
    """(doc, line_no, config_name, claimed_profile) for every co-mention.

    Scoped to a single line naming BOTH a shipped config and a profile, which
    is the shape that misled -- deliberately narrow, so prose discussing
    profiles in general is untouched.
    """
    configs = _shipped_config_profiles()
    for path in sorted(ROOT.rglob("*.md")):
        rel = path.relative_to(ROOT).as_posix()
        if is_snapshot_path(rel):
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            claim = _PROFILE_CLAIM.search(line)
            if not claim:
                continue
            for name in configs:
                if name in line:
                    yield rel, number, name, claim.group(1)


def test_docs_do_not_misstate_a_shipped_config_profile():
    configs = _shipped_config_profiles()
    assert configs, "no shipped configs declare a profile; this check would be vacuous"

    wrong = [
        (doc, number, name, claimed, configs[name])
        for doc, number, name, claimed in _profile_claims_in_docs()
        if claimed != configs[name]
    ]
    assert wrong == [], (
        "documents state a profile that disagrees with the shipped config: "
        + "; ".join(
            f"{doc}:{number} says {name} is Profile {claimed}, file says {actual}"
            for doc, number, name, claimed, actual in wrong
        )
        + ". Profile matching is exact equality, so a reader who follows the doc "
        "produces a pair that drops every event silently."
    )


def test_the_config_profile_check_would_catch_a_wrong_claim():
    """Red demonstration against the real files, not a synthetic pair."""
    configs = _shipped_config_profiles()
    assert "edge-config.json" in configs
    actual = configs["edge-config.json"]
    wrong = "L" if actual != "L" else "H"
    line = f"- `edge-config.json` - Profile {wrong} edge relay."

    claim = _PROFILE_CLAIM.search(line)
    assert claim and claim.group(1) == wrong
    assert "edge-config.json" in line
    assert claim.group(1) != actual, (
        "the demonstration's doctored claim matches the real config, so it "
        "proves nothing"
    )


# --------------------------------------------------------------------------
# Enum-slot tokens in author-facing prose (PR #8 timing-helper finding)
# --------------------------------------------------------------------------
# AUTHORING.md told authors to supply "source GPS/NTP/PTP metadata": NTP and
# PTP are time_source tokens, GPS is not, and an author who followed the
# prose landed an invalid value that failed schema validation far from its
# cause. A backtick-scoped check would have been vacuous on that exact
# sentence, because GPS was not backticked; the scope here is semantic: any
# line that names a checked slot or uses one of its member tokens has every
# capitalized token on it checked against the union of the slots it invokes.
#
# Known limits, documented rather than engineered around: the matcher is
# line-scoped, so a token on a continuation line that names neither a slot
# nor a member escapes; a line invoking two slots validates against their
# union, so a member of one slot beside the other slot's name passes; and
# lowercase misuse is invisible, because the token pattern is all-caps.
# Each is the price of a lexical check on prose; the schema stays the
# vocabulary authority - members are extracted from both lanes, never
# restated here.

_SLOT_DOC_SURFACES = (
    "adapters/AUTHORING.md",
    "adapters/README.md",
    "adapters/mapping-packs/README.md",
    "adapters/mapping-packs/edge-comms-bladerf/README.md",
    "adapters/mapping-packs/sapient-bsi-flex-335/README.md",
    "docs/zmeta_two_node_quickstart.md",
)
_SLOT_NAMES = ("time_source", "sync_state", "calibration_state", "geo_status")
# Slots whose member tokens are too common in ordinary prose to serve as
# triggers (RF, EO, TRACK_STATE appear in tables everywhere): only a line
# that literally names the slot is checked. The two are paired because a
# line discussing subtypes legitimately names event types beside them, so
# either one triggering admits both vocabularies.
_NAME_ONLY_SLOTS = ("event_subtype", "event_type")
_CAPS_TOKEN = re.compile(r"\b[A-Z][A-Z0-9_]{2,}\b")

# Deliberate non-members that legitimately share a line with a slot. Every
# entry needs a reason; an entry without one is the vacuity coming back.
_SLOT_TOKEN_ALLOWLIST = {
    # Prose acronyms that are not vocabulary claims.
    "UTC",      # timestamps discussed beside timing slots
    "JSON",     # serialization prose
    "YAML",     # serialization prose
    "AUTHORING",  # the guide referring to itself by filename stem
    "SAPIENT",  # the standard's name, not a token; its pack README
                # discusses timing slots in prose that names the standard
    "TIME_STATUS",  # a real schema token from a different vocabulary (the
                    # system event_subtype), legitimately co-mentioned with
                    # timing slots as the periodic timing-report event
}


def _schema_slot_enums():
    every_slot = _SLOT_NAMES + _NAME_ONLY_SLOTS
    enums = {slot: set() for slot in every_slot}
    for lane in ("zmeta-event-1.0.schema.json", "zmeta-event-1.1.0.schema.json"):
        data = json.loads((ROOT / "schema" / lane).read_text(encoding="utf-8"))

        def walk(node):
            if isinstance(node, dict):
                props = node.get("properties")
                if isinstance(props, dict):
                    for slot in every_slot:
                        spec = props.get(slot)
                        if isinstance(spec, dict):
                            values = spec.get("enum") or (
                                [spec["const"]] if "const" in spec else []
                            )
                            enums[slot].update(
                                value for value in values if isinstance(value, str)
                            )
                for value in node.values():
                    walk(value)
            elif isinstance(node, list):
                for value in node:
                    walk(value)

        walk(data)
    return {slot: members for slot, members in enums.items() if members}


def _slot_token_offences(text, enums):
    offences = []
    for number, line in enumerate(text.splitlines(), 1):
        triggered = [
            slot
            for slot in _SLOT_NAMES
            if slot in enums
            and (
                slot in line
                or any(member in _CAPS_TOKEN.findall(line) for member in enums[slot])
            )
        ]
        if any(slot in line for slot in _NAME_ONLY_SLOTS):
            triggered.extend(slot for slot in _NAME_ONLY_SLOTS if slot in enums)
        if not triggered:
            continue
        allowed = set().union(*(enums[slot] for slot in triggered))
        for token in _CAPS_TOKEN.findall(line):
            if token in allowed or token in _SLOT_TOKEN_ALLOWLIST:
                continue
            offences.append((number, "+".join(triggered), token))
    return offences


def test_author_facing_prose_uses_only_schema_tokens_beside_a_slot():
    enums = _schema_slot_enums()
    # Non-vacuity floors: the slots must resolve from the schema, and the
    # scan must actually see slot-invoking lines, or green means blind.
    assert len(enums) >= 3, f"slot extraction collapsed: {sorted(enums)}"
    for slot, members in enums.items():
        assert len(members) >= 2, f"{slot} extracted {members}, too small to be real"

    offences = []
    scanned_lines = 0
    for rel in _SLOT_DOC_SURFACES:
        path = ROOT / rel
        assert path.is_file(), f"scoped surface {rel} is gone; update the list deliberately"
        text = path.read_text(encoding="utf-8")
        hits = _slot_token_offences(text, enums)
        offences.extend((rel, *hit) for hit in hits)
        scanned_lines += sum(
            1
            for line in text.splitlines()
            if any(slot in line for slot in enums)
        )
    assert scanned_lines >= 5, (
        f"only {scanned_lines} slot-naming lines found across the scoped "
        "surfaces; the scan has gone vacuous"
    )
    assert offences == [], (
        "author-facing prose names tokens outside the schema vocabulary "
        "beside a checked slot. Use the schema tokens exactly, or add a "
        f"justified allowlist entry: {offences}"
    )


def test_the_slot_token_matcher_catches_the_exact_authoring_defect():
    """Self-test against the pre-fix text, per this file's own rule.

    The guidance that misled the field pass named no slot, so a
    slot-name-only trigger would miss it. Reproduced with the real
    pre-fix line break: GPS/NTP/PTP sat on the second line, so the
    member tokens NTP and PTP on that same line are what trigger the
    check there, and GPS is the non-member that must be flagged.
    """
    enums = _schema_slot_enums()
    pre_fix = (
        "   `coerce_timing_quality()`'s `UNKNOWN`/`UNSYNCED` fallback is deliberately\n"
        "   degraded; replace it with source GPS/NTP/PTP metadata when available, never\n"
        "   with an invented clean value.\n"
    )
    offences = _slot_token_offences(pre_fix, enums)
    assert [token for (_, _, token) in offences] == ["GPS"], (
        f"the matcher must flag exactly GPS on the pre-fix text, got {offences}"
    )


def test_the_subtype_slot_catches_the_first_contact_defect_class():
    """Self-test for the name-only slots, against the measured field class.

    The first external replay's dominant rejection was a product term
    supplied as event_subtype (a bearing line labeled with a bare LOB-style
    token instead of RF). The slot is name-only triggered, so the exact
    line shape the authoring guide teaches must be checked, and a legal
    pairing of subtype and event type on one line must pass.
    """
    enums = _schema_slot_enums()
    assert "event_subtype" in enums and len(enums["event_subtype"]) >= 8, (
        "event_subtype extraction collapsed; the name-only check is blind"
    )
    bad = 'A bearing line is `event_subtype: LOB` on an OBSERVATION_EVENT.'
    offences = _slot_token_offences(bad, enums)
    assert [token for (_, _, token) in offences] == ["LOB"], (
        f"the matcher must flag exactly LOB, got {offences}"
    )
    good = 'A bearing line is `event_subtype: RF` on an OBSERVATION_EVENT.'
    assert _slot_token_offences(good, enums) == [], (
        "a legal subtype beside its event type must pass"
    )
