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
