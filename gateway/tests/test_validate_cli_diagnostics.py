"""Branch-level schema diagnostics from the validate CLI.

The CLI used to validate every event against the version-discriminated
union schema and print only the first violation's message. A nested defect
in a lane-declared event therefore printed as the whole event dict plus
"is not valid under any of the given schemas", while the gateway, which
validates the declared version lane, emitted the actionable branch
diagnostic for the same event. An external field pass (PR #8) reported
walking branch-level diagnostics by hand for twelve events before finding
each cause; the CLI was the single surface in the stack that lost them.

The CLI now selects the lane from the event's declared zmeta_version,
prints every violation with its path, and names the union fallback when no
known lane is declared. Each test here fails against the pre-fix behavior:
the multi-defect test sees exactly the opaque dump the fix replaces, and
the fallback test pins the one case where the union message legitimately
remains.
"""

import json
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
TMP_ROOT = ROOT / "pytest-work"

DONOR_EXAMPLES = ROOT / "examples" / "zmeta-examples-1.0.jsonl"
DONOR_PROFILE = "H"

OPAQUE_UNION_MESSAGE = "is not valid under any of the given schemas"


@pytest.fixture
def workdir():
    path = TMP_ROOT / f"validate-cli-{uuid.uuid4().hex}"
    path.mkdir(parents=True)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)
        try:
            TMP_ROOT.rmdir()
        except OSError:
            pass


def _donor_event():
    with open(DONOR_EXAMPLES, encoding="utf-8") as handle:
        first = handle.readline().strip()
    event = json.loads(first)
    assert event["zmeta_version"] == "1.0", "donor drifted; pick a 1.0 line"
    return event


def _run_validate(path):
    return subprocess.run(
        [
            sys.executable,
            "tools/validate.py",
            "--file",
            str(path),
            "--profile",
            DONOR_PROFILE,
        ],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
    )


def _write_event(workdir, event):
    path = workdir / "event.jsonl"
    path.write_text(json.dumps(event) + "\n", encoding="utf-8")
    return path


def test_a_valid_event_still_passes(workdir):
    """Non-vacuity floor: the donor passes before any doctoring."""
    result = _run_validate(_write_event(workdir, _donor_event()))
    assert result.returncode == 0, result.stdout + result.stderr
    assert "passed=1" in result.stdout


def test_a_lane_declared_event_gets_branch_level_paths_for_every_defect(workdir):
    """Three independent defects, three named paths, zero opaque dumps."""
    event = _donor_event()
    event["event"]["ts"] = event["event"]["ts"].replace("Z", "+00:00")
    event["source"]["node_role"] = "EDGY"
    event["event"]["event_subtype"] = "NOT_A_SUBTYPE"

    result = _run_validate(_write_event(workdir, event))

    assert result.returncode == 1, result.stdout + result.stderr
    for expected_path in ("event/ts", "source/node_role", "event/event_subtype"):
        assert f"at: {expected_path}" in result.stdout, (
            f"missing branch path {expected_path}:\n{result.stdout}"
        )
    assert result.stdout.count("FAIL SCHEMA_INVALID") >= 3, result.stdout
    assert OPAQUE_UNION_MESSAGE not in result.stdout, (
        "lane-declared event fell back to the union dump:\n" + result.stdout
    )


def test_the_union_fallback_names_itself_and_hints_the_lanes(workdir):
    """The union message survives only where it is honest: no known lane.

    This is also the self-test of the assertion above: the exact opaque
    string the fix removed from the lane path is demonstrated still
    reachable, so the other test's not-in check cannot pass vacuously
    against a message that no longer exists anywhere.
    """
    event = _donor_event()
    event["zmeta_version"] = "9.9"

    result = _run_validate(_write_event(workdir, event))

    assert result.returncode == 1, result.stdout + result.stderr
    assert OPAQUE_UNION_MESSAGE in result.stdout, result.stdout
    assert "declare zmeta_version" in result.stdout, result.stdout


def test_an_unhashable_declared_version_falls_back_instead_of_crashing(workdir):
    """A wire-shaped zmeta_version (list/dict) must not raise on the lane lookup.

    The first version of the lane fix passed the raw value to dict.get,
    and an unhashable key is a TypeError: the CLI printed a traceback and
    no summary. It must fall back to the union like any unknown lane.
    """
    for bad in (["1.0"], {"v": "1.0"}):
        event = _donor_event()
        event["zmeta_version"] = bad

        result = _run_validate(_write_event(workdir, event))

        assert result.returncode == 1, result.stdout + result.stderr
        assert "Traceback" not in result.stderr, result.stderr
        assert "total=1" in result.stdout, result.stdout
        assert OPAQUE_UNION_MESSAGE in result.stdout, result.stdout


def test_a_nested_enum_defect_prints_the_enum_diagnostic(workdir):
    """The motivating case: a buried invalid enum names itself and its path."""
    event = _donor_event()
    payload = event.get("payload", {})
    timing = payload.get("timing_quality")
    if not isinstance(timing, dict):
        pytest.skip("donor no longer carries timing_quality; re-pick the donor")
    timing["time_source"] = "GPS"

    result = _run_validate(_write_event(workdir, event))

    assert result.returncode == 1, result.stdout + result.stderr
    assert "'GPS' is not one of" in result.stdout, result.stdout
    assert "timing_quality/time_source" in result.stdout, result.stdout
