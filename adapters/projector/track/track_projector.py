"""Associate broadcast-identity observations into tracks, and project their state.

A ZMeta-to-ZMeta component. It consumes OBSERVATION_EVENTs and emits the
FUSION_EVENT and STATE_EVENT pair that a track needs to exist, so a source whose
subjects announce their own identity reaches a COP without anyone writing a
tracker.

WHY THIS EXISTS. CoT projects STATE_EVENT only, and an ingress adapter emits
OBSERVATION_EVENT, so a sensor wired straight to a gateway puts ZMeta on the
wire and nothing on the map. For an RF bearing or an EO detection that gap is a
real tracker's worth of work: identity has to be inferred. For ADS-B, AIS and
anything else where the subject broadcasts a stable identifier, it does not.
The association key is handed to you, and the only work left is lifecycle.

WHY FUSION AND NOT EXTERNAL PROMOTION. The policy offers two routes to a
STATE_EVENT, and the honest one here is fusion:

  - external promotion (policy/producer-authority.yaml external_state_promotion)
    is for importing a track another system already computed, as
    adapters/ingress/cot and .../jreap do. Its lineage cites the ZMeta ancestry
    carried through that foreign projection.
  - fusion is for a track YOU associated. An aircraft broadcasts instantaneous
    position and identity. It does not compute a track, decide that successive
    broadcasts are one object, or decide when that object goes stale. That is
    this component's work, even though the association key was given to it.

The constraint agrees with the semantics. `policy/lineage.yaml` allows a
STATE_EVENT to cite only FUSION_EVENT or STATE_EVENT parents, so a STATE citing
an observation is refused with LINEAGE_PARENT_TYPE_INVALID. Reaching a track
from an observation without a fusion step would mean citing a parent id that
does not exist, and inventing lineage is the one thing every adapter here
refuses to do. `FusionPayload.members` is `minItems: 1`, so a single-member
association is schema-legal and needs no such invention.

WHAT IT REFUSES, ALWAYS. No identity means no track: an observation whose
identity field is absent is not guessed at. No canonical geo means no track: a
STATE_EVENT requires lat, lon and alt_m together, so a subject with a position
but no geometric altitude produces nothing here rather than a track at a
fabricated height. Both refusals are counted and reported, because an
association component that silently drops its inputs is indistinguishable from
one that is not running.

KNOWN LIMIT, and it is a version limit rather than a model limit. Under the
locked v1.0 kernel a STATE_EVENT's `geo` is exactly lat, lon and alt_m with
`additionalProperties: false`, so a v1.0 track carries no positional
uncertainty and `adapters/egress/cot`, which reads `geo.error_ellipse_m`,
renders every one of them with CoT's unknown-accuracy sentinel. An accuracy the
ingress adapter genuinely measured, such as the ellipse ADS-B derives from
`nac_p`, does not reach the display.

The v1.1.0 branch already solves this. `geo.error_ellipse_m` is a registered,
approved, schema-implemented extension allowed on STATE_EVENT, carrying
semi-major, semi-minor, orientation and an optional probability level. The open
question is which schema version a deployment runs, not whether ZMeta can say
it. See doctrine log SIM1-05.

Nothing here overstates accuracy either way, which is the half that matters.

SAPIENT EXPORT NEEDS AN OBJECT MAP. `adapters/egress/sapient` refuses a track
whose `track_id` is not a ULID unless the caller supplies `object_map`, because
minting a SAPIENT identity per report would shred track continuity on the
SAPIENT side. This projector's ids are broadcast-shaped (`icao24-a1b2c3`), so a
deployment exporting to SAPIENT must own and supply that mapping.
"""

from __future__ import annotations

import copy
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from zmeta_uuid import uuid7  # noqa: E402

ADAPTER_VERSION = "1.0.0"

# Identity sources, in priority order. The key becomes the track_id prefix, so
# a track is legible as "which broadcast scheme named this" without parsing.
# Deployments extend this rather than editing the logic: the promotion bar for
# any semantic change is independent implementations, not one adapter's needs.
DEFAULT_IDENTITY_PATHS = (
    ("icao24", ("payload", "features", "adsb_icao24")),
    ("mmsi", ("payload", "features", "ais_mmsi")),
)

DEFAULT_VALID_FOR_MS = 30000
DEFAULT_TRACK_TTL_MS = 120000
# Sender-controlled cardinality must not grow this component's memory without
# bound, the same rule the gateway's evidence index follows.
DEFAULT_MAX_TRACKS = 4096
DEFAULT_MAX_MEMBERS = 32
# Observations at which the count-based stability proxy reaches 1.0. See
# _stability: this is a declared heuristic, not a kinematic measurement.
DEFAULT_STABILITY_FULL_COUNT = 5


def _dig(event, path):
    node = event
    for key in path:
        if not isinstance(node, dict):
            return None
        node = node.get(key)
    return node


