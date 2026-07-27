"""
Compact binary mapping for ZMeta (CBOR + integer keys).

This module provides a fail-closed compact wire format intended for Profile L
links. It encodes only zmeta_version "1.0" events, and only those it can
expand back to a value-identical canonical JSON envelope; anything else is
refused with CompactUnrepresentableError rather than silently reduced. The
compact wire therefore carries locked-v1.0 semantics by definition, and
decode's "1.0" stamp is honest for every packet this encoder can produce.

"Value-identical" is exact except for the two representation
normalizations the mapping itself declares (spec/compact-binary-mapping.md):
UUID hex case (UUIDs travel as 16 raw bytes; RFC 4122 is case-insensitive)
and timestamp formatting at the declared millisecond resolution. A
truncated sub-millisecond instant is a different instant and is refused —
including below microsecond resolution, where a parsed-value comparison
cannot see the loss because both sides truncate identically.

Representability is a property of the MAPPING, not of the local install.
Limits the mapping imposes (notably the CBOR 64-bit integer range and the
canonical JSON value model) are enforced here rather than delegated to
whichever CBOR backend is present, because the supported backends disagree:
an out-of-range integer that zmeta_cbor refuses, cbor2 silently encodes as a
bignum tag that a zmeta_cbor consumer then decodes as raw bytes. Two
conforming nodes must never disagree about what an event means.
"""

from __future__ import annotations

import math
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Tuple

try:
    import cbor2
except ImportError:  # pragma: no cover - optional dependency
    cbor2 = None

try:
    import zmeta_cbor
except ImportError:  # pragma: no cover - optional dependency
    zmeta_cbor = None


COMPACT_VERSION = 1

TOP_KEYS = {
    "compact_version": 1,
    "event": 2,
    "source": 3,
    "payload": 4,
    "confidence": 5,
    "lineage": 6,
    "profile": 7,
}

EVENT_KEYS = {
    "event_id": 1,
    "event_type": 2,
    "event_subtype": 3,
    "ts": 4,
    "t_publish": 5,
    "t_receive": 6,
}

SOURCE_KEYS = {
    "platform_id": 1,
    "node_role": 2,
    "producer": 3,
    "sensor_id": 4,
    "sw_version": 5,
}

LINEAGE_KEYS = {
    "based_on": 1,
    "transform": 2,
}

STATE_PAYLOAD_KEYS = {
    "track_id": 1,
    "geo": 2,
    "valid_for_ms": 3,
    "class": 4,
    "source_summary": 5,
    "heading_deg": 6,
    "speed_mps": 7,
}

COMMAND_PAYLOAD_KEYS = {
    "task_id": 1,
    "task_type": 2,
    "target_geo": 3,
    "geometry": 4,
    "valid_from_ts": 5,
    "valid_for_ms": 6,
    "priority": 7,
    "requires_deconfliction": 8,
}

SYSTEM_PAYLOAD_KEYS = {
    "system_type": 1,
    "state": 2,
    "metrics": 3,
}

GEO_KEYS = {
    "lat": 1,
    "lon": 2,
    "alt_m": 3,
}

GEO2D_KEYS = {
    "lat": 1,
    "lon": 2,
}

TASK_ACK_METRICS_KEYS = {
    "task_id": 1,
    "original_event_id": 2,
    "reason_code": 3,
}

LINK_STATUS_METRICS_KEYS = {
    "link_id": 1,
    "latency_ms": 2,
    "packet_loss_pct": 3,
    "throughput_bps": 4,
    "rssi_dbm": 5,
    "snr_db": 6,
    "jitter_ms": 7,
    "reason_code": 8,
    "interface": 9,
}

TIME_STATUS_METRICS_KEYS = {
    "time_source": 1,
    "sync_state": 2,
    "est_error_ms": 3,
    "last_sync_ts": 4,
}

SCHEMA_VIOLATION_METRICS_KEYS = {
    "reason_code": 1,
    "original_event_id": 2,
    "path": 3,
    "error": 4,
}

EVENT_TYPE_MAP = {
    "OBSERVATION_EVENT": 1,
    "INFERENCE_EVENT": 2,
    "FUSION_EVENT": 3,
    "STATE_EVENT": 4,
    "COMMAND_EVENT": 5,
    "SYSTEM_EVENT": 6,
}

NODE_ROLE_MAP = {
    "EDGE": 1,
    "GATEWAY": 2,
    "APEX": 3,
    "DMZ": 4,
    "CLOUD": 5,
}

PROFILE_MAP = {"L": 1, "M": 2, "H": 3}

EVENT_SUBTYPE_MAP = {
    "TRACK_STATE": 1,
    "GOTO": 2,
    "TASK_ACK": 3,
    "LINK_STATUS": 4,
    "TIME_STATUS": 5,
    "SCHEMA_VIOLATION": 6,
    "TRACK_FUSION": 7,
    "CLASSIFICATION": 8,
    "ASSOCIATION": 9,
    "ANOMALY": 10,
    "BEHAVIOR": 11,
    "RF": 12,
    "EO": 13,
    "IR": 14,
    "ACOUSTIC": 15,
    "NETWORK": 16,
    "ORBIT": 17,
    "HOLD": 18,
    "SEARCH_BOX": 19,
}

SYSTEM_TYPE_MAP = {
    "LINK_STATUS": 1,
    "TIME_STATUS": 2,
    "SCHEMA_VIOLATION": 3,
    "TASK_ACK": 4,
}

TASK_TYPE_MAP = {
    "GOTO": 1,
    "ORBIT": 2,
    "HOLD": 3,
    "SEARCH_BOX": 4,
}

PRIORITY_MAP = {
    "LOW": 1,
    "MED": 2,
    "HIGH": 3,
}

TIME_SOURCE_MAP = {
    "GPS_PPS": 1,
    "GPS_NMEA": 2,
    "NTP": 3,
    "PTP": 4,
    "MANUAL": 5,
    "UNKNOWN": 6,
}

SYNC_STATE_MAP = {
    "LOCKED": 1,
    "HOLDOVER": 2,
    "UNSYNCED": 3,
}

TASK_ACK_STATE_MAP = {
    "RECEIVED": 1,
    "ACCEPTED": 2,
    "REJECTED": 3,
    "EXECUTING": 4,
    "COMPLETED": 5,
    "FAILED": 6,
    "CANCELLED": 7,
    "EXPIRED": 8,
    "DUPLICATE_IGNORED": 9,
}

LINK_STATUS_STATE_MAP = {
    "UP": 1,
    "DEGRADED": 2,
    "DOWN": 3,
    "UNKNOWN": 4,
}

