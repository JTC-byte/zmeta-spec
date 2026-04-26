# ZMeta Semantic Contract

**Status:** Working Draft (v0.x)

**Purpose:** This document captures the *agreed semantic foundations* that govern ZMeta. It is intended to precede and constrain the formal ZMeta v1.0 schema. As additional sections are finalized (Units & Geodesy, Schema, Profiles), they will be appended to this document.

## 0. Operating Model (Non-Normative)

ZMeta is a translation- and transport-agnostic metadata layer that decouples sensors, gateways, and visualization systems.

- Sensors and vendors can emit any native format; mapping packs normalize to ZMeta OBSERVATION events.
- The semantic pipeline is Observation -> Inference -> Fusion -> State. STATE_EVENT is a snapshot summary of best available belief.
- Profiles (L/M/H) thin what is exported to match bandwidth without changing meaning.
- STATE_EVENT is the projection point for visualization/interop formats (e.g., CoT for TAK, JREAP/Link 16 gateways).
- COMMAND_EVENT carries low-rate cueing/retasking when links are constrained and must route through a Comms/Deconfliction Node.
- Raw data used to generate a snapshot SHOULD be retained locally for AAR and deeper analysis; snapshots may reference local stores or external IDs when available.
- Optional data references may be attached as lightweight pointers; these references never replace or reinterpret the event payload.

These constraints let you plug systems together while preserving near-real-time fidelity under bandwidth constraints.

## 1. Core Semantic Contract (Pre-Schema)

The following semantics are **locked** and non-negotiable for the MVP. All schema design, partner integrations, and demos must conform to these rules.

### 1.1 Event-Based Worldview

- ZMeta represents **events**, not objects or sensor state.
- Each message describes *something that happened* at a specific time.
- There is no concept of a mutable or authoritative object record in ZMeta.

### 1.2 Append-Only Immutability

- ZMeta events are **append-only**.
- Once emitted, an event is never modified or deleted.
- Corrections, reinterpretations, or refinements must be represented as **new events** with lineage references.

### 1.3 Event Identity (UUIDv7 Requirement)

- All ZMeta `event_id` values **MUST** be UUIDv7 (RFC 9562).
- UUIDv7 provides sortable, timestamp-grounded identity required for:
  - Lineage reconstruction and auditing
  - Deduplication under high-rate emission
  - Track persistence across profiles
  - Ordering under constrained timing
- Adapters translating legacy systems with UUIDv4 or other identifier formats
  **MUST** regenerate `event_id` to UUIDv7 at the adapter boundary.
- Legacy event identifiers MAY be preserved in `payload.source_event_id` or an
  equivalent payload-scoped provenance field for traceability.
- Profile, transport, producer, and event type MUST NOT be encoded into `event_id`.

### 1.4 Layer Separation (Fact -> Opinion -> Belief -> State)

ZMeta enforces strict separation between semantic layers:

- **Observation**: What a sensor measured (facts)
- **Inference / Detection**: What an algorithm believes (opinions)
- **Fusion / Track**: What appears continuous across time or sensors (provisional identity)
- **State**: What the system believes *right now* for operator consumption

No layer may collapse into another. Violations are considered contract breaches.

### 1.5 Authority Boundaries

- Sensors may emit **Observation** events only.
- AI/analytics modules may emit **Inference** events only.
- Fusion nodes are the only components permitted to create **Track identity**.
- Operator interfaces (e.g., TAK) **do not author or modify ZMeta events**.

Note: `node_role` expresses deployment tier, not physical location. If analytics or fusion runs on-device,
use a non-EDGE role (e.g., GATEWAY) for those producers to preserve authority boundaries.
If a single software stack performs multiple roles (e.g., analytics + fusion), it MUST respect
the event-type boundaries above and MAY emit separate producer identities for each role.

### 1.6 Transport Is Non-Semantic

- Transport choice (LTE, IP radio, LoRa) carries **no semantic meaning**.
- Transport may affect payload density, rate, or precision, but **never interpretation**.
- Identical events flowing over different transports must remain semantically identical.

### 1.7 Profiles Thin Data, Never Reinterpret It

- Thin / Medium / Fat profiles may:
  - Remove optional fields
  - Reduce precision
  - Reduce update rate
- Profiles may **not**:
  - Rename fields
  - Change units
  - Change meanings
  - Introduce implicit defaults

### 1.8 Mandatory Lineage

- Lineage is required for:
  - Inference
  - Fusion
  - State
- COMMAND_EVENT and SYSTEM_EVENT lineage is optional unless a specific subtype
  or deployment policy requires it.
- Lineage enables auditability, AARs, debugging, and trust assessment.

Lineage scope:
- Lineage SHOULD reference immediate parent events only (not full ancestry) to keep payloads bounded.
- Full ancestry MAY be reconstructed from local storage or AAR data stores when needed.
- Under constrained profiles (especially Profile L), lineage MAY reference non-exported events; consumers must tolerate unresolved references.

