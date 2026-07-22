from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

VALIDATORS_PATH = ROOT / "gateway" / "src" / "validators.py"
validators_spec = importlib.util.spec_from_file_location("zmeta_validators", VALIDATORS_PATH)
validators = importlib.util.module_from_spec(validators_spec)
validators_spec.loader.exec_module(validators)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Lint ZMeta policy risk modes for unsafe ignore settings."
    )
    parser.add_argument(
        "--policy-dir",
        default=str(ROOT / "policy"),
        help="Directory containing ZMeta policy YAML files.",
    )
    parser.add_argument("--quiet", action="store_true", help="Only print failures.")
    return parser.parse_args()


def run(*, policy_dir: Path | str | None = None, quiet: bool = False) -> int:
    resolved_dir = Path(policy_dir) if policy_dir else ROOT / "policy"
    policy = validators.load_policy(resolved_dir)
    issues = validators.lint_policy_risk_modes(policy)
    issues = issues + validators.lint_producer_authority_structure(policy)
    issues = issues + validators.lint_routing_producer_enforcement_structure(policy)
    # Document-level: a misspelled top-level wrapper key is unwrapped into the
    # loader's permissive default, so the in-memory lints above cannot see it.
    issues = issues + validators.lint_policy_document_structure(resolved_dir)
    for issue in issues:
        reasons = ",".join(issue.get("reason_codes", []))
        print(
            "FAIL "
            f"code={issue.get('code')} "
            f"path={issue.get('path')} "
            f"risk_dimension={issue.get('risk_dimension')} "
            f"reason_codes={reasons} "
            f"message={issue.get('message')}"
        )
    if issues:
        print(f"policy risk mode lint failed total={len(issues)}")
        return 1
    if not quiet:
        print("policy risk mode lint ok")
    return 0


def main() -> None:
    args = parse_args()
    raise SystemExit(run(policy_dir=args.policy_dir, quiet=args.quiet))


if __name__ == "__main__":
    main()
