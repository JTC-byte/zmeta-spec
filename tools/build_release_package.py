from __future__ import annotations

import argparse
import hashlib
import importlib.util
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "release" / "zmeta-release-manifest.yaml"
DEFAULT_OUTPUT_DIR = ROOT / "release" / "package"
DEFAULT_RELEASE_NOTES_TEMPLATE = ROOT / "release" / "RELEASE_NOTES_TEMPLATE.md"
DEFAULT_ATTESTATION_TEMPLATE = ROOT / "release" / "ATTESTATION_TEMPLATE.yaml"
DEFAULT_CHECKSUM_FILE = "SHA256SUMS.txt"
DEFAULT_ATTESTATION_FILE = "ATTESTATION.yaml"
DEFAULT_PACKAGE_METADATA_FILE = "zmeta-release-package.yaml"
PLACEHOLDER = "explicit_release_input_required"

VALIDATE_MANIFEST_PATH = ROOT / "tools" / "validate_release_manifest.py"
spec = importlib.util.spec_from_file_location("zmeta_validate_release_manifest", VALIDATE_MANIFEST_PATH)
validate_release_manifest = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validate_release_manifest)


def load_yaml(path: Path | str) -> Any:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def _repo_relative(path: Path, root: Path = ROOT) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=False, width=1000), encoding="utf-8")


def _git_dirty(root: Path = ROOT) -> bool:
    try:
        result = subprocess.run(
            ["git", "status", "--short"],
            cwd=root,
            check=True,
            text=True,
            capture_output=True,
        )
    except Exception:
        return True
    return bool(result.stdout.strip())


def _load_valid_manifest(manifest_path: Path) -> dict[str, Any]:
    issues = validate_release_manifest.validate_manifest(manifest_path)
    if issues:
        lines = [f"{issue['code']}: {issue['message']}" for issue in issues]
        raise SystemExit("release manifest validation failed:\n" + "\n".join(lines))
    data = load_yaml(manifest_path)
    if not isinstance(data, dict):
        raise SystemExit(f"release manifest must be a YAML mapping: {manifest_path}")
    return data


def build_attestation(
    manifest: dict[str, Any],
    *,
    release_id: str,
    release_state: str,
    git_commit: str,
    git_tag: str,
    branch: str,
    template_path: Path,
) -> dict[str, Any]:
    template = load_yaml(template_path)
    if not isinstance(template, dict):
        raise SystemExit(f"attestation template must be a YAML mapping: {template_path}")

    template.update(
        {
            "attestation_version": template.get("attestation_version", 1),
            "release_id": release_id,
            "release_state": release_state,
            "git_commit": git_commit,
            "git_tag": git_tag,
            "branch": branch,
            "release_manifest_hash": manifest["release_manifest_hash"],
            "release_bundle_hash": manifest["release_bundle_hash"],
            "semantic_contract_hash": manifest["semantic_contract_hash"],
            "schema_bundle_hash": manifest["schema_bundle_hash"],
            "policy_bundle_hash": manifest["policy_bundle_hash"],
            "extension_registry_hash": manifest["extension_registry_hash"],
            "conformance_class_manifest_hash": manifest["conformance_class_manifest_hash"],
            "profile_projection_catalog_hash": manifest["profile_projection_catalog_hash"],
            "encoding_negative_suite_hash": manifest["encoding_negative_suite_hash"],
            "profile_precision_policy_hash": manifest["profile_precision_policy_hash"],
            "encoding_projection_specs_hash": manifest["encoding_projection_specs_hash"],
            "commands_run": [
                "python tools/validate_release_manifest.py --manifest release/zmeta-release-manifest.yaml",
                "python tools/validate_release_package.py --manifest release/zmeta-release-manifest.yaml --package-dir release/package",
            ],
            "test_summary": {
                "status": PLACEHOLDER,
                "details": PLACEHOLDER,
            },
            "build_environment": {
                "os": platform.platform(),
                "python": platform.python_version(),
                "builder": "tools/build_release_package.py",
            },
            "signer_identity_placeholder": PLACEHOLDER,
            "signature_artifacts": {
                "release_manifest": PLACEHOLDER,
                "checksums": PLACEHOLDER,
            },
            # Sourced from the manifest only - never a hardcoded fallback
            # (R1-11 R11-14: a stale hardcoded "D-003 OPEN" shipped in four
            # post-closure release attestations).
            "known_open_issues": manifest.get("known_open_issues", []),
        }
    )
    return template


def _checksum_lines(paths: list[Path], package_dir: Path) -> list[str]:
    lines = []
    for path in sorted(paths, key=lambda item: item.relative_to(package_dir).as_posix()):
        rel = path.relative_to(package_dir).as_posix()
        lines.append(f"{_sha256_file(path)}  {rel}")
    return lines


def package_metadata(
    manifest: dict[str, Any],
    *,
    release_id: str,
    release_state: str,
    signature_mode: str,
    package_artifacts: list[str],
) -> dict[str, Any]:
    return {
        "package_version": 1,
        "release_id": release_id,
        "release_state": release_state,
        "signature_mode": signature_mode,
        "release_manifest": "release/zmeta-release-manifest.yaml",
        "release_manifest_hash": manifest["release_manifest_hash"],
        "release_bundle_hash": manifest["release_bundle_hash"],
        "semantic_contract_hash": manifest["semantic_contract_hash"],
        "schema_bundle_hash": manifest["schema_bundle_hash"],
        "policy_bundle_hash": manifest["policy_bundle_hash"],
        "extension_registry_hash": manifest["extension_registry_hash"],
        "conformance_class_manifest_hash": manifest["conformance_class_manifest_hash"],
        "package_artifacts": package_artifacts,
        "notes": [
            "No signatures are generated by default.",
            "This package metadata does not create ZMeta semantics or make future vocabulary valid.",
        ],
    }


