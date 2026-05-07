# S1-01A v1.0 Baseline Verification and Targeted Schema Gap Plan

**Work item:** S1-01A - v1.0 Baseline Verification and Targeted Schema Gap Plan

**Date:** 2026-05-07

**Scope:** Documentation-only baseline verification of locked v1.0 behavior
against `spec/semantics-contract.md` and
`docs/zmeta_contract_to_stack_crosswalk.md`.

**Verification command run:** `python tools\validate_conformance.py --strict`

**Result:** `conformance ok`

## Executive Finding

No targeted v1.0 JSON Schema implementation change is recommended from this
review. The current v1.0 baseline already enforces the core locked schema
contract: version isolation, event vocabulary, subtype/payload matching,
UUIDv7, UTC-Z timestamps, confidence placement, lineage requirements, layer
separation, bounded command/tasking rules, system payload consistency, and
profile/event-type legality.

The remaining P0 hardening item is not a general schema gap. It is profile
projection preservation: proving that H/M/L thinning never rewrites meaning,
increases confidence, increases TTL, increases precision, changes units, or
loses required lineage. That work belongs in S1-02.

S1-01B is not needed unless a later review uncovers a concrete v1.0 schema
failure. Proceed directly to S1-02.

## A. v1.0 Baseline Confirmed

