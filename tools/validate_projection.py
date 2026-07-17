from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import sys
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from fnmatch import fnmatchcase
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

VALIDATORS_PATH = ROOT / "gateway" / "src" / "validators.py"
spec = importlib.util.spec_from_file_location("zmeta_validators", VALIDATORS_PATH)
validators = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validators)

import zmeta_compact
import zmeta_proto


FAILURE_CODES = (
    "PROJECTION_EVENT_ID_CHANGED",
    "PROJECTION_VERSION_CHANGED",
    "PROJECTION_EVENT_TS_CHANGED",
    "PROJECTION_EVENT_TYPE_CHANGED",
    "PROJECTION_EVENT_SUBTYPE_CHANGED",
    "PROJECTION_SOURCE_CHANGED",
    "PROJECTION_SOURCE_REWRITTEN",
    "PROJECTION_TRACK_ID_CHANGED",
    "PROJECTION_LINEAGE_REMOVED",
    "PROJECTION_LINEAGE_CHANGED",
    "PROJECTION_TRANSFORM_REMOVED",
    "PROJECTION_CONFIDENCE_INCREASE",
    "PROJECTION_TTL_INCREASE",
    "PROJECTION_PRECISION_INCREASE",
    "PROJECTION_UNIT_CHANGED",
    "PROJECTION_REQUIRED_FIELD_REMOVED",
    "PROJECTION_PROHIBITED_FIELD_ADDED",
    "PROJECTION_SEMANTIC_LAYER_COLLAPSE",
    "PROJECTION_PROFILE_ILLEGAL_EVENT",
    "PROJECTION_POLICY_RISK_LABEL_REMOVED",
    "PROJECTION_EXTERNAL_PROMOTION_EVIDENCE_REMOVED",
    "PROJECTION_UNDECLARED_OPTIONAL_OMISSION",
    "PROJECTION_ENCODING_DECODE_INVALID",
    "PROJECTION_SCHEMA_INVALID_SOURCE",
    "PROJECTION_SCHEMA_INVALID_PROJECTED",
    "PROJECTION_POLICY_INVALID_SOURCE",
    "PROJECTION_POLICY_INVALID_PROJECTED",
    "PROJECTION_FIELD_CHANGED",
)

MISSING = object()
UNIT_SUFFIXES = (
    "_mps",
    "_dbm",
    "_bps",
    "_pct",
    "_deg",
    "_hz",
    "_ms",
    "_m",
)
STATE_PROHIBITED_PAYLOAD_FIELDS = {
    "features",
    "raw_features",
    "modality",
    "measurement",
    "measurements",
    "t_start",
    "t_end",
    "data_ref",
    "data_refs",
}
# Full contract 7.8 enumerated altitude set (matching the
# policy/semantics.yaml command_event denylist); "altitude"-substring keys
# such as target_altitude are caught by the substring check below. Bare
# "msl_m" is kept as a defensive superset.
COMMAND_ALTITUDE_KEYS = {
    "alt",
    "alt_m",
    "altitude",
    "altitude_m",
    "alt_hae_m",
    "alt_msl_m",
    "agl_m",
    "msl_m",
    "target_alt_m",
}

REQUIRED_ALWAYS = (
    "zmeta_version",
    "event",
    "event.event_id",
    "event.event_type",
    "event.event_subtype",
    "event.ts",
    "source",
    "source.platform_id",
    "source.node_role",
    "source.producer",
    "payload",
)

REQUIRED_BY_EVENT_TYPE = {
    "OBSERVATION_EVENT": (
        "payload.modality",
        "payload.features",
    ),
    "INFERENCE_EVENT": (
        "confidence",
        "lineage",
        "lineage.based_on",
        "payload.inference_type",
        "payload.claim",
        "payload.model.name",
        "payload.model.version",
        "payload.based_on",
    ),
    "FUSION_EVENT": (
        "confidence",
        "lineage",
        "lineage.based_on",
        "payload.track_id",
        "payload.members",
        "payload.stability",
        "payload.last_seen_ts",
    ),
    "STATE_EVENT": (
        "confidence",
        "lineage",
        "lineage.based_on",
        "payload.track_id",
        "payload.geo",
        "payload.geo.lat",
        "payload.geo.lon",
        "payload.geo.alt_m",
        "payload.valid_for_ms",
    ),
    "COMMAND_EVENT": (
        "payload.task_id",
        "payload.task_type",
        "payload.valid_for_ms",
        "payload.requires_deconfliction",
    ),
    "SYSTEM_EVENT": (
        "payload.system_type",
        "payload.state",
    ),
}

