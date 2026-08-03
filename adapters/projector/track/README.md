# Broadcast-identity track projector

Turns observations whose subjects announce their own identity into tracks a COP
can draw. ZMeta in, ZMeta out.

## The gap it closes

`adapters/egress/cot` projects `STATE_EVENT` only. An ingress adapter emits
`OBSERVATION_EVENT`. A sensor wired straight through a gateway therefore puts
valid ZMeta on the wire and nothing on the map, and the shipped example corpus
happens to contain a `STATE_EVENT`, so a pre-event rehearsal passes and the real
sensor then shows nothing.

For an RF bearing or an EO detection, closing that gap means a tracker: identity
has to be inferred from the observations themselves. For ADS-B, AIS, and
anything else where the subject broadcasts a stable identifier, it does not. The
association key arrives with the data. What remains is lifecycle, and that is
what this does.

Measured 2026-07-30 on a synthetic six-aircraft snapshot: five observations in,
two tracks out, three refused, two CoT events on the wire where the same chain
without a projector produced zero.

## Use

```python
from adapters.projector.track.track_projector import TrackProjector

projector = TrackProjector(platform_id="adsb-node-01", confidence=0.9)

for observation in stream:             # ZMeta OBSERVATION_EVENTs
    for event in projector.observe(observation):
        publish(event)                 # FUSION_EVENT then STATE_EVENT
```

Emit order matters on the wire: the fusion cites the observation and the state
cites the fusion, so parents must precede children or a receiving gateway
reports unresolved lineage.

## Why fusion rather than external promotion

The policy offers two routes to a `STATE_EVENT` and they mean different things.

External promotion (`policy/producer-authority.yaml`, `external_state_promotion`)
is for importing a track another system already computed, which is what
`adapters/ingress/cot` and `adapters/ingress/jreap` do. Its lineage cites the
ZMeta ancestry carried through that foreign projection.

Fusion is for a track you associated yourself. An aircraft broadcasts
instantaneous position and identity. It does not decide that successive
broadcasts are one object, or when that object is stale. That work happens here,
even though the association key was handed over rather than inferred.

The lineage rules agree. `policy/lineage.yaml` allows a `STATE_EVENT` to cite
only `FUSION_EVENT` or `STATE_EVENT` parents, so a state citing an observation
is refused with `LINEAGE_PARENT_TYPE_INVALID`. Going straight from observation
to state would mean citing a parent that does not exist, and no adapter here
invents lineage. `FusionPayload.members` is `minItems: 1`, so a single-member
association is schema-legal and no invention is needed.

## Confidence is asserted by the deployment

There is no default and the constructor refuses without one.

The kernel requires `confidence` on both emitted event types. A cooperative
broadcast supplies none: ADS-B carries `nac_p` and `sil`, which are accuracy and
integrity, and the ingress adapter already projects those into an error ellipse.
Neither is a probability that the claim is true.

So the number has to come from somewhere, and the only honest source is the
operator deciding how far this deployment trusts decoded broadcasts from this
receiver. Inventing one here would send a fabricated value downstream looking
exactly like a measured one. Deriving it from `sil` was considered and rejected:
that mapping is a modelling decision nobody has adjudicated, and inventing it
inside an adapter is how a private dialect starts.

`stability` on the fusion event is a declared count-based proxy, documented at
`_stability`, not a kinematic measurement.

## What it refuses

| Input | Result | Why |
|---|---|---|
| No identity field | nothing, counted `refused_no_identity` | an unnamed subject is not a track |
| Position with no geometric altitude and no `"2D"` token | nothing, counted `refused_no_geo` | a state requires lat, lon and alt_m, unless the geo is explicitly declared 2-D; barometric altitude alone is not a geometric height and is not a declaration either |
| No position at all | nothing, counted `refused_no_geo` | Mode S targets without position are common |
| Anything not an `OBSERVATION_EVENT` | nothing, not counted | not this component's input |

Refusals are counted and exposed on `.stats` because an association component
that silently drops its inputs is indistinguishable from one that is not
running.

## Two-dimensional tracks (doctrine A1-02)

A surface vessel has no altitude to report, not a missing one, and a
barometric-only aircraft has a real horizontal fix with nothing to assert
vertically. `schema/zmeta-event-1.1.0.schema.json` names that shape:
`geo.dimensionality: "2D"` on the observation, which prohibits `alt_m`
outright rather than defaulting it. Absent, `dimensionality` means 3D, so an
observation that is merely missing `alt_m` with no explicit token still hits
the historical refusal above; only the explicit token changes the outcome.

