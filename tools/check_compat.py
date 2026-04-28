import argparse
import importlib.util
import json
import re
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATORS_PATH = ROOT / "gateway" / "src" / "validators.py"
spec = importlib.util.spec_from_file_location("zmeta_validators", VALIDATORS_PATH)
validators = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validators)

TARGETS = ("v1.1.1", "v1.1.2", "v1.1.3")

TIMESTAMP_KEYS = {
    "ts",
    "t_publish",
    "t_receive",
    "t_start",
    "t_end",
    "last_sync_ts",
    "last_seen_ts",
    "valid_from_ts",
    "capture_ts",
}

UTC_Z_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")

SUBTYPES_V1_0 = {
    "OBSERVATION_EVENT": {"RF", "EO", "IR", "ACOUSTIC", "NETWORK"},
    "INFERENCE_EVENT": {"CLASSIFICATION", "ASSOCIATION", "ANOMALY", "BEHAVIOR"},
    "FUSION_EVENT": {"TRACK_FUSION"},
    "STATE_EVENT": {"TRACK_STATE"},
    "COMMAND_EVENT": {"GOTO", "ORBIT", "HOLD", "SEARCH_BOX"},
    "SYSTEM_EVENT": {"LINK_STATUS", "TIME_STATUS", "SCHEMA_VIOLATION", "TASK_ACK"},
}

SUBTYPES_V1_1 = {
    **SUBTYPES_V1_0,
    "COMMAND_EVENT": SUBTYPES_V1_0["COMMAND_EVENT"]
    | {
        "RETURN_TO_BASE",
        "LAND",
        "LOITER",
        "SCAN_RF",
        "TRACK_TARGET",
        "CHANGE_SENSOR_MODE",
    },
    "SYSTEM_EVENT": SUBTYPES_V1_0["SYSTEM_EVENT"] | {"SENSOR_STATUS", "PLATFORM_STATUS"},
}

DISCRIMINATOR_BY_EVENT_TYPE = {
    "OBSERVATION_EVENT": ("modality", None),
    "INFERENCE_EVENT": ("inference_type", None),
    "COMMAND_EVENT": ("task_type", None),
    "SYSTEM_EVENT": ("system_type", None),
    "FUSION_EVENT": (None, "TRACK_FUSION"),
    "STATE_EVENT": (None, "TRACK_STATE"),
}

TIMING_REQUIRED_EVENT_TYPES = {
    "OBSERVATION_EVENT",
    "INFERENCE_EVENT",
    "FUSION_EVENT",
    "STATE_EVENT",
    "COMMAND_EVENT",
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Report migration-oriented ZMeta compatibility issues."
    )
    parser.add_argument("file", help="ZMeta JSON or JSONL file to check.")
    parser.add_argument(
        "--target",
        default="v1.1.3",
        choices=TARGETS,
        help="Release target to check against. v1.1.x keeps zmeta_version 1.0 and 1.1.0.",
    )
    parser.add_argument(
        "--profile",
        default="auto",
        choices=["auto", "L", "M", "H"],
        help="Export profile to check. auto uses event.profile when present, otherwise H.",
    )
    parser.add_argument(
        "--schema",
        default=str(ROOT / "schema" / "zmeta-event.schema.json"),
        help="Schema path. Defaults to the canonical version-discriminated schema.",
    )
    parser.add_argument(
        "--policy-dir",
        default=str(ROOT / "policy"),
        help="Policy directory used for producer authority, timing, routing, and profile checks.",
    )
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    return parser.parse_args()


def add_issue(issues, category, severity, line, event_id, path, message, details=None):
    issues.append(
        {
            "category": category,
            "severity": severity,
            "line": line,
            "event_id": event_id or "UNKNOWN",
            "path": path,
            "message": message,
            "details": details or {},
        }
    )


