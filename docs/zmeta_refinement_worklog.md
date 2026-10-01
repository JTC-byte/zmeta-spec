# ZMeta Refinement Worklog

## Current Resume Note

- Last updated: 2026-10-01 (shipped configs stop advertising unread failure modes, on `exp/failure-modes-honesty`)
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
- **2026-09-29 (v1.1.26 published).** The cut commit baf86f1 on `develop`;
  `main` moved to it without a checkout (`git branch -f`, after the
  ancestor check), so no tracked file was re-smudged between signing and
  upload; annotated tag `v1.1.26` on baf86f1; `develop`, `main` and the tag
  pushed together. The GitHub release carries seventeen assets, the
  v1.1.25 set: the four zips, the manifest, the notes, the validation
  report and `SHA256SUMS_v1.1.26.txt`, a detached signature for each of
  the eight, and the public key `ZMETA_RELEASE_SIGNING_KEY_v1.1.26.asc`.
  Verified as published: every asset downloaded from the release,
  `sha256sum -c` over the downloaded checksum file passed for all seven
  entries, the eight downloaded signatures verified as good against the
  Incept.IO ZMeta release signing key with the Gpg4win gpg, and the
  downloaded notes, report, checksum file, its signature and the public key
  are byte-identical to the tracked copies. One trap re-learned on the
  way: the signing tooling's `--verify-signatures` run from Git Bash
  resolves the Git-bundled gpg and an empty keyring and fails with exit 2;
  every signature step ran from PowerShell, where `gpg` is Gpg4win's, and
  the secret-key listing there hung until `gpgconf --kill gpg-agent`
  restarted the agent. GitHub CI completed with success for the release commit on develop, main and the tag.
- **2026-09-29 (v1.1.26 cut: the `cds` CoT profile, the CoT type parse,
  the gateway identity setting, the gateway's diagnostics on the 1.1.0
  lane, and the held integration line).** On the maintainer's direction
  of 2026-09-29, given in this repository's session ("once you have run
  all checks and tests to validate the adapter, I want it merged and on
  Main for public use", with the scope answered as the adapter plus the
  identity and lane-diagnostics branches, `develop` cut whole as v1.1.26,
  and tag, sign, push and publish), the five merges landed on `develop`
  in dependency order with no fast-forward: `main` (the notice set),
  `exp/cot-type-parse`, `exp/cot-cds-profile`, `exp/gateway-identity`,
  `exp/gateway-lane-diagnostics`. Every conflict was the known shape:
  two insertions at the same anchor in the three record files (both
  kept, the worklog sentinel deduplicated) and one `gateway.py` hunk
  where the identity and lane-diagnostics branches each added helpers
  before `build_violation_event` (both kept, the signature carrying
  `identity=None`). `wave/registry-candidates-2026-09` stays local, its
  U1-02 questions open. The cut followed `RELEASE_CHECKLIST.md`: the
  governed baseline regenerated from the v1.1.25 manifest before the
  bump; the release identity bumped across every current-facing
  surface the v1.1.25 cut touched; the manifest rebuilt with
  `--update-claims`; the notes and the validation report written; the
  bundles, the formal package and the checksums built; the signing key
  exported; the retention pass moved the 2026-08-10 through 2026-08-13
  session records to the archive. Validation at the cut is in
  `release/VALIDATION_REPORT_v1.1.26.md`.
  The signing, tagging, pushing and publishing steps are recorded in
  the entry that follows the cut commit.
