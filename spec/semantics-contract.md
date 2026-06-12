# ZMeta Semantic Contract

**Status:** v1.0 Locked (Normative)

**Purpose:** This document captures the agreed semantic foundations that govern
ZMeta v1.0. It constrains the formal schema, policy pack, reference gateway,
adapters, encodings, and conformance suite.

**Authority statement:** The semantic contract is authoritative. Schemas, policy
packs, encodings, adapters, gateways, examples, and conformance tests are
implementation surfaces that must preserve this contract.

## 0. Reading Model

Normative language:
- **MUST**, **SHALL**, and **REQUIRED** define mandatory behavior.
- **MUST NOT** and **SHALL NOT** define prohibited behavior.
- **SHOULD** defines recommended behavior that can be overridden only with a
  documented operational reason.
- **MAY** defines permitted behavior.

Version labels:
- **v1.0 normative**: locked ZMeta v1.0 semantics. These rules are not optional.
- **v1.0 schema-enforced**: rules implemented by JSON Schema.
- **v1.0 policy-enforced**: rules implemented by policy packs and runtime
  validators.
- **adapter/gateway guidance**: implementation requirements for preserving
  semantics at boundaries.
- **encoding projection**: binary or alternate wire representation that has no
  independent semantic meaning.
- **v1.1.0 extension**: experimental compatibility extension that applies only
  when `zmeta_version: "1.1.0"` selects that branch.
- **future candidate**: reserved concept that MUST NOT be treated as valid ZMeta
  vocabulary until a version branch, schema, policy, and conformance class are
  approved.
- **non-normative**: explanatory text, rationale, or examples.

## 1. Operating Model

ZMeta is a translation- and transport-agnostic metadata layer for resilient ISR
interoperability, edge AI provenance, bandwidth-aware dissemination, semantic
lineage, and operator-facing state projection.

ZMeta is:
- A semantic contract.
- A versioned event model.
- A JSON-schema-validated interchange format.
- A policy-driven enforcement model.
- A reference gateway and adapter pattern.
- A projection target for compact CBOR, protobuf, CoT/TAK, JREAP-style gateway
  inputs, and future transports.

ZMeta is not:
- A transport.
- A mutable object database.
- A video or raw data container.
- A replacement for MISB, MAVLink, CoT, TAK, Link 16, or native vendor formats.
- A continuous-control or safety-critical actuator command protocol.
- An IFF authority.
- A vendor COP data model.

The semantic pipeline is:

```text
OBSERVATION_EVENT -> INFERENCE_EVENT -> FUSION_EVENT -> STATE_EVENT
```

Where:
- Observations are measured facts.
- Inferences are algorithmic or analytic claims derived from observations.
- Fusion creates provisional track continuity and track identity.
- State is the current operator-facing belief projection.

Profiles L/M/H thin exported data for bandwidth, but they do not change meaning.
Encodings such as JSON, CBOR, compact CBOR, and protobuf are wire projections.
They MUST decode to the same canonical ZMeta event semantics.

Control planes are orthogonal. Bandwidth profile, coalition release profile,
compute tier, trust/quarantine state, replay mode, and operator view policy are
different concepts. Implementations MUST NOT overload `profile` to mean release
domain, trust state, emergency condition, or UI role.

### 1.1 Completeness Without Exhaustiveness

ZMeta defines the stable semantic primitives required to preserve operational
meaning across heterogeneous ISR systems. It does not attempt to define a
complete mission ontology for every sensor, platform, adapter, trust model,
operational role, doctrine, workflow, or edge case.

Implementations MAY build mission-specific workflows, policy packs, adapters,
profiles, extensions, operator views, and mission plugins on top of ZMeta. They
MUST NOT redefine the meaning of core event families, semantic layer
boundaries, confidence semantics, lineage semantics, profile behavior,
authority boundaries, command safety, or adapter/gateway obligations.

The purpose of the core contract is to prevent semantic corruption, not to
exhaustively model every possible mission. Mission-specific behavior belongs in
policy packs, deployment configuration, adapter mappings, profile projection
rules, extension branches, conformance-scoped branches, operator views, or
mission plugins.

## 2. Version Semantics

### 2.1 v1.0 Locked Semantics

ZMeta v1.0 is locked and normative. All v1.0 producers, schemas, validators,
policy packs, gateways, adapters, encodings, examples, and conformance tests
MUST preserve the invariants in this document.

Patch releases in the v1.0 line MAY clarify wording, fix contradictions, or
tighten conformance around already-defined semantics. Patch releases MUST NOT:
- Remove locked v1.0 invariants.
- Redefine existing v1.0 fields.
- Make previously invalid semantic layer collapses valid.
- Treat future extension candidates as valid v1.0 vocabulary.
- Make v1.1.0-only concepts valid when `zmeta_version` is `"1.0"`.

### 2.2 v1.1.0 Compatibility Extension

ZMeta v1.1.0 is an experimental compatibility extension branch. It preserves all
v1.0 invariants while adding version-selected vocabulary such as structured
quality metadata, error ellipse, formalized data references, additional
observation feature contracts, SENSOR_STATUS, PLATFORM_STATUS, and expanded
bounded tasking.

v1.1.0-only concepts:
- MUST declare `zmeta_version: "1.1.0"`.
- MUST NOT validate as `zmeta_version: "1.0"`.
- MUST NOT loosen layer separation, lineage, unit explicitness, command safety,
  profile behavior, authority boundaries, or append-only immutability.
- MUST remain optional or version-selected.
- MUST be ignorable by consumers that do not understand the extension unless a
  selected v1.1.0 subtype makes the extension part of that subtype contract.

`zmeta_version: "1.1"` is not a normative alias. Compatibility adapters MAY
normalize aliases before schema validation, but canonical schemas MUST require
exact version strings.

### 2.3 Future Version Rules

Future versions MUST preserve v1.0 invariants unless a breaking version branch
explicitly changes them. Future additions MUST define:
- Semantic meaning.
- Version branch.
- Schema enforcement, when structural validation is possible.
- Policy enforcement, when deployment context or runtime state is required.
- Adapter/gateway behavior.
- Encoding projection behavior, if wire mappings change.
- Conformance tests.

Future concepts in this document are not valid ZMeta event vocabulary until
adopted by a versioned branch.

### 2.4 Version Negotiation

Producers MUST emit an exact `zmeta_version`. Consumers MUST select the schema
and policy interpretation from that exact value.

Gateways MAY support multiple version branches, but they MUST NOT silently
reinterpret an event from one semantic version as another. Any compatibility
normalization happens before schema validation and SHOULD produce a sidecar
change report. Normalization MUST NOT rewrite source-authored event identity,
timestamps, event type/subtype, source identity, track identity, lineage, or
payload meaning.

### 2.5 Compatibility Expectations

Minor and patch releases in the 1.x family SHOULD preserve valid earlier 1.x
payloads unless those payloads violated locked invariants. A payload with a
non-UUIDv7 ZMeta `event_id`, collapsed semantic layers, implicit units,
missing required lineage, or invalid command safety is not compatible even if a
legacy implementation accepted it.

### 2.6 Core Semantic Change Threshold

Core semantic changes SHOULD NOT be accepted unless there is an observed
implementation failure, interoperability ambiguity, safety or audit risk, or
validated operational requirement that cannot be solved through policy,
profiles, adapters, governed extension branches, conformance classes, or
mission-specific logic.

A core clarification or change is appropriate when at least one of the following
is true:
- Two compliant implementations can interpret the same event differently.
- An adapter can silently upgrade or launder meaning across a semantic boundary.
- Bad, stale, degraded, unresolved, or externally promoted data can masquerade
  as clean authoritative state.
- Unsafe command generation can occur without an auditable basis.
- A profile projection can hide material degradation, confidence reduction,
  TTL reduction, or lineage uncertainty.

If an issue can be solved by deployment policy, profile selection, adapter
mapping, local operator view rules, mission plugin behavior, or a governed
extension branch, it SHOULD NOT change the core contract. Cleaner wording,
mission-specific preferences, and hypothetical future cases SHOULD be handled as
documentation, policy, or extension-registry work unless they expose a concrete
semantic ambiguity or safety/audit failure.

## 3. Enforcement Model

No single implementation surface enforces the whole semantic contract. The
surfaces are complementary.

### 3.1 JSON Schema Enforcement

JSON Schema SHOULD enforce:
- Required envelope structure.
- Exact version selection.
- UUIDv7 string shape.
- Required and prohibited fields.
- Event type and event subtype vocabulary.
- Event subtype and payload discriminator matching.
- Confidence presence/prohibition by event type.
- Lineage presence for INFERENCE_EVENT, FUSION_EVENT, and STATE_EVENT.
- Coordinate ranges and known scalar field ranges.
- Known payload shapes and task-specific command geometry.
- Profile/event-type compatibility when `profile` is present.
- v1.1.0 extension shapes when the v1.1.0 branch is selected.

JSON Schema cannot fully enforce:
- Historical immutability.
- Producer authority.
- Raw data retention truth.
- Actual time-source accuracy.
- Global track ID uniqueness.
- Trust, signing, or release policy.
- Semantic intent hidden in vendor extensions.

### 3.2 Policy Enforcement

Policy packs SHOULD enforce:
- Producer authority and role/event-type allowlists.
- Profile routing and export constraints.
- Command origin, deconfliction, and route constraints.
- Timing freshness thresholds and degrade/reject modes.
- Lineage parent availability and parent-type consistency when an event store is
  available.
- TASK_ACK, LINK_STATUS, and SCHEMA_VIOLATION reason-code behavior.
- Deployment-specific confidence caps.
- Future release labels, trust policies, quarantine modes, and signing
  allowlists.

Policy may tighten or loosen runtime behavior within the semantic contract. It
MUST NOT make invalid semantics valid.

### 3.3 Risk Adjudication and Operator-Tunable Policy

ZMeta separates semantic truth from operational risk acceptance.

The interoperability contract is locked. Deployment policy decides what to do
when valid data is stale, incomplete, degraded, externally promoted, unresolved,
or otherwise risky. Operators may choose what risk to accept, but ZMeta MUST make
that risk explicit and filterable.

ZMeta does not prescribe a single mission risk tolerance. It requires that any
accepted risk be explicitly labeled, policy-adjudicated, auditable, and
prevented from masquerading as clean authoritative state.

Contract and policy rules fall into four classes: `LOCKED`, `TUNABLE`,
`ADVISORY`, and `FUTURE_EXTENSION`.

- **Locked rules** protect interoperability and semantic truth. They MUST NOT be
  loosened by deployment policy. Examples include exact version selection,
  event type/subtype meaning, field units, layer separation, event identity,
  required lineage presence for derived events, command safety, and profile
  projection monotonicity.
- **Tunable rules** control operational response within the semantic contract.
  They MAY vary by deployment, profile, producer, route/link, event type,
  consumer, or temporary operator override. Examples include timing freshness
  thresholds, unresolved-lineage tolerance, external promotion response,
  confidence caps, TTL caps, profile thinning, producer allowlists, routing
  gates, and degraded-compute behavior.
- **Advisory rules** provide recommended quality targets, display hints, or
  operator guidance. They MUST NOT be interpreted as structural validity unless
  promoted to schema or policy enforcement by a versioned decision.
- **Future-extension rules** reserve, propose, or describe experimental concepts
  that are not valid current vocabulary. They MUST remain non-claimable until an
  approved version branch defines semantic text, schema or policy behavior,
  adapter/gateway guidance, encoding handling where applicable, and conformance
  tests.

