# ZMeta Field Dictionary (UI‑Focused)

This is a concise field reference for UI and integration teams. For full
validation rules, see the JSON schema in `schema/zmeta-event-1.0.schema.json`.

## Top-Level

- `zmeta_version` (string) — semantic contract version (e.g., `1.0`).
- `event` (object) — event envelope metadata.
- `source` (object) — producer identity.
- `payload` (object) — event‑specific content.
- `profile` (string, optional) — export profile: `L`, `M`, `H`.
- `confidence` (number, optional) — normalized confidence for fused/track events.
- `lineage` (object, optional) — `based_on` UUID array and optional `transform`.

## Event Block (`event`)

- `event_id` (uuid string) — unique event id.
- `event_type` (enum) — see “Enums” below.
- `event_subtype` (enum/string) — subtype, may be custom.
- `ts` (ISO timestamp) — event time.
- `t_receive` (ISO timestamp, optional) — gateway receipt time (stamped).
- `t_publish` (ISO timestamp, optional) — gateway publish time (stamped).

## Source Block (`source`)

- `platform_id` (string) — platform or node identifier.
- `node_role` (enum) — edge/gateway role (see enums).
- `producer` (string) — component name (e.g., `sensorops`, `torch`).
- `sensor_id` (string, optional) — sensor identifier.
- `sw_version` (string, optional) — software version.

## Payload (Common Shapes)

### STATE_EVENT / TRACK_STATE

- `track_id` (string) — track identifier.
- `geo` (object) — `lat`, `lon`, `alt_m` (numbers).
- `valid_for_ms` (int) — freshness window.
- `class` (string, optional) — CoT type or platform class.
- `source_summary` (string/array, optional) — short provenance hint(s).
- `heading_deg` (number, optional), `speed_mps` (number, optional).
- `data_ref` / `data_refs` (object/array, optional) — offboard artifact links.

### COMMAND_EVENT / MISSION_TASK

- `task_id` (string).
- `task_type` (enum).
- `target_geo` (object) — `lat`, `lon`.
- `valid_for_ms` (int).
- `valid_from_ts` (ISO timestamp, optional).
- `priority` (enum, optional).
- `requires_deconfliction` (bool, required by policy).

### SYSTEM_EVENT

Common fields:
- `system_type` (enum) — `TASK_ACK`, `LINK_STATUS`, `TIME_STATUS`, `SCHEMA_VIOLATION`.
- `state` (enum/string).
- `metrics` (object) — required keys vary by system type.

`TASK_ACK` metrics:
- `task_id`, `original_event_id` (required).
- `reason_code` (required for REJECTED/FAILED/CANCELLED/EXPIRED/DUPLICATE_IGNORED).

`LINK_STATUS` metrics (required):
- `link_id`, `latency_ms`, `packet_loss_pct`, `throughput_bps`.
- Optional: `rssi_dbm`, `snr_db`, `jitter_ms`, `reason_code`, `interface`.

`TIME_STATUS` metrics:
- `time_source`, `sync_state`, `est_error_ms`, `last_sync_ts`.

`SCHEMA_VIOLATION` metrics:
- `reason_code`, `original_event_id`, optional `path`, `error`.

## Enums (Common)

`event_type`:
- `OBSERVATION_EVENT`
- `INFERENCE_EVENT`
- `FUSION_EVENT`
- `STATE_EVENT`
- `COMMAND_EVENT`
- `SYSTEM_EVENT`

`event_subtype` (common):
- `TRACK_STATE`, `MISSION_TASK`, `TASK_ACK`, `LINK_STATUS`, `TIME_STATUS`, `SCHEMA_VIOLATION`

`node_role`:
- `EDGE`, `GATEWAY`, `APEX`, `DMZ`, `CLOUD`

`profile`:
- `L`, `M`, `H`

`system_type`:
- `TASK_ACK`, `LINK_STATUS`, `TIME_STATUS`, `SCHEMA_VIOLATION`

`task_type`:
- `GOTO`, `ORBIT`, `HOLD`, `SEARCH_BOX`

`priority`:
- `LOW`, `MED`, `HIGH`

`task_ack.state`:
- `RECEIVED`, `ACCEPTED`, `REJECTED`, `EXECUTING`, `COMPLETED`, `FAILED`,
  `CANCELLED`, `EXPIRED`, `DUPLICATE_IGNORED`

`link_status.state`:
- `UP`, `DEGRADED`, `DOWN`, `UNKNOWN`

`time_source`:
- `GPS_PPS`, `GPS_NMEA`, `NTP`, `PTP`, `MANUAL`, `UNKNOWN`

`sync_state`:
- `LOCKED`, `HOLDOVER`, `UNSYNCED`

Always refer to the schema and policy for authoritative constraints.
