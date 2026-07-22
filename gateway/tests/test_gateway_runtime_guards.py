"""Runtime resource-guard tests for the reference gateway.

Covers non-semantic runtime safeguards:
- ProducerRateLimiter memory bounds (stale per-producer windows are evicted).
- Oversize-datagram warning metrics on the UDP send path.
- Send-failure containment: an OSError from sendto (for example a >65507-byte
  UDP payload) drops that datagram with an explicit diagnostic instead of
  crashing the gateway main loop.

These guards must not change accept/reject semantics; the rate-limit
decisions and forwarding behavior are asserted unchanged.
"""

import importlib.util
import socket
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
GATEWAY_PATH = ROOT / "gateway" / "src" / "gateway.py"
spec_gw = importlib.util.spec_from_file_location("zmeta_gateway_guards", GATEWAY_PATH)
gateway = importlib.util.module_from_spec(spec_gw)
spec_gw.loader.exec_module(gateway)


class _ListLogger:
    def __init__(self):
        self.records = []

    def write(self, record):
        self.records.append(record)


class ProducerRateLimiterTest(unittest.TestCase):
    def test_rate_decisions_preserved_within_and_across_windows(self):
        limiter = gateway.ProducerRateLimiter(2)
        with mock.patch.object(gateway.time, "monotonic", return_value=100.0):
            self.assertTrue(limiter.allow("alpha"))
            self.assertTrue(limiter.allow("alpha"))
            self.assertFalse(limiter.allow("alpha"))
            # Independent producer budget in the same window.
            self.assertTrue(limiter.allow("bravo"))
            # None producer maps to the UNKNOWN bucket.
            self.assertTrue(limiter.allow(None))
            self.assertTrue(limiter.allow(None))
            self.assertFalse(limiter.allow(None))
        with mock.patch.object(gateway.time, "monotonic", return_value=101.0):
            # New one-second window resets every producer budget.
            self.assertTrue(limiter.allow("alpha"))
            self.assertTrue(limiter.allow("bravo"))

    def test_zero_limit_disables_rate_limiting(self):
        limiter = gateway.ProducerRateLimiter(0)
        with mock.patch.object(gateway.time, "monotonic", return_value=100.0):
            for _ in range(100):
                self.assertTrue(limiter.allow("alpha"))

    def test_stale_producer_windows_are_evicted(self):
        limiter = gateway.ProducerRateLimiter(5)
        with mock.patch.object(gateway.time, "monotonic", return_value=100.0):
            for idx in range(50):
                self.assertTrue(limiter.allow(f"producer-{idx}"))
            self.assertEqual(50, len(limiter.counters))
        with mock.patch.object(gateway.time, "monotonic", return_value=101.0):
            self.assertTrue(limiter.allow("producer-new"))
            # Entries from the previous window can never affect another
            # decision; they must not accumulate forever.
            self.assertEqual(1, len(limiter.counters))
            self.assertIn("producer-new", limiter.counters)


