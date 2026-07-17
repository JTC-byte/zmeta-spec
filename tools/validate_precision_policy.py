from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

VALIDATORS_PATH = ROOT / "gateway" / "src" / "validators.py"
validators_spec = importlib.util.spec_from_file_location("zmeta_validators", VALIDATORS_PATH)
validators = importlib.util.module_from_spec(validators_spec)
validators_spec.loader.exec_module(validators)

PROJECTION_PATH = ROOT / "tools" / "validate_projection.py"
projection_spec = importlib.util.spec_from_file_location("zmeta_validate_projection", PROJECTION_PATH)
validate_projection = importlib.util.module_from_spec(projection_spec)
projection_spec.loader.exec_module(validate_projection)

import zmeta_compact
import zmeta_proto


FAILURE_CODES = (
    "PRECISION_POLICY_SCHEMA_INVALID_SOURCE",
    "PRECISION_POLICY_SCHEMA_INVALID_PROJECTED",
    "PRECISION_POLICY_POLICY_INVALID_SOURCE",
    "PRECISION_POLICY_POLICY_INVALID_PROJECTED",
    "PRECISION_POLICY_PROJECTION_INVALID",
    "PRECISION_POLICY_IMMUTABLE_CHANGED",
    "PRECISION_POLICY_UNIT_CHANGED",
    "PRECISION_POLICY_PRECISION_INCREASE",
    "PRECISION_POLICY_CONFIDENCE_INCREASE",
    "PRECISION_POLICY_CONFIDENCE_ROUNDING_INVALID",
    "PRECISION_POLICY_TTL_INCREASE",
    "PRECISION_POLICY_TTL_ROUNDING_INVALID",
    "PRECISION_POLICY_ERROR_BOUND_DECREASE",
    "PRECISION_POLICY_ERROR_BOUND_ROUNDING_INVALID",
    "PRECISION_POLICY_UTILITY_FLOOR_VIOLATION",
    "PRECISION_POLICY_COMMAND_GEOMETRY_TOO_COARSE",
    "PRECISION_POLICY_RF_QUANTIZATION_INVALID",
    "PRECISION_POLICY_REQUIRED_FIELD_REMOVED",
    "PRECISION_POLICY_OPTIONAL_OMISSION_NOT_ALLOWED",
    "PRECISION_POLICY_HIDDEN_DEFAULT",
    "PRECISION_POLICY_PACKET_BUDGET_STRIPPED_REQUIRED",
    "PRECISION_POLICY_SOURCE_LIMITED_PRECISION_UNDECLARED",
)

REQUIRED_POLICY_KEYS = {
    "policy_version",
    "policy_name",
    "policy_status",
    "requires_mission_review",
    "zmeta_versions",
    "profiles",
    "field_families",
    "immutable_paths",
    "unit_locked_paths",
    "rounding_modes",
    "utility_floors",
    "precision_ceilings",
    "packet_budget_guidance",
    "notes",
}

REQUIRED_EVENT_PATHS = (
    "zmeta_version",
    "event.event_id",
    "event.event_type",
    "event.event_subtype",
    "event.ts",
    "source.platform_id",
    "source.node_role",
    "source.producer",
    "payload",
)

REQUIRED_BY_TYPE = {
    "STATE_EVENT": (
        "payload.track_id",
        "payload.geo",
        "payload.geo.lat",
        "payload.geo.lon",
        "payload.geo.alt_m",
        "payload.valid_for_ms",
        "confidence",
        "lineage",
        "lineage.based_on",
    ),
    "COMMAND_EVENT": (
        "payload.task_id",
        "payload.task_type",
        "payload.valid_for_ms",
        "payload.requires_deconfliction",
    ),
    "SYSTEM_EVENT": ("payload.system_type", "payload.state"),
    "OBSERVATION_EVENT": ("payload.modality", "payload.features"),
    "INFERENCE_EVENT": (
        "payload.inference_type",
        "payload.claim",
        "payload.model.name",
        "payload.model.version",
        "payload.based_on",
        "confidence",
        "lineage.based_on",
    ),
    "FUSION_EVENT": (
        "payload.track_id",
        "payload.members",
        "payload.stability",
        "payload.last_seen_ts",
        "confidence",
        "lineage.based_on",
    ),
}

