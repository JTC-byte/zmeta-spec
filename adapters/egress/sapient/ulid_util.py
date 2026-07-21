"""Shared ULID helpers for the SAPIENT (BSI Flex 335 v2.0) egress adapters.

Stock SAPIENT middleware (Apex `strictIdFormat`, on by default) validates
SapientMessage ids — `report_id`, `object_id`, `task_id` — with the proto
`is_ulid` check. These helpers keep the egress id discipline canonical:
a ULID's 48-bit timestamp component is always sourced from the event's
own time (the caller supplies it), never a wall-clock read — stamping
translate-time wall clock into an id would fabricate freshness.

Stdlib only.
"""

import os

_CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
_CROCKFORD_SET = frozenset(_CROCKFORD + _CROCKFORD.lower())


def ulid_from_ts_ms(ts_ms):
    """Mint a canonical 26-char uppercase Crockford base32 ULID.

    The 48-bit timestamp component is `ts_ms` — the caller supplies the
    event's own time in Unix epoch milliseconds; this function never
    reads the wall clock, so the ULID's embedded time is an honest claim
    about the event, not about translation time. The 80-bit randomness
    component comes from os.urandom. Output satisfies the SAPIENT proto
    `is_ulid` validation (Apex strictIdFormat).
    """
    if isinstance(ts_ms, bool) or not isinstance(ts_ms, int):
        raise ValueError("ts_ms must be an int (Unix epoch milliseconds)")
    if not 0 <= ts_ms < 1 << 48:
        raise ValueError("ts_ms out of the 48-bit ULID timestamp range")
    value = (ts_ms << 80) | int.from_bytes(os.urandom(10), "big")
    return "".join(_CROCKFORD[(value >> shift) & 0x1F] for shift in range(125, -1, -5))


def is_ulid(value):
    """Return True iff `value` passes the SAPIENT proto `is_ulid` check.

    A ULID is exactly 26 characters over the Crockford base32 alphabet
    (0123456789ABCDEFGHJKMNPQRSTVWXYZ), case-insensitive per the ULID
    spec, with the first character <= '7' (the 48-bit timestamp bound).
    """
    if not isinstance(value, str) or len(value) != 26:
        return False
    if value[0] not in "01234567":
        return False
    return all(ch in _CROCKFORD_SET for ch in value)
