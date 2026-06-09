from datetime import datetime, timedelta, timezone
import importlib.util
from pathlib import Path
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = ROOT / "adapters" / "egress" / "cot" / "zmeta_to_cot.py"
spec = importlib.util.spec_from_file_location("zmeta_to_cot_module", MODULE_PATH)
zmeta_to_cot_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(zmeta_to_cot_module)

# Use event-time mode so tests can assert against deterministic timestamps
_TEST_CONFIG = {"use_wall_clock": False}


def _expected_stale(ts: str, valid_for_ms: int) -> str:
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    dt = datetime.fromisoformat(ts).astimezone(timezone.utc)
    stale = dt + timedelta(milliseconds=valid_for_ms)
    return stale.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def test_zmeta_to_cot_returns_none_for_non_state():
    event = {"event": {"event_type": "OBSERVATION_EVENT"}}
    assert zmeta_to_cot_module.zmeta_to_cot(event) is None


def test_zmeta_to_cot_maps_state_event():
    event = {
        "event": {
            "event_type": "STATE_EVENT",
            "event_subtype": "TRACK_STATE",
            "event_id": "019c2b5c-c046-70e1-b6aa-34bf14c8a247",
            "ts": "2025-01-17T14:30:05Z",
        },
        "payload": {
            "track_id": "track-001",
            "geo": {"lat": 34.0524, "lon": -118.2435, "alt_m": 121.0},
            "valid_for_ms": 1500,
            "class": "a-f-G-U-C",
            "source_summary": ["rf", "eo"],
        },
        "confidence": 0.76,
    }

    xml_text = zmeta_to_cot_module.zmeta_to_cot(event, cot_config=_TEST_CONFIG)
    assert xml_text is not None

    root = ET.fromstring(xml_text)
    assert root.tag == "event"
    assert root.attrib["uid"] == "track-001"
    assert root.attrib["type"] == "a-f-G-U-C"
    assert root.attrib["how"] == "m-g"

    # Verify timestamps are derived from the event ts, not wall clock
    expected_stale = _expected_stale("2025-01-17T14:30:05Z", 1500)
    assert root.attrib["stale"] == expected_stale

    point = root.find("point")
    assert point is not None
    assert point.attrib["lat"] == "34.0524"
    assert point.attrib["lon"] == "-118.2435"
    assert point.attrib["hae"] == "121.0"

    detail = root.find("detail")
    assert detail is not None

    # Contact callsign present
    contact = detail.find("contact")
    assert contact is not None

    # Remarks include source summary
    remarks = detail.find("remarks")
    assert remarks is not None
    assert "rf" in remarks.text
    assert "eo" in remarks.text

    # __group element present for friendly CoT type
    group = detail.find("__group")
    assert group is not None
    assert group.attrib["name"] == "Cyan"


def test_zmeta_to_cot_no_geo_returns_none():
    event = {
        "event": {"event_type": "STATE_EVENT", "ts": "2025-01-17T14:30:05Z"},
        "payload": {"track_id": "track-001"},
    }
    assert zmeta_to_cot_module.zmeta_to_cot(event) is None


def test_zmeta_to_cot_rejects_state_with_raw_observation_fields():
    event = {
        "event": {
            "event_type": "STATE_EVENT",
            "event_subtype": "TRACK_STATE",
            "ts": "2025-01-17T14:30:05Z",
        },
        "payload": {
            "track_id": "track-raw",
            "geo": {"lat": 34.0, "lon": -118.0, "alt_m": 0},
            "valid_for_ms": 60000,
            "features": {"center_freq_hz": 2450000000},
        },
    }

    assert zmeta_to_cot_module.zmeta_to_cot(event, cot_config=_TEST_CONFIG) is None


