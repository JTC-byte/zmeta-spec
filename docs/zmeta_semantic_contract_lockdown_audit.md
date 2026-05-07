# ZMeta Semantic Contract Lockdown Audit

Date: 2026-05-07

Status: audit-only. This document proposes contract refinements but does not
modify the semantic contract, schemas, adapters, protobuf files, compact binary
mappings, validators, policy packs, examples, or tests.

Primary source reviewed:
- `spec/semantics-contract.md`

Supporting sources reviewed:
- `README.md`
- `spec/README.md`
- `spec/versioning.md`
- `spec/profile-compatibility.md`
- `spec/field-dictionary.md`
- `spec/compact-binary-mapping.md`
- `spec/protobuf-encoding.md`
- `schema/README.md`
- `schema/zmeta-event.schema.json`
- `schema/zmeta-event-1.0.schema.json`
- `schema/zmeta-event-1.1.0.schema.json`
- `schema/proto/zmeta_event_v1.proto`
- `policy/*.yaml`
- `configs/policy-variants/*.yaml`
- `examples/README.md`
- `conformance/README.md`
- `conformance/must-pass.jsonl`
- `conformance/must-fail.jsonl`
- `gateway/README.md`
- `gateway/src/validators.py`
- `gateway/tests/*`
- `adapters/README.md`
- Selected ingress and egress adapter docs/templates, including CoT, MAVLink,
  EO-CV, KrakenSDR, JREAP, and the ingress adapter template.

## A. Current Contract Summary

The current semantic contract is strong and already establishes the most
important v1.0 foundation: ZMeta is a semantic event system, not a transport,
object store, or C2 replacement. `README.md` and
`spec/semantics-contract.md` both describe ZMeta as transport-agnostic,
event-based, uncertainty-aware metadata for resilient ISR.

Current locked semantic foundations:

| Foundation | Current Contract Position | Source Trace |
|---|---|---|
| Event-based worldview | ZMeta represents events, not mutable objects or sensor state. Each message describes something that happened at a specific time. | `spec/semantics-contract.md` Section 1.1 |
| Append-only immutability | Events are never modified or deleted. Corrections, refinements, and reinterpretations require new events with lineage. Export projections may omit optional fields or conservatively reduce confidence/TTL while preserving `event_id`. | `spec/semantics-contract.md` Section 1.2 |
| UUIDv7 event identity | `event.event_id`, lineage references, and fusion members use UUIDv7. Legacy IDs must be regenerated at adapter boundaries and preserved in payload-scoped provenance when needed. | `spec/semantics-contract.md` Section 1.3; `schema/README.md` UUIDv7 section |
| Layer separation | Observation, inference, fusion, and state are separate semantic layers: facts, opinions, provisional continuity, and operator-facing current belief. | `spec/semantics-contract.md` Section 1.4 |
| Authority boundaries | Sensors produce observations, AI/analytics produce inferences, fusion nodes create track identity, operator interfaces do not author or mutate ZMeta events, and command/tasking requires a command-authorized or deconfliction producer. | `spec/semantics-contract.md` Sections 1.5, 1.10, 1.11 |
| Transport non-semantics | Transport choices affect rate, density, and precision but never interpretation. | `spec/semantics-contract.md` Section 1.6; `spec/profile-compatibility.md` Encoding Compatibility |
| Profile thinning without reinterpretation | Profiles L/M/H may omit optional fields, reduce precision, and reduce update rate, but may not rename fields, change units, change meaning, or introduce implicit defaults. | `spec/semantics-contract.md` Sections 1.7 and 4.9 |
| Mandatory lineage | Lineage is required for inference, fusion, and state. Envelope lineage is authoritative; payload-local references must be equal to or a subset of envelope lineage. | `spec/semantics-contract.md` Sections 1.8 and 5.4; `policy/lineage.yaml` |
| Explicit uncertainty | Confidence is required for inference/fusion/state and prohibited for observation/command/system. Observation quality belongs in payload quality metadata. Timing uncertainty is exposed through timing quality. | `spec/semantics-contract.md` Sections 1.9, 2.3, 4.1, Appendix B |
| Bounded command/tasking governance | COMMAND_EVENT is narrow, TTL-bound, idempotent by `task_id`, altitude-prohibited, and must route through deconfliction/out-of-band execution. | `spec/semantics-contract.md` Sections 1.10, 1.11, 4.7, 5.2 |
| Vendor extensibility rules | Vendors may extend payloads within their domain, but may not alter envelopes, redefine core fields, collapse layers, or make extensions non-ignorable. | `spec/semantics-contract.md` Section 1.12; `README.md` Adapters |
| Timing quality | `event.ts` is observation/capture/validity time. Timing quality is mandatory per event or via TIME_STATUS. `est_error_ms` is worst-case absolute timestamp error. | `spec/semantics-contract.md` Section 2; `policy/timing-freshness.yaml` |
| Units/geodesy | WGS-84 decimal degrees, HAE meters, meters/second, true-north degrees, Hertz, dBm, UTC-Z timestamps, and explicit unit fields are required. Unit inference is forbidden. | `spec/semantics-contract.md` Section 3 |
| v1.0 schema structure | v1.0 envelope, event types, payload discriminators, profile compatibility, confidence/lineage rules, UUIDv7, and field-level constraints are encoded in `schema/zmeta-event-1.0.schema.json`. | `spec/semantics-contract.md` Section 4; `schema/zmeta-event-1.0.schema.json` |
| Profile L/M/H behavior | Profile L carries STATE/SYSTEM/COMMAND; Profile M carries STATE/FUSION/SYSTEM/COMMAND/selected OBSERVATION; Profile H carries all event types. | `spec/semantics-contract.md` Section 4.9; `policy/profiles.yaml` |

Overall, the current contract does well at preventing the two major failure
modes that would damage ZMeta: semantic layer collapse and transport/profile
reinterpretation. It also correctly keeps v1.1.0 vocabulary behind explicit
version selection rather than allowing v1.1-only concepts to validate as v1.0.

