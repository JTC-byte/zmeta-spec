"""TAK Protocol Version 1 egress: the ZMeta CoT projection encoded as the TAK
protobuf wire form, mesh or stream framed.

The adapter is a wire step over `adapters/egress/cot/zmeta_to_cot.py`: every
refusal and both profiles of the CoT projection are inherited, and these tests
check only what the encoding adds. The known-answer test holds the expected
bytes for one small CoT event, computed by hand in this file from the TAK
Protocol Version 1 field numbers (TakMessage.cotEvent = 2; CotEvent type 1,
uid 5, sendTime 6, startTime 7, staleTime 8, how 9, lat 10, lon 11, hae 12,
ce 13, le 14, detail 15; Detail xmlDetail 1, contact 2, group 3,
precisionLocation 4, status 5, takv 6, track 7; Contact callsign 2; Track
speed 1, course 2), so it does not depend on the encoder's own tables. The
in-module reader is exercised as a second, dependent check and has its own
negative controls. A cross-check against the MIT-licensed `takproto` package
runs only when the environment variable `TAK_PROTO_SITE` names a directory
that holds it and `google.protobuf`; the repository vendors neither.

WHAT THIS FILE DOES NOT PROVE: that any TAK client or server accepts the
bytes. The recce of 2026-11-03 parsed the same shape back through takproto
(809 of 809 and 1680 of 1680 events, no field mismatch); no client or server
was driven.
"""
import importlib
import importlib.util
import os
import struct
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = ROOT / "adapters" / "egress" / "tak_protocol" / "zmeta_to_tak_protocol.py"
spec = importlib.util.spec_from_file_location("zmeta_to_tak_protocol_module", MODULE_PATH)
tak = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tak)

COT_PATH = ROOT / "adapters" / "egress" / "cot" / "zmeta_to_cot.py"
cot_spec = importlib.util.spec_from_file_location("zmeta_to_cot_for_tak_tests", COT_PATH)
cot = importlib.util.module_from_spec(cot_spec)
cot_spec.loader.exec_module(cot)


# --- independent helpers (not the module's) ---------------------------------

def _varint(value):
    """Protobuf base-128 varint, written here so the expected bytes do not come
    from the code under test."""
    out = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            out.append(byte | 0x80)
        else:
            out.append(byte)
            return bytes(out)


def _ms(stamp):
    dt = datetime.fromisoformat(stamp.replace("Z", "+00:00")).astimezone(timezone.utc)
    return int(dt.timestamp() * 1000)


def _ld(field, payload):
    """A length-delimited field: key (wire type 2), length, bytes."""
    return _varint((field << 3) | 2) + _varint(len(payload)) + payload


def _str(field, text):
    return _ld(field, text.encode("utf-8"))


def _u64(field, value):
    return _varint((field << 3) | 0) + _varint(value)


def _dbl(field, value):
    return _varint((field << 3) | 1) + struct.pack("<d", value)


# --- fixtures ----------------------------------------------------------------

KNOWN_XML = (
    '<event version="2.0" type="a-u-G" uid="t1" time="2026-01-17T14:30:05.000000Z"'
    ' start="2026-01-17T14:30:05.000000Z" stale="2026-01-17T14:31:05.000000Z" how="m-g">\n'
    '  <point lat="43.5" lon="-112.25" hae="1500.0" le="9999999.0" ce="150.0" />\n'
    '  <detail>\n'
    '    <contact callsign="Track t1" />\n'
    '    <remarks>confidence=0.82</remarks>\n'
    '    <track course="135.0" speed="12.5" />\n'
    '  </detail>\n'
    '</event>'
)

KNOWN_MESSAGE = _ld(
    2,
    _str(1, "a-u-G")
    + _str(5, "t1")
    + _u64(6, _ms("2026-01-17T14:30:05Z"))
    + _u64(7, _ms("2026-01-17T14:30:05Z"))
    + _u64(8, _ms("2026-01-17T14:31:05Z"))
    + _str(9, "m-g")
    + _dbl(10, 43.5)
    + _dbl(11, -112.25)
    + _dbl(12, 1500.0)
    + _dbl(13, 150.0)
    + _dbl(14, 9999999.0)
    + _ld(
        15,
        _str(1, "<remarks>confidence=0.82</remarks>")
        + _ld(2, _str(2, "Track t1"))
        + _ld(7, _dbl(1, 12.5) + _dbl(2, 135.0)),
    ),
)


