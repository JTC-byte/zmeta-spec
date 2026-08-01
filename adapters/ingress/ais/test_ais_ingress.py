"""AIS ingress: the honesty rules, pinned against real message shapes.

Every case here is a shape a decoder actually produces. The ones that matter
most are the refusals and the standard's not-available sentinels: explicit
encodings of "not reported" that, carried as values, would place a stopped
vessel at the north pole on a due-north heading.
"""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import jsonschema  # noqa: E402

from adapters.ingress.ais.ais_to_zmeta import (  # noqa: E402
    translate_message,
    translate_stream,
)
from adapters.ingress.time_utils import DEFAULT_UNSYNCED_ERROR_MS  # noqa: E402

SCHEMA = json.loads(
    (ROOT / "schema" / "zmeta-event-1.0.schema.json").read_text(encoding="utf-8")
)
VALIDATOR = jsonschema.Draft202012Validator(SCHEMA)

BASE = dict(platform_id="ais-node-01", receiver_id="rtlsdr-01")

CLASS_A = {
    "type": 1, "mmsi": 366123456, "lat": 33.7405, "lon": -118.2712,
    "speed": 12.4, "course": 271.3, "heading": 270, "status": 0,
    "accuracy": True, "second": 42, "signalpower": -31.2,
    "rxtime": "20260731120000", "shipname": "EVER GIVEN@@@@@@",
    "callsign": "H3RC@@@", "shiptype": 70,
}


def msg(**over):
    out = dict(CLASS_A)
    out.update(over)
    return out


def translate(**over):
    return translate_message(msg(**over), **BASE)


class TestSubjectAndScope:
    def test_a_full_position_report_becomes_an_event(self):
        """The control. Every refusal below is meaningless without this."""
        event = translate()
        assert event is not None
        assert event["event"]["event_type"] == "OBSERVATION_EVENT"
        assert event["event"]["event_subtype"] == "NETWORK"

    @pytest.mark.parametrize("mtype", [1, 2, 3, 18, 19, 27])
    def test_every_position_report_type_is_accepted(self, mtype):
        assert translate(type=mtype) is not None

    @pytest.mark.parametrize("mtype", [4, 5, 21, 24])
    def test_non_position_message_types_produce_nothing(self, mtype):
        """Static, base-station and aid-to-navigation messages carry no position
        report; emitting an event for them would invent an observation."""
        assert translate(type=mtype) is None

    def test_a_message_without_an_mmsi_is_refused(self):
        m = msg()
        del m["mmsi"]
        assert translate_message(m, **BASE) is None

    @pytest.mark.parametrize("bad", [0, -1, "366123456", None, True])
    def test_an_unusable_mmsi_is_refused(self, bad):
        assert translate(mmsi=bad) is None

    def test_non_dict_input_is_refused(self):
        assert translate_message("not a message", **BASE) is None


class TestTheAltitudeRule:
    """A vessel has no altitude, so canonical geo is never built."""

    def test_canonical_geo_is_never_emitted_even_with_a_perfect_position(self):
        event = translate()
        assert "geo" not in event["payload"], (
            "a vessel has no height above the ellipsoid; building canonical geo "
            "would require inventing alt_m"
        )

    def test_the_real_position_is_demoted_not_discarded(self):
        features = translate()["payload"]["features"]
        assert features["ais_lat_deg"] == 33.7405
        assert features["ais_lon_deg"] == -118.2712

    def test_geo_status_is_declared_unavailable(self):
        assert translate()["payload"]["quality"]["geo_status"] == "UNAVAILABLE"

    def test_no_altitude_key_is_invented_anywhere_in_the_payload(self):
        payload = json.dumps(translate()["payload"])
        for invented in ('"alt_m"', '"altitude"', '"hae"'):
            assert invented not in payload


