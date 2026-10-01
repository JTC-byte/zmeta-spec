"""Assemble a deployment policy directory from the reference policy plus variants.

configs/policy-variants/README.md describes the procedure this tool performs:
copy the reference policy directory, put each selected variant in place under
the filename the gateway reads, and recompute the deployment's hashes. The
output directory is what a deployment passes to the gateway as `policy_dir`
(or `--policy-dir`).

Each variant names its target by its leading filename: the target is the
reference policy YAML file whose name (without `.yaml`) is the longest prefix
of the variant's name that ends at a `.` or `-`, so
`command-evidence.strict.yaml` replaces `command-evidence.yaml`,
`timing-freshness-profile-L-degrade.yaml` replaces `timing-freshness.yaml`, and
`routingX.yaml` replaces nothing. `SOURCE=TARGET.yaml` names the target
explicitly; only the reference directory's `.yaml` files can be targets.

The tool refuses an output directory that is or lies inside the reference
policy directory, a path that exists and is not a directory, a directory that
already holds files, a variant that matches no reference file, and two
variants aimed at one file. It then loads
the assembled policy and runs the same lints as
`tools/lint_policy_risk_modes.py`; any finding is a failure and the directory
is left in place for inspection. The reference `policy/` directory is never
written.

Example:

    python tools/assemble_policy_dir.py --out build/policy-strict-command \\
        configs/policy-variants/command-evidence.strict.yaml \\
        configs/policy-variants/routing.command-origin.yaml
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GATEWAY_PATH = ROOT / "gateway" / "src" / "gateway.py"
VALIDATORS_PATH = ROOT / "gateway" / "src" / "validators.py"

_gw_spec = importlib.util.spec_from_file_location("zmeta_gateway", GATEWAY_PATH)
gateway = importlib.util.module_from_spec(_gw_spec)
_gw_spec.loader.exec_module(gateway)

_val_spec = importlib.util.spec_from_file_location("zmeta_validators", VALIDATORS_PATH)
validators = importlib.util.module_from_spec(_val_spec)
_val_spec.loader.exec_module(validators)


class AssemblyError(Exception):
    """A variant or output directory the tool refuses."""


def _stem_matches(stem: str, reference_stem: str) -> bool:
    """True when `stem` is `reference_stem` or starts with it followed by '.' or '-'.

    The boundary keeps `routingX.yaml` or `routing2.yaml` from silently
    replacing `routing.yaml`.
    """
    if stem == reference_stem:
        return True
    return stem.startswith(reference_stem) and stem[len(reference_stem)] in ".-"


def resolve_target(variant: str, reference_names: list[str]) -> tuple[Path, str]:
    """Return (source path, target filename) for one variant argument.

    Only the reference directory's `.yaml` files, the ones the gateway loads,
    can be replaced.
    """
    yaml_names = [name for name in reference_names if name.endswith(".yaml")]
    if "=" in variant:
        source_text, target = variant.rsplit("=", 1)
        source = Path(source_text)
        if target not in yaml_names:
            raise AssemblyError(
                f"{variant}: target {target!r} is not a policy YAML file of the reference directory"
            )
        return source, target
    source = Path(variant)
    stem = source.name[: -len(".yaml")] if source.name.endswith(".yaml") else source.name
    candidates = [name for name in yaml_names if _stem_matches(stem, name[: -len(".yaml")])]
    if not candidates:
        raise AssemblyError(
            f"{variant}: no reference policy file's name prefixes {source.name!r}; "
            "name the target as SOURCE=TARGET.yaml"
        )
    return source, max(candidates, key=len)


def assemble(out_dir: Path, variants: list[str], policy_dir: Path = ROOT / "policy") -> dict:
    """Build the deployment policy directory and return what was placed."""
    policy_dir = Path(policy_dir)
    out_dir = Path(out_dir)
    resolved_out, resolved_policy = out_dir.resolve(), policy_dir.resolve()
    # The gateway hashes the policy directory recursively, so an output
    # directory inside it would change the reference hash as surely as
    # writing the reference files themselves.
    if resolved_out == resolved_policy or resolved_policy in resolved_out.parents:
        raise AssemblyError(
            f"{out_dir} is the reference policy directory or inside it; "
            "writing there changes the reference policy hash"
        )
    if out_dir.exists() and not out_dir.is_dir():
        raise AssemblyError(f"{out_dir} exists and is not a directory")
    if out_dir.exists() and any(out_dir.iterdir()):
        raise AssemblyError(f"{out_dir} already holds files; choose an empty or new directory")

    reference_names = sorted(p.name for p in policy_dir.iterdir() if p.is_file())
    placements: dict[str, Path] = {}
    for variant in variants:
        source, target = resolve_target(variant, reference_names)
        if not source.is_file():
            raise AssemblyError(f"{variant}: no such file {source}")
        if target in placements:
            raise AssemblyError(
                f"{source} and {placements[target]} both replace {target}"
            )
        placements[target] = source

    # The whole tree, so the deployment hash covers what the reference hash
    # covers (the gateway hashes the policy directory recursively).
    shutil.copytree(policy_dir, out_dir, dirs_exist_ok=True)
    for target, source in placements.items():
        shutil.copyfile(source, out_dir / target)

    policy = validators.load_policy(out_dir)
    issues = validators.lint_policy_risk_modes(policy)
    issues += validators.lint_producer_authority_structure(policy)
    issues += validators.lint_routing_producer_enforcement_structure(policy)
    issues += validators.lint_policy_document_structure(out_dir)
    return {
        "out_dir": str(out_dir),
        "replaced": {target: str(source) for target, source in sorted(placements.items())},
        "lint_issues": issues,
    }


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Assemble a deployment policy directory from the reference policy plus variants."
    )
    parser.add_argument("--out", required=True, help="Output directory (new or empty).")
    parser.add_argument(
        "--policy", default=str(ROOT / "policy"), help="Reference policy directory."
    )
    parser.add_argument(
        "--schema",
        default=str(ROOT / "schema" / "zmeta-event-1.0.schema.json"),
        help=(
            "The schema_path the deployment's gateway loads, for the contract hash. "
            "The default matches the shipped configs and tools/compute_contract_hash.py; "
            "a gateway on the 1.1.0 lane passes schema/zmeta-event.schema.json."
        ),
    )
    parser.add_argument(
        "--semantics",
        default=str(ROOT / "spec" / "semantics-contract.md"),
        help="Semantic contract markdown path, for the contract hash.",
    )
    parser.add_argument("variants", nargs="+", help="Variant files, or SOURCE=TARGET.yaml.")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    try:
        result = assemble(Path(args.out), args.variants, Path(args.policy))
    except AssemblyError as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 2
    for target, source in result["replaced"].items():
        print(f"replaced {target} <- {source}")
    for issue in result["lint_issues"]:
        print(
            f"FAIL code={issue.get('code')} path={issue.get('path')} "
            f"message={issue.get('message')}"
        )
    if result["lint_issues"]:
        print(f"policy lint failed total={len(result['lint_issues'])}; {args.out} left for inspection")
        return 1
    hashes = gateway.compute_contract_hash(
        Path(args.schema), Path(args.out), Path(args.semantics)
    )
    print(json.dumps({"policy_dir": args.out, **hashes}, indent=2, sort_keys=True))
    print(
        "Set require_policy_hash / require_contract_hash in the deployment's gateway "
        "config to these values if it pins them."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
