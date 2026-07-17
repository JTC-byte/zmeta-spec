import argparse
import shutil
from pathlib import Path

MANIFEST_PATH = Path(__file__).resolve().parent / "zmeta-release-manifest.yaml"
IGNORE_NAMES = (
    "__pycache__",
    ".pytest_cache",
    ".pytest_cache_custom",
    ".pytest_tmp",
    ".pytest_work",
    "pytest-work",
)
IGNORE_PATTERNS = ("*.pyc", "*.pyo", "pytest-cache-files-*")


def _ignore_func(_dir, names):
    ignored = set()
    for name in names:
        if name in IGNORE_NAMES:
            ignored.add(name)
        for pattern in IGNORE_PATTERNS:
            if Path(name).match(pattern):
                ignored.add(name)
    return ignored


def copy_item(src: Path, dest_root: Path, root: Path) -> None:
    if not src.exists():
        raise FileNotFoundError(f"missing path: {src}")
    rel = src.relative_to(root)
    dest = dest_root / rel
    if src.is_dir():
        shutil.copytree(src, dest, dirs_exist_ok=True, ignore=_ignore_func)
    else:
        if src.name in IGNORE_NAMES:
            return
        for pattern in IGNORE_PATTERNS:
            if src.match(pattern):
                return
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)


def build_bundle(
    root: Path,
    bundle_root: Path,
    name: str,
    include_paths: list[str],
    version_tag: str,
) -> Path:
    dest = bundle_root / name
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True, exist_ok=True)

    for rel in include_paths:
        copy_item(root / rel, dest, root)

    (dest / "VERSION.txt").write_text(f"{version_tag}\n", encoding="utf-8")
    return dest


def make_zip(root: Path, bundle_dir: Path, archive_name: str) -> Path:
    archive_base = root / "release" / archive_name
    archive_path = archive_base.with_suffix(".zip")
    if archive_path.exists():
        archive_path.unlink()
    shutil.make_archive(str(archive_base), "zip", root_dir=bundle_dir)
    return archive_path


def default_version_tag():
    """Read the current release id from the release manifest (zmeta-vX -> vX)."""
    try:
        import yaml

        manifest = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
        release_id = str(manifest.get("release_id", ""))
    except Exception:
        return None
    if release_id.startswith("zmeta-"):
        release_id = release_id[len("zmeta-"):]
    return release_id or None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build edge and gateway ZMeta release packages.")
    parser.add_argument(
        "--version",
        default=None,
        help="Release tag, e.g. v1.1.9 (default: release_id from release/zmeta-release-manifest.yaml).",
    )
    return parser.parse_args()


COMMON_PATHS = [
    "schema",
    "policy",
    "spec",
    "adapters",
    "tools",
    "gateway",
    "examples",
    "conformance",
    "configs",
    "README.md",
    "LICENSE",
    "requirements.txt",
    "requirements-dev.txt",
    "zmeta_uuid.py",
    "zmeta_cbor.py",
    "zmeta_compact.py",
    "zmeta_proto.py",
    "deploy/README.md",
    "release/README.md",
    "release/build_mvp_packages.py",
    "release/build_release_bundle.py",
    "release/sign_release_artifacts.py",
]


def main() -> None:
    args = parse_args()
    version = args.version or default_version_tag()
    if not version:
        raise SystemExit(
            "could not derive release version from release/zmeta-release-manifest.yaml; pass --version"
        )
    version_tag = version if version.startswith("v") else f"v{version}"
    root = Path(__file__).resolve().parents[1]
    bundle_root = root / "release" / "bundles"
    bundle_root.mkdir(parents=True, exist_ok=True)

    edge_bundle = build_bundle(
        root,
        bundle_root,
        "zmeta-edge",
        COMMON_PATHS + ["deploy/edge"],
        version_tag,
    )
    gateway_bundle = build_bundle(
        root,
        bundle_root,
        "zmeta-gateway",
        COMMON_PATHS + ["deploy/gateway"],
        version_tag,
    )

    make_zip(root, edge_bundle, f"zmeta-edge-{version_tag}")
    make_zip(root, gateway_bundle, f"zmeta-gateway-{version_tag}")


if __name__ == "__main__":
    main()