class TestNotAvailableSentinels:
    def test_the_position_sentinels_are_not_a_position(self):
        """lat 91 / lon 181 mean 'not reported'. They are refused by name,
        not merely as out-of-range numbers."""
        features = translate(lat=91.0, lon=181.0)["payload"]["features"]
        assert "ais_lat_deg" not in features
        assert "ais_lon_deg" not in features

    def test_message_27_has_its_own_sentinels_and_they_are_dropped(self):
        """Long-range reports pack speed and course into smaller fields with
        their own not-available encodings. Carried as values they would be a
        vessel doing a real-looking 63 kt on a course that does not exist."""
        features = translate(type=27, speed=63.0, course=511.0)["payload"]["features"]
        assert "ais_sog_kt" not in features
        assert "ais_cog_deg_true" not in features

    def test_63_knots_in_a_class_a_report_is_a_real_speed(self):
        """The message 27 speed sentinel is scoped to message 27."""
        assert translate(type=1, speed=63.0)["payload"]["features"]["ais_sog_kt"] == 63.0

    def test_a_message_27_speed_above_its_own_field_is_dropped(self):
        """The message 27 speed field encodes 0 to 62 kt. An 80 kt reading
        cannot come out of it except as corruption, and the attack pass on
        the first fix found the guard still applying the Class A bound."""
        assert "ais_sog_kt" not in translate(type=27, speed=80.0)["payload"]["features"]

    def test_a_message_27_speed_at_its_field_maximum_is_carried(self):
        assert translate(type=27, speed=62.0)["payload"]["features"]["ais_sog_kt"] == 62.0

    def test_speed_over_ground_sentinel_is_dropped(self):
        assert "ais_sog_kt" not in translate(speed=102.3)["payload"]["features"]

    def test_course_sentinel_is_dropped(self):
        assert "ais_cog_deg_true" not in translate(course=360.0)["payload"]["features"]

    def test_heading_sentinel_is_dropped(self):
        assert "ais_heading_deg_true" not in translate(heading=511)["payload"]["features"]

    @pytest.mark.parametrize("second", [60, 61, 62, 63])
    def test_second_special_values_are_a_status_not_a_time(self, second):
        features = translate(second=second)["payload"]["features"]
        assert features["ais_second_status"] == second
        assert "ais_second_of_minute" not in features

    def test_a_real_second_is_carried_as_a_second(self):
        features = translate(second=42)["payload"]["features"]
        assert features["ais_second_of_minute"] == 42
        assert "ais_second_status" not in features

    def test_a_positionless_report_is_still_a_real_observation(self):
        """A decoded emitter with no position is a detection, not a non-event."""
        event = translate(lat=91.0, lon=181.0)
        assert event is not None
        assert event["payload"]["features"]["ais_mmsi"] == 366123456


class TestDecoderGarbage:
    """Values the AIS fields cannot encode are corruption, not measurements."""

    @pytest.mark.parametrize("bad", [-0.1, 102.4, 720.0])
    def test_an_impossible_speed_is_dropped(self, bad):
        assert "ais_sog_kt" not in translate(speed=bad)["payload"]["features"]

    @pytest.mark.parametrize("bad", [-1.0, 360.1, 511.0, 720.5])
    def test_an_impossible_course_is_dropped(self, bad):
        assert "ais_cog_deg_true" not in translate(course=bad)["payload"]["features"]

    def test_the_extremes_of_the_real_ranges_still_carry(self):
        """The guards drop what the fields cannot encode, not fast traffic."""
        features = translate(speed=102.2, course=359.9)["payload"]["features"]
        assert features["ais_sog_kt"] == 102.2
        assert features["ais_cog_deg_true"] == 359.9


class TestNoLaundering:
    def test_signal_power_is_never_power_dbm(self):
        features = translate()["payload"]["features"]
        assert features["ais_signal_power_db"] == -31.2
        assert "power_dbm" not in features

    def test_modality_is_network_not_rf(self):
        assert translate()["payload"]["modality"] == "NETWORK"

    def test_declared_codes_stay_codes_and_never_become_classifications(self):
        payload = translate()["payload"]
        assert payload["features"]["ais_nav_status_code"] == 0
        assert payload["features"]["ais_shiptype_code"] == 70
        assert "class" not in payload
        assert "classification" not in payload

    def test_the_observation_carries_no_identity_or_track(self):
        """An OBSERVATION_EVENT asserting identity is an authority-boundary
        violation the kernel refuses."""
        payload = translate()["payload"]
        assert "track_id" not in payload
        assert "identity" not in payload

    @pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf")])
    def test_non_finite_numbers_are_not_values(self, bad):
        features = translate(speed=bad, signalpower=bad)["payload"]["features"]
        assert "ais_sog_kt" not in features
        assert "ais_signal_power_db" not in features


