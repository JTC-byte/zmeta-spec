"""Operator-debuggability fixes for the reference gateway.

Four gaps from a verified operator-debuggability audit, all on the
diagnostic/metrics surface an operator actually reads at 3am:

1. GatewayMetrics.record_violation/record_warning/record_drop carried no
   detail beyond the bare code, so 24 structurally different garbage
   inputs collapsed into two counters in metrics.jsonl with nothing to
   tell one apart from another.
2. The SCHEMA_INVALID diagnostic could reflect a verbatim payload echo
   (audit measured 10,025 chars for one pathological event_id) straight
   into both the diagnostic event and the metrics record it feeds.
3. With emit_cot=false, the periodic metrics line was bit-identical to
   "CoT is enabled but nothing eligible has arrived yet" (both report
   cot=0 with nothing to distinguish the two operationally different
   states).
4. The startup banner named the JSON forward target but never the CoT
   destination when emit_cot was true.
"""

import contextlib
import importlib.util
import io
import json
import socket
import unittest
from pathlib import Path
from unittest import mock

from zmeta_uuid import uuid7


ROOT = Path(__file__).resolve().parents[2]
VALIDATORS_PATH = ROOT / "gateway" / "src" / "validators.py"
spec_v = importlib.util.spec_from_file_location("zmeta_validators_opdebug", VALIDATORS_PATH)
validators = importlib.util.module_from_spec(spec_v)
spec_v.loader.exec_module(validators)

GATEWAY_PATH = ROOT / "gateway" / "src" / "gateway.py"
spec_gw = importlib.util.spec_from_file_location("zmeta_gateway_opdebug", GATEWAY_PATH)
gateway = importlib.util.module_from_spec(spec_gw)
spec_gw.loader.exec_module(gateway)


class _ListLogger:
    def __init__(self):
        self.records = []

    def write(self, record):
        self.records.append(record)


def _valid_state_event():
    return {
        "zmeta_version": "1.0",
        "event": {
            "event_id": str(uuid7()),
            "event_type": "STATE_EVENT",
            "event_subtype": "TRACK_STATE",
            "ts": "2025-01-17T14:32:10Z",
        },
        "source": {
            "platform_id": "platform-1",
            "node_role": "GATEWAY",
            "producer": "torch",
        },
        "payload": {
            "track_id": "track-1",
            "geo": {"lat": 40.0, "lon": -75.0, "alt_m": 120.5},
            "valid_for_ms": 1000,
        },
        "confidence": 0.9,
        "lineage": {"based_on": [str(uuid7())]},
    }


class MetricsDetailsFieldTest(unittest.TestCase):
    """Fix 1: record_violation/record_warning/record_drop thread a bounded
    `details` string into the metrics.jsonl record, so structurally
    different failures of the same code are distinguishable there.
    """

    def test_record_violation_carries_a_bounded_details_field(self):
        logger = _ListLogger()
        metrics = gateway.GatewayMetrics(interval_sec=30, emit=False, logger=logger)

        metrics.record_violation(
            "SCHEMA_INVALID",
            event_id="evt-1",
            producer="torch",
            details="'x' is not of type 'number'",
        )

        record = logger.records[-1]
        self.assertEqual("violation", record["type"])
        self.assertEqual("SCHEMA_INVALID", record["code"])
        self.assertEqual("evt-1", record["event_id"])
        self.assertEqual("torch", record["producer"])
        self.assertEqual("'x' is not of type 'number'", record["details"])
        # The per-code histogram shape is unchanged by adding details.
        self.assertEqual(1, metrics.window["violation_codes"]["SCHEMA_INVALID"])
        self.assertEqual(1, metrics.total["violation_codes"]["SCHEMA_INVALID"])

    def test_record_violation_details_is_bounded_and_marked(self):
        logger = _ListLogger()
        metrics = gateway.GatewayMetrics(interval_sec=30, emit=False, logger=logger)
        huge = "x" * 5000

        metrics.record_violation("SCHEMA_INVALID", details=huge)

        record = logger.records[-1]
        self.assertLess(len(record["details"]), len(huge))
        self.assertTrue(record["details"].endswith("...<truncated>"))

    def test_record_violation_without_details_omits_the_key(self):
        logger = _ListLogger()
        metrics = gateway.GatewayMetrics(interval_sec=30, emit=False, logger=logger)

        metrics.record_violation("SCHEMA_INVALID")

        self.assertNotIn("details", logger.records[-1])

    def test_record_warning_carries_a_bounded_details_field(self):
        logger = _ListLogger()
        metrics = gateway.GatewayMetrics(interval_sec=30, emit=False, logger=logger)

        metrics.record_warning(
            "TIMING_STATUS_STALE", event_id="evt-2", producer="torch", details="stale by 500ms"
        )

        record = logger.records[-1]
        self.assertEqual("warning", record["type"])
        self.assertEqual("stale by 500ms", record["details"])
        self.assertEqual(1, metrics.window["warning_codes"]["TIMING_STATUS_STALE"])

    def test_record_drop_carries_event_id_and_bounded_details(self):
        logger = _ListLogger()
        metrics = gateway.GatewayMetrics(interval_sec=30, emit=False, logger=logger)

        metrics.record_drop(
            "ENCODING_UNSUPPORTED",
            producer="torch",
            event_id="evt-3",
            details="compact refuses lossy float",
        )

        record = logger.records[-1]
        self.assertEqual("drop", record["type"])
        self.assertEqual("evt-3", record["event_id"])
        self.assertEqual("compact refuses lossy float", record["details"])
        self.assertEqual(1, metrics.window["drop_reasons"]["ENCODING_UNSUPPORTED"])

    def test_two_structurally_different_garbage_inputs_are_now_distinguishable(self):
        """The exact audit measurement: undecodable garbage collapsed into
        one SCHEMA_INVALID counter with no way to tell one malformed input
        from another in metrics.jsonl.
        """
        logger = _ListLogger()
        metrics = gateway.GatewayMetrics(interval_sec=30, emit=False, logger=logger)
        schema_path = ROOT / "schema" / "zmeta-event-1.0.schema.json"
        policy_dir = ROOT / "policy"
        validator = validators.load_schema(schema_path)
        policy = validators.load_policy(policy_dir)

        gateway.process_message(
            b"not json at all {{{", validator, policy, "H", gateway.TaskDedupeCache(),
            "json", metrics=metrics,
        )
        gateway.process_message(
            b"[1, 2, unterminated", validator, policy, "H", gateway.TaskDedupeCache(),
            "json", metrics=metrics,
        )

        violation_records = [r for r in logger.records if r["type"] == "violation"]
        self.assertEqual(2, len(violation_records))
        self.assertEqual(2, metrics.window["violation_codes"]["SCHEMA_INVALID"])
        # Both are SCHEMA_INVALID, but the two records must not be
        # indistinguishable: each carries the short reason for its OWN
        # decode failure.
        self.assertIn("details", violation_records[0])
        self.assertIn("details", violation_records[1])
        self.assertNotEqual(violation_records[0]["details"], violation_records[1]["details"])