Tunable policy responses SHOULD use a bounded action vocabulary:

- `reject`: do not forward the source event as accepted ZMeta data; emit a
  diagnostic event.
- `warn`: forward the event unchanged and emit a diagnostic event.
- `degrade`: forward the event with reduced/capped confidence, shortened/capped
  `payload.valid_for_ms`, route/display limits, or equivalent visible effects;
  emit a diagnostic event.
- `quarantine`: forward only into a restricted policy path, local display, AAR,
  or other bounded consumer set; emit a diagnostic event and make the restricted
  status filterable.
- `ignore`: permitted only for explicitly non-material checks where policy says
  no diagnostic is required. It MUST NOT hide material uncertainty, trust, timing,
  lineage, command, or safety impacts.

Soft acceptance MUST NOT make risky data look clean. Any `warn`, `degrade`, or
`quarantine` decision MUST be filterable by consumers through the accepted event,
a same-stream diagnostic event keyed by `original_event_id`, or both. If an
event may travel without its diagnostic context and the policy decision
materially affects trust, use, fusion, command basis, display, export,
confidence, TTL, or routing interpretation, the accepted event MUST carry
compact self-labels or policy references sufficient for downstream filtering in
a policy-scoped extension.

Degradation effects MUST respect event-type confidence rules. For event types
that prohibit top-level `confidence`, degradation MUST be expressed through
policy diagnostics, allowed/prohibited uses, TTL or routing limits, quality
metadata where valid, or future approved fields.

Risk adjudication diagnostics SHOULD include:

- `risk_dimension`, such as `timing`, `lineage`, `external_promotion`,
  `profile_projection`, `producer_authority`, `routing`, `compute`, `pnt`,
  `evidence`, or a future approved dimension.
- `reason_code` from the governed diagnostic vocabulary.
- `policy_mode` and `policy_decision`.
- the matched rule, policy ID, or rule path where practical.
- scope, such as profile, producer, route/link, event type/subtype, or consumer.
- effects such as confidence factor/cap, TTL factor/cap, route/display limits,
  or quarantine path.
- `allowed_uses` and `prohibited_uses` when a soft decision limits how an
  accepted event may be consumed.
- source identifiers and `original_event_id` for correlation.
- schema, policy, semantic-contract, or combined contract hash when hash stamping
  is enabled.

Risk dimensions, policy decisions, reason codes, and allowed/prohibited use
labels SHOULD come from governed vocabularies. Deployments MAY add local labels,
but they SHOULD namespace or document them so consumers do not mistake local
policy terms for portable ZMeta semantics.

Common use labels include:

- `DISPLAY`
- `LOCAL_AWARENESS`
- `ALERTING`
- `FUSION_INPUT`
- `STATE_UPDATE`
- `COALITION_EXPORT`
- `COMMAND_BASIS`
- `AUTONOMY_TASKING`
- `AAR_ONLY`
- `DEBUG_ONLY`

Policy MAY accept an event for one use while prohibiting another. For example,
a timing-degraded or externally promoted event may be valid for display and AAR
while prohibited from command generation, autonomy tasking, or downstream fusion.
Use labels MUST NOT weaken locked rules; they only constrain operational
consumption of already-valid data.

Risk filters MUST operate on labels, thresholds, and policy decisions. They MUST
NOT rewrite event meaning, units, identity, lineage, layer, version, confidence
semantics, or command safety to make an event pass.

Operator overrides are policy decisions, not semantic exceptions. A temporary
override MAY lower the operational response for tunable rules. Any override
that softens a material policy response SHOULD be rejected unless it includes
reason, scope, authority, and expiry. For command-related, trust-related,
promotion-related, safety-related, or external-boundary overrides, reason,
scope, authority, and expiry MUST be present. Overrides MUST NOT apply to locked
rules.

`quarantine` in this section is a policy action. It is not a v1.0 schema-level
trust state. Future trust/quarantine vocabulary must be introduced only through
an approved versioned branch.

### 3.4 Adapter and Gateway Enforcement

Adapters and gateways are semantic boundaries. They MUST:
- Preserve semantic layer separation.
- Normalize units and timestamps before emission.
- Regenerate ZMeta `event_id` values as UUIDv7 when ingesting legacy identifiers.
- Preserve legacy IDs in payload-scoped provenance fields when traceability is
  needed.
- Add `lineage.transform` for translation steps when applicable.
- Preserve source-authored semantic fields when projecting or forwarding.
- Avoid treating schema acceptance as semantic authorization.
- Emit diagnostics for rejected events, malformed events, and soft policy
  decisions without using those diagnostics as generic operational status,
  domain trust state, or lifecycle state.

Gateways MAY add non-semantic export metadata such as `profile`, `event.t_receive`,
or gateway-supplied `event.t_publish` when allowed by Section 4.2. Gateways MUST
NOT rewrite meaning to make an event appear valid.

### 3.5 Encoding Projection Enforcement

JSON, CBOR, compact CBOR, protobuf, and future encodings are projections. An
encoding has no independent semantic authority.

An encoded event is valid only if decoding yields a canonical ZMeta event that
passes the applicable schema, policy, and conformance requirements. Map order,
wire field order, compact integer keys, and protobuf field order are not
semantic.

Encoding versions, such as `compact_version`, track wire mapping compatibility.
They do not change ZMeta semantic meaning.

### 3.6 Conformance Test Enforcement

Conformance tests SHOULD prove:
- Valid examples pass.
- Known invalid examples fail for the expected reason.
- Version discrimination prevents extension bleed.
- Profile restrictions are enforced.
- Projection and encoding round trips preserve contract-relevant fields.
- Gateways preserve source-authored semantics.
- Adapters map raw data, AI claims, fusion, state, command, and system events to
  the correct semantic layers.

Conformance is the guard against implementation drift.

## 4. Locked v1.0 Semantic Invariants

The following invariants are locked for v1.0.

### 4.1 Event-Based Worldview

ZMeta represents events, not mutable objects or authoritative sensor state
records. Each message describes something that happened, was inferred, was
fused, was projected, was commanded, or was reported at a specific time.

There is no mutable authoritative object record in ZMeta v1.0.

### 4.2 Append-Only Immutability

ZMeta events are append-only. Once emitted, an event is never modified or
deleted. Corrections, reinterpretations, or refinements MUST be represented as
new events with new `event_id` values and lineage references.

Source-authored semantic content is immutable. A gateway, bridge, adapter,
exporter, or consumer MUST NOT change:
- `event.ts`
- `event.event_id`
- `event.event_type`
- `event.event_subtype`
- `source`
- `payload.track_id`
- `lineage`
- Payload meaning

Profile exports MAY be represented as projections of the same event when they
only:
- Add non-semantic export metadata, such as `profile`.
- Add gateway receipt/publish stamps, such as `event.t_receive` or
  gateway-supplied `event.t_publish`.
- Omit optional fields for bandwidth.
- Reduce numeric precision.
- Conservatively lower `confidence` or `valid_for_ms` to reflect export-path
  degradation.

Such projections preserve the original `event_id`.

Any semantic payload change, reinterpretation, correction, replacement of
source-authored fields, increase in confidence, increase in TTL, increase in
precision, or increase in specificity requires a new event with a new
`event_id` and lineage.

### 4.3 Event Identity

All ZMeta `event.event_id` values MUST be UUIDv7 per RFC 9562. UUIDv7 is also
required for `lineage.based_on` values and `payload.members` values that
reference ZMeta events.

UUIDv7 supports:
- Lineage reconstruction.
- Audit and replay ordering.
- Deduplication under high-rate emission.
- Track persistence across profiles.
- Sorting under constrained timing.

Adapters translating legacy systems with UUIDv4 or other identifiers MUST
regenerate `event_id` as UUIDv7 at the adapter boundary. Legacy identifiers MAY
be preserved in `payload.source_event_id` or an equivalent payload-scoped
provenance field.

Profile, transport, producer, and event type MUST NOT be encoded into
`event_id`.

The timestamp bits inside UUIDv7 represent identity-generation time only.
`event.ts` remains the authoritative capture, observation, or validity time.
Consumers MUST NOT infer event timing, ordering, or freshness from UUIDv7
timestamp bits when `event.ts` and timing quality metadata are available.

### 4.4 Layer Separation

ZMeta enforces strict separation between semantic layers:

| Layer | Event Type | Meaning |
|---|---|---|
| Fact | OBSERVATION_EVENT | What a sensor measured. |
| Opinion | INFERENCE_EVENT | What an algorithm or analyst-derived process claims. |
| Belief / continuity | FUSION_EVENT | What appears continuous across time or sensors. |
| Operator state | STATE_EVENT | What the system believes right now for operator consumption. |
| Bounded directive | COMMAND_EVENT | Low-rate cueing or tasking under governance. |
| Health / audit | SYSTEM_EVENT | Timing, link, validation, task acknowledgement, or status. |

No layer may collapse into another. Raw measurements MUST NOT masquerade as
state. Model claims MUST NOT create track identity. State projections MUST NOT
carry raw sensor features. Command events MUST NOT bypass deconfliction.

### 4.5 Authority Boundaries

Authority is assigned to logical functions and producer identities, not merely
to hardware location or deployment tier.

v1.0 authority boundaries:
- Sensors may emit OBSERVATION_EVENT and appropriate SYSTEM_EVENTs.
- AI and analytics modules may emit INFERENCE_EVENT and appropriate
  SYSTEM_EVENTs.
- Fusion nodes are the only components permitted to create `track_id`.
- State projectors and fusion nodes may emit STATE_EVENT.
- Operator interfaces such as TAK do not author or modify ZMeta events unless a
  future operator-annotation event type is explicitly defined.
- COMMAND_EVENTs may be emitted only by command-authorized or
  deconfliction-authorized producers.

`source.node_role` expresses deployment role, not physical location. If
analytics or fusion runs on an edge device, the logical producer still must use
an authority-appropriate role and producer identity. A single physical node MAY
host multiple logical functions, but each function must emit only the event
types it is authorized to produce. Separate producer identities SHOULD be used
when one software stack performs multiple roles.

Producer authority is deployment policy, not JSON Schema. A portable schema
does not hard-code local producer names.

### 4.5.1 External Projection Promotion

External systems such as CoT/TAK, JREAP-style gateways, MAVLink bridges, and
vendor COPs may report tracks that are already lossy projections, external
reports, or reflections of prior ZMeta output. Schema-valid shape is not enough
to make such input authoritative ZMeta state.

A lossy adapter projection or external tactical track report MUST NOT be
promoted to authoritative ZMeta `STATE_EVENT` unless promotion policy,
freshness, lineage status, confidence basis, trust reference, and loop/reflection
status are explicit and valid under active deployment policy.

Promotion rules:
- External promotion creates a new ZMeta event with a new `event.event_id`.
- The external source identifier MAY be retained as payload-scoped provenance or
  policy-scoped promotion metadata; it MUST NOT replace ZMeta event identity.
- When the external report has no ZMeta parent event, promotion metadata MUST
  preserve enough source identity and lineage status for audit. A future
  `OBSERVATION_EVENT` subtype for network/tactical reports may provide a cleaner
  parent evidence event, but that vocabulary is not valid in v1.0 unless a
  version branch adopts it.
- `lineage.transform` SHOULD identify the promotion transform, for example a
  `promote:<adapter>:<policy>` form, rather than a generic translation.
- A reflected ZMeta projection MUST NOT be promoted back into authoritative
  state unless loop/reflection checks prove it is not the same semantic event
  returning through a lossy adapter path.
