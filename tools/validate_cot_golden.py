"""Check the golden CoT outputs against the reference CoT projection.

`conformance/cot-golden/golden.jsonl` holds one case per line: an example STATE_EVENT, the projection config, a fixed projection
instant, and what the reference projection (`adapters/egress/cot/zmeta_to_cot.py`) gives for it: the CoT XML string, or the
reason it refuses. This tool projects each case again and compares the result byte for byte. A case line that repeats a member
name is refused (contract 3.5), and so is a case that is not well formed: each is reported as a FAIL line naming the line, and
the run fails.

Usage: python tools/validate_cot_golden.py [--golden PATH] [--quiet]
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adapters.egress.cot.zmeta_to_cot import zmeta_to_cot  # noqa: E402
from zmeta_decode_guard import DecodeAmbiguousError, pairs_refusing_duplicates  # noqa: E402

DEFAULT_GOLDEN = ROOT / "conformance" / "cot-golden" / "golden.jsonl"


class CaseError(ValueError):
    """A case line that cannot be checked as written."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check the golden CoT outputs against the reference CoT projection.")
    parser.add_argument("--golden", default=str(DEFAULT_GOLDEN), help="Golden case JSONL file.")
    parser.add_argument("--quiet", action="store_true", help="Only print failures and the final summary.")
    return parser.parse_args()


def read_case(line: str) -> dict:
    """One case line, read as the gateway reads JSON, and checked for shape."""
    try:
        case = json.loads(line, object_pairs_hook=pairs_refusing_duplicates)
    except DecodeAmbiguousError as exc:
        raise CaseError(f"DECODE_AMBIGUOUS {exc}") from exc
    except json.JSONDecodeError as exc:
        raise CaseError(f"invalid JSON: {exc.msg}") from exc
    if not isinstance(case, dict):
        raise CaseError("a case must be a JSON object")
    if not isinstance(case.get("event"), dict):
        raise CaseError("`event` must be an object")
    if not isinstance(case.get("cot_config"), dict):
        raise CaseError("`cot_config` must be an object")
    now = case.get("now")
    if not isinstance(now, str) or not now.endswith("Z"):
        raise CaseError("`now` must be a UTC timestamp ending in Z")
    try:
        datetime.fromisoformat(now[:-1] + "+00:00")
    except ValueError as exc:
        raise CaseError(f"`now` does not parse: {exc}") from exc
    expect = case.get("expect")
    if not isinstance(expect, dict) or len(expect) != 1:
        raise CaseError("`expect` must hold exactly one of `cot_xml` and `refusal`")
    key, value = next(iter(expect.items()))
    if key not in ("cot_xml", "refusal") or not isinstance(value, str) or not value:
        raise CaseError("`expect` must hold a non-empty `cot_xml` string or a non-empty `refusal` reason")
    return case


def project(case: dict) -> dict:
    """What the reference projection gives for one case: {"cot_xml": ...} or {"refusal": ...}."""
    now = datetime.fromisoformat(case["now"][:-1] + "+00:00")
    refusal: dict = {}
    xml = zmeta_to_cot(case["event"], cot_config=case["cot_config"] or None, now=now, refusal=refusal)
    if xml is not None:
        return {"cot_xml": xml}
    return {"refusal": refusal.get("reason")}


def run(*, golden_path: Path | str = DEFAULT_GOLDEN, quiet: bool = False) -> int:
    path = Path(golden_path)
    if not path.exists():
        print(f"FAIL {path} not found")
        return 1
    passed = failures = 0
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            case = read_case(line.strip())
        except CaseError as exc:
            failures += 1
            print(f"FAIL line={line_no} {exc}")
            continue
        name = str(case.get("name") or f"line-{line_no}")
        got = project(case)
        if got != case["expect"]:
            failures += 1
            print(f"FAIL name={name} line={line_no}")
            print(f"  expected {json.dumps(case['expect'])[:300]}")
            print(f"  got      {json.dumps(got)[:300]}")
        else:
            passed += 1
            if not quiet:
                print(f"PASS name={name}")
    if passed + failures == 0:
        print(f"FAIL {path} contains no cases - an empty file proves nothing")
        return 1
    if failures:
        print(f"cot golden failed total={passed} failures={failures}")
        return 1
    print(f"cot golden ok total={passed}")
    return 0


def main() -> None:
    args = parse_args()
    raise SystemExit(run(golden_path=args.golden, quiet=args.quiet))


if __name__ == "__main__":
    main()
