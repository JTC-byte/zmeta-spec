import json
import pytest
import random
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import zmeta_cbor
import zmeta_compact
import zmeta_proto


def _load_events():
    path = ROOT / "examples" / "encoding-roundtrip.jsonl"
    lines = path.read_text(encoding="utf-8").splitlines()
    events = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        events.append(json.loads(line))
    return events


def test_cbor_roundtrip():
    for event in _load_events():
        encoded = zmeta_cbor.dumps(event)
        decoded = zmeta_cbor.loads(encoded)
        assert decoded == event


def test_cbor_map_order_is_deterministic():
    left = {"b": 1, "a": 2, "nested": {"z": True, "y": None}}
    right = {"nested": {"y": None, "z": True}, "a": 2, "b": 1}
    assert zmeta_cbor.dumps(left) == zmeta_cbor.dumps(right)


def test_cbor_rejects_oversized_message():
    with pytest.raises(ValueError, match="max_bytes"):
        zmeta_cbor.loads(b"\xf6", max_bytes=0)


def test_cbor_rejects_oversized_byte_and_text_items():
    with pytest.raises(ValueError, match="max_item_bytes"):
        zmeta_cbor.loads(b"\x44abcd", max_item_bytes=3)

    with pytest.raises(ValueError, match="max_item_bytes"):
        zmeta_cbor.loads(b"\x7a\x00\x00\x00\x10", max_item_bytes=8)


def test_cbor_rejects_oversized_containers():
    with pytest.raises(ValueError, match="max_container_items"):
        zmeta_cbor.loads(b"\x82\xf6\xf6", max_container_items=1)

    with pytest.raises(ValueError, match="max_container_items"):
        zmeta_cbor.loads(b"\xba\x00\x00\x00\x10", max_container_items=8)


def test_cbor_rejects_deep_nesting():
    value = 0
    for _ in range(8):
        value = [value]
    encoded = zmeta_cbor.dumps(value)

    with pytest.raises(ValueError, match="max_depth"):
        zmeta_cbor.loads(encoded, max_depth=3)


def test_cbor_rejects_deep_tag_nesting():
    with pytest.raises(ValueError, match="max_depth"):
        zmeta_cbor.loads(b"\xc0\xc0\xc0\xc0\xf6", max_depth=3)


def test_cbor_rejects_indefinite_lengths_and_truncated_payloads():
    with pytest.raises(ValueError, match="indefinite lengths"):
        zmeta_cbor.loads(b"\x9f\xff")

    with pytest.raises(ValueError, match="unexpected end of data"):
        zmeta_cbor.loads(b"\x45abc")


def test_cbor_rejects_unhashable_map_keys():
    with pytest.raises(ValueError, match="not hashable"):
        zmeta_cbor.loads(b"\xa1\x81\x01\x02")


def test_cbor_random_bytes_do_not_raise_unexpected_exceptions():
    samples = [
        b"",
        b"\xff",
        b"\x9f\xff",
        b"\xbf\xff",
        b"\xc0" * 80 + b"\xf6",
        bytes(range(32)),
        b"\x5a\xff\xff\xff\xff",
        b"\x9a\x00\x00\x00\x40" + (b"\xf6" * 8),
    ]

    for sample in samples:
        try:
            zmeta_cbor.loads(
                sample,
                max_bytes=256,
                max_item_bytes=64,
                max_container_items=16,
                max_depth=8,
            )
        except (ValueError, UnicodeDecodeError):
            continue


def test_cbor_seeded_random_fuzz_rejects_or_decodes_supported_values():
    rng = random.Random(0x43424F52)

    for _ in range(250):
        size = rng.randrange(0, 160)
        sample = bytes(rng.randrange(0, 256) for _ in range(size))
        try:
            zmeta_cbor.loads(
                sample,
                max_bytes=256,
                max_item_bytes=64,
                max_container_items=16,
                max_depth=8,
            )
        except (ValueError, UnicodeDecodeError):
            continue


def test_compact_roundtrip():
    for event in _load_events():
        encoded = zmeta_compact.dumps(event)
        decoded = zmeta_compact.loads(encoded)
        assert decoded == event


def test_compact_decode_accepts_cbor_limits():
    event = _load_events()[0]
    encoded = zmeta_compact.dumps(event)

    with pytest.raises(ValueError, match="max_depth"):
        zmeta_compact.loads(encoded, max_depth=1)


