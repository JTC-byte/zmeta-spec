# ZMeta Specification (v1.0 Locked, current release v1.1.5)

## Overview
- ZMeta is a transport-agnostic, event-based metadata standard for resilient ISR.
- Designed to survive degraded and denied environments.
- Separates observation, inference, fusion, state, and command semantics.

## Current Release

- Current release: `v1.1.5`
- Release notes and assets: <https://github.com/JTC-byte/zmeta-spec/releases/tag/v1.1.5>
- Release focus: hardened semantic baseline, release/hash governance, conformance expansion,
  formal release package tooling, and strict preservation of version-dispatched validation.
- Normative contract: v1.0 locked semantic contract, canonical version-discriminated
  JSON schema, v1.0 JSON schema, and policy pack.
- Experimental extension: `schema/zmeta-event-1.1.0.schema.json` is provided for proposed
  compatibility testing only; v1.1.0-only fields are not part of the locked v1.0 contract.

## What ZMeta Is
- A semantic contract
- A JSON schema
- A policy-driven enforcement model
- A reference gateway and adapters

## What ZMeta Is Not
- Not a transport
- Not a C2 system
- Not a video container
- Not a replacement for MISB

## Design Goals
- Honesty under uncertainty
- Graceful degradation
- Operator trust
- Interoperability across vendors and transports

## Start Here
- New to ZMeta: read `spec/installation-guide.md` for a full step-by-step install.
- Developer walkthrough: read `spec/quickstart.md` for runnable examples.
- Contract and semantics: read `spec/semantics-contract.md`.
- Profile compatibility matrix: read `spec/profile-compatibility.md`.
- Field dictionary for UIs: read `spec/field-dictionary.md`.
- Encoding guidance: read `spec/compact-binary-mapping.md` and `spec/protobuf-encoding.md`.

## Repository Structure
- `spec/` Core specification and normative text.
- `schema/` JSON schema definitions for ZMeta artifacts.
- `examples/` Sample payloads and usage patterns.
- `conformance/` Must-pass/must-fail regression corpus.
- `policy/` Policy language and enforcement guidance.
- `gateway/` Reference gateway implementation and tests.
- `adapters/` Ingress and egress adapter patterns and templates.
- `tools/` Utilities for validation and development workflows.

## Adapters

Reference adapters show how to translate between ZMeta and external systems.
See `adapters/README.md` for ingress templates, mapping packs, and egress projections.

Adapter semantic mapping:
- Native sensor measurements map to `OBSERVATION_EVENT`.
- Classifier or detector output maps to `INFERENCE_EVENT`.
- Track association and identity creation map to `FUSION_EVENT`.
- Operator display projection maps to `STATE_EVENT`.
- Mission tasking maps to `COMMAND_EVENT` only through deconfliction.
- Health, timing, link, validation, and task acknowledgement reports map to `SYSTEM_EVENT`.

ZMeta is strict about semantic invariants and flexible through ignorable,
namespaced, non-semantic extensions. Extensions must not redefine core event
meaning, authority boundaries, units, lineage, profile behavior, or command
safety.

## Schemas and Examples

Use `schema/zmeta-event.schema.json` as the canonical validation entry point.
It dispatches by `zmeta_version` and prevents v1.1.0 vocabulary from validating
under a v1.0 event. Version-specific wrappers are retained for integrations that
need a fixed target:
- `schema/zmeta-event-1.0.schema.json`
- `schema/zmeta-event-1.1.0.schema.json`

Runnable examples live in `examples/`:
- `zmeta-examples-1.0.jsonl`: RF observation, inference, fusion, and state projection.
- `zmeta-profile-L-examples.jsonl`: Profile L state/system/command examples.
- `zmeta-command-examples.jsonl`: GOTO and TASK_ACK lifecycle.
- `zmeta-v1.1-examples.jsonl`: SENSOR_STATUS, PLATFORM_STATUS, data_ref/data_refs,
  error_ellipse_m, and v1.1.0 tasking examples.

Intentionally invalid examples live in `conformance/must-fail.jsonl`; valid
regression fixtures live in `conformance/must-pass.jsonl`.

## Tools

Quick helpers for local validation and UDP replay:

```
python tools/run_gateway.py --profile H
python tools/udp_receiver.py
python tools/udp_sender.py --file examples/zmeta-command-examples.jsonl
python tools/replay.py --file examples/zmeta-command-examples.jsonl --delay-ms 200
python tools/check_compat.py legacy-events.jsonl --target v1.1.5
python tools/validate.py --file examples/zmeta-command-examples.jsonl --profile H
python tools/validate_conformance.py --strict
python tools/validate_release_manifest.py --manifest release/zmeta-release-manifest.yaml
python tools/validate_release_package.py --manifest release/zmeta-release-manifest.yaml --templates-only
python tools/compute_contract_hash.py
python tools/test_gateway_live.py
python tools/test_workflow_end_to_end.py
```

