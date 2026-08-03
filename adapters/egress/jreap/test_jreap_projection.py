from adapters.egress.jreap.zmeta_state_to_jreap_track_json import zmeta_state_to_jreap_track_json


def test_track_state_projection():
    event = {
        "event": {
            "event_type": "STATE_EVENT",
            "event_subtype": "TRACK_STATE",
            "ts": "2025-01-17T15:20:00Z",
        },
        "payload": {
            "track_id": "track-1",
            "geo": {"lat": 34.0, "lon": -118.0, "alt_m": 120.0},
            "valid_for_ms": 1000,
        },
    }

    result = zmeta_state_to_jreap_track_json(event)
    assert result["track_id"] == "track-1"
    assert result["stale_time"] == "2025-01-17T15:20:01Z"


def test_non_state_event_returns_none():
    event = {"event": {"event_type": "OBSERVATION_EVENT"}, "payload": {}}
    assert zmeta_state_to_jreap_track_json(event) is None


# R1-11 A-01: a non-finite number must refuse, not project. Value scoped -
# every number that reaches the projected track, not a list of the ones
# someone remembered.
NON_FINITE = (float("nan"), float("inf"), float("-inf"))


def _track_state_event():
    return {
        "event": {
            "event_type": "STATE_EVENT",
            "event_subtype": "TRACK_STATE",
            "ts": "2025-01-17T15:20:00Z",
        },
        "payload": {
            "track_id": "track-1",
            "geo": {"lat": 34.0, "lon": -118.0, "alt_m": 120.0},
            "valid_for_ms": 1000,
        },
        "confidence": 0.9,
    }


def test_non_finite_track_values_refuse():
    import copy
    import json

    for path in (
        ("payload", "geo", "lat"),
        ("payload", "geo", "lon"),
        ("payload", "geo", "alt_m"),
        ("confidence",),
    ):
        for value in NON_FINITE:
            event = _track_state_event()
            node = event
            for part in path[:-1]:
                node = node[part]
            node[path[-1]] = value
            assert zmeta_state_to_jreap_track_json(event) is None, (path, value)

    # The clean case still projects, and what it projects is RFC 8259.
    result = zmeta_state_to_jreap_track_json(_track_state_event())
    assert result is not None
    json.dumps(result, allow_nan=False)


# R1-11, third pass (R2-05 / R2-07). The guard above was written value scoped
# but with a dict/list-only walk and no seen-set, and the stale arithmetic
# above it ran BEFORE the guard - so shapes that reach this adapter on a
# cbor2-only install crashed it or escaped it entirely.


class _CborTag:
    """Stand-in for cbor2.CBORTag: an unrecognised tag decodes to an object
    whose `.value` still reaches the consumer."""

    def __init__(self, tag, value):
        self.tag = tag
        self.value = value


def test_non_finite_walk_terminates_on_a_cyclic_track():
    # CBOR value-sharing tags (28/29) make a decoded event possibly cyclic.
    # Without a seen-set this walk never returns and the egress path hangs -
    # the failure mode the iterative rewrite was supposed to have removed.
    from adapters.egress.jreap.zmeta_state_to_jreap_track_json import _has_non_finite

    loop = {"lat": 34.0}
    loop["self"] = loop
    assert _has_non_finite(loop) is False
    poisoned = {"lat": 34.0, "cep": float("nan")}
    poisoned["self"] = poisoned
    assert _has_non_finite(poisoned) is True


def test_non_finite_walk_sees_every_decoded_container():
    # cbor2 decodes tag 258 to a set, a map used as a map key to a Mapping
    # that is not a dict, tag 4/5 to a Decimal, and an unknown tag to a
    # wrapper object. A dict/list-only walk sees none of them.
    from collections import OrderedDict
    from decimal import Decimal

    from adapters.egress.jreap.zmeta_state_to_jreap_track_json import _has_non_finite

    for blob in (
        {float("nan")},
        frozenset({float("inf")}),
        (1.0, float("-inf")),
        _CborTag(4242, [float("nan")]),
        OrderedDict({"cep": float("nan")}),
        Decimal("NaN"),
        {"nested": [{"deep": (Decimal("Infinity"),)}]},
    ):
        assert _has_non_finite({"payload": blob}) is True, blob
    # A non-finite used as a MAP KEY is still on the wire.
    assert _has_non_finite({float("nan"): "x"}) is True
    # False-positive control: text must be a leaf, not a walk over its own
    # characters (a one-character string yields itself forever).
    assert _has_non_finite({"a": "x", "b": ["y"], "c": 1.0, "d": b"z"}) is False


def test_unrepresentable_stale_refuses_instead_of_raising():
    # Same class as the CoT sibling (R2-05): payload.valid_for_ms is
    # {"type": "integer", "minimum": 1} with no upper bound, so all three of
    # these clear the gateway's outgoing gate and then hit the timedelta.
    for ts, valid_for_ms in (
        ("2025-01-17T15:20:00Z", 10 ** 400),
        ("2025-01-17T15:20:00Z", 10 ** 15),
        ("9999-12-31T23:59:59Z", 300000),
    ):
        event = _track_state_event()
        event["event"]["ts"] = ts
        event["payload"]["valid_for_ms"] = valid_for_ms
        assert zmeta_state_to_jreap_track_json(event) is None, (ts, valid_for_ms)