- Promotion metadata MUST NOT carry raw sensor measurements, observation
  features, hidden defaults, or authority claims that override producer policy.
- Confidence in promoted state MUST be grounded in an explicit basis and MUST
  NOT increase merely because an external system reported the track.

Profile behavior:
- Profile H SHOULD carry full promotion audit detail, including source event
  identity when available, promotion policy, projection identity, confidence
  basis, freshness, trust reference, lineage status, and loop/reflection status.
- Profile M MAY carry compact policy, trust, projection, confidence-basis, and
  lineage-status references.
- Profile L MAY carry only compact handles, reason/status codes, and minimal
  lineage references needed to preserve auditability under the link budget.

Enforcement behavior:
- The reference policy rejects invalid external promotion by default.
- Deployments MAY tune the enforcement response to reject, warn, degrade, or
  quarantine according to local bandwidth, trust, and edge-operating conditions.
- Non-reject modes MUST emit an explicit diagnostic and MUST NOT erase the fact
  that promotion evidence was missing, stale, incomplete, or not approved.
- Degrade/quarantine modes MUST reduce confidence, shorten TTL, cap usable
  trust, or otherwise make the accepted state visibly lower authority than a
  clean promoted state.
- Loop/reflection risk SHOULD remain a hard rejection unless an operator
  deliberately enables a softer response with equivalent audit diagnostics.

External promotion metadata is policy-scoped boundary evidence. It is not
same-event profile projection metadata, and it does not make raw observation
fields valid inside `STATE_EVENT`.

### 4.6 Transport Is Non-Semantic

Transport choice carries no semantic meaning. LTE, IP radio, LoRa, mesh,
UDP, queues, files, CBOR, compact CBOR, protobuf, CoT, and future transports may
affect rate, payload density, or precision. They MUST NOT affect
interpretation.

Identical events flowing over different transports remain semantically
identical.

### 4.7 Profiles Thin Data, Never Reinterpret It

Profiles may:
- Remove optional fields.
- Reduce precision.
- Reduce update rate.
- Select a smaller encoding.

Profiles MUST NOT:
- Rename fields.
- Change units.
- Change meanings.
- Introduce implicit defaults.
- Increase confidence.
- Increase TTL.
- Invent precision that was not exported.
- Hide that a projection is degraded.

Profile thinning is about export fidelity, not semantic truth.

### 4.8 Mandatory Lineage

Lineage is required for:
- INFERENCE_EVENT
- FUSION_EVENT
- STATE_EVENT

COMMAND_EVENT and SYSTEM_EVENT lineage is optional unless a subtype or
deployment policy requires it.

Lineage enables auditability, AAR reconstruction, debugging, trust assessment,
and replay validation.

Lineage scope:
- `lineage.based_on` SHOULD reference immediate parent events only, not full
  ancestry, to keep payloads bounded.
- Full ancestry MAY be reconstructed from local storage or AAR data stores.
- Under constrained profiles, especially Profile L, lineage MAY reference
  non-exported events. Consumers must tolerate unresolved references according
  to profile policy.
- Envelope `lineage.based_on` is the authoritative audit lineage.
- Payload-local provenance fields such as `payload.based_on` MAY be used for
  claim-specific convenience.
- When both envelope lineage and payload-local references are present, payload
  references MUST be equal to or a subset of envelope lineage.

### 4.9 Explicit Uncertainty

ZMeta never implies certainty by omission. Confidence, quality, timing
uncertainty, geospatial uncertainty, degraded profile state, and lineage gaps
must be explicit when they are relevant to downstream use.

Degraded or low-quality data may still be valid. It must be marked truthfully.

### 4.10 Telemetry-First, Bounded Tasking

ZMeta is telemetry-first. It is not a continuous-control protocol.

Out-of-band control remains the default under unrestricted bandwidth, such as
MAVLink or a native autonomy API. ZMeta COMMAND_EVENT is permitted only for
low-rate cueing, retasking, and waypoint-level autonomy where the task is
TTL-bound, idempotent, deconflicted, and executed out-of-band.

AI and analytics producers SHALL NOT directly command platforms.

### 4.11 Vendor Extension Safety

Vendors may extend payloads within their domain. They may not:
- Alter the ZMeta envelope.
- Redefine core fields.
- Collapse semantic layers.
- Change units.
- Change lineage meaning.
- Change profile behavior.
- Create non-ignorable hidden semantics.

Extensions must remain safe to ignore by consumers that do not understand them,
unless a future versioned extension contract explicitly makes that extension
part of a selected subtype.

## 5. Time, Timing Quality, and PNT Degradation

Time semantics are critical for RF correlation, fusion, replay, and track
continuity.

### 5.1 Definition of `event.ts`

`event.ts` represents time of observation, capture, or validity. It does not
represent publish time, transmit time, or receive time.

Interpretation by event type:
- OBSERVATION_EVENT: when the sensor measurement was taken, or midpoint of a
  measurement window.
- INFERENCE_EVENT: the observation time of the primary input or inputs.
- FUSION_EVENT: the time the fused estimate is valid for, grounded in input
  observation times through lineage.
- STATE_EVENT: the time the state projection is valid for.
- COMMAND_EVENT: the command issue time or validity anchor.
- SYSTEM_EVENT: the time the reported system status is valid for.

### 5.2 Capture vs Publish vs Receive Time

`event.ts` is required. It is the semantic event time.

`event.t_publish` is optional. It records when a node emitted the event.

`event.t_receive` is optional. It records when a gateway ingested the event.

Gateway behavior:
- Gateways SHOULD stamp `event.t_receive` on forwarded events when missing.
- If `event.t_publish` is missing, gateways MAY set it to the same value as
  `event.t_receive` and SHOULD document that it was gateway-supplied.
- For bandwidth-constrained profiles, implementations MAY disable gateway
  latency stamps.

Publish and receive stamps are for debugging, latency analysis, and AAR. They
do not change event meaning.

### 5.3 Timing Quality Metadata

Timing quality metadata is mandatory for all profiles. A node MUST expose timing
quality either per event or periodically through SYSTEM_EVENT / TIME_STATUS. A
consumer receiving multiple events from a node MAY apply the latest TIME_STATUS
from that node until a newer status supersedes it, subject to freshness policy.

Minimum required TIME_STATUS fields:
- `time_source`: `GPS_PPS`, `GPS_NMEA`, `NTP`, `PTP`, `MANUAL`, or `UNKNOWN`
- `sync_state`: `LOCKED`, `HOLDOVER`, or `UNSYNCED`
- `est_error_ms`: worst-case absolute timestamp error upper bound
- `last_sync_ts`: last known synchronization time in UTC-Z

`est_error_ms` MUST NOT be omitted for RF and time-correlated fusion use cases.
Consumers MUST NOT treat periodic TIME_STATUS as valid indefinitely. If no
current timing status is available, consumers SHOULD treat timing quality as
unknown or stale and degrade confidence, gate fusion, warn, or reject according
to deployment policy.

When an event relies on periodic TIME_STATUS, consumers SHOULD compare the
event timestamp with the latest TIME_STATUS timestamp from the same source
identity. If the event timestamp is earlier than that TIME_STATUS by more than
the configured negative-age tolerance, the event MUST be labeled with
`TIMING_STATUS_AGE_NEGATIVE` or rejected according to policy. Implementations
MUST NOT clamp that negative interval to zero and treat it as clean freshness.
Small negative intervals within policy tolerance MAY be accepted to accommodate
benign out-of-order delivery.

### 5.4 Worst-Case Error Semantics

`est_error_ms` is a conservative upper bound. It is not 1-sigma, RMS, or a
statistical mean. Internal systems may use statistical timing models, but ZMeta
exposes worst-case timing error for interoperability.

### 5.5 Minimum Sync Approaches

Preferred:
- GPS PPS disciplined clock per node, expected error <= 1 ms.

Acceptable:
- NTP disciplined clock on a stable network, expected error roughly 10-50 ms.

Degraded:
- Unsynced or manually configured clocks. These must be marked as UNSYNCED with
  realistic error bounds.

### 5.6 Windowed Observations

If an observation is computed over a time window, include:
- `payload.t_start`
- `payload.t_end`

For RF windowed observations, `event.ts` MUST equal the midpoint of the window.
Validation tooling MAY allow up to 1 ms tolerance for fractional timestamp
serialization or rounding.

Future modality-specific contracts may define equivalent window behavior for
EO, IR, acoustic, network, radar, or other sensors.

### 5.7 Holdover and Drift

Loss of synchronization transitions a node to HOLDOVER. During holdover,
`est_error_ms` must monotonically increase. Upon re-lock, `sync_state` returns
to LOCKED and the error bound resets.

Monotonic holdover checks are policy/runtime enforcement, because they require
state across events.

### 5.8 Behavior Under Degraded Timing

Events may still be emitted under degraded timing. High-confidence
time-correlated fusion must be gated or down-weighted. Fusion and state outputs
must reflect degraded timing through confidence reduction, shorter TTL, warning,
or rejection according to policy.

### 5.9 Profile Timing Considerations

Profile L:
- `event.ts` is required.
- Timing quality metadata is required.
- `est_error_ms` MUST NOT be omitted.
- Timing quality may be sent periodically through TIME_STATUS when bandwidth is
  critical.

Profiles M/H:
- Timing quality metadata is required.
- Full timing quality SHOULD be emitted per event when practical or through
  periodic TIME_STATUS otherwise.

### 5.10 PNT Integrity Candidate

Timing quality is locked in v1.0. Broader PNT integrity is a future extension
candidate. Future PNT semantics SHOULD distinguish ordinary timing uncertainty
from navigation integrity conditions such as:
- GNSS jam suspicion.
- GNSS spoof suspicion.
- Degraded navigation source.
- Holdover quality.
- Manual position source.
- Conflicting PNT sources.
- Position source confidence.

PNT integrity should be policy-enforced and should cap confidence or quarantine
fusion/state when mission policy requires it. PNT integrity labels MUST NOT be
hidden inside ordinary confidence changes alone.

## 6. Units, Geodesy, and Measurement Quality

### 6.1 Coordinate Reference System

All geospatial coordinates SHALL use WGS-84. Latitude and longitude SHALL be
decimal degrees.

Ranges:
- Latitude: -90.0 to +90.0
- Longitude: -180.0 to +180.0

No alternate datums or coordinate systems are permitted in ZMeta v1.0 canonical
`geo`.

### 6.2 Altitude Reference

All altitude values SHALL be Height Above Ellipsoid (HAE) in meters.
Canonical altitude fields use `alt_m`.

MSL, AGL, terrain-relative, pressure altitude, or local-frame altitude are not
permitted in canonical ZMeta v1.0 `geo`. If an adapter ingests such values, it
must convert them or omit canonical `geo`.

### 6.3 Velocity and Motion

Linear speed is meters per second. Scalar speed fields such as `speed_mps` are
non-negative. Velocity vectors, when present, SHALL be earth-referenced unless a
future versioned feature contract explicitly states otherwise.

Acceleration, if present in a governed extension, is meters per second squared.

### 6.4 Bearings, Angles, and Orientation

Bearings and headings are degrees true north, increasing clockwise, range
0-360 inclusive. `360` is valid and equivalent to `0`; adapters MAY normalize
`360` to `0`, but consumers MUST treat both as valid.

Canonical `bearing.az_deg` SHALL be degrees true north. Sensor-native frames,
such as array-relative, platform-relative, or magnetic bearings, MUST be
converted to true north before canonical emission or the canonical `bearing`
omitted with the raw values placed in explicitly named payload-scoped fields
that cannot be confused with canonical bearings.

