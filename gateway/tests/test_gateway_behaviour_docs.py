"""The documents a deployer or consumer reads name three gateway behaviours.

From the pre-cut range review of 2026-11-14 (S5): the strip guard's protected
prefixes, the members of the admission record (contract 4.5.1), and the
DECODE_AMBIGUOUS refusal were stated only in the code, the tests and the
process records. Each check below reads the name from the code or the policy
where it can, so a later change to the behaviour fails here until the
document follows it.
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


def _admission_members():
    """The member names the reference writes into a record's effects."""
    event = {"confidence": 0.8, "payload": {"valid_for_ms": 1000}}
    claimed = sorted(validators._claimed_values(event))
    source = VALIDATORS_PATH.read_text(encoding="utf-8")
    # the declined-factor member is written by name on the promotion path
    if 'effects["reduction_declined"]' not in source:
        raise AssertionError("validators.py no longer writes effects['reduction_declined']")
    return claimed + ["reduction_declined"]


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


class GatewayReadmeDecodeRefusalTest(unittest.TestCase):
    def _section(self):
        return " ".join(_section(_text(GATEWAY_README), "Decode refusals").split())

    def test_the_section_names_the_code_and_what_it_refuses(self):
        section = self._section()
        self.assertIn("`DECODE_AMBIGUOUS`", section)
        self.assertIn("contract 3.5", section)
        self.assertIn("`lineage.based_on`", section)
        self.assertIn("wire type", section)

    def test_the_section_gives_the_v1_0_wire_form_from_policy(self):
        policy = validators.load_policy(ROOT / "policy")
        fallback = policy["semantics"]["system_event"]["schema_violation_v1_0_wire_fallback"]
        wire = fallback["DECODE_AMBIGUOUS"]
        section = self._section()
        self.assertIn(f"`{wire}`", section)
        self.assertIn("`metrics.diagnostic_code`", section)
        self.assertIn("`schema_violation_v1_0_wire_fallback`", section)

    def test_the_section_states_the_auto_lane_as_an_open_decision(self):
        section = self._section()
        self.assertIn("`auto` lane", section)
        self.assertIn("open pre-cut decision", section)


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

    def _truncated_compact(self):
        line = (ROOT / "examples" / "zmeta-examples-1.0.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()[0]
        event = json.loads(line)
        self.assertEqual(5, len(event), "the first example is a five-member event")
        return gateway._encode_message(event, "compact")[:-1]

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
