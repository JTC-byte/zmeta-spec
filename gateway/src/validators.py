import json
import math
from fnmatch import fnmatchcase
from datetime import datetime, timezone
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012


class ValidationState:
    def __init__(self):
        self.timing_sources = set()
        self.latest_timing = {}
        self.events = {}
        self.event_ids = set()
        self.command_task_ids = set()
        self.task_ack_keys = set()

    def has_timing(self, event):
        return self.get_timing(event)[1] is not None

    def get_timing(self, event):
        for key in _source_keys(event):
            if key in self.latest_timing:
                return key, self.latest_timing[key]
        return None, None

    def record(self, event):
        self.record_timing(event)
        event_block = event.get("event", {}) if isinstance(event, dict) else {}
        payload = event.get("payload", {}) if isinstance(event, dict) else {}
        event_type = event_block.get("event_type")
        system_type = payload.get("system_type") if isinstance(payload, dict) else None
        event_id = event_block.get("event_id")
        if event_id:
            self.event_ids.add(event_id)
            self.events[event_id] = {
                "event_type": event_type,
                "event_subtype": event_block.get("event_subtype"),
                "event": event,
            }
        if event_type == "COMMAND_EVENT" and isinstance(payload, dict):
            task_id = payload.get("task_id")
            if task_id:
                self.command_task_ids.add(task_id)
        if event_type == "SYSTEM_EVENT" and system_type == "TASK_ACK" and isinstance(payload, dict):
            metrics = payload.get("metrics", {})
            if isinstance(metrics, dict):
                key = (metrics.get("task_id"), metrics.get("original_event_id"), payload.get("state"))
                if all(key):
                    self.task_ack_keys.add(key)

    def get_event(self, event_id):
        return self.events.get(event_id)

    def record_timing(self, event):
        event_block = event.get("event", {}) if isinstance(event, dict) else {}
        payload = event.get("payload", {}) if isinstance(event, dict) else {}
        event_type = event_block.get("event_type")
        system_type = payload.get("system_type") if isinstance(payload, dict) else None
        if event_type == "SYSTEM_EVENT" and system_type == "TIME_STATUS":
            metrics = payload.get("metrics", {}) if isinstance(payload, dict) else {}
            if isinstance(metrics, dict):
                status = dict(metrics)
                status["_event_ts"] = event_block.get("ts")
                for key in _source_keys(event):
                    self.timing_sources.add(key)
                    current = self.latest_timing.get(key)
                    if _should_replace_timing_status(current, status):
                        self.latest_timing[key] = dict(status)


def load_schema(schema_path):
    schema_path = Path(schema_path)
    with open(schema_path, "r", encoding="utf-8") as handle:
        schema = json.load(handle)

    resources = []
    for candidate in sorted(schema_path.parent.glob("*.schema.json")):
        try:
            with open(candidate, "r", encoding="utf-8") as handle:
                candidate_schema = json.load(handle)
        except json.JSONDecodeError:
            continue
        schema_id = candidate_schema.get("$id")
        if schema_id:
            resources.append(
                (
                    schema_id,
                    Resource.from_contents(candidate_schema, default_specification=DRAFT202012),
                )
            )

    registry = Registry().with_resources(resources)
    return Draft202012Validator(schema, registry=registry, format_checker=FormatChecker())


