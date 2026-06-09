# S1-18B - End-to-End Stack and Runtime Audit

Date: 2026-06-08

## Scope

This audit checked the tracked ZMeta stack end to end after the semantic
contract, risk adjudication, external promotion, kernel-protection, and
operator risk-filtering work.

The target was to confirm that live files still conform to the semantic
contract and that runtime workflows still behave correctly across:

- schemas, policy, and semantic contract surfaces;
- conformance fixtures and claim metadata;
- examples and version compatibility;
- gateway validation and live UDP forwarding;
- compact, CBOR, and protobuf encodings;
- ingress and egress adapter boundaries;
- risk filtering and bandwidth-oriented Profile L behavior;
- release manifest, release-package planning, MVP bundles, and deployment
  compose files;
- docs and source-doc archive posture.

## Audit Findings

The tracked stack conforms to the current ZMeta semantic contract after the
cleanup made in this slice.

No live tracked file was found making future vocabulary current, weakening the
locked schema/interoperability rules, or treating operator risk settings as
semantic authority. Historical release notes, old checksum files, and prior
audit docs still reference older versions by design. The current live
compatibility target and release surfaces remain aligned to `v1.1.5`.

Ignored local artifacts are expected local state: local notes, Python caches,
pytest caches, release ZIP outputs, bundle smoke directories, and now `.tmp/`
package-smoke extraction directories. Those files are not part of the governed
repo baseline.

Example conformance claim files remain examples rather than release-grade
certificates. Their placeholder metadata is documented and does not function as
a live attestation.

## Cleanup Made

One adapter-boundary hardening issue was corrected during the audit.

The gateway validation path already rejects state events that carry raw
observation or evidence fields. Direct library callers could still call the CoT
egress adapter with a malformed `STATE_EVENT` payload containing fields such as
`features`, `raw_features`, `modality`, `data_ref`, or `data_refs` and receive a
projected CoT event.

That direct-call path now fails closed:

- `adapters/egress/cot/zmeta_to_cot.py` refuses non-dict payloads and state
  payloads containing raw observation/evidence fields.
- `adapters/egress/cot/test_zmeta_to_cot.py` covers the rejection.
- `adapters/egress/cot/README.md` documents the expectation that CoT egress
  consumes only semantically valid `STATE_EVENT` payloads.

This does not change schemas, event vocabulary, policy YAML semantics,
encodings, profile projection, or gateway mutation behavior. It makes the
direct adapter path match the same layer-separation rule already enforced by
the gateway.

## Folder-by-Folder Result

| Area | Result |
| --- | --- |
| `spec/` | Semantic contract, extension registry, conformance classes, profile projection, precision policy, release hash, and signing docs remain aligned. Future-extension concepts remain non-claimable. |
| `schema/` | v1.0 remains locked. v1.1.0 examples and schemas stay version-scoped. No future vocabulary leakage was found. |
| `policy/` | Timing, lineage, producer authority, profile precision, and risk behavior preserve locked/tunable/advisory boundaries. Soft acceptance remains label-driven and filterable. |
| `configs/` | Runtime knobs select profiles, policy files, encodings, risk behavior, and failure modes without redefining semantics. |
| `gateway/` | Self-tests, policy validation, runtime degradation labels, command duplicate handling, binary decode paths, and risk-filter tests passed. |
| `adapters/` | Ingress and egress boundaries remain schema/policy-bound. CoT egress direct-call hardening was added. Broader native sensor-adapter certification remains future breadth work. |
| `tools/` | Validators, compatibility checks, release tooling, risk filter, packet sizing, and live workflow tools passed their exercised paths. |
| `conformance/` | Projection, extension registry, class claims, encoding-negative, precision, bad-event, and adapter-harness suites passed. |
| `examples/` | All required example streams passed strict validation. All example streams passed `v1.1.5` compatibility checks. |
| `release/` | Manifest validation, release-package template validation, release-package dry-run, and MVP bundle build/smoke checks passed. |
| `deploy/` | Gateway and edge Docker Compose files rendered valid configs. Docker emitted a local `config.json` access warning, but compose config exited successfully. |
| `docs/` | Historical notes remain audit trail. `source-docs/` remains a legacy archive, with `spec/semantics-contract.md` as normative. |

