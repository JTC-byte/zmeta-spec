import importlib.util
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = ROOT / "tools" / "validate_encoding_negative.py"
COMPACT_PATH = ROOT / "conformance" / "encoding-negative" / "compact-must-fail.jsonl"
PROTOBUF_PATH = ROOT / "conformance" / "encoding-negative" / "protobuf-must-fail.jsonl"
GATEWAY_PATH = ROOT / "conformance" / "encoding-negative" / "gateway-must-fail.jsonl"

spec = importlib.util.spec_from_file_location("zmeta_validate_encoding_negative", VALIDATOR_PATH)
validate_encoding_negative = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validate_encoding_negative)


def _fixture(path, name):
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        if item.get("name") == name:
            return item
    raise AssertionError(f"fixture not found: {name}")


def _context():
    return validate_encoding_negative.load_contexts(
        ROOT / "conformance" / "encoding-negative" / "context.jsonl"
    )


def _schema_policy():
    schema = validate_encoding_negative.validators.load_schema(
        ROOT / "schema" / "zmeta-event.schema.json"
    )
    policy = validate_encoding_negative.validators.load_policy(ROOT / "policy")
    return schema, policy


def _evaluate(path, name):
    schema, policy = _schema_policy()
    return validate_encoding_negative.evaluate_fixture(_fixture(path, name), schema, policy, _context())


def test_validator_run_succeeds_for_current_fixture_suite():
    assert (
        validate_encoding_negative.run(
            compact_path=COMPACT_PATH,
            protobuf_path=PROTOBUF_PATH,
            gateway_path=GATEWAY_PATH,
            context_path=ROOT / "conformance" / "encoding-negative" / "context.jsonl",
            quiet=True,
        )
        == 0
    )


def test_validator_cli_exits_success_for_current_fixture_suite():
    result = subprocess.run(
        [
            sys.executable,
            str(VALIDATOR_PATH),
            "--compact",
            str(COMPACT_PATH),
            "--protobuf",
            str(PROTOBUF_PATH),
            "--gateway",
            str(GATEWAY_PATH),
            "--quiet",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0
    assert "encoding negative ok" in result.stdout


def test_gateway_explicit_compact_schema_invalid_rejected():
    result = _evaluate(GATEWAY_PATH, "gateway-compact-schema-invalid-rejected")
    assert result["stage"] == "gateway_cli"
    assert result["code"] == "ENCODE_NEGATIVE_SCHEMA_INVALID_DECODED"


def test_gateway_explicit_protobuf_policy_invalid_rejected():
    result = _evaluate(GATEWAY_PATH, "gateway-protobuf-policy-invalid-rejected")
    assert result["stage"] == "gateway_cli"
    assert result["code"] == "ENCODE_NEGATIVE_POLICY_INVALID_DECODED"


def test_convert_path_rejects_or_revalidates_invalid_decoded_json():
    result = _evaluate(GATEWAY_PATH, "convert-protobuf-schema-invalid-then-validate-rejects")
    assert result["stage"] == "gateway_cli"
    assert result["code"] == "ENCODE_NEGATIVE_SCHEMA_INVALID_DECODED"


def test_conformance_runner_encoding_negative_flag_exits_success():
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "validate_conformance.py"),
            "--strict",
            "--profile-projection",
            "--extension-registry",
            "--conformance-classes",
            "--encoding-negative",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0
    assert "encoding negative ok" in result.stdout
    assert "conformance ok" in result.stdout
