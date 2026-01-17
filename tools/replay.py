import argparse
import json
import socket
import time


def parse_args():
    parser = argparse.ArgumentParser(description="Replay ZMeta JSONL over UDP")
    parser.add_argument("--file", default="examples/zmeta-examples-1.0.jsonl")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5555)
    parser.add_argument("--delay-ms", type=int, default=200)
    parser.add_argument("--loop", action="store_true")
    parser.add_argument("--count", type=int)
    return parser.parse_args()


def iter_messages(path):
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            yield line


def main():
    args = parse_args()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sent = 0

    while True:
        for raw in iter_messages(args.file):
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue

            event = msg.get("event", {})
            event_type = event.get("event_type", "UNKNOWN")
            event_subtype = event.get("event_subtype", "UNKNOWN")
            event_id = event.get("event_id", "UNKNOWN")

            sock.sendto(raw.encode("utf-8"), (args.host, args.port))
            print(f"{event_type} {event_subtype} {event_id}")

            sent += 1
            if args.count is not None and sent >= args.count:
                return

            if args.delay_ms > 0:
                time.sleep(args.delay_ms / 1000.0)

        if not args.loop:
            break


if __name__ == "__main__":
    main()
