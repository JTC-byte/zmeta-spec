"""The identity the gateway stamps on the diagnostics it mints.

The producer name and node role are settings, `gateway_producer` and
`gateway_node_role`, so that a gateway deployed in another role, such as a DMZ
admission boundary, can name itself on its own evidence. The defaults are the
values the gateway has always used, and `platform_id` stays fixed.

The gateway's outgoing self-check runs role and producer authority over the
diagnostics it mints, so an identity its own policy does not authorize would
have every one of those diagnostics refused. A configured identity is therefore
checked at startup against the loaded policy, and refused before the gateway
starts. Only the identity is checked there; the schema half of the outgoing
self-check depends on the lane the gateway runs and is not an identity question.

WHAT THIS FILE DOES NOT PROVE. It proves the identity reaches every diagnostic
builder and every builder call inside `process_message`, and that the startup
check refuses what the loaded policy refuses. It does not prove a deployed
policy pack authorizes the name an operator chooses; that is the operator's
edit to `policy/producer-authority.yaml`, which the startup check reports.
"""
import copy
import importlib.util
import inspect
import json
import re
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
GATEWAY_PATH = ROOT / "gateway" / "src" / "gateway.py"
spec_gw = importlib.util.spec_from_file_location("zmeta_gateway_identity", GATEWAY_PATH)
gateway = importlib.util.module_from_spec(spec_gw)
spec_gw.loader.exec_module(gateway)

DEFAULT_SOURCE = {
    "platform_id": "zmeta-gateway",
    "node_role": "GATEWAY",
    "producer": "zmeta-gateway",
}
# A DMZ-identified boundary that keeps the producer name the shipped policy
# already authorizes for SYSTEM_EVENT.
DMZ = {"producer": "zmeta-gateway", "node_role": "DMZ"}
# A producer name the shipped policy does not authorize.
UNLISTED = {"producer": "dmz-boundary-unlisted", "node_role": "DMZ"}

COMMAND = {
    "event": {"event_id": "0190f1a0-0000-7000-8000-000000000001", "event_type": "COMMAND_EVENT"},
    "payload": {"task_id": "task-1"},
}


def args_with(*argv):
    with mock.patch("sys.argv", ["gateway.py", "--profile", "H", *argv]):
        return gateway.parse_args()


def _expected(identity):
    return {"platform_id": "zmeta-gateway", **identity}


class GatewayIdentityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = gateway.load_policy(ROOT / "policy")
        cls.validator = gateway.load_schema(ROOT / "schema" / "zmeta-event.schema.json")

    # --- the builders ------------------------------------------------------

    def test_defaults_are_the_identity_the_gateway_has_always_used(self):
        """The control. With no identity given, every builder stamps exactly
        what the gateway stamped before identity became configurable."""
        self.assertEqual(gateway.build_violation_event("SCHEMA_INVALID")["source"], DEFAULT_SOURCE)
        self.assertEqual(gateway.build_warning_event("EVENT_TS_IMPLAUSIBLE")["source"], DEFAULT_SOURCE)
        self.assertEqual(gateway.build_duplicate_ack(COMMAND)["source"], DEFAULT_SOURCE)

    def test_every_builder_stamps_a_configured_identity(self):
        identity = {"producer": "boundary-a", "node_role": "DMZ"}
        self.assertEqual(
            gateway.build_violation_event("SCHEMA_INVALID", identity=identity)["source"],
            _expected(identity),
        )
        self.assertEqual(
            gateway.build_warning_event("EVENT_TS_IMPLAUSIBLE", identity=identity)["source"],
            _expected(identity),
        )
        self.assertEqual(
            gateway.build_duplicate_ack(COMMAND, identity=identity)["source"],
            _expected(identity),
        )

    # --- process_message, the callable a deployment-side boundary imports --

    def test_process_message_stamps_the_identity_it_is_given(self):
        out = gateway.process_message(
            b"not json at all",
            self.validator,
            self.policy,
            "H",
            gateway.TaskDedupeCache(),
            "json",
            gateway_identity=DMZ,
        )
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["payload"]["metrics"]["reason_code"], "SCHEMA_INVALID")
        self.assertEqual(out[0]["source"], _expected(DMZ))

    def test_process_message_without_an_identity_keeps_the_default(self):
        out = gateway.process_message(
            b"not json at all", self.validator, self.policy, "H", gateway.TaskDedupeCache(), "json"
        )
        self.assertEqual(out[0]["source"], DEFAULT_SOURCE)

    def test_no_builder_call_in_process_message_drops_the_identity(self):
        """A structural guard. The decode-failure test above reaches one of the
        builder calls inside process_message; this one checks that every
        builder call there passes the identity through, so a refactor cannot
        quietly restore the hardcoded identity on a single refusal path."""
        source = inspect.getsource(gateway.process_message)
        calls = re.findall(r"build_(?:violation_event|warning_event|duplicate_ack)\(", source)
        passed = re.findall(r"identity=gateway_identity", source)
        self.assertGreater(len(calls), 0)
        self.assertEqual(len(passed), len(calls))

    def test_the_encoding_fallback_diagnostic_carries_the_settings_identity(self):
        poisoned = json.loads(
            (ROOT / "examples" / "encoding-roundtrip.jsonl").read_text(encoding="utf-8").splitlines()[0]
        )
        poisoned["event"]["ts"] = "2025-02-01T12:00:00.1234Z"
        settings = {
            "output_encoding": "compact",
            "stamp_contract_hash": False,
            "profile": "H",
            "gateway_producer": "boundary-a",
            "gateway_node_role": "DMZ",
        }
        _, emitted = gateway._encode_outgoing_or_diagnostic(
            poisoned, settings, contract_hashes=None, should_stamp_profile=False, metrics=None
        )
        self.assertEqual(emitted["payload"]["metrics"]["reason_code"], "ENCODING_UNSUPPORTED")
        self.assertEqual(emitted["source"], _expected({"producer": "boundary-a", "node_role": "DMZ"}))

    # --- settings ------------------------------------------------------------

    def test_settings_default_to_the_historical_identity(self):
        settings = gateway.build_settings(ROOT, args_with(), {"profile": "H"})
        self.assertEqual(settings["gateway_producer"], "zmeta-gateway")
        self.assertEqual(settings["gateway_node_role"], "GATEWAY")

    def test_settings_read_the_identity_from_config_and_flags_win(self):
        config = {"profile": "H", "gateway_producer": "from-config", "gateway_node_role": "DMZ"}
        settings = gateway.build_settings(ROOT, args_with(), config)
        self.assertEqual((settings["gateway_producer"], settings["gateway_node_role"]), ("from-config", "DMZ"))
        settings = gateway.build_settings(
            ROOT, args_with("--gateway-producer", "from-flag", "--gateway-node-role", "CLOUD"), config
        )
        self.assertEqual((settings["gateway_producer"], settings["gateway_node_role"]), ("from-flag", "CLOUD"))

    def test_an_empty_configured_identity_is_refused(self):
        for key in ("gateway_producer", "gateway_node_role"):
            with self.assertRaises(ValueError):
                gateway.build_settings(ROOT, args_with(), {"profile": "H", key: "   "})

    # --- the startup check -------------------------------------------------------

    def test_the_identity_check_reports_what_the_loaded_policy_refuses(self):
        self.assertEqual(gateway.check_gateway_identity({}, self.policy), [])
        self.assertEqual(gateway.check_gateway_identity(DMZ, self.policy), [])
        codes = {v["code"] for v in gateway.check_gateway_identity(UNLISTED, self.policy)}
        self.assertIn("PRODUCER_NOT_ALLOWED", codes)
        codes = {v["code"] for v in gateway.check_gateway_identity(
            {"producer": "zmeta-gateway", "node_role": "BOUNDARY"}, self.policy)}
        self.assertIn("EVENT_TYPE_NOT_ALLOWED_FOR_ROLE", codes)

    def test_startup_refuses_a_configured_identity_its_own_policy_would_refuse(self):
        settings = {"gateway_producer": UNLISTED["producer"], "gateway_node_role": UNLISTED["node_role"]}
        with self.assertRaises(SystemExit) as refused:
            gateway._enforce_gateway_identity(settings, self.policy)
        self.assertIn("PRODUCER_NOT_ALLOWED", str(refused.exception))
        gateway._enforce_gateway_identity(
            {"gateway_producer": DMZ["producer"], "gateway_node_role": DMZ["node_role"]}, self.policy
        )

    def test_the_default_identity_is_never_checked_at_startup(self):
        """Default behavior is unchanged. A policy pack that does not authorize
        zmeta-gateway already loses the gateway's diagnostics today; making
        identity configurable must not turn that into a refusal to start."""
        policy = copy.deepcopy(self.policy)
        policy["producer_authority"]["producers"].pop("zmeta-gateway")
        self.assertNotEqual(gateway.check_gateway_identity({}, policy), [])
        gateway._enforce_gateway_identity(
            {"gateway_producer": "zmeta-gateway", "gateway_node_role": "GATEWAY"}, policy
        )
        gateway._enforce_gateway_identity({}, policy)


    # --- main ----------------------------------------------------------------

    def test_main_refuses_to_start_before_it_opens_a_socket(self):
        """main() runs the startup check before it creates a socket. The socket
        is patched to raise, so a main() that skipped the check fails this test
        at the socket instead of binding a real port and waiting forever."""
        argv = ["gateway.py", "--profile", "H",
                "--gateway-producer", UNLISTED["producer"], "--gateway-node-role", UNLISTED["node_role"]]
        with mock.patch("sys.argv", argv),                 mock.patch.object(gateway.socket, "socket", side_effect=RuntimeError("reached the socket")):
            with self.assertRaises(SystemExit) as refused:
                gateway.main()
        self.assertIn("PRODUCER_NOT_ALLOWED", str(refused.exception))

    def test_main_passes_its_identity_to_process_message(self):
        """A structural guard. The receive loop cannot run in a unit test, so
        this checks that main() hands process_message the configured identity."""
        self.assertIn("gateway_identity=_identity_from_settings(settings)", inspect.getsource(gateway.main))


if __name__ == "__main__":
    unittest.main()
