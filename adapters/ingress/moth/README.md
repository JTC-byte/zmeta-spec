## Heaviside Moth Ingress Adapter

Translates Moth RF sensor output into ZMeta RF `OBSERVATION_EVENT` (LOB) events.

The Moth is a compact RF sensor that outputs peak frequency and signal strength
readings via serial, MAVLink TUNNEL messages, or a custom MAVLink dialect.
It has no antenna array, so raw serial and custom MAVLink readings are
omnidirectional: they carry no bearing, and the canonical `bearing` block is
omitted per the convert-or-omit rule (semantics contract section 6.4).
True bearing estimates are derived downstream by correlating signal strength
with UAS heading during yaw scans.

### Input formats

| Format | Function | Notes |
|--------|----------|-------|
| Serial JSON | `translate_serial_line()` | `{"peakDbm": -45.2, "peakFreqMhz": 2437.0}` |
| Serial CSV | `translate_serial_line()` | `2437.0,-45.2` (freq first, power second) |
| MAVLink TUNNEL | `translate_tunnel_payload()` | 32-byte struct with full LOB (bearing, freq, power, SNR, elevation, confidence) |
| Custom MAVLink msg | `translate_custom_mavlink()` | 6-byte payload (float32 freq_mhz + int16 power_dbm), shown as `UNKNOWN_15610` by pymavlink |
| JSON replay | `translate_json_replay()` | Structured dict with `bearing`, `frequency`, `power` sub-objects |

### Output

`OBSERVATION_EVENT` with `event_subtype: RF`, `modality: RF`.

### Key behaviors

- Serial and custom MAVLink readings are omnidirectional, so the `bearing`
  block and `angular_error_deg` are omitted entirely (a fabricated north
  bearing with 180-degree error would mislead downstream LOB fusion).
- TUNNEL messages contain the full ICD bearing fields, but the canonical
  `bearing` block is emitted only when the caller passes
  `bearing_frame="TRUE_NORTH"`.
- JSON replay inputs that carry `bearing.az_deg` follow the same rule:
  unknown-frame bearings are preserved as raw, explicitly named feature fields;
  replay inputs without bearing data omit bearing and angular error fields.
- All events include `features.sensor_hw = "moth"` and `features.source_format`
  to indicate the input transport.

### Bandwidth sentinel

`features.bandwidth_hz` is set to 0.0 on the serial and custom MAVLink paths
-- the Moth reports peak frequency and power, not emitter bandwidth, so 0.0
is the documented "no emitter bandwidth measured" sentinel (the same
convention as the KrakenSDR adapter, whose receiver likewise cannot measure
emitter bandwidth). The TUNNEL path passes the ICD `bw_hz` field through
unchanged; a 0.0 there carries the same sentinel meaning. On the JSON replay
path, a missing `frequency.bandwidth_hz` defaults to the 0.0 sentinel.

### Non-finite input (NaN/inf)

`translate_serial_line()` accepts both a JSON payload (which can carry a bare
`NaN`) and CSV text (where `float()` accepts the literal `"nan"`/`"inf"`
without raising), so parsing success alone does not mean `peakDbm` or
`peakFreqMhz` is a real reading. A non-finite value in either field is
refused, the same as a missing one.

`translate_custom_mavlink()` wire-encodes `freq_mhz` as a float32, which can
carry a NaN bit pattern from a corrupted or partially-written frame. The
existing sanity bounds (`freq_mhz <= 0`, `freq_mhz > 10000`) do not catch
this: both comparisons are false for NaN, the same way every comparison
against NaN is false, so a NaN reading passed the bound check unchallenged
before an explicit `isfinite` check was added ahead of it. (`power_dbm` is
wire-encoded as `int16` on this path and cannot itself carry a NaN bit
pattern.)

### JSON replay refusal matrix and geo (all-or-nothing)

`translate_json_replay()` never fabricates schema-required RF measurements:

| Missing input field | Behavior |
|---------------------|----------|
| `frequency.center_hz` | Refused -- returns `None` |
| `power.rssi_dbm` | Refused -- returns `None` |
| `frequency.bandwidth_hz` | Emitted with the documented 0.0 sentinel (above) |
| `bearing_error_deg` (in `bearing_frame="TRUE_NORTH"` mode) | Emitted without `features.angular_error_deg` and `quality.measurement_error` -- an error bound is never invented |

Canonical `geo` is all-or-nothing (contract 6.8) and datum-gated (contract
6.2): a caller-supplied `sensor_geo` or replay `sensor_position` yields a
full 3-D `payload.geo` only when `lat`, `lon`, and a declared WGS-84 HAE
`alt_hae_m` are all present. The legacy `alt_m` key asserts no datum -- in
this adapter's UAS origin the natural position source is autopilot
telemetry, whose MAVLink global-position altitude is MSL -- so it never
reaches canonical `alt_m`: the position degrades to the declared 2-D form
(`dimensionality: "2D"`, 1.1.0 stamp, `quality.geo_status:
VERTICAL_UNAVAILABLE`) with the value preserved as
`quality.moth_sensor_alt_unspecified_datum_m`. This is the same rule the
bearing axis gets from the frame gate below: no evidence, no claim. A
position with no vertical of any kind omits `geo` entirely with
`quality.geo_status: UNAVAILABLE` -- missing values are never zero-filled.

### Bearing frame

Canonical `bearing.az_deg` is contractually degrees true north (semantics
contract section 6.4). Neither the Moth TUNNEL ICD field (`bearing_deg`) nor
the JSON replay format declares a reference frame. By default this adapter
therefore omits canonical `payload.bearing` and preserves the raw input under
explicit feature names such as `features.bearing_frame_unknown_deg`,
`features.bearing_frame_unknown_error_deg`, and
`features.bearing_frame_unknown_el_deg`.

Deployments that have upstream ICD or configuration evidence that the
tunnel/replay bearing is already degrees true north may pass
`bearing_frame="TRUE_NORTH"` to `translate_tunnel_payload()` or
`translate_json_replay()`. In that mode the adapter emits canonical
`payload.bearing`, records `quality.bearing_frame = "TRUE_NORTH"`, and keeps
the angular error as canonical bearing uncertainty.

### Usage

```python
from adapters.ingress.moth.moth_to_zmeta import translate_serial_line

event = translate_serial_line(
    '{"peakDbm": -52.3, "peakFreqMhz": 2437.0}',
    platform_id="uav-01",
    sensor_geo={"lat": 43.49, "lon": -112.04, "alt_hae_m": 1433.0},
)
```

### Source

Extracted from Z-ISR `edge/edge/sensors/moth_rf.py` and
`edge/edge/zmeta_builder.py`.
