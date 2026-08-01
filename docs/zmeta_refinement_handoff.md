# ZMeta Refinement Handoff Notes

## NEXT SESSION: the v1.1.20 governed wave, then the remaining scoped waves

The live-readiness audit ran to completion on 2026-08-02: ten axes, every
verdict from executed paths, roughly 1.9 million subagent tokens. Verdicts:
encoding READY; normalize-rf, visualize, retask, lineage and zero-shot
READY_WITH_GAPS; normalize-tactical, containers, redact and operator-debug
GAPPED. The confirmed small fixes landed the same day as a four-fixer wave
(see the CHANGELOG's 2026-08-02 entries), and the maintainer adjudicated
four decisions, recorded on their doctrine entries: A1-02 (declared
dimensionality plus a geo_status token), MAVLink command translation
fail-closed with explicit override (shipped in the wave), the
state-projector-* wildcard removed (shipped, governed commit), and
error_ellipse_m promoted into v1.1.20 with the spelling reconciliation.

**The v1.1.20 governed wave, in one cut, all behaviour-changing items
together:**

1. A1-02: declared-dimensionality form on canonical geo plus the geo_status
   token, normative text drafted for maintainer review before anything
   lands. This unblocks maritime tracks reaching a COP at all.
2. error_ellipse_m promotion from the v1.1.0 branch into the formal schema,
   reconciling the semi_major_m adapter spelling in the same wave.
3. X1-01: constrain event.ts beyond the trailing Z.
4. Harness fixtures now that must-pass.jsonl moves anyway: AIS,
   signalhunter, and the track projector.
5. jreap-ingress and mavlink negative promotion pins in the bad-events
   corpus (the refusals work live; the corpus does not pin them).
6. Regenerate the stale Profile L size table in spec/compact-binary-mapping.md
   from tools/measure_packet_size.py output.

**Awaiting maintainer decisions, evidence assembled:** the contract 4.5.1
promoted-track lineage contradiction (external promotion with no ZMeta
parent versus lineage pointing at the ingest observation); the shipped
reference configs stripping payload.data_ref at every profile by default;
the X1-02 terminal call (N=6, terminal-call input on the entry); the
adapter zmeta_uuid import convention (three patterns now coexist: guarded
top-level, lazy, plain).

**Scoped waves queued, no decisions needed:** the CoT egress zero-default
ellipse fabrication fix (published code, still open, wants its own
red-first test); a track-projector stage in the reference deployment so the
documented containers can put a raw sensor feed on a map; TIME_STATUS
feeding the gateway's clock-health counters; value-scan forms of the AIS
no-classification pins.

**Parallel tracks:** the coalition egress example repository (adjudicated
direction: redaction is projection, canonical immutability untouched) with
its one spec-side residue, a declared-redaction extension registration; the
maintainer's Cesium experimentation COP; an awareness pass over
github.com/nkuntz1934/idahopulse.

## Superseded 2026-08-02 — the tier-2 list this replaced

The 2026-07-31 sequencing ran to completion the same day, in the order given:
the cold re-read first, the fixes it forced, then the push. Eight independent
lenses read the four commits with the producing context gone, and every
finding was adversarially verified. **The read did not come back green: 31
findings, 16 verified with none refuted, three MAJOR, all three in the AIS
adapter.** The must-fix set was fixed red-first in the same session, a cold
attack pass on the fixes reopened nothing and found no vacuous pins, and the
push follows the attack pass's own residue commit. Details are in the
worklog's newest 2026-07-31 entry and the CHANGELOG; the X1-02 terminal-call
input from the read is on the doctrine entry.

The two named targets both earned their naming. The changelog-check
strengthening was confirmed to be another cheaper sibling of its intent; its
residue is now documented in the check's own docstring as known limits, and
its red proof moved from a commit-message attestation into an in-tree
mutation canary. The SIM1 rename audit came back exact: 33 references
independently re-derived, the historical series untouched.

Discipline 6 is answered for this range: the cold panel found three MAJOR
defects the author's own reading had not.

**Queued from the 2026-07-31 pre-push review**, each outside the reviewed
range or below the fix bar, none blocking:

- `adapters/egress/cot/zmeta_to_cot.py` renders `<remarks>` and
  `<precisionlocation>` ellipse members with `.get(key, 0)` defaults, so an
  ellipse dict carrying wrong member spellings becomes a fabricated zero-size
  ellipse claim. Published code. A small fix that wants its own red-first
  test.
- Sibling-parity pass on `adapters/ingress/adsb/`: it demotes out-of-range
  coordinates with no bounds check where AIS refuses them, it lacks the epoch
  plausibility floor AIS now has, and the two differ on the guarded
  `zmeta_uuid` import. One scoped wave, both READMEs in the diff.
- The AIS no-classification pins enumerate key names, so a classification
  laundered under an unlisted key would pass the suite; a value-scan form is
  stronger.

## Tier 2 — resolved 2026-08-02 except item 1; kept as the decision record

Adjudications: item 2 (A1-02) DECIDED, declared dimensionality plus token,
v1.1.20; item 3 (experimental split) DECIDED by promoting error_ellipse_m
into v1.1.20; item 4 (state-projector-*) DECIDED and SHIPPED, the wildcard
is removed; item 5 (X1-01) rides the v1.1.20 cut as planned. Item 1, the
X1-02 terminal call, remains the maintainer's. Original list as written:

The maintainer's direction at the 2026-07-31 closeout. Tier 1 is complete and
committed. Everything below needs a call, not an implementation, and each has
its evidence already assembled.

1. **X1-02 terminal call.** Past the N=3 lifecycle threshold at five instances
   across two repositories, held open by a detection question its own text calls
   answerable in an afternoon. **A sixth instance landed on 2026-07-31 and it is
   the sharpest yet:** the check written at the previous closeout to catch
   records-lag passed while the records were stale, because it tested for an
   empty section rather than a current one. Written by the author of the X1-02
   note, one day after writing it. Either the detection question gets answered
   or the entry goes terminal as HELD-FIRM with the question recorded as
   declined.
2. **A1-02 disposition.** The promotion bar is met: two independent
   implementations, ADS-B and AIS, different sensor classes, same wall. The
   recommendation on record is a declaration of dimensionality rather than a
   subtype. Three facets now, and the third is much the cheapest: the
   `geo_status` vocabulary has no token for "horizontally known, vertically
   absent", so both adapters say `UNAVAILABLE` for a position that is known and
   present in the native features. That one is a vocabulary token or a normative
   sentence, independent of the dimensionality question.
3. **The experimental-split experiment.** Carries more weight since SIM1-05 was
   corrected: uncertainty already lives on the v1.1.0 branch as a registered,
   approved, schema-implemented extension, so this is the concrete thing v1.1.0
   buys rather than a hypothetical.
4. **`state-projector-*` promotion evidence.** The wildcard can assert an
   authoritative track with no promotion evidence at all; demonstrated by
   stripping the whole block and getting an identical result. Policy change,
   therefore yours.
5. **X1-01 disposition**, already queued for v1.1.20 and unchanged.

**Queued for the v1.1.20 cut** and cheap only there, because
`conformance/adapter-harness/must-pass.jsonl` is manifest-hashed: harness
fixtures for both `adapters/projector/track/` and `adapters/ingress/ais/`, plus
the three items grouped at the previous cut.

**Three commits are local and unpushed** as of this closeout: `4e37e54`,
`12df155`, `d81ada3`. *[Corrected 2026-07-31: false the moment it was
committed, because the commit carrying this sentence was the fourth. A count
of unpushed commits written inside an unpushed commit undercounts itself;
generate such counts, or date them to a named tree.]*

## CLOSEOUT — 2026-07-31

Two commits since the last closeout, reviewed against the intent that drove
them, battery verified by hand, records reconciled.

**The finding is that the previous closeout's own fix did not hold.**
`test_changelog_keeps_up.py`, written on 2026-07-30 to close the records-lag
watch-item, passed this session while the CHANGELOG described none of the work.
It asserted `[Unreleased]` was non-empty, and yesterday's entries were still
there. That is X1-02 in its purest available form, committed by the author of
the X1-02 note one day later. Strengthened red-first: the newest dated entry
must now be at least as recent as the worklog's last-updated date, demonstrated
failing on the real stale state before the fix.

**The other three checks were clean.** No governed artifact moved, no
manifest-hashed file was touched, the SIM1 rename left every historical
reference intact, and the AIS adapter's claims are pinned in colocated tests
rather than asserted in prose.

## Previous closeout — 2026-07-30

Three commits, 19 files, `main` pushed and CI green at `9fca0e1`, tree clean.
Battery verified by hand rather than accepted: kernel gate all flags exit 0,
strict examples 51/51, pytest 1518 passed plus 1074 subtests, both lints clean,
roadmap validator and policy JSON export clean.

**Four things the closeout found.**

1. **The CHANGELOG's `[Unreleased]` was empty** after three commits of
   user-facing work. This is the fourth instance across three cycles of records
   reconciling at points while commits land continuously, and the v1.1.19 rule
   scoring had already carried it with a pre-committed disposition: if it
   recurs, build something. It recurred, so
   `gateway/tests/test_changelog_keeps_up.py` now asserts that work recorded
   after the newest released version is described somewhere. It deliberately
   does not judge *what* the description says, because the rule that tried to
   judge whether prose meant the right thing failed twice on the release-focus
   bullet.
2. **X1-02 is past the lifecycle threshold and still OPEN.** The rule says a
   tension reaches a terminal status on its third recurrence; this one is at
   five across two repositories, held open by a detection question its own text
   calls answerable in an afternoon and which is now two days unstarted. Either
   the question gets answered or the entry goes terminal without it. Recorded on
   the entry, and it is the maintainer's call.
3. **Discipline 6 went unmet.** No independent panel read any of this cycle,
   including two deployment fixes and a new adapter category. The v1.1.19 cycle
   is the evidence for why that matters: an author-run pre-cut review produced a
   cut that looked ready, and independent panels then found the headline guard
   did not work. One cycle is not a pattern; two would be, and the work now
   sitting in front of a live event is the work most wanting a cold read.
4. **Considered and cleared:** the `recv=722 fwd=722` measurement is asserted in
   six places. The moving-fact rule counts that as a future defect count, but
   the fact is frozen and every instance is framed in the past tense as a
   defect that was corrected, so all six stay true. No action. *[Corrected
   2026-07-31: the clearance holds, the count did not. A generated recount
   (`grep -rn "recv=722"` over the canonical tree) finds nine places asserting
   the measurement and two more asserting this count of places. Six was a hand
   count inside a paragraph applying the counting rule.]*

**Nothing is half-done.** Every deferral is explicit and named: harness fixtures
for the projector wait for the v1.1.20 cut because `must-pass.jsonl` is
manifest-hashed, and the open doctrine entries are decisions rather than work.

## CURRENT STATE (track projector 2026-07-30)

**`adapters/projector/track/` closes the observation-to-track gap for sources
whose subjects broadcast an identity.** The same synthetic ADS-B snapshot that
produced zero CoT earlier the same day now produces two tracks on the CoT wire,
verified through two live gateway nodes. Nothing governed moved and no
manifest-hashed file was touched.

**A third adapter category, and the reason it is not ingress or egress.** A
projector takes ZMeta in and emits ZMeta out. It changes what an event *is*
rather than what format it is in. Ingress translates a foreign format inward,
egress projects outward, and neither describes promoting observations into a
track.

**Why fusion and not external promotion, since both reach a `STATE_EVENT`.**
Promotion is for importing a track another system already computed, which is
what the CoT and JREAP ingress adapters do. Fusion is for a track you associated
yourself. An aircraft broadcasts instantaneous position and identity; it does not
decide that successive broadcasts are one object or when that object is stale.
The lineage rules agree: `policy/lineage.yaml` allows a `STATE_EVENT` to cite
only `FUSION_EVENT` or `STATE_EVENT` parents, so a state citing an observation is
refused with `LINEAGE_PARENT_TYPE_INVALID`, and going straight from observation
to state would require citing a parent that does not exist.
`FusionPayload.members` is `minItems: 1`, so a single-member association is
schema-legal and no invention is needed. All three refusal paths were confirmed
by running them.

**`confidence` is a required constructor argument with no default, and that is
the finding underneath the component.** The kernel requires `confidence` on both
emitted event types. A cooperative broadcast supplies none: `nac_p` and `sil` are
accuracy and integrity, already projected into an error ellipse, and neither is a
probability that the claim is true. The only honest source is the operator, so
the projector refuses to construct without one. Deriving it from `sil` was
considered and rejected as an unadjudicated modelling decision.

**Doctrine log SIM1-05, CORRECTED 2026-07-31.** As first written this said a
v1.0 `STATE_EVENT` has nowhere to carry positional uncertainty and framed it as
a kernel gap. That overstates. `ERROR_ELLIPSE_M` is a registered, approved,
schema-implemented and conformance-implemented extension allowed on
`STATE_EVENT`, on the v1.1.0 branch, carrying semi-major, semi-minor,
orientation and an optional probability level. What is true is narrower: a
deployment on the locked v1.0 kernel, which is every shipped artifact and the
gateway default, carries none, so the 30 m ellipse ADS-B derives from
`nac_p: 9` reaches TAK as `ce="9999999.0"`. That makes it an adoption-path
question belonging with the experimental-split experiment, not a new gap.

One real defect survived the correction: the v1.0 generic quality object spells
the members `semi_major_m` / `semi_minor_m` and the v1.1.0 formal contract
spells them `semi_major` / `semi_minor`, which is what the CoT reader looks for.
A deployment moving between them gets silence rather than an error. Small, cheap
and independent of the adoption question.

**The correction is the lesson.** An external comparative survey reached the
same conclusion from a literature angle on the same day, and the agreement made
it feel settled. Two sources reaching the same wrong answer is not
corroboration when neither checked the extension registry. When an outside
claim matches your own, that is the moment to verify it, not to stop.

**Deferred to the v1.1.20 cut on purpose:** registering the projector in
`conformance/adapter-harness/must-pass.jsonl`. That file is manifest-hashed, so
adding fixtures now would regenerate the manifest under the published `v1.1.19`
identity and diverge `main` from its published checksums. It joins the three
items already grouped for that cut.

## Previous state (simulation reps 2026-07-30)

**`v1.1.19` remains the published release and nothing governed moved.** The work
on 2026-07-30 was a set of internal simulation reps run while field feedback is
pending, plus the fixes they justified. No schema, policy, semantics or
event-vocabulary change; no manifest-hashed file touched, so the published
`v1.1.19` manifest and checksums stay valid.

**Two real breaks in the deployment path, found by running the shipped
containers and fixed the same session.**

- **A containerized node could not deliver anything it produced.**
  `forward.host` and `cot.host` are `127.0.0.1`, correct on a host and wrong in
  a container, where it is the container's own loopback. The send succeeds and
  the datagram is unreadable, so nothing errors. Measured: the container
  reported `recv=722 fwd=722` while a receiver on the host's `127.0.0.1:5556`
  saw zero. `deploy/*/docker-compose.yml` now pass `--forward-host`,
  `--cot-host` and `--forward-port` on the command line, where they win over the
  config, defaulting to `host.docker.internal`. Re-run after the fix: ZMeta JSON
  on the host's 5556 and CoT on 6969, where both had measured zero.
- **The two Compose files both published `5555:5555/udp`**, so the pair failed
  to co-host with `Bind for 0.0.0.0:5555 failed: port is already allocated`.
  Host ports are now overridable and the corrected pair was run end to end on
  one machine.

`gateway/tests/test_container_egress_overrides.py` pins the invariant the fix
rests on, which is that CLI values are applied after the config and beat it. It
carries a control asserting the config's own values survive when no override is
given, and its docstring states plainly that the Compose text assertions guard
against silent removal and are not evidence of delivery.

**The finding that matters most before a live event, and it is not a code
defect.** CoT projects `STATE_EVENT` only. Five clean ADS-B observations
traversed both nodes and produced zero CoT, while the example corpus produces
one because it happens to contain a `STATE_EVENT`. The documented pre-event
rehearsal therefore passes and the real sensor then shows nothing on the COP.
The quickstart now says so at the top. Logged as **SIM1-03**: a fixture chosen to
demonstrate every event type is not a fixture representative of the input.

**Doctrine log cycle SIM1, three entries, all OPEN, nothing minted.** SIM1-01
`confidence` reaches CoT only as free text with no structured element, which is
gate 5 against gate 4 and the second instance across two stacks. SIM1-02 `drops=0`
is read as a loss counter though it can only see what arrived. SIM1-03 above. Each
carries the live question that would settle it, because none of the three is a
defect with a known fix.

**Verified working, by running rather than by reading:** the command-evidence
gate refuses a prohibited-parent citation with `LINEAGE_MISMATCH` while an
identical command citing a clean parent forwards; Profile L compact maxes at 150
bytes against the 240-byte budget; contract hashes are byte-identical across a
Windows host and a Linux container; the ADS-B adapter's refusals and demotions
behave exactly as its README claims on realistic input.

**Measured for the first time, so the Raspberry Pi visit is now a comparison
rather than a design exercise:** one gateway sustains 100% delivery at 400
events/s on an x86 host, saturates near 422/s, and at 1000/s offered delivers
44% while reporting `drops=0`, because loss above capacity happens in the kernel
upstream of the process.

**X1-01 confirmed live and deliberately untouched.** Six of six nonsense
timestamps pass the governed schema, including `banana-Z` and bare `Z`, with
both controls behaving; `rfc3339-validator` is absent and `date-time` is
unregistered, so the mitigation the adapter READMEs name is confirmed vacuous.
Run through the gateway, those events reach a downstream ZMeta consumer with no
violation or warning, while CoT egress refuses them. The protection is real for
TAK and absent for every ZMeta consumer. It stays sequenced for v1.1.20 as
already adjudicated, since minting a governed change inside a fix wave is
exactly what the playbook forbids.

**The rep harnesses are now committed, under a boundary that keeps them
extractable.** `tools/sim/two_node.py` and `tools/sim/throughput.py`, with the
control mode and the fresh-`event_id` generator that the session proved were
load-bearing. The maintainer flagged the real risk in committing them: a data
standard whose repository fills with operational tooling stops being a thing you
can read and adopt. That is recorded as doctrine **SIM1-04** with an extraction
criterion and a trigger, and it is enforced rather than promised by
`gateway/tests/test_sim_boundary.py`, which asserts nothing governed imports or
invokes anything under `tools/sim`. While that holds, extraction is a directory
move and a pointer. The trigger to stop deferring the question is a third
harness, a dependency outside the standard library, or a request to run these in
CI.

**The method note worth reusing.** Every rep had its pass and no-op criteria
written before the run. That caught three bad measurements of mine before they
became findings: a false "node did not come up" from a block-buffered pipe, a
throughput number that was measuring duplicate suppression because the generator
cycled `event_id`s, and a four-case command corpus in which every case failed
for an unrelated reason. Each would have been reported as a result.

## Previous state (closeout 2026-07-28)

**`v1.1.19` is PUBLISHED.** Annotated tag on `0eebb43`, eight assets, CI green
on the release commit. The published assets were downloaded back from GitHub and
verified against the published `SHA256SUMS_v1.1.19.txt`; all seven checksummed
artifacts matched. Checksums-only, consistent with v1.1.5 onward — no detached
signatures. The maintainer delegated tag and upload explicitly, which is the
condition AGENTS.md Release Limits require.

**Battery at closeout:** kernel gate all flags exit 0, strict examples 51/51,
adapter conformance 51/51, pytest **1477 + 1070 subtests**, both lints clean,
roadmap validator clean, `export_policy_json --check` clean, release manifest ok,
release package ok **in package mode**. `main` is pushed, CI green, tree clean.

**The cut was made twice, and the record says so.** The first tag was created
before the publish-path validations had been run, and
`validate_release_package.py --package-dir` — the command this release's own
body publishes — then failed on a package built at the prepare commit against a
manifest that had moved four hours later. Tagging is what makes checksums
immutable here, so the fix was correctly refused in place and the tag was
deleted before anything was published. **The durable rule: run every
publish-path validation BEFORE the tag exists**, specifically `--package-dir`
and `sha256sum -c`, not just the battery. Both gaps are now closed by checks
rather than by checklist items; see "Verification integrity" below.

### What v1.1.19 contains

- **`export/policy/*.json`** — the governed policy as a verbatim JSON
  projection, so a consumer outside the Python stack need not vendor a YAML
  parser or hand-copy governed data. Built because a fielded deployment was
  doing the latter.
- **The ADS-B ingress adapter** (`adapters/ingress/adsb/`) — first
  cooperative-broadcast adapter, and the release's most useful failure report.
- **Field-readiness fixes** that a first-run review found: the stock two-node
  path delivered zero events; the adapter-in-an-hour claim hid a 30–90 minute
  producer-authority wall; contract hashes differed across platforms two
  independent ways; the documented dev install was broken.
- **Packaging** — every hashed artifact now ships in every bundle, asserted
  against BUILT bundles rather than builder source.
- **Content currency** — the release-focus governance sentence is computed and
  required verbatim. The rule that tried to judge whether prose described the
  right release was removed after failing twice; see below.

### Verification integrity: two gaps closed during the cut itself

Both were the same shape — a weaker check standing in for a stronger one — and
both were invisible to every automated gate.

- **A release is now machine-checked to ship its full tracked artifact set.**
  This cut was found carrying only `RELEASE_NOTES_v1.1.19.md`, with no validation
  report and no checksums, through a validating manifest, a validating package, a
  green battery and green CI. The completeness rule had lived only as manual
  checkboxes in `RELEASE_CHECKLIST.md`.
  `gateway/tests/test_release_artifact_completeness.py` generates the required
  set and asserts it for the current release and every release since the
  convention began at v1.1.0.
- **A release package that fails package-mode validation can no longer acquire a
  pinned checksum.** `sign_release_artifacts.write_checksums` now invokes the
  governed validator before writing, so a stale package cannot become a published
  claim. Three paired tests, including one asserting the refusal comes from the
  validator rather than from the package directory merely existing.

Counting X1-01, that is **three instances in one day of a stronger check
existing while something cheaper ran in its place**: `--templates-only` for
`--package-dir`, a manual checklist for artifact completeness, and
`pattern: "Z$"` for `format: date-time`. Logged as an observation, not minted
as doctrine — see the doctrine log's lifecycle rules on earning promotion by
recurrence.

### The documentation voice pass

An outside reader found the README reads as machine-written; the identified
tells are heavy em-dash use and a rhetorical, catch-phrase tone. The target is
flat declarative technical prose. This is a voice pass only. The README's
structure and content were reworked deliberately last cycle and both are sound.

**COMPLETE for its scope, 2026-07-28, in three commits: `595e386` (README),
`287209d` (docs index, authoring guide, three densest adapter READMEs),
`a6a4383` (every remaining current-facing document).** 40 files, 300 em dashes
down to 1, plus the rhetorical constructions: inversion for emphasis, bold carrying
sentence rhythm rather than marking a scanning point, punchy fragments, and
metaphors standing in for statements. No structure, ordering, facts, claims or
code changed anywhere in the pass. The README is 24 words longer, so this was
not compression wearing a voice-pass label.

**Scope was set by measurement, and the exclusions are by category rather than
by omission.** Counting em-dash density across every markdown file put
`docs/README.md` worst in the repository at 52 per thousand words and showed
`docs/zmeta_professional_overview.md` already effectively clean at 0.5, the
opposite of what this handoff predicted. Deliberately untouched, holding about
1900 dashes between them:

- the three governed markdown files, since a prose edit to a governed artifact
  is a governed change;
- the twelve manifest-hashed files, where a comma would force a manifest
  regeneration for no reader benefit;
- process records, since rewriting them falsifies what was true when they were
  written (the exclusion `test_release_currency.py` already documents);
- `CLAUDE.md`, which is agent guidance written in a directive voice on purpose.

One in-scope dash survives, inside the maintainer's quoted rule in
`docs/zmeta_live_test_checklist.md`. Rewriting a quotation would misreport what
was said.

**Method note worth reusing.** Every substitution ran through a script
asserting each pattern matched exactly once, so a pattern that stopped matching
halted the run instead of reporting success over an unedited file. That check
caught nothing this time, which is the outcome it is supposed to have.

**ADOPTED AS THE REPO STANDARD, 2026-07-28.** The maintainer approved the
result and asked that this become the house voice: simple, clean, upfront and
detailed, professional without sounding like a sales pitch. It is written into
`CLAUDE.md` under "How we work here", with the specific tics to avoid, the
warning against over-correcting into hedging or padding, and the two exceptions
(quotations are copied exactly, process records are never restyled). `CLAUDE.md`
was itself brought to the standard in the same commit, because a style rule
stated in the one file that breaks it is the exemplar-violates-its-own-rule
defect `adapters/AUTHORING.md` section 9 already names.

**The one deferred piece, and one that is not deferred at all.** These are
different cases and were briefly written up as one:

- **Manifest-hashed but ungoverned: 5 dashes across 4 files** (`AGENTS.md` 1,
  `docs/zmeta_change_governance.md` 2, `spec/release-hash-policy.md` 1,
  `spec/future-branch-roadmap.md` 1). Skipped only because a comma is not worth
  a manifest regeneration on its own. That cost goes to zero at the next cut,
  when the manifest is rebuilt anyway, so folding them into the version bump is
  the cheap moment. The other eight hashed files already carry none.
- **Governed: 12 dashes, and they stay.** `spec/compact-binary-mapping.md` has
  11 and `spec/semantics-contract.md` has 1. A prose edit to a governed artifact
  is a governed change at any time, so the next cut does not make these cheaper.
  They move only through the normal escalation, if ever. The house voice does not
  override the change process.

**The honest limit.** The countable tells were counted and are at zero. Whether
the prose now reads as a person wrote it cannot be judged by its author, and an
outside reader is what that claim needs. If the calibration is wrong in either
direction, over-corrected into flatness or still too rhetorical, the fix is
cheap and uniform across all 40 files.

### NEW FINDING 2026-07-28: the kernel does not constrain `event.ts`

**Full record: `docs/zmeta_doctrine_review_log.md`, cycle X1, entry X1-01.**
Reproduction, the vacuous-mitigation half, the four options and the sequencing
live there and are not restated here on purpose — this finding is one fact and
gets one home. (The consumer's own §9 lesson, adopted the hour it arrived:
count where a moving fact is independently asserted; more than one is your
future defect count.)

One-line status: the governed schema accepts any `event.ts` ending in `Z`,
including `Z` itself; egress adapters refuse, consumers reading `ts` are
unprotected; **escalated, not fixed**, because there is no observed failure
(discipline 10). Sequencing: **tag v1.1.19 as-is — it stays a clean additive
cut — and handle this in v1.1.20, which is then behaviour-changing rather than
additive.** That distinction is what the fielded consumer's pin-advance review
keys on, so it is worth more to them stated in advance than discovered in a diff.

### Queued for the v1.1.20 cut — three things that are cheap only then

All three touch manifest-hashed files. Doing any of them now regenerates the
manifest under the published `v1.1.19` identity and diverges current `main` from
the published `SHA256SUMS_v1.1.19.txt` — the documented A-12 pattern. At the next
cut the manifest is rebuilt anyway, so the marginal cost of all three is zero.
Grouped here so they are found together rather than rediscovered separately.

1. **X1-01 enforcement**, if the maintainer chooses a closing option. This is
   what makes v1.1.20 behaviour-changing rather than additive, and the fielded
   consumer has already recorded that classification in advance.
2. **The conformance summary line.** `tools/validate_conformance.py:331` prints
   `conformance ok pass=20 fail=27`, which is accurate and reads alarming. A
   downstream reviewer had to run the identical command at `v1.1.18` as a control
   to establish that the 27 are the negative corpus refusing correctly. **The
   need is theirs; the constraint and the wording below are ours** — an earlier
   version of this entry credited them with finding the constraint, which they
   corrected. See the note under it.

   `gateway/tests/test_tool_input_floors.py:83-89` asserts **two** things about
   this line: `summary.startswith("conformance ok pass=")` and `" fail=" in
   summary`. Any replacement must satisfy both. Verified candidate:

   ```
   conformance ok pass=20 fail=27 (20 must-pass OK, 27 must-fail correctly refused)
   ```

   Keeps the machine-readable head intact and states the expectation a reader
   needs. **Do not use the bare form `20 must-pass OK, 27 must-fail correctly
   refused`** — it satisfies neither assertion and turns that test red.
3. **The hashed-file voice sweep**, 5 em dashes across 4 files (`AGENTS.md`,
   `docs/zmeta_change_governance.md`, `spec/release-hash-policy.md`,
   `spec/future-branch-roadmap.md`). The governed three stay out permanently;
   a prose edit there is a governed change at any time.

**Provenance note on item 2, kept rather than tidied away.** The first version
of this entry credited the fielded consumer with finding the
`conformance ok pass=` constraint. They did not; it was found here by grepping
for assertions on that output, and they corrected the attribution against their
own interest. They also pointed out that the wording they *had* proposed breaks
both assertions, so the entry as first written carried a fix that would turn a
test red, under a credit belonging to the party who did not write the
constraint. Both are corrected above.

The rule this produced, theirs: **credit is a claim too.** Verify attributions
in your favour at least as carefully as ones against you, because nobody else is
incentivised to. It is §9.15 pointed at praise instead of criticism, and it cost
one command to check.

### The decisions waiting on the maintainer

**Decision 1 of the original four is CLOSED: v1.1.19 is tagged and published.**
The rest stand, and none blocks running the standard live.

1. **X1-01, the `event.ts` disposition** (new this session). Four options are
   recorded in the doctrine log, outer rings first. Sequencing already decided:
   this lands in **v1.1.20**, which is therefore behaviour-changing rather than
   additive — the axis the fielded consumer's pin-advance review keys on. Not
   urgent: no observed failure, zero external producers anywhere.
2. **Doctrine log cycle A1** — three alphabet gaps from the ADS-B adapter, each
   with a second instance. The recommendation for all three is a *declaration,
   not a subtype*. **A1-01 already clears the 2+ independent implementation
   promotion bar** (kraken and ADS-B, both in-repo); A1-02 has one, and AIS on
   the same RTL-SDR dongle is the natural second.
3. **The experimental-split experiment** (maintainer's proposal, recorded in
   the doctrine log): put the candidate discriminators in the v1.1.0
   experimental branch, have the adapter emit either by flag, and let consumers
   decide. Not started — v1.0 stays locked and nothing has been minted.
4. **The `kraken` laundering** (`kraken_to_zmeta.py:160`). It works in the
   field today and the spec leaves no honest alternative, so it is recorded
   rather than patched. It resolves for free if A1-01 does.

### What was deliberately NOT done, and why

Per **playbook discipline 10**, adopted this cycle: hardening that cannot be
live-validated is written down rather than built.
`docs/zmeta_live_test_checklist.md` carries those questions in yes/no form —
including whether anyone actually needs calibrated power, whether anyone misses
the dropped 2-D positions, and whether anyone uses the dist bundle at all.
**"Nobody cared" is a complete answer** and closes the item.

### The lesson this cycle actually produced

Four independent panels ran. The code converged — no test, fixture or
conformance expectation regressed across the whole cycle. The **claims about
the code** did not: every late defect was an enumeration or measurement written
into prose without being run, and at one point three places carried three
different counts of the same thing.

**When a claim enumerates, generate it.** Applied in **two** places so far —
the governance sentence and the dist bundle's tool list. The conformance flag
list is still hand-typed prose that no generator writes and no test reads, and
it already carries an enumeration error of its own; it is the obvious third
candidate. (Superseded text follows.) The
governance sentence, the conformance flag list, and the dist bundle's tool
list. It is the one rule from this cycle that removes work rather than adding
it.

The corollary, from the guard that failed twice: a rule that must judge whether
prose *means* the right thing is not machine-checkable, and three rounds of
evidence say attempts to make it so keep producing new holes. Compute the fact
and require the generated text; do not parse the author.

---

---

## Previous state (closeout 2026-07-27)

**The R1-11 cycle is CLOSED and published. Two releases shipped 2026-07-27:
`v1.1.17` (the R1-11 audit/hardening cut, tag on `7302073`) and `v1.1.18`
(the event-readiness cut, tag on `157d41f`). Both checksums-only, both CI
green, `main` pushed and in sync with `origin`.** Nothing is held; there is
no frozen range.

**Current release: `v1.1.18`.** Clone the **tag** for deployment — the
published `SHA256SUMS_v1.1.18.txt` matches the tagged tree. `main` carries
post-tag commits (`dd5def7` cosmetic sweep, plus this closeout), so it
diverges from the published assets by design; published checksums are
immutable and the next cut re-baselines the manifest (the documented A-12
roll-forward pattern).

**Battery at closeout:** kernel gate all flags exit 0, strict examples 51/51,
pytest 1420 + 1070 subtests, adapter harness 48/48, policy risk-mode and
adapter-vocabulary lints and the roadmap validator clean, Profile L packet
max 150/240.

### What this cycle delivered

- **v1.1.17** — the R1-11 audit's full closure: the health fix wave (three
  MAJORs including two live in published v1.1.16 — a SAPIENT latency
  declaration that could *narrow* an uncertainty bound, and a CoT projection
  putting horizontal error into a vertical-error field), the records wave,
  and two maintainer-adjudicated governed waves (the compact fail-closed
  value-model clause; the `TIME_STATUS.state` Class B enum).
