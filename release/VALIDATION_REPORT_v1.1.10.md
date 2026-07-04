# ZMeta v1.1.10 Validation Report

Release date: 2026-07-03
Release target: `v1.1.10`

## Scope

This report covers the ZMeta v1.1.10 fielded-safety enforcement patch:
command-altitude denylist completion to the full section 7.8 set, a recursive
whitespace/case-normalized STATE laundering check with the full section 7.7 set,
adapter calibration honesty for the Kraken and Moth reference adapters, and
alignment of the egress MAVLink command altitude guard. It confirms that
schemas, the semantic contract, the extension registry, conformance classes,
examples, adapters, the release manifest, release package tooling, and release
metadata remain aligned, and that no schema or v1.0/v1.1.0 vocabulary changed.

## Commands

```bash
python tools/build_release_manifest.py --release-id zmeta-v1.1.10 --release-name "ZMeta v1.1.10" --release-status formal_release --release-date 2026-07-03 --branch main --update-claims
python tools/validate_release_manifest.py --manifest release/zmeta-release-manifest.yaml
python tools/validate_examples.py --strict --require-all
python tools/validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative --precision-policy --release-manifest --release-package --bad-events --adapter-harness
python tools/validate_bad_events.py --must-fail conformance/bad-events/must-fail.jsonl
python tools/validate_adapter_conformance.py --fixtures conformance/adapter-harness/must-pass.jsonl
python -m pytest -q
python gateway/src/gateway.py --profile H --self-test
python gateway/src/gateway.py --config configs/gateway-config.json --self-test
python gateway/src/gateway.py --config configs/edge-config.json --self-test
python tools/check_compat.py --target v1.1.10 --strict <each examples/*.jsonl>
python release/build_mvp_packages.py --version v1.1.10
python release/build_release_bundle.py --version 1.1.10
python tools/build_release_package.py --manifest release/zmeta-release-manifest.yaml --output-dir release/package-v1.1.10 --release-id zmeta-v1.1.10 --release-state formal_release --no-signatures --allow-dirty --clean-output
python tools/validate_release_package.py --manifest release/zmeta-release-manifest.yaml --package-dir release/package-v1.1.10
python release/sign_release_artifacts.py --version v1.1.10 --write-checksums --verify-checksums
git diff --check
```

## Results

- Release manifest validation: passed (`--release-manifest` in the full gate).
- Release package template and package validation: passed
  (`--release-package` in the full gate; `--package-dir` validated separately).
- Strict examples validation: `40 passed, 0 failed, 0 warnings`.
- Full kernel conformance: `conformance ok` with projection, registry,
  conformance class, encoding-negative, precision-policy, release-manifest,
  release-package, bad-event, and adapter-harness checks enabled.
- Projection validation: `37` cases passed.
- Extension registry validation: `57` entries passed.
- Conformance class validation: `34` classes and `2` claims passed.
- Encoding-negative validation: `50` cases passed.
- Precision policy validation: `32` cases passed.
- Bad-event corpus validation: `21` cases passed (11 added this release for
  deep-nested STATE laundering across every section 7.7 category, whitespace and
  case-padded evasion, and command altitude nested in `extensions`).
- Adapter conformance harness: `10` cases passed.
- Full pytest: `444 passed, 110 subtests passed` (adds two direct
  `validate_semantics` unit tests for the new STATE `{field, path}` detail).
- Gateway Profile H, gateway config, and edge config self-tests: passed.
- Compatibility checks: all seven example JSONL streams passed with
  `--target v1.1.10 --strict`.
- Adversarial enforcement verification: 100+ empirical bypass attempts against
  the real schema, semantic validator, and egress guard. Zero exact-name STATE
  or command-altitude bypasses; the recursion, list traversal, case-folding, and
  whitespace normalization held. The only residual is arbitrarily *renamed* raw
  content or altitude in free-form objects (for example `z_m`), the inherent
  limit of a name denylist, documented in the release notes.
- Release artifacts built:
  - `zmeta-v1.1.10-dist.zip`
  - `zmeta-edge-v1.1.10.zip`
  - `zmeta-gateway-v1.1.10.zip`
  - `zmeta-release-package-v1.1.10.zip`
- Release package output validation: passed.
- Checksum generation and verification: `checksums ok: SHA256SUMS_v1.1.10.txt`.
- `git diff --check`: passed with normal Windows LF-to-CRLF working-copy
  warnings only.

## Validation Scope Notes

- The change is confined to the semantic validator, policy denylists, two
  ingress reference adapters, and one egress adapter guard. It does not touch
  transport, encoding round-trips, or the runtime gateway data path.
- Transport/runtime plumbing (UDP live-gateway, workflow end-to-end, Docker
  Compose rendering, packet-size, and risk-filter checks) was not re-exercised
  in this session because it is orthogonal to the semantic-enforcement change and
  was unchanged since v1.1.9. Encoding round-trips are covered by the gateway
  self-tests and strict examples above.

## Semantic Boundary Checks

- No v1.1.0 or future vocabulary became valid under `zmeta_version: "1.0"`.
- The locked v1.0 schema and the semantic contract text are unchanged; policy
  and reference enforcement were tightened to match the already-normative
  sections 7.7 and 7.8.
- Tightened enforcement rejects only events that were always contract-violating
  (altitude on a COMMAND_EVENT; raw sensor content in a STATE projection).
- Adapter calibration output is honest: Kraken/Moth default to `UNCALIBRATED`
  and assert `CALIBRATED`/`DEGRADED` only when a deployment substantiates it.
- D-003 remains open as roadmap-planned future versioned semantic branches.

## Secret And Signature Safety

- No private key, token, credential, certificate private material, or signing
  secret was committed.
- The release package is generated in no-signature mode. No local signing key
  was present in the build environment.
- Detached signatures were not generated for this release; it is published
  checksums-only, consistent with v1.1.5 through v1.1.9.

## Remaining Open Work

- Release-authority detached signatures remain future work until a
  maintainer-controlled signing key/process is established.
- D-003 remains open as roadmap-planned future versioned semantic branches.
- Broader native sensor-adapter certification remains future harness breadth.
- Closed payload schemas plus producer conformance remain the future mitigation
  for the arbitrarily-renamed-field denylist residual.
