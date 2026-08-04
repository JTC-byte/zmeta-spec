from datetime import datetime, timedelta, timezone
from decimal import Decimal
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
    # `how` is a derivation-pedigree claim; unasserted it is OMITTED, never
    # defaulted to "m-g" (attack-pass completion, 2026-07-27).
    assert "how" not in root.attrib

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
    """Error ellipse maps to a conservative circular CE only; LE is never
    derived from the horizontal ellipse, and no precisionlocation is emitted
    without a caller-asserted source (CR-02 / CR-11 pins below)."""
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
    assert point.attrib["le"] == "9999999.0"

    assert root.find(".//precisionlocation") is None


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


def test_zmeta_to_cot_confidence_with_source_summary():
    """Confidence must appear in remarks even when source_summary is present."""
    event = {
        "event": {
            "event_type": "STATE_EVENT",
            "ts": "2025-01-17T14:30:05Z",
        },
        "payload": {
            "track_id": "track-003",
            "geo": {"lat": 34.0, "lon": -118.0, "alt_m": 0},
            "valid_for_ms": 5000,
            "source_summary": ["rf", "acoustic"],
        },
        "confidence": 0.64,
    }
    xml_text = zmeta_to_cot_module.zmeta_to_cot(event, cot_config=_TEST_CONFIG)
    assert xml_text is not None
    root = ET.fromstring(xml_text)
    remarks = root.find(".//remarks")
    assert remarks is not None
    assert "rf" in remarks.text
    assert "acoustic" in remarks.text
    assert "confidence=0.64" in remarks.text


def test_zmeta_to_cot_default_path_uses_event_time():
    """No config: event time is authoritative, not wall clock (contract 9.5)."""
    event = {
        "event": {
            "event_type": "STATE_EVENT",
            "ts": "2025-01-17T14:30:05Z",
        },
        "payload": {
            "track_id": "track-004",
            "geo": {"lat": 34.0, "lon": -118.0, "alt_m": 0},
            "valid_for_ms": 5000,
        },
    }
    xml_text = zmeta_to_cot_module.zmeta_to_cot(event)
    assert xml_text is not None
    root = ET.fromstring(xml_text)
    assert root.attrib["time"] == "2025-01-17T14:30:05.000000Z"
    assert root.attrib["start"] == "2025-01-17T14:30:05.000000Z"
    assert root.attrib["stale"] == _expected_stale("2025-01-17T14:30:05Z", 5000)


def test_zmeta_to_cot_default_path_unknown_accuracy():
    """No config + no uncertainty: CoT unknown convention 9999999.0, never
    an invented accuracy figure."""
    event = {
        "event": {
            "event_type": "STATE_EVENT",
            "ts": "2025-01-17T14:30:05Z",
        },
        "payload": {
            "track_id": "track-005",
            "geo": {"lat": 34.0, "lon": -118.0, "alt_m": 0},
            "valid_for_ms": 5000,
        },
    }
    xml_text = zmeta_to_cot_module.zmeta_to_cot(event)
    assert xml_text is not None
    root = ET.fromstring(xml_text)
    point = root.find("point")
    assert point.attrib["ce"] == "9999999.0"
    assert point.attrib["le"] == "9999999.0"


def test_zmeta_to_cot_default_path_maps_error_ellipse():
    """No config: real error_ellipse_m still maps to a conservative CE;
    LE stays the unknown convention (the ellipse is purely horizontal)."""
    event = {
        "event": {
            "event_type": "STATE_EVENT",
            "ts": "2025-01-17T14:30:05Z",
        },
        "payload": {
            "track_id": "track-006",
            "geo": {
                "lat": 34.0, "lon": -118.0, "alt_m": 0,
                "error_ellipse_m": {
                    "semi_major": 42.0,
                    "semi_minor": 17.0,
                    "orientation_deg": 90.0,
                },
            },
            "valid_for_ms": 5000,
        },
    }
    xml_text = zmeta_to_cot_module.zmeta_to_cot(event)
    assert xml_text is not None
    root = ET.fromstring(xml_text)
    point = root.find("point")
    assert point.attrib["ce"] == "42.0"
    assert point.attrib["le"] == "9999999.0"


def test_zmeta_to_cot_absent_altitude_emits_unknown_convention():
    """Bare lat/lon: hae must be the CoT unknown-value convention, never a
    fabricated 0 m altitude claim."""
    event = {
        "event": {
            "event_type": "STATE_EVENT",
            "ts": "2025-01-17T14:30:05Z",
        },
        "payload": {
            "track_id": "track-008",
            "geo": {"lat": 34.0, "lon": -118.0},
            "valid_for_ms": 5000,
        },
    }
    xml_text = zmeta_to_cot_module.zmeta_to_cot(event, cot_config=_TEST_CONFIG)
    assert xml_text is not None
    root = ET.fromstring(xml_text)
    point = root.find("point")
    assert point.attrib["hae"] == "9999999.0"


