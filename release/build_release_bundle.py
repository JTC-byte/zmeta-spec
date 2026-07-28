import argparse
import shutil
from pathlib import Path

MANIFEST_PATH = Path(__file__).resolve().parent / "zmeta-release-manifest.yaml"


def default_version():
    """Read the current release id from the release manifest (zmeta-vX -> X, no leading v)."""
    try:
        import yaml

        manifest = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
        release_id = str(manifest.get("release_id", ""))
    except Exception:
        return None
    if release_id.startswith("zmeta-"):
        release_id = release_id[len("zmeta-"):]
    return release_id.lstrip("v") or None


def collect_sources(root, version):
    sources = []

    required = [
        root / "schema" / "zmeta-event-1.0.schema.json",
        root / "spec" / "semantics-contract.md",
    ]
    for path in required:
        if not path.is_file():
            raise FileNotFoundError(f"required file missing: {path}")
        sources.append(path)

    optional = [
        root / "README.md",
        root / "CHANGELOG.md",
        # PC-09: the declared process_governance group.
        root / "AGENTS.md",
        root / "CONFORMANCE.md",
        root / "CONTRIBUTING.md",
        root / "IP_POLICY.md",
        root / "TRADEMARK.md",
        root / "docs" / "zmeta_change_governance.md",
        root / "docs" / "zmeta_defensive_publication.md",
        root / "zmeta_cbor.py",
        root / "zmeta_compact.py",
        root / "zmeta_proto.py",
        root / "schema" / "README.md",
        root / "schema" / "zmeta-event.schema.json",
        root / "schema" / "zmeta-event-1.1.0.schema.json",
        root / "schema" / "proto" / "zmeta_event_v1.proto",
        root / "release" / "README.md",
        root / "release" / "zmeta-release-manifest.yaml",
        root / "release" / "RELEASE_PACKAGE_README.md",
        root / "release" / "governed-baseline.yaml",
        root / "release" / "RELEASE_NOTES_TEMPLATE.md",
        root / "release" / "ATTESTATION_TEMPLATE.yaml",
        root / "release" / "sign_release_artifacts.py",
        root / "release" / f"RELEASE_NOTES_v{version}.md",
        root / "spec" / "quickstart.md",
        root / "spec" / "versioning.md",
        root / "spec" / "installation-guide.md",
        root / "spec" / "cot-mapping.md",
        root / "spec" / "klv-jreap-projection-notes.md",
        root / "spec" / "compact-binary-mapping.md",
        root / "spec" / "protobuf-encoding.md",
        root / "spec" / "field-dictionary.md",
        root / "spec" / "profile-compatibility.md",
        root / "spec" / "release-hash-policy.md",
        root / "spec" / "release-signing-attestation.md",
        root / "spec" / "README.md",
        root / "release" / f"VALIDATION_REPORT_v{version}.md",
    ]
    for path in optional:
        if path.is_file():
            sources.append(path)

    return sources


DIST_BUNDLE_NOTES = """# What this bundle is

`zmeta-vX.Y.Z-dist.zip` is the **specification distribution**: the semantic
contract, schemas, governed policy and its JSON projection, the conformance
corpus, the governance documents, examples, configs, and the spec-side tooling.

**It is not the reference stack.** It does not carry `gateway/` or `adapters/`,
so the repository README bundled here — written for a full clone — describes a
walkthrough this bundle cannot run. Two shipped tools import the reference
gateway at module load and will fail here for the same reason:

- `tools/validate_conformance.py`
- `tools/compute_contract_hash.py`

Everything else in `tools/` runs standalone, including
`tools/validate_release_manifest.py`, which verifies the hash manifest shipped
alongside this file:

    python tools/validate_release_manifest.py --manifest release/zmeta-release-manifest.yaml

## If you want to run something

Take `zmeta-edge-vX.Y.Z.zip` or `zmeta-gateway-vX.Y.Z.zip` for a runnable
deployment, or clone the repository for development. Those carry the gateway,
the adapters, and the full conformance toolchain.

## One flag is repository-only by design

`validate_conformance.py --conformance-classes` cites maintainer process
records as its class evidence. Bundles ship the governance documents but not
the process-record archive, so that flag reports missing paths from any
bundle. It is not a corrupt download. See `conformance/README.md`.
"""


