"""ADS-B ingress: the honesty rules, pinned against real message shapes.

Every case here is a shape dump1090 actually produces in the air, not an
invented edge case. The ones that matter most are the refusals: a Mode S-only
target with no position, and a target reporting only barometric altitude. Both
are common, and both are where an adapter is tempted to fill in a number.
"""

import json
import math
import sys
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adapters.ingress.adsb.adsb_to_zmeta import (  # noqa: E402
    translate_aircraft,
    translate_snapshot,
)
from adapters.ingress.time_utils import coerce_timing_quality  # noqa: E402

SCHEMA_DIR = ROOT / "schema"
VALIDATOR_1_0 = Draft202012Validator(
    json.loads((SCHEMA_DIR / "zmeta-event-1.0.schema.json").read_text(encoding="utf-8")),
    format_checker=FormatChecker(),
)
VALIDATOR_1_1_0 = Draft202012Validator(
    json.loads((SCHEMA_DIR / "zmeta-event-1.1.0.schema.json").read_text(encoding="utf-8")),
    format_checker=FormatChecker(),
)

NOW = 1769558400.0
BASE = dict(now_epoch_s=NOW, platform_id="adsb-node-01", receiver_id="rtlsdr-01")

FULL = {
    "hex": "a1b2c3", "flight": "UAL123 ", "lat": 34.05, "lon": -118.25,
    "alt_geom": 10500, "alt_baro": 10000, "gs": 420.5, "track": 95.2,
    "nac_p": 9, "sil": 3, "rssi": -18.4, "messages": 842,
    "seen": 0.1, "seen_pos": 0.3, "squawk": "1200",
}


def test_a_full_report_produces_canonical_geo_with_a_declared_bound():
    """NACp 9 declares a 30 m containment radius; it is not invented.

    The ellipse is geo uncertainty, so it lives at `payload.geo.error_ellipse_m`
    with the formal contract spellings (`semi_major`/`semi_minor`/
    `orientation_deg`), never the old `_m`-suffixed `payload.quality` location.
    The locked v1.0 `geo` def has no room for it, so an entry that populates
    the ellipse stamps `zmeta_version: 1.1.0` and must validate against the
    v1.1.0 schema, not just assert its own shape.
    """
    event = translate_aircraft(FULL, **BASE)
    assert event["zmeta_version"] == "1.1.0"
    geo = event["payload"]["geo"]
    assert geo["lat"] == 34.05 and geo["lon"] == -118.25
    # alt_geom is WGS84 and is the only altitude that may become alt_m
    assert geo["alt_m"] == pytest.approx(10500 * 0.3048)
    ellipse = geo["error_ellipse_m"]
    assert ellipse["semi_major"] == 30.0 and ellipse["semi_minor"] == 30.0
    assert ellipse["orientation_deg"] == 0.0
    assert "quality" not in event["payload"]
    VALIDATOR_1_1_0.validate(event)


def test_ellipse_free_entry_emits_byte_stable_v1_0_output():
    """No usable NACp bound (category 1, ">10 NM"): the promotion must not
    leak `zmeta_version`, `payload.geo.error_ellipse_m`, or the v1.1.0-only
    `features.protocol` key onto the branch that never populates an ellipse.
    The v1.0 payload this adapter has always produced stays unchanged."""
    entry = dict(FULL, nac_p=1)
    event = translate_aircraft(entry, **BASE)

    assert event["zmeta_version"] == "1.0"
    assert event["source"] == {
        "platform_id": "adsb-node-01",
        "node_role": "EDGE",
        "producer": "rf-sensor-adsb-01",
    }
    assert event["payload"] == {
        "modality": "NETWORK",
        "features": {
            "adsb_icao24": "a1b2c3",
            "adsb_downlink_hz": 1090_000_000,
            "adsb_receiver_id": "rtlsdr-01",
            "adsb_callsign": "UAL123",
            "adsb_squawk": "1200",
            "rssi_dbfs": -18.4,
            "adsb_alt_baro_ft": 10000,
            "adsb_ground_speed_kt": 420.5,
            "adsb_track_deg_true": 95.2,
            "adsb_message_count": 842,
            "adsb_seen_s": 0.1,
            "adsb_seen_pos_s": 0.3,
            "adsb_nac_p": 1,
            "adsb_sil": 3,
        },
        "timing_quality": coerce_timing_quality(None, event_ts=event["event"]["ts"]),
        "geo": {"lat": 34.05, "lon": -118.25, "alt_m": 10500 * 0.3048},
    }
    VALIDATOR_1_0.validate(event)


