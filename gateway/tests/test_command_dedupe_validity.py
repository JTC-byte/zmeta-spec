"""A duplicate COMMAND_EVENT is not forwarded a second time while the command can still execute.

Contract 13.2: "Duplicate COMMAND_EVENTs MUST NOT be forwarded for execution a
second time." The gateway used to hold a command's task_id for the smaller of
its valid_for_ms and 300 s, so the shipped example command, valid for 600 s,
was forwarded again when its duplicate arrived at 301 s. The id is now held for
the command's whole validity, including the lead time to valid_from_ts, and
the cache is bounded by count: when it is full a new command is refused
instead of an old id being forgotten.

What this file does not prove: the cache is in memory, so a gateway restart
forgets every held id, and a command whose validity has ended is not refused
here (the executing layer owns expiry). Both limits are stated in the gateway
README.
"""

import importlib.util
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
TIMING = {
    "time_source": "GPS_PPS",
    "sync_state": "LOCKED",
    "est_error_ms": 1,
    "last_sync_ts": "2025-01-17T14:31:50Z",
}
SOURCE = {"platform_id": "comms-node-1", "node_role": "GATEWAY", "producer": "sensorops"}


def shipped_command():
    """The first COMMAND_EVENT of the shipped command examples, valid for 600 s."""
    with open(ROOT / "examples" / "zmeta-command-examples.jsonl", "r", encoding="utf-8") as handle:
        for line in handle:
            event = json.loads(line)
            if event["event"]["event_type"] == "COMMAND_EVENT":
                return event
    raise AssertionError("no shipped command example")


def command(task_id, valid_for_ms=60000, valid_from_ts=None):
    payload = {
        "task_id": task_id,
        "task_type": "GOTO",
        "target_geo": {"lat": 34.0101, "lon": -118.0101},
        "valid_for_ms": valid_for_ms,
        "requires_deconfliction": True,
        "timing_quality": dict(TIMING),
    }
    if valid_from_ts is not None:
        payload["valid_from_ts"] = valid_from_ts
    return {
        "zmeta_version": "1.0",
        "event": {
            "event_id": str(uuid7()),
            "event_type": "COMMAND_EVENT",
            "event_subtype": "GOTO",
            "ts": "2025-01-17T14:32:10Z",
        },
        "source": dict(SOURCE),
        "profile": "L",
        "payload": payload,
    }


def time_status(ts="2025-01-17T14:31:50Z"):
    return {
        "zmeta_version": "1.0",
        "event": {
            "event_id": str(uuid7()),
            "event_type": "SYSTEM_EVENT",
            "event_subtype": "TIME_STATUS",
            "ts": ts,
        },
        "source": dict(SOURCE),
        "payload": {
            "system_type": "TIME_STATUS",
            "state": "LOCKED",
            "metrics": dict(TIMING, last_sync_ts=ts),
        },
    }


class Clock:
    """A settable stand-in for the gateway module's monotonic clock."""

    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


