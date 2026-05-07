# S1-02A Profile Projection Preservation Field Catalog and Conformance Plan

Status: COMPLETE
Date: 2026-05-07
Scope: Planning only. No schemas, gateway code, adapters, encodings, tests, examples, or policy files are changed by this work item.

## A. Current Projection Behavior

The current stack enforces profile legality but does not yet prove semantic preservation between a higher-fidelity event and a lower-profile projection.

Current behavior:

| Surface | Current Behavior | Preservation Gap |
| --- | --- | --- |
| `schema/zmeta-event-1.0.schema.json` | Enforces v1.0 event shape, subtype/payload matching, confidence and lineage presence or absence by event type, state raw-field prohibition, command altitude prohibition, and `profile` event-type compatibility. | Validates each event independently. It cannot compare a Profile L/M event against the source event it was projected from. |
| `policy/profiles.yaml` | Defines L/M/H allowed event types: L allows STATE/SYSTEM/COMMAND, M adds OBSERVATION/FUSION, H allows all v1.0 event types. | Does not define field-level projection invariants. |
| `gateway/src/gateway.py` | Can stamp `profile`, stamp `event.t_receive`/`event.t_publish`, strip configured optional dotted paths, apply timing/failure confidence degradation, then validate outgoing events. Default stripped paths are `source.sensor_id`, `source.sw_version`, `payload.data_ref`, and `payload.data_refs`. | There is no source/projected pair validator for event identity, source identity, track identity, lineage, units, precision monotonicity, confidence monotonicity, TTL monotonicity, or prohibited rewrites. |
| `gateway/src/validators.py` | Validates schema, profile, role, producer authority, timing quality exposure, timing freshness, lineage, and semantic policy rules. | Runtime validation catches malformed events but not whether a lower-profile event is a faithful projection of a specific source event. |
| `spec/compact-binary-mapping.md` and `zmeta_compact.py` | Define compact Profile L as a wire-level CBOR integer-key mapping that expands back to canonical JSON before validation. Compact roundtrip tests exist. | Roundtrip tests prove encode/decode equality for selected events, but not projection equivalence from H/M source events to L output. |
| `spec/protobuf-encoding.md` and `zmeta_proto.py` | Protobuf is an envelope projection that carries canonical payload JSON bytes and must decode back to JSON before validation. | It is not profile-specific and has no negative projection preservation fixtures. |
| `examples/*.jsonl` and `conformance/*.jsonl` | Provide valid and invalid profile examples and schema/policy conformance fixtures. | Fixtures are single-event pass/fail cases, not source/projected pair cases. |
| `tools/measure_packet_size.py` | Can strip dotted paths for packet-size measurement. | Size stripping is not a semantic projection validator. |
| `tools/convert_encoding.py` | Converts one event among JSON, CBOR, compact, and protobuf. | Conversion does not validate projection preservation against another event. |

S1-02B should add projection preservation as a conformance layer on top of current schema, policy, gateway, and encoding checks.

## B. Projection Invariants

These invariants apply when an exporter claims a lower-profile event is a projection of the same semantic event. If a transformation changes meaning, authorship, layer, track identity, or source-authored truth, it is not a profile projection; it must be emitted as a new event with new lineage.

