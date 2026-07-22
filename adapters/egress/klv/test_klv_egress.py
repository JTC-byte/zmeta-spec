from adapters.egress.klv.zmeta_to_klv_tagdict_template import zmeta_observation_to_klv_tagdict


def test_observation_to_klv_tagdict():
    event = {
        "zmeta_version": "1.0",
        "event": {
            "event_id": "019c2b5d-0ba0-7536-ad67-ba859248dc5c",
            "event_type": "OBSERVATION_EVENT",
            "event_subtype": "RF",
            "ts": "2025-01-17T15:20:00Z",
        },
        "source": {
            "platform_id": "platform-1",
            "node_role": "EDGE",
            "producer": "rf-sensor",
            "sensor_id": "sensor-1",
        },
        "payload": {
            "modality": "RF",
            "features": {
                "center_freq_hz": 2450000000,
                "bandwidth_hz": 20000000,
                "power_dbm": -35.2,
            },
            "geo": {"lat": 34.0, "lon": -118.0, "alt_m": 120.0},
        },
    }

    tagdict = zmeta_observation_to_klv_tagdict(event)
    assert tagdict["timestamp"] == "2025-01-17T15:20:00Z"
    assert tagdict["platform_id"] == "platform-1"
    assert tagdict["features"]["center_freq_hz"] == 2450000000


def test_non_observation_returns_none():
    event = {"event": {"event_type": "STATE_EVENT"}}
    assert zmeta_observation_to_klv_tagdict(event) is None


# R1-11 A-01: geo and features are copied wholesale from the payload, so a
# non-finite value anywhere inside them reaches the tag dict. Refuse instead.
NON_FINITE = (float("nan"), float("inf"), float("-inf"))


def _observation_event():
    return {
        "zmeta_version": "1.0",
        "event": {
            "event_id": "019c2b5d-0ba0-7536-ad67-ba859248dc5c",
            "event_type": "OBSERVATION_EVENT",
            "event_subtype": "RF",
            "ts": "2025-01-17T15:20:00Z",
        },
        "source": {
            "platform_id": "platform-1",
            "node_role": "EDGE",
            "producer": "rf-sensor",
            "sensor_id": "sensor-1",
        },
        "payload": {
            "modality": "RF",
            "features": {"center_freq_hz": 2450000000.0, "bandwidth_hz": 20000000.0},
            "geo": {"lat": 34.0, "lon": -118.0, "alt_m": 120.0},
        },
    }


def test_non_finite_tag_values_refuse():
    import json

    for path in (
        ("payload", "geo", "lat"),
        ("payload", "geo", "lon"),
        ("payload", "geo", "alt_m"),
        ("payload", "features", "center_freq_hz"),
        ("payload", "features", "bandwidth_hz"),
    ):
        for value in NON_FINITE:
            event = _observation_event()
            node = event
            for part in path[:-1]:
                node = node[part]
            node[path[-1]] = value
            assert zmeta_observation_to_klv_tagdict(event) is None, (path, value)

    result = zmeta_observation_to_klv_tagdict(_observation_event())
    assert result is not None
    json.dumps(result, allow_nan=False)


# R1-11, third pass (R2-07). The guard above walked dict/list only and had no
# seen-set: payload.features is copied wholesale into the tag dict, so the
# shapes reaching it are whatever the decoder produced.


class _CborTag:
    """Stand-in for cbor2.CBORTag: an unrecognised tag decodes to an object
    whose `.value` still reaches the consumer."""

    def __init__(self, tag, value):
        self.tag = tag
        self.value = value


def test_non_finite_walk_terminates_on_a_cyclic_feature_block():
    from adapters.egress.klv.zmeta_to_klv_tagdict_template import _has_non_finite

    loop = {"power_dbm": -35.2}
    loop["self"] = loop
    assert _has_non_finite(loop) is False
    poisoned = {"power_dbm": float("nan")}
    poisoned["self"] = poisoned
    assert _has_non_finite(poisoned) is True


def test_non_finite_walk_sees_every_decoded_container():
    from collections import OrderedDict
    from decimal import Decimal

    from adapters.egress.klv.zmeta_to_klv_tagdict_template import _has_non_finite

    for blob in (
        {float("nan")},
        frozenset({float("inf")}),
        (1.0, float("-inf")),
        _CborTag(4242, [float("nan")]),
        OrderedDict({"power_dbm": float("nan")}),
        Decimal("NaN"),
        {"nested": [{"deep": (Decimal("Infinity"),)}]},
    ):
        assert _has_non_finite({"features": blob}) is True, blob
    assert _has_non_finite({float("nan"): "x"}) is True
    assert _has_non_finite({"a": "x", "b": ["y"], "c": 1.0, "d": b"z"}) is False


def test_non_finite_inside_a_decoded_feature_container_refuses_the_tagdict():
    # At the projection boundary, not just the unit: features is copied
    # verbatim, so a set-carried NaN became a KLV tag value.
    from decimal import Decimal

    for blob in ({1.0, float("nan")}, (float("inf"),), Decimal("NaN")):
        event = _observation_event()
        event["payload"]["features"]["samples"] = blob
        assert zmeta_observation_to_klv_tagdict(event) is None, blob


def test_clean_tagdict_with_exotic_but_finite_containers_still_projects():
    from decimal import Decimal

    event = _observation_event()
    event["payload"]["features"]["samples"] = (1.0, 2.0)
    event["payload"]["features"]["cep_m"] = Decimal("12.5")
    assert zmeta_observation_to_klv_tagdict(event) is not None
