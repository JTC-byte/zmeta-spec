"""Every STATE field the contract prohibits by name is enforced by the policy.

Contract 7.7 lists payload fields a STATE_EVENT must not carry, and
`policy/semantics.yaml` holds the list the validators enforce. A name the
contract states and the policy lacks is a contract rule nothing enforces, so
this test fails on it. The policy list may hold more names than the
contract's: the contract's list says "include", and the command denylist
already keeps a defensive superset.

The comparison is exercised on synthetic text as well as the live tree,
because a comparison that only ever sees agreeing lists cannot show it would
notice a difference, and an extraction that finds nothing compares two empty
sets.
"""

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "spec" / "semantics-contract.md"
POLICY = ROOT / "policy" / "semantics.yaml"
SENTENCE_START = "- Prohibited state payload fields include"
# The contract's list as it stands, in order. A name that loses its backticks
# or its line drops out of the extraction; pinning the whole list makes that
# a failure here, where a floor on the count would let one name go unseen.
CONTRACT_LIST = [
    "features",
    "raw_features",
    "modality",
    "measurement",
    "measurements",
    "t_start",
    "t_end",
    "observed_at",
    "data_ref",
    "data_refs",
]


def contract_names(text):
    """Return the backticked names in the 7.7 prohibited-field bullet, in order."""
    lines = text.splitlines()
    starts = [i for i, line in enumerate(lines) if line.startswith(SENTENCE_START)]
    assert len(starts) == 1, f"expected one prohibited-field bullet, found {len(starts)}"
    bullet = [lines[starts[0]]]
    for line in lines[starts[0] + 1:]:
        if not line.startswith("  "):
            break
        bullet.append(line)
    return re.findall(r"`([^`]+)`", " ".join(bullet))


def policy_names(policy):
    """Return the names in the policy file's STATE list, in order."""
    return list(policy["semantics"]["state_event"]["payload_must_not_contain"])


def synthetic_policy(names):
    return {"semantics": {"state_event": {"payload_must_not_contain": names}}}


def unenforced(contract_text, policy):
    """Names the contract states and the policy does not enforce."""
    return set(contract_names(contract_text)) - set(policy_names(policy))


def test_every_contract_name_is_enforced():
    text = CONTRACT.read_text(encoding="utf-8")
    policy = yaml.safe_load(POLICY.read_text(encoding="utf-8"))
    assert contract_names(text) == CONTRACT_LIST
    assert unenforced(text, policy) == set()


def test_observed_at_is_named_in_both():
    text = CONTRACT.read_text(encoding="utf-8")
    policy = yaml.safe_load(POLICY.read_text(encoding="utf-8"))
    assert "observed_at" in contract_names(text)
    assert "observed_at" in policy_names(policy)


def test_a_name_missing_from_the_policy_is_reported():
    text = "- Prohibited state payload fields include `a`, `b`,\n  and `c`.\n- Next bullet names `d`.\n"
    assert unenforced(text, synthetic_policy(["a", "b"])) == {"c"}


def test_a_policy_superset_is_allowed():
    text = "- Prohibited state payload fields include `a` and `b`.\n"
    assert unenforced(text, synthetic_policy(["a", "b", "c"])) == set()