def test_compact_prefers_builtin_cbor_when_cbor2_is_present():
    class ExplodingCbor2:
        @staticmethod
        def dumps(*_args, **_kwargs):
            raise AssertionError("compact encoding should prefer zmeta_cbor")

        @staticmethod
        def loads(*_args, **_kwargs):
            raise AssertionError("compact decoding should prefer zmeta_cbor")

    original_cbor2 = zmeta_compact.cbor2
    try:
        zmeta_compact.cbor2 = ExplodingCbor2
        for event in _load_events():
            encoded = zmeta_compact.dumps(event)
            decoded = zmeta_compact.loads(encoded)
            assert decoded == event
    finally:
        zmeta_compact.cbor2 = original_cbor2


def test_proto_roundtrip():
    for event in _load_events():
        encoded = zmeta_proto.dumps(event)
        decoded = zmeta_proto.loads(encoded)
        assert decoded == event


def test_proto_rejects_oversized_message():
    with pytest.raises(ValueError, match="max_bytes"):
        zmeta_proto.loads(b"\x08\x00", max_bytes=1)


def test_proto_rejects_oversized_payload():
    event = _load_events()[0]
    encoded = zmeta_proto.dumps(event)

    with pytest.raises(ValueError, match="max_payload_bytes"):
        zmeta_proto.loads(encoded, max_payload_bytes=8)


def test_proto_rejects_deep_payload_json():
    event = _load_events()[0]
    event = {**event, "payload": {"a": {"b": {"c": {"d": 1}}}}}
    encoded = zmeta_proto.dumps(event)

    with pytest.raises(ValueError, match="max_json_depth"):
        zmeta_proto.loads(encoded, max_json_depth=3)


def test_proto_rejects_invalid_field_number():
    with pytest.raises(ValueError, match="field numbers"):
        zmeta_proto.loads(b"\x00\x00")


def test_proto_rejects_unknown_wire_type():
    with pytest.raises(ValueError, match="unsupported protobuf wire type"):
        zmeta_proto.loads(b"\x0b")


def test_proto_rejects_malformed_varint():
    with pytest.raises(ValueError, match="varint is too long"):
        zmeta_proto.loads(b"\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80")


def test_proto_rejects_truncated_length_delimited_field():
    with pytest.raises(ValueError, match="unexpected end of protobuf length-delimited field"):
        zmeta_proto.loads(b"\x0a\x05abc")


def test_proto_rejects_huge_declared_field_length_before_allocation():
    with pytest.raises(ValueError, match="max_field_bytes"):
        zmeta_proto.loads(b"\x0a\xff\xff\xff\xff\x0f", max_field_bytes=8)


def test_proto_rejects_invalid_utf8_string_field():
    with pytest.raises(UnicodeDecodeError):
        zmeta_proto.loads(b"\x0a\x01\xff")


def test_proto_rejects_truncated_fixed_fields():
    with pytest.raises(ValueError, match="fixed64"):
        zmeta_proto.loads(b"\x29\x00\x00")

    with pytest.raises(ValueError, match="fixed32"):
        zmeta_proto.loads(b"\x0d\x00")


def test_proto_random_bytes_do_not_raise_unexpected_exceptions():
    samples = [
        b"",
        b"\xff",
        b"\x12\x03\x08\x96\x01",
        b"\x22\x02{}",
        b"\x22\x07{\"a\":1}",
        bytes(range(32)),
        b"\x12\xff\x01" + (b"\x08\x01" * 64),
    ]

    for sample in samples:
        try:
            decoded = zmeta_proto.loads(sample, max_field_bytes=64, max_payload_bytes=64)
        except (ValueError, UnicodeDecodeError):
            continue
        assert isinstance(decoded, dict)


def test_proto_seeded_random_fuzz_rejects_or_decodes_dict():
    rng = random.Random(0x5A4D455441)

    for _ in range(250):
        size = rng.randrange(0, 160)
        sample = bytes(rng.randrange(0, 256) for _ in range(size))
        try:
            decoded = zmeta_proto.loads(sample, max_field_bytes=64, max_payload_bytes=64)
        except (ValueError, UnicodeDecodeError):
            continue
        assert isinstance(decoded, dict)
