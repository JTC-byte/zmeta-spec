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
| Position with no geometric altitude | nothing, counted `refused_no_geo` | a state requires lat, lon and alt_m; barometric altitude is not a geometric height |
| No position at all | nothing, counted `refused_no_geo` | Mode S targets without position are common |
| Anything not an `OBSERVATION_EVENT` | nothing, not counted | not this component's input |

Refusals are counted and exposed on `.stats` because an association component
that silently drops its inputs is indistinguishable from one that is not
running.

## Known limit: uncertainty cannot reach the display

Under the locked v1.0 kernel a `STATE_EVENT`'s `geo` is exactly `lat`, `lon` and
`alt_m`, with `additionalProperties: false`. There is nowhere on a v1.0 state to
put positional uncertainty. `adapters/egress/cot` reads `geo.error_ellipse_m`,
which exists only on the v1.1.0 experimental geo.

So a well-characterised accuracy that the ingress adapter genuinely measured,
such as the 30 m ellipse ADS-B derives from `nac_p: 9`, cannot travel to TAK on
a v1.0 track. Every such track renders with CoT's unknown-accuracy sentinel
(`ce="9999999.0"`).

Nothing is overstated, which is the half that matters. The measured value is
simply unsayable at this layer, and that is a question for the maintainer rather
than something to work around here.

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
