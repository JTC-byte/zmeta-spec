## ZMeta to CoT Egress Adapter

Converts ZMeta `STATE_EVENT` track states into CoT v2.0 XML for TAK
interoperability (ATAK, WinTAK, TAK Server).

### Features

| Feature | Details |
|---------|---------|
| Error uncertainty | Resolves CE/LE from `ce_display_m`, `error_ellipse_m`, legacy `ce`/`le`, or config defaults |
| Heading/speed | `<track>` element renders directional arrows on TAK map |
| Precision location | `<precisionlocation>` for MIL-STD-2525 elliptical uncertainty |
| Team coloring | `<__group>` element for ATAK friendly platform team panels |
| Hostile labels | Persistent `<labels_on>` so CE readout is always visible |
| Callsign fallback | Hostile emitters show "RF Emitter" / "Detection" instead of raw track IDs |
| Remarks | Source summary, confidence, and error ellipse details |
| Wall-clock mode | Uses current time for CoT timestamps so TAK shows fresh markers during historical replay |
| Custom icons | Quadcopter icon for drone/sensor platforms (`a-f-A-M-F-Q`) |

### Mapping

| ZMeta field | CoT field | Notes |
|-------------|-----------|-------|
| `payload.track_id` | `uid` | |
| `payload.class` | `type` | Falls back to `a-u-G` |
| `payload.geo.lat/lon/alt_m` | `point lat/lon/hae` | |
| `payload.geo.error_ellipse_m` | `point ce/le` + `precisionlocation` | |
| `payload.geo.ce_display_m` | `point ce` | Fusion-engine computed |
| `payload.valid_for_ms` | `stale` | `time + valid_for_ms` |
| `payload.heading_deg` | `track course` | |
| `payload.speed_mps` | `track speed` | |
| `payload.callsign` | `contact callsign` | With hostile fallback |
| `payload.source_summary` | `remarks` | Joined with `;` |
| `event.confidence` | `remarks` | Appended if no source_summary |

### Configuration

Pass a `cot_config` dict to customize behavior:

```python
cot_config = {
    "default_type": "a-u-G",           # Default CoT type
    "default_valid_for_ms": 300000,     # 5 minute stale time
    "default_ce": 15.0,                # Default circular error (m)
    "default_le": 10.0,                # Default linear error (m)
    "friendly_team_name": "Cyan",      # ATAK team color
    "friendly_team_role": "Team Member",
    "use_wall_clock": True,            # Fresh timestamps for replay
}
```

### Usage

```python
from adapters.egress.cot.zmeta_to_cot import zmeta_to_cot

state_event = {
    "zmeta_version": "1.0",
    "event": {"event_id": "...", "event_type": "STATE_EVENT", "ts": "..."},
    "payload": {
        "track_id": "emitter-01",
        "class": "a-h-G",
        "geo": {"lat": 43.49, "lon": -112.04, "alt_m": 1500,
                "error_ellipse_m": {"semi_major": 150, "semi_minor": 80, "orientation_deg": 45}},
        "valid_for_ms": 60000,
        "heading_deg": 135.0,
        "speed_mps": 12.5,
    },
    "confidence": 0.82,
}

cot_xml = zmeta_to_cot(state_event)
```

### Source

Production logic extracted from Z-ISR `zisr/transport/publisher.py`.
