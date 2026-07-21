# ZMeta v1.1.15 Validation Report

Release date: 2026-07-21
Release target: `v1.1.15`

## Scope

This report covers the ZMeta v1.1.15 SAPIENT bridge release: the
`sapient-bsi-flex-335` mapping pack, the SAPIENT ingress adapter
(DetectionReport layer split with registration-derived model identity,
fusion-node external promotion with caller-owned loop status,
StatusReport/TaskAck/Error mappings, RegistrationStore units codex,
send-time `est_error_ms` widening), the SAPIENT egress adapters
(COMMAND_EVENT→Task for the three mapped task types with structural
altitude exclusion; STATE_EVENT→DetectionReport with risk/timing
self-labels and export-use refusal; SAPIENT ULID id discipline), 12 new
adapter-harness fixtures, and the additive `sapient-ingress`
producer-authority policy block. The locked v1.0 kernel's semantics are
unchanged; no event-vocabulary or schema changes.

In addition to the standard battery, this release was wire-validated
end-to-end against Dstl's official tooling: Apex-SAPIENT-Middleware
v4.2.0 (commit 0c8591a), its shipped BSI Flex 335 v2.0 generated
protobuf modules and message validator, stock strict configuration,
on Python 3.11.9 / protobuf 4.25.1 (Apex's own pins).

## Commands

```bash
python tools/build_release_manifest.py --release-id zmeta-v1.1.15 --release-name "ZMeta v1.1.15" --release-status formal_release --release-date 2026-07-21 --branch main --update-claims
python tools/validate_release_manifest.py --manifest release/zmeta-release-manifest.yaml
python tools/compute_contract_hash.py
python tools/validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative --precision-policy --release-manifest --release-package --bad-events --adapter-harness
python tools/validate_examples.py --strict --require-all
python tools/lint_policy_risk_modes.py
python tools/validate_future_roadmap.py
python tools/validate_adapter_conformance.py
python tools/validate_conformance_classes.py --claims conformance/claims/example-core-producer.yaml conformance/claims/example-reference-gateway.yaml --verify-contract-hash
python -m pytest -q
python -m pytest -q gateway/tests/test_risk_filter_cli.py
python tools/test_workflow_end_to_end.py
python tools/test_workflow_end_to_end.py --profile M --listen-port 5665 --forward-port 5666 --cot-port 5667
python tools/test_gateway_live.py --listen-port 5675 --forward-port 5676 --cot-port 5677
python tools/test_gateway_live.py --profile L --encoding compact --input-encoding compact --listen-port 5695 --forward-port 5696 --cot-port 5697
python gateway/src/gateway.py --profile H --self-test
python gateway/src/gateway.py --config configs/gateway-config.json --self-test
python gateway/src/gateway.py --config configs/edge-config.json --self-test
python tools/check_compat.py --target v1.1.15 --strict <each examples/*.jsonl>
python tools/measure_packet_size.py --file examples/zmeta-profile-L-examples.jsonl --encodings compact --max-bytes 240 --summary-only
python release/build_mvp_packages.py --version v1.1.15
python release/build_release_bundle.py --version 1.1.15
python tools/build_release_package.py --manifest release/zmeta-release-manifest.yaml --output-dir release/package-v1.1.15 --release-id zmeta-v1.1.15 --release-state formal_release --no-signatures --allow-dirty --clean-output
python tools/validate_release_package.py --manifest release/zmeta-release-manifest.yaml --package-dir release/package-v1.1.15
docker compose -f gateway/docker-compose.yml up -d --build   # then replay + logs + down
python release/sign_release_artifacts.py --version v1.1.15 --write-checksums --verify-checksums
git diff --check
```

End-to-end SAPIENT wire validation (repo untouched; harness scripts and
captured evidence retained maintainer-side):

```text
Apex-SAPIENT-Middleware v4.2.0 pb2 modules + validate_proto.py, strict config
- egress: ParseDict strict (unknown fields disallowed) + byte round-trip +
  Apex validator clean for GOTO/TRACK_TARGET/CHANGE_SENSOR_MODE Tasks and
  DetectionReport projections (incl. zmeta.risk / zmeta.timing_quality
  object_info self-labels and object_map-resolved ids); ULID report_id
  embedded timestamps decode to the event's own ts
- ingress: official-pb2-built Registration / DetectionReport / StatusReport /
  TaskAck / Error (Apex-validator clean, camelCase AND proto-field-name JSON
  spellings) -> expected ZMeta event families, all schema-valid via the
  adapter's version-aware validate(); all refusal paths refuse
- live loop: local Apex instance — Registration acknowledged
  (acceptance: true); egress DetectionReports accepted as-is, zero error
  records, zero SAPIENT Error replies
- recorded as NOT exercised: C# BSI Flex 335 v2 test harness (no .NET SDK
  on the validation host); multi-node Apex routing
```

## Results

- Release manifest validation: passed — `release manifest ok groups=19
  artifacts=70`; manifest and example claim hashes regenerated for
  `zmeta-v1.1.15` (policy bundle and adapter-conformance categories
  re-baseline with the P1-07 work).
- Full kernel conformance: `conformance ok pass=20 fail=27` with all
  flags enabled.
- Projection validation: `37` cases passed.
- Extension registry validation: `61` entries passed.
- Conformance class validation: `34` classes and `2` claims passed;
  additionally verified with `--verify-contract-hash` (both claims
  match the manifest's recorded semantic contract hash).
- Encoding-negative validation: `50` cases passed.
- Precision policy validation: `32` cases passed.
- Bad-event corpus validation: `27` cases passed.
- Adapter conformance harness: `39` cases passed (27 prior + 12 SAPIENT
  fixtures: the fusion-promotion happy path and the refusal register —
  promotion without lineage, zero-fill geo, unregistered node, missing
  envelope timestamp, null node identity, TASK_ACK without task
  correlation, model-less alert).
- Strict examples: `51/51` passed (`--require-all`).
- Policy risk-mode lint: passed. Future-branch roadmap validation:
  passed (`candidates=18`).
- Full pytest: `687 passed, 172 subtests passed`, zero failures
  (v1.1.14 baseline was 570 + 172 — the growth is the SAPIENT
  ingress/egress suites and the e2e-driven ULID discipline tests).
- Consumer risk-filter presets: `6 passed`.
- Workflow end-to-end (H and M profiles): passed — forwarded event
  chains intact, CoT output carries event-authoritative time.
- Live gateway (JSON and compact-L): passed (exit 0).
- Gateway self-tests (H profile, gateway-config, edge-config): all
  `self-test: ok`.
- Migration compatibility sweep: all `9` example corpora pass
  `check_compat --target v1.1.15 --strict` (0 failures).
- Profile L packet size: `COMPACT min=98 avg=116.0 max=150` (budget
  240) — passed.
- SAPIENT end-to-end wire validation: passed as described in Scope —
  first-pass findings (egress `report_id` UUIDv7-instead-of-ULID,
  undocumented `object_id`/`task_id` ULID caller contracts) were fixed
  and the re-validation confirmed all egress cases Apex-clean, refusals
  refusing at the adapter layer, and the live middleware loop clean.
- Bundles and package: `zmeta-v1.1.15-dist.zip`,
  `zmeta-edge-v1.1.15.zip`, `zmeta-gateway-v1.1.15.zip` built;
  `release/package-v1.1.15` built in no-signature mode and validated
  (`release package ok mode=package`); the
  `zmeta-release-package-v1.1.15.zip` asset auto-built at checksum time
  by `sign_release_artifacts.py` (never hand-assembled).
- Containerized gateway: `docker compose` build and run verified —
  container starts, listens on 5555/H, replay of the canonical corpus
  received with no violation output. The container's startup
  `policy_hash`/`contract_hash` prints differ from Windows-local prints
  (known benign CRLF materialization; the release manifest's
  canonicalized hashes are the authoritative content gates and pass
  identically in both environments).
- `git diff --check`: clean.
- Checksums: `SHA256SUMS_v1.1.15.txt` generated (LF line endings) and
  verified with full artifact coverage.

## Signing Decision

Checksums-only release: no detached signatures are attached, and the
release notes state this. Signature generation remains the maintainer's
external release-authority process.
