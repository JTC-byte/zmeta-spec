import argparse
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATORS_PATH = ROOT / "gateway" / "src" / "validators.py"
spec = importlib.util.spec_from_file_location("zmeta_validators", VALIDATORS_PATH)
validators = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validators)


def parse_args():
    parser = argparse.ArgumentParser(description="Validate conformance pack.")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures.")
    parser.add_argument(
        "--profile-projection",
        action="store_true",
        help="Also run profile projection preservation fixtures.",
    )
    parser.add_argument(
        "--extension-registry",
        action="store_true",
        help="Also validate the extension registry.",
    )
    parser.add_argument(
        "--conformance-classes",
        action="store_true",
        help="Also validate the conformance class manifest and example claims.",
    )
    parser.add_argument(
        "--pass-file",
        default=str(ROOT / "conformance" / "must-pass.jsonl"),
        help="Path to must-pass JSONL",
    )
    parser.add_argument(
        "--fail-file",
        default=str(ROOT / "conformance" / "must-fail.jsonl"),
        help="Path to must-fail JSONL",
    )
    return parser.parse_args()


def _iter_jsonl(path):
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    for line_no, line in enumerate(lines, start=1):
        line = line.strip()
        if not line:
            continue
        yield line_no, json.loads(line)


def _run_checks(event, profile, policy, validator, strict, state=None):
    severity_map = policy.get("violation_severities", {})
    checks = []
    ok, violations = validators.validate_schema(event, validator, severity_map)
    if violations:
        checks.extend(violations)
        return checks

    checks.extend(
        validators.validate_role(event, {"roles": policy["roles"], "deny": policy["deny"]}, severity_map)[1]
    )
    checks.extend(validators.validate_profile(event, profile, policy["profiles"], severity_map)[1])
    checks.extend(
        validators.validate_timing_quality(
            event,
            policy["semantics"],
            state=state,
            severity_map=severity_map,
            timing_freshness_policy=policy.get("timing_freshness", {}),
            profile=profile,
        )[1]
    )
    checks.extend(validators.validate_semantics(event, policy["semantics"], severity_map)[1])
    checks.extend(
        validators.validate_lineage(
            event,
            policy.get("lineage", {}),
            state=state,
            profile=profile,
            severity_map=severity_map,
        )[1]
    )
    checks.extend(
        validators.validate_producer_authority(
            event, policy.get("producer_authority", {}), severity_map
        )[1]
    )
    checks.extend(validators.validate_routing(event, policy["routing"], severity_map)[1])
    checks.extend(validators.validate_deduplication(event, state=state, severity_map=severity_map)[1])
    if strict:
        for violation in checks:
            if violation.get("severity") == "warn":
                violation["severity"] = "fail"
    return checks


def main():
    args = parse_args()
    schema_path = ROOT / "schema" / "zmeta-event.schema.json"
    policy_dir = ROOT / "policy"
    validator = validators.load_schema(schema_path)
    policy = validators.load_policy(policy_dir)

    failures = 0

    pass_state = validators.ValidationState()
    for line_no, item in _iter_jsonl(args.pass_file):
        profile = item.get("profile", "H")
        event = item.get("event")
        if not event:
            failures += 1
            print(f"FAIL pass line={line_no} missing event")
            continue
        violations = _run_checks(event, profile, policy, validator, args.strict, state=pass_state)
        if not args.strict:
            violations = [violation for violation in violations if violation.get("severity") != "warn"]
        if violations:
            failures += 1
            print(f"FAIL pass line={line_no} profile={profile} code={violations[0]['code']}")
        else:
            pass_state.record(event)

    for line_no, item in _iter_jsonl(args.fail_file):
        profile = item.get("profile", "H")
        event = item.get("event")
        expected = item.get("expect_code")
        if not event or not expected:
            failures += 1
            print(f"FAIL fail line={line_no} missing event/expect_code")
            continue
        state = validators.ValidationState()
        for seed in item.get("preload", []):
            if isinstance(seed, dict):
                state.record(seed)
        violations = _run_checks(event, profile, policy, validator, args.strict, state=state)
        codes = [violation.get("code") for violation in violations]
        if expected not in codes:
            failures += 1
            code_str = ",".join(code for code in codes if code) or "none"
            print(
                f"FAIL fail line={line_no} profile={profile} expected={expected} got={code_str}"
            )

    if failures:
        raise SystemExit(1)

    if args.profile_projection:
        projection_path = ROOT / "tools" / "validate_projection.py"
        projection_spec = importlib.util.spec_from_file_location(
            "zmeta_validate_projection", projection_path
        )
        projection = importlib.util.module_from_spec(projection_spec)
        projection_spec.loader.exec_module(projection)
        result = projection.run_suite(
            catalog_path=ROOT / "conformance" / "profile_projection_field_catalog.yaml",
            must_pass_path=ROOT / "conformance" / "profile-projection" / "must-pass.jsonl",
            must_fail_path=ROOT / "conformance" / "profile-projection" / "must-fail.jsonl",
            quiet=True,
        )
        if result:
            raise SystemExit(result)

    if args.extension_registry:
        registry_path = ROOT / "tools" / "validate_extension_registry.py"
        registry_spec = importlib.util.spec_from_file_location(
            "zmeta_validate_extension_registry", registry_path
        )
        registry_validator = importlib.util.module_from_spec(registry_spec)
        registry_spec.loader.exec_module(registry_validator)
        result = registry_validator.run(
            ROOT / "spec" / "extension-registry.yaml",
            schema_v1_path=ROOT / "schema" / "zmeta-event-1.0.schema.json",
            schema_v1_1_path=ROOT / "schema" / "zmeta-event-1.1.0.schema.json",
        )
        if result:
            raise SystemExit(result)

    if args.conformance_classes:
        classes_path = ROOT / "tools" / "validate_conformance_classes.py"
        classes_spec = importlib.util.spec_from_file_location(
            "zmeta_validate_conformance_classes", classes_path
        )
        classes_validator = importlib.util.module_from_spec(classes_spec)
        classes_spec.loader.exec_module(classes_validator)
        result = classes_validator.run(
            ROOT / "conformance" / "conformance_classes.yaml",
            claims=[
                str(ROOT / "conformance" / "claims" / "example-reference-gateway.yaml"),
                str(ROOT / "conformance" / "claims" / "example-core-producer.yaml"),
            ],
            extension_registry_path=ROOT / "spec" / "extension-registry.yaml",
        )
        if result:
            raise SystemExit(result)

    print("conformance ok")


if __name__ == "__main__":
    main()
