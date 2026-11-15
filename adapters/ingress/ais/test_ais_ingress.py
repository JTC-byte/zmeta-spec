"""AIS ingress: the honesty rules, pinned against real message shapes.

Every case here is a shape a decoder actually produces. The ones that matter
most are the refusals and the standard's not-available sentinels: explicit
encodings of "not reported" that, carried as values, would place a stopped
vessel at the north pole on a due-north heading.
"""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import jsonschema  # noqa: E402

from adapters.ingress.ais.ais_to_zmeta import (  # noqa: E402
    AIS_CHANNEL_A_HZ,
    AIS_CHANNEL_B_HZ,
    translate_message,
    translate_stream,
)
from adapters.ingress.time_utils import (  # noqa: E402
    DEFAULT_UNSYNCED_ERROR_MS,
    coerce_timing_quality,
)

SCHEMA_DIR = ROOT / "schema"
VALIDATOR_1_0 = jsonschema.Draft202012Validator(
    json.loads((SCHEMA_DIR / "zmeta-event-1.0.schema.json").read_text(encoding="utf-8"))
)
VALIDATOR_1_1_0 = jsonschema.Draft202012Validator(
    json.loads((SCHEMA_DIR / "zmeta-event-1.1.0.schema.json").read_text(encoding="utf-8"))
)

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


class TestTheDeclaredTwoDimensionalGeo:
    """A vessel never has an altitude, so canonical geo is never the 3-D form,
    but doctrine A1-02 gives it a 2-D one: a usable position now gets a
    canonical home instead of a full demotion. This adapter is A1-02's
    independent second implementation, and the sharper instance -- every
    vessel, every message, not a barometric-only subset.
    """

    def test_a_usable_position_gets_the_declared_2d_canonical_form(self):
        event = translate()
        assert event["payload"]["geo"] == {
            "lat": 33.7405,
            "lon": -118.2712,
            "dimensionality": "2D",
        }
        assert event["zmeta_version"] == "1.1.0"
        VALIDATOR_1_1_0.validate(event)

    def test_the_real_position_is_still_carried_natively_too(self):
        """Canonical geo exists now, but the native keys stay: they are the
        exact as-broadcast record, and existing consumers already read them
        there regardless of what canonical geo says."""
        features = translate()["payload"]["features"]
        assert features["ais_lat_deg"] == 33.7405
        assert features["ais_lon_deg"] == -118.2712

    def test_geo_status_is_vertical_unavailable_not_available(self):
        """The horizontal fix is real and canonical; the vertical component
        does not exist for a surface vessel. AVAILABLE would claim a 3-D
        position this adapter never has grounds to assert."""
        assert translate()["payload"]["quality"]["geo_status"] == "VERTICAL_UNAVAILABLE"

    def test_no_altitude_key_is_ever_invented_anywhere_in_the_payload(self):
        payload = json.dumps(translate()["payload"])
        for invented in ('"alt_m"', '"altitude"', '"hae"'):
            assert invented not in payload

    def test_a_positionless_message_stays_on_the_locked_v1_0_branch(self):
        """No usable position touches no v1.1.0-only vocabulary, so the event
        never leaves v1.0: no geo, the historical UNAVAILABLE token, and no
        `protocol` feature."""
        event = translate(lat=91.0, lon=181.0)
        assert event["zmeta_version"] == "1.0"
        assert "geo" not in event["payload"]
        assert event["payload"]["quality"]["geo_status"] == "UNAVAILABLE"
        assert "protocol" not in event["payload"]["features"]
        VALIDATOR_1_0.validate(event)


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
        """The message 27 speed sentinel is scoped to message 27 and to a
        record with no message type. On a typed Class A report, 63 kt is a real
        speed."""
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