class CommandDedupeValidityTest(unittest.TestCase):
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

    def send(self, event, at_s, cache=None, metrics=None):
        self.assertEqual([], list(self.validator.iter_errors(event)), "input must be schema-valid")
        self.clock.now = 1000.0 + at_s
        return gateway.process_message(
            json.dumps(event).encode("utf-8"),
            self.validator,
            self.policy,
            "L",
            self.cache if cache is None else cache,
            "json",
            timing_state=self.state,
            metrics=metrics,
            now=WALL + timedelta(seconds=at_s),
        )

    def assert_forwarded(self, event, out):
        self.assertEqual([event], out)

    def assert_duplicate(self, out):
        self.assertEqual(1, len(out), out)
        self.assertEqual("TASK_ACK", out[0]["event"]["event_subtype"])
        self.assertEqual("DUPLICATE_IGNORED", out[0]["payload"]["state"])
        self.assertEqual("TASK_DUPLICATE", out[0]["payload"]["metrics"]["reason_code"])

    def test_the_shipped_600_s_command_is_not_forwarded_again_while_valid(self):
        cmd = shipped_command()
        self.assertEqual(600000, cmd["payload"]["valid_for_ms"])
        # The shipped command carries no per-event timing quality, so its node's
        # TIME_STATUS must be current at the command's own ts.
        self.assertEqual(SOURCE, cmd["source"])
        self.state.record(time_status(cmd["event"]["ts"]))
        self.assert_forwarded(cmd, self.send(cmd, 0))
        for at_s in (10, 301, 599):
            with self.subTest(at_s=at_s):
                self.assert_duplicate(self.send(cmd, at_s))

    def test_a_short_command_is_still_deduped_inside_its_validity(self):
        # The control for the test above: the 300 s cap never affected this one.
        cmd = command("task-short", valid_for_ms=60000)
        self.assert_forwarded(cmd, self.send(cmd, 0))
        self.assert_duplicate(self.send(cmd, 59))

    def test_the_id_is_released_when_the_validity_ends(self):
        cmd = command("task-release", valid_for_ms=60000)
        self.assert_forwarded(cmd, self.send(cmd, 0))
        self.assert_forwarded(cmd, self.send(cmd, 61))

    def test_lead_time_to_valid_from_ts_is_held(self):
        # Valid for 60 s starting 600 s after receipt: executable until 660 s.
        start = (WALL + timedelta(seconds=600)).strftime("%Y-%m-%dT%H:%M:%SZ")
        cmd = command("task-lead", valid_for_ms=60000, valid_from_ts=start)
        self.assert_forwarded(cmd, self.send(cmd, 0))
        for at_s in (61, 301, 659):
            with self.subTest(at_s=at_s):
                self.assert_duplicate(self.send(cmd, at_s))

    def test_a_past_valid_from_ts_adds_no_hold(self):
        start = (WALL - timedelta(seconds=600)).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.assertEqual(60000, gateway.command_hold_ms({"valid_for_ms": 60000, "valid_from_ts": start}, now=WALL))
        self.assertEqual(60000, gateway.command_hold_ms({"valid_for_ms": 60000, "valid_from_ts": "garbageZ"}, now=WALL))

    def test_an_enormous_validity_is_held_without_overflow(self):
        for valid_for_ms in (10 ** 15, 10 ** 400):
            with self.subTest(valid_for_ms=valid_for_ms):
                cmd = command(f"task-huge-{len(str(valid_for_ms))}", valid_for_ms=valid_for_ms)
                self.assert_forwarded(cmd, self.send(cmd, 0))
                self.assert_duplicate(self.send(cmd, 10 ** 9))

    def test_hold_falls_back_for_a_value_that_is_not_a_positive_integer(self):
        for bad in (None, "x", 0, -5, float("inf"), [1]):
            with self.subTest(valid_for_ms=bad):
                self.assertEqual(60000, gateway.command_hold_ms({"valid_for_ms": bad}, now=WALL))
        self.assertEqual(60000, gateway.command_hold_ms(None, now=WALL))

    def test_a_full_cache_refuses_a_new_command_and_forgets_nothing(self):
        cache = gateway.TaskDedupeCache(max_entries=2)
        first, second, third = (command(f"task-{n}", valid_for_ms=600000) for n in (1, 2, 3))
        self.assert_forwarded(first, self.send(first, 0, cache=cache))
        self.assert_forwarded(second, self.send(second, 1, cache=cache))

        metrics = mock.Mock()
        out = self.send(third, 2, cache=cache, metrics=metrics)

        self.assertNotIn(third, out)
        self.assertEqual(1, len(out), out)
        refusal = out[0]
        self.assertEqual("TASK_ACK", refusal["event"]["event_subtype"])
        self.assertEqual("REJECTED", refusal["payload"]["state"])
        self.assertEqual("TASK_REJECTED", refusal["payload"]["metrics"]["reason_code"])
        self.assertEqual("task-3", refusal["payload"]["metrics"]["task_id"])
        self.assertEqual(third["event"]["event_id"], refusal["payload"]["metrics"]["original_event_id"])
        self.assertEqual([], list(self.validator.iter_errors(refusal)), "the refusal must be valid")
        self.assertEqual("TASK_REJECTED", metrics.record_violation.call_args[0][0])
        # Nothing was forgotten to make room: both held commands still dedupe.
        self.assert_duplicate(self.send(first, 3, cache=cache))
        self.assert_duplicate(self.send(second, 3, cache=cache))
        # The refused command was not recorded, so it is still refused, not "duplicate".
        self.assertEqual("REJECTED", self.send(third, 4, cache=cache)[0]["payload"]["state"])

    def test_capacity_returns_when_a_held_command_expires(self):
        cache = gateway.TaskDedupeCache(max_entries=1)
        short = command("task-a", valid_for_ms=60000)
        later = command("task-b", valid_for_ms=60000)
        self.assert_forwarded(short, self.send(short, 0, cache=cache))
        self.assertEqual("REJECTED", self.send(later, 30, cache=cache)[0]["payload"]["state"])
        self.assert_forwarded(later, self.send(later, 61, cache=cache))

    def test_a_duplicate_takes_no_capacity(self):
        cache = gateway.TaskDedupeCache(max_entries=2)
        first = command("task-1", valid_for_ms=600000)
        second = command("task-2", valid_for_ms=600000)
        self.assert_forwarded(first, self.send(first, 0, cache=cache))
        for at_s in (1, 2, 3):
            self.assert_duplicate(self.send(first, at_s, cache=cache))
        self.assert_forwarded(second, self.send(second, 4, cache=cache))

    def test_check_and_set_still_reports_duplicates(self):
        cache = gateway.TaskDedupeCache()
        self.assertFalse(cache.check_and_set("t", 600000))
        self.clock.now += 301
        self.assertTrue(cache.check_and_set("t", 600000))

    def test_the_capacity_is_a_setting(self):
        with mock.patch("sys.argv", ["gateway.py", "--profile", "H"]):
            args = gateway.parse_args()
        self.assertEqual(
            gateway.DEFAULT_COMMAND_DEDUPE_MAX_ENTRIES,
            gateway.build_settings(ROOT, args, {})["command_dedupe_max_entries"],
        )
        self.assertEqual(
            16, gateway.build_settings(ROOT, args, {"command_dedupe_max_entries": 16})["command_dedupe_max_entries"]
        )
        for bad in (0, -1, "many"):
            with self.subTest(value=bad):
                with self.assertRaises(ValueError):
                    gateway.build_settings(ROOT, args, {"command_dedupe_max_entries": bad})


if __name__ == "__main__":
    unittest.main()
