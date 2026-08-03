"""Track projector: the association rules and the refusals, pinned.

The cases that matter are the refusals and the lineage shape. A projector that
quietly invents a track is worse than no projector, because the invented track
reaches a COP looking exactly like a real one.
"""

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import jsonschema  # noqa: E402

from adapters.projector.track.track_projector import TrackProjector  # noqa: E402

SCHEMA = json.loads(
    (ROOT / "schema" / "zmeta-event-1.0.schema.json").read_text(encoding="utf-8")
)
VALIDATOR = jsonschema.Draft202012Validator(SCHEMA)

SCHEMA_110 = json.loads(
    (ROOT / "schema" / "zmeta-event-1.1.0.schema.json").read_text(encoding="utf-8")
)
VALIDATOR_110 = jsonschema.Draft202012Validator(SCHEMA_110)

# Contract 7.7: a STATE projection must not re-carry raw observation artifacts.
FORBIDDEN_ON_STATE = (
    "features", "raw_features", "modality", "measurement", "measurements",
    "t_start", "t_end", "data_ref", "data_refs",
)


def observation(icao="a1b2c3", *, lat=34.05, lon=-118.25, alt_m=3200.4, eid=None, ts=None,
                features=None):
    payload = {
        "modality": "NETWORK",
        "features": features if features is not None else {"adsb_icao24": icao},
        "timing_quality": {
            "time_source": "UNKNOWN", "sync_state": "UNSYNCED",
            "est_error_ms": 60000, "last_sync_ts": "2026-01-27T23:59:59.700000Z",
        },
    }
    if lat is not None and lon is not None and alt_m is not None:
        payload["geo"] = {"lat": lat, "lon": lon, "alt_m": alt_m}
    return {
        "zmeta_version": "1.0",
        "event": {
            "event_id": eid or "019fb4bb-4c74-70dd-bb83-ca4f67ee0723",
            "event_type": "OBSERVATION_EVENT",
            "event_subtype": "NETWORK",
            "ts": ts or "2026-01-27T23:59:59.700Z",
        },
        "source": {
            "platform_id": "adsb-node-01", "node_role": "EDGE",
            "producer": "rf-sensor-adsb-01",
        },
        "payload": payload,
    }


def ais_observation(mmsi=366123456, *, lat=34.05, lon=-118.25, eid=None, ts=None,
                     dimensionality="2D"):
    """An AIS-shaped OBSERVATION_EVENT: mmsi identity, a declared 2-D position.

    Shaped after the doctrine A1-02 declared-position vocabulary
    (schema/zmeta-event-1.1.0.schema.json $defs/geo), which is what this
    projector consumes. It is not shaped after
    adapters/ingress/ais's *current* output, which still demotes position to
    native features and omits canonical geo entirely; landing that side of
    A1-02 is a sibling workstream. The projector's contract is the schema
    vocabulary, not any one adapter's present-day output.
    """
    geo = {"lat": lat, "lon": lon}
    if dimensionality is not None:
        geo["dimensionality"] = dimensionality
    payload = {
        "modality": "NETWORK",
        "features": {"ais_mmsi": mmsi, "protocol": "AIS"},
        "timing_quality": {
            "time_source": "UNKNOWN", "sync_state": "UNSYNCED",
            "est_error_ms": 60000, "last_sync_ts": "2026-01-27T23:59:59.700000Z",
        },
        "geo": geo,
        "quality": {"geo_status": "VERTICAL_UNAVAILABLE"},
    }
    return {
        "zmeta_version": "1.1.0",
        "event": {
            "event_id": eid or "019fb4bb-4c74-70dd-bb83-ca4f67ee0910",
            "event_type": "OBSERVATION_EVENT",
            "event_subtype": "NETWORK",
            "ts": ts or "2026-01-27T23:59:59.700Z",
        },
        "source": {
            "platform_id": "ais-node-01", "node_role": "EDGE",
            "producer": "rf-sensor-ais-01",
        },
        "payload": payload,
    }


def projector(**kw):
    kw.setdefault("platform_id", "adsb-node-01")
    kw.setdefault("confidence", 0.9)
    return TrackProjector(**kw)


def uid(n):
    return f"019fb4bb-4c74-70dd-bb83-ca4f67ee{n:04x}"


