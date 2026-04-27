# ZMeta Quickstart

This is a developer-oriented walkthrough. For a full installation guide with
step-by-step bundle installs, see `spec/installation-guide.md`.

## Prereqs

- Python 3.11+ (3.13 recommended)
- Docker + Docker Compose
- Windows Docker Desktop requires virtualization + WSL2 enabled.

Install runtime dependencies:
```
python -m pip install -r requirements.txt
```

Optional (tests/dev tools):
```
python -m pip install -r requirements-dev.txt
```

## Run gateway via docker-compose

From `gateway/`:

```
docker compose up
```

This listens on UDP `0.0.0.0:5555` and forwards to `127.0.0.1:5556`.

If Docker is unavailable, run the gateway directly:
```
python gateway/src/gateway.py --profile H
```

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

## Live gateway test (dedupe + CoT)

```
python tools/test_gateway_live.py
```

## What success looks like

- Valid events are validated and forwarded to the receiver after configured gateway transforms
  such as profile stamping, timing stamps, optional-field stripping, or output encoding.
- Violations are emitted as SYSTEM_EVENT (SCHEMA_VIOLATION or TASK_ACK) with reason codes.
  TASK_ACK requires `metrics.task_id` and `metrics.original_event_id`, and `reason_code` for
  failure states (REJECTED/FAILED/CANCELLED/EXPIRED/DUPLICATE_IGNORED).
- Forwarded events are stamped with `event.t_receive` (default for profiles L/M/H); if
  `event.t_publish` is missing it is set to the same value to help with AAR latency analysis.

Reference gateway implements severity tiers; schema remains the normative contract.

## Switch profiles (L/M/H)

Local:

```
python tools/run_gateway.py --profile L
python tools/run_gateway.py --profile M
python tools/run_gateway.py --profile H
```

Note: The reference gateway stamps outgoing events with the configured top-level
export `profile` (L/M/H) so downstream consumers know which profile was applied.

## End-to-end workflow test

```
python tools/test_workflow_end_to_end.py --profile H
python tools/test_workflow_end_to_end.py --profile M
python tools/test_workflow_end_to_end.py --profile L
python tools/test_workflow_end_to_end.py --profile M --expect COMMAND_EVENT,SYSTEM_EVENT
```

## Try binary encodings

CBOR and protobuf preserve the same decoded ZMeta event. Compact is the Profile L
integer-key CBOR mapping.

```
python tools/measure_packet_size.py --file examples/encoding-roundtrip.jsonl --encodings json,cbor,compact,proto
python tools/convert_encoding.py --from json --to proto --input examples/encoding-roundtrip.jsonl --output event.pb --allow-jsonl-first
python tools/convert_encoding.py --from proto --to json --input event.pb --output event.json
python tools/test_gateway_live.py --profile H --encoding proto --input-encoding proto --no-cot
python tools/test_gateway_live.py --profile L --encoding compact --input-encoding compact
```

Docker:

```
docker compose run --rm gateway python /app/gateway/src/gateway.py --profile L
docker compose run --rm gateway python /app/gateway/src/gateway.py --profile M
docker compose run --rm gateway python /app/gateway/src/gateway.py --profile H
```

## Docker deploy (edge + gateway)

```
docker compose -f deploy/edge/docker-compose.yml up
docker compose -f deploy/gateway/docker-compose.yml up
```

Edit `configs/edge-config.json` and `configs/gateway-config.json` before running.
At minimum, replace `GATEWAY_HOST` in the edge config with the actual gateway
IP or DNS name.

If you run edge and gateway on the same host, change one of the UDP port mappings
to avoid collisions. Both default to UDP `5555`.

## Where to look

- Schema: `schema/zmeta-event-1.0.schema.json`
- Policy: `policy/roles.yaml`, `policy/profiles.yaml`, `policy/semantics.yaml`, `policy/routing.yaml`
- Examples: `examples/`