REASON_CODE_MAP = {
    "SCHEMA_INVALID": 1,
    "EVENT_TYPE_NOT_ALLOWED_FOR_ROLE": 2,
    "EVENT_TYPE_NOT_ALLOWED_FOR_PROFILE": 3,
    "COMMAND_NOT_DECONFLICTED": 4,
    "COMMAND_HAS_ALTITUDE": 5,
    "OBSERVATION_HAS_IDENTITY": 6,
    "INFERENCE_HAS_TRACK_ID": 7,
    "STATE_HAS_RAW_FEATURES": 8,
    "SCHEMA_VIOLATION_MISSING_REASON_CODE": 9,
    "SCHEMA_VIOLATION_MISSING_ORIGINAL_EVENT_ID": 10,
    "SCHEMA_VIOLATION_INVALID_REASON_CODE": 11,
    "TASK_ACK_MISSING_TASK_ID": 12,
    "TASK_ACK_MISSING_REQUIRED_FIELD": 13,
    "TASK_ACK_MISSING_ORIGINAL_EVENT_ID": 14,
    "TASK_ACK_MISSING_REASON_CODE": 15,
    "TASK_ACK_INVALID_STATE": 16,
    "TASK_ACK_INVALID_REASON_CODE": 17,
    "LINK_STATUS_MISSING_REQUIRED_FIELD": 18,
    "LINK_STATUS_INVALID_STATE": 19,
    "LINK_STATUS_MISSING_REASON_CODE": 20,
    "LINK_STATUS_INVALID_REASON_CODE": 21,
    "PRODUCER_NOT_ALLOWED": 22,
    "TASK_DUPLICATE": 23,
    "TASK_EXPIRED": 24,
    "TASK_CANCELLED": 25,
    "TASK_FAILED": 26,
    "TASK_ABORTED": 27,
    "TASK_REJECTED": 28,
    "LINK_LOSS": 29,
    "LOW_RSSI": 30,
    "HIGH_LATENCY": 31,
    "HIGH_PACKET_LOSS": 32,
    "LOW_THROUGHPUT": 33,
    "INTERFERENCE": 34,
    "JAMMED": 35,
    "BACKHAUL_DOWN": 36,
    "NO_ROUTE": 37,
    "CONFIG_ERROR": 38,
    "POWER_SAVE": 39,
    "UNKNOWN_CAUSE": 40,
    "TIMING_STATUS_AGE_NEGATIVE": 41,
}


def _reverse_map(mapping: Dict[str, int]) -> Dict[int, str]:
    return {value: key for key, value in mapping.items()}


EVENT_TYPE_REV = _reverse_map(EVENT_TYPE_MAP)
NODE_ROLE_REV = _reverse_map(NODE_ROLE_MAP)
PROFILE_REV = _reverse_map(PROFILE_MAP)
EVENT_SUBTYPE_REV = _reverse_map(EVENT_SUBTYPE_MAP)
SYSTEM_TYPE_REV = _reverse_map(SYSTEM_TYPE_MAP)
TASK_TYPE_REV = _reverse_map(TASK_TYPE_MAP)
PRIORITY_REV = _reverse_map(PRIORITY_MAP)
TIME_SOURCE_REV = _reverse_map(TIME_SOURCE_MAP)
SYNC_STATE_REV = _reverse_map(SYNC_STATE_MAP)
TASK_ACK_STATE_REV = _reverse_map(TASK_ACK_STATE_MAP)
LINK_STATUS_STATE_REV = _reverse_map(LINK_STATUS_STATE_MAP)
REASON_CODE_REV = _reverse_map(REASON_CODE_MAP)


def _require_cbor():
    if cbor2 is None and zmeta_cbor is None:
        raise SystemExit("CBOR support requires cbor2 or zmeta_cbor.")


class CompactUnrepresentableError(ValueError):
    """Raised when an event cannot be encoded to compact without loss."""


# Declared representation normalizations (spec/compact-binary-mapping.md):
# UUIDs travel as 16 raw bytes, so hex case is not carried and decode emits
# the RFC 4122 canonical lowercase form; timestamps travel as epoch
# milliseconds, so the decoded string is that instant re-formatted. Neither
# changes the VALUE, so neither is loss. Anything else - a dropped field, a
# relabeled version, a truncated sub-millisecond instant - is loss and is
# refused.
_CANONICAL_UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)
_UTC_TS_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$")


def _same_uuid(left: str, right: str) -> bool:
    """True when both are the same UUID differing only in hex case."""
    return (
        _CANONICAL_UUID_RE.match(left) is not None
        and _CANONICAL_UUID_RE.match(right) is not None
        and left.lower() == right.lower()
    )


def _instant(value: Any):
    """Parse a UTC-Z timestamp, or None when it is not one."""
    if not isinstance(value, str) or _UTC_TS_RE.match(value) is None:
        return None
    try:
        return datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return None


def _is_millisecond_resolution(value: str) -> bool:
    """True when a UTC-Z timestamp carries no precision finer than 1 ms."""
    match = _UTC_TS_RE.match(value)
    if match is None:
        return False
    fraction = (match.group(1) or ".")[1:]
    return fraction[3:].strip("0") == ""


def _same_instant(left: str, right: str) -> bool:
    """True when both timestamps denote exactly the same instant.

    Sub-millisecond precision is genuinely lost by the epoch-ms mapping, so
    a truncated timestamp denotes a DIFFERENT instant and is not equivalent.

    The resolution of the ORIGINAL is checked directly rather than inferred
    from the parsed values: datetime.fromisoformat truncates at microseconds,
    so both sides of a comparison lose sub-microsecond digits identically and
    a parsed-value check cannot see that loss. Without this, a
    100-nanosecond instant (".8760001Z") compared equal to its millisecond
    round-trip and the codec silently dropped precision while claiming to
    refuse truncation.
    """
    parsed = _instant(left)
    if parsed is None or parsed != _instant(right):
        return False
    return _is_millisecond_resolution(left)


def _semantic_difference(original: Any, restored: Any, path: str = "$"):
    """First value-changing difference, or None when only normalized.

    Returns a human-readable path/reason string for the first difference
    that changes meaning, treating the codec's declared representation
    normalizations (above) as equivalent.

    This check is STRUCTURALLY BLIND to values outside the canonical JSON
    model and cannot be made to see them: both sides hold the same non-JSON
    object (a set, a CBORTag, a bytes blob, a non-string map key), so `==`
    is satisfied and nothing looks lost. That whole class is enforced by
    _find_unrepresentable instead, which is why the scan must run before the
    encode rather than being folded into this comparison.
    """
    if isinstance(original, dict) and isinstance(restored, dict):
        for key in original:
            if key not in restored:
                return f"{path}.{key} (dropped by compact encoding)"
        for key in restored:
            if key not in original:
                return f"{path}.{key} (introduced by compact decoding)"
        for key in original:
            difference = _semantic_difference(original[key], restored[key], f"{path}.{key}")
            if difference is not None:
                return difference
        return None
    if isinstance(original, list) and isinstance(restored, list):
        if len(original) != len(restored):
            return f"{path} (length {len(original)} != {len(restored)})"
        for idx, (left, right) in enumerate(zip(original, restored)):
            difference = _semantic_difference(left, right, f"{path}[{idx}]")
            if difference is not None:
                return difference
        return None
    # Non-finite floats have no canonical JSON form (RFC 8259), so they can
    # never survive the wire honestly even when CBOR carries them.
    if isinstance(original, float) and not math.isfinite(original):
        return f"{path} (non-finite float {original!r} has no canonical JSON form)"
    if isinstance(restored, float) and not math.isfinite(restored):
        return f"{path} (decoded to non-finite float {restored!r})"
    # bool is an int subclass; True must never compare equal to 1 here.
    if isinstance(original, bool) != isinstance(restored, bool):
        return f"{path} ({original!r} != {restored!r})"
    if original == restored:
        return None
    if isinstance(original, str) and isinstance(restored, str):
        if _same_uuid(original, restored) or _same_instant(original, restored):
            return None
    return f"{path} ({original!r} != {restored!r})"


# CBOR major types 0 and 1 carry integers in [-(2**64), 2**64 - 1]. Anything
# outside needs a bignum tag, which this mapping does not define — so an
# out-of-range integer is not representable in compact, full stop.
#
# This must be enforced by the CODEC, not left to the backend, because the
# two supported backends disagree: zmeta_cbor raises OverflowError (correct),
# while cbor2 silently emits tag 2/3 — and a zmeta_cbor consumer decodes that
# tag as raw BYTES, not an integer. Left to the backend, the same event would
# mean different things on two conforming ZMeta nodes depending on which CBOR
# library each happened to install, which is precisely the interoperability
# failure this format exists to prevent. Representability is a property of the
# mapping, never of the local install.
_CBOR_INT_MIN = -(2**64)
_CBOR_INT_MAX = 2**64 - 1


