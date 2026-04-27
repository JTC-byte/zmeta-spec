# Schema

JSON Schema definitions for ZMeta.

- `zmeta-event.schema.json` - canonical version-discriminated ZMeta event schema
  (Draft 2020-12)
- `zmeta-event-1.0.schema.json` - ZMeta v1.0 (Draft 2020-12)
- `zmeta-event-1.1.0.schema.json` - experimental ZMeta v1.1.0 extension (Draft 2020-12)
- `proto/zmeta_event_v1.proto` - experimental protobuf transport projection

`zmeta-event.schema.json` is the preferred validation entry point for integrations
that need to accept more than one supported version. It dispatches strictly on
`zmeta_version`: v1.0 events validate only against the v1.0 vocabulary, and
v1.1.0 events validate only against the v1.1.0 vocabulary.

The locked normative contract is v1.0. v1.1.0 is kept as a proposed compatibility
extension and must still preserve the v1.0 semantic boundaries. v1.1.0-only
concepts must not validate when an event claims `zmeta_version: "1.0"`.

The protobuf schema is an encoding projection only. Decoded protobuf events must
still validate against the JSON Schema and policy pack.

## Timestamp Handling

Timestamp fields use the shared `utcDateTime` definition. Values must be RFC
3339 date-time strings serialized in UTC with a trailing `Z`, for example
`2025-01-17T14:30:00Z` or `2025-01-17T14:30:00.123Z`. Offset forms such as
`2025-01-17T09:30:00-05:00` and timezone-less strings are schema-invalid.

Observation windows must provide `t_start` and `t_end` as a pair. RF windowed
observations are also checked by semantic validation: `event.ts` must equal the
window midpoint within a 1 ms tolerance.

## Event Subtype Discrimination

`event.event_subtype` is constrained by `event.event_type` and must match the
payload discriminator exactly:

- OBSERVATION_EVENT: `event_subtype == payload.modality`
- INFERENCE_EVENT: `event_subtype == payload.inference_type`
- COMMAND_EVENT: `event_subtype == payload.task_type`
- SYSTEM_EVENT: `event_subtype == payload.system_type`
- FUSION_EVENT: `event_subtype == "TRACK_FUSION"`
- STATE_EVENT: `event_subtype == "TRACK_STATE"`

Free-form adapter labels such as legacy `RF_OBSERVATION` or `MISSION_TASK` are
not valid subtypes. Put adapter-specific labels in payload-scoped provenance
fields instead.

## Inference Authority Boundaries

INFERENCE_EVENT payloads remain flexible for model-specific claim content, but
they cannot contain `track_id`, `members`, or `estimated_state` at the payload
root or inside `payload.claim`. Track identity and fused state belong to
FUSION_EVENT and STATE_EVENT authority.

## State Projection Boundaries

STATE_EVENT payloads are compact operator-facing track projections. They may use
state-safe fields such as `track_id`, `geo`, `class`, `source_summary`,
`heading_deg`, `speed_mps`, `valid_for_ms`, and UI/rendering `extensions`, but
they cannot contain raw observation fields: `features`, `raw_features`,
`modality`, `measurement`, `measurements`, `t_start`, `t_end`, `data_ref`, or
`data_refs`. Traceability belongs in `lineage.based_on`.
Scalar `speed_mps` values are non-negative. Heading and bearing angles keep the
contract range of 0-360 inclusive; adapters may normalize 360 to 0 before
emission, but both values are valid.

## Command Safety Boundaries

COMMAND_EVENT payloads are strict because tasking is safety-sensitive. Arbitrary
command metadata belongs in `payload.extensions`; unknown top-level command
fields are schema-invalid. Commands cannot specify altitude at the payload root,
inside `target_geo`, inside `geometry`, or at the first level of `extensions`.
Vertical selection and deconfliction stay outside ZMeta command metadata.

## Profile Export Constraints

`profile` remains optional. When present, schemas enforce that the claimed export
profile permits the event type:

- Profile L permits `STATE_EVENT`, `SYSTEM_EVENT`, and `COMMAND_EVENT`.
- Profile M permits `OBSERVATION_EVENT`, `FUSION_EVENT`, `STATE_EVENT`,
  `SYSTEM_EVENT`, and `COMMAND_EVENT`; it does not export `INFERENCE_EVENT`.
- Profile H permits all valid event types.

## v1.1.0 Changes (relative to v1.0)

### Modality-Specific Feature Schemas
Conditional feature validation for active observation modalities (extends existing RF pattern):
- **EO** supports raw sensor geometry such as `roi_px`, `fov_deg`, and
  strict `resolution_px`; `roi_px` is a crop/region-of-interest, not a detected
  object box. Detection boxes and semantic labels remain INFERENCE_EVENT claims.
- **IR** requires `band` (MWIR/LWIR/SWIR/NIR); optional `temperature_k`, `emissivity`; semantic labels and detector confidence remain INFERENCE_EVENT fields.
- **ACOUSTIC** requires measured signal facts `center_freq_hz` and `spl_db`;
  optional measured fields include `bandwidth_hz`, `duration_ms`,
  `spectral_centroid_hz`, `harmonic_count`, and `signature_hash`. Semantic
  labels such as acoustic source type belong in INFERENCE_EVENT.
