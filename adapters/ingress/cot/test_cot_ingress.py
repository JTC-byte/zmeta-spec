import json
import importlib.util
import xml.etree.ElementTree as ET
from pathlib import Path

from jsonschema import Draft202012Validator

from adapters.egress.cot.zmeta_to_cot import zmeta_to_cot
from adapters.ingress.cot.cot_to_zmeta_template import cot_dict_to_zmeta_track_state
from zmeta_uuid import uuid7


ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = ROOT / "schema" / "zmeta-event-1.0.schema.json"
SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
# No format_checker: `date-time` is annotation-only without an RFC 3339 checker.
VALIDATOR = Draft202012Validator(SCHEMA)
SCHEMA_1_1_0 = json.loads(
    (ROOT / "schema" / "zmeta-event-1.1.0.schema.json").read_text(encoding="utf-8")
)
VALIDATOR_1_1_0 = Draft202012Validator(SCHEMA_1_1_0)
VALIDATORS_PATH = ROOT / "gateway" / "src" / "validators.py"
spec = importlib.util.spec_from_file_location("zmeta_validators", VALIDATORS_PATH)
validators = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validators)
POLICY = validators.load_policy(ROOT / "policy")


def _cot_message(**overrides):
    cot = {
        "uid": "cot-1",
        "type": "a-f-G-U-C",
        "time": "2025-01-17T15:20:00Z",
        "stale": "2025-01-17T15:20:05Z",
        "point": {"lat": 34.0, "lon": -118.0, "hae": 120.0},
        "confidence": 0.7,
        "based_on": [str(uuid7())],
        # Message-carried reflection verdict: the template never
        # self-asserts it (contract 4.5.1) — see the refusal test below.
        "loop_status": "CHECKED_NOT_REFLECTION",
    }
    cot.update(overrides)
    return cot


def test_cot_to_track_state_schema_valid():
    event = cot_dict_to_zmeta_track_state(_cot_message())
    assert event["event"]["event_type"] == "STATE_EVENT"
    assert event["event"]["event_subtype"] == "TRACK_STATE"
    promotion = event["payload"]["extensions"]["external_promotion"]
    assert promotion["promotion_policy_id"] == "PROMOTE-COT-STATE-V1"
    assert promotion["loop_status"] == "CHECKED_NOT_REFLECTION"
    assert event["lineage"]["transform"].startswith("promote:cot@template:")
    VALIDATOR.validate(event)
    ok, violations = validators.validate_producer_authority(
        event, POLICY["producer_authority"], POLICY["violation_severities"]
    )
    assert ok, violations


def test_cot_without_loop_status_refuses():
    # The reflection verdict is never self-asserted (R1-11 R11-07): a CoT
    # message that does not carry loop_status must refuse the promotion.
    cot = _cot_message()
    del cot["loop_status"]
    try:
        cot_dict_to_zmeta_track_state(cot)
    except ValueError as exc:
        assert "loop_status" in str(exc)
    else:
        raise AssertionError("missing loop_status must refuse the promotion")


def test_cot_ingress_normalizes_utc_offset_timestamp():
    cot = _cot_message(
        time="2025-01-17T15:20:00+00:00",
        stale="2025-01-17T15:20:05+00:00",
    )

    event = cot_dict_to_zmeta_track_state(cot)

    assert event["event"]["ts"] == "2025-01-17T15:20:00Z"
    assert event["payload"]["valid_for_ms"] == 5000
    assert event["payload"]["timing_quality"]["last_sync_ts"] == "2025-01-17T15:20:00Z"
    VALIDATOR.validate(event)


def test_unknown_altitude_sentinel_degrades_to_declared_2d():
    # CoT's unknown-value convention for point@hae (9999999.0) is an explicit
    # "altitude unknown" claim, not a 9,999,999 m HAE measurement. alt_m has
    # no upper bound in the v1.0 schema, so before this guard the sentinel
    # promoted as a real altitude and passed every downstream check (the
    # C1-01 wrong-datum-through-a-plausible-value shape).
    event = cot_dict_to_zmeta_track_state(
        _cot_message(point={"lat": 34.0, "lon": -118.0, "hae": 9999999.0})
    )

    geo = event["payload"]["geo"]
    assert geo == {"lat": 34.0, "lon": -118.0, "dimensionality": "2D"}
    assert "alt_m" not in geo
    assert event["payload"]["quality"]["geo_status"] == "VERTICAL_UNAVAILABLE"
    assert event["zmeta_version"] == "1.1.0"
    VALIDATOR_1_1_0.validate(event)