## B. Normative vs Non-Normative Classification

Classification terms:
- v1.0 normative invariant: rule that defines ZMeta meaning and must not be weakened.
- v1.0 schema-enforced rule: rule currently enforced by JSON Schema.
- v1.0 policy-enforced rule: rule currently enforced by active policy YAML and reference validators.
- v1.0 adapter/gateway implementation guidance: expected implementation behavior, not the semantic authority.
- v1.1+ extension candidate: proposed or experimental vocabulary outside locked v1.0.
- non-normative explanation: rationale, operating guidance, or explanatory text.
- example only: illustrative sample, not a rule.

| Contract Section | Classification | Notes / Source Trace |
|---|---|---|
| Status and purpose | v1.0 normative invariant | Declares the semantic contract as the governing foundation for schema, policy, gateway, adapters, and conformance. |
| 0. Operating Model | non-normative explanation | Explicitly marked non-normative. Useful north-star material, but not independently enforceable. |
| 1. Core Semantic Contract | v1.0 normative invariant | Explicitly locked and non-negotiable. |
| 1.1 Event-Based Worldview | v1.0 normative invariant | Partially schema-reflected through event envelope/event_type, but the worldview is semantic. |
| 1.2 Append-Only Immutability | v1.0 normative invariant; v1.0 adapter/gateway implementation guidance | Immutability cannot be fully enforced on a single JSON document. Gateway/adapters must preserve source-authored fields. |
| 1.3 Event Identity | v1.0 normative invariant; v1.0 schema-enforced rule; v1.0 adapter/gateway implementation guidance | UUIDv7 pattern is schema-enforced. Regeneration/preservation of legacy IDs is adapter guidance. |
| 1.4 Layer Separation | v1.0 normative invariant; v1.0 schema-enforced rule; v1.0 policy-enforced rule | Schema blocks several layer-crossing fields; policy and validators add forbidden-field checks. |
| 1.5 Authority Boundaries | v1.0 normative invariant; v1.0 policy-enforced rule | JSON Schema remains portable; `policy/producer-authority.yaml`, `policy/roles.yaml`, and `policy/routing.yaml` enforce deployment authority. |
| 1.6 Transport Is Non-Semantic | v1.0 normative invariant; v1.0 adapter/gateway implementation guidance | Encoding specs repeat that decoded events must validate normally. |
| 1.7 Profiles Thin Data | v1.0 normative invariant; v1.0 schema-enforced rule; v1.0 policy-enforced rule | Schema/policy enforce allowed event types by profile; semantic no-reinterpretation remains mostly implementation/conformance-driven. |
| 1.8 Mandatory Lineage | v1.0 normative invariant; v1.0 schema-enforced rule; v1.0 policy-enforced rule | Schema requires lineage for INFERENCE/FUSION/STATE; policy validates subset and parent-type consistency where state exists. |
| 1.9 Explicit Uncertainty | v1.0 normative invariant; v1.0 schema-enforced rule; v1.0 policy-enforced rule | Confidence presence/prohibition is schema-enforced; timing exposure is policy/gateway-enforced. |
| 1.10 Telemetry-First Tasking | v1.0 normative invariant; v1.0 adapter/gateway implementation guidance | Scope and routing are semantic; actual command translation/deconfliction is adapter/gateway behavior. |
| 1.11 Tasking Governance | v1.0 normative invariant; v1.0 schema-enforced rule; v1.0 policy-enforced rule | Command shapes, TTL, deconfliction boolean, and altitude prohibition are schema/policy-covered. |
| 1.12 Vendor Extensibility Rules | v1.0 normative invariant; v1.0 schema-enforced rule; v1.0 adapter/gateway implementation guidance | Top-level and many sub-objects are strict; payloads often preserve `additionalProperties: true`, so extension safety needs policy/conformance guidance. |
| 2. Time Synchronization Contract | v1.0 normative invariant; v1.0 schema-enforced rule; v1.0 policy-enforced rule | UTC-Z, TIME_STATUS shape, timing_quality shape, RF midpoint checks, stale/missing timing behavior are distributed across schema and policy validators. |
| 2.1 Definition of `ts` | v1.0 normative invariant | Schema enforces format, not semantic source of time. |
| 2.2 Capture vs Publish vs Receive | v1.0 normative invariant; v1.0 adapter/gateway implementation guidance | Gateway stamping behavior is reference implementation behavior. |
| 2.3 Timing Quality Metadata | v1.0 normative invariant; v1.0 schema-enforced rule; v1.0 policy-enforced rule | Required fields and periodic TIME_STATUS freshness policy are present. |
| 2.4 Worst-Case Error | v1.0 normative invariant | Cannot be structurally verified beyond field presence/range. |
| 2.5 Minimum Sync Approaches | non-normative explanation; policy-enforced only if deployment adopts thresholds | Gold/Silver/Bronze expectations are guidance unless bound in policy. |
| 2.6 Windowed Observations | v1.0 normative invariant; v1.0 schema-enforced rule; v1.0 policy-enforced rule | Pairing is schema-enforced; midpoint tolerance is semantic validator/policy. |
| 2.7 Holdover and Drift | v1.0 normative invariant; v1.0 policy-enforced rule | Monotonic holdover error is policy warning by default. |
| 2.8 Degraded Timing | v1.0 normative invariant; policy-pack-only rule | Requires confidence degradation/gating, but exact caps are policy/deployment. |
| 2.9 Profile Timing Considerations | v1.0 normative invariant; v1.0 policy-enforced rule | Per-profile freshness and mandatory `est_error_ms` are policy-backed. |
| 3. Units & Geodesy | v1.0 normative invariant; v1.0 schema-enforced rule | Ranges/strict `geo` objects are schema-enforced; unit correctness of free-form extension fields is not fully enforceable. |
| 3.1 Coordinate Reference System | v1.0 normative invariant; partially schema-enforced | Lat/lon range enforced. Datum is semantic. |
| 3.2 Altitude Reference | v1.0 normative invariant; partially schema-enforced | `alt_m` shape enforced. HAE meaning is semantic. |
| 3.3 Velocity and Motion | v1.0 normative invariant; schema-enforced for known scalar fields | Non-negative scalar speeds are schema-covered in known payloads. |
| 3.4 Bearings, Angles, Orientation | v1.0 normative invariant; schema-enforced for known fields | 0-360 headings/bearings are schema-covered in known payloads. |
| 3.5 Distance and Range | v1.0 normative invariant; partially schema-enforced | Known fields use `_m`; extensions need namespace/units governance. |
| 3.6 RF Units | v1.0 normative invariant; partially schema-enforced | RF feature names imply Hz/dBm; v1.0 RF required fields are schema-covered. |
| 3.7 Time Units | v1.0 normative invariant; v1.0 schema-enforced rule | UTC-Z timestamp pattern is schema-enforced. |
| 3.8 Unit Inference Forbidden | v1.0 normative invariant | Requires adapter/conformance enforcement for extension fields. |
| 3.9 Degraded/Partial Geo | v1.0 normative invariant; v1.0 schema-enforced rule | `geo` is all-or-nothing by schema; confidence/quality reflection is semantic/policy. |
| 4. ZMeta v1.0 Schema | v1.0 normative invariant; v1.0 schema-enforced rule | Contract embeds canonical schema semantics. |
| 4.1 Canonical Envelope | v1.0 normative invariant; v1.0 schema-enforced rule | Top-level required fields, confidence/lineage by event type, and strict envelope are schema-enforced. |
| 4.2 Event Types and Subtypes | v1.0 normative invariant; v1.0 schema-enforced rule | Event type enum and subtype/payload discriminator matching are schema-enforced. |
| 4.3 OBSERVATION_EVENT | v1.0 normative invariant; v1.0 schema-enforced rule; v1.0 policy-enforced rule | Required modality/features, RF minimum fields, and forbidden identity/classification fields are covered. |
| 4.4 INFERENCE_EVENT | v1.0 normative invariant; v1.0 schema-enforced rule; v1.0 policy-enforced rule | Model `{name, version}`, based_on, confidence, and no `track_id` are covered. Deeper model-card provenance is absent. |
| 4.5 FUSION_EVENT | v1.0 normative invariant; v1.0 schema-enforced rule; v1.0 policy-enforced rule | Track ID, members, stability, last_seen, lineage; global non-reuse remains semantic. |
| 4.6 STATE_EVENT | v1.0 normative invariant; v1.0 schema-enforced rule; v1.0 adapter/gateway implementation guidance | Operator projection point and raw-feature prohibition are covered; CoT/JREAP mapping details are reference. |
| 4.7 COMMAND_EVENT | v1.0 normative invariant; v1.0 schema-enforced rule; v1.0 policy-enforced rule | Narrow v1.0 task set, geometry rules, TTL, idempotency, deconfliction, and altitude prohibition are covered. |
| 4.8 SYSTEM_EVENT | v1.0 normative invariant; v1.0 schema-enforced rule; v1.0 policy-enforced rule | TIME_STATUS, LINK_STATUS, SCHEMA_VIOLATION, and TASK_ACK are covered. Operational degradation events are deferred. |
| 4.9 Profile Compliance | v1.0 normative invariant; v1.0 schema-enforced rule; v1.0 policy-enforced rule | Event-type/profile compatibility is covered. Byte budgets/rate shaping are implementation. |
| 4A. v1.1.0 Extension Semantics | v1.1+ extension candidate; v1.0 normative guardrail | Explicitly version-selected and must not loosen v1.0 invariants. |
| 4A.1 Structured Quality Metadata | v1.1+ extension candidate; schema-enforced in v1.1.0 | Candidate foundation for richer uncertainty, but not v1.0. |
| 4A.2 Error Ellipse | v1.1+ extension candidate; schema-enforced in v1.1.0 | Useful for CoT uncertainty projection; not v1.0. |
| 4A.3 Data References | v1.1+ extension candidate; schema-enforced in v1.1.0; informative in v1.0 appendix | v1.0 schema currently permits data_ref, but contract treats formal semantics as v1.1.0. |
| 4A.4 Observation Modality Extensions | v1.1+ extension candidate; schema-enforced in v1.1.0 | Defines extension governance pattern for modalities. |
| 4A.5 SENSOR_STATUS | v1.1+ extension candidate; schema-enforced in v1.1.0 | Needed for health/capability state, not v1.0. |
| 4A.6 PLATFORM_STATUS | v1.1+ extension candidate; schema-enforced in v1.1.0 | Needed for platform availability/power/compute state, not v1.0. |
| 4A.7 Expanded Tasking | v1.1+ extension candidate; schema-enforced in v1.1.0 | Explicitly remains bounded, deconflicted, altitude-prohibited. |
| 5. Track Persistence and Deduplication | v1.0 normative invariant; v1.0 policy-enforced rule; v1.0 adapter/gateway implementation guidance | Dedup cache, lineage continuity, and lifecycle guidance exist; lifecycle states are not machine-readable events in v1.0. |
| 5.1 Track ID | v1.0 normative invariant | Schema checks presence; global uniqueness/non-reuse need policy/store/conformance. |
| 5.2 Deduplication Rules | v1.0 normative invariant; v1.0 gateway implementation guidance | Reference gateway implements command/TASK_ACK dedupe. Event dedupe is consumer state behavior. |
| 5.3 Track Lifecycle and Revisability | v1.0 normative invariant; v1.1+ extension candidate | Merge/split/lost are described but not dedicated machine-readable event types. |
| 5.4 Lineage-Based Continuity | v1.0 normative invariant; v1.0 policy-enforced rule | Parent-type validation and unresolved-parent policy exist. |
| 5.5 Track Persistence Across Profiles | v1.0 normative invariant; v1.0 adapter/gateway implementation guidance | Preserving `track_id` across profiles is semantic; enrichment behavior is implementation. |
| 6. Edge Operator Failure Mode Configuration | v1.0 normative invariant; policy-pack-only rule; adapter/gateway implementation guidance | Degradation defaults are specified, but current policy mostly covers timing/link/command/lineage, not all failure modes. |
| 6.1 Default Failure Mode Behavior | v1.0 normative invariant; policy-pack-only rule | Many rows are currently guidance unless implemented in deployment config/policy. |
| 6.2 User Configurable Profile Example | example only | Illustrative JSON config. |
| 6.3 Semantic Invariants Under Degradation | v1.0 normative invariant | Reasserts no reinterpretation, uncertainty, auditability, immutability, lineage. |
| 6.4 Recommended Operational Practices | non-normative explanation | Monitoring/testing/escalation recommendations. |
| Appendix A Data Reference Convention | non-normative explanation; v1.1+ extension candidate | Explicitly informative and optional; formalized in v1.1.0. |
| Appendix B Confidence Computation | non-normative explanation | Provides formulas but does not normatively bind producers. |