# Every typed field at once, so a wrong field number anywhere in the tables
# changes these bytes. Computed by hand from the schema, as KNOWN_MESSAGE is.
ALL_TYPED_XML = (
    '<event version="2.0" type="a-f-G" access="Undefined" qos="1-r-c" opex="e" uid="t2"'
    ' time="2026-01-17T14:30:05.000000Z" start="2026-01-17T14:30:05.000000Z"'
    ' stale="2026-01-17T14:31:05.000000Z" how="m-g">\n'
    '  <point lat="43.5" lon="-112.25" hae="1500.0" le="9999999.0" ce="150.0" />\n'
    '  <detail>\n'
    '    <contact endpoint="192.0.2.1:4242:tcp" callsign="Track t2" />\n'
    '    <__group name="Cyan" role="Team Member" />\n'
    '    <precisionlocation geopointsrc="GPS" altsrc="DTED0" />\n'
    '    <status battery="77" />\n'
    '    <takv device="x" platform="ATAK" os="34" version="5.1" />\n'
    '    <track course="135.0" speed="12.5" />\n'
    '  </detail>\n'
    '</event>'
)

ALL_TYPED_MESSAGE = _ld(
    2,
    _str(1, "a-f-G")
    + _str(2, "Undefined")
    + _str(3, "1-r-c")
    + _str(4, "e")
    + _str(5, "t2")
    + _u64(6, _ms("2026-01-17T14:30:05Z"))
    + _u64(7, _ms("2026-01-17T14:30:05Z"))
    + _u64(8, _ms("2026-01-17T14:31:05Z"))
    + _str(9, "m-g")
    + _dbl(10, 43.5)
    + _dbl(11, -112.25)
    + _dbl(12, 1500.0)
    + _dbl(13, 150.0)
    + _dbl(14, 9999999.0)
    + _ld(
        15,
        _ld(2, _str(1, "192.0.2.1:4242:tcp") + _str(2, "Track t2"))
        + _ld(3, _str(1, "Cyan") + _str(2, "Team Member"))
        + _ld(4, _str(1, "GPS") + _str(2, "DTED0"))
        + _ld(5, _u64(1, 77))
        + _ld(6, _str(1, "x") + _str(2, "ATAK") + _str(3, "34") + _str(4, "5.1"))
        + _ld(7, _dbl(1, 12.5) + _dbl(2, 135.0)),
    ),
)


def state_event(**overrides):
    """A schema-valid 1.1.0 STATE_EVENT with heading, speed and an ellipse."""
    event = {
        "zmeta_version": "1.1.0",
        "event": {
            "event_id": "019c2b5c-c046-70e1-b6aa-34bf14c8a247",
            "event_type": "STATE_EVENT",
            "event_subtype": "TRACK_STATE",
            "ts": "2026-01-17T14:30:05Z",
        },
        "source": {"platform_id": "gateway-01", "node_role": "GATEWAY", "producer": "fusion-engine"},
        "payload": {
            "track_id": "emitter-01",
            "class": "a-u-G",
            "geo": {
                "lat": 43.49,
                "lon": -112.04,
                "alt_m": 1500,
                "error_ellipse_m": {"semi_major": 150.0, "semi_minor": 80.0, "orientation_deg": 45.0},
            },
            "valid_for_ms": 60000,
            "heading_deg": 135.0,
            "speed_mps": 12.5,
        },
        "confidence": 0.82,
        "lineage": {"based_on": ["019c2b5c-88f0-7aa1-9b3e-5d2c41f0a9d2"]},
    }
    for key, value in overrides.items():
        event["payload"][key] = value
    return event


def vessel_2d_event():
    """A declared 2-D fix: the CoT projection emits the geo_dimensionality marker."""
    event = state_event()
    event["payload"]["geo"] = {
        "lat": 12.3456,
        "lon": -45.6789,
        "dimensionality": "2D",
        "error_ellipse_m": {"semi_major": 35.0, "semi_minor": 12.0, "orientation_deg": 80.0},
    }
    event["payload"]["quality"] = {"geo_status": "VERTICAL_UNAVAILABLE"}
    event["payload"]["class"] = "a-u-S"
    return event


# --- constants and framing ---------------------------------------------------

