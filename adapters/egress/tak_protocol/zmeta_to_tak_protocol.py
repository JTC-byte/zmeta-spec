"""ZMeta STATE_EVENT to TAK Protocol Version 1 (protobuf CoT) egress adapter.

TAK Protocol Version 1 is the binary wire form of Cursor-on-Target that TAK
clients and servers exchange on mesh (multicast UDP) and stream (TCP, TLS)
connections. It carries the same CoT event as the XML form, encoded as a
protobuf `TakMessage`, with the typed parts of `<detail>` in typed fields and
the rest of `<detail>` as XML text in `xmlDetail`.

This adapter is a wire step over the CoT egress projection
(`adapters/egress/cot/zmeta_to_cot.py`): it takes the CoT XML that projection
produces, under either of its profiles, and encodes it. The semantics, every
refusal and both profiles are the CoT adapter's; this module adds only the
encoding and the framing, and refuses whatever the encoding cannot carry
without loss. Nothing is read from the ZMeta event here except through the
CoT projection.

Encoding, as the TAK Protocol Version 1 schema defines it (the `.proto` files
in the ATAK-CIV repository; field numbers checked against the `takproto`
package's descriptors on 2026-11-09):

  TakMessage { TakControl takControl = 1; CotEvent cotEvent = 2; }
  CotEvent { type 1, access 2, qos 3, opex 4, uid 5 (strings); sendTime 6,
             startTime 7, staleTime 8 (uint64, milliseconds since the epoch);
             how 9 (string); lat 10, lon 11, hae 12, ce 13, le 14 (doubles);
             Detail detail 15 }
  Detail   { xmlDetail 1 (string); Contact contact 2; Group group 3;
             PrecisionLocation precisionLocation 4; Status status 5;
             Takv takv 6; Track track 7 }
  Contact { endpoint 1, callsign 2 }  Group { name 1, role 2 }
  PrecisionLocation { geopointsrc 1, altsrc 2 }  Status { battery 1 uint32 }
  Takv { device 1, platform 2, os 3, version 4 }  Track { speed 1, course 2 }

The encoder is written here against that schema, with no protobuf dependency,
in the canonical proto3 form: fields in field-number order, a scalar equal to
its default (an empty string, 0, 0.0) written as absent. `takControl` is not
written; it is a connection negotiation, not part of the event.

Framing: `mesh` prefixes the message with the three bytes `bf 01 bf`; `stream`
prefixes it with `bf` and the message length as a base-128 varint; `none`
returns the bare message.

What the encoding changes, and what it refuses (the README has the table):

  * Times are milliseconds. The CoT projection writes microseconds; the
    microseconds are dropped, never rounded up, so `stale` is never later
    than the event's claim (contract 4.2: a projection may lower a validity,
    never raise it). A time before 1970 has no uint64 and is refused.
  * The typed detail children (`contact`, `__group`, `precisionlocation`,
    `status`, `takv`, `track`) go to their typed fields only when the typed
    message carries the element whole: every attribute has a typed field,
    no attribute is empty (proto3 cannot tell an empty string from an absent
    one), every numeric field of the message is present (an absent number
    would read back as 0, a value), and the element has no text and no
    children. Otherwise the element travels whole in `xmlDetail`, as every
    other child does. The CoT projection's `<precisionlocation>` carries the
    error ellipse as attributes the typed message has no field for, so it
    travels in `xmlDetail`; `geopointsrc` and `altsrc` alone go typed (a
    shape the projection does not write, since it emits the element only
    with an ellipse). A typed element's numeric attribute that is not a
    number (`course="east"`, `battery="-1"`) refuses the event.
  * Two elements of one typed kind that both qualify for the typed field
    refuse the event, since the field holds one and choosing would drop the
    other; when only one qualifies the other travels in `xmlDetail`. An
    attribute of `<event>` or `<point>` the schema has no field for, a child
    of `<event>` other than `point` and `detail`, text directly inside
    `<detail>` or `<event>`, a comment, a document type declaration or a
    processing instruction anywhere, a `version` other than `2.0`, a missing
    `point` or point attribute, a point value that is not a finite number, a
    missing or unparseable `time`, `start` or `stale`, and an empty optional
    attribute (`access=""`, which proto3 would read back as absent) all
    refuse: the adapter never drops a part of the event in silence and never
    writes a claim the XML did not make. A refusal is the
    documented `None`, the CoT adapter's own signal; a caller that passes a
    `refusal` dict reads `TAK_PROTOCOL_UNREPRESENTABLE` there when the
    encoding, not the CoT projection, refused.
  * Attribute values become float64 (`lat`, `lon`, `hae`, `ce`, `le`,
    `course`, `speed`): a decimal with more digits than a double holds is
    rounded to the nearest double, which the XML form, as text, was not.
    The whitespace between detail children is formatting and is dropped;
    the typed children lose their position among the others, since a reader
    rebuilds `<detail>` from the typed fields and `xmlDetail` separately.

`read_tak_message` is a reader for the same schema, for tests and for a
consumer that wants to inspect the bytes. It refuses an unknown field, a
field with the wrong wire type, a repeated field, a truncated or oversized
frame and trailing bytes, by the rule of the repository's own decoders
(`DECODE_AMBIGUOUS`, 2026-11-02): a decode that would have to choose is not a
decode. It is not the proof of the encoder; the known-answer bytes in the
tests and the optional `takproto` cross-check are.

Not covered here: the connection itself (TakControl, TLS, the stream's
message boundaries beyond one frame) and any TAK Server or client's
acceptance of the bytes, which no test in this repository drives.
"""

