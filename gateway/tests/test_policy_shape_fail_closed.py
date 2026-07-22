"""R1-11 A-05 / A-07: producer-authority policy VALUE-SHAPE hardening.

Two independent halves, both required:

* deployment time — ``lint_producer_authority_structure`` /
  ``lint_routing_producer_enforcement_structure`` must fail on a
  present-but-wrong-typed value for every key the enforcement reads, not just
  on a typoed key NAME. Before this pin, a wrong-typed value linted green
  while it silently reverted the gate to "no constraint";
* runtime — the two require-match gates must FAIL CLOSED on a malformed
  value. An operator who never runs the lint must still be safe, and the
  refusal must name the policy defect rather than raising ``TypeError`` into
  the receive-loop backstop (which reports ``INTERNAL_ERROR`` and names no
  policy problem at all).

The completeness of the shape tables is pinned against the ENFORCEMENT SOURCE
via an AST scan, not against the lint's own key-name constants: a table
compared only to a sibling constant in the same module is blind to a key both
of them missed.

The three levels a key-by-key check structurally cannot reach are pinned
separately, because the first round of this fix closed the keys and left all
three open (R1-11 A-05 residuals a-d):

* the CONTAINER — the block that holds the keys is subject to the same
  bare-key mangle as the keys, and the guard skipped over it in silence;
* the ENTRY VOCABULARY — a well-formed string that is not an event type
  (`STATE_EVEN`) drops out of a gate exactly as silently as a non-string
  entry, and was unchecked;
* the DOCUMENT — `load_policy` unwraps `routing.yaml` with
  `.get("routing", {})`, so a misspelled wrapper key becomes the permissive
  default before any in-memory lint can see it.
"""

import ast
import copy
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VALIDATORS_PATH = ROOT / "gateway" / "src" / "validators.py"
spec = importlib.util.spec_from_file_location("zmeta_validators", VALIDATORS_PATH)
validators = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validators)


def state_event(producer, event_type="STATE_EVENT", event_subtype="TRACK_STATE"):
    return {
        "event": {
            "event_id": "01J0000000000000000000000A",
            "event_type": event_type,
            "event_subtype": event_subtype,
            "ts": "2026-07-21T00:00:00Z",
            "schema_version": "1.0",
        },
        "source": {
            "platform_id": "test-platform",
            "node_role": "GATEWAY",
            "producer": producer,
        },
        "payload": {},
        "lineage": {},
    }


# Every mangle below is one YAML line away from the shipped policy.
MALFORMED_VALUES = (
    ("bare key (YAML null)", None),
    ("scalar string", "STATE_EVENT"),
    ("scalar int", 6),
    ("mapping", {"STATE_EVENT": True}),
    ("bool", True),
)


class RequireMatchFailsClosedTest(unittest.TestCase):
    """A-05: the producer-authority require-match backstop."""

    @classmethod
    def setUpClass(cls):
        cls.policy = validators.load_policy(ROOT / "policy")
        cls.severity_map = cls.policy["violation_severities"]

    def authority(self, value=..., drop=False):
        authority = copy.deepcopy(self.policy["producer_authority"])
        if drop:
            authority.pop("require_match_for_event_types")
        elif value is not ...:
            authority["require_match_for_event_types"] = value
        return authority

    def test_shipped_policy_refuses_unregistered_producer(self):
        ok, violations = validators.validate_producer_authority(
            state_event("totally-unregistered-node"), self.authority(), self.severity_map
        )
        self.assertFalse(ok)
        self.assertEqual("PRODUCER_NOT_ALLOWED", violations[0]["code"])
        self.assertNotIn("policy_error", violations[0]["details"])

    def test_malformed_require_match_refuses_unregistered_producer(self):
        # Neither a crash nor an accept: an unregistered producer stays
        # refused on EVERY event type, and the diagnostic names the defect.
        for label, value in MALFORMED_VALUES:
            for event_type in (
                "OBSERVATION_EVENT",
                "INFERENCE_EVENT",
                "FUSION_EVENT",
                "STATE_EVENT",
                "COMMAND_EVENT",
                "SYSTEM_EVENT",
            ):
                with self.subTest(shape=label, event_type=event_type):
                    ok, violations = validators.validate_producer_authority(
                        state_event("totally-unregistered-node", event_type),
                        self.authority(value),
                        self.severity_map,
                    )
                    self.assertFalse(ok, f"{label} admitted an unregistered producer")
                    self.assertEqual("PRODUCER_NOT_ALLOWED", violations[0]["code"])
                    self.assertIn("policy_error", violations[0]["details"])
                    self.assertIn(
                        "require_match_for_event_types",
                        violations[0]["details"]["policy_error"],
                    )

    def test_malformed_require_match_does_not_punish_registered_producers(self):
        # Fail-closed applies to the control's own scope. A producer that
        # matches a rule is still adjudicated by that rule, so a mangled
        # backstop is not a 100% outage in the other direction either.
        for label, value in MALFORMED_VALUES:
            with self.subTest(shape=label):
                ok, violations = validators.validate_producer_authority(
                    state_event("rf-sensor", "OBSERVATION_EVENT", "RF"),
                    self.authority(value),
                    self.severity_map,
                )
                self.assertTrue(ok, violations)

    def test_trailing_colon_list_entry_fails_closed(self):
        # "  - STATE_EVENT:" is a well-formed LIST whose entry is a mapping.
        # The shape of the key is right; the shape of the item is not, and
        # str()-coercing it produces a token no event type can ever equal.
        mangled = [
            "OBSERVATION_EVENT",
            {"STATE_EVENT": None},
            "COMMAND_EVENT",
        ]
        ok, violations = validators.validate_producer_authority(
            state_event("totally-unregistered-node", "STATE_EVENT"),
            self.authority(mangled),
            self.severity_map,
        )
        self.assertFalse(ok)
        self.assertIn("policy_error", violations[0]["details"])

    def test_absent_require_match_stays_permissive(self):
        # Omitting the key is the documented "no require-match" deployment.
        # Absence must NOT be read as malformed.
        ok, violations = validators.validate_producer_authority(
            state_event("totally-unregistered-node"),
            self.authority(drop=True),
            self.severity_map,
        )
        self.assertTrue(ok, violations)

    def test_empty_require_match_list_stays_permissive(self):
        ok, violations = validators.validate_producer_authority(
            state_event("totally-unregistered-node"),
            self.authority([]),
            self.severity_map,
        )
        self.assertTrue(ok, violations)


class RoutingAllowlistFailsClosedTest(unittest.TestCase):
    """A-05 class: the routing COMMAND_EVENT allowlist gate, same defect."""

    @classmethod
    def setUpClass(cls):
        cls.policy = validators.load_policy(ROOT / "policy")
        cls.severity_map = cls.policy["violation_severities"]

    def routing(self, value=..., drop=False):
        routing = copy.deepcopy(self.policy["routing"])
        if drop:
            routing["producer_enforcement"].pop("require_allowlist_for_event_types")
        elif value is not ...:
            routing["producer_enforcement"]["require_allowlist_for_event_types"] = value
        return routing

    def test_malformed_allowlist_refuses_unlisted_producer(self):
        for label, value in MALFORMED_VALUES:
            with self.subTest(shape=label):
                ok, violations = validators.validate_routing(
                    state_event("totally-unregistered-node", "COMMAND_EVENT", "TASK_REQUEST"),
                    self.routing(value),
                    self.severity_map,
                )
                self.assertFalse(ok, f"{label} admitted an unlisted COMMAND_EVENT producer")
                self.assertEqual("PRODUCER_NOT_ALLOWED", violations[0]["code"])
                self.assertIn("policy_error", violations[0]["details"])

    def test_malformed_producer_enforcement_block_fails_closed(self):
        # The block HOLDING the allowlist, not just the key. Before the fix
        # this raised AttributeError; the fix must not be quieter than the
        # crash it replaces.
        for bad in (None, "COMMAND_EVENT", 7, ["COMMAND_EVENT"]):
            with self.subTest(shape=repr(bad)):
                routing = copy.deepcopy(self.policy["routing"])
                routing["producer_enforcement"] = bad
                ok, violations = validators.validate_routing(
                    state_event("totally-unregistered-node", "COMMAND_EVENT", "TASK_REQUEST"),
                    routing,
                    self.severity_map,
                )
                self.assertFalse(ok)
                self.assertIn("policy_error", violations[0]["details"])

    def test_malformed_producer_enforcement_block_is_linted(self):
        for bad in (None, "COMMAND_EVENT", 7, ["COMMAND_EVENT"]):
            with self.subTest(shape=repr(bad)):
                policy = copy.deepcopy(self.policy)
                policy["routing"]["producer_enforcement"] = bad
                paths = [
                    issue["path"]
                    for issue in validators.lint_routing_producer_enforcement_structure(policy)
                ]
                self.assertIn("routing.producer_enforcement", paths)

    def test_absent_allowlist_key_stays_permissive(self):
        ok, violations = validators.validate_routing(
            state_event("sensorops", "COMMAND_EVENT", "TASK_REQUEST"),
            self.routing(drop=True),
            self.severity_map,
        )
        self.assertTrue(ok, violations)

    def test_shipped_routing_still_admits_its_command_producer(self):
        ok, violations = validators.validate_routing(
            state_event("sensorops", "COMMAND_EVENT", "TASK_REQUEST"),
            self.routing(),
            self.severity_map,
        )
        self.assertTrue(ok, violations)


