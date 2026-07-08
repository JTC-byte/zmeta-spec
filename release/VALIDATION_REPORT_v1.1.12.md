# ZMeta v1.1.12 Validation Report

Release date: 2026-07-08
Release target: `v1.1.12`

## Scope

This report covers the ZMeta v1.1.12 governance and honesty closeout patch:
the extension-registry promotion evidence bar, the S1-11B machine-readable
future-branch roadmap (artifact, governance companion, validator, tests, and
release-manifest group), removal of fabricated `lineage.based_on` from six
ingress adapters with refusal semantics for mandatory-lineage events,
gateway UDP send-failure containment with new `send_failure` diagnostics,
mapping-pack and honesty-primitive enforcement-home documentation, and the
handoff standing-defaults closeout. It confirms that schemas, the semantic
contract, policy behavior, and v1.0/v1.1.0 vocabulary are unchanged, and
that the adapter and gateway behavior changes are pinned by fixtures and
tests.

## Commands

```bash
python tools/build_release_manifest.py --release-id zmeta-v1.1.12 --release-name "ZMeta v1.1.12" --release-status formal_release --release-date 2026-07-08 --branch main --update-claims
python tools/validate_release_manifest.py --manifest release/zmeta-release-manifest.yaml
python tools/validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative --precision-policy --release-manifest --release-package --bad-events --adapter-harness
python tools/validate_examples.py --strict --require-all
python tools/lint_policy_risk_modes.py
python tools/validate_future_roadmap.py
python tools/validate_adapter_conformance.py
python -m pytest -q
python tools/test_workflow_end_to_end.py
python tools/test_workflow_end_to_end.py --profile M --listen-port 5665 --forward-port 5666 --cot-port 5667
python tools/test_gateway_live.py --listen-port 5675 --forward-port 5676 --cot-port 5677
python tools/test_gateway_live.py --profile L --encoding compact --input-encoding compact --listen-port 5695 --forward-port 5696 --cot-port 5697
python gateway/src/gateway.py --profile H --self-test
python gateway/src/gateway.py --config configs/gateway-config.json --self-test
python gateway/src/gateway.py --config configs/edge-config.json --self-test
python tools/check_compat.py --target v1.1.12 --strict <each examples/*.jsonl>
python tools/measure_packet_size.py --file examples/zmeta-profile-L-examples.jsonl --encodings compact --max-bytes 240 --summary-only
python release/build_mvp_packages.py --version v1.1.12
python release/build_release_bundle.py --version 1.1.12
python tools/build_release_package.py --manifest release/zmeta-release-manifest.yaml --output-dir release/package-v1.1.12 --release-id zmeta-v1.1.12 --release-state formal_release --no-signatures --allow-dirty --clean-output
python tools/validate_release_package.py --manifest release/zmeta-release-manifest.yaml --package-dir release/package-v1.1.12
python release/sign_release_artifacts.py --version v1.1.12 --write-checksums --verify-checksums
git diff --check
```

## Results

- Release manifest validation: passed — `release manifest ok groups=19
  artifacts=70`; manifest and example claim hashes regenerated for
  `zmeta-v1.1.12` (new `future_branch_roadmap` group registered).
- Full kernel conformance: `conformance ok` with all flags enabled.
- Projection validation: `37` cases passed.
- Extension registry validation: `61` entries passed.
- Conformance class validation: `34` classes and `2` claims passed.
- Encoding-negative validation: `50` cases passed.
- Precision policy validation: `32` cases passed.
- Bad-event corpus validation: `23` cases passed.
- Adapter conformance harness: `11` cases passed (fixtures updated to pin
  honest lineage behavior: default observation outputs must omit lineage;
  the eo-cv inference fixture pins real `lineage.based_on` /
  `payload.based_on` from a UUIDv7 `source_event_id`; the mavlink state
  fixture supplies and pins real `based_on`; one new
  caller-supplied-lineage kraken fixture).
- Future-branch roadmap validation: `future-branch roadmap ok candidates=18
  rejected_or_deferred=3`.
- Strict examples validation: `47 passed, 0 failed, 0 warnings` across eight
  corpora.
- Policy risk-mode lint: `policy risk mode lint ok`.
- Full pytest: `465 passed, 110 subtests passed` (new: future-roadmap
  validator tests, eo-cv ingress tests, mavlink lineage refusal/fallback
  tests, KLV lineage-omission tests, gateway send-failure guard tests
  including a real-socket oversize UDP proof; release-manifest identity pins
  updated to `zmeta-v1.1.12` / `2026-07-08`).
- End-to-end workflow tests: Profile H and Profile M passed (observation,
  inference, fusion, state forwarding plus CoT output).
- Live gateway tests: JSON and compact-encoding paths passed, including
  command duplicate handling, TASK_ACK, state forwarding, and CoT XML
  output.
- Gateway Profile H, gateway config, and edge config self-tests: passed.
- Compatibility checks: all eight example JSONL streams passed with
  `--target v1.1.12 --strict` (`issues=0 failed=0 warnings=0` each).
- Packet-size check: compact Profile L `min=98 avg=116.0 max=150` under the
  240-byte ceiling.
- Release artifacts built:
  - `zmeta-v1.1.12-dist.zip`
  - `zmeta-edge-v1.1.12.zip`
  - `zmeta-gateway-v1.1.12.zip`
  - `zmeta-release-package-v1.1.12.zip`
- Release package output validation: passed (`release package ok
  mode=package`).
- Checksum generation and verification: `checksums ok:
  SHA256SUMS_v1.1.12.txt`.
- `git diff --check`: passed with normal Windows LF-to-CRLF working-copy
  warnings only.

## Validation Scope Notes

- Docker Compose config rendering was not re-exercised in this session; the
  deploy YAML files are unchanged since the last validated baseline.
- The adapter lineage change is a reference-implementation honesty
  correction: schema and policy already permitted lineage omission for
  observations and already required real parent semantics; the adapters now
  comply instead of fabricating. Gateway validation behavior is unchanged.
- The gateway send guard is containment-only: no accept/reject semantics,
  encoding, ordering, or event content changed; failed sends are dropped
  with an explicit diagnostic instead of terminating the process.

## Semantic Boundary Checks

- No v1.1.0 or future vocabulary became valid under `zmeta_version: "1.0"`,
  and no new vocabulary became valid under `"1.1.0"`.
- The locked v1.0 schema, the v1.1.0 schema, the semantic contract text, and
  all policy YAML behavior are unchanged.
- The future-branch roadmap and the promotion evidence bar are governance
  artifacts only; the roadmap validator enforces that no roadmap status can
  assert validity beyond what the extension registry supports.
- Adapter refusal semantics (mavlink STATE, eo-cv INFERENCE) implement
  already-normative contract rules (4.8, 11.3); nothing was loosened.

## Secret And Signature Safety

- No private key, token, credential, certificate private material, or
  signing secret was committed.
- The release package is generated in no-signature mode. No local signing
  key was present in the build environment.
- Detached signatures were not generated in this environment; the release
  authority is establishing a signing process and may attach signatures at
  or after publication.

## Remaining Open Work

- Release-authority signing process (in progress with the maintainer as of
  2026-07-08); whether future releases publish detached signatures and
  post-release claim attestations follows from it.
- Whether v1.1.0 remains permanently `experimental` or is adopted as a
  baseline.
- D-003 closure decision now that the S1-11B roadmap artifact exists
  (closure recommended; maintainer call).
- Broader native sensor-adapter certification remains future harness
  breadth, driven by real sensor captures.
- Closed payload schemas plus producer conformance remain the future
  mitigation for the arbitrarily-renamed-field denylist residual.
