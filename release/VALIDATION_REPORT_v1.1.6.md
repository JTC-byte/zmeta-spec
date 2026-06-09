# ZMeta v1.1.6 Validation Report

Release date: 2026-06-09
Release target: `v1.1.6`

## Scope

This report covers the ZMeta v1.1.6 semantic-risk, kernel-protection, adapter
boundary, and runtime validation release. It confirms that schemas, semantic
contract, policies, extension registry, conformance classes, examples,
adapters, release manifest, release package tooling, and runtime workflows
remain aligned.

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
python -m pytest -q
python gateway/src/gateway.py --profile H --self-test
python gateway/src/gateway.py --config configs/gateway-config.json --self-test
python gateway/src/gateway.py --config configs/edge-config.json --self-test
python tools/measure_packet_size.py --file examples/zmeta-profile-L-examples.jsonl --encodings compact,proto --max-bytes 240 --max-bytes-encoding compact --summary-only
python tools/filter_risk.py --input examples/zmeta-command-examples.jsonl --preset command --fail-on-drop --quiet
python release/build_mvp_packages.py --version v1.1.6
python release/build_release_bundle.py --version 1.1.6
python tools/build_release_package.py --manifest release/zmeta-release-manifest.yaml --output-dir release/package-v1.1.6 --release-id zmeta-v1.1.6 --release-state formal_release --no-signatures
python tools/validate_release_package.py --manifest release/zmeta-release-manifest.yaml --package-dir release/package-v1.1.6
python release/sign_release_artifacts.py --version v1.1.6 --write-checksums --verify-checksums
git diff --check
```

Compatibility and runtime workflow commands were also run:

```bash
python tools/check_compat.py --target v1.1.6 --strict <each examples/*.jsonl>
python tools/test_workflow_end_to_end.py --profile H
python tools/test_workflow_end_to_end.py --profile M --expect COMMAND_EVENT,SYSTEM_EVENT
python tools/test_workflow_end_to_end.py --profile L
python tools/test_workflow_end_to_end.py --profile H --encoding cbor --input-encoding cbor
python tools/test_workflow_end_to_end.py --profile L --encoding compact --input-encoding compact --no-cot
python tools/test_workflow_end_to_end.py --profile H --encoding proto --input-encoding proto --no-cot
python tools/test_gateway_live.py --profile H
python tools/test_gateway_live.py --profile L --encoding compact --input-encoding compact --no-cot
python tools/test_gateway_live.py --profile H --encoding proto --input-encoding proto --no-cot
```

Docker/container release smoke checks were run with disposable containers:

```bash
docker compose -f deploy/gateway/docker-compose.yml config
docker compose -f deploy/edge/docker-compose.yml config
docker run --rm ... gateway profile H JSON
docker run --rm ... gateway profile M JSON
docker run --rm ... gateway profile L compact
```

## Results

- Release manifest validation: passed.
- Release package template validation: passed.
- Release package output validation: passed.
- Strict examples validation: `40 passed, 0 failed, 0 warnings`.
- Full kernel conformance: passed with projection, registry, conformance class,
  encoding-negative, precision-policy, release-manifest, release-package,
  bad-event, and adapter-harness checks enabled.
- Projection validation: `33` cases passed.
- Extension registry validation: `56` entries passed.
- Conformance class validation: `34` classes and `2` claims passed.
- Encoding-negative validation: `49` cases passed.
- Precision policy validation: `32` cases passed.
- Bad-event corpus validation: `9` cases passed.
- Adapter conformance harness: `8` cases passed.
- Full pytest: `365 passed, 108 subtests passed`.
- Gateway Profile H, gateway config, and edge config self-tests: passed.
- Profile L compact packet-size check: compact max `150` bytes against a
  `240` byte budget.
- Risk filter command preset: passed without drops.
- Release edge, gateway, and source bundles: built.
- Release checksums: generated and verified.
- Docker Compose gateway and edge configs: rendered successfully.
- Disposable container runtime profile sweep: passed for Profile H, Profile M,
  and Profile L compact output.

## SDR-Derived Workflow Smoke

The release smoke test generated a deterministic SignalHunter-style PSD binary
capture and ran it through the real SignalHunter adapter. The adapter produced a
ZMeta `OBSERVATION_EVENT/RF`; the runtime sweep then carried the semantically
valid chain through `FUSION_EVENT`, `STATE_EVENT`, CoT output, and MAVLink
MissionIntent conversion.

Literal raw complex IQ demodulation was not claimed or validated. That remains
future work pending real sensor samples and a versioned adapter implementation.

## Drift Checks

- No future vocabulary became valid.
- v1.1.0 remains experimental and isolated from v1.0 validation.
- Operator policy tuning does not override locked schema, vocabulary, layer, or
  interoperability rules.
- Accepted-risk behavior remains explicit, labeled, and filterable.
- CoT egress rejects state payloads carrying raw observation/evidence fields.

## Secret And Signature Safety

- No private key, token, credential, certificate private material, or signing
  secret was committed.
- The release package was generated in no-signature mode.
- Detached signatures were not generated because no approved local signing
  authority was provided for this release.

## Remaining Open Work

- D-003 remains open as roadmap-planned future versioned semantic branches.
- Broader native sensor-adapter certification remains future harness breadth.
- Literal raw IQ support remains future work pending representative sensor data.
