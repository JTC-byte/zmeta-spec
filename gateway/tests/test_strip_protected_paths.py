"""Protected strip-path tests.

strip_optional_fields must never remove accepted-risk labels
(payload.extensions.risk_adjudication) or external-promotion evidence
(payload.extensions.external_promotion): silently deleting them would
launder degraded or externally-promoted data into clean-looking data
(docs/zmeta_change_governance.md no-silent-strip rule). A config that lists
a protected path (or anything nested under one) must be rejected at load,
not silently honored at runtime. The command start, payload.valid_from_ts,
is protected for its own reason: it starts a command's validity window
(contract 7.8), and the refusal says so.
"""

import importlib.util
import json
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
GATEWAY_PATH = ROOT / "gateway" / "src" / "gateway.py"
spec_gw = importlib.util.spec_from_file_location("zmeta_gateway_strip", GATEWAY_PATH)
gateway = importlib.util.module_from_spec(spec_gw)
spec_gw.loader.exec_module(gateway)


def default_args():
    with mock.patch("sys.argv", ["gateway.py", "--profile", "H"]):
        return gateway.parse_args()


class ProtectedStripPathConfigTest(unittest.TestCase):
    def test_config_stripping_risk_adjudication_is_rejected_at_load(self):
        config = {
            "strip_optional_fields": [
                "source.sensor_id",
                "payload.extensions.risk_adjudication",
            ]
        }
        with self.assertRaises(ValueError) as ctx:
            gateway.build_settings(ROOT, default_args(), config)
        message = str(ctx.exception)
        self.assertIn("payload.extensions.risk_adjudication", message)
        self.assertIn("strip_optional_fields", message)

    def test_config_stripping_nested_promotion_evidence_is_rejected_at_load(self):
        config = {
            "strip_optional_fields": [
                "payload.extensions.external_promotion.evidence",
            ]
        }
        with self.assertRaises(ValueError) as ctx:
            gateway.build_settings(ROOT, default_args(), config)
        message = str(ctx.exception)
        self.assertIn("payload.extensions.external_promotion.evidence", message)
        self.assertIn("payload.extensions.external_promotion", message)

    def test_config_stripping_a_command_start_is_rejected_at_load(self):
        # Contract 7.8 (2026-11-02): valid_from_ts is the start of a command's
        # validity window, so stripping it from a same-event_id projection
        # moves the window; the catalog preserves it and so does the gateway.
        config = {"strip_optional_fields": ["payload.valid_from_ts"]}
        with self.assertRaises(ValueError):
            gateway.build_settings(ROOT, default_args(), config)

    def test_shipped_default_config_strip_list_is_accepted(self):
        shipped = json.loads(
            (ROOT / "configs" / "gateway-config.json").read_text(encoding="utf-8")
        )
        settings = gateway.build_settings(
            ROOT, default_args(), {"strip_optional_fields": shipped["strip_optional_fields"]}
        )
        self.assertEqual(shipped["strip_optional_fields"], settings["strip_optional_fields"])

    def test_default_strip_list_is_accepted(self):
        settings = gateway.build_settings(ROOT, default_args(), {})
        self.assertEqual(
            gateway.DEFAULT_STRIP_OPTIONAL_FIELDS, settings["strip_optional_fields"]
        )

    def test_lookalike_sibling_extension_is_not_blocked(self):
        # Segment-wise prefix match: a sibling extension whose name merely
        # starts with a protected name's text is not protected.
        settings = gateway.build_settings(
            ROOT,
            default_args(),
            {"strip_optional_fields": ["payload.extensions.risk_adjudication_notes"]},
        )
        self.assertEqual(
            ["payload.extensions.risk_adjudication_notes"],
            settings["strip_optional_fields"],
        )


def _refusal(path):
    with mock.patch("sys.argv", ["gateway.py", "--profile", "H"]):
        args = gateway.parse_args()
    try:
        gateway.build_settings(ROOT, args, {"strip_optional_fields": [path]})
    except ValueError as exc:
        return str(exc)
    raise AssertionError(f"a config that strips {path!r} was accepted")


class ProtectedStripPathReasonTest(unittest.TestCase):
    """Each protected prefix is refused with its own reason (pre-cut range review of 2026-11-14, N1).

    The guard gave one reason for every prefix, so a config that stripped the
    command start was told the path carries accepted-risk labels or promotion
    evidence. The reason for that prefix is the validity window (contract 7.8).
    """

    def test_every_protected_prefix_has_a_reason_of_its_own(self):
        reasons = gateway.PROTECTED_STRIP_PATH_REASONS
        self.assertEqual(list(gateway.PROTECTED_STRIP_PATH_PREFIXES), list(reasons))
        self.assertGreaterEqual(len(reasons), 3)
        self.assertEqual(len(reasons), len(set(reasons.values())))

    def test_the_command_start_refusal_names_the_validity_window(self):
        message = _refusal("payload.valid_from_ts")
        self.assertIn("'payload.valid_from_ts'", message)
        self.assertIn("validity window", message)
        self.assertIn("contract 7.8", message)
        self.assertNotIn("accepted-risk", message)
        self.assertNotIn("promotion", message)

    def test_the_risk_label_refusal_names_the_labels_alone(self):
        message = _refusal("payload.extensions.risk_adjudication")
        self.assertIn("accepted-risk labels", message)
        self.assertIn("no-laundering rule", message)
        self.assertNotIn("promotion", message)
        self.assertNotIn("validity window", message)

    def test_the_refusal_states_the_rule_then_the_prefix_and_its_reason(self):
        # from the seeded review of 2026-11-14: "and must not be silently
        # stripped" followed the reason's relative clause, so it read as if
        # the window must not be stripped; the rule now comes first
        for prefix, reason in gateway.PROTECTED_STRIP_PATH_REASONS.items():
            self.assertEqual(
                f"strip_optional_fields entry '{prefix}' is protected and must not be "
                f"silently stripped: '{prefix}' {reason}",
                _refusal(prefix),
            )

    def test_the_promotion_refusal_names_the_evidence_alone(self):
        message = _refusal("payload.extensions.external_promotion.evidence")
        self.assertIn("'payload.extensions.external_promotion'", message)
        self.assertIn("external-promotion evidence", message)
        self.assertIn("no-laundering rule", message)
        self.assertNotIn("accepted-risk", message)
        self.assertNotIn("validity window", message)


class StripOptionalFieldsRuntimeTest(unittest.TestCase):
    def test_safe_list_still_strips_optional_fields(self):
        event = {
            "event": {"event_id": "evt-1"},
            "source": {"platform_id": "node-01", "sensor_id": "cam-01", "sw_version": "1.0"},
            "payload": {
                "data_ref": "s3://raw/frame-001.jpg",
                "extensions": {
                    "risk_adjudication": [{"reason_code": "TIMING_STATUS_UNSYNCED"}],
                    "external_promotion": {"state_category": "PROMOTED_EXTERNAL_STATE"},
                },
            },
        }
        gateway._strip_optional_fields(event, gateway.DEFAULT_STRIP_OPTIONAL_FIELDS)
        self.assertNotIn("sensor_id", event["source"])
        self.assertNotIn("sw_version", event["source"])
        self.assertNotIn("data_ref", event["payload"])
        # The risk labels remain untouched by the safe default list.
        self.assertIn("risk_adjudication", event["payload"]["extensions"])
        self.assertIn("external_promotion", event["payload"]["extensions"])


if __name__ == "__main__":
    unittest.main()
