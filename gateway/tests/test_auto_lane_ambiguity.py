"""The auto lane reports a protobuf refusal as DECODE_AMBIGUOUS only for a whole message carrying fields 2, 3 and 4.

Finding S2 of the pre-cut range review of 2026-11-14, and the maintainer's
selection of 2026-11-16 (option (a)), with the structural test of the build
ruling's amendment. After the strict protobuf decode has refused a datagram as
ambiguous, the auto lane re-raises that refusal only when
zmeta_proto.carries_event_members finds the datagram to be one whole protobuf
message, every key valid and every field complete to its last byte, whose
top-level field numbers include 2, 3 and 4 (event, source, payload), whatever
their wire types. Nothing is decoded for that test. Any other datagram falls
through to the UTF-8/JSON attempt as at v1.1.27 and reads SCHEMA_INVALID. The
json, cbor, compact and proto lanes are unchanged, so the held class (a
message the strict decoder refuses as ambiguous that is also cut short or
malformed at its top level after the refused field, or lacks field 2, 3 or 4)
reads SCHEMA_INVALID on auto and DECODE_AMBIGUOUS on proto, a difference
chosen and held here. A complete event whose event, source or payload carries
a wrong wire type stays DECODE_AMBIGUOUS on both lanes.

Written before the change. Each change-direction test was seen failing on
9b07c19 (5c092c9 since the 11-17 reword), and each hold-direction test fails under a named mutant: one of the
change itself, or, for the controls the change cannot reach (a duplicate JSON
key, a cut protobuf datagram, clean decodes), one of the code beside it. No
test uses subTest: pytest 9 reports a failing subtest as SUBFAILED under a
PASSED test, which a reader of FAILED lines alone does not see.
"""

import collections
import importlib.util
import json
import random
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import zmeta_proto  # noqa: E402

VALIDATORS_PATH = ROOT / "gateway" / "src" / "validators.py"
spec = importlib.util.spec_from_file_location("zmeta_validators_al", VALIDATORS_PATH)
validators = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validators)
GATEWAY_PATH = ROOT / "gateway" / "src" / "gateway.py"
spec_gw = importlib.util.spec_from_file_location("zmeta_gateway_al", GATEWAY_PATH)
gateway = importlib.util.module_from_spec(spec_gw)
spec_gw.loader.exec_module(gateway)

SCHEMA_VALIDATOR = validators.load_schema(ROOT / "schema" / "zmeta-event-1.0.schema.json")
POLICY = validators.load_policy(ROOT / "policy")

AIS = b"!AIVDM,1,1,,B,177KQJ5000G?tO`K>RA1wUbN0TKH,0*5C\r\n"
NMEA = b"$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47\r\n"
HELLO = b"hello world"
KEY = zmeta_proto._field_key
STRAY = KEY(9, zmeta_proto.WIRE_LEN) + b"\x01A"
DUPLICATE_PAYLOAD = zmeta_proto._field_bytes(4, b'{"a":1,"a":2}')
WRONG = {
    "varint": lambda number: KEY(number, zmeta_proto.WIRE_VARINT) + b"\x01",
    "fixed64": lambda number: KEY(number, zmeta_proto.WIRE_FIXED64) + b"\x00" * 8,
    "fixed32": lambda number: KEY(number, zmeta_proto.WIRE_FIXED32) + b"\x00" * 4,
}
NAMES = {2: "event", 3: "source", 4: "payload"}


def _five_member_event():
    """The first line of examples/zmeta-examples-1.0.jsonl, an OBSERVATION with five members."""
    line = (ROOT / "examples" / "zmeta-examples-1.0.jsonl").read_text(encoding="utf-8").splitlines()[0]
    event = json.loads(line)
    assert len(event) == 5, "the first example is no longer a five-member event"
    return event


