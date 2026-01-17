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


def event_id_from_instance(instance):
    if isinstance(instance, dict):
        return instance.get("event", {}).get("event_id", "UNKNOWN")
    return "UNKNOWN"


def main():
    args = parse_args()
    schema_path = ROOT / "schema" / "zmeta-event-1.0.schema.json"
    policy_dir = ROOT / "policy"

    validator = validators.load_schema(schema_path)
    policy = validators.load_policy(policy_dir)
    severity_map = policy.get("violation_severities", {})

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
            return
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

        ok, violations = validators.validate_schema(instance, validator, severity_map)
        if violations:
            failed += 1
            event_id = event_id_from_instance(instance)
            print(f"FAIL {violations[0]['code']} event_id={event_id}")
            continue

        checks = [
            validators.validate_role(instance, {"roles": policy["roles"], "deny": policy["deny"]}, severity_map),
            validators.validate_profile(instance, args.profile, policy["profiles"], severity_map),
            validators.validate_semantics(instance, policy["semantics"], severity_map),
            validators.validate_routing(instance, policy["routing"], severity_map),
        ]

        event_id = event_id_from_instance(instance)
        failed_local = False
        warned_local = False
        for _ok, violations in checks:
            for violation in violations:
                if violation.get("severity") == "warn":
                    warnings += 1
                    warned_local = True
                    print(f"WARN {violation['code']} event_id={event_id}")
                else:
                    failed += 1
                    failed_local = True
                    print(f"FAIL {violation['code']} event_id={event_id}")
        if failed_local or warned_local:
            continue

        passed += 1

    if args.strict and warnings:
        failed += warnings
        warnings = 0

    print(f"total={total} passed={passed} failed={failed} warnings={warnings}")


if __name__ == "__main__":
    main()
