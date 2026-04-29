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

Self-test (schema + policy + examples + encoding):

```
python gateway/src/gateway.py --profile H --self-test
```

Self-test + hash gate (example):

```
python tools/compute_contract_hash.py
python gateway/src/gateway.py --profile H --self-test --require-contract-hash <HASH>
```

### Config file (recommended)

Generate a deterministic config with the wizard:

```
python tools/gateway_wizard.py --output gateway-config.json
```

Run with the config:

```
python gateway/src/gateway.py --config gateway-config.json
```

Example config: `gateway/config/gateway-config.example.json`.

The config file keys are:

- `profile` (L/M/H)
- `listen` host/port
- `forward` host/port
- `emit_cot` and `cot` host/port
- `input_encoding` (`json`, `cbor`, `compact`, `proto`, `auto`) and `output_encoding` (`json`, `cbor`, `compact`, `proto`)
- `stamp_profile` and `stamp_profile_profiles` (profile field stamping)
- `stamp_timing` and `stamp_timing_profiles` (t_receive/t_publish stamping; default L/M/H)
- `strip_optional_fields` and `strip_optional_fields_profiles` (bandwidth compaction)
- `strict_validation` (treat warnings as failures)
- `emit_metrics` and `metrics_interval_sec` (periodic gateway metrics logs)
- `rate_limit_per_sec` (drop packets above receive rate)
- `rate_limit_producer_per_sec` (drop per-producer above receive rate)
- `metrics_log_path`, `metrics_log_max_bytes`, `metrics_log_backups` (JSONL metrics logs)
- `stamp_contract_hash` (include schema, policy, semantic-contract, and combined hashes in gateway-generated system events)
- `require_schema_hash`, `require_policy_hash`, `require_contract_hash` (startup gate)
- `schema_path` and `policy_dir` (resolved relative to the config file)

CLI flags like `--profile` and `--listen-port` override the config when needed.
Additional flags include `--strict-validation`, `--rate-limit-per-sec`,
`--metrics-interval-sec`, `--no-metrics`, `--rate-limit-producer-per-sec`,
`--metrics-log-path`, `--metrics-log-max-bytes`, `--metrics-log-backups`,
and `--self-test`.

### Encoding

The gateway accepts `input_encoding` of `json`, `cbor`, `compact`, `proto`, or
`auto`, and emits `output_encoding` of `json`, `cbor`, `compact`, or `proto`.
CBOR requires `cbor2` or the built-in `zmeta_cbor` fallback. A common pattern is
compact encoding on Profile L edge links (edge `output_encoding=compact`) and
JSON on gateway egress. Use `compact` for the Profile L compact mapping (see
`spec/compact-binary-mapping.md`). Use `proto` for the experimental protobuf
projection described in `spec/protobuf-encoding.md`.

### COMMAND_EVENT dedupe

The gateway deduplicates `COMMAND_EVENT` by `task_id` using an in-memory TTL cache.
TTL comes from `payload.valid_for_ms` (default 60000 ms, max 300000 ms). Duplicates are
not forwarded; the gateway emits a `SYSTEM_EVENT` `TASK_ACK` with state `DUPLICATE_IGNORED`
and metrics including `task_id`, `original_event_id`, and `reason_code=TASK_DUPLICATE`.

### Timing stamps

For AAR/latency analysis, the gateway stamps `event.t_receive` on forwarded events
when it is missing (default for profiles L/M/H). If `event.t_publish` is missing, it is
set to the same value as `t_receive`. Use `stamp_timing`/`stamp_timing_profiles` to
change this behavior.

### Telemetry and rate limiting

The gateway logs periodic metrics (received, forwarded, drops, violations, warnings) at
`metrics_interval_sec` when `emit_metrics` is true. Use `rate_limit_per_sec` to drop
packets above a configured receive rate. `rate_limit_producer_per_sec` applies per producer.
When CoT emission is enabled, metrics include `cot_skipped` and
`cot_skip_reasons` for STATE_EVENTs that cannot be projected to CoT, such as
missing `payload.track_id` or missing `payload.geo`.
Timing visibility metrics include `timing_quality_source`,
`timing_quality_fallback`, and `timing_quality_modes`. `UNKNOWN/UNSYNCED`
per-event timing increments the fallback counter so operators can distinguish
adapter fallback timing from stronger source-provided GPS/NTP/PTP timing.
`timing_quality_fallback` is a degraded-mode signal, not evidence of a healthy
time source; deployments should drive that count down by providing real timing
metadata per event or periodic `SYSTEM_EVENT` / `TIME_STATUS` updates.

If `metrics_log_path` is set, the gateway writes JSONL metrics/violation/drop records
and rotates logs based on `metrics_log_max_bytes` and `metrics_log_backups`.

### Strict validation

When `strict_validation` is enabled, warnings are treated as failures and the original
event is not forwarded.

### Contract hash gate

On startup, the gateway prints schema, policy, semantic-contract, and combined
contract hashes. If `require_*_hash` is set and does not match, the gateway exits
to prevent drift. Use `stamp_contract_hash` to include hashes in
gateway-generated system events for AAR traceability.

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

The Compose command runs the gateway with unbuffered Python so startup lines and
periodic metrics are visible immediately in `docker compose logs -f`.

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
    "event_id": "019c2b5d-7c82-7388-8c21-50e4f126d7a0",
    "event_type": "COMMAND_EVENT",
    "event_subtype": "GOTO",
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
    "requires_deconfliction": True,
    "timing_quality": {
      "time_source": "GPS_PPS",
      "sync_state": "LOCKED",
      "est_error_ms": 1.5,
      "last_sync_ts": "2025-01-17T14:32:09Z"
    }
  }
}
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.sendto(json.dumps(msg).encode("utf-8"), ("127.0.0.1", 5555))
PY
```

To see a violation, try an OBSERVATION_EVENT that includes `track_id` in its payload.