## C. Enforcement Surface Matrix

| Semantic Rule | Why It Matters | Enforced By JSON Schema? | Enforced By Policy Pack? | Enforced By Adapter/Gateway? | Enforced By Encoding Layer? | Enforced By Conformance Tests? | Current Gap / Risk |
|---|---|---|---|---|---|---|---|
| Exact version selection | Prevents v1.1.0 vocabulary from becoming valid v1.0 by accident. | Yes, canonical `oneOf` dispatch and version-specific consts. | Indirectly through validation. | Yes, validators use canonical schema. | No, encodings decode to JSON first. | Yes, version-discrimination tests and must-fail cases. | Compatibility normalizers must remain clearly non-normative. |
| UUIDv7 event identity | Enables sortable identity, lineage, dedupe, and replay audit. | Yes for `event_id`, lineage, members. | Indirectly. | Adapters generate UUIDv7. | Compact maps UUID bytes; protobuf keeps string. | Yes in schema tests. | Legacy ID preservation fields are not fully standardized. |
| Append-only immutability | Prevents gateways/adapters from rewriting meaning. | No, single-event validation cannot prove history. | Partial, through contract hash and validator behavior. | Partial, gateway stamping preserves source semantics; compat normalizer refuses immutable rewrites. | No. | Partial. | Needs conformance class or mutation/reprojection tests for adapters/gateways. |
| Observation/inference/fusion/state separation | Prevents facts, model claims, tracks, and operator state from collapsing. | Yes for many forbidden fields and discriminators. | Yes for forbidden-field semantic checks. | Yes in adapter rules. | No. | Yes, must-fail cases and gateway tests. | Free-form payload extensions can still carry semantic reinterpretation unless namespace rules are tightened. |
| Producer authority boundaries | Ensures only authorized logical functions emit specific event types. | No, schema is deployment-portable. | Yes, `roles.yaml`, `producer-authority.yaml`, `routing.yaml`. | Yes, gateway validators. | No. | Yes, producer authority tests. | Producer identity is string-pattern based; key identity/signing is not defined. |
| Transport non-semantics | Preserves meaning across LTE, IP radio, LoRa, CBOR, protobuf, and CoT/JREAP projection. | No. | No direct enforcement. | Partial, encoding converters decode to canonical JSON before validation. | Partial, specs require semantic equivalence. | Roundtrip tests cover encodings. | Need canonical equivalence conformance for every stable encoding and adapter projection. |
| Profile L/M/H event-type compatibility | Prevents Profile L from carrying raw observations or inference payloads. | Yes when `profile` is present. | Yes, active profile validation rejects disallowed event types. | Yes in gateway validation. | Compact only maps Profile L-supported payloads. | Yes, profile must-fail cases. | If `profile` is omitted, schema does not apply profile export restrictions; gateway profile must be authoritative at runtime. |
| Profile thinning without reinterpretation | Allows bandwidth reduction without semantic drift. | Partial, event-type profile constraints only. | Partial. | Partial, gateway/projection behavior. | Compact mapping omits/encodes fields but must expand back. | Partial through examples/size tests. | Need explicit projection conformance: same `event_id`, no semantic field rewrite, no confidence increase. |
| Mandatory lineage for inference/fusion/state | Enables audit, AAR, trust assessment, and reconstruction. | Yes. | Yes, subset/parent-type/unresolved checks. | Yes when gateway has local state. | Compact/protobuf carry lineage. | Yes, lineage tests. | Profile L unresolved parent semantics are well stated but trust impact is not defined. |
| Confidence required/prohibited by event type | Prevents observations from pretending to be beliefs and requires uncertainty for derived state. | Yes. | Indirectly. | Yes via validation. | Encodings preserve when present. | Yes. | Confidence decomposition and distinction from trust are underdeveloped. |
| Timing quality mandatory | Required for RF fusion, replay, and time-correlated state. | Shape is schema-enforced where present; TIME_STATUS shape is enforced. | Yes, missing/stale timing policy. | Yes, gateway stateful validation and adapter fallback timing. | Encodings carry timing as payload JSON or compact fields. | Yes, timing tests and must-fail cases. | Degraded timing confidence caps are policy/config guidance, not complete semantic vocabulary. |
| `event.ts` as capture/observation/validity time | Keeps replay, freshness, and fusion deterministic. | Format only. | RF midpoint policy partially. | Adapter timestamp normalization. | Encodings preserve timestamp values. | Partial. | Cannot prove source clock semantics structurally; adapter conformance needed. |
| UTC-Z timestamps only | Avoids timezone ambiguity. | Yes. | Indirectly. | Adapters normalize. | Compact uses epoch ms and expands to UTC-Z. | Yes. | Need equivalent tests for every adapter output. |
| Units/geodesy | Prevents cross-domain unit errors. | Partial for known fields/ranges and strict geo. | Partial through semantic validators. | Adapter template requires conversion. | No. | Partial. | Extension fields with units are not centrally registered or linted. |
| RF observation window midpoint | Enables coherent RF correlation. | Pairing yes; midpoint no. | Yes, `rf_window_midpoint_tolerance_ms`. | Yes in validators. | No. | Yes. | Applies to RF only; window semantics for EO/acoustic/network are not fully defined. |
| v1.0 event subtype/payload discriminator match | Prevents decorative or adapter-specific subtypes. | Yes. | Indirectly. | Yes through validation. | No. | Yes. | Extension namespace rules should be formalized for vendors. |
| Command TTL/idempotency/deconfliction | Prevents unsafe duplicate or undeconflicted mission tasking. | Yes for shape and `requires_deconfliction: true`. | Yes for command routing and duplicate logic. | Yes, reference gateway dedupes `task_id` and emits TASK_ACK. | Compact supports command payload. | Yes. | Deconfliction authority, approval evidence, and operator override semantics are not fully represented. |
| Command altitude prohibition | Keeps vertical deconfliction outside ZMeta tasking. | Yes at payload/geometry/extensions first level. | Yes via semantic validator. | Yes. | No. | Yes. | Deep nested extension semantics remain a risk if vendors hide altitude intent under namespaced structures. |
| TASK_ACK lifecycle | Provides command auditability and dedupe. | Yes for states, metrics, reason codes. | Yes. | Yes, gateway emits duplicate TASK_ACK. | Compact maps TASK_ACK states. | Yes. | Does not encode operator approval chain or deconfliction proof. |
| LINK_STATUS health | Supports transport diagnostics without making transport semantic. | Yes for required metrics/states/reason codes. | Yes. | Yes. | Compact maps common states. | Yes. | Mesh route/trust/quarantine states are not defined. |
| SCHEMA_VIOLATION diagnostics | Makes rejected/malformed events auditable. | Yes. | Yes. | Yes. | Compact maps subtype. | Yes. | Operational degradation must not use SCHEMA_VIOLATION, leaving gaps until dedicated status/lifecycle events are defined. |
| Track ID persistence and non-reuse | Prevents ambiguous state continuity. | Presence only. | Partial through lineage validation. | Consumer/fusion responsibility. | Encodings preserve field. | Partial. | No machine-readable retirement/merge/split events in v1.0; global non-reuse requires event store. |
| Data references | Links lightweight events to retained artifacts without carrying raw data. | v1.1.0 formalized; v1.0 permissive/informative. | Partial. | Adapter guidance. | Protobuf payload JSON carries them; compact advises omitting for L. | v1.1.0 examples/tests. | v1.0/v1.1 boundary is potentially confusing because v1.0 schema allows `data_ref` while Appendix A is informative. |
| Structured quality and error ellipse | Supports uncertainty projection and sensor quality. | v1.1.0 only. | Partial through schema invalid cases. | CoT egress uses error ellipse. | Payload JSON/proto; compact L does not define these. | v1.1.0 examples/tests. | Needed for future contract hardening but not locked in v1.0. |
| Encoding semantic equivalence | Avoids encoding becoming a competing semantic contract. | Decoded JSON must validate. | Indirectly. | Conversion tools and gateway decoders enforce. | Specs state equivalence; compact/proto are projections only. | Roundtrip tests. | Protobuf field numbers are experimental; compact enum extension governance needs versioned conformance. |
| CoT/TAK projection only from STATE_EVENT | Avoids raw/inference data becoming operator state. | STATE_EVENT schema, not CoT mapping itself. | Partial. | CoT egress returns only for STATE_EVENT. | No. | Adapter tests. | CoT ingress creates STATE_EVENT with minimal lineage; source authority and trust labeling need stronger semantics. |
| Vendor extension safety | Enables adoption without semantic capture by vendors. | Partial: strict envelope, flexible payloads. | Partial. | Adapter/mapping pack rules. | No. | Minimal. | Needs explicit namespace registry, collision policy, and extension conformance classes. |

