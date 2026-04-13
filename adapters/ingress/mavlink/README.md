# MAVLink Ingress Adapter

Translates decoded MAVLink v2 telemetry into ZMeta events.

## Event types produced

| MAVLink message | ZMeta event | Function |
|----------------|-------------|----------|
| GLOBAL_POSITION_INT + GPS_RAW_INT + ATTITUDE | `STATE_EVENT` / `PLATFORM_POSITION` | `translate_platform_state()` |
| SYS_STATUS / BATTERY_STATUS | `SYSTEM_EVENT` / `LINK_STATUS` | `translate_link_status()` |
| SYSTEM_TIME / TIMESYNC | `SYSTEM_EVENT` / `TIME_STATUS` | `translate_time_status()` |
| COMMAND_ACK / MISSION_ACK | `SYSTEM_EVENT` / `TASK_ACK` | `mavlink_decoded_to_zmeta_system_events()` |

## Platform state translation

The `translate_platform_state()` function converts accumulated MAVLink telemetry
into a `STATE_EVENT` with `PLATFORM_POSITION` subtype. It accepts either a dict
or an object with the following fields:

| MAVLink source | State field | ZMeta mapping |
|---------------|-------------|---------------|
| GLOBAL_POSITION_INT.lat/lon | lat, lon | `payload.geo.lat`, `payload.geo.lon` |
| GLOBAL_POSITION_INT.alt | alt_m | `payload.geo.alt_m` |
| GLOBAL_POSITION_INT.hdg | heading_deg | `payload.heading_deg` |
| GLOBAL_POSITION_INT.vx/vy | speed_mps | `payload.speed_mps` (computed) |
| GPS_RAW_INT.fix_type | gps_fix_type | `payload.features.gps_fix_type`, `confidence` |
| GPS_RAW_INT.satellites_visible | satellites_visible | `payload.features.satellites_visible` |
| ATTITUDE.roll/pitch/yaw | roll_deg, pitch_deg, yaw_deg | `payload.features.*` |
| SYS_STATUS.voltage_battery | battery_voltage | `payload.features.battery_voltage` |

Helper functions `decode_global_position_int()`, `decode_attitude()`,
`decode_gps_raw_int()`, and `decode_sys_status()` parse raw MAVLink message
dicts (int-encoded) into the float-valued state dict expected by the translator.

## Usage

```python
from adapters.ingress.mavlink.mavlink_to_zmeta_template import (
    translate_platform_state,
    decode_global_position_int,
    decode_gps_raw_int,
)

# Accumulate state from individual MAVLink messages
state = {}
state.update(decode_global_position_int({"lat": 434900000, "lon": -1120400000, "alt": 1500000, "hdg": 13500, "vx": 500, "vy": 0, "vz": 0}))
state.update(decode_gps_raw_int({"fix_type": 3, "satellites_visible": 12}))

event = translate_platform_state(state, platform_id="uav-01")
```

## Notes

- Input is a decoded MAVLink message dict (no MAVLink parsing library required).
- Ingress is telemetry/status only; do not emit `COMMAND_EVENT` from MAVLink.
- GPS fix type maps to confidence: 3D+ = 0.8, 2D = 0.5, lower = 0.2.
- When `gps_fix_type < 3`, the feature `geo_stale: true` is set.

## Source

Platform state translation extracted from Z-ISR `edge/edge/zmeta_builder.py`
and `edge/edge/mavlink/bridge.py`.
