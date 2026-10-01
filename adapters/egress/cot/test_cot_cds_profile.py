"""The `cds` profile of the CoT egress adapter: the variant a partner's
cross-domain guard passed into a higher enclave on 2026-09-29.

The profile is a post-projection transform over the standard output: the
detail children are limited to contact, track, remarks and precisionlocation;
`how` is a required deployment claim; remarks is replaced by one fixed-template
line of at most 200 characters whose honesty markers always survive the cut;
no http(s) link survives anywhere in the event; stale is the earlier of the
event's own claim (ts + valid_for_ms) and the projection time plus a window,
120 s unless the deployment sets another, so the window caps a claim and never
extends one; an event whose claim has lapsed at projection is refused unless
the deployment chooses send_stale; an event older than the maximum age at
projection is refused. The standard profile's bytes
are unchanged by the profile's existence, and one test freezes them.

WHAT THIS FILE DOES NOT PROVE. It does not prove that any guard passes the
output: one partner's guard passed this shape on one day (n=1), and that fact
is recorded in the README, not tested here. The schema test validates against
the public CoT event schema only when COT_EVENT_XSD names a copy and lxml is
installed; the structural test beside it runs always and needs neither.
"""
import copy
import importlib.util
import os
import re
import unittest
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = ROOT / "adapters" / "egress" / "cot" / "zmeta_to_cot.py"
spec = importlib.util.spec_from_file_location("zmeta_to_cot_cds_module", MODULE_PATH)
cot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cot)

NOW = datetime(2026, 9, 29, 19, 59, 0, tzinfo=timezone.utc)
STAMP = "%Y-%m-%dT%H:%M:%S.%fZ"
LINK = re.compile(r"https?://", re.I)
AFFILIATIONS = ("a-h-S", "a-f-S", "a-n-S", "a-s-S", "a-j-S", "a-k-S", "a-a-S", "a-p-S", "a-o-S", "a-x-S", "a-f-A-M-F-Q")

# The standard projection of vessel_event(). Regenerated 2026-10-01 for the
# fixture's 300 s validity claim from the adapter as it stood before the cds
# stale change (doctrine F3-03), never from the changed code; the cds profile's
# existence and its stale rule must not change it.
STANDARD_BYTES = (
    '<event version="2.0" type="a-u-S" uid="fused:vessel/0417" time="2026-09-29T19:58:30.000000Z" start="2026-09-29T19:58:30.000000Z" stale="2026-09-29T20:03:30.000000Z">\n'
    '  <point lat="12.3456" lon="-45.6789" hae="9999999.0" le="9999999.0" ce="35.0" />\n'
    '  <detail>\n'
    '    <contact callsign="Vessel 0417" />\n'
    '    <remarks>fused from two AIS reports; confidence=0.72; Error ellipse: 35m x 12m @ 80deg</remarks>\n'
    '    <track course="135.0" speed="6.2" />\n'
    '    <geo_dimensionality value="2D" />\n'
    '  </detail>\n'
    '</event>'
)


def vessel_event(**overrides):
    """A schema-valid 1.1.0 STATE_EVENT: a fused surface vessel, declared 2-D."""
    event = {
        "zmeta_version": "1.1.0",
        "event": {
            "event_id": "019c2b5c-c046-70e1-b6aa-34bf14c8a247",
            "event_type": "STATE_EVENT",
            "event_subtype": "TRACK_STATE",
            "ts": "2026-09-29T19:58:30Z",
        },
        "source": {"platform_id": "gateway-01", "node_role": "GATEWAY", "producer": "fusion-engine"},
        "payload": {
            "track_id": "fused:vessel/0417",
            "class": "a-u-S",
            "callsign": "Vessel 0417",
            "geo": {
                "lat": 12.3456,
                "lon": -45.6789,
                "dimensionality": "2D",
                "error_ellipse_m": {"semi_major": 35.0, "semi_minor": 12.0, "orientation_deg": 80.0},
            },
            "valid_for_ms": 300000,
            "heading_deg": 135.0,
            "speed_mps": 6.2,
            "source_summary": ["fused from two AIS reports"],
        },
        "confidence": 0.72,
        "lineage": {"based_on": ["019c2b5c-88f0-7aa1-9b3e-5d2c41f0a9d2"]},
    }
    for key, value in overrides.items():
        target = event
        parts = key.split(".")
        for part in parts[:-1]:
            target = target.setdefault(part, {})
        if value is None:
            target.pop(parts[-1], None)
        else:
            target[parts[-1]] = value
    return event


CDS = {"profile": "cds", "how": "m-f"}


def render(event, config=CDS, now=NOW):
    return cot.zmeta_to_cot(event, cot_config=dict(config), now=now)