### 1.9 Explicit Uncertainty

- ZMeta never implies certainty by omission.
- Confidence and uncertainty must be explicit.
- Degraded or low-quality data is still valid, but must be marked as such.

### 1.10 Telemetry-First; Limited Mission Tasking Under Constraint

- ZMeta is telemetry-first and is not intended for continuous control.
- Out-of-band control remains the default under unrestricted bandwidth (e.g., MAVLink, Swarm API).
- A narrow, explicitly-scoped mission tasking capability is permitted via ZMeta only for degraded profiles (e.g., Profile M/L), to preserve tipping/cueing and waypoint-level autonomy when other links are constrained.

**The Comms/Deconfliction Node is responsible for:**
- Converting permitted mission tasks into MAVLink/Swarm API tasking for execution
- Deconflicting airspace and mission intent
- Validating and deduplicating task messages

AI/analytics producers (e.g., Torch) SHALL NOT directly command platforms.

All mission tasking carried in ZMeta SHALL be routed through a designated Comms/Deconfliction Node (e.g., SensorOps).

### 1.11 Tasking Governance and Deconfliction

Permitted via ZMeta (strict):

- Low-rate cueing / retask messages
- Discrete waypoint / GPS mission updates (e.g., GOTO, ORBIT, HOLD, SEARCH_BOX)

Not permitted via ZMeta:

- Safety-critical actuator commands without deconfliction
- High-rate flight control
- Continuous control loops

### 1.12 Vendor Extensibility Rules

- Vendors may extend payloads **within their domain**.
- Vendors may not:
  - Alter the ZMeta envelope
  - Redefine core fields
  - Collapse semantic layers
- Extensions must remain ignorable by other consumers.

## 2. Time Synchronization Contract (MVP)

Time semantics are critical for RF correlation, fusion, and track continuity. The following rules define how time is represented and interpreted in ZMeta.

### 2.1 Definition of ts

- event.ts represents **time-of-observation (capture time)**.
- It does **not** represent publish time, transmit time, or receive time.

Interpretation by event type:

- **Observation**: When the sensor measurement was taken (or midpoint of a window)

- **Inference**: The observation time of the primary input(s)

- **Fusion / State**: The time the fused estimate is valid for, grounded in input observation times via lineage

### 2.2 Capture vs Publish vs Receive Time

- event.ts (required): capture/observation time
- t_publish (optional): when the node emitted the event
- t_receive (optional, gateway-level): when the event was ingested

Only event.ts is universally required. Others are for debugging and AARs.

Gateway behavior:
- Gateways SHOULD stamp `t_receive` on forwarded events when it is missing.
- If `t_publish` is missing, gateways MAY set it to the same value as `t_receive`
  and SHOULD document that it was gateway-supplied.
- For bandwidth-constrained profiles, implementations MAY disable timing stamps;
  the reference gateway defaults to stamping for profiles H/M and can be turned off.

### 2.3 Timing Quality Metadata (Mandatory)

Timing quality metadata is **mandatory for all profiles** (L, M, H). Each node
MUST expose timing quality either per-event or periodically via `SYSTEM_EVENT` /
`TIME_STATUS`. A consumer that receives multiple events from a node MAY apply the
latest `TIME_STATUS` from that node until a newer status supersedes it.

Minimum required fields for `TIME_STATUS`:

- `time_source`: GPS_PPS | GPS_NMEA | NTP | PTP | MANUAL | UNKNOWN
- `sync_state`: LOCKED | HOLDOVER | UNSYNCED
- `est_error_ms`: **worst-case absolute timestamp error (upper bound)** - REQUIRED
- `last_sync_ts`: last known sync time (UTC)

If bandwidth or implementation maturity forces a minimal timing report,
`est_error_ms` remains mandatory for RF and time-correlated fusion use cases.
Best practice is to emit all four fields whenever possible.

### 2.4 Worst-Case Error Semantics

- est_error_ms represents a **conservative upper bound**, not a statistical measure.
- It is **not** 1-sigma or RMS.
- Internal implementations may use statistical models, but ZMeta exposes worst-case bounds.

### 2.5 Minimum Acceptable Sync Approaches (MVP)

- **Preferred (Gold):** GPS PPS disciplined clock per node
  - Expected error: <= 1 ms
- **Acceptable (Silver):** NTP-disciplined clock on stable network
  - Expected error: ~10-50 ms
- **Degraded (Bronze):** Unsynced clocks
  - Must be flagged as UNSYNCED with realistic error bounds

### 2.6 Windowed Observations (RF-Specific)

- If observations are computed over a time window, include:
  - t_start
  - t_end
- event.ts must equal the midpoint of the window.

This is critical for synthetic aperture DF and multi-sensor RF correlation.

