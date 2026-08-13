# ZMeta Doctrine Review Log

**Standing artifact. Accumulates across cycles. Advisory / non-normative.**

## How to read this log

Entries are point-in-time records. Each body describes the repository as it
stood when the entry was written, and later cycles append rather than rewrite,
because rewriting a process record falsifies what was true at the time. The
status marker on an entry's heading is the authoritative current state: a body
that describes a defect in the present tense under a terminal status (CHANGED,
MINTED, HELD-FIRM, DROPPED) is describing a past state that has since been
resolved. Reading the open entries as an inventory of current defects will
systematically overstate what is broken; C1-09 records an external review that
made exactly that error. For current state, consult the CHANGELOG, the release
notes, and the conformance corpus at the tag you are evaluating.

## What this is

A record of every point where the guiding documents came under real pressure —
**including, deliberately, the cases where the documents won.**

ZMeta's semantic kernel is locked, and the governance apparatus exists to
enforce that lock. But a doctrine that is only ever enforced and never
re-examined closes itself off from evolution, which is its own failure mode.
This log is how both things stay true at once: the kernel stays protected in
the moment, and the guiding documents stay under continuous review.

## Why the wins are logged too

The value of this log is **not** any individual verdict. It is the **pattern
over time**.

A single tension resolved in doctrine's favour is evidence the doctrine is
working — noise, not signal. The same doctrine point taking pressure across
several cycles is signal that it may need to evolve. **Recording only the
unresolved cases destroys exactly that signal**, because it removes the
baseline that makes an outlier recognizable.

So the entries below are mostly expected to read "the guiding document was
right." That is the point, not a defect in the log.

## The bar for changing a guiding document is high

Both failure modes are real, and they pull in opposite directions:

- **Stagnation** — enforcing a doctrine that keeps causing unnecessary,
  harmful, or breaking issues.
- **Formlessness** — revising and doubting the guidelines so often that they
  stop constraining anything, which breaks the entire point of having them.

The asymmetry that resolves it: **logging is cheap, changing is expensive.**
Log freely and without judgement in the moment — it costs nothing and requires
no verdict. Reserve judgement for the review pass, when the whole pattern is
visible. Then change **rarely**, and only on a demonstrated recurring pattern —
never on a single compelling instance, however sharp it felt at the time.

Design gate 7 (*essentials-complete, not endlessly optimized*) applies to the
governance documents themselves, not only to the kernel.

## Protocol

When work collides with a governed document:

1. **Implement what doctrine already permits** — the detection, the refusal,
   the honest failure — using existing vocabulary and the outermost ring that
   works.
2. **Never mint** a governed change, and **never silently drop** the fix.
3. **Log the tension here** with its rationale and a recommendation.
4. **Adjudicate as a separate pass**, after closeout — never inside a fix wave,
   where the fix's momentum would decide a governance question.

Three kinds of entry are in scope:

- A fix recommendation a governed document forbids.
- **Code that contradicts documentation** — a doc asserting a guarantee the
  implementation does not keep. These frequently resolve *toward* the doc.
- A tension doctrine settled cleanly, where the tension itself is worth
  revisiting later.

Statuses: **OPEN** (awaiting adjudication) · **DECIDED** (the maintainer has
set direction; terminal when the implementing wave lands) · **CHANGED** (a
guiding document was amended) · **MINTED** (a governed change was made) ·
**HELD-FIRM** (doctrine upheld as final — re-open only on genuinely new
evidence) · **DROPPED** (recommendation withdrawn).

*(Reconciled 2026-07-27: this legend and the Lifecycle section had drifted —
the legend said "HELD", the Lifecycle names HELD-FIRM/MINTED as terminal, and
the adjudication pass introduced DECIDED. Pre-lifecycle **HELD** ≡
**HELD-FIRM**. The terminal set is CHANGED / MINTED / HELD-FIRM / DROPPED.)*

---

## Cycle R1-11 — 2026-07-22

Seeded from the fresh full-stack audit and the two adversarial fix rounds that
followed it, then extended by the records/teaching-corpus pass. Fourteen
entries. **No governed artifact was modified in any of them** —
`spec/semantics-contract.md`, `schema/*.json`, `policy/violation-codes.yaml`
and `policy/semantics.yaml` are untouched across the entire fix pass.

| # | Tension | Gates in play | Status |
|---|---|---|---|
| R1-11-01 | No governed reason code for a non-finite value | 1 vs 3 | **MINTED 2026-08-09** |
| R1-11-02 | CBOR value-sharing tags 28/29 undefined; backends disagree | 4, 6 | **CHANGED** |
| R1-11-03 | Compact mapping declares no maximum nesting depth | 4, 6 | **CHANGED** |
| R1-11-04 | `timing_quality` cannot say "bound unresolved" | 2, 3 | OPEN |
| R1-11-05 | `TASK_ACK` has no `UNKNOWN` state | 1, 3 | **HELD** |
| R1-11-06 | Adapter refusals are invisible to the wire | 3, 6 | OPEN |
| R1-11-07 | `bandwidth_hz: 0.0` sentinel is a documented convention | 3 | **HELD-FIRM** |
| R1-11-08 | CoT `error_ellipse` zero defaults | 3, 4 | **CLOSED 2026-08-09** |
| R1-11-09 | New `metrics_sink_gap` JSONL record type | 1, 6 | **CHANGED** |
| R1-11-10 | `risk_dimension: routing` — existing vocabulary or new? | 1 | OPEN |
| R1-11-11 | Policy `event_subtype` vocabulary: open or closed? | 1, 6 | OPEN |
| R1-11-12 | Collapsed-to-no-constraint now refuses (posture change) | 3, 6 | OPEN |
| R1-11-13 | CHANGELOG claim true-as-scoped, false read repo-wide | 3, 5 | OPEN |
| R1-11-14 | `--strict` makes a *tolerated* warn unrepresentable in the corpus | 3, 7 | OPEN |

### R1-11-01 — No governed reason code for a non-finite value · **MINTED 2026-08-09**

**Two gates pull against each other, which is what makes this the interesting
one.** Gate 3 (honesty) says a refusal must be filterable by the consumer.
Gate 1 (alphabet, not dictionary) says do not grow the vocabulary.

`policy/violation-codes.yaml` (56 entries, read in full) has no code meaning
"non-finite value" generally. Three candidates were evaluated:

- `NON_FINITE_CONFIDENCE` — **rejected.** Reporting a NaN *latitude* under a
  code that says "confidence" is itself a laundering: the operator filters on
  `reason_code`, and it would name the wrong field and the wrong failure.
- `INVALID_GEO_FIELD` — honest for geo, already in the schema enum, currently
  unused. **Rejected** because it forces a second code for non-geo fields
  (bearing, features, kinematics, extensions), fragmenting one condition across
  two filters — re-creating the per-field mapping that *was the defect*.
- `SCHEMA_INVALID` — **chosen and shipped.** NaN/Infinity are not JSON numbers
  under RFC 8259, so the datagram is not a valid instance of the data model;
  jsonschema cannot see it because min/max comparisons against NaN are vacuous.
  The fault is the producer's, so there is no misattribution.
  `details.field` carries the exact dotted path.

**Recommendation:** mint `NON_FINITE_VALUE` (severity `fail`) as a Class B
change. Two reasons beyond tidiness: (a) `SCHEMA_INVALID` is emitted from many
places, so an operator cannot filter or count non-finite refusals separately —
the honest-refusal-is-filterable property is weaker than gate 3 wants; (b) an
operator who legitimately downgrades `SCHEMA_INVALID` severity would silently
downgrade non-finite refusals with it.

**Counter-argument to weigh:** gate 1 is not satisfied by "it would be tidier."
The question is whether a consumer can *responsibly act* on `SCHEMA_INVALID` +
`details.field` — if yes, the existing code suffices and the recommendation
should be dropped.

**Occurrence count 3 reached 2026-07-27 — the lifecycle now forces a terminal
decision, and it is the maintainer's.** The reuse-vs-mint class has now taken
pressure three times: (1) this entry (non-finite refusals riding
`SCHEMA_INVALID`); (2) R2-30, the CoT skip-reason token, resolved outer-ring
by the 2026-07-27 vocabulary-boundary adjudication; (3) **H1-08** —
command-evidence refusals riding `LINEAGE_MISMATCH` /
`LINEAGE_PARENT_UNRESOLVED`, plus the TASK_ACK vocabulary being unable to name
an evidence refusal at all. Each reuse was individually correct under gate 1;
the question the threshold forces is whether the *accumulation* has degraded
the filterability gate 3 exists to protect. **Deliberately NOT decided inside
this closeout** (the protocol forbids deciding a governance question inside
the pass that surfaced it): the decision is either MINT the narrow codes
(`NON_FINITE_VALUE`, and a command-evidence pair) as one Class B batch, or
HELD-FIRM on reuse with the reasoning recorded once so the class stops being
re-litigated. The multi-UxS event is the natural evidence window — an operator
who cannot filter these apart in the field settles it either way.

**MINTED 2026-08-09, maintainer adjudication at the forced count.**
`NON_FINITE_VALUE` (fail) and the command-evidence pair
`COMMAND_EVIDENCE_UNRESOLVED` (warn) / `COMMAND_EVIDENCE_PROHIBITED` (fail)
enter `policy/violation-codes.yaml` and the 1.1.0 schema enum as one
Class B batch. The wire posture is diagnostic-first, because the locked
v1.0 reason-code enum cannot grow: a v1.0-stamped wire diagnostic keeps
its documented legacy code (`SCHEMA_INVALID`, `LINEAGE_PARENT_UNRESOLVED`
and `LINEAGE_MISMATCH` respectively; the mapping is policy data at
`policy/semantics.yaml` `schema_violation_v1_0_wire_fallback`, never
hardcoded) and carries the minted code in `metrics.diagnostic_code`,
while the gateway's JSONL diagnostics and the 1.1.0 enum carry it
natively. The filterability gate 3 was tracking is restored at the layer
the operator filters. On the wire, reason_code values are unchanged for
v1.0 consumers; the diagnostic gains one new metrics member,
diagnostic_code, which is schema-legal free-form metrics content that a
consumer ignoring unknown members never sees. Two residues, named rather than implied: the
require_evidence refusal (citations absent under the strict knob) keeps
`LINEAGE_MISMATCH`, a policy-strictness refusal outside the adjudicated
pair and filterable via `policy_ref`; and `NON_FINITE_CONFIDENCE`
remains the more specific code for the confidence sites, unchanged.
H1-08 closes with this batch. R2-30's outer-ring resolution is
undisturbed.

### R1-11-02 — CBOR value-sharing tags 28/29 undefined · **CHANGED 2026-07-27**

