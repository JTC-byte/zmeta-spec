import importlib.util
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = ROOT / "tools" / "validate_bad_events.py"
FIXTURE_PATH = ROOT / "conformance" / "bad-events" / "must-fail.jsonl"

spec = importlib.util.spec_from_file_location("zmeta_validate_bad_events", VALIDATOR_PATH)
validate_bad_events = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validate_bad_events)


def _fixture(name):
    for line in FIXTURE_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        if item.get("name") == name:
            return item
    raise AssertionError(f"fixture not found: {name}")


def _schema_policy():
    schema = validate_bad_events.validators.load_schema(
        ROOT / "schema" / "zmeta-event.schema.json"
    )
    policy = validate_bad_events.validators.load_policy(ROOT / "policy")
    return schema, policy


def test_bad_event_validator_run_succeeds():
    assert validate_bad_events.run(must_fail_path=FIXTURE_PATH, quiet=True) == 0


def test_bad_event_cli_exits_success():
    result = subprocess.run(
        [sys.executable, str(VALIDATOR_PATH), "--must-fail", str(FIXTURE_PATH), "--quiet"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "bad-event corpus ok" in result.stdout


def test_bad_event_external_promotion_fixture_hits_policy_code():
    schema, policy = _schema_policy()
    result = validate_bad_events.evaluate_fixture(
        _fixture("external-state-missing-promotion-evidence"),
        schema,
        policy,
    )

    assert result["passed"]
    assert "PRODUCER_NOT_ALLOWED" in result["codes"]


def test_bad_event_bearing_frame_fixture_fails_for_frame_label_only():
    schema, policy = _schema_policy()
    fixture = _fixture("observation-bearing-frame-mislabeled")

    result = validate_bad_events.evaluate_fixture(fixture, schema, policy)
    assert result["passed"]
    assert result["codes"] == ["SCHEMA_INVALID"]

    event = json.loads(json.dumps(fixture["event"]))
    assert event["payload"]["bearing"]["frame"] == "ARRAY_RELATIVE"

    sub_errors = []
    for err in schema.iter_errors(event):
        sub_errors.extend(err.context or [])
    frame_errors = [sub for sub in sub_errors if list(sub.absolute_path) == ["payload", "bearing", "frame"]]
    assert frame_errors, "expected a violation at payload.bearing.frame"
    assert any("TRUE_NORTH" in sub.message for sub in frame_errors)

    # The same event with the mislabeled frame corrected (or removed) is clean,
    # proving the frame label is the only cause of rejection.
    state = validate_bad_events.validators.ValidationState()
    event["payload"]["bearing"]["frame"] = "TRUE_NORTH"
    assert validate_bad_events._run_checks(event, "H", policy, schema, state) == []

    state = validate_bad_events.validators.ValidationState()
    del event["payload"]["bearing"]["frame"]
    assert validate_bad_events._run_checks(event, "H", policy, schema, state) == []


def test_conformance_runner_bad_events_flag_exits_success():
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "validate_conformance.py"), "--strict", "--bad-events"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "bad-event corpus ok" in result.stdout
    assert "conformance ok" in result.stdout
