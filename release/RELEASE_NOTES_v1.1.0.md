# ZMeta v1.1.0 Release Notes

**Status:** Proposed / Experimental (not locked)
**Compatibility:** Backward-compatible semantics; schema validation is strict by
`zmeta_version`

## Summary

ZMeta v1.1.0 is a backward-compatible extension of v1.0 driven by findings from
the Idaho Falls ISR demo (April 7-8, 2026), KrakenSDR bench testing, and
production Z-ISR fusion implementation experience.

Existing semantically compliant v1.0 events remain valid through the canonical
version-discriminated schema's v1.0 branch. They do not validate against the
standalone v1.1.0 branch unless upgraded to `zmeta_version: "1.1.0"`. Proposed
v1.1 fields must still respect the locked v1.0 semantic contract, especially the
OBSERVATION vs INFERENCE boundary.

The canonical and version-specific schemas now enforce `event.event_subtype` as
a semantic discriminator. OBSERVATION, INFERENCE, COMMAND, and SYSTEM subtypes
must match the corresponding payload discriminator (`modality`,
`inference_type`, `task_type`, or `system_type`); FUSION and STATE use fixed
subtypes.

When `profile` is present, schemas now enforce claimed export-profile event-type
rules. Profile L permits only STATE, SYSTEM, and COMMAND events; Profile M
permits OBSERVATION, FUSION, STATE, SYSTEM, and COMMAND events; Profile H permits
all valid event types.

INFERENCE_EVENT payloads remain flexible for model-specific claims, but they now
reject `track_id`, `members`, and `estimated_state` both at the payload root and
inside `payload.claim`. This keeps inference outputs from crossing into fusion or
state authority.

STATE_EVENT payloads now reject raw observation fields such as `features`,
`raw_features`, `modality`, `measurement`, `measurements`, `t_start`, `t_end`,
`data_ref`, and `data_refs`. State traceability is carried by lineage; optional
`extensions` are reserved for state-safe UI/rendering metadata.

COMMAND_EVENT payloads are now strict. Unknown top-level command fields are
schema-invalid, command-safe metadata belongs under `payload.extensions`, and
altitude/vertical-control fields are rejected at the command root, inside
`target_geo`, inside `geometry`, and at the first level of `extensions`.

All timestamp fields now use a shared UTC-Z schema definition. Producers must
emit RFC 3339 timestamps with a trailing `Z`; offset and timezone-less wire
formats are rejected.

Observation windows now require paired `t_start` and `t_end` values. RF windowed
observations must set `event.ts` to the window midpoint within the documented
1 ms semantic-validation tolerance.

Scalar `speed_mps` values are now constrained to be non-negative. Heading and
bearing angles preserve the contract range of 0-360 inclusive; producers may
normalize 360 to 0, but consumers must accept both.

## Changes

### Multi-Modality Feature Schemas

Only RF had conditional feature validation in v1.0. v1.1.0 adds conditional
`features` schemas for active observation modalities:

| Modality  | Required Features                 | New in v1.1 |
|-----------|-----------------------------------|-------------|
| RF        | `center_freq_hz`, `bandwidth_hz`, `power_dbm` | No (v1.0) |
| EO        | Raw image geometry such as `roi_px`, `fov_deg`, `resolution_px` | Yes |
| IR        | `band`                            | Yes |
| ACOUSTIC  | `center_freq_hz`, `spl_db`        | Yes |
| NETWORK   | `protocol`                        | Yes |

Additional observation modality names such as `RADAR`, `LIDAR`, `MAGNETIC`,
`SEISMIC`, `CYBER`, and `SIGINT` are reserved until their feature contracts are
defined. SENSOR_STATUS may still use those labels to describe sensor capability
where schema permits; that does not make them valid OBSERVATION_EVENT
modalities.

EO observation `roi_px` is defined as raw image ROI/crop coordinates. Detected
object boxes remain `INFERENCE_EVENT.claim.bbox`; `features.bbox` is invalid in
EO OBSERVATION_EVENT.

ACOUSTIC observation features are limited to measured signal facts. Semantic
labels such as `source_type` / rotor / engine / voice are schema-invalid in
OBSERVATION_EVENT and must be emitted as INFERENCE_EVENT with lineage.

### Structured Quality Block

The `quality` object gains typed optional properties:
- `measurement_error` (object) -- explicit `value`, `unit`, and `metric`
- `snr_db` (number) -- signal-to-noise ratio
- `calibration_state` (enum) -- CALIBRATED / UNCALIBRATED / DEGRADED
- `geo_status` (enum) -- AVAILABLE / UNAVAILABLE / ESTIMATED / STALE / CONFIGURED

`additionalProperties: true` is preserved, so vendor-specific quality fields
remain valid.
The old scalar `measurement_error` plus sibling `error_metric` pattern is
schema-invalid in v1.1.0 because it requires unit inference by consumers.

### GPS-Denied / Geo-Absent Support

`quality.geo_status` replaces the (0,0,0) sentinel pattern used by GPS-denied
edges. Producers set `geo_status: "UNAVAILABLE"` when no GPS fix is available,
or `geo_status: "CONFIGURED"` when position is injected from config.

### Error Ellipse

`geo.error_ellipse_m` is now a typed optional object:
- `semi_major`, `semi_minor` (meters)
- `orientation_deg` (degrees from true north)
- `probability` (1_SIGMA / CEP / CE_90 / CE_95)

Canonical `geo` remains strict. v1.1.0 permits only `lat`, `lon`, `alt_m`, and
the controlled `error_ellipse_m` uncertainty block; alternate datums and
non-HAE altitude references remain schema-invalid.

