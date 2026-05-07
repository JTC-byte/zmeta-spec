# S1-06 Profile Precision / Quantization Policy Floors Plan

Status: COMPLETE
Date: 2026-05-07
Scope: Plan only. No schemas, policy YAML files, validators, gateway runtime,
codecs, adapters, extension registry artifacts, conformance class manifests,
semantic contract text, examples, release hashes, or event vocabulary were
changed.

## A. Current Precision / Quantization Landscape

ZMeta already has strong semantic boundaries for profiles, but it does not yet
have a machine-readable precision policy that tells exporters how coarse Profile
M/L numeric values should be.

Current enforced behavior:

- JSON Schema enforces numeric ranges, required fields, event family placement,
  subtype/payload matching, UUIDv7 identity, UTC `Z` timestamps, command
  altitude prohibition, STATE_EVENT raw-field prohibition, and v1.0/v1.1.0
  version dispatch.
- Field naming and unit conventions are defined by suffixes and payload
  contracts: `_m`, `_mps`, `_hz`, `_dbm`, `_deg`, and `_ms` fields preserve
  units and cannot be silently rescaled.
- `policy/profiles.yaml` defines Profile L/M/H event-type legality. Profile L
  carries STATE_EVENT, SYSTEM_EVENT, and COMMAND_EVENT; Profile M adds
  OBSERVATION_EVENT and FUSION_EVENT; Profile H allows all valid event families.
- `conformance/profile_projection_field_catalog.yaml` classifies fields as
  required, optional removable, precision reducible, confidence reducible, TTL
  reducible, never mutable, contextual, and prohibited in specific cases.
- `tools/validate_projection.py` compares source/projected event pairs and
  enforces identity preservation, semantic layer preservation, source
  preservation, lineage preservation, unit preservation, confidence
  non-increase, TTL non-increase, precision non-increase, and catalog-governed
  optional omissions.
- Confidence non-increase is enforced by projection fixtures and policy/gateway
  checks where timing degradation applies.
- TTL non-increase is enforced for `payload.valid_for_ms` projection cases.
- Timing quality policy requires or falls back to TIME_STATUS depending on
  profile/event type and detects stale timing status according to
  `policy/timing-freshness.yaml`.
- Gateway export behavior can stamp profile/timing fields and strip configured
  optional dotted paths, but it does not apply a field-family quantization
  policy.
- Compact Profile L is a wire-level mapping that expands back to canonical JSON.
  It improves packet density but does not define semantic precision policy.
- `tools/measure_packet_size.py` measures JSON, CBOR, compact CBOR, and protobuf
  size, optionally stripping dotted paths, but it does not decide which
  precision reductions are allowed or required.
- Compact/protobuf decoded validation and encoding-negative tests prove encoded
  forms cannot bypass canonical validation.
- Current examples and projection fixtures include representative precision
  reductions, such as H/M state geo values rounded for L output, but those
  examples are not governed by a reusable profile precision artifact.

Remaining undefined behavior:

- Profile-specific precision ceilings for numeric field families.
- Utility floors below which an exported event becomes operationally misleading.
- Field-family-specific quantization steps.
- Conservative rounding direction by field semantics.
- How packet budget interacts with optional omission versus required-field
  precision.
- Whether precision reductions should require quality/confidence/uncertainty
  adjustment.
- How gateways/exporters should report inability to satisfy both packet budget
  and utility floor.

## B. Problem Statement

Precision non-increase is necessary but not sufficient. It prevents an exporter
from inventing detail, but it does not say how much detail each profile should
preserve.

Risks without profile precision policy:

- Profile L/M/H producers can produce inconsistent fidelity while all passing
  schema and projection checks.
- Low-bandwidth exports can imply false precision by retaining unnecessary
  decimals without exposing degraded context.
- Over-thinning can make a track, command target, timing status, or RF
  observation operationally useless.
- Packet budgets can be missed because exporters keep decimals that do not
  materially improve utility.
- Coordinate jitter can appear when different gateways use inconsistent
  rounding grids across updates.
- Confidence or TTL can be rounded in a non-conservative direction.
- Error bounds and timing uncertainty can be rounded down and appear more
  certain than the source.
