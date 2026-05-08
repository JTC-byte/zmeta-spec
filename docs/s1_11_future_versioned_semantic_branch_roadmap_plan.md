# S1-11A - Future Versioned Semantic Branch Roadmap Plan

Date: 2026-05-07

## Summary

This plan establishes a disciplined roadmap for D-003 future ZMeta semantic
branches. It does not implement any branch, change schemas, change the
extension registry, change conformance classes, change validators, change
runtime behavior, or make future vocabulary valid.

Future semantics must be adopted through explicit version branches with
semantic definitions, schema shape where structural, policy behavior where
contextual, adapter/gateway expectations, encoding guidance, documentation,
positive and negative fixtures, release/hash updates, and audit.

## A. Current Future-Semantic Landscape

Current valid v1.0 vocabulary is defined by `schema/zmeta-event-1.0.schema.json`
and governed by the semantic contract, policy packs, validators, examples, and
conformance fixtures. It includes the current event families, v1.0 subtypes,
Profile L/M/H behavior, lineage, confidence, timing quality, command governance,
and adapter/gateway invariants.

The v1.1.0 branch is experimental. The dispatcher validates v1.1.0 events only
against `schema/zmeta-event-1.1.0.schema.json`, and v1.1.0 concepts must not
validate under `zmeta_version: "1.0"`. Current experimental registry entries
include structured quality, error ellipse, formal data reference behavior,
EO/IR/ACOUSTIC/NETWORK feature contracts, SENSOR_STATUS, PLATFORM_STATUS, and
expanded command tasks such as RETURN_TO_BASE, LAND, LOITER, SCAN_RF,
TRACK_TARGET, and CHANGE_SENSOR_MODE.

Reserved or proposed future vocabulary is tracked in
`spec/extension-registry.yaml` and by future conformance classes. Examples
include PNT_STATUS, MODEL_STATUS, ASSURANCE_EVENT, TRUST_STATUS, event signing
and key identity concepts, UAS identity concepts, release/export concepts,
replay labels, emergency profile concepts, track lifecycle names, and future
observation modalities such as RADAR, LIDAR, MAGNETIC, SEISMIC, SIGINT, CYBER,
ENVIRONMENTAL, and MARITIME.

Concepts removed by S1-10P are outside ZMeta baseline scope. They must not be
reintroduced as semantic branches unless a new ZMeta-specific event semantic is
defined without organizational package scope.

## B. Problem Statement

Future ZMeta concepts need a roadmap because uncontrolled adoption can weaken
the locked baseline. Main risks are:

- future vocabulary leaking into v1.0 validation;
- v1.1.0 experimental concepts being treated as adopted baseline;
- loose vendor/private extensions redefining core meaning;
- profile/export, trust, release, UI, emergency, and transport concepts being
  conflated;
- schema changes landing without policy, gateway, encoding, and conformance
  coverage;
- out-of-scope organizational artifacts being reintroduced as if they were
  ZMeta event semantics.

The roadmap lets maintainers prioritize future semantic work while keeping
reserved concepts invalid until their implementation surfaces are complete.

## C. Scope Guardrails

Future ZMeta branches may cover event semantics, schema vocabulary, policy
enforcement, adapter and gateway behavior, encoding projection behavior,
conformance tests, profile/export behavior, and event-relevant timing, PNT,
lineage, confidence, trust, release, and identity semantics.

Future ZMeta branches must not cover acquisition, vendor scoring, data-rights
governance, DevSecOps evidence, TTP/training, lessons learned, procurement,
FORGE capability packages, or organizational transition packages. Those are not
ZMeta event semantics.

## D. Version Branch Governance Model

Branch lifecycle statuses:

- `candidate`: idea identified but not yet reserved or scoped.
- `reserved`: name or concept held so it cannot accidentally become current
  vocabulary.
- `proposed`: initial scope and rationale exist.
- `experimental`: valid only in the named version branch with schema and tests.
- `implemented_pending_audit`: implementation exists but is not closed.
- `adopted`: fully covered and valid in a named branch.
- `rejected`: reviewed and not appropriate for ZMeta event semantics.
- `superseded`: replaced by a newer branch or concept.
- `deprecated`: valid historically but discouraged for new producers.

Adoption gates:

- semantic definition;
- version branch decision;
- schema shape if structural;
- policy rules if contextual;
- adapter/gateway requirements;
- encoding implications;
- positive and negative fixtures;
- conformance class impact;
- release/hash impact;
- migration guidance;
- post-implementation audit.

## E. Candidate Branch Inventory

