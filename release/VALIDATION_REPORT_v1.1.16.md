# ZMeta v1.1.16 Validation Report

Release date: 2026-07-21
Release target: `v1.1.16`

## Scope

This report covers the ZMeta v1.1.16 release: the merge of PR #7
(`adapters/mapping-packs/edge-comms-bladerf/` — the first external
real-capture corpus: two real bladeRF / ROS2 EW `rf_detection` inputs
paired with schema-valid RF `OBSERVATION_EVENT` expected outputs) plus
the maintainer review fixes applied on merge (frame-unlabeled
heading-derived bearing demoted to explicitly named native features
per contract 6.4 and AUTHORING rule 2; unasserted `1_SIGMA`
measurement-error metric dropped; `features.timestamp_source`
provenance added; `mapping.yaml` reconciled with the fixtures;
FFT-bin-width `bandwidth_hz` convention documented). No schema,
policy, or event-vocabulary changes; the locked v1.0 kernel's
semantics are unchanged.

Review method: maintainer close read plus an independent adversarial
review attempting refutation against the contract, the validators,
and the kraken/moth reference precedent, with every expected-output
field walked back to an input field or a documented convention. Both
fixtures pass `tools/validate.py --profile H --strict` before and
after the fixes.

## Commands

```bash
python tools/build_release_manifest.py --release-id zmeta-v1.1.16 --release-name "ZMeta v1.1.16" --release-status formal_release --release-date 2026-07-21 --branch main --update-claims
python tools/validate_release_manifest.py --manifest release/zmeta-release-manifest.yaml
python tools/compute_contract_hash.py
python tools/validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative --precision-policy --release-manifest --release-package --bad-events --adapter-harness
python tools/validate_examples.py --strict --require-all
python tools/lint_policy_risk_modes.py
python tools/validate_conformance_classes.py --claims conformance/claims/example-core-producer.yaml conformance/claims/example-reference-gateway.yaml --verify-contract-hash
python -m pytest -q
python -m pytest -q gateway/tests/test_risk_filter_cli.py
python tools/validate.py --file adapters/mapping-packs/edge-comms-bladerf/tests/case-01-vhf-orbit/expected.json --profile H --strict
python tools/validate.py --file adapters/mapping-packs/edge-comms-bladerf/tests/case-02-cband-fft/expected.json --profile H --strict
python tools/test_workflow_end_to_end.py
python tools/test_workflow_end_to_end.py --profile M --listen-port 5665 --forward-port 5666 --cot-port 5667
python tools/test_gateway_live.py --listen-port 5675 --forward-port 5676 --cot-port 5677
python tools/test_gateway_live.py --profile L --encoding compact --input-encoding compact --listen-port 5695 --forward-port 5696 --cot-port 5697
python gateway/src/gateway.py --profile H --self-test
python gateway/src/gateway.py --config configs/gateway-config.json --self-test
python gateway/src/gateway.py --config configs/edge-config.json --self-test
python tools/check_compat.py --target v1.1.16 --strict <each examples/*.jsonl>
python tools/measure_packet_size.py --file examples/zmeta-profile-L-examples.jsonl --encodings compact --max-bytes 240 --summary-only
python release/build_mvp_packages.py --version v1.1.16
python release/build_release_bundle.py --version 1.1.16
python tools/build_release_package.py --manifest release/zmeta-release-manifest.yaml --output-dir release/package-v1.1.16 --release-id zmeta-v1.1.16 --release-state formal_release --no-signatures --allow-dirty --clean-output
python tools/validate_release_package.py --manifest release/zmeta-release-manifest.yaml --package-dir release/package-v1.1.16
docker compose -f gateway/docker-compose.yml up -d --build   # then replay + down
python release/sign_release_artifacts.py --version v1.1.16 --write-checksums --verify-checksums
git diff --check
```

## Results

- Release manifest validation: passed — `release manifest ok groups=19
  artifacts=70`; manifest and claim hashes regenerated for
  `zmeta-v1.1.16`.
- Full kernel conformance: `conformance ok pass=20 fail=27` with all
  flags (adapter harness 39, bad-events 27).
- Strict examples: `51/51` (`--require-all`). Policy risk-mode lint:
  passed.
- Conformance classes: `34` classes, `2` claims, verified with
  `--verify-contract-hash` against the manifest's recorded value.
- Full pytest: `687 passed, 172 subtests passed`, zero failures.
- Consumer risk-filter presets: `6 passed`.
- Pack fixtures: both cases pass strict H-profile validation after the
  review fixes.
- Workflow end-to-end (H and M), live gateway (JSON and compact-L,
  exit 0), gateway self-tests (H, gateway-config, edge-config): all
  passed / `self-test: ok`.
- Migration compatibility sweep: all `9` example corpora pass
  `check_compat --target v1.1.16 --strict`.
- Profile L packet size: `COMPACT min=98 avg=116.0 max=150` (budget
  240) — passed.
- Bundles and package: all three zips built; `release/package-v1.1.16`
  validated (`release package ok mode=package`); the release-package
  zip auto-built at checksum time.
- Containerized gateway: build, run, canonical-corpus replay with no
  violation output, clean teardown.
- `git diff --check`: clean.
- Checksums: `SHA256SUMS_v1.1.16.txt` generated (LF) and verified.
- Known benign observation, verified during this cut: the
  `compute_contract_hash.py` raw-byte `policy_hash` print differs from
  the v1.1.15 battery because branch-checkout/merge operations
  re-materialized working-copy line endings (the documented Windows
  CRLF class); the canonicalized manifest `policy_bundle_hash` is
  byte-identical between the v1.1.15 and v1.1.16 manifests
  (`sha256:6cb5918c...`), proving policy content unchanged. The
  manifest's canonicalized hashes remain the authoritative gates.

## Signing Decision

Checksums-only release: no detached signatures are attached, and the
release notes state this. Signature generation remains the maintainer's
external release-authority process.
