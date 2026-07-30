"""Single-node throughput simulation.

Measures what one gateway sustains on this host, and where anything missing
went. See tools/sim/README.md for scope: this is an operational harness and
nothing governed may depend on it.

Four independent counts are reported, because agreeing on one number is the only
way to tell a clean run from a lossy one:

  sent  what the generator put on the wire
  recv  what the gateway says it received, from its own metrics
  fwd   what the gateway says it forwarded
  sink  what a separate socket actually received downstream

sent > recv is loss upstream of the process, in the kernel receive buffer. The
gateway cannot see it and does not count it, so `drops=0` is true and does not
mean nothing was lost. recv > fwd is refusal, and violations says why.
fwd > sink is loss downstream.
"""

import argparse
import json
import re
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from zmeta_uuid import uuid7  # noqa: E402

EXIT_PASS = 0
EXIT_INVALID = 2

METRIC_RE = re.compile(r"recv=(?P<recv>\d+) bytes=(?P<bytes>\d+) fwd=(?P<fwd>\d+)")


class CountingSink:
    def __init__(self, port):
        self.port = port
        self.count = 0
        self.bytes = 0
        self.bound = False
        self.bind_error = None
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
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 8 * 1024 * 1024)
            sock.bind(("127.0.0.1", self.port))
        except OSError as exc:
            self.bind_error = str(exc)
            return
        sock.settimeout(0.3)
        self.bound = True
        while not self._stop.is_set():
            try:
                data, _ = sock.recvfrom(65535)
            except socket.timeout:
                continue
            except OSError:
                break
            self.count += 1
            self.bytes += len(data)
        sock.close()

    def stop(self):
        self._stop.set()
        self._thread.join(timeout=3)


def pick_template(corpus_path):
    """A self-contained event, so the load carries no unresolved lineage.

    Lineage parents that never arrive produce warnings that have nothing to do
    with capacity and would muddy every count in the report.
    """
    for line in corpus_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        obj = json.loads(line)
        if (obj.get("event") or {}).get("event_type") == "OBSERVATION_EVENT" and not obj.get("lineage"):
            return obj
    for line in corpus_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            return json.loads(line)
    return None


def parse_args():
    p = argparse.ArgumentParser(
        description="Push load through one gateway and report where anything missing went.")
    p.add_argument("--corpus", default="examples/zmeta-profile-H-examples.jsonl")
    p.add_argument("--events", type=int, default=2000)
    p.add_argument("--rate", type=float, default=200.0,
                   help="target events/sec; 0 means as fast as the sender can go")
    p.add_argument("--listen", type=int, default=15561)
    p.add_argument("--consumer", type=int, default=15562)
    p.add_argument("--profile", default="H", choices=["L", "M", "H"])
    return p.parse_args()


def main():
    args = parse_args()
    corpus = Path(args.corpus)
    if not corpus.is_absolute():
        corpus = ROOT / args.corpus
    if not corpus.is_file():
        print(f"VERDICT: INVALID - corpus not found: {corpus}")
        return EXIT_INVALID
    template = pick_template(corpus)
    if template is None:
        print(f"VERDICT: INVALID - no usable event in {corpus}")
        return EXIT_INVALID

    sink = CountingSink(args.consumer)
    sink.start()
    if not sink.bound:
        print(f"VERDICT: INVALID - sink did not bind: {sink.bind_error}")
        return EXIT_INVALID

    lines = []
    proc = subprocess.Popen(
        [sys.executable, "-u", str(ROOT / "gateway" / "src" / "gateway.py"),
         "--profile", args.profile,
         "--listen-host", "127.0.0.1", "--listen-port", str(args.listen),
         "--forward-host", "127.0.0.1", "--forward-port", str(args.consumer),
         "--input-encoding", "auto", "--output-encoding", "compact",
         "--no-emit-cot", "--metrics-interval-sec", "1"],
        cwd=str(ROOT), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1,
    )
    threading.Thread(
        target=lambda: [lines.append(ln.rstrip()) for ln in proc.stdout], daemon=True
    ).start()

    try:
        deadline = time.time() + 30
        while time.time() < deadline and not any("gateway listening" in ln for ln in lines):
            if proc.poll() is not None:
                print("VERDICT: INVALID - gateway exited:\n" + "\n".join(lines[-10:]))
                return EXIT_INVALID
            time.sleep(0.05)
        time.sleep(0.3)

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 4 * 1024 * 1024)
        addr = ("127.0.0.1", args.listen)
        interval = 1.0 / args.rate if args.rate > 0 else 0.0
        sent = 0
        start = time.perf_counter()
        next_at = start
        for _ in range(args.events):
            # A fresh event_id per event, as a real producer mints. Re-sending an
            # id is deduplicated, so a generator that cycles a corpus verbatim
            # measures dedupe rather than capacity.
            event = json.loads(json.dumps(template))
            event["event"]["event_id"] = str(uuid7())
            sock.sendto(json.dumps(event, separators=(",", ":")).encode("utf-8"), addr)
            sent += 1
            if interval:
                next_at += interval
                slack = next_at - time.perf_counter()
                if slack > 0:
                    time.sleep(slack)
        elapsed = time.perf_counter() - start
        sock.close()
        time.sleep(2.5)
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        time.sleep(0.3)
        sink.stop()

    windows = [ln for ln in lines if "recv=" in ln]
    last = None
    for ln in windows:
        match = METRIC_RE.search(ln)
        if match:
            last = {k: int(v) for k, v in match.groupdict().items()}

    print(f"corpus          {corpus.name} (one self-contained template, fresh event_id per send)")
    print(f"offered         sent={sent} in {elapsed:.3f}s = {sent / elapsed:,.0f} events/sec")
    print(f"sink            received={sink.count} ({sink.bytes:,} bytes, "
          f"{sink.bytes / max(sink.count, 1):.0f} B/event)")
    if last:
        print(f"gateway window  recv={last['recv']} fwd={last['fwd']} bytes={last['bytes']}")
    else:
        print("gateway window  NONE PRINTED (metrics are emitted from the datagram "
              "path, so a short or slow run may produce none)")
    print(f"metrics windows {len(windows)}")
    for ln in windows[-2:]:
        print("  M| " + ln)

    delivered = 100.0 * sink.count / sent if sent else 0.0
    print(f"end-to-end      {delivered:.1f}% of offered load")
    if delivered < 99.0:
        print("  the shortfall is upstream of the gateway if its own drops counter "
              "reads 0: the kernel discarded datagrams the process never saw")
    return EXIT_PASS


if __name__ == "__main__":
    sys.exit(main())
