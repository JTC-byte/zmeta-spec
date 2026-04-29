"""
Minimal deterministic CBOR encoder/decoder for ZMeta payloads.

Supports: dict, list/tuple, str, bytes/bytearray, int, float, bool, None.
This is a fallback when cbor2 is unavailable. Maps are encoded using canonical
CBOR key ordering so equivalent objects produce stable bytes. Decoding enforces
default message, item, container, and nesting limits for untrusted network input.
"""

from __future__ import annotations

import math
import struct
from typing import Any, Tuple


DEFAULT_MAX_MESSAGE_BYTES = 1_048_576
DEFAULT_MAX_ITEM_BYTES = 524_288
DEFAULT_MAX_CONTAINER_ITEMS = 65_536
DEFAULT_MAX_DEPTH = 64


def dumps(obj: Any) -> bytes:
    return _encode(obj)


def loads(
    data: bytes,
    *,
    max_bytes: int | None = DEFAULT_MAX_MESSAGE_BYTES,
    max_item_bytes: int | None = DEFAULT_MAX_ITEM_BYTES,
    max_container_items: int | None = DEFAULT_MAX_CONTAINER_ITEMS,
    max_depth: int | None = DEFAULT_MAX_DEPTH,
) -> Any:
    data = _coerce_bytes(data)
    _validate_limit(max_bytes, "max_bytes")
    _validate_limit(max_item_bytes, "max_item_bytes")
    _validate_limit(max_container_items, "max_container_items")
    _validate_limit(max_depth, "max_depth")
    if max_bytes is not None and len(data) > max_bytes:
        raise ValueError("CBOR message exceeds max_bytes")

    value, index = _decode(
        data,
        0,
        depth=0,
        max_item_bytes=max_item_bytes,
        max_container_items=max_container_items,
        max_depth=max_depth,
    )
    if index != len(data):
        raise ValueError("extra bytes after top-level CBOR item")
    return value


def _encode(obj: Any) -> bytes:
    if obj is None:
        return bytes([0xF6])
    if obj is False:
        return bytes([0xF4])
    if obj is True:
        return bytes([0xF5])
    if isinstance(obj, int) and not isinstance(obj, bool):
        if obj >= 0:
            return _encode_uint(0, obj)
        return _encode_uint(1, -1 - obj)
    if isinstance(obj, float):
        return bytes([0xFB]) + struct.pack(">d", obj)
    if isinstance(obj, (bytes, bytearray)):
        payload = bytes(obj)
        return _encode_uint(2, len(payload)) + payload
    if isinstance(obj, str):
        payload = obj.encode("utf-8")
        return _encode_uint(3, len(payload)) + payload
    if isinstance(obj, (list, tuple)):
        items = b"".join(_encode(item) for item in obj)
        return _encode_uint(4, len(obj)) + items
    if isinstance(obj, dict):
        items = []
        for key, value in obj.items():
            encoded_key = _encode(key)
            encoded_value = _encode(value)
            items.append((encoded_key, encoded_value))
        items.sort(key=lambda item: (len(item[0]), item[0]))
        payload_parts = []
        for encoded_key, encoded_value in items:
            payload_parts.append(encoded_key)
            payload_parts.append(encoded_value)
        payload = b"".join(payload_parts)
        return _encode_uint(5, len(obj)) + payload
    raise TypeError(f"unsupported type for CBOR encoding: {type(obj).__name__}")


def _encode_uint(major: int, value: int) -> bytes:
    if value < 0:
        raise ValueError("value must be non-negative")
    if value < 24:
        return bytes([(major << 5) | value])
    if value < 256:
        return bytes([(major << 5) | 24, value])
    if value < 65536:
        return bytes([(major << 5) | 25]) + struct.pack(">H", value)
    if value < 2**32:
        return bytes([(major << 5) | 26]) + struct.pack(">I", value)
    if value < 2**64:
        return bytes([(major << 5) | 27]) + struct.pack(">Q", value)
    raise OverflowError("integer too large for CBOR")


