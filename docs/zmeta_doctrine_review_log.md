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

Statuses: **OPEN** (awaiting adjudication) · **HELD** (doctrine reviewed and
upheld) · **CHANGED** (a guiding document was amended) · **DROPPED**
(recommendation withdrawn).

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
| R1-11-02 | CBOR value-sharing tags 28/29 undefined; backends disagree | 4, 6 | OPEN |
| R1-11-03 | Compact mapping declares no maximum nesting depth | 4, 6 | OPEN |
| R1-11-04 | `timing_quality` cannot say "bound unresolved" | 2, 3 | OPEN |
| R1-11-05 | `TASK_ACK` has no `UNKNOWN` state | 1, 3 | **HELD** |
| R1-11-06 | Adapter refusals are invisible to the wire | 3, 6 | OPEN |
| R1-11-07 | `bandwidth_hz: 0.0` sentinel is a documented convention | 3 | OPEN |
| R1-11-08 | CoT `error_ellipse` zero defaults | 3, 4 | OPEN |
| R1-11-09 | New `metrics_sink_gap` JSONL record type | 1, 6 | OPEN |
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

### R1-11-02 — CBOR value-sharing tags 28/29 undefined · OPEN

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

### R1-11-03 — Compact mapping declares no maximum nesting depth · OPEN

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

### R1-11-07 — `bandwidth_hz: 0.0` sentinel convention · OPEN

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

### R1-11-08 — CoT `error_ellipse` zero defaults · OPEN

`zmeta_to_cot.py:235-237, 268-270` use `error_ellipse.get("semi_major", 0)`,
rendering `ellipse_major="0.0"` — a **sub-metre precision claim on an ATAK
screen** — for a partially populated ellipse. Same class as R1-11-07, on the
egress side, where gate 4 (egress is a lossy projection, never an upgrade in
apparent certainty) also applies.

### R1-11-09 — New `metrics_sink_gap` JSONL record type · OPEN

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

| # | Tension | Gates | Status |
|---|---|---|---|
| R1-11-14 | `TIME_STATUS.state` is not enum-constrained while its two siblings are | 1, 3 | OPEN |
| R1-11-15 | Adapter-declared vocabularies mirror governed enums by hand, unlinted | 1, 6 | OPEN |
| R1-11-16 | Formal release identity has no stated grammar | 5 | OPEN |
| R1-11-17 | Compact mapping declares no size or expansion bound | 4, 6 | OPEN |
| R1-11-18 | `--strict` makes a deliberately tolerated warn unrepresentable | 2, 3 | OPEN |
| R1-11-19 | Two conventions the new pins now enforce, chosen not discovered | 5, 7 | OPEN |
| R1-11-20 | Illustrative-example currency policy left inconsistent | 7 | OPEN |

### R1-11-14 — `TIME_STATUS.state` is unconstrained by the schema · OPEN

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

### R1-11-15 — Hand-mirrored vocabularies with no lint · OPEN

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

### R1-11-16 — Formal release identity has no stated grammar · OPEN

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

### R1-11-17 — No size or expansion bound in the compact mapping · OPEN

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

### R1-11-18 — `--strict` makes a tolerated warn unrepresentable · OPEN

The teaching corpus is validated with `--strict --require-all`, which means a
condition the standard deliberately **tolerates as a warning** cannot be shown
in an example. So the corpus can teach what is valid and what is refused, but
not what is *permitted-with-a-caveat* — which is precisely where an integrator
most needs an example.

**Recommendation:** decide whether the corpus should carry a warn-bearing
example under a relaxed flag, or whether teaching-by-example is deliberately
scoped to the pass/fail boundary. Gate 2 argues the former; gate 7 argues the
latter. No change made.

### R1-11-19 — Two conventions the new pins now enforce · OPEN

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

### R1-11-20 — Illustrative-example currency policy · OPEN

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

Terminal tension entries and retired rules, one line each. Empty for now — the
first entries reach the archive when a tension hits its third recurrence or a
rule is scored out.