# The same argument, one level up from the integer range: CBOR can carry a
# whole family of values the canonical ZMeta envelope cannot express at all.
#
# `spec/compact-binary-mapping.md` already governs this. Encoders MUST refuse
# any event "that would not expand back to a value-identical canonical
# envelope", and the clause names non-finite floats as its worked example
# precisely because they are values "CBOR can carry but canonical JSON
# (RFC 8259) cannot represent, so they could never decode back to a valid
# canonical envelope". Non-finite floats are one member of that class. The
# rest of it was never enforced, so the round-trip check waved it through:
# both sides of the comparison are the SAME non-JSON object, so `==` is
# satisfied and nothing looks lost. Measured on HEAD before this check, all
# through the public `dumps()` on a schema-valid Profile-L STATE:
#
#   accepted on cbor2 only  set, frozenset, Decimal, datetime, date, UUID,
#                           re.Pattern, IPv4Address, frozendict,
#                           CBORSimpleValue, undefined, complex
#   accepted on BOTH        bytes, bytearray, and any non-string map key
#                           (int, big int, float, bool, None, bytes, tuple)
#
# Two failures, not one. The cbor2-only rows are backend-dependent
# representability - the exact sentence this module's header forbids, and the
# B-01/R2-04 finding (a `set` carrying a 2**70 integer left compact egress as
# a bignum tag: a cbor2 consumer read an integer, a zmeta_cbor consumer read a
# list of raw bytes, neither errored). The both-backends rows are a private
# dialect: a channel two compact nodes can use that no other ZMeta encoding
# can express, which is the interoperability guarantee failing quietly.
#
# So the rule is stated positively, as an ALLOWLIST of the canonical JSON
# value model. A blocklist of container types would have to be re-derived
# every time a backend learns a new tag; an allowlist refuses the unknown by
# construction and needs no maintenance. It also means the walk below never
# has to descend into an exotic container - it refuses at the container
# itself, which closes the tuple-mediated cycle that used to fall through to
# the backend and produce two different refusal reasons for one event.
_JSON_SCALARS: Tuple[type, ...] = (str, bool, float)
_JSON_CONTAINERS: Tuple[type, ...] = (dict, list)


# Traversal modes for the explicit-stack walk below: _LEAVE marks the point
# where a container's whole subtree has been popped, so it can come back off
# the "currently on this path" set.
_ENTER = object()
_LEAVE = object()


def _joined_path(link) -> str:
    """Materialize a parent-linked path chain into its "$.a[0].b" form."""
    parts = []
    while link is not None:
        text, link = link
        parts.append(text)
    parts.reverse()
    return "".join(parts)


def _find_unrepresentable(value: Any, path: str = "$"):
    """The mapping-limit scan. First integer outside the CBOR 64-bit range,
    or None.

    Two kinds of finding come out of this walk, and they leave by two
    different doors:

      RETURNED  an integer outside the CBOR 64-bit range. The caller composes
                it with the mapping's range explanation, because the reason
                is a property of the mapping rather than of the value.
      RAISED    a value the canonical envelope cannot express at all - an
                exotic type, a non-string map key, a reference cycle. Each
                carries its own reason and its own honest advice, which
                differ per case, so they are raised where they are found
                rather than flattened into one caller-side message. Raising
                is safe: the sole production caller invokes this from inside
                the guard's try, whose first handler re-raises
                CompactUnrepresentableError unchanged.

    The type allowlist (_JSON_SCALARS / _JSON_CONTAINERS above) is checked by
    `isinstance`, not by exact type, so a str/int/float/dict/list SUBCLASS is
    accepted: it is value-identical to its base in canonical JSON, which is
    the only question this mapping asks. `bool` is listed as a scalar in its
    own right and tested before `int`, so it never reaches the range check.

    Iterative depth-first traversal, for the same reason as
    validators._find_forbidden_key: recursing here tied the process stack to
    sender-controlled nesting depth, and this scan runs on the encode path
    where the fail-closed guard lives. A deeply nested but schema-valid
    payload therefore raised a raw RecursionError out of the public API from
    IN FRONT of the try/except in _verified_compact_bytes whose whole job is
    to turn that into a CompactUnrepresentableError refusal. An explicit
    stack removes the interpreter-limit dependency instead of catching it.

    Traversal order is unchanged (same pre-order walk, same first offender
    reported). Path chains are parent-linked rather than concatenated at
    every level, so hostile depth costs linear memory rather than quadratic
    string building -- trading a crash for a hang is not a refusal.

    The walk also has to TERMINATE. The first iterative version had neither a
    visited set nor a bound, so a self-referential structure spun forever with
    the heap rising -- exactly the crash-for-hang trade the paragraph above
    forbids, made worse because the old recursive version had at least ended
    in a RecursionError the guard converts into a refusal (R1-11 residual
    against the A-04 wave). This is the textbook three-colour DFS:

      on_path  containers on the current root->node chain (grey). A container
               reached again while still on that chain IS a cycle.
      scanned  containers already walked to completion (black). Re-walking one
               cannot reveal a first offender the first walk missed -- the
               scan returns on the first hit, so "finished without returning"
               means the subtree is clean -- and skipping it is what keeps a
               SHARED (acyclic) subtree from costing exponential time. CBOR
               value-sharing tags let a few hundred wire bytes expand into a
               structure with exponentially many paths.

    A bound was the alternative and is rejected FOR THIS SCAN: any node
    budget refuses some large-but-honest event, and discarding good data is
    not a safe default; the memo already makes the walk linear in distinct
    containers, so no bound is needed to terminate. The DECODE side is a
    different question with a different answer: the mapping now declares an
    expansion bound there (DEFAULT_MAX_EXPANDED_NODES, R1-11-18, adjudicated
    2026-07-27), because a consumer must never materialize an expansion it
    cannot afford, and an event whose expansion exceeds what a conforming
    consumer will decode is not deliverable anyway.

    A reference cycle has no finite CBOR encoding, so it is unrepresentable
    and is refused HERE, by the mapping. Left to the backend the caller gets
    two different reasons for one event -- zmeta_cbor raises RecursionError
    ("nesting too deep", which names the wrong cause) and cbor2 raises
    CBOREncodeValueError -- and which one an operator sees would depend on the
    local install.
    """
    stack = [(_ENTER, value, (path, None), 0)]
    on_path = set()
    scanned = set()
    while stack:
        mode, current, link, depth = stack.pop()
        if mode is _LEAVE:
            on_path.discard(id(current))
            continue
        if isinstance(current, _JSON_CONTAINERS):
            # The declared nesting maximum is a property of the MAPPING
            # (spec: compact v1 cannot represent deeper), so it is enforced
            # here on the encode path too -- BEFORE any backend serializer
            # runs. This is not the rejected node budget from the paragraph
            # above: a depth-65 event has no compact encoding at all, so
            # refusing it discards nothing deliverable. Found the hard way
            # (post-release CI, 2026-07-27): a C-extension cbor2 backend
            # recurses on sender-controlled depth and SEGFAULTS the process
            # where the pure-Python backends raise a catchable error -- the
            # guard must fire before the structure ever reaches a backend.
            if depth > COMPACT_MAX_DEPTH:
                raise CompactUnrepresentableError(
                    f"compact cannot encode {_joined_path(link)}: nesting "
                    "depth exceeds the compact mapping's declared maximum "
                    f"of {COMPACT_MAX_DEPTH}, so no conforming consumer "
                    "could decode it; refused before any backend encoder "
                    "runs"
                )
            marker = id(current)
            if marker in on_path:
                raise CompactUnrepresentableError(
                    f"compact cannot encode {_joined_path(link)}: the "
                    "structure refers back to itself, and a reference cycle "
                    "has no finite encoding in CBOR or in canonical JSON, so "
                    "no ZMeta encoding can carry it; the producer must emit "
                    "an acyclic event"
                )
            if marker in scanned:
                continue
            on_path.add(marker)
            scanned.add(marker)
            stack.append((_LEAVE, current, link, depth))
            if isinstance(current, dict):
                # Keys are scanned as well as values -- the walk used to push
                # values only, so nothing about a key was ever checked. A
                # canonical JSON object key is a string. A non-string key
                # survives CBOR as itself (an integer key past the 64-bit
                # range becomes a bignum tag, which is where B-01 hid one
                # level deeper than the finding named) while json.dumps
                # silently stringifies it -- 1.5 to "1.5", NaN to "NaN", None
                # to "null" -- so the two encodings of one event disagree
                # about what the field is even called.
                for key, item in reversed(list(current.items())):
                    if not isinstance(key, str):
                        raise CompactUnrepresentableError(
                            f"compact cannot encode {_joined_path(link)}: the "
                            f"map key {key!r} is a {type(key).__name__} and "
                            "canonical JSON object keys are strings, so this "
                            "event has no canonical envelope to decode back "
                            "to; the producer must emit string keys"
                        )
                    stack.append((_ENTER, item, (f".{key}", link), depth + 1))
            else:
                for index in range(len(current) - 1, -1, -1):
                    stack.append(
                        (_ENTER, current[index], (f"[{index}]", link), depth + 1)
                    )
            continue
        if current is None or isinstance(current, _JSON_SCALARS):
            # Non-finite floats are the one scalar that is in the JSON value
            # model by type and outside it by value. They are refused HERE,
            # before any bytes exist, so the diagnostic names the CANONICAL
            # path the producer-side operator filters on; the decode-side
            # scan (_refuse_unexpandable) would otherwise refuse them during
            # the round-trip with a compact-integer-key path instead.
            # _semantic_difference keeps its own check as defence in depth
            # for direct callers.
            if isinstance(current, float) and not math.isfinite(current):
                raise CompactUnrepresentableError(
                    f"compact cannot encode {_joined_path(link)}: non-finite "
                    f"float {current!r} has no canonical JSON form "
                    "(RFC 8259), so no ZMeta encoding can carry it honestly; "
                    "the producer must emit a finite number"
                )
            continue
        if isinstance(current, int):
            if not _CBOR_INT_MIN <= current <= _CBOR_INT_MAX:
                return (
                    f"{_joined_path(link)} (integer {current} is outside the "
                    "CBOR 64-bit range)"
                )
            continue
        raise CompactUnrepresentableError(
            f"compact cannot encode {_joined_path(link)}: a "
            f"{type(current).__name__} is not a value the canonical ZMeta "
            "envelope can express (the event model is JSON/RFC 8259: object, "
            "array, string, number, true/false, null), so no compact packet "
            "could decode back to it; the producer must emit a canonical "
            "value"
        )
    return None


