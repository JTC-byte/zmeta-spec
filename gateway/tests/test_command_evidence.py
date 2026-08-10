"""Command-evidence lineage check (UxS command loop, GCS-originated tasking).

A COMMAND_EVENT may cite the inference/fusion evidence that motivated it via
the EXISTING lineage vocabulary (lineage.based_on); the gateway checks those
citations against what it saw upstream (policy/command-evidence.yaml):

- cited parent never seen or evicted -> COMMAND_EVIDENCE_UNRESOLVED per
  mode (minted 2026-08-09; rode LINEAGE_PARENT_UNRESOLVED before the
  R1-11-01 Class B batch);
- cited parent whose event_type cannot motivate a command
  -> LINEAGE_PARENT_TYPE_INVALID per mode (honest reuse, kept);
- cited parent whose risk_adjudication carries a use limit prohibiting
  command basis (COMMAND_BASIS / AUTONOMY_TASKING, the S1-15
  blocked-from-command-basis posture) -> COMMAND_EVIDENCE_PROHIBITED per
  mode (minted 2026-08-09; rode LINEAGE_MISMATCH before the batch).

A bare command with NO cited parents stays legal by default (a human
operator's direct tasking has no fused parent); the require_evidence knob is
the deployment-side gate for automation, and its refusal keeps
LINEAGE_MISMATCH: a policy-strictness refusal, not an evidence
adjudication. On the v1.0 wire the minted codes ride their documented
legacy fallbacks with metrics.diagnostic_code carrying the specific
condition; the gateway-layer tests below pin exactly that.
"""

import copy
import importlib.util
import json
import unittest
from pathlib import Path

from zmeta_uuid import uuid7


ROOT = Path(__file__).resolve().parents[2]
VALIDATORS_PATH = ROOT / "gateway" / "src" / "validators.py"
spec = importlib.util.spec_from_file_location("zmeta_validators", VALIDATORS_PATH)
validators = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validators)

GATEWAY_PATH = ROOT / "gateway" / "src" / "gateway.py"
spec_gw = importlib.util.spec_from_file_location("zmeta_gateway", GATEWAY_PATH)
gateway = importlib.util.module_from_spec(spec_gw)
spec_gw.loader.exec_module(gateway)


TIMING_QUALITY = {
    "time_source": "GPS_PPS",
    "sync_state": "LOCKED",
    "est_error_ms": 1,
    "last_sync_ts": "2025-01-17T14:31:50Z",
}

COMMAND_PROHIBITING_RECORD = {
    # The record shape the gateway itself stamps on soft-accepted events
    # (S1-15): risk labels plus allowed/prohibited uses.
    "risk_dimension": "external_promotion",
    "reason_code": "PRODUCER_NOT_ALLOWED",
    "policy_mode": "warn",
    "policy_decision": "WARN_ACCEPT",
    "policy_ref": "policy/producer-authority.yaml#external_state_promotion",
    "allowed_uses": ["DISPLAY", "LOCAL_AWARENESS", "ALERTING"],
    "prohibited_uses": ["COMMAND_BASIS", "AUTONOMY_TASKING"],
}


def source(producer="sensorops", role="GATEWAY", platform_id="comms-node-1"):
    return {"platform_id": platform_id, "node_role": role, "producer": producer}


def observation(event_id=None):
    return {
        "zmeta_version": "1.0",
        "event": {
            "event_id": event_id or str(uuid7()),
            "event_type": "OBSERVATION_EVENT",
            "event_subtype": "RF",
            "ts": "2025-01-17T14:30:00Z",
        },
        "source": source("rf-sensor", "EDGE", "sensor-node-01"),
        "profile": "H",
        "payload": {
            "modality": "RF",
            "features": {
                "center_freq_hz": 2450000000,
                "bandwidth_hz": 20000000,
                "power_dbm": -35.2,
            },
        },
    }


