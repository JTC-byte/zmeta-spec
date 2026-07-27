# ZMeta After-Action Log

**Standing artifact. Accumulates one entry per audit/review cycle. Advisory /
non-normative.**

## What this is

A public, redacted record of *why* each audit cycle went the way it did — what
was found, what it cost in shape (not in raw figures), what worked, and what
changed in the process as a result. It exists so a contributor or an agent
arriving later can understand the reasoning behind a decision without having
lived through the cycle.

Operational cost figures and internal strategy are kept in a private companion
copy. **Nothing safety-relevant is redacted** — every defect, reproduction and
fix from a cycle is committed in that cycle's own records
(`docs/r1_11_full_stack_audit.md`, `docs/r1_11_fix_pass_findings.md`,
`docs/zmeta_doctrine_review_log.md`, and the closure probe). Hiding a defect
would violate the honesty gate the whole standard rests on; the redaction is
about cost and framing only.

The forward-looking methodology these entries feed is
`docs/zmeta_audit_playbook.md`.

---

## R1-11 — 2026-07-22

**Outcome: six release-blocking defects closed and independently verified;
release still HELD; a formalized audit cadence adopted for future cycles.**

### What happened

A prior cycle's own two verification passes had declared its work done. A fresh
full-stack audit of that held work found **six MAJOR blockers** it had missed —
non-finite values reaching the wire and CoT/TAK egress, a receive-loop crash
class, an authorization lint that passed a malformed policy, and a MAVLink
altitude fabrication — several of them defects that had survived multiple prior
cycles under a fully green test battery.

Two serious issues in *no* finding were also found and closed along the way: an
unauthenticated hang of the gateway receive loop from a small crafted datagram
(a CBOR value-sharing cycle), and a path that rewrote a not-a-number confidence
to maximum confidence and forwarded it.

The blockers were fixed, then the fixes were adversarially attacked, then the
findings from that attack were remediated and attacked again, then the
remaining findings were worked to doctrine. Six blockers verified closed by an
independent probe (17 of 17 reproductions no longer reproduce). Test battery
moved from 785 + 316 subtests to 1200 + 1021.

### What it cost, in shape

The cycle audited the whole repository in one pass and then fixed
open-endedly. Each fix round generated much of the next round's work: the final
adversarial pass found that most of its findings had been *introduced* by that
same round's fixes. Severity fell round on round, but volume did not, and the
introduction rate rose. The work stopped at the point where what remained was
design trade-offs — questions with no derivable answer — rather than defects.

### Why the process, not just the result, is the lesson

The test battery was green at *every* step, including the steps where fixes had
introduced new defects. The single discipline that kept the cycle net-positive
rather than net-negative was the **adversarial attack pass after every fix
set** — without it, introduced defects would have been committed as fixes. This
is recorded plainly because a green battery reading as "done" is exactly the
trap this cycle exists to warn against.

Honesty about the method: four test "pins" written this cycle initially
asserted nothing — they passed even with the fix they guarded reverted — and
were caught and rewritten. Two fixes closed a defect by introducing a quieter
one and had to be re-done. These are why the playbook now requires every pin to
be proven by reverting the fix and watching the specific assertion fail.

### What changed as a result

- **Audit by waves, not by blast.** The stack is now audited in bounded, ordered
  passes — kernel, gateway runtime, ingress, egress, release tooling, records —
  each with a fixed surface, one doctrinal lens, a defined objective, a
  fix-budget, and an exit criterion. See `docs/zmeta_audit_playbook.md`.
- **Fix-budget over exhaustion.** A wave fixes to a severity floor and defers
  the rest; if a fix round introduces too large a fraction of its own follow-up
  work, it stops and re-scopes instead of spawning another round.
- **The sustains are now standing rules**, not habits: commit at every
  boundary, resume from the tree, verify the battery yourself, mandatory attack
  pass, no vacuous pins, author-is-not-grader, and no minting a governed change
  inside a fix wave.

### Governance

No governed artifact — the locked semantics contract, the schemas, or the
policy vocabulary — was modified anywhere in this cycle, and no diagnostic code
was minted. Twenty-one points where the code or a proposed fix came under tension
with the guiding documents were recorded for separate adjudication in
`docs/zmeta_doctrine_review_log.md`, including the cases the documents resolved
cleanly. The release decision remains the maintainer's, and nothing in the
cycle has been published.

### Addendum — first live run of the refresh tier (2026-07-26)

The cadence this AAR produced fired for the first time: the mandated
fresh-eyes cold re-read of the held range ran after a three-day gap — nine
independent lenses over the wave partition plus the cycle's own failure-mode
lenses, adversarial verification of every candidate. It confirmed **30
distinct findings the cycle's author-passes had missed**, including two code
MAJORs that also exist in the published v1.1.16 assets (SAPIENT
negative-latency narrowing; CoT lateral-to-vertical error projection) and one
records-integrity MAJOR — the round-3 findings were never persisted, so the
open backlog existed only as counts. Findings record:
`docs/r1_11_cold_reread_findings.md`; landed with the doctrine-log
numbering-collision fix as `7eaea97` and `e524c8c`.

Verdict: the tier works as designed — the catch happened exactly where this
AAR predicted it would, on cold context. The run also taught a cost lesson:
the heavy fan-out consumed most of a plan session window in about 35 minutes.
Well-placed for this pass, ruinous as a default — adopted by maintainer
direction as playbook discipline 9 (heavy verification only where independent
eyes are load-bearing; everything else runs lean).
