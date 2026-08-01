"""Pins the plain-`cbor` envelope to the canonical value model (H1-07).

docs/zmeta_doctrine_review_log.md, Cycle H1: the fail-closed clause of
spec/compact-binary-mapping.md ("Value Model, Tags, and Expansion Bound")
was enforced at the COMPACT decode seam, while the gateway's plain-`cbor`
(non-compact) envelope fell back to bare `cbor2.loads` on cbor2-only
installs. Pre-fix, one datagram meant two different things one envelope
over from the one the clause closed:

  * a value-shared (tags 28/29) datagram was refused at parse on a
    zmeta_cbor install and ACCEPTED -- as a shared/cyclic structure -- on a
    cbor2-only install;
  * a bignum-tagged (tag 2/3) datagram was refused on zmeta_cbor and
    accepted as an out-of-64-bit-range integer on cbor2-only;
  * an 80-deep datagram was refused on zmeta_cbor (max_depth 64) and
    accepted on cbor2-only (cbor2's own limit is 400 -- and on the
    C-extension builds deployed installs use, wire recursion beyond it is a
    crash, not a catchable error);
  * a NaN-bearing datagram passed DECODE on both backends (zmeta_cbor
    refuses tags, not non-finite floats), leaking the refusal decision to a
    later layer on one envelope and keeping it at decode on the other.

These tests assert the fixed seam: gateway._decode_message(wire, "cbor")
refuses all four on BOTH supported installs (zmeta_cbor present, and the
cbor2-only install simulated by monkeypatching gateway.zmeta_cbor to None),
a clean canonical event still decodes on both, and a refusal is LOUD --
surfaced as a counted SCHEMA_INVALID diagnostic, never a silent drop.
"""

import importlib.util
import unittest
from pathlib import Path

try:
    import cbor2
except ImportError:  # pragma: no cover - optional dependency
    cbor2 = None


ROOT = Path(__file__).resolve().parents[2]

_spec_gw = importlib.util.spec_from_file_location(
    "zmeta_gateway_cbor_envelope", ROOT / "gateway" / "src" / "gateway.py"
)
gateway = importlib.util.module_from_spec(_spec_gw)
_spec_gw.loader.exec_module(gateway)


def _clean_event():
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
        "payload": {"state": "ACTIVE", "geo": {"lat": 34.05, "lon": -117.2}},
    }


def _shared_wire():
    # Value sharing (tags 28/29): a tiny datagram describing a cyclic event.
    vendor = {}
    vendor["self"] = vendor
    event = {
        "event": {"event_id": "x"},
        "source": {},
        "payload": {"extensions": {"vendor": vendor}},
    }
    return cbor2.dumps(event, value_sharing=True)


def _bignum_wire():
    # cbor2 encodes an integer past the 64-bit range as bignum tag 2.
    return cbor2.dumps({"event": {}, "source": {}, "payload": {"x": 2**70}})


def _deep_wire(n):
    # n nested one-element arrays around the integer 1, built as raw bytes
    # so no encoder's own recursion limit shapes the test input.
    return b"\x81" * n + b"\x01"


class _RecordingMetrics:
    def __init__(self):
        self.violations = []

    def record_violation(self, code, event_id=None, producer=None, details=None):
        self.violations.append(code)


class _Cbor2OnlyInstall:
    """Simulate the supported cbor2-only install (zmeta_cbor absent)."""

    def __enter__(self):
        self._original = gateway.zmeta_cbor
        gateway.zmeta_cbor = None
        return self

    def __exit__(self, *exc_info):
        gateway.zmeta_cbor = self._original
        return False


