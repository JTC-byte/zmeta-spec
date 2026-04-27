"""
Experimental protobuf wire projection for ZMeta events.

This module intentionally avoids generated-code dependencies so the reference
stack can round-trip protobuf-encoded events in constrained environments. The
wire layout matches schema/proto/zmeta_event_v1.proto.
"""

from __future__ import annotations

import json
import struct
from typing import Any, Dict, Tuple


WIRE_VARINT = 0
WIRE_FIXED64 = 1
WIRE_LEN = 2
WIRE_FIXED32 = 5


def dumps(event: Dict[str, Any]) -> bytes:
    parts = []
    if event.get("zmeta_version") is not None:
        parts.append(_field_string(1, event["zmeta_version"]))
    if isinstance(event.get("event"), dict):
        parts.append(_field_message(2, _encode_event_block(event["event"])))
    if isinstance(event.get("source"), dict):
        parts.append(_field_message(3, _encode_source(event["source"])))
    if "payload" in event:
        parts.append(_field_bytes(4, _payload_to_bytes(event["payload"])))
    if event.get("confidence") is not None:
        parts.append(_field_double(5, float(event["confidence"])))
    if isinstance(event.get("lineage"), dict):
        parts.append(_field_message(6, _encode_lineage(event["lineage"])))
    if event.get("profile") is not None:
        parts.append(_field_string(7, event["profile"]))
    return b"".join(parts)


def loads(data: bytes) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    index = 0
    while index < len(data):
        field, wire_type, index = _read_key(data, index)
        if field == 1 and wire_type == WIRE_LEN:
            value, index = _read_string(data, index)
            out["zmeta_version"] = value
        elif field == 2 and wire_type == WIRE_LEN:
            value, index = _read_message(data, index)
            out["event"] = _decode_event_block(value)
        elif field == 3 and wire_type == WIRE_LEN:
            value, index = _read_message(data, index)
            out["source"] = _decode_source(value)
        elif field == 4 and wire_type == WIRE_LEN:
            value, index = _read_bytes(data, index)
            out["payload"] = _payload_from_bytes(value)
        elif field == 5 and wire_type == WIRE_FIXED64:
            value, index = _read_double(data, index)
            out["confidence"] = value
        elif field == 6 and wire_type == WIRE_LEN:
            value, index = _read_message(data, index)
            out["lineage"] = _decode_lineage(value)
        elif field == 7 and wire_type == WIRE_LEN:
            value, index = _read_string(data, index)
            out["profile"] = value
        else:
            index = _skip_field(data, index, wire_type)
    return out


def is_proto_message(data: bytes) -> bool:
    try:
        event = loads(data)
    except Exception:
        return False
    return isinstance(event, dict) and {"event", "source", "payload"}.issubset(event)


def _payload_to_bytes(payload: Any) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )


def _payload_from_bytes(payload: bytes) -> Any:
    return json.loads(payload.decode("utf-8"))


def _encode_event_block(block: Dict[str, Any]) -> bytes:
    parts = []
    for number, key in (
        (1, "event_id"),
        (2, "event_type"),
        (3, "event_subtype"),
        (4, "ts"),
        (5, "t_publish"),
        (6, "t_receive"),
    ):
        if block.get(key) is not None:
            parts.append(_field_string(number, block[key]))
    return b"".join(parts)


def _decode_event_block(data: bytes) -> Dict[str, Any]:
    names = {
        1: "event_id",
        2: "event_type",
        3: "event_subtype",
        4: "ts",
        5: "t_publish",
        6: "t_receive",
    }
    return _decode_string_fields(data, names)


def _encode_source(source: Dict[str, Any]) -> bytes:
    parts = []
    for number, key in (
        (1, "platform_id"),
        (2, "node_role"),
        (3, "producer"),
        (4, "sensor_id"),
        (5, "sw_version"),
    ):
        if source.get(key) is not None:
            parts.append(_field_string(number, source[key]))
    return b"".join(parts)


def _decode_source(data: bytes) -> Dict[str, Any]:
    names = {
        1: "platform_id",
        2: "node_role",
        3: "producer",
        4: "sensor_id",
        5: "sw_version",
    }
    return _decode_string_fields(data, names)


