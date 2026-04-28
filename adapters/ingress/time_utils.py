"""Timestamp helpers for ingress adapters."""

from __future__ import annotations

from datetime import datetime, timezone

DEFAULT_UNSYNCED_ERROR_MS = 60_000


def format_utc_z(value: datetime, *, timespec: str = "auto") -> str:
    """Format a datetime as a UTC timestamp with trailing Z."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    text = value.astimezone(timezone.utc).isoformat(timespec=timespec)
    return text.replace("+00:00", "Z")


def utc_now_z(*, timespec: str = "seconds") -> str:
    return format_utc_z(datetime.now(timezone.utc), timespec=timespec)


def epoch_ms_to_utc_z(timestamp_ms: int | float) -> str:
    return format_utc_z(
        datetime.fromtimestamp(float(timestamp_ms) / 1000.0, tz=timezone.utc),
        timespec="milliseconds",
    )


def normalize_utc_z(value, *, default=None, timespec: str = "auto"):
    """Normalize a timestamp-like value to UTC-Z, returning default if invalid."""
    if value is None:
        return default
    if isinstance(value, datetime):
        return format_utc_z(value, timespec=timespec)
    if not isinstance(value, str):
        return default
    text = value.strip()
    if not text:
        return default
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return default
    return format_utc_z(parsed, timespec=timespec)


def coerce_timing_quality(value=None, *, event_ts=None) -> dict:
    """Return schema-valid timing quality, preserving supplied fields when present."""
    timing = dict(value) if isinstance(value, dict) else {}
    timing.setdefault("time_source", "UNKNOWN")
    timing.setdefault("sync_state", "UNSYNCED")
    timing.setdefault("est_error_ms", DEFAULT_UNSYNCED_ERROR_MS)
    timing["last_sync_ts"] = (
        normalize_utc_z(timing.get("last_sync_ts"))
        or normalize_utc_z(event_ts)
        or utc_now_z()
    )
    return timing
