# ZMeta Contract-to-Stack Crosswalk

**Work item:** S0-03 - Crosswalk the updated semantic contract against the
implementation stack

**Date:** 2026-05-07

**Scope:** Documentation-only comparison of `spec/semantics-contract.md` against
the current schemas, policy pack, reference gateway, encodings, adapters,
examples, and conformance tests. No implementation files were changed.

## Reading Rules

- **Enforced** means the current stack has an active schema, policy, gateway,
  adapter, encoding, or conformance surface that checks the rule.
- **Partially Enforced** means the current stack checks part of the rule, but
  the contract still depends on deployment policy, adapter discipline, or future
  tests.
- **Not Enforced** means the contract describes current expected behavior but
  the inspected stack does not yet provide a reliable enforcement surface.
- **Future** means the contract explicitly labels the concept as a future
  extension candidate. These are not current compliance failures and must not be
  implemented into v1.0 validation without an approved version branch.

## Files Inspected

- Contract and spec: `spec/semantics-contract.md`, `spec/README.md`,
  `spec/versioning.md`, `spec/profile-compatibility.md`,
  `spec/compact-binary-mapping.md`, `spec/protobuf-encoding.md`,
  `spec/field-dictionary.md`
- Schemas: `schema/zmeta-event.schema.json`,
  `schema/zmeta-event-1.0.schema.json`,
  `schema/zmeta-event-1.1.0.schema.json`,
  `schema/proto/zmeta_event_v1.proto`, `schema/README.md`
- Policy: `policy/*.yaml`, especially `profiles.yaml`, `roles.yaml`,
  `semantics.yaml`, `producer-authority.yaml`, `lineage.yaml`,
  `timing-freshness.yaml`, `routing.yaml`, `violation-codes.yaml`
- Gateway and tools: `gateway/src/validators.py`, `gateway/src/gateway.py`,
  `tools/validate.py`, `tools/validate_conformance.py`,
  `tools/check_compat.py`, `tools/convert_encoding.py`,
  `tools/compute_contract_hash.py`
- Encodings: `zmeta_compact.py`, `zmeta_cbor.py`, `zmeta_proto.py`
- Adapters: `adapters/README.md`, `adapters/ingress/*`,
  `adapters/egress/*`, with specific review of CoT ingress/egress
- Examples and tests: `examples/*.jsonl`, `conformance/*.jsonl`,
  `gateway/tests/*.py`, adapter tests

## Section Coverage Summary

| Contract Section | Implementation Status | Notes |
|---|---:|---|
| 0. Reading Model | Enforced | Terminology is documentary; enforcement language is used by schema/policy split. |
| 1. Operating Model | Partially Enforced | Event sourcing, layer roles, and projection boundaries are enforced in schemas/policies; append-only storage behavior is deployment/gateway discipline. |
| 2. Version Semantics | Enforced | Canonical dispatcher and version-specific schemas isolate v1.0 and v1.1.0. |
| 3. Enforcement Model | Enforced | Schema, policy, gateway, encoding, and conformance surfaces exist. No single surface enforces all semantics. |
| 4. Locked v1.0 Semantic Invariants | Partially Enforced | Core invariants are enforced; projection non-reinterpretation needs stronger conformance. |
| 5. Time, Timing Quality, and PNT Degradation | Partially Enforced | UTC-Z, timing quality, TIME_STATUS freshness, and holdover warnings exist; PNT integrity is future. |
| 6. Units, Geodesy, and Measurement Quality | Partially Enforced | Core units/geodesy are schema-enforced; broader modality quality semantics are partial. |
| 7. v1.0 Event Model and Payload Contracts | Enforced | Event families, subtype consistency, payload restrictions, confidence, and lineage are schema/policy enforced. |
| 8. Confidence, Uncertainty, and Trust | Partially Enforced | Confidence placement is enforced; trust score and confidence decomposition are future. |
| 9. Lineage, Provenance, Evidence, and Raw-Data-Absent Mode | Partially Enforced | Mandatory lineage and parent checks exist; raw-data-absent evidence states are future. |
| 10. Profiles, Bandwidth, and Degraded Operation | Partially Enforced | H/M/L legality and compact mapping exist; projection metadata and full thinning audit are future. |
| 11. AI Provenance and Inference Semantics | Partially Enforced | v1.0 model name/version and lineage exist; model cards, runtime, drift, and assurance are future. |
| 12. Compute Elasticity | Future | Current semantics guide low compute behavior, but no compute-tier vocabulary exists. |
| 13. Track Persistence and Lifecycle Governance | Partially Enforced | Track identity in fusion/state is enforced; lifecycle states are guidance/future. |
| 14. Operator State Projection and CoT/TAK Mapping | Partially Enforced | CoT egress is STATE_EVENT-only and ingress requires confidence/lineage; projection conformance class is not formalized. |
| 15. Command and Tasking Governance | Enforced | Bounded tasking, deconfliction, altitude prohibition, dedupe, TASK_ACK, and command routing are enforced. |
| 16. Security, Mesh Trust, Signing, and Quarantine | Future | Current schema violation events exist, but signing/trust/quarantine are not current vocabulary. |
| 17. UAS Identity and Behavioral Trust | Future | Identity claims are not current subtype vocabulary. |
| 18. Coalition Release and Cross-Domain Export | Future | Release labels, redaction projection, and guard audit are not current vocabulary. |
| 19. Data Nutrition Labels | Future | Operator summary concept is contract guidance only. |
| 20. Extension Registry and Namespace Governance | Partially Enforced | Reserved semantics are documented in schema README; no registry artifact or adoption workflow exists. |
| 21. v1.1.0 Extension Semantics | Enforced | Experimental schema and conformance fixtures isolate SENSOR_STATUS, PLATFORM_STATUS, structured quality, data_ref/data_refs, and expanded tasks. |
| 22. Conformance Classes | Partially Enforced | Test families exist, but no machine-readable conformance-class claim matrix exists. |
| 23. Implementation Mapping | Enforced | Current document maps surfaces; this crosswalk turns gaps into backlog items. |
| 24. Change Log / Semantic Delta | Enforced | Documentation only; implementation blockers remain deferred. |

