"""Timestamp helpers for ingress adapters."""

from __future__ import annotations

import math
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


TIME_SOURCE_VALUES = frozenset(
    {"GPS_PPS", "GPS_NMEA", "NTP", "PTP", "MANUAL", "UNKNOWN"}
)
SYNC_STATE_VALUES = frozenset({"LOCKED", "HOLDOVER", "UNSYNCED"})


def _fold_to_vocabulary(token, vocabulary, degraded_token):
    """(member or degraded token, whether it degraded).

    Non-strings degrade instead of raising: 12 of the helper's 17 call
    sites pass wire-parsed dicts, and an unhashable value in a frozenset
    membership test is a crash, not a refusal (the A-14 class). Strings
    fold whitespace and case before comparison, matching
    _normalize_vocabulary_token in the mavlink template; a fold is not a
    guess, because it never maps one vocabulary member toward another.
    """
    if not isinstance(token, str):
        return degraded_token, True
    folded = token.strip().upper()
    if folded in vocabulary:
        return folded, False
    return degraded_token, True


def coerce_timing_quality(value=None, *, event_ts=None) -> dict:
    """Return schema-valid timing quality, preserving supplied fields when valid.

    The schema requires last_sync_ts even for never-synced clocks; the
    reference convention fills it with the event timestamp. Per contract
    5.3, last_sync_ts is a synchronization claim only when sync_state is
    not UNSYNCED - consumers must read the pair together.

    A supplied value outside the schema vocabulary degrades rather than
    surviving to fail schema validation far from its cause: an unknown
    time_source becomes UNKNOWN, an unknown sync_state becomes UNSYNCED,
    each independently, and when either degrades the error bound widens
    to at least the unsynced default, because the bound was predicated on
    the claim that failed. Comparison folds whitespace and case first
    (the mavlink template's vocabulary rule: a label that renders
    correctly in every UI must not escape on one space); anything beyond
    that fold, including a non-string, degrades rather than guesses.
    Wire data must never crash this path, so the guards screen shape
    before membership.

    Degrade repairs vocabulary only when the rest of the timing claim is
    well-formed. A claim whose error bound is poisoned (wrong type,
    non-finite, or negative) passes through untouched, setdefault fills
    aside, so downstream gates refuse it whole: partially cleaning it
    would launder a malfunctioning producer's output into a schema-clean
    event, and SAPIENT's refusal contract (degradation never substitutes
    a clean value for a poisoned one) depends on seeing the poison.

    The invalid token is not preserved here - timing_quality is a closed
    object on both schema lanes - so an adapter that wants the raw source
    token auditable must record it in the event-level quality block,
    never inside timing_quality, before calling this helper (AUTHORING.md
    section 3, rule 5).
    """
    timing = dict(value) if isinstance(value, dict) else {}
    timing.setdefault("time_source", "UNKNOWN")
    timing.setdefault("sync_state", "UNSYNCED")
    timing.setdefault("est_error_ms", DEFAULT_UNSYNCED_ERROR_MS)

    est = timing["est_error_ms"]
    est_is_sound = (
        isinstance(est, (int, float))
        and not isinstance(est, bool)
        and math.isfinite(est)
        and est >= 0
    )
    if not est_is_sound:
        return_ts = timing.get("last_sync_ts")
        timing["last_sync_ts"] = (
            normalize_utc_z(return_ts) or normalize_utc_z(event_ts) or utc_now_z()
        )
        return timing

    degraded = False
    timing["time_source"], fell = _fold_to_vocabulary(
        timing["time_source"], TIME_SOURCE_VALUES, "UNKNOWN"
    )
    degraded = degraded or fell
    timing["sync_state"], fell = _fold_to_vocabulary(
        timing["sync_state"], SYNC_STATE_VALUES, "UNSYNCED"
    )
    degraded = degraded or fell
    if degraded:
        timing["est_error_ms"] = max(est, DEFAULT_UNSYNCED_ERROR_MS)

    timing["last_sync_ts"] = (
        normalize_utc_z(timing.get("last_sync_ts"))
        or normalize_utc_z(event_ts)
        or utc_now_z()
    )
    return timing