class TestAssertedConfidence:
    """The kernel requires confidence; a broadcast source supplies none."""

    def test_omitting_confidence_is_a_construction_error(self):
        with pytest.raises(TypeError):
            TrackProjector(platform_id="adsb-node-01")

    @pytest.mark.parametrize("bad", [0, -0.1, 1.5, "0.9", None, True])
    def test_a_confidence_that_is_not_a_proportion_is_refused(self, bad):
        with pytest.raises(ValueError):
            TrackProjector(platform_id="adsb-node-01", confidence=bad)

    def test_the_asserted_value_reaches_both_emitted_events(self):
        pair = projector(confidence=0.42).observe(observation())
        assert [e["confidence"] for e in pair] == [0.42, 0.42]


class TestRefusals:
    def test_a_known_good_observation_does_produce_a_pair(self):
        """The control. Without this the refusal tests below could pass because
        the projector emits nothing under any circumstances."""
        proj = projector()
        assert len(proj.observe(observation())) == 2
        assert proj.stats["projected"] == 1

    def test_no_identity_means_no_track(self):
        proj = projector()
        obs = observation(features={"rssi_dbfs": -18.4})
        assert proj.observe(obs) == []
        assert proj.stats["refused_no_identity"] == 1

    def test_a_position_without_geometric_altitude_produces_nothing(self):
        """The barometric-only case, which is common in the air and is where an
        implementation is tempted to substitute a height nobody measured."""
        proj = projector()
        assert proj.observe(observation(alt_m=None)) == []
        assert proj.stats["refused_no_geo"] == 1
        assert proj.tracks == {}

    def test_a_target_with_no_position_at_all_produces_nothing(self):
        proj = projector()
        assert proj.observe(observation(lat=None, lon=None, alt_m=None)) == []
        assert proj.stats["refused_no_geo"] == 1

    def test_non_observation_input_is_ignored_without_being_counted_as_refused(self):
        proj = projector()
        state = observation()
        state["event"]["event_type"] = "STATE_EVENT"
        assert proj.observe(state) == []
        assert proj.stats["refused_no_identity"] == 0


class TestIdentity:
    def test_adsb_identity_becomes_a_prefixed_track_id(self):
        assert projector().identity_of(observation("A1B2C3")) == "icao24-a1b2c3"

    def test_ais_identity_is_supported_without_touching_the_logic(self):
        obs = observation(features={"ais_mmsi": 366123456})
        assert projector().identity_of(obs) == "mmsi-366123456"

    def test_the_same_subject_accumulates_into_one_track(self):
        proj = projector()
        for i in range(3):
            proj.observe(observation(eid=uid(i)))
        assert list(proj.tracks) == ["icao24-a1b2c3"]
        assert proj.tracks["icao24-a1b2c3"].count == 3


class TestLineageShape:
    """A STATE may cite only FUSION or STATE parents, so the pair is the point."""

    def test_the_state_cites_the_fusion_and_the_fusion_cites_the_observation(self):
        obs = observation(eid=uid(1))
        fusion, state = projector().observe(obs)
        assert fusion["event"]["event_type"] == "FUSION_EVENT"
        assert state["event"]["event_type"] == "STATE_EVENT"
        assert fusion["lineage"]["based_on"] == [uid(1)]
        assert state["lineage"]["based_on"] == [fusion["event"]["event_id"]]

    def test_no_lineage_parent_is_ever_invented(self):
        """Every id the pair cites was supplied or minted here, never guessed."""
        obs = observation(eid=uid(1))
        fusion, state = projector().observe(obs)
        assert set(fusion["lineage"]["based_on"]) == {uid(1)}
        assert set(fusion["payload"]["members"]) == {uid(1)}
        assert state["lineage"]["based_on"] == [fusion["event"]["event_id"]]

    def test_the_transform_names_what_happened(self):
        fusion, state = projector().observe(observation())
        assert fusion["lineage"]["transform"].startswith("associate:")
        assert state["lineage"]["transform"].startswith("project:")


class TestStateProjectionPurity:
    def test_the_state_carries_no_raw_observation_artifact(self):
        obs = observation(features={
            "adsb_icao24": "a1b2c3", "rssi_dbfs": -18.4, "adsb_message_count": 842,
        })
        obs["payload"]["data_ref"] = {"ref_id": "x", "store": "local", "kind": "RAW"}
        _, state = projector().observe(obs)
        for key in FORBIDDEN_ON_STATE:
            assert key not in state["payload"], f"contract 7.7: {key} on a STATE"

    def test_course_and_speed_project_when_the_source_reports_them(self):
        obs = observation(features={
            "adsb_icao24": "a1b2c3",
            "adsb_ground_speed_kt": 420.5,
            "adsb_track_deg_true": 95.2,
        })
        _, state = projector().observe(obs)
        assert state["payload"]["heading_deg"] == 95.2
        assert state["payload"]["speed_mps"] == pytest.approx(216.32, abs=0.01)

    def test_course_and_speed_are_omitted_when_the_source_does_not_report_them(self):
        _, state = projector().observe(observation())
        assert "heading_deg" not in state["payload"]
        assert "speed_mps" not in state["payload"]