| Invariant | Rule | Enforcement Target |
| --- | --- | --- |
| `zmeta_version` | Must remain the same unless an explicit versioned migration is being tested. v1.1+ fields must not be introduced into v1.0 projection fixtures. | Projection validator and conformance fixtures. |
| `event.event_id` | Must be preserved for same-event profile export projections. A new ID is allowed only when a new semantic event is authored, and then lineage must explain the transform. | Projection validator. |
| `event.ts` | Must preserve the source event timestamp. Export receipt/publish timestamps may be added as non-semantic gateway metadata. | Projection validator. |
| `event.event_type` | Must not change. Observation cannot become state by profile projection alone. | Schema plus projection validator. |
| `event.event_subtype` | Must not change except under an approved versioned adapter mapping that emits a new event. | Schema plus projection validator. |
| `source.platform_id`, `source.node_role`, `source.producer` | Source identity is source-authored and must not be rewritten by thinning. Optional `source.sensor_id` and `source.sw_version` may be omitted only if the catalog marks them removable for the target profile. | Projection validator. |
| `payload.track_id` | Track identity must not change for STATE_EVENT or FUSION_EVENT projection. | Projection validator. |
| `lineage.based_on` | Must be preserved for INFERENCE_EVENT, FUSION_EVENT, and STATE_EVENT. Profile L may omit parent events from export, but it must not delete the lineage references. | Schema plus projection validator. |
| `lineage.transform` | Should be preserved when present. Removal is a loss of audit detail and should fail unless the catalog explicitly allows removal for a specific future profile policy. | Projection validator. |
| Units | Units are semantic. `_m`, `_ms`, `_mps`, `_deg`, `_hz`, `_dbm`, `_bps`, and percent fields must not be converted, renamed, or silently rescaled. | Projection validator. |
| Coordinate system | `geo.lat`, `geo.lon`, `geo.alt_m`, `target_geo`, and search/orbit geometry keep their coordinate meaning. Precision may be reduced; coordinate semantics must not change. | Projection validator. |
| Semantic layer | OBSERVATION, INFERENCE, FUSION, STATE, COMMAND, and SYSTEM layers must remain separated. Profile projection cannot collapse observations or inferences into state. | Schema plus projection validator. |
| Payload discriminator | `payload.modality`, `payload.inference_type`, `payload.task_type`, and `payload.system_type` must remain consistent with `event.event_subtype`. | Schema plus projection validator. |
| Confidence monotonicity | If confidence exists on both source and projected events, projected confidence must be less than or equal to source confidence. Profile projection must never increase confidence. | Projection validator. |
| TTL monotonicity | `payload.valid_for_ms` must be less than or equal to the source TTL when it exists on both events. Profile projection must never increase validity. | Projection validator. |
| Timing quality exposure | Events requiring timing quality must keep per-event timing quality or have an explicit paired TIME_STATUS context in the fixture. Profile projection must not hide timing degradation. | Policy plus projection fixture context. |
| Required fields | All fields required by event type and target profile must remain present. Required STATE_EVENT fields are especially protected in Profile L: `track_id`, `geo`, `valid_for_ms`, `confidence`, and `lineage`. | Schema plus projection validator. |

## C. Allowed Projection Changes

Profile thinning may make only conservative, meaning-preserving changes:

| Allowed Change | Conditions |
| --- | --- |
| Omit optional fields | The field must be listed as removable for the target profile in the field catalog. Required fields and protected identity/source/lineage fields are never removable. |
| Reduce numeric precision | Allowed for cataloged numeric measurement, coordinate, bearing, heading, speed, and timing fields. The projected value must be a coarser representation of the source value, not a more specific or contradictory value. |
| Reduce update rate | Allowed at the stream/export layer. It is not represented by mutating a single event except by shortening TTL or omitting some events from export. |
| Lower confidence | Allowed for INFERENCE_EVENT, FUSION_EVENT, and STATE_EVENT. It may be required by timing freshness, profile downgrade, release, or compute degradation policy. |
| Shorten `valid_for_ms` | Allowed for STATE_EVENT and COMMAND_EVENT. A projection may become stale sooner than the source, never later. |
| Add non-semantic export metadata | Existing v1.0-safe examples are `profile`, `event.t_receive`, and `event.t_publish` when allowed by schema. Future `projection` metadata is a versioned candidate and must not be inserted into v1.0 events. |
| Omit parent events from export | Allowed for low-bandwidth or release-constrained exports only if `lineage.based_on` remains intact and policy records unresolved lineage as warning/degrade/reject according to the profile. |
| Omit an entire event from a lower-profile export | Allowed when the event type is not legal in the target profile. For example, Profile L must not rewrite an INFERENCE_EVENT into STATE_EVENT; it should omit the inference or export a separately authored STATE_EVENT with lineage. |

## D. Prohibited Projection Changes

These cases must fail projection preservation conformance even if the projected event passes JSON Schema by itself:

| Prohibited Change | Reason |
| --- | --- |
| Confidence increase | Overstates certainty after thinning. |
| `valid_for_ms` increase | Hides staleness and overstates validity. |
| Precision increase | Invents detail not present in the source projection. |
| Unit change | Reinterprets measurement meaning. |
| Source rewrite | Changes authorship and breaks provenance. |
| `track_id` rewrite | Breaks track continuity and operator state identity. |
| Lineage deletion for INFERENCE/FUSION/STATE | Removes auditability and parent evidence. |
| Observation converted to state without separately authored fusion/state lineage | Collapses semantic layers. |
| Raw fields inserted into STATE_EVENT | Violates state projection discipline. |
| New `event_id` without semantic change | Breaks idempotence and replay dedupe. |
| Same `event_id` with semantic payload change | Mutates an immutable event while pretending it is the same event. Conservative omissions and precision reduction listed in the catalog are not semantic payload changes. |
| Required field removal | Produces a thinned event that cannot carry the minimum semantic contract. |
| Hidden defaults | Adds assumptions that were not in the source, such as implicit confidence, implied altitude, implied lineage, or inferred modality. |
| Profile-incompatible event emission | Exports an event type not allowed for the target profile. |
| Compact or protobuf treated as semantic authority | Encoding must decode to canonical JSON and then pass schema, policy, and projection checks. |