- RF/geo/timing values can be reduced without reflecting changed quality or
  confidence.
- Hidden defaults, such as zero-filled coordinates, can appear as valid-looking
  precision.

The policy goal is not to make every deployment use the same mission precision.
It is to define an auditable mechanism for profile-specific precision ceilings,
utility floors, rounding modes, and failure behavior.

## C. Terminology

- `precision ceiling`: maximum detail permitted for a field under a target
  profile. Example: Profile L may permit no more than a specified lat/lon grid.
- `utility floor`: minimum detail required for the event to remain useful and
  safe for the target profile and event type.
- `quantization step`: allowed increment, bucket, or grid size used to reduce
  precision.
- `rounding mode`: deterministic method used to map source values to lower
  precision values.
- `conservative rounding`: rounding direction that avoids overstating certainty,
  validity, freshness, or operational precision.
- `precision non-increase`: projected value cannot be more specific than the
  source value.
- `profile policy`: deployment or conformance rule that governs profile export
  precision without changing schema vocabulary.
- `semantic immutability`: source-authored identity, units, meaning, lineage,
  authority, and event layer cannot be changed by precision policy.

Recommended naming:

- Use `precision_ceiling` for maximum allowed detail.
- Use `utility_floor` for minimum allowed usefulness.
- Use `quantization_step` for concrete increments.
- Use `rounding_mode` for deterministic method and direction.

## D. Design Principles

- Precision policy is a profile/export policy, not a schema change.
- Source-authored identity and authority fields are never quantized or
  rewritten: `event.event_id`, `event.event_type`, `event.event_subtype`,
  `event.ts`, `source.platform_id`, `source.node_role`, `source.producer`,
  `payload.track_id`, and `lineage`.
- Units never change.
- Coordinate semantics never change. WGS-84 latitude/longitude and HAE altitude
  remain WGS-84/HAE after quantization.
- Confidence may be preserved or lowered, never increased.
- `payload.valid_for_ms` may be preserved or shortened, never increased.
- Error bounds and uncertainty estimates round conservatively upward.
- Confidence-like certainty values round conservatively downward.
- Required fields may not be removed.
- Optional fields may be removed only if the projection catalog and profile
  policy allow removal.
- Precision policy is not coalition release policy, trust policy, emergency
  behavior, or UI role policy.
- Encodings remain projections. Compact CBOR and protobuf do not define
  semantic precision.
- Precision changes that alter semantic meaning require a new event with new
  lineage, not a same-event projection.

## E. Field Family Review

### 1. Never Mutable / Never Quantized

Fields:

- `zmeta_version`
- `event.event_id`
- `event.event_type`
- `event.event_subtype`
- `event.ts`
- `source.platform_id`
- `source.node_role`
- `source.producer`
- `lineage.based_on`
- `lineage.transform`
- `payload.track_id`
- discriminator fields such as `payload.modality`, `payload.inference_type`,
  `payload.task_type`, and `payload.system_type`

Policy behavior: preserve exactly. These fields are outside precision policy.
Changing them is projection failure or a new semantic event.

### 2. Optional Export Metadata

Fields:

- `event.t_receive`
- `event.t_publish`
- `profile`

Policy behavior: preserve or omit only when the catalog and profile export
policy permit. Do not quantize timestamps unless a future versioned rule
explicitly defines publication-time redaction. `profile` must match the target
profile when present.

### 3. Geospatial

Fields:

- `payload.geo.lat`
- `payload.geo.lon`
- `payload.geo.alt_m`
- `payload.target_geo.lat`
- `payload.target_geo.lon`
- command geometry coordinates
- future `geo.error_ellipse_m` and related v1.1.0 uncertainty fields

Policy behavior: permit quantization. Require deterministic grid or decimal
policy by target profile. Required geo fields remain all-or-nothing: never emit
partial or zero-filled geo. Command target/geometry precision should have a
stricter utility floor than operator display state because command safety depends
on target semantics.

### 4. Motion and Direction

Fields:

- `payload.heading_deg`
- `payload.speed_mps`
- `payload.bearing.az_deg`
- `payload.bearing.el_deg`

