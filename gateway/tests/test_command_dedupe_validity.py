"""A duplicate COMMAND_EVENT is not forwarded a second time while the forwarded copy can execute.

Contract 13.2: "Duplicate COMMAND_EVENTs MUST NOT be forwarded for execution a
second time." The gateway used to hold a command's task_id for the smaller of
its valid_for_ms and 300 s, so the shipped example command, valid for 600 s,
was forwarded again when its duplicate arrived at 301 s.

What is pinned here:

- A task_id is held from the moment its command is admitted until that
  command's validity ends, read the widest way (valid_for_ms after the latest
  of receipt, event.ts and valid_from_ts), plus a fixed margin for clock
  disagreement.
- A later copy of a held command is a duplicate and changes nothing. It
  neither shortens nor lengthens the hold.
- A command is refused, not forwarded, when the gateway cannot hold its
  task_id: the hold would exceed the maximum, a validity anchor is present
  and unreadable, or the cache is full. A refused command is not held.
- A command refused by an earlier check does not claim its task_id, and a
  command that was admitted and then did not leave the gateway gives it back:
  replaced by a diagnostic, not encodable, not sent, or lost to an exception.
- Both limits are settings with ceilings, and main() hands them to the cache.

What this file does not prove. The cache is in memory, so a gateway restart
forgets every held id. A command whose validity has already ended is not
refused. A task_id is released when its hold ends, and the same task_id is
then admitted as a new command; contract 13.2 sets no time bound on "a second
time", so that release is a reading the maintainer has not ruled on (doctrine
E1-06), and the tests that assert a release pin the behavior, not the ruling.

A note for whoever edits these tests: every probe that re-sends a command is
itself a copy. The cache ignores copies, and CopiesChangeNothingTest exists
to keep it that way; a cache that lengthened a hold on each copy would make
most duplicate assertions here pass for the wrong reason.
"""

import contextlib
import copy
import importlib.util
import io
import json
import math
import os
import time
import unittest
from datetime import datetime, timedelta, timezone, tzinfo
from pathlib import Path
from unittest import mock

from zmeta_uuid import uuid7


ROOT = Path(__file__).resolve().parents[2]


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validators = _load("zmeta_validators_dedupe", ROOT / "gateway" / "src" / "validators.py")
gateway = _load("zmeta_gateway_dedupe", ROOT / "gateway" / "src" / "gateway.py")

WALL = datetime(2025, 1, 17, 14, 32, 10, tzinfo=timezone.utc)
SOURCE = {"platform_id": "comms-node-1", "node_role": "GATEWAY", "producer": "sensorops"}
MARGIN_S = 60
DAY_MS = 24 * 60 * 60 * 1000
LANES = (
    ("1.0 lane", "zmeta-event-1.0.schema.json", ("1.0",)),
    ("1.1.0 lane", "zmeta-event-1.1.0.schema.json", ("1.1.0",)),
    ("union", "zmeta-event.schema.json", ("1.0", "1.1.0")),
)

CAPACITY_REASON = "command dedupe capacity reached"
TOO_LONG_REASON = "command validity exceeds the dedupe hold limit"
UNREADABLE_REASON = "command validity anchor is not a readable UTC instant"
# Schema-valid on both lanes, and not an instant this gateway can read.
IMPOSSIBLE_DATE = "2025-02-30T00:00:00Z"


def z(moment):
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_z(value):
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def timing(ts):
    return {
        "time_source": "GPS_PPS",
        "sync_state": "LOCKED",
        "est_error_ms": 1,
        "last_sync_ts": z(ts - timedelta(seconds=20)),
    }


def shipped_command():
    """The first COMMAND_EVENT of the shipped command examples, valid for 600 s."""
    with open(ROOT / "examples" / "zmeta-command-examples.jsonl", "r", encoding="utf-8") as handle:
        for line in handle:
            event = json.loads(line)
            if event["event"]["event_type"] == "COMMAND_EVENT":
                return event
    raise AssertionError("no shipped command example")


def command(task_id, valid_for_ms=60000, valid_from_ts=None, ts=WALL, source=None, version="1.0"):
    payload = {
        "task_id": task_id,
        "task_type": "GOTO",
        "target_geo": {"lat": 34.0101, "lon": -118.0101},
        "valid_for_ms": valid_for_ms,
        "requires_deconfliction": True,
        "timing_quality": timing(ts),
    }
    if valid_from_ts is not None:
        payload["valid_from_ts"] = valid_from_ts
    return {
        "zmeta_version": version,
        "event": {
            "event_id": str(uuid7()),
            "event_type": "COMMAND_EVENT",
            "event_subtype": "GOTO",
            "ts": z(ts),
        },
        "source": dict(source or SOURCE),
        "profile": "L",
        "payload": payload,
    }


def time_status(ts=WALL - timedelta(seconds=20), source=None, version="1.0"):
    if isinstance(ts, str):
        stamp, metrics = ts, dict(timing(WALL), last_sync_ts=ts)
    else:
        stamp, metrics = z(ts), dict(timing(ts), last_sync_ts=z(ts))
    return {
        "zmeta_version": version,
        "event": {
            "event_id": str(uuid7()),
            "event_type": "SYSTEM_EVENT",
            "event_subtype": "TIME_STATUS",
            "ts": stamp,
        },
        "source": dict(source or SOURCE),
        "payload": {"system_type": "TIME_STATUS", "state": "LOCKED", "metrics": metrics},
    }


class NoOffset(tzinfo):
    """A time zone that reports no offset. Python counts such a datetime as naive."""

    def utcoffset(self, _dt):
        return None

    def dst(self, _dt):
        return None

    def tzname(self, _dt):
        return None


@contextlib.contextmanager
def a_local_zone_that_is_not_utc(test):
    """Run the body with the process's local zone five hours behind UTC.

    "A naive `now` is read as UTC" can only be told apart from "read as
    local time" where local time is not UTC. Continuous integration runs in
    UTC, so the zone is set for the test where the platform allows it; where
    it does not, a host whose local zone is UTC skips, visibly, instead of
    passing for the wrong reason.
    """
    if hasattr(time, "tzset"):
        saved = os.environ.get("TZ")
        os.environ["TZ"] = "EST+05"
        time.tzset()
        try:
            yield
        finally:
            if saved is None:
                os.environ.pop("TZ", None)
            else:
                os.environ["TZ"] = saved
            time.tzset()
    else:
        if WALL.replace(tzinfo=None).astimezone().utcoffset() == timedelta(0):
            test.skipTest("the local zone is UTC and this platform cannot change it for one test")
        yield


class Clock:
    """A settable stand-in for the gateway module's monotonic clock."""

    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


class DedupeCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.validator = validators.load_schema(ROOT / "schema" / "zmeta-event-1.0.schema.json")
        cls.policy = validators.load_policy(ROOT / "policy")

    def setUp(self):
        self.clock = Clock()
        patcher = mock.patch.object(gateway.time, "monotonic", self.clock)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.cache = gateway.TaskDedupeCache()
        self.state = validators.ValidationState()
        self.state.record(time_status())

    def send(self, event, at_s, cache=None, validator=None, wall=WALL, **kwargs):
        """Hand `event` to process_message `at_s` seconds after `wall`, on both clocks."""
        validator = validator or self.validator
        self.assertEqual([], list(validator.iter_errors(event)), "input must be schema-valid")
        self.clock.now = 1000.0 + at_s
        return gateway.process_message(
            json.dumps(event).encode("utf-8"),
            validator,
            self.policy,
            "L",
            self.cache if cache is None else cache,
            "json",
            timing_state=self.state,
            now=wall + timedelta(seconds=at_s),
            **kwargs,
        )

    def assert_forwarded(self, event, out):
        self.assertTrue(out, "nothing came out")
        self.assertEqual(event, out[0])
        for extra in out[1:]:
            # A warning may ride behind a forwarded event; a task
            # acknowledgement behind one would mean it was also refused.
            self.assertNotEqual("TASK_ACK", extra["event"]["event_subtype"], extra)

    def assert_duplicate(self, event, out):
        self.assertEqual(1, len(out), out)
        ack = out[0]
        self.assertEqual("SYSTEM_EVENT", ack["event"]["event_type"])
        self.assertEqual("TASK_ACK", ack["event"]["event_subtype"])
        self.assertEqual("DUPLICATE_IGNORED", ack["payload"]["state"])
        metrics = ack["payload"]["metrics"]
        self.assertEqual("TASK_DUPLICATE", metrics["reason_code"])
        self.assertEqual(event["payload"]["task_id"], metrics["task_id"])
        self.assertEqual(event["event"]["event_id"], metrics["original_event_id"])
        return ack

    def assert_refused(self, event, out, reason, limit_key, limit, validator=None):
        self.assertEqual(1, len(out), out)
        refusal = out[0]
        self.assertNotEqual(event, refusal)
        self.assertEqual("SYSTEM_EVENT", refusal["event"]["event_type"])
        self.assertEqual("TASK_ACK", refusal["event"]["event_subtype"])
        self.assertEqual("TASK_ACK", refusal["payload"]["system_type"])
        self.assertEqual("REJECTED", refusal["payload"]["state"])
        metrics = refusal["payload"]["metrics"]
        self.assertEqual("TASK_REJECTED", metrics["reason_code"])
        self.assertEqual(reason, metrics["reason"])
        self.assertEqual(limit, metrics[limit_key])
        self.assertEqual(event["payload"]["task_id"], metrics["task_id"])
        self.assertEqual(event["event"]["event_id"], metrics["original_event_id"])
        self.assertEqual(event["source"]["producer"], metrics["source_producer"])
        self.assertEqual(
            [],
            gateway.validate_outgoing_event(refusal, validator or self.validator, self.policy, "L"),
            "the refusal must pass the gateway's own outgoing check",
        )
        return refusal


