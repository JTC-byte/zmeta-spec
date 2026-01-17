# ZMeta Semantic Contract

**Status:** Working Draft (v0.x)

**Purpose:** This document captures the *agreed semantic foundations* that govern ZMeta. It is intended to precede and constrain the formal ZMeta v1.0 schema. As additional sections are finalized (Units & Geodesy, Schema, Profiles), they will be appended to this document.

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

### 1.3 Layer Separation (Fact → Opinion → Belief → State)

ZMeta enforces strict separation between semantic layers:

- **Observation**: What a sensor measured (facts)
- **Inference / Detection**: What an algorithm believes (opinions)
- **Fusion / Track**: What appears continuous across time or sensors (provisional identity)
- **State**: What the system believes *right now* for operator consumption

No layer may collapse into another. Violations are considered contract breaches.

### 1.4 Authority Boundaries

- Sensors may emit **Observation** events only.
- AI/analytics modules may emit **Inference** events only.
- Fusion nodes are the only components permitted to create **Track identity**.
- Operator interfaces (e.g., TAK) **do not author or modify ZMeta events**.

### 1.5 Transport Is Non-Semantic

- Transport choice (LTE, IP radio, LoRa) carries **no semantic meaning**.
- Transport may affect payload density, rate, or precision, but **never interpretation**.
- Identical events flowing over different transports must remain semantically identical.

### 1.6 Profiles Thin Data, Never Reinterpret It

- Thin / Medium / Fat profiles may:
  - Remove optional fields
  - Reduce precision
  - Reduce update rate
- Profiles may **not**:
  - Rename fields
  - Change units
  - Change meanings
  - Introduce implicit defaults

### 1.7 Mandatory Lineage

- All non-observation events must reference upstream events via lineage.
- Lineage is required for:
  - Inference
  - Fusion
  - State
- Lineage enables auditability, AARs, debugging, and trust assessment.

### 1.8 Explicit Uncertainty

- ZMeta never implies certainty by omission.
- Confidence and uncertainty must be explicit.
- Degraded or low-quality data is still valid, but must be marked as such.

### 1.9 Telemetry-First; Limited Mission Tasking Under Constraint

- ZMeta is telemetry-first and is not intended for continuous control.
- Out-of-band control remains the default under unrestricted bandwidth (e.g., MAVLink, Swarm API).
- A narrow, explicitly-scoped mission tasking capability is permitted via ZMeta only for degraded profiles (e.g., Profile M/L), to preserve tipping/cueing and waypoint-level autonomy when other links are constrained.

**The Comms/Deconfliction Node is responsible for:**

- Converting permitted mission tasks into      MAVLink/Swarm API tasking for execution

- Deconflicting airspace and mission intent

- Validating and deduplicating task messages

AI/analytics producers (e.g., Torch) SHALL NOT directly command platforms.

All mission tasking carried in ZMeta SHALL be routed through a designated Comms/Deconfliction Node (e.g., SensorOps).

### 1.10 Tasking Governance and Deconfliction

Permitted via ZMeta (strict):

• Low-rate cueing / retask messages

• Discrete waypoint / GPS mission updates (e.g.,   GOTO, ORBIT, HOLD, SEARCH_BOX)

Not permitted via ZMeta:

• Safety-critical actuator commands without deconfliction

• High-rate flight control

• Continuous control loops

### 1.11 Vendor Extensibility Rules

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

### 2.3 Timing Quality Metadata

Each node must expose timing quality, either per-event or periodically via SystemEvents.

Minimum required fields:

- time_source: GPS_PPS | GPS_NMEA | NTP | PTP | MANUAL | UNKNOWN

- sync_state: LOCKED | HOLDOVER | UNSYNCED

- est_error_ms: **worst-case absolute timestamp error (upper bound)**

- last_sync_ts: last known sync time (UTC)

If only one field can be supported, est_error_ms is **mandatory** for RF use cases.

### 2.4 Worst-Case Error Semantics

- est_error_ms represents a **conservative upper bound**, not a statistical measure.
- It is **not** 1-sigma or RMS.
- Internal implementations may use statistical models, but ZMeta exposes worst-case bounds.

### 2.5 Minimum Acceptable Sync Approaches (MVP)

- **Preferred (Gold):** GPS PPS disciplined clock per node
  - Expected error: ≤ 1 ms
- **Acceptable (Silver):** NTP-disciplined clock on stable network
  - Expected error: ~10–50 ms
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
  - Timing quality may be sent periodically via SystemEvents
- **Profiles M/H (IP Radio / LTE):**
  - Full timing quality metadata strongly recommended

## 3. Units & Geodesy Standard (MVP)

This section defines the **mandatory geospatial and unit conventions** used by ZMeta. These conventions are fixed for the MVP and must be applied consistently across all partners, sensors, transports, and processing layers.

### 3.1 Coordinate Reference System

- All geospatial coordinates shall use **WGS‑84**.
- Latitude and longitude shall be expressed in **decimal degrees**.
- Latitude range: −90.0 to +90.0
- Longitude range: −180.0 to +180.0

No alternative datums or coordinate systems are permitted in ZMeta v1.0.

### 3.2 Altitude Reference

- All altitude values shall be expressed as **Height Above Ellipsoid (HAE)**.
- Units: **meters**
- Altitude field names shall explicitly imply HAE (e.g., alt_m).

Mean Sea Level (MSL), Above Ground Level (AGL), or terrain‑relative heights are **not permitted** in ZMeta v1.0.

### 3.3 Velocity and Motion

- Linear speed: **meters per second (m/s)**
- Velocity vectors, when present, shall be earth‑referenced unless explicitly stated otherwise.
- Acceleration (if present): **meters per second squared (m/s²)**

