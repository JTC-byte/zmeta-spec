import argparse
import subprocess
import sys
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description="Run the ZMeta gateway")
    parser.add_argument("--config")
    parser.add_argument("--profile", choices=["L", "M", "H"])
    parser.add_argument("--emit-cot", action="store_true")
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
    raise SystemExit(subprocess.call(cmd))


if __name__ == "__main__":
    main()