class TestVersionStampAndProtocol:
    """The conditional-stamp pattern (adapters/ingress/adsb/adsb_to_zmeta.py
    is the reference implementation): an event stamps `zmeta_version
    "1.1.0"` only when it actually uses v1.1.0-only vocabulary, `"1.0"`
    otherwise, and NETWORK `features` gains the mandatory `protocol` key only
    on the branch that needs the newer schema at all.
    """

    def test_a_usable_position_stamps_1_1_0_and_gains_protocol(self):
        event = translate()
        assert event["zmeta_version"] == "1.1.0"
        assert event["payload"]["features"]["protocol"] == "AIS"
        VALIDATOR_1_1_0.validate(event)

    def test_a_positionless_message_is_byte_stable_v1_0_output(self):
        """No position touches no v1.1.0-only vocabulary, so this is exactly
        the payload the adapter has always produced for a positionless
        message: no `geo`, no `protocol`, `geo_status` UNAVAILABLE."""
        event = translate(lat=91.0, lon=181.0)
        assert event["zmeta_version"] == "1.0"
        assert event["source"] == {
            "platform_id": "ais-node-01",
            "node_role": "EDGE",
            "producer": "rf-sensor-ais-01",
        }
        assert event["payload"] == {
            "modality": "NETWORK",
            "features": {
                "ais_mmsi": 366123456,
                "ais_channel_a_hz": AIS_CHANNEL_A_HZ,
                "ais_channel_b_hz": AIS_CHANNEL_B_HZ,
                "ais_receiver_id": "rtlsdr-01",
                "ais_message_type": 1,
                "ais_sog_kt": 12.4,
                "ais_cog_deg_true": 271.3,
                "ais_heading_deg_true": 270,
                "ais_nav_status_code": 0,
                "ais_position_accuracy_high": True,
                "ais_second_of_minute": 42,
                "ais_signal_power_db": -31.2,
                "ais_shipname": "EVER GIVEN",
                "ais_callsign": "H3RC",
                "ais_shiptype_code": 70,
            },
            "timing_quality": coerce_timing_quality(None, event_ts=event["event"]["ts"]),
            "quality": {"geo_status": "UNAVAILABLE"},
        }
        VALIDATOR_1_0.validate(event)


class TestSchemaConformance:
    def test_emitted_events_validate_against_the_schema_their_stamp_names(self):
        """A message with a usable position now stamps 1.1.0 and must
        validate against the 1.1.0 schema; a positionless message stays on
        the locked v1.0 branch and must still validate against it."""
        events = translate_stream([msg(), msg(type=18, mmsi=338111222)], **BASE)
        assert events, "nothing emitted, so this asserts nothing"
        for event in events:
            validator = VALIDATOR_1_1_0 if event["zmeta_version"] == "1.1.0" else VALIDATOR_1_0
            errors = sorted(validator.iter_errors(event), key=lambda e: list(e.path))
            assert not errors, f"schema-invalid: {errors[0].message}"

    def test_a_positionless_message_still_validates_against_the_locked_v1_0_kernel(self):
        event = translate(lat=91.0, lon=181.0)
        assert event["zmeta_version"] == "1.0"
        errors = sorted(VALIDATOR_1_0.iter_errors(event), key=lambda e: list(e.path))
        assert not errors, f"schema-invalid: {errors[0].message}"

    def test_the_schema_check_would_notice_a_broken_event(self):
        broken = translate()
        del broken["event"]["event_type"]
        assert list(VALIDATOR_1_1_0.iter_errors(broken))


class TestTrackProjectionConsequence:
    """A1-02's wall covered projection too, and this is its measured lift.

    A track needs canonical geo, and under v1.0 AIS's demoted-only position
    could never give it one: every vessel, every message projected to zero
    tracks. The declared 2-D form gives the projector a canonical position to
    build from, and it does, without ever claiming a vertical the message
    never gave.
    """

    def test_a_valid_ais_observation_now_yields_a_two_dimensional_track(self):
        from adapters.projector.track.track_projector import TrackProjector

        projector = TrackProjector(platform_id="ais-node-01", confidence=0.9)
        event = translate()
        assert projector.identity_of(event) == "mmsi-366123456"
        fusion, state = projector.observe(event)
        assert fusion["event"]["event_type"] == "FUSION_EVENT"
        assert state["event"]["event_type"] == "STATE_EVENT"
        assert state["zmeta_version"] == "1.1.0"
        assert state["payload"]["geo"] == {
            "lat": 33.7405,
            "lon": -118.2712,
            "dimensionality": "2D",
        }
        assert state["payload"]["quality"]["geo_status"] == "VERTICAL_UNAVAILABLE"
        assert "alt_m" not in state["payload"]["geo"]
        assert projector.stats["projected_2d"] == 1
        assert projector.stats["refused_no_geo"] == 0

    def test_a_positionless_ais_observation_still_yields_no_track(self):
        """The refusal this class used to document unconditionally still
        holds for the one case that still has no honest position at all."""
        from adapters.projector.track.track_projector import TrackProjector

        projector = TrackProjector(platform_id="ais-node-01", confidence=0.9)
        event = translate(lat=91.0, lon=181.0)
        assert projector.identity_of(event) == "mmsi-366123456"
        assert projector.observe(event) == []
        assert projector.stats["refused_no_geo"] == 1
        assert projector.stats["refused_no_identity"] == 0


