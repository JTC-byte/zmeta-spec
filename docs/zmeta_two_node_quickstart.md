# ZMeta Two-Node Quickstart: Sensor Edge to COP

**Advisory (Docs/advisory change class). Non-normative.** The fastest path
from "a sensor emitting native records" to "honest tracks on a COP":
one gateway container beside the sensor, one at the consumption edge, ZMeta
on the wire between them. Everything here uses the stock configs and
containers in this repository; nothing needs to be built.

## The topology

```
 [sensor] --native--> [adapter] --ZMeta/JSON--> [EDGE gateway]      (sensor host / Raspberry Pi)
                                                     |
                                            ZMeta compact (Profile H)
                                                     v
 (any relay node: forward the ZMeta datagram verbatim -- never translate)
                                                     v
                                            [GCS gateway]           (GCS computer / big-compute node)
                                             |            |
                                     ZMeta/JSON out   CoT out --> TAK / COP
                                     (fusion, SAPIENT egress, tools)
```

**What reaches TAK, and what does not.** The CoT projection converts
`STATE_EVENT` track states only. An ingress adapter emits `OBSERVATION_EVENT`,
so a sensor wired straight through this topology produces ZMeta on the wire and
nothing on the map until something associates observations into tracks.
Verified 2026-07-30: five clean ADS-B observations traversed both nodes and
produced zero CoT datagrams, while the example corpus below produces one
because it contains one `STATE_EVENT`. The rehearsal passes and the real sensor
shows nothing, so decide which case you are in before the event.

How much work that is depends entirely on your sensor:

- **The subject broadcasts its own identity** (ADS-B, AIS). The association key
  arrives with the data, so `adapters/projector/track/` does the job. Feed it
  observations, publish the `FUSION_EVENT` and `STATE_EVENT` pair it returns,
  and tracks appear. The same synthetic snapshot that produced zero CoT above
  produces two tracks through it.
- **Identity has to be inferred** (RF bearings, EO detections). That is a real
  tracker and it is yours to bring. This repository ships the semantics for
  expressing correlation, deliberately not a correlation engine, because that
  decision depends on your sensors and your scenario.

Two rules govern the whole design:

1. **The canonical ZMeta event is the source of truth; every egress is a
   lossy projection** (design gate 4). Translate to CoT/SAPIENT only at the
   node that consumes it. A relay that translates mid-path
   destroys authority for every node downstream.
2. **Nothing is fabricated.** Every honesty behavior in this guide
   (omitted pedigrees, refused geo, degraded-timing labels) is the system
   working as designed. The observability table at the end says where to
   look for each one.

## Node A: the sensor edge (host or Raspberry Pi)

The edge gateway ingests adapter output (JSON), validates it against the
locked kernel, and forwards **compact** datagrams.

**Both stock nodes ship Profile H**, and they must match: profile validation is
exact equality, so a mismatched pair refuses 100% of traffic. H is the default
because Profile L excludes `OBSERVATION_EVENT`, which is everything an ingress
adapter emits, so an L node cannot carry sensor detections at all.

The refusal is not silent on the data path and is silent on the operator
console, which is worth knowing before you debug one. Measured 2026-07-30 with
an H edge feeding an L GCS node: every event produced a
`SYSTEM_EVENT`/`SCHEMA_VIOLATION` diagnostic on the receiving node's forward
port, and the node's own stdout printed nothing at all beyond its startup
banner. Look at the consumer stream, not the log, to find this.

Profile L remains the bandwidth shape for a constrained link (measured max 150
bytes against a 240-byte budget for the L corpus). Choosing it is a deliberate
decision that your edge sends STATE/SYSTEM/COMMAND rather than raw detections,
and **both** nodes must be set to it.

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
Profile H, `input_encoding: auto` (JSON or compact in), compact out, CoT
off, failure-mode handling on.

