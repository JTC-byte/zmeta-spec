"""X1-01: event.ts is constrained by structural calendar shape, not just "Z$".

JSON Schema `format: date-time` is annotation-only in this stack (no
format-checker library backs it), so before this change the only gate on
`event.ts` was the pattern `Z$` -- anything ending in the letter Z passed,
including a 14-digit corruption that decodes to year 0001. Demonstrated live
on the AIS ingress path (see adapters/ingress/ais/ais_to_zmeta.py).

The fix lives at the ADJUDICATED layer: schema/zmeta-event-1.1.0.schema.json
`$defs/utcDateTime` gains a regex that enforces structural calendar SHAPE
(year 1970-2999, month 01-12, day 01-31, hour 00-23, minute/second 00-59,
optional fractional seconds, trailing Z). It is deliberately NOT a full
calendar validator -- Feb 30 still passes, because a regex cannot know which
months have 30 vs 31 days. Cross-field calendar and cross-event plausibility
is policy/runtime enforcement (contract 5.7); see
test_ts_plausibility_window.py for that half.

The locked v1.0 schema is out of scope entirely and MUST NOT change: moving
its bytes would fail test_v1_lock_baseline.py, which is the correct outcome.
"""

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

try:
    import jsonschema
except ImportError:  # pragma: no cover - exercised only if jsonschema is absent
    jsonschema = None


def rf_observation(ts):
    return {
        "zmeta_version": "1.1.0",
        "event": {
            "event_id": "019c2b5c-c045-7222-be17-463750a407f4",
            "event_type": "OBSERVATION_EVENT",
            "event_subtype": "RF",
            "ts": ts,
        },
        "source": {
            "platform_id": "sensor-node-01",
            "node_role": "EDGE",
            "producer": "rf-sensor-01",
        },
        "payload": {
            "modality": "RF",
            "features": {
                "center_freq_hz": 2450000000,
                "bandwidth_hz": 20000000,
                "power_dbm": -35.2,
            },
        },
    }


@unittest.skipIf(jsonschema is None, "jsonschema is not installed")
class UtcDateTimePatternTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads(
            (ROOT / "schema" / "zmeta-event-1.1.0.schema.json").read_text(
                encoding="utf-8"
            )
        )
        cls.schema_v10 = json.loads(
            (ROOT / "schema" / "zmeta-event-1.0.schema.json").read_text(
                encoding="utf-8"
            )
        )
        cls.validator = jsonschema.Draft202012Validator(cls.schema)
        cls.validator_v10 = jsonschema.Draft202012Validator(cls.schema_v10)

    def assert_valid(self, ts):
        errors = list(self.validator.iter_errors(rf_observation(ts)))
        self.assertEqual([], errors, errors[0].message if errors else "")

    def assert_invalid(self, ts):
        errors = list(self.validator.iter_errors(rf_observation(ts)))
        self.assertTrue(errors, f"{ts!r} validated but must not")

    # --- the corruption class this change exists to kill --------------

    def test_year_0001_corruption_is_refused(self):
        """The live-demonstrated AIS-path defect: a 14-digit corruption
        that decodes to year 0001 must no longer pass."""
        self.assert_invalid("0001-01-01T00:00:00Z")

    def test_month_88_corruption_is_refused(self):
        self.assert_invalid("2026-88-03T12:00:00Z")

    def test_year_before_the_1970_floor_is_refused(self):
        self.assert_invalid("1969-12-31T23:59:59Z")

    def test_year_after_the_2999_ceiling_is_refused(self):
        self.assert_invalid("3000-01-01T00:00:00Z")

    def test_day_32_is_refused(self):
        self.assert_invalid("2026-08-32T12:00:00Z")

    def test_hour_24_is_refused(self):
        self.assert_invalid("2026-08-03T24:00:00Z")

    def test_minute_60_is_refused(self):
        self.assert_invalid("2026-08-03T23:60:00Z")

    def test_second_60_is_refused(self):
        self.assert_invalid("2026-08-03T23:59:60Z")

    def test_missing_trailing_z_is_still_refused(self):
        self.assert_invalid("2026-08-03T12:00:00")
        self.assert_invalid("2026-08-03T12:00:00-05:00")

    # --- non-vacuity: real timestamps in real shapes still validate ---

    def test_ordinary_timestamps_still_validate(self):
        for ts in (
            "1970-01-01T00:00:00Z",
            "2026-08-03T12:00:00Z",
            "2026-08-03T12:00:00.123Z",
            "2999-12-31T23:59:59Z",
        ):
            with self.subTest(ts=ts):
                self.assert_valid(ts)

    def test_leading_zero_day_and_month_still_validate(self):
        self.assert_valid("2026-01-05T00:00:00Z")

    # --- the documented boundary: not a calendar validator -------------

    def test_february_30_is_structurally_shaped_and_still_passes(self):
        """Documented boundary: the pattern enforces SHAPE, not the calendar.
        A regex cannot know which months hold 30 vs 31 days, and the schema
        description says so; this pins that the boundary is real, not just
        asserted in prose."""
        self.assert_valid("2026-02-30T12:00:00Z")

    def test_boundary_is_documented_in_the_description(self):
        description = self.schema["$defs"]["utcDateTime"]["description"]
        self.assertIn("NOT a full calendar validator", description)

    # --- the locked v1.0 branch is untouched ---------------------------

    def test_the_v10_schema_still_accepts_the_old_permissive_shape(self):
        """The locked kernel is out of scope entirely: a v1.0 event with a
        year-0001 ts still validates under the (unchanged) v1.0 schema,
        because touching it is not this change's business."""
        event = rf_observation("0001-01-01T00:00:00Z")
        event["zmeta_version"] = "1.0"
        errors = list(self.validator_v10.iter_errors(event))
        self.assertEqual([], errors, errors[0].message if errors else "")


if __name__ == "__main__":
    unittest.main()