class TestTextAndTiming:
    def test_ais_text_padding_is_not_content(self):
        features = translate()["payload"]["features"]
        assert features["ais_shipname"] == "EVER GIVEN"
        assert features["ais_callsign"] == "H3RC"

    def test_an_all_padding_name_yields_no_name(self):
        assert "ais_shipname" not in translate(shipname="@@@@@@@@")["payload"]["features"]

    def test_reception_time_comes_from_the_decoder(self):
        assert translate()["event"]["ts"].startswith("2026-07-31T12:00:00")

    def test_a_message_with_no_usable_time_is_refused(self):
        m = msg()
        del m["rxtime"]
        assert translate_message(m, platform_id="ais-node-01") is None

    def test_fourteen_digits_that_are_not_a_date_refuse_the_message(self):
        """Month 88 slices into a string the schema accepts as a timestamp.
        A corrupt time channel is a refusal, not a fact to reformat."""
        assert translate(rxtime="20268888888888") is None

    def test_an_epoch_far_outside_datetime_range_refuses_not_crashes(self):
        m = msg()
        del m["rxtime"]
        m["timestamp"] = 1e18
        assert translate_message(m, **BASE) is None

    def test_a_small_number_under_timestamp_is_not_epoch_seconds(self):
        """A second-of-minute leaking in under the `timestamp` key must not
        date the event 1970-01-01."""
        m = msg()
        del m["rxtime"]
        m["timestamp"] = 42
        assert translate_message(m, **BASE) is None

    def test_absent_clock_metadata_degrades_rather_than_claiming_sync(self):
        """The governed fallback, pinned exactly. The first version of this
        pin asserted only `!= "LOCKED"`, which a fabricated HOLDOVER claim
        also satisfies; the 2026-07-31 pre-push cold read demonstrated it."""
        timing = translate()["payload"]["timing_quality"]
        assert timing["time_source"] == "UNKNOWN"
        assert timing["sync_state"] == "UNSYNCED"
        assert timing["est_error_ms"] == DEFAULT_UNSYNCED_ERROR_MS


class TestStreamAccounting:
    def test_refusals_are_dropped_not_patched(self):
        messages = [msg(), msg(type=5), msg(mmsi=0), msg(mmsi=338111222)]
        events = translate_stream(messages, **BASE)
        assert len(events) == 2
        assert [e["payload"]["features"]["ais_mmsi"] for e in events] == [366123456, 338111222]

    def test_a_generator_stream_is_translated_not_swallowed(self):
        """A generator is the natural shape of a live decoder feed. The first
        version of this function returned [] for one, silently."""
        stream = (m for m in [msg(), msg(mmsi=338111222)])
        assert len(translate_stream(stream, **BASE)) == 2

    def test_a_non_iterable_raises_rather_than_yielding_an_empty_sea(self):
        """Zero events from a miswired call must not look like zero traffic."""
        with pytest.raises(TypeError):
            translate_stream(None, **BASE)

    def test_a_single_message_dict_is_a_miswired_call_not_a_stream(self):
        """Passing one message where a stream belongs is the natural mistake,
        and a dict iterates as its keys, which reads as an empty sea."""
        with pytest.raises(TypeError):
            translate_stream(msg(), **BASE)

    def test_a_string_is_a_miswired_call_not_a_stream(self):
        with pytest.raises(TypeError):
            translate_stream("decoded.json", **BASE)

    def test_one_poisoned_message_does_not_kill_the_batch(self):
        poisoned = msg(mmsi=338111222)
        del poisoned["rxtime"]
        poisoned["timestamp"] = 1e18
        events = translate_stream([msg(), poisoned], **BASE)
        assert len(events) == 1
        assert events[0]["payload"]["features"]["ais_mmsi"] == 366123456


class TestSchemaConformance:
    def test_emitted_events_validate_against_the_locked_kernel(self):
        events = translate_stream([msg(), msg(type=18, mmsi=338111222)], **BASE)
        assert events, "nothing emitted, so this asserts nothing"
        for event in events:
            errors = sorted(VALIDATOR.iter_errors(event), key=lambda e: list(e.path))
            assert not errors, f"schema-invalid: {errors[0].message}"

    def test_the_schema_check_would_notice_a_broken_event(self):
        broken = translate()
        del broken["event"]["event_type"]
        assert list(VALIDATOR.iter_errors(broken))


class TestTrackProjectionConsequence:
    def test_a_valid_ais_observation_yields_no_track(self):
        """A1-02, second independent implementation, and total rather than partial.

        Identity resolves, the position is exact and broadcast, the event is
        schema-valid, and no track can be projected because a track needs
        canonical geo. Every vessel, every message.
        """
        from adapters.projector.track.track_projector import TrackProjector

        projector = TrackProjector(platform_id="ais-node-01", confidence=0.9)
        event = translate()
        assert projector.identity_of(event) == "mmsi-366123456"
        assert projector.observe(event) == []
        assert projector.stats["refused_no_geo"] == 1
        assert projector.stats["refused_no_identity"] == 0