def test_module_constants():
    assert tak.ADAPTER_VERSION
    assert tak.MESH_HEADER == b"\xbf\x01\xbf"
    assert tak.STREAM_HEADER == b"\xbf"
    assert tak.FRAMINGS == ("mesh", "stream", "none")


def test_known_answer_unframed_bytes():
    assert tak.cot_xml_to_tak_message(KNOWN_XML) == KNOWN_MESSAGE


def test_known_answer_every_typed_field():
    assert tak.cot_xml_to_tak_message(ALL_TYPED_XML) == ALL_TYPED_MESSAGE


def test_negative_zero_keeps_its_sign():
    """protobuf compares the bits, so -0.0 is not the default and is written."""
    xml = KNOWN_XML.replace('lat="43.5"', 'lat="-0.0"')
    message = tak.cot_xml_to_tak_message(xml)
    # the same length, so the known bytes with one double swapped are the expectation
    assert message == KNOWN_MESSAGE.replace(_dbl(10, 43.5), _dbl(10, -0.0))
    assert struct.pack("<d", tak.read_tak_message(message)["cotEvent"]["lat"]) == struct.pack("<d", -0.0)
    zero = tak.cot_xml_to_tak_message(KNOWN_XML.replace('lat="43.5"', 'lat="0.0"'))
    assert "lat" not in tak.read_tak_message(zero)["cotEvent"]


def test_mesh_framing_is_header_plus_message():
    assert tak.frame_mesh(KNOWN_MESSAGE) == b"\xbf\x01\xbf" + KNOWN_MESSAGE


def test_stream_framing_is_header_varint_length_message():
    assert len(KNOWN_MESSAGE) > 127, "the fixture must need a two-byte varint length"
    assert tak.frame_stream(KNOWN_MESSAGE) == b"\xbf" + _varint(len(KNOWN_MESSAGE)) + KNOWN_MESSAGE
    short = b"\x12\x02\x0a\x00"
    assert tak.frame_stream(short) == b"\xbf" + bytes([len(short)]) + short


def test_zmeta_to_tak_protocol_frames_the_cot_projection():
    event = state_event()
    xml = cot.zmeta_to_cot(event, cot_config={"how": "m-g"})
    message = tak.cot_xml_to_tak_message(xml)
    assert message is not None
    assert tak.zmeta_to_tak_protocol(event, cot_config={"how": "m-g"}) == b"\xbf\x01\xbf" + message
    assert tak.zmeta_to_tak_protocol(event, cot_config={"how": "m-g"}, framing="stream") == tak.frame_stream(message)
    assert tak.zmeta_to_tak_protocol(event, cot_config={"how": "m-g"}, framing="none") == message


def test_unknown_framing_is_refused():
    with pytest.raises(ValueError):
        tak.validate_framing("datagram")
    assert tak.zmeta_to_tak_protocol(state_event(), cot_config={"how": "m-g"}, framing="datagram") is None


# --- the reader as a second check --------------------------------------------

def test_reader_round_trips_the_known_message_on_both_framings():
    for framed in (tak.frame_mesh(KNOWN_MESSAGE), tak.frame_stream(KNOWN_MESSAGE), KNOWN_MESSAGE):
        read = tak.read_tak_message(framed)
        ev = read["cotEvent"]
        assert ev["type"] == "a-u-G"
        assert ev["uid"] == "t1"
        assert ev["how"] == "m-g"
        assert ev["sendTime"] == ev["startTime"] == _ms("2026-01-17T14:30:05Z")
        assert ev["staleTime"] == _ms("2026-01-17T14:31:05Z")
        assert (ev["lat"], ev["lon"], ev["hae"], ev["ce"], ev["le"]) == (43.5, -112.25, 1500.0, 150.0, 9999999.0)
        detail = ev["detail"]
        assert detail["xmlDetail"] == "<remarks>confidence=0.82</remarks>"
        assert detail["contact"] == {"callsign": "Track t1"}
        assert detail["track"] == {"speed": 12.5, "course": 135.0}
        assert "takControl" not in read


def test_reader_refuses_an_unknown_field_number():
    unknown = KNOWN_MESSAGE + _str(99, "x")
    with pytest.raises(ValueError):
        tak.read_tak_message(unknown)


