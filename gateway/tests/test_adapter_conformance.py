import importlib.util
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = ROOT / "tools" / "validate_adapter_conformance.py"
FIXTURE_PATH = ROOT / "conformance" / "adapter-harness" / "must-pass.jsonl"

spec = importlib.util.spec_from_file_location("zmeta_validate_adapter_conformance", VALIDATOR_PATH)
validate_adapter_conformance = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validate_adapter_conformance)


def _fixture(name):
    for line in FIXTURE_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        if item.get("name") == name:
            return item
    raise AssertionError(f"fixture not found: {name}")


def test_adapter_conformance_run_succeeds():
    assert validate_adapter_conformance.run(fixtures_path=FIXTURE_PATH, quiet=True) == 0


def test_adapter_conformance_cli_exits_success():
    result = subprocess.run(
        [sys.executable, str(VALIDATOR_PATH), "--fixtures", str(FIXTURE_PATH), "--quiet"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "adapter conformance ok" in result.stdout


def test_adapter_conformance_detects_fixture_output_contract():
    schema = validate_adapter_conformance.validators.load_schema(
        ROOT / "schema" / "zmeta-event.schema.json"
    )
    policy = validate_adapter_conformance.validators.load_policy(ROOT / "policy")
    fixture = {
        "module": "adapters/ingress/klv/klv_to_zmeta_template.py",
        "callable": "klv_decoded_to_zmeta_observation",
        "args": [{"lat": 34.0, "lon": -118.0, "alt_m": 120.0}],
        "kwargs": {
            "platform_id": "platform-1",
            "sensor_id": "sensor-1",
            "producer": "klv:misb:0601",
            "ts": "2025-01-17T15:20:00+00:00",
            "based_on": ["019c2b5c-c053-70e1-b6aa-340000000001"],
        },
        "profile": "H",
        "expect": {
            "event_type": "OBSERVATION_EVENT",
            "event_subtype": "EO",
            "lineage_transform_prefix": "translate:klv@",
            "allow_degraded_timing": True,
        },
    }

    assert validate_adapter_conformance.evaluate_fixture(fixture, schema, policy) == []


def test_expected_values_match_produces_no_issues():
    event = {"payload": {"bearing": {"az_deg": 213.4}, "quality": {"bearing_frame": "TRUE_NORTH"}}}
    expect = {
        "utc_z_paths": [],
        "expected_values": {
            "payload.bearing.az_deg": 213.4,
            "payload.quality.bearing_frame": "TRUE_NORTH",
        },
    }

    assert validate_adapter_conformance._expectation_issues(event, expect) == []


def test_expected_values_mismatch_is_reported():
    event = {"payload": {"bearing": {"az_deg": 123.4}}}
    expect = {"utc_z_paths": [], "expected_values": {"payload.bearing.az_deg": 213.4}}

    issues = validate_adapter_conformance._expectation_issues(event, expect)

    assert [item["code"] for item in issues] == ["ADAPTER_EXPECTED_VALUE_MISMATCH"]
    assert issues[0]["path"] == "payload.bearing.az_deg"


def test_expected_values_non_numeric_mismatch_is_reported():
    event = {"payload": {"quality": {"bearing_frame": "ARRAY_RELATIVE"}}}
    expect = {"utc_z_paths": [], "expected_values": {"payload.quality.bearing_frame": "TRUE_NORTH"}}

    issues = validate_adapter_conformance._expectation_issues(event, expect)

    assert [item["code"] for item in issues] == ["ADAPTER_EXPECTED_VALUE_MISMATCH"]


def test_expected_values_missing_path_is_reported_with_distinct_code():
    event = {"payload": {"features": {}}}
    expect = {"utc_z_paths": [], "expected_values": {"payload.features.doa_array_relative_deg": 123.4}}

    issues = validate_adapter_conformance._expectation_issues(event, expect)

    assert [item["code"] for item in issues] == ["ADAPTER_EXPECTED_VALUE_MISSING"]
    assert issues[0]["path"] == "payload.features.doa_array_relative_deg"


def test_expected_values_numeric_comparison_uses_absolute_tolerance():
    within = {"payload": {"bearing": {"az_deg": 213.4 + 5e-7}}}
    beyond = {"payload": {"bearing": {"az_deg": 213.4 + 5e-6}}}
    expect = {"utc_z_paths": [], "expected_values": {"payload.bearing.az_deg": 213.4}}

    assert validate_adapter_conformance._expectation_issues(within, expect) == []
    issues = validate_adapter_conformance._expectation_issues(beyond, expect)
    assert [item["code"] for item in issues] == ["ADAPTER_EXPECTED_VALUE_MISMATCH"]


def test_expected_values_bool_pin_does_not_match_equal_number():
    bool_pin = {"utc_z_paths": [], "expected_values": {"payload.flag": True}}

    numeric_actual = {"payload": {"flag": 1.0}}
    issues = validate_adapter_conformance._expectation_issues(numeric_actual, bool_pin)
    assert [item["code"] for item in issues] == ["ADAPTER_EXPECTED_VALUE_MISMATCH"]

    bool_actual = {"payload": {"flag": True}}
    assert validate_adapter_conformance._expectation_issues(bool_actual, bool_pin) == []


def test_kraken_fixture_expected_values_prove_bearing_rotation():
    schema = validate_adapter_conformance.validators.load_schema(
        ROOT / "schema" / "zmeta-event.schema.json"
    )
    policy = validate_adapter_conformance.validators.load_policy(ROOT / "policy")
    fixture = _fixture("kraken-csv-rf-observation")

    expected_values = fixture["expect"]["expected_values"]
    assert expected_values["payload.bearing.az_deg"] == 213.4
    assert expected_values["payload.features.doa_array_relative_deg"] == 123.4
    assert expected_values["payload.quality.bearing_frame"] == "TRUE_NORTH"
    assert expected_values["payload.quality.heading_source"] == "AHRS_TRUE"

    assert validate_adapter_conformance.evaluate_fixture(fixture, schema, policy) == []


def test_conformance_runner_adapter_harness_flag_exits_success():
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "validate_conformance.py"),
            "--strict",
            "--adapter-harness",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "adapter conformance ok" in result.stdout
    assert "conformance ok" in result.stdout


def test_event_count_zero_pins_refusal():
    schema = validate_adapter_conformance.validators.load_schema(
        ROOT / "schema" / "zmeta-event.schema.json"
    )
    policy = validate_adapter_conformance.validators.load_policy(ROOT / "policy")
    fixture = _fixture("example-vendor-refuses-missing-bandwidth")

    assert validate_adapter_conformance.evaluate_fixture(fixture, schema, policy) == []


def test_event_count_mismatch_is_reported():
    schema = validate_adapter_conformance.validators.load_schema(
        ROOT / "schema" / "zmeta-event.schema.json"
    )
    policy = validate_adapter_conformance.validators.load_policy(ROOT / "policy")
    fixture = json.loads(json.dumps(_fixture("example-vendor-refuses-missing-bandwidth")))
    fixture["args"][0]["bandwidth_hz"] = 1000000

    issues = validate_adapter_conformance.evaluate_fixture(fixture, schema, policy)

    assert issues, "emission against an event_count 0 pin must fail"
    assert issues[0]["code"] == "ADAPTER_EVENT_COUNT_MISMATCH"


def test_event_count_invalid_value_is_a_fixture_error():
    schema = validate_adapter_conformance.validators.load_schema(
        ROOT / "schema" / "zmeta-event.schema.json"
    )
    policy = validate_adapter_conformance.validators.load_policy(ROOT / "policy")
    fixture = json.loads(json.dumps(_fixture("example-vendor-refuses-missing-bandwidth")))
    fixture["expect"]["event_count"] = True

    issues = validate_adapter_conformance.evaluate_fixture(fixture, schema, policy)

    assert issues and issues[0]["code"] == "ADAPTER_FIXTURE_INVALID"


def test_none_refusal_under_event_kind_passes_with_event_count_zero():
    # A single-event callable that refuses fabricated input returns None; the
    # harness must count that as zero events so event_count 0 pins the refusal.
    schema = validate_adapter_conformance.validators.load_schema(
        ROOT / "schema" / "zmeta-event.schema.json"
    )
    policy = validate_adapter_conformance.validators.load_policy(ROOT / "policy")
    fixture = _fixture("kraken-json-refuses-missing-center-freq")
    assert fixture["result"] == "event"

    assert validate_adapter_conformance.evaluate_fixture(fixture, schema, policy) == []


def test_none_refusal_under_event_kind_fails_event_count_one():
    schema = validate_adapter_conformance.validators.load_schema(
        ROOT / "schema" / "zmeta-event.schema.json"
    )
    policy = validate_adapter_conformance.validators.load_policy(ROOT / "policy")
    fixture = json.loads(json.dumps(_fixture("kraken-json-refuses-missing-center-freq")))
    fixture["expect"]["event_count"] = 1

    issues = validate_adapter_conformance.evaluate_fixture(fixture, schema, policy)

    assert issues, "a None return against event_count 1 must fail"
    assert issues[0]["code"] == "ADAPTER_EVENT_COUNT_MISMATCH"


def test_unpinned_none_refusal_under_event_kind_is_a_count_mismatch():
    # Without an explicit event_count, a single-event fixture implicitly
    # promises exactly one event: an adapter refusal (None) must fail rather
    # than let required_paths etc. pass vacuously against zero events.
    schema = validate_adapter_conformance.validators.load_schema(
        ROOT / "schema" / "zmeta-event.schema.json"
    )
    policy = validate_adapter_conformance.validators.load_policy(ROOT / "policy")
    fixture = json.loads(json.dumps(_fixture("kraken-json-refuses-missing-center-freq")))
    fixture["expect"] = {"required_paths": ["payload.modality"], "utc_z_paths": []}

    issues = validate_adapter_conformance.evaluate_fixture(fixture, schema, policy)

    assert issues, "an unpinned None return must not pass vacuously"
    assert issues[0]["code"] == "ADAPTER_EVENT_COUNT_MISMATCH"


def test_surplus_expect_events_entries_are_reported():
    # The audit probe: expect.events pins 2 events but the adapter returns 1.
    # Before the guard, index >= 1 expectations were silently never evaluated.
    schema = validate_adapter_conformance.validators.load_schema(
        ROOT / "schema" / "zmeta-event.schema.json"
    )
    policy = validate_adapter_conformance.validators.load_policy(ROOT / "policy")
    fixture = json.loads(json.dumps(_fixture("example-vendor-json-rf-observation")))
    fixture["expect"]["events"] = fixture["expect"]["events"] + [
        {"required_paths": ["payload.never_checked_before_this_guard"]}
    ]
    assert fixture["expect"]["event_count"] == 1

    issues = validate_adapter_conformance.evaluate_fixture(fixture, schema, policy)

    assert [item["code"] for item in issues] == ["ADAPTER_EXPECTATION_SURPLUS"]


def test_expect_events_without_event_count_is_a_fixture_error():
    schema = validate_adapter_conformance.validators.load_schema(
        ROOT / "schema" / "zmeta-event.schema.json"
    )
    policy = validate_adapter_conformance.validators.load_policy(ROOT / "policy")
    fixture = json.loads(json.dumps(_fixture("example-vendor-json-rf-observation")))
    del fixture["expect"]["event_count"]

    issues = validate_adapter_conformance.evaluate_fixture(fixture, schema, policy)

    assert issues and issues[0]["code"] == "ADAPTER_FIXTURE_INVALID"
    assert "event_count" in issues[0]["message"]