- **NETWORK** requires `protocol`; optional `source_addr`, `dest_addr`, `port`

### Observation Modality Governance
Observation `payload.modality` values are allowed only when this schema defines
a feature contract. `RADAR`, `LIDAR`, `MAGNETIC`, `SEISMIC`, `CYBER`, and
`SIGINT` are reserved observation candidates until their feature contracts are
defined. These names are not valid `OBSERVATION_EVENT` modalities in v1.1.0.
SENSOR_STATUS may still describe sensor capability using broader modality labels
where the status schema allows them; that does not make those labels valid
observation payload vocabulary.

### Structured Quality Block
`quality` now has typed optional properties: `measurement_error`, `snr_db`,
`calibration_state`, `geo_status`. All optional, `additionalProperties: true`.
`measurement_error` is an object with explicit `value`, `unit`, and `metric`;
the legacy scalar `measurement_error` plus sibling `error_metric` pattern is not
valid in v1.1.0.

### Geo-Absent Support
`quality.geo_status` enum: `AVAILABLE | UNAVAILABLE | ESTIMATED | STALE | CONFIGURED`.
Eliminates (0,0,0) sentinel pattern for GPS-denied edges.

### Error Ellipse
`geo` object now allows `error_ellipse_m` with `semi_major`, `semi_minor`,
`orientation_deg`, and optional `probability` (1_SIGMA/CEP/CE_90/CE_95).
`geo` remains strict: v1.1.0 permits only `lat`, `lon`, `alt_m`, and the
controlled `error_ellipse_m` uncertainty block. Alternate datums and altitude
references are not valid canonical `geo` fields.

### Expanded COMMAND_EVENT Task Types
Added: `RETURN_TO_BASE`, `LAND`, `LOITER`, `SCAN_RF`, `TRACK_TARGET`, `CHANGE_SENSOR_MODE`
with task-specific validation. For example, `SCAN_RF` requires `sensor_id`,
`freq_range_hz`, and `dwell_ms`; `TRACK_TARGET` requires `target_track_id`; and
`CHANGE_SENSOR_MODE` requires `sensor_id` and `sensor_mode`.

### Task-Specific Command Geometry
Command `geometry` is validated by `task_type`. `GOTO`, `HOLD`,
`RETURN_TO_BASE`, `LAND`, `SCAN_RF`, `TRACK_TARGET`, and
`CHANGE_SENSOR_MODE` do not accept geometry. `ORBIT` uses
`$defs/orbit_geometry`, `SEARCH_BOX` uses `$defs/search_box_geometry`, and
`LOITER` uses `$defs/loiter_geometry`.

### SENSOR_STATUS and PLATFORM_STATUS
New `system_type` values with conditional metrics validation:
- **SENSOR_STATUS**: `payload.state` is the single operational state and
  `metrics.sensor_id` is required; optional `modality`, `mode`, `freq_range_hz`,
  etc. describe capability. `metrics.operational_state` is invalid.
- **PLATFORM_STATUS**: requires at least one of `battery_pct`,
  `fuel_remaining_pct`, `endurance_remaining_ms`, or `power_state`; optional
  `flight_mode`, `platform_type`, etc. describe availability. Legacy
  `endurance_remaining_sec` is invalid in v1.1.0.

### data_ref / data_refs
Optional `data_ref` object or `data_refs` array on `ObservationPayload` for
linking events to raw captures (IQ, video, PCAP). Each pointer requires `ref_id`;
optional fields include `store`, `kind`, `format`, `hash`, and `size_bytes`.
v1.1.0 permits one pointer style per payload (`data_ref` xor `data_refs`).
Pointer objects are strict metadata only, `hash` must be `sha256:<64 hex chars>`
when present, and pointer `t_start` / `t_end` timestamps must be paired.

### UUIDv7 Event Identity
`event.event_id`, `lineage.based_on`, and fusion `members` are constrained to
UUIDv7 (RFC 9562). Adapters that ingest legacy UUIDv4 or vendor identifiers must
regenerate ZMeta `event_id` values at the adapter boundary and preserve legacy
IDs in payload-scoped provenance fields when traceability is needed.

### Profile Field
Inherited from v1.0.3: `profile` top-level field (L/M/H) for export profile tagging.

### Compatibility
- `zmeta-event-1.0.schema.json` accepts exactly `zmeta_version: "1.0"`
- `zmeta-event-1.1.0.schema.json` accepts exactly `zmeta_version: "1.1.0"`
- The canonical `zmeta-event.schema.json` uses `oneOf` to select exactly one
  version branch by `zmeta_version`
- Non-normative compatibility adapters may normalize aliases such as `"1.1"` to
  `"1.1.0"` before schema validation; aliases are not accepted by normative schemas
- The optional `tools/compat_normalize.py` helper performs conservative
  adapter-side normalization before schema validation and records a sidecar
  change report. It is disabled by default and is not part of strict
  conformance.
- New fields are optional unless a v1.1.0 task or system subtype explicitly
  selects them as part of its validation contract
- Existing semantically compliant v1.0 events pass the canonical schema via the
  v1.0 branch, not the v1.1.0 branch
- `additionalProperties: true` preserved on all payload types
