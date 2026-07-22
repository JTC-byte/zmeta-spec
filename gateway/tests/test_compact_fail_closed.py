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
        deep = current = {}
        for _ in range(300):
            child = {}
            current["d"] = child
            current = child
        event = self._v1_0_state()
        event.setdefault("payload", {}).setdefault("extensions", {})["vendor"] = deep
        with self.assertRaises(zmeta_compact.CompactUnrepresentableError):
            zmeta_compact.dumps(event)

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


if __name__ == "__main__":
    unittest.main()