class HoldCoversTheValidityTest(DedupeCase):
    def test_the_shipped_600_s_command_is_held_for_its_validity_and_no_longer(self):
        cmd = shipped_command()
        self.assertEqual(600000, cmd["payload"]["valid_for_ms"])
        self.assertNotIn("valid_from_ts", cmd["payload"])
        self.assertEqual(SOURCE, cmd["source"])
        # Received at the command's own ts, so the hold is the 600 s validity
        # plus the margin and nothing else. (Received earlier, the lead to
        # event.ts would carry the hold and hide a broken validity.) The
        # shipped command carries no per-event timing quality, so its node's
        # TIME_STATUS must be current at that ts.
        anchor = parse_z(cmd["event"]["ts"])
        self.state.record(time_status(cmd["event"]["ts"]))
        self.assert_forwarded(cmd, self.send(cmd, 0, wall=anchor))
        for at_s in (10, 301, 599, 600 + MARGIN_S - 1):
            with self.subTest(at_s=at_s):
                self.assert_duplicate(cmd, self.send(cmd, at_s, wall=anchor))
        self.assert_forwarded(cmd, self.send(cmd, 600 + MARGIN_S + 1, wall=anchor))

    def test_a_short_command_is_held_through_its_validity_and_the_margin_then_released(self):
        # The release pins the behavior, not a ruling: contract 13.2 sets no
        # time bound on "a second time" (doctrine E1-06).
        cmd = command("task-short", valid_for_ms=60000)
        self.assert_forwarded(cmd, self.send(cmd, 0))
        for at_s in (1, 59, 61, 60 + MARGIN_S - 1):
            with self.subTest(at_s=at_s):
                self.assert_duplicate(cmd, self.send(cmd, at_s))
        self.assert_forwarded(cmd, self.send(cmd, 60 + MARGIN_S + 1))

    def test_the_margin_is_one_minute(self):
        self.assertEqual(60000, gateway.COMMAND_HOLD_MARGIN_MS)
        self.assertEqual(MARGIN_S * 1000, gateway.COMMAND_HOLD_MARGIN_MS)

    def test_lead_time_to_valid_from_ts_is_held(self):
        # Valid for 60 s starting 600 s after receipt: executable until 660 s.
        cmd = command("task-lead", valid_for_ms=60000, valid_from_ts=z(WALL + timedelta(seconds=600)))
        self.assert_forwarded(cmd, self.send(cmd, 0))
        for at_s in (61, 121, 301, 659, 660 + MARGIN_S - 1):
            with self.subTest(at_s=at_s):
                self.assert_duplicate(cmd, self.send(cmd, at_s))
        self.assert_forwarded(cmd, self.send(cmd, 660 + MARGIN_S + 1))

    def test_a_future_event_ts_is_held_as_the_validity_anchor(self):
        # Contract 5.1: a command's event.ts is "the command issue time or
        # validity anchor". A consumer that anchors validity there can still
        # execute this command 659 s after the gateway received it.
        ahead = WALL + timedelta(seconds=600)
        self.state.record(time_status(ahead - timedelta(seconds=20)))
        cmd = command("task-future-ts", valid_for_ms=60000, ts=ahead)
        self.assert_forwarded(cmd, self.send(cmd, 0))
        for at_s in (61, 121, 301, 659, 660 + MARGIN_S - 1):
            with self.subTest(at_s=at_s):
                self.assert_duplicate(cmd, self.send(cmd, at_s))
        self.assert_forwarded(cmd, self.send(cmd, 660 + MARGIN_S + 1))

    def test_the_hold_is_measured_to_the_latest_anchor(self):
        hold = gateway.command_hold_ms
        soon, late = z(WALL + timedelta(seconds=100)), z(WALL + timedelta(seconds=600))
        past = z(WALL - timedelta(seconds=600))
        margin = gateway.COMMAND_HOLD_MARGIN_MS
        cases = (
            # (valid_from_ts, event_ts, expected lead in ms)
            (None, None, 0),
            (past, past, 0),
            (late, None, 600000),
            (None, late, 600000),
            (late, soon, 600000),
            (soon, late, 600000),
            (soon, past, 100000),
            (past, soon, 100000),
        )
        for valid_from_ts, event_ts, lead in cases:
            with self.subTest(valid_from_ts=valid_from_ts, event_ts=event_ts):
                payload = {"valid_for_ms": 60000}
                if valid_from_ts is not None:
                    payload["valid_from_ts"] = valid_from_ts
                self.assertEqual(60000 + lead + margin, hold(payload, now=WALL, event_ts=event_ts))
        # The lead shrinks as the gateway's clock approaches the anchor.
        self.assertEqual(
            60000 + 100000 + margin,
            hold({"valid_for_ms": 60000, "valid_from_ts": late}, now=WALL + timedelta(seconds=500)),
        )

    def test_a_lead_is_counted_to_the_millisecond_and_never_rounded_down(self):
        start = z(WALL + timedelta(seconds=10))
        margin = gateway.COMMAND_HOLD_MARGIN_MS
        self.assertEqual(
            60000 + 9500 + margin,
            gateway.command_hold_ms(
                {"valid_for_ms": 60000, "valid_from_ts": start}, now=WALL + timedelta(milliseconds=500)
            ),
        )
        self.assertEqual(
            60000 + 9001 + margin,
            gateway.command_hold_ms(
                {"valid_for_ms": 60000, "valid_from_ts": start}, now=WALL + timedelta(microseconds=999500)
            ),
        )

    def test_the_hold_counts_the_lead_on_the_wall_clock_when_the_caller_gives_no_now(self):
        # The only path main() uses: it never passes `now`.
        start = datetime.now(timezone.utc) + timedelta(seconds=600)
        held = gateway.command_hold_ms({"valid_for_ms": 60000, "valid_from_ts": z(start)})
        self.assertGreaterEqual(held, 60000 + 598000 + gateway.COMMAND_HOLD_MARGIN_MS)
        self.assertLessEqual(held, 60000 + 601000 + gateway.COMMAND_HOLD_MARGIN_MS)

    def test_a_naive_now_is_read_as_utc(self):
        late = z(WALL + timedelta(seconds=600))
        payload = {"valid_for_ms": 60000, "valid_from_ts": late}
        expected = 60000 + 600000 + gateway.COMMAND_HOLD_MARGIN_MS
        with a_local_zone_that_is_not_utc(self):
            self.assertNotEqual(timedelta(0), WALL.replace(tzinfo=None).astimezone().utcoffset())
            self.assertEqual(expected, gateway.command_hold_ms(payload, now=WALL.replace(tzinfo=None)))

    def test_a_now_whose_zone_reports_no_offset_is_read_as_utc(self):
        # Python treats such a datetime as naive: subtracting an aware
        # instant from it raises. It is not enough to test `tzinfo is None`.
        late = z(WALL + timedelta(seconds=600))
        now = WALL.replace(tzinfo=NoOffset())
        self.assertIsNotNone(now.tzinfo)
        self.assertEqual(
            60000 + 600000 + gateway.COMMAND_HOLD_MARGIN_MS,
            gateway.command_hold_ms({"valid_for_ms": 60000, "valid_from_ts": late}, now=now),
        )

    def test_hold_falls_back_for_a_validity_int_cannot_read_or_reads_as_not_positive(self):
        expected = 60000 + gateway.COMMAND_HOLD_MARGIN_MS
        for bad in (None, "x", 0, -5, float("inf"), [1]):
            with self.subTest(valid_for_ms=bad):
                self.assertEqual(expected, gateway.command_hold_ms({"valid_for_ms": bad}, now=WALL))
        self.assertEqual(expected, gateway.command_hold_ms(None, now=WALL))

    def test_the_same_task_id_from_another_platform_or_producer_is_a_duplicate(self):
        # Contract 13.2 keys the dedupe on payload.task_id alone.
        others = (
            dict(SOURCE, platform_id="comms-node-2"),
            dict(SOURCE, producer="retasking-engine"),
        )
        first = command("task-shared", valid_for_ms=600000)
        self.assert_forwarded(first, self.send(first, 0))
        for n, other in enumerate(others, start=1):
            with self.subTest(source=other):
                self.state.record(time_status(source=other))
                second = command("task-shared", valid_for_ms=600000, source=other)
                self.assert_duplicate(second, self.send(second, 5 * n))