### 3.4 Bearings, Angles, and Orientation

- Bearings and headings shall be expressed in **degrees**.
- Reference: **true north** (not magnetic).
- Range: 0–360 degrees, increasing clockwise.

Pitch, roll, and yaw (if present) shall also be expressed in degrees.

### 3.5 Distance and Range

- All distances and ranges shall be expressed in **meters**.
- No mixed‑unit or implicit unit representations are allowed.

### 3.6 RF‑Specific Units

- Frequency: **Hertz (Hz)**
- Bandwidth: **Hertz (Hz)**
- Power: **decibels referenced to one milliwatt (dBm)** unless explicitly stated otherwise

If alternate RF units are used internally (e.g., dBFS), they must be converted before emission into ZMeta or clearly labeled with unit‑specific field names.

### 3.7 Time Units (Cross‑Reference)

- All timestamps are expressed in **UTC**.
- Durations and time deltas are expressed in **milliseconds (ms)** unless otherwise specified.

(See Section 2: Time Synchronization Contract.)

### 3.8 Unit Inference Is Forbidden

- Units shall never be inferred by consumers.
- Absence of units does **not** imply default units.
- Fields without defined units are considered invalid for fusion and correlation.

### 3.9 Degraded or Partial Geospatial Data

- Events with incomplete geospatial information may still be emitted.
- Missing fields must be omitted (not zero‑filled).
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
  }
  source: {
    platform_id: string
    node_role: EDGE | GATEWAY | APEX | DMZ | CLOUD
    producer: string
    sensor_id?: string
    sw_version?: string
  }
  payload: OBJECT   // Defined by event_type
  confidence: float // 0.0 – 1.0 (worst-case interpretation)
  lineage?: {
    based_on: UUIDv7[]
    transform?: string
  }
}
```

**Envelope Rules:** - Envelope fields are **immutable and globally consistent**. - payload semantics are determined exclusively by event_type and event_subtype. - confidence is mandatory for all non-observation events.

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

**Rules:** - No track_id permitted - No entity_class permitted - ts represents capture time or midpoint of window

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

**Rules:** - Must reference upstream observations - Must not emit track_id - Confidence reflects model belief, not truth

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

**Rules:** - Only fusion nodes may create track_id - Track identity is provisional and revisable

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

**Rules:** - This is the **only** payload translated to CoT - Derived from FusionEvents - No raw sensor features allowed

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

Rules: - Not continuous control - Must be idempotent (dedupe by task_id) - Must route through Comms/Deconfliction Node - Executed out-of-band via MAVLink/Swarm API
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

### 4.9 Profile Compliance

Profiles define **transport-driven transmission constraints**, not semantic shortcuts. The internal semantic pipeline (Observation → Inference → Fusion → State) remains valid in all profiles; profiles constrain **what is exported** and **at what fidelity**.

#### Profile L (LoRa Thin) — Severe Constraint / Denied Environment

**Purpose:** Preserve operator-relevant awareness under extreme bandwidth constraint.

**Compliance (Essential):**

- Transmit: STATE_EVENT, SYSTEM_EVENT, and COMMAND_EVENT (mission directives only).

- Behavior: Nodes SHALL perform whatever local processing is necessary to emit an honest, time-bounded STATE_EVENT reflecting the best available belief.
- COMMAND_EVENT is permitted only for discrete waypoint / GPS mission directives and must be TTL-bound, idempotent (task_id), and routed through the Comms/Deconfliction Node.

- **Uncertainty:** Confidence, timing quality, and short TTL **MUST** explicitly reflect degraded conditions.

- **Authority:** Identity is **provisional and revisable**; no authoritative claims.

- **Prohibitions:** No raw observations, no inference payloads, no semantic reinterpretation.

**Rationale:** The pipe can carry belief-state only; exporting belief-state preserves semantics while respecting the link.

#### Profile M (IP Radio) — Constrained IP / Intermittent Backhaul

**Purpose:** Balance fidelity and robustness on bandwidth-limited IP links.

**Compliance (Essential):**

- Transmit: STATE_EVENT, FUSION_EVENT, and selected SYSTEM_EVENTs; selective OBSERVATION_EVENTs may be transmitted when justified; COMMAND_EVENT is permitted for mission directives.

- Behavior: Semantic layers SHALL NOT be collapsed by default; fusion may occur upstream or downstream.
- COMMAND_EVENT may be used for cueing and waypoint-level tasking when out-of-band control is unavailable or impractical (still subject to deconfliction).

- **Uncertainty:** Maintain explicit confidence and timing quality.

- **Prohibitions:** Do not assume LTE-like capacity; do not fork semantics.

**Rationale:** Profile M enables selective richness without changing meaning.

#### Profile H (LTE Fat) — Full Fidelity / Preferred Operation

**Purpose:** Maximize observability and analytic potential when bandwidth permits.

**Compliance (Essential):**

- Transmit: All event types (OBSERVATION, INFERENCE, FUSION, STATE, COMMAND, SYSTEM).

- Behavior: Maintain full semantic separation; no justification for layer collapse.
- While COMMAND_EVENT is supported, out-of-band control (MAVLink / Swarm API) is the preferred mechanism under Profile H; ZMeta tasking should be used only for fallback, consistency, or testing.

- **Uncertainty:** Preserve explicit confidence and lineage.

- **Prohibitions:** No transport-driven shortcuts.

**Rationale:** Full fidelity enables best fusion, auditability, and downstream projection.

**Profile Rule (Global):** Profiles may remove fields or reduce rate/precision, but **never reinterpret meaning** or rename fields.