An observation carrying a declared 2-D position is projected. The
`FUSION_EVENT` and `STATE_EVENT` it produces both carry:

- `geo`: `lat`, `lon`, `dimensionality: "2D"`, and no `alt_m`;
- `quality: {"geo_status": "VERTICAL_UNAVAILABLE"}`;
- `zmeta_version: "1.1.0"`, because that vocabulary is not valid under the
  locked v1.0 kernel.

A 3-D observation, or one with no dimensionality token at all, produces
exactly the v1.0-shaped output this projector always emitted: no `geo` on the
fusion event, no `quality` block on either event, `zmeta_version: "1.0"`. The
conditional stamp means a deployment that never sees a 2-D source is
unaffected byte-for-byte.

`.stats["projected_2d"]` counts the 2-D subset of `.stats["projected"]`, so a
deployment can watch the 2-D share of its traffic without recomputing it from
events. It is not counted in `refused_no_geo`: a declared 2-D position is
accepted, not refused.

**Mixed tracks, an explicit modelling choice.** A track can accumulate members
of both kinds over time, for example an AIS-shaped source today and a future
sensor contributing a 3-D fix to the same identity tomorrow. Each call to
`observe()` builds its `FUSION_EVENT`/`STATE_EVENT` pair from the member that
triggered that call, and only proceeds when that member itself carries a
projectable position, so the state's dimensionality is always the
dimensionality of its most recent position-bearing member: a track that just
took a 2-D observation projects a 2-D state, and the next 3-D observation on
the same identity projects a 3-D state again, with no memory of the geo shape
in between.

The alternative considered and rejected was carrying the last known `alt_m`
forward across a subsequent 2-D observation, so a track never "loses" its
vertical. That reads as one fresh, single-epoch measurement when it is
actually a current horizontal fix stapled to a stale vertical one, of unstated
age, which is exactly the kind of laundering this standard exists to refuse.
This projector accepts a track's vertical availability flickering with its
most recent source over carrying a numeric altitude past the observation that
supported it. Revisit if a deployment finds the flicker more disruptive than
the honesty is worth; nothing here forecloses a future `estimated_state`-based
fusion that reconciles both explicitly and says so.

## Known limit: uncertainty on a v1.0 track

Under the locked v1.0 kernel a `STATE_EVENT`'s `geo` is exactly `lat`, `lon` and
`alt_m`, with `additionalProperties: false`. A v1.0 track therefore carries no
positional uncertainty, and since `adapters/egress/cot` reads
`geo.error_ellipse_m`, every such track renders with CoT's unknown-accuracy
sentinel (`ce="9999999.0"`). The 30 m ellipse ADS-B derives from `nac_p: 9` does
not reach TAK.

This is a version limit, not a model limit. On the v1.1.0 branch
`geo.error_ellipse_m` is a registered, approved, schema-implemented extension
allowed on `STATE_EVENT`, carrying semi-major, semi-minor, orientation and an
optional probability level (`1_SIGMA`, `CEP`, `CE_90`, `CE_95`). The open
question is which schema version a deployment runs. See doctrine log SIM1-05.

Nothing is overstated either way, which is the half that matters.

## Exporting these tracks to SAPIENT

`adapters/egress/sapient` refuses a track whose `track_id` is not a ULID unless
the caller supplies an `object_map`. That refusal is deliberate: minting a fresh
SAPIENT identity per report would destroy track continuity on the SAPIENT side,
so object identity is caller-owned deployment state.

This projector's identifiers are broadcast-shaped (`icao24-a1b2c3`,
`mmsi-366123456`), which is the point of them, so a deployment exporting to
SAPIENT owns and supplies the mapping:

```python
zmeta_state_to_sapient_detection(
    state, node_id=NODE_UUID,
    object_map={"icao24-a1b2c3": "01JQ0000000000000000000001"})
```

Without it the export returns `None` and no detection is produced.

## Bounds

Track count and members per track are both capped, and the oldest track is
evicted first so a flood of new identities cannot displace an active subject
ahead of a dormant one. Sender-controlled cardinality must not grow memory
without bound, the same rule the gateway's command-evidence index follows.

## Lifecycle

`expire(now_ms)` drops tracks past their TTL and returns what it dropped.
Expiry is deliberately silent on the wire: `valid_for_ms` already tells a
consumer when a track stops being current, and a separate end-of-life event
would be a second way to say the same thing. The full pattern, including
command-grade criteria, is in `docs/zmeta_track_lifecycle_pattern.md`.
