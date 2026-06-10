from __future__ import annotations

import argparse
import copy
import importlib.util
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
BUILDER_PATH = ROOT / "tools" / "build_release_manifest.py"
spec = importlib.util.spec_from_file_location("zmeta_build_release_manifest", BUILDER_PATH)
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


REQUIRED_TOP_LEVEL = {
    "manifest_version",
    "release_id",
    "release_name",
    "release_status",
    "release_date",
    "zmeta_versions",
    "hash_algorithm",
    "hash_canonicalization",
    "semantic_contract_hash",
    "schema_bundle_hash",
    "policy_bundle_hash",
    "extension_registry_hash",
    "conformance_class_manifest_hash",
    "profile_projection_catalog_hash",
    "encoding_negative_suite_hash",
    "profile_precision_policy_hash",
    "bad_event_corpus_hash",
    "adapter_conformance_hash",
    "encoding_projection_specs_hash",
    "process_governance_hash",
    "release_bundle_hash",
    "release_manifest_hash",
    "artifact_hashes",
    "artifact_groups",
    "tool_versions",
    "git_commit",
    "branch",
    "generated_by",
    "notes",
    "known_open_issues",
    "experimental_surfaces",
    "future_surfaces_not_valid",
}

REQUIRED_GROUPS = {
    "semantic_contract",
    "schema_bundle",
    "policy_bundle",
    "extension_registry",
    "conformance_classes",
    "core_conformance",
    "profile_projection",
    "encoding_negative",
    "profile_precision",
    "bad_event_corpus",
    "adapter_conformance",
    "encoding_projection_specs",
    "release_tools",
    "conformance_tools",
    "claims",
    "release_policy",
    "process_governance",
    "release_packaging",
}


def _issue(code: str, message: str, *, item: str | None = None) -> dict[str, str]:
    out = {"code": code, "message": message}
    if item:
        out["item"] = item
    return out


def load_yaml(path: Path | str) -> Any:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def _load_manifest(path: Path) -> tuple[dict[str, Any] | None, list[dict[str, str]]]:
    if not path.is_file():
        return None, [_issue("RELEASE_MANIFEST_MISSING", f"manifest file not found: {path}")]
    try:
        data = load_yaml(path)
    except Exception as exc:
        return None, [_issue("RELEASE_MANIFEST_YAML_INVALID", f"failed to load manifest YAML: {exc}")]
    if not isinstance(data, dict):
        return None, [_issue("RELEASE_MANIFEST_INVALID", "manifest must be a YAML mapping")]
    return data, []


