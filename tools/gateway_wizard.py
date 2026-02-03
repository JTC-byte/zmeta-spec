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
    cot_host = prompt_text("CoT host", DEFAULTS["cot_host"])
    cot_port = prompt_port("CoT port", DEFAULTS["cot_port"])
    schema_path = prompt_text("Schema path", DEFAULTS["schema_path"])
    policy_dir = prompt_text("Policy dir", DEFAULTS["policy_dir"])

    config = {
        "profile": profile,
        "listen": {"host": listen_host, "port": listen_port},
        "forward": {"host": forward_host, "port": forward_port},
        "emit_cot": emit_cot,
        "cot": {"host": cot_host, "port": cot_port},
        "schema_path": schema_path,
        "policy_dir": policy_dir,
    }

    output_path.write_text(json.dumps(config, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
