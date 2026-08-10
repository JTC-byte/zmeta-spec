# Release Notes Errata

Docs/advisory. Non-normative. Records content defects in published
release-notes files. Published release artifacts are never rewritten
(AGENTS.md release limits), so corrections live here, dated, with the
evidence that establishes the accurate state.

## v1.1.20: the X1-01 closure section credits a runtime layer that no-ops on the class it names

Recorded 2026-08-10. Found while verifying an external technical review's
claim that a malformed `event.ts` validates; the claim was stale for the
v1.1.0 branch and accurate for the locked v1.0 branch, and checking why led
here. Full entry: `docs/zmeta_doctrine_review_log.md`, cycle C1, entry C1-02.

`release/RELEASE_NOTES_v1.1.20.md`, section on the X1-01 closure, states that
the closure "lands at both lawful layers" and describes the second layer as a
gateway plausibility window that counts an implausible `ts` on every
`zmeta_version`.

The window is version-agnostic, as described. It also does nothing at all on
the malformed class the locked v1.0 branch still admits. `gateway/src/gateway.py`
parses the timestamp and returns before any comparison when the parse fails,
so an unparseable value is never measured against the horizon and never
counted. Verified against the shipped module rather than read from the source:

- `ts="garbageZ"` produces no warning and zero counted warnings.
- `ts="Z"` produces no warning and zero counted warnings.
- `ts="2020-01-01T00:00:00Z"`, a well-formed but out-of-horizon value,
  produces one warning, which is the behavior the section describes.

The accurate state of the shipped v1.1.20 tree is therefore narrower than the
published sentence. On the v1.1.0 branch the closure is real and schema-level:
the structural pattern rejects the whole corruption class. On the locked v1.0
branch, which was deliberately left untouched under the lock doctrine, a
malformed `ts` passed schema validation and produced no runtime diagnostic
either. The fail-closed behavior the section credits existed only in the
egress adapters, which refuse such events; anything consuming the forwarded
canonical event was unprotected and unwarned.

Corrected forward rather than by rewriting the published file: the gateway now
emits its existing implausible-timestamp diagnostic for the unparseable case,
with a detail distinguishing an unreadable timestamp from an out-of-horizon
one, and `gateway/tests/test_ts_plausibility_window.py` pins it. No new
violation code was minted, because the occurrence rule reserves new governed
vocabulary for a third instance and an unparseable timestamp is honestly
implausible.

For the current state of `ts` enforcement, the authoritative records are the
`$defs/utcDateTime` description in `schema/zmeta-event-1.1.0.schema.json`, the
Timestamp Handling section of `schema/README.md`, and cycle X1 entry X1-01 in
the doctrine log. The published release-notes file stays exactly as published.

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