# Decode-side enforcement of the same rule (spec/compact-binary-mapping.md,
# "Value Model, Tags, and Expansion Bound"; doctrine R1-11-02/03/18,
# adjudicated 2026-07-27). The preferred backend (zmeta_cbor) refuses every
# tag at parse, but the cbor2 fallback interprets tags BEFORE this mapping
# can see them: value-sharing tags 28/29 arrive as containers reachable more
# than once (or as cycles), bignum tags 2/3 as integers outside the 64-bit
# range, and other tags as non-JSON objects. Those footprints are refused
# here, at the mapping layer, so a datagram means the same thing -- or
# refuses the same way -- on both supported installs.
#
# The expansion bound exists because value sharing lets a few hundred wire
# bytes describe a structure astronomically larger than the datagram, and
# because the cbor2 fallback has no message-size limit of its own (the
# zmeta_cbor backend caps messages at 1 MiB). Refusing sharing closes the
# front door; the bound is the declared guarantee that a decoder never
# materializes an expansion it cannot afford, whatever the door. The default
# is deliberately aligned with the 1 MiB message limit: every decoded node
# costs at least one wire byte, so no honest datagram a conforming consumer
# could decode is refused by it.
DEFAULT_MAX_EXPANDED_NODES = 1_048_576  # 2**20

# The mapping's declared nesting maximum (R1-11-03). Matches the fallback
# decoder's default max_depth: before this was a mapping-level rule, a
# 65..400-deep datagram encoded on a cbor2-only node and refused on every
# zmeta_cbor consumer -- representability depended on the local install.
COMPACT_MAX_DEPTH = 64


def _refuse_unexpandable(compact: Any, max_expanded_nodes: int | None) -> None:
    """Refuse any decoded compact structure outside the wire value model.

    Runs on every decode (decode_event calls it first), on the DECODED
    object rather than the wire bytes, because that is the only place the
    cbor2 fallback's tag interpretation can still be seen. Refusals:

      * a container reachable more than once, including cycles -- the
        footprint of CBOR value sharing (tags 28/29); a tree decode can
        never produce one, so nothing honest is refused;
      * expanded node count beyond `max_expanded_nodes` (containers plus
        values, map keys uncounted), refused BEFORE the offending
        container's children are pushed, not after materializing them;
      * nesting beyond COMPACT_MAX_DEPTH (root at depth 0), mirroring
        zmeta_cbor's decode-side accounting;
      * integers outside the CBOR 64-bit range (bignum tags 2/3);
      * non-finite floats (in the wire model by type, outside it by value);
      * map keys that are not integers or text;
      * any value outside the wire model: map, array, text, bytes
        (the transport form of UUIDs), 64-bit integer, finite float,
        boolean, null.

    Iterative for the same reason as _find_unrepresentable: this walk runs
    on sender-controlled structure and must not tie the process stack to it.
    Termination is by construction -- every container is visited at most
    once because a revisit refuses.
    """
    if max_expanded_nodes is not None and max_expanded_nodes < 0:
        raise ValueError("max_expanded_nodes must be non-negative or None")
    stack = [(compact, ("$", None), 0)]
    seen: set = set()
    nodes = 1
    while stack:
        current, link, depth = stack.pop()
        if depth > COMPACT_MAX_DEPTH:
            raise CompactUnrepresentableError(
                f"compact decode refused at {_joined_path(link)}: nesting "
                "depth exceeds the compact mapping's declared maximum of "
                f"{COMPACT_MAX_DEPTH}"
            )
        if isinstance(current, (dict, list)):
            marker = id(current)
            if marker in seen:
                raise CompactUnrepresentableError(
                    f"compact decode refused at {_joined_path(link)}: this "
                    "container is reachable more than once, which is value "
                    "sharing (CBOR tags 28/29); the compact mapping defines "
                    "no tags and no sharing, so the datagram has no single "
                    "canonical expansion"
                )
            seen.add(marker)
            nodes += len(current)
            if max_expanded_nodes is not None and nodes > max_expanded_nodes:
                raise CompactUnrepresentableError(
                    "compact decode refused: the datagram expands to more "
                    f"than {max_expanded_nodes} nodes (max_expanded_nodes="
                    f"{max_expanded_nodes}); refusing to materialize the "
                    "expansion"
                )
            if isinstance(current, dict):
                for key, item in current.items():
                    if isinstance(key, bool) or not isinstance(key, (int, str)):
                        raise CompactUnrepresentableError(
                            f"compact decode refused at {_joined_path(link)}: "
                            f"the map key {key!r} is a {type(key).__name__}; "
                            "compact map keys are integers (assigned by this "
                            "mapping) or text, and fabricating a text key "
                            "from anything else names a field the producer "
                            "never sent"
                        )
                    stack.append((item, (f".{key}", link), depth + 1))
            else:
                for index in range(len(current) - 1, -1, -1):
                    stack.append(
                        (current[index], (f"[{index}]", link), depth + 1)
                    )
            continue
        if current is None or isinstance(current, (str, bytes, bytearray)):
            continue
        if isinstance(current, bool):
            continue
        if isinstance(current, float):
            if not math.isfinite(current):
                raise CompactUnrepresentableError(
                    f"compact decode refused at {_joined_path(link)}: "
                    f"non-finite float {current!r} has no canonical JSON "
                    "form (RFC 8259), so this datagram cannot expand to a "
                    "canonical envelope"
                )
            continue
        if isinstance(current, int):
            if not _CBOR_INT_MIN <= current <= _CBOR_INT_MAX:
                raise CompactUnrepresentableError(
                    f"compact decode refused at {_joined_path(link)}: "
                    f"integer {current} is outside the CBOR 64-bit range "
                    "and this mapping defines no bignum tag"
                )
            continue
        raise CompactUnrepresentableError(
            f"compact decode refused at {_joined_path(link)}: a "
            f"{type(current).__name__} is not a value the compact wire "
            "model defines (map, array, text, bytes, 64-bit integer, "
            "finite float, boolean, null); refusing to reinterpret it"
        )


