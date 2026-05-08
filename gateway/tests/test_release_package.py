import importlib.util
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[2]


def _load_tool(name, rel_path):
    path = ROOT / rel_path
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


builder = _load_tool("zmeta_build_release_package", "tools/build_release_package.py")
validator = _load_tool("zmeta_validate_release_package", "tools/validate_release_package.py")
TMP_ROOT = ROOT / "pytest-work"


@pytest.fixture
def release_tmp_dir():
    path = TMP_ROOT / uuid.uuid4().hex
    path.mkdir(parents=True)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)
        try:
            TMP_ROOT.rmdir()
        except OSError:
            pass


def _build_temp_package(tmp_path):
    output_dir = tmp_path / "package"
    builder.build_package(
        manifest_path=ROOT / "release" / "zmeta-release-manifest.yaml",
        output_dir=output_dir,
        no_signatures=True,
        allow_dirty=True,
    )
    return output_dir


def _refresh_checksums(package_dir):
    targets = [
        package_dir / "zmeta-release-package.yaml",
        package_dir / "RELEASE_NOTES.md",
        package_dir / "ATTESTATION.yaml",
    ]
    lines = []
    for path in targets:
        if path.is_file():
            lines.append(f"{validator._sha256_file(path)}  {path.name}")
    (package_dir / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _issue_codes(issues):
    return {issue["code"] for issue in issues}


def test_release_package_templates_exist():
    expected = [
        ROOT / "spec" / "release-signing-attestation.md",
        ROOT / "release" / "RELEASE_NOTES_TEMPLATE.md",
        ROOT / "release" / "ATTESTATION_TEMPLATE.yaml",
        ROOT / "release" / "RELEASE_PACKAGE_README.md",
    ]

    assert all(path.is_file() for path in expected)


def test_release_package_templates_validate():
    assert validator.run(ROOT / "release" / "zmeta-release-manifest.yaml", templates_only=True, quiet=True) == 0


def test_release_package_builder_dry_run_succeeds(release_tmp_dir):
    result = builder.build_package(
        manifest_path=ROOT / "release" / "zmeta-release-manifest.yaml",
        output_dir=release_tmp_dir / "package",
        no_signatures=True,
        dry_run=True,
    )

    assert result["dry_run"] is True
    assert "ATTESTATION.yaml" in result["planned_files"]


def test_release_package_output_validates(release_tmp_dir):
    package_dir = _build_temp_package(release_tmp_dir)

    issues = validator.validate_release_package(
        manifest_path=ROOT / "release" / "zmeta-release-manifest.yaml",
        package_dir=package_dir,
    )

    assert issues == []


def test_no_secret_scanner_rejects_private_key_like_content(release_tmp_dir):
    package_dir = release_tmp_dir / "package"
    package_dir.mkdir()
    private_key_marker = "-----BEGIN " + "PRIVATE KEY-----\n"
    (package_dir / "safe.txt").write_text(private_key_marker, encoding="utf-8")

    issues = validator.scan_no_secrets([package_dir])

    assert "RELEASE_PACKAGE_SECRET_CONTENT" in _issue_codes(issues)


def test_no_secret_scanner_rejects_secret_like_filename(release_tmp_dir):
    package_dir = release_tmp_dir / "package"
    package_dir.mkdir()
    (package_dir / "release-token.txt").write_text("placeholder\n", encoding="utf-8")

    issues = validator.scan_no_secrets([package_dir])

    assert "RELEASE_PACKAGE_SECRET_FILENAME" in _issue_codes(issues)


def test_checksum_mismatch_fails(release_tmp_dir):
    package_dir = _build_temp_package(release_tmp_dir)
    (package_dir / "RELEASE_NOTES.md").write_text("tampered\n", encoding="utf-8")

    issues = validator.validate_release_package(
        manifest_path=ROOT / "release" / "zmeta-release-manifest.yaml",
        package_dir=package_dir,
    )

    assert "RELEASE_PACKAGE_CHECKSUM_MISMATCH" in _issue_codes(issues)


def test_attestation_hash_mismatch_fails(release_tmp_dir):
    package_dir = _build_temp_package(release_tmp_dir)
    attestation_path = package_dir / "ATTESTATION.yaml"
    data = yaml.safe_load(attestation_path.read_text(encoding="utf-8"))
    data["semantic_contract_hash"] = "sha256:" + "0" * 64
    attestation_path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    _refresh_checksums(package_dir)

    issues = validator.validate_release_package(
        manifest_path=ROOT / "release" / "zmeta-release-manifest.yaml",
        package_dir=package_dir,
    )

    assert "RELEASE_PACKAGE_ATTESTATION_HASH_MISMATCH" in _issue_codes(issues)


def test_missing_package_artifact_fails(release_tmp_dir):
    package_dir = _build_temp_package(release_tmp_dir)
    (package_dir / "RELEASE_NOTES.md").unlink()

    issues = validator.validate_release_package(
        manifest_path=ROOT / "release" / "zmeta-release-manifest.yaml",
        package_dir=package_dir,
    )

    assert "RELEASE_PACKAGE_ARTIFACT_MISSING" in _issue_codes(issues)


def test_release_package_conformance_flag_succeeds():
    result = subprocess.run(
        [sys.executable, "tools/validate_conformance.py", "--strict", "--release-package"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "conformance ok" in result.stdout


def test_default_strict_conformance_unchanged():
    result = subprocess.run(
        [sys.executable, "tools/validate_conformance.py", "--strict"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "conformance ok" in result.stdout