class OversizeDatagramWarningTest(unittest.TestCase):
    def test_metrics_record_oversize_datagram(self):
        logger = _ListLogger()
        metrics = gateway.GatewayMetrics(interval_sec=30, emit=False, logger=logger)

        metrics.record_oversize_datagram(2048, 1400, "forward", event_id="evt-1", producer="prod-1")

        self.assertEqual(1, metrics.window["oversize_datagrams"])
        self.assertEqual({"forward": 1}, metrics.window["oversize_datagram_kinds"])
        record = logger.records[-1]
        self.assertEqual("oversize_datagram", record["type"])
        self.assertEqual(2048, record["size_bytes"])
        self.assertEqual(1400, record["threshold_bytes"])
        self.assertEqual("forward", record["kind"])
        self.assertEqual("evt-1", record["event_id"])
        self.assertEqual("prod-1", record["producer"])

    def test_check_datagram_size_thresholds(self):
        metrics = gateway.GatewayMetrics(interval_sec=30, emit=False)

        # Disabled threshold (0/None) never warns.
        self.assertFalse(gateway._check_datagram_size(metrics, 70000, 0, "forward"))
        self.assertFalse(gateway._check_datagram_size(metrics, 70000, None, "forward"))
        # At or below the threshold does not warn.
        self.assertFalse(gateway._check_datagram_size(metrics, 1400, 1400, "forward"))
        self.assertEqual(0, metrics.window["oversize_datagrams"])
        # Above the threshold warns and records the kind.
        self.assertTrue(gateway._check_datagram_size(metrics, 1401, 1400, "forward"))
        self.assertTrue(gateway._check_datagram_size(metrics, 9000, 1400, "cot"))
        self.assertEqual(2, metrics.window["oversize_datagrams"])
        self.assertEqual(
            {"forward": 1, "cot": 1}, metrics.window["oversize_datagram_kinds"]
        )
        # Missing metrics object is a no-op, not an error.
        self.assertFalse(gateway._check_datagram_size(None, 9000, 1400, "forward"))

    def test_warn_datagram_bytes_setting_default_config_and_cli(self):
        with mock.patch("sys.argv", ["gateway.py", "--profile", "H"]):
            args = gateway.parse_args()
        settings = gateway.build_settings(ROOT, args, {})
        # Default: disabled (no behavior or log change unless configured).
        self.assertEqual(0, settings["warn_datagram_bytes"])

        settings = gateway.build_settings(ROOT, args, {"warn_datagram_bytes": 1400})
        self.assertEqual(1400, settings["warn_datagram_bytes"])

        with mock.patch(
            "sys.argv",
            ["gateway.py", "--profile", "H", "--warn-datagram-bytes", "900"],
        ):
            args = gateway.parse_args()
        settings = gateway.build_settings(ROOT, args, {"warn_datagram_bytes": 1400})
        # CLI overrides config.
        self.assertEqual(900, settings["warn_datagram_bytes"])


class _FakeSocket:
    def __init__(self, error=None):
        self.error = error
        self.sent = []

    def sendto(self, payload, addr):
        if self.error is not None:
            raise self.error
        self.sent.append((payload, addr))
        return len(payload)


class SendFailureGuardTest(unittest.TestCase):
    def test_send_datagram_success_returns_true_and_sends(self):
        sock = _FakeSocket()
        metrics = gateway.GatewayMetrics(interval_sec=30, emit=False)

        sent = gateway._send_datagram(
            sock, b"payload", ("127.0.0.1", 5556), metrics=metrics, kind="forward"
        )

        self.assertTrue(sent)
        self.assertEqual([(b"payload", ("127.0.0.1", 5556))], sock.sent)
        self.assertEqual(0, metrics.window["send_failures"])

    def test_send_datagram_oserror_is_dropped_and_recorded(self):
        sock = _FakeSocket(error=OSError("message too long"))
        logger = _ListLogger()
        metrics = gateway.GatewayMetrics(interval_sec=30, emit=False, logger=logger)

        sent = gateway._send_datagram(
            sock,
            b"x" * 70000,
            ("127.0.0.1", 5556),
            metrics=metrics,
            kind="cot",
            event_id="evt-1",
            producer="prod-1",
        )

        self.assertFalse(sent)
        self.assertEqual(1, metrics.window["send_failures"])
        self.assertEqual({"cot": 1}, metrics.window["send_failure_kinds"])
        record = logger.records[-1]
        self.assertEqual("send_failure", record["type"])
        self.assertEqual("cot", record["kind"])
        self.assertEqual(70000, record["size_bytes"])
        self.assertEqual("evt-1", record["event_id"])
        self.assertEqual("prod-1", record["producer"])

    def test_send_datagram_survives_real_oversize_udp_payload(self):
        # A real UDP socket refuses datagrams above the ~65507-byte limit with
        # an OSError. The guard must contain it; before this guard the gateway
        # main loop crashed here.
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            metrics = gateway.GatewayMetrics(interval_sec=30, emit=False)
            sent = gateway._send_datagram(
                sock,
                b"x" * 70000,
                ("127.0.0.1", 5556),
                metrics=metrics,
                kind="forward",
            )

            self.assertFalse(sent)
            self.assertEqual(1, metrics.window["send_failures"])
            self.assertEqual({"forward": 1}, metrics.window["send_failure_kinds"])
        finally:
            sock.close()

    def test_send_datagram_without_metrics_does_not_raise(self):
        sock = _FakeSocket(error=OSError("message too long"))

        sent = gateway._send_datagram(sock, b"x" * 70000, ("127.0.0.1", 5556), metrics=None)

        self.assertFalse(sent)