| Candidate | Purpose | Current Status | Affected Events | Impact Summary | Priority | Recommendation |
| --- | --- | --- | --- | --- | --- | --- |
| PNT integrity / navigation confidence | Represent navigation integrity beyond timing error. | Proposed/reserved through PNT_STATUS and semantic-contract guidance. | SYSTEM_EVENT, STATE_EVENT, FUSION_EVENT, OBSERVATION_EVENT. | Schema/status fields likely; policy confidence caps; gateway quarantine/degrade behavior; fixtures for spoofing, holdover, conflicting sources. | Near-term | Plan first because it protects confidence and state reliability. |
| Event signing / key identity / anti-replay | Authenticate event origin and detect replay without changing event meaning. | Proposed/reserved. | Envelope or sidecar security surface; SYSTEM_EVENT for status. | Structural schema or sidecar decision; policy failure actions; encoding preservation; negative fixtures for bad/missing signatures. | Near-term | Plan before mesh trust because trust needs key and replay primitives. |
| Mesh trust / quarantine | Separate source/path trust from event confidence. | Proposed/reserved. | SYSTEM_EVENT, gateway/export behavior, possibly envelope metadata. | Policy-heavy; gateway routing/quarantine; conformance for confidence/trust separation. | Mid-term | Depends on signing/key identity and trust policy design. |
| UAS identity / behavioral identity | Represent declared, signed, or inferred UAS identity evidence. | Reserved. | INFERENCE_EVENT, FUSION_EVENT, STATE_EVENT. | Must not become IFF authority; needs lineage/evidence and confidence semantics; may depend on PNT, signing, and modality contracts. | Mid-term | Keep future until evidence model is mature. |
| AI model assurance / MODEL_STATUS / ASSURANCE_EVENT | Express event-relevant model/runtime health, drift, calibration, and assurance state. | MODEL_STATUS proposed; ASSURANCE_EVENT reserved; future class exists. | INFERENCE_EVENT, SYSTEM_EVENT. | Schema/status branch; policy for degraded model outputs; fixtures for drift/runtime status; must avoid model-card or process-governance scope. | Mid-term | Plan as event-level runtime/model semantics only. |
| Raw-data-absent / evidence status | Make raw-present, raw-referenced, lineage-only, withheld, redacted, or not-retained evidence status explicit. | Future guidance; replay/data evidence registry categories exist. | OBSERVATION_EVENT, INFERENCE_EVENT, FUSION_EVENT, STATE_EVENT. | Schema or policy-only decision; confidence/trust impact; Profile L lineage tolerance; negative fixtures for hidden uncertainty. | Near-term | Good candidate because it strengthens lineage honesty. |
| Coalition release / cross-domain export label | Govern event-level release/redaction/export semantics. | Reserved/future. | Export projection, STATE_EVENT, FUSION_EVENT, source/lineage fields. | Policy-heavy; projection metadata dependencies; must not become data-rights governance. | Long-term | Defer until projection metadata and release policy are better defined. |
| Projection metadata | Record explicit projection/thinning/redaction/degradation reason without changing same-event meaning. | Future guidance. | All event families at export time. | Schema or sidecar decision; profile interaction; compact/protobuf mapping; projection fixtures. | Near-term | Strong candidate because profiles already need auditable degradation. |
| Track lifecycle | Define track new/active/stale/lost/merged/split/retired semantics. | Reserved names. | FUSION_EVENT, STATE_EVENT, SYSTEM_EVENT maybe. | Schema/state machine; lineage rules for merge/split; gateway dedupe; conformance for no mutation of old events. | Mid-term | Plan after projection and lineage coverage remain stable. |
| Future modality contracts | Add feature contracts for RADAR, LIDAR, MAGNETIC, SEISMIC, SIGINT, CYBER, ENVIRONMENTAL, MARITIME. | Reserved. | OBSERVATION_EVENT, SENSOR_STATUS. | Schema feature contracts; adapter unit normalization; encoding; negative tests for leakage into v1.0. | Mid-term | Implement one modality at a time only when feature contract is complete. |
| Data quality / operator-facing data summary | Summarize event-relevant quality, freshness, confidence, lineage, and trust in a compact operator-facing way. | Future data nutrition guidance/class. | Potentially all events or derived SYSTEM_EVENT. | High conflation risk with UI/reporting; must not replace confidence, quality, lineage, or trust fields. | Long-term | Defer unless scoped as strict semantic summary; reject organizational reporting variants. |
| Compute elasticity / degradation state | Represent degraded runtime tier or fallback mode when it affects outputs. | Future class exists. | SYSTEM_EVENT, INFERENCE_EVENT, gateway/export behavior. | Policy and status fields; confidence impact; gateway handling. | Mid-term | Keep policy-first; add schema only if current status events cannot carry it safely. |
| Emergency / L0 profile | Define behavior below Profile L for severe emergency/denied links. | Reserved/future. | Profile/export policy, STATE_EVENT, SYSTEM_EVENT, COMMAND_EVENT. | High safety risk; must not silently drop required semantics; compact impact. | Long-term | Defer until profile projection and precision policy can prove safety. |

