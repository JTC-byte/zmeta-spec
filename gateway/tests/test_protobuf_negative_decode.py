import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = ROOT / "tools" / "validate_encoding_negative.py"
PROTOBUF_PATH = ROOT / "conformance" / "encoding-negative" / "protobuf-must-fail.jsonl"

spec = importlib.util.spec_from_file_location("zmeta_validate_encoding_negative", VALIDATOR_PATH)
validate_encoding_negative = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validate_encoding_negative)

import zmeta_proto


def _fixture(name):
    for line in PROTOBUF_PATH.read_text(encoding="utf-8").splitlines():
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


def test_malformed_protobuf_rejected_by_decoder():
    with pytest.raises(ValueError, match="varint"):
        zmeta_proto.loads(bytes.fromhex("80808080808080808080"))


def test_protobuf_invalid_field_number_rejected():
    result = _evaluate("protobuf-invalid-field-zero-fail")
    assert result["stage"] == "decode"
    assert result["code"] == "ENCODE_NEGATIVE_INVALID_PROTOBUF_FIELD"


def test_protobuf_unsupported_wire_type_rejected():
    result = _evaluate("protobuf-unsupported-wire-type-fail")
    assert result["stage"] == "decode"
    assert result["code"] == "ENCODE_NEGATIVE_UNSUPPORTED_PROTOBUF_WIRE_TYPE"


def test_protobuf_size_depth_and_utf8_bounds_rejected():
    assert _evaluate("protobuf-oversized-message-fail")["code"] == "ENCODE_NEGATIVE_PROTOBUF_OVERSIZE"
    assert _evaluate("protobuf-oversized-payload-json-fail")["code"] == "ENCODE_NEGATIVE_PAYLOAD_JSON_OVERSIZE"
    assert _evaluate("protobuf-payload-json-too-deep-fail")["code"] == "ENCODE_NEGATIVE_PAYLOAD_JSON_TOO_DEEP"
    assert _evaluate("protobuf-invalid-utf8-payload-fail")["code"] == "ENCODE_NEGATIVE_INVALID_UTF8"


def test_protobuf_payload_not_object_rejected_after_decode():
    result = _evaluate("protobuf-payload-not-object-fail")
    assert result["stage"] == "schema"
    assert result["code"] == "ENCODE_NEGATIVE_PAYLOAD_NOT_OBJECT"


def test_protobuf_schema_invalid_decoded_event_fails():
    result = _evaluate("protobuf-uuidv4-event-id-fail")
    assert result["stage"] == "schema"
    assert result["code"] == "ENCODE_NEGATIVE_SCHEMA_INVALID_DECODED"


def test_protobuf_reserved_and_v1_1_vocabulary_rejected():
    assert _evaluate("protobuf-v1-1-sensor-status-under-v1-fail")["code"] == "ENCODE_NEGATIVE_V1_1_LEAK_TO_V1_0"
    assert _evaluate("protobuf-reserved-radar-vocab-fail")["code"] == "ENCODE_NEGATIVE_RESERVED_VOCAB_LEAK"


def test_protobuf_policy_invalid_decoded_event_fails():
    result = _evaluate("protobuf-policy-producer-unauthorized-fail")
    assert result["stage"] == "policy"
    assert result["code"] == "ENCODE_NEGATIVE_POLICY_INVALID_DECODED"


def test_protobuf_projection_invalid_decoded_event_fails():
    result = _evaluate("protobuf-projection-ttl-increase-fail")
    assert result["stage"] == "projection"
    assert result["code"] == "ENCODE_NEGATIVE_PROJECTION_INVALID_DECODED"
