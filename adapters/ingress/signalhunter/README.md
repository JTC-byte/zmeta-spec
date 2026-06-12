## SignalHunter Ingress Adapter

Translates SignalHunter PSD (Power Spectral Density) spectrum analyzer
captures into ZMeta RF `OBSERVATION_EVENT` (LOB) events.

### How it works

The SignalHunter is a handheld USB spectrum analyzer connected to an Android
device. It has no antenna array and cannot produce DOA bearings directly.
Instead, this adapter uses **power-gradient analysis**: by comparing signal
strength between consecutive PSD sweeps taken at different GPS positions,
it infers bearing toward the emitter.

- If power increased, the operator moved closer; bearing = travel direction.
- If power decreased, the operator moved away; bearing = reverse direction.
- Delta < 0.5 dB is discarded as noise.

These synthetic LOBs carry large angular error (default 75 deg) but converge
through WLS fusion when many observations accumulate.

Because the bearing is the geodesic travel direction (or its reverse) between
two GPS fixes, it is degrees true north by construction — no heading
compensation is involved. Events therefore assert frame provenance per
semantics contract section 6.4: `quality.bearing_frame = "TRUE_NORTH"` and
`quality.heading_source = "GPS_COURSE"`.

### Input format

Binary `.bin` capture files with:
- 1060-byte header: start/end freq, frame count, GPS lat/lon, location name
- N frames of 822 float32 PSD bins (3288 bytes each)
- GPS-only trailing frames (repeating lat/lon pairs for position updates)

### Output

`OBSERVATION_EVENT` with `event_subtype: RF`, `modality: RF`.

### Key features

| Feature | Details |
|---------|---------|
| Peak detection | Local-maximum with prominence filter and noise floor |
| Peak persistence | Only report peaks seen in N of last M sweeps |
| Gradient bearing | Travel-direction or reverse based on power delta |
| GPS interpolation | Header position updated from trailing GPS frames |

### Usage

```python
from pathlib import Path
from adapters.ingress.signalhunter.signalhunter_to_zmeta import translate_bin_file

raw = Path("capture.bin").read_bytes()
events = translate_bin_file(
    raw,
    platform_id="foot-patrol-01",
    noise_floor_dbm=-95.0,
    bearing_error_deg=75.0,
)
```

### Source

Extracted from Z-ISR `edge/edge/sensors/signalhunter_rf.py`.
