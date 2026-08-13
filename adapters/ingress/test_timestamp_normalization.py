import importlib.util
from pathlib import Path

from adapters.ingress.kraken.kraken_to_zmeta import translate_csv_row
from adapters.ingress.moth.moth_to_zmeta import translate_serial_line
from adapters.ingress.time_utils import (
    DEFAULT_UNSYNCED_ERROR_MS,
    coerce_timing_quality,
    epoch_ms_to_utc_z,
    normalize_utc_z,
)


INGRESS_ROOT = Path(__file__).resolve().parent
EO_CV_PATH = INGRESS_ROOT / "eo-cv" / "eo_cv_to_zmeta.py"
spec = importlib.util.spec_from_file_location("eo_cv_to_zmeta", EO_CV_PATH)
eo_cv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eo_cv)


def test_normalize_utc_z_converts_offsets_to_trailing_z():
    assert normalize_utc_z("2025-01-17T10:20:00-05:00") == "2025-01-17T15:20:00Z"
    assert normalize_utc_z("2025-01-17T15:20:00+00:00") == "2025-01-17T15:20:00Z"


def test_epoch_ms_to_utc_z_uses_schema_timestamp_form():
    assert epoch_ms_to_utc_z(1737127200123) == "2025-01-17T15:20:00.123Z"


def test_coerce_timing_quality_defaults_to_explicit_unsynced_state():
    timing = coerce_timing_quality(event_ts="2025-01-17T15:20:00+00:00")

    assert timing == {
        "time_source": "UNKNOWN",
        "sync_state": "UNSYNCED",
        "est_error_ms": DEFAULT_UNSYNCED_ERROR_MS,
        "last_sync_ts": "2025-01-17T15:20:00Z",
    }


def test_coerce_timing_quality_preserves_valid_supplied_values():
    timing = coerce_timing_quality(
        {"time_source": "GPS_PPS", "sync_state": "LOCKED", "est_error_ms": 2},
        event_ts="2025-01-17T15:20:00+00:00",
    )

    assert timing["time_source"] == "GPS_PPS"
    assert timing["sync_state"] == "LOCKED"
    assert timing["est_error_ms"] == 2


def test_coerce_timing_quality_degrades_an_invalid_time_source():
    """The PR #8 field-verification finding, pinned at the helper.

    A supplied token outside the schema vocabulary previously survived and
    failed schema validation far from its cause. It degrades here instead:
    the source becomes UNKNOWN and the error bound widens, because the
    bound was predicated on the source claim that failed vocabulary. A
    valid supplied sync_state stays: it is a separate claim in a legal
    token, and contract 5.3 has consumers read the pair together.
    """
    timing = coerce_timing_quality(
        {"time_source": "GPS", "sync_state": "LOCKED", "est_error_ms": 5},
        event_ts="2025-01-17T15:20:00+00:00",
    )

    assert timing["time_source"] == "UNKNOWN"
    assert timing["sync_state"] == "LOCKED"
    assert timing["est_error_ms"] == DEFAULT_UNSYNCED_ERROR_MS


def test_coerce_timing_quality_degrades_an_invalid_sync_state():
    timing = coerce_timing_quality(
        {"time_source": "NTP", "sync_state": "SYNCED", "est_error_ms": 5},
        event_ts="2025-01-17T15:20:00+00:00",
    )

    assert timing["time_source"] == "NTP"
    assert timing["sync_state"] == "UNSYNCED"
    assert timing["est_error_ms"] == DEFAULT_UNSYNCED_ERROR_MS


def test_coerce_timing_quality_never_narrows_a_wide_error_bound_on_degrade():
    timing = coerce_timing_quality(
        {"time_source": "GPS", "est_error_ms": 90_000},
        event_ts="2025-01-17T15:20:00+00:00",
    )

    assert timing["time_source"] == "UNKNOWN"
    assert timing["est_error_ms"] == 90_000


