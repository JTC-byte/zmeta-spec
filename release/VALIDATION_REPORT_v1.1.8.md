# ZMeta v1.1.8 Validation Report

Release date: 2026-06-12
Release target: `v1.1.8`

## Scope

This report covers the v1.1.8 bearing-frame integrity, adapter hardening,
gateway runtime guard, conformance, documentation, and release publication
work. It confirms that the adopted partner stack and review fixes preserve the
locked v1.0 kernel while adding version-scoped v1.1.0 bearing-frame assertion
support.

## Commands

```bash
python tools/validate_release_manifest.py --manifest release/zmeta-release-manifest.yaml
python tools/validate_release_package.py --manifest release/zmeta-release-manifest.yaml --templates-only
python tools/validate_examples.py --strict --require-all
python tools/validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative --precision-policy --release-manifest --release-package --bad-events --adapter-harness
python tools/validate_projection.py --catalog conformance/profile_projection_field_catalog.yaml --must-pass conformance/profile-projection/must-pass.jsonl --must-fail conformance/profile-projection/must-fail.jsonl --quiet
python tools/validate_extension_registry.py --registry spec/extension-registry.yaml
python tools/validate_conformance_classes.py --manifest conformance/conformance_classes.yaml --claims conformance/claims/example-reference-gateway.yaml conformance/claims/example-core-producer.yaml
python tools/validate_encoding_negative.py --compact conformance/encoding-negative/compact-must-fail.jsonl --protobuf conformance/encoding-negative/protobuf-must-fail.jsonl --gateway conformance/encoding-negative/gateway-must-fail.jsonl --quiet
python tools/validate_precision_policy.py --policy policy/profile-precision.yaml --must-pass conformance/profile-precision/must-pass.jsonl --must-fail conformance/profile-precision/must-fail.jsonl --quiet
python tools/validate_bad_events.py --must-fail conformance/bad-events/must-fail.jsonl
python tools/validate_adapter_conformance.py --fixtures conformance/adapter-harness/must-pass.jsonl
python tools/lint_policy_risk_modes.py
python -m pytest -q
python gateway/src/gateway.py --profile H --self-test
python gateway/src/gateway.py --config configs/gateway-config.json --self-test
python gateway/src/gateway.py --config configs/edge-config.json --self-test
python tools/measure_packet_size.py --file examples/zmeta-profile-L-examples.jsonl --encodings compact,proto --max-bytes 240 --max-bytes-encoding compact --summary-only
python tools/filter_risk.py --input examples/zmeta-command-examples.jsonl --preset command --fail-on-drop --quiet
python release/build_mvp_packages.py --version v1.1.8
python release/build_release_bundle.py --version 1.1.8
python tools/build_release_package.py --manifest release/zmeta-release-manifest.yaml --output-dir release/package-v1.1.8 --release-id zmeta-v1.1.8 --release-state formal_release --no-signatures --allow-dirty --clean-output
python tools/validate_release_package.py --manifest release/zmeta-release-manifest.yaml --package-dir release/package-v1.1.8
python release/sign_release_artifacts.py --version v1.1.8 --write-checksums --verify-checksums
git diff --check
```

Compatibility and runtime workflow commands:

```bash
python tools/check_compat.py --target v1.1.8 --strict <each examples/*.jsonl>
python tools/test_workflow_end_to_end.py --profile H
python tools/test_workflow_end_to_end.py --profile M --expect COMMAND_EVENT,SYSTEM_EVENT --listen-port 19011 --forward-port 19012 --cot-port 19013
python tools/test_workflow_end_to_end.py --profile L --listen-port 19021 --forward-port 19022 --cot-port 19023
python tools/test_workflow_end_to_end.py --profile H --encoding cbor --input-encoding cbor --listen-port 19031 --forward-port 19032 --cot-port 19033
python tools/test_workflow_end_to_end.py --profile L --encoding compact --input-encoding compact --no-cot --listen-port 19041 --forward-port 19042 --cot-port 19043
python tools/test_workflow_end_to_end.py --profile H --encoding proto --input-encoding proto --no-cot --listen-port 19051 --forward-port 19052 --cot-port 19053
python tools/test_gateway_live.py --profile H --listen-port 19101 --forward-port 19102 --cot-port 19103
python tools/test_gateway_live.py --profile L --encoding compact --input-encoding compact --no-cot --listen-port 19111 --forward-port 19112 --cot-port 19113
python tools/test_gateway_live.py --profile H --encoding proto --input-encoding proto --no-cot --listen-port 19121 --forward-port 19122 --cot-port 19123
docker compose -f deploy/gateway/docker-compose.yml config
docker compose -f deploy/edge/docker-compose.yml config
```

## Results

- Release manifest validation: `release manifest ok groups=18 artifacts=62`.
- Release package template validation: `release package ok mode=templates`.
- Strict examples validation: `40 passed, 0 failed, 0 warnings`.
- Full kernel conformance: passed with projection, registry, conformance class,
  encoding-negative, precision-policy, release-manifest, release-package,
  bad-event, and adapter-harness checks enabled.
- Projection validation: `37` cases passed.
- Extension registry validation: `57` entries passed.
- Conformance class validation: `34` classes and `2` claims passed.
- Encoding-negative validation: `49` cases passed.
- Precision policy validation: `32` cases passed.
- Bad-event corpus validation: `10` cases passed.
- Adapter conformance harness: `10` cases passed.
- Policy risk-mode lint: passed.
- Full pytest: `435 passed, 108 subtests passed`.
- Gateway Profile H, gateway config, and edge config self-tests: passed.
- Compatibility checks: all seven example JSONL streams passed with
  `--target v1.1.8 --strict`.
- Profile L compact packet-size check: compact max `150` bytes against a
  `240` byte budget.
- Risk filter command preset: passed without drops.
- End-to-end workflow checks: Profile H, Profile M command/system, Profile L,
  CBOR, compact, and protobuf variants passed.
- Live gateway UDP checks: Profile H JSON, Profile L compact, and Profile H
  protobuf paths passed.
- Docker Compose gateway and edge configs rendered successfully. Docker emitted
  local warnings about denied access to `C:\Users\User\.docker\config.json`,
  but both config commands exited successfully and produced rendered configs.
- Release artifacts built:
  - `zmeta-v1.1.8-dist.zip`
  - `zmeta-edge-v1.1.8.zip`
  - `zmeta-gateway-v1.1.8.zip`
  - `zmeta-release-package-v1.1.8.zip`
- Release package output validation: `release package ok mode=package`.
- Checksum generation and verification: `checksums ok: SHA256SUMS_v1.1.8.txt`.
- `git diff --check`: passed with normal Windows LF-to-CRLF working-copy
  warnings.

## Semantic Boundary Checks

- No v1.1.0 or future vocabulary became valid under `zmeta_version: "1.0"`.
- The locked v1.0 schema remains unchanged.
- `bearing.frame` remains optional, v1.1.0-scoped, and single-valued.
- Unknown-frame adapter values are retained only under explicitly named
  non-canonical fields unless deployment configuration asserts true north.
- Accepted-risk and external-promotion projection behavior remains preserved.

## Secret And Signature Safety

- No private key, token, credential, certificate private material, or signing
  secret was committed.
- The release package is generated in no-signature mode unless an approved
  signing authority supplies an external key.

## Remaining Open Work

- D-013 remains open for timing-freshness negative-age semantics.
- D-014 remains open for compact-codec unknown integer key semantics.
