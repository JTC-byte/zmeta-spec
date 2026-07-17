# ZMeta v1.1.14 Validation Report

Release date: 2026-07-17
Release target: `v1.1.14`

## Scope

This report covers the ZMeta v1.1.14 audit-driven honesty hardening
patch: the R1-10 full stack audit and its fix-every-finding pass — the
reference-adapter honesty fixes (refusal/omission instead of invented
values, contract 6.8 geo all-or-nothing, documented receiver-bandwidth
sentinel, CoT egress honest display defaults), the machine-encoded
honesty invariants (quality frame provenance, INFERENCE fused-state
denylist completion, zero-fill warn diagnostic, protected risk-label
strip paths, harness refusal register and surplus-expectation guard),
the falsifiable checking machinery (empty-input floors, checksum
coverage, manifest-derived defaults, release-currency test), the
Class B contract wording clarifications (sections 2.1 and 5.7), the
four governed diagnostic `reason_code` additions to both schemas, and
the post-fix verification audit that re-ran every original audit probe
against the fixed tree. The locked v1.0 kernel's semantics are
unchanged; no event vocabulary changes.

## Commands

```bash
python tools/build_release_manifest.py --release-id zmeta-v1.1.14 --release-name "ZMeta v1.1.14" --release-status formal_release --release-date 2026-07-17 --update-claims
python tools/validate_release_manifest.py --manifest release/zmeta-release-manifest.yaml
python tools/compute_contract_hash.py
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
python tools/check_compat.py --target v1.1.14 --strict <each examples/*.jsonl>
python tools/measure_packet_size.py --file examples/zmeta-profile-L-examples.jsonl --encodings compact --max-bytes 240 --summary-only
python release/build_mvp_packages.py --version v1.1.14
python release/build_release_bundle.py --version 1.1.14
python tools/build_release_package.py --manifest release/zmeta-release-manifest.yaml --output-dir release/package-v1.1.14 --release-id zmeta-v1.1.14 --release-state formal_release --no-signatures --allow-dirty --clean-output
python tools/validate_release_package.py --manifest release/zmeta-release-manifest.yaml --package-dir release/package-v1.1.14
docker compose -f gateway/docker-compose.yml up -d   # then replay + logs + down
python release/sign_release_artifacts.py --write-checksums --verify-checksums
git diff --check
```

## Results

- Release manifest validation: passed — `release manifest ok groups=19
  artifacts=70`; manifest and example claim hashes regenerated for
  `zmeta-v1.1.14` (the semantic contract, both schema files, the policy
  bundle, and both conformance corpora re-baseline with the fix-pass
  work).
- Full kernel conformance: `conformance ok pass=20 fail=27` with all
  flags enabled.
- Projection validation: `37` cases passed.
- Extension registry validation: `61` entries passed.
- Conformance class validation: `34` classes and `2` claims passed;
  additionally verified with `--verify-contract-hash` (both claims
  match the manifest's recorded semantic contract hash).
- Encoding-negative validation: `50` cases passed.
- Precision policy validation: `32` cases passed.
- Bad-event corpus validation: `27` cases passed (23 prior + nested
  INFERENCE fused-state x2 and quality bearing-frame x2).
- Adapter conformance harness: `27` cases passed (15 prior + 12 fix-pass
  fixtures: refusal pins for null identity, absent/null confidence, and
  missing JSON-replay RF measurements, plus omission pins for
  geo-all-or-nothing and never-invented error bounds). Refusal pins
  verified non-vacuous during the pass: restoring a refused field makes
  the harness fail that fixture with `ADAPTER_EVENT_COUNT_MISMATCH`.
- Strict examples: `51/51` passed (`--require-all`).
- Policy risk-mode lint: passed. Future-branch roadmap validation:
  passed (`candidates=18`).
- Full pytest: `570 passed, 172 subtests passed`, zero failures
  (v1.1.13 baseline was 485 + 110 — the growth is the fix pass's new
  refusal/floor/currency/inverse-coverage/strip-guard/zero-fill test
  families).
- Consumer risk-filter presets: `6 passed`.
- Workflow end-to-end (H and M profiles): passed — forwarded event
  chains intact, CoT output carries event-authoritative time (the new
  honest default) and confidence in remarks.
- Live gateway (JSON and compact-L): passed.
- Gateway self-tests (H profile, gateway-config, edge-config): all
  `self-test: ok`.
- Migration compatibility sweep: all `9` example corpora pass
  `check_compat --target v1.1.14 --strict` (0 failures).
- Profile L packet size: `COMPACT min=98 avg=116.0 max=150` (budget
  240) — passed.
- Bundles and package: `zmeta-v1.1.14-dist.zip`,
  `zmeta-edge-v1.1.14.zip`, `zmeta-gateway-v1.1.14.zip` built;
  `release/package-v1.1.14` built in no-signature mode and validated
  (`release package ok mode=package`); the
  `zmeta-release-package-v1.1.14.zip` asset auto-built at checksum time
  by `sign_release_artifacts.py` (never hand-assembled).
- Containerized gateway: `docker compose` build and run verified —
  container starts, listens on 5555/H, replay of the canonical corpus
  received with no violation output. Note: the container's startup
  `policy_hash`/`contract_hash` prints differ from Windows-local prints
  because the Windows working copy materializes some files CRLF and the
  informational startup hash reads bytes as-is; the release manifest's
  canonicalized (CRLF-to-LF) hashes are the authoritative content
  gates and pass identically in both environments.
- `git diff --check`: clean.
- Checksums: `SHA256SUMS_v1.1.14.txt` generated (LF line endings) and
  verified with full artifact coverage.

## Signing Decision

Checksums-only release: no detached signatures are attached, and the
release notes state this. Signature generation remains the maintainer's
external release-authority process.
