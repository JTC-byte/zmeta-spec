## ZMeta to CoT Egress Adapter

Converts ZMeta `STATE_EVENT` track states into CoT v2.0 XML for TAK
interoperability (ATAK, WinTAK, TAK Server).

The adapter expects a semantically valid ZMeta `STATE_EVENT`. It refuses
non-state inputs and state payloads that still carry raw observation/evidence
fields such as `features`, `raw_features`, `modality`, `data_ref`, or
`data_refs`; those events must be rejected or corrected before projection.

It also refuses (`None`) any event carrying a non-finite (`NaN`/`inf`) number
in a canonical field, plus any non-finite value in the operator-supplied
`cot_config` and in the `zmeta_to_cot_uncertainty_circle` radius. `lat="nan"`
renders on ATAK as an ordinary marker whose coordinates are not a position,
carrying no uncertainty label and nothing an operator can filter on. The
gateway refuses such an event at its outgoing gate before CoT is ever called;
this guard covers callers that project directly, and the gateway buckets the
refusal as a counted, reason-tagged `cot_skipped` record.

The check is scoped by value, not by a list of fields: every canonical field
is walked, so a number that reaches `<remarks>`, an uncertainty key added to
`geo.error_ellipse_m` later, or a `default_valid_for_ms` that would otherwise
raise out of the adapter are all covered without editing a list.
`payload.extensions` is the one deliberate exclusion. It is namespaced vendor
content this adapter never reads and never renders, and refusing the
operator's track because a provenance blob carried a `NaN` would destroy good
canonical data over content CoT does not project.

It refuses (`None`) one further case: a validity window whose `stale`
timestamp is not representable. `payload.valid_for_ms` is
`{"type": "integer", "minimum": 1}` with no upper bound, and `event.ts` is any
RFC3339 instant, so the kernel forwards events whose `time + valid_for_ms` the
`datetime` module cannot express: `10**400` ms, `10**15` ms, and even an
ordinary 300 000 ms stale on `ts="9999-12-31T23:59:59Z"`. Each of those used
to leave the adapter as a raw `OverflowError`. CoT has no unknown-value
convention for `stale` the way it has `9999999.0` for `ce`/`le`, and `stale` is a
required CoT attribute, so the whole event is refused rather
than published with a substituted default. A fallback to
`default_valid_for_ms` would assert a freshness bound the event never made.

Values are checked as text as well as numbers, because the projection writes
them into XML (2026-10-01). A point value (`lat`, `lon`, `hae`, `ce`, `le`)
must be a finite number, a Decimal, or text that is wholly a finite number such
as `"12.5"`; anything else is refused, so a string from a caller that skipped
schema validation cannot carry quotes or markup into an attribute. An
`error_ellipse_m` member must be a number. A character XML 1.0 forbids (a C0
control other than tab, newline or return, a lone surrogate, U+FFFE or U+FFFF)
is replaced by a space in `remarks`, which is free text, and refuses the event
when it sits in an identity attribute such as the callsign or the uid, the same
rule the `cds` profile applies. As a backstop, an output that does not parse,
or whose root holds anything but a `point` and a `detail`, is refused. A
`default_ce` or `default_le` that is not a finite, non-negative number is a
configuration error under every profile, so the gateway stops at startup
instead of writing it into every track.

### Declared 2-D geo (doctrine A1-02)

`payload.geo.dimensionality: "2D"` (schema/zmeta-event-1.1.0.schema.json
`$defs/geo`) is a real, exact horizontal fix with no geometric vertical to
assert, ever: every AIS vessel, a barometric-only aircraft. Unlike the
JREAP egress sibling, this adapter cannot emit a null altitude for it: CoT
`point@hae` is a required *numeric* attribute, and refusing the TAK event
outright over an honest horizontal-only fix would defeat the
vessel-reaches-the-map purpose doctrine A1-02 was adjudicated for. The
wire value therefore stays `hae="9999999.0"`, the same sentinel the
historical ambiguous absent-altitude case (no `dimensionality` token, no
`alt_m`) has always emitted, and always will: that case's rendered XML is
unchanged by this section, byte for byte.