- **2026-09-29 (the `cds` CoT profile on `exp/cot-cds-profile`, based on
  `exp/cot-type-parse`, not merged).** On the maintainer's direction of
  2026-09-29, given in this repository's session, the shape one partner's
  cross-domain guard passed on 2026-09-29 is captured as a profile of the
  reference CoT egress adapter, selected by `cot_config["profile"]`. The
  definition came from the downstream ecosystem's TAK session as data: the
  pinned reference adapter's output with the detail children limited to
  four, `how` asserted per source, one remarks line, no links, and stale
  set to arrival plus 120 s; the last two went live together at 20:01 UTC
  and neither was tested alone. The documentation test found the governing
  text: contract section 14 decides that display conveniences are adapter
  behavior, and also lists `valid_for_ms` as freshness/stale behavior among
  what a projection must preserve, which this profile does not, so F3-03 is
  open; section 18.2 guides (section 18 is stated as future direction and
  policy guidance) what a redaction may not do, and five of its six
  prohibitions are tests, the sixth being the README's statement of the
  profile; section 18.3 guides that export audit metadata belongs to policy
  and conformance, and the profile carries none; nothing decides whether an
  asserted affiliation may cross a guard, so the profile refuses it. The
  profile is a transform applied after the standard projection, which keeps
  the standard bytes untouched (a test freezes them) and makes the profile
  exactly what was validated. Two refutation rounds shaped it. The first
  (fourteen readers, fourteen findings confirmed) turned a draft that built
  remarks from the standard text plus markers into the validated
  deployment's fixed template with the markers first; the mutation check on
  that rewrite found two vacuous items (a config-time link check that could
  never fire, a circle-wrapper test passing on the age gate). The second
  round, four readers against the rewrite (adapter code, test vacuity,
  documents against code, and the gateway run live): thirteen adapter
  defects reproduced and closed (a non-UTC instant mis-stamped every time;
  replay-display mode defeated the age rule and is now refused; a producer
  name could forge a marker and the separator is now replaced in every
  part; a string confidence or one out of range reached the far side and is
  now not sent; control characters and lone surrogates raised or produced
  ill-formed XML; a string point value could smuggle elements past the
  child filter and the root shape is now checked; a source that is not an
  object raised); four vacuous tests and five gaps closed; eleven document
  errors corrected, among them a contract quote that joined a lead-in to a
  bullet, a section 18.2 phrase applied to a case it does not cover, and a
  claim that the oldest case "cannot occur" that replay-display mode
  falsified; and one gateway fail-open (a `cot.config` given as a string
  ran the standard profile in silence), closed by refusing a mistyped `cot`
  block, which reverses the 2026-07-27 rule that a malformed block is
  ignored, on the changed premise that the block now selects a redaction.
  Fifty-four behavior-changing mutants, every one killed;
  the output validates against MITRE's public event schema with lxml.
  Validation at the branch tip: `python -m pytest -q adapters/egress/cot
  gateway/tests/test_gateway_cot_profile.py gateway/tests/test_gateway_cot_config.py`
  134 passed and 1 skipped (the public schema test, which passed with
  `COT_EVENT_XSD` set); `python tools/validate_examples.py --strict
  --require-all` 51 of 51; `python tools/validate_conformance.py
  --kernel-gate` 14 `RELEASE_MANIFEST_*` lines over the same items as
  `develop` and no other failure; `python tools/validate_future_roadmap.py`
  ok; `python -m pytest -q` 13 failed (the release-pin set), 1930 passed,
  1 skipped; `git diff --check` clean. Nothing pushed.
- **2026-09-28 (the CoT egress class parse on `exp/cot-type-parse`, not
  merged).** On the maintainer's ruling of 2026-09-28, the CoT egress now
  accepts `payload.class` as the CoT type only when it parses as a CoT atom
  type. Otherwise it sends `a-u-G`, which claims no affiliation, and carries
  the label in `remarks` as one quoted token, with characters that are not
  printable replaced and the length capped at 64. A configured `default_type`
  is held to the same grammar. The documentation test found the reason for the
  defect. Both schema versions declare `TrackStatePayload.class` only as a
  string, the CoT ingress stores a CoT type there, and the egress README
  described a fallback for an absent class only, so it was silent on a class
  that is a label. The first draft's five tests failed four of five against
  the unchanged egress. An opus refuter then found that a label could forge a
  remarks fragment and that six mutants of the fix survived those tests. The
  second draft quotes the label, adds five tests, and validates
  `default_type`. A mutation check over ten mutants, the refuter's six plus
  four against the new safeguards, killed all ten. Validation at the branch
  tip:
  `python -m pytest -q adapters/egress/cot/` 69 passed;
  `python tools/validate_examples.py --strict --require-all` 51 of 51;
  `python tools/validate_conformance.py --kernel-gate` 14
  `RELEASE_MANIFEST_*` lines over the same items as `develop` and no other
  failure; `python -m pytest -q` 13 failed (the release-pin set) and 1869
