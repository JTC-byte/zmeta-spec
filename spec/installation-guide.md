# ZMeta Installation and Packaging Guide

This guide focuses on repeatable installs with deterministic settings for gateways
and device configuration packs (drones, sensors, and payloads).

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
inference, fusion, or track/state generation, treat it as an edge analytics node
and set `node_role` accordingly (`GATEWAY` or `FUSION`).

Notes:
- OBSERVATION events do not include `confidence` by schema. Confidence is required
  for INFERENCE/FUSION/STATE events.
- Use `ObservationPayload.quality` to report observation measurement quality
  (e.g., SNR, error bounds, timing quality, calibration state).
- If you need a quality threshold for observations, gate internally and emit only
  when the threshold is met.
- Profiles constrain what leaves the device, not the internal pipeline.
  Profile L exports STATE/SYSTEM/COMMAND only; Profile M allows OBSERVATION/FUSION/STATE;
  Profile H allows the full pipeline.
- When bandwidth is constrained, keep the internal pipeline intact, export only
  the allowed event types, and retain the raw data locally for recall.

## Comms / deconfliction node (gateway + drone)

Keep command authority separated from analytics. Torch (or other analytics) emits
recommendations/inference; a dedicated Comms/Deconfliction node emits COMMAND_EVENT.
This preserves the semantic contract and keeps command governance centralized.
It also makes the analytics layer plug-and-play without expanding the command
surface area.

Recommended pattern:
- Gateway host runs two logical producers:
  - `producer = torch` (analytics; INFERENCE/FUSION/STATE as allowed)
  - `producer = sensorops` (comms/deconfliction; COMMAND_EVENT only)
- Drone host runs a comms module that receives COMMAND_EVENT and translates to
  MAVLink/Swarm API.

Example producer IDs (config snippet):
```
{
  "analytics": { "producer": "torch", "node_role": "GATEWAY" },
  "comms": { "producer": "sensorops", "node_role": "GATEWAY" }
}
```

## Deterministic settings checklist

Capture these in configuration or release notes:
- ZMeta profile (L/M/H)
- Ports and hosts (listen, forward, CoT)
- Policy version and schema version
- Mapping pack `schema_id` and `version`
- Node role (`EDGE`, `GATEWAY`, `FUSION`) and producer IDs

## Recommended bundle layout

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
