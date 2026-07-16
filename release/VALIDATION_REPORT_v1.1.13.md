# ZMeta v1.1.13 Validation Report

Release date: 2026-07-16
Release target: `v1.1.13`

## Scope

This report covers the ZMeta v1.1.13 onboarding and machine-checked refusal
patch: the adapter authoring guide and its red-team hardening, the worked
example-vendor exercise adapter, the `tools/check_adapter.py` ladder
wrapper, the EO full-chain example corpus, the GitHub intake templates and
README first-contact restructure, the worklog retention pass, and the
adapter-harness refusal-fixture capability (`expect.event_count`) with the
example-vendor emission and refusal fixtures. It confirms that schemas, the
semantic contract, policy behavior, and v1.0/v1.1.0 vocabulary are
unchanged, and that the new harness capability is pinned by tests in both
directions (a genuine refusal passes; an emission against an
`event_count: 0` pin fails with `ADAPTER_EVENT_COUNT_MISMATCH`).

## Commands

```bash
python tools/build_release_manifest.py --release-id zmeta-v1.1.13 --release-name "ZMeta v1.1.13" --release-status formal_release --release-date 2026-07-16 --branch main --update-claims
python tools/validate_release_manifest.py --manifest release/zmeta-release-manifest.yaml
python tools/validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative --precision-policy --release-manifest --release-package --bad-events --adapter-harness
python tools/validate_examples.py --strict --require-all
python tools/lint_policy_risk_modes.py
python tools/validate_future_roadmap.py
python tools/validate_adapter_conformance.py
python -m pytest -q
python -m pytest -q gateway/tests/test_risk_filter_cli.py
python tools/test_workflow_end_to_end.py
python tools/test_workflow_end_to_end.py --profile M --listen-port 5665 --forward-port 5666 --cot-port 5667
python tools/test_gateway_live.py --listen-port 5675 --forward-port 5676 --cot-port 5677
python tools/test_gateway_live.py --profile L --encoding compact --input-encoding compact --listen-port 5695 --forward-port 5696 --cot-port 5697
python gateway/src/gateway.py --profile H --self-test
python gateway/src/gateway.py --config configs/gateway-config.json --self-test
python gateway/src/gateway.py --config configs/edge-config.json --self-test
python tools/check_compat.py --target v1.1.13 --strict <each examples/*.jsonl>
python tools/measure_packet_size.py --file examples/zmeta-profile-L-examples.jsonl --encodings compact --max-bytes 240 --summary-only
python release/build_mvp_packages.py --version v1.1.13
python release/build_release_bundle.py --version 1.1.13
python tools/build_release_package.py --manifest release/zmeta-release-manifest.yaml --output-dir release/package-v1.1.13 --release-id zmeta-v1.1.13 --release-state formal_release --no-signatures --allow-dirty --clean-output
python tools/validate_release_package.py --manifest release/zmeta-release-manifest.yaml --package-dir release/package-v1.1.13
docker compose -f gateway/docker-compose.yml up -d   # then replay + logs + down
python release/sign_release_artifacts.py --version v1.1.13 --write-checksums --verify-checksums
git diff --check
```

## Results

- Release manifest validation: passed — `release manifest ok groups=19
  artifacts=70`; manifest and example claim hashes regenerated for
  `zmeta-v1.1.13` (the `must-pass.jsonl` and
  `tools/validate_adapter_conformance.py` hashes re-baseline with the
  refusal-fixture work).
- Full kernel conformance: `conformance ok` with all flags enabled.
- Projection validation: `37` cases passed.
- Extension registry validation: `61` entries passed.
- Conformance class validation: `34` classes and `2` claims passed.
- Encoding-negative validation: `50` cases passed.
- Precision policy validation: `32` cases passed.
- Bad-event corpus validation: `23` cases passed.
- Adapter conformance harness: `15` cases passed (11 prior + the
  example-vendor emission fixture and three refusal fixtures — one per
  schema-required RF input field). Negative probe verified during
  development: an emission against an `event_count: 0` pin fails with
  `ADAPTER_EVENT_COUNT_MISMATCH` (exit 1), so refusal pins are not
  vacuous.
- Strict examples: `51/51` passed (`--require-all`), including the new EO
  chain corpus at profile H.
- Policy risk-mode lint: ok. Future-branch roadmap validation: ok
  (18 candidates, 3 rejected/deferred).
- Full pytest: `483 passed, 110 subtests passed, 0 failed` (includes the
  12 new example-vendor tests, 3 new `event_count` harness tests, and
  3 new fixture-schema sync tests).
- Risk-filter presets: `6 passed`.
- Workflow end-to-end: profile H and profile M runs forwarded the expected
  chains and emitted CoT.
- Live gateway: profile H run and profile L compact-encoding run both
  exit 0 — COMMAND GOTO forwarded, duplicate command acknowledged
  `DUPLICATE_IGNORED`, STATE forwarded.
- Gateway self-tests: profile H, gateway config, and edge config all
  `self-test: ok`.
- Migration compatibility: all nine `examples/*.jsonl` corpora clean
  against `--target v1.1.13 --strict` (issues=0 failed=0 warnings=0 each).
- Packet size (Profile L, compact): min=98 avg=116.0 max=150 bytes,
  within the 240-byte limit.
- Containerized gateway (`gateway/docker-compose.yml`, Docker 29.6.1):
  started, logged matching `semantics_hash`/`contract_hash`, received and
  forwarded replayed traffic with zero violations
  (`recv=1 ... fwd=1 ... drops=0 violations=0`), compose down clean.
- Release artifacts built: `zmeta-edge-v1.1.13.zip`,
  `zmeta-gateway-v1.1.13.zip`, `zmeta-v1.1.13-dist.zip`, formal release
  package `release/package-v1.1.13` (`release package ok mode=package`,
  no-signature mode; no secrets in package paths).
- Checksums: `SHA256SUMS_v1.1.13.txt` generated and verified for all
  release assets. Detached signatures: none generated — signing remains
  reserved to the release authority's external process (checksums-only
  release, consistent with v1.1.11/v1.1.12).
- `git diff --check`: clean at release commit time.

## Environment Notes

- Windows 11, Python 3.13, Docker 29.6.1. The previously documented
  MAX_PATH-sensitive pytest failures do not occur at the canonical
  repository path (all 483 tests pass); they remain an artifact of
  long-path working copies only.
