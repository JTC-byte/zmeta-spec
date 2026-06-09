import importlib.util
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = ROOT / "tools" / "validate_adapter_conformance.py"
FIXTURE_PATH = ROOT / "conformance" / "adapter-harness" / "must-pass.jsonl"

spec = importlib.util.spec_from_file_location("zmeta_validate_adapter_conformance", VALIDATOR_PATH)
validate_adapter_conformance = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validate_adapter_conformance)


def test_adapter_conformance_run_succeeds():
    assert validate_adapter_conformance.run(fixtures_path=FIXTURE_PATH, quiet=True) == 0


def test_adapter_conformance_cli_exits_success():
    result = subprocess.run(
        [sys.executable, str(VALIDATOR_PATH), "--fixtures", str(FIXTURE_PATH), "--quiet"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "adapter conformance ok" in result.stdout


def test_adapter_conformance_detects_fixture_output_contract():
    schema = validate_adapter_conformance.validators.load_schema(
        ROOT / "schema" / "zmeta-event.schema.json"
    )
    policy = validate_adapter_conformance.validators.load_policy(ROOT / "policy")
    fixture = {
        "module": "adapters/ingress/klv/klv_to_zmeta_template.py",
        "callable": "klv_decoded_to_zmeta_observation",
        "args": [{"lat": 34.0, "lon": -118.0, "alt_m": 120.0}],
        "kwargs": {
            "platform_id": "platform-1",
            "sensor_id": "sensor-1",
            "producer": "klv:misb:0601",
            "ts": "2025-01-17T15:20:00+00:00",
        },
        "profile": "H",
        "expect": {
            "event_type": "OBSERVATION_EVENT",
            "event_subtype": "EO",
            "lineage_transform_prefix": "translate:klv@",
            "allow_degraded_timing": True,
        },
    }

    assert validate_adapter_conformance.evaluate_fixture(fixture, schema, policy) == []


def test_conformance_runner_adapter_harness_flag_exits_success():
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "validate_conformance.py"),
            "--strict",
            "--adapter-harness",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "adapter conformance ok" in result.stdout
    assert "conformance ok" in result.stdout