def load_yaml(path):
    with open(path, "r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    return data or {}


def load_policy(policy_dir):
    policy_dir = Path(policy_dir)
    roles_cfg = load_yaml(policy_dir / "roles.yaml")
    profiles_cfg = load_yaml(policy_dir / "profiles.yaml")
    semantics_cfg = load_yaml(policy_dir / "semantics.yaml")
    routing_cfg = load_yaml(policy_dir / "routing.yaml")
    producer_authority_path = policy_dir / "producer-authority.yaml"
    producer_authority_cfg = (
        load_yaml(producer_authority_path) if producer_authority_path.exists() else {}
    )
    lineage_path = policy_dir / "lineage.yaml"
    lineage_cfg = load_yaml(lineage_path) if lineage_path.exists() else {}
    timing_freshness_path = policy_dir / "timing-freshness.yaml"
    timing_freshness_cfg = (
        load_yaml(timing_freshness_path) if timing_freshness_path.exists() else {}
    )
    codes_cfg = load_yaml(policy_dir / "violation-codes.yaml")
    severity_map = {}
    for item in codes_cfg.get("violation_codes", []):
        if isinstance(item, dict) and "code" in item:
            severity_map[item["code"]] = item.get("severity", "fail")

    return {
        "roles": roles_cfg.get("roles", {}),
        "deny": roles_cfg.get("deny", []),
        "profiles": profiles_cfg.get("profiles", {}),
        "semantics": semantics_cfg.get("semantics", {}),
        "routing": routing_cfg.get("routing", {}),
        "producer_authority": producer_authority_cfg.get("producer_authority", producer_authority_cfg),
        "lineage": lineage_cfg.get("lineage", lineage_cfg),
        "timing_freshness": timing_freshness_cfg.get("timing_freshness", timing_freshness_cfg),
        "violation_codes": codes_cfg.get("violation_codes", []),
        "violation_severities": severity_map,
    }


def _resolve_severity(code, severity_map):
    if not severity_map:
        return "fail"
    return severity_map.get(code, "fail")


def _violation(code, message, details=None, severity_map=None, severity=None):
    return {
        "code": code,
        "message": message,
        "severity": severity or _resolve_severity(code, severity_map),
        "details": details or {},
    }


_POLICY_DECISION_BY_MODE = {
    "reject": "REJECTED",
    "warn": "WARN_ACCEPT",
    "degrade": "DEGRADED_ACCEPT",
    "quarantine": "QUARANTINE_ACCEPT",
    "ignore": "IGNORED",
}


def _policy_decision_for_mode(mode):
    return _POLICY_DECISION_BY_MODE.get(str(mode or "").strip().lower(), "REJECTED")


def _risk_use_limits(policy, mode):
    if not isinstance(policy, dict):
        return {}
    configured = policy.get("use_limits", {})
    if not isinstance(configured, dict):
        return {}
    limits = configured.get(str(mode or "").strip().lower(), {})
    return limits if isinstance(limits, dict) else {}


def _risk_details(
    details,
    risk_dimension,
    mode,
    policy=None,
    policy_ref=None,
    policy_decision=None,
):
    result = dict(details or {})
    mode = str(mode or "reject").strip().lower()
    result["risk_dimension"] = risk_dimension
    result["policy_mode"] = mode
    result["policy_decision"] = policy_decision or _policy_decision_for_mode(mode)
    if policy_ref:
        result["policy_ref"] = policy_ref

    limits = _risk_use_limits(policy, mode)
    for key in ("allowed_uses", "prohibited_uses"):
        if key in result:
            continue
        values = _list_values(limits.get(key))
        if values:
            result[key] = values
    return result


def _append_risk_adjudication(event, violation, effects=None):
    if not isinstance(event, dict) or not isinstance(violation, dict):
        return False
    payload = event.get("payload")
    if not isinstance(payload, dict):
        return False
    details = violation.get("details", {})
    if not isinstance(details, dict):
        return False
    risk_dimension = details.get("risk_dimension")
    policy_decision = details.get("policy_decision")
    if not risk_dimension or not policy_decision:
        return False

    extensions = payload.get("extensions")
    if not isinstance(extensions, dict):
        extensions = {}
        payload["extensions"] = extensions
    records = extensions.get("risk_adjudication")
    if not isinstance(records, list):
        records = []
        extensions["risk_adjudication"] = records

    record = {
        "risk_dimension": risk_dimension,
        "reason_code": violation.get("code"),
        "policy_mode": details.get("policy_mode"),
        "policy_decision": policy_decision,
    }
    for key in (
        "policy_ref",
        "profile",
        "producer",
        "event_type",
        "event_subtype",
        "allowed_uses",
        "prohibited_uses",
    ):
        value = details.get(key)
        if value is not None:
            record[key] = value
    configured_effects = details.get("effects")
    if isinstance(configured_effects, dict):
        record["effects"] = dict(configured_effects)
    if isinstance(effects, dict):
        record["effects"] = {**record.get("effects", {}), **effects}

    records.append(record)
    return True


def _source_keys(event):
    source = event.get("source", {}) if isinstance(event, dict) else {}
    platform_id = str(source.get("platform_id") or "UNKNOWN")
    producer = str(source.get("producer") or "UNKNOWN")
    sensor_id = source.get("sensor_id")
    node_role = source.get("node_role")

    keys = []
    if sensor_id:
        keys.append((platform_id, producer, str(sensor_id)))
    keys.append((platform_id, producer))
    if node_role:
        # Legacy compatibility for existing gateway failure-mode lookups.
        keys.append((platform_id, producer, str(node_role)))

    unique = []
    for key in keys:
        if key not in unique:
            unique.append(key)
    return unique


def _source_key(event):
    return _source_keys(event)[0]


def _resolve_path(value, dotted_path):
    target = value
    for part in str(dotted_path).split("."):
        if not part:
            continue
        if not isinstance(target, dict):
            return None
        target = target.get(part)
    return target


def _normalize_key(value):
    # Normalize a key for denylist comparison: strip surrounding whitespace and
    # casefold, so whitespace- or case-padded copies of a reserved name (e.g.
    # "features ", "\tRAW_FEATURES") cannot slip past the semantic denylist that
    # the schema pins only for the exact bytes. Both the payload key and the
    # forbidden set are normalized the same way for a symmetric compare.
    return str(value).strip().casefold()


def _find_forbidden_key(value, forbidden_keys):
    if isinstance(value, dict):
        for key, item in value.items():
            key_str = str(key)
            if _normalize_key(key_str) in forbidden_keys:
                return key_str, [key_str]
            found = _find_forbidden_key(item, forbidden_keys)
            if found:
                found_key, path = found
                return found_key, [key_str] + path
    elif isinstance(value, list):
        for idx, item in enumerate(value):
            found = _find_forbidden_key(item, forbidden_keys)
            if found:
                found_key, path = found
                return found_key, [str(idx)] + path
    return None


def _parse_utc_z(value):
    if not isinstance(value, str) or not value.endswith("Z"):
        return None
    try:
        return datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return None


def _format_utc_z(value):
    if not isinstance(value, datetime):
        return None
    value = value.astimezone(timezone.utc)
    if value.microsecond:
        text = value.isoformat(timespec="milliseconds")
    else:
        text = value.isoformat(timespec="seconds")
    return text.replace("+00:00", "Z")


def _should_replace_timing_status(current, new_status):
    if not isinstance(current, dict):
        return True
    current_ts = _parse_utc_z(current.get("_event_ts"))
    new_ts = _parse_utc_z(new_status.get("_event_ts"))
    if current_ts is None or new_ts is None:
        return True
    return new_ts >= current_ts


def _profile_for_event(event, profile=None):
    if profile:
        return str(profile)
    event_profile = event.get("profile") if isinstance(event, dict) else None
    return str(event_profile or "H")


def _timing_freshness_enabled(policy):
    return isinstance(policy, dict) and policy.get("enabled", True) is not False


def _timing_mode(policy, reason, profile=None):
    if not isinstance(policy, dict):
        return "reject"
    mode = None
    if profile:
        for key in (f"{reason}_mode_by_profile", "mode_by_profile"):
            configured = policy.get(key)
            if isinstance(configured, dict) and profile in configured:
                mode = configured.get(profile)
                break
    if mode is None:
        mode = policy.get(f"{reason}_mode", policy.get("mode", "reject"))
    mode = str(mode or "reject").strip().lower()
    if mode not in {"warn", "degrade", "reject"}:
        return "reject"
    return mode


def _timing_mode_severity(mode):
    return "fail" if mode == "reject" else "warn"


def _max_timing_status_age_ms(policy, profile):
    defaults = {"L": 60000, "M": 30000, "H": 10000}
    configured = policy.get("max_timing_status_age_ms", {}) if isinstance(policy, dict) else {}
    if not isinstance(configured, dict):
        configured = {}
    raw = configured.get(profile, defaults.get(profile, defaults["H"]))
    try:
        value = int(raw)
    except (TypeError, ValueError):
        value = defaults.get(profile, defaults["H"])
    return max(0, value)


def _max_negative_timing_status_age_ms(policy, profile):
    defaults = {"L": 5000, "M": 2000, "H": 1000}
    configured = policy.get("max_negative_age_ms", {}) if isinstance(policy, dict) else {}
    if isinstance(configured, dict):
        raw = configured.get(profile, defaults.get(profile, defaults["H"]))
    else:
        raw = configured
    try:
        value = int(raw)
    except (TypeError, ValueError):
        value = defaults.get(profile, defaults["H"])
    return max(0, value)


_TIMING_DEGRADABLE_CODES = {
    "TIMING_STATUS_MISSING",
    "TIMING_STATUS_STALE",
    "TIMING_STATUS_AGE_NEGATIVE",
}


def _timing_policy_violation(
    code,
    message,
    mode,
    details,
    timing_freshness_policy=None,
    severity_map=None,
):
    details = _risk_details(
        details,
        "timing",
        mode,
        policy=timing_freshness_policy,
        policy_ref="policy/timing-freshness.yaml",
    )
    if mode == "degrade":
        details["action"] = "degrade"
        degradation = (
            timing_freshness_policy.get("degrade", {})
            if isinstance(timing_freshness_policy, dict)
            else {}
        )
        if not isinstance(degradation, dict):
            degradation = {}
        try:
            factor = float(degradation.get("confidence_reduction_factor", 2.0))
        except (TypeError, ValueError):
            factor = 2.0
        if factor <= 0:
            factor = 2.0
        details["effects"] = {"confidence_reduction_factor": factor}
    return _violation(
        code,
        message,
        details=details,
        severity_map=severity_map,
        severity=_timing_mode_severity(mode),
    )


def apply_timing_freshness_degradation(event, violations, timing_freshness_policy):
    if not isinstance(event, dict) or not isinstance(timing_freshness_policy, dict):
        return False
    if not any(
        violation.get("details", {}).get("action") == "degrade"
        and violation.get("code") in _TIMING_DEGRADABLE_CODES
        for violation in violations or []
    ):
        return False

    degradation = timing_freshness_policy.get("degrade", {})
    if not isinstance(degradation, dict):
        degradation = {}
    try:
        factor = float(degradation.get("confidence_reduction_factor", 2.0))
    except (TypeError, ValueError):
        factor = 2.0
    if factor <= 0:
        factor = 2.0

    confidence = event.get("confidence")
    if not isinstance(confidence, (int, float)):
        return False
    event["confidence"] = max(0.0, min(1.0, confidence / factor))
    changed = True
    for violation in violations or []:
        if (
            violation.get("details", {}).get("action") == "degrade"
            and violation.get("code") in _TIMING_DEGRADABLE_CODES
        ):
            changed = _append_risk_adjudication(
                event, violation, {"confidence_reduction_factor": factor}
            ) or changed
    return changed


def _normalize_pattern(value):
    return str(value or "").strip().lower()


def _matches_pattern(value, pattern):
    value_lc = _normalize_pattern(value)
    pattern_lc = _normalize_pattern(pattern)
    return bool(value_lc and pattern_lc and fnmatchcase(value_lc, pattern_lc))


def _matching_producer_rules(producer, producer_rules):
    if not isinstance(producer_rules, dict):
        return []
    matches = []
    for pattern, rule in producer_rules.items():
        if _matches_pattern(producer, pattern):
            matches.append((str(pattern), rule))
    return matches


def _list_values(value):
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _is_blank(value):
    return value is None or value == "" or value == []


def _external_promotion_rules(matching_rules):
    rules = []
    for pattern, rule in matching_rules:
        if not isinstance(rule, dict):
            continue
        cfg = rule.get("external_state_promotion")
        if not isinstance(cfg, dict) or cfg.get("required", False) is not True:
            continue
        rules.append((pattern, cfg))
    return rules


def _union_rule_values(rules, key):
    values = set()
    for _pattern, cfg in rules:
        values.update(_list_values(cfg.get(key)))
    return values


_PROMOTION_MODES = {"reject", "warn", "quarantine", "degrade"}


def _normalize_promotion_mode(value, default="reject"):
    mode = str(value or default).strip().lower()
    if mode not in _PROMOTION_MODES:
        return default
    return mode


def _promotion_mode(global_cfg, promotion_rules, profile):
    if not isinstance(global_cfg, dict):
        return "reject"

    mode = global_cfg.get("mode", "reject")
    by_profile = global_cfg.get("mode_by_profile")
    if isinstance(by_profile, dict):
        mode = by_profile.get(profile, by_profile.get("default", mode))

    for _pattern, cfg in promotion_rules or []:
        if not isinstance(cfg, dict):
            continue
        rule_mode = cfg.get("mode")
        rule_by_profile = cfg.get("mode_by_profile")
        if isinstance(rule_by_profile, dict):
            rule_mode = rule_by_profile.get(profile, rule_by_profile.get("default", rule_mode))
        if rule_mode is not None:
            mode = rule_mode

    return _normalize_promotion_mode(mode)


def _promotion_mode_severity(mode):
    return "fail" if mode == "reject" else "warn"


def _promotion_violation(message, details=None, severity_map=None):
    details = dict(details or {})
    mode = _normalize_promotion_mode(details.get("policy_mode"), default="reject")
    details = _risk_details(
        details,
        "external_promotion",
        mode,
        policy_ref="policy/producer-authority.yaml#external_state_promotion",
    )
    if mode in {"degrade", "quarantine"}:
        details["action"] = mode
    return _violation(
        "PRODUCER_NOT_ALLOWED",
        message,
        details=details,
        severity_map=severity_map,
        severity=_promotion_mode_severity(mode),
    )


def _positive_float(value, default):
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    if parsed <= 0:
        return default
    return parsed


def _bounded_float(value, default, low=0.0, high=1.0):
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        parsed = default
    return max(low, min(high, parsed))


def _non_negative_int(value, default):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return max(0, parsed)


def _ensure_path_dict(value, dotted_path):
    if not isinstance(value, dict):
        return None
    target = value
    parts = [part for part in str(dotted_path).split(".") if part]
    for part in parts:
        if not isinstance(target, dict):
            return None
        child = target.get(part)
        if not isinstance(child, dict):
            child = {}
            target[part] = child
        target = child
    return target


def _reduce_confidence(event, factor):
    confidence = event.get("confidence") if isinstance(event, dict) else None
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
        return False
    event["confidence"] = max(0.0, min(1.0, float(confidence) / factor))
    return True


def _cap_confidence(event, cap):
    confidence = event.get("confidence") if isinstance(event, dict) else None
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
        return False
    event["confidence"] = max(0.0, min(1.0, min(float(confidence), cap)))
    return True


def _reduce_valid_for_ms(event, factor):
    payload = event.get("payload", {}) if isinstance(event, dict) else {}
    if not isinstance(payload, dict):
        return False
    value = payload.get("valid_for_ms")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    payload["valid_for_ms"] = max(1, int(float(value) / factor))
    return True


def _cap_valid_for_ms(event, cap):
    payload = event.get("payload", {}) if isinstance(event, dict) else {}
    if not isinstance(payload, dict):
        return False
    value = payload.get("valid_for_ms")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    payload["valid_for_ms"] = max(0, int(min(float(value), cap)))
    return True


def apply_external_promotion_policy_action(event, violations, authority_policy):
    if not isinstance(event, dict) or not isinstance(authority_policy, dict):
        return False
    global_cfg = authority_policy.get("external_state_promotion", {})
    if not isinstance(global_cfg, dict):
        global_cfg = {}

    metadata_path = global_cfg.get("metadata_path", "payload.extensions.external_promotion")
    changed = False
    for violation in violations or []:
        if violation.get("code") != "PRODUCER_NOT_ALLOWED":
            continue
        details = violation.get("details", {})
        action = details.get("action") if isinstance(details, dict) else None
        if action not in {"degrade", "quarantine"}:
            continue

        metadata = _ensure_path_dict(event, metadata_path)
        if metadata is not None:
            metadata["policy_mode"] = action
            metadata["policy_reason_code"] = violation.get("code")
            metadata["policy_decision"] = _policy_decision_for_mode(action)
            changed = True

        if action == "degrade":
            degrade_cfg = global_cfg.get("degrade", {})
            if not isinstance(degrade_cfg, dict):
                degrade_cfg = {}
            confidence_factor = _positive_float(
                degrade_cfg.get("confidence_reduction_factor"), 2.0
            )
            valid_for_factor = _positive_float(
                degrade_cfg.get("valid_for_ms_reduction_factor"), confidence_factor
            )
            changed = _reduce_confidence(event, confidence_factor) or changed
            changed = _reduce_valid_for_ms(event, valid_for_factor) or changed
            changed = _append_risk_adjudication(
                event,
                violation,
                {
                    "confidence_reduction_factor": confidence_factor,
                    "valid_for_ms_reduction_factor": valid_for_factor,
                },
            ) or changed
            continue

        quarantine_cfg = global_cfg.get("quarantine", {})
        if not isinstance(quarantine_cfg, dict):
            quarantine_cfg = {}
        confidence_cap = _bounded_float(quarantine_cfg.get("confidence_cap"), 0.25)
        valid_for_cap = _non_negative_int(quarantine_cfg.get("valid_for_ms_cap"), 1000)
        changed = _cap_confidence(event, confidence_cap) or changed
        changed = _cap_valid_for_ms(event, valid_for_cap) or changed
        changed = _append_risk_adjudication(
            event,
            violation,
            {
                "confidence_cap": confidence_cap,
                "valid_for_ms_cap": valid_for_cap,
            },
        ) or changed

    return changed


def _validate_external_state_promotion(
    event,
    authority_policy,
    promotion_rules,
    matched_patterns,
    severity_map=None,
):
    if not promotion_rules:
        return None

    event_block = event.get("event", {}) if isinstance(event, dict) else {}
    event_type = event_block.get("event_type")
    if event_type != "STATE_EVENT":
        return None

    global_cfg = authority_policy.get("external_state_promotion", {})
    if not isinstance(global_cfg, dict) or global_cfg.get("enabled", True) is False:
        return None

    source = event.get("source", {}) if isinstance(event, dict) else {}
    producer = (source.get("producer") or "").strip()
    profile = _profile_for_event(event)
    mode = _promotion_mode(global_cfg, promotion_rules, profile)
    metadata_path = global_cfg.get("metadata_path", "payload.extensions.external_promotion")
    metadata = _resolve_path(event, metadata_path)
    details = _risk_details(
        {
            "event_type": event_type,
            "producer": producer,
            "profile": profile,
            "matched_patterns": matched_patterns,
            "metadata_path": metadata_path,
            "policy_mode": mode,
        },
        "external_promotion",
        mode,
        policy=global_cfg,
        policy_ref="policy/producer-authority.yaml#external_state_promotion",
    )

    if not isinstance(metadata, dict):
        return _promotion_violation(
            "external STATE_EVENT promotion metadata missing",
            details=details,
            severity_map=severity_map,
        )

    required_by_profile = global_cfg.get("required_fields_by_profile", {})
    if not isinstance(required_by_profile, dict):
        required_by_profile = {}
    required_fields = _list_values(
        required_by_profile.get(profile, required_by_profile.get("default", []))
    )
    missing = [field for field in required_fields if _is_blank(metadata.get(field))]
    if missing:
        return _promotion_violation(
            "external STATE_EVENT promotion metadata missing required fields",
            details={**details, "missing": missing},
            severity_map=severity_map,
        )

    expected_category = global_cfg.get("required_state_category")
    if expected_category and metadata.get("state_category") != expected_category:
        return _promotion_violation(
            "external STATE_EVENT promotion category is not allowed",
            details={
                **details,
                "state_category": metadata.get("state_category"),
                "required_state_category": expected_category,
            },
            severity_map=severity_map,
        )

    allowed_origin_kinds = set(_list_values(global_cfg.get("allowed_origin_kinds")))
    origin_kind = metadata.get("origin_kind")
    if origin_kind is not None and allowed_origin_kinds and origin_kind not in allowed_origin_kinds:
        return _promotion_violation(
            "external STATE_EVENT promotion origin kind is not allowed",
            details={**details, "origin_kind": origin_kind, "allowed_origin_kinds": sorted(allowed_origin_kinds)},
            severity_map=severity_map,
        )

    lineage_by_profile = global_cfg.get("allowed_lineage_status_by_profile", {})
    if not isinstance(lineage_by_profile, dict):
        lineage_by_profile = {}
    allowed_lineage_status = set(
        _list_values(lineage_by_profile.get(profile, lineage_by_profile.get("default", [])))
    )
    lineage_status = metadata.get("lineage_status")
    if lineage_status is not None and allowed_lineage_status and lineage_status not in allowed_lineage_status:
        return _promotion_violation(
            "external STATE_EVENT promotion lineage status is not allowed for profile",
            details={
                **details,
                "lineage_status": lineage_status,
                "allowed_lineage_status": sorted(allowed_lineage_status),
            },
            severity_map=severity_map,
        )

    source_uid_statuses = set(_list_values(global_cfg.get("source_event_uid_required_statuses")))
    if lineage_status in source_uid_statuses and _is_blank(metadata.get("source_event_uid")):
        return _promotion_violation(
            "external STATE_EVENT promotion requires source event identity",
            details={**details, "lineage_status": lineage_status, "missing": ["source_event_uid"]},
            severity_map=severity_map,
        )

    trust_ref = metadata.get("trust_ref")
    trust_prefixes = _list_values(global_cfg.get("required_trust_ref_prefixes"))
    if trust_ref is not None and trust_prefixes:
        trust_ref_text = str(trust_ref)
        if not any(trust_ref_text.startswith(prefix) for prefix in trust_prefixes):
            return _promotion_violation(
                "external STATE_EVENT promotion trust reference is not allowed",
                details={**details, "trust_ref": trust_ref, "required_prefixes": trust_prefixes},
                severity_map=severity_map,
            )

    current_event_id = event_block.get("event_id")
    lineage_ids = set(_lineage_based_on(event))
    source_zmeta_event_id = metadata.get("source_zmeta_event_id")
    loop_status = metadata.get("loop_status")
    loop_risk_statuses = set(_list_values(global_cfg.get("loop_risk_statuses")))
    if (
        loop_status in loop_risk_statuses
        or (source_zmeta_event_id and source_zmeta_event_id == current_event_id)
        or (current_event_id and current_event_id in lineage_ids)
    ):
        loop_mode = mode
        if global_cfg.get("always_reject_loop_risk", True) is not False:
            loop_mode = "reject"
        loop_details_source = {
            key: value
            for key, value in details.items()
            if key not in {"allowed_uses", "prohibited_uses", "policy_decision"}
        }
        return _promotion_violation(
            "external STATE_EVENT promotion has loop/reflection risk",
            details=_risk_details(
                {
                    **loop_details_source,
                    "policy_mode": loop_mode,
                    "loop_status": loop_status,
                    "source_zmeta_event_id": source_zmeta_event_id,
                    "event_id": current_event_id,
                },
                "external_promotion",
                loop_mode,
                policy=global_cfg,
                policy_ref="policy/producer-authority.yaml#external_state_promotion",
            ),
            severity_map=severity_map,
        )

    allowed_loop_statuses = set(_list_values(global_cfg.get("allowed_loop_statuses")))
    if loop_status is not None and allowed_loop_statuses and loop_status not in allowed_loop_statuses:
        return _promotion_violation(
            "external STATE_EVENT promotion loop status is not allowed",
            details={**details, "loop_status": loop_status, "allowed_loop_statuses": sorted(allowed_loop_statuses)},
            severity_map=severity_map,
        )

    transform = event.get("lineage", {}).get("transform") if isinstance(event.get("lineage"), dict) else None
    transform_prefixes = _list_values(global_cfg.get("required_lineage_transform_prefixes"))
    if transform_prefixes and not any(str(transform or "").startswith(prefix) for prefix in transform_prefixes):
        return _promotion_violation(
            "external STATE_EVENT promotion lineage transform is not a promotion transform",
            details={**details, "transform": transform, "required_prefixes": transform_prefixes},
            severity_map=severity_map,
        )

    policy_id = metadata.get("promotion_policy_id")
    approved_policy_ids = _union_rule_values(promotion_rules, "approved_policy_ids")
    if policy_id is not None and approved_policy_ids and policy_id not in approved_policy_ids:
        return _promotion_violation(
            "external STATE_EVENT promotion policy is not approved for producer",
            details={**details, "promotion_policy_id": policy_id, "approved_policy_ids": sorted(approved_policy_ids)},
            severity_map=severity_map,
        )

    projection_id = metadata.get("projection_id")
    allowed_projection_ids = _union_rule_values(promotion_rules, "allowed_projection_ids")
    if projection_id is not None and allowed_projection_ids and projection_id not in allowed_projection_ids:
        return _promotion_violation(
            "external STATE_EVENT projection id is not approved for producer",
            details={**details, "projection_id": projection_id, "allowed_projection_ids": sorted(allowed_projection_ids)},
            severity_map=severity_map,
        )

    confidence_basis = metadata.get("confidence_basis")
    allowed_confidence_basis = _union_rule_values(promotion_rules, "allowed_confidence_basis")
    if confidence_basis is not None and allowed_confidence_basis and confidence_basis not in allowed_confidence_basis:
        return _promotion_violation(
            "external STATE_EVENT confidence basis is not approved for producer",
            details={
                **details,
                "confidence_basis": confidence_basis,
                "allowed_confidence_basis": sorted(allowed_confidence_basis),
            },
            severity_map=severity_map,
        )

    freshness_ms = metadata.get("freshness_ms")
    if freshness_ms is not None:
        try:
            freshness_value = float(freshness_ms)
        except (TypeError, ValueError):
            return _promotion_violation(
                "external STATE_EVENT promotion freshness is not numeric",
                details={**details, "freshness_ms": freshness_ms},
                severity_map=severity_map,
            )
        if freshness_value < 0:
            return _promotion_violation(
                "external STATE_EVENT promotion freshness is negative",
                details={**details, "freshness_ms": freshness_ms},
                severity_map=severity_map,
            )
        max_by_profile = global_cfg.get("max_freshness_ms_by_profile", {})
        if not isinstance(max_by_profile, dict):
            max_by_profile = {}
        max_freshness = max_by_profile.get(profile, max_by_profile.get("default"))
        if max_freshness is not None:
            try:
                max_freshness = float(max_freshness)
            except (TypeError, ValueError):
                max_freshness = None
        if max_freshness is not None and freshness_value > max_freshness:
            return _promotion_violation(
                "external STATE_EVENT promotion freshness exceeds policy",
                details={**details, "freshness_ms": freshness_ms, "max_freshness_ms": max_freshness},
                severity_map=severity_map,
            )

    return None


def _mode_for_profile(policy, key, profile, default="warn"):
    if not isinstance(policy, dict):
        return default
    value = policy.get(key, default)
    if isinstance(value, dict):
        value = value.get(profile, value.get("default", default))
    mode = str(value or default).strip().lower()
    if mode not in {"ignore", "warn", "reject"}:
        return default
    return mode


def _mode_severity(mode):
    return "fail" if mode == "reject" else "warn"


def _mode_violation(
    code,
    message,
    mode,
    details=None,
    severity_map=None,
    risk_dimension=None,
    policy=None,
    policy_ref=None,
):
    if mode == "ignore":
        return None
    details = dict(details or {})
    if risk_dimension:
        details = _risk_details(
            details,
            risk_dimension,
            mode,
            policy=policy,
            policy_ref=policy_ref,
        )
    else:
        details["policy_mode"] = mode
    return _violation(
        code,
        message,
        details=details,
        severity_map=severity_map,
        severity=_mode_severity(mode),
    )


_NON_MATERIAL_IGNORE_ALLOWLIST = {
    ("lineage", "unresolved_parent_mode", "L", "LINEAGE_PARENT_UNRESOLVED"),
}


def _policy_mode_entries(section, config, key, reason_codes, risk_dimension):
    if not isinstance(config, dict) or key not in config:
        return
    value = config.get(key)
    if isinstance(value, dict):
        for profile, mode in value.items():
            yield {
                "section": section,
                "path": f"{section}.{key}.{profile}",
                "key": key,
                "profile": str(profile),
                "mode": str(mode or "").strip().lower(),
                "risk_dimension": risk_dimension,
                "reason_codes": list(reason_codes),
            }
        return
    yield {
        "section": section,
        "path": f"{section}.{key}",
        "key": key,
        "profile": None,
        "mode": str(value or "").strip().lower(),
        "risk_dimension": risk_dimension,
        "reason_codes": list(reason_codes),
    }


def _ignore_is_allowlisted(entry):
    profile = entry.get("profile")
    if profile is None:
        return False
    for reason_code in entry.get("reason_codes", []):
        key = (entry.get("section"), entry.get("key"), profile, reason_code)
        if key not in _NON_MATERIAL_IGNORE_ALLOWLIST:
            return False
    return True


def lint_policy_risk_modes(policy):
    """Return policy lint issues for risk modes that can hide material risk."""
    issues = []
    if not isinstance(policy, dict):
        return issues

    entries = []
    timing = policy.get("timing_freshness", {})
    entries.extend(
        _policy_mode_entries(
            "timing_freshness",
            timing,
            "mode",
            ["TIMING_STATUS_MISSING", "TIMING_STATUS_STALE", "TIMING_STATUS_AGE_NEGATIVE"],
            "timing",
        )
    )
    entries.extend(
        _policy_mode_entries(
            "timing_freshness",
            timing,
            "mode_by_profile",
            ["TIMING_STATUS_MISSING", "TIMING_STATUS_STALE", "TIMING_STATUS_AGE_NEGATIVE"],
            "timing",
        )
    )
    entries.extend(
        _policy_mode_entries(
            "timing_freshness",
            timing,
            "missing_mode",
            ["TIMING_STATUS_MISSING"],
            "timing",
        )
    )
    entries.extend(
        _policy_mode_entries(
            "timing_freshness",
            timing,
            "missing_mode_by_profile",
            ["TIMING_STATUS_MISSING"],
            "timing",
        )
    )
    entries.extend(
        _policy_mode_entries(
            "timing_freshness",
            timing,
            "stale_mode",
            ["TIMING_STATUS_STALE"],
            "timing",
        )
    )
    entries.extend(
        _policy_mode_entries(
            "timing_freshness",
            timing,
            "stale_mode_by_profile",
            ["TIMING_STATUS_STALE"],
            "timing",
        )
    )
    entries.extend(
        _policy_mode_entries(
            "timing_freshness",
            timing,
            "negative_age_mode",
            ["TIMING_STATUS_AGE_NEGATIVE"],
            "timing",
        )
    )
    entries.extend(
        _policy_mode_entries(
            "timing_freshness",
            timing,
            "negative_age_mode_by_profile",
            ["TIMING_STATUS_AGE_NEGATIVE"],
            "timing",
        )
    )
    holdover = timing.get("holdover_est_error_monotonic", {})
    entries.extend(
        _policy_mode_entries(
            "timing_freshness.holdover_est_error_monotonic",
            holdover,
            "mode",
            ["TIMING_STATUS_HOLDOVER_NON_MONOTONIC"],
            "timing",
        )
    )

    lineage = policy.get("lineage", {})
    entries.extend(
        _policy_mode_entries(
            "lineage",
            lineage,
            "payload_based_on_subset_mode",
            ["LINEAGE_PAYLOAD_BASED_ON_NOT_SUBSET"],
            "lineage",
        )
    )
    entries.extend(
        _policy_mode_entries(
            "lineage",
            lineage,
            "fusion_members_in_lineage_mode",
            ["LINEAGE_FUSION_MEMBERS_NOT_IN_BASED_ON"],
            "lineage",
        )
    )
    entries.extend(
        _policy_mode_entries(
            "lineage",
            lineage,
            "unresolved_parent_mode",
            ["LINEAGE_PARENT_UNRESOLVED"],
            "lineage",
        )
    )
    entries.extend(
        _policy_mode_entries(
            "lineage",
            lineage,
            "parent_type_mismatch_mode",
            ["LINEAGE_PARENT_TYPE_INVALID"],
            "lineage",
        )
    )

    producer_authority = policy.get("producer_authority", {})
    promotion = producer_authority.get("external_state_promotion", {})
    entries.extend(
        _policy_mode_entries(
            "producer_authority.external_state_promotion",
            promotion,
            "mode",
            ["PRODUCER_NOT_ALLOWED"],
            "external_promotion",
        )
    )
    entries.extend(
        _policy_mode_entries(
            "producer_authority.external_state_promotion",
            promotion,
            "mode_by_profile",
            ["PRODUCER_NOT_ALLOWED"],
            "external_promotion",
        )
    )
    producers = producer_authority.get("producers", {})
    if isinstance(producers, dict):
        for producer, producer_rule in producers.items():
            if not isinstance(producer_rule, dict):
                continue
            rule = producer_rule.get("external_state_promotion", {})
            if not isinstance(rule, dict):
                continue
            section = f"producer_authority.producers.{producer}.external_state_promotion"
            entries.extend(
                _policy_mode_entries(
                    section,
                    rule,
                    "mode",
                    ["PRODUCER_NOT_ALLOWED"],
                    "external_promotion",
                )
            )
            entries.extend(
                _policy_mode_entries(
                    section,
                    rule,
                    "mode_by_profile",
                    ["PRODUCER_NOT_ALLOWED"],
                    "external_promotion",
                )
            )

    for entry in entries:
        if entry.get("mode") != "ignore" or _ignore_is_allowlisted(entry):
            continue
        issues.append(
            {
                "code": "POLICY_IGNORE_MATERIAL_RISK",
                "path": entry["path"],
                "risk_dimension": entry["risk_dimension"],
                "reason_codes": entry["reason_codes"],
                "message": (
                    "ignore is only allowed for explicitly non-material checks; "
                    "material timing, lineage, promotion, command, trust, or safety "
                    "risk must be rejected, warned, degraded, quarantined, or labeled"
                ),
            }
        )
    return issues


# Producer-authority structural vocabulary. validate_producer_authority
# reads these blocks with .get() defaults, so a typoed key or a deleted
# promotion sub-block silently disables enforcement while every gate stays
# green (R1-11 R11-05) — structural drift must fail the lint instead.
_PRODUCER_AUTHORITY_TOP_KEYS = frozenset(
    {"enabled", "producers", "require_match_for_event_types", "external_state_promotion"}
)
_PRODUCER_ENTRY_KEYS = frozenset(
    {"allowed_event_types", "forbidden_event_types", "external_state_promotion"}
)
# Producer promotion rules may carry the producer-specific gates plus
# overrides of any global promotion key the enforcement reads per-rule.
_PROMOTION_RULE_KEYS = frozenset(
    {
        "required",
        "approved_policy_ids",
        "allowed_projection_ids",
        "allowed_confidence_basis",
        "mode",
        "mode_by_profile",
        "always_reject_loop_risk",
        "allowed_loop_statuses",
        "loop_risk_statuses",
        "allowed_origin_kinds",
        "allowed_lineage_status_by_profile",
        "required_fields_by_profile",
        "required_state_category",
        "required_trust_ref_prefixes",
        "required_lineage_transform_prefixes",
        "source_event_uid_required_statuses",
        "max_freshness_ms_by_profile",
        "metadata_path",
        "degrade",
        "quarantine",
        "confidence_cap",
        "confidence_reduction_factor",
        "valid_for_ms_cap",
        "valid_for_ms_reduction_factor",
        "enabled",
    }
)


def lint_producer_authority_structure(policy):
    """Return lint issues for structurally mangled producer-authority policy."""
    issues = []
    if not isinstance(policy, dict):
        return issues
    authority = policy.get("producer_authority")
    if not isinstance(authority, dict):
        return issues

    def _issue(path, message):
        issues.append(
            {
                "code": "POLICY_PRODUCER_AUTHORITY_STRUCTURE",
                "path": path,
                "risk_dimension": "external_promotion",
                "reason_codes": ["PRODUCER_NOT_ALLOWED"],
                "message": message,
            }
        )

    for key in sorted(set(authority) - _PRODUCER_AUTHORITY_TOP_KEYS):
        _issue(
            f"producer_authority.{key}",
            "unknown producer-authority key: a typo here silently disables enforcement",
        )
    producers = authority.get("producers")
    if not isinstance(producers, dict):
        _issue("producer_authority.producers", "producers must be a mapping")
        return issues
    for name in sorted(producers):
        cfg = producers[name]
        base = f"producer_authority.producers.{name}"
        if not isinstance(cfg, dict):
            _issue(base, "producer entry must be a mapping")
            continue
        for key in sorted(set(cfg) - _PRODUCER_ENTRY_KEYS):
            _issue(
                f"{base}.{key}",
                "unknown producer entry key: a typo here silently disables enforcement",
            )
        promotion = cfg.get("external_state_promotion")
        if promotion is None:
            continue
        if not isinstance(promotion, dict):
            _issue(f"{base}.external_state_promotion", "external_state_promotion must be a mapping")
            continue
        for key in sorted(set(promotion) - _PROMOTION_RULE_KEYS):
            _issue(
                f"{base}.external_state_promotion.{key}",
                "unknown promotion-rule key: a typo here silently disables enforcement",
            )
        if not isinstance(promotion.get("required"), bool):
            _issue(
                f"{base}.external_state_promotion.required",
                "required must be an explicit boolean: absent or non-bool values "
                "silently disable promotion enforcement (cfg.get default)",
            )
    return issues


def _ids_from_list(value):
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if isinstance(item, str) and item.strip()]