The sentinel alone cannot tell the two cases apart, so a declared `"2D"` geo
additionally emits a structured `<detail>` marker naming the declared
dimensionality: `<geo_dimensionality value="2D" geo_status="…" />`.
`geo_status` is included only when the event's own
`payload.quality.geo_status` carries one (typically `VERTICAL_UNAVAILABLE`);
a value the event never asserted is an omitted attribute, never a fabricated
token, the same honest-absence rule the ellipse fields above already follow.
The ambiguous case emits no marker at all, so a consumer that reads
`<detail>` can now tell a genuine horizontal-only fix apart from a sensor
that simply failed to report altitude; a consumer that reads only
`point@hae` sees the same wire-compatible sentinel it always has.

A geo that declares `"2D"` yet still carries `alt_m` is the A1-02 coherence
contradiction: two claims that cannot both be true. It is schema-invalid
upstream, so the gateway never hands it to this egress, but a direct
embedder call can, and this adapter refuses it (`None`) rather than silently
picking one claim to believe, the same disposition the JREAP egress sibling
gives the identical contradiction.

| `geo` shape | `point@hae` | `detail` marker | Disposition |
|---|---|---|---|
| `alt_m` present, no `dimensionality` (or `"3D"`) | the real `alt_m` | none | unchanged |
| `dimensionality: "2D"`, `alt_m` absent | `9999999.0` | `<geo_dimensionality value="2D" .../>` | projected |
| no `dimensionality`, `alt_m` absent (ambiguous) | `9999999.0` | none | unchanged, byte-compatible with the pre-existing behavior |
| `dimensionality: "2D"` with `alt_m` present | n/a | n/a | refused (`None`); the A1-02 contradiction |

### Features

