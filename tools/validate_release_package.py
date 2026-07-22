from __future__ import annotations

import argparse
import hashlib
import importlib.util
import re
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "release" / "zmeta-release-manifest.yaml"
DEFAULT_PACKAGE_DIR = ROOT / "release" / "package"
TEMPLATE_PATHS = [
    ROOT / "spec" / "release-signing-attestation.md",
    ROOT / "release" / "RELEASE_NOTES_TEMPLATE.md",
    ROOT / "release" / "ATTESTATION_TEMPLATE.yaml",
    ROOT / "release" / "RELEASE_PACKAGE_README.md",
]
REQUIRED_ATTESTATION_FIELDS = {
    "attestation_version",
    "release_id",
    "release_state",
    "git_commit",
    "git_tag",
    "branch",
    "release_manifest_hash",
    "release_bundle_hash",
    "semantic_contract_hash",
    "schema_bundle_hash",
    "policy_bundle_hash",
    "extension_registry_hash",
    "conformance_class_manifest_hash",
    "profile_projection_catalog_hash",
    "encoding_negative_suite_hash",
    "profile_precision_policy_hash",
    "encoding_projection_specs_hash",
    "commands_run",
    "test_summary",
    "build_environment",
    "signer_identity_placeholder",
    "signature_artifacts",
    "known_open_issues",
    "limitations",
    "notes",
}
HASH_FIELDS = [
    "release_manifest_hash",
    "release_bundle_hash",
    "semantic_contract_hash",
    "schema_bundle_hash",
    "policy_bundle_hash",
    "extension_registry_hash",
    "conformance_class_manifest_hash",
    "profile_projection_catalog_hash",
    "encoding_negative_suite_hash",
    "profile_precision_policy_hash",
    "encoding_projection_specs_hash",
]
SECRET_FILENAME_PATTERNS = [
    ".key",
    ".pem",
    ".p12",
    ".pfx",
    "id_rsa",
    "id_ed25519",
    "secret",
    "token",
    "credential",
    "private",
]
SECRET_CONTENT_PATTERNS = [
    "BEGIN PRIVATE KEY",
    "BEGIN RSA PRIVATE KEY",
    "BEGIN OPENSSH PRIVATE KEY",
    "AWS_SECRET_ACCESS_KEY",
    "PRIVATE_TOKEN",
    "GITHUB_TOKEN",
    "API_KEY=",
    "password=",
    "secret=",
]

VALIDATE_MANIFEST_PATH = ROOT / "tools" / "validate_release_manifest.py"
spec = importlib.util.spec_from_file_location("zmeta_validate_release_manifest", VALIDATE_MANIFEST_PATH)
validate_release_manifest = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validate_release_manifest)


def _issue(code: str, message: str, *, item: str | None = None) -> dict[str, str]:
    out = {"code": code, "message": message}
    if item:
        out["item"] = item
    return out


