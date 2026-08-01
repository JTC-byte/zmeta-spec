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

---

## The v1.1.19 cycle — 2026-07-28

### What happened

The cycle opened on a report from outside. A fielded deployment advancing its
ZMeta pin found that the published v1.1.17 and v1.1.18 trees carried a README
bullet asserting "No schema, policy, or event-vocabulary changes," which was
true of v1.1.16 and false of both releases that inherited it.

The fix for that defect became the cycle's main lesson. A content-currency
guard was built, and an independent panel showed it accepted the exact bullet
it was written to reject after two one-word edits. A redesign followed, and a
second panel found four more defects in it. The rule that tried to judge
whether prose described the right release was then removed rather than patched
a third time, because judging that is not reliably machine-checkable. What
survives is the part two panels confirmed sound: a governance sentence computed
from the release manifest and required verbatim.

Six independent panels ran across the cycle. The findings that mattered most
came from the lens with the least obvious value, a first-run walkthrough of the
documented getting-started path. It found that the stock two-node deployment
delivered zero events, that the "adapter in about an hour" claim contained an
undocumented 30 to 90 minute wall, that contract hashes differed between
Windows and Linux clones of the same commit in two independent ways, and that
the documented development install produced a broken environment. All were
long-standing. The hash defect dated to the repository's first commit.

An ADS-B ingress adapter was then built against real decoder output. It shipped
on the locked kernel with nothing minted, and produced three findings recorded
as doctrine-log cycle A1: places where a real thing cannot be expressed in the
current alphabet, each with a second instance elsewhere in the repository.

### What it cost, and where

Rework concentrated in one place. The content guard went through three designs.
Nothing else in the cycle went round more than once, and no test, fixture or
conformance expectation regressed at any point.

The distinction that explains it: work driven by an observed failure converged,
because the defect pool was finite and each fix was verifiable by re-running
the thing that failed. Work driven by an anticipated failure did not. Every
long-standing defect found in this cycle came from the first kind. Every round
of rework came from the second.

A second pattern accounted for most of the late findings. Claims about the code
lived in three or four documents and were corrected in one or two. At one point
three places in a single commit carried three different counts of the same
quantity. The verification pass on the closeout found the same shape recurring
inside the closeout that had recorded it as a watch item.

### The finding worth carrying forward

Every valuable finding in this cycle came from outside the working loop: a
downstream consumer advancing a pin, independent reviewers, a first-run
walkthrough, and a reader's reaction to the README's writing style. None came
from re-reading work already done, and a great deal of re-reading was done.

The governance apparatus was measuring itself. It is well developed, and it did
not surface any of the defects above. Contact with use did.

### What changed as a result

- **Playbook discipline 10**, adopted by maintainer direction: validate the
  assumption live before hardening it, and where that is impossible, record the
  question rather than build the defence. `docs/zmeta_live_test_checklist.md`
  holds those questions in a form a deployment can answer, including whether
  anyone needs calibrated power and whether anyone misses the positions the
  standard currently discards.
- **When a claim enumerates, generate it.** Applied to the governance sentence
  and the dist bundle's tool list. A third candidate, the conformance flag
  list, remains hand-typed.
- **Documentation claims are bound to the tree by test** where the failure was
  dangerous. A check now requires any document naming a config file and a
  profile to agree with that file. It found a fifth instance on its first run
  that neither the author nor an independent reviewer had found by reading.

### Governance

The locked v1.0 kernel is unchanged and nothing was minted. Three alphabet gaps
were recorded with recommendations and left for maintainer adjudication. The
recommendation in each case is a declaration rather than a new subtype:
constrain the meaning of a datum, not the category of its source.

One tension is recorded here rather than in the doctrine log because it
concerns the log itself. The governance apparatus grew again this cycle: three
new doctrine entries, a new discipline, a new standing artifact, two new
checks. The project's stated goal is a small alphabet that can be adopted
quickly, and design gate 7 binds the guiding documents as much as the kernel.
The apparatus is now large relative to the thing it governs, and the Lifecycle
rules exist for exactly this. They may warrant firing more aggressively than
the recurrence threshold strictly requires.

---

## Addendum — the v1.1.19 publication session, 2026-07-28

