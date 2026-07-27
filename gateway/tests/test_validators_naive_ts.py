"""VW-01 pins: the validators' own naive-timestamp arm.

Python's ``fromisoformat`` accepts date-only ("1969-12-31") and ISO-week
("2026-W01-1") shapes and silently ignores an appended "+00:00", so
"1969-12-31Z" and "2026-W01-1Z" satisfy the schema's ``Z$`` gate yet parse
NAIVE on Python 3.14. Before the fix, a naive datetime escaped
``_parse_utc_z`` and every downstream comparison/subtraction raised
mixed naive/aware TypeError into the receive loop's last-resort guard —
a whole datagram dropped as a generic INTERNAL_ERROR.

The class closes at the seam: ``_parse_utc_z`` treats a naive parse as a
failed parse (returns its documented cannot-parse signal, None), so a
gate-clean-but-naive ts takes the SAME arm every caller already has for an
unparseable ts: timing-status replacement proceeds, the freshness gate
passes through with no violation, the RF-window check is skipped.
``_format_utc_z`` refuses naive datetimes for the same reason — calling
``.astimezone()`` on a naive value asks the platform (host-local
reinterpretation, or OSError pre-epoch on Windows).
"""

import importlib.util
import unittest
from datetime import datetime, timezone
from pathlib import Path

from zmeta_uuid import uuid7


ROOT = Path(__file__).resolve().parents[2]
VALIDATORS_PATH = ROOT / "gateway" / "src" / "validators.py"
spec = importlib.util.spec_from_file_location("zmeta_validators", VALIDATORS_PATH)
validators = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validators)


# Gate-clean naive shapes: satisfy the schema's Z$ pattern, parse naive
# via fromisoformat on this interpreter.
NAIVE_DATE_ONLY = "1969-12-31Z"
NAIVE_WEEK_DATE = "2026-W01-1Z"
UNPARSEABLE = "not-a-timestampZ"
AWARE = "2026-07-27T12:00:00Z"


def time_status(ts, *, sync_state="LOCKED", est_error_ms=1):
    return {
        "zmeta_version": "1.0",
        "event": {
            "event_id": str(uuid7()),
            "event_type": "SYSTEM_EVENT",
            "event_subtype": "TIME_STATUS",
            "ts": ts,
        },
        "source": {
            "platform_id": "node-01",
            "node_role": "GATEWAY",
            "producer": "sensorops",
        },
        "payload": {
            "system_type": "TIME_STATUS",
            "state": sync_state,
            "metrics": {
                "time_source": "GPS_PPS",
                "sync_state": sync_state,
                "est_error_ms": est_error_ms,
                "last_sync_ts": ts,
            },
        },
    }


def state_event(ts):
    return {
        "zmeta_version": "1.0",
        "event": {
            "event_id": str(uuid7()),
            "event_type": "STATE_EVENT",
            "event_subtype": "TRACK_STATE",
            "ts": ts,
        },
        "source": {
            "platform_id": "node-01",
            "node_role": "GATEWAY",
            "producer": "sensorops",
        },
        "profile": "H",
        "payload": {
            "track_id": "track-1",
            "geo": {"lat": 34.0, "lon": -118.0, "alt_m": 100.0},
            "valid_for_ms": 1000,
        },
        "confidence": 0.8,
        "lineage": {"based_on": [str(uuid7())]},
    }


def rf_observation(ts, t_start, t_end):
    return {
        "zmeta_version": "1.0",
        "event": {
            "event_id": str(uuid7()),
            "event_type": "OBSERVATION_EVENT",
            "event_subtype": "RF_DETECTION",
            "ts": ts,
        },
        "source": {
            "platform_id": "node-01",
            "node_role": "EDGE_SENSOR",
            "producer": "sensorops",
        },
        "payload": {"modality": "RF", "t_start": t_start, "t_end": t_end},
    }


class NaiveTimestampSeamTest(unittest.TestCase):
    """_parse_utc_z / _format_utc_z: naive is a failed parse, never a value."""

    def test_naive_date_only_shape_refused(self):
        self.assertIsNone(validators._parse_utc_z(NAIVE_DATE_ONLY))

    def test_naive_week_date_shape_refused(self):
        self.assertIsNone(validators._parse_utc_z(NAIVE_WEEK_DATE))

    def test_aware_control_still_parses(self):
        parsed = validators._parse_utc_z(AWARE)
        self.assertEqual(
            datetime(2026, 7, 27, 12, 0, 0, tzinfo=timezone.utc), parsed
        )
        self.assertIsNotNone(parsed.tzinfo)

    def test_aware_millisecond_control_still_parses(self):
        parsed = validators._parse_utc_z("2026-07-27T12:00:00.250Z")
        self.assertEqual(
            datetime(2026, 7, 27, 12, 0, 0, 250000, tzinfo=timezone.utc), parsed
        )

    def test_format_refuses_naive_datetime(self):
        # Pre-fix this called .astimezone() on the naive value: host-local
        # reinterpretation, or OSError pre-epoch on Windows. Refusal is the
        # documented cannot-format signal, and it must not raise.
        self.assertIsNone(validators._format_utc_z(datetime(1969, 12, 31)))

    def test_format_aware_control_unchanged(self):
        self.assertEqual(
            "2026-07-27T12:00:00Z",
            validators._format_utc_z(
                datetime(2026, 7, 27, 12, 0, 0, tzinfo=timezone.utc)
            ),
        )


