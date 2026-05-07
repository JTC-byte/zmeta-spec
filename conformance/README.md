# Conformance Pack

This folder contains a regression corpus for the canonical
version-discriminated schema plus policy pack:

- `must-pass.jsonl`: events that must validate against schema + policy.
- `must-fail.jsonl`: events that must fail with the specified `expect_code`.
- `profile_projection_field_catalog.yaml`: sidecar field catalog for profile
  projection preservation checks.
- `profile-projection/`: source/projected fixture pairs that prove H/M/L
  thinning preserves event meaning.

Use:

```
python tools/validate_conformance.py --strict
```

Profile projection preservation is opt-in for the conformance runner:

```
python tools/validate_conformance.py --strict --profile-projection
```

It can also be run directly:

```
python tools/validate_projection.py --catalog conformance/profile_projection_field_catalog.yaml --must-pass conformance/profile-projection/must-pass.jsonl --must-fail conformance/profile-projection/must-fail.jsonl
```
