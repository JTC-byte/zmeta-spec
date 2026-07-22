"""Pins the value-scoped non-finite refusal (R1-11 A-01).

The guard this pins replaced a FIELD-scoped one whose candidate list was
exactly [confidence, payload.claim.confidence]. The defect was not that a
particular field was missing from the list; it was that there was a list.
So these tests are written to fail against any re-introduced allowlist:
they walk a family of canonical numeric locations plus an arbitrary
namespaced extension key, and they assert wire honesty with the standard
library (`json.dumps(..., allow_nan=False)`) rather than with any repo
encoder - `zmeta_compact.dumps` refuses non-finite input on its own, so a
round-trip through it can never observe this defect (that blindness is
A-19 in the same audit).
"""

import copy
import importlib.util
import json
import math
import unittest
from collections.abc import Mapping
from decimal import Decimal
from pathlib import Path

try:
    import cbor2
except ImportError:  # pragma: no cover - optional dependency
    cbor2 = None


ROOT = Path(__file__).resolve().parents[2]

_spec = importlib.util.spec_from_file_location(
    "zmeta_validators_nf", ROOT / "gateway" / "src" / "validators.py"
)
validators = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(validators)

_spec_gw = importlib.util.spec_from_file_location(
    "zmeta_gateway_nf", ROOT / "gateway" / "src" / "gateway.py"
)
gateway = importlib.util.module_from_spec(_spec_gw)
_spec_gw.loader.exec_module(gateway)


NON_FINITE = (float("nan"), float("inf"), float("-inf"))


def _state_event():
    return {
        "zmeta_version": "1.0",
        "event": {
            "event_id": "019c2b5c-c047-73ea-8f1a-302b9d9c0aa4",
            "event_type": "STATE_EVENT",
            "event_subtype": "TRACK_STATE",
            "ts": "2025-01-17T14:40:00Z",
        },
        "source": {
            "platform_id": "lora-node-01",
            "node_role": "GATEWAY",
            "producer": "sensorops",
        },
        "profile": "L",
        "payload": {
            "track_id": "track-l-001",
            "geo": {"lat": 34.0001, "lon": -118.0001, "alt_m": 100.0},
            "valid_for_ms": 1000,
            "heading_deg": 90.0,
            "speed_mps": 12.0,
            "quality": {"pos_sigma_m": 5.0},
            "extensions": {"acme.telemetry": {"battery_v": 12.6}},
        },
        "confidence": 0.62,
        "lineage": {"based_on": ["019c2b5c-c047-73ea-8f1a-302e4b7b0aa4"]},
    }


# Canonical numeric locations a non-finite value can occupy on a TRACK_STATE.
# Deliberately includes a vendor extension: the kernel does not interpret
# namespaced extension content, but it still puts it on the wire, so the
# refusal must not stop at fields the kernel knows the meaning of.
NUMERIC_PATHS = [
    ["payload", "geo", "lat"],
    ["payload", "geo", "lon"],
    ["payload", "geo", "alt_m"],
    ["payload", "valid_for_ms"],
    ["payload", "heading_deg"],
    ["payload", "speed_mps"],
    ["payload", "quality", "pos_sigma_m"],
    ["payload", "extensions", "acme.telemetry", "battery_v"],
]


def _put(event, path, value):
    node = event
    for part in path[:-1]:
        node = node[part]
    node[path[-1]] = value
    return event


class ValueScopedNonFiniteTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.validator = validators.load_schema(
            ROOT / "schema" / "zmeta-event-1.0.schema.json"
        )
        cls.policy = validators.load_policy(ROOT / "policy")
        cls.severity_map = cls.policy["violation_severities"]

    def _semantics(self, event):
        return validators.validate_semantics(
            event, self.policy["semantics"], self.severity_map
        )

    def test_baseline_event_passes(self):
        # The family below only means something if the untouched event is clean.
        ok, violations = self._semantics(_state_event())
        self.assertTrue(ok, violations)

    def test_every_numeric_location_refuses(self):
        for path in NUMERIC_PATHS:
            for value in NON_FINITE:
                with self.subTest(path=".".join(path), value=repr(value)):
                    event = _put(_state_event(), path, value)
                    ok, violations = self._semantics(event)
                    self.assertFalse(ok)
                    self.assertEqual("SCHEMA_INVALID", violations[0]["code"])
                    self.assertEqual("fail", violations[0]["severity"])
                    # The refusal must name the offending location, not the
                    # offending value: details flow verbatim into the
                    # diagnostic's payload.metrics, so echoing the value there
                    # would put the NaN back on the wire inside the refusal.
                    self.assertEqual(
                        ".".join(path), violations[0]["details"]["field"]
                    )
                    self.assertNotIn("value", violations[0]["details"])

    def test_confidence_keeps_its_own_diagnostic(self):
        # The two confidence sites must keep firing NON_FINITE_CONFIDENCE
        # exactly as before; the generic code would be a less honest report
        # for a field the vocabulary already names.
        for value in NON_FINITE:
            with self.subTest(field="confidence", value=repr(value)):
                event = _put(_state_event(), ["confidence"], value)
                ok, violations = self._semantics(event)
                self.assertFalse(ok)
                self.assertEqual("NON_FINITE_CONFIDENCE", violations[0]["code"])
                self.assertEqual("confidence", violations[0]["details"]["field"])

        for value in NON_FINITE:
            with self.subTest(field="payload.claim.confidence", value=repr(value)):
                event = _state_event()
                event["payload"]["claim"] = {"type": "UAV", "confidence": value}
                ok, violations = self._semantics(event)
                self.assertFalse(ok)
                self.assertEqual("NON_FINITE_CONFIDENCE", violations[0]["code"])
                self.assertEqual(
                    "payload.claim.confidence", violations[0]["details"]["field"]
                )

    def test_non_finite_dict_key_refuses(self):
        # Reachable only from a CBOR producer (JSON keys are strings), and
        # json.dumps would launder a NaN key into the string "NaN".
        event = _state_event()
        event["payload"]["extensions"] = {float("nan"): 1}
        ok, violations = self._semantics(event)
        self.assertFalse(ok)
        self.assertEqual("SCHEMA_INVALID", violations[0]["code"])
        self.assertTrue(violations[0]["details"]["field"].endswith("<key>"))

    def test_non_finite_inside_a_list_refuses(self):
        event = _state_event()
        event["payload"]["extensions"]["acme.telemetry"]["samples"] = [
            1.0,
            2.0,
            float("inf"),
        ]
        ok, violations = self._semantics(event)
        self.assertFalse(ok)
        self.assertEqual("SCHEMA_INVALID", violations[0]["code"])

    def test_deep_nesting_does_not_recurse(self):
        # A sender-controlled nesting depth must be a memory cost, never a
        # RecursionError that takes the gateway down before any egress guard
        # runs (the reason _find_forbidden_key is iterative too).
        event = _state_event()
        node = event["payload"]["extensions"]["acme.telemetry"]
        for _ in range(50000):
            node["n"] = {}
            node = node["n"]
        node["bad"] = float("nan")
        ok, violations = self._semantics(event)
        self.assertFalse(ok)
        self.assertEqual("SCHEMA_INVALID", violations[0]["code"])
        # The reported path is sender-controlled and ships inside the
        # diagnostic; it must be bounded and the truncation must be visible.
        field = violations[0]["details"]["field"]
        self.assertLess(len(field), 512)
        self.assertTrue(field.endswith("...<truncated>"))


