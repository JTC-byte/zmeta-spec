# ZMeta Doctrine Review Log

**Standing artifact. Accumulates across cycles. Advisory / non-normative.**

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
| R1-11-01 | No governed reason code for a non-finite value | 1 vs 3 | OPEN |
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

### R1-11-01 — No governed reason code for a non-finite value · OPEN

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
| H1-08 | Command-evidence refusals ride lineage codes; TASK_ACK cannot name them | 1, 3 | OPEN |

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

### H1-08 — Command-evidence refusals ride lineage codes · OPEN

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
| A1-01 | RF minimum features assume a calibrated receiver | 1, 3 | OPEN |
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

## Lifecycle — these logs terminate, they do not accumulate

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
