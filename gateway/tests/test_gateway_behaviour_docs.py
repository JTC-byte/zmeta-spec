"""The documents a deployer or consumer reads name three gateway behaviours.

From the pre-cut range review of 2026-11-14 (S5): the strip guard's protected
prefixes, the members of the admission record (contract 4.5.1), and the
DECODE_AMBIGUOUS refusal were missing from configs/README.md,
gateway/README.md and policy/README.md. Each check below reads the name from
the code or the policy where it can, so a later change to the behaviour fails
here until the document follows it. The seeded review of the same day added
the checks that read the members from the records the code writes, the
declined-factor range, and the README's account of each auto-lane case.
"""

import importlib.util
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

VALIDATORS_PATH = ROOT / "gateway" / "src" / "validators.py"
spec = importlib.util.spec_from_file_location("zmeta_validators_bd", VALIDATORS_PATH)
validators = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validators)
GATEWAY_PATH = ROOT / "gateway" / "src" / "gateway.py"
spec_gw = importlib.util.spec_from_file_location("zmeta_gateway_bd", GATEWAY_PATH)
gateway = importlib.util.module_from_spec(spec_gw)
spec_gw.loader.exec_module(gateway)

CONFIGS_README = ROOT / "configs" / "README.md"
GATEWAY_README = ROOT / "gateway" / "README.md"
POLICY_README = ROOT / "policy" / "README.md"

NUMBER_WORDS = {
    1: "one", 2: "two", 3: "three", 4: "four", 5: "five",
    6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten",
}


def _text(path):
    return path.read_text(encoding="utf-8")


def _has(test, needle, text, where):
    """assertIn without printing the whole document on a failure."""
    test.assertTrue(needle in text, f"{where} does not contain {needle!r}")


def _section(text, heading):
    """The body of one `### ` section of a README, without the heading."""
    start = text.find(f"\n### {heading}\n")
    if start < 0:
        raise AssertionError(f"no '### {heading}' section")
    body = text[start + len(heading) + 6:]
    end = body.find("\n### ")
    return body if end < 0 else body[:end]


FACTOR_KEYS = {"confidence_reduction_factor", "valid_for_ms_reduction_factor"}


def _event():
    return {"confidence": 0.8, "payload": {"valid_for_ms": 1000}, "event": {"event_type": "STATE_EVENT"}}


def _records(event):
    return event["payload"].get("extensions", {}).get("risk_adjudication", [])


def _promotion_degrade(factor):
    """The external-promotion degrade path, as validators.py runs it."""
    event = _event()
    violation = {"code": "PRODUCER_NOT_ALLOWED", "details": {
        "action": "degrade", "risk_dimension": "producer_authority",
        "policy_decision": "DEGRADED_ACCEPT"}}
    validators.apply_external_promotion_policy_action(
        event, [violation],
        {"external_state_promotion": {"degrade": {"confidence_reduction_factor": factor}}})
    return event


def _timing_freshness(factor):
    """The timing-freshness degradation at admission."""
    event = _event()
    violation = {"code": "TIMING_STATUS_STALE", "details": {
        "action": "degrade", "risk_dimension": "timing",
        "policy_decision": "DEGRADED_ACCEPT"}}
    validators.apply_timing_freshness_degradation(
        event, [violation], {"degrade": {"confidence_reduction_factor": factor}})
    return event


class _UnsyncedTiming:
    def get_timing(self, event):
        return "key", {"sync_state": "UNSYNCED"}


def _timing_loss(factor):
    """The timing_loss failure mode on an outgoing STATE."""
    event = _event()
    gateway._apply_failure_mode_degradation(
        event, {"timing_loss": {"enabled": True, "confidence_reduction_factor": factor}},
        _UnsyncedTiming())
    return event


def _admission_members():
    """The member names the reference writes into a record's effects.

    The claimed members come from the promotion path's record when both
    values change, and the declined member from its record when both factors
    are declined: each is read from what the code writes, not from its text.
    """
    reduced = _records(_promotion_degrade(2.0))
    declined = _records(_promotion_degrade(0.5))
    if len(reduced) != 1 or len(declined) != 1:
        raise AssertionError("the promotion degrade path no longer writes one record")
    claimed = sorted(set(reduced[0]["effects"]) - FACTOR_KEYS)
    return claimed + sorted(set(declined[0]["effects"]) - FACTOR_KEYS)


