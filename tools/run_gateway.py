import argparse
import subprocess
import sys
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description="Run the ZMeta gateway")
    parser.add_argument("--config")
    parser.add_argument("--profile", choices=["L", "M", "H"])
    parser.add_argument("--emit-cot", action="store_true")
    parser.add_argument("--strict-validation", action="store_true")
    parser.add_argument("--metrics-interval-sec", type=int)
    parser.add_argument("--no-metrics", action="store_true")
    parser.add_argument("--rate-limit-per-sec", type=int)
    parser.add_argument("--rate-limit-producer-per-sec", type=int)
    parser.add_argument("--metrics-log-path")
    parser.add_argument("--metrics-log-max-bytes", type=int)
    parser.add_argument("--metrics-log-backups", type=int)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--stamp-contract-hash", action="store_true")
    parser.add_argument("--require-schema-hash")
    parser.add_argument("--require-policy-hash")
    parser.add_argument("--require-contract-hash")
    return parser.parse_args()


def main():
    args = parse_args()
    root = Path(__file__).resolve().parents[1]
    gateway_path = root / "gateway" / "src" / "gateway.py"
    cmd = [sys.executable, str(gateway_path)]
    if args.config:
        cmd.extend(["--config", args.config])
    if args.profile:
        cmd.extend(["--profile", args.profile])
    elif not args.config:
        cmd.extend(["--profile", "H"])
    if args.emit_cot:
        cmd.append("--emit-cot")
    if args.strict_validation:
        cmd.append("--strict-validation")
    if args.metrics_interval_sec is not None:
        cmd.extend(["--metrics-interval-sec", str(args.metrics_interval_sec)])
    if args.no_metrics:
        cmd.append("--no-metrics")
    if args.rate_limit_per_sec is not None:
        cmd.extend(["--rate-limit-per-sec", str(args.rate_limit_per_sec)])
    if args.rate_limit_producer_per_sec is not None:
        cmd.extend(["--rate-limit-producer-per-sec", str(args.rate_limit_producer_per_sec)])
    if args.metrics_log_path:
        cmd.extend(["--metrics-log-path", args.metrics_log_path])
    if args.metrics_log_max_bytes is not None:
        cmd.extend(["--metrics-log-max-bytes", str(args.metrics_log_max_bytes)])
    if args.metrics_log_backups is not None:
        cmd.extend(["--metrics-log-backups", str(args.metrics_log_backups)])
    if args.self_test:
        cmd.append("--self-test")
    if args.stamp_contract_hash:
        cmd.append("--stamp-contract-hash")
    if args.require_schema_hash:
        cmd.extend(["--require-schema-hash", args.require_schema_hash])
    if args.require_policy_hash:
        cmd.extend(["--require-policy-hash", args.require_policy_hash])
    if args.require_contract_hash:
        cmd.extend(["--require-contract-hash", args.require_contract_hash])
    raise SystemExit(subprocess.call(cmd))


if __name__ == "__main__":
    main()
