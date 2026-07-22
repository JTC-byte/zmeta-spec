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
manifest_builder = _load_tool(
    "zmeta_build_release_manifest_pkg_tests", "tools/build_release_manifest.py"
)
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


def test_formal_release_shipping_the_notes_template_fails(release_tmp_dir):
    # R1-11 verification pass 2: the builder copied RELEASE_NOTES_TEMPLATE.md
    # verbatim, so every formal package shipped notes titled "ZMeta Release
    # Notes Template" with placeholder provenance and a closing "This template
    # is an example" - beside metadata declaring release_state: formal_release.
    # Nothing read the file's content, so four releases shipped that way.
    package_dir = _build_temp_package(release_tmp_dir)
    metadata_path = package_dir / "zmeta-release-package.yaml"
    metadata = yaml.safe_load(metadata_path.read_text(encoding="utf-8"))
    metadata["release_state"] = "formal_release"
    metadata_path.write_text(yaml.safe_dump(metadata, sort_keys=False), encoding="utf-8")
    _refresh_checksums(package_dir)

    issues = validator.validate_release_package(
        manifest_path=ROOT / "release" / "zmeta-release-manifest.yaml",
        package_dir=package_dir,
    )

    assert "RELEASE_PACKAGE_NOTES_PLACEHOLDER" in _issue_codes(issues)


def test_formal_release_with_real_notes_passes(release_tmp_dir):
    # The other direction: real notes in a formal package must be accepted,
    # and a release_candidate may legitimately still carry the template.
    package_dir = _build_temp_package(release_tmp_dir)
    metadata_path = package_dir / "zmeta-release-package.yaml"
    metadata = yaml.safe_load(metadata_path.read_text(encoding="utf-8"))
    metadata["release_state"] = "formal_release"
    metadata_path.write_text(yaml.safe_dump(metadata, sort_keys=False), encoding="utf-8")
    (package_dir / "RELEASE_NOTES.md").write_text(
        "# ZMeta v1.1.16\n\nReal release notes for this cut.\n", encoding="utf-8"
    )
    _refresh_checksums(package_dir)

    issues = validator.validate_release_package(
        manifest_path=ROOT / "release" / "zmeta-release-manifest.yaml",
        package_dir=package_dir,
    )

    assert "RELEASE_PACKAGE_NOTES_PLACEHOLDER" not in _issue_codes(issues)


def test_builder_release_notes_option_ships_real_notes(release_tmp_dir):
    real_notes = release_tmp_dir / "REAL_NOTES.md"
    real_notes.write_text("# ZMeta v1.1.16\n\nReal notes.\n", encoding="utf-8")
    output_dir = release_tmp_dir / "package-real"
    builder.build_package(
        manifest_path=ROOT / "release" / "zmeta-release-manifest.yaml",
        output_dir=output_dir,
        release_notes=real_notes,
        no_signatures=True,
        allow_dirty=True,
    )

    shipped = (output_dir / "RELEASE_NOTES.md").read_text(encoding="utf-8")
    assert "Real notes." in shipped
    assert "explicit_release_input_required" not in shipped


def test_missing_package_artifact_fails(release_tmp_dir):
    package_dir = _build_temp_package(release_tmp_dir)
    (package_dir / "RELEASE_NOTES.md").unlink()

    issues = validator.validate_release_package(
        manifest_path=ROOT / "release" / "zmeta-release-manifest.yaml",
        package_dir=package_dir,
    )

    assert "RELEASE_PACKAGE_ARTIFACT_MISSING" in _issue_codes(issues)


def _current_manifest(tmp_path):
    """A manifest built from the tree as it stands right now.

    The committed manifest is regenerated at cut time, so between a source
    edit and that regeneration it does not match the tree and the package
    builder refuses to run against it. These integrity checks must stay
    executable in that window - a pin that cannot run is not a pin.
    """
    data = manifest_builder.build_manifest_data()
    path = tmp_path / "current-manifest.yaml"
    path.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=False, width=1000),
        encoding="utf-8",
    )
    return path


def test_package_metadata_verifies_every_hash_it_carries(release_tmp_dir):
    # R1-11 A-19: _validate_metadata compared a literal 4-tuple while the
    # builder wrote seven hashes, so policy_bundle_hash,
    # extension_registry_hash and conformance_class_manifest_hash were
    # unverified claims in the file a consumer is most likely to read
    # alone. _validate_checksums cannot catch it: it only proves the file
    # matches its OWN listed digest, so a wrong value stays self-consistent
    # once the checksum file is regenerated - which is exactly what this
    # test does before validating.
    #
    # Every field the builder writes is mutated in turn: an oracle that
    # only checked one field would pass a partial fix.
    manifest_path = _current_manifest(release_tmp_dir)
    package_dir = release_tmp_dir / "package"
    builder.build_package(
        manifest_path=manifest_path,
        output_dir=package_dir,
        no_signatures=True,
        allow_dirty=True,
    )
    metadata_path = package_dir / "zmeta-release-package.yaml"
    clean = metadata_path.read_text(encoding="utf-8")

    assert validator.validate_release_package(
        manifest_path=manifest_path, package_dir=package_dir
    ) == []
    # Both directions of the writer/checker relationship, so the drift that
    # produced A-19 cannot recur silently: every declared field is written,
    # and every hash written is declared (hence compared below).
    written = yaml.safe_load(clean)
    assert set(builder.METADATA_HASH_FIELDS) <= set(written)
    assert {key for key in written if key.endswith("_hash")} == set(
        builder.METADATA_HASH_FIELDS
    )

    for field in builder.METADATA_HASH_FIELDS:
        data = yaml.safe_load(clean)
        data[field] = "sha256:" + "0" * 64
        metadata_path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
        _refresh_checksums(package_dir)

        issues = validator.validate_release_package(
            manifest_path=manifest_path, package_dir=package_dir
        )
        flagged = {
            issue.get("item")
            for issue in issues
            if issue["code"] == "RELEASE_PACKAGE_METADATA_HASH_MISMATCH"
        }
        assert field in flagged, f"{field} misdescribed and reported clean: {issues}"

    metadata_path.write_text(clean, encoding="utf-8")


def test_attestation_open_issue_mismatch_fails(release_tmp_dir):
    # R1-11 A-27: the mirror check's negative branch was unexercised - the
    # templates_only path returns before _validate_attestation, and the one
    # test that reached it built the attestation from the same manifest, so
    # the comparison was tautological.
    manifest_path = _current_manifest(release_tmp_dir)
    package_dir = release_tmp_dir / "package"
    builder.build_package(
        manifest_path=manifest_path,
        output_dir=package_dir,
        no_signatures=True,
        allow_dirty=True,
    )
    attestation_path = package_dir / "ATTESTATION.yaml"
    data = yaml.safe_load(attestation_path.read_text(encoding="utf-8"))
    assert data["known_open_issues"] == []
    data["known_open_issues"] = ["D-003 OPEN"]
    attestation_path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    _refresh_checksums(package_dir)

    issues = validator.validate_release_package(
        manifest_path=manifest_path, package_dir=package_dir
    )

    assert "RELEASE_PACKAGE_ATTESTATION_OPEN_ISSUE_MISMATCH" in _issue_codes(issues)


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
