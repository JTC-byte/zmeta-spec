"""One-command wrapper for the tool-based steps of the adapter ladder.

Runs the validator steps of the adapters/AUTHORING.md ladder with a single
command. Two ladder steps stay outside it: your colocated pytest (ladder
step 1) still runs separately, and the full kernel gate (ladder step 5) runs
only with --kernel-gate. The delegated steps invoke the governed validators
they name (tools/validate.py, tools/check_compat.py,
tools/validate_adapter_conformance.py, tools/validate_conformance.py), and
those remain the authority; the built-in fixture lint and empty-input guard
are strictly additive — they can add failures, never mask one. The commands
are printed as they run so authors learn the underlying ladder.

Usage:
  python tools/check_adapter.py --events my-adapter-output.jsonl
  python tools/check_adapter.py --fixtures my-fixtures.jsonl
  python tools/check_adapter.py --events out.jsonl --fixtures f.jsonl --kernel-gate
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_SCHEMA_PATH = ROOT / "conformance" / "adapter-harness" / "fixture.schema.json"
MANIFEST_PATH = ROOT / "release" / "zmeta-release-manifest.yaml"

KERNEL_GATE_ARGS = [
    "tools/validate_conformance.py",
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
]


def default_compat_target():
    """Read the current release id from the release manifest (zmeta-vX -> vX)."""
    try:
        import yaml

        manifest = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
        release_id = str(manifest.get("release_id", ""))
    except Exception:
        return None
    if release_id.startswith("zmeta-"):
        return release_id[len("zmeta-"):]
    return release_id or None


def count_nonempty_lines(path: Path):
    with open(path, "r", encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def lint_fixtures(path: Path):
    """Validate each fixture line against the advisory fixture schema."""
    import jsonschema

    schema = json.loads(FIXTURE_SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    errors = []
    total = 0
    with open(path, "r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            total += 1
            try:
                fixture = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"line {line_no}: invalid JSON ({exc.msg})")
                continue
            for error in validator.iter_errors(fixture):
                where = "/".join(str(p) for p in error.absolute_path) or "<root>"
                errors.append(f"line {line_no}: {where}: {error.message}")
    if total == 0:
        errors.append("no fixture lines found - an empty file proves nothing")
    return errors


def run_step(label, cmd):
    print(f"\n=== {label} ===", flush=True)
    print("$ " + " ".join(cmd), flush=True)
    completed = subprocess.run(cmd, cwd=ROOT)
    return completed.returncode == 0


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Run the tool-based steps of the adapters/AUTHORING.md validation "
            "ladder in one command (colocated pytest runs separately; the "
            "kernel gate is opt-in via --kernel-gate)."
        )
    )
    parser.add_argument(
        "--events",
        help="JSONL file of events emitted by your adapter (runs schema/policy validation and the compatibility pre-check).",
    )
    parser.add_argument(
        "--fixtures",
        help="Adapter-harness fixture JSONL (linted against fixture.schema.json, then run through the harness).",
    )
    parser.add_argument("--profile", default="H", choices=["L", "M", "H"])
    parser.add_argument(
        "--target",
        help="check_compat.py target release (default: release_id from release/zmeta-release-manifest.yaml).",
    )
    parser.add_argument(
        "--skip-compat",
        action="store_true",
        help="Skip the check_compat.py step.",
    )
    parser.add_argument(
        "--kernel-gate",
        action="store_true",
        help="Also run the full kernel-protection conformance gate.",
    )
    args = parser.parse_args()

    if not args.events and not args.fixtures:
        parser.error("provide --events and/or --fixtures")

    results = []

    if args.fixtures:
        fixtures_path = Path(args.fixtures)
        print(f"\n=== fixture lint ({fixtures_path}) ===", flush=True)
        print(f"(advisory schema: {FIXTURE_SCHEMA_PATH.relative_to(ROOT)})", flush=True)
        errors = lint_fixtures(fixtures_path)
        for error in errors:
            print(f"FIXTURE {error}", flush=True)
        results.append(("fixture lint", not errors))

    if args.events:
        event_count = count_nonempty_lines(Path(args.events))
        if event_count == 0:
            print("\n=== events input ===", flush=True)
            print(
                f"FAIL: {args.events} contains no events - an empty file proves nothing",
                flush=True,
            )
            results.append(("events input", False))
        results.append(
            (
                "schema/policy validation",
                run_step(
                    "schema/policy validation",
                    [
                        sys.executable,
                        "tools/validate.py",
                        "--file",
                        args.events,
                        "--profile",
                        args.profile,
                        "--strict",
                    ],
                ),
            )
        )
        if not args.skip_compat:
            target = args.target or default_compat_target()
            if target is None:
                print("\n=== compatibility pre-check ===")
                print("SKIP: no --target given and release manifest unreadable")
                results.append(("compatibility pre-check", False))
            else:
                results.append(
                    (
                        "compatibility pre-check",
                        run_step(
                            "compatibility pre-check",
                            [
                                sys.executable,
                                "tools/check_compat.py",
                                args.events,
                                "--target",
                                target,
                            ],
                        ),
                    )
                )

    if args.fixtures:
        results.append(
            (
                "adapter harness",
                run_step(
                    "adapter harness",
                    [
                        sys.executable,
                        "tools/validate_adapter_conformance.py",
                        "--fixtures",
                        args.fixtures,
                    ],
                ),
            )
        )

    if args.kernel_gate:
        results.append(
            (
                "kernel gate",
                run_step("kernel gate", [sys.executable] + KERNEL_GATE_ARGS),
            )
        )

    print("\n=== summary ===")
    failed = 0
    for label, ok in results:
        print(f"{'PASS' if ok else 'FAIL'}  {label}")
        if not ok:
            failed += 1
    if failed:
        print(f"adapter check FAILED ({failed} step(s))")
        return 1
    print("adapter check ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