- **2026-09-28 (the gateway identity setting on `exp/gateway-identity`, not
  merged).** On the maintainer's concurrence of 2026-09-28, the producer name
  and node role the reference gateway stamps on its own diagnostics are the
  settings `gateway_producer` and `gateway_node_role`, defaulting to the
  historical `zmeta-gateway` and `GATEWAY`; `platform_id` stays fixed, since
  the concurrence named the producer and the role. The identity reaches all
  three diagnostic builders, all thirteen builder calls inside
  `process_message` through a new `gateway_identity` argument, and the
  encoding fallback. The gateway's outgoing self-check runs role and producer
  authority over its own diagnostics, so a configured identity the loaded
  policy refuses would have had every one of them refused; a startup check now
  exits instead. It covers identity only, because the schema half of the
  self-check depends on the lane, and running it at startup would stop a
  gateway on the 1.1.0 lane from starting at all. The default identity is
  never checked. Twelve tests were written first and ten failed against the
  unchanged gateway, the other two being controls on the defaults; two more
  cover `main()`. A mutation check over fourteen mutants killed all fourteen,
  including a dropped identity at a single later builder call, which only the
  structural test catches. Validation at the branch tip:
  `python -m pytest -q gateway/tests/test_gateway_identity.py` 14 passed;
  `python tools/validate_examples.py --strict --require-all` 51 of 51;
  `python tools/validate_conformance.py --kernel-gate` 14
  `RELEASE_MANIFEST_*` lines over the same items as `develop` and no other
  failure; `python -m pytest -q` 13 failed (the release-pin set) and 1873
- **2026-09-28 (the 1.1.0-lane diagnostic self-check on
  `exp/gateway-lane-diagnostics`, not merged).** Under the maintainer's
  ruling of 2026-09-12 (handoff item 1), the reference gateway's outgoing
  self-check validates a diagnostic the gateway minted against the schema its
  own declared `zmeta_version` selects, and a forwarded producer event against
  the inbound lane as before. The v1.0 stamp stays. The TV-09 pins were
  parameterised first, across the v1.0 lane, the 1.1.0 lane and the union,
  and three pin classes holding five tests were added. Against the unchanged
  gateway, six of the nine test functions failed, every failure on the 1.1.0
  lane or on the missing mark, while the v1.0 lane and the union passed; pins
  built on the v1.0 schema alone could not have seen the defect. The end-to-end pin through
  `main()` found a second symptom the ruling did not name. On the 1.1.0 lane,
  each warning on an accepted event was replaced by a REJECTED
  `SCHEMA_INVALID`, so the output showed an accepted event beside refusals of
  events that were never sent. The self-check tells a minted diagnostic from a
  forwarded event by type: the three builders return `GatewayDiagnostic`, a
  `dict` subclass that encodes byte for byte like a plain dict on all four
  output encodings. Three alternatives were rejected. Keying on the source
  block trusts a self-declared field, and the identity setting on
  `exp/gateway-identity` makes that block configurable. A registry of minted
  ids is module state. Changing the shape `process_message` returns would
  break a deployment that imports it. The ruling also asked for an interim
  README sentence naming the dispatching schema as the lane for legible 1.1.0
  diagnostics until the fix lands. It is not written, because the fix lands in
  the same commit; the gateway README states the lanes as they now behave.
  An opus refuter found no blocker or major defect and nine minor ones.
  Seven are resolved on the branch and two are booked in the handoff. A
  missing or unreadable `schema/` directory would have left the self-check
  falling back to the lane without a word, so `main()` now mints a probe
  diagnostic at startup and exits unless the schema it declares is present
  and accepts it; a tenth test covers that. The forged-wire test could not
  fail on the rule it was credited with, so its docstring now says what it
  shows and it gains the union-lane case. The gateway README now names the
  two diagnostics the self-check does not cover. The records now state the
  drop in violation counts on the 1.1.0 lane, the changed check for a v1.0
  lane served from another directory, the test count, and the merge conflict
  with the identity branch. The two booked are the contract hash, which does
  not pin the v1.0 schema a 1.1.0-lane gateway now checks its diagnostics
  against, and the README sentence on native codes, already booked. A
  mutation check over fifteen mutants killed
  the fourteen that change behavior. The fifteenth validates diagnostics
  against the dispatching schema, which accepts exactly what the v1.0 schema
  accepts for a v1.0 diagnostic and differs only in how an invalid one's
  error reads. Validation at the branch tip:
  `python -m pytest -q gateway/tests/test_violation_event_self_validity.py`
  10 passed; `python tools/validate_examples.py --strict --require-all` 51
  of 51; `python tools/validate_future_roadmap.py` ok;
  `python tools/validate_conformance.py --kernel-gate` 14
  `RELEASE_MANIFEST_*` lines over the same items as `develop` and no other
  failure; `python -m pytest -q` 13 failed (the release-pin set) and 1865
  passed; `git diff --check` clean. Nothing pushed.