def inference(parent_id=None, event_id=None):
    parent_id = parent_id or str(uuid7())
    return {
        "zmeta_version": "1.0",
        "event": {
            "event_id": event_id or str(uuid7()),
            "event_type": "INFERENCE_EVENT",
            "event_subtype": "CLASSIFICATION",
            "ts": "2025-01-17T14:30:01Z",
        },
        "source": source("torch"),
        "profile": "H",
        "payload": {
            "inference_type": "CLASSIFICATION",
            "claim": {"label": "drone"},
            "model": {"name": "rf-classifier", "version": "1.0.0"},
        },
        "confidence": 0.82,
        "lineage": {"based_on": [parent_id]},
    }


def track_state(event_id=None, risk_records=None):
    event = {
        "zmeta_version": "1.0",
        "event": {
            "event_id": event_id or str(uuid7()),
            "event_type": "STATE_EVENT",
            "event_subtype": "TRACK_STATE",
            "ts": "2025-01-17T14:30:02Z",
        },
        "source": source("torch"),
        "profile": "H",
        "payload": {
            "track_id": "track-1",
            "geo": {"lat": 34.0, "lon": -118.0, "alt_m": 100.0},
            "valid_for_ms": 60000,
        },
        "confidence": 0.7,
        "lineage": {"based_on": [str(uuid7())]},
    }
    if risk_records is not None:
        event["payload"]["extensions"] = {
            "risk_adjudication": copy.deepcopy(risk_records)
        }
    return event


def command(parent_ids=None, task_id=None, task_type="GOTO", profile="L"):
    event = {
        "zmeta_version": "1.0",
        "event": {
            "event_id": str(uuid7()),
            "event_type": "COMMAND_EVENT",
            "event_subtype": task_type,
            "ts": "2025-01-17T14:32:10Z",
        },
        "source": source(),
        "profile": profile,
        "payload": {
            "task_id": task_id or f"task-{uuid7()}",
            "task_type": task_type,
            "target_geo": {"lat": 34.0101, "lon": -118.0101},
            "valid_for_ms": 600000,
            "requires_deconfliction": True,
            "timing_quality": dict(TIMING_QUALITY),
        },
    }
    if parent_ids is not None:
        event["lineage"] = {"based_on": list(parent_ids)}
    return event


def recorded_state(*parents, cap=None):
    state = (
        validators.ValidationState()
        if cap is None
        else validators.ValidationState(command_evidence_max_entries=cap)
    )
    for parent in parents:
        state.record(parent)
    return state


class CommandEvidenceValidatorTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = validators.load_policy(ROOT / "policy")
        cls.severity_map = cls.policy["violation_severities"]
        cls.ce_policy = cls.policy["command_evidence"]
        cls.schema = validators.load_schema(ROOT / "schema" / "zmeta-event-1.0.schema.json")

    def check(self, event, state, policy=None):
        return validators.validate_command_evidence(
            event,
            self.ce_policy if policy is None else policy,
            state=state,
            profile=None,
            severity_map=self.severity_map,
        )

    def test_shipped_policy_defaults_are_permissive_for_bare_commands(self):
        # load_policy must pick the file up, and the reference defaults must
        # not gate direct operator tasking.
        self.assertIsInstance(self.ce_policy, dict)
        self.assertTrue(self.ce_policy)
        self.assertIsNot(True, self.ce_policy.get("require_evidence"))

    def test_bare_command_is_legal_by_default(self):
        ok, violations = self.check(command(), recorded_state())
        self.assertTrue(ok, violations)
        self.assertEqual([], violations)

    def test_permitted_citation_passes_and_fabricates_nothing(self):
        parent = inference()
        state = recorded_state(parent)
        cmd = command([parent["event"]["event_id"]])
        # Anti-vacuity: a command citing lineage is schema-legal.
        self.assertEqual([], list(self.schema.iter_errors(cmd)))
        untouched = copy.deepcopy(cmd)

        ok, violations = self.check(cmd, state)

        self.assertTrue(ok, violations)
        self.assertEqual([], violations)
        self.assertEqual(untouched, cmd, "a clean pass must not mutate the command")

    def test_cited_parent_unknown_warns_by_default(self):
        missing = str(uuid7())
        cmd = command([missing])

        ok, violations = self.check(cmd, recorded_state())

        self.assertTrue(ok, violations)
        self.assertEqual(1, len(violations))
        violation = violations[0]
        self.assertEqual("COMMAND_EVIDENCE_UNRESOLVED", violation["code"])
        self.assertEqual("warn", violation["severity"])
        details = violation["details"]
        self.assertEqual([missing], details["unresolved"])
        self.assertEqual("lineage", details["risk_dimension"])
        self.assertEqual("WARN_ACCEPT", details["policy_decision"])
        self.assertEqual(
            "policy/command-evidence.yaml#unresolved_parent_mode",
            details["policy_ref"],
        )
        self.assertEqual(cmd["payload"]["task_id"], details["task_id"])
        # The soft acceptance travels with its use limits: the shaky command
        # must be filterable out of autonomy execution.
        self.assertIn("AUTONOMY_TASKING", details["prohibited_uses"])

    def test_cited_parent_unknown_rejects_when_mode_reject(self):
        policy = copy.deepcopy(self.ce_policy)
        policy["unresolved_parent_mode"] = "reject"
        cmd = command([str(uuid7())])

        ok, violations = self.check(cmd, recorded_state(), policy=policy)

        self.assertFalse(ok)
        self.assertEqual("COMMAND_EVIDENCE_UNRESOLVED", violations[0]["code"])
        self.assertEqual("fail", violations[0]["severity"])
        self.assertEqual("REJECTED", violations[0]["details"]["policy_decision"])

    def test_cited_parent_type_cannot_motivate_a_command(self):
        parent = observation()
        state = recorded_state(parent)
        cmd = command([parent["event"]["event_id"]])

        ok, violations = self.check(cmd, state)

        self.assertFalse(ok)
        violation = violations[0]
        self.assertEqual("LINEAGE_PARENT_TYPE_INVALID", violation["code"])
        self.assertEqual("fail", violation["severity"])
        details = violation["details"]
        self.assertEqual(
            [{"event_id": parent["event"]["event_id"], "event_type": "OBSERVATION_EVENT"}],
            details["invalid_parents"],
        )
        self.assertIn("INFERENCE_EVENT", details["motivating_parent_event_types"])
        self.assertEqual(
            "policy/command-evidence.yaml#parent_type_mismatch_mode",
            details["policy_ref"],
        )

    def test_prohibited_use_parent_is_refused_by_default(self):
        parent = track_state(risk_records=[COMMAND_PROHIBITING_RECORD])
        state = recorded_state(parent)
        cmd = command([parent["event"]["event_id"]])

        ok, violations = self.check(cmd, state)

        self.assertFalse(ok)
        violation = violations[0]
        self.assertEqual("COMMAND_EVIDENCE_PROHIBITED", violation["code"])
        self.assertEqual("fail", violation["severity"])
        details = violation["details"]
        self.assertEqual("REJECTED", details["policy_decision"])
        self.assertEqual(
            "policy/command-evidence.yaml#prohibited_use_mode", details["policy_ref"]
        )
        (entry,) = details["prohibited_parents"]
        self.assertEqual(parent["event"]["event_id"], entry["event_id"])
        self.assertEqual(
            ["AUTONOMY_TASKING", "COMMAND_BASIS"], entry["prohibited_command_uses"]
        )
        # The refusal names the upstream adjudication it is honoring.
        self.assertEqual(["PRODUCER_NOT_ALLOWED"], entry["risk_reason_codes"])

    def test_parent_with_only_benign_labels_is_not_refused(self):
        benign = dict(COMMAND_PROHIBITING_RECORD)
        benign["prohibited_uses"] = ["COALITION_EXPORT"]
        parent = track_state(risk_records=[benign])
        state = recorded_state(parent)

        ok, violations = self.check(command([parent["event"]["event_id"]]), state)

        self.assertTrue(ok, violations)
        self.assertEqual([], violations)

    def test_prohibited_use_warn_mode_accepts_with_loud_label(self):
        policy = copy.deepcopy(self.ce_policy)
        policy["prohibited_use_mode"] = "warn"
        parent = track_state(risk_records=[COMMAND_PROHIBITING_RECORD])
        state = recorded_state(parent)

        ok, violations = self.check(command([parent["event"]["event_id"]]), state, policy=policy)

        self.assertTrue(ok)
        self.assertEqual("COMMAND_EVIDENCE_PROHIBITED", violations[0]["code"])
        self.assertEqual("warn", violations[0]["severity"])
        self.assertEqual("WARN_ACCEPT", violations[0]["details"]["policy_decision"])
        self.assertIn("AUTONOMY_TASKING", violations[0]["details"]["prohibited_uses"])

    def test_prohibited_use_degrade_mode_stamps_the_command(self):
        policy = copy.deepcopy(self.ce_policy)
        policy["prohibited_use_mode"] = "degrade"
        parent = track_state(risk_records=[COMMAND_PROHIBITING_RECORD])
        state = recorded_state(parent)
        cmd = command([parent["event"]["event_id"]])

        ok, violations = self.check(cmd, state, policy=policy)

        self.assertTrue(ok)
        self.assertEqual("warn", violations[0]["severity"])
        self.assertEqual("degrade", violations[0]["details"]["action"])
        self.assertEqual(
            "DEGRADED_ACCEPT", violations[0]["details"]["policy_decision"]
        )

        changed = validators.apply_command_evidence_policy_action(cmd, violations, policy)

        self.assertTrue(changed)
        records = cmd["payload"]["extensions"]["risk_adjudication"]
        self.assertEqual(1, len(records))
        record = records[0]
        self.assertEqual("lineage", record["risk_dimension"])
        self.assertEqual("COMMAND_EVIDENCE_PROHIBITED", record["reason_code"])
        self.assertEqual("DEGRADED_ACCEPT", record["policy_decision"])
        self.assertIn("AUTONOMY_TASKING", record["prohibited_uses"])
        # The stamped command is still a valid instance of the contract.
        self.assertEqual([], list(self.schema.iter_errors(cmd)))

    def test_apply_does_not_stamp_on_warn_or_reject(self):
        parent = track_state(risk_records=[COMMAND_PROHIBITING_RECORD])
        state = recorded_state(parent)
        for mode in ("warn", "reject"):
            with self.subTest(mode=mode):
                policy = copy.deepcopy(self.ce_policy)
                policy["prohibited_use_mode"] = mode
                cmd = command([parent["event"]["event_id"]])
                _ok, violations = self.check(cmd, state, policy=policy)
                changed = validators.apply_command_evidence_policy_action(
                    cmd, violations, policy
                )
                self.assertFalse(changed)
                self.assertNotIn("extensions", cmd["payload"])

    def test_strict_knob_refuses_bare_commands_only_when_enabled(self):
        policy = copy.deepcopy(self.ce_policy)
        policy["require_evidence"] = True

        ok, violations = self.check(command(), recorded_state(), policy=policy)

        self.assertFalse(ok)
        self.assertEqual("LINEAGE_MISMATCH", violations[0]["code"])
        self.assertEqual(
            "policy/command-evidence.yaml#require_evidence_mode",
            violations[0]["details"]["policy_ref"],
        )

        # A command that DOES cite permitted evidence still passes.
        parent = inference()
        state = recorded_state(parent)
        ok, violations = self.check(
            command([parent["event"]["event_id"]]), state, policy=policy
        )
        self.assertTrue(ok, violations)
        self.assertEqual([], violations)

    def test_strict_knob_scopes_by_task_type(self):
        policy = copy.deepcopy(self.ce_policy)
        policy["require_evidence"] = True
        policy["require_evidence_task_types"] = ["ORBIT"]

        ok, violations = self.check(command(task_type="GOTO"), recorded_state(), policy=policy)
        self.assertTrue(ok, violations)
        self.assertEqual([], violations)

        ok, violations = self.check(command(task_type="ORBIT"), recorded_state(), policy=policy)
        self.assertFalse(ok)
        self.assertEqual("LINEAGE_MISMATCH", violations[0]["code"])

    def test_non_command_events_are_out_of_scope(self):
        parent = observation()
        state = recorded_state(parent)
        inf = inference(parent_id=parent["event"]["event_id"])

        ok, violations = self.check(inf, state)

        self.assertTrue(ok, violations)
        self.assertEqual([], violations)

    def test_evicted_parent_resolves_as_unresolved(self):
        first, second, third = inference(), inference(), inference()
        state = recorded_state(first, second, third, cap=2)

        self.assertEqual(2, len(state.command_evidence))
        self.assertNotIn(first["event"]["event_id"], state.command_evidence)

        ok, violations = self.check(command([first["event"]["event_id"]]), state)
        self.assertTrue(ok)
        self.assertEqual("COMMAND_EVIDENCE_UNRESOLVED", violations[0]["code"])

        # The survivors still resolve cleanly.
        ok, violations = self.check(command([third["event"]["event_id"]]), state)
        self.assertTrue(ok, violations)
        self.assertEqual([], violations)

    def test_invalid_index_cap_falls_back_to_the_default(self):
        for bad in (0, -5, "nope", None):
            with self.subTest(cap=repr(bad)):
                state = validators.ValidationState(command_evidence_max_entries=bad)
                self.assertEqual(
                    validators.DEFAULT_COMMAND_EVIDENCE_INDEX_MAX_ENTRIES,
                    state.command_evidence_max_entries,
                )

    def test_mangled_policy_block_reports_and_still_checks(self):
        parent = track_state(risk_records=[COMMAND_PROHIBITING_RECORD])
        state = recorded_state(parent)
        cmd = command([parent["event"]["event_id"]])

        ok, violations = validators.validate_command_evidence(
            cmd, "oops", state=state, severity_map=self.severity_map
        )

        self.assertFalse(ok, "a destroyed policy block must not disable the check")
        self.assertEqual("COMMAND_EVIDENCE_PROHIBITED", violations[0]["code"])
        self.assertIn("policy_error", violations[0]["details"])

    def test_explicit_disable_is_honoured(self):
        parent = track_state(risk_records=[COMMAND_PROHIBITING_RECORD])
        state = recorded_state(parent)
        cmd = command([parent["event"]["event_id"]])

        ok, violations = self.check(cmd, state, policy={"enabled": False})

        self.assertTrue(ok)
        self.assertEqual([], violations)


class CommandEvidencePolicyLintTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = validators.load_policy(ROOT / "policy")

    def test_shipped_policy_is_lint_clean(self):
        self.assertEqual([], validators.lint_policy_risk_modes(self.policy))

    def test_ignore_mode_is_flagged_as_material_risk(self):
        for key, code in (
            ("unresolved_parent_mode", "COMMAND_EVIDENCE_UNRESOLVED"),
            ("parent_type_mismatch_mode", "LINEAGE_PARENT_TYPE_INVALID"),
            ("prohibited_use_mode", "COMMAND_EVIDENCE_PROHIBITED"),
            ("require_evidence_mode", "LINEAGE_MISMATCH"),
        ):
            with self.subTest(key=key):
                policy = copy.deepcopy(self.policy)
                policy["command_evidence"][key] = "ignore"

                issues = validators.lint_policy_risk_modes(policy)

                self.assertEqual(1, len(issues), issues)
                self.assertEqual("POLICY_IGNORE_MATERIAL_RISK", issues[0]["code"])
                self.assertEqual(f"command_evidence.{key}", issues[0]["path"])
                self.assertIn(code, issues[0]["reason_codes"])

    def test_mangled_block_is_named_by_the_lint(self):
        policy = copy.deepcopy(self.policy)
        policy["command_evidence"] = "oops"

        issues = validators.lint_policy_risk_modes(policy)

        reported = [issue for issue in issues if issue["path"] == "command_evidence"]
        self.assertTrue(reported, issues)
        self.assertEqual("lineage", reported[0]["risk_dimension"])
        self.assertTrue(reported[0]["reason_codes"])

    def test_wrapper_typo_is_reported_by_the_document_lint(self):
        import shutil
        import tempfile

        scratch = Path(tempfile.mkdtemp()) / "policy"
        shutil.copytree(ROOT / "policy", scratch)
        original = (scratch / "command-evidence.yaml").read_text(encoding="utf-8")
        typo = original.replace("command_evidence:", "command_evidenc:", 1)
        self.assertNotEqual(original, typo)
        (scratch / "command-evidence.yaml").write_text(typo, encoding="utf-8")

        paths = [
            issue["path"]
            for issue in validators.lint_policy_document_structure(scratch)
        ]

        self.assertIn("command-evidence.yaml#command_evidence", paths)

    def test_absent_document_is_a_legal_deployment(self):
        import shutil
        import tempfile

        scratch = Path(tempfile.mkdtemp()) / "policy"
        shutil.copytree(ROOT / "policy", scratch)
        (scratch / "command-evidence.yaml").unlink()

        policy = validators.load_policy(scratch)
        self.assertEqual({}, policy["command_evidence"])
        issues = validators.lint_policy_risk_modes(
            policy
        ) + validators.lint_policy_document_structure(scratch)
        self.assertEqual([], [issue["path"] for issue in issues])

        # ...and the built-in defaults still check cited parents.
        parent = track_state(risk_records=[COMMAND_PROHIBITING_RECORD])
        state = recorded_state(parent)
        ok, violations = validators.validate_command_evidence(
            command([parent["event"]["event_id"]]),
            policy["command_evidence"],
            state=state,
            severity_map=policy["violation_severities"],
        )
        self.assertFalse(ok)
        self.assertEqual("COMMAND_EVIDENCE_PROHIBITED", violations[0]["code"])