def _encode_lineage(lineage: Dict[str, Any]) -> bytes:
    parts = []
    for value in lineage.get("based_on", []):
        if value is not None:
            parts.append(_field_string(1, value))
    if lineage.get("transform") is not None:
        parts.append(_field_string(2, lineage["transform"]))
    return b"".join(parts)


def _decode_lineage(data: bytes) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    based_on = []
    index = 0
    while index < len(data):
        field, wire_type, index = _read_key(data, index)
        if field == 1 and wire_type == WIRE_LEN:
            value, index = _read_string(data, index)
            based_on.append(value)
        elif field == 2 and wire_type == WIRE_LEN:
            value, index = _read_string(data, index)
            out["transform"] = value
        else:
            index = _skip_field(data, index, wire_type)
    if based_on:
        out["based_on"] = based_on
    return out


def _decode_string_fields(data: bytes, names: Dict[int, str]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    index = 0
    while index < len(data):
        field, wire_type, index = _read_key(data, index)
        if field in names and wire_type == WIRE_LEN:
            value, index = _read_string(data, index)
            out[names[field]] = value
        else:
            index = _skip_field(data, index, wire_type)
    return out


def _field_key(number: int, wire_type: int) -> bytes:
    if number <= 0:
        raise ValueError("protobuf field numbers must be positive")
    return _varint((number << 3) | wire_type)


def _field_string(number: int, value: Any) -> bytes:
    return _field_bytes(number, str(value).encode("utf-8"))


def _field_bytes(number: int, value: bytes) -> bytes:
    return _field_key(number, WIRE_LEN) + _varint(len(value)) + value


def _field_message(number: int, value: bytes) -> bytes:
    return _field_bytes(number, value)


def _field_double(number: int, value: float) -> bytes:
    return _field_key(number, WIRE_FIXED64) + struct.pack("<d", value)


def _varint(value: int) -> bytes:
    if value < 0:
        raise ValueError("varint value must be non-negative")
    parts = []
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            parts.append(byte | 0x80)
        else:
            parts.append(byte)
            break
    return bytes(parts)


def _read_key(data: bytes, index: int) -> Tuple[int, int, int]:
    key, index = _read_varint(data, index)
    return key >> 3, key & 0x07, index


def _read_varint(data: bytes, index: int) -> Tuple[int, int]:
    shift = 0
    value = 0
    while True:
        if index >= len(data):
            raise ValueError("unexpected end of protobuf varint")
        byte = data[index]
        index += 1
        value |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return value, index
        shift += 7
        if shift >= 70:
            raise ValueError("protobuf varint is too long")


def _read_bytes(data: bytes, index: int) -> Tuple[bytes, int]:
    length, index = _read_varint(data, index)
    end = index + length
    if end > len(data):
        raise ValueError("unexpected end of protobuf length-delimited field")
    return data[index:end], end


def _read_message(data: bytes, index: int) -> Tuple[bytes, int]:
    return _read_bytes(data, index)


def _read_string(data: bytes, index: int) -> Tuple[str, int]:
    value, index = _read_bytes(data, index)
    return value.decode("utf-8"), index


def _read_double(data: bytes, index: int) -> Tuple[float, int]:
    end = index + 8
    if end > len(data):
        raise ValueError("unexpected end of protobuf fixed64 field")
    return struct.unpack("<d", data[index:end])[0], end


def _skip_field(data: bytes, index: int, wire_type: int) -> int:
    if wire_type == WIRE_VARINT:
        _value, index = _read_varint(data, index)
        return index
    if wire_type == WIRE_FIXED64:
        end = index + 8
        if end > len(data):
            raise ValueError("unexpected end of protobuf fixed64 field")
        return end
    if wire_type == WIRE_LEN:
        _value, index = _read_bytes(data, index)
        return index
    if wire_type == WIRE_FIXED32:
        end = index + 4
        if end > len(data):
            raise ValueError("unexpected end of protobuf fixed32 field")
        return end
    raise ValueError(f"unsupported protobuf wire type: {wire_type}")