def parsed(xml):
    return ET.fromstring(xml)


def remarks(xml):
    return parsed(xml).find("detail/remarks").text


class StandardProfileUnchangedTest(unittest.TestCase):
    def test_the_standard_bytes_are_frozen(self):
        self.assertEqual(STANDARD_BYTES, cot.zmeta_to_cot(vessel_event()))
        self.assertEqual(STANDARD_BYTES, cot.zmeta_to_cot(vessel_event(), cot_config={"profile": "standard"}))
        self.assertEqual(STANDARD_BYTES, cot.zmeta_to_cot(vessel_event(), cot_config={}, now=NOW))

    def test_validate_cot_config_accepts_the_defaults(self):
        self.assertEqual("standard", cot.validate_cot_config(None))
        self.assertEqual("standard", cot.validate_cot_config({}))
        self.assertEqual("standard", cot.validate_cot_config({"how": "m-g"}))

    def test_the_original_event_is_not_mutated_by_either_profile(self):
        event = vessel_event()
        frozen = copy.deepcopy(event)
        cot.zmeta_to_cot(event)
        render(event)
        self.assertEqual(frozen, event)


class CdsShapeTest(unittest.TestCase):
    def test_detail_children_are_exactly_the_standard_ones_that_survive(self):
        root = parsed(render(vessel_event()))
        self.assertEqual(["contact", "remarks", "track"], [child.tag for child in root.find("detail")])
        self.assertEqual("2.0", root.get("version"))
        self.assertEqual(["point", "detail"], [child.tag for child in root])

    def test_uid_type_time_point_contact_and_track_are_the_standard_ones(self):
        event = vessel_event()
        standard = parsed(cot.zmeta_to_cot(event, cot_config={"how": "m-f"}))
        cds = parsed(render(event))
        for name in ("uid", "type", "time", "start", "how", "version"):
            self.assertEqual(standard.get(name), cds.get(name), name)
        self.assertEqual(standard.find("point").attrib, cds.find("point").attrib)
        self.assertEqual(standard.find("detail/contact").attrib, cds.find("detail/contact").attrib)
        self.assertEqual(standard.find("detail/track").attrib, cds.find("detail/track").attrib)
        self.assertEqual("fused:vessel/0417", cds.get("uid"))

    def test_precisionlocation_is_kept_when_the_deployment_asserts_a_source(self):
        root = parsed(render(vessel_event(), dict(CDS, geopointsrc="AIS")))
        precision = root.find("detail/precisionlocation")
        self.assertIsNotNone(precision)
        self.assertEqual("AIS", precision.get("geopointsrc"))
        self.assertEqual(["contact", "remarks", "track", "precisionlocation"], [c.tag for c in root.find("detail")])

    def test_point_attributes_are_plain_decimals(self):
        event = vessel_event(**{"payload.geo.lat": 0.00001, "payload.geo.lon": -0.000002,
                                "payload.geo.error_ellipse_m.semi_major": 0.00001})
        self.assertIn("1e-05", cot.zmeta_to_cot(event))
        point = parsed(render(event)).find("point")
        for name in ("lat", "lon", "hae", "ce", "le"):
            with self.subTest(attr=name):
                self.assertRegex(point.get(name), r"^-?[0-9]+(\.[0-9]+)?$")
        self.assertEqual("0.00001", point.get("lat"))
        self.assertEqual("-0.000002", point.get("lon"))