def _decode(
    data: bytes,
    index: int,
    *,
    depth: int,
    max_item_bytes: int | None,
    max_container_items: int | None,
    max_depth: int | None,
) -> Tuple[Any, int]:
    _check_depth(depth, max_depth)
    if index >= len(data):
        raise ValueError("unexpected end of data")
    initial = data[index]
    index += 1
    major = initial >> 5
    addl = initial & 0x1F

    if major == 0:
        value, index = _read_uint(data, index, addl)
        return value, index
    if major == 1:
        value, index = _read_uint(data, index, addl)
        return -1 - value, index
    if major == 2:
        length, index = _read_uint(data, index, addl)
        _check_item_length(length, max_item_bytes)
        payload = _read_bytes(data, index, length)
        return payload, index + length
    if major == 3:
        length, index = _read_uint(data, index, addl)
        _check_item_length(length, max_item_bytes)
        payload = _read_bytes(data, index, length)
        return payload.decode("utf-8"), index + length
    if major == 4:
        length, index = _read_uint(data, index, addl)
        _check_container_length(length, max_container_items)
        items = []
        for _ in range(length):
            item, index = _decode(
                data,
                index,
                depth=depth + 1,
                max_item_bytes=max_item_bytes,
                max_container_items=max_container_items,
                max_depth=max_depth,
            )
            items.append(item)
        return items, index
    if major == 5:
        length, index = _read_uint(data, index, addl)
        _check_container_length(length, max_container_items)
        mapping = {}
        for _ in range(length):
            key, index = _decode(
                data,
                index,
                depth=depth + 1,
                max_item_bytes=max_item_bytes,
                max_container_items=max_container_items,
                max_depth=max_depth,
            )
            value, index = _decode(
                data,
                index,
                depth=depth + 1,
                max_item_bytes=max_item_bytes,
                max_container_items=max_container_items,
                max_depth=max_depth,
            )
            try:
                mapping[key] = value
            except TypeError as exc:
                raise ValueError("CBOR map key is not hashable") from exc
        return mapping, index
    if major == 6:
        # tag; ignore and decode tagged item
        _tag, index = _read_uint(data, index, addl)
        return _decode(
            data,
            index,
            depth=depth + 1,
            max_item_bytes=max_item_bytes,
            max_container_items=max_container_items,
            max_depth=max_depth,
        )
    if major == 7:
        return _decode_simple(data, index, addl)

    raise ValueError(f"unsupported CBOR major type: {major}")


def _read_uint(data: bytes, index: int, addl: int) -> Tuple[int, int]:
    if addl < 24:
        return addl, index
    if addl == 24:
        return _read_uint_n(data, index, 1)
    if addl == 25:
        return _read_uint_n(data, index, 2)
    if addl == 26:
        return _read_uint_n(data, index, 4)
    if addl == 27:
        return _read_uint_n(data, index, 8)
    raise ValueError("indefinite lengths not supported in this CBOR decoder")


def _read_uint_n(data: bytes, index: int, length: int) -> Tuple[int, int]:
    end = index + length
    if end > len(data):
        raise ValueError("unexpected end of data")
    value = int.from_bytes(data[index:end], byteorder="big", signed=False)
    return value, end


def _read_bytes(data: bytes, index: int, length: int) -> bytes:
    end = index + length
    if end > len(data):
        raise ValueError("unexpected end of data")
    return data[index:end]


def _check_item_length(length: int, max_item_bytes: int | None) -> None:
    if max_item_bytes is not None and length > max_item_bytes:
        raise ValueError("CBOR byte/text item exceeds max_item_bytes")


def _check_container_length(length: int, max_container_items: int | None) -> None:
    if max_container_items is not None and length > max_container_items:
        raise ValueError("CBOR array/map exceeds max_container_items")


def _check_depth(depth: int, max_depth: int | None) -> None:
    if max_depth is not None and depth > max_depth:
        raise ValueError("CBOR nesting exceeds max_depth")


def _coerce_bytes(data: bytes) -> bytes:
    if isinstance(data, bytes):
        return data
    if isinstance(data, (bytearray, memoryview)):
        return bytes(data)
    raise TypeError("CBOR input must be bytes-like")


def _validate_limit(value: int | None, name: str) -> None:
    if value is not None and value < 0:
        raise ValueError(f"{name} must be non-negative or None")


def _decode_simple(data: bytes, index: int, addl: int) -> Tuple[Any, int]:
    if addl == 20:
        return False, index
    if addl == 21:
        return True, index
    if addl == 22:
        return None, index
    if addl == 23:
        return None, index
    if addl == 24:
        value, index = _read_uint_n(data, index, 1)
        return value, index
    if addl == 25:
        bits, index = _read_uint_n(data, index, 2)
        return _float16(bits), index
    if addl == 26:
        end = index + 4
        if end > len(data):
            raise ValueError("unexpected end of data")
        return struct.unpack(">f", data[index:end])[0], end
    if addl == 27:
        end = index + 8
        if end > len(data):
            raise ValueError("unexpected end of data")
        return struct.unpack(">d", data[index:end])[0], end
    raise ValueError("unsupported simple value")


def _float16(bits: int) -> float:
    sign = (bits >> 15) & 0x01
    exp = (bits >> 10) & 0x1F
    frac = bits & 0x3FF
    if exp == 0:
        if frac == 0:
            return -0.0 if sign else 0.0
        return (-1.0 if sign else 1.0) * (2 ** -14) * (frac / 1024.0)
    if exp == 31:
        if frac == 0:
            return -math.inf if sign else math.inf
        return math.nan
    return (-1.0 if sign else 1.0) * (2 ** (exp - 15)) * (1 + frac / 1024.0)