import copy
import importlib.util
import math
import re
import struct
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path

ADAPTER_VERSION = "1.0.0"

MESH_HEADER = b"\xbf\x01\xbf"
STREAM_HEADER = b"\xbf"
FRAMINGS = ("mesh", "stream", "none")
COT_VERSION = "2.0"

# The refusal reason written to a caller's `refusal` dict when the encoding,
# not the CoT projection, refused.
REFUSAL_UNREPRESENTABLE = "TAK_PROTOCOL_UNREPRESENTABLE"

_UINT32_MAX = 2**32 - 1
_UINT64_MAX = 2**64 - 1
_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
_ONE_MS = timedelta(milliseconds=1)

# The same shape the CoT adapter accepts as a point value: a plain decimal,
# with an optional exponent. Python's float() also reads "nan", "inf",
# "1_000" and surrounding whitespace, none of which is a CoT number.
_NUMBER_TEXT = re.compile(r"[-+]?(?:[0-9]+\.?[0-9]*|\.[0-9]+)(?:[eE][-+]?[0-9]+)?")
_DIGITS = re.compile(r"[0-9]+")

# CotEvent: attribute name -> (field number, kind). `version` has no field: it
# is the XML form's own and must be 2.0, the CoT this schema encodes.
_EVENT_STRINGS = (("type", 1), ("access", 2), ("qos", 3), ("opex", 4), ("uid", 5), ("how", 9))
_EVENT_TIMES = (("time", 6), ("start", 7), ("stale", 8))
_EVENT_REQUIRED = ("type", "uid", "time", "start", "stale")
_EVENT_ATTRIBUTES = frozenset(("version",) + tuple(n for n, _ in _EVENT_STRINGS) + tuple(n for n, _ in _EVENT_TIMES))
_POINT_DOUBLES = (("lat", 10), ("lon", 11), ("hae", 12), ("ce", 13), ("le", 14))
_POINT_ATTRIBUTES = frozenset(n for n, _ in _POINT_DOUBLES)
_DETAIL_FIELD = 15
_XML_DETAIL_FIELD = 1

# Typed detail children: tag -> (Detail field number, ((attribute, field, kind), ...)).
_TYPED_CHILDREN = {
    "contact": (2, (("endpoint", 1, "string"), ("callsign", 2, "string"))),
    "__group": (3, (("name", 1, "string"), ("role", 2, "string"))),
    "precisionlocation": (4, (("geopointsrc", 1, "string"), ("altsrc", 2, "string"))),
    "status": (5, (("battery", 1, "uint32"),)),
    "takv": (6, (("device", 1, "string"), ("platform", 2, "string"), ("os", 3, "string"), ("version", 4, "string"))),
    "track": (7, (("speed", 1, "double"), ("course", 2, "double"))),
}