## D. Deep Gap Review

This section compares the current contract against future ZMeta/Z-ISR needs. The
audit distinguishes current coverage from recommended next contract work.

| Future Semantic Area | Current Coverage | Gap / Underdeveloped Area | Recommended Direction |
|---|---|---|---|
| AI model provenance and model cards | INFERENCE_EVENT requires `payload.model.name` and `payload.model.version`. | No model hash, training data lineage, model-card URI/hash, runtime package identity, calibration date, or model family semantics. | Add a normative `model_provenance` block for v1.1+ or v1.2 with optional model card reference, artifact hash, runtime package ID, calibration/evaluation metadata, and producer-owned model namespace. |
| Model drift / runtime monitoring | Confidence guidance says confidence accounts for model confidence and input quality. | No explicit drift state, drift detector output, population shift indicator, performance degradation, or monitoring cadence. | Define model runtime status as SYSTEM_EVENT extension or quality sub-block. Include drift metrics and confidence cap guidance. |
| Raw-data-absent evidence flags | Data refs are optional/informative in v1.0 and formalized in v1.1.0. | No field that explicitly says raw evidence is absent, unavailable, intentionally withheld, degraded, deleted, or never collected. | Add evidence availability metadata: `evidence_status`, `raw_data_status`, and reason codes. |
| Data references and local stores | Appendix A and v1.1.0 data_ref/data_refs define lightweight pointers. | Store identity, retention horizon, access domain, hash requirement, local-only behavior, and redaction/export behavior are not fully governed. | Promote data references to a governed extension with store namespace, retention, releaseability, hash policy, and raw-data-absent semantics. |
| Confidence decomposition | Appendix B gives formula guidance; v1.1 quality block exists. | Top-level confidence is a single scalar with no machine-readable decomposition into model, timing, spatial, lineage, freshness, profile, and human factors. | Add optional `confidence_factors` or `quality.confidence_components` with explicit semantics and caps. |
| Trust scoring versus confidence | Confidence is defined as downstream consumption confidence. Producer authority exists as policy. | Trust in producer/key/mesh path is not separated from confidence in the observation/inference/state claim. | Define `trust` as separate from `confidence`: producer identity trust, key trust, route trust, quarantine state, spoof suspicion, and confidence cap interactions. |
| Mesh trust and event signing | No signing semantics. Contract hash gates exist for deployment drift. | No event signature, key ID, signer role, trust anchor, path attestation, signature failure behavior, quarantine, or replay/spoof recovery. | Add a security/signing section with optional signature envelope, key identity, accepted algorithms, chain of custody, and policy modes. |
| Producer identity and key identity | `source.producer` and policy pattern allowlists exist. | Producer string is not bound to a cryptographic key, cert, hardware identity, or attested software package. | Define `source_identity` versus `key_identity`, with policy binding from producer to key and role. |
| Drone friend/foe / behavioral identity | CoT egress has friendly/hostile display behaviors; track state has `class`. | No ZMeta-native identity confidence, friend/foe labels, behavioral trust, spoof suspicion, or drone behavioral fingerprint semantics. | Add track identity semantics for IFF-like labels, behavioral identity claims, and their separation from entity class. Keep these as inference/fusion/state-derived, not observation facts. |
| Compute-tier degradation | Section 6 describes failure modes and Profile L/M operator defaults. | No compute capability taxonomy, Orin/Pi/MCU class behavior, model fallback semantics, local processing limits, or compute-derived confidence caps. | Add compute elasticity section: compute tiers, allowed degradation, model fallback, local-only inference, and minimum Profile L obligations. |
| Emergency profile below Profile L | Profile L is severe constraint. | No Profile E/minimum survival mode for sub-LoRa, burst-only, MCU-only, or store-and-forward beacon operation. | Consider future Profile E/EL as v1.2+ candidate with explicit minimum envelope, state, timing, lineage handle, and trust semantics. |
| Coalition release labels and redaction behavior | No release labels. Data refs and extensions are ignorable. | No releasability labels, caveats, classification markings, originator control, redaction provenance, sanitized projection semantics, or cross-coalition field handling. | Add coalition release/cross-domain metadata and redaction rules. Redaction should be a projection with explicit provenance, never silent mutation. |
| Cross-domain export metadata | DMZ node role exists; `source.node_role` includes DMZ/CLOUD. | No cross-domain guard/export decision metadata, sanitization evidence, policy pack ID, release domain, or denied-field trace. | Add cross-domain export block and conformance tests for sanitized projections. |
| Track lifecycle states | Section 5.3 describes NEW/ACTIVE/MERGED/SPLIT/LOST and retirement. | No dedicated machine-readable lifecycle event type in v1.0; stale/lost/retired/merge/split are represented indirectly. | Add v1.1+ or v1.2 lifecycle SYSTEM_EVENT/FUSION subtype vocabulary with merge/split/stale/lost/retired semantics. |
| Human/operator confirmation and override | Operator interfaces do not author or modify ZMeta events. | No human confirmation, analyst adjudication, override, or operator annotation event semantics. | Define operator confirmation as separate event type/subtype or governed annotation event that references prior events without mutating them. |
| Replay and red-team event labeling | Replay tools exist; CoT egress can use wall-clock mode for replay. | No event-level replay, exercise, simulated, red-team, synthetic, or adversarial label semantics. | Add optional `event_context` labels for replay/simulation/red-team with policy-driven export handling. |
| Software supply chain and model/package provenance | `source.sw_version` exists; release artifacts are signed. | No package hash, container image digest, SBOM reference, adapter version identity, or runtime attestation in events. | Add `source.sw_build` / `runtime_provenance` optional block and define how it interacts with producer trust. |
| Extension registry and namespace governance | Vendor extensibility rules exist, and mapping packs exist. | No formal registry, namespace syntax, reserved prefixes, review process, conflict handling, deprecation, or ignorable-extension conformance tests. | Add extension registry/versioning section with vendor namespace rules and machine-readable registry file candidate. |
| Conformance class definitions | Conformance pack exists with must-pass/must-fail. | No named conformance classes for producer, gateway, policy, Profile L compact, CoT/TAK, protobuf, security, or cross-domain roles. | Define conformance classes and required tests per class. |
| Raw-data-absent trust mode | Related to data refs and confidence guidance. | No standard way to trust a STATE_EVENT when parents/raw artifacts are not available over the link, except unresolved lineage tolerance in Profile L. | Define trust modes: raw-present, raw-referenced, lineage-only, producer-attested, redacted, and raw-absent. |
| Bandwidth-denied operation | Profile L and compact mapping are strong. | Profile L still assumes STATE_EVENT with lineage and confidence; no burst, queue, or eventual sync semantics for extended denial. | Add denied-operation lifecycle and queue/replay semantics, including what remains mandatory under extreme budget. |
| Zero-trust metadata flows | DMZ/CLOUD roles and policy exist. | No zero-trust event verification, claim validation, quarantine, or trust downgrade workflow. | Add zero-trust flow section tied to signing, source identity, quarantine, and release labels. |

