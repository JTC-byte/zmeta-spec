## KLV to ZMeta (Template)

Overview: see `adapters/README.md`.

Purpose: normalize decoded KLV metadata into ZMeta OBSERVATION_EVENT.

Assumption: input is already decoded into a dict of KLV tags. This repo does not
ship a full MISB 4609 parser.

Template function: `klv_decoded_to_zmeta_observation(decoded_klv, platform_id, sensor_id, producer, ts)`.

### Altitude datum (contract 6.2)

Canonical `payload.geo.alt_m` is WGS-84 Height Above Ellipsoid. MISB ST 0601
defines its dominant altitude tags as MSL, so the decoder feeding this
template must name the datum in the keys it produces:

| ST 0601 tag | Datum | Decoded key | Disposition |
| --- | --- | --- | --- |
| Tag 75 Sensor Ellipsoid Height | HAE | `alt_hae_m` | The only key that may occupy canonical `geo.alt_m` (1.0 stamp) |
| Tag 15 Sensor True Altitude | MSL | `alt_msl_m` | Never canonical: geo degrades to the declared 2-D form (`dimensionality: "2D"`, 1.1.0 stamp), value preserved as `quality.klv_alt_msl_m` |
| Tag 25 Frame Center Elevation | MSL | `alt_msl_m` | As above, and see the referent note below |
| Tag 42 Target Location Elevation | MSL | `alt_msl_m` | As above, and see the referent note below |
| legacy generic `alt_m` | unspecified | `alt_m` | Never canonical: same 2-D degrade, value preserved as `quality.klv_alt_unspecified_datum_m` |

Both datums present: HAE wins. No altitude of any kind: geo is omitted
entirely (all-or-nothing, contract 6.8), never zero-filled. The 2-D branch
also sets `quality.geo_status: "VERTICAL_UNAVAILABLE"`.

Referent note: this template's `payload.geo` asserts the sensor position
(Tags 13/14 plus the sensor altitude tags). Frame center (Tags 23/24/25/78)
and target location (Tags 40/41/42) are different world points; a decoder
that maps one of them into `lat`/`lon`/`alt_hae_m` is asserting a different
thing than the event's source fields claim. Route those points to `features`
or to separate events.

The whole decoded dict still travels as `payload.features.klv`, so
source-native values, including MSL altitudes under their original tags,
remain available unconverted. Features carry source-native datums and units;
only `payload.geo` is canonical.

Mapping guidance:
- KLV timestamp -> event.ts
- platform/sensor IDs -> source fields
- geo fields -> payload.geo per the altitude-datum table above (WGS-84;
  only `alt_hae_m` reaches `alt_m`)
- derived analytics -> separate INFERENCE_EVENT
- store-and-forward raw KLV/video is separate
- lineage is omitted unless the caller supplies real parent event ids via
  `based_on`; when supplied, lineage.transform ->
  `translate:klv@<adapter_version>`. Parent ids are never fabricated.

### Smoke test

```
python - <<'PY'
from adapters.ingress.klv.klv_to_zmeta_template import klv_decoded_to_zmeta_observation

decoded = {"lat": 34.0, "lon": -118.0, "alt_hae_m": 96.0, "sensor_mode": "EO"}
event = klv_decoded_to_zmeta_observation(
  decoded,
  platform_id="platform-1",
  sensor_id="sensor-1",
  producer="klv:misb:0601",
  ts="2025-01-17T15:20:00Z",
)
print(event)
PY
```
