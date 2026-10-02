"""The running gateway keeps a bounded index of recent events, not every event it forwards.

`ValidationState.record` used to keep each forwarded event whole, with its id,
for as long as the process ran. The lineage check reads that store for one
thing, a parent's `event_type`.

What is pinned here:

- `ValidationState()` with no cap behaves as it always has: every recorded
  event is held whole and every id is remembered. The offline tools build it
  that way and validate one bounded file per run.
- `ValidationState(event_index_max_entries=N)` keeps the `event_type` and
  `event_subtype` of the N most recently recorded events and nothing else of
  them. The oldest entry is dropped first. Recording an id again makes it the
  newest, and looking an id up does not.
- A parent that has been dropped is reported by the lineage check with the
  existing `LINEAGE_PARENT_UNRESOLVED` code under the existing policy mode. A
  parent still in the index resolves, and a parent of the wrong type that is
  still in the index is refused.
- The cost of the bound, pinned and not hidden: a parent of the wrong type
  that has left the index is no longer refused. It is reported unresolved,
  which the shipped policy ignores at profile L and warns on at M and H.
- The id sets `validate_deduplication` reads are bounded by the same number.
  The two task sets are each counted on their own; `event_ids` is the event
  index's own keys. A duplicate of a dropped id is not reported; that is the
  stated limit of a bounded state, and the running gateway does not use
  those sets (it has its own time-bounded caches).
- An entry's size does not depend on what a producer wrote: an id longer
  than 64 characters is kept as a 16-byte digest and still matches.
- The cap is a gateway setting with a default and a ceiling, a value that is
  not a positive integer is a startup error on either input path, the flag
  is not coerced, and `main()` hands the setting to the state it builds
  under every profile and input encoding.

What this file does not prove. The memory checks walk what the state can
reach after a few hundred events; they do not measure a process, and the
figures in the README come from a separate measurement. `latest_timing` and
`timing_sources` still grow with the number of distinct sources and are not
bounded here. The index is in memory, so a restart empties it. The
command-evidence index is a separate store with its own cap and is only
checked here for being left alone. Events reach the real `main()` loop here
as JSON at profile M only; the other profiles and encodings are checked for
the cap reaching the state, with no datagram sent.
"""

import contextlib
import copy
import gc
import importlib.util
import io
import json
import sys
import tempfile
import types
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


validators = _load("zmeta_validators_event_index", ROOT / "gateway" / "src" / "validators.py")
gateway = _load("zmeta_gateway_event_index", ROOT / "gateway" / "src" / "gateway.py")

WALL = datetime(2025, 1, 17, 14, 30, 0, tzinfo=timezone.utc)
SENSOR = {"platform_id": "node-01", "node_role": "EDGE", "producer": "rf-sensor"}
FUSER = {"platform_id": "node-02", "node_role": "GATEWAY", "producer": "torch"}
TASKER = {"platform_id": "comms-node-1", "node_role": "GATEWAY", "producer": "sensorops"}

DEFAULT_CAP = 65536
CEILING = 1024 * 1024
NOT_A_CAP = (0, -1, "16", "many", 16.0, True, False, [], {}, CEILING + 1, 10 ** 400)


def z(moment):
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def timing(ts):
    return {
        "time_source": "GPS_PPS",
        "sync_state": "LOCKED",
        "est_error_ms": 1,
        "last_sync_ts": z(ts - timedelta(seconds=20)),
    }


def observation(profile="H", ts=WALL):
    return {
        "zmeta_version": "1.0",
        "event": {
            "event_id": str(uuid7()),
            "event_type": "OBSERVATION_EVENT",
            "event_subtype": "RF",
            "ts": z(ts),
        },
        "source": dict(SENSOR),
        "profile": profile,
        "payload": {
            "modality": "RF",
            "features": {
                "center_freq_hz": 2450000000,
                "bandwidth_hz": 20000000,
                "power_dbm": -35.2,
            },
            "timing_quality": timing(ts),
        },
    }


def fusion(parent_id, profile="H", ts=WALL):
    return {
        "zmeta_version": "1.0",
        "event": {
            "event_id": str(uuid7()),
            "event_type": "FUSION_EVENT",
            "event_subtype": "TRACK_FUSION",
            "ts": z(ts),
        },
        "source": dict(FUSER),
        "profile": profile,
        "payload": {
            "track_id": "track-1",
            "members": [parent_id],
            "stability": 0.6,
            "last_seen_ts": z(ts),
            "timing_quality": timing(ts),
        },
        "confidence": 0.76,
        "lineage": {"based_on": [parent_id]},
    }


def command(task_id, ts=WALL):
    return {
        "zmeta_version": "1.0",
        "event": {
            "event_id": str(uuid7()),
            "event_type": "COMMAND_EVENT",
            "event_subtype": "GOTO",
            "ts": z(ts),
        },
        "source": dict(TASKER),
        "profile": "L",
        "payload": {
            "task_id": task_id,
            "task_type": "GOTO",
            "target_geo": {"lat": 34.0101, "lon": -118.0101},
            "valid_for_ms": 60000,
            "requires_deconfliction": True,
            "timing_quality": timing(ts),
        },
    }


def task_ack(task_id, original_event_id, state="ACCEPTED", ts=WALL):
    return {
        "zmeta_version": "1.0",
        "event": {
            "event_id": str(uuid7()),
            "event_type": "SYSTEM_EVENT",
            "event_subtype": "TASK_ACK",
            "ts": z(ts),
        },
        "source": dict(TASKER),
        "payload": {
            "system_type": "TASK_ACK",
            "state": state,
            "metrics": {"task_id": task_id, "original_event_id": original_event_id},
        },
    }