## E. Brittleness / Ambiguity Review

1. v1.0 data references are ambiguous. Appendix A is informative and optional,
   while `schema/zmeta-event-1.0.schema.json` permits `payload.data_ref` and
   `payload.data_refs` on observations. v1.1.0 formalizes those semantics more
   tightly. Risk: implementers may treat v1.0 data refs as fully normative
   despite the contract labeling them informative.

2. `additionalProperties: true` in several payloads preserves vendor adoption
   flexibility but creates an extension safety gap. Risk: vendors may smuggle
   semantic fields into free-form payload/claim/quality/extensions objects and
   downstream consumers may reinterpret them.

3. Confidence is overloaded. It is currently model belief, downstream
   consumption confidence, and degraded-state confidence depending on context.
   Appendix B gives useful guidance, but the contract lacks a normative
   decomposition and a clear separation between confidence and trust.

4. Trust is mostly policy authority, not event semantics. Producer authority is
   pattern-based in YAML and effective for reference validation, but it is not
   bound to cryptographic identity, route trust, or mesh behavior.

5. Track lifecycle is semantically strong but operationally incomplete. The
   contract defines merge/split/lost/retired behavior, but v1.0 lacks
   machine-readable lifecycle events. Risk: gateways and fusion engines will
   invent incompatible system events or local logs.

