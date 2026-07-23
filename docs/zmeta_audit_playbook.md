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
5. **No vacuous pins.** Every pin is proven by revert-simulation *with a
   specific assertion* — watch it fail on the reverted tree, on the exact
   claim, not on `assertFalse(ok)`. Four vacuous pins slipped through R1-11
   before this was enforced.
6. **Author is not grader.** Closure is verified by a probe written by one
   party and executed by another (`docs/r1_11_closure_probe.py`).
7. **No minting; log the collision.** A fix that wants a governed change
   (a `reason_code`, an enum entry, normative text) implements what doctrine
   permits and records the tension in `docs/zmeta_doctrine_review_log.md`. It
   never decides a governance question inside a fix wave.

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
