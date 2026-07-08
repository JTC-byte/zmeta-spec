# Deployment Concept Crosswalk - Mapping Common Domain Concepts to Canonical ZMeta Vocabulary

Status: advisory (Docs/advisory change class), non-normative.
Current release context: ZMeta v1.1.11.

This document is a dictionary-to-alphabet table. It changes no validation
rule, no dispatch behavior, no schema, and no policy. When anything here
appears to conflict with a governed source, the governed source wins, in this
order: `spec/semantics-contract.md` (v1.0 Locked), the canonical schemas under
`schema/`, and the policy pack under `policy/`. Change process and authority
order are defined in `AGENTS.md` and `docs/zmeta_change_governance.md`.

The deployment concepts in the left-hand columns below were harvested from a
real at-scale deployment, documented by an external contributor in
[PR #4](https://github.com/JTC-byte/zmeta-spec/pull/4). Crediting that PR as
the source of the observed field conventions is not an endorsement of its
proposed mechanism: the PR expressed these concepts as free-form
`event_subtype` values, which the locked kernel rejects (contract Section
7.3). This document re-derives the same operational needs from the kernel
outward.

## Why This Document Exists

ZMeta ships an alphabet, not a dictionary. The kernel defines a small set of
composable primitives - six event families, locked subtype enums, confidence
and lineage rules, authority boundaries - and it is generatively complete:
the concepts adopters keep inventing names for are almost always spellable
with the letters that already exist.

Inventing a private subtype (`ais_track`, `geofence_alert`, `heartbeat`)
feels convenient and costs nothing locally. Globally it creates a dialect:
every consumer that dispatches on the locked vocabulary either rejects the
event (`EVENT_SUBTYPE_MISMATCH`) or silently ignores it, and the
interoperability promise - adapt once, interoperate with everything - breaks
for everyone downstream. Contract Section 7.3 is explicit: producers MUST NOT
use free-form subtypes, and adapter/vendor labels belong in payload-scoped
provenance or ignorable extensions, never in `event_subtype`.

So before reaching for a new name, use this crosswalk: find the concept,
spell it with the locked alphabet.

## The Locked Alphabet at a Glance

Valid `event_type` / `event_subtype` vocabulary (contract Sections 7.2, 7.3,
and 21):

| event_type | Locked subtypes (v1.0) | v1.1.0 experimental additions |
|---|---|---|
| `OBSERVATION_EVENT` | `RF`, `EO`, `IR`, `ACOUSTIC`, `NETWORK` | (feature contracts formalized; no new modalities) |
| `INFERENCE_EVENT` | `CLASSIFICATION`, `ASSOCIATION`, `ANOMALY`, `BEHAVIOR` | - |
| `FUSION_EVENT` | `TRACK_FUSION` | - |
| `STATE_EVENT` | `TRACK_STATE` | - |
| `COMMAND_EVENT` | `GOTO`, `ORBIT`, `HOLD`, `SEARCH_BOX` | `RETURN_TO_BASE`, `LAND`, `LOITER`, `SCAN_RF`, `TRACK_TARGET`, `CHANGE_SENSOR_MODE` |
| `SYSTEM_EVENT` | `LINK_STATUS`, `TIME_STATUS`, `SCHEMA_VIOLATION`, `TASK_ACK` | `SENSOR_STATUS`, `PLATFORM_STATUS` |

Cross-cutting rules that shape every mapping below:

- Top-level `confidence` is mandatory for `INFERENCE_EVENT`, `FUSION_EVENT`,
  and `STATE_EVENT`; it is prohibited for `OBSERVATION_EVENT`,
  `COMMAND_EVENT`, and `SYSTEM_EVENT` (contract 7.1, 8.1).
- `lineage.based_on` is mandatory for `INFERENCE_EVENT`, `FUSION_EVENT`, and
  `STATE_EVENT` (contract 4.8).
- Only fusion-authorized producers create `track_id` (contract 4.5, 7.6,
  13.1).
- v1.1.0-only vocabulary requires `zmeta_version: "1.1.0"` and never
  validates as `"1.0"` (contract 2.2).

## Crosswalk: External Tactical Tracks

| Deployment concept | Canonical ZMeta expression | Notes |
|---|---|---|
| `ais_track`, `adsb_track`, `external_track`, external C2 / COP track feeds | `STATE_EVENT` / `TRACK_STATE` via the contract 4.5.1 external-promotion path | Never a free-form observation subtype. AIS, ADS-B, CoT, JREAP, and vendor COP tracks are external reports or lossy projections, not measurements your sensor made. If the deployment needs them as authoritative operator state, they enter through promotion: a new UUIDv7 `event_id`, promotion evidence in `payload.extensions.external_promotion` (state category, origin kind, promotion policy ID, trust reference, lineage status, loop/reflection status, confidence basis, and - per profile - projection ID, source event UID, freshness; see `policy/producer-authority.yaml`), and a `lineage.transform` of the `promote:<adapter>:<policy>` form. Confidence must be grounded in an explicit basis and never rises just because an external system reported the track. The reference policy rejects promotion without this evidence. Contract 4.5.1 reserves a possible future `OBSERVATION_EVENT` subtype for network/tactical reports; it is not valid vocabulary today. |
| Re-imported CoT/TAK track that originated as a ZMeta projection | Rejected at the promotion boundary (loop/reflection check) | A reflected projection is never equal to the original. Loop/reflection risk stays a hard rejection unless policy deliberately softens it with equivalent audit diagnostics (contract 4.5.1, Section 14). |

## Crosswalk: Sensor Detections and Measurements

| Deployment concept | Canonical ZMeta expression | Notes |
|---|---|---|
| `eo_detection` | `OBSERVATION_EVENT` / `EO` **plus** `INFERENCE_EVENT` / `CLASSIFICATION` | A "detection" bundles two ZMeta letters. The raw frame metadata (image region, field of view, resolution - the v1.1.0 EO feature contract) is the observation. The detected-object claim - bounding box, class name, detector confidence - is an inference with mandatory `confidence`, `lineage.based_on` pointing at the observation, and `payload.model.name`/`version` (contract 7.4, 21.4). A `confidence: 0.82` on an observation payload is invalid: observation payloads ban `confidence`, `classification`, `label`, `class_name`, `entity_class`, and `track_id`. |
| `sonar_detection` | `OBSERVATION_EVENT` / `ACOUSTIC` | Water-column measured signal facts (center frequency, sound pressure level per the v1.1.0 acoustic feature contract). Any semantic label ("propeller", "biologic") is `INFERENCE_EVENT` / `CLASSIFICATION` (contract 21.4). |
| `rf_detection`, `rf_spectrum_sweep`, `rf_heatmap` | `OBSERVATION_EVENT` / `RF` | The RF feature contract requires `features.center_freq_hz`, `features.bandwidth_hz`, and `features.power_dbm` (contract 7.4). Windowed sweeps carry `payload.t_start`/`payload.t_end` with `event.ts` at the window midpoint (contract 5.6). Bulk artifacts such as heatmap matrices or capture files ride out-of-band via `payload.data_ref`/`data_refs` (v1.1.0 formal behavior, contract 21.3), not inlined into the event. |
| `fmv_klv`, `fmv_track` (MISB ST 0601 streams) | KLV ingress adapter -> `OBSERVATION_EVENT` / `EO` | See `adapters/ingress/klv/`. Parsed gimbal pointing and frame-center metadata are observation features. The "track" a KLV stream implies is not ZMeta track identity - continuity across observations is minted only by fusion (`FUSION_EVENT` / `TRACK_FUSION`). |

## Crosswalk: Inference Concepts

| Deployment concept | Canonical ZMeta expression | Notes |
|---|---|---|
| `classification`, `classified_vessel` | `INFERENCE_EVENT` / `CLASSIFICATION` | Mandatory top-level `confidence`, mandatory `lineage.based_on`, mandatory `payload.model.name` and `payload.model.version` (contract 7.5, 11.1). The payload must not carry `track_id` - a classification is a claim about evidence, not an identity assertion. Domain flavor ("vessel") lives inside `payload.claim`, not in the subtype. |
| `geofence_alert` | `INFERENCE_EVENT` / `ANOMALY` or `BEHAVIOR` | A zone entry or boundary crossing is an analytic claim derived from track state or observations. Use `ANOMALY` for "this should not be here" claims and `BEHAVIOR` for pattern claims (loitering, shadowing). The zone definition itself is deployment configuration, not event vocabulary. Confidence and lineage are mandatory as for any inference. |
| `bond_assigned`, `bond_dissolved` (fusion-to-sensor correlation protocol) | `INFERENCE_EVENT` / `ASSOCIATION`, with identity changes expressed as `FUSION_EVENT` / `TRACK_FUSION` | The claim "these local tracks concern the same entity" is an association inference (see `docs/zmeta_correlation_pattern.md` for the full pattern). The stable fused identity itself is created and revised only by fusion: bond dissolution and atomic splits map to the contract 13.3 lifecycle - new `FUSION_EVENT`s with distinct `track_id` values and lineage to the original history; `track_id` values are never reused after merge, split, loss, or retirement. Inference payloads ban `track_id`, `members`, and `estimated_state`, so the association claim references its parents through lineage rather than minting identity. |
| `command_ack` | `SYSTEM_EVENT` / `TASK_ACK` | Not an inference - there is no model claim and no confidence. TASK_ACK is the governed command lifecycle: `metrics.task_id` and `metrics.original_event_id` are required; `payload.state` comes from the locked lifecycle set (`RECEIVED`, `ACCEPTED`, `REJECTED`, `EXECUTING`, `COMPLETED`, `FAILED`, `CANCELLED`, `EXPIRED`, `DUPLICATE_IGNORED`); terminal failure states require a governed `metrics.reason_code` (contract 7.9). |

## Crosswalk: Fusion Concepts

| Deployment concept | Canonical ZMeta expression | Notes |
|---|---|---|
| `multi_source_track` | `FUSION_EVENT` / `TRACK_FUSION` | This is exactly what the fusion letter spells: `track_id`, `members` (contributing event IDs), optional `estimated_state`, `stability`, `last_seen_ts`, mandatory `confidence` and `lineage.based_on` (contract 7.6). Only fusion-authorized producers create `track_id`; it must persist unchanged and be globally unique. The operator-facing rendering of the fused track is a downstream `STATE_EVENT` / `TRACK_STATE`, not the fusion event itself. |
| `rf_emitter` (DF-bearing triangulation fix) | `FUSION_EVENT` / `TRACK_FUSION` over the contributing RF observations | Cross-sensor association producing provisional continuity is fusion by definition (contract 1, 7.6). The `members` and lineage reference the RF `OBSERVATION_EVENT`s; emitter identification ("this is emitter type X") is a separate `INFERENCE_EVENT` / `CLASSIFICATION`. |

## Crosswalk: State and Tasking Concepts

| Deployment concept | Canonical ZMeta expression | Notes |
|---|---|---|
| `asset`, platform position/kinematics state | `STATE_EVENT` / `TRACK_STATE` from an authorized producer | State is emitted by state projectors and fusion nodes (contract 4.5). When the platform state arrives from a MAVLink, CoT-like, or vendor telemetry feed rather than internal fusion, it enters through the 4.5.1 promotion path - see `adapters/ingress/mavlink/` for the reference pattern (`payload.extensions.external_promotion` evidence plus a `promote:*` lineage transform). State payloads are fused summaries: the denylist bans `features`, `raw_features`, `modality`, `measurement`/`measurements`, `t_start`, `t_end`, `data_ref`, and `data_refs`, enforced recursively so nesting inside `extensions` cannot launder raw telemetry into operator-facing state (contract 7.7, `policy/semantics.yaml`). |
| `task_definition`, `asset_task`, task lifecycle | The COMMAND lane: `COMMAND_EVENT` + `SYSTEM_EVENT` / `TASK_ACK` | A task is a bounded directive, not entity state. `COMMAND_EVENT` carries `task_id` (the idempotency/dedupe key), a locked `task_type`, `valid_for_ms` TTL, and `requires_deconfliction: true`; the altitude denylist (`alt`, `alt_m`, `altitude`, `altitude_m`, `alt_hae_m`, `alt_msl_m`, `agl_m`, `target_alt_m`, `target_altitude`) is enforced recursively across payload, geometry, and extensions (contract 7.8). Task lifecycle progress is `TASK_ACK`, not a retained "task state" event. Keeping the last task visible on a broker via a retained message is transport behavior - transport is non-semantic (contract 4.6) - and does not move tasks into the STATE family. |

## Crosswalk: System Health Concepts

| Deployment concept | Canonical ZMeta expression | Notes |
|---|---|---|
| `heartbeat` | `SYSTEM_EVENT` - `LINK_STATUS` (v1.0) or `PLATFORM_STATUS` (v1.1.0) | If the heartbeat's meaning is "the link to this node is alive", `LINK_STATUS` with its required metrics (`link_id`, `latency_ms`, `packet_loss_pct`, `throughput_bps`) and states (`UP`, `DEGRADED`, `DOWN`, `UNKNOWN`) is the v1.0 spelling. If it means "the platform/service is healthy", `PLATFORM_STATUS` on the v1.1.0 branch. Liveness-by-retained-message is a transport convention, not vocabulary. |
| `node_health`, `node_metrics` | `SYSTEM_EVENT` - `PLATFORM_STATUS` / `SENSOR_STATUS` (v1.1.0) for health that downstream consumers act on; deployment-local monitoring for the rest | Sensor health, configuration, and capability state is `SENSOR_STATUS`; platform health and operating state is `PLATFORM_STATUS` (contract 21.5, 21.6). Neither may carry raw measurements, detections, classifications, or track identity. General-purpose telemetry firehoses (CPU, RAM, disk at 5-second cadence) are observability data - keep them in the deployment's monitoring stack rather than minting ZMeta events for them. |
| `broker_election`, VIP holder, service discovery | Stays deployment-local | Broker orchestration is transport-plane infrastructure. Transport carries no semantic meaning (contract 4.6), so ZMeta defines no vocabulary for it; if a broker failover degrades a link, that consequence is expressible as `LINK_STATUS`. |
| `schema_violation`, policy diagnostics | `SYSTEM_EVENT` / `SCHEMA_VIOLATION` | Already in the alphabet: the v1.0 diagnostic envelope for rejected/malformed events and soft policy decisions, with governed reason codes and `original_event_id` correlation (contract 7.9, 3.3). Do not reuse it as a trust state, lifecycle state, or general status channel. |

## Crosswalk: Node Databases and Fleet Snapshots

| Deployment concept | Canonical ZMeta expression | Notes |
|---|---|---|
| `lora_nodedb`, `ingestor_fleet`, fleet/entity snapshot containers | Per-entity events: one entity, one event | ZMeta's unit of meaning is the event about one subject. A node database or fleet roster decomposes into per-entity events, each with its own identity, lineage, and TTL: platforms with position project as individual `STATE_EVENT` / `TRACK_STATE` events (through promotion if sourced from an external mesh/telemetry feed); per-node radio or service health projects as individual `SYSTEM_EVENT` status events. An aggregate "snapshot" container - one event whose payload holds an `entries[]` array wholesale-replacing prior state - is **not** current ZMeta vocabulary. It is a future-extension concept in the contract 3.3 sense: non-claimable until an approved version branch defines its semantics, schema, policy, adapter behavior, and conformance tests. Snapshot-replacement delivery (for example, MQTT retained messages) remains available as deployment transport behavior for the per-entity events without any new vocabulary. |

## Reserved but Invalid: Future Modalities

`RADAR`, `LIDAR`, `MAGNETIC`, `SEISMIC`, `CYBER`, and `SIGINT` are reserved
future observation-modality candidates (contract 20.2). The extension
registry (`spec/extension-registry.yaml`) additionally reserves
`ENVIRONMENTAL` and `MARITIME`. Reserved means the name is protected so
nobody claims it informally - it is **not** emittable vocabulary in v1.0 or
v1.1.0, and events using these modalities fail validation.

Two traps to avoid while these remain reserved:

- Do not launder a radar contact through `OBSERVATION_EVENT` / `RF`. The RF
  feature contract describes a measured RF signal (`center_freq_hz`,
  `bandwidth_hz`, `power_dbm`); a radar-derived contact with range and
  bearing is not that. If the radar track arrives from an external system,
  it is external-track ingress (Section 4.5.1 promotion). If you own the
  sensor and need the modality, propose it - see below.
- Do not smuggle a reserved modality in as a free-form subtype or a hidden
  payload discriminator. Reserved names are exactly the names the registry
  exists to protect (contract 20.1).

## When the Alphabet Genuinely Cannot Spell It

Occasionally a concept truly has no spelling - a new sensing modality, a new
status family. The path is governed, and it is never "just use a new subtype
string":

1. **Extension-registry proposal.** Propose the concept in
   `spec/extension-registry.yaml` with semantic definition, rationale, scope,
   and collision analysis (contract 20.4).
2. **Versioned branch adoption.** The concept becomes valid vocabulary only
   when a version branch defines its semantic text, schema shape, policy
   behavior, adapter/gateway guidance, encoding projection, and conformance
   tests. This is the D-003 roadmap discipline
   (`docs/s1_11_future_versioned_semantic_branch_roadmap_plan.md`).

Until then, the pressure valve for deployment-local detail is **namespaced
payload extensions**: collision-resistant, safe-to-ignore payload objects
such as `vendor.<name>` namespaces or the schema-permitted `extensions`
blocks (contract 4.11, 20.3). Extensions may carry local labels, native IDs,
rendering hints, and vendor detail. They may not redefine core fields,
collapse semantic layers, change units, alter lineage meaning, or create
hidden required semantics. Your local name for a concept (`ais_track`,
`geofence_alert`) is welcome as payload-scoped provenance inside the
canonical event - it just cannot be the `event_subtype`.

## Guardrails That Will Catch You

The mappings above are not stylistic preferences; the reference stack
enforces them. A quick checklist of the enforcement surfaces this crosswalk
keeps you clear of:

- **Subtype vocabulary and discriminator match** are schema-enforced per
  version branch. Free-form subtypes fail dispatch (contract 7.3).
- **Payload denylists are recursive and key-normalized** (whitespace and
  case variations are caught): observation payloads ban `track_id`,
  `entity_class`, `classification`, `label`, `class_name`, and `confidence`;
  inference payloads ban `track_id`; state payloads ban the raw-artifact set;
  command payloads ban all altitude keys everywhere in the payload tree
  (`policy/semantics.yaml`, `gateway/src/validators.py`).
- **Confidence presence/prohibition** and **mandatory lineage** are
  schema-enforced by event type (contract 7.1, 4.8).
- **Producer authority** (who may emit state, who may create `track_id`,
  who may command) and **external-promotion evidence** are policy-enforced
  (contract 4.5, 4.5.1; `policy/producer-authority.yaml`).
- **Command safety** - deconfliction, `task_id` idempotency, TTL, no
  altitude - is enforced across schema and policy (contract 7.8, 15).

## References

- `spec/semantics-contract.md` - the normative contract (Sections cited
  throughout).
- `schema/zmeta-event.schema.json`, `schema/zmeta-event-1.0.schema.json`,
  `schema/zmeta-event-1.1.0.schema.json` - canonical schemas.
- `policy/semantics.yaml`, `policy/producer-authority.yaml` - denylists,
  promotion evidence, authority rules.
- `spec/extension-registry.md`, `spec/extension-registry.yaml` - reserved
  names and the extension adoption process.
- `docs/zmeta_correlation_pattern.md` - correlation/association pattern for
  fusion-to-sensor identity propagation.
- `docs/s1_11_future_versioned_semantic_branch_roadmap_plan.md` - D-003
  versioned-branch roadmap.
- `docs/s1_14_external_projection_promotion_contract.md` - external
  promotion design record.
- `adapters/ingress/klv/`, `adapters/ingress/mavlink/` - reference ingress
  patterns cited above.
- [PR #4](https://github.com/JTC-byte/zmeta-spec/pull/4) - source of the
  observed deployment concepts crosswalked here.