class CommandEvidenceGatewayTest(unittest.TestCase):
    """The dispositions measured where the operator sees them."""

    @classmethod
    def setUpClass(cls):
        cls.validator = validators.load_schema(ROOT / "schema" / "zmeta-event-1.0.schema.json")
        cls.policy = validators.load_policy(ROOT / "policy")

    def time_status(self):
        return {
            "zmeta_version": "1.0",
            "event": {
                "event_id": str(uuid7()),
                "event_type": "SYSTEM_EVENT",
                "event_subtype": "TIME_STATUS",
                "ts": "2025-01-17T14:31:50Z",
            },
            "source": source(),
            "payload": {
                "system_type": "TIME_STATUS",
                "metrics": dict(TIMING_QUALITY),
            },
        }

    def process(self, cmd, state, policy=None):
        return gateway.process_message(
            json.dumps(cmd).encode("utf-8"),
            self.validator,
            self.policy if policy is None else policy,
            "L",
            gateway.TaskDedupeCache(),
            "json",
            timing_state=state,
        )

    def pipeline_state(self, *parents):
        state = recorded_state(*parents)
        state.record(self.time_status())
        return state

    def test_bare_command_passes_the_pipeline_untouched(self):
        cmd = command()
        out = self.process(cmd, self.pipeline_state())
        self.assertEqual([cmd], out)

    def test_refused_command_produces_a_valid_loud_diagnostic(self):
        parent = track_state(risk_records=[COMMAND_PROHIBITING_RECORD])
        cmd = command([parent["event"]["event_id"]])
        # Anti-vacuity: the input is schema-valid; the refusal below is the
        # evidence check speaking, not a schema error.
        self.assertEqual([], list(self.validator.iter_errors(cmd)))

        out = self.process(cmd, self.pipeline_state(parent))

        self.assertEqual(1, len(out))
        diagnostic = out[0]
        self.assertEqual("SYSTEM_EVENT", diagnostic["event"]["event_type"])
        self.assertEqual("SCHEMA_VIOLATION", diagnostic["event"]["event_subtype"])
        self.assertEqual("REJECTED", diagnostic["payload"]["state"])
        metrics = diagnostic["payload"]["metrics"]
        # Diagnostic-first posture: the v1.0 wire keeps the documented
        # fallback code; the minted code rides diagnostic_code.
        self.assertEqual("LINEAGE_MISMATCH", metrics["reason_code"])
        self.assertEqual("COMMAND_EVIDENCE_PROHIBITED", metrics["diagnostic_code"])
        self.assertEqual(cmd["event"]["event_id"], metrics["original_event_id"])
        # Task correlation survives the SCHEMA_VIOLATION shape (the lineage
        # codes are not in the deliberately task-limited TASK_ACK vocabulary).
        self.assertEqual(cmd["payload"]["task_id"], metrics["task_id"])
        # The refusal itself is a valid instance: loud, filterable, honest.
        self.assertEqual([], list(self.validator.iter_errors(diagnostic)))

    def test_unresolved_citation_forwards_with_a_loud_warning(self):
        missing = str(uuid7())
        cmd = command([missing])

        out = self.process(cmd, self.pipeline_state())

        self.assertEqual(2, len(out))
        self.assertEqual(cmd, out[0], "the warned command must forward unmodified")
        warning = out[1]
        self.assertEqual("SCHEMA_VIOLATION", warning["event"]["event_subtype"])
        self.assertEqual("WARNING", warning["payload"]["state"])
        metrics = warning["payload"]["metrics"]
        self.assertEqual("LINEAGE_PARENT_UNRESOLVED", metrics["reason_code"])
        self.assertEqual("COMMAND_EVIDENCE_UNRESOLVED", metrics["diagnostic_code"])
        self.assertEqual([missing], metrics["unresolved"])
        self.assertEqual([], list(self.validator.iter_errors(warning)))

    def test_degrade_mode_forwards_the_stamped_command(self):
        policy = copy.deepcopy(self.policy)
        policy["command_evidence"]["prohibited_use_mode"] = "degrade"
        parent = track_state(risk_records=[COMMAND_PROHIBITING_RECORD])
        cmd = command([parent["event"]["event_id"]])

        out = self.process(cmd, self.pipeline_state(parent), policy=policy)

        self.assertEqual(2, len(out))
        forwarded = out[0]
        records = forwarded["payload"]["extensions"]["risk_adjudication"]
        self.assertEqual("COMMAND_EVIDENCE_PROHIBITED", records[0]["reason_code"])
        self.assertEqual("DEGRADED_ACCEPT", records[0]["policy_decision"])
        self.assertIn("AUTONOMY_TASKING", records[0]["prohibited_uses"])
        self.assertEqual([], list(self.validator.iter_errors(forwarded)))
        self.assertEqual(
            "LINEAGE_MISMATCH", out[1]["payload"]["metrics"]["reason_code"]
        )

    def test_permitted_citation_forwards_clean(self):
        parent = inference()
        cmd = command([parent["event"]["event_id"]])
        untouched = copy.deepcopy(cmd)

        out = self.process(cmd, self.pipeline_state(parent))

        self.assertEqual([untouched], out, "a permitted citation must add nothing")

    def test_strict_knob_refuses_bare_commands_in_the_pipeline(self):
        policy = copy.deepcopy(self.policy)
        policy["command_evidence"]["require_evidence"] = True
        cmd = command()

        out = self.process(cmd, self.pipeline_state(), policy=policy)

        self.assertEqual(1, len(out))
        self.assertEqual("REJECTED", out[0]["payload"]["state"])
        self.assertEqual(
            "LINEAGE_MISMATCH", out[0]["payload"]["metrics"]["reason_code"]
        )
        self.assertEqual([], list(self.validator.iter_errors(out[0])))


