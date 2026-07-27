## bladeRF Ingress Adapter

Translates edge-comms bladeRF / ROS2 EW `rf_detection` records into ZMeta
RF `OBSERVATION_EVENT` events. Reference implementation for the
`adapters/mapping-packs/edge-comms-bladerf` mapping pack; pinned to that pack's
two real-capture fixture pairs.

### Input format

Structured `rf_detection` JSON (schema_id `vendor:edge_comms_bladerf:v1`) from
the `ros2_ew` producer, topics `sdr/orbit_spectrum` (reduced orbit spectrum)
and `spectrum_fft` (FFT peak). These are decoded detections -- centre
frequency, power, SNR, noise floor, bearing metadata -- not raw IQ; the
DSP/FFT stage runs upstream of ZMeta (AUTHORING section 1).

### Output

`OBSERVATION_EVENT`, `event_subtype: RF`, `modality: RF`, producer
`rf-sensor-bladerf` (matches the reference `rf-sensor-*` producer-authority
pattern), `node_role: EDGE`. `platform_id` is deployment-supplied;
`sensor_id` defaults to `metadata.zmeta_sensor_id`.

### Entry points

- `detect(input_bytes) -> schema_id | None` -- recognises a JSON detection
  whose `metadata.sensor_hw == "bladerf"`.
- `translate(input_obj, schema_id=SCHEMA_ID, *, platform_id, sensor_id=None,
  based_on=None, timing_quality=None) -> list[dict]` -- returns `[event]` or
  `[]` (fail-closed refusal). Harness-facing entry point.
- `translate_detection(...) -> dict | None` -- single-record worker.
- `validate(zmeta_event) -> ("pass"|"fail", violations)`.

### Bearing frame (convert-or-omit) -- the load-bearing decision

The native `bearing_deg` is **heading-derived**: UAS heading plus a fixed
antenna offset. The capture asserts **no reference frame** --
`metadata.heading_source` (`"interpolated"`) names a *sampling method*, not a
datum, and nothing in the record claims true north. Per **semantics contract
6.4** and **AUTHORING rule 2**, an unlabeled/unprovable frame stays in
explicitly named non-canonical features and the canonical `payload.bearing` is
**omitted in both cases** -- including case-02, whose `bearing_source` is
`heading_at_peak`. Emitting `payload.bearing.az_deg` here would require minting
a `TRUE_NORTH` assertion the producer never made -- the laundering the mirror
case in AUTHORING section 3 explicitly prohibits.

| Native field | ZMeta field |
|---|---|
| `bearing_deg` | `features.native_bearing_deg` |
| `bearing_error_deg` | `features.native_bearing_error_deg` |
| `metadata.bearing_source` | `features.bearing_source` |
| `metadata.heading_source` | `features.heading_source_native` |
| `metadata.uas_heading_deg` | `features.uas_heading_deg` |

The raw `bearing_error_deg` declares no statistical metric, so it stays a
feature and **no `quality.measurement_error`** is claimed (AUTHORING rule 3).
A deployment that can assert `TRUE_NORTH` for its heading source may emit
canonical `bearing` with `quality.bearing_frame` + `quality.heading_source`,
mirroring the kraken reference adapter -- a code change, not a default.

### Geo (all-or-nothing)

`payload.geo` is emitted only when `sensor_lat`, `sensor_lon`, and
`sensor_alt_m` are all present **and** the fix is not the null-island `(0,0)`
sentinel; otherwise geo is omitted and `quality.geo_status` is `UNAVAILABLE`
(contract 6.8, AUTHORING rule 9). Both fixtures refuse geo: case-01 has null
positions, case-02 has `(0.0, 0.0)`. Missing components are never zero-filled.

### Key feature mappings

| Native | ZMeta feature | Notes |
|---|---|---|
| `center_freq_hz` | `features.center_freq_hz` | Required (contract 7.4); refused if missing |
| `bandwidth_hz` | `features.bandwidth_hz` | Required. On `spectrum_fft` this is the **FFT bin width** (`sample_rate_hz / fft_size`) -- a documented resolution artifact the source reports, not a measured emitter bandwidth; passed through verbatim |
| `power_dbm` | `features.power_dbm` | Required; refused if missing |
| `snr_db` | `features.snr_db` + `quality.snr_db` | Emitted only when the source reports it |
| `noise_floor_dbm`, `detection_id` | same-named features | Copied when present |
| `metadata.timestamp_source` | `features.timestamp_source` | Records whether `event.ts` came from embedded telemetry (case-02) or adapter receive time (case-01) |
| `metadata.{fft_bin,fft_size,bin_width_hz,sample_rate_hz,fft_center_freq_hz}` | same-named features | `spectrum_fft` product only |
| `metadata.{orbit_spectrum_bin,orbit_spectrum_bins}` | same-named features | `orbit_spectrum` product only |

Only whitelisted metadata crosses into features; unmapped vendor metadata
(`antenna_left`, `baseline_m`, `scan_state`, ...) is intentionally dropped so
the canonical event carries only consumer-relevant provenance.

### Timing (degraded fallback)

The `rf_detection` format carries no clock-sync metadata, so timing falls to
the deliberately degraded fallback from `coerce_timing_quality`:
`time_source: UNKNOWN`, `sync_state: UNSYNCED`, `est_error_ms: 60000`,
`last_sync_ts` = `event.ts` (contract 5.3, AUTHORING rule 5). When a deployment
wires real GPS/NTP/PTP metadata, pass it via `timing_quality` to replace the
fallback -- never with an invented clean value.

### Lineage

Original detections have no ZMeta parent, so `lineage` is omitted entirely
(contract 4.8). When a caller supplies real parent event ids via `based_on`,
the event stamps `lineage.based_on` and
`lineage.transform = translate:vendor:edge_comms_bladerf:v1@1.0.0`. Parent ids
are never fabricated.

### Tests

`test_bladerf_ingress.py` runs both pack fixture pairs as acceptance tests
(exact reproduction of `expected.json` modulo the runtime UUIDv7 `event_id`,
plus schema validation) and pins the honesty decisions above, including one
fail-closed refusal per schema-required field (AUTHORING section 9).

```
python -m pytest adapters/ingress/bladerf -q
```

Harness fixtures for this adapter live in
`conformance/adapter-harness/must-pass.jsonl` (entries prefixed `bladerf-`).

### Source

Real captures from Z-ISR
`flight-artifacts-2026-05-14_v22rfpayload-edge-comms`
(`blackbox_141233.jsonl`, native category `rf_detection`).
