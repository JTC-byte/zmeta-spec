"""The remaining reference readers of event and fixture JSON refuse a repeated member name.

Contract 3.5: a JSON text in which one object repeats a member name, at any
depth, is not a valid encoded event, and a decoder that keeps one of the
repeated values chooses a reading the text does not state. The gateway and
four tools refused such a text from 2026-11-10. On the maintainer's selection
of that day ("Yes, before the cut") the twelve readers that still kept the last
value move to the refusing reader (`zmeta_decode_guard.pairs_refusing_duplicates`):

- three tools that read events: `tools/compat_normalize.py`,
  `tools/filter_risk.py`, `tools/measure_packet_size.py`;
- five tools that read fixtures: `tools/check_adapter.py`,
  `tools/validate_adapter_conformance.py`, `tools/validate_encoding_negative.py`,
  `tools/validate_precision_policy.py`, `tools/validate_projection.py`;
- the gateway's self-test reader of its shipped example file (`_load_jsonl`);
- three development harnesses: `tools/sim/throughput.py`,
  `tools/sim/two_node.py`, `tools/test_workflow_end_to_end.py`.

Each repeat below writes a wrong value first and the shipped value last, so a
reader that keeps the last value reads the shipped text and accepts it: each
refusal test therefore fails on a last-wins reader. Each reader is tried with a
repeat at the top level and with one below it, and the same text without the
repeat is the control that the reader accepts. Written before the change; the
refusal tests were seen failing on the unchanged tree and the controls passed.
"""

import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SIM = ROOT / "tools" / "sim"


def _load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _first_line(relative):
    return next(line for line in (ROOT / relative).read_text(encoding="utf-8").splitlines() if line.strip())


def _repeat_top(line, key, wrong):
    """`line` with the top-level member `key` written twice: `wrong` first, the shipped value last."""
    shipped = json.loads(line)
    assert key in shipped and shipped[key] != wrong
    text = "{" + json.dumps(key) + ": " + json.dumps(wrong) + ", " + line.strip()[1:]
    assert json.loads(text) == shipped
    return text


def _repeat_nested(line):
    """`line` with the first member of its first non-empty nested object written twice, a wrong value first."""
    shipped = json.loads(line)
    for key, value in shipped.items():
        if isinstance(value, dict) and value:
            inner = next(iter(value))
            wrong = "wrong-value" if value[inner] != "wrong-value" else "other-wrong-value"
            nested = "{" + json.dumps(inner) + ": " + json.dumps(wrong) + ", " + json.dumps(value)[1:]
            parts = [json.dumps(k) + ": " + (nested if k == key else json.dumps(v)) for k, v in shipped.items()]
            text = "{" + ", ".join(parts) + "}"
            assert json.loads(text) == shipped
            return text
    raise AssertionError("the line has no nested object to repeat a member in")


def _event_line():
    # A shipped Profile L example that every event reader accepts as it stands.
    return _first_line("examples/zmeta-profile-L-examples.jsonl")


def _event_cases():
    line = _event_line()
    return {
        "top": _repeat_top(line, "zmeta_version", "9.9"),
        "nested": _repeat_nested(line),
        "clean": line,
    }


def _run_tool(relative, *argv):
    return subprocess.run(
        [sys.executable, str(ROOT / relative), *argv], capture_output=True, text=True, cwd=str(ROOT)
    )


