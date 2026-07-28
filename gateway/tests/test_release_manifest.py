import importlib.util
import re
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
    assert data["release_id"] == "zmeta-v1.1.19"
    assert data["release_status"] == "formal_release"
    assert data["release_date"] == "2026-07-27"


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


def _write_built_manifest(release_tmp_dir, name, **kwargs):
    """Write a freshly BUILT manifest, so the file hashes are current.

    These cases must exercise the builder's own defaults end to end, not a
    mutated copy of the committed manifest: A-09 was a defaulting bug, and
    a hand-mutated copy would not have shown it.
    """
    data = builder.build_manifest_data(**kwargs)
    path = release_tmp_dir / name
    path.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=False, width=1000),
        encoding="utf-8",
    )
    return path


def _identity_items(issues):
    return {
        issue.get("item")
        for issue in issues
        if issue["code"] == "RELEASE_MANIFEST_FORMAL_IDENTITY_INVALID"
    }


def test_formal_manifest_with_reference_baseline_identity_fails(release_tmp_dir):
    # R1-11 A-09: `--release-status formal_release --branch main` with the
    # identity flags omitted built a governed, hash-pinned manifest that
    # called itself the reference hardening baseline, dated 2026-05-07, and
    # validated with ZERO issues - while spec/release-hash-policy.md:181-183
    # told the maintainer this validator refuses exactly that. The branch
    # half was enforced; the identity half was not.
    #
    # All three fields are asserted individually: a partial implementation
    # that checks only release_id passes a bare "some issue was raised"
    # oracle.
    path = _write_built_manifest(
        release_tmp_dir,
        "formal-default-identity.yaml",
        release_status="formal_release",
        branch="main",
    )
    issues = validator.validate_manifest(path)

    assert "RELEASE_MANIFEST_FORMAL_PROVENANCE_MISSING" not in _codes(issues)
    assert _identity_items(issues) == {"release_id", "release_name", "release_date"}


def test_formal_manifest_with_explicit_identity_passes(release_tmp_dir):
    # The other direction: a real cut must validate clean. Without this the
    # check above could be satisfied by refusing every formal manifest.
    path = _write_built_manifest(
        release_tmp_dir,
        "formal-real-identity.yaml",
        release_id="zmeta-v9.9.9",
        release_name="ZMeta v9.9.9",
        release_status="formal_release",
        release_date="2026-07-22",
        branch="main",
    )

    assert validator.validate_manifest(path) == []


def test_reference_baseline_manifest_keeps_its_default_identity(release_tmp_dir):
    # False-positive guard: the baseline identity is CORRECT for a
    # non-formal reference manifest, which is what the builder writes by
    # default and what the repo committed for most of its history.
    path = _write_built_manifest(release_tmp_dir, "reference-baseline.yaml")

    assert validator.validate_manifest(path) == []


def test_builder_known_open_issues_are_explicit_only(release_tmp_dir):
    # R1-11 A-27: the R11-14 fix (stop hardcoding "D-003 OPEN") had no
    # direct test - only an assertion on the committed manifest, which a
    # regeneration also rewrites.
    assert builder.build_manifest_data()["known_open_issues"] == []
    assert builder.build_manifest_data(known_open_issues=["D-999"])[
        "known_open_issues"
    ] == ["D-999"]


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


# ---------------------------------------------------------------------------
# PC-08 (v1.1.19 pre-cut review): the manifest hashed twelve export/policy
# artifacts as part of the release while NEITHER bundle builder copied the
# directory, so every downloadable artifact omitted files the manifest
# declared shipped -- and a consumer who took a bundle could not verify them
# against the manifest because they were not there.
#
# The instance was `export/`, added the same day. The class is older and is
# the one this pins: a green kernel gate says nothing about the packaging
# layer, which is exactly how the release-package `templates_only` gap
# survived earlier in this cycle. Static check on the builders' own path
# lists rather than a build, so it stays a unit test.
# ---------------------------------------------------------------------------


def _hashed_artifact_roots() -> set[str]:
    """Top-level directories the release manifest claims are part of the release."""
    manifest = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
    roots = set()
    for entry in manifest["artifact_hashes"]:
        head = entry["path"].split("/")[0]
        if "." not in head:  # a directory, not a top-level file
            roots.add(head)
    return roots


