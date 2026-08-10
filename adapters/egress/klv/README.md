# ZMeta to KLV Tag Dict (Template)

Overview: see `adapters/README.md`.

Purpose: project ZMeta observations into a decoded KLV-style tag dictionary.

Notes:
- This is NOT a STANAG 4609 binary encoder.
- Output is a tag dict intended for external video pipelines to embed.
- Altitude datum at the handoff (contract 6.2): `geo.alt_m` in the output is
  WGS-84 Height Above Ellipsoid, because canonical ZMeta altitude is HAE by
  contract and this template copies it unconverted. An MISB ST 0601 embedder
  SHALL map it to Tag 75 (Sensor Ellipsoid Height), or Tag 78 (Frame Center
  Height Above Ellipsoid) if the deployment's geo referent is the frame
  center, and SHALL NOT write it to Tag 15 (Sensor True Altitude), Tag 25
  (Frame Center Elevation), or Tag 42 (Target Location Elevation): those
  fields are MSL-defined, no geoid model ships with this template, and an
  unconverted HAE value in an MSL field is the C1-01 wrong-datum class
  outbound.
- `features` values are source-native, not SI-canonical: whatever units and
  datums the ingress preserved (including any raw source altitude keys under
  `features.klv`) cross unconverted under their original names. Only
  `geo.alt_m` carries the canonical HAE guarantee.
- Input is limited to ZMeta `OBSERVATION_EVENT`.
- This is a sensor-metadata projection, not an operator-facing track state.
- `payload.geo` and `payload.features` are copied wholesale, so the guard runs
  on the built tag dict rather than on a list of fields. Any non-finite
  (`NaN`/`inf`) value anywhere in it refuses the whole tag dict (`None`). A
  footprint or feature measurement that is not a number must not be embedded
  in a video stream as if it were one.
- Swept for the SAPIENT egress's all-or-nothing altitude defect (first
  independent SAPIENT interop run, 2026-08) and found clean: `payload.geo`
  is never examined, only copied, so a declared 2-D geo (doctrine A1-02,
  `dimensionality: "2D"`, no `alt_m` — every AIS vessel, a barometric-only
  aircraft) crosses byte-for-byte, dimensionality token included. No fix
  needed here; pinned in `test_declared_2d_geo_from_real_ais_ingress_passes_through_unchanged`.
- That walk covers containers by abstract type (`Mapping`, `Set`, `Sequence`,
  CBOR tag wrappers, `Decimal`), not just `dict`/`list`, and carries a
  seen-set so a cyclic structure, reachable via CBOR value-sharing tags on a
  `cbor2`-only install, terminates instead of hanging the egress path.
