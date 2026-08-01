# AIS ingress (Reference)

Decoded AIS position reports into ZMeta `OBSERVATION_EVENT`s. AIS is a
cooperative broadcast on VHF: a vessel transmits its own identity, position and
motion, and a receiver decodes it. Almost nothing here is our measurement, and
that shapes every decision in the adapter.

## Input

A decoded message dict in the shape AIS-catcher's JSON output produces.
AIS-catcher is the common RTL-SDR decoder, so this runs on the same dongle as
the ADS-B adapter. Raw NMEA `!AIVDM` sentences are out of scope: decode first,
with AIS-catcher, `pyais`, `gpsd` or equivalent.

```python
from adapters.ingress.ais.ais_to_zmeta import translate_stream

events = translate_stream(messages, platform_id="ais-node-01",
                          receiver_id="rtlsdr-01")
```

Only position reports are consumed: types 1, 2, 3 (Class A), 18 and 19
(Class B), and 27 (long range). Static and voyage data (5, 24) carry a name and
dimensions but no position, so they produce no event on their own. A decoder
that merges static fields into a position report is welcome to; the merged
fields are carried natively.

## The altitude problem, which is the whole story

Canonical `payload.geo` requires `lat`, `lon` and `alt_m` together (contract
6.8). **A vessel has no altitude.** Not missing, not unreported: a surface
vessel has no meaningful height above the ellipsoid, and AIS has no field for
one.

Substituting zero would be the worst option available. `alt_m` is height above
the WGS-84 ellipsoid, and the geoid departs from the ellipsoid by up to about
100 m, so sea level is not ellipsoid zero anywhere on Earth. Writing `0.0` would
assert a geometric height nobody measured, in a field a consumer may read as
measured.

So **every AIS observation omits canonical geo** and the real horizontal
position is demoted to `ais_lat_deg` and `ais_lon_deg`.

This is doctrine **A1-02**, and this adapter is its independent second
implementation. It is also the sharper instance. For ADS-B, barometric-only
targets are a subset. For AIS it is every vessel, every message, always.

**The measured consequence**, from the colocated test and reproducible in one
command: a schema-valid AIS observation whose identity resolves cleanly
(`mmsi-366123456`) and whose position is exact projects to **zero tracks**
through `adapters/projector/track`, because a track needs canonical geo. Nothing
reaches a COP.

A second consequence follows from the first. The position accuracy AIS declares
is a real, standard-defined statement (better or worse than 10 m), and
`quality.error_ellipse_m` attaches to a canonical geo object that is never
built. The declared accuracy is carried natively and cannot be canonical.

## On `geo_status`

When canonical geo is omitted this sets `quality.geo_status = "UNAVAILABLE"`,
matching the ADS-B adapter.

Read it as the status of the canonical geo object, which is genuinely
unavailable, and not as a claim that the position is unknown, because it is not:
it sits in the native features, exact as broadcast. The contract's vocabulary
(`AVAILABLE`, `UNAVAILABLE`, `ESTIMATED`, `STALE`, `CONFIGURED`) has no token
for "horizontally known, vertically absent". The least-wrong token is used, the
two adapters stay consistent with each other, and the ambiguity is recorded for
the maintainer rather than resolved locally.

## Not-available sentinels

ITU-R M.1371 encodes "not reporting" as explicit field values. Each is refused
rather than carried:

| Field | Sentinel | Carried as |
|---|---|---|
| `lat` / `lon` | 91.0 / 181.0 | no position at all |
| `speed` | 102.3 | omitted |
| `speed` (message 27) | 63 | omitted |
| `course` | 360.0 | omitted |
| `course` (message 27) | 511 | omitted |
| `heading` | 511 | omitted |
| `second` | 60 to 63 | `ais_second_status`, never a second-of-minute |

Carrying them would put a stopped vessel at the north pole on a due-north
heading. Message 27 packs speed and course into smaller fields with their own
not-available encodings, and 63 kt is a real speed in a Class A report, so
those two are checked only for message 27.

Beyond the sentinels, the fields bound what a real report can say: speed 0 to
102.2 kt, course 0 to 359.9 degrees, heading 0 to 359. A decoded value outside
those bounds is corruption, not an AIS claim, and the field is dropped.

## Native features

| Key | Source |
|---|---|
| `ais_mmsi` | the subject; a message without one is refused |
| `ais_message_type` | AIS message type |
| `ais_lat_deg` / `ais_lon_deg` | the broadcast position, demoted |
| `ais_sog_kt` / `ais_cog_deg_true` / `ais_heading_deg_true` | motion, sentinels removed |
| `ais_nav_status_code` | declared navigation status, as a code |
| `ais_shiptype_code` | declared ship type, as a code |
| `ais_position_accuracy_high` | the one-bit accuracy declaration |
| `ais_second_of_minute` / `ais_second_status` | the `second` field, split by meaning |
| `ais_signal_power_db` | receiver-relative power, never `power_dbm` |
| `ais_shipname` / `ais_callsign` | text, `@` padding stripped |
| `ais_channel_a_hz` / `ais_channel_b_hz` | band context |
| `ais_receiver_id` | supplied by the caller |

## What is never inferred

MMSI encodes country and service in its leading digits, `shiptype` is a declared
code, and navigation status is a declared enum. None becomes a ZMeta
classification or identity here. An `OBSERVATION_EVENT` carrying identity or
classification is an authority-boundary violation the kernel refuses, and these
are the vessel's own claims for an inference stage to adjudicate, not facts the
receiver established.

## Modality is `NETWORK`, and it is a judgement

Same reasoning as the ADS-B adapter. Contract 7.4 gives RF a normative minimum
feature set including `power_dbm`, and a decoder reports signal power in
uncalibrated dB relative to its own chain. Emitting that as `power_dbm` is
laundering, so the observation is modelled as the decoded message and power is
carried natively. A deployment with a calibrated receiver could honestly emit
RF; that is a later refinement, not something to fake here.

## Refusals

| Input | Result |
|---|---|
| Not a position report type | no event |
| No MMSI, or an unusable one | no event; there is no subject |
| No usable reception time | no event |
| A present but impossible `rxtime` or `timestamp` | no event; a corrupt time channel is a decoder fault, not a reason to borrow another clock |
| Position sentinels | event without a position; the emitter was still decoded |
| Non-finite number in any field | that field dropped |
| A speed or course the field cannot encode | that field dropped |

Reception time is trusted only when it can be a moment: `rxtime` must parse as
a calendar date, and an epoch `timestamp` below 2000-01-01 is read as some
other quantity that leaked in under that name, not as epoch seconds.

`translate_stream` takes any iterable, a generator included, and raises for a
non-iterable rather than returning an empty list: zero events from a miswired
call must not look identical to zero events from an empty sea. One refused
message never stops the batch.

Refusals are dropped, not patched. The count is the caller's to observe: an
adapter that invents a position to keep its yield up is the failure mode this
whole file exists to avoid.