if __name__ == "__main__":
    unittest.main()


class CommandEvidenceStickyLabelTest(unittest.TestCase):
    """Pre-cut review findings: the evidence index must not be downgradable.

    Duplicate suppression is TIME-bounded (EventDedupeCache TTL) while this
    index is only CARDINALITY-bounded, so a clean copy of an already-seen
    event_id arriving after the dedupe window used to overwrite the recorded
    prohibition -- and the citing command then forwarded with no diagnostic
    at all. Distinct from the banked VW-16 flood-eviction item, which
    downgrades REJECT to unresolved-WARN and is closed by
    unresolved_parent_mode: reject; this one downgraded REJECT to CLEAN and
    survived that mitigation.
    """

    @classmethod
    def setUpClass(cls):
        cls.policy = validators.load_policy(ROOT / "policy")
        cls.ce_policy = cls.policy["command_evidence"]
        cls.severity_map = cls.policy["violation_severities"]

    def check(self, event, state):
        return validators.validate_command_evidence(
            event, self.ce_policy, state=state, profile=None,
            severity_map=self.severity_map,
        )

    def test_resent_clean_copy_cannot_erase_a_recorded_prohibition(self):
        parent = track_state(risk_records=[COMMAND_PROHIBITING_RECORD])
        parent_id = parent["event"]["event_id"]
        state = recorded_state(parent)
        ok, violations = self.check(command(parent_ids=[parent_id]), state)
        self.assertFalse(ok)
        self.assertEqual("COMMAND_EVIDENCE_PROHIBITED", violations[0]["code"])

        # The attack: same event_id, no risk_adjudication at all.
        clean_copy = track_state(event_id=parent_id)
        self.assertNotIn("extensions", clean_copy["payload"])
        state.record(clean_copy)

        entry = state.command_evidence[parent_id]
        self.assertIn("COMMAND_BASIS", entry["prohibited_uses"])
        self.assertIn("AUTONOMY_TASKING", entry["prohibited_uses"])
        self.assertIn("PRODUCER_NOT_ALLOWED", entry["risk_reason_codes"])

        ok_after, violations_after = self.check(
            command(parent_ids=[parent_id]), state
        )
        self.assertFalse(ok_after, "a re-send erased the recorded prohibition")
        self.assertEqual("COMMAND_EVIDENCE_PROHIBITED", violations_after[0]["code"])

    def test_labels_union_across_resends_rather_than_replace(self):
        parent = track_state(risk_records=[COMMAND_PROHIBITING_RECORD])
        parent_id = parent["event"]["event_id"]
        state = recorded_state(parent)
        other = copy.deepcopy(COMMAND_PROHIBITING_RECORD)
        other["reason_code"] = "TIMING_STATUS_STALE"
        other["prohibited_uses"] = ["FUSION_INPUT"]
        state.record(track_state(event_id=parent_id, risk_records=[other]))
        entry = state.command_evidence[parent_id]
        self.assertEqual(
            ("AUTONOMY_TASKING", "COMMAND_BASIS", "FUSION_INPUT"),
            entry["prohibited_uses"],
        )
        self.assertEqual(
            ("PRODUCER_NOT_ALLOWED", "TIMING_STATUS_STALE"),
            entry["risk_reason_codes"],
        )

    def test_unreadable_risk_shape_is_unadjudicable_not_clean(self):
        # A schema-legal non-list risk_adjudication (extensions is
        # additionalProperties: true) used to have its labels silently
        # dropped, so the parent recorded as unlabeled and citations passed.
        parent = track_state()
        parent_id = parent["event"]["event_id"]
        parent["payload"]["extensions"] = {
            "risk_adjudication": dict(COMMAND_PROHIBITING_RECORD)
        }
        state = recorded_state(parent)
        self.assertEqual(
            ("UNADJUDICABLE_RISK_SHAPE",),
            state.command_evidence[parent_id]["prohibited_uses"],
        )
        ok, violations = self.check(command(parent_ids=[parent_id]), state)
        self.assertFalse(ok)
        self.assertEqual("COMMAND_EVIDENCE_PROHIBITED", violations[0]["code"])


