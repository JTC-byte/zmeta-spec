import importlib.util
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[2]
BUILDER_PATH = ROOT / "tools" / "build_release_manifest.py"
VALIDATOR_PATH = ROOT / "tools" / "validate_release_manifest.py"
MANIFEST_PATH = ROOT / "release" / "zmeta-release-manifest.yaml"
TMP_ROOT = ROOT / "pytest-work"

builder_spec = importlib.util.spec_from_file_location("zmeta_build_release_manifest", BUILDER_PATH)
builder = importlib.util.module_from_spec(builder_spec)
builder_spec.loader.exec_module(builder)

validator_spec = importlib.util.spec_from_file_location("zmeta_validate_release_manifest", VALIDATOR_PATH)
validator = importlib.util.module_from_spec(validator_spec)
validator_spec.loader.exec_module(validator)


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


def _manifest_copy(release_tmp_dir, mutate):
    data = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
    mutate(data)
    path = release_tmp_dir / "manifest.yaml"
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


def _codes(issues):
    return {issue["code"] for issue in issues}


def test_release_manifest_exists():
    assert MANIFEST_PATH.is_file()


def test_release_manifest_yaml_loads():
    data = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    assert data["release_id"] == "zmeta-v1.1.16"
    assert data["release_status"] == "formal_release"
    assert data["release_date"] == "2026-07-21"


def test_required_top_level_fields_exist():
    data = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
    missing = validator.REQUIRED_TOP_LEVEL - set(data)
    assert missing == set()


def test_required_artifact_groups_exist():
    data = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
    missing = validator.REQUIRED_GROUPS - set(data["artifact_groups"])
    assert missing == set()


def test_builder_produces_deterministic_manifest():
    first = builder.build_manifest_data(git_commit="test-commit", branch="test-branch")
    second = builder.build_manifest_data(git_commit="test-commit", branch="test-branch")
    assert first["release_bundle_hash"] == second["release_bundle_hash"]
    assert first["release_manifest_hash"] == second["release_manifest_hash"]


def test_builder_uses_stable_reference_metadata_by_default():
    manifest = builder.build_manifest_data()

    assert manifest["git_commit"] == builder.DEFAULT_RELEASE_METADATA
    assert manifest["branch"] == builder.DEFAULT_RELEASE_METADATA


def test_validator_passes_current_manifest():
    assert validator.validate_manifest(MANIFEST_PATH) == []


def test_formal_manifest_state_is_coherent():
    # R1-11 R11-10/R11-14: the shipped formal manifest must not
    # self-describe as non-formal, must carry a real branch, and must not
    # assert stale deferred-register state (the register closed 2026-07-08;
    # reopened issues enter via --known-open-issue, never a hardcode).
    data = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert data["release_status"] == "formal_release"
    assert data["branch"] != builder.DEFAULT_RELEASE_METADATA
    assert "not a formal tagged release" not in " ".join(data["notes"])
    assert data["known_open_issues"] == []


def test_formal_manifest_with_placeholder_branch_fails(release_tmp_dir):
    def mutate(data):
        data["branch"] = builder.DEFAULT_RELEASE_METADATA

    path = _manifest_copy(release_tmp_dir, mutate)
    assert "RELEASE_MANIFEST_FORMAL_PROVENANCE_MISSING" in _codes(
        validator.validate_manifest(path)
    )


def test_formal_manifest_with_non_formal_note_fails(release_tmp_dir):
    def mutate(data):
        data["notes"] = [
            "Reference hardening-baseline manifest, not a formal tagged release."
        ]

    path = _manifest_copy(release_tmp_dir, mutate)
    assert "RELEASE_MANIFEST_FORMAL_STATUS_CONTRADICTED" in _codes(
        validator.validate_manifest(path)
    )


def test_missing_artifact_fails(release_tmp_dir):
    def mutate(data):
        old_path = data["artifact_groups"]["semantic_contract"]["paths"][0]
        data["artifact_groups"]["semantic_contract"]["paths"][0] = "missing/artifact.md"
        for artifact in data["artifact_hashes"]:
            if artifact["path"] == old_path:
                artifact["path"] = "missing/artifact.md"

    path = _manifest_copy(release_tmp_dir, mutate)
    assert "RELEASE_MANIFEST_ARTIFACT_MISSING" in _codes(validator.validate_manifest(path))


def test_modified_artifact_hash_mismatch_fails(release_tmp_dir):
    def mutate(data):
        data["artifact_hashes"][0]["hash"] = "sha256:" + ("0" * 64)

    path = _manifest_copy(release_tmp_dir, mutate)
    assert "RELEASE_MANIFEST_ARTIFACT_HASH_MISMATCH" in _codes(validator.validate_manifest(path))


def test_group_hash_mismatch_fails(release_tmp_dir):
    def mutate(data):
        data["artifact_groups"]["schema_bundle"]["hash"] = "sha256:" + ("1" * 64)

    path = _manifest_copy(release_tmp_dir, mutate)
    assert "RELEASE_MANIFEST_GROUP_HASH_MISMATCH" in _codes(validator.validate_manifest(path))


def test_release_bundle_hash_mismatch_fails(release_tmp_dir):
    def mutate(data):
        data["release_bundle_hash"] = "sha256:" + ("2" * 64)

    path = _manifest_copy(release_tmp_dir, mutate)
    assert "RELEASE_MANIFEST_BUNDLE_HASH_MISMATCH" in _codes(validator.validate_manifest(path))


def test_release_manifest_hash_mismatch_fails(release_tmp_dir):
    def mutate(data):
        data["release_manifest_hash"] = "sha256:" + ("3" * 64)

    path = _manifest_copy(release_tmp_dir, mutate)
    assert "RELEASE_MANIFEST_SELF_HASH_MISMATCH" in _codes(validator.validate_manifest(path))


def test_file_ordering_does_not_change_group_hash(release_tmp_dir):
    (release_tmp_dir / "a.txt").write_text("a\n", encoding="utf-8")
    (release_tmp_dir / "b.txt").write_text("b\n", encoding="utf-8")

    first = builder.group_hash(["b.txt", "a.txt"], release_tmp_dir)
    second = builder.group_hash(["a.txt", "b.txt"], release_tmp_dir)

    assert first == second


def test_lf_normalization_behavior_is_deterministic(release_tmp_dir):
    crlf = release_tmp_dir / "crlf.txt"
    lf = release_tmp_dir / "lf.txt"
    crlf.write_bytes(b"line1\r\nline2\r\n")
    lf.write_bytes(b"line1\nline2\n")

    assert builder.file_hash("crlf.txt", release_tmp_dir) == builder.file_hash("lf.txt", release_tmp_dir)


def test_default_strict_conformance_unchanged():
    result = subprocess.run(
        [sys.executable, "tools/validate_conformance.py", "--strict"],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "conformance ok" in result.stdout


def test_optional_release_manifest_conformance_flag_passes():
    result = subprocess.run(
        [sys.executable, "tools/validate_conformance.py", "--strict", "--release-manifest"],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "conformance ok" in result.stdout
