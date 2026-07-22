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
        # Everything print() actually put into the stream before flush failed.
        # These bytes are produced whether or not the warning was delivered,
        # which is the whole reason the retry has to be bounded.
        self.text = ""

    def write(self, text):
        self.text += text
        return len(text)

    def flush(self):
        if self._live:
            raise OSError("stream is gone")

    def close(self):
        # Finalization flushes; a raise from there is the test harness's
        # problem, not the property under test.
        self._live = False
        super().close()


def _let_the_warning_retry(*sinks):
    """Model the passage of one gateway.SINK_WARNING_RETRY_SEC.

    An undelivered one-shot sink warning is re-attempted, but at most once per
    retry interval, so a test that issues its writes back to back has to say
    that time passed. Opening the gate directly keeps these tests deterministic
    and off the wall clock. The bound ITSELF is pinned by
    MetricsSinkWarningStormTest, which never touches these attributes.
    """
    for sink in sinks:
        for attr in ("_warn_retry_at", "_console_warn_retry_at"):
            if hasattr(sink, attr):
                setattr(sink, attr, 0.0)


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
        # stderr recovers; the sink is still dead. A retry interval has to have
        # elapsed for the re-attempt to be due.
        _let_the_warning_retry(logger)
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
        _let_the_warning_retry(metrics)
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
        _let_the_warning_retry(logger)
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
        # Matches _write's real signature, `rotate` included: a double that
        # silently accepted anything would hide a signature change in the
        # method it stands in for.
        def _boom(_record, rotate=True):
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

            def _fail_the_marker_then_recover(record, rotate=True):
                attempts["n"] += 1
                if attempts["n"] == 1:
                    raise OSError("no space left on device")
                healthy(record, rotate=rotate)

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

    def test_console_window_and_cumulative_are_distinct_on_both_surfaces(self):
        """The console half of the window-vs-cumulative distinction.

        The log half is pinned above. Restating a running total as a per-window
        count makes an operator read a long-past outage as an ongoing one,
        every interval, forever - and it was unpinned on the console counter:
        substituting `self.console_failures` for `window["console_failures"]`
        at either the record site or the console-line site left the whole file
        green (R1-11 R2-25). Both surfaces are asserted because the two sites
        are separate.
        """
        logger = gateway.MetricsLogger(self.path)
        metrics = gateway.GatewayMetrics(interval_sec=1, emit=True, logger=logger)
        # Interval 1: stdout is dead, so the console counter takes real losses.
        with contextlib.redirect_stderr(io.StringIO()):
            metrics.last_log -= 3600
            with contextlib.redirect_stdout(_BrokenStream()):
                metrics.maybe_log()
        first = [rec for rec in self._records() if rec["type"] == "metrics"][-1]
        lost = first["console_failures"]
        self.assertGreater(lost, 0)
        self.assertEqual(lost, first["console_failures_total"])
        # Interval 2: stdout works again and nothing new is lost. The window
        # count must be 0 while the cumulative one still remembers.
        out = io.StringIO()
        metrics.last_log -= 3600
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            metrics.maybe_log()
        second = [rec for rec in self._records() if rec["type"] == "metrics"][-1]
        self.assertEqual(
            0,
            second["console_failures"],
            "a quiet interval must not restate the earlier console losses",
        )
        self.assertEqual(lost, second["console_failures_total"])
        degraded = [
            line for line in out.getvalue().splitlines() if "sink_degraded" in line
        ]
        self.assertEqual(1, len(degraded))
        self.assertIn("console_failures=0 ", degraded[0])
        self.assertIn(f"console_failures_total={lost}", degraded[0])

    def test_an_unreadable_counter_is_reported_as_unknown_not_as_zero_losses(self):
        """Degrading to "0 losses" is a claim, not an absence of one.

        The counter read can fail while the sink is still dead. Reporting
        (0, 0) then made the cumulative total non-monotone (200 -> 0 -> 250,
        which a delta collector reads as a counter reset), deleted the
        sink_degraded line for the whole interval, and put a positive
        `write_failures_total: 0` on the wire at the moment the gateway knew
        least (R1-11 R2-14).
        """

        class _Flaky:
            def __init__(self):
                self.records = []
                self.count = 200
                self.raising = False

            def write(self, record):
                self.records.append(record)

            @property
            def write_failures(self):
                if self.raising:
                    raise RuntimeError("counter transiently unavailable")
                return self.count

        logger = _Flaky()
        metrics = gateway.GatewayMetrics(interval_sec=1, emit=True, logger=logger)
        lines, records = [], []

        def _interval():
            out = io.StringIO()
            metrics.last_log -= 3600
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
                metrics.maybe_log()
            lines.append(out.getvalue())
            records.append([r for r in logger.records if r["type"] == "metrics"][-1])

        _interval()                       # readable, 200 genuinely lost
        logger.raising = True
        _interval()                       # counter unreadable, sink still dead
        logger.raising = False
        logger.count = 250
        _interval()                       # readable again

        totals = [rec["write_failures_total"] for rec in records]
        self.assertEqual([200, 200, 250], totals, "the cumulative total went backwards")
        self.assertEqual(sorted(totals), totals, "the cumulative total is not monotone")
        self.assertEqual([True, False, True], [r["write_failures_readable"] for r in records])
        # The surface this whole subsystem exists to provide must not vanish
        # exactly when the reading fails.
        self.assertIn("sink_degraded", lines[1])
        self.assertIn("write_failures_readable=false", lines[1])
        # ...and it must not carry that qualifier when the reading is good.
        self.assertNotIn("write_failures_readable", lines[0])
        self.assertNotIn("write_failures_readable", lines[2])
        # The window delta is still a delta, never the running total restated.
        self.assertEqual([200, 0, 50], [rec["write_failures"] for rec in records])

    def test_a_counter_that_goes_backwards_is_not_believed(self):
        # A counter that decreases is a broken counter or a replaced sink;
        # believing it publishes a cumulative total that drops.
        class _Rewinding:
            def __init__(self):
                self.records = []
                self.write_failures = 200

            def write(self, record):
                self.records.append(record)

        logger = _Rewinding()
        metrics = gateway.GatewayMetrics(interval_sec=1, emit=True, logger=logger)
        # 5 is a plausible replaced sink; -1 and a value int() cannot read are
        # the hostile shapes. All three are "unknown", none of them is zero.
        for value in (200, 5):
            logger.write_failures = value
            metrics.last_log -= 3600
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                metrics.maybe_log()
        records = [r for r in logger.records if r["type"] == "metrics"]
        self.assertEqual([200, 200], [r["write_failures_total"] for r in records])
        self.assertEqual([True, False], [r["write_failures_readable"] for r in records])

    def test_a_counter_that_is_not_a_number_is_unknown_not_zero(self):
        # int() raising is the same class as the property raising: neither is
        # evidence that the sink is healthy.
        for hostile in ("not-a-number", float("nan"), object(), -1):
            with self.subTest(counter=repr(hostile)):

                class _Hostile:
                    def __init__(self):
                        self.records = []
                        self.write_failures = hostile

                    def write(self, record):
                        self.records.append(record)

                logger = _Hostile()
                metrics = gateway.GatewayMetrics(interval_sec=1, emit=True, logger=logger)
                metrics.last_log -= 3600
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    metrics.maybe_log()  # must not raise
                record = [r for r in logger.records if r["type"] == "metrics"][-1]
                self.assertFalse(record["write_failures_readable"])
                self.assertEqual(0, record["write_failures_total"])

    def test_a_sink_that_exposes_no_counter_does_not_claim_a_healthy_sink(self):
        # getattr's default turned "this sink has no counter" into "this sink
        # lost nothing" - a positive claim about a sink the gateway cannot see.
        class _NoCounter:
            def __init__(self):
                self.records = []

            def write(self, record):
                self.records.append(record)

        logger = _NoCounter()
        metrics = gateway.GatewayMetrics(interval_sec=1, emit=True, logger=logger)
        out = io.StringIO()
        metrics.last_log -= 3600
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            metrics.maybe_log()
        record = [r for r in logger.records if r["type"] == "metrics"][-1]
        self.assertFalse(record["write_failures_readable"])
        # No console noise for a benign configuration: nothing was lost, so
        # the degradation line must not fire every interval forever.
        self.assertNotIn("sink_degraded", out.getvalue())

    def test_log_sink_losses_reach_the_run_total_like_every_other_counter(self):
        # log_write_failures was the one counter incremented straight onto the
        # window dict, so total['log_write_failures'] was dead and permanently
        # 0 for the life of the process (R1-11 R2-29).
        logger = gateway.MetricsLogger(self.path)
        metrics = gateway.GatewayMetrics(interval_sec=1, emit=True, logger=logger)
        with contextlib.redirect_stderr(io.StringIO()):
            self._kill(logger)
            for _ in range(7):
                metrics.record_drop("X")
            metrics.last_log -= 3600
            with contextlib.redirect_stdout(io.StringIO()):
                metrics.maybe_log()
        self.assertEqual(7, metrics.total["log_write_failures"])

    def test_no_window_counter_is_incremented_outside_bump(self):
        """Class guard: `self.total` only stays true if every counter uses _bump.

        Scoped to the family rather than to log_write_failures, so the next
        counter written straight onto the window dict is caught the day it is
        added rather than the day someone reads self.total and gets a zero.
        """
        source = GATEWAY_PATH.read_text(encoding="utf-8")
        offenders = [
            line.strip()
            for line in source.splitlines()
            # A literal-keyed window increment. `self.window[key] += inc`
            # inside _bump itself is the mechanism, not an offender.
            if 'window["' in line and "+=" in line
        ]
        self.assertEqual([], offenders)
        # Guard the guard: _bump is still the thing that keeps the two in step.
        self.assertIn("self.total[key] += inc", source)


