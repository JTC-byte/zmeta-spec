# ZMeta Compact Binary Mapping (Profile L)

This document defines an optional **compact wire encoding** for Profile L links.
It preserves ZMeta semantics by expanding to the canonical JSON envelope before validation
and downstream translation (e.g., CoT/TAK).

## Purpose

Profile L links are bandwidth-constrained. The compact mapping reduces overhead by:
- Using CBOR with **integer keys** instead of string field names.
- Encoding UUIDv7 values as **16-byte binary** values.
- Encoding timestamps as **epoch milliseconds** (int64).
- Mapping common enums to small integers.

The gateway expands compact packets back into standard ZMeta JSON for enforcement and CoT emission.

## CBOR Determinism

ZMeta CBOR encoders SHOULD emit deterministic CBOR:
- Definite-length strings, byte strings, arrays, and maps only.
- No indefinite-length containers.
- Map keys sorted by canonical CBOR ordering.
- No semantic dependence on JSON object ordering or CBOR map ordering.

The reference fallback encoder (`zmeta_cbor.py`) uses deterministic map ordering.
When `cbor2` is available, the reference tools and gateway use canonical mode
for CBOR output.

## Encoding Rules (Compact v1)

Top-level map keys:
- `1`: `compact_version` (int; currently `1`)
- `2`: `event`
- `3`: `source`
- `4`: `payload`
- `5`: `confidence`
- `6`: `lineage`
- `7`: `profile`

Event map keys:
- `1`: `event_id` (UUID bytes)
- `2`: `event_type` (enum)
- `3`: `event_subtype` (enum or string)
- `4`: `ts` (epoch ms)
- `5`: `t_publish` (epoch ms, optional)
- `6`: `t_receive` (epoch ms, optional)

Source map keys:
- `1`: `platform_id`
- `2`: `node_role` (enum)
- `3`: `producer`
- `4`: `sensor_id` (optional)
- `5`: `sw_version` (optional)

Lineage map keys:
- `1`: `based_on` (array of UUID bytes)
- `2`: `transform` (optional)

## Payload Encoding (Profile L)

STATE_EVENT payload map keys:
- `1`: `track_id`
- `2`: `geo` (map)
- `3`: `valid_for_ms`
- `4`: `class` (optional)
- `5`: `source_summary` (optional)
- `6`: `heading_deg` (optional)
- `7`: `speed_mps` (optional)

Geo map keys:
- `1`: `lat`
- `2`: `lon`
- `3`: `alt_m`

COMMAND_EVENT payload map keys:
- `1`: `task_id`
- `2`: `task_type` (enum)
- `3`: `target_geo` (map)
- `4`: `geometry` (optional)
- `5`: `valid_from_ts` (epoch ms, optional)
- `6`: `valid_for_ms`
- `7`: `priority` (enum, optional)
- `8`: `requires_deconfliction` (optional; default true when expanded)

System event payload map keys:
- `1`: `system_type` (enum)
- `2`: `state` (enum or string)
- `3`: `metrics` (map)

## Enums (Compact v1)

Event types:
- `1` OBSERVATION_EVENT
- `2` INFERENCE_EVENT
- `3` FUSION_EVENT
- `4` STATE_EVENT
- `5` COMMAND_EVENT
- `6` SYSTEM_EVENT

Node roles:
- `1` EDGE
- `2` GATEWAY
- `3` APEX
- `4` DMZ
- `5` CLOUD

Profiles:
- `1` L
- `2` M
- `3` H

Event subtypes (common):
- `1` TRACK_STATE
- `2` MISSION_TASK
- `3` TASK_ACK
- `4` LINK_STATUS
- `5` TIME_STATUS
- `6` SCHEMA_VIOLATION

System types:
- `1` LINK_STATUS
- `2` TIME_STATUS
- `3` SCHEMA_VIOLATION
- `4` TASK_ACK

Task types:
- `1` GOTO
- `2` ORBIT
- `3` HOLD
- `4` SEARCH_BOX

Priorities:
- `1` LOW
- `2` MED
- `3` HIGH

Time source:
- `1` GPS_PPS
- `2` GPS_NMEA
- `3` NTP
- `4` PTP
- `5` MANUAL
- `6` UNKNOWN

Sync state:
- `1` LOCKED
- `2` HOLDOVER
- `3` UNSYNCED

TASK_ACK states:
- `1` RECEIVED
- `2` ACCEPTED
- `3` REJECTED
- `4` EXECUTING
- `5` COMPLETED
- `6` FAILED
- `7` CANCELLED
- `8` EXPIRED
- `9` DUPLICATE_IGNORED

LINK_STATUS states:
- `1` UP
- `2` DEGRADED
- `3` DOWN
- `4` UNKNOWN

Reason codes:
- Mapped to small integers by the reference implementation.
- Unknown reason codes may be transmitted as strings and are preserved.

## Compatibility

- The compact mapping is **wire-level only**.
- Gateways must expand compact packets into the canonical JSON schema before validation.
- Semantics are unchanged; only field names and primitive representations are compacted.

## Size Optimization Tips (Profile L)

If you must drive STATE_EVENT packets under ~200 bytes, focus on optional fields and
omit them at the producer (gateway stripping does not reduce link size).

Common high-impact optional fields:
- `payload.data_ref` / `payload.data_refs`
- `payload.source_summary`
- `payload.heading_deg`
- `payload.speed_mps`
- `payload.class`

Do not strip required STATE_EVENT fields such as `confidence` or `lineage`.
Profile L may reference non-exported lineage parents, but the lineage field
itself remains required for STATE_EVENT.

## Versioning

- `compact_version` (top-level key `1`) enables forward compatibility.
- Current version is `1`. Producers must set it to `1`.
- Decoders should reject unknown versions to avoid misinterpreting wire data.

## Profile L Payload Budget (Illustrative)

These are example sizes from `tools/measure_packet_size.py` using the current
Profile L examples. Actual sizes vary with field lengths and optional fields.

| Event Type | JSON (bytes) | CBOR (bytes) | COMPACT (bytes) | Notes |
| --- | --- | --- | --- | --- |
| STATE_EVENT/TRACK_STATE | 558 | 476 | 231 | Tight budgets should drop optional payload fields such as `payload.data_ref`, `source_summary`, `heading_deg`, `speed_mps`, or `class`; keep `confidence` and `lineage`. |
| SYSTEM_EVENT/TIME_STATUS | 444 | 373 | 101 | Already within tight budgets. |
| COMMAND_EVENT/MISSION_TASK | 422 | 353 | 115 | Already within tight budgets. |
