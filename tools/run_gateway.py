import argparse
import subprocess
import sys
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description="Run the ZMeta gateway")
    parser.add_argument("--profile", choices=["L", "M", "H"], default="H")
    return parser.parse_args()


def main():
    args = parse_args()
    root = Path(__file__).resolve().parents[1]
    gateway_path = root / "gateway" / "src" / "gateway.py"
    cmd = [sys.executable, str(gateway_path), "--profile", args.profile]
    raise SystemExit(subprocess.call(cmd))


if __name__ == "__main__":
    main()