class CommandEvidenceKeyLintTest(unittest.TestCase):
    """A typo in any knob must not silently revert it to the shipped default.

    Pre-cut review: the block had mode-VALUE and wrapper-KEY lints but
    nothing checking key NAMES or value TYPES.
    """

    def lint(self, block):
        return [
            issue
            for issue in validators.lint_policy_risk_modes({"command_evidence": block})
            if issue["path"].startswith("command_evidence.")
        ]

    def test_misspelled_mode_key_is_reported(self):
        issues = self.lint({"unresolved_parent_mod": "reject"})
        self.assertEqual(1, len(issues), issues)
        self.assertEqual("command_evidence.unresolved_parent_mod", issues[0]["path"])
        self.assertIn("unknown command-evidence key", issues[0]["message"])
        self.assertEqual("lineage", issues[0]["risk_dimension"])

    def test_wrong_typed_knob_is_reported(self):
        issues = self.lint({"require_evidence": "true"})
        self.assertEqual(1, len(issues), issues)
        self.assertIn("must be bool", issues[0]["message"])

    def test_wrong_typed_list_and_int_knobs_are_reported(self):
        self.assertIn(
            "must be list",
            self.lint({"motivating_parent_event_types": "FUSION_EVENT"})[0]["message"],
        )
        self.assertIn(
            "must be int",
            self.lint({"evidence_index_max_entries": "4096"})[0]["message"],
        )

    def test_shipped_policy_passes_the_key_lint(self):
        shipped = validators.load_policy(ROOT / "policy")["command_evidence"]
        self.assertEqual([], self.lint(shipped))