def _lineage_based_on(event):
    lineage = event.get("lineage", {}) if isinstance(event, dict) else {}
    if not isinstance(lineage, dict):
        return []
    return _ids_from_list(lineage.get("based_on"))


def validate_schema(event, schema, severity_map=None):
    errors = sorted(schema.iter_errors(event), key=lambda e: e.path)
    violations = []
    for err in errors:
        violations.append(
            _violation(
                "SCHEMA_INVALID",
                err.message,
                details={"path": "/".join(str(p) for p in err.path)},
                severity_map=severity_map,
            )
        )
    return not violations, violations


def validate_role(event, roles_policy, severity_map=None):
    event_block = event.get("event", {})
    source = event.get("source", {})
    event_type = event_block.get("event_type")
    node_role = source.get("node_role")
    producer = source.get("producer")

    roles = roles_policy.get("roles", {})
    role_cfg = roles.get(node_role)
    if not role_cfg:
        return False, [
            _violation(
                "EVENT_TYPE_NOT_ALLOWED_FOR_ROLE",
                "unknown node_role",
                details={"node_role": node_role},
                severity_map=severity_map,
            )
        ]

    allowed = role_cfg.get("allowed_event_types", [])
    if event_type not in allowed:
        return False, [
            _violation(
                "EVENT_TYPE_NOT_ALLOWED_FOR_ROLE",
                "event_type not allowed for role",
                details={"event_type": event_type, "node_role": node_role},
                severity_map=severity_map,
            )
        ]

    producer_lc = (producer or "").lower()
    for rule in roles_policy.get("deny", []):
        if "event_type" in rule and rule["event_type"] != event_type:
            continue
        if "node_role" in rule and rule["node_role"] != node_role:
            continue
        if "producer" in rule and rule["producer"].lower() != producer_lc:
            continue
        return False, [
            _violation(
                "EVENT_TYPE_NOT_ALLOWED_FOR_ROLE",
                "event_type explicitly denied",
                details={"event_type": event_type, "node_role": node_role, "producer": producer},
                severity_map=severity_map,
            )
        ]

    return True, []