class PolicyShapeLintTest(unittest.TestCase):
    """A-05 + A-07: the deployment-time half, over the WHOLE key set."""

    @classmethod
    def setUpClass(cls):
        cls.policy = validators.load_policy(ROOT / "policy")
        cls.severity_map = cls.policy["violation_severities"]

    def lint(self, policy):
        return validators.lint_producer_authority_structure(
            policy
        ) + validators.lint_routing_producer_enforcement_structure(policy)

    def test_shipped_policy_is_shape_clean(self):
        self.assertEqual([], self.lint(self.policy))

    def test_strict_variant_is_shape_clean(self):
        # configs/policy-variants/producer-authority.strict.yaml is a
        # legitimate deployment shape with NO external_state_promotion block.
        import yaml

        variant = yaml.safe_load(
            (ROOT / "configs" / "policy-variants" / "producer-authority.strict.yaml").read_text(
                encoding="utf-8"
            )
        )
        policy = copy.deepcopy(self.policy)
        policy["producer_authority"] = variant["producer_authority"]
        self.assertEqual([], self.lint(policy))

    def _wrong_values(self, shape_label):
        return {
            "list": (None, "SOME_VALUE", 7, {"a": 1}, True),
            "mapping": (None, "SOME_VALUE", 7, ["a"], True),
            "string": (None, 7, ["a"], {"a": 1}, True),
            "boolean": (None, "true", 7, ["a"], {"a": 1}),
            "number": (None, "SOME_VALUE", ["a"], {"a": 1}, True),
        }[shape_label]

    VALID_SAMPLE = {
        "list": ["SOME_VALUE"],
        "mapping": {},
        "string": "reject",
        "boolean": True,
        "number": 1,
    }

    def test_allowed_event_subtypes_is_legal_policy_the_lint_accepts(self):
        """R1-11 A-15: the lint must not fail a control that is IN FORCE.

        ``validate_producer_authority`` reads ``allowed_event_subtypes`` and
        refuses on it. The producer-entry name lint reported that key as
        "unknown ... a typo here silently disables enforcement", so the
        remedy it prescribed — delete the key — would have removed a subtype
        restriction that was actually working, turning a correct
        configuration into a weaker one.

        Both halves are asserted together, because either alone can pass
        while the pair is incoherent.
        """
        policy = copy.deepcopy(self.policy)
        policy["producer_authority"]["producers"]["rf-sensor"][
            "allowed_event_subtypes"
        ] = ["RF"]

        self.assertEqual(
            [],
            validators.lint_producer_authority_structure(policy),
            "the lint failed a policy whose control the enforcement honours",
        )

        allowed = state_event("rf-sensor", "OBSERVATION_EVENT", "RF")
        ok, violations = validators.validate_producer_authority(
            allowed, policy["producer_authority"], self.severity_map
        )
        self.assertTrue(ok, violations)

        refused = state_event("rf-sensor", "OBSERVATION_EVENT", "OTHER_SUBTYPE")
        ok, violations = validators.validate_producer_authority(
            refused, policy["producer_authority"], self.severity_map
        )
        self.assertFalse(ok, "the key the lint called a typo is not enforced")
        self.assertEqual(
            "event_subtype not authorized for producer", violations[0]["message"]
        )

        # ...and a wrong-typed value for it is still reported, so accepting
        # the key did not buy silence on the shape.
        policy["producer_authority"]["producers"]["rf-sensor"][
            "allowed_event_subtypes"
        ] = 7
        self.assertIn(
            "producer_authority.producers.rf-sensor.allowed_event_subtypes",
            [issue["path"] for issue in validators.lint_producer_authority_structure(policy)],
        )

    def test_every_global_promotion_key_shape_is_linted(self):
        for key, (label, _types) in validators._GLOBAL_PROMOTION_SHAPES.items():
            for bad in self._wrong_values(label):
                with self.subTest(key=key, bad=repr(bad)):
                    policy = copy.deepcopy(self.policy)
                    policy["producer_authority"]["external_state_promotion"][key] = bad
                    paths = [issue["path"] for issue in self.lint(policy)]
                    self.assertIn(
                        f"producer_authority.external_state_promotion.{key}", paths
                    )

    def test_every_top_level_authority_key_shape_is_linted(self):
        for key, (label, _types) in validators._PRODUCER_AUTHORITY_TOP_SHAPES.items():
            for bad in self._wrong_values(label):
                with self.subTest(key=key, bad=repr(bad)):
                    policy = copy.deepcopy(self.policy)
                    policy["producer_authority"][key] = bad
                    paths = [issue["path"] for issue in self.lint(policy)]
                    self.assertIn(f"producer_authority.{key}", paths)

    def test_every_producer_entry_key_shape_is_linted(self):
        for key, (label, _types) in validators._PRODUCER_ENTRY_SHAPES.items():
            for bad in self._wrong_values(label):
                with self.subTest(key=key, bad=repr(bad)):
                    policy = copy.deepcopy(self.policy)
                    policy["producer_authority"]["producers"]["cot-ingress"][key] = bad
                    paths = [issue["path"] for issue in self.lint(policy)]
                    self.assertIn(
                        f"producer_authority.producers.cot-ingress.{key}", paths
                    )

    def test_every_promotion_rule_key_shape_is_linted(self):
        for key, (label, _types) in validators._PROMOTION_RULE_SHAPES.items():
            for bad in self._wrong_values(label):
                with self.subTest(key=key, bad=repr(bad)):
                    policy = copy.deepcopy(self.policy)
                    policy["producer_authority"]["producers"]["cot-ingress"][
                        "external_state_promotion"
                    ][key] = bad
                    paths = [issue["path"] for issue in self.lint(policy)]
                    self.assertIn(
                        "producer_authority.producers.cot-ingress."
                        f"external_state_promotion.{key}",
                        paths,
                    )

    def test_routing_allowlist_shape_is_linted(self):
        for bad in self._wrong_values("list"):
            with self.subTest(bad=repr(bad)):
                policy = copy.deepcopy(self.policy)
                policy["routing"]["producer_enforcement"][
                    "require_allowlist_for_event_types"
                ] = bad
                paths = [issue["path"] for issue in self.lint(policy)]
                self.assertIn(
                    "routing.producer_enforcement.require_allowlist_for_event_types",
                    paths,
                )

    def test_non_string_list_entries_are_linted(self):
        # Same trailing-colon mangle, deployment-time half, for every
        # list-shaped key in every producer-authority block.
        bad_entry = {"SOME_VALUE": None}
        for key, (label, _types) in validators._GLOBAL_PROMOTION_SHAPES.items():
            if label != "list":
                continue
            with self.subTest(key=key):
                policy = copy.deepcopy(self.policy)
                policy["producer_authority"]["external_state_promotion"][key] = [
                    "SOME_VALUE",
                    bad_entry,
                ]
                paths = [issue["path"] for issue in self.lint(policy)]
                self.assertIn(
                    f"producer_authority.external_state_promotion.{key}", paths
                )
        for block, key in (
            ("producer_authority", "require_match_for_event_types"),
            ("routing", "require_allowlist_for_event_types"),
        ):
            with self.subTest(key=key):
                policy = copy.deepcopy(self.policy)
                if block == "producer_authority":
                    policy[block][key] = ["STATE_EVENT", bad_entry]
                    expected = f"producer_authority.{key}"
                else:
                    policy[block]["producer_enforcement"][key] = [
                        "COMMAND_EVENT",
                        bad_entry,
                    ]
                    expected = f"routing.producer_enforcement.{key}"
                self.assertIn(expected, [issue["path"] for issue in self.lint(policy)])

    def test_by_profile_sub_key_shapes_are_linted(self):
        # Deleting the items under "L:" leaves a bare sub-key -> None, which
        # _list_values reads as [] and the freshness bound reads as "no
        # bound". Same A-05 mangle, one level down, same green light.
        for key, (label, _types) in validators._GLOBAL_PROMOTION_VALUE_SHAPES.items():
            for bad in self._wrong_values(label):
                with self.subTest(key=key, bad=repr(bad)):
                    policy = copy.deepcopy(self.policy)
                    promotion = policy["producer_authority"]["external_state_promotion"]
                    # mode_by_profile is optional and absent from the shipped
                    # policy; probe it in its legitimate configured form.
                    block = promotion.setdefault(key, {"H": self.VALID_SAMPLE[label]})
                    sub_key = sorted(block, key=str)[0]
                    block[sub_key] = bad
                    paths = [issue["path"] for issue in self.lint(policy)]
                    self.assertIn(
                        f"producer_authority.external_state_promotion.{key}.{sub_key}",
                        paths,
                    )

    def test_use_limit_entry_shapes_are_linted(self):
        for key in validators._PROMOTION_USE_LIMIT_ENTRY_SHAPES:
            for bad in self._wrong_values("list"):
                with self.subTest(key=key, bad=repr(bad)):
                    policy = copy.deepcopy(self.policy)
                    policy["producer_authority"]["external_state_promotion"][
                        "use_limits"
                    ]["warn"][key] = bad
                    paths = [issue["path"] for issue in self.lint(policy)]
                    self.assertIn(
                        "producer_authority.external_state_promotion."
                        f"use_limits.warn.{key}",
                        paths,
                    )

    def test_non_finite_numeric_bound_is_linted(self):
        # YAML .nan / .inf are legal floats, so the type check alone passes
        # them. A NaN bound compares false against every freshness value,
        # which disables the bound while leaving the key visibly configured.
        for bad in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(bad=repr(bad)):
                policy = copy.deepcopy(self.policy)
                policy["producer_authority"]["external_state_promotion"][
                    "max_freshness_ms_by_profile"
                ]["H"] = bad
                paths = [issue["path"] for issue in self.lint(policy)]
                self.assertIn(
                    "producer_authority.external_state_promotion."
                    "max_freshness_ms_by_profile.H",
                    paths,
                )

    def test_legal_shapes_stay_green(self):
        # Design-legal configurations the lint must never flag. Omitting a key
        # and required_fields_by_profile: {} are pinned as legal in
        # test_policy_risk_mode_lint.py; an empty list is the same class.
        promotion_keys = list(validators._GLOBAL_PROMOTION_SHAPES)
        for key in promotion_keys:
            with self.subTest(omitted=key):
                policy = copy.deepcopy(self.policy)
                policy["producer_authority"]["external_state_promotion"].pop(key, None)
                self.assertEqual([], self.lint(policy))
        empties = {
            "required_fields_by_profile": {},
            "allowed_lineage_status_by_profile": {},
            "max_freshness_ms_by_profile": {},
            "allowed_origin_kinds": [],
            "loop_risk_statuses": [],
        }
        for key, empty in empties.items():
            with self.subTest(empty=key):
                policy = copy.deepcopy(self.policy)
                policy["producer_authority"]["external_state_promotion"][key] = empty
                self.assertEqual([], self.lint(policy))
        policy = copy.deepcopy(self.policy)
        policy["producer_authority"]["require_match_for_event_types"] = []
        self.assertEqual([], self.lint(policy))
        policy = copy.deepcopy(self.policy)
        policy["producer_authority"].pop("require_match_for_event_types")
        self.assertEqual([], self.lint(policy))
        policy = copy.deepcopy(self.policy)
        policy["routing"].pop("producer_enforcement")
        self.assertEqual([], self.lint(policy))