The cycle above closed with v1.1.19 prepared and a recommendation to tag. This
records what happened between that recommendation and the published release,
because most of it was not the tag.

### The cut was made twice, and the second attempt is the one that shipped

The first tag was created before the publish-path validations had been run.
Running them afterwards found `validate_release_package.py --package-dir` — the
command this release's own body publishes — failing on a package built at the
prepare commit against a manifest that had moved four hours later. The battery,
the kernel gate and CI all run `--templates-only`; only `--package-dir` compares
the package's recorded hashes against the live manifest.

Tagging is what makes checksums immutable here, so `sign_release_artifacts`
refused to rewrite them and the stale package could not be corrected in place.
That refusal is the only reason it did not ship. The tag was deleted before
anything was published, the package rebuilt, and the cut redone.

**The durable rule: run every publish-path validation before the tag exists.**
Specifically `--package-dir` and `sha256sum -c`, not just the battery. The
ordering is not a preference; the tag changes what is still fixable.

### Three instances in one day of the same shape

A stronger check existed and something cheaper ran in its place.

- `--templates-only` stood in for `--package-dir`, so a stale package acquired a
  pinned checksum.
- A manual checklist stood in for a machine check, so the cut sat with only its
  release notes — no validation report, no checksums — through a validating
  manifest, a validating package, a green battery and green CI.
- `pattern: "Z$"` stands in for `format: date-time`, so `event.ts` is
  unconstrained beyond a trailing `Z` (X1-01).

Two of the three were invisible to every automated gate. Both of the closable
ones were closed by checks rather than by checklist items. The third is
escalated, because closing it changes what validates.

**Recorded as an observation, deliberately not minted as a discipline.** The
tension at the end of the previous entry — that the apparatus is now large
relative to the thing it governs — applies with full force to a rule proposed on
the day its evidence appeared. It earns promotion by recurrence or not at all.

### What the outside produced, again

Every finding in this session came from outside the working loop, which is now
the fifth consecutive time that has held. An outside reader's reaction to the
README's prose drove a 40-file voice pass. A sibling repository's offhand remark
about JSON Schema `format` semantics found X1-01 in our kernel. Running the
documented first-run command rather than the test suite found the stale package.
None came from re-reading work already done, and re-reading was done.

The corollary is uncomfortable and worth stating plainly: the governance
apparatus measured itself as green throughout, and was green, and none of that
green was evidence about the three defects that mattered.

### Method note: a control is not optional

Four probes this session passed for the wrong reason before a control caught
them — three of mine on the `event.ts` question, and one of the consumer's on
the same claim, from the other side, within the hour. In every case the failing
output was indistinguishable from the output a correct refusal would produce.
Only a known-good control plus an assertion that the mutation was not a no-op
separated the claim from its negation.

### Checkpoint addendum — what landed after the closeout

Three commits landed after the session closeout, which is worth recording as its
own fact: a closeout is a line drawn at a moment, not a guarantee that the moment
holds. All three came from the cross-repo channel continuing after both sides had
said nothing was outstanding.

**The most useful of the three was a correction against the correcting party's
own interest.** An entry here credited the fielded consumer with finding a test
constraint that was actually found on this side, and the wording they had
proposed violated that constraint — so the queued fix would have turned a test
red at the next cut, logged against the wrong author. They checked their own
credit and sent it back.

Two rules came out of it. Theirs: **credit is a claim too.** Every verification
discipline built during this cycle points outward at claims that cost something —
a finding against the code, a correction against the record. Attribution in one's
own favour is the single class where the incentive runs the other way, which
makes it the only one where nobody else does the checking.

Ours, named against ourselves because it is a defect in how records get written
here rather than a slip: **an invented provenance is more convincing than the
truth, which is why it survives review.** A stale claim looks stale. A fabricated
attribution looks well-sourced, and reads better than the accurate version, so no
reviewer flags it. That is a different failure from staleness and needs its own
guard, which for now is a habit: when writing "X found" or "per X", check that X
did.

**On the finding-source measurement in the entry above**, the consumer improved
it and the improved version is the one to keep: *a second party reading your work
is the highest-yield finding source available, and it does not require them to
audit you.* Four of the five outside findings arrived as ordinary working traffic
— a remark, a question, a control someone ran for their own reasons, a
correction. None was commissioned. A survey-the-ecosystem rule buys the expensive
version of something that was already arriving free. The clause that makes it
repeatable is that nobody was auditing.

