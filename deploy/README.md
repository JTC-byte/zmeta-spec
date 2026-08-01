# Deployment (Docker)

These Compose files run the reference gateway as the MVP comms/validation module.
Use them when you want a repeatable, containerized install on edge and gateway nodes.

## Prerequisites

- Docker Desktop (Windows) or Docker Engine (Linux).
- Virtualization enabled in BIOS/UEFI on Windows.
- WSL2 enabled on Windows.
- UDP ports open between edge and gateway.

## Edge (relay)

From repo root or bundle root:
```
docker compose -f deploy/edge/docker-compose.yml up
```

The forward destination is set by the container command, not by
`configs/edge-config.json`. `deploy/edge/docker-compose.yml` always passes
`--forward-host` and `--forward-port` to the gateway process, and those flags
win over whatever the config file says (see Container networking below for
why). Set the real destination with environment variables:

```
ZMETA_GCS_HOST=<gateway-host-or-IP> ZMETA_GCS_PORT=<gateway-listen-port> \
  docker compose -f deploy/edge/docker-compose.yml up
```

`ZMETA_GCS_HOST` defaults to the literal string `GATEWAY_HOST`, which
resolves to nothing on purpose: a stranger who forgets to set it gets an
immediate, visible connection failure, not silent non-delivery to the wrong
place. `ZMETA_GCS_PORT` defaults to `5555`, the gateway node's listen port,
because node-to-node traffic always targets the receiving node's listen port.
Editing `configs/edge-config.json`'s `forward.host` or `forward.port` has no
effect on a container run; edit that file only for what the container command
does not override: `profile`, `emit_cot`, `input_encoding`/`output_encoding`,
and the `failure_modes` block.

What it does:
- Listens on UDP `listen.host:listen.port` inside the container, published to
  the host as `ZMETA_EDGE_PORT` (default `5555`).
- Forwards validated events to `ZMETA_GCS_HOST:ZMETA_GCS_PORT`.
- Does not emit CoT (`emit_cot: false`).

## Gateway (Profile H/M + CoT)

From repo root or bundle root:
```
docker compose -f deploy/gateway/docker-compose.yml up
```

The forward and CoT destinations are set by the container command, not by
`configs/gateway-config.json`. `deploy/gateway/docker-compose.yml` always
passes `--forward-host` and `--cot-host` to the gateway process, and those
flags win over the config file's `127.0.0.1` (see Container networking below
for why). Both default to `host.docker.internal`, which reaches services
running on the container's own host. Point them elsewhere with environment
variables:

```
ZMETA_CONSUMER_HOST=<fusion-host> ZMETA_COT_HOST=<TAK-host> \
  docker compose -f deploy/gateway/docker-compose.yml up
```

Editing `configs/gateway-config.json`'s `forward.host` or `cot.host` has no
effect on a container run. `forward.port` (the local-consumer JSON output,
default `5556`) and `cot.port` (default `6969`) are not overridden by the
container command and stay config-file settings, along with `profile` and
the `cot.config` position-source pedigree block.

What it does:
- Listens on UDP `listen.host:listen.port` inside the container, published to
  the host as `ZMETA_GATEWAY_PORT` (default `5555`).
- Forwards validated events to `ZMETA_CONSUMER_HOST:forward.port`.
- Emits CoT to `ZMETA_COT_HOST:cot.port` when `emit_cot: true`.

## Container networking

A gateway sends its forward and CoT streams outward. `configs/*.json` point both
at `127.0.0.1`, which is correct on a host and wrong in a container, where
`127.0.0.1` is the container's own loopback. The send succeeds, nothing can read
the destination, and no error is raised. Measured 2026-07-30 before this was
corrected: a container reported `recv=722 fwd=722` while a receiver on the
host's `127.0.0.1:5556` got zero datagrams.

Both Compose files therefore pass `--forward-host`, `--forward-port` (edge
only), and `--cot-host` (gateway only) on the command line, where they
override the config file, and default the hosts to `host.docker.internal`.
`host.docker.internal` is a Docker Desktop convention: Docker Desktop
(Windows, Mac) resolves it out of the box. Both Compose files also add an
explicit `extra_hosts: host.docker.internal:host-gateway` entry so the same
name resolves on Docker Engine (Linux) too. Publishing a port does not solve
this, because a published port carries traffic into a container and has no
bearing on what the gateway sends out. Only the listen port is published.