Under `zmeta_version` 1.1.0, producers SHOULD assert the frame explicitly via
`bearing.frame: "TRUE_NORTH"`. `TRUE_NORTH` is the only valid value; any other
frame label is schema-invalid, so a mislabeled sensor-native frame is
machine-caught rather than silently consumed.

Producers MAY record frame provenance in the free-form quality object via
`quality.bearing_frame` and `quality.heading_source`. `quality.bearing_frame`
(string) describes the canonical bearing only and therefore permits exactly
the same single value, `TRUE_NORTH`, as `bearing.frame`; its purpose is to let
v1.0 consumers distinguish assertively frame-compensated bearings from legacy
unlabeled ones. Raw sensor-native angles never use this field; they carry
their frame in their explicitly named payload-scoped field, for example a
features key naming the frame. `quality.heading_source` (string) identifies
the heading reference used for compensation, e.g. `AHRS_TRUE`, `GPS_COURSE`,
`FIXED_MOUNT_SURVEYED`. Because v1.0 is locked and its `bearing` object
rejects the `frame` key, this quality-scoped mechanism is the only frame
provenance available to v1.0-emitting producers.

Pitch, roll, and yaw, if present, are degrees.

### 6.5 Distance, Range, and RF Units

Distances and ranges are meters. Frequency and bandwidth are Hertz. Power is
dBm unless a field name explicitly states another unit.

Alternate internal units, such as dBFS or vendor-specific RF quality scores,
must be converted before canonical emission or placed in explicitly named
payload-scoped extension fields that cannot be confused with canonical units.

### 6.6 Time Units

Timestamps are UTC RFC 3339 date-time strings serialized with trailing `Z`.
Numeric offsets and timezone-less timestamps are not valid ZMeta wire format.

Durations and time deltas are milliseconds unless otherwise specified.

### 6.7 Unit Inference Is Forbidden

Consumers MUST NOT infer units by context. Absence of units does not imply
defaults. Fields without defined units are invalid for fusion and correlation
unless a versioned feature contract defines them.

### 6.8 Degraded or Partial Geospatial Data

Events with incomplete geospatial information may still be emitted.

Canonical `geo` is all-or-nothing. If any of `lat`, `lon`, or `alt_m` is
missing, omit `geo` entirely. Missing values MUST be omitted, not zero-filled.
Confidence and quality metadata must reflect reduced spatial certainty.

The `(0, 0, 0)` sentinel pattern is not valid evidence of unknown position.
Adapters MUST NOT emit zero-filled geospatial data to satisfy schema shape.

## 7. v1.0 Event Model and Payload Contracts

### 7.1 Canonical Envelope

Every ZMeta event has the following logical envelope:

```text
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
  payload: object
  confidence?: float
  lineage?: {
    based_on: UUIDv7[]
    transform?: string
  }
}
```

Envelope rules:
- Source-authored envelope fields are immutable and globally consistent.
- Payload semantics are determined exclusively by `event.event_type` and
  `event.event_subtype`.
- `confidence` is mandatory for INFERENCE_EVENT, FUSION_EVENT, and STATE_EVENT.
- `confidence` is prohibited for OBSERVATION_EVENT, COMMAND_EVENT, and
  SYSTEM_EVENT.
- `profile` is optional and reflects the export profile applied at emission
  time. Profile MUST NOT be encoded into `event_id`.

### 7.2 Event Types

v1.0 event types are:
- OBSERVATION_EVENT
- INFERENCE_EVENT
- FUSION_EVENT
- STATE_EVENT
- COMMAND_EVENT
- SYSTEM_EVENT

No additional top-level event types are permitted in v1.0.

### 7.3 Event Subtype Namespace

`event.event_subtype` is a semantic discriminator, not a decorative label. For
v1.0, it MUST come from the namespace assigned to `event.event_type` and MUST
match the payload discriminator exactly.

| event_type | allowed event_subtype values | required payload match |
|---|---|---|
| OBSERVATION_EVENT | `RF`, `EO`, `IR`, `ACOUSTIC`, `NETWORK` | `event_subtype == payload.modality` |
| INFERENCE_EVENT | `CLASSIFICATION`, `ASSOCIATION`, `ANOMALY`, `BEHAVIOR` | `event_subtype == payload.inference_type` |
| FUSION_EVENT | `TRACK_FUSION` | fixed subtype |
| STATE_EVENT | `TRACK_STATE` | fixed subtype |
| COMMAND_EVENT | `GOTO`, `ORBIT`, `HOLD`, `SEARCH_BOX` | `event_subtype == payload.task_type` |
| SYSTEM_EVENT | `LINK_STATUS`, `TIME_STATUS`, `SCHEMA_VIOLATION`, `TASK_ACK` | `event_subtype == payload.system_type` |

Rules:
- Producers MUST NOT use free-form subtypes.
- Envelope subtype and payload discriminator disagreement is invalid.
- Adapter/vendor labels belong in payload-scoped provenance or ignorable
  extensions, not in `event_subtype`.
- Future subtype values require a version branch, schema branch, semantic
  definition, and conformance tests.

### 7.4 OBSERVATION_EVENT

OBSERVATION_EVENT represents raw sensor-derived facts. It does not carry
classification, track identity, fused state, or operator belief.

Generic observation payload:

```text
ObservationPayload {
  modality: RF | EO | IR | ACOUSTIC | NETWORK
  geo?: { lat, lon, alt_m }
  bearing?: { az_deg, el_deg? }
  features: object
  quality?: object
  timing_quality?: object
  data_ref?: object
  data_refs?: object[]
  t_start?: UTC_TIMESTAMP
  t_end?: UTC_TIMESTAMP
}
```

Observation rules:
- `track_id` is prohibited.
- `entity_class` is prohibited.
- Classification, label, and class name fields are prohibited as observation
  facts.
- Top-level `confidence` is prohibited.
- `event.ts` is capture time or midpoint of a window.
- Observation quality belongs in `payload.quality` or a governed quality block,
  not in top-level confidence.

RF minimum features:

```text
features {
  center_freq_hz: number
  bandwidth_hz: number
  power_dbm: number
  signature_hash?: string
}
```

Additional RF features may be appended if they do not change meaning.

Raw data distinction:
- Raw observations are measured facts.
- AI detections or classifications derived from raw observations are
  INFERENCE_EVENTs.
- A raw image crop or RF measurement may be an observation feature.
- A detected object bounding box, entity class, acoustic source label, behavior,
  or model score is an inference claim.

### 7.5 INFERENCE_EVENT

INFERENCE_EVENT represents algorithmic or analytic claims derived from one or
more observations.

Inference payload:

```text
InferencePayload {
  inference_type: CLASSIFICATION | ASSOCIATION | ANOMALY | BEHAVIOR
  claim: object
  model: { name, version }
  based_on: UUIDv7[]
  timing_quality?: object
}
```

Inference rules:
- It MUST reference upstream observations through lineage.
- It MUST include `payload.model.name` and `payload.model.version`.
- It MUST include top-level `confidence`.
- It MUST NOT emit `track_id`.
- `payload` and `payload.claim` MUST NOT contain `track_id`, `members`, or
  `estimated_state`.
- Confidence reflects model or analytic confidence, not truth.

AI provenance semantics are expanded in Section 11.

### 7.6 FUSION_EVENT

FUSION_EVENT represents cross-sensor or temporal association resulting in
provisional continuity.

Fusion payload:

```text
FusionPayload {
  track_id: string
  members: UUIDv7[]
  estimated_state?: {
    geo?: { lat, lon, alt_m }
    bearing?: { az_deg, el_deg? }
    heading_deg?: number
    speed_mps?: number
  }
  stability: float
  last_seen_ts: UTC_TIMESTAMP
  timing_quality?: object
}
```

Fusion rules:
- Only fusion-authorized producers may create `track_id`.
- Track identity is provisional and revisable.
- Once assigned, a `track_id` MUST persist unchanged for subsequent events that
  reference the same track.
- `track_id` values MUST be globally unique.
- `track_id` values MUST NOT be reused after loss, merge, split, or retirement.

### 7.7 STATE_EVENT

STATE_EVENT represents current system belief intended for operator-facing
systems such as TAK, JREAP gateways, dashboards, or local operator views.

Track state payload:

```text
TrackStatePayload {
  track_id: string
  geo: { lat, lon, alt_m }
  heading_deg?: number
  speed_mps?: number
  class?: string
  source_summary?: string[]
  valid_for_ms: number
  timing_quality?: object
  extensions?: object
}
```

State rules:
- STATE_EVENT / TRACK_STATE is the only v1.0 payload translated to
  operator-facing track projections such as CoT/TAK or JREAP-style tactical
  track JSON.
- Sensor-metadata projections such as KLV-style observation exports remain
  OBSERVATION-based.
- STATE_EVENT is derived from FUSION_EVENTs or equivalent fusion-authorized
  state projection.
- STATE_EVENT payloads MUST NOT contain raw sensor features, raw measurements,
  observation modalities, observation timestamps, or raw artifact references.
- Prohibited state payload fields include `features`, `raw_features`,
  `modality`, `measurement`, `measurements`, `t_start`, `t_end`, `data_ref`,
  and `data_refs`.
- Traceability is provided through `lineage.based_on`, not raw data pointers in
  state payloads.
- `extensions` MAY carry UI or rendering metadata, but MUST NOT reinterpret
  state semantics or carry raw measurements.

### 7.8 COMMAND_EVENT

COMMAND_EVENT represents discrete mission directives used only for
tipping/cueing and waypoint-level autonomy. It is most important under
constrained links but remains bounded in every profile.

Command payload:

```text
CommandPayload {
  task_id: string
  task_type: GOTO | ORBIT | HOLD | SEARCH_BOX
  target_geo?: { lat, lon }
  geometry?: object
  valid_from_ts?: UTC_TIMESTAMP
  valid_for_ms: number
  priority?: LOW | MED | HIGH
  requires_deconfliction: true
  timing_quality?: object
  extensions?: object
}
```

Command rules:
- COMMAND_EVENT is not continuous control.
- COMMAND_EVENT MUST be idempotent by `payload.task_id`.
- COMMAND_EVENT MUST route through a Comms/Deconfliction Node or
  command-authorized producer.
- COMMAND_EVENT is executed out-of-band through the receiving autonomy or sensor
  layer.
- `GOTO` requires `target_geo` and does not permit `geometry`.
- `ORBIT` requires `target_geo` and orbit geometry with at least `pattern` and
  `radius_m`.
- `HOLD` is TTL-bound and may include `target_geo`; it does not require or
  permit `geometry`.
- `SEARCH_BOX` requires 2D search-box geometry and does not require
  `target_geo`.
- COMMAND_EVENT SHALL NOT specify altitude.
- Command payloads, `target_geo`, `geometry`, and command `extensions` MUST NOT
  contain common altitude fields such as `alt_m`, `altitude_m`, `alt_hae_m`,
  `alt_msl_m`, `agl_m`, `target_alt_m`, `altitude`, or `target_altitude`.
- `extensions` MAY carry command-safe vendor metadata, but MUST NOT imply
  vertical control, continuous control, or bypass deconfliction.

### 7.9 SYSTEM_EVENT

SYSTEM_EVENT represents platform, transport, validation, timing, task
acknowledgement, or schema health.

System payload:

```text
SystemPayload {
  system_type: LINK_STATUS | TIME_STATUS | SCHEMA_VIOLATION | TASK_ACK
  state: string
  metrics?: object
}
```

