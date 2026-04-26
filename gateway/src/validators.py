import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator, FormatChecker


class ValidationState:
    def __init__(self):
        self.timing_sources = set()
        self.latest_timing = {}
        self.event_ids = set()
        self.command_task_ids = set()
        self.task_ack_keys = set()

    def has_timing(self, event):
        return _source_key(event) in self.timing_sources

    def record(self, event):
        self.record_timing(event)
        event_block = event.get("event", {}) if isinstance(event, dict) else {}
        payload = event.get("payload", {}) if isinstance(event, dict) else {}
        event_type = event_block.get("event_type")
        system_type = payload.get("system_type") if isinstance(payload, dict) else None
        event_id = event_block.get("event_id")
        if event_id:
            self.event_ids.add(event_id)
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

    def record_timing(self, event):
        event_block = event.get("event", {}) if isinstance(event, dict) else {}
        payload = event.get("payload", {}) if isinstance(event, dict) else {}
        event_type = event_block.get("event_type")
        system_type = payload.get("system_type") if isinstance(payload, dict) else None
        if event_type == "SYSTEM_EVENT" and system_type == "TIME_STATUS":
            key = _source_key(event)
            self.timing_sources.add(key)
            metrics = payload.get("metrics", {}) if isinstance(payload, dict) else {}
            if isinstance(metrics, dict):
                self.latest_timing[key] = dict(metrics)


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


def _source_key(event):
    source = event.get("source", {}) if isinstance(event, dict) else {}
    return (
        str(source.get("platform_id") or "UNKNOWN"),
        str(source.get("producer") or "UNKNOWN"),
        str(source.get("node_role") or "UNKNOWN"),
    )


def _resolve_path(value, dotted_path):
    target = value
    for part in str(dotted_path).split("."):
        if not part:
            continue
        if not isinstance(target, dict):
            return None
        target = target.get(part)
    return target


def _find_forbidden_key(value, forbidden_keys):
    if isinstance(value, dict):
        for key, item in value.items():
            key_str = str(key)
            if key_str.lower() in forbidden_keys:
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


def validate_timing_quality(event, semantics_policy, state=None, severity_map=None):
    timing_policy = semantics_policy.get("timing_quality", {})
    if not timing_policy.get("required", False):
        return True, []

    event_type = event.get("event", {}).get("event_type")
    payload = event.get("payload", {}) if isinstance(event, dict) else {}
    system_type = payload.get("system_type") if isinstance(payload, dict) else None

    if event_type == "SYSTEM_EVENT" and system_type == "TIME_STATUS":
        return True, []

    required_event_types = timing_policy.get("required_event_types", [])
    required_event_types = {str(value) for value in required_event_types if str(value).strip()}
    if required_event_types and event_type not in required_event_types:
        return True, []

    if _has_per_event_timing(event, timing_policy):
        return True, []

    if state is not None and state.has_timing(event):
        return True, []

    return False, [
        _violation(
            "TIMING_STATUS_MISSING",
            "node has not exposed timing quality for this event",
            details={"source": "/".join(_source_key(event)), "event_type": event_type},
            severity_map=severity_map,
        )
    ]


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

    if event_type == "OBSERVATION_EVENT":
        forbidden = semantics_policy.get("observation_event", {}).get("payload_must_not_contain", [])
        forbidden_keys = {str(key).lower() for key in forbidden}
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

    if event_type == "INFERENCE_EVENT":
        forbidden = semantics_policy.get("inference_event", {}).get("payload_must_not_contain", [])
        forbidden_keys = {str(key).lower() for key in forbidden}
        found = _find_forbidden_key(payload, forbidden_keys)
        if found:
            found_key, path = found
            return False, [
                _violation(
                    "INFERENCE_HAS_TRACK_ID",
                    "inference payload contains track identity",
                    details={"field": found_key, "path": "/".join(path)},
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
        forbidden_keys = {str(key).lower() for key in forbidden}
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

    return True, []


def _is_comms_producer(producer, routing_policy):
    producer_lc = (producer or "").strip().lower()
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
    allowset = {str(token).strip().lower() for token in allowlist if str(token).strip()}
    return producer_lc in allowset


def validate_routing(event, routing_policy, severity_map=None):
    event_type = event.get("event", {}).get("event_type")
    event_subtype = event.get("event", {}).get("event_subtype")
    producer = (event.get("source", {}).get("producer") or "").strip().lower()
    producer_rules = routing_policy.get("producers", {})
    enforcement = routing_policy.get("producer_enforcement", {})
    require_allowlist = enforcement.get("require_allowlist_for_event_types", [])
    require_allowlist = {str(value).strip() for value in require_allowlist if str(value).strip()}
    if producer_rules:
        normalized_rules = {
            str(key).strip().lower(): value for key, value in producer_rules.items() if str(key).strip()
        }
        if require_allowlist and event_type in require_allowlist and producer not in normalized_rules:
            return False, [
                _violation(
                    "PRODUCER_NOT_ALLOWED",
                    "producer not allowlisted for event_type",
                    details={"event_type": event_type, "producer": producer},
                    severity_map=severity_map,
                )
            ]
        rule = normalized_rules.get(producer)
        if isinstance(rule, dict):
            allowed_types = rule.get("allowed_event_types")
            if isinstance(allowed_types, list) and event_type not in allowed_types:
                return False, [
                    _violation(
                        "EVENT_TYPE_NOT_ALLOWED_FOR_ROLE",
                        "event_type not allowed for producer",
                        details={"event_type": event_type, "producer": producer},
                        severity_map=severity_map,
                    )
                ]
            allowed_subtypes = rule.get("allowed_event_subtypes")
            if isinstance(allowed_subtypes, list) and event_subtype not in allowed_subtypes:
                return False, [
                    _violation(
                        "EVENT_TYPE_NOT_ALLOWED_FOR_ROLE",
                        "event_subtype not allowed for producer",
                        details={"event_subtype": event_subtype, "producer": producer},
                        severity_map=severity_map,
                    )
                ]
            forbidden = rule.get("forbidden_event_types")
            if isinstance(forbidden, list) and event_type in forbidden:
                return False, [
                    _violation(
                        "EVENT_TYPE_NOT_ALLOWED_FOR_ROLE",
                        "event_type forbidden for producer",
                        details={"event_type": event_type, "producer": producer},
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
