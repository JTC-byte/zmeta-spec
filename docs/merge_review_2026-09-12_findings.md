# Merge Review Finding Register, 2026-09-12

**Advisory / non-normative.** The complete verified finding set from the
review of `wave/f1-field-evidence` (7a01d35), `exp/acoustic-1.1.0` (b0666d0)
and `exp/acoustic-pressure` (8930fb8) before their merge into `develop`,
recorded here because the run artifacts that produced it are session-scoped
and do not survive. The determination was: good to merge into `develop` in
dependency order and hold without a cut, with six conditions, none
withholding the merge.

## Method

Eleven independent lenses read the three commits: seven doctrine dimensions
(design gates 1 to 7; change governance and the Branching rule; locked-kernel
integrity; registry and roadmap coherence; test and fixture integrity; records
accuracy and voice; the consumer's view of `develop` during the hold), three
whole-diff maintainer reads, one per branch, and one merge rehearsal on a
throwaway worktree that ran the full battery on the merged tree. Every finding
faced two adversarial refuters, one reproducing it on the tree and one checking
the cited rule text and the severity scale of `docs/zmeta_audit_playbook.md`;
a completeness critic then searched for surfaces, documents and rules the
lenses had not applied and raised six more candidates, four of which survived
the same two refuters. 155 agents; 84 raw findings; 65 after merging
duplicates; 47 survived verification; 24 were refuted.

**Treat the entries as claims that survived refutation, not as adjudicated
defects.** Each was produced by a read-only agent that had to demonstrate it at
`file:line`; the tier line is the doctrine refuter's reason for the severity.
Reproduce before acting. Line numbers are as of the merged tree on 2026-09-12.

## Tally

| Severity | Count | Disposition |
|---|---|---|
| BLOCKER | 0 | none |
| MAJOR | 0 | none |
| MODERATE | 2 | conditions on the merge, below |
| MINOR | 22 | recorded, deferred to scoped waves |
| OBSERVATION | 23 | recorded |
| Refuted | 24 | kept so they are not re-derived |

## The two moderates and the conditions

### F7-consumer-develop-01 (MODERATE, maintainer decision) - The documented 1.1.0-pinned lane destroys gateway diagnostics, and the 'names the pair on the wire' claim only holds on that untested lane's alternates

**Location:** `README.md:139-142 (also tools/README.md:22; B3: gateway/tests/test_schema_version_discrimination.py:831-841); root cause gateway/src/gateway.py:2240,2282,2314,2983,2995-2997`

**Claim:** b0666d0's README/tools/README note tells v1.1.0 producers to run --schema-path schema/zmeta-event-1.1.0.schema.json. Every gateway-minted SYSTEM_EVENT diagnostic is hardcoded zmeta_version:1.0 (gateway.py:2240,2282,2314); the outgoing self-check validates that diagnostic against the configured 1.1.0 schema, refuses it on the zmeta_version const, and rebuilds a content-free SCHEMA_VIOLATION with no error message and the wrong original_event_id. A consumer on the recommended lane gets no usable refusal reason at all. Separately, the governed claim that a missing ACOUSTIC level 'names the pressure pair on the wire' (8930fb8 commit body, CHANGELOG.md:12-14, doctrine log :2751) is true only against the 1.1.0-lane schema in isolation; against the dispatching union schema (schema/zmeta-event.schema.json) the first violation degrades to a whole-event dump with an empty path, and the reference gateway defaults to the locked v1.0 schema, not the 1.1.0 lane. The claim and the recommended launch lane are both unqualified where the actual behavior is lane-dependent.

**Evidence:** Live probe: gateway on --schema-path 1.1.0, valid ACOUSTIC forwarded, but the SCHEMA_INVALID diagnostic for a level-less event returns {'reason_code':'SCHEMA_INVALID','original_event_id':<never-sent id>,'path':'zmeta_version'} with no 'error' key. In-process: build_violation_event validates True on v1.0 lane, False on 1.1.0 lane ('1.1.0' was expected at zmeta_version). Separately, validate_schema on the same level-less event: against zmeta-event-1.1.0.schema.json first violation names pressure_pa/pressure_statistic at payload/features; against the dispatching zmeta-event.schema.json the message is the whole event object with empty path. grep for 'mixed-lane' in *.md returns only README.md:141, presented as a second-choice afterthought.

**Reproduction verifier:** Every literal claim in the finding reproduces on the working tree at 8930fb8, including the live probe, the in-process lane comparison, and all cited file:line locations. I attempted refutation on four axes and failed on all four: (1) the cited README/tools-README text says exactly what the finding says it says and was added by b0666d0 (git blame: README.md:139-142 and tools/README.md:22 both b0666d0f, 2026-09-10); (2) gateway.py:2240/2282/2314 do hardcode "zmeta_version": "1.0" in build_violation_event and the two sibling minters; (3) the live gateway on --schema-path schema/zmeta-event-1.1.0.schema.json does forward a valid ACOUSTIC event and does emit a content-free SCHEMA_VIOLATION with the wrong original_event_id for a level-less one; (4) validate_schema on the same level-less event does name the pressure pair against the 1.1.0 lane and does degrade to a whole-event dump with an empty path against the dispatching union schema, and the reference gateway default at gateway.py:1727 is schema/zmeta-event-1.0.schema.json, not the 1.1.0 lane. Three corrections to scope/attribution, all of which widen rather than narrow the finding, are in the evidence field. The one genuine attribution correction: the broken code is PRE-EXISTING at 282c9cf (gateway.py:2240 dates to dc5ba061, 2026-01-17, and the branches do not touch gateway.py at all - git diff --stat 282c9cf HEAD -- gateway/src/gateway.py is empty). What b0666d0 introduces is reachability and recommendation: run_gateway.py at 282c9cf had no --schema-path at all (git show 282c9cf:tools/run_gateway.py | grep -c schema-path returns 0), so the documented launcher could not reach the broken lane before this branch, and the README now tells v1.1.0 producers to go there. introduced_by_branch: true is therefore correct as to the fielded condition and should be qualified as "exposed and recommended by b0666d0; root cause pre-existing". Severity MAJOR holds: the named downstream consumer (the downstream COP) is specified to consume develop's 1.1.0 lane directly during the hold, which is precisely the lane on which refusal reasons are destroyed, and the minimal fix is an outer-ring documentation change (recommend the union lane, or qualify the wire claim), not a kernel change, so fix-before-merge rather than BLOCKER.

**Doctrine verifier:** Two of the three doctrine citations do not say what the finding needs, the second half of the defect is already booked and answered by an existing mechanism, and the root cause is pre-existing rather than branch-introduced, but the first half (a gateway that destroys its own diagnostic on the lane b0666d0 now documents) is real, unbooked, and matches an in-repo defect class the repo closed deliberately. (1) MIS-CITED, docs/zmeta_audit_playbook.md:170 discipline 5 reads "No vacuous pins, and the proof ships with the pin ... the demonstration must be an artifact in the repo, not an act in a session." It governs test pins and guards, not prose claims; it nowhere says "a claim must be true where it is asserted." (2) MIS-CITED, CLAUDE.md:69-72 gate 6 ("Solve needs via policy -> config -> profiles -> adapter mappings -> namespaced extensions before touching schema or core semantics") says nothing about documentation scope or diagnostics; it argues for the *remedy* (a documentation qualification is the outer ring here), not for the defect. (3) PARTLY SUPPORTED, CLAUDE.md:52-55 gate 3 literally protects data honesty ("Never make degraded, stale, low-confidence ... data look clean"), and nothing is laundered here: the event is still refused fail-closed, only the explanation is lost. Gate 3 reaches diagnostic legibility only by repo precedent (docs/zmeta_doctrine_review_log.md:181-183, R1-11-01: "The filterability gate 3 was tracking is restored at the layer the operator filters"). (4) SECOND HALF ALREADY ADJUDICATED AND ANSWERED, the "union schema degrades to a whole-event dump" behavior is the condition F1-04 already measured and booked (doctrine log:2478-2480, "the code that names this exact failure never fires because the schema rejects first with a raw internal message"), and its adjudicated answer is the guidance layer (doctrine log:2488, "diagnostics carry the fix ... the diagnostic that explains the wall should reach the first step that hits it"), which fires here: tools/validation_guidance.yaml:1802-1820 `acoustic-missing-level` detects on event content (modality + absent_all_paths spl_db/pressure_pa), not on the schema message, so it names the pressure pair under either schema. Nor is the claim false where asserted: CHANGELOG.md:5 and doctrine log F2-08:2745-2751 both scope the statement to "the 1.1.0 ACOUSTIC arm," and README.md:141-142 documents the mixed-lane selector as a stated option rather than burying it. (5) NOT BRANCH-INTRODUCED, `git show 282c9cf:gateway/src/gateway.py` already carries the hardcoded diagnostic stamps at 2240/2282/2314 and `--schema-path` at 2743; b0666d0 adds only the launcher passthrough and the README note, so `introduced_by_branch: true` is true of the exposure, not the defect. (6) WHAT SURVIVES, AND WHY MODERATE NOT MAJOR, the strongest anchor is one the finding missed: gateway/src/gateway.py:2159-2163 names this exact mechanism ("every wire diagnostic this gateway builds is stamped zmeta_version 1.0 ... the outgoing self-check would destroy it"), and gateway/tests/test_violation_event_self_validity.py:1-16 describes the precise symptom as the TV-09 defect ("original_event_id pointing at the never-transmitted TASK_ACK's own freshly-minted id ... The operator could not correlate the refusal") and closes it with a class sweep whose validator is pinned to schema/zmeta-event-1.0.schema.json (lines 76, 111, 167), so the newly documented lane sits outside the closure. That is a genuine consumer-facing gap on the lane the COP will use during the hold. But the only real fix (stamping or validating diagnostics per configured lane) collides head-on with the maintainer-adjudicated v1.0-stamped wire posture of R1-11-01 (doctrine log:174-184), and playbook discipline 7 (docs/zmeta_audit_playbook.md:194) requires that such a fix "implements what doctrine permits and records the tension ... It never decides a governance question inside a fix wave." A finding whose fix is by doctrine the maintainer's call is by the playbook's own scale MODERATE ("fix before merge unless the maintainer defers"), not MAJOR; and the lane posture is already routed to that same pending call at doctrine log F2-06:2683-2684 ("The default stays the locked lane pending a maintainer call"). Not BLOCKER: develop is a hold branch with no release cut, the locked v1.0 lane and its diagnostics are byte-identical and unaffected, and refusals still fail closed. The doctrine-permitted pre-merge action is the outer-ring one: qualify the README.md:139-142 and tools/README.md:22 lane note that the 1.1.0-pinned lane degrades gateway-minted diagnostics, and log the stamping collision for the maintainer alongside F2-06.

### B1-wave-read-07 (MODERATE, fix after merge) - The in-repo records for 7a01d35 omit the deliberately stale release-manifest state that the commit body itself records

**Location:** `docs/zmeta_refinement_worklog.md:5-33; docs/zmeta_refinement_handoff.md:51-120`

**Claim:** The commit body states plainly that the change is release-class, the manifest is deliberately not regenerated, and three kernel-gate hashes plus thirteen release-pin tests read stale as a result. Neither the worklog entry nor the handoff section added by the same commit mentions the manifest or any red test. Since the commit message is not part of the working tree a reader consults, the repository's own record of this wave does not answer what validation ran and what passed.

**Evidence:** git diff 282c9cf 7a01d35 for worklog/handoff contains no occurrence of 'manifest' relevant to this topic. Measured battery at the tip: 13 failed / 1859 passed / 1109 subtests, all thirteen in the two release-pin test files.

**Reproduction verifier:** Every factual claim in the finding reproduces exactly on the actual tree. The commit body of 7a01d35 does state the stale-manifest condition ("The release manifest is deliberately not regenerated here ... the three kernel-gate manifest hashes and the thirteen release-pin tests read stale against this commit until that cut runs"), and no file the same commit adds to the working tree records that condition anywhere. I widened the search beyond the two cited files to the entire commit diff (CHANGELOG.md, docs/zmeta_doctrine_review_log.md, spec/future-branch-roadmap.yaml, the guidance YAML) and still found zero added lines mentioning the release manifest, release-pin tests, kernel-gate hashes, or any red test; the only "stale" hits in the diff are unrelated guidance prose about TIMING_STATUS_STALE and profile values. The measured battery matches the stated numbers to the digit. Severity MINOR is correct: the information is not lost (it is in the commit message, and the branch is not being cut), the omission is a record-quality gap against AGENTS.md:148, and the working tree contains no incorrect statement, only a missing one. One citation is imprecise and corrected below, but it does not change the verdict; the on-point rule is the Handoff Standard, not the Release Limits divergence clause.

**Doctrine verifier:** The gap is real and undisposed, but the finding cites the wrong rule and therefore under-states it.

WHAT THE CITED DOCTRINE ACTUALLY SAYS. AGENTS.md:141-150 ("Handoff Standard") reads "A completed change should leave the next maintainer able to answer: ... what validation ran and what passed". It is vehicle-agnostic: it names no file, and the commit body of 7a01d35 does answer the question, naming both the deliberate non-regeneration and the exact stale surfaces ("the three kernel-gate manifest hashes and the thirteen release-pin tests read stale against this commit until that cut runs"). As cited, the finding rests on the reviewer's own premise that a commit message is not a record a reader consults, which is a preference, not rule text. The second citation is worse: AGENTS.md:134-140 is the only rule that names the worklog as the required vehicle for a manifest divergence, but its trigger is "A post-release main commit that regenerates the release manifest under the published identity". 7a01d35 is neither on main nor a regeneration; it is the mirror case. Applying it here is purposive, not textual. On the cited doctrine alone this finding would be REFUTED or an OBSERVATION.

THE RULE THAT DOES APPLY, WHICH THE FINDING MISSED. docs/zmeta_change_governance.md:299-306 sets the Implementation procedure for a governed change and closes "7. Run validation. 8. Update worklog and handoff with exact commands and results." That names precisely the two files the finding examined, and requires results, not merely a conclusion. 7a01d35 is a governed change on its own terms (the commit body: "the roadmap edit makes this commit release-class") and touches tools/validate.py, a validator, which AGENTS.md:77-79 places in the governed baseline. The worklog and handoff it adds carry no commands and no results at all, let alone the thirteen reds. docs/zmeta_change_governance.md:331 reinforces the same direction. This is a rule breach against text that names the vehicle, not a maintainer preference.

WHY MODERATE, NOT MINOR. Three things move it off the record-and-defer tier. First, it is not one commit: the same omission holds across all three tips (verified below), so the in-tree record of the entire wave is silent. Second, the merge context. develop is to be HELD without a cut for an unbounded period while the downstream COP consumes its 1.1.0 lane, so for that whole window the worklog resume note is the record a reader actually opens, and the three commit bodies are three levels down. Third, the repo states this exact hazard in "must never" terms at AGENTS.md:138-140: "an unexplained mismatch must never be the downstream verifier's first notice." The trigger clause does not literally cover this commit, but the hazard is identical and the hold makes it worse than the single-commit-to-next-cut horizon the rule was written for. The repo's own precedent shows the expected discipline: docs/zmeta_refinement_worklog.md:174-177 records the v1.1.24 manifest divergence in the worklog, citing "the post-release rule in AGENTS.md."

WHAT DOES NOT DISPOSE OF IT. Nothing in the tree books this. CHANGELOG.md's new Unreleased entry, the doctrine log cycle F1 additions, and handoff items 1-8 are all silent on the manifest and on any red test; handoff item 5's "cut as a release when verified" signals release-class status but says nothing about validation state. No maintainer ruling in the doctrine log covers it. The review brief's KNOWN-AND-EXPECTED note excludes the red tests themselves from being reported as a defect and assigns the acceptability of that state to F7; it does not excuse the record, which is a distinct claim.

A NOTE ON AN ADJACENT RULE I DECLINED TO STRETCH. Audit playbook discipline 5 (docs/zmeta_audit_playbook.md:170-186) says of an ephemeral proof: "Watching it go red in your working copy and saying so in the commit message is the practice this replaces." That is the same preference for an in-repo artifact over a commit-message attestation, but discipline 5 governs test pins, not validation records, and I do not count it as binding here.

CORRECTED ACTION. fix-after-merge, deliberately paired with MODERATE. The remedy that actually works is one docs-class worklog and handoff entry on develop covering the whole wave (commands run, the battery result, the thirteen release-pin tests and eleven kernel-gate lines that are stale by design, and that the cut resolves them). That commit is structurally post-merge; fixing it before merge would mean rewriting three wave-branch commits the maintainer intends to merge as-is. It should land with the merge event and before the hold begins, not be carried to the eventual release cut. Under docs/zmeta_audit_playbook.md:125-132 the maintainer may defer a MODERATE, and deferring this one is defensible since it self-resolves at the cut; the cost of deferring is that the hold is the exact window in which the record is load-bearing.

**Conditions set by the determination:** before the merge, the stale
`INVALID_MODALITY_FEATURES` hint on `exp/acoustic-pressure` (done, on the
branch) and the attribution trailer decision on 8930fb8 (maintainer's);
immediately after the merge, this register, the validation record in the
worklog and handoff, and the registry-count refresh in the ontology reference
and handoff item 6 (this commit); before the COP consumes `develop`, the
gateway diagnostic lane fix on its own branch from `develop`. Refused as
conditions: regenerating the manifest on `develop` (the Branching section
regenerates it at the cut), cutting now, re-opening Class D ceremony for the
experimental mints, and the `spec/versioning.md` challenge (its rule is
restated in the governance doc that was applied; F2-08 records the
relaxation).

## Rulings made on the documentation, 2026-09-12

At the maintainer's direction the three open questions were put to the
repository's own documents first (three independent readers and a refuter
per question, every citation opened), and ruled where the documents guide.
The test result is part of the record: each ruling names the passages that
decided it and the documentation defects the test surfaced.

1. **Gateway diagnostic stamping: keep the v1.0 stamp, fix the self-check.**
   Decided by doctrine entry R1-11-01 (the diagnostic-first posture rests on
   "a v1.0-stamped wire diagnostic"), the TV-09 invariant in
   `gateway/tests/test_violation_event_self_validity.py` (a minted diagnostic
   must never be refused by its own outgoing validation) and contract 2.4
   ("Consumers MUST select the schema and policy interpretation from that
   exact value"); a gateway validating a v1.0-stamped diagnostic against the
   configured 1.1.0 lane does what 2.4 forbids. Class C. Left for the
   maintainer: whether a gateway may ever author a 1.1.0-stamped diagnostic,
   and the default lane (F2-06). Documentation defects: `README.md:249-250`
   promises native codes on the 1.1.0 lane that no code produces;
   `README.md:139-142` and `tools/README.md:22` send 1.1.0 producers to the
   lane that destroys diagnostics without saying so; contract 7.9 and the
   ZMETA-GATEWAY class never state what a gateway stamps on a diagnostic it
   authors; the TV-09 pins are built on the 1.0 schema only; the gateway
   README never states the default lane; `CLAUDE.md:10` and `README.md:416`
   omit the 1.1.0 schema from the governed list; `spec/versioning.md:11`
   states as MUST what contract 2.5 states as SHOULD.
2. **Attribution trailers: stand as written, none from now on, rewrite is
   the maintainer's election** (doctrine F2-09). Decided by `CLAUDE.md`
   (human-only) and guided by `docs/v1_1_21_precut_panel_register.md` item 11
   (the same class, banked with the reword left to the maintainer) and the
   Branching section (an agent creates and commits on local branches and
   stops). Three commits carry the trailer, not two: `9814f2b` on `develop`
   as well. Documentation defects: the rule lives only in the advisory
   working guide, outside the authority stack; the authority order is silent
   on an instruction from outside the repository; no guard checks trailers;
   `CONTRIBUTING.md` is silent; the Branching section never says whether an
   unpushed branch may be amended before it merges.
3. **`level_reference` without `spl_db`: no binding; record the question.**
   Decided by playbook standing discipline 10 (a defence against an
   unobserved failure goes to the live-test checklist and the code is left
   alone); F2-08's pair binding does not transfer because it was the
   condition on which the relaxation shipped and a leak guard for the held
   marker. Recorded as checklist question F2-Q1; the description, README and
   registry now scope the marker to `spl_db`. Left for the maintainer:
   whether restoring an invariant the branch lapsed counts as hardening,
   which would reopen (A). Documentation defects: the F2-08 decision was
   silent on a consequence of its own relaxation (now noted); the registry
   entry was not revisited when its subject field became optional (now
   noted); Class D lists a new required field and nothing covers a
   conditional binding; the guidance set flags three corners of the pair and
   not the fourth, and `tools/explain.py` cannot show a rule on a clean
   stream anyway; the checklist had no section for an experimental cycle.

---

## MINOR: recorded and deferred

Below the fix floor. Each reproduces; the tier line is why it sits here.

### B2-acoustic-read-03 - est_error_basis is documented inside the observation-modality feature-contract list, a section whose stated scope excludes it

**Location:** `schema/README.md:134-138` (exp/acoustic-1.1.0; introduced by the branch)

**Claim:** The new est_error_basis bullet is inserted into '### Modality-Specific Feature Schemas', scoped to 'active observation modalities', between the ACOUSTIC and NETWORK bullets. timing_quality is not an observation modality and is not conditional on payload.modality; the marker applies to five event types (OBSERVATION/INFERENCE/FUSION/STATE/COMMAND). A reader will take a modality-independent marker for an observation-modality feature, and the insertion splits the RF/EO/IR/ACOUSTIC/NETWORK list, its organizing principle. Other 1.1.0 additions in the same file live under their own headings.

**Evidence:** schema/README.md:118-140 (at b0666d0) shows the scope sentence, then EO/IR/ACOUSTIC bullets, then the new timing_quality bullet, then NETWORK. schema/zmeta-event-1.1.0.schema.json:877 places est_error_basis inside $defs/timing_quality (line 862), not inside any modality if/then arm.

**Tier:** The bullet names timing_quality correctly, and other adopter-facing channels state it without any modality condition, so this is discoverability drift, not laundering. Disposition: record and defer.

### B2-acoustic-read-05 - The basis marker stops at payload.timing_quality; the SYSTEM_EVENT TIME_STATUS path accepts the same key with no enum at all

**Location:** `schema/zmeta-event-1.1.0.schema.json:1783-1795` (exp/acoustic-1.1.0; introduced by the branch)

**Claim:** The 1.1.0 schema carries a second, inline copy of the four timing members in the SYSTEM_EVENT TIME_STATUS arm (payload.metrics), the object the gateway's own timing state machine reads and the canonical place a source declares clock discipline to the network. It did not gain est_error_basis and has no additionalProperties:false, so the key is accepted there with ANY value. The registry entry excludes SYSTEM_EVENT and disclaims only the other alternate path, so this asymmetry is neither governed nor recorded, even though F2-02's own rationale applies to TIME_STATUS at least as strongly.

**Evidence:** Probe: a SYSTEM_EVENT/TIME_STATUS with payload.metrics.est_error_basis='TOTALLY_MADE_UP' validates. grep for est_error_basis in the schema returns exactly one governed occurrence, line 877.

**Tier:** The permissive TIME_STATUS arm predates the branch; what the branch introduces is the asymmetry of meaning between the two now-divergent timing paths. Disposition: record and defer.

### F1-design-gates-01 - TIMING_ERROR_BASIS is the only direct-to-experimental mint in the wave that does not state the promotion evidence bar or name any roadmap tripwire

**Location:** `spec/extension-registry.yaml:222-273` (exp/acoustic-1.1.0; introduced by the branch)

**Claim:** ACOUSTIC_LEVEL_REFERENCE and ACOUSTIC_PRESSURE_LEVEL each state explicitly that the promotion evidence bar is NOT claimed met and that the entry enters experimental with that condition unmet by maintainer adjudication. TIMING_ERROR_BASIS's notes carry neither that sentence nor a reference to independence/section 2.6, in the registry, the doctrine log (F2-02), or the CHANGELOG, and no future-branch-roadmap candidate references TIMING_ERROR_BASIS at all (the acoustic pair got one with two tripwires). A reader sees a risk-relevant experimental marker with no statement of its evidential standing and no path to promotion or retirement, while its evidence is an internal audit item plus the repo's own reference adapters, which do not meet the registry's independence test.

**Evidence:** grep -n 'NOT claimed met|not met' spec/extension-registry.yaml -> only :416 and :485. TIMING_ERROR_BASIS notes (:262-273) name only the adjudication date and R1-11-04. docs/zmeta_doctrine_review_log.md:2602-2628 (F2-02) never names the bar. grep -n 'TIMING_ERROR_BASIS' spec/future-branch-roadmap.yaml -> no hits; validate_future_roadmap.py only checks roadmap->registry direction, never registry->roadmap.

**Tier:** The promotion-bar clause applies only to reserved/proposed entries moving up, not new mints, and most existing entries already omit it. Disposition: record and defer.

### F1-design-gates-03 - TIMING_ERROR_BASIS declares preserve-under-projection but the projection checker exempts the whole timing_quality subtree, so the basis can be dropped or the bound widened with zero violations

**Location:** `tools/validate_projection.py:877-878` (exp/acoustic-1.1.0; introduced by the branch)

**Claim:** The entry sets risk_relevant:true, profile_projection_behavior:preserve, with a security note that the basis must survive projection with the bound. validate_projection.py explicitly skips undeclared-omission detection for any path starting with payload.timing_quality, checking only that the object survives at all; a projection that strips est_error_basis while keeping est_error_ms produces zero violations. Separately, policy/profile-precision.yaml's ttl_down_error_up behavior can widen est_error_ms at lower profiles while est_error_basis (not a governed projection path in conformance/profile_projection_field_catalog.yaml) survives unchanged, so a policy-widened bound stays labelled MEASURED. Either failure mode launders a conventional/degraded value as clean, the exact condition the marker was minted to prevent. The equivalent acoustic markers ARE protected: dropping level_reference or pressure_statistic does fire PROJECTION_UNDECLARED_OPTIONAL_OMISSION.

**Evidence:** tools/validate_projection.py:877-878 'if path.startswith("payload.timing_quality")...: continue'. Probe: source with est_error_basis CONVENTION_DEFAULT, projected with it dropped -> compare_projection returns []. Contrast: dropping level_reference on an ACOUSTIC observation returns PROJECTION_FIELD_CHANGED + PROJECTION_UNDECLARED_OPTIONAL_OMISSION. policy/profile-precision.yaml:55-60 ttl_and_error behavior ttl_down_error_up covers est_error_ms with no basis path anywhere in the catalog.

**Tier:** The exemption is pre-existing and systemic, shared by POWER_REFERENCE, and no shipped adapter emits the field yet, so exposure is only latent. Disposition: record and defer.

### F2-governance-02 - Registry entry counts in both the ontology reference and the booked handoff item are falsified by the two acoustic commits (63/62-63 -> 66/65-66)

**Location:** `docs/zmeta_ontology_reference.md:630-632` (exp/acoustic-1.1.0; introduced by the branch)

**Claim:** AGENTS.md requires matching docs to update in the same change as a governed registry edit. b0666d0 added two registry entries (63->65) and 8930fb8 a third (65->66), all experimental; neither touched docs/zmeta_ontology_reference.md, which states '63 entries... 16 experimental' as current fact in two places, nor updated handoff item 6, which asserts 'all 63 entries carry adapter_gateway_status: none and 62 of 63 carry encoding_status: none' (substance still holds at 66/66 and 65/66, only the count is wrong). No validator guards either claim, so nothing reports the drift at the cut either. The frozen historical records that also say 63 are correctly left alone.

**Evidence:** Counted per commit from spec/extension-registry.yaml: 282c9cf/7a01d35 = 63/16; b0666d0 = 65/18; 8930fb8 = 66/19 (validate_extension_registry.py confirms entries=66). git show b0666d0/8930fb8 --stat list no docs/zmeta_ontology_reference.md. pytest on test_governed_doc_claims.py etc. -> 28 passed, nothing pins these counts.

**Tier:** The ontology reference is release-pinned, due at the cut not the merge; the handoff entry is a frozen record correctly left alone. Disposition: record and defer.

### F2-governance-03 - b0666d0's manifest-stale statement names two manifest-listed artifacts when three changed

**Location:** `b0666d0 (commit message body)` (exp/acoustic-1.1.0; introduced by the branch)

**Claim:** b0666d0's body says the commit changes two manifest-listed artifacts (schema/zmeta-event-1.1.0.schema.json, spec/extension-registry.yaml), but it also changed tools/validate_extension_registry.py, which is manifest-listed under conformance_tools; both the artifact list and rollup list understate what goes stale. 8930fb8's body correctly names its equivalent change. Harmless to correctness since the manifest regenerates wholesale at the cut.

**Evidence:** Cross-referencing touched files against release/zmeta-release-manifest.yaml paths: b0666d0 touches schema/zmeta-event-1.1.0.schema.json, spec/extension-registry.yaml, and tools/validate_extension_registry.py (conformance_tools group), the third unnamed in the commit body.

**Tier:** The governance rule requires only a stale-manifest statement, not a full enumeration, and the undercount is harmless since the manifest regenerates wholesale. Disposition: record and defer.

### F3-locked-kernel-02 - 65 of 79 guidance citations into the 1.1.0 schema point at the wrong lines after b0666d0's insertions, and the test only checks non-emptiness

**Location:** `tools/validation_guidance.yaml:529-573` (exp/acoustic-1.1.0; introduced by the branch)

**Claim:** b0666d0 inserted 5 lines (est_error_basis) shifting every anchor below; 8930fb8 inserted 24 more in the ACOUSTIC arm. Neither re-anchored the guidance. 65 of 79 citations across 32 violation codes now land on different content, some with live emitters, so validate.py can print operator-facing remediation citing the wrong field. gateway/tests/test_validation_guidance.py asserts only that citations exist and are non-empty strings, never that they resolve.

**Evidence:** Probe comparing cited ranges at 7a01d35 vs tip: 65/79 moved across 32 codes. INVALID_QUALITY_BEARING_FRAME cites :949-952, which is now the geo_status block (bearing_frame moved to 954). PLATFORM_STATUS_POWER_MISSING cites 2079-2087, now 'detection_range_m' not the battery metrics. Inline prose anchors drifted too (band line 1250 vs actual 1255; protocol line 1347 vs actual 1376).

**Tier:** The file discloses citations may drift and are non-authoritative; F1-04 and F2-07 class such drift as a documentation bug, not a defect. Disposition: record and defer.

### F7-consumer-develop-04 - The only runnable ACOUSTIC example is exactly the under-declared shape the new rule flags, and the new pressure carrier has no example at all

**Location:** `examples/zmeta-v1.1-examples.jsonl:3` (exp/acoustic-1.1.0; introduced by the branch)

**Claim:** b0666d0 and 8930fb8 mint ACOUSTIC_LEVEL_REFERENCE and ACOUSTIC_PRESSURE_LEVEL and add guidance urging producers to declare the reference / use the pascals pair, but never touch examples/. The repo's single ACOUSTIC example still has spl_db with no level_reference (exactly what acoustic-level-without-reference flags), and no example anywhere shows pressure_pa+pressure_statistic. README.md points a consumer building a 1.1.0 producer at this file.

**Evidence:** git diff --stat 282c9cf 8930fb8 -- examples/ is empty. The example event has spl_db:72.3 and no level_reference; running it beside one failing line fires [CONSIDER] acoustic-level-without-reference on it. grep -rln pressure_pa across examples/conformance finds no example, only schema/registry/guidance/tests.

**Tier:** F2-08 ruled the existing example stays valid and fixed the field description instead; only the missing pressure-pair example is a genuine gap. Disposition: record and defer.

### F7-consumer-develop-07 - Four release-safety NEGATIVE guards go dark for the whole hold, not merely red

**Location:** `gateway/tests/test_release_package.py:133` (develop after the merge; introduced by the branch)

**Claim:** Of the 13 booked-red release-pin tests, four are negative tests proving the packager refuses bad input (checksum mismatch, attestation hash mismatch, formal release shipping the unpopulated notes template, missing package artifact). All four abort in fixture setup because the stale manifest fails validation before the test body ever runs its own assertion, so for the whole hold there is no evidence the packager still refuses any of these bad states. A fifth test would go from failing to skipping under proposed Option 2 of F7-consumer-develop-03.

**Evidence:** pytest test_release_package.py::test_checksum_mismatch_fails aborts inside _build_temp_package with SystemExit: release manifest validation failed, before the doctored-checksum assertion executes. Same for the other three named tests. Mitigation available: build_release_manifest.py --dry-run against the working tree already validates clean, so fixtures could rebuild a fresh manifest in the temp dir rather than relying on the committed one.

**Tier:** The exposure is delayed detection, not lost detection: the packager is re-exercised and the guards re-run at the release cut before shipping. Disposition: record and defer.

### FC-01 - The post-merge kernel-gate red band is 14 manifest lines, not the 11 the branches document, because develop is already red on 4 before any merge

**Location:** `docs/zmeta_change_governance.md:296-311` (develop after the merge; not introduced by the branches)

**Claim:** Every lens measured the accepted red band on the working tree (the three stacked commits) and got 11 RELEASE_MANIFEST_* lines. Nobody measured develop. develop's own commit 9814f2b changed docs/zmeta_change_governance.md, which is manifest-listed under process_governance (release/zmeta-release-manifest.yaml:134 and :500), so develop reads 4 manifest lines red today with no merge at all. After the three merges the gate reads 14 lines, and no record anywhere states that number. That matters for the hold specifically: playbook standing discipline 3 says never relay a self-reported green, and the practical form of that during a weeks-long red hold is an exact expected-red list. A maintainer or the COP team re-running the gate on develop has only the branches' '11' and '13' to check against, so three legitimate lines look like drift and any genuine fourteenth would look expected. The Branching section that sanctions this state scopes the sanction to 'an experimental branch that changes a manifest-listed artifact' and says in the same section that 'develop is expected to be green', so the doc as written does not actually cover the state the merge produces.

**Evidence:** In a throwaway clone with the three branches really merged into develop in dependency order:
  git checkout origin/exp/acoustic-pressure; python tools/validate_conformance.py --kernel-gate | grep -c "FAIL RELEASE_MANIFEST" -> 11
  git checkout develop (merged);            same command -> 14
  git checkout origin/develop (pre-merge);  same command -> 4
The pre-merge four are: RELEASE_MANIFEST_ARTIFACT_HASH_MISMATCH item=docs/zmeta_change_governance.md, RELEASE_MANIFEST_GROUP_HASH_MISMATCH item=process_governance, RELEASE_MANIFEST_TOP_LEVEL_HASH_MISMATCH item=process_governance_hash, RELEASE_MANIFEST_BUNDLE_HASH_MISMATCH (the bundle line overlaps with the branches', which is why 11+4 lands on 14). Test count is unchanged: python -m pytest -q on merged develop gives 13 failed / 1858 passed / 1109 subtests, exactly the declared release-pin set; validate_examples --strict --require-all 51/51; validate_future_roadmap ok candidates=20; git diff --check clean.

**Tier:** The governance doc's stale-manifest clause covers develop's pre-merge red state and calls it expected, and each commit body states its own artifact. Disposition: record and defer.

### FC-06 - A release-safety test flakes on mtime granularity, producing an occasional fourteenth red that is indistinguishable from the accepted band during the hold

**Location:** `gateway/tests/test_release_signing.py:167` (pre-existing at 282c9cf; not introduced by the branches)

**Claim:** On the first full-suite run in a fresh clone of merged develop the suite reported 14 failures rather than 13, the extra one being test_ensure_package_zip_refuses_a_stale_zip_and_never_overwrites with 'a package zip older than the package directory must refuse, not be silently checksummed'. It passes in isolation and passed on three subsequent full runs at both merged develop and the branch tip, so it is a filesystem-timestamp race rather than anything the branches did. It is worth one line in the record because of the hold: for as long as develop sits red on a documented set of 13, a test that intermittently adds a fourteenth is exactly the noise that trains a reader to stop counting, and the one it adds is a negative guard on release packaging. Pre-existing at 282c9cf; the file is not touched by any of the three commits.

**Evidence:** Fresh git clone, three real merges, then python -m pytest -q -> '14 failed, 1857 passed, 2 skipped' with FAILED gateway/tests/test_release_signing.py::test_ensure_package_zip_refuses_a_stale_zip_and_never_overwrites alongside the 13. Immediately after: python -m pytest -q gateway/tests/test_release_signing.py -> 26 passed; the same file passes at origin/exp/acoustic-pressure in the clone (26 passed) and in the real repository (26 passed); three further full runs (merged develop, branch tip, a second fresh clone) all gave exactly 13 failed. git log 282c9cf..8930fb8 -- gateway/tests/test_release_signing.py -> no commits.

**Tier:** It is a concrete, fixable test defect, not a bare state observation, since its complement test defends the same race with os.utime. Disposition: record and defer.

### B3-pressure-read-01 - New reserved-leak arm is modality-blind and will refuse legitimate future reserved feature contracts

**Location:** `tools/validate_extension_registry.py:322-385` (exp/acoustic-pressure; introduced by the branch)

**Claim:** _declared_feature_keys() collects property names under EVERY payload.features arm across both schemas, and the new observation_feature_contract check compares an entry's payload_scope leaf against that undifferentiated union without consulting allowed_event_subtypes. Generic member names (bandwidth_hz, duration_ms, etc.) are shared across modality arms, so a reserved/proposed feature contract for a new modality (RADAR, LIDAR, SEISMIC, all planned on the roadmap) gets falsely refused because a different modality already uses the same leaf name, with a misattributing error message.

**Evidence:** Probe: a temp RADAR_FEATURE_CONTRACT entry (reserved, payload_scope bandwidth_hz+range_m) is refused as REGISTRY_RESERVED_SCHEMA_LEAK 'bandwidth_hz is declared by the 1.0 schema', though that field belongs to the RF arm only. _declared_feature_keys(1.1.0 schema) returns 23 keys spanning all modality arms undifferentiated.

**Tier:** The shipped pin already asserts the exact claimed shape; the over-breadth is unobserved and zero-instance, so hardening it now would be speculative. Disposition: record and defer.

### B3-pressure-read-02 - The required-list relaxation lets level_reference dangle with no spl_db to reference, and no guard catches it

**Location:** `schema/zmeta-event-1.1.0.schema.json:1294-1336` (exp/acoustic-pressure; introduced by the branch)

**Claim:** Before 8930fb8 spl_db was required, so level_reference (defined as 'Reference of spl_db') always had a referent. After the relaxation, an event may carry only pressure_pa+pressure_statistic plus a level_reference with no spl_db, and it validates; a producer can even assert DB_RELATIVE (declaring an uncalibrated level) on an event whose only level is a calibrated pressure_pa, a direct contradiction on the wire. The commit applies pair-binding (dependentRequired) to pressure_pa/pressure_statistic in both directions and ships two guidance rules for that half-filled pair, but applies no symmetric guard to the now-orphaned reference marker, and the case is not discussed anywhere in the records.

**Evidence:** Probe against the schema: features {center_freq_hz, pressure_pa, pressure_statistic, level_reference:DBFS} -> VALID; {center_freq_hz, pressure_pa, pressure_statistic, level_reference:SPL_RE_1UPA} -> VALID. No guidance rule mirrors acoustic-pressure-without-statistic for the orphaned level_reference case. grep of doctrine/handoff/CHANGELOG for 'dangl|without spl|bind' returns no hits.

**Tier:** Gate 3 forbids laundering dirty data as clean; no decibel value exists here to launder, and the shape is unobserved and zero-instance. Disposition: record and defer.

### F3-locked-kernel-01 - Guidance for INVALID_MODALITY_FEATURES still tells an ACOUSTIC producer that spl_db is required, contradicting the 8930fb8 relaxation

**Location:** `tools/validation_guidance.yaml:545-546` (exp/acoustic-pressure; introduced by the branch)

**Claim:** 8930fb8 relaxed the 1.1.0 ACOUSTIC required list and updated the structural rules for it, but not this per-code remediation text, which still reads 'ACOUSTIC requires center_freq_hz and spl_db and prohibits power_db and source_type'. It now directs a pascals-only producer to fabricate a decibel it cannot honestly state, the exact laundering shape F2-01 identified. Reach is limited today (the code has no emitter and explain.py reads only structural_rules), but it is a wrong governed-surface claim shipped by the same branch stack that made it wrong.

**Evidence:** tools/validation_guidance.yaml:545-547 stale text vs schema required=['center_freq_hz'] plus if/then. Live gateway run accepted a pressure-only ACOUSTIC event end to end. Correctly updated sibling: gateway/tests/test_structural_guidance.py:79 acknowledges the change.

**Tier:** The guidance file's own header calls it advisory, non-normative; F1-04 rules a wrong hint is a documentation bug, below the fix floor. Disposition: record and defer.

### F2-governance-01 - No commands or gate results recorded for any of the three commits

**Location:** `docs/zmeta_refinement_worklog.md:1-35` (the stack; introduced by the branch)

**Claim:** docs/zmeta_change_governance.md:306 and AGENTS.md:123,148 require exact commands and results in the worklog/handoff for every implementation, with the repo's own established form being an explicit battery line. None of the three commits records a single gate command or result anywhere in the tracked records; the worklog/handoff narrate rulings and surfaces but never a pass/fail count. Merging three branches into develop and holding without a cut leaves the recorded evidence of what was green absent exactly where the release-pin reds make self-reported green unverifiable at a glance.

**Evidence:** git show <hash> | grep -iE for battery/pytest/kernel gate/examples returns only test source lines for all three commits, never a results block. Contrast docs/zmeta_refinement_handoff.md:764-765,967-968,1237-1238 and worklog:311 which do carry battery lines. Author ran the gates independently this session: validate_examples --strict --require-all -> 51/51 exit 0; validate_future_roadmap.py exit 0; validate_extension_registry.py exit 0 entries=66; pytest on touched files -> 174 passed. Those results exist only in this session (the ephemerality playbook discipline 5 exists to end).

**Tier:** Develop's own branching rule places the authoritative battery record at the integration merge, not before it, so it cannot gate the merge. Disposition: fix after merge.

### B1-wave-read-01 - explain.py tracebacks on a JSON-array input file that validate.py accepts

**Location:** `tools/explain.py:159` (wave/f1-field-evidence; introduced by the branch)

**Claim:** explain.py always parses --file line-by-line as JSONL and calls ev.get('event') on whatever json.loads returns. validate.py selects parse mode by suffix, so a .json file holding an array is legal input to it. Handed the same path, explain.py prints the correct validate report and then raises AttributeError: 'list' object has no attribute 'get'. A pretty-printed multi-line JSON file fails even more silently (every line raises JSONDecodeError, swallowed, guidance never prints, no word to the user).

**Evidence:** Reproduced: validate.py on a JSON-array file reports normally; explain.py on the same file crashes with the named traceback at the eid = (ev.get('event') or {}).get(...) line.

**Tier:** explain.py is non-normative and prints validate.py's authoritative verdict before crashing, so no event is laundered, only an advisory hint is lost. Disposition: record and defer.

### B1-wave-read-02 - Naive-timestamp detector misreads a negative UTC offset and misses a positive one

**Location:** `tools/explain.py:60-67` (wave/f1-field-evidence; introduced by the branch)

**Claim:** has_naive_timestamp treats a timestamp as naive unless it ends with 'Z' or contains '+' after index 10. A conformant offset form like -07:00 fires timestamp-missing-zulu with a hint asserting no timezone designator is present, which is false; +07:00 never fires the rule at all even though the schema pattern rejects it just as hard. The remediation itself (emit UTC with Z) stays correct.

**Evidence:** Probe against the structural_rules matcher: ts='2026-09-10T12:00:00-07:00' -> matches True (wrong assertion); ts='...+07:00' -> matches False (missed).

**Tier:** The guidance header calls a wrong hint a documentation bug, never a conformance defect, since the schema rejects both offsets regardless. Disposition: record and defer.

### B1-wave-read-05 - test_guidance_prints_once_per_code_per_run passes vacuously when guidance emission is switched off entirely

**Location:** `gateway/tests/test_validation_guidance.py:163-173` (wave/f1-field-evidence; introduced by the branch)

**Claim:** The test's only assertion is len(guidance_lines) == len(set(guidance_lines)), which an EMPTY list also satisfies -- it asserts no lower bound and cannot distinguish 'printed once' from 'never printed'. Only the sibling test_guidance_is_advisory_only's 'at least one line' assertion closes that gap; the two pins are independent, and the once-per-run pin the commit body names does not itself catch total suppression.

**Evidence:** Mutation disabling guidance emission entirely: the once-per-run test alone still passes (rc=0); the advisory-only sibling test alone fails (rc=1). A mutation removing the dedupe (not suppression) correctly fails the once-per-run test, so it does catch its stated regression -- just not total silence.

**Tier:** A sibling test asserts at least one guidance line prints, so total suppression still produces a signal in the same CI run. Disposition: fix after merge.

### F6-records-voice-01 - 'Three governed codes with no emitter' undercounts; the same commit's guidance file names five

**Location:** `CHANGELOG.md:88-90` (wave/f1-field-evidence; introduced by the branch)

**Claim:** The commit body, CHANGELOG, and handoff item 7 all state exactly three no-emitter codes (OBSERVATION_HAS_CLASSIFICATION, INVALID_MODALITY_FEATURES, RF_WINDOW_MIDPOINT_INVALID). The guidance file landed in the same commit states the identical no-emitter standing for two more, INVALID_COMMAND_GEOMETRY and INVALID_GEO_FIELD, both equally unwired in the tree, and omitted from the AAR decision list (emitter / reserved wire vocabulary / retire).

**Evidence:** Scan of the 61 guidance entries for a no-emitter statement returns five codes, not three. grep confirms no emitter for INVALID_COMMAND_GEOMETRY or INVALID_GEO_FIELD anywhere in gateway/tools/adapters.

**Tier:** Handoff item 7 already books the no-emitter class and its full decision menu; what escaped is two names inside an already-booked category. Disposition: record and defer.

### F6-records-voice-02 - F1-04's '10 of 61 violation codes carry any message' is not reconstructible from the tree

**Location:** `docs/zmeta_doctrine_review_log.md:2478-2479` (wave/f1-field-evidence; introduced by the branch)

**Claim:** Neither reading checks out: policy/violation-codes.yaml has no message field at all (0 of 61), and the reference gateway emits 36 distinct codes each with a non-empty message. The measurement's surface is unnamed, so it cannot be reproduced or re-run, and as written it reads false against both surfaces that exist.

**Evidence:** yaml load of violation-codes.yaml -> 0 entries with a 'message' key. Regex over validators.py _violation() call sites -> 36 distinct codes, all with a message argument.

**Tier:** The entry is a point-in-time record naming no surface; the decision it drove is unchanged regardless of the true count. Disposition: record and defer.

### F7-consumer-develop-02 - The two new acoustic-level guidance rules can never fire on a clean stream, and their fixture bypasses the CLI that would show it

**Location:** `tools/explain.py:157` (wave/f1-field-evidence; introduced by the branch)

**Claim:** explain.py short-circuits before loading any structural rule when the input validates clean ('failed=0' in out and 'FAIL' not in out: return). acoustic-level-without-reference and acoustic-level-on-locked-lane both target schema-VALID events (an under-declared spl_db, or a v1.0 event using the open features namespace), so through the tool's only entry point they print only as a side effect of some unrelated event in the same file failing; on a clean 1.1.0 stream, including the downstream COP's Orcasound producer that the rule was minted for, the advisory can never appear. gateway/tests/test_structural_guidance.py calls explain.matches() directly, never main(), so the pin proves the rule matches and never that the CLI a consumer runs ever prints it.

**Evidence:** The shipped ACOUSTIC example (spl_db, no level_reference) alone in a file: explain.py prints 'total=1 passed=1 failed=0' with no GUIDANCE block. The identical event plus one unrelated failing line: explain.py prints '[CONSIDER] acoustic-level-without-reference' for the PASSING event. Identical event content, opposite output, decided by an unrelated neighbor's failure. grep of gateway/tests for explain.py returns only test_structural_guidance.py, which never invokes main().

**Tier:** The guidance file is advisory/non-normative by its own header and F2-07 rules a wrong hint a documentation bug, below the fix floor. Disposition: record and defer.

### F7-consumer-develop-05 - explain.py and its --no-guidance flag are on no consumer-facing documentation surface, though explain.py is the only place the honest ACOUSTIC-level answer is stated

**Location:** `tools/README.md:1-260` (wave/f1-field-evidence; introduced by the branch)

**Claim:** 7a01d35 lands explain.py, a consumer diagnostic tool, without adding it to any surface a consumer reads; tools/README.md's 17-section tool catalog has no entry for it, and no README.md/docs/*.md mentions it or --no-guidance. This matters acutely here: on the README-recommended 1.1.0 lane the gateway wire says nothing useful (see F7-consumer-develop-01), and tools/validate.py alone (after 8930fb8's if/then) never mentions spl_db as an option, only pressure_pa/pressure_statistic -- explain.py is the sole complete, correct answer, and it is undiscoverable.

**Evidence:** grep -rn 'explain\.py' across *.md/*.yaml/*.py/*.txt (excluding local/.tmp/release) returns only CHANGELOG.md, the tool itself, its own test, and validation_guidance.yaml's internal reference -- no README. Without it, tools/validate.py on a level-less event reports only 'pressure_pa'/'pressure_statistic' required, never spl_db.

**Tier:** tools/README.md already omits 13 of 35 tools with no enforcing test, so explain.py is the 14th instance of a pre-existing gap. Disposition: record and defer.

---

## OBSERVATION: recorded

| Id | Where | Branch | What | Why this tier |
|---|---|---|---|---|
| `B2-acoustic-read-07` | `spec/extension-registry.yaml:222` | exp/acoustic-1.1.0 | TIMING_ERROR_BASIS and ACOUSTIC_LEVEL_REFERENCE inherit ignorable_by_default:true though risk_relevant, unlike ACOUSTIC_PRESSURE_LEVEL, which sets it false for the same mechanism. | The registry rule binds ignorable_by_default only to must_preserve_when_used_for_policy, which both entries set false, so no rule is actually breached. |
| `B2-acoustic-read-08` | `CHANGELOG.md:21` | exp/acoustic-1.1.0 | CHANGELOG.md and other process records have five broken paragraph wraps, including a 21-character orphan fragment and a 106-character overrun line. | The documentation-voice rule governs word choice and rhetoric; no governed text sets a wrap width, so this is cosmetic house habit. |
| `F1-design-gates-06` | `tools/validation_guidance.yaml:1871-1890` | exp/acoustic-1.1.0 | A guidance rule offers the experimental 1.1.0 acoustic marker to locked-lane producers with no experimental/unpublished status qualifier, unlike its sibling rule. | The registry marks the entry experimental and 1.1.0-scoped by default, and three other wave-era rules referencing 1.1.0 vocabulary carry no qualifier either. |
| `F1-design-gates-07` | `docs/zmeta_doctrine_review_log.md:976-982` | exp/acoustic-1.1.0 | The two-leg promotion-evidence bar never fires on direct-to-experimental mints, and this wave creates three more, raising the uncounted recurrence from one to four. | Two of the three new entries name both priors in their notes, and A1-01 books the scope gap for its next revision. |
| `F1-design-gates-08` | `spec/extension-registry.yaml:368-378` | exp/acoustic-1.1.0 | level_reference:DBFS keeps a decibel value in the canonically-named spl_db field, satisfying contract 6.5's purpose but not its literal text requiring conversion or an extension field. | The tension is recorded in three places and the corrective contract sentence is booked for the post-lock pass. |
| `F3-locked-kernel-03` | `gateway/tests/test_run_gateway_launcher.py:27-52` | exp/acoustic-1.1.0 | The D1-01 launcher fix's test only checks that --schema-path appears in forwarded argv; no test starts a gateway or sends an event through either lane. | The test asserts exactly the passthrough claim it makes and fails if removed; the README's union-schema claim is pinned by another suite. |
| `F4-registry-roadmap-03` | `tools/validate_extension_registry.py:795-806` | exp/acoustic-1.1.0 | REGISTRY_LAST_UPDATED_STALE compares the top-level stamp only against the newest date_added, so an edit-only wave that adds no entry ships undetected. | X1-02 adjudicated this exact shape terminal with no standing apparatus minted; recurrence lands on a fresh citing entry, not a fix. |
| `F6-records-voice-05` | `docs/zmeta_refinement_handoff.md:3` | develop after the merge | The handoff's CURRENT STATE header still reads the 2026-08-13 post-v1.1.25 relock text, unrefreshed by three branches with two new doctrine cycles. | The header stays accurate to the published baseline, header refreshes are release-publication events by precedent, and stale CURRENT STATE headings pre-exist elsewhere. |
| `F7-consumer-develop-03` | `release/zmeta-release-manifest.yaml:1-5` | develop after the merge | kernel-gate exits with 11 manifest failures and 13 release-pin tests fail on develop, held open-ended with no stated end date for the COP's consumption window. | The governance doc's carve-out for an unreleased branch covers develop by its own text, so the red state is doctrine-prescribed. |
| `FC-02` | `docs/zmeta_refinement_worklog.md (Current Resume Note)` | develop after the merge | Commit 9814f2b, which establishes the branching rule and touches a manifest-listed governance doc, has no CHANGELOG, worklog, or handoff entry naming it. | The governance doc sits in process-guidance, not the governed baseline, so the cited update-in-same-change rule never triggers on it. |
| `B2-acoustic-read-09` | `tools/run_gateway.py:10-13` | pre-existing at 282c9cf | run_gateway.py's --schema-path passthrough reaches an unguarded json.load, so a non-JSON schema path exits with a raw JSONDecodeError traceback. | The crash is pre-existing gateway behavior; the repo's own register grades a strictly worse instance of this shape as OBSERVATION too. |
| `F4-registry-roadmap-05` | `tools/validate_extension_registry.py:359-383` | pre-existing at 282c9cf | No check sweeps schema-declared feature members against the registry, so a 1.1.0 feature member with zero registry record is invisible to the validator. | The narrower targeted-check design is already documented and accepted as sufficient for the current registry's risk profile, not an undetected defect. |
| `F7-consumer-develop-10` | `tools/README.md:94-97` | pre-existing at 282c9cf | tools/README.md still claims validate.py uses the version-discriminated union schema, though it actually selects the lane schema by declared zmeta_version. | The lane-selection behavior predates all three branches, so this is pre-existing drift the Documentation Matrix rule does not require fixing here. |
| `B2-acoustic-read-06` | `tools/validate_extension_registry.py:546-570` | exp/acoustic-pressure | The new REGISTRY_LIST_ITEM_INVALID check catches a mapping parsed inside a notes list but misses the same failure one level up, a bare-mapping notes block. | Doctrine log C1-12 already logs this exact class as open with no rule requiring a sweep after a verified fix. |
| `B3-pressure-read-03` | `policy/profile-precision.yaml:184-187` | exp/acoustic-pressure | policy/profile-precision.yaml quantizes center_freq_hz on a 100 Hz grid with no modality gate, so an infrasound event's only M/L projection is 0.0 Hz, silently. | A standing 2026-07-08 maintainer ruling holds these precision-policy values as reference defaults pending field evidence, and normative text forbids the degraded export. |
| `F6-records-voice-10` | `8930fb8 (commit message trailer)` | exp/acoustic-pressure | 8930fb8's commit body carries a Co-Authored-By trailer naming Claude, though CLAUDE.md states commit attribution is human-only. | The commit body flags the conflict and defers to the maintainer's review pass, so it stands recorded, not decided. |
| `B1-wave-read-03` | `tools/validation_guidance.yaml:1784-1801` | wave/f1-field-evidence | At the wave tip, the acoustic-missing-required-features rule had no zmeta_version gate, so it asserted a 1.1.0 feature contract against locked v1.0 ACOUSTIC events. | The guidance file's header caps a wrong hint below conformance severity, and b0666d0 adds the lane gate before the three-branch merge lands. |
| `B1-wave-read-04` | `tools/validate.py:70` | wave/f1-field-evidence | load_guidance collapses each remediation to one unwrapped line averaging about 870 characters, printed under each FAIL, unlike the sibling tool's 74-column wrap. | No cited rule governs line length or wrapping, and a wrap fix would break the advisory-guarantee test's line-by-line comparison. |
| `F5-fixtures-02` | `tools/validate.py:148, 227, 233` | wave/f1-field-evidence | Three of the four emit_guidance() call sites, including the semantic FAIL branch carrying most governed codes, are unpinned and could be deleted with tests green. | emit_guidance is advisory output printed after the verdict, not a guard, so discipline 5's vacuous-pin rule does not require per-site coverage. |
| `F5-fixtures-04` | `tools/validation_guidance.yaml:1733` | wave/f1-field-evidence | Seven of fourteen structural guidance rules ship with no behavior fixture, and explain.py's actual CLI print path is exercised by no test at all. | F2-07 already adjudicated and recorded the identical gap, scoping the fixture remedy deliberately to rules a live failure touched, not all fourteen. |
| `F5-fixtures-05` | `tools/validate.py:57-73` | wave/f1-field-evidence | No fixture removes or corrupts the guidance file to prove validation degrades gracefully, though the fallback's actual verdict-neutral state is separately pinned. | The except branch is a fallback, not a guard, and the claim it produces is pinned; the trigger edge alone is untested. |
| `F6-records-voice-06` | `docs/zmeta_doctrine_review_log.md:2468` | wave/f1-field-evidence | F1-04 stays DECIDED though its implementing wave, the guidance system, landed in the same commit that wrote the entry, unlike F2-06 and F2-07. | The log's own precedent anchors wave-lands to a published release cut, blessing the status catching up afterward, and F2-06/F2-07 were never DECIDED. |
| `FC-05` | `spec/future-branch-roadmap.yaml:12` | wave/f1-field-evidence | spec/future-branch-roadmap.yaml's last_updated stamp sits a month stale after 7a01d35's 28-line roadmap edit, against the doc's own keep-current procedure. | The stale stamp predates the wave and is pre-existing published behavior; the merged develop tip corrects it once 8930fb8 lands. |

---

## Refuted

Raised by a lens and refuted on reproduction or on the doctrine check; kept so
the next reviewer does not re-derive them.

| Id | Claim | Why it did not hold |
|---|---|---|
| `F1-design-gates-04` | Two new risk-relevant acoustic entries assert preserve-under-projection with no dedicated pin, though a whole-object catalog rule and a default-deny omission check already enforce it. | The finding's grep used a trailing dot and missed the two whole-object payload.features catalog rules that already govern both dropped paths. |
| `B3-pressure-read-04` | The held level_statistic marker for spl_db is claimed unguarded on the schema arm, though the maintainer ruling closes only one specific leak route. | The roadmap's acoustic-level-carriers candidate books this exact gap and its tripwire, so it is a recorded, deferred item, not a new defect. |
| `F7-consumer-develop-06` | README, release/README, and CONFORMANCE.md still assert v1.1.25 identity though four manifest-listed artifacts no longer hash to what the manifest records. | The governance doc's branching section already rules this the expected pre-cut state on develop, and the claims-currency test that matters stays green. |
| `F2-governance-04` | Two new registry-validator checks landed as a Class B change with no doctrine-log entry and no recorded maintainer ruling for either one. | Class B's requirement list names no doctrine-log entry, and neither check put any guiding document under pressure, which is discipline 7's trigger. |
| `F2-governance-05` | The D1-01 launcher fix rides on the experimental vocabulary branch, so the finding claims shelving the experiment would revert a repaired v1.0 README path too. | Every added launcher line is additive and 1.1.0-only; reverting the branch restores the v1.0 path exactly, coupling nothing. |
| `F6-records-voice-03` | 8930fb8 deletes the 2026-09-10 worklog Last-updated stamp instead of appending above it, allegedly leaving that entry with no stamp of its own. | Replacing the single currency stamp is the file's established convention, used identically by four prior commits, so nothing here departs from practice. |
| `F7-consumer-develop-08` | The new advisory guidance corpus and the validator README tells consumers to run sit outside the hash-pinned release bundle, leaving advice unverifiable. | Advisory material is documented as excluded from the release bundle by design, and F1-04 rules guidance can never move a conformance verdict. |
| `F7-consumer-develop-09` | The launcher leaves an orphan gateway on port 5555 so a lane switch can silently not take effect, reproducing the D1-01 symptom. | The second bind fails with no SO_REUSEADDR, raising a visible error and exit code 1, so the lane switch never fails silently. |
| `B2-acoustic-read-04` | est_error_basis:UNRESOLVED is claimed sayable only beside the required numeric bound whose value it says is unresolved, an unlabelable-quantity problem. | A conventional bound labeled UNRESOLVED is more explicit than the same bound bare, and the record already states the pairing. |
| `B3-pressure-read-06` | A silent getattr fallback could turn the new reserved-leak check into a silent no-op if the validator's schema attribute ever disappeared. | A paired negative fixture ships and goes red when the fallback is simulated, so the failure surfaces loudly as a CI failure. |
| `F2-governance-06` | b0666d0 fails to name its dependency branch in its first commit, though the branch structure and the naming rule postdate that commit. | No dependent branch existed when b0666d0 was authored, and the maintainer's later commit records the stacking fact the rule requires. |
| `F2-governance-07` | All three registry mints went direct to experimental, with Class D ceremony claimed adjudicated for two entries and silent for TIMING_ERROR_BASIS. | A private Class D plan document rules the class for both markers before implementation, so the claimed silence on TIMING_ERROR_BASIS is wrong. |
| `F3-locked-kernel-04` | The ACOUSTIC arm change is a relaxation and a tightening, but the records book only the relaxation and pair-binding, never the tightening. | No compatibility promise applied since the newly-refused keys were never sanctioned vocabulary, and F2-08 books the class question for re-adjudication. |
| `F4-registry-roadmap-06` | The acoustic level-window rule and F2-08's decision attribute a window behavior to contract section 5.6, which the finding says is RF-only. | Section 5.6 states window carriers generally and grants future modality-specific window contracts, so the acoustic entry is the mechanism the contract authorizes. |
| `F5-fixtures-06` | An acoustic structural rule had no lane gate at the wave tip, briefly asserting a 1.1.0-only contract against locked v1.0 events. | F2-07 logs this exact defect verbatim, ruled a documentation bug, and the fix lands in the same merge set the finding reviews. |
| `F5-fixtures-07` | HANDLED_DETECT_KEYS is guarded in one direction only, so a key added but never implemented in matches() would stay green. | The pin asserts exactly the direction it claims and fails when violated; discipline 5 requires no guard against every unobserved failure mode. |
| `F6-records-voice-07` | Doctrine cycles F1 and F2 omit the per-cycle summary table that nine of the eleven prior cycles carry. | The cited protocol requires logging tensions with rationale, not a table format, and the count is all eleven prior cycles, not nine. |
| `F6-records-voice-08` | The worklog's claimed eight maintainer rulings cannot be reconciled with the six F1 doctrine-log entries the public record carries. | The worklog text never equates the headings with the rulings, and the commit body supplies rulings six through eight, reconciling the count. |
| `B1-wave-read-06` | explain.py lands with no test at the wave tip, leaving it uncovered until the later acoustic branch closes the gap. | The maintainer merges wave, acoustic, then pressure in order, so develop never holds the untested state, and b0666d0 pins the exact hazard. |
| `B1-wave-read-08` | The roadmap's promotion-blocker note says reserved replay records explicitly carry flags they inherit from a YAML defaults anchor. | The claim is true of the resolved registry every consumer reads, so only the adverb form is imprecise, not the substance. |
| `B2-acoustic-read-11` | The cross-reference between POWER_REFERENCE and the new acoustic entry runs one way only, with no back-link added to the sibling entry. | No cited rule requires a back-link, the acoustic entry never claims a second POWER_REFERENCE instance, and the AAR generalization is already booked. |
| `B3-pressure-read-07` | F2-08 overrides gates 1 and 6 on the record without formally evaluating the narrower mint that its own analysis points at. | Gate 1 is asked and answered on the record, gate 6 requires escalation only, and the narrower shapes are refused by name. |
| `FC-03` | Three experimental markers are minted gated on a second independent implementation, but nothing is written into the live-test checklist for it. | Discipline 10's checklist deferral applies only to an unobserved, undefended failure; this wave acted by maintainer adjudication on proven field evidence instead. |
| `FC-04` | The required-field relaxation is claimed never weighed against spec/versioning.md, the document said to state the rule it brushes. | docs/zmeta_change_governance.md states the identical rule and sources it from versioning.md, and F2-08 already adjudicates and dates the relaxation. |

---

## Provenance

Workflow `wf_08111400-530` in the maintainer's session of 2026-09-12; the
private record with the merge rehearsal transcript is
`local/merge_review_2026-09-12_three_branches.md` (gitignored). The report
page for the maintainer's review pass is linked from that record.
