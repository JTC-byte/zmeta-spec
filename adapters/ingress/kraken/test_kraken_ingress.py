import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from adapters.ingress.kraken.kraken_to_zmeta import (
    translate_csv_row,
    translate_http_body,
    translate_json,
)


ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = ROOT / "schema" / "zmeta-event-1.0.schema.json"
SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
VALIDATOR = Draft202012Validator(SCHEMA, format_checker=FormatChecker())

CSV_FIELDS = ["1737127200.123", "123.4", "80", "-55.0", "433000000"]
JSON_RAW = {
    "timestamp_ms": 1737127200123,
    "bearing_deg": 123.4,
    "bearing_error_deg": 7.5,
    "power_dbm": -55.0,
    "center_freq_hz": 433000000.0,
}


def _csv_event(**kwargs):
    return translate_csv_row(CSV_FIELDS, platform_id="rf-node-1", **kwargs)


def _json_event(**kwargs):
    return translate_json(dict(JSON_RAW), platform_id="rf-node-1", **kwargs)


def test_csv_heading_compensation_rotates_doa_to_true_north():
    event = _csv_event(platform_heading_deg=90.0, array_offset_deg=0.0)

    assert event["payload"]["bearing"]["az_deg"] == pytest.approx(213.4)
    assert event["payload"]["quality"]["bearing_frame"] == "TRUE_NORTH"
    assert event["payload"]["features"]["doa_array_relative_deg"] == pytest.approx(123.4)


def test_csv_zero_heading_still_takes_compensated_path():
    # Heading 0.0 is a valid heading (north-facing fixed mount), not "absent":
    # the convert-or-omit pivot must be an `is None` check, never truthiness.
    event = _csv_event(platform_heading_deg=0.0)

    assert event["payload"]["bearing"]["az_deg"] == pytest.approx(123.4)
    assert event["payload"]["quality"]["bearing_frame"] == "TRUE_NORTH"


def test_csv_heading_compensation_wraps_past_360():
    fields = list(CSV_FIELDS)
    fields[1] = "300.0"
    event = translate_csv_row(fields, platform_id="rf-node-1", platform_heading_deg=120.0)

    assert event["payload"]["bearing"]["az_deg"] == pytest.approx(60.0)


def test_csv_negative_array_offset_applies_and_wraps():
    fields = list(CSV_FIELDS)
    fields[1] = "300.0"
    event = translate_csv_row(
        fields,
        platform_id="rf-node-1",
        platform_heading_deg=120.0,
        array_offset_deg=-30.0,
    )

    assert event["payload"]["bearing"]["az_deg"] == pytest.approx(30.0)
    assert event["payload"]["features"]["doa_array_relative_deg"] == pytest.approx(300.0)


def test_csv_without_heading_omits_canonical_bearing():
    event = _csv_event()

    assert "bearing" not in event["payload"]
    assert event["payload"]["features"]["doa_array_relative_deg"] == pytest.approx(123.4)
    assert "bearing_frame" not in event["payload"]["quality"]
    assert "heading_source" not in event["payload"]["quality"]


def test_csv_heading_source_propagates_to_quality():
    event = _csv_event(platform_heading_deg=90.0, heading_source="AHRS_TRUE")

    assert event["payload"]["quality"]["heading_source"] == "AHRS_TRUE"


def test_csv_heading_source_absent_when_not_given():
    event = _csv_event(platform_heading_deg=90.0)

    assert "heading_source" not in event["payload"]["quality"]


def test_csv_does_not_fabricate_snr():
    event = _csv_event(platform_heading_deg=90.0)

    assert "snr_db" not in event["payload"]["quality"]
    assert event["payload"]["features"]["power_dbm"] == pytest.approx(-55.0)


def test_json_heading_compensation_rotates_doa_to_true_north():
    event = _json_event(platform_heading_deg=90.0, heading_source="GPS_COURSE")

    assert event["payload"]["bearing"]["az_deg"] == pytest.approx(213.4)
    assert event["payload"]["quality"]["bearing_frame"] == "TRUE_NORTH"
    assert event["payload"]["quality"]["heading_source"] == "GPS_COURSE"
    assert event["payload"]["features"]["doa_array_relative_deg"] == pytest.approx(123.4)


def test_json_without_heading_omits_canonical_bearing():
    event = _json_event()

    assert "bearing" not in event["payload"]
    assert event["payload"]["features"]["doa_array_relative_deg"] == pytest.approx(123.4)
    assert "bearing_frame" not in event["payload"]["quality"]


def test_json_angular_error_preserved_in_both_paths():
    compensated = _json_event(platform_heading_deg=90.0)
    refused = _json_event()

    for event in (compensated, refused):
        assert event["payload"]["features"]["angular_error_deg"] == pytest.approx(7.5)
        assert event["payload"]["quality"]["measurement_error"]["value"] == pytest.approx(7.5)


def test_http_body_passes_heading_params_through():
    body = ",".join(CSV_FIELDS)
    events = translate_http_body(
        body,
        platform_id="rf-node-1",
        platform_heading_deg=90.0,
        array_offset_deg=0.0,
        heading_source="FIXED_MOUNT_SURVEYED",
    )

    assert len(events) == 1
    assert events[0]["payload"]["bearing"]["az_deg"] == pytest.approx(213.4)
    assert events[0]["payload"]["quality"]["heading_source"] == "FIXED_MOUNT_SURVEYED"


def test_events_validate_against_v1_0_schema():
    for event in (
        _csv_event(platform_heading_deg=90.0, heading_source="AHRS_TRUE"),
        _csv_event(),
        _json_event(platform_heading_deg=90.0, heading_source="GPS_COURSE"),
        _json_event(),
    ):
        VALIDATOR.validate(event)
