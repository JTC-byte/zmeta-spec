"""X1-01, runtime half: a config-gated plausibility window on event.ts.

schema/zmeta-event-1.1.0.schema.json now rejects a structurally corrupted
calendar shape (test_x1_01_ts_structural_shape.py), but a structurally VALID
ts that is simply wrong by years is not a schema question -- no pattern can
know what "now" is, and the locked v1.0 schema cannot gain a check like this
either way (semantics-contract 5.7: cross-event plausibility is
policy/runtime enforcement).

`_check_ts_plausibility` closes that gap at the gateway, on ANY
zmeta_version. It is wired exactly like the existing config-gated,
metrics-only checks (`_check_datagram_size` / `warn_datagram_bytes`): a
single threshold, 0 disables, never blocks forwarding, and a hit is counted
in GatewayMetrics under `warning_codes` with reason code
EVENT_TS_IMPLAUSIBLE. It is deliberately NOT routed through the
policy/violation-codes.yaml severity machinery: a fast producer clock, a
slow store-and-forward link, and a genuinely corrupted ts all land here the
same way, and the check cannot tell which of the three it is looking at, so
warn-only observability is the ceiling, not an escalatable policy decision.
"""

import importlib.util
import json
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

from zmeta_uuid import uuid7

ROOT = Path(__file__).resolve().parents[2]

VALIDATORS_PATH = ROOT / "gateway" / "src" / "validators.py"
_spec_v = importlib.util.spec_from_file_location("zmeta_validators_tsp", VALIDATORS_PATH)
validators = importlib.util.module_from_spec(_spec_v)
_spec_v.loader.exec_module(validators)

GATEWAY_PATH = ROOT / "gateway" / "src" / "gateway.py"
_spec_gw = importlib.util.spec_from_file_location("zmeta_gateway_tsp", GATEWAY_PATH)
gateway = importlib.util.module_from_spec(_spec_gw)
_spec_gw.loader.exec_module(gateway)


NOW = datetime(2026, 8, 3, 12, 0, 0, tzinfo=timezone.utc)
ONE_HOUR_MS = 60 * 60 * 1000


def state_event(ts, version="1.0"):
    return {
        "zmeta_version": version,
        "event": {
            "event_id": str(uuid7()),
            "event_type": "STATE_EVENT",
            "event_subtype": "TRACK_STATE",
            "ts": ts,
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
        },
        "confidence": 0.62,
        "lineage": {"based_on": [str(uuid7())]},
    }