class ConfigsReadmeStripPathsTest(unittest.TestCase):
    def test_every_protected_prefix_is_named(self):
        text = _text(CONFIGS_README)
        prefixes = list(gateway.PROTECTED_STRIP_PATH_PREFIXES)
        self.assertGreaterEqual(len(prefixes), 3)
        for prefix in prefixes:
            _has(self, f"`{prefix}`", text, "configs/README.md")

    def test_the_stated_count_is_the_count(self):
        text = _text(CONFIGS_README)
        found = re.findall(r"\b(\w+) path prefixes are protected", text)
        self.assertEqual(1, len(found), found)
        expected = NUMBER_WORDS[len(gateway.PROTECTED_STRIP_PATH_PREFIXES)]
        self.assertEqual(expected, found[0].lower())

    def test_the_command_start_gives_its_reason(self):
        text = " ".join(_text(CONFIGS_README).split())
        start = text.find("`payload.valid_from_ts`")
        self.assertGreaterEqual(start, 0)
        nearby = text[start:start + 400]
        self.assertIn("validity window", nearby)
        self.assertIn("contract 7.8", nearby)


class AdmissionRecordMembersTest(unittest.TestCase):
    def test_the_member_names_are_read_from_the_code(self):
        self.assertEqual(
            ["confidence_claimed", "valid_for_ms_claimed", "reduction_declined"],
            _admission_members(),
        )

    def test_the_two_timing_paths_write_the_confidence_member_alone(self):
        members = _admission_members()
        for name, event in (("timing freshness", _timing_freshness(2.0)),
                            ("timing_loss", _timing_loss(2.0))):
            records = _records(event)
            self.assertEqual(1, len(records), name)
            written = set(records[0]["effects"]) - FACTOR_KEYS
            self.assertEqual({"confidence_claimed"}, written, name)
            self.assertIn("confidence_claimed", members)
        section = " ".join(_section(_text(GATEWAY_README), "Admission records").split())
        self.assertIn("their records carry `confidence_claimed` alone", section)

    def test_the_declined_member_maps_each_factor_to_its_value(self):
        effects = _records(_promotion_degrade(0.5))[0]["effects"]
        self.assertEqual(
            {"confidence_reduction_factor": 0.5, "valid_for_ms_reduction_factor": 0.5},
            effects["reduction_declined"],
        )
        section = " ".join(_section(_text(GATEWAY_README), "Admission records").split())
        start = section.find("`effects.reduction_declined`")
        self.assertGreaterEqual(start, 0)
        self.assertIn("a mapping from the name of each reduction factor", section[start:start + 300])

    def test_the_gateway_readme_names_each_member_under_effects(self):
        section = _section(_text(GATEWAY_README), "Admission records")
        for member in _admission_members():
            _has(self, f"`effects.{member}`", section, "Admission records")

    def test_the_gateway_readme_states_where_the_producer_figure_is(self):
        section = " ".join(_section(_text(GATEWAY_README), "Admission records").split())
        self.assertIn("contract 4.5.1", section)
        self.assertIn("first record that carries", section)

    def test_the_policy_readme_names_each_member(self):
        text = _text(POLICY_README)
        for member in _admission_members():
            _has(self, f"`{member}`", text, "policy/README.md")

    def test_the_policy_readme_says_a_record_can_carry_both_values(self):
        # the promotion path's record carries both when both values change
        reduced = _records(_promotion_degrade(2.0))[0]["effects"]
        self.assertTrue({"confidence_claimed", "valid_for_ms_claimed"} <= set(reduced))
        text = " ".join(_text(POLICY_README).split())
        self.assertIn("`confidence_claimed`, `valid_for_ms_claimed` or both", text)


