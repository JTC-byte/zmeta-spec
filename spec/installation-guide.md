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
and set `node_role` accordingly (`GATEWAY` or `APEX`).

Notes:
- OBSERVATION events do not include `confidence` by schema. Confidence is required
  for INFERENCE/FUSION/STATE events.
- If you need a quality threshold for observations, gate internally and emit only
  when the threshold is met.
- Profiles constrain what leaves the device, not the internal pipeline.
  Profile L exports STATE/SYSTEM/COMMAND; Profile M allows OBSERVATION/FUSION/STATE/SYSTEM/COMMAND;
  Profile H allows the full pipeline.
- When bandwidth is constrained, keep the internal pipeline intact, export only
  the allowed event types, and retain the raw data locally for recall.

## Deterministic settings checklist

Capture these in configuration or release notes:
- ZMeta profile (L/M/H)
- Ports and hosts (listen, forward, CoT)
- Policy version and schema version
- Mapping pack `schema_id` and `version`
- Node role (`EDGE`, `GATEWAY`, `APEX`, `DMZ`, or `CLOUD`) and producer IDs
- Failure mode thresholds and confidence reduction policy
- Timing quality source, sync-state reporting cadence, and `est_error_ms` policy

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