def test_zmeta_to_cot_explicit_zero_altitude_stays_zero():
    """A legitimate alt_m of 0.0 is a real claim and must pass through."""
    event = {
        "event": {
            "event_type": "STATE_EVENT",
            "ts": "2025-01-17T14:30:05Z",
        },
        "payload": {
            "track_id": "track-009",
            "geo": {"lat": 34.0, "lon": -118.0, "alt_m": 0.0},
            "valid_for_ms": 5000,
        },
    }
    xml_text = zmeta_to_cot_module.zmeta_to_cot(event, cot_config=_TEST_CONFIG)
    assert xml_text is not None
    root = ET.fromstring(xml_text)
    point = root.find("point")
    assert point.attrib["hae"] == "0.0"


def test_zmeta_to_cot_real_altitude_maps_through():
    event = {
        "event": {
            "event_type": "STATE_EVENT",
            "ts": "2025-01-17T14:30:05Z",
        },
        "payload": {
            "track_id": "track-010",
            "geo": {"lat": 34.0, "lon": -118.0, "alt_m": 1500.5},
            "valid_for_ms": 5000,
        },
    }
    xml_text = zmeta_to_cot_module.zmeta_to_cot(event, cot_config=_TEST_CONFIG)
    assert xml_text is not None
    root = ET.fromstring(xml_text)
    point = root.find("point")
    assert point.attrib["hae"] == "1500.5"


def test_zmeta_to_cot_missing_ts_refuses_without_wall_clock():
    """Fail closed: no event.ts and wall-clock mode off must refuse (None),
    never silently stamp the current time (freshness fabrication)."""
    event = {
        "event": {
            "event_type": "STATE_EVENT",
            "event_subtype": "TRACK_STATE",
        },
        "payload": {
            "track_id": "track-011",
            "geo": {"lat": 34.0, "lon": -118.0, "alt_m": 100.0},
            "valid_for_ms": 5000,
        },
    }
    assert zmeta_to_cot_module.zmeta_to_cot(event) is None
    assert zmeta_to_cot_module.zmeta_to_cot(event, cot_config=_TEST_CONFIG) is None


def test_zmeta_to_cot_missing_ts_allowed_in_wall_clock_mode():
    """Wall-clock replay mode may stamp now - that is its documented purpose."""
    event = {
        "event": {
            "event_type": "STATE_EVENT",
            "event_subtype": "TRACK_STATE",
        },
        "payload": {
            "track_id": "track-012",
            "geo": {"lat": 34.0, "lon": -118.0, "alt_m": 100.0},
            "valid_for_ms": 5000,
        },
    }
    before = datetime.now(timezone.utc)
    xml_text = zmeta_to_cot_module.zmeta_to_cot(event, cot_config={"use_wall_clock": True})
    after = datetime.now(timezone.utc)
    assert xml_text is not None
    root = ET.fromstring(xml_text)
    stamped = datetime.fromisoformat(root.attrib["time"][:-1] + "+00:00")
    assert before <= stamped <= after


def test_zmeta_to_cot_wall_clock_opt_in():
    """use_wall_clock=True is the explicit replay-display mode: CoT time is
    re-stamped to the current wall clock, not the event timestamp."""
    event = {
        "event": {
            "event_type": "STATE_EVENT",
            "ts": "2025-01-17T14:30:05Z",
        },
        "payload": {
            "track_id": "track-007",
            "geo": {"lat": 34.0, "lon": -118.0, "alt_m": 0},
            "valid_for_ms": 5000,
        },
    }
    before = datetime.now(timezone.utc)
    xml_text = zmeta_to_cot_module.zmeta_to_cot(event, cot_config={"use_wall_clock": True})
    after = datetime.now(timezone.utc)
    assert xml_text is not None
    root = ET.fromstring(xml_text)
    time_attr = root.attrib["time"]
    stamped = datetime.fromisoformat(time_attr[:-1] + "+00:00")
    assert before <= stamped <= after
    assert time_attr != "2025-01-17T14:30:05.000000Z"


# R1-11 A-01: <point lat="nan" hae="inf"> renders on ATAK as an ordinary
# marker at a position that is not a position - no uncertainty label, no
# violation code, nothing an operator can filter on. Every number that
# becomes a CoT attribute must refuse, not just lat/lon.
_NON_FINITE = (float("nan"), float("inf"), float("-inf"))


def _nf_state_event():
    return {
        "zmeta_version": "1.0",
        "event": {
            "event_id": "019c2b5c-c047-73ea-8f1a-302b9d9c0aa4",
            "event_type": "STATE_EVENT",
            "event_subtype": "TRACK_STATE",
            "ts": "2025-01-17T15:20:00Z",
        },
        "source": {"platform_id": "node-1", "node_role": "EDGE", "producer": "p"},
        "payload": {
            "track_id": "track-1",
            "geo": {"lat": 34.0, "lon": -118.0, "alt_m": 120.0},
            "valid_for_ms": 1000,
            "heading_deg": 90.0,
            "speed_mps": 12.0,
        },
        "confidence": 0.9,
    }