class SchemaInvalidTruncationTest(unittest.TestCase):
    """Fix 2: the SCHEMA_INVALID diagnostic's embedded error text is bounded,
    not a verbatim echo of the offending payload (audit measured 10,025
    chars for one pathological event_id).
    """

    @classmethod
    def setUpClass(cls):
        cls.validator = validators.load_schema(ROOT / "schema" / "zmeta-event-1.0.schema.json")
        cls.policy = validators.load_policy(ROOT / "policy")

    def test_a_huge_invalid_event_id_does_not_echo_verbatim_into_the_diagnostic(self):
        event = _valid_state_event()
        # Trips the event_id UUID7 pattern check; jsonschema's pattern
        # mismatch message embeds the offending instance verbatim.
        event["event"]["event_id"] = "a" * 10000

        outgoing = gateway.process_message(
            json.dumps(event).encode("utf-8"),
            self.validator,
            self.policy,
            "H",
            gateway.TaskDedupeCache(),
            "json",
        )

        self.assertEqual(1, len(outgoing))
        error_text = outgoing[0]["payload"]["metrics"]["error"]
        self.assertLess(len(error_text), 2000)
        self.assertTrue(error_text.endswith("...<truncated>"))

    def test_the_bound_also_covers_a_raw_decode_failure(self):
        huge_garbage = ("{" + "x" * 10000).encode("utf-8")

        outgoing = gateway.process_message(
            huge_garbage,
            self.validator,
            self.policy,
            "H",
            gateway.TaskDedupeCache(),
            "json",
        )

        error_text = outgoing[0]["payload"]["metrics"]["error"]
        self.assertLessEqual(len(error_text), gateway.MAX_DIAGNOSTIC_ERROR_CHARS + len("...<truncated>"))


class MetricsCotEnabledLineTest(unittest.TestCase):
    """Fix 3: cot_enabled rides the metrics line and record, so the
    emit_cot=false case is distinguishable at a glance from "CoT enabled
    but nothing eligible has arrived".
    """

    def _summary(self, cot_enabled):
        logger = _ListLogger()
        metrics = gateway.GatewayMetrics(
            interval_sec=1, emit=True, logger=logger, cot_enabled=cot_enabled
        )
        metrics.last_log -= 3600  # force maybe_log past its interval
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            metrics.maybe_log()
        return out.getvalue(), logger.records

    def test_disabled_and_enabled_empty_produce_different_console_lines(self):
        text_off, _ = self._summary(False)
        text_on, _ = self._summary(True)
        self.assertNotEqual(text_off, text_on)
        self.assertIn("cot_enabled=false", text_off)
        self.assertIn("cot_enabled=true", text_on)

    def test_disabled_and_enabled_empty_produce_different_log_records(self):
        _, records_off = self._summary(False)
        _, records_on = self._summary(True)
        metrics_off = [r for r in records_off if r["type"] == "metrics"][-1]
        metrics_on = [r for r in records_on if r["type"] == "metrics"][-1]
        self.assertFalse(metrics_off["cot_enabled"])
        self.assertTrue(metrics_on["cot_enabled"])