class EventToolTest(unittest.TestCase):
    """The three tools that read events."""

    def test_compat_normalize_refuses_a_repeat_in_a_line_and_writes_no_output(self):
        cases = _event_cases()
        for where in ("top", "nested"):
            with self.subTest(where=where), tempfile.TemporaryDirectory() as tmp:
                source = Path(tmp) / "in.jsonl"
                source.write_text(cases["clean"] + "\n" + cases[where] + "\n", encoding="utf-8")
                proc = _run_tool(
                    "tools/compat_normalize.py", "--input", str(source),
                    "--output", str(Path(tmp) / "out.jsonl"), "--report", str(Path(tmp) / "report.json"),
                )
                self.assertNotIn("Traceback", proc.stderr)
                self.assertEqual(1, proc.returncode, proc.stderr[:400])
                report = json.loads((Path(tmp) / "report.json").read_text(encoding="utf-8"))
                self.assertEqual([2], [item["line"] for item in report["rejected"]])
                self.assertEqual(["DECODE_AMBIGUOUS"], [item["code"] for item in report["rejected"]])
                self.assertFalse((Path(tmp) / "out.jsonl").exists())

    def test_compat_normalize_refuses_a_whole_document_for_one_repeat(self):
        cases = _event_cases()
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "in.json"
            source.write_text("[\n" + cases["clean"] + ",\n" + cases["nested"] + "\n]\n", encoding="utf-8")
            proc = _run_tool(
                "tools/compat_normalize.py", "--input", str(source),
                "--output", str(Path(tmp) / "out.json"), "--report", str(Path(tmp) / "report.json"),
            )
            self.assertNotIn("Traceback", proc.stderr)
            self.assertEqual(1, proc.returncode, proc.stderr[:400])
            report = json.loads((Path(tmp) / "report.json").read_text(encoding="utf-8"))
            self.assertEqual([(1, "DECODE_AMBIGUOUS")], [(i["line"], i["code"]) for i in report["rejected"]])
            self.assertFalse((Path(tmp) / "out.json").exists())

    def test_filter_risk_refuses_a_repeat_with_its_line(self):
        cases = _event_cases()
        for where in ("top", "nested"):
            with self.subTest(where=where), tempfile.TemporaryDirectory() as tmp:
                source = Path(tmp) / "in.jsonl"
                source.write_text(cases["clean"] + "\n" + cases[where] + "\n", encoding="utf-8")
                proc = _run_tool(
                    "tools/filter_risk.py", "--input", str(source), "--output", str(Path(tmp) / "out.jsonl"),
                    "--preset", "display", "--quiet",
                )
                self.assertNotIn("Traceback", proc.stderr)
                self.assertEqual(1, proc.returncode, proc.stderr[:400])
                self.assertIn(":2: DECODE_AMBIGUOUS", proc.stderr)

    def test_measure_packet_size_refuses_a_repeat_with_its_line(self):
        cases = _event_cases()
        for where in ("top", "nested"):
            with self.subTest(where=where), tempfile.TemporaryDirectory() as tmp:
                source = Path(tmp) / "in.jsonl"
                source.write_text(cases["clean"] + "\n" + cases[where] + "\n", encoding="utf-8")
                proc = _run_tool("tools/measure_packet_size.py", "--file", str(source), "--summary-only")
                self.assertNotIn("Traceback", proc.stderr)
                self.assertNotEqual(0, proc.returncode)
                self.assertIn("line 2: DECODE_AMBIGUOUS", proc.stderr)

    def test_the_three_event_tools_accept_the_same_text_without_the_repeat(self):
        cases = _event_cases()
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "in.jsonl"
            source.write_text(cases["clean"] + "\n" + cases["clean"] + "\n", encoding="utf-8")
            proc = _run_tool(
                "tools/compat_normalize.py", "--input", str(source),
                "--output", str(Path(tmp) / "out.jsonl"), "--report", str(Path(tmp) / "report.json"),
            )
            self.assertEqual(0, proc.returncode, proc.stderr[:400])
            self.assertEqual(2, len((Path(tmp) / "out.jsonl").read_text(encoding="utf-8").splitlines()))
            proc = _run_tool(
                "tools/filter_risk.py", "--input", str(source), "--output", str(Path(tmp) / "f.jsonl"),
                "--preset", "display", "--quiet",
            )
            self.assertEqual(0, proc.returncode, proc.stderr[:400])
            proc = _run_tool("tools/measure_packet_size.py", "--file", str(source), "--summary-only")
            self.assertEqual(0, proc.returncode, proc.stderr[:400])

    def test_malformed_json_behaves_as_before_in_filter_risk(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "in.jsonl"
            source.write_text('{"zmeta_version": \n', encoding="utf-8")
            proc = _run_tool("tools/filter_risk.py", "--input", str(source), "--output", str(Path(tmp) / "o.jsonl"))
            self.assertEqual(1, proc.returncode)
            self.assertIn(":1: invalid JSON:", proc.stderr)


FIXTURE_TOOLS = {
    # tool: (shipped fixture file, argv builder for one replaced file)
    "tools/validate_adapter_conformance.py": (
        "conformance/adapter-harness/must-pass.jsonl",
        lambda path: ["--fixtures", str(path), "--quiet"],
    ),
    "tools/validate_encoding_negative.py": (
        "conformance/encoding-negative/compact-must-fail.jsonl",
        lambda path: [
            "--compact", str(path),
            "--protobuf", str(ROOT / "conformance" / "encoding-negative" / "protobuf-must-fail.jsonl"),
            "--gateway", str(ROOT / "conformance" / "encoding-negative" / "gateway-must-fail.jsonl"),
            "--context", str(ROOT / "conformance" / "encoding-negative" / "context.jsonl"),
            "--quiet",
        ],
    ),
    "tools/validate_precision_policy.py": (
        "conformance/profile-precision/must-pass.jsonl",
        lambda path: ["--must-pass", str(path), "--quiet"],
    ),
    "tools/validate_projection.py": (
        "conformance/profile-projection/must-pass.jsonl",
        lambda path: ["--must-pass", str(path), "--quiet"],
    ),
}


class FixtureToolTest(unittest.TestCase):
    """The four tools that run fixture files, and the fixture lint of the adapter ladder."""

    def _cases(self, shipped):
        # The first shipped line that holds a nested object, so the repeat can
        # be placed both at the top level and below it.
        line = next(
            line for line in (ROOT / shipped).read_text(encoding="utf-8").splitlines()
            if line.strip() and any(isinstance(v, dict) and v for v in json.loads(line).values())
        )
        first_key = next(iter(json.loads(line)))
        return {
            "top": _repeat_top(line, first_key, "wrong-value"),
            "nested": _repeat_nested(line),
            "clean": line,
        }

    def test_each_fixture_tool_refuses_a_fixture_line_that_repeats_a_member(self):
        for tool, (shipped, argv) in FIXTURE_TOOLS.items():
            cases = self._cases(shipped)
            for where in ("top", "nested"):
                with self.subTest(tool=tool, where=where), tempfile.TemporaryDirectory() as tmp:
                    path = Path(tmp) / "fixtures.jsonl"
                    path.write_text(cases[where] + "\n", encoding="utf-8")
                    proc = _run_tool(tool, *argv(path))
                    self.assertNotIn("Traceback", proc.stderr + proc.stdout)
                    self.assertEqual(1, proc.returncode, proc.stdout[-400:])
                    self.assertIn("FAIL DECODE_AMBIGUOUS", proc.stdout)
                    self.assertIn("line 1", proc.stdout)
                    self.assertNotIn("contains no fixtures", proc.stdout)

    def test_each_fixture_tool_accepts_the_same_line_without_the_repeat(self):
        for tool, (shipped, argv) in FIXTURE_TOOLS.items():
            with self.subTest(tool=tool), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "fixtures.jsonl"
                path.write_text(self._cases(shipped)["clean"] + "\n", encoding="utf-8")
                proc = _run_tool(tool, *argv(path))
                self.assertEqual(0, proc.returncode, proc.stdout[-400:])

    def test_the_in_process_run_reports_a_refused_fixture_file_cleanly(self):
        # tools/validate_conformance.py calls this run function in process; a
        # refusal is a FAIL line and a non-zero return there, not an exception.
        harness = _load("zmeta_vac_readers", "tools/validate_adapter_conformance.py")
        line = self._cases("conformance/adapter-harness/must-pass.jsonl")["nested"]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fixtures.jsonl"
            path.write_text(line + "\n", encoding="utf-8")
            out = io.StringIO()
            with redirect_stdout(out):
                result = harness.run(fixtures_path=path, quiet=True)
        self.assertEqual(1, result)
        self.assertIn("FAIL DECODE_AMBIGUOUS", out.getvalue())

    def test_the_context_file_of_the_encoding_negative_suite_is_refused_too(self):
        line = _first_line("conformance/encoding-negative/context.jsonl")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "context.jsonl"
            path.write_text(_repeat_top(line, next(iter(json.loads(line))), "wrong-value") + "\n", encoding="utf-8")
            argv = FIXTURE_TOOLS["tools/validate_encoding_negative.py"][1](
                ROOT / "conformance" / "encoding-negative" / "compact-must-fail.jsonl"
            )
            argv[argv.index("--context") + 1] = str(path)
            proc = _run_tool("tools/validate_encoding_negative.py", *argv)
        self.assertNotIn("Traceback", proc.stderr + proc.stdout)
        self.assertEqual(1, proc.returncode, proc.stdout[-400:])
        self.assertIn("FAIL DECODE_AMBIGUOUS", proc.stdout)

    def test_check_adapter_lint_reports_a_repeat_and_passes_the_clean_line(self):
        check_adapter = _load("zmeta_check_adapter_readers", "tools/check_adapter.py")
        cases = self._cases("conformance/adapter-harness/must-pass.jsonl")
        with tempfile.TemporaryDirectory() as tmp:
            for where in ("top", "nested"):
                with self.subTest(where=where):
                    path = Path(tmp) / f"{where}.jsonl"
                    path.write_text(cases[where] + "\n", encoding="utf-8")
                    errors = check_adapter.lint_fixtures(path)
                    self.assertEqual(1, len(errors), errors)
                    self.assertIn("line 1: DECODE_AMBIGUOUS", errors[0])
            clean = Path(tmp) / "clean.jsonl"
            clean.write_text(cases["clean"] + "\n", encoding="utf-8")
            self.assertEqual([], check_adapter.lint_fixtures(clean))


class GatewaySelfTestReaderTest(unittest.TestCase):
    """The gateway's self-test reads `examples/encoding-roundtrip.jsonl` through `_load_jsonl`."""

    @classmethod
    def setUpClass(cls):
        cls.gateway = _load("zmeta_gateway_readers", "gateway/src/gateway.py")

    def test_the_self_test_reader_refuses_a_repeat_and_names_the_file(self):
        cases = _event_cases()
        for where in ("top", "nested"):
            with self.subTest(where=where), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "encoding-roundtrip.jsonl"
                path.write_text(cases["clean"] + "\n" + cases[where] + "\n", encoding="utf-8")
                with self.assertRaises(SystemExit) as caught:
                    list(self.gateway._load_jsonl(path))
                self.assertIn("self-test failed", str(caught.exception))
                self.assertIn("DECODE_AMBIGUOUS", str(caught.exception))
                self.assertIn("encoding-roundtrip.jsonl", str(caught.exception))

    def test_the_self_test_reader_reads_the_shipped_file_and_a_clean_text(self):
        shipped = ROOT / "examples" / "encoding-roundtrip.jsonl"
        expected = [json.loads(line) for line in shipped.read_text(encoding="utf-8").splitlines() if line.strip()]
        self.assertEqual(expected, list(self.gateway._load_jsonl(shipped)))
        self.assertGreater(len(expected), 0)
        clean = _event_cases()["clean"]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "clean.jsonl"
            path.write_text(clean + "\n\n" + clean + "\n", encoding="utf-8")
            self.assertEqual([json.loads(clean)] * 2, list(self.gateway._load_jsonl(path)))

    def test_the_gateway_keeps_its_line_count(self):
        # The guidance file cites gateway.py by line in many places; a change
        # that adds or removes lines would have to move them in the same change.
        text = (ROOT / "gateway" / "src" / "gateway.py").read_text(encoding="utf-8")
        self.assertEqual(3389, text.count("\n"))


# As in test_sim_boundary.py: a release bundle (VERSION.txt at its root) leaves
# tools/sim out by design; in a repository checkout a missing tools/sim fails.
@unittest.skipIf(not SIM.is_dir() and (ROOT / "VERSION.txt").is_file(),
                 "tools/sim is curated out of release bundles by design")
class SimHarnessTest(unittest.TestCase):
    """The two harnesses under tools/sim."""

    def _main(self, module, corpus):
        out = io.StringIO()
        argv = sys.argv
        sys.argv = [module.__name__, "--corpus", str(corpus)]
        try:
            with redirect_stdout(out):
                result = module.main()
        finally:
            sys.argv = argv
        return result, out.getvalue()

    def test_throughput_refuses_a_corpus_line_that_repeats_a_member(self):
        from zmeta_decode_guard import DecodeAmbiguousError

        throughput = _load("zmeta_sim_throughput_readers", "tools/sim/throughput.py")
        cases = _event_cases()
        for where in ("top", "nested"):
            with self.subTest(where=where), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "corpus.jsonl"
                path.write_text(cases[where] + "\n", encoding="utf-8")
                with self.assertRaises(DecodeAmbiguousError) as caught:
                    throughput.pick_template(path)
                self.assertIn("line 1", str(caught.exception))
                # main() reports it as invalid input before any gateway starts
                result, printed = self._main(throughput, path)
                self.assertEqual(throughput.EXIT_INVALID, result)
                self.assertIn("VERDICT: INVALID - DECODE_AMBIGUOUS", printed)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "corpus.jsonl"
            path.write_text(cases["clean"] + "\n", encoding="utf-8")
            self.assertEqual(json.loads(cases["clean"]), throughput.pick_template(path))

    def test_two_node_refuses_a_corpus_line_before_it_is_sent(self):
        import socket

        from zmeta_decode_guard import DecodeAmbiguousError

        two_node = _load("zmeta_sim_two_node_readers", "tools/sim/two_node.py")
        cases = _event_cases()
        listener = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        listener.bind(("127.0.0.1", 0))
        listener.settimeout(0.5)
        port = listener.getsockname()[1]
        try:
            for where in ("top", "nested"):
                with self.subTest(where=where), tempfile.TemporaryDirectory() as tmp:
                    path = Path(tmp) / "corpus.jsonl"
                    path.write_text(cases[where] + "\n", encoding="utf-8")
                    with self.assertRaises(DecodeAmbiguousError) as caught:
                        two_node.replay(path, "127.0.0.1", port, 0)
                    self.assertIn("line 1", str(caught.exception))
                    with self.assertRaises(socket.timeout):
                        listener.recvfrom(65535)  # nothing was sent
                    # main() reports it as invalid input before any node starts
                    result, printed = self._main(two_node, path)
                    self.assertEqual(two_node.EXIT_INVALID, result)
                    self.assertIn("VERDICT: INVALID - DECODE_AMBIGUOUS", printed)
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "corpus.jsonl"
                path.write_text(cases["clean"] + "\n", encoding="utf-8")
                self.assertEqual(1, len(two_node.replay(path, "127.0.0.1", port, 0)))
                self.assertEqual(cases["clean"].encode("utf-8"), listener.recvfrom(65535)[0])
        finally:
            listener.close()

    def test_two_node_sink_counts_a_received_repeat_and_does_not_read_it(self):
        two_node = _load("zmeta_sim_two_node_sink_readers", "tools/sim/two_node.py")
        cases = _event_cases()
        sink = two_node.Sink("forward", 9)
        sink.datagrams = [cases["clean"].encode("utf-8"), cases["nested"].encode("utf-8"), b"not json"]
        self.assertEqual([json.loads(cases["clean"])], sink.events())
        self.assertEqual(1, sink.ambiguous)


class WorkflowHarnessTest(unittest.TestCase):
    """`tools/test_workflow_end_to_end.py` reads each datagram the gateway forwards."""

    def test_a_forwarded_datagram_that_repeats_a_member_is_refused(self):
        harness = _load("zmeta_workflow_readers", "tools/test_workflow_end_to_end.py")
        cases = _event_cases()
        for where in ("top", "nested"):
            with self.subTest(where=where):
                with self.assertRaises(SystemExit) as caught:
                    harness._parse_forwarded(cases[where].encode("utf-8"))
                self.assertIn("DECODE_AMBIGUOUS", str(caught.exception))
        self.assertEqual(json.loads(cases["clean"]), harness._parse_forwarded(cases["clean"].encode("utf-8")))


if __name__ == "__main__":
    unittest.main()