### 2.7 Holdover and Drift Behavior

- Loss of sync transitions node to HOLDOVER state.
- est_error_ms must monotonically increase during holdover.
- Upon re-lock, sync_state returns to LOCKED and error bound resets.

### 2.8 Behavior Under Degraded Timing

- Events may still be emitted under degraded timing.
- High-confidence time-correlated fusion must be gated or down-weighted.
- Fusion outputs must reflect degraded timing via reduced confidence.

### 2.9 Profile Considerations

- **Profile L (LoRa Thin):**
  - event.ts required
  - Timing quality metadata required
  - `est_error_ms` MUST NOT be omitted
  - Timing quality may be sent periodically via `TIME_STATUS` SystemEvents when bandwidth is critical
- **Profiles M/H (IP Radio / LTE):**
  - Timing quality metadata required
  - Full timing quality SHOULD be emitted per-event when practical, or via periodic SystemEvents otherwise

## 3. Units & Geodesy Standard (MVP)

This section defines the **mandatory geospatial and unit conventions** used by ZMeta. These conventions are fixed for the MVP and must be applied consistently across all partners, sensors, transports, and processing layers.

### 3.1 Coordinate Reference System

- All geospatial coordinates shall use **WGS-84**.
- Latitude and longitude shall be expressed in **decimal degrees**.
- Latitude range: -90.0 to +90.0
- Longitude range: -180.0 to +180.0

No alternative datums or coordinate systems are permitted in ZMeta v1.0.

### 3.2 Altitude Reference

- All altitude values shall be expressed as **Height Above Ellipsoid (HAE)**.
- Units: **meters**
- Altitude field names shall explicitly imply HAE (e.g., alt_m).

Mean Sea Level (MSL), Above Ground Level (AGL), or terrain-relative heights are **not permitted** in ZMeta v1.0.

### 3.3 Velocity and Motion

- Linear speed: **meters per second (m/s)**
- Velocity vectors, when present, shall be earth-referenced unless explicitly stated otherwise.
- Acceleration (if present): **meters per second squared (m/s^2)**

### 3.4 Bearings, Angles, and Orientation

- Bearings and headings shall be expressed in **degrees**.
- Reference: **true north** (not magnetic).
- Range: 0-360 degrees, increasing clockwise.

Pitch, roll, and yaw (if present) shall also be expressed in degrees.

### 3.5 Distance and Range

- All distances and ranges shall be expressed in **meters**.
- No mixed-unit or implicit unit representations are allowed.

### 3.6 RF-Specific Units

- Frequency: **Hertz (Hz)**
- Bandwidth: **Hertz (Hz)**
- Power: **decibels referenced to one milliwatt (dBm)** unless explicitly stated otherwise

If alternate RF units are used internally (e.g., dBFS), they must be converted before emission into ZMeta or clearly labeled with unit-specific field names.

### 3.7 Time Units (Cross-Reference)

- All timestamps are expressed in **UTC**.
- Durations and time deltas are expressed in **milliseconds (ms)** unless otherwise specified.

(See Section 2: Time Synchronization Contract.)

### 3.8 Unit Inference Is Forbidden

- Units shall never be inferred by consumers.
- Absence of units does **not** imply default units.
- Fields without defined units are considered invalid for fusion and correlation.

### 3.9 Degraded or Partial Geospatial Data

- Events with incomplete geospatial information may still be emitted.
- `geo` is all-or-nothing: if any of lat/lon/alt_m is missing, omit `geo` entirely.
- Missing fields must be omitted (not zero-filled).
- Confidence and quality metadata must reflect reduced spatial certainty.

## 4. ZMeta v1.0 Schema (Normative)

This section defines the **normative ZMeta v1.0 schema**, including the canonical envelope and the required payload types. All implementations must conform to this structure. Deviations are considered non-compliant.

### 4.1 Canonical ZMeta Envelope

Every ZMeta message **must** conform to the following top-level structure.

```
ZMetaEvent {
  zmeta_version: "1.0"
  event: {
    event_id: UUIDv7
    event_type: EVENT_TYPE
    event_subtype: EVENT_SUBTYPE
    ts: UTC_TIMESTAMP
    t_publish?: UTC_TIMESTAMP
    t_receive?: UTC_TIMESTAMP
  }
  source: {
    platform_id: string
    node_role: EDGE | GATEWAY | APEX | DMZ | CLOUD
    producer: string
    sensor_id?: string
    sw_version?: string
  }
  profile?: L | M | H
  payload: OBJECT   // Defined by event_type
  confidence: float // 0.0 - 1.0 (worst-case interpretation, REQUIRED for INFERENCE/FUSION/STATE)
  lineage?: {
    based_on: UUIDv7[]
    transform?: string
  }
}
```

