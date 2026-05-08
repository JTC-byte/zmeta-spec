from __future__ import annotations

import argparse
import copy
import hashlib
import platform
import sys
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "release" / "zmeta-release-manifest.yaml"
DEFAULT_RELEASE_DATE = "2026-05-07"
DEFAULT_RELEASE_ID = "zmeta-reference-hardening-baseline-2026-05-07"
DEFAULT_RELEASE_NAME = "ZMeta Reference Hardening Baseline"
DEFAULT_RELEASE_STATUS = "reference_hardening_baseline"
DEFAULT_RELEASE_METADATA = "explicit_release_input_required"

HASH_PREFIX = "sha256:"
TEXT_SUFFIXES = {
    ".cfg",
    ".csv",
    ".ini",
    ".json",
    ".jsonl",
    ".md",
    ".proto",
    ".ps1",
    ".py",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}

TOP_LEVEL_HASH_FIELDS = {
    "semantic_contract": "semantic_contract_hash",
    "schema_bundle": "schema_bundle_hash",
    "policy_bundle": "policy_bundle_hash",
    "extension_registry": "extension_registry_hash",
    "conformance_classes": "conformance_class_manifest_hash",
    "profile_projection": "profile_projection_catalog_hash",
    "encoding_negative": "encoding_negative_suite_hash",
    "profile_precision": "profile_precision_policy_hash",
    "encoding_projection_specs": "encoding_projection_specs_hash",
}


def _sha256(data: bytes) -> str:
    return HASH_PREFIX + hashlib.sha256(data).hexdigest()


def _repo_relative(path: Path, root: Path = ROOT) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _is_text_path(path: Path) -> bool:
    return path.suffix.lower() in TEXT_SUFFIXES


def canonical_file_bytes(path: Path, root: Path = ROOT) -> tuple[bytes, str]:
    full_path = path if path.is_absolute() else root / path
    data = full_path.read_bytes()
    if _is_text_path(full_path):
        text = data.decode("utf-8")
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        return text.encode("utf-8"), "text_lf"
    return data, "binary_raw"


def file_hash(path: Path | str, root: Path = ROOT) -> str:
    data, _mode = canonical_file_bytes(Path(path), root)
    return _sha256(data)


def group_hash(paths: list[Path | str], root: Path = ROOT) -> str:
    entries: list[str] = []
    for raw_path in sorted((Path(path) for path in paths), key=lambda item: item.as_posix()):
        rel = raw_path.as_posix()
        entries.append(f"{rel}\n{file_hash(raw_path, root)}\n")
    return _sha256("".join(entries).encode("utf-8"))


def release_bundle_hash(group_hashes: dict[str, str]) -> str:
    entries = [f"{name}\n{value}\n" for name, value in sorted(group_hashes.items())]
    return _sha256("".join(entries).encode("utf-8"))


def canonical_manifest_bytes(manifest: dict[str, Any]) -> bytes:
    canonical = copy.deepcopy(manifest)
    canonical["release_manifest_hash"] = None
    text = yaml.safe_dump(
        canonical,
        sort_keys=True,
        default_flow_style=False,
        allow_unicode=False,
        width=1000,
    )
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text.encode("utf-8")


def release_manifest_hash(manifest: dict[str, Any]) -> str:
    return _sha256(canonical_manifest_bytes(manifest))


def _existing(paths: list[str], root: Path = ROOT) -> list[str]:
    return [path for path in paths if (root / path).is_file()]


def _glob(pattern: str, root: Path = ROOT) -> list[str]:
    return sorted(_repo_relative(path, root) for path in root.glob(pattern) if path.is_file())


