# ZMeta Installation and Packaging Guide

This guide focuses on repeatable installs with deterministic settings for gateways
and device configuration packs (drones, sensors, and payloads). It is written so a
new reader can install and run ZMeta without prior context.

If you only want a fast developer walkthrough, start with `spec/quickstart.md`.
This document is the detailed, step-by-step install and deployment reference.

## What you are installing

ZMeta is a semantic contract, schema, and policy set. The repository includes:
- A normative contract and JSON schema that define meaning and structure (`spec/`, `schema/`).
- Policy rules that lock down semantics and producer rights (`policy/`).
- A reference gateway that validates and routes events (`gateway/`).
- Example events and tools for testing and verification (`examples/`, `tools/`).
- Config templates and deployment helpers for repeatable installs (`configs/`, `deploy/`).

The reference gateway is the installable runtime component used in the MVP.
It represents the comms/deconfliction module on both edge and gateway nodes.

## Prerequisites

Required:
- Windows or Linux (Ubuntu).
- Python 3.11+ (3.13 recommended).
- Network access to UDP ports used by your edge and gateway.

Docker deployment requires:
- Docker Desktop (Windows) or Docker Engine (Linux).
- Virtualization enabled in BIOS/UEFI on Windows.
- WSL2 enabled on Windows.

## Standard install paths

Linux (Ubuntu):
- `/opt/zmeta/` (bundle root)
- `/opt/zmeta/configs/edge-config.json`
- `/opt/zmeta/configs/gateway-config.json`