End-to-end workflow variants:
```
python tools/test_workflow_end_to_end.py --profile M
python tools/test_workflow_end_to_end.py --profile L
python tools/test_workflow_end_to_end.py --profile M --expect COMMAND_EVENT,SYSTEM_EVENT
```

`tools/test_gateway_live.py` exercises live UDP forwarding, COMMAND dedupe, and CoT emission.

Makefile targets run the same commands with `python` directly; ensure dependencies are installed
(`python -m pip install -r gateway/requirements.txt -r requirements-dev.txt`).

## Versioning
- v1.0.x = clarifications and fixes
- v1.1+ = proposed backward-compatible extensions until explicitly locked
- v2.0 = breaking changes

See `spec/versioning.md` for the full policy.

## Quickstart

Prereqs: Python 3.11+ and Docker.

Install runtime dependencies:
```
python -m pip install -r requirements.txt
```

Optional (tests/dev tools):
```
python -m pip install -r requirements-dev.txt
```

Windows Docker note: Docker Desktop requires virtualization + WSL2 enabled. If Docker is not available, run the gateway directly with Python.

See `spec/quickstart.md` for a runnable gateway + UDP replay walkthrough.

## Installation and Packaging

See `spec/installation-guide.md` for a deterministic install guide, gateway wizard,
and mapping pack installs for drone and sensor configs.

Timing quality metadata (`time_source`, `sync_state`, `est_error_ms`,
`last_sync_ts`) is required by the semantic contract for operational events.
Gateway `event.t_receive` / `event.t_publish` stamps are separate latency and
AAR fields added by the reference gateway when configured.
Adapter fallback timing (`UNKNOWN` / `UNSYNCED`) is intentionally degraded and
should be replaced by source-provided GPS/NTP/PTP timing or periodic
`TIME_STATUS` as soon as a deployment can expose it.

Deployment helpers:
- Config templates: `configs/edge-config.json`, `configs/gateway-config.json`
- Docker Compose: `deploy/edge/docker-compose.yml`, `deploy/gateway/docker-compose.yml`
- Bundle builders:
    - `python release/build_mvp_packages.py --version v1.1.5` produces `zmeta-edge-v1.1.5.zip` and `zmeta-gateway-v1.1.5.zip`
    - `python release/build_release_bundle.py --version 1.1.5` produces `zmeta-v1.1.5-dist.zip`
    - `python tools/build_release_package.py --manifest release/zmeta-release-manifest.yaml --output-dir release/package-v1.1.5 --release-id zmeta-v1.1.5 --release-state formal_release --no-signatures` builds formal package metadata without creating signatures.
    - `python release/sign_release_artifacts.py --version v1.1.5 --write-checksums --sign --target all` signs release assets with detached PGP signatures when an approved signing key is available.

## Deployment Checklist (Compact)

Use this to lock down schema, policy, and semantic-contract drift and verify a clean deployment:

1. Compute schema, policy, semantic-contract, and combined contract hashes: `python tools/compute_contract_hash.py`
1. Set `require_contract_hash` (and optionally `require_schema_hash`/`require_policy_hash`) in config.
1. If adopting a policy variant into the active `policy/` directory, recompute and update the deployment hash gates.
1. Validate the governed release baseline: `python tools/validate_release_manifest.py --manifest release/zmeta-release-manifest.yaml`
1. Validate formal release package templates or generated package output before distribution.
1. Run self-test: `python tools/run_gateway.py --profile H --self-test`
1. Run conformance: `python tools/validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative --precision-policy --release-manifest --release-package --bad-events --adapter-harness`
1. Verify consumer risk posture where needed: `python tools/filter_risk.py --input gateway-output.jsonl --preset command --fail-on-drop`
1. Start gateway with strict mode (optional): `python tools/run_gateway.py --config configs/gateway-config.json --strict-validation`
1. Verify metrics and drops in logs (enable `metrics_log_path` if needed).

## Normative vs Reference

Normative (contract): `spec/semantics-contract.md`, `schema/zmeta-event.schema.json`, `schema/zmeta-event-1.0.schema.json`, `policy/*.yaml`, `spec/versioning.md`
Reference: `gateway/*`, `tools/*`, `adapters/*`, `examples/*`

Normative files define compliance. Reference components exist to accelerate adoption.