def time_status(source=None, ts=WALL):
    return {
        "zmeta_version": "1.0",
        "event": {
            "event_id": str(uuid7()),
            "event_type": "SYSTEM_EVENT",
            "event_subtype": "TIME_STATUS",
            "ts": z(ts),
        },
        "source": dict(source or SENSOR),
        "payload": {
            "system_type": "TIME_STATUS",
            "state": "LOCKED",
            "metrics": dict(timing(ts), last_sync_ts=z(ts)),
        },
    }


def eid(event):
    return event["event"]["event_id"]


def reachable_bytes(*roots):
    """The size of everything the given objects can reach, each object counted once."""
    skipped = (type, types.ModuleType, types.FunctionType, types.MethodType, types.BuiltinFunctionType)
    seen, total, stack = set(), 0, list(roots)
    while stack:
        obj = stack.pop()
        if id(obj) in seen or isinstance(obj, skipped):
            continue
        seen.add(id(obj))
        total += sys.getsizeof(obj)
        stack.extend(gc.get_referents(obj))
    return total


LONG = 30000


def codes(violations):
    return [v["code"] for v in violations]


class PolicyCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = validators.load_policy(ROOT / "policy")
        cls.severity_map = cls.policy["violation_severities"]
        cls.lineage_policy = cls.policy["lineage"]

    def lineage(self, event, state, profile="H"):
        return validators.validate_lineage(
            event, self.lineage_policy, state=state, profile=profile, severity_map=self.severity_map
        )

    def dedupe(self, event, state):
        return validators.validate_deduplication(event, state=state, severity_map=self.severity_map)


class UnboundedByDefaultTest(PolicyCase):
    """No cap: the state the offline tools build. Nothing about it changes."""

    def test_no_cap_is_recorded_as_none(self):
        self.assertIsNone(validators.ValidationState().event_index_max_entries)
        self.assertIsNone(
            validators.ValidationState(event_index_max_entries=None).event_index_max_entries
        )

    def test_every_recorded_event_is_held_whole(self):
        state = validators.ValidationState()
        recorded = [observation() for _ in range(3000)]
        for event in recorded:
            state.record(event)
        self.assertEqual(3000, len(state.events))
        self.assertEqual(3000, len(state.event_ids))
        first = state.get_event(eid(recorded[0]))
        self.assertEqual("OBSERVATION_EVENT", first["event_type"])
        self.assertEqual("RF", first["event_subtype"])
        self.assertIs(recorded[0], first["event"])

    def test_the_first_parent_still_resolves_after_many_events(self):
        state = validators.ValidationState()
        parent = observation()
        state.record(parent)
        for _ in range(500):
            state.record(observation())
        ok, violations = self.lineage(fusion(eid(parent)), state)
        self.assertTrue(ok, violations)
        self.assertEqual([], violations)

    def test_the_first_duplicate_is_still_reported_after_many_events(self):
        state = validators.ValidationState()
        first_event = observation()
        first_command = command("task-first")
        first_ack = task_ack("task-first", eid(first_command))
        for event in (first_event, first_command, first_ack):
            state.record(event)
        for index in range(500):
            later = command(f"task-{index}")
            state.record(later)
            state.record(task_ack(f"task-{index}", eid(later)))
        self.assertEqual(["EVENT_DUPLICATE"], codes(self.dedupe(first_event, state)[1]))
        again = command("task-first")
        self.assertEqual(["TASK_DUPLICATE"], codes(self.dedupe(again, state)[1]))
        ack_again = task_ack("task-first", eid(first_command))
        self.assertEqual(["TASK_ACK_DUPLICATE"], codes(self.dedupe(ack_again, state)[1]))


