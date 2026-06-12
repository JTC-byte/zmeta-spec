from __future__ import annotations

import argparse
import importlib.util
import json
import re
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

UTC_Z_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")
MISSING = object()
EXPECTED_VALUE_TOLERANCE = 1e-6


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate ZMeta adapter conformance fixtures.")
    parser.add_argument(
        "--fixtures",
        default=str(ROOT / "conformance" / "adapter-harness" / "must-pass.jsonl"),
        help="Adapter fixture JSONL file.",
    )
    parser.add_argument("--quiet", action="store_true", help="Only print failures and final summary.")
    return parser.parse_args()


def iter_jsonl(path: Path | str):
    fixture_path = Path(path)
    if not fixture_path.exists():
        raise FileNotFoundError(f"adapter fixture file not found: {fixture_path}")
    for line_no, line in enumerate(fixture_path.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        yield line_no, json.loads(line)


def _issue(code: str, message: str, *, path: str | None = None, details: dict[str, Any] | None = None):
    item: dict[str, Any] = {"code": code, "message": message}
    if path:
        item["path"] = path
    if details:
        item["details"] = details
    return item


def _get_path(value: Any, path: str) -> Any:
    target = value
    for part in path.split("."):
        if isinstance(target, dict) and part in target:
            target = target[part]
        else:
            return MISSING
    return target


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _load_module(module_path: str):
    path = ROOT / module_path.replace("\\", "/")
    if not path.is_file():
        raise FileNotFoundError(f"adapter module not found: {module_path}")
    name = "zmeta_adapter_" + re.sub(r"[^a-zA-Z0-9_]", "_", module_path)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _call_fixture(fixture: dict[str, Any]) -> Any:
    module = _load_module(str(fixture["module"]))
    func = getattr(module, str(fixture["callable"]))
    args = fixture.get("args", [])
    kwargs = fixture.get("kwargs", {})
    if not isinstance(args, list):
        raise ValueError("fixture args must be a list")
    if not isinstance(kwargs, dict):
        raise ValueError("fixture kwargs must be a mapping")
    return func(*args, **kwargs)


def _events_from_result(fixture: dict[str, Any], result: Any) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    result_kind = fixture.get("result", "event")
    if result_kind == "event":
        if isinstance(result, dict):
            return [result], []
        return [], [_issue("ADAPTER_RESULT_INVALID", "adapter did not return an event mapping")]
    if result_kind == "events":
        if isinstance(result, list) and all(isinstance(item, dict) for item in result):
            return list(result), []
        return [], [_issue("ADAPTER_RESULT_INVALID", "adapter did not return a list of event mappings")]
    return [], [_issue("ADAPTER_FIXTURE_INVALID", f"unsupported result kind: {result_kind}")]


def _run_policy_checks(
    event: dict[str, Any],
    profile: str,
    policy: dict[str, Any],
    schema_validator: Any,
) -> list[dict[str, Any]]:
    severity_map = policy.get("violation_severities", {})
    ok, violations = validators.validate_schema(event, schema_validator, severity_map)
    if violations:
        return [_issue("ADAPTER_SCHEMA_INVALID", item.get("message", "schema invalid"), details=item) for item in violations]

    state = validators.ValidationState()
    checks = [
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
    ]
    issues: list[dict[str, Any]] = []
    for _ok, violations in checks:
        for violation in violations:
            if violation.get("severity") != "warn":
                issues.append(
                    _issue(
                        "ADAPTER_POLICY_INVALID",
                        f"adapter output failed policy validation: {violation.get('code')}",
                        details=violation,
                    )
                )
    return issues


def _event_type(event: dict[str, Any]) -> str:
    block = event.get("event", {})
    return str(block.get("event_type")) if isinstance(block, dict) and block.get("event_type") else ""


def _event_subtype(event: dict[str, Any]) -> str:
    block = event.get("event", {})
    return str(block.get("event_subtype")) if isinstance(block, dict) and block.get("event_subtype") else ""


def _layer_issues(event: dict[str, Any], expect: dict[str, Any]) -> list[dict[str, Any]]:
    event_type = _event_type(event)
    payload = event.get("payload", {}) if isinstance(event.get("payload"), dict) else {}
    issues: list[dict[str, Any]] = []

    if event_type == "OBSERVATION_EVENT":
        if "confidence" in event:
            issues.append(_issue("ADAPTER_LAYER_COLLAPSE", "observation output carries top-level confidence"))
        for path in ("payload.track_id", "payload.classification", "payload.label", "payload.class_name"):
            if _get_path(event, path) is not MISSING:
                issues.append(_issue("ADAPTER_LAYER_COLLAPSE", f"observation output carries {path}", path=path))
    elif event_type == "INFERENCE_EVENT":
        if "confidence" not in event:
            issues.append(_issue("ADAPTER_LAYER_COLLAPSE", "inference output missing confidence"))
        if _get_path(event, "payload.track_id") is not MISSING:
            issues.append(_issue("ADAPTER_LAYER_COLLAPSE", "inference output carries track_id", path="payload.track_id"))
    elif event_type == "STATE_EVENT":
        for path in ("payload.features", "payload.raw_features", "payload.modality", "payload.data_ref", "payload.data_refs"):
            if _get_path(event, path) is not MISSING:
                issues.append(_issue("ADAPTER_LAYER_COLLAPSE", f"state output carries raw/evidence field {path}", path=path))
        if expect.get("requires_external_promotion"):
            promotion = _get_path(event, "payload.extensions.external_promotion")
            if not isinstance(promotion, dict):
                issues.append(_issue("ADAPTER_PROMOTION_MISSING", "state output missing external promotion evidence"))
            else:
                for key in expect.get("external_promotion_required_keys", []):
                    if key not in promotion:
                        issues.append(_issue("ADAPTER_PROMOTION_MISSING", f"external promotion missing {key}", path=f"payload.extensions.external_promotion.{key}"))

    if event_type != "SYSTEM_EVENT" and expect.get("require_lineage_transform", True):
        transform = _get_path(event, "lineage.transform")
        if not isinstance(transform, str) or not transform:
            issues.append(_issue("ADAPTER_LINEAGE_MISSING", "adapter output missing lineage.transform", path="lineage.transform"))

    timing = _get_path(event, "payload.timing_quality")
    if isinstance(timing, dict) and timing.get("sync_state") == "UNSYNCED" and not expect.get("allow_degraded_timing", False):
        issues.append(_issue("ADAPTER_UNDECLARED_DEGRADED_TIMING", "UNSYNCED fallback timing must be declared by fixture", path="payload.timing_quality.sync_state"))
    if isinstance(payload, dict):
        quality_timing = _get_path(event, "payload.quality.timing_quality")
        if isinstance(quality_timing, dict) and quality_timing.get("sync_state") == "UNSYNCED" and not expect.get("allow_degraded_timing", False):
            issues.append(_issue("ADAPTER_UNDECLARED_DEGRADED_TIMING", "UNSYNCED fallback timing must be declared by fixture", path="payload.quality.timing_quality.sync_state"))

    return issues


def _expectation_issues(event: dict[str, Any], expect: dict[str, Any]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    expected_type = expect.get("event_type")
    if expected_type and _event_type(event) != expected_type:
        issues.append(_issue("ADAPTER_EXPECTATION_MISMATCH", f"expected event_type {expected_type}, got {_event_type(event)}", path="event.event_type"))
    expected_subtype = expect.get("event_subtype")
    if expected_subtype and _event_subtype(event) != expected_subtype:
        issues.append(_issue("ADAPTER_EXPECTATION_MISMATCH", f"expected event_subtype {expected_subtype}, got {_event_subtype(event)}", path="event.event_subtype"))

    for path in expect.get("required_paths", []):
        if _get_path(event, path) is MISSING:
            issues.append(_issue("ADAPTER_REQUIRED_PATH_MISSING", f"missing required path {path}", path=path))
    for path in expect.get("forbidden_paths", []):
        if _get_path(event, path) is not MISSING:
            issues.append(_issue("ADAPTER_FORBIDDEN_PATH_PRESENT", f"forbidden path present {path}", path=path))

    for path, expected in expect.get("expected_values", {}).items():
        value = _get_path(event, path)
        if value is MISSING:
            issues.append(_issue("ADAPTER_EXPECTED_VALUE_MISSING", f"expected value path missing {path}", path=path))
        elif isinstance(expected, bool) != isinstance(value, bool):
            issues.append(_issue("ADAPTER_EXPECTED_VALUE_MISMATCH", f"expected {path} == {expected!r}, got {value!r}", path=path, details={"expected": expected, "actual": value}))
        elif _is_number(expected) and _is_number(value):
            if abs(float(value) - float(expected)) > EXPECTED_VALUE_TOLERANCE:
                issues.append(_issue("ADAPTER_EXPECTED_VALUE_MISMATCH", f"expected {path} ~= {expected}, got {value}", path=path, details={"expected": expected, "actual": value}))
        elif value != expected:
            issues.append(_issue("ADAPTER_EXPECTED_VALUE_MISMATCH", f"expected {path} == {expected!r}, got {value!r}", path=path, details={"expected": expected, "actual": value}))

    for path in expect.get("utc_z_paths", ["event.ts"]):
        value = _get_path(event, path)
        if not isinstance(value, str) or UTC_Z_RE.match(value) is None:
            issues.append(_issue("ADAPTER_TIME_NOT_UTC_Z", f"{path} is not UTC-Z", path=path, details={"value": value}))

    prefix = expect.get("lineage_transform_prefix")
    if prefix:
        transform = _get_path(event, "lineage.transform")
        if not isinstance(transform, str) or not transform.startswith(str(prefix)):
            issues.append(_issue("ADAPTER_LINEAGE_MISMATCH", f"lineage.transform must start with {prefix}", path="lineage.transform"))

    producer = expect.get("source_producer")
    if producer and _get_path(event, "source.producer") != producer:
        issues.append(_issue("ADAPTER_EXPECTATION_MISMATCH", f"expected source.producer {producer}", path="source.producer"))
    return issues


def evaluate_fixture(
    fixture: dict[str, Any],
    schema_validator: Any,
    policy: dict[str, Any],
) -> list[dict[str, Any]]:
    try:
        result = _call_fixture(fixture)
    except Exception as exc:
        return [_issue("ADAPTER_CALL_FAILED", f"adapter call failed: {exc}")]

    events, issues = _events_from_result(fixture, result)
    if issues:
        return issues

    expect = fixture.get("expect", {})
    if not isinstance(expect, dict):
        return [_issue("ADAPTER_FIXTURE_INVALID", "expect must be a mapping")]

    profile = str(fixture.get("profile") or "H")
    all_issues: list[dict[str, Any]] = []
    for index, event in enumerate(events):
        indexed_expect = expect
        if isinstance(expect.get("events"), list):
            indexed_expect = expect["events"][index] if index < len(expect["events"]) else {}
        all_issues.extend(_run_policy_checks(event, profile, policy, schema_validator))
        all_issues.extend(_layer_issues(event, indexed_expect))
        all_issues.extend(_expectation_issues(event, indexed_expect))
    return all_issues


def run(*, fixtures_path: Path | str | None = None, quiet: bool = False) -> int:
    path = Path(fixtures_path) if fixtures_path else ROOT / "conformance" / "adapter-harness" / "must-pass.jsonl"
    schema_validator = validators.load_schema(ROOT / "schema" / "zmeta-event.schema.json")
    policy = validators.load_policy(ROOT / "policy")

    failures = 0
    passed = 0
    for line_no, fixture in iter_jsonl(path):
        label = str(fixture.get("name") or f"line-{line_no}")
        issues = evaluate_fixture(fixture, schema_validator, policy)
        if issues:
            failures += 1
            first = issues[0]
            location = f" path={first['path']}" if "path" in first else ""
            print(f"FAIL name={label} code={first['code']}{location}: {first['message']}")
        else:
            passed += 1
            if not quiet:
                print(f"PASS name={label}")

    if failures:
        print(f"adapter conformance failed total={passed} failures={failures}")
        return 1
    print(f"adapter conformance ok total={passed}")
    return 0


def main() -> None:
    args = parse_args()
    raise SystemExit(run(fixtures_path=args.fixtures, quiet=args.quiet))


if __name__ == "__main__":
    main()
