"""Every surface that states the governed battery states all of it.

The battery command literal was hand-copied across nine current-facing
files, and the copies diverged in composition while their flags stayed
byte-identical: two governance documents omitted the examples validator,
and no governance document named the roadmap validator after its C1
restoration, so the documented battery and the wired battery (CI, the
Makefile) disagreed for two cycles (apparatus audit, 2026-08-10, lever 1).
The only machine check was one-directional: it caught a cited flag that
did not exist and could not catch a command that was missing, which is
the exact shape of the v1.1.16 roadmap drop.

This file is the single source. The canonical command list below is the
governed battery; the surfaces enumerated are the ones whose text claims
to state it, and each must carry every canonical command. Contextual
mentions elsewhere (the README operator steps, the tools README's
conformance-pack section, the adapter ladder) deliberately are not
battery definitions and are not scanned. Each canonical command is also
verified runnable-shaped against the tool it names, so the canon cannot
itself drift from the code.
"""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# The governed battery, defined once. Order is the documented run order.
CANONICAL_BATTERY = (
    "python tools/validate_conformance.py --kernel-gate",
    "python tools/validate_examples.py --strict --require-all",
    "python tools/validate_future_roadmap.py",
    "python -m pytest -q",
)

# Surfaces whose text states the governed battery. A new document that
# defines the battery joins this list in the same commit.
BATTERY_SURFACES = (
    "AGENTS.md",
    "CONTRIBUTING.md",
    "CLAUDE.md",
    "RELEASE_CHECKLIST.md",
    "docs/zmeta_change_governance.md",
    "spec/installation-guide.md",
)


def _normalized(text: str) -> str:
    """Separator- and wrap-insensitive form for command matching.

    The PowerShell-fenced copies use backslashes and the prose copy in
    CLAUDE.md wraps commands across lines with backtick and comma
    punctuation; commands compare on their token stream.
    """
    text = text.replace("\\", "/")
    text = re.sub(r"[`,]", " ", text)
    return re.sub(r"\s+", " ", text)


def missing_commands(text: str) -> list[str]:
    haystack = _normalized(text)
    return [command for command in CANONICAL_BATTERY if command not in haystack]


class BatterySingleSourceTest(unittest.TestCase):
    def test_every_canonical_command_is_runnable_shaped(self):
        """The canon must track the code, not the other way around."""
        gate_source = (ROOT / "tools" / "validate_conformance.py").read_text(encoding="utf-8")
        self.assertIn("--kernel-gate", gate_source)
        examples_source = (ROOT / "tools" / "validate_examples.py").read_text(encoding="utf-8")
        self.assertIn("--require-all", examples_source)
        self.assertIn("--strict", examples_source)
        self.assertTrue((ROOT / "tools" / "validate_future_roadmap.py").is_file())

    def test_every_battery_surface_states_the_whole_battery(self):
        offenders = []
        for rel in BATTERY_SURFACES:
            path = ROOT / rel
            self.assertTrue(path.is_file(), f"battery surface {rel} is gone; update the list deliberately")
            missing = missing_commands(path.read_text(encoding="utf-8"))
            if missing:
                offenders.append((rel, missing))
        self.assertEqual(
            offenders, [],
            "a battery-defining document omits canonical commands. The battery "
            "is defined once, in this file; bring the document up to it (or "
            f"change the canon here, deliberately): {offenders}",
        )

    def test_the_omission_direction_actually_fires(self):
        """Self-test on the exact pre-fix state: CONTRIBUTING.md's block
        carried the kernel gate and pytest but not the examples or roadmap
        validators, and the old flag-existence check passed it."""
        pre_fix = (
            "```powershell\n"
            "python tools\\validate_conformance.py --kernel-gate\n"
            "python -m pytest -q\n"
            "git diff --check\n"
            "```\n"
        )
        missing = missing_commands(pre_fix)
        self.assertEqual(
            missing,
            [
                "python tools/validate_examples.py --strict --require-all",
                "python tools/validate_future_roadmap.py",
            ],
            "the matcher must name exactly the two omissions the audit found",
        )

    def test_the_prose_form_is_matched_too(self):
        """CLAUDE.md states the battery in wrapped prose with backticks;
        a matcher that only reads fenced blocks would go vacuous there."""
        prose = (
            "run `python tools/validate_conformance.py --kernel-gate`,\n"
            "`python tools/validate_examples.py --strict --require-all`,\n"
            "and `python tools/validate_future_roadmap.py`,\n"
            "then `python -m pytest -q` as documented."
        )
        self.assertEqual(missing_commands(prose), [])


if __name__ == "__main__":
    unittest.main()