def _clean_event():
    """A Profile L STATE_EVENT that the gateway accepts on every lane (seven members)."""
    return {
        "zmeta_version": "1.0",
        "event": {
            "event_id": "019c2b5c-c051-70e1-b6aa-34bf14c8b1e1",
            "event_type": "STATE_EVENT",
            "event_subtype": "TRACK_STATE",
            "ts": "2025-01-17T14:30:00Z",
        },
        "source": {"platform_id": "fusion-node-01", "node_role": "GATEWAY", "producer": "fusion-engine"},
        "profile": "L",
        "payload": {"track_id": "track-1", "geo": {"lat": 34.0, "lon": -118.0, "alt_m": 100.0}, "valid_for_ms": 1000},
        "confidence": 0.8,
        "lineage": {"based_on": ["019c2b5c-c051-70e1-b6aa-34bf14c8b1d0"]},
    }


def _members(event):
    """The top-level fields of an event's protobuf encoding, keyed by field number, in the order dumps writes them."""
    parts = collections.OrderedDict()
    if event.get("zmeta_version") is not None:
        parts[1] = zmeta_proto._field_string(1, event["zmeta_version"])
    if isinstance(event.get("event"), dict):
        parts[2] = zmeta_proto._field_message(2, zmeta_proto._encode_event_block(event["event"]))
    if isinstance(event.get("source"), dict):
        parts[3] = zmeta_proto._field_message(3, zmeta_proto._encode_source(event["source"]))
    if "payload" in event:
        parts[4] = zmeta_proto._field_bytes(4, zmeta_proto._payload_to_bytes(event["payload"]))
    if event.get("confidence") is not None:
        parts[5] = zmeta_proto._field_double(5, float(event["confidence"]))
    if isinstance(event.get("lineage"), dict):
        parts[6] = zmeta_proto._field_message(6, zmeta_proto._encode_lineage(event["lineage"]))
    if event.get("profile") is not None:
        parts[7] = zmeta_proto._field_string(7, event["profile"])
    assert b"".join(parts.values()) == zmeta_proto.dumps(event)
    return parts


def _join(parts, **changes):
    """The fields joined again, with field N replaced (fN=bytes) or left out (fN=None)."""
    joined = collections.OrderedDict(parts)
    for key, value in changes.items():
        if value is None:
            joined.pop(int(key[1:]), None)
        else:
            joined[int(key[1:])] = value
    return b"".join(joined.values())


def _held_members(event):
    """The pinned members of the held class, each refused as ambiguous by the strict decoder."""
    parts, whole = _members(event), zmeta_proto.dumps(event)
    return collections.OrderedDict([
        ("a stray field and no payload", _join(parts, f4=None) + STRAY),
        ("a stray field alone", STRAY),
        ("a stray field, then a one-byte cut", (STRAY + whole)[:-1]),
        ("a stray field and no source", _join(parts, f3=None) + STRAY),
        ("a stray field and no event", _join(parts, f2=None) + STRAY),
        ("a payload_json duplicate and no source", _join(parts, f3=None, f4=DUPLICATE_PAYLOAD)),
    ])


def _mistyped(event, number, wire):
    """A complete event whose field `number` (2, 3 or 4) carries a wrong wire type."""
    return _join(_members(event), **{f"f{number}": WRONG[wire](number)})


def _outputs(message, encoding):
    return gateway.process_message(message, SCHEMA_VALIDATOR, POLICY, "L", gateway.TaskDedupeCache(), encoding)


def _classify(wire, lane="auto"):
    """AMB for a DECODE_AMBIGUOUS refusal, INV for any other refusal, DEC for a decode."""
    try:
        gateway._decode_message(wire, lane)
    except Exception as exc:  # noqa: BLE001 - every refusal is classified
        return "AMB" if gateway.is_decode_ambiguous(exc) else "INV"
    return "DEC"


def _strictly_ambiguous(wire):
    try:
        zmeta_proto.loads(wire)
    except ValueError as exc:
        return gateway.is_decode_ambiguous(exc)
    return False