def iter_items(path):
    path = Path(path)
    if path.suffix.lower() == ".jsonl":
        with open(path, "r", encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, start=1):
                line = line.strip()
                if line:
                    yield line_no, line
        return

    with open(path, "r", encoding="utf-8") as handle:
        raw = handle.read()
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        yield 1, raw
        return
    if isinstance(value, list):
        for index, item in enumerate(value, start=1):
            yield index, json.dumps(item, separators=(",", ":"))
    else:
        yield 1, json.dumps(value, separators=(",", ":"))


def event_id(instance):
    if not isinstance(instance, dict):
        return "UNKNOWN"
    event = instance.get("event")
    if not isinstance(event, dict):
        return "UNKNOWN"
    return event.get("event_id") or "UNKNOWN"


def json_path(parts):
    if not parts:
        return "$"
    out = "$"
    for part in parts:
        if isinstance(part, int) or str(part).isdigit():
            out += f"[{part}]"
        else:
            out += f".{part}"
    return out


def walk_timestamps(value, parts=None):
    parts = parts or []
    if isinstance(value, dict):
        for key, item in value.items():
            child_parts = parts + [key]
            if isinstance(item, str) and _looks_like_timestamp_key(key):
                yield child_parts, item
            yield from walk_timestamps(item, child_parts)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from walk_timestamps(item, parts + [index])


def _looks_like_timestamp_key(key):
    key = str(key)
    return key in TIMESTAMP_KEYS or key.endswith("_ts")


def normalize_utc_z(value):
    if not isinstance(value, str):
        return None
    text = value.strip()
    if text.endswith("Z") and UTC_Z_RE.match(text):
        return text
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    parsed = parsed.astimezone(timezone.utc)
    if parsed.microsecond:
        formatted = parsed.isoformat(timespec="microseconds")
    else:
        formatted = parsed.isoformat(timespec="seconds")
    return formatted.replace("+00:00", "Z")


def check_timestamp_format(instance, line, issues):
    eid = event_id(instance)
    for parts, value in walk_timestamps(instance):
        if UTC_Z_RE.match(value):
            continue
        suggestion = normalize_utc_z(value)
        details = {"value": value}
        if suggestion:
            details["suggestion"] = suggestion
        add_issue(
            issues,
            "timestamp_format",
            "fail",
            line,
            eid,
            json_path(parts),
            "timestamp must be serialized as UTC with a trailing Z",
            details,
        )


def allowed_subtypes(version):
    return SUBTYPES_V1_1 if version == "1.1.0" else SUBTYPES_V1_0


def check_subtype_vocabulary(instance, line, issues):
    if not isinstance(instance, dict):
        return
    event = instance.get("event", {})
    payload = instance.get("payload", {})
    if not isinstance(event, dict):
        return
    if not isinstance(payload, dict):
        payload = {}

    eid = event_id(instance)
    version = instance.get("zmeta_version", "1.0")
    event_type = event.get("event_type")
    subtype = event.get("event_subtype")
    allowed_for_version = allowed_subtypes(version)
    allowed = allowed_for_version.get(event_type)
    allowed_under_v11 = SUBTYPES_V1_1.get(event_type, set())

    if allowed is not None and subtype not in allowed:
        if subtype in allowed_under_v11 and version != "1.1.0":
            add_issue(
                issues,
                "version_vocabulary",
                "fail",
                line,
                eid,
                "$.zmeta_version",
                f"{subtype} requires zmeta_version 1.1.0",
                {"event_type": event_type, "event_subtype": subtype, "zmeta_version": version},
            )
        else:
            add_issue(
                issues,
                "subtype_vocabulary",
                "fail",
                line,
                eid,
                "$.event.event_subtype",
                "event_subtype is not in the locked vocabulary for this event_type/version",
                {
                    "event_type": event_type,
                    "event_subtype": subtype,
                    "zmeta_version": version,
                    "allowed": sorted(allowed),
                },
            )

    discriminator_key, fixed_value = DISCRIMINATOR_BY_EVENT_TYPE.get(event_type, (None, None))
    if fixed_value is not None and subtype != fixed_value:
        add_issue(
            issues,
            "subtype_payload",
            "fail",
            line,
            eid,
            "$.event.event_subtype",
            "event_subtype does not match the required semantic discriminator",
            {"expected": fixed_value, "actual": subtype},
        )
    elif discriminator_key:
        payload_value = payload.get(discriminator_key)
        if payload_value is not None and subtype != payload_value:
            add_issue(
                issues,
                "subtype_payload",
                "fail",
                line,
                eid,
                f"$.payload.{discriminator_key}",
                "event_subtype does not match the payload discriminator",
                {"event_subtype": subtype, discriminator_key: payload_value},
            )


