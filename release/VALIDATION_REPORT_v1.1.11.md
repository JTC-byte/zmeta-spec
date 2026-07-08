# ZMeta v1.1.11 Validation Report

Release date: 2026-07-07
Release target: `v1.1.11`

## Scope

This report covers the ZMeta v1.1.11 field-driven adoption-guidance patch:
three advisory docs (MQTT transport binding guidance, deployment concept
crosswalk, correlation pattern), four extension-registry governance entries
(CORRELATION_HINT proposed, DATA_REF_MEDIA_METADATA proposed,
AGGREGATE_STATE_SNAPSHOT reserved, PAYLOAD_SCHEMA_URI rejected), a new
seven-event correlation example corpus, two new bad-event anti-laundering
fixtures, and post-publication release-baseline alignment. It confirms that
schemas, the semantic contract, the extension registry, conformance classes,
examples, adapters, the release manifest, release package tooling, and release
metadata remain aligned, and that no schema, policy behavior, or v1.0/v1.1.0
vocabulary changed.

## Commands

```bash
python tools/build_release_manifest.py --output release/zmeta-release-manifest.yaml --release-id zmeta-v1.1.11 --release-name "ZMeta v1.1.11" --release-status formal_release --release-date 2026-07-07 --update-claims
python tools/validate_release_manifest.py --manifest release/zmeta-release-manifest.yaml
python tools/validate_extension_registry.py
python tools/validate_examples.py --strict --require-all
python tools/validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative --precision-policy --release-manifest --release-package --bad-events --adapter-harness
python tools/validate_bad_events.py --must-fail conformance/bad-events/must-fail.jsonl
python -m pytest -q
python gateway/src/gateway.py --profile H --self-test
python gateway/src/gateway.py --config configs/gateway-config.json --self-test
python gateway/src/gateway.py --config configs/edge-config.json --self-test
python tools/check_compat.py --target v1.1.11 --strict <each examples/*.jsonl>
python release/build_mvp_packages.py --version v1.1.11
python release/build_release_bundle.py --version 1.1.11
python tools/build_release_package.py --manifest release/zmeta-release-manifest.yaml --output-dir release/package-v1.1.11 --release-id zmeta-v1.1.11 --release-state formal_release --no-signatures --allow-dirty --clean-output
python tools/validate_release_package.py --manifest release/zmeta-release-manifest.yaml --package-dir release/package-v1.1.11
python release/sign_release_artifacts.py --version v1.1.11 --write-checksums --verify-checksums
git diff --check
```

## Results

- Release manifest validation: passed (`--release-manifest` in the full
  gate); manifest and example claim hashes regenerated for `zmeta-v1.1.11`.
- Release package template and package validation: passed
  (`--release-package` in the full gate; `--package-dir` validated
  separately: `release package ok mode=package`).
- Strict examples validation: `47 passed, 0 failed, 0 warnings` across eight
  corpora, including the new
  `examples/zmeta-correlation-pattern-examples.jsonl` (7 events, Profile H).
- Full kernel conformance: `conformance ok` with projection, registry,
  conformance class, encoding-negative, precision-policy, release-manifest,
  release-package, bad-event, and adapter-harness checks enabled.
- Projection validation: `37` cases passed.
- Extension registry validation: `61` entries passed (4 added this release;
  reserved/proposed/rejected entries confirmed invalid under locked v1.0 and
  v1.1.0).
- Conformance class validation: `34` classes and `2` claims passed.
- Encoding-negative validation: `50` cases passed.
- Precision policy validation: `32` cases passed.
- Bad-event corpus validation: `23` cases passed (2 added this release
  proving `payload.extensions.correlation_hint` cannot carry `confidence` or
  `track_id` on an observation at any nesting depth; both fail with
  `OBSERVATION_HAS_IDENTITY` as expected).
- Adapter conformance harness: `10` cases passed.
- Full pytest: `444 passed, 110 subtests passed` (release-manifest identity
  pins updated to `zmeta-v1.1.11` / `2026-07-07`; compatibility CLI test
  updated to the `v1.1.11` target).
- Gateway Profile H, gateway config, and edge config self-tests: passed.
- Compatibility checks: all eight example JSONL streams passed with
  `--target v1.1.11 --strict`.
- Release artifacts built:
  - `zmeta-v1.1.11-dist.zip`
  - `zmeta-edge-v1.1.11.zip`
  - `zmeta-gateway-v1.1.11.zip`
  - `zmeta-release-package-v1.1.11.zip`
- Release package output validation: passed.
- Checksum generation and verification: `checksums ok: SHA256SUMS_v1.1.11.txt`.
- `git diff --check`: passed with normal Windows LF-to-CRLF working-copy
  warnings only.

## Validation Scope Notes

- The change is confined to advisory documentation, extension-registry
  records, example/conformance corpora, current-facing version references,
  and release metadata. It does not touch the semantic validator, policy
  denylist behavior, schemas, adapters, encodings, or the runtime gateway
  data path.
- Transport/runtime plumbing (UDP live-gateway, workflow end-to-end, Docker
  Compose rendering, packet-size, and risk-filter checks) was not
  re-exercised in this session because it is orthogonal to this
  docs/registry/fixture change and is unchanged since v1.1.10. Encoding
  round-trips are covered by the gateway self-tests and strict examples
  above.
- Upstream PR #4 was validated in an isolated worktree before this release
  was scoped: its proposed v1.2.0 dispatcher arm breaks `oneOf` dispatch for
  all v1.1.0 events and accepts command-altitude, STATE-laundering,
  observation-confidence, non-UUIDv7, and non-UTC-Z events under a `"1.2.0"`
  label. Those results are documented in the review posted on the PR and are
  the basis for the not-merged disposition.

## Semantic Boundary Checks

- No v1.1.0 or future vocabulary became valid under `zmeta_version: "1.0"`,
  and no new vocabulary became valid under `"1.1.0"`.
- The locked v1.0 schema, the v1.1.0 schema, the semantic contract text, and
  all policy YAML behavior are unchanged.
- Registry entries added this release are governance records only:
  proposed/reserved entries remain non-claimable, and the rejected
  `PAYLOAD_SCHEMA_URI` entry records the rejection rationale.
- The correlation pattern uses only locked vocabulary; the two new bad-event
  fixtures tighten nothing — they pin already-enforced recursive denylist
  behavior against the new documented extension shape.
- D-003 remains open as roadmap-planned future versioned semantic branches.

## Secret And Signature Safety

- No private key, token, credential, certificate private material, or signing
  secret was committed.
- The release package is generated in no-signature mode. No local signing key
  was present in the build environment.
- Detached signatures were not generated for this release; it is published
  checksums-only, consistent with v1.1.5 through v1.1.10.

## Remaining Open Work

- Release-authority detached signatures remain future work until a
  maintainer-controlled signing key/process is established.
- D-003 remains open as roadmap-planned future versioned semantic branches,
  now informed by the PR #4 field requirements (data_ref media enrichment,
  aggregate snapshot containers, first-class correlation identity if the
  extension pattern proves insufficient).
- Broader native sensor-adapter certification remains future harness breadth.
- Closed payload schemas plus producer conformance remain the future
  mitigation for the arbitrarily-renamed-field denylist residual.
