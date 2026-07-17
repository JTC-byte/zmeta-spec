"""Tests for the example-vendor worked-exercise ingress adapter."""

import importlib.util
import json
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PACK_TESTS = ROOT / "adapters" / "mapping-packs" / "example-vendor-pack" / "tests"

MODULE_PATH = Path(__file__).resolve().parent / "example_vendor_to_zmeta.py"
spec = importlib.util.spec_from_file_location("example_vendor_to_zmeta", MODULE_PATH)
example_vendor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(example_vendor)

PACK_INPUT = json.loads((PACK_TESTS / "input.json").read_text(encoding="utf-8"))
PACK_EXPECTED = json.loads((PACK_TESTS / "expected.json").read_text(encoding="utf-8"))

_PARENT_EVENT_ID = "019c2b5c-c053-70e1-b6aa-340000000001"


def test_detect_matches_pack_input():
    raw = json.dumps(PACK_INPUT).encode("utf-8")
    assert example_vendor.detect(raw) == example_vendor.SCHEMA_ID


def test_detect_rejects_foreign_payloads():
    assert example_vendor.detect(b"not json at all") is None
    assert example_vendor.detect(json.dumps({"foo": 1}).encode("utf-8")) is None


def test_translate_matches_pack_expected_mapping():
    events = example_vendor.translate(dict(PACK_INPUT), example_vendor.SCHEMA_ID)
    assert len(events) == 1
    event = events[0]

    assert event["zmeta_version"] == PACK_EXPECTED["zmeta_version"]
    assert event["event"]["event_type"] == PACK_EXPECTED["event"]["event_type"]
    assert event["event"]["event_subtype"] == PACK_EXPECTED["event"]["event_subtype"]
    assert event["event"]["ts"] == PACK_EXPECTED["event"]["ts"]
    assert event["source"] == PACK_EXPECTED["source"]
    assert event["payload"]["modality"] == PACK_EXPECTED["payload"]["modality"]
    assert event["payload"]["geo"] == PACK_EXPECTED["payload"]["geo"]
    assert event["payload"]["features"] == PACK_EXPECTED["payload"]["features"]


def test_translate_adds_contract_obligations_beyond_pack_fixture():
    event = example_vendor.translate(dict(PACK_INPUT), example_vendor.SCHEMA_ID)[0]

    # Fresh UUIDv7 identity, not the pack fixture's placeholder id.
    assert uuid.UUID(event["event"]["event_id"]).version == 7
    assert event["event"]["event_id"] != PACK_EXPECTED["event"]["event_id"]

    # Contract-required timing quality with the deliberately degraded fallback.
    timing = event["payload"]["timing_quality"]
    assert timing["time_source"] == "UNKNOWN"
    assert timing["sync_state"] == "UNSYNCED"
    assert timing["est_error_ms"] == 60_000

    # OBSERVATION_EVENT carries no confidence and no fabricated lineage.
    assert "confidence" not in event
    assert "lineage" not in event

    # No profile stamp: profile is gateway-added export metadata
    # (contract 3.4); the production reference adapters never stamp it.
    assert "profile" not in event


def test_translate_omits_geo_when_any_component_missing():
    reading = dict(PACK_INPUT)
    del reading["alt_m"]
    event = example_vendor.translate(reading, example_vendor.SCHEMA_ID)[0]
    assert "geo" not in event["payload"]


def test_translate_refuses_missing_required_keys():
    reading = dict(PACK_INPUT)
    del reading["center_freq_hz"]
    assert example_vendor.translate(reading, example_vendor.SCHEMA_ID) == []


def test_translate_refuses_missing_bandwidth():
    # The RF minimum feature set (contract 7.4) requires bandwidth_hz; a
    # reading without it must be refused, never emitted schema-invalid.
    reading = dict(PACK_INPUT)
    del reading["bandwidth_hz"]
    assert example_vendor.translate(reading, example_vendor.SCHEMA_ID) == []
    assert example_vendor.detect(json.dumps(reading).encode("utf-8")) is None

    reading = dict(PACK_INPUT)
    reading["bandwidth_hz"] = None
    assert example_vendor.translate(reading, example_vendor.SCHEMA_ID) == []


def test_translate_refuses_null_platform_id():
    # Identity is required semantics: a null platform_id must be refused,
    # never coerced into the fabricated string "None".
    reading = dict(PACK_INPUT)
    reading["platform_id"] = None
    assert example_vendor.translate(reading, example_vendor.SCHEMA_ID) == []


def test_translate_refuses_null_sensor_id():
    reading = dict(PACK_INPUT)
    reading["sensor_id"] = None
    assert example_vendor.translate(reading, example_vendor.SCHEMA_ID) == []


def test_translate_refuses_unparseable_timestamp():
    reading = dict(PACK_INPUT)
    reading["ts"] = "yesterday-ish"
    assert example_vendor.translate(reading, example_vendor.SCHEMA_ID) == []


def test_translate_refuses_wrong_schema_id():
    assert example_vendor.translate(dict(PACK_INPUT), "vendor:other:v1") == []


def test_caller_lineage_carries_translate_transform():
    event = example_vendor.translate(
        dict(PACK_INPUT), example_vendor.SCHEMA_ID, based_on=[_PARENT_EVENT_ID]
    )[0]
    assert event["lineage"]["based_on"] == [_PARENT_EVENT_ID]
    assert event["lineage"]["transform"] == (
        f"translate:{example_vendor.SCHEMA_ID}@{example_vendor.ADAPTER_VERSION}"
    )


def test_caller_timing_quality_is_preserved():
    timing = {
        "time_source": "GPS_PPS",
        "sync_state": "LOCKED",
        "est_error_ms": 1,
        "last_sync_ts": "2025-01-17T15:19:59Z",
    }
    event = example_vendor.translate(
        dict(PACK_INPUT), example_vendor.SCHEMA_ID, timing_quality=timing
    )[0]
    assert event["payload"]["timing_quality"] == timing


def test_validate_passes_locked_v1_schema():
    event = example_vendor.translate(dict(PACK_INPUT), example_vendor.SCHEMA_ID)[0]
    verdict, violations = example_vendor.validate(event)
    assert verdict == "pass"
    assert violations == []
