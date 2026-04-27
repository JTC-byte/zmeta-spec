import argparse
import socket
import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    import cbor2
except ImportError:  # pragma: no cover - optional dependency
    cbor2 = None

try:
    import zmeta_cbor
except ImportError:  # pragma: no cover - optional dependency
    zmeta_cbor = None

try:
    import zmeta_compact
except ImportError:  # pragma: no cover - optional dependency
    zmeta_compact = None

try:
    import zmeta_proto
except ImportError:  # pragma: no cover - optional dependency
    zmeta_proto = None


def parse_args():
    parser = argparse.ArgumentParser(description="Simple UDP sender")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5555)
    parser.add_argument("--file", help="Path to a JSON/JSONL file to send")
    parser.add_argument("--encoding", choices=["json", "cbor", "compact", "proto"], default="json")
    return parser.parse_args()


def read_payload(path):
    if path:
        with open(path, "r", encoding="utf-8") as handle:
            return handle.read().strip()
    return sys.stdin.read().strip()


def iter_payloads(payload):
    lines = [line.strip() for line in payload.splitlines() if line.strip()]
    if len(lines) > 1:
        return lines
    return [payload]


def encode_payload(raw, encoding):
    if encoding == "json":
        return raw.encode("utf-8")

    try:
        obj = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid JSON for {encoding.upper()} encoding: {exc}") from exc

    if encoding == "compact":
        if zmeta_compact is None:
            raise SystemExit("Compact encoding requires zmeta_compact.")
        return zmeta_compact.dumps(obj)

    if encoding == "proto":
        if zmeta_proto is None:
            raise SystemExit("Protobuf encoding requires zmeta_proto.")
        return zmeta_proto.dumps(obj)

    if cbor2 is None and zmeta_cbor is None:
        raise SystemExit("CBOR support requires cbor2 or zmeta_cbor.")
    if cbor2 is not None:
        return cbor2.dumps(obj, canonical=True)
    return zmeta_cbor.dumps(obj)


def main():
    args = parse_args()
    payload = read_payload(args.file)
    if not payload:
        raise SystemExit("no payload provided")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sent = 0
    for raw in iter_payloads(payload):
        sock.sendto(encode_payload(raw, args.encoding), (args.host, args.port))
        sent += 1
    print(f"sent={sent}")


if __name__ == "__main__":
    main()
