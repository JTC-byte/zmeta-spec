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


def parse_args():
    parser = argparse.ArgumentParser(description="Validate ZMeta events against schema and policy")
    parser.add_argument("--file", required=True)
    parser.add_argument("--profile", choices=["L", "M", "H"], required=True)
    parser.add_argument("--strict", action="store_true")
    return parser.parse_args()


def iter_jsonl(path):
    with open(path, "r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            yield line_no, line


def load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


LANE_SCHEMAS = {
    "1.0": "zmeta-event-1.0.schema.json",
    "1.1.0": "zmeta-event-1.1.0.schema.json",
}

UNION_FALLBACK_HINT = (
    "event declares no known zmeta_version, so it was validated against the "
    "version-discriminated union; declare zmeta_version as one of "
    + "/".join(sorted(LANE_SCHEMAS))
    + " for branch-level diagnostics"
)


def _detail(violation):
    """The violation's message and path, when it carries ones worth showing.

    Step 2 of the adapter ladder printed the reason_code alone, so an author
    hitting PRODUCER_NOT_ALLOWED saw a bare code and nothing pointing at the
    policy file, the reference wildcards, or AUTHORING.md section 7 -- while
    step 3 printed the full message. The diagnostic that explains the wall
    should reach the first step that hits it, not the third. The same
    lesson repeated for schema failures: the path was recorded in the
    violation and dropped here, so a nested enum mismatch printed as an
    opaque event dump (the PR #8 field pass reported walking branch-level
    diagnostics by hand for twelve events).
    """
    message = violation.get("message")
    path = (violation.get("details") or {}).get("path")
    parts = ""
    if path:
        parts += "\n  at: " + path
    if message:
        parts += "\n  " + message
    return parts


def event_id_from_instance(instance):
    if isinstance(instance, dict):
        return instance.get("event", {}).get("event_id", "UNKNOWN")
    return "UNKNOWN"


def main():
    args = parse_args()
    schema_path = ROOT / "schema" / "zmeta-event.schema.json"
    policy_dir = ROOT / "policy"

    validator = validators.load_schema(schema_path)
    lane_validators = {
        lane: validators.load_schema(ROOT / "schema" / filename)
        for lane, filename in LANE_SCHEMAS.items()
    }
    policy = validators.load_policy(policy_dir)
    severity_map = policy.get("violation_severities", {})
    state = validators.ValidationState()

    total = 0
    passed = 0
    failed = 0
    warnings = 0

    path = Path(args.file)
    is_jsonl = path.suffix.lower() == ".jsonl"

    if is_jsonl:
        items = list(iter_jsonl(path))
    else:
        try:
            obj = load_json(path)
        except json.JSONDecodeError as exc:
            total = 1
            failed = 1
            print(f"FAIL SCHEMA_INVALID event_id=UNKNOWN error={exc}")
            print(f"total={total} passed={passed} failed={failed} warnings={warnings}")
            raise SystemExit(1)
        if isinstance(obj, list):
            items = [(index + 1, json.dumps(item)) for index, item in enumerate(obj)]
        else:
            items = [(1, json.dumps(obj))]

    for line_no, raw in items:
        total += 1
        try:
            instance = json.loads(raw)
        except json.JSONDecodeError:
            warnings += 1
            print(f"WARN SCHEMA_INVALID event_id=UNKNOWN line={line_no}")
            continue

        if not isinstance(instance, dict):
            warnings += 1
            print(f"WARN SCHEMA_INVALID event_id=UNKNOWN line={line_no}")
            continue

        declared_version = instance.get("zmeta_version")
        lane_validator = (
            lane_validators.get(declared_version)
            if isinstance(declared_version, str)
            else None
        )
        union_fallback = lane_validator is None
        ok, violations = validators.validate_schema(
            instance, validator if union_fallback else lane_validator, severity_map
        )
        if violations:
            failed += 1
            event_id = event_id_from_instance(instance)
            for violation in violations:
                print(f"FAIL {violation['code']} event_id={event_id}"
                      + _detail(violation))
            if union_fallback:
                print("  " + UNION_FALLBACK_HINT)
            continue

        checks = [
            validators.validate_role(instance, {"roles": policy["roles"], "deny": policy["deny"]}, severity_map),
            validators.validate_profile(instance, args.profile, policy["profiles"], severity_map),
            validators.validate_timing_quality(
                instance,
                policy["semantics"],
                state=state,
                severity_map=severity_map,
                timing_freshness_policy=policy.get("timing_freshness", {}),
                profile=args.profile,
            ),
            validators.validate_semantics(instance, policy["semantics"], severity_map),
            validators.validate_lineage(
                instance,
                policy.get("lineage", {}),
                state=state,
                profile=args.profile,
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
                    print(f"WARN {violation['code']} event_id={event_id}"
                          + _detail(violation))
                else:
                    failed += 1
                    failed_local = True
                    print(f"FAIL {violation['code']} event_id={event_id}"
                          + _detail(violation))
        if failed_local:
            continue
        state.record(instance)
        if warned_local:
            continue

        passed += 1

    if total == 0:
        failed += 1
        print(f"FAIL EMPTY_INPUT file={args.file} contains no events - an empty file proves nothing")

    if args.strict and warnings:
        failed += warnings
        warnings = 0

    print(f"total={total} passed={passed} failed={failed} warnings={warnings}")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
