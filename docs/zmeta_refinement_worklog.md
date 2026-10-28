# ZMeta Refinement Worklog

## Current Resume Note

- Last updated: 2026-10-27 (v1.1.27 published)
- **2026-10-27 (v1.1.27 published).** The cut commit 3e692ff on `develop`;
  `main` moved to it without a checkout (`git branch -f`, after the
  ancestor check), so no tracked file was re-smudged between signing and
  upload; annotated tag `v1.1.27` on 3e692ff; `develop`, `main` and the tag
  pushed together in one atomic push on the maintainer's typed go of
  2026-10-27 ("you have my go, if all checks out and is green you can cut
  the commit, version tag and push"). GitHub CI completed with success for
  the release commit on develop, main and the tag, the first green
  `develop` run since the v1.1.26 cut. The GitHub release, on his typed
  word of the same evening ("if all is green, lets push forward"), carries
  seventeen assets, the v1.1.26 set: the four zips, the manifest, the
  notes, the validation report and `SHA256SUMS_v1.1.27.txt`, a detached
  signature for each of the eight, and the public key
  `ZMETA_RELEASE_SIGNING_KEY_v1.1.27.asc`. Verified as published: every
  asset downloaded from the release into a clean directory, `sha256sum -c`
  over the downloaded checksum file passed for all seven entries, the eight
  downloaded signatures verified as good against the Incept.IO ZMeta
  release signing key with the Gpg4win gpg, the downloaded key file
  imported into an empty keyring verified the downloaded checksum signature
  there, and all seventeen downloaded assets are byte-identical to the
  local copies, the tracked ones to the committed blobs. Before the
  signing, an independent three-reader verification of the prepared tree
  found one false sentence in the notes and the README (that well-formed
  CoT output is byte-identical under both profiles, which the `cds` stale
  cap contradicts); it was corrected and the bundles, the package and the
  checksums rebuilt before any signature was made. The battery with the
  signed set in place read 2022 passed, 3 skipped.
- **2026-10-27 (v1.1.27 cut: the 7.6 `last_seen_ts` definition, the
  section 22 class table row, the CoT egress hardening, the failure-modes
  honesty fix, the strict command posture variants, two registry waves and
  the October records waves).** On the maintainer's direction of
  2026-10-27, given in this repository's session ("please review and
  either concur and cut or let me know what issues arise for us to fix",
  after his option B of 2026-10-27: the cut waits for the 7.6 branch and
  lands by 2026-10-31), with the merge of `exp/last-seen-ts-7-6` (dcf3428,
  on his typed sentence of 2026-10-27 in the team-account session)
  re-verified here first: the kernel gate's eleven expected
  release-manifest lines and nothing else, examples 51 of 51, the lock
  baseline 5 of 5, the battery 13 failed in the release-pin set, 2,011
  passed, 1 skipped, `git diff --check` clean. `develop` is cut whole as
  v1.1.27, sixteen first-parent merges since v1.1.26. The cut followed
  `RELEASE_CHECKLIST.md`: the governed baseline regenerated from the
  v1.1.26 manifest before the bump; the release identity bumped across
  every current-facing surface the v1.1.26 cut touched; the manifest
  rebuilt with `--update-claims`, after which the kernel gate reads clean
  and the generated governance sentence names `conformance/must-pass.jsonl`
  beside the contract, the registry and the two policy variants, as the
  corrected vector requires; the notes and the validation report written;
  the bundles, the formal package and the checksums built; the retention
  pass moved the 2026-08-23 through 2026-09-29 session records to the
  archive, wrote the handoff's new state (the 2026-10-12 state had counted
  thirteen merges and stands as written below it) and corrected this
  note's two "merge pending" leads, the D1 and D2 items of the cut
  preparation, fixed here on the maintainer's choice of 2026-10-27; and the
  handoff books the follow-ups the 7.6 definition's reviews left for the
  next records pass: the relation check with its own failing control, the
  two inline test fixtures that carry the old relation
  (`gateway/tests/test_lineage_semantics.py`,
  `tools/test_workflow_end_to_end.py`), the guidance file's contract line
  citations, and the "follow-up work for the next records pass" wording of
  the 2026-10-27 changelog entry, now a booking. The live runtime harnesses
  and the Docker build and run were exercised because gateway and adapter
  code changed. Validation at the cut is in
  `release/VALIDATION_REPORT_v1.1.27.md`. The signing, tagging, pushing and
  publishing steps are recorded in the entry that follows the cut commit,
  each on the maintainer's own typed word.