class TestBounds:
    def test_members_are_capped_so_one_subject_cannot_grow_memory(self):
        proj = projector(max_members=3)
        for i in range(10):
            proj.observe(observation(eid=uid(i)))
        fusion, _ = proj.observe(observation(eid=uid(99)))
        assert len(fusion["payload"]["members"]) == 3
        assert fusion["payload"]["members"][-1] == uid(99)

    def test_track_count_is_capped_and_the_oldest_is_evicted_first(self):
        proj = projector(max_tracks=2)
        for i, icao in enumerate(("aaa001", "aaa002")):
            proj.observe(observation(icao, eid=uid(i), ts=f"2026-01-27T23:59:{50+i:02d}Z"))
        proj.observe(observation("aaa003", eid=uid(9), ts="2026-01-27T23:59:59Z"))
        assert len(proj.tracks) == 2
        assert "icao24-aaa001" not in proj.tracks
        assert proj.stats["evicted"] == 1


class TestStability:
    def test_stability_rises_with_observations_and_is_bounded(self):
        proj = projector(stability_full_count=4)
        seen = []
        for i in range(6):
            fusion, _ = proj.observe(observation(eid=uid(i)))
            seen.append(fusion["payload"]["stability"])
        assert seen[0] < seen[1] < seen[2]
        assert seen[-1] == 1.0
        assert all(0 < s <= 1 for s in seen)


class TestSchemaConformance:
    def test_every_emitted_event_validates_against_the_locked_kernel(self):
        proj = projector()
        emitted = []
        for i in range(3):
            emitted.extend(proj.observe(observation(eid=uid(i))))
        assert emitted, "nothing was emitted, so this asserts nothing"
        for event in emitted:
            errors = sorted(VALIDATOR.iter_errors(event), key=lambda e: list(e.path))
            assert not errors, (
                f"{event['event']['event_type']} is schema-invalid: "
                f"{errors[0].message}"
            )

    def test_the_schema_check_would_notice_a_broken_event(self):
        """Non-vacuity: the validator must reject something."""
        _, state = projector().observe(observation())
        broken = copy.deepcopy(state)
        del broken["payload"]["track_id"]
        assert list(VALIDATOR.iter_errors(broken))


class TestTwoDimensionalGeo:
    """Doctrine A1-02: a declared 2-D position is projectable, not refused.

    A surface vessel has no altitude to report, not a missing one. The
    historical refusal (canonical geo silently missing alt_m, no explicit
    token) must keep refusing: only an explicit "2D" dimensionality token
    changes the outcome.
    """

    def test_an_ais_shaped_2d_observation_is_projected(self):
        proj = projector()
        pair = proj.observe(ais_observation())
        assert len(pair) == 2
        assert proj.stats["projected"] == 1
        assert proj.stats["projected_2d"] == 1
        assert proj.stats["refused_no_geo"] == 0

    def test_the_2d_pair_is_stamped_1_1_0_and_a_3d_pair_stays_on_1_0(self):
        fusion_2d, state_2d = projector().observe(ais_observation())
        assert fusion_2d["zmeta_version"] == "1.1.0"
        assert state_2d["zmeta_version"] == "1.1.0"

        fusion_3d, state_3d = projector().observe(observation())
        assert fusion_3d["zmeta_version"] == "1.0"
        assert state_3d["zmeta_version"] == "1.0"

    def test_the_2d_geo_carries_lat_lon_and_the_token_but_never_alt_m(self):
        fusion, state = projector().observe(ais_observation(lat=12.5, lon=100.25))
        for event in (fusion, state):
            geo = event["payload"]["geo"]
            assert geo == {"lat": 12.5, "lon": 100.25, "dimensionality": "2D"}
            assert "alt_m" not in geo

    def test_the_2d_pair_declares_vertical_unavailable(self):
        fusion, state = projector().observe(ais_observation())
        assert fusion["payload"]["quality"] == {"geo_status": "VERTICAL_UNAVAILABLE"}
        assert state["payload"]["quality"] == {"geo_status": "VERTICAL_UNAVAILABLE"}

    def test_a_3d_pair_carries_no_quality_block_at_all(self):
        """A 3-D observation keeps producing exactly today's output."""
        fusion, state = projector().observe(observation())
        assert "quality" not in fusion["payload"]
        assert "quality" not in state["payload"]
        assert "geo" not in fusion["payload"]

    def test_the_2d_fusion_and_state_validate_against_the_1_1_0_schema(self):
        proj = projector()
        emitted = []
        for i in range(3):
            emitted.extend(proj.observe(ais_observation(eid=uid(i))))
        assert emitted, "nothing was emitted, so this asserts nothing"
        for event in emitted:
            errors = sorted(VALIDATOR_110.iter_errors(event), key=lambda e: list(e.path))
            assert not errors, (
                f"{event['event']['event_type']} is schema-invalid under 1.1.0: "
                f"{errors[0].message}"
            )

    def test_lat_lon_with_no_dimensionality_token_and_no_alt_m_still_refuses(self):
        """The historical refusal, pinned against the new acceptance path."""
        proj = projector()
        assert proj.observe(ais_observation(dimensionality=None)) == []
        assert proj.stats["refused_no_geo"] == 1
        assert proj.stats["projected_2d"] == 0

    def test_lat_lon_explicitly_declared_3d_with_no_alt_m_still_refuses(self):
        """An explicit "3D" token asserts a vertical exists; it still needs alt_m."""
        proj = projector()
        assert proj.observe(ais_observation(dimensionality="3D")) == []
        assert proj.stats["refused_no_geo"] == 1


