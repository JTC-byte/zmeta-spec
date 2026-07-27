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
`lineage.based_on` and `lineage.transform`, and it must be real: the caller
supplies `state["based_on"]` (parent ZMeta event ids, UUIDv7) or
`state["source_zmeta_event_id"]`. Without one of those the translator refuses
to emit — a lineage parent is never fabricated. The SYSTEM_EVENT builders
(`translate_link_status`, `translate_time_status`) omit lineage unless the
caller passes `based_on` (SYSTEM_EVENT lineage is optional).

State-safe fields used by this adapter include:

- `payload.track_id`
- `payload.geo`
- `payload.heading_deg` only when deployment config explicitly asserts a
  true-north heading frame
- `payload.speed_mps`
- `payload.valid_for_ms`
- `payload.timing_quality`
- `payload.quality` for state quality/status metadata such as GPS fix quality
- top-level `confidence`
- `lineage`

`payload.extensions` must not be used as a loophole for raw measurements. The
MAVLink state template uses `payload.extensions.external_promotion` only as
policy-scoped boundary evidence for the promotion decision; it does not carry
raw telemetry or reinterpret state. `loop_status` must arrive in the decoded
telemetry dict: the reflection check is a verification the template never
performs, so its verdict is never self-asserted — a message without it
refuses the promotion (returns None; contract 4.5.1, same rule as the
SAPIENT ingress).

| MAVLink input concept | Incorrect mapping to avoid | Correct ZMeta treatment | Notes |
|---|---|---|---|
| Global position / GPS fix | `payload.features.position` or raw GPS fields | `STATE_EVENT` `payload.geo` after state projection; GPS quality goes to `payload.quality` or status metadata | Do not expose native GPS packet fields as state features. |
| Heading | `payload.features.heading` | `STATE_EVENT` `payload.heading_deg` only with `heading_frame="TRUE_NORTH"`; otherwise `payload.quality.mavlink_hdg_frame_unknown_deg` | Derived from `GLOBAL_POSITION_INT.hdg` when available; omitted (never defaulted to 0) when `hdg` is unknown (`UINT16_MAX`). |
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