def _encode_compact_bytes(compact: Dict[int, Any]) -> bytes:
    _require_cbor()
    if zmeta_cbor is not None:
        return zmeta_cbor.dumps(compact)
    return cbor2.dumps(compact, canonical=True)


# Every codec failure must leave _verified_compact_bytes as a refusal, and the
# two supported backends do not agree on base classes: zmeta_cbor raises
# built-ins, while cbor2's CBOREncodeError / CBORDecodeError descend from
# CBORError -> Exception and are NOT ValueError subclasses. Naming only the
# built-ins let a cbor2 install raise a raw CBORDecodeError ("maximum
# container nesting depth (400) exceeded") straight out of the public API,
# past the guard, for the same deep-nesting input class the guard names.
# Representability must not depend on which CBOR library is installed.
_CODEC_FAILURES: Tuple[type, ...] = (
    OverflowError,
    ValueError,
    OSError,
    RecursionError,
    TypeError,
)
_CBOR2_ERROR = getattr(cbor2, "CBORError", None) if cbor2 is not None else None
if _CBOR2_ERROR is not None:
    _CODEC_FAILURES = _CODEC_FAILURES + (_CBOR2_ERROR,)


def _verified_compact_bytes(event: Dict[str, Any]) -> bytes:
    """Encode to compact bytes, refusing anything not representable.

    Verification runs through the REAL serialization boundary
    (bytes -> decode) rather than an in-memory key remap: the remap
    preserves object identity, and Python's container equality
    short-circuits on identity, so values that are not equal to
    themselves (NaN) would otherwise pass verification and reach the wire.

    Any event the codec cannot serialize honestly is an unrepresentable
    event, so the codec's own encode/decode failures are surfaced as
    CompactUnrepresentableError (the single exception egress callers and
    the gateway ladder handle) rather than escaping as a raw
    OverflowError / ValueError / OSError / RecursionError / TypeError
    and, in the gateway, terminating the receive loop. Examples that reach
    here on SCHEMA-VALID input: extension nesting beyond the CBOR decode
    depth limit (a conforming compact CONSUMER could not decode it
    either) and an epoch-ms value outside the representable datetime
    range.

    Mapping-level limits are checked HERE rather than left to whichever
    CBOR backend is installed, so an event is representable or not by the
    same rule everywhere (see _find_unrepresentable).

    EVERY traversal of caller-supplied structure runs INSIDE the guard. The
    pre-checks used to sit in front of it, so the one failure mode the guard
    names by name -- RecursionError on hostile nesting -- escaped it
    (R1-11 fresh-audit A-04). _find_unrepresentable is now iterative and
    cannot raise it at all; _semantic_difference is still recursive, so its
    call belongs under the same try rather than after it. Nothing that walks
    the event may be moved back out.
    """
    version = event.get("zmeta_version") if isinstance(event, dict) else None
    if version != "1.0":
        raise CompactUnrepresentableError(
            f"compact encodes zmeta_version '1.0' events only, got {version!r}; "
            "use a version-preserving encoding (json/cbor/proto)"
        )
    try:
        oversized = _find_unrepresentable(event)
        if oversized is not None:
            raise CompactUnrepresentableError(
                f"compact cannot encode {oversized}; CBOR major types 0/1 carry "
                "only [-(2**64), 2**64-1] and this mapping defines no bignum tag; "
                "use a version-preserving encoding (json/cbor/proto)"
            )
        payload = _encode_compact_bytes(encode_event(event))
        restored = decode_event(_decode_cbor(payload))
        difference = _semantic_difference(event, restored)
    except CompactUnrepresentableError:
        raise
    except _CODEC_FAILURES as exc:
        raise CompactUnrepresentableError(
            f"compact cannot serialize this event ({type(exc).__name__}: {exc}); "
            "use a version-preserving encoding (json/cbor/proto)"
        ) from exc
    if difference is not None:
        raise CompactUnrepresentableError(
            f"compact encoding would lose or alter content at {difference}; "
            "refusing lossy encode"
        )
    return payload


def verify_representable(event: Dict[str, Any]) -> None:
    """Refuse any event the compact mapping cannot round-trip losslessly.

    The compact wire has no zmeta_version key and enumerated field tables, so
    encoding is only honest when decode reproduces the event's meaning
    exactly. Callers on egress paths MUST invoke this (dumps() does) so
    unrepresentable content is refused instead of silently reduced and
    relabeled "1.0".
    """
    _verified_compact_bytes(event)


def dumps(event: Dict[str, Any]) -> bytes:
    return _verified_compact_bytes(event)


def loads(data: bytes, **decode_limits) -> Dict[str, Any]:
    # max_expanded_nodes is a MAPPING limit enforced by decode_event, not a
    # CBOR-layer knob, so it is peeled off here and works on either backend
    # (the remaining decode_limits still require zmeta_cbor).
    max_expanded_nodes = decode_limits.pop(
        "max_expanded_nodes", DEFAULT_MAX_EXPANDED_NODES
    )
    compact = _decode_cbor(data, **decode_limits)
    return decode_event(compact, max_expanded_nodes=max_expanded_nodes)


def is_compact(obj: Any) -> bool:
    if not isinstance(obj, dict):
        return False
    return any(isinstance(key, int) for key in obj.keys())


def _reject_unknown_integer_keys(mapping: Dict[Any, Any], known_keys: set[int], context: str) -> None:
    unknown = sorted(key for key in mapping if isinstance(key, int) and key not in known_keys)
    if unknown:
        raise ValueError(f"Unknown compact integer key in {context}: {unknown[0]}")