No additional `system_type` values are permitted in v1.0.

#### TASK_ACK

TASK_ACK provides an auditable lifecycle for COMMAND_EVENTs.

Required metrics:
- `task_id`
- `original_event_id`

Allowed states:
- `RECEIVED`
- `ACCEPTED`
- `REJECTED`
- `EXECUTING`
- `COMPLETED`
- `FAILED`
- `CANCELLED`
- `EXPIRED`
- `DUPLICATE_IGNORED`

`metrics.reason_code` is required for:
- `REJECTED`
- `FAILED`
- `CANCELLED`
- `EXPIRED`
- `DUPLICATE_IGNORED`

Allowed TASK_ACK reason codes:
- `SCHEMA_INVALID`
- `EVENT_TYPE_NOT_ALLOWED_FOR_ROLE`
- `EVENT_TYPE_NOT_ALLOWED_FOR_PROFILE`
- `PRODUCER_NOT_ALLOWED`
- `COMMAND_NOT_DECONFLICTED`
- `COMMAND_HAS_ALTITUDE`
- `TASK_DUPLICATE`
- `TASK_EXPIRED`
- `TASK_CANCELLED`
- `TASK_FAILED`
- `TASK_ABORTED`
- `TASK_REJECTED`

#### LINK_STATUS

LINK_STATUS provides standardized transport health for AAR, debugging, and UI
overlays.

Required metrics:
- `link_id`
- `latency_ms`
- `packet_loss_pct`
- `throughput_bps`

Allowed states:
- `UP`
- `DEGRADED`
- `DOWN`
- `UNKNOWN`

`metrics.reason_code` is required for `DEGRADED` and `DOWN`.

Allowed LINK_STATUS reason codes:
- `LINK_LOSS`
- `LOW_RSSI`
- `HIGH_LATENCY`
- `HIGH_PACKET_LOSS`
- `LOW_THROUGHPUT`
- `INTERFERENCE`
- `JAMMED`
- `BACKHAUL_DOWN`
- `NO_ROUTE`
- `CONFIG_ERROR`
- `POWER_SAVE`
- `UNKNOWN_CAUSE`

#### TIME_STATUS

TIME_STATUS reports node timing quality. Required metrics are listed in Section
5.3.

`TIMING_STATUS_AGE_NEGATIVE` is the governed diagnostic reason for events whose
timestamp predates the latest applicable TIME_STATUS by more than policy
tolerance. It is a timing-quality anomaly label; it does not create new event
vocabulary or new timing fields.

#### SCHEMA_VIOLATION

SCHEMA_VIOLATION is the v1.0 diagnostic envelope for schema and policy
validation outcomes. It represents rejected events, malformed events, and
gateway/policy warnings about accepted events. It provides auditability for
AAR/debug and risk filtering.

Required metrics:
- `reason_code`
- `original_event_id`

`metrics.reason_code` MUST be one of the codes defined by the active governed
diagnostic vocabulary.

Recommended optional metrics:
- `path`
- `error`

For soft policy decisions, SCHEMA_VIOLATION SHOULD use `payload.state: WARNING`
and SHOULD include the risk adjudication fields from Section 3.3 when practical.

SCHEMA_VIOLATION MUST NOT be reused as a domain trust state, quarantine state,
track lifecycle state, or general status event. Normal operational degradation
such as memory pressure, timing loss, track merge, or link degradation SHOULD be
reported through the appropriate status event, local log, policy warning, or
future versioned vocabulary. If the degradation causes a policy warning or
rejection, SCHEMA_VIOLATION MAY carry the diagnostic reason, but the diagnostic
MUST NOT make the event's semantic meaning appear cleaner than it is.

A future branch SHOULD define a clearer policy diagnostic subtype such as
`POLICY_ADJUDICATION` or `POLICY_DIAGNOSTIC`. Until that branch is approved,
SCHEMA_VIOLATION remains the v1.0 compatibility envelope for schema and policy
diagnostics.

## 8. Confidence, Uncertainty, and Trust

### 8.1 Confidence Is Not Truth

`confidence` is not truth. It is a bounded machine-readable estimate of how safe
an INFERENCE_EVENT, FUSION_EVENT, or STATE_EVENT is for downstream use under the
producer's documented assumptions.

Top-level `confidence`:
- MUST be in `[0.0, 1.0]`.
- MUST be present for INFERENCE_EVENT, FUSION_EVENT, and STATE_EVENT.
- MUST be absent for OBSERVATION_EVENT, COMMAND_EVENT, and SYSTEM_EVENT.
- MUST NOT be increased during profile projection.
- SHOULD be reduced or capped when timing, lineage, input quality, stale data,
  degraded compute, profile thinning, or raw-data absence materially reduces
  use safety.

### 8.2 Observation Quality Is Not Inference Confidence

OBSERVATION_EVENTs describe measured facts. Observation quality fields such as
SNR, measurement error, calibration state, geolocation status, or sensor quality
describe measurement quality. They are not top-level confidence and do not imply
classification, identity, or track persistence.

INFERENCE_EVENT confidence describes model or analytic claim confidence. A good
sensor measurement can still produce a poor inference. A poor sensor measurement
can still be valuable if the uncertainty is explicit.

### 8.3 Fusion and State Confidence

Fusion and state confidence MUST account for:
- Input confidence.
- Observation quality.
- Timing quality and PNT degradation.
- Lineage availability and parent quality.
- Fusion stability.
- Observation freshness.
- Profile projection effects.
- Compute degradation or fallback model behavior, when applicable.
- Raw-data availability, when relevant to downstream trust.

Fusion confidence SHOULD NOT appear more reliable than the weakest material
input unless the producer's documented model justifies the increase.

### 8.4 Confidence During Profile Projection

Profile projection may reduce precision, remove optional fields, reduce rate, or
reduce confidence/TTL. It MUST NOT increase confidence, TTL, precision, or
specificity.

Profile L events MUST NOT reduce confidence merely because they are Profile L.
Confidence reduction is appropriate only when Profile L actually removes context
or precision that materially affects use safety.

### 8.5 Trust Is Separate From Confidence

Trust, if introduced, is separate from confidence.

Confidence is about the event claim or state estimate.

Trust is about source identity, key identity, route/path integrity, producer
authorization, release domain, quarantine status, and spoof/replay suspicion.

Future trust fields MUST NOT replace confidence. A high-confidence event from an
untrusted producer may still be quarantined. A trusted producer may still emit a
low-confidence event.

### 8.6 Confidence Decomposition

Confidence decomposition is a future extension candidate. A future version may
define machine-readable components such as:
- `model_confidence`
- `measurement_quality_factor`
- `timing_factor`
- `lineage_factor`
- `freshness_factor`
- `profile_factor`
- `compute_factor`
- `raw_data_factor`
- `human_confirmation_factor`

Until such a branch is approved, producers SHOULD document confidence formulas
in operational runbooks or non-semantic metadata.

## 9. Lineage, Provenance, Evidence, and Raw-Data-Absent Mode

### 9.1 Authoritative Lineage

`lineage.based_on` is the authoritative causal/audit link between events. It is
not optional for INFERENCE_EVENT, FUSION_EVENT, or STATE_EVENT.

Lineage may reference events that were not exported over a constrained link.
This is especially common in Profile L. Unresolved lineage is allowed only as a
profile/deployment policy decision and should affect trust or confidence when
material.

### 9.2 Payload-Scoped Provenance

Payload-scoped provenance MAY include:
- Legacy event IDs.
- Source object IDs.
- Source sensor identifiers.
- Adapter transform names.
- Model names and versions.
- Raw artifact pointers where allowed.

Payload provenance MUST NOT override envelope lineage, event identity, timing,
confidence, source identity, or payload meaning.

### 9.3 Data References in v1.0 and v1.1.0

In v1.0, lightweight data references are optional provenance pointers when
present on observation payloads. They are not required for validity and do not
replace lineage. Consumers may ignore unresolved pointers without changing the
meaning of the event.

In v1.1.0, `payload.data_ref` and `payload.data_refs` are formalized extension
semantics with stricter pointer rules.

Data references:
- MUST point to retained artifacts or derived vectors.
- MUST NOT contain raw payload data.
- MUST NOT override event semantics, confidence, lineage, timing, or payload
  fields.
- MUST NOT appear in STATE_EVENT payloads.

### 9.4 Raw-Data-Absent Mode

ZMeta must remain trustworthy when raw data is unavailable over the link or was
never retained. Raw-data absence is not a validation failure by itself. It is a
trust and provenance condition.

v1.0 behavior:
- If raw data is retained and pointer metadata is safe to export, an
  OBSERVATION_EVENT MAY include `data_ref` or `data_refs`.
- If raw data is retained locally but not exported, lineage still references
  parent events and local AAR stores may reconstruct full ancestry.
- If raw data is unavailable, omitted, withheld, or not retained, the event may
  still be valid, but confidence/trust should reflect the reduced audit depth
  when relevant.
- Profile L may export STATE_EVENT with lineage pointing to non-exported parent
  events.

Future evidence status vocabulary SHOULD distinguish:
- Raw data available locally.
- Raw data referenced by pointer.
- Raw data not retained.
- Raw data withheld by profile.
- Raw data withheld by coalition or release rule.
- Raw data unavailable due to bandwidth.
- Raw data unavailable due to sensor condition.
- Raw data redacted or sanitized for cross-domain export.

These status labels are future candidates until a versioned schema and policy
branch adopts them.

### 9.5 Replay and Red-Team Labels

Replay, simulation, exercise, synthetic, and red-team/adversarial labels are
future extension candidates. Until adopted, replay tools and test harnesses must
not make replayed data indistinguishable from live operational data in operator
systems unless the operator has explicitly selected replay mode.

Future replay semantics SHOULD define:
- Live vs replayed event labels.
- Historical event time vs wall-clock projection time.
- Red-team event labels.
- Synthetic data labels.
- Policy rules for export, display, quarantine, and AAR.

## 10. Profiles, Bandwidth, and Degraded Operation

Profiles define transport-driven export constraints, not semantic shortcuts.
The internal semantic pipeline remains valid in all profiles.

### 10.1 Profile L

Profile L is for severe constraint and denied environments.

Profile L transmits:
- STATE_EVENT
- SYSTEM_EVENT
- COMMAND_EVENT for bounded mission directives

Profile L behavior:
- Nodes SHALL perform local processing necessary to emit honest, time-bounded
  STATE_EVENTs reflecting best available belief.
- Lineage MUST still be included, even when parents were not exported.
- Lineage may reference non-exported local events.
- Confidence, timing quality, and short TTL MUST reflect degraded conditions.
- Identity remains provisional and revisable.

Profile L prohibits:
- Raw observation export.
- INFERENCE_EVENT export.
- Semantic reinterpretation.
- Hidden precision.

### 10.2 Profile M

Profile M is for constrained IP or intermittent backhaul.

Profile M transmits:
- STATE_EVENT
- FUSION_EVENT
- SYSTEM_EVENT
- COMMAND_EVENT
- Selected OBSERVATION_EVENTs when justified

Profile M does not export INFERENCE_EVENT unless a future schema/profile branch
explicitly allows selected inference export.

### 10.3 Profile H

Profile H is full fidelity and preferred operation when bandwidth permits.

Profile H transmits all valid event types:
- OBSERVATION_EVENT
- INFERENCE_EVENT
- FUSION_EVENT
- STATE_EVENT
- COMMAND_EVENT
- SYSTEM_EVENT

Profile H has no justification for layer collapse.

### 10.4 Profile Rule Global

