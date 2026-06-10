import argparse
import copy
import importlib.util
import json
import re
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
VALIDATORS_PATH = ROOT / "gateway" / "src" / "validators.py"
spec = importlib.util.spec_from_file_location("zmeta_validators", VALIDATORS_PATH)
validators = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validators)


REQUIRED_TOP_LEVEL = {
    "registry_version",
    "generated_for_zmeta_versions",
    "authority",
    "last_updated",
    "status_values",
    "category_values",
    "projection_behavior_values",
    "entries",
}

REQUIRED_ENTRY_FIELDS = {
    "name",
    "display_name",
    "category",
    "status",
    "version_branch",
    "introduced_in",
    "owner",
    "semantic_definition",
    "rationale",
    "allowed_event_types",
    "allowed_event_subtypes",
    "payload_scope",
    "profile_scope",
    "schema_status",
    "policy_status",
    "adapter_gateway_status",
    "encoding_status",
    "conformance_status",
    "ignorable_by_default",
    "profile_projection_behavior",
    "risk_relevant",
    "must_preserve_when_used_for_policy",
    "collision_rules",
    "security_release_notes",
    "security_privacy_notes",
    "migration_notes",
    "fixture_references",
    "references",
    "date_added",
    "review_state",
    "supersedes",
    "superseded_by",
    "notes",
}

CORE_ENVELOPE_NAMES = {
    "zmeta_version",
    "event",
    "event.event_id",
    "event.event_type",
    "event.event_subtype",
    "event.ts",
    "event.t_receive",
    "event.t_publish",
    "source",
    "source.platform_id",
    "source.node_role",
    "source.producer",
    "source.sensor_id",
    "source.sw_version",
    "payload",
    "lineage",
    "lineage.based_on",
    "lineage.transform",
    "confidence",
    "profile",
}

