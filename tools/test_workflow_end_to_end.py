import argparse
import json
import socket
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from zmeta_uuid import uuid7


def build_args():
    parser = argparse.ArgumentParser(
        description="End-to-end workflow test: sensor -> ZMeta -> gateway -> CoT"
    )
    parser.add_argument("--profile", default="H", choices=["L", "M", "H"])
    parser.add_argument("--listen-port", type=int, default=5585)
    parser.add_argument("--forward-port", type=int, default=5586)
    parser.add_argument("--cot-port", type=int, default=6980)
    parser.add_argument("--timeout", type=float, default=3.0)
    parser.add_argument("--no-cot", action="store_true", help="Skip CoT output check")
    parser.add_argument(
        "--expect",
        default="",
        help="Comma-separated extra events to include/expect (COMMAND_EVENT,SYSTEM_EVENT)",
    )
    return parser.parse_args()


def _send(sock, host, port, obj):
    payload = json.dumps(obj, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    sock.sendto(payload, (host, port))


def _recv(sock, timeout=3.0):
    sock.settimeout(timeout)
    data, _addr = sock.recvfrom(65535)
    return data


def _parse_expect(value):
    tokens = [token.strip().upper() for token in (value or "").split(",") if token.strip()]
    supported = {"COMMAND_EVENT", "SYSTEM_EVENT"}
    invalid = [token for token in tokens if token not in supported]
    if invalid:
        raise ValueError(f"unsupported --expect values: {invalid}")
    return set(tokens)


def _build_events(profile, expect):
    obs_id = str(uuid7())
    inf_id = str(uuid7())
    fus_id = str(uuid7())
    state_id = str(uuid7())
    cmd_id = str(uuid7())
    sys_id = str(uuid7())

    observation = {
        "zmeta_version": "1.0",
        "event": {
            "event_id": obs_id,
            "event_type": "OBSERVATION_EVENT",
            "event_subtype": "RF_OBSERVATION",
            "ts": "2025-01-17T14:30:00Z",
        },
        "source": {"platform_id": "sensor-node-01", "node_role": "EDGE", "producer": "rf-sensor"},
        "payload": {
            "modality": "RF",
            "features": {
                "center_freq_hz": 2450000000,
                "bandwidth_hz": 20000000,
                "power_dbm": -35.2,
            },
            "geo": {"lat": 34.0522, "lon": -118.2437, "alt_m": 120.5},
        },
    }

    inference = {
        "zmeta_version": "1.0",
        "event": {
            "event_id": inf_id,
            "event_type": "INFERENCE_EVENT",
            "event_subtype": "CLASSIFICATION",
            "ts": "2025-01-17T14:30:02Z",
        },
        "source": {"platform_id": "edge-analytics-01", "node_role": "GATEWAY", "producer": "torch"},
        "payload": {
            "inference_type": "CLASSIFICATION",
            "claim": {"label": "drone"},
            "model": {"name": "rf-classifier", "version": "1.0.0"},
            "based_on": [obs_id],
        },
        "confidence": 0.82,
        "lineage": {"based_on": [obs_id]},
    }

    fusion = {
        "zmeta_version": "1.0",
        "event": {
            "event_id": fus_id,
            "event_type": "FUSION_EVENT",
            "event_subtype": "TRACK_FUSION",
            "ts": "2025-01-17T14:30:04Z",
        },
        "source": {"platform_id": "fusion-node-01", "node_role": "GATEWAY", "producer": "torch"},
        "payload": {
            "track_id": "track-001",
            "members": [obs_id],
            "stability": 0.6,
            "last_seen_ts": "2025-01-17T14:30:03Z",
        },
        "confidence": 0.75,
        "lineage": {"based_on": [inf_id]},
    }

    state_producer = "sensorops" if profile == "L" else "torch"
    state_platform = "edge-node-01" if profile == "L" else "fusion-node-01"
    state = {
        "zmeta_version": "1.0",
        "event": {
            "event_id": state_id,
            "event_type": "STATE_EVENT",
            "event_subtype": "TRACK_STATE",
            "ts": "2025-01-17T14:30:05Z",
        },
        "source": {"platform_id": state_platform, "node_role": "GATEWAY", "producer": state_producer},
        "payload": {
            "track_id": "track-001",
            "geo": {"lat": 34.0524, "lon": -118.2435, "alt_m": 121.0},
            "valid_for_ms": 1500,
        },
        "confidence": 0.7,
        "lineage": {"based_on": [fus_id]},
    }

    command = {
        "zmeta_version": "1.0",
        "event": {
            "event_id": cmd_id,
            "event_type": "COMMAND_EVENT",
            "event_subtype": "MISSION_TASK",
            "ts": "2025-01-17T14:30:06Z",
        },
        "source": {"platform_id": "comms-node-1", "node_role": "GATEWAY", "producer": "sensorops"},
        "payload": {
            "task_id": "task-e2e-0001",
            "task_type": "GOTO",
            "target_geo": {"lat": 34.0525, "lon": -118.2436},
            "valid_for_ms": 600000,
            "requires_deconfliction": True,
        },
    }

    system = {
        "zmeta_version": "1.0",
        "event": {
            "event_id": sys_id,
            "event_type": "SYSTEM_EVENT",
            "event_subtype": "LINK_STATUS",
            "ts": "2025-01-17T14:30:06Z",
        },
        "source": {"platform_id": "sensor-node-01", "node_role": "EDGE", "producer": "rf-sensor"},
        "payload": {"system_type": "LINK_STATUS", "state": "DEGRADED", "metrics": {"rssi_dbm": -98.2}},
    }

    extras = []
    if "COMMAND_EVENT" in expect:
        extras.append(command)
    if "SYSTEM_EVENT" in expect:
        extras.append(system)

    if profile == "H":
        return [observation, inference, fusion, state] + extras
    if profile == "M":
        # Inference exists internally but is not exported under Profile M.
        return [observation, fusion, state] + extras
    if profile == "L":
        # Only export belief-state; lineage may reference non-exported events.
        return [state] + extras
    raise ValueError(f"unsupported profile: {profile}")


def main():
    args = build_args()
    cmd = [
        sys.executable,
        "gateway/src/gateway.py",
        "--profile",
        args.profile,
        "--listen-port",
        str(args.listen_port),
        "--forward-port",
        str(args.forward_port),
    ]
    if not args.no_cot:
        cmd.extend(["--emit-cot", "--cot-port", str(args.cot_port)])

    proc = subprocess.Popen(cmd, cwd=".")
    try:
        time.sleep(1.0)

        recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        recv_sock.bind(("127.0.0.1", args.forward_port))

        cot_sock = None
        if not args.no_cot:
            cot_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            cot_sock.bind(("127.0.0.1", args.cot_port))

        send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        expect = _parse_expect(args.expect)
        events = _build_events(args.profile, expect)

        for event in events:
            _send(send_sock, "127.0.0.1", args.listen_port, event)

        forwarded = []
        for _ in range(len(events)):
            data = _recv(recv_sock, args.timeout)
            forwarded.append(json.loads(data.decode("utf-8")))

        forwarded_types = [e["event"]["event_type"] for e in forwarded]
        expected_types = [e["event"]["event_type"] for e in events]
        if Counter(forwarded_types) != Counter(expected_types):
            raise SystemExit(
                f"forwarded types mismatch: expected={expected_types} got={forwarded_types}"
            )

        cot_xml = None
        if cot_sock is not None:
            cot_xml = _recv(cot_sock, args.timeout).decode("utf-8")

        print("Forwarded event types:", forwarded_types)
        if cot_sock is not None and not cot_xml:
            raise SystemExit("expected CoT output but none received")
        if cot_xml:
            print("CoT output (truncated):", cot_xml[:160])
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    main()
