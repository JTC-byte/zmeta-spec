"""The strict command posture as two policy variants, and the tool that assembles them.

configs/policy-variants/command-evidence.strict.yaml turns the evidence
requirement on for every COMMAND_EVENT and refuses unresolvable citations.
configs/policy-variants/routing.command-origin.yaml restricts the automation
producers (retasking-engine, comms-deconfliction-*) to the closed set of
non-movement commands, SCAN_RF and CHANGE_SENSOR_MODE, while the human-origin
producer, sensorops, keeps every task type. tools/assemble_policy_dir.py builds a
deployment policy directory from the reference policy plus the variants.

The shape tests pin each variant to the reference so that a later change to the
reference cannot leave a variant silently stale, and pin the closed set against
the schema lanes so that a new command subtype cannot slip into the automation
lists unnoticed. The behaviour tests run the assembled pack through the gateway's
own pipeline, each against the reference policy as the control.
"""

import copy
import hashlib
import shutil
import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import yaml

from zmeta_uuid import uuid7


ROOT = Path(__file__).resolve().parents[2]
VARIANTS = ROOT / "configs" / "policy-variants"
STRICT_EVIDENCE = VARIANTS / "command-evidence.strict.yaml"
COMMAND_ORIGIN = VARIANTS / "routing.command-origin.yaml"
SCHEMA_DIR = ROOT / "schema"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validators = _load("zmeta_validators", ROOT / "gateway" / "src" / "validators.py")
gateway = _load("zmeta_gateway", ROOT / "gateway" / "src" / "gateway.py")
assembler = _load("assemble_policy_dir", ROOT / "tools" / "assemble_policy_dir.py")

CLOSED_SET = {"SCAN_RF", "CHANGE_SENSOR_MODE"}
HUMAN_ORIGIN = {"sensorops"}
AUTOMATION_PRODUCERS = ("retasking-engine", "comms-deconfliction-*")

TIMING_QUALITY = {
    "time_source": "GPS_PPS",
    "sync_state": "LOCKED",
    "est_error_ms": 1,
    "last_sync_ts": "2025-01-17T14:31:50Z",
}