def validate_profile(event, profile, profiles_policy, severity_map=None):
    event_type = event.get("event", {}).get("event_type")
    event_profile = event.get("profile")
    if event_profile is not None and event_profile != profile:
        return False, [
            _violation(
                "PROFILE_MISMATCH",
                "event profile does not match validation/export profile",
                details={"event_profile": event_profile, "profile": profile},
                severity_map=severity_map,
            )
        ]
    profile_cfg = profiles_policy.get(profile)
    if not profile_cfg:
        return False, [
            _violation(
                "EVENT_TYPE_NOT_ALLOWED_FOR_PROFILE",
                "unknown profile",
                details={"profile": profile},
                severity_map=severity_map,
            )
        ]
    allowed = profile_cfg.get("allowed_event_types", [])
    if event_type not in allowed:
        return False, [
            _violation(
                "EVENT_TYPE_NOT_ALLOWED_FOR_PROFILE",
                "event_type not allowed for profile",
                details={"event_type": event_type, "profile": profile},
                severity_map=severity_map,
            )
        ]
    return True, []


def _has_per_event_timing(event, timing_policy):
    required = [str(field) for field in timing_policy.get("required_fields", []) if str(field).strip()]
    if not required:
        required = ["time_source", "sync_state", "est_error_ms", "last_sync_ts"]
    for path in timing_policy.get("per_event_paths", []):
        value = _resolve_path(event, path)
        if isinstance(value, dict) and all(field in value for field in required):
            return True
    return False


