# S1-08A MAVLink State Payload Drift Cleanup

Date: 2026-05-07

## Purpose

S1-08A resolves D-001 with a narrow documentation cleanup for the MAVLink
ingress adapter README. The cleanup removes stale guidance that suggested
MAVLink platform-state telemetry should map into `STATE_EVENT`
`payload.features.*`.

The semantic contract remains authoritative: `STATE_EVENT` is current
operator-facing belief/state. It is not raw sensor telemetry and must not carry
raw observation features, raw measurements, observation modality fields,
observation time windows, or raw data references.

## Files Inspected

- `adapters/ingress/mavlink/README.md`
- `adapters/ingress/mavlink/mavlink_to_zmeta_template.py`
- `adapters/ingress/mavlink/test_mavlink_ingress.py`
- `adapters/README.md`
- `docs/zmeta_refinement_worklog.md`
- `docs/zmeta_refinement_handoff.md`
- `docs/zmeta_contract_to_stack_crosswalk.md`
- `docs/zmeta_semantic_contract_lockdown_audit.md`
- `docs/s1_01_v1_baseline_verification_plan.md`
- `spec/semantics-contract.md`
- `schema/README.md`
- `schema/zmeta-event-1.0.schema.json`
- `schema/zmeta-event-1.1.0.schema.json`
- `policy/semantics.yaml`
- `conformance/must-fail.jsonl`
- MAVLink-related adapter test references surfaced by grep

## Grep Results Summary

The required grep checks found:

- `adapters/ingress/mavlink/README.md` was the only MAVLink ingress source
  mapping platform-state telemetry into `payload.features.*`.
- `adapters/ingress/mavlink/mavlink_to_zmeta_template.py` does not emit
  `payload.features`, `raw_features`, `modality`, `measurement`,
  `measurements`, `data_ref`, or `data_refs` in `STATE_EVENT` payloads.
- `gateway/tests/test_schema_version_discrimination.py`,
  `schema/README.md`, `policy/semantics.yaml`, and `conformance/must-fail.jsonl`
  already document or test STATE_EVENT raw-field rejection.
- Other `payload.features` and modality references are valid OBSERVATION_EVENT
  or extension-governance surfaces, not MAVLink STATE_EVENT mappings.

## Drift Classification

### Correct STATE_EVENT mapping guidance

MAVLink platform position, heading, and speed may contribute to state-safe
fields after projection:

- `payload.track_id`
- `payload.geo`
- `payload.heading_deg`
- `payload.speed_mps`
- `payload.valid_for_ms`
- `payload.timing_quality`
- top-level `confidence`
- `lineage`

Quality/status details such as GPS fix type and satellite count may be retained
as state quality metadata when allowed, not as raw observation features.

### Erroneous raw telemetry guidance

The README incorrectly mapped:

- `GPS_RAW_INT.fix_type` to `payload.features.gps_fix_type`
- `GPS_RAW_INT.satellites_visible` to `payload.features.satellites_visible`
- `ATTITUDE.roll/pitch/yaw` to `payload.features.*`
- `SYS_STATUS.voltage_battery` to `payload.features.battery_voltage`

These mappings were removed or moved into explicit "incorrect mapping to avoid"
examples.

### Ambiguous wording corrected

The README note saying low GPS fix quality sets a `geo_stale` feature was
corrected to say the implementation sets `payload.quality.geo_status` to
`STALE`.

The README now states that `payload.extensions` must not be used as a loophole
for raw measurements.

### Implementation and test references

The implementation already emits MAVLink STATE_EVENT payloads using state-safe
fields and `payload.quality`. Existing schema tests reject raw observation
fields at the STATE_EVENT payload root and inside `payload.extensions`.

## Files Changed

- `adapters/ingress/mavlink/README.md`
- `docs/s1_08a_mavlink_state_payload_drift_cleanup.md`
- `docs/zmeta_refinement_worklog.md`
- `docs/zmeta_refinement_handoff.md`

## Code Behavior Summary