def test_zmeta_to_cot_refuses_every_non_finite_attribute():
    for path in (
        ("payload", "geo", "lat"),
        ("payload", "geo", "lon"),
        ("payload", "geo", "alt_m"),
        ("payload", "valid_for_ms"),
        ("payload", "heading_deg"),
        ("payload", "speed_mps"),
        ("confidence",),
    ):
        for value in _NON_FINITE:
            event = _nf_state_event()
            node = event
            for part in path[:-1]:
                node = node[part]
            node[path[-1]] = value
            assert (
                zmeta_to_cot_module.zmeta_to_cot(event, cot_config=_TEST_CONFIG) is None
            ), (path, value)


def test_zmeta_to_cot_refuses_non_finite_error_ellipse():
    for key in ("semi_major", "semi_minor", "orientation_deg"):
        for value in _NON_FINITE:
            event = _nf_state_event()
            event["payload"]["geo"]["error_ellipse_m"] = {
                "semi_major": 50.0,
                "semi_minor": 25.0,
                "orientation_deg": 45.0,
            }
            event["payload"]["geo"]["error_ellipse_m"][key] = value
            assert (
                zmeta_to_cot_module.zmeta_to_cot(event, cot_config=_TEST_CONFIG) is None
            ), (key, value)


def test_zmeta_to_cot_refuses_non_finite_config_accuracy_defaults():
    # An operator-supplied accuracy default is read on the map exactly like an
    # event-supplied one.
    for key in ("default_ce", "default_le"):
        for value in _NON_FINITE:
            config = dict(_TEST_CONFIG)
            config[key] = value
            assert (
                zmeta_to_cot_module.zmeta_to_cot(_nf_state_event(), cot_config=config)
                is None
            ), (key, value)


def test_uncertainty_circle_refuses_non_finite_radius():
    # `radius <= 0` alone cannot see NaN: every comparison with NaN is False.
    for value in _NON_FINITE:
        assert (
            zmeta_to_cot_module.zmeta_to_cot_uncertainty_circle(
                _nf_state_event(), value, cot_config=_TEST_CONFIG
            )
            is None
        ), value
    assert (
        zmeta_to_cot_module.zmeta_to_cot_uncertainty_circle(
            _nf_state_event(), 500.0, cot_config=_TEST_CONFIG
        )
        is not None
    )


def test_zmeta_to_cot_clean_event_still_renders():
    xml_text = zmeta_to_cot_module.zmeta_to_cot(_nf_state_event(), cot_config=_TEST_CONFIG)
    assert xml_text is not None
    assert "nan" not in xml_text.lower()
    assert 'lat="34.0"' in xml_text


# R1-11, second pass. The guard above was FIELD scoped - a list of nine
# candidate numbers - which is the same structure A-01 names as the defect,
# and the list was already short. These pin the value-scoped replacement, and
# each one passes with the field list restored only if the field list happens
# to name that field, which is the point.


def test_zmeta_to_cot_refuses_a_non_finite_in_remarks_source_summary():
    # payload.source_summary members are stringified into <remarks>, so a NaN
    # rendered as the literal token "nan" in operator-facing text. It was not
    # in the field list, and no field list would have caught it: it is not a
    # number field, it is a list of anything.
    event = _nf_state_event()
    event["payload"]["source_summary"] = ["rf-sensor", float("nan")]
    assert zmeta_to_cot_module.zmeta_to_cot(event, cot_config=_TEST_CONFIG) is None


def test_zmeta_to_cot_refuses_an_error_ellipse_key_nobody_listed():
    # The guard must not go stale when the uncertainty block grows a key.
    event = _nf_state_event()
    event["payload"]["geo"]["error_ellipse_m"] = {
        "semi_major": 50.0,
        "semi_minor": 25.0,
        "orientation_deg": 45.0,
        "cep_m": float("nan"),
    }
    assert zmeta_to_cot_module.zmeta_to_cot(event, cot_config=_TEST_CONFIG) is None


def test_zmeta_to_cot_refuses_a_non_finite_quality_value():
    # payload.quality is the event's own honesty label. CoT does not render it
    # today, but an event whose uncertainty is not a number is not an event
    # the kernel accepts either, and CoT must not be the one surface that
    # renders what every other consumer refuses.
    event = _nf_state_event()
    event["payload"]["quality"] = {"pos_sigma_m": float("nan")}
    assert zmeta_to_cot_module.zmeta_to_cot(event, cot_config=_TEST_CONFIG) is None


def test_zmeta_to_cot_refuses_a_non_finite_config_stale_interval():
    # default_valid_for_ms feeds timedelta(), so before the fix this escaped
    # as a RAW ValueError / OverflowError out of an adapter whose documented
    # failure signal is None - a crash where a counted cot_skipped was due.
    event = _nf_state_event()
    del event["payload"]["valid_for_ms"]
    for value in _NON_FINITE:
        config = dict(_TEST_CONFIG)
        config["default_valid_for_ms"] = value
        assert zmeta_to_cot_module.zmeta_to_cot(event, cot_config=config) is None, value


def test_zmeta_to_cot_refuses_non_finite_inside_a_decoded_cbor_container():
    # The CBOR backends decode tag 258 into a set and an unknown tag into a
    # wrapper object; neither is a dict or a list, so a dict/list walk never
    # looks inside them.
    class _Tag:
        def __init__(self, tag, value):
            self.tag = tag
            self.value = value

    for blob in ({1.0, float("nan")}, frozenset({float("inf")}), _Tag(4242, [float("nan")])):
        event = _nf_state_event()
        event["payload"]["source_summary"] = [blob]
        assert zmeta_to_cot_module.zmeta_to_cot(event, cot_config=_TEST_CONFIG) is None