Policy behavior: permit quantization when present. Preserve units and legal
ranges. Do not wrap or normalize in a way that changes meaning. Coarser
heading/bearing may require confidence or quality adjustment if operationally
material.

### 5. Time and TTL

Fields:

- `payload.valid_for_ms`
- `payload.t_start`
- `payload.t_end`
- `payload.timing_quality.*`
- TIME_STATUS `payload.metrics.est_error_ms`
- `payload.metrics.last_sync_ts`

Policy behavior:

- `payload.valid_for_ms` can only be preserved or shortened.
- `event.ts` remains immutable.
- Time uncertainty and error estimates round up.
- `last_sync_ts` and event time should not be rounded in same-event projection.
- RF observation `t_start`/`t_end` are source-authored measurement bounds and
  should usually preserve exactly or omit the entire observation if target
  profile cannot carry it.

### 6. RF and Measurement Features

Fields:

- `payload.features.center_freq_hz`
- `payload.features.bandwidth_hz`
- `payload.features.power_dbm`
- `payload.features.signature_hash`
- measurement quality fields

Policy behavior: Profile M/H observation exports may quantize numeric RF
features. Preserve units and measurement meaning. `signature_hash` is identity
or evidence-like data and should preserve exactly or be omitted only if the
catalog allows. Quantization of RF frequency/bandwidth/power should account for
sensor resolution and mission use; it should not convert units or imply
narrower windows.

### 7. Confidence and Quality

Fields:

- top-level `confidence`
- `payload.quality`
- v1.1.0 structured quality fields
- model confidence-like fields if present in future claims

Policy behavior: top-level confidence rounds down or preserves. Quality fields
with error, uncertainty, or age semantics round conservatively upward. Quality
fields with certainty semantics round downward. Mixed quality objects need
field-specific policy rather than object-wide rounding.

### 8. Display / String Fields

Fields:

- `payload.class`
- `payload.source_summary`
- UI/rendering `extensions`

Policy behavior: preserve exactly, truncate only under explicit field policy, or
omit when catalog/profile allows. Do not create new class labels or summarize in
a way that changes meaning. UI/rendering extension precision remains outside
core v1.0 policy unless a future extension branch adopts it.

## F. Candidate Profile Precision Policy

The following values are candidate defaults requiring human review. They should
not be treated as final operational policy.

| Field family | Profile H candidate | Profile M candidate | Profile L candidate |
| --- | --- | --- | --- |
| `payload.geo.lat/lon` | Preserve source precision within schema | Grid or decimal ceiling around 1e-4 deg | Grid or decimal ceiling around 1e-2 to 1e-3 deg, mission reviewed |
| `payload.geo.alt_m` | Preserve source precision | 1 m or 5 m step | 10 m step unless mission requires tighter |
| `payload.target_geo.lat/lon` | Preserve source precision | 1e-5 to 1e-4 deg ceiling | 1e-4 to 1e-3 deg ceiling, stricter than display state if command safety requires |
| Command geometry | Preserve source precision | Mission-reviewed grid | Mission-reviewed grid; fail/omit command if unsafe |
| Heading/bearing | Preserve source precision | 1 deg or 5 deg step | 5 deg or 10 deg step |
| Speed | Preserve source precision | 0.5 m/s or 1 m/s step | 1 m/s or 5 m/s step |
| Confidence | Preserve or floor to source decimals | floor to 0.01 | floor to 0.05 or 0.1 if materially degraded |
| `valid_for_ms` | Preserve or shorten | bucket downward to 100 ms or 1 s | bucket downward to 1 s or mission TTL bucket |
| Timing error | Preserve or round up | round up to 1 ms or 10 ms | round up to 10 ms or 100 ms |
| RF center frequency | Preserve source precision | mission/sensor step, e.g. kHz/MHz bucket | usually omitted in L because OBSERVATION_EVENT is not Profile L; if future L supports RF summary, use mission bucket |
| RF bandwidth | Preserve source precision | mission/sensor step | usually omitted in L under current v1.0 profile legality |
| RF power | Preserve source precision | 1 dB or 5 dB step | usually omitted in L under current v1.0 profile legality |
| `source_summary` | Preserve | preserve or cap list length | omit or cap to one coarse source label |
| `payload.class` | Preserve | preserve or omit | preserve only if operationally stable; otherwise omit |