_ABSENT = object()


def typeless(**over):
    """A position record with no message type that declares its transceiver
    class: the shape a record source produces when it publishes decoded
    position reports with the type removed and the class kept. An override
    of `_ABSENT` removes the key."""
    out = dict(CLASS_A)
    del out["type"]
    out["transceiver_class"] = "A"
    for key, value in over.items():
        if value is _ABSENT:
            out.pop(key, None)
        else:
            out[key] = value
    return out


def translate_typeless(**over):
    return translate_message(typeless(**over), **BASE)


class TestRecordsWithNoMessageType:
    """A record that carries no message type is accepted only on two
    statements the source made itself: a shipborne transceiver class, A or B,
    and a usable position. The event says which statement it rests on: it
    carries `ais_transceiver_class` and no `ais_message_type`, because no
    type was read and none is inferred. A message that does carry a type is
    translated exactly as before, and the class is not read on it.
    """

    def test_a_typeless_record_with_a_class_and_a_position_becomes_an_event(self):
        """The control. Every refusal in this class is meaningless without it."""
        event = translate_typeless()
        assert event is not None
        assert event["event"]["event_type"] == "OBSERVATION_EVENT"
        assert event["event"]["event_subtype"] == "NETWORK"
        features = event["payload"]["features"]
        assert "ais_message_type" not in features
        assert features["ais_transceiver_class"] == "A"
        assert features["ais_mmsi"] == 366123456
        assert features["protocol"] == "AIS"
        assert event["zmeta_version"] == "1.1.0"
        assert event["payload"]["geo"] == {
            "lat": 33.7405,
            "lon": -118.2712,
            "dimensionality": "2D",
        }
        assert event["payload"]["quality"]["geo_status"] == "VERTICAL_UNAVAILABLE"

    def test_a_type_key_holding_none_is_the_absent_case(self):
        event = translate_typeless(type=None)
        assert event is not None
        assert "ais_message_type" not in event["payload"]["features"]
        assert event["payload"]["features"]["ais_transceiver_class"] == "A"

    @pytest.mark.parametrize("declared, token", [("A", "A"), ("B", "B"), (" a ", "A"), ("b", "B"), ("\tB\n", "B")])
    def test_the_class_is_folded_for_whitespace_and_case(self, declared, token):
        """The fold the shared timing helper applies to its vocabularies: a
        token that reads the same to a person is the same token."""
        event = translate_typeless(transceiver_class=declared)
        assert event["payload"]["features"]["ais_transceiver_class"] == token

    def test_a_typeless_record_that_declares_no_class_is_refused(self):
        """A position alone does not show a vessel's report: base stations,
        aids to navigation and SAR aircraft report positions too, and this
        adapter consumes none of them."""
        assert translate_typeless(transceiver_class=_ABSENT) is None

    @pytest.mark.parametrize("bad", ["", " ", "C", "AB", "A B", "SO", 1, True, None, ["A"], {"class": "A"}])
    def test_a_typeless_record_with_an_unusable_class_is_refused(self, bad):
        assert translate_typeless(transceiver_class=bad) is None

    @pytest.mark.parametrize("lat, lon", [(_ABSENT, _ABSENT), (91.0, 181.0), (95.0, 10.0), (10.0, 190.0), (None, None)])
    def test_a_typeless_record_with_no_usable_position_is_refused(self, lat, lon):
        """With no type to read, the position is the only evidence that the
        record is a position report: static and voyage data come from the
        same transceivers and carry none."""
        assert translate_typeless(lat=lat, lon=lon) is None

    @pytest.mark.parametrize("bad", ["1", "18", True, False, 1.0, 18.0, [1]])
    def test_a_type_that_is_present_but_not_an_integer_still_refuses(self, bad):
        """A present but impossible type is a decoder fault. A declared class
        does not rescue it, the same rule the adapter applies to a present
        but impossible time channel."""
        assert translate_typeless(type=bad) is None

    @pytest.mark.parametrize("mtype", [4, 5, 9, 21, 24])
    def test_a_type_outside_the_position_reports_still_refuses_with_a_class(self, mtype):
        assert translate_typeless(type=mtype) is None

    @pytest.mark.parametrize("mtype", [1, 18, 27])
    def test_a_typed_message_is_unchanged_when_it_also_carries_a_class(self, mtype):
        """The class is read only when the type is absent, so a typed
        message's output does not depend on it."""
        with_class = translate(type=mtype, transceiver_class="B")
        without = translate(type=mtype)
        assert "ais_transceiver_class" not in with_class["payload"]["features"]
        assert with_class["payload"]["features"]["ais_message_type"] == mtype
        for event in (with_class, without):
            del event["event"]["event_id"]
        assert with_class == without

    def test_the_general_sentinels_hold_on_a_typeless_record(self):
        features = translate_typeless(speed=102.3, course=360.0, heading=511)["payload"]["features"]
        assert "ais_sog_kt" not in features
        assert "ais_cog_deg_true" not in features
        assert "ais_heading_deg_true" not in features

    @pytest.mark.parametrize("declared", ["A", "B"])
    def test_message_27s_sentinels_hold_on_a_typeless_record(self, declared):
        """With no type, the record may be a message 27, whatever its class,
        so its not-available encodings apply as well (adapters/AUTHORING.md:
        read the table for each message type the code path accepts). 63 kt
        is dropped although a Class A or Class B report of another type would
        mean it; a real 63 kt is lost, and no vessel is shown making a speed
        it never reported. The speed half tests the sentinel. The course half
        holds on every path, since 511 is outside the course bound."""
        features = translate_typeless(transceiver_class=declared, speed=63.0, course=511.0)["payload"]["features"]
        assert "ais_sog_kt" not in features
        assert "ais_cog_deg_true" not in features

    @pytest.mark.parametrize("speed", [62.0, 63.5, 70.0, 102.2])
    def test_other_speeds_on_a_typeless_record_are_carried(self, speed):
        """Only the exact message 27 sentinel is dropped. A speed above 62 kt
        cannot come out of message 27's field, so it is read with the general
        bound."""
        assert translate_typeless(speed=speed)["payload"]["features"]["ais_sog_kt"] == speed

    @pytest.mark.parametrize("bad", [0, -1, "366123456", _ABSENT])
    def test_a_typeless_record_still_needs_a_usable_mmsi(self, bad):
        assert translate_typeless(mmsi=bad) is None

    def test_a_typeless_record_still_needs_a_reception_time(self):
        """No `rxtime`, no `timestamp` and no caller clock: no time to date the
        event, so no event, as for a typed message."""
        assert translate_message(typeless(rxtime=_ABSENT), platform_id="ais-node-01") is None

    def test_a_typeless_event_validates_against_the_schema_its_stamp_names(self):
        event = translate_typeless()
        assert event["zmeta_version"] == "1.1.0"
        errors = sorted(VALIDATOR_1_1_0.iter_errors(event), key=lambda e: list(e.path))
        assert not errors, f"schema-invalid: {errors[0].message}"

    def test_a_typeless_event_yields_a_two_dimensional_track(self):
        from adapters.projector.track.track_projector import TrackProjector

        projector = TrackProjector(platform_id="ais-node-01", confidence=0.9)
        event = translate_typeless(transceiver_class="B")
        assert projector.identity_of(event) == "mmsi-366123456"
        fusion, state = projector.observe(event)
        assert fusion["event"]["event_type"] == "FUSION_EVENT"
        assert state["payload"]["geo"] == {
            "lat": 33.7405,
            "lon": -118.2712,
            "dimensionality": "2D",
        }
        assert projector.stats["projected_2d"] == 1

    def test_a_mixed_stream_keeps_the_typed_and_the_declared_records(self):
        messages = [
            msg(),
            typeless(mmsi=338111222, transceiver_class="B"),
            typeless(mmsi=338111333, transceiver_class=_ABSENT),
            typeless(mmsi=338111444, lat=91.0, lon=181.0),
            msg(type=5, mmsi=338111555),
        ]
        events = translate_stream(messages, **BASE)
        assert [e["payload"]["features"]["ais_mmsi"] for e in events] == [366123456, 338111222]
        assert events[0]["payload"]["features"]["ais_message_type"] == 1
        assert "ais_transceiver_class" not in events[0]["payload"]["features"]
        assert events[1]["payload"]["features"]["ais_transceiver_class"] == "B"
        assert "ais_message_type" not in events[1]["payload"]["features"]


