import hashlib
import importlib.util
import shutil
import uuid
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
SIGNING_PATH = ROOT / "release" / "sign_release_artifacts.py"
spec = importlib.util.spec_from_file_location("zmeta_release_signing", SIGNING_PATH)
signing = importlib.util.module_from_spec(spec)
spec.loader.exec_module(signing)

RELEASE_PACKAGE_PATH = ROOT / "tools" / "validate_release_package.py"
package_spec = importlib.util.spec_from_file_location(
    "zmeta_validate_release_package_signing_tests", RELEASE_PACKAGE_PATH
)
release_package = importlib.util.module_from_spec(package_spec)
package_spec.loader.exec_module(release_package)

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


def _write_artifacts(release_dir, version):
    for name in signing._artifact_names(version):
        (release_dir / name).write_text(f"{name}\n", encoding="utf-8")


def test_write_and_verify_checksums(release_tmp_dir):
    version = "v9.9.9"
    _write_artifacts(release_tmp_dir, version)

    checksum_path = signing.write_checksums(release_tmp_dir, version)

    assert checksum_path.name == "SHA256SUMS_v9.9.9.txt"
    failures = signing.verify_checksums(release_tmp_dir, version)
    assert failures == []


def test_verify_checksums_reports_mismatch(release_tmp_dir):
    version = "v9.9.9"
    _write_artifacts(release_tmp_dir, version)
    checksum_path = signing.write_checksums(release_tmp_dir, version)
    first_name = signing._artifact_names(version)[0]
    bad_hash = hashlib.sha256(b"bad\n").hexdigest()
    # Corrupt only the first entry's hash; keep every line so coverage stays
    # full and the single failure is exactly the mismatch.
    lines = checksum_path.read_text(encoding="utf-8").splitlines()
    lines[0] = f"{bad_hash}  {first_name}"
    checksum_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    failures = signing.verify_checksums(release_tmp_dir, version)

    assert len(failures) == 1
    assert first_name in failures[0]


def test_gpg_dry_run_prints_sign_commands(release_tmp_dir, capsys):
    path = release_tmp_dir / "artifact.zip"
    path.write_text("zip\n", encoding="utf-8")

    signing.sign_with_gpg([path], key_id="ABC123", dry_run=True)

    out = capsys.readouterr().out
    assert "gpg" in out.lower()
    assert "--yes --armor --detach-sign" in out
    assert "--local-user ABC123" in out
    assert "artifact.zip.asc" in out


def test_write_checksums_builds_missing_package_zip(release_tmp_dir):
    version = "v9.9.9"
    _write_artifacts(release_tmp_dir, version)
    package_zip = release_tmp_dir / f"zmeta-release-package-{version}.zip"
    package_zip.unlink()
    package_dir = release_tmp_dir / f"package-{version}"
    package_dir.mkdir()
    (package_dir / "release-package.json").write_text("{}\n", encoding="utf-8")

    signing.write_checksums(release_tmp_dir, version)

    assert package_zip.is_file()
    assert signing.verify_checksums(release_tmp_dir, version) == []


def test_write_checksums_never_overwrites_existing_package_zip(release_tmp_dir):
    version = "v9.9.9"
    _write_artifacts(release_tmp_dir, version)
    package_zip = release_tmp_dir / f"zmeta-release-package-{version}.zip"
    original = package_zip.read_bytes()
    package_dir = release_tmp_dir / f"package-{version}"
    package_dir.mkdir()
    (package_dir / "release-package.json").write_text("{}\n", encoding="utf-8")

    signing.write_checksums(release_tmp_dir, version)

    assert package_zip.read_bytes() == original


def test_write_checksums_uses_lf_line_endings(release_tmp_dir):
    version = "v9.9.9"
    _write_artifacts(release_tmp_dir, version)

    checksum_path = signing.write_checksums(release_tmp_dir, version)

    # Plain `sha256sum -c` on Linux requires LF-only checksum files.
    assert b"\r" not in checksum_path.read_bytes()


def test_verify_checksums_rejects_empty_checksum_file(release_tmp_dir):
    version = "v9.9.9"
    _write_artifacts(release_tmp_dir, version)
    checksum_path = signing.write_checksums(release_tmp_dir, version)
    checksum_path.write_text("", encoding="utf-8")

    failures = signing.verify_checksums(release_tmp_dir, version)

    assert failures
    assert any("no valid checksum lines" in failure for failure in failures)


def test_verify_checksums_rejects_partial_coverage(release_tmp_dir):
    version = "v9.9.9"
    _write_artifacts(release_tmp_dir, version)
    checksum_path = signing.write_checksums(release_tmp_dir, version)
    first_line = checksum_path.read_text(encoding="utf-8").splitlines()[0]
    checksum_path.write_text(first_line + "\n", encoding="utf-8")

    failures = signing.verify_checksums(release_tmp_dir, version)

    unlisted = [failure for failure in failures if "not listed" in failure]
    assert len(unlisted) == len(signing._artifact_names(version)) - 1


def test_verify_checksums_accepts_full_coverage(release_tmp_dir):
    version = "v9.9.9"
    _write_artifacts(release_tmp_dir, version)
    signing.write_checksums(release_tmp_dir, version)

    assert signing.verify_checksums(release_tmp_dir, version) == []


def _write_package_files(package_dir):
    (package_dir / "a.txt").write_text("a\n", encoding="utf-8")
    (package_dir / "b.txt").write_text("b\n", encoding="utf-8")
    artifacts = ["a.txt", "b.txt", "SHA256SUMS.txt"]
    lines = {
        name: f"{hashlib.sha256((package_dir / name).read_bytes()).hexdigest()}  {name}"
        for name in ("a.txt", "b.txt")
    }
    return artifacts, lines


def test_package_checksums_reject_empty_file(release_tmp_dir):
    artifacts, _lines = _write_package_files(release_tmp_dir)
    checksum_path = release_tmp_dir / "SHA256SUMS.txt"
    checksum_path.write_text("", encoding="utf-8")

    issues = release_package._validate_checksums(checksum_path, release_tmp_dir, artifacts)

    codes = [issue["code"] for issue in issues]
    assert "RELEASE_PACKAGE_CHECKSUMS_EMPTY" in codes


def test_package_checksums_require_coverage_of_artifact_list(release_tmp_dir):
    artifacts, lines = _write_package_files(release_tmp_dir)
    checksum_path = release_tmp_dir / "SHA256SUMS.txt"
    checksum_path.write_text(lines["a.txt"] + "\n", encoding="utf-8")

    issues = release_package._validate_checksums(checksum_path, release_tmp_dir, artifacts)

    codes = [issue["code"] for issue in issues]
    assert "RELEASE_PACKAGE_CHECKSUM_COVERAGE_MISSING" in codes
    assert any(issue.get("item") == "b.txt" for issue in issues)


def test_package_checksums_accept_full_coverage(release_tmp_dir):
    artifacts, lines = _write_package_files(release_tmp_dir)
    checksum_path = release_tmp_dir / "SHA256SUMS.txt"
    checksum_path.write_text(lines["a.txt"] + "\n" + lines["b.txt"] + "\n", encoding="utf-8")

    issues = release_package._validate_checksums(checksum_path, release_tmp_dir, artifacts)

    assert issues == []
