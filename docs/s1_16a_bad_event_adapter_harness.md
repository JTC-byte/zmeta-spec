# S1-16A - Bad-Event Corpus And Adapter Harness

Date: 2026-06-08

## Scope

This hardening slice added opt-in conformance evidence for two gaps:

- semantic bad events that must not be accepted as clean data;
- representative adapter outputs that must preserve ZMeta layer separation,
  UTC-Z timestamps, adapter lineage, schema/policy validity, and external
  promotion evidence.

The work did not change the semantic contract, JSON schemas, policy semantics,
event vocabulary, compact/protobuf encodings, or profile behavior.

## Changes Made

- Added `conformance/bad-events/must-fail.jsonl` and
  `tools/validate_bad_events.py`.
- Added `conformance/adapter-harness/must-pass.jsonl` and
  `tools/validate_adapter_conformance.py`.
- Added opt-in `--bad-events` and `--adapter-harness` flags to
  `tools/validate_conformance.py`.
- Updated KLV ingress template output to include adapter lineage
  `lineage.transform = "translate:klv@<adapter_version>"`.
- Promoted `ZMETA-ADAPTER` to implemented and `ZMETA-COT-PROJECTION` to
  implemented with explicit shared-harness evidence.
- Updated the example reference-stack claim, conformance docs, crosswalk, tool
  docs, adapter docs, and release manifest governance.

## Coverage

Bad-event fixtures cover:

- layer collapse across observation, inference, state, and command examples;
- missing external promotion evidence;
- loop/reflection risk;
- malformed diagnostics;
- payload-local lineage exceeding envelope lineage;
- missing timing quality for operational state.

Adapter fixtures cover representative:

- KrakenSDR RF observation;
- Moth RF observation;
- EO-CV classification inference;
- KLV EO observation;
- CoT promoted external state;
- JREAP promoted external state;
- MAVLink promoted platform state;
- MAVLink TIME_STATUS system event.

## Remaining Limits

- The adapter harness is representative, not exhaustive. It does not certify
  every native-message variant for every adapter.
- `ZMETA-SENSOR-ADAPTER` remains planned until broader sensor-family coverage
  exists.
- Future trust, markings, PNT, model assurance, and cross-domain export
  semantics remain future version-branch work.

## Verification

Verification for this slice:

```powershell
python tools\validate_bad_events.py --must-fail conformance\bad-events\must-fail.jsonl
python tools\validate_adapter_conformance.py --fixtures conformance\adapter-harness\must-pass.jsonl
```

Both validators passed before integration into the full optional conformance
path.