class AutoLaneNamedCaseTest(unittest.TestCase):
    """Named inputs through process_message, as a deployment sees them."""

    def _metrics(self, message, encoding, where):
        outputs = _outputs(message, encoding)
        self.assertEqual(1, len(outputs), where)
        self.assertEqual("SYSTEM_EVENT", outputs[0]["event"]["event_type"], where)
        return outputs[0]["payload"]["metrics"]

    def _schema_invalid(self, message, where, encoding="auto"):
        metrics = self._metrics(message, encoding, where)
        self.assertEqual(
            ("SCHEMA_INVALID", None), (metrics["reason_code"], metrics.get("diagnostic_code")), f"{where} on {encoding}"
        )
        self.assertNotIn("protobuf", metrics["error"], f"{where} on {encoding}")
        return metrics

    def _ambiguous(self, message, where, encoding):
        metrics = self._metrics(message, encoding, where)
        # the v1.0 wire keeps the legacy decode-stage code; the minted code rides
        # metrics.diagnostic_code (the post-lock route)
        self.assertEqual(
            ("SCHEMA_INVALID", "DECODE_AMBIGUOUS"),
            (metrics["reason_code"], metrics.get("diagnostic_code")),
            f"{where} on {encoding}",
        )
        return metrics

    def _compact(self):
        return gateway._encode_message(_five_member_event(), "compact")

    def _cbor(self):
        return gateway._encode_message(_five_member_event(), "cbor")

    # change direction: SCHEMA_INVALID with no diagnostic_code on auto

    def test_a_compact_event_cut_by_one_byte_reads_schema_invalid_on_auto(self):
        metrics = self._schema_invalid(self._compact()[:-1], "compact[:-1]")
        # the UTF-8 attempt's text, as at v1.1.27; carrying the CBOR attempt's
        # own text instead is option (c3), booked open and not built
        self.assertIn("'utf-8' codec can't decode", metrics["error"])
        compact = self._schema_invalid(self._compact()[:-1], "compact[:-1]", "compact")
        self.assertIn("unexpected end of data", compact["error"])

    def test_a_compact_event_cut_at_the_fragment_points_reads_schema_invalid_on_auto(self):
        wire = self._compact()
        for k in (6, 8):
            # a fragment point: one whole protobuf message (the forensic read
            # decodes it end to end) without fields 2, 3 and 4; v1.1.27 decoded
            # it to {} and refused it at the schema
            fragment = zmeta_proto.loads(wire[:k], unknown_fields="skip")
            self.assertEqual(set(), {"event", "source", "payload"} & set(fragment), f"compact[:{k}] read {fragment}")
            self.assertEqual("AMB", _classify(wire[:k], "proto"), f"compact[:{k}] on proto")
            metrics = self._schema_invalid(wire[:k], f"compact[:{k}]")
            # the lane falls through to the UTF-8/JSON attempt
            self.assertIn("'utf-8' codec can't decode", metrics["error"], f"compact[:{k}]")

    def test_its_cbor_encoding_cut_by_one_byte_and_at_6_reads_schema_invalid_on_auto(self):
        wire = self._cbor()
        self.assertEqual({}, zmeta_proto.loads(wire[:6], unknown_fields="skip"))
        for k in (len(wire) - 1, 6):
            self._schema_invalid(wire[:k], f"cbor[:{k}]")
            self._schema_invalid(wire[:k], f"cbor[:{k}]", "cbor")

    def test_the_compact_encoding_with_one_trailing_byte_reads_schema_invalid_on_auto(self):
        self._schema_invalid(self._compact() + b"\x00", "compact+00")

    def test_an_ais_sentence_reads_schema_invalid_on_auto(self):
        self._schema_invalid(AIS, "AIS")

    def test_plain_text_reads_schema_invalid_on_auto(self):
        self._schema_invalid(HELLO, "hello world")

    def _held(self, name):
        """One pinned member of the held class: SCHEMA_INVALID on auto, DECODE_AMBIGUOUS on proto."""
        held = _held_members(_clean_event())
        self.assertEqual(6, len(held))
        wire = held[name]
        self.assertTrue(_strictly_ambiguous(wire), f"{name}: the strict decoder must refuse it as ambiguous")
        self._schema_invalid(wire, name)
        self._ambiguous(wire, name, "proto")

    def test_held_a_stray_field_and_no_payload(self):
        self._held("a stray field and no payload")

    def test_held_a_stray_field_alone(self):
        self._held("a stray field alone")

    def test_held_a_stray_field_then_a_one_byte_cut(self):
        self._held("a stray field, then a one-byte cut")

    def test_held_a_stray_field_and_no_source(self):
        self._held("a stray field and no source")

    def test_held_a_stray_field_and_no_event(self):
        self._held("a stray field and no event")

    def test_held_a_payload_json_duplicate_and_no_source(self):
        self._held("a payload_json duplicate and no source")

    def test_held_a_stray_field_then_an_invalid_key(self):
        # a member of the class beyond the six pinned ones: malformed at the top
        # level after the refused field (field number 0), from the seeded review
        wire = STRAY + b"\x00\x00" + zmeta_proto.dumps(_clean_event())
        self.assertTrue(_strictly_ambiguous(wire), "the strict decoder must refuse it as ambiguous")
        self._schema_invalid(wire, "a stray field, then field number 0")
        self._ambiguous(wire, "a stray field, then field number 0", "proto")

    # hold direction: DECODE_AMBIGUOUS on auto and on proto

    def test_a_protobuf_event_with_a_stray_field_reads_decode_ambiguous_on_auto_and_proto(self):
        base = zmeta_proto.dumps(_clean_event())
        for where, wire in (("appended", base + STRAY), ("prepended", STRAY + base)):
            for lane in ("auto", "proto"):
                metrics = self._ambiguous(wire, f"stray field {where}", lane)
                self.assertIn("ambiguous protobuf: field 9", metrics["error"], f"{where} on {lane}")

    def test_a_complete_event_with_a_mistyped_member_reads_decode_ambiguous_on_auto_and_proto(self):
        for number, name in NAMES.items():
            wire = _mistyped(_clean_event(), number, "varint")
            for lane in ("auto", "proto"):
                metrics = self._ambiguous(wire, f"{name} as a varint", lane)
                self.assertIn(f"field {number} with wire type 0", metrics["error"], f"{name} on {lane}")

    def test_a_duplicate_key_in_payload_json_reads_decode_ambiguous_on_both_lanes(self):
        wire = _join(_members(_clean_event()), f4=DUPLICATE_PAYLOAD)
        for lane in ("auto", "proto"):
            metrics = self._ambiguous(wire, "payload_json duplicate", lane)
            self.assertIn("duplicate key 'a'", metrics["error"], lane)

    def test_a_stray_field_then_an_event_block_malformed_inside_reads_decode_ambiguous_on_auto_and_proto(self):
        # the test reads the top level only; a block's inside is the strict decoder's
        parts = _members(_clean_event())
        block = zmeta_proto._encode_event_block(_clean_event()["event"])
        wire = STRAY + _join(parts, f2=zmeta_proto._field_message(2, block + b"\x0f"))
        for lane in ("auto", "proto"):
            self._ambiguous(wire, "a stray field, then a malformed event block", lane)

    def test_a_whole_event_whose_payload_is_not_json_falls_through_to_the_json_attempt(self):
        # a refusal that is not ambiguous is never re-raised on auto: the lane
        # reports the UTF-8/JSON attempt's own text, as at v1.1.27
        wire = _join(_members(_clean_event()), f4=zmeta_proto._field_bytes(4, b"not json"))
        with self.assertRaises(ValueError) as decoder:
            zmeta_proto.loads(wire)
        self.assertFalse(gateway.is_decode_ambiguous(decoder.exception))
        try:
            gateway._json_loads(wire.decode("utf-8"))
        except ValueError as fall_through:
            expected = str(fall_through)
        else:  # pragma: no cover - the bytes are not JSON
            self.fail("the protobuf bytes parsed as JSON")
        self.assertNotEqual(str(decoder.exception), expected)
        metrics = self._schema_invalid(wire, "a payload that is not JSON")
        self.assertEqual(expected, metrics["error"])

    def test_a_clean_protobuf_event_decodes_on_auto(self):
        outputs = _outputs(zmeta_proto.dumps(_clean_event()), "auto")
        self.assertEqual(["STATE_EVENT"], [out["event"]["event_type"] for out in outputs])

    def test_a_clean_event_in_every_encoding_decodes_on_auto(self):
        event = _clean_event()
        for encoding in ("json", "cbor", "compact", "proto"):
            outputs = _outputs(gateway._encode_message(event, encoding), "auto")
            self.assertEqual(["STATE_EVENT"], [out["event"]["event_type"] for out in outputs], encoding)
            self.assertEqual(event["event"]["event_id"], outputs[0]["event"]["event_id"], encoding)