- **v1.1.18** — event readiness: the bladeRF reference ingress adapter,
  container verification on x86-64 and ARM64 (contract hashes byte-identical
  across architectures), the two-node quickstart, the `cot.config` pedigree
  knob, the command-evidence gate, and the track-lifecycle pattern expressed
  in current vocabulary with no vocabulary minted.

### Live queue — everything agent-executable is done

**Gated on hardware or access (not on work):**

1. **Real-Pi throughput** — a five-minute replay smoke when hardware arrives.
   Build, dependency resolution, startup, and semantics are already verified
   under ARM64 emulation; only throughput is unmeasured.
2. **TAK/COP display validation** with live tooling. The `cot.config`
   pedigree knob that enables `<precisionlocation>` detail is shipped and
   pinned but has never rendered on a real COP.
3. **SAPIENT live-enclave** validation against the official BSI Flex 335
   harness and multi-node routing (recorded not-exercised since v1.1.15).
4. **The SITL end-to-end gate** — the maintainer's own stated precondition
   for live GCS-originated tasking. The command-evidence check is its
   repo-side prerequisite, not a substitute.

**Maintainer decisions, none blocking:**

5. **The v1.1.0 adoption decision** (fourteen experimental concepts) — see the
   Next Work Queue below. The multi-UxS event is the second evidence leg the
   promotion bar wants.
