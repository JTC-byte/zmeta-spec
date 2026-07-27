"""Dedicated pins for the `metrics_sink_gap` JSONL record (R1-11-09).

The record is the in-band loss marker for the gateway's metrics log sink:
when the sink dies and later recovers, the marker is appended ahead of the
next record so a consumer READS the discontinuity instead of inferring it
from a hole it has no way to see. The alternative - no marker - was
measured as silent loss of 200 records with the summary still reporting
every one of them (docs/zmeta_doctrine_review_log.md, R1-11-09).

The token is operator-visible vocabulary: log tooling keys on the exact
string `metrics_sink_gap` and on the exact field names it carries.
Adjudicated 2026-07-27 as outer-ring - gateway-internal observability, not
the governed event model - so the record has no JSON Schema and this file
is what keeps the token and its payload shape from drifting. That is why
the assertions below are exact (full key set, exact token, exact error
string), not merely presence checks: a consumer's filter breaks on a
renamed field whether or not a schema exists.
"""

import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
GATEWAY_PATH = ROOT / "gateway" / "src" / "gateway.py"
spec_gw = importlib.util.spec_from_file_location("zmeta_gateway_sink_gap", GATEWAY_PATH)
gateway = importlib.util.module_from_spec(spec_gw)
spec_gw.loader.exec_module(gateway)


class MetricsSinkGapRecordTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.path = self.tmp / "ok" / "metrics.jsonl"

    @staticmethod
    def _kill(logger, message):
        # Matches _write's real signature, `rotate` included: a double that
        # silently accepted anything would hide a signature change in the
        # method it stands in for.
        def _boom(_record, rotate=True):
            raise OSError(message)

        logger._write = _boom

    def _records(self):
        return [
            json.loads(line)
            for line in self.path.read_text(encoding="utf-8").splitlines()
        ]

    def test_gap_record_carries_exactly_the_documented_shape(self):
        logger = gateway.MetricsLogger(self.path)
        with contextlib.redirect_stderr(io.StringIO()):
            logger.write({"type": "violation", "code": "A"})
            healthy = logger._write
            self._kill(logger, "disk gone: first failure")
            logger.write({"type": "violation", "code": "LOST"})
            # A later, different error must not displace the FIRST: the
            # marker attributes the gap to what killed the sink, not to
            # whatever it happened to die of last.
            self._kill(logger, "disk gone: later failure")
            for _ in range(2):
                logger.write({"type": "violation", "code": "LOST"})
            logger._write = healthy
            logger.write({"type": "violation", "code": "B"})
        records = self._records()
        self.assertEqual(
            ["violation", "metrics_sink_gap", "violation"],
            [record["type"] for record in records],
        )
        marker = records[1]
        # The full key set is the record's wire contract: consumers key on
        # exactly these five names, and nothing else rides along - not even
        # contract_hash, which belongs to event records, not to a statement
        # about the sink itself.
        self.assertEqual(
            {"type", "ts", "path", "lost_records", "first_error"}, set(marker)
        )
        self.assertEqual("metrics_sink_gap", marker["type"])
        self.assertEqual(3, marker["lost_records"])
        self.assertEqual("OSError: disk gone: first failure", marker["first_error"])
        self.assertEqual(str(self.path), marker["path"])
        self.assertEqual(3, logger.write_failures)
        # ts follows the same utc_now() convention as every _log_event
        # record: second-resolution ISO-8601 UTC with a Z suffix.
        self.assertTrue(marker["ts"].endswith("Z"), marker["ts"])
        parsed = datetime.fromisoformat(marker["ts"].replace("Z", "+00:00"))
        self.assertEqual(0, parsed.microsecond)

    def test_a_healthy_sink_never_emits_the_marker(self):
        # Anti-noise direction: the marker means LOSS, so a healthy run must
        # produce zero of them. A marker on a healthy file would train
        # consumers to ignore the one token that exists to be alarming.
        logger = gateway.MetricsLogger(self.path)
        for idx in range(50):
            logger.write({"type": "violation", "code": f"A{idx}"})
        self.assertEqual(
            {"violation"}, {record["type"] for record in self._records()}
        )
        self.assertEqual(50, len(self._records()))
        self.assertEqual(0, logger.write_failures)

    def test_the_measured_silent_gap_is_now_read_in_band(self):
        """The R1-11-09 measurement, replayed through GatewayMetrics.

        The no-marker alternative was measured as 200 records lost with the
        in-memory summary still counting all of them - the file showed
        contiguous records and nothing said otherwise. Driven through the
        same record_* entry points, the file must now carry the gap where
        the loss happened, quantified.
        """
        logger = gateway.MetricsLogger(self.path)
        metrics = gateway.GatewayMetrics(interval_sec=3600, emit=False, logger=logger)
        with contextlib.redirect_stderr(io.StringIO()):
            for _ in range(4):
                metrics.record_violation("SCHEMA_INVALID")
            healthy = logger._write
            self._kill(logger, "no space left on device")
            for _ in range(200):
                metrics.record_violation("SCHEMA_INVALID")
            logger._write = healthy
            metrics.record_violation("SCHEMA_INVALID")
        # The in-memory summary still counts every violation...
        self.assertEqual(205, metrics.total["violations"])
        # ...and the file no longer pretends it saw them all: 4 landed, the
        # gap is read as a record, then the post-recovery one.
        records = self._records()
        self.assertEqual(
            ["violation"] * 4 + ["metrics_sink_gap", "violation"],
            [record["type"] for record in records],
        )
        self.assertEqual(200, records[4]["lost_records"])
        self.assertEqual("OSError: no space left on device", records[4]["first_error"])
        self.assertEqual(200, logger.write_failures)


if __name__ == "__main__":
    unittest.main()