class ShippedLintCliTest(unittest.TestCase):
    """The lint an operator actually runs must carry both checks.

    The tests above call the lint functions directly; that proves the
    functions work and proves nothing about whether
    tools/lint_policy_risk_modes.py still calls them. A deployment-time
    control that is not wired into the deployment-time command is not a
    control.
    """

    LINT = ROOT / "tools" / "lint_policy_risk_modes.py"

    def run_cli(self, mutate=None):
        import shutil
        import subprocess
        import sys
        import tempfile

        import yaml

        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "policy"
            shutil.copytree(ROOT / "policy", dest)
            if mutate is not None:
                section, body = mutate(validators.load_policy(dest))
                (dest / f"{section.replace('_', '-')}.yaml").write_text(
                    yaml.safe_dump({section: body}, sort_keys=False), encoding="utf-8"
                )
            proc = subprocess.run(
                [sys.executable, str(self.LINT), "--policy-dir", str(dest)],
                capture_output=True,
                text=True,
            )
        return proc.returncode, proc.stdout

    def test_shipped_policy_passes_the_cli(self):
        code, out = self.run_cli()
        self.assertEqual(0, code, out)
        self.assertIn("ok", out)

    def test_cli_fails_on_mangled_require_match(self):
        def mutate(policy):
            policy["producer_authority"]["require_match_for_event_types"] = "STATE_EVENT"
            return "producer_authority", policy["producer_authority"]

        code, out = self.run_cli(mutate)
        self.assertEqual(1, code, out)
        self.assertIn("require_match_for_event_types", out)

    def test_cli_fails_on_mangled_routing_allowlist(self):
        def mutate(policy):
            policy["routing"]["producer_enforcement"][
                "require_allowlist_for_event_types"
            ] = None
            return "routing", policy["routing"]

        code, out = self.run_cli(mutate)
        self.assertEqual(1, code, out)
        self.assertIn("require_allowlist_for_event_types", out)

    def test_cli_fails_on_flattened_required_fields(self):
        def mutate(policy):
            promotion = policy["producer_authority"]["external_state_promotion"]
            promotion["required_fields_by_profile"] = ["state_category", "trust_ref"]
            return "producer_authority", policy["producer_authority"]

        code, out = self.run_cli(mutate)
        self.assertEqual(1, code, out)
        self.assertIn("required_fields_by_profile", out)