## E. Projection Field Catalog

S1-02B should create a machine-readable field catalog, recommended path `conformance/profile_projection_field_catalog.yaml`, with a documentation rendering in `spec/profile-projection-field-catalog.md`. The catalog should classify fields by projection behavior, not merely by schema validity.

Recommended catalog columns:

| Column | Meaning |
| --- | --- |
| `path` | Dotted path or glob-like path, such as `payload.geo.lat` or `payload.estimated_state.geo.*`. |
| `event_types` | Event types the rule applies to. |
| `profiles` | Target profiles the rule applies to. |
| `status` | `required_always`, `required_by_event_type`, `required_by_profile`, `optional_removable`, `precision_reducible`, `confidence_reducible`, `ttl_reducible`, `prohibited_in_profile_l`, `prohibited_in_state`, or `never_mutable`. |
| `comparison` | Equality, subset, non-increase, precision-non-increase, optional-omission, prohibited, or contextual. |
| `notes` | Human-readable rationale and any schema/policy source. |

Initial v1.0 field catalog:

| Field / Pattern | Event Scope | Catalog Status | Projection Rule |
| --- | --- | --- | --- |
| `zmeta_version` | All | Required always, never mutable | Preserve exactly. |
| `event.event_id` | All | Required always, never mutable | Preserve for same-event projection. New ID means a new semantic event, not a projection. |
| `event.event_type` | All | Required always, never mutable | Preserve exactly. |
| `event.event_subtype` | All | Required always, never mutable | Preserve exactly. |
| `event.ts` | All | Required always, never mutable | Preserve source event time. |
| `event.t_receive`, `event.t_publish` | All | Optional export metadata | May be added by gateway; must not replace `event.ts`. |
| `source.platform_id` | All | Required always, never mutable | Preserve exactly. |
| `source.node_role` | All | Required always, never mutable | Preserve exactly. |
| `source.producer` | All | Required always, never mutable | Preserve exactly. |
| `source.sensor_id` | All | Optional removable | May be omitted when cataloged for target profile; must not be rewritten. |
| `source.sw_version` | All | Optional removable | May be omitted when cataloged for target profile; must not be rewritten. |
| `profile` | All | Required by export context when claimed | May be stamped to target profile by gateway. Must match validation/export profile. |
| `confidence` | INFERENCE/FUSION/STATE | Required by event type, confidence reducible | Preserve or lower. Never increase. |
| `confidence` | OBSERVATION/COMMAND/SYSTEM | Prohibited | Must not be added during projection. |
| `lineage.based_on` | INFERENCE/FUSION/STATE | Required by event type, never mutable | Preserve exact parent references. Parent events may be absent from low-profile export. |
| `lineage.transform` | INFERENCE/FUSION/STATE | Audit metadata, default preserve | Preserve when present unless a future policy explicitly allows omission. |
| `payload.timing_quality` | All event types needing timing exposure | Contextual required exposure | Preserve per-event timing quality when present; otherwise fixture must include valid TIME_STATUS context. |
| `payload.modality` | OBSERVATION | Required by event type, never mutable | Preserve exactly. |
| `payload.features` | OBSERVATION | Required by event type; Profile L prohibited by event type | Preserve for legal OBSERVATION projections. Do not move into STATE_EVENT. RF required fields must remain for RF observation projections. |
| `payload.features.center_freq_hz`, `payload.features.bandwidth_hz`, `payload.features.power_dbm` | RF OBSERVATION | Required by RF modality | Preserve units. Precision may be reduced only if cataloged and still truthful. |
| `payload.geo.*` | OBSERVATION/STATE and nested fusion state | Precision reducible | Preserve coordinate meaning and units; reduce precision only. |
| `payload.bearing.*` | OBSERVATION and nested fusion state | Precision reducible | Preserve degrees and reference meaning; reduce precision only. |
| `payload.quality` | OBSERVATION | Optional removable or precision reducible | May be omitted for target profile only if loss is reflected by confidence/timing/profile policy where applicable. |
| `payload.data_ref`, `payload.data_refs` | OBSERVATION and v1.1+ evidence carriers | Optional removable | May be omitted from lower-profile export. Must not be inserted into STATE_EVENT. |
| `payload.t_start`, `payload.t_end` | OBSERVATION | Optional removable as a pair | If one is preserved, both must remain and midpoint semantics must remain valid. |
| `payload.inference_type` | INFERENCE | Required by event type, never mutable | Preserve exactly. Profile M/L do not export INFERENCE_EVENT in current policy. |
| `payload.claim` | INFERENCE | Required by event type | Preserve for legal H projection; optional claim subfields may only be removed by future catalog rules. |
| `payload.model.name`, `payload.model.version` | INFERENCE | Required by event type | Preserve exactly for H projection. |
| `payload.based_on` | INFERENCE | Required by event type | Must equal or be subset of `lineage.based_on` according to lineage policy; default preserve. |
| `payload.track_id` | FUSION/STATE | Required by event type, never mutable | Preserve exactly. |
| `payload.members` | FUSION | Required by event type | Preserve exact member IDs for same-event projection. |
| `payload.estimated_state` | FUSION | Optional removable or precision reducible | May omit optional estimated-state subfields if cataloged; must not rewrite track identity. |
| `payload.stability` | FUSION | Required by event type | Preserve or lower only if later catalog treats it as confidence-like. Default preserve exactly. |
| `payload.last_seen_ts` | FUSION | Required by event type, never mutable | Preserve exactly. |
| `payload.geo` | STATE | Required by event type/profile | Preserve with same coordinate semantics; precision may be reduced. |
| `payload.class` | STATE | Optional removable | May be omitted in Profile L; must not be changed to a different class by projection. |
| `payload.source_summary` | STATE | Optional removable | May be omitted in Profile L; lineage must remain. |
| `payload.heading_deg`, `payload.speed_mps` | STATE | Optional removable, precision reducible | May be omitted or rounded down in precision; units must remain unchanged. |
| `payload.valid_for_ms` | STATE/COMMAND | Required by event type, TTL reducible | Preserve or shorten. Never increase. |
| `payload.features`, `payload.raw_features`, `payload.modality`, `payload.measurement`, `payload.measurements`, `payload.t_start`, `payload.t_end`, `payload.data_ref`, `payload.data_refs` | STATE | Prohibited in STATE_EVENT | Must never be inserted by projection. |
| `payload.task_id` | COMMAND | Required by event type, never mutable | Preserve exactly for COMMAND_EVENT projection. |
| `payload.task_type` | COMMAND | Required by event type, never mutable | Preserve exactly. |
| `payload.target_geo` | COMMAND GOTO/ORBIT | Required by task type, precision reducible | Preserve 2D semantics; altitude remains prohibited. |
| `payload.geometry` | COMMAND ORBIT/SEARCH_BOX | Required by task type where applicable, precision reducible | Preserve task geometry semantics; altitude remains prohibited. |
| `payload.valid_from_ts` | COMMAND | Optional removable or preserve | If present and retained, preserve exactly. |
| `payload.priority` | COMMAND | Optional removable | May be omitted only if policy allows. Must not be raised by projection. |
| `payload.requires_deconfliction` | COMMAND | Required by event type, never mutable | Must remain `true`. |
| Command altitude-like fields | COMMAND | Prohibited | Must never be added. |
| `payload.system_type` | SYSTEM | Required by event type, never mutable | Preserve exactly and match `event.event_subtype`. |
| `payload.state` | SYSTEM | Required by event type | Preserve exactly unless a new SYSTEM_EVENT is authored. |
| `payload.metrics` | SYSTEM | Required by subtype for TIME_STATUS, TASK_ACK, LINK_STATUS, SCHEMA_VIOLATION where schema requires | Preserve required metrics. Optional metrics may be removed only if cataloged and not misleading. |

