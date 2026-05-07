import argparse
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_TOP_LEVEL = {
    "manifest_version",
    "zmeta_versions",
    "authority",
    "last_updated",
    "status_values",
    "class_records",
    "claim_model",
    "notes",
}

REQUIRED_CLASS_FIELDS = {
    "class_id",
    "display_name",
    "status",
    "version_scope",
    "description",
    "semantic_contract_sections",
    "required_schema_surfaces",
    "required_policy_surfaces",
    "required_gateway_surfaces",
    "required_adapter_surfaces",
    "required_encoding_surfaces",
    "required_conformance_fixtures",
    "required_test_commands",
    "dependencies",
    "exclusions",
    "allowed_claimants",
    "claim_evidence_required",
    "current_repo_support",
    "future_or_reserved_notes",
    "extension_registry_dependencies",
    "references",
}

REQUIRED_CLAIM_FIELDS = {
    "implementation_name",
    "implementation_type",
    "implementation_version",
    "zmeta_versions_supported",
    "classes_claimed",
    "class_claims",
    "test_commands_run",
    "test_results",
    "schema_versions",
    "policy_pack_versions",
    "extension_registry_version",
    "projection_catalog_version",
    "contract_hash",
    "commit_hash",
    "date",
    "claim_owner",
    "limitations",
    "exceptions",
}

REQUIRED_CLASS_CLAIM_FIELDS = {
    "class_id",
    "claim_status",
    "commands",
    "result_summary",
    "limitations",
    "exceptions",
}

PATH_FIELDS = {
    "required_schema_surfaces",
    "required_policy_surfaces",
    "required_gateway_surfaces",
    "required_adapter_surfaces",
    "required_encoding_surfaces",
    "required_conformance_fixtures",
    "references",
}

