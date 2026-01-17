## KLV to ZMeta (Template)

Purpose: normalize decoded KLV metadata into ZMeta OBSERVATION_EVENT.

Assumption: input is already decoded into a dict of KLV tags. This repo does not
ship a full MISB 4609 parser.

Template function: `klv_decoded_to_zmeta_observation(decoded_klv, platform_id, sensor_id, producer, ts)`.

Mapping guidance:
- KLV timestamp -> event.ts
- platform/sensor IDs -> source fields
- geo fields -> payload.geo (WGS-84, HAE)
- derived analytics -> separate INFERENCE_EVENT
- store-and-forward raw KLV/video is separate

### Smoke test

```
python - <<'PY'
from adapters.ingress.klv.klv_to_zmeta_template import klv_decoded_to_zmeta_observation

decoded = {"lat": 34.0, "lon": -118.0, "alt_m": 120.0, "sensor_mode": "EO"}
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
