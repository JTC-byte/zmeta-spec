import importlib.util
import json
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = ROOT / "schema" / "zmeta-event-1.0.schema.json"
SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
# No format_checker: `date-time` is annotation-only without an RFC 3339 checker.
VALIDATOR = Draft202012Validator(SCHEMA)

MODULE_PATH = Path(__file__).resolve().parent / "eo_cv_to_zmeta.py"
spec = importlib.util.spec_from_file_location("eo_cv_to_zmeta", MODULE_PATH)
eo_cv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eo_cv)


_PARENT_EVENT_ID = "019c2b5c-c053-70e1-b6aa-340000000001"
_SECOND_PARENT_ID = "019c2b5c-c053-70e1-b6aa-340000000002"


def _detection(**overrides):
    detection = {
        "class_name": "vehicle",
        "confidence": 0.82,
        "gps": [34.0, -118.0],
        "altitude": 120.0,
        "timestamp": "2025-01-17T15:20:00+00:00",
        "source_event_id": _PARENT_EVENT_ID,
    }
    detection.update(overrides)
    return detection


def test_source_event_id_becomes_real_lineage():
    event = eo_cv.translate(_detection(), platform_id="camera-node-1")

    assert event["event"]["event_type"] == "INFERENCE_EVENT"
    assert event["lineage"]["based_on"] == [_PARENT_EVENT_ID]
    assert event["payload"]["based_on"] == [_PARENT_EVENT_ID]
    assert event["payload"]["claim"]["source_event_id"] == _PARENT_EVENT_ID
    VALIDATOR.validate(event)


def test_explicit_parent_event_ids_take_precedence():
    event = eo_cv.translate(
        _detection(),
        platform_id="camera-node-1",
        parent_event_ids=[_SECOND_PARENT_ID],
    )

    assert event["lineage"]["based_on"] == [_SECOND_PARENT_ID]
    assert event["payload"]["based_on"] == [_SECOND_PARENT_ID]
    VALIDATOR.validate(event)


def test_refuses_detection_without_any_parent_id():
    # INFERENCE_EVENT lineage must reference the real input observation
    # (contract 4.8 / 11.3). Without a schema-valid parent id the adapter
    # refuses to emit rather than fabricating one.
    detection = _detection()
    detection.pop("source_event_id")

    assert eo_cv.translate(detection, platform_id="camera-node-1") is None


def test_refuses_non_uuid_source_event_id():
    # A non-UUIDv7 upstream handle (e.g. a frame name) cannot be laundered
    # into lineage; it is preserved in the claim only via parent_event_ids
    # being absent -> refusal.
    detection = _detection(source_event_id="eo-frame-001")

    assert eo_cv.translate(detection, platform_id="camera-node-1") is None


def test_refuses_invalid_explicit_parent_ids():
    event = eo_cv.translate(
        _detection(),
        platform_id="camera-node-1",
        parent_event_ids=["not-a-uuid"],
    )

    assert event is None


def test_below_confidence_floor_still_refused():
    event = eo_cv.translate(
        _detection(confidence=0.1),
        platform_id="camera-node-1",
        confidence_floor=0.5,
    )

    assert event is None


def test_refuses_detection_without_confidence():
    # INFERENCE_EVENT schema-requires confidence; a quality metric is never
    # fabricated to satisfy it, so a detection missing confidence is
    # refused even with the default confidence_floor of 0.0.
    detection = _detection()
    detection.pop("confidence")

    assert eo_cv.translate(detection, platform_id="camera-node-1") is None


def test_refuses_null_confidence():
    event = eo_cv.translate(
        _detection(confidence=None),
        platform_id="camera-node-1",
    )

    assert event is None


def test_refuses_non_numeric_confidence():
    event = eo_cv.translate(
        _detection(confidence="0.82"),
        platform_id="camera-node-1",
    )

    assert event is None


def test_numeric_confidence_passes_through_unchanged():
    event = eo_cv.translate(_detection(confidence=0.9), platform_id="camera-node-1")

    assert event["confidence"] == 0.9
    VALIDATOR.validate(event)


def test_missing_altitude_omits_geo_entirely():
    # Canonical geo is all-or-nothing (contract 6.8): no altitude means no
    # claim.geo — the alt_m is never zero-filled.
    detection = _detection()
    detection.pop("altitude")

    event = eo_cv.translate(detection, platform_id="camera-node-1")

    assert "geo" not in event["payload"]["claim"]
    assert event["payload"]["claim"]["geo_source"] == "unavailable"
    VALIDATOR.validate(event)


def test_null_altitude_omits_geo_entirely():
    event = eo_cv.translate(
        _detection(altitude=None),
        platform_id="camera-node-1",
    )

    assert "geo" not in event["payload"]["claim"]
    assert event["payload"]["claim"]["geo_source"] == "unavailable"
    VALIDATOR.validate(event)


def test_zero_altitude_is_legitimate_not_falsy():
    event = eo_cv.translate(
        _detection(altitude=0.0),
        platform_id="camera-node-1",
    )

    assert event["payload"]["claim"]["geo"]["alt_m"] == 0.0
    assert event["payload"]["claim"]["geo_source"] == "detection"
    VALIDATOR.validate(event)