def _epoch_ms(ts):
    """Epoch milliseconds from a ZMeta timestamp, or None if it is not one.

    None rather than an exception, and None means the track is never expired by
    TTL. A timestamp this cannot read is a reason to keep a track and let
    valid_for_ms speak, not a reason to drop it on a parse failure. The kernel
    accepts any `ts` ending in Z, so unreadable values are reachable in practice
    (doctrine log X1-01).
    """
    if not isinstance(ts, str):
        return None
    try:
        parsed = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return int(parsed.timestamp() * 1000)


def _canonical_geo(payload):
    """lat, lon and alt_m together, or nothing.

    A STATE_EVENT requires all three. A subject reporting position with only a
    barometric altitude has no geometric height, and substituting one would put
    a track at an altitude nobody measured.
    """
    geo = payload.get("geo")
    if not isinstance(geo, dict):
        return None
    lat, lon, alt = geo.get("lat"), geo.get("lon"), geo.get("alt_m")
    if lat is None or lon is None or alt is None:
        return None
    return {"lat": lat, "lon": lon, "alt_m": alt}


class TrackRecord:
    __slots__ = ("track_id", "members", "count", "last_ts", "last_event_ts")

    def __init__(self, track_id):
        self.track_id = track_id
        self.members = []
        self.count = 0
        self.last_ts = None
        self.last_event_ts = None


