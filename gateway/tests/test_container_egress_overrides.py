"""The container deployment depends on CLI overrides beating the config file.

A gateway SENDS its forward and CoT streams. `configs/*.json` aim both at
127.0.0.1, which is correct on a host and wrong inside a container, where
127.0.0.1 is the container's own loopback: the send succeeds, nothing can read
the destination, and no error is raised. Measured 2026-07-30 before the Compose
files were corrected, a container reported `recv=722 fwd=722` while a receiver
on the host's 127.0.0.1:5556 saw zero datagrams.

The correction is that `deploy/*/docker-compose.yml` pass `--forward-host`,
`--cot-host` and `--forward-port` on the command line while still loading the
config file. That only works because argument values are applied after the
config and win over it. This file pins that precedence, in both directions, so
a refactor cannot quietly restore the broken deployment.

WHAT THE COMPOSE ASSERTION BELOW DOES NOT PROVE. It checks that the override
flags are present in the shipped Compose files. It does not prove a datagram
reaches the host: that needs Docker and was verified by running the pair end to
end (events fed to the edge's published port arrived as ZMeta JSON on the host's
5556 and as CoT on 6969). Treat the text assertion as a guard against silent
removal, not as evidence of delivery.
"""

import importlib.util
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
GATEWAY_PATH = ROOT / "gateway" / "src" / "gateway.py"
spec_gw = importlib.util.spec_from_file_location("zmeta_gateway_container", GATEWAY_PATH)
gateway = importlib.util.module_from_spec(spec_gw)
spec_gw.loader.exec_module(gateway)

# The container's own loopback. A config carrying this is exactly the shipped
# state that made the deployment undeliverable.
LOOPBACK_CONFIG = {
    "profile": "H",
    "forward": {"host": "127.0.0.1", "port": 5556},
    "cot": {"host": "127.0.0.1", "port": 6969},
}


def args_with(*argv):
    with mock.patch("sys.argv", ["gateway.py", "--profile", "H", *argv]):
        return gateway.parse_args()


class ContainerEgressOverrideTest(unittest.TestCase):
    def test_config_alone_still_yields_the_loopback_destinations(self):
        """The control. Without overrides the config's own values must survive.

        If this ever stops holding, the override test below would pass for a
        reason that has nothing to do with precedence.
        """
        settings = gateway.build_settings(ROOT, args_with(), LOOPBACK_CONFIG)
        self.assertEqual(settings["forward_host"], "127.0.0.1")
        self.assertEqual(settings["forward_port"], 5556)
        self.assertEqual(settings["cot_host"], "127.0.0.1")

    def test_cli_forward_host_overrides_the_config_loopback(self):
        settings = gateway.build_settings(
            ROOT, args_with("--forward-host", "host.docker.internal"), LOOPBACK_CONFIG
        )
        self.assertEqual(
            settings["forward_host"],
            "host.docker.internal",
            "the container deployment forwards to a namespace nothing can read "
            "when the config wins over --forward-host",
        )

    def test_cli_cot_host_overrides_the_config_loopback(self):
        settings = gateway.build_settings(
            ROOT, args_with("--cot-host", "host.docker.internal"), LOOPBACK_CONFIG
        )
        self.assertEqual(settings["cot_host"], "host.docker.internal")

    def test_cli_forward_port_overrides_the_config_local_consumer_port(self):
        """Node-to-node targets the receiving node's LISTEN port.

        5556 is the local-consumer destination; edge traffic sent to a gateway
        node's 5556 arrives nowhere and reports nothing, so deploy/edge passes
        5555 explicitly.
        """
        settings = gateway.build_settings(
            ROOT, args_with("--forward-port", "5555"), LOOPBACK_CONFIG
        )
        self.assertEqual(settings["forward_port"], 5555)


class ShippedComposeCarriesTheOverridesTest(unittest.TestCase):
    """Guards against silent removal. Not evidence of delivery: see module docstring."""

    def test_gateway_compose_overrides_both_egress_hosts(self):
        text = (ROOT / "deploy" / "gateway" / "docker-compose.yml").read_text(encoding="utf-8")
        self.assertIn("--forward-host", text)
        self.assertIn("--cot-host", text)
        self.assertIn("host.docker.internal:host-gateway", text)

    def test_edge_compose_overrides_forward_host_and_port(self):
        text = (ROOT / "deploy" / "edge" / "docker-compose.yml").read_text(encoding="utf-8")
        self.assertIn("--forward-host", text)
        self.assertIn("--forward-port", text)

    def test_both_compose_files_allow_a_distinct_host_port(self):
        """Both nodes listen on 5555 inside their container, so a co-hosted pair
        needs different host ports or the second fails to bind."""
        gw = (ROOT / "deploy" / "gateway" / "docker-compose.yml").read_text(encoding="utf-8")
        edge = (ROOT / "deploy" / "edge" / "docker-compose.yml").read_text(encoding="utf-8")
        self.assertIn("ZMETA_GATEWAY_PORT", gw)
        self.assertIn("ZMETA_EDGE_PORT", edge)


if __name__ == "__main__":
    unittest.main()