def build_package(
    *,
    manifest_path: Path,
    output_dir: Path,
    release_id: str | None = None,
    release_state: str = "release_candidate",
    release_notes_template: Path = DEFAULT_RELEASE_NOTES_TEMPLATE,
    attestation_template: Path = DEFAULT_ATTESTATION_TEMPLATE,
    checksum_file: str = DEFAULT_CHECKSUM_FILE,
    attestation_output: str = DEFAULT_ATTESTATION_FILE,
    signature_mode: str = "external",
    no_signatures: bool = True,
    dry_run: bool = False,
    clean_output: bool = False,
    allow_dirty: bool = False,
) -> dict[str, Any]:
    manifest = _load_valid_manifest(manifest_path)
    release_id = release_id or str(manifest.get("release_id") or PLACEHOLDER)

    if not no_signatures:
        raise SystemExit("signature generation is not implemented; rerun with --no-signatures")
    if signature_mode != "external":
        raise SystemExit("only --signature-mode external is supported in S1-12B")
    if not dry_run and not allow_dirty and _git_dirty():
        raise SystemExit("working tree is dirty; rerun after committing changes or pass --allow-dirty")

    attestation = build_attestation(
        manifest,
        release_id=release_id,
        release_state=release_state,
        git_commit=str(manifest.get("git_commit") or PLACEHOLDER),
        git_tag=PLACEHOLDER,
        branch=str(manifest.get("branch") or PLACEHOLDER),
        template_path=attestation_template,
    )

    planned_files = [
        DEFAULT_PACKAGE_METADATA_FILE,
        "RELEASE_NOTES.md",
        attestation_output,
        checksum_file,
    ]
    metadata = package_metadata(
        manifest,
        release_id=release_id,
        release_state=release_state,
        signature_mode="none" if no_signatures else signature_mode,
        package_artifacts=list(planned_files),
    )

    if dry_run:
        return {
            "dry_run": True,
            "output_dir": output_dir.as_posix(),
            "planned_files": planned_files,
            "package_metadata": metadata,
            "attestation": attestation,
        }

    if clean_output and output_dir.exists():
        resolved = output_dir.resolve()
        allowed = (ROOT / "release").resolve()
        if allowed not in resolved.parents:
            raise SystemExit(f"refusing to clean output outside release directory: {output_dir}")
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    metadata_path = output_dir / DEFAULT_PACKAGE_METADATA_FILE
    notes_path = output_dir / "RELEASE_NOTES.md"
    attestation_path = output_dir / attestation_output
    checksum_path = output_dir / checksum_file

    _write_yaml(metadata_path, metadata)
    notes_path.write_text(release_notes_template.read_text(encoding="utf-8"), encoding="utf-8")
    _write_yaml(attestation_path, attestation)

    checksum_targets = [metadata_path, notes_path, attestation_path]
    checksum_path.write_text("\n".join(_checksum_lines(checksum_targets, output_dir)) + "\n", encoding="utf-8")

    return {
        "dry_run": False,
        "output_dir": output_dir.as_posix(),
        "written": [path.as_posix() for path in [metadata_path, notes_path, attestation_path, checksum_path]],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a ZMeta release package in no-signature mode.")
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST), help="Path to release manifest YAML.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Release package output directory.")
    parser.add_argument("--release-id", help="Explicit release ID for package metadata.")
    parser.add_argument("--release-state", default="release_candidate", help="Release package state.")
    parser.add_argument("--release-notes-template", default=str(DEFAULT_RELEASE_NOTES_TEMPLATE))
    parser.add_argument("--attestation-template", default=str(DEFAULT_ATTESTATION_TEMPLATE))
    parser.add_argument("--dry-run", action="store_true", help="Print planned package metadata without writing files.")
    parser.add_argument("--clean-output", action="store_true", help="Remove the output directory before writing.")
    parser.add_argument("--no-signatures", action="store_true", default=True, help="Do not generate signatures.")
    parser.add_argument("--signature-mode", default="external", choices=["external"], help="External signature mode placeholder.")
    parser.add_argument("--checksum-file", default=DEFAULT_CHECKSUM_FILE)
    parser.add_argument("--attestation-output", default=DEFAULT_ATTESTATION_FILE)
    parser.add_argument("--allow-dirty", action="store_true", help="Allow writing package output from a dirty working tree.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = build_package(
        manifest_path=Path(args.manifest),
        output_dir=Path(args.output_dir),
        release_id=args.release_id,
        release_state=args.release_state,
        release_notes_template=Path(args.release_notes_template),
        attestation_template=Path(args.attestation_template),
        checksum_file=args.checksum_file,
        attestation_output=args.attestation_output,
        signature_mode=args.signature_mode,
        no_signatures=args.no_signatures,
        dry_run=args.dry_run,
        clean_output=args.clean_output,
        allow_dirty=args.allow_dirty,
    )
    if args.dry_run:
        sys.stdout.write(yaml.safe_dump(result, sort_keys=False, allow_unicode=False, width=1000))
    else:
        print(f"wrote release package: {result['output_dir']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