class ShapeTableCompletenessTest(unittest.TestCase):
    """The guard's own blind spot: does the table cover what enforcement reads?

    Comparing the shape tables to ``_GLOBAL_PROMOTION_KEYS`` and friends only
    proves two constants agree. This reads the ENFORCEMENT SOURCE instead and
    asserts that every policy key it pulls out of a producer-authority or
    routing block has a declared shape.
    """

    # Enforcement functions, and the local name each policy block is bound to.
    SCOPES = {
        "validate_producer_authority": {
            "authority_policy": "_PRODUCER_AUTHORITY_TOP_SHAPES",
            "rule": "_PRODUCER_ENTRY_SHAPES",
        },
        "validate_routing": {
            "enforcement": "_ROUTING_PRODUCER_ENFORCEMENT_SHAPES",
            "routing_policy": "_ROUTING_TOP_SHAPES",
            "rule": "_ROUTING_PRODUCER_ENTRY_SHAPES",
        },
        "_is_comms_producer": {
            "routing_policy": "_ROUTING_TOP_SHAPES",
            "cmd_cfg": "_ROUTING_COMMAND_EVENT_SHAPES",
        },
        "_validate_external_state_promotion": {
            "authority_policy": "_PRODUCER_AUTHORITY_TOP_SHAPES",
            "global_cfg": "_GLOBAL_PROMOTION_SHAPES",
        },
        "apply_external_promotion_policy_action": {
            "authority_policy": "_PRODUCER_AUTHORITY_TOP_SHAPES",
            "global_cfg": "_GLOBAL_PROMOTION_SHAPES",
        },
        "_promotion_mode": {
            "global_cfg": "_GLOBAL_PROMOTION_SHAPES",
            "cfg": "_PROMOTION_RULE_SHAPES",
        },
        "_external_promotion_rules": {
            "cfg": "_PROMOTION_RULE_SHAPES",
            "rule": "_PRODUCER_ENTRY_SHAPES",
        },
        # _risk_use_limits binds the global promotion block to a local named
        # `policy`; without this scope the scan would not see use_limits at
        # all and the equality assertion below would be vacuously weaker.
        "_risk_use_limits": {
            "policy": "_GLOBAL_PROMOTION_SHAPES",
        },
    }
    # Keys reached through a helper call rather than an attribute access.
    # The A-05 fix itself moved require_match_for_event_types behind
    # _require_match_types, which would have made this scan blind to the very
    # key it was written for.
    HELPER_READS = {"_require_match_types"}
    # Read by enforcement, deliberately NOT given a declared shape here.
    #
    # EMPTY, and it must stay empty unless a maintainer decides otherwise:
    # every key the enforcement reads now has a declared shape. R1-11 A-15
    # (`allowed_event_subtypes`, read and ENFORCED by
    # validate_producer_authority while the name lint called it a typo that
    # "silently disables enforcement") was the only entry, and it is fixed —
    # so the exclusion is retired rather than left to rot into a blanket
    # excuse. An entry added here suppresses a real drift signal, so
    # test_no_silent_exclusions below forces it to be justified.
    KNOWN_UNDECLARED = frozenset()

    @staticmethod
    def _loop_constants(function_node):
        """Map a loop variable to the constant strings it iterates.

        ``_is_comms_producer`` reads its three keys as
        ``for key in ("a", "b", "c"): cmd_cfg.get(key)``. A scan that only
        understands ``cfg.get("literal")`` sees nothing there, which would
        leave the command_event table unpinned in exactly the direction this
        test exists to check.
        """
        bindings = {}
        for sub in ast.walk(function_node):
            if not isinstance(sub, ast.For) or not isinstance(sub.target, ast.Name):
                continue
            if not isinstance(sub.iter, (ast.Tuple, ast.List, ast.Set)):
                continue
            values = [
                element.value
                for element in sub.iter.elts
                if isinstance(element, ast.Constant) and isinstance(element.value, str)
            ]
            if values:
                bindings.setdefault(sub.target.id, set()).update(values)
        return bindings

    def test_every_enforcement_read_has_a_declared_shape(self):
        tree = ast.parse(VALIDATORS_PATH.read_text(encoding="utf-8"))
        found = set()
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef) or node.name not in self.SCOPES:
                continue
            scope = self.SCOPES[node.name]
            loop_constants = self._loop_constants(node)
            for sub in ast.walk(node):
                if not isinstance(sub, ast.Call):
                    continue
                func = sub.func
                if (
                    isinstance(func, ast.Attribute)
                    and func.attr == "get"
                    and isinstance(func.value, ast.Name)
                    and func.value.id in scope
                    and sub.args
                    and isinstance(sub.args[0], ast.Constant)
                    and isinstance(sub.args[0].value, str)
                ):
                    found.add((scope[func.value.id], sub.args[0].value))
                # cfg.get(key) where `key` iterates a tuple of literals.
                if (
                    isinstance(func, ast.Attribute)
                    and func.attr == "get"
                    and isinstance(func.value, ast.Name)
                    and func.value.id in scope
                    and sub.args
                    and isinstance(sub.args[0], ast.Name)
                    and sub.args[0].id in loop_constants
                ):
                    for key in loop_constants[sub.args[0].id]:
                        found.add((scope[func.value.id], key))
                # _union_rule_values(promotion_rules, "<key>") reads a
                # per-rule promotion key without an attribute access.
                if (
                    isinstance(func, ast.Name)
                    and func.id == "_union_rule_values"
                    and len(sub.args) == 2
                    and isinstance(sub.args[1], ast.Constant)
                ):
                    found.add(("_PROMOTION_RULE_SHAPES", sub.args[1].value))
                # _require_match_types(<block>, "<key>", ...)
                if (
                    isinstance(func, ast.Name)
                    and func.id in self.HELPER_READS
                    and len(sub.args) >= 2
                    and isinstance(sub.args[0], ast.Name)
                    and sub.args[0].id in scope
                    and isinstance(sub.args[1], ast.Constant)
                ):
                    found.add((scope[sub.args[0].id], sub.args[1].value))

        self.assertTrue(found, "AST scan found no enforcement policy reads")
        missing = set()
        for table_name, key in sorted(found):
            if (table_name, key) in self.KNOWN_UNDECLARED:
                continue
            if key not in getattr(validators, table_name):
                missing.add(f"{table_name}[{key}]")
        self.assertEqual(
            set(),
            missing,
            "enforcement reads policy keys with no declared shape: "
            f"{sorted(missing)}",
        )

        # The other direction: a declared shape for a key nothing reads is a
        # table that has drifted away from the enforcement it describes.
        for table_name in (
            "_PRODUCER_AUTHORITY_TOP_SHAPES",
            "_GLOBAL_PROMOTION_SHAPES",
            "_PRODUCER_ENTRY_SHAPES",
            "_PROMOTION_RULE_SHAPES",
            "_ROUTING_PRODUCER_ENFORCEMENT_SHAPES",
            "_ROUTING_TOP_SHAPES",
            "_ROUTING_PRODUCER_ENTRY_SHAPES",
            "_ROUTING_COMMAND_EVENT_SHAPES",
        ):
            with self.subTest(table=table_name):
                scanned = {key for table, key in found if table == table_name}
                declared = set(getattr(validators, table_name))
                self.assertEqual(
                    declared,
                    scanned - {key for table, key in self.KNOWN_UNDECLARED if table == table_name},
                    f"{table_name} and the enforcement source disagree",
                )

    def test_no_silent_exclusions(self):
        # The exclusion set suppresses the drift signal the scan above
        # exists to raise, so it may not grow quietly. Empty is the pinned
        # state; any future entry has to name a key the enforcement really
        # reads AND really lacks a shape, or this fails.
        tree = ast.parse(VALIDATORS_PATH.read_text(encoding="utf-8"))
        source_keys = {
            sub.args[0].value
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and node.name == "validate_producer_authority"
            for sub in ast.walk(node)
            if isinstance(sub, ast.Call)
            and isinstance(sub.func, ast.Attribute)
            and sub.func.attr == "get"
            and isinstance(sub.func.value, ast.Name)
            and sub.func.value.id == "rule"
            and sub.args
            and isinstance(sub.args[0], ast.Constant)
        }
        self.assertEqual(
            frozenset(),
            frozenset(self.KNOWN_UNDECLARED),
            "an enforcement-read key was excluded from the shape tables; "
            "justify it here or declare the shape",
        )
        for table_name, key in self.KNOWN_UNDECLARED:  # pragma: no cover
            with self.subTest(key=key):
                self.assertIn(key, source_keys)
                self.assertNotIn(key, getattr(validators, table_name))

    def test_shape_tables_and_name_vocabularies_agree(self):
        pairs = (
            (validators._PRODUCER_AUTHORITY_TOP_SHAPES, validators._PRODUCER_AUTHORITY_TOP_KEYS),
            (validators._GLOBAL_PROMOTION_SHAPES, validators._GLOBAL_PROMOTION_KEYS),
            (validators._PRODUCER_ENTRY_SHAPES, validators._PRODUCER_ENTRY_KEYS),
            (validators._PROMOTION_RULE_SHAPES, validators._PROMOTION_RULE_KEYS),
            (validators._ROUTING_TOP_SHAPES, validators._ROUTING_TOP_KEYS),
            (
                validators._ROUTING_PRODUCER_ENTRY_SHAPES,
                validators._ROUTING_PRODUCER_ENTRY_KEYS,
            ),
            (
                validators._ROUTING_COMMAND_EVENT_SHAPES,
                validators._ROUTING_COMMAND_EVENT_KEYS,
            ),
        )
        for shapes, names in pairs:
            with self.subTest(names=sorted(names)[:2]):
                self.assertEqual(set(names), set(shapes))


WRONG_FOR_MAPPING = (None, "SOME_VALUE", 7, ["a"], True)


