"""The state-projector-* wildcard is gone from the reference policy.

Adjudicated 2026-08-02 after the live-readiness audit sized the hole from two
axes: the wildcard authorized any producer matching a broad glob to emit
authoritative STATE_EVENTs with no external-promotion evidence and no named
identity, while no reference component used it (the track projector runs as
fusion-*). A deployment that needs a state projector now adds a named
producer deliberately, the way configs/policy-variants/producer-authority.
strict.yaml already does with state-projector-01. Removal closes the
demonstrated injection path: an unnamed projector displaying tracks
indistinguishable from adjudicated ones.
"""

import importlib.util
import unittest
from pathlib import Path

from zmeta_uuid import uuid7

ROOT = Path(__file__).resolve().parents[2]
VALIDATORS_PATH = ROOT / "gateway" / "src" / "validators.py"
spec = importlib.util.spec_from_file_location("zmeta_validators_spw", VALIDATORS_PATH)
validators = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validators)


def state_event(producer):
    parent_id = str(uuid7())
    return {
        "zmeta_version": "1.0",
        "event": {
            "event_id": str(uuid7()),
            "event_type": "STATE_EVENT",
            "event_subtype": "TRACK_STATE",
            "ts": "2025-01-17T14:30:00Z",
        },
        "source": {
            "platform_id": "node-1",
            "node_role": "GATEWAY",
            "producer": producer,
        },
        "profile": "H",
        "payload": {
            "track_id": "track-1",
            "geo": {"lat": 34.0, "lon": -118.0, "alt_m": 100.0},
            "valid_for_ms": 1000,
            "timing_quality": {
                "time_source": "GPS_PPS",
                "sync_state": "LOCKED",
                "est_error_ms": 1,
                "last_sync_ts": "2025-01-17T14:29:59Z",
            },
        },
        "confidence": 0.7,
        "lineage": {"based_on": [parent_id], "transform": "fuse:track"},
    }


class StateProjectorWildcardRemovedTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = validators.load_policy(ROOT / "policy")
        cls.severity_map = cls.policy["violation_severities"]
        cls.authority = cls.policy["producer_authority"]

    def validate_authority(self, event):
        return validators.validate_producer_authority(
            event, self.authority, self.severity_map
        )

    def test_the_wildcard_is_not_in_the_shipped_policy(self):
        """The stanza itself must be gone, not merely unreachable."""
        producers = self.authority.get("producers", self.authority)
        flat = str(sorted(str(k) for k in self._producer_keys(producers)))
        self.assertNotIn("state-projector-*", flat)

    def _producer_keys(self, node, out=None):
        out = [] if out is None else out
        if isinstance(node, dict):
            for key, value in node.items():
                out.append(key)
                self._producer_keys(value, out)
        return out

    def test_an_unnamed_state_projector_is_refused(self):
        """The audit's injection path: an authoritative track from a producer
        nobody named. With the wildcard gone this must refuse, not validate."""
        ok, violations = self.validate_authority(state_event("state-projector-99"))
        self.assertFalse(
            ok,
            "state-projector-99 emitted an authoritative STATE_EVENT with no "
            "promotion evidence and no named authority - the wildcard is back "
            "or something broader admitted it",
        )
        self.assertEqual("PRODUCER_NOT_ALLOWED", violations[0]["code"])

    def test_the_legitimate_internal_fusion_path_still_works(self):
        """Positive control: the removal must not touch fusion-*, which is the
        path the reference track projector actually uses."""
        ok, violations = self.validate_authority(state_event("fusion-engine"))
        self.assertTrue(ok, violations)


if __name__ == "__main__":
    unittest.main()
