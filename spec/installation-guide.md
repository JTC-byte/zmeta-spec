# ZMeta Installation And Packaging Guide

This guide covers repeatable local installs, deterministic gateway settings, and
device configuration packs for the current `v1.1.13` release baseline and
current `main` integration docs. It is an installation guide, not a release
publication workflow; do not create tags, signatures, GitHub releases, or
published checksum updates from these steps.

## Prerequisites

- Python 3.11+.
- Docker Desktop on Windows, or Docker Engine plus Docker Compose on Linux, if
  using the containerized edge/gateway deployment.
- Windows Docker Desktop requires virtualization and WSL2 enabled.

Install runtime dependencies from the repository root:

```text
python -m pip install -r requirements.txt
```

Install optional test and development dependencies:

```text
python -m pip install -r requirements-dev.txt
```

If you are running gateway tests directly from a release bundle, also install
the gateway-specific requirements when present:

```text
python -m pip install -r gateway/requirements.txt
```

## Gateway Install With Maintained Templates

The maintained install templates live under `configs/`:

- `configs/gateway-config.json` - Profile H gateway with validation and CoT
  emission enabled.
- `configs/gateway-config-strict.json` - strict validation preset.
- `configs/edge-config.json` - Profile L edge relay that forwards to a gateway.
- `configs/edge-config-profile-L-lean.json` - compact Profile L preset for
  constrained links.

Run the gateway with the maintained gateway template:

```text
python gateway/src/gateway.py --config configs/gateway-config.json
```

Run the edge relay template after replacing `GATEWAY_HOST` with the real
gateway IP or DNS name:

```text
python gateway/src/gateway.py --config configs/edge-config.json
```

The older example template `gateway/config/gateway-config.example.json` remains
available for code-local examples, but new deployments should start from the
maintained `configs/` templates because they include the current deployment
controls documented in `configs/README.md`.

Notes:

- `schema_path` and `policy_dir` are resolved relative to the config file.
- Keep deployment configs in version control to make behavior deterministic.
- When adopting a policy variant into the active `policy/` directory, recompute
  deployment hash gates with `python tools/compute_contract_hash.py`.
- Use `python tools/lint_policy_risk_modes.py` after policy edits to catch
  material risk checks configured to `ignore`.

## Gateway Install With Wizard Output

Use the wizard when you need a local config generated interactively:

```text
python tools/gateway_wizard.py --output gateway-config.json
python gateway/src/gateway.py --config gateway-config.json
```

The wizard writes paths suitable for a repo-root config by default. Use
`--force` only when you intend to replace an existing generated file.

Override a single setting at launch when needed:

```text
python gateway/src/gateway.py --config gateway-config.json --listen-port 6000
```

## Docker Compose Install

Containerized templates are available for edge and gateway nodes:

```text
docker compose -f deploy/edge/docker-compose.yml up
docker compose -f deploy/gateway/docker-compose.yml up
```

Both templates default to UDP port `5555`. If edge and gateway run on the same
host, change one port mapping or config value to avoid a collision. Use
`docker compose ... config` to render and inspect the effective configuration
before deployment.

## Drone And Sensor Config Packs

Mapping packs convert vendor payloads into ZMeta. To make installs repeatable,
ship packs as folders or zip files and include a manifest.

Pack layout:

```
<pack>/
  mapping.yaml
  enums.yaml
  units.yaml
  pack.json
  tests/
```

Manifest example (`pack.json`):

```
{
  "schema_id": "vendor:acme_rf:v1",
  "pack_slug": "vendor__acme_rf__v1",
  "version": "1.0.0",
  "description": "Acme RF sensor mapping pack"
}
```

Install options:
- Copy the pack folder into `adapters/mapping-packs/<pack_slug>`.
- Or run `python tools/install_mapping_pack.py --pack <path>`.
- Add `--force` only when replacing an existing installed pack intentionally.
- Add `--dest <mapping-packs-dir>` when installing into a deployment bundle
  instead of the repository default.

Pin the pack version and schema_id alongside your gateway config to ensure
deterministic interpretation of vendor telemetry.

## On-Device Processing And Profile-Constrained Export

Sensors should emit `OBSERVATION_EVENT` outputs only. If an on-drone processor performs
inference, fusion, or track/state generation, treat it as an edge analytics node
and set `node_role` accordingly (`GATEWAY` or `APEX`).

Notes:
- `OBSERVATION_EVENT` outputs do not include `confidence` by schema. Confidence
  is required for `INFERENCE_EVENT`, `FUSION_EVENT`, and `STATE_EVENT` outputs.
- If you need a quality threshold for observations, gate internally and emit only
  when the threshold is met.
- Profiles constrain what leaves the device, not the internal pipeline.
  Profile L exports `STATE_EVENT`, `SYSTEM_EVENT`, and `COMMAND_EVENT`;
  Profile M allows `OBSERVATION_EVENT`, `FUSION_EVENT`, `STATE_EVENT`,
  `SYSTEM_EVENT`, and `COMMAND_EVENT`; Profile H allows the full pipeline.
- When bandwidth is constrained, keep the internal pipeline intact, export only
  the allowed event types, and retain the raw data locally for recall.

## Deterministic Settings Checklist

Capture these in configuration or release notes:

- ZMeta profile (L/M/H)
- Ports and hosts (listen, forward, CoT)
- Policy version and schema version
- Mapping pack `schema_id` and `version`
- Node role (`EDGE`, `GATEWAY`, `APEX`, `DMZ`, or `CLOUD`) and producer IDs
- Failure mode thresholds and confidence reduction policy
- Timing quality source, sync-state reporting cadence, and `est_error_ms` policy
- Input and output encodings (`json`, `cbor`, `compact`, `proto`, or `auto`)
- Contract hash gates, if enabled
- Consumer accepted-risk filter preset or equivalent downstream label handling

## Validation Before Handoff Or Deployment

Run focused validation first:

```text
python tools/validate_release_manifest.py --manifest release/zmeta-release-manifest.yaml
python tools/validate_release_package.py --manifest release/zmeta-release-manifest.yaml --templates-only
python tools/validate_examples.py --strict --require-all
```

For governed repository changes, run the full kernel gate from `AGENTS.md` and
`docs/zmeta_change_governance.md`:

```text
python tools/validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative --precision-policy --release-manifest --release-package --bad-events --adapter-harness
python -m pytest -q
git diff --check
```

For deployment-only config changes that do not modify the upstream ZMeta
baseline, validate the active gateway config and any adopted policy variants,
then document the local hash values and risk-filter posture in deployment
notes.

## Recommended Bundle Layout

```
zmeta-package/
  gateway/
  policy/
  schema/
  adapters/
    mapping-packs/
  configs/
    gateway-config.json
    device-packs/
```

Use the same bundle layout in local installs and deployments to keep paths stable.

## Release Packages

Formal release package tooling is available for release-authority workflows and
local verification:

```text
python release/build_mvp_packages.py --version v1.1.13
python release/build_release_bundle.py --version 1.1.11
python tools/build_release_package.py --manifest release/zmeta-release-manifest.yaml --output-dir release/package-v1.1.13 --release-id zmeta-v1.1.13 --release-state formal_release --no-signatures
python tools/validate_release_package.py --manifest release/zmeta-release-manifest.yaml --package-dir release/package-v1.1.13
```

Generated bundles, package directories, and zip files are ignored local outputs
unless an explicit release publication task selects them. Detached signatures
require an approved external signing key/process.