class ReceiveLoopBackstopScopeTest(unittest.TestCase):
    """The last-resort per-datagram guard must be scoped so that resilience
    never becomes concealment (R1-11 verification pass 2): a hostile datagram
    is survivable, but a dead listener or a configuration failure must still
    stop the process instead of becoming an infinite drop loop."""

    def _loop_source(self):
        import inspect
        import textwrap

        return textwrap.dedent(inspect.getsource(gateway.main))

    def test_recvfrom_is_outside_the_backstop(self):
        source = self._loop_source()
        recv_at = source.index("sock_in.recvfrom")
        try_at = source.index("try:", source.index("# Receive-loop backstop"))
        self.assertLess(
            recv_at,
            try_at,
            "recvfrom moved inside the backstop: a dead listener socket would "
            "hot-loop forever instead of terminating",
        )

    def test_backstop_catches_exception_not_baseexception(self):
        source = self._loop_source()
        tail = source[source.index("# Receive-loop backstop"):]
        self.assertIn("except Exception as exc:", tail)
        self.assertNotIn("except BaseException", tail)

    def test_interrupts_and_config_failures_still_propagate(self):
        # SystemExit is how _require_cbor/_require_compact/_require_proto
        # report an unusable configuration; it must not be swallowed.
        for exc in (KeyboardInterrupt, SystemExit):
            with self.subTest(exc=exc.__name__):
                with self.assertRaises(exc):
                    try:
                        raise exc("propagates")
                    except Exception:  # noqa: BLE001 - mirrors the backstop
                        self.fail(f"{exc.__name__} was swallowed by the backstop")


class DropReasonVocabularyTest(unittest.TestCase):
    """drop_reasons keys are the operator-facing filter surface, so they must
    share one spelling convention. A lone lowercase reason hides that bucket
    from a SCREAMING_SNAKE filter (R1-11 verification pass 2)."""

    def test_every_record_drop_reason_is_screaming_snake(self):
        import re

        source = (ROOT / "gateway" / "src" / "gateway.py").read_text(encoding="utf-8")
        reasons = re.findall(r'record_drop\(\s*"([^"]+)"', source)
        self.assertGreaterEqual(len(reasons), 4, "record_drop call sites vanished")
        for reason in reasons:
            with self.subTest(reason=reason):
                self.assertRegex(reason, r"^[A-Z][A-Z0-9_]*$")


VALIDATORS_PATH = ROOT / "gateway" / "src" / "validators.py"
spec_val = importlib.util.spec_from_file_location("zmeta_validators_guards", VALIDATORS_PATH)
validators = importlib.util.module_from_spec(spec_val)
spec_val.loader.exec_module(validators)


class ForbiddenKeyTraversalGuardTest(unittest.TestCase):
    """The denylist walk must not tie the process stack to sender-controlled
    nesting depth: a deeply nested but schema-valid payload killed the gateway
    with RecursionError at ingress (R1-11 verification pass 2)."""

    def test_traversal_survives_hostile_nesting_depth(self):
        deep = current = {}
        for _ in range(100_000):
            child = {}
            current["d"] = child
            current = child
        # No forbidden key anywhere: the full structure must be walked.
        self.assertIsNone(validators._find_forbidden_key(deep, {"features"}))
        # A forbidden key at the bottom of the hostile structure is found.
        current["features"] = 1
        found = validators._find_forbidden_key(deep, {"features"})
        self.assertIsNotNone(found)
        self.assertEqual("features", found[0])

    def test_traversal_reports_shallowest_match_with_path(self):
        value = {
            "a": {"b": [{"raw_features": 1}]},
            "features": 2,
        }
        found = validators._find_forbidden_key(value, {"features", "raw_features"})
        self.assertEqual(("features", ["features"]), found)
        nested_only = {"a": {"b": [{"raw_features": 1}]}}
        found = validators._find_forbidden_key(nested_only, {"features", "raw_features"})
        self.assertEqual(("raw_features", ["a", "b", "0", "raw_features"]), found)


if __name__ == "__main__":
    unittest.main()
