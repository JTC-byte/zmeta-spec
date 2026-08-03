"""A1-02: a real position with no vertical is sayable, honestly, on v1.1.

Adjudicated 2026-08-02 (shape approved with rationale, recorded in the
handoff): a large share of real traffic will never have vertical data, and
denying good pings for data they will never have is the wrong failure.
Canonical geo on the v1.1.0 branch gains a declared dimensionality; absent
means 3D so every pre-existing event validates unchanged, and "2D" declares
a horizontal-only position and prohibits alt_m entirely. quality.geo_status
gains VERTICAL_UNAVAILABLE: canonical geo present and two-dimensional. The
coherence arms keep token and form honest in both directions, so a
status-only consumer cannot mistake a 2-D fix for a full one. The locked
v1.0 schema is untouched: the 2-D form exists only where producers opt in.
"""

import copy
import json
import unittest
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[2]


def observation_2d(dimensionality="2D", alt_m=None, geo_status=None):
    event = {
        "zmeta_version": "1.1.0",
        "event": {
            "event_id": "019c2b5c-c045-7222-be17-463750a407f4",
            "event_type": "OBSERVATION_EVENT",
            "event_subtype": "NETWORK",
            "ts": "2026-08-01T12:00:00Z",
        },
        "source": {
            "platform_id": "ais-node-01",
            "node_role": "EDGE",
            "producer": "rf-sensor-ais-01",
        },
        "profile": "H",
        "payload": {
            "modality": "NETWORK",
            "features": {"ais_mmsi": 366123456, "protocol": "AIS"},
            "geo": {"lat": 33.7405, "lon": -118.2712},
            "timing_quality": {
                "time_source": "UNKNOWN",
                "sync_state": "UNSYNCED",
                "est_error_ms": 60000,
                "last_sync_ts": "2026-08-01T12:00:00Z",
            },
        },
    }
    if dimensionality is not None:
        event["payload"]["geo"]["dimensionality"] = dimensionality
    if alt_m is not None:
        event["payload"]["geo"]["alt_m"] = alt_m
    if geo_status is not None:
        event["payload"]["quality"] = {"geo_status": geo_status}
    return event


