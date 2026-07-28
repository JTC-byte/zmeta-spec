# ADS-B ingress adapter

`dump1090` / `readsb` `aircraft.json` → ZMeta `OBSERVATION_EVENT`.

Works with any of the decoders `adsbcot` supports — `readsb`, `dump1090`,
`dump1090-fa`, `dump1090-mutability` — reading the `aircraft.json` snapshot.

```python
from adapters.ingress.adsb.adsb_to_zmeta import translate_snapshot

snapshot = json.load(open("/run/dump1090-fa/aircraft.json"))
events = translate_snapshot(
    snapshot,
    platform_id="adsb-node-01",
    producer="rf-sensor-adsb-01",   # must match producer authority; see AUTHORING.md 7
    receiver_id="rtlsdr-01",
)
```

## Why ADS-B is a good conformance target

It is a **cooperative broadcast** carrying its own declared quality — `nac_p`,
`nac_v`, `sil`, `nic`. Most sensors declare nothing about their own accuracy,
so ADS-B exercises the honesty primitives against data that actually has them,
and it produces the hard cases continuously and for free:

| Real `aircraft.json` case | What this adapter does |
|---|---|
| position + `alt_geom` + `nac_p` | canonical `geo`, error ellipse from the **declared** NACp bound |
| position, `alt_baro` only | **no canonical `geo`** — see open question 2 — lat/lon kept as native features, `geo_status: UNAVAILABLE` |
| Mode S only, no position | a real detection of a real emitter, positionless |
| `nac_p` absent | no error bound invented |
| NaN / out-of-range coordinate | not a position |
| no `hex` | refused entirely — no subject for the observation |

## Field mapping

Canonical, only when honestly derivable:

- `event.ts` ← `now - seen_pos` (position age), else `now - seen`
- `payload.geo` ← `lat`, `lon`, and `alt_geom` **only** (feet → metres)
- `payload.quality.error_ellipse_m` ← `nac_p`, DO-260B containment radius
- `payload.quality.geo_status` ← `UNAVAILABLE` when there is no canonical geo
- `payload.timing_quality` ← degraded fallback unless the deployment supplies
  real clock metadata

Native, explicitly named so nothing reads more into them than the data supports:
`adsb_icao24`, `adsb_callsign`, `adsb_squawk`, `rssi_dbfs`, `adsb_alt_baro_ft`,
`adsb_ground_speed_kt`, `adsb_track_deg_true`, `adsb_baro_rate_fpm`,
`adsb_message_count`, `adsb_seen_s`, `adsb_seen_pos_s`, `adsb_nac_p`,
`adsb_nac_v`, `adsb_sil`, `adsb_nic`, `adsb_downlink_hz`, `adsb_receiver_id`,
and `adsb_lat_deg` / `adsb_lon_deg` when the position could not become canonical.

## Two open questions this adapter raised

Both are **standard-level questions, not adapter bugs**, and both are recorded
in `docs/zmeta_doctrine_review_log.md`. Neither is settled. They are here
because an adapter author meeting the same wall should know it is a known wall.

### 1. Modality is `NETWORK`, and that is a workaround

ADS-B *is* RF. But semantics-contract 7.4 makes `power_dbm` a **required** RF
feature, and `dump1090` reports `rssi` in **dBFS** — relative to the receiver's
full scale, dependent on antenna and gain chain, not convertible to absolute
dBm without a calibration the message never carries.

So an RF-modality ADS-B observation would have to either fabricate `power_dbm`
or refuse every event. This adapter takes neither option: it models the decoded
message as `NETWORK` and carries `rssi_dbfs` under a key that says what it is.

**This is not an ADS-B quirk.** Every SDR-based RF sensor has it. The shipped
`kraken` adapter writes a value its own documentation calls "RSSI dB" straight
into `power_dbm` — not carelessness, but the only alternative the spec leaves.
The gap is that ZMeta has no way to say *what reference a power measurement
uses*, so honest representation is impossible for uncalibrated sensors.

The candidate fix is a declaration, not a new subtype: power declares its
reference the way `bearing.frame` declares `TRUE_NORTH` and
`quality.calibration_state` declares `UNCALIBRATED`. One optional discriminator
covers every SDR; a subtype per sensor family would be a dictionary, not an
alphabet.

### 2. All-or-nothing geo discards good 2-D positions

`payload.geo` requires `alt_m` (contract 6.8). A large share of ADS-B targets
report only barometric altitude, so their perfectly good horizontal fix cannot
become a canonical position.

Also not an ADS-B quirk. **AIS is the sharper case** — a vessel has no
meaningful altitude *ever*, so ZMeta cannot carry an AIS position canonically
at all. Ground radar and most DF systems are 2-D too.

The candidate fix is again a declaration: geo declares its dimensionality,
the way `geo_status` already declares availability.

**Whether either matters is a field question**, not an argument to have here.
It is entirely possible nobody misses the dropped altitudes. That is what the
live test is for.

## Running it against real data

```
python -m pytest adapters/ingress/adsb -q
python tools/validate.py --file your-adsb-events.jsonl --profile H
python tools/check_compat.py your-adsb-events.jsonl --target v1.1.19 --strict
```

`--strict` will report `timing_quality_fallback` for every event unless the
deployment supplies real clock metadata. That is correct and expected for an
uncalibrated receiver — the events are declaring an unsynchronised clock rather
than claiming a synchronisation nobody made.