# Reader schemas: field number -> (name, kind), kind a scalar name or a nested schema.
_TYPED_SCHEMAS = {
    tag: (field, {num: (attr, kind) for attr, num, kind in members})
    for tag, (field, members) in _TYPED_CHILDREN.items()
}
_DETAIL_SCHEMA = {_XML_DETAIL_FIELD: ("xmlDetail", "string")}
_DETAIL_NAMES = {"contact": "contact", "__group": "group", "precisionlocation": "precisionLocation",
                 "status": "status", "takv": "takv", "track": "track"}
for _tag, (_field, _schema) in _TYPED_SCHEMAS.items():
    _DETAIL_SCHEMA[_field] = (_DETAIL_NAMES[_tag], _schema)
_COT_EVENT_SCHEMA = {num: (name, "string") for name, num in _EVENT_STRINGS}
_COT_EVENT_SCHEMA.update({num: (("sendTime", "startTime", "staleTime")[i], "uint64") for i, (_, num) in enumerate(_EVENT_TIMES)})
_COT_EVENT_SCHEMA.update({num: (name, "double") for name, num in _POINT_DOUBLES})
_COT_EVENT_SCHEMA[_DETAIL_FIELD] = ("detail", _DETAIL_SCHEMA)
_TAK_CONTROL_SCHEMA = {1: ("minProtoVersion", "uint32"), 2: ("maxProtoVersion", "uint32"), 3: ("contactUid", "string")}
_TAK_MESSAGE_SCHEMA = {1: ("takControl", _TAK_CONTROL_SCHEMA), 2: ("cotEvent", _COT_EVENT_SCHEMA)}

_WIRE_VARINT = 0
_WIRE_FIXED64 = 1
_WIRE_LENGTH = 2
_WIRE_OF_KIND = {"string": _WIRE_LENGTH, "uint32": _WIRE_VARINT, "uint64": _WIRE_VARINT, "double": _WIRE_FIXED64}


# --- protobuf writing --------------------------------------------------------

def _varint(value):
    out = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            out.append(byte | 0x80)
        else:
            out.append(byte)
            return bytes(out)


def _key(field, wire_type):
    return _varint((field << 3) | wire_type)


def _write_string(field, text):
    """A string field; the proto3 default (empty) is written as absent."""
    if not text:
        return b""
    data = text.encode("utf-8")
    return _key(field, _WIRE_LENGTH) + _varint(len(data)) + data


def _write_uint(field, value):
    if value == 0:
        return b""
    return _key(field, _WIRE_VARINT) + _varint(value)


_ZERO_DOUBLE = struct.pack("<d", 0.0)


def _write_double(field, value):
    """A double; the proto3 default is written as absent. The comparison is
    on the bits, as protobuf's own serializers compare, so -0.0 is written."""
    packed = struct.pack("<d", value)
    if packed == _ZERO_DOUBLE:
        return b""
    return _key(field, _WIRE_FIXED64) + packed


def _write_message(field, payload):
    """An embedded message; an empty message is still written, since its
    presence is itself the information (a Detail with no fields is not no
    Detail). Callers omit the call when the element is absent."""
    return _key(field, _WIRE_LENGTH) + _varint(len(payload)) + payload


# --- the XML side ------------------------------------------------------------

# Markup the encoding has no carrier for, anywhere in the document: a comment,
# a document type declaration (whose entities the parser would expand into
# content the event never carried), and a processing instruction other than
# the XML declaration that may open the document. In well-formed XML these
# sequences cannot occur inside text or an attribute value, so a text scan is
# exact. CDATA sections are content and pass; the parser re-escapes them.
_XML_DECLARATION = re.compile(r"\A\s*<\?xml\s[^?]*\?>")
_FORBIDDEN_MARKUP = re.compile(r"<!--|<!DOCTYPE|<\?")


def _parse(cot_xml):
    """The parsed root, or None. A comment, a document type declaration or a
    processing instruction anywhere refuses here, before parsing; the parser
    keeps any that reach it as nodes, so the caller can refuse those too."""
    if isinstance(cot_xml, bytes):
        try:
            cot_xml = cot_xml.decode("utf-8")
        except UnicodeDecodeError:
            return None
    if not isinstance(cot_xml, str) or not cot_xml.strip():
        return None
    if cot_xml.startswith("﻿"):
        cot_xml = cot_xml[1:]
    if _FORBIDDEN_MARKUP.search(_XML_DECLARATION.sub("", cot_xml, count=1)):
        return None
    parser = ET.XMLParser(target=ET.TreeBuilder(insert_comments=True, insert_pis=True))
    try:
        return ET.fromstring(cot_xml, parser=parser)
    except (ET.ParseError, ValueError, TypeError):
        return None