## Contract-to-Stack Crosswalk

| Contract Rule | Contract Section | Current Enforcement Surface | File(s) | Status | Recommended Implementation Item | Priority |
|---|---|---|---|---:|---|---:|
| Semantic contract is authoritative over schemas, policy, encodings, adapters, gateways, examples, and tests | 0, 3 | Documentation, contract hash support | `spec/semantics-contract.md`, `README.md`, `tools/compute_contract_hash.py`, `gateway/src/gateway.py` | Partially Enforced | Recompute release/deployment contract hashes after this contract rewrite before release hardening. | P0 |
| v1.0 vocabulary lock | 2.1, 21 | Exact `zmeta_version: "1.0"` branch, dispatcher `oneOf`, conformance invalid examples | `schema/zmeta-event.schema.json`, `schema/zmeta-event-1.0.schema.json`, `conformance/must-fail.jsonl`, `gateway/tests/test_schema_version_discrimination.py` | Enforced | Maintain as release gate. | Maintain |
| v1.1.0 isolation from v1.0 | 2.2, 21 | Exact v1.1.0 branch; v1.1.0-only SENSOR_STATUS/PLATFORM_STATUS invalid under v1.0 | `schema/zmeta-event.schema.json`, `schema/zmeta-event-1.1.0.schema.json`, `schema/README.md`, `conformance/must-fail.jsonl` | Enforced | Maintain negative tests whenever adding extension vocabulary. | Maintain |
| Future concepts are not valid current vocabulary | 2.3, 16-20 | Schema strictness rejects unknown core fields/subtypes; contract labels future candidates | `schema/*.json`, `spec/semantics-contract.md`, `conformance/must-fail.jsonl` | Partially Enforced | Add an explicit extension registry artifact so future names are reserved without becoming valid. | P1 |
| Version negotiation must not reinterpret events | 2.4 | Compatibility normalizer is non-normative and records sidecar reports; validators use canonical dispatcher | `tools/compat_normalizer.py`, `tools/check_compat.py`, `tools/README.md`, `schema/README.md` | Enforced | Keep alias normalization outside normative validation. | Maintain |
| Event subtype consistency | 7.1, 7.2 | Schema conditional payload matching and payload discriminator checks | `schema/zmeta-event-1.0.schema.json`, `schema/zmeta-event-1.1.0.schema.json`, `conformance/must-fail.jsonl` | Enforced | Maintain subtype mismatch tests. | Maintain |
| Observation/inference/fusion/state separation | 4.3, 7 | Schema and policy forbid identity/classification in observations, track IDs in inferences, raw features in state | `schema/*.json`, `policy/semantics.yaml`, `gateway/src/validators.py`, `conformance/must-fail.jsonl` | Enforced | Add adapter projection tests for every ingress adapter to prove layer classification. | P1 |
| Source-authored immutability and append-only behavior | 4.1, 4.2 | UUIDv7 and dedupe are enforced; no event-store immutability layer is present | `schema/*.json`, `gateway/src/validators.py`, `gateway/src/gateway.py` | Partially Enforced | Define gateway/store append-only acceptance tests when a persistent event store is introduced. | P1 |
| UUIDv7 event identity | 4.2 | Regex pattern in schema; generators in examples/tests | `schema/*.json`, `zmeta_uuid.py`, `conformance/*.jsonl`, `gateway/tests/*.py` | Enforced | Maintain; add future tests for adapters that generate IDs internally. | Maintain |
| UTC timestamp with trailing `Z` | 5.1, 5.2 | Schema timestamp pattern and adapter timestamp normalization helpers | `schema/*.json`, `adapters/ingress/time_utils.py`, `adapters/ingress/test_timestamp_normalization.py`, `conformance/must-fail.jsonl` | Enforced | Maintain UTC-Z negative fixtures. | Maintain |
| `event.ts` semantics per event family | 5.2 | Documentation and adapter conventions; schema enforces format, not semantic source meaning | `spec/semantics-contract.md`, `adapters/README.md`, adapter READMEs | Partially Enforced | Add adapter-specific assertions documenting how native timestamps map into `event.ts`. | P2 |
| Timing quality presence and shape | 5.3, 5.4 | Schema permits timing blocks; policy requires timing quality for operational event types or fallback TIME_STATUS | `schema/*.json`, `policy/semantics.yaml`, `gateway/src/validators.py`, `tools/validate.py`, `conformance/*.jsonl` | Enforced | Maintain; keep Profile L fallback behavior tested. | Maintain |
| TIME_STATUS freshness and holdover monotonicity | 5.4, 5.5 | Policy pack and gateway validators check max age by profile and warn on non-monotonic holdover error | `policy/timing-freshness.yaml`, `gateway/src/validators.py`, `gateway/tests/test_timing_freshness.py` | Enforced | Maintain deployment-specific freshness policies. | Maintain |
| PNT integrity, jam/spoof suspicion, nav source integrity | 5.7 | Future guidance only | `spec/semantics-contract.md` | Future | Implement only through approved PNT_STATUS or equivalent version branch. | Future |
| Units and geodesy | 6 | Schema constrains canonical geo fields and units; policy has quality/unit checks | `schema/*.json`, `policy/semantics.yaml`, `schema/README.md`, `conformance/must-fail.jsonl` | Enforced | Maintain invalid geo/unit fixtures. | Maintain |
| Measurement quality is separate from confidence | 6, 8 | v1.1.0 structured `quality` supports measurement error; confidence placement schema-enforced | `schema/zmeta-event-1.1.0.schema.json`, `schema/README.md`, `conformance/*.jsonl` | Partially Enforced | Add examples/tests that show observation quality feeding, but not replacing, inference confidence. | P2 |
| Confidence prohibited for observation/command/system | 8.1, 7 | Schema forbids top-level confidence on those event families; policy forbids payload confidence in observations | `schema/*.json`, `policy/semantics.yaml`, `conformance/must-fail.jsonl` | Enforced | Maintain negative fixtures. | Maintain |
| Confidence required for inference/fusion/state | 8.1, 7 | Schema requires top-level `confidence` for INFERENCE_EVENT, FUSION_EVENT, STATE_EVENT | `schema/*.json`, `conformance/*.jsonl`, adapter tests | Enforced | Maintain adapter tests for state/inference producers. | Maintain |
| Confidence must not increase during profile projection | 8.4, 10.2 | Gateway timing degradation can reduce confidence; no general H->M->L projection comparison test exists | `gateway/src/gateway.py`, `tools/test_workflow_end_to_end.py` | Partially Enforced | Add projection conformance cases comparing source and thinned events for confidence, TTL, precision, and field removal. | P0 |
| Trust score is separate from confidence | 8.5, 16 | Current stack has no trust score field; producer authority is policy-only | `policy/producer-authority.yaml`, `policy/routing.yaml` | Future | Do not add trust fields to v1.0; plan versioned trust/quarantine branch. | Future |
| Mandatory lineage for inference/fusion/state | 9.1 | Schema requires `lineage` and `lineage.based_on`; validators add parent consistency checks | `schema/*.json`, `policy/lineage.yaml`, `gateway/src/validators.py`, `gateway/tests/test_lineage_semantics.py` | Enforced | Maintain. | Maintain |
| Payload-local provenance cannot exceed envelope lineage | 9.1 | Policy rejects payload `based_on` outside envelope lineage | `policy/lineage.yaml`, `gateway/src/validators.py`, `gateway/tests/test_lineage_semantics.py` | Enforced | Maintain. | Maintain |
| Lineage resolvability is policy-only, with Profile L tolerance | 9.1, 10.1 | Policy ignores unresolved parents for L and warns for M/H when local state is available | `policy/lineage.yaml`, `gateway/src/validators.py`, `gateway/tests/test_lineage_semantics.py` | Enforced | Maintain by profile; avoid schema-level resolvability. | Maintain |
| `data_ref` links are evidence pointers, not lineage or raw payload | 9.3, Appendix A | v1.0 allows lightweight `data_ref`; v1.1.0 tightens pointer shape and xor with `data_refs`; state forbids raw refs | `schema/*.json`, `schema/README.md`, `examples/*.jsonl`, `conformance/*.jsonl` | Partially Enforced | Add explicit raw-data-absent/evidence status only in a future version; add current tests that state cannot carry `data_ref`. | P2 |
| Raw-data-absent mode | 9.4 | Contract guidance only; no `evidence_status` vocabulary | `spec/semantics-contract.md` | Future | Define evidence status in a versioned schema branch before implementation. | Future |
| Replay labels and scenario bundle identity | 9.5 | Replay tools exist, but no replay event labels or scenario manifest schema | `tools/replay.py`, `examples/*.jsonl` | Future | Keep as companion artifact first; add stable event references only after replay manifest design. | Future |
| Profile L/M/H event-type legality | 10.1 | Schema `profileExportConsistency`; policy `profiles.yaml`; validator `validate_profile` | `schema/*.json`, `policy/profiles.yaml`, `gateway/src/validators.py`, `conformance/*.jsonl` | Enforced | Maintain. | Maintain |
| Profile thinning without reinterpretation | 10.2 | Docs and gateway optional-field stripping exist; no formal field catalog/projection audit exists | `gateway/src/gateway.py`, `tools/measure_packet_size.py`, `spec/profile-compatibility.md` | Partially Enforced | Define a projection field catalog and conformance tests for allowed omissions/precision changes. | P0 |
| Emergency/L0 behavior | 10.3 | Future guidance only; H/M/L remain stable | `spec/semantics-contract.md` | Future | Do not add a fourth profile yet; prototype emergency behavior as projection policy in a future branch. | Future |
| Projection/thinning metadata | 10.4 | Not present in current event vocabulary | `spec/semantics-contract.md` | Future | Design `projection` metadata branch covering source profile, export profile, policy ID, omitted fields, precision changes, and reason codes. | Future |
| AI inference model name/version | 11.1, 11.2 | Inference payload requires model name/version | `schema/*.json`, `examples/*.jsonl`, `conformance/*.jsonl` | Enforced | Maintain. | Maintain |
| AI model family/hash/runtime/model card/drift/OOD/assurance | 11.3, 11.4 | Future guidance only | `spec/semantics-contract.md` | Future | Create MODEL_STATUS/ASSURANCE_EVENT or equivalent version branch before schema changes. | Future |
| Degraded AI inputs and confidence impacts | 11.4 | Timing degradation can reduce confidence; no AI-specific degraded-input flags | `gateway/src/gateway.py`, `spec/semantics-contract.md` | Future | Tie degraded input flags to future AI provenance schema and conformance. | Future |
| Compute elasticity without layer collapse | 12 | Contract guidance only; no compute tier/status vocabulary | `spec/semantics-contract.md`, `schema/zmeta-event-1.1.0.schema.json` for PLATFORM_STATUS partial health | Future | Define COMPUTE_STATUS or platform compute metrics in version branch; keep semantic layer rules unchanged. | Future |
| Fusion owns track identity; state is projection | 13.1, 14 | Schema requires fusion/state track fields and forbids track IDs in observations/inferences | `schema/*.json`, `policy/semantics.yaml`, `conformance/*.jsonl` | Enforced | Maintain. | Maintain |
| Track lifecycle states: new, active, stale, lost, merged, split, retired | 13.2 | Contract guidance only; no lifecycle subtype or payload block | `spec/semantics-contract.md` | Future | Define lifecycle actions as versioned fusion/state extension before implementation. | Future |
| Track confidence decay and stale display policy | 13.3, 14 | Timing policy can reject/degrade; no explicit track lifecycle decay policy | `policy/timing-freshness.yaml`, `gateway/src/gateway.py` | Partially Enforced | Add policy and conformance for stale/lost/retired state once lifecycle vocabulary exists. | Future |
| CoT/TAK egress is STATE_EVENT-only | 14.2 | Adapter returns `None` for non-state events; tests cover state-only projection | `adapters/egress/cot/zmeta_to_cot.py`, `adapters/egress/cot/test_zmeta_to_cot.py` | Enforced | Maintain; add pre-validation guidance for caller-supplied state events. | P2 |
| CoT/JREAP ingress must provide confidence and lineage | 14.2 | Ingress templates reject missing confidence/lineage and normalize timing | `adapters/ingress/cot/cot_to_zmeta_template.py`, `adapters/ingress/jreap/jreap_track_to_zmeta_template.py`, adapter tests | Enforced | Maintain adapter tests. | Maintain |
| Operator overrides and human confirmation | 14.3 | Future guidance only | `spec/semantics-contract.md` | Future | Define override event semantics before any UI/operator adapter implements it. | Future |
| Commands are bounded, idempotent, TTL-bound tasking | 15 | Schema and policy require task IDs, allowed task types, TTL fields, deconfliction, and TASK_ACK lifecycle | `schema/*.json`, `policy/semantics.yaml`, `gateway/src/validators.py`, `conformance/*.jsonl` | Enforced | Maintain. | Maintain |
| Command altitude prohibition | 15 | Schema and policy forbid altitude fields in command payload and target geo | `schema/*.json`, `policy/semantics.yaml`, `gateway/src/validators.py`, `conformance/must-fail.jsonl` | Enforced | Maintain. | Maintain |
| Command authorization is policy/gateway-only | 15 | Role, producer authority, routing, and command-path checks | `policy/roles.yaml`, `policy/producer-authority.yaml`, `policy/routing.yaml`, `gateway/src/validators.py`, `gateway/tests/test_producer_authority.py` | Enforced | Maintain deployment-specific allowlists; do not bake local authority into schema. | Maintain |
| Event dedupe, task dedupe, TASK_ACK dedupe | 4.1, 15 | Gateway state and validators detect duplicates; conformance/gateway tests cover task ack and command dedupe | `gateway/src/validators.py`, `gateway/src/gateway.py`, `gateway/tests/test_gateway_smoke.py` | Enforced | Maintain; revisit when signed counters are added. | Maintain |
| SCHEMA_VIOLATION is diagnostic, not trust/quarantine state | 16.4 | Policy reason codes and contract wording distinguish schema diagnostics from trust | `policy/semantics.yaml`, `policy/violation-codes.yaml`, `gateway/src/gateway.py`, `spec/semantics-contract.md` | Partially Enforced | Add conformance/docs examples showing `SCHEMA_VIOLATION` must not be used for quarantine/spoof labels. | P2 |
| Mesh signing, producer key identity, counters, spoof recovery, quarantine | 16 | Future guidance only | `spec/semantics-contract.md` | Future | Create integrity/trust branch with canonical signing, key registry, anti-replay windows, and quarantine semantics. | Future |
| UAS declared/signed/behavioral/RF/acoustic identity | 17 | Future guidance only; current CLASSIFICATION can label classes but not identity confidence model | `spec/semantics-contract.md`, `schema/*.json` | Future | Define IDENTITY or cooperative-ID observation/inference extension; Remote ID must remain evidence, not IFF truth. | Future |
| Coalition release, markings, redaction, cross-domain export audit | 18 | Future guidance only | `spec/semantics-contract.md` | Future | Create markings/release/projection branch plus guard conformance corpus. | Future |
| Data nutrition labels / trust summary | 19 | Future guidance only | `spec/semantics-contract.md` | Future | Define state-safe evidence summary after raw-data-absent vocabulary and projection metadata are approved. | Future |
| Extension namespace safety | 20 | Schema strictness and README reserve undefined modalities; no registry artifact | `schema/README.md`, `schema/*.json`, `spec/semantics-contract.md` | Partially Enforced | Add `spec/extension-registry.md` or machine-readable registry with reserved subtype names and adoption states. | P1 |
| v1.1.0 RF/EO/IR/ACOUSTIC/NETWORK feature contracts | 21.1 | v1.1.0 schema and examples enforce feature-specific contracts | `schema/zmeta-event-1.1.0.schema.json`, `examples/zmeta-v1.1-examples.jsonl`, `conformance/*.jsonl` | Enforced | Maintain and expand negative fixtures for future modalities. | Maintain |
| v1.1.0 SENSOR_STATUS and PLATFORM_STATUS | 21.2 | v1.1.0 schema enforces current status payloads; v1.0 rejects them | `schema/zmeta-event-1.1.0.schema.json`, `conformance/*.jsonl`, `gateway/tests/test_reason_codes.py` | Enforced | Maintain version discrimination. | Maintain |
| v1.1.0 expanded tasking remains bounded | 21.3 | v1.1.0 schema supports RETURN_TO_BASE, LAND, LOITER, SCAN_RF, TRACK_TARGET, and CHANGE_SENSOR_MODE with TTL/deconfliction boundaries | `schema/zmeta-event-1.1.0.schema.json`, `examples/zmeta-v1.1-examples.jsonl` | Enforced | Add more must-fail fixtures for each expanded task type before promotion. | P2 |
| Compact binary expands to canonical JSON before validation | 10, 23 | Compact codec expands to JSON; gateway decodes compact before schema/policy checks; roundtrip tests exist | `spec/compact-binary-mapping.md`, `zmeta_compact.py`, `gateway/src/gateway.py`, `gateway/tests/test_encoding_roundtrip.py` | Enforced | Add invalid compact-after-expansion negative fixture. | P2 |
| Compact Profile L must preserve semantics | 10, 23 | Compact mapping covers Profile L state/system/command and deterministic CBOR; no full semantic-diff conformance beyond roundtrip | `spec/compact-binary-mapping.md`, `zmeta_compact.py`, `examples/encoding-roundtrip.jsonl` | Partially Enforced | Add compact conformance that compares decoded canonical fields and rejects illegal Profile L event types. | P1 |
| Protobuf decoded JSON validation | 3.4, 23 | Protobuf decoder expands payload JSON; gateway validates decoded event; conversion CLI is projection-only | `spec/protobuf-encoding.md`, `schema/proto/zmeta_event_v1.proto`, `zmeta_proto.py`, `gateway/src/gateway.py`, `tools/convert_encoding.py` | Partially Enforced | Add explicit gateway/CLI negative tests for schema-invalid protobuf after decode. | P1 |
| Protobuf is not semantic authority | 3.4, 23 | Spec and proto comments say decoded events must pass JSON schema/policy | `spec/protobuf-encoding.md`, `schema/proto/zmeta_event_v1.proto`, `schema/README.md` | Enforced | Maintain until protobuf promotion decision. | Maintain |
| Validation CLI uses canonical dispatcher and policy pack | 3.1, 3.2 | CLI validates schema, role, profile, timing, semantics, lineage, producer authority, routing, and dedupe | `tools/validate.py`, `tools/validate_conformance.py` | Enforced | Maintain; add option to report section-to-rule mapping later. | P2 |
| Conformance classes are claimable by implementations | 22 | Tests exist by behavior, but no class manifest or certification matrix exists | `conformance/*.jsonl`, `gateway/tests/*.py`, `spec/semantics-contract.md` | Partially Enforced | Add machine-readable conformance class manifest and test selectors. | P1 |

