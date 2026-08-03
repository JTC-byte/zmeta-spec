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
- `failure_modes` (edge runtime degradation controls such as timing loss)
- `strict_validation` (treat warnings as failures)
- `emit_metrics` and `metrics_interval_sec` (periodic gateway metrics logs)
- `rate_limit_per_sec` (drop packets above receive rate)
- `rate_limit_producer_per_sec` (drop per-producer above receive rate)
- `metrics_log_path`, `metrics_log_max_bytes`, `metrics_log_backups` (JSONL metrics logs)
- `warn_datagram_bytes` (warn when an outgoing datagram exceeds this size; 0 disables)
- `ts_plausibility_horizon_ms` (warn when `event.ts` sits outside a window around now; 0 disables; see Event timestamp plausibility below)
- `stamp_contract_hash` (include schema, policy, semantic-contract, and combined hashes in gateway-generated system events)
- `require_schema_hash`, `require_policy_hash`, `require_contract_hash` (startup gate)
- `schema_path` and `policy_dir` (resolved relative to the config file)

CLI flags like `--profile` and `--listen-port` override the config when needed.
Additional flags include `--strict-validation`, `--rate-limit-per-sec`,
`--metrics-interval-sec`, `--no-metrics`, `--rate-limit-producer-per-sec`,
`--metrics-log-path`, `--metrics-log-max-bytes`, `--metrics-log-backups`,
`--warn-datagram-bytes`, `--ts-plausibility-horizon-ms`, and `--self-test`.

### Encoding

The gateway accepts `input_encoding` of `json`, `cbor`, `compact`, `proto`, or
`auto`, and emits `output_encoding` of `json`, `cbor`, `compact`, or `proto`.
CBOR/compact use the built-in deterministic `zmeta_cbor` decoder when
available, with default message, item, container, and nesting limits for
untrusted input. A common pattern is compact encoding on Profile L edge links
(edge `output_encoding=compact`) and JSON on gateway egress. Use `compact` for
the Profile L compact mapping (see `spec/compact-binary-mapping.md`). Use
`proto` for the experimental protobuf projection described in
`spec/protobuf-encoding.md`.

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

The periodic summary prints on schedule even when no datagrams arrive at all. The
receive loop wakes on `metrics_interval_sec` with nothing to receive and still logs
the summary from there, so an idle gateway reports `recv=0` on schedule instead of
going silent past the startup banner. This is what lets an operator tell an
idle-but-healthy gateway apart from a wedged one, which prints nothing at all.

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

When policy soft-accepts risky data, gateway-generated warning diagnostics carry
filterable risk fields such as `risk_dimension`, `policy_mode`,
`policy_decision`, `allowed_uses`, `prohibited_uses`, and effect details. Runtime
failure-mode degradation also stamps accepted events under
`payload.extensions.risk_adjudication` so confidence or TTL changes are not
silent.

Downstream consumers can filter accepted-risk streams without mutating events:

```
python tools/filter_risk.py --input gateway-output.jsonl --preset display
python tools/filter_risk.py --input gateway-output.jsonl --preset fusion
python tools/filter_risk.py --input gateway-output.jsonl --preset command --fail-on-drop
```

The filter reads event-side risk labels and same-stream warning diagnostics. It
passes or drops events based on explicit `allowed_uses`, `prohibited_uses`,
`risk_dimension`, and `policy_decision` labels; it does not change the event or
turn degraded data into clean data. Consumers that do not run this tool still
have the same responsibility: honor `allowed_uses`, `prohibited_uses`, and
`policy_decision` before using accepted-risk data for fusion, state update,
command basis, autonomy, or export.

If `metrics_log_path` is set, the gateway writes JSONL metrics/violation/drop records
and rotates logs based on `metrics_log_max_bytes` and `metrics_log_backups`.

The metrics sinks are observability, not translation. If the log file or the
console becomes unwritable (full disk, read-only remount, removed directory,
closed pipe), the gateway keeps translating: the failure is reported once on
stderr - once, because a per-datagram warning storm is its own outage - and
writes keep being attempted so the sink recovers on its own. Nothing about an
event changes, and the in-memory counters stay accurate, so the drop and
violation buckets an operator filters on remain honest while the file is gone.
A failing sink must never terminate the gateway for every producer behind it.

Degraded observability is quantified rather than merely announced, on three
surfaces, so a consumer can see loss instead of inferring it:

- The one stderr warning is emitted when it is DELIVERED, not when it is
  attempted. Full disk and closed pipe usually take stderr down together with
  the sink, so a latch spent on an undelivered line meant zero warnings for the
  whole run; the warning is retried until one lands, then never again.
- The periodic summary prints `metrics sink_degraded console_failures=...
  write_failures=... console_failures_total=... write_failures_total=...`
  whenever either sink has lost anything (per-window counts plus run totals),
  and the same four counts appear in the JSONL `metrics` record. The two sinks
  report each other, so whichever channel survives still carries the number.
- When the log sink recovers, a `metrics_sink_gap` record is appended ahead of
  the next record, carrying `lost_records`, `first_error`, and `path`. Records
  lost to a dead sink are not recoverable, but the discontinuity is in band: a
  consumer reads the gap instead of seeing two records that look contiguous.

If the sink never recovers, the marker never lands - a file cannot report its
own end - which is why the stderr warning and the console counters exist.

### Strict validation

When `strict_validation` is enabled, warnings are treated as failures and the original
event is not forwarded.

### Event timestamp plausibility

The `zmeta-event-1.1.0.schema.json` `utcDateTime` pattern enforces structural
calendar shape (year 1970-2999, month 01-12, day 01-31, hour 00-23, minute/second
00-59), which rejects a corrupted value such as year 0001 or month 88 on the
1.1.0 branch. `zmeta-event-1.0.schema.json` is locked and does not gain this
pattern, and neither schema can know what "now" is. A structurally valid `ts`
that is simply wrong by years is a runtime plausibility question that no
schema pattern can answer (semantics-contract 5.7).

The gateway closes that gap at runtime, on every `zmeta_version`. Set
`ts_plausibility_horizon_ms` (default 86400000, 24 hours; 0 disables) to warn
when an incoming `event.ts` sits more than the configured horizon before or
after wall-clock now, in either direction. The check never rejects an event
and never runs under `strict_validation` escalation: it is purely observability,
the same as `warn_datagram_bytes` above. A hit is counted in metrics under
`warning_codes` with reason code `EVENT_TS_IMPLAUSIBLE`, carrying the offending
`ts`, the direction (`past`/`future`), the delta in milliseconds, and the
configured horizon.

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
