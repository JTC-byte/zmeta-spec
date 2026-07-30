"""Two-node wire-path simulation.

Stands up an edge gateway and a GCS gateway, replays a corpus into the edge, and
reports what actually arrived downstream. See tools/sim/README.md for scope: this
is an operational harness and nothing governed may depend on it.

The design constraint is that a dead harness and a clean run must not look the
same. Every sink reports whether it bound and what it saw, every node reports
whether it started, and --control runs the whole thing with the edge node
deliberately absent so the zero case is measured rather than assumed.
"""

import argparse
import json
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

EXIT_PASS = 0
EXIT_FAIL = 1
EXIT_INVALID = 2


class Sink:
    """A UDP listener that records what it received and whether it ever bound."""

    def __init__(self, name, port):
        self.name = name
        self.port = port
        self.bound = False
        self.bind_error = None
        self.datagrams = []
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self._thread.start()
        for _ in range(200):
            if self.bound or self.bind_error:
                return
            time.sleep(0.01)

    def _run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.bind(("127.0.0.1", self.port))
        except OSError as exc:
            self.bind_error = str(exc)
            return
        sock.settimeout(0.2)
        self.bound = True
        while not self._stop.is_set():
            try:
                data, _ = sock.recvfrom(65535)
            except socket.timeout:
                continue
            except OSError as exc:
                self.bind_error = f"recv failed: {exc}"
                break
            self.datagrams.append(data)
        sock.close()

    def stop(self):
        self._stop.set()
        self._thread.join(timeout=3)

    def events(self):
        out = []
        for raw in self.datagrams:
            try:
                obj = json.loads(raw.decode("utf-8"))
            except Exception:
                continue
            if isinstance(obj, dict):
                out.append(obj)
        return out


class Node:
    """One gateway subprocess, with its stdout captured."""

    def __init__(self, name, args):
        self.name = name
        self.args = args
        self.proc = None
        self.lines = []
        self._thread = None

    def start(self, wait_for="gateway listening on", timeout=30):
        # -u matches deploy/*/docker-compose.yml. Without it the startup banner
        # sits in a block-buffered pipe and a live gateway reads as a dead one.
        cmd = [sys.executable, "-u", str(ROOT / "gateway" / "src" / "gateway.py")] + self.args
        self.proc = subprocess.Popen(
            cmd, cwd=str(ROOT), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1,
        )
        self._thread = threading.Thread(target=self._pump, daemon=True)
        self._thread.start()
        deadline = time.time() + timeout
        while time.time() < deadline:
            if any(wait_for in ln for ln in self.lines):
                return True
            if self.proc.poll() is not None:
                return False
            time.sleep(0.05)
        return False

    def _pump(self):
        for line in self.proc.stdout:
            self.lines.append(line.rstrip("\n"))

    def stop(self):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        if self._thread:
            self._thread.join(timeout=3)

    def hashes(self):
        out = {}
        for ln in self.lines:
            for key in ("schema_hash", "policy_hash", "semantics_hash", "contract_hash"):
                if ln.startswith(key + "="):
                    out[key] = ln.split("=", 1)[1]
        return out


def event_id(obj):
    return ((obj.get("event") or {}) if isinstance(obj, dict) else {}).get("event_id")


