"""The gateway refuses to start on a CoT profile it cannot run.

The `cds` profile of the CoT egress adapter requires `how` as a deployment
claim. A gateway configured for that profile without one would refuse every
track at egress, each refusal counted as a cot_skipped record, and nothing
would say why at startup. build_settings therefore validates the CoT config
when it reads it, and main() turns the ValueError into the same SystemExit it
gives every other configuration error.
"""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
GATEWAY_PATH = ROOT / "gateway" / "src" / "gateway.py"
spec_gw = importlib.util.spec_from_file_location("zmeta_gateway_cot_profile", GATEWAY_PATH)
gateway = importlib.util.module_from_spec(spec_gw)
spec_gw.loader.exec_module(gateway)


def args_with(*argv):
    with mock.patch("sys.argv", ["gateway.py", "--profile", "H", *argv]):
        return gateway.parse_args()


def settings_for(cot_config):
    return gateway.build_settings(ROOT, args_with(), {"cot": {"config": cot_config}})


class GatewayCotProfileConfigTest(unittest.TestCase):
    def test_a_cds_profile_without_how_is_refused_when_settings_are_built(self):
        with self.assertRaises(ValueError) as caught:
            settings_for({"profile": "cds"})
        self.assertIn("how", str(caught.exception))

    def test_a_cds_profile_with_how_is_accepted_verbatim(self):
        settings = settings_for({"profile": "cds", "how": "m-f", "stale_window_s": 120})
        self.assertEqual({"profile": "cds", "how": "m-f", "stale_window_s": 120}, settings["cot_config"])

    def test_an_unknown_profile_is_refused(self):
        with self.assertRaises(ValueError):
            settings_for({"profile": "strict", "how": "m-f"})

    def test_the_standard_config_is_unchanged(self):
        settings = settings_for({"geopointsrc": "GPS"})
        self.assertEqual({"geopointsrc": "GPS"}, settings["cot_config"])

    def test_a_standard_config_with_a_how_that_is_not_a_token_is_refused_at_startup(self):
        for bad in ("", "machine", 5, True):
            with self.subTest(how=bad):
                with self.assertRaises(ValueError) as caught:
                    settings_for({"how": bad})
                self.assertIn("how", str(caught.exception))
        self.assertEqual({"how": "m-r"}, settings_for({"how": "m-r"})["cot_config"])
        self.assertEqual({"how": None}, settings_for({"how": None})["cot_config"])

    def test_a_mistyped_cot_config_fails_loud_not_open(self):
        # A live run showed cot.config given as a string starting the gateway
        # on the standard profile, sending unreduced CoT where the deployment
        # meant the guard-facing shape.
        for bad in ("cds", ["cds"], 5):
            with self.subTest(config=bad):
                with self.assertRaises(ValueError):
                    gateway.build_settings(ROOT, args_with(), {"cot": {"config": bad}})
        # A JSON null is "no adapter settings", as before.
        self.assertIsNone(gateway.build_settings(ROOT, args_with(), {"cot": {"config": None}})["cot_config"])
        with self.assertRaises(ValueError) as caught:
            gateway.build_settings(ROOT, args_with(), {"cot": {"cot_config": {"profile": "cds", "how": "m-f"}}})
        self.assertIn("cot_config", str(caught.exception))
        # host and port alone, as the shipped example config has them, still build.
        settings = gateway.build_settings(ROOT, args_with(), {"cot": {"host": "127.0.0.1", "port": 6969}})
        self.assertEqual(6969, settings["cot_port"])
        self.assertNotIn("profile", settings.get("cot_config") or {})

    def test_main_exits_on_a_bad_profile_before_opening_a_socket(self):
        with tempfile.TemporaryDirectory() as folder:
            config_path = Path(folder) / "gateway.json"
            config_path.write_text(json.dumps({"cot": {"config": {"profile": "cds"}}}), encoding="utf-8")
            argv = ["gateway.py", "--profile", "H", "--config", str(config_path)]
            with mock.patch("sys.argv", argv), \
                    mock.patch.object(gateway.socket, "socket", side_effect=RuntimeError("reached the socket")):
                with self.assertRaises(SystemExit) as caught:
                    gateway.main()
        self.assertIn("how", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