def write_manifest(dist, rel_paths):
    manifest_path = dist / "MANIFEST.txt"
    manifest_lines = sorted(rel_paths + ["MANIFEST.txt"])
    manifest_path.write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")


def _ignore_build_residue(_dir, names):
    return {
        name
        for name in names
        if name in ("__pycache__", ".pytest_cache") or name.endswith((".pyc", ".pyo"))
    }


def copy_tree(src, dest):
    if not src.is_dir():
        # M6: this used to return silently, so a moved or missing tree produced
        # a quietly thin bundle -- the export directory could vanish and every
        # gate stayed green. A source tree that is not there is a build error.
        raise FileNotFoundError(f"bundle source tree missing: {src}")
    shutil.copytree(src, dest, dirs_exist_ok=True, ignore=_ignore_build_residue)


def parse_args():
    parser = argparse.ArgumentParser(description="Build the full ZMeta release bundle.")
    parser.add_argument(
        "--version",
        default=None,
        help=(
            "Release version without leading v "
            "(default: release_id from release/zmeta-release-manifest.yaml)."
        ),
    )
    return parser.parse_args()


def main():
    args = parse_args()
    version = args.version.lstrip("v") if args.version else default_version()
    if not version:
        raise SystemExit(
            "could not derive release version from release/zmeta-release-manifest.yaml; pass --version"
        )
    root = Path(__file__).resolve().parents[1]
    dist = root / "release" / "dist"

    if dist.exists():
        shutil.rmtree(dist)
    dist.mkdir(parents=True, exist_ok=True)

    sources = collect_sources(root, version)

    for src in sources:
        rel = src.relative_to(root)
        dest = dist / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)

    copy_tree(root / "policy", dist / "policy")
    copy_tree(root / "export", dist / "export")
    copy_tree(root / "conformance", dist / "conformance")
    # PC-09/PC-12: whole trees, not enumerated files -- the enumeration drifted
    # silently every time a spec file or validator was added.
    #
    # PC-12 REVERSED on measurement. It first removed `tools` entirely, on the
    # premise that these validators import the reference gateway at module load
    # and this bundle carries no `gateway/`. A later review measured it: that is
    # true of exactly TWO of them (`validate_conformance.py`,
    # `compute_contract_hash.py`); the other fourteen run standalone. Worse, the
    # manifest hashes sixteen `tools/` paths, so a dist without them could not
    # validate the hash manifest it still shipped -- and
    # `spec/release-hash-policy.md`, also in this bundle, tells deployments to
    # validate before startup. The real complaint was never the tools; it was a
    # bundle whose README promised a walkthrough it could not run. That is a
    # documentation problem and BUNDLE_NOTES.md below is the fix.
    copy_tree(root / "spec", dist / "spec")
    copy_tree(root / "tools", dist / "tools")
    copy_tree(root / "configs", dist / "configs")
    copy_tree(root / "examples", dist / "examples")

    (dist / "VERSION.txt").write_text(f"{version}\n", encoding="utf-8")
    (dist / "BUNDLE_NOTES.md").write_text(DIST_BUNDLE_NOTES, encoding="utf-8")

    rel_paths = []
    for path in sorted(dist.rglob("*")):
        if path.is_file():
            rel_paths.append(path.relative_to(dist).as_posix())

    write_manifest(dist, rel_paths)

    archive_base = root / "release" / f"zmeta-v{version}-dist"
    archive_path = archive_base.with_suffix(".zip")
    if archive_path.exists():
        archive_path.unlink()
    shutil.make_archive(str(archive_base), "zip", root_dir=dist)


if __name__ == "__main__":
    main()
