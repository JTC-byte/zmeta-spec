"""Helpers for proving a guard would actually fail.

A pin that passes tells you the tree is currently good. It does NOT tell you
the pin would notice if the tree went bad — and the whole reason a pin exists
is that second claim. Separating the two is the recurring failure this repo
has now recorded seven times across tests, shipped tooling, and audit probes
(doctrine log P2-D1).

The demonstration is the part that rots, because it has historically been a
*session act*: an author mutates something, watches a check go red, and says
so in a commit message. Nothing re-runs it, nothing checks the mutation was
real, and the reader inherits an author-attested claim. One of those probes
turned out to be a `str.replace` whose anchor did not match, so it mutated
nothing and proved nothing while reporting success.

`mutate` closes that specific hole: a substitution that changes nothing is an
error, not a quiet pass. Use it wherever a test doctors real content to
demonstrate a guard's red state, so the demonstration lives in the repo and
re-runs in CI instead of living in a commit message.
"""

from __future__ import annotations


class VacuousProbe(AssertionError):
    """Raised when a demonstration could not have proven anything."""


def mutate(text: str, old: str, new: str, *, what: str) -> str:
    """Replace `old` with `new`, refusing a substitution that changes nothing.

    Two ways a doctoring step silently proves nothing, both seen in practice:
    the anchor is absent (a reworded source, a copy-paste with different
    wrapping), or the replacement is identical to what was already there. Both
    raise here rather than returning the untouched text to a caller that is
    about to assert a guard "caught" it.

    `what` names the demonstration, so a failure says which proof collapsed
    rather than pointing at a helper.
    """
    if not isinstance(text, str) or not isinstance(old, str) or not isinstance(new, str):
        raise TypeError("mutate operates on text")
    if old == "":
        raise VacuousProbe(f"{what}: empty anchor would match everywhere and prove nothing")
    if old not in text:
        raise VacuousProbe(
            f"{what}: anchor not found in the source, so nothing was doctored and the "
            f"guard would have been asked about unmodified content"
        )
    result = text.replace(old, new)
    if result == text:
        raise VacuousProbe(
            f"{what}: substitution was a no-op — the replacement is identical to the "
            f"anchor, so the guard would have been asked about unmodified content"
        )
    return result


def assert_differs(before: str, after: str, *, what: str) -> None:
    """Assert a doctoring step produced a genuine change.

    For mutations built some other way than a substitution — regex edits,
    structural rewrites, deletions — where the same no-op risk applies.
    """
    if before == after:
        raise VacuousProbe(f"{what}: produced no change, so any check run against it proves nothing")