def test_zmeta_to_cot_hostile_callsign_fallback():
    """Hostile tracks should never show raw track IDs as callsigns."""
    event = {
        "event": {
            "event_type": "STATE_EVENT",
            "event_subtype": "TRACK_STATE",
            "ts": "2025-01-17T14:30:05Z",
        },
        "payload": {
            "track_id": "torchai-track-abc123",
            "geo": {"lat": 34.0, "lon": -118.0, "alt_m": 0},
            "valid_for_ms": 60000,
            "class": "a-h-G",
        },
    }
    xml_text = zmeta_to_cot_module.zmeta_to_cot(event, cot_config=_TEST_CONFIG)
    assert xml_text is not None

    root = ET.fromstring(xml_text)
    contact = root.find(".//contact")
    assert contact is not None
    assert contact.attrib["callsign"] == "RF Emitter"

    labels = root.find(".//labels_on")
    assert labels is not None


def test_zmeta_to_cot_error_ellipse():
    """Error ellipse should map to CE/LE and precisionlocation."""
    event = {
        "event": {
            "event_type": "STATE_EVENT",
            "ts": "2025-01-17T14:30:05Z",
        },
        "payload": {
            "track_id": "emitter-01",
            "geo": {
                "lat": 43.49, "lon": -112.04, "alt_m": 1500,
                "error_ellipse_m": {
                    "semi_major": 150.0,
                    "semi_minor": 80.0,
                    "orientation_deg": 45.0,
                },
            },
            "valid_for_ms": 60000,
            "class": "a-h-G",
        },
    }
    xml_text = zmeta_to_cot_module.zmeta_to_cot(event, cot_config=_TEST_CONFIG)
    assert xml_text is not None

    root = ET.fromstring(xml_text)
    point = root.find("point")
    assert point.attrib["ce"] == "150.0"
    assert point.attrib["le"] == "80.0"

    precision = root.find(".//precisionlocation")
    assert precision is not None
    assert precision.attrib["ellipse_major"] == "150.0"


def test_zmeta_to_cot_heading_speed():
    """Heading and speed should produce a <track> element."""
    event = {
        "event": {
            "event_type": "STATE_EVENT",
            "ts": "2025-01-17T14:30:05Z",
        },
        "payload": {
            "track_id": "uav-01",
            "geo": {"lat": 43.49, "lon": -112.04, "alt_m": 100},
            "valid_for_ms": 30000,
            "class": "a-f-A-M-F-Q",
            "heading_deg": 135.0,
            "speed_mps": 12.5,
        },
    }
    xml_text = zmeta_to_cot_module.zmeta_to_cot(event, cot_config=_TEST_CONFIG)
    assert xml_text is not None

    root = ET.fromstring(xml_text)
    track = root.find(".//track")
    assert track is not None
    assert track.attrib["course"] == "135.0"
    assert track.attrib["speed"] == "12.5"


def test_zmeta_to_cot_uncertainty_circle():
    event = {
        "event": {
            "event_type": "STATE_EVENT",
            "event_subtype": "TRACK_STATE",
            "ts": "2025-01-17T14:30:05Z",
        },
        "payload": {
            "track_id": "track-001",
            "geo": {"lat": 34.0, "lon": -118.0, "alt_m": 0},
            "valid_for_ms": 1500,
        },
    }
    xml_text = zmeta_to_cot_module.zmeta_to_cot_uncertainty_circle(
        event, 500.0, cot_config=_TEST_CONFIG
    )
    assert xml_text is not None
    root = ET.fromstring(xml_text)
    circle = root.find(".//circle")
    assert circle is not None
    assert circle.attrib["radius"] == "500.0"


def test_zmeta_to_cot_confidence_only():
    """When no source_summary, confidence should appear in remarks."""
    event = {
        "event": {
            "event_type": "STATE_EVENT",
            "ts": "2025-01-17T14:30:05Z",
        },
        "payload": {
            "track_id": "track-002",
            "geo": {"lat": 34.0, "lon": -118.0, "alt_m": 0},
            "valid_for_ms": 5000,
        },
        "confidence": 0.85,
    }
    xml_text = zmeta_to_cot_module.zmeta_to_cot(event, cot_config=_TEST_CONFIG)
    assert xml_text is not None
    root = ET.fromstring(xml_text)
    remarks = root.find(".//remarks")
    assert remarks is not None
    assert "confidence=0.85" in remarks.text