def test_zmeta_to_cot_still_projects_when_only_a_vendor_extension_is_dirty():
    # The deliberate limit of the scope, pinned so it is not widened by
    # accident. payload.extensions is namespaced vendor content this adapter
    # never reads and never renders. Refusing the operator's track because a
    # provenance blob carried a NaN would destroy good canonical data over
    # content CoT does not project - the escalation this repo had to repair in
    # the SAPIENT ingress adapter in the same audit.
    event = _nf_state_event()
    event["payload"]["extensions"] = {"acme.telemetry": {"battery_v": float("nan")}}
    xml_text = zmeta_to_cot_module.zmeta_to_cot(event, cot_config=_TEST_CONFIG)
    assert xml_text is not None
    assert "nan" not in xml_text.lower()


def test_zmeta_to_cot_guard_terminates_on_a_cyclic_payload():
    # CBOR value-sharing tags make a decoded event possibly cyclic. A walk
    # without a seen-set here would be a hang on the egress path.
    event = _nf_state_event()
    loop = {"lat": 1.0}
    loop["self"] = loop
    event["payload"]["source_summary"] = [loop]
    assert zmeta_to_cot_module.zmeta_to_cot(event, cot_config=_TEST_CONFIG) is not None


def test_zmeta_to_cot_guard_accepts_extreme_but_legal_floats():
    # Refusing a legitimate float64 would be its own honesty failure.
    event = _nf_state_event()
    event["payload"]["geo"]["alt_m"] = 1e308
    event["payload"]["speed_mps"] = 5e-324
    assert zmeta_to_cot_module.zmeta_to_cot(event, cot_config=_TEST_CONFIG) is not None


def test_zmeta_to_cot_guard_does_not_convert_huge_ints():
    # math.isfinite() on an int outside float64 range raises OverflowError;
    # a legal JSON integer literal must not crash the projection.
    event = _nf_state_event()
    event["payload"]["source_summary"] = [10 ** 400]
    assert zmeta_to_cot_module.zmeta_to_cot(event, cot_config=_TEST_CONFIG) is not None


# R1-11, third pass (R2-05 / R2-06). Two members of the same class the pass
# above closed only halfway: an adapter whose documented failure signal is
# None must not raise, and a guard branch nothing exercises is not a guard.


def test_is_non_finite_sees_a_decimal_nan():
    # R2-06. cbor2 decodes CBOR tag 4/5 into a Decimal, and Decimal('NaN') is
    # not a float, so `isinstance(x, float)` alone never sees it. This is the
    # unit-level twin of the projection pin below: deleting the two Decimal
    # lines from _is_non_finite left 33/33 CoT tests green because NOTHING in
    # this file mentioned Decimal.
    for token in ("NaN", "sNaN", "Infinity", "-Infinity"):
        assert zmeta_to_cot_module._is_non_finite(Decimal(token)) is True, token
    for token in ("0", "-118.2435", "1E+308"):
        assert zmeta_to_cot_module._is_non_finite(Decimal(token)) is False, token


def test_zmeta_to_cot_refuses_a_decimal_non_finite_on_a_rendered_attribute():
    # R2-06 at the boundary that matters: without the Decimal arm this puts
    # <point lat="NaN"> on the TAK wire - an ordinary marker at a position
    # that is not a position, carrying nothing an operator can filter on.
    for path in (
        ("payload", "geo", "lat"),
        ("payload", "geo", "lon"),
        ("payload", "geo", "alt_m"),
        ("payload", "heading_deg"),
        ("payload", "speed_mps"),
        ("confidence",),
    ):
        for token in ("NaN", "Infinity", "-Infinity"):
            event = _nf_state_event()
            target = event
            for key in path[:-1]:
                target = target[key]
            target[path[-1]] = Decimal(token)
            xml_text = zmeta_to_cot_module.zmeta_to_cot(event, cot_config=_TEST_CONFIG)
            assert xml_text is None, (path, token, xml_text)


def test_zmeta_to_cot_refuses_a_decimal_non_finite_nested_in_a_container():
    # The Decimal arm and the container walk are separate mechanisms; a leaf
    # pin on a top-level attribute passes even if the walk never descends.
    event = _nf_state_event()
    event["payload"]["source_summary"] = ["rf-sensor", {"cep": Decimal("NaN")}]
    assert zmeta_to_cot_module.zmeta_to_cot(event, cot_config=_TEST_CONFIG) is None


def test_zmeta_to_cot_still_renders_a_finite_decimal():
    # The refusal must be about non-finiteness, not about the type. A
    # Decimal carrying a real number is a real number.
    event = _nf_state_event()
    event["payload"]["geo"]["alt_m"] = Decimal("120.5")
    assert zmeta_to_cot_module.zmeta_to_cot(event, cot_config=_TEST_CONFIG) is not None


