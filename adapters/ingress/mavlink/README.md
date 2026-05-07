# MAVLink Ingress Adapter

Translates decoded MAVLink v2 telemetry into ZMeta events.

## Event types produced

| MAVLink message | ZMeta event | Function |
|----------------|-------------|----------|
| GLOBAL_POSITION_INT + GPS_RAW_INT + ATTITUDE | `STATE_EVENT` / `TRACK_STATE` | `translate_platform_state()` |
| SYS_STATUS / BATTERY_STATUS | `SYSTEM_EVENT` / `LINK_STATUS` | `translate_link_status()` |
| SYSTEM_TIME / TIMESYNC | `SYSTEM_EVENT` / `TIME_STATUS` | `translate_time_status()` |
| COMMAND_ACK / MISSION_ACK | `SYSTEM_EVENT` / `TASK_ACK` | `mavlink_decoded_to_zmeta_system_events()` |

## Platform state translation

The `translate_platform_state()` function converts accumulated MAVLink telemetry
into a `STATE_EVENT` with `TRACK_STATE` subtype. It accepts either a dict
or an object with the following fields:

MAVLink platform telemetry can contribute to a ZMeta `STATE_EVENT` only after it
is projected into state-safe fields. `STATE_EVENT` payloads must not contain
`payload.features.*`, raw telemetry measurements, observation modality fields,
observation time windows, or raw data references. Traceability belongs in
`lineage.based_on` and `lineage.transform`.

State-safe fields used by this adapter include:

- `payload.track_id`
- `payload.geo`
- `payload.heading_deg`
- `payload.speed_mps`
- `payload.valid_for_ms`
- `payload.timing_quality`
- `payload.quality` for state quality/status metadata such as GPS fix quality
- top-level `confidence`
- `lineage`

`payload.extensions` must not be used as a loophole for raw measurements. It is
reserved for safe UI/rendering hints that do not reinterpret state.

| MAVLink input concept | Incorrect mapping to avoid | Correct ZMeta treatment | Notes |
|---|---|---|---|
| Global position / GPS fix | `payload.features.position` or raw GPS fields | `STATE_EVENT` `payload.geo` after state projection; GPS quality goes to `payload.quality` or status metadata | Do not expose native GPS packet fields as state features. |
| Heading | `payload.features.heading` | `STATE_EVENT` `payload.heading_deg` | Derived from `GLOBAL_POSITION_INT.hdg` when available. |
| Ground speed | `payload.features.speed` | `STATE_EVENT` `payload.speed_mps` | Computed from velocity components as state, not raw telemetry. |
| GPS fix type / satellite count | `payload.features.gps_fix_type`, `payload.features.satellites_visible` | `payload.quality.gps_fix_type`, `payload.quality.satellites_visible`, and conservative top-level `confidence` | Quality metadata describes state reliability; it is not an observation feature block. |
| Attitude roll/pitch/yaw | `payload.features.*` | `payload.quality.roll_deg`, `payload.quality.pitch_deg`, `payload.quality.yaw_deg` when retained | These are platform-state quality/context fields, not raw observation features. |
| Battery / power state | `STATE_EVENT` `payload.features.battery` | `SYSTEM_EVENT` `LINK_STATUS` in v1.0, or `PLATFORM_STATUS` when using the v1.1.0 branch | Power and platform health are system/status concepts. |
| GPS quality / HDOP / fix status | Raw `STATE_EVENT` feature | `payload.quality`, `payload.timing_quality`, `SYSTEM_EVENT` status, or a future PNT integrity branch | Do not create informal PNT fields in state. |
| Raw sensor measurements | `STATE_EVENT` raw feature, `payload.modality`, `payload.measurement`, `payload.data_ref` | `OBSERVATION_EVENT` only when it is a true supported observation modality; otherwise omit or use a future versioned extension | Do not collapse observation telemetry into state. |
| Native MAVLink message ID | Reuse as `event.event_id` | Keep ZMeta `event.event_id` as UUIDv7; preserve native IDs only as allowed payload-scoped provenance or test metadata | Native IDs must not replace ZMeta event identity. |

Helper functions `decode_global_position_int()`, `decode_attitude()`,
`decode_gps_raw_int()`, and `decode_sys_status()` parse raw MAVLink message
dicts (int-encoded) into the float-valued state dict expected by the translator.

If a native MAVLink field cannot be represented without violating `STATE_EVENT`
semantics, omit it, map it to allowed quality/status metadata, or emit a
separate appropriate ZMeta event with lineage. Raw sensor-style telemetry should
be modeled as `OBSERVATION_EVENT` only when it is truly a sensor observation and
the modality contract applies. Platform health/status telemetry should be
modeled as `SYSTEM_EVENT` where appropriate, especially `PLATFORM_STATUS` when
the v1.1.0 branch is selected.

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
- When `gps_fix_type < 3`, `payload.quality.geo_status` is set to `STALE`.

## Source

Platform state translation extracted from Z-ISR `edge/edge/zmeta_builder.py`
and `edge/edge/mavlink/bridge.py`.