Profile H should usually preserve source precision, subject to schema and policy.
Profile M should reduce precision enough to control bandwidth but retain enough
detail for constrained IP workflows. Profile L should prioritize required
state/command/system semantics, lineage, timing quality, and packet budget over
optional detail.

## G. Conservative Rounding Rules

Field-specific direction:

- Confidence: floor or preserve. Never round half-up if that can increase the
  value.
- TTL / `valid_for_ms`: floor to bucket or shorten. Never ceil.
- Error bounds: ceil to bucket. Never floor.
- Timing uncertainty: ceil to bucket.
- Geospatial coordinates: deterministic grid rounding. The policy must state
  whether nearest-grid rounding is acceptable or whether cell-center/cell-index
  behavior is needed. If grid rounding increases spatial uncertainty, quality,
  confidence, or uncertainty fields should reflect it.
- RF frequency/bandwidth/power: preserve units and quantize according to sensor
  resolution and mission use. Frequency/bandwidth quantization must not imply a
  narrower spectral window than the source.
- Speed/heading/bearing: quantize to coarser representation while preserving
  valid ranges. Heading wrap-around must be deterministic.
- String/list fields: omit, cap, or preserve. Do not synthesize new labels.

Recommended rounding modes for S1-06B policy vocabulary:

- `floor`
- `ceil`
- `nearest_grid`
- `truncate_decimals`
- `omit`
- `preserve`
- `reject_if_below_utility_floor`

## H. Profile Utility Floors

Precision ceilings control maximum detail. Utility floors prevent over-thinning.

Candidate utility floor model:

- Profile L STATE_EVENT / TRACK_STATE minimum useful set:
  - event identity, source identity, target profile, `payload.track_id`,
    `payload.valid_for_ms`, top-level `confidence`, lineage, and timing quality
    or current TIME_STATUS fallback.
  - `payload.geo` if the state is position-bearing; omit the event rather than
    zero-fill or over-thin below mission utility.
- Profile L COMMAND_EVENT minimum useful set:
  - task identity, task type, deconfliction requirement, TTL, timing quality, and
    target/geometry precision sufficient for command safety.
  - If target quantization makes the command unsafe or ambiguous, reject export
    rather than emit a misleading command.
- Profile L SYSTEM_EVENT / TIME_STATUS minimum useful set:
  - time source, sync state, estimated error, and last sync time. Timing error
    rounds up, not down.
- Profile M OBSERVATION_EVENT minimum useful set:
  - modality, required feature contract fields, source, timing quality, and
    measurement quality sufficient to interpret reduced RF/geo precision.
- Profile H utility floor:
  - generally full fidelity. Policy should warn if H export applies avoidable
    precision reduction without an explicit deployment reason.

Utility floors should live in policy and conformance, with gateway/exporter
configuration selecting the active policy. They should not be schema-only
because operational usefulness is mission- and deployment-dependent.

## I. Packet Budget Interaction

Profile L compact packets have packet-size goals, but packet pressure must not
strip required semantics.

Recommended packet-budget order:

1. Validate source event first.
2. Select target profile and event legality.
3. Omit optional fields allowed by catalog/profile policy.
4. Apply profile precision ceilings with conservative rounding.
5. Revalidate projection preservation and precision policy.
6. Measure packet size with `tools/measure_packet_size.py` or equivalent
   library logic.
7. If budget still fails, omit additional optional fields only if policy allows.
8. If budget still fails, reject/omit the event with a reason rather than
   removing required lineage, confidence, timing, source identity, or
   discriminator fields.

Packet budget must not cause:

- required lineage removal;
- confidence removal for STATE/FUSION/INFERENCE;
- timing exposure removal when policy requires it;
- event identity/source/track rewrite;
- zero-filled geo;
- unit conversion;
- hidden defaults.

S1-06B should include tests proving packet-size optimization does not corrupt
semantics and does not treat compact CBOR as the source of precision rules.