class CarriesEventMembersTest(unittest.TestCase):
    """zmeta_proto.carries_event_members, read directly."""

    def test_true_for_a_whole_message_carrying_fields_2_3_and_4_whatever_their_wire_types(self):
        event = _clean_event()
        parts, whole = _members(event), zmeta_proto.dumps(event)
        cases = {
            "a clean event": whole,
            "a stray field appended": whole + STRAY,
            "a stray field prepended": STRAY + whole,
            "a payload_json duplicate": _join(parts, f4=DUPLICATE_PAYLOAD),
            "fields 2, 3 and 4 alone": parts[2] + parts[3] + parts[4],
            "the same, bytes-like": bytearray(parts[2] + parts[3] + parts[4]),
        }
        for number in NAMES:
            for wire in WRONG:
                cases[f"field {number} as {wire}"] = _mistyped(event, number, wire)
        for name, data in cases.items():
            self.assertIs(True, zmeta_proto.carries_event_members(data), name)

    def test_false_for_each_held_member_and_for_bytes_that_are_no_whole_message(self):
        compact = gateway._encode_message(_five_member_event(), "compact")
        parts, whole = _members(_clean_event()), zmeta_proto.dumps(_clean_event())
        cases = dict(_held_members(_clean_event()))
        cases.update({
            "a compact event cut by one byte": compact[:-1],
            "a compact fragment (one whole fixed32 field)": compact[:6],
            "the AIS sentence": AIS,
            "hello world": HELLO,
            "no bytes": b"",
            # a whole varint field with field number 0, before three whole members:
            # only the key check refuses it
            "field number 0, then fields 2, 3 and 4": b"\x00\x00" + parts[2] + parts[3] + parts[4],
            "a stray field, then field number 0, then a whole event": STRAY + b"\x00\x00" + whole,
            "an unsupported wire type after a whole event": whole + b"\x0f",
        })
        for name, data in cases.items():
            self.assertIs(False, zmeta_proto.carries_event_members(data), name)

    def test_the_message_and_field_bounds_of_loads_apply(self):
        def three(size_2, size_3, size_4):
            return (zmeta_proto._field_bytes(2, b"e" * size_2) + zmeta_proto._field_bytes(3, b"s" * size_3)
                    + zmeta_proto._field_bytes(4, b"p" * size_4))

        over_message = three(400_000, 400_000, 400_000)
        self.assertGreater(len(over_message), zmeta_proto.DEFAULT_MAX_MESSAGE_BYTES)
        self.assertIs(False, zmeta_proto.carries_event_members(over_message))
        self.assertIs(True, zmeta_proto.carries_event_members(three(300_000, 300_000, 300_000)))
        # the message bound itself: exactly 1,048,576 bytes is within it, one more is not
        at_bound = three(349_524, 349_524, 349_516)
        self.assertEqual(zmeta_proto.DEFAULT_MAX_MESSAGE_BYTES, len(at_bound))
        self.assertIs(True, zmeta_proto.carries_event_members(at_bound))
        one_over = three(349_524, 349_524, 349_517)
        self.assertEqual(zmeta_proto.DEFAULT_MAX_MESSAGE_BYTES + 1, len(one_over))
        self.assertIs(False, zmeta_proto.carries_event_members(one_over))
        over_field = three(10, 10, zmeta_proto.DEFAULT_MAX_FIELD_BYTES + 1)
        self.assertLess(len(over_field), zmeta_proto.DEFAULT_MAX_MESSAGE_BYTES)
        self.assertIs(False, zmeta_proto.carries_event_members(over_field))
        self.assertIs(True, zmeta_proto.carries_event_members(three(10, 10, zmeta_proto.DEFAULT_MAX_FIELD_BYTES)))