# The reference validator and policy, loaded the way the MAVLink and SAPIENT
# ingress suites load them (adapters/ingress/mavlink/test_mavlink_ingress.py).
_VALIDATORS_PATH = ROOT / "gateway" / "src" / "validators.py"
_validators_spec = importlib.util.spec_from_file_location("zmeta_validators", _VALIDATORS_PATH)
gateway_validators = importlib.util.module_from_spec(_validators_spec)
_validators_spec.loader.exec_module(gateway_validators)
GATEWAY_POLICY = gateway_validators.load_policy(ROOT / "policy")
_UNION_SCHEMA = gateway_validators.load_schema(SCHEMA_DIR / "zmeta-event.schema.json")
_LANE_SCHEMAS = {
    "1.0": gateway_validators.load_schema(SCHEMA_DIR / "zmeta-event-1.0.schema.json"),
    "1.1.0": gateway_validators.load_schema(SCHEMA_DIR / "zmeta-event-1.1.0.schema.json"),
}


def reference_violations(event, profile):
    """Every violation the reference schema-and-policy validation reports for
    one event at one profile, as (severity, code) pairs, in the order
    `tools/validate.py` runs its checks: the schema of the lane the event's
    stamp names, then, when the schema passes, the role, profile, timing,
    semantics, lineage, producer-authority, routing and deduplication
    checks, with a fresh validation state. An empty list is a pass with no
    warning."""
    severity_map = GATEWAY_POLICY.get("violation_severities", {})
    version = event.get("zmeta_version")
    schema = _LANE_SCHEMAS.get(version) if isinstance(version, str) else None
    _ok, violations = gateway_validators.validate_schema(event, schema or _UNION_SCHEMA, severity_map)
    found = [("warn" if v.get("severity") == "warn" else "fail", v["code"]) for v in violations]
    if found:
        return found
    policy = GATEWAY_POLICY
    state = gateway_validators.ValidationState()
    checks = [
        gateway_validators.validate_role(event, {"roles": policy["roles"], "deny": policy["deny"]}, severity_map),
        gateway_validators.validate_profile(event, profile, policy["profiles"], severity_map),
        gateway_validators.validate_timing_quality(
            event,
            policy["semantics"],
            state=state,
            severity_map=severity_map,
            timing_freshness_policy=policy.get("timing_freshness", {}),
            profile=profile,
        ),
        gateway_validators.validate_semantics(event, policy["semantics"], severity_map),
        gateway_validators.validate_lineage(
            event, policy.get("lineage", {}), state=state, profile=profile, severity_map=severity_map
        ),
        gateway_validators.validate_producer_authority(event, policy.get("producer_authority", {}), severity_map),
        gateway_validators.validate_routing(event, policy["routing"], severity_map),
        gateway_validators.validate_deduplication(event, state=state, severity_map=severity_map),
    ]
    for _ok, violations in checks:
        found.extend(("warn" if v.get("severity") == "warn" else "fail", v["code"]) for v in violations)
    return found


