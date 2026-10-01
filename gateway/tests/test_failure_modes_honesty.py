"""Shipped configs never advertise a failure mode the gateway does not read.

The edge configs once enabled observation_timeout, deconfliction_offline and
fusion_instability, and timing_loss.gate_fusion_threshold. The gateway read none
of them, so a deployment that copied a shipped config believed it had command
queueing and instability holds it did not have. This pins the shipped configs to
what the gateway implements and checks the startup warning for anything else.
"""

import importlib.util
import io
import json
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("zmeta_gateway_fm", ROOT / "gateway" / "src" / "gateway.py")
gateway = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gateway)


def args_with(*argv):
    with mock.patch("sys.argv", ["gateway.py", "--profile", "H", *argv]):
        return gateway.parse_args()


class FailureModesHonestyTest(unittest.TestCase):
    def test_every_shipped_config_names_only_what_the_gateway_reads(self):
        configs = sorted((ROOT / "configs").glob("*.json"))
        self.assertTrue(configs)
        seen = 0
        for path in configs:
            with self.subTest(config=path.name):
                data = json.loads(path.read_text(encoding="utf-8"))
                if "failure_modes" in data:
                    seen += 1
                    self.assertEqual([], gateway.unread_failure_mode_keys(data["failure_modes"]))
        self.assertGreater(seen, 0, "no shipped config carries failure_modes; the pin is vacuous")

    def test_unread_keys_are_named(self):
        modes = {
            "timing_loss": {"enabled": True, "confidence_reduction_factor": 2.0, "gate_fusion_threshold": 0.4},
            "deconfliction_offline": {"enabled": True},
        }
        self.assertEqual(
            ["failure_modes.deconfliction_offline", "failure_modes.timing_loss.gate_fusion_threshold"],
            gateway.unread_failure_mode_keys(modes),
        )
        self.assertEqual([], gateway.unread_failure_mode_keys({"timing_loss": {"enabled": True}}))
        self.assertEqual([], gateway.unread_failure_mode_keys(None))

    def test_startup_warns_for_an_unread_mode_and_keeps_running(self):
        config = {"failure_modes": {"timing_loss": {"enabled": True}, "fusion_instability": {"enabled": True}}}
        buffer = io.StringIO()
        with redirect_stderr(buffer):
            settings = gateway.build_settings(ROOT, args_with(), config)
        self.assertIn("failure_modes.fusion_instability is not implemented", buffer.getvalue())
        self.assertEqual(config["failure_modes"], settings["failure_modes"])
        quiet = io.StringIO()
        with redirect_stderr(quiet):
            gateway.build_settings(ROOT, args_with(), {"failure_modes": {"timing_loss": {"enabled": True}}})
        self.assertEqual("", quiet.getvalue())

    def test_the_implemented_set_matches_what_the_timing_loss_path_reads(self):
        # If the gateway starts reading another member, this set must grow with it.
        self.assertEqual({"timing_loss"}, set(gateway.IMPLEMENTED_FAILURE_MODES))
        source = (ROOT / "gateway" / "src" / "gateway.py").read_text(encoding="utf-8")
        for member in gateway.IMPLEMENTED_FAILURE_MODES["timing_loss"]:
            self.assertIn(f'timing_loss.get("{member}"', source)


if __name__ == "__main__":
    unittest.main()
