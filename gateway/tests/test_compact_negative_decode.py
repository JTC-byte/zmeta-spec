import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = ROOT / "tools" / "validate_encoding_negative.py"
COMPACT_PATH = ROOT / "conformance" / "encoding-negative" / "compact-must-fail.jsonl"

spec = importlib.util.spec_from_file_location("zmeta_validate_encoding_negative", VALIDATOR_PATH)
validate_encoding_negative = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validate_encoding_negative)

import zmeta_compact


def _fixture(name):
    for line in COMPACT_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        if item.get("name") == name:
            return item
    raise AssertionError(f"fixture not found: {name}")


def _evaluate(name):
    schema = validate_encoding_negative.validators.load_schema(
        ROOT / "schema" / "zmeta-event.schema.json"
    )
    policy = validate_encoding_negative.validators.load_policy(ROOT / "policy")
    contexts = validate_encoding_negative.load_contexts(
        ROOT / "conformance" / "encoding-negative" / "context.jsonl"
    )
    return validate_encoding_negative.evaluate_fixture(_fixture(name), schema, policy, contexts)


def test_malformed_compact_cbor_rejected_by_decoder():
    with pytest.raises(ValueError, match="unexpected end"):
        zmeta_compact.loads(bytes.fromhex("45616263"))


def test_unsupported_compact_version_rejected():
    result = _evaluate("compact-unsupported-version-fail")
    assert result["stage"] == "decode"
    assert result["code"] == "ENCODE_NEGATIVE_UNSUPPORTED_COMPACT_VERSION"


def test_compact_invalid_uuid_bytes_fails_after_decode():
    result = _evaluate("compact-invalid-uuid-bytes-fail")
    assert result["stage"] == "schema"
    assert result["code"] == "ENCODE_NEGATIVE_INVALID_UUID_BYTES"


def test_compact_unknown_enum_values_do_not_create_vocabulary():
    result = _evaluate("compact-invalid-event-type-enum-fail")
    assert result["stage"] == "schema"
    assert result["code"] == "ENCODE_NEGATIVE_INVALID_COMPACT_ENUM"


def test_compact_schema_invalid_decoded_event_fails():
    result = _evaluate("compact-state-missing-lineage-fail")
    assert result["stage"] == "schema"
    assert result["code"] == "ENCODE_NEGATIVE_SCHEMA_INVALID_DECODED"


def test_compact_policy_invalid_decoded_event_fails():
    result = _evaluate("compact-policy-producer-unauthorized-fail")
    assert result["stage"] == "policy"
    assert result["code"] == "ENCODE_NEGATIVE_POLICY_INVALID_DECODED"


def test_compact_projection_invalid_decoded_event_fails():
    result = _evaluate("compact-projection-confidence-increase-fail")
    assert result["stage"] == "projection"
    assert result["code"] == "ENCODE_NEGATIVE_PROJECTION_INVALID_DECODED"
