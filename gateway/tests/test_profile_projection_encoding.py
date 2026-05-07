import importlib.util
import json
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


def _compare(fixture):
    catalog = validate_projection.load_catalog(CATALOG_PATH)
    schema_validator = validate_projection.validators.load_schema(
        ROOT / "schema" / "zmeta-event.schema.json"
    )
    policy = validate_projection.validators.load_policy(ROOT / "policy")
    return validate_projection.compare_projection(fixture, catalog, policy, schema_validator)


def _codes(fixture):
    return {violation["code"] for violation in _compare(fixture)}


def test_compact_profile_l_decoded_equivalence_passes():
    fixture = _fixture(PASS_PATH, "compact-profile-l-expansion-equivalence-pass")
    assert _compare(fixture) == []


def test_protobuf_decoded_json_validation_passes():
    fixture = _fixture(PASS_PATH, "protobuf-decoded-json-validation-pass")
    assert _compare(fixture) == []


def test_compact_decoded_schema_valid_projection_invalid_event_fails():
    fixture = _fixture(FAIL_PATH, "compact-decoded-projection-invalid-fail")
    codes = _codes(fixture)
    assert "PROJECTION_CONFIDENCE_INCREASE" in codes
    assert "PROJECTION_ENCODING_DECODE_INVALID" not in codes


def test_protobuf_decoded_schema_valid_projection_invalid_event_fails():
    fixture = _fixture(FAIL_PATH, "protobuf-decoded-projection-invalid-fail")
    codes = _codes(fixture)
    assert "PROJECTION_TTL_INCREASE" in codes
    assert "PROJECTION_ENCODING_DECODE_INVALID" not in codes