## F. Conformance Fixture Plan

Projection fixtures should be pairwise wrappers, not standalone ZMeta events. This avoids adding projection metadata to v1.0 event payloads.

Recommended fixture layout:

```json
{
  "case_id": "profile-h-to-l-state-lowered-confidence-pass",
  "source_profile": "H",
  "target_profile": "L",
  "source": { "zmeta_version": "1.0" },
  "projected": { "zmeta_version": "1.0" },
  "expect": "pass",
  "checks": [
    "schema_source",
    "schema_projected",
    "profile_projected",
    "same_event_id",
    "same_source_identity",
    "same_track_id",
    "lineage_preserved",
    "confidence_non_increase",
    "ttl_non_increase",
    "precision_non_increase",
    "compact_roundtrip_equivalence"
  ]
}
```

Recommended files:

| Fixture File | Purpose |
| --- | --- |
| `conformance/profile-projection/must-pass.jsonl` | Positive source/projected projection pairs. |
| `conformance/profile-projection/must-fail.jsonl` | Negative source/projected projection pairs with `expect_code`. |
| `conformance/profile-projection/context.jsonl` | Optional TIME_STATUS or parent events used by lineage/timing context. |
| `conformance/profile-projection/README.md` | Fixture semantics and runner instructions. |

Required positive fixtures:

