# ZMeta Field Dictionary (UI-Focused)

This is a concise field reference for UI and integration teams. For full
validation rules, see the JSON schemas in `schema/` and the semantic contract in
`spec/semantics-contract.md`.

## Top-Level

- `zmeta_version` (string) - exact semantic contract/schema version (for example,
  `1.0` or `1.1.0`); aliases such as `1.1` must be normalized before validation.
- `event` (object) - event envelope metadata.
- `source` (object) - producer identity.
- `payload` (object) - event-specific content.
- `profile` (string, optional) - export profile: `L`, `M`, `H`; when present,
  schema validation enforces profile/event-type compatibility.
- `confidence` (number) - required for INFERENCE/FUSION/STATE events; prohibited for OBSERVATION/COMMAND/SYSTEM events.
- `lineage` (object) - required for INFERENCE/FUSION/STATE events; contains `based_on` UUIDv7 array and optional `transform`.

## Event Block (`event`)

- `event_id` (UUIDv7 string) - immutable event id.
- `event_type` (enum) - see "Enums" below.
- `event_subtype` (enum) - semantic subtype; must match the payload
  discriminator for the event type.
- `ts` (UTC-Z timestamp) - event capture/observation time.
- `t_receive` (UTC-Z timestamp, optional) - gateway receipt time (stamped).
- `t_publish` (UTC-Z timestamp, optional) - gateway publish time (stamped).

## Source Block (`source`)

- `platform_id` (string) - platform or node identifier.
- `node_role` (enum) - edge/gateway role (see enums).
- `producer` (string) - component name (for example, `sensorops`, `torch`).
- `sensor_id` (string, optional) - sensor identifier.
- `sw_version` (string, optional) - software version.

## Payload (Common Shapes)

### STATE_EVENT / TRACK_STATE

- `track_id` (string) - globally unique track identifier assigned by a fusion node; not reused.
- `geo` (object) - `lat`, `lon`, `alt_m` (numbers); experimental v1.1.0 also
  allows `error_ellipse_m` as the only canonical `geo` extension.
- `valid_for_ms` (int) - freshness window.
- `class` (string, optional) - CoT type or platform class.
- `source_summary` (string array, optional) - short provenance hints.
- `heading_deg` (number, optional, 0-360 inclusive), `speed_mps` (number,
  optional, non-negative).
- `extensions.external_promotion` (object, policy-scoped) - required by the
  reference producer-authority policy for explicitly marked external ingress
  producers such as CoT, JREAP, and MAVLink when they promote external reports
  into `STATE_EVENT`. Profile L may carry compact handles only.
- Raw observation features and artifact links (`data_ref` / `data_refs`) are
  not allowed on state projections; use lineage for traceability.

### COMMAND_EVENT / task type

- `task_id` (string) - idempotent command key; dedupe retransmissions by this field.
- `task_type` (enum).
- `target_geo` (object, optional) - `lat`, `lon`; altitude is prohibited.
- `geometry` (object, optional).
- `valid_for_ms` (int).
- `valid_from_ts` (UTC-Z timestamp, optional).
- `priority` (enum, optional).
- `requires_deconfliction` (bool, required by policy and must be `true`).

### SYSTEM_EVENT

Common fields:
- `system_type` (enum) - `TASK_ACK`, `LINK_STATUS`, `TIME_STATUS`, `SCHEMA_VIOLATION`; the experimental v1.1.0 schema also defines `SENSOR_STATUS` and `PLATFORM_STATUS`.
- `state` (enum/string).
- `metrics` (object) - required keys vary by system type.

`TASK_ACK` metrics:
- `task_id`, `original_event_id` (required).
- `reason_code` (required for REJECTED/FAILED/CANCELLED/EXPIRED/DUPLICATE_IGNORED).
- Deduplicate acknowledgements by `task_id` + `original_event_id` + `state`.

`LINK_STATUS` metrics (required):
- `link_id`, `latency_ms`, `packet_loss_pct`, `throughput_bps`.
- Optional: `rssi_dbm`, `snr_db`, `jitter_ms`, `reason_code`, `interface`.

`TIME_STATUS` metrics (required):
- `time_source`, `sync_state`, `est_error_ms`, `last_sync_ts`.
- `est_error_ms` is the worst-case absolute timestamp error upper bound.
- `state` (v1.1.0 only): enum `LOCKED`, `HOLDOVER`, `UNSYNCED`, `UP`,
  `DEGRADED`, `DOWN`, the Class B constraint adopted 2026-07-27 (doctrine
  R1-11-15), matching the sibling-branch pattern so a self-contradicting
  timing event is visible to the kernel. The locked v1.0 branch constrains
  `metrics` only and leaves `state` a free string.

`SCHEMA_VIOLATION` metrics:
- `reason_code`, `original_event_id`, optional `path`, `error`.
- Use for schema/policy diagnostics, including rejected events and warnings
  about accepted events. Do not reuse as a generic trust, quarantine, lifecycle,
  or operational status label.

## Enums (Common)

`event_type`:
- `OBSERVATION_EVENT`
- `INFERENCE_EVENT`
- `FUSION_EVENT`
- `STATE_EVENT`
- `COMMAND_EVENT`
- `SYSTEM_EVENT`

`event_subtype` (common):
- OBSERVATION_EVENT: `RF`, `EO`, `IR`, `ACOUSTIC`, `NETWORK`
- INFERENCE_EVENT: `CLASSIFICATION`, `ASSOCIATION`, `ANOMALY`, `BEHAVIOR`
- FUSION_EVENT: `TRACK_FUSION`
- STATE_EVENT: `TRACK_STATE`
- COMMAND_EVENT: `GOTO`, `ORBIT`, `HOLD`, `SEARCH_BOX`
- SYSTEM_EVENT: `TASK_ACK`, `LINK_STATUS`, `TIME_STATUS`, `SCHEMA_VIOLATION`
- Experimental v1.1.0 COMMAND_EVENT: `RETURN_TO_BASE`, `LAND`, `LOITER`,
  `SCAN_RF`, `TRACK_TARGET`, `CHANGE_SENSOR_MODE`
- Experimental v1.1.0 SYSTEM_EVENT: `SENSOR_STATUS`, `PLATFORM_STATUS`

`node_role`:
- `EDGE`, `GATEWAY`, `APEX`, `DMZ`, `CLOUD`

`profile`:
- `L`, `M`, `H`

`system_type`:
- `TASK_ACK`, `LINK_STATUS`, `TIME_STATUS`, `SCHEMA_VIOLATION`
- Experimental v1.1.0: `SENSOR_STATUS`, `PLATFORM_STATUS`

`task_type`:
- `GOTO`, `ORBIT`, `HOLD`, `SEARCH_BOX`
- Experimental v1.1.0: `RETURN_TO_BASE`, `LAND`, `LOITER`, `SCAN_RF`, `TRACK_TARGET`, `CHANGE_SENSOR_MODE`
- v1.1.0 expanded task types have task-specific required fields in the schema
  and semantic contract.

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