class NonFiniteEndToEndTest(unittest.TestCase):
    """The gateway must refuse, and its own refusal must be RFC 8259."""

    @classmethod
    def setUpClass(cls):
        cls.validator = validators.load_schema(
            ROOT / "schema" / "zmeta-event-1.0.schema.json"
        )
        cls.policy = validators.load_policy(ROOT / "policy")

    def _process(self, event, input_encoding="json"):
        if input_encoding == "json":
            raw = json.dumps(event).encode("utf-8")
        else:
            raw = gateway._encode_message(event, input_encoding)
        return gateway.process_message(
            raw,
            self.validator,
            self.policy,
            "L",
            {},
            input_encoding,
            strict_validation=True,
        )

    def _assert_refused_and_clean(self, out):
        self.assertEqual(1, len(out))
        diagnostic = out[0]
        self.assertEqual("SYSTEM_EVENT", diagnostic["event"]["event_type"])
        self.assertEqual("SCHEMA_VIOLATION", diagnostic["event"]["event_subtype"])
        self.assertEqual("REJECTED", diagnostic["payload"]["state"])
        # Independent of every repo encoder: the standard library decides
        # whether what we are about to emit is RFC 8259.
        json.dumps(diagnostic, allow_nan=False)
        # And every wire form the gateway can be configured to emit. Encoding
        # alone would prove little here - cbor and proto happily carry a
        # non-finite double, so a bare _encode_message call cannot see this
        # defect - so each binary form is decoded back and handed to the
        # standard library for the verdict. compact refuses non-finite input
        # itself, which is why it must not be the only thing asked.
        for encoding in ("json", "cbor", "compact", "proto"):
            with self.subTest(encoding=encoding):
                encoded = gateway._encode_message(diagnostic, encoding)
                json.dumps(
                    gateway._decode_message(encoded, encoding), allow_nan=False
                )
        return diagnostic

    def test_nan_position_is_refused_not_forwarded(self):
        event = _put(_state_event(), ["payload", "geo", "lat"], float("nan"))
        event = _put(event, ["payload", "geo", "alt_m"], float("inf"))
        diagnostic = self._assert_refused_and_clean(self._process(event))
        self.assertEqual(
            "SCHEMA_INVALID", diagnostic["payload"]["metrics"]["reason_code"]
        )

    def test_json_wire_never_carries_the_nan_token(self):
        event = _put(_state_event(), ["payload", "geo", "lat"], float("nan"))
        out = self._process(event)
        wire = gateway._encode_message(out[0], "json")
        self.assertNotIn(b"NaN", wire)
        self.assertNotIn(b"Infinity", wire)

    def test_refused_on_every_ingress_encoding(self):
        # Whether a non-finite value is refused must be decided by the
        # semantics, not by which encoding the operator configured. compact
        # refuses on the producer side, so it cannot carry one at all.
        for encoding in ("json", "cbor", "proto"):
            with self.subTest(encoding=encoding):
                event = _put(_state_event(), ["payload", "geo", "lat"], float("nan"))
                self._assert_refused_and_clean(self._process(event, encoding))

    def test_diagnostic_never_echoes_the_offending_value(self):
        # Several semantic checks copy the offending value verbatim into
        # violation details, which build_violation_event merges into
        # payload.metrics. A non-finite value must be refused before any of
        # them run, or the gateway's own refusal ships the NaN.
        for field in ("bearing_frame", "heading_source"):
            for value in NON_FINITE:
                with self.subTest(field=field, value=repr(value)):
                    event = _state_event()
                    event["payload"]["quality"] = {field: value}
                    self._assert_refused_and_clean(self._process(event))

    def test_severity_downgrade_cannot_reopen_the_hole(self):
        # Found by attacking the guard rather than the defect: the refusal
        # originally resolved its severity from the operator's severity map,
        # so `SCHEMA_INVALID: warn` plus strict_validation=False forwarded the
        # event verbatim with a warning beside it - `"lat":NaN` back on the
        # wire, laundering by configuration. NON_FINITE_CONFIDENCE had the
        # identical exposure. Both severities are now pinned.
        policy = copy.deepcopy(self.policy)
        policy["violation_severities"] = dict(policy["violation_severities"])
        for code in ("SCHEMA_INVALID", "NON_FINITE_CONFIDENCE"):
            policy["violation_severities"][code] = "warn"

        for path, value in (
            (["payload", "geo", "lat"], float("nan")),
            (["confidence"], float("nan")),
        ):
            with self.subTest(path=".".join(path)):
                event = _put(_state_event(), path, value)
                out = gateway.process_message(
                    json.dumps(event).encode("utf-8"),
                    self.validator,
                    policy,
                    "L",
                    {},
                    "json",
                    strict_validation=False,
                )
                # An empty list would satisfy the loop below without asserting
                # anything - the vacuous-oracle shape.
                self.assertGreaterEqual(len(out), 1)
                for emitted in out:
                    self.assertEqual(
                        "SYSTEM_EVENT", emitted["event"]["event_type"]
                    )
                    json.dumps(emitted, allow_nan=False)

    def test_outgoing_gate_refuses_too(self):
        # The egress gate is the last thing between a translated event and
        # the wire; it must apply the same value-scoped refusal.
        event = _put(_state_event(), ["payload", "geo", "lat"], float("nan"))
        violations = gateway.validate_outgoing_event(
            event, self.validator, self.policy, "L"
        )
        self.assertTrue(violations)
        self.assertEqual("SCHEMA_INVALID", violations[0]["code"])


