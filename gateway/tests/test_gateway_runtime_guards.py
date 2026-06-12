"""Runtime resource-guard tests for the reference gateway.

Covers non-semantic runtime safeguards:
- ProducerRateLimiter memory bounds (stale per-producer windows are evicted).
- Oversize-datagram warning metrics on the UDP send path.

These guards must not change accept/reject semantics; the rate-limit
decisions and forwarding behavior are asserted unchanged.
"""

import importlib.util
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


if __name__ == "__main__":
    unittest.main()