The same 11-byte payload `d81ca16473656c66d81d00` decodes to a genuinely
self-referential dict under `cbor2`, and to `{'self': 0}` under `zmeta_cbor`
(tag 28 ignored, tag 29's argument read as a literal integer). A repo-wide grep
finds no mention of value sharing, tag 28, tag 29, `shareable` or `sharedref`
in any spec, schema, policy or code file.

So the wire format is **silent**, and one datagram means two different things
on two conforming nodes depending on which library each installed — the exact
interoperability failure the format exists to prevent, and a near-twin of the
bignum tag 2/3 disagreement already documented in `zmeta_compact.py`'s header.

This was found while closing a hang, and it is worse than it first looked: the
cycle it creates made two ingress walkers non-terminating, i.e. **an
unauthenticated remote hang of the gateway receive loop from a 586-byte
datagram**. That half is now fixed in code and nothing is blocked on this entry
— but defence-in-depth is not a decision.

**Recommendation, in outer-ring order:** (1) state in
`spec/compact-binary-mapping.md` that the ZMeta CBOR profile defines no
value-sharing tags and a decoder MUST reject tags 28/29 rather than interpret
them — which also makes `zmeta_cbor`'s current silent-integer behaviour
non-conforming and worth correcting; (2) then have the `cbor2` fallback reject
such datagrams at the ingress boundary so the backends agree. Step 1 is
normative MUST text — Class B.

### R1-11-03 — Compact mapping declares no maximum nesting depth · **CHANGED 2026-07-27**

An event with extensions nested 65–400 deep **encodes** under `cbor2` and
**refuses** under `zmeta_cbor` (`DEFAULT_MAX_DEPTH = 64`). A cbor2-backed node
emits a compact datagram a conforming `zmeta_cbor` consumer cannot decode.

This is precisely what `zmeta_compact.py`'s own docstring says must never
happen — *"Representability is a property of the MAPPING, not of the local
install"* — stated and enforced there for the 64-bit integer range, while
nesting depth never got the same treatment.

**Recommendation:** a mapping-level max-depth pre-check inside
`_verified_compact_bytes`, mirroring the existing integer check. Mechanically
small; needs a maintainer decision on the normative number and a clause in
`spec/compact-binary-mapping.md` first. Same family as R1-11-02 — adjudicate
them together.

### R1-11-04 — `timing_quality` cannot say "bound unresolved" · OPEN

`$defs/timing_quality` is `additionalProperties: false` with exactly
`{time_source, sync_state, est_error_ms, last_sync_ts}`; `sync_state` is enum
`[LOCKED, HOLDOVER, UNSYNCED]`. There is no in-vocabulary way to state what is
actually true when a SAPIENT node declares a capture→send latency bound that
cannot be resolved: *"a bound was declared and we could not resolve it, so no
finite `est_error_ms` is defensible."*

Implemented the closest honest thing the locked vocabulary allows — degrade to
`UNKNOWN`/`UNSYNCED` and widen to `max(caller, unknown-clock default)`.

**The cost, stated plainly:** this *overstates* clock uncertainty (labelling a
possibly GPS-locked clock `UNSYNCED`) to avoid *understating* absolute
timestamp error. Overstating is the correct direction for an uncertainty field,
but it conflates two different unknowns — clock sync and latency bound — into
one label a consumer cannot pull apart. `60000 ms` is a repo convention, not a
proven bound.

**Recommendation (Class B):** option (2) preferred — a governed `reason_code`
the gateway attaches, leaving `timing_quality` alone and out of the locked
kernel. Option (1), a `bound_status` / `est_error_basis` member, is more
expressive but requires relaxing `additionalProperties` on a locked structure.

### R1-11-05 — `TASK_ACK` has no `UNKNOWN` state · **HELD**

**Logged precisely because doctrine won cleanly.** `$defs/SystemPayload`
constrains `TASK_ACK` state to nine definite verdicts. `LINK_STATUS` gets
`UNKNOWN`; `TASK_ACK` does not. A MAVLink message carrying no ack verdict has
nothing honest to degrade into.

Closed by **refusing** (`ValueError`) rather than by adding an enum member.

**Verdict — leave the enum alone.** An "unknown acknowledgement" is not a state
a task can be in; it is the *absence* of an ack. Emitting a `TASK_ACK` to say
"no ack" would be its own quiet fiction. Refusal is the right shape, matches
how the adapter already handles missing `task_id`/`original_event_id`, and an
enum member here would be a Class B change made to paper over an event that
should not exist. **Gates 1 and 3 agree; no change recommended.**

### R1-11-06 — Adapter refusals are invisible to the wire · OPEN

Ingress adapters refuse by omission — `translate()` returns the subset it can
honestly emit, `[]` when it can emit nothing. A refused detection is *silently
absent* to a standalone caller: no in-band, operator-filterable marker saying
"this detection existed and was refused."

This is the modules' own documented contract and the pre-existing convention
across the template family, so it was not changed. **The gateway path is
already covered** — the A-01 work refuses these at `validate_semantics` with a
governed `SCHEMA_INVALID` diagnostic — so exposure is limited to deployments
embedding an adapter without the gateway.

**Open question:** should ingress refusals be a filterable bucket rather than
an absence? That needs a governed diagnostic code. Interacts with R1-11-01.

### R1-11-07 — `bandwidth_hz: 0.0` sentinel convention · **HELD-FIRM 2026-07-27**

Three adapters (`kraken:159`, `moth:176,362,453`, `signalhunter:387`) emit
`bandwidth_hz: 0.0` as a "not measured" sentinel. **This is the same
fabricate-a-sentinel class as A-06** — 0 Hz is a physical claim about an
emitter — but unlike A-06 it is a deliberate, documented, cross-adapter
convention (`moth README:41-46`; the kraken docstring states it explicitly).

Not changed: three adapters plus READMEs plus a convention decision is well
outside minimal-and-in-class. Flagged because the gate-3 argument that
condemned the MAVLink altitude zero-fill applies here verbatim — an
unmeasurable quantity should be omitted, not reported as zero.

**This is the entry most likely to become a pattern.** The zero-fill class has
now been closed in moth (R1-10), signalhunter (R1-11 wave 3) and MAVLink
(R1-11 wave 6) while this documented convention survived each time.

**Fourth survival, recorded 2026-08-09.** The class closed a fourth time in
v1.1.20 (CoT egress ellipse zero-fill, R1-11-08) while this convention stood,
and the convention is now codified for new adapters in `adapters/AUTHORING.md`
alongside the kraken, moth and signalhunter READMEs. A future in-repo adapter
that omits rather than zero-fills would be the first counter-example, and
earns a line here if it arrives.

### R1-11-08 — CoT `error_ellipse` zero defaults · **CLOSED 2026-08-09** (rescoped 2026-07-27)

**Rescope and anchor refresh (cold re-read CR-20 + the health wave).** The
line anchors this entry originally carried matched no committed tree. Half the
tension is now closed: the point-level `ce`/`le` defaults were fixed by the
health wave (CR-02 — `le` no longer inherits the horizontal ellipse) and by
the `cot.config` knob, which makes the defaults deployment-asserted rather
than fabricated. **The surviving member** is the zero-filled
`ellipse_major`/`ellipse_minor`/`ellipse_angle` in the `<precisionlocation>`
detail when a partial ellipse is present, plus the remarks free-text twin —
`adapters/egress/cot/zmeta_to_cot.py` (search `ellipse_major=`). That is what
stays OPEN.



`zmeta_to_cot.py:235-237, 268-270` use `error_ellipse.get("semi_major", 0)`,
rendering `ellipse_major="0.0"` — a **sub-metre precision claim on an ATAK
screen** — for a partially populated ellipse. Same class as R1-11-07, on the
egress side, where gate 4 (egress is a lossy projection, never an upgrade in
apparent certainty) also applies.

**CLOSED 2026-08-09 (records pass; the fix landed 2026-08-03 in v1.1.20).**
The surviving member closed in the v1.1.20 fix wave: CoT egress stopped
zero-filling missing ellipse members into `<precisionlocation>` and remarks
(`CHANGELOG.md` `[1.1.20]`: "CoT egress stops zero-filling missing ellipse
members into remarks and precisionlocation"; `zmeta_to_cot.py` now renders
`ellipse_minor` and `ellipse_angle` only when the member is present). The
point-level `ce`/`le` half was already closed by the health wave and the
`cot.config` knob, as rescoped above. This status line is bookkeeping
catching up: the entry was not moved to terminal when its wave landed.

### R1-11-09 — New `metrics_sink_gap` JSONL record type · **CHANGED 2026-07-27**

The metrics-degradation fix introduced a new value of the `type` field in the
gateway's metrics JSONL log. That log is gateway-internal observability — not a
ZMeta event, no JSON Schema, not in the release manifest, no in-repo consumer
but tests — so **by the letter of the rules it is not governed vocabulary.**

But it *is* a consumer-visible token an operator's log tooling may key on. The
alternative (no marker) was measured as silent loss of 200 records with the
summary still reporting 204.

**Recommendation:** accept, or redirect to an existing record type
(`type: "warning"` with a code) — a one-line change, pins move with it. The
broader question worth adjudicating: **where is the boundary of "governed
vocabulary"?** Operator-visible tokens outside the event model currently have
no doctrine at all.

### R1-11-10 — `risk_dimension: routing` · OPEN

The new routing lint issues carry `risk_dimension: "routing"` rather than the
`"external_promotion"` the producer-authority lint uses, because
`spec/semantics-contract.md:317-319` explicitly lists `routing` and
`producer_authority` as risk dimensions. Read as *using existing governed
vocabulary*, not minting — but it is the one place a value was chosen that does
not yet appear in code. **Overrule if the dimension list reads as closed.**
The existing producer-authority lint was deliberately *not* re-labelled from
`external_promotion` to the more accurate `producer_authority` — churn on a
shipped surface for no defect.

### R1-11-11 — Policy `event_subtype` vocabulary: open or closed? · OPEN

`allowed_event_subtypes` entries were deliberately **not** vocabulary-checked.
The schema declares subtypes per event type, but `spec/extension-registry.yaml`
registers subtypes that are not yet schema-valid (`SENSOR_STATUS`,
`RETURN_TO_BASE`, `LOITER`, …) — so "unknown subtype token" is not decidable
from the schema alone, and asserting it would itself be a vocabulary claim.
The gap is fail-closed in direction.

**If the answer is "policy entries must name currently-valid subtypes"**, the
check is a one-line table addition and the deriver already extracts the
constants. The real question is whether the extension registry is a staging
area for the schema or a parallel vocabulary.

### R1-11-12 — Collapsed-to-no-constraint now refuses · OPEN

A policy block or producer rule that is *present but collapsed to no
constraint* now refuses instead of admitting. This is the fail-closed direction
and it names itself in the diagnostic — but it is a **runtime posture change**,
not merely a lint change: it will refuse a deployment that is silently
mis-configured today rather than continuing to admit traffic.

**Recommendation: accept.** Flagged because a posture change on a shipped
surface deserves an explicit decision rather than arriving as a side effect of
a lint fix.

### R1-11-13 — CHANGELOG claim true-as-scoped, false read repo-wide · OPEN

`CHANGELOG.md:37-38` asserts "non-finite numbers refuse at every canonical
guard and are dropped from native pass-through blocks." The bullet is headed
"SAPIENT adapter honesty (R11-02/-03/-04/-12/-20)", and **as scoped to SAPIENT
it is now true** — the code was brought up to the claim rather than the claim
down to the code, which is the healthy direction.

Read repo-wide the sentence is still false. **Recommendation:** narrow the
wording at closeout. Logged as a documentation-precision pattern worth
watching: a scoped claim under a scoped heading is easy to read unscoped.

**Disposition (2026-07-22, records group):** wording narrowed in place —
`CHANGELOG.md` now carries the scope inside the sentence ("in this adapter
family") rather than relying on the heading, and points back at this entry.
The recommendation is applied; the entry stays OPEN because the underlying
*pattern* judgement (whether scoped-heading inheritance is acceptable in the
CHANGELOG at all) is the maintainer's, not a records fix.

### R1-11-14 — `--strict` makes a *tolerated* warn unrepresentable in the corpus · OPEN

Raised while dispositioning **A-21** (teaching-corpus doctrine).

`BEARING_FRAME_UNLABELED` is `warn`, and the contract's own §6.4 language
*tolerates* legacy-unlabeled v1.0 bearings — a deliberate, documented
tolerance. But `tools/validate_examples.py:131-133` promotes warnings to
failures under `--strict`, and `--strict --require-all` is part of the
mandated kernel gate. The consequence is structural: **no shipped example
can ever demonstrate the case the contract says is tolerated.** The only
pressure the gate can apply to the teaching corpus is *toward stamping a
frame label* — which is how `c1eb9d0` came to add `TRUE_NORTH` provenance to
two examples in the same commit that introduced the warn.

That is a gate-3 problem pointed at the teaching surface rather than at the
wire: the corpus can teach "always labeled" but cannot teach "unlabeled is
tolerated and here is what it looks like", so an adapter author reading the
corpus infers a stricter rule than the contract states, and the honest
legacy shape has nowhere to live.

**What the fix wants:** a way for the corpus to carry an example whose
*expected* diagnostic is a specific warn — an expectations sidecar, a
`warn-tolerated` corpus, or a `--strict` that fails on unexpected warnings
rather than on all of them.

**What blocks it here:** all three land in `tools/validate_examples.py`
and/or a new corpus file plus its gate wiring — outside a records pass, and
a change to the *mandated release gate's* semantics is a maintainer call
under gate 6, not a documentation fix. Narrowing `--strict` would also
weaken a gate that currently catches real regressions.

**What was done instead:** nothing to the gate. The falsifiable half of
A-21 was closed on its merits (the RF example now carries the
`features.doa_array_relative_deg` provenance the reference adapter it names
always emits, so the example depicts a shape `kraken-sdr` can actually
produce). The doctrinal half is logged here rather than guessed at.

**Recommendation:** adjudicate alongside R1-11-06 (adapter refusals
invisible to the wire) — both are the same shape, a *deliberately tolerated
or refused* condition having no representable place in the artifacts a
consumer or author reads.

---

## Pattern notes for the next review

Observations that only become meaningful across cycles. Not verdicts.

- **The fabricate-a-sentinel class keeps recurring** (R1-11-07, R1-11-08, plus
  the A-06 altitude and the R1-10 moth fix). Doctrine is unambiguous — gate 3
  forbids it — yet a *documented convention* has survived three consecutive
  cycles of the same class being closed elsewhere. If it survives a fourth,
  the question is no longer whether the doctrine is right but why enforcement
  keeps stopping at the convention boundary.
- **Honesty (gate 3) and alphabet-not-dictionary (gate 1) genuinely conflict**
  when a new failure mode has no governed code (R1-11-01, R1-11-04, R1-11-06).
  Each was resolved by reusing the nearest honest existing code, which is
  correct in isolation. Watch whether repeated reuse gradually overloads a few
  general codes to the point that filtering — the property gate 3 exists to
  protect — stops working.
- **"Governed" has no defined boundary outside the event model** (R1-11-09,
  R1-11-10). Log record types, lint dimensions and diagnostic detail strings
  are all consumer-visible and none is covered by the change-class rules.
---

## Cycle R1-11 — disposition pass addendum (2026-07-22)

Seven further entries, surfaced by working the remaining findings per doctrine.
Same rule as above: **no governed artifact was modified** to produce any of
them. Several are the same tension arriving from a new direction, which is
exactly the pattern this log exists to make visible.

*(Renumbered 2026-07-26: these seven were first recorded as R1-11-14..20,
colliding with the first pass's R1-11-14 — they are now R1-11-15..21, and the
log holds twenty-one entries, not the twenty the cycle records first counted.
In-repo cross-references were swept in the same commit.)*

| # | Tension | Gates | Status |
|---|---|---|---|
| R1-11-15 | `TIME_STATUS.state` is not enum-constrained while its two siblings are | 1, 3 | **MINTED** |
| R1-11-16 | Adapter-declared vocabularies mirror governed enums by hand, unlinted | 1, 6 | **CHANGED** |
| R1-11-17 | Formal release identity has no stated grammar | 5 | OPEN |
| R1-11-18 | Compact mapping declares no size or expansion bound | 4, 6 | **CHANGED** |
| R1-11-19 | *(merged into R1-11-14 — same tension, counted once)* | 2, 3 | MERGED |
| R1-11-20 | Two conventions the new pins now enforce, chosen not discovered | 5, 7 | OPEN |
| R1-11-21 | Illustrative-example currency policy left inconsistent | 7 | OPEN |

### R1-11-15 — `TIME_STATUS.state` is unconstrained by the schema · **MINTED 2026-07-27**

**This is why B-04 was invisible.** `$defs/SystemPayload` enum-constrains
`state` on the `LINK_STATUS` and `TASK_ACK` branches, but the `TIME_STATUS`
branch constrains `metrics` only and leaves `state` as the base
`{type: string, minLength: 1}`. Probed live: `payload.state = 'NOMINAL'` over
`metrics.sync_state = 'UNSYNCED'` is schema-OK and passes `validate_semantics`
without complaint — a self-contradicting event the kernel cannot see.

Closed adapter-side by declaring the vocabulary and its severity ordering in
the MAVLink template and refusing there. **That makes one adapter honest; it
does not make the kernel enforce it for all of them.**

**Recommendation:** decide whether the `TIME_STATUS` branch should
enum-constrain `state` the way its siblings do. Class B. This is the clearest
case in the log of a *missing* constraint rather than a contested one — the
asymmetry between the three branches reads as an oversight, not a design.

### R1-11-16 — Hand-mirrored vocabularies with no lint · **CHANGED 2026-07-27**

Three vocabularies now live in `mavlink_to_zmeta_template.py` duplicating
governed enums by hand: `_LINK_STATUS_STATES` (pre-existing),
`_LINK_STATUS_REASON_CODES` and `_TASK_ACK_STATES` (new). They mirror rather
than load the schema because the file is a **template meant to be copied into
a bridge with no ZMeta repo alongside it** — loading the schema at runtime
would add a filesystem dependency to an adapter.

Drift is fail-closed in one direction (adapter over-refuses a code the kernel
allows — covered by a pin that runs all twelve codes through the shipped
validator) and **fail-open in the other** (under-refuses — not covered).

**Recommendation:** a repo-side lint asserting adapter-declared vocabularies
are subsets of the schema enums. Closes it for every adapter at once, costs
nothing at runtime, and keeps the template dependency-free. Cheap and
outer-ring — this one probably just wants doing.

### R1-11-17 — Formal release identity has no stated grammar · OPEN

A-09 is closed to the letter of what `spec/release-hash-policy.md` already
promises: a formal manifest can no longer keep the builder's *default*
identity. But **nothing in any governed document says what a valid formal
identity looks like**, so a manifest carrying a wrong-but-plausible one — the
previous release's id, or a date that is not the cut date — still validates
clean.

**Recommendation:** if tag/identity agreement should be enforced, it belongs in
`spec/release-hash-policy.md` first and the validator second, and the natural
enforcement point is **the cut, not the committed manifest**. Note the shape:
a validator can only ever enforce a rule the spec has stated.

### R1-11-18 — No size or expansion bound in the compact mapping · **CHANGED 2026-07-27**

CBOR value sharing lets a small datagram expand enormously. Measured: an
~800-byte shared-DAG datagram costs 2.77 s inside `dumps()` before refusing at
2^20 paths, and materialises 786 KB at 2^16. The mechanism to refuse it cheaply
already exists — the walk's memo makes the exact expanded node count computable
in linear time.

**What blocks it is that every candidate number is a normative choice.**
`zmeta_compact.py`'s own docstring rejects node budgets outright: *"any node
budget refuses some large-but-honest event, and discarding good data is not a
safe default."* `zmeta_cbor`'s 1 MiB default is a self-declared receive-side
DoS knob, not a mapping limit; adopting it would newly refuse honest large
events on cbor2-only installs — the same runtime posture change as R1-11-12.

**Adjudicate with R1-11-02 and R1-11-03.** All three are the same missing
clause in `spec/compact-binary-mapping.md`, and answering them separately risks
three inconsistent answers.

### R1-11-19 — `--strict` makes a tolerated warn unrepresentable · OPEN
### → MERGED INTO R1-11-14 (2026-07-27)

**This is R1-11-14, recorded twice.** Cold re-read CR-27 flagged the
duplication; the records wave did not close it, so it is closed here. The two
entries are the same tension arriving from the first pass and the disposition
pass, and later records already cite them jointly ("doctrine R1-11-14/19").
**They count as ONE tension in any tally**, and its occurrence count is 3
(first pass, disposition pass, and the VW-17 citation when the command-evidence
corpus example could not be written). The body below is retained for its
distinct framing; the live entry is R1-11-14. The threshold decision is the
maintainer's, same shape as R1-11-01 above: either a warn-expectations
mechanism for the teaching corpus, or HELD-FIRM that teaching-by-example is
deliberately scoped to the pass/fail boundary.



The teaching corpus is validated with `--strict --require-all`, which means a
condition the standard deliberately **tolerates as a warning** cannot be shown
in an example. So the corpus can teach what is valid and what is refused, but
not what is *permitted-with-a-caveat* — which is precisely where an integrator
most needs an example.

**Recommendation:** decide whether the corpus should carry a warn-bearing
example under a relaxed flag, or whether teaching-by-example is deliberately
scoped to the pass/fail boundary. Gate 2 argues the former; gate 7 argues the
latter. No change made.

### R1-11-20 — Two conventions the new pins now enforce · OPEN

Listed so they are **chosen rather than discovered**, which is the whole point
of writing them down before they harden:

1. A future compact normalization must close its spec-table row with
   `"Same <thing>."` **and** be implemented as `_same_<thing>(original,
   restored)` inside `_semantic_difference`. A naming convention promoted to a
   machine-checked contract.
2. `release/zmeta-release-manifest.yaml`'s `known_open_issues` is now
   **authoritative over prose** in `spec/*.md`, the release templates,
   `release/README.md`, `RELEASE_CHECKLIST.md`, `AGENTS.md` and `README.md`: a
   genuinely open issue must be listed there before a forward-facing document
   may say it is open.

Both are narrower than the surfaces they bind, and both were adopted by a pin
rather than by a decision. **Endorse or loosen them deliberately.**

### R1-11-21 — Illustrative-example currency policy · OPEN

`TRADEMARK.md:22,24` and `adapters/README.md` carry structurally identical
release-named examples. The previous cycle re-baselined one and deliberately
declined the other, and this pass pinned neither.

This is a taste call about what the standard promises to keep current. Either
pin the family or record the exclusion in the currency suite's docstring —
**the current silence is the only real problem.** Relates to the
fabricate-a-sentinel note above: a convention survives partly because nobody
wrote down that it was a convention.

### Pattern note added this pass

**"Governed" still has no defined boundary, and it is now blocking work.**
R1-11-09 raised it; this pass hit it three more times — the CoT skip-reason
vocabulary, a new metrics JSONL token, and adapter-mirrored enums. Two
otherwise-mechanical fixes are parked *solely* because nobody can say whether
an operator-visible token outside the event model is governed vocabulary.

This is the highest-leverage entry in the log: adjudicating it unblocks several
others at once, and unlike the kernel questions it costs nothing to answer —
it is a scope definition, not a semantic change.

---

## Adjudication pass — 2026-07-27 (maintainer)

Four decisions taken with the maintainer in-session, per the protocol's
separate-pass rule. New interim status **DECIDED**: the maintainer has set
the direction; the entry reaches its terminal status (CHANGED / MINTED) when
the implementing wave lands.

1. **Governed-vocabulary boundary (R1-11-09, R1-11-16, both pattern notes) —
   governed = the event model only.** Schema enums, reason codes, policy
   vocabulary, and wire semantics are governed. Operator-visible tokens
   outside the event model — gateway JSONL record types, lint dimensions,
   diagnostic detail strings, adapter-declared vocabularies — are
   **outer-ring**: mirrors of governed enums must stay subsets, and adding an
   outer-ring token needs no governance gate. R1-11-09 → **CHANGED** (the
   `metrics_sink_gap` record type had already shipped in the disposition pass
   and is now pinned); R1-11-16 → **CHANGED** (the subset lint shipped:
   `tools/lint_adapter_vocabularies.py`). The two parked mechanical fixes
   landed the same day (R2-30 `NON_FINITE_VALUE` skip token — `dcabcc8`).
2. **Compact-mapping clause cluster (R1-11-02/03/18) — fail-closed clause
   approved; all three DECIDED.** The mapping accepts only the canonical JSON
   value model: any tag or construct that cannot expand back value-identically
   (28/29 included) is refused at decode, and decoders MUST enforce a declared
   expansion bound — the walk's memo makes the expanded node count linear-time
   computable — refusing beyond it with an explicit diagnostic. Implementation
   is its own governed wave in `spec/compact-binary-mapping.md`; the entries go
   CHANGED when it lands. **Landed the same day** (`40be64a`): the normative
   "Value Model, Tags, and Expansion Bound (Fail Closed)" section, enforced
   on both backends and spec-sync-pinned. All three entries are CHANGED.
3. **R1-11-15 `TIME_STATUS.state` — Class B enum approved; DECIDED.**
   Constrain to a declared vocabulary matching the sibling branches at the
   next cut, with fixtures and conformance evidence; goes MINTED when it lands.
   **Landed the same day** (`2a00ef2`): v1.1.0-only enum, bad-event fixture,
   red-first pins, v1.0 byte-identical and pinned so. MINTED.
4. **Round-3 register loss (cold re-read CR-03; a records decision, not a
   doctrine entry) — the loss is recorded as final.** No reconstruction
   round; the findings re-derive from the tree via scoped waves. Recorded in
   the register's Status block.

---

## Cycle H1 — 2026-07-27 (health fix wave)

Tensions surfaced by the wave's fix and attack agents. Same rule as always:
no governed artifact was modified to produce any of them.

| # | Tension | Gates | Status |
|---|---|---|---|
| H1-01 | ADAPTER_VERSION bump discipline is undefined | 5, 7 | OPEN |
| H1-02 | Negative TASK_ACK verdicts default to a restating reason_code | 3 | OPEN |
| H1-03 | Adapter-stricter-than-schema contradiction refusals | 1, 3 | OPEN |
| H1-04 | Vocabulary lint: mandated-gate wiring and schema breadth | 6, 7 | OPEN |
| H1-05 | CoT `how`/pedigree omission vs consumer expectations | 4 | OPEN |
| H1-06 | `_normalized_uses` member-shape tolerance is mirrored in filter_risk | 3 | OPEN |
| H1-07 | Gateway plain-`cbor` envelope ingress still interprets tags on cbor2-only installs | 4, 6 | **CHANGED** |
| H1-08 | Command-evidence refusals ride lineage codes; TASK_ACK cannot name them | 1, 3 | **MINTED 2026-08-09** |

### H1-01 — ADAPTER_VERSION bump discipline · OPEN

The mavlink template's behavior changed materially this wave (new refusals,
new emitted fields) with ADAPTER_VERSION left at 1.2.0. Precedent cuts both
ways: one prior commit bumped for behavior alignment, while three held-range
fix commits to the same file did not. Decide what a version bump MEANS for a
template adapter, then apply it one way.

### H1-02 — Restating reason_code on negative acks · OPEN

For a negative TASK_ACK verdict with no message-carried cause, the adapter
now writes the code that restates the verdict (REJECTED → TASK_REJECTED) —
the SAPIENT sibling's pairing, and a restatement adds no cause the message
did not carry. Logged because it WRITES a field the wire did not: the
alternative (refusing every causeless negative ack) suppresses exactly the
verdicts a commander most needs.

### H1-03 — Adapter-stricter-than-schema refusals · OPEN

The schema permits `metrics.reason_code` on any TASK_ACK state; the adapter
refuses a failure cause under a clean verdict (and keeps the UP twin on
LINK_STATUS) as self-contradictory. Honest in direction, but it is an
adapter inventing a constraint the kernel does not state — if the pattern
recurs, the constraint belongs in the schema (Class B) or nowhere.

### H1-04 — Lint gate wiring and schema breadth · OPEN

Two open knobs on the new vocabulary lint: whether it joins the mandated
kernel gate (a gate-semantics change — maintainer call), and that it holds
mirrors against BOTH published schemas while the mavlink template claims
v1.0 specifically (identical enums today; a future v1.1-only value forces
the question). Known-blind spots, banked as register candidates: rebindings
inside `if`/`try` blocks and tuple-target assignments.

### H1-05 — CoT `how` omission vs consumer expectations · OPEN

`how`, `geopointsrc`, and `altsrc` are now config-asserted and omitted when
unasserted — honest, but some TAK-ecosystem consumers may expect `how` on
every event. Validate against the real display tools at the field exercise;
if a consumer chokes, the answer is a deployment config assertion, never a
restored hardcoded default.

### H1-07 — Plain-`cbor` envelope ingress vs the fail-closed clause · **CHANGED 2026-07-27**

The new value-model clause is enforced at the COMPACT decode seam. The
gateway's plain-`cbor` (non-compact) envelope path falls back to bare
`cbor2.loads` on cbor2-only installs (`gateway/src/gateway.py:~1119`), so a
tagged/shared datagram on that envelope is still interpreted there, while
zmeta_cbor installs now refuse it — a refusal-vs-acceptance divergence one
envelope over from the one just closed. Candidate for the next scoped wave
together with VW-01 (the validators' naive-ts arm).

**CHANGED same day:** `_decode_cbor_envelope` is now the plain-`cbor`
ingress seam — zmeta_cbor when present, else cbor2 with a probed
`max_depth` knob, plus the same fail-closed value-model scan the compact
envelope runs, and a hard refusal when neither scanner is importable.
Both envelopes now refuse tags/sharing/non-finite/over-deep input
identically on both backends; refusals surface as counted SCHEMA_INVALID
diagnostics. Residual siblings banked as VW-15 (the `auto` and `compact`
branch call sites still reach bare `cbor2.loads` pre-decode on
cbor2-only installs; resource-knob parity; the scanner-absent install
combination).

### H1-08 — Command-evidence refusals ride lineage codes · **MINTED 2026-08-09**

The command-evidence check (2026-07-27, maintainer-directed) reuses
LINEAGE_MISMATCH / LINEAGE_PARENT_UNRESOLVED for its two new refusal
conditions rather than minting COMMAND_EVIDENCE_* codes — correct under
gate 1 and the R1-11-01 reuse doctrine, but the same watch applies: if an
operator cannot filter "evidence prohibited for command basis" apart from
generic lineage mismatches in practice, the code wants minting as Class B.
Related seams, same entry: the TASK_ACK reason vocabulary is deliberately
task-limited so evidence refusals ride the documented
force_schema_violation SCHEMA_VIOLATION shape; and risk_dimension reuses
'lineage' pending the R1-11-10 dimension-boundary question. Adjudicate
together with R1-11-01/-10 when the pattern is visible — the multi-UxS
event is the natural evidence window.

**MINTED 2026-08-09, with the R1-11-01 batch.** The two riding conditions
carry their own codes now: `COMMAND_EVIDENCE_UNRESOLVED` for a citation
the gateway cannot resolve, `COMMAND_EVIDENCE_PROHIBITED` for evidence
whose adjudicated use limits prohibit command basis, each with the v1.0
wire fallback and `diagnostic_code` detail recorded in the R1-11-01
closure. Deliberately untouched, so the residue stays legible: evidence
refusals keep riding the documented force_schema_violation
SCHEMA_VIOLATION shape (extending the TASK_ACK vocabulary was outside
the adjudicated batch), and the `risk_dimension: lineage` reuse stays
pending R1-11-10, which this batch does not decide.

### H1-06 — Member-shape tolerance mirrored across two surfaces · OPEN

`_normalized_uses` (sapient egress) deliberately mirrors
`tools/filter_risk.py` `_list_values`, and both coerce garbage members into
never-matching tokens — a member-level tuple/bytes prohibition fails open
(verifier MODERATE, deferred). A fix must move BOTH surfaces together, or
egress and operator tooling adjudicate the same labels differently.


---

## Cycle P2 — 2026-07-27 (downstream consumer report)

Seeded by a fielded consumer's pin-advance review rather than by an internal
audit. Findings in this exchange are numbered `P2-NN`, so doctrine entries take
the `P2-DN` form to keep the two namespaces apart.

| # | Tension | Gates in play | Status |
|---|---|---|---|
| P2-D1 | A verification that cannot fail is recorded as verification | 3, 5, 7 | **CHANGED** |

### P2-D1 — A verification that cannot fail is recorded as verification · **CHANGED 2026-07-27**

**The tension is not that vacuous pins happen. It is that discipline 5 already
forbids them and they kept happening — seven times, across three surfaces,
while the rule was in force and being cited.** A doctrine that is stated,
believed, quoted in commit messages, and still violated at this rate is not a
discipline problem. It is a rule with no mechanism, and that is a governance
defect rather than an execution one.

**The recorded instances.** All are in-repo findings, not recollection:

| # | Instance | Mechanism of vacuity | Where |
|---|---|---|---|
| 1 | A-02 pin: `_assert_clean` satisfied by an empty event list; 7 of 13 parametrized cases pass with the fix reverted | **Post-condition satisfiable by nothing** | `r1_11_fix_pass_findings.md` R1-04 (MAJOR) |
| 2 | `test_risk_mode_lint_survives_a_mangled_block` asserts only "did not raise"; 5 of 15 subtests exercise no touched path | **Asserts non-crash, not the post-condition** | `r1_11_fix_pass_findings.md` R2-18 (introduced by remediation) |
| 3 | First A-14 unhashable-guard pin: `assertFalse(ok)` passes on the reverted tree | **A different gate refuses first** | `r1_11_full_stack_audit.md:1771` |
| 4 | Arm 3 of the *replacement* trigger-polarity pin, same shape | **A different gate refuses first** | Cold re-read CR-16 (MODERATE) |
| 5 | NaN-confidence pin blind by construction — all 15 tests call `process_message` without `timing_state`, skipping the block entirely | **Named path unreachable from the test** | `r1_11_fix_pass_findings.md:172,528` |
| 6 | Adapter harness passes a fixture with rich expectations **all unevaluated** when the adapter returns `[]` | **Shipped tooling; defeats the harness README's own "rather than pass vacuously" promise** | `r1_11_full_stack_audit.md` R11-08 |
| 7 | Live red-first probe run by hand: a `str.replace` whose anchor did not match, so it mutated nothing and "proved" the guard fired | **Mutation never applied** | This session, 2026-07-27 |

Adjacent, same family, worth naming because it shows the class is not
test-specific: jsonschema `minimum`/`maximum` are **no-ops against NaN**
(R11-04), so a schema constraint that reads as a bound enforces nothing on the
one value it most needs to; and an audit finding's own evidence was once a
`git diff` over a **gitignored** directory, which is empty by construction and
therefore proves whatever the author hoped (`r1_11_full_stack_audit.md:1298`).
Instance 4 is the sharpest single fact: it is a vacuous pin **inside the fix
for a vacuous pin**, found only by a later fresh-eyes pass.

**Why the existing rule did not hold.** Discipline 5 says *"proven by
revert-simulation with a specific assertion — watch it fail on the reverted
tree."* Read closely, that is an instruction to perform a **session act** and
then attest to it. Three properties follow, and all three are the failure:

- **Ephemeral.** The reverted tree exists for seconds in one author's working
  copy. Nothing re-runs it. A pin that was genuinely non-vacuous in March can
  become vacuous in July — a new gate lands upstream of it and starts refusing
  first — and no signal fires, because the proof was never a thing that runs.
- **Author-attested.** The evidence a reader inherits is prose in a commit
  message. Discipline 6 (*author is not grader*) is enforced for closure
  probes and not for pin quality, which is the same claim class.
- **Unverified at the mutation step.** Nothing checked that the revert or the
  doctoring actually changed anything — instance 7 exactly.

This is a **gate 5 problem** and naming it that way is what makes it
tractable: *structure is authoritative, free-text is a human projection.* The
repo already applies that to event data and refuses to let load-bearing
meaning live only in `remarks`. A pin's non-vacuity is load-bearing meaning,
and it has been living only in remarks.

**Rejected on measurement, recorded so it is not re-proposed.** A static lint
for "test functions containing no assertion" looks attractive and is not
viable: measured across the suite it flags **39 of 1310** functions, and
spot-checking shows the overwhelming majority delegate to asserting helpers
(`self.check_container(...)` in `test_policy_shape_fail_closed.py` is the
representative shape). At that signal-to-noise it would be ignored within a
cycle, and an ignored lint is worse than none because it launders coverage.
Full mutation testing over 1310 tests was not pursued for the gate 7 reason:
the cost is real, the noise is high, and the failure has a cheaper structural
fix.

**What changed.** `docs/zmeta_audit_playbook.md` discipline 5 now requires the
demonstration to be **an artifact in the repo rather than an act in a
session** — a paired check that constructs the bad state and asserts the guard
reports it, living beside the guard and re-running in CI. That converts an
author-attested past-tense claim into a present-tense structural one, which is
the only form that survives the guard's surroundings changing underneath it.

The supporting primitive is `gateway/tests/vacuity.py`: `mutate()` refuses a
substitution that changes nothing, so instance 7's shape raises instead of
passing quietly. It is deliberately small — one hole, closed mechanically —
and it is itself pinned in both directions, because a helper that exists to
refuse meaningless proofs is the bottom of the stack with no outer guard.

**Deliberately NOT changed, and the honest limit of this.** Nothing here
detects mechanisms 1–5 automatically. A paired demonstration is still written
by the same author who wrote the guard, so instance 4 — a vacuous pin inside
the fix for a vacuous pin — would still be possible; what changes is that the
bad state is now *executable and permanent*, so a later reader or fresh-eyes
pass can interrogate it instead of re-deriving it. The remaining exposure is
the same one the cold re-read named: **~7.8k lines of pre-existing test mass
with under 15% deep-read coverage**, written before any of this applied. Those
pins are not retro-fitted and should not be assumed non-vacuous. That is a
scoped wave, not a sweep, and it is the natural next use of the pin-quality
lens.

**Occurrence count: 7 (threshold is 3).** Reaching a terminal status was
overdue by four instances, which is itself the argument for the change rather
than another cycle of watching.

---

## Cycle A1 — 2026-07-28 (first cooperative-broadcast adapter)

Raised by building the ADS-B ingress adapter against real `dump1090` shapes,
ahead of a live RTL-SDR test. All three are cases where **a real thing cannot
be said in the current alphabet**, so an adapter author's only options are to
fabricate or to discard. None is an ADS-B quirk; each has at least one other
instance, which is what keeps a fix from being an accommodation for one source.

| # | Tension | Gates in play | Status |
|---|---|---|---|
| A1-01 | RF minimum features assume a calibrated receiver | 1, 3 | OPEN — experimental discriminator shipped 2026-08-09 |
| A1-02 | All-or-nothing geo discards good 2-D positions | 1, 2, 3 | **CLOSED 2026-08-03** — shipped end to end: schema, token, coherence arms, contract 21.1/21.8, registry, both adapters, projector |
| A1-03 | Translation provenance is unsayable for an original observation | 3, 5 | OPEN |

### A1-01 — `power_dbm` assumes a calibrated receiver · OPEN

Semantics-contract 7.4 makes `power_dbm` a **required** RF minimum feature.
`dump1090` reports `rssi` in **dBFS** — relative to the receiver's full scale,
dependent on antenna and gain chain, not convertible to absolute dBm without a
calibration the message never carries. So an RF-modality ADS-B observation must
either fabricate the field or refuse every event.

**Second instance, already shipped:** `adapters/ingress/kraken/kraken_to_zmeta.py:160`
writes `"power_dbm": rssi_db`, where its own input documentation
(`:8`, `:93`) calls field 3 "RSSI dB" — an uncalibrated relative value from the
KrakenSDR DoA chain. This is **not** adapter carelessness: the spec leaves no
third option. The gap manifests as a defect in every adapter that meets it.

Maintainer's field observation, recorded because it bounds the severity: the
kraken path translates, fuses and maps correctly in TAK today. Within one
deployment everyone knows the source and treats the number consistently. The
cost appears only when a second sensor's power meets it in the same consumer,
where `-40` from a calibrated receiver and `-40` from kraken are not the same
physical quantity — i.e. it works right up until interoperability happens,
which is the one scenario ZMeta exists for.

**Recommendation:** not a new subtype. `RF_ADSB`/`RF_KRAKEN` per sensor family
is a dictionary, and gate 1 forbids it. The alphabet-shaped fix is a
**declaration of reference** — power says whether it is absolute dBm,
full-scale dBFS, or relative dB — exactly as `bearing.frame` declares
`TRUE_NORTH` and `quality.calibration_state` declares `UNCALIBRATED`. One
optional discriminator covers every SDR ever made. **Constrain the meaning,
not the source.**

The ADS-B adapter ships on v1.0 using `NETWORK` modality to avoid the
fabrication. That is a WORKAROUND, not a design — ADS-B is RF — and it is
recorded as such in the adapter README.

**DECIDED 2026-08-09, maintainer adjudication: the experimental split runs.**
The discriminator this entry recommends is minted on the v1.1.0
experimental branch as `features.power_reference` (`DBM_ABSOLUTE` / `DBFS`
/ `DB_RELATIVE`; registry entry POWER_REFERENCE, experimental), and the
ADS-B adapter emits either form by flag (`rf_power_reference`) under
conditional 1.1.0 stamping, exactly the mechanism the experiment section
below proposed and A1-02 has since proven end to end. Two things stay on
the record. First, the independence caveat from the A1-02 erratum applies
here in full: the experiment section's claim that this entry "already
clears" the promotion bar cites kraken and ADS-B, which share one
codebase, author and organization, so the bar is NOT met under the
registry's independence definition; the discriminator enters as an
experiment gathering consumer evidence, not as a promotion. Second, the
entry stays OPEN: the tension is the formal vocabulary's calibrated-power
assumption, and it closes when field evidence answers the checklist A1-01
question in either direction — promotion on real consumer need, or the
registry's served-in-place disposition if nobody compares power across
sensors. The fielded kraken adapter is deliberately unchanged either way. One
further tension, logged rather than smoothed: the registry's Promotion
Evidence Requirements make independent demonstrated need a necessary
condition for experimental standing, and this entry enters experimental
with that condition unmet, by explicit maintainer adjudication. The
clause was written for promotion from reserved or proposed and did not
anticipate direct-to-experimental creation; whether it should govern
that path too belongs to the registry's next revision, and this
sentence is the record that the pressure existed.

### A1-02 — All-or-nothing geo discards good 2-D positions · CLOSED 2026-08-03

**Shipped end to end in the v1.1.20 waves, and the measured consequence
that opened this entry now measures the other way:** the same schema-valid
AIS observation that projected to zero tracks projects to a
two-dimensional FUSION_EVENT and STATE_EVENT pair, geo_status
VERTICAL_UNAVAILABLE, never a vertical the message never gave. The full
surface: schema/zmeta-event-1.1.0.schema.json ($defs/geo dimensionality
plus three coherence arms), contract sections 21.1 and 21.8, registry
entry GEO_DIMENSIONALITY (adopted, risk_relevant), AIS and
barometric-only ADS-B emitting the form under conditional 1.1.0 stamping,
and the track projector accepting it. The locked v1.0 lane keeps the
demotion this entry documented, which is now the adoption-path story, not
a wall. Original entry as written:

`payload.geo` requires `alt_m` (contract 6.8). A large share of ADS-B targets
report only `alt_baro`, a pressure altitude referenced to 1013.25 hPa, which is
not a height above the ellipsoid and is not convertible without local QNH. The
horizontal fix is good; the standard cannot carry it.

**The sharper instance is AIS:** a vessel has no meaningful altitude *ever*, so
ZMeta cannot canonically carry an AIS position at all. Ground radar and most DF
systems are likewise 2-D. This is a whole class of sensors, not an edge case.

**Recommendation:** again a declaration rather than a subtype — geo declares
its **dimensionality**, the way `geo_status` already declares availability.

**Whether it matters is a field question.** It is entirely possible no consumer
misses the dropped positions, and that is cheaper to discover than to argue.

**SECOND INDEPENDENT IMPLEMENTATION LANDED 2026-07-31, and it clears the
promotion bar.** `adapters/ingress/ais/` is the AIS instance this entry
predicted. It is not a variation on the ADS-B case, it is the total form: for
ADS-B, barometric-only targets are a subset; for AIS it is every vessel, every
message, always, because a surface vessel has no height above the ellipsoid and
the message has no field for one. Substituting sea level would be wrong by up to
the geoid separation, roughly 100 m, and would assert a measurement nobody made.

**The consequence is measured, not argued.** A schema-valid AIS observation
whose identity resolves cleanly (`mmsi-366123456`) and whose position is exact
as broadcast projects to **zero tracks** through `adapters/projector/track`,
because a track requires canonical geo. The identity works, the position is
right there, the event validates, and nothing reaches a COP. Pinned in
`adapters/ingress/ais/test_ais_ingress.py::TestTrackProjectionConsequence`.

Two implementations now, in this repository, on different sensor classes,
reaching the same wall from opposite directions: ADS-B refuses to substitute an
altitude it cannot convert, AIS has no altitude to convert. The bar this entry
was waiting on is met.

**A third facet, surfaced while writing the second implementation.** When
canonical geo is omitted, the only available status token misdescribes the
result. The contract's `geo_status` vocabulary is `AVAILABLE`, `UNAVAILABLE`,
`ESTIMATED`, `STALE`, `CONFIGURED` (section 21.1), and both adapters set
`UNAVAILABLE` for a position that is known, exact and sitting in the native
features. Read as the status of the canonical geo object it is correct; read as
a statement about our knowledge of position it is false, and a consumer
filtering on `geo_status == UNAVAILABLE` would discard vessels it could have
plotted. The adapters were deliberately kept consistent with each other rather
than diverging, so this needs either a vocabulary token or a contract sentence
saying which reading is normative. It is the cheapest of the three fixes and
independent of the dimensionality question.

**DECIDED 2026-08-02, maintainer adjudication.** The disposition this entry
recommended: canonical geo gains a declared-dimensionality form, plus a
`geo_status` vocabulary token for "horizontally known, vertically absent",
one mechanism for AIS, barometric-only ADS-B, and every future 2-D source.
Per-source carve-outs were considered and rejected as dialect. Two paths
were examined and declined on the record: reusing `geo2d` on state payloads
(two position homes on one payload makes every consumer branch forever) and
rehoming AIS as SYSTEM_EVENT (SystemPayload carries no geo member, and the
system channel is trusted internal telemetry, the wrong authority lane for a
spoofable broadcast). The urgency input was the readiness audit's finding
that maritime tracks cannot reach a COP through the reference pipeline at
all. Lands in the v1.1.20 governed wave, which is already
behaviour-changing under X1-01. Lineage was confirmed a non-issue: the
single-member FUSION path is legal and instant; the wall was geometry only.

**Record correction 2026-08-09 (post-cut erratum).** The promotion-bar
citation above ("SECOND INDEPENDENT IMPLEMENTATION LANDED ... it clears the
promotion bar") does not meet the independence definition in
`spec/extension-registry.md` (Promotion Evidence Requirements, item 1: two
implementations "not derived from the same codebase, vendor, or
organization"). The ADS-B and AIS adapters share one codebase, one author
and one organization; they are two instances of the need, not two
independent implementations. The private planning record that flagged this
asked for the correction before the cut; the cut happened with the citation
intact, so the correction lands here, dated. The decision itself is not
disturbed: the promotion rests on the 2026-08-02 maintainer adjudication
and the readiness audit's finding that maritime tracks could not reach a
COP through the reference pipeline at all, which is the evidence this
record should have led with. The same caveat applies to the experiment
section's claim below that A1-01 "already clears" the bar with kraken and
ADS-B: those are likewise same-origin, and the A1-01 entry now carries the
caveat where its disposition is recorded.

### A1-03 — Translation provenance is unsayable for an original observation · OPEN

`lineage` requires `based_on` with `minItems: 1`, and `transform` lives inside
it. An original observation has no ZMeta parent, so an adapter cannot record
*"this was translated from dump1090 aircraft.json@1.0"* canonically — precisely
where adapters live. Expressible as a native feature, so this is a minor gap
rather than a headline, but it is the same shape as the two above.

### The proposed experiment (maintainer, 2026-07-28)

Use the **canonical / experimental schema split** as it was designed to be
used: leave v1.0 locked, add the candidate discriminators to the v1.1.0
experimental branch and the extension registry, and have the ADS-B adapter emit
either by flag. The same capture, two encodings, decided by what downstream
consumers actually want rather than by argument.

The promotion bar is 2+ independent implementations. **A1-01 already clears it**
(kraken and ADS-B, both in-repo). **A1-02 has one**; AIS on the same RTL-SDR
dongle is the natural second — no extra hardware, genuinely independent sensor
family, and the strongest possible case since altitude is meaningless rather
than merely missing.

**Overtaken 2026-07-31.** The experiment ran: the AIS adapter landed as exactly
this second implementation (`adapters/ingress/ais/`), and the A1-02 entry above
records the promotion bar as met. The paragraph stays as written because it is
the experiment that was proposed. The pre-push cold read flagged the
contradiction between this paragraph and the entry above; this note closes it.

---

## Cycle X1 — 2026-07-28 (cross-repo exchange with the fielded consumer)

Raised while checking whether the Praesens deployment's CoT egress had
inherited this cycle's hardening. It had not, because it never had the defects;
but their note on JSON Schema `format` semantics pointed at our own kernel.
Confirmed independently on both stacks before being written down.

| # | Tension | Gates in play | Status |
|---|---|---|---|
| X1-01 | The kernel does not constrain `event.ts` beyond a trailing `Z` | 3, 5, 6 | **CLOSED 2026-08-03** — v1.1.0 structural shape + gateway plausibility window; locked v1.0 untouched by the lock doctrine |
| X1-02 | A weaker check keeps standing in for a stronger one that exists | 5, 7 | **TERMINAL 2026-08-03 — inventory ran, result recorded on the entry** |
| X1-03 | The retirement rule reads silence as death, which inverts for constitutional rules | 7 | OPEN |

### X1-01 — The kernel does not constrain `event.ts` · CLOSED 2026-08-03

**Closed at both layers the contract allows, and deliberately not at the
one it does not.** The v1.1.0 utcDateTime pattern now enforces structural
calendar shape (the year-0001 and month-88 corruption classes die; a
schema is a shape gate, so February 30 passes and the description says
so), and the gateway carries a config-gated, warn-only plausibility window
(ts_plausibility_horizon_ms, EVENT_TS_IMPLAUSIBLE) per section 5.7's
assignment of cross-event plausibility to the policy and runtime layer.
The locked v1.0 utcDateTime is untouched: after the lock-baseline
adjudication, narrowing it was never on the table, and its hash anchor
would have gone red. The original deferral note below predates that
adjudication; v1.1.20 is behaviour-changing on the v1.1 lane only.
Original entry as written:

`utcDateTime` is `{"type":"string","format":"date-time","pattern":"Z$"}`. Under
JSON Schema 2020-12 `format` is **annotation-only**, so `pattern` is the entire
constraint and it requires only a trailing `Z`.

**Reproduction (with a control, which is the load-bearing part).** Mutate only
the STATE event's `event.ts` in `examples/zmeta-examples-1.0.jsonl`, then run
`python tools/validate.py --file <copy> --profile H --strict`:

| `event.ts` | result |
|---|---|
| unmutated control | exit 0, 4/4 passed, no diagnostics |
| `2025-02-29T00:00:00Z` (non-leap Feb 29) | exit 0, accepted |
| `2026-02-30T00:00:00Z` | exit 0, accepted |
| `2026-13-01T00:00:00Z` | exit 0, accepted |
| `garbageZ` | exit 0, accepted |
| `Z` | exit 0, accepted |

A single letter `Z` is a valid operational timestamp to this kernel. Confirmed
independently by the consumer against their pinned v1.1.18 submodule.

**The documented mitigation is vacuous.** `adapters/egress/cot/README.md` and
`adapters/egress/jreap/README.md` both attribute the looseness to the absence of
"an installed `FormatChecker`", which implies installing one closes it. It does
not: `jsonschema.FormatChecker()` does not register `date-time` unless the
optional `rfc3339-validator` package is present, that package is declared in no
requirements file here, and an unregistered format silently conforms
(`fc.conforms("garbageZ","date-time")` is `True`). Member of the P2-D1 class.

**Why it is a gate-5 tension, not merely a gap.** Contract §6 requires UTC
RFC3339. The requirement therefore lives in prose while the structure permits
anything ending in `Z` — load-bearing meaning in free-text, which is the
inversion gate 5 exists to prevent. The egress adapters do refuse (verified: the
CoT adapter returns `None` for `2026-02-30T00:00:00Z`), so projections are
protected. What is unprotected is any consumer that validates an event, is told
it is valid, and then reads `ts` for freshness, staleness, ordering, or TTL.

**Options, outer rings first.** (1) Add `rfc3339-validator` and enable format
checking in the reference validators — non-governed, but behaviour-changing:
events that pass today would newly fail, so it needs a conformance-impact pass
and must ride a release deliberately. (2) Tighten the `utcDateTime` pattern to a
real RFC3339 regex — governed schema change. (3) A policy-layer semantic check —
governed policy change. (4) Decide the current split is correct and say so in
the contract: the kernel accepts, the egress refuses. Cheapest, and it makes the
prose match the structure.

**Not fixed, deliberately.** Discipline 10: no observed failure. The consumer's
production readback shows zero external producers, so no bad `ts` has ever been
emitted at either end. Sequencing recorded: tag v1.1.19 as-is, which stays a
clean additive cut; handle this in v1.1.20, which is then behaviour-changing
rather than additive — a distinction the consumer's pin-advance review keys on.

### X1-02 — A weaker check keeps standing in for a stronger one · TERMINAL 2026-08-03, the inventory ran and this is its result

**The one-time gate inventory the 2026-08-02 adjudication ordered was
executed in full: 21 cited gates enumerated, the stronger sibling of each
named, and every safe, local, never-run stronger form actually run.** The
enumeration and per-row results live in the v1.1.20 push records; the
outcome in one paragraph: five real defects, two severe, three lesser.
Severe: every published SHA256SUMS carried wrong text-asset checksums back
to v1.1.0 (signer fixed, errata published, sixteen entries across fifteen
tags); and the v1.0 schema's subtype enforcement had drifted from its
baseline, which forced the lock-baseline adjudication recorded as L1-01
below and ended with the lock anchored by hash in
gateway/tests/test_v1_lock_baseline.py. Lesser, queued with owners: the MVP
bundles carry no hash-pinning of bundle-unique content, gateway --self-test
runs the weak base pack and is the only in-bundle check, and the CoT
round-trip laundering the inventory re-demonstrated was fixed in wave 1.
Also run clean: all 20 conformance-class claims re-executed with matching
counts, and the bundles byte-verified against all 84 manifest-pinned
artifacts. **The entry closes with a result, not a shrug: eight instances
taught that the class does not spare fresh, named, guarded-against checks,
and the inventory converted "know what each green means" from an aspiration
into an executed, recorded pass. No standing apparatus was minted, per the
adjudication; recurrence lands on a fresh entry citing this one.**

**Closeout note, 2026-07-30.** The lifecycle rule below says a tension must
reach a terminal status on its third recurrence. This entry is at five instances
across two repositories and is still OPEN, held there by a detection question
its own text calls answerable in an afternoon, which has now gone two days
unstarted. The rule fired and was overridden by judgement. That is recorded
rather than quietly repeated, because a threshold that is passed without comment
is not a threshold.

The honest reading: this entry is not waiting for more evidence, it is waiting
for an afternoon. Two dispositions are available and a third is not. Either the
detection question gets answered, at which point the entry goes terminal with a
result, or it goes terminal without one as HELD-FIRM with the question recorded
as declined. Carrying it open through another cycle should stop being an option.
**Maintainer's call.**

**SIXTH INSTANCE, 2026-07-31, and it is the sharpest available.**
`gateway/tests/test_changelog_keeps_up.py` was written at the previous closeout
to close the records-lag watch-item with a mechanism. It asserted `[Unreleased]`
was non-empty. One day later a session shipped an adapter, corrected a doctrine
entry and renamed a cycle, none of it reached the CHANGELOG, and the check
**passed**, because the previous day's entries were still sitting there.

Not vacuity: it carried a mutation test, the mutation test was honest, and it
would have caught the empty case it was written for. It is exactly this entry's
class — a cheaper sibling of the right check ("is the section non-empty" for "is
the current work described"), passing, and the passing is what stopped anyone
asking. **Written by the author of this entry, one day after writing it.**

That is the strongest evidence available that this class is not an attention
problem. It was fresh, it was named, it was the thing being guarded against, and
it still happened. Strengthened red-first the same session: the newest dated
`[Unreleased]` entry must now be at least as recent as the worklog's
last-updated date, demonstrated failing on the real stale state before the fix.

**Terminal-call input from the 2026-07-31 pre-push cold read, which attacked
the strengthened check by mutation.** Verdict: the strengthening is materially
stronger than what it replaced and it is still a cheaper sibling of the intent,
because it compares hand-maintained dates where the intent is about prose. The
demonstrated residue: it is blind when both record surfaces lag together, which
is the natural way the guarded defect occurs; a dated line with no content
satisfies it; a one-token date bump on yesterday's entry recreates the exact
state it was written against and passes; a future-dated typo satisfies it
permanently; and it skips for the remainder of any release day. The same read
also found the strengthening's red demonstration lived only in a commit
message, the session-act proof the playbook forbids, closed the same day with
an in-tree mutation canary and the residue written into the check's own
docstring as known limits. Deliberately not counted as a seventh instance: it
is the sixth instance's check, examined harder, not a new substitution. What it
adds to the terminal call is evidence that even the corrected form of a check
in this class reverts toward the cheaper sibling, which strengthens the case
for answering the detection question rather than closing HELD-FIRM.

**TERMINAL CALL MADE 2026-08-02, maintainer adjudication: the detection
question gets answered once, inside the v1.1.20 push's validation phase.**
The shape: enumerate every gate the battery, CI and closeouts cite; name the
stronger check each one stands in for; run the stronger forms once; fix what
that finds; close this entry with the result. Deliberately NOT a standing
inventory artifact with a currency check, because that mints permanent
apparatus in exactly the way the v1.1.19 after-action warned against, and
the inventory itself would become one more surface that can rot. The entry
goes terminal when the inventory's result is recorded here. Two further
adjacent instances from the same day the call was made, both the author's
own and both caught by existing guards, are recorded in the after-action
log rather than counted, per the SIM1-02 precedent on count inflation.

**Not counted as an instance: SIM1-02**, the `drops` counter read as a loss
counter. The shapes are adjacent and not the same. X1-02 is a *check* being
substituted by a cheaper sibling that shares its name or neighbourhood. SIM1-02 is
a correctly scoped *counter* being read as though its scope were wider, with no
substitution involved. Counting it here would inflate the number that drives the
lifecycle decision above, which is the one place an inflated count does real
damage. Recorded as its own entry with the relationship stated.

Three instances in a single day, all in this session, each one a case where the
stronger check already existed and something cheaper was being run in its place:

1. `validate_release_package.py --templates-only` ran in the battery, the kernel
   gate and CI, while `--package-dir` — the mode that compares the package's
   recorded hashes against the live manifest — was never run for the cut. A
   stale package acquired a pinned checksum.
2. Release-artifact completeness lived as manual checkboxes in
   `RELEASE_CHECKLIST.md` rather than as a check. The cut sat with only its
   release notes through a validating manifest, a validating package, a green
   battery and green CI.
3. `pattern: "Z$"` stands in for `format: date-time`, which is annotation-only
   under 2020-12 (X1-01 above).

**Two of the three were invisible to every automated gate**, because the gate
was running the weaker mode. The pattern is not "we lack checks" — it is that a
cheaper sibling of the right check is easy to wire up and indistinguishable from
it in a green summary.

Instances 1 and 2 are closed by checks in this cycle. Instance 3 is escalated,
because closing it changes what validates.

**Sharpened by the fielded consumer, 2026-07-28, and the sharpening is the
useful part.** Their §9.1 says an assertion gets treated as evidence. This says
something narrower and more actionable:

> **A check that exists gets substituted by a cheaper one that shares its name
> or its neighbourhood, and the substitution survives precisely because the
> cheaper check passes.**

Two further instances from their estate, taking the count to five across two
repositories: `check_links --offline` validating a single link across the whole
documentation estate while being cited as closeout evidence, and mutation
testing standing in for reading assertions against intent.

**The detection question it implies**, which is answerable in an afternoon and
is the reason to keep this open rather than close it:

> **For each gate we cite, what is the stronger check it is standing in for,
> and when did we last run that one?**

Note the shape of the failure mode: in all five instances the cheaper check was
*green*, and its greenness is what prevented anyone from asking. That is why
this is not simply "run more checks" — it is "know what each green means".

**Deliberately NOT minted as a playbook discipline.** Three instances in one day
is one session's evidence, not recurrence across cycles, and the v1.1.19
after-action already records that the apparatus is large relative to the thing
it governs. A rule proposed on the day its evidence appears is exactly the kind
that should have to earn its place. Logged so that a later instance finds a
record waiting rather than starting the count over — which it now has, twice,
from a second repository.

### X1-03 — The retirement rule reads silence as death · OPEN

The Lifecycle section below says a rule that has **never fired** after several
cycles is a "retirement candidate… documentation pretending to be a guardrail."
The fielded consumer's audit playbook (§9.3) argues that this inverts for one
class of rule, and the argument holds here:

> An after-action log can only measure **procedural** rules. A **constitutional**
> rule — layer discipline, authority boundaries, adapter obligations — succeeds
> by making violations not happen, so it can never generate a "this caught
> something" row. Reading its silence as death is reading the instrument
> backwards.

They flagged it at this repository specifically: **a spec repo is mostly
constitutional rules, and a naive earn-your-place pass would gut exactly the
wrong half.** The live instance is already on the board — the playbook's Status
scoring carries "the one-third introduction cap has NEVER fired" as a
watch-item, and the cap is plausibly working by deterrence rather than sitting
inert. There is no way to tell those apart from firing counts alone.

Not resolved here. The likely shape of a fix is to classify each rule as
procedural or constitutional *before* scoring it, and to score only the
procedural ones on firing count — but that adds a step to the governance
apparatus in order to protect the governance apparatus, which is its own tension
with gate 7. Recorded for the maintainer, since amending the lifecycle rules is
a change to how every other rule is judged.

### The observation that found it, and a candidate rule

This was already recorded **three times** in this repo — both adapter READMEs
and `docs/r1_11_full_stack_audit.md` — each time as the reason that one
component defends itself. Three independent local defences, three write-ups,
and never once a kernel question.

> **A fact known only where it is worked around is not a decision anybody has
> taken.**

The consumer generalised it better than the original, and against their own
earlier heuristic (which counted duplicated *facts*):

> **When the same workaround appears in more than one component, the thing being
> worked around is an undecided question, not a local quirk.**

Two instances so far, from opposite directions: one gap defended in three places
here, one fact maintained in six places there. Both are duplication substituting
for a decision, and in both cases the duplication is what hid the need for one.

**Recorded as a candidate, deliberately NOT minted as a playbook discipline.**
The v1.1.19 after-action already flags that the apparatus grew by three doctrine
entries, a discipline, a standing artifact and two checks in one cycle, and that
gate 7 binds the guiding documents as much as the kernel. "Log freely, change
rarely" applies here: let it earn promotion by recurrence rather than by seeming
good on the day it was written.

---

## Cycle L1 — 2026-08-03 (the v1.1.20 push, lock forensics)

| # | Tension | Gates in play | Status |
|---|---|---|---|
| L1-01 | A lock without a dated birth certificate invites baseline confusion in both directions | 3, 6, 7 | **CLOSED** — provenance note + dual hash anchors shipped with the adjudication |

### L1-01 — The lock needed a birth certificate · CLOSED 2026-08-03

Two adjudications in two days went opposite directions on the same
question because the lock's baseline was undated. The 2026-04-26 stamp
declared the contract locked while it still said any non-empty subtype; the
2026-05-07 lockdown audit rewrote it into the enforceable form with the
closed namespace and built the verification apparatus in the same commit;
and nothing anywhere recorded which of those moments WAS the lock. The
first adjudication (2026-08-02) read the April tag as the baseline and
restored free-form subtypes; the contract scout then surfaced section 7.3,
forensics dated both candidates, and the second adjudication (2026-08-03)
settled it: the lockdown audit is the lock, because it is the baseline
every subsequent verification descends from and the one that predates all
fielded adoption.

Both adjudications were made honestly on the evidence in front of them;
the defect was that the evidence had to be excavated at all. The closure is
structural, not procedural: the contract now opens with a lock provenance
note naming its own hardening date and the audit document that performed
it, and gateway/tests/test_v1_lock_baseline.py anchors both the contract
text and the v1.0 schema by content hash, so every future edit to either
surface arrives with an adjudication or arrives red. The class this closes
is not subtype vocabulary; it is any future argument about what the lock
meant, which is now answerable by reading one paragraph instead of running
two days of forensics.

## Cycle SIM1 — 2026-07-30 (internal simulation reps)

**Named SIM1, not S1, and the reason is worth one line.** This cycle was first
written as `S1-01`..`S1-05` on 2026-07-30. That collides with the historical
`S1-01A`..`S1-19` work-item series from the original build phase, which is
referenced throughout the handoff's Key Docs table and the worklog, and which
includes a completed item literally called S1-05
(`docs/s1_05_encoding_negative_validation_plan.md`). A doctrine log whose whole
value is that entries are citable cannot have two meanings for one identifier.
Renamed on 2026-07-31, one day old and before any external citation. The
historical series was not touched: it is a dated process record, and the rename
was verified to leave every lettered reference unchanged.

Raised while running the shipped deployment path rather than reading it: two
gateway nodes, the containers, the ADS-B adapter on a synthetic snapshot, the
command-evidence loop, and a throughput sweep. The operating rule for the cycle
was that a real break gets fixed and an assumption of behaviour gets recorded
with the live validation that would settle it. Three of the four entries below
are the second kind. The breaks found in the same session were fixed and are
recorded in `docs/zmeta_live_test_checklist.md` rather than here, because they
were defects with a known fix and not tensions between gates.

| # | Tension | Gates in play | Status |
|---|---|---|---|
| SIM1-01 | `confidence` reaches CoT only as free text, with no structured element | 4, 5 | OPEN |
| SIM1-02 | A counter that can only see what arrived is read as a loss counter | 3 | OPEN (observation) |
| SIM1-03 | The rehearsal corpus exercises a path the real input does not | 5, 7 | OPEN (observation) |
| SIM1-04 | Operational tooling accumulating inside a data standard | 1, 7 | OPEN (maintainer, criterion set) |
| SIM1-05 | A v1.0 deployment cannot carry uncertainty the v1.1.0 branch already can | 2, 3 | **CLOSED 2026-08-09** |

### SIM1-01 — `confidence` reaches CoT only as free text · OPEN

`adapters/egress/cot/zmeta_to_cot.py` composes `confidence=<value>` into
`<remarks>` and emits no structured `<detail>` child carrying it. Captured off
the wire on 2026-07-30 from the stock two-node path:

```xml
<detail>
    <contact callsign="Track track-001" />
    <remarks>confidence=0.76</remarks>
</detail>
```

The `labels_on` element present in the same builder is a TAK rendering toggle,
not a quality projection. The error ellipse does have a structured home
(`point@ce`, and `precisionlocation` once the operator asserts pedigree), so
`confidence` is the field with no structured channel at all.

**The tension.** Gate 5 says semantically load-bearing data lives in structured
parseable fields and names CoT `<detail>` sub-elements as the example, never
free text alone. Gate 4 says the canonical ZMeta event is the source of truth
and every egress is a lossy projection, which argues that CoT is the
human-facing rendering and a machine consumer should read the ZMeta event.
Both readings are defensible and they disagree here.

**Why it is not being fixed on the spot.** Adding a `<detail>` child changes
what every existing CoT consumer receives, and the Praesens review already
carries the same observation as its finding #5, so this is the second instance
across two stacks and the shared root is upstream. Changing egress shape to
settle a doctrinal question, with no consumer asking for it, is the failure
mode discipline 10 exists to prevent.

**What would settle it, live:** does any CoT consumer at the event need to read
confidence by machine, or is the remarks string what a human reads while
machine consumers take the ZMeta stream? "Nobody parses it" closes this and
`<remarks>` stays the whole answer.

### SIM1-02 — A counter that can only see what arrived is read as a loss counter · OPEN

The gateway's `drops` counter is honest about what the gateway discarded. It
cannot see datagrams the kernel dropped before `recvfrom`, because the process
was never given them. Measured on one x86 host: 100% delivery at 400 events/s,
saturation near 422/s, and at 1000/s offered only 44% arrived while the node
reported `drops=0 violations=0` throughout.

Nothing here is a lie. The operator-facing reading is the problem: `drops=0`
alongside `violations=0` is exactly what a healthy node prints, and it is also
what a node prints while more than half its sensor feed is discarded upstream.
That is the X1-02 family seen from the metrics side, where a green reading stops
the question.

Recorded, not fixed. A receive-buffer overflow count is available per platform
(`SO_RXQ_OVFL` on Linux, nothing portable on Windows), so the fix is
platform-specific code for a condition no deployment has yet reported. The
cheat-sheet row added to the quickstart is the cheap half.

**What would settle it, live:** does any deployment run near capacity? If none
do, this stays a documentation row forever, which is the right outcome.

### SIM1-03 — The rehearsal corpus exercises a path the real input does not · OPEN

The pre-event wire check replays `examples/zmeta-examples-1.0.jsonl`, which
contains one `STATE_EVENT` and therefore produces CoT. An ingress adapter emits
`OBSERVATION_EVENT`, and CoT projects `STATE_EVENT` only, so five clean ADS-B
observations produced zero CoT on the same path minutes later. The rehearsal
passes and the live run shows nothing, which is worse than a rehearsal that
fails, because it converts a missing component into a mystery on the day.

The generalisation worth watching, and the reason this is logged rather than
just fixed in the guide: **a fixture chosen to demonstrate every feature is not
a fixture representative of the input.** The example corpus is deliberately one
of each event type. That makes it a fine conformance sample and a misleading
smoke test. Same shape as the vacuous-verification family, one level out: the
check passed, and it passed for a reason unrelated to what the operator was
about to do.

Not minted. One instance, and the guide correction may be the whole remedy.

**What would settle it, live:** do teams arrive with a fusion or tracking stage?
If most expect the gateway to promote observations to track state, this stops
being a rehearsal-fixture question and becomes a missing-component question.

### SIM1-04 — Operational tooling accumulating inside a data standard · OPEN

Raised by the maintainer on 2026-07-30, when the simulation harnesses from the
rep cycle were committed to `tools/sim/`: *"I just want to make sure we do not
start a habit of overstuffing what is simply meant to be a data standard,
although these tools are invaluable."*

Both halves are true at once, which is what makes it a tension rather than a
decision. The harnesses found two real deployment breaks that reading the code
had not, so their value is demonstrated rather than assumed. And a data standard
whose repository fills with operational tooling stops being a thing you can read
and adopt, which is gate 1 pointed at the repository instead of at the event
model: an alphabet, not a dictionary, applies to what we ship as much as to what
we define.

**Resolved for now by making the boundary structural rather than a promise.**
`gateway/tests/test_sim_boundary.py` asserts that no governed artifact imports
or invokes anything under `tools/sim`. The dependency is allowed to run one
direction only. That test carries its own non-vacuity checks, including one that
proves the detector fires, which caught a real gap in the detector on the day it
was written.

**The criterion for extraction, agreed the same day:** when the harnesses grow
their own configuration surface, their own dependencies, or an audience that is
not "someone integrating a sensor with ZMeta", they are a product and belong in
their own repository. While the boundary test holds, that move is a directory
rename plus a pointer, so deferring the decision costs nothing and keeping the
option open is the whole point.

**What would force the decision:** a third harness, a dependency outside the
standard library, or any request to run these in CI. Any one of those is the
trigger to answer the question rather than re-defer it, and the N=3 lifecycle
rule below applies normally.

Worth stating because it is easy to lose: the surface being protected is not
disk space. It is that a reader can tell, in one look, which parts of this
repository define the standard and which parts merely help you operate it.

### SIM1-05 — A v1.0 deployment cannot carry uncertainty the v1.1.0 branch already can · **CLOSED 2026-08-09**

Found while building `adapters/projector/track`, which is the first component
that has to carry a measured accuracy from an observation onto a track.

Under the locked v1.0 kernel, `$defs/geo` is exactly `lat`, `lon` and `alt_m`
with `additionalProperties: false`, and `TrackStatePayload.geo` is a plain
`$ref` to it. There is no field on a v1.0 `STATE_EVENT` for positional
uncertainty. An `OBSERVATION_EVENT` can carry one, under
`payload.quality.error_ellipse_m`, and the ADS-B adapter populates it with a
real value derived from `nac_p`.

`adapters/egress/cot` reads `geo.error_ellipse_m`, which exists only on the
v1.1.0 experimental geo, and its own comment says so: *"the only schema-valid
uncertainty source on geo (v1.1.0 $defs/geo; v1.0 geo carries none)"*.

**Observed end to end 2026-07-30.** An ADS-B target with `nac_p: 9` produces a
30 m semi-major ellipse on the observation. The projected track reaches TAK as
`ce="9999999.0"`, CoT's unknown-accuracy sentinel. The measurement exists, is
honest, and cannot travel.

Two smaller things fall out of the same look. The key names differ between the
two homes: the observation carries `semi_major_m` under `quality`, and the CoT
reader expects `semi_major` under `geo`. And the repository's own CoT example is
a v1.1.0 event for exactly this reason, so the documented example does not
demonstrate what a v1.0 deployment will see.

**This is not R1-11-08**, which is about zero-filling a *partially* populated
ellipse and overstating precision. This is the opposite direction: a fully
populated, correctly measured ellipse with nowhere to go.

**Gate 2 is what makes it a tension rather than a limitation.** Consumer
sufficiency asks whether a downstream consumer has what it needs to responsibly
act. An operator deciding whether a track is precise enough to act on is the
canonical case, and on a v1.0 track the answer is always "unknown" no matter how
well the sensor characterised itself. Nothing is overstated, which is the half
the honesty gates protect, and the half they do not protect is that a real
measurement is silently unavailable.

**CORRECTED 2026-07-31, and the correction is most of the entry.** The framing
above overstates. Prompted by an external comparative survey making the same
claim from a literature angle, I re-checked the tree instead of accepting the
agreement, and the agreement was wrong in the same direction I was.

`ERROR_ELLIPSE_M` is a **registered, approved extension** in
`spec/extension-registry.yaml`: `status: experimental`, `version_branch: 1.1.0`,
`schema_status: implemented`, `conformance_status: implemented`,
`review_state: approved`, `allowed_event_types: [OBSERVATION_EVENT,
FUSION_EVENT, STATE_EVENT]`, `payload_scope: [payload.geo.error_ellipse_m,
payload.estimated_state.geo.error_ellipse_m]`. Verified directly against both
schemas: v1.1.0 `$defs/geo` carries `error_ellipse_m` referencing a formal
`$defs/error_ellipse` with `semi_major`, `semi_minor`, `orientation_deg` and an
optional `probability` enum (`1_SIGMA`, `CEP`, `CE_90`, `CE_95`). v1.0 does not.

So this is **not** an expressibility gap in ZMeta, and the original heading was
wrong. A v1.1.0 track carries positional uncertainty today, on the branch built
for exactly this, with a probability level attached — which is better than the
scalar most peers manage. What is true is narrower: **a deployment on the locked
v1.0 kernel, which is what every shipped artifact and the gateway default use,
cannot carry it, so a measured accuracy does not reach the display.**

That makes this an adoption-path question, not an alphabet question, and it
belongs with the experimental-split experiment from cycle A1 as a concrete thing
v1.1.0 already buys rather than as a new gap to close.

**The one thing here that is a genuine defect, and it survived the
correction.** The two homes spell the same quantity differently: the v1.0
generic quality object uses `semi_major_m` / `semi_minor_m` (the ADS-B adapter
emits these), and the v1.1.0 formal contract uses `semi_major` / `semi_minor`,
which is what `adapters/egress/cot` reads. A deployment moving from the v1.0
quality object to the v1.1.0 formal block gets silence rather than an error,
because the reader looks for a key the writer never wrote. That is a small,
cheap, real fix and it is independent of the adoption question.

**Corrected 2026-07-31 by the pre-push cold read, before this entry left the
tree, and the paragraph above is wrong in both of its factual claims.** First,
the v1.0 schema defines no ellipse member spellings at all: `semi_major_m` is
the ADS-B adapter's own convention inside the free-form `quality` object, not
a v1.0 definition. Second, the failure mode is not silence. The v1.1.0
`$defs/error_ellipse` requires all three members and forbids unknown ones, so
a validating path refuses the wrong spelling loudly. The non-validating CoT
path emits `point@ce` as the unknown-value convention, which is honest, and
then renders `<remarks>` and `<precisionlocation>` from `.get(key, 0)`
defaults, a fabricated zero-size ellipse claim on an event that asserted no
such thing. The adjacent claim that nothing here is overstated did not survive
this look either. The fabrication itself is a defect in published egress code,
outside the reviewed range, and is queued in the handoff rather than fixed
here.

**PROMOTION DECIDED 2026-08-02, maintainer adjudication.** `error_ellipse_m`
moves from the v1.1.0 experimental branch into the v1.1.20 formal cut, with
the `semi_major_m` spelling divergence reconciled in the same governed wave.
The deciding input: the readiness audit reproduced the fielded
LOB-fusion-to-ellipse retask workflow end to end and confirmed a live user
stands on the experimental branch today, hitting an undocumented wall when
building from the public trunk. The adoption-path question this entry framed
is answered by promotion rather than by documentation.

**Method note worth keeping.** An outside review and an inside rep agreed on
this finding, and the agreement made it feel settled. Two sources reaching the
same wrong conclusion is not corroboration when neither checked the registry.
The rule this earns: **when an external claim matches your own, that is the
moment to verify it, not the moment to stop.**

**What would settle the remaining question, live:** does any operator at the
event act differently on a track with a 30 m ellipse than on one with an unknown
one? If everything is treated as approximate anyway, the v1.0 limit costs
nothing and the adoption question answers itself.

**CLOSED 2026-08-09 (records pass).** The implementing wave landed in
v1.1.20: the promotion decided above shipped with the ADS-B NACp ellipse
moved to `payload.geo.error_ellipse_m` under the formal member spellings,
conditional `zmeta_version: "1.1.0"` stamping on exactly the events that
carry it, and the registry entry adopted (`CHANGELOG.md` `[1.1.20]`
wave-1 entry; `spec/extension-registry.yaml` ERROR_ELLIPSE_M). Under the
lifecycle rule a DECIDED entry goes terminal when its wave lands; the wave
landed in the push that closed the cycle, and this status line is the
bookkeeping catching up. The live operator question the entry ends on
stays open on the field checklist, unmoved by this closure.

---

## Cycle B1 — 2026-08-09

Seeded outside an audit. A 2026-08-03 bespoke-sensor planning session hit
this wall from two independent design lanes, and the 2026-08-09 register
sweep confirmed the silence was recorded nowhere in the repository's open
registers. The evidence table was built by reading every shipped ingress
adapter's emission code, with file and line cited for each. One entry.

| # | Tension | Gates in play | Status |
|---|---|---|---|
| B1-01 | The referent of `payload.geo` on an OBSERVATION_EVENT is unstated | 2, 3, 5 | **DECIDED 2026-08-09** |

### B1-01 — The referent of `payload.geo` on an OBSERVATION_EVENT is unstated · **DECIDED 2026-08-09**

The contract defines `geo`'s datum (6.1), units (6.2), completeness rule
(6.8) and, since v1.1.20, its dimensionality (21.8). It never says whose
position it is. Section 7.4 lists `geo?` on ObservationPayload with no
relationship stated to the observation's subject or to the observing
sensor, and a search of the normative text for any referent statement
returns nothing. Every shipped ingress adapter had to answer the question
anyway, and they split four ways, correlated with sensor class:

| Adapter | Reading of observation `geo` | Evidence |
|---|---|---|
| adsb | subject: the aircraft's broadcast position; receiver position never emitted | `adsb_to_zmeta.py:192-234` |
| ais | subject: the vessel's broadcast position | `ais_to_zmeta.py:165-203` |
| sapient | subject: `DetectionReport.location`; the node's own position is explicitly extension-only ("never canonical geo") | `sapient_to_zmeta.py:872-873, 1243-1246` |
| kraken | the sensor's own position (`sensor_geo` kwarg, "sensor position" in its docstring); the emitter gets only a line of bearing | `kraken_to_zmeta.py:162, 210` |
| moth | the sensor's own position | `moth/README.md:79-83` |
| bladerf | the sensor's own position (`geo.lat: input.sensor_lat` in the mapping pack) | `bladerf_to_zmeta.py:285-287`; `edge-comms-bladerf/mapping.yaml:19-21` |
| signalhunter | neither: `geo` never emitted, `geo_status: UNAVAILABLE` hardcoded, and the sensor position parked in an ad-hoc unregistered key `payload.quality.sensor_position_2d` | `signalhunter_to_zmeta.py:421-425` |
| eo-cv | subject preferred, sensor fallback, and the only adapter that labels which: `claim.geo_source` is `detection` / `fc_fallback` / `unavailable` | `eo_cv_to_zmeta.py:173-214` |
| klv | unqualified: MISB 0601 offers sensor position, frame center and target location, and the template never says which it reads | `klv_to_zmeta_template.py:26-28` |
| example-vendor | unqualified, de facto sensor position — the reference adapter new authors copy is silent on exactly this ambiguity | `example_vendor_to_zmeta.py:115-120` |

**The downstream consequence is what makes this gate 2 and 3 rather than
tidiness.** The one shipped ZMeta-to-ZMeta consumer,
`adapters/projector/track/track_projector.py`, copies observation `geo`
straight into a track's `STATE_EVENT` geo: it reads the subject
convention. Feed it a kraken, moth or bladeRF event and it would place a
track on the sensor. The only thing preventing that today is accidental:
`DEFAULT_IDENTITY_PATHS` is limited to `adsb_icao24` and `ais_mmsi`, so
the sensor-position adapters are refused as `refused_no_identity` before
their geo is ever read. Any deployment that widens `identity_paths`
loses that protection silently.

**The missing sentence is one line of normative text:** on an
OBSERVATION_EVENT, `payload.geo` is the position of the observation's
subject; a sensor's own position is not a subject position, and it
travels under source or extension vocabulary, never canonical geo. The
sapient adapter already implements exactly this reading and the eo-cv
adapter labels its deviation from it, so the sentence ratifies the
strictest existing practice rather than inventing one.

**DECIDED 2026-08-09, maintainer adjudication: this entry now, the
normative sentence in a scheduled governed wave.** Landing the sentence
is wire-compatible but makes kraken, moth, bladeRF and the
example-vendor reference retroactively non-conforming, moves the
contract hash anchor, and needs an agreed home for a sensor's own
position before the old one is closed (signalhunter's unregistered
`sensor_position_2d` is what pressure invents in the absence of one). So
it is a wave with adapter work, not a records edit. Until that wave
lands, this entry is the record a fielding party can find: a
line-of-bearing adapter's `geo` is the sensor, not the emitter, and a
consumer that widens the track projector's identity paths must know
that before it does.

---

## Cycle C1 — 2026-08-10

Seeded by an independent technical review that compared ZMeta against CoT,
MISB ST 0601, STANAG 4676, OGC/ISO OMS, W3C PROV, Sparkplug B, MAVLink,
ASTERIX, C2PA and CloudEvents. The review had no raw-byte access to the
normative files and worked from the README, the professional overview,
CONFORMANCE.md, the CHANGELOG and this log. Every claim it made was then
verified against the tree at `8b24da5` with file and line cited.

The review's own findings were roughly a third accurate: it was correct that
no per-event integrity exists and that covariance and sequence primitives are
absent, wrong about the UUIDv7 version nibble, schema-level laundering guards,
deduplication and deterministic CBOR, and stale on 2-D geo, the `event.ts`
pattern and the v1.1.21 code mint. The entries below are mostly not its
findings. They are what verifying its findings turned up.

| # | Tension | Gates in play | Status |
|---|---|---|---|
| C1-01 | The MAVLink ingress publishes an MSL altitude as canonical HAE | 3, 5 | **MINTED 2026-08-10** |
| C1-02 | A release-notes claim credits a runtime layer that no-ops on the class it names | 3 | **MINTED 2026-08-10** (erratum) |
| C1-03 | The governed corpora carry no malformed-timestamp vectors, while the crosswalk cites them as the evidence | 3, 7 | **MINTED 2026-08-10** |
| C1-04 | Fusion and state uncertainty cannot express a correlated distribution, and the gap is unbooked | 2 | **OPEN — decision-due** |
| C1-05 | Gap detection is booked only under adversarial trust, so a cooperative-link reliability need has no home | 2, 6 | **MINTED 2026-08-10** |
| C1-06 | Per-event signing provably cannot be met in the outer rings, because the event root is closed | 1, 6 | **OPEN** |
| C1-07 | Float width is unspecified, so two conforming CBOR backends emit different bytes for one event | 4, 7 | **OPEN — decision-due** |
| C1-08 | A format checker is installed at a dozen sites and validates nothing | 3 | **DECIDED 2026-08-10** |
| C1-09 | An outside reader treats a published pressure log as the defect list | 5 | **OPEN** |
| C1-10 | An absent altitude refuses while an unusable one degrades to 2-D | 2, 3 | **OPEN** |
| C1-11 | Lineage cycle prevention covers self-reference on one path, not cycles | 3 | **OPEN** |
| C1-12 | A verified fix proves its instance while the class stays unswept | 3, 7 | **OPEN** |

### C1-01 — The MAVLink ingress publishes an MSL altitude as canonical HAE · **MINTED 2026-08-10**

Contract 6.2 is a `SHALL`: canonical altitude is Height Above Ellipsoid, and
MSL "is not permitted in canonical ZMeta v1.0 `geo`", with the remedy stated
in the same sentence, "it must convert them or omit canonical `geo`". The
MAVLink template did neither. Its docstring described its own `alt_m` input as
"metres AMSL" (`mavlink_to_zmeta_template.py:364`), it wrote that value
unconverted into `payload.geo.alt_m` (`:459`), and the decoder derived it from
`GLOBAL_POSITION_INT.alt`, which MAVLink defines as height above mean sea
level (`:600-606`). No conversion utility exists anywhere in the repository.

**This is the third appearance of the altitude-datum class.** The July 2026
audit found it in a fielded stack; the ADS-B ingress was then hardened to
refuse it at the source, and says so on its face: `alt_baro` is a pressure
altitude and "never becomes `alt_m`", with the module docstring naming the
fielded finding as its reason (`adsb_to_zmeta.py:64-69`). MAVLink was the same
class, in the same repository, left unfixed. The occurrence rule therefore
forced a terminal status on sight rather than after further instances.

What makes it worse than an ordinary mapping bug is that the surrounding code
is scrupulous. The same function refuses a missing altitude rather than
zero-filling it, refuses the null-island no-fix signature, refuses an
unreported speed rather than asserting a standstill, and refuses a heading
whose frame is undeclared. Every honesty class this template guards is one
where the *absence* of a value was the hazard. The datum defect is the one
where a present, well-formed, plausible number is wrong, and that shape passed
every guard the file has.

**Fixed this cycle, and the fix is the A1-02 mechanism doing the job it was
built for.** The two datums are now separated at the decode boundary:
`GLOBAL_POSITION_INT.alt` decodes to `alt_msl_m` and can never reach canonical
geo, while `GPS_RAW_INT.alt_ellipsoid`, which MAVLink defines as height above
the WGS-84 ellipsoid, decodes to `alt_hae_m` and is the only value admitted to
`payload.geo.alt_m`. When only MSL is available the horizontal fix is still
real, so the position is emitted as the declared 2-D form, `dimensionality:
"2D"` with `geo_status: VERTICAL_UNAVAILABLE` under a `1.1.0` stamp, and the
reported MSL value is preserved as non-canonical
`quality.mavlink_alt_msl_m`. The legacy `alt_m` input key is read as MSL, so
an existing caller degrades to the honest form instead of continuing to
publish a wrong-datum HAE claim. Nine tests pin the behavior, including the
decode-to-translate composition, because a decoder that mislabels a datum
defeats a translator-only guard.

**The general lesson is worth more than the fix.** Every anti-fabrication
guard in this repository keys on absence: a missing value must not become a
zero. A wrong-datum value is present, finite, in range and plausible, so it
passes all of them. The guard that catches it is naming the datum at the
boundary rather than at the destination, which is what `alt_msl_m` versus
`alt_hae_m` does. The remaining ingress adapters that write canonical
altitude should be read against that standard rather than against the
absence-shaped one.

### C1-02 — A release-notes claim credits a runtime layer that no-ops on the class it names · **MINTED 2026-08-10** (erratum)

`release/RELEASE_NOTES_v1.1.20.md:126-131` states that the X1-01 closure
"lands at both lawful layers", the schema pattern on the v1.1.0 branch and a
gateway plausibility window that counts an implausible `ts` on every
`zmeta_version`. The window is version-agnostic as described. It also returns
before doing anything on precisely the malformed class the locked v1.0 lane
still admits: `gateway.py:992-994` parses `ts` and returns `False` when the
parse fails, so an unparseable value is never compared and never counted.
Verified against the shipped module: `garbageZ` and a bare `Z` produce no
warning, while a well-formed out-of-horizon timestamp produces one.

The consequence is narrow but exact. A v1.0 event carrying `ts="garbageZ"`
passes schema validation clean, because the locked pattern is `Z$`, and then
produces zero runtime diagnostics. The fail-closed behavior the X1-01 entry
credits exists only in the egress adapters, which refuse; anything consuming
the forwarded canonical event is unprotected and unwarned.

This is the vacuous-verification class (P2-D1) appearing inside a published
claim rather than inside a test. Published files are not rewritten, so the
correction lands in `docs/release_notes_errata.md` and the gateway now emits
its existing implausible-timestamp diagnostic for the unparseable case, with a
distinguishing detail so an operator can tell an unreadable timestamp from an
out-of-horizon one. No code was minted for it: the occurrence rule reserves
new vocabulary for the third instance, and an unparseable timestamp is
honestly implausible.

### C1-03 — The governed corpora carry no malformed-timestamp vectors · **MINTED 2026-08-10**

Every record in `conformance/must-fail.jsonl` and
`conformance/bad-events/must-fail.jsonl` was parsed against the v1.1.0
structural pattern. Exactly one row had a non-conforming `event.ts`, the
UTC-offset form that even the weak `Z$` pattern rejects. The entire X1-01
corruption class was covered only by
`gateway/tests/test_x1_01_ts_structural_shape.py`, a unit test outside the
governed corpora, while `docs/zmeta_contract_to_stack_crosswalk.md:93` marked
the trailing-`Z` requirement "Enforced" and cited the corpus as its evidence.

The gap is the one that matters most for an outside implementer: conformance
vectors are what an independent stack runs, and on timestamp shape they said
nothing. Vectors covering a garbage string, a bare `Z`, an impossible month,
an impossible hour and an out-of-range year were added on the v1.1.0 lane,
where the pattern actually rejects them, and the crosswalk row now describes
enforcement by layer instead of citing a corpus that did not carry it. No
v1.0-stamped equivalents were added, because the locked schema deliberately
accepts them and a fixture asserting otherwise would be a lie about the lane.

### C1-04 — Fusion and state uncertainty cannot express a correlated distribution · **OPEN — decision-due**

Covariance appears nowhere in `spec/`, `docs/`, `policy/` or `schema/`; the
only occurrence in the repository is inside a figure-generation script.
`ERROR_ELLIPSE_M` is adopted but horizontal-only, with no vertical and no
velocity term, and `FusionPayload.estimated_state` admits only `geo`,
`bearing`, `heading_deg` and `speed_mps`. A fusion consumer receives a scalar
`confidence` and, at best, a horizontal ellipse. Neither the roadmap's
`rejected_or_deferred` list nor the extension registry records the absence,
so this is the one item in the review that was both correct and genuinely new
information.

It is a real gate 2 question rather than an obvious addition. Consumer
sufficiency argues that a fusion consumer cannot responsibly propagate
uncertainty without correlation structure. The alphabet gate argues the
opposite, that a full covariance matrix is a dictionary entry and belongs in a
namespaced extension. Recorded now, per maintainer adjudication 2026-08-10, as
decision-due rather than field-gated: no deployment has to report a problem
before this can be decided, because the modelling question is answerable from
the contract alone.

### C1-05 — Gap detection is booked only under adversarial trust · **MINTED 2026-08-10**

Sequence counters exist in the record exactly once, as a security concern:
contract 16.3 lists "Source sequence counters or anti-replay windows" under
future mesh trust, the roadmap candidate is `event-signing-anti-replay`, and
the registry reserves `ANTI_REPLAY_NONCE`. That candidate's tripwire fires on
"deployments requiring an adversarial trust boundary rather than the current
cooperative-producer posture".

The need the review actually identified is not adversarial. It is a
cooperative node losing events on a degraded link with no way for the consumer
to know. That tripwire will never fire on it, because no adversary is
involved, so the need had no roadmap home at all. The repository already
measures the consequence and states it plainly:
`docs/zmeta_two_node_quickstart.md:259` records that `drops=0` alongside a
consumer clearly missing events is expected, because "drops counts what the
gateway discarded, not what never reached it", and reports 44% arrival with
`drops=0` at 1000 events/s. Undetected loss is a known, measured property.

A distinct roadmap candidate for cooperative-mesh gap detection was added per
maintainer adjudication 2026-08-10, with its own tripwire keyed to a
deployment losing events undetectably rather than to a trust boundary. The
misfiling, not the absence, was the finding: a booked item under the wrong
heading reads as covered and never comes due.

### C1-06 — Per-event signing cannot be met in the outer rings · **OPEN**

Design Gate 6 directs every need to policy, config, profiles, adapter mappings
and namespaced extensions before schema or core semantics. Per-event signing
is one of the few needs that provably cannot be met there. The event root sets
`additionalProperties: false`, as do `$defs/event`, `$defs/source` and
`$defs/lineage`, so an adopter cannot attach a signature envelope as a
namespaced extension. The schema rejects any unknown top-level member.

The roadmap half-states this. `event-signing-anti-replay` notes that the
"envelope-or-sidecar decision is structural" without saying that schema
closure is what forces the decision. Recorded here so the next reader of Gate
6 does not spend the effort rediscovering that the outer rings are closed on
this one. Two adjacent facts belong with it: the candidate carries
`promotion_evidence: []`, so nothing has been banked toward it, and its
tripwire names the adversarial trust boundary as the trigger, which is
precisely the deployment class most likely to be evaluating ZMeta.

### C1-07 — Float width is unspecified across conforming encoders · **OPEN — decision-due**

`spec/compact-binary-mapping.md:66-73` specifies deterministic CBOR as
definite-length containers, no indefinite-length forms, and canonically
ordered map keys. It says nothing about float width. Both shipped backends
satisfy every bullet and disagree: `zmeta_cbor.py:83` always emits float64,
while the documented `cbor2` fallback emits shortest-float. On the repository's
own fixture value `120.0` that is `fb405e000000000000` against `f95780`.

Two conforming nodes therefore emit different bytes for the same event. This
costs nothing today, because the contract defines cross-encoding equality as
object equality with ordering explicitly non-semantic, and no feature in the
tree hashes an event. It is load-bearing for anything that later signs one,
which is why it is recorded next to C1-06 rather than as an encoding footnote.
The determinism section is also SHOULD-level, so tightening it is a governed
decision about strength as well as content.

### C1-08 — A format checker is installed at a dozen sites and validates nothing · **DECIDED 2026-08-10**

`format_checker=FormatChecker()` was passed at roughly a dozen call sites,
including the gateway's central validator factory. It reads as if format
validation is enabled. It validates nothing for `date-time`, because
`jsonschema` registers no `date-time` checker unless the separate
`rfc3339-validator` package is installed, and that package is not declared.
Confirmed directly: `'date-time' in FormatChecker().checkers` is `False`.

Behavior was never affected, since `pattern` is the real gate on both
branches. The defect is that the presence implies a guarantee it does not
deliver, which is the P2-D1 class exactly. **Maintainer adjudication
2026-08-10: leave the format inert and remove the misleading argument.**
Declaring the dependency was the considered alternative and was rejected for
now: it would make `date-time` genuinely enforce, which would close the v1.0
residual at the validator layer without moving locked bytes, but it would also
start rejecting v1.0 producers whose timestamps are currently tolerated. That
is a fielded behavior change and belongs in a wave that can absorb it. The
question stays available on this entry rather than being lost with the
argument.

### C1-09 — An outside reader treats a published pressure log as the defect list · **OPEN**

This is a finding about the review's method rather than about ZMeta, and it
will recur, so it is recorded rather than remembered. The reviewer had no
raw-byte access and read this log and the CHANGELOG as current state. The
result is systematic: it was stalest on exactly the items most recently
fixed, and reported as live defects the 2-D geo gap closed in v1.1.20, the
`event.ts` pattern closed in the same release, and the violation-code names
superseded by the v1.1.21 mint. Candor about open questions was converted into
an inventory of failures.

That is a real cost of publishing the log, and it is not an argument for
hiding it. It is an argument for two cheap things. The log should carry a
current-state header saying that entries are open questions at the time of
writing and that status lines are authoritative. And the current-facing
documents should carry their own disclosures, because several of the reviewer's
errors were invited by our own summaries rather than invented: the schema
README stated one timestamp rule for both branches without noting that the
v1.0 lane accepts any string ending in `Z`, the README and professional
overview said "identical canonical JSON" without the qualifier the two
normative documents attach, and the field dictionary still described
`error_ellipse_m` as the only canonical geo extension nine days after
`dimensionality` shipped. All three were corrected this cycle. This is the
second external survey in ten days, so the pattern is already n=2.

*Addendum 2026-08-10: the current-state header now exists ("How to read this
log", top of this file), which lands the first of the two remedies named
above. The second, disclosures on the current-facing documents, was corrected
within cycle C1 as the body records. The entry stays open because the finding
concerns a recurring reading pattern rather than a missing sentence, and the
pattern sits at n=2; the next external survey tests whether the header changes
the outcome.*

### C1-10 — An absent altitude refuses while an unusable one degrades to 2-D · **OPEN**

Raised by C1-01's fix rather than by the review. After this cycle the MAVLink
translator refuses to emit when no altitude of any datum was reported, which
is the R1-11 A-06 behavior, but emits the declared 2-D form when an altitude
was reported in a datum it cannot state canonically. Both cases have a real
horizontal fix and no canonical vertical, so the asymmetry needs a reason or
needs removing.

The reason it was left in place this cycle is scope: A-06 is pinned by an
existing test and the adjudicated remedy covered the datum case only. The
argument for keeping it is that a reported MSL value is positive evidence of a
working three-dimensional positioning solution, whereas silence may mean a
degraded telemetry stream, and A1-02's `VERTICAL_UNAVAILABLE` should not
become a way to launder "we never heard an altitude" into "this platform has
no vertical". The argument against is that `dimensionality: "2D"` describes
the geometry rather than the reason, and the horizontal fix is equally real
either way. Left open for the maintainer, with no instance count yet.

### C1-11 — Lineage cycle prevention covers self-reference on one path, not cycles · **OPEN**

`lineage.based_on` is a set of parent identifiers, which makes a lineage graph
a DAG only by convention. What the stack actually enforces is narrower than
that. The reference validator treats an event whose own `event_id` appears in
its lineage as loop risk and forces a reject, and contract 4.5.1 requires a
reflected projection to prove it is not the same semantic event returning
through a lossy adapter path. Both of those guard the external-promotion path
and the one-hop case.

Nothing detects a multi-hop cycle. If A cites B and B cites A, or a longer
ring forms across three or more events, no schema keyword, policy rule or
conformance vector rejects it. JSON Schema cannot express acyclicity, so this
is a policy or runtime question by construction, not a kernel one.

The honest severity is low today and the reason is worth recording, because it
is the reason this stayed open rather than being fixed in this cycle. Building
a cycle requires citing an identifier that did not exist when the parent was
minted, so a cooperative producer using UUIDv7 identity essentially cannot
create one by accident. The realistic sources are a replayed corpus with
rewritten identifiers, a test fixture, or a hostile producer, and the last of
those is the adversarial posture the contract already defers. Recorded so that
the deferral is a decision rather than an assumption, and so a future signing
or trust branch inherits it as a known open edge instead of rediscovering it.

### C1-12 — A verified fix proves its instance while the class stays unswept · **OPEN**

Raised by C1-01's own closing paragraph rather than by the review. After the
MAVLink fix landed, that entry said the remaining adapters "should be read
against that standard". Nothing in the apparatus makes that reading happen.
Every check verifies that a thing was done: the regression test pins the fixed
file, the corpus pins the fixed vector, the release gates verify the fixed
artifact's hash. No check verifies that the thing was done everywhere it
applies. The altitude-datum class needed three appearances (the July 2026
fielded-stack audit, then ADS-B hardened, then MAVLink found carrying the same
defect) before a class-wide sweep ran, and the third appearance sat one
directory away from the second the whole time.

This is the sibling of the cross-repo claims rule in the Praesens playbook:
that rule says the number of places a moving fact is asserted is the future
defect count. This one says the number of sibling surfaces sharing a fixed
defect's shape is the future recurrence count. Both are countable on the day
of the fix, and neither count was being taken.

The first execution ran this cycle: a sweep of the twelve remaining adapter
surfaces (ingress, egress, command, and projector) against the C1-01
standard, one finder per surface, every finding then adversarially verified
through three independent lenses (format-datum fact, code-path reachability,
existing-guard coverage). The result was 21 findings, 20 confirmed by at
least two of three lenses, 1 refuted. The refutation is itself evidence the
class definition holds: the refuting lenses showed the claimed value is
schema-invalid before any datum gate is consulted, which removes it from a
class whose danger is precisely that its values pass schema validation. Of
the confirmed findings: the KLV ingress carried the full defect (MISB ST
0601's dominant altitude tags are MSL, and the generic decoded key reached
canonical `alt_m` unqualified); the JREAP ingress still performed the exact
legacy-key fallback the MAVLink fix names as the laundering class; the CoT
ingress promoted CoT's documented 9999999.0 unknown-altitude convention as a
real nine-million-metre HAE claim; the bladerf adapter mapped a
datum-unverified flight-telemetry altitude to canonical; the eo-cv fallback
laundered a documented flight-controller MSL position; moth and kraken
accepted caller altitudes with no datum obligation anywhere on their
surfaces; and the teaching surfaces (the example-vendor exemplar, the
authoring guide, the template README) taught the unqualified mapping to every
future author. All of it was fixed within the cycle to the C1-01 pattern,
with the boundary named in each adapter's documentation, pinned by
per-surface regression tests, and taught in AUTHORING.md's new
"datum-unlabeled plausible values" residue class.

One coupling the wave surfaced is logged here so it is a record rather than a
session memory: the A1-02 `VERTICAL_UNAVAILABLE` token is bound to
`payload.geo` by the adjudicated schema coherence rule, so the eo-cv
INFERENCE surface, whose geo is claim-scoped, carries its 2-D declaration in
`claim.geo.dimensionality` alone and asserts no `geo_status` token. Lawful,
and the schema said so before any code tried otherwise, but the token's scope
is narrower than the vocabulary's natural reading. Doctrine held; no mint.

The entry stays open because the sweep ran once and nothing makes it recur.
No rule yet requires the next within-class fix to trigger a class sweep, and
where that mechanism should live (an audit-playbook rule, a fix-wave
checklist item, a check with a defined retirement condition) is exactly the
shape of the pending apparatus review, which should adjudicate it deliberately
rather than this wave deciding it inside its own momentum.

## Cycle X2 — 2026-08-12 (second external contribution, PR #8 review)

Seeded by PR #8 (barrettdowns, Torch): four fixes against published
v1.1.22, submitted with field telemetry relayed by text. The telemetry was
the strongest field news the standard has had. The altitude-datum fix held
under a deliberate adversarial test on real ISR sensor logs across four
ingestion paths, the conformance gate drove three fixes inside the
contributor's own codebase, and encoding round-trips on real traffic were
lossless. The review verdicts and asks are on the PR itself (review
4920530322). The entries below record what verifying the PR exposed in
this repository's own records. The PR's governed commit, a metrics-only
code offered registry membership, is under maintainer adjudication and
logs here at disposition, with the merge wave.

| # | Tension | Gates in play | Status |
|---|---|---|---|
| X2-01 | A hash pin was accepted as proof of claim currency, and refuted a true finding | 3 | **CHANGED 2026-08-13** |
| X2-02 | The signing record cites a decision that was never made | 3, 5 | **CHANGED 2026-08-12** |
| X2-03 | The changelog guard skips on a convention an external contributor cannot know | 3 | **CHANGED 2026-08-13** |

### X2-01 — A hash pin was accepted as proof of claim currency · **CHANGED 2026-08-13**

Both example conformance claims carry `release_hashes` entries that
disagree with the release manifest beside them: `adapter_conformance_hash`
and `process_governance_hash` are stale in both files at the published
v1.1.22 tag. The drift entered at the first v1.1.22 cut commit
(`f0f5134`), which rebuilt the manifest without refreshing the claims, and
it shipped in every published v1.1.22 bundle. v1.1.21 has no divergence.
`docs/release_claims_errata.md` records the values and the reproduction.

Two prior verifications said this could not happen, and both passed for
reasons other than the ones claimed. The R1-11 audit refuted the finding
"conformance claims' `release_hashes` are never cross-checked against the
manifest" 3/3, partly on the ground that the claim files sit in the
manifest's hash-pinned claims group. The pin is real and certifies the
wrong property: it proves the stale bytes are intact, which is integrity,
while the finding was about currency. The refutation's other ground, that
the only documented command includes `--update-claims`, was falsified by
the v1.1.22 cut itself. This is the vacuous-verification class (P2-D1)
operating at the audit layer: the refutation was a check that could not
fail. A dated correction now sits on the refuted finding in
`docs/r1_11_full_stack_audit.md`.

No gate could catch the class when this entry was written, because nothing
in the repository read `release_hashes` back. Queued for the next fix wave:
a currency check that parses each example claim's `release_hashes` and
asserts equality with the manifest it sits beside. `RELEASE_CHECKLIST.md`
gained the `--update-claims` step this cycle as the interim human control.

Resolution 2026-08-13, hence the CHANGED status: the reader exists.
`gateway/tests/test_claims_release_hashes_currency.py` asserts every claim
hash against the manifest beside it, pins the deliberate
`release_manifest_hash` circularity omission, and demonstrates itself red
on the exact stale-hash state that shipped in v1.1.22. The checklist step
remains as the human control; the gate is the mechanical one.

### X2-02 — The signing record cites a decision that was never made · **CHANGED 2026-08-12**

Sixteen releases, v1.1.5 through v1.1.22, shipped checksums-only while
their records cited "the recorded signing decision". No such decision
exists. v1.1.2 through v1.1.4 shipped seven detached signatures each, made
with a release signing key created 2026-04-28 whose public half is tracked
in `release/` today. Signing stopped at v1.1.5, the first agent-executed
cut, and the maintainer reports having believed that releases were still
being signed.

The "recorded decision" resolves only to restatements of itself. Each
release's notes cited the convention, and the refinement handoff asserted
"no signing key has ever been configured (verified against git config, the
keyring, and every published release's asset list)". That sentence carried
its own verification credentials and was still wrong: the keyring checked
was the shell's, which is empty, while the keyring the signing tooling
resolves held the original key throughout, and the tracked public-key
files contradicted "never configured" from three directory entries away.

Two failure classes compounded. A negative existence claim was verified in
one environment and asserted for all environments, which is the
vacuous-verification class (P2-D1). And an inference was promoted to a
"recorded decision" with no decider and no date, which is the laundering
gate pointed at the project's own process records: an unlabeled inference
travelled as an adjudicated fact.

Resolution this cycle, hence the CHANGED status: `RELEASE_CHECKLIST.md`'s
signing items now require the decision to name the release authority and
the date, forbid carrying a prior release's answer forward, and require
key existence to be re-derived at each cut with the same gpg binary the
signing tooling resolves. The handoff's false passages carry dated
corrections. The key itself was verified end to end on 2026-08-12, so the
next release can ship signed. Queued for the fix wave: a completeness-gate
extension so a release that drops detached signatures relative to its
predecessor fails unless its notes carry the attributed decision.

Addendum 2026-08-13: the extension landed, with a different mechanism than
queued. `gateway/tests/test_release_artifact_completeness.py` requires the
tracked signature trio for the signed regimes (v1.1.2 through v1.1.4, and
v1.1.23 onward); a checksums-only release after the baseline is possible
only through an in-code exemption entry that must name the release
authority and the date, which a dedicated test enforces. The
predecessor-relative comparison was not built: an explicit regime is
simpler to reason about, and the exemption dict is the attributed decision
in artifact form rather than a prose sentence a test would have to parse.

### X2-03 — The changelog guard skips on a convention an external contributor cannot know · **CHANGED 2026-08-13**

PR #8's governed change arrived with no CHANGELOG entry, and
`test_changelog_keeps_up` skipped instead of failing. The guard keys on
the worklog's `- Last updated:` sentinel line; the contributor added a
dated 2026-08-11 entry above a sentinel still reading 2026-08-10, and a
stale sentinel is the guard's documented skip condition. No document
explains the sentinel convention, so an external contributor can satisfy
it only by accident. The apparatus audit already carries this guard's
failure-to-catch record as a maintainer-call item; this instance is the
first at the contributor boundary, where the convention is least knowable,
which raises its weight. Queued recommendation: derive the worked-on date
from the newest dated worklog entry instead of the sentinel, so the guard
keys on what contributors actually write.

A second instance followed on the maintainer side (recorded 2026-08-13):
the 2026-08-12 errata wave landed on develop with no changelog entry and no
sentinel bump, and the guard stayed silent for the same reason. The PR #8
second review's merge probe caught it: merging the contributor's honest
sentinel bump would have turned the guard green over a record missing two
days of maintainer work, so the guard's skip condition converts one side's
omission into a false currency assertion the moment the other side does the
right thing. The record was completed at the merge wave. Occurrence count: 2.

Resolution 2026-08-13, hence the CHANGED status: the queued recommendation
landed in `gateway/tests/test_changelog_keeps_up.py`. The worked-on date
now derives from the newest dated worklog entry heading, which is what
contributors actually write, and a top sentinel that disagrees with the
newest entry is a hard failure whose message teaches the convention at the
moment it matters, instead of a silent skip. The red demonstration is the
exact contributor-boundary state from this entry. The both-surfaces-lag
blind spot from instance two remains and is documented in the guard's
known-limits paragraph: a maintainer wave that writes neither an entry nor
a changelog line is still invisible to date comparison, and closing that
would take git-awareness the guard's own docstring rules out for CI
reasons.

### Disposition — the PR #8 governed commit · 2026-08-13

The contributor withdrew the registration after the review: the force-push
dropped the governed commit entirely, and the three accepted fixes merged
2026-08-13 (`36345fb`) with the withdrawal recorded in the branch's own
changelog and worklog entries. No governed change was minted; `warn` keeps
one meaning across the registry.

The need survives the withdrawal and is harvested per the intake doctrine:
nothing in the registry or its documentation tells a reader that
`EVENT_TS_IMPLAUSIBLE` exists or why it is deliberately absent, and the
origin of the false wiring analogy ("wired exactly like
`warn_datagram_bytes`") is this repository's own test docstring. Queued for
the fix wave, with credit to Barrett Downs: a non-governed documentation
surface for metrics-only diagnostics, and reconciliation of the
`test_ts_plausibility_window.py` docstring so the analogy cannot be read as
a wiring claim again.

---

The value of this log is the pattern over time. But a log that only ever grows
is a swamp: questions go in and never come out. So both the tensions here and
the rules in `docs/zmeta_audit_playbook.md` carry a defined end state, and reach
it on a trigger rather than by endless re-review.

### Tensions (the entries above)

Each entry carries an **occurrence count across cycles**. A tension may sit OPEN
while it is rare — one instance is noise. But recurrence forces a decision:

- **On the Nth recurrence [working value: N = 3], the entry MUST reach a
  terminal status** — it can no longer stay OPEN, and it is no longer re-reviewed
  from scratch each cycle. Terminal statuses: **CHANGED** (a guiding document was
  amended), **HELD-FIRM** (doctrine upheld as final — re-open only on genuinely
  new evidence, never on another instance of the same shape), **MINTED** (a
  governed change was made), **DROPPED** (recommendation withdrawn).
- **N = 3 is not arbitrary.** The fabricate-a-sentinel class already took
  pressure across three cycles (R1-10, then twice in R1-11) before anyone forced
  the question. Three recurrences is where "noise" has demonstrably become
  "signal." Tune it after observing a few, like the other thresholds.
- **A terminal entry is summarized to one line and moved to the Archive** below,
  out of the active list. The active list stays short by construction — that is
  the whole point.

### Rules (the playbook's disciplines and budgets)

A rule is not sacred because it is written down. Each is **scored, and the score
is reviewed on the cadence** — reconstructed from the record (git history, the
after-action log) at review time, *not* maintained as live per-event
bookkeeping, which would be its own bureaucracy:

| Dimension | Question |
|---|---|
| **Age** | How long has it been in force? |
| **Fired** | How many times has it actually caught something? |
| **Outcome** | When it fired, did it prevent harm — or misfire? |

- **Never fired** after several cycles → **retirement candidate.** It is
  documentation pretending to be a guardrail.
- **Fires but misfires** → **revision candidate.**
- **Fires and prevents harm** → **validated; leave it alone.**

Retiring a stale rule is "prefer a known-good over a tangled knot" applied to
governance: a rule that no longer earns its place is removed, not grandfathered.
The discipline to *add* a rule is matched by the discipline to *retire* one.

## Archive

Terminal tension entries and retired rules, one line each. Full bodies live in
git history; the one-liner plus its commit is what a later reader needs.

**Swept 2026-07-27** (the deferral above was anchored to the cut review; both
v1.1.17 and v1.1.18 have shipped, so it is spent). Eight terminal entries:

- **R1-11-02 — CHANGED** (`40be64a`): CBOR value-sharing tags 28/29 were
  undefined and the two reference backends disagreed about the same datagram;
  the fail-closed value-model clause refuses all tags by name, closing the
  cross-backend divergence and the receive-loop hang class with it.
- **R1-11-03 — CHANGED** (`40be64a`): the compact mapping declared no maximum
  nesting depth; it now declares 64, enforced identically on both backends
  (and, after the post-release hotfix `8175aa7`, before any backend encoder
  runs).
- **R1-11-05 — HELD-FIRM**: `TASK_ACK` has no `UNKNOWN` state, and does not
  need one — an ack whose verdict is unknown is an ack that has not happened.
  Upheld at first pass; nothing since has pressed it.
- **R1-11-09 — CHANGED** (adjudication 2026-07-27): a new `metrics_sink_gap`
  JSONL record type was parked on "is this governed vocabulary?"; the boundary
  decision (governed = the event model only) made it outer-ring, and it shipped
  with pin coverage.
- **R1-11-15 — MINTED** (`2a00ef2`): `TIME_STATUS.state` was the only
  SystemPayload branch without an enum — which is why B-04 was invisible. Class
  B enum added to v1.1.0 with fixtures; v1.0 untouched and pinned byte-identical.
- **R1-11-16 — CHANGED** (`dcabcc8`): adapter-declared vocabularies mirrored
  governed enums by hand with no lint; `tools/lint_adapter_vocabularies.py` now
  holds every registered mirror to its schema enum. It would have caught
  CR-05/06 mechanically.
- **R1-11-18 — CHANGED** (`40be64a`): the compact mapping declared no size or
  expansion bound; it now declares 2^20 expanded nodes, refused before the
  expansion is materialized.
- **H1-07 — CHANGED** (`b6af2ff`): the plain-`cbor` envelope still interpreted
  tags on cbor2-only installs, one envelope over from the clause that closed the
  compact path; both envelopes now refuse identically, with a probed pre-decode
  depth bound.

Retired rules: none yet. No playbook discipline has scored out (see the
playbook's Status scoring blocks).