# --- R2-05: the stale interval, class-enumerated from the expression ---
#
# `payload.valid_for_ms` is {"type": "integer", "minimum": 1} with NO upper
# bound (schema/zmeta-event-1.0.schema.json), and `event.ts` is any RFC3339
# instant, so all three of these pass the gateway's outgoing gate with zero
# violations and then hit `time + timedelta(milliseconds=valid_for_ms)`.
# Each raised a different OverflowError out of an adapter documented to
# return None. The gateway's per-datagram backstop swallowed it as an
# uncounted INTERNAL_ERROR drop AFTER the event had already been forwarded,
# so the operator lost the counted, reason-tagged cot_skipped record the
# README promises for exactly this case.

_UNREPRESENTABLE_STALE = (
    # (ts, valid_for_ms, why)
    ("2025-01-17T15:20:00Z", 10 ** 400, "int too large to convert to C int"),
    ("2025-01-17T15:20:00Z", 10 ** 15, "date value out of range"),
    ("9999-12-31T23:59:59Z", 300000, "ordinary 5 min stale on a legal late ts"),
)


def test_zmeta_to_cot_refuses_an_unrepresentable_stale_instead_of_raising():
    for ts, valid_for_ms, why in _UNREPRESENTABLE_STALE:
        event = _nf_state_event()
        event["event"]["ts"] = ts
        event["payload"]["valid_for_ms"] = valid_for_ms
        result = zmeta_to_cot_module.zmeta_to_cot(event, cot_config=_TEST_CONFIG)
        assert result is None, (ts, valid_for_ms, why, result)


def test_zmeta_to_cot_refuses_an_unrepresentable_config_stale_interval():
    # The config default reaches the same expression, and the README states
    # outright that a default_valid_for_ms "that would otherwise raise out of
    # the adapter" is covered. The non-finite arm of that promise was kept;
    # the integer arm was not.
    for valid_for_ms in (10 ** 400, 10 ** 15):
        event = _nf_state_event()
        del event["payload"]["valid_for_ms"]
        config = dict(_TEST_CONFIG)
        config["default_valid_for_ms"] = valid_for_ms
        result = zmeta_to_cot_module.zmeta_to_cot(event, cot_config=config)
        assert result is None, (valid_for_ms, result)


def test_zmeta_to_cot_refusal_is_a_refusal_not_a_substituted_default():
    # The failure mode this fix must NOT have: quietly falling back to the
    # 300000 ms default would publish a freshness bound the event never
    # claimed. Nothing may come out of the adapter for these inputs.
    event = _nf_state_event()
    event["payload"]["valid_for_ms"] = 10 ** 400
    assert zmeta_to_cot_module.zmeta_to_cot(event) is None
    assert zmeta_to_cot_module.zmeta_to_cot(event, cot_config={"use_wall_clock": True}) is None


def test_zmeta_to_cot_still_projects_a_large_but_representable_stale():
    # Proportionality: the refusal is scoped to windows datetime cannot
    # express, not to windows that merely look big. ~1000 years is fine.
    event = _nf_state_event()
    event["payload"]["valid_for_ms"] = 31_536_000_000_000
    xml_text = zmeta_to_cot_module.zmeta_to_cot(event, cot_config=_TEST_CONFIG)
    assert xml_text is not None
    assert 'stale="3024-05-20T15:20:00' in xml_text


# R1-11 cold re-read: CR-02 (semi_minor -> point@le fabricated a vertical
# bound the event never claimed), CR-11 (unconditional geopointsrc="GPS"
# altsrc="GPS" fabricated source pedigree on fusion products), and the banked
# _parse_utc MAJOR (a gate-clean malformed ts escaped as a raw ValueError out
# of an adapter whose documented failure signal is None).


def _ellipse_event():
    return {
        "event": {
            "event_type": "STATE_EVENT",
            "event_subtype": "TRACK_STATE",
            "ts": "2026-01-17T14:30:05Z",
        },
        "payload": {
            "track_id": "emitter-01",
            "class": "a-h-G",
            "geo": {
                "lat": 43.49, "lon": -112.04, "alt_m": 1500,
                "error_ellipse_m": {
                    "semi_major": 150.0,
                    "semi_minor": 80.0,
                    "orientation_deg": 45.0,
                },
            },
            "valid_for_ms": 60000,
        },
    }


def test_zmeta_to_cot_never_derives_le_from_the_horizontal_ellipse():
    # CR-02. CoT point@le is LINEAR error - the vertical/HAE uncertainty -
    # while contract section 21.2 defines error_ellipse_m as purely
    # horizontal (orientation_deg is degrees true north; the schema carries
    # no vertical-uncertainty field at all). semi_minor -> le told TAK
    # "altitude known to +/-80 m" - certainty the source never had.
    xml_text = zmeta_to_cot_module.zmeta_to_cot(_ellipse_event(), cot_config=_TEST_CONFIG)
    assert xml_text is not None
    point = ET.fromstring(xml_text).find("point")
    assert point.attrib["ce"] == "150.0"  # conservative circular bound
    assert point.attrib["le"] == "9999999.0"  # unknown convention, never 80.0


