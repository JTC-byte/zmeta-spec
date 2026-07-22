"""Runtime resource-guard tests for the reference gateway.

Covers non-semantic runtime safeguards:
- ProducerRateLimiter memory bounds (stale per-producer windows are evicted).
- Oversize-datagram warning metrics on the UDP send path.
- Send-failure containment: an OSError from sendto (for example a >65507-byte
  UDP payload) drops that datagram with an explicit diagnostic instead of
  crashing the gateway main loop.
- Metrics-sink containment (A-03): a failing observability sink degrades in
  place instead of raising into the datagram path, including from inside the
  receive-loop backstop's own handler.

These guards must not change accept/reject semantics; the rate-limit
decisions and forwarding behavior are asserted unchanged.
"""

import contextlib
import importlib.util
import inspect
import io
import json
import socket
import sys
import tempfile
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

    def test_backstop_handler_does_not_re_enter_the_metrics_sink(self):
        # A-03: the handler called metrics.record_drop/maybe_log directly. When
        # the metrics sink was what failed inside the try, the identical
        # exception was raised from inside the except and killed the gateway.
        # The handler must delegate to the guarded helper instead.
        source = self._loop_source()
        handler = source[source.index("except Exception as exc:"):]
        self.assertIn("_record_backstop_drop(metrics, exc)", handler)
        self.assertNotIn("metrics.record_drop(", handler)
        self.assertNotIn("metrics.maybe_log(", handler)


class _BrokenStream(io.TextIOBase):
    """A stream whose every write fails, like a closed pipe or a full disk."""

    def write(self, _text):
        raise OSError("stream is gone")


class _RaisingLogger:
    """A sink that does NOT degrade in place - an operator-supplied logger or a
    third-party handler. The backstop handler must survive it too."""

    def write(self, _record):
        raise RuntimeError("hostile sink")


