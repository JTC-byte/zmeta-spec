"""Adapter vocabulary mirrors must stay subsets of the governed enums.

Doctrine review log R1-11-16: adapter-declared vocabularies mirror governed
schema enums by hand, because a template copied into a bridge with no ZMeta
repo alongside it cannot load the schema at runtime. Drift is fail-closed in
one direction (the adapter over-refuses a code the kernel allows) but
fail-open in the other: a mirror that grows a token the kernel never granted
lets the adapter emit it looking legal. The 2026-07-27 adjudication holds
such mirrors to the subset rule, and tools/lint_adapter_vocabularies.py is
the repo-side gate for it.

These tests run the lint green on the shipped tree and prove non-vacuity by
feeding the check a deliberate superset in-memory and asserting the exact
named value-by-value diff.
"""

import contextlib
import importlib.util
import io
import json
import os
import shutil
import unittest
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LINT_PATH = ROOT / "tools" / "lint_adapter_vocabularies.py"
spec = importlib.util.spec_from_file_location(
    "zmeta_lint_adapter_vocabularies", LINT_PATH
)
lint = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lint)

MAVLINK_ADAPTER = "adapters/ingress/mavlink/mavlink_to_zmeta_template.py"
LINK_STATE_POINTER = (
    "$defs/SystemPayload/allOf[system_type=LINK_STATUS]/then/properties/state/enum"
)


class ShippedTreeLintTest(unittest.TestCase):
    """The lint must pass on the current tree: the mavlink mirrors were
    aligned to the governed enums this cycle, so a FAIL here is either a
    real subset violation or lint breakage - both stop the wave."""

    def test_shipped_mirrors_lint_clean(self):
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            rc = lint.run()

        self.assertEqual(0, rc, stdout.getvalue())
        self.assertIn("adapter vocabulary lint ok", stdout.getvalue())
        self.assertNotIn("FAIL", stdout.getvalue())

    def test_registry_covers_the_mavlink_mirrors(self):
        # The registry is the coverage contract: dropping an entry would
        # silently reopen the fail-open direction for that mirror.
        covered = {(adapter, constant) for adapter, constant, _ in lint.MIRROR_REGISTRY}

        for constant in (
            "_LINK_STATUS_STATES",
            "_LINK_STATUS_REASON_CODES",
            "_TASK_ACK_STATES",
            "_TASK_ACK_REASON_CODES",
        ):
            self.assertIn((MAVLINK_ADAPTER, constant), covered)

    def test_lint_checks_every_governed_schema(self):
        self.assertIn("schema/zmeta-event-1.0.schema.json", lint.GOVERNED_SCHEMA_FILES)
        self.assertIn(
            "schema/zmeta-event-1.1.0.schema.json", lint.GOVERNED_SCHEMA_FILES
        )


class MirrorExtractionTest(unittest.TestCase):
    def test_extraction_reads_the_adapter_source(self):
        # DUPLICATE_IGNORED is the token whose absence was the R1-11 drift;
        # its presence pins that extraction reads the aligned source, not a
        # stale copy.
        states = lint.load_mirror_constant(ROOT / MAVLINK_ADAPTER, "_TASK_ACK_STATES")

        self.assertIn("DUPLICATE_IGNORED", states)
        self.assertTrue(all(isinstance(value, str) for value in states))

    def test_unknown_constant_is_loud(self):
        with self.assertRaises(lint.LintError) as ctx:
            lint.load_mirror_constant(ROOT / MAVLINK_ADAPTER, "_NO_SUCH_MIRROR")

        self.assertIn("_NO_SUCH_MIRROR", str(ctx.exception))


class EnumPointerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema_1_0 = json.loads(
            (ROOT / "schema" / "zmeta-event-1.0.schema.json").read_text(
                encoding="utf-8"
            )
        )

    def test_branch_selector_resolves_the_governed_enum(self):
        resolved = lint.resolve_enum_pointer(self.schema_1_0, LINK_STATE_POINTER)

        self.assertEqual(["UP", "DEGRADED", "DOWN", "UNKNOWN"], resolved)

    def test_unresolvable_branch_selector_is_loud(self):
        # A pointer that stops resolving means the registry drifted from the
        # schema; that must never read as a pass.
        pointer = (
            "$defs/SystemPayload/allOf[system_type=NO_SUCH_TYPE]"
            "/then/properties/state/enum"
        )

        with self.assertRaises(lint.LintError) as ctx:
            lint.resolve_enum_pointer(self.schema_1_0, pointer)

        self.assertIn("NO_SUCH_TYPE", str(ctx.exception))


