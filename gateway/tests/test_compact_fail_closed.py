"""Compact encoding fail-closed tests (R1-11 R11-01).

The compact wire has no zmeta_version key and enumerated field tables, so a
lossy encode silently relabels events as locked-v1.0 and destroys fields
(witnessed live: geo.error_ellipse_m). The honesty rule is refusal over
reduction: dumps()/verify_representable must reject any event that does not
round-trip to a value-identical event (exact except for the two declared
representation normalizations), the gateway compact egress must replace the
event with an ENCODING_UNSUPPORTED diagnostic instead of reducing it, and
that diagnostic must itself be compact-representable and schema/semantics
valid (the GEO_ZERO_FILL_SUSPECTED destroyed-diagnostic lesson).
"""

import ast
import importlib.util
import json
import subprocess
import sys
import unittest
import uuid
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import zmeta_compact  # noqa: E402

VALIDATORS_PATH = ROOT / "gateway" / "src" / "validators.py"
spec_val = importlib.util.spec_from_file_location("zmeta_validators_cfc", VALIDATORS_PATH)
validators = importlib.util.module_from_spec(spec_val)
spec_val.loader.exec_module(validators)

GATEWAY_PATH = ROOT / "gateway" / "src" / "gateway.py"
spec_gw = importlib.util.spec_from_file_location("zmeta_gateway_cfc", GATEWAY_PATH)
gateway = importlib.util.module_from_spec(spec_gw)
spec_gw.loader.exec_module(gateway)


def _load_jsonl(path):
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _v1_1_examples():
    return _load_jsonl(ROOT / "examples" / "zmeta-v1.1-examples.jsonl")


def _hostile_depth():
    """A nesting depth the interpreter cannot recurse to.

    Derived from the live limit rather than hard-coded, so raising
    sys.setrecursionlimit() in a runner cannot quietly drop the pin back
    below the threshold it exists to cross.
    """
    return max(100_000, sys.getrecursionlimit() * 10)


def _deep_chain(depth, leaf=None):
    """A `depth`-deep dict chain, optionally with `leaf` at the bottom."""
    root = current = {}
    for _ in range(depth):
        child = {}
        current["d"] = child
        current = child
    if leaf is not None:
        current["leaf"] = leaf
    return root


class ExpansionBudgetExceeded(Exception):
    """A walk expanded more containers than the structure contains."""


class _Budget:
    """Turns non-termination into a bounded, deterministic failure.

    A walk that never terminates cannot be pinned with a plain assertion --
    the test would hang instead of failing, which is why the residual that
    found this defect had to use a watchdog thread. Instead the FIXTURE
    counts: every expansion of one of these containers spends budget, and a
    walk that revisits a container without limit blows the budget in
    milliseconds. A terminating walk expands each container once and never
    comes near it. No threads, no timeouts, no runaway heap in CI.
    """

    def __init__(self, limit):
        self.limit = limit
        self.used = 0

    def spend(self):
        self.used += 1
        if self.used > self.limit:
            raise ExpansionBudgetExceeded(
                f"walk expanded containers {self.used} times against a budget "
                f"of {self.limit}: it is not terminating"
            )