def test_reader_refuses_a_truncated_stream_frame():
    framed = tak.frame_stream(KNOWN_MESSAGE)
    with pytest.raises(ValueError):
        tak.read_tak_message(framed[:-3])


def test_reader_refuses_a_wrong_wire_type():
    # lat (field 10) as a varint instead of a double
    bad = _ld(2, _str(1, "a-u-G") + _u64(10, 5))
    with pytest.raises(ValueError):
        tak.read_tak_message(bad)


def test_reader_refuses_a_repeated_field():
    with pytest.raises(ValueError):
        tak.read_tak_message(_ld(2, _str(1, "a-u-G") + _str(1, "a-u-G")))
    with pytest.raises(ValueError):
        tak.read_tak_message(KNOWN_MESSAGE + KNOWN_MESSAGE)


def test_reader_refuses_trailing_bytes_after_a_stream_frame():
    with pytest.raises(ValueError):
        tak.read_tak_message(tak.frame_stream(KNOWN_MESSAGE) + b"\x00")


def test_reader_refuses_a_string_that_is_not_utf8():
    with pytest.raises(ValueError):
        tak.read_tak_message(_ld(2, _ld(1, b"\xff\xfe")))


def test_reader_refuses_a_varint_wider_than_64_bits():
    # ten bytes whose last carries more than the one bit a uint64 has room for
    wide = _ld(2, bytes([0x30]) + b"\xff" * 9 + b"\x7f")
    with pytest.raises(ValueError):
        tak.read_tak_message(wide)
    assert tak.read_tak_message(_ld(2, _u64(6, 2**64 - 1)))["cotEvent"]["sendTime"] == 2**64 - 1


def test_reader_refuses_empty_input_and_reads_an_empty_mesh_frame():
    with pytest.raises(ValueError):
        tak.read_tak_message(b"")
    assert tak.read_tak_message(b"\xbf\x01\xbf") == {}


def test_refusal_dict_names_the_encoding_when_the_projection_passed():
    """The CoT projection accepts a 1969 instant; the uint64 times cannot."""
    event = state_event()
    event["event"]["ts"] = "1969-12-31T23:59:59Z"
    refusal = {}
    xml = cot.zmeta_to_cot(event, cot_config={"how": "m-g"})
    if xml is None:
        pytest.skip("this platform's CoT projection refuses a pre-1970 instant itself")
    assert tak.zmeta_to_tak_protocol(event, cot_config={"how": "m-g"}, refusal=refusal) is None
    assert refusal == {"reason": "TAK_PROTOCOL_UNREPRESENTABLE"}
    clean = {}
    assert tak.zmeta_to_tak_protocol(state_event(), cot_config={"how": "m-g"}, refusal=clean) is not None
    assert clean == {}


# --- what the detail carries -------------------------------------------------

def test_untyped_children_ride_xml_detail_in_document_order():
    event = vessel_2d_event()
    xml = cot.zmeta_to_cot(event, cot_config={"how": "m-g"})
    assert "<geo_dimensionality" in xml and "<remarks>" in xml and "<track" in xml
    read = tak.read_tak_message(tak.zmeta_to_tak_protocol(event, cot_config={"how": "m-g"}))
    detail = read["cotEvent"]["detail"]
    xml_detail = detail["xmlDetail"]
    assert xml_detail.startswith("<remarks>")
    assert '<geo_dimensionality value="2D" geo_status="VERTICAL_UNAVAILABLE" />' in xml_detail
    assert xml_detail.index("<remarks>") < xml_detail.index("<geo_dimensionality")
    # typed children are typed, and never duplicated into xmlDetail
    assert "<contact" not in xml_detail and "<track" not in xml_detail
    assert detail["contact"] == {"callsign": "Track emitter-01"}
    assert detail["track"] == {"speed": 12.5, "course": 135.0}


def test_hostile_track_labels_on_rides_xml_detail():
    event = state_event()
    event["payload"]["class"] = "a-h-G"
    read = tak.read_tak_message(tak.zmeta_to_tak_protocol(event, cot_config={"how": "m-g"}))
    detail = read["cotEvent"]["detail"]
    assert '<labels_on value="true" />' in detail["xmlDetail"]
    assert detail["contact"] == {"callsign": "RF Emitter"}


