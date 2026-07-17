## ZMeta to CoT Egress Adapter

Converts ZMeta `STATE_EVENT` track states into CoT v2.0 XML for TAK
interoperability (ATAK, WinTAK, TAK Server).

The adapter expects a semantically valid ZMeta `STATE_EVENT`. It refuses
non-state inputs and state payloads that still carry raw observation/evidence
fields such as `features`, `raw_features`, `modality`, `data_ref`, or
`data_refs`; those events must be rejected or corrected before projection.

### Features

| Feature | Details |
|---------|---------|
| Error uncertainty | Resolves CE/LE from `geo.error_ellipse_m`; emits `9999999.0` (CoT's unknown-value convention) when the event carries no uncertainty |
| Heading/speed | `<track>` element renders directional arrows on TAK map |
| Precision location | `<precisionlocation>` for MIL-STD-2525 elliptical uncertainty |
| Team coloring | `<__group>` element for ATAK friendly platform team panels |
| Hostile labels | Persistent `<labels_on>` so CE readout is always visible |
| Callsign fallback | Hostile emitters show "RF Emitter" / "Detection" instead of raw track IDs |
| Remarks | Source summary, confidence (whenever the event carries one), and error ellipse details |
| Wall-clock mode | Opt-in replay-display mode (`use_wall_clock: True`) re-stamps CoT timestamps to now; off by default — event time is authoritative |
| Custom icons | Quadcopter icon for drone/sensor platforms (`a-f-A-M-F-Q`) |

### Mapping

| ZMeta field | CoT field | Notes |
|-------------|-----------|-------|
| `payload.track_id` | `uid` | |
| `payload.class` | `type` | Falls back to `a-u-G` |
| `payload.geo.lat/lon/alt_m` | `point lat/lon/hae` | |
| `payload.geo.error_ellipse_m` | `point ce/le` + `precisionlocation` | `semi_major` → `ce`, `semi_minor` → `le`; absent → `9999999.0` (CoT unknown-value convention) |
| `payload.valid_for_ms` | `stale` | `time + valid_for_ms` |
| `payload.heading_deg` | `track course` | Frame-preserving: both are degrees true north (see below) |
| `payload.speed_mps` | `track speed` | |
| `payload.callsign` | `contact callsign` | With hostile fallback |
| `payload.source_summary` | `remarks` | Joined with `;` |
| `confidence` (top level) | `remarks` | Appended whenever present, after any source summary |

### Heading / course frame

CoT `track@course` is degrees true north by convention, and ZMeta
`payload.heading_deg` is contractually degrees true north (semantics contract
section 6.4), so the projection is frame-preserving with no conversion.
The adapter relies on the upstream producer having honored that contract; it
does not (and cannot) re-verify the frame at egress.

Caveat: when `speed_mps` is present but `heading_deg` is absent, the `<track>`
element is still emitted with the placeholder `course="0.0"` because TAK
requires the attribute to render speed. Consumers should not interpret that
placeholder as a real due-north heading; ZMeta events that omit `heading_deg`
carry no heading claim.

### Configuration

Pass a `cot_config` dict to customize behavior:

```python
cot_config = {
    "default_type": "a-u-G",           # Default CoT type
    "default_valid_for_ms": 300000,     # 5 minute stale time
    "default_ce": 9999999.0,           # CE (m) when event has no uncertainty
    "default_le": 9999999.0,           # LE (m) when event has no uncertainty
    "friendly_team_name": "Cyan",      # ATAK team color
    "friendly_team_role": "Team Member",
    "use_wall_clock": False,           # Opt-in replay-display mode (see below)
}
```

**Uncertainty defaults.** `9999999.0` is CoT's own documented unknown-value
convention for `point@ce`/`point@le` — it tells TAK consumers "accuracy
unknown" instead of asserting a precision the event never carried
(semantics contract sections 4.7 / 12.2: never invent precision). Deployments
that have a real, characterized error model for their sensors may override
`default_ce`/`default_le`; leaving the defaults in place is the honest choice
everywhere else.

**Timestamps.** By default CoT `time`/`start` come from the event's `ts` —
event time is authoritative, and replayed or stale data must not render as
live (semantics contract section 9.5). `use_wall_clock: True` is an explicit
replay-display mode for operators who have deliberately selected replay and
want TAK to show fresh markers; it re-stamps the CoT timestamps to the
current time. It is off by default.

### Usage

```python
from adapters.egress.cot.zmeta_to_cot import zmeta_to_cot

state_event = {
    "zmeta_version": "1.1.0",
    "event": {
        "event_id": "019c2b5c-c046-70e1-b6aa-34bf14c8a247",
        "event_type": "STATE_EVENT",
        "event_subtype": "TRACK_STATE",
        "ts": "2026-01-17T14:30:05Z",
    },
    "source": {
        "platform_id": "gateway-01",
        "node_role": "GATEWAY",
        "producer": "fusion-engine",
    },
    "payload": {
        "track_id": "emitter-01",
        "class": "a-h-G",
        "geo": {
            "lat": 43.49,
            "lon": -112.04,
            "alt_m": 1500,
            "error_ellipse_m": {
                "semi_major": 150.0,
                "semi_minor": 80.0,
                "orientation_deg": 45.0,
            },
        },
        "valid_for_ms": 60000,
        "heading_deg": 135.0,
        "speed_mps": 12.5,
    },
    "confidence": 0.82,
    "lineage": {
        "based_on": ["019c2b5c-88f0-7aa1-9b3e-5d2c41f0a9d2"],
    },
}

cot_xml = zmeta_to_cot(state_event)
```

The example is a schema-valid v1.1.0 `STATE_EVENT` (`geo.error_ellipse_m` is
v1.1.0 vocabulary; the locked v1.0 `geo` carries no uncertainty fields, so a
v1.0 event always egresses with the unknown-value CE/LE convention).

### Source

Production logic extracted from Z-ISR `zisr/transport/publisher.py`.
