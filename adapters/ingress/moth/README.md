## Heaviside Moth Ingress Adapter

Translates Moth RF sensor output into ZMeta RF `OBSERVATION_EVENT` (LOB) events.

The Moth is a compact RF sensor that outputs peak frequency and signal strength
readings via serial, MAVLink TUNNEL messages, or a custom MAVLink dialect.
It has no antenna array, so raw readings carry 180-degree bearing uncertainty.
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

- Serial and custom MAVLink readings produce events with `bearing.az_deg = 0.0`
  and `angular_error_deg = 180.0` (omnidirectional).
- TUNNEL messages contain the full ICD and produce proper bearing estimates.
- All events include `features.sensor_hw = "moth"` and `features.source_format`
  to indicate the input transport.

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
