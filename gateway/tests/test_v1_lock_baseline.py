"""The lock has one baseline, it is dated, and this file pins it.

Three acts, all on the record. Act one, 2026-08-02: the X1-02 gate inventory
ran the stronger form of the schema gate, found the v1.0 schema rejecting a
record from the v1.0.5 tag's own corpus, read that as a post-lock narrowing,
and a maintainer adjudication restored the free-form subtype. Act two, the
same wave's contract scout surfaced section 7.3 ("MUST match the payload
discriminator exactly"; "Producers MUST NOT use free-form subtypes") and
forensics dated it: the 2026-04-26 "Locked" stamp predated the real
hardening, and the 2026-05-07 lockdown audit (d19e33d) is the baseline every
subsequent verification descends from, older than all fielded adoption. Act
three, 2026-08-03: maintainer adjudication reversed the restoration. The
locked v1.0 is the lockdown-audit contract; the schema's subtype consistency
block is lawful enforcement of it; the v1.0.5-era RF_OBSERVATION record is a
pre-lock artifact, not protected data.

The lesson this file exists to keep: a lock without a dated birth
certificate invites baseline confusion, and both directions of that
confusion were expensive. The contract now carries its lock provenance note,
and the anchors below make moving either surface an on-record adjudication.
"""

import copy
import hashlib
import json
import unittest
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[2]

# Moving either anchor requires a maintainer adjudication on the record.
# Contract anchor moved 2026-08-03 under the A1-02 and ellipse-adoption
# adjudications: section 21.1 gains VERTICAL_UNAVAILABLE with the
# object-not-knowledge sentence, new section 21.8 defines declared geo
# dimensionality, and the section 21 preamble defers extension maturity to
# the registry. The locked v1.0 sections are untouched by that edit.
CONTRACT_SHA256 = "eb405618a2cbc1421f0947271f75a5b2716a9d7428d5ae9fe10c0963733048d4"
V1_0_SCHEMA_SHA256 = "1d2d84164b3a8986874e932c0e9369be3bf392a483a8ff261d464f34bd16d7b5"

# Embedded verbatim from the v1.0.5 tag's example corpus. Pre-lock history:
# written under the premature April stamp, superseded by the lockdown audit.
PRE_LOCK_RF_OBSERVATION = json.loads(
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


def _normalized_sha256(path):
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


class V1LockBaselineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema_v10 = json.loads(
            (ROOT / "schema" / "zmeta-event-1.0.schema.json").read_text(
                encoding="utf-8"
            )
        )
        cls.validator = jsonschema.Draft202012Validator(cls.schema_v10)

    def test_the_contract_text_is_anchored(self):
        """The lockdown-audit contract, plus its provenance note, is the
        lock. Any edit moves this hash and must arrive with an adjudication."""
        self.assertEqual(
            _normalized_sha256(ROOT / "spec" / "semantics-contract.md"),
            CONTRACT_SHA256,
        )

    def test_the_v10_schema_is_anchored_at_the_enforcing_bytes(self):
        self.assertEqual(
            _normalized_sha256(ROOT / "schema" / "zmeta-event-1.0.schema.json"),
            V1_0_SCHEMA_SHA256,
        )

    def test_the_subtype_consistency_block_is_present_as_contract_law(self):
        """Contract section 7.3 mandates the namespace and the discriminator
        match for v1.0; the schema block enforces it and stays."""
        self.assertIn(
            "eventSubtypeConsistency",
            json.dumps(self.schema_v10),
        )

    def test_the_pre_lock_record_stays_outside_the_lock(self):
        """The v1.0.5-era free-form subtype is pre-lock history. It must NOT
        validate: accepting it would mean the April stamp, not the lockdown
        audit, had quietly become the baseline again."""
        errors = list(self.validator.iter_errors(PRE_LOCK_RF_OBSERVATION))
        self.assertTrue(
            errors,
            "a pre-lockdown free-form subtype validated under v1.0 - the "
            "adjudicated baseline has come loose",
        )

    def test_the_lockdown_namespace_itself_validates(self):
        """Positive control: the same record, said the way the locked
        contract says it, is clean."""
        event = copy.deepcopy(PRE_LOCK_RF_OBSERVATION)
        event["event"]["event_subtype"] = "RF"
        errors = sorted(
            self.validator.iter_errors(event), key=lambda e: list(e.path)
        )
        self.assertFalse(errors, errors[0].message if errors else "")


if __name__ == "__main__":
    unittest.main()