## Prioritized Implementation Backlog

### P0 - Before Stack Hardening Release

| Item | Owner Surface | Rationale | Suggested Output |
|---|---|---|---|
| Recompute contract and release hashes after S0-02/S0-03 docs are approved | Release/gateway | The semantic contract changed and gateway hash gates can enforce stale hashes. | Updated hash values and release/checklist artifacts in a release-specific task. |
| Add profile projection semantic preservation tests | Conformance/gateway | The contract requires thinning without reinterpretation and confidence must not increase during projection. | H/M/L source-to-projection fixtures checking confidence, TTL, precision, omitted fields, track ID, and lineage. |
| Define a projection field catalog for current H/M/L thinning | Spec/conformance | Current optional-field stripping is configurable, but not tied to a contract-visible catalog. | `spec/profile-compatibility.md` or new conformance appendix that names permitted omissions and precision reductions. |

### P1 - Stack Hardening Backlog

| Item | Owner Surface | Rationale | Suggested Output |
|---|---|---|---|
| Create extension registry artifact | Spec/schema governance | Future names are described but not governed by a durable registry. | `spec/extension-registry.md` or machine-readable registry with reserved names, status, and owner. |
| Add conformance-class claim matrix | Conformance/docs | Contract defines ZMETA-* classes, but implementations cannot yet claim a class mechanically. | `conformance/classes.yaml` plus validation/test selectors. |
| Add invalid compact/protobuf-after-decode tests | Encoding/gateway | Roundtrip works; negative validation after decode should be explicit. | Must-fail fixtures and gateway/CLI tests for illegal event type, profile, and subtype after binary decode. |
| Add adapter layer-classification assertions | Adapter tests | Adapters are semantic boundaries and should prove they do not collapse observation/inference/state. | Per-adapter tests or shared adapter conformance harness. |
| Tighten CoT/JREAP projection preconditions | Adapter docs/tests | Egress adapters depend on valid STATE_EVENT input; this should be explicit and tested. | Projection tests that invalid state-with-raw-fields is rejected before or outside projection. |

