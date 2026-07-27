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
renders on ATAK as an ordinary marker at a position that is not a position,
carrying no uncertainty label and nothing an operator can filter on. The
gateway refuses such an event at its outgoing gate before CoT is ever called;
this guard covers callers that project directly, and the gateway buckets the
refusal as a counted, reason-tagged `cot_skipped` record.

The check is scoped by value, not by a list of fields: every canonical field
is walked, so a number that reaches `<remarks>`, an uncertainty key added to
`geo.error_ellipse_m` later, or a `default_valid_for_ms` that would otherwise
raise out of the adapter are all covered without editing a list.
`payload.extensions` is the one deliberate exclusion — it is namespaced vendor
content this adapter never reads and never renders, and refusing the
operator's track because a provenance blob carried a `NaN` would destroy good
canonical data over content CoT does not project.

It refuses (`None`) one further case: a validity window whose `stale`
timestamp is not representable. `payload.valid_for_ms` is
`{"type": "integer", "minimum": 1}` with no upper bound, and `event.ts` is any
RFC3339 instant, so the kernel forwards events whose `time + valid_for_ms` the
`datetime` module cannot express — `10**400` ms, `10**15` ms, and even an
ordinary 300 000 ms stale on `ts="9999-12-31T23:59:59Z"`. Each of those used
to leave the adapter as a raw `OverflowError`. CoT has no unknown-value
convention for `stale` the way it has `9999999.0` for `ce`/`le`, and a CoT
event without `stale` is not a CoT event, so the whole event is refused rather
than published with a substituted default — a fallback to
`default_valid_for_ms` would assert a freshness bound the event never made.

### Features

| Feature | Details |
|---------|---------|
| Error uncertainty | Resolves CE from `geo.error_ellipse_m` `semi_major` (the conservative circular bound); emits `9999999.0` (CoT's unknown-value convention) when the event carries no uncertainty. LE is never derived from the horizontal ellipse — see the mapping table |
| Heading/speed | `<track>` element renders directional arrows on TAK map |
| Precision location | `<precisionlocation>` for MIL-STD-2525 elliptical uncertainty — emitted only when the config asserts `geopointsrc`/`altsrc`; source pedigree is never defaulted to `"GPS"` |
| Team coloring | `<__group>` element for ATAK friendly platform team panels |
| Hostile labels | Persistent `<labels_on>` so CE readout is always visible |
| Callsign fallback | Hostile emitters show "RF Emitter" / "Detection" instead of raw track IDs |
| Remarks | Source summary, confidence (whenever the event carries one), and error ellipse details |
| Wall-clock mode | Opt-in replay-display mode (`use_wall_clock: True`) re-stamps CoT timestamps to now; off by default — event time is authoritative, and an event missing `event.ts` is refused (`None`) outside this mode |
| Custom icons | Quadcopter icon for drone/sensor platforms (`a-f-A-M-F-Q`) |

### Mapping

| ZMeta field | CoT field | Notes |
|-------------|-----------|-------|
| `payload.track_id` | `uid` | |
| `payload.class` | `type` | Falls back to `a-u-G` |
| `payload.geo.lat/lon/alt_m` | `point lat/lon/hae` | Absent `alt_m` → `hae="9999999.0"` (CoT unknown-value convention — never a fabricated 0 m claim); a real `alt_m` of `0.0` passes through as `0.0` |
| `payload.geo.error_ellipse_m` | `point ce` + `precisionlocation` | `semi_major` → `ce` as the **conservative circular bound** (a circle of radius `semi_major` covers the whole ellipse, so `ce` never understates the horizontal error); absent → `9999999.0` (CoT unknown-value convention). `le` is **never** derived from the ellipse: CoT `le` is linear (vertical/HAE) error, the contract's ellipse is purely horizontal (§21.2, orientation from true north), and the event model has no vertical-uncertainty field — so `le` is always `default_le` (`9999999.0` unless the deployment has a real vertical error model). `precisionlocation` is emitted only when a source is asserted (see Configuration) |
| `payload.valid_for_ms` | `stale` | `time + valid_for_ms`; a sum `datetime` cannot represent refuses the event (`None`) rather than substituting the config default |
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
    "default_le": 9999999.0,           # LE (m) — always the emitted le; see below
    "friendly_team_name": "Cyan",      # ATAK team color
    "friendly_team_role": "Team Member",
    "use_wall_clock": False,           # Opt-in replay-display mode (see below)
    "geopointsrc": None,               # Position-source pedigree; None = omit
    "how": None,                       # Event derivation pedigree (e.g. "m-g"); None = omit
    "altsrc": None,                    # Altitude-source pedigree; None = omit
}
```

**Uncertainty defaults.** `9999999.0` is CoT's own documented unknown-value
convention for `point@ce`/`point@le` — it tells TAK consumers "accuracy
unknown" instead of asserting a precision the event never carried
(semantics contract sections 4.7 / 12.2: never invent precision). Deployments
that have a real, characterized error model for their sensors may override
`default_ce`/`default_le`; leaving the defaults in place is the honest choice
everywhere else. Note that `default_le` is *always* the emitted `le`: the
event model carries no vertical-error field, so there is nothing on the event
that may honestly feed it (in particular not the horizontal error ellipse).

**Source provenance.** `geopointsrc`/`altsrc` are the `<precisionlocation>`
pedigree attributes TAK consumers read as "how this position/altitude was
derived". No ZMeta field carries that claim, so the adapter cannot infer it —
the element is emitted only when the operator's config explicitly asserts a
source (and only the asserted attribute is stamped; asserting the position
source says nothing about the altitude source). With neither asserted the
element is omitted entirely and the ellipse projects as the conservative
`point@ce` plus human-readable remarks text. An RF-triangulated fusion
product must never arrive on TAK wearing a GPS badge.

**Timestamps.** By default CoT `time`/`start` come from the event's `ts` —
event time is authoritative, and replayed or stale data must not render as
live (semantics contract section 9.5). An event with no `event.ts` — or a
`ts` that does not parse as an RFC3339 instant, which still passes the schema
gate because jsonschema does not enforce `format: date-time` without an
installed `FormatChecker` — is refused (the adapter returns `None`) rather
than silently stamped with the current time or allowed to escape as a raw
`ValueError` — fabricating freshness for malformed input would launder it.
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