def validate_timing_quality(
    event,
    semantics_policy,
    state=None,
    severity_map=None,
    timing_freshness_policy=None,
    profile=None,
):
    timing_policy = semantics_policy.get("timing_quality", {})
    if not timing_policy.get("required", False):
        return True, []

    event_type = event.get("event", {}).get("event_type")
    payload = event.get("payload", {}) if isinstance(event, dict) else {}
    system_type = payload.get("system_type") if isinstance(payload, dict) else None

    freshness_enabled = _timing_freshness_enabled(timing_freshness_policy)

    if event_type == "SYSTEM_EVENT" and system_type == "TIME_STATUS":
        if not freshness_enabled or state is None:
            return True, []
        holdover_policy = timing_freshness_policy.get("holdover_est_error_monotonic", {})
        if not isinstance(holdover_policy, dict) or not holdover_policy.get("enabled", False):
            return True, []
        metrics = payload.get("metrics", {}) if isinstance(payload, dict) else {}
        if not isinstance(metrics, dict) or metrics.get("sync_state") != "HOLDOVER":
            return True, []
        _key, previous = state.get_timing(event)
        if not isinstance(previous, dict) or previous.get("sync_state") != "HOLDOVER":
            return True, []
        try:
            current_error = float(metrics.get("est_error_ms"))
            previous_error = float(previous.get("est_error_ms"))
        except (TypeError, ValueError):
            return True, []
        if current_error >= previous_error:
            return True, []
        mode = str(holdover_policy.get("mode", "warn") or "warn").strip().lower()
        if mode not in {"warn", "reject"}:
            mode = "warn"
        violation = _violation(
            "TIMING_STATUS_HOLDOVER_NON_MONOTONIC",
            "HOLDOVER est_error_ms decreased compared with previous TIME_STATUS",
            details=_risk_details(
                {
                    "source": "/".join(_source_key(event)),
                    "previous_est_error_ms": previous_error,
                    "current_est_error_ms": current_error,
                    "previous_ts": previous.get("_event_ts"),
                    "current_ts": event.get("event", {}).get("ts"),
                    "policy_mode": mode,
                },
                "timing",
                mode,
                policy=timing_freshness_policy,
                policy_ref="policy/timing-freshness.yaml#holdover_est_error_monotonic",
            ),
            severity_map=severity_map,
            severity="fail" if mode == "reject" else "warn",
        )
        return mode != "reject", [violation]

    required_event_types = timing_policy.get("required_event_types", [])
    required_event_types = {str(value) for value in required_event_types if str(value).strip()}
    if required_event_types and event_type not in required_event_types:
        return True, []

    if _has_per_event_timing(event, timing_policy):
        return True, []

    timing_status = None
    timing_key = None
    if state is not None:
        timing_key, timing_status = state.get_timing(event)
    if timing_status is not None:
        if not freshness_enabled:
            return True, []

        event_ts = _parse_utc_z(event.get("event", {}).get("ts"))
        status_ts = _parse_utc_z(timing_status.get("_event_ts"))
        if event_ts is None or status_ts is None:
            return True, []
        raw_age_ms = (event_ts - status_ts).total_seconds() * 1000.0
        event_profile = _profile_for_event(event, profile)
        if raw_age_ms < 0:
            negative_age_ms = abs(raw_age_ms)
            max_negative_age_ms = _max_negative_timing_status_age_ms(
                timing_freshness_policy, event_profile
            )
            if negative_age_ms <= max_negative_age_ms:
                return True, []

            mode = _timing_mode(timing_freshness_policy, "negative_age", event_profile)
            violation = _timing_policy_violation(
                "TIMING_STATUS_AGE_NEGATIVE",
                "event timestamp is earlier than latest TIME_STATUS beyond policy tolerance",
                mode,
                {
                    "source": "/".join(timing_key or _source_key(event)),
                    "event_type": event_type,
                    "profile": event_profile,
                    "age_ms": raw_age_ms,
                    "negative_age_ms": negative_age_ms,
                    "max_negative_age_ms": max_negative_age_ms,
                    "timing_status_ts": timing_status.get("_event_ts"),
                    "event_ts": event.get("event", {}).get("ts"),
                },
                timing_freshness_policy=timing_freshness_policy,
                severity_map=severity_map,
            )
            return violation["severity"] != "fail", [violation]

        age_ms = raw_age_ms
        max_age_ms = _max_timing_status_age_ms(timing_freshness_policy, event_profile)
        if age_ms <= max_age_ms:
            return True, []

        mode = _timing_mode(timing_freshness_policy, "stale", event_profile)
        violation = _timing_policy_violation(
            "TIMING_STATUS_STALE",
            "latest TIME_STATUS is older than policy maximum age",
            mode,
            {
                "source": "/".join(timing_key or _source_key(event)),
                "event_type": event_type,
                "profile": event_profile,
                "age_ms": age_ms,
                "max_age_ms": max_age_ms,
                "timing_status_ts": timing_status.get("_event_ts"),
                "event_ts": event.get("event", {}).get("ts"),
            },
            timing_freshness_policy=timing_freshness_policy,
            severity_map=severity_map,
        )
        return violation["severity"] != "fail", [violation]

    event_profile = _profile_for_event(event, profile)
    mode = (
        _timing_mode(timing_freshness_policy, "missing", event_profile)
        if freshness_enabled
        else "reject"
    )
    violation = _timing_policy_violation(
        "TIMING_STATUS_MISSING",
        "node has not exposed timing quality for this event",
        mode,
        {
            "source": "/".join(_source_key(event)),
            "event_type": event_type,
            "profile": event_profile,
        },
        timing_freshness_policy=timing_freshness_policy,
        severity_map=severity_map,
    )
    return violation["severity"] != "fail", [violation]


