import shutil
from pathlib import Path


def collect_sources(root):
    sources = []

    required = [
        root / "schema" / "zmeta-event-1.0.schema.json",
        root / "spec" / "semantics-contract.md",
        root / "spec" / "quickstart.md",
    ]
    for path in required:
        if not path.is_file():
            raise FileNotFoundError(f"required file missing: {path}")
        sources.append(path)

    sources.extend(sorted(root.glob("policy/*.yaml")))
    sources.extend(sorted(root.glob("examples/*.jsonl")))

    optional = [
        root / "spec" / "cot-mapping.md",
        root / "spec" / "klv-jreap-projection-notes.md",
    ]
    for path in optional:
        if path.is_file():
            sources.append(path)

    return sources


def write_manifest(dist, rel_paths):
    manifest_path = dist / "MANIFEST.txt"
    manifest_lines = sorted(rel_paths + ["MANIFEST.txt", "VERSION.txt"])
    manifest_path.write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")


def main():
    root = Path(__file__).resolve().parents[1]
    dist = root / "release" / "dist"

    if dist.exists():
        shutil.rmtree(dist)
    dist.mkdir(parents=True, exist_ok=True)

    sources = collect_sources(root)
    rel_paths = []

    for src in sources:
        rel = src.relative_to(root)
        dest = dist / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        rel_paths.append(rel.as_posix())

    (dist / "VERSION.txt").write_text("1.0.0\n", encoding="utf-8")
    write_manifest(dist, rel_paths)


if __name__ == "__main__":
    main()
