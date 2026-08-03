import argparse
import json
from pathlib import Path


DEFAULTS = {
    "profile": "H",
    "listen_host": "0.0.0.0",
    "listen_port": 5555,
    "forward_host": "127.0.0.1",
    "forward_port": 5556,
    "emit_cot": False,
    "input_encoding": "json",
    "output_encoding": "json",
    "stamp_profile": True,
    "stamp_profile_profiles": ["L", "M", "H"],
    "stamp_timing": True,
    "stamp_timing_profiles": ["L", "M", "H"],
    "strip_optional_fields": [
        "source.sensor_id",
        "source.sw_version",
        "payload.data_ref",
        "payload.data_refs",
    ],
    "strip_optional_fields_profiles": ["L", "M", "H"],
    "strict_validation": False,
    "ts_plausibility_horizon_ms": 86400000,
    "emit_metrics": True,
    "metrics_interval_sec": 30,
    "rate_limit_per_sec": 0,
    "rate_limit_producer_per_sec": 0,
    "metrics_log_path": "",
    "metrics_log_max_bytes": 5000000,
    "metrics_log_backups": 3,
    "stamp_contract_hash": False,
    "require_schema_hash": "",
    "require_policy_hash": "",
    "require_contract_hash": "",
    "cot_host": "127.0.0.1",
    "cot_port": 6969,
    "schema_path": "schema/zmeta-event-1.0.schema.json",
    "policy_dir": "policy",
}


def prompt_text(label, default=None, choices=None):
    while True:
        suffix = f" [{default}]" if default is not None else ""
        value = input(f"{label}{suffix}: ").strip()
        if not value:
            value = default
        if choices and value not in choices:
            print(f"Choose one of: {', '.join(choices)}")
            continue
        if value is None:
            print("Value is required.")
            continue
        return value


def prompt_port(label, default):
    while True:
        value = prompt_text(label, str(default))
        try:
            port = int(value)
        except ValueError:
            print("Port must be an integer.")
            continue
        if not (1 <= port <= 65535):
            print("Port must be between 1 and 65535.")
            continue
        return port


def prompt_bool(label, default):
    default_value = "y" if default else "n"
    while True:
        value = input(f"{label} [y/n] (default {default_value}): ").strip().lower()
        if not value:
            return default
        if value in {"y", "yes"}:
            return True
        if value in {"n", "no"}:
            return False
        print("Enter y or n.")


def prompt_int(label, default, allow_zero=True):
    while True:
        value = prompt_text(label, str(default))
        try:
            number = int(value)
        except ValueError:
            print("Value must be an integer.")
            continue
        if number < 0 or (number == 0 and not allow_zero):
            print("Value must be positive.")
            continue
        return number