## F. Candidate Rejection / Defer Criteria

Reject or defer a candidate when:

- it is organizational rather than semantic;
- it belongs in policy configuration, not schema;
- it belongs in adapter documentation, not event vocabulary;
- it belongs in release/deployment tooling, not events;
- existing confidence, quality, timing, or lineage semantics already cover it;
- it would create unsafe command/control behavior;
- it violates v1.0 invariants;
- it cannot be safely ignored by consumers.

## G. Recommended Sequencing

Near-term planning candidates:

1. Projection metadata.
2. Raw-data-absent / evidence status.
3. PNT integrity / navigation confidence.
4. Event signing / key identity / anti-replay.

Mid-term candidates:

1. Mesh trust / quarantine.
2. AI model assurance / MODEL_STATUS.
3. Track lifecycle.
4. Compute elasticity / degradation state.
5. Individual future modality contracts.

Long-term candidates:

1. Coalition release / cross-domain export labels.
2. UAS identity / behavioral identity.
3. Emergency / L0 profile.
4. Strict semantic data quality/operator summary, only if it does not become
   reporting or UI governance.

This sequencing is advisory. No branch is approved by this plan.

## H. Branch Dependency Map

- Event signing/key identity should precede mesh trust and quarantine.
- Anti-replay should share the signing/key identity branch or be implemented
  immediately adjacent to it.
- PNT integrity should precede confidence caps for degraded navigation.
- Raw-data-absent/evidence status should precede richer trust and release
  policy behavior.
- Projection metadata should precede coalition export/redaction and Emergency
  L0 behavior.
- AI model assurance depends on lineage, evidence status, and inference
  confidence semantics.
- UAS behavioral identity depends on evidence status, modality contracts, PNT
  integrity, and signing/key identity.
- Track lifecycle depends on lineage and projection preservation so merge/split
  can be represented without mutating old events.

## I. Extension Registry Interaction

Future branches should use `spec/extension-registry.yaml` as the gatekeeper for
names, categories, status transitions, and leakage prevention. A registry entry
does not make vocabulary valid. Reserved and proposed entries remain invalid.
Experimental entries are valid only in their named branch. Adopted entries
require schema, policy, adapter/gateway, encoding, documentation, conformance,
and release review where applicable.

S1-11A does not modify the registry.

## J. Conformance Class Interaction

Future branches should add or update conformance classes only when an
implementation is concrete enough to define claimable evidence. Future classes
must remain unclaimable until required commands, fixtures, dependencies,
limitations, and validation behavior exist. Example claims must not overclaim
future branches.

S1-11A does not modify conformance classes.

## K. Release Manifest / Hash Impact

Future branch implementation can affect:

- `semantic_contract_hash` when semantic text changes;
- `schema_bundle_hash` when schemas change;
- `policy_bundle_hash` when policy packs change;
- `extension_registry_hash` when registry entries or statuses change;
- `conformance_class_manifest_hash` when class definitions change;
- fixture and tool group hashes when validation assets change;
- `release_manifest_hash` and `release_bundle_hash` after manifest rebuild.

Hash updates must follow the S1-09 release manifest process and should not be
casual side effects.

## L. Implementation Pattern for Future Branches

Use the same pattern for each future branch:

1. `Sx-A Plan Only`
2. `Sx-B Implementation`
3. `Sx-C Post-Implementation Audit`
4. Release/hash update if needed

Implementation must include schema if structural, policy if contextual,
adapter/gateway behavior if translation or enforcement is involved, encoding
projection guidance, positive fixtures, negative fixtures, conformance class
updates if claimable, release manifest updates, and audit.

## M. D-003 Closure Strategy

S1-11A should not close D-003. Recommended status after this plan:

```text
OPEN - ROADMAP PLANNED
```

D-003 can close later if maintainers decide that a machine-readable future
branch roadmap or governance artifact is sufficient to track all future branch
work individually. Until then, D-003 remains the umbrella issue preventing
future vocabulary leakage.

## N. Risks and Open Questions

- Branch naming and version numbering: v1.2 versus v2.0 criteria remain open.
- Whether v1.1.0 should ever be adopted or remain experimental remains open.
- Classified or restricted semantic branches may require private review, but
  must not bypass schema/policy/conformance gates.
- Some candidates may remain policy-only and never need schema vocabulary.
- Profile, confidence, trust, quality, release, and UI display semantics must
  stay separate.
- FORGE/development-cell organizational artifact scope must not be reintroduced.
- The next implementation decision is whether S1-11B should create a
  machine-readable future branch roadmap artifact, separate from the extension
  registry and not itself a vocabulary source.
