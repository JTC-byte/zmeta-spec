import json
import importlib.util
from pathlib import Path

from jsonschema import Draft202012Validator

from adapters.ingress.jreap.jreap_track_to_zmeta_template import jreap_track_dict_to_zmeta_track_state
from zmeta_uuid import uuid7


ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = ROOT / "schema" / "zmeta-event-1.0.schema.json"
SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
# No format_checker: `date-time` is annotation-only without an RFC 3339 checker.
VALIDATOR = Draft202012Validator(SCHEMA)
VALIDATORS_PATH = ROOT / "gateway" / "src" / "validators.py"
spec = importlib.util.spec_from_file_location("zmeta_validators", VALIDATORS_PATH)
validators = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validators)
POLICY = validators.load_policy(ROOT / "policy")


def _jreap_track(**overrides):
    track = {
        "track_id": "track-1",
        "lat": 34.0,
        "lon": -118.0,
        "hae_m": 120.0,
        "timestamp": "2025-01-17T15:20:00Z",
        "stale_time": "2025-01-17T15:20:05Z",
        "track_type": "UNKNOWN",
        "confidence": 0.6,
        "based_on": [str(uuid7())],
        # Message-carried reflection verdict: the template never
        # self-asserts it (contract 4.5.1) — see the refusal test below.
        "loop_status": "CHECKED_NOT_REFLECTION",
    }
    track.update(overrides)
    return track


def test_jreap_track_to_state_schema_valid():
    event = jreap_track_dict_to_zmeta_track_state(_jreap_track())
    assert event["event"]["event_type"] == "STATE_EVENT"
    assert event["event"]["event_subtype"] == "TRACK_STATE"
    promotion = event["payload"]["extensions"]["external_promotion"]
    assert promotion["promotion_policy_id"] == "PROMOTE-JREAP-STATE-V1"
    assert promotion["loop_status"] == "CHECKED_NOT_REFLECTION"
    assert event["lineage"]["transform"].startswith("promote:jreap@template:")
    VALIDATOR.validate(event)
    ok, violations = validators.validate_producer_authority(
        event, POLICY["producer_authority"], POLICY["violation_severities"]
    )
    assert ok, violations


def test_jreap_without_loop_status_refuses():
    # The reflection verdict is never self-asserted (R1-11 R11-07).
    track = _jreap_track()
    del track["loop_status"]
    try:
        jreap_track_dict_to_zmeta_track_state(track)
    except ValueError as exc:
        assert "loop_status" in str(exc)
    else:
        raise AssertionError("missing loop_status must refuse the promotion")


def test_jreap_ingress_normalizes_utc_offset_timestamp():
    track = _jreap_track(
        timestamp="2025-01-17T15:20:00+00:00",
        stale_time="2025-01-17T15:20:05+00:00",
    )

    event = jreap_track_dict_to_zmeta_track_state(track)

    assert event["event"]["ts"] == "2025-01-17T15:20:00Z"
    assert event["payload"]["valid_for_ms"] == 5000
    assert event["payload"]["timing_quality"]["last_sync_ts"] == "2025-01-17T15:20:00Z"
    VALIDATOR.validate(event)
