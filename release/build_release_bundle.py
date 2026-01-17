import shutil
from pathlib import Path


def collect_sources(root):
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
        root / "spec" / "quickstart.md",
        root / "spec" / "cot-mapping.md",
        root / "spec" / "klv-jreap-projection-notes.md",
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


def main():
    root = Path(__file__).resolve().parents[1]
    dist = root / "release" / "dist"

    if dist.exists():
        shutil.rmtree(dist)
    dist.mkdir(parents=True, exist_ok=True)

    sources = collect_sources(root)

    for src in sources:
        rel = src.relative_to(root)
        dest = dist / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)

    copy_tree(root / "policy", dist / "policy")
    copy_tree(root / "examples", dist / "examples")

    (dist / "VERSION.txt").write_text("1.0.0\n", encoding="utf-8")

    rel_paths = []
    for path in sorted(dist.rglob("*")):
        if path.is_file():
            rel_paths.append(path.relative_to(dist).as_posix())

    write_manifest(dist, rel_paths)


if __name__ == "__main__":
    main()