class NonFiniteHelperTest(unittest.TestCase):
    """Direct tests of the traversal, independent of any event shape."""

    def test_finds_shallowest_and_reports_a_usable_path(self):
        self.assertIsNone(validators._find_non_finite({"a": [1, 2, {"b": "c"}]}))
        self.assertEqual("a.b.2", validators._find_non_finite({"a": {"b": [1, 2, float("nan")]}}))
        self.assertEqual("l.0.x", validators._find_non_finite({"l": [{"x": float("-inf")}]}))
        self.assertEqual("<root>", validators._find_non_finite(float("inf")))
        self.assertEqual("a.<key>", validators._find_non_finite({"a": {float("nan"): 1}}))

    def test_finite_edge_values_pass(self):
        # The guard refuses non-finite values, not extreme ones. Refusing a
        # legitimate float64 would be its own honesty failure.
        for value in (0.0, -0.0, 1e308, -1e308, 5e-324, math.pi):
            with self.subTest(value=repr(value)):
                self.assertIsNone(validators._find_non_finite({"v": value}))

    def test_bools_and_ints_are_not_mistaken_for_floats(self):
        self.assertIsNone(validators._find_non_finite({"a": True, "b": 0, "c": -1}))

    def test_huge_int_is_finite_and_does_not_raise(self):
        # math.isfinite() on an int outside float64 range raises
        # OverflowError. Converting here would trade the laundering defect for
        # a crash on a legal JSON integer literal.
        self.assertIsNone(validators._find_non_finite({"v": 10 ** 400}))
        self.assertIsNone(validators._find_non_finite({"v": -(10 ** 400)}))
        self.assertFalse(validators._is_non_finite_number(10 ** 400))


class NonFiniteContainerCoverageTest(unittest.TestCase):
    """The walk must see every container the supported decoders can produce.

    Dispatching on `dict` / `(list, tuple)` and on a `float` leaf let four
    separate cbor2-decoded shapes through, each of which was FORWARDED with
    strict_validation=True and each of which put the NaN back on the CBOR
    wire. cbor2 is the fallback backend `gateway._decode_cbor` explicitly
    supports when zmeta_cbor is absent, so this is a supported configuration,
    not an exotic one.

    These are written against abstract container behaviour rather than
    against cbor2's concrete classes wherever possible, so a different CBOR
    library with the same Mapping/Set/tag shapes is covered too.
    """

    def test_sets_are_traversed(self):
        self.assertEqual("a.<set>", validators._find_non_finite({"a": {1.0, float("nan")}}))
        self.assertEqual(
            "a.<set>", validators._find_non_finite({"a": frozenset({float("inf")})})
        )
        self.assertIsNone(validators._find_non_finite({"a": {1.0, 2.0}}))

    def test_non_dict_mappings_are_traversed(self):
        # A Mapping that is not a dict: cbor2 hands one back for a CBOR map
        # used as a map key, and `isinstance(x, dict)` is False for it.
        class _FrozenMapping(Mapping):
            def __init__(self, data):
                self._data = dict(data)

            def __getitem__(self, key):
                return self._data[key]

            def __iter__(self):
                return iter(self._data)

            def __len__(self):
                return len(self._data)

            def __hash__(self):
                return 0

        self.assertEqual(
            "a.x", validators._find_non_finite({"a": _FrozenMapping({"x": float("nan")})})
        )
        # ... and as a map KEY, which is where cbor2 actually produces it.
        self.assertEqual(
            "a.<key>.x",
            validators._find_non_finite({"a": {_FrozenMapping({"x": float("nan")}): 1}}),
        )

    def test_tag_wrappers_are_traversed(self):
        # An unrecognised CBOR tag decodes to a wrapper object whose .value
        # holds fully decoded content that still reaches the wire.
        class _Tag:
            def __init__(self, tag, value):
                self.tag = tag
                self.value = value

        self.assertEqual(
            "a.<tag>.1", validators._find_non_finite({"a": _Tag(4242, [1.0, float("nan")])})
        )

    def test_decimal_nan_is_a_non_finite_leaf(self):
        # cbor2 decodes CBOR tag 5 (bigfloat) with a NaN mantissa into
        # Decimal('NaN'); isinstance(Decimal('NaN'), float) is False.
        self.assertEqual("a", validators._find_non_finite({"a": Decimal("NaN")}))
        self.assertEqual("a", validators._find_non_finite({"a": Decimal("Infinity")}))
        self.assertIsNone(validators._find_non_finite({"a": Decimal("1.5")}))

    def test_forbidden_key_walk_sees_the_same_containers(self):
        # The denylist walk shares the dispatch, so it cannot drift: a
        # hashable mapping can sit inside a set or serve as a map key and
        # carry a forbidden key with it.
        class _FrozenMapping(Mapping):
            def __init__(self, data):
                self._data = dict(data)

            def __getitem__(self, key):
                return self._data[key]

            def __iter__(self):
                return iter(self._data)

            def __len__(self):
                return len(self._data)

            def __hash__(self):
                return 0

        forbidden = {"raw_features"}
        self.assertIsNotNone(
            validators._find_forbidden_key(
                {"a": {_FrozenMapping({"raw_features": 1})}}, forbidden
            )
        )
        self.assertIsNotNone(
            validators._find_forbidden_key(
                {"a": {_FrozenMapping({"raw_features": 1}): 1}}, forbidden
            )
        )
        # A list INDEX is not a key: "0" must not be treated as one.
        self.assertIsNone(validators._find_forbidden_key({"a": [1, 2]}, {"0", "1"}))

    def test_container_walks_still_terminate_on_a_cycle(self):
        # Widening the dispatch must not reopen the remote-hang defect the
        # seen-set closed. A self-referential list and a self-referential dict
        # both have to return.
        loop = {}
        loop["self"] = loop
        self.assertIsNone(validators._find_non_finite(loop))
        self.assertIsNone(validators._find_forbidden_key(loop, {"nope"}))
        ring = []
        ring.append(ring)
        self.assertIsNone(validators._find_non_finite({"a": ring}))