**Envelope Rules:**
- Envelope fields are **immutable and globally consistent**.
- Payload semantics are determined exclusively by event_type and event_subtype.
- `confidence` is mandatory for INFERENCE/FUSION/STATE events and prohibited for
  OBSERVATION/COMMAND/SYSTEM events.
  - It reflects worst-case consumption confidence: how safe the event is for
    downstream fusion or state projection.
  - It MUST account for input data quality, timing uncertainty, model confidence,
    and any active profile or failure-mode degradation.
  - Under degraded timing (HOLDOVER/UNSYNCED), confidence MUST be reduced
    proportionally to `est_error_ms` according to the producer's documented policy.
- `profile` is optional and reflects the **export profile** applied at emission time; do not encode profile into event_id.

### 4.2 Event Types (Authoritative)

```
EVENT_TYPE :=
  OBSERVATION_EVENT 
  INFERENCE_EVENT   
  FUSION_EVENT      
  STATE_EVENT       
  COMMAND_EVENT     
  SYSTEM_EVENT
```

No additional top-level event types are permitted in v1.0.

### 4.3 OBSERVATION_EVENT

Represents **raw sensor-derived facts**. No interpretation, classification, or persistence is allowed.

#### 4.3.1 Observation Payload (Generic)

```
ObservationPayload {
  modality: RF | EO | IR | ACOUSTIC | NETWORK
  geo?: { lat, lon, alt_m }
  bearing?: { az_deg, el_deg? }
  features: OBJECT
  quality?: OBJECT
  t_start?: UTC_TIMESTAMP
  t_end?: UTC_TIMESTAMP
}
```

**Rules:**
- No track_id permitted
- No entity_class permitted
- No classification/label permitted
- ts represents capture time or midpoint of window

**Quality guidance:** `payload.quality` is the place for observation measurement quality and uncertainty
(e.g., SNR, error bounds, timing quality, calibration state). Do not use envelope
`confidence` for observations; confidence is reserved for non-observation events.

#### 4.3.2 RF Observation Features (Minimum)

```
features {
  center_freq_hz: number
  bandwidth_hz: number
  power_dbm: number
  signature_hash?: string
}
```

Additional RF features may be appended but may not change semantics.

### 4.4 INFERENCE_EVENT

Represents **algorithmic claims** derived from one or more observations.

#### 4.4.1 Inference Payload

```
InferencePayload {
  inference_type: CLASSIFICATION | ASSOCIATION | ANOMALY | BEHAVIOR
  claim: OBJECT
  model: { name, version }
  based_on: UUIDv7[]
}
```

**Rules:**
- Must reference upstream observations
- Must not emit track_id
- Confidence reflects model belief, not truth

### 4.5 FUSION_EVENT

Represents **cross-sensor or temporal association** resulting in provisional continuity.

#### 4.5.1 Track Fusion Payload

```
FusionPayload {
  track_id: string
  members: UUIDv7[]
  estimated_state: {
    geo?: { lat, lon, alt_m }
    heading_deg?: number
    speed_mps?: number
  }
  stability: float
  last_seen_ts: UTC_TIMESTAMP
}
```

**Rules:**
- Only fusion nodes may create track_id
- Track identity is provisional and revisable
- Once assigned, a `track_id` MUST persist unchanged for subsequent events that
  reference the same track
- `track_id` values MUST be globally unique and MUST NOT be reused after track loss

### 4.6 STATE_EVENT

Represents **current system belief** intended for operator-facing systems (e.g., TAK).

#### 4.6.1 Track State Payload

```
TrackStatePayload {
  track_id: string
  geo: { lat, lon, alt_m }
  heading_deg?: number
  speed_mps?: number
  class?: string
  source_summary?: string[]
  valid_for_ms: number
}
```

**Rules:**
- This is the **only** payload translated to operator-facing track projections (e.g., CoT/TAK, JREAP/Link 16 gateways).
- Sensor-metadata projections (e.g., KLV-style observation exports) remain OBSERVATION-based and are not operator track state.
- Derived from FusionEvents
- No raw sensor features allowed

### 4.7 COMMAND_EVENT

Represents discrete mission directives used only for tipping/cueing and waypoint-level autonomy under degraded conditions.

#### 4.7.1 Mission Task Payload (Normative)

```
CommandPayload {
  task_id: string            // idempotent, globally unique
  task_type: GOTO | ORBIT | HOLD | SEARCH_BOX
  target_geo?: { lat, lon }
  geometry?: OBJECT          // e.g., box or orbit parameters
  valid_from_ts?: UTC_TIMESTAMP
  valid_for_ms: number       // TTL
  priority?: LOW | MED | HIGH
  requires_deconfliction: true
}
```

**Rules:**
- Not continuous control
- Must be idempotent (dedupe by task_id)
- Must route through Comms/Deconfliction Node
- Executed out-of-band via MAVLink/Swarm API
- `task_id` MUST be treated as an idempotent key across retransmissions.
- COMMAND_EVENT SHALL NOT specify altitude. Vertical deconfliction and altitude selection are the responsibility of the autonomy layer.