NON_CLAIMABLE_DEFAULT = {"future", "reserved", "planned"}
IMPLEMENTED_LIKE = {"implemented", "partially_implemented"}
PLACEHOLDER_HASHES = {"pending_D-002", "pending_d002", "pending", "example_pending_checkpoint_commit"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate ZMeta conformance classes and claims.")
    parser.add_argument(
        "--manifest",
        default=str(ROOT / "conformance" / "conformance_classes.yaml"),
        help="Path to conformance class manifest YAML.",
    )
    parser.add_argument(
        "--claims",
        nargs="*",
        default=None,
        help="Claim YAML files or directories of claim YAML files.",
    )
    parser.add_argument(
        "--extension-registry",
        default=str(ROOT / "spec" / "extension-registry.yaml"),
        help="Path to extension registry YAML used for dependency checks.",
    )
    return parser.parse_args()


def _issue(code: str, message: str, *, item: str | None = None) -> dict[str, str]:
    out = {"code": code, "message": message}
    if item:
        out["item"] = item
    return out


def load_yaml(path: Path | str) -> Any:
    with Path(path).open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _string_list(value: Any) -> list[str]:
    return [str(item) for item in _as_list(value)]


def _looks_like_path(value: str) -> bool:
    if not value or value.startswith("python "):
        return False
    if "://" in value:
        return False
    if "/" in value or "\\" in value:
        return True
    return value.endswith((".py", ".md", ".yaml", ".json", ".jsonl", ".proto"))


def _path_exists(value: str) -> bool:
    path = ROOT / value.replace("\\", "/")
    return path.exists()


def _load_manifest(path: Path) -> tuple[dict[str, Any] | None, list[dict[str, str]]]:
    if not path.exists():
        return None, [_issue("CONFORMANCE_MANIFEST_MISSING", f"manifest file not found: {path}")]
    try:
        data = load_yaml(path)
    except Exception as exc:
        return None, [_issue("CONFORMANCE_YAML_INVALID", f"failed to load manifest YAML: {exc}")]
    if not isinstance(data, dict):
        return None, [_issue("CONFORMANCE_TOP_LEVEL_INVALID", "manifest must be a YAML mapping")]
    return data, []


def _load_registry_entries(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    try:
        registry = load_yaml(path)
    except Exception:
        return {}
    entries = registry.get("entries", []) if isinstance(registry, dict) else []
    if not isinstance(entries, list):
        return {}
    return {str(entry.get("name")): entry for entry in entries if isinstance(entry, dict) and entry.get("name")}


def _class_map(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(record.get("class_id")): record
        for record in manifest.get("class_records", [])
        if isinstance(record, dict) and record.get("class_id")
    }


def _dependency_cycle_issues(records: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(class_id: str, stack: list[str]) -> None:
        if class_id in visited:
            return
        if class_id in visiting:
            cycle = " -> ".join(stack + [class_id])
            issues.append(_issue("CONFORMANCE_DEPENDENCY_CYCLE", f"dependency cycle detected: {cycle}", item=class_id))
            return
        visiting.add(class_id)
        for dependency in _string_list(records[class_id].get("dependencies")):
            if dependency in records:
                visit(dependency, stack + [class_id])
        visiting.remove(class_id)
        visited.add(class_id)

    for class_id in records:
        visit(class_id, [])
    return issues


def _check_path_fields(record: dict[str, Any], class_id: str) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    for field in sorted(PATH_FIELDS):
        for value in _string_list(record.get(field)):
            if _looks_like_path(value) and not _path_exists(value):
                issues.append(
                    _issue(
                        "CONFORMANCE_PATH_MISSING",
                        f"{field} references missing repo path: {value}",
                        item=class_id,
                    )
                )
    return issues


def validate_manifest(
    manifest_path: Path | str,
    extension_registry_path: Path | str | None = None,
) -> list[dict[str, str]]:
    manifest_file = Path(manifest_path)
    manifest, issues = _load_manifest(manifest_file)
    if manifest is None:
        return issues

    for key in sorted(REQUIRED_TOP_LEVEL):
        if key not in manifest:
            issues.append(_issue("CONFORMANCE_TOP_LEVEL_MISSING", f"missing top-level key: {key}"))

    records_raw = manifest.get("class_records", [])
    if not isinstance(records_raw, list):
        issues.append(_issue("CONFORMANCE_CLASS_RECORDS_INVALID", "class_records must be a list"))
        records_raw = []

    status_values = set(_string_list(manifest.get("status_values")))
    non_claimable = set(_string_list(manifest.get("non_claimable_statuses"))) or NON_CLAIMABLE_DEFAULT
    seen: dict[str, str] = {}

    for idx, record in enumerate(records_raw):
        if not isinstance(record, dict):
            issues.append(_issue("CONFORMANCE_CLASS_RECORD_INVALID", f"class record {idx} must be a mapping"))
            continue
        class_id = str(record.get("class_id", "") or "")
        if not class_id:
            issues.append(_issue("CONFORMANCE_CLASS_ID_MISSING", f"class record {idx} missing class_id"))
            class_id = f"<class-{idx}>"

        for field in sorted(REQUIRED_CLASS_FIELDS):
            if field not in record:
                issues.append(_issue("CONFORMANCE_CLASS_FIELD_MISSING", f"missing field: {field}", item=class_id))

        if class_id in seen:
            issues.append(_issue("CONFORMANCE_DUPLICATE_CLASS_ID", f"duplicate class ID already seen as {seen[class_id]}", item=class_id))
        else:
            seen[class_id] = str(record.get("status", ""))

        status = str(record.get("status", "") or "")
        if status not in status_values:
            issues.append(_issue("CONFORMANCE_STATUS_INVALID", f"invalid status: {status}", item=class_id))

        if status in IMPLEMENTED_LIKE and not _string_list(record.get("required_test_commands")):
            issues.append(
                _issue(
                    "CONFORMANCE_TEST_COMMAND_MISSING",
                    "implemented or partially implemented classes require at least one test command",
                    item=class_id,
                )
            )

        if status in non_claimable and str(record.get("current_repo_support", "")) == "implemented":
            issues.append(
                _issue(
                    "CONFORMANCE_NONCLAIMABLE_SUPPORT",
                    "future/reserved/planned classes must not claim implemented repo support",
                    item=class_id,
                )
            )

        issues.extend(_check_path_fields(record, class_id))

    records = _class_map(manifest)
    for class_id, record in records.items():
        for dependency in _string_list(record.get("dependencies")):
            if dependency not in records:
                issues.append(_issue("CONFORMANCE_DEPENDENCY_UNKNOWN", f"unknown dependency: {dependency}", item=class_id))

    issues.extend(_dependency_cycle_issues(records))

    registry_path = Path(extension_registry_path) if extension_registry_path else ROOT / "spec" / "extension-registry.yaml"
    registry_entries = _load_registry_entries(registry_path)
    for class_id, record in records.items():
        status = str(record.get("status", ""))
        for registry_name in _string_list(record.get("extension_registry_dependencies")):
            entry = registry_entries.get(registry_name)
            if not entry:
                issues.append(
                    _issue(
                        "CONFORMANCE_EXTENSION_DEPENDENCY_UNKNOWN",
                        f"unknown extension registry dependency: {registry_name}",
                        item=class_id,
                    )
                )
                continue
            registry_status = str(entry.get("status", ""))
            if status in IMPLEMENTED_LIKE and registry_status in {"reserved", "proposed", "rejected"}:
                issues.append(
                    _issue(
                        "CONFORMANCE_EXTENSION_DEPENDENCY_NOT_CLAIMABLE",
                        f"implemented class depends on non-claimable registry entry {registry_name}:{registry_status}",
                        item=class_id,
                    )
                )

    return issues


def _claim_paths(paths: list[str] | None) -> list[Path]:
    if not paths:
        return []
    out: list[Path] = []
    for raw in paths:
        path = Path(raw)
        if path.is_dir():
            out.extend(sorted(path.glob("*.yaml")))
            out.extend(sorted(path.glob("*.yml")))
        else:
            out.append(path)
    return out


def _load_claim(path: Path) -> tuple[dict[str, Any] | None, list[dict[str, str]]]:
    if not path.exists():
        return None, [_issue("CONFORMANCE_CLAIM_FILE_MISSING", f"claim file not found: {path}")]
    try:
        data = load_yaml(path)
    except Exception as exc:
        return None, [_issue("CONFORMANCE_CLAIM_YAML_INVALID", f"failed to load claim YAML: {exc}", item=str(path))]
    if not isinstance(data, dict):
        return None, [_issue("CONFORMANCE_CLAIM_INVALID", "claim must be a YAML mapping", item=str(path))]
    return data, []


def _dependency_closure(class_id: str, records: dict[str, dict[str, Any]]) -> set[str]:
    closure: set[str] = set()

    def visit(current: str) -> None:
        for dependency in _string_list(records.get(current, {}).get("dependencies")):
            if dependency not in closure:
                closure.add(dependency)
                visit(dependency)

    visit(class_id)
    return closure


def _result_map(claim: dict[str, Any]) -> dict[str, str]:
    results: dict[str, str] = {}
    for item in _as_list(claim.get("test_results")):
        if isinstance(item, dict) and item.get("command"):
            results[str(item["command"])] = str(item.get("status", ""))
    return results


def validate_claim(
    claim_path: Path | str,
    manifest: dict[str, Any],
) -> list[dict[str, str]]:
    path = Path(claim_path)
    claim, issues = _load_claim(path)
    if claim is None:
        return issues

    records = _class_map(manifest)
    status_values = set(_string_list(manifest.get("status_values")))
    non_claimable = set(_string_list(manifest.get("non_claimable_statuses"))) or NON_CLAIMABLE_DEFAULT
    claim_status_values = set(_string_list(manifest.get("claim_status_values"))) or {"claimed", "partial", "not_claimed", "not_applicable"}
    item_name = str(path)

    for field in sorted(REQUIRED_CLAIM_FIELDS):
        if field not in claim:
            issues.append(_issue("CONFORMANCE_CLAIM_FIELD_MISSING", f"missing field: {field}", item=item_name))

    classes_claimed = set(_string_list(claim.get("classes_claimed")))
    class_claims_raw = claim.get("class_claims", [])
    if not isinstance(class_claims_raw, list):
        issues.append(_issue("CONFORMANCE_CLAIM_CLASS_CLAIMS_INVALID", "class_claims must be a list", item=item_name))
        class_claims_raw = []

    class_claims: dict[str, dict[str, Any]] = {}
    for class_claim in class_claims_raw:
        if not isinstance(class_claim, dict):
            issues.append(_issue("CONFORMANCE_CLAIM_CLASS_INVALID", "class claim must be a mapping", item=item_name))
            continue
        class_id = str(class_claim.get("class_id", "") or "")
        if class_id:
            class_claims[class_id] = class_claim
        for field in sorted(REQUIRED_CLASS_CLAIM_FIELDS):
            if field not in class_claim:
                issues.append(_issue("CONFORMANCE_CLAIM_CLASS_FIELD_MISSING", f"missing field: {field}", item=class_id or item_name))
        claim_status = str(class_claim.get("claim_status", "") or "")
        if claim_status and claim_status not in claim_status_values:
            issues.append(_issue("CONFORMANCE_CLAIM_STATUS_INVALID", f"invalid claim_status: {claim_status}", item=class_id or item_name))

    command_results = _result_map(claim)
    test_commands_run = set(_string_list(claim.get("test_commands_run")))
    implementation_type = str(claim.get("implementation_type", "") or "")
    versions_supported = set(_string_list(claim.get("zmeta_versions_supported")))

    for class_id in sorted(classes_claimed):
        record = records.get(class_id)
        if not record:
            issues.append(_issue("CONFORMANCE_CLAIM_CLASS_UNKNOWN", f"unknown claimed class: {class_id}", item=item_name))
            continue

        status = str(record.get("status", "") or "")
        if status not in status_values:
            issues.append(_issue("CONFORMANCE_CLAIM_CLASS_STATUS_INVALID", f"class has invalid manifest status: {status}", item=class_id))
        if status in non_claimable:
            issues.append(_issue("CONFORMANCE_CLAIM_CLASS_NONCLAIMABLE", f"class status is not claimable: {status}", item=class_id))

        allowed = set(_string_list(record.get("allowed_claimants")))
        if allowed and implementation_type not in allowed:
            issues.append(
                _issue(
                    "CONFORMANCE_CLAIMANT_NOT_ALLOWED",
                    f"implementation_type {implementation_type} cannot claim this class",
                    item=class_id,
                )
            )

        missing_dependencies = _dependency_closure(class_id, records) - classes_claimed
        for dependency in sorted(missing_dependencies):
            issues.append(
                _issue(
                    "CONFORMANCE_CLAIM_DEPENDENCY_MISSING",
                    f"claimed class requires dependency closure entry: {dependency}",
                    item=class_id,
                )
            )

        version_scope = set(_string_list(record.get("version_scope")))
        if "1.1.0-experimental" in version_scope and "1.1.0-experimental" not in versions_supported:
            issues.append(
                _issue(
                    "CONFORMANCE_CLAIM_VERSION_SCOPE_INVALID",
                    "v1.1.0 experimental class requires zmeta_versions_supported to include 1.1.0-experimental",
                    item=class_id,
                )
            )

        class_claim = class_claims.get(class_id)
        if not class_claim:
            issues.append(_issue("CONFORMANCE_CLAIM_CLASS_EVIDENCE_MISSING", "missing class_claim entry", item=class_id))
            continue
        if status == "partially_implemented" and class_claim.get("claim_status") == "claimed":
            issues.append(
                _issue(
                    "CONFORMANCE_PARTIAL_CLASS_CLAIMED_FULL",
                    "partially implemented classes must use claim_status: partial",
                    item=class_id,
                )
            )

        claim_commands = set(_string_list(class_claim.get("commands")))
        for command in _string_list(record.get("required_test_commands")):
            if command not in claim_commands:
                issues.append(_issue("CONFORMANCE_CLAIM_COMMAND_MISSING", f"class claim missing required command: {command}", item=class_id))
            if command not in test_commands_run:
                issues.append(_issue("CONFORMANCE_CLAIM_COMMAND_NOT_RUN", f"test_commands_run missing required command: {command}", item=class_id))
            status_value = command_results.get(command)
            if status_value is None:
                issues.append(_issue("CONFORMANCE_CLAIM_RESULT_MISSING", f"test_results missing required command: {command}", item=class_id))
            elif status_value != "passed":
                issues.append(_issue("CONFORMANCE_CLAIM_RESULT_FAILED", f"required command did not pass: {command}", item=class_id))

    extra_class_claims = set(class_claims) - classes_claimed
    for class_id in sorted(extra_class_claims):
        issues.append(_issue("CONFORMANCE_CLAIM_UNLISTED_CLASS_EVIDENCE", "class_claim entry is not listed in classes_claimed", item=class_id))

    if not claim.get("commit_hash"):
        issues.append(_issue("CONFORMANCE_CLAIM_HASH_MISSING", "commit_hash is required", item=item_name))
    if not claim.get("contract_hash"):
        issues.append(_issue("CONFORMANCE_CLAIM_HASH_MISSING", "contract_hash is required or must use pending_D-002", item=item_name))

    if claim.get("contract_hash") in {None, ""}:
        issues.append(_issue("CONFORMANCE_CLAIM_HASH_MISSING", "contract_hash cannot be empty", item=item_name))
    if claim.get("commit_hash") in {None, ""}:
        issues.append(_issue("CONFORMANCE_CLAIM_HASH_MISSING", "commit_hash cannot be empty", item=item_name))

    for field in ["schema_versions", "policy_pack_versions", "extension_registry_version", "projection_catalog_version"]:
        value = claim.get(field)
        if value in (None, "", []):
            issues.append(_issue("CONFORMANCE_CLAIM_VERSION_FIELD_MISSING", f"{field} must be recorded or explicitly placeholdered", item=item_name))

    return issues


def validate_claims(
    claim_paths: list[Path | str],
    manifest_path: Path | str,
) -> list[dict[str, str]]:
    manifest, issues = _load_manifest(Path(manifest_path))
    if manifest is None:
        return issues
    for path in claim_paths:
        issues.extend(validate_claim(Path(path), manifest))
    return issues


def run(
    manifest_path: Path | str,
    claims: list[str] | None = None,
    extension_registry_path: Path | str | None = None,
    *,
    quiet: bool = False,
) -> int:
    manifest_file = Path(manifest_path)
    issues = validate_manifest(manifest_file, extension_registry_path)
    claim_files = _claim_paths(claims)

    if not issues and claim_files:
        issues.extend(validate_claims(claim_files, manifest_file))

    if issues:
        for issue in issues:
            item = f" item={issue['item']}" if "item" in issue else ""
            print(f"FAIL {issue['code']}{item}: {issue['message']}")
        return 1

    if not quiet:
        manifest = load_yaml(manifest_file)
        print(f"conformance classes ok classes={len(manifest.get('class_records', []))} claims={len(claim_files)}")
    return 0


def main() -> None:
    args = parse_args()
    raise SystemExit(
        run(
            args.manifest,
            claims=args.claims,
            extension_registry_path=args.extension_registry,
        )
    )


if __name__ == "__main__":
    main()
