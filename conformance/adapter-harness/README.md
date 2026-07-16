# Adapter Harness

This suite validates representative adapter outputs as ZMeta events. It is a
shared harness for layer separation, timestamp normalization, lineage transform
evidence, schema validity, hard policy validity, and external-promotion
metadata where an adapter emits state from lossy or external reports.

Use:

```powershell
python tools\validate_adapter_conformance.py --fixtures conformance\adapter-harness\must-pass.jsonl
python tools\validate_conformance.py --strict --adapter-harness
```

The harness is fixture-driven. It does not require every adapter to expose the
same Python API, and it does not make lossy external projections authoritative
without promotion evidence.

An advisory JSON Schema for fixture lines lives at
`conformance/adapter-harness/fixture.schema.json`; `tools/check_adapter.py
--fixtures` lints against it before running the harness to catch key typos.
The harness itself remains the behavioral authority.

Beyond presence checks (`required_paths`/`forbidden_paths`), a fixture may pin
exact output values with an optional `expected_values` map of dotted path to
expected value. Numeric expectations compare with a small absolute tolerance
(1e-6); other values compare by equality; a boolean never matches a
non-boolean (a `true` pin cannot be satisfied by `1`/`1.0` output); a missing
path is reported as a distinct failure. This is how the corpus proves value-level contracts such as
the bearing reference-frame rotation (array-relative DOA plus platform heading
equals canonical true-north `bearing.az_deg`).
