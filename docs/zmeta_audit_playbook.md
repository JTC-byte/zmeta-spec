# ZMeta Audit & Review Playbook

**Standing artifact. Advisory / non-normative.** This governs *how* we audit and
review the ZMeta stack. It does not define conformance and does not replace
`AGENTS.md` or `spec/semantics-contract.md`. It complements the "How we work
here" section of `CLAUDE.md` with an operational cadence.

> **Adopted 2026-07-22** from the R1-11 after-action review. The three-tier
> cadence, the MAJOR/MODERATE severity floor and the one-third introduction-rate
> cap are in force. The wave partition is provisional and under observation for
> the first few audits — see Status at the end.

## Why this exists

The R1-11 cycle audited the whole repository in one pass, then fixed
open-endedly across three rounds. It closed six serious defects that had
survived multiple prior cycles — but it also spent about thirteen continuous
hours, and each fix round generated much of the next round's work (the
adversarial pass after round three found that 74% of its findings were
introduced by that same round's fixes).

The lesson is not "audit less." The audit was high-value and cheap. The lesson
is that **an unscoped audit-and-fix is a shotgun**: no per-part objective, no
fix-budget, no exit criterion, so it runs until exhaustion rather than until
done. This playbook replaces the shotgun with **audit waves** — bounded,
ordered, intentional passes, each over one part of the stack, each with a
defined objective and a hard stop.

## The core rule: audit by waves, not by blast

A **wave** is one audit pass over **one part of the stack**, with:

- a **fixed surface** (an enumerated set of files),
- a **single doctrinal lens** (the design gate that part most has to satisfy),
- a **defined objective** (what "clean" means for this part),
- an **exit criterion** (how you know the wave is done),
- a **fix-budget** (how much may be fixed before re-auditing),
- and a declared **parallelism** (which other waves it may run beside).

You never open a wave you cannot state all six for. That single discipline is
what turns a blast into a cadence.

## The cadence: closeout, refresh, full audit

Reviews run continuously at three escalating scopes, so drift is caught as it
appears rather than accumulating into one giant pre-cut audit. The small
continuous passes are what make the large one cheap.

- **Closeout** — at the end of every session or change. Briefly touch
  *everything just changed* and confirm each change still fits the intent that
  drove it. Scoped to the working diff. First line of defence: a change is
  reviewed against its own purpose while that purpose is fresh.
- **Refresh** — at the start of every fresh session. The usual re-orientation
  on the repo generals and the logs of prior work, **plus** a fresh-eyes
  re-look at the *previous* session's changes to see whether any assessment
  shifts when context is rebuilt cold. A defect that looked fine to its author
  often does not survive a fresh reading — this is where that catch happens.
- **Full wave audit** — when a whole backlog item is complete (for example a
  finished adapter or integration, like the TAK work), before a release cut.
  The full six-wave pass. It is streamlined *because* closeout and refresh have
  already reviewed each change as it landed: the full audit confirms an
  already-reviewed stack rather than discovering an unreviewed one.

  **For a release cut, this tier runs as a fresh-eyes review of the entire
  post-previous-cut range as ONE surface, at release stakes** — not as six
  wave passes replayed. The question is not "is each wave sound" (the attack
  passes answered that as each landed) but "what does a cold reader see across
  the joins, and would any of it mislead a release decision or a downstream
  consumer?" Adopted 2026-07-27 on evidence: the v1.1.18 pre-cut review found
  13 verified findings in nine already-attacked commits, and **three of them
  had survived their own per-wave adversarial attacks** — a fail-open created
  by the interaction between a time-bounded cache and a cardinality-bounded
  index, a typo-fails-open gap in a new policy block, and a screen applied to
  some emit arms but not others. None was visible from inside a single wave.

The failure this prevents is R1-11's: a whole cycle of change reaching a single
audit at once, with no continuous review behind it. We generally stay within a
scope and do not jump around, so "touch everything recently changed" stays
small and bounded in practice.

## The wave partition

The stack divides along its own authority order and its honesty seams. Six
waves, ordered by authority (highest first):

