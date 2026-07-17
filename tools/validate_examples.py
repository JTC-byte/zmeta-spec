import argparse
import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATORS_PATH = ROOT / "gateway" / "src" / "validators.py"
spec = importlib.util.spec_from_file_location("zmeta_validators", VALIDATORS_PATH)
validators = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validators)


EXAMPLE_MAP = [
    ("examples/zmeta-examples-1.0.jsonl", "H"),
    ("examples/zmeta-profile-L-examples.jsonl", "L"),
    ("examples/zmeta-profile-M-examples.jsonl", "M"),
    ("examples/zmeta-profile-H-examples.jsonl", "H"),
    ("examples/zmeta-command-examples.jsonl", "L"),
    ("examples/encoding-roundtrip.jsonl", "L"),
    ("examples/zmeta-v1.1-examples.jsonl", "H"),
    ("examples/zmeta-correlation-pattern-examples.jsonl", "H"),
    ("examples/zmeta-eo-chain-examples.jsonl", "H"),
]


def parse_args():
    parser = argparse.ArgumentParser(description="Validate all example JSONL files.")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures.")
    parser.add_argument(
        "--require-all",
        action="store_true",
        help="Fail if any expected example file is missing.",
    )
    return parser.parse_args()


def iter_jsonl(path):
    with open(path, "r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            yield line_no, line


def event_id_from_instance(instance):
    if isinstance(instance, dict):
        return instance.get("event", {}).get("event_id", "UNKNOWN")
    return "UNKNOWN"


def validate_file(path: Path, profile: str, validator, policy, severity_map, strict: bool) -> dict:
    total = 0
    passed = 0
    failed = 0
    warnings = 0
    state = validators.ValidationState()

    items = list(iter_jsonl(path))

    for line_no, raw in items:
        total += 1
        try:
            instance = json.loads(raw)
        except json.JSONDecodeError:
            warnings += 1
            print(f"WARN SCHEMA_INVALID event_id=UNKNOWN line={line_no} file={path}")
            continue

        if not isinstance(instance, dict):
            warnings += 1
            print(f"WARN SCHEMA_INVALID event_id=UNKNOWN line={line_no} file={path}")
            continue

        ok, violations = validators.validate_schema(instance, validator, severity_map)
        if violations:
            failed += 1
            event_id = event_id_from_instance(instance)
            print(f"FAIL {violations[0]['code']} event_id={event_id} file={path}")
            continue

        checks = [
            validators.validate_role(instance, {"roles": policy["roles"], "deny": policy["deny"]}, severity_map),
            validators.validate_profile(instance, profile, policy["profiles"], severity_map),
            validators.validate_timing_quality(
                instance,
                policy["semantics"],
                state=state,
                severity_map=severity_map,
                timing_freshness_policy=policy.get("timing_freshness", {}),
                profile=profile,
            ),
            validators.validate_semantics(instance, policy["semantics"], severity_map),
            validators.validate_lineage(
                instance,
                policy.get("lineage", {}),
                state=state,
                profile=profile,
                severity_map=severity_map,
            ),
            validators.validate_producer_authority(
                instance, policy.get("producer_authority", {}), severity_map
            ),
            validators.validate_routing(instance, policy["routing"], severity_map),
            validators.validate_deduplication(instance, state=state, severity_map=severity_map),
        ]

        event_id = event_id_from_instance(instance)
        failed_local = False
        warned_local = False
        for _ok, violations in checks:
            for violation in violations:
                if violation.get("severity") == "warn":
                    warnings += 1
                    warned_local = True
                    print(f"WARN {violation['code']} event_id={event_id} file={path}")
                else:
                    failed += 1
                    failed_local = True
                    print(f"FAIL {violation['code']} event_id={event_id} file={path}")
        if failed_local:
            continue
        state.record(instance)
        if warned_local:
            continue

        passed += 1

    if strict and warnings:
        failed += warnings
        warnings = 0

    return {"total": total, "passed": passed, "failed": failed, "warnings": warnings}


def run(*, strict=False, require_all=False, root=None, example_map=None):
    root = Path(root) if root else ROOT
    example_map = example_map if example_map is not None else EXAMPLE_MAP
    schema_path = ROOT / "schema" / "zmeta-event.schema.json"
    policy_dir = ROOT / "policy"

    validator = validators.load_schema(schema_path)
    policy = validators.load_policy(policy_dir)
    severity_map = policy.get("violation_severities", {})

    missing = []
    empty = []
    overall = {"total": 0, "passed": 0, "failed": 0, "warnings": 0}

    for rel_path, profile in example_map:
        path = root / rel_path
        if not path.exists():
            missing.append(rel_path)
            print(f"WARN missing file {rel_path}")
            continue
        stats = validate_file(path, profile, validator, policy, severity_map, strict)
        if stats["total"] == 0:
            # A registered corpus file that exists but holds zero events must
            # not pass silently - an empty file proves nothing.
            empty.append(rel_path)
            label = "FAIL" if (strict or require_all) else "WARN"
            print(f"{label} empty corpus {rel_path} contains no events - an empty file proves nothing")
        overall["total"] += stats["total"]
        overall["passed"] += stats["passed"]
        overall["failed"] += stats["failed"]
        overall["warnings"] += stats["warnings"]
        print(
            f"{rel_path} profile={profile} total={stats['total']} "
            f"passed={stats['passed']} failed={stats['failed']} warnings={stats['warnings']}"
        )

    if missing and require_all:
        overall["failed"] += len(missing)
    if empty and (strict or require_all):
        overall["failed"] += len(empty)

    print(
        f"overall total={overall['total']} passed={overall['passed']} "
        f"failed={overall['failed']} warnings={overall['warnings']}"
    )

    return 1 if overall["failed"] else 0


def main():
    args = parse_args()
    raise SystemExit(run(strict=args.strict, require_all=args.require_all))


if __name__ == "__main__":
    main()
