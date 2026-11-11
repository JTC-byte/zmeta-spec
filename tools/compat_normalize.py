import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from compat_normalizer import (  # noqa: E402
    CompatibilityNormalizationError,
    CompatibilityOptions,
    normalize_event,
)
from zmeta_decode_guard import DecodeAmbiguousError, pairs_refusing_duplicates  # noqa: E402


def parse_args():
    parser = argparse.ArgumentParser(
        description="Non-normative compatibility normalizer for ZMeta events"
    )
    parser.add_argument("--input", required=True, help="Input JSON or JSONL file")
    parser.add_argument(
        "--output",
        help="Output JSON or JSONL file. Defaults to stdout.",
    )
    parser.add_argument(
        "--report",
        help="Write sidecar JSON normalization report to this path. Defaults to stderr.",
    )
    parser.add_argument(
        "--allow-version-alias",
        action="store_true",
        help='Normalize zmeta_version "1.1" to "1.1.0".',
    )
    parser.add_argument(
        "--convert-endurance-seconds",
        action="store_true",
        help="Convert PLATFORM_STATUS metrics.endurance_remaining_sec to endurance_remaining_ms.",
    )
    parser.add_argument(
        "--assume-eo-bbox-roi",
        action="store_true",
        help="Rename EO features.bbox to roi_px only when bbox is known ROI metadata.",
    )
    return parser.parse_args()


def _read_items(path: Path):
    """Read the input as the gateway reads it.

    A member name repeated in one object is refused, never resolved to its
    last value (contract 3.5). Returns `(is_jsonl, items, refused)`. A
    `.jsonl` file is refused line by line; a `.json` document is one JSON
    text, so one repeat anywhere in it refuses the whole document, reported
    at line 1.
    """
    refused = []
    if path.suffix.lower() == ".jsonl":
        items = []
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            line = line.strip()
            if not line:
                continue
            try:
                items.append((line_no, json.loads(line, object_pairs_hook=pairs_refusing_duplicates)))
            except DecodeAmbiguousError as exc:
                refused.append({"line": line_no, "code": "DECODE_AMBIGUOUS", "message": str(exc)})
        return True, items, refused

    try:
        data = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=pairs_refusing_duplicates)
    except DecodeAmbiguousError as exc:
        return False, [], [{"line": 1, "code": "DECODE_AMBIGUOUS", "message": str(exc)}]
    if isinstance(data, list):
        return False, list(enumerate(data, start=1)), refused
    return False, [(1, data)], refused


def _write_output(path: str | None, is_jsonl: bool, normalized_items):
    if is_jsonl:
        content = "\n".join(json.dumps(item, separators=(",", ":")) for item in normalized_items)
        if content:
            content += "\n"
    elif len(normalized_items) == 1:
        content = json.dumps(normalized_items[0], indent=2) + "\n"
    else:
        content = json.dumps(normalized_items, indent=2) + "\n"

    if path:
        Path(path).write_text(content, encoding="utf-8")
    else:
        sys.stdout.write(content)


def _write_report(path: str | None, report):
    content = json.dumps(report, indent=2) + "\n"
    if path:
        Path(path).write_text(content, encoding="utf-8")
    else:
        sys.stderr.write(content)


def main():
    args = parse_args()
    options = CompatibilityOptions(
        allow_version_alias=args.allow_version_alias,
        convert_endurance_seconds=args.convert_endurance_seconds,
        rename_eo_bbox_roi=args.assume_eo_bbox_roi,
    )

    input_path = Path(args.input)
    is_jsonl, items, refused = _read_items(input_path)
    normalized_items = []
    report = {"input": str(input_path), "changes": [], "rejected": list(refused)}

    for line_no, event in items:
        try:
            normalized, changes = normalize_event(event, options)
        except CompatibilityNormalizationError as exc:
            report["rejected"].append({"line": line_no, **exc.to_dict()})
            continue
        normalized_items.append(normalized)
        for change in changes:
            report["changes"].append({"line": line_no, **change})

    report["rejected"].sort(key=lambda item: item["line"])
    _write_report(args.report, report)
    if report["rejected"]:
        return 1

    _write_output(args.output, is_jsonl, normalized_items)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