class CdsRemarksTest(unittest.TestCase):
    def test_the_full_line_for_the_reference_event(self):
        config = dict(CDS, attribution="Synthetic attribution words")
        self.assertEqual(
            "track via ZMeta; affiliation not asserted; confidence=0.72; 2-D fix, altitude not asserted; "
            "producer fusion-engine; Synthetic attribution words",
            remarks(render(vessel_event(), config)),
        )

    def test_producer_free_text_does_not_cross(self):
        event = vessel_event(**{"payload.source_summary": ["a narrative the guard never saw"]})
        text = remarks(render(event))
        self.assertNotIn("narrative", text)
        self.assertNotIn("Error ellipse", text)
        self.assertIn("narrative", cot.zmeta_to_cot(event))

    def test_the_markers_survive_a_long_label_and_attribution(self):
        event = vessel_event(**{"payload.class": "x" * 80})
        config = dict(CDS, attribution="y" * 500)
        text = remarks(render(event, config))
        self.assertLessEqual(len(text), cot.CDS_REMARKS_MAX)
        for marker in ("track via ZMeta", "affiliation not asserted", "confidence=0.72",
                       "2-D fix, altitude not asserted", "producer fusion-engine"):
            self.assertIn(marker, text, marker)
        # The label is capped by the standard quoting rule, so it fits whole and closed.
        self.assertIn('class "' + "x" * 64 + '..."', text)
        self.assertTrue(text.endswith("; " + "y" * (200 - len(text.rsplit("; ", 1)[0]) - 2)), text)

    def test_a_long_producer_name_is_cut_and_the_markers_before_it_survive(self):
        event = vessel_event(**{"source.producer": "p" * 300})
        text = remarks(render(event))
        self.assertEqual(cot.CDS_REMARKS_MAX, len(text))
        self.assertTrue(text.startswith(
            "track via ZMeta; affiliation not asserted; confidence=0.72; 2-D fix, altitude not asserted; producer ppp"), text)

    def test_a_3d_fix_does_not_claim_to_be_2d(self):
        event = vessel_event(**{"payload.geo.dimensionality": None, "payload.geo.alt_m": 3.0})
        self.assertNotIn("2-D fix", remarks(render(event)))

    def test_an_absent_altitude_without_the_token_is_not_a_2d_claim(self):
        event = vessel_event(**{"payload.geo.dimensionality": None})
        xml = render(event)
        self.assertIsNotNone(xml)
        self.assertNotIn("2-D fix", remarks(xml))
        self.assertEqual("9999999.0", parsed(xml).find("point").get("hae"))

    def test_no_confidence_means_no_confidence_token(self):
        text = remarks(render(vessel_event(confidence=None)))
        self.assertNotIn("confidence", text)
        self.assertIn("affiliation not asserted", text)

    def test_a_label_class_is_quoted_after_the_link_rule(self):
        event = vessel_event(**{"payload.class": 'car; see https://example.invalid/x "quoted"'})
        text = remarks(render(event))
        self.assertIsNone(LINK.search(text), text)
        # The part separator is replaced inside every part, the label included.
        self.assertIn('class "car, see \\"quoted\\""', text)
        self.assertEqual("a-u-G", parsed(render(event)).get("type"))
        # The link rule runs before the quoting, so a link at the end of the
        # label cannot eat the closing quote.
        text = remarks(render(vessel_event(**{"payload.class": "car https://example.invalid/x"})))
        self.assertTrue(text.endswith('; class "car"'), text)

    def test_a_label_that_does_not_fit_whole_is_omitted_not_cut(self):
        event = vessel_event(**{"source.producer": "p" * 70, "payload.class": "car; confidence=0.99"})
        text = remarks(render(event))
        self.assertLessEqual(len(text), 200)
        self.assertNotIn("class", text)
        self.assertNotIn("0.99", text)
        # With room, the same label goes whole.
        text = remarks(render(vessel_event(**{"payload.class": "car; confidence=0.99"})))
        self.assertTrue(text.endswith('; class "car, confidence=0.99"'), text)

    def test_a_control_character_in_a_remarks_part_becomes_a_space(self):
        event = vessel_event(**{"source.producer": "fusion\x01engine"})
        xml = render(event)
        self.assertIsNotNone(xml)
        self.assertIn("producer fusion engine", remarks(xml))

    def test_remarks_is_one_line(self):
        config = dict(CDS, attribution="line one\nline two\t  three")
        text = remarks(render(vessel_event(), config))
        self.assertNotIn("\n", text)
        self.assertIn("line one line two three", text)
        self.assertEqual(200, cot.CDS_REMARKS_MAX)

    def test_replay_display_mode_is_refused_at_config_time(self):
        # In that mode the event's time is re-stamped to now, and the age
        # rule could not see a day-old event.
        with self.assertRaises(ValueError):
            cot.validate_cot_config(dict(CDS, use_wall_clock=True))
        old = vessel_event(**{"event.ts": (NOW - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")})
        self.assertIsNone(render(old, dict(CDS, use_wall_clock=True)))
        self.assertIsNone(render(vessel_event(**{"event.ts": None}), dict(CDS, use_wall_clock=True)))
        # The standard profile keeps the mode.
        self.assertIsNotNone(cot.zmeta_to_cot(old, cot_config={"use_wall_clock": True}, now=NOW))

    def test_a_misspelled_cds_key_is_refused(self):
        for key in ("stale_ceiling_s", "max_age", "attribution_text", "How"):
            with self.subTest(key=key):
                with self.assertRaises(ValueError):
                    cot.validate_cot_config(dict(CDS, **{key: 30}))
        # The standard profile is unchanged: unknown keys are ignored there.
        self.assertEqual("standard", cot.validate_cot_config({"stale_ceiling_s": 30}))


class CdsLinksTest(unittest.TestCase):
    def test_links_are_stripped_from_event_words_and_the_words_stay(self):
        event = vessel_event(**{"source.producer": "fusion-engine, HTTPS://EXAMPLE.INVALID/about more words"})
        text = remarks(render(event))
        self.assertIsNone(LINK.search(text), text)
        self.assertTrue(text.endswith("; producer fusion-engine more words"), text)

    def test_an_attribution_with_a_link_of_any_scheme_is_a_config_error(self):
        for bad in ("words, https://example.invalid/x", "HTTP://EXAMPLE.INVALID", "see ftp://example.invalid", "x tak://y"):
            with self.subTest(attribution=bad):
                with self.assertRaises(ValueError):
                    cot.validate_cot_config({"profile": "cds", "how": "m-f", "attribution": bad})
                self.assertIsNone(render(vessel_event(), dict(CDS, attribution=bad)))
        self.assertEqual("cds", cot.validate_cot_config({"profile": "cds", "how": "m-f", "attribution": "words: example.invalid/x"}))

    def test_the_standard_profile_keeps_a_link_so_the_assertion_is_live(self):
        event = vessel_event(**{"source.producer": "feed, https://example.invalid/feed", "payload.class": "car https://example.invalid/c"})
        self.assertIsNotNone(LINK.search(cot.zmeta_to_cot(event, cot_config={"how": "m-f"})))
        xml = render(event)
        self.assertIsNone(LINK.search(xml))
        self.assertIn("producer feed", remarks(xml))

    def test_a_link_outside_remarks_refuses_the_event(self):
        self.assertIsNone(render(vessel_event(**{"payload.callsign": "see http://example.invalid"})))
        self.assertIsNone(render(vessel_event(**{"payload.callsign": "see HTTP://EXAMPLE.INVALID"})))

    def test_validate_cot_config_refuses_an_attribution_that_is_not_a_string(self):
        with self.assertRaises(ValueError):
            cot.validate_cot_config({"profile": "cds", "how": "m-f", "attribution": 5})

    def test_validate_cot_config_refuses_an_attribution_with_a_control_character(self):
        with self.assertRaises(ValueError):
            cot.validate_cot_config({"profile": "cds", "how": "m-f", "attribution": "words\x01more"})
        self.assertIsNone(render(vessel_event(), dict(CDS, attribution="words\x01more")))
        self.assertEqual("cds", cot.validate_cot_config({"profile": "cds", "how": "m-f", "attribution": "two\twords\nmore"}))


class CdsHowAndWindowTest(unittest.TestCase):
    def test_how_is_required_and_asserted(self):
        self.assertIsNone(render(vessel_event(), {"profile": "cds"}))
        self.assertEqual("m-f", parsed(render(vessel_event())).get("how"))
        self.assertEqual("m-r", parsed(render(vessel_event(), {"profile": "cds", "how": "m-r"})).get("how"))

    def test_validate_cot_config_refuses_a_how_that_is_not_a_token(self):
        for bad in (None, True, 5, "GPS", "M-F", "m-f junk", "m-f\n", "m-", "-f", "mf"):
            with self.subTest(how=bad):
                with self.assertRaises(ValueError):
                    cot.validate_cot_config({"profile": "cds", "how": bad})
        for good in ("m-f", "m-r", "h-e", "m-g-n"):
            with self.subTest(how=good):
                self.assertEqual("cds", cot.validate_cot_config({"profile": "cds", "how": good}))

    def test_validate_cot_config_refuses_a_bad_window_or_age(self):
        for key in ("stale_window_s", "max_age_s"):
            for bad in (0, -5, float("nan"), float("inf"), "120", True, 10 ** 12, 1e300, cot.CDS_MAX_WINDOW_S + 1):
                with self.subTest(key=key, value=bad):
                    with self.assertRaises(ValueError):
                        cot.validate_cot_config({"profile": "cds", "how": "m-f", key: bad})
        self.assertEqual("cds", cot.validate_cot_config({"profile": "cds", "how": "m-f", "stale_window_s": 60, "max_age_s": 30}))
        self.assertEqual("cds", cot.validate_cot_config({"profile": "cds", "how": "m-f", "stale_window_s": cot.CDS_MAX_WINDOW_S}))

    def test_the_maximum_age_may_not_exceed_the_window(self):
        with self.assertRaises(ValueError):
            cot.validate_cot_config({"profile": "cds", "how": "m-f", "stale_window_s": 30, "max_age_s": 60})
        with self.assertRaises(ValueError):
            cot.validate_cot_config({"profile": "cds", "how": "m-f", "max_age_s": 121})
        self.assertEqual("cds", cot.validate_cot_config({"profile": "cds", "how": "m-f", "max_age_s": 120}))

    def test_an_unknown_profile_is_refused_at_config_and_at_egress(self):
        with self.assertRaises(ValueError):
            cot.validate_cot_config({"profile": "strict", "how": "m-f"})
        self.assertIsNone(render(vessel_event(), {"profile": "strict", "how": "m-f"}))


class CdsStaleAndAgeTest(unittest.TestCase):
    def test_stale_is_the_projection_time_plus_the_window(self):
        root = parsed(render(vessel_event()))
        self.assertEqual((NOW + timedelta(seconds=120)).strftime(STAMP), root.get("stale"))
        self.assertEqual("2026-09-29T19:58:30.000000Z", root.get("time"))
        self.assertEqual(root.get("time"), root.get("start"))

    def test_the_window_is_the_deployments_to_set(self):
        root = parsed(render(vessel_event(), dict(CDS, stale_window_s=30)))
        self.assertEqual((NOW + timedelta(seconds=30)).strftime(STAMP), root.get("stale"))

    def test_the_maximum_age_defaults_to_the_window(self):
        aged_60 = vessel_event(**{"event.ts": (NOW - timedelta(seconds=60)).strftime("%Y-%m-%dT%H:%M:%SZ")})
        self.assertIsNone(render(aged_60, dict(CDS, stale_window_s=30)))
        self.assertIsNotNone(render(aged_60, dict(CDS, stale_window_s=90)))
        self.assertIsNotNone(render(aged_60, dict(CDS, stale_window_s=90, max_age_s=61)))
        self.assertIsNone(render(aged_60, dict(CDS, stale_window_s=90, max_age_s=59)))

    def test_a_shorter_claim_is_carried(self):
        # ts is NOW - 30 s, so a 60 s claim ends at NOW + 30 s, inside the window.
        root = parsed(render(vessel_event(**{"payload.valid_for_ms": 60000})))
        self.assertEqual((NOW + timedelta(seconds=30)).strftime(STAMP), root.get("stale"))

    def test_the_window_caps_a_longer_claim(self):
        for claim in (300000, 3600000):
            with self.subTest(valid_for_ms=claim):
                root = parsed(render(vessel_event(**{"payload.valid_for_ms": claim})))
                self.assertEqual((NOW + timedelta(seconds=120)).strftime(STAMP), root.get("stale"))

    def test_a_lapsed_claim_is_refused_and_named(self):
        lapsed = vessel_event(**{"payload.valid_for_ms": 5000})
        refusal = {}
        self.assertIsNone(cot.zmeta_to_cot(lapsed, cot_config=dict(CDS), now=NOW, refusal=refusal))
        self.assertEqual({"reason": "VALIDITY_LAPSED"}, refusal)
        # Control: the standard profile still renders the same event.
        self.assertIsNotNone(cot.zmeta_to_cot(lapsed))
        # A claim ending exactly at the projection instant has lapsed.
        self.assertIsNone(render(vessel_event(**{"payload.valid_for_ms": 30000})))
        self.assertIsNotNone(render(vessel_event(**{"payload.valid_for_ms": 30001})))

    def test_send_stale_carries_the_past_stale(self):
        config = dict(CDS, lapsed_validity="send_stale")
        root = parsed(render(vessel_event(**{"payload.valid_for_ms": 5000}), config))
        self.assertEqual("2026-09-29T19:58:35.000000Z", root.get("stale"))
        self.assertEqual("2026-09-29T19:58:30.000000Z", root.get("time"))
        self.assertLess(root.get("stale"), NOW.strftime(STAMP))
        # A live claim is unaffected by the option.
        live = parsed(render(vessel_event(**{"payload.valid_for_ms": 60000}), config))
        self.assertEqual((NOW + timedelta(seconds=30)).strftime(STAMP), live.get("stale"))

    def test_send_stale_is_still_bound_by_the_maximum_age(self):
        old = vessel_event(**{
            "event.ts": (NOW - timedelta(seconds=121)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "payload.valid_for_ms": 5000,
        })
        refusal = {}
        config = dict(CDS, lapsed_validity="send_stale")
        self.assertIsNone(cot.zmeta_to_cot(old, cot_config=config, now=NOW, refusal=refusal))
        # The age rule refused it, so no lapsed-validity reason is recorded.
        self.assertEqual({}, refusal)

    def test_lapsed_validity_must_be_a_known_value(self):
        for value in ("keep_window", "", None, True):
            with self.subTest(value=value):
                config = dict(CDS, lapsed_validity=value)
                with self.assertRaises(ValueError):
                    cot.validate_cot_config(config)
                self.assertIsNone(render(vessel_event(), config))
        for value in ("refuse", "send_stale"):
            self.assertEqual("cds", cot.validate_cot_config(dict(CDS, lapsed_validity=value)))

    def test_an_affiliation_refusal_is_named_and_others_are_not(self):
        refusal = {}
        hostile = vessel_event(**{"payload.class": "a-h-S"})
        self.assertIsNone(cot.zmeta_to_cot(hostile, cot_config=dict(CDS), now=NOW, refusal=refusal))
        self.assertEqual({"reason": "AFFILIATION_ASSERTED"}, refusal)
        other = {}
        no_track = vessel_event(**{"payload.track_id": None})
        self.assertIsNone(cot.zmeta_to_cot(no_track, cot_config=dict(CDS), now=NOW, refusal=other))
        self.assertEqual({}, other)
        # The standard profile never writes a reason.
        standard = {}
        self.assertIsNotNone(cot.zmeta_to_cot(hostile, refusal=standard))
        self.assertEqual({}, standard)

    def test_an_event_older_than_the_maximum_age_is_refused(self):
        old = vessel_event(**{"event.ts": (NOW - timedelta(seconds=121)).strftime("%Y-%m-%dT%H:%M:%SZ")})
        self.assertIsNone(render(old))
        self.assertIsNotNone(cot.zmeta_to_cot(old))
        recent = vessel_event(**{"event.ts": (NOW - timedelta(seconds=119)).strftime("%Y-%m-%dT%H:%M:%SZ")})
        self.assertIsNotNone(render(recent))
        self.assertIsNotNone(render(old, dict(CDS, stale_window_s=600, max_age_s=600)))

    def test_an_event_dated_beyond_the_maximum_age_in_the_future_is_refused(self):
        ahead = vessel_event(**{"event.ts": (NOW + timedelta(seconds=121)).strftime("%Y-%m-%dT%H:%M:%SZ")})
        self.assertIsNone(render(ahead))
        within = vessel_event(**{"event.ts": (NOW + timedelta(seconds=119)).strftime("%Y-%m-%dT%H:%M:%SZ")})
        self.assertIsNotNone(render(within))
        # With the age shorter than the window, the age rule alone refuses a
        # future event that stale-after-time would still let through.
        ahead_60 = vessel_event(**{"event.ts": (NOW + timedelta(seconds=60)).strftime("%Y-%m-%dT%H:%M:%SZ")})
        self.assertIsNone(render(ahead_60, dict(CDS, max_age_s=30)))
        self.assertIsNotNone(render(ahead_60, dict(CDS, max_age_s=90)))

    def test_the_projection_instant_defaults_to_the_clock(self):
        before = datetime.now(timezone.utc)
        event = vessel_event(**{"event.ts": before.strftime("%Y-%m-%dT%H:%M:%SZ")})
        xml = cot.zmeta_to_cot(event, cot_config=dict(CDS))
        self.assertIsNotNone(xml)
        stale = datetime.strptime(parsed(xml).get("stale"), STAMP).replace(tzinfo=timezone.utc)
        after = datetime.now(timezone.utc)
        self.assertGreaterEqual(stale, before + timedelta(seconds=120))
        self.assertLessEqual(stale, after + timedelta(seconds=120))

    def test_the_standard_profile_honours_the_injected_instant_in_wall_clock_mode(self):
        standard = parsed(cot.zmeta_to_cot(vessel_event(), cot_config={"use_wall_clock": True}, now=NOW))
        self.assertEqual(NOW.strftime(STAMP), standard.get("time"))
        self.assertEqual(NOW.strftime(STAMP), standard.get("start"))


class CdsHardeningTest(unittest.TestCase):
    """Inputs the second refutation round built: JSON-decodable, some schema-invalid."""

    def test_a_non_utc_or_naive_instant_is_taken_as_the_same_moment(self):
        shifted = NOW.astimezone(timezone(timedelta(hours=5)))
        self.assertEqual(parsed(render(vessel_event())).get("stale"), parsed(render(vessel_event(), now=shifted)).get("stale"))
        naive = NOW.replace(tzinfo=None)
        self.assertEqual(parsed(render(vessel_event())).get("stale"), parsed(render(vessel_event(), now=naive)).get("stale"))
        standard = parsed(cot.zmeta_to_cot(vessel_event(), cot_config={"use_wall_clock": True}, now=shifted))
        self.assertEqual(NOW.strftime(STAMP), standard.get("time"))

    def test_a_source_that_is_not_an_object_renders_without_a_producer(self):
        for source in (None, "gw", ["a"], 5):
            with self.subTest(source=source):
                event = vessel_event(); event["source"] = source
                self.assertIsNotNone(cot.zmeta_to_cot(event))
                xml = render(event)
                self.assertIsNotNone(xml)
                self.assertNotIn("producer", remarks(xml))

    def test_a_confidence_that_is_not_a_number_in_range_is_not_sent(self):
        # A non-finite confidence is refused by the standard path before the profile runs.
        self.assertIsNone(render(vessel_event(confidence=float("nan"))))
        for bad in ("x" * 300, "0.99; operator verified hostile", 10 ** 250, 1.5, -0.1, True):
            with self.subTest(confidence=bad):
                text = remarks(render(vessel_event(confidence=bad)))
                self.assertLessEqual(len(text), 200)
                self.assertNotIn("confidence", text)
                self.assertNotIn("hostile", text)
        self.assertIn("confidence=1", remarks(render(vessel_event(confidence=1))))
        self.assertIn("confidence=0", remarks(render(vessel_event(confidence=0))))

    def test_a_producer_name_cannot_forge_a_marker(self):
        text = remarks(render(vessel_event(confidence=None, **{"source.producer": "x; confidence=0.99"})))
        self.assertNotIn("; confidence=0.99", text)
        self.assertIn("producer x, confidence=0.99", text)

    def test_a_future_event_inside_the_window_keeps_stale_after_time(self):
        ahead = vessel_event(**{"event.ts": (NOW + timedelta(seconds=50)).strftime("%Y-%m-%dT%H:%M:%SZ")})
        root = parsed(render(ahead, dict(CDS, stale_window_s=60)))
        self.assertGreaterEqual(root.get("stale"), root.get("time"))

    def test_a_string_point_value_cannot_smuggle_elements(self):
        smuggle = '3" le="1" ce="1" /><detail /><point lat="1" lon="2" hae="3'
        event = vessel_event(**{"payload.geo.dimensionality": None, "payload.geo.alt_m": smuggle})
        self.assertIsNone(render(event))
        self.assertIsNone(render(vessel_event(**{"payload.geo.lat": "1_2.5"})))
        self.assertIsNotNone(render(vessel_event(**{"payload.geo.lat": "12.5"})))

    def test_a_bare_scheme_is_removed_not_refused(self):
        for producer in ("see http://", "see http:// more", "see HTTPS:// more"):
            with self.subTest(producer=producer):
                xml = render(vessel_event(**{"source.producer": producer}))
                self.assertIsNotNone(xml)
                self.assertIn("producer see", remarks(xml))
                self.assertIsNone(LINK.search(xml))

    def test_a_lone_surrogate_refuses_or_is_replaced(self):
        self.assertIsNone(render(vessel_event(**{"payload.callsign": "a\ud800b"})))
        xml = render(vessel_event(**{"source.producer": "a\ud800b"}))
        self.assertIsNotNone(xml)
        xml.encode("utf-8")
        self.assertIn("producer a b", remarks(xml))
        self.assertIsNotNone(render(vessel_event(**{"source.producer": "a\uffffb"})))

    def test_a_scheme_of_any_letters_in_the_attribution_is_refused(self):
        with self.assertRaises(ValueError):
            cot.validate_cot_config({"profile": "cds", "how": "m-f", "attribution": "see http\u017f://example.invalid/x"})


class CdsRefusalsTest(unittest.TestCase):
    def test_an_asserted_affiliation_is_refused_rather_than_retyped(self):
        for cot_type in AFFILIATIONS:
            with self.subTest(type=cot_type):
                event = vessel_event(**{"payload.class": cot_type})
                self.assertIsNotNone(cot.zmeta_to_cot(event))
                self.assertIsNone(render(event))
        for cot_type in ("a-u-S", "a-u-G-E-V", "a-u-A"):
            with self.subTest(type=cot_type):
                self.assertEqual(cot_type, parsed(render(vessel_event(**{"payload.class": cot_type}))).get("type"))

    def test_a_label_class_still_projects_on_the_unknown_branch(self):
        root = parsed(render(vessel_event(**{"payload.class": "car"})))
        self.assertEqual("a-u-G", root.get("type"))
        self.assertIn('class "car"', root.find("detail/remarks").text)

    def test_standard_refusals_still_refuse(self):
        # On the default clock, so the refusal is the missing ts and not the age rule.
        self.assertIsNone(cot.zmeta_to_cot(vessel_event(**{"event.ts": None}), cot_config=dict(CDS, max_age_s=cot.CDS_MAX_WINDOW_S, stale_window_s=cot.CDS_MAX_WINDOW_S)))
        self.assertIsNone(render(vessel_event(**{"payload.geo": None})))
        # The standard stale arithmetic runs first, so its refusals are inherited.
        self.assertIsNone(render(vessel_event(**{"payload.valid_for_ms": 10 ** 15})))

    def test_a_point_attribute_that_is_not_a_number_refuses(self):
        for key in ("default_le", "default_ce"):
            with self.subTest(key=key):
                self.assertIsNone(render(vessel_event(**{"payload.geo.error_ellipse_m": None}), dict(CDS, **{key: "unknown"})))
                self.assertIsNotNone(render(vessel_event(**{"payload.geo.error_ellipse_m": None}), dict(CDS, **{key: 50})))

    def test_a_control_character_refuses_instead_of_raising(self):
        for field in ("payload.callsign", "payload.track_id"):
            with self.subTest(field=field):
                event = vessel_event(**{field: "bad\x01value"})
                self.assertIsNone(render(event))

    def test_the_uncertainty_circle_wrapper_refuses_under_the_profile(self):
        # The instant is inside the age window, so the refusal is the profile's.
        self.assertIsNone(cot.zmeta_to_cot_uncertainty_circle(vessel_event(), 50.0, cot_config=dict(CDS), now=NOW))
        self.assertIsNotNone(render(vessel_event(), now=NOW))
        standard = parsed(cot.zmeta_to_cot_uncertainty_circle(vessel_event(), 50.0, now=NOW))
        self.assertIsNotNone(standard.find("detail/circle"))


class CdsStructureTest(unittest.TestCase):
    """The public CoT event schema's structure, checked without the schema."""

    def structural_check(self, xml):
        root = parsed(xml)
        self.assertEqual("event", root.tag)
        for name in ("version", "uid", "type", "time", "start", "stale", "how"):
            self.assertTrue(root.get(name), name)
        self.assertRegex(root.get("type"), r"^a-u-[A-Z](-[A-Z0-9]+)*$")
        self.assertRegex(root.get("how"), r"^[a-z]-[a-z](-[a-z]+)*$")
        for name in ("time", "start", "stale"):
            datetime.strptime(root.get(name), STAMP)
        self.assertEqual(["point", "detail"], [child.tag for child in root])
        point = root.find("point")
        for name in ("lat", "lon", "hae", "ce", "le"):
            self.assertRegex(point.get(name), r"^-?[0-9]+(\.[0-9]+)?$", name)
        self.assertLessEqual({child.tag for child in root.find("detail")}, {"contact", "track", "remarks", "precisionlocation"})
        self.assertLessEqual(len(root.find("detail/remarks").text), 200)
        self.assertIsNone(LINK.search(xml))

    def test_every_rendered_shape_holds_the_structure(self):
        for label, event, config in (
            ("vessel", vessel_event(), CDS),
            ("labelled", vessel_event(**{"payload.class": "car"}), CDS),
            ("3-D with source", vessel_event(**{"payload.geo.dimensionality": None, "payload.geo.alt_m": 3.0}), dict(CDS, geopointsrc="AIS")),
            ("near zero", vessel_event(**{"payload.geo.lat": 0.00001, "payload.geo.lon": -0.000002}), CDS),
            ("attributed", vessel_event(), dict(CDS, attribution="words")),
        ):
            with self.subTest(event=label):
                xml = render(event, config)
                self.assertIsNotNone(xml)
                self.structural_check(xml)


class CdsPublicSchemaTest(unittest.TestCase):
    """Validates against the public CoT event schema when one is available.

    Set COT_EVENT_XSD to a copy of Event-PUBLIC.xsd and install lxml; the
    repository vendors neither. Skipped otherwise, and the skip is reported.
    """

    def test_output_validates_against_the_public_event_schema(self):
        xsd = os.environ.get("COT_EVENT_XSD")
        if not xsd or not Path(xsd).is_file():
            self.skipTest("COT_EVENT_XSD does not name a schema file")
        try:
            from lxml import etree
        except ImportError:
            self.skipTest("lxml is not installed")
        schema = etree.XMLSchema(etree.parse(xsd))
        for label, event, config in (
            ("vessel", vessel_event(), dict(CDS, geopointsrc="AIS")),
            ("labelled", vessel_event(**{"payload.class": "car"}), CDS),
            ("3-D", vessel_event(**{"payload.geo.dimensionality": None, "payload.geo.alt_m": 3.0}), CDS),
            ("near zero", vessel_event(**{"payload.geo.lat": 0.00001, "payload.geo.lon": -0.000002}), CDS),
        ):
            with self.subTest(event=label):
                xml = render(event, config)
                self.assertIsNotNone(xml)
                doc = etree.fromstring(xml.encode("utf-8"))
                self.assertTrue(schema.validate(doc), [str(e) for e in schema.error_log])


if __name__ == "__main__":
    unittest.main()