class CopiesChangeNothingTest(DedupeCase):
    def test_a_later_copy_with_a_longer_validity_does_not_lengthen_the_hold(self):
        first = command("task-repeat", valid_for_ms=60000)
        longer = command("task-repeat", valid_for_ms=600000)
        self.assert_forwarded(first, self.send(first, 0))
        self.assert_duplicate(longer, self.send(longer, 50))
        self.assert_duplicate(first, self.send(first, 60 + MARGIN_S - 1))
        # The hold was the forwarded copy's: released on its schedule.
        self.assert_forwarded(first, self.send(first, 60 + MARGIN_S + 1))

    def test_a_later_copy_with_a_shorter_validity_does_not_shorten_the_hold(self):
        first = command("task-keep", valid_for_ms=600000)
        shorter = command("task-keep", valid_for_ms=60000)
        self.assert_forwarded(first, self.send(first, 0))
        self.assert_duplicate(shorter, self.send(shorter, 10))
        for at_s in (10 + 60 + MARGIN_S + 1, 300, 600 + MARGIN_S - 1):
            with self.subTest(at_s=at_s):
                self.assert_duplicate(shorter, self.send(shorter, at_s))
        self.assert_forwarded(first, self.send(first, 600 + MARGIN_S + 1))

    def test_a_copy_too_long_to_admit_is_still_a_duplicate_of_a_held_command(self):
        cache = gateway.TaskDedupeCache(max_entries=4, max_hold_ms=180000)
        first = command("task-cap", valid_for_ms=60000)
        huge = command("task-cap", valid_for_ms=10 ** 15)
        unreadable = command("task-cap", valid_from_ts=IMPOSSIBLE_DATE)
        self.assert_forwarded(first, self.send(first, 0, cache=cache))
        self.assert_duplicate(huge, self.send(huge, 10, cache=cache))
        self.assert_duplicate(unreadable, self.send(unreadable, 20, cache=cache))
        self.assert_forwarded(first, self.send(first, 60 + MARGIN_S + 1, cache=cache))

    def test_repeating_held_commands_cannot_keep_the_cache_full(self):
        # The second review's reproduction: when copies lengthened a hold,
        # re-sending held ids kept every slot taken for as long as the
        # copies kept coming, and every new command was refused.
        cache = gateway.TaskDedupeCache(max_entries=2, max_hold_ms=180000)
        held = [command(f"task-held-{n}", valid_for_ms=60000) for n in (1, 2)]
        for cmd in held:
            self.assert_forwarded(cmd, self.send(cmd, 0, cache=cache))
        for at_s in (30, 60, 90, 119):
            for cmd in held:
                refresh = command(cmd["payload"]["task_id"], valid_for_ms=10 ** 15)
                self.assert_duplicate(refresh, self.send(refresh, at_s, cache=cache))
        waiting = command("task-waiting", valid_for_ms=60000)
        self.assert_refused(
            waiting, self.send(waiting, 119, cache=cache), CAPACITY_REASON, "command_dedupe_max_entries", 2
        )
        self.assert_forwarded(waiting, self.send(waiting, 60 + MARGIN_S + 1, cache=cache))


class UnreadableAnchorTest(DedupeCase):
    def test_an_unreadable_anchor_makes_the_hold_infinite_and_is_named(self):
        cases = (
            ({"valid_for_ms": 60000, "valid_from_ts": IMPOSSIBLE_DATE}, None, "payload.valid_from_ts"),
            ({"valid_for_ms": 60000, "valid_from_ts": "2025-01-17T23:59:60Z"}, None, "payload.valid_from_ts"),
            ({"valid_for_ms": 60000, "valid_from_ts": "garbageZ"}, None, "payload.valid_from_ts"),
            ({"valid_for_ms": 60000}, IMPOSSIBLE_DATE, "event.ts"),
            ({"valid_for_ms": 60000}, "garbageZ", "event.ts"),
            ({"valid_for_ms": 60000, "valid_from_ts": 5}, None, "payload.valid_from_ts"),
        )
        for payload, event_ts, name in cases:
            with self.subTest(payload=payload, event_ts=event_ts):
                self.assertEqual(name, gateway.unreadable_command_anchor(payload, event_ts))
                self.assertEqual(math.inf, gateway.command_hold_ms(payload, now=WALL, event_ts=event_ts))
        readable = {"valid_for_ms": 60000, "valid_from_ts": z(WALL)}
        self.assertIsNone(gateway.unreadable_command_anchor(readable, z(WALL)))
        self.assertIsNone(gateway.unreadable_command_anchor({"valid_for_ms": 60000}, None))
        self.assertIsNone(gateway.unreadable_command_anchor(None, None))

    def test_a_command_with_an_unreadable_valid_from_ts_is_refused_not_forwarded(self):
        # Before this refusal the hold fell back to the narrowest reading
        # (valid_for_ms from receipt) and the same task_id was forwarded
        # again while a consumer that reads the date leniently, as October
        # 1 for "September 31", still held the command valid.
        for bad in (IMPOSSIBLE_DATE, "2025-01-17T23:59:60Z", "garbageZ"):
            with self.subTest(valid_from_ts=bad):
                cmd = command(f"task-unreadable-{bad}", valid_for_ms=600000, valid_from_ts=bad)
                metrics = mock.Mock()
                self.assert_refused(
                    cmd, self.send(cmd, 0, metrics=metrics), UNREADABLE_REASON, "anchor", "payload.valid_from_ts"
                )
                metrics.record_violation.assert_called_once_with(
                    "TASK_REJECTED",
                    event_id=cmd["event"]["event_id"],
                    producer="sensorops",
                    details={"reason": UNREADABLE_REASON, "anchor": "payload.valid_from_ts"},
                )
                # Refused again, never "duplicate": nothing was held.
                self.assert_refused(cmd, self.send(cmd, 700), UNREADABLE_REASON, "anchor", "payload.valid_from_ts")

    def test_a_command_with_an_unreadable_event_ts_is_refused_and_the_anchor_is_named(self):
        for bad in (IMPOSSIBLE_DATE, "garbageZ"):
            with self.subTest(event_ts=bad):
                cmd = command(f"task-bad-ts-{bad}", valid_for_ms=600000)
                cmd["event"]["ts"] = bad
                self.assert_refused(cmd, self.send(cmd, 0), UNREADABLE_REASON, "anchor", "event.ts")
                # Its task_id is not held against a corrected copy.
                fixed = command(f"task-bad-ts-{bad}", valid_for_ms=600000)
                self.assert_forwarded(fixed, self.send(fixed, 1))

    def test_a_leap_second_is_refused_where_the_schema_admits_it(self):
        # The 1.0 lane gates timestamps on a trailing Z alone; the 1.1.0 lane
        # refuses second 60 in schema, so only the 1.0 lane reaches here.
        cmd = command("task-leap", valid_for_ms=600000, valid_from_ts="2025-01-17T23:59:60Z")
        self.assert_refused(cmd, self.send(cmd, 0), UNREADABLE_REASON, "anchor", "payload.valid_from_ts")
        lane_1_1_0 = validators.load_schema(ROOT / "schema" / "zmeta-event-1.1.0.schema.json")
        self.assertNotEqual([], list(lane_1_1_0.iter_errors(dict(cmd, zmeta_version="1.1.0"))))


