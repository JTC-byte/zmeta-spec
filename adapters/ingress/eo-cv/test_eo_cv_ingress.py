import importlib.util
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = ROOT / "schema" / "zmeta-event-1.0.schema.json"
SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
VALIDATOR = Draft202012Validator(SCHEMA, format_checker=FormatChecker())

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