COMMAND_TARGET_PATHS = {"payload.target_geo.lat", "payload.target_geo.lon"}
RF_PATHS = {
    "payload.features.center_freq_hz",
    "payload.features.bandwidth_hz",
    "payload.features.power_dbm",
}
ERROR_BOUND_PATHS = (
    "payload.timing_quality.est_error_ms",
    "payload.quality.timing_quality.est_error_ms",
    "payload.metrics.est_error_ms",
)
HIDDEN_DEFAULT_PATHS = (
    "payload.heading_deg",
    "payload.speed_mps",
    "payload.bearing.az_deg",
    "payload.bearing.el_deg",
)
UNIT_SUFFIXES = ("_mps", "_dbm", "_bps", "_pct", "_deg", "_hz", "_ms", "_m")
MISSING = object()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate ZMeta profile precision policy fixtures.")
    parser.add_argument(
        "--policy",
        default=str(ROOT / "policy" / "profile-precision.yaml"),
        help="Profile precision policy YAML.",
    )
    parser.add_argument(
        "--must-pass",
        default=str(ROOT / "conformance" / "profile-precision" / "must-pass.jsonl"),
        help="JSONL fixture file whose cases must pass.",
    )
    parser.add_argument(
        "--must-fail",
        default=str(ROOT / "conformance" / "profile-precision" / "must-fail.jsonl"),
        help="JSONL fixture file whose cases must fail with expect_code.",
    )
    parser.add_argument("--quiet", action="store_true", help="Only print failures and final summary.")
    return parser.parse_args()


def _issue(code: str, message: str, path: str | None = None, details: dict[str, Any] | None = None):
    item: dict[str, Any] = {"code": code, "message": message}
    if path:
        item["path"] = path
    if details:
        item["details"] = details
    return item


def load_precision_policy(path: str | Path) -> dict[str, Any]:
    policy_path = Path(path)
    if not policy_path.exists():
        raise FileNotFoundError(f"profile precision policy not found: {policy_path}")
    with policy_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError("profile precision policy must be a YAML mapping")
    return data


