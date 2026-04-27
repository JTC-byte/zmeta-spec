import argparse
import socket
import json
import sys
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
    parser = argparse.ArgumentParser(description="Simple UDP receiver")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5556)
    parser.add_argument("--encoding", choices=["json", "cbor", "compact", "proto", "auto"], default="json")
    return parser.parse_args()


def looks_like_event(obj):
    return isinstance(obj, dict) and {"event", "source", "payload"}.issubset(obj)


def main():
    args = parse_args()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((args.host, args.port))
    print(f"listening on {args.host}:{args.port}")
    while True:
        data, _addr = sock.recvfrom(65535)
        if args.encoding == "json":
            print(data.decode("utf-8", errors="replace"))
            continue
        if args.encoding == "cbor":
            if cbor2 is None and zmeta_cbor is None:
                raise SystemExit("CBOR support requires cbor2 or zmeta_cbor.")
            if cbor2 is not None:
                obj = cbor2.loads(data)
            else:
                obj = zmeta_cbor.loads(data)
            print(json.dumps(obj, separators=(",", ":"), ensure_ascii=True))
            continue
        if args.encoding == "compact":
            if zmeta_compact is None:
                raise SystemExit("Compact decoding requires zmeta_compact.")
            obj = zmeta_compact.loads(data)
            print(json.dumps(obj, separators=(",", ":"), ensure_ascii=True))
            continue
        if args.encoding == "proto":
            if zmeta_proto is None:
                raise SystemExit("Protobuf decoding requires zmeta_proto.")
            obj = zmeta_proto.loads(data)
            print(json.dumps(obj, separators=(",", ":"), ensure_ascii=True))
            continue
        # auto
        prefix = data.lstrip()[:1]
        if prefix in (b"{", b"["):
            print(data.decode("utf-8", errors="replace"))
            continue
        obj = None
        if cbor2 is not None or zmeta_cbor is not None:
            try:
                if cbor2 is not None:
                    decoded = cbor2.loads(data)
                else:
                    decoded = zmeta_cbor.loads(data)
                if zmeta_compact is not None and zmeta_compact.is_compact(decoded):
                    decoded = zmeta_compact.decode_event(decoded)
                if looks_like_event(decoded):
                    obj = decoded
            except Exception:
                obj = None
        if obj is None:
            if zmeta_proto is None:
                raise SystemExit("Auto decoding failed; protobuf support requires zmeta_proto.")
            obj = zmeta_proto.loads(data)
        print(json.dumps(obj, separators=(",", ":"), ensure_ascii=True))


if __name__ == "__main__":
    main()