def _timing_quality(instance):
    payload = instance.get("payload", {}) if isinstance(instance, dict) else {}
    if not isinstance(payload, dict):
        return None, None
    candidates = [
        ("$.payload.timing_quality", payload.get("timing_quality")),
        (
            "$.payload.quality.timing_quality",
            payload.get("quality", {}).get("timing_quality")
            if isinstance(payload.get("quality"), dict)
            else None,
        ),
        ("$.payload.quality", payload.get("quality")),
    ]
    for path, value in candidates:
        if isinstance(value, dict):
            required = {"time_source", "sync_state", "est_error_ms", "last_sync_ts"}
            if required.issubset(value):
                return path, value
    return None, None


def check_timing_quality(instance, line, issues, policy, state, profile):
    if not isinstance(instance, dict):
        return
    event_type = instance.get("event", {}).get("event_type")
    if event_type in TIMING_REQUIRED_EVENT_TYPES:
        path, timing = _timing_quality(instance)
        if isinstance(timing, dict):
            if (
                timing.get("time_source") == "UNKNOWN"
                and timing.get("sync_state") == "UNSYNCED"
            ):
                add_issue(
                    issues,
                    "timing_quality_fallback",
                    "warn",
                    line,
                    event_id(instance),
                    path,
                    "timing quality is explicit but degraded; treat UNKNOWN/UNSYNCED as fallback, not good timing",
                    {
                        "time_source": timing.get("time_source"),
                        "sync_state": timing.get("sync_state"),
                        "est_error_ms": timing.get("est_error_ms"),
                    },
                )

    ok, violations = validators.validate_timing_quality(
        instance,
        policy["semantics"],
        state=state,
        severity_map=policy.get("violation_severities", {}),
        timing_freshness_policy=policy.get("timing_freshness", {}),
        profile=profile,
    )
    _add_policy_violations(
        violations,
        "timing_quality",
        line,
        event_id(instance),
        issues,
    )
    return ok


def check_cot_projection(instance, line, issues):
    if not isinstance(instance, dict):
        return
    event = instance.get("event", {})
    payload = instance.get("payload", {})
    if not isinstance(event, dict) or not isinstance(payload, dict):
        return
    if event.get("event_type") != "STATE_EVENT":
        return
    if not payload.get("track_id"):
        add_issue(
            issues,
            "cot_projection",
            "warn",
            line,
            event_id(instance),
            "$.payload.track_id",
            "CoT projection will skip STATE_EVENT without payload.track_id",
        )
    geo = payload.get("geo")
    if not isinstance(geo, dict) or not {"lat", "lon", "alt_m"}.issubset(geo):
        add_issue(
            issues,
            "cot_projection",
            "warn",
            line,
            event_id(instance),
            "$.payload.geo",
            "CoT projection will skip STATE_EVENT without payload.geo lat/lon/alt_m",
        )


def _add_policy_violations(violations, category, line, eid, issues):
    for violation in violations:
        severity = "warn" if violation.get("severity") == "warn" else "fail"
        add_issue(
            issues,
            category,
            severity,
            line,
            eid,
            "$",
            f"{violation.get('code')}: {violation.get('message')}",
            violation.get("details") or {},
        )


