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
- `encoding-negative/`: compact/protobuf invalid-after-decode fixture suites.
- `profile-precision/`: source/projected fixtures for Profile L/M/H precision
  ceilings, utility floors, and conservative quantization.
- `../spec/extension-registry.yaml`: spec-owned machine-readable extension
  registry consumed by optional registry validation.
- `../policy/profile-precision.yaml`: reference conformance default precision
  policy for profile/export validation.
- `../release/zmeta-release-manifest.yaml`: reference hardening-baseline release
  manifest for governed artifact hashes.
- `../release/RELEASE_NOTES_TEMPLATE.md`,
  `../release/ATTESTATION_TEMPLATE.yaml`, and
  `../release/RELEASE_PACKAGE_README.md`: formal release package templates.

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

Encoding-negative validation is opt-in:

```
python tools/validate_encoding_negative.py --compact conformance/encoding-negative/compact-must-fail.jsonl --protobuf conformance/encoding-negative/protobuf-must-fail.jsonl --gateway conformance/encoding-negative/gateway-must-fail.jsonl
python tools/validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative
```

Compact CBOR and protobuf remain encoding projections only. The negative suite
decodes wire inputs to canonical JSON and then proves invalid decoded events fail
schema, policy, projection, gateway/CLI, or conversion-plus-validation checks.
It does not change schemas and does not make new vocabulary valid.

Profile precision policy validation is opt-in:

```
python tools/validate_precision_policy.py --policy policy/profile-precision.yaml --must-pass conformance/profile-precision/must-pass.jsonl --must-fail conformance/profile-precision/must-fail.jsonl
python tools/validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative --precision-policy
```

Precision policy is profile/export policy, not JSON Schema, release policy,
trust policy, emergency mode, UI policy, or transport semantics. The reference
defaults in `policy/profile-precision.yaml` are `reference_conformance_default`
values with `requires_mission_review: true`. They prove conservative
quantization behavior without making new event vocabulary valid.

Release manifest validation is opt-in:

```
python tools/build_release_manifest.py --output release/zmeta-release-manifest.yaml
python tools/validate_release_manifest.py --manifest release/zmeta-release-manifest.yaml
python tools/validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative --precision-policy --release-manifest
```

Example claims use `contract_hash` for the narrow semantic contract hash and
record broader release category hashes under `release_hashes`. They omit
`release_manifest_hash` in S1-09B because the reference manifest includes the
claim files; a formal tagged release may publish post-release attestations if it
needs claim-level manifest hashes.

Release package validation is opt-in and template-only by default:

```
python tools/build_release_package.py --manifest release/zmeta-release-manifest.yaml --output-dir release/package --dry-run --no-signatures
python tools/validate_release_package.py --manifest release/zmeta-release-manifest.yaml --templates-only
python tools/validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative --precision-policy --release-manifest --release-package
```

The release package framework does not create tags, generate signatures, store
keys or secrets, change validation behavior, or make future vocabulary valid.