| Wave | Surface | Doctrinal lens | Objective |
|---|---|---|---|
| **W1 — Kernel** | `spec/semantics-contract.md`, `schema/*.json`, `policy/*.yaml` | Gate 1 (alphabet), additive-only | No drift, no vocabulary growth, every change strictly additive and governed |
| **W2 — Gateway runtime** | `gateway/src/*.py`, `zmeta_compact.py`, `zmeta_cbor.py` | Gate 3 (no laundering), fail-closed | No non-finite/degraded/stale value reaches the wire clean; every error path refuses honestly; no unbounded traversal |
| **W3 — Ingress adapters** | `adapters/ingress/**` | Gates 2 & 3 (consumer-sufficiency, honesty) | No fabricated field, no laundered sentinel, uncertainty travels with the datum |
| **W4 — Egress adapters** | `adapters/egress/**` | Gates 4 & 5 (lossy projection, structure-authoritative) | A projection never gains certainty its source lacked; nothing load-bearing lives only in free text |
| **W5 — Release & tooling** | `tools/**`, `release/**` | Integrity, immutability | Manifests, hashes and identities are honest and reproducible; published checksums are immutable |
| **W6 — Records & currency** | `docs/**`, `README.md`, `CHANGELOG.md`, `examples/**` | Gate 5, claim-truth | Every stated number, claim and version literal is currently true |

**Ordering and parallelism.** W1 is the authority everything else conforms to,
so it runs first and alone. W2 depends on W1. **W3 and W4 are disjoint in
files and may run in parallel** with each other. **W5 and W6 are largely
independent and may run in parallel** with W3/W4. This directly answers the
R1-11 over-serialization cost: serialize only where surfaces actually overlap.

## The per-wave contract

Each wave runs the same shape:

1. **Scope-lock.** Enumerate the surface from the diff or the tree. State the
   lens and the objective. If you cannot, do not open the wave.
2. **Adversarial find.** Independent lenses attack the surface. Findings must
   anchor at `file:line` with a reproduction. Speculation is dropped.
3. **Verify.** Every candidate finding faces adversarial refutation before it
   is believed. A refuted finding is a result, not a failure.
4. **Fix within budget** (see below), or defer.
5. **Attack the fixes.** *Mandatory.* Every fix set is adversarially
   re-attacked before the wave closes — this is the discipline that made R1-11
   net-positive, and the battery being green does not substitute for it.
6. **Close or re-scope.** Meet the exit criterion, or record what remains and
   stop. Never roll straight into an unbounded next round.

## The fix-budget rule

The scope-discipline the R1-11 review found missing. Gate 7 binds *scope*, not
only the stopping point.

- **Severity floor: fix MAJOR and MODERATE; defer the rest.** A wave fixes
  findings at or above MODERATE and no further. MINOR and OBSERVATION findings
  are *recorded* to a register (`docs/r1_11_fix_pass_findings.md` is the
  template) and deferred to a later, separately-scoped wave — banked honestly,
  not ignored, not fixed inline. In R1-11 the low-severity tail is where much of
  the self-inflicted churn came from. *(Uniform for now; the kernel wave may
  warrant fixing everything, since even minor drift matters on a locked
  surface — under observation.)*
- **Introduction-rate cap: one third.** After a fix batch, the mandatory attack
  pass classifies each new finding as pre-existing or introduced-by-this-batch.
  If introduced findings exceed one third of the batch's total, the wave
  **stops, freezes, and re-scopes** rather than spawning another fix round.
  R1-11 ran 7% → 56% → 74%; a one-third cap ends it after the second round, and
  most of the third round's introduced defects are never created.
- **Prefer a known-good over a tangled knot.** When a fix has introduced a
  defect, revert to the last known-good and re-derive — do not patch the patch.
  Patience over forward momentum: there is no time crunch, and momentum in the
  wrong direction is worse than a deliberate restart. **A revert does not lose
  the context that produced it.** The failed attempt is reconnaissance — it
  showed where the ground gives way, and that hindsight travels forward from the
  known-good, so the second approach is better-informed than the first. Restart
  an effort entirely before tangling it further — but do not swing to the other
  failure and loop in endless optimization; the escape from both is a properly
  scoped objective, not more or less momentum.

## Standing disciplines (sustains — these are not optional)

Formalized from what demonstrably worked across R1-09, R1-10 and R1-11:

1. **Commit at every boundary.** Survived four usage-limit breaks and a full
   chat reset with zero lost work.
2. **Resume from the tree, never the transcript.** A clean working tree is
   orthogonal to partial application — a fix can be committed, green, and still
   half-applied. Verify order, not just presence.
3. **Verify the battery yourself.** In R1-11, twelve tests were red under the
   agents' reported "green" until the manifest was regenerated. Never relay a
   self-reported green.
4. **The attack pass is load-bearing, not ceremonial.** It caught every
   introduced defect the green battery did not.
5. **No vacuous pins — and the proof ships with the pin.** Every pin asserts
   the *specific* claim, never a bare `assertFalse(ok)` that some other gate
   could satisfy. **Amended 2026-07-27 (doctrine log P2-D1): the
   demonstration must be an artifact in the repo, not an act in a session.**
   Write a paired check that constructs the bad state and asserts the guard
   reports it, beside the guard, re-running in CI — a synthetic fixture, a
   doctored copy of the real content, a temporary root. Watching it go red in
   your working copy and saying so in the commit message is the practice this
   replaces: it is ephemeral (nothing re-runs it, so a pin that was honest in
   March goes vacuous in July when a new gate lands upstream of it and
   refuses first — with no signal), author-attested (discipline 6 applies to
   this claim class too), and it never verified the mutation applied at all.
   Use `gateway/tests/vacuity.py::mutate` when doctoring text — it refuses a
   substitution that changes nothing, which is precisely how one hand-run
   probe reported success having mutated nothing. **Seven instances forced this** — five test pins, one in shipped
   tooling, and one hand-run probe; the audit-evidence case is logged as
   adjacent to the class, not one of the seven (doctrine log P2-D1), including one
   vacuous pin inside the fix for a vacuous pin. Pre-2026-07-27 pins are not
   retro-fitted and must not be assumed non-vacuous.
6. **Author is not grader.** Closure is verified by a probe written by one
   party and executed by another (`docs/r1_11_closure_probe.py`).
7. **No minting; log the collision.** A fix that wants a governed change
   (a `reason_code`, an enum entry, normative text) implements what doctrine
   permits and records the tension in `docs/zmeta_doctrine_review_log.md`. It
   never decides a governance question inside a fix wave.
8. **Audit the doctrine; do not just follow it.** These rules are themselves
   scored on the cadence — age, times-fired, outcome — and a rule that stops
   earning its place is retired, not grandfathered. Tensions in the doctrine log
   reach a forced terminal decision after recurring (working value: three
   times), then archive. A log that only grows is a swamp. Lifecycle and scoring
   are defined in `docs/zmeta_doctrine_review_log.md` (Lifecycle).
9. **Scale verification to the pass, not the habit.** Heavy multi-agent
   fan-outs — independent lenses, adversarial refutation panels — are reserved
   for the passes where they are load-bearing: fresh audits, the refresh
   tier's fresh-eyes re-reads, and pre-cut verification. Records work, scoped
   fix waves, and adjudication support run lean. Adopted 2026-07-26 by
   maintainer direction, after the first refresh-tier run proved both halves:
   the heavy pass caught what three author-rounds missed, and it consumed most
   of a plan session window in ~35 minutes — well-placed there, ruinous as a
   default.

10. **Validate before hardening; otherwise write the question down.**
    Adopted 2026-07-28 by maintainer direction. A defence built against a
    failure nobody has observed is speculation, and speculation has no
    stopping point — one guard in the v1.1.19 cycle went through three designs
    and two independent panels before that was recognised. So: **live-validate
    the assumption before hardening it.** Where it cannot be live-validated,
    record it in `docs/zmeta_live_test_checklist.md` as a yes/no question a
    deployment can answer, and leave the code alone. Proactive hardening stays
    available where the defect is certain or the cost of being wrong is high;
    it is the exception, not the default. **"Nobody cared" is a complete
    result** and closes the item.
    The distinction that makes this operational: work driven by something
    that actually broke converges, because the defect pool is finite and each
    fix is verifiable by re-running it. Work driven by what might break does
    not. In the v1.1.19 cycle every long-standing defect — a two-node path
    that delivered nothing, an undocumented producer wall, platform-divergent
    hashes dating to the repository's first day — came from the first kind,
    and every round of rework came from the second.