def check_policy(instance, line, issues, policy, state, profile):
    severity_map = policy.get("violation_severities", {})
    checks = [
        (
            "role_policy",
            validators.validate_role(
                instance, {"roles": policy["roles"], "deny": policy["deny"]}, severity_map
            ),
        ),
        (
            "profile",
            validators.validate_profile(instance, profile, policy["profiles"], severity_map),
        ),
        (
            "producer_authority",
            validators.validate_producer_authority(
                instance, policy.get("producer_authority", {}), severity_map
            ),
        ),
        (
            "routing",
            validators.validate_routing(instance, policy["routing"], severity_map),
        ),
        (
            "semantic_policy",
            validators.validate_semantics(instance, policy["semantics"], severity_map),
        ),
        (
            "lineage",
            validators.validate_lineage(
                instance,
                policy.get("lineage", {}),
                state=state,
                profile=profile,
                severity_map=severity_map,
            ),
        ),
    ]
    eid = event_id(instance)
    for category, (_ok, violations) in checks:
        _add_policy_violations(violations, category, line, eid, issues)


def check_schema(instance, line, issues, schema, policy):
    _ok, violations = validators.validate_schema(
        instance, schema, policy.get("violation_severities", {})
    )
    for violation in violations:
        schema_path = violation.get("details", {}).get("path")
        add_issue(
            issues,
            "schema",
            "fail",
            line,
            event_id(instance),
            _schema_json_path(schema_path),
            violation.get("message") or "schema validation failed",
            violation.get("details") or {},
        )


def _schema_json_path(path):
    if not path:
        return "$"
    return "$." + str(path).replace("/", ".")


def profile_for_event(args_profile, instance):
    if args_profile != "auto":
        return args_profile
    if isinstance(instance, dict) and instance.get("profile") in {"L", "M", "H"}:
        return instance["profile"]
    return "H"


def print_text(path, issues, strict):
    counts = {}
    for issue in issues:
        counts[issue["category"]] = counts.get(issue["category"], 0) + 1
        details = ""
        if issue.get("details"):
            suggestion = issue["details"].get("suggestion")
            if suggestion:
                details = f" suggestion={suggestion}"
        print(
            f"{issue['severity'].upper()} {issue['category']} "
            f"line={issue['line']} event_id={issue['event_id']} path={issue['path']} "
            f"message={issue['message']}{details}"
        )

    failed = sum(1 for issue in issues if issue["severity"] == "fail")
    warnings = sum(1 for issue in issues if issue["severity"] == "warn")
    effective_failed = failed + warnings if strict else failed
    category_text = " ".join(f"{key}={counts[key]}" for key in sorted(counts))
    print(
        f"summary file={path} issues={len(issues)} failed={effective_failed} "
        f"warnings={0 if strict else warnings} {category_text}".rstrip()
    )


def main():
    args = parse_args()
    schema = validators.load_schema(args.schema)
    policy = validators.load_policy(args.policy_dir)
    state = validators.ValidationState()
    issues = []
    parsed_events = 0

    for line, raw in iter_items(args.file):
        try:
            instance = json.loads(raw)
        except json.JSONDecodeError as exc:
            add_issue(
                issues,
                "parse",
                "fail",
                line,
                "UNKNOWN",
                "$",
                f"invalid JSON: {exc}",
            )
            continue
        if not isinstance(instance, dict):
            add_issue(issues, "parse", "fail", line, "UNKNOWN", "$", "event must be a JSON object")
            continue

        parsed_events += 1
        profile = profile_for_event(args.profile, instance)
        check_timestamp_format(instance, line, issues)
        check_subtype_vocabulary(instance, line, issues)
        check_timing_quality(instance, line, issues, policy, state, profile)
        check_cot_projection(instance, line, issues)
        check_policy(instance, line, issues, policy, state, profile)
        check_schema(instance, line, issues, schema, policy)
        state.record(instance)

    failed = sum(1 for issue in issues if issue["severity"] == "fail")
    warnings = sum(1 for issue in issues if issue["severity"] == "warn")
    exit_failed = failed or (args.strict and warnings)

    if args.json:
        print(
            json.dumps(
                {
                    "target": args.target,
                    "file": str(args.file),
                    "events": parsed_events,
                    "failed": failed + warnings if args.strict else failed,
                    "warnings": 0 if args.strict else warnings,
                    "issues": issues,
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print_text(args.file, issues, args.strict)

    if exit_failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
