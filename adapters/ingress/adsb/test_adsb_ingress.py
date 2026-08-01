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

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adapters.ingress.adsb.adsb_to_zmeta import (  # noqa: E402
    translate_aircraft,
    translate_snapshot,
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
    event = translate_aircraft(FULL, **BASE)
    geo = event["payload"]["geo"]
    assert geo["lat"] == 34.05 and geo["lon"] == -118.25
    # alt_geom is WGS84 and is the only altitude that may become alt_m
    assert geo["alt_m"] == pytest.approx(10500 * 0.3048)
    # NACp 9 declares a 30 m containment radius; it is not invented
    ellipse = event["payload"]["quality"]["error_ellipse_m"]
    assert ellipse["semi_major_m"] == 30.0 and ellipse["semi_minor_m"] == 30.0


def test_barometric_only_refuses_canonical_geo_and_keeps_the_position_natively():
    """The common case, and the one that decides whether this adapter is honest.

    Canonical geo requires alt_m (contract 6.8, all-or-nothing) and `alt_baro`
    is a pressure altitude referenced to 1013.25 hPa -- not a height above the
    ellipsoid, and not convertible without local QNH the message never carries.
    So there is no canonical position. The horizontal fix is real, though, so it
    is preserved under explicitly native keys where it claims nothing canonical.
    """
    entry = {k: v for k, v in FULL.items() if k != "alt_geom"}
    event = translate_aircraft(entry, **BASE)
    features = event["payload"]["features"]

    assert "geo" not in event["payload"]
    assert event["payload"]["quality"]["geo_status"] == "UNAVAILABLE"
    assert features["adsb_lat_deg"] == 34.05
    assert features["adsb_lon_deg"] == -118.25
    # the pressure altitude survives, named as what it is
    assert features["adsb_alt_baro_ft"] == 10000
    assert "alt_m" not in json.dumps(event["payload"].get("geo", {}))


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
# a depth no aircraft occupies. Contract 6.8 all-or-nothing then applies the
# same way a missing alt_geom does: no canonical geo, position demoted
# natively, geo_status UNAVAILABLE.


def test_a_sentinel_geometric_altitude_is_rejected_like_a_missing_one():
    entry = dict(FULL, alt_geom=-9999)
    event = translate_aircraft(entry, **BASE)
    features = event["payload"]["features"]

    assert "geo" not in event["payload"]
    assert event["payload"]["quality"]["geo_status"] == "UNAVAILABLE"
    assert features["adsb_lat_deg"] == 34.05
    assert features["adsb_lon_deg"] == -118.25
    # the raw declared value survives so the corrupted reading is visible,
    # not silently dropped
    assert features["adsb_alt_geom_ft"] == -9999


def test_a_geometric_altitude_above_the_plausibility_ceiling_is_rejected():
    """Sustained flight above ~20 km is beyond every civil and known military

    fixed-wing envelope, so a value up there is decoder garbage, not a real
    aircraft.
    """
    entry = dict(FULL, alt_geom=200000)  # ~60960 m
    event = translate_aircraft(entry, **BASE)

    assert "geo" not in event["payload"]
    assert event["payload"]["quality"]["geo_status"] == "UNAVAILABLE"
    assert event["payload"]["features"]["adsb_alt_geom_ft"] == 200000


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
    """NACp absent, or a category that declares no bound, invents nothing."""
    for entry in (
        {k: v for k, v in FULL.items() if k != "nac_p"},
        dict(FULL, nac_p=0),   # "unknown"
        dict(FULL, nac_p=1),   # "> 10 NM", no usable radius
    ):
        event = translate_aircraft(entry, **BASE)
        assert "error_ellipse_m" not in event["payload"].get("quality", {})


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
