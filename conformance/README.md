# Conformance Pack

This folder contains a regression corpus for the canonical
version-discriminated schema plus policy pack:

- `must-pass.jsonl`: events that must validate against schema + policy.
- `must-fail.jsonl`: events that must fail with the specified `expect_code`.
- `profile_projection_field_catalog.yaml`: sidecar field catalog for profile
  projection preservation checks.
- `profile-projection/`: source/projected fixture pairs that prove H/M/L
  thinning preserves event meaning.
- `conformance_classes.yaml`: machine-readable conformance class manifest.
- `claims/`: example implementation claim files for the class manifest.
- `../spec/extension-registry.yaml`: spec-owned machine-readable extension
  registry consumed by optional registry validation.

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

Extension registry validation is also opt-in:

```
python tools/validate_extension_registry.py --registry spec/extension-registry.yaml
python tools/validate_conformance.py --strict --extension-registry
python tools/validate_conformance.py --strict --profile-projection --extension-registry
```

The registry does not make reserved or proposed concepts valid event
vocabulary. v1.1.0 registry entries remain experimental until explicitly
promoted by a later version/release decision.

Conformance class validation is opt-in:

```
python tools/validate_conformance_classes.py --manifest conformance/conformance_classes.yaml
python tools/validate_conformance_classes.py --manifest conformance/conformance_classes.yaml --claims conformance/claims/example-reference-gateway.yaml conformance/claims/example-core-producer.yaml
python tools/validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes
```

Class records and claim files do not make future vocabulary valid. They state
which existing semantic, schema, policy, adapter, gateway, encoding, and
conformance surfaces an implementation satisfies. Future, reserved, and planned
classes are not claimable by current implementation claim files.
