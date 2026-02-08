import argparse
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GATEWAY_PATH = ROOT / "gateway" / "src" / "gateway.py"
spec = importlib.util.spec_from_file_location("zmeta_gateway", GATEWAY_PATH)
gateway = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gateway)


def parse_args():
    parser = argparse.ArgumentParser(description="Compute schema/policy/contract hash.")
    parser.add_argument(
        "--schema",
        default=str(ROOT / "schema" / "zmeta-event-1.0.schema.json"),
        help="Schema path",
    )
    parser.add_argument("--policy", default=str(ROOT / "policy"), help="Policy directory")
    return parser.parse_args()


def main():
    args = parse_args()
    schema_path = Path(args.schema)
    policy_dir = Path(args.policy)
    hashes = gateway.compute_contract_hash(schema_path, policy_dir)
    print(f"schema_hash={hashes['schema_hash']}")
    print(f"policy_hash={hashes['policy_hash']}")
    print(f"contract_hash={hashes['contract_hash']}")


if __name__ == "__main__":
    main()