class TestMixedDimensionalityTracks:
    """A track whose members alternate between 2-D and 3-D sources.

    Modelling choice, documented in README.md: the state reflects only the
    member that triggered it, which is by construction the most recent
    position-bearing member, since observe() only proceeds when the incoming
    observation itself carries a projectable position.
    """

    def test_a_track_that_gains_a_2d_member_after_a_3d_one_reflects_the_2d_fix(self):
        proj = projector()
        proj.observe(observation(icao="a1b2c3", eid=uid(1)))
        obs = ais_observation(eid=uid(2))
        obs["payload"]["features"]["adsb_icao24"] = "a1b2c3"
        del obs["payload"]["features"]["ais_mmsi"]
        _, state = proj.observe(obs)
        assert state["payload"]["geo"]["dimensionality"] == "2D"
        assert "alt_m" not in state["payload"]["geo"]
        assert state["zmeta_version"] == "1.1.0"
        assert list(proj.tracks) == ["icao24-a1b2c3"]
        assert proj.tracks["icao24-a1b2c3"].count == 2

    def test_a_track_that_regains_a_3d_member_after_a_2d_one_reflects_the_3d_fix(self):
        proj = projector()
        obs_2d = ais_observation(eid=uid(1))
        obs_2d["payload"]["features"]["adsb_icao24"] = "a1b2c3"
        del obs_2d["payload"]["features"]["ais_mmsi"]
        proj.observe(obs_2d)
        _, state = proj.observe(observation(icao="a1b2c3", eid=uid(2)))
        assert state["payload"]["geo"]["alt_m"] == pytest.approx(3200.4)
        assert "dimensionality" not in state["payload"]["geo"]
        assert state["zmeta_version"] == "1.0"
        assert proj.tracks["icao24-a1b2c3"].count == 2


class TestExpiry:
    def test_a_track_past_its_ttl_is_dropped(self):
        proj = projector(track_ttl_ms=1000)
        proj.observe(observation(ts="2026-01-27T23:59:00Z"))
        assert proj.expire(_ms("2026-01-27T23:59:00Z") + 500) == []
        assert proj.expire(_ms("2026-01-27T23:59:00Z") + 5000) == ["icao24-a1b2c3"]
        assert proj.tracks == {}

    def test_an_unreadable_timestamp_keeps_the_track_rather_than_dropping_it(self):
        """The kernel accepts any ts ending in Z, so this is reachable. Dropping
        a track on a parse failure would lose a real subject over a bad clock."""
        proj = projector(track_ttl_ms=1000)
        proj.observe(observation(ts="banana-Z"))
        assert proj.expire(10**13) == []
        assert "icao24-a1b2c3" in proj.tracks


def _ms(ts):
    from adapters.projector.track.track_projector import _epoch_ms
    return _epoch_ms(ts)
