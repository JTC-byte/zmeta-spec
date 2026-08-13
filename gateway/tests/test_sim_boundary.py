"""tools/sim must stay extractable, and that is enforced rather than promised.

ZMeta is a data standard. The simulation harnesses under tools/sim are an
operational convenience built on top of it: useful for proving a deployment
works, and not part of what the standard defines or enforces. The risk is not
that they are wrong, it is that something governed quietly starts importing
them, at which point the standard has grown an implementation dependency and
moving the harnesses to their own repository stops being a directory move.

So the rule is one-directional. tools/sim may read anything in the repository.
Nothing governed may read tools/sim.

"Governed" here is the enforcement surface: the schema and policy files, the
validators and kernel-gate tools in tools/, the conformance corpora, and the
gateway runtime. If that set is ever redrawn, redraw it here too.

Retirement condition evaluated and DECLINED (2026-08-13). The apparatus
audit drafted "retires if tools/sim is curated out of bundles". The
curation landed that day, and it inverts the condition instead of meeting
it: with sim absent from every shipped bundle, a governed import of
tools/sim would leave the in-repo battery green (sim exists in the repo)
while every shipped bundle breaks at import. This guard is now the only
in-repo detector of that state, so it stays.

The scope question this protects is recorded as doctrine log SIM1-04.
"""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SIM = ROOT / "tools" / "sim"

# Anything that would make a sim harness load-bearing. The separator allows one
# or two backslashes because a Windows path written in Python source carries the
# escaped form ("tools\\sim"), and the single-backslash pattern missed it. That
# gap was found by test_the_reference_detector_actually_fires below, which is
# the entire reason that test exists.
SIM_REFERENCE = re.compile(
    r"(from\s+tools\.sim|import\s+tools\.sim|from\s+sim\s+import|tools[/\\]{1,2}sim)"
)

# Directories whose contents define or enforce the standard.
GOVERNED_TREES = ("schema", "policy", "spec", "conformance", "gateway/src")


def governed_files():
    """Every governed source file, excluding tools/sim itself."""
    found = []
    for tree in GOVERNED_TREES:
        base = ROOT / tree
        if not base.is_dir():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or "__pycache__" in path.parts:
                continue
            if path.suffix in (".py", ".yaml", ".yml", ".json", ".jsonl", ".md"):
                found.append(path)
    # tools/ at one level: the validators and gate tools, not the sim subtree.
    for path in (ROOT / "tools").glob("*.py"):
        found.append(path)
    return found


class SimBoundaryTest(unittest.TestCase):
    def test_the_sim_directory_exists_and_has_content(self):
        """Non-vacuity: with no harnesses present every assertion below is trivially true.

        A release bundle is the one place the harnesses are legitimately
        absent: they are curated out of every bundle (2026-08-13), the
        bundles ship this battery, and a bundle root carries the
        VERSION.txt the builders write. There the check skips by name
        instead of alarming an operator about a directory the bundle
        deliberately does not carry. In a repository checkout (no
        VERSION.txt at root) a missing tools/sim stays a hard failure,
        so the floor cannot go quietly vacuous where the guard matters.
        """
        if not SIM.is_dir() and (ROOT / "VERSION.txt").is_file():
            self.skipTest("tools/sim is curated out of release bundles by design")
        self.assertTrue(SIM.is_dir(), "tools/sim is missing")
        harnesses = sorted(p.name for p in SIM.glob("*.py"))
        self.assertTrue(harnesses, "tools/sim contains no harnesses, so this file guards nothing")

    def test_the_governed_file_set_is_not_empty(self):
        """Non-vacuity: a broken locator would scan nothing and pass."""
        files = governed_files()
        self.assertGreater(
            len(files), 50,
            f"governed file locator found only {len(files)} files; it has stopped working "
            "and this boundary is no longer being checked",
        )

    def test_nothing_governed_references_tools_sim(self):
        offenders = []
        for path in governed_files():
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            if SIM_REFERENCE.search(text):
                offenders.append(path.relative_to(ROOT).as_posix())
        self.assertEqual(
            offenders, [],
            "a governed artifact references tools/sim: "
            f"{offenders}. The simulation harnesses are an operational convenience "
            "and must never become load-bearing for the standard. Either the "
            "dependency is wrong, or the harness has earned promotion out of "
            "tools/sim and into the enforcement surface deliberately.",
        )

    def test_the_reference_detector_actually_fires(self):
        """The detector must catch what it claims to catch, in each spelling."""
        for sample in (
            "from tools.sim import two_node",
            "import tools.sim.throughput",
            "subprocess.run(['python', 'tools/sim/two_node.py'])",
            "path = ROOT / 'tools\\\\sim' / 'throughput.py'",
        ):
            with self.subTest(sample=sample):
                self.assertTrue(
                    SIM_REFERENCE.search(sample),
                    f"detector missed {sample!r}, so a real dependency would pass unnoticed",
                )

    def test_sim_harnesses_do_not_import_each_other_into_a_package(self):
        """Each harness stands alone, so extracting one is not a dependency exercise."""
        for path in SIM.glob("*.py"):
            text = path.read_text(encoding="utf-8")
            self.assertNotIn(
                "from tools.sim", text,
                f"{path.name} imports a sibling harness as a package; keep them standalone",
            )


if __name__ == "__main__":
    unittest.main()
