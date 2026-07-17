"""Pytest shim for the teaching-corpus examples gate.

Shells the mandated kernel-gate command (`python tools/validate_examples.py
--strict --require-all`) so the full pytest suite also covers the example
corpora: every registered example file must exist, be non-empty, and validate
cleanly against the schema and policy pack.
"""

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_examples_gate_strict_require_all_passes():
    result = subprocess.run(
        [sys.executable, "tools/validate_examples.py", "--strict", "--require-all"],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, (
        f"examples gate failed (python tools/validate_examples.py --strict --require-all):\n"
        f"{result.stdout}\n{result.stderr}"
    )