def test_non_finite_valid_for_ms_refuses_rather_than_crashing_the_coercion():
    # int(float("nan")) raises ValueError and int(float("inf")) raises
    # OverflowError. The coercion ran upstream of the non-finite guard, so
    # the guard written to refuse these never saw them.
    for value in NON_FINITE:
        event = _track_state_event()
        event["payload"]["valid_for_ms"] = value
        assert zmeta_state_to_jreap_track_json(event) is None, value


def test_unparseable_ts_refuses_instead_of_raising():
    # Banked R1-11 MAJOR (fix-pass carry-forward): the schema's utcDateTime
    # enforces only `"pattern": "Z$"` — `format: date-time` is advisory
    # because no RFC 3339 format checker is installed — so a Z-suffixed but
    # unparseable ts is gate-clean, and _parse_utc raised ValueError out of
    # the public entry point on it. The documented disposition for a field
    # this projection cannot honestly use is the None refusal, never a raise
    # and never a substituted timestamp.
    for ts in (
        "2026-02-30T00:00:00Z",  # calendar-invalid: February 30th
        "2026-07-27T25:61:61Z",  # clock-invalid: hour 25
        "not-a-dateZ",  # junk wearing the trailing Z the pattern wants
    ):
        event = _track_state_event()
        event["event"]["ts"] = ts
        assert zmeta_state_to_jreap_track_json(event) is None, ts
    # Attribution control: the identical event with a parseable ts still
    # projects, so the refusals above are the ts and nothing else.
    result = zmeta_state_to_jreap_track_json(_track_state_event())
    assert result["timestamp"] == "2025-01-17T15:20:00Z"


def test_embedder_reachable_ts_shapes_refuse_not_raise():
    # Not gate-clean (the Z$ pattern blocks both), but this adapter has no
    # non-test caller — embedders hand it events directly, and the None
    # contract is what the README tells them to handle. A naive pre-epoch
    # instant raises OSError(EINVAL) out of .astimezone() on Windows (the
    # arm the SAPIENT twins already carry), and a non-string ts raised
    # AttributeError off .endswith.
    for ts in ("1969-12-31T23:59:59", 12345):
        event = _track_state_event()
        event["event"]["ts"] = ts
        assert zmeta_state_to_jreap_track_json(event) is None, repr(ts)


def test_large_but_representable_stale_still_projects():
    # Proportionality: refuse the window datetime cannot express, not every
    # window that looks big.
    event = _track_state_event()
    event["payload"]["valid_for_ms"] = 31536000000000
    result = zmeta_state_to_jreap_track_json(event)
    assert result is not None
    assert result["stale_time"].startswith("3024-")


def test_gate_clean_naive_shapes_refuse_not_localize():
    # Attack-pass completion (2026-07-27): "1969-12-31Z" / "2026-W01-1Z"
    # pass the schema's Z$ pattern yet parse NAIVE; pre-fix they reached
    # the platform delegate (OSError pre-epoch on Windows) or were
    # silently reinterpreted as host-local time - a fabricated instant on
    # the wire. Refusal is None, per the documented contract.
    for ts in ("1969-12-31Z", "2026-W01-1Z"):
        event = _track_state_event()
        event["event"]["ts"] = ts
        assert zmeta_state_to_jreap_track_json(event) is None


# --- A1-02 declared 2-D geo sweep -------------------------------------------
# The first independent SAPIENT interop run's finding
# (adapters/egress/sapient) prompted a sweep of the sibling egress adapters
# for the same all-or-nothing altitude assumption against a 2-D STATE. This
# adapter never had one: it reads `geo.get("alt_m")` directly, so a
# genuinely 2-D declared position (doctrine A1-02, `dimensionality: "2D"`,
# no `alt_m`) already projected `hae_m: null`, never a fabricated altitude
# and never a silent drop. What it did not do is tell that case apart from
# the schema-invalid shape a real gateway would already have rejected -
# geo missing `alt_m` with no explicit "2D" token - so both produced the
# identical `hae_m: null` track. The fix below closes that: only an
# explicit "2D" token earns the no-altitude disposition.


def test_declared_2d_geo_projects_with_null_altitude_not_fabricated():
    event = _track_state_event()
    event["payload"]["geo"] = {"lat": 34.0, "lon": -118.0, "dimensionality": "2D"}
    result = zmeta_state_to_jreap_track_json(event)

    assert result is not None
    assert result["lat"] == 34.0
    assert result["lon"] == -118.0
    assert result["hae_m"] is None


def test_2d_geo_carrying_an_altitude_is_a_contradiction_and_refuses():
    # A "2D" token paired with a present alt_m is schema-incoherent upstream
    # (schema/zmeta-event-1.1.0.schema.json coherence arm 1): the geo makes
    # two claims that cannot both be true.
    event = _track_state_event()
    event["payload"]["geo"] = {
        "lat": 34.0, "lon": -118.0, "alt_m": 120.0, "dimensionality": "2D",
    }
    assert zmeta_state_to_jreap_track_json(event) is None


def test_ambiguous_missing_altitude_without_2d_token_refuses():
    # Schema-invalid upstream (absent dimensionality means 3D, and 3D
    # requires alt_m), so a real gateway never hands this shape to egress -
    # but a direct embedder call can, and before this fix the adapter could
    # not tell it apart from a genuine 2-D declaration: both produced
    # `hae_m: null`.
    event = _track_state_event()
    event["payload"]["geo"] = {"lat": 34.0, "lon": -118.0}
    assert zmeta_state_to_jreap_track_json(event) is None
