"""
Convert a single ZMeta event between JSON, CBOR, compact CBOR, and protobuf.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import zmeta_cbor
import zmeta_compact
import zmeta_proto


INPUT_ENCODINGS = {"json", "cbor", "compact", "proto", "auto"}
OUTPUT_ENCODINGS = {"json", "cbor", "compact", "proto"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert one ZMeta event between supported wire encodings."
    )
    parser.add_argument(
        "--from",
        dest="source_encoding",
        choices=sorted(INPUT_ENCODINGS),
        required=True,
        help="Input encoding.",
    )
    parser.add_argument(
        "--to",
        dest="target_encoding",
        choices=sorted(OUTPUT_ENCODINGS),
        required=True,
        help="Output encoding.",
    )
    parser.add_argument("--input", "-i", help="Input file. Defaults to stdin.")
    parser.add_argument("--output", "-o", help="Output file. Defaults to stdout.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    parser.add_argument(
        "--allow-jsonl-first",
        action="store_true",
        help="When JSON input contains JSONL, convert the first non-empty line.",
    )
    return parser.parse_args()


def read_input(path: str | None, encoding: str) -> bytes:
    if path:
        return Path(path).read_bytes()
    if encoding == "json":
        return sys.stdin.read().encode("utf-8")
    return sys.stdin.buffer.read()


def write_output(path: str | None, data: bytes, encoding: str) -> None:
    if path:
        Path(path).write_bytes(data)
        return
    if encoding == "json":
        sys.stdout.write(data.decode("utf-8"))
        if not data.endswith(b"\n"):
            sys.stdout.write("\n")
        return
    sys.stdout.buffer.write(data)


def looks_like_event(obj: Any) -> bool:
    return isinstance(obj, dict) and {"event", "source", "payload"}.issubset(obj)


def decode_event(data: bytes, encoding: str, allow_jsonl_first: bool = False) -> Dict[str, Any]:
    if encoding == "json":
        return _decode_json(data, allow_jsonl_first)
    if encoding == "cbor":
        obj = zmeta_cbor.loads(data)
        if not looks_like_event(obj):
            raise ValueError("CBOR input did not decode to a ZMeta event")
        return obj
    if encoding == "compact":
        return zmeta_compact.loads(data)
    if encoding == "proto":
        obj = zmeta_proto.loads(data)
        if not looks_like_event(obj):
            raise ValueError("protobuf input did not decode to a ZMeta event")
        return obj
    if encoding == "auto":
        return _decode_auto(data, allow_jsonl_first)
    raise ValueError(f"unsupported input encoding: {encoding}")


def encode_event(event: Dict[str, Any], encoding: str, pretty: bool = False) -> bytes:
    if encoding == "json":
        if pretty:
            return (json.dumps(event, indent=2, ensure_ascii=True) + "\n").encode("utf-8")
        return (json.dumps(event, separators=(",", ":"), ensure_ascii=True) + "\n").encode(
            "utf-8"
        )
    if encoding == "cbor":
        return zmeta_cbor.dumps(event)
    if encoding == "compact":
        return zmeta_compact.dumps(event)
    if encoding == "proto":
        return zmeta_proto.dumps(event)
    raise ValueError(f"unsupported output encoding: {encoding}")


def _decode_json(data: bytes, allow_jsonl_first: bool = False) -> Dict[str, Any]:
    text = data.decode("utf-8").strip()
    if not text:
        raise ValueError("empty JSON input")
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        if not allow_jsonl_first:
            raise
        for line in text.splitlines():
            line = line.strip()
            if line:
                obj = json.loads(line)
                break
        else:
            raise ValueError("no JSONL event found")
    if not looks_like_event(obj):
        raise ValueError("JSON input did not decode to a ZMeta event")
    return obj


def _decode_auto(data: bytes, allow_jsonl_first: bool = False) -> Dict[str, Any]:
    prefix = data.lstrip()[:1]
    if prefix in (b"{", b"["):
        return _decode_json(data, allow_jsonl_first)

    try:
        obj = zmeta_cbor.loads(data)
        if zmeta_compact.is_compact(obj):
            return zmeta_compact.decode_event(obj)
        if looks_like_event(obj):
            return obj
    except Exception:
        pass

    obj = zmeta_proto.loads(data)
    if not looks_like_event(obj):
        raise ValueError("auto input did not decode to a ZMeta event")
    return obj


def main() -> None:
    args = parse_args()
    data = read_input(args.input, args.source_encoding)
    event = decode_event(data, args.source_encoding, args.allow_jsonl_first)
    out = encode_event(event, args.target_encoding, args.pretty)
    write_output(args.output, out, args.target_encoding)


if __name__ == "__main__":
    main()