def artifact_groups(root: Path = ROOT, *, include_tool_source: bool = True) -> dict[str, dict[str, Any]]:
    groups: dict[str, dict[str, Any]] = {
        "semantic_contract": {
            "description": "Narrow normative semantic baseline.",
            "paths": ["spec/semantics-contract.md"],
        },
        "schema_bundle": {
            "description": "Canonical dispatcher plus locked v1.0 and experimental v1.1.0 schemas.",
            "paths": [
                "schema/zmeta-event.schema.json",
                "schema/zmeta-event-1.0.schema.json",
                "schema/zmeta-event-1.1.0.schema.json",
            ],
        },
        "policy_bundle": {
            "description": "Release-included policy YAML and policy variant baselines.",
            "paths": _glob("policy/*.yaml", root) + _glob("configs/policy-variants/*.yaml", root),
        },
        "extension_registry": {
            "description": "Machine-readable extension and reserved-vocabulary registry.",
            "paths": ["spec/extension-registry.yaml"],
        },
        "conformance_classes": {
            "description": "Machine-readable conformance class manifest.",
            "paths": ["conformance/conformance_classes.yaml"],
        },
        "core_conformance": {
            "description": "Core schema and policy conformance must-pass/must-fail fixtures.",
            "paths": [
                "conformance/must-pass.jsonl",
                "conformance/must-fail.jsonl",
            ],
        },
        "profile_projection": {
            "description": "Profile projection field catalog and source/projected fixtures.",
            "paths": _existing(
                [
                    "conformance/profile_projection_field_catalog.yaml",
                    "conformance/profile-projection/must-pass.jsonl",
                    "conformance/profile-projection/must-fail.jsonl",
                    "conformance/profile-projection/context.jsonl",
                ],
                root,
            ),
        },
        "encoding_negative": {
            "description": "Compact/protobuf/gateway invalid-after-decode fixture suite.",
            "paths": _existing(
                [
                    "conformance/encoding-negative/compact-must-fail.jsonl",
                    "conformance/encoding-negative/protobuf-must-fail.jsonl",
                    "conformance/encoding-negative/gateway-must-fail.jsonl",
                    "conformance/encoding-negative/context.jsonl",
                ],
                root,
            ),
        },
        "profile_precision": {
            "description": "Reference profile precision policy and source/projected fixtures.",
            "paths": _existing(
                [
                    "policy/profile-precision.yaml",
                    "conformance/profile-precision/must-pass.jsonl",
                    "conformance/profile-precision/must-fail.jsonl",
                    "conformance/profile-precision/context.jsonl",
                ],
                root,
            ),
        },
        "encoding_projection_specs": {
            "description": "Compact CBOR and protobuf projection specifications and codec evidence.",
            "paths": [
                "spec/compact-binary-mapping.md",
                "spec/protobuf-encoding.md",
                "schema/proto/zmeta_event_v1.proto",
                "zmeta_compact.py",
                "zmeta_cbor.py",
                "zmeta_proto.py",
            ],
        },
        "claims": {
            "description": "Example implementation claim files for release-baseline references.",
            "paths": [
                "conformance/claims/example-reference-gateway.yaml",
                "conformance/claims/example-core-producer.yaml",
            ],
        },
        "release_policy": {
            "description": "Human-readable release hash taxonomy and canonicalization policy.",
            "paths": ["spec/release-hash-policy.md"],
        },
    }

    if include_tool_source:
        groups["release_tools"] = {
            "description": "Release hash build and validation tooling.",
            "paths": [
                "tools/compute_contract_hash.py",
                "tools/build_release_manifest.py",
                "tools/validate_release_manifest.py",
            ],
        }
        groups["conformance_tools"] = {
            "description": "Conformance validators included in the reference baseline.",
            "paths": [
                "tools/validate_conformance.py",
                "tools/validate_projection.py",
                "tools/validate_extension_registry.py",
                "tools/validate_conformance_classes.py",
                "tools/validate_encoding_negative.py",
                "tools/validate_precision_policy.py",
            ],
        }

    return groups