| v1.0 Rule | Current Enforcement | File(s) / Evidence | Status |
|---|---|---|---:|
| Exact `zmeta_version: "1.0"` | Version-specific schema uses exact const; canonical dispatcher selects by `oneOf`. | `schema/zmeta-event.schema.json`, `schema/zmeta-event-1.0.schema.json`, `schema/README.md`, `gateway/tests/test_schema_version_discrimination.py` | Confirmed |
| Canonical dispatcher isolation | Dispatcher validates v1.0 and v1.1.0 against separate branches; aliases are rejected by normative validation. | `schema/zmeta-event.schema.json`, `schema/README.md`, `tools/validate.py`, `tools/validate_conformance.py` | Confirmed |
| UUIDv7 event identity | `event.event_id`, lineage parents, and fusion members use UUIDv7 regex constraints. | `schema/zmeta-event-1.0.schema.json`, `zmeta_uuid.py`, `conformance/*.jsonl`, `gateway/tests/test_schema_version_discrimination.py` | Confirmed |
| UTC trailing-Z timestamps | Shared `utcDateTime` pattern requires UTC `Z`; offsets and timezone-less strings fail. | `schema/zmeta-event-1.0.schema.json`, `schema/README.md`, `gateway/tests/test_schema_version_discrimination.py`, `conformance/must-fail.jsonl` | Confirmed |
| Event type vocabulary | v1.0 permits only OBSERVATION_EVENT, INFERENCE_EVENT, FUSION_EVENT, STATE_EVENT, COMMAND_EVENT, and SYSTEM_EVENT. | `schema/zmeta-event-1.0.schema.json`, `spec/semantics-contract.md` Section 7.2 | Confirmed |
| Subtype vocabulary | v1.0 subtype namespaces are bounded by event type. | `schema/zmeta-event-1.0.schema.json`, `spec/semantics-contract.md` Section 7.3, `gateway/tests/test_schema_version_discrimination.py` | Confirmed |
| Subtype/payload discriminator matching | Conditional schema rules require subtype to match `payload.modality`, `payload.inference_type`, `payload.task_type`, or `payload.system_type`; fusion/state fixed subtypes are enforced. | `schema/zmeta-event-1.0.schema.json`, `conformance/must-fail.jsonl` | Confirmed |
| Confidence required/prohibited by event type | INFERENCE_EVENT, FUSION_EVENT, STATE_EVENT require top-level `confidence`; OBSERVATION_EVENT, COMMAND_EVENT, SYSTEM_EVENT prohibit it. | `schema/zmeta-event-1.0.schema.json`, `gateway/tests/test_schema_version_discrimination.py`, `conformance/*.jsonl` | Confirmed |
| Lineage required for INFERENCE_EVENT, FUSION_EVENT, STATE_EVENT | Schema requires envelope `lineage` and `lineage.based_on` for derived layers. | `schema/zmeta-event-1.0.schema.json`, `gateway/tests/test_lineage_semantics.py` | Confirmed |
| OBSERVATION_EVENT forbidden fields | Schema and policy prohibit track/identity/classification/confidence fields at the observation payload and feature levels, with recursive policy checks for configured forbidden keys. | `schema/zmeta-event-1.0.schema.json`, `policy/semantics.yaml`, `gateway/src/validators.py`, `gateway/tests/test_gateway_smoke.py` | Confirmed |
| INFERENCE_EVENT forbidden track/fusion/state fields | Schema rejects `track_id`, `members`, and `estimated_state` in inference payload and claim. | `schema/zmeta-event-1.0.schema.json`, `gateway/tests/test_schema_version_discrimination.py`, `conformance/must-fail.jsonl` | Confirmed |
| FUSION_EVENT required `track_id` and `members` | Schema requires `track_id`, `members`, `stability`, and `last_seen_ts`; member IDs are UUIDv7. | `schema/zmeta-event-1.0.schema.json`, `conformance/must-pass.jsonl` | Confirmed |
| STATE_EVENT raw observation field prohibition | Schema rejects raw observation fields at state payload root and under `payload.extensions`; conformance includes negative state raw-field examples. | `schema/zmeta-event-1.0.schema.json`, `gateway/tests/test_schema_version_discrimination.py`, `conformance/must-fail.jsonl` | Confirmed |
| COMMAND_EVENT bounded tasking and altitude prohibition | Schema enforces task ID, task type, TTL, `requires_deconfliction: true`, task-specific geometry, 2D target geo, and common altitude-field bans. | `schema/zmeta-event-1.0.schema.json`, `policy/semantics.yaml`, `gateway/tests/test_schema_version_discrimination.py`, `adapters/egress/mavlink/test_mavlink_intent.py` | Confirmed |
| SYSTEM_EVENT subtype/payload consistency | Schema enforces LINK_STATUS, TIME_STATUS, SCHEMA_VIOLATION, and TASK_ACK payload discriminators and required metrics. | `schema/zmeta-event-1.0.schema.json`, `policy/semantics.yaml`, `gateway/tests/test_reason_codes.py`, `conformance/*.jsonl` | Confirmed |
| Profile/event-type legality | Schema `profileExportConsistency` and policy `profiles.yaml` enforce H/M/L event-type legality when profile is present or runtime profile is selected. | `schema/zmeta-event-1.0.schema.json`, `policy/profiles.yaml`, `gateway/src/validators.py`, `conformance/*.jsonl` | Confirmed |
| Timing quality and TIME_STATUS freshness | Schema enforces timing-quality shape where present; policy/gateway require operational timing quality or fresh TIME_STATUS by profile. | `schema/zmeta-event-1.0.schema.json`, `policy/semantics.yaml`, `policy/timing-freshness.yaml`, `gateway/src/validators.py`, `gateway/tests/test_timing_freshness.py` | Confirmed by policy/runtime |
| Producer authority and routing | Role, producer authority, and command routing checks are active outside schema. | `policy/roles.yaml`, `policy/producer-authority.yaml`, `policy/routing.yaml`, `gateway/src/validators.py`, `gateway/tests/test_producer_authority.py` | Confirmed by policy/runtime |
| Compact/protobuf are projections | Compact and protobuf decode to canonical JSON before schema/policy enforcement; roundtrip tests exist. | `spec/compact-binary-mapping.md`, `spec/protobuf-encoding.md`, `zmeta_compact.py`, `zmeta_proto.py`, `gateway/src/gateway.py`, `gateway/tests/test_encoding_roundtrip.py` | Confirmed |
| CoT state projection boundary | CoT egress is STATE_EVENT-only; CoT ingress emits STATE_EVENT/TRACK_STATE and requires confidence and lineage. | `adapters/egress/cot/zmeta_to_cot.py`, `adapters/ingress/cot/cot_to_zmeta_template.py`, adapter tests | Confirmed |

## B. Actual Schema-Enforceable Gaps

No concrete v1.0 JSON Schema gap was identified that should be fixed before
S1-02.

The following were reviewed and rejected as schema-change candidates:

| Candidate | Decision | Rationale |
|---|---|---|
| Producer authority in JSON Schema | Do not add | Producer authority depends on deployment-specific producer IDs and roles. It belongs in policy/runtime. |
| Lineage parent availability in JSON Schema | Do not add | A single event document cannot know local event-store contents. Policy/gateway validation is the right surface. |
| Timing freshness in JSON Schema | Do not add | Freshness requires event history and current profile/runtime context. |
| Profile projection preservation in JSON Schema | Do not add | Projection honesty requires comparing source and projected events. This belongs in S1-02 conformance/policy/gateway tests. |
| Confidence degradation formulas in JSON Schema | Do not add | Exact degradation is policy and producer behavior, not structural event validity. |
| Global track ID uniqueness or non-reuse in JSON Schema | Do not add | Requires event history and track lifecycle state. |
| Append-only event-store immutability in JSON Schema | Do not add | Requires storage/gateway behavior, not single-document validation. |
| v1.1.0 structured quality into v1.0 | Do not add | v1.0 intentionally permits generic `payload.quality`; v1.1.0 formalizes the structured contract. |
| v1.1.0 formal `data_ref`/`data_refs` behavior into v1.0 | Do not add | v1.0 permits lightweight pointers. v1.1.0 tightens hash/window/xor/raw-data rules. |
| v1.1.0 modality feature contracts into v1.0 | Do not add | v1.0 already includes EO/IR/ACOUSTIC/NETWORK subtype names with generic features. v1.1.0 adds stricter feature contracts without narrowing v1.0. |

