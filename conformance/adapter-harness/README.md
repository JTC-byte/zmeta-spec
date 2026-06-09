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