| Feature | Details |
|---------|---------|
| Error uncertainty | Resolves CE from `geo.error_ellipse_m` `semi_major` (the conservative circular bound); emits `9999999.0` (CoT's unknown-value convention) when the event carries no uncertainty. LE is never derived from the horizontal ellipse; see the mapping table |
| Heading/speed | `<track>` element renders directional arrows on TAK map |
| Precision location | `<precisionlocation>` for MIL-STD-2525 elliptical uncertainty, emitted only when the config asserts `geopointsrc`/`altsrc`; source pedigree is never defaulted to `"GPS"` |
| Team coloring | `<__group>` element for ATAK friendly platform team panels |
| Hostile labels | Persistent `<labels_on>` so CE readout is always visible |
| Callsign fallback | Hostile emitters show "RF Emitter" / "Detection" instead of raw track IDs |
| Remarks | The class as a quoted label when it is not a CoT type, then source summary, confidence (whenever the event carries one), and error ellipse details |
| Wall-clock mode | Opt-in replay-display mode (`use_wall_clock: True`) re-stamps CoT timestamps to now; off by default, since event time is authoritative, and an event missing `event.ts` is refused (`None`) outside this mode |
| Custom icons | Quadcopter icon for drone/sensor platforms (`a-f-A-M-F-Q`) |
| Declared 2-D geo | `<geo_dimensionality>` detail marker distinguishes a declared horizontal-only fix from the ambiguous absent-altitude case (both still emit `hae="9999999.0"`, CoT `hae` being required and numeric); a `"2D"` geo carrying `alt_m` refuses (doctrine A1-02, see below) |
| Profiles | `standard` (the default, everything above) and `cds`, the shape one partner's cross-domain guard passed on 2026-09-29: four detail children, `how` asserted, one fixed-template remarks line, no http(s) link, a stale capped by a window and never later than the event's claim, a maximum age, no replay-display mode. See "Profiles" |

### Mapping

| ZMeta field | CoT field | Notes |
|-------------|-----------|-------|
| `payload.track_id` | `uid` | |
| `payload.class` | `type` | Used as the type only when it parses as a CoT atom type (`a`, an affiliation letter, a battle dimension, then function-code segments, as in `a-h-G-U-C-I`). Any other class is an entity label, such as a detector's `car`: the event goes out as `a-u-G`, which claims no affiliation, and the label is prepended to `remarks` as one quoted token, `class="<label>"`. An absent or null class uses `default_type`; an empty or whitespace-only class goes out as `a-u-G` with no label. See "Class and type" |
| `payload.geo.lat/lon/alt_m` | `point lat/lon/hae` | Absent `alt_m` → `hae="9999999.0"` (CoT unknown-value convention, never a fabricated 0 m claim); a real `alt_m` of `0.0` passes through as `0.0`. A declared `geo.dimensionality: "2D"` also renders `hae="9999999.0"` (CoT `hae` is a required numeric attribute with no "not applicable" convention), paired with the `geo_dimensionality` detail marker below so the sentinel is not the whole story; see "Declared 2-D geo" |
| `payload.geo.dimensionality` | `detail geo_dimensionality` | Emitted only for a declared `"2D"` geo, as `<geo_dimensionality value="2D" geo_status="…" />`; `geo_status` rides along only when `payload.quality.geo_status` is present. Absent `dimensionality` (the historical ambiguous case) emits no marker at all; see "Declared 2-D geo" |
| `payload.geo.error_ellipse_m` | `point ce` + `precisionlocation` + `remarks` | `semi_major` → `ce` as the **conservative circular bound** (a circle of radius `semi_major` covers the whole ellipse, so `ce` never understates the horizontal error); absent → `9999999.0` (CoT unknown-value convention). `le` is **never** derived from the ellipse: CoT `le` is linear (vertical/HAE) error, the contract's ellipse is purely horizontal (§21.2, orientation from true north), and the event model has no vertical-uncertainty field, so `le` is always `default_le` (`9999999.0` unless the deployment has a real vertical error model). `precisionlocation` is emitted only when a source is asserted (see Configuration). A `semi_minor` or `orientation_deg` the dict never asserted is an omitted fragment/attribute in `remarks`/`precisionlocation`, never a fabricated `0`; a dict with no `semi_major` under that name (missing, or a wrong-spelled key) has no ellipse this adapter can honestly render at all, so nothing is emitted for it, the same way `ce` falls back to `default_ce` rather than reading a `0` out of it |
| `payload.valid_for_ms` | `stale` | `time + valid_for_ms`; a sum `datetime` cannot represent refuses the event (`None`) rather than substituting the config default |
| `payload.heading_deg` | `track course` | Frame-preserving: both are degrees true north (see below) |
| `payload.speed_mps` | `track speed` | |
| `payload.callsign` | `contact callsign` | With hostile fallback |
| `payload.source_summary` | `remarks` | Joined with `;` |
| `confidence` (top level) | `remarks` | Appended whenever present, after any source summary |

### Class and type

`payload.class` is a free string in both schema versions: `TrackStatePayload`
declares it only as `{"type": "string"}`. The CoT ingress adapter stores the
CoT type there, another producer may store an entity label, and both are
conforming. This adapter therefore uses the class as the CoT type only when it
parses as a CoT atom type. The check is grammatical rather than a lookup in a
type table: a well-formed type is accepted whether or not a table knows it,
which means a grammatical type that denotes nothing still passes, and a label
never becomes a type. A CoT round trip keeps an atom type. Any other CoT type,
such as a marker type, comes back as `a-u-G` with the original type in
`remarks`.

A class that fails the check goes out as `a-u-G`, so it can never place a
hostile or friendly marker on a map. Its label is prepended to `remarks` as one
quoted token, `class="<label>"`, with internal quotes and backslashes escaped,
so a label such as `car; confidence=0.99` cannot pass for a remarks fragment of
its own. Characters that are not printable become spaces, and a label longer
than 64 characters is cut with a trailing `...`. An empty or whitespace-only
class goes out as `a-u-G` with no label. A class that does parse carries its
own affiliation through unchanged, including the hostile callsign fallback and
the friendly team coloring above.

`default_type` applies only to a track whose class is absent or null, never to
a class that is a label. A configured value that does not parse as a CoT atom
type falls back to `a-u-G`.

### Profiles

`cot_config["profile"]` selects one of two projections. `standard`, the
default, is the output described everywhere else in this README; it is
unchanged by the other profile's existence, and a test freezes its bytes.
`cds` is the shape one partner's cross-domain guard passed into a higher
enclave on 2026-09-29, recorded here so a deployment can select the validated
shape by name instead of rebuilding it.

What passed, and how much that proves: one deployment, one partner's guard,
one day (n=1). The deployment reported that the partner saw its tracks on the
partner's federation hub on 2026-09-24 under an earlier shape the deployment
had named strict, and that the guard did not pass them. Two changes went live
together at 20:01 UTC on 2026-09-29, after which the deployment reported that
the guard passed everything: a stale time of arrival plus 120 s on every
source, and no link anywhere in the event. Which of the two the guard needed
is not known, and neither was tested alone, so the profile carries both under
one name and a deployment cannot lose either by accident. Nothing here claims
that another guard, or the same guard on another day, passes this shape.

The profile is a transform applied after the standard projection, so it is
exactly "the standard output plus these changes", which is how it was
validated. Every refusal of the standard projection is inherited, including
an unrepresentable `valid_for_ms`, because the standard string is built
first.

| Element | `standard` | `cds` |
|---|---|---|
| `detail` children | `contact`, and any of `labels_on`, `remarks`, `track`, `precisionlocation`, `__group`, `usericon`, `geo_dimensionality` as the event and config call for | `contact`, `track`, `remarks`, `precisionlocation` only; every other child is removed |
| `type` | the class when it parses as a CoT type, else `a-u-G` | the same; an event whose type asserts an affiliation (`a-h-`, `a-f-`, and the rest) is refused rather than retyped, see below |
| `how` | omitted unless the config asserts it | required, the config's `how` token, a deployment claim |
| `remarks` | the class label, source summary, confidence and ellipse text | one line from a fixed template, see below; producer free text does not cross |
| `stale` | event `ts` + `valid_for_ms` | the earlier of event `ts` + `valid_for_ms` and the projection time + `stale_window_s` (default 120); an event whose own validity has lapsed at projection is refused, or sent with that past stale under `lapsed_validity: send_stale` |
| age | any | an event whose `ts` is more than `max_age_s` (default: the stale window, which it may not exceed) before or after the projection time is refused |
| replay-display mode | `use_wall_clock` re-stamps `time` to now | refused at config time: a re-stamped event would pass the age rule with any age |
| links | as the event carries them | no http(s) link anywhere; one that survives outside `remarks`, for example in a callsign, refuses the event |
| `point` attributes | Python's float text, exponent form for a value near zero | plain decimal notation, the form the public CoT event schema accepts; a value that is not a number refuses |
| `uid`, `time`, `start`, `contact`, `track`, `precisionlocation` | | same values, serialized by `ElementTree` |

The `remarks` line is built from a template, in this order, joined by `; `:
`track via ZMeta`; `affiliation not asserted`; `confidence=<value>` when the
event carries a finite number in [0, 1] there; `2-D fix, altitude not
asserted` for a declared 2-D geo; `producer <name>`; `class "<label>"` when
the class is a label rather than a CoT type; then the config's
`attribution`. The markers up to the 2-D words are never cut, and they are
bounded, so the line has room for the rest. The producer name and the
attribution are cut to the room left under 200 characters, in that order,
so a long producer name loses its tail before an honesty marker loses a
letter; a class label that does not fit whole is left out rather than cut
through its closing quote. In every part an http(s) link is removed, a
character that is not printable becomes a space, `;` becomes `,` so no part
can read as a marker the event never made, and whitespace collapses to one
line. A confidence that is not a finite number in range is not sent. The
event's `source_summary` and the ellipse text do not cross under this
profile; the ellipse still reaches `point@ce` and, with `geopointsrc` or
`altsrc` configured, `precisionlocation`.

Four of those rows change what a consumer can read, and each is recorded in
the doctrine pressure log (cycle F3):

- **The 2-D declaration travels as words.** The structured
  `<geo_dimensionality>` marker does not pass the guard, so a declared 2-D geo
  says `2-D fix, altitude not asserted` in `remarks` instead. That keeps
  doctrine A1-02's honesty in the only channel the guard passes. Design gate
  5 (structure over free text) is not met at this boundary: no structured
  child carrying the declaration passes the guard.
- **`stale` is never later than the producer's claim; the window is a cap.**
  Contract section 14 lists `payload.valid_for_ms` as freshness/stale
  behavior a CoT projection must preserve, and section 4.2 lets a
  projection lower a validity but never raise it. Since 2026-10-01 (doctrine
  F3-03) `stale` is the earlier of the event's own `ts` + `valid_for_ms`
  (the deployment's `default_valid_for_ms` when the event carries none) and
  the projection time plus the window. The validated packets carried the
  window whatever the event claimed; an earlier stale cannot breach a
  guard's stale ceiling, but it is a change from the shape that passed, so a
  deployment confirms it with the far side before relying on it. An event
  whose own validity has lapsed at projection is refused, because sending it
  under the window would tell the far side it is live. A deployment whose
  far-side display shows a past-stale packet as stale, rather than dropping
  it, may set `lapsed_validity` to `send_stale`, and the packet then leaves
  with that past stale (contract section 13.3). A producer whose
  `valid_for_ms` is shorter than the hub-and-guard latency will have every
  track refused; the fix lies in the producer's claim or the far-side
  display policy. The maximum age still refuses a report older than
  the window, and replay-display mode is still refused because a re-stamped
  event would defeat both rules. The window does not announce itself in
  `remarks`: the stale attribute carries it, and the validated template is
  unchanged.
- **`how` is asserted by the deployment.** The event model carries no
  position-source claim, so the adapter never fills it in. A deployment
  asserts the token it can stand behind: `m-f` for fused tracks, `m-r` for
  relayed reports, and so on.
- **Producer free text does not cross.** Under this profile `remarks` is the
  adapter's template, so no producer text reaches a consumer on the far
  side, and nothing outside the template's slots can be said.

An asserted affiliation is refused rather than retyped. The validated packets
never asserted one. A retype to the unknown branch would hide a claim the
event made, and section 18.2 says a redaction must not "Hide that redaction
occurred when the consumer needs that fact"; passing it through would assert
a claim the far side may act on, and nothing in the contract decides whether
an affiliation may cross a guard, the release profiles of section 18.1 that
would govern it being future. Section 17 adds that an affiliation must not
travel without its confidence, lineage, evidence type and trust context,
which this profile's shape cannot carry. No deployment option passes one
(doctrine F3-05, decided 2026-10-01); the route is a release profile under
roadmap candidate `coalition-release-export`. The refusal is the adapter's
usual `None`, which the gateway counts as a `cot_skipped` record under the
reason `AFFILIATION_ASSERTED`; a lapsed validity is counted as
`VALIDITY_LAPSED`. A deployment watches the first count, because a hostile
track absent from the far side is itself safety-relevant.

The export audit metadata contract section 18.3 lists (release label,
exporting authority, guard or policy identifier, redaction reason, removed
field categories, export timestamp, destination domain or partner class,
contract or policy hash) is not in the packet: the guard's format carries no
place for it, and it remains future vocabulary (the roadmap's
`coalition-release-export` candidate, registry names `RELEASE_LABEL`,
`REDACTION_PROFILE`, `EXPORT_AUDIT`). A deployment that needs the audit keeps
it beside the packet.

`validate_cot_config(cot_config)` returns the profile name or raises
`ValueError` for a config the adapter cannot run. An unknown profile is
refused under any config. For a `cds` config it also refuses a key the
adapter does not read (so a misspelled `stale_window_s` cannot leave the
default in force), a missing or malformed `how` token, `use_wall_clock`, a
window or age that is not a positive number of seconds within thirty days,
an age larger than the window, a `lapsed_validity` other than `refuse` or
`send_stale`, and an attribution that is not a string, that
is not printable text, or that carries a link of any scheme. The gateway
calls it when it reads `cot.config` and exits with the message, so a
deployment learns at startup rather than as a refusal of every track.
`zmeta_to_cot_uncertainty_circle` returns `None` under the profile, since a
`<circle>` child is outside the shape and the radius already reaches the
packet as `point@ce`. The `cds` output is serialized by `ElementTree` after
the transform, so its text escaping and whitespace differ from the standard
string. The tests validate the `cds` output against MITRE's public
`Event-PUBLIC.xsd` when `COT_EVENT_XSD` names a copy and `lxml` is installed;
the repository vendors neither, and a structural test that needs neither
runs always.

```python
cot_config = {
    "profile": "cds",
    "how": "m-f",                       # required: the deployment's own claim
    "stale_window_s": 120,              # stale is capped at projection time + window; 120 is the value that passed
    "lapsed_validity": "refuse",        # or "send_stale" if the far side shows past-stale packets as stale
    "max_age_s": 120,                   # older or newer than this at projection: refused (default: the window)
    "attribution": "Data from an open feed, attribution in words",  # optional; printable words, no link
}
```

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
    "default_type": "a-u-G",           # Type for a track with no class
    "default_valid_for_ms": 300000,     # 5 minute stale time
    "default_ce": 9999999.0,           # CE (m) when event has no uncertainty
    "default_le": 9999999.0,           # LE (m); always the emitted le, see below
    "friendly_team_name": "Cyan",      # ATAK team color
    "friendly_team_role": "Team Member",
    "use_wall_clock": False,           # Opt-in replay-display mode (see below)
    "geopointsrc": None,               # Position-source pedigree; None = omit
    "how": None,                       # Event derivation pedigree (e.g. "m-g"); None = omit
    "altsrc": None,                    # Altitude-source pedigree; None = omit
    "profile": "standard",             # or "cds"; see Profiles
}
```

**Uncertainty defaults.** `9999999.0` is CoT's own documented unknown-value
convention for `point@ce`/`point@le`. It tells TAK consumers "accuracy
unknown" instead of asserting a precision the event never carried
(semantics contract sections 4.7 / 12.2: never invent precision). Deployments
that have a real, characterized error model for their sensors may override
`default_ce`/`default_le`; leaving the defaults in place is the honest choice
everywhere else. Note that `default_le` is *always* the emitted `le`: the
event model carries no vertical-error field, so there is nothing on the event
that may honestly feed it (in particular not the horizontal error ellipse).

**Source provenance.** `geopointsrc`/`altsrc` are the `<precisionlocation>`
pedigree attributes TAK consumers read as "how this position/altitude was
derived". No ZMeta field carries that claim, so the adapter cannot infer it.
The element is emitted only when the operator's config explicitly asserts a
source (and only the asserted attribute is stamped; asserting the position
source says nothing about the altitude source). With neither asserted the
element is omitted entirely and the ellipse projects as the conservative
`point@ce` plus human-readable remarks text. An RF-triangulated fusion
product must never reach TAK carrying a GPS pedigree.

**Timestamps.** By default CoT `time`/`start` come from the event's `ts`, because
event time is authoritative, and replayed or stale data must not render as
live (semantics contract section 9.5). An event with no `event.ts`, or a
`ts` that does not parse as an RFC3339 instant, is refused (the adapter
returns `None`) rather than silently stamped with the current time or
allowed to escape as a raw `ValueError`. That gap is real on the locked v1.0
schema branch, where `utcDateTime` enforces only a trailing `Z` and
`format: date-time` is advisory without an RFC 3339 checker. Installing a
`FormatChecker` does not close it: `jsonschema` registers no `date-time`
checker unless the optional `rfc3339-validator` package is present, that
package is declared in no requirements file here, and an unregistered format
silently conforms. The v1.1.0 branch tightens the pattern to structural
calendar shape instead (year/month/day/hour/minute/second ranges, doctrine
X1-01), so most malformed shapes no longer reach this adapter gate-clean on
that branch; neither branch is a full calendar validator, so a structurally
well-formed but calendrically impossible value such as
`"2026-02-30T00:00:00Z"` still passes both. Fabricating freshness for
malformed input would launder it.
`use_wall_clock: True` is an explicit replay-display mode for operators who
have deliberately selected replay and want TAK to show fresh markers; it
re-stamps the CoT timestamps to the current time (including for events with
no `ts`, since now-stamping is that mode's documented purpose). It is off by
default.

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