def test_barometric_only_emits_the_2d_canonical_form():
    """The common case, and the one that used to hit the all-or-nothing wall.

    Canonical geo used to require alt_m unconditionally (contract 6.8), and
    `alt_baro` is a pressure altitude referenced to 1013.25 hPa -- not a
    height above the ellipsoid, and not convertible without local QNH the
    message never carries. Doctrine A1-02 gives geo a declared
    `dimensionality`, so the real horizontal fix now gets a canonical home as
    the 2-D form instead of being fully demoted to native features. NACp's
    horizontal bound is about the horizontal fix, not the missing vertical,
    so it still attaches even though the geo is 2-D.
    """
    entry = {k: v for k, v in FULL.items() if k != "alt_geom"}
    event = translate_aircraft(entry, **BASE)
    features = event["payload"]["features"]

    assert event["zmeta_version"] == "1.1.0"
    assert event["payload"]["geo"] == {
        "lat": 34.05,
        "lon": -118.25,
        "dimensionality": "2D",
        "error_ellipse_m": {"semi_major": 30.0, "semi_minor": 30.0, "orientation_deg": 0.0},
    }
    assert event["payload"]["quality"]["geo_status"] == "VERTICAL_UNAVAILABLE"
    assert "adsb_lat_deg" not in features
    assert "adsb_lon_deg" not in features
    # the pressure altitude survives, named as what it is
    assert features["adsb_alt_baro_ft"] == 10000
    assert features["protocol"] == "ADS-B"
    VALIDATOR_1_1_0.validate(event)


def test_barometric_only_without_a_declared_bound_still_emits_2d_geo():
    """Same wall, minus NACp: the 2-D form does not depend on an ellipse.

    Confirms the promotion to 1.1.0 is driven by `dimensionality` on its own,
    not only by the ellipse branch wave 1 shipped.
    """
    entry = {k: v for k, v in FULL.items() if k not in ("alt_geom", "nac_p")}
    event = translate_aircraft(entry, **BASE)

    assert event["zmeta_version"] == "1.1.0"
    assert event["payload"]["geo"] == {"lat": 34.05, "lon": -118.25, "dimensionality": "2D"}
    assert event["payload"]["quality"]["geo_status"] == "VERTICAL_UNAVAILABLE"
    assert event["payload"]["features"]["protocol"] == "ADS-B"
    VALIDATOR_1_1_0.validate(event)


def test_mode_s_only_is_a_real_detection_with_no_position():
    """No lat/lon at all -- Mode S, or ADS-B before position lock.

    A naive adapter drops this target or emits null island. It is a genuine
    detection of a genuine emitter and belongs on the wire, positionless.
    """
    event = translate_aircraft(
        {"hex": "aabbcc", "rssi": -31.7, "messages": 12, "seen": 2.1}, **BASE
    )
    assert event is not None
    assert "geo" not in event["payload"]
    assert event["payload"]["quality"]["geo_status"] == "UNAVAILABLE"
    assert event["payload"]["features"]["adsb_icao24"] == "aabbcc"
    assert event["payload"]["features"]["rssi_dbfs"] == -31.7


def test_rssi_is_never_presented_as_calibrated_power():
    """dump1090 reports dBFS. `power_dbm` asserts absolute calibrated dBm.

    Putting one in the other is the laundering the contract forbids, and it is
    why this adapter uses NETWORK modality rather than RF -- see the module
    docstring and the README's open questions.
    """
    event = translate_aircraft(FULL, **BASE)
    blob = json.dumps(event)
    assert "power_dbm" not in blob
    assert event["payload"]["features"]["rssi_dbfs"] == -18.4


@pytest.mark.parametrize("field", ["lat", "lon"])
def test_a_non_finite_coordinate_is_not_a_position(field):
    entry = dict(FULL, **{field: math.nan})
    event = translate_aircraft(entry, **BASE)
    assert "geo" not in event["payload"]
    assert event["payload"]["quality"]["geo_status"] == "UNAVAILABLE"


@pytest.mark.parametrize("lat,lon", [(91.0, 0.0), (-91.0, 0.0), (0.0, 181.0)])
def test_out_of_range_coordinates_are_refused(lat, lon):
    event = translate_aircraft(dict(FULL, lat=lat, lon=lon), **BASE)
    assert "geo" not in event["payload"]


def test_an_entry_without_an_emitter_identity_is_refused_entirely():
    """No `hex` means no subject for the observation."""
    assert translate_aircraft({"lat": 34.0, "lon": -118.0, "seen": 0.2}, **BASE) is None
    assert translate_aircraft({"hex": "   "}, **BASE) is None


def test_an_unusable_snapshot_clock_refuses_rather_than_guessing():
    assert translate_aircraft(FULL, **dict(BASE, now_epoch_s=None)) is None
    assert translate_aircraft(FULL, **dict(BASE, now_epoch_s=math.nan)) is None