@unittest.skipIf(cbor2 is None, "cbor2 not installed")
class NonFiniteCborBackendTest(unittest.TestCase):
    """End to end on the cbor2 backend, from wire bytes to wire bytes.

    The direct traversal tests above use stand-in classes so they do not
    depend on one library's internals; this one uses the real decoder so the
    stand-ins cannot be wrong about what the decoder actually produces.
    """

    @classmethod
    def setUpClass(cls):
        cls.validator = validators.load_schema(
            ROOT / "schema" / "zmeta-event-1.0.schema.json"
        )
        cls.policy = validators.load_policy(ROOT / "policy")

    def _process_cbor2(self, event):
        original = gateway.zmeta_cbor
        gateway.zmeta_cbor = None  # the supported cbor2-only configuration
        try:
            return gateway.process_message(
                cbor2.dumps(event),
                self.validator,
                self.policy,
                "L",
                {},
                "cbor",
                strict_validation=True,
            )
        finally:
            gateway.zmeta_cbor = original

    def test_every_cbor_container_shape_is_refused(self):
        nan = float("nan")
        shapes = {
            "tag258_set": cbor2.CBORTag(258, [1.0, nan]),
            "unknown_tag": cbor2.CBORTag(4242, [1.0, nan]),
            "map_key_map": {cbor2.frozendict({"x": nan}): 1},
            "tag5_decimal_nan": cbor2.CBORTag(5, [-1, nan]),
        }
        for label, blob in shapes.items():
            with self.subTest(shape=label):
                event = _state_event()
                event["payload"]["extensions"]["acme.telemetry"]["samples"] = blob
                out = self._process_cbor2(event)
                self.assertEqual(1, len(out))
                self.assertEqual("SYSTEM_EVENT", out[0]["event"]["event_type"])
                self.assertEqual(
                    "SCHEMA_INVALID", out[0]["payload"]["metrics"]["reason_code"]
                )
                # The refusal has to name where it was, or it is not usable.
                self.assertIn("samples", out[0]["payload"]["metrics"]["field"])
                json.dumps(out[0], allow_nan=False)

    def test_a_clean_cbor_container_still_passes(self):
        # The refusal must be about non-finite values, not about sets or tags.
        event = _state_event()
        event["payload"]["extensions"]["acme.telemetry"]["samples"] = cbor2.CBORTag(
            258, [1.0, 2.0]
        )
        out = self._process_cbor2(event)
        self.assertEqual("STATE_EVENT", out[0]["event"]["event_type"])


