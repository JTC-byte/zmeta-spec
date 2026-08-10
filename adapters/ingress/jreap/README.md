# JREAP Ingress (Template)

Overview: see `adapters/README.md`.

Purpose: normalize JREAP/Link-style track dictionaries into ZMeta
`STATE_EVENT` / `TRACK_STATE`.

Notes:
- Input is an already-decoded track dict (no Link-16 encoding/decoding in v1.0).
- Altitude datum (contract 6.2): `hae_m` SHALL be WGS-84 Height Above
  Ellipsoid in metres, and it is the only input key that may occupy canonical
  `payload.geo.alt_m`. JREAP/Link-16 native track altitude fields carry their
  own datums (typically barometric/pressure or MSL-referenced heights); the
  decode layer feeding this template must convert them to HAE or hand them
  over under the legacy `alt_m` key, which is treated as datum-unlabeled:
  never canonical, the event degrades to the declared 2-D geo form
  (`dimensionality: "2D"`, 1.1.0 stamp) and the value is preserved as
  `quality.jreap_alt_unlabeled_datum_m`. No altitude of any kind refuses the
  promotion.
- Output is a promoted ZMeta track state with minimal lineage.
- `STATE_EVENT` requires `confidence` in the schema; include it in the input when available.
- The template emits `payload.extensions.external_promotion` and a
  `promote:jreap` lineage transform so producer-authority policy can reject
  schema-valid JREAP reflections that lack explicit promotion evidence.
- `loop_status` must arrive message-carried (top-level or `detail` key): the
  reflection check is a verification this template never performs, so its
  verdict is never self-asserted, and a track without it refuses the promotion
  (contract 4.5.1; same rule as the SAPIENT ingress).