Profiles may remove optional fields, reduce rate, reduce precision, and select
wire encodings. They never reinterpret meaning. If `profile` is present, schema
validation enforces event-type compatibility. If `profile` is omitted, runtime
gateway/policy profile still governs export behavior.

### 10.5 Emergency / L0 Mode Candidate

An emergency mode below Profile L is a future candidate. The preferred design is
to keep H/M/L stable and express emergency behavior through projection metadata,
thinning policy identifiers, queue/burst behavior, and explicit degradation
reasons. A fourth profile should be adopted only if a versioned design proves
that H/M/L plus projection policy cannot express the operational need.

Emergency or L0 vocabulary is not valid v1.0 or v1.1.0 vocabulary unless
adopted by a version branch.

An Emergency or L0 mode SHOULD define:
- Minimum useful state.
- Very short TTL.
- Explicit confidence cap.
- Unresolved lineage tolerance.
- Explicit degraded profile marker.
- No hidden precision.
- No raw observations.
- No inference export.
- No command behavior unless separately authorized.
- Store-and-forward or burst semantics.

Emergency/L0 behavior MUST NOT silently drop required v1.0 semantics under
the name of bandwidth optimization. If v1.0 cannot fit, a versioned emergency
mode must define what replaces it.

### 10.6 Projection and Thinning Metadata Candidate

Projection metadata is a future extension candidate. It SHOULD make profile
thinning, redaction, emergency behavior, and replay projection explicit without
overloading the `profile` field.

Future projection metadata SHOULD define:
- Source profile.
- Export profile.
- Thinning policy ID.
- Export or guard policy ID.
- Omitted field categories or field paths.
- Precision changes.
- TTL or confidence reductions.
- Projection reason codes such as link degradation, partner release, emergency
  burst, replay, or operator view policy.
- Whether the same `event_id` is preserved or a new redacted/projection event
  was created under a versioned projection rule.

Projection metadata MUST NOT permit semantic reinterpretation, unit changes,
track identity changes, confidence increases, TTL increases, or hidden
precision.

### 10.7 Edge Failure Modes

Edge nodes in Profile L or M deployments must support defensible failure-mode
behavior while preserving semantic invariants. Configuration may change rates,
TTLs, confidence reductions, queueing, and local gating behavior. It may not
change event meaning.

Default failure-mode expectations:

| Failure Mode | Default Semantic Behavior |
|---|---|
| Timing loss | Emit TIME_STATUS with UNSYNCED or HOLDOVER, reduce or cap STATE_EVENT confidence, and gate high-precision fusion. |
| Observation timeout | Continue STATE_EVENT only while `valid_for_ms` truthfully represents stale data; reduce confidence or TTL. |
| Deconfliction node offline | Queue COMMAND_EVENTs with TTL; do not execute undeconflicted commands; emit TASK_ACK failure or expiry when applicable. |
| Memory/storage exhausted | Drop non-lineage optional fields first, then optional payload references, then older lineage references while retaining the most recent; only then drop observations. Record the condition in logs or future status events. |
| Link degradation | Emit LINK_STATUS, thin optional payload fields per profile, and reduce rate as policy allows. |
| Fusion instability | Hold STATE_EVENT emission or emit degraded low-confidence state until stability improves or TTL expires. |

Even under degradation:
- No semantic reinterpretation.
- Uncertainty remains explicit.
- Risk labels and policy decisions remain filterable.
- Required lineage remains present.
- Immutability remains intact.
- Auditability is preserved where a status event or local log is available.

## 11. AI Provenance and Inference Semantics

AI outputs are INFERENCE_EVENTs unless and until a fusion node converts them into
track continuity or state. AI outputs MUST NOT be emitted as raw observations
and MUST NOT create track identity.

### 11.1 v1.0 AI Provenance

v1.0 INFERENCE_EVENT requires:
- `payload.inference_type`
- `payload.claim`
- `payload.model.name`
- `payload.model.version`
- `payload.based_on`
- top-level `confidence`
- envelope `lineage.based_on`

`payload.model.name` identifies the model or analytic process. It is not a
producer identity. `payload.model.version` identifies the model version used for
the claim. Both must be stable enough for AAR and debugging.

`payload.claim` contains the model claim, such as classification, association,
anomaly, or behavior. It must not include `track_id`, `members`, or
`estimated_state`.

### 11.2 Model Confidence

Model confidence is part of INFERENCE_EVENT confidence. It is not truth. It is
also not observation quality. An inference confidence may be low because of weak
model evidence, degraded input, missing raw data, poor timing, or runtime
degradation.

### 11.3 Input Lineage

AI inference MUST reference input observations through lineage. If raw data is
not retained or not exportable, lineage still references the parent event
identity. Raw-data absence should be reflected through future evidence status
labels or local policy until a version branch adopts explicit fields.

### 11.4 Future AI Provenance Extensions

The following are v1.1+ or v1.2+ candidates:
- Model family.
- Stable model identifier or model version digest.
- Runtime class or inference service identifier where it affects output
  interpretation.
- Calibration profile.
- Model drift status.
- Runtime monitoring status.
- Degraded input flags.
- Confidence decomposition.
- MODEL_STATUS, ASSURANCE_EVENT, or another governed status mechanism for
  drift, OOD, calibration, runtime health, and assurance state.

These fields MUST NOT be treated as valid v1.0 requirements unless a future
version branch adopts them.

## 12. Compute Elasticity

ZMeta must survive across edge compute tiers without collapsing semantics.
Compute tier may reduce which events are emitted or how often they are emitted.
It may not make a weaker event pretend to be a stronger semantic layer.

### 12.1 Compute Tiers

Compute tier labels are future candidates, but the semantic expectations are:

| Compute Class | Expected Behavior |
|---|---|
| Full compute | Can emit observations, inferences, fusion, state, status, and full lineage as profile allows. |
| Medium compute | May reduce model complexity, event rate, feature richness, or local retention while preserving layer separation. |
| Thin compute | May emit observations and status, or locally projected state if fusion authority exists, with explicit degraded quality. |
| MCU / emergency compute | May be limited to minimal state/status beacons or store-and-forward records under a future emergency mode. |

### 12.2 Compute Degradation Rules

Lower compute may:
- Reduce emitted event types.
- Reduce update rate.
- Use simpler models.
- Omit optional fields.
- Emit lower confidence.
- Shorten TTL.
- Emit degraded system status.

Lower compute MUST NOT:
- Emit raw measurements as state.
- Emit AI claims as observations.
- Create track identity without fusion authority.
- Hide model fallback.
- Increase confidence to compensate for missing compute.
- Invent precision not present in inputs.

### 12.3 Model Fallback

If a producer switches to a fallback model or reduced runtime path, downstream
consumers should be able to detect that through model version, future runtime
provenance fields, system status, or deployment logs. Future versions SHOULD
standardize fallback indicators and confidence caps.

## 13. Track Persistence and Lifecycle Governance

### 13.1 Track ID

Track identity is anchored in `payload.track_id`, assigned only by fusion
authority.

Rules:
- `track_id` MUST persist unchanged across subsequent events referencing the
  same track.
- `track_id` is profile-agnostic.
- `track_id` SHOULD be human-readable when practical but MUST be globally
  unique.
- `track_id` MUST NOT be reused after a track is lost, merged, split, or
  retired.

### 13.2 Deduplication

Event deduplication uses immutable `event_id` unless an event type has an
explicit idempotency key.

Rules:
- OBSERVATION_EVENT, INFERENCE_EVENT, FUSION_EVENT, STATE_EVENT, and ordinary
  SYSTEM_EVENTs dedupe by `event_id`.
- COMMAND_EVENT dedupes by `payload.task_id`.
- Duplicate COMMAND_EVENTs MUST NOT be forwarded for execution a second time.
- TASK_ACK dedupes by `payload.metrics.task_id` +
  `payload.metrics.original_event_id` + `payload.state`.

### 13.3 Lifecycle States

v1.0 defines lifecycle semantics but does not define dedicated machine-readable
lifecycle event types for every state.

Lifecycle meanings:
- NEW: a fusion node emits an initial FUSION_EVENT with a new `track_id`.
- ACTIVE: the fusion node continues emitting FUSION_EVENT and STATE_EVENT
  updates for the same `track_id`.
- STALE: inputs are older than a configured threshold; confidence and TTL must
  decay.
- LOST: observations exceed a configured age threshold; state emission stops or
  remains explicitly stale/low confidence until TTL expires.
- MERGED: two tracks are determined to be the same entity; emit a new
  FUSION_EVENT with canonical `track_id` and lineage to both histories; retire
  the non-canonical ID.
- SPLIT: one track becomes multiple entities; emit new FUSION_EVENTs with
  distinct `track_id` values and lineage to the original history.
- RETIRED: a track ID will not be used again.

Merge/split/lost/retired SHOULD be recorded in local AAR/operator logs or future
versioned lifecycle events. They MUST NOT be represented by mutating old events.

### 13.4 Track Confidence Decay

Track confidence should decay when:
- Observations become stale.
- Timing status becomes stale or degraded.
- Lineage parents are unresolved beyond profile policy.
- Fusion stability degrades.
- Compute fallback changes inference quality.
- Raw data is absent and audit depth matters.

Exact decay formulas are policy or producer guidance unless a future version
standardizes them.

### 13.5 Display Projection and Operator Override

Operator display projections must be derived from STATE_EVENT. Displays may
hide, highlight, group, or annotate state, but must not mutate the underlying
event.

Operator confirmation, analyst adjudication, and operator override are future
extension candidates. They should be represented as new events referencing prior
events, not as edits to existing ZMeta events.

## 14. Operator State Projection and CoT/TAK Mapping

STATE_EVENT / TRACK_STATE is the v1.0 projection point for operator-facing
tracks. CoT/TAK, JREAP-style tactical track JSON, dashboards, and other display
formats must preserve:
- `payload.track_id` as the track identity.
- `payload.geo` as WGS-84/HAE position.
- `payload.valid_for_ms` as freshness/stale behavior.
- Confidence and lineage as ZMeta-side audit context, even when downstream
  formats cannot carry them fully.

CoT/TAK projection rules:
- Only STATE_EVENT / TRACK_STATE projects to operator track CoT in v1.0.
- Observation metadata exports remain observation-based, not state tracks.
- CoT display conveniences such as callsign fallback, team color, icons, labels,
  or wall-clock replay mode are adapter behavior, not semantic truth.
- If a projection omits confidence or lineage because the downstream format does
  not support them, the original ZMeta event remains authoritative.

CoT/TAK ingress is a lossy adapter boundary. CoT/TAK input SHOULD be treated as
external report evidence unless active promotion policy authorizes conversion
into ZMeta `STATE_EVENT`. Any promotion to `STATE_EVENT` MUST satisfy the
external projection promotion requirements in Section 4.5.1, including explicit
promotion policy, freshness, lineage status, confidence basis, trust reference,
and loop/reflection status. Confidence and lineage remain necessary for promoted
state, but they are not sufficient by themselves.

## 15. Command and Tasking Governance

COMMAND_EVENT exists only for bounded mission tasking and cueing. It does not
replace native command/control.

The Comms/Deconfliction Node or command-authorized producer is responsible for:
- Validating command schema.
- Deduplicating `task_id`.
- Deconflicting airspace and mission intent.
- Converting permitted mission tasks into MAVLink, Swarm API, or other native
  command channels for execution.
- Emitting TASK_ACK lifecycle events.

Not permitted via ZMeta:
- Safety-critical actuator commands without deconfliction.
- High-rate flight control.
- Continuous control loops.
- Hidden altitude or vertical control.

