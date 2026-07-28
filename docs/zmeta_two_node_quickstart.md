# ZMeta Two-Node Quickstart — Sensor Edge to COP

**Advisory (Docs/advisory change class). Non-normative.** The fastest path
from "a sensor emitting native records" to "honest tracks on a COP":
one gateway container beside the sensor, one at the consumption edge, ZMeta
on the wire between them. Everything here uses the stock configs and
containers in this repository; nothing needs to be built.

## The topology

```
 [sensor] --native--> [adapter] --ZMeta/JSON--> [EDGE gateway]      (sensor host / Raspberry Pi)
                                                     |
                                          ZMeta compact (Profile L)
                                                     v
 (any relay node: forward the ZMeta datagram verbatim -- never translate)
                                                     v
                                            [GCS gateway]           (GCS computer / big-compute node)
                                             |            |
                                     ZMeta/JSON out   CoT out --> TAK / COP
                                     (fusion, SAPIENT egress, tools)
```

Two rules carry the whole design:

1. **The canonical ZMeta event is the source of truth; every egress is a
   lossy projection** (design gate 4). Translate to CoT/SAPIENT only at the
   node that consumes it. A relay that "helpfully" translates mid-path
   destroys authority for every node downstream.
2. **Nothing is fabricated.** Every honesty behavior in this guide
   (omitted pedigrees, refused geo, degraded-timing labels) is the system
   working, not breaking. The observability table at the end says where to
   look instead of guessing.

## Node A — the sensor edge (host or Raspberry Pi)

The edge gateway ingests adapter output (JSON), validates it against the
locked kernel, and forwards **compact Profile L** — the bandwidth shape
(measured max 150 bytes against a 240-byte budget for the Profile L corpus).

```bash
cd deploy/edge
# Edit ../../configs/edge-config.json FIRST -- two fields, both required:
#   forward.host : the GCS (or next-hop) address; the shipped placeholder
#                  is the literal string GATEWAY_HOST, which resolves to
#                  nothing
#   forward.port : 5555, NOT the shipped 5556
# Why the port edit: the shipped 5556 is the LOCAL-CONSUMER port (what a
# gateway forwards to on its own host, where tools/udp_receiver.py sits).
# The GCS gateway LISTENS on 5555, and deploy/gateway/docker-compose.yml
# publishes 5555/udp and 6969/udp only -- so edge datagrams sent to
# GCS:5556 arrive nowhere, silently. Node-to-node always targets the
# receiving node's listen port.
docker compose up -d
docker compose logs -f   # wait for: gateway listening on 0.0.0.0:5555
```

The stock `configs/edge-config.json` is already the sensor-side shape:
Profile L, `input_encoding: auto` (JSON or compact in), compact out, CoT
off, failure-mode handling on.

**Raspberry Pi / ARM64.** The compose files use the multi-arch
`python:3.13-slim` image, so the same file runs unmodified on a Pi.
Verified 2026-07-27 under QEMU arm64 emulation (`--platform linux/arm64`):
all dependencies install from wheels, the gateway starts and processes the
example corpus with zero violations, and the schema/policy/semantics/
contract hashes printed at startup are **byte-identical to the x86 run** —
same kernel, any architecture. (On that wheel set, `cbor2` resolves to its
pure-Python build; both codec backends are first-class and cross-pinned in
the test suite.) Real-hardware throughput on a Pi is the one thing
emulation does not measure — re-run the replay smoke below when hardware
arrives.

Point your adapter at the edge gateway: `--host 127.0.0.1 --port 5555`
(UDP, one JSON event per datagram). Building the adapter is the
one-sitting exercise documented in `adapters/AUTHORING.md`; the
`adapters/ingress/bladerf/` reference plus its mapping pack is the worked
RF example, and `adapters/ingress/example-vendor/` is the teaching one.

## Node B — the GCS / consumption edge

```bash
cd deploy/gateway
docker compose up -d
```