class MetricsSinkDegradationTest(unittest.TestCase):
    """A-03: the observability sink must never raise into the datagram path.

    Every metrics call sits on that path - including the receive-loop
    backstop's own except handler and the rate-limit drop, which is OUTSIDE the
    backstop entirely. An unguarded raise from the sink meant one datagram
    terminated the gateway for every producer behind it, at exactly the moment
    an edge node is already under stress (disk full, read-only remount, log
    directory removed). Degrading is not laundering: no event is altered, the
    in-memory counters stay honest, and the failure is announced.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        # Parent of the log path is a regular FILE, so mkdir raises. This is
        # the cheapest faithful stand-in for the real causes (ENOSPC, EROFS,
        # EACCES, a removed directory), which all fail inside the same write.
        blocker = self.tmp / "logs"
        blocker.write_text("not a directory", encoding="utf-8")
        self.dead_path = blocker / "metrics.jsonl"

    def _dead_logger(self):
        return gateway.MetricsLogger(self.dead_path)

    def test_metrics_logger_write_degrades_and_warns_exactly_once(self):
        logger = self._dead_logger()
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            for _ in range(5):
                # Must not raise: this is the call that killed the gateway.
                self.assertIsNone(logger.write({"type": "drop", "reason": "X"}))
        # Degradation is counted, not silent.
        self.assertEqual(5, logger.write_failures)
        warnings = [line for line in err.getvalue().splitlines() if "metrics log sink" in line]
        self.assertEqual(
            1,
            len(warnings),
            "one warning per datagram is its own outage on a full disk",
        )
        self.assertIn("FileExistsError", warnings[0] + err.getvalue())
        self.assertIn(str(self.dead_path), warnings[0])

    def test_metrics_logger_write_survives_an_unserializable_record(self):
        # Not every sink failure is I/O: event_id/producer are copied from the
        # wire, and a CBOR producer can put bytes there, which json.dumps
        # refuses with TypeError from inside the same write.
        path = self.tmp / "ok" / "metrics.jsonl"
        logger = gateway.MetricsLogger(path)
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            self.assertIsNone(logger.write({"type": "drop", "event_id": b"\x00\x01"}))
            # A healthy record after the failure still lands: the sink degraded
            # for that record, it did not shut itself off.
            logger.write({"type": "drop", "reason": "INTERNAL_ERROR"})
        self.assertEqual(1, logger.write_failures)
        lines = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        # The healthy record still lands - the sink degraded for that record,
        # it did not shut itself off - and the record it lost is marked in
        # band, so a consumer reads the discontinuity instead of seeing two
        # records that look contiguous.
        marker, landed = lines
        self.assertEqual("metrics_sink_gap", marker["type"])
        self.assertEqual(1, marker["lost_records"])
        self.assertIn("TypeError", marker["first_error"])
        self.assertEqual({"type": "drop", "reason": "INTERNAL_ERROR"}, landed)

    def test_every_metrics_entry_point_survives_a_dead_sink(self):
        """The whole family, enumerated from the class rather than by hand.

        A-03 named record_drop, but every record_* method reaches the same
        _log_event -> logger.write, and a method added later inherits the same
        exposure. Enumerating by introspection means a new sibling is covered
        the day it is written instead of the day someone remembers it.
        """
        names = sorted(
            name
            for name in dir(gateway.GatewayMetrics)
            if name.startswith("record_") or name == "maybe_log"
        )
        # Guard the guard: if the family is ever renamed away, this test must
        # not quietly become an assertion about nothing.
        self.assertGreaterEqual(len(names), 9, "the record_* family vanished")
        self.assertIn("record_drop", names)
        self.assertIn("maybe_log", names)

        for name in names:
            with self.subTest(method=name):
                metrics = gateway.GatewayMetrics(
                    interval_sec=1, emit=True, logger=self._dead_logger()
                )
                metrics.last_log -= 3600  # force maybe_log past its interval
                method = getattr(metrics, name)
                params = [
                    param
                    for param in inspect.signature(method).parameters.values()
                    if param.default is inspect.Parameter.empty
                    and param.kind
                    in (param.POSITIONAL_ONLY, param.POSITIONAL_OR_KEYWORD)
                ]
                out, err = io.StringIO(), io.StringIO()
                with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                    method(*[1 for _ in params])

    def test_metrics_console_sink_degrades_and_warns_exactly_once(self):
        # stdout is the second sink on the datagram path: a closed pipe (the
        # gateway piped into a consumer that exited) raises from print().
        metrics = gateway.GatewayMetrics(interval_sec=1, emit=True)
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            for _ in range(3):
                metrics.last_log -= 3600
                with contextlib.redirect_stdout(_BrokenStream()):
                    metrics.maybe_log()
        self.assertGreaterEqual(metrics.console_failures, 3)
        warnings = [
            line for line in err.getvalue().splitlines() if "metrics console sink" in line
        ]
        self.assertEqual(1, len(warnings))

    def test_backstop_helper_never_raises_and_still_names_the_failure(self):
        cases = {
            "no metrics": None,
            "dead file sink": gateway.GatewayMetrics(
                interval_sec=1, emit=False, logger=self._dead_logger()
            ),
            "sink that does not degrade": gateway.GatewayMetrics(
                interval_sec=1, emit=False, logger=_RaisingLogger()
            ),
        }
        for label, metrics in cases.items():
            with self.subTest(case=label):
                err = io.StringIO()
                with contextlib.redirect_stderr(err):
                    gateway._record_backstop_drop(metrics, ValueError("boom"))
                # Degrading is not swallowing: the operator still gets the line.
                self.assertIn("datagram dropped after unexpected", err.getvalue())
                self.assertIn("ValueError: boom", err.getvalue())
                if metrics is not None:
                    # The in-memory bucket an operator filters on stays honest
                    # even when no sink survives to write it down.
                    self.assertEqual(1, metrics.window["drops"])
                    self.assertEqual(
                        {"INTERNAL_ERROR": 1}, metrics.window["drop_reasons"]
                    )

    def test_backstop_helper_does_not_swallow_interrupts_from_the_sink(self):
        # The new guard is itself unreviewed code: widening its except to
        # BaseException would turn an operator interrupt or a SystemExit
        # configuration failure raised by a sink into a per-datagram no-op,
        # which is the concealment the backstop's scope tests exist to prevent.
        for exc in (KeyboardInterrupt, SystemExit):
            with self.subTest(exc=exc.__name__):

                class _Interrupting:
                    def record_drop(self, _reason, **_kwargs):
                        raise exc("propagates")

                with contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(exc):
                        gateway._record_backstop_drop(_Interrupting(), ValueError("x"))

    def test_backstop_helper_survives_an_exception_that_cannot_describe_itself(self):
        # The warning string is built inside a handler that is not itself
        # inside a try, so a raising __str__ escapes by exactly the route the
        # metrics sink used to. The report degrades to the type name; it does
        # not vanish and it does not become a second failure.
        class _Unprintable(Exception):
            def __str__(self):
                raise RuntimeError("cannot render")

        metrics = gateway.GatewayMetrics(
            interval_sec=1, emit=False, logger=self._dead_logger()
        )
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            gateway._record_backstop_drop(metrics, _Unprintable())
        self.assertIn("datagram dropped after unexpected _Unprintable", err.getvalue())
        self.assertEqual(1, metrics.window["drops"])

    def test_backstop_helper_survives_a_broken_stderr(self):
        metrics = gateway.GatewayMetrics(
            interval_sec=1, emit=False, logger=self._dead_logger()
        )
        with contextlib.redirect_stderr(_BrokenStream()):
            gateway._record_backstop_drop(metrics, ValueError("boom"))
        self.assertEqual(1, metrics.window["drops"])


class _FlushFailsStream(io.TextIOBase):
    """Accepts writes and fails at flush - a buffered pipe or a full disk.

    print() buffers, so this is how ENOSPC and EPIPE frequently surface. A
    warning that was only queued is not a warning that was delivered.
    """

    def __init__(self):
        super().__init__()
        self._live = True

    def write(self, text):
        return len(text)

    def flush(self):
        if self._live:
            raise OSError("stream is gone")

    def close(self):
        # Finalization flushes; a raise from there is the test harness's
        # problem, not the property under test.
        self._live = False
        super().close()


class MetricsSinkWarningDeliveryTest(unittest.TestCase):
    """The one-shot sink warning must be spent on DELIVERY, not on attempt.

    Both sinks announce their degradation once, because a per-datagram warning
    storm on a full disk is its own outage. That is only honest if the one
    warning is one the operator RECEIVED. Latching on the attempt spent it on
    an undelivered line, and the coincidence is the correlated case rather than
    an exotic one: full disk and closed pipe are the documented primary causes
    and they take stderr down together with the sink. The measured result was
    write_failures=1001 with zero warnings ever delivered, for the whole run,
    even after stderr came back.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        blocker = self.tmp / "logs"
        blocker.write_text("not a directory", encoding="utf-8")
        self.dead_path = blocker / "metrics.jsonl"

    def test_log_sink_warning_survives_a_stderr_that_was_down_at_first_failure(self):
        logger = gateway.MetricsLogger(self.dead_path)
        # The correlated case: the very first sink failure lands while stderr
        # is unusable too.
        with contextlib.redirect_stderr(_BrokenStream()):
            logger.write({"type": "drop", "reason": "X"})
        self.assertEqual(1, logger.write_failures)
        # stderr recovers; the sink is still dead.
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            for _ in range(50):
                logger.write({"type": "drop", "reason": "X"})
        warnings = [
            line for line in err.getvalue().splitlines() if "metrics log sink" in line
        ]
        self.assertEqual(
            1,
            len(warnings),
            "the operator must get exactly one warning: not zero because the "
            "latch was spent undelivered, and not one per datagram",
        )
        self.assertEqual(51, logger.write_failures)

    def test_console_sink_warning_survives_a_stderr_that_was_down_at_first_failure(self):
        metrics = gateway.GatewayMetrics(interval_sec=1, emit=True)
        with contextlib.redirect_stderr(_BrokenStream()):
            metrics.last_log -= 3600
            with contextlib.redirect_stdout(_BrokenStream()):
                metrics.maybe_log()
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            for _ in range(5):
                metrics.last_log -= 3600
                with contextlib.redirect_stdout(_BrokenStream()):
                    metrics.maybe_log()
        warnings = [
            line
            for line in err.getvalue().splitlines()
            if "metrics console sink" in line
        ]
        self.assertEqual(1, len(warnings))

    def test_a_queued_warning_is_not_a_delivered_warning(self):
        # print() buffers. A stderr that accepts the write and fails at flush
        # delivered nothing, so the latch must not be spent on it.
        logger = gateway.MetricsLogger(self.dead_path)
        with contextlib.redirect_stderr(_FlushFailsStream()):
            logger.write({"type": "drop", "reason": "X"})
        self.assertFalse(
            logger._warned, "a warning that only reached the buffer was not delivered"
        )
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            logger.write({"type": "drop", "reason": "X"})
        self.assertIn("metrics log sink", err.getvalue())

    def test_warn_stderr_never_diverts_the_warning_onto_stdout(self):
        # print(file=None) falls back to sys.stdout, and stdout here is the
        # machine-readable metrics channel. Corrupting the machine channel to
        # report a failure on the human channel is the wrong direction, and
        # returning True for it makes every caller latch on a lie.
        out = io.StringIO()
        saved = sys.stderr
        try:
            sys.stderr = None
            with contextlib.redirect_stdout(out):
                delivered = gateway._warn_stderr("WARNING: probe")
        finally:
            sys.stderr = saved
        self.assertFalse(delivered)
        self.assertEqual("", out.getvalue())

    def test_no_latched_sink_warning_is_set_without_consulting_delivery(self):
        """Class guard: the latch assignment must read _warn_stderr's result.

        Named-exemplar pins go stale the moment a third latched sink is added.
        Every `self._X_warned = True` in the module is by construction a latch
        spent without asking whether anything was delivered.
        """
        source = GATEWAY_PATH.read_text(encoding="utf-8")
        offenders = [
            line.strip()
            for line in source.splitlines()
            if line.strip().startswith("self._")
            and "_warned" in line
            and line.strip().endswith("= True")
        ]
        self.assertEqual([], offenders)
        # Guard the guard: the latches still exist and are still assigned from
        # the delivery result, so this is not an assertion about nothing.
        latched = [
            line.strip()
            for line in source.splitlines()
            if "_warned = _warn_stderr(" in line
        ]
        self.assertEqual(2, len(latched), "the latched-sink family changed shape")