Future operator approval/override semantics must be represented as additional
versioned audit events, not as mutation of COMMAND_EVENT.

## 16. Security, Mesh Trust, Signing, and Quarantine

This section defines future semantic direction and policy guidance. It does not
create valid v1.0 event fields unless a future version branch adopts them.

### 16.1 Producer Identity and Key Identity

v1.0 has `source.producer`, `source.platform_id`, `source.sensor_id`, and policy
allowlists. This is not cryptographic identity.

Future trust semantics SHOULD distinguish:
- Producer identity.
- Platform identity.
- Sensor identity.
- Signing key identity.
- Certificate or trust-anchor identity.
- Software/runtime identity.
- Route or mesh path identity.

### 16.2 Event Signing

Future signing semantics SHOULD define:
- What is signed.
- Canonicalization rules.
- Signature algorithm.
- Signer key identity.
- Trust anchor.
- Signature timestamp.
- Signature failure behavior.
- Whether gateway-added export metadata is inside or outside the signed
  semantic event.

Signing MUST NOT change event meaning. Failed or missing signatures should be
policy-enforced through quarantine, warning, rejection, or trust downgrade.

### 16.3 Mesh Trust and Quarantine

Future mesh trust semantics SHOULD define:
- Trust score or trust label separate from confidence.
- Suspect event labels.
- Quarantined event handling.
- Replay detection.
- Source sequence counters or anti-replay windows.
- Impossible motion detection.
- Spoof suspicion.
- Spoof recovery.
- Route/path trust.

Quarantined events SHOULD remain auditable. Quarantine means a consumer does not
apply the event to operational state until policy releases it. It does not mean
the event is deleted or rewritten.

### 16.4 Replayed, Suspect, and Spoofed Events

Replay, spoof suspicion, and impossible motion are future labels or system
events. They MUST NOT be encoded as ordinary confidence changes alone. A
high-confidence but spoof-suspected event must remain distinguishable from a
low-confidence event.

Schema validity is not trust validity. A schema-valid event may still be
suspect, quarantined, replayed, or spoof-suspected under future trust policy.
SCHEMA_VIOLATION remains the v1.0 diagnostic envelope for schema and policy
validation outcomes and MUST NOT be reused as a generic trust/quarantine label.

## 17. UAS Identity and Behavioral Trust

This section is future extension guidance. It does not define v1.0 IFF.

UAS identity signals may include:
- Declared identity.
- Signed identity.
- Behavioral identity.
- RF signature identity.
- Acoustic signature identity.
- Thermal/EO signature identity.
- Operator-declared status.
- Coalition release or mission-specific identity labels.

These signals are claims or fused beliefs, not raw truth. They should be emitted
as INFERENCE_EVENT or FUSION_EVENT inputs and then projected to STATE_EVENT when
appropriate.

Future UAS status labels SHOULD be confidence labels, not absolute IFF:
- `FRIENDLY`
- `LIKELY_FRIENDLY`
- `UNKNOWN`
- `SUSPECT`
- `HOSTILE_INDICATED`

These labels must be paired with confidence, lineage, evidence type, and trust
context. ZMeta MUST NOT imply absolute friend/foe authority unless a future
deployment-specific policy and versioned semantics explicitly define it.

Remote ID, ADS-B, cooperative beacons, mission declarations, RF signatures,
acoustic signatures, thermal signatures, and behavior are evidence sources. They
are not standalone proof of friendly or hostile status.

## 18. Coalition Release and Cross-Domain Export

This section defines future semantic direction and policy guidance. It does not
create valid v1.0 release-label vocabulary unless adopted by a version branch.

### 18.1 Release Profiles

Future coalition semantics SHOULD distinguish:
- Internal profile.
- Trusted partner profile.
- Minimal partner profile.
- Public or untrusted export profile, if permitted.

Release profiles are not the same as bandwidth profiles L/M/H. A release
profile governs who may receive what. A bandwidth profile governs what can fit
over a link.

### 18.2 Redaction Projection

Redaction is a projection. It may remove fields, reduce precision, remove raw
data pointers, redact source identity, or collapse detail into approved summary
fields only if release policy allows it.

Redaction MUST NOT:
- Reinterpret meaning.
- Change units.
- Change track identity without a new event/projection rule.
- Increase confidence.
- Hide that redaction occurred when the consumer needs that fact.
- Mutate the original event.

### 18.3 Export Audit

Future cross-domain export metadata SHOULD include:
- Release label.
- Exporting authority.
- Guard or policy identifier.
- Redaction reason.
- Removed field categories.
- Export timestamp.
- Destination domain or partner class.
- Contract/policy hash when practical.

Export metadata should be enforced by policy and conformance tests, not by
adapters inventing one-off redaction semantics.

## 19. Data Nutrition Labels

Data nutrition labels are a future operator-facing summary concept. They are
not v1.0 required fields.

A data nutrition label summarizes why an operator should trust, question, or
ignore a state projection without exposing raw data. It should be derived from
ZMeta fields, lineage, policy, and local stores.

Future nutrition summaries may include:
- Source count.
- Modality count.
- Last observation age.
- Timing quality.
- Confidence.
- Lineage status.
- Profile.
- AI-generated status.
- Human-confirmed status.
- Fused status.
- Raw data available, referenced, absent, withheld, or redacted.
- Trust/quarantine status.
- Release/redaction status.

Nutrition labels must not become a substitute for lineage, confidence, or
trust. They are summaries, not semantic authorities.

## 20. Extension Registry and Namespace Governance

### 20.1 Reserved Names

Event types, event subtypes, system types, task types, observation modalities,
quality fields, trust fields, release fields, and lifecycle names are reserved
semantic vocabulary. Producers MUST NOT invent core-looking values without a
versioned extension contract.

### 20.2 Modality Feature Contracts

An observation modality is valid only when a schema and semantic feature
contract define:
- Required fields.
- Units.
- Optional fields.
- Prohibited fields.
- Timing/window behavior.
- Quality metadata.
- Layer boundaries.
- Conformance tests.

Reserved future modality candidates include RADAR, LIDAR, MAGNETIC, SEISMIC,
CYBER, and SIGINT. They are not valid v1.0 observation modalities.

### 20.3 Vendor Extension Namespaces

Vendor extensions SHOULD use collision-resistant namespaces, such as
`vendor.<name>` or another registry-approved prefix. Extensions must be safe to
ignore and must not override core fields.

Vendor extensions MUST NOT:
- Define hidden required semantics.
- Redefine units.
- Change event type or subtype meaning.
- Override confidence, trust, lineage, timing, profile, command safety, or
  authority boundaries.
- Create alternate track identity semantics.

### 20.4 Extension Adoption

Before extension adoption, define:
- Semantic contract text.
- Schema branch or policy-only rationale.
- Policy behavior.
- Adapter/gateway guidance.
- Encoding projection behavior.
- Conformance tests.
- Versioning and deprecation plan.

No extension becomes normative because an adapter emits it or a schema happens
to allow extra properties.

## 21. v1.1.0 Extension Semantics

This section governs experimental v1.1.0 extension vocabulary. It is valid only
when `zmeta_version: "1.1.0"` selects that branch.

### 21.1 Structured Quality Metadata

v1.1.0 formalizes `payload.quality` for observations and other payloads that
need machine-readable quality metadata.

Defined fields include:
- `measurement_error`: object with explicit `value`, `unit`, and `metric`.
- `snr_db`: signal-to-noise ratio in decibels.
- `calibration_state`: `CALIBRATED`, `UNCALIBRATED`, or `DEGRADED`.
- `geo_status`: `AVAILABLE`, `UNAVAILABLE`, `ESTIMATED`, `STALE`, or
  `CONFIGURED`.

Quality metadata never creates identity, classification, or track persistence.

### 21.2 Error Ellipse

v1.1.0 permits `geo.error_ellipse_m` when an event has geospatial uncertainty.

Rules:
- `semi_major` and `semi_minor` are meters.
- `orientation_deg` is degrees true north.
- `probability` declares the convention when known.
- Error ellipse does not change WGS-84/HAE conventions.

### 21.3 Data References

v1.1.0 formalizes:
- `payload.data_ref`
- `payload.data_refs`

Rules:
- Use exactly one pointer style per Observation payload.
- Each pointer requires `ref_id`.
- Pointer objects are metadata only.
- Hashes use `sha256:<64 hex chars>` when provided.
- `t_start` and `t_end` appear together.
- Consumers may ignore unresolved data references without changing event
  meaning.

### 21.4 Observation Modality Extensions

v1.1.0 defines feature contracts for RF, EO, IR, ACOUSTIC, and NETWORK.

EO observation features are raw image metadata only. Detected object boxes,
semantic labels, detector confidence, and class names belong in INFERENCE_EVENT.

ACOUSTIC observation features are measured signal facts only. Acoustic semantic
labels belong in INFERENCE_EVENT.

Reserved candidates such as RADAR, LIDAR, MAGNETIC, SEISMIC, CYBER, and SIGINT
remain invalid as OBSERVATION_EVENT modalities until their feature contracts are
defined.

### 21.5 SENSOR_STATUS

SENSOR_STATUS is a v1.1.0 SYSTEM_EVENT subtype for sensor health,
configuration, and capability state.

It reports sensor state only. It must not contain raw measurements, detections,
classifications, or track identity.

### 21.6 PLATFORM_STATUS

PLATFORM_STATUS is a v1.1.0 SYSTEM_EVENT subtype for platform health and
operating state.

It reports platform state only. It must not imply track position, command
acceptance, task execution, or link health.

### 21.7 Expanded Tasking

v1.1.0 may define additional COMMAND_EVENT task types only where task-specific
semantics are defined. All expanded tasking remains TTL-bound, idempotent,
deconflicted, altitude-prohibited, and executed out-of-band.

Defined v1.1.0 task types:
- `RETURN_TO_BASE`
- `LAND`
- `LOITER`
- `SCAN_RF`
- `TRACK_TARGET`
- `CHANGE_SENSOR_MODE`

Future task types MUST NOT be added without semantic definition and validation
contract.

## 22. Conformance Classes

Conformance classes define what an implementation claims to support. A product
may support more than one class.

| Class | Required Scope |
|---|---|
| ZMETA-CORE | v1.0 envelope, event types, subtype matching, UUIDv7, timestamps, units, confidence, lineage, and layer separation. |
| ZMETA-PROFILE-L | Profile L event-type constraints, unresolved lineage tolerance, explicit timing quality, short TTL/degraded confidence behavior, and compact Profile L compatibility when used. |
| ZMETA-PROFILE-M | Profile M event-type constraints, selective observation export, timing quality, and no inference export unless a future branch permits it. |
| ZMETA-PROFILE-H | Full fidelity v1.0 event support with all semantic layers preserved. |
| ZMETA-ADAPTER | Correct mapping from native formats to semantic layers, timestamp/unit normalization, UUIDv7 generation, lineage transform, rejection of ambiguous inputs, and external-boundary promotion evidence where applicable. |
| ZMETA-GATEWAY | Schema and policy validation, profile enforcement, source-field preservation, dedupe, timing status handling, risk adjudication labels, contract hash gates, and non-semantic projection behavior. |
| ZMETA-POLICY-ADJUDICATION | Tunable policy decisions using bounded actions, risk dimensions, governed reason codes, allowed/prohibited uses, effect labels, and diagnostic correlation. |
| ZMETA-EXTERNAL-PROMOTION | Enforcement of external projection promotion requirements for lossy tactical tracks, including promotion metadata, freshness, lineage status, confidence basis, trust reference, and loop/reflection status. |
| ZMETA-RISK-FILTERING | Consumer/filter behavior for accepted-risk data, including compact self-labels when diagnostics may not travel and enforcement of allowed/prohibited uses. |
| ZMETA-COT-PROJECTION | STATE_EVENT-only CoT/TAK egress projection plus CoT/TAK ingress treatment as external report evidence unless Section 4.5.1 promotion policy authorizes STATE_EVENT output. |
| ZMETA-PROJECTION-ORIGIN | Future projection instance/origin metadata for source event IDs, projection IDs, policy IDs, projection reasons, and same-event projection dedupe behavior. |
| ZMETA-AI-PROVENANCE | v1.0 model name/version, inference lineage, model confidence semantics, and future model provenance fields when adopted. |
| ZMETA-COALITION-EXPORT | Future release labels, redaction projection, export audit, and cross-domain conformance once a version branch adopts them. |
| ZMETA-MESH-TRUST | Future signing, key identity, route trust, quarantine, spoof suspicion, and trust/confidence separation once adopted. |
| ZMETA-REPLAY | Replay/simulation labels, event-time vs wall-clock projection semantics, and replay-safe display/export behavior once adopted. |