## Runtime Workflow Matrix

Live gateway workflow checks passed across profiles and encodings:

| Workflow | Result |
| --- | --- |
| Profile H JSON with CoT output | Forwarded `OBSERVATION_EVENT`, `INFERENCE_EVENT`, `FUSION_EVENT`, `STATE_EVENT`; produced CoT output. |
| Profile M JSON with command/system events | Forwarded `OBSERVATION_EVENT`, `FUSION_EVENT`, `STATE_EVENT`, `COMMAND_EVENT`, `SYSTEM_EVENT`; produced CoT output. |
| Profile L JSON with CoT output | Forwarded `STATE_EVENT`; produced CoT output. |
| Profile H CBOR input/output | Forwarded `OBSERVATION_EVENT`, `INFERENCE_EVENT`, `FUSION_EVENT`, `STATE_EVENT`; produced CoT output. |
| Profile L compact input/output | Forwarded `STATE_EVENT`. |
| Profile H protobuf input/output | Forwarded `OBSERVATION_EVENT`, `INFERENCE_EVENT`, `FUSION_EVENT`, `STATE_EVENT`. |
| Gateway live Profile H command path | Forwarded command, generated duplicate `TASK_ACK`, forwarded state, produced CoT output. |
| Gateway live Profile L compact command path | Forwarded command and generated duplicate `TASK_ACK`. |
| Gateway live Profile H protobuf command path | Forwarded command and generated duplicate `TASK_ACK`. |

Package workflow checks also passed:

- release package dry-run planned the expected metadata, notes, attestation, and
  checksum files without writing a package;
- MVP edge and gateway ZIPs built successfully;
- both extracted ZIPs passed `gateway.py --self-test` against their included
  files.

## Verification

Validation commands run for this audit:

```powershell
python -m pytest -q adapters\egress\cot
# 9 passed

python tools\validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative --precision-policy --release-manifest --release-package --bad-events --adapter-harness
# projection conformance ok total=33
# extension registry ok entries=56
# conformance classes ok classes=34 claims=2
# encoding negative ok total=49
# profile precision policy ok total=32
# bad-event corpus ok total=9
# adapter conformance ok total=8
# conformance ok

python tools\validate_examples.py --strict --require-all
# overall total=40 passed=40 failed=0 warnings=0

python tools\validate_release_manifest.py --manifest release\zmeta-release-manifest.yaml
# release manifest ok groups=17 artifacts=60

python tools\validate_release_package.py --manifest release\zmeta-release-manifest.yaml --templates-only
# release package ok mode=templates

python tools\validate_projection.py --catalog conformance\profile_projection_field_catalog.yaml --must-pass conformance\profile-projection\must-pass.jsonl --must-fail conformance\profile-projection\must-fail.jsonl --quiet
# projection conformance ok total=33

python tools\validate_extension_registry.py --registry spec\extension-registry.yaml
# extension registry ok entries=56

python tools\validate_conformance_classes.py --manifest conformance\conformance_classes.yaml --claims conformance\claims\example-reference-gateway.yaml conformance\claims\example-core-producer.yaml
# conformance classes ok classes=34 claims=2

python tools\validate_encoding_negative.py --compact conformance\encoding-negative\compact-must-fail.jsonl --protobuf conformance\encoding-negative\protobuf-must-fail.jsonl --gateway conformance\encoding-negative\gateway-must-fail.jsonl --quiet
# encoding negative ok total=49

python tools\validate_precision_policy.py --policy policy\profile-precision.yaml --must-pass conformance\profile-precision\must-pass.jsonl --must-fail conformance\profile-precision\must-fail.jsonl --quiet
# profile precision policy ok total=32

python tools\validate_bad_events.py --must-fail conformance\bad-events\must-fail.jsonl
# bad-event corpus ok total=9

python tools\validate_adapter_conformance.py --fixtures conformance\adapter-harness\must-pass.jsonl
# adapter conformance ok total=8

Get-ChildItem examples\*.jsonl | ForEach-Object { python tools\check_compat.py --target v1.1.5 --strict $_.FullName }
# all 7 example streams passed with issues=0 failed=0 warnings=0

python gateway\src\gateway.py --profile H --self-test
python gateway\src\gateway.py --config configs\gateway-config.json --self-test
python gateway\src\gateway.py --config configs\edge-config.json --self-test
# each self-test passed with 40 examples, conformance ok, and self-test: ok

python tools\test_workflow_end_to_end.py --profile H --listen-port 5585 --forward-port 5586 --cot-port 6980
python tools\test_workflow_end_to_end.py --profile M --expect COMMAND_EVENT,SYSTEM_EVENT --listen-port 5595 --forward-port 5596 --cot-port 6990
python tools\test_workflow_end_to_end.py --profile L --listen-port 5605 --forward-port 5606 --cot-port 7000
python tools\test_workflow_end_to_end.py --profile H --encoding cbor --input-encoding cbor --listen-port 5615 --forward-port 5616 --cot-port 7010
python tools\test_workflow_end_to_end.py --profile L --encoding compact --input-encoding compact --no-cot --listen-port 5625 --forward-port 5626 --cot-port 7020
python tools\test_workflow_end_to_end.py --profile H --encoding proto --input-encoding proto --no-cot --listen-port 5635 --forward-port 5636 --cot-port 7030
# live workflow matrix passed

python tools\test_gateway_live.py --profile H --listen-port 5645 --forward-port 5646 --cot-port 7040
python tools\test_gateway_live.py --profile L --encoding compact --input-encoding compact --no-cot --listen-port 5655 --forward-port 5656 --cot-port 7050
python tools\test_gateway_live.py --profile H --encoding proto --input-encoding proto --no-cot --listen-port 5665 --forward-port 5666 --cot-port 7060
# live gateway command/state matrix passed

python tools\measure_packet_size.py --file examples\zmeta-profile-L-examples.jsonl --encodings compact,proto --max-bytes 240 --max-bytes-encoding compact --summary-only
# COMPACT max=150; PROTO max=301; compact budget passed

python tools\filter_risk.py --list-presets
# listed aar, audit, autonomy, command, display, fusion, state

python tools\filter_risk.py --input examples\zmeta-command-examples.jsonl --preset command --fail-on-drop --quiet
# command preset passed without drops

python tools\compute_contract_hash.py
# contract_hash=9aa997d264d71575eb24c21ba93935a4d4165a24aef07bae0e6ced7e40949590

python -m pytest -q
# 365 passed, 108 subtests passed

python tools\build_release_package.py --manifest release\zmeta-release-manifest.yaml --output-dir release\package-audit --release-id zmeta-audit-runtime --release-state audit_runtime_sweep --dry-run --no-signatures
# dry-run planned expected release-package outputs

docker compose -f deploy\gateway\docker-compose.yml config
docker compose -f deploy\edge\docker-compose.yml config
# both compose configs rendered successfully; local Docker config access warning only

python release\build_mvp_packages.py --version vci
# produced release\zmeta-edge-vci.zip and release\zmeta-gateway-vci.zip

python gateway\src\gateway.py --config configs\edge-config.json --self-test
# run from extracted edge ZIP; self-test passed

python gateway\src\gateway.py --config configs\gateway-config.json --self-test
# run from extracted gateway ZIP; self-test passed
```

## Residual Work

No blocking semantic-contract drift or stale tracked file was found.

Remaining work is optional breadth, not a discovered conformance failure:

- D-003 remains open as roadmap-planned future versioned semantic branches.
- Broader native sensor-adapter certification remains future harness breadth.
- Full Docker container boot was not required for this audit because live
  gateway runtime paths were exercised directly and compose configs rendered
  successfully. A later deployment audit can run container boot/pull tests in an
  environment with approved image and dependency access.
- Formal detached release signatures remain a release-authority operation,
  unchanged from `v1.1.5`.
