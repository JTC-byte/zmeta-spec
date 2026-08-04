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
"""

import importlib.util
import json
import unittest
from pathlib import Path

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


def _command_event(event_id=None, profile=None):
    event = {
        "zmeta_version": "1.0",
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
    """Pin 1 (unit-level)."""

    @classmethod
    def setUpClass(cls):
        cls.validator = validators.load_schema(ROOT / "schema" / "zmeta-event-1.0.schema.json")
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
        # that used to catch and replace this diagnostic.
        violations = gateway.validate_outgoing_event(diagnostic, self.validator, self.policy, "L")
        self.assertEqual([], violations)


class ProcessMessageProfileMismatchPipelineTest(unittest.TestCase):
    """Pin 2 (pipeline-level), via gateway.process_message()."""

    @classmethod
    def setUpClass(cls):
        cls.validator = validators.load_schema(ROOT / "schema" / "zmeta-event-1.0.schema.json")
        cls.policy = validators.load_policy(ROOT / "policy")

    def test_profile_mismatch_command_yields_one_correlated_schema_violation(self):
        command_event_id = str(uuid7())
        # The event declares profile H; the gateway is run at profile L, so
        # validate_profile raises PROFILE_MISMATCH (severity: fail).
        command = _command_event(event_id=command_event_id, profile="H")
        raw = json.dumps(command).encode("utf-8")

        outgoing = gateway.process_message(
            raw, self.validator, self.policy, "L", gateway.TaskDedupeCache(), "json"
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

        # What actually reaches the wire must itself be schema-valid.
        violations = gateway.validate_outgoing_event(diagnostic, self.validator, self.policy, "L")
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
        cls.validator = validators.load_schema(ROOT / "schema" / "zmeta-event-1.0.schema.json")
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
        for code in codes:
            diagnostic = gateway.build_violation_event(
                code, original=command, policy=self.policy
            )
            violations = gateway.validate_outgoing_event(
                diagnostic, self.validator, self.policy, "L"
            )
            if violations:
                failures.append((code, diagnostic["event"]["event_subtype"], violations))

        self.assertEqual(
            [], failures,
            f"{len(failures)} reason code(s) produced a self-invalid diagnostic: {failures}",
        )


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
