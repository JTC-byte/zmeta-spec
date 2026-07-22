"""Generate checksums and detached signatures for ZMeta release artifacts."""

from __future__ import annotations

import argparse
import hashlib
import os
import shlex
import shutil
import subprocess
from pathlib import Path


MANIFEST_PATH = Path(__file__).resolve().parent / "zmeta-release-manifest.yaml"


def _release_dir() -> Path:
    return Path(__file__).resolve().parent


def default_version_tag():
    """Read the current release id from the release manifest (zmeta-vX -> vX)."""
    try:
        import yaml

        manifest = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
        release_id = str(manifest.get("release_id", ""))
    except Exception:
        return None
    if release_id.startswith("zmeta-"):
        release_id = release_id[len("zmeta-"):]
    return release_id or None


def _artifact_names(version: str) -> list[str]:
    return [
        f"zmeta-{version}-dist.zip",
        f"zmeta-edge-{version}.zip",
        f"zmeta-gateway-{version}.zip",
        f"zmeta-release-package-{version}.zip",
        "zmeta-release-manifest.yaml",
        f"RELEASE_NOTES_{version}.md",
        f"VALIDATION_REPORT_{version}.md",
    ]


def _sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _existing_artifacts(release_dir: Path, version: str) -> list[Path]:
    artifacts = []
    missing = []
    for name in _artifact_names(version):
        path = release_dir / name
        if path.is_file():
            artifacts.append(path)
        else:
            missing.append(name)
    if missing:
        raise FileNotFoundError("missing release artifacts: " + ", ".join(missing))
    return artifacts


def _ensure_package_zip(release_dir: Path, version: str) -> None:
    """Build zmeta-release-package-<version>.zip from package-<version>/ when absent.

    tools/build_release_package.py (governed) writes the package directory
    but no archive, while the zip is a required checksum/release asset.
    Building it here at checksum time closes that gap without touching the
    governed builder. An existing zip is never overwritten, so a published
    artifact cannot be silently rebuilt.
    """
    zip_path = release_dir / f"zmeta-release-package-{version}.zip"
    package_dir = release_dir / f"package-{version}"
    if zip_path.is_file() or not package_dir.is_dir():
        return
    shutil.make_archive(str(zip_path.with_suffix("")), "zip", root_dir=package_dir)
    print(f"built {zip_path.name} from {package_dir.name}/")


def write_checksums(release_dir: Path, version: str) -> Path:
    _ensure_package_zip(release_dir, version)
    artifacts = _existing_artifacts(release_dir, version)
    checksum_path = release_dir / f"SHA256SUMS_{version}.txt"
    lines = [f"{_sha256(path)}  {path.name}" for path in artifacts]
    # LF line endings so plain `sha256sum -c` works on Linux. Applies only to
    # newly written checksum files; published SHA256SUMS_*.txt are immutable.
    with checksum_path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines) + "\n")
    return checksum_path


def verify_checksums(release_dir: Path, version: str) -> list[str]:
    checksum_path = release_dir / f"SHA256SUMS_{version}.txt"
    if not checksum_path.is_file():
        raise FileNotFoundError(f"missing checksum file: {checksum_path}")

    failures = []
    listed_names: set[str] = set()
    valid_lines = 0
    for line_no, raw in enumerate(checksum_path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) != 2:
            failures.append(f"line {line_no}: malformed checksum entry")
            continue
        expected, name = parts
        valid_lines += 1
        listed_names.add(name)
        path = release_dir / name
        if not path.is_file():
            failures.append(f"{name}: missing")
            continue
        actual = _sha256(path)
        if actual != expected:
            failures.append(f"{name}: expected {expected}, got {actual}")

    # Parity with GNU `sha256sum -c`, which errors when no properly formatted
    # checksum lines are found - an empty checksum file proves nothing.
    if valid_lines == 0:
        failures.append(
            f"{checksum_path.name}: no valid checksum lines found - an empty checksum file proves nothing"
        )

    # Coverage cross-check: every expected release artifact that exists on
    # disk must be listed, so a truncated checksum file cannot verify clean.
    for name in _artifact_names(version):
        if (release_dir / name).is_file() and name not in listed_names:
            failures.append(f"{name}: present on disk but not listed in {checksum_path.name}")
    return failures