def _is_blank(text):
    return text is None or not text.strip()


def _epoch_ms(text):
    """Milliseconds since the epoch, floored, or None.

    Accepts what `datetime.fromisoformat` accepts when it carries an offset
    (`Z` is read as `+00:00`), which is wider than RFC 3339: a space in place
    of `T`, a basic-format date, a week date. The CoT projection writes
    `%Y-%m-%dT%H:%M:%S.%fZ`, which is inside both. Refuses text without an
    offset, text the parser does not read, an instant before 1970 (no uint64)
    and one the datetime module cannot convert."""
    if not isinstance(text, str) or not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except (ValueError, TypeError):
        return None
    if parsed.tzinfo is None:
        return None
    try:
        delta = parsed.astimezone(timezone.utc) - _EPOCH
    except (OverflowError, OSError, ValueError):
        return None
    ms = delta // _ONE_MS
    if ms < 0 or ms > _UINT64_MAX:
        return None
    return ms


def _finite_double(text):
    """The float a CoT decimal attribute denotes, or None."""
    if not isinstance(text, str) or not _NUMBER_TEXT.fullmatch(text):
        return None
    try:
        value = float(text)
    except (ValueError, OverflowError):
        return None
    if not math.isfinite(value):
        return None
    return value


def _uint32(text):
    if not isinstance(text, str) or not _DIGITS.fullmatch(text):
        return None
    value = int(text)
    if value > _UINT32_MAX:
        return None
    return value


def _typed_route(element):
    """True when the typed message carries this element whole: every
    attribute has a typed field, none is empty, every numeric field of the
    message is present, and the element has neither text nor children. False
    sends it whole to xmlDetail.

    An absent string reads back as absent (proto3's empty default), so a
    string attribute may be left out. An absent number would read back as
    0, which is a value, so `<track course="90.0" />` without `speed` is not
    carried typed: the reader could not tell it from a speed of 0.
    """
    _, members = _TYPED_CHILDREN[element.tag]
    names = {attr for attr, _, _ in members}
    if not set(element.attrib) <= names:
        return False
    if any(value == "" for value in element.attrib.values()):
        return False
    if any(kind != "string" and attr not in element.attrib for attr, _, kind in members):
        return False
    if not _is_blank(element.text) or len(element) > 0:
        return False
    return True


def _encode_typed(element):
    """The typed message's bytes, or None when a numeric attribute is not a number."""
    _, members = _TYPED_CHILDREN[element.tag]
    out = b""
    for attr, field, kind in members:
        value = element.attrib.get(attr)
        if value is None:
            continue
        if kind == "string":
            out += _write_string(field, value)
        elif kind == "double":
            number = _finite_double(value)
            if number is None:
                return None
            out += _write_double(field, number)
        else:  # uint32
            number = _uint32(value)
            if number is None:
                return None
            out += _write_uint(field, number)
    return out


def _serialize_child(element):
    """The element as XML text, without its tail."""
    bare = copy.copy(element)
    bare.tail = None
    return ET.tostring(bare, encoding="unicode")


def _encode_detail(detail):
    """The Detail message bytes, or None on a refusal."""
    if not _is_blank(detail.text):
        return None
    xml_detail = []
    typed = {}
    for child in detail:
        if not isinstance(child.tag, str):
            # A comment or processing instruction: no carrier, never dropped.
            return None
        if not _is_blank(child.tail):
            return None
        if child.tag in _TYPED_CHILDREN and _typed_route(child):
            field = _TYPED_CHILDREN[child.tag][0]
            if field in typed:
                # Two elements of one typed kind: the field holds one, and
                # choosing would drop the other.
                return None
            encoded = _encode_typed(child)
            if encoded is None:
                return None
            typed[field] = encoded
            continue
        xml_detail.append(_serialize_child(child))
    out = _write_string(_XML_DETAIL_FIELD, "".join(xml_detail))
    for field in sorted(typed):
        out += _write_message(field, typed[field])
    return out