def test_sentinel_arriving_as_string_still_degrades():
    # A lenient upstream XML parser can deliver point attributes as strings;
    # the sentinel comparison happens after float coercion.
    event = cot_dict_to_zmeta_track_state(
        _cot_message(point={"lat": 34.0, "lon": -118.0, "hae": "9999999.0"})
    )
    assert event["payload"]["geo"]["dimensionality"] == "2D"
    assert "alt_m" not in event["payload"]["geo"]


def test_geo_dimensionality_marker_selects_2d_and_carries_geo_status():
    # The egress sibling's <geo_dimensionality> detail marker is the honest
    # channel for the declared-2D case; a carried non-AVAILABLE geo_status
    # (e.g. STALE from the source event) survives the promotion.
    cot = _cot_message(point={"lat": 34.0, "lon": -118.0, "hae": 9999999.0})
    cot["detail"] = {"geo_dimensionality": {"value": "2D", "geo_status": "STALE"}}

    event = cot_dict_to_zmeta_track_state(cot)

    assert event["payload"]["geo"]["dimensionality"] == "2D"
    assert event["payload"]["quality"]["geo_status"] == "STALE"
    assert event["zmeta_version"] == "1.1.0"
    VALIDATOR_1_1_0.validate(event)


def test_2d_marker_beside_real_altitude_refuses():
    # A "2D" declaration next to a real hae is the A1-02 coherence
    # contradiction; the egress refuses to build it, so the ingress refuses
    # to promote it.
    cot = _cot_message(point={"lat": 34.0, "lon": -118.0, "hae": 120.0})
    cot["detail"] = {"geo_dimensionality": {"value": "2D"}}
    try:
        cot_dict_to_zmeta_track_state(cot)
    except ValueError as exc:
        assert "2D" in str(exc)
    else:
        raise AssertionError("2D marker beside a real altitude must refuse")


def test_real_altitude_still_promotes_as_canonical_hae():
    # CoT point@hae is HAE by the CoT spec, so the datum-proper path is
    # unchanged: real value, canonical alt_m, 1.0 stamp.
    event = cot_dict_to_zmeta_track_state(_cot_message())
    assert event["payload"]["geo"]["alt_m"] == 120.0
    assert event["zmeta_version"] == "1.0"
    VALIDATOR.validate(event)


def test_egress_2d_round_trip_survives_via_the_detail_marker():
    # End to end across the wire format: a declared-2D state event projects
    # to CoT XML (hae carries the required numeric sentinel, the marker
    # carries the truth), and re-promoting the parsed XML yields a declared
    # 2-D geo again instead of a 9,999,999 m altitude claim.
    xml = zmeta_to_cot(
        {
            "event": {
                "event_type": "STATE_EVENT",
                "event_subtype": "TRACK_STATE",
                "ts": "2026-08-10T12:00:00Z",
            },
            "payload": {
                "track_id": "track-2d",
                "geo": {"lat": 33.7405, "lon": -118.2712, "dimensionality": "2D"},
                "valid_for_ms": 5000,
                "quality": {"geo_status": "VERTICAL_UNAVAILABLE"},
            },
        },
        cot_config={"use_wall_clock": False},
    )
    assert xml is not None

    root = ET.fromstring(xml)
    point = root.find("point")
    marker = root.find(".//geo_dimensionality")
    assert point.attrib["hae"] == "9999999.0"
    assert marker is not None

    cot = _cot_message(
        point={
            "lat": float(point.attrib["lat"]),
            "lon": float(point.attrib["lon"]),
            "hae": float(point.attrib["hae"]),
        }
    )
    cot["detail"] = {"geo_dimensionality": dict(marker.attrib)}

    event = cot_dict_to_zmeta_track_state(cot)

    geo = event["payload"]["geo"]
    assert geo["dimensionality"] == "2D"
    assert "alt_m" not in geo
    assert event["payload"]["quality"]["geo_status"] == "VERTICAL_UNAVAILABLE"
    assert event["zmeta_version"] == "1.1.0"
    VALIDATOR_1_1_0.validate(event)
