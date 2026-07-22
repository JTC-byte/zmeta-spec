# ZMeta to KLV Tag Dict (Template)

Overview: see `adapters/README.md`.

Purpose: project ZMeta observations into a decoded KLV-style tag dictionary.

Notes:
- This is NOT a STANAG 4609 binary encoder.
- Output is a tag dict intended for external video pipelines to embed.
- Input is limited to ZMeta `OBSERVATION_EVENT`.
- This is a sensor-metadata projection, not an operator-facing track state.
- `payload.geo` and `payload.features` are copied wholesale, so the guard runs
  on the built tag dict rather than on a list of fields. Any non-finite
  (`NaN`/`inf`) value anywhere in it refuses the whole tag dict (`None`) — a
  footprint or feature measurement that is not a number must not be embedded
  in a video stream as if it were one.
- That walk covers containers by abstract type (`Mapping`, `Set`, `Sequence`,
  CBOR tag wrappers, `Decimal`), not just `dict`/`list`, and carries a
  seen-set so a cyclic structure — reachable via CBOR value-sharing tags on a
  `cbor2`-only install — terminates instead of hanging the egress path.