class _CountedDict(dict):
    def __init__(self, budget, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._budget = budget

    def items(self):
        self._budget.spend()
        return super().items()


class _CountedList(list):
    def __init__(self, budget, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._budget = budget

    def __iter__(self):
        self._budget.spend()
        return super().__iter__()

    def __len__(self):
        self._budget.spend()
        return super().__len__()


def _self_referential_dict(budget):
    node = _CountedDict(budget)
    node["self"] = node
    return node


def _self_referential_list(budget):
    node = _CountedList(budget)
    node.append(node)
    return node


def _all_v1_0_example_events():
    events = []
    for path in sorted((ROOT / "examples").glob("*.jsonl")):
        for event in _load_jsonl(path):
            if event.get("zmeta_version") == "1.0":
                events.append((path.name, event))
    return events


class CompactFailClosedTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.validator = validators.load_schema(ROOT / "schema" / "zmeta-event.schema.json")
        cls.policy = validators.load_policy(ROOT / "policy")

    def test_every_v1_1_example_refuses_compact_encode(self):
        examples = _v1_1_examples()
        self.assertGreaterEqual(len(examples), 13, "v1.1 example corpus shrank")
        for idx, event in enumerate(examples):
            with self.subTest(index=idx, subtype=event["event"].get("event_subtype")):
                with self.assertRaises(zmeta_compact.CompactUnrepresentableError):
                    zmeta_compact.dumps(event)

    def test_v1_0_example_corpus_still_roundtrips(self):
        events = _all_v1_0_example_events()
        self.assertGreaterEqual(len(events), 30, "v1.0 example corpus shrank")
        for name, event in events:
            with self.subTest(corpus=name, event_id=event["event"]["event_id"]):
                restored = zmeta_compact.loads(zmeta_compact.dumps(event))
                self.assertEqual(restored, event)

    def test_refusal_message_names_version_or_lossy_path(self):
        state = next(
            e for e in _v1_1_examples()
            if "error_ellipse_m" in e.get("payload", {}).get("geo", {})
        )
        with self.assertRaises(zmeta_compact.CompactUnrepresentableError) as ctx:
            zmeta_compact.verify_representable(state)
        self.assertIn("1.0", str(ctx.exception))

        lossy = {
            "zmeta_version": "1.0",
            "event": {
                "event_id": "019c2b5d-4cd9-770e-b02d-55d71e516898",
                "event_type": "STATE_EVENT",
                "event_subtype": "TRACK_STATE",
                "ts": "2025-01-17T14:31:05Z",
            },
            "source": {
                "platform_id": "fusion-node-01",
                "node_role": "FUSION",
                "producer": "fusion-engine",
            },
            "payload": {
                "track_id": "trk-001",
                "geo": {
                    "lat": 34.05,
                    "lon": -118.24,
                    "alt_m": 120.0,
                    "error_ellipse_m": {"semi_major": 150.0, "semi_minor": 75.0},
                },
            },
        }
        with self.assertRaises(zmeta_compact.CompactUnrepresentableError) as ctx:
            zmeta_compact.verify_representable(lossy)
        self.assertIn("error_ellipse_m", str(ctx.exception))
        self.assertIn("dropped", str(ctx.exception))

        # A truncated sub-millisecond instant IS loss (the epoch-ms mapping
        # cannot carry it) and is refused with the exact path named.
        sub_ms = json.loads(json.dumps(lossy))
        del sub_ms["payload"]["geo"]["error_ellipse_m"]
        sub_ms["event"]["ts"] = "2025-01-17T14:31:05.1234Z"
        with self.assertRaises(zmeta_compact.CompactUnrepresentableError) as ctx:
            zmeta_compact.verify_representable(sub_ms)
        self.assertIn("$.event.ts", str(ctx.exception))

    def test_gateway_encode_message_compact_refuses_v1_1(self):
        state = _v1_1_examples()[0]
        with self.assertRaises(zmeta_compact.CompactUnrepresentableError):
            gateway._encode_message(state, "compact")
        # json/cbor/proto remain version-preserving for the same event.
        for encoding in ("json", "cbor", "proto"):
            self.assertTrue(gateway._encode_message(state, encoding))

    def test_encoding_unsupported_diagnostic_survives_the_full_chain(self):
        original = next(
            e for e in _v1_1_examples()
            if "error_ellipse_m" in e.get("payload", {}).get("geo", {})
        )
        diagnostic = gateway.build_violation_event(
            "ENCODING_UNSUPPORTED",
            original=original,
            details={"error": "compact encoding would lose payload.geo.error_ellipse_m"},
            force_schema_violation=True,
        )
        self.assertEqual(diagnostic["event"]["event_subtype"], "SCHEMA_VIOLATION")
        self.assertEqual(
            diagnostic["payload"]["metrics"]["original_event_id"],
            original["event"]["event_id"],
        )
        # The replacement diagnostic must itself be compact-representable...
        zmeta_compact.verify_representable(diagnostic)
        self.assertEqual(
            zmeta_compact.loads(zmeta_compact.dumps(diagnostic)), diagnostic
        )
        # ...and must not be destroyed by outgoing validation.
        self.assertEqual(list(self.validator.iter_errors(diagnostic)), [])
        ok, violations = validators.validate_semantics(
            diagnostic,
            self.policy["semantics"],
            self.policy["violation_severities"],
        )
        self.assertTrue(ok, violations)
        self.assertEqual([], violations)

    # --- declared representation normalizations (post-fix verification) ----
    # The wave-1 check compared byte-wise, which refused schema-valid events
    # from conforming producers: the uuid pattern admits uppercase hex and
    # utcDateTime admits fractional seconds. Both bladeRF real-capture
    # fixtures (millisecond timestamps) were refused by their own repo.

    def _v1_0_state(self, **event_overrides):
        event = json.loads(
            (ROOT / "examples" / "encoding-roundtrip.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()[0]
        )
        self.assertEqual(event["zmeta_version"], "1.0")
        event["event"].update(event_overrides)
        return event

    def test_uppercase_uuid_is_representable_and_decodes_canonical(self):
        event = self._v1_0_state()
        lower = event["event"]["event_id"]
        upper = self._v1_0_state(event_id=lower.upper())
        self.assertEqual(list(self.validator.iter_errors(upper)), [])

        restored = zmeta_compact.loads(zmeta_compact.dumps(upper))
        # Same UUID, RFC 4122 canonical lowercase form on the wire.
        self.assertEqual(restored["event"]["event_id"], lower)
        self.assertEqual(list(self.validator.iter_errors(restored)), [])

    def test_millisecond_timestamps_are_representable(self):
        for ts in ("2025-02-01T12:00:00.000Z", "2025-02-01T12:00:00.876Z"):
            with self.subTest(ts=ts):
                event = self._v1_0_state(ts=ts)
                self.assertEqual(list(self.validator.iter_errors(event)), [])
                restored = zmeta_compact.loads(zmeta_compact.dumps(event))
                # Same instant, re-formatted at the declared resolution.
                self.assertEqual(
                    zmeta_compact._instant(restored["event"]["ts"]),
                    zmeta_compact._instant(ts),
                )

    def test_shipped_mapping_pack_expected_events_are_representable(self):
        packs = sorted((ROOT / "adapters" / "mapping-packs").glob("*/tests/*/expected.json"))
        packs += sorted((ROOT / "adapters" / "mapping-packs").glob("*/tests/expected.json"))
        checked = 0
        for path in packs:
            payload = json.loads(path.read_text(encoding="utf-8"))
            for event in payload if isinstance(payload, list) else [payload]:
                if not isinstance(event, dict) or event.get("zmeta_version") != "1.0":
                    continue
                with self.subTest(pack=path.relative_to(ROOT).as_posix()):
                    zmeta_compact.verify_representable(event)
                checked += 1
        self.assertGreaterEqual(checked, 3, "mapping-pack expected-event corpus shrank")

    def test_sub_millisecond_precision_is_still_refused(self):
        event = self._v1_0_state(ts="2025-02-01T12:00:00.1234Z")
        with self.assertRaises(zmeta_compact.CompactUnrepresentableError) as ctx:
            zmeta_compact.verify_representable(event)
        self.assertIn("$.event.ts", str(ctx.exception))

    def test_non_finite_floats_are_refused_through_real_serialization(self):
        # Verification runs through encode->bytes->decode; an in-memory
        # comparison would pass NaN because container equality
        # short-circuits on object identity.
        for bad in (float("nan"), float("inf")):
            with self.subTest(value=repr(bad)):
                event = self._v1_0_state()
                event.setdefault("payload", {}).setdefault("extensions", {})[
                    "vendor"
                ] = {"snr_db": bad}
                with self.assertRaises(zmeta_compact.CompactUnrepresentableError) as ctx:
                    zmeta_compact.verify_representable(event)
                self.assertIn("$.payload.extensions.vendor.snr_db", str(ctx.exception))

    def test_wire_output_is_always_canonical_json_serializable(self):
        for name, event in _all_v1_0_example_events():
            with self.subTest(corpus=name):
                decoded = zmeta_compact.loads(zmeta_compact.dumps(event))
                json.dumps(decoded, allow_nan=False)

    def test_bool_never_matches_numeric_equivalent(self):
        self.assertIsNotNone(zmeta_compact._semantic_difference(True, 1))
        self.assertIsNotNone(zmeta_compact._semantic_difference(0, False))
        self.assertIsNone(zmeta_compact._semantic_difference(True, True))

    # --- gateway recovery ladder must never raise --------------------------

    def test_gateway_recovery_never_raises_when_diagnostic_inherits_defect(self):
        # The diagnostic copies the original's event_id into
        # metrics.original_event_id, so a value that made the original
        # unrepresentable can make the diagnostic unrepresentable too. The
        # ladder must fall back to the UNKNOWN sentinel, never propagate.
        settings = {
            "output_encoding": "compact",
            "stamp_contract_hash": False,
            "profile": "H",
        }
        poisoned = self._v1_0_state(ts="2025-02-01T12:00:00.1234Z")

        payload, emitted = gateway._encode_outgoing_or_diagnostic(
            poisoned,
            settings,
            contract_hashes=None,
            should_stamp_profile=False,
            metrics=None,
        )

        self.assertIsNotNone(payload, "recovery ladder produced no payload")
        self.assertEqual(emitted["event"]["event_subtype"], "SCHEMA_VIOLATION")
        self.assertEqual(
            emitted["payload"]["metrics"]["reason_code"], "ENCODING_UNSUPPORTED"
        )
        decoded = zmeta_compact.loads(payload)
        self.assertEqual(decoded["payload"]["metrics"]["reason_code"], "ENCODING_UNSUPPORTED")
        self.assertEqual(list(self.validator.iter_errors(emitted)), [])

    def test_gateway_recovery_falls_back_to_unknown_sentinel_rung(self):
        # Force the first diagnostic rung to fail so the terminal rung (no
        # original -> UNKNOWN correlation sentinel, zero caller-controlled
        # content) is proven to work rather than assumed.
        settings = {
            "output_encoding": "compact",
            "stamp_contract_hash": False,
            "profile": "H",
        }
        real_encode = gateway._encode_message
        calls = []

        def flaky_encode(event, encoding):
            calls.append(event)
            metrics = event.get("payload", {}).get("metrics", {})
            # Only the terminal rung (UNKNOWN sentinel) is allowed to encode:
            # the original and the diagnostic that inherits its event_id both
            # fail, exactly as an inherited unrepresentable value behaves.
            if metrics.get("original_event_id") == "UNKNOWN":
                return real_encode(event, encoding)
            raise zmeta_compact.CompactUnrepresentableError("forced: inherited defect")

        with mock.patch.object(gateway, "_encode_message", flaky_encode):
            payload, emitted = gateway._encode_outgoing_or_diagnostic(
                self._v1_0_state(),
                settings,
                contract_hashes=None,
                should_stamp_profile=False,
                metrics=None,
            )

        self.assertIsNotNone(payload, "terminal fallback rung failed to encode")
        self.assertEqual(emitted["payload"]["metrics"]["original_event_id"], "UNKNOWN")
        self.assertEqual(
            emitted["payload"]["metrics"]["reason_code"], "ENCODING_UNSUPPORTED"
        )
        self.assertEqual(list(self.validator.iter_errors(emitted)), [])
        self.assertGreaterEqual(len(calls), 3, "ladder did not exhaust both rungs")

    def test_gateway_recovery_returns_none_instead_of_raising_when_all_rungs_fail(self):
        settings = {
            "output_encoding": "compact",
            "stamp_contract_hash": False,
            "profile": "H",
        }

        def always_fails(event, encoding):
            raise zmeta_compact.CompactUnrepresentableError("forced: nothing encodable")

        with mock.patch.object(gateway, "_encode_message", always_fails):
            payload, emitted = gateway._encode_outgoing_or_diagnostic(
                self._v1_0_state(),
                settings,
                contract_hashes=None,
                should_stamp_profile=False,
                metrics=None,
            )

        # The receive loop drops the datagram; it must never terminate.
        self.assertIsNone(payload)
        self.assertIsNotNone(emitted)

    def test_gateway_recovery_passes_through_representable_events(self):
        settings = {
            "output_encoding": "compact",
            "stamp_contract_hash": False,
            "profile": "H",
        }
        event = self._v1_0_state()
        payload, emitted = gateway._encode_outgoing_or_diagnostic(
            event,
            settings,
            contract_hashes=None,
            should_stamp_profile=False,
            metrics=None,
        )
        self.assertIsNotNone(payload)
        self.assertEqual(emitted, event)

    def test_command_original_stays_schema_violation_when_forced(self):
        command = {
            "zmeta_version": "1.0",
            "event": {
                "event_id": "019c2b5d-4cd9-770e-b02d-55d63910a2e7",
                "event_type": "COMMAND_EVENT",
                "event_subtype": "GOTO",
                "ts": "2025-01-17T14:31:00Z",
            },
            "source": {
                "platform_id": "comms-node-1",
                "node_role": "GATEWAY",
                "producer": "sensorops",
            },
            "payload": {"task_id": "task-001", "task_type": "GOTO"},
        }
        forced = gateway.build_violation_event(
            "ENCODING_UNSUPPORTED", original=command, force_schema_violation=True
        )
        self.assertEqual(forced["event"]["event_subtype"], "SCHEMA_VIOLATION")
        self.assertEqual(list(self.validator.iter_errors(forced)), [])
        # Default TASK_ACK selection for commands is unchanged for task codes.
        acked = gateway.build_violation_event("TASK_REJECTED", original=command)
        self.assertEqual(acked["event"]["event_subtype"], "TASK_ACK")

    # --- crash class: codec-internal failures must refuse, never raise raw --
    # (R1-11 verification pass 2.) The recovery ladder handles exactly
    # CompactUnrepresentableError; a raw OverflowError / ValueError /
    # RecursionError escaping the codec on schema-valid input terminated the
    # gateway process for every producer behind it.

    def _both_cbor_backends(self):
        """Run a check once per supported CBOR backend.

        Representability must be a property of the MAPPING, not of the local
        install: zmeta_cbor and cbor2 disagree about out-of-range integers
        (cbor2 emits a bignum tag that a zmeta_cbor consumer decodes as raw
        BYTES), so any guarantee asserted here has to hold on both.
        """
        yield "zmeta_cbor"
        original = zmeta_compact.zmeta_cbor
        if original is None:
            return
        zmeta_compact.zmeta_cbor = None
        try:
            yield "cbor2"
        finally:
            zmeta_compact.zmeta_cbor = original

    def test_oversized_int_refuses_on_every_backend(self):
        for backend in self._both_cbor_backends():
            for value in (2**64, -(2**64) - 1, 2**70):
                with self.subTest(backend=backend, value=value):
                    event = self._v1_0_state()
                    event.setdefault("payload", {}).setdefault("extensions", {})[
                        "vendor"
                    ] = {"sample_count": value}
                    with self.assertRaises(
                        zmeta_compact.CompactUnrepresentableError
                    ) as ctx:
                        zmeta_compact.dumps(event)
                    self.assertIn("CBOR 64-bit range", str(ctx.exception))

    def test_cbor_range_boundary_is_representable_on_every_backend(self):
        # The refusal must be exactly at the CBOR major-type 0/1 boundary,
        # not a conservative guess that also rejects honest events.
        for backend in self._both_cbor_backends():
            for value in (2**64 - 1, -(2**64), 0, -1):
                with self.subTest(backend=backend, value=value):
                    event = self._v1_0_state()
                    event.setdefault("payload", {}).setdefault("extensions", {})[
                        "vendor"
                    ] = {"sample_count": value}
                    restored = zmeta_compact.loads(zmeta_compact.dumps(event))
                    self.assertEqual(
                        restored["payload"]["extensions"]["vendor"]["sample_count"],
                        value,
                    )

    def test_nesting_beyond_decode_depth_refuses_instead_of_raising(self):
        # Depth must exceed the interpreter's recursion limit, on EVERY
        # backend. The original pin used 300 -- above zmeta_cbor's max_depth
        # of 64 but far below sys.getrecursionlimit(), so it never reached
        # the recursive pre-scan that sat in front of the guard, and it never
        # reached cbor2's own 400-item nesting ceiling either. Both escapes
        # were live at that depth and the pin could not see them (R1-11
        # fresh-audit A-04).
        depth = _hostile_depth()
        self.assertGreater(depth, sys.getrecursionlimit())
        for backend in self._both_cbor_backends():
            for value in (None, 2**70):
                # Deep alone, and deep carrying an unencodable int at the
                # bottom: the second proves the traversal still reaches the
                # floor of a structure it can no longer recurse into.
                with self.subTest(backend=backend, leaf=value):
                    event = self._v1_0_state()
                    event.setdefault("payload", {}).setdefault("extensions", {})[
                        "vendor"
                    ] = _deep_chain(depth, leaf=value)
                    with self.assertRaises(
                        zmeta_compact.CompactUnrepresentableError
                    ):
                        zmeta_compact.dumps(event)

    def test_backend_native_codec_errors_become_refusals(self):
        # The guard names built-in exceptions, but cbor2's CBOREncodeError /
        # CBORDecodeError descend from CBORError -> Exception and are NOT
        # ValueError subclasses. Depth 500 is the window where that is the
        # SOLE failure: past cbor2's own 400-item nesting ceiling, below the
        # interpreter's recursion limit. Whether an event refuses honestly
        # must not depend on which CBOR library happens to be installed.
        if zmeta_compact.cbor2 is None:  # pragma: no cover - optional dep
            self.skipTest("cbor2 not installed")
        self.assertLess(500, sys.getrecursionlimit())
        original = zmeta_compact.zmeta_cbor
        zmeta_compact.zmeta_cbor = None
        try:
            event = self._v1_0_state()
            event.setdefault("payload", {}).setdefault("extensions", {})[
                "vendor"
            ] = _deep_chain(500)
            with self.assertRaises(zmeta_compact.CompactUnrepresentableError):
                zmeta_compact.dumps(event)
        finally:
            zmeta_compact.zmeta_cbor = original

    def test_unencodable_int_scan_survives_hostile_nesting_depth(self):
        # The mapping-limit scan runs on the encode path, in front of nothing
        # that can rescue it: it must not tie the process stack to
        # sender-controlled nesting depth (same rule as
        # validators._find_forbidden_key).
        depth = _hostile_depth()
        self.assertGreater(depth, sys.getrecursionlimit())
        clean = _deep_chain(depth)
        self.assertIsNone(zmeta_compact._find_unencodable_int(clean))
        found = zmeta_compact._find_unencodable_int(_deep_chain(depth, leaf=2**70))
        self.assertIsNotNone(found)
        self.assertIn("CBOR 64-bit range", found)
        # Lists are the other container the walk descends; depth is
        # sender-controlled through either one.
        deep_list = current = []
        for _ in range(depth):
            child = []
            current.append(child)
            current = child
        self.assertIsNone(zmeta_compact._find_unencodable_int(deep_list))
        current.append(2**70)
        self.assertIn(
            "CBOR 64-bit range", zmeta_compact._find_unencodable_int(deep_list)
        )

    def test_unencodable_int_scan_terminates_on_self_referential_structure(self):
        # The iterative rewrite removed the RecursionError but added no
        # visited set and no bound, so a structure that refers back to itself
        # spun forever with the heap rising: a bounded crash traded for an
        # unbounded hang, which is worse -- the crash was already being
        # converted into a governed refusal by the guard this scan now sits
        # inside (R1-11 residual against the A-04 wave).
        #
        # Reachability is not theoretical. json.loads cannot build a cycle,
        # but CBOR ingress can: cbor2 honours the value-sharing tags
        # (28 shareable / 29 sharedref) by default, so a ~600 byte datagram
        # decodes into a self-referential dict on a cbor2-only install -- a
        # configuration both zmeta_compact's backend selection and
        # gateway._decode_cbor explicitly support. See
        # CborValueSharingReachabilityTest below.
        for label, factory in (
            ("dict", _self_referential_dict),
            ("list", _self_referential_list),
        ):
            with self.subTest(container=label):
                budget = _Budget(64)
                value = factory(budget)
                # A cycle has no finite CBOR encoding, so the refusal belongs
                # to the MAPPING and must not be left to whichever backend is
                # installed: zmeta_cbor raises RecursionError (which names the
                # wrong cause) and cbor2 raises CBOREncodeValueError.
                with self.assertRaises(
                    zmeta_compact.CompactUnrepresentableError
                ) as caught:
                    zmeta_compact._find_unencodable_int(value)
                self.assertIn("refers back to itself", str(caught.exception))

    def test_shared_but_acyclic_structure_is_not_refused_as_a_cycle(self):
        # The other half of the trade: terminating by refusing anything seen
        # twice would reject a perfectly representable event. Sharing is not a
        # cycle. This is also the check that the seen-set is not just a
        # disguised bound -- nothing large-but-honest may be discarded.
        shared_clean = {"n": 1}
        self.assertIsNone(
            zmeta_compact._find_unencodable_int(
                {"a": shared_clean, "b": shared_clean}
            )
        )
        # And the skip must not hide an offender: a shared subtree reachable
        # only through the SECOND reference is still reported.
        shared_bad = {"n": 2**70}
        self.assertEqual(
            "$.b.n (integer %d is outside the CBOR 64-bit range)" % (2**70),
            zmeta_compact._find_unencodable_int({"a": {"x": 1}, "b": shared_bad}),
        )
        # Sharing at every level is 2**levels distinct paths. Before the
        # seen-set this was exponential work off a few hundred wire bytes;
        # it must now be linear in CONTAINERS.
        budget = _Budget(256)
        node = _CountedDict(budget, {"leaf": 1})
        for _ in range(64):
            node = _CountedDict(budget, {"l": node, "r": node})
        self.assertIsNone(zmeta_compact._find_unencodable_int(node))

    def test_dumps_refuses_a_self_referential_event(self):
        # End of the class, through the public API: the operator gets the one
        # governed refusal the compact ladder handles, not a hang.
        #
        # The vendor blob is budget-counted so that reverting the fix makes
        # THIS test fail too instead of wedging the whole suite. The budget is
        # deliberately loose -- it only has to be finite.
        budget = _Budget(512)
        for entry in (zmeta_compact.dumps, zmeta_compact.verify_representable):
            with self.subTest(entry=entry.__name__):
                event = self._v1_0_state()
                event.setdefault("payload", {}).setdefault("extensions", {})[
                    "vendor"
                ] = _self_referential_dict(budget)
                with self.assertRaises(
                    zmeta_compact.CompactUnrepresentableError
                ) as caught:
                    entry(event)
                self.assertIn("refers back to itself", str(caught.exception))

    def test_no_recursive_walk_runs_outside_the_fail_closed_guard(self):
        """Structural pin: nothing that can RecursionError may sit in front
        of the try that converts RecursionError into a refusal.

        The behavioural pins above can only see failures a live input can
        reach today. _semantic_difference is still recursive and is only
        depth-bounded because decode refuses first -- move its call back out
        of the try and no input in this suite notices, until some later
        change to the decode limits makes it reachable. That is the exact
        shape of A-04: a guard defeated by code shipped alongside it. This
        test reads the module's own structure instead, so the family is
        enumerated from the code rather than from anyone's memory of it.

        Two things this pin gets wrong if written casually, both of which it
        got wrong on the first pass and both of which let a live escape pass
        green:
          - "inside the try" is the try BODY, not ast.walk(Try). An else:,
            finally: or except: clause is outside the guard.
          - the perimeter is the whole encode path, not one function. A
            pre-scan in dumps() escapes just as completely.
        """
        source = (ROOT / "zmeta_compact.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        funcs = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}

        def callees(node):
            return {
                sub.func.id
                for sub in ast.walk(node)
                if isinstance(sub, ast.Call)
                and isinstance(sub.func, ast.Name)
                and sub.func.id in funcs
            }

        graph = {name: callees(node) for name, node in funcs.items()}

        def closure(names, stop=frozenset()):
            seen, stack = set(), [n for n in names if n not in stop]
            while stack:
                current = stack.pop()
                if current in seen:
                    continue
                seen.add(current)
                stack.extend(c for c in graph.get(current, ()) if c not in stop)
            return seen

        recursive = {name for name in funcs if name in closure(graph[name])}
        # Vacuity guard: this module HAS recursive walkers. If the scan finds
        # none, the parse broke and the assertion below means nothing.
        self.assertTrue(recursive, "recursion scan found nothing to check")
        # AsyncFunctionDef and Lambda are in this list because `funcs` cannot
        # see them at all: a recursive walker written as either would be
        # invisible to the call graph below, and so would every escape it
        # makes. There are none today; if one appears, re-derive this test
        # rather than widening the assertion.
        self.assertEqual(
            len(funcs),
            len(
                [
                    n
                    for n in ast.walk(tree)
                    if isinstance(
                        n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)
                    )
                ]
            ),
            "nested / async / lambda function defs exist; the top-level scan "
            "no longer sees every function in this module",
        )
        self.assertIn(
            "_semantic_difference",
            recursive,
            "the known recursive walker is gone from the scan -- if it was "
            "made iterative that is an improvement, but re-derive this "
            "test's coverage before deleting the assertion",
        )

        guard = "_verified_compact_bytes"
        guarded = funcs[guard]
        tries = [n for n in ast.walk(guarded) if isinstance(n, ast.Try)]
        self.assertEqual(1, len(tries), "expected exactly one guard try block")
        # ONLY the try BODY is protected. ast.walk over an ast.Try descends
        # into handlers, orelse and finalbody as well, and code in an
        # `except:` / `else:` / `finally:` clause is semantically OUTSIDE the
        # guard -- an exception raised there propagates raw. Counting those as
        # "inside" is how the first version of this pin stayed green on a
        # source where the recursive walk provably escaped: moving the
        # _semantic_difference call from the try body into an `else:` of the
        # same try turned the refusal back into a raw RecursionError and this
        # test did not notice (R1-11 residual against the A-04 wave).
        protected = {
            id(n) for stmt in tries[0].body for n in ast.walk(stmt)
        }
        self.assertTrue(protected, "the guard's try body is empty")

        # The perimeter is not just the guard function. A recursive pre-scan
        # added one level up, in dumps() or verify_representable(), is exactly
        # as far outside the try as one added in front of it -- and that is
        # A-04's own shape. Derive the encode-path entry points from the call
        # graph rather than naming them from memory, so a public entry added
        # later is covered the day it is written.
        entries = {
            name
            for name in funcs
            if not name.startswith("_") and guard in closure(graph[name])
        } | {guard}
        for expected in ("dumps", "verify_representable"):
            self.assertIn(
                expected,
                entries,
                f"{expected}() no longer routes through {guard}; the "
                "perimeter this test walks is derived from that fact",
            )

        # Three ways a module function reaches the outside of the guard, all
        # of which a naive "Call with a Name func" scan misses. B1/B2 below
        # were live blind spots in this pin until they were attacked:
        #   f(...)          a plain call
        #   obj.f(...)      an attribute call -- the graph is name-based, so
        #                   this is invisible unless matched on the attr
        #   g = f; g(...)   a bare reference that hands the function off; a
        #                   rename must not be a way out of the guard
        unguarded = set()
        for name in entries:
            for sub in ast.walk(funcs[name]):
                if id(sub) in protected:
                    continue
                if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name):
                    if sub.func.id in funcs:
                        unguarded.add(sub.func.id)
                elif isinstance(sub, ast.Attribute) and sub.attr in funcs:
                    unguarded.add(sub.attr)
                elif (
                    isinstance(sub, ast.Name)
                    and isinstance(sub.ctx, ast.Load)
                    and sub.id in funcs
                ):
                    unguarded.add(sub.id)
        # Calls TO the guard are what the entries are supposed to do, and the
        # guard's own interior is judged by `protected` above, so do not walk
        # back through it.
        exposed = sorted(closure(unguarded, stop={guard}) & recursive)
        self.assertEqual(
            [],
            exposed,
            "recursive walker(s) reachable from the compact encode path "
            f"({sorted(entries)}) outside the {guard} try body: {exposed}",
        )
        # And the guard must actually be covering something.
        guarded_calls = {
            sub.func.id
            for stmt in tries[0].body
            for sub in ast.walk(stmt)
            if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name)
            and sub.func.id in funcs
        }
        self.assertTrue(closure(guarded_calls) & recursive)

    def test_unencodable_int_scan_reports_first_offender_with_path(self):
        # Pin the traversal ORDER and the path text, not just "something was
        # found": an iterative walk that reports a different offender than
        # the pre-order walk changes the refusal message operators filter on.
        value = {"a": {"b": [{"c": 2**70}]}, "z": -(2**64) - 1}
        self.assertEqual(
            "$.a.b[0].c (integer %d is outside the CBOR 64-bit range)" % (2**70),
            zmeta_compact._find_unencodable_int(value),
        )
        self.assertIsNone(zmeta_compact._find_unencodable_int({"a": {"b": [True, 1]}}))

    def test_gateway_forwards_encoding_unsupported_for_hostile_nesting(self):
        # The honest end of A-04: the consumer must get the governed
        # ENCODING_UNSUPPORTED refusal, not silence. Before the fix the raw
        # RecursionError escaped _COMPACT_UNREPRESENTABLE entirely and the
        # datagram was dropped as INTERNAL_ERROR with nothing forwarded.
        settings = {
            "output_encoding": "compact",
            "stamp_contract_hash": False,
            "profile": "H",
        }
        event = self._v1_0_state()
        event.setdefault("payload", {}).setdefault("extensions", {})["vendor"] = (
            _deep_chain(_hostile_depth())
        )

        payload, emitted = gateway._encode_outgoing_or_diagnostic(
            event,
            settings,
            contract_hashes=None,
            should_stamp_profile=False,
            metrics=None,
        )

        self.assertIsNotNone(payload, "hostile nesting produced no forwarded payload")
        self.assertEqual(
            emitted["payload"]["metrics"]["reason_code"], "ENCODING_UNSUPPORTED"
        )
        decoded = zmeta_compact.loads(payload)
        self.assertEqual(
            decoded["payload"]["metrics"]["reason_code"], "ENCODING_UNSUPPORTED"
        )
        self.assertEqual(list(self.validator.iter_errors(emitted)), [])

    def test_sub_microsecond_truncation_is_refused(self):
        # datetime.fromisoformat truncates at microseconds, so BOTH sides of a
        # parsed-value comparison lose the same digits and cannot see the
        # loss. The original's resolution must be checked directly.
        for ts in (
            "2025-02-01T12:00:00.8760001Z",
            "2025-02-01T12:00:00.876000000001Z",
        ):
            with self.subTest(ts=ts):
                event = self._v1_0_state(ts=ts)
                with self.assertRaises(zmeta_compact.CompactUnrepresentableError):
                    zmeta_compact.verify_representable(event)

    def test_trailing_zero_millisecond_timestamps_stay_representable(self):
        # Guard the other direction: '.876000Z' is millisecond resolution
        # written long-hand, not sub-millisecond precision.
        for ts in ("2025-02-01T12:00:00.876000Z", "2025-02-01T12:00:00.8760Z"):
            with self.subTest(ts=ts):
                zmeta_compact.verify_representable(self._v1_0_state(ts=ts))

    def test_decode_refuses_out_of_range_epoch_ms_instead_of_crashing(self):
        # loads() is public API on the INGRESS side, outside the encode-path
        # guard: a hostile epoch-ms value must fail closed, not crash the
        # consumer with a raw OverflowError.
        for wire_ms in (2**63, -(2**63), 10**18):
            with self.subTest(wire_ms=wire_ms):
                with self.assertRaises(zmeta_compact.CompactUnrepresentableError):
                    zmeta_compact._format_ts(wire_ms)

    # --- epoch-ms arithmetic must be exact, never float-mediated -----------
    # int(dt.timestamp() * 1000) was off by one for a date-banded fraction of
    # schema-valid millisecond timestamps (6% in the sweep below), so the
    # round-trip check refused honest events from conforming producers.

    def test_epoch_ms_round_trip_is_exact_across_sweep(self):
        bands = (-86400000, 1076707800000, 1753142400000, 4102444800000)
        for base in bands:
            for ms in range(base, base + 500):
                if zmeta_compact._parse_ts(zmeta_compact._format_ts(ms)) != ms:
                    self.fail(f"epoch-ms round trip corrupted {ms}")

    def test_float_banded_millisecond_timestamp_is_representable(self):
        # 1076707800001 ms: a concrete value the float path parsed one ms
        # early, refusing the schema-valid event that carried it.
        event = self._v1_0_state(ts="2004-02-13T21:30:00.001Z")
        self.assertEqual(list(self.validator.iter_errors(event)), [])
        restored = zmeta_compact.loads(zmeta_compact.dumps(event))
        self.assertEqual(
            zmeta_compact._instant(restored["event"]["ts"]),
            zmeta_compact._instant("2004-02-13T21:30:00.001Z"),
        )

    def test_out_of_platform_epoch_range_timestamps_round_trip(self):
        # datetime.timestamp()/fromtimestamp() raise OSError on Windows for
        # instants outside the platform epoch range; exact timedelta
        # arithmetic makes these honest round-trips instead of crashes.
        for ts in ("1969-12-31T23:59:59.500Z", "9999-12-31T23:59:59.999Z"):
            with self.subTest(ts=ts):
                event = self._v1_0_state(ts=ts)
                restored = zmeta_compact.loads(zmeta_compact.dumps(event))
                self.assertEqual(
                    zmeta_compact._instant(restored["event"]["ts"]),
                    zmeta_compact._instant(ts),
                )

    def test_convert_encoding_cli_refuses_v1_1_to_compact(self):
        tmp = ROOT / "pytest-work" / f"compact-refuse-{uuid.uuid4().hex}"
        tmp.mkdir(parents=True, exist_ok=False)
        try:
            src = tmp / "event.json"
            dst = tmp / "event.compact"
            src.write_text(json.dumps(_v1_1_examples()[0]), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "tools" / "convert_encoding.py"),
                    "--from", "json",
                    "--to", "compact",
                    "--input", str(src),
                    "--output", str(dst),
                ],
                capture_output=True,
                text=True,
                cwd=str(ROOT),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("conversion refused", result.stderr)
            self.assertFalse(dst.exists(), "refused conversion must not write output")
        finally:
            import shutil

            shutil.rmtree(tmp, ignore_errors=True)
            try:
                (ROOT / "pytest-work").rmdir()
            except OSError:
                pass