6. Profile L semantics are strong but possibly brittle under extreme bandwidth.
   The compact mapping reports Profile L STATE_EVENT at about 231 bytes with
   optional field stripping. Links below that budget may need an emergency
   profile rather than informal field dropping.

7. "Timing quality mandatory" is well-motivated, but stale/missing timing policy
   can fail closed by default. A provided Profile L policy variant allows
   degraded forwarding, but the contract should explicitly define the semantic
   difference between reject, warn, and degrade modes.

8. Low-compute degradation is described through failure modes, but not tied to
   compute tiers or model substitution. Risk: Orin-class and Pi/MCU-class nodes
   may emit semantically similar events with very different inference quality and
   runtime guarantees.

9. CoT/TAK projection is correctly limited to STATE_EVENT, but the projection
   boundary lacks release/trust semantics. CoT egress currently includes display
   conveniences such as hostile label fallbacks and wall-clock replay mode.
   Those are reference behaviors and should not become hidden semantic rules.

10. Adapter docs show some integration drift risk. For example, the MAVLink
    README says platform state maps several telemetry fields to
    `payload.features.*`, while current STATE_EVENT schema forbids raw
    `features` and the implementation now uses `payload.quality`. This is a
    documentation friction point rather than a contract failure.

11. Raw-data-absent operation is not explicit. Profile L permits unresolved
    lineage references, but consumers lack a standard trust mode for
    lineage-only, raw-referenced, raw-redacted, or raw-unavailable events.