## J. Projection Validator Interaction

S1-06B should keep profile precision validation pairwise, like projection
preservation.

Options:

- Extend `tools/validate_projection.py` with optional `--precision-policy`.
  Advantage: direct reuse of source/projected comparison and failure model.
  Risk: projection validator becomes too broad.
- Create `tools/validate_precision_policy.py`.
  Advantage: keeps precision ceilings, utility floors, and packet-budget rules
  separate while still importing projection comparison helpers.
  Recommendation: preferred for S1-06B.
- Add precision checks directly to the projection field catalog.
  Advantage: one catalog. Risk: mixes field mutability with operational
  quantization values.
- Add a new `conformance/profile-precision/` fixture suite.
  Recommendation: use this with the standalone precision validator.

Required principle:

Profile precision validation compares source/projected pairs and confirms
quantization is allowed, conservative, within policy, above utility floor, and
does not violate projection preservation.

Recommended S1-06B behavior:

- `tools/validate_precision_policy.py` loads:
  - `policy/profile-precision.yaml`
  - `conformance/profile_projection_field_catalog.yaml`
  - `conformance/profile-precision/must-pass.jsonl`
  - `conformance/profile-precision/must-fail.jsonl`
- It should run projection preservation first or reuse its checks so precision
  policy cannot accept a projection-invalid pair.
- It should produce stable precision failure codes, such as:
  - `PRECISION_CONFIDENCE_ROUNDED_UP`
  - `PRECISION_TTL_ROUNDED_UP`
  - `PRECISION_ERROR_BOUND_ROUNDED_DOWN`
  - `PRECISION_POLICY_CEILING_EXCEEDED`
  - `PRECISION_UTILITY_FLOOR_VIOLATED`
  - `PRECISION_IMMUTABLE_FIELD_CHANGED`
  - `PRECISION_UNIT_CHANGED`
  - `PRECISION_REQUIRED_FIELD_REMOVED`
  - `PRECISION_PACKET_BUDGET_SEMANTIC_STRIP`

## K. Policy Artifact Plan

Recommended artifacts:

- Human-readable policy:
  - `spec/profile-precision-policy.md`
- Machine-readable policy:
  - `policy/profile-precision.yaml`

Rationale for `policy/`: precision ceilings and utility floors are export
policy, not schema. They should live with `profiles.yaml`, `semantics.yaml`, and
timing policy rather than under `conformance/`.

Recommended fixtures:

- `conformance/profile-precision/README.md`
- `conformance/profile-precision/must-pass.jsonl`
- `conformance/profile-precision/must-fail.jsonl`
- `conformance/profile-precision/context.jsonl`

Recommended validator:

- `tools/validate_precision_policy.py`

Recommended tests:

- `gateway/tests/test_profile_precision_policy.py`

Optional implementation references:

- `tools/measure_packet_size.py` for budget checks.
- `tools/validate_projection.py` for pairwise preservation checks.

## L. Fixture Plan

Must-pass cases:

- H to M STATE_EVENT with policy-allowed lat/lon reduction.
- M to L STATE_EVENT with policy-allowed lat/lon reduction.
- Confidence rounded down.
- `valid_for_ms` shortened or bucketed down.
- Timing error rounded up.
- `source_summary` omitted by policy.
- Profile M RF OBSERVATION_EVENT frequency/bandwidth/power quantized according
  to policy.
- Compact Profile L packet remains valid after policy-compliant quantization.
- Command target_geo quantized within command safety utility floor.
- Error ellipse or quality error field rounded up for v1.1.0 experimental
  branch fixtures, if S1-06B deliberately includes v1.1.0 policy examples.

Must-fail cases:

- Confidence rounded up.
- `valid_for_ms` rounded up.
- Timing error rounded down.
- Lat/lon precision increased.
- Units changed.
- `event.ts` changed or rounded.
- `track_id` changed.
- Lineage removed.
- Required field removed.
- Geo over-thinned below utility floor.
- Command `target_geo` over-thinned below command safety policy.
- RF `center_freq_hz` rounded in a way that changes meaning beyond policy.
- Implicit zero-filled geo created.
- Hidden default introduced.
- Precision policy accepts a Profile L event that violates projection
  preservation.
