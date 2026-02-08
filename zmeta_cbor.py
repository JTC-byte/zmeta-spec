"""
Minimal CBOR encoder/decoder for ZMeta payloads.
Supports: dict, list/tuple, str, bytes/bytearray, int, float, bool, None.
This is a fallback when cbor2 is unavailable.
"""

from __future__ import annotations

import math
import struct
from typing import Any, Tuple


def dumps(obj: Any) -> bytes:
    return _encode(obj)


def loads(data: bytes) -> Any:
    value, index = _decode(data, 0)
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
            items.append(_encode(key))
            items.append(_encode(value))
        payload = b"".join(items)
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


def _decode(data: bytes, index: int) -> Tuple[Any, int]:
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
        payload = _read_bytes(data, index, length)
        return payload, index + length
    if major == 3:
        length, index = _read_uint(data, index, addl)
        payload = _read_bytes(data, index, length)
        return payload.decode("utf-8"), index + length
    if major == 4:
        length, index = _read_uint(data, index, addl)
        items = []
        for _ in range(length):
            item, index = _decode(data, index)
            items.append(item)
        return items, index
    if major == 5:
        length, index = _read_uint(data, index, addl)
        mapping = {}
        for _ in range(length):
            key, index = _decode(data, index)
            value, index = _decode(data, index)
            mapping[key] = value
        return mapping, index
    if major == 6:
        # tag; ignore and decode tagged item
        _tag, index = _read_uint(data, index, addl)
        return _decode(data, index)
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