def test_friendly_group_is_typed():
    event = state_event()
    event["payload"]["class"] = "a-f-G"
    read = tak.read_tak_message(
        tak.zmeta_to_tak_protocol(event, cot_config={"how": "m-g", "friendly_team_name": "Cyan", "friendly_team_role": "Team Member"})
    )
    detail = read["cotEvent"]["detail"]
    assert detail["group"] == {"name": "Cyan", "role": "Team Member"}
    assert "__group" not in detail["xmlDetail"]


def test_precisionlocation_with_ellipse_attributes_rides_xml_detail_whole():
    """The typed PrecisionLocation message holds geopointsrc and altsrc only.
    The CoT projection's element also carries the ellipse; a typed carrier
    would drop it, so the element travels whole in xmlDetail."""
    event = state_event()
    read = tak.read_tak_message(tak.zmeta_to_tak_protocol(event, cot_config={"how": "m-g", "geopointsrc": "GPS"}))
    detail = read["cotEvent"]["detail"]
    assert "precisionLocation" not in detail
    assert '<precisionlocation geopointsrc="GPS" ellipse_major="150.0" ellipse_minor="80.0" ellipse_angle="45.0" />' in detail["xmlDetail"]


def test_precisionlocation_with_only_typed_attributes_is_typed():
    xml = KNOWN_XML.replace("<remarks>confidence=0.82</remarks>", '<precisionlocation geopointsrc="GPS" altsrc="GPS" />')
    read = tak.read_tak_message(tak.cot_xml_to_tak_message(xml))
    detail = read["cotEvent"]["detail"]
    assert detail["precisionLocation"] == {"geopointsrc": "GPS", "altsrc": "GPS"}
    assert "xmlDetail" not in detail


def test_status_and_takv_are_typed_when_lossless():
    xml = KNOWN_XML.replace(
        "<remarks>confidence=0.82</remarks>",
        '<status battery="77" /><takv device="x" platform="ATAK" os="34" version="5.1" />',
    )
    detail = tak.read_tak_message(tak.cot_xml_to_tak_message(xml))["cotEvent"]["detail"]
    assert detail["status"] == {"battery": 77}
    assert detail["takv"] == {"device": "x", "platform": "ATAK", "os": "34", "version": "5.1"}
    assert "xmlDetail" not in detail


def test_typed_child_with_an_extra_attribute_rides_xml_detail_whole():
    xml = KNOWN_XML.replace('<contact callsign="Track t1" />', '<contact callsign="Track t1" phone="555" />')
    detail = tak.read_tak_message(tak.cot_xml_to_tak_message(xml))["cotEvent"]["detail"]
    assert "contact" not in detail
    assert '<contact callsign="Track t1" phone="555" />' in detail["xmlDetail"]


def test_typed_child_with_an_empty_attribute_rides_xml_detail_whole():
    """proto3 cannot tell an empty string from an absent one, so an element
    carrying an empty attribute is not represented by the typed field."""
    xml = KNOWN_XML.replace('<contact callsign="Track t1" />', '<contact callsign="" />')
    detail = tak.read_tak_message(tak.cot_xml_to_tak_message(xml))["cotEvent"]["detail"]
    assert "contact" not in detail
    assert '<contact callsign="" />' in detail["xmlDetail"]


def test_track_with_one_numeric_attribute_rides_xml_detail_whole():
    """An absent double would read back as 0, a value; the element is carried
    whole instead. A status of battery 0 is typed: its one field reads as 0."""
    xml = KNOWN_XML.replace('<track course="135.0" speed="12.5" />', '<track course="90.0" />')
    detail = tak.read_tak_message(tak.cot_xml_to_tak_message(xml))["cotEvent"]["detail"]
    assert "track" not in detail
    assert '<track course="90.0" />' in detail["xmlDetail"]
    xml = KNOWN_XML.replace("<remarks>confidence=0.82</remarks>", '<status battery="0" />')
    detail = tak.read_tak_message(tak.cot_xml_to_tak_message(xml))["cotEvent"]["detail"]
    assert detail["status"] == {}


def test_a_second_element_of_a_typed_kind_that_does_not_qualify_rides_xml_detail():
    xml = KNOWN_XML.replace(
        '<contact callsign="Track t1" />', '<contact callsign="Track t1" phone="555" /><contact callsign="other" />'
    )
    detail = tak.read_tak_message(tak.cot_xml_to_tak_message(xml))["cotEvent"]["detail"]
    assert detail["contact"] == {"callsign": "other"}
    assert '<contact callsign="Track t1" phone="555" />' in detail["xmlDetail"]


