## EO (Computer Vision) Ingress Adapter

Translates CV inference service detections into ZMeta `INFERENCE_EVENT`
classification events. EO/IR detections are semantic claims, not raw
observations.

### Input format

JSON messages from a computer vision inference service. Two envelope styles
are supported:

```json
{"type": "detection", "payload": {"class_name": "person", "confidence": 0.92, "gps": [43.49, -112.04], ...}}
```

```json
{"class_name": "vehicle", "confidence": 0.85, "bbox": [100, 200, 300, 400], ...}
```

### Output

`INFERENCE_EVENT` with `event_subtype: CLASSIFICATION` and
`payload.inference_type: CLASSIFICATION`. Detection boxes are emitted as
`payload.claim.bbox`; EO `OBSERVATION_EVENT` uses `features.roi_px` only for
raw image region/crop metadata.

### GPS resolution logic

The adapter implements a multi-tier GPS fallback:

1. **Detection GPS**: Use `gps: [lat, lon]` from the detection if present
   and not the (0, 0) sentinel.
2. **Plausibility check**: If detection GPS is >10km from the platform/sensor
   GPS, discard it and fall back to sensor GPS.
3. **FC fallback**: If detection GPS is missing or (0, 0), use the
   platform/flight-controller position.
4. **Unavailable**: If no GPS is available from any source, use (0, 0, 0)
   and mark `geo_source: "unavailable"`.

The `payload.claim.geo_source` field records which tier was used:
`"detection"`, `"fc_fallback"`, or `"unavailable"`.

### Key mappings

| CV field | ZMeta field | Notes |
|----------|-------------|-------|
| class_name | `payload.claim.label` | Semantic classification |
| confidence | top-level `confidence` | Subject to `confidence_floor` filter |
| gps | `payload.claim.geo` | Destructured from [lat, lon] array |
| bbox | `payload.claim.bbox` | Detected object box; not an EO observation `roi_px` |
| track_id | `payload.claim.source_object_id` | Source tracker/object ID, not ZMeta `track_id` |
| stream_id | `source.sensor_id` | Camera/stream identifier |

### Usage

```python
from adapters.ingress.eo_cv.eo_cv_to_zmeta import translate

event = translate(
    {"class_name": "person", "confidence": 0.92, "gps": [43.49, -112.04]},
    platform_id="uav-01",
    sensor_geo={"lat": 43.50, "lon": -112.05, "alt_m": 1500},
    confidence_floor=0.5,
)
```

### Source

Extracted from Z-ISR `edge/edge/sensors/eo_consumer.py` and
`edge/edge/zmeta_builder.py`.
