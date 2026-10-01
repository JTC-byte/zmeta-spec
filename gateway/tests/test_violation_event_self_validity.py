"""TV-09: build_violation_event() must never construct a diagnostic that its
own outgoing validation will refuse.

TASK_ACK's reason_code enum (schema/zmeta-event-1.0.schema.json TASK_ACK
block, mirrored in policy/semantics.yaml task_ack_allowed_reason_codes) is
deliberately task-limited: it does not include every code the gateway's
validators can raise against a COMMAND_EVENT. PROFILE_MISMATCH is one such
code. Before this fix, build_violation_event() routed any COMMAND_EVENT
violation into the TASK_ACK shape regardless of whether the reason_code was
legal there, so the diagnostic it built was itself schema-invalid. The
gateway's own outgoing self-check then caught that and replaced the
diagnostic with a generic SYSTEM_EVENT/SCHEMA_VIOLATION carrying
reason_code=SCHEMA_INVALID and original_event_id pointing at the
never-transmitted TASK_ACK's own freshly-minted id, not the id of the
COMMAND_EVENT that was actually refused. The operator could not correlate
the refusal to the command that caused it.

The fix makes build_violation_event() derive TASK_ACK legality itself from
the loaded policy's task_ack_allowed_reason_codes list, so no call site can
reopen the gap by forgetting to set force_schema_violation for a code it
does not already know about.

Every pin runs on three lanes: the locked v1.0 schema, the 1.1.0 schema,
and the dispatching union schema. The gateway stamps every diagnostic it
mints zmeta_version "1.0" (doctrine R1-11-01), and the outgoing self-check
used to validate that diagnostic against whichever schema the gateway was
launched with. On the 1.1.0 lane the lane schema refuses the "1.0" stamp on
its const, so the self-check replaced every refusal with a content-free
SCHEMA_INVALID and turned every warning on an accepted event into a
REJECTED diagnostic, both pointing at the id of a diagnostic that was never
sent. When these pins were built on the v1.0 schema alone, none of them
could see that. Contract 2.4 has consumers select the schema from the
event's own zmeta_version, so a diagnostic the gateway minted is now
checked against the schema its declared version selects. A forwarded
producer event is still checked against the inbound lane.
"""

import contextlib
import copy
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from zmeta_uuid import uuid7


ROOT = Path(__file__).resolve().parents[2]
VALIDATORS_PATH = ROOT / "gateway" / "src" / "validators.py"
spec_v = importlib.util.spec_from_file_location("zmeta_validators_tv09", VALIDATORS_PATH)
validators = importlib.util.module_from_spec(spec_v)
spec_v.loader.exec_module(validators)

GATEWAY_PATH = ROOT / "gateway" / "src" / "gateway.py"
spec_gw = importlib.util.spec_from_file_location("zmeta_gateway_tv09", GATEWAY_PATH)
gateway = importlib.util.module_from_spec(spec_gw)
spec_gw.loader.exec_module(gateway)

# (lane label, schema file the gateway is launched with, zmeta_version values
# that lane admits from a producer)
LANES = (
    ("v1.0 lane", "zmeta-event-1.0.schema.json", ("1.0",)),
    ("1.1.0 lane", "zmeta-event-1.1.0.schema.json", ("1.1.0",)),
    ("union", "zmeta-event.schema.json", ("1.0", "1.1.0")),
)
LANE_VALIDATORS = {
    label: validators.load_schema(ROOT / "schema" / schema_file)
    for label, schema_file, _versions in LANES
}
V1_1_0_LANE = "1.1.0 lane"


def _command_event(event_id=None, profile=None, zmeta_version="1.0"):
    event = {
        "zmeta_version": zmeta_version,
        "event": {
            "event_id": event_id or str(uuid7()),
            "event_type": "COMMAND_EVENT",
            "event_subtype": "GOTO",
            "ts": "2025-01-17T14:32:10Z",
        },
        "source": {
            "platform_id": "comms-node-1",
            "node_role": "GATEWAY",
            "producer": "sensorops",
        },
        "payload": {
            "task_id": "task-tv09-0001",
            "task_type": "GOTO",
            "target_geo": {"lat": 34.0102, "lon": -118.0102},
            "valid_for_ms": 600000,
            "requires_deconfliction": True,
        },
    }
    if profile is not None:
        event["profile"] = profile
    return event


