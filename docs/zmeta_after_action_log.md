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
full-stack audit of that held work found **six MAJOR blockers** *(CR-24 correction 2026-07-27: the audit record grades one of the six MODERATE — “six blockers” is right, uniform MAJOR is not)* it had missed —
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
one and had to be re-done. These are why the playbook required every pin to
be proven by reverting the fix and watching the specific assertion fail.
*(Corrected 2026-07-28: that formulation was RETIRED by doctrine-log P2-D1 —
it describes a session act, which is precisely why it failed seven times. The
current rule is that a guard's red demonstration must be an artifact in the
repository, re-running in CI. Left in place with this note rather than
rewritten, per this log's dated-correction convention.)*

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
was minted. *(CR-04 correction 2026-07-27: true of the fix and disposition passes only — the cycle's earlier waves minted three additive `reason_code` enum entries in schema/policy and +6/−1 in contract §5.3; the public claim must scope to the passes.)* Twenty-one points where the code or a proposed fix came under tension
with the guiding documents were recorded for separate adjudication in
`docs/zmeta_doctrine_review_log.md`, including the cases the documents resolved
cleanly. The release decision remains the maintainer's, and nothing in the
cycle has been published.

*(Dated correction 2026-07-27: the held cycle was published as **v1.1.17** on
2026-07-27 after maintainer review, and **v1.1.18** followed the same day. The
"nothing has been published" statement above was true when written and is
retained as the record of that moment. The two code MAJORs the refresh-tier
addendum below reports as live in the published v1.1.16 assets are fixed in
v1.1.17.)*

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

---

## R1-11 closeout and the event-readiness cycle — 2026-07-27

**Outcome: the held cycle published as v1.1.17, an event-readiness cycle
published as v1.1.18 the same day, and the audit cadence proved itself at all
three tiers — including its own limit.**

### What happened

The R1-11 cycle had been complete and frozen for days, waiting on decisions
only the maintainer could make. Those were taken in a single sitting, and the
consequences ran: the vocabulary-boundary question (which had been parking
otherwise-mechanical fixes) resolved to "governed means the event model," the
compact fail-closed clause was approved and written into the mapping spec, and
a Class B schema constraint was approved for the branch whose missing enum had
made a whole class of self-contradicting timing events invisible.

Two defects the fresh-eyes re-read had found were fixed and are worth naming,
because both were live in already-published assets: an ingress path where a
malformed latency declaration could *narrow* an uncertainty bound rather than
widen it, and a projection that put a horizontal error measurement into a
field consumers read as vertical accuracy. Neither was theoretical; both would
have shown an operator a track that looked better-known than it was.

The second half of the cycle was deployment readiness rather than semantics: a
reference adapter built against real capture data, containers verified on two
processor architectures, a two-node deployment guide, and the command-evidence
gate — the piece that lets an operator's retasking automation cite the fused
track that motivated it, and lets the gateway refuse when that evidence was
never permitted to justify a command.

### What it cost, in shape

Two releases in one day is not the shape to plan for. It happened because the
first cut was the end of a long-held cycle and the second was a distinct body
of work that had no reason to wait behind it. The cost was concentrated in
re-verification: every cut re-runs the whole battery, re-baselines the
current-facing documents, and regenerates hashed artifacts, and doing that
twice in a day is most of a session on its own.

The other cost was self-inflicted and instructive. The first release's own
commit went red in continuous integration on two platform-dependent defects
that no local run could see, because the local interpreter and the build
machine resolve a codec dependency differently. Both were fixed within
fifteen minutes, but the lesson is structural: a long-held range accumulates
platform risk invisibly, because it never touches the one environment that
differs from the author's.

### Why the process, not just the result, is the lesson

The adversarial attack pass after every fix set has been this repository's
most load-bearing discipline. This cycle measured its limit precisely. Before
the second cut, a fresh-eyes review read the whole post-release range as one
surface and found thirteen further defects — and **three of them had already
survived their own wave's adversarial attack**. Each of the three was an
interaction that no single wave could see from inside itself: a fail-open
created by two bounds of different kinds meeting, a configuration typo that
reverted a knob to its permissive default with every lint green, and a value
screen applied to some emission paths but not their siblings.

That is not a failure of the attack pass. It is the discovery that
per-change review and whole-range review catch different classes, and that a
release cut needs both. The playbook's cut tier now says so explicitly.

One more result belongs in the record because it is uncomfortable: a
deployment guide written in this cycle documented a wire path that could not
work — two nodes configured exactly as written would have passed nothing
between them. It was caught by the pre-cut review, not by any test, and it
had never been executed end to end by anyone. **A document that has never
been run is a hypothesis.**

### What changed as a result

- **The cut tier is now a whole-range fresh-eyes review**, at release stakes,
  rather than a replay of the wave passes.
- **The doctrine log's lifecycle fired for the first time**: eight terminal
  entries were archived to one-liners, and three tensions that had recurred to
  the threshold were forced out of indefinite OPEN status and put to the
  maintainer as decisions rather than left to drift.
- **Every standing rule was scored** against this cycle's record (playbook,
  "Rule scoring"). None scored out; the one that has never fired is named as a
  watch-item rather than quietly kept.

### Governance

The locked v1.0 kernel is unchanged. The governed changes in this cycle — a
normative clause in the compact mapping and one additive Class B schema
constraint in the experimental v1.1.0 branch — were each adjudicated by the
maintainer in a pass separate from the work that surfaced them, which is the
protocol this log exists to enforce. Both releases are published
checksums-only. Open tensions, deferred findings, and the items that remain
gated on hardware or live tooling are recorded in the doctrine review log, the
cold re-read record, and the handoff — not in this entry, and not only in
commit messages. *(Corrected 2026-07-28: this became false during the v1.1.19
cut — see the CHANGELOG's [1.1.19] entries. It is true again as of that
reconciliation.)*
