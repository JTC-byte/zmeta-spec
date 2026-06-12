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
- TUNNEL messages contain the full ICD and produce proper bearing estimates.
- JSON replay inputs that carry `bearing.az_deg` pass it through as measured;
  replay inputs without bearing data omit the `bearing` block and any
  angular error, same as the serial path.
- All events include `features.sensor_hw = "moth"` and `features.source_format`
  to indicate the input transport.

### Bearing frame (known gap)

Canonical `bearing.az_deg` is contractually degrees true north (semantics
contract section 6.4). Neither the Moth TUNNEL ICD field (`bearing_deg`) nor
the JSON replay format declares a reference frame, so this adapter passes the
value through as received and deliberately asserts **no**
`quality.bearing_frame` provenance — it will not claim a frame the source does
not guarantee. Deployments must guarantee that upstream Moth tunnel/replay
bearings are already degrees true north; consumers needing an asserted frame
should treat these LOBs as legacy unlabeled bearings.

### Usage

```python
from adapters.ingress.moth.moth_to_zmeta import translate_serial_line

event = translate_serial_line(
    '{"peakDbm": -52.3, "peakFreqMhz": 2437.0}',
    platform_id="uav-01",
    sensor_geo={"lat": 43.49, "lon": -112.04, "alt_m": 1500},
)
```

### Source

Extracted from Z-ISR `edge/edge/sensors/moth_rf.py` and
`edge/edge/zmeta_builder.py`.
