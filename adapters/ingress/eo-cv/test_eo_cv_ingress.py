import importlib.util
import json
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = ROOT / "schema" / "zmeta-event-1.0.schema.json"
SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
# No format_checker: `date-time` is annotation-only without an RFC 3339 checker.
VALIDATOR = Draft202012Validator(SCHEMA)
VALIDATOR_1_1_0 = Draft202012Validator(
    json.loads((ROOT / "schema" / "zmeta-event-1.1.0.schema.json").read_text(encoding="utf-8"))
)

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
        # The datum-qualified vertical: only a declared-HAE altitude reaches
        # canonical claim.geo.alt_m (contract 6.2, doctrine C1-01). The
        # legacy `altitude` key is exercised by the degrade tests below.
        "altitude_hae_m": 120.0,
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
    # Canonical geo is all-or-nothing (contract 6.8): no vertical of any
    # kind means no claim.geo — the alt_m is never zero-filled.
    detection = _detection()
    detection.pop("altitude_hae_m")

    event = eo_cv.translate(detection, platform_id="camera-node-1")

    assert "geo" not in event["payload"]["claim"]
    assert event["payload"]["claim"]["geo_source"] == "unavailable"
    VALIDATOR.validate(event)


def test_null_altitude_omits_geo_entirely():
    event = eo_cv.translate(
        _detection(altitude_hae_m=None),
        platform_id="camera-node-1",
    )

    assert "geo" not in event["payload"]["claim"]
    assert event["payload"]["claim"]["geo_source"] == "unavailable"
    VALIDATOR.validate(event)


def test_zero_altitude_is_legitimate_not_falsy():
    event = eo_cv.translate(
        _detection(altitude_hae_m=0.0),
        platform_id="camera-node-1",
    )

    assert event["payload"]["claim"]["geo"]["alt_m"] == 0.0
    assert event["payload"]["claim"]["geo_source"] == "detection"
    VALIDATOR.validate(event)


# The C1-01 altitude-datum boundary. The legacy keys carry no HAE claim: the
# detection's `altitude` declares no datum, and sensor_geo's `alt_m` is
# documented as a flight controller GPS position, whose global-position
# altitude MAVLink defines as MSL. Neither may reach canonical alt_m.


def test_legacy_altitude_key_never_reaches_canonical_alt_m():
    detection = _detection(altitude=120.0)
    detection.pop("altitude_hae_m")

    event = eo_cv.translate(detection, platform_id="camera-node-1")

    geo = event["payload"]["claim"]["geo"]
    assert geo == {"lat": 34.0, "lon": -118.0, "dimensionality": "2D"}
    assert "alt_m" not in geo
    assert event["payload"]["quality"]["eo_cv_alt_unspecified_datum_m"] == 120.0
    # No geo_status token: A1-02's VERTICAL_UNAVAILABLE is coupled to
    # payload.geo by the schema coherence rule, and this geo is claim-scoped.
    assert "geo_status" not in event["payload"]["quality"]
    assert event["zmeta_version"] == "1.1.0"
    VALIDATOR_1_1_0.validate(event)


def test_fc_fallback_msl_altitude_degrades_to_declared_2d():
    # The documented fc_fallback wiring: detection GPS is the (0,0) no-fix
    # sentinel, the FC position fills in. Its legacy alt_m is MSL, so the
    # position degrades to the declared 2-D form instead of publishing a
    # wrong-datum HAE claim (the fielded-honesty defect this pins against).
    detection = _detection(gps=[0, 0])
    detection.pop("altitude_hae_m")

    event = eo_cv.translate(
        detection,
        platform_id="camera-node-1",
        sensor_geo={"lat": 34.001, "lon": -118.001, "alt_m": 1450.0},
    )

    geo = event["payload"]["claim"]["geo"]
    assert geo == {"lat": 34.001, "lon": -118.001, "dimensionality": "2D"}
    assert "alt_m" not in geo
    assert event["payload"]["claim"]["geo_source"] == "fc_fallback"
    assert event["payload"]["quality"]["eo_cv_sensor_alt_msl_m"] == 1450.0
    assert "geo_status" not in event["payload"]["quality"]
    assert event["zmeta_version"] == "1.1.0"
    VALIDATOR_1_1_0.validate(event)


def test_fc_fallback_declared_hae_regains_canonical_alt_m():
    # A deployment that can assert HAE (e.g. from GPS_RAW_INT.alt_ellipsoid)
    # supplies alt_hae_m and keeps the full 3-D position under the 1.0 stamp.
    detection = _detection(gps=[0, 0])
    detection.pop("altitude_hae_m")

    event = eo_cv.translate(
        detection,
        platform_id="camera-node-1",
        sensor_geo={"lat": 34.001, "lon": -118.001, "alt_hae_m": 1433.0},
    )

    geo = event["payload"]["claim"]["geo"]
    assert geo == {"lat": 34.001, "lon": -118.001, "alt_m": 1433.0}
    assert event["payload"]["claim"]["geo_source"] == "fc_fallback"
    assert "quality" not in event["payload"]
    assert event["zmeta_version"] == "1.0"
    VALIDATOR.validate(event)


def test_extra_sensor_geo_keys_do_not_ride_into_claim_geo():
    # geo is built field-by-field: caller keys beyond the position never
    # reach claim.geo (the old dict(sensor_geo) copy forwarded everything).
    detection = _detection(gps=[0, 0])
    detection.pop("altitude_hae_m")

    event = eo_cv.translate(
        detection,
        platform_id="camera-node-1",
        sensor_geo={
            "lat": 34.001,
            "lon": -118.001,
            "alt_hae_m": 1433.0,
            "fix_type": 4,
        },
    )

    assert set(event["payload"]["claim"]["geo"].keys()) == {"lat", "lon", "alt_m"}