class UpstreamMutationTest(unittest.TestCase):
    """No mutation upstream of the gate may turn a non-value into a value.

    `max(0.0, min(1.0, x))` is the shape used at six sites to clamp a
    confidence or a validity window. `min(1.0, nan)` is 1.0 in Python, so
    clamping a NaN confidence rewrote it to MAXIMUM confidence - and because
    the timing degradation runs at gateway.py's timing stage, ahead of
    validate_semantics, the gate then saw a clean 1.0 and forwarded the
    STATE_EVENT. `int(nan)` / `int(inf)` in the valid_for_ms twins raise
    straight out of the gateway instead of refusing.

    These assert the whole family, not the one site that was caught: the
    property is that the operand is left EXACTLY as it arrived, so the gate
    downstream still has something to refuse.
    """

    @classmethod
    def setUpClass(cls):
        cls.validator = validators.load_schema(
            ROOT / "schema" / "zmeta-event-1.0.schema.json"
        )
        cls.policy = validators.load_policy(ROOT / "policy")

    def _degrade_policy(self):
        policy = copy.deepcopy(self.policy)
        policy["timing_freshness"] = copy.deepcopy(policy["timing_freshness"])
        policy["timing_freshness"]["mode"] = "degrade"
        return policy

    def test_timing_degradation_leaves_a_non_finite_confidence_alone(self):
        policy = self._degrade_policy()
        for value in NON_FINITE:
            with self.subTest(value=repr(value)):
                event = _put(_state_event(), ["confidence"], value)
                violations = [
                    {
                        "code": "TIMING_STATUS_MISSING",
                        "details": {"action": "degrade"},
                    }
                ]
                validators.apply_timing_freshness_degradation(
                    event, violations, policy["timing_freshness"]
                )
                self.assertTrue(
                    math.isnan(event["confidence"]) or math.isinf(event["confidence"]),
                    event["confidence"],
                )

    def test_degrade_mode_refuses_a_non_finite_confidence_end_to_end(self):
        # The measured defect: confidence in = nan -> STATE_EVENT forwarded
        # with confidence 1.0, because the mutation runs before the gate.
        policy = self._degrade_policy()
        for value in NON_FINITE:
            with self.subTest(value=repr(value)):
                event = _put(_state_event(), ["confidence"], value)
                out = gateway.process_message(
                    json.dumps(event).encode("utf-8"),
                    self.validator,
                    policy,
                    "L",
                    {},
                    "json",
                    timing_state=gateway.ValidationState(),
                    strict_validation=False,
                )
                # Asserted before the loop on purpose: an oracle that only
                # walks the emitted list is satisfied by an empty list, which
                # is how a guard ends up pinning nothing.
                self.assertGreaterEqual(len(out), 1)
                for emitted in out:
                    self.assertEqual("SYSTEM_EVENT", emitted["event"]["event_type"])
                    self.assertIsNone(emitted.get("confidence"))
                    json.dumps(emitted, allow_nan=False)

    def test_degrade_mode_still_degrades_a_real_confidence(self):
        # The guard must refuse to compute on a non-value, not stop degrading.
        policy = self._degrade_policy()
        event = _put(_state_event(), ["confidence"], 0.62)
        out = gateway.process_message(
            json.dumps(event).encode("utf-8"),
            self.validator,
            policy,
            "L",
            {},
            "json",
            timing_state=gateway.ValidationState(),
            strict_validation=False,
        )
        forwarded = [e for e in out if e["event"]["event_type"] == "STATE_EVENT"]
        self.assertEqual(1, len(forwarded))
        self.assertAlmostEqual(0.31, forwarded[0]["confidence"])

    def test_every_clamp_helper_refuses_a_non_finite_operand(self):
        for value in NON_FINITE:
            for name, helper, arg in (
                ("_reduce_confidence", validators._reduce_confidence, 2.0),
                ("_cap_confidence", validators._cap_confidence, 0.5),
            ):
                with self.subTest(helper=name, value=repr(value)):
                    event = _put(_state_event(), ["confidence"], value)
                    self.assertFalse(helper(event, arg))
                    self.assertFalse(math.isfinite(event["confidence"]))
            for name, helper, arg in (
                ("_reduce_valid_for_ms", validators._reduce_valid_for_ms, 2.0),
                ("_cap_valid_for_ms", validators._cap_valid_for_ms, 500),
            ):
                with self.subTest(helper=name, value=repr(value)):
                    event = _put(_state_event(), ["payload", "valid_for_ms"], value)
                    # int(nan) raises ValueError and int(inf) OverflowError:
                    # the guard has to come before the arithmetic, not after.
                    self.assertFalse(helper(event, arg))
                    self.assertFalse(math.isfinite(event["payload"]["valid_for_ms"]))

    def test_failure_mode_degradation_refuses_a_non_finite_confidence(self):
        # The sixth site, on the OUTGOING event, ahead of
        # validate_outgoing_event's copy of the same gate.
        state = gateway.ValidationState()
        event = _put(_state_event(), ["confidence"], float("nan"))
        state.latest_timing[validators._source_key(event)] = {
            "sync_state": "UNSYNCED",
            "_event_ts": "2025-01-17T14:39:00Z",
        }
        gateway._apply_failure_mode_degradation(
            event,
            {"timing_loss": {"enabled": True, "confidence_reduction_factor": 2.0}},
            state,
            self.policy.get("timing_freshness", {}),
        )
        self.assertTrue(math.isnan(event["confidence"]))