class CheckTsPlausibilityUnitTest(unittest.TestCase):
    """Direct unit coverage of the pure gate, mirroring
    OversizeDatagramWarningTest.test_check_datagram_size_thresholds."""

    def test_disabled_threshold_never_warns(self):
        metrics = gateway.GatewayMetrics(interval_sec=30, emit=False)
        event = state_event("0001-01-01T00:00:00Z")
        self.assertFalse(
            gateway._check_ts_plausibility(metrics, event, 0, now=NOW)
        )
        self.assertFalse(
            gateway._check_ts_plausibility(metrics, event, None, now=NOW)
        )
        self.assertFalse(
            gateway._check_ts_plausibility(metrics, event, -1, now=NOW)
        )
        self.assertEqual(0, metrics.window["warnings"])

    def test_ts_inside_the_window_does_not_warn(self):
        metrics = gateway.GatewayMetrics(interval_sec=30, emit=False)
        event = state_event("2026-08-03T11:59:00Z")
        self.assertFalse(
            gateway._check_ts_plausibility(metrics, event, ONE_HOUR_MS, now=NOW)
        )
        self.assertEqual(0, metrics.window["warnings"])

    def test_ts_before_the_window_warns_direction_past(self):
        metrics = gateway.GatewayMetrics(interval_sec=30, emit=False)
        event = state_event("2025-01-17T14:40:00Z")
        self.assertTrue(
            gateway._check_ts_plausibility(
                metrics, event, ONE_HOUR_MS, now=NOW, event_id="evt-1", producer="prod-1"
            )
        )
        self.assertEqual(1, metrics.window["warnings"])
        self.assertEqual({"EVENT_TS_IMPLAUSIBLE": 1}, metrics.window["warning_codes"])

    def test_ts_after_the_window_warns_direction_future(self):
        metrics = gateway.GatewayMetrics(interval_sec=30, emit=False)
        event = state_event("2027-01-17T14:40:00Z")
        self.assertTrue(
            gateway._check_ts_plausibility(metrics, event, ONE_HOUR_MS, now=NOW)
        )
        self.assertEqual({"EVENT_TS_IMPLAUSIBLE": 1}, metrics.window["warning_codes"])

    def test_metrics_record_carries_direction_and_delta(self):
        logger_records = []

        class _ListLogger:
            def write(self, record):
                logger_records.append(record)

        metrics = gateway.GatewayMetrics(interval_sec=30, emit=False, logger=_ListLogger())
        event = state_event("2025-01-17T14:40:00Z")
        gateway._check_ts_plausibility(
            metrics, event, ONE_HOUR_MS, now=NOW, event_id="evt-9", producer="prod-9"
        )
        record = logger_records[-1]
        self.assertEqual("warning", record["type"])
        self.assertEqual("EVENT_TS_IMPLAUSIBLE", record["code"])
        self.assertEqual("evt-9", record["event_id"])
        self.assertEqual("prod-9", record["producer"])
        self.assertIn("'direction': 'past'", record["details"])

    def test_missing_metrics_is_a_noop(self):
        event = state_event("0001-01-01T00:00:00Z")
        self.assertFalse(
            gateway._check_ts_plausibility(None, event, ONE_HOUR_MS, now=NOW)
        )

    def test_unparsable_ts_is_a_noop_not_a_crash(self):
        metrics = gateway.GatewayMetrics(interval_sec=30, emit=False)
        for bad_ts in ("not-a-timestamp", None, "2025-01-17T14:40:00-05:00"):
            with self.subTest(ts=bad_ts):
                event = state_event(bad_ts if bad_ts is not None else "2025-01-17T14:40:00Z")
                event["event"]["ts"] = bad_ts
                self.assertFalse(
                    gateway._check_ts_plausibility(metrics, event, ONE_HOUR_MS, now=NOW)
                )
        self.assertEqual(0, metrics.window["warnings"])

    def test_default_now_falls_back_to_wall_clock(self):
        # No `now` passed: an event stamped far in the past against a small
        # horizon must still warn against the real wall clock.
        metrics = gateway.GatewayMetrics(interval_sec=30, emit=False)
        event = state_event("2000-01-01T00:00:00Z")
        self.assertTrue(
            gateway._check_ts_plausibility(metrics, event, ONE_HOUR_MS)
        )


class TsPlausibilitySettingsTest(unittest.TestCase):
    """Config/CLI wiring, mirroring
    test_warn_datagram_bytes_setting_default_config_and_cli."""

    def test_default_is_enabled_at_the_documented_24_hour_horizon(self):
        with mock.patch("sys.argv", ["gateway.py", "--profile", "H"]):
            args = gateway.parse_args()
        settings = gateway.build_settings(ROOT, args, {})
        self.assertEqual(
            gateway.DEFAULT_TS_PLAUSIBILITY_HORIZON_MS,
            settings["ts_plausibility_horizon_ms"],
        )
        self.assertEqual(24 * 60 * 60 * 1000, settings["ts_plausibility_horizon_ms"])

    def test_config_overrides_the_default(self):
        with mock.patch("sys.argv", ["gateway.py", "--profile", "H"]):
            args = gateway.parse_args()
        settings = gateway.build_settings(
            ROOT, args, {"ts_plausibility_horizon_ms": 5000}
        )
        self.assertEqual(5000, settings["ts_plausibility_horizon_ms"])

    def test_explicit_zero_in_config_disables_and_is_not_reset_to_default(self):
        with mock.patch("sys.argv", ["gateway.py", "--profile", "H"]):
            args = gateway.parse_args()
        settings = gateway.build_settings(
            ROOT, args, {"ts_plausibility_horizon_ms": 0}
        )
        self.assertEqual(0, settings["ts_plausibility_horizon_ms"])

    def test_cli_overrides_config(self):
        with mock.patch(
            "sys.argv",
            ["gateway.py", "--profile", "H", "--ts-plausibility-horizon-ms", "900"],
        ):
            args = gateway.parse_args()
        settings = gateway.build_settings(
            ROOT, args, {"ts_plausibility_horizon_ms": 5000}
        )
        self.assertEqual(900, settings["ts_plausibility_horizon_ms"])


