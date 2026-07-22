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
    """No config: real error_ellipse_m still maps to CE/LE."""
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
    assert point.attrib["le"] == "17.0"


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
