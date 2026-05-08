# ZMeta v1.1.5 Validation Report

Release date: 2026-05-07
Release target: `v1.1.5`

## Scope

This report covers the hardened ZMeta baseline and formal release packaging framework. The validation
confirms that schemas, semantic contract, extension registry, conformance classes, release manifest,
release package tooling, and conformance paths remain aligned for the v1.1.5 release.

## Commands

```bash
python tools/validate_release_manifest.py --manifest release/zmeta-release-manifest.yaml
python tools/build_release_package.py --manifest release/zmeta-release-manifest.yaml --output-dir release/package --dry-run --no-signatures
python tools/validate_release_package.py --manifest release/zmeta-release-manifest.yaml --templates-only
python tools/compute_contract_hash.py
python tools/validate_conformance.py --strict
python tools/validate_conformance.py --strict --profile-projection
python tools/validate_conformance.py --strict --profile-projection --extension-registry
python tools/validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes
python tools/validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative
python tools/validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative --precision-policy
python tools/validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative --precision-policy --release-manifest
python tools/validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative --precision-policy --release-manifest --release-package
python tools/validate_projection.py --catalog conformance/profile_projection_field_catalog.yaml --must-pass conformance/profile-projection/must-pass.jsonl --must-fail conformance/profile-projection/must-fail.jsonl --quiet
python tools/validate_extension_registry.py --registry spec/extension-registry.yaml
python tools/validate_conformance_classes.py --manifest conformance/conformance_classes.yaml --claims conformance/claims/example-reference-gateway.yaml conformance/claims/example-core-producer.yaml
python tools/validate_encoding_negative.py --compact conformance/encoding-negative/compact-must-fail.jsonl --protobuf conformance/encoding-negative/protobuf-must-fail.jsonl --gateway conformance/encoding-negative/gateway-must-fail.jsonl --quiet
python tools/validate_precision_policy.py --policy policy/profile-precision.yaml --must-pass conformance/profile-precision/must-pass.jsonl --must-fail conformance/profile-precision/must-fail.jsonl --quiet
python -m pytest -q gateway/tests/test_release_package.py
python -m pytest
git diff --check
```

## Results

- Release manifest validation: passed.
- Release package template validation: passed.
- Contract hash computation: passed.
- Strict conformance validation: passed.
- Projection validation: passed.
- Extension registry validation: passed.
- Conformance class validation: passed.
- Encoding-negative validation: passed.
- Precision-policy validation: passed.
- Focused release package tests: passed.
- Full pytest: passed.
- Whitespace diff check: passed.

## Drift Checks

- JSON schemas remained unchanged during release packaging audit.
- Semantic contract remained unchanged during release packaging audit.
- Extension registry remained unchanged during release packaging audit.
- Conformance class manifest remained valid.
- No new event vocabulary became valid.
- v1.1.0 remained experimental and isolated from v1.0 validation.

## Secret And Signature Safety

- No real git tag was created during release packaging implementation or audit.
- No real signature was generated or committed during release packaging implementation or audit.
- No private key, token, credential, certificate private material, or signing secret was committed.
- Release package signing remains external to the repository and controlled by the release authority.

## Remaining Open Work

- D-003 remains open as roadmap planned for future versioned semantic branches.
- D-004 is closed as removed from ZMeta scope.
- D-012 is closed after the release packaging framework audit.
