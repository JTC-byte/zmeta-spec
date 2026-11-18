"""The golden CoT outputs: the reference CoT XML for every example STATE event, as a conformance artifact.

On the maintainer's answer of 2026-11-10 ("Add the fixtures"), `conformance/cot-golden/golden.jsonl` holds, for each STATE_EVENT
the repository ships in `examples/`, what the reference CoT projection (`adapters/egress/cot/zmeta_to_cot.py`) gives under each of
its two profiles, `standard` and `cds`, at a fixed projection instant: the CoT XML it writes, or the reason it refuses.
`tools/validate_cot_golden.py` re-projects each case and compares the result byte for byte.

The first ten tests were written before the corpus and the tool existed and failed then. The controls show that each check can
fail: the comparison sees one changed byte and a changed refusal; the event comparison sees a number whose type changed; the
coverage check sees a missing case; the tool refuses a malformed case with a FAIL line.
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from zmeta_decode_guard import pairs_refusing_duplicates  # noqa: E402

GOLDEN = ROOT / "conformance" / "cot-golden" / "golden.jsonl"
TOOL = ROOT / "tools" / "validate_cot_golden.py"
PROFILES = ("standard", "cds")


def _read_jsonl(path):
    """Each line read as the gateway reads JSON: a repeated member name is refused (contract 3.5)."""
    return [json.loads(line, object_pairs_hook=pairs_refusing_duplicates)
            for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _cases(path=GOLDEN):
    return _read_jsonl(path)


def _example_state_events():
    found = {}
    for path in sorted((ROOT / "examples").glob("*.jsonl")):
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if line.strip() and '"STATE_EVENT"' in line:
                event = json.loads(line, object_pairs_hook=pairs_refusing_duplicates)
                if event.get("event", {}).get("event_type") == "STATE_EVENT":
                    found[f"examples/{path.name}:{line_no}"] = event
    return found


def _same_event(a, b):
    """Equal as JSON, number types included: 120 and 120.0 differ, as they do on the wire."""
    return json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def _coverage_gaps(cases, examples):
    """(source, profile) pairs with no case, and cases whose pair is not an example's."""
    have = [(case["source"], case["cot_config"].get("profile", "standard")) for case in cases]
    want = [(source, profile) for source in examples for profile in PROFILES]
    return sorted(set(want) - set(have)), sorted(set(have) - set(want)), len(have) - len(set(have))


def _run(path):
    return subprocess.run([sys.executable, str(TOOL), "--golden", str(path)], capture_output=True, text=True, cwd=str(ROOT))


def _run_lines(lines):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "golden.jsonl"
        path.write_text("".join(line + "\n" for line in lines), encoding="utf-8")
        return _run(path)


class GoldenCorpusTest(unittest.TestCase):
    def test_the_shipped_corpus_matches_the_reference_projection(self):
        proc = _run(GOLDEN)
        self.assertEqual(0, proc.returncode, proc.stdout[-800:])
        self.assertIn(f"cot golden ok total={len(_cases())}", proc.stdout)

    def test_every_example_state_event_has_a_case_under_both_profiles(self):
        examples = _example_state_events()
        self.assertGreater(len(examples), 0)
        self.assertEqual(([], [], 0), _coverage_gaps(_cases(), examples))

    def test_each_case_carries_its_example_event_unchanged(self):
        examples = _example_state_events()
        for case in _cases():
            with self.subTest(case=case["name"]):
                self.assertTrue(_same_event(examples[case["source"]], case["event"]))

    def test_each_case_states_one_expectation(self):
        for case in _cases():
            with self.subTest(case=case["name"]):
                self.assertEqual(1, len(case["expect"]))
                self.assertIn(next(iter(case["expect"])), ("cot_xml", "refusal"))
                self.assertTrue(case["now"].endswith("Z"))

    def test_the_corpus_is_read_through_the_refusing_reader(self):
        # contract 3.5: a case line that repeats a member name is refused, not read last-wins
        line = GOLDEN.read_text(encoding="utf-8").splitlines()[0]
        proc = _run_lines(['{"name": "wrong-name", ' + line.strip()[1:]])
        self.assertNotIn("Traceback", proc.stderr + proc.stdout)
        self.assertEqual(1, proc.returncode, proc.stdout[-400:])
        self.assertIn("FAIL line=1 DECODE_AMBIGUOUS", proc.stdout)


