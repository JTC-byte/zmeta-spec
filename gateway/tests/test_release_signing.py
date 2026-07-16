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
    expected = hashlib.sha256(b"bad\n").hexdigest()
    checksum_path.write_text(f"{expected}  {first_name}\n", encoding="utf-8")

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