def encode_event(event: Dict[str, Any]) -> Dict[int, Any]:
    out: Dict[int, Any] = {}
    out[TOP_KEYS["compact_version"]] = COMPACT_VERSION

    event_block = event.get("event", {})
    source = event.get("source", {})
    payload = event.get("payload", {})

    if event_block:
        out[TOP_KEYS["event"]] = _encode_event_block(event_block)
    if source:
        out[TOP_KEYS["source"]] = _encode_source(source)
    if payload is not None:
        out[TOP_KEYS["payload"]] = _encode_payload(payload, event_block.get("event_type"))

    if "confidence" in event:
        out[TOP_KEYS["confidence"]] = event.get("confidence")
    if "lineage" in event:
        out[TOP_KEYS["lineage"]] = _encode_lineage(event.get("lineage", {}))
    if "profile" in event:
        out[TOP_KEYS["profile"]] = _map_enum(event.get("profile"), PROFILE_MAP)

    return out


def decode_event(
    compact: Dict[int, Any],
    *,
    max_expanded_nodes: int | None = DEFAULT_MAX_EXPANDED_NODES,
) -> Dict[str, Any]:
    if not isinstance(compact, dict):
        raise ValueError("compact shape must be a map")
    # The fail-closed scan runs HERE rather than only in loads() because
    # the gateway compact ingress calls decode_event directly on whatever
    # its CBOR layer produced (gateway._decode_message), and on a
    # cbor2-only install that object can carry tag footprints -- shared or
    # cyclic containers, out-of-range integers, non-JSON values -- that
    # this mapping must refuse, never partially interpret.
    _refuse_unexpandable(compact, max_expanded_nodes)
    _reject_unknown_integer_keys(compact, set(TOP_KEYS.values()), "top-level")

    event: Dict[str, Any] = {"zmeta_version": "1.0"}

    if TOP_KEYS["compact_version"] in compact:
        version = compact.get(TOP_KEYS["compact_version"])
        if version != COMPACT_VERSION:
            raise ValueError(f"Unsupported compact_version: {version}")

    event_block = compact.get(TOP_KEYS["event"])
    if isinstance(event_block, dict):
        event["event"] = _decode_event_block(event_block)

    source = compact.get(TOP_KEYS["source"])
    if isinstance(source, dict):
        event["source"] = _decode_source(source)

    payload = compact.get(TOP_KEYS["payload"])
    if payload is not None and "event" in event:
        event_type = event["event"].get("event_type")
        event["payload"] = _decode_payload(payload, event_type)
    elif payload is not None:
        event["payload"] = payload

    if TOP_KEYS["confidence"] in compact:
        event["confidence"] = compact.get(TOP_KEYS["confidence"])
    if TOP_KEYS["lineage"] in compact:
        event["lineage"] = _decode_lineage(compact.get(TOP_KEYS["lineage"]))
    if TOP_KEYS["profile"] in compact:
        event["profile"] = _unmap_enum(compact.get(TOP_KEYS["profile"]), PROFILE_REV)

    return event


def _decode_cbor(data: bytes, **decode_limits) -> Any:
    _require_cbor()
    if zmeta_cbor is not None:
        return zmeta_cbor.loads(data, **decode_limits)
    if decode_limits:
        raise ValueError("compact decode limits require zmeta_cbor")
    return cbor2.loads(data)


def _encode_event_block(block: Dict[str, Any]) -> Dict[int, Any]:
    out: Dict[int, Any] = {}
    event_id = block.get("event_id")
    if event_id is not None:
        out[EVENT_KEYS["event_id"]] = _uuid_to_bytes(event_id)
    event_type = block.get("event_type")
    if event_type is not None:
        out[EVENT_KEYS["event_type"]] = _map_enum(event_type, EVENT_TYPE_MAP)
    event_subtype = block.get("event_subtype")
    if event_subtype is not None:
        out[EVENT_KEYS["event_subtype"]] = _map_enum(event_subtype, EVENT_SUBTYPE_MAP)
    ts = block.get("ts")
    if ts is not None:
        out[EVENT_KEYS["ts"]] = _parse_ts(ts)
    t_publish = block.get("t_publish")
    if t_publish is not None:
        out[EVENT_KEYS["t_publish"]] = _parse_ts(t_publish)
    t_receive = block.get("t_receive")
    if t_receive is not None:
        out[EVENT_KEYS["t_receive"]] = _parse_ts(t_receive)
    return out


def _decode_event_block(block: Dict[int, Any]) -> Dict[str, Any]:
    _reject_unknown_integer_keys(block, set(EVENT_KEYS.values()), "event")
    out: Dict[str, Any] = {}
    if EVENT_KEYS["event_id"] in block:
        out["event_id"] = _uuid_from_bytes(block.get(EVENT_KEYS["event_id"]))
    if EVENT_KEYS["event_type"] in block:
        out["event_type"] = _unmap_enum(block.get(EVENT_KEYS["event_type"]), EVENT_TYPE_REV)
    if EVENT_KEYS["event_subtype"] in block:
        out["event_subtype"] = _unmap_enum(block.get(EVENT_KEYS["event_subtype"]), EVENT_SUBTYPE_REV)
    if EVENT_KEYS["ts"] in block:
        out["ts"] = _format_ts(block.get(EVENT_KEYS["ts"]))
    if EVENT_KEYS["t_publish"] in block:
        out["t_publish"] = _format_ts(block.get(EVENT_KEYS["t_publish"]))
    if EVENT_KEYS["t_receive"] in block:
        out["t_receive"] = _format_ts(block.get(EVENT_KEYS["t_receive"]))
    return out


def _encode_source(source: Dict[str, Any]) -> Dict[int, Any]:
    out: Dict[int, Any] = {}
    if source.get("platform_id") is not None:
        out[SOURCE_KEYS["platform_id"]] = source.get("platform_id")
    if source.get("node_role") is not None:
        out[SOURCE_KEYS["node_role"]] = _map_enum(source.get("node_role"), NODE_ROLE_MAP)
    if source.get("producer") is not None:
        out[SOURCE_KEYS["producer"]] = source.get("producer")
    if source.get("sensor_id") is not None:
        out[SOURCE_KEYS["sensor_id"]] = source.get("sensor_id")
    if source.get("sw_version") is not None:
        out[SOURCE_KEYS["sw_version"]] = source.get("sw_version")
    return out


def _decode_source(source: Dict[int, Any]) -> Dict[str, Any]:
    _reject_unknown_integer_keys(source, set(SOURCE_KEYS.values()), "source")
    out: Dict[str, Any] = {}
    if SOURCE_KEYS["platform_id"] in source:
        out["platform_id"] = source.get(SOURCE_KEYS["platform_id"])
    if SOURCE_KEYS["node_role"] in source:
        out["node_role"] = _unmap_enum(source.get(SOURCE_KEYS["node_role"]), NODE_ROLE_REV)
    if SOURCE_KEYS["producer"] in source:
        out["producer"] = source.get(SOURCE_KEYS["producer"])
    if SOURCE_KEYS["sensor_id"] in source:
        out["sensor_id"] = source.get(SOURCE_KEYS["sensor_id"])
    if SOURCE_KEYS["sw_version"] in source:
        out["sw_version"] = source.get(SOURCE_KEYS["sw_version"])
    return out


def _encode_lineage(lineage: Dict[str, Any]) -> Dict[int, Any]:
    out: Dict[int, Any] = {}
    based_on = lineage.get("based_on")
    if based_on is not None:
        out[LINEAGE_KEYS["based_on"]] = [_uuid_to_bytes(value) for value in based_on]
    if lineage.get("transform") is not None:
        out[LINEAGE_KEYS["transform"]] = lineage.get("transform")
    return out