- Packet-budget path strips required lineage/confidence/timing fields.

Fixture wrapper should include:

- `name`
- `description`
- `source_profile`
- `target_profile`
- `policy_id`
- `source`
- `projected`
- `expect`
- `expect_code`
- optional `packet_budget`
- optional `context`
- optional `roundtrip`
- optional `notes`

## M. Gateway / Exporter Plan

Future gateway/exporter implementation should apply precision policy only at an
explicit export step.

Rules:

- Do not mutate the source event in the event store.
- Decode and validate source event first.
- Apply optional field omission according to projection catalog/profile policy.
- Apply deterministic quantization functions selected by policy.
- Validate the output as a same-event projection when event identity is
  preserved.
- If the output changes semantic meaning, emit a new event with new `event_id`
  and lineage instead of a same-event projection.
- Emit warnings or structured failure codes when an event cannot satisfy both
  packet budget and utility floor.
- Preserve event identity, source identity, track identity, event layer,
  lineage, units, coordinate system, and discriminator consistency.

Recommended config shape for future implementation:

```yaml
profile_precision_policy:
  enabled: false
  policy_file: policy/profile-precision.yaml
  target_profile: L
  packet_budget:
    encoding: compact
    max_bytes: 256
  on_utility_floor_failure: reject
```

This config is illustrative only and should not be added during S1-06A.

## N. Conformance Runner Integration Plan

S1-06B should keep a standalone validator authoritative:

```powershell
python tools\validate_precision_policy.py --policy policy\profile-precision.yaml --must-pass conformance\profile-precision\must-pass.jsonl --must-fail conformance\profile-precision\must-fail.jsonl
```

Optional conformance integration:

```powershell
python tools\validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative --precision-policy
```

Default `--strict` should remain unchanged at first.

`--precision-policy` should be combinable with:

- `--profile-projection`
- `--extension-registry`
- `--conformance-classes`
- `--encoding-negative`

It should not silently skip missing policy or fixture files.

## O. Conformance Class Impact

S1-06B should probably strengthen existing class evidence first:

- `ZMETA-PROFILE-L`
- `ZMETA-PROFILE-M`
- `ZMETA-PROFILE-H`
- `ZMETA-PROJECTION-PRESERVATION`

Preferred approach:

- Do not add a new conformance class in S1-06B unless the precision validator,
  policy, fixtures, and claims can support it cleanly.
- If a new class is justified, use `ZMETA-PRECISION-POLICY`, mark it implemented
  only if the full validator and fixture suite exists, and make it depend on
  `ZMETA-PROJECTION-PRESERVATION`.
- Consider deferring class-manifest changes until S1-06C audit verifies the
  implementation.

Do not reopen D-008 for precision policy unless conformance-class validation or
claim evidence becomes inconsistent.

## P. Human Decisions Required

Before S1-06B, maintainers should decide:

- Exact candidate precision defaults by profile and field family.
- Whether precision values are global defaults or mission/profile-configurable.
- Whether Profile L has one universal policy or multiple mission policies.
- Whether coordinate quantization is decimal-place-based, grid-based, or
  uncertainty/CEP-based.
- Whether confidence rounding should truncate to fixed decimals or floor to
  configured buckets.
- Whether timing error should round to fixed buckets.
- Whether command geometry policy must be stricter than state display policy.
- Whether RF quantization varies by modality, sensor resolution, band, or mission.
- Whether precision policy is enforced in gateway exports, conformance only, or
  both.
- Whether precision-policy validation should ever join default strict.
- Whether future v1.1.0 error ellipse fields should be included in the first
  policy or deferred until v1.1.0 branch adoption decisions.

## Q. Implementation Plan for S1-06B

Recommended file-by-file implementation:

- `spec/profile-precision-policy.md`
  - Human-readable precision policy, field families, rounding modes, packet
    budget order, and conservative semantics.
- `policy/profile-precision.yaml`
  - Machine-readable profile ceilings, utility floors, rounding modes, packet
    budget hooks, and field-family rules.