def test_typed_child_with_text_or_children_rides_xml_detail_whole():
    xml = KNOWN_XML.replace('<contact callsign="Track t1" />', '<contact callsign="Track t1"><x/></contact>')
    detail = tak.read_tak_message(tak.cot_xml_to_tak_message(xml))["cotEvent"]["detail"]
    assert "contact" not in detail
    assert "<contact" in detail["xmlDetail"] and "<x />" in detail["xmlDetail"]


def test_no_detail_means_no_detail_field():
    xml = (
        '<event version="2.0" type="a-u-G" uid="t1" time="2026-01-17T14:30:05Z"'
        ' start="2026-01-17T14:30:05Z" stale="2026-01-17T14:31:05Z" how="m-g">'
        '<point lat="43.5" lon="-112.25" hae="1500.0" le="9999999.0" ce="150.0" /></event>'
    )
    message = tak.cot_xml_to_tak_message(xml)
    assert message is not None
    assert "detail" not in tak.read_tak_message(message)["cotEvent"]


def test_detail_formatting_whitespace_is_dropped_but_element_text_is_kept():
    xml = KNOWN_XML.replace("<remarks>confidence=0.82</remarks>", "<remarks>a &amp; b; c</remarks>")
    detail = tak.read_tak_message(tak.cot_xml_to_tak_message(xml))["cotEvent"]["detail"]
    assert detail["xmlDetail"] == "<remarks>a &amp; b; c</remarks>"


# --- times -------------------------------------------------------------------

def test_times_floor_to_the_millisecond_and_stale_never_lengthens():
    xml = KNOWN_XML.replace('time="2026-01-17T14:30:05.000000Z"', 'time="2026-01-17T14:30:05.999999Z"').replace(
        'stale="2026-01-17T14:31:05.000000Z"', 'stale="2026-01-17T14:31:05.000999Z"'
    )
    ev = tak.read_tak_message(tak.cot_xml_to_tak_message(xml))["cotEvent"]
    assert ev["sendTime"] == _ms("2026-01-17T14:30:05Z") + 999
    assert ev["staleTime"] == _ms("2026-01-17T14:31:05Z")  # the 999 microseconds are dropped, never rounded up


def test_a_time_before_1970_is_refused():
    xml = KNOWN_XML.replace('start="2026-01-17T14:30:05.000000Z"', 'start="1969-12-31T23:59:59.000000Z"')
    assert tak.cot_xml_to_tak_message(xml) is None


def test_a_missing_or_unparseable_time_is_refused():
    assert tak.cot_xml_to_tak_message(KNOWN_XML.replace(' stale="2026-01-17T14:31:05.000000Z"', "")) is None
    assert tak.cot_xml_to_tak_message(KNOWN_XML.replace('stale="2026-01-17T14:31:05.000000Z"', 'stale="soon"')) is None
    assert tak.cot_xml_to_tak_message(KNOWN_XML.replace('time="2026-01-17T14:30:05.000000Z"', 'time="2026-01-17T14:30:05"')) is None


# --- refusals ----------------------------------------------------------------

def test_non_state_event_is_refused():
    event = state_event()
    event["event"]["event_type"] = "OBSERVATION_EVENT"
    assert tak.zmeta_to_tak_protocol(event, cot_config={"how": "m-g"}) is None


def test_cot_refusal_is_inherited():
    event = state_event()
    del event["payload"]["geo"]
    assert tak.zmeta_to_tak_protocol(event, cot_config={"how": "m-g"}) is None


def test_malformed_xml_is_refused():
    assert tak.cot_xml_to_tak_message("<event this is not xml") is None
    assert tak.cot_xml_to_tak_message("") is None
    assert tak.cot_xml_to_tak_message(None) is None


def test_root_that_is_not_an_event_is_refused():
    assert tak.cot_xml_to_tak_message("<point lat='1' lon='2' hae='0' ce='1' le='1'/>") is None


def test_version_other_than_2_0_is_refused():
    assert tak.cot_xml_to_tak_message(KNOWN_XML.replace('version="2.0"', 'version="3.0"')) is None
    assert tak.cot_xml_to_tak_message(KNOWN_XML.replace('version="2.0" ', "")) is None