class TsPlausibilityEndToEndTest(unittest.TestCase):
    """Through the full gateway pipeline: forwarded either way, never
    escalated by strict_validation, on any zmeta_version."""

    @classmethod
    def setUpClass(cls):
        cls.validator = validators.load_schema(
            ROOT / "schema" / "zmeta-event-1.0.schema.json"
        )
        cls.policy = validators.load_policy(ROOT / "policy")

    def _process(self, event, **kwargs):
        raw = json.dumps(event).encode("utf-8")
        metrics = gateway.GatewayMetrics(interval_sec=30, emit=False)
        out = gateway.process_message(
            raw, self.validator, self.policy, "L", {}, "json", metrics=metrics, **kwargs
        )
        return out, metrics

    def test_a_grossly_stale_ts_is_forwarded_unchanged_and_flagged_in_metrics(self):
        event = state_event("2025-01-17T14:40:00Z")
        out, metrics = self._process(
            event, now=NOW, ts_plausibility_horizon_ms=ONE_HOUR_MS
        )
        self.assertEqual(1, len(out))
        self.assertEqual(event, out[0])
        self.assertEqual(1, metrics.window["warnings"])
        self.assertEqual({"EVENT_TS_IMPLAUSIBLE": 1}, metrics.window["warning_codes"])

    def test_a_ts_inside_the_window_is_forwarded_with_no_warning(self):
        event = state_event("2026-08-03T11:59:00Z")
        out, metrics = self._process(
            event, now=NOW, ts_plausibility_horizon_ms=ONE_HOUR_MS
        )
        self.assertEqual(1, len(out))
        self.assertEqual(0, metrics.window["warnings"])

    def test_strict_validation_does_not_escalate_the_plausibility_warning(self):
        """This check is observability, not an escalatable policy decision:
        strict_validation must not turn a flagged event into a drop."""
        event = state_event("2025-01-17T14:40:00Z")
        out, metrics = self._process(
            event,
            now=NOW,
            ts_plausibility_horizon_ms=ONE_HOUR_MS,
            strict_validation=True,
        )
        self.assertEqual(1, len(out))
        self.assertEqual("STATE_EVENT", out[0]["event"]["event_type"])
        self.assertEqual(1, metrics.window["warnings"])
        self.assertEqual(0, metrics.window["violations"])

    def test_disabled_by_default_zero_never_flags_a_stale_event(self):
        event = state_event("2025-01-17T14:40:00Z")
        out, metrics = self._process(event, now=NOW, ts_plausibility_horizon_ms=0)
        self.assertEqual(1, len(out))
        self.assertEqual(0, metrics.window["warnings"])

    def test_runs_on_the_1_1_0_branch_too(self):
        """Runtime, not schema: the check applies on ANY zmeta_version."""
        validator_11 = validators.load_schema(
            ROOT / "schema" / "zmeta-event-1.1.0.schema.json"
        )
        event = state_event("2025-01-17T14:40:00Z", version="1.1.0")
        raw = json.dumps(event).encode("utf-8")
        metrics = gateway.GatewayMetrics(interval_sec=30, emit=False)
        out = gateway.process_message(
            raw,
            validator_11,
            self.policy,
            "L",
            {},
            "json",
            metrics=metrics,
            now=NOW,
            ts_plausibility_horizon_ms=ONE_HOUR_MS,
        )
        self.assertEqual(1, len(out))
        self.assertEqual({"EVENT_TS_IMPLAUSIBLE": 1}, metrics.window["warning_codes"])


if __name__ == "__main__":
    unittest.main()
