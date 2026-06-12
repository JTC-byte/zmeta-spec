# ZMeta Defensive Publication

Status: current-main advisory disclosure.

Date: 2026-06-12

This document publicly describes the ZMeta architecture in technical,
patent-searchable language. Its purpose is to strengthen the public record for
the open ZMeta specification and reduce ambiguity before industry
socialization. It is not legal advice, a patent opinion, a patent filing, a
patent license, a trademark filing, export guidance, or a formal
standards-body policy.

For legal strategy, including defensive publication venues, provisional patent
decisions, trademark registration, contributor agreements, and standards-body
patent commitments, consult qualified counsel.

## Public Baseline

ZMeta is a transport-agnostic, event-based metadata specification and
reference stack for resilient ISR systems. It separates sensor facts,
inference claims, fusion decisions, operator-facing state, command/tasking
intent, and system diagnostics into distinct event families with governed
validation, lineage, timing, confidence, profile projection, and policy
adjudication.

The public baseline includes:

- normative semantic contract;
- version-discriminated JSON schemas;
- policy YAML;
- extension registry;
- conformance classes and fixtures;
- compact CBOR and protobuf projection specifications;
- reference gateway and adapters;
- release manifest and example implementation claims;
- process governance for downstream clones, forks, releases, and dialects.

## Technical Disclosure

### Event-Family Separation

ZMeta uses event-family separation to prevent raw measurements, model claims,
fusion decisions, display state, commands, and diagnostics from collapsing into
one ambiguous metadata object.

- `OBSERVATION_EVENT` carries measured sensor facts and measurement context.
- `INFERENCE_EVENT` carries model or analytic claims derived from observations.
- `FUSION_EVENT` carries association and track-formation decisions.
- `STATE_EVENT` carries operator-facing track or state projection.
- `COMMAND_EVENT` carries bounded tasking intent with safety constraints.
- `SYSTEM_EVENT` carries health, timing, link, validation, and task
  acknowledgement diagnostics.

This separation prevents a state projection from becoming raw evidence,
prevents a classifier claim from becoming a track by assertion, and prevents a
command from bypassing authority and deconfliction policy.

### Semantic Contract Authority

The semantic contract is the primary authority over schemas, policy, encodings,
adapters, validators, examples, and release metadata. Schemas enforce shape and
version dispatch. Policy enforces deployment-sensitive authority and risk
decisions. Conformance fixtures make the contract testable.

The locked v1.0 kernel preserves stable meaning for event identity, event
families, version dispatch, units, geodesy, timing quality, confidence,
lineage, profile projection, producer authority, accepted risk, and command
safety.

### Version Dispatch And Private Dialects

ZMeta validates by exact `zmeta_version` dispatch. Future or experimental
concepts do not become valid under the locked v1.0 branch unless a governed
version process adopts them. Downstream changes to core vocabulary, schema,
policy semantics, projection, or command authority form a private dialect or
fork unless they are versioned, documented, conformance-covered, and released
through equivalent governance.

### Timing Quality And PNT Degradation

ZMeta represents timing quality directly on events or through applicable
`TIME_STATUS` diagnostics. Timing freshness policy evaluates event timestamps
against timing status, detects missing, stale, unsynced, holdover, and
negative-age anomalies, and emits governed diagnostics such as
`TIMING_STATUS_MISSING`, `TIMING_STATUS_STALE`, and
`TIMING_STATUS_AGE_NEGATIVE`.

Negative age is not silently clamped to zero beyond a configured tolerance.
That preserves evidence of producer clock anomalies or out-of-order timing
references.

### Lineage, Evidence, And Raw-Data-Absent Mode

ZMeta events carry lineage through UUIDv7 event identity and `lineage.based_on`
references. Adapters may preserve external or legacy identifiers in
payload-scoped provenance fields, but canonical event identity remains ZMeta
identity. Lineage supports audit, replay, confidence review, and downstream
explainability without requiring raw captures to be present in every message.

### Confidence And Accepted Risk

ZMeta distinguishes confidence from accepted risk. A policy-adjudicated event
may remain schema-valid while carrying accepted-risk labels, use limits, and
diagnostic reason codes. Degraded or externally promoted data must not look
clean. Consumers are expected to honor `allowed_uses`, `prohibited_uses`,
`policy_decision`, `risk_dimension`, `reason_code`, and effect metadata during
display, fusion, command basis, autonomy, after-action review, and audit
intake.

### Producer Authority And External Promotion

ZMeta distinguishes external track or state messages from authoritative ZMeta
state. External CoT, JREAP, MAVLink, or similar inputs cannot become
authoritative `STATE_EVENT` outputs unless policy-scoped external-promotion
evidence and lineage transforms are present and accepted by producer-authority
policy.

This prevents an adapter from silently promoting another system's display state
into upstream ZMeta truth.

### Profile Projection And Bandwidth Discipline

ZMeta supports profile projection for constrained links and consumers. Lower
profiles may remove or reduce fields only when the projection preserves core
semantics, risk labels, timing quality, confidence meaning, lineage,
external-promotion evidence, and profile precision rules. Profile projection
must not silently strip accepted-risk labels or make degraded data appear
clean.

### Units, Geodesy, And Reference Frames

ZMeta standardizes canonical units and geodesy. Coordinates, altitude, speed,
heading, bearing, timing, and uncertainty fields carry controlled meanings.
Canonical bearing and heading fields must use their governed reference frame;
sensor-native or unknown frames must be converted, omitted, or preserved under
explicit non-canonical provenance fields.

### Command Safety And Deconfliction

ZMeta command events are bounded tasking metadata, not free-form control
channels. Command safety includes authority policy, task-type constraints,
dedupe, task acknowledgement, validity windows, deconfliction requirements, and
prohibition of unsafe or ambiguous command surfaces such as ungoverned altitude
control in generic task metadata.

### Encoding Projections

Compact CBOR and protobuf are wire projections of canonical ZMeta JSON, not
independent semantic authorities. Decoded messages must pass the same schema,
policy, projection, extension-registry, and conformance expectations as JSON.
Compact v1 decoders reject unknown integer keys in governed maps rather than
re-mapping them to ambiguous string keys.

### Release Hashes And Claims

ZMeta release manifests hash the semantic contract, schema bundle, policy
bundle, extension registry, conformance classes, profile projection catalog,
encoding-negative suite, precision policy, bad-event corpus, adapter
conformance fixtures, encoding projection specs, process governance, and release
bundle. Example claims bind implementations to those release hash baselines.

This creates a reproducible public record for a specific release and makes
conformance claims auditable.

### Adapters And External Protocols

ZMeta adapters map external systems into event families without redefining
ZMeta semantics. Native sensor measurements map to observations, analytic
outputs map to inferences, association outputs map to fusion, external display
tracks require promotion evidence before becoming state, and tasking maps to
commands only through command safety rules.

## Open Architecture Intent

The architecture disclosed here is intended to remain openly implementable.
Implementers may build proprietary or open systems around the Apache-licensed
reference material, but should not claim upstream ZMeta conformance after
changing governed semantics. Private dialects should be labeled as private
dialects.

## Publication Guidance

When sharing ZMeta externally, cite:

- the public repository;
- a specific tagged release;
- release notes and validation report;
- release manifest or release bundle hash;
- this defensive publication;
- conformance and trademark guidance.

Avoid privately disclosing unpublished future vocabulary, roadmap concepts, or
deployment-specific mappings unless those disclosures are covered by an
appropriate agreement or have already been published.

