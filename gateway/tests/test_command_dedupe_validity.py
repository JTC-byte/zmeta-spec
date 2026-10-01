"""A duplicate COMMAND_EVENT is not forwarded a second time while any copy seen could execute.

Contract 13.2: "Duplicate COMMAND_EVENTs MUST NOT be forwarded for execution a
second time." The gateway used to hold a command's task_id for the smaller of
its valid_for_ms and 300 s, so the shipped example command, valid for 600 s,
was forwarded again when its duplicate arrived at 301 s.

What is pinned here:

- A task_id is held from first receipt until the command's validity ends,
  read the widest way (valid_for_ms after the latest of receipt, event.ts and
  valid_from_ts), plus a fixed margin for clock disagreement.
- A later copy never shortens the hold and lengthens it when its own validity
  ends later.
- A command the gateway would have to hold for longer than the maximum hold
  is refused, so every held id expires and a full cache always clears.
- The cache is bounded by count. When it is full a new command is refused
  instead of an old id being forgotten.
- Both limits are settings, and main() hands them to the cache.

What this file does not prove. The cache is in memory, so a gateway restart
forgets every held id. A command whose validity has already ended is not
refused. A task_id is released when its hold ends, and the same task_id is
then admitted as a new command; contract 13.2 sets no time bound on "a second
time", so that release is a reading the maintainer has not ruled on (doctrine
E1-06), and test_the_id_is_released_when_the_hold_ends pins the behavior, not
the ruling.
"""

import contextlib
import importlib.util
import io
import json
import unittest
from datetime import datetime, timedelta, timezone
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


