# S1-07A TAKEOFF Crosswalk Cleanup

Date: 2026-05-07

## Purpose

S1-07A resolves D-011 with a narrow documentation cleanup. The goal was to
remove or clarify erroneous `TAKEOFF` references without changing schemas,
validators, encodings, adapters, gateway runtime behavior, extension registry
entries, conformance class definitions, examples, fixtures, or event
vocabulary.

The semantic contract remains authoritative. `TAKEOFF` is not current v1.0 or
v1.1.0 command vocabulary and is not an adopted, experimental, proposed, or
reserved extension registry entry.

## Grep Summary

`git grep -n -i "takeoff"` found one erroneous documentation reference before
cleanup:

- `docs/zmeta_contract_to_stack_crosswalk.md` listed `TAKEOFF` in the v1.1.0
  expanded-tasking row as if it were supported command vocabulary.

The remaining references are invalidity guards, audit history, planning notes,
or current issue-tracking notes. No schema, registry, example, fixture, or
command vocabulary list made `TAKEOFF` valid.

## Reference Classification

### Allowed invalidity and guard references

- `tools/validate_extension_registry.py` keeps `TAKEOFF` in
  `UNREGISTERED_RESERVED_SCHEMA_VALUES` so it cannot leak into current schemas.
- `gateway/tests/test_extension_registry.py` proves `TAKEOFF` is invalid under
  v1.0 and v1.1.0 and that registry validation fails if it appears in current
  schema vocabulary.
- `tools/validate_encoding_negative.py` includes `TAKEOFF` in a reserved-name
  leakage list for invalid-after-decode checks.
- S1-03/S1-04/S1-05/S1-06 plan and audit documents mention `TAKEOFF` only as a
  stray crosswalk typo, invalidity guard, or deferred cleanup item.

### Erroneous or ambiguous documentation references

- `docs/zmeta_contract_to_stack_crosswalk.md` incorrectly listed `TAKEOFF` as a
  v1.1.0 expanded tasking command. This was corrected to list the actual
  supported v1.1.0 expanded tasking values:
  `RETURN_TO_BASE`, `LAND`, `LOITER`, `SCAN_RF`, `TRACK_TARGET`, and
  `CHANGE_SENSOR_MODE`.

### Unexpected code, schema, fixture, or vocabulary references

- None found. The code references are leakage guards, not vocabulary adoption.

## Files Changed

- `docs/zmeta_contract_to_stack_crosswalk.md`
- `docs/s1_07a_takeoff_crosswalk_cleanup.md`
- `docs/zmeta_refinement_worklog.md`
- `docs/zmeta_refinement_handoff.md`

## Files Intentionally Not Changed

- `spec/semantics-contract.md`
- `schema/zmeta-event.schema.json`
- `schema/zmeta-event-1.0.schema.json`
- `schema/zmeta-event-1.1.0.schema.json`
- `spec/extension-registry.md`
- `spec/extension-registry.yaml`
- validators, gateway runtime, codecs, adapters, examples, fixtures, and
  conformance class definitions

## Drift Check

- Schemas were not changed.
- The semantic contract was not changed.
- The extension registry was not changed.
- No new event vocabulary became valid.
- `TAKEOFF` remains invalid current vocabulary.
- The `TAKEOFF` leakage guard remains in place.

## Validation

- `git grep -n -i "takeoff"`: remaining references are invalidity guards,
  historical planning/audit notes, or S1-07A closure notes.
- `python tools/validate_extension_registry.py --registry spec/extension-registry.yaml`:
  `extension registry ok entries=63`.
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
- `python tools/validate_conformance_classes.py --manifest conformance/conformance_classes.yaml --claims conformance/claims/example-reference-gateway.yaml conformance/claims/example-core-producer.yaml`:
  `conformance classes ok classes=30 claims=2`.
- `python tools/validate_encoding_negative.py --compact conformance/encoding-negative/compact-must-fail.jsonl --protobuf conformance/encoding-negative/protobuf-must-fail.jsonl --gateway conformance/encoding-negative/gateway-must-fail.jsonl --quiet`:
  `encoding negative ok total=49`.
- `python tools/validate_precision_policy.py --policy policy/profile-precision.yaml --must-pass conformance/profile-precision/must-pass.jsonl --must-fail conformance/profile-precision/must-fail.jsonl --quiet`:
  `profile precision policy ok total=32`.
- `python -m pytest`: `306 passed`.
- `git diff --check`: passed with CRLF conversion warnings only.

## D-011 Recommendation

D-011 can close. The only erroneous `TAKEOFF` current-vocabulary reference was
removed from the crosswalk, and the remaining references are explicit
invalidity guards or historical cleanup notes.

## Recommended Next Item

S1-08A - MAVLink Adapter README State Payload Drift Cleanup.