class SupersetMirrorTest(unittest.TestCase):
    """Non-vacuity: a deliberately-superset mirror must produce the exact
    named value-by-value diff, and a subset-with-missing-members must not.
    The check enforces the fail-open direction only - the adapter may refuse
    more than the kernel, never pass more."""

    @classmethod
    def setUpClass(cls):
        schema = json.loads(
            (ROOT / "schema" / "zmeta-event-1.0.schema.json").read_text(
                encoding="utf-8"
            )
        )
        cls.enum_values = lint.resolve_enum_pointer(schema, LINK_STATE_POINTER)

    def check(self, mirror_values):
        return lint.check_mirror_subset(
            adapter=MAVLINK_ADAPTER,
            constant="_LINK_STATUS_STATES",
            mirror_values=mirror_values,
            enum_values=self.enum_values,
            schema="schema/zmeta-event-1.0.schema.json",
            pointer=LINK_STATE_POINTER,
        )

    def test_superset_mirror_yields_named_value_diff(self):
        issues = self.check(("UP", "DEGRADED", "DOWN", "UNKNOWN", "FLAPPING"))

        self.assertEqual(1, len(issues))
        self.assertEqual("ADAPTER_VOCABULARY_NOT_SUBSET", issues[0]["code"])
        self.assertEqual("FLAPPING", issues[0]["value"])
        self.assertEqual("_LINK_STATUS_STATES", issues[0]["constant"])
        self.assertEqual(MAVLINK_ADAPTER, issues[0]["adapter"])
        self.assertEqual("schema/zmeta-event-1.0.schema.json", issues[0]["schema"])
        self.assertEqual(LINK_STATE_POINTER, issues[0]["pointer"])

    def test_diff_is_value_by_value_in_mirror_order(self):
        issues = self.check(("UP", "FLAPPING", "DOWN", "SEVERED"))

        self.assertEqual(
            ["FLAPPING", "SEVERED"], [issue["value"] for issue in issues]
        )

    def test_missing_member_is_not_a_violation(self):
        self.assertEqual([], self.check(("UP", "DOWN")))


class LintRunFailurePathTest(unittest.TestCase):
    """End-to-end: a registry entry whose on-disk mirror is a superset must
    drive run() nonzero with the named diff on stdout."""

    def test_superset_registry_entry_fails_run(self):
        workdir = ROOT / "pytest-work" / f"adapter-vocab-{uuid.uuid4().hex}"
        workdir.mkdir(parents=True)
        original_registry = lint.MIRROR_REGISTRY
        try:
            fake_adapter = workdir / "fake_adapter.py"
            fake_adapter.write_text(
                'BAD_MIRROR = ("UP", "DEGRADED", "DOWN", "UNKNOWN", "FLAPPING")\n',
                encoding="utf-8",
            )
            relpath = os.path.relpath(fake_adapter, ROOT).replace(os.sep, "/")
            lint.MIRROR_REGISTRY = ((relpath, "BAD_MIRROR", LINK_STATE_POINTER),)

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                rc = lint.run(quiet=True)

            output = stdout.getvalue()
            self.assertEqual(1, rc)
            self.assertIn("code=ADAPTER_VOCABULARY_NOT_SUBSET", output)
            self.assertIn("constant=BAD_MIRROR", output)
            self.assertIn("value=FLAPPING", output)
            # One violation per governed schema the mirror is held against.
            self.assertIn(
                f"adapter vocabulary lint failed total={len(lint.GOVERNED_SCHEMA_FILES)}",
                output,
            )
        finally:
            lint.MIRROR_REGISTRY = original_registry
            shutil.rmtree(workdir, ignore_errors=True)
            try:
                (ROOT / "pytest-work").rmdir()
            except OSError:
                pass


if __name__ == "__main__":
    unittest.main()


class LastBindingLintTest(unittest.TestCase):
    """Runtime semantics are last-binding-wins (attack-pass finding,
    2026-07-27): a mirror grown by a second assignment must be linted at
    its final value, and a non-literal mutation must fail closed."""

    def test_rebinding_cannot_hide_behind_the_first_literal(self):
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "adapter.py"
            src.write_text(
                '_STATES = ("UP", "DEGRADED")\n'
                '_STATES = ("UP", "DEGRADED", "FLAPPING")\n',
                encoding="utf-8",
            )
            self.assertEqual(
                lint.load_mirror_constant(src, "_STATES"),
                ("UP", "DEGRADED", "FLAPPING"),
            )

    def test_augmented_mirror_fails_closed(self):
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "adapter.py"
            src.write_text(
                '_STATES = ("UP",)\n_STATES += ("DOWN",)\n', encoding="utf-8"
            )
            with self.assertRaisesRegex(lint.LintError, "augmented after assignment"):
                lint.load_mirror_constant(src, "_STATES")

    def test_non_literal_rebinding_fails_closed(self):
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "adapter.py"
            src.write_text(
                '_STATES = ("UP",)\n_STATES = _STATES + ("DOWN",)\n',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(lint.LintError, "not a literal vocabulary"):
                lint.load_mirror_constant(src, "_STATES")
