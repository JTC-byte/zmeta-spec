"""The example conformance claims' release_hashes match the manifest beside them.

Nothing in the repository read `release_hashes` back before this file
existed, and that absence let stale values ship in every published
v1.1.22 bundle: the v1.1.22 cut rebuilt the manifest without refreshing
the claims, and the two prior verifications that said this could not
happen both passed for other reasons (the R1-11 refutation leaned on the
manifest's hash pin, which certifies integrity, not currency; doctrine
pressure log X2-01 records the chain, and `docs/release_claims_errata.md`
records the shipped values). The checklist's `--update-claims` step is
the human control; this test is the mechanical one.
"""

import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "release" / "zmeta-release-manifest.yaml"
CLAIMS = sorted((ROOT / "conformance" / "claims").glob("example-*.yaml"))

CIRCULARITY_SENTINEL = "omitted_to_avoid_claim_manifest_circularity"

# The exact key set every example claim must carry. A floor alone was blind
# to deletion (dropping three load-bearing hashes still cleared a
# ten-key floor, found by the pre-cut attack pass); an exact set makes a
# dropped or added key a named failure. Grows only deliberately, in the
# same commit as the claim-writer change that grows it.
EXPECTED_HASH_KEYS = frozenset(
    {
        "semantic_contract_hash",
        "schema_bundle_hash",
        "policy_bundle_hash",
        "extension_registry_hash",
        "conformance_class_manifest_hash",
        "profile_projection_catalog_hash",
        "encoding_negative_suite_hash",
        "profile_precision_policy_hash",
        "bad_event_corpus_hash",
        "adapter_conformance_hash",
        "encoding_projection_specs_hash",
        "process_governance_hash",
        "release_manifest_hash",
    }
)


def _manifest():
    return yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))


def _claim_hashes(path):
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    hashes = data.get("release_hashes")
    assert isinstance(hashes, dict) and hashes, f"{path.name} carries no release_hashes"
    return hashes


def _stale_entries(claim_hashes, manifest):
    """Every (key, claimed, manifest) triple where the claim disagrees."""
    stale = []
    for key, claimed in claim_hashes.items():
        if key == "release_manifest_hash":
            continue
        current = manifest.get(key)
        if claimed != current:
            stale.append((key, claimed, current))
    return stale


class ClaimsReleaseHashesCurrencyTest(unittest.TestCase):
    def test_the_inputs_exist_and_are_not_trivially_small(self):
        """Non-vacuity floor: an empty claim set or hash block proves nothing."""
        self.assertGreaterEqual(len(CLAIMS), 2, "the example claim pair went missing")

    def test_every_claim_carries_exactly_the_expected_key_set(self):
        """Deletion is drift too: a claim that quietly stops asserting the
        contract hash passes every equality check on the keys it kept."""
        for path in CLAIMS:
            self.assertEqual(
                set(_claim_hashes(path)), EXPECTED_HASH_KEYS,
                f"{path.name} release_hashes keys diverged from the expected "
                "set; if the claim writer changed deliberately, update "
                "EXPECTED_HASH_KEYS in the same commit",
            )

    def test_every_claimed_hash_matches_the_manifest_beside_it(self):
        manifest = _manifest()
        for path in CLAIMS:
            stale = _stale_entries(_claim_hashes(path), manifest)
            self.assertEqual(
                stale, [],
                f"{path.name} release_hashes disagree with the release manifest. "
                "The manifest is authoritative; rebuild it with --update-claims "
                "and commit the refreshed claims beside it (RELEASE_CHECKLIST.md). "
                f"Stale entries: {stale}",
            )

    def test_every_claimed_key_exists_in_the_manifest(self):
        """A renamed manifest key must not turn its claim entry into dead weight."""
        manifest = _manifest()
        for path in CLAIMS:
            for key in _claim_hashes(path):
                if key == "release_manifest_hash":
                    continue
                self.assertIn(
                    key, manifest,
                    f"{path.name} claims {key}, which the manifest does not define; "
                    "the comparison above silently skips nothing",
                )

    def test_the_manifest_hash_stays_omitted_for_circularity(self):
        """The one deliberate omission stays deliberate and labeled.

        The manifest hashes the claim files, so a claim carrying the real
        release_manifest_hash could never be committed consistently. The
        sentinel documents that; a real-looking hash here would be a claim
        that cannot be true.
        """
        for path in CLAIMS:
            self.assertEqual(
                _claim_hashes(path).get("release_manifest_hash"),
                CIRCULARITY_SENTINEL,
                f"{path.name} release_manifest_hash must stay the labeled omission",
            )

    def test_the_check_would_notice_a_stale_hash(self):
        """Mutation: the exact v1.1.22 state, demonstrated red in-memory."""
        manifest = _manifest()
        hashes = dict(_claim_hashes(CLAIMS[0]))
        target = next(k for k in hashes if k != "release_manifest_hash")
        hashes[target] = "sha256:" + "0" * 64
        stale = _stale_entries(hashes, manifest)
        self.assertEqual(
            [entry[0] for entry in stale], [target],
            "the doctored stale hash was not detected, so the gate is vacuous",
        )


if __name__ == "__main__":
    unittest.main()
