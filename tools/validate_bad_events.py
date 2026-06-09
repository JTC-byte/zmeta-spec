from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

VALIDATORS_PATH = ROOT / "gateway" / "src" / "validators.py"
validators_spec = importlib.util.spec_from_file_location("zmeta_validators", VALIDATORS_PATH)
validators = importlib.util.module_from_spec(validators_spec)
validators_spec.loader.exec_module(validators)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate ZMeta semantic bad-event fixtures.")
    parser.add_argument(
        "--must-fail",
        default=str(ROOT / "conformance" / "bad-events" / "must-fail.jsonl"),
        help="JSONL fixture file whose events must fail or warn with expect_code.",
    )
    parser.add_argument("--quiet", action="store_true", help="Only print failures and final summary.")
    return parser.parse_args()


def iter_jsonl(path: Path | str):
    fixture_path = Path(path)
    if not fixture_path.exists():
        raise FileNotFoundError(f"bad-event fixture file not found: {fixture_path}")
    for line_no, line in enumerate(fixture_path.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        yield line_no, json.loads(line)


def _run_checks(
    event: dict[str, Any],
    profile: str,
    policy: dict[str, Any],
    schema_validator: Any,
    state: Any,
) -> list[dict[str, Any]]:
    severity_map = policy.get("violation_severities", {})
    ok, violations = validators.validate_schema(event, schema_validator, severity_map)
    if violations:
        return list(violations)

    checks: list[tuple[bool, list[dict[str, Any]]]] = [
        validators.validate_role(event, {"roles": policy["roles"], "deny": policy["deny"]}, severity_map),
        validators.validate_profile(event, profile, policy["profiles"], severity_map),
        validators.validate_timing_quality(
            event,
            policy["semantics"],
            state=state,
            severity_map=severity_map,
            timing_freshness_policy=policy.get("timing_freshness", {}),
            profile=profile,
        ),
        validators.validate_semantics(event, policy["semantics"], severity_map),
        validators.validate_lineage(
            event,
            policy.get("lineage", {}),
            state=state,
            profile=profile,
            severity_map=severity_map,
        ),
        validators.validate_producer_authority(
            event,
            policy.get("producer_authority", {}),
            severity_map,
        ),
        validators.validate_routing(event, policy["routing"], severity_map),
        validators.validate_deduplication(event, state=state, severity_map=severity_map),
    ]
    out: list[dict[str, Any]] = []
    for _ok, items in checks:
        out.extend(items)
    return out


def evaluate_fixture(
    fixture: dict[str, Any],
    schema_validator: Any,
    policy: dict[str, Any],
) -> dict[str, Any]:
    event = fixture.get("event")
    if not isinstance(event, dict):
        return {"passed": False, "message": "fixture missing event", "codes": []}

    profile = str(fixture.get("profile") or event.get("profile") or "H")
    state = validators.ValidationState()
    for seed in fixture.get("preload", []):
        if isinstance(seed, dict):
            state.record(seed)

    violations = _run_checks(event, profile, policy, schema_validator, state)
    expected_code = fixture.get("expect_code")
    expected_severity = fixture.get("expect_severity")
    matching = [item for item in violations if item.get("code") == expected_code]
    if expected_severity:
        matching = [item for item in matching if item.get("severity") == expected_severity]

    codes = [str(item.get("code")) for item in violations if item.get("code")]
    if not matching:
        expected = str(expected_code)
        if expected_severity:
            expected = f"{expected}/{expected_severity}"
        got = ",".join(codes) or "none"
        return {
            "passed": False,
            "message": f"expected {expected}, got {got}",
            "codes": codes,
            "violations": violations,
        }
    return {"passed": True, "codes": codes, "violations": violations}


def run(*, must_fail_path: Path | str | None = None, quiet: bool = False) -> int:
    path = Path(must_fail_path) if must_fail_path else ROOT / "conformance" / "bad-events" / "must-fail.jsonl"
    schema_validator = validators.load_schema(ROOT / "schema" / "zmeta-event.schema.json")
    policy = validators.load_policy(ROOT / "policy")

    failures = 0
    passed = 0
    for line_no, fixture in iter_jsonl(path):
        label = str(fixture.get("name") or f"line-{line_no}")
        result = evaluate_fixture(fixture, schema_validator, policy)
        if result["passed"]:
            passed += 1
            if not quiet:
                print(f"PASS name={label} expected={fixture.get('expect_code')}")
        else:
            failures += 1
            print(f"FAIL name={label}: {result['message']}")

    if failures:
        print(f"bad-event corpus failed total={passed} failures={failures}")
        return 1
    print(f"bad-event corpus ok total={passed}")
    return 0


def main() -> None:
    args = parse_args()
    raise SystemExit(run(must_fail_path=args.must_fail, quiet=args.quiet))


if __name__ == "__main__":
    main()
