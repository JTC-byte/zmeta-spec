# Conformance Pack

This folder contains a regression corpus for the canonical
version-discriminated schema plus policy pack:

- `must-pass.jsonl`: events that must validate against schema + policy.
- `must-fail.jsonl`: events that must fail with the specified `expect_code`.

Use:

```
python tools/validate_conformance.py --strict
```