class BoundedIndexTest(PolicyCase):
    def test_the_cap_is_recorded(self):
        self.assertEqual(3, validators.ValidationState(event_index_max_entries=3).event_index_max_entries)

    def test_only_the_most_recent_events_are_kept(self):
        state = validators.ValidationState(event_index_max_entries=3)
        recorded = [observation() for _ in range(5)]
        for event in recorded:
            state.record(event)
        self.assertEqual(3, len(state.events))
        for dropped in recorded[:2]:
            self.assertIsNone(state.get_event(eid(dropped)))
        for kept in recorded[2:]:
            self.assertIsNotNone(state.get_event(eid(kept)))

    def test_exactly_the_cap_is_kept_and_one_more_drops_the_oldest(self):
        state = validators.ValidationState(event_index_max_entries=3)
        recorded = [observation() for _ in range(3)]
        for event in recorded:
            state.record(event)
        self.assertEqual(3, len(state.events))
        self.assertIsNotNone(state.get_event(eid(recorded[0])))
        extra = observation()
        state.record(extra)
        self.assertEqual(3, len(state.events))
        self.assertIsNone(state.get_event(eid(recorded[0])))
        self.assertIsNotNone(state.get_event(eid(recorded[1])))
        self.assertIsNotNone(state.get_event(eid(extra)))

    def test_an_entry_is_the_type_and_subtype_and_nothing_else(self):
        state = validators.ValidationState(event_index_max_entries=3)
        event = fusion(str(uuid7()))
        state.record(event)
        self.assertEqual(
            {"event_type": "FUSION_EVENT", "event_subtype": "TRACK_FUSION"},
            state.get_event(eid(event)),
        )
        held = repr(state.events) + repr(state.event_ids)
        self.assertNotIn("track-1", held)
        self.assertNotIn("stability", held)

    def test_recording_an_id_again_makes_it_the_newest(self):
        state = validators.ValidationState(event_index_max_entries=3)
        a, b, c, d = (observation() for _ in range(4))
        for event in (a, b, c, a, d):
            state.record(event)
        self.assertIsNotNone(state.get_event(eid(a)))
        self.assertIsNone(state.get_event(eid(b)))
        self.assertIsNotNone(state.get_event(eid(c)))
        self.assertIsNotNone(state.get_event(eid(d)))
        self.assertTrue(eid(a) in state.event_ids)
        self.assertFalse(eid(b) in state.event_ids)

    def test_recording_again_an_id_that_is_not_the_oldest_drops_nothing(self):
        state = validators.ValidationState(event_index_max_entries=3)
        a, b, c, d = (observation() for _ in range(4))
        for event in (a, b, c, b):
            state.record(event)
        self.assertEqual(3, len(state.events))
        for kept in (a, b, c):
            self.assertIsNotNone(state.get_event(eid(kept)))
        state.record(d)
        self.assertIsNone(state.get_event(eid(a)))
        for kept in (b, c, d):
            self.assertIsNotNone(state.get_event(eid(kept)))

    def test_looking_an_id_up_does_not_make_it_newer(self):
        state = validators.ValidationState(event_index_max_entries=2)
        a, b, c = (observation() for _ in range(3))
        state.record(a)
        state.record(b)
        self.assertIsNotNone(state.get_event(eid(a)))
        self.assertTrue(eid(a) in state.event_ids)
        self.assertEqual(["EVENT_DUPLICATE"], codes(self.dedupe(a, state)[1]))
        state.record(c)
        self.assertIsNone(state.get_event(eid(a)))
        self.assertFalse(eid(a) in state.event_ids)
        self.assertIsNotNone(state.get_event(eid(b)))

    def test_event_ids_is_the_index_and_not_a_second_copy(self):
        state = validators.ValidationState(event_index_max_entries=3)
        recorded = [observation() for _ in range(5)]
        for event in recorded:
            state.record(event)
        self.assertEqual(3, len(state.event_ids))
        self.assertEqual(list(state.events), list(state.event_ids))
        self.assertFalse(eid(recorded[1]) in state.event_ids)
        self.assertTrue(eid(recorded[2]) in state.event_ids)

    def test_the_type_strings_are_shared_between_entries(self):
        # Each parsed event brings its own copy of "OBSERVATION_EVENT". The
        # index keeps one, which is part of what an entry is measured to cost.
        state = validators.ValidationState(event_index_max_entries=3)
        first = json.loads(json.dumps(observation()))
        second = json.loads(json.dumps(observation()))
        self.assertIsNot(first["event"]["event_type"], second["event"]["event_type"])
        state.record(first)
        state.record(second)
        one, two = state.events[eid(first)], state.events[eid(second)]
        self.assertIs(one[0], two[0])
        self.assertIs(one[1], two[1])

    def test_the_latest_record_of_an_id_decides_its_type(self):
        for cap in (None, 3):
            with self.subTest(cap=cap):
                state = validators.ValidationState(event_index_max_entries=cap)
                first = observation()
                second = fusion(str(uuid7()))
                second["event"]["event_id"] = eid(first)
                state.record(first)
                state.record(second)
                self.assertEqual("FUSION_EVENT", state.get_event(eid(first))["event_type"])
                self.assertEqual("TRACK_FUSION", state.get_event(eid(first))["event_subtype"])

    def test_an_event_without_an_id_is_not_indexed(self):
        for cap in (None, 3):
            with self.subTest(cap=cap):
                state = validators.ValidationState(event_index_max_entries=cap)
                event = observation()
                del event["event"]["event_id"]
                state.record(event)
                self.assertEqual(0, len(state.events))
                self.assertEqual(0, len(state.event_ids))

    def test_a_type_or_subtype_that_is_missing_or_not_a_string_is_recorded_as_it_is(self):
        # The offline tools record seed events that have not been validated.
        for cap in (None, 3):
            with self.subTest(cap=cap):
                state = validators.ValidationState(event_index_max_entries=cap)
                no_subtype = observation()
                del no_subtype["event"]["event_subtype"]
                odd = observation()
                odd["event"]["event_type"] = ["OBSERVATION_EVENT"]
                odd["event"]["event_subtype"] = 7
                state.record(no_subtype)
                state.record(odd)
                self.assertEqual("OBSERVATION_EVENT", state.get_event(eid(no_subtype))["event_type"])
                self.assertIsNone(state.get_event(eid(no_subtype))["event_subtype"])
                self.assertEqual(["OBSERVATION_EVENT"], state.get_event(eid(odd))["event_type"])
                self.assertEqual(7, state.get_event(eid(odd))["event_subtype"])

    def test_a_cap_of_one_keeps_the_last_event_only(self):
        state = validators.ValidationState(event_index_max_entries=1)
        first, second = observation(), observation()
        state.record(first)
        state.record(second)
        self.assertIsNone(state.get_event(eid(first)))
        self.assertIsNotNone(state.get_event(eid(second)))
        self.assertEqual(1, len(state.events))

    def test_a_dropped_parent_is_reported_unresolved(self):
        state = validators.ValidationState(event_index_max_entries=3)
        parent = observation()
        state.record(parent)
        for _ in range(3):
            state.record(observation())
        child = fusion(eid(parent))
        ok, violations = self.lineage(child, state)
        self.assertEqual(["LINEAGE_PARENT_UNRESOLVED"], codes(violations))
        self.assertEqual([eid(parent)], violations[0]["details"]["unresolved"])
        self.assertEqual("warn", violations[0]["severity"])
        self.assertTrue(ok)

    def test_a_dropped_parent_follows_the_policy_mode_for_the_profile(self):
        state = validators.ValidationState(event_index_max_entries=1)
        parent = observation()
        state.record(parent)
        state.record(observation())
        self.assertIsNone(state.get_event(eid(parent)))
        # The same dropped parent: a warning at M and H, nothing at L.
        for profile in ("M", "H"):
            ok, violations = self.lineage(fusion(eid(parent), profile=profile), state, profile=profile)
            self.assertEqual(["LINEAGE_PARENT_UNRESOLVED"], codes(violations), profile)
            self.assertTrue(ok)
        ok, violations = self.lineage(fusion(eid(parent), profile="L"), state, profile="L")
        self.assertTrue(ok, violations)
        self.assertEqual([], violations)

    def test_a_dropped_parent_of_the_wrong_type_is_no_longer_refused(self):
        # The cost of the bound. While the parent is in the index its type is
        # checked and the citing event is refused. Once it has left, the
        # check cannot tell it from a parent it never saw.
        parent = command("task-parent")
        for profile, expected in (("H", ["LINEAGE_PARENT_UNRESOLVED"]), ("M", ["LINEAGE_PARENT_UNRESOLVED"]), ("L", [])):
            with self.subTest(profile=profile):
                unbounded = validators.ValidationState()
                bounded = validators.ValidationState(event_index_max_entries=2)
                for state in (unbounded, bounded):
                    state.record(parent)
                child = fusion(eid(parent), profile=profile)
                for state in (unbounded, bounded):
                    ok, violations = self.lineage(child, state, profile=profile)
                    self.assertFalse(ok)
                    self.assertEqual(["LINEAGE_PARENT_TYPE_INVALID"], codes(violations))
                for state in (unbounded, bounded):
                    state.record(observation())
                    state.record(observation())
                ok, violations = self.lineage(child, unbounded, profile=profile)
                self.assertFalse(ok)
                self.assertEqual(["LINEAGE_PARENT_TYPE_INVALID"], codes(violations))
                ok, violations = self.lineage(child, bounded, profile=profile)
                self.assertTrue(ok)
                self.assertEqual(expected, codes(violations))

    def test_a_kept_parent_resolves(self):
        state = validators.ValidationState(event_index_max_entries=3)
        parent = observation()
        state.record(observation())
        state.record(parent)
        state.record(observation())
        ok, violations = self.lineage(fusion(eid(parent)), state)
        self.assertTrue(ok, violations)
        self.assertEqual([], violations)

    def test_a_kept_parent_of_the_wrong_type_is_still_refused(self):
        state = validators.ValidationState(event_index_max_entries=3)
        parent = command("task-parent")
        state.record(parent)
        ok, violations = self.lineage(fusion(eid(parent)), state)
        self.assertFalse(ok)
        self.assertEqual(["LINEAGE_PARENT_TYPE_INVALID"], codes(violations))

    def test_the_id_sets_are_bounded_and_drop_the_oldest(self):
        state = validators.ValidationState(event_index_max_entries=2)
        commands = [command(f"task-{index}") for index in range(4)]
        acks = [task_ack(f"task-{index}", eid(commands[index])) for index in range(4)]
        for cmd, ack in zip(commands, acks):
            state.record(cmd)
            state.record(ack)
        self.assertEqual(2, len(state.event_ids))
        self.assertEqual(2, len(state.command_task_ids))
        self.assertEqual(2, len(state.task_ack_keys))
        self.assertFalse("task-1" in state.command_task_ids)
        self.assertTrue("task-2" in state.command_task_ids)
        self.assertTrue("task-3" in state.command_task_ids)
        self.assertFalse(("task-1", eid(commands[1]), "ACCEPTED") in state.task_ack_keys)
        self.assertTrue(("task-2", eid(commands[2]), "ACCEPTED") in state.task_ack_keys)

    def test_adding_a_task_id_or_an_ack_key_again_makes_it_the_newest(self):
        state = validators.ValidationState(event_index_max_entries=2)
        commands = {name: command(name) for name in ("t1", "t2", "t3")}
        for name in ("t1", "t2", "t1", "t3"):
            state.record(command(name))
            state.record(task_ack(name, eid(commands[name])))
        self.assertTrue("t1" in state.command_task_ids)
        self.assertFalse("t2" in state.command_task_ids)
        self.assertTrue("t3" in state.command_task_ids)
        self.assertTrue(("t1", eid(commands["t1"]), "ACCEPTED") in state.task_ack_keys)
        self.assertFalse(("t2", eid(commands["t2"]), "ACCEPTED") in state.task_ack_keys)
        self.assertTrue(("t3", eid(commands["t3"]), "ACCEPTED") in state.task_ack_keys)

    def test_adding_again_a_key_that_is_not_the_oldest_drops_nothing(self):
        state = validators.ValidationState(event_index_max_entries=2)
        commands = {name: command(name) for name in ("t1", "t2")}
        for name in ("t1", "t2", "t2"):
            state.record(command(name))
            state.record(task_ack(name, eid(commands[name])))
        self.assertEqual(2, len(state.command_task_ids))
        self.assertEqual(2, len(state.task_ack_keys))
        self.assertTrue("t1" in state.command_task_ids)
        self.assertTrue(("t1", eid(commands["t1"]), "ACCEPTED") in state.task_ack_keys)

    def test_asking_whether_a_key_is_held_does_not_make_it_newer(self):
        state = validators.ValidationState(event_index_max_entries=2)
        commands = {name: command(name) for name in ("t1", "t2", "t3")}
        for name in ("t1", "t2"):
            state.record(commands[name])
            state.record(task_ack(name, eid(commands[name])))
        self.assertTrue("t1" in state.command_task_ids)
        self.assertTrue(("t1", eid(commands["t1"]), "ACCEPTED") in state.task_ack_keys)
        self.assertEqual(["TASK_DUPLICATE"], codes(self.dedupe(command("t1"), state)[1]))
        self.assertEqual(
            ["TASK_ACK_DUPLICATE"], codes(self.dedupe(task_ack("t1", eid(commands["t1"])), state)[1])
        )
        state.record(commands["t3"])
        state.record(task_ack("t3", eid(commands["t3"])))
        self.assertFalse("t1" in state.command_task_ids)
        self.assertTrue("t2" in state.command_task_ids)
        self.assertFalse(("t1", eid(commands["t1"]), "ACCEPTED") in state.task_ack_keys)
        self.assertTrue(("t2", eid(commands["t2"]), "ACCEPTED") in state.task_ack_keys)

    def test_each_id_set_is_counted_on_its_own(self):
        state = validators.ValidationState(event_index_max_entries=2)
        cmd = command("task-kept")
        ack = task_ack("task-kept", eid(cmd))
        state.record(cmd)
        state.record(ack)
        for _ in range(5):
            state.record(observation())
        self.assertFalse(eid(cmd) in state.event_ids)
        self.assertTrue("task-kept" in state.command_task_ids)
        self.assertTrue(("task-kept", eid(cmd), "ACCEPTED") in state.task_ack_keys)

    def test_a_duplicate_of_a_kept_id_is_reported(self):
        state = validators.ValidationState(event_index_max_entries=2)
        event = observation()
        cmd = command("task-a")
        ack = task_ack("task-a", eid(cmd))
        state.record(cmd)
        state.record(ack)
        state.record(event)
        self.assertEqual(["EVENT_DUPLICATE"], codes(self.dedupe(event, state)[1]))
        self.assertEqual(["TASK_DUPLICATE"], codes(self.dedupe(command("task-a"), state)[1]))
        self.assertEqual(
            ["TASK_ACK_DUPLICATE"], codes(self.dedupe(task_ack("task-a", eid(cmd)), state)[1])
        )

    def test_a_duplicate_of_a_dropped_id_is_not_reported(self):
        # The stated limit of a bounded state. The running gateway does not
        # call validate_deduplication; it has its own time-bounded caches.
        state = validators.ValidationState(event_index_max_entries=2)
        old_event = observation()
        old_command = command("task-old")
        old_ack = task_ack("task-old", eid(old_command))
        for event in (old_event, old_command, old_ack):
            state.record(event)
        for index in range(2):
            later = command(f"task-{index}")
            state.record(later)
            state.record(task_ack(f"task-{index}", eid(later)))
        for copy_of_dropped in (old_event, command("task-old"), task_ack("task-old", eid(old_command))):
            ok, violations = self.dedupe(copy_of_dropped, state)
            self.assertTrue(ok, violations)
            self.assertEqual([], violations)

    def test_a_long_id_is_kept_as_a_digest_and_still_matches(self):
        state = validators.ValidationState(event_index_max_entries=4)
        long_task = "t" * LONG
        other_long_task = "t" * (LONG - 1) + "u"
        cmd = command(long_task)
        ack = task_ack(long_task, "e" * LONG)
        seed = observation()
        seed["event"]["event_id"] = "i" * LONG
        for event in (cmd, ack, seed):
            state.record(event)

        self.assertTrue(long_task in state.command_task_ids)
        self.assertFalse(other_long_task in state.command_task_ids)
        self.assertEqual(["TASK_DUPLICATE"], codes(self.dedupe(command(long_task), state)[1]))
        self.assertEqual([], codes(self.dedupe(command(other_long_task), state)[1]))
        self.assertEqual(
            ["TASK_ACK_DUPLICATE"], codes(self.dedupe(task_ack(long_task, "e" * LONG), state)[1])
        )
        self.assertEqual([], codes(self.dedupe(task_ack(long_task, "e" * (LONG - 1) + "f"), state)[1]))
        self.assertEqual("OBSERVATION_EVENT", state.get_event("i" * LONG)["event_type"])
        self.assertIsNone(state.get_event("i" * (LONG - 1) + "j"))
        self.assertTrue("i" * LONG in state.event_ids)

        def parts(key):
            return key if isinstance(key, tuple) else (key,)

        kept = [part for store in (state.events, state.command_task_ids, state.task_ack_keys)
                for key in store for part in parts(key)]
        self.assertTrue(kept)
        for part in kept:
            if isinstance(part, bytes):
                self.assertEqual(16, len(part))
            else:
                self.assertLessEqual(len(part), 64)
        self.assertEqual(4, sum(isinstance(part, bytes) for part in kept))

    def test_a_key_of_64_characters_is_kept_whole_and_one_of_65_is_not(self):
        state = validators.ValidationState(event_index_max_entries=4)
        state.record(command("a" * 64))
        state.record(command("b" * 65))
        kept = list(state.command_task_ids)
        self.assertEqual("a" * 64, kept[0])
        self.assertIsInstance(kept[1], bytes)
        self.assertTrue("b" * 65 in state.command_task_ids)
        # A digest never matches a short key, whatever the short key spells.
        self.assertFalse(kept[1].decode("latin-1") in state.command_task_ids)

    def test_what_a_bounded_state_holds_does_not_grow_with_what_a_producer_wrote(self):
        count = 300
        bounded = validators.ValidationState(event_index_max_entries=count)
        unbounded = validators.ValidationState()
        for index in range(count):
            task = f"{index:05d}" + "t" * LONG
            cmd = command(task)
            ack = task_ack(task, f"{index:05d}" + "e" * LONG)
            obs = observation()
            obs["payload"]["features"]["blob"] = f"{index:05d}" + "x" * LONG
            for state in (bounded, unbounded):
                for event in (cmd, ack, obs):
                    state.record(event)

        def stores(state):
            return reachable_bytes(state.events, state.event_ids, state.command_task_ids, state.task_ack_keys)

        self.assertEqual(count, len(bounded.command_task_ids))
        self.assertEqual(count, len(bounded.task_ack_keys))
        # Under 1 KB for each round of three events; the unbounded state
        # holds the three 30 KB strings each round brought.
        self.assertLess(stores(bounded), count * 1000)
        self.assertGreater(stores(unbounded), count * 2 * LONG)

    def test_an_empty_bounded_state_reports_no_duplicate(self):
        state = validators.ValidationState(event_index_max_entries=2)
        ok, violations = self.dedupe(command("task-a"), state)
        self.assertTrue(ok, violations)
        self.assertEqual([], violations)

    def test_the_command_evidence_index_keeps_its_own_cap(self):
        state = validators.ValidationState(event_index_max_entries=2)
        recorded = [observation() for _ in range(5)]
        for event in recorded:
            state.record(event)
        self.assertEqual(2, len(state.events))
        self.assertEqual(5, len(state.command_evidence))
        self.assertEqual(
            validators.DEFAULT_COMMAND_EVIDENCE_INDEX_MAX_ENTRIES, state.command_evidence_max_entries
        )
        both = validators.ValidationState(command_evidence_max_entries=4, event_index_max_entries=2)
        for event in recorded:
            both.record(event)
        self.assertEqual(2, len(both.events))
        self.assertEqual(4, len(both.command_evidence))

    def test_a_source_timing_status_outlives_the_index(self):
        # latest_timing is not part of the bound: a quiet source's last
        # TIME_STATUS must not be forgotten because other events arrived.
        state = validators.ValidationState(event_index_max_entries=2)
        status = time_status()
        state.record(status)
        for _ in range(5):
            state.record(observation())
        self.assertIsNone(state.get_event(eid(status)))
        _key, latest = state.get_timing(observation())
        self.assertIsNotNone(latest)
        self.assertEqual(z(WALL), latest["_event_ts"])


