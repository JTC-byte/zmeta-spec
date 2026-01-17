## ZMeta Reference Gateway (Minimal)

Validates ZMeta events against the v1.0 schema and enforces policy-as-config rules
before forwarding events over UDP.

### Run locally

```
python -m pip install -r gateway/requirements.txt
python gateway/src/gateway.py --profile=H
```

Listens on UDP `0.0.0.0:5555` and forwards to `127.0.0.1:5556`.

Optional helper:

```
python tools/run_gateway.py --profile H
```

### COMMAND_EVENT dedupe

The gateway deduplicates `COMMAND_EVENT` by `task_id` using an in-memory TTL cache.
TTL comes from `payload.valid_for_ms` (default 60000 ms, max 300000 ms). Duplicates are
not forwarded; the gateway emits a `SYSTEM_EVENT` `TASK_ACK` with state `DUPLICATE_IGNORED`.

### CoT emission (optional)

Enable CoT output for forwarded `STATE_EVENT` / `TRACK_STATE`:

```
python gateway/src/gateway.py --profile H --emit-cot
```

CoT XML is sent via UDP to `127.0.0.1:6969`.

### Run with Docker

From `gateway/`:

```
docker compose up
```

### Example (send + receive)

Start a UDP receiver:

```
python - <<'PY'
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind(("127.0.0.1", 5556))
print(s.recvfrom(65535)[0].decode())
PY
```

Send a COMMAND_EVENT (valid, forwarded):

```
python - <<'PY'
import json
import socket
msg = {
  "zmeta_version": "1.0",
  "event": {
    "event_id": "7b9a8f9a-2d2a-4c3f-9e6b-7a7f3a6d2c10",
    "event_type": "COMMAND_EVENT",
    "event_subtype": "MISSION_TASK",
    "ts": "2025-01-17T14:32:10Z"
  },
  "source": {
    "platform_id": "comms-node-1",
    "node_role": "GATEWAY",
    "producer": "sensorops"
  },
  "payload": {
    "task_id": "task-20250117-0001",
    "task_type": "GOTO",
    "target_geo": {"lat": 34.0522, "lon": -118.2437},
    "valid_for_ms": 600000,
    "requires_deconfliction": True
  }
}
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.sendto(json.dumps(msg).encode("utf-8"), ("127.0.0.1", 5555))
PY
```

To see a violation, try an OBSERVATION_EVENT that includes `track_id` in its payload.