def test_zmeta_to_cot_ellipse_le_comes_only_from_the_deployment_model():
    # default_le is the deployment's characterized vertical error model. An
    # ellipse on the event must not displace it: the ellipse carries no
    # vertical information at all.
    config = dict(_TEST_CONFIG)
    config["default_le"] = 42.5
    xml_text = zmeta_to_cot_module.zmeta_to_cot(_ellipse_event(), cot_config=config)
    assert xml_text is not None
    assert ET.fromstring(xml_text).find("point").attrib["le"] == "42.5"


def test_zmeta_to_cot_omits_precisionlocation_without_an_asserted_source():
    # CR-11. geopointsrc/altsrc are pedigree attributes TAK reads as "how
    # this position/altitude was derived". The event model carries no
    # geo-source field, so absent an explicit operator assertion the element
    # is omitted (refuse-or-omit) - an RF-triangulated fusion product must
    # never arrive wearing a GPS badge.
    xml_text = zmeta_to_cot_module.zmeta_to_cot(_ellipse_event(), cot_config=_TEST_CONFIG)
    assert xml_text is not None
    assert ET.fromstring(xml_text).find(".//precisionlocation") is None
    assert "GPS" not in xml_text
    assert "geopointsrc" not in xml_text


def test_zmeta_to_cot_precisionlocation_carries_only_the_asserted_source():
    # A deployment that knows how its positions are derived asserts it in
    # config; the attributes carry exactly the asserted strings, never a
    # substituted default.
    config = dict(_TEST_CONFIG)
    config["geopointsrc"] = "RF-TRIANGULATION"
    config["altsrc"] = "BARO"
    xml_text = zmeta_to_cot_module.zmeta_to_cot(_ellipse_event(), cot_config=config)
    assert xml_text is not None
    precision = ET.fromstring(xml_text).find(".//precisionlocation")
    assert precision is not None
    assert precision.attrib["geopointsrc"] == "RF-TRIANGULATION"
    assert precision.attrib["altsrc"] == "BARO"
    assert precision.attrib["ellipse_major"] == "150.0"
    assert precision.attrib["ellipse_minor"] == "80.0"
    assert precision.attrib["ellipse_angle"] == "45.0"


def test_zmeta_to_cot_precisionlocation_partial_assertion_stamps_one_source():
    # Asserting the position source says nothing about the altitude source;
    # the unasserted attribute is omitted, not defaulted.
    config = dict(_TEST_CONFIG)
    config["geopointsrc"] = "GPS"
    xml_text = zmeta_to_cot_module.zmeta_to_cot(_ellipse_event(), cot_config=config)
    assert xml_text is not None
    precision = ET.fromstring(xml_text).find(".//precisionlocation")
    assert precision is not None
    assert precision.attrib["geopointsrc"] == "GPS"
    assert "altsrc" not in precision.attrib


def test_zmeta_to_cot_no_precisionlocation_without_an_ellipse():
    # Boundary pin (passes before and after the CR-11 fix): the element
    # exists to carry the ellipse; an asserted source with no ellipse has
    # nothing to attach to.
    event = _ellipse_event()
    del event["payload"]["geo"]["error_ellipse_m"]
    config = dict(_TEST_CONFIG)
    config["geopointsrc"] = "GPS"
    config["altsrc"] = "GPS"
    xml_text = zmeta_to_cot_module.zmeta_to_cot(event, cot_config=config)
    assert xml_text is not None
    assert ET.fromstring(xml_text).find(".//precisionlocation") is None


# Long-queued zero-default fix: remarks and <precisionlocation> read missing
# ellipse members via `.get(key, 0)`, which fabricates a zero-size ellipse
# claim for a member the event never asserted. Honest absence means the
# member's element/line is omitted, not zero-filled -- and a wrong-spelled
# ellipse dict (no `semi_major` under the name this adapter reads) has no
# claim to render at all, the same way `ce` already falls back to
# `default_ce` rather than reading a `0` out of it.


def test_zmeta_to_cot_omits_a_missing_ellipse_member_instead_of_zero_filling():
    """`orientation_deg` absent, `semi_major`/`semi_minor` present: the
    rendered ellipse must drop the angle, never claim "@ 0deg"."""
    event = _ellipse_event()
    del event["payload"]["geo"]["error_ellipse_m"]["orientation_deg"]
    config = dict(_TEST_CONFIG, geopointsrc="GPS", altsrc="GPS")
    xml_text = zmeta_to_cot_module.zmeta_to_cot(event, cot_config=config)
    assert xml_text is not None

    root = ET.fromstring(xml_text)
    remarks = root.find(".//remarks")
    assert remarks is not None
    assert "150m x 80m" in remarks.text
    assert "0deg" not in remarks.text

    precision = root.find(".//precisionlocation")
    assert precision is not None
    assert precision.attrib["ellipse_major"] == "150.0"
    assert precision.attrib["ellipse_minor"] == "80.0"
    assert "ellipse_angle" not in precision.attrib