class DeclinedFactorStatementTest(unittest.TestCase):
    """The Admission records section's account of a declined factor holds for the code.

    A factor is a divisor. A factor above 0 and below 1 would raise the value
    and is declined on every path. A confidence_reduction_factor of 0 or less
    is read as the default 2.0 on the promotion and timing-freshness paths
    and declined on the timing_loss path; on the promotion path a
    valid_for_ms_reduction_factor of 0 or less is read as the confidence
    factor.
    """

    def test_a_factor_above_0_and_below_1_is_declined_on_every_path(self):
        promotion = _promotion_degrade(0.5)
        self.assertEqual(0.8, promotion["confidence"])
        self.assertIn("reduction_declined", _records(promotion)[0]["effects"])
        for name, event in (("timing freshness", _timing_freshness(0.5)),
                            ("timing_loss", _timing_loss(0.5))):
            self.assertEqual(0.8, event["confidence"], name)
            self.assertEqual([], _records(event), name)

    def test_a_factor_of_0_or_less_is_the_default_or_declined(self):
        for factor in (0, -1):
            for name, event in (("promotion", _promotion_degrade(factor)),
                                ("timing freshness", _timing_freshness(factor))):
                self.assertAlmostEqual(0.4, event["confidence"], msg=name)
                effects = _records(event)[0]["effects"]
                self.assertEqual(2.0, effects["confidence_reduction_factor"], name)
                self.assertEqual(0.8, effects["confidence_claimed"], name)
            loss = _timing_loss(factor)
            self.assertEqual(0.8, loss["confidence"])
            self.assertEqual([], _records(loss))
        event = _event()
        violation = {"code": "PRODUCER_NOT_ALLOWED", "details": {
            "action": "degrade", "risk_dimension": "producer_authority",
            "policy_decision": "DEGRADED_ACCEPT"}}
        validators.apply_external_promotion_policy_action(
            event, [violation], {"external_state_promotion": {"degrade": {
                "confidence_reduction_factor": 4.0, "valid_for_ms_reduction_factor": 0}}})
        self.assertEqual(250, event["payload"]["valid_for_ms"])

    def test_the_section_states_the_range_the_code_declines(self):
        section = " ".join(_section(_text(GATEWAY_README), "Admission records").split())
        self.assertEqual(2, section.count("factor above 0 and below 1"), section)
        self.assertIn("A `confidence_reduction_factor` of 0 or less is read as the default "
                      "2.0 on the promotion and timing-freshness paths and declined on the "
                      "`timing_loss` path; on the promotion path a "
                      "`valid_for_ms_reduction_factor` of 0 or less is read as the "
                      "confidence factor.", section)
        self.assertNotIn("a factor above 1", section.lower())
        self.assertNotIn("decline a factor below 1", section)


class GatewayReadmeDecodeRefusalTest(unittest.TestCase):
    def _section(self):
        return " ".join(_section(_text(GATEWAY_README), "Decode refusals").split())

    def test_the_section_names_the_code_and_what_it_refuses(self):
        section = self._section()
        self.assertIn("`DECODE_AMBIGUOUS`", section)
        self.assertIn("contract 3.5", section)
        self.assertIn("`lineage.based_on`", section)
        self.assertIn("wire type", section)

    def test_the_schema_invalid_sentence_names_the_dedicated_lanes(self):
        section = self._section()
        self.assertIn("On the `json`, `cbor`, `compact` and `proto` lanes, any other "
                      "datagram that fails to decode is refused as `SCHEMA_INVALID`", section)
        self.assertNotIn("Any other datagram that fails to decode", section)

    def test_the_duplicate_map_key_sentence_gives_the_selection(self):
        section = self._section()
        self.assertNotIn("booked for the maintainer's word", section)
        self.assertIn("for a branch after the next cut", section)

    def test_the_section_gives_the_v1_0_wire_form_from_policy(self):
        policy = validators.load_policy(ROOT / "policy")
        fallback = policy["semantics"]["system_event"]["schema_violation_v1_0_wire_fallback"]
        wire = fallback["DECODE_AMBIGUOUS"]
        section = self._section()
        self.assertIn(f"the diagnostic's `metrics.reason_code` is `{wire}`", section)
        self.assertIn("`metrics.diagnostic_code` carries `DECODE_AMBIGUOUS`", section)
        self.assertIn("`schema_violation_v1_0_wire_fallback`", section)

    def test_the_section_states_the_auto_lane_as_an_open_decision(self):
        section = self._section()
        self.assertIn("`auto` lane", section)
        self.assertIn("finding S2 of the pre-cut range review of 2026-11-14", section)
        self.assertIn("`docs/zmeta_refinement_handoff.md`", section)
        self.assertNotIn("pre-cut decision", section)
        self.assertNotIn("pre-cut decision", GATEWAY_PATH.read_text(encoding="utf-8"))

    def test_the_section_names_each_case_the_auto_lane_tests_hold(self):
        section = self._section()
        for case in (
            "A compact datagram cut short in transit, a compact datagram with one "
            "trailing byte, a truncated CBOR datagram and plain text such as "
            "`hello world` read this way.",
            "The same truncated compact datagram reads `SCHEMA_INVALID` on the "
            "`compact` lane.",
            "one with seven reads `SCHEMA_INVALID`",
            "A datagram that opens with `{` or `[` and does not parse as JSON is "
            "read as CBOR and the compact mapping only, and reads `SCHEMA_INVALID` "
            "when that decode fails.",
        ):
            self.assertIn(case, section)
        self.assertNotIn("behaviour", section)