class MetricsSinkWarningStormTest(unittest.TestCase):
    """Retrying an undelivered warning must not become the storm it replaced.

    The latch is spent on DELIVERY, so an undelivered attempt has to be
    retried. Retrying on every failed write reintroduced exactly the
    per-datagram warning storm the one-shot design exists to prevent: measured
    at 1000 warning lines / 473,000 bytes of stderr for 1000 failed writes, on
    a stream that accepts the write and fails at flush - which is how ENOSPC
    and EPIPE usually surface, and is the shape the delivery fix itself was
    written for (R1-11 R2-15). The bound is in TIME, not in count: a count cap
    would silently stop reporting recovery.

    Nothing here touches _warn_retry_at - that is the property under test.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        blocker = Path(self._tmp.name) / "logs"
        blocker.write_text("not a directory", encoding="utf-8")
        self.dead_path = blocker / "metrics.jsonl"

    def test_a_stderr_that_queues_and_fails_at_flush_does_not_get_one_warning_per_record(self):
        logger = gateway.MetricsLogger(self.dead_path)
        stream = _FlushFailsStream()
        with contextlib.redirect_stderr(stream):
            for _ in range(1000):
                logger.write({"type": "drop", "reason": "X"})
        self.assertEqual(1000, logger.write_failures)
        self.assertFalse(logger._warned, "nothing was ever delivered, so nothing latched")
        lines = stream.text.count("metrics log sink unavailable")
        self.assertLessEqual(
            lines,
            2,
            f"{lines} warnings for 1000 failed writes is the storm the latch exists "
            "to prevent",
        )
        self.assertGreaterEqual(lines, 1, "the operator must still be told once")

    def test_the_console_sink_retry_is_bounded_the_same_way(self):
        # maybe_log calls _print once per summary LINE, so an unbounded retry
        # is already several stderr warnings per interval here.
        metrics = gateway.GatewayMetrics(interval_sec=1, emit=True)
        stream = _FlushFailsStream()
        with contextlib.redirect_stderr(stream):
            for _ in range(50):
                metrics.last_log -= 3600
                with contextlib.redirect_stdout(_BrokenStream()):
                    metrics.maybe_log()
        lines = stream.text.count("metrics console sink unavailable")
        self.assertLessEqual(lines, 2, f"{lines} console-sink warnings is a storm")
        self.assertGreaterEqual(lines, 1)

    def test_a_real_full_disk_stderr_is_not_hammered_once_per_record(self):
        """Independent oracle: count syscalls, not warning lines.

        _FlushFailsStream is a hand-written double that shares its notion of
        "queued but not delivered" with the code under test. This one measures
        the thing the operator's machine actually pays - failed write attempts
        against a dead fd - through a real TextIOWrapper/BufferedWriter stack
        over a raw stream that raises ENOSPC, i.e. `gateway 2> /full/disk`.
        Measured unbounded: 2000 failed record writes produced 2000 of them.
        """

        class _NoSpaceRaw(io.RawIOBase):
            def __init__(self):
                super().__init__()
                self.attempts = 0
                self.live = True

            def writable(self):
                return True

            def write(self, data):
                if not self.live:
                    # Finalization flushes; a raise from there is the harness's
                    # problem, not the property under test.
                    return len(data)
                self.attempts += 1
                raise OSError(28, "No space left on device")

        raw = _NoSpaceRaw()
        stream = io.TextIOWrapper(io.BufferedWriter(raw, 8192), line_buffering=True)
        logger = gateway.MetricsLogger(self.dead_path)
        with contextlib.redirect_stderr(stream):
            for _ in range(2000):
                logger.write({"type": "drop", "reason": "X"})
        raw.live = False
        self.addCleanup(stream.close)
        self.assertEqual(2000, logger.write_failures)
        self.assertLessEqual(
            raw.attempts,
            2,
            f"{raw.attempts} write(2) attempts against a dead fd for 2000 records",
        )
        self.assertGreaterEqual(raw.attempts, 1, "the operator must still be told once")

    def test_the_bound_is_time_based_so_recovery_is_still_announced(self):
        # A count cap would stop reporting forever. After the retry interval
        # elapses the warning must still land the moment stderr comes back.
        logger = gateway.MetricsLogger(self.dead_path)
        with contextlib.redirect_stderr(_FlushFailsStream()):
            for _ in range(100):
                logger.write({"type": "drop", "reason": "X"})
        self.assertFalse(logger._warned)
        logger._warn_retry_at -= gateway.SINK_WARNING_RETRY_SEC + 1  # time passes
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            logger.write({"type": "drop", "reason": "X"})
        self.assertTrue(logger._warned)
        self.assertEqual(1, err.getvalue().count("metrics log sink unavailable"))


class MetricsSinkGapMarkerRotationTest(unittest.TestCase):
    """The gap marker and the record it annotates must land in one file.

    _write rotates before every append, so writing the marker and then the
    record as two appends let rotation fall between them: the post-gap record
    started a new file with no marker above it, and with backups <= 0 the
    rotation truncates in place and destroys the marker outright - leaving
    exactly the pair of contiguous-looking records the marker exists to
    prevent (R1-11 R2-16). The pre-existing marker pin uses the 5 MB default
    max_bytes and ~200 short records, so it structurally cannot cross a
    rotation boundary.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)
        self.path = self.dir / "metrics.jsonl"

    def _kinds(self, path):
        if not path.exists():
            return []
        return [
            json.loads(line)["type"]
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def _run(self, backups, prefill):
        logger = gateway.MetricsLogger(self.path, max_bytes=200, backups=backups)
        with contextlib.redirect_stderr(io.StringIO()):
            for idx in range(prefill):
                logger.write({"type": "violation", "code": f"A{idx}"})
            size_before = self.path.stat().st_size
            healthy = logger._write

            def _boom(_record, rotate=True):
                raise OSError("no space left on device")

            logger._write = _boom
            for _ in range(3):
                logger.write({"type": "violation", "code": "LOST"})
            logger._write = healthy
            logger.write({"type": "violation", "code": "B"})
        return size_before

    def test_the_marker_stays_with_its_record_across_a_rotation_boundary(self):
        # prefill=6 puts the file over max_bytes so the recovery write really
        # does cross a rotation boundary; prefill=1 is the control.
        for backups in (3, 0):
            for prefill, rotates in ((1, False), (6, True)):
                with self.subTest(backups=backups, prefill=prefill):
                    self.setUp()
                    size_before = self._run(backups, prefill)
                    # Anti-vacuity: if the boundary were never crossed this
                    # subtest would prove nothing at all.
                    self.assertEqual(
                        rotates,
                        size_before >= 200,
                        "the rotation case no longer crosses max_bytes",
                    )
                    live = self._kinds(self.path)
                    self.assertIn(
                        "metrics_sink_gap",
                        live,
                        "the marker is not in the file the consumer is tailing",
                    )
                    # ...and immediately above the record it annotates.
                    self.assertEqual(
                        "violation",
                        live[live.index("metrics_sink_gap") + 1],
                        "the marker was separated from the record it precedes",
                    )
                    if rotates and backups > 0:
                        # ...and the rotation genuinely happened.
                        self.assertTrue(
                            (self.dir / "metrics.jsonl.1").exists(),
                            "no rotation occurred, so nothing was under test",
                        )

    def test_truncating_rotation_cannot_destroy_the_marker(self):
        # backups=0 truncates in place, so a rotation after the marker erases
        # it from disk entirely rather than merely relocating it.
        self._run(0, 6)
        on_disk = any(
            "metrics_sink_gap" in path.read_text(encoding="utf-8")
            for path in self.dir.iterdir()
            if path.is_file()
        )
        self.assertTrue(on_disk, "the marker exists nowhere on disk")


class WireSafeDetailsCoverageTest(unittest.TestCase):
    """The details sanitizer must cover keys and abstract containers.

    It is the boundary where violation details become wire content, and it
    reproduced inside its own remediation the two blindnesses the kernel walk
    was widened to remove: values were converted but KEYS were not, so
    json.dumps laundered a NaN key into the bare string "NaN"; and dispatch
    was on concrete dict/list/tuple/set, so a cbor2 frozendict passed through
    with its non-finite intact (R1-11 R2-22).
    """

    def test_a_non_finite_map_key_is_marked_not_laundered(self):
        cleaned = gateway._wire_safe_details(
            {"field": "payload.metrics.est_error_ms", "histogram": {float("nan"): 3}}
        )
        key = list(cleaned["histogram"])[0]
        self.assertIsInstance(key, str)
        self.assertEqual("<non-finite:nan>", key)
        # The whole point: the refusal is now RFC 8259 and cannot be misread
        # as a number the sensor reported.
        text = json.dumps(cleaned, allow_nan=False)
        self.assertNotIn('"NaN"', text)

    def test_every_non_finite_key_flavour_is_named(self):
        cleaned = gateway._wire_safe_details(
            {float("nan"): 1, float("inf"): 2, float("-inf"): 3}
        )
        # Read off the module's own marker table: NaN, +inf and -inf are
        # different sensor faults and the key must keep the distinction.
        self.assertEqual(
            sorted(gateway._NON_FINITE_DETAIL_MARKERS.values()), sorted(cleaned)
        )
        self.assertEqual(3, len(cleaned))

    def test_ordinary_keys_are_left_exactly_as_they_were(self):
        # Renaming a key changes the diagnostic; only the dishonest ones move.
        original = {"field": 1, 2: "two", True: "yes", None: "none", 3.5: "f"}
        self.assertEqual(original, gateway._wire_safe_details(original))

    def test_a_non_dict_mapping_is_walked_and_becomes_encodable(self):
        cbor2 = _optional("cbor2")
        if cbor2 is None:  # pragma: no cover - cbor2 is a declared dependency
            self.skipTest("cbor2 not installed")
        cleaned = gateway._wire_safe_details(
            {"vendor": cbor2.frozendict({"x": float("nan")})}
        )
        self.assertEqual({"vendor": {"x": "<non-finite:nan>"}}, cleaned)
        json.dumps(cleaned, allow_nan=False)

    def test_text_is_a_leaf_not_a_sequence(self):
        """Forward guard on the next plausible widening of the dispatch.

        str/bytes/bytearray are Sequences. The dispatch matches Mapping and Set
        abstractly but list/tuple concretely, so today nothing walks text; the
        moment someone widens it to bare `Sequence` without putting a text leaf
        arm in front, every string in every diagnostic becomes a list of its
        own characters. That mutation is what this catches.
        """
        original = {"t": "abc", "b": b"abc", "ba": bytearray(b"ab"), "n": [1.0]}
        self.assertEqual(original, gateway._wire_safe_details(original))

    def test_a_self_referential_detail_still_terminates(self):
        # Guard the guard: widening the dispatch must not reopen the cycle
        # hang the memo was added for.
        loop = {"a": 1}
        loop["self"] = loop
        cleaned = gateway._wire_safe_details(loop)
        self.assertIs(cleaned, cleaned["self"])


def _optional(name):
    try:
        return importlib.import_module(name)
    except ImportError:  # pragma: no cover - optional dependency
        return None


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


class UnencodableEventDropReasonTest(unittest.TestCase):
    """The last rung of the egress ladder must drop honestly, not generically.

    R1-11 A-28: `_encode_outgoing_or_diagnostic` returns `(None, event)` when
    even the minimal diagnostic cannot be encoded, and the receive loop then
    drops that datagram as `ENCODING_UNSUPPORTED` and continues. Nothing drove
    that branch. Deleting it left the whole suite green - the nearest test
    counts `record_drop` string literals `>= 4`, which goes slack the moment a
    fifth lands anywhere - while the datagram fell through to
    `_check_datagram_size(len(None))`, raising TypeError into the A-03
    backstop. No crash, but the operator-facing drop reason silently changed
    from the honest `ENCODING_UNSUPPORTED` to the catch-all `INTERNAL_ERROR`,
    so a `drop_reasons` filter for encoding refusals showed zero while every
    such event was being discarded.

    There is no natural datagram that reaches it: the second rung builds a
    minimal diagnostic with no caller content, which compact can always carry.
    So the fault is injected at the documented boundary - `_encode_message`,
    the sole thing `_encode_outgoing_or_diagnostic` calls - and the injection
    is itself asserted below rather than assumed, because an oracle that
    silently stopped reaching the branch would pass with zero drops.
    """

    def setUp(self):
        if not gateway._COMPACT_UNREPRESENTABLE:  # pragma: no cover
            self.skipTest("zmeta_compact not installed")
        self._unrepresentable = gateway._COMPACT_UNREPRESENTABLE[0]
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.log_path = Path(self._tmp.name) / "metrics.jsonl"

    def _refuse_every_encode(self, *_args, **_kwargs):
        raise self._unrepresentable("nothing on this wire can carry it")

    def _run_loop(self, datagrams):
        sock_in = _LoopSocket(datagrams)
        sock_out = _LoopSocket()
        sockets = [sock_in, sock_out]
        argv = [
            "gateway.py",
            "--profile", "H",
            "--listen-port", "45597",
            "--forward-port", "45596",
            "--metrics-log-path", str(self.log_path),
        ]
        out, err = io.StringIO(), io.StringIO()
        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch("sys.argv", argv))
            stack.enter_context(
                mock.patch.object(gateway.socket, "socket", lambda *a, **k: sockets.pop(0))
            )
            stack.enter_context(
                mock.patch.object(gateway, "_encode_message", self._refuse_every_encode)
            )
            stack.enter_context(contextlib.redirect_stdout(out))
            stack.enter_context(contextlib.redirect_stderr(err))
            with self.assertRaises(_StopReceiveLoop):
                gateway.main()
        return sock_out, err.getvalue()

    def _records(self):
        if not self.log_path.exists():
            return []
        return [
            json.loads(line)
            for line in self.log_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def test_the_injection_really_exhausts_the_recovery_ladder(self):
        # Anti-vacuity: if the ladder ever stopped returning None under this
        # injection, the loop test below would pass having driven nothing.
        settings = {
            "output_encoding": "json",
            "profile": "H",
            "stamp_contract_hash": False,
        }
        with mock.patch.object(gateway, "_encode_message", self._refuse_every_encode):
            payload, event = gateway._encode_outgoing_or_diagnostic(
                {"event": {"event_id": "e-1"}},
                settings,
                contract_hashes={"contract_hash": "sha256:x"},
                should_stamp_profile=False,
                metrics=None,
            )
        self.assertIsNone(payload)
        self.assertEqual({"event": {"event_id": "e-1"}}, event)

    def test_an_unencodable_event_is_dropped_as_encoding_unsupported(self):
        bad = json.dumps({"event": {"event_type": "NOT_A_TYPE"}}).encode()
        sock_out, err = self._run_loop([bad, bad])

        # Nothing may reach the wire: there is no honest bytes to send.
        self.assertEqual([], sock_out.sent)
        drops = [record for record in self._records() if record["type"] == "drop"]
        # Exactly one per datagram, so the loop continued rather than dying on
        # the first - and the count cannot pass on an empty result set.
        self.assertEqual(2, len(drops), f"expected two drops, got {drops}")
        self.assertEqual(
            ["ENCODING_UNSUPPORTED", "ENCODING_UNSUPPORTED"],
            [record["reason"] for record in drops],
            "the operator-facing drop reason is not the honest encoding "
            "refusal; a drop_reasons filter for encoding failures now shows "
            "zero while every such event is discarded",
        )
        # It must be the dedicated branch that recorded it, not the catch-all
        # backstop reached by falling through into len(None).
        self.assertNotIn("datagram dropped after unexpected", err)

    def test_the_refusal_is_still_announced_as_a_violation(self):
        # Proportionality: the datagram is dropped, but the reason travels on
        # the violation surface too, so an operator can see WHICH event was
        # unrepresentable and not merely that a drop happened.
        bad = json.dumps({"event": {"event_type": "NOT_A_TYPE"}}).encode()
        self._run_loop([bad])
        violations = [
            record for record in self._records() if record["type"] == "violation"
        ]
        self.assertIn("ENCODING_UNSUPPORTED", [record["code"] for record in violations])


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
