"""Validate the ZMeta future-branch roadmap artifact (S1-11B).

The roadmap is a planning/governance artifact only. This validator proves the
artifact stays structurally honest: statuses and priorities use the declared
vocabulary, candidate ids and dependencies resolve, registry cross-references
exist, every candidate carries promotion tripwires, and no roadmap candidate
claims experimental/adopted standing while its registry names remain
reserved/proposed.
"""

import argparse
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_TOP_LEVEL = {
    "roadmap_version",
    "last_updated",
    "source_plan",
    "evidence_bar",
    "authority",
    "status_values",
    "priority_values",
    "default_required_surfaces",
    "candidates",
    "rejected_or_deferred",
}

REQUIRED_CANDIDATE_FIELDS = {
    "id",
    "display_name",
    "status",
    "priority",
    "purpose",
    "affected_events",
    "registry_refs",
    "depends_on",
    "required_surfaces",
    "promotion_evidence",
    "tripwires",
    "recommendation",
    "notes",
}

REQUIRED_DECISION_FIELDS = {
    "id",
    "display_name",
    "decision",
    "date",
    "registry_refs",
    "rationale",
}

EVENT_FAMILIES = {
    "OBSERVATION_EVENT",
    "INFERENCE_EVENT",
    "FUSION_EVENT",
    "STATE_EVENT",
    "COMMAND_EVENT",
    "SYSTEM_EVENT",
}

# Roadmap statuses that assert branch validity and therefore require the
# referenced registry names to already be experimental/adopted.
VALIDITY_ASSERTING_STATUSES = {"experimental", "implemented_pending_audit", "adopted"}
REGISTRY_VALID_STATUSES = {"experimental", "adopted"}

AUTHORITY_REQUIRED_PHRASE = "does not make any concept valid"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate the ZMeta future-branch roadmap.")
    parser.add_argument(
        "--roadmap",
        default=str(ROOT / "spec" / "future-branch-roadmap.yaml"),
        help="Path to the future-branch roadmap YAML.",
    )
    parser.add_argument(
        "--registry",
        default=str(ROOT / "spec" / "extension-registry.yaml"),
        help="Path to the extension registry YAML for cross-reference checks.",
    )
    parser.add_argument("--quiet", action="store_true", help="Suppress the ok summary line.")
    return parser.parse_args()


def _issue(code: str, message: str, *, item: str | None = None) -> dict[str, str]:
    out = {"code": code, "message": message}
    if item:
        out["item"] = item
    return out


def _load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _registry_statuses(registry_path: Path) -> dict[str, str]:
    data = _load_yaml(registry_path)
    statuses: dict[str, str] = {}
    for entry in data.get("entries", []):
        if isinstance(entry, dict) and "name" in entry:
            statuses[str(entry["name"])] = str(entry.get("status", ""))
    return statuses


def _check_string_list(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) and item.strip() for item in value)