class BuildViolationEventProfileMismatchTest(unittest.TestCase):
    """Pin 1 (unit-level), on every lane."""

    @classmethod
    def setUpClass(cls):
        cls.policy = validators.load_policy(ROOT / "policy")

    def test_profile_mismatch_command_diagnostic_is_self_valid_and_correlated(self):
        command_event_id = str(uuid7())
        command = _command_event(event_id=command_event_id)

        diagnostic = gateway.build_violation_event(
            "PROFILE_MISMATCH",
            original=command,
            details={"event_profile": "H", "profile": "L"},
            policy=self.policy,
        )

        # Must not be the TASK_ACK shape: PROFILE_MISMATCH is not in
        # task_ack_allowed_reason_codes, so a TASK_ACK carrying it would be
        # schema-invalid on its own.
        self.assertEqual(diagnostic["event"]["event_subtype"], "SCHEMA_VIOLATION")
        self.assertEqual(diagnostic["payload"]["system_type"], "SCHEMA_VIOLATION")
        self.assertEqual(diagnostic["payload"]["metrics"]["reason_code"], "PROFILE_MISMATCH")
        self.assertEqual(
            diagnostic["payload"]["metrics"]["original_event_id"], command_event_id
        )

        # Must pass the gateway's own outgoing self-check, the exact check
        # that used to catch and replace this diagnostic, on every lane.
        for lane, validator in LANE_VALIDATORS.items():
            with self.subTest(lane=lane):
                violations = gateway.validate_outgoing_event(diagnostic, validator, self.policy, "L")
                self.assertEqual([], violations)


class ProcessMessageProfileMismatchPipelineTest(unittest.TestCase):
    """Pin 2 (pipeline-level), via gateway.process_message(), on every lane
    and for every producer version that lane admits."""

    @classmethod
    def setUpClass(cls):
        cls.policy = validators.load_policy(ROOT / "policy")

    def test_profile_mismatch_command_yields_one_correlated_schema_violation(self):
        for lane, _schema_file, versions in LANES:
            validator = LANE_VALIDATORS[lane]
            for version in versions:
                with self.subTest(lane=lane, zmeta_version=version):
                    self._check_one(validator, version)

    def _check_one(self, validator, version):
        command_event_id = str(uuid7())
        # The event declares profile H; the gateway is run at profile L, so
        # validate_profile raises PROFILE_MISMATCH (severity: fail).
        command = _command_event(event_id=command_event_id, profile="H", zmeta_version=version)
        raw = json.dumps(command).encode("utf-8")

        outgoing = gateway.process_message(
            raw, validator, self.policy, "L", gateway.TaskDedupeCache(), "json"
        )

        # Exactly one diagnostic reaches the wire for the one rejected input.
        self.assertEqual(1, len(outgoing))
        diagnostic = outgoing[0]

        self.assertEqual(diagnostic["event"]["event_type"], "SYSTEM_EVENT")
        self.assertEqual(diagnostic["event"]["event_subtype"], "SCHEMA_VIOLATION")
        self.assertEqual(diagnostic["payload"]["metrics"]["reason_code"], "PROFILE_MISMATCH")
        # The true refused event, not a never-transmitted internal TASK_ACK.
        self.assertEqual(
            diagnostic["payload"]["metrics"]["original_event_id"], command_event_id
        )

        # What actually reaches the wire must itself be schema-valid, checked
        # by the same lane validator the gateway was launched with.
        violations = gateway.validate_outgoing_event(diagnostic, validator, self.policy, "L")
        self.assertEqual([], violations)


