## ZMeta to ASTERIX CAT062 Egress Adapter (Reference)

Overview: see `adapters/README.md`.

ASTERIX is EUROCONTROL's binary format for surveillance data exchange, and
Category 062 carries system tracks: the output of a surveillance data
processing system to its users. This adapter encodes one ZMeta
`STATE_EVENT`/`TRACK_STATE` as one CAT062 record under edition 1.21
(EUROCONTROL-SPEC-0149-9, 05/06/2025), and wraps records in a CAT062 data
block. Section and page numbers below cite that edition; its text is not
reproduced here.

Input: ZMeta `STATE_EVENT`/`TRACK_STATE`.
Output: one CAT062 record (FSPEC and items) per event, and a data block (CAT,
LEN, records) from `cat062_data_block`.

Status: Reference, on the same basis as the TAK Protocol Version 1 adapter.
The encoding was checked byte for byte against the BSD-3-Clause `libasterix`
package (0.37.0, `Cat_062_1_21`) for the two known-answer records and three
further records, and `libasterix` parses the adapter's output back to the
same bytes. A scratch run on 2026-11-14 took 809 STATE events of a
downstream producer's recorded run and 1,680 STATE events the track
projector made from 1,680 live ADS-B observations. Every one of them
carries unsynchronized timing, so with the default every one was refused for
it; with `allow_degraded_timing=True`, all 809 and all 1,680 were encoded and
parsed back.
No CAT062 consumer (a surveillance data processing system, a display or a
recorder) has been driven with the bytes from this repository, and the
adapter opens no connection. The adapter is not among the required surfaces
of any conformance class.

### Usage

```python
from adapters.egress.asterix.zmeta_to_asterix_cat062 import (
    validate_asterix_config, zmeta_state_to_asterix_cat062, cat062_data_block,
)

config = {"sac": 25, "sic": 7, "monosensor": False, "tentative": False, "simulated": False}
validate_asterix_config(config)                   # at startup: raises ValueError for a configuration it cannot run

track_numbers = {"<track_id>": 1234}              # the caller's map; the adapter never mints a number
refusal = {}
record = zmeta_state_to_asterix_cat062(event, config, track_numbers=track_numbers, refusal=refusal)
if record is None:
    print(refusal["reason"])                      # one of the reasons below
block = cat062_data_block([record])               # CAT 62, LEN, the records

# Only where the deployment tells its receivers the time basis of the feed (see "Timing"):
record = zmeta_state_to_asterix_cat062(event, config, track_numbers=track_numbers, allow_degraded_timing=True)
```

The adapter returns `None` for every refusal and never raises on an event.
A caller that passes a dict as `refusal` reads the reason under `"reason"`;
it is written only by the refusal that fired. `cat062_data_block` raises
`ValueError` for no records, a record that is not non-empty bytes, or a block
longer than the 65,535 octets LEN can state; a sender splits its records
across blocks.

### The configuration

Every item whose every value is a claim the event does not make is declared
by the deployment. No key has a default, and an unknown key is an error.

| Key | Item | Meaning |
| --- | --- | --- |
| `sac`, `sic` | I062/010 | the sender's System Area Code and System Identification Code, 0 to 255 each; required |
| `monosensor` | I062/080 MON | `true` writes "monosensor track", `false` "multisensor track"; required |
| `tentative` | I062/080 CNF | `true` writes "tentative track", `false` "confirmed track"; required |
| `simulated` | none | required; `true` is refused (below) |
| `service_id` | I062/015 | 0 to 255, written only when declared |

`track_numbers`, the map of `track_id` to I062/040's number (0 to 65,535), is
deployment state, as the SAPIENT adapter's `object_map` is. A track the map
does not name is refused. ZMeta never reuses a `track_id` (contract 13.1),
while a 16-bit number space is recycled by every tracker, so when the map
releases a number is the deployment's decision.

`export_use` (default `"COALITION_EXPORT"`) is the use label this export path
consumes under, as in the SAPIENT adapter; the risk gate below reads it.

### The items

The UAP is §5.3, Table 1 (pp. 131 and 132). Items go in FRN order, and the
FSPEC has seven item bits per octet with FX set on every octet but the last.

