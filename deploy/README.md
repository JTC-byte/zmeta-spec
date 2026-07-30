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

Edit `configs/edge-config.json` to set the gateway host/IP.

What it does:
- Listens on UDP `listen.host:listen.port`.
- Forwards validated events to `forward.host:forward.port`.
- Does not emit CoT (`emit_cot: false`).

## Gateway (Profile H/M + CoT)

From repo root or bundle root:
```
docker compose -f deploy/gateway/docker-compose.yml up
```

Edit `configs/gateway-config.json` to adjust profile, ports, and CoT target.

What it does:
- Listens on UDP `listen.host:listen.port`.
- Forwards validated events to `forward.host:forward.port`.
- Emits CoT when `emit_cot: true`.

## Container networking

A gateway sends its forward and CoT streams outward. `configs/*.json` point both
at `127.0.0.1`, which is correct on a host and wrong in a container, where
`127.0.0.1` is the container's own loopback. The send succeeds, nothing can read
the destination, and no error is raised. Measured 2026-07-30 before this was
corrected: a container reported `recv=722 fwd=722` while a receiver on the
host's `127.0.0.1:5556` got zero datagrams.

Both Compose files therefore pass `--forward-host`, `--cot-host` and
`--forward-port` on the command line, where they override the config file, and
default them to `host.docker.internal`. Publishing a port does not solve this,
because a published port carries traffic into a container and has no bearing on
what the gateway sends out. Only the listen port is published.

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

## Notes

- Edge and gateway both listen on UDP `5555` inside their own container, so the
  pair needs different host ports on one machine. Without that the second one
  fails with `Bind for 0.0.0.0:5555 failed: port is already allocated`:
  ```
  cd deploy/gateway && docker compose up -d
  cd ../edge && ZMETA_EDGE_PORT=5557 ZMETA_GCS_HOST=host.docker.internal docker compose up -d
  ```
  Verified end to end on 2026-07-30: events fed to host port 5557 arrived as
  ZMeta JSON on the host's 5556 and as CoT on 6969.
- `docker compose` names its project after the directory, so `deploy/edge` runs
  as project `edge`. If another stack on the same machine also uses an `edge`
  directory, the two share a project namespace. Pass `-p` to keep them apart.
- Compose runs the gateway with unbuffered Python (`python -u`) so startup lines
  such as `gateway listening on ...`, hash values, and metrics configuration are
  visible immediately in `docker compose logs -f`.
- Stop services with `docker compose down`.
