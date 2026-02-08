from datetime import datetime, timedelta, timezone
import importlib.util
from pathlib import Path
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = ROOT / "adapters" / "egress" / "cot" / "zmeta_to_cot.py"
spec = importlib.util.spec_from_file_location("zmeta_to_cot_module", MODULE_PATH)
zmeta_to_cot_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(zmeta_to_cot_module)


def _expected_stale(ts: str, valid_for_ms: int) -> str:
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    dt = datetime.fromisoformat(ts).astimezone(timezone.utc)
    stale = dt + timedelta(milliseconds=valid_for_ms)
    return stale.isoformat().replace("+00:00", "Z")


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

    xml_text = zmeta_to_cot_module.zmeta_to_cot(event)
    assert xml_text is not None

    root = ET.fromstring(xml_text)
    assert root.tag == "event"
    assert root.attrib["uid"] == "track-001"
    assert root.attrib["type"] == "a-f-G-U-C"
    assert root.attrib["time"] == "2025-01-17T14:30:05Z"
    assert root.attrib["start"] == "2025-01-17T14:30:05Z"
    assert root.attrib["stale"] == _expected_stale("2025-01-17T14:30:05Z", 1500)
    assert root.attrib["how"] == "m-g"

    point = root.find("point")
    assert point is not None
    assert point.attrib["lat"] == "34.0524"
    assert point.attrib["lon"] == "-118.2435"
    assert point.attrib["hae"] == "121.0"

    detail = root.find("detail")
    assert detail is not None
    remarks = detail.find("remarks")
    assert remarks is not None
    assert remarks.text == "confidence=0.76; source_summary=rf,eo"
