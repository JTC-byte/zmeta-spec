"""The gateway's failure_modes.timing_loss degradation under contract 4.5.1 (2026-11-02).

The record carries the confidence it replaced, and a reduction factor below 1,
which would raise the value, is declined (contract 4.2 makes an increase a
new event). Written before the code, seen failing first.
"""

import importlib.util
import unittest
from pathlib import Path

from zmeta_uuid import uuid7


ROOT = Path(__file__).resolve().parents[2]
GATEWAY_PATH = ROOT / "gateway" / "src" / "gateway.py"
spec_gw = importlib.util.spec_from_file_location("zmeta_gateway_claimed", GATEWAY_PATH)
gateway = importlib.util.module_from_spec(spec_gw)
spec_gw.loader.exec_module(gateway)


class _UnsyncedTiming:
    def get_timing(self, event):
        return "key", {"sync_state": "UNSYNCED"}


def _state_event(confidence):
    return {
        "zmeta_version": "1.0",
        "event": {
            "event_id": str(uuid7()),
            "event_type": "STATE_EVENT",
            "event_subtype": "TRACK_STATE",
            "ts": "2025-01-17T14:30:00Z",
        },
        "source": {"platform_id": "fusion-node-01", "node_role": "GATEWAY", "producer": "fusion-engine"},
        "profile": "L",
        "payload": {"track_id": "track-1", "geo": {"lat": 34.0, "lon": -118.0, "alt_m": 100.0}, "valid_for_ms": 1000},
        "confidence": confidence,
        "lineage": {"based_on": [str(uuid7())]},
    }


class FailureModeClaimedValuesTest(unittest.TestCase):
    def test_timing_loss_record_carries_the_confidence_it_replaced(self):
        event = _state_event(0.8)
        changed = gateway._apply_failure_mode_degradation(
            event, {"timing_loss": {"enabled": True, "confidence_reduction_factor": 2.0}}, _UnsyncedTiming()
        )
        self.assertTrue(changed)
        self.assertAlmostEqual(0.4, event["confidence"])
        risk = event["payload"]["extensions"]["risk_adjudication"][0]
        self.assertEqual(
            {"confidence_reduction_factor": 2.0, "confidence_claimed": 0.8}, risk["effects"]
        )

    def test_timing_loss_factor_below_one_is_declined(self):
        event = _state_event(0.4)
        changed = gateway._apply_failure_mode_degradation(
            event, {"timing_loss": {"enabled": True, "confidence_reduction_factor": 0.5}}, _UnsyncedTiming()
        )
        self.assertFalse(changed)
        self.assertAlmostEqual(0.4, event["confidence"])
        self.assertNotIn("extensions", event["payload"])


if __name__ == "__main__":
    unittest.main()