## The simulation-rep cycle — 2026-07-30

A cycle with no audit in it. The operator asked for internal reps while field
feedback was pending, with one constraint that shaped everything: fix a real
break, and for anything that is an assumption of behaviour, record it with the
live validation that would settle it instead of building on it. The stated
reason was that working from assumptions, without touching the code, and
trusting what a log said rather than letting it point at what to check, had been
expensive before.

### The result that justifies the cadence

Running the shipped deployment found two breaks that reading it never had, and
neither was subtle once observed. A containerized node forwarded both its output
streams to the container's own loopback, so a gateway reporting `recv=722
fwd=722` delivered nothing a host could read, and no error was raised because
the send succeeded. The two Compose files both bound the same host port, so the
pair could not come up together at all.

Neither is visible in a code review. Both are obvious in one run. That is the
whole argument for reps as a tier, and it is worth stating plainly because the
repository already had a green battery, green CI, and a documented wire check
that could not pass against its own containers.

### Controls-first paid three times, and each time against us

Every rep had its pass and no-op criteria written before the run. Three
measurements failed those criteria and would otherwise have been reported as
findings:

- A gateway was reported as "did not come up" because its startup banner sat in
  a block-buffered pipe. The process was healthy and listening. The shipped
  Compose files already run `python -u` for exactly this reason; the harness did
  not, and a live gateway read as a dead one.
- A throughput run reported 17% delivery. The generator was cycling a corpus
  verbatim, so it was measuring duplicate suppression rather than capacity. The
  same property is why `tools/replay.py --loop` forwards nothing after its first
  pass, which is now documented.
- A four-case command-evidence corpus failed in all four cases, including the
  two that had to pass. The cause was unrelated to what was being tested: the
  node had not published `TIME_STATUS`.

The third is the instructive one. Case A alone would have "confirmed" that the
command-evidence gate refuses a prohibited-parent citation. It does refuse it,
which is what makes the near miss worth recording: the right answer was reached
for the wrong reason, and only the control that had to pass revealed it.

### The finding that matters most for a live event

CoT projects `STATE_EVENT` only. An ingress adapter emits `OBSERVATION_EVENT`.
So a sensor wired through the documented topology produces valid ZMeta and an
empty map, and the shipped example corpus contains a `STATE_EVENT`, so the
documented pre-event rehearsal passes and the real sensor then shows nothing.

The general form, logged as SIM1-03: **a fixture chosen to demonstrate every
feature is not a fixture representative of the input.** The example corpus is
deliberately one of each event type, which makes it a good conformance sample
and a misleading smoke test. It is the vacuous-verification family one level
out, where the check passed for a reason unrelated to what the operator was
about to do.

### What the fix taught, which was more than the fix

Closing that gap for broadcast-identity sources meant deciding between two
routes to a `STATE_EVENT`, and the decision was made by running into each
constraint rather than by reading the policy and reasoning:

- a state citing an observation is refused, `LINEAGE_PARENT_TYPE_INVALID`;
- a sensor producer attempting to declare a track is refused,
  `PRODUCER_NOT_ALLOWED`;
- external promotion carries no requirement on the `state-projector-*` wildcard,
  so stripping the entire evidence block changed nothing observable.

Fusion was the honest route and also the one needing no invented lineage, since
`FusionPayload.members` is `minItems: 1`. Two attempts failed before the working
one, and that is why the answer is trustworthy rather than merely plausible.

Underneath it sat a smaller finding with a wider shape. The kernel requires
`confidence` on both emitted event types, and a cooperative broadcast has none
to give: `nac_p` and `sil` are accuracy and integrity, not the probability that
a claim is true. So the value has to be asserted by the operator, and the
component refuses to construct without one. Deriving it from `sil` was rejected
because that mapping is a modelling decision nobody has adjudicated, and
inventing it inside an adapter is how a private dialect starts.

### A rule that fired and was not honoured

The doctrine log's lifecycle says a tension must reach a terminal status on its
third recurrence. X1-02, a weaker check standing in for a stronger one, is at
five instances across two repositories and is still OPEN, held there by a
detection question described as answerable in an afternoon and not yet started.

That is the rule working as an instrument and being overridden by judgement,
which is worth naming rather than quietly repeating. The honest reading is that
the entry is not waiting for more evidence; it is waiting for an afternoon.
Either the question gets answered or the entry goes terminal without it, and
carrying it open through another cycle is the option that should stop being
available.

### On adding tooling to a standard

The harnesses were committed on the operator's instruction, alongside his own
caution: operational tooling is invaluable and a data standard whose repository
accumulates it stops being readable as a standard. Both are true, which is why
it went into the log as SIM1-04 rather than being settled on the day.

The move that made deferring honest was making the boundary structural. A test
asserts that nothing governed imports or invokes anything under `tools/sim`, so
the dependency runs one direction only and extraction stays a directory move.
Deferring a decision is only free when you have paid for the option to reverse
it, and this is what paying for it looks like.

That test also earned its keep immediately. Its own detector-fires check caught
a gap in the detector: a Windows path in Python source carries an escaped
separator, and the first pattern matched only a single one, so a real dependency
written that way would have passed unnoticed.

## Addendum — the external-review session, 2026-07-31

An outside agent produced a comparative survey of ZMeta against SAPIENT, OGC
O&M/SensorThings, CloudEvents, C2PA, PROV-O, in-toto/SLSA, ODCS, FHIR and the
NATO STANAGs, without access to this repository. The operator's framing was that
it should expose gaps rather than redirect effort. That framing held, and the
most useful thing it produced was a correction to us.

### The best result was the survey being wrong in the same direction we were

The survey concluded ZMeta's uncertainty handling is thin. The previous day's
rep had independently reached the same conclusion by watching a track render
with CoT's unknown-accuracy sentinel. Two sources, two methods, one answer, and
the agreement made it feel settled.

Checking it instead of accepting it showed both were wrong. `ERROR_ELLIPSE_M` is
a registered, approved, schema-implemented and conformance-implemented extension
allowed on `STATE_EVENT`, on the v1.1.0 branch, carrying semi-major, semi-minor,
orientation and an optional probability level. Only the locked v1.0 kernel
carries none, which makes it an adoption-path question rather than a gap in what
the model can express.

The rule this earns, now on the entry: **when an external claim matches your
own, that is the moment to verify it, not the moment to stop.** Corroboration
requires independent checking, not independent arrival. Neither source had read
the extension registry.

### What survives fact-checking is worth more than what does not

Verified correct and acted on: classification and releasability are genuinely
unexpressible today, though reserved in the registry rather than unconsidered;
confidence is a single scalar; malformed `event.ts` validates; the conformance
apparatus lacks a third-party programme rather than lacking machinery.

Verified wrong: the head-to-head framing against SAPIENT, since this repository
ships a complete bidirectional SAPIENT bridge and treats it as a mapped format;
and the recommendation to rebase on CloudEvents, whose required attributes
measure 134 bytes bare and 168 with `time`, against a Profile L compact event
that measured 98 to 150 in a 240-byte budget. The envelope is larger than the
event it would wrap.

The asymmetry is the lesson about outside review generally. A reviewer without
stack access finds real gaps and misjudges posture, and both halves are useful
provided you check which is which rather than accepting or rejecting wholesale.

### A citation collision, caught by grepping for our own claim

The doctrine cycle opened the previous day as `S1-01` through `S1-05` collided
with the historical `S1-01A` through `S1-19` work-item series, which includes a
completed item also called S1-05. A log whose value is that entries are citable
cannot carry two meanings for one identifier. Renamed to SIM1 one day old,
33 references, history untouched and verified per file.

It surfaced only because a search for one of our own overstated claims returned
files that had nothing to do with it. Worth generalising: **check for identifier
collisions before naming a cycle**, because the cost of the rename rises with
every citation.

### The check from the last closeout failed at this one

`test_changelog_keeps_up.py` was written on 2026-07-30 to close the records-lag
watch-item with a mechanism instead of another sweep. At this closeout it passed
while the CHANGELOG described none of the session's work, because it asserted
`[Unreleased]` was non-empty and the previous day's entries were still there.

This is not vacuity. The check had a mutation test, the mutation test was
honest, and it would have caught the case it was written for. It is X1-02: a
cheaper sibling of the right check, passing, and the passing is what stops
anyone asking. Committed by the author of the X1-02 note, one day after writing
it, which is the strongest evidence available that the class is not an attention
problem and will not be solved by trying harder.

Strengthened red-first the same session. It is also the sixth instance, and it
is why the terminal call on X1-02 is now the first item for the next session
rather than a standing question.

## Addendum — the pre-push cold read, 2026-07-31

The maintainer sequenced the held range as review, then push, then tier 2,
with the review run cold: eight independent lenses over the four unpushed
commits, producing context gone, every finding adversarially verified before
it counted. This is the discipline 6 experiment the last two closeouts said
the work needed, run before the push, which is the last point it could change
anything.

### The result

The author's reading had this range clean. The cold panel returned 31
findings, verified 16 with none refuted, and three were MAJOR, all in the AIS
adapter the closeout had called pinned: message 27's not-available sentinels
carried as clean motion data, one poisoned timestamp killing a whole
`translate_stream` batch with an uncaught OSError, and a timing pin that a
fabricated sync claim satisfies. Fixed red-first the same session, 14 new
tests demonstrated failing before the fix.

### What generalises

- **Cold reading catches what careful authorship does not, and the margin
  here was three MAJOR on 728 new lines.** The v1.1.19 cycle showed it for a
  cut; this shows it for an ordinary feature commit. The strongest defect sat
  in behavior no test exercised, so re-reading the tests could not have
  surfaced it.
- **The sentinel class does not close instance by instance.** The adapter was
  written around the sentinel problem, documented it, and tested it, and it
  still carried the type-27 pair, because the standard defines sentinels per
  message type and the implementation checked per field. Closing the class
  means reading the standard's tables per type, next to the code that accepts
  each type.
- **The verify-what-agrees-with-you rule fired one level up.** The SIM1-05
  correction, itself a product of that rule, carried two false claims of its
  own: a failure mode described as silence that is loud on one path and
  fabricating on the other, and a v1.0 member spelling the v1.0 schema never
  defines. Both read as details of an already-verified story, so neither was
  checked.
- **Self-referential counts are a small, distinct class.** "Three commits are
  unpushed" was committed inside the fourth; "six places" was hand-counted
  inside the paragraph applying the moving-fact rule. Where a count moves
  with the tree, generate it or date it to a named tree.

### What it cost

Roughly 1.9 million subagent tokens across 24 agents for a four-commit range,
and the purchase was three MAJOR defects stopped short of origin plus five
record corrections. The depth priced out because the range contained a new
component; the two records-only commits contributed corrections, never
stoppers. That is a usable sizing rule for this tier: scale the panel to the
newest code in the range, not to the diff line count.

## Addendum — the live-readiness audit and its fix wave, 2026-08-02

Ten axes, each required to run its path rather than read it; the full result
set is the session's, the verdicts and gap queue are in the handoff and
CHANGELOG. Three process notes worth keeping:

- **Two instruments failed in the author's own hands the same day, both in
  the X1-02 shape.** A verification one-liner piped pytest through tail, so
  the shell reported the tail's exit code and printed the green marker over
  30 failures; reading the output caught it, the marker did not. And a bare
  `tools/build_release_manifest.py` run reset the manifest's identity fields
  to the tool's hardening-baseline defaults, which 30 release-currency pins
  caught on the next battery. The manifest tool's defaults are for the
  baseline; a mid-cycle rebuild must always pass the release identity
  explicitly. Both are the cheaper-check class: a green marker standing in
  for the thing it summarizes.
- **The content-currency guard fired for real for the first time.** The
  governed policy edit changed the machine-generated governance sentence,
  and the guard refused the stale README bullet until the regenerated
  sentence was carried verbatim. The P2-01 mechanism works under live fire.
- **The budget shape that worked:** the fan-out ran on a separate model
  budget with the orchestrating session reserved for judgment, synthesis and
  the governed edit. Nine axes plus a four-fixer wave landed inside one
  session that way. The banked-axis pattern (inline a completed axis's
  result as a literal, rerun only the rest) is what recovered two aborted
  runs without re-spending them.