class GatewaySkipModeTest(unittest.TestCase):
    def test_the_gateway_never_asks_for_the_skip_mode(self):
        # spec/protobuf-encoding.md, its decoder bounds, says the gateway never
        # passes unknown_fields="skip"; the auto lane's test decodes nothing
        spec_text = " ".join((ROOT / "spec" / "protobuf-encoding.md").read_text(encoding="utf-8").split())
        self.assertIn('passes `unknown_fields="skip"` by name, and the gateway never does.', spec_text)
        self.assertNotIn("unknown_fields", GATEWAY_PATH.read_text(encoding="utf-8"))


def _examples():
    events = []
    for path in sorted((ROOT / "examples").glob("*.jsonl")):
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if line.strip():
                events.append((f"{path.name}:{number}", json.loads(line)))
    return events


def _strays(event):
    """Nine stray-field variants of an event's protobuf encoding (check.py's group C)."""
    text = zmeta_proto._field_string
    base = zmeta_proto.dumps(event)
    block = zmeta_proto._encode_event_block(event["event"])
    source = zmeta_proto._encode_source(event["source"])
    inner = zmeta_proto._field_message(2, block)
    yield "append unknown 9 LEN", base + KEY(9, zmeta_proto.WIRE_LEN) + b"\x01A"
    yield "prepend unknown 9 LEN", KEY(9, zmeta_proto.WIRE_LEN) + b"\x01A" + base
    yield "append unknown 20 fixed32", base + KEY(20, zmeta_proto.WIRE_FIXED32) + b"\x00\x00\x00\x00"
    yield "prepend unknown 20 fixed32", KEY(20, zmeta_proto.WIRE_FIXED32) + b"\x00\x00\x00\x00" + base
    yield "prepend unknown 1000 varint", KEY(1000, zmeta_proto.WIRE_VARINT) + b"\x07" + base
    yield "append field 5 as varint", base + KEY(5, zmeta_proto.WIRE_VARINT) + b"\x01"
    yield "append second source", base + zmeta_proto._field_message(3, source)
    yield "unknown field inside the event block", base.replace(
        inner, zmeta_proto._field_message(2, block + KEY(9, zmeta_proto.WIRE_LEN) + b"\x01A"), 1)
    yield "repeated event_type inside the event block", base.replace(
        inner, zmeta_proto._field_message(2, block + text(2, "COMMAND_EVENT")), 1)