class GoldenControlTest(unittest.TestCase):
    """Each control changes one thing and must make the check it guards fail."""

    def _run_changed(self, change):
        cases = _cases()
        name = change(cases)
        return name, _run_lines([json.dumps(case, sort_keys=True) for case in cases])

    def test_one_changed_byte_in_an_expected_xml_fails_that_case(self):
        def change(cases):
            case = next(c for c in cases if "cot_xml" in c["expect"])
            xml = case["expect"]["cot_xml"]
            case["expect"]["cot_xml"] = xml.replace('version="2.0"', 'version="2.1"', 1)
            self.assertNotEqual(xml, case["expect"]["cot_xml"])
            return case["name"]

        name, proc = self._run_changed(change)
        self.assertEqual(1, proc.returncode)
        self.assertEqual([name], [l.split("name=")[1].split()[0] for l in proc.stdout.splitlines() if l.startswith("FAIL name=")])

    def test_a_changed_refusal_fails_that_case(self):
        def change(cases):
            case = next(c for c in cases if "refusal" in c["expect"])
            case["expect"]["refusal"] = "VALIDITY_LAPSED"
            return case["name"]

        name, proc = self._run_changed(change)
        self.assertEqual(1, proc.returncode)
        self.assertIn(f"FAIL name={name}", proc.stdout)

    def test_a_case_expecting_xml_where_the_projection_refuses_fails(self):
        def change(cases):
            case = next(c for c in cases if "refusal" in c["expect"])
            case["expect"] = {"cot_xml": "<event/>"}
            return case["name"]

        name, proc = self._run_changed(change)
        self.assertEqual(1, proc.returncode)
        self.assertIn(f"FAIL name={name}", proc.stdout)

    def test_an_empty_corpus_proves_nothing(self):
        proc = _run_lines([])
        self.assertEqual(1, proc.returncode)
        self.assertIn("contains no cases", proc.stdout)

    def test_the_event_comparison_sees_a_changed_number_type(self):
        event = next(iter(_example_state_events().values()))
        self.assertTrue(_same_event(event, json.loads(json.dumps(event))))
        reordered = dict(reversed(list(event.items())))
        self.assertTrue(_same_event(event, reordered))
        changed = json.loads(json.dumps(event))
        changed["payload"]["geo"]["alt_m"] = int(changed["payload"]["geo"]["alt_m"])
        self.assertIsInstance(event["payload"]["geo"]["alt_m"], float)
        self.assertEqual(event, changed)  # Python's == cannot see it
        self.assertFalse(_same_event(event, changed))

    def test_the_coverage_check_reports_a_missing_case(self):
        examples = _example_state_events()
        cases = _cases()
        missing, extra, repeated = _coverage_gaps(cases[:-1], examples)
        self.assertEqual([(cases[-1]["source"], cases[-1]["cot_config"].get("profile", "standard"))], missing)
        self.assertEqual(([], 0), (extra, repeated))
        self.assertEqual(1, _coverage_gaps(cases + cases[-1:], examples)[2])

    def test_a_malformed_case_is_a_fail_line_and_not_a_traceback(self):
        good = json.loads(GOLDEN.read_text(encoding="utf-8").splitlines()[0])
        variants = {
            "not json": "{not json",
            "not an object": "[1, 2]",
            "no now": json.dumps({k: v for k, v in good.items() if k != "now"}),
            "naive now": json.dumps({**good, "now": good["now"][:-1]}),
            "two expectations": json.dumps({**good, "expect": {"cot_xml": "<event/>", "refusal": "X"}}),
            "empty refusal": json.dumps({**good, "expect": {"refusal": None}}),
        }
        for label, line in variants.items():
            with self.subTest(case=label):
                proc = _run_lines([line])
                self.assertNotIn("Traceback", proc.stderr + proc.stdout)
                self.assertEqual(1, proc.returncode)
                self.assertIn("FAIL line=1", proc.stdout)


class ConformanceClassTest(unittest.TestCase):
    def test_the_cot_projection_class_names_the_corpus_and_its_tool(self):
        import yaml

        manifest = yaml.safe_load((ROOT / "conformance" / "conformance_classes.yaml").read_text(encoding="utf-8"))
        classes = {c["class_id"]: c for c in manifest["class_records"]}
        cot = classes["ZMETA-COT-PROJECTION"]
        self.assertIn("conformance/cot-golden/golden.jsonl", cot["required_conformance_fixtures"])
        self.assertIn("python tools/validate_cot_golden.py", cot["required_test_commands"])

    def test_the_release_manifest_builder_pins_the_corpus_and_its_tool(self):
        text = (ROOT / "tools" / "build_release_manifest.py").read_text(encoding="utf-8")
        self.assertIn('"conformance/cot-golden/golden.jsonl"', text)
        self.assertIn('"tools/validate_cot_golden.py"', text)


if __name__ == "__main__":
    unittest.main()
