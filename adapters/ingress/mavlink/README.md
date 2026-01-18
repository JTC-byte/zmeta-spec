# MAVLink Ingress (Template)

Overview: see `adapters/README.md`.

Purpose: normalize decoded MAVLink telemetry/status into ZMeta `SYSTEM_EVENT`s.

Notes:
- Input is a decoded MAVLink message dict (no MAVLink parsing library in v1.0).
- Ingress is telemetry/status only; do not emit `COMMAND_EVENT` from MAVLink.
- Emission is heuristic and intentionally minimal.
