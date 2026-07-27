import hashlib
import importlib.util
import os
import shutil
import stat
import subprocess
import uuid
from pathlib import Path

import pytest
import yaml


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
        # ignore_errors alone leaks on Windows: a throwaway repo's .git
        # objects are read-only, rmtree stops at the first one, and the
        # residue lands inside the real working tree (attack-pass finding,
        # 2026-07-27). Clear the read-only bit first, then remove.
        for item in path.rglob("*"):
            try:
                os.chmod(item, stat.S_IWRITE)
            except OSError:
                pass
        shutil.rmtree(path, ignore_errors=True)
        try:
            TMP_ROOT.rmdir()
        except OSError:
            pass


def _write_artifacts(release_dir, version):
    for name in signing._artifact_names(version):
        (release_dir / name).write_text(f"{name}\n", encoding="utf-8")


def test_default_version_tag_derives_from_release_manifest():
    # No stale hardcoded default: the version tag must come from the release
    # manifest's release_id (zmeta-vX.Y.Z -> vX.Y.Z), same pattern as
    # release/build_mvp_packages.py default_version_tag().
    manifest = yaml.safe_load(
        (ROOT / "release" / "zmeta-release-manifest.yaml").read_text(encoding="utf-8")
    )
    release_id = str(manifest["release_id"])
    assert release_id.startswith("zmeta-v")
    assert signing.default_version_tag() == release_id[len("zmeta-"):]


def test_default_version_tag_strips_zmeta_prefix(release_tmp_dir, monkeypatch):
    path = release_tmp_dir / "zmeta-release-manifest.yaml"
    path.write_text("release_id: zmeta-v9.9.9\n", encoding="utf-8")
    monkeypatch.setattr(signing, "MANIFEST_PATH", path)
    assert signing.default_version_tag() == "v9.9.9"


def test_default_version_tag_missing_manifest_returns_none(release_tmp_dir, monkeypatch):
    monkeypatch.setattr(signing, "MANIFEST_PATH", release_tmp_dir / "missing.yaml")
    assert signing.default_version_tag() is None


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


def test_write_checksums_refuses_to_rewrite_a_published_release(release_tmp_dir, monkeypatch):
    # R1-11 A-23: write_checksums opened SHA256SUMS_<version>.txt in "w"
    # with no existence check, and --version defaults to the manifest
    # release_id - which in the post-release window is the ALREADY
    # PUBLISHED version. A bare `--write-checksums` therefore rewrote a
    # published, immutable record (AGENTS.md release limits) and nothing in
    # the tool refused. "Published" is the release tag, the same definition
    # test_published_checksums_immutable.py uses.
    version = "v9.9.9"
    _write_artifacts(release_tmp_dir, version)
    monkeypatch.setattr(signing, "_published_release_tags", lambda: set())
    published = signing.write_checksums(release_tmp_dir, version)
    original = published.read_bytes()

    monkeypatch.setattr(signing, "_published_release_tags", lambda: {version})
    with pytest.raises(SystemExit) as excinfo:
        signing.write_checksums(release_tmp_dir, version)

    assert "already published" in str(excinfo.value)
    assert published.read_bytes() == original


def test_write_checksums_allows_regeneration_before_the_release_is_tagged(
    release_tmp_dir, monkeypatch
):
    # The guard must not obstruct the cut it protects. RELEASE_CHECKLIST.md
    # writes checksums BEFORE the tag is created, and a cut legitimately
    # regenerates them after rebuilding an asset.
    version = "v9.9.9"
    _write_artifacts(release_tmp_dir, version)
    monkeypatch.setattr(signing, "_published_release_tags", lambda: {"v1.1.16"})
    first = signing.write_checksums(release_tmp_dir, version)
    (release_tmp_dir / signing._artifact_names(version)[0]).write_text(
        "rebuilt\n", encoding="utf-8"
    )

    second = signing.write_checksums(release_tmp_dir, version)

    assert second == first
    assert signing.verify_checksums(release_tmp_dir, version) == []


def test_write_checksums_announces_unknown_publication_state(release_tmp_dir, monkeypatch, capsys):
    # Honest degradation: in a tagless/shallow checkout the tool cannot
    # tell whether the version is published. It proceeds - refusing would
    # break out-of-tree use - but it says so rather than letting an
    # unverifiable state read as verified.
    version = "v9.9.9"
    _write_artifacts(release_tmp_dir, version)
    monkeypatch.setattr(signing, "_published_release_tags", lambda: set())
    signing.write_checksums(release_tmp_dir, version)
    capsys.readouterr()

    monkeypatch.setattr(signing, "_published_release_tags", lambda: None)
    signing.write_checksums(release_tmp_dir, version)

    out = capsys.readouterr().out
    assert "cannot determine whether v9.9.9 is already published" in out


def _git(cwd, *args):
    return subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, check=True)


def test_published_release_tags_reads_real_git_tags(release_tmp_dir, monkeypatch):
    # Non-vacuity: the guard is only as good as this lookup. If it silently
    # returned an empty set, every guard test above would still pass while
    # the shipped guard never fired. The original pin asserted v1.1.16 is
    # visible in THIS repository, which fails honestly-empty in a shallow or
    # tagless checkout (default CI fetch-depth 1) where `git tag -l v*`
    # legitimately returns nothing (CR-12). A throwaway repo carrying known
    # tags exercises the same lookup with an EXACT expectation, identically
    # in full and tagless checkouts.
    if shutil.which("git") is None:
        pytest.skip("git executable not available")
    repo = release_tmp_dir / "tagged-repo"
    repo.mkdir()
    _git(repo, "init", "--quiet")
    # Hermetic identity/signing config for the throwaway repo only, so a
    # host-level gpgsign default cannot fail the fixture commit or tags.
    _git(repo, "config", "user.name", "zmeta-tests")
    _git(repo, "config", "user.email", "zmeta-tests@localhost")
    _git(repo, "config", "commit.gpgsign", "false")
    _git(repo, "config", "tag.gpgSign", "false")
    (repo / "seed.txt").write_text("seed\n", encoding="utf-8")
    _git(repo, "add", "seed.txt")
    _git(repo, "commit", "--quiet", "-m", "seed")
    _git(repo, "tag", "v1.1.16")
    _git(repo, "tag", "v9.9.9")
    # A non-v* tag must NOT count: the guard's definition of "published"
    # is the v-prefixed release tag, nothing else.
    _git(repo, "tag", "checkpoint-1")
    monkeypatch.setattr(signing, "ROOT", repo)

    assert signing._published_release_tags() == {"v1.1.16", "v9.9.9"}


def test_published_release_tags_agrees_with_this_repository():
    # The temp-repo pin above proves the lookup reads tags; this one proves
    # the shipped ROOT points at THIS repository, by asking git the same
    # question independently and requiring agreement. In a shallow/tagless
    # checkout both sides are legitimately empty and the agreement still
    # holds - meaningful in every checkout shape, no skip, no false red.
    tags = signing._published_release_tags()

    if shutil.which("git") is None:
        assert tags is None
        return
    result = subprocess.run(
        ["git", "tag", "-l", "v*"],
        cwd=str(signing.ROOT),
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        assert tags is None
        return
    expected = set(result.stdout.decode("utf-8", "replace").split())
    assert tags == expected


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