def validate_policy_shape(policy: dict[str, Any]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for key in sorted(REQUIRED_POLICY_KEYS):
        if key not in policy:
            issues.append(_issue("PRECISION_POLICY_PROJECTION_INVALID", f"missing policy key: {key}"))
    if policy.get("policy_status") != "reference_conformance_default":
        issues.append(
            _issue(
                "PRECISION_POLICY_PROJECTION_INVALID",
                "policy_status must be reference_conformance_default",
            )
        )
    if policy.get("requires_mission_review") is not True:
        issues.append(
            _issue(
                "PRECISION_POLICY_PROJECTION_INVALID",
                "requires_mission_review must be true for S1-06B reference defaults",
            )
        )
    return issues


def iter_jsonl(path: str | Path):
    fixture_path = Path(path)
    if not fixture_path.exists():
        raise FileNotFoundError(f"profile precision fixture file not found: {fixture_path}")
    for line_no, line in enumerate(fixture_path.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        yield line_no, json.loads(line)


def _event_block(event: Any) -> dict[str, Any]:
    block = event.get("event", {}) if isinstance(event, dict) else {}
    return block if isinstance(block, dict) else {}


def _payload(event: Any) -> dict[str, Any]:
    payload = event.get("payload", {}) if isinstance(event, dict) else {}
    return payload if isinstance(payload, dict) else {}


def _event_type(event: Any) -> str | None:
    value = _event_block(event).get("event_type")
    return str(value) if value else None


def _event_subtype(event: Any) -> str | None:
    value = _event_block(event).get("event_subtype")
    return str(value) if value else None


def _get_path(value: Any, path: str) -> Any:
    target = value
    for part in path.split("."):
        if not isinstance(target, dict) or part not in target:
            return MISSING
        target = target[part]
    return target


def _set_path(value: dict[str, Any], path: str, item: Any) -> None:
    target: Any = value
    parts = path.split(".")
    for part in parts[:-1]:
        target = target.setdefault(part, {})
    target[parts[-1]] = item


def _flatten(value: Any, prefix: str = "") -> dict[str, Any]:
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for key, item in value.items():
            child = f"{prefix}.{key}" if prefix else str(key)
            out.update(_flatten(item, child))
        return out
    if isinstance(value, list):
        return {prefix: value} if prefix else {}
    return {prefix: value} if prefix else {}


def _values_equal(left: Any, right: Any) -> bool:
    return left == right


def _decimal(value: Any) -> Decimal | None:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _decimal_places(value: Any) -> int:
    decimal = _decimal(value)
    if decimal is None:
        return 0
    exponent = decimal.as_tuple().exponent
    return abs(exponent) if exponent < 0 else 0


def _is_multiple(value: Any, step: Any) -> bool:
    decimal = _decimal(value)
    step_value = _decimal(step)
    if decimal is None or step_value is None or step_value == 0:
        return False
    return decimal.remainder_near(step_value) == 0


def _abs_delta(left: Any, right: Any) -> Decimal | None:
    left_decimal = _decimal(left)
    right_decimal = _decimal(right)
    if left_decimal is None or right_decimal is None:
        return None
    return abs(left_decimal - right_decimal)


def _unit_suffix(path: str) -> str | None:
    leaf = path.split(".")[-1].lower()
    for suffix in UNIT_SUFFIXES:
        if leaf.endswith(suffix):
            return suffix
    return None


def _rules_for_profile(policy: dict[str, Any], target_profile: str) -> dict[str, dict[str, Any]]:
    rules = policy.get("precision_ceilings", {}).get(target_profile, {})
    return rules if isinstance(rules, dict) else {}


def _source_limited_ack(fixture: dict[str, Any]) -> bool:
    policy = fixture.get("policy", {})
    if isinstance(policy, dict) and policy.get("source_limited_precision"):
        return True
    return bool(fixture.get("source_limited_precision"))


def _required_paths(event: dict[str, Any]) -> list[str]:
    event_type = _event_type(event)
    paths = list(REQUIRED_EVENT_PATHS)
    paths.extend(REQUIRED_BY_TYPE.get(event_type or "", ()))
    if event_type == "COMMAND_EVENT" and _event_subtype(event) == "GOTO":
        paths.extend(("payload.target_geo", "payload.target_geo.lat", "payload.target_geo.lon"))
    if event_type == "SYSTEM_EVENT" and _payload(event).get("system_type") == "TIME_STATUS":
        paths.extend(
            (
                "payload.metrics",
                "payload.metrics.time_source",
                "payload.metrics.sync_state",
                "payload.metrics.est_error_ms",
                "payload.metrics.last_sync_ts",
            )
        )
    return paths


def _check_packet_budget(fixture: dict[str, Any], policy: dict[str, Any]) -> list[dict[str, Any]]:
    budget = fixture.get("packet_budget", {})
    if not isinstance(budget, dict):
        return []
    stripped = {str(path) for path in budget.get("stripped_paths", [])}
    required = set(policy.get("packet_budget_guidance", {}).get("required_paths_must_not_be_stripped", []))
    for path in sorted(stripped):
        for required_path in required:
            if path == required_path or path.startswith(required_path + ".") or required_path.startswith(path + "."):
                return [
                    _issue(
                        "PRECISION_POLICY_PACKET_BUDGET_STRIPPED_REQUIRED",
                        "packet-budget pressure stripped a required semantic path",
                        path=path,
                    )
                ]
    return []


def _check_required_removed(source: dict[str, Any], projected: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for path in _required_paths(source):
        if _get_path(source, path) is not MISSING and _get_path(projected, path) is MISSING:
            out.append(
                _issue(
                    "PRECISION_POLICY_REQUIRED_FIELD_REMOVED",
                    "required field was removed during precision projection",
                    path=path,
                )
            )
            break
    return out


def _check_immutable(source: dict[str, Any], projected: dict[str, Any], policy: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for path in policy.get("immutable_paths", []):
        source_value = _get_path(source, str(path))
        if source_value is MISSING:
            continue
        projected_value = _get_path(projected, str(path))
        if projected_value is MISSING or not _values_equal(source_value, projected_value):
            out.append(
                _issue(
                    "PRECISION_POLICY_IMMUTABLE_CHANGED",
                    "immutable semantic path changed during precision projection",
                    path=str(path),
                    details={"source": source_value, "projected": projected_value},
                )
            )
            break
    return out


def _check_hidden_defaults(source: dict[str, Any], projected: dict[str, Any]) -> list[dict[str, Any]]:
    source_geo = _get_path(source, "payload.geo")
    projected_geo = _get_path(projected, "payload.geo")
    if isinstance(source_geo, dict) and isinstance(projected_geo, dict):
        if (
            _decimal(source_geo.get("lat")) not in (None, Decimal("0"))
            and _decimal(source_geo.get("lon")) not in (None, Decimal("0"))
            and _decimal(projected_geo.get("lat")) == Decimal("0")
            and _decimal(projected_geo.get("lon")) == Decimal("0")
        ):
            return [
                _issue(
                    "PRECISION_POLICY_HIDDEN_DEFAULT",
                    "projected geo was zero-filled instead of conservatively quantized",
                    path="payload.geo",
                )
            ]
    for path in HIDDEN_DEFAULT_PATHS:
        if _get_path(source, path) is MISSING:
            projected_value = _get_path(projected, path)
            if projected_value is not MISSING and _decimal(projected_value) == Decimal("0"):
                return [
                    _issue(
                        "PRECISION_POLICY_HIDDEN_DEFAULT",
                        "projection introduced an implicit zero default",
                        path=path,
                    )
                ]
    return []


def _check_confidence(source: dict[str, Any], projected: dict[str, Any], rules: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    source_confidence = _get_path(source, "confidence")
    projected_confidence = _get_path(projected, "confidence")
    if source_confidence is MISSING or projected_confidence is MISSING:
        return []
    source_decimal = _decimal(source_confidence)
    projected_decimal = _decimal(projected_confidence)
    if source_decimal is None or projected_decimal is None:
        return []
    if projected_decimal > source_decimal:
        return [
            _issue(
                "PRECISION_POLICY_CONFIDENCE_INCREASE",
                "projected confidence increased",
                path="confidence",
                details={"source": source_confidence, "projected": projected_confidence},
            )
        ]
    rule = rules.get("confidence", {})
    max_places = rule.get("max_decimal_places")
    if max_places is not None and _decimal_places(projected_confidence) > int(max_places):
        return [
            _issue(
                "PRECISION_POLICY_CONFIDENCE_ROUNDING_INVALID",
                "projected confidence exceeds profile decimal ceiling",
                path="confidence",
            )
        ]
    return []


def _check_ttl(source: dict[str, Any], projected: dict[str, Any], rules: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    path = "payload.valid_for_ms"
    source_value = _get_path(source, path)
    projected_value = _get_path(projected, path)
    if source_value is MISSING or projected_value is MISSING:
        return []
    if int(projected_value) > int(source_value):
        return [
            _issue(
                "PRECISION_POLICY_TTL_INCREASE",
                "projected valid_for_ms increased",
                path=path,
                details={"source": source_value, "projected": projected_value},
            )
        ]
    rule = rules.get(path, {})
    step = rule.get("quantization_step")
    if step is not None and not _is_multiple(projected_value, step):
        return [
            _issue(
                "PRECISION_POLICY_TTL_ROUNDING_INVALID",
                "projected valid_for_ms is not aligned to the profile TTL step",
                path=path,
            )
        ]
    return []


def _check_error_bounds(source: dict[str, Any], projected: dict[str, Any], rules: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    for path in ERROR_BOUND_PATHS:
        source_value = _get_path(source, path)
        projected_value = _get_path(projected, path)
        if source_value is MISSING or projected_value is MISSING:
            continue
        source_decimal = _decimal(source_value)
        projected_decimal = _decimal(projected_value)
        if source_decimal is None or projected_decimal is None:
            continue
        if projected_decimal < source_decimal:
            return [
                _issue(
                    "PRECISION_POLICY_ERROR_BOUND_DECREASE",
                    "projected error or timing uncertainty decreased",
                    path=path,
                    details={"source": source_value, "projected": projected_value},
                )
            ]
        step = rules.get(path, {}).get("quantization_step")
        if step is not None and not _is_multiple(projected_value, step):
            return [
                _issue(
                    "PRECISION_POLICY_ERROR_BOUND_ROUNDING_INVALID",
                    "projected error or timing uncertainty is not aligned to the profile step",
                    path=path,
                )
            ]
    return []


def _check_decimal_rules(
    source: dict[str, Any],
    projected: dict[str, Any],
    rules: dict[str, dict[str, Any]],
    fixture: dict[str, Any],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for path, rule in rules.items():
        if not isinstance(rule, dict) or "max_decimal_places" not in rule:
            continue
        if path == "confidence":
            continue
        source_value = _get_path(source, path)
        projected_value = _get_path(projected, path)
        if source_value is MISSING or projected_value is MISSING:
            continue
        source_places = _decimal_places(source_value)
        projected_places = _decimal_places(projected_value)
        max_places = int(rule["max_decimal_places"])
        floor = rule.get("utility_floor_decimal_places")
        if projected_places > source_places:
            out.append(
                _issue(
                    "PRECISION_POLICY_PRECISION_INCREASE",
                    "projected numeric field has more decimal precision than the source",
                    path=path,
                )
            )
            break
        if projected_places > max_places:
            out.append(
                _issue(
                    "PRECISION_POLICY_PRECISION_INCREASE",
                    "projected numeric field exceeds the profile precision ceiling",
                    path=path,
                )
            )
            break
        if floor is None:
            continue
        floor_value = int(floor)
        if source_places < floor_value and projected_places <= source_places and not _source_limited_ack(fixture):
            out.append(
                _issue(
                    "PRECISION_POLICY_SOURCE_LIMITED_PRECISION_UNDECLARED",
                    "source-limited precision below the utility floor was not explicitly acknowledged",
                    path=path,
                )
            )
            break
        if source_places >= floor_value and projected_places < floor_value:
            code = (
                "PRECISION_POLICY_COMMAND_GEOMETRY_TOO_COARSE"
                if path in COMMAND_TARGET_PATHS or rule.get("command_geometry")
                else "PRECISION_POLICY_UTILITY_FLOOR_VIOLATION"
            )
            out.append(
                _issue(
                    code,
                    "projected field is below the profile utility floor",
                    path=path,
                )
            )
            break
    return out


def _check_step_rules(
    source: dict[str, Any],
    projected: dict[str, Any],
    rules: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    for path, rule in rules.items():
        if not isinstance(rule, dict) or "quantization_step" not in rule:
            continue
        if path in RF_PATHS or path in ERROR_BOUND_PATHS or path == "payload.valid_for_ms":
            continue
        source_value = _get_path(source, path)
        projected_value = _get_path(projected, path)
        if source_value is MISSING or projected_value is MISSING:
            continue
        step = rule["quantization_step"]
        if not _is_multiple(projected_value, step):
            return [
                _issue(
                    "PRECISION_POLICY_UNIT_CHANGED" if _unit_suffix(path) else "PRECISION_POLICY_PRECISION_INCREASE",
                    "projected field is not aligned to the configured quantization step",
                    path=path,
                )
            ]
        delta = _abs_delta(source_value, projected_value)
        step_decimal = _decimal(step)
        if delta is not None and step_decimal is not None and delta > step_decimal / 2:
            return [
                _issue(
                    "PRECISION_POLICY_UNIT_CHANGED" if _unit_suffix(path) else "PRECISION_POLICY_PRECISION_INCREASE",
                    "projected field moved beyond the allowed quantization tolerance",
                    path=path,
                    details={"source": source_value, "projected": projected_value, "step": step},
                )
            ]
    return []


def _check_rf_rules(source: dict[str, Any], projected: dict[str, Any], rules: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    for path in sorted(RF_PATHS):
        rule = rules.get(path)
        if not isinstance(rule, dict):
            continue
        source_value = _get_path(source, path)
        projected_value = _get_path(projected, path)
        if source_value is MISSING or projected_value is MISSING:
            continue
        step = rule.get("quantization_step")
        if step is not None and not _is_multiple(projected_value, step):
            return [
                _issue(
                    "PRECISION_POLICY_RF_QUANTIZATION_INVALID",
                    "RF value is not aligned to the configured quantization step",
                    path=path,
                )
            ]
        max_delta = _decimal(rule.get("max_delta", Decimal(str(step)) / 2 if step is not None else "0"))
        delta = _abs_delta(source_value, projected_value)
        if max_delta is not None and delta is not None and delta > max_delta:
            return [
                _issue(
                    "PRECISION_POLICY_RF_QUANTIZATION_INVALID",
                    "RF value moved outside the allowed policy tolerance",
                    path=path,
                    details={"source": source_value, "projected": projected_value},
                )
            ]
    return []


def _roundtrip_projected(projected: dict[str, Any], fixture: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    event = copy.deepcopy(projected)
    roundtrips = fixture.get("roundtrip", [])
    if isinstance(roundtrips, str):
        roundtrips = [roundtrips]
    out: list[dict[str, Any]] = []
    for encoding in roundtrips:
        try:
            if encoding == "compact":
                decoded = zmeta_compact.loads(zmeta_compact.dumps(event))
            elif encoding in {"proto", "protobuf"}:
                decoded = zmeta_proto.loads(zmeta_proto.dumps(event))
            else:
                out.append(_issue("PRECISION_POLICY_PROJECTION_INVALID", f"unsupported roundtrip encoding: {encoding}"))
                continue
            if decoded != event:
                out.append(
                    _issue(
                        "PRECISION_POLICY_PROJECTION_INVALID",
                        "encoding roundtrip did not preserve projected canonical JSON",
                    )
                )
            event = decoded
        except Exception as exc:
            out.append(
                _issue(
                    "PRECISION_POLICY_PROJECTION_INVALID",
                    "projected event failed encoding roundtrip",
                    details={"encoding": str(encoding), "error": str(exc)},
                )
            )
    return event, out


def _precision_projection_issue_allowed(
    issue: dict[str, Any],
    source: dict[str, Any],
    projected: dict[str, Any],
    rules: dict[str, dict[str, Any]],
) -> bool:
    code = issue.get("code")
    path = issue.get("path")
    if code not in {"PROJECTION_FIELD_CHANGED", "PROJECTION_PRECISION_INCREASE", "PROJECTION_UNIT_CHANGED"}:
        return False
    if isinstance(path, str) and path in rules:
        return True
    if path == "payload.features":
        for rf_path in RF_PATHS:
            if _get_path(source, rf_path) is not MISSING and _get_path(projected, rf_path) is not MISSING:
                if _check_rf_rules(source, projected, rules):
                    return False
        source_features = _get_path(source, "payload.features")
        projected_features = _get_path(projected, "payload.features")
        if not isinstance(source_features, dict) or not isinstance(projected_features, dict):
            return False
        for key, value in source_features.items():
            path_key = f"payload.features.{key}"
            if path_key in RF_PATHS:
                continue
            if projected_features.get(key) != value:
                return False
        return True
    return str(path) in RF_PATHS and not _check_rf_rules(source, projected, rules)


def _map_projection_issue(issue: dict[str, Any]) -> dict[str, Any]:
    original_code = str(issue.get("code", ""))
    mapping = {
        "PROJECTION_SCHEMA_INVALID_SOURCE": "PRECISION_POLICY_SCHEMA_INVALID_SOURCE",
        "PROJECTION_SCHEMA_INVALID_PROJECTED": "PRECISION_POLICY_SCHEMA_INVALID_PROJECTED",
        "PROJECTION_POLICY_INVALID_SOURCE": "PRECISION_POLICY_POLICY_INVALID_SOURCE",
        "PROJECTION_POLICY_INVALID_PROJECTED": "PRECISION_POLICY_POLICY_INVALID_PROJECTED",
        "PROJECTION_CONFIDENCE_INCREASE": "PRECISION_POLICY_CONFIDENCE_INCREASE",
        "PROJECTION_TTL_INCREASE": "PRECISION_POLICY_TTL_INCREASE",
        "PROJECTION_PRECISION_INCREASE": "PRECISION_POLICY_PRECISION_INCREASE",
        "PROJECTION_UNIT_CHANGED": "PRECISION_POLICY_UNIT_CHANGED",
        "PROJECTION_REQUIRED_FIELD_REMOVED": "PRECISION_POLICY_REQUIRED_FIELD_REMOVED",
        "PROJECTION_LINEAGE_REMOVED": "PRECISION_POLICY_REQUIRED_FIELD_REMOVED",
        "PROJECTION_UNDECLARED_OPTIONAL_OMISSION": "PRECISION_POLICY_OPTIONAL_OMISSION_NOT_ALLOWED",
        "PROJECTION_EVENT_ID_CHANGED": "PRECISION_POLICY_IMMUTABLE_CHANGED",
        "PROJECTION_VERSION_CHANGED": "PRECISION_POLICY_IMMUTABLE_CHANGED",
        "PROJECTION_EVENT_TS_CHANGED": "PRECISION_POLICY_IMMUTABLE_CHANGED",
        "PROJECTION_EVENT_TYPE_CHANGED": "PRECISION_POLICY_IMMUTABLE_CHANGED",
        "PROJECTION_EVENT_SUBTYPE_CHANGED": "PRECISION_POLICY_IMMUTABLE_CHANGED",
        "PROJECTION_SOURCE_CHANGED": "PRECISION_POLICY_IMMUTABLE_CHANGED",
        "PROJECTION_TRACK_ID_CHANGED": "PRECISION_POLICY_IMMUTABLE_CHANGED",
        "PROJECTION_LINEAGE_CHANGED": "PRECISION_POLICY_IMMUTABLE_CHANGED",
        "PROJECTION_TRANSFORM_REMOVED": "PRECISION_POLICY_REQUIRED_FIELD_REMOVED",
    }
    code = mapping.get(original_code, "PRECISION_POLICY_PROJECTION_INVALID")
    return _issue(
        code,
        f"projection preservation failed: {original_code}",
        path=issue.get("path"),
        details={"original_code": original_code, "original_details": issue.get("details", {})},
    )


def _projection_issues(
    fixture: dict[str, Any],
    source: dict[str, Any],
    projected: dict[str, Any],
    rules: dict[str, dict[str, Any]],
    catalog: dict[str, Any],
    base_policy: dict[str, Any],
    schema_validator: Any,
) -> list[dict[str, Any]]:
    projection_fixture = copy.deepcopy(fixture)
    projection_fixture["source"] = source
    projection_fixture["projected"] = projected
    projection_fixture["roundtrip"] = []
    issues = validate_projection.compare_projection(projection_fixture, catalog, base_policy, schema_validator)
    out = []
    for issue in issues:
        if _precision_projection_issue_allowed(issue, source, projected, rules):
            continue
        out.append(_map_projection_issue(issue))
    return out


def compare_precision(
    fixture: dict[str, Any],
    precision_policy: dict[str, Any],
    catalog: dict[str, Any],
    base_policy: dict[str, Any],
    schema_validator: Any,
) -> list[dict[str, Any]]:
    source = fixture.get("source")
    projected = fixture.get("projected")
    target_profile = str(fixture.get("target_profile") or "")
    if not isinstance(source, dict):
        return [_issue("PRECISION_POLICY_SCHEMA_INVALID_SOURCE", "fixture source must be a ZMeta event object")]
    if not isinstance(projected, dict):
        return [_issue("PRECISION_POLICY_SCHEMA_INVALID_PROJECTED", "fixture projected must be a ZMeta event object")]

    projected_for_checks, roundtrip_issues = _roundtrip_projected(projected, fixture)
    if roundtrip_issues:
        return roundtrip_issues

    rules = _rules_for_profile(precision_policy, target_profile)
    if target_profile not in precision_policy.get("profiles", {}):
        return [
            _issue(
                "PRECISION_POLICY_PROJECTION_INVALID",
                "fixture target_profile is not configured in precision policy",
                details={"target_profile": target_profile},
            )
        ]

    direct_checks = [
        _check_packet_budget(fixture, precision_policy),
        _check_required_removed(source, projected_for_checks),
        _check_immutable(source, projected_for_checks, precision_policy),
        _check_hidden_defaults(source, projected_for_checks),
        _check_confidence(source, projected_for_checks, rules),
        _check_ttl(source, projected_for_checks, rules),
        _check_error_bounds(source, projected_for_checks, rules),
        _check_decimal_rules(source, projected_for_checks, rules, fixture),
        _check_rf_rules(source, projected_for_checks, rules),
        _check_step_rules(source, projected_for_checks, rules),
    ]
    for issues in direct_checks:
        if issues:
            return issues

    return _projection_issues(
        fixture,
        source,
        projected_for_checks,
        rules,
        catalog,
        base_policy,
        schema_validator,
    )


def _case_label(item: dict[str, Any], line_no: int) -> str:
    return str(item.get("name") or item.get("case_id") or f"line-{line_no}")


def run_suite(
    *,
    policy_path: str | Path,
    must_pass_path: str | Path,
    must_fail_path: str | Path,
    quiet: bool = False,
) -> int:
    precision_policy = load_precision_policy(policy_path)
    shape_issues = validate_policy_shape(precision_policy)
    catalog = validate_projection.load_catalog(ROOT / "conformance" / "profile_projection_field_catalog.yaml")
    schema_validator = validators.load_schema(ROOT / "schema" / "zmeta-event.schema.json")
    base_policy = validators.load_policy(ROOT / "policy")

    failures = 0
    passed = 0
    expected_failures = 0
    must_pass_total = 0
    must_fail_total = 0

    if shape_issues:
        for issue in shape_issues:
            print(f"FAIL policy {issue['code']}: {issue['message']}")
        return 1

    for line_no, item in iter_jsonl(must_pass_path):
        must_pass_total += 1
        label = _case_label(item, line_no)
        issues = compare_precision(item, precision_policy, catalog, base_policy, schema_validator)
        if issues:
            failures += 1
            codes = ",".join(issue["code"] for issue in issues)
            print(f"FAIL must-pass name={label} codes={codes}")
            for issue in issues:
                print(f"  {issue['code']}: {issue['message']}")
        else:
            passed += 1
            if not quiet:
                print(f"PASS must-pass name={label}")

    for line_no, item in iter_jsonl(must_fail_path):
        must_fail_total += 1
        label = _case_label(item, line_no)
        expected = item.get("expect_code")
        if expected not in FAILURE_CODES:
            failures += 1
            print(f"FAIL must-fail name={label} invalid or missing expect_code={expected}")
            continue
        issues = compare_precision(item, precision_policy, catalog, base_policy, schema_validator)
        codes = [issue["code"] for issue in issues]
        selected = next((issue for issue in issues if issue["code"] == expected), issues[0] if issues else None)
        message_contains = item.get("expect_message_contains")
        if expected not in codes:
            failures += 1
            code_str = ",".join(codes) or "none"
            print(f"FAIL must-fail name={label} expected={expected} got={code_str}")
            for issue in issues:
                print(f"  {issue['code']}: {issue['message']}")
        elif message_contains and selected and str(message_contains) not in selected.get("message", ""):
            failures += 1
            print(f"FAIL must-fail name={label} expected message to contain={message_contains}")
        else:
            expected_failures += 1
            if not quiet:
                print(f"PASS must-fail name={label} expected={expected}")

    if must_pass_total == 0:
        failures += 1
        print(f"FAIL must-pass file {must_pass_path} contains no fixtures - an empty file proves nothing")
    if must_fail_total == 0:
        failures += 1
        print(f"FAIL must-fail file {must_fail_path} contains no fixtures - an empty file proves nothing")

    total = passed + expected_failures
    if failures:
        print(f"profile precision policy failed total={total} failures={failures}")
        return 1
    print(f"profile precision policy ok total={total}")
    return 0


def main() -> None:
    args = parse_args()
    raise SystemExit(
        run_suite(
            policy_path=args.policy,
            must_pass_path=args.must_pass,
            must_fail_path=args.must_fail,
            quiet=args.quiet,
        )
    )


if __name__ == "__main__":
    main()