def test_an_event_attribute_with_no_carrier_is_refused():
    assert tak.cot_xml_to_tak_message(KNOWN_XML.replace('how="m-g"', 'how="m-g" foo="bar"')) is None


def test_a_point_attribute_with_no_carrier_is_refused():
    assert tak.cot_xml_to_tak_message(KNOWN_XML.replace('ce="150.0" />', 'ce="150.0" extra="1" />')) is None


def test_a_missing_point_or_point_attribute_is_refused():
    no_point = KNOWN_XML.replace('  <point lat="43.5" lon="-112.25" hae="1500.0" le="9999999.0" ce="150.0" />\n', "")
    assert tak.cot_xml_to_tak_message(no_point) is None
    assert tak.cot_xml_to_tak_message(KNOWN_XML.replace(' hae="1500.0"', "")) is None


def test_a_point_value_that_is_not_a_finite_number_is_refused():
    assert tak.cot_xml_to_tak_message(KNOWN_XML.replace('lat="43.5"', 'lat="nan"')) is None
    assert tak.cot_xml_to_tak_message(KNOWN_XML.replace('lat="43.5"', 'lat="inf"')) is None
    assert tak.cot_xml_to_tak_message(KNOWN_XML.replace('lat="43.5"', 'lat="north"')) is None


def test_a_typed_numeric_attribute_that_is_not_a_number_is_refused():
    assert tak.cot_xml_to_tak_message(KNOWN_XML.replace('course="135.0"', 'course="east"')) is None
    assert tak.cot_xml_to_tak_message(KNOWN_XML.replace('course="135.0"', 'course="nan"')) is None
    bad_battery = KNOWN_XML.replace("<remarks>confidence=0.82</remarks>", '<status battery="-1" />')
    assert tak.cot_xml_to_tak_message(bad_battery) is None
    bad_battery = KNOWN_XML.replace("<remarks>confidence=0.82</remarks>", '<status battery="4294967296" />')
    assert tak.cot_xml_to_tak_message(bad_battery) is None


def test_two_elements_of_one_typed_kind_are_refused():
    xml = KNOWN_XML.replace('<contact callsign="Track t1" />', '<contact callsign="Track t1" /><contact callsign="other" />')
    assert tak.cot_xml_to_tak_message(xml) is None


def test_a_child_of_event_other_than_point_and_detail_is_refused():
    assert tak.cot_xml_to_tak_message(KNOWN_XML.replace("</event>", "<extra/></event>")) is None


def test_text_directly_inside_detail_is_refused():
    assert tak.cot_xml_to_tak_message(KNOWN_XML.replace("<detail>\n", "<detail>\n    loose words\n")) is None


def test_a_comment_or_processing_instruction_is_refused_rather_than_dropped():
    assert tak.cot_xml_to_tak_message(KNOWN_XML.replace("<detail>\n", "<detail>\n    <!-- note -->\n")) is None
    assert tak.cot_xml_to_tak_message(KNOWN_XML.replace("<detail>\n", "<detail>\n    <?pi x?>\n")) is None
    # outside the root element too, where the parser would drop them in silence
    assert tak.cot_xml_to_tak_message("<!-- before -->" + KNOWN_XML) is None
    assert tak.cot_xml_to_tak_message(KNOWN_XML + "<!-- after -->") is None
    assert tak.cot_xml_to_tak_message("<?pi x?>" + KNOWN_XML) is None
    assert tak.cot_xml_to_tak_message('<!DOCTYPE event [<!ENTITY e "x">]>' + KNOWN_XML) is None
    # the XML declaration is not a processing instruction and passes
    assert tak.cot_xml_to_tak_message('<?xml version="1.0" encoding="UTF-8"?>\n' + KNOWN_XML) == KNOWN_MESSAGE
    assert tak.cot_xml_to_tak_message(KNOWN_XML.encode("utf-8")) == KNOWN_MESSAGE


def test_empty_optional_event_attributes_are_refused_not_defaulted():
    """proto3 writes no field for an empty string, so a present-but-empty
    `access` would read back as absent. The adapter refuses rather than send a
    claim that cannot be told from no claim."""
    assert tak.cot_xml_to_tak_message(KNOWN_XML.replace('how="m-g"', 'how="m-g" access="Undefined"')) is not None
    assert tak.cot_xml_to_tak_message(KNOWN_XML.replace('how="m-g"', 'how="m-g" access=""')) is None


