import argparse
import json
import socket
import subprocess
import sys
import time
from pathlib import Path


def build_args():
    parser = argparse.ArgumentParser(description="Live UDP test for gateway (dedupe + CoT)")
    parser.add_argument("--profile", default="H", choices=["L", "M", "H"])
    parser.add_argument("--listen-port", type=int, default=5575)
    parser.add_argument("--forward-port", type=int, default=5576)
    parser.add_argument("--cot-port", type=int, default=6970)
    parser.add_argument("--timeout", type=float, default=3.0)
    parser.add_argument("--no-cot", action="store_true", help="Skip CoT emission test")
    return parser.parse_args()


def recv_or_fail(sock, timeout_s, label):
    sock.settimeout(timeout_s)
    try:
        data, _addr = sock.recvfrom(65535)
    except TimeoutError as exc:
        raise SystemExit(f"Timed out waiting for {label}") from exc
    return data.decode("utf-8")


def main():
    args = build_args()
    root = Path(__file__).resolve().parents[1]
    cmd = [
        sys.executable,
        str(root / "gateway" / "src" / "gateway.py"),
        "--profile",
        args.profile,
        "--listen-port",
        str(args.listen_port),
        "--forward-port",
        str(args.forward_port),
    ]
    if not args.no_cot:
        cmd.extend(["--emit-cot", "--cot-port", str(args.cot_port)])

    proc = subprocess.Popen(cmd, cwd=str(root))
    try:
        time.sleep(1.0)

        cmd_event = {
            "zmeta_version": "1.0",
            "event": {
                "event_id": "22222222-2222-4333-8444-555555555555",
                "event_type": "COMMAND_EVENT",
                "event_subtype": "MISSION_TASK",
                "ts": "2025-01-17T14:31:00Z",
            },
            "source": {
                "platform_id": "comms-node-1",
                "node_role": "GATEWAY",
                "producer": "sensorops",
            },
            "payload": {
                "task_id": "task-20250117-0002",
                "task_type": "GOTO",
                "target_geo": {"lat": 34.0005, "lon": -118.0004},
                "valid_for_ms": 600000,
                "requires_deconfliction": True,
            },
        }

        state_event = {
            "zmeta_version": "1.0",
            "event": {
                "event_id": "33333333-2222-4333-8444-555555555555",
                "event_type": "STATE_EVENT",
                "event_subtype": "TRACK_STATE",
                "ts": "2025-01-17T14:31:05Z",
            },
            "source": {
                "platform_id": "fusion-node-01",
                "node_role": "GATEWAY",
                "producer": "fusion-engine",
            },
            "payload": {
                "track_id": "track-001",
                "geo": {"lat": 34.0524, "lon": -118.2435, "alt_m": 121.0},
                "valid_for_ms": 1500,
            },
            "confidence": 0.76,
            "lineage": {"based_on": ["22222222-2222-4333-8444-555555555555"]},
        }

        recv = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        recv.bind(("127.0.0.1", args.forward_port))

        cot_recv = None
        if not args.no_cot:
            cot_recv = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            cot_recv.bind(("127.0.0.1", args.cot_port))

        send = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Send command twice to trigger dedupe.
        send.sendto(json.dumps(cmd_event).encode("utf-8"), ("127.0.0.1", args.listen_port))
        print("forwarded-1", recv_or_fail(recv, args.timeout, "first command"))

        send.sendto(json.dumps(cmd_event).encode("utf-8"), ("127.0.0.1", args.listen_port))
        print("forwarded-2", recv_or_fail(recv, args.timeout, "dedupe ack"))

        if not args.no_cot:
            # Send state to generate CoT.
            send.sendto(json.dumps(state_event).encode("utf-8"), ("127.0.0.1", args.listen_port))
            print("forwarded-state", recv_or_fail(recv, args.timeout, "state forward"))
            print("cot", recv_or_fail(cot_recv, args.timeout, "cot output"))
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    main()
