# ZMeta Refinement Worklog

## Current Resume Note

- Last updated: 2026-11-14 (the tests branch's seeded-review follow-up;
  the gate's red held to the release pins and the
  typeless AIS event at the reference validator;
  the release facts' seeded-review follow-up;
  the release facts classify the golden CoT
  corpus; the gate runs every stage; AIS records with no
  message type;
  Clause 1's follow-up; three more manifest
  passages; the develop-green
  wording; the gateway README's
  run notes; contract 7.8:
  projections keep `valid_from_ts`;
  the 4.3 clause classified a 2.1 patch;
  contract 4.2 points to 4.5.1; `payload_json`
  under contract 3.5 in the
  protobuf encoding document; the GitHub usage habits in CLAUDE.md;
  `last_seen_ts` named in contract 7.7 and
  refused on a STATE; golden CoT outputs as a conformance artifact;
  the twelve remaining JSON readers refuse a
  repeated member; records: doctrine cycle F10, the SIM1-01
  confirmation and an acoustic evidence item; `observed_at` named in
  contract 7.7 and refused
  on a STATE; the JSON duplicate-key sentence in contract 3.5,
  four tools and the re-anchored guidance citations; the records wave of two
  registry entries, the
  enrichment note and three terminal doctrine statuses; the TAK Protocol
  Version 1 egress adapter before its first contact; the signing tripwire
  re-affirmed not fired; the
  pre-cut dry run; the TAK Protocol Version 1 egress adapter; DECODE_AMBIGUOUS,
  three commits, the third on 2026-11-03; two contract sentences;
  carried-list records pass; heading_deg defined; records pass after 7.6)