def _decode_lineage(lineage: Any) -> Any:
    if not isinstance(lineage, dict):
        return lineage
    _reject_unknown_integer_keys(lineage, set(LINEAGE_KEYS.values()), "lineage")
    out: Dict[str, Any] = {}
    if LINEAGE_KEYS["based_on"] in lineage:
        values = lineage.get(LINEAGE_KEYS["based_on"], [])
        out["based_on"] = [_uuid_from_bytes(value) for value in values]
    if LINEAGE_KEYS["transform"] in lineage:
        out["transform"] = lineage.get(LINEAGE_KEYS["transform"])
    return out


def _encode_payload(payload: Any, event_type: Any) -> Any:
    if not isinstance(payload, dict):
        return payload
    event_type_str = _unmap_enum(event_type, EVENT_TYPE_REV) if isinstance(event_type, int) else event_type
    if event_type_str == "STATE_EVENT":
        return _encode_state_payload(payload)
    if event_type_str == "COMMAND_EVENT":
        return _encode_command_payload(payload)
    if event_type_str == "SYSTEM_EVENT":
        return _encode_system_payload(payload)
    return payload


def _decode_payload(payload: Any, event_type: Any) -> Any:
    if not isinstance(payload, dict):
        return payload
    if event_type == "STATE_EVENT":
        return _decode_state_payload(payload)
    if event_type == "COMMAND_EVENT":
        return _decode_command_payload(payload)
    if event_type == "SYSTEM_EVENT":
        return _decode_system_payload(payload)
    _reject_unknown_integer_keys(payload, set(), "payload")
    return payload


def _encode_state_payload(payload: Dict[str, Any]) -> Dict[int, Any]:
    out: Dict[int, Any] = {}
    for key, idx in STATE_PAYLOAD_KEYS.items():
        if key not in payload:
            continue
        value = payload[key]
        if key == "geo" and isinstance(value, dict):
            out[idx] = _encode_geo(value)
        else:
            out[idx] = value
    for key, value in payload.items():
        if key not in STATE_PAYLOAD_KEYS:
            out[key] = value
    return out


def _decode_state_payload(payload: Dict[int, Any]) -> Dict[str, Any]:
    _reject_unknown_integer_keys(payload, set(STATE_PAYLOAD_KEYS.values()), "STATE_EVENT payload")
    out: Dict[str, Any] = {}
    for key, idx in STATE_PAYLOAD_KEYS.items():
        if idx not in payload:
            continue
        value = payload[idx]
        if key == "geo" and isinstance(value, dict):
            out[key] = _decode_geo(value)
        else:
            out[key] = value
    for key, value in payload.items():
        if key not in STATE_PAYLOAD_KEYS.values():
            out[str(key)] = value
    return out


def _encode_command_payload(payload: Dict[str, Any]) -> Dict[int, Any]:
    out: Dict[int, Any] = {}
    for key, idx in COMMAND_PAYLOAD_KEYS.items():
        if key not in payload:
            continue
        value = payload[key]
        if key == "task_type":
            out[idx] = _map_enum(value, TASK_TYPE_MAP)
        elif key == "priority":
            out[idx] = _map_enum(value, PRIORITY_MAP)
        elif key == "valid_from_ts":
            out[idx] = _parse_ts(value)
        elif key == "target_geo" and isinstance(value, dict):
            out[idx] = _encode_geo2d(value)
        else:
            out[idx] = value
    for key, value in payload.items():
        if key not in COMMAND_PAYLOAD_KEYS:
            out[key] = value
    return out


def _decode_command_payload(payload: Dict[int, Any]) -> Dict[str, Any]:
    _reject_unknown_integer_keys(payload, set(COMMAND_PAYLOAD_KEYS.values()), "COMMAND_EVENT payload")
    out: Dict[str, Any] = {}
    for key, idx in COMMAND_PAYLOAD_KEYS.items():
        if idx not in payload:
            continue
        value = payload[idx]
        if key == "task_type":
            out[key] = _unmap_enum(value, TASK_TYPE_REV)
        elif key == "priority":
            out[key] = _unmap_enum(value, PRIORITY_REV)
        elif key == "valid_from_ts":
            out[key] = _format_ts(value)
        elif key == "target_geo" and isinstance(value, dict):
            out[key] = _decode_geo2d(value)
        else:
            out[key] = value
    for key, value in payload.items():
        if key not in COMMAND_PAYLOAD_KEYS.values():
            out[str(key)] = value
    out.setdefault("requires_deconfliction", True)
    return out


def _encode_system_payload(payload: Dict[str, Any]) -> Dict[int, Any]:
    out: Dict[int, Any] = {}
    system_type = payload.get("system_type")
    if system_type is not None:
        out[SYSTEM_PAYLOAD_KEYS["system_type"]] = _map_enum(system_type, SYSTEM_TYPE_MAP)
    state = payload.get("state")
    if state is not None:
        out[SYSTEM_PAYLOAD_KEYS["state"]] = _encode_system_state(system_type, state)
    metrics = payload.get("metrics")
    if metrics is not None:
        out[SYSTEM_PAYLOAD_KEYS["metrics"]] = _encode_metrics(system_type, metrics)
    for key, value in payload.items():
        if key not in SYSTEM_PAYLOAD_KEYS:
            out[key] = value
    return out


def _decode_system_payload(payload: Dict[int, Any]) -> Dict[str, Any]:
    _reject_unknown_integer_keys(payload, set(SYSTEM_PAYLOAD_KEYS.values()), "SYSTEM_EVENT payload")
    out: Dict[str, Any] = {}
    system_type = None
    if SYSTEM_PAYLOAD_KEYS["system_type"] in payload:
        system_type = _unmap_enum(payload.get(SYSTEM_PAYLOAD_KEYS["system_type"]), SYSTEM_TYPE_REV)
        out["system_type"] = system_type
    if SYSTEM_PAYLOAD_KEYS["state"] in payload:
        out["state"] = _decode_system_state(system_type, payload.get(SYSTEM_PAYLOAD_KEYS["state"]))
    if SYSTEM_PAYLOAD_KEYS["metrics"] in payload:
        out["metrics"] = _decode_metrics(system_type, payload.get(SYSTEM_PAYLOAD_KEYS["metrics"]))
    for key, value in payload.items():
        if key not in SYSTEM_PAYLOAD_KEYS.values():
            out[str(key)] = value
    return out


def _encode_geo(geo: Dict[str, Any]) -> Dict[int, Any]:
    out: Dict[int, Any] = {}
    for key, idx in GEO_KEYS.items():
        if key in geo:
            out[idx] = geo[key]
    return out


def _decode_geo(geo: Dict[int, Any]) -> Dict[str, Any]:
    _reject_unknown_integer_keys(geo, set(GEO_KEYS.values()), "geo")
    out: Dict[str, Any] = {}
    for key, idx in GEO_KEYS.items():
        if idx in geo:
            out[key] = geo[idx]
    return out


def _encode_geo2d(geo: Dict[str, Any]) -> Dict[int, Any]:
    out: Dict[int, Any] = {}
    for key, idx in GEO2D_KEYS.items():
        if key in geo:
            out[idx] = geo[key]
    return out


def _decode_geo2d(geo: Dict[int, Any]) -> Dict[str, Any]:
    _reject_unknown_integer_keys(geo, set(GEO2D_KEYS.values()), "target_geo")
    out: Dict[str, Any] = {}
    for key, idx in GEO2D_KEYS.items():
        if idx in geo:
            out[key] = geo[idx]
    return out