class TestTypelessEventAtTheReferenceValidator:
    """The schema test above checks the 1.1.0 schema only, and the adapter
    harness corpus holds the typed shapes only. These hold the typeless event
    to the reference schema-and-policy validation at profiles H and M, so a
    change to how the observation deny-list matches key names that refused
    `ais_transceiver_class` at the gateway fails here, in the adapter's own
    tests. The two controls show that the same validation refuses the class
    under a name the policy reserves for identity: `class_name`, which the
    1.1.0 schema refuses, and `Entity_Class`, a case-varied copy of
    `entity_class` that the schema passes and the policy's normalised
    deny-list refuses."""

    @staticmethod
    def _renamed(new_key):
        event = translate_typeless()
        features = event["payload"]["features"]
        features[new_key] = features.pop("ais_transceiver_class")
        return event

    @pytest.mark.parametrize("profile", ["H", "M"])
    def test_a_typeless_event_passes_the_reference_validation(self, profile):
        event = translate_typeless()
        assert "ais_transceiver_class" in event["payload"]["features"]
        assert reference_violations(event, profile) == []

    @pytest.mark.parametrize("profile", ["H", "M"])
    def test_the_class_renamed_class_name_is_refused(self, profile):
        found = reference_violations(self._renamed("class_name"), profile)
        assert found, "the validation passed an observation carrying class_name"
        assert {code for _, code in found} == {"SCHEMA_INVALID"}, found
        assert all(severity == "fail" for severity, _ in found), found

    @pytest.mark.parametrize("profile", ["H", "M"])
    def test_the_class_renamed_entity_class_is_refused_as_identity(self, profile):
        assert reference_violations(self._renamed("Entity_Class"), profile) == [
            ("fail", "OBSERVATION_HAS_IDENTITY")
        ]