12. Coalition and cross-domain behavior is absent. Without release labels,
    redaction provenance, and cross-domain export metadata, implementers may
    either leak fields or silently remove fields in ways that look like ordinary
    profile thinning.

13. Version boundaries are mostly clear, but v1.1.0 is described as both
    experimental and compatibility-tested while the current release is v1.1.4.
    The contract should continue to state which pieces are locked v1.0,
    governed v1.1.0 extension, and reference implementation.

14. Schema validation can be confused with semantic validation. The repo already
    says schema and policy together define enforcement, but future users may
    rely on JSON Schema only and miss producer authority, timing freshness,
    lineage parent typing, dedupe, and no-reinterpretation rules.

## F. Recommended Contract Changes

These are recommendations only. They should be applied to the semantic contract
in a future task after review. No contract text was changed by this audit.

### Must Add Before Stack Hardening

- Add a "Normative Authority and Enforcement Surface" section that states:
  semantic contract is the source of meaning; JSON Schema enforces structure and
  some cross-field rules; policy enforces deployment/runtime rules; adapters and
  gateways implement projections; encodings are non-semantic projections;
  examples are non-normative.
- Add a compact normative-vs-non-normative legend inside the contract so each
  section clearly identifies invariant, schema rule, policy rule, adapter
  guidance, extension candidate, explanation, or example.
- Clarify v1.0 data reference status: either keep Appendix A explicitly
  informative and say v1.0 schema permissiveness does not make data refs
  semantically required, or promote a minimal v1.0 data reference convention.
- Define confidence versus trust. Keep `confidence` about claim/model/state
  reliability and define `trust` as producer/key/path/releaseworthiness.
- Define raw-data-absent and unresolved-lineage trust modes, especially for
  Profile L and denied operation.
- Add extension namespace governance: reserved prefixes, vendor namespaces,
  ignorable-extension requirements, no reinterpretation tests, and review path.
- Add conformance class definitions before expanding implementations:
  core producer, schema validator, policy validator, gateway, Profile L compact,
  protobuf projection, CoT/TAK adapter, ingress adapter, and conformance pack.
- Clarify that recommendations in Appendices and examples do not create
  valid-under-v1.0 semantics unless schema and normative contract text say so.

### Should Add For v1.1.0

- Promote structured quality metadata and error ellipse semantics as governed
  extension concepts while preserving v1.0 invariants.
- Add model provenance extension fields: model name/version plus optional model
  card reference, model artifact hash, package/runtime identifier, calibration
  date, and training/evaluation caveat references.
- Add model drift/runtime monitoring semantics as SYSTEM_EVENT extension or
  governed quality block.
- Add SENSOR_STATUS and PLATFORM_STATUS as governed status events with clear
  separation from observation/state/task/link semantics.
- Add explicit evidence/data reference states:
  `RAW_PRESENT`, `RAW_REFERENCED`, `RAW_LOCAL_ONLY`, `RAW_REDACTED`,
  `RAW_UNAVAILABLE`, `RAW_NOT_COLLECTED`.
- Add lifecycle event candidates for track stale, lost, retired, merge, split,
  and identity revision if those are not deferred to v1.2.
- Add replay/simulation/red-team labels that cannot be silently stripped during
  cross-domain or profile projection.

### Future v1.2+ Candidates

- Event signing, key identity, trust chain, mesh route attestation, quarantine,
  spoof suspicion, and spoof recovery semantics.
- Coalition release labels, redaction provenance, cross-domain export decisions,
  release authority, and guard policy hash references.
- Compute-tier taxonomy and degraded runtime behavior for Orin-class, Pi-class,
  MCU-class, and intermittent compute.
- Emergency profile below Profile L for ultra-constrained burst-only links.
- Drone identity, friend/foe labels, behavioral identity claims, and spoofed
  drone behavior detection.
- Software supply chain provenance: container/image digest, adapter package
  hash, SBOM reference, runtime attestation, and model package provenance.
- A machine-readable extension registry and reserved-field namespace file.

### Policy-Pack-Only Rules

- Producer-to-role/event-type bindings.
- Producer/key allowlists once key identity exists.
- Timing freshness thresholds and reject/warn/degrade mode per profile.
- Confidence caps under degraded timing, unresolved lineage, stale observations,
  model drift, or raw-data-absent modes.
