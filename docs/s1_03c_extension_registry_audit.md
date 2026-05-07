# S1-03C Extension Registry Post-Implementation Audit

Status: COMPLETE
Date: 2026-05-07
Scope: Audit only, with one small validator/test cleanup for the D-011 TAKEOFF
stray crosswalk mention. No schemas, semantic contract text, adapters,
encodings, examples, conformance fixtures, or event vocabulary were changed.

## Summary

S1-03B implemented the extension registry as spec-owned human and
machine-readable artifacts:

- `spec/extension-registry.md`
- `spec/extension-registry.yaml`
- `tools/validate_extension_registry.py`
- `gateway/tests/test_extension_registry.py`
- optional `tools/validate_conformance.py --extension-registry` integration

The audit confirms the registry preserves version boundaries. Existing v1.1.0
concepts remain `experimental`, future concepts remain `reserved` or
`proposed`, and the registry does not make any future concept valid event
vocabulary.

## Files Inspected

- `spec/extension-registry.md`
- `spec/extension-registry.yaml`
- `tools/validate_extension_registry.py`
- `gateway/tests/test_extension_registry.py`
- `tools/validate_conformance.py`
- `spec/README.md`
- `conformance/README.md`
- `docs/s1_03_extension_registry_plan.md`
- `docs/zmeta_refinement_worklog.md`
- `docs/zmeta_refinement_handoff.md`
- `docs/zmeta_contract_to_stack_crosswalk.md`
- `spec/semantics-contract.md`
- `schema/README.md`
- `schema/zmeta-event.schema.json`
- `schema/zmeta-event-1.0.schema.json`
- `schema/zmeta-event-1.1.0.schema.json`
- `spec/versioning.md`
- `spec/profile-compatibility.md`
- `spec/compact-binary-mapping.md`
- `spec/protobuf-encoding.md`
- `examples/zmeta-v1.1-examples.jsonl`
- current conformance JSONL fixtures and v1.1 schema tests

## Files Changed During S1-03C

- `docs/s1_03c_extension_registry_audit.md`
- `tools/validate_extension_registry.py`
- `gateway/tests/test_extension_registry.py`
- `docs/zmeta_refinement_worklog.md`
- `docs/zmeta_refinement_handoff.md`

## Schema Drift Check

S1-03B changed only the expected registry, validator, test, README, worklog, and
handoff files. The S1-03B diff did not include:

- `schema/zmeta-event.schema.json`
- `schema/zmeta-event-1.0.schema.json`
- `schema/zmeta-event-1.1.0.schema.json`

S1-03C also did not edit schemas. No reserved/proposed registry concept became
valid schema vocabulary.

## Semantic Contract Drift Check

`spec/semantics-contract.md` was not modified by S1-03B or S1-03C. The registry
implementation conforms to the contract's version-branch and future-candidate
rules instead of changing the contract.

## Registry Document Review

`spec/extension-registry.md` clearly states:

- the registry does not make a concept valid;
- validity requires an approved version branch plus schema, policy,
  adapter/gateway, encoding, documentation, and conformance coverage;
- reserved/proposed entries are not valid event vocabulary;
- v1.1.0 entries remain experimental unless explicitly promoted;
- vendor/private extensions must be namespaced and safe to ignore;
- extensions must not alter the envelope, collapse semantic layers, redefine
  units, change lineage, change profile behavior, or modify authority
  boundaries;
- future prompts should check the registry before adding vocabulary.

## Registry YAML Review

`spec/extension-registry.yaml` includes the required top-level metadata:

- `registry_version`
- `generated_for_zmeta_versions`
- `authority`
- `last_updated`
- `status_values`
- `category_values`
- `entries`

All 63 entries include the required record fields after YAML merge expansion.
No entry is missing the required field model from the S1-03A plan.

Registry entry count:

- total entries: 63
- `experimental`: 15
- `reserved`: 41
- `proposed`: 7

## Status And Category Review

Valid statuses are present and documented:

- `reserved`
- `proposed`
- `experimental`
- `adopted`
- `deprecated`
- `rejected`
- `superseded`

No entry uses an undefined status. No entry is `adopted`. v1.1.0 entries are
`experimental`; future concepts are `reserved` or `proposed`. Reserved and
proposed entries do not claim `schema_status: implemented` or
`conformance_status: implemented`.

Categories used by current entries are valid:

- `ai_model_provenance`
- `coalition_release`
- `command_task_type`
- `companion_artifact`
- `data_evidence`
- `observation_feature_contract`
- `observation_modality`
- `operator_display`
- `pnt_integrity`
- `profile_export_control`
- `replay_test`
- `state_extension`
- `system_status_type`
- `track_lifecycle`
- `trust_integrity`

The registry's category value set also retains unused planned categories such as
`inference_type`, `fusion_extension`, `adapter_vendor_namespace`,
`encoding_projection`, and `conformance_class` for future governed entries.
No new entries were added during S1-03C.

## Initial Population Review

The registry includes the planned v1.1.0 experimental entries:

