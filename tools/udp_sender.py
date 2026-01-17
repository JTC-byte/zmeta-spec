import argparse
import socket
import sys


def parse_args():
    parser = argparse.ArgumentParser(description="Simple UDP sender")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5555)
    parser.add_argument("--file", help="Path to a JSON/JSONL file to send")
    return parser.parse_args()


def read_payload(path):
    if path:
        with open(path, "r", encoding="utf-8") as handle:
            return handle.read().strip()
    return sys.stdin.read().strip()


def main():
    args = parse_args()
    payload = read_payload(args.file)
    if not payload:
        raise SystemExit("no payload provided")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(payload.encode("utf-8"), (args.host, args.port))


if __name__ == "__main__":
    main()
