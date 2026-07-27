"""Lint adapter-declared vocabulary mirrors against the governed schema enums.

Doctrine review log R1-11-16: adapter templates mirror governed enums by hand
because they are copied into bridges with no ZMeta repo alongside them, so
they cannot load the schema at runtime. Drift is fail-closed when the adapter
over-refuses a code the kernel allows, but fail-open when a mirror grows a
token the kernel never granted. Per the 2026-07-27 adjudication, such mirrors
are outer-ring and need no governance gate - but they MUST stay subsets of
the governed enum they mirror. This lint is the repo-side gate for that
subset rule: it costs the template nothing at runtime and closes the
fail-open direction for every registered adapter at once.

Standalone and advisory: not wired into validate_conformance or the kernel
gate (gate semantics are a maintainer call).
"""

from __future__ import annotations

import argparse
import ast
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

# Every mirror is held against ALL of these schemas: the adapter may refuse
# more than the kernel (fail-closed, covered by adapter pins), but a token
# the kernel never granted must never leave the adapter looking legal under
# either published schema version.
GOVERNED_SCHEMA_FILES = (
    "schema/zmeta-event-1.0.schema.json",
    "schema/zmeta-event-1.1.0.schema.json",
)

# The mirror registry. Each entry is one line: (adapter file relative to the
# repo root, module-level constant name, governed enum pointer). The pointer
# walks the schema JSON key by key; the one extension is
# `allOf[system_type=X]`, which selects the SystemPayload branch whose `if`
# discriminates on exactly that system_type - index-free, so adding or
# reordering branches never silently retargets the lint. Adding a future
# adapter mirror is one more tuple here.
_MAVLINK = "adapters/ingress/mavlink/mavlink_to_zmeta_template.py"
_SYSTEM = "$defs/SystemPayload"
MIRROR_REGISTRY = (
    (_MAVLINK, "_LINK_STATUS_STATES",
     f"{_SYSTEM}/allOf[system_type=LINK_STATUS]/then/properties/state/enum"),
    (_MAVLINK, "_LINK_STATUS_REASON_CODES",
     f"{_SYSTEM}/allOf[system_type=LINK_STATUS]/then/properties/metrics/properties/reason_code/enum"),
    (_MAVLINK, "_TASK_ACK_STATES",
     f"{_SYSTEM}/allOf[system_type=TASK_ACK]/then/properties/state/enum"),
    (_MAVLINK, "_TASK_ACK_REASON_CODES",
     f"{_SYSTEM}/allOf[system_type=TASK_ACK]/then/properties/metrics/properties/reason_code/enum"),
)

_BRANCH_SELECTOR = re.compile(r"^allOf\[system_type=([A-Za-z0-9_]+)\]$")


class LintError(RuntimeError):
    """Registry or schema resolution failure - always nonzero, never a pass."""


def resolve_enum_pointer(schema: dict, pointer: str) -> list[str]:
    """Walk `pointer` through `schema` and return the enum value list.

    An unresolvable segment raises LintError: a pointer that stopped
    resolving means the registry drifted from the schema, and that must
    never read as a clean lint.
    """
    node = schema
    for segment in pointer.strip("/").split("/"):
        selector = _BRANCH_SELECTOR.match(segment)
        if selector:
            system_type = selector.group(1)
            branches = node.get("allOf") if isinstance(node, dict) else None
            if not isinstance(branches, list):
                raise LintError(
                    f"pointer {pointer!r}: segment {segment!r} expects an allOf list"
                )
            # Match only the unconditional type branch: `if.properties` must
            # discriminate on system_type alone, so the conditional-obligation
            # branches (system_type + state) can never shadow it.
            matches = [
                branch
                for branch in branches
                if isinstance(branch, dict)
                and isinstance(branch.get("if"), dict)
                and isinstance(branch["if"].get("properties"), dict)
                and set(branch["if"]["properties"]) == {"system_type"}
                and isinstance(branch["if"]["properties"].get("system_type"), dict)
                and branch["if"]["properties"]["system_type"].get("const")
                == system_type
            ]
            if len(matches) != 1:
                raise LintError(
                    f"pointer {pointer!r}: expected exactly one allOf branch "
                    f"discriminating on system_type={system_type}, found {len(matches)}"
                )
            node = matches[0]
        elif isinstance(node, dict) and segment in node:
            node = node[segment]
        elif isinstance(node, list) and segment.isdigit() and int(segment) < len(node):
            node = node[int(segment)]
        else:
            raise LintError(
                f"pointer {pointer!r}: segment {segment!r} did not resolve"
            )
    if (
        not isinstance(node, list)
        or not node
        or not all(isinstance(value, str) for value in node)
    ):
        raise LintError(
            f"pointer {pointer!r} resolved to {type(node).__name__}, "
            "not a non-empty enum list of strings"
        )
    return node