class MaximumHoldTest(DedupeCase):
    def test_the_default_maximum_hold_is_one_day(self):
        self.assertEqual(DAY_MS, gateway.DEFAULT_COMMAND_MAX_HOLD_MS)
        self.assertEqual(DAY_MS, gateway.TaskDedupeCache().max_hold_ms)

    def test_a_command_at_the_maximum_hold_is_forwarded_and_one_past_it_is_refused(self):
        longest = DAY_MS - gateway.COMMAND_HOLD_MARGIN_MS
        at_limit = command("task-at-limit", valid_for_ms=longest)
        self.assert_forwarded(at_limit, self.send(at_limit, 0))
        self.assert_duplicate(at_limit, self.send(at_limit, DAY_MS // 1000 - 1))
        self.assert_forwarded(at_limit, self.send(at_limit, DAY_MS // 1000 + 1))
        past_limit = command("task-past-limit", valid_for_ms=longest + 1)
        self.assert_refused(
            past_limit, self.send(past_limit, 0), TOO_LONG_REASON, "command_max_hold_ms", DAY_MS
        )

    def test_an_enormous_validity_is_refused_without_overflow(self):
        for valid_for_ms in (10 ** 15, 10 ** 400):
            with self.subTest(digits=len(str(valid_for_ms))):
                cmd = command(f"task-huge-{len(str(valid_for_ms))}", valid_for_ms=valid_for_ms)
                self.assert_refused(cmd, self.send(cmd, 0), TOO_LONG_REASON, "command_max_hold_ms", DAY_MS)

    def test_a_validity_that_starts_too_far_ahead_is_refused(self):
        cmd = command("task-far", valid_for_ms=60000, valid_from_ts="9999-12-31T23:59:59Z")
        self.assert_refused(cmd, self.send(cmd, 0), TOO_LONG_REASON, "command_max_hold_ms", DAY_MS)

    def test_a_refused_command_is_not_held_and_takes_no_capacity(self):
        cache = gateway.TaskDedupeCache(max_entries=1, max_hold_ms=180000)
        too_long = command("task-again", valid_for_ms=600000)
        metrics = mock.Mock()
        self.assert_refused(
            too_long, self.send(too_long, 0, cache=cache, metrics=metrics),
            TOO_LONG_REASON, "command_max_hold_ms", 180000,
        )
        metrics.record_violation.assert_called_once_with(
            "TASK_REJECTED",
            event_id=too_long["event"]["event_id"],
            producer="sensorops",
            details={"reason": TOO_LONG_REASON, "command_max_hold_ms": 180000},
        )
        metrics.record_duplicate.assert_not_called()
        # Still refused, never "duplicate": the refusal recorded nothing.
        self.assert_refused(
            too_long, self.send(too_long, 1, cache=cache), TOO_LONG_REASON, "command_max_hold_ms", 180000
        )
        # The one slot is still free, and the same task_id is admitted when
        # it comes back with a validity the gateway can hold.
        reissued = command("task-again", valid_for_ms=60000)
        self.assert_forwarded(reissued, self.send(reissued, 2, cache=cache))

    def test_a_full_cache_clears_within_the_maximum_hold(self):
        # Every hold is finite and no copy lengthens one, so a full cache
        # refuses for at most the maximum hold after its last admission.
        # Before the maximum hold existed, ids held "forever" filled the
        # cache until the gateway was restarted.
        cache = gateway.TaskDedupeCache(max_entries=2, max_hold_ms=180000)
        longest = 180000 - gateway.COMMAND_HOLD_MARGIN_MS
        for n in (1, 2):
            cmd = command(f"task-fill-{n}", valid_for_ms=longest)
            self.assert_forwarded(cmd, self.send(cmd, 0, cache=cache))
        waiting = command("task-waiting", valid_for_ms=60000)
        self.assert_refused(
            waiting, self.send(waiting, 179, cache=cache), CAPACITY_REASON, "command_dedupe_max_entries", 2
        )
        self.assert_forwarded(waiting, self.send(waiting, 181, cache=cache))


class CapacityTest(DedupeCase):
    def test_the_default_capacity_is_4096(self):
        self.assertEqual(4096, gateway.DEFAULT_COMMAND_DEDUPE_MAX_ENTRIES)
        self.assertEqual(4096, gateway.TaskDedupeCache().max_entries)

    def test_a_full_cache_refuses_a_new_command_and_forgets_nothing(self):
        cache = gateway.TaskDedupeCache(max_entries=5)
        held = [command(f"task-{n}", valid_for_ms=600000) for n in range(5)]
        for n, cmd in enumerate(held):
            self.assert_forwarded(cmd, self.send(cmd, n, cache=cache))

        sixth = command("task-5", valid_for_ms=600000)
        metrics = mock.Mock()
        identity = {"producer": "zmeta-gateway", "node_role": "DMZ"}
        out = self.send(sixth, 6, cache=cache, metrics=metrics, gateway_identity=identity)

        refusal = self.assert_refused(sixth, out, CAPACITY_REASON, "command_dedupe_max_entries", 5)
        self.assertEqual("zmeta-gateway", refusal["source"]["producer"])
        self.assertEqual("DMZ", refusal["source"]["node_role"])
        metrics.record_violation.assert_called_once_with(
            "TASK_REJECTED",
            event_id=sixth["event"]["event_id"],
            producer="sensorops",
            details={"reason": CAPACITY_REASON, "command_dedupe_max_entries": 5},
        )
        metrics.record_duplicate.assert_not_called()
        # Nothing was forgotten to make room: every held command still dedupes.
        for cmd in held:
            self.assert_duplicate(cmd, self.send(cmd, 7, cache=cache))
        # The refused command was not recorded, so it is still refused, not "duplicate".
        self.assert_refused(
            sixth, self.send(sixth, 8, cache=cache), CAPACITY_REASON, "command_dedupe_max_entries", 5
        )

    def test_capacity_returns_when_a_held_command_expires(self):
        cache = gateway.TaskDedupeCache(max_entries=1)
        short = command("task-a", valid_for_ms=60000)
        later = command("task-b", valid_for_ms=60000)
        self.assert_forwarded(short, self.send(short, 0, cache=cache))
        self.assert_refused(
            later, self.send(later, 60 + MARGIN_S - 1, cache=cache),
            CAPACITY_REASON, "command_dedupe_max_entries", 1,
        )
        self.assert_forwarded(later, self.send(later, 60 + MARGIN_S + 1, cache=cache))

    def test_a_duplicate_takes_no_capacity(self):
        cache = gateway.TaskDedupeCache(max_entries=2)
        first = command("task-1", valid_for_ms=600000)
        second = command("task-2", valid_for_ms=600000)
        self.assert_forwarded(first, self.send(first, 0, cache=cache))
        for at_s in (1, 2, 3):
            self.assert_duplicate(first, self.send(first, at_s, cache=cache))
        self.assert_forwarded(second, self.send(second, 4, cache=cache))

    def test_the_refusals_are_valid_on_every_lane(self):
        for lane, schema_file, versions in LANES:
            validator = validators.load_schema(ROOT / "schema" / schema_file)
            for version in versions:
                with self.subTest(lane=lane, zmeta_version=version):
                    cache = gateway.TaskDedupeCache(max_entries=1, max_hold_ms=180000)
                    held = command(f"task-held-{version}", version=version)
                    self.assert_forwarded(held, self.send(held, 0, cache=cache, validator=validator))
                    ack = self.assert_duplicate(held, self.send(held, 1, cache=cache, validator=validator))
                    self.assertEqual([], gateway.validate_outgoing_event(ack, validator, self.policy, "L"))
                    extra = command(f"task-extra-{version}", version=version)
                    self.assert_refused(
                        extra, self.send(extra, 2, cache=cache, validator=validator),
                        CAPACITY_REASON, "command_dedupe_max_entries", 1, validator=validator,
                    )
                    too_long = command(f"task-long-{version}", valid_for_ms=600000, version=version)
                    self.assert_refused(
                        too_long, self.send(too_long, 3, cache=cache, validator=validator),
                        TOO_LONG_REASON, "command_max_hold_ms", 180000, validator=validator,
                    )
                    unreadable = command(
                        f"task-unreadable-{version}", valid_from_ts=IMPOSSIBLE_DATE, version=version
                    )
                    self.assert_refused(
                        unreadable, self.send(unreadable, 4, cache=cache, validator=validator),
                        UNREADABLE_REASON, "anchor", "payload.valid_from_ts", validator=validator,
                    )


class DuplicateAcknowledgementTest(DedupeCase):
    def test_a_duplicate_is_acknowledged_and_counted_when_a_metrics_sink_is_present(self):
        # main() always passes a metrics sink; the other process_message
        # duplicate tests in this file pass none.
        cmd = command("task-dup-metrics")
        self.assert_forwarded(cmd, self.send(cmd, 0))
        metrics = mock.Mock()
        self.assert_duplicate(cmd, self.send(cmd, 5, metrics=metrics))
        metrics.record_duplicate.assert_called_once_with(task_id="task-dup-metrics")
        metrics.record_violation.assert_called_once_with(
            "TASK_DUPLICATE", event_id=cmd["event"]["event_id"], producer="sensorops", details="task-dup-metrics"
        )

    def test_the_acknowledgement_names_the_copy_and_carries_the_gateway_identity_and_hash(self):
        first = command("task-dup-names")
        again = command("task-dup-names")
        hashes = {"contract_hash": "c" * 64, "schema_hash": "s" * 64, "policy_hash": "p" * 64}
        self.assert_forwarded(first, self.send(first, 0))
        ack = self.assert_duplicate(
            again,
            self.send(
                again, 5,
                gateway_identity={"producer": "zmeta-gateway", "node_role": "DMZ"},
                contract_hashes=hashes, stamp_contract_hash=True,
            ),
        )
        self.assertNotEqual(first["event"]["event_id"], ack["payload"]["metrics"]["original_event_id"])
        self.assertEqual("zmeta-gateway", ack["source"]["producer"])
        self.assertEqual("DMZ", ack["source"]["node_role"])
        self.assertEqual("c" * 64, ack["payload"]["metrics"]["contract_hash"])

    def test_a_resend_is_acknowledged_not_swallowed_with_the_caches_main_wires(self):
        # main() also wires the event-id and task-ack caches. Commands are
        # excluded from event-id dedupe; were they not, an identical resend
        # would be dropped with no acknowledgement at all.
        cmd = command("task-main-wiring")
        caches = dict(
            event_dedupe_cache=gateway.EventDedupeCache(),
            task_ack_dedupe_cache=gateway.TaskAckDedupeCache(),
        )
        self.assert_forwarded(cmd, self.send(cmd, 0, **caches))
        self.assert_duplicate(cmd, self.send(cmd, 5, **caches))
        refused = command("task-main-wiring-long", valid_for_ms=10 ** 15)
        for at_s in (6, 7):
            self.assert_refused(
                refused, self.send(refused, at_s, **caches), TOO_LONG_REASON, "command_max_hold_ms", DAY_MS
            )


class NothingIsHeldForACommandThatWasNotReturnedTest(DedupeCase):
    def test_a_failure_after_admission_gives_the_task_id_back(self):
        cmd = command("task-raise")
        with mock.patch.object(self.state, "record", side_effect=RuntimeError("store failed")):
            with self.assertRaises(RuntimeError):
                self.send(cmd, 0)
        # The command was admitted and never returned to the caller, so
        # nothing forwarded it. A second copy is a first copy.
        self.assert_forwarded(cmd, self.send(cmd, 1))
        self.assert_duplicate(cmd, self.send(cmd, 2))

    def test_an_interrupt_after_admission_gives_the_task_id_back(self):
        # Not only ordinary errors: an interrupt or exit also means the
        # admitted command is never returned to the caller.
        cmd = command("task-interrupt")
        with mock.patch.object(self.state, "record", side_effect=KeyboardInterrupt()):
            with self.assertRaises(KeyboardInterrupt):
                self.send(cmd, 0)
        self.assert_forwarded(cmd, self.send(cmd, 1))

    def test_a_failure_while_building_a_warning_gives_the_task_id_back(self):
        # The whole tail of process_message is covered, not only its first
        # statement: here the failure comes after the event was recorded.
        cmd = command("task-warn-fails")
        cmd["lineage"] = {"based_on": [str(uuid7())]}
        metrics = mock.Mock()
        metrics.record_warning.side_effect = RuntimeError("metrics failed")
        with self.assertRaises(RuntimeError):
            self.send(cmd, 0, metrics=metrics)
        metrics.record_warning.assert_called_once()
        corrected = command("task-warn-fails")
        self.assert_forwarded(corrected, self.send(corrected, 1))

    def test_a_failure_on_an_event_that_is_not_a_command_propagates_unchanged(self):
        status = time_status(WALL - timedelta(seconds=5))
        for error in (RuntimeError("store failed"), KeyboardInterrupt()):
            with self.subTest(error=type(error).__name__):
                with mock.patch.object(self.state, "record", side_effect=error):
                    with self.assertRaises(type(error)):
                        self.send(status, 0)

    def test_a_caller_cache_without_release_does_not_hide_the_failure(self):
        class AdmitOnly:
            def __init__(self, inner):
                self.inner = inner
                self.max_entries, self.max_hold_ms = inner.max_entries, inner.max_hold_ms

            def admit(self, task_id, hold_ms):
                return self.inner.admit(task_id, hold_ms)

        cmd = command("task-duck")
        with mock.patch.object(self.state, "record", side_effect=RuntimeError("store failed")):
            with self.assertRaises(RuntimeError):
                self.send(cmd, 0, cache=AdmitOnly(gateway.TaskDedupeCache()))

    def test_a_naive_now_is_read_as_utc_by_every_check(self):
        # The timestamp plausibility check runs before the dedupe and used
        # to raise on a naive `now` whenever a metrics sink was present.
        late = z(WALL + timedelta(seconds=600))
        for label, now in (("naive", WALL.replace(tzinfo=None)), ("no offset", WALL.replace(tzinfo=NoOffset()))):
            with self.subTest(now=label):
                status = time_status(WALL - timedelta(seconds=5))
                metrics = mock.Mock()
                self.clock.now = 1000.0
                out = gateway.process_message(
                    json.dumps(status).encode("utf-8"), self.validator, self.policy, "L", self.cache, "json",
                    timing_state=self.state, metrics=metrics, ts_plausibility_horizon_ms=DAY_MS, now=now,
                )
                # Any event, not only a command: the plausibility check runs for all.
                self.assertEqual(status, out[0])
        cmd = command("task-naive", valid_for_ms=60000, valid_from_ts=late)
        metrics = mock.Mock()
        self.clock.now = 1000.0
        with a_local_zone_that_is_not_utc(self):
            out = gateway.process_message(
                json.dumps(cmd).encode("utf-8"), self.validator, self.policy, "L", self.cache, "json",
                timing_state=self.state, metrics=metrics, ts_plausibility_horizon_ms=1000,
                now=WALL.replace(tzinfo=None),
            )
        self.assert_forwarded(cmd, out)
        # Read as the same instant in UTC: the command's ts equals `now`, so
        # a one-second plausibility horizon records nothing.
        self.assertEqual([], [c for c in metrics.record_warning.call_args_list if c.args[0] == "EVENT_TS_IMPLAUSIBLE"])
        # The hold is exact: the lead to valid_from_ts, the validity, the margin.
        self.assert_duplicate(cmd, self.send(cmd, 660 + MARGIN_S - 1))
        self.assert_forwarded(cmd, self.send(cmd, 660 + MARGIN_S + 1))

    def test_an_aware_now_in_another_zone_is_the_same_instant(self):
        late = z(WALL + timedelta(seconds=600))
        cmd = command("task-zone", valid_for_ms=60000, valid_from_ts=late)
        eastern = timezone(timedelta(hours=-5))
        self.clock.now = 1000.0
        out = gateway.process_message(
            json.dumps(cmd).encode("utf-8"), self.validator, self.policy, "L", self.cache, "json",
            timing_state=self.state, now=WALL.astimezone(eastern),
        )
        self.assert_forwarded(cmd, out)
        self.assert_duplicate(cmd, self.send(cmd, 660 + MARGIN_S - 1))
        self.assert_forwarded(cmd, self.send(cmd, 660 + MARGIN_S + 1))
        self.assertEqual(
            60000 + 600000 + gateway.COMMAND_HOLD_MARGIN_MS,
            gateway.command_hold_ms({"valid_for_ms": 60000, "valid_from_ts": late}, now=WALL.astimezone(eastern)),
        )


class RefusedEarlierTest(DedupeCase):
    def test_a_command_refused_by_policy_does_not_claim_its_task_id(self):
        torch = dict(SOURCE, producer="torch")
        self.state.record(time_status(source=torch))
        denied = command("task-claim", source=torch)
        out = self.send(denied, 0)
        self.assertNotIn(denied, out)
        self.assertEqual("REJECTED", out[0]["payload"]["state"])
        legitimate = command("task-claim")
        self.assert_forwarded(legitimate, self.send(legitimate, 1))

    def test_a_command_refused_by_strict_validation_does_not_claim_its_task_id(self):
        cited = command("task-strict")
        cited["lineage"] = {"based_on": [str(uuid7())]}
        out = self.send(cited, 0, strict_validation=True)
        self.assertEqual(1, len(out), out)
        self.assertNotEqual(cited["event"]["event_id"], out[0]["event"]["event_id"])
        fixed = command("task-strict")
        self.assert_forwarded(fixed, self.send(fixed, 1, strict_validation=True))


class CacheContractTest(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        patcher = mock.patch.object(gateway.time, "monotonic", self.clock)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_the_cache_has_no_method_that_hides_a_refusal(self):
        # check_and_set(task_id, ttl_ms) answered only "duplicate or not", so
        # a caller written against it forwarded a command the cache had
        # refused to hold. It is gone; admit() is the one entry.
        self.assertFalse(hasattr(gateway.TaskDedupeCache, "check_and_set"))
        self.assertFalse(hasattr(gateway, "ttl_ms_from_payload"))

    def test_an_empty_cache_is_still_a_cache(self):
        # process_message guards on `if task_id and dedupe_cache`; a cache
        # that reported itself empty and falsy would switch the dedupe off.
        self.assertTrue(gateway.TaskDedupeCache())

    def test_the_cache_refuses_limits_that_are_not_positive_integers(self):
        for bad in (0, -1, True, 1.5, "4", None, float("inf")):
            with self.subTest(max_entries=bad):
                with self.assertRaises(ValueError):
                    gateway.TaskDedupeCache(max_entries=bad)
            with self.subTest(max_hold_ms=bad):
                with self.assertRaises(ValueError):
                    gateway.TaskDedupeCache(max_hold_ms=bad)

    def test_the_limits_have_ceilings(self):
        self.assertEqual(1024 * 1024, gateway.MAX_COMMAND_DEDUPE_MAX_ENTRIES)
        self.assertEqual(31 * DAY_MS, gateway.MAX_COMMAND_MAX_HOLD_MS)
        cache = gateway.TaskDedupeCache(
            max_entries=gateway.MAX_COMMAND_DEDUPE_MAX_ENTRIES, max_hold_ms=gateway.MAX_COMMAND_MAX_HOLD_MS
        )
        self.assertEqual(gateway.TaskDedupeCache.NEW, cache.admit("task", gateway.MAX_COMMAND_MAX_HOLD_MS))
        with self.assertRaises(ValueError):
            gateway.TaskDedupeCache(max_entries=gateway.MAX_COMMAND_DEDUPE_MAX_ENTRIES + 1)
        for too_big in (gateway.MAX_COMMAND_MAX_HOLD_MS + 1, 10 ** 20, 10 ** 400):
            with self.subTest(max_hold_ms=too_big):
                with self.assertRaises(ValueError):
                    gateway.TaskDedupeCache(max_hold_ms=too_big)

    def test_admit_refuses_a_hold_that_is_not_a_positive_number(self):
        cache = gateway.TaskDedupeCache()
        for bad in (0, -1, True, "x", None, float("nan")):
            with self.subTest(hold_ms=bad):
                with self.assertRaises(ValueError):
                    cache.admit("task", bad)
        self.assertEqual(gateway.TaskDedupeCache.NEW, cache.admit("task", 1000))
        self.assertEqual(gateway.TaskDedupeCache.TOO_LONG, cache.admit("other", float("inf")))
        self.assertEqual(gateway.TaskDedupeCache.TOO_LONG, cache.admit("other", 10 ** 400))

    def test_a_hold_is_kept_to_the_fraction_of_a_second(self):
        cache = gateway.TaskDedupeCache()
        self.assertEqual(gateway.TaskDedupeCache.NEW, cache.admit("task", 61500))
        self.clock.now = 1061.2
        self.assertEqual(gateway.TaskDedupeCache.DUPLICATE, cache.admit("task", 1000))
        self.clock.now = 1061.6
        self.assertEqual(gateway.TaskDedupeCache.NEW, cache.admit("task", 1000))

    def test_capacity_returns_at_the_exact_end_of_a_hold(self):
        cache = gateway.TaskDedupeCache(max_entries=1)
        self.assertEqual(gateway.TaskDedupeCache.NEW, cache.admit("a", 60000))
        self.clock.now = 1059.999
        self.assertEqual(gateway.TaskDedupeCache.FULL, cache.admit("b", 60000))
        self.clock.now = 1060.0
        self.assertEqual(gateway.TaskDedupeCache.NEW, cache.admit("b", 60000))

    def test_only_a_command_event_has_a_command_task_id(self):
        cmd = command("task-x")
        self.assertEqual("task-x", gateway._command_task_id(cmd))
        # System and state payloads admit extra properties, so a schema-valid
        # TIME_STATUS can carry a `payload.task_id`. It is not a command.
        status = time_status()
        status["payload"]["task_id"] = "task-x"
        self.assertIsNone(gateway._command_task_id(status))
        ack = {"event": {"event_type": "SYSTEM_EVENT"}, "payload": {"metrics": {"task_id": "task-x"}}}
        self.assertIsNone(gateway._command_task_id(ack))
        for bad in (None, "", 7, ["task-x"]):
            with self.subTest(task_id=bad):
                broken = command("task-x")
                broken["payload"]["task_id"] = bad
                self.assertIsNone(gateway._command_task_id(broken))
        for not_an_event in (None, [], "x", {"event": "COMMAND_EVENT"}, {"event": {}, "payload": None}):
            self.assertIsNone(gateway._command_task_id(not_an_event))

    def test_release_forgets_one_id_and_only_that_id(self):
        cache = gateway.TaskDedupeCache(max_entries=2)
        self.assertEqual(gateway.TaskDedupeCache.NEW, cache.admit("a", 60000))
        self.assertEqual(gateway.TaskDedupeCache.NEW, cache.admit("b", 60000))
        cache.release("a")
        cache.release("never-held")
        self.assertEqual(gateway.TaskDedupeCache.DUPLICATE, cache.admit("b", 60000))
        self.assertEqual(gateway.TaskDedupeCache.NEW, cache.admit("a", 60000))
        self.assertEqual(gateway.TaskDedupeCache.FULL, cache.admit("c", 60000))


def args_with(*argv):
    with mock.patch("sys.argv", ["gateway.py", "--profile", "H", *argv]):
        return gateway.parse_args()


class SettingsTest(unittest.TestCase):
    KEYS = (
        ("command_dedupe_max_entries", "--command-dedupe-max-entries", 4096, 1024 * 1024),
        ("command_max_hold_ms", "--command-max-hold-ms", DAY_MS, 31 * DAY_MS),
    )

    def test_both_limits_are_settings_and_flags_win(self):
        for key, flag, default, _ceiling in self.KEYS:
            with self.subTest(key=key):
                self.assertEqual(default, gateway.build_settings(ROOT, args_with(), {})[key])
                self.assertEqual(90000, gateway.build_settings(ROOT, args_with(), {key: 90000})[key])
                self.assertEqual(
                    120000, gateway.build_settings(ROOT, args_with(flag, "120000"), {key: 90000})[key]
                )

    def test_a_limit_that_is_not_a_positive_integer_is_refused(self):
        for key, flag, _default, _ceiling in self.KEYS:
            for bad in (0, -1, "many", "16", 16.0, True, None):
                with self.subTest(key=key, value=bad):
                    with self.assertRaises(ValueError):
                        gateway.build_settings(ROOT, args_with(), {key: bad})
            for bad in ("0", "-1"):
                with self.subTest(flag=flag, value=bad):
                    with self.assertRaises(ValueError):
                        gateway.build_settings(ROOT, args_with(flag, bad), {})

    def test_a_limit_above_its_ceiling_is_refused(self):
        for key, flag, _default, ceiling in self.KEYS:
            with self.subTest(key=key):
                self.assertEqual(ceiling, gateway.build_settings(ROOT, args_with(), {key: ceiling})[key])
                self.assertEqual(ceiling, gateway.build_settings(ROOT, args_with(flag, str(ceiling)), {})[key])
                with self.assertRaises(ValueError):
                    gateway.build_settings(ROOT, args_with(), {key: ceiling + 1})
                with self.assertRaises(ValueError):
                    gateway.build_settings(ROOT, args_with(flag, str(ceiling + 1)), {})
                with self.assertRaises(ValueError):
                    gateway.build_settings(ROOT, args_with(), {key: 10 ** 400})

    def test_a_maximum_hold_no_longer_than_the_margin_is_refused(self):
        # Every hold includes the margin, so such a limit would refuse every command.
        margin = gateway.COMMAND_HOLD_MARGIN_MS
        with self.assertRaises(ValueError):
            gateway.build_settings(ROOT, args_with(), {"command_max_hold_ms": margin})
        with self.assertRaises(ValueError):
            gateway.build_settings(ROOT, args_with("--command-max-hold-ms", str(margin)), {})
        with self.assertRaises(ValueError):
            gateway.build_settings(
                ROOT, args_with("--command-max-hold-ms", str(margin)), {"command_max_hold_ms": margin + 1}
            )
        self.assertEqual(
            margin + 1,
            gateway.build_settings(ROOT, args_with(), {"command_max_hold_ms": margin + 1})["command_max_hold_ms"],
        )
        self.assertEqual(
            margin + 1,
            gateway.build_settings(
                ROOT, args_with("--command-max-hold-ms", str(margin + 1)), {}
            )["command_max_hold_ms"],
        )


class _StopReceiveLoop(BaseException):
    """Ends main()'s receive loop from recvfrom; `except Exception` cannot catch it."""


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


class MainLoopCase(unittest.TestCase):
    """Through the real main() receive loop, with the two UDP sockets replaced.

    A test that needs a failure inside the loop adds its own patch and says so.
    """

    def setUp(self):
        self.now = datetime.now(timezone.utc).replace(microsecond=0)
        self.status = time_status(self.now - timedelta(seconds=20))

    def live(self, task_id, valid_for_ms=60000):
        return command(task_id, valid_for_ms=valid_for_ms, ts=self.now)

    def run_loop(self, events, *flags, patches=()):
        sock_in = _LoopSocket([json.dumps(event).encode("utf-8") for event in events])
        sock_out = _LoopSocket()
        sockets = [sock_in, sock_out]
        argv = ["gateway.py", "--profile", "L", "--listen-port", "45597", "--forward-port", "45596",
                "--no-metrics", *flags]
        out, err = io.StringIO(), io.StringIO()
        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch("sys.argv", argv))
            stack.enter_context(mock.patch.object(gateway.socket, "socket", lambda *a, **k: sockets.pop(0)))
            for patch in patches:
                stack.enter_context(patch)
            stack.enter_context(contextlib.redirect_stdout(out))
            stack.enter_context(contextlib.redirect_stderr(err))
            with self.assertRaises(_StopReceiveLoop):
                gateway.main()
        self.stderr = err.getvalue()
        return [json.loads(payload) for payload, _addr in sock_out.sent], out.getvalue()

    @staticmethod
    def ids(sent):
        return [e["event"]["event_id"] for e in sent]

    @staticmethod
    def acks(sent):
        return [e for e in sent if e["event"]["event_subtype"] == "TASK_ACK"]


class MainHandsTheLimitsToTheCacheTest(MainLoopCase):
    def assert_refusal(self, sent, original, reason, limit_key, limit):
        acks = self.acks(sent)
        self.assertEqual(1, len(acks), sent)
        metrics = acks[0]["payload"]["metrics"]
        self.assertEqual("REJECTED", acks[0]["payload"]["state"])
        self.assertEqual(original["event"]["event_id"], metrics["original_event_id"])
        self.assertEqual(reason, metrics["reason"])
        self.assertEqual(limit, metrics[limit_key])
        self.assertNotIn(original["event"]["event_id"], self.ids(sent))

    def test_main_uses_the_configured_capacity(self):
        first, second = self.live("task-main-1"), self.live("task-main-2")
        sent, banner = self.run_loop([self.status, first, second], "--command-dedupe-max-entries", "1")
        self.assertIn(first["event"]["event_id"], self.ids(sent))
        self.assert_refusal(sent, second, CAPACITY_REASON, "command_dedupe_max_entries", 1)
        self.assertIn("command dedupe: up to 1 task_ids held, each for at most 86400000ms", banner)

    def test_main_uses_the_configured_maximum_hold(self):
        short, long_lived = self.live("task-main-short"), self.live("task-main-long", valid_for_ms=600000)
        sent, banner = self.run_loop([self.status, short, long_lived], "--command-max-hold-ms", "180000")
        self.assertIn(short["event"]["event_id"], self.ids(sent))
        self.assert_refusal(sent, long_lived, TOO_LONG_REASON, "command_max_hold_ms", 180000)
        self.assertIn("command dedupe: up to 4096 task_ids held, each for at most 180000ms", banner)

    def test_main_with_the_defaults_forwards_both(self):
        # The control for the two tests above: without the flags nothing is refused.
        first, second = self.live("task-main-a"), self.live("task-main-b", valid_for_ms=600000)
        sent, _banner = self.run_loop([self.status, first, second])
        self.assertIn(first["event"]["event_id"], self.ids(sent))
        self.assertIn(second["event"]["event_id"], self.ids(sent))
        self.assertEqual([], self.acks(sent))

    def test_main_keeps_one_cache_across_datagrams_and_acknowledges_a_duplicate(self):
        first, again = self.live("task-main-dup"), self.live("task-main-dup")
        sent, _banner = self.run_loop([self.status, first, again])
        self.assertIn(first["event"]["event_id"], self.ids(sent))
        self.assertNotIn(again["event"]["event_id"], self.ids(sent))
        acks = self.acks(sent)
        self.assertEqual(1, len(acks), sent)
        self.assertEqual("DUPLICATE_IGNORED", acks[0]["payload"]["state"])
        self.assertEqual(again["event"]["event_id"], acks[0]["payload"]["metrics"]["original_event_id"])


class AnUndeliveredCommandGivesItsTaskIdBackTest(MainLoopCase):
    """A command that was admitted and then did not leave the gateway is not held.

    Nothing can execute it, so a corrected copy under the same task_id is a
    first copy. Before this, the retry was answered DUPLICATE_IGNORED for the
    rest of the first copy's hold.
    """

    def retry_is_forwarded(self, patch):
        first, retry = self.live("task-undelivered"), self.live("task-undelivered")
        sent, _banner = self.run_loop([self.status, first, retry], patches=[patch(first)])
        self.assertNotIn(first["event"]["event_id"], self.ids(sent))
        self.assertIn(retry["event"]["event_id"], self.ids(sent))
        self.assertEqual([], [a for a in self.acks(sent) if a["payload"]["state"] == "DUPLICATE_IGNORED"])
        return sent

    def test_when_the_send_fails(self):
        real = gateway._send_datagram

        def patch(first):
            def send(sock, payload, addr, **kwargs):
                if kwargs.get("event_id") == first["event"]["event_id"]:
                    return False
                return real(sock, payload, addr, **kwargs)
            return mock.patch.object(gateway, "_send_datagram", send)

        self.retry_is_forwarded(patch)

    def test_when_the_outgoing_check_replaces_it_with_a_diagnostic(self):
        real = gateway.validate_outgoing_event

        def patch(first):
            def check(event, validator, policy, profile):
                if event.get("event", {}).get("event_id") == first["event"]["event_id"]:
                    return [{"code": "SCHEMA_INVALID", "message": "forced by the test", "details": {}}]
                return real(event, validator, policy, profile)
            return mock.patch.object(gateway, "validate_outgoing_event", check)

        sent = self.retry_is_forwarded(patch)
        rejected = [a for a in self.acks(sent) if a["payload"]["state"] == "REJECTED"]
        self.assertEqual(1, len(rejected), sent)

    def test_when_the_outgoing_check_itself_fails(self):
        # An error before the send, at the first step that can raise after
        # admission, reaches the receive loop's last-resort handler.
        real = gateway.validate_outgoing_event

        def patch(first):
            def check(event, validator, policy, profile):
                if event.get("event", {}).get("event_id") == first["event"]["event_id"]:
                    raise RuntimeError("outgoing check failed")
                return real(event, validator, policy, profile)
            return mock.patch.object(gateway, "validate_outgoing_event", check)

        self.retry_is_forwarded(patch)
        self.assertIn("datagram dropped after unexpected RuntimeError", self.stderr)

    def test_when_the_encoder_reports_nothing_can_be_sent(self):
        # The (None, outgoing) return, forced by a patch: the path taken
        # when not even a diagnostic can be encoded.
        real = gateway._encode_outgoing_or_diagnostic

        def patch(first):
            def encode(outgoing, settings, **kwargs):
                if outgoing.get("event", {}).get("event_id") == first["event"]["event_id"]:
                    return None, outgoing
                return real(outgoing, settings, **kwargs)
            return mock.patch.object(gateway, "_encode_outgoing_or_diagnostic", encode)

        self.retry_is_forwarded(patch)

    def unencodable_then_corrected(self, *flags, decode):
        """A command no binary encoding can carry, then a corrected copy; nothing is patched."""
        first, retry = self.live("task-unencodable"), self.live("task-unencodable")
        # Schema-valid: command extensions admit extra properties, and JSON
        # carries an integer of any size. CBOR and the compact form do not.
        first["payload"]["extensions"] = {"n": 2 ** 64}
        sock_in = _LoopSocket([json.dumps(e).encode("utf-8") for e in (self.status, first, retry)])
        sock_out = _LoopSocket()
        sockets = [sock_in, sock_out]
        argv = ["gateway.py", "--profile", "L", "--listen-port", "45597", "--forward-port", "45596",
                "--no-metrics", *flags]
        err = io.StringIO()
        with mock.patch("sys.argv", argv), \
                mock.patch.object(gateway.socket, "socket", lambda *a, **k: sockets.pop(0)), \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
            with self.assertRaises(_StopReceiveLoop):
                gateway.main()
        sent = [decode(payload) for payload, _addr in sock_out.sent]
        self.assertNotIn(first["event"]["event_id"], self.ids(sent))
        self.assertIn(retry["event"]["event_id"], self.ids(sent))
        self.assertEqual([], [a for a in self.acks(sent) if a["payload"]["state"] == "DUPLICATE_IGNORED"])
        return sent, err.getvalue()

    def test_when_the_cbor_encoder_raises(self):
        # The exception escapes to the receive loop's backstop, which used
        # to leave the task_id held: the corrected copy was answered
        # DUPLICATE_IGNORED although the first copy was never sent.
        if gateway.zmeta_cbor is None:  # pragma: no cover - ships in this repository
            self.skipTest("zmeta_cbor not importable")
        _sent, err = self.unencodable_then_corrected(
            "--output-encoding", "cbor", decode=lambda payload: gateway._decode_message(payload, "cbor")
        )
        # Proof the path under test was taken: the backstop reported the drop.
        self.assertIn("datagram dropped after unexpected", err)

    def test_when_the_compact_encoding_replaces_it_with_a_diagnostic(self):
        if gateway.zmeta_compact is None or gateway.cbor2 is None:  # pragma: no cover
            self.skipTest("zmeta_compact or cbor2 not installed")
        sent, err = self.unencodable_then_corrected(
            "--output-encoding", "compact", decode=lambda payload: gateway._decode_message(payload, "compact")
        )
        # Proof the path under test was taken: a diagnostic went out in the
        # command's place, and nothing reached the backstop.
        self.assertIn("ENCODING_UNSUPPORTED", [e["payload"].get("metrics", {}).get("reason_code") for e in sent])
        self.assertNotIn("datagram dropped after unexpected", err)

    def test_a_delivered_command_stays_held(self):
        # The control: with nothing failing, the second copy is a duplicate.
        first, again = self.live("task-delivered"), self.live("task-delivered")
        sent, _banner = self.run_loop([self.status, first, again])
        self.assertIn(first["event"]["event_id"], self.ids(sent))
        self.assertNotIn(again["event"]["event_id"], self.ids(sent))

    def test_a_delivered_command_stays_held_when_a_warning_rides_behind_it(self):
        # process_message returns the command and then its warning. The
        # warning is not the command, and sending it must not be read as
        # "the command was replaced".
        first, again = self.live("task-warned"), self.live("task-warned")
        for cmd in (first, again):
            # A citation the gateway has not seen: a warning under the shipped policy.
            cmd["lineage"] = {"based_on": [str(uuid7())]}
        sent, _banner = self.run_loop([self.status, first, again])
        self.assertIn(first["event"]["event_id"], self.ids(sent))
        position = self.ids(sent).index(first["event"]["event_id"])
        behind = sent[position + 1]
        self.assertEqual("SCHEMA_VIOLATION", behind["event"]["event_subtype"], "a warning must ride behind")
        self.assertEqual(first["event"]["event_id"], behind["payload"]["metrics"]["original_event_id"])
        self.assertNotIn(again["event"]["event_id"], self.ids(sent))
        self.assertEqual(1, len([a for a in self.acks(sent) if a["payload"]["state"] == "DUPLICATE_IGNORED"]))

    def test_a_failure_after_the_send_does_not_release_the_delivered_command(self):
        # The command went out, then the same datagram's bookkeeping raised
        # and the receive loop's backstop ran. The command was delivered, so
        # its id stays held; releasing it would forward the next copy.
        first, again = self.live("task-sent-then-failed"), self.live("task-sent-then-failed")
        calls = []

        def record_forwarded(_metrics, count=1):
            calls.append(count)
            if len(calls) == 2:  # the TIME_STATUS is the first forward, the command the second
                raise RuntimeError("metrics failed after the send")

        sent, _banner = self.run_loop(
            [self.status, first, again],
            patches=[mock.patch.object(gateway.GatewayMetrics, "record_forwarded", record_forwarded)],
        )
        # Three forwards: the TIME_STATUS, the command, the duplicate's acknowledgement.
        self.assertEqual(3, len(calls))
        self.assertIn("datagram dropped after unexpected RuntimeError", self.stderr)
        self.assertIn(first["event"]["event_id"], self.ids(sent))
        self.assertNotIn(again["event"]["event_id"], self.ids(sent))
        self.assertEqual(1, len([a for a in self.acks(sent) if a["payload"]["state"] == "DUPLICATE_IGNORED"]))

    def test_a_lost_system_event_that_carries_a_task_id_releases_nothing(self):
        # A TIME_STATUS may carry `payload.task_id` and stay schema-valid.
        # Losing it on the wire must not release the command of that name.
        first, again = self.live("task-named"), self.live("task-named")
        decoy = time_status(self.now - timedelta(seconds=10))
        decoy["payload"]["task_id"] = "task-named"
        real = gateway._send_datagram

        def send(sock, payload, addr, **kwargs):
            if kwargs.get("event_id") == decoy["event"]["event_id"]:
                return False
            return real(sock, payload, addr, **kwargs)

        sent, _banner = self.run_loop(
            [self.status, first, decoy, again], patches=[mock.patch.object(gateway, "_send_datagram", send)]
        )
        self.assertIn(first["event"]["event_id"], self.ids(sent))
        self.assertNotIn(decoy["event"]["event_id"], self.ids(sent))
        self.assertNotIn(again["event"]["event_id"], self.ids(sent))

    def test_a_refused_duplicate_does_not_release_the_held_command(self):
        # A duplicate's acknowledgement is not a COMMAND_EVENT, so a failed
        # send of the acknowledgement must not release the id it protects.
        first, again, third = (self.live("task-ack-lost") for _ in range(3))
        real = gateway._send_datagram

        def send(sock, payload, addr, **kwargs):
            if b"DUPLICATE_IGNORED" in payload:
                return False
            return real(sock, payload, addr, **kwargs)

        sent, _banner = self.run_loop(
            [self.status, first, again, third], patches=[mock.patch.object(gateway, "_send_datagram", send)]
        )
        self.assertIn(first["event"]["event_id"], self.ids(sent))
        self.assertNotIn(again["event"]["event_id"], self.ids(sent))
        self.assertNotIn(third["event"]["event_id"], self.ids(sent))


if __name__ == "__main__":
    unittest.main()