def test_an_implausibly_small_snapshot_clock_refuses_rather_than_dating_near_1970():
    """A `now` far below any real epoch second is not a moment.

    It is some other quantity that leaked in under that key (a counter, a
    relative offset). Converting it anyway would silently date the event
    near 1970-01-01. Mirrors the AIS adapter's EPOCH_FLOOR_S.
    """
    assert translate_aircraft(FULL, **dict(BASE, now_epoch_s=1000.0)) is None


# --- Geometric altitude plausibility (sibling-parity, AIS altitude doctrine) -
# A sentinel or a garbled decode (dump1090 has been observed to report
# alt_geom -9999) must not become a canonical alt_m: -9999 ft is -3047.7 m,
# a depth no aircraft occupies. It is treated the same way a missing
# alt_geom is (doctrine A1-02): the horizontal fix still gets canonical geo,
# declared 2-D, geo_status VERTICAL_UNAVAILABLE.


def test_a_sentinel_geometric_altitude_falls_back_to_the_2d_form():
    """A sentinel or a garbled decode still leaves a real horizontal fix.

    It is rejected like a missing `alt_geom` (contract: no honest vertical),
    but doctrine A1-02 means "no honest vertical" is a 2-D geo now, not a
    full demotion.
    """
    entry = dict(FULL, alt_geom=-9999)
    event = translate_aircraft(entry, **BASE)
    features = event["payload"]["features"]
    geo = event["payload"]["geo"]

    assert geo["dimensionality"] == "2D"
    assert "alt_m" not in geo
    assert event["payload"]["quality"]["geo_status"] == "VERTICAL_UNAVAILABLE"
    assert "adsb_lat_deg" not in features
    assert "adsb_lon_deg" not in features
    # the raw declared value survives so the corrupted reading is visible,
    # not silently dropped
    assert features["adsb_alt_geom_ft"] == -9999
    VALIDATOR_1_1_0.validate(event)


def test_a_geometric_altitude_above_the_plausibility_ceiling_falls_back_to_the_2d_form():
    """Sustained flight above ~20 km is beyond every civil and known military

    fixed-wing envelope, so a value up there is decoder garbage, not a real
    aircraft. The horizontal fix is unaffected by that garbage, so it still
    gets its canonical 2-D home.
    """
    entry = dict(FULL, alt_geom=200000)  # ~60960 m
    event = translate_aircraft(entry, **BASE)
    geo = event["payload"]["geo"]

    assert geo["dimensionality"] == "2D"
    assert "alt_m" not in geo
    assert event["payload"]["quality"]["geo_status"] == "VERTICAL_UNAVAILABLE"
    assert event["payload"]["features"]["adsb_alt_geom_ft"] == 200000
    VALIDATOR_1_1_0.validate(event)


def test_geometric_altitude_within_the_plausibility_band_is_unaffected():
    """The band must not squeeze real high-altitude traffic."""
    entry = dict(FULL, alt_geom=65000)  # ~19812 m, inside the band
    event = translate_aircraft(entry, **BASE)

    assert event["payload"]["geo"]["alt_m"] == pytest.approx(65000 * 0.3048)


def test_an_out_of_range_coordinate_is_not_demoted_to_native_either():
    """An impossible coordinate is corruption, not a position worth keeping.

    Sibling-parity with the AIS adapter's `_position()`: the bounds check
    that keeps an out-of-range coordinate out of canonical geo must also
    keep it out of the native demotion path, or the "not a position" claim
    is only half-honored.
    """
    entry = {"hex": "aabbcc", "lat": 95.0, "lon": 200.0, "seen": 1.0}
    event = translate_aircraft(entry, **BASE)
    features = event["payload"]["features"]

    assert "geo" not in event["payload"]
    assert "adsb_lat_deg" not in features
    assert "adsb_lon_deg" not in features


def test_absent_declared_accuracy_produces_no_bound():
    """NACp absent, or a category that declares no bound, invents nothing.

    No ellipse means no reason to leave the locked v1.0 stamp either.
    """
    for entry in (
        {k: v for k, v in FULL.items() if k != "nac_p"},
        dict(FULL, nac_p=0),   # "unknown"
        dict(FULL, nac_p=1),   # "> 10 NM", no usable radius
    ):
        event = translate_aircraft(entry, **BASE)
        assert "error_ellipse_m" not in event["payload"].get("geo", {})
        assert event["zmeta_version"] == "1.0"


def test_timing_is_the_degraded_fallback_unless_the_deployment_supplies_real_metadata():
    """An RTL-SDR has no disciplined clock, and the event says so."""
    event = translate_aircraft(FULL, **BASE)
    timing = event["payload"]["timing_quality"]
    assert timing["time_source"] == "UNKNOWN"
    assert timing["sync_state"] == "UNSYNCED"

    supplied = {"time_source": "GPS", "sync_state": "LOCKED", "est_error_ms": 5}
    event = translate_aircraft(FULL, **dict(BASE, timing_quality=supplied))
    assert event["payload"]["timing_quality"]["time_source"] == "GPS"
    assert event["payload"]["timing_quality"]["sync_state"] == "LOCKED"