class CborValueSharingReachabilityTest(unittest.TestCase):
    """Records WHY the cycle-termination pins above matter.

    The residual that found the non-terminating walk called it unreachable
    from the wire, on the grounds that json.loads cannot build a cycle. That
    is true of JSON and false of the gateway: CBOR ingress is a supported
    input encoding, gateway._decode_cbor falls back to cbor2 when zmeta_cbor
    is absent (an install both modules explicitly support), and cbor2 honours
    the standard value-sharing tags by default. This test asserts only the
    decode fact -- it never walks the result, so it cannot hang even with the
    fix reverted. If cbor2 ever stops doing this the pin fails, and that is
    correct: the threat model changed and the walkers' cycle-safety should be
    re-derived rather than assumed.
    """

    def test_cbor2_ingress_decode_can_produce_a_self_referential_event(self):
        if zmeta_compact.cbor2 is None:  # pragma: no cover - optional dep
            self.skipTest("cbor2 not installed")
        vendor = {}
        vendor["self"] = vendor
        event = {"payload": {"extensions": {"vendor": vendor}}}
        wire = zmeta_compact.cbor2.dumps(event, value_sharing=True)
        self.assertLess(len(wire), 256, "the hostile datagram is tiny")

        original = gateway.zmeta_cbor
        gateway.zmeta_cbor = None  # the supported cbor2-only install
        try:
            decoded = gateway._decode_cbor(wire)
        finally:
            gateway.zmeta_cbor = original
        blob = decoded["payload"]["extensions"]["vendor"]
        self.assertIs(blob, blob["self"], "no cycle -- reachability changed")


if __name__ == "__main__":
    unittest.main()
