## KrakenSDR Ingress Adapter

Translates KrakenSDR 5-channel coherent receiver DOA output into ZMeta
RF `OBSERVATION_EVENT` (LOB) events.

### Input formats

- **DOA CSV** (from Kraken App HTTP endpoint, typically port 8081):
  `epoch_sec, doa_azimuth_deg, confidence_0_99, rssi_db, center_freq_hz`
- **JSON replay** (bench test / offline replay):
  `{bearing_deg, power_dbm, center_freq_hz, timestamp_ms, ...}`

### Output

`OBSERVATION_EVENT` with `event_subtype: RF`, `modality: RF`.

### Key mappings

| Kraken field | ZMeta field | Notes |
|-------------|-------------|-------|
| DOA azimuth | `bearing.az_deg` | Compass-style, 0=N |
| confidence (0-99) | `features.kraken_confidence_0_99` | Also mapped to explicit `quality.measurement_error` (`unit: deg`, `metric: 1_SIGMA`) via `_confidence_to_error_deg()` |
| RSSI | `features.power_dbm` | |
| centre frequency | `features.center_freq_hz` | |
| (derived) | `features.bandwidth_hz` | Set to 0 -- KrakenSDR reports receiver bandwidth, not emitter |

### Usage

```python
from adapters.ingress.kraken.kraken_to_zmeta import translate_csv_row

fields = ["1712600000.0", "135.2", "85", "-52.3", "433000000"]
event = translate_csv_row(
    fields,
    platform_id="sensor-01",
    sensor_geo={"lat": 43.49, "lon": -112.04, "alt_m": 1500},
)
```

### Source

Extracted from Z-ISR `edge/edge/sensors/kraken_rf.py` and
`edge/edge/zmeta_builder.py`.
