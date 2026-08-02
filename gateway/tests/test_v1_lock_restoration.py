"""Data written under the v1.0 lock validates under the v1.0 lock. Forever.

The original v1.0 contract (v1.0.0 through v1.0.5) defined event_subtype as
any non-empty string. The v1.1.0 release commit (76e3855) added a per-type
subtype enum INTO the v1.0 schema file, silently narrowing the locked
contract: the v1.0.5 tag's own example corpus carried
event_subtype "RF_OBSERVATION", legal when written, rejected afterward. The
corpus record was later edited away, which hid the breach until the X1-02
gate inventory ran the stronger form of the schema gate on 2026-08-02.

Maintainer adjudication, 2026-08-02: restore the v1.0 contract; the
controlled subtype vocabulary stays in the v1.1.0 schema, where narrowing
is lawful because producers opt into that stamp.

The record below is embedded verbatim from the v1.0.5 tag
(git show v1.0.5:examples/zmeta-examples-1.0.jsonl). Do not modernize it:
its whole value is that it is exactly what a v1.0.5-era producer emitted.
"""

import copy
import json
import unittest
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[2]

V105_RF_OBSERVATION = json.loads(
    '{"zmeta_version":"1.0","event":{"event_id":"019c2b5c-c045-7222-be17-463750a407f4",'
    '"event_type":"OBSERVATION_EVENT","event_subtype":"RF_OBSERVATION",'
    '"ts":"2025-01-17T14:30:00Z","t_publish":"2025-01-17T14:30:01Z",'
    '"t_receive":"2025-01-17T14:30:02Z"},'
    '"source":{"platform_id":"sensor-node-01","node_role":"EDGE","producer":"rf-sensor"},'
    '"profile":"H","payload":{"modality":"RF",'
    '"features":{"center_freq_hz":2450000000,"bandwidth_hz":20000000,"power_dbm":-35.2},'
    '"geo":{"lat":34.0522,"lon":-118.2437,"alt_m":120.5},'
    '"data_ref":{"ref_id":"rf-capture-20250117-143000Z-0001","store":"local","kind":"RAW",'
    '"format":"iq","t_start":"2025-01-17T14:29:58Z","t_end":"2025-01-17T14:30:02Z"},'
    '"timing_quality":{"time_source":"GPS_PPS","sync_state":"LOCKED",'
    '"est_error_ms":1,"last_sync_ts":"2025-01-17T14:29:59Z"}}}'
)


class V1LockRestorationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema_v10 = json.loads(
            (ROOT / "schema" / "zmeta-event-1.0.schema.json").read_text(
                encoding="utf-8"
            )
        )
        cls.schema_v110 = json.loads(
            (ROOT / "schema" / "zmeta-event-1.1.0.schema.json").read_text(
                encoding="utf-8"
            )
        )

    def test_a_v105_era_record_validates_under_v10_as_the_lock_promised(self):
        errors = sorted(
            jsonschema.Draft202012Validator(self.schema_v10).iter_errors(
                V105_RF_OBSERVATION
            ),
            key=lambda e: list(e.path),
        )
        self.assertFalse(
            errors,
            "a record that was legal under the original locked v1.0 contract "
            f"is rejected by the current v1.0 schema: {errors[0].message if errors else ''}",
        )

    def test_the_subtype_vocabulary_still_binds_where_it_lawfully_lives(self):
        """The restoration must not loosen v1.1.0: the controlled vocabulary
        stays binding for producers who opt into that stamp."""
        modern = copy.deepcopy(V105_RF_OBSERVATION)
        modern["zmeta_version"] = "1.1.0"
        errors = list(
            jsonschema.Draft202012Validator(self.schema_v110).iter_errors(modern)
        )
        self.assertTrue(
            errors,
            "a free-form subtype was ACCEPTED under the v1.1.0 stamp - the "
            "controlled vocabulary has come loose from the version where it "
            "lawfully lives",
        )

    def test_the_v10_schema_carries_no_subtype_consistency_block(self):
        """The narrowing mechanism itself must be gone from the locked file,
        not merely unreachable."""
        raw = (ROOT / "schema" / "zmeta-event-1.0.schema.json").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("eventSubtypeConsistency", raw)


if __name__ == "__main__":
    unittest.main()