class CapValueTest(unittest.TestCase):
    def test_the_default_and_the_ceiling(self):
        self.assertEqual(DEFAULT_CAP, validators.DEFAULT_EVENT_INDEX_MAX_ENTRIES)
        self.assertEqual(CEILING, validators.MAX_EVENT_INDEX_MAX_ENTRIES)

    def test_a_cap_that_is_not_a_positive_integer_within_the_ceiling_is_refused(self):
        for bad in NOT_A_CAP:
            with self.subTest(value=bad):
                with self.assertRaises(ValueError):
                    validators.ValidationState(event_index_max_entries=bad)
                with self.assertRaises(ValueError):
                    validators.normalize_event_index_max_entries(bad)
        with self.assertRaises(ValueError):
            validators.normalize_event_index_max_entries(None)

    def test_one_and_the_ceiling_are_accepted(self):
        for good in (1, 2, DEFAULT_CAP, CEILING):
            with self.subTest(value=good):
                self.assertEqual(good, validators.normalize_event_index_max_entries(good))
                self.assertEqual(
                    good, validators.ValidationState(event_index_max_entries=good).event_index_max_entries
                )

    def test_the_refusal_names_the_setting_and_the_range(self):
        with self.assertRaises(ValueError) as caught:
            validators.normalize_event_index_max_entries(0)
        message = str(caught.exception)
        self.assertIn("event_index_max_entries", message)
        self.assertIn(str(CEILING), message)