class DiagnosticDetailsTest(unittest.TestCase):
    """The gateway's own refusal must be parseable by the consumer it warns.

    Violation `details` are merged verbatim into `payload.metrics`, so any
    check that echoes an event-derived number puts it back on the wire inside
    the refusal. `validate_timing_quality` runs ahead of validate_semantics
    and echoed `est_error_ms`, so the refusal itself shipped a raw NaN.
    """

    @classmethod
    def setUpClass(cls):
        cls.validator = validators.load_schema(
            ROOT / "schema" / "zmeta-event-1.0.schema.json"
        )
        cls.policy = validators.load_policy(ROOT / "policy")

    def _time_status(self, event_id, est_error_ms, ts):
        return {
            "zmeta_version": "1.0",
            "event": {
                "event_id": event_id,
                "event_type": "SYSTEM_EVENT",
                "event_subtype": "TIME_STATUS",
                "ts": ts,
            },
            "source": {
                "platform_id": "lora-node-01",
                "node_role": "GATEWAY",
                "producer": "sensorops",
            },
            "profile": "L",
            "payload": {
                "system_type": "TIME_STATUS",
                "state": "DEGRADED",
                "metrics": {
                    "time_source": "GPS_PPS",
                    "sync_state": "HOLDOVER",
                    "est_error_ms": est_error_ms,
                    "last_sync_ts": "2025-01-17T14:00:00Z",
                },
            },
        }

    def test_holdover_refusal_is_rfc8259_and_still_names_the_value(self):
        policy = copy.deepcopy(self.policy)
        policy["timing_freshness"] = copy.deepcopy(policy["timing_freshness"])
        policy["timing_freshness"]["holdover_est_error_monotonic"] = {
            "enabled": True,
            "mode": "reject",
        }
        state = gateway.ValidationState()
        gateway.process_message(
            json.dumps(
                self._time_status(
                    "019c2b5c-c047-73ea-8f1a-302b9d9c0a01", 50.0, "2025-01-17T14:40:00Z"
                )
            ).encode("utf-8"),
            self.validator,
            policy,
            "L",
            {},
            "json",
            timing_state=state,
            strict_validation=False,
        )
        out = gateway.process_message(
            json.dumps(
                self._time_status(
                    "019c2b5c-c047-73ea-8f1a-302b9d9c0a02",
                    float("nan"),
                    "2025-01-17T14:41:00Z",
                )
            ).encode("utf-8"),
            self.validator,
            policy,
            "L",
            {},
            "json",
            timing_state=state,
            strict_validation=False,
        )
        self.assertEqual(1, len(out))
        metrics = out[0]["payload"]["metrics"]
        self.assertEqual(
            "TIMING_STATUS_HOLDOVER_NON_MONOTONIC", metrics["reason_code"]
        )
        # Marked, not dropped and not coerced: the operator still learns that
        # est_error_ms was non-finite, and which non-finite it was.
        self.assertEqual("<non-finite:nan>", metrics["current_est_error_ms"])
        self.assertEqual(50.0, metrics["previous_est_error_ms"])
        json.dumps(out[0], allow_nan=False)

    def test_details_are_sanitized_at_the_builder_for_every_validator(self):
        # The class fix is at the boundary where details become wire content,
        # so a check nobody has audited yet inherits it.
        details = {
            "flat": float("nan"),
            "nested": {"deep": [1.0, float("-inf")]},
            "decimal": Decimal("NaN"),
            "kept": 42,
        }
        for builder in (gateway.build_violation_event, gateway.build_warning_event):
            with self.subTest(builder=builder.__name__):
                built = builder("SCHEMA_INVALID", original=_state_event(), details=details)
                json.dumps(built, allow_nan=False)
                metrics = built["payload"]["metrics"]
                self.assertEqual("<non-finite:nan>", metrics["flat"])
                self.assertEqual("<non-finite:-inf>", metrics["nested"]["deep"][1])
                self.assertEqual("<non-finite:nan>", metrics["decimal"])
                self.assertEqual(42, metrics["kept"])
        # The caller's own dict must not be mutated: violation details are
        # also handed to the metrics recorder.
        self.assertTrue(math.isnan(details["flat"]))

    def test_sanitizer_terminates_on_a_cyclic_details_blob(self):
        loop = {"x": float("inf")}
        loop["self"] = loop
        cleaned = gateway._wire_safe_details(loop)
        self.assertEqual("<non-finite:+inf>", cleaned["x"])


