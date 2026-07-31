# ZMeta Refinement Worklog

## Current Resume Note

- Last updated: 2026-07-31 (external review fact-checked; AIS shipped; A1-02 bar met)
- **2026-07-31 — an outside comparative survey, fact-checked against the stack,
  and the second implementation A1-02 was waiting for.** An external agent
  reviewed ZMeta against SAPIENT, OGC O&M, CloudEvents, C2PA, PROV-O and the
  STANAGs without repository access. Treated as gap exposure rather than
  direction, and every claim about ZMeta that could be checked was checked.
  **The most useful result was a correction to us, not to them.** The survey and
  the previous day's rep independently agreed that ZMeta cannot carry positional
  uncertainty on a track, and the agreement made it feel settled. Both were
  wrong: `ERROR_ELLIPSE_M` is a registered, approved, schema-implemented
  extension allowed on `STATE_EVENT`, on the v1.1.0 branch, with a probability
  level attached. Only the locked v1.0 kernel carries none, which makes it an
  adoption-path question rather than an expressibility gap. Corrected in six
  places. Rule earned: **when an external claim matches your own, that is the
  moment to verify it, not the moment to stop.**
  **Survived the correction:** the v1.0 quality object spells `semi_major_m` and
  the v1.1.0 formal contract spells `semi_major`, which is what the CoT reader
  looks for, so a deployment moving between them gets silence rather than an
  error.
  **The doctrine cycle was renamed S1 to SIM1**, 33 references, because
  `S1-01`..`S1-05` collided with the historical `S1-01A`..`S1-19` work-item
  series including a real completed S1-05. History untouched, verified per file.
  **AIS ingress shipped** (`adapters/ingress/ais/`, 49 tests) and clears the
  A1-02 promotion bar as the second independent implementation. It is the total
  case rather than a variation: every vessel, every message, because a surface
  vessel has no height above the ellipsoid. Measured consequence, pinned in a
  test: a schema-valid AIS observation with a clean identity and an exact
  position projects to zero tracks. A third facet surfaced with it, the
  `geo_status` vocabulary having no token for "horizontally known, vertically
  absent", which is the cheapest of the three A1-02 fixes.
  Also documented from running the ZMeta to SAPIENT round trip: the egress needs
  a caller-supplied `object_map` for non-ULID track ids, and it fills
  `classification[].confidence` but never `detection_confidence`.
- **2026-07-30 (closeout).** Three commits reviewed against the intent that drove
  them, battery verified by hand, records reconciled across every surface. Four
  findings. The CHANGELOG's `[Unreleased]` was empty after three commits of
  user-facing work, which is the fourth instance of records lagging commits and
  the one the v1.1.19 scoring had pre-committed to fixing with a mechanism, so
  `gateway/tests/test_changelog_keeps_up.py` now asserts the description exists
  without judging what it says. X1-02 is past the N=3 lifecycle threshold at five
  instances and still OPEN, which is a rule firing and being overridden by
  judgement; recorded on the entry for the maintainer. Discipline 6 went unmet,
  because no independent panel read this cycle at all. And the repeated
  `recv=722` measurement was considered and cleared: six assertions, all framed
  in the past tense as a corrected defect, so all six stay true.
- **2026-07-30 (later) — `adapters/projector/track/`.** The simulation reps
  earlier the same day found that CoT projects `STATE_EVENT` only, so five clean
  ADS-B observations reached a consumer and produced zero CoT while the example
  corpus produced one because it happens to contain a `STATE_EVENT`. The
  rehearsal passed and the real sensor showed nothing. This closes that for
  sources whose subjects broadcast an identity: the same snapshot now produces
  two tracks on the CoT wire, verified through two live gateway nodes, 9 of 9
  events forwarded with zero diagnostics.
  **A third adapter category.** A projector is ZMeta in and ZMeta out. It
  changes what an event is rather than what format it is in, which is neither
  ingress nor egress.
  **Fusion, not external promotion, and the constraints agree with the
  semantics.** Promotion imports a track another system computed; fusion is a
  track you associated. `policy/lineage.yaml` permits a `STATE_EVENT` to cite
  only `FUSION_EVENT` or `STATE_EVENT` parents, so a state citing an observation
  is refused with `LINEAGE_PARENT_TYPE_INVALID`, and `FusionPayload.members` is
  `minItems: 1`, so a single-member association needs no invented lineage. Both
  were confirmed by running them rather than by reading the policy.
  **The finding underneath the component:** `confidence` is required by the
  kernel on both emitted types and a cooperative broadcast supplies none, so the
  projector refuses to construct without an operator-asserted value. Deriving it
  from `sil` was rejected as an unadjudicated modelling decision.
  **Doctrine log SIM1-05, kernel-shaped:** a v1.0 `STATE_EVENT` has nowhere to
  carry positional uncertainty, so a measured 30 m ADS-B ellipse reaches TAK as
  the unknown-accuracy sentinel. Nothing overstated, a real measurement
  unavailable, and every outer-ring workaround worse than the gap.
  29 colocated tests. Battery 1518 + 1074.
- **2026-07-30 — internal simulation reps while field feedback is pending.**
  The stack was run rather than read: two gateway nodes, the shipped containers,
  the ADS-B adapter on a synthetic `aircraft.json`, the command-evidence loop in
  four cases, a throughput sweep, and an X1-01 reproduction. Every rep carried a
  control defined before the run, which caught three bad measurements of my own
  before they became findings: a false "node did not come up" from a
  block-buffered pipe, a throughput figure that was measuring duplicate
  suppression rather than capacity, and a command corpus in which all four cases
  failed for an unrelated reason (`TIMING_STATUS_MISSING`, because the node had
  not published `TIME_STATUS`).
  **Two real breaks in the deployment path, both fixed and both verified by
  re-running.** The containerized nodes could not deliver anything: `forward.host`
  and `cot.host` are `127.0.0.1`, which inside a container is the container's own
  loopback, so the send succeeds and the datagram is unreadable. Measured at
  `recv=722 fwd=722` in the container against zero on the host. And the two
  Compose files both published `5555:5555/udp`, so the pair could not co-host.
  The Compose files now override both egress hosts on the command line and take
  host-port overrides; the corrected pair was run end to end on one machine, with
  ZMeta JSON arriving on the host's 5556 and CoT on 6969 where both had
  previously measured zero.
  **The finding that matters most for a live event.** CoT projects `STATE_EVENT`
  only, so five clean ADS-B observations produced zero CoT while the example
  corpus produces one because it contains a `STATE_EVENT`. The documented
  rehearsal passes and the real sensor then shows nothing, which is the worst
  available ordering. Recorded as SIM1-03: a fixture chosen to demonstrate every
  feature is not a fixture representative of the input.
  **Confirmed rather than assumed:** X1-01 accepts six of six nonsense
  timestamps including `banana-Z`, with both controls behaving, and those events
  reach a downstream ZMeta consumer with no violation while CoT egress refuses
  them. Left untouched, since it is adjudicated for v1.1.20. Also verified
  working: the command-evidence gate refuses a prohibited-parent citation with
  `LINEAGE_MISMATCH` while an identical command on a clean parent forwards;
  Profile L compact maxes at 150 bytes against the 240-byte budget; contract
  hashes are byte-identical across host and Linux container.
  **Measured for the first time:** 100% delivery at 400 events/s, saturation
  near 422/s, and 44% delivery at 1000/s offered while the node reported
  `drops=0`, because loss above capacity happens upstream of the process.
  **The harnesses were then committed to `tools/sim/` under a structural
  boundary.** The maintainer named the risk in the same breath as the value:
  operational tooling is invaluable and a data standard that accumulates it
  stops being readable as a standard. Recorded as doctrine SIM1-04 with an
  extraction criterion and a trigger, and enforced by
  `gateway/tests/test_sim_boundary.py`, which asserts that nothing governed
  imports or invokes anything under `tools/sim`. The dependency runs one
  direction only, so extraction stays a directory move rather than a refactor.
  That test's own detector-fires check caught a gap in its detector on the day
  it was written: a Windows path in Python source carries an escaped separator
  and the first pattern missed it.
- **2026-07-28 (later session) — v1.1.19 PUBLISHED; documentation voice pass;
  X1-01; two verification gaps closed.** Four strands.
  **(1) The house voice.** An outside reader called the README machine-written.
  40 current-facing files rewritten, 300 em dashes to 1, prose only — verified
  by a structural invariant check (headings, tables, fences, links, code spans
  identical except seven intentional heading rewordings; zero broken links).
  Word count rose slightly, so it was not compression wearing a voice-pass
  label. Scope set by measurement: `docs/README.md` was worst in the repository
  at 52 dashes per 1k words, while `zmeta_professional_overview.md` was already
  clean at 0.5 — the opposite of what the handoff predicted. Governed and
  manifest-hashed files computed and excluded, not judged by eye. Adopted as the
  repo standard in `CLAUDE.md`, which was itself brought to the standard in the
  same commit because a style rule stated in the one file that breaks it is the
  exemplar-violates-its-own-rule defect `adapters/AUTHORING.md` §9 already names.
  **(2) A cross-repo exchange with the fielded consumer.** Two findings raised
  against their deployment (calendar-invalid `ts` silently shifting a CoT
  timestamp; a declared vertical datum read and discarded), each reproduced
  independently on both sides. Their observation about JSON Schema `format`
  semantics then found **X1-01 in our own kernel**: `event.ts` is unconstrained
  beyond a trailing `Z`, and the mitigation named in two adapter READMEs cannot
  work as shipped. Recorded, escalated, not fixed.
  **(3) The cut, made twice.** The first tag was created before the publish-path
  validations had run; `--package-dir` then failed on a package built at the
  prepare commit against a manifest that had moved four hours later. Tagging is
  what makes checksums immutable, so the fix was correctly refused in place and
  the tag was deleted before anything was published. **Rule: run every
  publish-path validation before the tag exists.**
  **(4) Two verification gaps closed by checks rather than checklists** — release
  artifact completeness, and package-mode validation at checksum time. With
  X1-01 that is three instances in one day of a stronger check existing while
  something cheaper ran in its place. Logged as an observation; not minted.
  **Published and verified:** tag on `0eebb43`, 8 assets, CI green, published
  assets downloaded back and re-verified against published checksums.
  Battery 1477 + 1070.
- **2026-07-28 (checkpoint after the session closeout) — three commits landed
  after `b8385ef`, reconciled here.** The closeout is the tier that catches
  exactly this, so the drift is recorded rather than folded in silently.
  **Doctrine log cycle X1 now carries three OPEN entries**, none minted:
  **X1-01** `event.ts` unconstrained beyond a trailing `Z`, sequenced for
  v1.1.20 which is therefore behaviour-changing rather than additive;
  **X1-02** a weaker check standing in for a stronger one; **X1-03** our own
  retirement rule reading silence as death, which inverts for constitutional
  rules — a spec repo is mostly those, so a naive earn-your-place pass would
  remove the wrong half.
  **X1-02 was sharpened by the fielded consumer and the count reached five
  across two repositories.** Their mechanism, better than the three
  coincidences originally recorded: *a check that exists gets substituted by a
  cheaper one that shares its name or its neighbourhood, and the substitution
  survives precisely because the cheaper check passes.* In all five instances
  the cheaper check was green, and the greenness is what stopped anyone asking.
  The detection question — *for each gate we cite, what stronger check is it
  standing in for, and when did we last run that one?* — is deliberately
  unstarted on both sides. Starting a sweep off the back of a closeout is how
  the previous cycle grew an apparatus it then had to apologise for.
  **Three items queued for the v1.1.20 cut**, grouped because being free at the
  next manifest rebuild is the only property they share: X1-01 enforcement, the
  conformance summary legibility line, and a five-dash voice sweep across four
  manifest-hashed files. Doing any now would diverge `main` from the published
  `SHA256SUMS_v1.1.19.txt` for no reader benefit (the A-12 pattern).
  **A false credit was corrected, and it is the entry worth reading.** The queue
  credited the consumer with finding a test constraint that was found here, and
  the wording they *had* proposed breaks both assertions that test makes — so
  the entry carried a fix that would turn a test red under a credit belonging to
  the party who did not supply the constraint. Both halves corrected; the
  replacement line is verified against both assertions rather than proposed.
  The rule, theirs: **credit is a claim too** — verify attributions in your
  favour at least as carefully as ones against you, because nobody else is
  incentivised to. The hazard, named against ourselves: **an invented provenance
  is more convincing than the truth, which is why it survives review.**
  **Downstream:** the consumer advanced their pin to v1.1.19 (reviewed GO,
  additive, full battery green) and reports `ahead 0 behind 0` for the first
  time in this arc. Their hand-mirrored §7.7 denylist is verified as a drop-in
  replacement for `export/policy/semantics.json` and retires when their W1 wave
  closes. Battery unchanged at 1477 + 1070; no hashed artifact touched, so the
  published manifest and checksums stay valid.
