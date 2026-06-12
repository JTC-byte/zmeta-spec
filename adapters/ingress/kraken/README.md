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

### Bearing frame (convert-or-omit)

The Kraken DOA azimuth is **array-relative**, not true north. Canonical
`bearing.az_deg` must be degrees true north (semantics contract section 6.4),
so both translate paths (`translate_csv_row` and `translate_json` -- the JSON
replay `bearing_deg` is the same array-relative DOA) apply the same rule,
controlled by keyword-only parameters:

- `platform_heading_deg` (default `None`): platform heading, degrees true north.
- `array_offset_deg` (default `0.0`): fixed clockwise mounting offset of the
  array reference relative to platform heading.
- `heading_source` (default `None`): heading reference label per the contract,
  e.g. `"AHRS_TRUE"`, `"GPS_COURSE"`, `"FIXED_MOUNT_SURVEYED"`.

`translate_http_body` passes all three through to `translate_csv_row`.

- **Compensated** (`platform_heading_deg` given):
  `bearing.az_deg = (doa + platform_heading_deg + array_offset_deg) % 360`,
  `quality.bearing_frame = "TRUE_NORTH"`, and `quality.heading_source` when
  provided. The raw DOA stays available as `features.doa_array_relative_deg`.
- **Omitted** (`platform_heading_deg` is `None`, the default): no canonical
  `bearing` is emitted at all; the raw DOA travels only in
  `features.doa_array_relative_deg`.

### Key mappings

| Kraken field | ZMeta field | Notes |
|-------------|-------------|-------|
| DOA azimuth | `features.doa_array_relative_deg` | Array-relative, always present |
| DOA azimuth (heading-compensated) | `bearing.az_deg` | Degrees true north; only when `platform_heading_deg` is supplied |
| confidence (0-99) | `features.kraken_confidence_0_99` | Also mapped to explicit `quality.measurement_error` (`unit: deg`, `metric: 1_SIGMA`) via `_confidence_to_error_deg()` |
| RSSI | `features.power_dbm` | |
| centre frequency | `features.center_freq_hz` | |
| (derived) | `features.bandwidth_hz` | Set to 0 -- KrakenSDR reports receiver bandwidth, not emitter |

`quality.snr_db` is only emitted on the JSON path when the input provides
`snr_db`. The CSV path carries no noise floor, so SNR is omitted there (earlier
adapter versions fabricated it from RSSI; that is removed as of 1.1.0).

### Usage

```python
from adapters.ingress.kraken.kraken_to_zmeta import translate_csv_row

fields = ["1712600000.0", "135.2", "85", "-52.3", "433000000"]
event = translate_csv_row(
    fields,
    platform_id="sensor-01",
    sensor_geo={"lat": 43.49, "lon": -112.04, "alt_m": 1500},
    platform_heading_deg=270.0,   # from AHRS; omit to suppress canonical bearing
    array_offset_deg=0.0,
    heading_source="AHRS_TRUE",
)
```

### Source

Extracted from Z-ISR `edge/edge/sensors/kraken_rf.py` and
`edge/edge/zmeta_builder.py`.
