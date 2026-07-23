# ZMeta Audit & Review Playbook

**Standing artifact. Advisory / non-normative.** This governs *how* we audit and
review the ZMeta stack. It does not define conformance and does not replace
`AGENTS.md` or `spec/semantics-contract.md`. It complements the "How we work
here" section of `CLAUDE.md` with an operational cadence.

> **Draft, 2026-07-22.** Authored from the R1-11 after-action review. The wave
> partition and cadence model below are proposed and await the maintainer's
> confirmation. See the open decisions at the end.

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

## The fix-budget rule (the R1-11 change)

This is the specific antidote to the 74% introduction rate:

- **Bound the appetite by severity, not by exhaustion.** A wave fixes findings
  **at or above its declared severity floor** and no further. Everything below
  goes to a register (`docs/r1_11_fix_pass_findings.md` is the template) for a
  later, separately-scoped wave. Gate 7 applies to *scope*, not only to the
  stopping point.
- **Cap the introduction rate.** If a fix round's own attack pass finds that
  more than a set fraction of its findings were introduced by that round, the
  wave **stops and re-scopes** rather than spawning another fix round. R1-11's
  rounds went 7% → 56% → 74%; a cap around one-third would have ended the fix
  marathon a full round earlier.
- **Prefer revert to layering.** A defect introduced by a previous fix is
  usually cleaner to revert-and-re-derive than to patch. Patching three deep is
  how a codebase becomes unreasonable.

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

## Open decisions for the maintainer

1. **The wave partition** above is proposed along doctrinal seams. Confirm or
   re-cut it — you know the stack's natural boundaries best.
2. **The cadence trigger.** Three candidate models, not mutually exclusive:
   (a) *on-change* — a wave runs when its surface changes on a branch;
   (b) *full rotation before any release cut* — all six waves, in order,
   bounded; (c) *triggered deep-dive* — a wave escalates to a full pass when it
   finds a systemic issue. Which govern?
3. **The introduction-rate cap** — the specific fraction that stops a fix round.
   One-third is a starting proposal, not a derived number.
4. **The severity floor per wave** — do all waves fix down to the same floor,
   or does the kernel (W1) fix everything while the outer rings defer more?