### 4.8 SYSTEM_EVENT

Represents platform, transport, or schema health.

#### 4.8.1 Time / Link Status Payload

```
SystemPayload {
  system_type: LINK_STATUS | TIME_STATUS | SCHEMA_VIOLATION | TASK_ACK
  state: string
  metrics?: OBJECT
}
```

Used for diagnostics, AARs, and gating fusion logic.

#### 4.8.2 TASK_ACK (Command Acknowledgement)

TASK_ACK provides an auditable lifecycle for COMMAND_EVENTs.

Required `metrics` fields:
- `task_id`
- `original_event_id`

Allowed `state` values:
- `RECEIVED` received by the comms/edge node.
- `ACCEPTED` validated and queued for execution.
- `REJECTED` rejected by policy or validation.
- `EXECUTING` accepted and currently executing.
- `COMPLETED` executed successfully.
- `FAILED` execution attempted but failed.
- `CANCELLED` cancelled by operator/system before completion.
- `EXPIRED` TTL expired before execution.
- `DUPLICATE_IGNORED` duplicate command ignored.

Reason code rules:
- `metrics.reason_code` is required for `REJECTED`, `FAILED`, `CANCELLED`, `EXPIRED`, and `DUPLICATE_IGNORED`.
- `metrics.reason_code` must be one of:
  `SCHEMA_INVALID`,
  `EVENT_TYPE_NOT_ALLOWED_FOR_ROLE`,
  `EVENT_TYPE_NOT_ALLOWED_FOR_PROFILE`,
  `PRODUCER_NOT_ALLOWED`,
  `COMMAND_NOT_DECONFLICTED`,
  `COMMAND_HAS_ALTITUDE`,
  `TASK_DUPLICATE`,
  `TASK_EXPIRED`,
  `TASK_CANCELLED`,
  `TASK_FAILED`,
  `TASK_ABORTED`,
  `TASK_REJECTED`.

#### 4.8.3 LINK_STATUS (Transport Health)

LINK_STATUS provides standardized transport health for AAR/debug and UI overlays.

Required `metrics` fields:
- `link_id` (string)
- `latency_ms`
- `packet_loss_pct`
- `throughput_bps`

Allowed `state` values:
- `UP`
- `DEGRADED`
- `DOWN`
- `UNKNOWN`

Reason code rules:
- `metrics.reason_code` is required for `DEGRADED` and `DOWN`.
- `metrics.reason_code` must be one of:
  `LINK_LOSS`,
  `LOW_RSSI`,
  `HIGH_LATENCY`,
  `HIGH_PACKET_LOSS`,
  `LOW_THROUGHPUT`,
  `INTERFERENCE`,
  `JAMMED`,
  `BACKHAUL_DOWN`,
  `NO_ROUTE`,
  `CONFIG_ERROR`,
  `POWER_SAVE`,
  `UNKNOWN_CAUSE`.

#### 4.8.4 SCHEMA_VIOLATION (Validation Failure)

SCHEMA_VIOLATION represents a rejected or malformed event and provides auditability
for AAR/debug.

Required `metrics` fields:
- `reason_code`
- `original_event_id`

Allowed `reason_code` values:
- All codes defined in `policy/violation-codes.yaml`.

Recommended optional fields:
- `metrics.path` (schema pointer)
- `metrics.error` (short error message)

### 4.9 Profile Compliance

Profiles define **transport-driven transmission constraints**, not semantic shortcuts. The internal semantic pipeline (Observation -> Inference -> Fusion -> State) remains valid in all profiles; profiles constrain **what is exported** and **at what fidelity**.

#### Profile L (LoRa Thin) - Severe Constraint / Denied Environment

**Purpose:** Preserve operator-relevant awareness under extreme bandwidth constraint.

**Compliance (Essential):**

- Transmit: STATE_EVENT, SYSTEM_EVENT, and COMMAND_EVENT (mission directives only).

- Behavior: Nodes SHALL perform whatever local processing is necessary to emit an honest, time-bounded STATE_EVENT reflecting the best available belief.
- Lineage MUST still be included even when upstream events are not transmitted; references may point to non-exported local events.
- COMMAND_EVENT is permitted only for discrete waypoint / GPS mission directives and must be TTL-bound, idempotent (task_id), and routed through the Comms/Deconfliction Node.

- **Uncertainty:** Confidence, timing quality, and short TTL **MUST** explicitly reflect degraded conditions.

- **Authority:** Identity is **provisional and revisable**; no authoritative claims.

- **Prohibitions:** No raw observations, no inference payloads, no semantic reinterpretation.

**Rationale:** The pipe can carry belief-state only; exporting belief-state preserves semantics while respecting the link.

