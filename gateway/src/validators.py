import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator, FormatChecker


def load_schema(schema_path):
    with open(schema_path, "r", encoding="utf-8") as handle:
        schema = json.load(handle)
    return Draft202012Validator(schema, format_checker=FormatChecker())


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
        "violation_codes": codes_cfg.get("violation_codes", []),
        "violation_severities": severity_map,
    }


def _resolve_severity(code, severity_map):
    if not severity_map:
        return "fail"
    return severity_map.get(code, "fail")


def _violation(code, message, details=None, severity_map=None):
    return {
        "code": code,
        "message": message,
        "severity": _resolve_severity(code, severity_map),
        "details": details or {},
    }


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


def validate_semantics(event, semantics_policy, severity_map=None):
    event_block = event.get("event", {})
    payload = event.get("payload", {})

    event_type = event_block.get("event_type")
    event_subtype = event_block.get("event_subtype")

    if event_type == "OBSERVATION_EVENT":
        forbidden = semantics_policy.get("observation_event", {}).get("payload_must_not_contain", [])
        for key in forbidden:
            if key in payload:
                return False, [
                    _violation(
                        "OBSERVATION_HAS_IDENTITY",
                        "observation payload contains identity fields",
                        details={"field": key},
                        severity_map=severity_map,
                    )
                ]

    if event_type == "STATE_EVENT":
        forbidden = semantics_policy.get("state_event", {}).get("payload_must_not_contain", [])
        for key in forbidden:
            if key in payload:
                return False, [
                    _violation(
                        "STATE_HAS_RAW_FEATURES",
                        "state payload contains raw sensor features",
                        details={"field": key},
                        severity_map=severity_map,
                    )
                ]

    if event_type == "COMMAND_EVENT":
        if payload.get("requires_deconfliction") is not True:
            return False, [
                _violation(
                    "COMMAND_NOT_DECONFLICTED",
                    "requires_deconfliction must be true",
                    details={"field": "requires_deconfliction"},
                    severity_map=severity_map,
                )
            ]
        target_geo = payload.get("target_geo")
        if isinstance(target_geo, dict):
            forbidden = semantics_policy.get("command_event", {}).get("target_geo_must_not_include", [])
            for key in forbidden:
                if key in target_geo:
                    return False, [
                        _violation(
                            "COMMAND_HAS_ALTITUDE",
                            "target_geo must not include altitude",
                            details={"field": key},
                            severity_map=severity_map,
                        )
                    ]

    if event_type == "SYSTEM_EVENT":
        if event_subtype == "TASK_ACK" or payload.get("system_type") == "TASK_ACK":
            metrics = payload.get("metrics")
            if not isinstance(metrics, dict) or "task_id" not in metrics:
                return False, [
                    _violation(
                        "TASK_ACK_MISSING_TASK_ID",
                        "TASK_ACK metrics requires task_id",
                        details={"field": "metrics.task_id"},
                        severity_map=severity_map,
                    )
                ]

    return True, []


def _is_comms_producer(producer, routing_policy):
    producer_lc = (producer or "").lower()
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
    return any(token.lower() in producer_lc for token in allowlist)


def validate_routing(event, routing_policy, severity_map=None):
    event_type = event.get("event", {}).get("event_type")
    producer = event.get("source", {}).get("producer")
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