## C. Rules That Must Remain Policy/Runtime

These rules must not be moved into JSON Schema:

| Rule | Correct Surface | Reason |
|---|---|---|
| Producer authority | Policy/gateway | Deployment-specific producer names, roles, and authority boundaries belong in `policy/producer-authority.yaml`, `policy/roles.yaml`, and `policy/routing.yaml`. |
| Lineage resolvability | Policy/gateway/event store | Depends on what parent events are locally available and on the active profile. |
| Parent event availability | Runtime/event store | Cannot be checked from a single JSON document. |
| Timing freshness | Policy/gateway | Requires latest TIME_STATUS cache and profile-specific thresholds. |
| Holdover monotonicity | Policy/gateway | Requires previous timing state for the same source identity. |
| Command authorization and deconfliction | Policy/gateway/adapter | Depends on command path, producer authorization, mission policy, and receiving autonomy. |
| Profile projection behavior | Gateway/conformance | Requires comparing source and projected event fields. |
| Confidence degradation policy | Policy/gateway/producer | Formulas and caps are deployment/mission policy, not static syntax. |
| Global track ID uniqueness | Fusion service/event store | Requires track history and lifecycle state. |
| Append-only event store behavior | Gateway/store/conformance | Requires persistence semantics, not per-event schema. |
| Transport behavior | Gateway/encoding/conformance | Transport is explicitly non-semantic; encodings must decode before validation. |
| Replay/quarantine decisions | Future policy/runtime | Replay, spoof suspicion, and quarantine are future trust semantics, not current v1.0 schema vocabulary. |

## D. v1.0 / v1.1.0 Boundary Check

| v1.1.0 Area | v1.0 Boundary Result | Evidence / Notes |
|---|---|---|
| SENSOR_STATUS | Does not validate as v1.0 | v1.0 system subtype enum excludes SENSOR_STATUS; conformance must-fail lines cover `zmeta_version: "1.0"` with SENSOR_STATUS. |
| PLATFORM_STATUS | Does not validate as v1.0 | v1.0 system subtype enum excludes PLATFORM_STATUS; conformance and compatibility tests cover this boundary. |
| Expanded command task types | Do not validate as v1.0 | v1.0 command task enum permits only GOTO, ORBIT, HOLD, SEARCH_BOX. Test code asserts v1.1-only task tokens are absent from v1.0 schema. |
| `error_ellipse_m` | Does not validate as v1.0 | v1.0 `geo` is strict and excludes `error_ellipse_m`; schema tests include v1.0 failure and v1.1.0 success. |
| Structured quality fields | Partially boundary-sensitive by design | `payload.quality` exists in v1.0 as a generic object. v1.1.0 formalizes structured measurement-error, calibration, and geo-status rules. A v1.0 event may carry a generic `quality` object, but consumers must not treat it as the v1.1.0 structured contract unless `zmeta_version: "1.1.0"` is selected. |
| Formal `data_ref` / `data_refs` behavior | Partially boundary-sensitive by design | v1.0 permits lightweight `data_ref` and `data_refs` pointers with `ref_id`; v1.1.0 adds stricter xor, hash, paired time-window, no-raw-data, and shape rules. Do not backport those stricter rules into locked v1.0. |
| v1.1 modality feature contracts | Partially boundary-sensitive by design | v1.0 already permits RF, EO, IR, ACOUSTIC, and NETWORK subtype names with generic features. v1.1.0 formalizes feature contracts such as EO `roi_px`, IR `band`, ACOUSTIC `spl_db`, and NETWORK `protocol`. This is not accidental leakage; it is a v1.0 generic-extension surface plus a v1.1.0 stricter interpretation. |
| Reserved future modalities such as RADAR, LIDAR, MAGNETIC, SEISMIC, CYBER, SIGINT | Do not validate as v1.0 or v1.1.0 observation modalities | Conformance and schema tests reject reserved modalities until a future branch defines them. |

Boundary conclusion:
- No core v1.1.0-only subtype or command vocabulary leakage into v1.0 was found.
- Some v1.1.0-shaped observation detail can be structurally accepted by v1.0
  only because v1.0 intentionally allows generic observation extensions. That
  must be documented/tested as "structurally valid as generic v1.0 data, not
  semantically adopted as v1.1.0."

