# S1-02C Projection Preservation Audit

Status: COMPLETE
Date: 2026-05-07

## Summary

S1-02B implemented Profile Projection Preservation as a conformance/tooling
layer: a sidecar field catalog, source/projected fixture wrappers, standalone
projection validator, opt-in conformance runner integration, compact/protobuf
decoded projection checks, documentation, and regression tests.

S1-02C audited that implementation against the semantic contract and S1-02A
plan. The audit found no v1.0 schema drift, no semantic contract drift, no
future vocabulary additions, and no evidence that compact CBOR or protobuf were
made semantic authorities.

Small cleanup performed during S1-02C:

- `tools/validate_projection.py` now fails explicitly when a fixture file is
  missing instead of silently skipping it.
- `gateway/tests/test_profile_projection_preservation.py` now covers the
  missing-fixture failure path.
- `conformance/profile-projection/README.md` now documents the stable
  projection failure code set and states that `PROJECTION_FIELD_CHANGED` is a
  fallback, not a replacement for more specific invariant codes.

## Files Inspected

- `docs/s1_02_profile_projection_preservation_plan.md`
- `docs/zmeta_refinement_worklog.md`
- `spec/semantics-contract.md`
- `spec/profile-compatibility.md`
- `spec/profile-projection-field-catalog.md`
- `spec/compact-binary-mapping.md`
- `spec/protobuf-encoding.md`
- `schema/zmeta-event.schema.json`
- `schema/zmeta-event-1.0.schema.json`
- `schema/zmeta-event-1.1.0.schema.json`
- `policy/profiles.yaml`
- `conformance/profile_projection_field_catalog.yaml`
- `conformance/profile-projection/README.md`
- `conformance/profile-projection/context.jsonl`
- `conformance/profile-projection/must-pass.jsonl`
- `conformance/profile-projection/must-fail.jsonl`
- `tools/validate_projection.py`
- `tools/validate_conformance.py`
- `gateway/tests/test_profile_projection_preservation.py`
- `gateway/tests/test_profile_projection_encoding.py`

## Files Changed During S1-02C

- `tools/validate_projection.py`
- `gateway/tests/test_profile_projection_preservation.py`
- `conformance/profile-projection/README.md`
- `docs/s1_02c_projection_preservation_audit.md`
- `docs/zmeta_refinement_worklog.md`
- `docs/zmeta_refinement_handoff.md`

## Semantic Drift Check

S1-02B changed only projection conformance artifacts, docs, tests, and optional
conformance runner integration. It did not alter ZMeta event semantics.

The projection validator compares source/projected pairs after source and
projected events pass canonical schema and policy checks where possible. Profile
thinning is enforced as preservation plus cataloged omission/coarsening, not as
reinterpretation.

## v1.0 Schema Drift Check

`schema/zmeta-event-1.0.schema.json` was not changed by S1-02B or S1-02C.
No v1.1.0 or future fields were made valid under `zmeta_version: "1.0"`.

## Semantic Contract Drift Check

`spec/semantics-contract.md` was not changed by S1-02B or S1-02C. Projection
preservation was implemented as an external conformance layer that follows the
contract rather than altering it.

## Field Catalog Review

`conformance/profile_projection_field_catalog.yaml` covers the required
identity, source, lineage, timing, profile, confidence, TTL, precision, command,
system, and STATE_EVENT-prohibited raw-field rules.

Catalog rules use explicit status and comparison modes, including required,
optional removable, precision reducible, confidence reducible, TTL reducible,
prohibited, never mutable, and contextual behavior.

## Validator Review

`tools/validate_projection.py`:

- Loads JSONL source/projected fixtures.
- Loads the sidecar catalog.
- Validates source and projected events through canonical schema and policy.
- Enforces same-event identity, time, type, subtype, source identity, track ID,
  lineage, confidence, TTL, precision, units, required fields, prohibited
  fields, and profile legality.
- Allows optional omissions only when cataloged.
- Supports explicit legal omission with `projected: null` and
  `allowed_omission_reason`.