### P2 - Documentation and Test Coverage

| Item | Owner Surface | Rationale | Suggested Output |
|---|---|---|---|
| Add examples for observation quality versus inference confidence | Examples/conformance | The contract distinguishes measurement quality from confidence; examples should make this visible. | Paired observation/inference examples with quality feeding confidence. |
| Add SCHEMA_VIOLATION diagnostic-only example | Policy/conformance | Prevent future misuse of schema violation as quarantine/trust state. | Example and must-fail/must-pass expectations for allowed reason codes. |
| Add event timestamp semantic notes per adapter | Adapter docs | Schema enforces format, not native-source semantic meaning. | README rows naming native time source used for `event.ts`. |
| Improve validation reports with contract section IDs | Tools/docs | Integrators will map failures faster if reports cite semantic sections. | Optional mapping table in `tools/check_compat.py` output or docs. |

### Future Version Branches

These are required by the hardened contract direction but must not be added to
v1.0 validation or v1.1.0 experimental schemas without explicit version approval:

| Future Branch | Contract Sections | Required Surfaces |
|---|---|---|
| Markings, release, and cross-domain export | 18 | Schema branch, release policy pack, guard conformance corpus, redaction/projection examples. |
| Integrity, signing, anti-replay, mesh trust, quarantine | 16 | Canonical signing rules, key registry, counters/windows, policy, gateway checks, replay/spoof tests. |
| AI runtime assurance | 11 | MODEL_STATUS/ASSURANCE_EVENT or equivalent, model card/hash/runtime fields, drift/OOD tests. |
| Raw-data-absent evidence status | 9, 19 | Evidence status vocabulary, data retention/release behavior, state-safe trust summaries. |
| Projection metadata | 10, 18, 19 | Source/export profile, policy ID, omitted fields, precision changes, reason codes, replay behavior. |
| Compute/PNT status | 5, 12 | COMPUTE_STATUS/PNT_STATUS or equivalent, policy caps, degraded confidence behavior. |
| UAS identity and cooperative ID | 17 | IDENTITY inference or COOPERATIVE_ID observation semantics, Remote ID evidence mapping, behavioral trust tests. |
| Track lifecycle | 13 | Lifecycle event/subtype vocabulary for stale, lost, merged, split, retired, override semantics. |
| Data nutrition labels | 19 | State-safe evidence summary fields and operator projection tests. |

## Deferred Issues Confirmed During S0-03

- The current stack has strong schema and reference policy enforcement for
  locked v1.0 semantics, but projection/thinning semantic preservation is not
  yet proven end-to-end by conformance.
- Extension governance is currently documentary. A registry artifact is needed
  before future semantics start landing.
- Binary encoding roundtrip tests exist; explicit invalid-after-decode tests
  should be added for compact and protobuf to make the "decode before validate"
  rule hard to regress.
- Conformance class definitions exist in the contract but not as a
  machine-readable claim/test matrix.
- Several future areas are intentionally not current gaps: markings, mesh trust,
  UAS identity, raw-data-absent status, data nutrition labels, emergency/L0,
  compute tier, PNT integrity, model assurance, and track lifecycle events.