- **2026-10-27 (the 7.6 `last_seen_ts` definition, `exp/last-seen-ts-7-6`;
  merged into `develop` as dcf3428 on 2026-10-27).** On the maintainer's adoption of the
  sentence (2026-10-25, decision 4), his choice to correct the examples rather
  than loosen it (2026-10-27), and his concurrence that a first definition of
  a listed, undefined field is a contract 2.1 patch (2026-10-27): one bullet
  added to 7.6's Fusion rules, four FUSION examples and one must-pass
  conformance vector corrected to their member observation's `event.ts`, the
  lock anchor moved with a dated note. Negative control: the anchor test seen
  failing with the sentence in and the anchor unmoved, then green after the
  move. The sentence states the reference projector's in-order behaviour; its
  late-input stamping is a question for the relation check, which no validator
  runs yet and which is follow-up work for the next records pass, with its own
  failing control.
- **2026-10-23 (the CoT projection guards, `exp/cot-projection-guards-2026-10`;
  merged into `develop` as 9157ce3 on 2026-10-24).** On the maintainer's go of
  2026-10-19, after a read of what a consumer that translates a dialect
  itself and feeds the result straight to the projection would send: a
  position outside the schema's bounds now refuses (`_within_position_bounds`,
  after the point-value checks), and a callsign or uid longer than the new
  `max_name_chars` setting (default 256) refuses rather than cuts, the
  derived `Track <uid>` callsign counted as written. The read's first case,
  a character XML 1.0 forbids in an identity attribute, was found already
  closed on `develop` by the 2026-10-01 hardening (refused under `cds`
  since v1.1.26; open at v1.1.25 and on the standard path at v1.1.26), so
  the branch adds no code for it and records the per-tag state instead.
  Fourteen tests, run first against develop d1a503d with only the name
  constant defined there: twelve tests failed and the two boundary cases
  passed, the positive control; every example `STATE_EVENT` projected byte
  for byte the same by the `develop` module and the branch module under the
  standard profile, with and without
  a `how`, and under `cds` with the projection instant beside each event's
  time, and a mutated event (lat 91) differed as the comparison's own
  control. `max_name_chars` is a known `cds` key; anything but a positive
  integer is a configuration error under every profile. Found on the way
  and not changed here: a `track_id` that is not text raises out of `_esc`
  at every tag, where the documented signal is `None`; put to the
  maintainer with the branch. The independent Opus 5.5 review (a fresh
  context, with a seeded off-by-one in a control copy of the adapter, which
  it found) returned three blocking items, all applied: the position bound
  compared through a float, so a Decimal or numeric text a hair past the
  bound passed and left as written, and `cds` then rewrote it (now an exact
  Decimal comparison, with tests); the first negative-control run had failed
  the name-bound tests for a missing constant, not a missing guard, and the
  records had counted it (re-run with the constant defined; the counts
  above); the doctrine entry gave v1.1.25 a `cds` path it does not have. Its
  non-blocking items applied: the hostile fallback runs before the bound
  (README and a test); the bound counts code points; a fielded figure removed
  from a public comment and, after the re-read, from the doctrine entry,
  whether it may be public being his; two formatting lines. Put to the maintainer, not
  changed: a `track_id` that is not text raises out of `_esc`; a present null
  callsign writes `None`; an integer beyond float range raises in the
  point-value check; and `cds` rewrites an in-range Decimal through a float
  (`_plain_decimal`); all four predate the branch. A Sonnet 5.5 factual pass
  over the records found the test count wrong and the v1.1.25 "both paths"
  wording loose (both corrected), called the `cds` byte-for-byte comparison
  weak (how many examples emit under `cds` depends on the instant chosen;
  at ten seconds past each event's time, one), and could not verify six
  claims that rest on private records or runs outside its scope. A focused Opus 5.5
  re-read of the review answers closed the three items, reproduced the
  control itself, and found two overclaims in the records, corrected here.
- **2026-10-12 (records wave `wave/records-pass-2026-10-12`; no behavior
  change).** `wave/records-gaps-2026-10` (456f7f7) merged into `develop` as
  0231151 on the maintainer's go of 2026-10-11 and was pushed; the kernel
  gate and the lock tests ran on the merged tree first (the nine
  release-manifest mismatch lines of the recorded band; lock tests 5
  passed; examples 51 of 51; roadmap ok). `develop` was thirteen
  first-parent merges ahead of `main` before this wave, and its contract hash differs from
  v1.1.26's until the next cut regenerates the manifest. This wave books,
  for the maintainer, four tensions from the downstream answers of
  2026-10-05 to 2026-10-12 (doctrine F4-01 to F4-04: a deterministic
  detection's class; cooperative broadcasts received by relay against the
  routing table, the crosswalk and contract 24.4, guidance gap (z); a
  shipped adapter stamping send time against 5.1; in-place promotion caps
  against 4.2 and 3.4), guidance gap (af), the handoff's state lines, a dated
  correction to the handoff's `translate:` sentence, and two documentation
  corrections: the track projector README and
  `adapters/AUTHORING.md` said `identity_paths` takes `(label,
  dotted.path)` pairs added to the stock pair, where the code takes tuples
  of keys and replaces the stock pair (found while ruling on a downstream pack on
  2026-10-09).
- **2026-10-07 (records wave `wave/records-gaps-2026-10`; no behavior
  change; prepared on the maintainer's go of 2026-10-07 for the
  maintainer's merge).** The wave makes two bookings. Guidance gap (ae): FUSION_EVENT has no
  governed validity window; both schema lanes define `valid_for_ms` on
  TRACK_STATE and on commands only and the FUSION payload is open, so a
  producer's `valid_for_ms` on a FUSION_EVENT validates as an ungoverned
  key with no definition and no type check, which one deployment's producer
  wrote when the question was asked; the handoff records, as a reading and
  not a ruling, that a consumer ages a fusion estimate by its own labelled
  policy and that a producer's window goes under a namespaced vendor key
  until a second independent implementation needs a governed one, and it
  names two things for the maintainer to weigh (the path-keyed projection
  guard a vendor key would lose; FusionPayload's lack of an `extensions`
  member). The advisory
  crosswalk's `geofence_alert` row said an inference derives "from track
  state or observations", while `policy/lineage.yaml` admits only
  OBSERVATION_EVENT parents for an inference; the row now says the claim
  cites observations and that a consulted track is referenced by value in
  the claim, as the correlation pattern does. Booked 2026-08-23 as tension 1
  of `docs/zmeta_ontology_reference.md` section 14, and corrected in the
  next entry: contract section 22's class table names ZMETA-GATEWAY where
  the conformance manifest's class is ZMETA-GATEWAY-REFERENCE, and
  `tools/validate_conformance_classes.py` refuses the table's name. An
  independent read of the first draft found twelve items, corrected before
  the merge: 13.3 names no field for the TTL (10.7 and 14 name the
  STATE_EVENT's `valid_for_ms`); "never as `valid_for_ms`" was a ruling
  without its label; the entry sat under the 2026-10-01 lead; the class-table
  item was already booked; the projection guard a vendor key would lose; the
  correlation pattern's by-value reference for the crosswalk row; and six
  wording points.
- **2026-10-07, same wave (Class B, semantic contract and its lock
  anchor; no behavior change).** On the maintainer's go of 2026-10-07 the section
  22 class table names `ZMETA-GATEWAY-REFERENCE` in place of
  `ZMETA-GATEWAY`, the id the conformance manifest defines and the claims
  validator accepts; the manifest and the validator stand. The tension
  booked 2026-08-23 (ontology reference, section 14, tension 1) carries a
  dated resolution. It is the first edit to `spec/semantics-contract.md`
  since v1.1.20: the manifest's `semantic_contract_hash` is not
  regenerated on the wave (the cut regenerates it, as for every change
  since v1.1.26), so the kernel gate's release-manifest mismatch lines
  grow from six to nine on this branch; nothing else in the gates
  changes beyond the bundle line's computed value. The lock-baseline anchor on the contract text
  (`gateway/tests/test_v1_lock_baseline.py`, CONTRACT_SHA256) moved with
  the edit under the same go, with a dated note beside it, as the
  2026-08-03 move did; the full battery on the branch reads 13 failed
  (the release-pin band), 1997 passed, 1 skipped; kernel gate 9
  `RELEASE_MANIFEST_*` lines; examples 51 of 51; roadmap ok 22;
  `git diff --check` clean. An independent read
  precedes any merge.
- **2026-10-02 (records wave `wave/records-gateway-findings-2026-10-02`; no
  behavior change).** An independent review of unmerged gateway work
  reported two behaviors of the gateway that are older than that work.
  Both were reproduced on the integration line before they were written
  down, through the real `main()` receive loop with the two sockets
  replaced. At profiles M and H: a command with `event_id` X is forwarded,
  and a FUSION_EVENT citing X is refused `LINEAGE_PARENT_TYPE_INVALID`;
  with an OBSERVATION_EVENT reusing X sent between them, the observation
  and the fusion are both forwarded and no diagnostic is emitted. At
  profile L: one `event_id` sent 40 times as a command with a new
  `task_id` each time, each copy carrying a distinct use token and reason
  code of about 1,000 characters, gave 40 forwarded commands and one
  command-evidence entry holding 40 prohibited-use tokens and 40 reason
  codes, 80,380 characters. The exclusion of commands from the `event_id`
  cache is why a reused id is forwarded when its first use was a command;
  for other event types the cache holds an id for 300 s. The validation
  state keeps the latest type of an id, and the command-evidence index
  unions labels with no bound on an entry. Recorded as handoff item 10
  with three questions. No code changed: both arise from how the gateway
  treats a command's `event_id`. An independent check of the first draft
  of this record found it inexact in four places, corrected before the
  merge: the entry was said to grow with every copy, where it gains only
  labels it does not hold; the exclusion was called the cause of both
  results, where the overwrite and the growth have their own; "on the
  command path" did not fit the first result as worded; and the draft
  left out what the repository already records, handoff item 7, the
  v1.0.4 release notes and the offline duplicate check.
- **2026-10-02 (records wave `wave/records-findings-2026-10-02`; no behavior
  change).** Two pieces of work on 2026-10-01 asked the documents questions
  they had not been asked: a read of a field sample from a sensor class
  ZMeta has no modality for, and a ruling for a downstream hub on a
  projection token. What they found in this repository is booked here. Five
  guidance gaps, (z) to (ad) in the handoff: the contract and the
  producer-authority policy provide for promoting an external track that
  has no ZMeta parent, and that event can be emitted only by inventing a
  parent id; the unknown-clock convention understates a clock known to be
  far off, and no text covers correcting a known offset; the documents do
  not say whether a sensor's own track is an external report; nothing
  carries how a position was derived; TIME_STATUS has no declared place for
  the basis of its bound. Record defects corrected in five places: the C1
  status table (C1-04 was decided on 2026-08-26 and still showed open), the
  "ground radar is 2-D" generalisation in doctrine A1-02 (a dated note, the
  entry left as written) and in the ADS-B adapter README, and the adapter
  index rows for the CoT and KLV templates, which named the wire format
  where both templates take an already-decoded dict. An independent check
  of the first draft of this wave found three inaccurate sentences and
  several omissions, all corrected before the merge. The parentless case
  had been called impossible to emit, where the schemas require a parent
  id and cannot check that it resolves. The ADS-B adapter had been said to
  use its own clock, where it uses the snapshot's. "No text says" had been
  written of re-stamping `event.ts`, where contract 5.1 and doctrine F1-01
  speak to it. Two statements were checked by running the validator on both
  lanes: a shipped STATE example with its lineage removed is refused, and a
  TIME_STATUS with an undeclared `est_error_basis` member is accepted.
- **2026-10-01 (CoT `how` shape, `exp/cot-how-shape`).** The independent
  check of the day's `how` evidence noted that the standard profile does
  not validate the configured value. Four tests were written first; the
  two refusal tests failed against the unchanged adapter (an empty string
  was written as `how=""`, and `5` and `True` were written as text), and
  the two that guard against refusing too much passed, as they should.
  `validate_cot_config` now refuses, under every profile, a `how` that is
  not one ASCII letter or digit followed by dash-separated groups of ASCII
  letters or digits. That is the ASCII letters-and-digits subset of the CoT
  schema's own pattern, which also admits non-ASCII letters and a few
  symbols. The gateway reports it at startup; the adapter returns nothing
  for a config it cannot run, as it already did for other config errors.
  Absent or null still omits the attribute, so the open question in
  doctrine H1-05, what the adapter does when nothing is configured, is
  untouched. An independent review then found a way past the check for a
  program calling the adapter directly (a `str` subclass whose text differs
  from what was checked), wording that described the rule more loosely than
  the code applies it, and four mutants the tests missed, one of which
  refused `h-g-i-g-o`, a token TAK clients emit. All are closed: the check
  requires exactly a `str`, the wording says ASCII, and the tests name the
  real tokens.
- **2026-10-01 (records wave `wave/records-evidence-2026-10`; no behavior
  change).** Four things were recorded. (1) A downstream implementation
  reported that the CoT base-event schema declares `how` required while
  the standard profile omits it by default. The repository read the schema
  copy and TAK Server's `cotevent.proto` itself and confirmed it; the
  evidence is in doctrine H1-05, the adapter README states the limit, and
  the default is left to the maintainer. An independent check of that
  evidence then read TAK Server's and ATAK's public source and changed two
  things in it: a server does not reject the omission on every path, and
  ATAK fills a missing `how` with `m-g-g`. (2) The gateway's unbounded
  validation state, an open candidate since 2026-07-27, was measured
  (about 3.9 KB held per forwarded event) and brought forward as handoff
  item 8. A first note of it called it newly booked, which was wrong; the
  search behind that note had covered five files. (3) The held dedupe fix
  went through four rounds of independent review on its branch and was
  revised after each, and the handoff now says what the branch does and
  what it leaves to the maintainer. (4) Three answers to downstream
  implementations (on a consumer acting on a producer's vendor-extension
  simulation marker; on conflicting reuse of an `event_id` and on duplicate
  codes; on CoT `how` tokens) were each sent to an independent reviewer
  the same day. All three were upheld with corrections: six, nine and
  five. Two sentences were wrong: that no released text speaks to refusing
  an expired command, when the advisory MQTT guidance does; and that the
  CoT adapter is unchanged between v1.1.25 and v1.1.26, when only the
  standard profile's `how` handling is. The corrections went to each
  recipient; in one case the first answer's overstatement had already been
  copied into the recipient's code comments. Two guidance gaps came out of
  the day and are booked as (x) and (y).
- **2026-10-01 (two audit rounds of the session's own answers; the close).**
  The session answered several dozen questions from downstream
  implementations on what the standard says. Three independent reviewers
  then checked 101 statements in those answers against the v1.1.26 text and
  upheld 58; of the 43 not upheld, 5 were wrong, 9 went beyond the
  documents, 15 cited the wrong text and 14 were incomplete. Corrections
  went to each recipient. A second round checked 73 statements in the
  corrections and in eight later answers and upheld 41; the 32 not upheld
  were mostly incomplete, with 1 wrong and 8 beyond the documents, and
  refinements were sent. What the audits found in this repository itself:
  the overstated `translate:` claim (corrected, merge 492a920) and the
  command dedupe window (doctrine E1-06, fix held on
  `exp/command-dedupe-validity`). The working rule taken from it: an answer
  about the standard quotes the text it rests on, says plainly when the
  documents are silent and the answer is a ruling, avoids "never", "only"
  and "must" unless the text uses them, and goes to an independent reader
  before a consumer builds on it. Battery at the close on `develop`: kernel
  gate 6 `RELEASE_MANIFEST_*` lines, examples 51 of 51, roadmap ok 22,
  registry ok 68, `python -m pytest -q` 13 failed (the release-pin set),
  1992 passed, 1 skipped.
- **2026-10-01 (records corrections, `wave/records-corrections-2026-10`).**
  A downstream question (does contract 3.4 bind a parentless observation to
  carry a transform) showed that the wave of 2026-09-28 overstated the
  `translate:` transform as stamped by every shipped ingress adapter. Counted
  on the tree and recounted by an independent reviewer, who corrected the
  first count: of the thirteen shipped ingress adapters, ADS-B and AIS stamp
  none, CoT and JREAP stamp `promote:`, nine stamp `translate:` on events
  with parents, and MAVLink and SAPIENT among them also stamp `promote:`;
  the template directory stamps nothing.
  The registry entry, the roadmap candidate, doctrine U1-02 (a dated
  correction, the original text kept) and the changelog are corrected. The
  roadmap's `model-assurance` candidate notes a producer's model-digest need
  against contract 11.4. Separately, every answer this session gave
  downstream implementations on 2026-10-01 was audited by independent
  reviewers against the v1.1.26 text; the wrong and overreaching ones were
  corrected with their recipients, and the private session record holds the
  list.
- **2026-10-01 (failure-modes honesty, `exp/failure-modes-honesty`).** A
  downstream mapping pass found `configs/README.md` claiming four failure
  modes where the gateway reads one. The shipped edge configs now carry only
  `timing_loss.enabled` and `confidence_reduction_factor`, the gateway warns
  at startup for anything else under `failure_modes`, and
  `gateway/tests/test_failure_modes_honesty.py` (four tests, two mutants
  killed) pins the configs. Doctrine E1-05.
- **2026-10-01 (scope check of the five unreleased waves).** On the
  maintainer's direction that ZMeta stay within its defined scope and that the
  repository's documents decide, three independent reviews (a top-tier scope
  judge, an opus stray-hunter, a sonnet change-class checker) read
  `v1.1.26..7746c68` against the North Star, the design gates, the
  governance, the contract and the registry rules. Verdict: all five waves
  inside scope, three with fixes, none widening the kernel or the governed
  vocabulary. Fixes: the assembly tool replaces only tunable policy files;
  `SEARCH_PATTERN` is risk-relevant with its carrier left to promotion; the
  `cds` documents say the stale cap is new and unseen by the guard; the
  `send_stale` citation is corrected; the new status DECIDED (delegated)
  replaces DECIDED on decisions taken under the delegated go, and E1-03 and
  E1-04 return to OPEN. Nine guidance gaps are booked in the handoff for the
  maintainer.
- **2026-10-01 (two registry records, `wave/registry-candidates-2026-10`).**
  On the maintainer's go of 2026-09-30: `RAW_DATA_ABSENT_STATUS` gains the
  destroyed-with-receipt candidate state and roadmap
  `raw-data-absent-evidence-status` its first evidence; `SEARCH_PATTERN` is
  proposed on SEARCH_BOX. Counts recomputed with the validator's own
  predicates: 68 entries (35 reserved, 19 experimental, 11 proposed, 2
  adopted, 1 rejected), 18 of the 46 reserved and proposed entries under a
  leak probe that can see their vocabulary (the validator's predicates also
  run on `SEARCH_PATTERN`, but only on its name), 67 of 68 with
  `encoding_status: none`; the ontology
  reference and handoff item 6 carry them. Doctrine E1-03 and E1-04.
- **2026-10-01 (the CoT standard-profile hardening, `exp/cot-standard-hardening`).**
  The three items booked by the cds refutation rounds: forbidden characters
  in an identity attribute refuse (as under `cds`) and are replaced in
  `remarks`; point values must be finite numbers, Decimals or wholly numeric
  text; ellipse members must be numbers; a non-numeric or negative
  `default_ce` or `default_le` is a configuration error under every profile.
  A parse-and-shape backstop refuses any output that is not a point and a
  detail. The first draft sanitised the callsign instead of refusing it; three
  existing cds tests, which pin refusal, a finite Decimal and a numeric string
  as earlier rounds decided, failed it, and the draft was narrowed to match
  them. Six new tests; five mutants against the guards were all killed.
- **2026-10-01 (F3-03, F3-04 and F3-05 decided, `wave/cds-f3-2026-10`).** On
  the maintainer's go of 2026-09-30, after a top-tier review whose
  recommendation was taken whole. `stale` under the `cds` profile is the
  earlier of the claim and the window; a lapsed claim is refused and
  counted as `VALIDITY_LAPSED`, or sent with its past stale under
  `lapsed_validity: send_stale`; an asserted affiliation stays refused and
  is counted as `AFFILIATION_ASSERTED`; the window does not enter
  `remarks`; `coalition-release-export` records the 2026-09-29 validation.
  The frozen standard bytes were regenerated, for the fixture's new 300 s
  claim, from the adapter before the change (the regeneration refused to
  run against a changed adapter). Eight mutants against the new rule, the
  option, the config check and the gateway's reason wiring were all
  killed. This closes the booked profile-specific `cot_skip_reasons` token.
- **2026-10-01 (review of `wave/command-authority-2026-10` and its fixes).** A
  three-agent review (an opus code refuter, a sonnet records checker, a
  top-tier judge for the open profile questions) found two majors in the
  assembly tool and its test: an output directory inside the reference
  `policy/` directory was accepted, which changes the reference policy hash
  because the gateway hashes the directory recursively; and the test of the
  reference-directory refusal passed on the occupied-directory check instead.
  Fixed: the tool refuses an output at or under the reference directory, a
  path that is not a directory, a prefix match that does not end at `.` or
  `-`, and an explicit target that is not a policy YAML file; it splits
  `SOURCE=TARGET` on the last `=` and copies the whole reference tree. Each
  refusal test now asserts its own message, the containment test runs on a
  copy of the reference so only that guard can fire, the v1.0 lane is
  pinned, the closed-set evidence test has a reference control, and the
  schema lanes are discovered from `schema/`. Five mutants against the new
  guards were all killed. The pack's enforcement held against every bypass
  the refuter tried: producer-name case and whitespace, the v1.0 lane, a
  self-citation, a subtype that disagrees with `task_type`, and
  non-motivating or prohibited parents. Wording fixes from the records
  check: U1-02's decision now says it takes the positions of the routing's
  five questions as well as its Recommendation, the E1 prose names a
  deployment, contrast constructions are restated, and the em dashes the
  variants inherited from the reference commentary are replaced. 24 tests
  in `gateway/tests/test_command_policy_variants.py`.
- **2026-10-01 (the strict command posture, `wave/command-authority-2026-10`).**
  On the maintainer's go of 2026-09-30, two policy variants and an assembly
  tool. `configs/policy-variants/command-evidence.strict.yaml` sets
  `require_evidence: true` for every task type and `unresolved_parent_mode:
  reject`; `configs/policy-variants/routing.command-origin.yaml` gives the
  automation producers the closed set SCAN_RF and CHANGE_SENSOR_MODE plus every
  SYSTEM_EVENT subtype. `tools/assemble_policy_dir.py` builds a deployment
  policy directory, lints it and prints the hashes. Twenty tests in
  `gateway/tests/test_command_policy_variants.py`: shape pins against the
  reference files and the schema lanes, the pipeline behaviour with the
  reference policy as control (including the shipped 1.1.0 ORBIT and
  RETURN_TO_BASE examples from `retasking-engine`, forwarded by the reference
  and refused by the pack), and the tool's refusals. A mutation pass of seven
  mutants (widening the closed set on one producer, either strict value
  reverted, a system subtype dropped, a misspelled subtype, the overlay step
  removed, shortest-prefix resolution) killed all seven after one test was
  added for nested reference names. Doctrine E1-01 and E1-02. The reference
  `policy/` directory is unchanged. Validation: kernel gate the same 6
  `RELEASE_MANIFEST_*` lines as `develop`; examples 51 of 51; roadmap ok 22;
  policy lint ok; `python -m pytest -q` 13 failed (the release-pin set), 1970
  passed, 1 skipped (the CoT XSD test); `git diff --check` clean.
- **2026-10-01 (doctrine U1-02 decided; the registry wave merges into
  `develop`).** The maintainer's go of 2026-09-30 handed this
  repository's open questions to its own recommendations, as revertible
  decisions. U1-02's five were taken as the routing and its recommendation propose
  them:
  DIALECT_LABEL stays `proposed` with its carrier open and the `translate:`
  lineage transform weighed first; the label's scope is events translated
  into schema-valid ZMeta; one organization's implementations count as
  one instance; the live-versus-recording discriminator is a question for
  a `data_ref` branch; and `event-signing-anti-replay` now depends on
  `canonical-byte-form`. Whether the signing tripwire has fired stays with
  the maintainer. `develop` was merged into the wave first (95c0865); the
  four conflicts were append-append in CHANGELOG, handoff, worklog and
  doctrine log, and each keeps both sides in date order. Validation on the
  wave before the merge: `python tools/validate_conformance.py
  --kernel-gate` 6 `RELEASE_MANIFEST_*` lines, all on the registry and
  roadmap files this wave changes, and no other failure; `python
  tools/validate_examples.py --strict --require-all` 51 of 51; `python
  tools/validate_future_roadmap.py` ok candidates=22; `python -m pytest
  -q` 13 failed (the release-pin set: `test_release_manifest.py` 3,
  `test_release_package.py` 10), 1948 passed, 3 skipped; `git diff
  --check` clean. The release-pin set stays red until the next cut.
## Archived Task Sections

Completed task sections S0-01 through R1-05 are archived verbatim in
`docs/zmeta_refinement_worklog_archive.md` (retention pass, 2026-07-15).
The session records from 2026-08-10 through 2026-08-13 were moved there at
the v1.1.26 retention pass (2026-09-29), and the records from 2026-08-23
through 2026-09-29 (the v1.1.26 cycle) at the v1.1.27 retention pass
(2026-10-27).
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