Conformance claims must name the contract version, schema version, policy pack
or profile, and encoding/projection mappings used.

## 23. Implementation Mapping

| Rule / Concept | JSON Schema | Policy Pack | Adapter/Gateway | Encoding Projection | Conformance Test | Documentation Only |
|---|---|---|---|---|---|---|
| Completeness without exhaustiveness | No | Must not use local policy to redefine core semantics | Must keep mission-specific mapping outside the core kernel | No independent role | Bad-event, adapter, registry, and class evidence protect boundaries | Yes |
| Core semantic change threshold | No | No runtime role | No runtime role | No independent role | Release/audit governance evidence only | Yes |
| Exact `zmeta_version` selection | Required | Validates selected policy context | Uses canonical schema | Decodes before validation | Required | No |
| UUIDv7 event identity | Required | Optional diagnostics | Generates at boundaries | Preserves value | Required | No |
| Append-only immutability | Partial | Partial | Required | Preserves fields | Required for gateways/adapters | No |
| Event type/subtype vocabulary | Required | Optional | Required | Preserves fields | Required | No |
| Subtype/payload discriminator match | Required | Optional | Required | Preserves fields | Required | No |
| Layer separation | Partial | Required for context checks | Required | No independent role | Required | No |
| Producer authority | No | Required | Required | No | Required | No |
| Risk adjudication actions | No | Required | Required for diagnostics/effects | Preserves labels | Required | No |
| Policy decision diagnostics | SCHEMA_VIOLATION v1.0 envelope | Required reason/use/effect fields | Emits warnings/rejections | Preserves metrics | Required | No |
| Allowed/prohibited uses | No | Required where soft acceptance is used | Required for filters/routes | Preserves labels | Required | No |
| Compact self-label behavior | Extension object allowed where schema permits | Required for material risk crossing boundaries | Required when diagnostics may not travel | Preserves extension labels | Required | No |
| Operator override semantics | No current event vocabulary | Required for local override policy | Must not bypass locked rules | Preserves labels if present | Future/current policy tests | Guidance plus future audit events |
| Timing format | Required | Optional | Normalizes | Preserves/expands | Required | No |
| Timing freshness | No | Required | Required when stateful | No | Required | No |
| PNT integrity labels | Future | Future | Future | Future | Future | Current guidance only |
| Units/geodesy | Partial | Optional | Required | Preserves/expands | Required for adapters | No |
| Confidence required/prohibited | Required | Optional | Required | Preserves | Required | No |
| Confidence degradation/caps | No | Required where configured | Required where projecting/degrading | No | Required when policy exists | No |
| Trust score | Future | Future | Future | Future | Future | Current guidance only |
| Mandatory lineage | Required for I/F/S | Required for context checks | Required | Preserves | Required | No |
| Raw-data-absent status | Future | Future | Future | Future | Future | Current guidance only |
| Profile event-type compatibility | Required when `profile` present | Required at runtime | Required | Compact supports L | Required | No |
| Emergency/L0 profile or projection policy | Future | Future | Future | Future | Future | Current guidance only |
| Command safety | Required | Required | Required | Preserves | Required | No |
| TASK_ACK lifecycle | Required | Required | Required | Compact maps common values | Required | No |
| Track lifecycle machine events | Future | Future | Future | Future | Future | Current v1.0 guidance |
| CoT/TAK projection boundary | No | Optional | Required | No | Required for projection class | No |
| External projection promotion | No | Required | Required for CoT/JREAP/MAVLink ingress state | Preserves labels | Required | No |
| Loop/reflection status | No | Required for external promotion | Required at promotion boundary | Preserves labels | Required | No |
| AI model name/version | Required for inference | Optional | Required | Preserves | Required | No |
| Model/runtime provenance | Future | Future | Future | Future | Future | Current guidance only |
| Mesh signing/quarantine | Future | Future | Future | Future | Future | Current guidance only |
| Coalition release/redaction | Future | Future | Future | Future | Future | Current guidance only |
| Projection/thinning metadata | Future | Future | Future | Future | Future | Current guidance only |
| Projection origin/instance identity | Future | Future | Future | Future | Future | Current guidance only |
| Extension namespace safety | Partial | Optional | Required | Preserves | Required for extension adoption | No |
| Future-extension non-claimability | Required through version/subtype rejection | Must not treat future terms as current authority | Must not emit or promote reserved terms as current vocabulary | Decodes before validation | Extension registry and conformance-class validators | No |
| Data nutrition labels | Future | Future | Future UI/projection | No | Future | Current guidance only |

## 24. Change Log / Semantic Delta

### 24.1 Clarified

- The semantic contract is the authority; schema, policy, adapters, gateways,
  encodings, examples, and conformance tests are implementation surfaces.
- ZMeta is complete enough to prevent semantic corruption without becoming an
  exhaustive mission ontology.
- v1.0 remains locked and normative.
- v1.1.0 is an experimental compatibility extension branch and does not loosen
  v1.0 invariants.
- Version aliases must be normalized before validation and are not canonical
  schema values.
- Confidence is not truth and is separate from observation quality.
- Trust, if introduced, is separate from confidence.
- Raw data absence is not a validation failure by itself.
- Profile thinning is projection, not reinterpretation.
- CoT/TAK projection is STATE_EVENT-only in v1.0.
- CoT/TAK ingress is external report evidence unless active promotion policy
  authorizes `STATE_EVENT` promotion under Section 4.5.1.
- SCHEMA_VIOLATION is the v1.0 compatibility envelope for schema and policy
  diagnostics, not the ideal long-term name for policy adjudication.
- Extension adoption requires semantic text, schema/policy behavior, adapter
  guidance, encoding handling, and conformance tests.

### 24.2 Added

- Explicit version semantics and compatibility expectations.
- Enforcement model for schema, policy, adapter/gateway, encoding, and
  conformance surfaces.
- Confidence, uncertainty, and trust section.
- AI provenance and model-runtime guidance.
- Raw-data-absent mode guidance.
- Risk adjudication and operator-tunable policy.
- Completeness without exhaustiveness as a kernel-protection doctrine.
- Core semantic change threshold for future contract edits.
- Locked, tunable, advisory, and future-extension rule classes.
- Bounded policy actions: reject, warn, degrade, quarantine, and scoped ignore.
- Allowed/prohibited use labels for accepted-risk data.
- External projection promotion requirements for lossy tactical-track ingress.
- Soft policy decisions through diagnostics and compact self-labels.
- Operator override constraints for material policy softening.
- Compute elasticity and emergency compute guidance.
- Emergency/L0 thinning and projection-policy candidate guidance.
- Mesh trust, signing, spoof suspicion, and quarantine future guidance.
- UAS identity and behavioral trust future guidance.
- Coalition release and cross-domain export future guidance.
- Projection and thinning metadata future guidance.
- Data nutrition label future concept.
- Extension registry and namespace governance.
- Conformance class definitions.
- Implementation mapping matrix.

### 24.3 Preserved

This rewrite preserves all locked v1.0 invariants from the previous contract,
including:
- Event-based worldview.
- Append-only immutability.
- UUIDv7 event identity.
- Layer separation.
- Authority boundaries.
- Transport non-semantics.
- Profile thinning without reinterpretation.
- Mandatory lineage.
- Explicit uncertainty.
- Timing quality.
- Units/geodesy.
- v1.0 envelope and payload contracts.
- Profile L/M/H behavior.
- Command/tasking governance.
- Track persistence and deduplication.
- Edge degradation invariants.

### 24.4 Future Work

The following MUST NOT be implemented as valid event vocabulary until a version
branch, schema, policy, and conformance tests are approved:
- Trust score fields.
- Event signatures and key identity fields.
- Mesh route trust and quarantine fields.
- UAS identity/IFF-like labels.
- Coalition release labels and redaction metadata.
- Emergency/L0 profile or emergency projection-policy vocabulary.
- Track lifecycle event subtypes beyond v1.0 guidance.
- Projection/thinning metadata fields.
- Projection origin/instance metadata for dedupe and store reconciliation.
- Data nutrition labels.
- Confidence decomposition fields.
- Full model/runtime provenance fields.
- MODEL_STATUS, ASSURANCE_EVENT, PNT_STATUS, or equivalent governed status
  subtypes.
- OBSERVATION_EVENT/NETWORK_REPORT or equivalent external-report evidence
  subtype.
- SYSTEM_EVENT/POLICY_ADJUDICATION or equivalent clearer policy diagnostic
  subtype.
- Replay/red-team/synthetic labels.
- Future machine-readable extension registry field expansions beyond the
  current registry contract.

## Appendix A. Data Reference Convention

Some deployments retain raw data locally or in upstream stores for AAR,
reprocessing, or vectorization. To link lightweight ZMeta events to those
datasets without inflating payloads, use optional observation payload pointers.

Recommended pointer fields:
- `ref_id`: unique within the referenced store.
- `store`: local, gateway cache, object store, or other storage namespace.
- `kind`: `RAW`, `VECTOR`, or `FILE`.
- `format`: artifact format such as `iq`, `wav`, `mp4`, `pcap`, or `npy`.
- `hash`: content hash, preferably SHA-256.
- `size_bytes`: artifact size.
- `t_start`: artifact window start.
- `t_end`: artifact window end.

Data references do not replace lineage and must not carry raw payload data.

## Appendix B. Confidence Computation Guidance

This appendix is non-normative guidance. Producers should document their chosen
formula in operational runbooks.

Input aggregation:

```text
confidence = min(input_confidences) * aggregation_factor
```

Timing degradation:

```text
timing_factor = max(0.0, 1.0 - (est_error_ms / sync_threshold_ms))
confidence_with_timing = base_confidence * timing_factor
```

Profile and precision:

```text
profile_precision_factor = 0.8
confidence_with_profile = base_confidence * profile_precision_factor
```

Only apply a profile factor when quantization or omitted context materially
reduces use safety.

Freshness:

```text
age_ms = now_ts - oldest_input_ts
freshness_factor = max(0.0, 1.0 - (age_ms / max_age_ms))
confidence_with_freshness = base_confidence * freshness_factor
```

Recommended complete form:

```text
confidence =
  min(input_confidences)
  * aggregation_factor
  * timing_factor
  * profile_precision_factor
  * freshness_factor

confidence = clip(confidence, 0.0, 1.0)
```