def test_zmeta_to_cot_wrong_spelled_ellipse_renders_no_fabricated_claim():
    """A dict with no `semi_major` under the name this adapter reads (e.g. the
    legacy `_m`-suffixed ADS-B keys) carries no ellipse this adapter can
    honestly render -- not a zero-size one. `ce` still falls back to the
    unknown convention, as it already does when `semi_major` is absent."""
    event = _ellipse_event()
    event["payload"]["geo"]["error_ellipse_m"] = {
        "semi_major_m": 150.0,
        "semi_minor_m": 80.0,
        "orientation_deg": 45.0,
    }
    config = dict(_TEST_CONFIG, geopointsrc="GPS", altsrc="GPS")
    xml_text = zmeta_to_cot_module.zmeta_to_cot(event, cot_config=config)
    assert xml_text is not None

    root = ET.fromstring(xml_text)
    assert root.find(".//precisionlocation") is None
    remarks = root.find(".//remarks")
    assert remarks is None or "Error ellipse" not in remarks.text
    assert root.find("point").attrib["ce"] == "9999999.0"


# Banked _parse_utc MAJOR: jsonschema does not enforce format: date-time
# without an installed FormatChecker, so a hostile-but-gate-clean event.ts
# reaches _parse_utc, and the ValueError used to escape the adapter.

_UNPARSEABLE_TS = (
    "2026-07-27T99:99:99Z",  # field values out of range
    "2026-02-30T12:00:00Z",  # day out of range for month
    "not-a-timestamp",       # not a timestamp at all
)


def test_zmeta_to_cot_malformed_ts_refuses_instead_of_raising():
    # Same refusal as a missing ts: an unparseable time claim is no time
    # claim, and CoT time/start/stale cannot be derived from it. The
    # valid-ts control run proves the None comes from the ts specifically.
    assert zmeta_to_cot_module.zmeta_to_cot(_ellipse_event(), cot_config=_TEST_CONFIG) is not None
    for ts in _UNPARSEABLE_TS:
        event = _ellipse_event()
        event["event"]["ts"] = ts
        result = zmeta_to_cot_module.zmeta_to_cot(event, cot_config=_TEST_CONFIG)
        assert result is None, (ts, result)


def test_zmeta_to_cot_malformed_ts_still_projects_in_wall_clock_mode():
    # Boundary pin: wall-clock replay mode never reads ts - now-stamping is
    # its documented purpose (mirrors the missing-ts wall-clock test above).
    event = _ellipse_event()
    event["event"]["ts"] = "not-a-timestamp"
    xml_text = zmeta_to_cot_module.zmeta_to_cot(event, cot_config={"use_wall_clock": True})
    assert xml_text is not None


def test_gate_clean_naive_ts_is_refused_not_localized():
    # Attack-pass completion (2026-07-27): "1969-12-31Z" satisfies the
    # schema's Z$ pattern (gate-clean) yet parses NAIVE on this
    # interpreter; pre-fix .astimezone() asked the platform - OSError
    # pre-epoch on Windows, silent host-local reinterpretation elsewhere.
    # The refusal contract is None: never a traceback, never a shifted
    # instant.
    for ts in ("1969-12-31Z", "2026-W01-1Z"):
        event = _ellipse_event()
        event["event"]["ts"] = ts
        assert zmeta_to_cot_module.zmeta_to_cot(event, cot_config=_TEST_CONFIG) is None


def test_how_pedigree_is_config_asserted_never_defaulted():
    # Attack-pass completion (2026-07-27): every event carried a hardcoded
    # how="m-g" (machine/GPS-derived) - the CR-11 class at its last
    # unmigrated site, a fabricated derivation pedigree on positions that
    # may be RF-triangulated fusion products.
    event = _ellipse_event()
    root = ET.fromstring(zmeta_to_cot_module.zmeta_to_cot(event, cot_config=_TEST_CONFIG))
    assert "how" not in root.attrib
    asserted = dict(_TEST_CONFIG, how="m-g")
    root = ET.fromstring(zmeta_to_cot_module.zmeta_to_cot(event, cot_config=asserted))
    assert root.attrib["how"] == "m-g"


def test_non_string_team_config_does_not_crash_the_projection():
    # Pre-cut review: friendly_team_name/role reached _esc() without str(),
    # so a YAML scalar that parses as a number or bool raised inside the
    # projection and the gateway backstop dropped the whole event.
    event = _ellipse_event()
    event["payload"]["class"] = "a-f-G-U-C"
    config = dict(_TEST_CONFIG, friendly_team_name=7, friendly_team_role=True)
    xml_text = zmeta_to_cot_module.zmeta_to_cot(event, cot_config=config)
    assert xml_text is not None
    root = ET.fromstring(xml_text)
    group = root.find("./detail/__group")
    assert group is not None
    assert group.attrib["name"] == "7"
    assert group.attrib["role"] == "True"


# TV-04 (A1-02): the CoT egress was scoped out of the declared-2D sweep that
# already covers JREAP/KLV. A genuinely-declared-2D geo (dimensionality
# "2D", quality.geo_status VERTICAL_UNAVAILABLE, no alt_m) and the historical
# ambiguous absent-altitude shape (no dimensionality token, no alt_m) both
# rendered hae="9999999.0" with nothing else on the wire to tell them apart -
# indistinguishable to a TAK operator from a failed altitude sensor. CoT
# point@hae is a required numeric attribute (unlike JREAP's hae_m, it has no
# null to reach for), so the sentinel stays; the fix is the honest channel
# alongside it, per the repo's structure-is-authoritative rule.


