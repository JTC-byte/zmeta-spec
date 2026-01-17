import argparse
import json
import socket
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

MODULE_DIR = Path(__file__).resolve().parent
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))

from validators import (
    load_policy,
    load_schema,
    validate_profile,
    validate_role,
    validate_routing,
    validate_schema,
    validate_semantics,
)

from adapters.egress.cot.zmeta_to_cot import zmeta_to_cot


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class TaskDedupeCache:
    def __init__(self):
        self._cache = {}

    def _purge(self, now):
        expired = [key for key, expiry in self._cache.items() if expiry <= now]
        for key in expired:
            del self._cache[key]

    def check_and_set(self, task_id, ttl_ms):
        now = time.monotonic()
        self._purge(now)
        expiry = self._cache.get(task_id)
        if expiry and expiry > now:
            return True
        self._cache[task_id] = now + (ttl_ms / 1000.0)
        return False


def ttl_ms_from_payload(payload):
    ttl_ms = payload.get("valid_for_ms")
    try:
        ttl_ms = int(ttl_ms)
    except (TypeError, ValueError):
        ttl_ms = 60000
    if ttl_ms <= 0:
        ttl_ms = 60000
    return min(ttl_ms, 300000)


def build_violation_event(reason_code, original=None, details=None):
    original_event = original.get("event", {}) if isinstance(original, dict) else {}
    original_source = original.get("source", {}) if isinstance(original, dict) else {}
    original_payload = original.get("payload", {}) if isinstance(original, dict) else {}

    is_command = original_event.get("event_type") == "COMMAND_EVENT"
    event_subtype = "TASK_ACK" if is_command else "SCHEMA_VIOLATION"
    system_type = "TASK_ACK" if is_command else "SCHEMA_VIOLATION"

    metrics = {"reason_code": reason_code}
    if original_event.get("event_id"):
        metrics["original_event_id"] = original_event.get("event_id")
    if original_source.get("platform_id"):
        metrics["source_platform_id"] = original_source.get("platform_id")
    if original_source.get("producer"):
        metrics["source_producer"] = original_source.get("producer")
    if is_command and isinstance(original_payload, dict) and original_payload.get("task_id"):
        metrics["task_id"] = original_payload.get("task_id")
    if details:
        metrics.update(details)

    return {
        "zmeta_version": "1.0",
        "event": {
            "event_id": str(uuid.uuid4()),
            "event_type": "SYSTEM_EVENT",
            "event_subtype": event_subtype,
            "ts": utc_now(),
        },
        "source": {
            "platform_id": "zmeta-gateway",
            "node_role": "GATEWAY",
            "producer": "zmeta-gateway",
        },
        "payload": {
            "system_type": system_type,
            "state": "REJECTED",
            "metrics": metrics,
        },
    }


def build_warning_event(reason_code, original=None, details=None):
    original_event = original.get("event", {}) if isinstance(original, dict) else {}
    original_source = original.get("source", {}) if isinstance(original, dict) else {}

    metrics = {"reason_code": reason_code}
    if original_event.get("event_id"):
        metrics["original_event_id"] = original_event.get("event_id")
    if original_source.get("platform_id"):
        metrics["source_platform_id"] = original_source.get("platform_id")
    if original_source.get("producer"):
        metrics["source_producer"] = original_source.get("producer")
    if details:
        metrics.update(details)

    return {
        "zmeta_version": "1.0",
        "event": {
            "event_id": str(uuid.uuid4()),
            "event_type": "SYSTEM_EVENT",
            "event_subtype": "SCHEMA_VIOLATION",
            "ts": utc_now(),
        },
        "source": {
            "platform_id": "zmeta-gateway",
            "node_role": "GATEWAY",
            "producer": "zmeta-gateway",
        },
        "payload": {
            "system_type": "SCHEMA_VIOLATION",
            "state": "WARNING",
            "metrics": metrics,
        },
    }


def build_duplicate_ack(original):
    original_event = original.get("event", {}) if isinstance(original, dict) else {}
    original_payload = original.get("payload", {}) if isinstance(original, dict) else {}

    metrics = {
        "reason_code": "TASK_DUPLICATE",
        "task_id": original_payload.get("task_id"),
        "original_event_id": original_event.get("event_id"),
    }

    return {
        "zmeta_version": "1.0",
        "event": {
            "event_id": str(uuid.uuid4()),
            "event_type": "SYSTEM_EVENT",
            "event_subtype": "TASK_ACK",
            "ts": utc_now(),
        },
        "source": {
            "platform_id": "zmeta-gateway",
            "node_role": "GATEWAY",
            "producer": "zmeta-gateway",
        },
        "payload": {
            "system_type": "TASK_ACK",
            "state": "DUPLICATE_IGNORED",
            "metrics": metrics,
        },
    }


