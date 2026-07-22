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


def test_large_but_representable_stale_still_projects():
    # Proportionality: refuse the window datetime cannot express, not every
    # window that looks big.
    event = _track_state_event()
    event["payload"]["valid_for_ms"] = 31536000000000
    result = zmeta_state_to_jreap_track_json(event)
    assert result is not None
    assert result["stale_time"].startswith("3024-")