def _encode_metrics(system_type: Any, metrics: Any) -> Any:
    if not isinstance(metrics, dict):
        return metrics
    system_type_str = (
        _unmap_enum(system_type, SYSTEM_TYPE_REV) if isinstance(system_type, int) else system_type
    )
    if system_type_str == "TASK_ACK":
        return _encode_metrics_with_keys(metrics, TASK_ACK_METRICS_KEYS, uuid_keys={"original_event_id"})
    if system_type_str == "LINK_STATUS":
        return _encode_metrics_with_keys(metrics, LINK_STATUS_METRICS_KEYS)
    if system_type_str == "TIME_STATUS":
        return _encode_time_status_metrics(metrics)
    if system_type_str == "SCHEMA_VIOLATION":
        return _encode_metrics_with_keys(
            metrics, SCHEMA_VIOLATION_METRICS_KEYS, uuid_keys={"original_event_id"}
        )
    return metrics


def _decode_metrics(system_type: Any, metrics: Any) -> Any:
    if not isinstance(metrics, dict):
        return metrics
    system_type_str = (
        _unmap_enum(system_type, SYSTEM_TYPE_REV) if isinstance(system_type, int) else system_type
    )
    if system_type_str == "TASK_ACK":
        return _decode_metrics_with_keys(metrics, TASK_ACK_METRICS_KEYS, uuid_keys={"original_event_id"})
    if system_type_str == "LINK_STATUS":
        return _decode_metrics_with_keys(metrics, LINK_STATUS_METRICS_KEYS)
    if system_type_str == "TIME_STATUS":
        return _decode_time_status_metrics(metrics)
    if system_type_str == "SCHEMA_VIOLATION":
        return _decode_metrics_with_keys(
            metrics, SCHEMA_VIOLATION_METRICS_KEYS, uuid_keys={"original_event_id"}
        )
    _reject_unknown_integer_keys(metrics, set(), "metrics")
    return metrics


def _encode_metrics_with_keys(
    metrics: Dict[str, Any],
    key_map: Dict[str, int],
    uuid_keys: set[str] | None = None,
) -> Dict[int, Any]:
    out: Dict[int, Any] = {}
    uuid_keys = uuid_keys or set()
    for key, value in metrics.items():
        if key in key_map:
            idx = key_map[key]
            if key in uuid_keys:
                out[idx] = _uuid_to_bytes(value)
            elif key == "reason_code":
                out[idx] = _map_enum(value, REASON_CODE_MAP)
            else:
                out[idx] = value
        else:
            out[key] = value
    return out


def _decode_metrics_with_keys(
    metrics: Dict[int, Any],
    key_map: Dict[str, int],
    uuid_keys: set[str] | None = None,
) -> Dict[str, Any]:
    _reject_unknown_integer_keys(metrics, set(key_map.values()), "metrics")
    out: Dict[str, Any] = {}
    uuid_keys = uuid_keys or set()
    reverse = _reverse_map(key_map)
    for key, value in metrics.items():
        if key in reverse:
            name = reverse[key]
            if name in uuid_keys:
                out[name] = _uuid_from_bytes(value)
            elif name == "reason_code":
                out[name] = _unmap_enum(value, REASON_CODE_REV)
            else:
                out[name] = value
        else:
            out[str(key)] = value
    return out


def _encode_time_status_metrics(metrics: Dict[str, Any]) -> Dict[int, Any]:
    out: Dict[int, Any] = {}
    for key, idx in TIME_STATUS_METRICS_KEYS.items():
        if key not in metrics:
            continue
        value = metrics[key]
        if key == "time_source":
            out[idx] = _map_enum(value, TIME_SOURCE_MAP)
        elif key == "sync_state":
            out[idx] = _map_enum(value, SYNC_STATE_MAP)
        elif key == "last_sync_ts":
            out[idx] = _parse_ts(value)
        else:
            out[idx] = value
    for key, value in metrics.items():
        if key not in TIME_STATUS_METRICS_KEYS:
            out[key] = value
    return out


def _decode_time_status_metrics(metrics: Dict[int, Any]) -> Dict[str, Any]:
    _reject_unknown_integer_keys(metrics, set(TIME_STATUS_METRICS_KEYS.values()), "TIME_STATUS metrics")
    out: Dict[str, Any] = {}
    for key, idx in TIME_STATUS_METRICS_KEYS.items():
        if idx not in metrics:
            continue
        value = metrics[idx]
        if key == "time_source":
            out[key] = _unmap_enum(value, TIME_SOURCE_REV)
        elif key == "sync_state":
            out[key] = _unmap_enum(value, SYNC_STATE_REV)
        elif key == "last_sync_ts":
            out[key] = _format_ts(value)
        else:
            out[key] = value
    for key, value in metrics.items():
        if key not in TIME_STATUS_METRICS_KEYS.values():
            out[str(key)] = value
    return out


def _encode_system_state(system_type: Any, state: Any) -> Any:
    system_type_str = (
        _unmap_enum(system_type, SYSTEM_TYPE_REV) if isinstance(system_type, int) else system_type
    )
    if system_type_str == "TASK_ACK":
        return _map_enum(state, TASK_ACK_STATE_MAP)
    if system_type_str == "LINK_STATUS":
        return _map_enum(state, LINK_STATUS_STATE_MAP)
    return state


def _decode_system_state(system_type: Any, state: Any) -> Any:
    if system_type == "TASK_ACK":
        return _unmap_enum(state, TASK_ACK_STATE_REV)
    if system_type == "LINK_STATUS":
        return _unmap_enum(state, LINK_STATUS_STATE_REV)
    return state


def _map_enum(value: Any, mapping: Dict[str, int]) -> Any:
    if isinstance(value, str) and value in mapping:
        return mapping[value]
    return value


def _unmap_enum(value: Any, mapping: Dict[int, str]) -> Any:
    if isinstance(value, int) and value in mapping:
        return mapping[value]
    return value


def _uuid_to_bytes(value: Any) -> Any:
    if isinstance(value, (bytes, bytearray)) and len(value) == 16:
        return bytes(value)
    if isinstance(value, str):
        try:
            return uuid.UUID(value).bytes
        except (ValueError, AttributeError):
            return value
    return value


def _uuid_from_bytes(value: Any) -> Any:
    if isinstance(value, (bytes, bytearray)) and len(value) == 16:
        try:
            return str(uuid.UUID(bytes=bytes(value)))
        except (ValueError, AttributeError):
            return value
    return value


# Exact epoch-ms conversion. datetime.timestamp() and fromtimestamp() route
# through float seconds, and most millisecond instants have no exact float
# representation - int(dt.timestamp() * 1000) lands one ms off for a
# date-banded fraction of schema-valid timestamps, so the round-trip check
# refused honest events (and on Windows, out-of-range instants raised OSError
# instead of refusing). timedelta arithmetic keeps the whole path in integers.
_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
_ONE_MS = timedelta(milliseconds=1)


def _parse_ts(value: Any) -> Any:
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        ts = value.strip()
        if ts.endswith("Z"):
            ts = ts[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(ts)
        except ValueError:
            return value
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return (dt - _EPOCH) // _ONE_MS
    return value


def _format_ts(value: Any) -> Any:
    if isinstance(value, (int, float)):
        # Reached from the PUBLIC decode path (loads/decode_event) on a
        # sender-controlled epoch-ms value, which is outside the encode-side
        # try/except. A wire value far enough out of range makes timedelta
        # raise, so refuse it here: decode fails closed like every other
        # invalid compact input, instead of crashing the consumer.
        try:
            dt = _EPOCH + timedelta(milliseconds=value)
        except (OverflowError, OSError, ValueError) as exc:
            raise CompactUnrepresentableError(
                f"compact epoch-ms value {value!r} is outside the representable "
                "date range; refusing to decode"
            ) from exc
        return dt.isoformat().replace("+00:00", "Z")
    return value