def test_coerce_timing_quality_passes_a_poisoned_bound_through_for_downstream_refusal():
    """A poisoned bound suppresses every repair, so gates refuse it whole.

    Two shipped contracts collided here and the battery adjudicated. The
    first isfinite fix replaced a non-finite bound with the degraded
    default, which hid the poison from SAPIENT's refusal gate and broke
    its pinned rule that degradation never substitutes a clean value for
    a poisoned one. The resolution: a claim carrying a poisoned bound is
    not partially cleaned; it passes through untouched and downstream
    refusal or schema validation rejects the whole event, which is also
    exactly the pre-wave behavior for these inputs.
    """
    for bad in ("5", None, True, -1, float("nan"), float("inf"), float("-inf")):
        supplied = {"time_source": "GPS", "sync_state": "SYNCED", "est_error_ms": bad}
        timing = coerce_timing_quality(dict(supplied), event_ts="2025-01-17T15:20:00+00:00")
        assert timing["time_source"] == "GPS", bad
        assert timing["sync_state"] == "SYNCED", bad
        if isinstance(bad, float):
            assert timing["est_error_ms"] != timing["est_error_ms"] or timing[
                "est_error_ms"
            ] == bad, bad
        else:
            assert timing["est_error_ms"] == bad, bad


def test_coerce_timing_quality_never_lets_a_nan_bound_ride_a_degrade():
    """The laundering regression the pre-cut attack pass caught.

    The first version of the degrade fix widened with max(est, default),
    and max(nan, default) is nan, so an event the schema gate previously
    REJECTED on its enum defects came out schema-clean while carrying a
    NaN error bound. With poisoned-bound pass-through, the enum defects
    survive too, and the schema gate rejects the event exactly as it did
    before the wave.
    """
    timing = coerce_timing_quality(
        {"time_source": "GPS", "sync_state": "SYNCED", "est_error_ms": float("nan")},
        event_ts="2025-01-17T15:20:00+00:00",
    )
    assert timing["time_source"] == "GPS"
    assert timing["sync_state"] == "SYNCED"
    assert timing["est_error_ms"] != timing["est_error_ms"]


def test_coerce_timing_quality_degrades_unhashable_wire_values_without_crashing():
    """Wire data must never crash the ingest loop (the A-14 class).

    A frozenset membership test on a list or dict raises TypeError, and
    12 of the helper's 17 call sites pass wire-parsed dicts straight in.
    """
    for bad in (["GPS_PPS"], {"v": "GPS_PPS"}, 7, None, b"NTP"):
        timing = coerce_timing_quality(
            {"time_source": bad, "sync_state": bad},
            event_ts="2025-01-17T15:20:00+00:00",
        )
        assert timing["time_source"] == "UNKNOWN", bad
        assert timing["sync_state"] == "UNSYNCED", bad
        assert timing["est_error_ms"] == DEFAULT_UNSYNCED_ERROR_MS, bad


def test_coerce_timing_quality_folds_whitespace_and_case_onto_the_vocabulary():
    """A fold is not a guess: 'ntp ' means NTP in every UI that renders it.

    Matches the mavlink template's _normalize_vocabulary_token rule. A
    token that folding cannot place (GPS) still degrades.
    """
    timing = coerce_timing_quality(
        {"time_source": " ntp ", "sync_state": "locked", "est_error_ms": 5},
        event_ts="2025-01-17T15:20:00+00:00",
    )
    assert timing["time_source"] == "NTP"
    assert timing["sync_state"] == "LOCKED"
    assert timing["est_error_ms"] == 5


def test_kraken_timestamp_uses_trailing_z():
    event = translate_csv_row(
        ["1737127200.123", "90.0", "80.0", "-55.0", "433000000"],
        platform_id="rf-node-1",
    )

    assert event["event"]["ts"] == "2025-01-17T15:20:00.123Z"
    assert event["payload"]["timing_quality"]["sync_state"] == "UNSYNCED"


def test_moth_timestamp_uses_trailing_z():
    event = translate_serial_line(
        "2437.0,-45.2",
        platform_id="rf-node-1",
        timestamp_ms=1737127200123,
    )

    assert event["event"]["ts"] == "2025-01-17T15:20:00.123Z"
    assert event["payload"]["timing_quality"]["sync_state"] == "UNSYNCED"


def test_eo_cv_timestamp_uses_trailing_z():
    event = eo_cv.translate(
        {
            "class_name": "vehicle",
            "confidence": 0.9,
            "timestamp": "2025-01-17T15:20:00+00:00",
            "source_event_id": "019c2b5c-c053-70e1-b6aa-340000000001",
        },
        platform_id="camera-node-1",
    )

    assert event["event"]["ts"] == "2025-01-17T15:20:00Z"
    assert event["payload"]["timing_quality"]["sync_state"] == "UNSYNCED"