class PolicyContainerFailsClosedTest(unittest.TestCase):
    """R1-11 A-05 residuals a/b/d: the CONTAINER, not only the keys in it.

    The key-level guards were written for the bare-key / wrong-type mangle,
    then applied only INSIDE the block that holds the keys. Measured before
    this pin, each mangle below produced ``policy risk mode lint ok`` and
    exit 0, and at runtime either raised ``AttributeError`` on every event
    (reported by the receive-loop backstop as ``INTERNAL_ERROR``, naming no
    policy problem) or switched its gate off in silence.

    The assertion is deliberately the strongest available: a block that has
    been destroyed cannot AUTHORIZE anything it holds. Each probe uses a
    producer the shipped policy admits, so a fail-open shows up as a pass.
    """

    @classmethod
    def setUpClass(cls):
        cls.policy = validators.load_policy(ROOT / "policy")
        cls.severity_map = cls.policy["violation_severities"]

    def lint(self, policy):
        return validators.lint_producer_authority_structure(
            policy
        ) + validators.lint_routing_producer_enforcement_structure(policy)

    def authority_probe(self, policy, event):
        return validators.validate_producer_authority(
            event, policy["producer_authority"], self.severity_map
        )

    def routing_probe(self, policy, event):
        return validators.validate_routing(
            event, policy["routing"], self.severity_map
        )

    def assert_shipped_admits(self, event, probe):
        ok, violations = probe(self.policy, event)
        self.assertTrue(ok, f"probe is useless unless the shipped policy admits it: {violations}")

    def check_container(self, mutate, lint_path, probe, event):
        # The probe must be one the shipped policy lets through, or "refused"
        # proves nothing about the mangle.
        self.assert_shipped_admits(event, probe)
        for bad in WRONG_FOR_MAPPING:
            with self.subTest(bad=repr(bad)):
                policy = copy.deepcopy(self.policy)
                mutate(policy, bad)
                paths = [issue["path"] for issue in self.lint(policy)]
                self.assertIn(lint_path, paths, f"lint stayed silent on {lint_path}={bad!r}")
                # Must not raise: an AttributeError into the backstop is not a
                # diagnostic, and must not admit: this block is destroyed.
                ok, violations = probe(policy, event)
                self.assertFalse(ok, f"{lint_path}={bad!r} still authorized the event")
                self.assertIn(
                    "policy_error",
                    violations[0]["details"],
                    "a refusal caused by broken policy must name the policy",
                )

    def test_producer_authority_block(self):
        self.check_container(
            lambda policy, bad: policy.__setitem__("producer_authority", bad),
            "producer_authority",
            self.authority_probe,
            state_event("rf-sensor", "OBSERVATION_EVENT", "RF"),
        )

    def test_producer_authority_producers_table(self):
        self.check_container(
            lambda policy, bad: policy["producer_authority"].__setitem__("producers", bad),
            "producer_authority.producers",
            self.authority_probe,
            state_event("rf-sensor", "OBSERVATION_EVENT", "RF"),
        )

    def test_producer_authority_producer_entry(self):
        self.check_container(
            lambda policy, bad: policy["producer_authority"]["producers"].__setitem__(
                "rf-sensor", bad
            ),
            "producer_authority.producers.rf-sensor",
            self.authority_probe,
            state_event("rf-sensor", "OBSERVATION_EVENT", "RF"),
        )

    def test_routing_block(self):
        self.check_container(
            lambda policy, bad: policy.__setitem__("routing", bad),
            "routing",
            self.routing_probe,
            state_event("fusion-engine", "STATE_EVENT", "TRACK_STATE"),
        )

    def test_routing_producers_table(self):
        self.check_container(
            lambda policy, bad: policy["routing"].__setitem__("producers", bad),
            "routing.producers",
            self.routing_probe,
            state_event("fusion-engine", "STATE_EVENT", "TRACK_STATE"),
        )

    def test_routing_producer_entry(self):
        self.check_container(
            lambda policy, bad: policy["routing"]["producers"].__setitem__("torch", bad),
            "routing.producers.torch",
            self.routing_probe,
            state_event("torch", "INFERENCE_EVENT", "CLASSIFICATION"),
        )

    def test_routing_command_event_block(self):
        self.check_container(
            lambda policy, bad: policy["routing"].__setitem__("command_event", bad),
            "routing.command_event",
            self.routing_probe,
            state_event("sensorops", "COMMAND_EVENT", "GOTO"),
        )

    def test_routing_command_event_keys(self):
        # Not a container but the same silent drop: a wrong-typed entry is
        # skipped by _is_comms_producer's isinstance filter, so that origin
        # quietly leaves the COMMAND_EVENT allowlist.
        for key, (label, _types) in validators._ROUTING_COMMAND_EVENT_SHAPES.items():
            for bad in PolicyShapeLintTest._wrong_values(self, label):
                with self.subTest(key=key, bad=repr(bad)):
                    policy = copy.deepcopy(self.policy)
                    policy["routing"]["command_event"][key] = bad
                    paths = [issue["path"] for issue in self.lint(policy)]
                    self.assertIn(f"routing.command_event.{key}", paths)

    def test_risk_mode_lint_reports_a_mangled_block(self):
        """R1-11 B-02 / R2-18: not-crashing is not the property to pin.

        The predecessor of this test called ``lint_policy_risk_modes`` and
        asserted nothing. It therefore certified "the lint did not traceback"
        as sufficient, and passed precisely BECAUSE nothing was reported: the
        coercion that stopped the AttributeError substituted a clean, empty,
        entirely legal-looking block for a destroyed one, and the operator got
        ``policy risk mode lint ok``, exit 0, with the timing-freshness gate
        fully off. Two of its three arms were also vacuous — a mangled
        ``lineage`` block never raised in the first place, so those subtests
        exercised no code the change touched.

        The property is: a destroyed block is NAMED. Surviving the mangle is
        asserted too (the call is still made), but it is now the weaker half.
        """
        blocks = (
            "producer_authority",
            "producer_authority.external_state_promotion",
            "timing_freshness",
            "timing_freshness.holdover_est_error_monotonic",
            "lineage",
        )
        for block in blocks:
            for bad in WRONG_FOR_MAPPING:
                with self.subTest(block=block, bad=repr(bad)):
                    policy = copy.deepcopy(self.policy)
                    head, _, tail = block.partition(".")
                    if tail:
                        policy[head][tail] = bad
                    else:
                        policy[head] = bad
                    issues = validators.lint_policy_risk_modes(policy)
                    paths = [issue["path"] for issue in issues]
                    self.assertIn(
                        block,
                        paths,
                        f"{block}={bad!r} was coerced to an empty block in silence",
                    )
                    reported = next(i for i in issues if i["path"] == block)
                    # The issue has to be usable: an operator filtering on
                    # risk_dimension or reason_code must see it.
                    self.assertTrue(reported["risk_dimension"])
                    self.assertTrue(reported["reason_codes"])
                    self.assertIn(type(bad).__name__, reported["message"])

    def test_every_coerced_block_is_covered_by_the_risk_table(self):
        """The coercion helper cannot be used without deciding how it reports.

        This is the structural half of B-02: the previous arrangement was
        "coerce, and rely on some other lint happening to speak for this
        block", which held for ``producer_authority`` and silently did not
        for ``timing_freshness``. Read the SOURCE, not the constants: every
        ``_mapping_or_empty`` call site must name a path the risk table
        knows, or the block it coerces has no way to announce itself.
        """
        tree = ast.parse(VALIDATORS_PATH.read_text(encoding="utf-8"))
        call_paths = set()
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "_mapping_or_empty"
            ):
                self.assertEqual(
                    4,
                    len(node.args),
                    "_mapping_or_empty must be called with (container, key, path, emit)",
                )
                path_arg = node.args[2]
                self.assertIsInstance(
                    path_arg, ast.Constant, "the reported path must be a literal"
                )
                call_paths.add(path_arg.value)

        self.assertTrue(call_paths, "AST scan found no _mapping_or_empty call sites")
        self.assertEqual(
            set(),
            call_paths - set(validators._POLICY_BLOCK_RISK),
            "a coerced block has no entry in _POLICY_BLOCK_RISK, so a "
            "destroyed one would raise KeyError instead of reporting",
        )
        self.assertEqual(
            set(validators._POLICY_BLOCK_RISK),
            call_paths,
            "_POLICY_BLOCK_RISK describes a block nothing coerces",
        )

    def test_mangled_timing_freshness_does_not_certify_a_stale_event(self):
        """R1-11 B-02, the runtime half the lint silence was hiding.

        A destroyed ``timing_freshness`` block cannot say ``enabled: false``.
        Reading it that way turned the whole stale / negative-age gate off,
        so an event whose only TIME_STATUS was an hour old validated clean.
        Absence stays permissive-with-defaults, because ``load_policy`` gives
        an absent file ``{}`` — which is a mapping and never lands here.
        """
        timing_status = {
            "zmeta_version": "1.0",
            "event": {
                "event_id": "01J00000000000000000000TS",
                "event_type": "SYSTEM_EVENT",
                "ts": "2026-07-21T00:00:00Z",
            },
            "source": {
                "platform_id": "test-platform",
                "node_role": "GATEWAY",
                "producer": "zmeta-gateway",
            },
            "payload": {
                "system_type": "TIME_STATUS",
                "metrics": {
                    "time_source": "GPS_PPS",
                    "sync_state": "LOCKED",
                    "est_error_ms": 1,
                    "last_sync_ts": "2026-07-21T00:00:00Z",
                },
            },
        }
        # One hour later, same source: stale against every shipped bound.
        target = state_event("zmeta-gateway", "STATE_EVENT", "TRACK_STATE")
        target["source"]["platform_id"] = "test-platform"
        target["event"]["ts"] = "2026-07-21T01:00:00Z"

        def check(timing_policy):
            state = validators.ValidationState()
            state.record_timing(timing_status)
            return validators.validate_timing_quality(
                target,
                self.policy["semantics"],
                state=state,
                severity_map=self.severity_map,
                timing_freshness_policy=timing_policy,
            )

        ok, violations = check(self.policy["timing_freshness"])
        self.assertFalse(ok, "the probe is useless unless the shipped policy refuses")
        self.assertEqual("TIMING_STATUS_STALE", violations[0]["code"])

        for bad in WRONG_FOR_MAPPING:
            with self.subTest(bad=repr(bad)):
                ok, violations = check(bad)
                self.assertFalse(ok, f"timing_freshness={bad!r} certified a stale event")
                self.assertEqual("TIMING_STATUS_STALE", violations[0]["code"])
                self.assertIn(
                    "policy_error",
                    violations[0]["details"],
                    "a refusal caused by broken policy must name the policy",
                )

        # An explicit disable is still honoured, and an absent file (`{}`)
        # still runs on the built-in defaults.
        ok, _ = check({"enabled": False})
        self.assertTrue(ok)
        ok, violations = check({})
        self.assertFalse(ok, "an absent policy file must still bound staleness")
        self.assertNotIn("policy_error", violations[0]["details"])

    def test_mangled_promotion_block_does_not_wave_a_promotion_through(self):
        """Same class as B-02, in the gate that exists to stop laundering.

        ``producer_authority.external_state_promotion`` mangled to a bare key
        silently switched the ENTIRE external-promotion gate off: no trust
        anchor, no lineage status, no loop check, no freshness bound, for
        every producer whose rule requires promotion.
        """
        event = state_event("cot-ingress", "STATE_EVENT", "TRACK_STATE")
        ok, violations = self.authority_probe(self.policy, event)
        self.assertFalse(ok, "the probe is useless unless the shipped policy refuses")

        for bad in WRONG_FOR_MAPPING:
            with self.subTest(bad=repr(bad)):
                policy = copy.deepcopy(self.policy)
                policy["producer_authority"]["external_state_promotion"] = bad
                self.assertIn(
                    "producer_authority.external_state_promotion",
                    [i["path"] for i in validators.lint_policy_risk_modes(policy)],
                )
                ok, violations = self.authority_probe(policy, event)
                self.assertFalse(ok, f"promotion block {bad!r} disabled the gate")
                self.assertIn("policy_error", violations[0]["details"])

        # enabled: false is a real, documented deployment and stays honoured.
        policy = copy.deepcopy(self.policy)
        policy["producer_authority"]["external_state_promotion"]["enabled"] = False
        ok, _ = self.authority_probe(policy, event)
        self.assertTrue(ok)

    def test_mangled_lineage_block_still_produces_its_diagnostics(self):
        """Third member of the same family: a destroyed block is not a disable."""
        event = state_event("fusion-engine", "STATE_EVENT", "TRACK_STATE")
        event["lineage"] = {"based_on": ["01J000000000000000000PARENT"]}

        def check(lineage_policy):
            return validators.validate_lineage(
                event,
                lineage_policy,
                state=validators.ValidationState(),
                profile="H",
                severity_map=self.severity_map,
            )

        _ok, violations = check(self.policy["lineage"])
        self.assertEqual(["LINEAGE_PARENT_UNRESOLVED"], [v["code"] for v in violations])

        for bad in WRONG_FOR_MAPPING:
            with self.subTest(bad=repr(bad)):
                _ok, violations = check(bad)
                self.assertEqual(
                    ["LINEAGE_PARENT_UNRESOLVED"],
                    [v["code"] for v in violations],
                    f"lineage={bad!r} dropped the lineage diagnostics in silence",
                )
                self.assertIn("policy_error", violations[0]["details"])

        _ok, violations = check({"enabled": False})
        self.assertEqual([], violations)

    def test_unhashable_promotion_metadata_refuses_instead_of_crashing(self):
        """R1-11 A-14: `payload.extensions` is free-form in both schemas.

        A producer may legally put a list or a dict where the promotion guard
        expects a scalar token, and ``<list> in <set>`` raised ``TypeError``
        out of the public ``validate_producer_authority`` API — an
        ``INTERNAL_ERROR`` drop that tells the operator "gateway bug" instead
        of "promotion refused", hiding the laundering attempt.

        Enumerated from the metadata the guard tests for membership, not from
        the one key the finding named.
        """
        metadata = {
            "state_category": "PROMOTED_EXTERNAL_STATE",
            "origin_kind": "EXTERNAL_REPORT",
            "projection_id": "cot",
            "promotion_policy_id": "PROMOTE-COT-STATE-V1",
            "trust_ref": "producer-authority:cot-ingress",
            "lineage_status": "EXTERNAL_SOURCE",
            "loop_status": "CHECKED_NOT_REFLECTION",
            "confidence_basis": "EXPLICIT_EXTERNAL_CONFIDENCE",
            "source_event_uid": "cot:external-1",
            "freshness_ms": 5000,
        }
        event = state_event("cot-ingress", "STATE_EVENT", "TRACK_STATE")
        event["lineage"] = {
            "based_on": ["01J000000000000000000PARENT"],
            "transform": "promote:cot@template:PROMOTE-COT-STATE-V1",
        }
        event["payload"] = {"extensions": {"external_promotion": dict(metadata)}}

        ok, violations = self.authority_probe(self.policy, event)
        self.assertTrue(ok, f"the probe is useless unless it passes clean: {violations}")

        # `source_event_uid` is only PRESENCE-checked (`_is_blank`), never
        # compared against a policy allowlist, so an unhashable value there is
        # not a promotion-policy question at all — refusing it would need a
        # type claim about promotion metadata that neither schema makes
        # (`payload.extensions` is `additionalProperties: true`). The crash
        # class still has to be closed for it; the refusal must not be
        # invented. `source_zmeta_event_id` is the same shape.
        PRESENCE_ONLY = {"source_event_uid", "source_zmeta_event_id"}

        for key in sorted(metadata):
            for bad in (["X"], {"X": 1}, [{"X": 1}]):
                with self.subTest(key=key, bad=repr(bad)):
                    poisoned = copy.deepcopy(event)
                    poisoned["payload"]["extensions"]["external_promotion"][key] = bad
                    try:
                        ok, violations = self.authority_probe(self.policy, poisoned)
                    except Exception as exc:  # noqa: BLE001 - that IS the defect
                        self.fail(f"{key}={bad!r} raised {type(exc).__name__}: {exc}")
                    if key in PRESENCE_ONLY:
                        continue
                    self.assertFalse(
                        ok,
                        f"{key}={bad!r} was accepted as a valid promotion token",
                    )
                    self.assertEqual("PRODUCER_NOT_ALLOWED", violations[0]["code"])

        # And the split above must stay honest: every key excluded from the
        # refusal assertion has to be one the promotion guard really never
        # membership-tests, read from the SOURCE rather than trusted.
        promotion_source = ast.parse(VALIDATORS_PATH.read_text(encoding="utf-8"))
        compared = set()
        for node in ast.walk(promotion_source):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
                continue
            if node.func.id != "_allowlist_contains" or not node.args:
                continue
            target = node.args[0]
            if isinstance(target, ast.Name):
                compared.add(target.id)
        self.assertTrue(compared, "AST scan found no allowlist membership tests")
        self.assertEqual(
            set(),
            compared & PRESENCE_ONLY,
            "a key excluded from the refusal assertion IS membership-tested",
        )

        # ...and the enumeration above must not drift: resolve each compared
        # local back to the metadata key it was read from, and require the
        # probe to carry it. A new membership-tested metadata key added to the
        # guard fails here instead of shipping unexercised.
        bound = {}
        for node in ast.walk(promotion_source):
            if not isinstance(node, ast.FunctionDef):
                continue
            if node.name != "_validate_external_state_promotion":
                continue
            for sub in ast.walk(node):
                if not isinstance(sub, ast.Assign) or len(sub.targets) != 1:
                    continue
                target = sub.targets[0]
                call = sub.value
                if not isinstance(target, ast.Name) or not isinstance(call, ast.Call):
                    continue
                func = call.func
                if (
                    isinstance(func, ast.Attribute)
                    and func.attr == "get"
                    and isinstance(func.value, ast.Name)
                    and func.value.id == "metadata"
                    and call.args
                    and isinstance(call.args[0], ast.Constant)
                ):
                    bound[target.id] = call.args[0].value
        exercised = {bound[name] for name in compared if name in bound}
        self.assertTrue(exercised, "no membership-tested metadata key was resolved")
        self.assertEqual(
            set(),
            exercised - set(metadata),
            "the guard membership-tests a metadata key this probe never poisons",
        )

    def test_empty_authority_document_is_a_legal_deployment(self):
        """R1-11 R2-24: an absent and an empty policy file are the same thing.

        ``load_policy`` produces ``{}`` for both, so a lint that reports one
        and blesses the other fails a deployment it cannot distinguish.
        """
        import tempfile
        import shutil

        for content, label in (
            ("# no producer-authority policy in this deployment\n", "comment-only"),
            ("", "empty"),
            (None, "absent"),
        ):
            with self.subTest(document=label):
                scratch = Path(tempfile.mkdtemp()) / "policy"
                shutil.copytree(ROOT / "policy", scratch)
                target = scratch / "producer-authority.yaml"
                if content is None:
                    target.unlink()
                else:
                    target.write_text(content, encoding="utf-8")

                policy = validators.load_policy(scratch)
                self.assertEqual({}, policy["producer_authority"], label)
                issues = (
                    validators.lint_policy_risk_modes(policy)
                    + validators.lint_producer_authority_structure(policy)
                    + validators.lint_routing_producer_enforcement_structure(policy)
                    + validators.lint_policy_document_structure(scratch)
                )
                self.assertEqual(
                    [],
                    [issue["path"] for issue in issues],
                    f"a {label} producer-authority.yaml failed the lint",
                )

        # routing.yaml is NOT optional to load_policy, so an empty one is not
        # equivalent to anything legal and must still be reported.
        scratch = Path(tempfile.mkdtemp()) / "policy"
        shutil.copytree(ROOT / "policy", scratch)
        (scratch / "routing.yaml").write_text("# oops\n", encoding="utf-8")
        self.assertIn(
            "routing.yaml#routing",
            [i["path"] for i in validators.lint_policy_document_structure(scratch)],
        )

    def test_an_unreadable_vocabulary_is_never_cached(self):
        """R1-11 R2-32: one unlucky first call must not disable the check.

        The vocabulary is derived from ``schema/*.schema.json``. Caching an
        EMPTY derivation makes a transient unreadable-schema condition
        permanent for the life of the process, and the runtime half of the
        entry check reports nothing when the vocabulary is empty.
        """
        saved_dir = validators._KERNEL_SCHEMA_DIR
        saved_cache = dict(validators._EVENT_VOCABULARY_CACHE)
        try:
            validators._EVENT_VOCABULARY_CACHE.clear()
            validators._KERNEL_SCHEMA_DIR = ROOT / "no-such-schema-directory"
            self.assertEqual(frozenset(), validators._event_vocabulary("event_type"))
            self.assertEqual(
                {},
                validators._EVENT_VOCABULARY_CACHE,
                "a failed derivation was cached and now cannot recover",
            )
            validators._KERNEL_SCHEMA_DIR = saved_dir
            self.assertIn("STATE_EVENT", validators._event_vocabulary("event_type"))
        finally:
            validators._KERNEL_SCHEMA_DIR = saved_dir
            validators._EVENT_VOCABULARY_CACHE.clear()
            validators._EVENT_VOCABULARY_CACHE.update(saved_cache)

    def test_routing_key_name_typos_are_reported(self):
        # The other half of the treatment the producer-authority side already
        # had. A renamed key is invisible to a shape table — the key it
        # describes is simply not there — and `producrs:` admitted an event
        # the shipped routing policy refuses.
        cases = (
            (lambda routing: routing, validators._ROUTING_TOP_KEYS, "routing"),
            (
                lambda routing: routing["producers"]["torch"],
                validators._ROUTING_PRODUCER_ENTRY_KEYS,
                "routing.producers.torch",
            ),
            (
                lambda routing: routing["command_event"],
                validators._ROUTING_COMMAND_EVENT_KEYS,
                "routing.command_event",
            ),
        )
        for select, keys, base in cases:
            for key in sorted(keys):
                with self.subTest(base=base, key=key):
                    policy = copy.deepcopy(self.policy)
                    block = select(policy["routing"])
                    if key not in block:
                        continue
                    block[f"{key}x"] = block.pop(key)
                    paths = [issue["path"] for issue in self.lint(policy)]
                    self.assertIn(f"{base}.{key}x", paths)

    def test_shipped_policy_stays_clean(self):
        self.assertEqual([], self.lint(self.policy))