class TaskAckReasonCodeSweepTest(unittest.TestCase):
    """Pin 3: closes the class, not just the PROFILE_MISMATCH instance.

    For every reason code the gateway's own policy knows about (the full
    policy/violation-codes.yaml list, loaded, never hardcoded here), build a
    diagnostic against a COMMAND_EVENT original and confirm the result
    passes the gateway's own outgoing self-check -- whether that code is
    legal for TASK_ACK (and rides the TASK_ACK shape) or not (and rides the
    SCHEMA_VIOLATION shape instead).
    """

    # Matches test_reason_codes.py: these two codes are v1.1.0-only additions
    # to schema_violation_allowed_reason_codes and are documented there
    # (test_v1_1_only_diagnostic_codes_do_not_leak_into_v1_0) as invalid
    # under the v1.0 schema in *either* shape, TASK_ACK or SCHEMA_VIOLATION.
    # build_violation_event() always stamps zmeta_version "1.0", so sweeping
    # these two here would fail regardless of TV-09's fix and is not this
    # defect's class.
    V1_1_ONLY_SCHEMA_VIOLATION_CODES = {
        "SENSOR_STATUS_STATE_MISMATCH",
        "PLATFORM_STATUS_POWER_MISSING",
    }

    @classmethod
    def setUpClass(cls):
        cls.policy = validators.load_policy(ROOT / "policy")

    def test_every_policy_reason_code_produces_a_self_valid_command_diagnostic(self):
        command = _command_event()
        codes = [
            item["code"]
            for item in self.policy["violation_codes"]
            if isinstance(item, dict) and "code" in item
            and item["code"] not in self.V1_1_ONLY_SCHEMA_VIOLATION_CODES
        ]
        self.assertTrue(codes, "policy/violation-codes.yaml yielded no codes to sweep")

        failures = []
        for lane, validator in LANE_VALIDATORS.items():
            for code in codes:
                diagnostic = gateway.build_violation_event(
                    code, original=command, policy=self.policy
                )
                violations = gateway.validate_outgoing_event(
                    diagnostic, validator, self.policy, "L"
                )
                if violations:
                    failures.append((lane, code, diagnostic["event"]["event_subtype"], violations))

        self.assertEqual(
            [], failures,
            f"{len(failures)} lane and reason code pair(s) produced a self-invalid diagnostic: {failures}",
        )


def _track_event(event_id, geo, zmeta_version="1.1.0"):
    """A TRACK_STATE event. With geo at 0/0 it is accepted with a
    GEO_ZERO_FILL_SUSPECTED warning; on the 1.1.0 schema, a geo without
    alt_m is refused."""
    return {
        "zmeta_version": zmeta_version,
        "event": {
            "event_id": event_id,
            "event_type": "STATE_EVENT",
            "event_subtype": "TRACK_STATE",
            "ts": "2026-07-16T10:00:00Z",
        },
        "source": {
            "platform_id": "fusion-node-01",
            "node_role": "GATEWAY",
            "producer": "fusion-engine",
        },
        "profile": "H",
        "payload": {
            "track_id": "TRACK-TV09-LANE-001",
            "geo": geo,
            "valid_for_ms": 1000,
            "timing_quality": {
                "time_source": "GPS_PPS",
                "sync_state": "LOCKED",
                "est_error_ms": 1,
                "last_sync_ts": "2026-07-16T09:59:59Z",
            },
        },
        "confidence": 0.7,
        "lineage": {"based_on": ["019c2b5c-c053-70e1-b6aa-34bf14c8a402"]},
    }


class EveryBuilderOnEveryLaneTest(unittest.TestCase):
    """Pin 4: all three diagnostic builders, not only build_violation_event,
    produce a diagnostic that passes the outgoing self-check on every lane,
    whichever version the event it describes declared."""

    @classmethod
    def setUpClass(cls):
        cls.policy = validators.load_policy(ROOT / "policy")

    def _diagnostics(self, version):
        command = _command_event(zmeta_version=version)
        track = _track_event(str(uuid7()), {"lat": 0.0, "lon": 0.0, "alt_m": 100.0}, version)
        return {
            "violation": gateway.build_violation_event(
                "PROFILE_MISMATCH", original=command, policy=self.policy
            ),
            "warning": gateway.build_warning_event(
                "GEO_ZERO_FILL_SUSPECTED", original=track, policy=self.policy
            ),
            "duplicate_ack": gateway.build_duplicate_ack(command),
        }

    def test_every_builder_is_marked_and_self_valid_on_every_lane(self):
        for version in ("1.0", "1.1.0"):
            for name, diagnostic in self._diagnostics(version).items():
                self.assertIsInstance(diagnostic, gateway.GatewayDiagnostic, name)
                self.assertEqual("1.0", diagnostic["zmeta_version"], name)
                for lane, validator in LANE_VALIDATORS.items():
                    with self.subTest(builder=name, original_version=version, lane=lane):
                        violations = gateway.validate_outgoing_event(
                            diagnostic, validator, self.policy, "L"
                        )
                        self.assertEqual([], violations)


