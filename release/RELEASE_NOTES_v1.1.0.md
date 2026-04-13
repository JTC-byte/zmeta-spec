# ZMeta v1.1.0 Release Notes

**Status:** Proposed (develop branch)
**Compatibility:** Backward-compatible with v1.0

## Summary

ZMeta v1.1.0 is a backward-compatible extension of v1.0 driven by findings from
the Idaho Falls ISR demo (April 7-8, 2026), KrakenSDR bench testing, and
production Z-ISR fusion implementation experience.

All changes are additive. Existing valid v1.0 events pass v1.1.0 validation
without modification.

## Changes

### Multi-Modality Feature Schemas

Only RF had conditional feature validation in v1.0. v1.1.0 adds conditional
`features` schemas for all declared modalities:

| Modality  | Required Features                 | New in v1.1 |
|-----------|-----------------------------------|-------------|
| RF        | `center_freq_hz`, `bandwidth_hz`, `power_dbm` | No (v1.0) |
| EO        | `class_name`, `confidence`        | Yes |
| IR        | `band`                            | Yes |
| ACOUSTIC  | `center_freq_hz`, `power_db`      | Yes |
| NETWORK   | `protocol`                        | Yes |

New modality enum values: `RADAR`, `LIDAR`, `MAGNETIC`, `SEISMIC`, `CYBER`, `SIGINT`.

### Structured Quality Block

The `quality` object gains typed optional properties:
- `measurement_error` (number) -- 1-sigma error in primary measurement unit
- `error_metric` (enum) -- how measurement_error is expressed
- `snr_db` (number) -- signal-to-noise ratio
- `calibration_state` (enum) -- CALIBRATED / UNCALIBRATED / DEGRADED
- `geo_status` (enum) -- AVAILABLE / UNAVAILABLE / ESTIMATED / STALE / CONFIGURED

`additionalProperties: true` is preserved, so vendor-specific quality fields
remain valid.

### GPS-Denied / Geo-Absent Support

`quality.geo_status` replaces the (0,0,0) sentinel pattern used by GPS-denied
edges. Producers set `geo_status: "UNAVAILABLE"` when no GPS fix is available,
or `geo_status: "CONFIGURED"` when position is injected from config.

### Error Ellipse

`geo.error_ellipse_m` is now a typed optional object:
- `semi_major`, `semi_minor` (meters)
- `orientation_deg` (degrees from true north)
- `probability` (1_SIGMA / CEP / CE_90 / CE_95)

`geo.additionalProperties` changed from `false` to `true` to accommodate this.

### Expanded COMMAND_EVENT

New `task_type` values:
- `RETURN_TO_BASE`, `LAND`, `LOITER` (navigation)
- `SCAN_RF`, `TRACK_TARGET`, `CHANGE_SENSOR_MODE` (sensor-directed)

`geometry` now references a typed `orbit_geometry` definition with `pattern`,
`radius_m`, `direction`, `lobe_separation_m`, `arc_degrees`.

### SENSOR_STATUS and PLATFORM_STATUS

New `system_type` values for health reporting:
- **SENSOR_STATUS**: sensor health, calibration, mode, capabilities
- **PLATFORM_STATUS**: battery, endurance, flight mode, platform type

This separates sensor/platform health from link health (LINK_STATUS) and enables
capability-aware retasking without out-of-band configuration.

### data_ref

Optional `data_ref` object on `ObservationPayload` for linking events to raw
captures. Formalizes the Appendix A convention from the semantic contract.

### UUID Pattern Relaxation

UUID regex relaxed from strict UUIDv7 to accept any valid UUID format.
Producers SHOULD use UUIDv7 for time-ordering benefits, but the schema
does not reject v4 or other variants.

## Migration Guide

No migration required. All existing v1.0 events are valid under v1.1.0.

Producers upgrading to v1.1.0 should:
1. Set `zmeta_version` to `"1.1.0"` (or `"1.1"`)
2. Add `quality.geo_status` to observations where GPS provenance matters
3. Use structured `quality` fields instead of vendor-specific feature fields
4. Use `SENSOR_STATUS` / `PLATFORM_STATUS` instead of shoehorning health
   data into `LINK_STATUS`
