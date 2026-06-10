import importlib.util
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VALIDATE_PROJECTION_PATH = ROOT / "tools" / "validate_projection.py"
CATALOG_PATH = ROOT / "conformance" / "profile_projection_field_catalog.yaml"
PASS_PATH = ROOT / "conformance" / "profile-projection" / "must-pass.jsonl"
FAIL_PATH = ROOT / "conformance" / "profile-projection" / "must-fail.jsonl"

spec = importlib.util.spec_from_file_location("validate_projection", VALIDATE_PROJECTION_PATH)
validate_projection = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validate_projection)


def _fixture(path, name):
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        if item.get("name") == name:
            return item
    raise AssertionError(f"fixture not found: {name}")


def _violations(name):
    fixture = _fixture(FAIL_PATH, name)
    catalog = validate_projection.load_catalog(CATALOG_PATH)
    schema_validator = validate_projection.validators.load_schema(
        ROOT / "schema" / "zmeta-event.schema.json"
    )
    policy = validate_projection.validators.load_policy(ROOT / "policy")
    return validate_projection.compare_projection(fixture, catalog, policy, schema_validator)


def _codes(name):
    return {violation["code"] for violation in _violations(name)}


def test_projection_cli_succeeds_on_default_fixture_suite():
    result = subprocess.run(
        [
            sys.executable,
            str(VALIDATE_PROJECTION_PATH),
            "--catalog",
            str(CATALOG_PATH),
            "--must-pass",
            str(PASS_PATH),
            "--must-fail",
            str(FAIL_PATH),
            "--quiet",
        ],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "projection conformance ok" in result.stdout


def test_projection_cli_fails_for_missing_fixture_file():
    result = subprocess.run(
        [
            sys.executable,
            str(VALIDATE_PROJECTION_PATH),
            "--catalog",
            str(CATALOG_PATH),
            "--must-pass",
            str(ROOT / "conformance" / "profile-projection" / "does-not-exist.jsonl"),
            "--must-fail",
            str(FAIL_PATH),
            "--quiet",
        ],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "projection fixture file not found" in result.stderr


def test_projection_failure_codes_include_required_contract_set():
    required = {
        "PROJECTION_EVENT_ID_CHANGED",
        "PROJECTION_VERSION_CHANGED",
        "PROJECTION_EVENT_TS_CHANGED",
        "PROJECTION_EVENT_TYPE_CHANGED",
        "PROJECTION_EVENT_SUBTYPE_CHANGED",
        "PROJECTION_SOURCE_CHANGED",
        "PROJECTION_SOURCE_REWRITTEN",
        "PROJECTION_TRACK_ID_CHANGED",
        "PROJECTION_LINEAGE_REMOVED",
        "PROJECTION_LINEAGE_CHANGED",
        "PROJECTION_TRANSFORM_REMOVED",
        "PROJECTION_CONFIDENCE_INCREASE",
        "PROJECTION_TTL_INCREASE",
        "PROJECTION_PRECISION_INCREASE",
        "PROJECTION_UNIT_CHANGED",
        "PROJECTION_REQUIRED_FIELD_REMOVED",
        "PROJECTION_PROHIBITED_FIELD_ADDED",
        "PROJECTION_SEMANTIC_LAYER_COLLAPSE",
        "PROJECTION_PROFILE_ILLEGAL_EVENT",
        "PROJECTION_POLICY_RISK_LABEL_REMOVED",
        "PROJECTION_EXTERNAL_PROMOTION_EVIDENCE_REMOVED",
        "PROJECTION_UNDECLARED_OPTIONAL_OMISSION",
        "PROJECTION_ENCODING_DECODE_INVALID",
        "PROJECTION_SCHEMA_INVALID_SOURCE",
        "PROJECTION_SCHEMA_INVALID_PROJECTED",
        "PROJECTION_POLICY_INVALID_SOURCE",
        "PROJECTION_POLICY_INVALID_PROJECTED",
    }

    assert required.issubset(set(validate_projection.FAILURE_CODES))


def test_projection_confidence_ttl_and_precision_monotonicity():
    assert "PROJECTION_CONFIDENCE_INCREASE" in _codes("confidence-increase-fail")
    assert "PROJECTION_TTL_INCREASE" in _codes("ttl-increase-fail")
    assert "PROJECTION_PRECISION_INCREASE" in _codes("precision-increase-fail")


def test_projection_identity_source_track_and_lineage_preservation():
    assert "PROJECTION_EVENT_ID_CHANGED" in _codes("event-id-change-fail")
    assert "PROJECTION_SOURCE_CHANGED" in _codes("source-rewrite-fail")
    assert "PROJECTION_SOURCE_REWRITTEN" in _codes("optional-source-rewrite-fail")
    assert "PROJECTION_TRACK_ID_CHANGED" in _codes("track-id-rewrite-fail")
    assert "PROJECTION_LINEAGE_REMOVED" in _codes("lineage-deletion-fail")
    assert "PROJECTION_TRANSFORM_REMOVED" in _codes("lineage-transform-removal-fail")


def test_projection_optional_omission_must_be_cataloged():
    good = _fixture(PASS_PATH, "optional-source-fields-stripped-pass")
    catalog = validate_projection.load_catalog(CATALOG_PATH)
    schema_validator = validate_projection.validators.load_schema(
        ROOT / "schema" / "zmeta-event.schema.json"
    )
    policy = validate_projection.validators.load_policy(ROOT / "policy")

    assert validate_projection.compare_projection(good, catalog, policy, schema_validator) == []
    assert "PROJECTION_UNDECLARED_OPTIONAL_OMISSION" in _codes(
        "undeclared-optional-omission-fail"
    )


def test_projection_preserves_policy_risk_extensions():
    assert "PROJECTION_POLICY_RISK_LABEL_REMOVED" in _codes(
        "risk-adjudication-stripped-fail"
    )
    assert "PROJECTION_EXTERNAL_PROMOTION_EVIDENCE_REMOVED" in _codes(
        "external-promotion-compact-evidence-stripped-fail"
    )


def test_projection_rejects_semantic_layer_collapse_and_raw_state_fields():
    assert "PROJECTION_SEMANTIC_LAYER_COLLAPSE" in _codes(
        "observation-to-state-same-id-fail"
    )
    assert "PROJECTION_SEMANTIC_LAYER_COLLAPSE" in _codes(
        "inference-to-state-same-id-fail"
    )
    assert "PROJECTION_PROHIBITED_FIELD_ADDED" in _codes("raw-state-fields-fail")