6. **Three doctrine tensions at the recurrence threshold**, put to the
   maintainer at this closeout rather than left to drift: the reuse-vs-mint
   class (R1-11-01 with H1-08), the tolerated-warn corpus question
   (R1-11-14, with R1-11-19 merged into it), and — already decided —
   R1-11-07 HELD-FIRM. Nineteen further tensions remain OPEN by design.
7. **The SAPIENT follow-ups** (Task ingress needs command-safety escalation;
   the harness registration entry point).
8. **Extend the currency guard from version literals to content — DONE
   2026-07-27, and it stopped being a records-hygiene item before it was
   built.** The queued rationale was that the guard pins version *literals*,
   so the README's release-focus prose carried v1.1.16 content through two
   cuts with every pin green and only a human reading caught it. What
   arrived next was the consequence: **P2-01**, reported by a downstream
   consumer advancing its ZMeta pin, who found that the carried-forward
   bullet asserts *"No schema, policy, or event-vocabulary changes"* — true
   of v1.1.16, **false of both v1.1.17 and v1.1.18**, which between them
   added three `reason_code` values to the locked v1.0 schema, the
   `TIME_STATUS.state` enum, amendments to two pre-existing policy files
   (neither added), 148 normative lines to the
   compact mapping, and `policy/command-evidence.yaml`. A stale paragraph
   became a false governance claim in two published tags, aimed at exactly
   the reader who most needs it to be true: one deciding whether a pin
   advance requires re-deriving a hand-maintained vocabulary copy.
   **It was a near miss, not an incident, and the record says so.** That
   consumer worked from the release notes and diffed its consumed surfaces
   directly; the README is what disagreed with its evidence, which is how it
   was caught. A disciplined process stepped around a live trap. The guard
   still earns its place — the next reader may take the bullet instead of
   the diff — but nothing here was actually mis-advised, and our own
   honesty rule applies to our incident records too.
   **Two corrections to the first write-up of this finding, both from that
   consumer and both verified against our tags:** its pin was at v1.1.16,
   not the v1.1.9 line (five reviewed advances had happened since a stale
   private note), so the consumed gap is v1.1.16→v1.1.18 and the locked v1.0
   schema gained exactly **three** `reason_code` tokens over it —
   `ENCODING_UNSUPPORTED`, `BEARING_FRAME_UNLABELED`, `NON_FINITE_CONFIDENCE`.
   The other four arrived at v1.1.16 and were adjudicated at that advance.
   Lesson for this repo's own analysis: a downstream pin is *their* live
   state, never ours to assume — ask, or read their pin record.
   Implemented as two checks anchored to `release/RELEASE_NOTES_v<current>.md`
   — the authoritative record of what a cut changed — rather than to commit
   ranges, so they hold in a fresh clone: the focus bullet must name at least
   one artifact that release introduced, and any negative governance claim it
   makes must appear in those notes. Both pinned red-first against the real
   shipped bullet. Errata for the two tags is in the CHANGELOG; published
   assets and checksums are immutable and were not touched.
   **The transferable lesson: version literals were machine-visible and the
   claim they sat next to was not, and the claim was the load-bearing part.**
   Worth asking of the other release-facing surfaces before the next cut.
