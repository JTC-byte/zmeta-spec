"""Protected strip-path tests.

strip_optional_fields must never remove accepted-risk labels
(payload.extensions.risk_adjudication) or external-promotion evidence
(payload.extensions.external_promotion): silently deleting them would
launder degraded or externally-promoted data into clean-looking data
(docs/zmeta_change_governance.md no-silent-strip rule). A config that lists
a protected path (or anything nested under one) must be rejected at load,
not silently honored at runtime.
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