| FRN | Item | Written | From | Layout and LSB | Section, page |
| --- | --- | --- | --- | --- | --- |
| 1 | I062/010 Data Source Identifier | always (mandatory) | `sac`, `sic` | two octets | 5.2.1, p. 9 |
| 3 | I062/015 Service Identification | when declared | `service_id` | one octet | 5.2.2, p. 9 |
| 4 | I062/070 Time Of Track Information | always (mandatory) | `event.ts` | three octets, 1/128 s since UTC midnight, floored | 5.2.5, p. 11 |
| 5 | I062/105 Calculated Position In WGS-84 | always | `geo.lat`, `geo.lon` | two 32-bit two's complement values, 180/2^25 degrees, nearest | 5.2.8, p. 24 |
| 7 | I062/185 Calculated Track Velocity (Cartesian) | when the event carries both `heading_deg` and `speed_mps` | course and speed | Vx east, Vy north, 16-bit two's complement each, 0.25 m/s, nearest | 5.2.14, p. 39; 4.3.2, p. 6 |
| 12 | I062/040 Track Number | always (mandatory) | `track_numbers[track_id]` | two octets | 5.2.3, p. 10 |
| 13 | I062/080 Track Status | always (mandatory) | `monosensor`, `tentative` | the first octet alone | 5.2.6, pp. 12 and 13 |
| 18 | I062/130 Calculated Track Geometric Altitude | when the geo is 3-D | `geo.alt_m` | 16-bit two's complement, 6.25 ft (1.905 m), nearest | 5.2.11, p. 36 |
| 27 | I062/500 Estimated Accuracies | when the ellipse is `1_SIGMA` and the latitude is not a pole | `geo.error_ellipse_m` | subfield APW alone | 5.2.26, pp. 123 and 126 |

**Time.** `event.ts` is a STATE's validity time (contract 5.1), and the edition
defines I062/070 as the time of the track state vector. The time is floored,
so the item never reads later than the state's time. The timestamp parse is
the CoT egress adapter's own (`_parse_utc`), so the egress adapters read
`event.ts` the same way; a timestamp that does not parse to an instant with an
offset is refused.

**Position.** The latitude range is -90 to 90 degrees inclusive, and the
longitude range stops short of +180 (p. 24). ZMeta allows a longitude of +180
(contract 6.1), so a longitude that quantizes to +180 is written as -180, the
same meridian.

**Velocity.** The edition puts the y-axis at geographical north at the target
(p. 39) and the x-axis east (§4.3.2), so Vx = speed × sin(course) and Vy =
speed × cos(course), with the course over ground in degrees true north
(contract 6.4). A component whose nearest count falls outside the item's
range, -8,192 to 8,191.75 m/s, refuses the event.

**Altitude.** I062/130 is the height above the WGS-84 ellipsoid (p. 36), the
datum of `alt_m` (contract 6.2). A declared 2-D geo writes no altitude item.
An altitude whose nearest count falls outside the item's range, -1,500 ft to
150,000 ft (-457.2 m to 45,720 m), refuses the event. I062/135 and I062/136
are barometric, and ZMeta carries no barometric height, so they are never
written.

**Track status.** I062/080's first octet is mandatory, and each of its
subfields MON, MRH and CNF has two values, each a claim. The adapter writes:

- MON and CNF as the deployment declares them. The event states neither how
  many sensors fed the track nor whether it is confirmed, and nothing is
  inferred from `confidence`: a deployment that wants low-confidence tracks
  marked tentative sets its own rule before the call.
- SPI 0, the edition's default value.
- MRH 1, geometric altitude more reliable: ZMeta's only canonical height is
  geometric. On a declared 2-D track no altitude item follows, and the bit
  still reads geometric altitude as more reliable, although such a source may
  have had only a barometric height (contract 21.8).
- SRC 000, no source: the event does not state how `alt_m` was obtained.
- FX 0: no extent follows. Every extent holds a subfield whose every value is
  a claim the event cannot support (KOS and SIM in the first; AMA in the
  second; in the third, the technology-age flags, whose value 0 states that
  the technology was used wherever the receiving system supports it, by the
  notes on p. 17; EMS in the fourth; MLAT in the fifth; M5I in the sixth),
  and a later extent cannot be written without the earlier ones.

**Simulation.** The SIM bit is in the first extent. With no extent, a receiver
reads a track as actual, and contract 9.5 forbids making replayed data
indistinguishable from live data. The caller therefore states `simulated` on
every call, and `true` is refused: marking it needs the first extent, whose
KOS subfield the event cannot fill. Writing the first extent is booked for a
later branch.

**Accuracy.** The edition defines every accuracy in I062/500 as a standard
deviation (pp. 125 to 128), so only an ellipse whose `probability` is
`1_SIGMA` is written. The record carries the WGS-84 position and no Cartesian
one, so the adapter writes APW, the accuracy of the WGS-84 position in its own
frame (p. 126), and not APC and COV, which describe a position in the
system's Cartesian plane, defined from a reference point the adapter does not
have (§4.3.2). With semi-major a, semi-minor b and orientation θ from true
north, the north and east standard deviations are the ellipse's exact
marginals:

- σn = sqrt(a² cos²θ + b² sin²θ)
- σe = sqrt(a² sin²θ + b² cos²θ)

They are converted to degrees with the WGS-84 radii of curvature at the
target's latitude (the meridional radius for σn, the prime vertical radius
times the cosine of the latitude for σe), and each is rounded up to the next
LSB, so neither axis's deviation is stated smaller than the source's. APW has
no cross term, so a receiver reads an ellipse aligned with north and east.
Along an oblique major axis that reads up to √2 smaller than the source's
deviation in that direction: an ellipse of 30 m by 10 m at 45 degrees reads
as 22.4 m on each axis, where the source's deviation along 45 degrees is
30 m. The loss register names it. A deviation
beyond the item saturates at its maximum, which the edition reads as that
value or above. At a latitude of exactly 90 degrees north or south the
longitude deviation is undefined, and no accuracy is written.

### The risk gate

A CAT062 record has no carrier for a self-label, and contract 3.3 says that
soft acceptance must not make risky data look clean. The adapter therefore
exports an event only when it carries no risk record
(`payload.extensions.risk_adjudication`, as `tools/filter_risk.py` reads
it), or when every record is an `IGNORED` decision with no use restriction on
`export_use`. Every other decision is refused, each with its own reason, and
a container or record the gate cannot read is refused too. A deployment whose
events carry timing or other risk labels will see them refused here. The
SAPIENT projection carries such labels as `object_info` self-labels.

### Timing