9. **Re-homed from the R1-10 second-glance register** at the 2026-07-27
   retention pass, so archival cannot bury them: the pre-existing worktree at
   `.tmp/review-pr-2` (branch `review/pr2-frame-fixes`) is still present and
   its keep-or-prune is a maintainer call; the `.gitattributes` LF-normalization
   decision remains escalated-not-applied (it would retire the CRLF
   materialization class but changes working-copy bytes for hashed files); and
   the deployment-side halves of the UxS command loop — authenticated transport
   and the SITL gate — remain open (items 1–4 above cover the gated work).

10. **A machine-consumable projection of the governed vocabularies —
   ADJUDICATED AND DONE 2026-07-27.** The governed
   vocabularies ship only as `policy/*.yaml`, so every non-Python consumer
   either vendors a YAML parser plus the raw files or hand-mirrors the parts
   it needs. The consumer that reported P2-01 does the latter: its
   `zmeta_semantics.ts` hand-codes the §7.7 STATE denylist as a mirror of
   `policy/semantics.yaml`. It was byte-aligned across this advance —
   verified by hand, again, which is exactly the point. That is manual
   alignment re-verified at every pin advance, and it is the **live,
   evidenced instance** of the paused Praesens review's finding #3 (policy
   reimplemented rather than sourced), which until now was a drift
   hypothesis. They rate it a workstream input, not a pin blocker, and that
   is the right severity.
   The shape that would fit doctrine, if it is wanted: a *generated,
   derived, hash-pinned* export of the vocabularies that already exist — a
   projection under gate 4, adding no vocabulary under gate 1, living in the
   outer rings under gate 6. It changes no semantics; it removes the reason
   a consumer hand-copies them. This bears directly on the multi-sensor
   event, where participants clone this repo and write adapters in stacks
   that are mostly not Python.
   **Maintainer chose the verbatim projection over a curated bundle or
   generated language bindings, and it shipped:** `export/policy/*.json`,
   one file per governed policy file, same name, same data, generated by
   `tools/export_policy_json.py` and hash-pinned in the manifest under the
   new `policy_json_export` group. The curated-bundle option was declined
   for the right reason — deciding what a consumer needs is a judgement,
   and a judgement creates a third artifact that can drift from both
   parents. `policy_bundle_hash` is unchanged by the addition; that
   invariant is what keeps a derived artifact from perturbing a governed
   one, and it is worth re-checking on any future export.
   Pinned by `gateway/tests/test_policy_json_export.py` — freshness,
   per-file semantic equality, coverage both directions, hash-function
   agreement with the manifest, and manifest membership — with the drift
   pins run against a synthetic repo root so they are known to fail on the
   bad state. **Side finding closed en route:** `policy/README.md` did not
   list `command-evidence.yaml` or `profile-precision.yaml`; the list is
   now complete and pinned to the directory.
   **Still open, and the honest limit of this:** it removes the *reason* to
   hand-copy, it does not remove an existing copy. Whether the fielded
   consumer adopts it is theirs to decide, and finding #3 stays open until
   one does. First real adoption is the evidence to watch for.

**Banked register candidates** live in `docs/r1_11_cold_reread_findings.md`
(CR ledger + VW-01..17) and the doctrine log. Nothing is recorded only in a
commit message. *(Re-checked 2026-07-28 and it had become FALSE: an entire
commit's findings, PC-10, PC-11, and the author-graded-review caveat were
commit-message-only until an independent panel found them. All are now in the
CHANGELOG. A tripwire sentence only works if somebody re-checks it — that is
the lesson, not the sentence.)*

### The lesson worth carrying forward

An interruption once left a **half-applied two-layer fix** that looked
complete and was caught only by reading the working diff. The interruption
ledger and the full execution continuity record live in
`docs/r1_11_full_stack_audit.md` ("HOLD state" / "Execution continuity").
**Resume from the tree, never from the transcript.** This closeout applied
the same rule to its own edits and found two defects no test could see.

---

## Current Position

The semantic contract has been audited, rewritten, and crosswalked against the current implementation stack. The locked v1.0 baseline was verified, and no S1-01B targeted schema implementation task is currently needed. Profile projection preservation has been implemented and audited as sidecar conformance tooling without changing v1.0 schema or event vocabulary. The extension registry has been implemented and audited. The conformance class manifest and claim model have been implemented and audited without changing schemas or making new vocabulary valid. Encoding-negative validation has been implemented and audited for compact CBOR and protobuf invalid-after-decode paths. Profile precision and quantization policy has been implemented and audited as a reference conformance default. The D-011 `TAKEOFF` crosswalk cleanup is complete. The D-001 MAVLink ingress README state payload drift cleanup is complete. S1-09A planned the contract hash and release hash follow-up for D-002, S1-09B implemented the reference release hash policy, manifest, builder, validator, claim hash updates, and optional conformance integration, and S1-09C audited that implementation and closed D-002. S1-10P removed FORGE-derived organizational artifact scope from the ZMeta baseline. S1-10B was stopped before commit, no stopped implementation files remain, and D-004 is closed as removed from ZMeta scope. S1-11A planned the D-003 future versioned semantic branch roadmap and left D-003 open as roadmap-planned. S1-12A planned formal release tag, signature, checksum, and attestation packaging for D-012, S1-12B implemented the release packaging framework without creating real tags/signatures/keys/secrets or semantic drift, and S1-12C audited it and closed D-012. R1-01 published `v1.1.5` from commit `d4d406b43a705ca5b7a314e1d5388c3ca39c750a` with release notes, validation report, release manifest, release package zip, edge/gateway/source bundles, and checksum manifest. S1-13A audited the stack for semantic conformance and stale files, corrected the live compatibility checker/CI target to `v1.1.5`, added explicit v1.0/v1.1.0 observation extension boundary tests, and closed D-009 without changing schemas, policy, adapters, encodings, the semantic contract, or event vocabulary. S1-14 implemented external projection promotion hardening so CoT/JREAP/MAVLink ingress state must carry policy-scoped promotion evidence before becoming authoritative ZMeta state, with operator-tunable reject/warn/degrade/quarantine modes that preserve diagnostics and bandwidth discipline. S1-15A added the risk adjudication semantic baseline: locked/tunable/advisory rule classes, bounded policy actions, filterable risk diagnostics, and operator override constraints. S1-15B conformed the stack to that baseline across policy use limits, validator diagnostics, gateway runtime degradation labels, conformance fixtures, tests, schemas, and docs. S1-15C cleaned up feedback on the contract text, conformance classes, claims, crosswalk, and future-only boundaries. S1-16A added the semantic bad-event corpus and shared adapter harness, promoted generic adapter and CoT projection conformance evidence, and kept broader sensor-adapter certification as planned future work. S1-16B added the kernel-protection doctrine: ZMeta is complete without becoming exhaustive, future core changes must clear a concrete need threshold, and `FUTURE_EXTENSION` remains non-claimable until versioned adoption. S1-17A audited the tracked stack against that doctrine, added full kernel-protection conformance to CI and Makefile, and clarified policy/config tunability boundaries. S1-18A added consumer-side risk filter tooling so operators can choose display, fusion, command, autonomy, AAR, or audit intake posture using existing risk labels without mutating events. S1-18B completed an end-to-end stack and runtime audit, hardened direct CoT egress so malformed state payloads carrying raw observation/evidence fields fail closed, and confirmed the full local validation/runtime/package sweep passes. R1-02 published `v1.1.6` from commit `a42f1b1d538cf2f2318a81203f28d7c656c22ce8`. P1-01 addressed partner feedback by adding post-v1.1.6 integration guidance for external-promotion metadata, clarifying that `trust_ref` is policy-scoped evidence rather than proof of authenticity, strengthening consumer responsibilities for accepted-risk labels, and adding `tools/lint_policy_risk_modes.py` with tests to flag unsafe `ignore` settings on material risk. P1-02 added machine-checkable profile-projection preservation for `payload.extensions.risk_adjudication` and compact `payload.extensions.external_promotion` evidence, strengthened extension registry entry metadata for projection/risk/security/fixture behavior, and rebuilt the current-main release manifest plus example claim hashes. P1-03 added `AGENTS.md` and `docs/zmeta_change_governance.md` as the formal human/AI agent change process, linked them from README/release surfaces, and added governed `process_governance_hash` release-manifest coverage plus downstream clone compatibility limits. R1-03 audited the stack for stale current-release references, ignored local build residue, tracked-source secret risk, and generated artifact residue, then prepared v1.1.7 as the current formal patch release without changing schemas, event vocabulary, or the locked v1.0 semantic kernel. P1-04 (branch `worktree-bearing-frame-fixes`, dated 2026-06-11) closed the bearing reference-frame ambiguity: semantics-contract section 6.4 now normatively requires canonical `payload.bearing.az_deg` to be degrees true north with a convert-or-omit rule for sensor-native frames; the v1.1.0 schema gained an optional `bearing.frame` marker with single-value enum `["TRUE_NORTH"]` (v1.0 untouched and still rejecting the key); the extension registry gained the experimental `BEARING_FRAME` entry; the bad-event corpus gained `observation-bearing-frame-mislabeled` (total 10); the adapter harness gained a value-pinning `expected_values` mechanism (1e-6 numeric tolerance, distinct missing/mismatch codes, boolean pins never match numbers) with the kraken rotation math pinned and a no-heading convert-or-omit fixture (total 9); the Kraken adapter (1.1.0) gained platform-heading compensation and stopped fabricating CSV SNR; the Moth adapter (1.1.0) stopped fabricating omnidirectional bearings; SignalHunter (1.0.1) asserts `TRUE_NORTH`/`GPS_COURSE` provenance for geodesically constructed gradient LOBs; the MAVLink adapter (1.1.0) omits unknown headings (`hdg=65535`/absent) and refuses null-island `(0, 0)` TRACK_STATE fabrication; and the gateway gained opt-in `warn_datagram_bytes` oversize-datagram observability plus a decision-preserving rate-limiter stale-window purge. P1-04 also recorded two verified deferred findings, D-013 and D-014; S1-19 closed them on current `main` with governed timing negative-age diagnostics and compact unknown-integer-key rejection.

Current stack status:

- S1-24 (2026-07-03) prepared the v1.1.10 fielded-safety enforcement release on
  current `main`, aligning policy and reference enforcement with the
  already-normative semantics contract §7.7/§7.8. No schema or v1.0/v1.1.0
  vocabulary change; tightened enforcement rejects events that were always
  contract-violating.
  - Command altitude: `command_event.payload_must_not_contain` now carries the
    full §7.8 set (bare `alt` retained as a superset); `COMMAND_EVENT` altitude
    is refused at any nesting depth (payload/target_geo/geometry/extensions).
    The egress MAVLink command→mission-intent altitude guard was aligned to the
    same set.
  - STATE laundering: the STATE branch in `gateway/src/validators.py` now
    recurses via `_find_forbidden_key` (case-insensitive, reports
    `{field, path}`) like its sibling branches and enforces the full §7.7
    raw-artifact list; deep-nested raw features/measurements/observation
    timestamps/data-refs no longer launder into a STATE projection.
  - Adapter honesty: Kraken and Moth no longer hardcode
    `quality.calibration_state: CALIBRATED`; it is now a keyword parameter
    defaulting to the conservative `UNCALIBRATED`, asserted otherwise only when
    a deployment substantiates it. SignalHunter was already honest.
  - Hardening from adversarial verification: the semantic forbidden-key check
    (`_find_forbidden_key`) and the egress MAVLink altitude guard now
    strip+casefold keys before matching, closing a whitespace-/case-padding
    bypass of the exact-name denylists across all four event families. The
    residual — arbitrarily *renamed* raw content/altitude in free-form objects
    (e.g. `z_m`) — is the inherent limit of a name denylist (closed schemas +
    producer conformance are the mitigation, not denylist growth).
  - Coverage/validation: eleven new deep-nested (schema-valid) bad-event
    fixtures in `conformance/bad-events/must-fail.jsonl` (total 21) plus two
    direct `validate_semantics` unit tests; enforcement was adversarially
    verified with 100+ empirical bypass attempts. The release manifest and
    example claims were regenerated for `zmeta-v1.1.10` (2026-07-03). The full
    kernel gate (incl. `--release-manifest --release-package --bad-events
    --adapter-harness`) and pytest (`444 passed`, 110 subtests) are green.
  - R1-06: the release authority published `v1.1.10` on 2026-07-04: annotated
    tag `v1.1.10` on release commit `6ce4f29`, GitHub release with all seven
    expected assets plus `SHA256SUMS_v1.1.10.txt`, GitHub CI green for the
    pushed release commit. Published checksums-only, consistent with v1.1.5
    through v1.1.9; detached signatures remain an optional release-authority
    step. Published v1.1.9 assets/checksums are unchanged.
  - Post-publication alignment (2026-07-07): current-facing docs, tool
    examples, the CI compatibility target, and the compatibility CLI test were
    aligned with the published `v1.1.10` release (README, installation guide,
    tools README, professional overview header, `.github/workflows/ci.yml`,
    `gateway/tests/test_check_compat_cli.py`). No published release assets,
    manifests, checksums, tags, or signatures were changed.