def validate_deduplication(event, state=None, severity_map=None):
    if state is None:
        return True, []
    event_block = event.get("event", {}) if isinstance(event, dict) else {}
    payload = event.get("payload", {}) if isinstance(event, dict) else {}
    event_type = event_block.get("event_type")
    event_id = event_block.get("event_id")

    if event_id and event_id in state.event_ids:
        return False, [
            _violation(
                "EVENT_DUPLICATE",
                "event_id has already been applied",
                details={"event_id": event_id},
                severity_map=severity_map,
            )
        ]

    if event_type == "COMMAND_EVENT" and isinstance(payload, dict):
        task_id = payload.get("task_id")
        if task_id and task_id in state.command_task_ids:
            return False, [
                _violation(
                    "TASK_DUPLICATE",
                    "COMMAND_EVENT task_id has already been applied",
                    details={"task_id": task_id},
                    severity_map=severity_map,
                )
            ]

    if event_type == "SYSTEM_EVENT" and isinstance(payload, dict) and payload.get("system_type") == "TASK_ACK":
        metrics = payload.get("metrics", {})
        if isinstance(metrics, dict):
            key = (metrics.get("task_id"), metrics.get("original_event_id"), payload.get("state"))
            if all(key) and key in state.task_ack_keys:
                return False, [
                    _violation(
                        "TASK_ACK_DUPLICATE",
                        "TASK_ACK state transition has already been applied",
                        details={
                            "task_id": key[0],
                            "original_event_id": key[1],
                            "state": key[2],
                        },
                        severity_map=severity_map,
                    )
                ]

    return True, []


