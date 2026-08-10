"""The --kernel-gate alias is the battery's single named form.

The kernel protection gate used to exist only as a hand-maintained flag
string copied across the Makefile, CI, and every governance document that
quotes the command; the 2026-08-10 apparatus audit counted sixteen
current-facing copies and two live drifts. The alias makes the gate one
stable token, and this test pins the two facts that make that safe: the
alias expands to exactly the documented flag set, and every flag it enables
has an implementation block in the tool, so the alias cannot silently
enable nothing.
"""

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location(
    "validate_conformance", ROOT / "tools" / "validate_conformance.py"
)
validate_conformance = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(validate_conformance)


def _parse(argv, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["validate_conformance.py", *argv])
    return validate_conformance.parse_args()


def test_kernel_gate_expands_to_the_full_flag_set(monkeypatch):
    args = _parse(["--kernel-gate"], monkeypatch)
    for flag in validate_conformance.KERNEL_GATE_CHECKS:
        assert getattr(args, flag) is True, f"--kernel-gate must enable --{flag}"


def test_kernel_gate_equals_the_hand_flagged_invocation(monkeypatch):
    # The alias and the historical long form must be interchangeable: any
    # divergence means documents quoting either form disagree about what
    # the gate runs.
    long_form = _parse(
        [
            "--strict",
            "--profile-projection",
            "--extension-registry",
            "--conformance-classes",
            "--encoding-negative",
            "--precision-policy",
            "--release-manifest",
            "--release-package",
            "--bad-events",
            "--adapter-harness",
        ],
        monkeypatch,
    )
    alias_form = _parse(["--kernel-gate"], monkeypatch)
    for flag in validate_conformance.KERNEL_GATE_CHECKS:
        assert getattr(alias_form, flag) == getattr(long_form, flag)


def test_every_gate_check_has_an_implementation_block():
    # A flag added to KERNEL_GATE_CHECKS without an `if args.<flag>:` block
    # would run nothing while claiming coverage, which is the vacuity class.
    source = (ROOT / "tools" / "validate_conformance.py").read_text(encoding="utf-8")
    for flag in validate_conformance.KERNEL_GATE_CHECKS:
        if flag == "strict":
            continue
        assert f"if args.{flag}:" in source, (
            f"KERNEL_GATE_CHECKS names '{flag}' but the tool has no "
            f"'if args.{flag}:' implementation block"
        )
