"""The version scope of the ZMETA-COT-PROJECTION conformance class matches the versions of its required fixtures.

The class requires `conformance/cot-golden/golden.jsonl` and `conformance/adapter-harness/must-pass.jsonl`. Both hold
cases of the 1.1.0 experimental branch: two golden cases project `examples/zmeta-v1.1-examples.jsonl:13`, and three
harness cases expect `zmeta_version` 1.1.0. On the maintainer's answer of 2026-11-16 that no CoT projection claimant
implements ZMeta 1.0 only, the class's `version_scope` names both branches, `["1.0", "1.1.0-experimental"]`, so the
scope states what the required evidence covers.

The first test reads the versions the two fixtures state (each golden case's `event.zmeta_version`, and each harness
case's `expect.expected_values.zmeta_version` where it names one) and holds the scope to them. It is written for this
class alone. `ZMETA-ADAPTER` requires the same harness file under a scope of `["1.0"]`, and whether it follows is the
maintainer's open question, so no general check of fixtures against scopes is made here.

The second test shows the consequence the class validator enforces once the scope names the experimental branch: a
claim of the class whose `zmeta_versions_supported` omits `1.1.0-experimental` is refused with
`CONFORMANCE_CLAIM_VERSION_SCOPE_INVALID` for this class.

Both tests were run against the manifest before the scope was widened and failed there.
"""

import importlib.util
import json
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from zmeta_decode_guard import pairs_refusing_duplicates  # noqa: E402

MANIFEST_PATH = ROOT / "conformance" / "conformance_classes.yaml"
REFERENCE_CLAIM_PATH = ROOT / "conformance" / "claims" / "example-reference-gateway.yaml"
VALIDATOR_PATH = ROOT / "tools" / "validate_conformance_classes.py"
CLASS_ID = "ZMETA-COT-PROJECTION"
GOLDEN = "conformance/cot-golden/golden.jsonl"
HARNESS = "conformance/adapter-harness/must-pass.jsonl"

# An event's zmeta_version and the scope token that names its branch (conformance_classes.yaml, zmeta_versions).
SCOPE_TOKEN = {"1.0": "1.0", "1.1.0": "1.1.0-experimental"}

spec = importlib.util.spec_from_file_location("zmeta_validate_conformance_classes_scope", VALIDATOR_PATH)
validate_conformance_classes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validate_conformance_classes)


def _record(manifest):
    records = [record for record in manifest["class_records"] if record["class_id"] == CLASS_ID]
    assert len(records) == 1, f"{CLASS_ID} records found: {len(records)}"
    return records[0]


def _cases(rel):
    text = (ROOT / rel).read_text(encoding="utf-8")
    return [json.loads(line, object_pairs_hook=pairs_refusing_duplicates) for line in text.splitlines() if line.strip()]


def _stated_versions(rel):
    """The zmeta_version values a required fixture states, one per case that states one."""
    if rel == GOLDEN:
        return [case["event"]["zmeta_version"] for case in _cases(rel)]
    if rel == HARNESS:
        return [case["expect"]["expected_values"]["zmeta_version"] for case in _cases(rel)
                if "zmeta_version" in (case.get("expect", {}).get("expected_values") or {})]
    raise AssertionError(f"{CLASS_ID} requires a fixture this test does not know how to read: {rel}")


def test_the_cot_projection_class_scope_matches_its_required_fixtures():
    manifest = validate_conformance_classes.load_yaml(MANIFEST_PATH)
    record = _record(manifest)
    assert record["required_conformance_fixtures"] == [HARNESS, GOLDEN]
    stated = {rel: sorted(set(_stated_versions(rel))) for rel in record["required_conformance_fixtures"]}
    assert stated == {HARNESS: ["1.1.0"], GOLDEN: ["1.0", "1.1.0"]}, stated
    unknown = sorted({v for versions in stated.values() for v in versions} - set(SCOPE_TOKEN))
    assert not unknown, f"a fixture states a version with no scope token: {unknown}"
    covered = sorted({SCOPE_TOKEN[v] for versions in stated.values() for v in versions})
    scope = record["version_scope"]
    assert len(scope) == len(set(scope)), f"{CLASS_ID} version_scope repeats a value: {scope}"
    assert set(scope) <= set(manifest["zmeta_versions"]), f"{CLASS_ID} version_scope names an unknown branch: {scope}"
    assert sorted(scope) == covered, f"{CLASS_ID} version_scope {scope}; its required fixtures cover {covered}"


def test_a_cot_projection_claim_without_the_experimental_branch_is_refused():
    manifest = validate_conformance_classes.load_yaml(MANIFEST_PATH)
    claim = validate_conformance_classes.load_yaml(REFERENCE_CLAIM_PATH)
    assert CLASS_ID in claim["classes_claimed"]

    def scope_issues(versions):
        claim["zmeta_versions_supported"] = versions
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "claim.yaml"
            path.write_text(yaml.safe_dump(claim, sort_keys=False), encoding="utf-8")
            issues = validate_conformance_classes.validate_claim(path, manifest)
        return [issue for issue in issues
                if issue["code"] == "CONFORMANCE_CLAIM_VERSION_SCOPE_INVALID" and issue.get("item") == CLASS_ID]

    assert scope_issues(["1.0", "1.1.0-experimental"]) == []
    assert len(scope_issues(["1.0"])) == 1