- `conformance/profile-precision/README.md`
  - Fixture wrapper, failure codes, command usage, and relationship to
    projection preservation.
- `conformance/profile-precision/must-pass.jsonl`
  - Positive source/projected precision policy pairs.
- `conformance/profile-precision/must-fail.jsonl`
  - Negative precision, rounding, utility floor, packet-budget, and projection
    interaction cases.
- `conformance/profile-precision/context.jsonl`
  - Optional policy context, if packet budget or utility floor checks require
    named context.
- `tools/validate_precision_policy.py`
  - Standalone validator that loads policy, validates source/projected events,
    invokes projection checks, enforces precision ceilings and utility floors,
    and checks packet budgets where specified.
- `gateway/tests/test_profile_precision_policy.py`
  - Focused tests for validator success/failure, rounding directions, immutable
    fields, utility floors, packet-budget behavior, and conformance integration.
- `tools/validate_conformance.py`
  - Add optional `--precision-policy` only.
- `spec/profile-compatibility.md`
  - Add a short reference to precision policy as profile/export policy.
- `spec/profile-projection-field-catalog.md`
  - Clarify division between field mutability and precision policy values.
- `spec/compact-binary-mapping.md`
  - State compact packet budgets may consume precision policy output but do not
    define precision policy.
- `conformance/README.md`
  - Document the new precision policy fixture suite and command.
- `docs/zmeta_refinement_worklog.md`
  - Mark S1-06B implementation status and D-010 state.
- `docs/zmeta_refinement_handoff.md`
  - Record artifacts, commands, limitations, and next audit.

Fewer files are acceptable if S1-06B chooses conformance-only validation and
defers gateway/exporter implementation. The policy and validator should still be
separate artifacts.

## R. Acceptance Criteria for S1-06B

S1-06B should satisfy:

- No schemas changed.
- Semantic contract unchanged.
- No new event vocabulary.
- Profile precision policy artifact exists.
- Precision validator exists.
- Must-pass precision fixtures pass.
- Must-fail precision fixtures fail with stable codes.
- Confidence/TTL/error-bound rounding directions are enforced.
- `event.ts`, event identity, source identity, track identity, and lineage remain
  immutable.
- Units cannot change.
- Over-thinning below utility floor fails.
- Packet-budget checks do not strip required semantic fields.
- Projection conformance still passes.
- Encoding-negative still passes.
- Extension registry validation still passes.
- Conformance class validation still passes.
- Optional `--precision-policy` conformance path works.
- Default strict conformance remains unchanged.
- D-010 is marked implemented pending S1-06C audit, not closed in S1-06B.

## S. Risks and Open Questions

Risks:

- Operational precision values may be sensitive to mission, geography, and
  sensor type.
- False precision can persist if ceilings are too permissive.
- Over-thinning can make state, command, RF, or timing data unsafe or useless.
- Coordinate jitter can be introduced by inconsistent grid origin or rounding
  method.
- Packet budget and operator utility can conflict.
- Source-native measurement uncertainty may be absent, making conservative
  quality adjustment difficult.
- Mission-specific overrides can fragment conformance if not identified by
  policy ID.
- Precision policy can be confused with coalition release/redaction policy if
  docs do not keep boundaries explicit.
- Future Emergency/L0 behavior may need different ceilings, but it must remain
  out of current H/M/L policy until a versioned branch approves it.
- Some precision policy may be deployment-specific rather than universal; the
  conformance suite should validate policy mechanics and candidate defaults
  without freezing every operational value globally.

Open questions:

- Which candidate defaults should be promoted to baseline conformance values?
- Should command geometry use a separate safety policy from STATE_EVENT display?
- Should Profile M RF quantization be band-specific?
- Should the first implementation include v1.1.0 error ellipse policy or keep
  S1-06B v1.0-focused?
- Should packet-budget failures emit SYSTEM_EVENT diagnostics, CLI failures, or
  exporter warnings?

## Recommended Next Work Item

Proceed to S1-06B - Profile Precision / Quantization Policy Floors
Implementation.

Keep D-010 open until S1-06B implements the policy and S1-06C audits it.