class EventTypeVocabularyFailsClosedTest(unittest.TestCase):
    """R1-11 A-05 residual c: an entry that is a STRING but not an event type.

    ``STATE_EVEN`` / ``state_event`` is stringified into a token no event can
    ever carry — identical in effect to the non-string entry the shape check
    already rejects, and identically invisible. One character turned the
    producer-authority require-match gate off and forwarded an unregistered
    producer's track as clean authoritative state.
    """

    @classmethod
    def setUpClass(cls):
        cls.policy = validators.load_policy(ROOT / "policy")
        cls.severity_map = cls.policy["violation_severities"]

    TYPOS = ("STATE_EVEN", "state_event", "STATE_EVENT x")

    def lint(self, policy):
        return validators.lint_producer_authority_structure(
            policy
        ) + validators.lint_routing_producer_enforcement_structure(policy)

    def check_typo(self, mutate, lint_path, probe, event):
        for typo in self.TYPOS:
            with self.subTest(typo=typo):
                policy = copy.deepcopy(self.policy)
                mutate(policy, typo)
                paths = [issue["path"] for issue in self.lint(policy)]
                self.assertIn(lint_path, paths, f"lint stayed silent on {typo!r}")
                ok, violations = probe(policy, event)
                self.assertFalse(ok, f"{typo!r} disabled the gate at runtime")
                self.assertIn("policy_error", violations[0]["details"])

    def authority_probe(self, policy, event):
        return validators.validate_producer_authority(
            event, policy["producer_authority"], self.severity_map
        )

    def routing_probe(self, policy, event):
        return validators.validate_routing(event, policy["routing"], self.severity_map)

    def test_require_match_for_event_types(self):
        def mutate(policy, typo):
            values = list(policy["producer_authority"]["require_match_for_event_types"])
            values[values.index("STATE_EVENT")] = typo
            policy["producer_authority"]["require_match_for_event_types"] = values

        # Shipped policy refuses this producer BECAUSE STATE_EVENT is in the
        # require-match list; the typo is the whole difference.
        ok, _ = self.authority_probe(self.policy, state_event("totally-unregistered-node"))
        self.assertFalse(ok)
        self.check_typo(
            mutate,
            "producer_authority.require_match_for_event_types",
            self.authority_probe,
            state_event("totally-unregistered-node"),
        )

    def test_routing_require_allowlist_for_event_types(self):
        def mutate(policy, typo):
            policy["routing"]["producer_enforcement"][
                "require_allowlist_for_event_types"
            ] = [typo]

        self.check_typo(
            mutate,
            "routing.producer_enforcement.require_allowlist_for_event_types",
            self.routing_probe,
            state_event("totally-unregistered-node", "COMMAND_EVENT", "GOTO"),
        )

    def test_producer_authority_forbidden_event_types(self):
        def mutate(policy, typo):
            policy["producer_authority"]["producers"]["torch"]["forbidden_event_types"] = [typo]

        self.check_typo(
            mutate,
            "producer_authority.producers.torch.forbidden_event_types",
            self.authority_probe,
            state_event("torch", "INFERENCE_EVENT", "CLASSIFICATION"),
        )

    def test_routing_forbidden_event_types(self):
        def mutate(policy, typo):
            policy["routing"]["producers"]["torch"]["forbidden_event_types"] = [typo]

        self.check_typo(
            mutate,
            "routing.producers.torch.forbidden_event_types",
            self.routing_probe,
            state_event("torch", "INFERENCE_EVENT", "CLASSIFICATION"),
        )

    def check_allowlist_typo_is_proportionate(self, mutate, lint_path, probe, key_typed):
        """R1-11 R2-17: an ALLOWLIST typo must not cost the surviving entries.

        A typo in ``allowed_event_types`` removes an entry from an allowlist,
        which already fails closed on its own — the event type that was
        misspelled simply stops being authorized. Refusing the producer
        WHOLESALE on top of that throws away the events the surviving,
        correctly-spelled entries explicitly authorize, and buys no honesty:
        it re-closes a door that is already shut. That is the "discard good
        canonical data" failure, and this pins that it does not happen.

        Three things are asserted together, because the fail-open direction
        must NOT be relaxed with it:
          1. the deployment lint still reports the typo, loudly and by path;
          2. an event named correctly in a surviving entry is still admitted;
          3. the event type that was MIStyped is refused.
        """
        for typo in self.TYPOS:
            with self.subTest(typo=typo):
                policy = copy.deepcopy(self.policy)
                mutate(policy, typo)

                paths = [issue["path"] for issue in self.lint(policy)]
                self.assertIn(lint_path, paths, f"lint stayed silent on {typo!r}")

                survivor = state_event("torch", "FUSION_EVENT", "TRACK_FUSION")
                ok, violations = probe(policy, survivor)
                self.assertTrue(
                    ok,
                    f"{typo!r} discarded an event the surviving entry authorizes: "
                    f"{violations}",
                )

                mistyped = state_event("torch", key_typed, "TRACK_STATE")
                ok, _violations = probe(policy, mistyped)
                self.assertFalse(
                    ok,
                    f"{typo!r} left the MIStyped event type authorized",
                )

    def test_routing_allowed_event_types(self):
        def mutate(policy, typo):
            policy["routing"]["producers"]["torch"]["allowed_event_types"] = [
                typo,
                "FUSION_EVENT",
            ]

        self.check_allowlist_typo_is_proportionate(
            mutate,
            "routing.producers.torch.allowed_event_types",
            self.routing_probe,
            "STATE_EVENT",
        )

    def test_producer_authority_allowed_event_types(self):
        def mutate(policy, typo):
            policy["producer_authority"]["producers"]["torch"]["allowed_event_types"] = [
                typo,
                "FUSION_EVENT",
            ]

        self.check_allowlist_typo_is_proportionate(
            mutate,
            "producer_authority.producers.torch.allowed_event_types",
            self.authority_probe,
            "STATE_EVENT",
        )

    def test_real_event_types_stay_green(self):
        # The check must not fire on any event type the schema declares, or
        # it is a lint that forbids correct policy.
        for event_type in sorted(validators._event_vocabulary("event_type")):
            with self.subTest(event_type=event_type):
                policy = copy.deepcopy(self.policy)
                policy["producer_authority"]["require_match_for_event_types"] = [event_type]
                policy["routing"]["producers"]["torch"]["forbidden_event_types"] = [event_type]
                self.assertEqual([], self.lint(policy))

    def test_a_scalar_value_still_works_at_runtime(self):
        # _list_values reads a bare scalar as a one-item list and loses
        # nothing, so refusing it would punish a working deployment. The lint
        # still reports the shape; the runtime must not fail closed on it.
        policy = copy.deepcopy(self.policy)
        policy["routing"]["producers"]["torch"]["allowed_event_types"] = "FUSION_EVENT"
        ok, violations = self.routing_probe(
            policy, state_event("torch", "FUSION_EVENT", "TRACK_FUSION")
        )
        self.assertTrue(ok, violations)
        self.assertIn(
            "routing.producers.torch.allowed_event_types",
            [issue["path"] for issue in self.lint(policy)],
        )


