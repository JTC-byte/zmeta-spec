# Subtype registry — seed

**Status:** Proposed for v1.2.0. **Advisory, not normative.** This is a
*seed* for a community-maintained registry of commonly-used
`event.event_subtype` values. None of the entries here are required;
adopters may use any other subtype string they want, subject to the
naming guidance in `spec/mqtt-bindings.md`.

## Purpose

The ZMeta spec deliberately leaves `event.event_subtype` free-form so
adopters can describe their domain. In practice, adopters keep
re-inventing similar values for the same concepts (`ais_track` vs
`AISTrack` vs `ais-vessel-track`). A reference catalog lets new adopters
reach for an existing convention before inventing a variant.

This document seeds that catalog with subtypes observed in production
deployments. If accepted upstream, the maintainer may move it to a
machine-readable registry file (`spec/subtype-registry.yaml` or similar)
that adapters can validate against.

## OBSERVATION_EVENT subtypes

Sensor measurements of things in the world. Topic shape:
`observation/<subtype>/<id>`.

| Subtype | Domain | Notes |
|---|---|---|
| `ais_track` | maritime | Payload: kinematics + AIS identity. id = MMSI. |
| `adsb_track` | air | Payload: kinematics + ADS-B identity. id = ICAO24 hex. |
| `eo_detection` | EO | Camera-derived detection. |
| `rf_detection` | RF | Generic RF detection (radar, signal). |
| `rf_spectrum_sweep` | RF | High-frequency spectrum scan. CBOR-encoded for size. |
| `rf_heatmap` | RF | Quantized matrix per AOR. CBOR-encoded. |
| `fmv_track` | air/EO | Gimbal-tracked platform motion from MISB ST 0601. |
| `fmv_klv` | EO | Per-tick gimbal pointing + frame-center viewpoint from a parsed KLV stream. |
| `sonar_detection` | subsurface | Water-column object detection. |
| `external_track` | catch-all | Tracks from an external C2 with no native subtype. |

## INFERENCE_EVENT subtypes

Processed conclusions drawn from observations. Topic shape:
`inference/<subtype>/<id>`.

| Subtype | Notes |
|---|---|
| `bond_assigned` | Fusion correlation protocol; per-sensor target. Convention defined in `docs/v1.2-event-types-conventions.md`. |
| `bond_dissolved` | Atomic split: dissolved + new_bonds in one event. |
| `classification` | Disposition / classification update for a correlated entity. |
| `classified_vessel` | Vessel classification with confidence (maritime-specific). |
| `command_ack` | Per-command outcome: `ack` / `rejected` / `error` with message. |
| `geofence_alert` | Track inside an alert zone or boundary crossing. |

## FUSION_EVENT subtypes

Multi-source synthesized estimates. Topic shape: `fusion/<subtype>/<id>`.

| Subtype | Notes |
|---|---|
| `multi_source_track` | Authoritative track for one correlation_id; renders as a single map entity. |
| `rf_emitter` | RF emitter fix from DF-bearing triangulation. |

## STATE_EVENT subtypes

Current state of an entity. Topic shape: `state/<subtype>/<id>`.
Typically retained on MQTT.

| Subtype | Cardinality | Notes |
|---|---|---|
| `asset` | single | Real platform with kinematics. |
| `sensor` | single | Sub-sensor of an asset (camera, radar, sonar). |
| `comms_node` | single | Physical radio in the field. |
| `task_definition` | single | Task lifecycle in payload (e.g., Lattice Task shape). |
| `aor` | single | Operator-drawn area of responsibility. |
| `geo` | single | Operator-drawn geo constraint (zones, control areas). |

## COMMAND_EVENT subtypes

Imperatives directed at entities or services. Topic shape:
`command/<subtype>/<id>`. Usually NOT retained.

| Subtype | Notes |
|---|---|
| `asset_task` | Task dispatched to a specific asset. |
| `task_action` | Cancel / pause / resume / complete. |
| `sensor_control` | Sensor parameter commands (e.g., RF retune). |

## SYSTEM_EVENT subtypes

Operational events about the system itself. Topic shape:
`system/<subtype>/<id>`.

| Subtype | Cardinality | Notes |
|---|---|---|
| `heartbeat` | single | Service heartbeat with timestamp. Retained, short keepalive. |
| `ingestor_fleet` | snapshot | Per-ingestor running map. Retained. |
| `node_metrics` | single | Real-time node telemetry (~5 s cadence). |
| `node_health` | single | Node health summary. |
| `broker_election` | single | Broker VIP holder (VRRP). Retained. |

## Process for additions

If/when this seed becomes a maintained registry, additions should:

1. Document the payload shape, even if not a normative schema (a
   `payload_schema_uri` is recommended).
2. Note retain/cardinality semantics on MQTT.
3. Identify the producer pattern (which kind of service emits this).
4. Avoid duplicating an existing subtype's purpose under a different
   name.

## What's NOT in this seed

Subtypes that are highly deployment-specific have been intentionally
omitted. Example categories:

- LoRa-specific topics (`lora_text`, `lora_position`, `lora_node`,
  `lora_nodedb`)
- MediaMTX / stream-relay (`stream_offer`, `stream_routing`,
  `stream_subscribe`, `stream_unsubscribe`)
- Transport plane controls (`transport_control`, `pipeline_runtime`)
- Simulation hooks (`sim_ground_truth`)

These are real subtypes in active deployments; they're just not
broadly enough applicable to warrant being in a reference registry.
A deployment may freely use them or any others.