def _artifact_hash_map(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    artifacts = manifest.get("artifact_hashes", [])
    if not isinstance(artifacts, list):
        return {}
    out: dict[str, dict[str, Any]] = {}
    for item in artifacts:
        if isinstance(item, dict) and item.get("path"):
            out[str(item["path"])] = item
    return out


def validate_manifest(manifest_path: Path | str, *, root: Path = ROOT) -> list[dict[str, str]]:
    path = Path(manifest_path)
    manifest, issues = _load_manifest(path)
    if manifest is None:
        return issues

    for field in sorted(REQUIRED_TOP_LEVEL):
        if field not in manifest:
            issues.append(_issue("RELEASE_MANIFEST_FIELD_MISSING", f"missing top-level field: {field}"))

    if manifest.get("hash_algorithm") != "SHA-256":
        issues.append(
            _issue(
                "RELEASE_MANIFEST_HASH_ALGORITHM_INVALID",
                f"hash_algorithm must be SHA-256, got {manifest.get('hash_algorithm')}",
            )
        )

    artifact_groups = manifest.get("artifact_groups")
    if not isinstance(artifact_groups, dict):
        issues.append(_issue("RELEASE_MANIFEST_GROUPS_INVALID", "artifact_groups must be a mapping"))
        artifact_groups = {}

    for group_name in sorted(REQUIRED_GROUPS):
        if group_name not in artifact_groups:
            issues.append(_issue("RELEASE_MANIFEST_GROUP_MISSING", f"missing required artifact group: {group_name}"))

    artifact_map = _artifact_hash_map(manifest)
    if not artifact_map:
        issues.append(_issue("RELEASE_MANIFEST_ARTIFACTS_INVALID", "artifact_hashes must be a non-empty list"))

    recomputed_file_hashes: dict[str, str] = {}
    for rel_path, artifact in sorted(artifact_map.items()):
        full_path = root / rel_path
        if not full_path.is_file():
            issues.append(_issue("RELEASE_MANIFEST_ARTIFACT_MISSING", f"listed artifact not found: {rel_path}", item=rel_path))
            continue
        actual_hash = builder.file_hash(rel_path, root)
        recomputed_file_hashes[rel_path] = actual_hash
        expected_hash = artifact.get("hash")
        if expected_hash != actual_hash:
            issues.append(
                _issue(
                    "RELEASE_MANIFEST_ARTIFACT_HASH_MISMATCH",
                    f"expected {expected_hash}, got {actual_hash}",
                    item=rel_path,
                )
            )

    recomputed_group_hashes: dict[str, str] = {}
    for group_name, group in sorted(artifact_groups.items()):
        if not isinstance(group, dict):
            issues.append(_issue("RELEASE_MANIFEST_GROUP_INVALID", "artifact group must be a mapping", item=group_name))
            continue
        paths = group.get("paths")
        if not isinstance(paths, list) or not paths:
            issues.append(_issue("RELEASE_MANIFEST_GROUP_PATHS_INVALID", "artifact group requires non-empty paths", item=group_name))
            continue
        for rel_path in paths:
            if rel_path not in artifact_map:
                issues.append(
                    _issue(
                        "RELEASE_MANIFEST_GROUP_ARTIFACT_MISSING",
                        f"group path lacks artifact_hash entry: {rel_path}",
                        item=group_name,
                    )
                )
        if all((root / str(rel_path)).is_file() for rel_path in paths):
            actual_group_hash = builder.group_hash([str(rel_path) for rel_path in paths], root)
            recomputed_group_hashes[group_name] = actual_group_hash
            expected_group_hash = group.get("hash")
            if expected_group_hash != actual_group_hash:
                issues.append(
                    _issue(
                        "RELEASE_MANIFEST_GROUP_HASH_MISMATCH",
                        f"expected {expected_group_hash}, got {actual_group_hash}",
                        item=group_name,
                    )
                )
            top_field = builder.TOP_LEVEL_HASH_FIELDS.get(group_name)
            if top_field and manifest.get(top_field) != actual_group_hash:
                issues.append(
                    _issue(
                        "RELEASE_MANIFEST_TOP_LEVEL_HASH_MISMATCH",
                        f"{top_field} expected {manifest.get(top_field)}, got {actual_group_hash}",
                        item=group_name,
                    )
                )

    if recomputed_group_hashes:
        actual_bundle_hash = builder.release_bundle_hash(recomputed_group_hashes)
        if manifest.get("release_bundle_hash") != actual_bundle_hash:
            issues.append(
                _issue(
                    "RELEASE_MANIFEST_BUNDLE_HASH_MISMATCH",
                    f"expected {manifest.get('release_bundle_hash')}, got {actual_bundle_hash}",
                )
            )

    manifest_for_hash = copy.deepcopy(manifest)
    actual_manifest_hash = builder.release_manifest_hash(manifest_for_hash)
    if manifest.get("release_manifest_hash") != actual_manifest_hash:
        issues.append(
            _issue(
                "RELEASE_MANIFEST_SELF_HASH_MISMATCH",
                f"expected {manifest.get('release_manifest_hash')}, got {actual_manifest_hash}",
            )
        )

    if path.name == "zmeta-release-manifest.yaml" and any(
        artifact.get("path") == "release/zmeta-release-manifest.yaml"
        for artifact in artifact_map.values()
    ):
        issues.append(
            _issue(
                "RELEASE_MANIFEST_CIRCULAR_ARTIFACT",
                "release/zmeta-release-manifest.yaml must not be included in release_bundle_hash",
            )
        )

    return issues


def run(manifest_path: Path | str, *, quiet: bool = False) -> int:
    issues = validate_manifest(manifest_path)
    if issues:
        for issue in issues:
            item = f" item={issue['item']}" if "item" in issue else ""
            print(f"FAIL {issue['code']}{item}: {issue['message']}")
        return 1
    if not quiet:
        manifest = load_yaml(manifest_path)
        groups = manifest.get("artifact_groups", {})
        artifacts = manifest.get("artifact_hashes", [])
        print(f"release manifest ok groups={len(groups)} artifacts={len(artifacts)}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate the ZMeta release manifest.")
    parser.add_argument(
        "--manifest",
        default=str(ROOT / "release" / "zmeta-release-manifest.yaml"),
        help="Path to release manifest YAML.",
    )
    parser.add_argument("--quiet", action="store_true", help="Suppress success output.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    raise SystemExit(run(args.manifest, quiet=args.quiet))


if __name__ == "__main__":
    main()