def args_with(*argv):
    with mock.patch("sys.argv", ["gateway.py", "--profile", "H", *argv]):
        return gateway.parse_args()


class SettingsTest(unittest.TestCase):
    KEY = "event_index_max_entries"
    FLAG = "--event-index-max-entries"

    def test_the_cap_is_a_setting_and_the_flag_wins(self):
        self.assertEqual(DEFAULT_CAP, gateway.build_settings(ROOT, args_with(), {})[self.KEY])
        self.assertEqual(900, gateway.build_settings(ROOT, args_with(), {self.KEY: 900})[self.KEY])
        self.assertEqual(
            1200, gateway.build_settings(ROOT, args_with(self.FLAG, "1200"), {self.KEY: 900})[self.KEY]
        )

    def test_a_cap_that_is_not_a_positive_integer_is_refused(self):
        for bad in (0, -1, "many", "16", 16.0, True, None):
            with self.subTest(value=bad):
                with self.assertRaises(ValueError):
                    gateway.build_settings(ROOT, args_with(), {self.KEY: bad})
        with self.assertRaises(ValueError):
            gateway.build_settings(ROOT, args_with(self.FLAG, "0"), {})

    def test_the_flag_is_not_coerced(self):
        # int() alone would read each of these as a number.
        for text in ("-1", "+7", " 7", "7 ", "1_000", "0007", "00", "7.0", "\u0667", "\uff17", "many", ""):
            with self.subTest(text=text):
                with contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit):
                        args_with(self.FLAG, text)
        self.assertEqual(7, args_with(self.FLAG, "7").event_index_max_entries)
        self.assertEqual(1000, args_with(self.FLAG, "1000").event_index_max_entries)
        self.assertEqual(0, args_with(self.FLAG, "0").event_index_max_entries)

    def test_a_bad_config_value_is_refused_even_when_a_good_flag_overrides_it(self):
        for bad in (0, "16", True, None, CEILING + 1):
            with self.subTest(value=bad):
                with self.assertRaises(ValueError):
                    gateway.build_settings(ROOT, args_with(self.FLAG, "900"), {self.KEY: bad})

    def test_a_cap_above_the_ceiling_is_refused(self):
        self.assertEqual(CEILING, gateway.build_settings(ROOT, args_with(), {self.KEY: CEILING})[self.KEY])
        self.assertEqual(
            CEILING, gateway.build_settings(ROOT, args_with(self.FLAG, str(CEILING)), {})[self.KEY]
        )
        with self.assertRaises(ValueError):
            gateway.build_settings(ROOT, args_with(), {self.KEY: CEILING + 1})
        with self.assertRaises(ValueError):
            gateway.build_settings(ROOT, args_with(self.FLAG, str(CEILING + 1)), {})

    def test_a_bad_flag_does_not_fall_back_to_a_good_config_value(self):
        with self.assertRaises(ValueError):
            gateway.build_settings(ROOT, args_with(self.FLAG, "0"), {self.KEY: 900})

    def test_the_example_config_states_the_default(self):
        with open(ROOT / "gateway" / "config" / "gateway-config.example.json", "r", encoding="utf-8") as handle:
            example = json.load(handle)
        self.assertEqual(DEFAULT_CAP, example[self.KEY])


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