The stock `configs/gateway-config.json` is the receive shape: Profile H,
listening on **5555** (this is the port the edge node must forward to),
`input_encoding: auto` (accepts the edge's compact datagrams directly),
JSON out to local consumers on **5556** (same-host consumers: your fusion
process, `tools/udp_receiver.py`, the SAPIENT/JREAP projections), CoT out
to `cot.host:cot.port` (default 127.0.0.1:6969 — point it at your TAK
input).

Port summary, because the two 555x numbers are easy to transpose:

| Port | Who binds it | Who sends to it |
|---|---|---|
| 5555/udp | both gateways (`listen`) | the upstream node — adapter → edge, edge → GCS |
| 5556/udp | nothing (a destination) | each gateway's own `forward`, for **same-host** consumers |
| 6969/udp | your TAK/COP input | the GCS gateway's CoT egress |

**To see error ellipses and position pedigree on TAK, you must assert your
position source.** The projection never stamps `geopointsrc`/`altsrc`/`how`
it cannot prove — unasserted, the `<precisionlocation>` ellipse detail and
`how` attribute are *omitted by design*, and tracks still render with the
conservative circular error. The deployment operator, who knows how the
node derives positions, asserts it in the config:

```json
"cot": {
  "host": "TAK_HOST",
  "port": 6969,
  "config": { "geopointsrc": "GPS", "altsrc": "GPS", "how": "m-g" }
}
```

If a track's position is an RF-triangulated fusion product rather than a
GPS fix, do **not** assert `"GPS"` — that is exactly the lie the omission
default exists to prevent.

**SAPIENT egress** is adapter-level, not gateway-built-in: consume the
gateway's JSON output (port 5556) and project with
`adapters/egress/sapient/zmeta_state_to_sapient_detection.py` (wire-shape
validated against the official Dstl Apex tooling). Same pattern for
JREAP/KLV.

## Wire check (five minutes, run it before the event)

From the repo root on any host that can reach the nodes:

```bash
# 1. ON THE GCS HOST: watch what its gateway forwards to local consumers
python tools/udp_receiver.py --host 127.0.0.1 --port 5556

# 2. FROM ANYWHERE THAT CAN REACH THE EDGE: replay the example corpus in
python tools/replay.py --file examples/zmeta-profile-L-examples.jsonl --host <edge-host> --port 5555
```

(Run step 1 on the GCS host itself: 5556 is that gateway's local-consumer
forward, not a network-facing port. To sanity-check a single node before
wiring two, replay into it and receive on the same machine.)

What you should see:

- Edge logs: `recv=N ... fwd=N ... violations=0`, compact bytes well under
  240.
- GCS logs: the same events arriving compact, forwarded as JSON, `cot=N`
  when CoT is on.
- **The four hash lines printed by both gateways match.** That is the
  interoperability contract made visible: if the hashes differ, the nodes
  are not speaking the same governed kernel — stop and reconcile versions
  before anything else.

## Reading the honesty signals (field debugging cheat-sheet)

| You see | It means | It is |
|---|---|---|
| `violations=N` climbing | events refused by schema/policy, each with a reason code | the gate working — inspect the SYSTEM_EVENT diagnostics on the output |
| `cot_skipped` with `NON_FINITE_VALUE` | a value-honesty refusal (NaN/inf) filtered apart from the generic bucket | working |
| `cot_skipped` with `MISSING_GEO` | tracks without a usable position are not drawn as if they had one | working |
| `timing_fallback=N` | events arrived without clock-sync metadata; uncertainty widened, labeled UNSYNCED | honest degradation, not loss |
| no ellipse detail on TAK | `geopointsrc`/`altsrc` not asserted in `cot.config` | the omission default — assert it if (and only if) it is true |
| no bearing on a track you expected one for | the adapter demoted a frame-unlabeled bearing to native features (contract 6.4) | working — assert the frame at the producer if it is provable |
| an adapter emitting nothing for a record | fail-closed refusal on an unmappable/unavailable datum | working — the adapter's colocated tests enumerate its refusal reasons |

## Pre-event checklist per team

1. Bring **~10 minutes of recorded sensor output** (or expose the live
   stream). That plus `adapters/AUTHORING.md` is everything needed to
   build and verify an adapter on the spot.
2. Clone the repo at the current release tag on both nodes; confirm the
   startup hash lines match.
3. Edit the two config files (edge `forward.host`; GCS `cot.host` and the
   `cot.config` pedigree block if truthful).
4. Run the wire check above end-to-end once with the example corpus
   before connecting the real sensor.