def parse_args():
    parser = argparse.ArgumentParser(description="ZMeta gateway config wizard")
    parser.add_argument("--output", default="gateway-config.json")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    output_path = Path(args.output)
    if output_path.exists() and not args.force:
        raise SystemExit(f"output already exists: {output_path} (use --force to overwrite)")

    profile = prompt_text("Profile (L/M/H)", DEFAULTS["profile"], choices=["L", "M", "H"])
    listen_host = prompt_text("Listen host", DEFAULTS["listen_host"])
    listen_port = prompt_port("Listen port", DEFAULTS["listen_port"])
    forward_host = prompt_text("Forward host", DEFAULTS["forward_host"])
    forward_port = prompt_port("Forward port", DEFAULTS["forward_port"])
    emit_cot = prompt_bool("Emit CoT", DEFAULTS["emit_cot"])
    input_encoding = prompt_text(
        "Input encoding (json/cbor/compact/proto/auto)",
        DEFAULTS["input_encoding"],
        choices=["json", "cbor", "compact", "proto", "auto"],
    )
    output_encoding = prompt_text(
        "Output encoding (json/cbor/compact/proto)",
        DEFAULTS["output_encoding"],
        choices=["json", "cbor", "compact", "proto"],
    )
    stamp_profile = prompt_bool("Stamp profile field", DEFAULTS["stamp_profile"])
    stamp_timing = prompt_bool("Stamp timing fields (t_receive/t_publish)", DEFAULTS["stamp_timing"])
    strip_optional_fields = prompt_bool(
        "Strip optional fields (sensor_id, sw_version, data_ref(s))",
        True,
    )
    strict_validation = prompt_bool("Strict validation (treat warnings as failures)", DEFAULTS["strict_validation"])
    ts_plausibility_horizon_ms = prompt_int(
        "Event ts plausibility horizon in ms, warn-only (0 disables)",
        DEFAULTS["ts_plausibility_horizon_ms"],
    )
    emit_metrics = prompt_bool("Emit metrics logs", DEFAULTS["emit_metrics"])
    metrics_interval_sec = prompt_int("Metrics interval (sec)", DEFAULTS["metrics_interval_sec"])
    rate_limit_per_sec = prompt_int("Rate limit per sec (0 = disabled)", DEFAULTS["rate_limit_per_sec"])
    rate_limit_producer_per_sec = prompt_int(
        "Per-producer rate limit per sec (0 = disabled)",
        DEFAULTS["rate_limit_producer_per_sec"],
    )
    metrics_log_path = prompt_text("Metrics log path (blank to disable)", DEFAULTS["metrics_log_path"])
    metrics_log_max_bytes = prompt_int("Metrics log max bytes", DEFAULTS["metrics_log_max_bytes"])
    metrics_log_backups = prompt_int("Metrics log backups", DEFAULTS["metrics_log_backups"])
    stamp_contract_hash = prompt_bool("Stamp contract hash on gateway system events", DEFAULTS["stamp_contract_hash"])
    require_schema_hash = prompt_text(
        "Require schema hash (blank to disable)", DEFAULTS["require_schema_hash"]
    )
    require_policy_hash = prompt_text(
        "Require policy hash (blank to disable)", DEFAULTS["require_policy_hash"]
    )
    require_contract_hash = prompt_text(
        "Require contract hash (blank to disable)", DEFAULTS["require_contract_hash"]
    )
    cot_host = prompt_text("CoT host", DEFAULTS["cot_host"])
    cot_port = prompt_port("CoT port", DEFAULTS["cot_port"])
    schema_path = prompt_text("Schema path", DEFAULTS["schema_path"])
    policy_dir = prompt_text("Policy dir", DEFAULTS["policy_dir"])

    config = {
        "profile": profile,
        "listen": {"host": listen_host, "port": listen_port},
        "forward": {"host": forward_host, "port": forward_port},
        "emit_cot": emit_cot,
        "input_encoding": input_encoding,
        "output_encoding": output_encoding,
        "stamp_profile": stamp_profile,
        "stamp_profile_profiles": DEFAULTS["stamp_profile_profiles"],
        "stamp_timing": stamp_timing,
        "stamp_timing_profiles": DEFAULTS["stamp_timing_profiles"],
        "strip_optional_fields": DEFAULTS["strip_optional_fields"] if strip_optional_fields else [],
        "strip_optional_fields_profiles": DEFAULTS["strip_optional_fields_profiles"],
        "strict_validation": strict_validation,
        "ts_plausibility_horizon_ms": ts_plausibility_horizon_ms,
        "emit_metrics": emit_metrics,
        "metrics_interval_sec": metrics_interval_sec,
        "rate_limit_per_sec": rate_limit_per_sec,
        "rate_limit_producer_per_sec": rate_limit_producer_per_sec,
        "metrics_log_path": metrics_log_path or None,
        "metrics_log_max_bytes": metrics_log_max_bytes,
        "metrics_log_backups": metrics_log_backups,
        "stamp_contract_hash": stamp_contract_hash,
        "require_schema_hash": require_schema_hash or None,
        "require_policy_hash": require_policy_hash or None,
        "require_contract_hash": require_contract_hash or None,
        "cot": {"host": cot_host, "port": cot_port},
        "schema_path": schema_path,
        "policy_dir": policy_dir,
    }

    output_path.write_text(json.dumps(config, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