**Raspberry Pi / ARM64.** The compose files use the multi-arch
`python:3.13-slim` image, so the same file runs unmodified on a Pi.
Verified 2026-07-27 under QEMU arm64 emulation (`--platform linux/arm64`):
all dependencies install from wheels, the gateway starts and processes the
example corpus with zero violations, and the schema/policy/semantics/
contract hashes printed at startup are byte-identical to the x86 run:
the same kernel on any architecture. (On that wheel set, `cbor2` resolves to its
pure-Python build; both codec backends are first-class and cross-pinned in
the test suite.) Real-hardware throughput on a Pi is the one thing
emulation does not measure; re-run the replay smoke below when hardware
arrives.

Point your adapter at the edge gateway: `--host 127.0.0.1 --port 5555`
(UDP, one JSON event per datagram). Building the adapter is the
one-sitting exercise documented in `adapters/AUTHORING.md`; the
`adapters/ingress/bladerf/` reference plus its mapping pack is the worked
RF example, and `adapters/ingress/example-vendor/` is the teaching one.

## Node B: the GCS / consumption edge

```bash
cd deploy/gateway
docker compose up -d
```

The stock `configs/gateway-config.json` is the receive shape: Profile H,
listening on **5555** (this is the port the edge node must forward to),
`input_encoding: auto` (accepts the edge's compact datagrams directly),
JSON out to local consumers on **5556** (same-host consumers: your fusion
process, `tools/udp_receiver.py`, the SAPIENT/JREAP projections), CoT out
to `cot.host:cot.port` (default 127.0.0.1:6969; point it at your TAK
input).

Port summary, because the two 555x numbers are easy to transpose:

| Port | Who binds it | Who sends to it |
|---|---|---|
| 5555/udp | both gateways (`listen`) | the upstream node: adapter → edge, edge → GCS |
| 5556/udp | nothing (a destination) | each gateway's own `forward`, for **same-host** consumers |
| 6969/udp | your TAK/COP input | the GCS gateway's CoT egress |

**To see error ellipses and position pedigree on TAK, you must assert your
position source.** The projection never stamps `geopointsrc`/`altsrc`/`how`
it cannot prove. Unasserted, the `<precisionlocation>` ellipse detail and
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
GPS fix, do not assert `"GPS"`. That is the false claim the omission
default exists to prevent.

**SAPIENT egress** is adapter-level, not gateway-built-in: consume the
gateway's JSON output (port 5556) and project with
`adapters/egress/sapient/zmeta_state_to_sapient_detection.py` (wire-shape
validated against the official Dstl Apex tooling). Same pattern for
JREAP/KLV.

## Running the nodes in containers

The two `deploy/` Compose files handle the container-specific parts of this,
and it is worth knowing what they are doing on your behalf.

A gateway sends its forward and CoT streams outward. `configs/*.json` set both
destinations to `127.0.0.1`, which is right when the gateway runs directly on a
host and wrong inside a container, where `127.0.0.1` is the container's own
loopback. Datagrams sent there are delivered to a namespace nothing can read,
and no error is raised, because the send succeeds. Measured 2026-07-30 before
this was corrected: a container reported `recv=722 fwd=722` while a receiver on
the host's `127.0.0.1:5556` saw zero, and the wire check above could not pass.
The Compose files now pass `--forward-host` and `--cot-host` on the command
line, where they override the config, and default them to
`host.docker.internal`.

Publishing a port does not help here. A published port carries traffic *into* a
container and has no bearing on what the gateway sends out, which is why only
the listen port is published now.

Environment overrides, all optional:

| Variable | Default | Use it when |
|---|---|---|
| `ZMETA_GATEWAY_PORT` | `5555` | the GCS node's host port must move |
| `ZMETA_EDGE_PORT` | `5555` | running both nodes on one machine |
| `ZMETA_CONSUMER_HOST` | `host.docker.internal` | your fusion process is not on the container's host |
| `ZMETA_COT_HOST` | `host.docker.internal` | TAK is not on the container's host |
| `ZMETA_GCS_HOST` | `GATEWAY_HOST` | the edge node needs the GCS address |
| `ZMETA_GCS_PORT` | `5555` | the GCS node listens somewhere other than 5555 |

Both nodes listen on 5555 inside their own container, so running the pair on
one machine needs different host ports. Without that, the second one refuses to
start with `Bind for 0.0.0.0:5555 failed: port is already allocated`. The whole
pair on one host:

```bash
cd deploy/gateway && docker compose up -d
cd ../edge && ZMETA_EDGE_PORT=5557 ZMETA_GCS_HOST=host.docker.internal docker compose up -d
```

Feed the edge on host port 5557; ZMeta JSON arrives on the host's 5556 and CoT
on 6969. That exact pair was run end to end on 2026-07-30.

## Wire check (five minutes, run it before the event)

From the repo root on any host that can reach the nodes:

```bash
# 1. ON THE GCS HOST: watch what its gateway forwards to local consumers
python tools/udp_receiver.py --host 127.0.0.1 --port 5556

# 2. FROM ANYWHERE THAT CAN REACH THE EDGE: replay the example corpus in
python tools/replay.py --file examples/zmeta-examples-1.0.jsonl --host <edge-host> --port 5555
```

(Run step 1 on the GCS host itself: 5556 is that gateway's local-consumer
forward, not a network-facing port. To sanity-check a single node before
wiring two, replay into it and receive on the same machine.)

What you should see:

- **The receiver in step 1 prints the replayed events.** This is the check
  that matters, because it is the only one a short replay actually produces.
  Compare the event ids it prints against the corpus you sent.
- **The four hash lines printed by both gateways match.** That is the
  interoperability contract made visible: if the hashes differ, the nodes
  are not speaking the same governed kernel. Stop and reconcile versions
  before anything else.

**What you will NOT see, and it is not a fault.** The `recv=N ... fwd=N ...
violations=0` metrics line is emitted from the datagram path, so it appears
only when a datagram arrives after the metrics interval has elapsed. A replay
of four events finishes in under a second and the node then goes idle, so the
line never prints and the run's final window is never flushed. Shortening
`metrics_interval_sec` does not change this: verified 2026-07-30 at a
one-second interval with seven seconds of idle, still no output. Metrics are a
sustained-traffic instrument. To see them, hold a load for longer than the
interval, or read the far-consumer count above instead.

## Reading the honesty signals (field debugging cheat-sheet)

| You see | It means | It is |
|---|---|---|
| `violations=N` climbing | events refused by schema/policy, each with a reason code | the gate working; inspect the SYSTEM_EVENT diagnostics on the output |
| `cot_skipped` with `NON_FINITE_VALUE` | a value-honesty refusal (NaN/inf) filtered apart from the generic bucket | working |
| `cot_skipped` with `MISSING_GEO` | tracks without a usable position are not drawn as if they had one | working |
| `timing_fallback=N` | events arrived without clock-sync metadata; uncertainty widened, labeled UNSYNCED | honest degradation, not loss |
| no ellipse detail on TAK | `geopointsrc`/`altsrc` not asserted in `cot.config` | the omission default; assert it if (and only if) it is true |
| no bearing on a track you expected one for | the adapter demoted a frame-unlabeled bearing to native features (contract 6.4) | working; assert the frame at the producer if it is provable |
| an adapter emitting nothing for a record | fail-closed refusal on an unmappable/unavailable datum | working; the adapter's colocated tests enumerate its refusal reasons |
| events flowing to consumers but nothing on TAK | your stream is observations; CoT projects `STATE_EVENT` only | working; you need track association, see the top of this guide |
| a track on TAK with `ce="9999999.0"` though your sensor knows its accuracy | a v1.0 `STATE_EVENT` has nowhere to carry positional uncertainty | a known limit, doctrine log S1-05; nothing is overstated, the measurement is simply unsayable on a v1.0 track |
| no metrics line at all | the node is idle, or the replay was shorter than one metrics interval | working; metrics are emitted from the datagram path, so hold a load to see them |
| `drops=0` while a consumer is clearly missing events | drops counts what the gateway discarded, not what never reached it | check offered load: at 1000 events/s on one test host, 44% arrived with `drops=0`, the rest lost in the kernel receive buffer upstream |
| `duplicates` climbing and `fwd` flat | the same `event_id` is being re-sent | working; event dedupe is keyed on `event_id`, and `tools/replay.py --loop` re-sends ids verbatim, so only its first pass forwards |

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
