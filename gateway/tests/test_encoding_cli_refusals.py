"""Compact-refusal reporting across the encoding CLI family (R1-11 A-24).

zmeta_compact refuses events it cannot carry honestly (non-1.0
zmeta_version, out-of-range integers). That refusal is correct and must
stay - the pre-fix alternative, reporting a compact byte count for an
event compact cannot carry, was the dishonest behaviour.

What is pinned here is how the operator-facing CLIs *report* it.
tools/convert_encoding.py already translated CompactUnrepresentableError
into a one-line `SystemExit`; measure_packet_size, udp_sender and replay
aborted with a raw traceback through zmeta_compact internals. The family
is enumerated from the code: every tools/ CLI that feeds an arbitrary
operator-supplied corpus to zmeta_compact.dumps().

Each case asserts exit 1 AND the absence of a traceback, so restoring the
unguarded call fails the test rather than merely changing the wording.
"""

import shutil
import subprocess
import sys
import uuid
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
TMP_ROOT = ROOT / "pytest-work"
V11_CORPUS = ROOT / "examples" / "zmeta-v1.1-examples.jsonl"
V10_CORPUS = ROOT / "examples" / "zmeta-profile-L-examples.jsonl"


@pytest.fixture
def workdir():
    path = TMP_ROOT / f"encoding-refusal-{uuid.uuid4().hex}"
    path.mkdir(parents=True)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)
        try:
            TMP_ROOT.rmdir()
        except OSError:
            pass


def _first_line(source: Path, target: Path) -> Path:
    line = source.read_text(encoding="utf-8").splitlines()[0]
    target.write_text(line + "\n", encoding="utf-8")
    return target


def _run(*args):
    return subprocess.run(
        [sys.executable, *[str(item) for item in args]],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def _assert_reported_refusal(result, expected_prefix):
    combined = result.stdout + result.stderr
    assert result.returncode == 1, combined
    assert "Traceback (most recent call last)" not in combined, combined
    assert expected_prefix in combined, combined
    # The codec's own explanation must survive into the operator message -
    # a refusal that does not say why is not actionable.
    assert "zmeta_version" in combined, combined


def test_measure_packet_size_reports_the_compact_refusal():
    result = _run(
        ROOT / "tools" / "measure_packet_size.py",
        "--file",
        V11_CORPUS,
        "--summary-only",
    )
    _assert_reported_refusal(result, "measurement refused for ")


def test_measure_packet_size_still_measures_the_v1_0_corpus():
    # Positive control: the refusal path must not have swallowed the
    # working case the CI gate and every VALIDATION_REPORT depend on.
    result = _run(
        ROOT / "tools" / "measure_packet_size.py",
        "--file",
        V10_CORPUS,
        "--summary-only",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "COMPACT" in result.stdout


def test_udp_sender_reports_the_compact_refusal(workdir):
    payload = _first_line(V11_CORPUS, workdir / "one.jsonl")
    result = _run(
        ROOT / "tools" / "udp_sender.py",
        "--file",
        payload,
        "--encoding",
        "compact",
    )
    _assert_reported_refusal(result, "send refused: ")


def test_replay_reports_the_compact_refusal(workdir):
    # UDP to a closed local port neither blocks nor errors; the refusal
    # fires before any datagram is built, so no listener is needed.
    payload = _first_line(V11_CORPUS, workdir / "one.jsonl")
    result = _run(
        ROOT / "tools" / "replay.py",
        "--file",
        payload,
        "--encoding",
        "compact",
        "--count",
        "1",
        "--delay-ms",
        "0",
    )
    _assert_reported_refusal(result, "replay refused after 0 events sent: ")


def test_convert_encoding_reports_the_compact_refusal(workdir):
    # The sibling that already had this behaviour, pinned so the family
    # stays consistent in both directions.
    payload = _first_line(V11_CORPUS, workdir / "one.json")
    result = _run(
        ROOT / "tools" / "convert_encoding.py",
        "--from",
        "json",
        "--to",
        "compact",
        "--input",
        payload,
        "--output",
        workdir / "out.bin",
    )
    _assert_reported_refusal(result, "conversion refused: ")