- Round-trips compact/protobuf fixtures and compares decoded JSON rather than
  raw bytes.
- Returns nonzero on unexpected pass/fail.
- Fails if fixture files are missing.

## Failure Code Review

The projection failure code set is defined in `tools/validate_projection.py`,
documented in `conformance/profile-projection/README.md`, and asserted by tests.

Specific invariant checks run before catalog fallback equality checks.
`PROJECTION_FIELD_CHANGED` is used only as a fallback for catalog equality drift
where no more specific invariant code applies. Specific codes remain available
for identity, source, track, lineage, confidence, TTL, precision, unit, profile,
schema, policy, and encoding failures.

## Fixture Review

Must-pass fixtures cover:

- H to M STATE_EVENT projection.
- M to L STATE_EVENT projection.
- H to L STATE_EVENT projection.
- Profile L preserved lineage.
- Profile L lowered confidence.
- Profile L shortened TTL.
- COMMAND_EVENT L projection.
- SYSTEM_EVENT TIME_STATUS L projection.
- Optional source fields stripped only where catalog allows.
- Compact Profile L expansion equivalence.
- Protobuf decoded JSON validation.
- Profile L observation omission represented as `projected: null`.

Must-fail fixtures cover:

- Confidence increase.
- TTL increase.
- Precision increase.
- Unit rescale.
- Source rewrite.
- Optional source field rewrite.
- Track ID rewrite.
- Lineage deletion.
- Lineage transform removal.
- OBSERVATION_EVENT to STATE_EVENT same-ID collapse.
- INFERENCE_EVENT to STATE_EVENT same-ID collapse.
- Raw fields inserted into STATE_EVENT.
- Required field removal.
- Event timestamp change.
- Event type change.
- Event subtype change.
- Event ID change.
- Compact decoded projection-invalid JSON.
- Protobuf decoded projection-invalid JSON.
- Profile-illegal projected event.
- Undeclared optional omission.

The Profile L observation omission fixture uses `projected: null` with an
explicit omission reason. It does not rewrite an observation into STATE_EVENT.

## Compact/Protobuf Review

Compact CBOR remains documented as Profile L wire-level encoding that expands to
canonical JSON before validation. Protobuf remains documented as an experimental
encoding projection. The tests validate decoded JSON against projection rules;
raw compact/protobuf bytes are not semantic authority.

## Test Commands And Results

```powershell
python tools\validate_conformance.py --strict
```

Result: `conformance ok`.

```powershell
python tools\validate_conformance.py --strict --profile-projection
```

Result: `projection conformance ok total=33`; `conformance ok`.

```powershell
python tools\validate_projection.py --catalog conformance\profile_projection_field_catalog.yaml --must-pass conformance\profile-projection\must-pass.jsonl --must-fail conformance\profile-projection\must-fail.jsonl --quiet
```

Result: `projection conformance ok total=33`.

```powershell
python -m pytest -q gateway\tests\test_profile_projection_preservation.py gateway\tests\test_profile_projection_encoding.py
```

Result: `11 passed`.

```powershell
python -m pytest
```

Result: `242 passed`.

```powershell
git diff --check
```

Result: passed with Git CRLF conversion warnings only.

## Remaining Coverage Gaps

- D-007 remains partially open. S1-02B covers compact/protobuf decoded JSON
  cases that are schema-valid but projection-invalid. Broader gateway/CLI tests
  for binary inputs that decode to schema-invalid or policy-invalid events
  remain future work.
- Profile M/L precision floors are not specified. S1-02B enforces precision
  non-increase but does not define mission/profile-specific quantization floors.
  This is tracked as D-010.

## Deferred Issue Recommendations

- D-005 can remain closed. Projection preservation is implemented and tested.
- D-007 should remain open and partially covered until broader binary
  invalid-after-decode gateway/CLI tests are added.
- D-010 should track future Profile M/L precision and quantization policy
  floors.

## Recommended Next Work Item

Proceed to S1-03A - Extension Registry Plan Only. Do not implement the registry
or future extension vocabulary as part of S1-02C.