def test_access_qos_opex_are_carried():
    xml = KNOWN_XML.replace('how="m-g"', 'how="m-g" access="Undefined" qos="1-r-c" opex="e"')
    ev = tak.read_tak_message(tak.cot_xml_to_tak_message(xml))["cotEvent"]
    assert (ev["access"], ev["qos"], ev["opex"]) == ("Undefined", "1-r-c", "e")


def test_how_absent_is_absent_on_the_wire():
    xml = KNOWN_XML.replace(' how="m-g"', "")
    ev = tak.read_tak_message(tak.cot_xml_to_tak_message(xml))["cotEvent"]
    assert "how" not in ev


# --- the cds profile passes through ------------------------------------------

def test_cds_profile_output_encodes():
    now = datetime(2026, 1, 17, 14, 30, 20, tzinfo=timezone.utc)
    event = vessel_2d_event()
    config = {"profile": "cds", "how": "m-f", "stale_window_s": 120}
    xml = cot.zmeta_to_cot(event, cot_config=config, now=now)
    assert xml is not None
    framed = tak.zmeta_to_tak_protocol(event, cot_config=config, now=now)
    ev = tak.read_tak_message(framed)["cotEvent"]
    assert ev["how"] == "m-f"
    assert ev["detail"]["contact"] == {"callsign": "Track emitter-01"}
    assert "track via ZMeta; affiliation not asserted; confidence=0.82; 2-D fix, altitude not asserted" in ev["detail"]["xmlDetail"]
    assert "<geo_dimensionality" not in ev["detail"]["xmlDetail"]
    assert ev["staleTime"] == _ms("2026-01-17T14:31:05Z")  # the event's own claim, earlier than now + 120 s


# --- optional cross-check against takproto -----------------------------------

def _takproto():
    site = os.environ.get("TAK_PROTO_SITE")
    if not site or not Path(site).is_dir():
        return None
    if site not in sys.path:
        sys.path.insert(0, site)
    try:
        return importlib.import_module("takproto")
    except Exception:  # noqa: BLE001 - any import failure means "not available"
        return None


@pytest.mark.skipif(_takproto() is None, reason="TAK_PROTO_SITE does not name a directory holding takproto")
def test_bytes_match_takproto_for_the_known_event():
    takproto = _takproto()
    theirs = bytes(takproto.xml2proto(KNOWN_XML, takproto.TAKProtoVer.MESH))
    assert tak.frame_mesh(tak.cot_xml_to_tak_message(KNOWN_XML)) == theirs
    theirs_stream = bytes(takproto.xml2proto(KNOWN_XML, takproto.TAKProtoVer.STREAM))
    assert tak.frame_stream(tak.cot_xml_to_tak_message(KNOWN_XML)) == theirs_stream
    all_typed = bytes(takproto.xml2proto(ALL_TYPED_XML, takproto.TAKProtoVer.MESH))
    assert tak.frame_mesh(tak.cot_xml_to_tak_message(ALL_TYPED_XML)) == all_typed
    negative_zero = bytes(takproto.xml2proto(KNOWN_XML.replace('lat="43.5"', 'lat="-0.0"'), takproto.TAKProtoVer.MESH))
    assert tak.frame_mesh(tak.cot_xml_to_tak_message(KNOWN_XML.replace('lat="43.5"', 'lat="-0.0"'))) == negative_zero


@pytest.mark.skipif(_takproto() is None, reason="TAK_PROTO_SITE does not name a directory holding takproto")
def test_takproto_parses_the_projection_of_a_declared_2d_vessel():
    takproto = _takproto()
    event = vessel_2d_event()
    framed = tak.zmeta_to_tak_protocol(event, cot_config={"how": "m-g"})
    parsed = takproto.parse_mesh(bytearray(framed))
    ce = parsed.cotEvent
    assert ce.uid == "emitter-01" and ce.type == "a-u-S" and ce.how == "m-g"
    assert ce.lat == 12.3456 and ce.lon == -45.6789 and ce.hae == 9999999.0 and ce.ce == 35.0
    assert ce.detail.contact.callsign == "Track emitter-01"
    assert ce.detail.track.course == 135.0 and ce.detail.track.speed == 12.5
    assert "<geo_dimensionality" in ce.detail.xmlDetail
