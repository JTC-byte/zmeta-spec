"""The anti-vacuity helper must not itself be vacuous.

A helper whose job is to refuse meaningless proofs is worthless if it accepts
one, and there is no outer guard to catch that — it is the bottom of the
stack. So both directions are pinned: every shape that must raise, and the
ordinary substitution that must be allowed through untouched.
"""

import pytest

from vacuity import VacuousProbe, assert_differs, mutate


SOURCE = "release focus: the bladeRF corpus. No schema, policy, or vocab changes.\n"


def test_mutate_performs_an_ordinary_substitution():
    result = mutate(SOURCE, "bladeRF corpus", "two-node quickstart", what="ordinary edit")
    assert "two-node quickstart" in result
    assert "bladeRF corpus" not in result


def test_mutate_refuses_an_absent_anchor():
    """The exact failure that made a live probe prove nothing.

    A `str.replace` with a slightly-wrong anchor returns the source unchanged
    and reports success, so the guard is then asked about unmodified content
    and passes for the most boring possible reason.
    """
    with pytest.raises(VacuousProbe, match="anchor not found"):
        mutate(SOURCE, "bladeRF korpus", "anything", what="typo'd anchor")


def test_mutate_refuses_a_no_op_substitution():
    with pytest.raises(VacuousProbe, match="no-op"):
        mutate(SOURCE, "bladeRF corpus", "bladeRF corpus", what="identical replacement")


def test_mutate_refuses_an_empty_anchor():
    with pytest.raises(VacuousProbe, match="empty anchor"):
        mutate(SOURCE, "", "x", what="empty anchor")


def test_mutate_names_the_demonstration_in_its_error():
    """A failure must say which proof collapsed, not point at the helper."""
    with pytest.raises(VacuousProbe, match="swap the focus bullet"):
        mutate(SOURCE, "absent", "x", what="swap the focus bullet")


def test_assert_differs_accepts_a_real_change_and_refuses_none():
    assert_differs("a", "b", what="real change")
    with pytest.raises(VacuousProbe, match="produced no change"):
        assert_differs("a", "a", what="unchanged")