| Case | Expected Checks |
| --- | --- |
| H to M STATE_EVENT projection | Same event ID, event type/subtype, source identity, track ID, lineage; optional state fields may be omitted; confidence and TTL do not increase. |
| M to L STATE_EVENT projection | Same identity and lineage; optional fields omitted; Profile L legality; lower or same confidence; shorter or same TTL. |
| H to L STATE_EVENT projection | Direct high-to-low thinning with coordinate precision reduction, optional field omission, lowered confidence, shorter TTL. |
| Profile L STATE_EVENT with preserved lineage | Parent events may be absent from L export but `lineage.based_on` remains intact. |
| Profile L STATE_EVENT with lowered confidence | Projected confidence lower than source, schema-valid, profile-valid. |
| Profile L STATE_EVENT with shortened TTL | Projected `valid_for_ms` lower than source. |
| COMMAND_EVENT L projection | Same task ID, task type, target/geometry semantics, no altitude, TTL not increased. |
| SYSTEM_EVENT TIME_STATUS L projection | Required timing metrics preserved; compact roundtrip equality. |
| Optional source fields stripped | `source.sensor_id`, `source.sw_version`, `payload.data_ref`, or `payload.data_refs` omitted only where catalog allows. |
| Compact Profile L expansion equivalence | Projected L event encoded as compact, decoded to canonical JSON, and compared with the projected JSON using equality after documented expansion defaults. |
| Protobuf decoded JSON validation | Projected event encoded/decoded via protobuf and revalidated against schema/policy. |

Required negative fixtures:

| Case | Expected Failure |
| --- | --- |
| Invalid Profile L with confidence increase | `PROJECTION_CONFIDENCE_INCREASE` |
| Invalid Profile L with `track_id` rewrite | `PROJECTION_TRACK_ID_CHANGED` |
| Invalid Profile L with source rewrite | `PROJECTION_SOURCE_CHANGED` |
| Invalid Profile L with missing lineage | Schema failure or `PROJECTION_LINEAGE_REMOVED` depending on fixture shape. |
| Invalid Profile L with raw observation fields in state | Schema failure plus projection failure if paired. |
| Invalid Profile L with `valid_for_ms` increase | `PROJECTION_TTL_INCREASE` |
| Invalid Profile L with precision increase | `PROJECTION_PRECISION_INCREASE` |
| Invalid Profile L with unit rename or rescale | `PROJECTION_UNIT_CHANGED` |
| Invalid projection that rewrites OBSERVATION_EVENT to STATE_EVENT with same event ID | `PROJECTION_EVENT_TYPE_CHANGED` |
| Invalid projection that omits required `payload.track_id` or `payload.geo` | Schema failure. |
| Invalid projection that changes `event.ts` | `PROJECTION_EVENT_TS_CHANGED` |
| Invalid projection that changes `lineage.based_on` | `PROJECTION_LINEAGE_CHANGED` |
| Invalid compact packet that decodes to schema-valid but projection-invalid JSON | `PROJECTION_*` after decode. |
| Invalid protobuf packet that decodes to schema-valid but projection-invalid JSON | `PROJECTION_*` after decode. |

Event types not legal in a target profile should be represented as either:

- no exported event, with a fixture asserting omission is allowed; or
- a separately authored legal event with a new `event.event_id` and lineage, outside same-event projection preservation.

They should not be represented as same-event type rewrites.

## G. Implementation Plan

