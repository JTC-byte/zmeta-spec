import copy
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VALIDATORS_PATH = ROOT / "gateway" / "src" / "validators.py"
spec = importlib.util.spec_from_file_location("zmeta_validators", VALIDATORS_PATH)
validators = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validators)


class PolicyRiskModeLintTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = validators.load_policy(ROOT / "policy")

    def test_reference_policy_ignore_modes_are_allowlisted(self):
        issues = validators.lint_policy_risk_modes(self.policy)

        self.assertEqual([], issues)

    def test_profile_l_unresolved_lineage_ignore_is_non_material_exception(self):
        policy = copy.deepcopy(self.policy)
        policy["lineage"]["unresolved_parent_mode"] = {
            "L": "ignore",
            "M": "warn",
            "H": "warn",
        }

        issues = validators.lint_policy_risk_modes(policy)

        self.assertEqual([], issues)

    def test_material_timing_ignore_is_flagged(self):
        policy = copy.deepcopy(self.policy)
        policy["timing_freshness"]["mode_by_profile"] = {
            "L": "ignore",
            "M": "reject",
            "H": "reject",
        }

        issues = validators.lint_policy_risk_modes(policy)

        self.assertEqual(1, len(issues))
        self.assertEqual("POLICY_IGNORE_MATERIAL_RISK", issues[0]["code"])
        self.assertEqual("timing_freshness.mode_by_profile.L", issues[0]["path"])
        self.assertIn("TIMING_STATUS_STALE", issues[0]["reason_codes"])
        self.assertIn("TIMING_STATUS_AGE_NEGATIVE", issues[0]["reason_codes"])

    def test_negative_age_timing_ignore_is_flagged(self):
        policy = copy.deepcopy(self.policy)
        policy["timing_freshness"]["negative_age_mode"] = "ignore"

        issues = validators.lint_policy_risk_modes(policy)

        self.assertEqual(1, len(issues))
        self.assertEqual("POLICY_IGNORE_MATERIAL_RISK", issues[0]["code"])
        self.assertEqual("timing_freshness.negative_age_mode", issues[0]["path"])
        self.assertEqual(["TIMING_STATUS_AGE_NEGATIVE"], issues[0]["reason_codes"])

    def test_material_lineage_ignore_is_flagged(self):
        policy = copy.deepcopy(self.policy)
        policy["lineage"]["parent_type_mismatch_mode"] = "ignore"

        issues = validators.lint_policy_risk_modes(policy)

        self.assertEqual(1, len(issues))
        self.assertEqual("lineage.parent_type_mismatch_mode", issues[0]["path"])
        self.assertEqual(["LINEAGE_PARENT_TYPE_INVALID"], issues[0]["reason_codes"])

    def test_external_promotion_ignore_is_flagged(self):
        policy = copy.deepcopy(self.policy)
        policy["producer_authority"]["external_state_promotion"]["mode"] = "ignore"

        issues = validators.lint_policy_risk_modes(policy)

        self.assertEqual(1, len(issues))
        self.assertEqual(
            "producer_authority.external_state_promotion.mode",
            issues[0]["path"],
        )
        self.assertEqual("external_promotion", issues[0]["risk_dimension"])


class ProducerAuthorityStructureLintTest(unittest.TestCase):
    """R1-11 R11-05: validate_producer_authority reads policy blocks with
    .get() defaults, so structural mangling (typoed keys, non-bool
    required) silently disables enforcement. The structural lint must
    catch those shapes; sub-block DELETION stays lint-legal (producers
    without promotion enforcement are legitimate) and is covered by the
    sapient bad-events corpus pair instead."""

    @classmethod
    def setUpClass(cls):
        cls.policy = validators.load_policy(ROOT / "policy")

    def lint(self, policy):
        return validators.lint_producer_authority_structure(policy)

    def test_shipped_policy_is_structurally_clean(self):
        self.assertEqual([], self.lint(self.policy))

    def test_typoed_promotion_subblock_key_fails_lint(self):
        policy = copy.deepcopy(self.policy)
        entry = policy["producer_authority"]["producers"]["sapient-ingress"]
        entry["extenal_state_promotion"] = entry.pop("external_state_promotion")

        issues = self.lint(policy)

        self.assertTrue(issues)
        self.assertEqual("POLICY_PRODUCER_AUTHORITY_STRUCTURE", issues[0]["code"])
        self.assertIn("extenal_state_promotion", issues[0]["path"])

    def test_unknown_promotion_rule_key_fails_lint(self):
        policy = copy.deepcopy(self.policy)
        promotion = policy["producer_authority"]["producers"]["sapient-ingress"][
            "external_state_promotion"
        ]
        promotion["aproved_policy_ids"] = promotion.pop("approved_policy_ids")

        issues = self.lint(policy)

        self.assertTrue(any("aproved_policy_ids" in issue["path"] for issue in issues))

    def test_non_bool_required_fails_lint(self):
        policy = copy.deepcopy(self.policy)
        policy["producer_authority"]["producers"]["sapient-ingress"][
            "external_state_promotion"
        ]["required"] = "true"

        issues = self.lint(policy)

        self.assertTrue(any(issue["path"].endswith(".required") for issue in issues))

    def test_unknown_top_level_authority_key_fails_lint(self):
        policy = copy.deepcopy(self.policy)
        policy["producer_authority"]["producres"] = {}

        issues = self.lint(policy)

        self.assertTrue(any("producres" in issue["path"] for issue in issues))

    def test_legitimate_mode_override_stays_clean(self):
        # test_producer_rule_can_override_global_promotion_mode relies on a
        # producer-level mode override; the structural lint must not flag it.
        policy = copy.deepcopy(self.policy)
        policy["producer_authority"]["producers"]["sapient-ingress"][
            "external_state_promotion"
        ]["mode"] = "warn"

        self.assertEqual([], self.lint(policy))


if __name__ == "__main__":
    unittest.main()