- Command origin gates, deconfliction authority, and command route constraints.
- Release/redaction policy, once release labels and export metadata exist.
- Quarantine behavior for failed signatures, spoof suspicion, stale trust, or
  untrusted mesh paths.

### Adapter/Gateway Guidance

- Adapters must never treat schema acceptance as semantic authorization.
- Compatibility normalizers must stay opt-in, sidecar-recorded, and explicitly
  pre-validation.
- Gateways must preserve source-authored event fields and only add allowed
  export/profile/timing annotations or conservative degradation fields.
- CoT/TAK and JREAP projections must remain STATE_EVENT-only unless a future
  contract explicitly defines another projection class.
- Ingress adapters must record legacy IDs in payload-scoped provenance rather
  than reusing them as ZMeta `event_id`.
- Adapter docs should be kept synchronized with schema prohibitions, especially
  STATE_EVENT raw-feature/data-ref restrictions.

### Conformance-Test Requirements

- Add projection immutability tests: gateway/profile projection must preserve
  `event_id`, event type/subtype, source-authored timestamp, source identity,
  lineage, track ID, and payload meaning.
- Add extension safety tests: vendor extensions are ignored unless registered
  and must not override core fields or layer boundaries.
- Add confidence/trust tests once trust fields exist.
- Add raw-data-absent and unresolved-lineage tests for Profile L.
- Add signing/quarantine tests once security semantics exist.
- Add lifecycle tests for merge/split/stale/lost/retired once event vocabulary
  exists.
- Add cross-domain redaction tests: redaction must be explicit, lineage-preserved,
  and non-reinterpreting.
- Add per-adapter conformance fixtures for timestamp, unit conversion, layer
  mapping, lineage, and profile compatibility.
- Add encoding equivalence tests for compact/protobuf whenever mapping versions
  change.

## G. Proposed Contract Outline

0. Operating Model
   - Purpose, threat model assumptions, semantic authority, and non-goals.

1. Locked v1.0 Semantic Invariants
   - Event worldview, immutability, UUIDv7, layer separation, authority
     boundaries, transport non-semantics, profile thinning, lineage,
     uncertainty, command/tasking limits, vendor extension safety.

2. Normative Authority and Enforcement Surface
   - Contract vs schema vs policy vs adapter/gateway vs encoding vs examples.
   - Normative/non-normative classification legend.

3. Event Identity and Immutability
   - UUIDv7, legacy ID preservation, event projection rules, correction rules,
     replay identity, and no source-authored field mutation.

4. Layer Model and Authority Boundaries
   - Observation, inference, fusion, state, command, system.
   - Producer/role authority and policy binding.

5. Time, Timing Quality, and PNT Degradation
   - `event.ts`, publish/receive stamps, TIME_STATUS, holdover, drift,
     freshness, degraded timing modes, RF windows.

6. Units, Geodesy, and Measurement Quality
   - WGS-84, HAE, UTC-Z, known units, structured quality, geo availability,
     error ellipse.

7. Confidence, Uncertainty, and Trust
   - Top-level confidence, confidence components, quality metadata, producer/key
     trust, route trust, raw-data-absent trust modes, trust/confidence
     interactions.

8. Lineage, Provenance, Evidence, and Replay
   - Envelope lineage, payload-local provenance, data references, raw data
     availability, replay/simulation/red-team labels, AAR reconstruction.

9. Profiles and Bandwidth Thinning
   - Profile L/M/H, emergency profile candidates, allowed event types,
     thinning rules, compact Profile L semantics, denied-operation behavior.

10. Operator State Projection and CoT/TAK Mapping
    - STATE_EVENT projection boundary, CoT/JREAP guidance, UI metadata,
      no raw data in state.

11. Command / Tasking Governance
    - Allowed task types, idempotency, TTL, deconfliction, TASK_ACK lifecycle,
      operator approval/override candidates.

12. Track Persistence and Lifecycle Governance
    - Track ID assignment, non-reuse, dedupe, merge, split, stale, lost,
      retired, identity revision.

13. Security, Signing, Mesh Trust, and Quarantine
    - Event signatures, key identity, trust anchors, route/path trust,
      quarantine, spoof suspicion, spoof recovery.

14. Coalition Release and Cross-Domain Export
    - Release labels, redaction provenance, cross-domain guard metadata,
      export policy hash, sanitized projection rules.

15. AI / Model Provenance and Runtime Monitoring
    - Model cards, artifact hashes, package provenance, drift, runtime health,
      calibration, confidence caps.

16. Compute Elasticity and Degraded Runtime Behavior
    - Compute tiers, degraded model/runtime behavior, Profile L obligations,
      MCU/Pi/Orin classes, local processing limits.

17. Extension Registry and Versioning
    - Vendor namespaces, reserved prefixes, extension review, deprecation,
      version branch rules, compact/protobuf mapping version rules.

18. Enforcement Matrix
    - Rule-by-rule mapping across schema, policy, adapters/gateways, encodings,
      and conformance.

19. Conformance Classes
    - Producer, validator, gateway, policy pack, Profile L compact, protobuf,
      adapter ingress, CoT/TAK egress, cross-domain, security.

20. Future Extension Candidates
    - Explicit list of deferred semantics and criteria for promotion.

## Audit Conclusion

The current contract is a solid v1.0 semantic foundation. It already locks the
essential concepts that keep ZMeta from becoming a brittle adapter schema:
events, immutability, UUIDv7 identity, layer separation, lineage, uncertainty,
profile non-reinterpretation, time quality, units/geodesy, and bounded command
governance.

The main lockdown risk before significant stack work is not that v1.0 is weak.
It is that future ISR, edge AI, coalition, mesh, compact encoding, and Z-ISR
needs will be implemented faster than the semantic contract absorbs them. The
highest-priority contract additions are enforcement-surface clarity, trust
versus confidence, raw-data-absent evidence, extension namespace governance,
conformance classes, and explicit treatment of signing/mesh/quarantine,
coalition redaction, model provenance/drift, and compute-tier degradation.
