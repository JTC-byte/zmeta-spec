import copy
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "spec" / "extension-registry.yaml"
VALIDATOR_PATH = ROOT / "tools" / "validate_extension_registry.py"

spec = importlib.util.spec_from_file_location("zmeta_validate_extension_registry", VALIDATOR_PATH)
validate_extension_registry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validate_extension_registry)


def load_registry():
    return validate_extension_registry.load_registry(REGISTRY_PATH)


def write_registry(name, data):
    path = ROOT / "gateway" / "tests" / f"_{name}.yaml"
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


def write_json(name, data):
    path = ROOT / "gateway" / "tests" / f"_{name}.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_registry_yaml_loads():
    data = load_registry()
    assert data["registry_version"] == 1
    assert isinstance(data["entries"], list)
    assert len(data["entries"]) >= 56


def test_required_fields_exist():
    data = load_registry()
    required = validate_extension_registry.REQUIRED_ENTRY_FIELDS
    for entry in data["entries"]:
        assert required.issubset(entry.keys()), entry["name"]


def test_statuses_and_categories_are_valid():
    data = load_registry()
    statuses = set(data["status_values"])
    categories = set(data["category_values"])
    for entry in data["entries"]:
        assert entry["status"] in statuses
        assert entry["category"] in categories


def test_current_registry_validator_succeeds():
    issues = validate_extension_registry.validate_registry(REGISTRY_PATH)
    assert issues == []


def test_validator_cli_exits_success():
    result = subprocess.run(
        [
            sys.executable,
            str(VALIDATOR_PATH),
            "--registry",
            str(REGISTRY_PATH),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0
    assert "extension registry ok" in result.stdout


def test_duplicate_names_fail():
    data = load_registry()
    data["entries"].append(copy.deepcopy(data["entries"][0]))
    path = write_registry("extension_registry_duplicate", data)
    try:
        issues = validate_extension_registry.validate_registry(path)
        assert any(issue["code"] == "REGISTRY_DUPLICATE_NAME" for issue in issues)
    finally:
        path.unlink(missing_ok=True)


def test_reserved_entry_claiming_schema_implemented_fails():
    data = load_registry()
    for entry in data["entries"]:
        if entry["name"] == "RADAR":
            entry["schema_status"] = "implemented"
            break
    path = write_registry("extension_registry_reserved_implemented", data)
    try:
        issues = validate_extension_registry.validate_registry(path)
        assert any(issue["code"] == "REGISTRY_RESERVED_SCHEMA_IMPLEMENTED" for issue in issues)
    finally:
        path.unlink(missing_ok=True)


def test_adopted_entry_without_coverage_fails():
    data = load_registry()
    for entry in data["entries"]:
        if entry["name"] == "PNT_STATUS":
            entry["status"] = "adopted"
            entry["version_branch"] = "1.2.0"
            entry["schema_status"] = "none"
            entry["policy_status"] = "none"
            entry["conformance_status"] = "none"
            break
    path = write_registry("extension_registry_adopted_missing", data)
    try:
        issues = validate_extension_registry.validate_registry(path)
        codes = {issue["code"] for issue in issues}
        assert "REGISTRY_ADOPTED_SURFACE_MISSING" in codes
        assert "REGISTRY_ADOPTED_CONFORMANCE_MISSING" in codes
    finally:
        path.unlink(missing_ok=True)


def test_reserved_modalities_do_not_validate_as_observations():
    schema_v1 = validate_extension_registry._schema_validator(
        ROOT / "schema" / "zmeta-event-1.0.schema.json"
    )
    schema_v1_1 = validate_extension_registry._schema_validator(
        ROOT / "schema" / "zmeta-event-1.1.0.schema.json"
    )
    for modality in ["RADAR", "LIDAR", "MAGNETIC", "SEISMIC", "CYBER", "SIGINT"]:
        assert not validate_extension_registry._schema_valid(
            validate_extension_registry.observation_event(modality, "1.0"), schema_v1
        )
        assert not validate_extension_registry._schema_valid(
            validate_extension_registry.observation_event(modality, "1.1.0"), schema_v1_1
        )


def test_v1_1_command_task_types_do_not_validate_under_v1_0():
    schema_v1 = validate_extension_registry._schema_validator(
        ROOT / "schema" / "zmeta-event-1.0.schema.json"
    )
    for task_type in [
        "RETURN_TO_BASE",
        "LAND",
        "LOITER",
        "SCAN_RF",
        "TRACK_TARGET",
        "CHANGE_SENSOR_MODE",
    ]:
        assert not validate_extension_registry._schema_valid(
            validate_extension_registry.command_event(task_type, "1.0"), schema_v1
        )


def test_v1_1_system_status_types_do_not_validate_under_v1_0():
    schema_v1 = validate_extension_registry._schema_validator(
        ROOT / "schema" / "zmeta-event-1.0.schema.json"
    )
    for system_type in ["SENSOR_STATUS", "PLATFORM_STATUS"]:
        assert not validate_extension_registry._schema_valid(
            validate_extension_registry.system_event(system_type, "1.0"), schema_v1
        )


def test_takeoff_crosswalk_stray_is_not_current_vocabulary():
    assert "TAKEOFF" in validate_extension_registry.UNREGISTERED_RESERVED_SCHEMA_VALUES

    schema_v1 = validate_extension_registry._schema_validator(
        ROOT / "schema" / "zmeta-event-1.0.schema.json"
    )
    schema_v1_1 = validate_extension_registry._schema_validator(
        ROOT / "schema" / "zmeta-event-1.1.0.schema.json"
    )
    assert not validate_extension_registry._schema_valid(
        validate_extension_registry.command_event("TAKEOFF", "1.0"), schema_v1
    )
    assert not validate_extension_registry._schema_valid(
        validate_extension_registry.command_event("TAKEOFF", "1.1.0"), schema_v1_1
    )

    with (ROOT / "schema" / "zmeta-event-1.0.schema.json").open("r", encoding="utf-8") as handle:
        bad_schema = json.load(handle)
    bad_schema["x-audit-regression"] = {"enum": ["TAKEOFF"]}
    path = write_json("extension_registry_takeoff_schema", bad_schema)
    try:
        issues = validate_extension_registry.validate_registry(
            REGISTRY_PATH,
            schema_v1_path=path,
            schema_v1_1_path=ROOT / "schema" / "zmeta-event-1.1.0.schema.json",
        )
        assert any(issue["code"] == "REGISTRY_UNREGISTERED_SCHEMA_LEAK" for issue in issues)
    finally:
        path.unlink(missing_ok=True)
