"""The conformance gate runs every stage it is asked for, then reports them all.

Until 2026-11-14 `tools/validate_conformance.py` exited at its first failing
stage. On an unreleased branch the release manifest is stale on purpose, so
`--kernel-gate` stopped at the manifest pins and the stages after them never
ran: "red for the manifest pins alone" (the governance Branching section) was
an inference, not something the gate's output showed. The gate now records
each stage's result, prints one `conformance stages:` line naming every stage
when any failed, and exits with the first failing stage's code, which is the
code the early exit gave. A passing run prints exactly what it printed before.
"""

import importlib.util
import inspect
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location(
    "validate_conformance_every_stage", ROOT / "tools" / "validate_conformance.py"
)
validate_conformance = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(validate_conformance)

SUMMARY_PREFIX = "conformance stages:"
GATE_STAGES = ["must_pass_must_fail"] + [
    flag for flag in validate_conformance.KERNEL_GATE_CHECKS if flag != "strict"
]


def _run(*argv):
    return subprocess.run(
        [sys.executable, "tools/validate_conformance.py", *argv],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def _summary_lines(stdout):
    return [line for line in stdout.splitlines() if line.startswith(SUMMARY_PREFIX)]


def _stages_named(summary_line):
    """[(stage, 'ok' or 'FAIL (exit N)'), ...] from the summary line."""
    body = summary_line[len(SUMMARY_PREFIX):].strip()
    out = []
    for part in body.split(", "):
        name, _, status = part.partition(" ")
        out.append((name, status))
    return out


# The two stages that read the committed release manifest. Between cuts they
# are red by design, for the stale manifest's pins
# (docs/zmeta_change_governance.md, Branching), and no other stage may be.
PIN_STAGES = ("release_manifest", "release_package")
_HASH = r"sha256:[0-9a-f]{64}"
_MISMATCH = rf"expected {_HASH}, got {_HASH}"
# Every line the two stages print for a stale pin, by stage. The codes and
# messages are those of tools/validate_release_manifest.py; the package stage
# validates the same manifest first and reports each of its issues as
# RELEASE_PACKAGE_MANIFEST_INVALID with the manifest's message
# (tools/validate_release_package.py, _load_valid_manifest).
# RELEASE_MANIFEST_SELF_HASH_MISMATCH is not accepted. The manifest's own hash
# covers the manifest's content only (tools/build_release_manifest.py,
# canonical_manifest_bytes), so a stale pin does not move it; it moves when the
# committed manifest is edited by hand or the builder's canonical form changes,
# and either is more than a stale pin.
PIN_LINE_PATTERNS = {
    "release_manifest": [
        re.compile(rf"FAIL RELEASE_MANIFEST_ARTIFACT_HASH_MISMATCH item=\S+: {_MISMATCH}"),
        re.compile(rf"FAIL RELEASE_MANIFEST_GROUP_HASH_MISMATCH item=\w+: {_MISMATCH}"),
        re.compile(rf"FAIL RELEASE_MANIFEST_TOP_LEVEL_HASH_MISMATCH item=\w+: \w+_hash {_MISMATCH}"),
        re.compile(rf"FAIL RELEASE_MANIFEST_BUNDLE_HASH_MISMATCH: {_MISMATCH}"),
    ],
    "release_package": [
        re.compile(rf"FAIL RELEASE_PACKAGE_MANIFEST_INVALID(?: item=\S+)?: (?:\w+_hash )?{_MISMATCH}"),
    ],
}


def _red_beyond_the_pins(stages, stdout):
    """What in a red gate's output is more than the stale release pins.

    `stages` is the summary line read by _stages_named. The result is empty
    when the failing stages are within PIN_STAGES, every output line that
    begins "FAIL " is a hash mismatch printed by one of the failing pin
    stages, and each failing pin stage printed at least one such line.
    Otherwise it lists each thing that is more, one string per item.
    """
    failing = [name for name, status in stages if status != "ok"]
    beyond = [f"stage {name} fails" for name in failing if name not in PIN_STAGES]
    if not failing:
        beyond.append("no stage fails")
    failing_pins = [name for name in PIN_STAGES if name in failing]
    printed = dict.fromkeys(failing_pins, 0)
    for line in stdout.splitlines():
        if not line.startswith("FAIL "):
            continue
        stage = next(
            (
                name
                for name in failing_pins
                if any(pattern.fullmatch(line) for pattern in PIN_LINE_PATTERNS[name])
            ),
            None,
        )
        if stage is None:
            beyond.append(f"not a hash mismatch of a failing release stage: {line}")
        else:
            printed[stage] += 1
    beyond.extend(f"stage {name} fails with no hash-mismatch line" for name, count in printed.items() if not count)
    return beyond


def _failing_must_pass_file(tmp_path):
    """One must-pass fixture made schema-invalid, so the core stage fails."""
    first = (ROOT / "conformance" / "must-pass.jsonl").read_text(encoding="utf-8").splitlines()[0]
    item = json.loads(first)
    del item["event"]["event"]["event_type"]
    path = tmp_path / "must-pass-broken.jsonl"
    path.write_text(json.dumps(item) + "\n", encoding="utf-8")
    return path


def test_a_failing_core_stage_does_not_stop_the_stages_after_it(tmp_path):
    """T1. The core stage fails; the two sub-checks after it still run."""
    result = _run(
        "--strict",
        "--pass-file",
        str(_failing_must_pass_file(tmp_path)),
        "--bad-events",
        "--adapter-harness",
    )
    out = result.stdout
    assert result.returncode == 1, out + result.stderr
    assert "bad-event corpus ok" in out, out
    assert "adapter conformance ok" in out, out
    assert "conformance ok pass=" not in out, out
    summaries = _summary_lines(out)
    assert len(summaries) == 1, out
    assert _stages_named(summaries[0]) == [
        ("must_pass_must_fail", "FAIL (exit 1)"),
        ("bad_events", "ok"),
        ("adapter_harness", "ok"),
    ]


def test_the_core_stage_exits_1_however_many_fixtures_fail(tmp_path):
    """T1b. The old gate exited 1 for any number of failing fixtures. Recording
    the count instead would exit 2 here, and 256 failing fixtures would exit
    with status 0 on Linux: a red gate read as green."""
    first = (ROOT / "conformance" / "must-pass.jsonl").read_text(encoding="utf-8").splitlines()[:2]
    broken = []
    for line in first:
        item = json.loads(line)
        del item["event"]["event"]["event_type"]
        broken.append(json.dumps(item))
    path = tmp_path / "must-pass-two-broken.jsonl"
    path.write_text("\n".join(broken) + "\n", encoding="utf-8")
    result = _run("--strict", "--pass-file", str(path), "--bad-events")
    assert result.returncode == 1, result.stdout + result.stderr
    assert sum(1 for line in result.stdout.splitlines() if line.startswith("FAIL pass ")) == 2, result.stdout
    assert _stages_named(_summary_lines(result.stdout)[0]) == [
        ("must_pass_must_fail", "FAIL (exit 1)"),
        ("bad_events", "ok"),
    ]


def test_a_passing_run_prints_what_it_always_printed():
    """T2. The success path is unchanged: no summary line, the ok line last."""
    result = _run("--strict", "--bad-events")
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.strip().splitlines()[-1].startswith("conformance ok pass=")
    assert not _summary_lines(result.stdout)


def test_the_exit_code_is_the_first_failing_stages():
    """T3. The early exit returned the first failing stage's code; so must the
    end of the run, or a later stage's code would change the exit status."""
    stages = validate_conformance._Stages()
    for name, code in (("a", 0), ("b", 2), ("c", 0), ("d", 3), ("e", 1)):
        stages.record(name, code)
    assert stages.exit_code() == 2
    assert stages.summary() == (
        "conformance stages: a ok, b FAIL (exit 2), c ok, d FAIL (exit 3), e FAIL (exit 1)"
    )
    clean = validate_conformance._Stages()
    clean.record("a", 0)
    clean.record("b", None)
    assert clean.exit_code() == 0
    truthy = validate_conformance._Stages()
    truthy.record("a", True)
    assert truthy.exit_code() == 1
    assert truthy.summary() == "conformance stages: a FAIL (exit 1)"


def test_the_run_ends_with_the_first_failing_stages_code(capsys):
    """T3b. _finish exits with the first failing stage's code, not a fixed 1,
    and prints the summary; with no failure it prints the ok line and returns."""
    stages = validate_conformance._Stages()
    stages.record("a", 0)
    stages.record("b", 2)
    stages.record("c", 1)
    try:
        validate_conformance._finish(stages, 3, 4)
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("_finish did not exit on a failing stage")
    assert capsys.readouterr().out.strip() == "conformance stages: a ok, b FAIL (exit 2), c FAIL (exit 1)"
    clean = validate_conformance._Stages()
    clean.record("a", 0)
    validate_conformance._finish(clean, 3, 4)
    assert capsys.readouterr().out.strip() == "conformance ok pass=3 fail=4"


def test_no_stage_block_exits_early():
    """T4. main() never exits; every stage block records its result, and the one
    exit is in _finish, after every stage has run."""
    source = inspect.getsource(validate_conformance.main)
    for exit_call in ("SystemExit", "sys.exit(", "exit(", "os._exit("):
        assert exit_call not in source, f"main() calls {exit_call}: a stage could exit before the others run"
    assert "_finish(stages, pass_total, fail_total)" in source
    finish = inspect.getsource(validate_conformance._finish)
    assert finish.count("raise SystemExit(") == 1
    blocks = re.split(r"\n    if args\.", source)[1:]
    flags = [block.split(":", 1)[0] for block in blocks]
    sub_checks = [flag for flag in validate_conformance.KERNEL_GATE_CHECKS if flag != "strict"]
    assert [flag for flag in flags if flag in sub_checks] == sub_checks
    for flag, block in zip(flags, blocks):
        if flag in sub_checks:
            assert "stages.record(" in block, f"the {flag} block does not record its result"
    assert source.count("stages.record(") == len(sub_checks) + 1


def test_the_kernel_gate_reads_out_every_stage():
    """T5. Between cuts the gate is red on the manifest pins; it must still name
    every stage, so the reader can see whether the pins are the only red. At a
    cut it is green and prints the ok line.

    When the gate is red, the red must be the pins alone: the failing stages
    are within release_manifest and release_package, and every line that
    begins "FAIL " is a hash mismatch of a failing one of them
    (_red_beyond_the_pins). A listed artifact reported missing, a missing
    group or field, a template defect, or any third failing stage turns this
    test red. A consequence follows: a branch that renames or removes a
    manifest-listed file turns this test red until the cut regenerates the
    manifest, because the gate reports the file missing, which is not a hash
    mismatch. Until this change the test passed when any further stage
    failed, and a defect inside the two red stages was one more line among
    the hash mismatches."""
    result = _run("--kernel-gate")
    out = result.stdout
    summaries = _summary_lines(out)
    if result.returncode == 0:
        assert out.strip().splitlines()[-1].startswith("conformance ok pass="), out
        assert not summaries, out
    else:
        assert len(summaries) == 1, out[-2000:]
        named = _stages_named(summaries[0])
        assert [name for name, _ in named] == GATE_STAGES, summaries[0]
        assert any(status != "ok" for _, status in named), summaries[0]
        beyond = _red_beyond_the_pins(named, out)
        assert not beyond, "the gate is red for more than the release pins:\n" + "\n".join(beyond[:20])


_PIN_RED = [
    (stage, "FAIL (exit 1)" if stage in PIN_STAGES else "ok") for stage in GATE_STAGES
]
_H1 = "sha256:" + "a" * 64
_H2 = "sha256:" + "b" * 64
_PIN_LINES = [
    f"FAIL RELEASE_MANIFEST_ARTIFACT_HASH_MISMATCH item=AGENTS.md: expected {_H1}, got {_H2}",
    f"FAIL RELEASE_MANIFEST_GROUP_HASH_MISMATCH item=bad_event_corpus: expected {_H1}, got {_H2}",
    f"FAIL RELEASE_MANIFEST_TOP_LEVEL_HASH_MISMATCH item=bad_event_corpus: "
    f"bad_event_corpus_hash expected {_H1}, got {_H2}",
    f"FAIL RELEASE_MANIFEST_BUNDLE_HASH_MISMATCH: expected {_H1}, got {_H2}",
    f"FAIL RELEASE_PACKAGE_MANIFEST_INVALID item=AGENTS.md: expected {_H1}, got {_H2}",
    f"FAIL RELEASE_PACKAGE_MANIFEST_INVALID item=bad_event_corpus: "
    f"bad_event_corpus_hash expected {_H1}, got {_H2}",
    f"FAIL RELEASE_PACKAGE_MANIFEST_INVALID: expected {_H1}, got {_H2}",
]
_PIN_OUTPUT = "\n".join(["projection conformance ok total=39", *_PIN_LINES, "adapter conformance ok total=53"])


def test_the_pin_classifier_accepts_the_stale_pins_alone():
    """T6. The control for T6b to T6e: the shapes the two stages print for
    stale pins, measured on develop on 2026-11-14, are the pins alone."""
    assert _red_beyond_the_pins(_PIN_RED, _PIN_OUTPUT) == []


NON_HASH_LINES = [
    # a template defect (tools/validate_release_package.py, validate_templates)
    "FAIL RELEASE_PACKAGE_TEMPLATE_MISSING item=release/RELEASE_NOTES_TEMPLATE.md: "
    "template missing: release/RELEASE_NOTES_TEMPLATE.md",
    "FAIL RELEASE_MANIFEST_GROUP_MISSING: missing required artifact group: cot_projection_golden",
    "FAIL RELEASE_MANIFEST_FIELD_MISSING: missing top-level field: policy_hash",
    "FAIL RELEASE_MANIFEST_HASH_ALGORITHM_INVALID: hash_algorithm must be SHA-256, got SHA-1",
    # a hash code whose values are not both hashes
    f"FAIL RELEASE_MANIFEST_GROUP_HASH_MISMATCH item=bad_event_corpus: expected None, got {_H2}",
    f"FAIL RELEASE_PACKAGE_MANIFEST_INVALID: expected None, got {_H2}",
    # a line of the core stage
    "FAIL pass line=1 profile=H code=SCHEMA_INVALID",
    # the manifest's own hash, which a stale pin does not move
    f"FAIL RELEASE_MANIFEST_SELF_HASH_MISMATCH: expected {_H1}, got {_H2}",
    # a valid mismatch body with text after it
    f"FAIL RELEASE_MANIFEST_ARTIFACT_HASH_MISMATCH item=AGENTS.md: expected {_H1}, got {_H2} and more",
    # a hash shorter than SHA-256
    f"FAIL RELEASE_MANIFEST_ARTIFACT_HASH_MISMATCH item=AGENTS.md: expected sha256:{'a' * 12}, got {_H2}",
    # another message before a valid mismatch body
    f"FAIL RELEASE_PACKAGE_MANIFEST_INVALID item=AGENTS.md: listed artifact not found: AGENTS.md, "
    f"expected {_H1}, got {_H2}",
]


@pytest.mark.parametrize("line", NON_HASH_LINES)
def test_the_pin_classifier_rejects_a_line_that_is_not_a_hash_mismatch(line):
    """T6b. A FAIL line that is not a hash mismatch is more than the pins,
    though only the two release stages fail."""
    beyond = _red_beyond_the_pins(_PIN_RED, _PIN_OUTPUT + "\n" + line)
    assert any(line in item for item in beyond), beyond


@pytest.mark.parametrize("line", [
    "FAIL RELEASE_MANIFEST_ARTIFACT_MISSING item=docs/zmeta_audit_playbook.md: "
    "listed artifact not found: docs/zmeta_audit_playbook.md",
    "FAIL RELEASE_PACKAGE_MANIFEST_INVALID item=docs/zmeta_audit_playbook.md: "
    "listed artifact not found: docs/zmeta_audit_playbook.md",
])
def test_the_pin_classifier_rejects_a_missing_artifact(line):
    """T6c. A listed artifact that is missing, in the manifest stage's form
    and in the package stage's, is the line a renamed or removed file
    gives."""
    beyond = _red_beyond_the_pins(_PIN_RED, _PIN_OUTPUT + "\n" + line)
    assert any(line in item for item in beyond), beyond


@pytest.mark.parametrize("third", [stage for stage in GATE_STAGES if stage not in PIN_STAGES])
def test_the_pin_classifier_rejects_a_third_failing_stage(third):
    """T6d. Any stage other than the two release stages failing is more than
    the pins, though every FAIL line is a hash mismatch."""
    stages = [(name, "FAIL (exit 1)" if name == third else status) for name, status in _PIN_RED]
    beyond = _red_beyond_the_pins(stages, _PIN_OUTPUT)
    assert any(third in item for item in beyond), beyond


def test_the_pin_classifier_holds_each_line_to_a_failing_pin_stage():
    """T6e. A pin line is accepted only from a release stage that the summary
    line reads as failing, and a release stage that fails must have printed a
    hash mismatch of its own."""
    manifest_only = [(name, "ok" if name == "release_package" else status) for name, status in _PIN_RED]
    beyond = _red_beyond_the_pins(manifest_only, _PIN_OUTPUT)
    assert any("RELEASE_PACKAGE_MANIFEST_INVALID" in item for item in beyond), beyond
    manifest_lines = "\n".join(line for line in _PIN_LINES if "RELEASE_MANIFEST_" in line)
    assert _red_beyond_the_pins(manifest_only, manifest_lines) == []
    beyond = _red_beyond_the_pins(_PIN_RED, manifest_lines)
    assert any("release_package" in item for item in beyond), beyond
    assert _red_beyond_the_pins([(name, "ok") for name, _ in _PIN_RED], "") != []