class PathScopedCheckCoverageTest(unittest.TestCase):
    """R1-11 A-16: the same defect shape as A-01, one axis over.

    A-01 was a check with a hardcoded list of FIELDS. These two are checks
    with a hardcoded list of PATHS, and the list was short in the direction
    that matters: ``GEO_ZERO_FILL_SUSPECTED`` walked two of the three places
    a payload can carry a ``geo`` block and ``BEARING_FRAME_UNLABELED``
    walked exactly one, so the FUSED estimate — the promoted, downstream
    state, furthest from the sensor that knew the frame, and the one a
    consumer is most likely to act on — was invisible to both. Worse than
    a plain gap: the check's PRESENCE on observations made its absence on
    fusion read as an assertion that the fused bearing WAS labeled.

    The expected path set is derived from the SHIPPED SCHEMAS here, not from
    ``validators._SPATIAL_CONTAINERS``. A test that reads the same constant
    the code reads cannot see a location both of them missed.
    """

    @classmethod
    def setUpClass(cls):
        cls.policy = validators.load_policy(ROOT / "policy")
        cls.severity_map = cls.policy["violation_severities"]

    @staticmethod
    def _schema_payload_paths(key):
        """Every ``payload...<key>`` location the shipped schemas declare."""
        found = set()
        for name in ("zmeta-event-1.0.schema.json", "zmeta-event-1.1.0.schema.json"):
            document = json.loads(
                (ROOT / "schema" / name).read_text(encoding="utf-8")
            )
            for def_name, definition in document.get("$defs", {}).items():
                if not def_name.endswith("Payload") or not isinstance(definition, dict):
                    continue
                properties = definition.get("properties")
                if not isinstance(properties, dict):
                    continue
                if isinstance(properties.get(key), dict):
                    found.add(f"payload.{key}")
                for container, spec in properties.items():
                    if not isinstance(spec, dict):
                        continue
                    nested = spec.get("properties")
                    if isinstance(nested, dict) and isinstance(nested.get(key), dict):
                        found.add(f"payload.{container}.{key}")
        return found

    def _semantics(self, event):
        return validators.validate_semantics(
            event, self.policy["semantics"], self.severity_map
        )

    def _fusion_event(self):
        for line in (
            ROOT / "examples" / "zmeta-v1.1-examples.jsonl"
        ).read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            event = json.loads(line)
            if event.get("event", {}).get("event_type") == "FUSION_EVENT":
                return event
        self.fail("no FUSION_EVENT in the shipped example corpus")

    def _place(self, path, value):
        event = self._fusion_event()
        payload = event["payload"]
        for container in ("claim", "estimated_state"):
            if isinstance(payload.get(container), dict):
                payload[container].pop(path.rsplit(".", 1)[-1], None)
        payload.pop(path.rsplit(".", 1)[-1], None)
        parts = path.split(".")[1:]
        node = payload
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = value
        return event

    def test_unlabeled_bearing_is_reported_at_every_schema_declared_path(self):
        declared = self._schema_payload_paths("bearing")
        self.assertIn("payload.estimated_state.bearing", declared)
        for path in sorted(declared):
            with self.subTest(path=path):
                event = self._place(path, {"az_deg": 45.0})
                _ok, violations = self._semantics(event)
                codes = [v["code"] for v in violations]
                self.assertIn("BEARING_FRAME_UNLABELED", codes, f"{path} is invisible")
                reported = next(
                    v for v in violations if v["code"] == "BEARING_FRAME_UNLABELED"
                )
                # A warning that names the wrong location is not filterable.
                self.assertEqual(path, reported["details"]["path"])
                self.assertEqual("warn", reported["severity"])

    def test_a_labeled_bearing_stays_clean_at_every_path(self):
        # The check must not fire on correctly-labeled data, or it is noise
        # that trains operators to ignore it.
        for path in sorted(self._schema_payload_paths("bearing")):
            with self.subTest(path=path):
                event = self._place(path, {"az_deg": 45.0, "frame": "TRUE_NORTH"})
                _ok, violations = self._semantics(event)
                self.assertNotIn(
                    "BEARING_FRAME_UNLABELED", [v["code"] for v in violations]
                )

    def test_zero_fill_geo_is_reported_at_every_schema_declared_path(self):
        declared = self._schema_payload_paths("geo")
        self.assertIn("payload.estimated_state.geo", declared)
        for path in sorted(declared):
            with self.subTest(path=path):
                event = self._place(path, {"lat": 0.0, "lon": 0.0})
                _ok, violations = self._semantics(event)
                reported = [
                    v for v in violations if v["code"] == "GEO_ZERO_FILL_SUSPECTED"
                ]
                self.assertTrue(reported, f"{path} is invisible")
                self.assertEqual(path, reported[0]["details"]["path"])

    def test_a_real_position_stays_clean_at_every_path(self):
        for path in sorted(self._schema_payload_paths("geo")):
            with self.subTest(path=path):
                event = self._place(path, {"lat": 34.05, "lon": -118.24})
                _ok, violations = self._semantics(event)
                self.assertNotIn(
                    "GEO_ZERO_FILL_SUSPECTED", [v["code"] for v in violations]
                )


if __name__ == "__main__":
    unittest.main()