- **2026-07-28 — P2 + A1 CYCLE, v1.1.19 PREPARED, CLOSED OUT.** Opened by a
  downstream consumer's pin-advance report (P2-01: a stale README release-focus
  bullet asserting a governance negative that was false in two published tags)
  and closed with the first cooperative-broadcast adapter. Four independent
  panels ran across the cycle; a fifth pass verified the fourth's fixes.
  **What the panels found that internal passes had not:** the content guard
  built for P2-01 did not work — a carried-forward bullet passed both rules
  after two one-word edits — and its replacement had four MAJORs of its own, so
  the rule that tried to judge whether prose was about the right release was
  **removed** rather than patched a third time. What survives is the part two
  panels confirmed sound: a governance sentence COMPUTED from the manifest
  against a committed `release/governed-baseline.yaml` and required verbatim.
  **The first-run lens paid best**, and it is the one I would have skipped: the
  documented two-node path delivered zero events (edge L, gateway H, exact
  profile matching), the "adapter in about an hour" claim hid a 30–90 minute
  producer-authority wall, contract hashes differed between Windows and Linux
  clones **in two independent ways**, and `requirements-dev.txt` produced a
  broken environment. All long-standing — the hash defect dates to the
  repository's first day, 2026-01-17.
  **Churn diagnosis, measured not asserted:** the code converged (no test,
  fixture or conformance expectation regressed across the whole cycle); the
  *claims about* the code did not. Every late-cycle defect was an enumeration
  or measurement written into prose without being run — three separate places
  once carried three different counts of the same thing. The durable rule that
  came out of it: **when a claim enumerates, generate it.** Applied in three
  places now (the governance sentence, the conformance flag list, the dist
  bundle's tool list).
  **ADS-B adapter landed** (`adapters/ingress/adsb/`, 17 tests, 3 fixtures)
  and produced doctrine-log cycle **A1** — three alphabet gaps, each with a
  second instance so no fix accommodates one source, and the shipped `kraken`
  adapter shown to be laundering uncalibrated RSSI into `power_dbm` because the
  spec leaves no third option. Recommendation for all: a declaration, not a
  subtype. **Maintainer adopted playbook discipline 10** (validate before
  hardening; otherwise write the question down) and
  `docs/zmeta_live_test_checklist.md` now carries the deferred questions.
- Quick handoff: `docs/zmeta_refinement_handoff.md`
- **2026-07-27 — P2 CYCLE + v1.1.19 PREPARED.** Opened by a downstream
  consumer's pin-advance review, not by an internal pass. **P2-01**: the
  published v1.1.17 and v1.1.18 trees carry a README release-focus bullet
  held over from v1.1.16 asserting "No schema, policy, or event-vocabulary
  changes" — false for both. Errata recorded; published checksums untouched;
  the currency guard now pins release-focus CONTENT, not only version
  literals (`bdd02a5`, `05106b8`). **Item 10 shipped** (`31ac80e`):
  `export/policy/*.json`, a verbatim JSON projection of the governed policy
  with `tools/export_policy_json.py`, hash-pinned under a new
  `policy_json_export` manifest group — built because that consumer had been
  hand-mirroring the §7.7 STATE denylist for want of any other option.
  **P2-D1** (`508aafe`): seven instances of the vacuous-verification class
  (five test pins, one in shipped tooling, one hand-run probe; the
  audit-evidence case is adjacent to the class, not one of the seven) forced
  playbook discipline
  5 to change — a guard's red demonstration must now be an artifact in the
  repo, not a session act; `gateway/tests/vacuity.py` supports it. The
  **pre-cut whole-range review** then produced **eleven** findings (PC-01..11;
  PC-10 and PC-11 surfaced while fixing the first nine), and an independent
  five-lens panel afterwards found the content guard itself did not work,
  two of them live defects: `adapters/README.md` had pointed at
  `--target v1.1.16` for two releases, and the manifest hashed eleven
  `export/policy` artifacts that NEITHER bundle builder carried. Four
  previously-unpinned current-release literals are now covered, including
  the README title line and the CI workflow's compat target. **PC-09 was CLOSED 2026-07-28** — this sentence recorded it as deferred and
  was missed by the first correction pass, which is the sibling-claim defect
  the second panel named. Original statement: **PC-09 is
  deferred to the maintainer**: the bundles omit `docs/` (and the dist zip
  also omits `conformance/`) though both are hashed, and README directs
  bundle users to governance docs their bundle does not contain — a
  packaging-scope judgement, not a mechanism.
- **2026-07-27 — v1.1.18 PUBLISHED + SESSION CLOSEOUT.** Publication
  facts (previously recorded only in commit messages — the CR-03 class):
  annotated tag `v1.1.18` on release commit `157d41f`, pushed with
  `main`; GitHub release live with all **eight** assets
  (`zmeta-v1.1.18-dist.zip`, edge, gateway, release-package,
  `zmeta-release-manifest.yaml`, `RELEASE_NOTES_v1.1.18.md`,
  `VALIDATION_REPORT_v1.1.18.md`, `SHA256SUMS_v1.1.18.txt`);
  **checksums-only** per the standing signing decision (consistent
  v1.1.5 onward); **CI green on BOTH the tag and `main` runs** — a first
  for this cycle, v1.1.17 having gone red on publish. Post-tag:
  `dd5def7` swept the interruption-affected edits and closed two
  cosmetic defects (a stranded parenthesis in the CHANGELOG entry, a
  stray lint directive in `validators.py`), regenerating
  manifest/claims — so `main` diverges from the published v1.1.18
  assets by design (A-12 roll-forward pattern; **deploy from the tag**).
  **CLOSEOUT (this bullet's commit):** a four-lens read of every
  standing record produced 36 actions, all applied — the AAR gained its
  cycle entry; the doctrine log's lifecycle fired for the first time
  (eight terminal entries archived to one-liners, the legend reconciled
  with the Lifecycle vocabulary, and three tensions at the N=3
  recurrence threshold forced out of indefinite OPEN and put to the
  maintainer: R1-11-07 → HELD-FIRM, R1-11-01/H1-08 and R1-11-14/19
  escalated); the playbook gained a full rule-scoring block (no rule
  scored out; the one-third cap has never fired and is named as a
  watch-item) and the cut tier was amended to a whole-range fresh-eyes
  review on the evidence that three pre-cut findings survived their own
  per-wave attacks; README's release focus and integration notes were
  rewritten (they had carried **v1.1.16 content verbatim** through two
  cuts — invisible to the currency guard, which pins version literals
  only, and the v1.1.16 text is now re-homed under its own heading);
  the CHANGELOG gained the waves it was missing (both CI hotfixes, the
  ARM64/Docker verification, the `cot.config` knob, the quickstart, the
  pre-cut review) plus the v1.1.17 publication note; the cold re-read
  record gained the honest CR-01..30 disposition ledger (10 fixed / 1
  adjudicated final / 8 records-corrected / 2 closed at closeout / 9
  open by design) that existed nowhere before; the audit record closed
  A-13 and A-12/A-29 with the roll-forward pattern named; and this
  worklog took the retention pass below. Battery unchanged and green
  throughout: **1420 + 1070 subtests**, gate all flags exit 0.
  **README pass after the closeout (`a8fcc7b`, `4cb3f3c`, both CI green):**
  front-loaded the value proposition with the three graphics that already
  existed in `docs/img/` but were reachable only from inside the
  professional overview (now linked directly for evaluators); reordered to
  pitch → field evidence → framing → proof → routing → reference; merged the
  two duplicate quickstart blocks; and moved six historical per-release
  Integration Notes sections verbatim to `CHANGELOG.md` — they were 39% of
  the README and sat between the pitch and all reference material (598 → 395
  lines, nothing lost, links and images verified). Added the one-time Windows
  long-paths fix after a test clone into a deep path failed checkout on the
  260-character limit; the repo's own deepest path is 79 chars, so normal
  clone locations have headroom. That test also settled a question worth
  recording: **a fresh clone of `main` runs clean for a new user** — the
  in-repo manifest is regenerated to be self-consistent with `main`, so the
  earlier "deploy from the tag" guidance was over-cautious and is retracted;
  the tag matters only for byte-exact verification against published assets.
- **2026-07-27 (post-publish) — PRE-CUT REVIEW + v1.1.18 CUT.**
  Bounded four-lens fresh-eyes review of the whole post-v1.1.17 range
  (9 commits, 33 files) at release stakes, every finding independently
  verified: **13 confirmed, 0 refuted**, all closed before the cut. Three
  had survived their per-wave attacks: (a) MODERATE — a re-sent clean
  copy of an already-seen parent ERASED its recorded command prohibition
  and the citing command then forwarded with no diagnostic (dedupe is
  time-bounded, the evidence index only cardinality-bounded); closed by
  making recorded labels STICKY (union, never downgrade) plus an
  unadjudicable-shape marker for unreadable risk blocks; (b) MODERATE —
  the new policy block had mode-value and wrapper-key lints but nothing
  checking key NAMES or value TYPES, so a one-character typo silently
  reverted a knob to its permissive default with the lint green; closed
  with a key/type lint; (c) MODERATE — the bladeRF non-finite screen
  missed the bearing-demotion and metadata arms. Also closed: the
  quickstart's wire path was WRONG (edge forwards 5556, GCS listens
  5555 — stock two-node path silently went nowhere), the 4096-cap memory
  rationale overstated what it bounds (ValidationState.events is
  unbounded — corrected in place rather than smuggling a behavior
  change), CoT team-name config could crash the projection, and three
  records claims (the superseded ~40 min figure, a 44-vs-42 commit
  count, a stale handoff block). **v1.1.18 CUT:** currency pass first,
  manifest last; notes + validation report written (incl. the honest
  not-exercised list: real-Pi throughput, TAK display, SAPIENT enclave,
  SITL); bundles + package + `SHA256SUMS_v1.1.18.txt` written and
  verified; battery **1420 + 1070 subtests**, gate all flags exit 0,
  harness 48/48, all lints + roadmap validator clean, packet max
  150/240.
- **2026-07-27 (post-publish) — THE COMMAND-LOOP PAIR LANDED
  (maintainer-directed).** Wave A, attack verdict CLEAN: the
  command-evidence lineage check — `policy/command-evidence.yaml` (S1-15
  risk-model shape, lint-covered) + `validate_command_evidence` +
  bounded ValidationState evidence index (4096, eviction=unresolved) +
  gateway wiring beside the command machinery; refusals reuse
  LINEAGE_MISMATCH / LINEAGE_PARENT_UNRESOLVED / LINEAGE_PARENT_TYPE_INVALID
  (zero minted vocabulary), degrade stamps the S1-15 risk record, bare
  commands default-legal, `require_evidence` strict knob for automations;
  29 red-first pins. Wave B: `docs/zmeta_track_lifecycle_pattern.md`
  expresses the lifecycle + command-grade criteria in current vocabulary
  only; roadmap candidate stays RESERVED with evidence legs recorded
  honestly (n=1 + awaited event); three attack doc-accuracy findings
  fixed same-sitting (preset default boundary stated precisely,
  per-code dispositions, policy enumeration). Banked: H1-08 (wanted
  evidence codes), VW-16 (flood-eviction tradeoff, documented in
  policy), VW-17 (seams). Battery: **1410 + 1070 subtests**, gate all
  flags exit 0, risk-mode lint ok, roadmap validator ok, corpus 51/51.
  Event queue: all agent-executable items DONE — remaining items await
  hardware/access (real-Pi throughput, TAK display validation with the
  cot.config knob, SAPIENT live-enclave, SITL end-to-end).
- **2026-07-27 (post-publish) — VIRTUAL-PI VERIFICATION, THE
  cot.config KNOB, AND THE TWO-NODE QUICKSTART.** Docker build+run — the
  one checklist item the cut could not exercise — is now verified both
  ways: x86 native (stock compose, corpus replayed end-to-end,
  violations=0) and **arm64 under QEMU emulation as the virtual Pi**
  (deps install from wheels, gateway starts, corpus forwarded clean, and
  the schema/policy/semantics/contract hashes are BYTE-IDENTICAL to the
  x86 run — the interop guarantee demonstrated across architectures).
  Platform pins ran on arm64: 98 + 232 subtests green; one failure was
  environmental only (a test wants a scratch dir under the read-only
  deployment mount). Honest scope notes: cbor2 resolves to its
  pure-Python build on that wheel set (the C-extension class stays
  covered by Linux x86 CI), and real-Pi throughput awaits hardware.
  NEW KNOB (outer-ring, red-first pinned in
  gateway/tests/test_gateway_cot_config.py): the gateway config's
  `cot.config` block now passes deployment-asserted projection knobs
  (geopointsrc/altsrc/how, team names, default_ce/le) through to
  zmeta_to_cot — previously the serve loop called the projection bare,
  so no deployment could EVER assert a pedigree and the
  `<precisionlocation>` ellipse detail was unreachable (found while
  writing the quickstart; the TAK-ellipse story depends on it).
  Unasserted stays omitted — the honest default is unchanged.
  `docs/zmeta_two_node_quickstart.md` (advisory) ties it together:
  topology, both node configs, the wire check, hash-match rule, the
  honesty-signal cheat-sheet, and the per-team pre-event checklist.
  Battery: pytest **1381 + 1060 subtests**, kernel gate all flags exit 0.
- **2026-07-27 (post-publish) — BLADERF REFERENCE ADAPTER LANDED
  (the maintainer-directed "NEXT" item, timed).** The merged
  `edge-comms-bladerf` pack now has its runnable reference
  implementation at `adapters/ingress/bladerf/`, authored along the
  documented path exactly (AUTHORING.md end-to-end -> pack primaries ->
  contract 3.4/4.4/4.8/6/7.1/7.3/7.4 -> sibling references), as the
  repo's receipt that the authoring guide takes a new RF sensor from
  recorded output to a verified adapter in one sitting. **Timed receipt
  (commit `71f8e18`), orchestrator external wall-clock: **~13 min
  zero-shot authoring** (12:48->13:01), **~25 min full verified cycle**
  to 13:13 (the agent self-estimated ~40 min of effort; the external
  wall-clock is the honest receipt). Then an
  independent adversarial attack (verdict CLEAN on the semantics; one
  value-honesty finding — finite-blind geo/feature guards) and
  same-sitting hardening.** The guide's "run this guide as a checklist"
  step did real work: the in-sitting review caught four fail-closed
  gaps before landing — an unmapped alternate `event.ts` source (the
  `timestamp` rendering could rescue a missing `timestamp_ms`; now
  mapped-source-only), crash-not-refusal arms (non-numeric/boolean
  `timestamp_ms`, non-dict `metadata`, non-numeric geo), a
  `platform_id` TypeError where a refusal belongs, and `str()`
  coercion of caller lineage ids (now pass-through, schema rejects).
  The `quality.geo_status AVAILABLE/UNAVAILABLE` convention was
  verified against the SAPIENT reference + v1.1.0 quality vocabulary
  before adoption, not assumed. Non-finite values are screened at the
  boundary (NaN/inf SNR refuses the event; a non-finite coordinate
  refuses geo; NaN `timestamp_ms` refuses), red-first pinned. Landed
  together (Class C set): module + README (both declared conventions
  documented: FFT bin-width `bandwidth_hz`, native-bearing demotion) +
  67 colocated tests (both capture pairs reproduced exactly; one
  refusal per schema-required field), 8 `bladerf-` harness fixtures,
  README table row (Reference legend widened to real-capture corpora),
  pack README cross-link, manifest/claims regenerated under the current
  identity (A-12 interim pattern; next cut re-baselines). Evidence
  (each run where it could fail): `pytest adapters/ingress/bladerf -q`
  = 67 passed; `tools/validate.py --profile H --strict` on emitted
  events = 2/2; `tools/check_compat.py --target v1.1.17` = 0 failed (2
  deliberate `timing_quality_fallback` warnings); `tools/check_adapter.py
  --fixtures` = lint + harness 48/48; kernel gate all flags exit 0;
  examples 51/51; full pytest **1377 + 1060 subtests**;
  `git diff --check` clean. Adapter core + fixtures committed as
  `71f8e18`; this registration set (README row, pack cross-link,
  manifest/claims, records) rides the follow-up commit — whether it
  cuts is the maintainer's call per the commit=release policy.
- **2026-07-27 (post-publish, later) — KERNEL-ADJACENT RESIDUALS CLOSED
  (VW-01, H1-07).** Scoped wave per the playbook (fix + attack per item).
  VW-01: naive-ts refused at `_parse_utc_z`/`_format_utc_z`; the attack
  pass caught the first fix converting a loud crash into silent
  participation in a PRE-EXISTING fail-open (any unparseable recorded
  TIME_STATUS made freshness silently pass for that source) — repaired at
  the record seam: unorderable statuses are never recorded, the source
  keeps the loud MISSING arm. H1-07 → CHANGED: `_decode_cbor_envelope`
  runs the fail-closed value-model scan on the plain-`cbor` envelope on
  both backends, pre-decode depth bound probed (never version-guessed);
  two legacy pins updated to clause semantics with their locatability
  property preserved. Banked: VW-14 (event-side silent freshness arm +
  env-dependent `date-time` gate strictness), VW-15 (auto/compact-branch
  bare pre-decode, resource-knob parity, scanner-absent combo, three
  inconsistent naive-datetime doctrines repo-wide). Battery: pytest
  **1310 + 1060 subtests**, kernel gate all flags exit 0. NEXT (maintainer
  direction): the bladeRF reference adapter, timed, per AUTHORING.md.
- **2026-07-27 (post-publish) — v1.1.17 PUBLISHED; two CI hotfixes; CI
  GREEN.** Release published with explicit maintainer direction (tag on
  `7302073`, eight assets, checksums-only). The release commit's CI — the
  first CI contact for the entire 42-commit held range — caught two
  platform-dependent defects no local run could see (local cbor2 is
  pure-Python on 3.14; the runner's is the C extension): (1) the compact
  ENCODE path handed hostile-depth structures to the backend before
  refusing — segfault on C-extension installs; fixed in `8175aa7` (depth
  guard in the iterative scan, sentinel-pinned pre-backend refusal;
  shipped gateway/edge bundles unaffected — they bundle and prefer
  zmeta_cbor; noted honestly on the GitHub release body, assets
  untouched); (2) the v1.0 byte-identity pin hashed raw checkout bytes,
  which differ under autocrlf — fixed in `1fb6fa3` (LF-normalized digest).
  The A-13 anchored-totals pin also fired exactly as designed the moment
  the push moved origin/main, catching three remaining unanchored figure
  sites — anchored in `8175aa7`. The repo manifest again diverges from the
  published v1.1.17 manifest asset (hotfix regeneration; published
  checksums immutable; next cut resolves — the documented A-12 pattern).
  NEXT: the event-readiness queue (bladeRF adapter as the timed
  hour-proof, Pi/Docker verification, two-node quickstart, TAK display
  validation, UxS-roadmap command-evidence lineage + track-lifecycle +
  SITL gate).
- **2026-07-27 (later) — GOVERNED WAVES, RECORDS WAVE, v1.1.17 CUT PREPARED
  (HELD).** The two adjudicated governed waves landed with attack passes:
  `40be64a` (compact fail-closed value-model clause — no tags incl. 28/29,
  declared nesting max 64, declared expansion bound 2^20; spec-sync-pinned;
  doctrine 02/03/18 → CHANGED) and `2a00ef2` (TIME_STATUS.state enum in
  v1.1.0, Class B; B-04 now schema-visible; v1.0 pinned byte-identical;
  doctrine 15 → MINTED). Records wave `ae42a4d` closed A-13 (figures
  anchored to literal base `09118b3`, currency pin extended) and corrected
  the six frozen-record counts (CR-04/13/14/15/24/25) with dated notes;
  health-wave verifier candidates banked as VW-01..13. Cut prep: manifest
  rebuilt under `zmeta-v1.1.17` with explicit provenance and claims
  update, release notes + validation report written, dist/edge/gateway
  bundles + release package built, `SHA256SUMS_v1.1.17.txt` written and
  verified, doc-currency re-baselined (README, installation guide,
  overview, release/tools READMEs, guidance docs, CI target, compat
  TARGETS, manifest pins, signer example). Battery at hold: kernel gate
  all flags exit 0, examples 51/51, pytest **1284 + 1051 subtests**,
  packet check max 150/240, checksums verified. **PUBLISHED 2026-07-27 with explicit maintainer
  direction after review**: `main` pushed (`09118b3..7302073`, the full
  42-commit held range), annotated tag `v1.1.17` on `7302073`, GitHub
  release live with all eight assets incl. `SHA256SUMS_v1.1.17.txt`.
  Checksums-only. Not exercised locally: Docker build/run; CI runs
  post-push (status recorded at publish in this note's session).
- **2026-07-27 — HEALTH FIX WAVE + ADJUDICATION (resume session 2).**
  Maintainer adjudicated four decisions in-session (doctrine log
  "Adjudication pass"): governed vocabulary = the event model only;
  compact fail-closed clause approved (own governed wave pending);
  `TIME_STATUS.state` Class B enum approved for the next cut; round-3
  register loss recorded as final. Fix wave per the playbook — nine
  disjoint-surface clusters, red-first pins, an independent attacker per
  cluster, a verifier-driven completion round — commits
  `25bb5fa`/`ede9bb6`/`dcabcc8` plus this records commit. Closed: CR-01
  and CR-02 (both MAJOR, both live in published v1.1.16), the banked
  `_parse_utc` MAJOR as a CLASS (CoT/JREAP/SAPIENT twins; unparseable AND
  gate-clean naive shapes refuse — "1969-12-31Z" parses naive on Python
  3.14 and used to localize silently), CR-05/06/08/09/10/11/12/16, the
  unblocked R2-30 skip token, and the R1-11-16 vocabulary lint (which
  would have caught CR-05/06 mechanically). Introduced-at-MODERATE+
  across the whole batch: 1, fixed same-day — the one-third cap held.
  Battery: kernel gate all flags exit 0, examples 51/51 strict, pytest
  **1262 passed + 1021 subtests**, vocabulary lint ok. Six new tensions
  banked (H1-01..06); the audit record's falsified "Refuted 3/3" ts
  disposition carries a dated correction. **NEXT: the records wave (A-13,
  CR-13/14/15/23/24/25, verifier register candidates), the compact-clause
  governed wave, then the v1.1.17 cut.**
- **2026-07-26 — R1-11 resume queue P1 COMPLETE (refresh + cold re-read);
  next is P2, the maintainer's doctrine adjudication.** Battery re-verified
  live (kernel gate all flags exit 0, examples 51/51 strict, pytest 1200
  passed + 1021 subtests). `7eaea97` closed the doctrine-log numbering
  collision (the disposition addendum had restarted at 14; renumbered
  15–21, cross-references swept — the log holds **21** tensions, and the
  adjudication clusters are now R1-11-09/15/16 (governed-vocabulary
  boundary) and R1-11-02/03/18 (compact-mapping clause)). `e524c8c`
  recorded the cold re-read: nine independent lenses (the six playbook
  wave surfaces plus commit-truth, vacuous-pin, and half-applied-fix),
  adversarial verification of every candidate, three-lens panels for
  MAJORs — 48 candidates, 47 confirmed, 1 refuted, merged to **30
  distinct findings in `docs/r1_11_cold_reread_findings.md`, RECORDED not
  fixed** (the round-3 stop decision and the P2 bottleneck stand).
  Headlines: **CR-01 MAJOR** — SAPIENT ingress, a negative declared
  `maximum_latency` *narrows* `est_error_ms` (sign member of the
  R1-03/B-03 class, unswept, **also live in published v1.1.16**);
  **CR-02 MAJOR** — CoT egress stamps the horizontal ellipse `semi_minor`
  into `point@le`, fabricating vertical certainty (**also live in
  v1.1.16**); **CR-03 MAJOR** — the 44 open sub-MAJOR and round-3 attack
  findings are recorded nowhere in the tree (the fix-pass register ends
  at round 2), so queue item P4 must reconstruct its own input; **CR-04**
  — the cycle-wide "no governed artifact touched / no `reason_code`
  minted" claim is false as written (three additive reason codes were
  minted by the early waves) — the live handoff surface is corrected; the
  frozen records keep their count/claim defects banked (CR-13..15,
  CR-23..25) for a scoped records wave. Completeness critic's top gap:
  the ~7.8k lines of new test mass were deep-read below 15% — candidate
  surface for the next scoped wave. Process note (maintainer direction
  2026-07-26): ultracode stays on with lean-vs-heavy judgment delegated —
  heavy fan-outs reserved for passes where independent eyes are
  load-bearing (fresh audits, fresh-eyes re-reads, pre-cut verification);
  records work and scoped waves run lean.
- **HOLD (2026-07-22): the R1-11 cycle is COMPLETE and FROZEN pending a
  fresh full-stack audit.** Held range `118f0b9`..`HEAD` — the entire
  cycle, none of it pushed (`git log --oneline origin/main..HEAD` gives
  the live set; last code commit `6ea9888`, anything after it is records
  only). Tree clean; nothing pushed, tagged, or signed, so no consumer
  has seen any of it and the published v1.1.16 assets remain the only
  downstream truth. The maintainer's
  release decision stays OPEN behind that audit. **The cycle was
  executed across four sessions broken by usage limits, plus a model
  switch and a full chat reset — the interruption ledger, the residue
  checks that were run, and a targeted checklist for the fresh audit are
  recorded in `docs/r1_11_full_stack_audit.md` ("HOLD state" and
  "Execution continuity").** The single most important item there:
  interruption 2 left a **half-applied two-layer fix** (compact codec
  layer applied, gateway backstop layer missing) that looked complete
  and was caught only because the resuming session read the working diff
  instead of trusting the narrative — **resume from the tree, never from
  the transcript.** **What was touched: measure it live with
  `git diff --shortstat origin/main..HEAD` — no total is frozen here,
  because the range grows with every record commit and the frozen figure
  was falsified by the commit that wrote it (A-13); at the fresh audit's
  anchor, `git diff --shortstat 09118b3..eb41794` = 77 files,
  +4920 / −392, over 18 commits. The
  record's "What was touched — validation inventory" maps it (governed
  surfaces first: `schema/`+`policy/` took only three additive
  `reason_code` enum entries, `spec/semantics-contract.md` took +6/−1 in
  §5.3; the release manifest and conformance claims are BUILD OUTPUTS,
  verify by regenerating and diffing, not reading), and "Order of events"
  gives the chronology with interruption points marked. The audit's FIRST
  deliverable is "Step 0" in that record: a finding → code → test map,
  17 rows (`V1-01`..`V1-03`, `V2-01`..`V2-14`), derived from the code
  rather than copied from the record — it does not exist yet, every later
  check depends on it, and a row that cannot be filled is a live
  finding.**
- Current state (2026-07-22, fifth closeout): the **R1-11 cycle is
  COMPLETE through both post-fix verification passes.** The fix pass
  (seven waves) and verification pass 1 (`d955cd0`) were followed by
  verification pass 2, which closed **14 findings — 2 MAJOR (a
  process-killing crash class and a cross-backend laundering/interop
  hole), 7 MODERATE, 5 MINOR**; the findings record
  `docs/r1_11_full_stack_audit.md` now carries the disposition, the
  cycle outcome, and both verification passes. Final battery: kernel
  gate all flags (bad-events 29, harness 40), examples 51/51 strict,
  packet size compact max=150 of 240 (unchanged), pytest **785+316**
  zero failures, `git diff --check` clean. **Post-release divergence
  record (per the AGENTS.md rule): the fix-pass and verification-pass
  commits regenerate the manifest and claims under the v1.1.16
  identity, so current main diverges from the published v1.1.16
  SHA256SUMS manifest/package pins; published checksums stay
  immutable; resolution is the next release cut.** NEXT: **a fresh
  full-stack audit over the held cycle** (targeted checklist in the
  findings record: partial-application residue, commit-truth across the
  interrupted boundaries, the new guards as unreviewed code,
  blind-by-construction self-checks, record counts, doc-currency
  judgement calls), THEN the maintainer release-cut decision (v1.1.17
  recommended — the cycle includes a MAJOR honesty fix, two MAJOR crash
  classes, a MAJOR cross-backend laundering/interop hole, and two
  Class B vocabulary batches). **Carry-forward lesson: a fix has
  introduced or exposed the next defect more than a dozen times across
  R1-10, the R1-11 fix pass, and both verification passes — the
  verification pass produced most of this cycle's real findings and
  should stay mandatory after any pass touching honesty-critical
  paths. Two sharper forms earned in pass 2: a new guard is itself
  unreviewed code (two fresh pins reproduced the exact defect class
  they were written to prevent), and a self-check running the same
  machinery on both sides is blind by construction (V2-09).**
  Prior closeout state follows.
- Previous state (2026-07-21, first closeout): the SAPIENT lane is
  FULLY CLOSED — P1-07 mapping pack + reference adapters, the end-to-end
  wire validation against official Dstl tooling (PASSED; ULID findings
  fixed pre-release), and **v1.1.15 PUBLISHED** (release commit
  `bbd4c89`, publication record `f1c249a`, tag pushed, GitHub release
  live with eight assets marked Latest, CI green, checksums-only).
  Tree clean and in sync with origin at closeout.
  **Maintainer decision 2026-07-21 (closes the 2026-07-17 open item):
  a FULL fresh stack audit — not a scoped one — is the NEXT WORK ITEM
  (R1-11), to be run safely in a fresh session before any queued
  backlog resumes.** Inputs and method precedent are recorded in the
  handoff Next Work Queue item 1. Queued behind R1-11: the v1.1.0
  adoption-decision session (holding fielded command-loop evidence
  context and the SAPIENT evidence legs), the five deferred P1-06
  maintainer decisions, PR #4 status, and signing.
  Lane lessons worth carrying into R1-11 (recorded here so the audit
  can use them as lenses, per the R1-09/R1-10 pattern): (1)
  counterparty-official end-to-end validation catches a defect class
  that colocated tests AND adversarial code review both missed —
  wire-level id-format discipline (the ULID findings) surfaced only
  against Dstl's own validator; prefer official-tooling validation
  for every future mapping pack. (2) The release-currency machine
  check caught stale installation-guide pins mid-cut — the
  R1-10-built checking machinery is earning its keep. (3) The
  session-limit interruption recovery (resume with verify-and-complete
  prompts + a dedicated interruption-integrity review) left zero
  half-done state, twice validated as a working pattern.
- R1-11 execution continuity + HOLD (2026-07-22): the cycle ran across
  **four sessions broken by usage limits**, plus a mid-cycle model
  switch (Fable 5 → Opus 4.8, twice, from safeguards spuriously
  flagging routine work on this defensive ISR codebase) and one **full
  chat reset**. Recorded because interrupted work is its own defect
  surface. (1) The first post-fix verification audit was killed with
  **1 of 6 slices complete** — that lone slice had already found two
  defects the fix pass introduced; on resume its result was re-read
  rather than re-run, both were independently reproduced before fixing,
  and a third surfaced during the fix (→ `d955cd0`). (2) The next limit
  hit **mid-edit on a two-layer fix**, leaving the compact codec layer
  applied and the gateway backstop layer missing, uncommitted. **This
  is the dangerous class: a partial fix looks finished** — syntactically
  complete, imports clean, reads as deliberate. It was caught only
  because the resuming session started from `git status` and the real
  working diff. **Resume from the tree, never from the transcript.**
  (3) After the chat reset the recovering session had zero in-context
  memory and rebuilt state purely from the repo (git log, working diff,
  findings record, worklog) with the prior transcript supplied as data;
  everything in `6ea9888` was produced under that reconstruction.
  Residue checks run at freeze: full working-diff read before any new
  edit (caught the partial fix), full battery after every change set,
  finding list re-derived from audit output rather than memory,
  counts re-measured, UTF-8/mojibake scan on every edited doc (clean,
  no BOM), manifest regenerated and re-validated after every code
  change. **HOLD: held range `118f0b9`..`HEAD` (entire cycle, last code
  commit `6ea9888`), tree clean, nothing pushed/tagged/signed — a fresh
  full-stack audit runs before any release decision, with a targeted
  checklist in `docs/r1_11_full_stack_audit.md`.** This is the third validation of
  the interruption-recovery pattern (R1-09, R1-10, now R1-11), and the
  first under a full context reset — the pattern held, but only
  because state was reconstructed from artifacts rather than narrative.
- R1-11 post-fix verification passes (2026-07-21/22): **BOTH COMPLETE.**
  The R1-10 lesson — the fix pass is itself an audit surface — paid out
  twice more. Pass 1 (`d955cd0`) found three defects wave 1 had
  introduced or caused: (V1-01 MAJOR crash) the recovery path guarded
  only the FIRST encode, and because the diagnostic inherits the
  original's `event_id` as `original_event_id`, an event whose
  `event_id` was the unrepresentable part poisoned its own diagnostic —
  with `main()` catching only `KeyboardInterrupt`, one packet could kill
  a compact-output gateway for every producer; fixed with a fallback
  ladder ending at the `UNKNOWN` sentinel. (V1-02 MODERATE laundering)
  `verify_representable` compared an in-memory key remap that PRESERVES
  OBJECT IDENTITY, and Python container equality short-circuits on
  identity, so NaN — not equal to itself — passed verification and
  reached the wire with no RFC-8259 form; verification now runs through
  the real serialization boundary. (V1-03 MODERATE over-refusal) the
  byte-wise check refused SCHEMA-VALID events — **both bladeRF
  real-capture fixtures, this repo's own v1.1.16 corpus, were refused by
  compact egress over `.876Z` vs `.876000Z`, the same instant.** Wave
  1's tests used only whole-second timestamps. The check now recognizes
  exactly the two declared normalizations (UUID hex case; timestamp
  formatting at ms resolution); the `.000Z` refusal pin deliberately
  flipped to a normalization, with the sub-millisecond case replacing it
  as the honest refusal pin.
  Pass 2 (seven slices, 24 agents, every finding adversarially refuted
  before acceptance; 2 refuted) opened with these, and the second sweep
  below extended it to **14 findings total — 2 MAJOR, 7 MODERATE,
  5 MINOR**: (V2-01 MAJOR crash) the ladder catches only
  `CompactUnrepresentableError`, but the codec itself raises
  `OverflowError` (int ≥ 2**64), `ValueError` (nesting past CBOR decode
  depth — pass 1's real-serialization decode ADDED this path), and
  `OSError`/`RecursionError` on schema-valid input, each escaping and
  killing the process; fixed at two layers (codec converts its own
  failures; receive loop gained a per-datagram backstop) with the
  backstop's scope pinned by test — `recvfrom` stays OUTSIDE it so a
  dead listener still terminates, and `except Exception` never catches
  the `SystemExit` that reports an unusable config, so resilience never
  becomes concealment. (V2-02 MODERATE crash) `_find_forbidden_key`
  recursed, so deeply nested schema-valid JSON killed the gateway at
  INGRESS before egress on any encoding; now iterative breadth-first.
  (V2-03 MODERATE laundering) the R11-04 non-finite drop ran on 1 of 5
  SAPIENT ingress paths; a structural pin written to stop the guard
  drifting then showed **"five paths" was itself undercounted — there
  are SIX vendor-block sinks**, the missed one being the PLATFORM_STATUS
  event's verbatim `power` block (a non-finite `voltage` reached the
  wire even though `battery_pct` derived from that same block was
  guarded); all six now guard at the POINT OF USE, not once earlier in
  the function (the detection path dropped first and then assigned
  `vendor_ext["colour"]`, safe only by string-guard accident), with the
  invariant pinned by a source-level test. **Fixing this surfaced a
  second hole in the same helper — three cycles deep on this one class
  now** — dropping a bare non-finite LIST ELEMENT silently re-indexed
  positional numeric arrays (`[1.0, NaN, 3.0]` arriving as a clean
  two-element array); a non-finite element now drops the containing key. (V2-04 MODERATE
  enforcement) the R11-05 lint covered only per-producer rules, not the
  GLOBAL promotion block where most enforcement keys live — the same
  failure mode one block over — and additionally blessed per-producer
  overrides of global-only keys that enforcement never reads
  (`always_reject_loop_risk: false` on a producer changed nothing);
  **stress-testing the new lint caught it committing the same sin** —
  present-but-mistyped `degrade`/`quarantine`/`use_limits` sub-blocks
  were skipped, and a non-mapping there reverts the action to its
  built-in default, so they now fail (absence stays legal).
  (V2-05 MINOR over-refusal) compact epoch-ms routed through float
  seconds, landing 1 ms off for a date-banded fraction of schema-valid
  timestamps (480 of 8000 swept) and raising `OSError` on Windows for
  out-of-range instants; now exact `timedelta` integer arithmetic.
  (V2-06 MINOR honesty) non-string `ts` raised `AttributeError` past the
  documented None-refusal in both SAPIENT egress adapters, and the
  compact drop reason was the lone lowercase entry in a
  `SCREAMING_SNAKE` `drop_reasons` vocabulary that operators filter on.
  (V2-07 MINOR checking machinery) the overview currency guard matched
  one literal phrasing (`currently vX.Y.Z`) — shaped around the sentence
  the last regression happened to use — so `as of today, v1.1.9` / `pin
  to release v1.1.14` passed clean; replaced with a phrasing-independent
  superseded-release check, and **the first cut of the replacement was
  itself wrong** (lookahead rejected any version ending a sentence, the
  exact target shape), so the matcher now self-tests both directions.
  (V2-08 MINOR release machinery) `RELEASE_NOTES_TEMPLATE.md` still
  shipped the retired "D-003 remains roadmap-planned" line into every
  packaged note four releases after closure — R11-14 fixed the
  *validator* enforcing the claim but not the *template* emitting it;
  the same claim had two producers.
  A second nine-lens sweep over the RESULTING FIXES (85 agents, 29
  findings surviving adversarial refutation of 75 judged) added six
  more, headlined by **the most serious finding of the cycle: (V2-09
  MAJOR laundering/interop) compact representability depended on WHICH
  CBOR LIBRARY WAS INSTALLED.** The mapping's integer limit was left to
  the backend; `zmeta_cbor` correctly refuses an integer outside
  `[-(2**64), 2**64-1]`, but `cbor2` silently emits a bignum tag that a
  `zmeta_cbor` consumer decodes as raw BYTES — two conforming nodes
  disagreeing about the same event's meaning over a local install
  detail. **The round-trip self-check is structurally blind to this**:
  it encodes and decodes with the same library, so the corruption only
  appears on the receiving node. The codec now enforces the range
  itself on every backend, boundary pinned exactly, both regression
  tests run against both backends. Also: (V2-10) `_same_instant`
  compared two values already truncated identically at microseconds, so
  a 100-nanosecond instant compared equal to its ms round-trip while
  the codec claimed to refuse truncation; (V2-11) `_format_ts` crashed
  the PUBLIC decode path on a hostile epoch-ms value, outside the
  encode-side guard; (V2-12) four docs carry the identical pinned
  "Current release context" header but only the overview was guarded,
  so **three sat five releases stale** — the family is pinned now, plus
  a test that the pinned list still names every carrier; (V2-13) the
  package builder copied the notes TEMPLATE verbatim as each package's
  `RELEASE_NOTES.md` and nothing read its content, so the published
  v1.1.16 package ships "ZMeta Release Notes Template" with placeholder
  provenance beside `release_state: formal_release` while the real
  notes never entered the package (builder `--release-notes` +
  validator `RELEASE_PACKAGE_NOTES_PLACEHOLDER` + checklist step;
  published checksums untouched, effective next cut); (V2-14)
  `spec/release-signing-attestation.md`, a manifest-hash-pinned artifact
  validated every release, still asserted "D-003 remains the roadmap"
  for an item closed at v1.1.12, plus assorted stale literals — the
  compat CLI test's "current release target" now derives from the
  manifest rather than a pin.
  Live re-probe at close: the gateway survives every poison class
  (2**64 int, 300-deep nesting, 20k-deep raw JSON) with honest
  `ENCODING_UNSUPPORTED`/`SCHEMA_INVALID` diagnostics on the wire, the
  uppercase-UUID + millisecond-ts event forwards normally, and normal
  traffic still flows afterward — process alive throughout. Validation:
  kernel gate all flags (bad-events 29, harness 40), examples 51/51
  strict, packet size compact max=150 of 240 unchanged, pytest
  **742+237 → 785+316** zero failures, `git diff --check` clean.
  Governed regeneration: manifest + claims under the v1.1.16 identity
  (divergence record above continues to apply).
- R1-11 fix pass (2026-07-21): **ALL SEVEN WAVES COMPLETE** under the
  maintainer directive "give me a list... then lets work down that
  list" (R11-24 bladerf disclosure inventory cleared: "the bladerf
  stuff is good"). Wave -> commit map: (1) `74d92e1` compact
  fail-closed (R11-01 MAJOR; verify_representable self-check, gateway
  ENCODING_UNSUPPORTED in-band diagnostic, spec Scope section, CLI
  refusal; live UDP re-probe shows the diagnostic on the wire where
  the laundered STATE used to be); (2) `88b527e` SAPIENT adapter
  honesty (R11-02/-03/-04/-12/-20; sapient suites 117 -> 133 — the
  new NaN test caught a residual the audit probes missed:
  native_classification carried NaN verbatim, poisoning RFC-8259
  serialization; fixed with _drop_non_finite on native blocks);
  (3) `e3203ad` signalhunter no-lock + three-template loop_status
  (R11-06/-07; harness fixtures now pin the message-carried verdict
  VALUE); (4) `545fe0b` checking machinery (R11-05/-08/-09 + the
  SHA256SUMS immutability pytest pin; bad-events 27 -> 29, harness
  self-lints its corpus); (5) `c1eb9d0` machine-encoded semantics
  (R11-13/-21 + R11-04 validator side; Class B batch
  BEARING_FRAME_UNLABELED warn + NON_FINITE_CONFIDENCE fail, both
  enums, sanctioned); (6) `33230af` release machinery
  (R11-10/-14/-16; root-cause find during the fix:
  validate_release_package MACHINE-ENFORCED the stale "D-003 OPEN"
  claim — "known_open_issues must include D-003" — which is why it
  survived four releases; replaced with an attestation-mirrors-
  manifest check); (7) `05ad9a8` doc currency + teaching
  (R11-11/-15/-17/-18/-19/-23/-25; currency test extended to the
  body/worked-command surfaces that escaped one-line pins; contract
  5.3 last_sync_ts reading rule, Class B). Wave 1 additionally
  recorded the ENCODING_UNSUPPORTED Class B addition; wave 1's
  strict round-trip equality also surfaced the honest ".000Z"
  ts-normalization refusal case (pinned in tests). Not fixed by
  design: R11-22 (governed deviation, registration entry point stays
  queued in handoff 1a); R11-24 (cleared). **Divergence record (per
  the AGENTS.md rule this pass added): waves 1/3/4/5/6/7 regenerate
  the manifest/claims (and waves 6/7 the release package) under the
  v1.1.16 identity — current main diverges from the published
  v1.1.16 SHA256SUMS manifest/package pins; published checksums are
  immutable; resolution is the next release cut.** Validation at
  every wave boundary and final: kernel gate all flags green,
  examples 51/51 strict, pytest 687+172 -> 742+237 zero failures,
  git diff --check clean. Post-fix verification audit and the
  release-cut decision follow.
- R1-11 (2026-07-21): **FULL STACK AUDIT COMPLETE — findings record
  `docs/r1_11_full_stack_audit.md`, maintainer disposition RECORDED
  (fix pass directed and executed; see the fix-pass entry above).**
  Audited tree `09118b3`, strictly read-only. Method: green baseline
  (kernel gate all flags, examples 51/51, pytest 687+172 zero
  failures), then seven independent finder lenses (SAPIENT pack
  honesty; bladerf/external-fixture discipline + harness
  expressiveness; staged residuals/second-glance status; R1-10 +
  2026-07-01 regression; release/commit-truth 2a1e9ce..09118b3; doc
  currency/teaching; fresh-eyes core sweep), dedup, one adversarial
  verifier per substantive finding (sixteen), a DOC/OBSERVATION batch
  check, and a completeness critic whose two real gaps were closed by
  direct probes (B3 regression HOLDS via the 12-test checksum-floor
  family; R11-01 witnessed at live gateway process level, three
  legs). Verification changed severity in only 2 of 16 findings
  (R11-14 upgraded MINOR->MODERATE — the stale "D-003 OPEN" claim
  ships in manifests AND package attestations/release notes; R11-12
  reclassified same-severity), zero refuted — vs 7 of 16 changed in
  R1-10; refutation-first finder prompts removed the false-alarm mass
  before verification. Headline: **R11-01 (MAJOR) — the compact codec
  silently relabels v1.1.0 events as locked-v1.0 and destroys
  geo.error_ellipse_m; live-witnessed as a laundering bypass of the
  default gateway's own schema gate (honest JSON 1.1.0 event refused
  SCHEMA_VIOLATION; the identical event compact-encoded accepted,
  laundered, forwarded clean with zero diagnostics).** Remaining
  mass: R1-10 defect classes surviving as siblings where the fix
  pinned one exemplar (TaskAck 'None' coercion R11-03; loop_status
  self-assert in THREE templates R11-07; harness events-kind vacuity
  R11-08 + unlinted shipped corpus R11-09; one-line doc-currency pins
  R11-11/15/17/18), enforcement arriving after new governed surfaces
  (sapient policy block zero negative coverage R11-05; NaN confidence
  vacuity R11-04; fail-open egress risk set R11-02), signalhunter
  no-lock exposure worse than recorded (R11-06 — fabricated
  TRUE_NORTH bearing from null island), and formal-release manifests
  carrying placeholder provenance vs the hash-policy MUST (R11-10).
  Positive assurance: ALL R1-10 fixes and ALL 2026-07-01
  fielded-safety fixes hold (54+36+8 probe families, full refusal
  matrices); v1.1.15/v1.1.16 published assets verified to
  cryptographic digests with SHA256SUMS never modified post-release;
  every numeric claim in all ten commits of the stretch reproduces
  (the commit-truth discipline working); proto/CBOR codecs faithful
  on their claimed surfaces; SAPIENT honesty spine held under 20+
  adversarial probes; diagnostic emission set enum-complete in all
  four registries. Maintainer attention flags: R11-24 (bladerf pack
  public-disclosure inventory — already in git history and published
  assets, scrubbing main would not retract publication) and the
  R11-01 fix-priority call. Disposition and any fix pass to be
  recorded here when directed.