## How this feeds the self-healing automation

The playbook is the orchestration layer over the primitives the repo already
carries:

- **Refresh-from-tree** — the resume discipline (2) is what lets a wave survive
  interruption and rebuild state from the repository alone.
- **Closeout** — a cycle closes out only when every wave has met its exit
  criterion or explicitly deferred; a half-closed wave reported as closed is the
  failure mode the fresh audit exists to catch.
- **Doctrine review log** — waves feed it; the maintainer adjudicates it as a
  separate pass (`docs/zmeta_doctrine_review_log.md`).
- **Contradiction / no-mint register** — the standing rule that keeps the locked
  kernel out of the reach of a fix's momentum.

Each wave is small enough to run, verify, and close inside one working session,
which is what makes the whole thing survivable when sessions are interrupted —
the property R1-11 proved matters most.

## Status

**Adopted 2026-07-22** (R1-11 after-action review):

- The three-tier cadence — closeout, refresh, full wave audit before a cut.
- The six-wave partition along doctrinal seams.
- Severity floor: fix MAJOR and MODERATE, defer the rest.
- Introduction-rate cap: one third.

**Under observation** — watch-items, not open questions; the cadence runs on the
adopted settings until observation says otherwise. Revisit after the first few
full audits:

- Whether the doctrinal-seam partition holds, or a wave needs re-cutting once
  real drift is seen. The first few runs are deliberately watched for this.
- Whether the kernel wave (W1) should fix everything rather than stop at the
  MODERATE floor, given it is small, locked, and drift-intolerant.

## Rule scoring — 2026-07-30 (the simulation-rep cycle)

**No rule scored out; one watch-item closed with a mechanism; one discipline
went unmet and that is the finding.**

