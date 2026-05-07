import importlib.util
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = ROOT / "tools" / "validate_precision_policy.py"
POLICY_PATH = ROOT / "policy" / "profile-precision.yaml"
PASS_PATH = ROOT / "conformance" / "profile-precision" / "must-pass.jsonl"
FAIL_PATH = ROOT / "conformance" / "profile-precision" / "must-fail.jsonl"

spec = importlib.util.spec_from_file_location("zmeta_validate_precision_policy", VALIDATOR_PATH)
validate_precision_policy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validate_precision_policy)


def _fixture(path, name):
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        if item.get("name") == name:
            return item
    raise AssertionError(f"fixture not found: {name}")


def _runtime():
    precision_policy = validate_precision_policy.load_precision_policy(POLICY_PATH)
    catalog = validate_precision_policy.validate_projection.load_catalog(
        ROOT / "conformance" / "profile_projection_field_catalog.yaml"
    )
    schema = validate_precision_policy.validators.load_schema(
        ROOT / "schema" / "zmeta-event.schema.json"
    )
    base_policy = validate_precision_policy.validators.load_policy(ROOT / "policy")
    return precision_policy, catalog, base_policy, schema


def _codes(path, name):
    precision_policy, catalog, base_policy, schema = _runtime()
    issues = validate_precision_policy.compare_precision(
        _fixture(path, name),
        precision_policy,
        catalog,
        base_policy,
        schema,
    )
    return {issue["code"] for issue in issues}


def test_precision_policy_yaml_loads_and_has_required_sections():
    policy = validate_precision_policy.load_precision_policy(POLICY_PATH)
    assert validate_precision_policy.validate_policy_shape(policy) == []
    assert "L" in policy["profiles"]
    assert "M" in policy["profiles"]
    assert "H" in policy["profiles"]
    assert "payload.geo.lat" in policy["precision_ceilings"]["L"]
    assert policy["policy_status"] == "reference_conformance_default"
    assert policy["requires_mission_review"] is True


def test_validator_cli_succeeds_for_current_fixture_suite():
    result = subprocess.run(
        [
            sys.executable,
            str(VALIDATOR_PATH),
            "--policy",
            str(POLICY_PATH),
            "--must-pass",
            str(PASS_PATH),
            "--must-fail",
            str(FAIL_PATH),
            "--quiet",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "profile precision policy ok" in result.stdout


def test_confidence_rounding_rules():
    assert (
        validate_precision_policy.compare_precision(
            _fixture(PASS_PATH, "confidence-rounded-down-pass"),
            *_runtime(),
        )
        == []
    )
    assert "PRECISION_POLICY_CONFIDENCE_INCREASE" in _codes(
        FAIL_PATH, "confidence-rounded-up-fail"
    )
    assert "PRECISION_POLICY_CONFIDENCE_ROUNDING_INVALID" in _codes(
        FAIL_PATH, "confidence-rounding-invalid-fail"
    )


def test_ttl_rounding_rules():
    assert (
        validate_precision_policy.compare_precision(
            _fixture(PASS_PATH, "valid-for-ms-rounded-down-pass"),
            *_runtime(),
        )
        == []
    )
    assert "PRECISION_POLICY_TTL_INCREASE" in _codes(
        FAIL_PATH, "valid-for-ms-rounded-up-fail"
    )
    assert "PRECISION_POLICY_TTL_ROUNDING_INVALID" in _codes(
        FAIL_PATH, "valid-for-ms-rounding-invalid-fail"
    )


def test_error_bound_rounding_rules():
    assert (
        validate_precision_policy.compare_precision(
            _fixture(PASS_PATH, "timing-error-rounded-up-pass"),
            *_runtime(),
        )
        == []
    )
    assert "PRECISION_POLICY_ERROR_BOUND_DECREASE" in _codes(
        FAIL_PATH, "timing-error-rounded-down-fail"
    )


def test_lat_lon_precision_and_utility_floor_rules():
    assert (
        validate_precision_policy.compare_precision(
            _fixture(PASS_PATH, "m-to-l-state-geo-precision-pass"),
            *_runtime(),
        )
        == []
    )
    assert "PRECISION_POLICY_PRECISION_INCREASE" in _codes(
        FAIL_PATH, "lat-lon-precision-increased-fail"
    )
    assert "PRECISION_POLICY_UTILITY_FLOOR_VIOLATION" in _codes(
        FAIL_PATH, "geo-over-thinned-fail"
    )
    assert "PRECISION_POLICY_SOURCE_LIMITED_PRECISION_UNDECLARED" in _codes(
        FAIL_PATH, "source-limited-precision-undeclared-fail"
    )


def test_command_target_and_rf_policy_rules():
    assert (
        validate_precision_policy.compare_precision(
            _fixture(PASS_PATH, "command-target-geo-utility-floor-pass"),
            *_runtime(),
        )
        == []
    )
    assert (
        validate_precision_policy.compare_precision(
            _fixture(PASS_PATH, "profile-m-rf-quantization-pass"),
            *_runtime(),
        )
        == []
    )
    assert "PRECISION_POLICY_COMMAND_GEOMETRY_TOO_COARSE" in _codes(
        FAIL_PATH, "command-target-geo-too-coarse-fail"
    )
    assert "PRECISION_POLICY_RF_QUANTIZATION_INVALID" in _codes(
        FAIL_PATH, "rf-center-frequency-invalid-fail"
    )


def test_immutable_unit_hidden_default_and_required_field_failures():
    assert "PRECISION_POLICY_IMMUTABLE_CHANGED" in _codes(
        FAIL_PATH, "event-ts-changed-fail"
    )
    assert "PRECISION_POLICY_IMMUTABLE_CHANGED" in _codes(
        FAIL_PATH, "event-id-changed-fail"
    )
    assert "PRECISION_POLICY_UNIT_CHANGED" in _codes(FAIL_PATH, "unit-rescale-fail")
    assert "PRECISION_POLICY_HIDDEN_DEFAULT" in _codes(
        FAIL_PATH, "hidden-default-heading-fail"
    )
    assert "PRECISION_POLICY_REQUIRED_FIELD_REMOVED" in _codes(
        FAIL_PATH, "required-track-id-removed-fail"
    )


def test_compact_profile_l_policy_compliant_fixture_stays_valid():
    assert (
        validate_precision_policy.compare_precision(
            _fixture(PASS_PATH, "compact-profile-l-policy-compliant-pass"),
            *_runtime(),
        )
        == []
    )


def test_projection_and_packet_budget_failures_are_mapped():
    assert "PRECISION_POLICY_PROJECTION_INVALID" in _codes(
        FAIL_PATH, "projection-invalid-field-change-fail"
    )
    assert "PRECISION_POLICY_PACKET_BUDGET_STRIPPED_REQUIRED" in _codes(
        FAIL_PATH, "packet-budget-stripped-required-fail"
    )


def test_precision_validator_fails_if_fixture_files_are_missing():
    result = subprocess.run(
        [
            sys.executable,
            str(VALIDATOR_PATH),
            "--policy",
            str(POLICY_PATH),
            "--must-pass",
            str(ROOT / "conformance" / "profile-precision" / "missing.jsonl"),
            "--must-fail",
            str(FAIL_PATH),
            "--quiet",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "profile precision fixture file not found" in result.stderr
