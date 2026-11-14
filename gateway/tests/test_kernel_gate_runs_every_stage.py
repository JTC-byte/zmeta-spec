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
    cut it is green and prints the ok line."""
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
