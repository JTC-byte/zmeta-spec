# ZMeta Quickstart

## Prereqs

- Python 3.11+ (3.13 recommended)
- Docker + Docker Compose

## Run gateway via docker-compose

From `gateway/`:

```
docker compose up
```

This listens on UDP `0.0.0.0:5555` and forwards to `127.0.0.1:5556`.

## Run udp_receiver on 5556

From repo root:

```
python tools/udp_receiver.py --host 127.0.0.1 --port 5556
```

## Replay core examples into 5555

```
python tools/replay.py --file examples/zmeta-examples-1.0.jsonl --host 127.0.0.1 --port 5555
```

## Replay command examples into 5555

```
python tools/replay.py --file examples/zmeta-command-examples.jsonl --host 127.0.0.1 --port 5555
```

## What success looks like

- Valid events are forwarded unchanged to the receiver.
- Violations are emitted as SYSTEM_EVENT (SCHEMA_VIOLATION or TASK_ACK) with reason codes.

Reference gateway implements severity tiers; schema remains the normative contract.

## Switch profiles (L/M/H)

Local:

```
python tools/run_gateway.py --profile L
python tools/run_gateway.py --profile M
python tools/run_gateway.py --profile H
```

Docker:

```
docker compose run --rm gateway python /app/gateway/src/gateway.py --profile L
docker compose run --rm gateway python /app/gateway/src/gateway.py --profile M
docker compose run --rm gateway python /app/gateway/src/gateway.py --profile H
```

## Where to look

- Schema: `schema/zmeta-event-1.0.schema.json`
- Policy: `policy/roles.yaml`, `policy/profiles.yaml`, `policy/semantics.yaml`, `policy/routing.yaml`
- Examples: `examples/`