def reason_codes(payload):
    """Collect diagnostic reason codes wherever they sit in the payload."""
    found = []

    def walk(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if key in ("reason_code", "code", "violation", "reason") and isinstance(value, str):
                    found.append(value)
                else:
                    walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(payload)
    return sorted(set(found))


def replay(corpus, host, port, delay_ms):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sent = []
    for line in Path(corpus).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        sock.sendto(line.encode("utf-8"), (host, port))
        sent.append(event_id(json.loads(line)))
        time.sleep(delay_ms / 1000.0)
    sock.close()
    return sent


def parse_args():
    p = argparse.ArgumentParser(
        description="Replay a corpus through an edge node and a GCS node, and "
                    "report what actually arrived.",
        epilog="Run --control first. It must report zero, or no other run means anything.",
    )
    p.add_argument("--corpus", default="examples/zmeta-examples-1.0.jsonl",
                   help="JSONL of ZMeta events; absolute, or relative to the repo root")
    p.add_argument("--edge-profile", default="H", choices=["L", "M", "H"])
    p.add_argument("--gcs-profile", default="H", choices=["L", "M", "H"],
                   help="set this different from --edge-profile to exercise a mismatched pair")
    p.add_argument("--edge-listen", type=int, default=15555)
    p.add_argument("--gcs-listen", type=int, default=15556)
    p.add_argument("--consumer", type=int, default=15557)
    p.add_argument("--cot", type=int, default=16969)
    p.add_argument("--delay-ms", type=int, default=40)
    p.add_argument("--settle", type=float, default=2.5,
                   help="seconds to wait after the last event before counting")
    p.add_argument("--control", action="store_true",
                   help="do not start the edge node; downstream MUST observe zero")
    p.add_argument("--show-cot", action="store_true",
                   help="print the CoT XML captured off the egress port")
    p.add_argument("--verbose", action="store_true", help="print both node logs")
    return p.parse_args()


def main():
    args = parse_args()
    corpus = Path(args.corpus)
    if not corpus.is_absolute():
        corpus = ROOT / args.corpus
    if not corpus.is_file():
        print(f"VERDICT: INVALID - corpus not found: {corpus}")
        return EXIT_INVALID

    print(f"# two-node wire path   control={args.control}")
    print(f"# corpus={corpus.name} edge_profile={args.edge_profile} gcs_profile={args.gcs_profile}")

    consumer = Sink("consumer", args.consumer)
    cot = Sink("cot", args.cot)
    consumer.start()
    cot.start()
    print(f"sink consumer   port={args.consumer} bound={consumer.bound} err={consumer.bind_error}")
    print(f"sink cot        port={args.cot} bound={cot.bound} err={cot.bind_error}")
    if not consumer.bound or not cot.bound:
        consumer.stop()
        cot.stop()
        print("VERDICT: INVALID - a sink failed to bind, so any count would be meaningless")
        return EXIT_INVALID

    gcs = Node("gcs", [
        "--profile", args.gcs_profile,
        "--listen-host", "127.0.0.1", "--listen-port", str(args.gcs_listen),
        "--forward-host", "127.0.0.1", "--forward-port", str(args.consumer),
        "--input-encoding", "auto", "--output-encoding", "json",
        "--emit-cot", "--cot-host", "127.0.0.1", "--cot-port", str(args.cot),
        "--metrics-interval-sec", "1",
    ])
    edge = None
    sent = []
    try:
        if not gcs.start():
            print("\n".join(gcs.lines[-15:]))
            print("VERDICT: INVALID - the GCS node did not come up")
            return EXIT_INVALID
        print("node gcs        started=True")

        if args.control:
            print("node edge       started=False (control run, deliberately absent)")
        else:
            edge = Node("edge", [
                "--profile", args.edge_profile,
                "--listen-host", "127.0.0.1", "--listen-port", str(args.edge_listen),
                "--forward-host", "127.0.0.1", "--forward-port", str(args.gcs_listen),
                "--input-encoding", "auto", "--output-encoding", "compact",
                "--no-emit-cot", "--metrics-interval-sec", "1",
            ])
            if not edge.start():
                print("\n".join(edge.lines[-15:]))
                print("VERDICT: INVALID - the edge node did not come up")
                return EXIT_INVALID
            print("node edge       started=True")

        time.sleep(0.5)
        sent = replay(str(corpus), "127.0.0.1", args.edge_listen, args.delay_ms)
        print(f"replay          sent={len(sent)} into 127.0.0.1:{args.edge_listen}")
        time.sleep(args.settle)
    finally:
        if edge:
            edge.stop()
        gcs.stop()
        time.sleep(0.3)
        consumer.stop()
        cot.stop()

    received = consumer.events()
    forwarded = [e for e in received
                 if (e.get("event") or {}).get("event_subtype") != "SCHEMA_VIOLATION"]
    diagnostics = [e for e in received
                   if (e.get("event") or {}).get("event_subtype") == "SCHEMA_VIOLATION"]

    print(f"observed        consumer={len(received)} forwarded={len(forwarded)} "
          f"diagnostics={len(diagnostics)} cot={len(cot.datagrams)}")
    for e in forwarded:
        ev = e.get("event") or {}
        pl = e.get("payload") or {}
        print(f"  fwd  {ev.get('event_type')}/{ev.get('event_subtype')} "
              f"geo={'yes' if pl.get('geo') else 'no'} id={ev.get('event_id')}")
    for e in diagnostics:
        print(f"  diag SCHEMA_VIOLATION reasons={reason_codes(e.get('payload') or {})}")
    if args.show_cot:
        for raw in cot.datagrams:
            for line in raw.decode("utf-8", "replace").splitlines():
                print("  cot| " + line)

    if args.control:
        clean = not consumer.datagrams and not cot.datagrams
        print("VERDICT: " + ("CONTROL CLEAN - the ports are quiet, other runs can be believed"
                            if clean else
                            "CONTROL DIRTY - something else is feeding these ports"))
        return EXIT_PASS if clean else EXIT_FAIL

    if edge:
        edge_h, gcs_h = edge.hashes(), gcs.hashes()
        agree = bool(edge_h) and edge_h == gcs_h
        print(f"hashes_match    {agree}")
        if not agree:
            print(f"  edge {edge_h}")
            print(f"  gcs  {gcs_h}")
        if args.verbose:
            for ln in edge.lines:
                print("  E| " + ln)
            for ln in gcs.lines:
                print("  G| " + ln)

    delivered = [event_id(e) for e in forwarded]
    ok = len(delivered) == len(sent) and set(delivered) == set(sent)
    print(f"VERDICT: delivery={'PASS' if ok else 'FAIL'} "
          f"({len(delivered)}/{len(sent)} events) cot_emitted={len(cot.datagrams)}")
    if not ok and diagnostics:
        print("  note: events were refused rather than lost; the reason codes above say why")
    return EXIT_PASS if ok else EXIT_FAIL


if __name__ == "__main__":
    sys.exit(main())
