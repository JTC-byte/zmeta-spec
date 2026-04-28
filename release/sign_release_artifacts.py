"""Generate checksums and detached signatures for ZMeta release artifacts."""

from __future__ import annotations

import argparse
import hashlib
import os
import shlex
import shutil
import subprocess
from pathlib import Path


VERSION = "v1.1.1"


def _release_dir() -> Path:
    return Path(__file__).resolve().parent


def _artifact_names(version: str) -> list[str]:
    return [
        f"zmeta-{version}-dist.zip",
        f"zmeta-edge-{version}.zip",
        f"zmeta-gateway-{version}.zip",
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


def write_checksums(release_dir: Path, version: str) -> Path:
    artifacts = _existing_artifacts(release_dir, version)
    checksum_path = release_dir / f"SHA256SUMS_{version}.txt"
    lines = [f"{_sha256(path)}  {path.name}" for path in artifacts]
    checksum_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return checksum_path


def verify_checksums(release_dir: Path, version: str) -> list[str]:
    checksum_path = release_dir / f"SHA256SUMS_{version}.txt"
    if not checksum_path.is_file():
        raise FileNotFoundError(f"missing checksum file: {checksum_path}")

    failures = []
    for line_no, raw in enumerate(checksum_path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) != 2:
            failures.append(f"line {line_no}: malformed checksum entry")
            continue
        expected, name = parts
        path = release_dir / name
        if not path.is_file():
            failures.append(f"{name}: missing")
            continue
        actual = _sha256(path)
        if actual != expected:
            failures.append(f"{name}: expected {expected}, got {actual}")
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


def _gpg_sign_command(path: Path, key_id: str | None = None) -> list[str]:
    command = [
        "gpg",
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
    return ["gpg", "--verify", str(path.with_name(path.name + ".asc")), str(path)]


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
    if not dry_run and shutil.which("gpg") is None:
        raise SystemExit("gpg not found; install GnuPG or rerun with --dry-run")
    _run_commands([_gpg_sign_command(path, key_id) for path in targets], dry_run)


def verify_gpg(targets: list[Path], dry_run: bool) -> None:
    if not dry_run and shutil.which("gpg") is None:
        raise SystemExit("gpg not found; install GnuPG or rerun with --dry-run")
    _run_commands([_gpg_verify_command(path) for path in targets], dry_run)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate SHA256SUMS and detached PGP signatures for release artifacts."
    )
    parser.add_argument("--version", default=VERSION, help="Release version tag, e.g. v1.1.1.")
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
    version = args.version

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