#### Profile M (IP Radio) - Constrained IP / Intermittent Backhaul

**Purpose:** Balance fidelity and robustness on bandwidth-limited IP links.

**Compliance (Essential):**

- Transmit: STATE_EVENT, FUSION_EVENT, and selected SYSTEM_EVENTs; selective OBSERVATION_EVENTs may be transmitted when justified; COMMAND_EVENT is permitted for mission directives.

- Behavior: Semantic layers SHALL NOT be collapsed by default; fusion may occur upstream or downstream.
- COMMAND_EVENT may be used for cueing and waypoint-level tasking when out-of-band control is unavailable or impractical (still subject to deconfliction).

- **Uncertainty:** Maintain explicit confidence and timing quality.

- **Prohibitions:** Do not assume LTE-like capacity; do not fork semantics.

**Rationale:** Profile M enables selective richness without changing meaning.

#### Profile H (LTE Fat) - Full Fidelity / Preferred Operation

**Purpose:** Maximize observability and analytic potential when bandwidth permits.

**Compliance (Essential):**

- Transmit: All event types (OBSERVATION, INFERENCE, FUSION, STATE, COMMAND, SYSTEM).

- Behavior: Maintain full semantic separation; no justification for layer collapse.
- While COMMAND_EVENT is supported, out-of-band control (MAVLink / Swarm API) is the preferred mechanism under Profile H; ZMeta tasking should be used only for fallback, consistency, or testing.

- **Uncertainty:** Preserve explicit confidence and lineage.

- **Prohibitions:** No transport-driven shortcuts.

**Rationale:** Full fidelity enables best fusion, auditability, and downstream projection.

**Profile Rule (Global):** Profiles may remove fields or reduce rate/precision, but **never reinterpret meaning** or rename fields.

## 5. Track Persistence and Deduplication (Normative)

Track identity must persist across profile transitions, time gaps, and network
boundaries. Deduplication and continuity rely on immutable event identity,
idempotent task identity, and explicit lineage.

### 5.1 Primary Identification Method: Track ID

Track identity is anchored in `payload.track_id`, which is assigned only by a
fusion node (see Section 1.5 Authority Boundaries).

**Rules:**
- `track_id` is assigned by fusion nodes only.
- `track_id` MUST persist unchanged across all subsequent events referencing the same track.
- `track_id` is profile-agnostic and remains valid across Profile L, M, and H exports.
- `track_id` SHOULD be human-readable when practical (for example, `TRACK-20250117-001`) but MUST be globally unique.
- `track_id` MUST NOT be reused after a track is lost, merged, or retired.

### 5.2 Deduplication Rules

Event deduplication uses the immutable `event_id` unless the event type has an
explicit idempotency key.

**FUSION_EVENT / STATE_EVENT deduplication:**
- Use `event_id` as the primary deduplication key.
- If an identical event with the same `event_id` arrives more than once, consumers SHOULD drop subsequent copies without changing state.
- Consumers maintaining local state MUST record the `event_id` values already applied.

**COMMAND_EVENT deduplication:**
- Use `payload.task_id` as the idempotent key, not `event_id`.
- Retransmitted COMMAND_EVENTs with the same `task_id` MUST be treated as the same command.
- A duplicate command MUST NOT be forwarded for execution a second time.
- The node detecting the duplicate SHOULD emit a `SYSTEM_EVENT` / `TASK_ACK` with:
  - `payload.state: DUPLICATE_IGNORED`
  - `payload.metrics.task_id`
  - `payload.metrics.original_event_id`
  - `payload.metrics.reason_code: TASK_DUPLICATE`

**TASK_ACK deduplication:**
- Use `payload.metrics.task_id` + `payload.metrics.original_event_id` + `payload.state` as the composite key.
- A task may be acknowledged once per state transition.
- Multiple acknowledgements for different states of the same task are valid lifecycle updates.

### 5.3 Track Lifecycle and Revisability

Track identity is **provisional and revisable**, but revisability is represented
with new events and lineage, never by mutating old events or reusing IDs.

**Lifecycle states:**
- **NEW:** A fusion node emits an initial FUSION_EVENT with a new `track_id`.
- **ACTIVE:** The node continues emitting FUSION_EVENT and STATE_EVENT updates for the same `track_id`.
- **MERGED:** If two tracks are determined to be the same entity:
  - Emit a new FUSION_EVENT with the canonical `track_id`.
  - Include lineage references to the events that supported both prior tracks.
  - Retire the non-canonical `track_id`; do not reuse it.
  - Record the merge in local AAR/operator logs, or in an implementation-defined system event if supported by that schema version.
- **LOST:** If observations for a track exceed a configurable age threshold:
  - Stop emitting STATE_EVENTs for that `track_id`, or emit only low-confidence updates that truthfully represent stale state.
  - Allow existing `valid_for_ms` windows to expire.
  - Retire the `track_id`; do not reuse it after any quiet period.