def load_yaml(path: Path | str) -> Any:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def _sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def scan_no_secrets(paths: list[Path]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    files: list[Path] = []
    for path in paths:
        if path.is_dir():
            files.extend(item for item in path.rglob("*") if item.is_file())
        elif path.is_file():
            files.append(path)
        else:
            issues.append(_issue("RELEASE_PACKAGE_SCAN_PATH_MISSING", f"scan path not found: {path}", item=str(path)))

    for path in files:
        lower_name = path.name.lower()
        for pattern in SECRET_FILENAME_PATTERNS:
            if pattern in lower_name:
                issues.append(
                    _issue(
                        "RELEASE_PACKAGE_SECRET_FILENAME",
                        f"secret-like file name is not allowed: {path.name}",
                        item=str(path),
                    )
                )
                break
        try:
            data = path.read_bytes()
        except OSError as exc:
            issues.append(_issue("RELEASE_PACKAGE_SCAN_READ_FAILED", f"could not read file: {exc}", item=str(path)))
            continue
        if b"\x00" in data[:4096]:
            continue
        text = data[:1024 * 1024].decode("utf-8", errors="ignore")
        for pattern in SECRET_CONTENT_PATTERNS:
            if pattern in text:
                issues.append(
                    _issue(
                        "RELEASE_PACKAGE_SECRET_CONTENT",
                        f"secret-like content pattern is not allowed: {pattern}",
                        item=str(path),
                    )
                )
        if re.search(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----", text):
            issues.append(
                _issue(
                    "RELEASE_PACKAGE_PRIVATE_KEY_CONTENT",
                    "private-key block is not allowed",
                    item=str(path),
                )
            )
    return issues


def _load_valid_manifest(manifest_path: Path) -> tuple[dict[str, Any] | None, list[dict[str, str]]]:
    issues = validate_release_manifest.validate_manifest(manifest_path)
    if issues:
        return None, [_issue("RELEASE_PACKAGE_MANIFEST_INVALID", issue["message"], item=issue.get("item")) for issue in issues]
    data = load_yaml(manifest_path)
    if not isinstance(data, dict):
        return None, [_issue("RELEASE_PACKAGE_MANIFEST_INVALID", "manifest must be a YAML mapping")]
    return data, []


def validate_templates() -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    for path in TEMPLATE_PATHS:
        if not path.is_file():
            issues.append(_issue("RELEASE_PACKAGE_TEMPLATE_MISSING", f"template missing: {path}", item=str(path)))
    attestation_path = ROOT / "release" / "ATTESTATION_TEMPLATE.yaml"
    if attestation_path.is_file():
        data = load_yaml(attestation_path)
        if not isinstance(data, dict):
            issues.append(_issue("RELEASE_PACKAGE_ATTESTATION_TEMPLATE_INVALID", "attestation template must be a YAML mapping"))
        else:
            for field in sorted(REQUIRED_ATTESTATION_FIELDS):
                if field not in data:
                    issues.append(_issue("RELEASE_PACKAGE_ATTESTATION_FIELD_MISSING", f"missing attestation template field: {field}"))
    existing_templates = [path for path in TEMPLATE_PATHS if path.exists()]
    issues.extend(scan_no_secrets(existing_templates))
    return issues


def _validate_attestation(path: Path, manifest: dict[str, Any]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if not path.is_file():
        return [_issue("RELEASE_PACKAGE_ATTESTATION_MISSING", f"attestation not found: {path}", item=str(path))]
    data = load_yaml(path)
    if not isinstance(data, dict):
        return [_issue("RELEASE_PACKAGE_ATTESTATION_INVALID", "attestation must be a YAML mapping", item=str(path))]
    for field in sorted(REQUIRED_ATTESTATION_FIELDS):
        if field not in data:
            issues.append(_issue("RELEASE_PACKAGE_ATTESTATION_FIELD_MISSING", f"missing attestation field: {field}", item=field))
    for field in HASH_FIELDS:
        if data.get(field) != manifest.get(field):
            issues.append(
                _issue(
                    "RELEASE_PACKAGE_ATTESTATION_HASH_MISMATCH",
                    f"{field} expected {manifest.get(field)}, got {data.get(field)}",
                    item=field,
                )
            )
    # The attestation's open-issue list must mirror the manifest's - the
    # manifest is the governed source of register state. The previous check
    # required the literal "D-003", machine-enforcing a stale claim for
    # four releases after the register closed (R1-11 R11-14).
    attested = [str(item) for item in data.get("known_open_issues", []) or []]
    manifest_issues = [str(item) for item in manifest.get("known_open_issues", []) or []]
    if attested != manifest_issues:
        issues.append(
            _issue(
                "RELEASE_PACKAGE_ATTESTATION_OPEN_ISSUE_MISMATCH",
                f"known_open_issues must mirror the manifest: expected {manifest_issues}, got {attested}",
            )
        )
    return issues


def _package_artifact_list(metadata_path: Path) -> list[str]:
    """Read package_artifacts from the package metadata for coverage checks."""
    if not metadata_path.is_file():
        return []
    try:
        data = load_yaml(metadata_path)
    except Exception:
        return []
    if not isinstance(data, dict):
        return []
    artifacts = data.get("package_artifacts", [])
    if not isinstance(artifacts, list):
        return []
    return [str(item) for item in artifacts]


def _validate_checksums(
    path: Path,
    package_dir: Path,
    expected_artifacts: list[str] | None = None,
) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if not path.is_file():
        return [_issue("RELEASE_PACKAGE_CHECKSUMS_MISSING", f"checksum file not found: {path}", item=str(path))]
    listed: set[str] = set()
    valid_lines = 0
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) != 2:
            issues.append(_issue("RELEASE_PACKAGE_CHECKSUM_MALFORMED", f"line {line_no} is malformed", item=str(path)))
            continue
        expected, rel = parts
        valid_lines += 1
        listed.add(rel)
        artifact = package_dir / rel
        if not artifact.is_file():
            issues.append(_issue("RELEASE_PACKAGE_ARTIFACT_MISSING", f"checksum target missing: {rel}", item=rel))
            continue
        actual = _sha256_file(artifact)
        if actual != expected:
            issues.append(
                _issue(
                    "RELEASE_PACKAGE_CHECKSUM_MISMATCH",
                    f"{rel} expected {expected}, got {actual}",
                    item=rel,
                )
            )

    if valid_lines == 0:
        issues.append(
            _issue(
                "RELEASE_PACKAGE_CHECKSUMS_EMPTY",
                f"{path.name} has no valid checksum lines - an empty checksum file proves nothing",
                item=str(path),
            )
        )

    # Coverage cross-check: every package artifact that exists on disk must be
    # listed (the checksum file cannot contain its own hash, so it is exempt).
    for rel in expected_artifacts or []:
        if rel == path.name:
            continue
        if (package_dir / rel).is_file() and rel not in listed:
            issues.append(
                _issue(
                    "RELEASE_PACKAGE_CHECKSUM_COVERAGE_MISSING",
                    f"package artifact not covered by {path.name}: {rel}",
                    item=rel,
                )
            )
    return issues


def _validate_metadata(path: Path, manifest: dict[str, Any], package_dir: Path) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if not path.is_file():
        return [_issue("RELEASE_PACKAGE_METADATA_MISSING", f"package metadata not found: {path}", item=str(path))]
    data = load_yaml(path)
    if not isinstance(data, dict):
        return [_issue("RELEASE_PACKAGE_METADATA_INVALID", "package metadata must be a YAML mapping", item=str(path))]
    for field in ("release_manifest_hash", "release_bundle_hash", "semantic_contract_hash", "schema_bundle_hash"):
        if data.get(field) != manifest.get(field):
            issues.append(
                _issue(
                    "RELEASE_PACKAGE_METADATA_HASH_MISMATCH",
                    f"{field} expected {manifest.get(field)}, got {data.get(field)}",
                    item=field,
                )
            )
    artifacts = data.get("package_artifacts", [])
    if not isinstance(artifacts, list) or not artifacts:
        issues.append(_issue("RELEASE_PACKAGE_METADATA_ARTIFACTS_INVALID", "package_artifacts must be a non-empty list"))
    else:
        for rel in artifacts:
            if not (package_dir / str(rel)).is_file():
                issues.append(_issue("RELEASE_PACKAGE_ARTIFACT_MISSING", f"metadata artifact missing: {rel}", item=str(rel)))
    return issues


# Markers that identify the unpopulated release-notes TEMPLATE. A formal
# release package must ship the release's real notes: copying the template
# verbatim produced a package titled "ZMeta Release Notes Template", with every
# provenance field left as the literal placeholder and a closing "This template
# is an example", sitting beside metadata declaring release_state:
# formal_release (R1-11 verification pass 2 — the R11-10
# self-describes-as-non-formal shape, one artifact over).
_NOTES_TEMPLATE_MARKERS = (
    "explicit_release_input_required",
    "This template is an example",
    "# ZMeta Release Notes Template",
)


def _validate_release_notes(path: Path, metadata_path: Path) -> list[dict[str, str]]:
    """A formal_release package must not ship the notes template as its notes."""
    if not path.is_file():
        return [
            _issue(
                "RELEASE_PACKAGE_NOTES_MISSING",
                f"release notes not found: {path}",
                item=str(path),
            )
        ]
    if not metadata_path.is_file():
        return []
    try:
        metadata = load_yaml(metadata_path)
    except Exception:
        return []
    if not isinstance(metadata, dict):
        return []
    if str(metadata.get("release_state", "")).strip() != "formal_release":
        return []
    text = path.read_text(encoding="utf-8")
    found = [marker for marker in _NOTES_TEMPLATE_MARKERS if marker in text]
    if not found:
        return []
    return [
        _issue(
            "RELEASE_PACKAGE_NOTES_PLACEHOLDER",
            "formal_release package ships the unpopulated release-notes "
            f"template as RELEASE_NOTES.md (found {found[0]!r}); pass the "
            "release's real notes via build_release_package.py --release-notes",
            item=str(path),
        )
    ]


def validate_release_package(
    *,
    manifest_path: Path,
    package_dir: Path = DEFAULT_PACKAGE_DIR,
    templates_only: bool = False,
) -> list[dict[str, str]]:
    manifest, issues = _load_valid_manifest(manifest_path)
    issues.extend(validate_templates())
    if templates_only:
        return issues
    if manifest is None:
        return issues
    if not package_dir.is_dir():
        issues.append(_issue("RELEASE_PACKAGE_DIR_MISSING", f"package directory not found: {package_dir}", item=str(package_dir)))
        return issues
    issues.extend(scan_no_secrets([package_dir]))
    metadata_path = package_dir / "zmeta-release-package.yaml"
    issues.extend(_validate_metadata(metadata_path, manifest, package_dir))
    issues.extend(_validate_release_notes(package_dir / "RELEASE_NOTES.md", metadata_path))
    issues.extend(_validate_attestation(package_dir / "ATTESTATION.yaml", manifest))
    issues.extend(
        _validate_checksums(
            package_dir / "SHA256SUMS.txt",
            package_dir,
            _package_artifact_list(metadata_path),
        )
    )
    return issues


def run(
    manifest_path: Path | str = DEFAULT_MANIFEST,
    *,
    package_dir: Path | str = DEFAULT_PACKAGE_DIR,
    templates_only: bool = False,
    quiet: bool = False,
) -> int:
    issues = validate_release_package(
        manifest_path=Path(manifest_path),
        package_dir=Path(package_dir),
        templates_only=templates_only,
    )
    if issues:
        for issue in issues:
            item = f" item={issue['item']}" if "item" in issue else ""
            print(f"FAIL {issue['code']}{item}: {issue['message']}")
        return 1
    if not quiet:
        mode = "templates" if templates_only else "package"
        print(f"release package ok mode={mode}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate ZMeta release package templates or output.")
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST), help="Path to release manifest YAML.")
    parser.add_argument("--package-dir", default=str(DEFAULT_PACKAGE_DIR), help="Release package directory.")
    parser.add_argument("--templates-only", action="store_true", help="Validate release package templates only.")
    parser.add_argument("--quiet", action="store_true", help="Suppress success output.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    return run(
        args.manifest,
        package_dir=args.package_dir,
        templates_only=args.templates_only,
        quiet=args.quiet,
    )


if __name__ == "__main__":
    raise SystemExit(main())