def validate_semantics(event, semantics_policy, severity_map=None):
    event_block = event.get("event", {})
    payload = event.get("payload", {})

    event_type = event_block.get("event_type")
    event_subtype = event_block.get("event_subtype")

    warnings = []

    # Contract 6.4 frame provenance (version-agnostic, all event types).
    # quality.bearing_frame describes the canonical bearing and permits exactly
    # TRUE_NORTH; quality.heading_source is a free-form string naming the
    # heading reference. The v1.0 schema leaves quality free-form and the
    # locked schema cannot change, so this semantic check is the
    # lock-compatible enforcement route for v1.0 producers (and backstops
    # v1.1.0, where the schema also pins the enum).
    quality = payload.get("quality") if isinstance(payload, dict) else None
    if isinstance(quality, dict):
        if "bearing_frame" in quality and quality.get("bearing_frame") != "TRUE_NORTH":
            return False, [
                _violation(
                    "INVALID_QUALITY_BEARING_FRAME",
                    "quality.bearing_frame permits exactly TRUE_NORTH",
                    details={
                        "field": "quality.bearing_frame",
                        "value": quality.get("bearing_frame"),
                    },
                    severity_map=severity_map,
                )
            ]
        if "heading_source" in quality and not isinstance(quality.get("heading_source"), str):
            return False, [
                _violation(
                    "INVALID_QUALITY_HEADING_SOURCE",
                    "quality.heading_source must be a string",
                    details={
                        "field": "quality.heading_source",
                        "value": quality.get("heading_source"),
                    },
                    severity_map=severity_map,
                )
            ]

    # Contract 6.8 zero-fill heuristic (warn only, never reject). (0, 0) is a
    # legitimate coordinate (null island), so lat == 0.0 and lon == 0.0 cannot
    # be proven to be zero-fill - a hard check is impossible and warn severity
    # is the documented ceiling. The same ambiguity is handled at ingress by
    # the MAVLink adapter's refuse-to-fabricate rule
    # (adapters/ingress/mavlink/README.md).
    if isinstance(payload, dict):
        geo_candidates = [("payload.geo", payload.get("geo"))]
        claim = payload.get("claim")
        if isinstance(claim, dict):
            geo_candidates.append(("payload.claim.geo", claim.get("geo")))
        for geo_path, geo in geo_candidates:
            if (
                isinstance(geo, dict)
                and isinstance(geo.get("lat"), (int, float))
                and isinstance(geo.get("lon"), (int, float))
                and float(geo["lat"]) == 0.0
                and float(geo["lon"]) == 0.0
            ):
                warnings.append(
                    _violation(
                        "GEO_ZERO_FILL_SUSPECTED",
                        "geo sits at (0, 0); zero-filled position suspected (contract 6.8)",
                        details={"path": geo_path},
                        severity_map=severity_map,
                    )
                )

    # Contract 6.4 frame-provenance heuristic (warn only, never reject): a
    # canonical bearing with no frame provenance in either channel
    # (bearing.frame or quality.bearing_frame) passes every hard gate, yet
    # a mislabeled magnetic bearing consumed as true north is silent
    # geolocation corruption. v1.0 tolerates legacy-unlabeled bearings, so
    # warn is the ceiling - this makes the assertively-labeled vs
    # legacy-unlabeled distinction machine-visible (R1-11 R11-21).
    if isinstance(payload, dict):
        bearing = payload.get("bearing")
        if isinstance(bearing, dict) and bearing.get("az_deg") is not None:
            quality_block = payload.get("quality")
            if not isinstance(quality_block, dict):
                quality_block = {}
            if "frame" not in bearing and "bearing_frame" not in quality_block:
                warnings.append(
                    _violation(
                        "BEARING_FRAME_UNLABELED",
                        "canonical bearing carries no frame provenance "
                        "(bearing.frame or quality.bearing_frame) - contract 6.4 "
                        "frame assertion missing",
                        details={"path": "payload.bearing"},
                        severity_map=severity_map,
                    )
                )

    # Contract 8.1 confidence honesty: jsonschema min/max comparisons are
    # vacuous against NaN, so a non-finite confidence validates clean at
    # the schema layer while carrying no claim at all - fail it here
    # (R1-11 R11-04, validator side).
    confidence_candidates = [("confidence", event.get("confidence"))]
    if isinstance(payload, dict):
        claim_block = payload.get("claim")
        if isinstance(claim_block, dict):
            confidence_candidates.append(
                ("payload.claim.confidence", claim_block.get("confidence"))
            )
    for conf_path, conf_value in confidence_candidates:
        if isinstance(conf_value, float) and not math.isfinite(conf_value):
            return False, [
                _violation(
                    "NON_FINITE_CONFIDENCE",
                    "confidence must be a finite number in [0, 1]; NaN/inf is not an honest claim",
                    details={"field": conf_path},
                    severity_map=severity_map,
                )
            ]

    if event_type == "OBSERVATION_EVENT":
        forbidden = semantics_policy.get("observation_event", {}).get("payload_must_not_contain", [])
        forbidden_keys = {_normalize_key(key) for key in forbidden}
        found = _find_forbidden_key(payload, forbidden_keys)
        if found:
            found_key, path = found
            return False, [
                _violation(
                    "OBSERVATION_HAS_IDENTITY",
                    "observation payload contains identity fields",
                    details={"field": found_key, "path": "/".join(path)},
                    severity_map=severity_map,
                )
            ]

        if payload.get("modality") == "RF" and "t_start" in payload and "t_end" in payload:
            timestamp = _parse_utc_z(event_block.get("ts"))
            start = _parse_utc_z(payload.get("t_start"))
            end = _parse_utc_z(payload.get("t_end"))
            tolerance_ms = semantics_policy.get("observation_event", {}).get(
                "rf_window_midpoint_tolerance_ms", 1
            )
            try:
                tolerance_ms = float(tolerance_ms)
            except (TypeError, ValueError):
                tolerance_ms = 1.0
            if timestamp is not None and start is not None and end is not None:
                midpoint = start + ((end - start) / 2)
                delta_ms = abs((timestamp - midpoint).total_seconds() * 1000)
                if end < start or delta_ms > tolerance_ms:
                    return False, [
                        _violation(
                            "RF_WINDOW_MIDPOINT_MISMATCH",
                            "RF observation event.ts must equal the t_start/t_end midpoint",
                            details={
                                "ts": event_block.get("ts"),
                                "t_start": payload.get("t_start"),
                                "t_end": payload.get("t_end"),
                                "expected_midpoint": _format_utc_z(midpoint),
                                "delta_ms": delta_ms,
                                "tolerance_ms": tolerance_ms,
                            },
                            severity_map=severity_map,
                        )
                    ]

    if event_type == "INFERENCE_EVENT":
        forbidden = semantics_policy.get("inference_event", {}).get("payload_must_not_contain", [])
        forbidden_keys = {_normalize_key(key) for key in forbidden}
        found = _find_forbidden_key(payload, forbidden_keys)
        if found:
            found_key, path = found
            # Contract 7.5: payload and payload.claim MUST NOT contain
            # track_id, members, or estimated_state. track_id keeps its
            # historical code; the fused-state fields (members,
            # estimated_state) report INFERENCE_HAS_FUSION_STATE.
            if _normalize_key(found_key) == "track_id":
                code = "INFERENCE_HAS_TRACK_ID"
                message = "inference payload contains track identity"
            else:
                code = "INFERENCE_HAS_FUSION_STATE"
                message = "inference payload contains fused-state fields"
            return False, [
                _violation(
                    code,
                    message,
                    details={"field": found_key, "path": "/".join(path)},
                    severity_map=severity_map,
                )
            ]

    if event_type == "STATE_EVENT":
        forbidden = semantics_policy.get("state_event", {}).get("payload_must_not_contain", [])
        forbidden_keys = {_normalize_key(key) for key in forbidden}
        found = _find_forbidden_key(payload, forbidden_keys)
        if found:
            found_key, path = found
            return False, [
                _violation(
                    "STATE_HAS_RAW_FEATURES",
                    "state payload contains raw sensor features",
                    details={"field": found_key, "path": "/".join(path)},
                    severity_map=severity_map,
                )
            ]

    if event_type == "COMMAND_EVENT":
        requires_deconfliction = (
            semantics_policy.get("command_event", {}).get("requires_deconfliction", True)
        )
        if requires_deconfliction and payload.get("requires_deconfliction") is not True:
            return False, [
                _violation(
                    "COMMAND_NOT_DECONFLICTED",
                    "requires_deconfliction must be true",
                    details={"field": "requires_deconfliction"},
                    severity_map=severity_map,
                )
            ]
        forbidden = semantics_policy.get("command_event", {}).get("payload_must_not_contain", [])
        if not forbidden:
            forbidden = semantics_policy.get("command_event", {}).get("target_geo_must_not_include", [])
        forbidden_keys = {_normalize_key(key) for key in forbidden}
        found = _find_forbidden_key(payload, forbidden_keys) if forbidden_keys else None
        if found:
            found_key, path = found
            return False, [
                _violation(
                    "COMMAND_HAS_ALTITUDE",
                    "command payload must not include altitude",
                    details={"field": found_key, "path": "/".join(path)},
                    severity_map=severity_map,
                )
            ]

    if event_type == "SYSTEM_EVENT":
        system_policy = semantics_policy.get("system_event", {})
        system_type = payload.get("system_type")

        if system_type == "SCHEMA_VIOLATION":
            metrics = payload.get("metrics")
            required_fields = system_policy.get("schema_violation_required_metrics_fields", [])
            required_fields = [str(field) for field in required_fields if str(field).strip()]
            if not isinstance(metrics, dict):
                missing = required_fields or ["reason_code", "original_event_id"]
                if "reason_code" in missing:
                    code = "SCHEMA_VIOLATION_MISSING_REASON_CODE"
                elif "original_event_id" in missing:
                    code = "SCHEMA_VIOLATION_MISSING_ORIGINAL_EVENT_ID"
                else:
                    code = "SCHEMA_VIOLATION_MISSING_REASON_CODE"
                return False, [
                    _violation(
                        code,
                        "SCHEMA_VIOLATION metrics missing required fields",
                        details={"missing": missing},
                        severity_map=severity_map,
                    )
                ]
            missing = [field for field in required_fields if field not in metrics]
            if missing:
                if "reason_code" in missing:
                    code = "SCHEMA_VIOLATION_MISSING_REASON_CODE"
                elif "original_event_id" in missing:
                    code = "SCHEMA_VIOLATION_MISSING_ORIGINAL_EVENT_ID"
                else:
                    code = "SCHEMA_VIOLATION_MISSING_REASON_CODE"
                return False, [
                    _violation(
                        code,
                        "SCHEMA_VIOLATION metrics missing required fields",
                        details={"missing": missing},
                        severity_map=severity_map,
                    )
                ]

            reason_code = metrics.get("reason_code") if isinstance(metrics, dict) else None
            allowed_reason_codes = system_policy.get("schema_violation_allowed_reason_codes", [])
            allowed_reason_codes = [str(value) for value in allowed_reason_codes if str(value).strip()]
            if allowed_reason_codes and isinstance(reason_code, str) and reason_code.strip():
                if reason_code not in allowed_reason_codes:
                    return False, [
                        _violation(
                            "SCHEMA_VIOLATION_INVALID_REASON_CODE",
                            "SCHEMA_VIOLATION reason_code not allowed",
                            details={"reason_code": reason_code},
                            severity_map=severity_map,
                        )
                    ]

        if system_type == "LINK_STATUS":
            state = payload.get("state")
            allowed_states = system_policy.get("link_status_allowed_states", [])
            allowed_states = [str(value) for value in allowed_states if str(value).strip()]
            if allowed_states and state not in allowed_states:
                return False, [
                    _violation(
                        "LINK_STATUS_INVALID_STATE",
                        "LINK_STATUS state not allowed",
                        details={"state": state},
                        severity_map=severity_map,
                    )
                ]

            metrics = payload.get("metrics")
            required_fields = system_policy.get("link_status_required_metrics_fields", [])
            required_fields = [str(field) for field in required_fields if str(field).strip()]
            if not isinstance(metrics, dict):
                missing = required_fields or ["link_id"]
                return False, [
                    _violation(
                        "LINK_STATUS_MISSING_REQUIRED_FIELD",
                        "LINK_STATUS metrics missing required fields",
                        details={"missing": missing},
                        severity_map=severity_map,
                    )
                ]
            missing = [field for field in required_fields if field not in metrics]
            if missing:
                return False, [
                    _violation(
                        "LINK_STATUS_MISSING_REQUIRED_FIELD",
                        "LINK_STATUS metrics missing required fields",
                        details={"missing": missing},
                        severity_map=severity_map,
                    )
                ]

            reason_code = metrics.get("reason_code") if isinstance(metrics, dict) else None
            require_reason_states = system_policy.get("link_status_reason_code_required_states", [])
            require_reason_states = [str(value) for value in require_reason_states if str(value).strip()]
            if require_reason_states and state in require_reason_states:
                if not isinstance(reason_code, str) or not reason_code.strip():
                    return False, [
                        _violation(
                            "LINK_STATUS_MISSING_REASON_CODE",
                            "LINK_STATUS reason_code required for state",
                            details={"state": state},
                            severity_map=severity_map,
                        )
                    ]

            allowed_reason_codes = system_policy.get("link_status_allowed_reason_codes", [])
            allowed_reason_codes = [str(value) for value in allowed_reason_codes if str(value).strip()]
            if allowed_reason_codes and isinstance(reason_code, str) and reason_code.strip():
                if reason_code not in allowed_reason_codes:
                    return False, [
                        _violation(
                            "LINK_STATUS_INVALID_REASON_CODE",
                            "LINK_STATUS reason_code not allowed",
                            details={"reason_code": reason_code, "state": state},
                            severity_map=severity_map,
                        )
                    ]

        if event_subtype == "TASK_ACK" or system_type == "TASK_ACK":
            state = payload.get("state")
            allowed_states = system_policy.get("task_ack_allowed_states", [])
            allowed_states = [str(value) for value in allowed_states if str(value).strip()]
            if allowed_states and state not in allowed_states:
                return False, [
                    _violation(
                        "TASK_ACK_INVALID_STATE",
                        "TASK_ACK state not allowed",
                        details={"state": state},
                        severity_map=severity_map,
                    )
                ]

            metrics = payload.get("metrics")
            required_fields = system_policy.get("task_ack_required_metrics_fields")
            if not required_fields:
                required_fields = system_policy.get("task_ack_requires_metrics_fields", [])
            required_fields = [str(field) for field in required_fields if str(field).strip()]
            if not isinstance(metrics, dict):
                missing = required_fields or ["task_id"]
                if "task_id" in missing:
                    code = "TASK_ACK_MISSING_TASK_ID"
                elif "original_event_id" in missing:
                    code = "TASK_ACK_MISSING_ORIGINAL_EVENT_ID"
                else:
                    code = "TASK_ACK_MISSING_REQUIRED_FIELD"
                return False, [
                    _violation(
                        code,
                        "TASK_ACK metrics missing required fields",
                        details={"missing": missing},
                        severity_map=severity_map,
                    )
                ]
            missing = [field for field in required_fields if field not in metrics]
            if missing:
                if "task_id" in missing:
                    code = "TASK_ACK_MISSING_TASK_ID"
                elif "original_event_id" in missing:
                    code = "TASK_ACK_MISSING_ORIGINAL_EVENT_ID"
                else:
                    code = "TASK_ACK_MISSING_REQUIRED_FIELD"
                return False, [
                    _violation(
                        code,
                        "TASK_ACK metrics missing required fields",
                        details={"missing": missing},
                        severity_map=severity_map,
                    )
                ]

            reason_code = metrics.get("reason_code") if isinstance(metrics, dict) else None
            require_reason_states = system_policy.get("task_ack_reason_code_required_states", [])
            require_reason_states = [str(value) for value in require_reason_states if str(value).strip()]
            if require_reason_states and state in require_reason_states:
                if not isinstance(reason_code, str) or not reason_code.strip():
                    return False, [
                        _violation(
                            "TASK_ACK_MISSING_REASON_CODE",
                            "TASK_ACK reason_code required for state",
                            details={"state": state},
                            severity_map=severity_map,
                        )
                    ]

            allowed_reason_codes = system_policy.get("task_ack_allowed_reason_codes", [])
            allowed_reason_codes = [str(value) for value in allowed_reason_codes if str(value).strip()]
            if allowed_reason_codes and isinstance(reason_code, str) and reason_code.strip():
                if reason_code not in allowed_reason_codes:
                    return False, [
                        _violation(
                            "TASK_ACK_INVALID_REASON_CODE",
                            "TASK_ACK reason_code not allowed",
                            details={"reason_code": reason_code, "state": state},
                            severity_map=severity_map,
                        )
                    ]

    return True, warnings