def z(moment):
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


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

    def send(self, event, at_s, cache=None, metrics=None, validator=None, identity=None):
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
            metrics=metrics,
            now=WALL + timedelta(seconds=at_s),
            gateway_identity=identity,
        )

    def assert_forwarded(self, event, out):
        self.assertTrue(out, "nothing came out")
        self.assertEqual(event, out[0])
        for extra in out[1:]:
            # A warning may ride behind a forwarded event; a task
            # acknowledgement behind one would mean it was also refused.
            self.assertNotEqual("TASK_ACK", extra["event"]["event_subtype"], extra)

    def assert_duplicate(self, out):
        self.assertEqual(1, len(out), out)
        self.assertEqual("TASK_ACK", out[0]["event"]["event_subtype"])
        self.assertEqual("DUPLICATE_IGNORED", out[0]["payload"]["state"])
        self.assertEqual("TASK_DUPLICATE", out[0]["payload"]["metrics"]["reason_code"])

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
    def test_the_shipped_600_s_command_is_not_forwarded_again_while_valid(self):
        cmd = shipped_command()
        self.assertEqual(600000, cmd["payload"]["valid_for_ms"])
        # The shipped command carries no per-event timing quality, so its node's
        # TIME_STATUS must be current at the command's own ts.
        self.assertEqual(SOURCE, cmd["source"])
        self.state.record(time_status(cmd["event"]["ts"]))
        self.assert_forwarded(cmd, self.send(cmd, 0))
        for at_s in (10, 301, 599, 600 + MARGIN_S - 1):
            with self.subTest(at_s=at_s):
                self.assert_duplicate(self.send(cmd, at_s))

    def test_a_short_command_is_deduped_through_its_validity_and_the_margin(self):
        cmd = command("task-short", valid_for_ms=60000)
        self.assert_forwarded(cmd, self.send(cmd, 0))
        for at_s in (1, 59, 61, 60 + MARGIN_S - 1):
            with self.subTest(at_s=at_s):
                self.assert_duplicate(self.send(cmd, at_s))

    def test_the_id_is_released_when_the_hold_ends(self):
        # Pins the behavior, not a ruling: contract 13.2 sets no time bound on
        # "a second time" (doctrine E1-06).
        cmd = command("task-release", valid_for_ms=60000)
        self.assert_forwarded(cmd, self.send(cmd, 0))
        self.assert_forwarded(cmd, self.send(cmd, 60 + MARGIN_S + 1))

    def test_the_margin_is_one_minute(self):
        self.assertEqual(60000, gateway.COMMAND_HOLD_MARGIN_MS)
        self.assertEqual(MARGIN_S * 1000, gateway.COMMAND_HOLD_MARGIN_MS)

    def test_lead_time_to_valid_from_ts_is_held(self):
        # Valid for 60 s starting 600 s after receipt: executable until 660 s.
        start = z(WALL + timedelta(seconds=600))
        cmd = command("task-lead", valid_for_ms=60000, valid_from_ts=start)
        self.assert_forwarded(cmd, self.send(cmd, 0))
        for at_s in (61, 301, 659, 660 + MARGIN_S - 1):
            with self.subTest(at_s=at_s):
                self.assert_duplicate(self.send(cmd, at_s))
        # The lead is held and no longer: an id nobody repeated is released
        # when that hold ends. (Each copy above lengthened its own id's hold,
        # so the release is checked on an id that was sent once.)
        once = command("task-lead-once", valid_for_ms=60000, valid_from_ts=start)
        self.assert_forwarded(once, self.send(once, 0))
        self.assert_forwarded(once, self.send(once, 660 + MARGIN_S + 1))

    def test_a_future_event_ts_is_held_as_the_validity_anchor(self):
        # Contract 5.1: a command's event.ts is "the command issue time or
        # validity anchor". A consumer that anchors validity there can still
        # execute this command 659 s after the gateway received it.
        ahead = WALL + timedelta(seconds=600)
        self.state.record(time_status(ahead - timedelta(seconds=20)))
        cmd = command("task-future-ts", valid_for_ms=60000, ts=ahead)
        self.assert_forwarded(cmd, self.send(cmd, 0))
        for at_s in (61, 301, 659, 660 + MARGIN_S - 1):
            with self.subTest(at_s=at_s):
                self.assert_duplicate(self.send(cmd, at_s))

    def test_the_hold_is_measured_to_the_latest_anchor(self):
        hold = gateway.command_hold_ms
        soon, late = z(WALL + timedelta(seconds=100)), z(WALL + timedelta(seconds=600))
        past = z(WALL - timedelta(seconds=600))
        margin = gateway.COMMAND_HOLD_MARGIN_MS
        cases = (
            # (valid_from_ts, event_ts, expected lead in ms)
            (None, None, 0),
            (past, past, 0),
            ("garbageZ", "garbageZ", 0),
            (late, None, 600000),
            (None, late, 600000),
            (late, soon, 600000),
            (soon, late, 600000),
            (soon, past, 100000),
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

    def test_hold_falls_back_for_a_value_that_is_not_a_positive_integer(self):
        expected = 60000 + gateway.COMMAND_HOLD_MARGIN_MS
        for bad in (None, "x", 0, -5, float("inf"), [1]):
            with self.subTest(valid_for_ms=bad):
                self.assertEqual(expected, gateway.command_hold_ms({"valid_for_ms": bad}, now=WALL))
        self.assertEqual(expected, gateway.command_hold_ms(None, now=WALL))

    def test_the_same_task_id_from_another_platform_is_a_duplicate(self):
        # Contract 13.2 keys the dedupe on payload.task_id alone.
        other = dict(SOURCE, platform_id="comms-node-2")
        self.state.record(time_status(source=other))
        first = command("task-shared", valid_for_ms=600000)
        second = command("task-shared", valid_for_ms=600000, source=other)
        self.assert_forwarded(first, self.send(first, 0))
        self.assert_duplicate(self.send(second, 5))


class LaterCopiesTest(DedupeCase):
    def test_a_later_copy_with_a_longer_validity_lengthens_the_hold(self):
        # A producer repeating one task with a longer validity: the id stays
        # held while any copy seen could execute.
        first = command("task-repeat", valid_for_ms=60000)
        longer = command("task-repeat", valid_for_ms=600000)
        self.assert_forwarded(first, self.send(first, 0))
        self.assert_duplicate(self.send(longer, 50))
        # Probed with the short copy, which cannot lengthen the hold itself
        # until the last probe.
        for at_s in (60 + MARGIN_S + 1, 200, 50 + 600 + MARGIN_S - 1):
            with self.subTest(at_s=at_s):
                self.assert_duplicate(self.send(first, at_s))

    def test_a_later_copy_with_a_shorter_validity_does_not_shorten_the_hold(self):
        first = command("task-keep", valid_for_ms=600000)
        shorter = command("task-keep", valid_for_ms=60000)
        self.assert_forwarded(first, self.send(first, 0))
        self.assert_duplicate(self.send(shorter, 10))
        # Probed with the short copy, so the probes do not lengthen the hold.
        for at_s in (10 + 60 + MARGIN_S + 1, 300, 600 + MARGIN_S - 1):
            with self.subTest(at_s=at_s):
                self.assert_duplicate(self.send(shorter, at_s))

    def test_a_later_copy_cannot_lengthen_the_hold_past_the_maximum(self):
        cache = gateway.TaskDedupeCache(max_entries=4, max_hold_ms=180000)
        # Two ids, because a probe is itself a copy and lengthens the hold:
        # one id shows the hold reached the maximum, the other that it
        # stopped there.
        for task_id, probe_at_s, held in (("task-cap-a", 10 + 180 - 1, True), ("task-cap-b", 10 + 180 + 1, False)):
            with self.subTest(task_id=task_id):
                first = command(task_id, valid_for_ms=60000)
                huge = command(task_id, valid_for_ms=10 ** 15)
                self.assert_forwarded(first, self.send(first, 0, cache=cache))
                # A copy of a held command is a duplicate whatever its validity.
                self.assert_duplicate(self.send(huge, 10, cache=cache))
                out = self.send(first, probe_at_s, cache=cache)
                if held:
                    self.assert_duplicate(out)
                else:
                    self.assert_forwarded(first, out)


class MaximumHoldTest(DedupeCase):
    def test_the_default_maximum_hold_is_one_day(self):
        self.assertEqual(DAY_MS, gateway.DEFAULT_COMMAND_MAX_HOLD_MS)
        self.assertEqual(DAY_MS, gateway.TaskDedupeCache().max_hold_ms)

    def test_a_command_at_the_maximum_hold_is_forwarded_and_one_past_it_is_refused(self):
        longest = DAY_MS - gateway.COMMAND_HOLD_MARGIN_MS
        at_limit = command("task-at-limit", valid_for_ms=longest)
        self.assert_forwarded(at_limit, self.send(at_limit, 0))
        self.assert_duplicate(self.send(at_limit, DAY_MS // 1000 - 1))
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

    def test_a_full_cache_always_clears(self):
        # Every hold is finite, so a full cache refuses for at most the
        # maximum hold. Before the maximum hold existed, ids held "forever"
        # filled the cache until the gateway was restarted.
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
        out = self.send(sixth, 6, cache=cache, metrics=metrics, identity=identity)

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
            self.assert_duplicate(self.send(cmd, 7, cache=cache))
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
            self.assert_duplicate(self.send(first, at_s, cache=cache))
        self.assert_forwarded(second, self.send(second, 4, cache=cache))

    def test_the_refusals_are_valid_on_every_lane(self):
        for lane, schema_file, versions in LANES:
            validator = validators.load_schema(ROOT / "schema" / schema_file)
            for version in versions:
                with self.subTest(lane=lane, zmeta_version=version):
                    cache = gateway.TaskDedupeCache(max_entries=1, max_hold_ms=180000)
                    held = command(f"task-held-{version}", version=version)
                    self.assert_forwarded(held, self.send(held, 0, cache=cache, validator=validator))
                    self.assert_duplicate(self.send(held, 1, cache=cache, validator=validator))
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


class CacheContractTest(unittest.TestCase):
    def test_the_cache_has_no_method_that_hides_a_refusal(self):
        # check_and_set(task_id, ttl_ms) answered only "duplicate or not", so
        # a caller written against it forwarded a command the cache had
        # refused to hold. It is gone; admit() is the one entry.
        self.assertFalse(hasattr(gateway.TaskDedupeCache, "check_and_set"))
        self.assertFalse(hasattr(gateway, "ttl_ms_from_payload"))

    def test_the_cache_refuses_limits_that_are_not_positive_integers(self):
        for bad in (0, -1, True, 1.5, "4", None, float("inf")):
            with self.subTest(max_entries=bad):
                with self.assertRaises(ValueError):
                    gateway.TaskDedupeCache(max_entries=bad)
            with self.subTest(max_hold_ms=bad):
                with self.assertRaises(ValueError):
                    gateway.TaskDedupeCache(max_hold_ms=bad)

    def test_admit_refuses_a_hold_that_is_not_a_positive_number(self):
        cache = gateway.TaskDedupeCache()
        for bad in (0, -1, True, "x", None, float("nan")):
            with self.subTest(hold_ms=bad):
                with self.assertRaises(ValueError):
                    cache.admit("task", bad)
        self.assertEqual(gateway.TaskDedupeCache.NEW, cache.admit("task", 1000))
        self.assertEqual(gateway.TaskDedupeCache.TOO_LONG, cache.admit("other", float("inf")))


def args_with(*argv):
    with mock.patch("sys.argv", ["gateway.py", "--profile", "H", *argv]):
        return gateway.parse_args()


class SettingsTest(unittest.TestCase):
    KEYS = (
        ("command_dedupe_max_entries", "--command-dedupe-max-entries", 4096),
        ("command_max_hold_ms", "--command-max-hold-ms", DAY_MS),
    )

    def test_both_limits_are_settings_and_flags_win(self):
        for key, flag, default in self.KEYS:
            with self.subTest(key=key):
                self.assertEqual(default, gateway.build_settings(ROOT, args_with(), {})[key])
                self.assertEqual(90000, gateway.build_settings(ROOT, args_with(), {key: 90000})[key])
                self.assertEqual(
                    120000, gateway.build_settings(ROOT, args_with(flag, "120000"), {key: 90000})[key]
                )

    def test_a_limit_that_is_not_a_positive_integer_is_refused(self):
        for key, flag, _default in self.KEYS:
            for bad in (0, -1, "many", "16", 16.0, True, None):
                with self.subTest(key=key, value=bad):
                    with self.assertRaises(ValueError):
                        gateway.build_settings(ROOT, args_with(), {key: bad})
            for bad in ("0", "-1"):
                with self.subTest(flag=flag, value=bad):
                    with self.assertRaises(ValueError):
                        gateway.build_settings(ROOT, args_with(flag, bad), {})

    def test_a_maximum_hold_no_longer_than_the_margin_is_refused(self):
        # Every hold includes the margin, so such a limit would refuse every command.
        margin = gateway.COMMAND_HOLD_MARGIN_MS
        with self.assertRaises(ValueError):
            gateway.build_settings(ROOT, args_with(), {"command_max_hold_ms": margin})
        self.assertEqual(
            margin + 1,
            gateway.build_settings(ROOT, args_with(), {"command_max_hold_ms": margin + 1})["command_max_hold_ms"],
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


class MainHandsTheLimitsToTheCacheTest(unittest.TestCase):
    """Through the real main() receive loop; only the two UDP sockets are replaced."""

    def run_loop(self, events, *flags):
        sock_in = _LoopSocket([json.dumps(event).encode("utf-8") for event in events])
        sock_out = _LoopSocket()
        sockets = [sock_in, sock_out]
        argv = ["gateway.py", "--profile", "L", "--listen-port", "45597", "--forward-port", "45596",
                "--no-metrics", *flags]
        out = io.StringIO()
        with mock.patch("sys.argv", argv), \
                mock.patch.object(gateway.socket, "socket", lambda *a, **k: sockets.pop(0)), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(_StopReceiveLoop):
                gateway.main()
        return [json.loads(payload) for payload, _addr in sock_out.sent], out.getvalue()

    def live(self, task_id, valid_for_ms=60000):
        return command(task_id, valid_for_ms=valid_for_ms, ts=self.now)

    def setUp(self):
        self.now = datetime.now(timezone.utc).replace(microsecond=0)
        self.status = time_status(self.now - timedelta(seconds=20))

    def assert_refusal(self, sent, original, reason, limit_key, limit):
        acks = [e for e in sent if e["event"]["event_subtype"] == "TASK_ACK"]
        self.assertEqual(1, len(acks), sent)
        metrics = acks[0]["payload"]["metrics"]
        self.assertEqual("REJECTED", acks[0]["payload"]["state"])
        self.assertEqual(original["event"]["event_id"], metrics["original_event_id"])
        self.assertEqual(reason, metrics["reason"])
        self.assertEqual(limit, metrics[limit_key])
        self.assertNotIn(original["event"]["event_id"], [e["event"]["event_id"] for e in sent])

    def test_main_uses_the_configured_capacity(self):
        first, second = self.live("task-main-1"), self.live("task-main-2")
        sent, banner = self.run_loop([self.status, first, second], "--command-dedupe-max-entries", "1")
        self.assertIn(first["event"]["event_id"], [e["event"]["event_id"] for e in sent])
        self.assert_refusal(sent, second, CAPACITY_REASON, "command_dedupe_max_entries", 1)
        self.assertIn("command dedupe: up to 1 task_ids held, each for at most 86400000ms", banner)

    def test_main_uses_the_configured_maximum_hold(self):
        short, long_lived = self.live("task-main-short"), self.live("task-main-long", valid_for_ms=600000)
        sent, banner = self.run_loop([self.status, short, long_lived], "--command-max-hold-ms", "180000")
        self.assertIn(short["event"]["event_id"], [e["event"]["event_id"] for e in sent])
        self.assert_refusal(sent, long_lived, TOO_LONG_REASON, "command_max_hold_ms", 180000)
        self.assertIn("command dedupe: up to 4096 task_ids held, each for at most 180000ms", banner)

    def test_main_with_the_defaults_forwards_both(self):
        # The control for the two tests above: without the flags nothing is refused.
        first, second = self.live("task-main-a"), self.live("task-main-b", valid_for_ms=600000)
        sent, _banner = self.run_loop([self.status, first, second])
        ids = [e["event"]["event_id"] for e in sent]
        self.assertIn(first["event"]["event_id"], ids)
        self.assertIn(second["event"]["event_id"], ids)
        self.assertEqual([], [e for e in sent if e["event"]["event_subtype"] == "TASK_ACK"])


if __name__ == "__main__":
    unittest.main()
