"""
Measure packet sizes for ZMeta JSONL across JSON, CBOR, compact, and protobuf encodings.
"""

from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Iterable, List
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import zmeta_cbor
import zmeta_compact
import zmeta_proto


def _iter_events(path: Path) -> Iterable[Dict[str, Any]]:
    for line in path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text or text.startswith("#"):
            continue
        yield json.loads(text)


def _event_label(event: Dict[str, Any]) -> str:
    block = event.get("event", {})
    event_type = block.get("event_type", "UNKNOWN")
    subtype = block.get("event_subtype")
    if subtype:
        return f"{event_type}/{subtype}"
    return str(event_type)


def _strip_paths(event: Dict[str, Any], paths: List[str]) -> Dict[str, Any]:
    if not paths:
        return event
    out = deepcopy(event)
    for path in paths:
        parts = path.split(".")
        cur: Any = out
        for part in parts[:-1]:
            if not isinstance(cur, dict):
                cur = None
                break
            cur = cur.get(part)
        if isinstance(cur, dict):
            cur.pop(parts[-1], None)
    return out


def _size_json(event: Dict[str, Any]) -> int:
    data = json.dumps(event, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return len(data)


def _size_cbor(event: Dict[str, Any]) -> int:
    return len(zmeta_cbor.dumps(event))


def _size_compact(event: Dict[str, Any]) -> int:
    return len(zmeta_compact.dumps(event))


def _size_proto(event: Dict[str, Any]) -> int:
    return len(zmeta_proto.dumps(event))


def _summary(values: List[int]) -> str:
    if not values:
        return "min=0 avg=0 max=0"
    avg = sum(values) / len(values)
    return f"min={min(values)} avg={avg:.1f} max={max(values)}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Measure ZMeta packet sizes.")
    parser.add_argument("--file", required=True, help="Path to JSONL file.")
    parser.add_argument(
        "--encodings",
        default="json,cbor,compact,proto",
        help="Comma-separated list: json,cbor,compact,proto",
    )
    parser.add_argument("--event-type", help="Filter by event_type.")
    parser.add_argument("--event-subtype", help="Filter by event_subtype.")
    parser.add_argument(
        "--strip",
        action="append",
        default=[],
        help="Dotted path to remove (repeatable). Example: payload.data_ref",
    )
    parser.add_argument(
        "--max-bytes",
        type=int,
        help="Fail if any event exceeds this size (selected encoding).",
    )
    parser.add_argument(
        "--max-bytes-encoding",
        choices=["json", "cbor", "compact", "proto"],
        help="Encoding to enforce max-bytes for. Required if multiple encodings are selected.",
    )
    parser.add_argument("--summary-only", action="store_true", help="Only print summary.")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        raise SystemExit(f"File not found: {path}")

    encodings = [item.strip().lower() for item in args.encodings.split(",") if item.strip()]
    valid = {"json", "cbor", "compact", "proto"}
    for encoding in encodings:
        if encoding not in valid:
            raise SystemExit(f"Unsupported encoding: {encoding}")

    budget_encoding = None
    if args.max_bytes is not None:
        if args.max_bytes <= 0:
            raise SystemExit("--max-bytes must be > 0")
        if args.max_bytes_encoding:
            budget_encoding = args.max_bytes_encoding
        elif len(encodings) == 1:
            budget_encoding = encodings[0]
        else:
            raise SystemExit("--max-bytes-encoding is required when multiple encodings are selected")

    rows = []
    oversized = []
    for event in _iter_events(path):
        if args.event_type and event.get("event", {}).get("event_type") != args.event_type:
            continue
        if args.event_subtype and event.get("event", {}).get("event_subtype") != args.event_subtype:
            continue
        trimmed = _strip_paths(event, args.strip)
        label = _event_label(trimmed)
        sizes: Dict[str, int] = {}
        if "json" in encodings:
            sizes["json"] = _size_json(trimmed)
        if "cbor" in encodings:
            sizes["cbor"] = _size_cbor(trimmed)
        if "compact" in encodings:
            sizes["compact"] = _size_compact(trimmed)
        if "proto" in encodings:
            sizes["proto"] = _size_proto(trimmed)
        rows.append((label, sizes))
        if budget_encoding:
            size_value = sizes.get(budget_encoding)
            if size_value is not None and size_value > args.max_bytes:
                oversized.append((label, size_value))

    if not rows:
        raise SystemExit("No events matched the filters.")

    print(f"File: {path} (events={len(rows)})")
    if args.strip:
        print(f"Stripped: {', '.join(args.strip)}")

    if rows:
        print("Summary:")
        for encoding in encodings:
            values = [sizes[encoding] for _, sizes in rows if encoding in sizes]
            print(f"  {encoding.upper()}: {_summary(values)}")

    if oversized:
        print(f"\nBudget exceeded ({budget_encoding.upper()} > {args.max_bytes} bytes):")
        for label, size_value in oversized:
            print(f"  {label}: {size_value} bytes")
        raise SystemExit(1)

    if not args.summary_only:
        print("\nPer-event:")
        for label, sizes in rows:
            parts = " ".join(f"{key.upper()}={value}" for key, value in sizes.items())
            print(f"  {label}: {parts}")


if __name__ == "__main__":
    main()