class AutoLaneStatementIsTrueTest(unittest.TestCase):
    """The README's account of the auto lane holds for the code as it is.

    When the open decision on the auto lane is taken, this test and the
    README's Decode refusals section change in the same commit.
    """

    def _diagnostic(self, message, encoding):
        validator = validators.load_schema(ROOT / "schema" / "zmeta-event-1.0.schema.json")
        policy = validators.load_policy(ROOT / "policy")
        outputs = gateway.process_message(
            message, validator, policy, "L", gateway.TaskDedupeCache(), encoding
        )
        self.assertEqual(1, len(outputs))
        return outputs[0]["payload"]["metrics"]

    def _example(self, index):
        line = (ROOT / "examples" / "zmeta-examples-1.0.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()[index]
        return json.loads(line)

    def _first_example(self):
        event = self._example(0)
        self.assertEqual(5, len(event), "the first example is a five-member event")
        return event

    def _truncated_compact(self):
        return gateway._encode_message(self._first_example(), "compact")[:-1]

    def _ambiguous(self, metrics):
        self.assertEqual("SCHEMA_INVALID", metrics["reason_code"])
        self.assertEqual("DECODE_AMBIGUOUS", metrics.get("diagnostic_code"))

    def _invalid(self, metrics):
        self.assertEqual("SCHEMA_INVALID", metrics["reason_code"])
        self.assertNotIn("diagnostic_code", metrics)

    def test_a_compact_datagram_with_one_trailing_byte_reads_decode_ambiguous_on_auto(self):
        message = gateway._encode_message(self._first_example(), "compact") + b"\x00"
        self._ambiguous(self._diagnostic(message, "auto"))

    def test_a_truncated_cbor_datagram_reads_decode_ambiguous_on_auto(self):
        message = gateway._encode_message(self._first_example(), "cbor")[:-1]
        self._ambiguous(self._diagnostic(message, "auto"))
        self._invalid(self._diagnostic(message, "cbor"))

    def test_a_seven_member_event_cut_short_reads_schema_invalid_on_auto(self):
        event = self._example(3)
        self.assertEqual(7, len(event))
        message = gateway._encode_message(event, "compact")[:-1]
        self._invalid(self._diagnostic(message, "auto"))

    def test_a_brace_datagram_that_is_not_json_reads_schema_invalid_on_auto(self):
        for message in (b"{abc", json.dumps(self._first_example()).encode("utf-8")[:-1]):
            self._invalid(self._diagnostic(message, "auto"))
            self._invalid(self._diagnostic(message, "json"))

    def test_a_truncated_compact_datagram_reads_decode_ambiguous_on_auto(self):
        metrics = self._diagnostic(self._truncated_compact(), "auto")
        self.assertEqual("SCHEMA_INVALID", metrics["reason_code"])
        self.assertEqual("DECODE_AMBIGUOUS", metrics.get("diagnostic_code"))

    def test_the_same_datagram_reads_schema_invalid_on_the_compact_lane(self):
        metrics = self._diagnostic(self._truncated_compact(), "compact")
        self.assertEqual("SCHEMA_INVALID", metrics["reason_code"])
        self.assertNotIn("diagnostic_code", metrics)

    def test_plain_text_reads_decode_ambiguous_on_auto(self):
        metrics = self._diagnostic(b"hello world", "auto")
        self.assertEqual("DECODE_AMBIGUOUS", metrics.get("diagnostic_code"))


if __name__ == "__main__":
    unittest.main()