def build_manifest_data(
    *,
    release_id: str = DEFAULT_RELEASE_ID,
    release_name: str = DEFAULT_RELEASE_NAME,
    release_status: str = DEFAULT_RELEASE_STATUS,
    release_date: str = DEFAULT_RELEASE_DATE,
    git_commit: str | None = DEFAULT_RELEASE_METADATA,
    branch: str | None = DEFAULT_RELEASE_METADATA,
    generated_by: str = "tools/build_release_manifest.py",
    include_tool_source: bool = True,
    root: Path = ROOT,
) -> dict[str, Any]:
    groups = artifact_groups(root, include_tool_source=include_tool_source)
    artifact_hashes: list[dict[str, str]] = []
    group_hashes: dict[str, str] = {}

    for group_name, group in sorted(groups.items()):
        paths = sorted(group["paths"])
        if not paths:
            raise FileNotFoundError(f"artifact group has no files: {group_name}")
        for rel_path in paths:
            full_path = root / rel_path
            if not full_path.is_file():
                raise FileNotFoundError(f"required artifact missing: {rel_path}")
            artifact_hash, mode = file_hash(rel_path, root), canonical_file_bytes(Path(rel_path), root)[1]
            artifact_hashes.append(
                {
                    "path": rel_path,
                    "group": group_name,
                    "hash": artifact_hash,
                    "canonicalization": mode,
                }
            )
        group_hashes[group_name] = group_hash(paths, root)
        group["paths"] = paths
        group["hash"] = group_hashes[group_name]

    manifest: dict[str, Any] = {
        "manifest_version": 1,
        "release_id": release_id,
        "release_name": release_name,
        "release_status": release_status,
        "release_date": release_date,
        "zmeta_versions": {
            "normative": ["1.0"],
            "experimental": ["1.1.0-experimental"],
        },
        "hash_algorithm": "SHA-256",
        "hash_canonicalization": {
            "text_files": "UTF-8 bytes after CRLF/CR to LF normalization",
            "binary_files": "raw bytes",
            "file_hashes": "sha256 over canonicalized file bytes",
            "group_hashes": "sha256 over sorted 'relative/path\\nsha256:<file_hash>\\n' entries",
            "release_bundle_hash": "sha256 over sorted 'group_name\\nsha256:<group_hash>\\n' entries; release manifest file excluded",
            "release_manifest_hash": "sha256 over canonical YAML manifest content with release_manifest_hash set to null",
        },
        "semantic_contract_hash": group_hashes["semantic_contract"],
        "schema_bundle_hash": group_hashes["schema_bundle"],
        "policy_bundle_hash": group_hashes["policy_bundle"],
        "extension_registry_hash": group_hashes["extension_registry"],
        "conformance_class_manifest_hash": group_hashes["conformance_classes"],
        "profile_projection_catalog_hash": group_hashes["profile_projection"],
        "encoding_negative_suite_hash": group_hashes["encoding_negative"],
        "profile_precision_policy_hash": group_hashes["profile_precision"],
        "encoding_projection_specs_hash": group_hashes["encoding_projection_specs"],
        "release_bundle_hash": release_bundle_hash(group_hashes),
        "release_manifest_hash": None,
        "artifact_hashes": sorted(artifact_hashes, key=lambda item: item["path"]),
        "artifact_groups": groups,
        "tool_versions": {
            "python": platform.python_version(),
            "builder": "tools/build_release_manifest.py",
            "validator": "tools/validate_release_manifest.py",
        },
        "git_commit": git_commit or DEFAULT_RELEASE_METADATA,
        "branch": branch or DEFAULT_RELEASE_METADATA,
        "generated_by": generated_by,
        "notes": [
            "Reference hardening-baseline manifest, not a formal tagged release.",
            "git_commit and branch use stable placeholders by default; formal release generation must pass explicit metadata.",
            "The semantic contract hash is narrow and does not include implementation artifacts.",
            "Protobuf is classified as an experimental encoding projection, not v1.0 semantic authority.",
            "Release manifest validation is opt-in and does not change default strict conformance.",
        ],
        "known_open_issues": [
            "D-003 OPEN - Future Semantics Require Versioned Implementation Branches",
            "D-004 OPEN - Companion Artifact Set Needed",
            "D-012 OPEN - Formal Release Tag, Signature, and Attestation Packaging",
        ],
        "experimental_surfaces": [
            "schema/zmeta-event-1.1.0.schema.json",
            "schema/proto/zmeta_event_v1.proto",
            "spec/protobuf-encoding.md",
            "zmeta_proto.py",
        ],
        "future_surfaces_not_valid": [
            "reserved and proposed extension registry entries",
            "future conformance classes with planned/reserved/future status",
            "D-003 version-branch candidates",
            "D-004 companion artifact concepts",
        ],
    }
    manifest["release_manifest_hash"] = release_manifest_hash(manifest)
    return manifest