- **2026-11-14 (the tests branch's seeded-review follow-up).** A seeded
  review of the branch `wave/precut-tests-2026-11` (an error planted in a
  copy, found; `local/precut_fixes_2026-11-14/p2/review/review_report.md`,
  claude-opus-5-5) gave one BLOCKER, two SHOULD FIX findings and five NITs,
  read here against the branch's own tree under the maintainer's selections
  of 2026-11-14 that opened Option E of the gate change and the AIS records
  with no message type. The BLOCKER is the planted error; the branch's
  CHANGELOG entry gives `SCHEMA_INVALID` for the class key renamed
  `class_name`. The first SHOULD FIX is applied: the helper's eight policy
  checks had a failing control for the semantics check alone. New controls
  refuse the typeless event at profile L
  (`EVENT_TYPE_NOT_ALLOWED_FOR_PROFILE`) and, with one validation state, the
  same event the second time (`EVENT_DUPLICATE`); the helper takes an
  optional state and records an event with no failure in it, as
  `tools/validate.py` does. A third control compares the helper's list of
  checks with the tool's, with whitespace and trailing commas removed and the
  tool's names mapped, so a check left out or given other arguments fails; a
  fourth checks that the schema is the lane's for a known stamp and the union
  schema for an unknown one. The role, timing, lineage, producer-authority
  and routing checks have no behavioural control, since the typeless event
  gives none of them a refusal to show; the class docstring says so. The
  second SHOULD FIX is applied: the handoff called the rename case a rule for
  every branch and then said no rule changes; it now calls it a consequence
  of the test, says that the governance Branching section does not name the
  case, and leaves open whether it should. T5's docstring and the CHANGELOG
  no longer call the rename case "by design". All five NITs are applied. The
  classifier no longer accepts `RELEASE_MANIFEST_SELF_HASH_MISMATCH`: the
  manifest's own hash covers the manifest's content only, so a stale pin does
  not move it, and the line is now rejected. T6b gains a mismatch body with
  text after it, a short hash and a package line with another message before
  the body, for the regex mutants that survived. T5's docstring says "Until
  this change" for the test's earlier judgement, since the test was created
  on 2026-11-14. The helper counts every schema violation as a failure, as
  the tool does. `tools/README.md` is rewrapped. Tests first: with the helper
  unchanged, the duplicate control failed (`reference_violations()` had no
  `state` argument) and the severity control failed (`warn` for a schema
  violation); with the self pattern in place, its T6b case failed. After the
  change the AIS file passed, 138 tests, and the gate file, 30. The new
  source-comparison and lane-schema controls passed on the present helper;
  the branch's mutants are the controls that must see them fail. No rule
  changes, and no changed file is listed in the release manifest, so no pin
  moves. The mutants and the full validation run on the commit under the
  heavy-run lock, and the merge record gives their results.
- **2026-11-14 (the gate's red held to the release pins and the typeless AIS
  event at the reference validator).** Two corrections from the pre-cut range
  review of 2026-11-14 (its S4 and N4), on the branch
  `wave/precut-tests-2026-11`, based on `wave/precut-release-facts-2026-11`.
  S4, under the maintainer's selection of 2026-11-14 that opened Option E of
  the gate change: T5 of `gateway/tests/test_kernel_gate_runs_every_stage.py`
  asserted that a red gate names every stage and that one is not `ok`, so it
  passed when a third stage failed, and a defect inside the two release
  stages that is not a pin was one more line among the hash mismatches. On a
  red gate T5 now calls `_red_beyond_the_pins`, which reports a failing stage
  outside `release_manifest` and `release_package`, a line beginning `FAIL `
  that is not a hash mismatch of a failing one of them, and a failing
  release stage that printed no hash mismatch. The accepted lines are the
  five hash-mismatch codes of `tools/validate_release_manifest.py` (artifact,
  group, top-level, bundle, self) with both values `sha256:` hashes, and the
  package stage's `RELEASE_PACKAGE_MANIFEST_INVALID` lines with the same
  messages, since `tools/validate_release_package.py` validates the manifest
  first and re-reports its issues under that code. The gate's output on this
  branch, measured once (exit 1; `release_manifest` and `release_package`
  red, every other stage `ok`; 114 `FAIL` lines: 57 manifest lines, by code
  30 artifact, 16 group, 10 top-level and 1 bundle, and 57 package lines),
  classifies as the pins alone. Unit controls (T6 to T6e) accept the
  stale-pin shapes and reject a line that is not a hash mismatch (a template
  defect, a missing group or field, an invalid hash algorithm, a hash code
  whose expected value is not a hash, a core-stage line), a listed artifact
  reported missing in both stages' forms, each third stage failing, a pin
  line from a release stage that does not fail, and a failing release stage
  with no line. T5's docstring says that a branch that renames or removes a
  manifest-listed file turns the test red until the cut, by design.
  `tools/README.md` replaces "should read `ok`" with what the test holds.
  N4, under the maintainer's selection of 2026-11-14 that opened the AIS
  records with no message type: the policy-level pass of the typeless event
  rested on a session's own run, and the adapter's test checked the 1.1.0
  schema only. A new class in `adapters/ingress/ais/test_ais_ingress.py`
  loads the reference validators and policy the way the MAVLink and SAPIENT
  suites do and runs the schema check and the eight policy checks in the
  order of `tools/validate.py`; the typeless event passes at profiles H and
  M with no warning, the class key renamed `class_name` is refused as
  `SCHEMA_INVALID` and renamed `Entity_Class` as `OBSERVATION_HAS_IDENTITY`.
  `tools/validate.py --strict` on the same three events gave the same
  verdicts at both profiles. Tests first: with the classifier reduced to
  T5's old judgement, 18 of the gate file's 26 tests failed and T5 and T6
  passed; with the classifier, 26 passed. With the helper reduced to the
  schema check, the two `Entity_Class` controls failed and the other four
  new tests passed; with the policy checks, the AIS file passed, 133 tests.
  No rule changes, and no changed file is listed in the release manifest, so
  no pin moves. The mutants and the full validation run on the commit under
  the heavy-run lock, and the merge record gives their results.
- **2026-11-14 (the release facts' seeded-review follow-up).** A seeded
  review of the branch `wave/precut-release-facts-2026-11` (an error planted
  in a copy, found; `local/precut_fixes_2026-11-14/p1/review/review_report.md`,
  claude-opus-5-5, READY WITH CORRECTIONS) gave two SHOULD FIX findings and
  four NITs, read here against the branch's own tree under the maintainer's
  selection of 2026-11-10 that opened the golden CoT outputs. The first
  SHOULD FIX is the planted error; the branch's comment in
  `tools/release_focus_facts.py` names `ZMETA-COT-PROJECTION`. The second is
  applied: the entry below and the CHANGELOG said that every check between
  cuts reads the committed manifest, while
  `gateway/tests/test_release_manifest.py` and
  `gateway/tests/test_release_package.py` build a manifest from the tree;
  both now say that every check that classified the groups read the
  committed manifest until this change. Three NITs are applied. The
  classification assertions of the exactly-once test now live in a helper,
  `_check_builder_classification`, and a second control runs it on small
  doctored sets, so a deleted assertion fails the test file; the CHANGELOG
  entry now says that the test checks that the golden corpus is a governed
  path; the handoff names the five tests that fail at the cut as the
  release-currency tests that classify the committed manifest's groups,
  apart from the five tests of the paragraph before it, which are about the
  committed manifest itself. One NIT is not applied: the vacuity floor of 20 groups claims only that
  the check is not vacuous, and the golden-path assertion is the one that
  fails when the groups are read from the committed manifest instead of the
  builder. Tests first: with a helper that asserted nothing, the new control
  failed ("no assertion fired"); with the helper, the test file passed, 32
  tests. The body of the branch's first commit keeps the sentence the second
  SHOULD FIX corrects, because local history is not rewritten. The mutants
  and the full validation run on the commit under the heavy-run lock, and
  the merge record gives their results.
- **2026-11-14 (the release facts classify the golden CoT corpus).** A
  correction from the pre-cut range review of 2026-11-14, under the
  maintainer's selection of 2026-11-10 that opened the golden CoT outputs
  (A8). The manifest builder has defined the group `cot_projection_golden`
  since 2026-11-11, and `tools/release_focus_facts.py` classified it as
  neither governed nor ungoverned. Until this change, every check that
  classified the groups read the committed manifest, which does not carry
  the group, so the gap could show only at the cut: after the manifest is
  rebuilt, `governed_paths` raises,
  the README's release-focus sentence cannot be generated, and five
  release-currency tests fail (the review counted four; its verification
  added `test_a_deleted_governed_artifact_is_visible`). The group is now in
  `GOVERNED_GROUPS`, with its reason beside it: the corpus is a required
  fixture of `ZMETA-COT-PROJECTION` (`conformance/conformance_classes.yaml`),
  beside the adapter harness corpus, which is governed, and none of the
  reasons the file gives for an ungoverned group (process, release
  mechanics, tooling source, claims, a derived export, future-only) fits it.
  The existing classification test reads the committed manifest, which
  changes only at a cut, so a new group stays unseen for a release. A new
  test in `gateway/tests/test_release_currency.py` builds the manifest's
  groups from the tree in memory (`build_manifest_data()`, which writes
  nothing) and fails when a group is in neither set or in both, and checks
  that the golden corpus is a governed path; a control shows that the check
  reports an added group and a group placed in both sets, and that
  `governed_paths` raises on the added group. Tests first: before the
  classification the new test failed, naming `cot_projection_golden`, and
  the control passed; after it the test file passed, 31 tests. Branch
  `wave/precut-release-facts-2026-11`. Neither changed file is listed in the
  release manifest, so no pin moves, and the print-only run of
  `tools/release_focus_facts.py` is unchanged. Two items are left to the cut
  commit, because the gate and `gateway/tests/test_release_manifest.py` read
  the committed manifest and an earlier change would add a red line that is
  not a hash mismatch: `cot_projection_golden` in `REQUIRED_GROUPS` of
  `tools/validate_release_manifest.py`, with a decision on a top-level hash
  field, as 9b4ba26 did for `bad_event_corpus` and `adapter_conformance`; and
  the five groups `spec/release-hash-policy.md` does not list
  (`cot_projection_golden`, `bad_event_corpus`, `adapter_conformance`,
  `future_branch_roadmap` and `policy_json_export`). The handoff books both.
  The mutants and the full validation run on the commit under the heavy-run
  lock, and the merge record gives their results.
- **2026-11-14 (the gate runs every stage; Z4 Option E).** On the
  maintainer's selection of 2026-11-14 (his click "Yes, build E" at 16:04:28
  EST in this repository's session), Option E of the team account's read of
  2026-11-12 (Z4) is built. `tools/validate_conformance.py` runs every stage
  it is asked for and exits with the first failing stage's code, the code its
  early exit gave; when a stage fails it prints a `conformance stages:` line
  naming every stage. Between cuts `--kernel-gate` now reads
  `release_manifest` and `release_package` as its only failing stages, so
  "red for the manifest pins alone" is read from the gate's output instead of
  inferred. The release-package tests build their packages from a manifest of
  the tree: eight tests whose negative controls died in the builder before
  their assertions between cuts now run, and the five tests about the
  committed manifest itself stay red until the cut. Every CI validation step
  after the install, the kernel gate among them, runs when an earlier one
  fails, unless the run was cancelled or the install failed; the run stays
  red. Branch `wave/gate-every-stage-2026-11`. The gate
  tool is manifest-listed. Its pin was already stale on develop (4bb6e41,
  2026-11-10) and stays stale until the next cut, so the gate's
  `release_manifest` stage keeps its 57 lines, three of them with a new hash;
  the `release_package` stage, which never ran before, reports the same stale
  pins. Seven new tests in a new file
  (`gateway/tests/test_kernel_gate_runs_every_stage.py`); on develop's gate
  four of the first five failed, the fifth being the success-path control. On
  develop the eight package tests failed in the builder before their
  assertions; now they pass, and the battery's red falls from thirteen tests
  to the five about the committed manifest. Fifteen mutants: eleven on the
  gate against the new tests, and four on the release-package validator
  against the eight repaired tests, which on develop could not be told apart.
  A seeded review (one reviewer, opus at high effort, read only, on a copy
  with one planted error, which it found) returned READY WITH CORRECTIONS;
  its corrections are applied: the core stage's exit stays 1 for any number of
  failing fixtures (recording the count would let 256 failures exit 0 on
  Linux), the end of the run is tested on its own, the exit-status claim is
  narrowed for a stage that raises, the package tests' manifest carries the
  committed release identity, and every CI validation step after the
  install, not only those after the gate, runs when an earlier one fails.
  The mutants ran under the heavy-run lock before the commit, and the twelve
  gate legs, the conformance sub-checks, both live harnesses and the full
  battery run on the commit; the merge record gives their results.
- **2026-11-14 (AIS records with no message type).** On the maintainer's
  selection of 2026-11-14, the AIS ingress adapter reads a position record
  whose message type is absent, on two statements the record makes itself: a
  declared shipborne transceiver class (A or B) and a usable position. It
  infers no type. The selection is his click "All as recommended" at 14:31:34
  EST on the parent session's roll-up of that day (item 14), relayed by the
  parent he named in this repository's session at 15:14:10 EST. The need came
  from zisr-producers' local replay of a record source that drops the type
  and keeps the class: its converter inferred 1 or 18 from the class and
  said so, and this repository's ruling of 2026-11-12 refused the inference
  and named the adapter change as the fix. The event omits `ais_message_type`
  and carries `ais_transceiver_class`. Message 27's not-available encodings
  apply to such a record (`adapters/AUTHORING.md`), so an exact 63 kt is
  dropped; the design brief of the same day had carried it as a declared
  limit, and the AUTHORING rule decided the other way. A typed message is
  translated as before and the class is not read on it. Branch
  `exp/ais-typeless-records-2026-11`, adapter 1.1.0. The two statements
  rule out what the record can rule out and no more (a Class A UTC and date
  response, message 11, also carries a position), so the README says the
  rest rests on the record source's word, and that such a record's position
  has an unknown resolution, since it may be message 27's coarser grid.
  Fifty-four new test cases in one class: the first forty-eight were written
  before the change and sixteen of them failed on the unchanged adapter; six
  came from the review. A seeded review (one reviewer, opus at high effort,
  read only, on a copy with one planted error, which it found) returned READY
  WITH CORRECTIONS; its corrections are applied: the older message 27
  sentences, a refusal row, a Class B case at 63 kt, the MMSI and time cases,
  the record source's word, the resolution, and the class in "What is never
  inferred". The mutants ran under the heavy-run lock before the commit, and
  the twelve gate legs, the conformance sub-checks, both live harnesses and
  the full battery run on the commit; the merge record gives their results.
  The new code sits after `_quality`, so the lines the doctrine review log
  cites (`ais_to_zmeta.py:165-203`) keep their numbers. No schema, policy,
  contract, registry, conformance or manifest-listed file changes.
- **2026-11-12 (Clause 1's follow-up).** The team account's seeded read of
  Clause 1's final text (Z3,
  `local/team_pieces_2026-11-12/c1_final_review.md`, claude-fable-5-2, READY
  WITH CORRECTIONS, its plant found) gave two SHOULD FIX findings, applied
  here under the maintainer's selection of 2026-11-11 that opened Clause 1.
  The `EVENT_DUPLICATE` remediation in `tools/validation_guidance.yaml` now
  carries 4.5.1's "on the accepted event". The 2026-11-11 entry for contract
  4.2 below records a seeded review and a commit (a270f80) that are both of
  2026-11-12; its resume line has read 2026-11-12 since that day's first
  records commit. Its seven NITs change nothing. Branch
  `wave/clause1-followup-2026-11`. A script checks that the remediation
  carries 4.5.1's phrase as the contract has it; one mutant, the old
  remediation restored, failed it. No agent ran: the change is the read's own
  correction. The mutant runs under the heavy-run lock before the commit; the
  twelve gate legs, the conformance sub-checks, both live harnesses and the
  full battery run on it.
- **2026-11-12 (three more manifest passages).** The maintainer selected
  "Amend all four" on 2026-11-12, after the four texts were quoted to him:
  governance :161-162 and :344, AGENTS.md :105-106, and "experimental or wave
  branch" at governance :305. They come from the team account's read of the
  develop-green question (Z4,
  `local/team_pieces_2026-11-12/governance_green_options.md`). Branch
  `wave/governance-manifest-passages-2026-11`. Both files are manifest-listed,
  so their pins join the stale ones until the cut. A script checks each of the
  four approved texts byte for byte and that its old text is gone; four
  mutants, each restoring one old text, failed it on that amendment alone. No
  factual-pass agent ran: the texts are the approved drafts, checked by
  script, on the maintainer's direction of 2026-11-12 to keep usage lean. The
  mutants run under the heavy-run lock before the commit; the twelve gate
  legs, the conformance sub-checks, both live harnesses and the full battery
  run on it.
- **2026-11-12 (the develop-green wording in the governance text).** The
  maintainer selected "Amend the text" on 2026-11-12, after both sentences of
  the Branching section, the measured state of `develop` (the kernel gate 53
  lines and the battery 13 failures, all release-manifest pins) and the other
  options (a pin-tolerant gate, a manifest regenerated at each merge, no
  change) were put to him. Branch `wave/governance-develop-green-2026-11`.
  `docs/zmeta_change_governance.md` :286 and :307 change; the document is
  manifest-listed, so its own pin joins the stale ones until the cut. A script
  checked both amended sentences and the state they describe: every
  kernel-gate failure on `develop` a release-manifest pin, every battery
  failure in the two release test files. Two mutants of the text each failed
  it on the check named for them. A seeded factual pass found the error
  planted for it; its one note, a line range that named an unchanged line, is
  corrected. The mutants run under the heavy-run lock before the commit; the
  twelve gate legs, the conformance sub-checks, both live harnesses and the
  full battery run on it.
- **2026-11-12 (the gateway README's run notes).** The maintainer selected
  "README notes" on 2026-11-12, after the two notes were quoted to him with
  two corrections measured against the code: the profile may come from the
  config file, and the helper defaults to profile H and passes fewer flags
  than the first draft listed. Branch `wave/gateway-readme-run-notes-2026-11`.
  `gateway/README.md` "Run locally" gains the two notes. The other route, the
  helper passing on every flag it does not know, stays available as its own
  branch. A script checked each claim of the two notes against
  `gateway/src/gateway.py` and `tools/run_gateway.py`: the quoted refusal,
  both sources of the profile, the default lane, every flag the helper
  defines, its default profile, and each kind of flag the notes send to the
  gateway itself. Five mutants of the notes each failed it on the check named
  for them. A seeded factual pass found the error planted for it; of its three
  minor notes, the handoff's count of the notes is corrected, and the other
  two leave the notes as the maintainer selected them. The mutants run under
  the heavy-run lock before the commit; the twelve gate legs, the conformance
  sub-checks, both live harnesses and the full battery run on it.
- **2026-11-12 (contract 7.8: projections keep `valid_from_ts`).** The
  maintainer selected "A 2.1 patch" on 2026-11-12, after the bullet, the
  catalog entry at v1.1.27 and on develop, the released vector, and 7.8, 4.2,
  4.7, 10.4, 2.1 and spec/versioning.md were quoted to him. Branch
  `wave/clause3-valid-from-ts-2026-11`. Contract 7.8 gains one bullet after
  its last command rule: "A same-event projection of a command (Section 4.2)
  MUST NOT omit or alter a `payload.valid_from_ts` the source wrote." The two
  must-fail projection vectors were written first. On develop's catalog, which
  has held the member `never_mutable` since 2026-11-02, both already fail with
  their codes, so their negative control is the catalog entry restored to
  v1.1.27's, under which both vectors stop failing. The guidance file's
  contract citations after :1237 moved by six with the shift tool (221
  citation groups; 85 references moved, 153 unchanged, none grown). The
  ontology reference's fixture count reads 25 must-fail. Five mutants each
  fail the anchor test, the guidance citation test or the projection suite
  test: the anchor left at the previous hash, the contract as develop held it,
  the guidance as develop held it, the catalog entry as v1.1.27 held it, and
  the omission vector expecting PROJECTION_FIELD_CHANGED. A seeded review
  found the error planted for it; the wording of these records on the SAPIENT
  egress and on the vectors' negative control follows its findings. The
  mutants run under the heavy-run lock before the commit; the twelve gate
  legs, the conformance sub-checks, both live harnesses and the full battery
  run on it.
- **2026-11-12 (the 4.3 clause of 2026-11-02 is a 2.1 patch).** The maintainer
  selected "Yes, it covers it" on 2026-11-12, after 4.3, 5.1, 7.8 and 2.1 were
  quoted to him: his contract 2.1 concurrence of 2026-11-02 covers the clause
  4.3 gained that day, "or, for a command with `valid_from_ts`, its issue
  time", as well as the 4.5.1 bullet and the 7.8 rule it named. Branch
  `wave/clause2-classification-2026-11`. Records only: a dated CHANGELOG entry
  (the 2026-11-02 entry stays as written), the question closed in the
  handoff's gap (x), and this entry. No contract, schema, policy or code byte
  changes, and the contract anchor stays. Two mutants each fail the changelog
  currency test: the resume note left at 2026-11-11, and the CHANGELOG entry
  dated 2026-11-11. A seeded factual pass found the error planted for it and
  no other error. The mutants run under the heavy-run lock before the commit;
  the twelve gate legs, the conformance sub-checks, both live harnesses and
  the full battery run on it.
- **2026-11-11 (contract 4.2 points to 4.5.1).** The maintainer selected it on
  2026-11-11 ("Yes, add it") after seeing the lines before and after; the
  clause text had passed a seeded refuter earlier that day. Branch
  `wave/contract-4-2-clause-2026-11`. Contract 4.2 gains three lines after
  "Such projections preserve the original `event_id`.": "Section 4.5.1 makes a
  reduction of `confidence` or `valid_for_ms` applied at admission under a
  declared degrade or quarantine mode such a projection, on the condition
  stated there." Taken alone, 4.2 could be read as making such a cap a
  replacement; the two sections now read alike (doctrine F4-04, which gains
  two dated lines; its validator check and configuration lint stay booked).
  The guidance file's contract citations after :470 moved by three with the
  shift tool (220 citation groups; 217 references moved, 19 unchanged, none
  grown); its two citations of 4.2's list, :460-470, became :460-473 by hand,
  and the `EVENT_DUPLICATE` remediation, whose sentence 4.5.1 had already made
  incomplete, names the admission case with :599-604. Four mutants each fail
  the anchor test or the guidance citation test: the anchor left at the
  previous hash, the contract as develop held it, the guidance as develop held
  it, and the clause's second line dropped. A seeded review found the error
  planted for it; the wording of these records on 4.2 taken alone, the
  handoff's naming of the two open questions and the second dated line on
  F4-04 follow its findings. The mutants run under the heavy-run lock before
  the commit; the twelve gate legs, the conformance sub-checks, both live
  harnesses and the full battery run on it.
- **2026-11-11 (`payload_json` under contract 3.5).** The maintainer selected
  it on 2026-11-11 ("Yes, add it") after seeing the bullet before and after.
  Branch `wave/payload-json-sentence-2026-11`. `spec/protobuf-encoding.md`'s
  bullet on `payload_json` adds that its bytes are a JSON text under contract
  section 3.5, and that one which repeats a member name in one object, at any
  depth, is not a valid encoded event. It is the sentence the handoff booked
  with the contract 3.5 change of 2026-11-10. The reference decoder already
  refuses such bytes: `zmeta_proto.py` reads the payload with the refusing
  hook except in the forensic skip mode, which the gateway never asks for. The
  document is manifest-listed and gains two lines; the guidance file's
  citation `spec/protobuf-encoding.md:112-129` (the `DECODE_AMBIGUOUS` entry)
  moves to `:114-131`. A mutant that lets `zmeta_proto.py` read `payload_json`
  last-wins fails the decoder's existing test
  (`test_duplicate_key_in_the_protobuf_payload_json_is_refused`). A seeded
  review by an independent reviewer, on a copy with its own planted error,
  found that error and one omission, applied here: open item 3 of the handoff
  still listed the sentence as waiting. It also noted that the document's
  sentence on the forensic skip mode does not say a repeated payload member is
  read to its last value there; that clause is left for a later pass. The
  mutant runs under the heavy-run lock before the commit; the twelve gate
  legs, the conformance sub-checks, both live harnesses and the full battery
  run on it.
- **2026-11-11 (CLAUDE.md: GitHub usage).** The maintainer approved the
  drafted bullet ("Yes, as drafted"), on his direction of the same evening to
  write down how the repositories use GitHub. Branch
  `wave/github-usage-2026-11`. CLAUDE.md gains one bullet under "How we work
  here", after the release-limits bullet; AGENTS.md, which holds the release
  limits, is unchanged. No document conflicted: the governance Branching
  section already reads "An agent creates and commits on local branches and
  stops." Measured for the bullet, read-only: the CI's one job took 1.5 to 1.8
  minutes green at the v1.1.27 cut, and on develop it stops at the kernel gate
  on the release manifest's pins (46 lines on 0bfa733). The public text names
  no budget, account or estate path. The battery single-source test, which
  reads the commands CLAUDE.md repeats, still fails on a broken copy of either
  of the two checked (two mutants). A seeded factual pass by a second model,
  on a copy with its own planted error, found that error and nothing else
  wrong. It noted one tension the bullet reads into: the Branching section
  says "`develop` is expected to be green but is not published", and also that
  a branch which changes a manifest-listed artifact reads red on the manifest
  pins until the cut regenerates them, which develop has done since v1.1.27.
  Settling the first sentence is the maintainer's. The mutants run under the
  heavy-run lock before the commit; the twelve gate legs, the conformance
  sub-checks, both live harnesses and the full battery run on it.
- **2026-11-11 (contract 7.7: `last_seen_ts` on a STATE).** The maintainer
  selected it on 2026-11-11 ("Yes, add it") after seeing the bullet before and
  after and the counts. Branch `exp/state-last-seen-ts-2026-11`. Contract
  7.7's list and `policy/semantics.yaml`
  `state_event.payload_must_not_contain` each gain `last_seen_ts`, after
  `observed_at`. It is the third of the four items the `observed_at` branch of
  2026-11-10 booked; the other three stay booked. Contract 7.6 defines the
  member as the `event.ts` of the latest contributing observation, so 7.7's
  category sentence already forbade it on a STATE; it stays a required
  FUSION_EVENT member. Counted before the selection and again on the branch,
  counts only: none of 5,295 STATE events in a downstream consumer's window
  carries it at any depth, while all 2,156 FUSION events there carry it at the
  payload top level; none of 809 STATE events in a producer's recorded run
  carries it; no STATE in the eight example and vector files that named the
  member before this branch carries it. A planted control was found by each
  count. Measured on the branch with the tree's own bad-event evaluator: a
  STATE that carries the member is refused as `STATE_HAS_RAW_FEATURES` at the
  top level, under `provenance`, nested under `extensions`, as `Last_Seen_TS`
  and with surrounding spaces; `lastSeenTs` passes, as before; on develop none
  of these is refused. Tests first: the pin test's eleven-name list, a test
  that names the member in both lists, and the fixture
  `state-last-seen-ts-fusion-member-collapse` failed before the contract and
  policy edit (five failures in two files) and pass after it. The export of
  `policy/semantics.yaml` is regenerated (`export/policy/semantics.json` and
  its index hash). The policy file gains one line, so the guidance file's
  citations into it move: 50 references moved and two ranges grew to hold the
  new line, and the four policy-citation tests pass. The
  `STATE_HAS_RAW_FEATURES` guidance names the field, says it belongs on the
  fusion parent, and drops `last_seen_ts` from its sentence on other
  spellings. `adapters/AUTHORING.md`, `docs/zmeta_ontology_reference.md`,
  `schema/README.md` and `docs/zmeta_vocabulary_crosswalk.md` name it with the
  others. The v1.0 lock anchor moves with its record. Unchanged: both schemas,
  for the reasons recorded on 2026-11-10; the two code copies of the nine
  names, booked. A seeded review by an independent reviewer, on a copy with
  its own planted error, found that error and nine findings, all applied. The
  main one: the lines added to `adapters/AUTHORING.md` and `schema/README.md`
  had moved the guidance file's citations into them by one line (seven
  references, and one range named in a citation's note), which no test reads,
  so both paragraphs are rewrapped to their old length and a script compares
  every cited range with develop's. The others: the records' wording and
  wrapping, two clauses on the other booked items, the fixture's event id back
  in its series, and a test comment that now says only what the test asserts.
  A separate factual pass by a second model, on a copy with its own planted
  error, found that error and nothing else wrong; it re-derived the corpus
  count, the pin list, both hashes, the schemas' names, the citation counts
  and every cited line of the guidance entry. A fact checker of these records
  (21 checks; three planted-error controls each fail on the check they target)
  caught one error in their first draft, a count of moved citations that
  included the two grown ranges. The nine mutants and the fact checker run
  under the heavy-run lock before the commit; the twelve gate legs, the
  conformance sub-checks, both live harnesses and the full battery run on it.
- **2026-11-11 (golden CoT outputs, A8).** The maintainer selected it on
  2026-11-10 ("Add the fixtures"). Branch `wave/cot-golden-2026-11`. Each case
  is built by a script in the session's records from the eight STATE_EVENT
  lines of `examples/`: the `standard` profile with the default config, and
  the `cds` profile with `how` `m-f`, which that profile requires; the
  projection instant is the event's `ts` plus 500 ms. At an instant of `ts`
  plus one second the `cds` profile refused the Profile L example, whose
  window of 1,000 ms had lapsed (`VALIDITY_LAPSED`), so the instant sits
  inside every example's window. Measured on the corpus: the `standard` output
  of all eight is the same at an instant 400 days later, so that profile does
  not read the instant; the `cds` profile refuses all seven of its projected
  cases at that later instant (its age rule). The corpus README says the
  strings are the reference implementation's and that the `standard` profile's
  float text may take an exponent form. Tests first: the first ten tests
  failed with no corpus and no tool; four more came with the review's
  corrections (the event comparison seeing a number whose type changed, the
  coverage check seeing a missing case, a malformed case reported as a FAIL
  line, the manifest builder naming the corpus and the tool). All fourteen
  pass. Eleven mutants, each killed by the test file: the comparison cut to 20
  characters; the refusal cases skipped; the corpus read last-wins; an empty
  corpus passed; the projection instant dropped; the corpus without its last
  case; an example's confidence changed; the class without the corpus; a case
  with no instant accepted; an empty refusal accepted; the drift test
  comparing events with Python's `==`, which cannot see `120` against `120.0`.
  An independent reviewer, on a sealed copy with one planted error, found that
  error (a projection instant of `ts` plus 250 ms in the README) and made
  eight other findings. Seven are applied: the event comparison made to see
  number types, with its control; the change's records, which are these; the
  release-manifest builder pinning the corpus and the tool; the test file's
  controls for drift and coverage; the `cds` number format stated for the
  point attributes only; a malformed case reported as a FAIL line, with an
  instant ending in Z and one non-empty expectation required; and the nits
  (the `description` member, the refusal named in the README lines, the class
  description, the stale cap the corpus does not reach, the corpus read
  through the refusing reader in the test file, and the README's sentence
  about other implementations). One is left out on purpose: the corpus as a
  kernel-gate sub-check, which would change what every release bundle runs. A
  factual pass over these records, by a second model on a copy with its own
  planted error, found that error and nothing else wrong; it re-projected the
  corpus, the later instants and the Profile L case, and recounted the
  kernel-gate lines. Gates before the commit: the kernel gate, whose 52 FAIL
  lines are all release-pin lines (develop's 50, two more on the claim, six
  reading new values); the example and roadmap validators; the bad-event
  corpus, 37; the conformance pack with the class and claim checks and the
  adapter harness; the CoT adapter tests and six test files that read the
  changed files, 256 passed; `git diff --check`. The eleven mutants and the
  fact checker of these records run under the heavy-run lock before the
  commit; the twelve gate legs, the conformance sub-checks, both live
  harnesses and the full battery run on it.
- **2026-11-11 (the twelve remaining JSON readers refuse a repeated member).**
  The maintainer selected it on 2026-11-10 ("Yes, before the cut"). Branch
  `exp/json-readers-refuse-2026-11`. The readers and what each does with a
  text that repeats a member name, at any depth: see the CHANGELOG entry and
  the paragraph added to `tools/README.md`. Reading sites: the twelve readers'
  files held 21 `json.loads` calls without the refusing hook (the private
  count of 2026-11-10 said nineteen, counting the gateway's self-test reader
  alone of its three). Fifteen change: two in `compat_normalize.py` (a
  `.jsonl` line, a `.json` document), one in each of `filter_risk.py`,
  `measure_packet_size.py`, `check_adapter.py` and the four fixture tools, the
  gateway's `_load_jsonl`, two in `sim/throughput.py` (now one helper), two in
  `sim/two_node.py` (a corpus line, now read before it is sent, and a received
  datagram, now counted in `ambiguous` and not read) and one in
  `test_workflow_end_to_end.py` (a forwarded datagram). Six stay: the schema
  reads of `measure_packet_size.py`, `check_adapter.py`,
  `validate_adapter_conformance.py` and the gateway, the gateway's config
  read, and `json.loads(json.dumps(template))` in `sim/throughput.py`, a deep
  copy that cannot repeat a member. One behaviour moves for a corpus line that
  is not JSON: `sim/two_node.py` now reads a line before it sends it, so such
  a line is no longer sent before the same traceback. `gateway/src/gateway.py`
  changes in two places and keeps its 3,389 lines, so none of the guidance
  file's line citations into it moves: the import line names
  `DecodeAmbiguousError`, and `_load_jsonl` reads through the refusing hook
  and stops the self-test with a named failure. The decoder of received
  traffic (`json.loads(text, object_pairs_hook=pairs_refusing_duplicates)`,
  which refused a repeat before this branch) is not touched. Tests first: the
  new test file's refusal tests and subtests failed on the unchanged tree and
  its controls passed; after the change all pass. Twenty-one mutants, each
  killed by the new test file and `test_decode_ambiguous.py`: fourteen put the
  changed reads back to last-wins (the two corpus reads of `sim/throughput.py`
  share one helper, so one mutant covers both), a refused fixture file treated
  as an empty one in two tools, a refused context file left to raise, a
  refused file left uncounted in two tools, and each harness's INVALID report
  of a refused corpus removed. An independent reviewer, on a sealed copy with
  one planted error, found that error (an exit code of 2 for `filter_risk.py`)
  and made six other findings, all applied: what the gateway's self-test and
  each harness print, in the README; the harnesses' report of a refused corpus
  as `VERDICT: INVALID` with exit 2 before any node starts, where they had
  exited 1 after the nodes started; the `ambiguous` count on two_node's
  observed line; the changed behaviour for a corpus line that is not JSON,
  recorded above; the names of three tests made true, the two_node test now
  checking that nothing was sent; and the sim tests skipped only in a release
  bundle, as `test_sim_boundary.py` does. It also counted the reading sites
  and found 21, which these records state. A first launch of the review was
  stopped before it reported, because the error planted for it was not false;
  the review ran again on a copy with a false one. A factual pass over these
  records, by a second model on a copy with its own planted error, found that
  error and two real points, both applied: the mutant list added up to 22
  against the script's 21, and `sim/throughput.py` reads a corpus only up to
  its template event, so a repeat on a later line is never read and is not
  reported. Gates before the commit: the kernel gate, whose 50 FAIL lines are
  all release-pin lines (develop's 46, four more on tool files, three reading
  new values); the example and roadmap validators; the bad-event corpus, 37;
  the conformance pack and its sub-checks; seventeen test files that hold the
  readers or read the records, 191 passed; `git diff --check`. The twenty-one
  mutants and the fact checker of these records run under the heavy-run lock
  before the commit; the twelve gate legs, the conformance sub-checks, both
  live harnesses and the full battery run on it.
- **2026-11-11 (records: cycle F10, the SIM1-01 confirmation, an acoustic
  evidence item).** Branch `wave/records-f10-acoustic-2026-11`. Three records
  acts, each on a selection the maintainer made on 2026-11-10. First, the
  doctrine log gains cycle F10 ("Yes, log them"): F10-01, F10-02 and F10-03
  OPEN, F10-04 CHANGED. Before the entries were written their statements were
  run again on this tree. The 1.1.0 schema declares `quality` on
  `ObservationPayload` alone, and `TrackStatePayload` admits additional
  properties. The registry allows the quality block on OBSERVATION_EVENT only
  and the dimensionality entry on STATE_EVENT too. A STATE with a 2D geo and
  an unregistered `quality.geo_status` token passes the reference check, and
  the same STATE with `AVAILABLE` is refused. On a downstream consumer's
  window of 2026-11-11, 5,152 of 5,295 STATE events carry `quality.geo_status`
  `VERTICAL_UNAVAILABLE`, each with a 2D geo and an error ellipse (counts
  only; no value of an event was read out). Second, SIM1-01 gains a note dated
  2026-11-11: the maintainer confirmed on 2026-11-10 ("Yes, it stands") that
  HELD-FIRM stands on the corrected facts, so the status is his decision and
  no longer the session's reading. The entry above the note is left as
  written. Third, the roadmap candidate `acoustic-level-carriers` gains a
  second `promotion_evidence` item and the file's `last_updated` reads
  2026-11-11. The item was measured again on the same window: 2,305 ACOUSTIC
  observations from one producer with the role EDGE, each with `spl_db` and
  `level_reference` `DB_RE_1UPA`; the producer's name marks it as a sensor
  simulator and is in no tracked file of this repository or of the six
  downstream repositories searched. Three earlier reads on 2026-11-10 gave
  2,266, 2,372 and 2,424, and the consumer's own count was 2,259. The
  maintainer confirmed on 2026-11-10 that the producer is an edge user's. The
  first tripwire asks for a second independent implementation. The candidate's
  first evidence item counts one implementation of the reference mechanism,
  and the registry note on ACOUSTIC_LEVEL_REFERENCE names the Orcasound
  hydrophone capture as the first independent evidence instance; which
  implementation the tripwire counts as the first is a reading that waits for
  the maintainer. The item does not say the tripwire fired: a simulator that
  declares a reference under an unregistered token is the maintainer's to
  adjudicate, and contract 20.4 keeps an emitted spelling out of the
  vocabulary. Not done here: the Archive sweep booked on 2026-11-10, and the
  README notes from the field leg below. The field leg. The second of the
  three field legs before the cut ran on 2026-11-11 against `develop` at
  65366f7, by the sender's own record (counts only): a live JSON stream of 411
  clean events and one text with a repeated member, and three protobuf
  messages, one carrying an unknown field. The gateway refused each tampered
  message as `DECODE_AMBIGUOUS` and forwarded every clean one. The protobuf
  bytes came from this repository's encoder, because no producer in the
  downstream program emits protobuf, so that half shows the gateway's refusal
  and says nothing about another implementation's protobuf. `git diff --stat
  65366f7 76aed0f -- gateway/src` is empty. An independent reviewer, on a
  sealed copy with one planted error, found that error (the quality block's
  registry scope widened to FUSION_EVENT) and made fifteen other findings.
  Fourteen are applied: the repositories searched for the producer's name (six
  downstream, the search run again on 2026-11-11 with no hit); what the TAK
  Protocol adapter still refuses, and its pattern written as one to watch
  (F10-04); what was read for F10-01, the processor's code and one position
  across 60,887 observations; the measured count behind F10-02 and what
  contract 21.8 says of a STATE; the source of each half of F10-03; contract
  8.3 quoted as it stands and the ruling's ranking of its two forms (F10-01);
  the roadmap's own evidence bar beside contract 20.4; the simulator named in
  the CHANGELOG and the handoff; the source of the first implementation; the
  producer's name kept out of the records; the scope of the protobuf sentence;
  the wording of the SIM1-01 note; and "confirmed" for his selection. One is
  left to the readers branch, which rewrites the handoff's item 3. A factual
  pass over these records, by a second model on a copy with its own planted
  error, found that error and nothing else wrong; it counted the window again
  and searched the six downstream repositories again, with the same results.
  Gates before the commit: the kernel gate, whose 46 FAIL lines are all
  release-pin lines, three of them reading new values on the roadmap; the
  example and roadmap validators; the bad-event corpus, 37; the conformance
  pack; the eight test files that read the changed records, 101 passed; `git
  diff --check`. The fact checker of these records runs under the heavy-run
  lock before the commit; the twelve gate legs, the conformance sub-checks,
  both live harnesses and the full battery run on it.
- **2026-11-10 (contract 7.7: `observed_at` on a STATE).** The maintainer
  selected it on 2026-11-10 ("Policy and contract now") after seeing the
  bullet before and after. Branch `exp/state-observed-at-2026-11`. Contract
  7.7's list of prohibited state payload fields and `policy/semantics.yaml`
  `state_event.payload_must_not_contain` each gain `observed_at`, after
  `t_end`. The category sentence above the list already forbade observation
  timestamps; the list says "include" and the reference check enforces the
  list, so a STATE that carried the member under `payload.provenance` passed.
  Such a STATE was already outside the contract, so the change invalidates no
  payload that complied with it (`spec/versioning.md`, Backward Compatibility
  Expectations), and contract 2.1 lets a patch tighten conformance around
  already-defined semantics. The check is unchanged: it searches the payload
  at any depth and reports `STATE_HAS_RAW_FEATURES` with the path. Measured on
  the branch: the name is refused as a text key under `provenance`, nested
  under `extensions`, in another letter case and with surrounding spaces;
  `observedAt`, `observation_ts`, `last_observed_at`, `t_observed` and
  `last_seen_ts` pass, as before, at the top level and under `provenance`.
  `last_seen_ts` is the one of these the contract defines: 7.6 makes it the
  `event.ts` of the latest contributing observation, so it is an observation
  timestamp under 7.7's category sentence. It is booked as a candidate for the
  list, for the maintainer's selection, and the guidance entry names it. A map
  key that is a byte string passes the check for all ten names, as it did
  before the branch; a check that refuses such a key in a STATE payload is
  booked. Thirty-two shipped OBSERVATION, INFERENCE and FUSION events (the
  examples and the must-pass pack) keep their verdict when given the member.
  Surfaces: the contract bullet, three lines before and after, so no contract
  citation moves; the anchor, with a dated comment; the policy list and the
  regenerated JSON export; the guidance entry for `STATE_HAS_RAW_FEATURES`
  (the tenth name, "six of those ten", two stale citations to the validators
  set to their lines by reading, and a sentence on where an observation time
  belongs: on the parent OBSERVATION's `event.ts` and the FUSION's
  `last_seen_ts`, while the STATE's `event.ts` is its valid time);
  `schema/README.md`, which now says the policy refuses the tenth name where
  the schemas do not list it; `adapters/AUTHORING.md` rule 8, its line count
  unchanged; the ontology reference, which now says the policy refuses ten
  names and the schemas nine; the vocabulary crosswalk. The policy file gains
  one line. Of the guidance file's 61 line references into it, 50 move by one,
  two grow to include the new line and nine stand above it, each compared with
  the old file's text. The branch's first commit, on the maintainer's
  selection of 2026-11-10 ("Yes, repair them"), had put those references back
  on their text. Two commits of 2026-11-02 (`b5eec25`, `61232f7`) added five
  lines to the policy file and moved no reference into it, so 32 of the 60
  named other text: a code one line above its own, or a key five lines above
  its own. That commit moves 29 of them, two of which it also extends to the
  present end of the v1.0 wire fallback map, and grows three by the code
  inserted inside the list they cite whole. It writes one line number that
  stood as prose as a citation, which is the sixty-first reference, and
  corrects a count beside another. It adds four tests to
  `gateway/tests/test_validation_guidance.py` that read the references and
  fail on a policy line number written as prose; seven mutants each fail them.
  On the file as it stood the reader reports 21 of the 32, so it is a tripwire
  and not a proof. The same drift in the citations to the validators (the two
  corrected here each began 64 lines above its code), the schemas and the
  gateway is booked as its own repair; no test reads those citations.
  Unchanged, each with its reason: both schemas, because the v1.0 schema is
  byte-locked (`V1_0_SCHEMA_SHA256`), a schema refuses a name only at the
  paths it lists, and naming the member in the 1.1.0 schema alone would split
  the two version schemas, so the policy's any-depth check enforces the rule
  for both versions (a schema could refuse `payload.provenance.observed_at`
  and leave `provenance` open; an earlier draft of these records said it could
  not, which was wrong); the two code copies of the nine names that read the
  payload's top level only (`tools/validate_projection.py`,
  `adapters/egress/cot/zmeta_to_cot.py`), booked with
  `conformance/profile_projection_field_catalog.yaml`. Called directly, the
  CoT adapter projects a STATE that carries `observed_at`, nested or at the
  top level, and refuses one that carries a top-level `t_end`, so its own
  guard disagrees with the contract; the gateway runs the policy check before
  it projects, and the copies are taken together with the catalog when the
  booked item is opened. Verification: the fixture
  `state-observed-at-nested-collapse` was written first; on the unchanged tree
  the must-fail runner reported it as not refused (its only code was the
  lineage warning), and it is refused now with the path
  `provenance/observed_at`; the same event without `payload.provenance` is not
  refused under either list.
  `gateway/tests/test_state_prohibited_fields_pin.py` was written first: its
  test for the name failed on the unchanged tree, and its two synthetic tests
  show the comparison reporting a missing name and allowing a policy superset.
  It pins the contract's list of ten names in order, so a name that loses its
  backticks fails it. The fixture's `observed_at` is five seconds earlier than
  its `ts`, as an observation time carried forward would be. Ten mutants, each
  killed by the five test files that hold the change: the policy list without
  the name, or with it spelled `observedAt` (under either, the must-fail
  runner reports the new fixture alone as no longer refused); the contract
  bullet without the name, or with it spelled `observedAt`; the anchor with
  the old hash; the exported list as it stood before; the export index as it
  stood before; the STATE check reading the payload's top level only, under
  which eight nested fixtures stop being refused, the new one among them; the
  guidance file as the branch's first commit left it, with no reference moved
  for the new policy line; and the contract bullet with one name's backticks
  removed, which the pin's earlier floor of nine names let pass. An
  independent reviewer, on a sealed copy with one planted error, found that
  error (a count of "seven" for six) and made thirteen other findings. The
  branch's first commit answers three: the 32 drifted policy citations, a
  policy line number written as prose, and a citation whose note contradicted
  it. Nine are applied: the false reason given for leaving the schemas
  unchanged; the pin's floor; `last_seen_ts`; `schema/README.md`; the CoT
  adapter's top-level asymmetry; the text-key qualifier; where an observation
  time belongs; the fixture's times; and one finding on wording, the
  maintainer's selection and the anchor comment's clause. One needs no change:
  `exp/` names this governed unit, as it named the previous one. A factual
  pass over these records, by a second model on a copy with its own planted
  error, found that error and nothing else wrong; it found two lists that
  could be counted two ways, the mutants and the applied findings, and both
  are written out one by one. Gates before the commit: the kernel gate, whose
  46 FAIL lines are all release-pin lines (develop's 43, three more on the
  bad-event corpus, ten reading new values); the example and roadmap
  validators; the bad-event corpus, 37; the conformance pack; the seven test
  files that hold the change or read the guidance file, 80 passed; `git diff
  --check`. The ten mutants and the fact checker of these records run under
  the heavy-run lock before the commit; the twelve gate legs, the conformance
  sub-checks, both live harnesses and the full battery run on it. What this
  ties together: a gateway on this policy refuses that producer's STATE while
  it carries the field, so the cut that carries this change follows the
  consumer's dating fix and the producer's removal of the field, in that
  order. Both are the other lanes' acts.
- **2026-11-10 (contract 3.5: the JSON duplicate-key sentence, four tools,
  and the guidance file's citations).** On the maintainer's selection of
  2026-11-10 ("Sentence and tools now"), who was shown the paragraph in the
  question. Branch `exp/contract-json-duplicate-2026-11`, two commits. The
  second: contract 3.5 gains the paragraph as he was shown it, between the
  validity paragraph and the paragraph on encoding versions (four lines).
  The reference decoders already refused such a text (doctrine F7-01); the
  contract now says it is not a valid encoded event, which binds every
  implementation. `tools/check_compat.py` (its line path and its
  whole-document path), `tools/validate_examples.py`,
  `tools/validate_bad_events.py` and `tools/validate_conformance.py` read
  JSON through `pairs_refusing_duplicates` and report or refuse a repeated
  member without a traceback. The two fixture tools still read a file as it
  comes, so what they print before a refused line is unchanged, and a
  malformed fixture line still ends in a traceback, as it did. A `.json`
  document is refused whole for one repeat, reported at line 1. One
  conformance fixture is added for a repeat at depth
  (`conformance/encoding-negative/gateway-must-fail.jsonl`, ten fixtures;
  the suite reads 55); the same event without the repeat passes the gateway
  with no diagnostic. The anchor in `gateway/tests/test_v1_lock_baseline.py`
  moves to the new contract hash with a dated comment. The guidance entry
  for `DECODE_AMBIGUOUS`, the tools README, and comments in
  `gateway/src/gateway.py` and `zmeta_decode_guard.py` name 3.5; neither code
  file's line count changes, because thirty-six lines of
  `tools/validation_guidance.yaml` cite the gateway by line. The first
  commit repairs something the shift exposed. `tools/validation_guidance.yaml`
  cites the contract by line, and the contract sentences of 2026-11-02 (a
  clause in 4.3, a bullet in 4.5.1, a command rule in 7.8) were added without
  moving the citations below them, so 196 of the 219 references written in
  citation form had named lines 1, 7 or 10 above their text since then,
  eight of them a blank line. Each is mapped by the diff of the contract it
  was written against (the contract of d0ee31f for 218, of b5eec25 for one)
  to the lines that hold its text today. Three measures agree on those 219:
  no reference's lines were changed or split; a new test that reads the
  edges of every reference failed on the file as it stood, with 70 off
  their text, and passes; of twelve quoted phrases beside a citation, two
  were in the cited lines before and eleven are after. The repair missed
  eight more contract line numbers, in six places, that stood in prose
  ("for the rule, 1206-1207 and 1867-1884", "at line 939"). The tool and the
  test read only the citation form, and the independent reviewer found
  them: six had drifted with the others and two had been wrong longer. They
  are set to the lines the sentences are about, rewritten in citation form
  (228 references now, with the one new citation), and a second test fails
  on a contract line number written as prose; it failed on the eight. The
  new paragraph moves 206 of the first 219 by four lines; a checker compares
  each with the old contract's text and fails on the unshifted file. Both
  tests are tripwires: they read where a reference begins and ends and how
  it is written, not what the cited lines say. Verification: six refusal
  tests and a control were written first; on the unchanged tree the six
  failed (the compatibility tool reported the repeating text with no issue
  and exit 0) and the control passed. Added after the change, each held by a
  mutant: the must-fail file of the conformance tool (the tool as it stood
  reads the repeat and exits 0), a repeat below the top level in each tool,
  a document with a clean sibling, the issue category, the single FAIL line
  of a refused fixture file, and the paragraph's place. Nineteen mutants
  were each run against the four test files and each failed them: twelve of
  the tools, three of the contract's paragraph, one of the anchor, two of
  the citations, and one that puts the gateway's JSON reader back to
  last-wins, which the new fixture and the older tests catch. The
  independent reviewer, a different model on a sealed copy with one planted
  error (the tools README naming the wrong category), found that error and
  made eleven other findings. Applied: the eight prose line numbers and the
  second citation test; the records' count of what the repair covered; the
  list of readers that still keep the last value, which was incomplete; the
  whole-document refusal said in the README and held by a test; the fixture
  tools reading as they come again; the test gaps above; the
  `payload_json` case in the guidance entry and the doctrine note; the
  versioning statement and the depth fixture; the wording of the count of
  gateway citations. Booked: a row for this rule in
  `docs/zmeta_contract_to_stack_crosswalk.md`, which has not followed the
  contract since 2026-08. A factual pass over the records, by a second
  model on a copy with its own planted error, found that error and one
  imprecise count of comments, corrected. It lists what it could not check
  from the tree: the maintainer's selection, the mutant run, the history of
  which test failed when, and the reviewer's findings.
  Gates before the commit: the encoding-negative suite, 55; the kernel gate,
  whose 43 FAIL lines are develop's 41 release-pin lines and two more on the
  two conformance tools, with eight lines reading new values; the example
  and roadmap validators, the bad-event corpus and the conformance pack;
  the thirteen test files that hold the change or the records, 142 passed;
  `git diff --check`. The nineteen mutants, the twelve gate legs, the
  conformance sub-checks, both live harnesses and the full battery run under
  the heavy-run lock, the mutants before the commit and the rest on it, and
  the merge message carries their result.
  Not in this branch, booked for the maintainer's word. Other readers of
  event or fixture JSON still keep the last value: eight tools under
  `tools/`, three that read events (`compat_normalize.py`, `filter_risk.py`,
  `measure_packet_size.py`) and five that read fixtures (`check_adapter.py`,
  `validate_adapter_conformance.py`, `validate_encoding_negative.py` for its
  fixture file, `validate_precision_policy.py`, `validate_projection.py`);
  the gateway's self-test reader of `examples/encoding-roundtrip.jsonl`
  (`_load_jsonl`); and three development harnesses (`tools/sim/throughput.py`,
  `tools/sim/two_node.py`, `tools/test_workflow_end_to_end.py`). The question
  put to him named four tools as the ones that read last-wins; that list was
  not complete, and he is told so. Also booked: one sentence in
  `spec/protobuf-encoding.md` that a member repeated inside `payload_json`
  falls under contract 3.5; duplicate map keys on the CBOR and compact lanes;
  a clean FAIL line for a malformed fixture line; a check that holds each
  citation to the words quoted beside it; and the guidance file's line
  citations into other files, which nothing reads.
- **2026-11-10 (records wave: two registry entries, the enrichment note,
  three terminal doctrine statuses).** On the maintainer's selections of
  2026-11-10 in this repository's session. Branch
  `wave/records-lookup-held-firm-2026-11`. Registry
  (`spec/extension-registry.yaml`, Class B): `COLLECT_EXTERNAL_RECORDS`
  reserved under `command_task_type` and risk-relevant, the first reserved
  entry so marked; `OSINT` rejected under `observation_modality`;
  `last_updated` 2026-11-10; 70 entries (36 reserved, 19 experimental, 11
  proposed, 2 adopted, 2 rejected). New advisory note
  `docs/zmeta_enrichment_results_note.md`, listed in `docs/README.md` and in
  the release-context list of `gateway/tests/test_release_currency.py`; its
  quotations were checked against the contract sections it names by a script
  with two controls seen failing. Doctrine log: cycle F9 with F9-01 OPEN;
  F8-01 and F8-02 HELD-FIRM, with the SAPIENT egress recorded as F8-02's
  second occurrence; SIM1-01 HELD-FIRM with a dated note and the TAK plane's
  answers. One statement was corrected on the way. A session record of
  2026-11-03 said the CoT projection wrote no `<remarks>` for a captured run
  of 809 STATE events; re-run on 2026-11-10, all 809 carry `confidence=` in
  `<remarks>`. The maintainer's selection of 2026-11-03 was made on that
  statement, and the correction is put to him with this wave.
  `RELEASE_CHECKLIST.md`: the container step names
  `docker compose -f deploy/gateway/docker-compose.yml up` and what verified
  means. The ontology reference's count sentence and the handoff (a
  current-state paragraph, items 3 and 6, and the surface-coherence counts)
  are brought to the tree. Verification: the two entry tests were written
  first and failed for the missing entries; with the entries in, the count
  test failed on the ontology reference's 68 until the sentence was
  corrected; the registry validator reported `REGISTRY_LAST_UPDATED_STALE`
  until the stamp moved, and reads 70 entries now; the release-context
  completeness test failed until the note was listed; four doctored schemas
  that admit the new names each turn the registry's probe valid, which is
  the state the entry tests refuse. An independent reviewer, a different
  model on a sealed copy with one planted error, read the change against
  the contract, both schemas, the lineage policy and checks, the three
  adapters, the compose file and the last validation report. It built the
  receipt and the claim the note describes and ran them through the
  validators, where both pass. It found the planted error and made ten
  other findings. Applied: these records said five tests when four had
  been added; the ontology reference's next sentence, the count of names
  the leak probe runs on, was stale at 18 of 46 and reads 20 of 47 by the
  validator's own function, held by a fifth test that failed on the stale
  sentence; the reserved-name test gains a control for the 1.0 branch; the
  note names the `model` and `based_on` members a claim cannot validate
  without, and says which part of its held-results rule is the contract
  and which is a reading; the rejected entry's rationale makes the
  reporting observation conditional; the SIM1-01 decision says whose
  reading it is that the answer stands; the checklist names a
  STATE_EVENT; the handoff names the four tools. Left as it is: the three
  terminal entries stay in place until the next Archive sweep, as earlier
  terminal entries have. A factual pass over the records, by a second
  model on a copy with its own planted error, found that error and no
  other wrong statement; it lists what it could not check from the tree,
  which is the maintainer's selections, the TAK plane's answers, the
  809-event run and the history of which test failed when.
  Gates before the commit: the registry validator, 70 entries; the kernel
  gate, whose 41 FAIL lines are develop's 38 release-pin lines and three
  more on the registry, with the bundle hash line reading a new value; the
  example and roadmap validators; the six registry and currency test
  files, 87 passed; `git diff --check`. The twelve gate legs, the
  conformance sub-checks, both live harnesses and the full battery run on
  the commit, and the merge message carries their result.
  Not in this wave, booked: the two governed reason codes for looked-up
  results, which wait for a real result; four doctrine tensions met on
  2026-11-10, which wait for the maintainer's word to be logged; a general
  validator probe that holds every rejected name out of the schemas, which
  today only the `OSINT` test does for its one name; a matching durable
  decision for `OSINT` in the roadmap's `rejected_or_deferred` list, which
  the `PAYLOAD_SCHEMA_URI` rejection has and the roadmap validator does not
  require; one Archive line each for SIM1-01, F8-01 and F8-02 at the next
  sweep.
- **2026-11-10 (TAK Protocol Version 1 egress, before its first contact).**
  On the maintainer's selection of 2026-11-10 ("fix all before the leg"),
  after an independent review of the same day read the adapter against the
  `.proto` files and the protocol text published in the ATAK-CIV repository.
  The review found the bytes of a projected track correct and four things
  that a first contact with a server or client would meet badly. Changed in
  `adapters/egress/tak_protocol/zmeta_to_tak_protocol.py`: `how` is required,
  as the published `CotEvent` requires it, and a missing one is refused with
  `TAK_PROTOCOL_HOW_REQUIRED` (the CoT projection writes `how` only when the
  deployment configures it); the typed route requires every item of the
  published message except the contact's `endpoint`, the one item noted as
  optional; two elements of one typed kind, and a typed element whose
  numeric attribute is not a number, travel in `xmlDetail` and the event is
  sent, as the published sender rule says, where both refused the event
  before; `tak_control_message` writes the standalone mesh announcement; the
  reader refuses a stream length beyond the published range. The README
  states what a sender does on mesh and on a stream, and no longer calls
  `takControl` a stream's negotiation: a stream starts in XML and negotiates
  with three XML events before any frame. Verification: tests were written
  first, in two rounds (the build's private record holds both first runs).
  Seven new or changed tests failed against the module as it stood, with
  forty-eight passing. An independent reviewer then read
  the change against the published text, found the error planted for it, and
  made seven other findings; two more tests, written for those findings,
  failed against the first change. A factual pass over the records, by a
  second model on a copy with its own planted error, found that error and
  one statement no test pinned, a missing or empty `type` or `uid` refused;
  a test now pins it. Fifty-eight pass now, and sixty when `takproto` is
  present. Fifteen mutants were each run against the suite and each failed
  it, thirteen of the change and two of the required-attribute checks. The
  reviewer's findings changed three things:
  a missing `how` is named as the reason only when it is the one thing
  refused; the announcement always states a minimum version of 1; the
  README's mesh steps restate the published rules for counting contacts and
  for falling back to XML. Records: the adapter README, the module's
  docstring, this entry, the handoff's current-state paragraph, the
  CHANGELOG, and a dated note under doctrine F8-01. No manifest-listed
  artifact changed. The field leg that drives the adapter against a TAK
  Server and a client is the plane's, on the maintainer's word, and by his
  selection of the same day it comes before the next cut, with two more
  legs: a real sender exercising the `DECODE_AMBIGUOUS` refusal, and one
  consumer running a `develop` gateway for a day.
- **2026-11-09 (the signing tripwire, and the pre-cut dry run).** On the
  maintainer's selection of 2026-11-09, handoff item 4 records that the
  signing tripwire (roadmap `event-signing-anti-replay`; the downstream
  register's DR-15) has not fired, re-affirmed after a reading of the
  downstream records; the evidence is in the item. The same selection took
  the pre-cut dry run: every leg `RELEASE_CHECKLIST.md` names for a
  runtime-code cut was run on `develop` dffe599 with no cut (the twelve gate
  legs, ten green and the two release-manifest pin legs red until a cut; the
  two live runtime harnesses, both passed; the gateway container by the
  v1.1.27 report's compose command, its four hashes equal to the host's and
  one shipped event forwarded with its CoT and the same two expected
  warnings as that report). No feature failure. The next cut, v1.1.28, waits
  until after the demonstration and comes on the maintainer's word, with
  more testing and validation first by his line of the same day. Booked for
  a records branch on his word: `RELEASE_CHECKLIST.md` :125 names a "Docker
  build" the tree does not define (no Dockerfile); the leg the validation
  reports run is `docker compose -f deploy/gateway/docker-compose.yml up`,
  and the line should name that command and what "verified" means.
- **2026-11-09 (TAK Protocol Version 1 egress).** On the maintainer's
  selection of 2026-11-09 (his "all recommended" on the open decisions, which
  took option (a): the egress adapter builds open with TAK Protocol Version 1
  first, then the signing tripwire's question, behind the demonstration
  lanes' rulings), the branch `exp/tak-protocol-egress-2026-11` off `develop`
  c1f5800, two commits, Class C. The egress recce of 2026-11-03 (a private
  session record) assessed fifteen rows of formats, ranked six for a build,
  placed this one first, and measured the shape
  through the `takproto` package: 809 events of the producers' run 7 and
  1,680 live ADS-B events through the CoT projection to protobuf and back with
  no field mismatch. Tests first: forty-two in
  `adapters/egress/tak_protocol/test_tak_protocol_egress.py`, plus two that
  run only when `TAK_PROTO_SITE` names a directory holding `takproto`,
  which failed at collection with no module; then the module
  `zmeta_to_tak_protocol.py`: a hand-written canonical proto3 encoder for the
  TAK Protocol Version 1 schema (field numbers checked against `takproto`'s
  descriptors), the mesh and stream framings, a reader that refuses by the
  decoders' rule of 2026-11-02, and the typed route: a typed detail child
  goes to its typed field only when the typed message carries it whole, else
  whole in `xmlDetail`, so the CoT projection's `precisionlocation` keeps its
  ellipse attributes (doctrine F8-01). Times floor to the millisecond
  (contract 4.2: a validity may be lowered, never raised). Refusals rather
  than silent drops for everything the schema cannot carry. Verification:
  the known-answer bytes are computed in the test from the field numbers and
  an independent varint writer; three encoder mutants (the `uid` field
  number, rounding instead of flooring, the typed route's attribute check)
  each failed the suite, 3, 1 and 2 failures; with `TAK_PROTO_SITE` set the
  mesh and stream bytes for the known event equal `takproto.xml2proto`'s and
  `takproto.parse_mesh` reads a declared 2-D vessel's projection with every
  checked field equal. Records: the adapter README (schema, mapping, the
  typed route, refusals, what the encoding changes, the reader,
  verification), the adapters overview line, this entry, the handoff's
  current-state paragraph, the CHANGELOG, doctrine F8-01 and F8-02. No
  manifest-listed artifact changed; the release manifest's state is as
  `develop` left it. `adapters/README.md` is a required surface of
  `ZMETA-ADAPTER` and a governed-doc test surface; the two test files that
  read it pass (42). The second commit applies a seeded refuter's twenty
  findings (Opus 5.5, read-only, on the first commit with one planted
  contradiction in the README, found): the encoder writes `-0.0` (a bit
  comparison, as protobuf's serializers compare), refuses a comment, a
  document type declaration or a processing instruction outside the root
  element too (a text scan before parsing; the parser dropped those in
  silence), sends a typed element with a numeric field left out to
  `xmlDetail` (an absent number reads back as 0), the reader bounds a varint
  at 64 bits and refuses an empty input; a second known answer sets every
  typed field, because a fourth mutant that moved the typed messages' field
  numbers had passed the suite; the reader's repeated-field, trailing-bytes,
  non-UTF-8 and wide-varint refusals and the `refusal` dict gain tests; the
  documents' over-statements corrected (two typed elements refuse only when
  both qualify; the projection writes `precisionlocation` only with an
  ellipse, so the typed field is never reached through it; the gateway does
  not yet call the adapter; the doctrine entries are OPEN, not HELD-FIRM,
  under the log's own protocol). Suite after: 52 passed, 2 skipped; 54 with
  `TAK_PROTO_SITE`. Gates in the worktree on the second commit's tree: the
  focused suite and the two governed-doc test files 94 passed, 2 skipped;
  examples 51 of 51; roadmap ok; `git diff --check` clean; the kernel gate
  stops at the release-manifest pins as it does on `develop` since 2026-11-02
  (no manifest-listed artifact changed here); the full battery under the
  estate's heavy-run lock 2107 passed, 4 skipped, 1273 subtests passed,
  13 failed, the thirteen being the release-manifest pin tests
  (`test_release_manifest.py`, `test_release_package.py`) that fail on
  `develop` until the next cut, no feature failure. No TAK Server or client
  was driven; the adapter opens no connection.
- **2026-11-02 (the decoders refuse ambiguity: `DECODE_AMBIGUOUS`).** On the
  maintainer's selection of 2026-11-02 in this repository's session (the
  carried list's item 4, option (a): refuse with a governed code; the
  rebuild ruling's hazards 1 and 3), the branch `exp/decode-ambiguous-2026-11`
  off `develop` 6089a9a, three commits (this paragraph records the first;
  where the second superseded it, the note says so). Tests first (eleven in
  `gateway/tests/test_decode_ambiguous.py`; nine failed on the unchanged code,
  the two clean-event controls passed), then the code: `zmeta_decode_guard.py`
  (the exception and the JSON `object_pairs_hook`), the gateway's three JSON
  decode sites and its decode-failure branch (the code `DECODE_AMBIGUOUS`
  where the exception is the guard's, `SCHEMA_INVALID` otherwise),
  `zmeta_proto.loads` with `unknown_fields="refuse"` by default at every
  message level (malformed bytes still reported first; three pre-existing
  tests on unsupported wire types and truncated fields kept green by that
  order), the protobuf payload's JSON held to the same rule, and
  `convert_encoding` reading JSON the same way. The registry route: the code
  in `policy/violation-codes.yaml` (62 codes; 9 warn, 53 fail, the ontology
  reference updated), `policy/semantics.yaml`, both schemas' reason-code
  enums (the v1.0 schema anchor moved with a dated note; the lock test failed
  with the enum changed and the anchor unmoved, then passed; superseded by
  the second commit, which took the post-lock route and returned the
  anchor), the guidance
  entry (the no-orphans test failed without it, then passed). Fixtures: two
  protobuf and one gateway encoding-negative fixtures, seen failing with the
  decoders stashed, passing with them; the first run exposed a vacuous pass
  in `validate_encoding_negative.py` (a forwarded event counted as a
  rejection when the fixture had not decoded), closed in the same commit.
  Gates in the worktree: the sub-checks explicit (projection 37, registry 68,
  classes 34, encoding negative 53, precision 41, bad-event corpus 36,
  adapter harness 53, conformance pass=22 fail=42); examples 51 of 51;
  roadmap ok; the full battery 2042 passed, 2 skipped, 13 failed (the
  release-manifest pin tests); `git diff --check` clean.
  The first battery read four more failures, all consequences of the new
  code: the policy JSON export under `export/policy/` is a verbatim
  projection of `policy/*.yaml` and was regenerated with
  `tools/export_policy_json.py` (three files), and a second v1.0 schema
  anchor in `test_time_status_state_enum.py` moved with a dated note on his
  selection, the adjudication that test asks for (returned to 1d2d8416 in
  the second commit).
  Doctrine F7-01 records the decision; handoff item 3 names it and books
  what stays open. A seeded refuter then found its plant and twenty-seven
  mismatches; the maintainer took three as selections (the post-lock route,
  so the code lives in the 1.1.0 enum only with a v1.0 wire fallback to
  SCHEMA_INVALID and both v1.0 anchors restored; protobuf repeated
  non-repeatable fields refused too; the rule stated in
  `spec/protobuf-encoding.md` with its forward-compatibility cost, the JSON
  contract sentence booked), and the rest were this lane's, applied in a
  second commit: the guard required at import (its fallback had failed
  open) and shipped in the four release and conformance lists; the auto
  lane surfaces an ambiguous protobuf refusal instead of a UTF-8
  SCHEMA_INVALID; `skip` reads the payload last-wins too; `tools/validate.py`
  and `tools/explain.py` read JSON with the hook, and `validate.py` reports
  the refusal as a FAIL line under the code (a producer's validator had
  passed what the gateway refuses); the fixture tool compares the gateway's
  own code; four more tests seen failing first; the records corrected (the
  plane's protobuf lane is not enabled; "reads against"; CBOR and compact
  duplicates and trailing bytes booked; the rule binds the reference
  decoders). Gates after the second commit: 2047 passed, 2 skipped, 13
  failed (the release-manifest pin tests). Corrections of record to the
  second commit's message, which is immutable: its test-first figures ("8 of
  24"; "78 across seven files") were measured before the test files took
  their final form and do not reproduce; the figure of record is the second
  refuter's (b5eec25 with the HEAD test files: 10 failed, 25 passed; four of
  the five new tests failed first, the malformed-JSON test is a regression
  guard that passed; 33 tests across the four touched test files pass); and
  its CBOR booking named cbor2 where the reference path is this repository's
  `zmeta_cbor` (F7-01 has the corrected booking). A second seeded refuter over
  the whole branch diff found its plant and sixteen findings, all applied in
  a third commit on 2026-11-03: the decoder reads a repeated field's bytes
  before refusing the repeat (the refuter's two probes, a truncated repeated
  field and a repeated field with the wrong wire type, reported "repeated"
  before and malformed or mistyped after) and names the wire type;
  `tools/explain.py` catches the refusal (a traceback before);
  `tools/replay.py` and `tools/udp_sender.py` read a line with the hook and
  refuse to re-encode a duplicate key into a binary lane (the JSON lane sends
  verbatim); the fixture tool reports a gateway exception against
  `expect_gateway_code`; a repeated-field fixture (its control: b5eec25's
  decoder accepts the bytes as `{"zmeta_version": "1.1"}`); the governed-code
  test asserts the v1.0 enum was found and the allowlist membership; eight
  tests seen failing first; 54 encoding-negative fixtures; the records
  corrected (the plane's boundary is a ratified design, not yet built; the
  CBOR booking; the guidance citations and header; the commit count). Gates
  after the third commit: 2055 passed, 2 skipped, 13 failed (the
  release-manifest pin tests). The merge into `develop` and the push wait for
  the maintainer's words. A downstream boundary's ratified
  design (not yet built) refuses the JSON case to quarantine under its
  interim; the reference's rule for JSON now matches it, and its re-pin reads
  this.
- **2026-11-02 (two contract sentences: admission caps, the command window).**
  On the maintainer's word of 2026-11-02 in this repository's session (his
  selections of F4-04 R1 and gap (x) R1 with the carried list's refuted
  corrections, then of wording A in 4.5.1 and wording B in 7.8 from a
  read-only preparation, refuted after his selection in this branch),
  the branch `exp/contract-sentences-2026-11` off `develop` 44175a3. First
  commit: the 4.5.1 bullet and the 7.8 rule as he worded them, the field
  dictionary's `valid_from_ts` line, doctrine F4-04 to DECIDED, the handoff's
  gap (x) closed, the lock-baseline anchor moved to aa62e3d2d0e0986f...
  (the anchor test failed with the sentences in and the anchor unmoved,
  then passed). Second commit: the gateway's `risk_adjudication` record
  carries `confidence_claimed` and `valid_for_ms_claimed` whenever a cap or
  reduction changes a value, and the SAPIENT command egress computes
  `task_end_time` from `valid_from_ts` when present, else `event.ts`; tests
  seen failing first (five tests); one must-pass vector (a GOTO with a later
  `valid_from_ts`). Gates in the worktree: the kernel gate's sub-checks run
  explicitly beside the gate, because `--kernel-gate` stops at its first red
  stage and on an unreleased branch the stale manifest hides the stages after
  it (projection 37, registry 68, classes 34, encoding negative 50, precision
  41, bad-event corpus 36, adapter harness 53, conformance pass=22 fail=42;
  the same command on `develop` 44175a3 is green with pass=21); examples 51 of
  51; roadmap ok; the full battery 2024 passed, 2 skipped, 13 failed (the
  release-manifest pin tests); `git diff --check` clean. The merge into
  `develop` and the push wait for the maintainer's words. Third commit, on the
  branch's seeded refuter (it found its plant and twenty findings): his
  words of 2026-11-02 took "lacks either" for 4.5.1's second sentence, a 4.3
  clause (a command's `event.ts` is its issue time when `valid_from_ts` is
  present), the profile projection catalog preserving `valid_from_ts` (the
  projection vector seen failing first, then corrected) and the SAPIENT
  refusal of a window that opens after `event.ts` (his selections, clicks
  in the repository's session), and he concurred that
  both sentences are 2.1 patches; the anchor moved to 15a9bf4e234e2621...
  with its control. This lane's fixes: the claimed values are the values a
  cap or reduction changed, on the timing-degrade paths too; a reduction
  factor below 1 is declined; the lock comment says section 4.5.1 gains a
  rule; the F4-04 paragraph names the mode, drops a vector that did not
  exist and books the replacement-case check; the handoff's gap (x) note
  names the dedupe hold and the MAVLink mission intent as measured by the
  rule. A second seeded refuter found its plant and ten findings, applied in
  a fourth commit: the gateway's failure-mode path declines a factor below
  1 and its record is tested; the promotion record says `reduction_declined`
  instead of reporting a reduction that did not run; the strip guard
  protects `payload.valid_from_ts`; the SAPIENT mapping pack and the MAVLink
  egress README say what their commands carry; the handoff's item 7 line
  and the gap (x) note name what is answered and what stays open (the 4.3
  clause's 2.1 coverage, the 4.2 pointer, the optional-field permissions,
  the closed-at-issue window, the factor lint). Gates after the third
  commit: the sub-checks explicit (projection 37,
  registry 68, classes 34, encoding negative 50, precision 41, bad-event
  corpus 36, adapter harness 53, conformance pass=22 fail=42); examples 51 of
  51; roadmap ok; the full battery 2028 passed, 2 skipped, 13 failed (the
  release-manifest pin tests); `git diff --check` clean.
- **2026-11-02 (records pass on the maintainer's carried-list decisions).** On
  the maintainer's word of 2026-11-02 in this repository's session, after
  his thirteen selections over the carried list (each put to him with a
  seeded refuter's corrections), the branch `wave/records-t7-2026-11` off
  `develop` 32ae445, one commit, records class: doctrine U1-02, F3-03,
  F3-04 and F3-05 ratified (DECIDED, with a dated paragraph each; the cds
  cap's first release named as v1.1.27; one deployment's `cds` window
  recorded as his held choice against 4.2 until its partner re-check);
  C1-07 decided (binary64, float64 on the wire, the determinism clause a
  MUST at adoption, digits beyond binary64 not content, a labelled
  received-bytes digest fires no tripwire; the compact-mapping text rides
  the `canonical-byte-form` branch when the first hashing need appears;
  the roadmap note says so); the signing tripwire recorded in the handoff
  as not yet with its firing conditions and the counter-reading kept; the
  handoff's stale U1-02 "OPEN" corrected; the KLV row names the evidence
  that moves it. His other selections of the day open their own branches
  on his word (F4-04 R1 and gap (x) R1 as class (a) sentences; the
  hazards 1 and 3 refusal; zmeta-18; the relation check under R-A; the
  gap (z) refuter before T5; the replay branch after the demonstration)
  and are recorded in the private session file. Gates in the worktree:
  roadmap ok, candidates=22; examples 51 of 51; the kernel gate red on the
  six release-manifest lines `develop` already carries; the full battery
  2019 passed, 2 skipped, 13 failed (the release-manifest pin tests);
  `git diff --check` clean. The merge into `develop` and the push wait for
  the maintainer's words.
- **2026-11-02 (the `heading_deg` definition and the MAVLink course).** On the
  maintainer's word of 2026-11-02 in this repository's session (his
  selection of course over ground on 2026-10-28 and of the wording on
  2026-11-02), the branch `exp/heading-deg-course-2026-10` off `develop`
  fbe6ad4, two commits. First, contract 6.4 gains the definition paragraph
  and `spec/field-dictionary.md` the same meaning; the v1.0 lock-baseline
  contract anchor moves with a dated note (the anchor test failed with the
  sentence in and the anchor unmoved, then passed); the records (this entry,
  the changelog, doctrine F6-01, handoff items 3 and 18, an addendum to the
  s1_08a record). Second, the MAVLink template derives the course from the
  ground velocity at or above `MIN_COURSE_SPEED_MPS` (1.0 m/s, a deployment
  keyword), keeps `hdg` and yaw in `quality`, records an asserted frame
  beside the retained `hdg`, refuses a course from a non-finite velocity,
  and moves to adapter version 1.3.0 so the lineage transform tells a
  course from a body angle (the version applies to every transform the
  template writes, the SYSTEM_EVENT `translate:` strings included, whose
  behaviour did not change); ten tests failed on the unchanged template
  first, then 81 passed; the README is rewritten, and the adapters' README
  sentence that made the frame assertion canonical is corrected. Third, on
  the seeded refuter's findings: the 150 contract citations in
  `tools/validation_guidance.yaml` past the 6.4 insertion and eleven
  continuation references re-anchored by the seven inserted lines (the
  before-and-after comparison read 0 of 150 on the unedited file first,
  then 150 of 150, non-blank text required); the README example given the
  lineage it needs to emit at all; the records corrected (three of the
  ruling's five revisions were refuted with a seeded error, not five; 7.6
  lists `estimated_state.heading_deg`; the dictionary speaks for the STATE
  scope; JREAP drops the member; any version before 1.3.0 is the body
  angle, not 1.2.0 alone; the 2.1 reading is his, accepted on the record).
  Gates in the worktree: examples strict 51 of 51; roadmap ok; the kernel
  gate green except four release-manifest lines (the contract is a
  manifest-listed artifact: the artifact, group, top-level and bundle
  hashes), the stale manifest an unreleased branch leaves on purpose
  (`docs/zmeta_change_governance.md`, Branching); the full battery 2016
  passed, 4 skipped, 13 failed, the thirteen the release-manifest pin tests
  (`test_release_manifest.py`, `test_release_package.py`), which pass on
  the unedited tree; `git diff --check` clean. The adapter conformance
  harness vector for the template passes unchanged (it asserts no frame).
  Confirmed conformant under the definition with no change: the track
  projector (ADS-B ground track), the CoT egress (`<track course>`), the
  SAPIENT egress (velocity from course and speed); no other shipped ingress
  writes `payload.heading_deg`. Booked, not this branch: the projector could
  fill an AIS-derived state's `heading_deg` from `ais_cog_deg_true`; the CoT
  egress's `speed="0.0"` placeholder when only a heading is present
  (handoff item 18). Consumers at v1.1.25 see no definition until the next
  cut and their re-pin; a consumer tells the template's two behaviours
  apart by the lineage transform (`promote:mavlink-telemetry@` any version
  before 1.3.0 a body angle, `@1.3.0` a course). The merge into `develop`
  and the push wait for the maintainer's words.
- **2026-11-02 (records pass after the 7.6 `last_seen_ts` definition).** On
  the maintainer's word of 2026-11-02 in this repository's session, the
  branch `wave/records-7-6-followups-2026-10` off `develop` fbe6ad4, three
  commits, records class: the two inline test fixtures that carried the
  old relation (`gateway/tests/test_lineage_semantics.py`,
  `tools/test_workflow_end_to_end.py`) now give the member observation's
  `event.ts`, as 7.6 requires; the 92 contract citations in
  `tools/validation_guidance.yaml` past the 7.6 insertion were re-anchored
  by the two inserted lines (a before-and-after comparison read 92 of 92
  naming on `develop` the text they named at v1.1.26; the same comparison
  on the unedited file read 0 of 92 first; seven continuation references,
  contract line numbers written after a prefixed citation without the
  prefix on six lines, were found unshifted by the branch's seeded review
  and shifted in the second commit, each verified the same way); the
  review also corrected the PHOTO-01 bullet's event type (the pointer is
  the OBSERVATION's; a STATE carries no `data_ref`, contract 7.7); the
  2026-10-27 changelog
  entry's booking sentence now names where the relation check goes; one
  evidence bullet (2026-10-27, PHOTO-01) added to the roadmap candidate
  `raw-data-absent-evidence-status` (a mis-indented trial copy failed the
  roadmap validator first; the edited file reads ok, candidates=22). Gates
  in the worktree: examples strict 51 of 51; roadmap ok; the two edited
  test files 7 passed; the full battery 2008 passed, 4 skipped, 13 failed;
  `git diff --check` clean. The kernel gate and thirteen battery tests
  (`test_release_manifest.py`, `test_release_package.py`) read red on the
  release-manifest pins alone, because the roadmap is a manifest-listed
  artifact; the same thirteen pass on the unedited tree. An unreleased
  branch leaves the manifest stale on purpose
  (`docs/zmeta_change_governance.md`, Branching); the cut regenerates it,
  so `develop` reads red on those pins from the merge to the next cut, as
  it did between v1.1.26 and v1.1.27. No schema, policy or validator byte
  changes.
  The relation check on `last_seen_ts` (handoff item 2 (a)) is its own
  branch; the maintainer selected the sentence as written (never later and
  the latest member's time) on 2026-11-02. The merge into `develop` and the
  push wait for the maintainer's words.
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