class EventVocabularyDerivationTest(unittest.TestCase):
    """The vocabulary must come from the schemas, not from a copy of them."""

    def test_matches_the_shipped_schema_enum(self):
        import json

        declared = set()
        for path in sorted((ROOT / "schema").glob("*.schema.json")):
            document = json.loads(path.read_text(encoding="utf-8"))
            event = document.get("$defs", {}).get("event", {})
            declared.update(event.get("properties", {}).get("event_type", {}).get("enum", []))
        self.assertTrue(declared)
        self.assertEqual(declared, set(validators._event_vocabulary("event_type")))

    def test_is_read_from_the_schema_directory(self):
        # A restated list would ignore this file entirely.
        import json
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "invented.schema.json"
            path.write_text(
                json.dumps(
                    {
                        "$defs": {
                            "event": {
                                "properties": {
                                    "event_type": {"enum": ["INVENTED_EVENT"]}
                                }
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )
            derived = validators._event_vocabulary("event_type", schema_dir=tmp)
        self.assertEqual({"INVENTED_EVENT"}, set(derived))

    def test_underivable_vocabulary_is_announced_not_skipped(self):
        # If the schemas cannot be read the entry check cannot run. It must
        # say so rather than pass everything, which would be a guard that is
        # green precisely when it is blind.
        import tempfile

        original_dir = validators._KERNEL_SCHEMA_DIR
        original_cache = dict(validators._EVENT_VOCABULARY_CACHE)
        try:
            with tempfile.TemporaryDirectory() as tmp:
                validators._KERNEL_SCHEMA_DIR = Path(tmp)
                validators._EVENT_VOCABULARY_CACHE.clear()
                problem = validators._shape_problem(
                    "require_match_for_event_types",
                    ["STATE_EVENT"],
                    validators._SHAPE_LIST,
                )
                self.assertIsNotNone(problem)
                self.assertIn("did not run", problem)
        finally:
            validators._KERNEL_SCHEMA_DIR = original_dir
            validators._EVENT_VOCABULARY_CACHE.clear()
            validators._EVENT_VOCABULARY_CACHE.update(original_cache)

    def test_runtime_rule_keys_match_the_declared_shapes(self):
        # _producer_rule_policy_error walks its own key tuple. If that drifts
        # from the shape table, the runtime and the lint stop checking the
        # same thing.
        self.assertEqual(
            set(validators._ROUTING_PRODUCER_ENTRY_SHAPES),
            set(validators._PRODUCER_RULE_LIST_KEYS),
        )


class PolicyDocumentStructureTest(unittest.TestCase):
    """R1-11 A-05 residual a: the wrapper key, which no in-memory lint can see.

    ``load_policy`` unwraps each document with ``.get("<wrapper>", <default>)``.
    A misspelled top-level key therefore loads as the permissive default, and
    by the time any in-memory lint runs, ``routng:`` and a legitimately empty
    block are the same object.
    """

    LINT = ROOT / "tools" / "lint_policy_risk_modes.py"

    def scratch_policy(self, filename=None, text=None):
        import shutil
        import tempfile

        tmp = tempfile.mkdtemp()
        dest = Path(tmp) / "policy"
        shutil.copytree(ROOT / "policy", dest)
        if filename is not None:
            (dest / filename).write_text(text, encoding="utf-8")
        return dest

    def run_cli(self, policy_dir):
        import subprocess
        import sys

        proc = subprocess.run(
            [sys.executable, str(self.LINT), "--policy-dir", str(policy_dir)],
            capture_output=True,
            text=True,
        )
        return proc.returncode, proc.stdout

    def test_shipped_policy_documents_are_clean(self):
        self.assertEqual([], validators.lint_policy_document_structure(ROOT / "policy"))

    def test_misspelled_wrapper_key_is_reported(self):
        for filename, wrapper in (
            ("routing.yaml", "routing"),
            ("producer-authority.yaml", "producer_authority"),
        ):
            with self.subTest(filename=filename):
                original = (ROOT / "policy" / filename).read_text(encoding="utf-8")
                typo = original.replace(f"{wrapper}:", f"{wrapper[:-1]}:", 1)
                self.assertNotEqual(original, typo)
                dest = self.scratch_policy(filename, typo)
                paths = [
                    issue["path"]
                    for issue in validators.lint_policy_document_structure(dest)
                ]
                self.assertIn(f"{filename}#{wrapper}", paths)

    def test_the_shipped_cli_carries_the_document_check(self):
        # A check that is not wired into the command an operator runs is not
        # a control.
        original = (ROOT / "policy" / "routing.yaml").read_text(encoding="utf-8")
        dest = self.scratch_policy("routing.yaml", original.replace("routing:", "routng:", 1))
        code, out = self.run_cli(dest)
        self.assertEqual(1, code, out)
        self.assertIn("routing.yaml#routing", out)

    def test_shipped_policy_passes_the_cli(self):
        code, out = self.run_cli(self.scratch_policy())
        self.assertEqual(0, code, out)


class MangledPolicyEndToEndTest(unittest.TestCase):
    """The whole point, measured where the operator sees it.

    A mangled ``routing`` block used to raise ``AttributeError`` out of every
    call, which the receive-loop backstop reports as ``INTERNAL_ERROR`` naming
    no policy problem — a 100% outage with no way to tell it from a code bug.
    The refusal that replaces it must reach the wire as a governed
    SCHEMA_VIOLATION that names the file and key.
    """

    @classmethod
    def setUpClass(cls):
        import json

        gateway_path = ROOT / "gateway" / "src" / "gateway.py"
        gateway_spec = importlib.util.spec_from_file_location("zmeta_gateway", gateway_path)
        cls.gateway = importlib.util.module_from_spec(gateway_spec)
        gateway_spec.loader.exec_module(cls.gateway)
        cls.validator = validators.load_schema(ROOT / "schema" / "zmeta-event.schema.json")
        cls.event = None
        for line in (
            (ROOT / "examples" / "zmeta-v1.1-examples.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
        ):
            if not line.strip():
                continue
            candidate = json.loads(line)
            if candidate.get("event", {}).get("event_type") == "STATE_EVENT":
                cls.event = candidate
                break

    def emit(self, policy_dir):
        import json

        policy = validators.load_policy(policy_dir)
        emitted = self.gateway.process_message(
            json.dumps(self.event).encode(),
            self.validator,
            policy,
            "H",
            set(),
            "json",
            timing_state=validators.ValidationState(),
        )
        return [
            json.loads(item) if isinstance(item, (bytes, str)) else item
            for item in emitted
        ]

    def scratch(self, text):
        import shutil
        import tempfile

        dest = Path(tempfile.mkdtemp()) / "policy"
        shutil.copytree(ROOT / "policy", dest)
        (dest / "routing.yaml").write_text(text, encoding="utf-8")
        return dest

    def test_shipped_policy_forwards_the_event(self):
        self.assertIsNotNone(self.event, "no shipped STATE_EVENT to probe with")
        types = [event["event"]["event_type"] for event in self.emit(ROOT / "policy")]
        self.assertIn("STATE_EVENT", types)

    def test_mangled_routing_block_emits_a_named_refusal(self):
        for text in ("routing:\n", "routing: producers\n"):
            with self.subTest(routing_yaml=text.strip()):
                emitted = self.emit(self.scratch(text))
                self.assertTrue(emitted, "the refusal must reach the wire")
                types = {event["event"]["event_type"] for event in emitted}
                self.assertNotIn("STATE_EVENT", types, "mangled policy forwarded the event")
                metrics = emitted[0]["payload"]["metrics"]
                self.assertEqual("PRODUCER_NOT_ALLOWED", metrics.get("reason_code"))
                self.assertIn("policy/routing.yaml", metrics.get("policy_error", ""))


if __name__ == "__main__":
    unittest.main()