def _claim_hash_values(manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "contract_hash": manifest["semantic_contract_hash"],
        "release_hashes": {
            "semantic_contract_hash": manifest["semantic_contract_hash"],
            "schema_bundle_hash": manifest["schema_bundle_hash"],
            "policy_bundle_hash": manifest["policy_bundle_hash"],
            "extension_registry_hash": manifest["extension_registry_hash"],
            "conformance_class_manifest_hash": manifest["conformance_class_manifest_hash"],
            "profile_projection_catalog_hash": manifest["profile_projection_catalog_hash"],
            "encoding_negative_suite_hash": manifest["encoding_negative_suite_hash"],
            "profile_precision_policy_hash": manifest["profile_precision_policy_hash"],
            "encoding_projection_specs_hash": manifest["encoding_projection_specs_hash"],
            "release_manifest_hash": "omitted_to_avoid_claim_manifest_circularity",
        },
    }


def update_claim_files(manifest: dict[str, Any], root: Path = ROOT) -> None:
    values = _claim_hash_values(manifest)
    for rel_path in (
        "conformance/claims/example-reference-gateway.yaml",
        "conformance/claims/example-core-producer.yaml",
    ):
        path = root / rel_path
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError(f"claim file must be a mapping: {rel_path}")
        data.update(values)
        limitations = data.get("limitations")
        if isinstance(limitations, list):
            data["limitations"] = [
                item.replace(
                    "Release-grade claims must record actual commit and release hashes.",
                    "Release-grade claims must record the actual release commit; this example uses reference hash baselines.",
                )
                if isinstance(item, str)
                else item
                for item in limitations
            ]
        path.write_text(
            yaml.safe_dump(data, sort_keys=False, allow_unicode=False, width=1000),
            encoding="utf-8",
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the ZMeta reference release manifest.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Manifest output path.")
    parser.add_argument("--release-id", default=DEFAULT_RELEASE_ID)
    parser.add_argument("--release-name", default=DEFAULT_RELEASE_NAME)
    parser.add_argument("--release-status", default=DEFAULT_RELEASE_STATUS)
    parser.add_argument("--release-date", default=DEFAULT_RELEASE_DATE)
    parser.add_argument(
        "--git-commit",
        default=DEFAULT_RELEASE_METADATA,
        help="Explicit release git commit. Default is a stable placeholder for committed reference manifests.",
    )
    parser.add_argument(
        "--branch",
        default=DEFAULT_RELEASE_METADATA,
        help="Explicit release branch. Default is a stable placeholder for committed reference manifests.",
    )
    parser.add_argument("--generated-by", default="tools/build_release_manifest.py")
    parser.add_argument("--include-tool-source", action="store_true", default=True)
    parser.add_argument("--no-include-tool-source", dest="include_tool_source", action="store_false")
    parser.add_argument("--update-claims", action="store_true", help="Update example claims with current release hash fields before rebuilding the manifest.")
    parser.add_argument("--no-update-claims", action="store_true", help="Accepted for explicit no-op compatibility.")
    parser.add_argument("--dry-run", action="store_true", help="Print manifest YAML instead of writing it.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = build_manifest_data(
        release_id=args.release_id,
        release_name=args.release_name,
        release_status=args.release_status,
        release_date=args.release_date,
        git_commit=args.git_commit,
        branch=args.branch,
        generated_by=args.generated_by,
        include_tool_source=args.include_tool_source,
    )

    if args.update_claims:
        update_claim_files(manifest)
        manifest = build_manifest_data(
            release_id=args.release_id,
            release_name=args.release_name,
            release_status=args.release_status,
            release_date=args.release_date,
            git_commit=args.git_commit,
            branch=args.branch,
            generated_by=args.generated_by,
            include_tool_source=args.include_tool_source,
        )

    output = Path(args.output)
    text = yaml.safe_dump(manifest, sort_keys=False, allow_unicode=False, width=1000)
    if args.dry_run:
        sys.stdout.write(text)
        return 0
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")
    print(f"wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