- P1-09 (2026-07-21): **PR #4 RESOLVED — closed unmerged with credit;
  harvest confirmed complete** (maintainer direction: stop waiting for
  contributor revisions; "review it and merge it... if we haven't
  already done so" — the review established we already had). Full
  re-review of the PR against main at v1.1.16: every component is
  HARVESTED (correlation pattern doc + 7-event corpus + crosswalk +
  corrected MQTT guidance, all crediting PR #4), REJECTED-RECORDED
  (payload_schema_uri "not re-litigated"; snapshot container;
  1.2.0 dispatcher — empirically breaks 13/40 v1.1.0 events), or a
  recorded evidence-gated candidate carrying the contributor's
  deployment as n=1 evidence (data-ref-media-metadata,
  correlation-identity, aggregate-state-snapshot). No contributor
  revisions ever arrived after the 2026-07-08 review (single commit,
  2026-07-01) — the v1.1.0 adoption session's "check PR #4 for
  revisions" input resolves to: none. Mechanical finding worth the
  record: the branch merges TEXTUALLY CLEAN into v1.1.16 (zero
  conflicts; 8 of 11 files new, the governed files it edits untouched
  since its branch point) and would be semantically catastrophic — the
  1.2.0 oneOf arm double-matches every v1.1.0 event and the 1.2.0
  stamp exempts producers from every locked invariant. A clean merge
  with no conflicts to force human review is the most dangerous
  dialect shape; recorded as an R1-11 lens. Residue implemented (the
  entire unharvested remainder of 1,053 lines): legacy-topic
  enumeration in the MQTT guidance legacy-paths section; a
  preview-thumbnail exclusion scope note on DATA_REF_MEDIA_METADATA
  (the exclusion is now a decision, not an omission); a Class D
  encoding-surface consequence note on the correlation-identity
  roadmap candidate. Manifest regenerated (v1.1.16 identity kept),
  full battery green (687+172, gate all flags, examples 51/51,
  roadmap candidates=18). PR closed with a credit comment pointing
  the contributor at the four registry entries and roadmap tripwires
  their telemetry seeded.
- P1-08 (2026-07-21): **v1.1.16 PUBLISHED** — release commit `f8951ee`,
  annotated tag pushed, GitHub release live with all eight assets
  marked Latest, CI green (run 29805064763), checksums-only (signing
  decision in the release notes). Contributor notified on PR #7 with
  the full fix rationale and an invitation to restore the canonical
  bearing with a producer frame assertion. Battery results in
  `release/VALIDATION_REPORT_v1.1.16.md`, including the verified-benign
  CRLF policy-hash print observation (canonicalized
  `policy_bundle_hash` byte-identical across v1.1.15/v1.1.16).
- P1-08 (2026-07-21): **PR #7 (edge-comms-bladerf real-capture pack)
  reviewed and MERGED with maintainer fixes** (maintainer-directed
  "run a full review on it and if it is all good, merge it"). Review
  method: close maintainer read + independent adversarial review
  attempting refutation against contract/validator/reference-adapter
  precedent, with every fixture field walked back to an input field or
  documented convention. Verdict: mergeable-with-maintainer-fixes —
  the contribution's honesty handling was strong as submitted (geo
  refusal incl. zero-island, case-01 bearing omission, repo-exact
  timing fallback, lineage omission, calibration default, producer
  matches the committed `rf-sensor-*` pattern; both fixtures pass
  strict H validation), and it is the first EXTERNAL real-capture
  corpus (second independent RF telemetry source — promotion-evidence
  relevant). Findings fixed on merge: (MAJOR) case-02 emitted a
  frame-unlabeled canonical bearing that is provably heading-derived
  (az == uas_heading + 56.0 exactly) with `heading_source:
  "interpolated"` naming a sampling method, not a frame — the machine
  gates pass it because the bearing_frame check is value-when-present
  (contract 6.4 tolerates legacy-unlabeled v1.0 bearings), so this was
  review-caught, not machine-caught; demoted to
  features.native_bearing_deg per AUTHORING rule 2 (we cannot mint a
  TRUE_NORTH assertion the producer did not make), with the
  frame-provenance route documented for deployments that can assert
  it. (MODERATE) undocumented 1_SIGMA metric dropped — raw bound kept
  as features.native_bearing_error_deg; timestamp_source provenance
  preserved (receive-time vs embedded-telemetry); mapping.yaml
  reconciled with fixtures (unconditional bearing row removed,
  conditional rules + missing entries added). (MINOR) FFT-bin-width
  bandwidth convention documented. Governance-record hunks
  (CHANGELOG/worklog/handoff, written against pre-v1.1.15 main) were
  NOT merged — re-derived maintainer-side per the intake doctrine.
  Disclosure note for the maintainer: the pack README publishes
  internal flight-artifact names, the platform identity, and detection
  frequencies with precise timestamps — retained as provenance
  evidence on the contributor's own initiative; flag if any of it
  should be scrubbed. Second-glance addition: the bearing_frame
  presence gap (canonical bearing without frame provenance passes all
  machine gates) is a candidate warn-check for R1-11.
- P1-07 (2026-07-21): **v1.1.15 PUBLISHED** (maintainer-directed "once
  the end to end validation is good, cut the release per the
  documentation"; agent-executed per RELEASE_CHECKLIST). Release
  commit `bbd4c89`, annotated tag `v1.1.15` pushed, GitHub release
  live with all eight assets and marked Latest, CI green for the
  release commit (run 29802675100), checksums-only (signing decision
  recorded in the release notes; signing remains the maintainer's
  external process). Doc-currency pass covered README, installation
  guide (5 pins — caught by test_release_currency, which is the
  machine check working as designed), professional overview, tools
  README, release README, check_compat TARGETS, CI compat target, and
  the release-manifest test pins. Retention pass: no worklog archival
  this cut (the archive last ran at P1-06; the resume-note retention
  extension remains an open maintainer decision). Full battery
  results in `release/VALIDATION_REPORT_v1.1.15.md`.
- P1-07 e2e follow-up (2026-07-21, maintainer-directed "run the follow
  up first then once the end to end validation is good, cut the
  release"): **end-to-end wire validation against official Dstl tooling
  PASSED** — Apex-SAPIENT-Middleware v4.2.0 (commit 0c8591a), its
  shipped BSI Flex 335 v2.0 pb2 modules + validator, stock strict
  config, Python 3.11/protobuf 4.25.1 per Apex pins. Egress: strict
  ParseDict + byte round-trip + validator clean for all mapped Task
  types and DetectionReport projections incl. the zmeta.risk/
  zmeta.timing_quality self-labels; live Apex accepted Registration
  (acked) and egress detections as-is, zero error records, zero Error
  replies. Ingress: official-pb2-built messages (validator-clean, both
  JSON spellings) → schema-valid ZMeta events, zero findings. The
  validation's first pass found a MAJOR + two MODERATEs, all fixed
  pre-release and re-verified clean: egress report_id was UUIDv7 where
  the proto demands ULID (now ULID minted from the event's own ts —
  new ulid_util.py, no wall clock); object_id/task_id pass-throughs
  now validate-or-refuse with a caller-owned object_map escape hatch
  (idempotency keys are never rewritten). Honest skip record: C# BSI
  Flex 335 v2 test harness (no .NET SDK on host) and multi-node Apex
  routing not exercised — open integration targets, recorded in the
  pack README Validation section. Egress tests 41→48; adapters suite
  243.
- P1-07 (2026-07-20): **SAPIENT / BSI Flex 335 v2.0 mapping pack +
  reference adapters** (maintainer-directed after a verified spec-level
  comparison and ecosystem review of SAPIENT — the UK MOD C-sUAS
  standard, NATO C-UAS standard per STANREC 4869/AEDP-4869, and the
  compliance baseline in NATO ACT's 2025 C-UAS RFI; analysis records
  held maintainer-side, outside the repo). What landed (Class A/C
  reference surface + two sanctioned governed touches):
  `adapters/mapping-packs/sapient-bsi-flex-335/` (declarative pack,
  schema_id `vendor:sapient_bsi335:v2`),
  `adapters/ingress/sapient/` (SapientMessage protobuf-JSON ingress:
  DetectionReport -> OBSERVATION + per-claim INFERENCE with
  registration-derived model identity; fusion-node -> STATE promotion
  gated on caller promotion metadata incl. caller-owned loop_status;
  StatusReport -> SENSOR_STATUS/PLATFORM_STATUS on the 1.1.0 branch;
  TaskAck -> TASK_ACK; Error -> SCHEMA_VIOLATION; RegistrationStore as
  the units-and-error codex), `adapters/egress/sapient/`
  (COMMAND_EVENT->Task for GOTO/TRACK_TARGET/CHANGE_SENSOR_MODE only,
  altitude structurally excluded; STATE->DetectionReport with
  zmeta.risk/zmeta.timing_quality self-labels and quarantine/
  prohibited-use export refusal), 12 adapter-harness fixtures
  (27 -> 39), the `sapient-ingress` producer-authority block (governed
  policy touch, mirrors cot-ingress), adapters/README rows, release
  manifest regen (governed; v1.1.14 identity kept). SAPIENT Task
  ingress (external DMM tasking ZMeta platforms) deliberately OUT of
  v1 — command-safety escalation avoided by scope.
  **Session-limit interruption + integrity audit:** a usage limit killed
  the wire/verify agents mid-pass (after the policy/README edits, before
  any lint). On resume, a dedicated interruption-integrity review passed
  all nine checks (sanctioned surfaces only; byte-level append-only
  proof for harness fixtures; hunk-by-hunk truncation hunt on the two
  interrupted files; claimed-vs-on-disk file reconciliation; no stray
  artifacts; locked kernel untouched; style/pack/policy conventions
  faithful; no CRLF/mojibake; clean pytest collection). The
  adversarial honesty review then found four real defects, all fixed
  with tests: (1) unknown active_mode silently dropped the
  maximum_latency est_error_ms widen -> conservative cross-mode
  fallback; (2) signal[] entries past the first vanished -> preserved
  as vendor.sapient.signal_additional; (3) the promotion path
  self-asserted loop_status CHECKED_NOT_REFLECTION -> now refused
  unless caller-supplied (deliberate divergence from the CoT template,
  which can receive it message-carried); (4) out-of-range protobuf
  Timestamp raised out of translate() -> fail-closed refusal.
  **Accepted deviations (adjudicated at closeout):** unregistered-node
  detections refuse entirely (the build-spec's obs-still-emitted
  variant would have required fabricating a modality — refusal over
  fabrication ratified); four registration-dependent harness fixtures
  are structurally inexpressible (the harness passes JSON-only kwargs
  and cannot construct a RegistrationStore) — coverage lives in the 110
  colocated pytest tests; ingress ships without __init__.py per the
  klv-pair precedent.
  **Second-glance register additions:** (a) cot_to_zmeta_template still
  defaults promotion loop_status to CHECKED_NOT_REFLECTION — same
  pattern the SAPIENT fix removed; should sync with the paused CoT
  egress findings cluster. (b) Harness gap: fixtures cannot construct
  non-JSON objects; a module-level entry point taking registration
  message dicts (e.g. translate_with_registration_msgs) would make the
  four missing fixtures one-liners — candidate, not built. (c) SAPIENT
  branch-evidence items recorded, not implemented: RADAR-family
  modality feature contracts (roadmap-queued; radar/lidar/seismic
  ingress currently degrades to inference/promotion paths),
  track-lifecycle vocabulary (SAPIENT evidence thin: free-text state
  only), tasking verbs (LOOK_AT, multi-waypoint patrol, task-cancel).
  (d) Egress detection projection emits full proto enum names
  (proto3-JSON wire form) — protobuf wire encoding itself remains
  out-of-scope, documented.
  **Validation:** full kernel gate green all flags, examples 51/51,
  full pytest 680 passed + 172 subtests zero failures (570 -> 680),
  adapter harness 39/39, policy lint ok, manifest regenerated +
  validated (groups=19 artifacts=70), git diff --check clean.
- R1-10 AAR (2026-07-17), maintainer side — the full audit -> fix ->
  verify -> release cycle as an exercise of the R1-09 AAR's own
  lessons. **What happened:** the R1-10 stack audit ran the R1-09
  lessons as lenses (teaching artifacts, prose-only vs machine-pinned,
  falsifiable evidence, doc currency) plus a 2026-07-01 defect
  regression check — five independent finder passes, then sixteen
  adversarial verifiers, one per substantive finding, each instructed
  to refute with live probes. Verified findings: seven MAJOR, four
  MODERATE, eight MINOR plus the doc-currency list; three initial
  HIGHs dissolved to MINOR because the governance record documented
  the deferral. The maintainer directed fix-every-finding then
  re-audit. The fix pass ran as six dependency-ordered waves
  (adapters; harness+validators/policy/schema; tools; contract; docs;
  governed regen) with disjoint file ownership, committed at wave
  boundaries. A session usage limit killed the doc-sweep agent
  mid-pass; the relaunched wave completed, and a six-slice
  verification audit afterward (interrupted-wave item-by-item, live
  re-probes of every original audit probe, commit-truth verification
  of every commit message, findings-coverage critic) confirmed the
  interruption left zero half-done file state. That verification
  audit also caught two MAJOR residues the fix pass itself introduced
  — the GEO_ZERO_FILL_SUSPECTED warn code was omitted from the
  diagnostic enums, so the gateway destroyed its own zero-fill
  warning diagnostic before egress (proven live); and the manifest
  regeneration diverged from the published SHA256SUMS_v1.1.13 pin —
  plus commit-evidence inaccuracies. Residues were fixed (6f47237),
  the divergence was resolved by the maintainer-directed v1.1.14 cut
  (f9241c4), run strictly per RELEASE_CHECKLIST with the full battery
  green. Eleven commits total, b826445..0cb5407. **Why the defects
  existed:** the v1.1.13 refusal doctrine was machine-pinned on
  example-vendor only — the same fabrication class survived in every
  other reference adapter because fix-plus-fixture ran once, not
  per-surface; honesty invariants stated in the contract but
  schema-inexpressible had no policy/validator encoding; the checking
  tools trusted their inputs (empty-file vacuity); and current-facing
  doc claims lived only in prose. **What held under stress:** the
  locked kernel (byte-stable minus sanctioned diagnostic enums, all
  2026-07-01 fielded-safety fixes re-verified by fresh probes);
  the governance record — three findings dissolved precisely because
  deferrals were documented where an auditor would look; the manifest
  hash gates (every governed drift caught, honest regen forced); the
  release checklist (run literally, its new currency test made an
  incomplete doc pass impossible — 26 pinned-surface tests gated the
  release commit); and wave-boundary commits with disjoint ownership,
  which is why a hard mid-pass interruption cost nothing. **Lessons:**
  (1) Machine-pinning one exemplar does not propagate — when a
  doctrine lands, the fix-plus-fixture loop must run per reference
  surface, and the harness must be able to EXPRESS the doctrine for
  every callable shape (the None-refusal register gap blocked refusal
  fixtures for single-event adapters until fixed). (2) Adversarial
  verification pays twice: it kills false positives AND calibrates
  severity — unverified severity did not survive in seven of sixteen
  findings, every change downward or refuted-as-framed: exactly the
  false-alarm mass verification exists to remove before a maintainer
  spends attention on it. (3) The fix pass is itself an audit surface:
  both post-fix MAJORs were introduced BY the fixes (one by the
  auditor's own wrong adjudication that warn codes are never cited in
  diagnostics); fix work gets the same falsifiable-evidence discipline
  as releases, including an end-to-end probe of each new check's
  emission path, not just its detection path. (4) Recorded evidence
  must be counted, not estimated: three commit messages carried
  numeric claims that do not reproduce ("35 tests" vs 30 collected;
  "917" vs 916 lines; "21 tests" unreproducible) — corrections
  recorded here per the falsifiable-evidence rule; commit messages are
  immutable, so the worklog carries the corrections. (5)
  Forward-looking status claims in committed docs are interruption
  hazards — the one cutoff artifact was a "queued, landing in later
  commits" CHANGELOG bullet the later commits never flipped; write
  past-tense records, or flip forward references in the commit that
  lands them. (6) Environment honesty: Windows CRLF materialization
  made container and local gateway startup hash prints diverge on
  identical content — the manifest's canonicalized hashes are the
  authoritative gate; a .gitattributes LF pin would retire the whole
  class (maintainer decision, flagged below). Net enforcement growth
  across the cycle: pytest 485 -> 570 (subtests 110 -> 172), harness
  fixtures 15 -> 27, bad-events 23 -> 27, four governed diagnostic
  codes, and five new test families (release-currency, input floors,
  inverse coverage, strip guard, zero-fill warn). Nothing in the
  cycle touched locked-kernel semantics; every fix landed in the
  outer rings — the design working as claimed, again.
- Second-glance register from the R1-10 closeout (recorded so nothing
  lives only in session context; none are defects, all are candidates
  for the next audit or maintainer decisions): (a) unencoded
  SHOULD-level conventions found by the audit's conventions lens but
  below the findings bar — fusion/state confidence exceeding the
  weakest material input (contract 8.3) has no warn-check;
  gateway-backfilled `t_publish` carries no gateway-supplied marker
  (contract 5.2); `lineage.transform` prefix shape
  (`translate:`/`promote:`) is harness-checked only when a fixture
  opts in; published historical `SHA256SUMS_*.txt` immutability has
  no pytest pin. (b) signalhunter residuals (flagged in the fix-pass
  entry above). (c) a pre-existing worktree at `.tmp/review-pr-2`
  (branch `review/pr2-frame-fixes`) — outside the canonical tree,
  keep-or-prune is a maintainer call. *(Still open 2026-07-27: the
  worktree still exists; re-homed to the handoff's live maintainer
  queue so it is not buried by archival.)* (d) `.gitattributes` LF
  normalization would retire the CRLF materialization class (container
  hash prints, historical checksum-entry caveat) — governance-adjacent
  because it changes working-copy bytes for hashed files; escalated,
  not applied. (e) the worklog resume note is growing and the archive
  policy covers completed task sections only — a retention-policy
  extension for superseded resume-note bullets is a maintainer
  decision. **RESOLVED 2026-07-27 (maintainer-directed at closeout:
  "do any updates, edits and pruning needed"): the policy is extended
  to cover superseded resume-note bullets of COMPLETED, PUBLISHED
  cycles — append-moved VERBATIM to
  `docs/zmeta_refinement_worklog_archive.md`, never deleted, never
  summarized away.** Two guards, both from this cycle's own lessons:
  a bullet is only movable once its cycle is published (so no live
  context is archived), and any still-open pointer inside a bullet is
  re-homed to the handoff's live queue BEFORE the move (so archiving
  never buries an open item — the CR-03 class in reverse). (f) UxS command-loop fielding roadmap (maintainer
  discussion, 2026-07-17): display loop fieldable now; GCS-originated
  tasking needs the command-evidence lineage check (commands citing
  motivating inference/fusion parents, gateway-checked against
  upstream `use_limits`) plus a SITL end-to-end gate;
  platform-to-platform retasking additionally needs authenticated
  transport (deployment-side) and the track-lifecycle promotion (this
  deployment is the roadmap tripwire evidence); the v1.1.0 adoption
  session should take the command-loop evidence as input. *(Status
  2026-07-27: the command-evidence lineage check SHIPPED in v1.1.18
  (`policy/command-evidence.yaml` + gateway enforcement), and the
  track-lifecycle work landed as a current-vocabulary pattern doc with
  the roadmap candidate deliberately left RESERVED — the multi-UxS
  deployment is the awaited second evidence leg. Still open and
  re-homed to the handoff's live queue: the SITL end-to-end gate and
  authenticated transport, both deployment-side.)*
- R1-10 (2026-07-17): **v1.1.14 released** (maintainer-directed,
  agent-executed) — the audit-driven honesty hardening cut, run
  strictly per RELEASE_CHECKLIST. Content: the seven R1-10 fix-pass
  commits plus the verification-audit fixes (see the fix-pass entry
  below). Validation battery all green: manifest regenerated and
  validated for zmeta-v1.1.14 (groups=19, artifacts=70; claims synced
  and verified with --verify-contract-hash), full kernel gate with all
  flags (bad-events 27, adapter harness 27), strict examples 51/51,
  policy risk lint, future-roadmap validation, full pytest 570+172
  zero failures, risk-filter presets, workflow end-to-end (H and M —
  CoT output now carries event-authoritative time, the honest default
  visible on the wire), live gateway (JSON and compact-L), three
  gateway self-tests, compat sweep 9/9 corpora at v1.1.14, packet-size
  max=150 of 240, bundles + release package built and validated
  (package zip auto-built at checksum time), containerized gateway
  verified (build, run, replay received, no violations; the
  container-vs-Windows startup hash print difference is CRLF
  materialization — the manifest's canonicalized hashes are the
  authoritative gate and pass identically), SHA256SUMS_v1.1.14.txt
  written LF and verified with full coverage, git diff --check clean.
  Doc-currency pass executed per the checklist (README release section
  + v1.1.14 integration notes, installation guide, professional
  overview, tools README, release/README, check_compat TARGETS +
  v1.1.14, CI compat target, compat CLI test, release-manifest test
  pins; test_release_currency green against the v1.1.14 manifest).
  Signing decision: checksums-only, stated in the release notes.
  Retention: nothing newly archivable (fix-pass records are current
  context). Publication confirmed (2026-07-17): release commit
  `f9241c4`, annotated tag `v1.1.14` pushed, GitHub release live with
  all eight assets and marked Latest
  (<https://github.com/JTC-byte/zmeta-spec/releases/tag/v1.1.14>),
  GitHub CI passed for the release commit, body carries the release
  notes including checksum verification instructions. Checksums-only;
  signing remains the maintainer's external process.
- R1-10 fix pass + verification (2026-07-17, maintainer-directed "fix
  every issue found, then re-audit"): every audit finding fixed or
  documented-deferred across nine commits — ddd0252 (audit record),
  06a576f (reference-adapter honesty pass: null-identity refusal,
  eo-cv confidence/geo fixes, kraken+moth JSON-replay refusal matrices
  including the contract 6.8 moth alt_m fix, CoT honest defaults,
  template lineage docstring, plus two same-class in-pass finds),
  cf4e7da (checking machinery: empty-input floors in all eight gate
  tools, checksum coverage cross-check + LF endings, manifest-derived
  defaults, release-currency test, claims-validator residues,
  kernel-gate examples wiring), e07af84 (machine-encoded honesty:
  v1.1 quality bearing_frame/heading_source constraints with
  version-agnostic checks, INFERENCE fused-state denylist completion,
  zero-fill warn heuristic, protected strip paths, harness refusal
  register + surplus-expectation guard, refusal-fixture rollout
  15 -> 27, bad-events 23 -> 27, three governed diagnostic codes added
  to both schema enums per the D-013 pattern), ef08974 (doc
  currency/retention sweep, ten items), a1bfa1f (contract 2.1/5.7
  clarifications, Class B), 0da1a5c and the closeout commit (manifest
  + claims regenerated, release identity preserved), 6f47237
  (verification-audit fixes). The session-limit interruption mid-pass
  left no half-done file state (verified hunk-by-hunk). Post-fix
  verification audit (six adversarial slices: interrupted-wave
  item-by-item, live re-probes of every original audit probe at HEAD,
  commit-truth verification of all messages, findings-coverage
  critic): the pass held; residues found were fixed in 6f47237 —
  GEO_ZERO_FILL_SUSPECTED diagnostic coherence (the gateway's own
  zero-fill warning diagnostic was schema-invalid and destroyed before
  egress; now in both enums + allowed list with an inverse-coverage
  test), CoT point@hae unknown-convention on absent alt_m and
  missing-ts refusal outside wall-clock mode, sign-script
  manifest-derived default, and a --verify-contract-hash zero-claims
  floor. Commit-evidence corrections recorded per the
  falsifiable-evidence rule (messages are immutable history; the
  record is corrected here): cf4e7da says "35 tests added" — 30
  collect; ef08974 says handoff "917 -> 727 lines" — the before-count
  is 916; e07af84 says "reason-code sync suite 21 tests, 116
  subtests" — the file collects 5 tests, 116 subtests (the 21 does
  not reproduce). Recorded, maintainer decision pending: the
  regenerated in-repo manifest diverges from the manifest entry pinned
  in the published SHA256SUMS_v1.1.13.txt (published checksums are
  immutable; resolution is the next release cut or an explicit
  accepted-divergence record). Flagged residuals for the next audit
  (in-pass observations, deliberately not fixed this pass):
  signalhunter .bin replay stamps wall-clock ts at translation time
  (honestly labeled UNSYNCED, but an A4 sibling class); signalhunter
  GPS no-lock (0,0) passes into quality.sensor_position_2d unguarded
  (the new zero-fill warn covers canonical geo, not
  sensor_position_2d); signalhunter's internal GPS-frame dict carries
  a dead alt_m 0.0. Final validation: full kernel gate green with all
  flags (bad-events 27, adapter harness 27, claims=2 including
  --verify-contract-hash), strict examples 51/51, full pytest 570
  passed + 172 subtests with zero failures, diff-check clean. Net
  enforcement growth across the pass: pytest 485 -> 570 tests
  (subtests 110 -> 172), harness fixtures 15 -> 27, bad-events
  23 -> 27, plus the release-currency, input-floor, inverse-coverage,
  strip-guard, and zero-fill test families.
- R1-10 (2026-07-16): full stack audit executed per the queued
  direction, applying the R1-09 AAR lessons as audit lenses (teaching
  artifacts, prose-only vs machine-pinned conventions, falsifiable
  evidence, doc currency/retention) plus a regression check of the
  2026-07-01 audit defects and governed-artifact integrity. Method:
  verified-green baseline first (kernel gate, pytest 485+110 zero
  failures, diff-check clean at `b826445`), five independent finder
  passes, then every substantive finding adversarially verified by an
  independent skeptic pass with live probes — post-verification
  severities recorded; three findings dissolved to MINOR precisely
  because the governance record documented the deferral (command-
  altitude synonym residual per the v1.1.10 Known Enforcement
  Limitation; track-lifecycle per the s1-01 do-not-add decision and
  roadmap branch; locked-schema diagnostic enum additions per their
  Class B record). Audit was read-only; tree untouched. **Verdict: the
  kernel and governance apparatus held** — 2026-07-01 fielded-safety
  defects re-verified fixed by fresh probes, manifest tamper detection
  witnessed, locked v1.0 schema byte-stable since v1.1.10, all
  machine-pinned release surfaces correct. **The defect mass is in the
  outer rings, exactly where the AAR predicted:** the reference
  adapters the authoring guide routes authors to carry unfixed
  instances of the fabrication class v1.1.13 machine-pinned on
  example-vendor only (null-identity coercion in the worked exercise;
  eo-cv fabricated confidence 0.0 / null-confidence crash / alt_m
  zero-fill; kraken+moth JSON-replay fabricated RF defaults; moth geo
  alt_m zero-fill — a contract 6.8 MUST violation; CoT egress
  fabricated ce/le accuracy and wall-clock-fresh timestamps live by
  default on the gateway --emit-cot path). Latent honesty gaps with no
  machine check: quality.bearing_frame/heading_source unconstrained in
  both schemas (the only v1.0 frame-provenance channel),
  gateway strip config can silently delete risk_adjudication (declared
  never_mutable; shipped configs clean, so latent), INFERENCE nested
  estimated_state/members laundering residue (policy denylist never
  expanded when STATE/COMMAND were), zero-fill geo passes clean.
  Checking-machinery vacuities: all eight JSONL gate tools pass on
  empty input (manifest pinning backstops conformance/** in CI; the
  unprotected surface is examples/*.jsonl — unpinned, unfloored,
  absent from the local kernel-gate command), harness expect.events
  overhang silently unevaluated with event_count optional, checksum
  verification accepts empty/partial files. Doc currency: every defect
  prose-side, none machine-pinned — installation guide stale at
  v1.1.12 (a checklist-NAMED surface, the item's second confirmed
  miss), release/README at v1.1.11 and contradicting the reconciled
  never-hand-zip rule, professional overview stale, handoff internally
  inconsistent about the current release with under-executed
  retention, check_compat CLI default three releases stale, two bundle
  builders with stale version constants (the sign-script default's
  unenumerated siblings). Full tiered findings, evidence anchors,
  refuted items, and positive-assurance record:
  `docs/r1_10_full_stack_audit.md`. **Maintainer disposition: fix every
  finding (six-part fix pass recorded in the audit doc's disposition
  section), then a follow-up audit.**
- Previously queued (2026-07-08, now queue item 2): the all-fourteen
  v1.1.0 adoption-decision session — worksheet plus decisions in one
  session, promotion evidence bar as the standard, check PR #4 for
  contributor revisions first.
- R1-09 AAR (2026-07-16), maintainer side — the PR #5/#6 -> v1.1.13
  exchange as a red-team exercise against the standard's own claims,
  agent-guidance docs, and workflows. **What happened:** two
  onboarding PRs from the external-adopter thread (P1-05/P1-06, authored
  maintainer-side; driver: a multi-sensor drone/COP team onboarding
  through an AI coding agent — the first adopter cohort onboarding from
  scratch through the authoring path) were red-teamed maintainer-side,
  with every finding adversarially verified before posting; the review
  record, including refuted findings, lives on the PR #5/#6 threads.
  Surviving findings clustered exactly where the standard predicts risk:
  the teaching adapter emitted schema-invalid output instead of refusing
  (bandwidth_hz), the canonical EO example taught a bounding-box dialect
  contradicting the reference adapter it mirrored, one commit message
  recorded validation evidence that did not reproduce, and one intake
  template misparaphrased the governed promotion evidence bar. Rework
  came back as fix commit (#5) + rebase (#6, because a false validation
  claim must not become immutable history) + an additive commit
  institutionalizing the lessons (AUTHORING §3 rule 10, §9 failure
  modes); the delta re-verification (recorded on the PR #6 thread)
  confirmed zero drift beyond the approved fix list and that every
  commit-message validation claim reproduced at review time. Then,
  maintainer-directed: fast-forward merges preserving
  the reviewed SHAs, intake labels, the AAR's machine-encoding candidate
  implemented (harness `event_count` refusal pins, corpus 11 -> 15,
  lint-schema sync test), and the v1.1.13 cut run strictly per
  RELEASE_CHECKLIST — which itself got red-teamed by being run: it was
  missing the release-manifest test pins (found by pytest mid-release,
  item amended), the package zip had no producing script (now auto-built
  by `sign_release_artifacts.py`, tested both directions), the signature
  items were unskippable-yet-always-skipped (now conditional behind an
  explicit signing-decision line), and `sign_release_artifacts.py`
  carried a stale VERSION default (bumped; added to doc-currency).
  **Why:** green-path authoring (schema requiredness lives per-subtype in
  the schema; the guide didn't say to read it); secondhand summaries
  instead of primary sources (the example mirrored a description of the
  eo-cv adapter, not its code); evidence recorded as ritual rather than
  as commands run where they could fail; checklist items written before
  ever being exercised. **What held under stress:** every
  schema/policy-checkable dishonesty was caught mechanically the moment
  failing input was exercised; everything that escaped lived only in
  prose — the exact boundary the refusal fixtures now move; dialect
  drift was caught in the canonical imitation source before external
  agents could learn it; the manifest-hash gates enforced the
  governed/advisory boundary mechanically all the way through (nothing
  hashed moved without maintainer direction, and when directed, the gate
  forced honest regen); authority order and release limits held — agent
  execution, human decision at every irreversible gate (merge, publish,
  cut). Net enforcement growth across the exchange: harness fixtures
  11 -> 15, strict examples 47 -> 51, pytest 465 -> 485 tests (+110
  subtests). **Lessons, zmeta side:** (1) teaching artifacts are the
  highest-leverage defect surface — agents copy them verbatim; red-team
  them before merge, always. (2) When review catches a prose-only
  convention violation, the fix is two-part: correct it AND ask what
  fixture/test would have caught it — that loop is what produced
  `event_count`; conventions encoded as fixtures get caught, conventions
  living in prose escape. (3) Validation evidence must be falsifiable:
  name the exact command, run where it can fail (now practiced by the
  release commit itself). (4) The release checklist is a living gate:
  its first honest end-to-end exercise found four gaps — one amended
  mid-run (the test pins), three reconciled in the immediate post-release
  follow-up — keep running it literally every release. (5) The
  cross-session pattern that worked: PR threads for the durable review
  record, direct session messages for awareness; rebase-vs-fix-commit
  decided by whether a false claim would become immutable. (6)
  Maintainer-side tooling (first bite, recorded): two Windows-shell
  text-processing near-misses in one cycle (a WinPS Get-Content/
  Set-Content round-trip mojibake'd README UTF-8, caught and reverted
  before commit; a quote-mangled `git commit -m` that loudly failed) —
  prose edits belong in file tools or python, commit messages in
  `git commit -F`; one hygiene bullet added to CLAUDE.md. Nothing in
  this exchange required touching the locked kernel: the outer rings
  (docs, examples, fixtures, tooling, policy-adjacent conformance)
  absorbed all of it, which is the design working as claimed. Meta-note:
  this AAR entry was itself fact-checked against the repository record
  before commit; the check found and corrected five inaccuracies in the
  draft — including an overclaim inside lesson (4), the lesson about
  falsifiable evidence — which is lesson (3) demonstrating itself.
- R1-09 follow-up (2026-07-16): intake funnel closed
  (`blank_issues_enabled: false` + a fourth "General question or report"
  template labeled `question`) and the two release-flow friction points
  from the v1.1.13 retrospective reconciled — the package zip is now
  auto-built at checksum time by `release/sign_release_artifacts.py`
  (tested both directions: builds when missing, never overwrites), and
  the checklist marks signature items signed-releases-only with an
  explicit signing-decision line. Maintainer-directed.
- R1-09 publication confirmed (2026-07-16): release commit `1117bc6`,
  annotated tag `v1.1.13` pushed, GitHub release live with all eight assets
  and marked Latest, CI green on the release commit (2/2 runs), body
  includes checksum verification instructions. Checksums-only; signing
  remains the maintainer's external process.
- R1-09 (2026-07-16): **v1.1.13 released** — merged PR #5 then PR #6
  (fast-forward, no squash, reviewed SHAs preserved), created the three
  intake labels (`adapter-authoring`, `field-telemetry`,
  `semantic-ambiguity`), and cut the release per RELEASE_CHECKLIST
  (maintainer-directed, agent-executed). Release content beyond the merged
  PRs (Class B, maintainer-directed): the adapter harness gains
  `expect.event_count` (0 pins fail-closed refusal — the P1-06 AAR's
  machine-encoding candidate, now implemented); must-pass corpus 11 -> 15
  (example-vendor emission fixture + one refusal fixture per
  schema-required RF input field, negative-probed non-vacuous);
  `fixture.schema.json` learns `event_count` and
  `gateway/tests/test_fixture_schema_sync.py` pins lint-schema/harness
  sync. Doc-currency pass run per the new checklist item (README release
  section + v1.1.13 integration notes, tools README, CI compat target,
  compat CLI test, check_compat TARGETS + v1.1.13, release-manifest test
  pins); the checklist item itself was improved mid-pass — it did not name
  the `gateway/tests/test_release_manifest.py` `release_id`/`release_date`
  pins, which full pytest caught (checklist-usefulness verdict: the new
  items work; first exercise found and closed one gap). Validation: full
  kernel gate green (harness 15), 51/51 strict examples, pytest 483+110
  zero failures, compat sweep of all nine corpora at v1.1.13 clean,
  self-tests/e2e/live/packet-size ok, containerized gateway verified
  (recv/fwd, zero violations), manifest + claims regenerated for
  zmeta-v1.1.13, checksums written and verified — checksums-only, signing
  remains the maintainer's external process. Retention pass: P1-05/P1-06
  resume-note entries retained as current context (most recent sessions);
  nothing newly archivable ahead of this release.
- P1-06 AAR (2026-07-16): the maintainer review of PRs #5/#6 doubled as the
  first external red-team pass of the authoring guide, and the findings are
  institutionalized rather than just fixed. Finding: every caught defect's
  rule already existed in-repo — the in-repo normative docs were sufficient
  (the guide itself had one gap, closed as the section 3 rule below), the
  validators flagged every schema-checkable issue instantly once the failing
  input was exercised, and the escapes were prose-only conventions (bbox
  dialect) plus author-workflow failures. Actions: the four review-proven
  failure modes are now
  AUTHORING.md §9 agent guidance (primaries-not-summaries; refusal tests per
  required field; guide-as-checklist against your own exemplar; exact
  evidence commands), and the one true doc gap is closed as §3 rule 10
  (schema minimums are per-subtype; requiredness from the schema, never
  from sample inputs). Candidate machine-encoding follow-up recorded, not
  implemented: "refusal fixtures" for the adapter harness (callable must
  return an empty result for a given input) so fail-closed behavior is
  pinned the way must-pass pins emission — conventions encoded as fixtures
  get caught, conventions living only in prose escape.
- P1-06 (2026-07-15): onboarding batch on current `main` (Class A docs +
  Class C reference; no governed-artifact change). Follows P1-05 from the
  same external-adopter thread. (1) README restructured for first contact —
  ten-minute proof path, Start Here By Role, ZMeta In The Field (fielded
  EO/CV + RF provenance of the Production adapters, deployments unnamed
  pending maintainer decision); (2) worked exercise
  `adapters/ingress/example-vendor/` implementing the example-vendor pack to
  the AUTHORING.md requirements (12 tests; adapters README table gains this
  row plus the missing JREAP row); (3) `tools/check_adapter.py` one-command
  ladder wrapper + advisory `conformance/adapter-harness/fixture.schema.json`
  (all 11 existing fixtures lint clean); (4) GitHub issue templates
  (authoring friction / semantic ambiguity / deployment field report) + PR
  template; (5) retention: worklog S0-01..R1-05 archived verbatim to
  `docs/zmeta_refinement_worklog_archive.md`, new `docs/README.md`
  guidance-vs-process index, RELEASE_CHECKLIST doc-currency + retention
  items. Deferred to maintainer: naming the fielded deployments; the
  `mavlink_to_zmeta_template.py` rename (governed fixture + classes refs);
  physical `docs/process/` move (5 governed refs in conformance_classes);
  mechanical claim generator; v1.1.0 adoption decision (already queued).
  Maintainer-review fixes folded in the rebase: bandwidth_hz is now
  fail-closed with a refusal test (the schema's RF minimum feature set made
  the optional-bandwidth path emit schema-invalid events — the teaching
  adapter violated the rule it teaches); the profile kwarg/stamp dropped
  (gateway-added export metadata, contract 3.4); check_adapter gained an
  empty-input guard, flushed step headers, and honestly scoped wording;
  fixture-schema `expect.events` made exclusive of silently-ignored sibling
  keys; the field-report template points at the evidence bar instead of
  paraphrasing it; handoff pointers updated for the worklog/archive split;
  the archive's trailing blank line stripped (verbatim-move separator, not
  section content).
  Validation: example-vendor tests 12/12, check_adapter full ladder PASS,
  strict examples 51/51, full kernel gate green, pytest failure set
  unchanged vs clean main (Windows MAX_PATH tmp-path artifact), git diff
  --check clean against the merge base.
- P1-05 (2026-07-15): adapter-author onboarding consolidation on current
  `main` (Class A docs + examples; no schema, policy, vocabulary, or
  validation-behavior change). Driven by external-adopter demand (a
  multi-sensor drone/COP team onboarding via an AI coding agent): (1) new
  `adapters/AUTHORING.md` — the single consolidated authoring entry point
  (orientation, decoded-input floor, layer-choice table with nearest
  reference per input kind, the anti-fabrication non-negotiables with
  contract cites, the exact validation command ladder, a formal
  adapter-harness fixture-key reference, producer-authority and
  definition-of-done notes, AI-agent guardrails), linked from
  `adapters/README.md`; (2) new `examples/zmeta-eo-chain-examples.jsonl` — a
  worked EO full chain (OBSERVATION -> INFERENCE -> FUSION -> STATE, genuine
  chained lineage, policy-allowed producers `eo-camera`/`eo-cv-adapter`/
  `fusion-engine`, local mp4 `data_ref` pointer, no raw features on STATE)
  as the EO companion to the core RF chain, registered in
  `tools/validate_examples.py` (corpus 47 -> 51) and the examples README.
  Validation: new corpus 4/4 strict, full strict examples pass, full kernel
  gate, and full pytest green (results in the handoff).
  Classification note (maintainer review): the `tools/validate_examples.py`
  registration edit is a validator change — Class B under the governance
  taxonomy, not plain Class A — and it grows what CI `--require-all`
  enforces (47 -> 51). Its Class B requirements (docs, fixture-by-example,
  full kernel gate, pytest) were met in this same change and the file is not
  manifest-hashed; future corpus additions should classify as Class B rather
  than cite this entry as Class A precedent.
- S1-26 (2026-07-08): prepared v1.1.12 (governance and honesty closeout) on
  current `main` per explicit maintainer direction to work the full
  relock-gap list. Delivered: (1) promotion evidence bar in
  `spec/extension-registry.md` + change-governance Class D — moving
  reserved/proposed concepts into a version branch now requires two or more
  independent implementations demonstrating the need plus a documented
  contract Section 2.6 failure condition the outer rings cannot solve;
  (2) S1-11B implemented — `spec/future-branch-roadmap.yaml`/`.md` (18
  candidates with evidence + tripwires, 3 recorded rejections/deferrals,
  including the PR #4 tranche-3 candidates and honesty-primitive schema
  standing), `tools/validate_future_roadmap.py`, tests, and a new
  `future_branch_roadmap` release-manifest group (groups=19, artifacts=70);
  D-003 closure condition met, closure recommended (maintainer call);
  (3) lineage honesty — kraken/moth/signalhunter/klv/mavlink/eo-cv no longer
  fabricate `lineage.based_on` with random UUIDv7s: observation/system
  outputs omit lineage unless callers pass real `based_on`;
  mandatory-lineage events refuse to emit without real parents (mavlink
  STATE needs `based_on`/`source_zmeta_event_id`; eo-cv INFERENCE needs
  `parent_event_ids` or a UUIDv7 `source_event_id`); adapter versions
  bumped; harness fixtures updated + 1 new caller-lineage fixture (total
  11); new eo-cv test file; ingress template README never-fabricate rule;
  (4) gateway UDP send containment — `_send_datagram` catches OSError
  (oversize ~65507-byte sends), drops with new `send_failure`
  metrics/diagnostics instead of crashing the main loop; real-socket
  oversize test proves it; (5) truth-in-advertising — mapping-packs README
  states no runtime engine executes `mapping.yaml` (declarative packs +
  adapter code + test evidence); (6) honesty-primitive enforcement home
  documented in the professional overview (policy + conformance is the
  intended home; schema standing parked as an evidence-gated roadmap
  candidate); (7) handoff human-decision list resolved to standing defaults
  with two genuinely open items (signing process — maintainer generating a
  signature 2026-07-08; v1.1.0 adopted-vs-experimental). Validation: full
  kernel gate green (projection 37, registry 61, classes 34/2,
  encoding-negative 50, precision 32, bad-events 23, adapter 11), roadmap
  validator ok (18/3), examples 47/47, policy lint ok, pytest 465 + 110
  subtests, workflow end-to-end H/M, live gateway JSON/compact, gateway
  self-tests x3, check_compat v1.1.12 for all 8 corpora, packet-size
  max=150/240, release package ok, checksums ok. Release commit carries
  notes/report/SHA256SUMS_v1.1.12.txt; annotated tag created locally;
  publication (push, GitHub release, optional signatures) remains with the
  release authority.
- R1-08 (2026-07-08): `v1.1.12` published per explicit release-authority
  direction — `main` and the annotated tag pushed (release commit `e5a88b1`),
  GitHub CI green for the pushed commit, GitHub release created with all
  eight assets including `SHA256SUMS_v1.1.12.txt`, marked Latest. Published
  checksums-only per the maintainer's direction; he is standing up the
  signing process for the next release. Post-publication alignment updated
  current-facing docs (README, installation guide, tools README,
  professional overview), the CI compatibility target, and the compatibility
  CLI test to `v1.1.12`. **D-003 closed by maintainer decision** in the same
  pass: the roadmap artifact + registry + evidence bar now track future
  branch work individually (register entry updated). The deferred issue
  register is now fully closed — D-001 through D-014 all resolved.
- S1-24 session record (at the time, the current next work item): S1-24
  prepared the v1.1.10 fielded-safety enforcement
  release on then-current `main` — command-altitude denylist completion to the full
  §7.8 set, a recursive STATE laundering check with whitespace/case key
  normalization plus the full §7.7 list, adapter calibration honesty
  (Kraken/Moth stop hardcoding `CALIBRATED`; default conservative
  `UNCALIBRATED`), and egress MAVLink altitude-guard alignment — with eleven new
  deep-nested bad-event fixtures, two direct `validate_semantics` unit tests,
  adversarial bypass verification, and a regenerated release manifest and
  claims. The full kernel gate and pytest are green.
- R1-06 publication note: the release authority published `v1.1.10` on
  2026-07-04 — annotated tag on release commit `6ce4f29`, GitHub release with
  all seven expected assets plus `SHA256SUMS_v1.1.10.txt`, CI green.
  Published checksums-only, consistent with v1.1.5 through v1.1.9; detached
  signatures remain an optional release-authority step. A post-publication
  alignment pass (2026-07-07) updated current-facing docs, tool examples, the
  CI compatibility target, and the compatibility CLI test to the published
  `v1.1.10` baseline without touching any published release assets.
- S1-25 (2026-07-07): prepared v1.1.11 (field-driven adoption guidance).
  Upstream PR #4 — a v1.2.0 proposal from a live at-scale ZMeta deployment
  (multi-node drones/sensors, fusion engine, custom COP, TAK bridges) — was
  reviewed against the locked kernel and NOT merged: empirically verified
  that its v1.2.0 schema arm breaks oneOf dispatch for all v1.1.0 events and
  drops every locked invariant (command altitude, STATE laundering,
  confidence placement, UUIDv7, UTC-Z all accepted under a "1.2.0" label);
  review with evidence posted on the PR. The legitimate fielded needs were
  re-derived from the kernel outward: three advisory docs (MQTT binding
  guidance, vocabulary crosswalk, correlation pattern), four
  extension-registry entries (CORRELATION_HINT proposed,
  DATA_REF_MEDIA_METADATA proposed, AGGREGATE_STATE_SNAPSHOT reserved,
  PAYLOAD_SCHEMA_URI rejected), a 7-event runnable correlation example
  corpus, and two bad-event anti-laundering fixtures (corpus 23). No schema,
  policy-behavior, or vocabulary change. R1-07: published 2026-07-08 with
  explicit release-authority direction — annotated tag `v1.1.11` on `922f0ca`,
  GitHub release with all eight assets including `SHA256SUMS_v1.1.11.txt`,
  CI green; checksums-only, consistent with v1.1.5 through v1.1.10. Optional
  future work remains S1-11B future-branch roadmap artifact (now informed by
  PR #4's data_ref-enrichment and correlation requirements), adapter-harness
  breadth from real sensor captures, or deployment/container runtime breadth.
- Current-main audit note: the final baseline audit corrected two missed
  current-facing guidance examples to the `v1.1.8` target: the adapter
  `check_compat` invocation and the change-governance manifest rebuild command.
  Published `SHA256SUMS_v1.1.8.txt` and release assets remain unchanged.
- Final closeout note: S1-22 completed a full baseline audit and notes/log
  refresh. Current `main` is clean and pushed at `c814d95`; GitHub CI passed;
  local validation covered the governed kernel gate, examples, release
  manifest/package validation, full pytest, workflow/live gateway smoke tests,
  direct focused validators, package/bundle builders, Docker Compose config
  rendering, stale/secret/generated-artifact scans, and GitHub PR/issue queue
  checks. No baseline blockers remain.
- Documentation freshness note: S1-23 audited the README-linked documentation
  surface on 2026-06-18, refreshed `spec/installation-guide.md` around the
  maintained `configs/` templates and current validation gates, corrected stale
  `beffed3` final-closeout references to `c814d95`, verified tracked
  Markdown/TXT relative links, and found no rogue untracked files outside
  expected ignored local/build outputs.
- Decision of record at the time of S1-24: ZMeta v1.1.10 was the then-current
  formal release target for the
  fielded-safety enforcement baseline (command-altitude denylist completion,
  recursive STATE laundering enforcement with key normalization, adapter
  calibration honesty). It preserves the locked v1.0 schema and does not make
  v1.1.0 concepts valid under `zmeta_version: "1.0"`.
  S1-12C audited the D-012 formal release
  packaging framework and closed D-012. S1-13A audited the stack for semantic
  conformance and stale files, corrected the live compatibility checker and CI
  target to `v1.1.5`, added explicit v1.0/v1.1.0 observation extension boundary
  tests, and closed D-009.
  S1-14 implemented external projection promotion hardening for CoT/JREAP/
  MAVLink state ingress through producer-authority policy, adapter metadata,
  conformance/tests, and operator-tunable reject/warn/degrade/quarantine
  enforcement while preserving Profile L compact handles.
  S1-15A added the risk adjudication semantic baseline: locked/tunable/advisory
  rule classes, bounded policy actions, filterable risk diagnostics, and
  operator override constraints.
  S1-15B conformed the stack to that baseline across policy use limits,
  validator diagnostics, gateway runtime degradation labels, conformance
  fixtures, tests, and audit docs.
  S1-15C cleaned up semantic-contract feedback: Section 14 now defers lossy
  tactical ingress promotion to Section 4.5.1, material risk self-labels and
  safety/promotion override evidence are stronger, and conformance classes now
  cover policy adjudication, external promotion, and risk filtering.
  S1-16A added semantic bad-event fixtures and the shared adapter conformance
  harness, promoted `ZMETA-ADAPTER` and `ZMETA-COT-PROJECTION` to implemented,
  and left broader `ZMETA-SENSOR-ADAPTER` certification planned.
  S1-16B added the kernel-protection doctrine: complete without exhaustive
  mission ontology, a high threshold for future core semantic changes, and
  `FUTURE_EXTENSION` as the non-claimable class for future/reserved/planned
  semantics.
  S1-17A audited the tracked stack against that doctrine, found no live
  schema/runtime/adapter/encoding/vocabulary drift, and promoted full
  kernel-protection conformance to CI, Makefile, and release checklist usage.
  S1-18A added consumer-side accepted-risk filtering with operator presets for
  display, fusion, state, command, autonomy, AAR, and audit intake posture.
  S1-18B completed an end-to-end stack and runtime audit, hardened direct CoT
  egress against malformed state payloads carrying raw observation/evidence
  fields, and verified schema/policy/conformance/examples/gateway/live
  workflow/release-package/bundle-smoke paths.
  R1-02 published `v1.1.6` with source, edge, gateway, release package,
  manifest, notes, validation report, and checksum assets. P1-01 addressed
  partner feedback by documenting external-promotion upgrade responsibilities,
  clarifying that `trust_ref` is policy-scoped evidence rather than
  authenticity proof, strengthening downstream consumer responsibility for
  accepted-risk labels, and adding a policy lint that flags unsafe `ignore`
  settings on material risk. P1-02 added machine-checkable profile-projection
  preservation for `payload.extensions.risk_adjudication` and compact
  `payload.extensions.external_promotion` evidence, strengthened the extension
  registry entry contract with validated projection/risk/security/fixture
  fields, and rebuilt the current-main release manifest and example claim
  hashes. P1-03 added formal human/AI agent change governance through
  `AGENTS.md` and `docs/zmeta_change_governance.md`, linked it from public
  entry points, added downstream clone interoperability limits, and added
  governed release-manifest coverage for process guidance. R1-03 audited the
  current stack for stale release references, ignored local build residue, and
  tracked-source secret/generated-artifact risk; updated active release
  surfaces to v1.1.7; built source, edge, gateway, release package, manifest,
  notes, validation report, and checksum assets for publication.
  P1-04 closed the bearing reference-frame ambiguity: a normative section 6.4
  true-north rule with convert-or-omit, an optional v1.1.0 `bearing.frame`
  marker, the experimental `BEARING_FRAME` registry entry, bad-event and
  adapter-harness enforcement with value-level `expected_values` pinning,
  Kraken heading compensation plus fabricated-SNR removal, Moth fabricated
  omnidirectional-bearing removal, SignalHunter/MAVLink frame-provenance
  audit fixes, and MAVLink null-island, gateway oversize-datagram, and
  rate-limiter runtime guards. The locked v1.0 schema is untouched.
  R1-04A completed the post-release current-reference cleanup after the full
  stack audit: `README.md`, tool examples, the CI compatibility target,
  professional overview, compatibility CLI test, handoff, and worklog now
  point current-facing guidance at `v1.1.8`; historical `v1.1.7` release
  records and published checksum files remain unchanged.
  D-003 remains `OPEN - ROADMAP PLANNED`. D-004 remains closed as removed from
  ZMeta scope. S1-19 closed D-013 and D-014 by adding negative TIME_STATUS age
  diagnostics and compact unknown-integer-key rejection. S1-20 added advisory
  industry-sharing, contributor-authority, conformance, name-use, and
  defensive-publication posture without changing schemas, policy behavior,
  event vocabulary, or the locked v1.0 kernel. S1-21 incorporated post-release
  feedback by clarifying current-main adapter upgrade guidance and recording
  that frame assertions are producer provenance, not proof. S1-22 completed
  the final baseline audit/closeout and updated durable plus local notes.
  S1-23 refreshed README-linked documentation and install guidance. R1-05
  publishes those current-main updates as the v1.1.9 formal patch release.

## Archived Task Sections

Completed task sections S0-01 through R1-05 are archived verbatim in
`docs/zmeta_refinement_worklog_archive.md` (retention pass, 2026-07-15).
Newer session records live in the Current Resume Note above; deferred issues
remain below.

## Deferred Issue Register

### D-001 - MAVLink Adapter README State Payload Drift

- Status: CLOSED
- Discovered during: S0-01 / S0-02 review
- Issue: `adapters/ingress/mavlink/README.md` describes several platform-state
  telemetry values as mapping to `payload.features.*`, while STATE_EVENT
  semantics prohibit raw `features` and the current implementation uses
  quality-style metadata.
- Impact: Documentation drift can encourage future adapter authors to place raw
  telemetry features in STATE_EVENT payloads.
- Proposed follow-up: Docs/adapter cleanup task. Do not change during S0-02
  because this work item is semantic-contract-only.
- S1-08A cleanup: Corrected the MAVLink ingress README to prohibit raw
  `payload.features.*`, raw measurements, observation modality fields,
  observation time windows, and raw data references in STATE_EVENT payloads.
  The README now maps MAVLink state inputs to state-safe fields,
  `payload.quality`, SYSTEM_EVENT status, OBSERVATION_EVENT where a true
  supported modality applies, and lineage. Implementation inspection found no
  STATE_EVENT raw-feature emission, so no D-012 follow-up was needed. D-001 is
  closed.

### D-002 - Contract Hash / Release Hash Follow-Up

- Status: CLOSED
- Discovered during: S0-02
- Issue: Rewriting `spec/semantics-contract.md` changes the normative contract
  hash used by gateway/deployment hash gates.
- Impact: Deployments with `require_contract_hash` or release validation assets
  will need an intentional hash update in a later release task.
- Proposed follow-up: Recompute contract hashes and update release/checklist
  artifacts only when the stack-hardening branch is ready.
- S1-09A coverage: Planned a release-hash strategy that keeps the narrow
  semantic contract hash separate from schema, policy, registry, conformance,
  projection, encoding, precision, release-manifest, and release-bundle hashes.
  The plan recommends `release/zmeta-release-manifest.yaml`, deterministic
  build/validation tooling, deployment gate behavior, and conformance claim hash
  integration. No hashes were recomputed and D-002 remains open pending
  implementation.
- S1-09B coverage: Implemented `spec/release-hash-policy.md`,
  `release/zmeta-release-manifest.yaml`, deterministic build and validation
  tooling, focused tests, optional `--release-manifest` conformance integration,
  and claim hash updates. D-002 remained open pending S1-09C audit.
- S1-09C audit: Verified the release hash policy, manifest structure, artifact
  groups, canonicalization, builder/validator behavior, claim integration,
  gateway-compatible hash behavior, optional conformance integration, and tests.
  Fixed post-checkpoint manifest reproducibility by replacing default current
  git metadata with stable placeholders for committed reference manifests.
  D-002 is closed.

### D-003 - Future Semantics Require Versioned Implementation Branches

- Status: CLOSED - ROADMAP ARTIFACT IMPLEMENTED
- Discovered during: S0-02
- Issue: The rewritten contract defines future candidates for markings,
  integrity, anti-replay, trust, MODEL_STATUS/ASSURANCE_EVENT, PNT integrity,
  UAS identity, coalition export, projection metadata, data nutrition labels,
  and emergency/L0 behavior.
- Impact: These concepts are intentionally not valid event vocabulary yet.
- Proposed follow-up: Create dedicated versioned prompts for schema, policy,
  adapter/gateway, encoding, examples, and conformance implementation after
  approval of each extension branch.
- S1-11A coverage: Planned the future versioned semantic branch roadmap,
  candidate inventory, sequencing, dependency map, extension-registry
  interaction, conformance-class interaction, release/hash impact, and standard
  Sx-A/Sx-B/Sx-C implementation pattern. No branch was implemented and no
  future vocabulary became valid.
- S1-26 coverage (2026-07-08): S1-11B is implemented —
  `spec/future-branch-roadmap.yaml` / `.md` record all candidates with
  status, dependencies, required surfaces, recorded field evidence, and
  promotion tripwires, validated by `tools/validate_future_roadmap.py` and
  registered in the release manifest. The S1-11A Section M closure condition
  (a machine-readable roadmap/governance artifact sufficient to track future
  branch work individually) is now met.
- Resolution (2026-07-08): the maintainer approved closure after the v1.1.12
  publication (R1-08). The future-branch roadmap artifact, the extension
  registry, and the promotion evidence bar in `spec/extension-registry.md`
  now track all future versioned-branch work individually; the leak
  prevention D-003 existed for is enforced by CI kernel conformance, the
  registry validators, and the roadmap status-leakage check. Reserved,
  proposed, and future concepts remain invalid vocabulary; any future branch
  still requires its own Sx-A/Sx-B/Sx-C cycle, the evidence bar, and
  explicit maintainer approval.

### D-004 - Out-of-Scope Artifact Set

- Status: CLOSED - REMOVED FROM ZMETA SCOPE
- Discovered during: S0-02 research review alignment
- Issue: D-004 was determined to be outside the ZMeta semantic standard.
- Impact: Keeping this issue active would risk pulling organizational artifact
  scope into a semantic data standard.
- Resolution: S1-10P removed D-004 from active ZMeta scope. ZMeta will remain
  focused on event semantics, profiles, adapters, encodings, validation,
  conformance, and release baselines.

### D-005 - Profile Projection Preservation Coverage Gap

- Status: CLOSED
- Discovered during: S0-03
- Issue: The stack enforces profile event-type legality and supports optional
  field stripping, compact Profile L encoding, and timing-based confidence
  degradation, but there is not yet a conformance suite proving that H/M/L
  projections preserve identity, lineage, units, confidence monotonicity, TTL,
  and semantic meaning across thinning.
- Impact: Profile L/M/H exporters could accidentally pass schema validation
  while still reinterpreting or over-trusting thinned state.
- Resolution: S1-02B added a sidecar field catalog, source/projected projection
  fixtures, standalone validator CLI, compact/protobuf decoded-equivalence
  fixture coverage, opt-in conformance runner integration, and regression tests.
- Audit: S1-02C verified fixture breadth, validator behavior, failure code
  stability, docs alignment, and absence of schema/contract drift.

### D-006 - Extension Registry Artifact Missing

- Status: CLOSED
- Discovered during: S0-03
- Issue: The contract and schema README reserve future subtype and modality
  names by prose, but the repository does not yet contain a durable extension
  registry artifact with status, ownership, collision rules, and adoption
  requirements.
- Impact: Future prompts could add extension vocabulary inconsistently or make
  reserved names appear valid before a version branch is approved.
- S1-03A coverage: Planned `spec/extension-registry.md`,
  `spec/extension-registry.yaml`, validation tooling, initial entries, status
  model, category model, collision rules, and adoption requirements.
- S1-03B coverage: Implemented the human-readable registry, machine-readable
  registry, validator CLI, optional conformance flag, tests, and docs
  integration. Existing v1.1.0 entries are experimental; future entries are
  reserved/proposed.
- S1-03C audit: Confirmed registry shape, status/category semantics, version
  boundary checks, reserved/proposed invalidity, tests, documentation, and
  optional conformance integration. D-006 is closed.

### D-007 - Encoding Negative Validation Gap

- Status: CLOSED
- Discovered during: S0-03
- Issue: Compact and protobuf roundtrip coverage exists, and the gateway
  decodes binary encodings before validation, but there are not explicit
  invalid-after-decode fixtures for compact and protobuf inputs.
- Impact: The "encoding is not semantic authority" rule is harder to regression
  test across future encoding changes.
- S1-02B coverage: Added compact/protobuf projection fixtures where decoded JSON
  is schema-valid but projection-invalid, proving encoding does not override
  projection semantics.
- S1-02C audit: Confirmed compact/protobuf remain encoding projections only and
  decoded JSON is the validation authority.
- S1-05A coverage: Planned a dedicated encoding-negative fixture strategy,
  validator/tooling approach, compact/protobuf negative categories,
  gateway/CLI path coverage, policy/context model, and conformance-class impact
  recommendations.
- S1-05B coverage: Implemented `conformance/encoding-negative/` fixtures,
  standalone validator CLI, opt-in conformance runner integration, focused
  compact/protobuf/gateway tests, and class evidence updates for compact CBOR
  and protobuf projection.
- S1-05C audit: Verified fixture breadth, stable failure codes, validator
  behavior, gateway/CLI parity, opt-in conformance integration,
  conformance-class evidence, and absence of schema/contract/registry drift.
  D-007 is closed.

### D-008 - Conformance Class Manifest Missing

- Status: CLOSED
- Discovered during: S0-03
- Issue: The semantic contract defines ZMETA-CORE, ZMETA-PROFILE-L/M/H,
  ZMETA-ADAPTER, ZMETA-GATEWAY, ZMETA-COT-PROJECTION,
  ZMETA-AI-PROVENANCE, ZMETA-COALITION-EXPORT, ZMETA-MESH-TRUST, and
  ZMETA-REPLAY classes, but the repo does not yet provide a machine-readable
  class claim/test matrix.
- Impact: Implementations can run tests, but they cannot yet make precise,
  repeatable conformance claims by class.
- S1-04A coverage: Planned `spec/conformance-classes.md`,
  `conformance/conformance_classes.yaml`, example claim files, standalone
  validation tooling, focused tests, optional conformance runner integration,
  class status model, claim model, dependencies, required test mappings, and
  S1-04B implementation path.
- S1-04B coverage: Implemented `spec/conformance-classes.md`,
  `conformance/conformance_classes.yaml`, example claim files, standalone
  validation tooling, focused tests, optional conformance runner integration,
  class status model, claim model, dependencies, and required test mappings.
- S1-04C audit: Verified class record shape, status semantics, claim
  dependency/evidence enforcement, future/reserved/planned non-claimability,
  partial-class overclaim protection, docs alignment, optional conformance
  integration, and absence of schema/contract/registry drift. D-008 is closed.

### D-009 - v1.0/v1.1 Observation Extension Boundary Needs Explicit Tests

- Status: CLOSED
- Discovered during: S1-01A
- Issue: v1.0 intentionally allows EO, IR, ACOUSTIC, and NETWORK observation
  subtype names with generic `features`, and also allows generic `quality`,
  `data_ref`, and `data_refs` structures. v1.1.0 formalizes stricter feature,
  quality, and data-reference contracts for some of those same field names.
- Impact: Integrators may confuse "structurally valid generic v1.0 extension"
  with "semantically adopted v1.1.0 feature contract" unless tests/docs make the
  boundary explicit.
- Proposed follow-up: Add boundary documentation/tests during extension registry
  or conformance-class work. Do not treat this as a v1.0 schema defect.
- S1-13A coverage: Added explicit
  `gateway/tests/test_schema_version_discrimination.py` cases proving that
  structurally valid generic v1.0 observation extension fields do not adopt the
  stricter v1.1.0 EO/ACOUSTIC feature contracts, structured quality contract,
  or formal data-reference contract. D-009 is closed without schema,
  contract, policy, registry, adapter, encoding, or vocabulary changes.

### D-010 - Profile Precision / Quantization Policy Floors

- Status: CLOSED
- Discovered during: S1-02C
- Issue: S1-02B enforces precision non-increase for profile projection, but it
  does not define operational precision floors or quantization requirements for
  Profile M/L by field, mission, or packet budget.
- Impact: Projection conformance prevents invented precision, but exporters do
  not yet have a normative target for how coarse Profile M/L latitude,
  longitude, altitude, heading, speed, bearing, RF metrics, or timing values
  should become under specific operational budgets.
- Proposed follow-up: Define mission/profile-specific quantization floors and
  packet-budget policy after representative Profile L/M traffic and operational
  requirements are available.
- S1-06A coverage: Planned precision ceilings, utility floors, quantization
  steps, conservative rounding directions, packet-budget interaction, policy
  artifacts, fixtures, validator behavior, gateway/exporter approach, optional
  conformance integration, and S1-06B/S1-06C path. D-010 remains open until
  implementation and audit.
- S1-06B coverage: Implemented the reference precision policy artifact,
  source/projected fixture suite, standalone validator, focused tests, optional
  `--precision-policy` conformance runner flag, and class/claim evidence
  updates. D-010 remains open as `OPEN - IMPLEMENTED PENDING S1-06C AUDIT`.
- S1-06C audit: Verified policy quality, field-family coverage, Profile H/M/L
  behavior, conservative rounding, fixture coverage, validator behavior,
  packet-budget guardrails, projection interaction, optional conformance
  integration, conformance-class evidence, and absence of schema/contract/
  registry/vocabulary drift. D-010 is closed.

### D-011 - Crosswalk TAKEOFF Mention Cleanup

- Status: CLOSED
- Discovered during: S1-03A / S1-03B registry planning and implementation
- Issue: `docs/zmeta_contract_to_stack_crosswalk.md` mentions `TAKEOFF` in one
  v1.1.0 expanded-tasking row, but the v1.1.0 schema, schema README, examples,
  tests, and extension registry do not define `TAKEOFF`.
- Impact: The typo could confuse future tasking-extension prompts into treating
  `TAKEOFF` as existing or planned vocabulary.
- Proposed follow-up: Clean up the crosswalk row in a narrow docs task or
  during S1-03C audit if maintainers want audit cleanup to include confirmed
  typo fixes. Do not add `TAKEOFF` to current schemas or registry unless a
  future versioned task explicitly proposes it.
- S1-03C audit: Added validator and test coverage proving `TAKEOFF` remains
  invalid under v1.0/v1.1.0 and fails registry validation if it appears in a
  current schema enum/const. The crosswalk typo itself remains open for a narrow
  docs cleanup task.
- S1-07A cleanup: Corrected the crosswalk row to remove `TAKEOFF` and list only
  the actual supported v1.1.0 expanded task values. The remaining `TAKEOFF`
  references are invalidity guards or historical cleanup notes. `TAKEOFF`
  remains invalid current vocabulary, and no schema or extension registry
  artifacts were changed. D-011 is closed.

### D-012 - Formal Release Tag, Signature, and Attestation Packaging

- Status: CLOSED
- Discovered during: S1-09C
- Issue: The S1-09B/S1-09C reference hardening-baseline manifest is
  reproducible and sufficient to close D-002, but it is not a formal tagged
  release package with signed artifacts, post-release claim attestations, and
  final release commit metadata.
- Impact: Deployments can validate the governed reference baseline now, but a
  public or operational release may still need a tagged release, release notes,
  validation report, checksums, signatures, and post-release claim attestations.
- Proposed follow-up: Plan and implement formal release tag, signature, and
  attestation packaging when the hardened stack is ready for a published
  release. Do not reopen D-002 for this packaging work.
- S1-12A coverage: Planned the formal release artifact model, release state
  model, tag naming, signing strategy, attestation/provenance contents, key and
  secret handling rules, formal workflow, consumer verification workflow,
  S1-12B tooling path, S1-12B test strategy, and S1-12C closure strategy. No
  signatures, keys, tags, schemas, release manifests, validators, runtime code,
  or vocabulary were changed.
- S1-12B coverage: Implemented the release signing/attestation specification,
  release package templates, no-signature package builder, package validator,
  no-secret scanner, optional conformance flag, focused tests, docs updates,
  and release manifest `release_packaging` group. No real tags, signatures,
  keys, secrets, schemas, semantic contract text, extension registry entries,
  conformance class status, gateway runtime behavior, adapters, codecs, or
  event vocabulary were changed.
- S1-12C audit: Verified release packaging behavior, template safety,
  no-secret checks, generated package validation, optional conformance
  integration, release manifest validity, and absence of semantic/vocabulary
  drift. Removed D-012 from open-issue defaults after closure. D-012 is closed.
- R1-01 publication: Published `v1.1.5` from commit
  `d4d406b43a705ca5b7a314e1d5388c3ca39c750a` with release notes, validation
  report, release manifest, release package zip, edge/gateway/source bundles,
  and checksum manifest. No detached signatures were attached because no
  approved local signing key was available. D-012 remains closed because the
  packaging framework is implemented and audited; future detached signatures are
  a release-authority operation, not a reopened baseline-hardening issue.

### D-013 - Timing-Freshness Negative-Age Clamp Hides Producer Clock Anomalies

- Status: CLOSED
- Discovered during: P1-04 code-review lead verification (verified line by
  line; deferred because the fix needs new semantic surface)
- Issue: `gateway/src/validators.py:1430` clamps the event-versus-TIME_STATUS
  age with `max(0.0, ...)`, so a negative age (event timestamp earlier than
  the TIME_STATUS reference would allow) validates as "fresh". This conflates
  benign out-of-order delivery with producer clock anomalies. Freshness
  validation compares only producer-supplied timestamps with each other, so a
  self-consistently wrong producer clock validates cleanly. No existing
  violation code covers negative age (current codes:
  `TIMING_STATUS_MISSING`/`STALE`/`UNSYNCED`/`HOLDOVER_NON_MONOTONIC`), and
  contract section 5.10 locks timing semantics in v1.0.
- Impact: A producer with a skewed or manipulated clock can present stale or
  future-dated observations as fresh, and the gateway has no diagnostic label
  for the anomaly.
- Proposed follow-up: New `TIMING_STATUS_AGE_NEGATIVE` warn code, a
  `max_negative_age_ms` policy knob, and an optional `t_receive` plausibility
  check, implemented as a governed Class B/D change with conformance fixtures.
  Not implemented in P1-04 because it adds violation-code vocabulary and
  policy surface to locked v1.0 timing semantics.
- S1-19 closure: Implemented the governed diagnostic and policy surface.
  Validators now preserve raw negative age, tolerate only profile-configured
  small negative intervals, and emit `TIMING_STATUS_AGE_NEGATIVE` with timing
  risk labels beyond tolerance. Default reference policy warns; deployments may
  tune to reject or degrade. Added schema/policy reason-code coverage, compact
  reason-code mapping, focused tests, and core conformance coverage. The
  optional `t_receive` plausibility check was not added because gateway
  `t_receive` stamping happens after inbound validation and is latency/AAR
  metadata rather than producer timing authority.

### D-014 - Compact Codec Degrades Unknown Integer Payload Keys on Re-Encode

- Status: CLOSED
- Discovered during: P1-04 code-review lead verification (verified line by
  line; deferred because the fix needs spec text and a fixture decision)
- Issue: `zmeta_compact.py` decode converts unknown integer payload keys to
  `str(key)`, while encode passes string keys through unchanged. A
  decode-then-re-encode cycle therefore degrades a future integer key `99` to
  the string key `"99"` on the wire. `spec/compact-binary-mapping.md` is
  silent on unknown integer keys, and no encoding-negative fixture covers the
  path.
- Impact: Future compact-mapping key assignments silently lose their compact
  form through any decode/re-encode relay, and the degradation cannot be
  distinguished from a producer that genuinely sent the string key `"99"`.
- Proposed follow-up: Add spec text stating unknown integer keys MUST be
  rejected at decode, add a compact must-fail encoding-negative fixture, and
  align the decoder, as a governed Class B change. Rejection is preferred over
  re-mapping because re-mapping cannot disambiguate a genuine string key
  `"99"` from a degraded integer key 99.
- S1-19 closure: Implemented compact v1 decode rejection for unknown integer
  keys in governed compact maps, added spec text, preserved string extension
  keys, and added a generated encoding-negative fixture that fails before
  schema/policy validation as `ENCODE_NEGATIVE_UNKNOWN_COMPACT_KEY`.