COMMAND_REQUIRED_BY_SUBTYPE = {
    "GOTO": ("payload.target_geo", "payload.target_geo.lat", "payload.target_geo.lon"),
    "ORBIT": (
        "payload.target_geo",
        "payload.target_geo.lat",
        "payload.target_geo.lon",
        "payload.geometry",
    ),
    "SEARCH_BOX": ("payload.geometry",),
}

SYSTEM_REQUIRED_BY_SUBTYPE = {
    "TIME_STATUS": (
        "payload.metrics",
        "payload.metrics.time_source",
        "payload.metrics.sync_state",
        "payload.metrics.est_error_ms",
        "payload.metrics.last_sync_ts",
    ),
    "LINK_STATUS": ("payload.metrics", "payload.metrics.link_id"),
    "TASK_ACK": ("payload.metrics", "payload.metrics.task_id", "payload.metrics.original_event_id"),
    "SCHEMA_VIOLATION": (
        "payload.metrics",
        "payload.metrics.reason_code",
        "payload.metrics.original_event_id",
    ),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate ZMeta profile projection fixtures.")
    parser.add_argument(
        "--catalog",
        default=str(ROOT / "conformance" / "profile_projection_field_catalog.yaml"),
        help="Projection field catalog YAML.",
    )
    parser.add_argument(
        "--must-pass",
        default=str(ROOT / "conformance" / "profile-projection" / "must-pass.jsonl"),
        help="JSONL fixture file whose cases must pass.",
    )
    parser.add_argument(
        "--must-fail",
        default=str(ROOT / "conformance" / "profile-projection" / "must-fail.jsonl"),
        help="JSONL fixture file whose cases must fail with expect_code.",
    )
    parser.add_argument("--quiet", action="store_true", help="Only print failures and final summary.")
    return parser.parse_args()


def load_catalog(path: str | Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError("projection catalog must be a YAML mapping")
    data.setdefault("rules", [])
    return data


def iter_jsonl(path: str | Path):
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"projection fixture file not found: {path}")
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        yield line_no, json.loads(line)


def _violation(code: str, message: str, path: str | None = None, details: dict[str, Any] | None = None):
    item: dict[str, Any] = {"code": code, "message": message}
    if path:
        item["path"] = path
    if details:
        item["details"] = details
    return item


def _event_block(event: Any) -> dict[str, Any]:
    return event.get("event", {}) if isinstance(event, dict) else {}


def _payload(event: Any) -> dict[str, Any]:
    payload = event.get("payload", {}) if isinstance(event, dict) else {}
    return payload if isinstance(payload, dict) else {}


def _source(event: Any) -> dict[str, Any]:
    source = event.get("source", {}) if isinstance(event, dict) else {}
    return source if isinstance(source, dict) else {}


def _event_type(event: Any) -> str | None:
    value = _event_block(event).get("event_type")
    return str(value) if value is not None else None


def _event_subtype(event: Any) -> str | None:
    value = _event_block(event).get("event_subtype")
    return str(value) if value is not None else None


def _event_id(event: Any) -> str:
    value = _event_block(event).get("event_id")
    return str(value) if value else "UNKNOWN"


def _get_path(value: Any, path: str) -> Any:
    target = value
    for part in path.split("."):
        if not part:
            continue
        if not isinstance(target, dict) or part not in target:
            return MISSING
        target = target[part]
    return target


def _flatten(value: Any, prefix: str = "") -> dict[str, Any]:
    if isinstance(value, dict):
        if not value:
            return {prefix: value} if prefix else {}
        out: dict[str, Any] = {}
        for key, item in value.items():
            child = f"{prefix}.{key}" if prefix else str(key)
            out.update(_flatten(item, child))
        return out
    if isinstance(value, list):
        return {prefix: value} if prefix else {}
    return {prefix: value} if prefix else {}


def _walk(value: Any, prefix: str = ""):
    if isinstance(value, dict):
        for key, item in value.items():
            child = f"{prefix}.{key}" if prefix else str(key)
            yield child, key, item
            yield from _walk(item, child)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            child = f"{prefix}.{index}" if prefix else str(index)
            yield child, str(index), item
            yield from _walk(item, child)


def _path_matches(rule_path: str, value_path: str, *, allow_descendant: bool = False) -> bool:
    if rule_path == value_path:
        return True
    if allow_descendant and value_path.startswith(rule_path + "."):
        return True
    return fnmatchcase(value_path, rule_path)


def _rule_applies(rule: dict[str, Any], event_type: str | None, target_profile: str) -> bool:
    event_types = rule.get("event_types") or []
    profiles = rule.get("profiles") or []
    return ("*" in event_types or event_type in event_types) and target_profile in profiles


def _rule_statuses(rule: dict[str, Any]) -> set[str]:
    status = rule.get("status", [])
    if isinstance(status, str):
        return {status}
    return {str(item) for item in status}


def _matching_rules(
    catalog: dict[str, Any],
    path: str,
    event_type: str | None,
    target_profile: str,
    *,
    allow_descendant: bool = False,
) -> list[dict[str, Any]]:
    rules = []
    for rule in catalog.get("rules", []):
        if not isinstance(rule, dict):
            continue
        rule_path = str(rule.get("path", ""))
        if not rule_path or not _path_matches(rule_path, path, allow_descendant=allow_descendant):
            continue
        if _rule_applies(rule, event_type, target_profile):
            rules.append(rule)
    return rules


def _catalog_allows_optional_omission(
    catalog: dict[str, Any],
    path: str,
    event_type: str | None,
    target_profile: str,
) -> bool:
    for rule in _matching_rules(
        catalog, path, event_type, target_profile, allow_descendant=True
    ):
        statuses = _rule_statuses(rule)
        if "optional_removable" in statuses:
            return True
    return False


def _catalog_is_precision_reducible(
    catalog: dict[str, Any],
    path: str,
    event_type: str | None,
    target_profile: str,
) -> bool:
    for rule in _matching_rules(catalog, path, event_type, target_profile):
        statuses = _rule_statuses(rule)
        if "precision_reducible" in statuses or rule.get("comparison") == "precision_non_increase":
            return True
    return False


def _catalog_equality_rules(catalog: dict[str, Any], event_type: str | None, target_profile: str):
    for rule in catalog.get("rules", []):
        if not isinstance(rule, dict):
            continue
        if rule.get("comparison") != "equality":
            continue
        if not _rule_applies(rule, event_type, target_profile):
            continue
        yield str(rule.get("path", ""))


def _allowed_event_types(policy: dict[str, Any], profile: str) -> set[str]:
    cfg = policy.get("profiles", {}).get(profile, {})
    return {str(item) for item in cfg.get("allowed_event_types", [])}


def _hard_violations(violations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [item for item in violations if item.get("severity") != "warn"]


def _policy_checks(
    event: dict[str, Any],
    profile: str,
    policy: dict[str, Any],
    schema_validator: Any,
    context: list[dict[str, Any]],
    *,
    source_label: str,
) -> list[dict[str, Any]]:
    severity_map = policy.get("violation_severities", {})
    prefix = "SOURCE" if source_label == "source" else "PROJECTED"
    schema_code = f"PROJECTION_SCHEMA_INVALID_{prefix}"
    policy_code = f"PROJECTION_POLICY_INVALID_{prefix}"

    ok, schema_violations = validators.validate_schema(event, schema_validator, severity_map)
    out: list[dict[str, Any]] = []
    if not ok:
        first = schema_violations[0]
        out.append(
            _violation(
                schema_code,
                f"{source_label} event failed schema validation: {first.get('message')}",
                details={"original_code": first.get("code"), "original_details": first.get("details", {})},
            )
        )

    state = validators.ValidationState()
    for item in context:
        if isinstance(item, dict):
            state.record(item)

    checks = [
        validators.validate_role(
            event, {"roles": policy["roles"], "deny": policy["deny"]}, severity_map
        ),
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
            event, policy.get("producer_authority", {}), severity_map
        ),
        validators.validate_routing(event, policy["routing"], severity_map),
    ]
    policy_violations: list[dict[str, Any]] = []
    for _ok, violations in checks:
        policy_violations.extend(_hard_violations(violations))

    if policy_violations:
        first = policy_violations[0]
        if (
            source_label == "projected"
            and first.get("code") in {"EVENT_TYPE_NOT_ALLOWED_FOR_PROFILE", "PROFILE_MISMATCH"}
        ):
            out.append(
                _violation(
                    "PROJECTION_PROFILE_ILLEGAL_EVENT",
                    "projected event is not legal for the target profile",
                    details={"original_code": first.get("code"), "profile": profile},
                )
            )
        out.append(
            _violation(
                policy_code,
                f"{source_label} event failed policy validation: {first.get('code')}",
                details={"original_code": first.get("code"), "original_details": first.get("details", {})},
            )
        )
    return out


def _context_events(fixture: dict[str, Any]) -> list[dict[str, Any]]:
    context = fixture.get("context", [])
    if isinstance(context, dict):
        return [context]
    if isinstance(context, list):
        return [item for item in context if isinstance(item, dict)]
    return []


def _context_has_time_status(context: list[dict[str, Any]]) -> bool:
    for item in context:
        payload = _payload(item)
        if _event_type(item) == "SYSTEM_EVENT" and payload.get("system_type") == "TIME_STATUS":
            return True
    return False


def _same_decimal(left: Any, right: Any) -> bool:
    try:
        return Decimal(str(left)) == Decimal(str(right))
    except InvalidOperation:
        return left == right


def _decimal_places(value: Any) -> int:
    try:
        decimal = Decimal(str(value))
    except InvalidOperation:
        return 0
    exponent = decimal.as_tuple().exponent
    return abs(exponent) if exponent < 0 else 0


def _quantize_to_places(value: Any, places: int) -> Decimal | None:
    try:
        decimal = Decimal(str(value))
    except InvalidOperation:
        return None
    quantum = Decimal("1") if places == 0 else Decimal("1").scaleb(-places)
    return decimal.quantize(quantum, rounding=ROUND_HALF_UP)


def _is_precision_projection_ok(source_value: Any, projected_value: Any) -> bool:
    if not isinstance(source_value, (int, float)) or not isinstance(projected_value, (int, float)):
        return source_value == projected_value
    source_places = _decimal_places(source_value)
    projected_places = _decimal_places(projected_value)
    if projected_places > source_places:
        return False
    rounded = _quantize_to_places(source_value, projected_places)
    if rounded is None:
        return False
    try:
        return rounded == Decimal(str(projected_value))
    except InvalidOperation:
        return False


def _unit_suffix(path: str) -> str | None:
    leaf = path.split(".")[-1].lower()
    for suffix in UNIT_SUFFIXES:
        if leaf.endswith(suffix):
            return suffix
    return None


def _unit_base(path: str) -> str:
    leaf = path.split(".")[-1].lower()
    suffix = _unit_suffix(path)
    if suffix:
        leaf = leaf[: -len(suffix)]
    parent = ".".join(path.split(".")[:-1])
    return f"{parent}.{leaf}" if parent else leaf


def _values_equal(left: Any, right: Any) -> bool:
    if isinstance(left, list) and isinstance(right, list):
        return left == right
    return left == right


def _compare_exact(
    source: dict[str, Any],
    projected: dict[str, Any],
    path: str,
    code: str,
    message: str,
) -> list[dict[str, Any]]:
    left = _get_path(source, path)
    right = _get_path(projected, path)
    if left is MISSING and right is MISSING:
        return []
    if left is MISSING or right is MISSING or not _values_equal(left, right):
        return [_violation(code, message, path=path, details={"source": left, "projected": right})]
    return []


def _required_paths_for_event(event: dict[str, Any]) -> list[str]:
    event_type = _event_type(event)
    subtype = _event_subtype(event)
    paths = list(REQUIRED_ALWAYS)
    paths.extend(REQUIRED_BY_EVENT_TYPE.get(event_type or "", ()))
    if event_type == "COMMAND_EVENT":
        paths.extend(COMMAND_REQUIRED_BY_SUBTYPE.get(subtype or "", ()))
    if event_type == "SYSTEM_EVENT":
        paths.extend(SYSTEM_REQUIRED_BY_SUBTYPE.get(subtype or "", ()))
    return paths


def _check_required_fields(projected: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for path in _required_paths_for_event(projected):
        if _get_path(projected, path) is MISSING:
            out.append(
                _violation(
                    "PROJECTION_REQUIRED_FIELD_REMOVED",
                    "required projected field is missing",
                    path=path,
                )
            )
    return out


def _check_prohibited_fields(projected: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    event_type = _event_type(projected)
    payload = _payload(projected)
    if event_type == "STATE_EVENT":
        for key in sorted(STATE_PROHIBITED_PAYLOAD_FIELDS):
            if key in payload:
                out.append(
                    _violation(
                        "PROJECTION_PROHIBITED_FIELD_ADDED",
                        "STATE_EVENT projection contains a prohibited raw field",
                        path=f"payload.{key}",
                    )
                )
    if event_type == "COMMAND_EVENT":
        for path, key, _value in _walk(payload, "payload"):
            # strip()+casefold parity with the runtime semantic check
            # (gateway/src/validators.py _normalize_key), so padded or
            # case-varied copies of a denylisted name cannot slip past this
            # redundant defense-in-depth check either.
            key_lc = str(key).strip().casefold()
            if key_lc in COMMAND_ALTITUDE_KEYS or "altitude" in key_lc:
                out.append(
                    _violation(
                        "PROJECTION_PROHIBITED_FIELD_ADDED",
                        "COMMAND_EVENT projection contains an altitude-like field",
                        path=path,
                    )
                )
    return out


def _check_source_identity(source: dict[str, Any], projected: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for path in ("source.platform_id", "source.node_role", "source.producer"):
        out.extend(
            _compare_exact(
                source,
                projected,
                path,
                "PROJECTION_SOURCE_CHANGED",
                "source identity changed during projection",
            )
        )
    for path in ("source.sensor_id", "source.sw_version"):
        left = _get_path(source, path)
        right = _get_path(projected, path)
        if left is MISSING:
            continue
        if right is MISSING:
            continue
        if left != right:
            out.append(
                _violation(
                    "PROJECTION_SOURCE_REWRITTEN",
                    "optional source-authored field was rewritten instead of omitted",
                    path=path,
                    details={"source": left, "projected": right},
                )
            )
    return out


def _check_lineage(source: dict[str, Any], projected: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    event_type = _event_type(source)
    if event_type not in {"INFERENCE_EVENT", "FUSION_EVENT", "STATE_EVENT"}:
        return out
    source_lineage = _get_path(source, "lineage.based_on")
    projected_lineage = _get_path(projected, "lineage.based_on")
    if source_lineage is not MISSING and projected_lineage is MISSING:
        out.append(
            _violation(
                "PROJECTION_LINEAGE_REMOVED",
                "lineage.based_on was removed during projection",
                path="lineage.based_on",
            )
        )
    elif source_lineage is not MISSING and projected_lineage is not MISSING:
        if set(source_lineage) != set(projected_lineage):
            out.append(
                _violation(
                    "PROJECTION_LINEAGE_CHANGED",
                    "lineage.based_on changed during projection",
                    path="lineage.based_on",
                    details={"source": source_lineage, "projected": projected_lineage},
                )
            )
    source_transform = _get_path(source, "lineage.transform")
    projected_transform = _get_path(projected, "lineage.transform")
    if source_transform is not MISSING and projected_transform is MISSING:
        out.append(
            _violation(
                "PROJECTION_TRANSFORM_REMOVED",
                "lineage.transform was removed during projection",
                path="lineage.transform",
            )
        )
    elif source_transform is not MISSING and projected_transform != source_transform:
        out.append(
            _violation(
                "PROJECTION_LINEAGE_CHANGED",
                "lineage.transform changed during projection",
                path="lineage.transform",
                details={"source": source_transform, "projected": projected_transform},
            )
        )
    return out


def _check_confidence_and_ttl(source: dict[str, Any], projected: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    source_confidence = _get_path(source, "confidence")
    projected_confidence = _get_path(projected, "confidence")
    if source_confidence is not MISSING and projected_confidence is not MISSING:
        if float(projected_confidence) > float(source_confidence):
            out.append(
                _violation(
                    "PROJECTION_CONFIDENCE_INCREASE",
                    "projected confidence increased",
                    path="confidence",
                    details={"source": source_confidence, "projected": projected_confidence},
                )
            )
    source_ttl = _get_path(source, "payload.valid_for_ms")
    projected_ttl = _get_path(projected, "payload.valid_for_ms")
    if source_ttl is not MISSING and projected_ttl is not MISSING:
        if int(projected_ttl) > int(source_ttl):
            out.append(
                _violation(
                    "PROJECTION_TTL_INCREASE",
                    "projected valid_for_ms increased",
                    path="payload.valid_for_ms",
                    details={"source": source_ttl, "projected": projected_ttl},
                )
            )
    return out


def _check_precision_and_units(
    source: dict[str, Any],
    projected: dict[str, Any],
    catalog: dict[str, Any],
    target_profile: str,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    event_type = _event_type(source)
    source_flat = _flatten(source)
    projected_flat = _flatten(projected)
    projected_unit_bases: dict[str, list[str]] = {}
    for path in projected_flat:
        if _unit_suffix(path):
            projected_unit_bases.setdefault(_unit_base(path), []).append(path)

    for path, source_value in source_flat.items():
        if path in {"confidence", "payload.valid_for_ms"}:
            continue
        projected_value = projected_flat.get(path, MISSING)
        if projected_value is MISSING:
            suffix = _unit_suffix(path)
            if suffix:
                for projected_path in projected_unit_bases.get(_unit_base(path), []):
                    if projected_path != path:
                        out.append(
                            _violation(
                                "PROJECTION_UNIT_CHANGED",
                                "unit-suffixed field was renamed during projection",
                                path=projected_path,
                                details={"source_path": path, "projected_path": projected_path},
                            )
                        )
            continue

        if _catalog_is_precision_reducible(catalog, path, event_type, target_profile):
            if not _is_precision_projection_ok(source_value, projected_value):
                out.append(
                    _violation(
                        "PROJECTION_PRECISION_INCREASE",
                        "projected numeric field is more specific or not a coarser representation",
                        path=path,
                        details={"source": source_value, "projected": projected_value},
                    )
                )
                if _unit_suffix(path):
                    out.append(
                        _violation(
                            "PROJECTION_UNIT_CHANGED",
                            "unit-suffixed field appears silently rescaled",
                            path=path,
                            details={"source": source_value, "projected": projected_value},
                        )
                    )
        elif _unit_suffix(path) and projected_value != source_value:
            out.append(
                _violation(
                    "PROJECTION_UNIT_CHANGED",
                    "unit-suffixed field changed without a cataloged precision reduction rule",
                    path=path,
                    details={"source": source_value, "projected": projected_value},
                )
            )
    return out


def _check_catalog_equality(
    source: dict[str, Any],
    projected: dict[str, Any],
    catalog: dict[str, Any],
    target_profile: str,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    handled = {
        "zmeta_version",
        "event.event_id",
        "event.event_type",
        "event.event_subtype",
        "event.ts",
        "source.platform_id",
        "source.node_role",
        "source.producer",
        "lineage.based_on",
        "lineage.transform",
    }
    for path in _catalog_equality_rules(catalog, _event_type(source), target_profile):
        if not path or "*" in path or path in handled:
            continue
        left = _get_path(source, path)
        right = _get_path(projected, path)
        if left is MISSING or right is MISSING:
            continue
        if left != right:
            code = "PROJECTION_FIELD_CHANGED"
            if _unit_suffix(path):
                code = "PROJECTION_UNIT_CHANGED"
            out.append(
                _violation(
                    code,
                    "catalog equality field changed during projection",
                    path=path,
                    details={"source": left, "projected": right},
                )
            )
    return out


def _check_undeclared_omissions(
    source: dict[str, Any],
    projected: dict[str, Any],
    catalog: dict[str, Any],
    target_profile: str,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    event_type = _event_type(source)
    source_flat = _flatten(source)
    for path in sorted(source_flat):
        if path in {"profile", "event.t_receive", "event.t_publish"}:
            continue
        if path.startswith("profile."):
            continue
        if _get_path(projected, path) is not MISSING:
            continue
        if _catalog_allows_optional_omission(catalog, path, event_type, target_profile):
            continue
        if path in _required_paths_for_event(projected):
            continue
        if path in {"source.sensor_id", "source.sw_version"}:
            continue
        if path.startswith("lineage."):
            continue
        if path.startswith("payload.timing_quality") or path.startswith("payload.quality.timing_quality"):
            continue
        code = "PROJECTION_UNDECLARED_OPTIONAL_OMISSION"
        message = "source field was omitted without a catalog allowance"
        if path == "payload.extensions.risk_adjudication" or path.startswith(
            "payload.extensions.risk_adjudication."
        ):
            code = "PROJECTION_POLICY_RISK_LABEL_REMOVED"
            message = "policy risk adjudication labels were removed during projection"
        elif path.startswith("payload.extensions.external_promotion."):
            code = "PROJECTION_EXTERNAL_PROMOTION_EVIDENCE_REMOVED"
            message = "external promotion evidence was removed during projection"
        out.append(
            _violation(
                code,
                message,
                path=path,
            )
        )
    return out


def _check_timing_quality(
    source: dict[str, Any],
    projected: dict[str, Any],
    context: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    source_timing = _get_path(source, "payload.timing_quality")
    if source_timing is MISSING:
        source_timing = _get_path(source, "payload.quality.timing_quality")
    if source_timing is MISSING:
        return []
    projected_timing = _get_path(projected, "payload.timing_quality")
    if projected_timing is MISSING:
        projected_timing = _get_path(projected, "payload.quality.timing_quality")
    if projected_timing is not MISSING or _context_has_time_status(context):
        return []
    return [
        _violation(
            "PROJECTION_REQUIRED_FIELD_REMOVED",
            "projection removed timing quality without TIME_STATUS context",
            path="payload.timing_quality",
        )
    ]


def _roundtrip_projected(
    projected: dict[str, Any],
    fixture: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    roundtrips = fixture.get("roundtrip", [])
    if isinstance(roundtrips, str):
        roundtrips = [roundtrips]
    event = copy.deepcopy(projected)
    out: list[dict[str, Any]] = []
    for encoding in roundtrips:
        try:
            if encoding == "compact":
                event = zmeta_compact.loads(zmeta_compact.dumps(event))
            elif encoding in {"proto", "protobuf"}:
                event = zmeta_proto.loads(zmeta_proto.dumps(event))
            else:
                out.append(
                    _violation(
                        "PROJECTION_ENCODING_DECODE_INVALID",
                        "unsupported projection roundtrip encoding",
                        details={"encoding": encoding},
                    )
                )
        except Exception as exc:
            out.append(
                _violation(
                    "PROJECTION_ENCODING_DECODE_INVALID",
                    "projected event failed encoding roundtrip decode",
                    details={"encoding": encoding, "error": str(exc)},
                )
            )
    return event, out


def _compare_decoded_equivalence(projected: dict[str, Any], decoded: dict[str, Any]) -> list[dict[str, Any]]:
    if decoded == projected:
        return []
    return [
        _violation(
            "PROJECTION_ENCODING_DECODE_INVALID",
            "encoding roundtrip did not decode to the projected canonical JSON",
        )
    ]


def compare_projection(
    fixture: dict[str, Any],
    catalog: dict[str, Any],
    policy: dict[str, Any],
    schema_validator: Any,
) -> list[dict[str, Any]]:
    source = fixture.get("source")
    projected = fixture.get("projected")
    target_profile = str(fixture.get("target_profile") or "")
    source_profile = str(fixture.get("source_profile") or (source or {}).get("profile") or "H")
    context = _context_events(fixture)
    out: list[dict[str, Any]] = []

    if not isinstance(source, dict):
        return [
            _violation(
                "PROJECTION_SCHEMA_INVALID_SOURCE",
                "fixture source must be a ZMeta event object",
            )
        ]
    if target_profile not in policy.get("profiles", {}):
        out.append(
            _violation(
                "PROJECTION_PROFILE_ILLEGAL_EVENT",
                "fixture target_profile is not configured",
                details={"target_profile": target_profile},
            )
        )

    out.extend(_policy_checks(source, source_profile, policy, schema_validator, context, source_label="source"))

    source_type = _event_type(source)
    allowed_types = _allowed_event_types(policy, target_profile)
    if projected is None:
        if source_type not in allowed_types and fixture.get("allowed_omission_reason"):
            return out
        out.append(
            _violation(
                "PROJECTION_PROFILE_ILLEGAL_EVENT",
                "projected event is null without a target-profile omission allowance",
                details={"source_event_type": source_type, "target_profile": target_profile},
            )
        )
        return out

    if not isinstance(projected, dict):
        out.append(
            _violation(
                "PROJECTION_SCHEMA_INVALID_PROJECTED",
                "fixture projected value must be an event object or null",
            )
        )
        return out

    decoded_projected, roundtrip_violations = _roundtrip_projected(projected, fixture)
    out.extend(roundtrip_violations)
    out.extend(_compare_decoded_equivalence(projected, decoded_projected))
    projected_for_checks = decoded_projected

    out.extend(
        _policy_checks(
            projected_for_checks,
            target_profile,
            policy,
            schema_validator,
            context,
            source_label="projected",
        )
    )

    out.extend(
        _compare_exact(
            source,
            projected_for_checks,
            "zmeta_version",
            "PROJECTION_VERSION_CHANGED",
            "zmeta_version changed during projection",
        )
    )
    out.extend(
        _compare_exact(
            source,
            projected_for_checks,
            "event.event_id",
            "PROJECTION_EVENT_ID_CHANGED",
            "event_id changed during same-event projection",
        )
    )

    if _event_type(source) != _event_type(projected_for_checks):
        if _event_type(projected_for_checks) == "STATE_EVENT" and _event_type(source) in {
            "OBSERVATION_EVENT",
            "INFERENCE_EVENT",
        }:
            out.append(
                _violation(
                    "PROJECTION_SEMANTIC_LAYER_COLLAPSE",
                    "observation/inference was rewritten into state with the same event identity",
                    path="event.event_type",
                    details={"source": _event_type(source), "projected": _event_type(projected_for_checks)},
                )
            )
        out.append(
            _violation(
                "PROJECTION_EVENT_TYPE_CHANGED",
                "event_type changed during projection",
                path="event.event_type",
                details={"source": _event_type(source), "projected": _event_type(projected_for_checks)},
            )
        )

    if _event_subtype(source) != _event_subtype(projected_for_checks):
        out.append(
            _violation(
                "PROJECTION_EVENT_SUBTYPE_CHANGED",
                "event_subtype changed during projection",
                path="event.event_subtype",
                details={"source": _event_subtype(source), "projected": _event_subtype(projected_for_checks)},
            )
        )

    out.extend(
        _compare_exact(
            source,
            projected_for_checks,
            "event.ts",
            "PROJECTION_EVENT_TS_CHANGED",
            "event.ts changed during projection",
        )
    )

    out.extend(_check_source_identity(source, projected_for_checks))

    if _event_type(source) in {"STATE_EVENT", "FUSION_EVENT"}:
        out.extend(
            _compare_exact(
                source,
                projected_for_checks,
                "payload.track_id",
                "PROJECTION_TRACK_ID_CHANGED",
                "track_id changed during projection",
            )
        )

    out.extend(_check_lineage(source, projected_for_checks))
    out.extend(_check_confidence_and_ttl(source, projected_for_checks))
    out.extend(_check_required_fields(projected_for_checks))
    out.extend(_check_prohibited_fields(projected_for_checks))
    out.extend(_check_timing_quality(source, projected_for_checks, context))
    out.extend(_check_precision_and_units(source, projected_for_checks, catalog, target_profile))
    out.extend(_check_catalog_equality(source, projected_for_checks, catalog, target_profile))
    out.extend(_check_undeclared_omissions(source, projected_for_checks, catalog, target_profile))
    return _dedupe_violations(out)


def _dedupe_violations(violations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    out = []
    for violation in violations:
        key = (violation.get("code"), violation.get("path"), json.dumps(violation.get("details", {}), sort_keys=True, default=str))
        if key in seen:
            continue
        seen.add(key)
        out.append(violation)
    return out


def _case_label(item: dict[str, Any], line_no: int) -> str:
    return str(item.get("name") or item.get("case_id") or f"line-{line_no}")


def run_suite(
    *,
    catalog_path: str | Path,
    must_pass_path: str | Path,
    must_fail_path: str | Path,
    quiet: bool = False,
) -> int:
    catalog = load_catalog(catalog_path)
    schema_validator = validators.load_schema(ROOT / "schema" / "zmeta-event.schema.json")
    policy = validators.load_policy(ROOT / "policy")

    failures = 0
    passed = 0
    expected_failures = 0
    must_pass_total = 0
    must_fail_total = 0

    for line_no, item in iter_jsonl(must_pass_path) or []:
        must_pass_total += 1
        label = _case_label(item, line_no)
        violations = compare_projection(item, catalog, policy, schema_validator)
        if violations:
            failures += 1
            codes = ",".join(violation["code"] for violation in violations)
            print(f"FAIL must-pass name={label} codes={codes}")
            for violation in violations:
                print(f"  {violation['code']}: {violation['message']}")
        else:
            passed += 1
            if not quiet:
                print(f"PASS must-pass name={label}")

    for line_no, item in iter_jsonl(must_fail_path) or []:
        must_fail_total += 1
        label = _case_label(item, line_no)
        expected = item.get("expect_code")
        violations = compare_projection(item, catalog, policy, schema_validator)
        codes = [violation["code"] for violation in violations]
        if not expected:
            failures += 1
            print(f"FAIL must-fail name={label} missing expect_code")
        elif expected not in codes:
            failures += 1
            code_str = ",".join(codes) or "none"
            print(f"FAIL must-fail name={label} expected={expected} got={code_str}")
            for violation in violations:
                print(f"  {violation['code']}: {violation['message']}")
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
        print(f"projection conformance failed total={total} failures={failures}")
        return 1
    print(f"projection conformance ok total={total}")
    return 0


def main() -> None:
    args = parse_args()
    raise SystemExit(
        run_suite(
            catalog_path=args.catalog,
            must_pass_path=args.must_pass,
            must_fail_path=args.must_fail,
            quiet=args.quiet,
        )
    )


if __name__ == "__main__":
    main()
