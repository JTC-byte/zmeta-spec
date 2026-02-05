# Config Templates

These configs are intended to be edited and used directly by the edge/gateway services.

- `edge-config.json` - Profile L edge relay (forward-only, no CoT emission).
- `gateway-config.json` - Gateway validator + CoT emission.

Notes:
- `schema_path` and `policy_dir` are resolved relative to the config file location.
- Replace `GATEWAY_HOST` in `edge-config.json` with the actual gateway IP/hostname.
- MVP roles: `sensorops` runs comms + edge export; `torch` runs gateway fusion/retasking.