def load_mirror_constant(adapter_path: Path, constant: str) -> tuple[str, ...]:
    """Read a module-level vocabulary constant from adapter source, read-only.

    Parsed via ast rather than imported so the lint never executes adapter
    code and never needs the adapter's runtime dependencies.
    """
    try:
        tree = ast.parse(adapter_path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError) as exc:
        raise LintError(f"{adapter_path}: cannot parse adapter source: {exc}") from exc
    # Runtime semantics are LAST-binding-wins, so the whole module body is
    # scanned and the LAST matching assignment is the one linted - a mirror
    # grown by rebinding must not hide behind its first, smaller literal.
    matched = None
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == constant
            for target in node.targets
        ):
            matched = node.value
        elif (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == constant
            and node.value is not None
        ):
            matched = node.value
        elif (
            isinstance(node, ast.AugAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == constant
        ):
            raise LintError(
                f"{adapter_path}: {constant} is augmented after assignment; "
                "the lint cannot see the runtime value"
            )
    if matched is None:
        raise LintError(f"{adapter_path}: no module-level constant {constant}")
    try:
        value = ast.literal_eval(matched)
    except ValueError as exc:
        raise LintError(
            f"{adapter_path}: {constant} is not a literal vocabulary: {exc}"
        ) from exc
    if (
        not isinstance(value, (tuple, list))
        or not value
        or not all(isinstance(member, str) for member in value)
    ):
        raise LintError(
            f"{adapter_path}: {constant} must be a non-empty tuple/list of strings"
        )
    return tuple(value)


def check_mirror_subset(
    *,
    adapter: str,
    constant: str,
    mirror_values: tuple[str, ...],
    enum_values: list[str],
    schema: str,
    pointer: str,
) -> list[dict]:
    """Return one issue per mirror value the governed enum does not carry.

    Value-by-value and in mirror order, so the diff names exactly which
    tokens the adapter invented. The missing direction (enum members the
    mirror lacks) is deliberately NOT an issue: an adapter may refuse more
    than the kernel, it must never pass more.
    """
    issues = []
    for value in mirror_values:
        if value in enum_values:
            continue
        issues.append(
            {
                "code": "ADAPTER_VOCABULARY_NOT_SUBSET",
                "adapter": adapter,
                "constant": constant,
                "value": value,
                "schema": schema,
                "pointer": pointer,
                "message": (
                    f"{constant} declares {value!r}; the governed enum at "
                    f"{schema}#{pointer} does not carry it, so the mirror is "
                    "not a subset"
                ),
            }
        )
    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Lint adapter-declared vocabulary mirrors: every mirror must be "
            "a subset of the governed schema enum it mirrors."
        )
    )
    parser.add_argument("--quiet", action="store_true", help="Only print failures.")
    return parser.parse_args()


def run(*, quiet: bool = False) -> int:
    issues = []
    try:
        schemas = {
            name: json.loads((ROOT / name).read_text(encoding="utf-8"))
            for name in GOVERNED_SCHEMA_FILES
        }
        for adapter, constant, pointer in MIRROR_REGISTRY:
            mirror_values = load_mirror_constant(ROOT / adapter, constant)
            for schema_name in GOVERNED_SCHEMA_FILES:
                enum_values = resolve_enum_pointer(schemas[schema_name], pointer)
                issues = issues + check_mirror_subset(
                    adapter=adapter,
                    constant=constant,
                    mirror_values=mirror_values,
                    enum_values=enum_values,
                    schema=schema_name,
                    pointer=pointer,
                )
    except (LintError, OSError, json.JSONDecodeError) as exc:
        # Resolution failure is its own loud fail-closed exit, never a pass
        # - including a missing or corrupt schema file, which must never
        # read as a clean lint.
        print(f"FAIL code=ADAPTER_VOCABULARY_LINT_ERROR message={exc}")
        print("adapter vocabulary lint failed total=1")
        return 1
    for issue in issues:
        print(
            "FAIL "
            f"code={issue['code']} "
            f"adapter={issue['adapter']} "
            f"constant={issue['constant']} "
            f"value={issue['value']} "
            f"schema={issue['schema']} "
            f"pointer={issue['pointer']} "
            f"message={issue['message']}"
        )
    if issues:
        print(f"adapter vocabulary lint failed total={len(issues)}")
        return 1
    if not quiet:
        print("adapter vocabulary lint ok")
    return 0


def main() -> None:
    args = parse_args()
    raise SystemExit(run(quiet=args.quiet))


if __name__ == "__main__":
    main()