CAT062 edition 1.21 has no item for the quality of the time source. I062/070
is mandatory and states the time of the track as UTC (§5.2.5), so a record
claims a time basis that an event with an undisciplined clock does not
claim. The adapter therefore refuses an event whose timing is not locked.
Locked means `payload.timing_quality` is a mapping whose `sync_state` is
exactly `LOCKED`. Every other case is refused, with its own reason:
`HOLDOVER`, `UNSYNCED`, an absent `timing_quality`, and a malformed one (not
a mapping, or a `sync_state` outside the schema's three tokens). The adapter
reads no `est_error_ms`: a timing threshold is deployment policy, and reaches
this adapter through the risk gate.

`allow_degraded_timing=True` exports such an event. Only the boolean `True`
allows it; any other value that is not a boolean refuses the call, so the
string `"false"` never reads as true. With the allowance on, the record's time
of track information reads as an ordinary time, with no notice that the
source clock was unsynchronized, in holdover or undeclared. The deployment
that sets it is the party telling its receivers so, for example in the
interface agreement for the feed's SAC/SIC. The allowance never opens the
risk gate: an event that carries a timing risk record is refused for risk
whatever the allowance says.

A producer whose clock is disciplined says so in `timing_quality`
(`adapters/AUTHORING.md`, rule 5: degraded timing stays visible), and its
events then need no allowance.

### Refusals

| Reason | When |
| --- | --- |
| `CAT062_NOT_TRACK_STATE` | the input is not a `STATE_EVENT`/`TRACK_STATE` with an event block and a payload |
| `CAT062_CONFIG_INVALID` | a declaration missing, of the wrong type or out of range; an unknown key; an `export_use` that is not a label; an `allow_degraded_timing` that is not a boolean |
| `CAT062_SIMULATED_UNSUPPORTED` | `simulated` is `true` |
| `CAT062_RISK_WARN_ACCEPT`, `CAT062_RISK_DEGRADED_ACCEPT`, `CAT062_RISK_QUARANTINE_ACCEPT`, `CAT062_RISK_REJECTED` | a risk record with that decision |
| `CAT062_RISK_UNKNOWN_DECISION` | a risk record with any other decision text, or none |
| `CAT062_RISK_USE_RESTRICTED` | an `IGNORED` record whose uses prohibit, or do not grant, `export_use` |
| `CAT062_RISK_UNREADABLE` | extensions, records or use labels in a shape the gate cannot read |
| `CAT062_TIMING_HOLDOVER`, `CAT062_TIMING_UNSYNCED` | `timing_quality.sync_state` is that token, and degraded timing is not allowed |
| `CAT062_TIMING_ABSENT` | no `timing_quality`, and degraded timing is not allowed |
| `CAT062_TIMING_MALFORMED` | a `timing_quality` that is not a mapping, or a `sync_state` outside the schema's three tokens, and degraded timing is not allowed |
| `CAT062_TIME_UNPARSEABLE` | `event.ts` missing, or not an instant with an offset |
| `CAT062_TRACK_UNMAPPED` | `track_id` missing, or not in the caller's map |
| `CAT062_TRACK_NUMBER_INVALID` | the mapped number is not an integer from 0 to 65,535 |
| `CAT062_POSITION_INVALID` | geo missing, or a latitude or longitude missing, not a finite number, or out of range |
| `CAT062_ALTITUDE_INVALID` | a declared 2-D geo with `alt_m`, a 3-D geo without a finite `alt_m`, or an unknown dimensionality |
| `CAT062_ALTITUDE_OUT_OF_RANGE` | `alt_m` beyond I062/130's range |
| `CAT062_VELOCITY_INVALID` | course and speed both present, and either not a finite number or out of its range |
| `CAT062_VELOCITY_OUT_OF_RANGE` | a velocity component beyond I062/185's range |
| `CAT062_ACCURACY_INVALID` | an ellipse that is not an object, or a `1_SIGMA` ellipse with a member missing, not a finite number, or out of range |

When several conditions hold, the first in this order is reported; among
risk records, the most severe.

### Loss register

What the record does not carry, as `ASTERIX_EGRESS_LOSS_NOTES` in the module
keeps it. ZMeta remains the source of truth, and a re-import of a record is
never equal to the event (contract 4.5.1).

| Concern | What happens |
| --- | --- |
| date | I062/070 counts from the last UTC midnight; a receiver dates the record by its own clock |
| time resolution | `event.ts` is floored to 1/128 s (7.8125 ms) |
| event identity | `event.event_id` has no item; a record traces to its event only through track number and time |
| source identity | the source block has no item; I062/010 names the sender the deployment declares |
| confidence | no item; CNF is the deployment's statement and is not derived from it |
| lineage | `lineage.based_on` and `transform` have no item |
| timing quality | `payload.timing_quality` has no item, and a locked claim does not export either. An event whose timing is not locked is refused unless degraded timing is allowed; with the allowance, the record reads like one from a disciplined clock |
| validity | `payload.valid_for_ms` has no item. The encoder has no clock and encodes a state whose validity has ended like any other, so the sending deployment must stop sending a track when its validity ends; the receiver ages a track by I062/070 under its own rules |
| class | no item: I062/300 is a fixed table of airport vehicle types, and I062/380's emitter category is derived from the aircraft |
| source summary, provenance, quality, extensions | no item; a declared 2-D position shows only as the absence of I062/130 |
| risk adjudication | no item carries a self-label, so adjudicated events are refused (the gate above) rather than exported clean |
| geo uncertainty | APW carries the north and east standard deviations, each rounded up; the orientation and the cross-correlation are lost, so along an oblique major axis a receiver reads up to √2 less than the source's deviation; an ellipse with another probability, or none, writes no accuracy; none at a pole |
| altitude source | SRC is 000, no source |
| height reliability | MRH is always 1; on a 2-D track it still reads geometric altitude as more reliable, although such a source may have had only a barometric height |
| track status | MON and CNF are the deployment's statements |
| lifecycle | no extent is written, so the first and last messages for a track (TSB, TSE) and coasting (CST) are not signalled |
| simulation | SIM is not written, so a receiver reads every track as actual; `simulated` true is refused |
| course or speed alone | I062/185 needs both |
| callsign | no item: the edition says I062/245 shall not be used (p. 44), I062/380 subfield #2 states a downlink from the aircraft, and I062/390 subfield #2 a flight plan correlation |
| Cartesian position | I062/100 is not written: the adapter has no system reference point or projection, so a receiver that reads only the Cartesian position finds none |

### Tests

`test_asterix_cat062_egress.py` holds two known-answer records computed by
hand from the edition's layouts and LSBs in exact arithmetic, the FSPEC of
each item set, a test for each rule and each refusal, and a check that the
module imports only the standard library and its CoT sibling. A cross-check
against `libasterix` runs when the environment variable `ASTERIX_SITE` names
a directory holding the library's `asterix` package; it runs the library in a
separate `python -I` process, because this package's import name under pytest
would shadow the library's, and skips when the variable is absent. The
repository vendors no copy, and the adapter does not import it.

```bash
python -m pytest -q adapters/egress/asterix
ASTERIX_SITE=/path/to/libasterix-site python -m pytest -q adapters/egress/asterix
```

### Not in this adapter

Encoding ADS-B observations as target reports is a later branch, as is
I062/080's first extent. The adapter writes no I062/100, I062/135,
I062/136, I062/200, I062/210, I062/220, I062/245, I062/270, I062/290,
I062/295, I062/300, I062/340, I062/380, I062/390, I062/510, Mode codes, the
Reserved Expansion Field or the Special Purpose field: the event has no
source for any of them, and carrying ZMeta members in RE or SP would make a
private dialect of CAT062.