def _mvp_common_paths() -> set[str]:
    text = (ROOT / "release" / "build_mvp_packages.py").read_text(encoding="utf-8")
    block = re.search(r"COMMON_PATHS\s*=\s*\[(.*?)\]", text, re.DOTALL)
    assert block, "release/build_mvp_packages.py COMMON_PATHS not found"
    return {item.split("/")[0] for item in re.findall(r'"([^"]+)"', block.group(1))}


def _dist_bundle_roots() -> set[str]:
    text = (ROOT / "release" / "build_release_bundle.py").read_text(encoding="utf-8")
    trees = set(re.findall(r'copy_tree\(root / "([^"]+)"', text))
    files = {item.split("/")[0] for item in re.findall(r'root / "([^"]+)"', text)}
    return trees | files


# PC-09, found by the pin below and DEFERRED rather than fixed inside a cut.
# The edge/gateway bundles omit `docs/`, which the manifest hashes for two
# governance files (`zmeta_change_governance.md`,
# `zmeta_defensive_publication.md`) -- and README.md tells downstream clone
# users to read both before altering schema or policy. So a bundle directs its
# reader to files it does not contain.
#
# Not fixed here because the fix is a judgement, not a mechanism: adding
# `docs` wholesale would drag the entire process-record archive into a runtime
# deployment package, so the real question is which governance files belong in
# a deployment bundle at all -- which also covers the top-level AGENTS.md,
# CONFORMANCE.md, IP_POLICY.md and TRADEMARK.md, hashed and equally absent.
# Maintainer scope call, recorded in the handoff.
#
# Listed here rather than dropped from the check so the guard still catches a
# NEW omission, which is the regression this exists for.
_MVP_KNOWN_OMISSIONS = {"docs"}

# The dist zip enumerates files individually and carries neither the
# conformance corpus nor the governance docs, both hashed. Same PC-09
# question, same reason for not answering it inside a cut.
_DIST_KNOWN_OMISSIONS = {"docs", "conformance"}


def test_release_bundles_carry_every_hashed_artifact_root():
    hashed = _hashed_artifact_roots()
    assert hashed, "no hashed artifact roots found; this check would be vacuous"

    mvp_missing = sorted(hashed - _mvp_common_paths() - _MVP_KNOWN_OMISSIONS)
    assert mvp_missing == [], (
        f"release/build_mvp_packages.py COMMON_PATHS omits {mvp_missing}, which the "
        f"release manifest hashes as part of the release. The edge and gateway bundles "
        f"would ship without files the manifest declares shipped."
    )
    assert _MVP_KNOWN_OMISSIONS <= hashed, (
        f"a documented MVP omission is no longer a hashed artifact root; prune "
        f"_MVP_KNOWN_OMISSIONS so it cannot silence a real finding"
    )

    dist_missing = sorted(hashed - _dist_bundle_roots() - _DIST_KNOWN_OMISSIONS)
    assert dist_missing == [], (
        f"release/build_release_bundle.py omits {dist_missing}, which the release "
        f"manifest hashes as part of the release; the dist zip would not carry them."
    )
    assert _DIST_KNOWN_OMISSIONS <= hashed, (
        "a documented dist omission is no longer a hashed artifact root; prune "
        "_DIST_KNOWN_OMISSIONS so it cannot silence a real finding"
    )


def test_bundle_coverage_pin_notices_a_dropped_root():
    """Red demonstration: the pin must fail when a builder drops a hashed root.

    Discipline 5 as amended -- the proof that this catches the PC-08 shape
    lives here and re-runs, rather than being a claim in a commit message.
    """
    hashed = _hashed_artifact_roots()
    dropped = "export"
    assert dropped in hashed, (
        f"{dropped!r} is no longer a hashed artifact root; pick another root for this "
        f"demonstration or it proves nothing"
    )
    crippled = _mvp_common_paths() - {dropped}
    assert sorted(hashed - crippled - _MVP_KNOWN_OMISSIONS) == [dropped], (
        "removing a hashed root from the builder's path set was not detected as missing"
    )
