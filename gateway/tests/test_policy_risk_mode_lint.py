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


if __name__ == "__main__":
    unittest.main()