class A102DimensionalityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads(
            (ROOT / "schema" / "zmeta-event-1.1.0.schema.json").read_text(
                encoding="utf-8"
            )
        )
        cls.validator = jsonschema.Draft202012Validator(cls.schema)

    def assert_valid(self, event):
        errors = sorted(
            self.validator.iter_errors(event), key=lambda e: list(e.path)
        )
        self.assertFalse(errors, errors[0].message if errors else "")

    def assert_invalid(self, event):
        self.assertTrue(list(self.validator.iter_errors(event)))

    def test_a_declared_2d_position_needs_no_altitude(self):
        """The headline: the AIS vessel's exact position is sayable."""
        self.assert_valid(observation_2d())

    def test_a_2d_position_carrying_an_altitude_is_a_contradiction(self):
        self.assert_invalid(observation_2d(alt_m=120.5))

    def test_absent_dimensionality_still_means_3d(self):
        """Backward compatibility is a schema rule, not a hope: every
        pre-existing event carries alt_m and no dimensionality field."""
        self.assert_invalid(observation_2d(dimensionality=None))
        self.assert_valid(observation_2d(dimensionality=None, alt_m=120.5))

    def test_explicit_3d_requires_altitude_like_absent_does(self):
        self.assert_invalid(observation_2d(dimensionality="3D"))
        self.assert_valid(observation_2d(dimensionality="3D", alt_m=120.5))

    def test_an_unknown_dimensionality_value_is_refused(self):
        self.assert_invalid(observation_2d(dimensionality="2.5D"))

    def test_vertical_unavailable_token_fits_a_2d_geo(self):
        self.assert_valid(observation_2d(geo_status="VERTICAL_UNAVAILABLE"))

    def test_vertical_unavailable_on_a_3d_geo_is_a_lie(self):
        self.assert_invalid(
            observation_2d(
                dimensionality=None, alt_m=120.5, geo_status="VERTICAL_UNAVAILABLE"
            )
        )

    def test_available_on_a_2d_geo_hides_the_missing_vertical(self):
        """The status a filter-only consumer reads must not claim a full fix
        for a horizontal-only position."""
        self.assert_invalid(observation_2d(geo_status="AVAILABLE"))

    def test_unavailable_beside_a_present_geo_is_the_third_lie(self):
        """Queued by the wave-1 attack pass: UNAVAILABLE means no canonical
        geo at all, and nothing blocked asserting it beside a present geo.
        Arm 3 does, for 2-D and 3-D alike."""
        self.assert_invalid(
            observation_2d(dimensionality=None, alt_m=120.5, geo_status="UNAVAILABLE")
        )
        self.assert_invalid(observation_2d(geo_status="UNAVAILABLE"))

    def test_unavailable_without_geo_stays_the_honest_no_fix_statement(self):
        event = observation_2d(dimensionality=None, geo_status="UNAVAILABLE")
        del event["payload"]["geo"]
        self.assert_valid(event)

    @staticmethod
    def _fusion_event(estimated_geo, geo_status=None):
        """A COMPLETE, otherwise-valid FUSION_EVENT, so each assertion below
        fails or passes for exactly one reason. The first draft of these
        pins omitted track_id and stability, which made the negative pin
        pass vacuously on unrelated required-field errors: the exact defect
        class this file exists to prevent, caught by running the control."""
        payload = {
            "track_id": "mmsi-366123456",
            "members": ["019c2b5c-c045-7222-be17-463750a407f5"],
            "stability": 0.9,
            "last_seen_ts": "2026-08-01T12:00:00Z",
            "estimated_state": {"geo": estimated_geo},
            "timing_quality": {
                "time_source": "UNKNOWN",
                "sync_state": "UNSYNCED",
                "est_error_ms": 60000,
                "last_sync_ts": "2026-08-01T12:00:00Z",
            },
        }
        if geo_status is not None:
            payload["quality"] = {"geo_status": geo_status}
        return {
            "zmeta_version": "1.1.0",
            "event": {
                "event_id": "019c2b5c-c045-7222-be17-463750a407f4",
                "event_type": "FUSION_EVENT",
                "event_subtype": "TRACK_FUSION",
                "ts": "2026-08-01T12:00:00Z",
            },
            "source": {
                "platform_id": "fusion-node-01",
                "node_role": "GATEWAY",
                "producer": "fusion-engine",
            },
            "profile": "H",
            "confidence": 0.8,
            "lineage": {
                "based_on": ["019c2b5c-c045-7222-be17-463750a407f5"],
                "transform": "fuse:track",
            },
            "payload": payload,
        }

    def test_estimated_state_2d_geo_cannot_claim_available_either(self):
        """The wave-2 attack pass reproduced the arm-2 lie one container
        over: FUSION estimated_state.geo declared 2-D beside geo_status
        AVAILABLE validated clean. Same lie, same refusal (the R1-11 A-16
        lesson: spatial rules walk every container that carries geo)."""
        lie = self._fusion_event(
            {"lat": 33.7, "lon": -118.2, "dimensionality": "2D"},
            geo_status="AVAILABLE",
        )
        self.assert_invalid(lie)
        control = self._fusion_event(
            {"lat": 33.7, "lon": -118.2, "dimensionality": "2D"},
            geo_status="VERTICAL_UNAVAILABLE",
        )
        # Arm 1 requires payload.geo for the token today; the estimated_state
        # producer that would motivate extending it does not exist yet, so
        # the honest control here uses no status at all.
        no_status = self._fusion_event(
            {"lat": 33.7, "lon": -118.2, "dimensionality": "2D"}
        )
        self.assert_valid(no_status)

    def test_estimated_state_geo_cannot_be_called_unavailable_either(self):
        """The cross-wave pat-down found arm 3 carrying the same blind spot
        arm 2b had closed 22 minutes earlier in this same file: the general
        lesson (spatial rules walk every container that carries geo) was
        written down and applied to one arm only. UNAVAILABLE means no
        canonical geo anywhere, so a populated estimated_state.geo refuses
        it, 2-D and 3-D alike."""
        for geo in (
            {"lat": 33.7, "lon": -118.2, "dimensionality": "2D"},
            {"lat": 33.7, "lon": -118.2, "alt_m": 120.5},
        ):
            self.assert_invalid(self._fusion_event(geo, geo_status="UNAVAILABLE"))

    def test_unavailable_still_stands_when_no_container_carries_geo(self):
        event = self._fusion_event({"lat": 33.7, "lon": -118.2, "alt_m": 1.0})
        del event["payload"]["estimated_state"]
        event["payload"]["quality"] = {"geo_status": "UNAVAILABLE"}
        self.assert_valid(event)

    def test_the_shape_rule_already_binds_inside_estimated_state(self):
        """Inherited from the shared geo def and pinned here so the registry
        entry's estimated_state payload_scope claim is substantiated by a
        fixture, which the attack pass found it was not."""
        self.assert_invalid(
            self._fusion_event(
                {"lat": 33.7, "lon": -118.2, "dimensionality": "2D", "alt_m": 10.0}
            )
        )
        self.assert_valid(
            self._fusion_event({"lat": 33.7, "lon": -118.2, "alt_m": 10.0})
        )

    def test_the_2d_form_does_not_exist_under_the_locked_v10_stamp(self):
        """The locked kernel is untouched: dimensionality is not a v1.0
        member, so the 2-D form rides the 1.1.0 stamp only."""
        schema_v10 = json.loads(
            (ROOT / "schema" / "zmeta-event-1.0.schema.json").read_text(
                encoding="utf-8"
            )
        )
        event = observation_2d()
        event["zmeta_version"] = "1.0"
        self.assertTrue(
            list(jsonschema.Draft202012Validator(schema_v10).iter_errors(event))
        )


if __name__ == "__main__":
    unittest.main()