def cot_xml_to_tak_message(cot_xml):
    """Encode one CoT XML event as a TAK Protocol Version 1 `TakMessage`.

    Returns the message bytes without framing, or None when the XML does not
    parse, is not a CoT 2.0 event, or carries anything the encoding cannot
    hold without loss or invention (the module docstring lists the cases).
    """
    root = _parse(cot_xml)
    if root is None or root.tag != "event":
        return None
    for node in root.iter():
        if not isinstance(node.tag, str):
            return None
    if not _is_blank(root.text):
        return None
    attrs = root.attrib
    if not set(attrs) <= _EVENT_ATTRIBUTES:
        return None
    if attrs.get("version") != COT_VERSION:
        return None
    for name in _EVENT_REQUIRED:
        if not attrs.get(name):
            return None
    for name, _ in _EVENT_STRINGS:
        if name in attrs and attrs[name] == "":
            return None

    point = None
    detail = None
    for child in root:
        if not _is_blank(child.tail):
            return None
        if child.tag == "point" and point is None:
            point = child
        elif child.tag == "detail" and detail is None:
            detail = child
        else:
            return None
    if point is None:
        return None
    if set(point.attrib) != _POINT_ATTRIBUTES or not _is_blank(point.text) or len(point) > 0:
        return None

    out = b""
    strings = dict(_EVENT_STRINGS)
    times = dict(_EVENT_TIMES)
    doubles = dict(_POINT_DOUBLES)
    # Field-number order: 1 type, 2 access, 3 qos, 4 opex, 5 uid, 6 to 8 the
    # times, 9 how, 10 to 14 the point, 15 detail.
    for name in ("type", "access", "qos", "opex", "uid"):
        if name in attrs:
            out += _write_string(strings[name], attrs[name])
    for name in ("time", "start", "stale"):
        ms = _epoch_ms(attrs[name])
        if ms is None:
            return None
        out += _write_uint(times[name], ms)
    if "how" in attrs:
        out += _write_string(strings["how"], attrs["how"])
    for name in ("lat", "lon", "hae", "ce", "le"):
        value = _finite_double(point.attrib[name])
        if value is None:
            return None
        out += _write_double(doubles[name], value)
    if detail is not None:
        encoded = _encode_detail(detail)
        if encoded is None:
            return None
        out += _write_message(_DETAIL_FIELD, encoded)
    return _write_message(2, out)


# --- framing -----------------------------------------------------------------

def validate_framing(framing):
    """Return the framing name, or raise ValueError for one the adapter does not know."""
    if framing not in FRAMINGS:
        raise ValueError(f"framing must be one of {', '.join(FRAMINGS)}, got {framing!r}")
    return framing


def frame_mesh(message):
    """The TAK Protocol Version 1 mesh frame: `bf 01 bf` then the message."""
    return MESH_HEADER + bytes(message)


def frame_stream(message):
    """The TAK Protocol Version 1 stream frame: `bf`, the message length as a varint, the message."""
    message = bytes(message)
    return STREAM_HEADER + _varint(len(message)) + message


_FRAMERS = {"mesh": frame_mesh, "stream": frame_stream, "none": bytes}


# --- the adapter entry point ---------------------------------------------------

_cot_module = None