### 5.4 Lineage-Based Continuity

Track continuity is validated via lineage:

- Every FUSION_EVENT and STATE_EVENT **MUST** include `lineage.based_on` referencing parent observations, inferences, or fusion events.
- Lineage establishes causality: this track update is derived from these prior events.
- Under Profile L, lineage MAY reference non-exported events; consumers must tolerate unresolved references.
- Full ancestry MAY be reconstructed from local AAR stores when needed.

Example:

```json
{
  "event_type": "STATE_EVENT",
  "payload": {
    "track_id": "TRACK-20250117-001",
    "geo": { "lat": 40.7128, "lon": -74.0060, "alt_m": 100 },
    "valid_for_ms": 1000
  },
  "lineage": {
    "based_on": [
      "019c2b5c-c046-70e1-b6aa-34bf14c8a247",
      "019c2b5c-c047-73ea-8f1a-3027c7ac09aa"
    ]
  }
}
```

### 5.5 Handling Track Persistence Across Profiles

Invariant: `track_id` is profile-agnostic. A track exported in Profile H remains
the same track when exported in Profile L, and vice versa.

**Profile L edge behavior:**
- An edge node that receives a FUSION_EVENT with `track_id: T123` MAY emit a Profile L STATE_EVENT with `track_id: T123`.
- The `track_id` is preserved; only optional fields may be dropped.
- Lineage may reference non-exported fusion events under bandwidth constraint.

**Profile M/H gateway behavior:**
- A gateway that receives a Profile L STATE_EVENT with `track_id: T123` preserves `track_id`.
- The gateway MAY enrich the event with fuller lineage or emit a FUSION_EVENT if it has access to upstream data.
- Enrichment must be transparent to downstream consumers and MUST NOT modify or replace the existing event.

## 6. Edge Operator Failure Mode Configuration (Normative)

Edge nodes in Profile L or M deployments must support user-configurable failure
mode handling while preserving semantic contract invariants. Configuration may
change rates, TTLs, confidence reductions, queueing, and local gating behavior;
it may not change event meaning.

### 6.1 Default Failure Mode Behavior

All edge nodes **MUST** implement defensible defaults for the following failure
modes. Operators MAY override the thresholds and factors in deployment config.

| Failure Mode | Default Behavior | User Configurable |
|---|---|---|
| **Timing Loss (UNSYNCED)** | Emit TIME_STATUS with `sync_state: UNSYNCED`; reduce STATE_EVENT confidence by factor of 2; gate high-precision fusion | Yes |
| **Observation Timeout** | Continue STATE_EVENT emission only while `valid_for_ms` truthfully represents stale data; reduce `valid_for_ms` by 50%; reduce confidence by 10% per update cycle | Yes |
| **Deconfliction Node Offline** | Queue COMMAND_EVENTs locally with TTL; do not execute undeconflicted commands; emit TASK_ACK failure/expiry when applicable | Yes |
| **Memory/Storage Exhausted** | Preserve required envelope, confidence, and lineage fields; drop optional references first; drop least-confident observations before stronger state | Yes |
| **Link Degradation** | Emit LINK_STATUS; thin optional payload fields per profile rules; may reduce STATE_EVENT emission rate | Yes |
| **Fusion Instability** | If `stability < 0.3`, hold STATE_EVENT emission until stability improves or TTL expires unless operator policy requires degraded-state emission | Yes |

`SCHEMA_VIOLATION` MUST be used only for rejected or malformed events. It MUST
NOT be used to report normal operational degradation such as memory pressure,
track merge, timing loss, or link degradation unless the degradation directly
caused schema validation failure.

### 6.2 User-Configurable Profile Example

Edge operators may override defaults via configuration:

```json
{
  "failure_modes": {
    "timing_loss": {
      "enabled": true,
      "confidence_reduction_factor": 2.0,
      "gate_fusion_threshold": 0.4
    },
    "observation_timeout": {
      "enabled": true,
      "valid_for_ms_reduction": 0.5,
      "confidence_reduction_per_cycle": 0.1,
      "max_age_ms": 300000
    },
    "deconfliction_offline": {
      "enabled": true,
      "queue_max_size": 100,
      "queue_ttl_ms": 600000,
      "emit_backpressure_event": true
    },
    "fusion_instability": {
      "enabled": true,
      "stability_threshold": 0.3,
      "hold_until_stable": true,
      "force_emit_after_ms": 5000
    }
  },
  "profile": "L",
  "time_source": "GPS_PPS",
  "max_lineage_depth": 3,
  "max_payload_bytes": 256
}
```

### 6.3 Semantic Invariants Under Degradation

Even when failure modes are active, the following invariants MUST be maintained:

- **No semantic reinterpretation:** Degraded STATE_EVENTs remain STATE_EVENTs.
- **Explicit uncertainty:** Confidence and timing metadata always reflect current conditions.
- **Auditability:** Significant degradation transitions are emitted as standardized SystemEvents when available and logged for AAR.
- **Immutability:** Once an event is emitted, it cannot be modified; corrections are new events.
- **Lineage preservation:** Required `lineage.based_on` references must be included, even if unresolved under Profile L.

### 6.4 Recommended Operational Practices

Monitoring:
- Track `est_error_ms` and `sync_state` to anticipate fusion reliability.
- Alert if confidence remains below an operator-defined threshold such as `0.3`.
- Log all failure mode activations for post-mission AAR.

Testing:
- Validate behavior under each failure mode before deployment.
- Test Profile L -> M -> H transitions to ensure track continuity.
- Verify deduplication under high-loss and retransmission conditions.

Escalation:
- Define recovery objectives for UNSYNCED operation.
- Define observation timeout recovery behavior.
- Document manual recovery procedures for persistent failure modes.

## Appendix A (Informative): Data Reference Convention (Optional)

Some deployments retain raw data locally or in upstream stores for AAR, reprocessing, or vectorization. To link
lightweight ZMeta events to those datasets without inflating payloads, use an optional reference pointer.

Guidance:
- Use `payload.data_ref` for a single pointer, or `payload.data_refs` for multiple pointers.
- References are metadata only; they must not contain raw data or override event semantics.
- References may point to local storage, gateway caches, or external data stores.

Recommended fields (all optional except `ref_id`):
- ref_id: string (unique within the referenced store)
- store: string (e.g., "local", "gateway-cache", "s3-bucket:region/path")
- kind: RAW | VECTOR | FILE
- format: string (e.g., "iq", "wav", "mp4", "pcap", "npy")
- hash: string (e.g., "sha256:...") 
- size_bytes: integer
- t_start: UTC_TIMESTAMP
- t_end: UTC_TIMESTAMP

Example:
```
payload: {
  ...,
  data_ref: {
    ref_id: "rf-capture-20250117-143000Z-0001",
    store: "local",
    kind: "RAW",
    format: "iq",
    hash: "sha256:abc123...",
    size_bytes: 10485760,
    t_start: "2025-01-17T14:29:58Z",
    t_end: "2025-01-17T14:30:02Z"
  }
}
```

## Appendix B (Informative): Confidence Computation Guidelines

This appendix provides non-normative guidance for computing `confidence` values
for FUSION and STATE events. Operators and producers SHOULD document their chosen
formula in operational runbooks.

### B.1 Input Confidence Aggregation

When fusing multiple observations or inferences:

```text
confidence = min(input_confidences) * aggregation_factor
```

Where:
- `min(input_confidences)` is the lowest confidence among all inputs.
- `aggregation_factor` is a domain-specific multiplier, such as `0.8` for a
  conservative two-sensor fusion model or `0.9` for high-quality inputs.

Rationale: a fused track should not appear more reliable than its weakest
material input unless the producer's model explicitly justifies that increase.

### B.2 Timing Quality Degradation

If timing synchronization is degraded:

```text
timing_factor = max(0.0, 1.0 - (est_error_ms / sync_threshold_ms))
confidence_with_timing = base_confidence * timing_factor
```

Where:
- `est_error_ms` is the node's current timing error from `TIME_STATUS`.
- `sync_threshold_ms` is a configurable threshold, such as `100 ms` for RF fusion
  or `500 ms` for general tracking.

Example:
- Base confidence: `0.8`
- Timing error: `50 ms`
- Threshold: `100 ms`
- Timing factor: `1.0 - (50 / 100) = 0.5`
- Final confidence: `0.8 * 0.5 = 0.4`

### B.3 Profile and Precision Effects

Profile L events MUST NOT reduce confidence merely because they are Profile L.
However, confidence SHOULD reflect any real loss of precision, missing optional
context, unresolved lineage, or active degradation introduced by profile
constraint.

Example:

```text
profile_precision_factor = 0.8  # only when quantization or omitted context materially reduces use safety
confidence_with_profile = base_confidence * profile_precision_factor
```

### B.4 Observation Freshness

If a STATE_EVENT is based on observations older than a configured threshold:

```text
age_ms = now_ts - oldest_input_ts
freshness_factor = max(0.0, 1.0 - (age_ms / max_age_ms))
confidence_with_freshness = base_confidence * freshness_factor
```

Where `max_age_ms` is typically 30-60 seconds for real-time tracking, but should
be tuned by mission and sensor modality.

### B.5 Recommended Formula

For a complete confidence computation in a fusion node:

```text
confidence =
  min(input_confidences)
  * aggregation_factor
  * timing_factor
  * profile_precision_factor
  * freshness_factor

confidence = clip(confidence, 0.0, 1.0)
```

All factors are computed independently, then multiplied. Clamping ensures the
result remains in `[0, 1]`.