- **2026-09-28 (five upstream asks on `wave/registry-candidates-2026-09`,
  not merged).** On the maintainer's go of 2026-09-28 to open five upstream
  asks as candidates, doctrine U1-01 records the go and U1-02, OPEN, records
  the routing as this session's disposition with the questions it surfaced.
  Two asks open as new candidates: DIALECT_LABEL, `proposed`, with roadmap
  candidate `dialect-label` and its carrier left to promotion; and roadmap
  candidate `canonical-byte-form` with no registry name. Three are recorded on
  existing records: the signing concepts were already open, the F2-04 booking
  is recorded in SENSOR_STATUS's notes, and DATA_REF_MEDIA_METADATA's notes
  record the live-versus-recording question against contract Section 9.3. The
  ontology reference's present-tense counts move to 67 entries (10 proposed),
  18 of 45 reserved or proposed entries under the leak check, and 22 roadmap
  candidates. Its section 13 registry row, headed as of v1.1.25, is corrected
  to v1.1.25's 63 entries, and the heading now says earlier sections describe
  the current tree; the section's figure is left for regeneration at the next
  release. Handoff item 6's counts are refreshed to 67. Two independent opus
  refuters reviewed the first draft and found one blocker, eleven majors (nine
  distinct) and ten minors. The blocker was that the draft ruled out carrying
  the label inside the admitted event, which contract Section 3.3 permits, and
  requires when the admission is itself a warn, degrade or quarantine
  decision. A second pass over the rewrite found sixteen of the prior findings
  resolved and raised further corrections, the largest being that every
  shipped ingress adapter already names the source dialect in
  `lineage.transform`. Each was addressed before the commit. Validation at the
  branch tip:
  `python tools/validate_extension_registry.py` ok entries=67;
  `python tools/validate_future_roadmap.py` ok candidates=22
  rejected_or_deferred=3; `python tools/validate_examples.py --strict
  --require-all` 51 of 51; `python tools/validate_conformance.py
  --kernel-gate` 14 `RELEASE_MANIFEST_*` lines over the same items as
  `develop` and no other failure; `python -m pytest -q` 13 failed (the
  release-pin set) and 1859 passed; `git diff --check` clean. Nothing pushed.
