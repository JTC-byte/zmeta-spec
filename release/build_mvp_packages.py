import shutil
from pathlib import Path

VERSION_TAG = "v1.1.0"
IGNORE_NAMES = (
    "__pycache__",
    ".pytest_cache",
    ".pytest_cache_custom",
    ".pytest_tmp",
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


def build_bundle(root: Path, bundle_root: Path, name: str, include_paths: list[str]) -> Path:
    dest = bundle_root / name
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True, exist_ok=True)

    for rel in include_paths:
        copy_item(root / rel, dest, root)

    (dest / "VERSION.txt").write_text(f"{VERSION_TAG}\n", encoding="utf-8")
    return dest


def make_zip(root: Path, bundle_dir: Path, archive_name: str) -> Path:
    archive_base = root / "release" / archive_name
    archive_path = archive_base.with_suffix(".zip")
    if archive_path.exists():
        archive_path.unlink()
    shutil.make_archive(str(archive_base), "zip", root_dir=bundle_dir)
    return archive_path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    bundle_root = root / "release" / "bundles"
    bundle_root.mkdir(parents=True, exist_ok=True)

    common = [
        "schema",
        "policy",
        "spec",
        "adapters",
        "tools",
        "gateway",
        "examples",
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
    ]

    edge_bundle = build_bundle(
        root,
        bundle_root,
        "zmeta-edge",
        common + ["deploy/edge"],
    )
    gateway_bundle = build_bundle(
        root,
        bundle_root,
        "zmeta-gateway",
        common + ["deploy/gateway"],
    )

    make_zip(root, edge_bundle, f"zmeta-edge-{VERSION_TAG}")
    make_zip(root, gateway_bundle, f"zmeta-gateway-{VERSION_TAG}")


if __name__ == "__main__":
    main()