- S1-25 (2026-07-07) prepared the v1.1.11 field-driven adoption-guidance
  release on current `main`, harvesting upstream PR #4 (a v1.2.0 proposal
  from a live at-scale deployment; reviewed, found kernel-breaking, and NOT
  merged — review posted on the PR with empirical evidence).
  - Advisory docs (Class A): `docs/zmeta_mqtt_binding_guidance.md`,
    `docs/zmeta_vocabulary_crosswalk.md`, and
    `docs/zmeta_correlation_pattern.md` re-derive the PR's fielded needs from
    the locked kernel outward — locked-vocabulary MQTT topic shapes with
    retain/tombstone honesty rules, a dictionary-to-alphabet concept
    crosswalk, and cross-sensor correlation expressed entirely in existing
    v1.0 vocabulary (FUSION identity + INFERENCE/ASSOCIATION bonds with the
    atomic-split invariant credited to the PR).
  - Governed baseline (Class B): four extension-registry entries —
    `CORRELATION_HINT` (proposed), `DATA_REF_MEDIA_METADATA` (proposed,
    future branch), `AGGREGATE_STATE_SNAPSHOT` (reserved),
    `PAYLOAD_SCHEMA_URI` (rejected with rationale so the concept is not
    re-litigated). No new vocabulary becomes valid.
  - Examples/conformance: `examples/zmeta-correlation-pattern-examples.jsonl`
    (7 events, Profile H, registered in `tools/validate_examples.py`) and two
    bad-event fixtures (corpus total 23) proving the correlation hint cannot
    launder `confidence`/`track_id` into observation payloads.
  - Intake doctrine applied (standing): external PRs are field telemetry —
    harvest requirements, re-derive from the kernel outward, never merge
    dialect surfaces, record rejections in the registry, credit contributors,
    and compare our implementation against the contributor's revisions.
  - R1-07: `v1.1.11` was published on 2026-07-08 with explicit release-authority
    direction: annotated tag `v1.1.11` on release commit `922f0ca`, GitHub
    release with all eight expected assets including `SHA256SUMS_v1.1.11.txt`,
    CI green for the pushed release commit. Published checksums-only,
    consistent with v1.1.5 through v1.1.10; detached signatures remain an
    optional release-authority step. Published v1.1.10-and-earlier
    assets/checksums are unchanged.