def test_position_age_moves_the_timestamp_back_not_the_snapshot_time():
    """`seen_pos` is how old the position is; the event is stamped accordingly."""
    event = translate_aircraft(dict(FULL, seen_pos=5.0), **BASE)
    assert event["event"]["ts"].endswith("Z")
    assert event["event"]["ts"] < translate_aircraft(FULL, **BASE)["event"]["ts"]


def test_snapshot_drops_unusable_entries_without_patching_them():
    snapshot = {
        "now": NOW,
        "aircraft": [FULL, {"hex": "aabbcc", "seen": 1.0}, {"flight": "NOHEX"}],
    }
    events = translate_snapshot(snapshot, platform_id="adsb-node-01")
    assert len(events) == 2
    assert {e["payload"]["features"]["adsb_icao24"] for e in events} == {"a1b2c3", "aabbcc"}


def test_a_malformed_snapshot_yields_nothing_rather_than_raising():
    assert translate_snapshot(None, platform_id="p") == []
    assert translate_snapshot({"now": NOW}, platform_id="p") == []
    assert translate_snapshot({"now": NOW, "aircraft": "not-a-list"}, platform_id="p") == []


def test_the_default_producer_satisfies_reference_producer_authority():
    """`rf-sensor-*` is one of the reference wildcards (AUTHORING.md 7).

    An adapter whose default producer fails policy sends its author into the
    30-90 minute wall the first-run review measured.
    """
    event = translate_aircraft(FULL, **BASE)
    assert event["source"]["producer"].startswith("rf-sensor-")
    assert event["source"]["node_role"] == "EDGE"


def test_rf_power_reference_flag_emits_the_declared_rf_form():
    """The A1-01 experimental split: dBFS in power_dbm is sayable only with
    its reference declared beside it (registry POWER_REFERENCE, v1.1.0).

    The RF minimum feature set is complete and each member exactly as honest
    as the data: real downlink frequency, the documented not-measured 0.0
    bandwidth sentinel, and the rssi value with power_reference "DBFS". The
    stamp is forced to 1.1.0 because the discriminator is 1.1.0 vocabulary,
    and the event must validate there, not just assert its own shape.
    """
    event = translate_aircraft(FULL, rf_power_reference=True, **BASE)
    assert event["zmeta_version"] == "1.1.0"
    assert event["payload"]["modality"] == "RF"
    assert event["event"]["event_subtype"] == "RF"
    features = event["payload"]["features"]
    assert features["center_freq_hz"] == 1090_000_000.0
    assert features["bandwidth_hz"] == 0.0
    assert features["power_dbm"] == -18.4
    assert features["power_reference"] == "DBFS"
    # The native claim stays alongside the canonical one; removing it would
    # delete information the default form has always carried.
    assert features["rssi_dbfs"] == -18.4
    VALIDATOR_1_1_0.validate(event)


def test_rf_flag_without_rssi_keeps_the_network_form():
    """An RF observation without its required power claim would have to
    fabricate one, so an rssi-less entry keeps the NETWORK form under the
    flag rather than inventing power_dbm."""
    entry = {k: v for k, v in FULL.items() if k != "rssi"}
    event = translate_aircraft(entry, rf_power_reference=True, **BASE)
    assert event["payload"]["modality"] == "NETWORK"
    assert event["event"]["event_subtype"] == "NETWORK"
    features = event["payload"]["features"]
    assert "power_dbm" not in features
    assert "power_reference" not in features


def test_rf_flag_off_never_emits_the_discriminator():
    """Default output is byte-for-byte the established behavior: no RF form,
    no power_reference, rssi only under its explicitly named native key."""
    event = translate_aircraft(FULL, **BASE)
    assert event["payload"]["modality"] == "NETWORK"
    features = event["payload"]["features"]
    assert "power_dbm" not in features
    assert "power_reference" not in features
    assert features["rssi_dbfs"] == -18.4


def test_power_reference_enum_rejects_an_undeclared_token():
    """Red proof for the schema enum: a token outside DBM_ABSOLUTE / DBFS /
    DB_RELATIVE fails 1.1.0 validation, so a producer cannot mint private
    reference vocabulary through this member."""
    event = translate_aircraft(FULL, rf_power_reference=True, **BASE)
    event["payload"]["features"]["power_reference"] = "DBM"
    errors = list(VALIDATOR_1_1_0.iter_errors(event))
    assert errors, "an undeclared power_reference token validated"
