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