| Rule / setting | Fired | Outcome |
|---|---|---|
| 1. Commit at every boundary | Continuously | Validated. Three commits, each pushed with CI green before the next began. |
| 2. Resume from the tree | Fired at refresh | **Prevented a wrong recommendation.** My own memory said the compact-mapping fail-closed clause was still a pending governed wave. The tree said it landed 2026-07-27. I nearly proposed it as the next line of business. |
| 3. Verify the battery yourself | Every commit | Validated, and it found nothing, which is the outcome it should mostly have. |
| 4. Attack pass is load-bearing | **Did not fire** | No adversarial pass ran this cycle. Its function was partly served by per-rep controls defined before each run, which caught three bad measurements. That is not the same instrument and should not be recorded as though it were. |
| 5. No vacuous pins; the demonstration ships with the pin | Fired three times | Validated. Every check added this cycle carries a control or a mutation proof, and one of them (`test_sim_boundary`'s detector-fires case) caught a real gap in its own detector on the day it was written. |
| 6. Author is not grader | **NOT APPLIED** | **The honest gap in this cycle.** No independent panel read any of this work. Everything here, including two deployment fixes and a new adapter category, is author-graded. The v1.1.19 cycle is the direct evidence for why that matters: an author-run pre-cut review produced a cut that looked ready, and independent panels then found the headline guard did not work. |
| 7. No minting; log the collision | Continuously | Validated. Five doctrine entries this cycle, nothing minted, locked kernel untouched, and two policy questions escalated rather than answered. |
| 8. Audit the doctrine | Fired at this closeout | Validated, and it produced the sharpest finding: X1-02 is past the N=3 threshold and still OPEN. |
| 9. Scale verification to the pass | Fired | Correct for the work and incomplete as a result. Lean was right for reps, where the value is in executing rather than reading. It is what left rule 6 unmet, so the two are the same decision seen twice. |
| 10. Validate before hardening | Fired repeatedly | **The cycle's spine.** SIM1-01, SIM1-02, SIM1-03 and SIM1-05 are all recorded with their live question rather than fixed, on the operator's explicit instruction. Two real breaks were fixed, and the line between the two categories held. |

**Watch-items.** (a) The one-third introduction cap has still never fired,
across yet another cycle. It is now the longest-standing never-fired rule and
the X1-03 caution applies directly: silence from a constitutional rule is not
evidence of uselessness, so do not prune it on that basis, but do stop citing it
as active machinery. (b) **Closed with a mechanism.** "Records surfaces
reconcile at points while commits land continuously" was carried with a
pre-committed disposition: if it recurs, build something. It recurred at this
closeout, where three commits of user-facing work sat under an empty
`[Unreleased]`. `gateway/tests/test_changelog_keeps_up.py` now asserts that
work recorded after the newest released version is described, and deliberately
does not judge what the description says. (c) **New: rule 6 went unmet.** One
cycle is not a pattern. Two would be, and the work most needing an independent
read is the work now sitting in front of a live event.

## Rule scoring — 2026-07-28 (the v1.1.19 cycle)

**No rule scored out; one added (10), one vindicated decisively (6).**

| Rule / setting | Fired | Outcome |
|---|---|---|
| 1. Commit at every boundary | Continuously | Validated. A very long cycle with four panels and several reversals; nothing lost, every state recoverable. |
| 2. Resume from the tree | Fired repeatedly | Validated. Reviewers working against a concurrently-edited tree flagged it themselves; holding writes while a panel read the tree was the right call each time. |
| 3. Verify the battery yourself | Every wave | **Prevented harm twice.** CI caught a carrier the local battery could not see, and one reviewer claim (a mutation-survival result) did not reproduce when I ran it — reported as measured rather than as received. |
| 4. Attack pass is load-bearing | Every wave | Validated, and its limit re-measured: internal attack passes did not catch that the cycle's headline guard was defeatable by two one-word edits. |
| 5. No vacuous pins; the demonstration ships with the pin | Fired (a further instance; the P2-D1 table stands at seven and was not extended) | **Amended last cycle, and immediately tested by instance 8 — the guard written FOR that doctrine was itself vacuous.** The amendment held: the paired in-repo demonstration is what a later panel used to prove the replacement worked. |
| 6. Author is not grader | Fired at the pre-cut tier | **Validated decisively; the single strongest result of the cycle.** The author-run pre-cut review produced a cut I would have called ready. The independent panel then found the headline feature did not work, a silent-corruption bug that shipped through every green gate, bundle-coverage gaps, and stale records. Four author passes had not found any of it. |
| 7. No minting; log the collision | Continuously | **Validated hard.** Three alphabet gaps found (cycle A1) and the locked kernel untouched; nothing minted, everything recorded with a recommendation. |
| 8. Audit the doctrine | Fired at this closeout | Validated. Produced discipline 10 and this scoring pass. |
| 9. Scale verification to the pass | Fired, with an error | **Partially failed, my error.** I cut a five-lens panel to three on a budget assumption that was wrong, and the maintainer corrected it. The lens I dropped and later restored (first-run experience) is the one that found the release's worst defect. Lesson recorded: scope a pass by whether independent eyes pay, never by a guess about budget. |
| 10. Validate before hardening | Adopted this cycle | New. See the discipline and `docs/zmeta_live_test_checklist.md`. |

**Watch-items carried forward.** (a) The one-third introduction cap has still
never fired — now several cycles without firing; ask again whether the severity
floor and small-wave discipline are doing all the work. (b) **"When a claim
enumerates, generate it"** is new and unscored: it removed a defect class twice this cycle (the conformance flag list is a third candidate, still hand-typed)
times this cycle, but it has not yet been tested by someone adding a fourth
enumeration. Watch whether it is reached for, or forgotten. (c) The records
surfaces still reconcile at points while commits land continuously — this
closeout found five unreconciled commits including the release's largest
addition, which is the third instance this cycle. If it recurs again it wants a
mechanism, not another sweep.

## Rule scoring — 2026-07-27 (the v1.1.17 / v1.1.18 cycle)

Reconstructed at review time from the record, per the doctrine log's Lifecycle
("Rules"). **No rule scored out; one was amended, one added.**

| Rule / setting | Age | Fired | Outcome |
|---|---|---|---|
| Three-tier cadence | 5 days | **All three tiers fired** | Validated. Refresh caught 30; the pre-cut range review caught 13 (3 of them attack-survivors); this closeout caught 36 records actions. Each tier caught what the tier below it structurally could not. |
| Six-wave partition | 5 days | Used to scope every wave this cycle | Held. Not re-cut. The pre-cut tier now runs the range as one surface (above), which is a tier change, not a partition change. |
| Severity floor (MAJOR/MODERATE) | 5 days | Every fix wave | Validated. The deferred tail stayed deferred and stayed recorded; nothing below the floor was fixed inline, and the banked items (VW-01..17) are re-derivable. |
| One-third introduction cap | 5 days | Measured every wave; **never tripped** | Validated by not needing to fire: the worst wave introduced 1 MODERATE-or-above across nine clusters. That is the cap working as a discipline, not a dead rule — the measurement is what kept the batches small. |
| 1. Commit at every boundary | 5 days | Continuously | Validated. Two publishes, several interruptions, zero lost work. |
| 2. Resume from the tree | 5 days | Fired at the post-cut sweep | **Prevented harm.** Verifying the tree after interrupted edits found two defects (a stranded parenthesis, a stray lint directive) that no test could see. |
| 3. Verify the battery yourself | 5 days | Every wave | Validated. Agent-reported green was wrong at least twice (stale manifest hashes both times). |
| 4. Attack pass is load-bearing | 5 days | Every fix wave | **Prevented harm repeatedly** — and its limit was measured this cycle: three defects still reached the cut, which is what the amended pre-cut tier now covers. |
| 5. No vacuous pins | 5 days | Fired (CR-16, the fifth of the cycle) | ~~Validated; the rate is falling.~~ **Corrected 2026-07-27 — this score was wrong.** A sixth instance appeared the same day (a hand-run red-first probe whose substitution did not match, so it mutated nothing and reported success), and re-counting the class rather than tests alone put it at **seven**: five test pins, one in shipped tooling (the adapter harness's own vacuous-pass), and one hand-run probe. *(Composition corrected 2026-07-28 to agree with doctrine log P2-D1's table: the `git diff`-over-a-gitignored-path case is adjacent to the class, not one of the seven. The count was right; the composition was not.)* The rate was not falling; the class was under-counted because only test-side instances were being tallied. **Rule AMENDED, not retired — the demonstration must now ship with the pin.** See doctrine log P2-D1. |
| 6. Author is not grader | 5 days | Every wave (separate attacker/verifier agents) | Validated. |
| 7. No minting; log the collision | 5 days | Fired continuously | **Validated hard.** Across ~33k inserted lines the only governed additions were the ones the maintainer adjudicated in a separate pass. |
| 8. Audit the doctrine | 5 days | Fired at this closeout | Validated on first use: the log's own N=3 rule forced three entries to terminal status that would otherwise have drifted. |
| 9. Scale verification to the pass | 1 day | Fired every task since adoption | Validated. Heavy for audits/re-reads/pre-cut; lean for records and scoped waves. |

**Watch-items carried forward.** (a) The attack pass cannot see cross-wave
interactions — measured, and now covered by the amended pre-cut tier; watch
whether that tier keeps catching attack-survivors or whether the rate falls to
zero (either result is informative). (b) The one-third cap has never fired;
if it still has not fired after several more cycles, ask whether the floor and
the small-wave discipline are doing all the work and the cap is documentation.
(c) **The scoring pass itself is a claim and can be wrong.** Rule 5 was scored
"validated, the rate is falling" here and was corrected the same day on new
evidence. The lesson is not that the scoring is unreliable — it is that a
score derived from *one surface's* instances will read as improvement when the
class is simply being counted narrowly. Score a rule against every surface its
failure mode can appear on, not just the one it was written for.

**Amendment log for this table.** Rule 5 amended 2026-07-27 (demonstration
must ship with the pin — doctrine log P2-D1). Recorded here rather than by
rewriting the header summary above, which describes what the original pass
concluded and should stay as it was written.

**First firing (2026-07-26, refresh tier):** validated. The mandated cold
re-read of the R1-11 held range — nine lenses, adversarial verification —
confirmed 30 distinct findings the cycle's own author-passes had missed,
including two code MAJORs also present in the published v1.1.16 assets and
one records-integrity MAJOR (`docs/r1_11_cold_reread_findings.md`). The catch
happened exactly where the cadence predicted: on cold context, after a gap.
Cost observation from the same run produced discipline 9.
