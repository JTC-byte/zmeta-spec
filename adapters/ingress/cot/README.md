# CoT Ingress (Template)

Overview: see `adapters/README.md`.

Purpose: normalize CoT state into ZMeta `STATE_EVENT` / `TRACK_STATE`.

Notes:
- Input is an already-parsed CoT dict (no XML parsing in v1.0).
- Output is a ZMeta track state with minimal lineage.
- `STATE_EVENT` requires `confidence` in the schema; include it in the input when available.
