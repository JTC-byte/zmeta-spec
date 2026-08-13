"""A release is not complete until it ships its whole tracked artifact set.

Why this exists. `v1.1.19` was prepared, manifest-validated, package-validated,
battery-green and CI-green with `RELEASE_NOTES_v1.1.19.md` present but
`VALIDATION_REPORT_v1.1.19.md` and `SHA256SUMS_v1.1.19.txt` absent entirely.
Nothing noticed. The handoff meanwhile asserted that only tag, sign and upload
remained, which was written by an earlier session and never re-derived.

The completeness rule existed only as manual checkboxes in
`RELEASE_CHECKLIST.md`, so it was a claim about process rather than a check on
the tree. Prose that enumerates a required set and is read by no test is the
recurring shape this cycle kept hitting: when a claim enumerates, generate it.

Scope note, deliberately narrow. The trio convention starts at `v1.1.0`.
Earlier tags predate it: `v1.0.2`/`v1.0.3` ship no checksums, and no `v1.0.x`
ships a validation report. Asserting the convention over those would fail on
history that is correct as published, so the baseline is explicit rather than
implied.

Known limit, recorded rather than engineered around: this checks the working
tree, so an artifact that exists but is gitignored would satisfy it and still
never ship. Verified once by hand at authoring time that neither
`release/VALIDATION_REPORT_v*.md` nor `release/SHA256SUMS_v*.txt` matches an
ignore rule (`release/` ignores cover only `*.zip`, `bundles/`, `package*/` and
`smoke-*/`). Re-implementing gitignore semantics here would cost more than the
hole is worth.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[2]
RELEASE_DIR = ROOT / "release"
MANIFEST_PATH = RELEASE_DIR / "zmeta-release-manifest.yaml"

# The convention's first release. See the scope note above.
CONVENTION_BASELINE = (1, 1, 0)

# Every per-version artifact a release is required to track, as a format
# template. Generated from here rather than restated in prose anywhere else.
REQUIRED_TEMPLATES = (
    "RELEASE_NOTES_{version}.md",
    "VALIDATION_REPORT_{version}.md",
    "SHA256SUMS_{version}.txt",
)

# Signing continuity (doctrine pressure log X2-02). Sixteen releases shipped
# checksums-only citing a decision that was never made, and the regression
# from seven detached signatures to zero at v1.1.5 was invisible to every
# gate. Signed releases must track the text-artifact signature trio, so a
# release that silently drops them fails here. Two signed regimes exist:
# v1.1.2 through v1.1.4 (the original signed span; all three .asc are
# tracked for each, verified against git ls-files when this landed) and
# v1.1.23 onward, where signing resumed. The unsigned span between them is
# history that is correct as published and stays exempt. A deliberate
# checksums-only release after the baseline is possible, but only by adding
# its version to ATTRIBUTED_CHECKSUMS_ONLY with the release authority and
# date, which is the attributed decision the old chain never had.
SIGNED_HISTORICAL_SPAN = ((1, 1, 2), (1, 1, 4))
SIGNED_BASELINE = (1, 1, 23)
SIGNATURE_TEMPLATES = (
    "RELEASE_NOTES_{version}.md.asc",
    "VALIDATION_REPORT_{version}.md.asc",
    "SHA256SUMS_{version}.txt.asc",
)
ATTRIBUTED_CHECKSUMS_ONLY: dict[str, str] = {
    # "vX.Y.Z": "decided by <release authority>, <YYYY-MM-DD>, recorded in
    #            RELEASE_NOTES_vX.Y.Z.md",
}


def _version_key(tag: str) -> tuple[int, ...]:
    return tuple(int(part) for part in tag.lstrip("v").split("."))


def manifest_release_version() -> str:
    manifest = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
    release_id = manifest["release_id"]
    assert release_id.startswith("zmeta-v"), (
        f"release_id must look like zmeta-vX.Y.Z, got {release_id!r}"
    )
    return release_id[len("zmeta-"):]


def _signing_required(version: str) -> bool:
    key = _version_key(version)
    if SIGNED_HISTORICAL_SPAN[0] <= key <= SIGNED_HISTORICAL_SPAN[1]:
        return True
    return key >= SIGNED_BASELINE and version not in ATTRIBUTED_CHECKSUMS_ONLY


def required_artifacts(version: str) -> list[str]:
    """The artifact filenames a given release must track.

    An exemption entry relaxes only the signature trio; the notes,
    validation report, and checksums stay required for every release
    since the convention began.
    """
    names = [template.format(version=version) for template in REQUIRED_TEMPLATES]
    if _signing_required(version):
        names.extend(template.format(version=version) for template in SIGNATURE_TEMPLATES)
    return names


def missing_artifacts(release_dir: Path, version: str) -> list[str]:
    """Required artifacts absent from `release_dir` for `version`."""
    return [
        name
        for name in required_artifacts(version)
        if not (release_dir / name).is_file()
    ]


def released_versions(release_dir: Path) -> list[str]:
    """Versions that have release notes, which is how a release announces itself."""
    found = []
    for path in release_dir.glob("RELEASE_NOTES_v*.md"):
        match = re.fullmatch(r"RELEASE_NOTES_(v\d+\.\d+\.\d+)\.md", path.name)
        if match:
            found.append(match.group(1))
    return sorted(found, key=_version_key)


def test_current_release_ships_its_full_artifact_set():
    version = manifest_release_version()
    missing = missing_artifacts(RELEASE_DIR, version)
    assert missing == [], (
        f"the release manifest declares {version}, but these tracked artifacts "
        f"are missing from release/: {missing}. A cut is not complete until all "
        f"of {required_artifacts(version)} exist. Generate checksums with "
        f"`python release/sign_release_artifacts.py --version {version} "
        f"--write-checksums --verify-checksums`; the validation report is authored."
    )


def test_every_release_since_the_convention_ships_its_full_set():
    offenders: list[tuple[str, list[str]]] = []
    inspected = 0
    for version in released_versions(RELEASE_DIR):
        if _version_key(version) < CONVENTION_BASELINE:
            continue
        inspected += 1
        missing = missing_artifacts(RELEASE_DIR, version)
        if missing:
            offenders.append((version, missing))

    # Non-vacuity floor: v1.1.0 through the current cut is well over ten
    # releases. A collapse here means the locator stopped finding release notes,
    # not that the tree got cleaner.
    assert inspected >= 10, (
        f"fewer than ten releases inspected (inspected={inspected}); this guard "
        f"has gone vacuous, check released_versions()"
    )
    assert offenders == [], (
        f"releases missing tracked artifacts: {offenders}. Published releases are "
        f"immutable, so a historical gap here is a real hole in the record, not "
        f"something to backfill silently."
    )


def test_completeness_detector_actually_fires(tmp_path: Path):
    """The paired demonstration: construct the bad state, assert it is reported.

    Discipline 5 requires this to be an artifact that re-runs in CI, not a
    session act. Each required artifact is removed in turn, because a detector
    that only notices a missing checksum file would have passed the exact tree
    that motivated this module.
    """
    for version, expected_count in (("v1.1.9", 3), ("v1.1.3", 6), ("v9.9.9", 6)):
        names = required_artifacts(version)
        assert len(names) == expected_count, (
            f"{version}: expected {expected_count} required artifacts, got {names}"
        )

        for name in names:
            fake = tmp_path / f"{version}-{name}".replace(".", "_")  # unique dir per arm
            fake.mkdir()
            for other in names:
                if other != name:
                    (fake / other).write_text("x", encoding="utf-8")
            assert missing_artifacts(fake, version) == [name], (
                f"detector failed to report {name} as missing for {version}"
            )

        complete = tmp_path / f"{version}-complete".replace(".", "_")
        complete.mkdir()
        for other in names:
            (complete / other).write_text("x", encoding="utf-8")
        assert missing_artifacts(complete, version) == [], (
            f"detector reported a missing artifact on a complete {version} set"
        )


def test_required_set_is_not_silently_narrowed():
    """A future edit that drops a template would make the guard pass vacuously."""
    assert set(REQUIRED_TEMPLATES) == {
        "RELEASE_NOTES_{version}.md",
        "VALIDATION_REPORT_{version}.md",
        "SHA256SUMS_{version}.txt",
    }, (
        "the required-artifact set changed; update RELEASE_CHECKLIST.md in the "
        "same commit so the manual checklist and this guard cannot disagree"
    )
    assert set(SIGNATURE_TEMPLATES) == {
        "RELEASE_NOTES_{version}.md.asc",
        "VALIDATION_REPORT_{version}.md.asc",
        "SHA256SUMS_{version}.txt.asc",
    }, (
        "the signature set changed; update RELEASE_CHECKLIST.md and the X2-02 "
        "record in the same commit"
    )


def test_a_checksums_only_exemption_must_be_attributed():
    """An empty string in the exemption dict is the unattributed decision
    this extension exists to forbid; the entry must name its authority."""
    for version, decision in ATTRIBUTED_CHECKSUMS_ONLY.items():
        assert re.fullmatch(r"v\d+\.\d+\.\d+", version), version
        assert "decided by" in decision and re.search(r"\d{4}-\d{2}-\d{2}", decision), (
            f"{version}: the exemption must name the release authority and date, "
            f"got {decision!r}"
        )


def test_an_exemption_relaxes_only_the_signatures_never_the_trio():
    """The escape hatch must not let the base artifact set lapse with it.

    Exercised through the same public functions the real checks use, with
    the exemption injected and removed around the probe.
    """
    version = "v9.9.8"
    assert len(required_artifacts(version)) == 6, "probe version must be post-baseline"
    ATTRIBUTED_CHECKSUMS_ONLY[version] = "decided by Test Authority, 2026-08-13"
    try:
        names = required_artifacts(version)
        assert names == [t.format(version=version) for t in REQUIRED_TEMPLATES], (
            f"exempt release must still require exactly the trio, got {names}"
        )
    finally:
        del ATTRIBUTED_CHECKSUMS_ONLY[version]
    assert len(required_artifacts(version)) == 6, "the probe exemption leaked"
