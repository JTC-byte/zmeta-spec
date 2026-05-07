import copy
import importlib.util
import subprocess
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "conformance" / "conformance_classes.yaml"
REFERENCE_CLAIM_PATH = ROOT / "conformance" / "claims" / "example-reference-gateway.yaml"
CORE_PRODUCER_CLAIM_PATH = ROOT / "conformance" / "claims" / "example-core-producer.yaml"
VALIDATOR_PATH = ROOT / "tools" / "validate_conformance_classes.py"

spec = importlib.util.spec_from_file_location("zmeta_validate_conformance_classes", VALIDATOR_PATH)
validate_conformance_classes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validate_conformance_classes)


def load_yaml(path):
    return validate_conformance_classes.load_yaml(path)


def write_yaml(name, data):
    path = ROOT / "gateway" / "tests" / f"_{name}.yaml"
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


def test_manifest_yaml_loads():
    data = load_yaml(MANIFEST_PATH)
    assert data["manifest_version"] == 1
    assert isinstance(data["class_records"], list)
    assert len(data["class_records"]) >= 30


def test_required_top_level_keys_exist():
    data = load_yaml(MANIFEST_PATH)
    assert validate_conformance_classes.REQUIRED_TOP_LEVEL.issubset(data.keys())


def test_class_required_fields_exist():
    data = load_yaml(MANIFEST_PATH)
    required = validate_conformance_classes.REQUIRED_CLASS_FIELDS
    for record in data["class_records"]:
        assert required.issubset(record.keys()), record["class_id"]


def test_statuses_valid_and_class_ids_unique():
    data = load_yaml(MANIFEST_PATH)
    statuses = set(data["status_values"])
    class_ids = []
    for record in data["class_records"]:
        assert record["status"] in statuses
        class_ids.append(record["class_id"])
    assert len(class_ids) == len(set(class_ids))


def test_dependencies_are_valid():
    data = load_yaml(MANIFEST_PATH)
    class_ids = {record["class_id"] for record in data["class_records"]}
    for record in data["class_records"]:
        for dependency in record["dependencies"]:
            assert dependency in class_ids


def test_implemented_classes_have_test_commands():
    data = load_yaml(MANIFEST_PATH)
    for record in data["class_records"]:
        if record["status"] == "implemented":
            assert record["required_test_commands"], record["class_id"]


def test_future_reserved_planned_classes_are_not_claimable():
    data = load_yaml(MANIFEST_PATH)
    non_claimable = set(data["non_claimable_statuses"])
    for record in data["class_records"]:
        if record["class_id"] in {
            "ZMETA-ADAPTER",
            "ZMETA-AI-PROVENANCE",
            "ZMETA-VENDOR-EXTENSION",
        }:
            assert record["status"] in non_claimable


def test_current_manifest_validator_succeeds():
    issues = validate_conformance_classes.validate_manifest(MANIFEST_PATH)
    assert issues == []


def test_example_claims_validate():
    issues = validate_conformance_classes.validate_claims(
        [REFERENCE_CLAIM_PATH, CORE_PRODUCER_CLAIM_PATH],
        MANIFEST_PATH,
    )
    assert issues == []


def test_validator_cli_exits_success_for_manifest_and_claims():
    result = subprocess.run(
        [
            sys.executable,
            str(VALIDATOR_PATH),
            "--manifest",
            str(MANIFEST_PATH),
            "--claims",
            str(REFERENCE_CLAIM_PATH),
            str(CORE_PRODUCER_CLAIM_PATH),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0
    assert "conformance classes ok" in result.stdout


def test_synthetic_future_class_claim_fails():
    claim = load_yaml(CORE_PRODUCER_CLAIM_PATH)
    claim["classes_claimed"].append("ZMETA-AI-PROVENANCE")
    claim["class_claims"].append(
        {
            "class_id": "ZMETA-AI-PROVENANCE",
            "claim_status": "claimed",
            "commands": [],
            "result_summary": "synthetic bad claim",
            "limitations": [],
            "exceptions": [],
        }
    )
    path = write_yaml("conformance_claim_future", claim)
    try:
        issues = validate_conformance_classes.validate_claim(path, load_yaml(MANIFEST_PATH))
        assert any(issue["code"] == "CONFORMANCE_CLAIM_CLASS_NONCLAIMABLE" for issue in issues)
    finally:
        path.unlink(missing_ok=True)


def test_synthetic_claim_missing_dependency_fails():
    claim = load_yaml(CORE_PRODUCER_CLAIM_PATH)
    claim["classes_claimed"].remove("ZMETA-CORE")
    claim["class_claims"] = [
        class_claim for class_claim in claim["class_claims"] if class_claim["class_id"] != "ZMETA-CORE"
    ]
    path = write_yaml("conformance_claim_missing_dependency", claim)
    try:
        issues = validate_conformance_classes.validate_claim(path, load_yaml(MANIFEST_PATH))
        assert any(issue["code"] == "CONFORMANCE_CLAIM_DEPENDENCY_MISSING" for issue in issues)
    finally:
        path.unlink(missing_ok=True)


def test_synthetic_duplicate_class_id_manifest_fails():
    data = load_yaml(MANIFEST_PATH)
    data["class_records"].append(copy.deepcopy(data["class_records"][0]))
    path = write_yaml("conformance_manifest_duplicate", data)
    try:
        issues = validate_conformance_classes.validate_manifest(path)
        assert any(issue["code"] == "CONFORMANCE_DUPLICATE_CLASS_ID" for issue in issues)
    finally:
        path.unlink(missing_ok=True)


def test_synthetic_invalid_status_manifest_fails():
    data = load_yaml(MANIFEST_PATH)
    data["class_records"][0]["status"] = "active"
    path = write_yaml("conformance_manifest_bad_status", data)
    try:
        issues = validate_conformance_classes.validate_manifest(path)
        assert any(issue["code"] == "CONFORMANCE_STATUS_INVALID" for issue in issues)
    finally:
        path.unlink(missing_ok=True)


def test_synthetic_implemented_class_without_test_evidence_fails():
    data = load_yaml(MANIFEST_PATH)
    data["class_records"][0]["required_test_commands"] = []
    path = write_yaml("conformance_manifest_missing_tests", data)
    try:
        issues = validate_conformance_classes.validate_manifest(path)
        assert any(issue["code"] == "CONFORMANCE_TEST_COMMAND_MISSING" for issue in issues)
    finally:
        path.unlink(missing_ok=True)