class ForwardedEventsKeepTheLaneTest(unittest.TestCase):
    """Pin 5: only a diagnostic the gateway minted leaves the inbound lane.

    The self-check picks the version-selected schema from the type the
    builders return, never from what an event says about itself.
    test_the_mark_not_the_content_selects_the_schema is the pin that binds
    that rule. The forged-wire test only shows that an imitation arriving on
    the wire is an ordinary producer event: refused inbound on the 1.1.0
    lane, and forwarded unmarked on the union lane."""

    @classmethod
    def setUpClass(cls):
        cls.policy = validators.load_policy(ROOT / "policy")
        cls.lane = LANE_VALIDATORS[V1_1_0_LANE]

    def _minted(self):
        return gateway.build_violation_event(
            "PROFILE_MISMATCH", original=_command_event(zmeta_version="1.1.0"), policy=self.policy
        )

    def test_the_mark_not_the_content_selects_the_schema(self):
        minted = self._minted()
        plain = json.loads(json.dumps(minted))
        self.assertIs(type(plain), dict)
        self.assertEqual(minted, plain)

        self.assertEqual([], gateway.validate_outgoing_event(minted, self.lane, self.policy, "L"))
        refused = gateway.validate_outgoing_event(plain, self.lane, self.policy, "L")
        self.assertEqual(["SCHEMA_INVALID"], [violation["code"] for violation in refused])

    def test_a_diagnostic_forged_on_the_wire_is_an_ordinary_producer_event(self):
        forged = self._minted()
        raw = json.dumps(forged).encode("utf-8")
        self.assertIs(type(gateway._decode_message(raw, "json")), dict)

        # The 1.1.0 lane refuses it inbound, on its v1.0 stamp.
        outgoing = gateway.process_message(
            raw, self.lane, self.policy, "L", gateway.TaskDedupeCache(), "json"
        )
        self.assertEqual(1, len(outgoing))
        refusal = outgoing[0]
        self.assertEqual("REJECTED", refusal["payload"]["state"])
        self.assertEqual("SCHEMA_INVALID", refusal["payload"]["metrics"]["reason_code"])
        self.assertEqual(forged["event"]["event_id"], refusal["payload"]["metrics"]["original_event_id"])

        # The union lane admits it, and forwards it as a plain dict, so its
        # outgoing self-check is the lane's.
        outgoing = gateway.process_message(
            raw, LANE_VALIDATORS["union"], self.policy, "L", gateway.TaskDedupeCache(), "json"
        )
        self.assertEqual(1, len(outgoing))
        forwarded = outgoing[0]
        self.assertEqual(forged["event"]["event_id"], forwarded["event"]["event_id"])
        self.assertIs(type(forwarded), dict)

    def test_the_mark_does_not_change_the_bytes_on_any_output_encoding(self):
        minted = self._minted()
        plain = copy.deepcopy(dict(minted))
        self.assertIs(type(plain), dict)
        for encoding in sorted(gateway.OUTPUT_ENCODING_CHOICES):
            with self.subTest(encoding=encoding):
                try:
                    marked_bytes = gateway._encode_message(minted, encoding)
                except SystemExit as exc:
                    self.skipTest(f"{encoding} encoder unavailable: {exc}")
                self.assertEqual(marked_bytes, gateway._encode_message(plain, encoding))


class _ListenerClosed(OSError):
    """Raised by the fake listener once its datagrams are spent. It is not a
    socket.timeout, so main() lets it propagate and the test ends there."""


class _FakeNetwork:
    """Stands in for socket.socket: delivers queued datagrams to the
    listener and records every datagram the gateway sends."""

    def __init__(self, datagrams):
        self.inbox = list(datagrams)
        self.sent = []

    def socket(self, *args, **kwargs):
        return _FakeSocket(self)


class _FakeSocket:
    def __init__(self, network):
        self.network = network

    def bind(self, addr):
        pass

    def settimeout(self, value):
        pass

    def recvfrom(self, size):
        if not self.network.inbox:
            raise _ListenerClosed("fake listener closed")
        return self.network.inbox.pop(0), ("127.0.0.1", 40000)

    def sendto(self, payload, addr):
        self.network.sent.append((payload, addr))


