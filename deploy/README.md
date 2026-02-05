# Deployment (Docker)

These Compose files run the reference gateway as the MVP comms/validation module.
Use them when you want a repeatable, containerized install on edge and gateway nodes.

## Prerequisites

- Docker Desktop (Windows) or Docker Engine (Linux).
- Virtualization enabled in BIOS/UEFI on Windows.
- WSL2 enabled on Windows.
- UDP ports open between edge and gateway.

## Edge (Profile L relay)

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

## Notes

- Edge and gateway both default to UDP `5555`. If you run them on the same host,
  change one port mapping in the compose file or config to avoid collisions.
- Stop services with `docker compose down`.
