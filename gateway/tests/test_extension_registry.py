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
    projection_behaviors = set(data["projection_behavior_values"])
    for entry in data["entries"]:
        assert entry["status"] in statuses
        assert entry["category"] in categories
        assert entry["profile_projection_behavior"] in projection_behaviors


def test_projection_risk_contract_fields_have_valid_types():
    data = load_registry()
    for entry in data["entries"]:
        assert isinstance(entry["risk_relevant"], bool), entry["name"]
        assert isinstance(entry["must_preserve_when_used_for_policy"], bool), entry["name"]
        assert isinstance(entry["security_privacy_notes"], list), entry["name"]
        assert isinstance(entry["fixture_references"], list), entry["name"]


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


def test_invalid_projection_behavior_fails():
    data = load_registry()
    data["entries"][0]["profile_projection_behavior"] = "strip_silently"
    path = write_registry("extension_registry_bad_projection_behavior", data)
    try:
        issues = validate_extension_registry.validate_registry(path)
        assert any(issue["code"] == "REGISTRY_PROJECTION_BEHAVIOR_INVALID" for issue in issues)
    finally:
        path.unlink(missing_ok=True)


def test_policy_preserved_extension_cannot_be_ignorable():
    data = load_registry()
    entry = data["entries"][0]
    entry["risk_relevant"] = True
    entry["must_preserve_when_used_for_policy"] = True
    entry["profile_projection_behavior"] = "preserve"
    entry["ignorable_by_default"] = True
    entry["security_privacy_notes"] = ["Policy-relevant regression fixture."]
    entry["fixture_references"] = ["conformance/profile-projection/must-pass.jsonl"]
    path = write_registry("extension_registry_policy_preserve_ignorable", data)
    try:
        issues = validate_extension_registry.validate_registry(path)
        assert any(issue["code"] == "REGISTRY_POLICY_PRESERVE_IGNORABLE" for issue in issues)
    finally:
        path.unlink(missing_ok=True)


def test_risk_relevant_extension_requires_fixture_references():
    data = load_registry()
    entry = data["entries"][0]
    entry["risk_relevant"] = True
    entry["profile_projection_behavior"] = "preserve"
    entry["security_privacy_notes"] = ["Risk-relevant regression fixture."]
    entry["fixture_references"] = []
    path = write_registry("extension_registry_risk_missing_fixtures", data)
    try:
        issues = validate_extension_registry.validate_registry(path)
        assert any(issue["code"] == "REGISTRY_RISK_FIXTURES_MISSING" for issue in issues)
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


