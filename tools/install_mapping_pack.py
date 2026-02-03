import argparse
import json
import shutil
import tempfile
import zipfile
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description="Install a ZMeta mapping pack")
    parser.add_argument("--pack", required=True, help="Path to a pack directory or zip file")
    parser.add_argument("--dest", help="Destination mapping-packs directory")
    parser.add_argument("--schema-id", help="Override schema_id in pack.json")
    parser.add_argument("--pack-slug", help="Override destination folder name")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def read_manifest(pack_root):
    manifest_path = pack_root / "pack.json"
    if not manifest_path.is_file():
        return {}
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("pack.json must be a JSON object")
    return data


def resolve_pack_root(base_dir):
    entries = [entry for entry in base_dir.iterdir() if entry.name != "__MACOSX"]
    if len(entries) == 1 and entries[0].is_dir():
        return entries[0]
    return base_dir


def install_pack(pack_root, dest_root, pack_slug, force=False):
    dest_root.mkdir(parents=True, exist_ok=True)
    dest_dir = dest_root / pack_slug
    if dest_dir.exists():
        if not force:
            raise FileExistsError(f"destination already exists: {dest_dir}")
        shutil.rmtree(dest_dir)
    shutil.copytree(pack_root, dest_dir)
    return dest_dir


def main():
    args = parse_args()
    pack_path = Path(args.pack)
    if not pack_path.exists():
        raise SystemExit(f"pack not found: {pack_path}")

    root = Path(__file__).resolve().parents[1]
    dest_root = Path(args.dest) if args.dest else root / "adapters" / "mapping-packs"

    pack_root = None
    from_zip = False
    temp_dir = None
    if pack_path.is_dir():
        pack_root = pack_path
    elif zipfile.is_zipfile(pack_path):
        temp_dir = tempfile.TemporaryDirectory()
        base_dir = Path(temp_dir.name)
        with zipfile.ZipFile(pack_path) as archive:
            archive.extractall(base_dir)
        from_zip = True
        pack_root = resolve_pack_root(base_dir)
    else:
        raise SystemExit("pack must be a directory or zip file")

    try:
        manifest = read_manifest(pack_root)
        schema_id = args.schema_id or manifest.get("schema_id")
        pack_slug = args.pack_slug or manifest.get("pack_slug")
        if not pack_slug:
            if from_zip and temp_dir is not None and pack_root == Path(temp_dir.name):
                raise SystemExit("pack slug is required for zip packs without a top-level folder")
            pack_slug = pack_root.name
        if not pack_slug:
            raise SystemExit("pack slug is required (use --pack-slug or pack.json)")

        mapping_path = pack_root / "mapping.yaml"
        if not mapping_path.is_file():
            raise SystemExit("mapping.yaml is required in the pack root")

        dest_dir = install_pack(pack_root, dest_root, pack_slug, force=args.force)
    finally:
        if temp_dir is not None:
            temp_dir.cleanup()

    schema_note = f" (schema_id: {schema_id})" if schema_id else ""
    print(f"Installed mapping pack to {dest_dir}{schema_note}")


if __name__ == "__main__":
    main()