Windows:
- `C:\ProgramData\ZMeta\` (bundle root)
- `C:\ProgramData\ZMeta\configs\edge-config.json`
- `C:\ProgramData\ZMeta\configs\gateway-config.json`

## Why the stack is locked down

ZMeta is valuable only if every producer and consumer interprets events the same
way. The schema and policy files are intentionally strict so vendors cannot drift
the semantics. Profiles (L/M/H) reduce bandwidth without skipping the semantic
pipeline, and producer allowlists prevent unauthorized event types.

This gives you adaptability without fragmentation: vendors can swap in and out as
long as they emit compliant ZMeta events and obey the policy.

## MVP deployment model (Orin + edge gateway)

Roles (MVP vendors):
- `swarmint`: drone + EO/IR payload platform only (no ZMeta producer role).
- `sensorops`: comms + edge compute module (edge export + gateway command emission).
- `torch`: gateway analytics (fusion + retasking).

Operational flow (MVP):
- Drone payloads collect data and feed the Orin.
- Orin performs local semantic processing and emits ZMeta events (Profile L export = STATE_EVENT only).
- `sensorops` on the drone broadcasts ZMeta offboard to the gateway.
- Gateway validates and projects to downstream formats (e.g., CoT/TAK).
- `torch` fuses multi-drone tracks and generates retasking recommendations.
- `sensorops` on the gateway converts retasking into ZMeta COMMAND_EVENTs.
- Edge `sensorops` receives COMMAND_EVENTs, deconflicts, and hands off to
  Swarm/ArduPilot autonomy for execution.

These producer IDs are MVP-specific. Later vendors can fill the same roles by updating
`policy/routing.yaml` allowlists.

## Step-by-step installation (MVP bundle)

This is the recommended path for real deployments. It uses the packaged bundles
so file paths and configs are stable across systems.

1) Obtain the bundle.

If you received a zip, use it directly. If you are building from source:

```
python release/build_mvp_packages.py
```

This creates:
- `release/zmeta-edge-mvp.zip`
- `release/zmeta-gateway-mvp.zip`

2) Choose an install directory.

Use a deterministic location to avoid path drift:
- Linux: `/opt/zmeta/`
- Windows: `C:\ProgramData\ZMeta\`

3) Unzip the bundle into that directory.

Example (Windows, PowerShell):
```
Expand-Archive -Path zmeta-edge-mvp.zip -DestinationPath C:\ProgramData\ZMeta\edge
Expand-Archive -Path zmeta-gateway-mvp.zip -DestinationPath C:\ProgramData\ZMeta\gateway
```

Example (Linux):
```
sudo mkdir -p /opt/zmeta
sudo unzip zmeta-edge-mvp.zip -d /opt/zmeta/edge
sudo unzip zmeta-gateway-mvp.zip -d /opt/zmeta/gateway
```

4) Edit the edge config (`configs/edge-config.json`).

At minimum:
- Set `forward_host` to the gateway IP or hostname.
- Confirm `profile` is `L` for edge export.
- Confirm `schema_path` and `policy_dir` point to bundle paths.

5) Edit the gateway config (`configs/gateway-config.json`).

At minimum:
- Set `profile` to `H` or `M` based on bandwidth.
- Set `listen_host` and `listen_port` for UDP ingest.
- Set `cot_host` and `cot_port` if emitting CoT.
- Confirm `schema_path` and `policy_dir` point to bundle paths.

6) Ensure UDP traffic can flow.

Open the UDP ports used by your edge and gateway on firewalls and security groups.
By default, the edge forwards to UDP `5555` on the gateway.

7) Start the edge service.

Docker (recommended):
```
docker compose -f deploy/edge/docker-compose.yml up
```

Direct Python:
```
python gateway/src/gateway.py --config configs/edge-config.json
```

8) Start the gateway service.

Docker (recommended):
```
docker compose -f deploy/gateway/docker-compose.yml up
```

Direct Python:
```
python gateway/src/gateway.py --config configs/gateway-config.json
```

9) Validate that traffic is flowing.

Run the end-to-end workflow test from the bundle root:
```
python tools/test_workflow_end_to_end.py --profile H
```

Success indicators:
- Gateway logs show it is listening on UDP.
- `Forwarded event types` include the expected profile event set.
- CoT output is emitted when `cot_host` is configured.

## Configuration reference (edge + gateway)

The configs in `configs/` are the single source of truth for runtime behavior.
Keep them in version control so installs are deterministic.

Key fields:
- `profile`: `L`, `M`, or `H`. Controls what event types may leave the node.
- `listen.host` and `listen.port`: UDP address the gateway listens on.
- `forward.host` and `forward.port`: UDP target for validated events.
- `emit_cot`: set to `true` to emit CoT; `false` for edge-only relay.
- `cot.host` and `cot.port`: CoT destination when `emit_cot` is `true`.
- `schema_path`: path to `schema/zmeta-event-1.0.schema.json`.
- `policy_dir`: path to the `policy/` directory.

Do not change `schema_path` or `policy_dir` to unvetted copies. These are the
contract and enforcement boundary for the MVP.

## Verification checklist

Use this after any install or config change:
- Edge gateway starts and binds to UDP `listen.port`.
- Gateway starts and binds to UDP `listen.port`.
- Edge can reach the gateway `forward.host` over UDP.
- Profile enforcement matches the configured profile.
- CoT output is produced only when `emit_cot` is enabled.

## Troubleshooting

Common issues and fixes:
- Docker engine not running. Start Docker Desktop and re-run `docker compose`.
- Virtualization not enabled (Windows). Enable in BIOS/UEFI and ensure WSL2 is installed.
- UDP blocked by firewall. Allow the configured ports between edge and gateway.
- Port collision when running edge and gateway on the same host. Change one UDP port mapping.

## Gateway install (wizard + config)

1) Generate a config:

```
python tools/gateway_wizard.py --output gateway-config.json
```

2) Run the gateway with the config:

```
python gateway/src/gateway.py --config gateway-config.json
```

Example template: `gateway/config/gateway-config.example.json`.

3) (Optional) Override a single setting with CLI flags:

```
python gateway/src/gateway.py --config gateway-config.json --listen-port 6000
```

Notes:
- `schema_path` and `policy_dir` in the config are resolved relative to the config file.
- Keep the config in version control to make behavior deterministic.

## Docker installs (recommended for MVP)

Edge (Profile L relay):
```
docker compose -f deploy/edge/docker-compose.yml up
```

Gateway (Profile H/M + CoT):
```
docker compose -f deploy/gateway/docker-compose.yml up
```

Edit `configs/edge-config.json` and `configs/gateway-config.json` before running.
Replace `GATEWAY_HOST` with the actual gateway IP/hostname for edge installs.

If you run edge and gateway on the same host, change one of the UDP port mappings
to avoid collisions. Both default to UDP `5555`.

## Edge install (direct Python)

```
python gateway/src/gateway.py --config configs/edge-config.json
```

This runs the reference comms/validation module in Profile L. The on-device
semantic pipeline (vendor-specific) publishes STATE_EVENTs to this module for
forwarding to the gateway.

## Drone and sensor config packs (mapping packs)

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

Pin the pack version and schema_id alongside your gateway config to ensure
deterministic interpretation of vendor telemetry.

## On-device processing and profile-constrained export

Sensors should emit OBSERVATION events only. If an on-drone processor performs
inference, fusion, or track/state generation, treat it as a gateway-tier analytics
node and set `node_role` accordingly (typically `GATEWAY`). `EDGE` is reserved for
raw sensor emitters; analytics/fusion producers should use a non-EDGE role.

Notes:
- OBSERVATION events do not include `confidence` by schema. Confidence is required
  for INFERENCE/FUSION/STATE events.
- Use `ObservationPayload.quality` to report observation measurement quality
  (e.g., SNR, error bounds, timing quality, calibration state).
- If you need a quality threshold for observations, gate internally and emit only
  when the threshold is met.
- Retain raw sensor data locally when possible. ZMeta snapshots are lightweight
  summaries; local storage enables AAR and deeper analysis, and lineage may
  reference non-exported events under Profile L.
- If you need to link snapshots to raw data or vectorized artifacts, use the
  optional `payload.data_ref(s)` convention in `spec/semantics-contract.md`.
- Profiles constrain what leaves the device, not the internal pipeline.
  Profile L exports STATE/SYSTEM/COMMAND only; Profile M allows STATE/FUSION/SYSTEM with
  selective OBSERVATION and COMMAND; Profile H allows the full pipeline.
- When bandwidth is constrained, keep the internal pipeline intact, export only
  the allowed event types, and retain the raw data locally for recall.

## Comms / deconfliction node (gateway + drone)

Keep command authority separated from analytics. Torch (or other analytics) emits
recommendations/inference; a dedicated Comms/Deconfliction node emits COMMAND_EVENT.
This preserves the semantic contract and keeps command governance centralized.
It also makes the analytics layer plug-and-play without expanding the command
surface area.

Recommended pattern (MVP/demo):
- Gateway host runs separate logical producers.
- `producer = torch` handles analytics and emits INFERENCE_EVENT, FUSION_EVENT, and STATE_EVENT.
- `producer = sensorops` handles comms/deconfliction and emits COMMAND_EVENT plus forwarding.
- Drone/edge host runs a local semantics pipeline and exports via comms.
- `producer = sensorops` emits event types allowed by the active profile.
- Drone host runs a comms module that receives COMMAND_EVENT and translates to
  MAVLink/Swarm API.

Example producer IDs (config snippet):
```
{
  "analytics_fusion": { "producer": "torch", "node_role": "GATEWAY" },
  "comms": { "producer": "sensorops", "node_role": "GATEWAY" }
}
```

## Deterministic settings checklist

Capture these in configuration or release notes:
- ZMeta profile (L/M/H)
- Ports and hosts (listen, forward, CoT)
- Policy version and schema version
- Mapping pack `schema_id` and `version`
- Node role (`EDGE`, `GATEWAY`, `APEX`, `DMZ`, `CLOUD`) and producer IDs
- Producer allowlists in `policy/routing.yaml` aligned to your producer IDs

## Recommended bundle layout

```
zmeta-package/
  deploy/
    edge/
    gateway/
  gateway/
  policy/
  schema/
  adapters/
    mapping-packs/
  configs/
    edge-config.json
    gateway-config.json
    device-packs/
```

Use the same bundle layout in local installs and deployments to keep paths stable.

## Build MVP bundles (edge + gateway)

```
python release/build_mvp_packages.py
```

Outputs:
- `release/bundles/zmeta-edge/`
- `release/bundles/zmeta-gateway/`
- `release/zmeta-edge-mvp.zip`
- `release/zmeta-gateway-mvp.zip`