def _registry_with(mutate, tmp_path):
    import copy
    data = copy.deepcopy(load_registry())
    mutate(data)
    path = tmp_path / "registry.yaml"
    import yaml as _yaml
    path.write_text(_yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return path


def test_a_note_that_parses_as_a_mapping_is_refused(tmp_path):
    # An unquoted note containing ": " loads as a one-key dict; the 2026-09-10
    # acoustic wave shipped one and the validator passed it silently.
    def mutate(data):
        data["entries"][0]["notes"] = [{"a note that became": "a mapping"}]
    issues = validate_extension_registry.validate_registry(_registry_with(mutate, tmp_path))
    assert any(i["code"] == "REGISTRY_LIST_ITEM_INVALID" for i in issues)


def test_a_stale_last_updated_stamp_is_refused(tmp_path):
    def mutate(data):
        data["last_updated"] = "2000-01-01"
    issues = validate_extension_registry.validate_registry(_registry_with(mutate, tmp_path))
    assert any(i["code"] == "REGISTRY_LAST_UPDATED_STALE" for i in issues)


def test_a_reserved_feature_contract_member_that_a_schema_declares_is_refused(tmp_path):
    # The 2026-09-12 acoustic pressure draft registered a name as reserved while
    # the same change made its fields schema-valid; the validator passed it.
    def mutate(data):
        for entry in data["entries"]:
            if entry["name"] == "ACOUSTIC_PRESSURE_LEVEL":
                entry["status"] = "reserved"
                entry["schema_status"] = "none"
                entry["conformance_status"] = "none"
                entry["review_state"] = "draft"
                break
        else:
            raise AssertionError("ACOUSTIC_PRESSURE_LEVEL is no longer in the registry")
    issues = validate_extension_registry.validate_registry(_registry_with(mutate, tmp_path))
    hits = [i for i in issues if i["code"] == "REGISTRY_RESERVED_SCHEMA_LEAK" and i.get("entry") == "ACOUSTIC_PRESSURE_LEVEL"]
    assert hits, issues
    assert any("pressure_pa" in i["message"] for i in hits), hits


def _entry(name):
    for entry in load_registry()["entries"]:
        if entry["name"] == name:
            return entry
    raise AssertionError(f"{name} is not in the registry")


def _both_schemas():
    return (
        validate_extension_registry._schema_validator(ROOT / "schema" / "zmeta-event-1.0.schema.json"),
        validate_extension_registry._schema_validator(ROOT / "schema" / "zmeta-event-1.1.0.schema.json"),
    )


def test_open_source_content_is_a_rejected_modality_and_no_schema_admits_it():
    # Rejected 2026-11-10. What a lookup of an identifier in open sources
    # yields is an inference with a receipt observation behind it, not a
    # modality. The validator's leak probe runs for reserved and proposed
    # entries only, so this test is what holds a rejected name out of both
    # schemas.
    entry = _entry("OSINT")
    assert entry["status"] == "rejected"
    assert entry["category"] == "observation_modality"
    assert entry["review_state"] == "approved"
    # The validator does not check a name in allowed_event_types against the
    # event-type vocabulary, so the empty list is pinned here.
    assert entry["allowed_event_types"] == []

    schema_v1, schema_v1_1 = _both_schemas()
    probe = validate_extension_registry.observation_event
    valid = validate_extension_registry._schema_valid
    # The probe validates for a live modality, so the refusals below belong
    # to the name and not to the probe's shape.
    assert valid(probe("RF", "1.0"), schema_v1)
    assert valid(probe("RF", "1.1.0"), schema_v1_1)
    assert not valid(probe("OSINT", "1.0"), schema_v1)
    assert not valid(probe("OSINT", "1.1.0"), schema_v1_1)


def test_external_records_collection_is_a_reserved_task_name_and_no_schema_admits_it():
    # Reserved 2026-11-10. The name is held for a task addressed to a
    # collector through the command path; it is not task vocabulary.
    entry = _entry("COLLECT_EXTERNAL_RECORDS")
    assert entry["status"] == "reserved"
    assert entry["category"] == "command_task_type"
    assert entry["allowed_event_types"] == ["COMMAND_EVENT"]
    assert entry["risk_relevant"] is True
    assert entry["security_privacy_notes"], "a risk-relevant entry states its security and privacy notes"
    assert entry["profile_projection_behavior"] == "future_branch_required"
    assert entry["schema_status"] == "none"
    assert entry["introduced_in"] is None

    schema_v1, schema_v1_1 = _both_schemas()
    probe = validate_extension_registry.command_event
    valid = validate_extension_registry._schema_valid
    # The probe validates for a live task type in each branch (HOLD in 1.0,
    # RETURN_TO_BASE in 1.1.0), so the refusals below belong to the name and
    # not to the probe's shape.
    assert valid(probe("HOLD", "1.0"), schema_v1)
    assert valid(probe("RETURN_TO_BASE", "1.1.0"), schema_v1_1)
    assert not valid(probe("COLLECT_EXTERNAL_RECORDS", "1.0"), schema_v1)
    assert not valid(probe("COLLECT_EXTERNAL_RECORDS", "1.1.0"), schema_v1_1)


def _status_counts_stated(text):
    """The counts the ontology reference states: (total, {status: count})."""
    import re

    flat = " ".join(text.split())
    match = re.search(r"Today's (\d+) entries split ([^.]+)\.", flat)
    assert match, "the ontology reference no longer carries the sentence \"Today's N entries split ...\""
    stated = {status: int(count) for count, status in re.findall(r"(\d+) ([a-z]+)", match.group(2))}
    return int(match.group(1)), stated


def test_the_ontology_reference_states_the_registry_counts_as_they_are():
    # The sentence is a hand-written count of a moving fact. It read 68
    # entries while the registry held 70 for the length of one edit on
    # 2026-11-10, which is the failure this test was seen to catch.
    from collections import Counter

    entries = load_registry()["entries"]
    actual = Counter(entry["status"] for entry in entries)
    text = (ROOT / "docs" / "zmeta_ontology_reference.md").read_text(encoding="utf-8")
    total, stated = _status_counts_stated(text)
    assert total == len(entries)
    assert stated == dict(actual)
    assert sum(stated.values()) == total


def test_the_count_readers_read_sentences_that_wrap_across_lines():
    total, stated = _status_counts_stated(
        "ladder. Today's 3 entries split 2 reserved,\n1\nrejected. The two adopted"
    )
    assert total == 3
    assert stated == {"reserved": 2, "rejected": 1}
    assert _probe_counts_stated("allowed event type, 4 of the\n9 reserved and\nproposed entries; names") == (4, 9)


def _probe_counts_stated(text):
    """What the ontology reference says the leak probe runs on: (probed, reserved and proposed)."""
    import re

    flat = " ".join(text.split())
    match = re.search(r"(\d+) of the (\d+) reserved and proposed entries", flat)
    assert match, "the ontology reference no longer says how many reserved and proposed entries the leak probe runs on"
    return int(match.group(1)), int(match.group(2))


def _names_the_leak_probe_runs_on():
    """The reserved and proposed entries for which the validator builds a probe.

    The validator's own function runs with its schema check wrapped, so the
    count follows what the validator does and not a copy of its predicates.
    """
    schema_v1, schema_v1_1 = _both_schemas()
    pending = [e for e in load_registry()["entries"] if e["status"] in ("reserved", "proposed")]
    calls = []
    real = validate_extension_registry._schema_valid

    def counting(event, validator):
        calls.append(1)
        return real(event, validator)

    probed = []
    validate_extension_registry._schema_valid = counting
    try:
        for entry in pending:
            calls.clear()
            validate_extension_registry._entry_context_checks(entry, schema_v1, schema_v1_1)
            feature_scopes = [s for s in (entry.get("payload_scope") or []) if str(s).startswith("payload.features.")]
            if calls or (entry["category"] == "observation_feature_contract" and feature_scopes):
                probed.append(entry["name"])
    finally:
        validate_extension_registry._schema_valid = real
    return probed, len(pending)


def test_the_ontology_reference_states_how_many_names_the_leak_probe_runs_on():
    # The sentence read 18 of 46 after the registry had grown to 47 reserved
    # and proposed entries. An independent review of 2026-11-10 found it, and
    # this test failed on it before the sentence was corrected.
    probed, pending = _names_the_leak_probe_runs_on()
    text = (ROOT / "docs" / "zmeta_ontology_reference.md").read_text(encoding="utf-8")
    assert _probe_counts_stated(text) == (len(probed), pending)
    # The wrapped check saw the two names the paragraph relies on, so an empty
    # or miscounted list cannot pass.
    assert "SEARCH_PATTERN" in probed
    assert "COLLECT_EXTERNAL_RECORDS" in probed