- S1-26 (2026-07-08) prepared the v1.1.12 governance and honesty closeout
  release on current `main`, working the full relock-gap list per explicit
  maintainer direction. No schema or v1.0/v1.1.0 vocabulary change.
  - Promotion evidence bar (governed docs): `spec/extension-registry.md`
    "Promotion Evidence Requirements" — reserved/proposed concepts enter a
    named version branch only with two or more independent implementations
    demonstrating the need plus a documented contract Section 2.6 failure
    condition the outer rings cannot solve; referenced from the
    change-governance Class D checklist. Encodes the intake doctrine
    (external PRs are field telemetry) into governed process.
  - S1-11B implemented (governed baseline): `spec/future-branch-roadmap.yaml`
    and `.md` — 18 candidates with status, priority, dependencies, required
    surfaces, recorded evidence, and promotion tripwires (including the
    PR #4 tranche-3 candidates and honesty-primitive schema standing), plus
    3 recorded rejection/defer decisions; validated by
    `tools/validate_future_roadmap.py` (registry cross-references, tripwire
    coverage, status-leakage check) with focused tests; new
    `future_branch_roadmap` release-manifest group (groups=19,
    artifacts=70). D-003's closure condition was met; closure was
    recommended and the maintainer closed D-003 at the v1.1.12 cut.
  - Lineage honesty (runtime/reference): kraken/moth/signalhunter/klv/
    mavlink/eo-cv no longer fabricate `lineage.based_on` with random
    UUIDv7s. Observation/system outputs omit lineage unless callers pass
    real `based_on`; mandatory-lineage events refuse to emit without real
    parents (mavlink STATE: `based_on`/`source_zmeta_event_id`; eo-cv
    INFERENCE: `parent_event_ids` or UUIDv7 `source_event_id`). Adapter
    versions bumped; harness fixtures pin the honest behavior (total 11);
    new eo-cv test file; ingress template README states the never-fabricate
    rule (omit or refuse).
  - Gateway containment (runtime): `_send_datagram` catches OSError on the
    two UDP send paths (oversize ~65507-byte payloads previously crashed the
    main loop), drops the datagram with new `send_failure`
    metrics/diagnostics, and counts forwarded/CoT only on actual sends;
    real-socket oversize test included.
  - Documentation honesty (advisory): mapping packs documented as
    declarative descriptions plus test evidence (no runtime engine executes
    `mapping.yaml`); professional overview documents policy + conformance as
    the deliberate enforcement home for `risk_adjudication`/
    `external_promotion`, with schema standing parked as an evidence-gated
    roadmap candidate.
  - Process closeout: the open-ended human-decision list in this handoff is
    resolved to standing defaults (see Next Work Queue); genuinely open:
    release-signing process (maintainer generating a signature, 2026-07-08)
    and v1.1.0 adopted-vs-experimental status.
  - Validation: full kernel gate, roadmap validator, strict examples
    (47/47), policy lint, pytest (465 passed, 110 subtests), workflow
    end-to-end (H/M), live gateway (JSON/compact), gateway self-tests,
    check_compat `v1.1.12` for all eight corpora, packet-size max=150/240,
    release package validation, and verified `SHA256SUMS_v1.1.12.txt`.
  - R1-08: `v1.1.12` was published on 2026-07-08 with explicit
    release-authority direction: `main` and the annotated tag pushed
    (release commit `e5a88b1`), GitHub CI green, GitHub release with all
    eight assets, marked Latest, checksums-only (the maintainer is standing
    up the signing process for the next release). Post-publication
    alignment moved current-facing docs, the CI compatibility target, and
    the compatibility CLI test to `v1.1.12`, and D-003 was closed by
    maintainer decision — the deferred issue register is now fully closed.
- P1-06 (2026-07-15) added the onboarding batch on current `main` (Class A +
  Class C reference; no governed-artifact change): README first-contact
  restructure (ten-minute proof, Start Here By Role, ZMeta In The Field),
  the `adapters/ingress/example-vendor/` worked exercise, the
  `tools/check_adapter.py` one-command ladder wrapper plus advisory harness
  fixture schema, GitHub issue/PR templates, the `docs/README.md`
  guidance-vs-process index, worklog retention (S0-01..R1-05 archived to
  `docs/zmeta_refinement_worklog_archive.md`), and standing RELEASE_CHECKLIST
  doc-currency/retention items. Maintainer decisions deferred: naming the
  fielded deployments in ZMeta In The Field; the MAVLink template-file
  rename; RF golden sample pairs (need sanitized field captures); the
  physical docs/process/ move; a mechanical conformance-claim generator.
  Details in the worklog Current Resume Note.
- P1-05 (2026-07-15) added adapter-author onboarding consolidation on current
  `main` (Class A; no schema, policy, vocabulary, or validation-behavior
  change): `adapters/AUTHORING.md` as the single consolidated authoring entry
  point for humans and AI agents (linked from `adapters/README.md`), plus the
  worked EO full-chain corpus `examples/zmeta-eo-chain-examples.jsonl`
  registered in `tools/validate_examples.py` (strict examples corpus is now
  51 events). Driven by external-adopter demand; details in the worklog
  Current Resume Note.
- The P1-04 bearing reference-frame integrity pass and P1-04R review fixes are
  adopted on `main` for v1.1.8. Schema 1.1.0 gained the optional
  `bearing.frame` marker; the locked v1.0 schema is untouched.
- Moth tunnel/replay and MAVLink `hdg` values no longer emit canonical
  bearing/heading fields unless callers explicitly assert `TRUE_NORTH`;
  unasserted native values remain auditable under explicitly named
  non-canonical fields.
- Use tag `v1.1.19` for current formal release assets and checksums **once it
  exists — it does not yet.** v1.1.19 is prepared, not published: no tag, no
  signature, no upload. Until then `v1.1.18` is the published release and the
  one to clone for byte-exact verification.
  *This line is machine-pinned on its version literal only, so it went on
  naming a tag that had never been created while the pin stayed green — the
  prose-beside-a-pinned-literal blind spot this cycle was convened to fix,
  found inside the record announcing the fix.* Use tag `v1.1.17` for the baseline before that. Use tag
  `v1.1.15` for the SAPIENT-bridge baseline and `v1.1.14` for the
  audit-driven honesty-hardening baseline.
- Use current `main` for the latest integration baseline with bearing-frame
  integrity, policy-risk linting, projection preservation for risk/promotion
  extensions, stricter extension registry metadata, formal human/AI agent
  change governance, downstream clone interoperability limits, and
  stale-release-reference audit cleanup.
- Post-release cleanup commit `9fc526e` is pushed to `origin/main`; it aligned
  current-facing docs, tools examples, CI compatibility target, and the
  compatibility CLI test with `v1.1.8`. No published v1.1.8 release assets,
  manifests, checksums, tags, or signatures were changed.
- Final baseline audit cleanup aligned two remaining current-facing guidance
  examples with `v1.1.8`: the adapter `check_compat` command and the
  change-governance manifest rebuild command. Published
  `SHA256SUMS_v1.1.8.txt` and release assets remain unchanged.
- Final baseline audit closeout is pushed at `c814d95` on `origin/main`
  (`beffed3` was the preceding guidance-cleanup commit).
  The full local validation suite, focused validators, workflow/live gateway
  smoke tests, package/bundle build checks, Docker Compose config rendering,
  GitHub PR/issue queue check, and GitHub CI passed. The tracked worktree is
  clean; only ignored local cache/build residue remains.
- S1-23 refreshed the README-linked documentation surface on 2026-06-18. The
  tracked Markdown/TXT link audit found no broken relative links, `git
  ls-files --others --exclude-standard` returned no rogue untracked files, and
  `spec/installation-guide.md` now points new installs at the maintained
  `configs/` templates while keeping release-publication boundaries explicit.
- R1-05 publishes the post-v1.1.8 current-main documentation freshness,
  governance hygiene, timing/compact follow-up, and release-process cleanup as
  `v1.1.9`. Historical `v1.1.8` release notes, validation report, assets, and
  checksums remain preserved.
- D-013 (timing-freshness negative-age clamp) and D-014 (compact codec
  unknown integer payload keys) are closed on current `main`. The stack now
  labels out-of-tolerance negative TIME_STATUS age with
  `TIMING_STATUS_AGE_NEGATIVE` and rejects unknown compact integer keys at
  decode instead of degrading them to strings.
- Current `main` also adds advisory industry-sharing posture docs:
  `IP_POLICY.md`, `CONTRIBUTING.md`, `CONFORMANCE.md`, `TRADEMARK.md`, and
  `docs/zmeta_defensive_publication.md`. These docs clarify Apache-2.0
  baseline limits, contributor authority, conformance/private dialect claims,
  ZMeta name use, and public defensive-publication posture without changing
  schemas, policy behavior, event vocabulary, or the locked v1.0 kernel.
- Future work is optional and should be driven by real sensor captures, a versioned semantic branch decision, release-authority signing process, formal legal review, or standards-body adoption.

Current release target:

- Release URL: <https://github.com/JTC-byte/zmeta-spec/releases/tag/v1.1.18>
- Tag: `v1.1.18` (annotated, on release commit `157d41f`, published
  2026-07-27 with all eight assets including `SHA256SUMS_v1.1.18.txt`;
  CI green on both the tag and `main` runs).
- Previous releases: `v1.1.17` (R1-11 audit/hardening cut, tag on
  `7302073`, published the same day), `v1.1.16` (edge-comms bladeRF
  corpus), `v1.1.15` (SAPIENT bridge). Their published assets,
  checksums, and release records are unchanged and immutable.
- Signature status: `v1.1.18` is published checksums-only per the
  maintainer's signing decision, consistent with v1.1.5 through
  v1.1.17; signing remains the maintainer's external process. Verify
  with `SHA256SUMS_<version>.txt`, the structured release manifest, and
  the release package checksum file.
- Post-release main note: post-tag commits regenerate the in-repo
  manifest under the current identity, so `main` diverges from the
  published `v1.1.18` manifest/package pins. Published checksums are
  immutable; the next cut resolves it. This is the documented A-12
  roll-forward pattern, not a defect — **deploy from the tag.**

## Key Docs

| Document | Purpose |
| --- | --- |
| `AGENTS.md` | Root quick-start guide for human maintainers and AI agents working in this governed repository. |
| `docs/zmeta_change_governance.md` | Formal change process, authority order, left/right limits, documentation matrix, validation gates, and release publication workflow. |
| `IP_POLICY.md` | Advisory open-specification, contributor authority, and industry-sharing posture. |
| `CONTRIBUTING.md` | Contribution license, authority, sign-off, semantic-boundary, and validation expectations. |
| `CONFORMANCE.md` | Definitions for ZMeta-conformant, compatible, derived, private dialect, and experimental extension claims. |
| `TRADEMARK.md` | Advisory name-use guidance for ZMeta compatibility and conformance statements. |
| `docs/zmeta_defensive_publication.md` | Public technical disclosure intended to make the open ZMeta architecture easier to cite and socialize. |
| `docs/zmeta_professional_overview.md` | Advisory overview for engineers, operators, and leadership explaining ZMeta purpose, architecture, profiles, governance, provenance, and enabled workflows. |
| `spec/semantics-contract.md` | Authoritative hardened semantic contract. Schemas, policy packs, adapters, encodings, examples, gateways, and conformance tests must preserve it. |
| `docs/zmeta_semantic_contract_lockdown_audit.md` | S0-01 audit of the prior contract against intended ZMeta roles, implementation surfaces, and future ISR/edge AI/coalition/mesh trust needs. |
| `docs/zmeta_contract_to_stack_crosswalk.md` | S0-03 contract-to-implementation crosswalk and prioritized implementation backlog. |
| `docs/s1_01_v1_baseline_verification_plan.md` | S1-01A v1.0 baseline verification. Confirms current v1.0 schema/policy coverage and states S1-01B is not needed. |
| `docs/s1_02_profile_projection_preservation_plan.md` | S1-02A plan for profile projection invariants, field catalog, fixture format, positive/negative conformance cases, and S1-02B file-by-file implementation. |
| `spec/profile-projection-field-catalog.md` | Human-readable guide to the profile projection field catalog and fixture semantics. |
| `conformance/profile_projection_field_catalog.yaml` | Machine-readable projection field catalog. |
| `conformance/profile-projection/` | Source/projected projection fixture suite. |
| `docs/s1_03_extension_registry_plan.md` | S1-03A plan for extension registry artifacts, statuses, categories, collision rules, adoption requirements, and validation. |
| `spec/extension-registry.md` | Human-readable extension registry governance, status definitions, collision rules, and adoption requirements. |
| `spec/extension-registry.yaml` | Machine-readable extension registry. Existing v1.1.0 entries are experimental; future entries are reserved/proposed. |
| `docs/s1_03c_extension_registry_audit.md` | S1-03C audit confirming extension registry implementation, validation behavior, and version-boundary protection. |
| `spec/future-branch-roadmap.md` | Governance companion for the S1-11B machine-readable future-branch roadmap: authority limits, field definitions, and usage. |
| `spec/future-branch-roadmap.yaml` | Machine-readable D-003 roadmap: candidates with status, dependencies, required surfaces, recorded evidence, promotion tripwires, and rejection/defer decisions. Not a vocabulary source. |
| `tools/validate_future_roadmap.py` | Standalone validator for the future-branch roadmap (structure, registry cross-references, tripwire coverage, status-leakage check). |
| `docs/s1_04_conformance_class_manifest_plan.md` | S1-04A plan for conformance class artifacts, claim model, dependencies, validation, and implementation path. |
| `spec/conformance-classes.md` | Human-readable conformance class and claim model. |
| `conformance/conformance_classes.yaml` | Machine-readable conformance class manifest. |
| `conformance/claims/` | Example implementation claim files for reference gateway and core producer. |
| `docs/s1_04c_conformance_class_manifest_audit.md` | S1-04C audit confirming conformance class implementation, claim validation, and no schema/contract/registry drift. |
| `docs/s1_05_encoding_negative_validation_plan.md` | S1-05A plan for compact/protobuf invalid-after-decode fixtures, validator tooling, gateway/CLI negative coverage, and D-007 closure path. |
| `conformance/encoding-negative/` | S1-05B compact/protobuf/gateway invalid-after-decode fixture suites. |
| `docs/s1_05c_encoding_negative_validation_audit.md` | S1-05C audit confirming encoding-negative validation coverage and closing D-007. |
| `docs/s1_06_profile_precision_quantization_policy_plan.md` | S1-06A plan for profile precision ceilings, utility floors, conservative rounding, packet-budget interaction, and S1-06B implementation. |
| `spec/profile-precision-policy.md` | Human-readable profile precision and quantization policy guide. |
| `policy/profile-precision.yaml` | Reference conformance default precision policy; requires mission review. |
| `conformance/profile-precision/` | Source/projected precision policy fixture suite. |
| `docs/s1_06c_profile_precision_quantization_policy_audit.md` | S1-06C audit confirming profile precision policy implementation and closing D-010. |
| `docs/s1_07a_takeoff_crosswalk_cleanup.md` | S1-07A cleanup note confirming the crosswalk typo was removed and `TAKEOFF` remains invalid current vocabulary. |
| `docs/s1_08a_mavlink_state_payload_drift_cleanup.md` | S1-08A cleanup note confirming MAVLink STATE_EVENT documentation no longer maps raw telemetry into `payload.features.*`. |
| `docs/s1_09_contract_release_hash_plan.md` | S1-09A plan for contract hash taxonomy, release manifest structure, deployment gates, claim integration, and S1-09B implementation. |
| `spec/release-hash-policy.md` | S1-09B release hash policy for narrow semantic contract hashes, broader release manifests, canonicalization, and deployment/claim guidance. |
| `release/zmeta-release-manifest.yaml` | Reference hardening-baseline manifest with governed artifact hashes. |
| `docs/s1_09c_contract_release_hash_audit.md` | S1-09C audit confirming release hash reproducibility, claim integration, and D-002 closure. |
| `docs/s1_10p_forge_scope_purge.md` | S1-10P cleanup note removing out-of-scope organizational artifact scope from the ZMeta baseline. |
| `docs/s1_11_future_versioned_semantic_branch_roadmap_plan.md` | S1-11A roadmap for future versioned semantic branches under D-003. |
| `docs/s1_12_formal_release_tag_signature_attestation_plan.md` | S1-12A plan for formal release tag, checksum, signature, attestation, and verification packaging under D-012. |
| `docs/s1_12c_formal_release_packaging_audit.md` | S1-12C audit closing D-012 after verifying release packaging support. |
| `docs/s1_13a_stack_conformance_and_stale_file_audit.md` | S1-13A audit confirming stack conformance, stale-file posture, v1.1.5 compatibility target alignment, and D-009 closure. |
| `docs/s1_14_external_projection_promotion_contract.md` | S1-14 implementation note for external projection promotion policy, profile behavior, and bandwidth guardrails. |
| `docs/s1_15b_risk_adjudication_stack_conformance_audit.md` | S1-15B folder-by-folder audit confirming policy, gateway, conformance, tests, and docs emit filterable accepted-risk semantics. |
| `docs/s1_15c_semantic_contract_feedback_cleanup.md` | S1-15C cleanup note for semantic-contract feedback on CoT promotion, self-labels, overrides, diagnostics, conformance classes, and future-only boundaries. |
| `docs/s1_16a_bad_event_adapter_harness.md` | S1-16A implementation note for semantic bad-event fixtures and the shared adapter conformance harness. |
| `docs/s1_16b_kernel_protection_contract_alignment.md` | S1-16B alignment note for completeness without exhaustiveness, the core semantic change threshold, and future-extension non-claimability. |
| `docs/s1_17a_kernel_protection_stack_audit.md` | S1-17A stack audit confirming live tracked surfaces conform to kernel-protection doctrine and wiring full kernel conformance into CI/local release flow. |
| `docs/s1_18a_operator_risk_filter_tooling.md` | S1-18A implementation note for consumer-side accepted-risk filtering and operator posture presets. |
| `docs/s1_18b_end_to_end_stack_runtime_audit.md` | S1-18B audit note for folder-by-folder semantic conformance, runtime workflow sweep, package smoke tests, and CoT egress hardening. |
| `docs/r1_03_v1_1_7_stack_audit_release.md` | R1-03 audit and release note for v1.1.7 stale-reference, generated-residue, secret-scan, and release-package cleanup. |
| `docs/r1_04_v1_1_8_bearing_frame_release.md` | R1-04 audit and release note for v1.1.8 bearing-frame integrity, adapter hardening, and release publication. |
| `conformance/bad-events/` | Semantic bad-event fixture suite for dishonest or unsafe events that must not be treated as clean data. |
| `conformance/adapter-harness/` | Shared fixture-driven adapter output harness for schema/policy validity, layer separation, lineage, timing, and external promotion. |
| `spec/release-signing-attestation.md` | S1-12B release signing, attestation, no-secret, and verification framework. |
| `release/RELEASE_PACKAGE_README.md` | S1-12B release package template guidance. |
| `release/RELEASE_NOTES_v<version>.md` | Published release notes, one file per formal release (v1.1.7 onward; the "Current release target" section above names the current version). |
| `release/VALIDATION_REPORT_v<version>.md` | Published validation report, one file per formal release. |
| `release/SHA256SUMS_v<version>.txt` | Published checksum manifest for each formal release's standard assets. |
| `tools/lint_policy_risk_modes.py` | Policy lint for unsafe `ignore` settings on material risk. |
| `docs/zmeta_refinement_worklog.md` | Running worklog: Current Resume Note (recent sessions), pending work items, and the deferred issue register. |
| `docs/zmeta_refinement_worklog_archive.md` | Completed task sections S0-01..R1-05, archived verbatim per the release-checklist retention pass. |

## Completed Recently

Completed work items S0-01 through R1-05 (contract lockdown, projection
preservation, registry, conformance classes, encoding-negative, precision
policy, release hashing/packaging, risk adjudication, bad-event corpus and
adapter harness, bearing-frame integrity, and the v1.1.5-v1.1.9 releases)
are recorded verbatim, one section each, in
`docs/zmeta_refinement_worklog_archive.md`. Later sessions (S1-24 onward)
are summarized in "Current stack status" above and in the worklog Current
Resume Note.

## Current Decisions

- The semantic contract is authoritative; implementation surfaces must preserve it.
- Humans and AI agents should follow `AGENTS.md` and
  `docs/zmeta_change_governance.md` before changing governed artifacts.
- Downstream clone users can integrate locally around pinned releases, but
  schema, vocabulary, version-dispatch, projection, risk, or command-authority
  changes are private dialect/fork work unless governed, versioned, documented,
  and backed by conformance evidence.
- Current formal release is `v1.1.18` (published 2026-07-27); latest integration baseline is
  current `main`.
- v1.0 remains locked.
- Do not add v1.1.0 or future concepts to v1.0.
- S1-01A found no schema-enforceable v1.0 gap requiring S1-01B.
- Profile projection preservation is now covered by a sidecar field catalog and source/projected conformance pairs.
- Compact Profile L and protobuf remain encoding projections; both must decode to canonical JSON before schema, policy, and projection checks.
- Existing strict conformance remains stable by default. Projection checks are explicit via `tools/validate_projection.py` or `tools/validate_conformance.py --strict --profile-projection`.
- The extension registry should be implemented as spec-owned artifacts:
  `spec/extension-registry.md` and `spec/extension-registry.yaml`.
- Existing v1.1.0 extension concepts should remain `experimental` by default
  until a version/release decision promotes them.
- Reserved/proposed concepts are not valid event vocabulary.
- Registry validation is standalone and opt-in through
  `tools/validate_extension_registry.py` or
  `tools/validate_conformance.py --strict --extension-registry`.
- D-006 is closed after S1-03C verified the registry implementation.
- D-011 is closed. S1-07A removed the erroneous crosswalk `TAKEOFF`
  current-vocabulary reference while preserving the validator/test guard proving
  `TAKEOFF` remains invalid.
- Conformance classes organize implementation claims and required evidence.
  They do not create semantics or make future classes claimable.
- Conformance class validation is standalone and opt-in through
  `tools/validate_conformance_classes.py` or
  `tools/validate_conformance.py --strict --conformance-classes`.
- `ZMETA-ADAPTER` and `ZMETA-COT-PROJECTION` are now implemented with shared
  adapter-harness evidence. Broader `ZMETA-SENSOR-ADAPTER` certification remains
  planned until more native-message variants are covered.
- ZMeta is complete enough to prevent semantic corruption without becoming an
  exhaustive mission ontology. Mission-specific behavior belongs in policy
  packs, deployment configuration, adapters, profiles, extension branches,
  operator views, or mission plugins unless a concrete ambiguity, failure, or
  safety/audit gap requires core contract work.
- Contract and policy rules are classified as `LOCKED`, `TUNABLE`, `ADVISORY`,
  or `FUTURE_EXTENSION`. Future-extension concepts are visible for governance
  but remain non-claimable until versioned schema/policy/adapter/encoding and
  conformance evidence exists.
- CI and `make validate-kernel` run the full kernel-protection conformance path:
  profile projection, extension registry, conformance classes,
  encoding-negative, precision policy, release manifest/package, bad-event
  corpus, and adapter harness.
- `tools/filter_risk.py` lets consumers filter JSONL streams by existing
  `risk_adjudication` and diagnostic labels. Presets include `display`,
  `fusion`, `state`, `command`, `autonomy`, `aar`, and `audit`; the tool passes
  accepted events unchanged and can emit dropped-event reasons to a sidecar.
- Profile projection treats `payload.extensions.risk_adjudication` as
  preserved policy/use-limit evidence when present. Profile L/M/H projections
  must not strip accepted-risk labels in ways that make degraded data appear
  clean.
- Profile projection requires compact
  `payload.extensions.external_promotion` evidence to preserve policy ID,
  trust reference, lineage status, and loop/reflection status while allowing
  Profile L to omit selected H-only audit detail when producer-authority policy
  still validates the projected event.
- Extension registry entries declare and validate
  `profile_projection_behavior`, `risk_relevant`,
  `must_preserve_when_used_for_policy`, `security_privacy_notes`, and
  `fixture_references` so future vendor or edge extensions cannot hide
  policy-relevant behavior behind ignorable metadata.
- Example claim files now use the narrow semantic `contract_hash` from
  `release/zmeta-release-manifest.yaml` and record broader category hashes under
  `release_hashes`. `release_manifest_hash` is omitted from claims to avoid
  circularity because the reference manifest includes the claim files.
- S1-04C verified the conformance class implementation. D-008 is closed.
- S1-05A planned encoding-negative validation only. Compact/protobuf remain
  wire projections, and S1-05B should prove invalid decoded compact/protobuf
  events cannot bypass schema, policy, projection, gateway, CLI, registry, or
  conformance expectations.
- S1-05B implemented encoding-negative validation as an opt-in suite. Default
  `--strict` remains unchanged. The compact/protobuf classes now include
  encoding-negative evidence, but no new conformance class was added.
- S1-05C verified encoding-negative validation. D-007 is closed. Remaining
  policy-specific examples from S1-05A are optional future breadth, not an
  encoding-layer bypass gap.
- S1-06B implemented the reference conformance default precision policy,
  precision fixture suite, validator, focused tests, optional
  `--precision-policy` conformance flag, and profile/projection class evidence
  updates.
- S1-06C audited precision policy quality, conservative rounding, utility
  floors, validator behavior, fixture coverage, packet-budget guardrails,
  projection interaction, conformance integration, and docs. D-010 is closed.
- Precision policy is profile/export policy, not schema, release policy, trust
  policy, emergency mode, UI policy, or transport semantics. Reference defaults
  require mission review.
- D-001 is closed. MAVLink ingress README guidance now prohibits STATE_EVENT
  raw `payload.features.*` and points telemetry into state-safe fields,
  `payload.quality`, SYSTEM_EVENT status, OBSERVATION_EVENT where appropriate,
  and lineage. Implementation inspection found no MAVLink STATE_EVENT
  raw-feature emission, so no D-012 follow-up was added.
- S1-09C verified the reference release hash system and closed D-002. It keeps
  `tools/compute_contract_hash.py` focused on the existing gateway-compatible
  schema/policy/semantic hash workflow, while `release/zmeta-release-manifest.yaml`
  records broader governed baseline hashes. Committed reference manifests use
  stable placeholder git metadata by default; formal release generation must
  pass explicit metadata. Formal tagged-release signatures and post-release
  attestations are tracked separately as D-012.
- S1-10P removed out-of-scope organizational artifact content from the ZMeta
  baseline. ZMeta remains focused on event semantics, profiles, adapters,
  encodings, validation, conformance, and release baselines.
- D-004 is closed as `CLOSED - REMOVED FROM ZMETA SCOPE`.
- S1-11A established a plan-only roadmap for future versioned semantic
  branches. D-003 remains `OPEN - ROADMAP PLANNED`; no future branch was
  implemented or approved.
- S1-12A established a plan-only path for formal release tags, checksums,
  detached signatures, release attestations, key-handling guardrails, and
  consumer verification. It made no tags, signatures, keys, schemas, release
  manifests, validators, runtime code, or vocabulary changes.
- S1-12B implemented the release package framework. The builder supports
  dry-run/no-signature mode and explicit package writes; the validator supports
  template-only and package-output validation, checksum checks, attestation hash
  checks, and no-secret checks.
- S1-12C audited the release package framework, verified template/package
  validation, no-secret behavior, release manifest integration, optional
  conformance integration, and absence of real tags/signatures/keys/secrets or
  semantic drift. D-012 is closed.
- R1-01 published the validated `v1.1.5` GitHub release and pushed `main` and
  the annotated `v1.1.5` tag. The release includes source, edge, gateway, release
  package, release manifest, release notes, validation report, and checksum
  assets. No `.asc` signatures were attached because no approved local signing
  key was available.
- S1-13A corrected stale live `v1.1.4` compatibility-checker and CI targets to
  `v1.1.5`, verified ignored local artifacts are expected generated/local state,
  and closed D-009 with explicit boundary tests for v1.0 generic observation
  extensions versus v1.1.0 formal contracts.
- S1-14 treats external tactical state ingress as a promotion boundary.
  CoT/JREAP/MAVLink state producers remain allowed only when
  `payload.extensions.external_promotion` satisfies producer-authority policy;
  Profile L may carry compact handles only, preserving bandwidth efficiency.
  The reference policy rejects invalid promotion by default, but operators can
  tune the response to warn, degrade, or quarantine while retaining explicit
  diagnostics and confidence/TTL effects.
- S1-15A establishes risk adjudication as the semantic model for configurable
  operational behavior: locked interoperability rules stay strict, tunable
  runtime rules may use reject/warn/degrade/quarantine/ignore within bounds, and
  soft acceptance must remain filterable through labels or correlated
  diagnostics. Policy can also declare allowed/prohibited operational uses, such
  as display-only, AAR-only, blocked-from-fusion, or blocked-from-command-basis.
- S1-15B implements that baseline in the live stack. Timing, lineage, external
  promotion, and runtime timing-loss degradation now produce explicit risk
  labels and use limits when accepted under soft policy.
- S1-15C aligns the contract text and conformance classes with that behavior:
  lossy CoT/TAK ingress now defers to external promotion, material risk labels
  are mandatory when diagnostics may not travel, and projection-origin,
  network-report parent evidence, and policy-adjudication subtypes remain
  future-only.
- S1-18B verified the tracked stack end to end against the semantic contract
  and local runtime workflows. Direct CoT egress now rejects malformed
  `STATE_EVENT` payloads that still carry raw observation/evidence fields,
  matching the layer-separation rule already enforced by gateway validation.
- P1-04 makes canonical bearings true north by contract (section 6.4):
  sensor-native frames must convert (with a heading source) or omit the
  canonical bearing while preserving the raw measurement in `features`.
  `bearing.frame` is an optional v1.1.0 marker with single-value enum
  `["TRUE_NORTH"]`; `BEARING_FRAME` is experimental in the registry; v1.0
  producers carry `quality.bearing_frame`/`quality.heading_source`
  provenance instead. Adapters must not fabricate bearings, SNR, headings,
  or positions; refuse-to-emit/omit is the schema-legal response to
  unavailable data. Moth tunnel/replay and MAVLink `hdg` inputs now require
  explicit `TRUE_NORTH` assertions before emitting canonical bearing/heading
  fields; otherwise the native values are retained only under explicitly named
  non-canonical fields.
- The adapter harness can pin exact output values per fixture through
  `expected_values` (1e-6 numeric tolerance, distinct
  `ADAPTER_EXPECTED_VALUE_MISSING`/`MISMATCH` codes, and a boolean type
  guard so a boolean pin never matches numeric output).

## Resolved Recent Findings

- **D-013 (timing freshness)**: closed on current `main`. Negative event age
  against the latest applicable TIME_STATUS is no longer clamped to zero.
  `policy/timing-freshness.yaml` now defines profile-specific
  `max_negative_age_ms` and default `negative_age_mode: warn`; validators emit
  `TIMING_STATUS_AGE_NEGATIVE` with timing risk labels when the tolerance is
  exceeded. Deployments may tune the mode to reject or degrade.
- **D-014 (compact codec)**: closed on current `main`. Compact v1 decoders now
  reject unknown integer keys in governed compact maps instead of converting
  them to decimal string keys. String extension keys remain preserved.

Follow-up notes (candidates for future hardening decisions, not register
entries):

- RESOLVED in v1.1.12 (S1-26 gateway containment): oversize outgoing UDP
  payloads (roughly 65507+ bytes) no longer raise an unhandled `OSError` in
  the gateway main loop — `_send_datagram` catches OSError, drops the
  datagram with explicit `send_failure` metrics/diagnostics, and counts
  forwarded/CoT only on actual sends.
- RESOLVED in v1.1.12 (S1-26 lineage honesty): ingress adapters no longer
  fabricate `lineage.based_on` with fresh random UUIDv7s — observation and
  system outputs omit lineage unless callers pass real parents, and
  mandatory-lineage events refuse to emit without them.
- Bearing frame provenance is still producer/configuration asserted. The
  `TRUE_NORTH` marker and `quality.heading_source` make the assertion auditable
  and reject unsupported labels, but they do not prove calibration,
  authenticity, or frame correctness. Treat deeper verification as future
  trust/PNT/integrity work rather than a current release blocker.

## Next Work Queue

1. **R1-11 full-stack audit — ✅ COMPLETE (closed 2026-07-27).** The audit
   ran, its findings were worked across the health/records/governed waves,
   and the cycle published as `v1.1.17` then `v1.1.18`. Findings record:
   `docs/r1_11_full_stack_audit.md`; the fresh-eyes re-read and its
   disposition ledger: `docs/r1_11_cold_reread_findings.md`. The history
   below is retained for provenance only.
   *(original entry follows)*
   - History: the R1-10 cycle (audit + fix pass + verification audit +
     v1.1.14) completed 2026-07-17 and left open whether a fresh
     full-stack audit runs before the backlog resumes. The maintainer
     then directed the SAPIENT lane (P1-07 mapping pack + official
     Apex end-to-end validation + **v1.1.15 released 2026-07-21**,
     worklog P1-07 entries), and on 2026-07-21 closed the decision:
     a full audit, run safely in a fresh session, precedes the
     backlog.
   - R1-11 inputs (gather at audit start): the R1-10 flagged residuals
     (signalhunter replay wall-clock ts; GPS no-lock (0,0)
     sensor_position_2d; dead internal alt_m 0.0 dict); the
     second-glance register (worklog R1-10 closeout entry: unencoded
     SHOULD-level checks — fusion-confidence ceiling warn,
     gateway-backfilled t_publish marker, lineage.transform prefix
     opt-in scope, published-SHA256SUMS immutability pin;
     .gitattributes decision; .tmp/review-pr-2 worktree; resume-note
     retention) plus the P1-07 additions (CoT-template loop_status
     default sync with the paused CoT egress cluster; harness
     registration-object entry-point gap); and the new-since-R1-10
     surface (the whole SAPIENT pack/adapters/fixtures/policy block,
     v1.1.15 release artifacts) — already build-verified and
     Apex-validated, but not yet covered by a full-stack audit pass —
     and the P1-08 merge (PR #7 edge-comms-bladerf pack + maintainer
     review fixes) including its second-glance candidate: canonical
     bearing without frame provenance passes every machine gate
     (bearing_frame is value-when-present; contract 6.4 tolerates
     legacy-unlabeled v1.0 bearings) — a presence-when-bearing-emitted
     warn-check is an R1-11 candidate.
   - Method precedent: R1-10 (finder lenses from prior AAR lessons,
     one adversarial verifier per substantive finding, live probes,
     falsifiable evidence, commit-truth checks) —
     `docs/r1_10_full_stack_audit.md` is the findings-record template.
   - Everything below this item is queued behind the R1-11 audit.

1a. **Queued (maintainer direction 2026-07-21): two adapter work
   items behind R1-11** — *(status 2026-07-27: the **bladeRF ingress adapter
   is DONE** — `adapters/ingress/bladerf/`, commit `71f8e18`, shipped in
   v1.1.18 with 67 colocated tests and 8 harness fixtures. The SAPIENT
   follow-ups below remain the surviving item.)*
   - **bladeRF ingress adapter** implementing the merged
     `edge-comms-bladerf` mapping pack (PR #7): detect/translate/
     validate per `adapters/AUTHORING.md`, the pack's two real-capture
     fixture pairs as acceptance evidence, harness fixtures + colocated
     tests per the kraken/moth precedent. If the PR #7 contributor
     supplies a producer frame assertion for the heading-derived
     bearing, the adapter gains the canonical-bearing path
     (quality.bearing_frame TRUE_NORTH + heading_source).
   - **SAPIENT follow-ups** (the ingress/egress adapters themselves
     shipped in v1.1.15): the deliberately-deferred SAPIENT Task
     ingress (external DMMs tasking ZMeta platforms — command-safety
     escalation required before any work), live-enclave validation
     against the official C# BSI Flex 335 v2 test harness and
     multi-node Apex routing (recorded as not-exercised in the pack
     README), and the harness registration-object entry point (P1-07
     second-glance item b) that would make the four inexpressible
     registration-dependent harness fixtures one-liners.

2. **Queued: v1.1.0 adoption decision (all fourteen concepts)**
   - Maintainer direction (2026-07-08): build the per-concept evidence
     worksheet (repo-side evidence for all fourteen experimental v1.1.0
     registry concepts, field-side evidence supplied by the maintainer)
     and make the adopt-vs-stay-experimental decision for every concept in
     that same session — no prolonging.
   - Evidence standard: the promotion evidence bar in
     `spec/extension-registry.md` (two or more independent implementations
     demonstrating the need plus a documented semantic-contract Section 2.6
     failure condition). Candidate telemetry: the maintainer's fielded
     deployment plus the upstream PR #4 deployment. RESOLVED 2026-07-21
     (P1-09): PR #4 closed unmerged with credit — no contributor
     revisions ever arrived; its telemetry stands as recorded n=1
     evidence on the registry/roadmap candidates, and the adoption
     session should treat those records (not the PR) as the evidence
     source. The PR #7 edge-comms deployment (P1-08) is a potential
     second evidence leg where its telemetry overlaps.
   - Expected shape for concepts that clear the bar: registry status
     changes (`experimental` -> `adopted`), conformance-class and doc
     updates, one release; no schema file changes. Expanded command-task
     concepts stay experimental absent fielded command-loop evidence.
   - Aside from that queued session, the stack is closed for the downstream
     integration baseline: S1-11B is implemented, the deferred issue
     register is fully closed, and remaining follow-ups activate only on
     real sensor data, an evidence-bar tripwire, or release-authority
     signing inputs.

3. **Standing defaults (recorded 2026-07-08 by maintainer direction)**
   The former open-ended "human decisions for future hardening" list is
   resolved to standing defaults: the shipped reference behavior stands
   unless field evidence or a promotion-evidence-bar tripwire
   (`spec/extension-registry.md`, `spec/future-branch-roadmap.yaml`) forces a
   revisit. Specifically:
   - Precision policy reference defaults (values, profile scoping,
     quantization basis, confidence rounding, command-vs-display strictness,
     RF variation) stand as reference conformance defaults requiring mission
     review; enforcement stays in conformance, not gateway exports.
   - Opt-in conformance flags (`--encoding-negative`, `--precision-policy`,
     `--extension-registry`) remain opt-in for downstream users; CI and
     `make validate-kernel` already run the full kernel path, which is the
     gate that protects releases.
   - Conformance class statuses stay `implemented`; claim files keep
     command/result summaries without captured-output artifacts.
   - Encoding-negative fixtures keep their current byte-storage format; no
     separate `ZMETA-ENCODING-NEGATIVE-VALIDATION` class — evidence stays
     folded into the compact/protobuf classes.
   - Vendor/private namespaces keep the `vendor.<owner>.<name>` convention;
     classified/restricted name representation is deferred to the
     future-branch roadmap.
   - Adapter-harness breadth grows only with real sensor captures; broader
     `ZMETA-SENSOR-ADAPTER` certification stays planned until then.
   - S1-11B is implemented (`spec/future-branch-roadmap.yaml` +
     `tools/validate_future_roadmap.py`); that decision is closed.

4. **Genuinely open maintainer decisions**
   - Release signing: releases since v1.1.5 are checksums-only. The release
     authority is standing up a signature (in progress 2026-07-08); whether
     future formal releases publish detached signatures and post-release
     claim attestations (including `release_manifest_hash`) follows from
     that process.
   - Whether v1.1.0 remains permanently `experimental` or is adopted as a
     baseline (open question from the future-branch roadmap, Section N).

5. **Deferred issue cleanup**
   - D-001 MAVLink Adapter README State Payload Drift is closed.
   - D-002 Contract Hash / Release Hash Follow-Up is closed.
   - D-003 Future Semantics Require Versioned Implementation Branches is
     closed (2026-07-08, maintainer decision after S1-11B): the
     future-branch roadmap artifact, extension registry, and promotion
     evidence bar now track future branch work individually. The deferred
     issue register is fully closed.
   - D-007 Encoding Negative Validation Gap is closed.
   - D-008 Conformance Class Manifest Missing is closed.
   - D-004 is closed as removed from ZMeta scope by S1-10P.
   - D-009 v1.0/v1.1 Observation Extension Boundary Needs Explicit Tests is closed.
   - D-010 Profile Precision / Quantization Policy Floors is closed.
   - D-011 Crosswalk TAKEOFF Mention Cleanup is closed.
   - D-012 Formal Release Tag, Signature, and Attestation Packaging is
     closed.
   - D-013 Timing-Freshness Negative-Age Clamp is closed.
   - D-014 Compact Codec Unknown Integer Payload Keys is closed.

6. **Later versioned semantic branches**
   - Markings/releasability.
   - Integrity, signing, anti-replay, mesh trust, and quarantine.
   - MODEL_STATUS / assurance and drift monitoring.
   - UAS identity and behavioral trust.
   - Track lifecycle extensions.
   - Coalition export and cross-domain guard metadata.
   - Compute status and degraded runtime behavior.

7. **P1-06 deferred maintainer decisions (recorded 2026-07-15; queued so
   they do not age out of prose)**
   - Name and link the fielded deployments in the README "ZMeta In The
     Field" section, or keep it generic (disclosure/positioning call).
   - RF golden sample pairs: sanitized real captures (Kraken DOA CSV window,
     Moth serial lines, small SignalHunter PSD `.bin`) plus expected ZMeta
     output as `samples/` input->expected pairs for the RF adapters —
     requires maintainer-supplied sanitized field data.
   - `mavlink_to_zmeta_template.py` rename to match its Production status —
     Class B follow-up (governed `must-pass.jsonl` + `conformance_classes`
     references + release-manifest regeneration).
   - Physical `docs/process/` move for the dated s1_*/r1_* records —
     optional; blocked-ish on 5 governed references in
     `conformance/conformance_classes.yaml`; the `docs/README.md` index
     covers the need for now.
   - Mechanical conformance-claim generator (`tools/make_claim.py`) —
     touches claim governance; follow-up if wanted.

## Guardrails for Next Prompt

- Do not change schemas unless the prompt explicitly moves into a schema implementation item.
- Do not recompute formal release/tag hashes until a release packaging task explicitly asks for it.
- Do not make v1.1.0 or future concepts valid under `zmeta_version: "1.0"`.
- Keep profile projection checks pairwise and external to v1.0 event payloads.
- Keep registry work plan-first and branch-scoped. A registry entry alone does
  not make vocabulary valid.
- Keep conformance class work evidence-driven. A class record alone does not
  prove an implementation claim.
- Document any newly discovered issues in the deferred issue register in `docs/zmeta_refinement_worklog.md`.

## Verification State

Most recent validation: the v1.1.18 release validation record lives
in `release/VALIDATION_REPORT_v1.1.18.md` (v1.1.17's is the prior
generation) and the worklog v1.1.18 cut/publication entry
(`docs/zmeta_refinement_worklog.md`); the v1.1.15 and v1.1.14 records live
in their respective `release/VALIDATION_REPORT_*.md` files and worklog
entries. The single block below is retained as the most recent full command
inventory recorded in this handoff; older validation generations were
pruned from this rolling brief and live in git history.

Validation command inventory **as recorded for the S1-26 v1.1.12 release
preparation (2026-07-08, Windows, Python) — historical; superseded by the
newest `release/VALIDATION_REPORT_v*.md`.** Keep it labelled that way: the
command set is *not* unchanged in shape since v1.1.12. It gained
`tools/compute_contract_hash.py` and
`tools/validate_conformance_classes.py --verify-contract-hash` at v1.1.14
and dropped `tools/validate_future_roadmap.py` at v1.1.16, so the block
below is a shape from three releases ago, not a per-release template.
**Take the inventory for a live cut from the most recent
`release/VALIDATION_REPORT_v*.md` and `RELEASE_CHECKLIST.md`, not from
here.** Reproduce the divergence with:

```bash
for v in 13 14 15 16; do f=release/VALIDATION_REPORT_v1.1.$v.md; \
  printf '%s roadmap=%s contract_hash=%s\n' "$f" \
    "$(grep -c validate_future_roadmap $f)" "$(grep -c compute_contract_hash $f)"; done
```

The results recorded beneath the block are likewise v1.1.12-era
(`465 passed, 110 subtests`; `total=47 passed=47`) and are **not** current.

```powershell
python tools\build_release_manifest.py --release-id zmeta-v1.1.12 --release-name "ZMeta v1.1.12" --release-status formal_release --release-date 2026-07-08 --branch main --update-claims
python tools\validate_release_manifest.py --manifest release\zmeta-release-manifest.yaml
python tools\validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative --precision-policy --release-manifest --release-package --bad-events --adapter-harness
python tools\validate_examples.py --strict --require-all
python tools\lint_policy_risk_modes.py
python tools\validate_future_roadmap.py
python -m pytest -q
python tools\test_workflow_end_to_end.py
python tools\test_workflow_end_to_end.py --profile M --listen-port 5665 --forward-port 5666 --cot-port 5667
python tools\test_gateway_live.py --listen-port 5675 --forward-port 5676 --cot-port 5677
python tools\test_gateway_live.py --profile L --encoding compact --input-encoding compact --listen-port 5695 --forward-port 5696 --cot-port 5697
python gateway\src\gateway.py --profile H --self-test
python gateway\src\gateway.py --config configs\gateway-config.json --self-test
python gateway\src\gateway.py --config configs\edge-config.json --self-test
python tools\check_compat.py --target v1.1.12 --strict <each examples\*.jsonl>
python tools\measure_packet_size.py --file examples\zmeta-profile-L-examples.jsonl --encodings compact --max-bytes 240 --summary-only
python release\build_mvp_packages.py --version v1.1.12
python release\build_release_bundle.py --version 1.1.12
python tools\build_release_package.py --manifest release\zmeta-release-manifest.yaml --output-dir release\package-v1.1.12 --release-id zmeta-v1.1.12 --release-state formal_release --no-signatures --allow-dirty --clean-output
python tools\validate_release_package.py --manifest release\zmeta-release-manifest.yaml --package-dir release\package-v1.1.12
python release\sign_release_artifacts.py --version v1.1.12 --write-checksums --verify-checksums
git diff --check
```

Full kernel conformance result: `projection conformance ok total=37`,
`extension registry ok entries=61`, `conformance classes ok classes=34
claims=2`, `encoding negative ok total=50`, `profile precision policy ok
total=32`, `bad-event corpus ok total=23`, `adapter conformance ok
total=11`, `conformance ok`.
Roadmap result: `future-branch roadmap ok candidates=18
rejected_or_deferred=3`.
Examples result: `overall total=47 passed=47 failed=0 warnings=0`.
Policy lint result: `policy risk mode lint ok`.
Release manifest result: `release manifest ok groups=19 artifacts=70`.
Release package result: `release package ok mode=package`.
Full pytest result: `465 passed, 110 subtests passed`.
Workflow/live gateway results: Profile H/M end-to-end and JSON/compact live
paths passed with CoT wire output; gateway self-tests passed for Profile H,
gateway config, and edge config.
Compatibility result: `issues=0 failed=0 warnings=0` for all eight example
corpora against target `v1.1.12`.
Packet-size result: compact Profile L `min=98 avg=116.0 max=150` under the
240-byte check.
Checksum result: `checksums ok: SHA256SUMS_v1.1.12.txt`.
Docker Compose config rendering was not re-exercised this session (deploy
YAML unchanged since the last validated baseline).
