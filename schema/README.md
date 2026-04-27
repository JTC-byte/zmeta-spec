# Schema

JSON Schema definitions for ZMeta.

- `zmeta-event-1.0.schema.json` - ZMeta v1.0 (Draft 2020-12)
- `zmeta-event-1.1.0.schema.json` - experimental ZMeta v1.1.0 extension (Draft 2020-12)
- `proto/zmeta_event_v1.proto` - experimental protobuf transport projection

The locked normative contract is v1.0. v1.1.0 is kept as a proposed compatibility
extension and must still preserve the v1.0 semantic boundaries.

The protobuf schema is an encoding projection only. Decoded protobuf events must
still validate against the JSON Schema and policy pack.

## v1.1.0 Changes (relative to v1.0)

### Modality-Specific Feature Schemas
Conditional feature validation for all modalities (extends existing RF pattern):
- **EO** supports raw sensor geometry such as `bbox`, `fov_deg`, and `resolution_px`; semantic labels and detector confidence remain INFERENCE_EVENT fields.
- **IR** requires `band` (MWIR/LWIR/SWIR/NIR); optional `temperature_k`, `emissivity`; semantic labels and detector confidence remain INFERENCE_EVENT fields.
- **ACOUSTIC** requires `center_freq_hz`, `power_db`; optional `duration_ms`, `source_type`
- **NETWORK** requires `protocol`; optional `source_addr`, `dest_addr`, `port`

### Expanded Modality Enum
Added: `RADAR`, `LIDAR`, `MAGNETIC`, `SEISMIC`, `CYBER`, `SIGINT`

### Structured Quality Block
`quality` now has typed optional properties: `measurement_error`, `error_metric`,
`snr_db`, `calibration_state`, `geo_status`. All optional, `additionalProperties: true`.

### Geo-Absent Support
`quality.geo_status` enum: `AVAILABLE | UNAVAILABLE | ESTIMATED | STALE | CONFIGURED`.
Eliminates (0,0,0) sentinel pattern for GPS-denied edges.

### Error Ellipse
`geo` object now allows `error_ellipse_m` with `semi_major`, `semi_minor`,
`orientation_deg`, and optional `probability` (1_SIGMA/CEP/CE_90/CE_95).
`geo.additionalProperties` changed to `true` to support this.

### Expanded COMMAND_EVENT Task Types
Added: `RETURN_TO_BASE`, `LAND`, `LOITER`, `SCAN_RF`, `TRACK_TARGET`, `CHANGE_SENSOR_MODE`

### Formalized Orbit Geometry
`geometry` now references `$defs/orbit_geometry` with `pattern`, `radius_m`,
`direction`, `lobe_separation_m`, `arc_degrees`.

### SENSOR_STATUS and PLATFORM_STATUS
New `system_type` values with conditional metrics validation:
- **SENSOR_STATUS**: requires `sensor_id`, `operational_state`; optional `modality`, `mode`, `freq_range_hz`, etc.
- **PLATFORM_STATUS**: requires `battery_pct`; optional `endurance_remaining_sec`, `flight_mode`, `platform_type`, etc.

### data_ref
Optional `data_ref` object on `ObservationPayload` for linking events to raw captures
(IQ, video, PCAP). Requires `ref_id`; optional `store`, `kind`, `format`, `hash`, `size_bytes`.

### UUIDv7 Event Identity
`event.event_id`, `lineage.based_on`, and fusion `members` are constrained to
UUIDv7 (RFC 9562). Adapters that ingest legacy UUIDv4 or vendor identifiers must
regenerate ZMeta `event_id` values at the adapter boundary and preserve legacy
IDs in payload-scoped provenance fields when traceability is needed.

### Profile Field
Inherited from v1.0.3: `profile` top-level field (L/M/H) for export profile tagging.

### Compatibility
- Accepts `zmeta_version` values: `"1.0"`, `"1.0.2"`, `"1.0.3"`, `"1.1"`, `"1.1.0"`
- All new fields are optional or additive enum extensions
- Existing semantically compliant v1.0 events pass v1.1.0 validation
- `additionalProperties: true` preserved on all payload types
