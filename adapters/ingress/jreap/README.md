# JREAP Ingress (Template)

Overview: see `adapters/README.md`.

Purpose: normalize JREAP/Link-style track dictionaries into ZMeta
`STATE_EVENT` / `TRACK_STATE`.

Notes:
- Input is an already-decoded track dict (no Link-16 encoding/decoding in v1.0).
- Output is a promoted ZMeta track state with minimal lineage.
- `STATE_EVENT` requires `confidence` in the schema; include it in the input when available.
- The template emits `payload.extensions.external_promotion` and a
  `promote:jreap` lineage transform so producer-authority policy can reject
  schema-valid JREAP reflections that lack explicit promotion evidence.
- `loop_status` must arrive message-carried (top-level or `detail` key): the
  reflection check is a verification this template never performs, so its
  verdict is never self-asserted — a track without it refuses the promotion
  (contract 4.5.1; same rule as the SAPIENT ingress).
