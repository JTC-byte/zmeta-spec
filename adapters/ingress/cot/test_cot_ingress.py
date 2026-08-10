import json
import importlib.util
from pathlib import Path

from jsonschema import Draft202012Validator

from adapters.ingress.cot.cot_to_zmeta_template import cot_dict_to_zmeta_track_state
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