def yaml_file(path):
    with open(path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def subtypes_by_event_type(schema_path):
    """event_type -> set of event_subtype values, read from a schema lane's if/then arms."""
    with open(schema_path, "r", encoding="utf-8") as handle:
        schema = json.load(handle)
    found = {}

    def walk(node):
        if isinstance(node, dict):
            condition, consequence = node.get("if"), node.get("then")
            if isinstance(condition, dict) and isinstance(consequence, dict):
                try:
                    event_type = condition["properties"]["event"]["properties"]["event_type"]["const"]
                    subtypes = consequence["properties"]["event"]["properties"]["event_subtype"]["enum"]
                except (KeyError, TypeError):
                    pass
                else:
                    found.setdefault(event_type, set()).update(subtypes)
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(schema)
    return found


# Every versioned lane file; the dispatcher (zmeta-event.schema.json) only
# routes between them. A lane added later is read without editing this list.
LANES = tuple(sorted(SCHEMA_DIR.glob("zmeta-event-*.schema.json")))


def lane_union(event_type):
    union = set()
    for lane in LANES:
        union |= subtypes_by_event_type(lane).get(event_type, set())
    return union


def source(producer):
    return {"platform_id": "gateway-01", "node_role": "GATEWAY", "producer": producer}


def track_state():
    return {
        "zmeta_version": "1.0",
        "event": {
            "event_id": str(uuid7()),
            "event_type": "STATE_EVENT",
            "event_subtype": "TRACK_STATE",
            "ts": "2025-01-17T14:30:02Z",
        },
        "source": source("torch"),
        "profile": "H",
        "payload": {
            "track_id": "track-1",
            "geo": {"lat": 34.0, "lon": -118.0, "alt_m": 100.0},
            "valid_for_ms": 60000,
        },
        "confidence": 0.7,
        "lineage": {"based_on": [str(uuid7())]},
    }


TASK_FIELDS = {
    "GOTO": {"target_geo": {"lat": 34.0101, "lon": -118.0101}},
    "SCAN_RF": {
        "sensor_id": "rf-01",
        "freq_range_hz": {"min": 24000000, "max": 1766000000},
        "dwell_ms": 1000,
    },
    "CHANGE_SENSOR_MODE": {"sensor_id": "rf-01", "sensor_mode": "DF"},
}


def command(task_type, producer, parents=None, version="1.1.0"):
    payload = {
        "task_id": f"task-{uuid7()}",
        "task_type": task_type,
        "valid_for_ms": 600000,
        "requires_deconfliction": True,
        "timing_quality": dict(TIMING_QUALITY),
    }
    payload.update(copy.deepcopy(TASK_FIELDS[task_type]))
    event = {
        "zmeta_version": version,
        "event": {
            "event_id": str(uuid7()),
            "event_type": "COMMAND_EVENT",
            "event_subtype": task_type,
            "ts": "2025-01-17T14:32:10Z",
        },
        "source": source(producer),
        "profile": "H",
        "payload": payload,
    }
    if parents is not None:
        event["lineage"] = {"based_on": list(parents)}
    return event


def time_status(producer="sensorops"):
    return {
        "zmeta_version": "1.0",
        "event": {
            "event_id": str(uuid7()),
            "event_type": "SYSTEM_EVENT",
            "event_subtype": "TIME_STATUS",
            "ts": "2025-01-17T14:31:50Z",
        },
        "source": source(producer),
        "profile": "H",
        "payload": {
            "system_type": "TIME_STATUS",
            "state": "LOCKED",
            "metrics": dict(TIMING_QUALITY),
        },
    }


def shipped_example(task_type):
    path = ROOT / "examples" / "zmeta-v1.1-examples.jsonl"
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            event = json.loads(line)
            if event["event"]["event_subtype"] == task_type:
                return event
    raise AssertionError(f"no shipped 1.1.0 example for {task_type}")


def refusal_codes(outputs):
    """Reason codes the gateway emitted for a refusal.

    A refused event comes back as a SCHEMA_VIOLATION diagnostic, or, when the
    refused event is a task-correlated command, as a TASK_ACK in state REJECTED.
    """
    codes = set()
    for out in outputs:
        subtype = out.get("event", {}).get("event_subtype")
        payload = out.get("payload", {})
        if subtype == "SCHEMA_VIOLATION" or (
            subtype == "TASK_ACK" and payload.get("state") == "REJECTED"
        ):
            metrics = payload.get("metrics", {})
            codes.update(
                code for code in (metrics.get("reason_code"), metrics.get("diagnostic_code")) if code
            )
    return codes


class VariantShapeTest(unittest.TestCase):
    def test_strict_evidence_variant_changes_exactly_two_values(self):
        reference = yaml_file(ROOT / "policy" / "command-evidence.yaml")
        variant = yaml_file(STRICT_EVIDENCE)
        self.assertIsNot(True, reference["command_evidence"]["require_evidence"])
        expected = copy.deepcopy(reference)
        expected["command_evidence"]["require_evidence"] = True
        expected["command_evidence"]["unresolved_parent_mode"] = "reject"
        self.assertEqual(expected, variant)
        self.assertEqual([], variant["command_evidence"]["require_evidence_task_types"])
        self.assertEqual("reject", variant["command_evidence"]["require_evidence_mode"])

    def test_routing_variant_changes_only_the_automation_subtype_lists(self):
        reference = yaml_file(ROOT / "policy" / "routing.yaml")
        variant = yaml_file(COMMAND_ORIGIN)
        stripped = copy.deepcopy(variant)
        for producer in AUTOMATION_PRODUCERS:
            self.assertIn("allowed_event_subtypes", stripped["routing"]["producers"][producer])
            del stripped["routing"]["producers"][producer]["allowed_event_subtypes"]
        self.assertEqual(reference, stripped)

    def test_both_lanes_are_read(self):
        names = {lane.name for lane in LANES}
        self.assertIn("zmeta-event-1.0.schema.json", names)
        self.assertIn("zmeta-event-1.1.0.schema.json", names)
        self.assertNotIn("zmeta-event.schema.json", names)

    def test_closed_set_is_exactly_the_two_non_movement_commands(self):
        command_subtypes = lane_union("COMMAND_EVENT")
        # Anti-vacuity: the lanes were read, and both members exist on one.
        self.assertTrue(CLOSED_SET <= command_subtypes, command_subtypes)
        self.assertIn("GOTO", command_subtypes)
        producers = yaml_file(COMMAND_ORIGIN)["routing"]["producers"]
        for producer in AUTOMATION_PRODUCERS:
            allowed = set(producers[producer]["allowed_event_subtypes"])
            self.assertEqual(CLOSED_SET, allowed & command_subtypes, producer)

    def test_automation_lists_carry_every_system_subtype_and_nothing_else(self):
        system_subtypes = lane_union("SYSTEM_EVENT")
        command_subtypes = lane_union("COMMAND_EVENT")
        self.assertIn("TASK_ACK", system_subtypes)
        producers = yaml_file(COMMAND_ORIGIN)["routing"]["producers"]
        for producer in AUTOMATION_PRODUCERS:
            allowed = set(producers[producer]["allowed_event_subtypes"])
            self.assertTrue(system_subtypes <= allowed, (producer, system_subtypes - allowed))
            # The subtype vocabulary is not linted for typos (doctrine R1-11-11),
            # so a misspelled entry would pass the policy lint. Pin it here.
            self.assertEqual(set(), allowed - system_subtypes - command_subtypes, producer)
            self.assertEqual(
                {"COMMAND_EVENT", "SYSTEM_EVENT"},
                set(producers[producer]["allowed_event_types"]),
                producer,
            )

    def test_every_command_origin_other_than_the_human_one_is_restricted(self):
        routing = yaml_file(COMMAND_ORIGIN)["routing"]
        origins = set(routing["command_event"]["allowed_producers"])
        self.assertTrue(HUMAN_ORIGIN <= origins)
        self.assertEqual(set(AUTOMATION_PRODUCERS), origins - HUMAN_ORIGIN)
        self.assertNotIn("allowed_event_subtypes", routing["producers"]["sensorops"])

    def test_assembled_pack_passes_the_policy_lints(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = assembler.assemble(
                Path(tmp) / "pack", [str(STRICT_EVIDENCE), str(COMMAND_ORIGIN)]
            )
        self.assertEqual([], result["lint_issues"])
        self.assertEqual(
            {"command-evidence.yaml", "routing.yaml"}, set(result["replaced"])
        )


class VariantBehaviourTest(unittest.TestCase):
    """The pack through the gateway pipeline, the reference policy as control."""

    @classmethod
    def setUpClass(cls):
        cls.validator = validators.load_schema(SCHEMA_DIR / "zmeta-event.schema.json")
        cls.reference = validators.load_policy(ROOT / "policy")
        cls._tmp = tempfile.TemporaryDirectory()
        pack_dir = Path(cls._tmp.name) / "pack"
        assembler.assemble(pack_dir, [str(STRICT_EVIDENCE), str(COMMAND_ORIGIN)])
        cls.pack = validators.load_policy(pack_dir)

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def run_pipeline(self, event, policy, *parents):
        self.assertEqual([], list(self.validator.iter_errors(event)), "input must be schema-valid")
        state = validators.ValidationState()
        for parent in parents:
            state.record(parent)
        state.record(time_status())
        return gateway.process_message(
            json.dumps(event).encode("utf-8"),
            self.validator,
            policy,
            "H",
            gateway.TaskDedupeCache(),
            "json",
            timing_state=state,
        )

    def assert_forwarded(self, event, policy, *parents):
        out = self.run_pipeline(event, policy, *parents)
        self.assertEqual([event], out)

    def assert_refused(self, event, policy, code, *parents):
        out = self.run_pipeline(event, policy, *parents)
        self.assertNotIn(event, out)
        self.assertIn(code, refusal_codes(out), out)

    def test_bare_operator_command_is_refused_under_the_pack_only(self):
        cmd = command("GOTO", "sensorops")
        self.assert_forwarded(cmd, self.reference)
        self.assert_refused(cmd, self.pack, "LINEAGE_MISMATCH")

    def test_operator_command_citing_its_track_is_forwarded(self):
        parent = track_state()
        cmd = command("GOTO", "sensorops", [parent["event"]["event_id"]])
        self.assert_forwarded(cmd, self.pack, parent)

    def test_automation_may_originate_the_closed_set_with_evidence(self):
        parent = track_state()
        for task_type in sorted(CLOSED_SET):
            with self.subTest(task_type=task_type):
                cmd = command(task_type, "retasking-engine", [parent["event"]["event_id"]])
                self.assert_forwarded(cmd, self.pack, parent)
                deconfliction = command(
                    task_type, "comms-deconfliction-01", [parent["event"]["event_id"]]
                )
                self.assert_forwarded(deconfliction, self.pack, parent)

    def test_automation_closed_set_still_needs_evidence(self):
        cmd = command("SCAN_RF", "retasking-engine")
        self.assert_forwarded(cmd, self.reference)
        self.assert_refused(cmd, self.pack, "LINEAGE_MISMATCH")

    def test_v1_0_lane_follows_the_same_posture(self):
        parent = track_state()
        cited = [parent["event"]["event_id"]]
        for producer in ("sensorops", "retasking-engine", "comms-deconfliction-01"):
            with self.subTest(producer=producer, cited=False):
                bare = command("GOTO", producer, version="1.0")
                self.assert_forwarded(bare, self.reference)
                self.assert_refused(bare, self.pack, "LINEAGE_MISMATCH")
        self.assert_forwarded(command("GOTO", "sensorops", cited, version="1.0"), self.pack, parent)
        for producer in ("retasking-engine", "comms-deconfliction-01"):
            with self.subTest(producer=producer, cited=True):
                movement = command("GOTO", producer, cited, version="1.0")
                self.assert_forwarded(movement, self.reference, parent)
                self.assert_refused(movement, self.pack, "EVENT_TYPE_NOT_ALLOWED_FOR_ROLE", parent)

    def test_automation_movement_command_is_refused_with_evidence_cited(self):
        parent = track_state()
        cmd = command("GOTO", "retasking-engine", [parent["event"]["event_id"]])
        self.assert_forwarded(cmd, self.reference, parent)
        self.assert_refused(cmd, self.pack, "EVENT_TYPE_NOT_ALLOWED_FOR_ROLE", parent)

    def test_shipped_automation_movement_examples_are_refused(self):
        parent = track_state()
        for task_type in ("ORBIT", "RETURN_TO_BASE"):
            with self.subTest(task_type=task_type):
                example = shipped_example(task_type)
                self.assertEqual("retasking-engine", example["source"]["producer"])
                cited = copy.deepcopy(example)
                cited["lineage"] = {"based_on": [parent["event"]["event_id"]]}
                self.assert_forwarded(cited, self.reference, parent)
                self.assert_refused(cited, self.pack, "EVENT_TYPE_NOT_ALLOWED_FOR_ROLE", parent)

    def test_automation_status_traffic_still_flows(self):
        status = time_status("retasking-engine")
        self.assert_forwarded(status, self.pack)

    def test_unresolvable_citation_is_refused_not_warned(self):
        cmd = command("GOTO", "sensorops", [str(uuid7())])
        out = self.run_pipeline(cmd, self.reference)
        self.assertIn(cmd, out, "the reference forwards with a warning")
        self.assert_refused(cmd, self.pack, "COMMAND_EVIDENCE_UNRESOLVED")


def _digest(directory):
    hasher = hashlib.sha256()
    for path in sorted(Path(directory).iterdir()):
        hasher.update(path.name.encode("utf-8"))
        hasher.update(path.read_bytes())
    return hasher.hexdigest()


class AssembleToolTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def names(self):
        return sorted(p.name for p in (ROOT / "policy").iterdir() if p.is_file())

    def test_target_is_the_longest_reference_prefix(self):
        names = self.names()
        cases = {
            "command-evidence.strict.yaml": "command-evidence.yaml",
            "routing.command-origin.yaml": "routing.yaml",
            "producer-authority.strict.yaml": "producer-authority.yaml",
            "timing-freshness-profile-L-degrade.yaml": "timing-freshness.yaml",
        }
        for variant, target in cases.items():
            with self.subTest(variant=variant):
                _source, resolved = assembler.resolve_target(str(VARIANTS / variant), names)
                self.assertEqual(target, resolved)

    def test_nested_names_resolve_to_the_longest_prefix(self):
        # No two reference file names nest today, so the rule is pinned on a
        # synthetic directory listing rather than left untested.
        names = ["timing.yaml", "timing-freshness.yaml", "README.md"]
        _source, target = assembler.resolve_target("timing-freshness.strict.yaml", names)
        self.assertEqual("timing-freshness.yaml", target)
        _source, target = assembler.resolve_target("timing.relaxed.yaml", names)
        self.assertEqual("timing.yaml", target)

    def test_explicit_target_must_be_a_reference_policy_yaml(self):
        names = self.names()
        _source, target = assembler.resolve_target(f"{STRICT_EVIDENCE}=command-evidence.yaml", names)
        self.assertEqual("command-evidence.yaml", target)
        for target in ("not-a-policy.yaml", "README.md"):
            with self.subTest(target=target):
                with self.assertRaisesRegex(assembler.AssemblyError, "not a policy YAML file"):
                    assembler.resolve_target(f"{STRICT_EVIDENCE}={target}", names)
        source, target = assembler.resolve_target("dir=x/v.yaml=routing.yaml", names)
        self.assertEqual(("dir=x/v.yaml", "routing.yaml"), (source.as_posix(), target))

    def test_a_prefix_must_end_at_a_separator(self):
        names = self.names()
        for variant in ("routingX.yaml", "routing2.yaml", "rolesy.yaml"):
            with self.subTest(variant=variant):
                with self.assertRaisesRegex(assembler.AssemblyError, "no reference policy file"):
                    assembler.resolve_target(variant, names)
        self.assertEqual("routing.yaml", assembler.resolve_target("routing.yaml", names)[1])
        self.assertEqual("routing.yaml", assembler.resolve_target("routing-x.yaml", names)[1])

    def test_refusals(self):
        unmatched = self.tmp / "nothing-like-a-policy.yaml"
        unmatched.write_text("x: 1\n", encoding="utf-8")
        with self.assertRaisesRegex(assembler.AssemblyError, "no reference policy file"):
            assembler.assemble(self.tmp / "a", [str(unmatched)])
        with self.assertRaisesRegex(assembler.AssemblyError, "both replace"):
            assembler.assemble(
                self.tmp / "b",
                [str(STRICT_EVIDENCE), f"{COMMAND_ORIGIN}=command-evidence.yaml"],
            )
        occupied = self.tmp / "occupied"
        occupied.mkdir()
        (occupied / "keep.txt").write_text("x", encoding="utf-8")
        with self.assertRaisesRegex(assembler.AssemblyError, "already holds files"):
            assembler.assemble(occupied, [str(STRICT_EVIDENCE)])
        a_file = self.tmp / "a-file"
        a_file.write_text("x", encoding="utf-8")
        with self.assertRaisesRegex(assembler.AssemblyError, "not a directory"):
            assembler.assemble(a_file, [str(STRICT_EVIDENCE)])

    def test_an_output_inside_the_reference_directory_is_refused(self):
        # A copy of the reference stands in for it, so the guard is exercised
        # without touching policy/. The sub-directories do not exist yet, so
        # only the containment guard can refuse them.
        reference = self.tmp / "reference"
        shutil.copytree(ROOT / "policy", reference)
        before = _digest(reference)
        for out in (reference, reference / "pack", reference / "a" / "b"):
            with self.subTest(out=out.name):
                with self.assertRaisesRegex(assembler.AssemblyError, "inside it"):
                    assembler.assemble(out, [str(STRICT_EVIDENCE)], policy_dir=reference)
        self.assertEqual(before, _digest(reference))
        self.assertEqual(
            sorted(p.name for p in (ROOT / "policy").iterdir()),
            sorted(p.name for p in reference.iterdir()),
        )

    def test_reference_policy_untouched_and_output_complete(self):
        before = _digest(ROOT / "policy")
        out = self.tmp / "pack"
        assembler.assemble(out, [str(STRICT_EVIDENCE), str(COMMAND_ORIGIN)])
        self.assertEqual(before, _digest(ROOT / "policy"))
        self.assertEqual(self.names(), sorted(p.name for p in out.iterdir()))
        self.assertEqual(
            STRICT_EVIDENCE.read_bytes(), (out / "command-evidence.yaml").read_bytes()
        )
        self.assertEqual(
            (ROOT / "policy" / "lineage.yaml").read_bytes(), (out / "lineage.yaml").read_bytes()
        )

    def test_main_prints_a_policy_hash_distinct_from_the_reference(self):
        out = self.tmp / "pack"
        buffer = io.StringIO()
        with redirect_stdout(buffer), redirect_stderr(io.StringIO()):
            code = assembler.main(
                ["--out", str(out), str(STRICT_EVIDENCE), str(COMMAND_ORIGIN)]
            )
        self.assertEqual(0, code)
        text = buffer.getvalue()
        printed = json.loads(text[text.index("{"): text.rindex("}") + 1])
        reference = gateway.compute_contract_hash(
            SCHEMA_DIR / "zmeta-event-1.0.schema.json",
            ROOT / "policy",
            ROOT / "spec" / "semantics-contract.md",
        )
        self.assertNotEqual(reference["policy_hash"], printed["policy_hash"])
        self.assertEqual(reference["schema_hash"], printed["schema_hash"])
        rerun = io.StringIO()
        with redirect_stdout(io.StringIO()), redirect_stderr(rerun):
            self.assertEqual(2, assembler.main(["--out", str(out), str(STRICT_EVIDENCE)]))
        self.assertIn("already holds files", rerun.getvalue())


if __name__ == "__main__":
    unittest.main()