| Variable | Default | Use it when |
|---|---|---|
| `ZMETA_GATEWAY_PORT` | `5555` | the gateway node's host port must move |
| `ZMETA_EDGE_PORT` | `5555` | running both nodes on one machine |
| `ZMETA_CONSUMER_HOST` | `host.docker.internal` | the consumer is not on the container's host |
| `ZMETA_COT_HOST` | `host.docker.internal` | TAK is not on the container's host |
| `ZMETA_GCS_HOST` | `GATEWAY_HOST` | the edge node needs the gateway address |
| `ZMETA_GCS_PORT` | `5555` | the gateway node listens somewhere other than 5555 |

The edge node's forward port defaults to `5555` here rather than to the config's
`5556`, because node-to-node traffic always targets the receiving node's listen
port. `5556` is the local-consumer destination, and edge traffic sent to a
gateway node's `5556` arrives nowhere and reports nothing.

In a real two-machine deployment, the gateway's published port
(`ZMETA_GATEWAY_PORT`) is the one that needs inbound access opened on the
gateway host, because that is what the edge node (on a different machine or
network segment) must reach. The edge's own published port
(`ZMETA_EDGE_PORT`) needs inbound access from whatever feeds it, usually the
adapter or sensor host, which is often the same machine and needs no firewall
change. If TAK runs on a third host, its inbound CoT port needs the same
treatment.

## One machine, both nodes

Edge and gateway both listen on UDP `5555` inside their own container, so the
pair needs different host ports on one machine. Without that the second one
fails with `Bind for 0.0.0.0:5555 failed: port is already allocated`.

Move the gateway's published port when `5555` is already taken on the host,
and point the edge node's `ZMETA_GCS_PORT` at that same number: on one
machine, `ZMETA_GATEWAY_PORT` and `ZMETA_GCS_PORT` are the same port by
construction, because the edge container reaches the gateway container
through the host's loopback (`host.docker.internal`), which exposes only
whatever the gateway published.

```bash
cd deploy/gateway
ZMETA_GATEWAY_PORT=5560 docker compose up -d

cd ../edge
ZMETA_EDGE_PORT=5561 ZMETA_GCS_HOST=host.docker.internal ZMETA_GCS_PORT=5560 \
  docker compose up -d
```

`ZMETA_EDGE_PORT` is independent of the other two: it is where you feed the
edge node from outside the container (an adapter, or `tools/replay.py`), and
nothing on this host reads it directly, so it can be any free port. Change
`ZMETA_GATEWAY_PORT` without also changing `ZMETA_GCS_PORT` to match, and the
edge node forwards to a port nothing is listening on, silently.

Verified 2026-08-01 with this exact shape: a single fresh event fed to host
port 5561 arrived, event id intact, as ZMeta JSON on the host's 5556.

`docker compose` names its project after the directory, so `deploy/edge` runs
as project `edge`. If another stack on the same machine also uses an `edge`
directory, the two share a project namespace. Pass `-p` to keep them apart.

## Verification

From the repo root, with both nodes up (adjust ports to match your own
`ZMETA_EDGE_PORT`/`ZMETA_GATEWAY_PORT`):

```bash
# On the host: watch what the gateway forwards to local consumers
python tools/udp_receiver.py --host 127.0.0.1 --port 5556

# From anywhere that can reach the edge node: replay the example corpus in
python tools/replay.py --file examples/zmeta-examples-1.0.jsonl --host 127.0.0.1 --port 5561
```

The receiver should print each replayed event, matching the event ids in the
corpus. `tools/replay.py` re-sends the same event ids on every run, and the
gateway dedupes on `event_id`, so a second replay of the same file forwards
nothing new; that is working as designed, not a fault.

`docs/zmeta_two_node_quickstart.md` has the full wire check: the four
startup hash lines both nodes must agree on, the CoT/TAK path, and the
observability table for reading degraded-timing and refusal signals off the
running nodes.

## Notes

- Compose runs the gateway with unbuffered Python (`python -u`) so startup lines
  such as `gateway listening on ...`, hash values, and metrics configuration are
  visible immediately in `docker compose logs -f`.
- Stop services with `docker compose down`.