class MainLoopTest(unittest.TestCase):
    """Through the real main() receive loop, with the two UDP sockets replaced.

    The state main() builds is captured as it is built; nothing about it is
    replaced.
    """

    def setUp(self):
        self.now = datetime.now(timezone.utc).replace(microsecond=0)
        self.state = None

    def run_loop(self, events, *flags, profile="M"):
        sock_in = _LoopSocket([json.dumps(event).encode("utf-8") for event in events])
        sock_out = _LoopSocket()
        sockets = [sock_in, sock_out]
        argv = ["gateway.py", "--profile", profile, "--listen-port", "45595", "--forward-port", "45594",
                "--no-metrics", *flags]
        out, err = io.StringIO(), io.StringIO()
        real_state = gateway.ValidationState

        def capture(*args, **kwargs):
            self.state = real_state(*args, **kwargs)
            return self.state

        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch("sys.argv", argv))
            stack.enter_context(mock.patch.object(gateway.socket, "socket", lambda *a, **k: sockets.pop(0)))
            stack.enter_context(mock.patch.object(gateway, "ValidationState", capture))
            stack.enter_context(contextlib.redirect_stdout(out))
            stack.enter_context(contextlib.redirect_stderr(err))
            with self.assertRaises(_StopReceiveLoop):
                gateway.main()
        self.stdout = out.getvalue()
        self.stderr = err.getvalue()
        return [json.loads(payload) for payload, _addr in sock_out.sent]

    def chain(self):
        """Three observations, then a fusion citing the first and one citing the third."""
        observations = [observation(profile="M", ts=self.now) for _ in range(3)]
        cites_first = fusion(eid(observations[0]), profile="M", ts=self.now)
        cites_third = fusion(eid(observations[2]), profile="M", ts=self.now)
        return observations, cites_first, cites_third

    @staticmethod
    def unresolved(sent):
        return [
            e for e in sent
            if e["event"]["event_type"] == "SYSTEM_EVENT"
            and e["payload"]["metrics"].get("reason_code") == "LINEAGE_PARENT_UNRESOLVED"
        ]

    @staticmethod
    def forwarded_ids(sent):
        return [eid(e) for e in sent if e["event"]["event_type"] != "SYSTEM_EVENT"]

    # The next four send no datagram. They show what main() builds, not
    # what the loop does with an event.

    def test_main_builds_the_state_with_the_default_cap(self):
        self.run_loop([])
        self.assertEqual(DEFAULT_CAP, self.state.event_index_max_entries)
        self.assertIn(f"event index: the {DEFAULT_CAP} most recent accepted events", self.stdout)

    def test_main_hands_the_flag_to_the_state_under_every_profile_and_encoding(self):
        for profile in ("L", "M", "H"):
            for encoding in ("json", "cbor", "compact", "auto"):
                for strict in ((), ("--strict-validation",)):
                    with self.subTest(profile=profile, encoding=encoding, strict=bool(strict)):
                        self.state = None
                        self.run_loop(
                            [], "--event-index-max-entries", "2", "--input-encoding", encoding, *strict,
                            profile=profile,
                        )
                        self.assertEqual(2, self.state.event_index_max_entries)
                        self.assertIn("event index: the 2 most recent accepted events", self.stdout)

    def test_main_hands_the_config_file_value_to_the_state(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "gateway.json"
            path.write_text(json.dumps({"event_index_max_entries": 7}), encoding="utf-8")
            self.run_loop([], "--config", str(path))
        self.assertEqual(7, self.state.event_index_max_entries)

    def test_a_bad_cap_stops_the_gateway_before_it_opens_a_socket(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "gateway.json"
            path.write_text(json.dumps({"event_index_max_entries": "16"}), encoding="utf-8")
            for flags in (
                ("--event-index-max-entries", "0"),
                ("--config", str(path)),
                ("--config", str(path), "--event-index-max-entries", "900"),
            ):
                with self.subTest(flags=flags[::2]):
                    argv = ["gateway.py", "--profile", "M", *flags]
                    with mock.patch("sys.argv", argv), \
                            mock.patch.object(gateway.socket, "socket", side_effect=AssertionError("no socket")), \
                            contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                        with self.assertRaises(SystemExit) as stopped:
                            gateway.main()
                    self.assertIn(
                        "event_index_max_entries must be an integer from 1 to", str(stopped.exception)
                    )

    # From here on, events go through the receive loop.

    def test_a_parent_just_inside_the_index_resolves(self):
        observations, cites_first, cites_third = self.chain()
        sent = self.run_loop(
            [*observations, cites_first, cites_third], "--event-index-max-entries", "3"
        )
        self.assertEqual([], self.unresolved(sent))
        self.assertEqual(
            [eid(e) for e in (*observations, cites_first, cites_third)], self.forwarded_ids(sent)
        )
        self.assertEqual(3, len(self.state.events))

    def test_a_parent_of_the_wrong_type_is_refused_while_it_is_in_the_index_and_not_after(self):
        def run(cap):
            status = time_status(ts=self.now - timedelta(seconds=20))
            fillers = [observation(profile="M", ts=self.now) for _ in range(2)]
            child = fusion(eid(status), profile="M", ts=self.now)
            return child, self.run_loop([status, *fillers, child], "--event-index-max-entries", cap)

        def diagnostics(sent, child):
            return [
                (e["payload"]["state"], e["payload"]["metrics"]["reason_code"])
                for e in sent
                if e["event"]["event_type"] == "SYSTEM_EVENT"
                and e["payload"]["metrics"].get("original_event_id") == eid(child)
            ]

        child, sent = run("3")
        self.assertEqual([("REJECTED", "LINEAGE_PARENT_TYPE_INVALID")], diagnostics(sent, child))
        self.assertNotIn(eid(child), self.forwarded_ids(sent))

        child, sent = run("2")
        self.assertEqual([("WARNING", "LINEAGE_PARENT_UNRESOLVED")], diagnostics(sent, child))
        self.assertIn(eid(child), self.forwarded_ids(sent))

    def test_long_ids_through_the_loop_leave_small_entries(self):
        acks = [
            task_ack(f"{index}" + "t" * LONG, f"{index}" + "e" * LONG, ts=self.now)
            for index in range(5)
        ]
        sent = self.run_loop(acks, "--event-index-max-entries", "8")
        self.assertEqual([eid(a) for a in acks], [eid(e) for e in sent])
        self.assertEqual(5, len(self.state.task_ack_keys))
        self.assertLess(reachable_bytes(self.state), 20000)

    def test_control_with_the_default_cap_both_parents_resolve(self):
        observations, cites_first, cites_third = self.chain()
        sent = self.run_loop([*observations, cites_first, cites_third])
        self.assertEqual([], self.unresolved(sent))
        self.assertEqual(
            [eid(e) for e in (*observations, cites_first, cites_third)], self.forwarded_ids(sent)
        )
        self.assertEqual(5, len(self.state.events))

    def test_a_parent_older_than_the_index_is_warned_and_the_event_is_forwarded(self):
        observations, cites_first, cites_third = self.chain()
        sent = self.run_loop(
            [*observations, cites_first, cites_third], "--event-index-max-entries", "2"
        )
        warnings = self.unresolved(sent)
        self.assertEqual(1, len(warnings), sent)
        metrics = warnings[0]["payload"]["metrics"]
        self.assertEqual("WARNING", warnings[0]["payload"]["state"])
        self.assertEqual(eid(cites_first), metrics["original_event_id"])
        self.assertEqual([eid(observations[0])], metrics["unresolved"])
        self.assertEqual("policy/lineage.yaml#unresolved_parent_mode", metrics["policy_ref"])
        self.assertEqual(
            [eid(e) for e in (*observations, cites_first, cites_third)], self.forwarded_ids(sent)
        )
        self.assertEqual(2, len(self.state.events))
        self.assertEqual("", self.stderr)

    def test_under_strict_validation_that_event_is_refused(self):
        observations, cites_first, cites_third = self.chain()
        sent = self.run_loop(
            [*observations, cites_first, cites_third],
            "--event-index-max-entries", "2", "--strict-validation",
        )
        refusals = self.unresolved(sent)
        self.assertEqual(1, len(refusals), sent)
        self.assertEqual("REJECTED", refusals[0]["payload"]["state"])
        self.assertEqual(eid(cites_first), refusals[0]["payload"]["metrics"]["original_event_id"])
        self.assertEqual(
            [eid(e) for e in (*observations, cites_third)], self.forwarded_ids(sent)
        )

    def test_the_running_gateway_holds_no_whole_event(self):
        observations, cites_first, cites_third = self.chain()
        self.run_loop([*observations, cites_first, cites_third], "--event-index-max-entries", "4")
        self.assertEqual(4, len(self.state.events))
        held = repr(self.state.events)
        self.assertNotIn("center_freq_hz", held)
        self.assertNotIn("track-1", held)
        self.assertEqual(
            {"event_type": "FUSION_EVENT", "event_subtype": "TRACK_FUSION"},
            self.state.get_event(eid(cites_third)),
        )

    def test_a_source_keeps_its_timing_status_past_the_index(self):
        status = time_status(ts=self.now - timedelta(seconds=20))
        observations = [observation(profile="M", ts=self.now) for _ in range(4)]
        sent = self.run_loop([status, *observations], "--event-index-max-entries", "2")
        self.assertEqual([eid(e) for e in observations], self.forwarded_ids(sent))
        self.assertIsNone(self.state.get_event(eid(status)))
        _key, latest = self.state.get_timing(observations[0])
        self.assertIsNotNone(latest)


if __name__ == "__main__":
    unittest.main()
