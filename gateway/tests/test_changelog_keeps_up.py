"""Work that landed after the last release must be described in the CHANGELOG.

This exists because the same defect recurred four times across three cycles:
commits land continuously, the record surfaces reconcile at points, and the gap
between them is invisible until someone sweeps. The v1.1.19 rule scoring carried
it as a watch-item with a pre-committed disposition: *if it recurs again it wants
a mechanism, not another sweep*. It recurred at the 2026-07-30 closeout, where
three commits of user-facing work sat under an empty `[Unreleased]`.

THE INVARIANT, and it is deliberately weak in one specific way. If the worklog
says work happened after the newest released version's date, `[Unreleased]` must
say something. It does not check *what* it says, because no test can judge
whether prose describes the right work; that rule was tried twice on the
release-focus bullet and produced new holes both times. This forces a decision
and accepts any honest answer, including "no user-facing change this session",
which is itself the record worth having.

KNOWN LIMITS, demonstrated by the 2026-07-31 pre-push cold read and accepted
rather than discovered later. The check compares two hand-maintained dates, so
it is blind when both record surfaces lag together; a dated line with no prose
after it satisfies it; a future-dated typo satisfies it from then on; and it
skips for the rest of any release day. Each is the price of the one design
decision above: a test cannot judge prose, so it judges dates. The X1-02
terminal call owns whether that price stands.

BOTH SIGNALS ARE TREE-LOCAL. Nothing here reads git. CI checks out without tags,
so a check comparing against `git describe` or a tag would pass vacuously in CI
while failing locally, which is the same class one level up (doctrine X1-02).
"""

import re
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHANGELOG = ROOT / "CHANGELOG.md"
WORKLOG = ROOT / "docs" / "zmeta_refinement_worklog.md"

VERSION_HEADING = re.compile(r"^## \[(?P<version>\d+\.\d+\.\d+)\] - (?P<date>\d{4}-\d{2}-\d{2})\s*$", re.M)
WORKLOG_DATE = re.compile(r"^- Last updated:\s*(?P<date>\d{4}-\d{2}-\d{2})", re.M)
UNRELEASED_SECTION = re.compile(r"^## \[Unreleased\]\s*$(?P<body>.*?)(?=^## )", re.M | re.S)


def newest_released():
    text = CHANGELOG.read_text(encoding="utf-8")
    matches = list(VERSION_HEADING.finditer(text))
    assert matches, "no released version heading found in CHANGELOG.md"
    first = matches[0]
    return first.group("version"), date.fromisoformat(first.group("date"))


def worklog_date():
    match = WORKLOG_DATE.search(WORKLOG.read_text(encoding="utf-8"))
    assert match, "no '- Last updated: YYYY-MM-DD' line found in the worklog"
    return date.fromisoformat(match.group("date"))


def unreleased_body(text=None):
    text = text if text is not None else CHANGELOG.read_text(encoding="utf-8")
    match = UNRELEASED_SECTION.search(text)
    assert match, "no [Unreleased] section found in CHANGELOG.md"
    return match.group("body").strip()


def newest_dated_entry(body):
    """The newest '- YYYY-MM-DD' entry date in a section body, or None."""
    dated = [date.fromisoformat(m) for m in re.findall(r"^- (\d{4}-\d{2}-\d{2})", body, re.M)]
    return max(dated) if dated else None


class ChangelogKeepsUpTest(unittest.TestCase):
    def test_the_locators_still_find_what_they_expect(self):
        """Non-vacuity. A broken regex would make every assertion below trivial."""
        version, released_on = newest_released()
        self.assertRegex(version, r"^\d+\.\d+\.\d+$")
        self.assertGreater(released_on.year, 2000)
        self.assertGreater(worklog_date().year, 2000)

    def test_work_after_the_last_release_is_described_in_unreleased(self):
        _, released_on = newest_released()
        worked_on = worklog_date()
        if worked_on <= released_on:
            self.skipTest("no worklog activity after the newest released version")
        self.assertTrue(
            unreleased_body(),
            f"the worklog records work on {worked_on}, after the newest released "
            f"version dated {released_on}, but CHANGELOG.md [Unreleased] is empty. "
            "Describe it, or state plainly that the session made no user-facing "
            "change. Either is a record; silence is not.",
        )

    def test_the_newest_work_is_described_and_not_just_some_older_work(self):
        """The strengthening this check needed, and it needed it immediately.

        As first written this file only asserted [Unreleased] was non-empty. One
        day later a session added an adapter, corrected a doctrine entry and
        renamed a cycle, and the check passed because yesterday's entries were
        still sitting there. A non-empty section is a cheaper sibling of "the
        current work is described", and the cheaper one passing is what stops
        anyone asking. That is doctrine X1-02 committed by the author of the
        X1-02 note, which is why the stronger form is here now.
        """
        _, released_on = newest_released()
        worked_on = worklog_date()
        if worked_on <= released_on:
            self.skipTest("no worklog activity after the newest released version")
        newest = newest_dated_entry(unreleased_body())
        self.assertIsNotNone(
            newest,
            "CHANGELOG.md [Unreleased] carries no dated entry, so its currency "
            "cannot be checked. Entries take the form '- YYYY-MM-DD — ...'.",
        )
        self.assertGreaterEqual(
            newest, worked_on,
            f"the worklog was last updated {worked_on} but the newest dated "
            f"[Unreleased] entry is {newest}. The latest work is not "
            "described. Add it, or state plainly that the session made no "
            "user-facing change.",
        )

    def test_the_check_would_notice_an_empty_unreleased(self):
        """Mutation. The assertion above must fail on the state it exists to catch."""
        text = CHANGELOG.read_text(encoding="utf-8")
        emptied = UNRELEASED_SECTION.sub("## [Unreleased]\n\n", text, count=1)
        self.assertNotEqual(emptied, text, "the mutation did not apply, so this proves nothing")
        self.assertEqual(unreleased_body(emptied), "")

    def test_the_check_would_notice_stale_dated_entries(self):
        """Mutation, for the strengthened assertion. This is the exact state
        that beat the first version of this file: a populated [Unreleased]
        whose newest dated entry predates the newest work. As committed, the
        red demonstration for the strengthening existed only in a commit
        message, which is the session-act proof this repo's playbook forbids;
        this puts it in the tree.
        """
        stale = ("- 2026-07-30 — an adapter, a correction and a rename,\n"
                 "  all still sitting there from yesterday\n")
        newest = newest_dated_entry(stale)
        self.assertIsNotNone(newest, "the stale fixture lost its dated entry, so this proves nothing")
        self.assertLess(
            newest, date(2026, 7, 31),
            "the fixture must predate the work for this to prove anything",
        )
        self.assertIsNone(
            newest_dated_entry("prose without any dated entry at all\n"),
            "a dateless body must read as 'no dated entry', which the "
            "assertion above refuses rather than treats as current",
        )


if __name__ == "__main__":
    unittest.main()
