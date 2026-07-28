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
| 5. No vacuous pins | 5 days | Fired (CR-16, the fifth of the cycle) | ~~Validated; the rate is falling.~~ **Corrected 2026-07-27 — this score was wrong.** A sixth instance appeared the same day (a hand-run red-first probe whose substitution did not match, so it mutated nothing and reported success), and re-counting the class across *all* surfaces rather than tests alone put it at **seven**: shipped tooling (the adapter harness's own vacuous-pass) and audit evidence (a `git diff` over a gitignored path) belong to it too. The rate was not falling; the class was under-counted because only test-side instances were being tallied. **Rule AMENDED, not retired — the demonstration must now ship with the pin.** See doctrine log P2-D1. |
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