@unittest.skipIf(cbor2 is None, "cbor2 not installed")
class PlainCborEnvelopeValueModelTest(unittest.TestCase):
    def setUp(self):
        # These pins are about the two supported installs; the dev
        # environment must actually have both modules for the comparison
        # to mean anything.
        self.assertIsNotNone(gateway.zmeta_cbor, "zmeta_cbor missing from repo")
        self.assertIsNotNone(gateway.zmeta_compact, "zmeta_compact missing from repo")

    def _decode(self, wire):
        return gateway._decode_message(wire, "cbor")

    # -- refusals, per hostile shape, per backend ------------------------

    def test_value_sharing_refused_on_zmeta_cbor_install(self):
        with self.assertRaises(ValueError) as ctx:
            self._decode(_shared_wire())
        self.assertIn("unsupported CBOR tag 28", str(ctx.exception))

    def test_value_sharing_refused_on_cbor2_only_install(self):
        # RED pre-fix: bare cbor2.loads ACCEPTED this datagram and returned
        # a cyclic dict -- the H1-07 divergence.
        with _Cbor2OnlyInstall():
            with self.assertRaises(Exception) as ctx:
                self._decode(_shared_wire())
        self.assertIn("value sharing (CBOR tags 28/29)", str(ctx.exception))

    def test_bignum_refused_on_zmeta_cbor_install(self):
        with self.assertRaises(ValueError) as ctx:
            self._decode(_bignum_wire())
        self.assertIn("unsupported CBOR tag 2", str(ctx.exception))

    def test_bignum_refused_on_cbor2_only_install(self):
        # RED pre-fix: accepted as the integer 2**70 under a fabricated
        # clean decode.
        with _Cbor2OnlyInstall():
            with self.assertRaises(Exception) as ctx:
                self._decode(_bignum_wire())
        self.assertIn("outside the CBOR 64-bit range", str(ctx.exception))

    def test_over_deep_refused_on_zmeta_cbor_install(self):
        for depth in (80, 2000):
            with self.subTest(depth=depth):
                with self.assertRaises(ValueError) as ctx:
                    self._decode(_deep_wire(depth))
                self.assertIn("nesting", str(ctx.exception))

    def test_over_deep_refused_on_cbor2_only_install(self):
        # RED pre-fix: depth 80 decoded fine on cbor2-only (cbor2's own
        # limit is 400), so representability depended on the local install.
        # The refusal must fire at PARSE, before the C extension of a
        # deployed cbor2 build can recurse on wire nesting: the installed
        # cbor2 exposes max_depth, and the gateway must pass the mapping's
        # declared bound (COMPACT_MAX_DEPTH) to it.
        for depth in (80, 2000):
            with self.subTest(depth=depth):
                with _Cbor2OnlyInstall():
                    with self.assertRaises(Exception) as ctx:
                        self._decode(_deep_wire(depth))
                self.assertIn("nesting", str(ctx.exception))

    def test_depth_boundary_is_identical_on_both_backends(self):
        # Exactly 64 nested arrays decodes everywhere; 65 refuses
        # everywhere. Anything else re-opens install-dependent meaning at
        # the boundary.
        ok, over = _deep_wire(64), _deep_wire(65)
        decoded = self._decode(ok)
        with _Cbor2OnlyInstall():
            self.assertEqual(decoded, self._decode(ok))
        with self.assertRaises(Exception):
            self._decode(over)
        with _Cbor2OnlyInstall():
            with self.assertRaises(Exception):
                self._decode(over)

    def test_non_finite_refused_at_decode_on_both_backends(self):
        # zmeta_cbor refuses tags at parse but carries NaN natively, so the
        # value-model scan must run on the DECODED object on both backends,
        # not only on the cbor2 fallback. RED pre-fix on both installs: the
        # decode seam returned the NaN-bearing dict and left the refusal to
        # a later layer.
        wire = cbor2.dumps(
            {"event": {}, "source": {}, "payload": {"x": float("nan")}}
        )
        with self.assertRaises(Exception) as ctx:
            self._decode(wire)
        self.assertIn("non-finite float", str(ctx.exception))
        with _Cbor2OnlyInstall():
            with self.assertRaises(Exception) as ctx:
                self._decode(wire)
        self.assertIn("non-finite float", str(ctx.exception))

    # -- the refusal is loud, not a silent drop --------------------------

    def test_refusal_surfaces_as_counted_schema_invalid_diagnostic(self):
        # Same surfacing as a compact-envelope refusal: one SCHEMA_INVALID
        # SYSTEM_EVENT diagnostic, and the violation is counted.
        for label, wire in (
            ("shared", _shared_wire()),
            ("bignum", _bignum_wire()),
            ("deep", _deep_wire(80)),
        ):
            with self.subTest(case=label):
                metrics = _RecordingMetrics()
                with _Cbor2OnlyInstall():
                    out = gateway.process_message(
                        wire, None, None, "L", {}, "cbor", metrics=metrics
                    )
                self.assertEqual(1, len(out))
                diagnostic = out[0]
                self.assertEqual(
                    "SYSTEM_EVENT", diagnostic["event"]["event_type"]
                )
                self.assertEqual(
                    "SCHEMA_VIOLATION", diagnostic["event"]["event_subtype"]
                )
                self.assertEqual("REJECTED", diagnostic["payload"]["state"])
                self.assertEqual(
                    "SCHEMA_INVALID",
                    diagnostic["payload"]["metrics"]["reason_code"],
                )
                self.assertEqual(["SCHEMA_INVALID"], metrics.violations)

    # -- nothing honest is refused ----------------------------------------

    def test_clean_canonical_event_decodes_on_both_backends(self):
        event = _clean_event()
        wire = cbor2.dumps(event, canonical=True)
        self.assertEqual(event, self._decode(wire))
        with _Cbor2OnlyInstall():
            self.assertEqual(event, self._decode(wire))

    # -- the degenerate install fails closed ------------------------------

    def test_bare_cbor2_install_without_scanner_refuses_loudly(self):
        # zmeta_cbor absent AND zmeta_compact absent: no parse-time tag
        # refusal and no value-model scan exist on this install, so plain
        # cbor ingress must refuse rather than silently interpret tags --
        # even for a clean datagram, because nothing can tell it from a
        # tagged one honestly. The refusal names why.
        wire = cbor2.dumps(_clean_event(), canonical=True)
        original_compact = gateway.zmeta_compact
        try:
            gateway.zmeta_compact = None
            with _Cbor2OnlyInstall():
                with self.assertRaises(Exception) as ctx:
                    self._decode(wire)
        finally:
            gateway.zmeta_compact = original_compact
        message = str(ctx.exception)
        self.assertIn("cbor ingress refused", message)
        self.assertIn("Value Model, Tags, and Expansion Bound", message)


if __name__ == "__main__":
    unittest.main()