## E. Test Coverage Gaps

The current baseline has strong test coverage. The gaps below are not blockers
for S1-02 and do not justify S1-01B unless the project wants a test-only
maintenance pass.

### Schema Tests

- Add explicit boundary tests documenting that v1.0 can structurally carry
  generic `quality`, `data_ref`, `data_refs`, and non-RF observation feature
  details without adopting the v1.1.0 stricter semantics.
- Add explicit negative tests for top-level confidence on OBSERVATION_EVENT and
  SYSTEM_EVENT. COMMAND_EVENT confidence is already tested.
- Keep adding v1.1.0-only token absence tests whenever new extension vocabulary
  is proposed.

### Policy Tests

- Existing tests cover producer authority, timing freshness, lineage, routing,
  and dedupe. Add policy tests only when projection preservation, lifecycle,
  trust/quarantine, or new producer authority packs are implemented.
- Add a diagnostic-only SCHEMA_VIOLATION test later to reinforce that
  SCHEMA_VIOLATION is not a trust/quarantine label.

### Gateway Tests

- Gateway tests cover validation flow, role/profile rejection, timing behavior,
  command dedupe, contract hashes, and CoT emission. S1-02 should add projection
  comparison tests around optional-field stripping and confidence/TTL behavior.

### Adapter Tests

- CoT ingress/egress tests cover state projection, confidence, lineage, and
  timestamp normalization.
- MAVLink implementation uses `payload.quality` for platform-state metadata,
  which is consistent with the state raw-feature prohibition. The MAVLink README
  still describes several values as `payload.features.*`; that remains D-001 and
  should be fixed as adapter documentation cleanup, not schema work.
- Adapter layer-classification tests should be broadened later so each adapter
  proves it emits OBSERVATION_EVENT, INFERENCE_EVENT, STATE_EVENT, or
  SYSTEM_EVENT according to semantic authorship.

### Encoding Roundtrip Tests

- CBOR, compact, and protobuf roundtrip and decoder-bound tests exist.
- Invalid-after-decode tests for compact/protobuf remain D-007. These are
  important, but they are encoding/gateway conformance work, not v1.0 schema
  repair.

### Conformance Fixtures

- `conformance/must-pass.jsonl` and `conformance/must-fail.jsonl` cover the
  current v1.0/v1.1.0 baseline and `validate_conformance.py --strict` passes.
- S1-02 should add projection-preservation conformance fixtures rather than
  broad schema fixtures.

## F. Defer-to-S1-02 Items

These are explicitly deferred to S1-02: Profile Projection Preservation Field
Catalog and Conformance Suite.

| S1-02 Item | Why It Is Not S1-01A Schema Work |
|---|---|
| Same `event_id` preservation during projection | Requires source/projection comparison. |
| Confidence never increases | Requires comparing source and projected event or policy-degraded event. |
| TTL never increases | Requires comparing source and projected state/command TTL. |
| Precision never increases | Requires profile-specific numeric precision policy and before/after values. |
| Units never change | Requires semantic comparison and field catalog, not just syntax. |
| Allowed optional field omissions | Requires a profile field catalog. |
| Source-authored fields not rewritten | Requires gateway/adapter behavior checks. |
| Lineage preserved or unresolved according to profile policy | Requires source/projection context and profile policy. |
| Profile L compact expansion equivalence | Requires binary decode plus canonical JSON comparison and validation. |

S1-02 should produce at minimum:
- A field catalog for H/M/L projection.
- Golden source/projected fixture pairs.
- Conformance checks for identity, lineage, units, precision, confidence, TTL,
  and permitted omissions.
- Compact Profile L decoded-equivalence tests.

## G. Recommended Next Work Items

### S1-01B Recommendation

Do not create S1-01B now. No targeted v1.0 schema or required test fix was found
that should block profile projection work.

If the project later wants a test-only cleanup, S1-01B could be scoped narrowly
to boundary tests for v1.0 generic observation extensions versus v1.1.0 formal
contracts. That is useful but not required before S1-02.

### Proceed to S1-02

Recommended next work item:

**S1-02 - Profile Projection Preservation Field Catalog and Conformance Suite**

Primary deliverables:
- Define the allowed H/M/L projection field catalog.
- Add conformance fixtures for H-to-M and H/M-to-L thinning.
- Prove confidence, TTL, precision, units, identity, lineage, and source fields
  are preserved or conservatively reduced.
- Include compact Profile L expansion equivalence.

## Final Baseline Decision

The v1.0 baseline is stable enough to proceed. Do not broadly edit schemas.
Move directly to S1-02.