No code changes were required. `translate_platform_state()` emits:

- `payload.geo`
- `payload.valid_for_ms`
- `payload.heading_deg`
- `payload.speed_mps`
- `payload.quality`
- `payload.timing_quality`
- top-level `confidence`
- `lineage`

It does not emit raw `payload.features.*` in `STATE_EVENT`.

## Drift Check

- Schemas were not changed.
- The semantic contract was not changed.
- The extension registry was not changed.
- The conformance class manifest was not changed.
- No new event vocabulary became valid.
- STATE_EVENT raw-field prohibitions remain intact.
- No D-012 follow-up was needed.

## Validation

- `git grep -n "payload.features" adapters/ingress/mavlink adapters README.md spec schema policy gateway tools conformance`:
  MAVLink README references are now prohibition or "incorrect mapping to avoid"
  examples; other hits are observation, extension, projection, or precision
  policy surfaces.
- `git grep -n -i "mavlink" adapters/ingress/mavlink adapters README.md docs spec conformance gateway/tests`:
  MAVLink references are adapter docs/tests, egress command projection, or S1
  governance notes.
- `git grep -n "raw_features\|measurement\|measurements\|modality\|data_ref\|data_refs" adapters/ingress/mavlink adapters README.md docs spec conformance gateway/tests`:
  MAVLink README references are raw-field prohibitions; schema/conformance/test
  references preserve existing observation and state raw-field boundaries.
- `python tools/validate_conformance.py --strict`: `conformance ok`.
- `python tools/validate_conformance.py --strict --profile-projection`:
  `projection conformance ok total=33`, `conformance ok`.
- `python tools/validate_conformance.py --strict --profile-projection --extension-registry`:
  `projection conformance ok total=33`, `extension registry ok entries=63`,
  `conformance ok`.
- `python tools/validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes`:
  `projection conformance ok total=33`, `extension registry ok entries=63`,
  `conformance classes ok classes=30 claims=2`, `conformance ok`.
- `python tools/validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative`:
  `projection conformance ok total=33`, `extension registry ok entries=63`,
  `conformance classes ok classes=30 claims=2`,
  `encoding negative ok total=49`, `conformance ok`.
- `python tools/validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative --precision-policy`:
  `projection conformance ok total=33`, `extension registry ok entries=63`,
  `conformance classes ok classes=30 claims=2`,
  `encoding negative ok total=49`, `profile precision policy ok total=32`,
  `conformance ok`.
- `python tools/validate_projection.py --catalog conformance/profile_projection_field_catalog.yaml --must-pass conformance/profile-projection/must-pass.jsonl --must-fail conformance/profile-projection/must-fail.jsonl --quiet`:
  `projection conformance ok total=33`.
- `python tools/validate_extension_registry.py --registry spec/extension-registry.yaml`:
  `extension registry ok entries=63`.
- `python tools/validate_conformance_classes.py --manifest conformance/conformance_classes.yaml --claims conformance/claims/example-reference-gateway.yaml conformance/claims/example-core-producer.yaml`:
  `conformance classes ok classes=30 claims=2`.
- `python tools/validate_encoding_negative.py --compact conformance/encoding-negative/compact-must-fail.jsonl --protobuf conformance/encoding-negative/protobuf-must-fail.jsonl --gateway conformance/encoding-negative/gateway-must-fail.jsonl --quiet`:
  `encoding negative ok total=49`.
- `python tools/validate_precision_policy.py --policy policy/profile-precision.yaml --must-pass conformance/profile-precision/must-pass.jsonl --must-fail conformance/profile-precision/must-fail.jsonl --quiet`:
  `profile precision policy ok total=32`.
- `python -m pytest`: `306 passed`.
- `git diff --check`: passed with CRLF conversion warnings only.

## D-001 Recommendation

D-001 can close. The MAVLink README drift was corrected, and inspection did not
find implementation drift that would require a new implementation follow-up.

## Recommended Next Item

S1-09A - Contract Hash / Release Hash Follow-Up Plan Only.