class NaiveTimestampValidatePathTest(unittest.TestCase):
    """Public validate path: naive-Z takes the exact unparseable-ts arm."""

    @classmethod
    def setUpClass(cls):
        cls.policy = validators.load_policy(ROOT / "policy")
        cls.severity_map = cls.policy["violation_severities"]
        cls.semantics = cls.policy["semantics"]
        cls.freshness = cls.policy["timing_freshness"]
        cls.schema = validators.load_schema(
            ROOT / "schema" / "zmeta-event-1.0.schema.json"
        )

    def _timing(self, event, state):
        return validators.validate_timing_quality(
            event,
            self.semantics,
            state=state,
            severity_map=self.severity_map,
            timing_freshness_policy=self.freshness,
            profile="H",
        )

    def test_naive_shapes_are_gate_clean(self):
        # Documented precondition, not the pin: these shapes pass the schema
        # gate, which is exactly why the parse seam must refuse them itself.
        for shape in (NAIVE_DATE_ONLY, NAIVE_WEEK_DATE):
            ok, violations = validators.validate_schema(
                state_event(shape), self.schema, self.severity_map
            )
            self.assertTrue(ok, violations)

    def test_record_timing_naive_status_is_not_recorded(self):
        # Pre-fix: TypeError("can't compare offset-naive and offset-aware
        # datetimes") out of _should_replace_timing_status. The first fix
        # routed naive into the replacement path - an unreadable ts
        # REPLACED the good aware one, poisoning the source's latest
        # (attack finding, same day). Now an unorderable status is never
        # recorded at all: the aware latest survives verbatim.
        state = validators.ValidationState()
        state.record_timing(time_status(AWARE))
        state.record_timing(time_status(NAIVE_DATE_ONLY))
        _key, status = state.get_timing(state_event(AWARE))
        self.assertEqual(AWARE, status["_event_ts"])

    def test_freshness_naive_event_ts_matches_unparseable_disposition(self):
        # Pre-fix: TypeError("can't subtract ...") at the freshness
        # subtraction. Post-fix: the same (ok, violations) the gate already
        # returns for an unparseable ts - pass-through, no violation.
        state = validators.ValidationState()
        state.record_timing(time_status(AWARE))
        unparseable_event = state_event(UNPARSEABLE)
        control = self._timing(unparseable_event, state)
        self.assertEqual((True, []), control)

        for shape in (NAIVE_DATE_ONLY, NAIVE_WEEK_DATE):
            result = self._timing(state_event(shape), state)
            self.assertEqual(control, result)

    def test_freshness_naive_status_is_missing_not_silently_fresh(self):
        # The mirror arm: a RECORDED status carrying a naive ts used to
        # participate silently in freshness adjudication. It is now never
        # recorded, so the source takes EXACTLY the disposition of a source
        # that never sent a TIME_STATUS - the existing, loud MISSING arm -
        # pinned by equality against a never-recorded control.
        recorded = validators.ValidationState()
        recorded.record_timing(time_status(NAIVE_DATE_ONLY))
        control = validators.ValidationState()
        event = state_event(AWARE)
        self.assertEqual(
            self._timing(event, control), self._timing(event, recorded)
        )

    def test_freshness_aware_controls_still_enforce(self):
        # The fix must not widen the None arm: aware timestamps still parse,
        # so the stale gate still fires.
        state = validators.ValidationState()
        state.record_timing(time_status("2026-07-27T12:00:00Z"))
        ok, violations = self._timing(state_event("2026-07-27T12:00:11Z"), state)
        self.assertFalse(ok)
        self.assertEqual("TIMING_STATUS_STALE", violations[0]["code"])

    def test_rf_window_mixed_naive_aware_does_not_raise(self):
        # Pre-fix: TypeError("can't subtract ...") in the RF-window midpoint
        # arithmetic. Post-fix: the window is unresolvable, so the check is
        # skipped - the same arm an unparseable t_start already takes.
        ok, violations = validators.validate_semantics(
            rf_observation(AWARE, NAIVE_DATE_ONLY, "2026-07-27T12:00:02Z"),
            self.semantics,
            severity_map=self.severity_map,
        )
        self.assertTrue(ok, violations)
        self.assertEqual([], violations)

    def test_rf_window_naive_event_ts_does_not_raise(self):
        ok, violations = validators.validate_semantics(
            rf_observation(
                NAIVE_DATE_ONLY, "2026-07-27T12:00:00Z", "2026-07-27T12:00:02Z"
            ),
            self.semantics,
            severity_map=self.severity_map,
        )
        self.assertTrue(ok, violations)
        self.assertEqual([], violations)

    def test_rf_window_aware_control_still_enforces(self):
        # All-aware mismatch still refuses: the gate itself is intact.
        ok, violations = validators.validate_semantics(
            rf_observation(
                "2026-07-27T12:00:10Z", "2026-07-27T12:00:00Z", "2026-07-27T12:00:02Z"
            ),
            self.semantics,
            severity_map=self.severity_map,
        )
        self.assertFalse(ok)
        self.assertEqual("RF_WINDOW_MIDPOINT_MISMATCH", violations[0]["code"])


if __name__ == "__main__":
    unittest.main()
