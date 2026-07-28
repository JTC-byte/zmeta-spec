# CoT Ingress (Template)

Overview: see `adapters/README.md`.

Purpose: normalize CoT state into ZMeta `STATE_EVENT` / `TRACK_STATE`.

Notes:
- Input is an already-parsed CoT dict (no XML parsing in v1.0).
- Output is a promoted ZMeta track state with minimal lineage.
- `STATE_EVENT` requires `confidence` in the schema; include it in the input when available.
- The template emits `payload.extensions.external_promotion` and a `promote:cot`
  lineage transform so producer-authority policy can reject schema-valid CoT
  reflections that lack explicit promotion evidence.
- `loop_status` must arrive message-carried (`detail.loop_status` or a
  top-level key): the reflection check is a verification this template never
  performs, so its verdict is never self-asserted, and a message without it
  refuses the promotion (contract 4.5.1; same rule as the SAPIENT ingress).