- structured quality block
- `ERROR_ELLIPSE_M`
- formal `data_ref` / `data_refs` behavior
- `EO_FEATURE_CONTRACT`
- `IR_FEATURE_CONTRACT`
- `ACOUSTIC_FEATURE_CONTRACT`
- `NETWORK_FEATURE_CONTRACT`
- `SENSOR_STATUS`
- `PLATFORM_STATUS`
- `RETURN_TO_BASE`
- `LAND`
- `LOITER`
- `SCAN_RF`
- `TRACK_TARGET`
- `CHANGE_SENSOR_MODE`

It also includes the planned future observation modalities, system/status and
assurance candidates, trust/identity/release/replay concepts, track lifecycle
concepts, and companion artifact candidates as reserved or proposed entries.

`MARITIME` remains a reserved observation modality candidate while current
v1.1.0 schema only uses similar broader labels in system/status metric contexts.
That does not make `MARITIME` an observation payload modality.

## Validator Behavior Review

`tools/validate_extension_registry.py` checks:

- YAML load and top-level shape;
- required top-level keys;
- required entry fields;
- duplicate entry names;
- status and category validity;
- version branch requirements;
- reserved/proposed entries cannot claim implemented schema or conformance;
- adopted entries require sufficient schema/policy and implemented conformance;
- experimental entries identify a version branch and at least one implemented
  surface;
- vendor/private namespace format when vendor entries are present;
- core envelope and invariant names cannot be redefined;
- reserved/proposed context leakage into current schemas;
- v1.1.0 experimental command and system entries do not validate under v1.0;
- v1.1.0 experimental command/system/error-ellipse entries validate under
  v1.1.0 where schema support exists.

The validator uses targeted semantic-context checks rather than full enum
extraction for every schema path. This is acceptable for the current registry
because the high-risk reserved/proposed entries are checked in the contexts
where they would become event vocabulary.

S1-03C added one narrow cleanup for D-011: `TAKEOFF` is now treated as an
unregistered reserved schema value for leakage checks. If a current schema enum
or const starts accepting `TAKEOFF`, the registry validator fails with
`REGISTRY_UNREGISTERED_SCHEMA_LEAK`. This does not add `TAKEOFF` to the
registry and does not close D-011.

## Test Coverage Review

`gateway/tests/test_extension_registry.py` covers:

- registry YAML load;
- required entry fields;
- status/category validity;
- current registry validator success;
- CLI success;
- duplicate-name failure;
- reserved/proposed-as-implemented failure;
- adopted-without-coverage failure;
- reserved observation modalities invalid as v1.0/v1.1.0 observations;
- v1.1.0 command task types invalid under v1.0;
- `SENSOR_STATUS` and `PLATFORM_STATUS` invalid under v1.0;
- `TAKEOFF` invalid under v1.0/v1.1.0 and rejected if it appears in a current
  schema enum/const.

## Conformance Integration Review

`tools/validate_conformance.py --strict` remains unchanged by default. Registry
validation runs only with `--extension-registry`. The extension registry flag can
run alone with strict conformance or together with `--profile-projection`.
Missing registry files are not silently skipped because the validator returns
`REGISTRY_FILE_MISSING`.

## D-006 Recommendation

D-006 can be closed. The durable extension registry artifact now exists, has
human and machine-readable forms, is validated by a standalone CLI, is covered by
focused tests, and can run through an explicit conformance flag without changing
default strict behavior.

## Open Issue Status

- D-006: close as complete after this audit.
- D-007: keep open and partially covered. S1-02B/S1-02C cover projection
  invalid-after-decode cases, but broader gateway/CLI binary invalid-after-decode
  tests remain future work.
- D-010: keep open. Precision non-increase exists, but operational Profile M/L
  quantization floors remain undefined.
- D-011: keep open. S1-03C added a validator/test guard against `TAKEOFF`
  becoming schema vocabulary, but the crosswalk typo itself remains for a narrow
  docs cleanup task.

## Unresolved Governance Decisions

- Whether v1.1.0 concepts should remain experimental indefinitely or be promoted
  in a later release decision.
- Whether registry validation should stay opt-in or eventually become part of
  default strict conformance after the format stabilizes.
- Final vendor/private namespace and classified/restricted-name policy.
- Whether companion artifacts should remain registry entries or split into a
  separate manifest.

## Recommended Next Work Item

Proceed to S1-04A - Conformance Class Manifest Plan Only.

## Verification

Final verification for this audit:

```powershell
python tools\validate_extension_registry.py --registry spec\extension-registry.yaml
python tools\validate_conformance.py --strict
python tools\validate_conformance.py --strict --profile-projection
python tools\validate_conformance.py --strict --profile-projection --extension-registry
python -m pytest -q gateway\tests\test_extension_registry.py
python -m pytest
git diff --check
```

Results:

- `python tools\validate_extension_registry.py --registry spec\extension-registry.yaml` ->
  `extension registry ok entries=63`
- `python tools\validate_conformance.py --strict` -> `conformance ok`
- `python tools\validate_conformance.py --strict --profile-projection` ->
  `projection conformance ok total=33`, `conformance ok`
- `python tools\validate_conformance.py --strict --profile-projection --extension-registry` ->
  `projection conformance ok total=33`, `extension registry ok entries=63`,
  `conformance ok`
- `python -m pytest -q gateway\tests\test_extension_registry.py` ->
  `12 passed`
- `python -m pytest` -> `254 passed`
- `git diff --check` -> passed with CRLF conversion warnings only.