- **2026-09-21 (pre-push history rewrite: the held develop records
  generalised, the consent recorded, the three trailers removed).** Before
  the first push of `develop` since v1.1.25, a share-readiness scan
  (verdict in the private session record) found the published line clean
  and the unpushed records carrying material that belongs in the private
  evidence record: the capture station's hosting model, retention figures,
  dated gap and store inventory in doctrine entry F1-06 and handoff item
  8; a named downstream consumer in twelve places across the doctrine log,
  the handoff, this worklog, the merge review register and one
  extension-registry note; and two build-host paths in the merge review
  register. On the maintainer's direction of 2026-09-21 the unpushed
  history was rewritten so those passages never reach the remote: each
  introducing commit was replayed with the passage generalised in place,
  the three commits carrying an attribution trailer (doctrine F2-09) were
  reworded without it, and the specifics moved to the private companion
  under `local/`. The fielding organization's consent to publish the
  cycle's derived findings, given 2026-09-21, is recorded in the Cycle F1
  header. Every unpushed commit changed identifier; the records above cite
  the old ones, and this table is the map (old, new, subject):
  9814f2b -> df781b3 (Write the branching rule into the change governance doc and )
  7a01d35 -> b1dcb26 (Record the F1 field-evidence adjudications and land the vali)
  b0666d0 -> aa070cd (Mint two experimental 1.1.0 markers from a live hydrophone a)
  8930fb8 -> f1cf0d3 (Let the 1.1.0 ACOUSTIC arm carry a linear-pressure level bes)
  c7819bb -> 0ad6c1e (Name both level forms in the INVALID_MODALITY_FEATURES hint)
  e7c1959 -> 2d4195c (Scope level_reference to spl_db in the descriptions and reco)
  e434096 -> d8b5c53 (Merge branch 'wave/f1-field-evidence' into develop)
  80d8181 -> 76e7692 (Merge branch 'exp/acoustic-1.1.0' into develop)
  4932afb -> 62b02ea (Merge branch 'exp/acoustic-pressure' into develop)
  29dd5b6 -> 3e399c8 (Record the integration of three waves into develop and the m)
  893ca9b -> f79c808 (Correct the battery count in the integration record)
  05be3c5 -> 72049fb (Merge branch 'exp/open-specification-notice' into develop)
  A second pass the same day reworded three commit messages that still
  named the consumer (found by a peer check of message bodies, which the
  first pass's gate had not scanned) and corrected this map to
  original-to-final identifiers; every tree is unchanged. The first-pass
  identifiers, on the remote for about twenty minutes before the
  force-push on the maintainer's direction: 633848b, 3a52700, e1e2f67, 5add606, e595b31, 4b1e9f2, 4a1214e, 53035b6, bd5e284, e4c2c99.
  The extension-registry note edit leaves the release manifest stale on
  purpose (Branching section); the manifest regenerates at the cut.
  Process records were altered only to remove the passages named here. No
  CHANGELOG entry: nothing user-visible changes.
- **2026-09-12 (integration: three waves merged into develop, held for
  live evidence).** `wave/f1-field-evidence` (7a01d35), `exp/acoustic-1.1.0`
  (b0666d0) and `exp/acoustic-pressure` (8930fb8, c7819bb, e7c1959)
  merged into `develop` in dependency order, each with `--no-ff`, after a
  review of all three against the guiding documents (register:
  `docs/merge_review_2026-09-12_findings.md`; determination: good to merge,
  six conditions, none withholding the merge) and three rulings made on the
  repository's own documentation at the maintainer's direction (doctrine
  F2-08 orphan note and F2-09; the gateway diagnostic ruling is in the
  handoff). `develop` is held without a
  cut until more live acoustic evidence arrives; the downstream COP consumes the
  1.1.0 lane from `develop` during the hold. Validation at the merged tip:
  `python tools/validate_extension_registry.py` ok entries=66;
  `python tools/validate_future_roadmap.py` ok candidates=20;
  `python tools/validate_examples.py --strict --require-all` 51 of 51 passed;
  `python tools/validate_conformance.py --kernel-gate` exit 1 with
  14 `RELEASE_MANIFEST_*` lines and no other failure line (four of
  those lines come from `docs/zmeta_change_governance.md` on `develop`
  itself, the rest from the four manifest-listed artifacts the branches
  change); `python -m pytest -q` 1859 passed, 13 failed (1858 in the
  rehearsal worktree, where one environment-dependent test skipped), every
  failure a manifest hash mismatch in `gateway/tests/test_release_manifest.py`
  or `gateway/tests/test_release_package.py`; `git diff --check` clean. That
  red band is the expected state of `develop` between these merges and the
  cut, by construction of the Branching section; the cut regenerates the
  manifest. One further failure appears about one run in fifty:
  `test_release_signing.py::test_ensure_package_zip_refuses_a_stale_zip_and_never_overwrites`,
  a pre-existing mtime-granularity race, booked in the register. Four
  negative guards in `test_release_package.py` abort in fixture setup on the
  stale manifest for the whole hold, so the packager's refusal of bad input
  is unproven until the cut; booked. This entry also records the 2026-09-11
  docs-class commit on `develop` (9814f2b, the branching rule in
  `docs/zmeta_change_governance.md` and `CLAUDE.md`), which had no worklog
  line of its own.
- **2026-09-12 (doctrine entry F2-08: a linear-pressure level on the
  ACOUSTIC arm, on its own branch).** The downstream COP investigated two more
  acoustic sources after Orcasound, a calibrated research hydrophone
  stated re 1 uPa and an atmospheric infrasound array whose field
  publishes calibrated pascals and no decibel, and reported that neither
  could emit. Verification found the refusal was one schema line, `spl_db`
  required on the experimental arm, not contract text, and that a named
  pascals feature already validated beside it; it also corrected three
  framings in the note (the contract does not mandate a decibel; the
  underwater and airborne references differ by a fixed 20 log10(20) =
  26.02 dB and
  the objection is laundering; the implementation count is one, not
  three). The maintainer ruled: the arm requires `center_freq_hz` and
  any of `spl_db` or `pressure_pa` with `pressure_statistic`, preserving
  the level-present guarantee; the `spl_db` description states its window
  and that it declares no amplitude statistic; a statistic marker is held
  behind a second implementation; a governed pressure contract is refused
  on gates 1 and 6 and the pair registered experimental with the bar
  stated unmet. The pre-cut verification returned twenty-six findings,
  led by a first draft that registered the name as reserved while the same
  change made the fields valid; the entry was re-registered, the
  reserved-leak check gained the arm that would have caught it, the level
  choice was rewritten so a missing level names the pressure pair on the
  wire,
  the pair was bound both ways with zero refused, and the schema gained
  nine fixtures in the discrimination suite so the red/green proof is an
  in-repo artifact rather than a session act. A second verification found
  the pressure-to-statistic direction of the binding unpinned and an
  existing power_db fixture made vacuous by the relaxation; both were
  repaired and a mirror guidance rule added. Landed on
  `exp/acoustic-pressure` stacked on the acoustic branch. The three-branch
  merge review of 2026-09-12 found the per-code hint for
  `INVALID_MODALITY_FEATURES` still saying `spl_db` is required; corrected
  on the branch before the merge.
- **2026-09-10 (doctrine cycle F2: the acoustic modality worked on 1.1.0
  from live evidence; two experimental markers minted; the lane fix).**
  The downstream COP session brought seven spec questions ahead of an Orcasound
  hydrophone producer and an environmental-station feed. The drafted
  answers were adversarially refuted before sending (three refuters, all
  three corrected the draft: the environmental blocker premise was false
  because `metrics.modality` is optional on SENSOR_STATUS, the drafted
  three-way split ran against the slot's documented coarse grain, and the
  drafted dBFS-in-`spl_db` form is the shape contract 6.5 prohibits), the
  COP's finding that SENSOR_STATUS has no canonical position was confirmed,
  and the maintainer ruled on every open point. A live Orcasound Lab
  segment was captured, analysed and templated on both lanes; the honest
  1.1.0 form validated only by laundering, and the honest v1.0 form failed
  on `timing_quality.est_error_ms` rather than fabricate a bound. Landed,
  additive on 1.1.0 with v1.0 byte-identical: ACOUSTIC_LEVEL_REFERENCE
  (`features.level_reference`, `spl_db` description corrected) and
  TIMING_ERROR_BASIS (`timing_quality.est_error_basis`), each experimental
  on the A1-01 mechanism with discrimination fixtures on both lanes; the
  D1-01 launcher passthrough with its red/green test and README lane notes;
  guidance lane gates with three new structural rules and the first fixture
  for the structural layer; and two registry validator checks the pre-cut
  verification showed were missing (a note containing ": " had parsed as a
  mapping and passed; the top-level stamp had lagged the newest entry).
  Booked: a
  producer-authority pattern for environmental stations, a governed `geo`
  on the SENSOR_STATUS arm, the cross-modality generalization of the level
  reference, and the contract sentences for the post-lock pass.
- Last updated: 2026-08-26 (field-evidence adjudications: the 2026-08 sonar/chat edge deployment)
- **2026-08-26 (doctrine cycle F1: eight maintainer rulings from live field
  evidence; no governed vocabulary moved; the lock stands).** A second edge
  organization fielded an imaging sonar with its own fusion pipeline and a
  bidirectional tactical-chat bridge, publishing a self-declared dialect
  onto the live bus the private capture station records. Live packets were
  measured directly and two audits ran with adversarial verification
  (thirteen agents each); the maintainer then ruled on every open question
  from the evidence. The rulings: the `replay-synthetic-labels` tripwire is
  adjudicated fired, with the deployment recorded as the second independent
  instance on the roadmap branch and a promotion blocker booked for the
  reserved replay records' droppable-label flags; chat is ruled in scope,
  evidence-gated, with the incoming adapter to be received as field
  telemetry; the `rssi`/`snr` zero pair is booked as second-instance
  evidence for generalizing the `RF_ZERO_FILL_SUSPECTED` predicate at the
  AAR; C1-04 closes with a recorded rationale and no mint, its narrow
  residue booked as a declaration-floor and adapter-consistency wave; and
  the diagnostics-carry-the-fix system graduates during the lock as a
  separate advisory file with coverage scaling to all 61 violation codes
  under per-hint adversarial verification. Cycle entry F1-05 records the
  counter-result worth as much as any change: five mint candidates from a
  novel sensor domain were all refuted as composable today, and the
  canonical templates built from the live data validate strict. One
  apparatus finding (F1-06): the capture station's rolling default plus a
  missed pull cadence discarded the deployment's raw feed before the final
  window; the prune manifest records what was lost, the recovered window is
  preserved in the capture repo, and the cadence question is booked. Public
  reasoning in doctrine log cycle F1; raw specimens, measurements, and the
  full adjudication records in the private evidence store.
- Last updated: 2026-08-23 (ontology reference wave: new doc, nine figures, corrections)
- **2026-08-23 (ontology reference, appreciation layer, doc corrections).**
  A docs-class wave, maintainer-directed while the repo stays locked for
  the field user's refactor: no governed artifact changed.
  `docs/zmeta_ontology_reference.md` is new, built from a fan-out of ten
  readers over the primary sources with ten adversarial verifiers
  re-deriving every fact; of 585 gathered facts, 370 survived unchanged,
  153 were corrected, 58 were re-tagged, 4 were refuted, and the page was
  written only from the verified residue. Its tension register carries
  sixteen confirmed divergences. The documentation-only ones were fixed
  in this wave (schema/README branch wording, the field dictionary's
  timestamp glosses, the lifecycle guide's stale-arm default, the
  registry prose ladder, README enumerations, the overview's adapter
  tables); the ones touching governed surfaces are booked for the
  post-AAR window, led by the contract section 22 class table naming
  ZMETA-GATEWAY where the conformance manifest defines
  ZMETA-GATEWAY-REFERENCE. `docs/diagrams/generate_figures.py` grows
  nine figures that read their counts from the manifests, the examples,
  and the adapter estate at generation time, with parsers that raise on
  drift rather than rendering stale numbers. Seven adversarial passes
  ran against the wave's own drafts and every pass found real defects,
  including a figure regex over-counting roadmap candidates by summing
  two YAML lists and three overclaims the honesty doctrine forbids; the
  shipped text states only what the data supports. The overview, README,
  and docs index now route readers between the narrative overview and
  the reference, and the reference opens with the first-exposure
  category material before its how-to-read apparatus, per maintainer
  direction on pacing.
- Last updated: 2026-08-13 (RF zero-fill minted; v1.1.25 cut)
## Archived Task Sections

Completed task sections S0-01 through R1-05 are archived verbatim in
`docs/zmeta_refinement_worklog_archive.md` (retention pass, 2026-07-15).
The session records from 2026-08-10 through 2026-08-13 were moved there at
the v1.1.26 retention pass (2026-09-29).
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