### Expanded COMMAND_EVENT

New `task_type` values:
- `RETURN_TO_BASE`, `LAND`, `LOITER` (navigation)
- `SCAN_RF`, `TRACK_TARGET`, `CHANGE_SENSOR_MODE` (sensor-directed)

`ORBIT` geometry now references a typed `orbit_geometry` definition with
`pattern`, `radius_m`, `direction`, `lobe_separation_m`, `arc_degrees`.
Task-specific validation is enforced for ambiguous task types: `GOTO` cannot
carry orbit geometry, `ORBIT` requires orbit geometry, `SEARCH_BOX` requires
search-box geometry, `SCAN_RF` requires `sensor_id`, `freq_range_hz`, and
`dwell_ms`, `TRACK_TARGET` requires `target_track_id`, and
`CHANGE_SENSOR_MODE` requires `sensor_id` and `sensor_mode`.

### SENSOR_STATUS and PLATFORM_STATUS (Proposed)

New `system_type` values for health reporting:
- **SENSOR_STATUS**: sensor health, calibration, mode, capabilities
- **PLATFORM_STATUS**: battery, endurance, flight mode, platform type

This separates sensor/platform health from link health (LINK_STATUS) and enables
capability-aware retasking without out-of-band configuration.
For SENSOR_STATUS, `payload.state` is the single operational state;
`metrics.operational_state` is invalid to avoid contradictory health metadata.
PLATFORM_STATUS is not battery-specific: at least one of `battery_pct`,
`fuel_remaining_pct`, `endurance_remaining_ms`, or `power_state` is required, and
`endurance_remaining_sec` is invalid in v1.1.0.

### data_ref / data_refs

Optional `data_ref` object or `data_refs` array on `ObservationPayload` for
linking events to raw captures. Formalizes the Appendix A convention from the
semantic contract.
Only one pointer style is valid per payload (`data_ref` xor `data_refs`). Pointer
objects are strict metadata only, `hash` uses `sha256:<64 hex chars>` when
provided, and pointer `t_start` / `t_end` values must be paired.

### UUIDv7 Event Identity

UUID validation is aligned with the semantic contract: ZMeta `event_id` values,
lineage references, and fusion member IDs must be UUIDv7. Adapters translating
legacy UUIDv4 or vendor identifiers must regenerate ZMeta event IDs at the
adapter boundary and preserve legacy IDs in payload provenance when needed.

## Migration Guide

Existing semantically compliant v1.0 events remain valid when validated through
the canonical version-discriminated schema. Producers that emitted non-UUIDv7
identifiers must regenerate ZMeta event IDs before validation.

Producers upgrading to v1.1.0 should:
1. Set `zmeta_version` to exactly `"1.1.0"`
2. Add `quality.geo_status` to observations where GPS provenance matters
3. Use structured `quality` fields instead of vendor-specific feature fields
4. Use `SENSOR_STATUS` / `PLATFORM_STATUS` instead of shoehorning health
   data into `LINK_STATUS`
5. Route producer-specific legacy wire cleanup through the opt-in compatibility
   normalizer before validation; do not rely on the normative schema accepting
   aliases or legacy fields.

## Policy and Runtime Enforcement

v1.1.0 adds executable policy support for rules that require deployment or stream
context:
- `policy/producer-authority.yaml` constrains which producer identities may emit
  each event type.
- `policy/timing-freshness.yaml` defines maximum TIME_STATUS age by profile and
  supports warn/degrade/reject behavior.
- `policy/lineage.yaml` validates payload/envelope lineage consistency, parent
  type rules, and unresolved-parent handling by profile.
- `policy/violation-codes.yaml` provides the SCHEMA_VIOLATION diagnostic
  vocabulary while TASK_ACK remains task-specific.

## Compatibility Normalizer

The release includes non-normative opt-in tooling for migration workflows:
`tools/compat_normalize.py` and `tools/compat_normalizer.py`.

Strict schema and conformance behavior is unchanged. Compatibility normalization
must run before validation and records a sidecar report for every change. It can
normalize selected legacy forms only when explicitly enabled:
- `zmeta_version: "1.1"` -> `"1.1.0"`
- `endurance_remaining_sec` -> `endurance_remaining_ms`
- EO `features.bbox` -> `features.roi_px` only when the caller asserts it is ROI
  metadata, not object detection.

## Conformance and Examples

The conformance pack now includes valid and invalid regression fixtures for
version discrimination, Profile L restrictions, inference authority boundaries,
state projection boundaries, command altitude safety, UTC-Z timestamps, RF
window pairing, geodesy strictness, explicit quality units, health-status
constraints, reason codes, data references, and v1.1.0 extension behavior.

Runnable examples now validate through the canonical version-discriminated
schema, including the v1.1.0 example corpus.

## Final Validation

Release validation was run locally on 2026-04-27:
- Gateway tests: 167 passed, 106 subtests passed
- Adapter tests: 19 passed
- Schema Draft 2020-12 lint: ok
- Strict examples: 40 passed
- Strict conformance: ok
- End-to-end workflows: H, M, and L passed

Contract hashes:
- `schema_hash=3f5f615c1539043f48a612a225421176aace9b3fb3a2507ea43dc31fe5bf1023`
- `policy_hash=70d8dc2b21641e44772e96c28989aa2a93211c2fba1e4c992ea12c8374bb1b16`
- `semantics_hash=bdc3c31e5c206cb667899d06aebf6576a43502af400f6f1e0e15ded65ada367b`
- `contract_hash=4fa2f874f17f15e9af1424672563c3fad32e6dc5a62efda4fa9f692f8f186833`