event = translate_platform_state(
    state,
    platform_id="uav-01",
    heading_frame="TRUE_NORTH",
    heading_source="AHRS_TRUE",
)
```

## Notes

- Input is a decoded MAVLink message dict (no MAVLink parsing library required).
- Ingress is telemetry/status only; do not emit `COMMAND_EVENT` from MAVLink.
- GPS fix type maps to confidence: 3D+ = 0.8, 2D = 0.5, lower = 0.2.
- When `gps_fix_type < 3`, `payload.quality.geo_status` is set to `STALE`.
- `translate_platform_state()` refuses to fabricate a position (returns
  `None`, no event) when any of `lat`/`lon`/`alt_m` is absent, or when
  `gps_fix_type < 2` with `lat == 0.0` and `lon == 0.0` (the ArduPilot
  pre-lock "null island" signature). Canonical `geo` is all-or-nothing
  (semantics contract 6.8: "If any of `lat`, `lon`, or `alt_m` is missing,
  omit `geo` entirely. Missing values MUST be omitted, not zero-filled"), and
  the v1.0 schema requires `payload.geo` on `TRACK_STATE` — so a state without
  a complete usable position must not be emitted rather than defaulted to
  `(0, 0, 0)`. A fabricated `alt_m: 0.0` is not harmless padding: CoT egress
  re-projects it as a concrete `hae="0.0"` altitude claim, and deconfliction,
  terrain masking and 3D fusion all consume it. `decode_global_position_int()`
  likewise decodes absent `lat`/`lon`/`alt` to `None` instead of `0.0`.
  Stale-but-real coordinates without a current fix are still emitted with
  `geo_status: STALE` and floor confidence. This follows the kraken/moth
  anti-fabrication pattern (convert or refuse, never invent).
- The same rule applies to every other never-reported value, not only to
  `geo` and not only to numbers. Every scalar this adapter emits is either a
  value the telemetry carried or a constant declared — with its reason — in
  the provenance sweeps in `test_mavlink_ingress.py`, which are path-scoped
  (a constant is authorised at one path, not as a literal everywhere) and
  cover strings and categorical verdicts, not only numerics:
  - an unreported `speed_mps` omits `payload.speed_mps` rather than asserting
    a stationary platform;
  - an unreported `gps_fix_type` / `satellites_visible` omits
    `payload.quality.gps_fix_type` / `.satellites_visible` rather than
    restating "no GPS / 0 satellites" — while still driving the conservative
    confidence floor, `geo_status: STALE` and the null-island refusal, so the
    omission only ever degrades the event;
  - `decode_attitude()` decodes an unreported axis to explicit `None`, not to
    0.0° (a measured level attitude) and not to an omitted key. An omitted key
    would leave the *previous* message's roll in the accumulating state dict
    below, and the translator would then publish it as a current reading with
    no per-field staleness marker — stale-presented-as-current is the same
    class as fabricated-as-measured. `decode_global_position_int()` already
    clobbers for the same reason;
  - `decode_gps_raw_int()` omits unreported fix quality and drops the MAVLink
    `satellites_visible = UINT8_MAX` (255) "count unknown" sentinel so it never
    becomes a 255-satellite reading; and `decode_sys_status()` omits both
    SYS_STATUS "not sent" sentinels (`voltage_battery = UINT16_MAX`,
    `battery_remaining = -1`) so neither becomes a 0 V flat battery nor a
    65.535 V reading;
  - every one of those sentinels is guarded on the **translator** side as well,
    because a state dict — and every `translate_link_status()` keyword — can be
    assembled by any bridge, so a decoder-only guard is half a guard. The full
    family, enumerated from the emitted fields rather than from the decoders:
    `satellites_visible` / `rc_rssi` / RADIO_STATUS `rssi` all carry MAVLink's
    uint8 "Values: [0-254], UINT8_MAX: invalid/unknown" convention and drop
    255 (255 on a 0–254 scale reads downstream as the strongest signal ever
    observed); `battery_voltage` drops the UINT16_MAX sentinel in volts
    (`65.535`, what a bridge that divides before handing over produces) as well
    as a non-positive value; `battery_remaining_pct` drops `-1`; and a heading
    outside 0–360 — commonly `655.35`, the `hdg = UINT16_MAX` sentinel divided
    by 100 — is dropped from both destinations rather than clamped, since the
    canonical `payload.heading_deg` is schema-bounded but the non-canonical
    `quality.mavlink_hdg_frame_unknown_deg` is not. Nothing is clamped: a clamp
    would invent a measurement at the top of the scale;
  - `translate_link_status()` requires caller-supplied `latency_ms`,
    `packet_loss_pct` and `throughput_bps` (the three measurements the v1.0
    schema requires on a LINK_STATUS payload) and raises `ValueError` without
    them, rather than reporting a perfect link the node never measured;
    `battery_voltage`, `battery_pct` and `rc_rssi` are omitted when
    unreported;
  - `payload.state` — the field a consumer reads before any metric — is never
    hard-coded either. `translate_link_status()` takes a caller-supplied
    `state` and defaults to the schema's own `UNKNOWN`, not `UP`: measuring
    latency is not the same as adjudicating link health, and every measured
    metric still travels so the consumer adjudicates. `DEGRADED`/`DOWN`
    additionally require `reason_code`, and an out-of-vocabulary state is
    refused rather than emitted schema-invalid. `reason_code` gets the same
    treatment as `state` and not merely a presence check: an out-of-vocabulary
    code is refused, and a code supplied under `state="UP"` is refused too — a
    healthy link with a cause of degradation contradicts itself in the field
    the operator reads first, and which half the caller meant is not
    adjudicable here. `UNKNOWN` may still carry a cause, because "I measured
    this and I am not adjudicating health" is an honest pair;
  - `translate_time_status()` requires caller-supplied `est_error_ms` and
    `last_sync_ts` and raises `ValueError` without them — a `0.0` timing
    error asserts a perfect clock in the very field consumers read to decide
    how far to trust the timeline, and a defaulted `last_sync_ts` asserts a
    sync that just happened;
  - both TIME_STATUS emitters derive `payload.state` from the sync verdict
    the message carried, through one shared derivation, so identical
    telemetry can never yield two opposite verdicts and an `UNSYNCED` metrics
    block can never sit under a `SYNCED` state. A carried verdict is honoured
    only when it is *more* conservative than the derived one, compared on a
    declared severity ordering (`UP` < `DEGRADED` < `DOWN`, with `SYNCED` as a
    spelling of `UP`) and after whitespace/case normalisation — `"UP "` renders
    as `UP` in every UI, so it must not escape the comparison. A carried value
    outside that ordering (`LOCKED`, `NOMINAL`, a raw numeric code) is
    **refused**, not published and not silently replaced by the derived
    verdict: an unrankable label may be *more* degraded than the derivation,
    and quietly emitting the derived verdict over it would launder in the
    other direction. An absent or blank verdict is not an unrankable one — it
    means the message said nothing about clock health, and takes the derived
    verdict;
  - `mavlink_decoded_to_zmeta_system_events()` refuses a TASK_ACK whose
    message carries no acknowledgement verdict rather than reporting
    `RECEIVED` — a commander reads that as the vehicle having taken the task,
    and the v1.0 TASK_ACK state vocabulary offers no "unknown" member to
    degrade into. Presence is tested by carrier key (`state` / `mission_state`
    / `ack`), never by truthiness: `MAV_MISSION_ACCEPTED` and
    `MAV_RESULT_ACCEPTED` are both the integer `0`, so a falsy test would
    destroy precisely the successful acknowledgements and report a false
    cause. A carrier that is present but carries something outside the v1.0
    TASK_ACK vocabulary gets its own, different refusal. Raw MAVLink result
    codes are refused rather than mapped: `0` means ACCEPTED under
    `MISSION_ACK.type` and `COMMAND_ACK.result` but UNKNOWN under
    `MISSION_CURRENT.mission_state`, and the decoded dict does not say which
    enum it came from — the bridge holds the message type, so the bridge maps
    the code. Guessing an acceptance is the one direction that must never be
    guessed;
  - the five negative TASK_ACK verdicts (`REJECTED` / `FAILED` / `CANCELLED`
    / `EXPIRED` / `DUPLICATE_IGNORED`) carry the `metrics.reason_code` the
    v1.0 schema requires on exactly those states: the message's own when it
    carried a member of the schema's 12-value TASK_ACK reason vocabulary,
    else the code that restates the verdict itself (`TASK_REJECTED`,
    `TASK_FAILED`, `TASK_CANCELLED`, `TASK_EXPIRED`, `TASK_DUPLICATE` — the
    same pairing the SAPIENT ingress makes). A restatement, not a diagnosis:
    it adds no cause the message did not carry. A message-carried
    `reason_code` is never silently dropped — an out-of-vocabulary one is
    refused, and one carried under a clean verdict (`RECEIVED` / `ACCEPTED` /
    `EXECUTING` / `COMPLETED`) is refused as self-contradictory, since the
    v1.0 reason vocabulary is causes of non-execution;
  - the decoded LINK_STATUS branch of the same function holds itself to the
    schema shape it emits, instead of leaving the whole advertised message
    family to be refused at the gateway: `latency_ms`, `packet_loss_pct` and
    `throughput_bps` are message-carried and refused when absent (never
    fabricated — same rule as `translate_link_status()`); `link_id` is the
    message's own or the declared `edge-comms-<platform_id>` default (an
    identifier the adapter assigns, not a measurement it invents); a carried
    `state` / `link_state` is normalised onto the v1.0
    `UP`/`DEGRADED`/`DOWN`/`UNKNOWN` vocabulary and refused when
    uninterpretable — never forwarded verbatim — while an absent or blank
    verdict stays the honest `UNKNOWN`; and `reason_code` follows the same
    vocabulary / required-under-`DEGRADED`-`DOWN` / no-cause-under-`UP` rules
    as `translate_link_status()`.

### Heading and attitude frame provenance

ZMeta `payload.heading_deg` is contractually degrees true north (semantics
contract section 6.4). The MAVLink wire format does not guarantee that frame:

- `GLOBAL_POSITION_INT.hdg` is defined only as "vehicle heading (yaw angle)"
  in centidegrees, with no declared true-vs-magnetic reference. On typical
  autopilots it is EKF yaw, which is true-north-referenced only when magnetic
  declination is correctly configured.
- `ATTITUDE.yaw` (retained as `payload.quality.yaw_deg`) carries the same
  ambiguity; it is platform-state context, not a canonical heading.

Because the source does not guarantee the frame, this adapter does not emit
canonical `payload.heading_deg` by default. Known but unasserted MAVLink
headings are preserved as `payload.quality.mavlink_hdg_frame_unknown_deg` so
consumers can audit the native value without confusing it for canonical state.
An unknown heading (`hdg = UINT16_MAX`) is omitted from the payload rather than
fabricated as `0.0`.

Deployments may pass `heading_frame="TRUE_NORTH"` to
`translate_platform_state()` only when upstream configuration guarantees a
true-north heading, such as verified AHRS or correct magnetic-declination
configuration. In that mode the adapter emits canonical `payload.heading_deg`
and records `quality.heading_source` from the provided `heading_source` value
or the default `MAVLINK_GLOBAL_POSITION_INT_TRUE_NORTH`.

## Source

Platform state translation extracted from Z-ISR `edge/edge/zmeta_builder.py`
and `edge/edge/mavlink/bridge.py`.
