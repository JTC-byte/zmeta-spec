import json
from pathlib import Path

from jsonschema import Draft202012Validator

from adapters.ingress.klv.klv_to_zmeta_template import klv_decoded_to_zmeta_observation


ROOT = Path(__file__).resolve().parents[3]
# No format_checker: `date-time` is annotation-only without an RFC 3339 checker.
VALIDATOR_1_0 = Draft202012Validator(
    json.loads((ROOT / "schema" / "zmeta-event-1.0.schema.json").read_text(encoding="utf-8"))
)
VALIDATOR_1_1_0 = Draft202012Validator(
    json.loads((ROOT / "schema" / "zmeta-event-1.1.0.schema.json").read_text(encoding="utf-8"))
)

_PARENT_EVENT_ID = "019c2b5c-c053-70e1-b6aa-340000000001"


def _translate(decoded):
    return klv_decoded_to_zmeta_observation(
        decoded,
        platform_id="platform-1",
        sensor_id="sensor-1",
        producer="klv:misb:0601",
        ts="2025-01-17T15:20:00+00:00",
    )


def test_klv_ingress_observation():
    decoded = {"lat": 34.0, "lon": -118.0, "alt_hae_m": 96.0, "sensor_mode": "EO"}
    event = _translate(decoded)

    assert event["event"]["event_type"] == "OBSERVATION_EVENT"
    assert event["event"]["ts"] == "2025-01-17T15:20:00Z"
    assert "features" in event["payload"]
    assert event["payload"]["timing_quality"]["sync_state"] == "UNSYNCED"
    assert "confidence" not in event
    # Original observations carry no ZMeta parent; lineage is omitted, never
    # fabricated with a random parent id.
    assert "lineage" not in event


def test_klv_ingress_observation_carries_caller_lineage_when_supplied():
    decoded = {"lat": 34.0, "lon": -118.0, "alt_hae_m": 96.0, "sensor_mode": "EO"}
    event = klv_decoded_to_zmeta_observation(
        decoded,
        platform_id="platform-1",
        sensor_id="sensor-1",
        producer="klv:misb:0601",
        ts="2025-01-17T15:20:00+00:00",
        based_on=[_PARENT_EVENT_ID],
    )

    assert event["lineage"]["based_on"] == [_PARENT_EVENT_ID]
    assert event["lineage"]["transform"].startswith("translate:klv@")


# The five C1-01 altitude-datum boundary cases. MISB ST 0601's dominant
# altitude tags (15 Sensor True Altitude, 25 Frame Center Elevation, 42
# Target Location Elevation) are MSL; only Tags 75/78 are HAE. Contract 6.2
# reserves canonical geo.alt_m for HAE, so the decode boundary must name the
# datum and only a known-HAE value may cross.


def test_hae_only_becomes_canonical_alt_m_under_the_1_0_stamp():
    event = _translate({"lat": 34.0, "lon": -118.0, "alt_hae_m": 96.0})

    assert event["payload"]["geo"] == {"lat": 34.0, "lon": -118.0, "alt_m": 96.0}
    assert event["zmeta_version"] == "1.0"
    VALIDATOR_1_0.validate(event)


def test_msl_only_degrades_to_declared_2d_with_the_value_preserved():
    # An MSL altitude (e.g. ST 0601 Tag 15) is a real measurement in a datum
    # this template cannot state canonically: the horizontal fix publishes as
    # the declared 2-D form and the vertical survives under a datum-named
    # non-canonical key instead of being laundered into alt_m.
    event = _translate({"lat": 34.0, "lon": -118.0, "alt_msl_m": 120.0})

    geo = event["payload"]["geo"]
    assert geo == {"lat": 34.0, "lon": -118.0, "dimensionality": "2D"}
    assert "alt_m" not in geo
    assert event["payload"]["quality"]["klv_alt_msl_m"] == 120.0
    assert event["payload"]["quality"]["geo_status"] == "VERTICAL_UNAVAILABLE"
    assert event["zmeta_version"] == "1.1.0"
    VALIDATOR_1_1_0.validate(event)


def test_both_datums_present_hae_wins():
    event = _translate(
        {"lat": 34.0, "lon": -118.0, "alt_hae_m": 96.0, "alt_msl_m": 120.0}
    )

    assert event["payload"]["geo"]["alt_m"] == 96.0
    assert event["zmeta_version"] == "1.0"
    VALIDATOR_1_0.validate(event)


def test_no_altitude_of_any_kind_omits_geo_entirely():
    # All-or-nothing (contract 6.8): a position with no vertical of any datum
    # omits geo rather than zero-filling it.
    event = _translate({"lat": 34.0, "lon": -118.0})

    assert "geo" not in event["payload"]
    VALIDATOR_1_0.validate(event)


def test_legacy_unqualified_alt_m_never_reaches_canonical_alt_m():
    # The legacy generic alt_m key asserts no datum at all, which is worse
    # than MSL: nothing is known about it. It degrades to the 2-D form with
    # the value preserved under an explicitly unspecified-datum name. Before
    # this boundary existed, this exact input published 120.0 as canonical
    # HAE (the modeled happy path of the old test suite).
    event = _translate({"lat": 34.0, "lon": -118.0, "alt_m": 120.0})

    geo = event["payload"]["geo"]
    assert geo == {"lat": 34.0, "lon": -118.0, "dimensionality": "2D"}
    assert "alt_m" not in geo
    assert event["payload"]["quality"]["klv_alt_unspecified_datum_m"] == 120.0
    assert event["payload"]["quality"]["geo_status"] == "VERTICAL_UNAVAILABLE"
    assert event["zmeta_version"] == "1.1.0"
    VALIDATOR_1_1_0.validate(event)