class MetricsSinkObservabilityTest(unittest.TestCase):
    """A counter the operator is told to consult must have an output surface.

    The one-shot warnings name write_failures and console_failures. Before this
    guard, both were assigned in gateway.py and read nowhere but tests: absent
    from the periodic summary, from the metrics record, and from every doc. A
    consumer reading metrics.jsonl across a 200-record outage saw four
    contiguous records and a summary that said 204 - the observability layer
    degraded silently, which is the honesty class the sink guard exists for,
    inverted.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.path = self.tmp / "ok" / "metrics.jsonl"

    @staticmethod
    def _kill(logger):
        def _boom(_record):
            raise OSError("no space left on device")

        logger._write = _boom

    def _records(self):
        return [
            json.loads(line)
            for line in self.path.read_text(encoding="utf-8").splitlines()
        ]

    def test_lost_records_are_marked_in_band_when_the_sink_recovers(self):
        logger = gateway.MetricsLogger(self.path)
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            logger.write({"type": "violation", "code": "A"})
            healthy = logger._write
            self._kill(logger)
            for _ in range(200):
                logger.write({"type": "violation", "code": "A"})
            logger._write = healthy
            logger.write({"type": "violation", "code": "B"})
        records = self._records()
        kinds = [record["type"] for record in records]
        self.assertEqual(["violation", "metrics_sink_gap", "violation"], kinds)
        marker = records[1]
        # The marker must quantify and attribute, not merely exist: a consumer
        # has to be able to tell 200 lost from 2 lost, and why.
        self.assertEqual(200, marker["lost_records"])
        self.assertIn("OSError", marker["first_error"])
        self.assertEqual(str(self.path), marker["path"])
        self.assertEqual(200, logger.write_failures)
        # It precedes the record that follows the gap, so it can never be read
        # as an attribute of that record.
        self.assertEqual("B", records[2]["code"])

    def test_a_failed_gap_marker_does_not_lose_the_count_it_carries(self):
        # The marker is written through the same sink it reports on, so it can
        # fail too. If it did and the count reset, the recovery marker would
        # understate the loss - a marker that undercounts is worse than none,
        # because it reads as authoritative.
        logger = gateway.MetricsLogger(self.path)
        healthy = logger._write
        with contextlib.redirect_stderr(io.StringIO()):
            self._kill(logger)
            for _ in range(5):
                logger.write({"type": "violation", "code": "A"})

            attempts = {"n": 0}

            def _fail_the_marker_then_recover(record):
                attempts["n"] += 1
                if attempts["n"] == 1:
                    raise OSError("no space left on device")
                healthy(record)

            logger._write = _fail_the_marker_then_recover
            logger.write({"type": "violation", "code": "B"})  # marker attempt fails
            logger.write({"type": "violation", "code": "C"})  # sink is back
        records = self._records()
        self.assertEqual(["metrics_sink_gap", "violation"], [r["type"] for r in records])
        # 5 lost while dead + the record whose marker attempt failed.
        self.assertEqual(6, records[0]["lost_records"])
        self.assertEqual(6, logger.write_failures)
        self.assertIn("OSError", records[0]["first_error"])

    def test_reading_the_counter_off_a_hostile_logger_is_not_an_outage(self):
        # The new surface reads write_failures off the logger, and the logger
        # can be operator-supplied. maybe_log sits on the datagram path,
        # including inside the backstop's own handler, so a property that
        # raises must degrade here exactly like every other sink failure.
        class _HostileCounter:
            def write(self, _record):
                return None

            @property
            def write_failures(self):
                raise RuntimeError("hostile counter")

        metrics = gateway.GatewayMetrics(
            interval_sec=1, emit=True, logger=_HostileCounter()
        )
        metrics.last_log -= 3600
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            metrics.maybe_log()  # must not raise
        self.assertIn("metrics interval=", out.getvalue())

    def test_sink_failure_counters_reach_both_operator_surfaces(self):
        logger = gateway.MetricsLogger(self.path)
        metrics = gateway.GatewayMetrics(interval_sec=1, emit=True, logger=logger)
        healthy = logger._write
        err, out = io.StringIO(), io.StringIO()
        with contextlib.redirect_stderr(err):
            self._kill(logger)
            for idx in range(200):
                metrics.record_violation("SCHEMA_INVALID", event_id=f"e{idx}")
            logger._write = healthy
            metrics.last_log -= 3600
            with contextlib.redirect_stdout(out):
                metrics.maybe_log()
        summary = out.getvalue()
        self.assertIn("write_failures=200", summary)
        self.assertIn("console_failures=", summary)
        record = [rec for rec in self._records() if rec["type"] == "metrics"]
        self.assertEqual(1, len(record))
        self.assertEqual(200, record[0]["write_failures"])
        self.assertEqual(200, record[0]["write_failures_total"])
        self.assertEqual(0, record[0]["console_failures"])
        # Windowed like every other count in the record: a second interval with
        # no new loss must not restate the same 200.
        out2 = io.StringIO()
        metrics.last_log -= 3600
        with contextlib.redirect_stdout(out2), contextlib.redirect_stderr(err):
            metrics.maybe_log()
        second = [rec for rec in self._records() if rec["type"] == "metrics"][1]
        self.assertEqual(0, second["write_failures"])
        self.assertEqual(200, second["write_failures_total"])

    def test_console_losses_are_reported_on_the_channel_that_still_works(self):
        # The two sinks report each other: a dead console cannot announce its
        # own loss, so the count has to reach the log record.
        logger = gateway.MetricsLogger(self.path)
        metrics = gateway.GatewayMetrics(interval_sec=1, emit=True, logger=logger)
        with contextlib.redirect_stderr(io.StringIO()):
            metrics.last_log -= 3600
            with contextlib.redirect_stdout(_BrokenStream()):
                metrics.maybe_log()
        record = [rec for rec in self._records() if rec["type"] == "metrics"][0]
        self.assertGreater(record["console_failures"], 0)
        self.assertEqual(metrics.console_failures, record["console_failures_total"])

    def test_every_sink_failure_counter_is_surfaced_somewhere(self):
        """Class guard: a counter named in a warning needs a surface, always.

        Scoped to the counter family rather than to the two names in today's
        warning text, so a third sink counter added later is covered the day it
        is written instead of the day someone remembers it.
        """
        logger = gateway.MetricsLogger(self.path)
        metrics = gateway.GatewayMetrics(interval_sec=1, emit=True, logger=logger)
        counters = sorted(
            name
            for obj in (logger, metrics)
            for name in vars(obj)
            if name.endswith("_failures") and not name.startswith("_")
        )
        self.assertIn("write_failures", counters)
        self.assertIn("console_failures", counters)
        healthy = logger._write
        self._kill(logger)
        with contextlib.redirect_stderr(io.StringIO()):
            metrics.record_drop("X")
            metrics.last_log -= 3600
            with contextlib.redirect_stdout(_BrokenStream()):
                metrics.maybe_log()
        logger._write = healthy
        out = io.StringIO()
        metrics.last_log -= 3600
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            metrics.maybe_log()
        record = [rec for rec in self._records() if rec["type"] == "metrics"][-1]
        for name in counters:
            with self.subTest(counter=name):
                self.assertIn(
                    name,
                    out.getvalue(),
                    f"{name} is named to the operator but never printed",
                )
                self.assertIn(
                    name,
                    record,
                    f"{name} is named to the operator but never logged",
                )


class _StopReceiveLoop(BaseException):
    """Ends the loop under test from recvfrom.

    Deliberately a BaseException: `except Exception` can never catch it, so the
    test terminates whether or not recvfrom is inside the backstop. A plain
    Exception would hang forever if the backstop were ever widened.
    """


class _LoopSocket:
    def __init__(self, datagrams=()):
        self.datagrams = list(datagrams)
        self.sent = []

    # sock_in
    def bind(self, _addr):
        return None

    def recvfrom(self, _size):
        if self.datagrams:
            return self.datagrams.pop(0), ("127.0.0.1", 40000)
        raise _StopReceiveLoop()

    # sock_out
    def sendto(self, payload, addr):
        self.sent.append((payload, addr))
        return len(payload)


class ReceiveLoopSurvivesDeadMetricsSinkTest(unittest.TestCase):
    """A-03 end to end, through the real main() receive loop.

    The unit tests above exercise the sinks directly and so share machinery
    with the fix. This one drives the actual loop body - the same code an
    operator runs - and only substitutes the two UDP sockets. Before the fix
    it ends in FileExistsError from inside the except handler instead of the
    sentinel, which is the gateway dying on one datagram.
    """

    def _run_loop(self, datagrams, process_message=None):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        blocker = Path(tmp.name) / "logs"
        blocker.write_text("not a directory", encoding="utf-8")

        sock_in = _LoopSocket(datagrams)
        sock_out = _LoopSocket()
        sockets = [sock_in, sock_out]
        argv = [
            "gateway.py",
            "--profile", "H",
            "--listen-port", "45599",
            "--forward-port", "45598",
            "--metrics-log-path", str(blocker / "metrics.jsonl"),
        ]
        out, err = io.StringIO(), io.StringIO()
        patches = [
            mock.patch("sys.argv", argv),
            mock.patch.object(gateway.socket, "socket", lambda *a, **k: sockets.pop(0)),
        ]
        if process_message is not None:
            patches.append(mock.patch.object(gateway, "process_message", process_message))
        with contextlib.ExitStack() as stack:
            for patch in patches:
                stack.enter_context(patch)
            stack.enter_context(contextlib.redirect_stdout(out))
            stack.enter_context(contextlib.redirect_stderr(err))
            with self.assertRaises(_StopReceiveLoop):
                gateway.main()
        return sock_out, err.getvalue()

    def test_dead_sink_does_not_kill_the_loop_on_the_ordinary_path(self):
        bad = json.dumps({"event": {"event_type": "NOT_A_TYPE"}}).encode()
        sock_out, err = self._run_loop([bad, bad])
        # Both datagrams were translated and their honest in-band diagnostic
        # forwarded; a dead log file changes nothing about the data.
        self.assertEqual(2, len(sock_out.sent))
        for payload, _addr in sock_out.sent:
            event = json.loads(payload)
            self.assertEqual("SCHEMA_VIOLATION", event["event"]["event_subtype"])
        self.assertEqual(1, err.count("metrics log sink unavailable"))

    def test_dead_sink_inside_the_backstop_does_not_kill_the_loop(self):
        # The literal A-03 sequence: something inside the try raises, the
        # backstop handler runs, and the sink it calls is itself dead.
        def _boom(*_args, **_kwargs):
            raise ValueError("inner failure")

        bad = json.dumps({"event": {"event_type": "NOT_A_TYPE"}}).encode()
        sock_out, err = self._run_loop([bad, bad], process_message=_boom)
        self.assertEqual(0, len(sock_out.sent))
        # Two datagrams reached the handler, so the loop survived the first.
        self.assertEqual(
            2, err.count("datagram dropped after unexpected ValueError: inner failure")
        )
        self.assertEqual(1, err.count("metrics log sink unavailable"))


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


class _ExpansionBudgetExceeded(Exception):
    """A walk expanded more containers than the structure contains."""


class _Budget:
    """Turns non-termination into a bounded, deterministic failure.

    A walk that never returns cannot be pinned with a plain assertion -- the
    test would hang instead of failing. So the FIXTURE counts: expanding one
    of these containers spends budget, a walk that revisits without limit
    blows it in milliseconds, and a terminating walk never comes near it. No
    threads, no timeouts, no runaway heap in CI.
    """

    def __init__(self, limit):
        self.limit = limit
        self.used = 0

    def spend(self):
        self.used += 1
        if self.used > self.limit:
            raise _ExpansionBudgetExceeded(
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


class IngressWalkTerminationTest(unittest.TestCase):
    """Both ingress walks must TERMINATE on structure they did not build.

    Removing the RecursionError was only half the job. Neither
    _find_forbidden_key nor _find_non_finite carried a visited set, so a
    self-referential structure wedged the walk forever with the heap rising
    -- ahead of schema validation, ahead of every semantic check, on the
    gateway's receive path. That is an unauthenticated remote hang, and a
    hang is strictly worse than the RecursionError crash the iterative
    rewrite was written to remove: a crash is bounded, observable and
    restartable.

    It is wire-reachable. json.loads cannot build a cycle, but CBOR is a
    supported input encoding and cbor2 -- gateway._decode_cbor's fallback
    when zmeta_cbor is absent -- honours the value-sharing tags (28/29) by
    default, so ~600 bytes decode into a self-referential dict. Same defect
    class as zmeta_compact._find_unencodable_int (R1-11 residual against the
    A-04 wave).
    """

    def test_forbidden_key_walk_terminates_on_a_cycle(self):
        for label, factory in (("dict", "d"), ("list", "l")):
            with self.subTest(container=label):
                budget = _Budget(64)
                if factory == "d":
                    node = _CountedDict(budget)
                    node["self"] = node
                else:
                    node = _CountedList(budget)
                    node.append(node)
                self.assertIsNone(
                    validators._find_forbidden_key(node, {"features"})
                )

    def test_non_finite_walk_terminates_on_a_cycle(self):
        for label, factory in (("dict", "d"), ("list", "l")):
            with self.subTest(container=label):
                budget = _Budget(64)
                if factory == "d":
                    node = _CountedDict(budget)
                    node["self"] = node
                else:
                    node = _CountedList(budget)
                    node.append(node)
                self.assertIsNone(validators._find_non_finite(node))

    def test_termination_does_not_cost_a_finding(self):
        # The seen-set must skip only what is provably redundant. Both walks
        # are breadth-first, so the visit that is kept is the SHALLOWEST one
        # -- which is the answer both functions are specified to return -- and
        # only containers are skipped, never a leaf value or a dict key.
        shared = {"password": 1}
        self.assertEqual(
            ("password", ["b", "password"]),
            validators._find_forbidden_key(
                {"a": {"z": 0}, "b": shared, "c": shared}, {"password"}
            ),
        )
        shared_nan = {"v": float("inf")}
        self.assertEqual(
            "b.v",
            validators._find_non_finite(
                {"a": {"z": 0}, "b": shared_nan, "c": shared_nan}
            ),
        )
        self.assertEqual(
            "a.<key>", validators._find_non_finite({"a": {float("nan"): 1}})
        )
        # A clean shared structure must NOT be reported: sharing is not a
        # cycle, and refusing it would discard honest data to buy termination.
        clean = {"n": 1}
        self.assertIsNone(
            validators._find_forbidden_key({"a": clean, "b": clean}, {"password"})
        )
        self.assertIsNone(validators._find_non_finite({"a": clean, "b": clean}))
        # And a repeat must end that BRANCH, not the walk. Aborting on the
        # first repeat also terminates, and is the cheap version of this fix
        # that silently loses every finding queued behind the duplicate --
        # laundering bought with a one-line "termination fix".
        self.assertEqual(
            ("password", ["c", "password"]),
            validators._find_forbidden_key(
                {"a": clean, "b": clean, "c": {"password": 1}}, {"password"}
            ),
        )
        self.assertEqual(
            "c.v",
            validators._find_non_finite(
                {"a": clean, "b": clean, "c": {"v": float("nan")}}
            ),
        )

    def test_shared_structure_costs_linear_work_not_exponential(self):
        # Value sharing at every level is 2**levels distinct paths. Without
        # the seen-set a few hundred wire bytes buy exponential ingress work,
        # which is the same denial of service by a quieter route.
        for walk in (
            lambda v: validators._find_forbidden_key(v, {"password"}),
            validators._find_non_finite,
        ):
            budget = _Budget(512)
            node = _CountedDict(budget, {"leaf": 1})
            for _ in range(64):
                node = _CountedDict(budget, {"l": node, "r": node})
            self.assertIsNone(walk(node))


if __name__ == "__main__":
    unittest.main()