class MainLoopLaneDiagnosticsTest(unittest.TestCase):
    """Pin 6 (end to end), through main() on the lanes that admit 1.1.0
    producers. This is the path where the defect reached the wire: the
    self-check in the receive loop refused the gateway's own v1.0 diagnostic
    and replaced it."""

    def _run_main(self, schema_file, datagrams):
        network = _FakeNetwork(datagrams)
        argv = [
            "gateway.py", "--profile", "H",
            "--schema-path", str(ROOT / "schema" / schema_file),
            "--no-metrics", "--no-emit-cot",
        ]
        with mock.patch("sys.argv", argv), \
                mock.patch.object(gateway.socket, "socket", network.socket), \
                contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(_ListenerClosed):
                gateway.main()
        return [json.loads(payload) for payload, _addr in network.sent]

    def test_warnings_and_refusals_reach_the_wire_intact(self):
        for lane, schema_file, versions in LANES:
            if "1.1.0" not in versions:
                continue
            with self.subTest(lane=lane):
                accepted_id, refused_id = str(uuid7()), str(uuid7())
                accepted = _track_event(accepted_id, {"lat": 0.0, "lon": 0.0, "alt_m": 100.0})
                refused = _track_event(refused_id, {"lat": 34.0, "lon": -118.0})
                wire = self._run_main(
                    schema_file,
                    [json.dumps(accepted).encode("utf-8"), json.dumps(refused).encode("utf-8")],
                )

                # The accepted track, its warnings, then the one refusal. The
                # track draws LINEAGE_PARENT_UNRESOLVED beside the zero-fill
                # warning, because its based_on parent was never seen.
                self.assertGreaterEqual(len(wire), 3, wire)
                track, warnings, refusal = wire[0], wire[1:-1], wire[-1]

                self.assertEqual(accepted_id, track["event"]["event_id"])

                # An accepted event's warnings stay warnings about that event.
                for warning in warnings:
                    self.assertEqual("WARNING", warning["payload"]["state"])
                    self.assertEqual(accepted_id, warning["payload"]["metrics"]["original_event_id"])
                self.assertIn(
                    "GEO_ZERO_FILL_SUSPECTED",
                    [warning["payload"]["metrics"]["reason_code"] for warning in warnings],
                )

                # A refusal names the refused event and where it failed.
                self.assertEqual("REJECTED", refusal["payload"]["state"])
                self.assertEqual("SCHEMA_INVALID", refusal["payload"]["metrics"]["reason_code"])
                self.assertEqual(refused_id, refusal["payload"]["metrics"]["original_event_id"])
                if lane == V1_1_0_LANE:
                    # The union schema's oneOf reports a refusal as the whole
                    # event with an empty path, so the path is pinned only
                    # where the lane schema can name it.
                    self.assertEqual("payload/geo", refusal["payload"]["metrics"].get("path"))

                for diagnostic in (*warnings, refusal):
                    self.assertEqual("1.0", diagnostic["zmeta_version"])

    def test_main_refuses_to_start_without_the_diagnostics_schema(self):
        """Without the schema its diagnostics declare, the self-check would
        fall back to the lane and the defect would return without a word, so
        main() exits before it opens a socket. The socket is patched to
        raise, so a main() that skipped the check fails here at the socket
        instead of binding a real port."""
        with tempfile.TemporaryDirectory() as empty_root:
            argv = ["gateway.py", "--profile", "H", "--no-metrics", "--no-emit-cot"]
            with mock.patch("sys.argv", argv), \
                    mock.patch.object(gateway, "ROOT_DIR", Path(empty_root)), \
                    mock.patch.object(gateway.socket, "socket", side_effect=RuntimeError("reached the socket")), \
                    contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit) as caught:
                    gateway.main()
        self.assertIn("zmeta_version '1.0'", str(caught.exception))


class CallSitePolicyCoverage(unittest.TestCase):
    """The attack pass on this fix found the class closed at the call sites
    inside process_message() and open at the main-loop outgoing self-check
    rebuild, which reproduced the pre-fix defect byte-for-byte because
    build_violation_event's policy parameter defaults to None and None means
    every reason code is presumed TASK_ACK-legal. A forgotten keyword is a
    source-shape fact, so this pin enumerates the call sites from the
    source, the same enumerated-sites pattern _risk_trigger_matches uses:
    every build_violation_event() call in gateway.py must pass policy= or
    force_schema_violation=True."""

    def test_every_call_site_passes_policy_or_forces_schema_violation(self):
        import ast

        tree = ast.parse(GATEWAY_PATH.read_text(encoding="utf-8"))
        offenders = []
        total = 0
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", None)
            if name != "build_violation_event":
                continue
            total += 1
            keywords = {kw.arg for kw in node.keywords}
            if "policy" not in keywords and "force_schema_violation" not in keywords:
                offenders.append(node.lineno)
        self.assertGreaterEqual(
            total, 12,
            "expected at least the 12 known build_violation_event call sites; "
            "if sites were removed, re-derive this floor from the source",
        )
        self.assertEqual(
            [], offenders,
            "build_violation_event call sites missing policy= or "
            f"force_schema_violation=True at gateway.py lines: {offenders}",
        )


if __name__ == "__main__":
    unittest.main()