def _signature_targets(release_dir: Path, version: str, target: str) -> list[Path]:
    checksum_path = release_dir / f"SHA256SUMS_{version}.txt"
    if target == "checksums":
        targets = [checksum_path]
    elif target == "assets":
        targets = _existing_artifacts(release_dir, version)
    elif target == "all":
        targets = [checksum_path] + _existing_artifacts(release_dir, version)
    else:
        raise ValueError(f"unsupported signature target: {target}")

    missing = [path.name for path in targets if not path.is_file()]
    if missing:
        raise FileNotFoundError("missing signature targets: " + ", ".join(missing))
    return targets


def _gpg_executable() -> str | None:
    configured = os.environ.get("GPG_EXE")
    if configured:
        path = Path(configured)
        if path.is_file():
            return str(path)
    found = shutil.which("gpg")
    if found:
        return found
    if os.name == "nt":
        for candidate in (
            Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "GnuPG" / "bin" / "gpg.exe",
            Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"))
            / "GnuPG"
            / "bin"
            / "gpg.exe",
        ):
            if candidate.is_file():
                return str(candidate)
    return None


def _gpg_sign_command(path: Path, key_id: str | None = None) -> list[str]:
    gpg = _gpg_executable() or "gpg"
    command = [
        gpg,
        "--yes",
        "--armor",
        "--detach-sign",
        "--output",
        str(path.with_name(path.name + ".asc")),
    ]
    if key_id:
        command.extend(["--local-user", key_id])
    command.append(str(path))
    return command


def _gpg_verify_command(path: Path) -> list[str]:
    return [_gpg_executable() or "gpg", "--verify", str(path.with_name(path.name + ".asc")), str(path)]


def _format_command(command: list[str]) -> str:
    if os.name == "nt":
        return subprocess.list2cmdline(command)
    return shlex.join(command)


def _run_commands(commands: list[list[str]], dry_run: bool) -> None:
    for command in commands:
        print(_format_command(command))
        if not dry_run:
            subprocess.run(command, check=True)


def sign_with_gpg(targets: list[Path], key_id: str | None, dry_run: bool) -> None:
    if not dry_run and _gpg_executable() is None:
        raise SystemExit("gpg not found; install GnuPG or rerun with --dry-run")
    _run_commands([_gpg_sign_command(path, key_id) for path in targets], dry_run)


def verify_gpg(targets: list[Path], dry_run: bool) -> None:
    if not dry_run and _gpg_executable() is None:
        raise SystemExit("gpg not found; install GnuPG or rerun with --dry-run")
    _run_commands([_gpg_verify_command(path) for path in targets], dry_run)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate SHA256SUMS and detached PGP signatures for release artifacts."
    )
    parser.add_argument(
        "--version",
        default=None,
        help="Release version tag, e.g. v1.1.16 (default: release_id from release/zmeta-release-manifest.yaml).",
    )
    parser.add_argument("--release-dir", default=str(_release_dir()), help="Directory containing artifacts.")
    parser.add_argument("--write-checksums", action="store_true", help="Rewrite SHA256SUMS_<version>.txt.")
    parser.add_argument("--verify-checksums", action="store_true", help="Verify SHA256SUMS_<version>.txt.")
    parser.add_argument("--sign", action="store_true", help="Create detached ASCII-armored GPG signatures.")
    parser.add_argument("--verify-signatures", action="store_true", help="Verify detached GPG signatures.")
    parser.add_argument(
        "--target",
        choices=["checksums", "assets", "all"],
        default="all",
        help="Files to sign or verify.",
    )
    parser.add_argument("--gpg-key-id", help="Optional GPG signing key ID or fingerprint.")
    parser.add_argument("--dry-run", action="store_true", help="Print signing commands without running them.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    release_dir = Path(args.release_dir).resolve()
    version = args.version or default_version_tag()
    if not version:
        raise SystemExit(
            "could not derive release version from release/zmeta-release-manifest.yaml; pass --version"
        )

    if args.write_checksums:
        checksum_path = write_checksums(release_dir, version)
        print(f"wrote {checksum_path}")

    if args.verify_checksums:
        failures = verify_checksums(release_dir, version)
        if failures:
            for failure in failures:
                print(f"checksum failed: {failure}")
            return 1
        print(f"checksums ok: SHA256SUMS_{version}.txt")

    if args.sign:
        targets = _signature_targets(release_dir, version, args.target)
        sign_with_gpg(targets, args.gpg_key_id, args.dry_run)

    if args.verify_signatures:
        targets = _signature_targets(release_dir, version, args.target)
        verify_gpg(targets, args.dry_run)

    if not any((args.write_checksums, args.verify_checksums, args.sign, args.verify_signatures)):
        raise SystemExit("choose at least one action")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