def _state_event_with_geo(geo, quality=None):
    payload = {
        "track_id": "track-2d",
        "geo": geo,
        "valid_for_ms": 5000,
    }
    if quality is not None:
        payload["quality"] = quality
    return {
        "event": {
            "event_type": "STATE_EVENT",
            "event_subtype": "TRACK_STATE",
            "ts": "2026-08-01T12:00:00Z",
        },
        "payload": payload,
    }


def test_declared_2d_is_distinguishable_from_the_ambiguous_absent_alt_case():
    """The headline red: before the fix both cases render byte-identical
    <point hae="9999999.0"> with no other trace of the distinction anywhere
    in the document, so a TAK operator cannot tell a declared horizontal-only
    fix from a sensor that simply failed to report altitude."""
    declared_2d = zmeta_to_cot_module.zmeta_to_cot(
        _state_event_with_geo(
            {"lat": 33.7405, "lon": -118.2712, "dimensionality": "2D"},
            quality={"geo_status": "VERTICAL_UNAVAILABLE"},
        ),
        cot_config=_TEST_CONFIG,
    )
    ambiguous = zmeta_to_cot_module.zmeta_to_cot(
        _state_event_with_geo({"lat": 33.7405, "lon": -118.2712}),
        cot_config=_TEST_CONFIG,
    )
    assert declared_2d is not None
    assert ambiguous is not None
    assert declared_2d != ambiguous, (
        "declared-2D and ambiguous-absent-alt events must not render "
        "byte-identical CoT XML"
    )

    declared_point = ET.fromstring(declared_2d).find("point")
    ambiguous_point = ET.fromstring(ambiguous).find("point")
    # Both still carry the required numeric hae sentinel - CoT wire
    # compatibility for the 2-D case is non-negotiable.
    assert declared_point.attrib["hae"] == "9999999.0"
    assert ambiguous_point.attrib["hae"] == "9999999.0"

    marker = ET.fromstring(declared_2d).find(".//geo_dimensionality")
    assert marker is not None, "declared-2D geo must carry an honest detail marker"
    assert marker.attrib["value"] == "2D"
    assert marker.attrib["geo_status"] == "VERTICAL_UNAVAILABLE"

    assert ET.fromstring(ambiguous).find(".//geo_dimensionality") is None


def test_ambiguous_absent_altitude_case_stays_byte_compatible():
    """No dimensionality token, no alt_m: the historical shape's rendered
    XML must not change at all - no new marker, same sentinel."""
    event = {
        "event": {
            "event_type": "STATE_EVENT",
            "ts": "2025-01-17T14:30:05Z",
        },
        "payload": {
            "track_id": "track-008",
            "geo": {"lat": 34.0, "lon": -118.0},
            "valid_for_ms": 5000,
        },
    }
    xml_text = zmeta_to_cot_module.zmeta_to_cot(event, cot_config=_TEST_CONFIG)
    assert xml_text is not None
    assert "geo_dimensionality" not in xml_text
    root = ET.fromstring(xml_text)
    assert root.find("point").attrib["hae"] == "9999999.0"


def test_declared_2d_without_geo_status_omits_the_status_attribute():
    """geo_status is asserted only when the event itself carries one - never
    fabricated onto the marker."""
    xml_text = zmeta_to_cot_module.zmeta_to_cot(
        _state_event_with_geo({"lat": 33.7, "lon": -118.2, "dimensionality": "2D"}),
        cot_config=_TEST_CONFIG,
    )
    assert xml_text is not None
    marker = ET.fromstring(xml_text).find(".//geo_dimensionality")
    assert marker is not None
    assert marker.attrib["value"] == "2D"
    assert "geo_status" not in marker.attrib


def test_declared_2d_with_alt_m_is_the_a1_02_contradiction_and_refuses():
    """Schema-valid input cannot carry both, but the adapter must not
    silently trust that - mirrors the JREAP sibling's refusal for the same
    contradiction."""
    xml_text = zmeta_to_cot_module.zmeta_to_cot(
        _state_event_with_geo(
            {"lat": 33.7, "lon": -118.2, "dimensionality": "2D", "alt_m": 120.5}
        ),
        cot_config=_TEST_CONFIG,
    )
    assert xml_text is None


def test_3d_geo_is_unaffected_by_the_2d_marker_logic():
    """A real alt_m with no dimensionality token (or an explicit "3D" token)
    renders exactly as before: real hae, no marker."""
    for geo in (
        {"lat": 33.7, "lon": -118.2, "alt_m": 1500.0},
        {"lat": 33.7, "lon": -118.2, "alt_m": 1500.0, "dimensionality": "3D"},
    ):
        xml_text = zmeta_to_cot_module.zmeta_to_cot(
            _state_event_with_geo(geo), cot_config=_TEST_CONFIG
        )
        assert xml_text is not None
        assert "geo_dimensionality" not in xml_text
        assert ET.fromstring(xml_text).find("point").attrib["hae"] == "1500.0"