IMPLEMENTED = {"implemented"}
SUFFICIENT = {"implemented", "not_applicable"}
VENDOR_NAME_RE = re.compile(r"^vendor\.[a-z0-9][a-z0-9_-]*(?:\.[A-Za-z0-9][A-Za-z0-9_.-]*)+$")
UNREGISTERED_RESERVED_SCHEMA_VALUES = {
    "TAKEOFF": "D-011 tracks this as a stray crosswalk mention; it is not current registry or event vocabulary.",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate the ZMeta extension registry.")
    parser.add_argument(
        "--registry",
        default=str(ROOT / "spec" / "extension-registry.yaml"),
        help="Path to extension registry YAML.",
    )
    parser.add_argument(
        "--schema-v1",
        default=str(ROOT / "schema" / "zmeta-event-1.0.schema.json"),
        help="Path to the v1.0 event schema.",
    )
    parser.add_argument(
        "--schema-v1_1",
        default=str(ROOT / "schema" / "zmeta-event-1.1.0.schema.json"),
        help="Path to the v1.1.0 event schema.",
    )
    return parser.parse_args()


def _issue(code: str, message: str, *, entry: str | None = None) -> dict[str, str]:
    out = {"code": code, "message": message}
    if entry:
        out["entry"] = entry
    return out


def load_registry(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    return data


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _schema_validator(path: Path):
    return validators.load_schema(path)


def _schema_contains_reserved_value(node: Any, value: str) -> bool:
    if isinstance(node, dict):
        enum_values = node.get("enum")
        if isinstance(enum_values, list) and value in enum_values:
            return True
        if node.get("const") == value:
            return True
        return any(_schema_contains_reserved_value(child, value) for child in node.values())
    if isinstance(node, list):
        return any(_schema_contains_reserved_value(child, value) for child in node)
    return False


def _schema_valid(event: dict[str, Any], schema_validator) -> bool:
    ok, _violations = validators.validate_schema(event, schema_validator, {})
    return ok


def _base_event(version: str, event_type: str, event_subtype: str, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "zmeta_version": version,
        "event": {
            "event_id": "01902a6b-c8d3-7def-8123-456789abcdef",
            "event_type": event_type,
            "event_subtype": event_subtype,
            "ts": "2026-01-15T18:30:00Z",
        },
        "source": {
            "platform_id": "registry-check-node",
            "node_role": "GATEWAY",
            "producer": "registry-validator",
        },
        "profile": "H",
        "payload": payload,
    }


def observation_event(name: str, version: str) -> dict[str, Any]:
    return _base_event(
        version,
        "OBSERVATION_EVENT",
        name,
        {
            "modality": name,
            "features": {
                "center_freq_hz": 2450000000,
                "bandwidth_hz": 20000000,
                "power_dbm": -35.2,
            },
            "timing_quality": {
                "time_source": "GPS_PPS",
                "sync_state": "LOCKED",
                "est_error_ms": 1,
                "last_sync_ts": "2026-01-15T18:29:59Z",
            },
        },
    )


def command_event(name: str, version: str) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "task_id": f"task-{name.lower()}",
        "task_type": name,
        "valid_for_ms": 60000,
        "requires_deconfliction": True,
    }
    if name == "LAND":
        payload["target_geo"] = {"lat": 34.0, "lon": -118.0}
    elif name == "LOITER":
        payload["geometry"] = {"pattern": "circle", "radius_m": 100.0}
    elif name == "SCAN_RF":
        payload.update(
            {
                "sensor_id": "rf-01",
                "freq_range_hz": {"min": 24000000, "max": 1766000000},
                "dwell_ms": 1000,
            }
        )
    elif name == "TRACK_TARGET":
        payload["target_track_id"] = "track-test-001"
    elif name == "CHANGE_SENSOR_MODE":
        payload.update({"sensor_id": "rf-01", "sensor_mode": "DF"})
    return _base_event(version, "COMMAND_EVENT", name, payload)


def system_event(name: str, version: str) -> dict[str, Any]:
    if name == "SENSOR_STATUS":
        state = "ACTIVE"
        metrics = {"sensor_id": "sensor-01", "modality": "RF"}
    elif name == "PLATFORM_STATUS":
        state = "NOMINAL"
        metrics = {"battery_pct": 87, "platform_type": "MULTIROTOR"}
    else:
        state = "UNKNOWN"
        metrics = {"status_id": "registry-check"}
    return _base_event(
        version,
        "SYSTEM_EVENT",
        name,
        {"system_type": name, "state": state, "metrics": metrics},
    )


def inference_event(name: str, version: str) -> dict[str, Any]:
    event = _base_event(
        version,
        "INFERENCE_EVENT",
        name,
        {
            "inference_type": name,
            "claim": {"label": "registry-check"},
            "model": {"name": "registry-model", "version": "0.0.1"},
            "based_on": ["01902a6b-c8d3-7def-8123-456789abcdea"],
        },
    )
    event["confidence"] = 0.5
    event["lineage"] = {
        "based_on": ["01902a6b-c8d3-7def-8123-456789abcdea"],
        "transform": "registry-check",
    }
    return event


def state_event_with_error_ellipse(version: str) -> dict[str, Any]:
    event = _base_event(
        version,
        "STATE_EVENT",
        "TRACK_STATE",
        {
            "track_id": "track-registry-001",
            "geo": {
                "lat": 34.0,
                "lon": -118.0,
                "alt_m": 10.0,
                "error_ellipse_m": {
                    "semi_major": 20.0,
                    "semi_minor": 10.0,
                    "orientation_deg": 45.0,
                    "probability": "CE_90",
                },
            },
            "valid_for_ms": 10000,
        },
    )
    event["confidence"] = 0.8
    event["lineage"] = {"based_on": ["01902a6b-c8d3-7def-8123-456789abcdea"]}
    return event


def profile_event(name: str, version: str) -> dict[str, Any]:
    event = _base_event(
        version,
        "STATE_EVENT",
        "TRACK_STATE",
        {
            "track_id": "track-registry-001",
            "geo": {"lat": 34.0, "lon": -118.0, "alt_m": 10.0},
            "valid_for_ms": 10000,
        },
    )
    event["profile"] = name
    event["confidence"] = 0.8
    event["lineage"] = {"based_on": ["01902a6b-c8d3-7def-8123-456789abcdea"]}
    return event


def _implemented_status(entry: dict[str, Any], key: str) -> bool:
    return str(entry.get(key, "none") or "none") in IMPLEMENTED


def _has_implementation_surface(entry: dict[str, Any]) -> bool:
    return any(
        _implemented_status(entry, key)
        for key in [
            "schema_status",
            "policy_status",
            "adapter_gateway_status",
            "encoding_status",
            "conformance_status",
        ]
    )


def _entry_context_checks(entry: dict[str, Any], schema_v1, schema_v1_1) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    name = str(entry.get("name", ""))
    status = str(entry.get("status", ""))
    category = str(entry.get("category", ""))
    allowed_event_types = set(entry.get("allowed_event_types") or [])

    if status in {"reserved", "proposed"}:
        if category == "observation_modality":
            if _schema_valid(observation_event(name, "1.0"), schema_v1) or _schema_valid(
                observation_event(name, "1.1.0"), schema_v1_1
            ):
                issues.append(
                    _issue(
                        "REGISTRY_RESERVED_SCHEMA_LEAK",
                        "reserved/proposed observation modality validates in a current schema",
                        entry=name,
                    )
                )
        if category == "command_task_type" or "COMMAND_EVENT" in allowed_event_types:
            if _schema_valid(command_event(name, "1.0"), schema_v1) or _schema_valid(
                command_event(name, "1.1.0"), schema_v1_1
            ):
                issues.append(
                    _issue(
                        "REGISTRY_RESERVED_SCHEMA_LEAK",
                        "reserved/proposed command task validates in a current schema",
                        entry=name,
                    )
                )
        if category == "system_status_type" or name.endswith("_STATUS") or "SYSTEM_EVENT" in allowed_event_types:
            if _schema_valid(system_event(name, "1.0"), schema_v1) or _schema_valid(
                system_event(name, "1.1.0"), schema_v1_1
            ):
                issues.append(
                    _issue(
                        "REGISTRY_RESERVED_SCHEMA_LEAK",
                        "reserved/proposed system status validates in a current schema",
                        entry=name,
                    )
                )
        if category == "inference_type" or "INFERENCE_EVENT" in allowed_event_types:
            if _schema_valid(inference_event(name, "1.0"), schema_v1) or _schema_valid(
                inference_event(name, "1.1.0"), schema_v1_1
            ):
                issues.append(
                    _issue(
                        "REGISTRY_RESERVED_SCHEMA_LEAK",
                        "reserved/proposed inference type validates in a current schema",
                        entry=name,
                    )
                )
        if category == "profile_export_control" and name.endswith("_PROFILE"):
            if _schema_valid(profile_event(name, "1.0"), schema_v1) or _schema_valid(
                profile_event(name, "1.1.0"), schema_v1_1
            ):
                issues.append(
                    _issue(
                        "REGISTRY_RESERVED_SCHEMA_LEAK",
                        "reserved/proposed profile label validates in a current schema",
                        entry=name,
                    )
                )

    if status == "experimental" and entry.get("version_branch") == "1.1.0":
        if category == "command_task_type":
            if _schema_valid(command_event(name, "1.0"), schema_v1):
                issues.append(
                    _issue(
                        "REGISTRY_EXPERIMENTAL_V1_LEAK",
                        "v1.1.0 experimental command task validates in v1.0",
                        entry=name,
                    )
                )
            if not _schema_valid(command_event(name, "1.1.0"), schema_v1_1):
                issues.append(
                    _issue(
                        "REGISTRY_EXPERIMENTAL_SCHEMA_MISSING",
                        "v1.1.0 experimental command task does not validate in v1.1.0",
                        entry=name,
                    )
                )
        if category == "system_status_type":
            if _schema_valid(system_event(name, "1.0"), schema_v1):
                issues.append(
                    _issue(
                        "REGISTRY_EXPERIMENTAL_V1_LEAK",
                        "v1.1.0 experimental system status validates in v1.0",
                        entry=name,
                    )
                )
            if not _schema_valid(system_event(name, "1.1.0"), schema_v1_1):
                issues.append(
                    _issue(
                        "REGISTRY_EXPERIMENTAL_SCHEMA_MISSING",
                        "v1.1.0 experimental system status does not validate in v1.1.0",
                        entry=name,
                    )
                )
        if name == "ERROR_ELLIPSE_M":
            if _schema_valid(state_event_with_error_ellipse("1.0"), schema_v1):
                issues.append(
                    _issue(
                        "REGISTRY_EXPERIMENTAL_V1_LEAK",
                        "error_ellipse_m validates in v1.0",
                        entry=name,
                    )
                )
            if not _schema_valid(state_event_with_error_ellipse("1.1.0"), schema_v1_1):
                issues.append(
                    _issue(
                        "REGISTRY_EXPERIMENTAL_SCHEMA_MISSING",
                        "error_ellipse_m does not validate in v1.1.0",
                        entry=name,
                    )
                )

    return issues


def validate_registry(
    registry_path: Path,
    schema_v1_path: Path | None = None,
    schema_v1_1_path: Path | None = None,
) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []

    if not registry_path.exists():
        return [_issue("REGISTRY_FILE_MISSING", f"registry file not found: {registry_path}")]

    try:
        registry = load_registry(registry_path)
    except Exception as exc:
        return [_issue("REGISTRY_YAML_INVALID", f"failed to load registry YAML: {exc}")]

    if not isinstance(registry, dict):
        return [_issue("REGISTRY_TOP_LEVEL_INVALID", "registry must be a YAML mapping")]

    for key in sorted(REQUIRED_TOP_LEVEL):
        if key not in registry:
            issues.append(_issue("REGISTRY_REQUIRED_TOP_LEVEL_MISSING", f"missing top-level key: {key}"))

    entries = registry.get("entries", [])
    if not isinstance(entries, list):
        issues.append(_issue("REGISTRY_ENTRIES_INVALID", "entries must be a list"))
        entries = []

    status_values = set(registry.get("status_values") or [])
    category_values = set(registry.get("category_values") or [])
    projection_behavior_values = set(registry.get("projection_behavior_values") or [])
    names: dict[str, str] = {}

    for idx, entry in enumerate(entries):
        if not isinstance(entry, dict):
            issues.append(_issue("REGISTRY_ENTRY_INVALID", f"entry {idx} must be a mapping"))
            continue

        name = str(entry.get("name", "") or "")
        if not name:
            issues.append(_issue("REGISTRY_ENTRY_NAME_MISSING", f"entry {idx} missing name"))
            name = f"<entry-{idx}>"

        for field in sorted(REQUIRED_ENTRY_FIELDS):
            if field not in entry:
                issues.append(
                    _issue("REGISTRY_REQUIRED_ENTRY_FIELD_MISSING", f"missing field: {field}", entry=name)
                )

        if name in names:
            issues.append(
                _issue(
                    "REGISTRY_DUPLICATE_NAME",
                    f"duplicate name already seen with status {names[name]}",
                    entry=name,
                )
            )
        else:
            names[name] = str(entry.get("status", ""))

        status = str(entry.get("status", "") or "")
        category = str(entry.get("category", "") or "")
        projection_behavior = str(entry.get("profile_projection_behavior", "") or "")
        version_branch = entry.get("version_branch")
        introduced_in = entry.get("introduced_in")

        if status not in status_values:
            issues.append(_issue("REGISTRY_STATUS_INVALID", f"invalid status: {status}", entry=name))
        if category not in category_values:
            issues.append(_issue("REGISTRY_CATEGORY_INVALID", f"invalid category: {category}", entry=name))
        if projection_behavior not in projection_behavior_values:
            issues.append(
                _issue(
                    "REGISTRY_PROJECTION_BEHAVIOR_INVALID",
                    f"invalid profile_projection_behavior: {projection_behavior}",
                    entry=name,
                )
            )

        for bool_field in ("risk_relevant", "must_preserve_when_used_for_policy"):
            if not isinstance(entry.get(bool_field), bool):
                issues.append(
                    _issue(
                        "REGISTRY_BOOLEAN_FIELD_INVALID",
                        f"{bool_field} must be true or false",
                        entry=name,
                    )
                )

        for list_field in (
            "security_release_notes",
            "security_privacy_notes",
            "migration_notes",
            "fixture_references",
            "references",
        ):
            if not isinstance(entry.get(list_field), list):
                issues.append(
                    _issue(
                        "REGISTRY_LIST_FIELD_INVALID",
                        f"{list_field} must be a list",
                        entry=name,
                    )
                )

        risk_relevant = entry.get("risk_relevant") is True
        must_preserve = entry.get("must_preserve_when_used_for_policy") is True
        fixture_references = entry.get("fixture_references") or []
        security_privacy_notes = entry.get("security_privacy_notes") or []

        if must_preserve and not risk_relevant:
            issues.append(
                _issue(
                    "REGISTRY_POLICY_PRESERVE_WITHOUT_RISK",
                    "must_preserve_when_used_for_policy requires risk_relevant: true",
                    entry=name,
                )
            )
        if must_preserve and entry.get("ignorable_by_default") is True:
            issues.append(
                _issue(
                    "REGISTRY_POLICY_PRESERVE_IGNORABLE",
                    "policy-relevant extensions that must be preserved cannot be ignorable_by_default",
                    entry=name,
                )
            )
        if risk_relevant and projection_behavior in {"optional_omission", "not_applicable"}:
            issues.append(
                _issue(
                    "REGISTRY_RISK_PROJECTION_BEHAVIOR_INVALID",
                    "risk-relevant entries must declare preserve, preserve_or_compact, prohibited, or future_branch_required projection behavior",
                    entry=name,
                )
            )
        if risk_relevant and not security_privacy_notes:
            issues.append(
                _issue(
                    "REGISTRY_RISK_SECURITY_NOTES_MISSING",
                    "risk-relevant entries must include security_privacy_notes",
                    entry=name,
                )
            )
        if status in {"experimental", "adopted"} and risk_relevant and not fixture_references:
            issues.append(
                _issue(
                    "REGISTRY_RISK_FIXTURES_MISSING",
                    "implemented risk-relevant entries must reference positive or negative fixtures",
                    entry=name,
                )
            )
        for fixture_path in fixture_references:
            if not isinstance(fixture_path, str) or not fixture_path:
                issues.append(
                    _issue(
                        "REGISTRY_FIXTURE_REFERENCE_INVALID",
                        "fixture_references entries must be non-empty strings",
                        entry=name,
                    )
                )
                continue
            if status in {"experimental", "adopted"} and not (ROOT / fixture_path).exists():
                issues.append(
                    _issue(
                        "REGISTRY_FIXTURE_REFERENCE_MISSING",
                        f"fixture reference does not exist: {fixture_path}",
                        entry=name,
                    )
                )

        if status in {"experimental", "adopted", "deprecated", "superseded"} and not version_branch:
            issues.append(
                _issue(
                    "REGISTRY_VERSION_BRANCH_MISSING",
                    f"{status} entries must identify a version_branch",
                    entry=name,
                )
            )
        if status in {"reserved", "proposed"} and introduced_in:
            issues.append(
                _issue(
                    "REGISTRY_RESERVED_INTRODUCED",
                    "reserved/proposed entries must not claim introduced_in",
                    entry=name,
                )
            )
        if status in {"reserved", "proposed"}:
            if _implemented_status(entry, "schema_status"):
                issues.append(
                    _issue(
                        "REGISTRY_RESERVED_SCHEMA_IMPLEMENTED",
                        "reserved/proposed entries must not claim schema_status: implemented",
                        entry=name,
                    )
                )
            if _implemented_status(entry, "conformance_status"):
                issues.append(
                    _issue(
                        "REGISTRY_RESERVED_CONFORMANCE_IMPLEMENTED",
                        "reserved/proposed entries must not claim conformance_status: implemented",
                        entry=name,
                    )
                )

        if status == "experimental" and not _has_implementation_surface(entry):
            issues.append(
                _issue(
                    "REGISTRY_EXPERIMENTAL_SURFACE_MISSING",
                    "experimental entries must identify at least one implemented surface",
                    entry=name,
                )
            )

        if status == "adopted":
            for key in ["schema_status", "policy_status"]:
                if str(entry.get(key, "none") or "none") not in SUFFICIENT:
                    issues.append(
                        _issue(
                            "REGISTRY_ADOPTED_SURFACE_MISSING",
                            f"adopted entries require sufficient {key}",
                            entry=name,
                        )
                    )
            if str(entry.get("conformance_status", "none") or "none") != "implemented":
                issues.append(
                    _issue(
                        "REGISTRY_ADOPTED_CONFORMANCE_MISSING",
                        "adopted entries require conformance_status: implemented",
                        entry=name,
                    )
                )

        if status == "superseded" and not entry.get("superseded_by"):
            issues.append(
                _issue("REGISTRY_SUPERSEDED_TARGET_MISSING", "superseded entries must name superseded_by", entry=name)
            )

        if name.startswith("vendor.") and not VENDOR_NAME_RE.match(name):
            issues.append(
                _issue(
                    "REGISTRY_VENDOR_NAMESPACE_INVALID",
                    "vendor/private names must follow vendor.<owner>.<name>",
                    entry=name,
                )
            )

        if name.lower() in CORE_ENVELOPE_NAMES:
            issues.append(
                _issue(
                    "REGISTRY_CORE_REDEFINITION",
                    "entry name redefines a core envelope or invariant field",
                    entry=name,
                )
            )

    schema_v1_path = schema_v1_path or ROOT / "schema" / "zmeta-event-1.0.schema.json"
    schema_v1_1_path = schema_v1_1_path or ROOT / "schema" / "zmeta-event-1.1.0.schema.json"
    if schema_v1_path.exists() and schema_v1_1_path.exists():
        schema_v1_doc = _load_json(schema_v1_path)
        schema_v1_1_doc = _load_json(schema_v1_1_path)
        for name, reason in sorted(UNREGISTERED_RESERVED_SCHEMA_VALUES.items()):
            if _schema_contains_reserved_value(schema_v1_doc, name) or _schema_contains_reserved_value(
                schema_v1_1_doc, name
            ):
                issues.append(
                    _issue(
                        "REGISTRY_UNREGISTERED_SCHEMA_LEAK",
                        f"unregistered reserved value appears in a current schema: {reason}",
                        entry=name,
                    )
                )
        schema_v1 = _schema_validator(schema_v1_path)
        schema_v1_1 = _schema_validator(schema_v1_1_path)
        for entry in entries:
            if isinstance(entry, dict):
                issues.extend(_entry_context_checks(entry, schema_v1, schema_v1_1))
    else:
        issues.append(
            _issue(
                "REGISTRY_SCHEMA_CHECK_UNAVAILABLE",
                "schema paths missing; targeted schema collision checks were not run",
            )
        )

    return issues


def run(
    registry_path: Path | str,
    schema_v1_path: Path | str | None = None,
    schema_v1_1_path: Path | str | None = None,
    *,
    quiet: bool = False,
) -> int:
    registry = Path(registry_path)
    schema_v1 = Path(schema_v1_path) if schema_v1_path else None
    schema_v1_1 = Path(schema_v1_1_path) if schema_v1_1_path else None
    issues = validate_registry(registry, schema_v1, schema_v1_1)
    if issues:
        for issue in issues:
            entry = f" entry={issue['entry']}" if "entry" in issue else ""
            print(f"FAIL {issue['code']}{entry}: {issue['message']}")
        return 1

    if not quiet:
        data = load_registry(registry)
        print(f"extension registry ok entries={len(data.get('entries', []))}")
    return 0


def main() -> None:
    args = parse_args()
    raise SystemExit(
        run(
            args.registry,
            schema_v1_path=args.schema_v1,
            schema_v1_1_path=args.schema_v1_1,
        )
    )


if __name__ == "__main__":
    main()
