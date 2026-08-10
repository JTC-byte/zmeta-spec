# ADS-B ingress adapter

`dump1090` / `readsb` `aircraft.json` → ZMeta `OBSERVATION_EVENT`.

Works with any of the decoders `adsbcot` supports (`readsb`, `dump1090`,
`dump1090-fa`, `dump1090-mutability`), reading the `aircraft.json` snapshot.

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

ADS-B is a cooperative broadcast that carries its own declared quality:
`nac_p`, `nac_v`, `sil`, `nic`. Most sensors declare nothing about their own
accuracy, so ADS-B exercises the honesty primitives against data that has
them. It also produces the hard cases continuously and for free:

| Real `aircraft.json` case | What this adapter does |
|---|---|
| position + `alt_geom` + `nac_p` | canonical 3-D `geo`, error ellipse from the declared NACp bound |
| position, `alt_baro` only | canonical 2-D `geo` (`dimensionality: "2D"`, no `alt_m`), `geo_status: VERTICAL_UNAVAILABLE` |
| position, `alt_geom` outside the plausibility band (roughly -450 m to 20000 m) | canonical 2-D `geo`; the raw `alt_geom` value kept as a native feature; `geo_status: VERTICAL_UNAVAILABLE` |
| Mode S only, no position | a real detection of a real emitter, positionless |
| `nac_p` absent | no error bound invented |
| NaN / out-of-range coordinate | not a position, no canonical `geo` at all |
| snapshot clock (`now`) below 2000-01-01 | refused entirely; not read as a moment |
| no `hex` | refused entirely; no subject for the observation |

### Geometric altitude plausibility

