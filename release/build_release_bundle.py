import argparse
import shutil
from pathlib import Path

VERSION = "1.1.9"


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
        root / "tools" / "build_release_manifest.py",
        root / "tools" / "validate_release_manifest.py",
        root / "tools" / "build_release_package.py",
        root / "tools" / "validate_release_package.py",
        root / "tools" / "compute_contract_hash.py",
        root / "tools" / "validate_conformance.py",
        root / "release" / f"VALIDATION_REPORT_v{version}.md",
    ]
    for path in optional:
        if path.is_file():
            sources.append(path)

    return sources


def write_manifest(dist, rel_paths):
    manifest_path = dist / "MANIFEST.txt"
    manifest_lines = sorted(rel_paths + ["MANIFEST.txt"])
    manifest_path.write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")


def copy_tree(src, dest):
    if not src.is_dir():
        return
    shutil.copytree(src, dest, dirs_exist_ok=True)


def parse_args():
    parser = argparse.ArgumentParser(description="Build the full ZMeta release bundle.")
    parser.add_argument("--version", default=VERSION, help="Release version without leading v.")
    return parser.parse_args()


def main():
    args = parse_args()
    version = args.version.lstrip("v")
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
    copy_tree(root / "configs", dist / "configs")
    copy_tree(root / "examples", dist / "examples")

    (dist / "VERSION.txt").write_text(f"{version}\n", encoding="utf-8")

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