def _cot():
    """The CoT egress adapter, loaded by path from the sibling directory so this
    module needs no package on sys.path."""
    global _cot_module
    if _cot_module is None:
        path = Path(__file__).resolve().parent.parent / "cot" / "zmeta_to_cot.py"
        spec = importlib.util.spec_from_file_location("zmeta_to_cot_for_tak_protocol", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _cot_module = module
    return _cot_module


def zmeta_to_tak_protocol(event, cot_config=None, now=None, framing="mesh", refusal=None):
    """Project a ZMeta STATE_EVENT to TAK Protocol Version 1 bytes.

    Args:
        event: the ZMeta event dict; must be a STATE_EVENT the CoT projection accepts.
        cot_config: the CoT adapter's configuration, passed through unchanged
            (profile, how, the defaults, the cds keys; see its README).
        now: the projection instant, passed through to the CoT adapter.
        framing: "mesh" (default), "stream" or "none".
        refusal: an optional dict; the CoT adapter writes its cds reasons
            there, and this adapter writes TAK_PROTOCOL_UNREPRESENTABLE when
            the encoding refused a CoT string the projection produced.

    Returns:
        The framed bytes, or None on any refusal: the CoT adapter's (wrong
        event type, missing geo, a lapsed cds validity, and the rest), an
        unknown framing, or an encoding refusal.
    """
    try:
        validate_framing(framing)
    except ValueError:
        return None
    cot_xml = _cot().zmeta_to_cot(event, cot_config=cot_config, now=now, refusal=refusal)
    if cot_xml is None:
        return None
    message = cot_xml_to_tak_message(cot_xml)
    if message is None:
        if isinstance(refusal, dict):
            refusal["reason"] = REFUSAL_UNREPRESENTABLE
        return None
    return _FRAMERS[framing](message)


# --- the reader ----------------------------------------------------------------

def _read_varint(data, pos):
    result = 0
    shift = 0
    while True:
        if pos >= len(data):
            raise ValueError("truncated varint")
        byte = data[pos]
        pos += 1
        result |= (byte & 0x7F) << shift
        if not byte & 0x80:
            if result > _UINT64_MAX:
                raise ValueError("varint longer than 64 bits")
            return result, pos
        shift += 7
        if shift > 63:
            raise ValueError("varint longer than 64 bits")


def _decode(data, schema, level):
    """Decode one message against `schema` into a dict of present fields.

    Refuses an unknown field number, a known field with the wrong wire type,
    a repeated field and a truncated field: the rule the repository's own
    decoders apply, so a reader never chooses between two readings.
    """
    out = {}
    pos = 0
    while pos < len(data):
        key, pos = _read_varint(data, pos)
        field, wire_type = key >> 3, key & 0x07
        if field not in schema:
            raise ValueError(f"unknown field {field} in {level}")
        name, kind = schema[field]
        expected = _WIRE_LENGTH if isinstance(kind, dict) else _WIRE_OF_KIND[kind]
        if wire_type != expected:
            raise ValueError(f"field {name} in {level} carries wire type {wire_type}, the schema uses {expected}")
        if name in out:
            raise ValueError(f"field {name} in {level} is repeated")
        if wire_type == _WIRE_VARINT:
            value, pos = _read_varint(data, pos)
            if kind == "uint32" and value > _UINT32_MAX:
                raise ValueError(f"field {name} in {level} exceeds uint32")
            out[name] = value
        elif wire_type == _WIRE_FIXED64:
            if pos + 8 > len(data):
                raise ValueError(f"truncated double in {level}")
            out[name] = struct.unpack("<d", data[pos:pos + 8])[0]
            pos += 8
        else:
            length, pos = _read_varint(data, pos)
            if pos + length > len(data):
                raise ValueError(f"truncated field {name} in {level}")
            chunk = data[pos:pos + length]
            pos += length
            if isinstance(kind, dict):
                out[name] = _decode(chunk, kind, name)
            else:
                try:
                    out[name] = chunk.decode("utf-8")
                except UnicodeDecodeError as exc:
                    raise ValueError(f"field {name} in {level} is not UTF-8") from exc
    return out


def read_tak_message(data):
    """Read a TAK Protocol Version 1 message, framed (mesh or stream) or bare,
    into a dict of the fields present, nested as the schema nests them.

    Raises ValueError for a frame or message the schema does not describe:
    an empty input, a truncated or oversized stream frame, trailing bytes
    after it, an unknown field, a wrong wire type, a repeated field, a
    truncated field, a string that is not UTF-8. The three bytes `bf 01 bf`
    alone are read as an empty mesh frame (an empty TakMessage, `{}`); the
    same bytes as a stream frame would carry a one-byte message, which no
    TakMessage is.
    """
    data = bytes(data)
    if not data:
        raise ValueError("no bytes to read")
    if data.startswith(MESH_HEADER):
        body = data[len(MESH_HEADER):]
    elif data.startswith(STREAM_HEADER):
        length, pos = _read_varint(data, len(STREAM_HEADER))
        if pos + length != len(data):
            raise ValueError("stream frame length does not match the bytes present")
        body = data[pos:]
    else:
        body = data
    return _decode(body, _TAK_MESSAGE_SCHEMA, "TakMessage")