def _split_violations(violations):
    fails = []
    warns = []
    for violation in violations:
        if violation.get("severity") == "warn":
            warns.append(violation)
        else:
            fails.append(violation)
    return fails, warns


def process_message(message, validator, policy, profile, dedupe_cache):
    try:
        text = message.decode("utf-8")
    except UnicodeDecodeError as exc:
        return build_violation_event("SCHEMA_INVALID", details={"error": str(exc)})

    try:
        instance = json.loads(text)
    except json.JSONDecodeError as exc:
        return build_violation_event("SCHEMA_INVALID", details={"error": str(exc)})

    severity_map = policy.get("violation_severities", {})
    warnings = []

    ok, violations = validate_schema(instance, validator, severity_map)
    if not ok:
        violation = violations[0]
        return [
            build_violation_event(
                violation["code"],
                original=instance,
                details={"error": violation["message"], **violation.get("details", {})},
            )
        ]

    ok, violations = validate_role(
        instance, {"roles": policy["roles"], "deny": policy["deny"]}, severity_map
    )
    if violations:
        fails, warns = _split_violations(violations)
        if fails:
            violation = fails[0]
            return [build_violation_event(violation["code"], original=instance, details=violation.get("details"))]
        warnings.extend(warns)

    ok, violations = validate_profile(instance, profile, policy["profiles"], severity_map)
    if violations:
        fails, warns = _split_violations(violations)
        if fails:
            violation = fails[0]
            return [build_violation_event(violation["code"], original=instance, details=violation.get("details"))]
        warnings.extend(warns)

    ok, violations = validate_semantics(instance, policy["semantics"], severity_map)
    if violations:
        fails, warns = _split_violations(violations)
        if fails:
            violation = fails[0]
            return [build_violation_event(violation["code"], original=instance, details=violation.get("details"))]
        warnings.extend(warns)

    ok, violations = validate_routing(instance, policy["routing"], severity_map)
    if violations:
        fails, warns = _split_violations(violations)
        if fails:
            violation = fails[0]
            return [build_violation_event(violation["code"], original=instance, details=violation.get("details"))]
        warnings.extend(warns)

    if instance.get("event", {}).get("event_type") == "COMMAND_EVENT":
        payload = instance.get("payload", {})
        task_id = payload.get("task_id")
        if task_id and dedupe_cache:
            ttl_ms = ttl_ms_from_payload(payload)
            if dedupe_cache.check_and_set(task_id, ttl_ms):
                return [build_duplicate_ack(instance)]

    outgoing = [instance]
    for warning in warnings:
        outgoing.append(build_warning_event(warning["code"], original=instance, details=warning.get("details")))
    return outgoing


def parse_args():
    parser = argparse.ArgumentParser(description="ZMeta minimal reference gateway")
    parser.add_argument("--profile", choices=["L", "M", "H"], required=True)
    parser.add_argument("--emit-cot", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    root = Path(__file__).resolve().parents[2]
    schema_path = root / "schema" / "zmeta-event-1.0.schema.json"
    policy_dir = root / "policy"

    validator = load_schema(schema_path)
    policy = load_policy(policy_dir)

    listen_addr = ("0.0.0.0", 5555)
    forward_addr = ("127.0.0.1", 5556)

    sock_in = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock_in.bind(listen_addr)
    sock_out = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    print(f"gateway listening on {listen_addr[0]}:{listen_addr[1]} (profile {args.profile})")
    print(f"forwarding to {forward_addr[0]}:{forward_addr[1]}")

    dedupe_cache = TaskDedupeCache()

    cot_addr = ("127.0.0.1", 6969)

    while True:
        data, _addr = sock_in.recvfrom(65535)
        out_events = process_message(data, validator, policy, args.profile, dedupe_cache)
        for outgoing in out_events:
            payload = json.dumps(outgoing, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
            sock_out.sendto(payload, forward_addr)
            if args.emit_cot:
                cot_xml = zmeta_to_cot(outgoing)
                if cot_xml:
                    sock_out.sendto(cot_xml.encode("utf-8"), cot_addr)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