class AutoLaneSweepTest(unittest.TestCase):
    """Every shipped example, ported from the S2 evidence's check.py (groups A to E) and the amendment's class M.

    The whole corpus runs, no subset: every cut point of every example's compact
    and CBOR encoding (with `profile` removed too, for the four- and six-member
    shapes), each also with one trailing byte; three non-ZMeta texts; nine
    stray-field variants and nine mistyped-member variants of every example's
    protobuf encoding; the clean decodes; every cut point of every protobuf
    encoding; 5,000 seeded random datagrams. The class's tests take about
    1.4 s on the maintainer's workstation (Python 3.14.0, pytest 9.0.2,
    measured 2026-11-16), so it keeps every cut point.
    """

    @classmethod
    def setUpClass(cls):
        cls.events = _examples()

    def test_no_cut_or_padded_compact_or_cbor_datagram_reads_decode_ambiguous_on_auto(self):
        bad, counted = collections.defaultdict(list), collections.Counter()
        shapes = self.events + [(name + " -profile", {k: v for k, v in ev.items() if k != "profile"})
                                for name, ev in self.events]
        for name, event in shapes:
            for encoding in ("compact", "cbor"):
                try:
                    wire = gateway._encode_message(event, encoding)
                except Exception:  # noqa: BLE001 - compact encodes v1.0 events only
                    continue
                for k in range(1, len(wire)):
                    counted[encoding] += 1
                    if _classify(wire[:k]) == "AMB":
                        bad[encoding].append(f"{name} {encoding}[:{k}]")
                counted[encoding + "+1"] += 1
                if _classify(wire + b"\x00") == "AMB":
                    bad[encoding + "+1"].append(f"{name} {encoding}+00")
        # the measured corpus: 19,886 compact and 52,146 CBOR cut points at 9b07c19 (5c092c9 since the 11-17 reword)
        self.assertGreater(counted["compact"], 15000, counted)
        self.assertGreater(counted["cbor"], 40000, counted)
        self.assertEqual({}, {group: (len(items), items[:3]) for group, items in bad.items()})

    def test_non_zmeta_text_never_reads_decode_ambiguous_on_auto(self):
        found = {name: _classify(text) for name, text in (("nmea", NMEA), ("ais", AIS), ("hello", HELLO))}
        self.assertEqual({"nmea": "INV", "ais": "INV", "hello": "INV"}, found)

    def test_every_stray_field_variant_stays_decode_ambiguous_on_auto_and_proto(self):
        bad, checked = [], 0
        for name, event in self.events:
            for label, wire in _strays(event):
                self.assertTrue(_strictly_ambiguous(wire), f"{name} {label}")
                checked += 1
                for lane in ("auto", "proto"):
                    if _classify(wire, lane) != "AMB":
                        bad.append(f"{name} {label} on {lane}")
        self.assertEqual(9 * len(self.events), checked)
        self.assertEqual([], bad[:5], f"{len(bad)} variants left DECODE_AMBIGUOUS")

    def test_every_mistyped_member_variant_stays_decode_ambiguous_on_auto_and_proto(self):
        bad, checked = [], 0
        for name, event in self.events:
            for number in NAMES:
                for wire_type in WRONG:
                    wire = _mistyped(event, number, wire_type)
                    self.assertTrue(_strictly_ambiguous(wire), f"{name} field {number} as {wire_type}")
                    checked += 1
                    for lane in ("auto", "proto"):
                        if _classify(wire, lane) != "AMB":
                            bad.append(f"{name} field {number} as {wire_type} on {lane}")
        self.assertEqual(9 * len(self.events), checked)
        self.assertEqual([], bad[:5], f"{len(bad)} variants left DECODE_AMBIGUOUS")

    def test_clean_decodes_are_unchanged_on_auto(self):
        bad, checked = [], 0
        for name, event in self.events:
            for encoding in ("json", "compact", "cbor", "proto"):
                try:
                    wire = gateway._encode_message(event, encoding)
                except Exception:  # noqa: BLE001 - compact encodes v1.0 events only
                    continue
                checked += 1
                if gateway._decode_message(wire, "auto") != gateway._decode_message(wire, encoding):
                    bad.append(f"{name} {encoding}")
        self.assertGreater(checked, 180)
        self.assertEqual([], bad)

    def test_a_duplicate_json_key_stays_decode_ambiguous_on_auto(self):
        bad, checked = [], 0
        for name, event in self.events:
            text = json.dumps(event)
            if '"profile"' not in text:
                continue
            checked += 1
            duplicate = text.replace('"zmeta_version"', '"profile": "H", "zmeta_version"', 1)
            if _classify(duplicate.encode("utf-8")) != "AMB":
                bad.append(name)
        self.assertGreater(checked, 40)
        self.assertEqual([], bad)

    def test_no_cut_protobuf_datagram_reads_decode_ambiguous_on_auto(self):
        bad = []
        for name, event in self.events:
            wire = zmeta_proto.dumps(event)
            bad.extend(f"{name} proto[:{k}]" for k in range(1, len(wire)) if _classify(wire[:k]) == "AMB")
        self.assertEqual([], bad[:5], f"{len(bad)} cut points read DECODE_AMBIGUOUS")

    def test_no_seeded_random_datagram_reads_decode_ambiguous_on_auto(self):
        # 1,934 of the 5,000 read DECODE_AMBIGUOUS at 9b07c19 (5c092c9 since the 11-17 reword)
        rng = random.Random(20261114)
        counted = collections.Counter(
            _classify(bytes(rng.getrandbits(8) for _ in range(rng.randint(1, 200)))) for _ in range(5000)
        )
        self.assertEqual(0, counted["AMB"], dict(counted))


if __name__ == "__main__":
    unittest.main()