class TrackProjector:
    """Associates observations by broadcast identity and projects track state.

    Not thread-safe. One instance per stream.
    """

    def __init__(
        self,
        *,
        platform_id,
        confidence,
        producer="fusion-track-projector",
        node_role="GATEWAY",
        identity_paths=DEFAULT_IDENTITY_PATHS,
        valid_for_ms=DEFAULT_VALID_FOR_MS,
        track_ttl_ms=DEFAULT_TRACK_TTL_MS,
        max_tracks=DEFAULT_MAX_TRACKS,
        max_members=DEFAULT_MAX_MEMBERS,
        stability_full_count=DEFAULT_STABILITY_FULL_COUNT,
    ):
        self.platform_id = platform_id
        # A DEPLOYMENT ASSERTION, not a measurement, and required for that
        # reason. The kernel requires `confidence` on FUSION_EVENT and
        # STATE_EVENT. A cooperative broadcast has none to give: ADS-B carries
        # nac_p and sil, which are accuracy and integrity, already projected by
        # the ingress adapter into an error ellipse. Neither is a probability
        # that the claim is true.
        #
        # So the value has to come from somewhere, and the only honest source is
        # the operator who decides how far this deployment trusts decoded
        # broadcasts from this receiver. There is deliberately no default:
        # a number invented here would travel downstream indistinguishable from
        # a measured one, which is the laundering the standard exists to stop.
        # Same rule as the CoT pedigree block, where an unasserted source is
        # omitted rather than guessed.
        #
        # Folding sil or nac_p into a derived confidence was considered and
        # rejected: that mapping is a modelling decision nobody has adjudicated,
        # and inventing it inside an adapter is how a private dialect starts.
        if not isinstance(confidence, (int, float)) or isinstance(confidence, bool):
            raise ValueError(
                "confidence must be asserted by the deployment: the kernel requires it "
                "on FUSION_EVENT and STATE_EVENT, and a broadcast source supplies none"
            )
        if not 0 < float(confidence) <= 1:
            raise ValueError("confidence must be greater than 0 and at most 1")
        self.confidence = float(confidence)
        # Must satisfy producer authority for FUSION_EVENT and STATE_EVENT. The
        # reference wildcard is fusion-*; a sensor producer is deliberately not
        # allowed to declare tracks, and that separation is the point.
        self.producer = producer
        self.node_role = node_role
        self.identity_paths = tuple(identity_paths)
        self.valid_for_ms = valid_for_ms
        self.track_ttl_ms = track_ttl_ms
        self.max_tracks = max_tracks
        self.max_members = max_members
        self.stability_full_count = max(1, int(stability_full_count))
        self.tracks = {}
        self.stats = {
            "observed": 0,
            "projected": 0,
            "refused_no_identity": 0,
            "refused_no_geo": 0,
            "evicted": 0,
        }

    def identity_of(self, event):
        for label, path in self.identity_paths:
            value = _dig(event, path)
            if isinstance(value, (str, int)) and str(value).strip():
                return f"{label}-{str(value).strip().lower()}"
        return None

    def _stability(self, count):
        """A declared count-based proxy, not a kinematic stability measurement.

        The contract requires a stability value on every FUSION_EVENT. For a
        cooperative broadcast the association itself is certain, so what remains
        uncertain early is whether the subject is really being seen repeatedly
        or was a single stray decode. Observation count is an honest proxy for
        exactly that, and it is stated here rather than tuned quietly.
        """
        return round(min(1.0, count / self.stability_full_count), 3)

    def observe(self, event):
        """Return the events to emit for one observation: [] or [fusion, state]."""
        self.stats["observed"] += 1
        if not isinstance(event, dict):
            self.stats["refused_no_identity"] += 1
            return []
        if (event.get("event") or {}).get("event_type") != "OBSERVATION_EVENT":
            return []

        track_id = self.identity_of(event)
        if not track_id:
            self.stats["refused_no_identity"] += 1
            return []

        payload = event.get("payload") or {}
        geo = _canonical_geo(payload)
        if geo is None:
            self.stats["refused_no_geo"] += 1
            return []

        obs_id = (event.get("event") or {}).get("event_id")
        obs_ts = (event.get("event") or {}).get("ts")
        if not obs_id or not obs_ts:
            self.stats["refused_no_identity"] += 1
            return []

        record = self.tracks.get(track_id)
        if record is None:
            if len(self.tracks) >= self.max_tracks:
                # Oldest first, so a flood of new identities cannot evict an
                # active track ahead of a dormant one.
                oldest = min(self.tracks, key=lambda k: self.tracks[k].last_ts or "")
                del self.tracks[oldest]
                self.stats["evicted"] += 1
            record = TrackRecord(track_id)
            self.tracks[track_id] = record

        record.members.append(obs_id)
        if len(record.members) > self.max_members:
            record.members = record.members[-self.max_members:]
        record.count += 1
        record.last_ts = obs_ts
        record.last_event_ts = _epoch_ms(obs_ts)

        timing = payload.get("timing_quality")
        fusion = self._fusion_event(record, obs_ts, timing)
        state = self._state_event(record, fusion, geo, payload, obs_ts, timing)
        self.stats["projected"] += 1
        return [fusion, state]

    def _fusion_event(self, record, ts, timing):
        event = {
            "zmeta_version": "1.0",
            "event": {
                "event_id": str(uuid7()),
                "event_type": "FUSION_EVENT",
                "event_subtype": "TRACK_FUSION",
                "ts": ts,
            },
            "source": {
                "platform_id": self.platform_id,
                "node_role": self.node_role,
                "producer": self.producer,
            },
            "payload": {
                "track_id": record.track_id,
                "members": list(record.members),
                "stability": self._stability(record.count),
                "last_seen_ts": ts,
            },
            "confidence": self.confidence,
            "lineage": {
                "based_on": list(record.members),
                "transform": f"associate:broadcast-identity@{ADAPTER_VERSION}",
            },
        }
        if isinstance(timing, dict):
            event["payload"]["timing_quality"] = copy.deepcopy(timing)
        return event

    def _state_event(self, record, fusion, geo, payload, ts, timing):
        # Contract 7.7: a STATE projection must not re-carry raw observation
        # artifacts. Nothing from payload.features, modality, measurements or
        # data_ref is copied here, and that is enforced by construction rather
        # than by filtering an inherited payload.
        state_payload = {
            "track_id": record.track_id,
            "geo": geo,
            "valid_for_ms": self.valid_for_ms,
        }
        if isinstance(timing, dict):
            state_payload["timing_quality"] = copy.deepcopy(timing)

        speed = _dig(payload, ("features", "adsb_ground_speed_kt"))
        if isinstance(speed, (int, float)):
            state_payload["speed_mps"] = round(speed * 0.514444, 3)
        heading = _dig(payload, ("features", "adsb_track_deg_true"))
        if isinstance(heading, (int, float)):
            state_payload["heading_deg"] = heading

        return {
            "zmeta_version": "1.0",
            "event": {
                "event_id": str(uuid7()),
                "event_type": "STATE_EVENT",
                "event_subtype": "TRACK_STATE",
                "ts": ts,
            },
            "source": {
                "platform_id": self.platform_id,
                "node_role": self.node_role,
                "producer": self.producer,
            },
            "payload": state_payload,
            "confidence": self.confidence,
            "lineage": {
                "based_on": [fusion["event"]["event_id"]],
                "transform": f"project:track-state@{ADAPTER_VERSION}",
            },
        }

    def expire(self, now_ts_ms):
        """Drop tracks past their TTL and return the ids dropped.

        Expiry is deliberately silent on the wire. `valid_for_ms` on each state
        already tells a consumer when the track stops being current, so an
        additional end-of-life event would be a second way to say the same
        thing. See docs/zmeta_track_lifecycle_pattern.md for the full pattern.
        """
        dropped = []
        for track_id, record in list(self.tracks.items()):
            last = record.last_event_ts
            if last is None:
                continue
            if now_ts_ms - last > self.track_ttl_ms:
                del self.tracks[track_id]
                dropped.append(track_id)
        return dropped

    def project_stream(self, events):
        """Run a whole iterable through, returning every emitted event in order."""
        out = []
        for event in events:
            out.extend(self.observe(event))
        return out
