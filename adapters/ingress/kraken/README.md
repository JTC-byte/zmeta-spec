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
| confidence (0-99) | `features.kraken_confidence_0_99` | Also mapped to explicit `quality.measurement_error` (`unit: deg`, `metric: 1_SIGMA`) via `_confidence_to_error_deg()` (CSV path) |
| bearing error (JSON `bearing_error_deg`) | `features.angular_error_deg` + `quality.measurement_error` | Omitted entirely when the input lacks it -- an error bound is never invented |
| RSSI | `features.power_dbm` | Measured; missing JSON input is refused |
| centre frequency | `features.center_freq_hz` | Measured; missing JSON input is refused |
| (derived) | `features.bandwidth_hz` | Set to 0 on both paths -- KrakenSDR reports receiver bandwidth, not emitter; a missing JSON `bandwidth_hz` takes the same 0.0 sentinel |

`quality.snr_db` is only emitted on the JSON path when the input provides
`snr_db`. The CSV path carries no noise floor, so SNR is omitted there (earlier
adapter versions fabricated it from RSSI; that is removed as of 1.1.0).

### Missing-input behavior (JSON path)

The CSV path refuses (returns `None`) any row it cannot parse. The JSON path
applies the same honesty rule per field class rather than defaulting:

- **`center_freq_hz` or `power_dbm` missing: refused** -- `translate_json`
  returns `None`. The KrakenSDR measures both, so an absent value means broken
  input, not an unmeasurable quantity (earlier adapter versions fabricated
  `0.0` Hz / `-80.0` dBm; that is removed as of 1.3.0).
- **`bandwidth_hz` missing: `0.0` sentinel**, same convention as the CSV
  path -- the sensor physically cannot measure emitter bandwidth, so 0 is the
  documented "not measured" marker, not a fabricated measurement. This
  convention is unconditional and is not affected by the NaN screening below.
- **`bearing_error_deg` missing: omitted** -- `features.angular_error_deg` and
  `quality.measurement_error` are both schema-optional and are left out
  entirely (earlier adapter versions fabricated a `15.0` deg `1_SIGMA` bound;
  that is removed as of 1.3.0).

### Non-finite input (NaN/inf)

`float()` accepts the literal strings `"nan"` and `"inf"` without raising, and
a JSON payload can carry a bare `NaN`, so parsing success alone does not mean
a value is a real measurement. Both translate paths screen for this at the
adapter boundary:

- **CSV row: any of the five columns non-finite, refused.** `epoch_sec`,
  `doa_deg`, `confidence`, `rssi_db`, and `freq_hz` are all required to build
  the row at all, so a non-finite value in any of them is refused the same
  way an unparseable column is.
- **JSON `bearing_deg`, `center_freq_hz`, or `power_dbm` non-finite,
  refused.** These are the measured fields; a non-finite value means broken
  input, same rule as a missing one above.
- **JSON `bearing_error_deg`, `snr_db`, or `bearing_confidence` non-finite,
  dropped.** These are schema-optional; a non-finite value is treated as
  absent rather than refusing the whole event, and no bound is invented in
  its place.

### Usage

```python
from adapters.ingress.kraken.kraken_to_zmeta import translate_csv_row

fields = ["1712600000.0", "135.2", "85", "-52.3", "433000000"]
event = translate_csv_row(
    fields,
    platform_id="sensor-01",
    sensor_geo={"lat": 43.49, "lon": -112.04, "alt_hae_m": 1433.0},
    platform_heading_deg=270.0,   # from AHRS; omit to suppress canonical bearing
    array_offset_deg=0.0,
    heading_source="AHRS_TRUE",
)
```

Sensor altitude datum (contract 6.2): `sensor_geo` yields a full 3-D
`payload.geo` only with a declared WGS-84 HAE `alt_hae_m`. The legacy
`alt_m` key asserts no datum (a typical caller has a GPS-derived or
surveyed site elevation, which is MSL-referenced), so it never reaches
canonical `alt_m`: the position degrades to the declared 2-D form
(`dimensionality: "2D"`, 1.1.0 stamp) with the value preserved as
`quality.kraken_sensor_alt_unspecified_datum_m`. This is the vertical
instance of the rule the bearing already follows: no frame or datum
evidence, no canonical claim.

### Source

Extracted from Z-ISR `edge/edge/sensors/kraken_rf.py` and
`edge/edge/zmeta_builder.py`.