def validate_lineage(event, lineage_policy, state=None, profile=None, severity_map=None):
    if not isinstance(lineage_policy, dict) or lineage_policy.get("enabled", True) is False:
        return True, []

    event_block = event.get("event", {}) if isinstance(event, dict) else {}
    payload = event.get("payload", {}) if isinstance(event, dict) else {}
    event_type = event_block.get("event_type")
    event_profile = _profile_for_event(event, profile)
    lineage_based_on = set(_lineage_based_on(event))
    violations = []

    payload_based_on = _ids_from_list(payload.get("based_on")) if isinstance(payload, dict) else []
    if payload_based_on:
        missing = sorted(item for item in payload_based_on if item not in lineage_based_on)
        if missing:
            mode = _mode_for_profile(
                lineage_policy, "payload_based_on_subset_mode", event_profile, default="reject"
            )
            violation = _mode_violation(
                "LINEAGE_PAYLOAD_BASED_ON_NOT_SUBSET",
                "payload.based_on must be equal to or a subset of lineage.based_on",
                mode,
                {
                    "event_id": event_block.get("event_id"),
                    "event_type": event_type,
                    "missing_from_lineage": missing,
                },
                severity_map=severity_map,
                risk_dimension="lineage",
                policy=lineage_policy,
                policy_ref="policy/lineage.yaml#payload_based_on_subset_mode",
            )
            if violation:
                violations.append(violation)

    if event_type == "FUSION_EVENT" and isinstance(payload, dict):
        members = _ids_from_list(payload.get("members"))
        if members:
            missing_members = sorted(item for item in members if item not in lineage_based_on)
            if missing_members:
                mode = _mode_for_profile(
                    lineage_policy, "fusion_members_in_lineage_mode", event_profile, default="warn"
                )
                violation = _mode_violation(
                    "LINEAGE_FUSION_MEMBERS_NOT_IN_BASED_ON",
                    "FUSION_EVENT payload.members should be represented in lineage.based_on",
                    mode,
                    {
                        "event_id": event_block.get("event_id"),
                        "missing_members": missing_members,
                    },
                    severity_map=severity_map,
                    risk_dimension="lineage",
                    policy=lineage_policy,
                    policy_ref="policy/lineage.yaml#fusion_members_in_lineage_mode",
                )
                if violation:
                    violations.append(violation)

    if state is None or not hasattr(state, "get_event"):
        return not any(v.get("severity") == "fail" for v in violations), violations

    allowed_policy = lineage_policy.get("allowed_parent_event_types", {})
    if not isinstance(allowed_policy, dict):
        allowed_policy = {}
    allowed_parent_types = set(_list_values(allowed_policy.get(event_type)))

    unresolved = []
    invalid = []
    for parent_id in sorted(lineage_based_on):
        parent = state.get_event(parent_id)
        if not parent:
            unresolved.append(parent_id)
            continue
        parent_type = parent.get("event_type")
        if allowed_parent_types and parent_type not in allowed_parent_types:
            invalid.append({"event_id": parent_id, "event_type": parent_type})

    if unresolved:
        mode = _mode_for_profile(lineage_policy, "unresolved_parent_mode", event_profile, default="warn")
        violation = _mode_violation(
            "LINEAGE_PARENT_UNRESOLVED",
            "lineage parent references are not available in the local event store",
            mode,
            {
                "event_id": event_block.get("event_id"),
                "event_type": event_type,
                "profile": event_profile,
                "unresolved": unresolved,
            },
            severity_map=severity_map,
            risk_dimension="lineage",
            policy=lineage_policy,
            policy_ref="policy/lineage.yaml#unresolved_parent_mode",
        )
        if violation:
            violations.append(violation)

    if invalid:
        mode = _mode_for_profile(lineage_policy, "parent_type_mismatch_mode", event_profile, default="reject")
        violation = _mode_violation(
            "LINEAGE_PARENT_TYPE_INVALID",
            "lineage parent event_type is not allowed for this event_type",
            mode,
            {
                "event_id": event_block.get("event_id"),
                "event_type": event_type,
                "invalid_parents": invalid,
                "allowed_parent_event_types": sorted(allowed_parent_types),
            },
            severity_map=severity_map,
            risk_dimension="lineage",
            policy=lineage_policy,
            policy_ref="policy/lineage.yaml#parent_type_mismatch_mode",
        )
        if violation:
            violations.append(violation)

    return not any(v.get("severity") == "fail" for v in violations), violations


def validate_producer_authority(event, authority_policy, severity_map=None):
    if not isinstance(authority_policy, dict) or authority_policy.get("enabled", True) is False:
        return True, []

    event_block = event.get("event", {}) if isinstance(event, dict) else {}
    source = event.get("source", {}) if isinstance(event, dict) else {}
    event_type = event_block.get("event_type")
    event_subtype = event_block.get("event_subtype")
    producer = (source.get("producer") or "").strip()

    producer_rules = authority_policy.get("producers", {})
    matching_rules = _matching_producer_rules(producer, producer_rules)
    matched_patterns = [pattern for pattern, _rule in matching_rules]
    require_match = {
        str(value).strip()
        for value in authority_policy.get("require_match_for_event_types", [])
        if str(value).strip()
    }

    if not matching_rules:
        if event_type in require_match:
            return False, [
                _violation(
                    "PRODUCER_NOT_ALLOWED",
                    "producer does not match producer authority policy",
                    details={"event_type": event_type, "producer": producer},
                    severity_map=severity_map,
                )
            ]
        return True, []

    forbidden_types = set()
    allowed_types = set()
    allowed_subtypes = set()
    has_allowed_types = False
    has_allowed_subtypes = False

    for _pattern, rule in matching_rules:
        if not isinstance(rule, dict):
            continue
        forbidden_types.update(_list_values(rule.get("forbidden_event_types")))
        rule_allowed_types = _list_values(rule.get("allowed_event_types"))
        if rule_allowed_types:
            has_allowed_types = True
            allowed_types.update(rule_allowed_types)
        rule_allowed_subtypes = _list_values(rule.get("allowed_event_subtypes"))
        if rule_allowed_subtypes:
            has_allowed_subtypes = True
            allowed_subtypes.update(rule_allowed_subtypes)

    if event_type in forbidden_types:
        return False, [
            _violation(
                "PRODUCER_NOT_ALLOWED",
                "event_type forbidden for producer",
                details={
                    "event_type": event_type,
                    "producer": producer,
                    "matched_patterns": matched_patterns,
                },
                severity_map=severity_map,
            )
        ]

    if has_allowed_types and event_type not in allowed_types:
        return False, [
            _violation(
                "PRODUCER_NOT_ALLOWED",
                "event_type not authorized for producer",
                details={
                    "event_type": event_type,
                    "producer": producer,
                    "matched_patterns": matched_patterns,
                },
                severity_map=severity_map,
            )
        ]

    if has_allowed_subtypes and event_subtype not in allowed_subtypes:
        return False, [
            _violation(
                "PRODUCER_NOT_ALLOWED",
                "event_subtype not authorized for producer",
                details={
                    "event_subtype": event_subtype,
                    "producer": producer,
                    "matched_patterns": matched_patterns,
                },
                severity_map=severity_map,
            )
        ]

    promotion_violation = _validate_external_state_promotion(
        event,
        authority_policy,
        _external_promotion_rules(matching_rules),
        matched_patterns,
        severity_map=severity_map,
    )
    if promotion_violation:
        return promotion_violation.get("severity") != "fail", [promotion_violation]

    return True, []


def _is_comms_producer(producer, routing_policy):
    cmd_cfg = routing_policy.get("command_event", {})
    allowlist = []
    for key in ("allowed_producers", "required_origin", "must_pass_through"):
        value = cmd_cfg.get(key)
        if isinstance(value, list):
            allowlist.extend(value)
        elif isinstance(value, str):
            allowlist.append(value)
    if not allowlist:
        allowlist = ["sensorops"]
    return any(_matches_pattern(producer, token) for token in allowlist)


def validate_routing(event, routing_policy, severity_map=None):
    event_type = event.get("event", {}).get("event_type")
    event_subtype = event.get("event", {}).get("event_subtype")
    producer = (event.get("source", {}).get("producer") or "").strip()
    producer_rules = routing_policy.get("producers", {})
    enforcement = routing_policy.get("producer_enforcement", {})
    require_allowlist = enforcement.get("require_allowlist_for_event_types", [])
    require_allowlist = {str(value).strip() for value in require_allowlist if str(value).strip()}
    if producer_rules:
        matching_rules = _matching_producer_rules(producer, producer_rules)
        matched_patterns = [pattern for pattern, _rule in matching_rules]
        if require_allowlist and event_type in require_allowlist and not matching_rules:
            return False, [
                _violation(
                    "PRODUCER_NOT_ALLOWED",
                    "producer not allowlisted for event_type",
                    details={"event_type": event_type, "producer": producer},
                    severity_map=severity_map,
                )
            ]
        if matching_rules:
            allowed_types = set()
            allowed_subtypes = set()
            forbidden = set()
            has_allowed_types = False
            has_allowed_subtypes = False
            for _pattern, rule in matching_rules:
                if not isinstance(rule, dict):
                    continue
                rule_allowed_types = _list_values(rule.get("allowed_event_types"))
                if rule_allowed_types:
                    has_allowed_types = True
                    allowed_types.update(rule_allowed_types)
                rule_allowed_subtypes = _list_values(rule.get("allowed_event_subtypes"))
                if rule_allowed_subtypes:
                    has_allowed_subtypes = True
                    allowed_subtypes.update(rule_allowed_subtypes)
                forbidden.update(_list_values(rule.get("forbidden_event_types")))

            if has_allowed_types and event_type not in allowed_types:
                return False, [
                    _violation(
                        "EVENT_TYPE_NOT_ALLOWED_FOR_ROLE",
                        "event_type not allowed for producer",
                        details={
                            "event_type": event_type,
                            "producer": producer,
                            "matched_patterns": matched_patterns,
                        },
                        severity_map=severity_map,
                    )
                ]
            if has_allowed_subtypes and event_subtype not in allowed_subtypes:
                return False, [
                    _violation(
                        "EVENT_TYPE_NOT_ALLOWED_FOR_ROLE",
                        "event_subtype not allowed for producer",
                        details={
                            "event_subtype": event_subtype,
                            "producer": producer,
                            "matched_patterns": matched_patterns,
                        },
                        severity_map=severity_map,
                    )
                ]
            if event_type in forbidden:
                return False, [
                    _violation(
                        "EVENT_TYPE_NOT_ALLOWED_FOR_ROLE",
                        "event_type forbidden for producer",
                        details={
                            "event_type": event_type,
                            "producer": producer,
                            "matched_patterns": matched_patterns,
                        },
                        severity_map=severity_map,
                    )
                ]

    if event_type != "COMMAND_EVENT":
        return True, []
    if not _is_comms_producer(producer, routing_policy):
        return False, [
            _violation(
                "COMMAND_NOT_DECONFLICTED",
                "COMMAND_EVENT must originate from comms node",
                details={"producer": producer},
                severity_map=severity_map,
            )
        ]
    return True, []