Recommended S1-02B file-by-file implementation:

| File / Path | Change |
| --- | --- |
| `conformance/profile_projection_field_catalog.yaml` | Add machine-readable field catalog with path rules, target profiles, comparison modes, and event-type scopes. |
| `spec/profile-projection-field-catalog.md` | Add human-readable field catalog and projection preservation rules. |
| `tools/validate_projection.py` | Add a CLI that validates source/projected fixture pairs, loading JSON Schema, policy, field catalog, optional timing/lineage context, and optional compact/protobuf decode paths. |
| `gateway/src/projection_validator.py` | Add shared projection comparison logic if gateway runtime enforcement will reuse the same checks. If S1-02B is conformance-only, keep the logic in `tools/validate_projection.py` first. |
| `gateway/tests/test_profile_projection_preservation.py` | Test confidence, TTL, event ID, source identity, track ID, lineage, precision, unit, and prohibited rewrite checks. |
| `gateway/tests/test_profile_projection_encoding.py` | Test compact Profile L and protobuf decoded JSON projection-equivalence failures and passes. |
| `conformance/profile-projection/must-pass.jsonl` | Add positive pair fixtures for H to M, M to L, H to L, Profile L state, command, system, timing, and compact roundtrip cases. |
| `conformance/profile-projection/must-fail.jsonl` | Add negative pair fixtures for confidence increase, TTL increase, source rewrite, track rewrite, lineage deletion, precision increase, unit change, event type rewrite, raw state fields, and invalid decoded encodings. |
| `conformance/profile-projection/README.md` | Document fixture wrapper format and expected runner behavior. |
| `tools/validate_conformance.py` | Optionally call the projection validator behind a flag such as `--profile-projection` or add a separate command in CI. Keep existing conformance behavior stable by default if needed. |
| `spec/profile-compatibility.md` | Update after implementation to point to the field catalog and fixture runner. |
| `spec/compact-binary-mapping.md` | Add a short cross-reference explaining compact roundtrip projection equivalence tests, without changing the mapping. |
| `spec/protobuf-encoding.md` | Add a short cross-reference explaining protobuf decoded JSON projection validation, without promoting protobuf to semantic authority. |

Implementation order:

1. Add the field catalog and pair fixture format.
2. Implement projection comparison logic as a standalone CLI.
3. Add positive and negative fixture pairs.
4. Add gateway/tool tests around the comparison logic.
5. Add compact/protobuf decoded-equivalence tests.
6. Wire the projection suite into conformance validation only after fixtures are stable.

## H. Open Questions

These decisions should be resolved at the start of S1-02B:

| Question | Recommended Default |
| --- | --- |
| Should same-event projection always preserve `event.event_id`? | Yes for profile export thinning. If meaning changes, create a new event with lineage. |
| What exact numeric precision floors should Profile M and L use for lat/lon, altitude, heading, speed, bearing, and RF metrics? | Start with catalog comparisons that verify precision does not increase; add exact profile-specific decimal/quantization limits once operational packet budgets are set. |
| Should `lineage.transform` be removable in Profile L? | Default no. Preserve it when present because it is compact audit metadata. |
| How should fixture pairs express omitted events? | Use an explicit wrapper outcome such as `"projected": null` plus an allowed omission reason for event types illegal in the target profile. |
| Does timing quality have to be per-event for projection fixtures? | Default accepts per-event timing quality or a paired TIME_STATUS context, matching current policy behavior. |
| Should `source.sensor_id` and `source.sw_version` remain removable for all profiles? | Keep current gateway default for S1-02B, but document that they are source-authored and may only be omitted, never rewritten. |
| Should `payload.source_summary` omission require confidence lowering? | Recommended yes for Profile L when it materially reduces operator evidence visibility, but make the exact degradation a policy rule rather than a schema rule. |
| How should array order be compared? | Treat lineage and member ID sets as unordered where semantics permit, but preserve ordered arrays where order carries meaning. The catalog should declare comparison mode per path. |
| Should profile projection metadata be added now? | No. `projection` metadata is a future versioned candidate. S1-02B should use sidecar fixture wrappers for conformance. |

## Recommendation

Proceed to S1-02B. The current v1.0 schema and policy pack do not need broad profile changes before projection work. The next useful implementation step is a standalone field catalog plus pairwise projection conformance validator, followed by positive and negative fixtures that prove Profile L/M/H thinning preserves ZMeta meaning.
