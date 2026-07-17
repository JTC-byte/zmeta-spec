"""Empty-input floors for the JSONL gate tools.

Every gate tool must exit nonzero when a fixture/input file parses to zero
entries — an empty file proves nothing, and a gate that exits 0 on it is a
vacuous check. Each test here shells the tool with an empty temp file and
asserts a nonzero exit plus the guard message; each fails if the corresponding
floor is removed.
"""

import importlib.util
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
TMP_ROOT = ROOT / "pytest-work"

FLOOR_MESSAGE = "an empty file proves nothing"


@pytest.fixture
def workdir():
    path = TMP_ROOT / f"tool-floors-{uuid.uuid4().hex}"
    path.mkdir(parents=True)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)
        try:
            TMP_ROOT.rmdir()
        except OSError:
            pass


@pytest.fixture
def empty_jsonl(workdir):
    path = workdir / "empty.jsonl"
    path.write_text("", encoding="utf-8")
    return path


def _run_tool(*argv):
    return subprocess.run(
        [sys.executable, *argv],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
    )


def _assert_floor(result):
    assert result.returncode != 0, f"expected nonzero exit, got 0:\n{result.stdout}\n{result.stderr}"
    assert FLOOR_MESSAGE in result.stdout, f"missing floor message:\n{result.stdout}\n{result.stderr}"


def test_validate_conformance_empty_pass_file_fails(empty_jsonl):
    result = _run_tool(
        "tools/validate_conformance.py",
        "--pass-file",
        str(empty_jsonl),
        "--fail-file",
        str(ROOT / "conformance" / "must-fail.jsonl"),
    )
    _assert_floor(result)


def test_validate_conformance_empty_fail_file_fails(empty_jsonl):
    result = _run_tool(
        "tools/validate_conformance.py",
        "--pass-file",
        str(ROOT / "conformance" / "must-pass.jsonl"),
        "--fail-file",
        str(empty_jsonl),
    )
    _assert_floor(result)


def test_validate_conformance_success_line_reports_counts():
    result = _run_tool("tools/validate_conformance.py")
    assert result.returncode == 0, f"base conformance gate failed:\n{result.stdout}\n{result.stderr}"
    summary = result.stdout.strip().splitlines()[-1]
    assert summary.startswith("conformance ok pass="), summary
    assert " fail=" in summary, summary


def test_validate_bad_events_empty_fixture_fails(empty_jsonl):
    result = _run_tool("tools/validate_bad_events.py", "--must-fail", str(empty_jsonl))
    _assert_floor(result)


def test_validate_adapter_conformance_empty_fixture_fails(empty_jsonl):
    result = _run_tool("tools/validate_adapter_conformance.py", "--fixtures", str(empty_jsonl))
    _assert_floor(result)


def test_validate_projection_empty_must_pass_fails(empty_jsonl):
    result = _run_tool(
        "tools/validate_projection.py",
        "--must-pass",
        str(empty_jsonl),
        "--must-fail",
        str(ROOT / "conformance" / "profile-projection" / "must-fail.jsonl"),
        "--quiet",
    )
    _assert_floor(result)


def test_validate_projection_empty_must_fail_fails(empty_jsonl):
    result = _run_tool(
        "tools/validate_projection.py",
        "--must-pass",
        str(ROOT / "conformance" / "profile-projection" / "must-pass.jsonl"),
        "--must-fail",
        str(empty_jsonl),
        "--quiet",
    )
    _assert_floor(result)


def test_validate_precision_policy_empty_must_pass_fails(empty_jsonl):
    result = _run_tool(
        "tools/validate_precision_policy.py",
        "--must-pass",
        str(empty_jsonl),
        "--must-fail",
        str(ROOT / "conformance" / "profile-precision" / "must-fail.jsonl"),
        "--quiet",
    )
    _assert_floor(result)


def test_validate_precision_policy_empty_must_fail_fails(empty_jsonl):
    result = _run_tool(
        "tools/validate_precision_policy.py",
        "--must-pass",
        str(ROOT / "conformance" / "profile-precision" / "must-pass.jsonl"),
        "--must-fail",
        str(empty_jsonl),
        "--quiet",
    )
    _assert_floor(result)


@pytest.mark.parametrize("empty_flag", ["--compact", "--protobuf", "--gateway"])
def test_validate_encoding_negative_empty_fixture_file_fails(empty_jsonl, empty_flag):
    fixture_dir = ROOT / "conformance" / "encoding-negative"
    args = {
        "--compact": str(fixture_dir / "compact-must-fail.jsonl"),
        "--protobuf": str(fixture_dir / "protobuf-must-fail.jsonl"),
        "--gateway": str(fixture_dir / "gateway-must-fail.jsonl"),
    }
    args[empty_flag] = str(empty_jsonl)
    result = _run_tool(
        "tools/validate_encoding_negative.py",
        "--compact",
        args["--compact"],
        "--protobuf",
        args["--protobuf"],
        "--gateway",
        args["--gateway"],
        "--quiet",
    )
    _assert_floor(result)


def test_validate_empty_input_file_fails(empty_jsonl):
    result = _run_tool("tools/validate.py", "--file", str(empty_jsonl), "--profile", "H")
    _assert_floor(result)


def test_check_compat_empty_input_file_fails(empty_jsonl):
    result = _run_tool("tools/check_compat.py", str(empty_jsonl))
    _assert_floor(result)


def _load_validate_examples():
    path = ROOT / "tools" / "validate_examples.py"
    spec = importlib.util.spec_from_file_location("zmeta_validate_examples_floors", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_validate_examples_strict_require_all_fails_on_empty_registered_corpus(workdir, capsys):
    validate_examples = _load_validate_examples()
    examples_dir = workdir / "examples"
    examples_dir.mkdir()
    (examples_dir / "empty-corpus.jsonl").write_text("", encoding="utf-8")

    result = validate_examples.run(
        strict=True,
        require_all=True,
        root=workdir,
        example_map=[("examples/empty-corpus.jsonl", "L")],
    )

    out = capsys.readouterr().out
    assert result != 0, out
    assert FLOOR_MESSAGE in out


def test_validate_examples_strict_require_all_passes_on_real_corpus(workdir, capsys):
    validate_examples = _load_validate_examples()
    examples_dir = workdir / "examples"
    examples_dir.mkdir()
    shutil.copy2(
        ROOT / "examples" / "encoding-roundtrip.jsonl",
        examples_dir / "real-corpus.jsonl",
    )

    result = validate_examples.run(
        strict=True,
        require_all=True,
        root=workdir,
        example_map=[("examples/real-corpus.jsonl", "L")],
    )

    out = capsys.readouterr().out
    assert result == 0, out