class _StopReceiveLoop(BaseException):
    """Ends main()'s receive loop from recvfrom once the startup banner has
    printed. Deliberately a BaseException so `except Exception` inside the
    loop's own backstop cannot swallow it.
    """


class _LoopSocket:
    def __init__(self, datagrams=()):
        self.datagrams = list(datagrams)
        self.sent = []

    def bind(self, _addr):
        return None

    def settimeout(self, _value):
        return None

    def recvfrom(self, _size):
        if self.datagrams:
            return self.datagrams.pop(0), ("127.0.0.1", 40000)
        raise _StopReceiveLoop()

    def sendto(self, payload, addr):
        self.sent.append((payload, addr))
        return len(payload)


class _IdleThenStopSocket:
    """sock_in that never receives a datagram: every recvfrom times out.

    Simulates an idle-but-healthy listen socket, the case where the gateway
    fix under test matters: nothing ever arrives, so the only way
    GatewayMetrics.maybe_log() can run at all is if the receive loop wakes
    on its own instead of blocking on recvfrom forever. After one timeout
    tick this raises _StopReceiveLoop so the test terminates.
    """

    def __init__(self):
        self.timed_out = False
        self.settimeout_calls = []

    def bind(self, _addr):
        return None

    def settimeout(self, value):
        self.settimeout_calls.append(value)

    def recvfrom(self, _size):
        if not self.timed_out:
            self.timed_out = True
            raise socket.timeout()
        raise _StopReceiveLoop()

    def sendto(self, payload, addr):
        raise AssertionError("an idle gateway must never send")


class StartupBannerCotDestinationTest(unittest.TestCase):
    """Fix 4: the startup banner prints the CoT destination when emit_cot is
    true, the same way it already prints the JSON forward target.
    """

    def _run(self, argv):
        sockets = [_LoopSocket([]), _LoopSocket()]
        out = io.StringIO()
        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch("sys.argv", argv))
            stack.enter_context(
                mock.patch.object(gateway.socket, "socket", lambda *a, **k: sockets.pop(0))
            )
            stack.enter_context(contextlib.redirect_stdout(out))
            stack.enter_context(contextlib.redirect_stderr(io.StringIO()))
            with self.assertRaises(_StopReceiveLoop):
                gateway.main()
        return out.getvalue()

    def test_banner_prints_cot_destination_when_emit_cot_is_enabled(self):
        text = self._run(
            [
                "gateway.py", "--profile", "H",
                "--listen-port", "45701", "--forward-port", "45702",
                "--emit-cot", "--cot-host", "10.0.0.5", "--cot-port", "4242",
            ]
        )
        self.assertIn("10.0.0.5:4242", text)

    def test_banner_says_nothing_about_cot_when_emit_cot_is_disabled(self):
        text = self._run(
            [
                "gateway.py", "--profile", "H",
                "--listen-port", "45703", "--forward-port", "45704",
                "--no-emit-cot",
            ]
        )
        self.assertNotIn("cot", text.lower())


class IdleGatewayEmitsPeriodicMetricsTest(unittest.TestCase):
    """v1.1.20 phase-3 fix: GatewayMetrics.maybe_log() was reachable only
    from inside the per-datagram body of the receive loop (and from the
    backstop's own drop handler), both of which run only once a datagram has
    arrived. On an idle listen socket, sock_in.recvfrom blocks forever and
    maybe_log() never runs at all -- so an idle-but-healthy gateway and a
    wedged one are both silent past the startup banner, and an operator has
    no periodic signal to tell the two apart.

    The fix wakes the receive loop on the metrics interval even with nothing
    to receive, and still runs the periodic summary from there.
    """

    def test_idle_gateway_still_prints_periodic_metrics_summary(self):
        sock_in = _IdleThenStopSocket()
        sockets = [sock_in, _LoopSocket()]
        argv = [
            "gateway.py", "--profile", "H",
            "--listen-port", "45705", "--forward-port", "45706",
            "--metrics-interval-sec", "1",
        ]
        out = io.StringIO()
        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch("sys.argv", argv))
            stack.enter_context(
                mock.patch.object(gateway.socket, "socket", lambda *a, **k: sockets.pop(0))
            )
            # Exactly two monotonic() reads occur on this path when idle:
            # GatewayMetrics.__init__ seeds last_log, then maybe_log() reads
            # "now" once on the timeout tick. Advancing by 10s past the 1s
            # interval forces maybe_log() to fire without a real sleep.
            stack.enter_context(
                mock.patch.object(gateway.time, "monotonic", side_effect=[1000.0, 1010.0])
            )
            stack.enter_context(contextlib.redirect_stdout(out))
            stack.enter_context(contextlib.redirect_stderr(io.StringIO()))
            with self.assertRaises(_StopReceiveLoop):
                gateway.main()
        text = out.getvalue()
        # recv=0: the summary printed with zero datagrams ever received, so
        # it could only have come from the idle wake-up, not the ordinary
        # per-datagram path.
        self.assertIn("metrics interval=1s recv=0 bytes=0 fwd=0", text)
        self.assertEqual([1], sock_in.settimeout_calls)


if __name__ == "__main__":
    unittest.main()
