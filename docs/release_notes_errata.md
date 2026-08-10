# Release Notes Errata

Docs/advisory. Non-normative. Records content defects in published
release-notes files. Published release artifacts are never rewritten
(AGENTS.md release limits), so corrections live here, dated, with the
evidence that establishes the accurate state.

## v1.1.20: the lock-restoration section describes a reversed state as final

Recorded 2026-08-09. Found by a full-register sweep of the repository's
open-item surfaces; previously unrecorded anywhere in the tree.

`release/RELEASE_NOTES_v1.1.20.md`, section "The lock has a birth
certificate, and the schema matches it", narrates the v1.0 schema
restoration in its mid-cycle form:

> The restoration removes the block, embeds the historical
> record verbatim in a test that proves all three facts (the record
> validates under restored v1.0, the vocabulary still binds under 1.1.0, the
> block is gone), and re-pins the byte-identity anchor at the restored
> bytes.

Two of the three parenthetical claims, and the framing sentence, describe a
state that was reversed before the release was cut. The accurate state of
the shipped v1.1.20 tree, each point generated from the tree rather than
asserted:

- `git diff v1.1.19..v1.1.20 -- schema/zmeta-event-1.0.schema.json` is
  empty. The locked v1.0 schema is byte-identical across the release. Two
  commits inside the range touched the file and net to zero: the
  2026-08-02 restoration (`69a14a7`) removed the subtype consistency
  block, and the 2026-08-03 adjudication (`0e0f32e`) reversed that
  removal, because the baseline the restoration had returned to was the
  premature April stamp, not the lockdown audit.
- The `eventSubtypeConsistency` block is present in the shipped v1.0
  schema. `gateway/tests/test_v1_lock_baseline.py` pins it as contract law
  (contract section 7.3; the test's own words: "the schema block enforces
  it and stays") and anchors the schema's byte identity at the shipped
  bytes, block included.
- The pre-lock record embedded in that test does not validate under the
  shipped v1.0 schema, and the test asserts that it must not
  (`test_the_pre_lock_record_stays_outside_the_lock`). The published
  sentence says the record validates; accepting it would mean the April
  stamp had quietly become the baseline again.
- `CHANGELOG.md`'s `[1.1.20]` section records the sequence correctly: the
  2026-08-02 restoration entry carries the annotation "[Reversed
  2026-08-03 by the entry above ...]" and is left as written because it
  records what was believed and done at the time.

What the published section gets right: the lock provenance note exists in
the contract, the historical record is embedded verbatim in a test, and
the byte-identity anchor was re-pinned. What it inverts is which baseline
won. A reader of the published notes alone would conclude the subtype
consistency block is gone from v1.0; the shipped schema keeps it, and the
test suite fails if it is removed.

For the lock's final state, the authoritative records are
`gateway/tests/test_v1_lock_baseline.py` and the `[1.1.20]` section of
`CHANGELOG.md`. The published release-notes file stays exactly as
published.