def validate_roadmap(roadmap_path: Path, registry_path: Path) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []

    data = _load_yaml(roadmap_path)
    if not isinstance(data, dict):
        return [_issue("ROADMAP_NOT_A_MAPPING", "roadmap root must be a mapping")]

    missing = REQUIRED_TOP_LEVEL - set(data)
    if missing:
        issues.append(
            _issue("ROADMAP_MISSING_TOP_LEVEL", f"missing top-level keys: {sorted(missing)}")
        )
        return issues

    authority = str(data.get("authority", ""))
    if AUTHORITY_REQUIRED_PHRASE not in authority:
        issues.append(
            _issue(
                "ROADMAP_AUTHORITY_STATEMENT_MISSING",
                "authority text must state that the roadmap "
                f"'{AUTHORITY_REQUIRED_PHRASE}'",
            )
        )

    status_values = data.get("status_values", [])
    priority_values = data.get("priority_values", [])
    if not _check_string_list(status_values):
        issues.append(_issue("ROADMAP_STATUS_VALUES_INVALID", "status_values must be a list of strings"))
    if not _check_string_list(priority_values):
        issues.append(_issue("ROADMAP_PRIORITY_VALUES_INVALID", "priority_values must be a list of strings"))
    if not _check_string_list(data.get("default_required_surfaces", [])):
        issues.append(
            _issue(
                "ROADMAP_DEFAULT_SURFACES_INVALID",
                "default_required_surfaces must be a list of strings",
            )
        )

    try:
        registry_statuses = _registry_statuses(registry_path)
    except (OSError, yaml.YAMLError) as exc:
        issues.append(
            _issue("ROADMAP_REGISTRY_UNREADABLE", f"could not read extension registry: {exc}")
        )
        registry_statuses = {}

    candidates = data.get("candidates", [])
    if not isinstance(candidates, list) or not candidates:
        issues.append(_issue("ROADMAP_CANDIDATES_INVALID", "candidates must be a non-empty list"))
        candidates = []

    seen_ids: set[str] = set()
    candidate_ids: set[str] = set()
    for candidate in candidates:
        if isinstance(candidate, dict) and isinstance(candidate.get("id"), str):
            candidate_ids.add(candidate["id"])

    for candidate in candidates:
        if not isinstance(candidate, dict):
            issues.append(_issue("ROADMAP_CANDIDATE_NOT_A_MAPPING", "candidate entries must be mappings"))
            continue
        cid = str(candidate.get("id", "<missing id>"))

        missing_fields = REQUIRED_CANDIDATE_FIELDS - set(candidate)
        if missing_fields:
            issues.append(
                _issue(
                    "ROADMAP_CANDIDATE_MISSING_FIELDS",
                    f"missing fields: {sorted(missing_fields)}",
                    item=cid,
                )
            )
            continue

        if cid in seen_ids:
            issues.append(_issue("ROADMAP_DUPLICATE_ID", "duplicate candidate id", item=cid))
        seen_ids.add(cid)

        if candidate["status"] not in status_values:
            issues.append(
                _issue(
                    "ROADMAP_STATUS_UNKNOWN",
                    f"status '{candidate['status']}' not in status_values",
                    item=cid,
                )
            )
        if candidate["priority"] not in priority_values:
            issues.append(
                _issue(
                    "ROADMAP_PRIORITY_UNKNOWN",
                    f"priority '{candidate['priority']}' not in priority_values",
                    item=cid,
                )
            )

        affected = candidate.get("affected_events", [])
        if not _check_string_list(affected):
            issues.append(
                _issue("ROADMAP_AFFECTED_EVENTS_INVALID", "affected_events must be a list of strings", item=cid)
            )
        else:
            unknown_events = sorted(set(affected) - EVENT_FAMILIES)
            if unknown_events:
                issues.append(
                    _issue(
                        "ROADMAP_AFFECTED_EVENTS_UNKNOWN",
                        f"unknown event families: {unknown_events}",
                        item=cid,
                    )
                )

        registry_refs = candidate.get("registry_refs", [])
        if not isinstance(registry_refs, list):
            issues.append(_issue("ROADMAP_REGISTRY_REFS_INVALID", "registry_refs must be a list", item=cid))
            registry_refs = []
        for ref in registry_refs:
            if registry_statuses and ref not in registry_statuses:
                issues.append(
                    _issue(
                        "ROADMAP_REGISTRY_REF_UNKNOWN",
                        f"registry_refs name '{ref}' not found in extension registry",
                        item=cid,
                    )
                )

        for dep in candidate.get("depends_on", []):
            if dep not in candidate_ids:
                issues.append(
                    _issue(
                        "ROADMAP_DEPENDENCY_UNKNOWN",
                        f"depends_on id '{dep}' does not match any candidate id",
                        item=cid,
                    )
                )
        if cid in candidate.get("depends_on", []):
            issues.append(_issue("ROADMAP_DEPENDENCY_SELF", "candidate depends on itself", item=cid))

        surfaces = candidate.get("required_surfaces")
        if surfaces != "default" and not _check_string_list(surfaces):
            issues.append(
                _issue(
                    "ROADMAP_REQUIRED_SURFACES_INVALID",
                    "required_surfaces must be 'default' or a non-empty list of strings",
                    item=cid,
                )
            )

        evidence = candidate.get("promotion_evidence")
        if not isinstance(evidence, list) or not all(isinstance(item, str) for item in evidence):
            issues.append(
                _issue(
                    "ROADMAP_EVIDENCE_INVALID",
                    "promotion_evidence must be a list of strings (empty allowed)",
                    item=cid,
                )
            )

        tripwires = candidate.get("tripwires")
        if not _check_string_list(tripwires) or not tripwires:
            issues.append(
                _issue(
                    "ROADMAP_TRIPWIRES_MISSING",
                    "every candidate must declare at least one promotion tripwire",
                    item=cid,
                )
            )

        if candidate["status"] in VALIDITY_ASSERTING_STATUSES and registry_statuses:
            for ref in registry_refs:
                ref_status = registry_statuses.get(ref)
                if ref_status is not None and ref_status not in REGISTRY_VALID_STATUSES:
                    issues.append(
                        _issue(
                            "ROADMAP_STATUS_LEAK",
                            f"candidate status '{candidate['status']}' requires registry "
                            f"entry '{ref}' to be experimental/adopted, found '{ref_status}'",
                            item=cid,
                        )
                    )

    decisions = data.get("rejected_or_deferred", [])
    if not isinstance(decisions, list):
        issues.append(_issue("ROADMAP_DECISIONS_INVALID", "rejected_or_deferred must be a list"))
        decisions = []
    for decision in decisions:
        if not isinstance(decision, dict):
            issues.append(
                _issue("ROADMAP_DECISION_NOT_A_MAPPING", "rejected_or_deferred entries must be mappings")
            )
            continue
        did = str(decision.get("id", "<missing id>"))
        missing_fields = REQUIRED_DECISION_FIELDS - set(decision)
        if missing_fields:
            issues.append(
                _issue(
                    "ROADMAP_DECISION_MISSING_FIELDS",
                    f"missing fields: {sorted(missing_fields)}",
                    item=did,
                )
            )
            continue
        if did in seen_ids:
            issues.append(_issue("ROADMAP_DUPLICATE_ID", "decision id collides with another id", item=did))
        seen_ids.add(did)
        for ref in decision.get("registry_refs", []):
            if registry_statuses and ref not in registry_statuses:
                issues.append(
                    _issue(
                        "ROADMAP_REGISTRY_REF_UNKNOWN",
                        f"registry_refs name '{ref}' not found in extension registry",
                        item=did,
                    )
                )

    return issues


def run(roadmap_path: Path | str, registry_path: Path | str, *, quiet: bool = False) -> int:
    roadmap = Path(roadmap_path)
    registry = Path(registry_path)
    issues = validate_roadmap(roadmap, registry)
    if issues:
        for issue in issues:
            item = f" item={issue['item']}" if "item" in issue else ""
            print(f"FAIL {issue['code']}{item}: {issue['message']}")
        return 1

    if not quiet:
        data = _load_yaml(roadmap)
        print(
            "future-branch roadmap ok "
            f"candidates={len(data.get('candidates', []))} "
            f"rejected_or_deferred={len(data.get('rejected_or_deferred', []))}"
        )
    return 0


def main() -> None:
    args = parse_args()
    raise SystemExit(run(args.roadmap, args.registry, quiet=args.quiet))


if __name__ == "__main__":
    main()
