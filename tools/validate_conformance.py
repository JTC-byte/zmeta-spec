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
    parser.add_argument(
        "--kernel-gate",
        action="store_true",
        help="Run the full kernel protection gate: --strict plus every "
        "sub-check flag below. This is the single named form of the gate, "
        "so the battery definition is one stable token instead of a "
        "hand-copied flag string; a new sub-check joins the gate here, in "
        "one place, rather than in every document that quotes the command "
        "(apparatus audit, 2026-08-10).",
    )
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
        "--encoding-negative",
        action="store_true",
        help="Also run compact/protobuf invalid-after-decode fixtures.",
    )
    parser.add_argument(
        "--precision-policy",
        action="store_true",
        help="Also run profile precision/quantization policy fixtures.",
    )
    parser.add_argument(
        "--release-manifest",
        action="store_true",
        help="Also validate the structured release manifest.",
    )
    parser.add_argument(
        "--release-package",
        action="store_true",
        help="Also validate formal release package templates.",
    )
    parser.add_argument(
        "--bad-events",
        action="store_true",
        help="Also run semantic bad-event corpus fixtures.",
    )
    parser.add_argument(
        "--adapter-harness",
        action="store_true",
        help="Also run shared adapter conformance fixtures.",
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
    args = parser.parse_args()
    if args.kernel_gate:
        # KERNEL_GATE_CHECKS is the one authoritative list; the equivalence
        # test pins that expanding the alias enables exactly these flags.
        for flag in KERNEL_GATE_CHECKS:
            setattr(args, flag, True)
    return args


# The kernel protection gate, as data: --kernel-gate sets --strict plus every
# flag named here. Adding a sub-check means adding it to this tuple (and its
# implementation block below); no document needs editing.
KERNEL_GATE_CHECKS = (
    "strict",
    "profile_projection",
    "extension_registry",
    "conformance_classes",
    "encoding_negative",
    "precision_policy",
    "release_manifest",
    "release_package",
    "bad_events",
    "adapter_harness",
)


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
    pass_total = 0
    fail_total = 0

    pass_state = validators.ValidationState()
    for line_no, item in _iter_jsonl(args.pass_file):
        pass_total += 1
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

    if pass_total == 0:
        failures += 1
        print(f"FAIL pass file {args.pass_file} contains no fixtures - an empty file proves nothing")

    for line_no, item in _iter_jsonl(args.fail_file):
        fail_total += 1
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

    if fail_total == 0:
        failures += 1
        print(f"FAIL fail file {args.fail_file} contains no fixtures - an empty file proves nothing")

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

    if args.encoding_negative:
        encoding_negative_path = ROOT / "tools" / "validate_encoding_negative.py"
        encoding_negative_spec = importlib.util.spec_from_file_location(
            "zmeta_validate_encoding_negative", encoding_negative_path
        )
        encoding_negative = importlib.util.module_from_spec(encoding_negative_spec)
        encoding_negative_spec.loader.exec_module(encoding_negative)
        result = encoding_negative.run(
            compact_path=ROOT / "conformance" / "encoding-negative" / "compact-must-fail.jsonl",
            protobuf_path=ROOT / "conformance" / "encoding-negative" / "protobuf-must-fail.jsonl",
            gateway_path=ROOT / "conformance" / "encoding-negative" / "gateway-must-fail.jsonl",
            context_path=ROOT / "conformance" / "encoding-negative" / "context.jsonl",
            quiet=True,
        )
        if result:
            raise SystemExit(result)

    if args.precision_policy:
        precision_policy_path = ROOT / "tools" / "validate_precision_policy.py"
        precision_policy_spec = importlib.util.spec_from_file_location(
            "zmeta_validate_precision_policy", precision_policy_path
        )
        precision_policy = importlib.util.module_from_spec(precision_policy_spec)
        precision_policy_spec.loader.exec_module(precision_policy)
        result = precision_policy.run_suite(
            policy_path=ROOT / "policy" / "profile-precision.yaml",
            must_pass_path=ROOT / "conformance" / "profile-precision" / "must-pass.jsonl",
            must_fail_path=ROOT / "conformance" / "profile-precision" / "must-fail.jsonl",
            quiet=True,
        )
        if result:
            raise SystemExit(result)

    if args.release_manifest:
        release_manifest_path = ROOT / "tools" / "validate_release_manifest.py"
        release_manifest_spec = importlib.util.spec_from_file_location(
            "zmeta_validate_release_manifest", release_manifest_path
        )
        release_manifest = importlib.util.module_from_spec(release_manifest_spec)
        release_manifest_spec.loader.exec_module(release_manifest)
        result = release_manifest.run(
            ROOT / "release" / "zmeta-release-manifest.yaml",
            quiet=True,
        )
        if result:
            raise SystemExit(result)

    if args.release_package:
        release_package_path = ROOT / "tools" / "validate_release_package.py"
        release_package_spec = importlib.util.spec_from_file_location(
            "zmeta_validate_release_package", release_package_path
        )
        release_package = importlib.util.module_from_spec(release_package_spec)
        release_package_spec.loader.exec_module(release_package)
        result = release_package.run(
            ROOT / "release" / "zmeta-release-manifest.yaml",
            templates_only=True,
            quiet=True,
        )
        if result:
            raise SystemExit(result)

    if args.bad_events:
        bad_events_path = ROOT / "tools" / "validate_bad_events.py"
        bad_events_spec = importlib.util.spec_from_file_location(
            "zmeta_validate_bad_events", bad_events_path
        )
        bad_events = importlib.util.module_from_spec(bad_events_spec)
        bad_events_spec.loader.exec_module(bad_events)
        result = bad_events.run(
            must_fail_path=ROOT / "conformance" / "bad-events" / "must-fail.jsonl",
            quiet=True,
        )
        if result:
            raise SystemExit(result)

    if args.adapter_harness:
        adapter_harness_path = ROOT / "tools" / "validate_adapter_conformance.py"
        adapter_harness_spec = importlib.util.spec_from_file_location(
            "zmeta_validate_adapter_conformance", adapter_harness_path
        )
        adapter_harness = importlib.util.module_from_spec(adapter_harness_spec)
        adapter_harness_spec.loader.exec_module(adapter_harness)
        result = adapter_harness.run(
            fixtures_path=ROOT / "conformance" / "adapter-harness" / "must-pass.jsonl",
            quiet=True,
        )
        if result:
            raise SystemExit(result)

    print(f"conformance ok pass={pass_total} fail={fail_total}")


if __name__ == "__main__":
    main()