`alt_geom` is WGS84 and is the only field that may become canonical `alt_m`,
but a present value is not automatically a usable one. A sentinel or a
corrupted decode (dump1090 has been observed to report `alt_geom` as `-9999`)
converts to a geometric height of -3047.7 m, a depth no aircraft occupies.
This adapter rejects `alt_geom` outside a plausibility band of roughly -450 m
(the Dead Sea shore, the lowest point on Earth's land surface, with margin)
to 20000 m (above every civil airliner and every known military fixed-wing
envelope, the U-2 and SR-71 included). A value outside that band is treated
the same way a missing `alt_geom` is (doctrine A1-02): the horizontal fix
still gets its canonical home, declared `dimensionality: "2D"` with no
`alt_m`, and `geo_status: VERTICAL_UNAVAILABLE`. The raw altitude also
survives, as `adsb_alt_geom_ft`, so the corrupted reading is visible rather
than silently dropped.

An out-of-range coordinate (for example `lat: 95.0`) is a different case: the
position itself is not real, so there is no canonical `geo` at all, and
nothing is preserved natively either. `_position()`'s bounds check is the one
place that decides "is this a position", and both the 3-D and 2-D branches of
`_geo` share it.

## Field mapping

Canonical, only when honestly derivable:

- `event.ts` ← `now - seen_pos` (position age), else `now - seen`
- `payload.geo` ← `lat`, `lon` always; `alt_geom` (feet → metres) when usable.
  When `alt_geom` is absent or implausible, `payload.geo` is still emitted,
  declared `dimensionality: "2D"` with no `alt_m` (doctrine A1-02), rather
  than omitted.
- `payload.geo.error_ellipse_m` ← `nac_p`, DO-260B containment radius,
  spelled `semi_major`/`semi_minor`/`orientation_deg` to match the formal
  contract shape (schema `$defs/error_ellipse`). Attaches whenever canonical
  `geo` exists, 2-D or 3-D, since NACp is a horizontal bound and is
  meaningful either way; it never attaches to a positionless detection.
- `payload.quality.geo_status` ← `UNAVAILABLE` when there is no canonical
  geo at all, `VERTICAL_UNAVAILABLE` when canonical geo is present but
  declared 2-D
- `payload.timing_quality` ← degraded fallback unless the deployment supplies
  real clock metadata

### Conditional `zmeta_version`

The locked v1.0 `geo` definition is `additionalProperties: false` with only
`lat`/`lon`/`alt_m`; it has no room for `error_ellipse_m` or
`dimensionality`. An entry whose `nac_p` yields a usable containment radius,
or whose horizontal fix has no usable `alt_geom`, therefore stamps
`zmeta_version: "1.1.0"` instead of the adapter's usual `"1.0"`, because that
is the schema branch that defines those fields. An entry with a full 3-D
position and no usable NACp bound keeps the `"1.0"` stamp unchanged, and its
output is otherwise byte-for-byte identical to what this adapter has always
produced: the promotion adds nothing to the branch that never populates
either 1.1.0-only field.

The v1.1.0 `NETWORK` observation payload also requires a `features.protocol`
string that the locked v1.0 payload does not. This adapter supplies
`"ADS-B"` there, and only on the 1.1.0-stamped branch, so the field never
leaks onto a v1.0 event either.

Native, explicitly named so nothing reads more into them than the data supports:
`adsb_icao24`, `adsb_callsign`, `adsb_squawk`, `rssi_dbfs`, `adsb_alt_baro_ft`,
`adsb_ground_speed_kt`, `adsb_track_deg_true`, `adsb_baro_rate_fpm`,
`adsb_message_count`, `adsb_seen_s`, `adsb_seen_pos_s`, `adsb_nac_p`,
`adsb_nac_v`, `adsb_sil`, `adsb_nic`, `adsb_downlink_hz`, `adsb_receiver_id`,
and `adsb_alt_geom_ft` when `alt_geom` was present but outside the
plausibility band above.

## Three open questions this adapter raised

All three are standard-level questions rather than adapter bugs, and all three
are recorded in `docs/zmeta_doctrine_review_log.md` as cycle A1. Two are still
open; the second is now closed for this adapter. They are listed here so that
an adapter author meeting the same wall knows it is a known one.

### 1. Modality is `NETWORK`, and that is a workaround

ADS-B is RF. Semantics-contract 7.4 makes `power_dbm` a required RF feature,
and `dump1090` reports `rssi` in dBFS, which is relative to the receiver's full
scale, dependent on antenna and gain chain, and not convertible to absolute dBm
without a calibration the message never carries.

An RF-modality ADS-B observation would therefore have to either fabricate
`power_dbm` or refuse every event. This adapter takes neither option. It models
the decoded message as `NETWORK` and carries `rssi_dbfs` under a key that says
what the value is.

The gap is not specific to ADS-B. Every SDR-based RF sensor has it. The shipped
`kraken` adapter writes a value its own documentation calls "RSSI dB" straight
into `power_dbm`, because the spec leaves no alternative. ZMeta has no way to
state what reference a power measurement uses, which makes honest
representation impossible for an uncalibrated sensor.

The candidate fix is a declaration rather than a new subtype: power declares
its reference the way `bearing.frame` declares `TRUE_NORTH` and
`quality.calibration_state` declares `UNCALIBRATED`. One optional discriminator
covers every SDR. A subtype per sensor family would turn the vocabulary into a
dictionary rather than an alphabet.

**The experimental split is running as of 2026-08-09.** The discriminator
exists on the v1.1.0 branch as `features.power_reference` (`DBM_ABSOLUTE`,
`DBFS`, or `DB_RELATIVE`; registry entry POWER_REFERENCE, experimental,
maintainer-directed). Passing `rf_power_reference=True` to
`translate_aircraft` or `translate_snapshot` emits the RF form for entries
that carry `rssi`: modality `RF`, the full contract 7.4 minimum feature
set, `power_dbm` holding the dBFS value with `power_reference: "DBFS"`
declared beside it, stamped `zmeta_version: 1.1.0`. Entries without `rssi`
keep the NETWORK form, and the default output is unchanged. The point of
the flag is the experiment cycle A1 approved: the same capture emitted both
ways, with downstream consumers deciding whether the declared form earns
promotion. NETWORK remains the default until that evidence arrives.

### 2. All-or-nothing geo discarded good 2-D positions -- closed for this adapter

`payload.geo` used to require `alt_m` unconditionally (contract 6.8). A large
share of ADS-B targets report only barometric altitude, so their usable
horizontal fix could not become a canonical position and was demoted to
native features instead.

The candidate fix recorded here was a declaration: geo declares its
dimensionality, the way `geo_status` already declares availability. That
landed as `geo.dimensionality` in `schema/zmeta-event-1.1.0.schema.json`
(doctrine A1-02), and this adapter now uses it: a barometric-only or
implausible-`alt_geom` entry gets canonical `geo` declared
`dimensionality: "2D"` with `geo_status: VERTICAL_UNAVAILABLE`, instead of
the old full demotion. See "Geometric altitude plausibility" above.

This was not specific to ADS-B, and closing it here did not close it only
here. AIS is the clearer case: a vessel never has a meaningful altitude, so
an AIS position could not be canonical at all under the old all-or-nothing
rule. AIS was in fact adopted by this same workstream, as doctrine A1-02's
independent second implementation: see `adapters/ingress/ais/README.md`,
which documents every AIS observation with a usable position now getting
canonical `geo` declared `dimensionality: "2D"` with `geo_status:
VERTICAL_UNAVAILABLE`, the identical mechanism this adapter uses. Ground
radar and most DF systems remain 2-D-shaped and unchanged; adopting
`dimensionality` there is still a question for their own workstreams.

### 3. Translation provenance cannot be recorded canonically

`lineage` requires `based_on` with at least one real parent event id, and
`transform` lives inside it. An original observation of a broadcast has no
ZMeta parent, so this adapter cannot record that it translated
`dump1090 aircraft.json`, which is exactly what adapters do. The harness
fixtures therefore set `require_lineage_transform: false`.

This one is expressible as a native feature, so it is a smaller gap than the
two above. It is listed because an adapter author hits it on their first
harness run and should know it is a known wall rather than a mistake in their
fixture.

Whether the remaining two matter is a field question. It is possible that
nobody misses calibrated RF power or canonical translation lineage.
Answering that is what the live test is for.

## Running it against real data

```
python -m pytest adapters/ingress/adsb -q
python tools/validate.py --file your-adsb-events.jsonl --profile H
python tools/check_compat.py your-adsb-events.jsonl --target v1.1.21 --strict
```

`--strict` will report `timing_quality_fallback` for every event unless the
deployment supplies real clock metadata. That is correct and expected for an
uncalibrated receiver: the events declare an unsynchronised clock rather than
claiming a synchronisation nobody made.
