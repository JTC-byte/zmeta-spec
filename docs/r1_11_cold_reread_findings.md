# R1-11 Cold Re-Read Findings — 2026-07-26

**Refresh-tier record (playbook cadence). Advisory / non-normative. Findings are
RECORDED, not fixed** — the resume-queue order stands: doctrine adjudication (P2)
remains the bottleneck, and no fix wave was opened by this pass.

## Method and scope

- Scope: the full held range `origin/main..7eaea97` (30 commits), weighted to the
  commits after `eb41794` (the range before it was already cold-audited by the
  fresh audit `02cb688`, whose findings are dispositioned).
- Method: nine independent cold readers — the six playbook wave surfaces
  (W1 kernel, W2 gateway runtime, W3 ingress, W4 egress, W5 release/tooling,
  W6 records/currency) plus three lenses aimed at this cycle's own documented
  failure modes (commit-message truth, vacuous pins, half-applied multi-layer
  fixes). Every candidate finding then faced adversarial refutation by a separate
  verifier that re-derived the evidence from the tree; candidate MAJORs faced a
  three-lens panel (reproduce / cause / scope+novelty) needing 2-of-3 to survive.
  78 agents total. Candidates already banked in `docs/r1_11_fix_pass_findings.md`,
  `docs/zmeta_doctrine_review_log.md`, or `docs/r1_11_full_stack_audit.md` were
  excluded by construction.
- Result: 48 candidates → 47 confirmed, 1 refuted, 0 already-banked duplicates.
  Readers converged on several defects from different angles; merging same-defect
  reports leaves the **30 distinct findings** below (multi-reader convergence is
  noted per entry — it is corroboration, not double-counting).
- Battery at the time of the read (verified live by four independent readers and
  by the session directly): kernel gate all flags exit 0, examples 51/51 strict,
  pytest 1200 passed + 1021 subtests. A green battery co-existing with every
  finding below is itself the point: none of this is visible to the gates.

## Summary — 3 MAJOR, 14 MODERATE, 10 MINOR, 3 OBSERVATION

| ID | Sev | Anchor | Finding |
|---|---|---|---|
| CR-01 | MAJOR | `adapters/ingress/sapient/sapient_to_zmeta.py:396` | SAPIENT: a negative declared maximum_latency NARROWS est_error_ms — the sign member of the R1-03/B-03 laundering class is open, and it falsifies the adapter's… |
| CR-02 | MAJOR | `adapters/egress/cot/zmeta_to_cot.py:307` | CoT egress projects the horizontal ellipse minor axis into point@le, a vertical-error field — fabricated vertical certainty on every ellipse-carrying event |
| CR-03 | MAJOR | `docs/r1_11_full_stack_audit.md:1810` | The 46 open findings are not re-derivable from the tree: three surfaces point to a register that cannot contain them, and the ~35 disposition-introduced defect… |
| CR-04 | MODERATE | `docs/zmeta_refinement_handoff.md:8` | Cycle-level 'no governed artifact touched / no reason_code minted' claims are false against the held range's own diffs |
| CR-05 | MODERATE | `adapters/ingress/mavlink/mavlink_to_zmeta_template.py:795` | MAVLink decoded LINK_STATUS branch: every event it emits is schema-invalid, its docstring's 'never accepted uninterpreted' claim is false on this branch, and t… |
| CR-06 | MODERATE | `adapters/ingress/mavlink/mavlink_to_zmeta_template.py:754` | MAVLink TASK_ACK: five of the nine advertised verdicts — the negative acks a commander most needs — always emit schema-invalid, because the mirrored vocabulary… |
| CR-07 | MODERATE | `docs/r1_11_fix_pass_findings.md:1462` | The fix-pass register still declares 'Round 2: open, undispositioned' after the disposition pass ran, and neither register carries per-finding open/closed mark… |
| CR-08 | MODERATE | `adapters/egress/mavlink/zmeta_command_to_mission_intent.py:137` | MAVLink mission-intent egress stamps priority=MED on commands that carried no priority — a fabricated tasking-priority claim reaching an autonomy consumer clean |
| CR-09 | MODERATE | `adapters/egress/sapient/zmeta_state_to_sapient_detection.py:294` | SAPIENT detection egress silently ignores a non-dict use_labels — a caller-supplied export prohibition passed as a list is dropped and the detection exports to… |
| CR-10 | MODERATE | `adapters/egress/sapient/zmeta_command_to_sapient_task.py:46` | SAPIENT task egress kept the recursive dict/list-only _contains_altitude — RecursionError past the documented ValueError/None contract, and blind to altitude k… |
| CR-11 | MODERATE | `adapters/egress/cot/zmeta_to_cot.py:371` | CoT precisionlocation stamps geopointsrc="GPS" altsrc="GPS" unconditionally — fabricated source-provenance labels on positions that may be RF-triangulated fusi… |
| CR-12 | MODERATE | `gateway/tests/test_release_signing.py:217` | New non-vacuity pin fails in the default shallow/tagless CI checkout — pushing the held range turns CI red |
| CR-13 | MODERATE | `CHANGELOG.md:7` | Three current-state record surfaces still freeze the cycle at 6ea9888 'pending a fresh audit' — falsified by ~15k lines of later code, and the CHANGELOG omits… |
| CR-14 | MODERATE | `docs/r1_11_full_stack_audit.md:1419` | Round-1 MAJOR count: the audit record says 8 in three places; the register itemizes and totals 10 |
| CR-15 | MODERATE | `docs/r1_11_full_stack_audit.md:1492` | 'Fourteen of the thirty-two are introduced-by-remediation' contradicts the 18 stated 40 lines earlier, the round table, and the register |
| CR-16 | MODERATE | `gateway/tests/test_external_state_promotion.py:193` | Arm 3 of the new trigger-polarity pin is vacuous — it passes identically on the reverted tree because the profile-H required-fields gate refuses first, never t… |
| CR-17 | MODERATE | `gateway/src/validators.py:1026` | c54215a commit message claims 'Seven allowlist sites' — the tree has six, at the commit and at HEAD |
| CR-18 | MINOR | `gateway/src/validators.py:540` | Decimal non-finite confidence is reported under the generic SCHEMA_INVALID, not NON_FINITE_CONFIDENCE — the confidence path loses its specific diagnostic exact… |
| CR-19 | MINOR | `adapters/ingress/sapient/registration_state.py:215` | RegistrationStore: duplicate mode_name declarations resolve last-wins instead of conflict-poisoning — order-dependent, and the broken-then-sane ordering erases… |
| CR-20 | MINOR | `docs/zmeta_doctrine_review_log.md:252` | Doctrine log entry R1-11-08 anchors zmeta_to_cot.py:235-237/268-270 — lines that match no committed tree in the held range; the code it names sits at 338-341/3… |
| CR-21 | MINOR | `adapters/egress/jreap/zmeta_state_to_jreap_track_json.py:123` | JREAP egress emits lat/lon as null for a present-but-partial geo, while its docstring and the held-range README refusal table say 'missing geo' is refused |
| CR-22 | MINOR | `release/sign_release_artifacts.py:27` | The A-23 checksum-rewrite guard's degraded-mode contract is false: a tagless/shallow checkout yields set(), not None, so it silently treats a published version… |
| CR-23 | MINOR | `docs/zmeta_refinement_handoff.md:5` | Handoff resume queue freezes '27 commits ahead' against the moving held range — stale in its own commit, and invisible to the new A-13 guard |
| CR-24 | MINOR | `docs/zmeta_after_action_log.md:35` | After-action log upgrades the six blockers to 'six MAJOR blockers'; the audit record grades one of them MODERATE |
| CR-25 | MINOR | `docs/r1_11_full_stack_audit.md:1046` | Fresh-audit record says '28 findings survived' but enumerates 30 (A-01..A-30), and no stated count reconciles the disposition's '91 findings' |
| CR-26 | MINOR | `docs/zmeta_audit_playbook.md:17` | Public playbook states the operational cost figure the AAR says is redacted to the private companion |
| CR-27 | MINOR | `docs/zmeta_doctrine_review_log.md:488` | The doctrine log carries the same tension twice as unlinked OPEN entries (R1-11-14 and R1-11-19), and the renumber pass that touched exactly this collision lef… |
| CR-28 | OBSERVATION | `gateway/src/gateway.py:1723` | _wire_safe_details residue-(2) justification 'not JSON-encodable at all, so a wrapper in details makes the encode fail loudly' is incomplete — cbor2.dumps enco… |
| CR-29 | OBSERVATION | `docs/zmeta_audit_playbook.md:8` | Playbook adoption is recorded without an adopter, 43 minutes after being declared pending the maintainer's sign-off |
| CR-30 | OBSERVATION | `docs/r1_11_closure_probe.py:1` | Positive assurance: the half-applied multi-layer hunt found no missing CODE layer — every claimed layer located and probed in the current tree |

---

### CR-01 (MAJOR) — SAPIENT: a negative declared maximum_latency NARROWS est_error_ms — the sign member of the R1-03/B-03 laundering class is open, and it falsifies the adapter's stated monotonicity property

**Anchor:** `adapters/ingress/sapient/sapient_to_zmeta.py:396` · **Commit:** c54215a · **Found by:** w3-ingress

**Claim under test:** The re-derived widen control flow claims the bound can only ever grow: sapient_to_zmeta.py:390-395 "falling back to the un-widened value would UNDERSTATE it — the one thing an uncertainty field must never do"; the MONOTONICITY block at :374-382 states "degrading a node can only ever WIDEN what it publishes"; README.md:209 says a broken declaration "can only ever widen the published est_error_ms, never tighten it"; and registration_state.py:88-98 says "a duration is never guessed". duration_ms guards units, numeric-ness and finiteness — never sign.

**Observed:** A registration declaring maximum_latency {value: -0.5, units: SECONDS} — a physically impossible capture-before-send bound, exactly the malformed-wire threat model the module states for itself — resolves as a real latency and is ADDED at :396, shrinking the caller's honest est_error_ms below its un-widened value. latency_unresolved never fires (the declaration resolved), sync_state stays LOCKED, the adapter's own validate() returns 'pass', and the event is schema-clean. With no caller timing at all, a declared -55 s eats 55 s off the module's own 60000 ms unknown-clock floor (60000 → 5000) while the label still says UNSYNCED. The banked R1-03 (MAJOR) and B-03 closed this identical laundering shape for NaN/overflow/unknown-units declarations; the negative member — the only remaining way a resolvable declaration can tighten the bound — was never swept (test_sapient_ingress.py's latency cases use only 0.5, NaN, and _BIG; no negative anywhere in the file) and is banked nowhere (no match in the fix-pass register, doctrine log, or audit record).

**Evidence:**

```
Probe through the repo's own test helpers, shipped schema+policy, caller timing {'time_source':'GPS_PPS','sync_state':'LOCKED','est_error_ms':5000.0}:
  +0.5s declared -> est_error_ms 5500.0  validate: pass
  -0.5s declared -> est_error_ms 4500.0  validate: pass   (narrower than the un-widened 5000)
  -4.0s declared -> est_error_ms 1000.0  validate: pass
  no caller timing, -55s declared -> {'time_source':'UNKNOWN','sync_state':'UNSYNCED','est_error_ms':5000.0} validate: pass (module's own conservative 60000 floor narrowed 12x); jsonschema Draft202012Validator errors: []
Code path: registration_state.py:112-125 returns any finite scaled value (`scaled = float(value) * factor ... if not math.isfinite(scaled): return None; return scaled` — no sign check), max_latency_ms :304-325 returns it, _timing :396 `timing["est_error_ms"] = float(timing["est_error_ms"]) + float(latency_ms)`.
```

**Reproduction:** `cd <repo> && python -c "import sys,importlib.util; sys.path.insert(0,'.'); import adapters.ingress.sapient.sapient_to_zmeta as s2z; spec=importlib.util.spec_from_file_location('t','adapters/ingress/sapient/test_sapient_ingress.py'); T=importlib.util.module_from_spec(spec); spec.loader.exec_module(T); tq={'time_source':'GPS_PPS','sync_state':'LOCKED','est_error_ms':5000.0}; ev=s2z.translate(T._detection_msg(), s2z.SCHEMA_ID, registration=T._store…`

**Verification panel:** CONFIRMED; CONFIRMED; CONFIRMED. CONFIRMED: Independently reproduced at HEAD 7eaea97 exactly as claimed: a registration declaring maximum_latency -0.5s yields est_error_ms 4500.0 (narrower than the un-widened 5000.0) with sync_state LOCKED and adapter validate() 'pass'; -4.0s yields 1000.0; with no caller timing, -55s narrows the module's own 60000 ms unknown-clock floor to 5000.0 while still labeled UNSYNCED. Code path verified from the tree: registration_state.py duration_ms (:112-125) checks units, numeric-ness, OverflowError, and finiteness but never sign, so a negative finite value resol…

### CR-02 (MAJOR) — CoT egress projects the horizontal ellipse minor axis into point@le, a vertical-error field — fabricated vertical certainty on every ellipse-carrying event

**Anchor:** `adapters/egress/cot/zmeta_to_cot.py:307` · **Commit:** pre-existing at origin/main (zmeta_to_cot.py:162); mapping row re-shipped unremarked in the held-range README rewrite and endorsed as 'already structured' by the fresh audit's gate-5 refutation (docs/r1_11_full_stack_audit.md:1258) · **Found by:** w4-egress

**Claim under test:** README.md:62 teaches '`semi_major` → `ce`, `semi_minor` → `le`' as the uncertainty mapping, and the adapter header sells CE/LE-from-error_ellipse as honest uncertainty projection. Contract §21.2 defines error_ellipse_m as a ground-plane ellipse ('orientation_deg is degrees true north'), i.e. both axes are horizontal.

**Observed:** Line 307: `le = error_ellipse.get("semi_minor", default_le)`. In CoT v2.0, point@ce is horizontal circular error and point@le is LINEAR error — the vertical/HAE uncertainty. The adapter therefore stamps the horizontal minor semi-axis as an explicit vertical-accuracy claim the event never made: the README's own example event (horizontal ellipse 150x80 m, no vertical error model anywhere in the schema) emits `<point ... hae="1500" le="80.0" ce="150.0" />` — TAK consumers read 'altitude known to ±80 m'. Gate 4 violated in the sharp direction: the projection gains certainty (a vertical bound) its source lacked, clean, unlabeled, unfilterable. The repo already adjudicated this exact move the other way: the SAPIENT egress loss note (zmeta_state_to_sapient_detection.py:90-94) drops the ellipse entirely because 'SAPIENT Location x/y/z_error are per-axis scalars and projecting an oriented ellipse onto them would misstate the error model' — CoT ce/le are per-axis scalars of the same kind. The honest le for an event with no vertical error model is the 9999999.0 unknown convention the adapter a…

**Evidence:**

```
zmeta_to_cot.py:306-307: `ce = error_ellipse.get("semi_major", default_ce)` / `le = error_ellipse.get("semi_minor", default_le)`. Live output from the README's own example event: `<point lat="43.49" lon="-112.04" hae="1500" le="80.0" ce="150.0" />`. schema/zmeta-event-1.1.0.schema.json $defs/error_ellipse: orientation_deg 'degrees from true north' (horizontal plane); $defs/geo carries no vertical-uncertainty field at all. spec/semantics-contract.md:2118-2119: 'semi_major and semi_minor are meters... orientation_deg is degrees true north.'
```

**Reproduction:** `cd repo; python -c "import sys; sys.path.insert(0,'adapters/egress/cot'); from zmeta_to_cot import zmeta_to_cot; ev={'event':{'event_type':'STATE_EVENT','event_subtype':'TRACK_STATE','ts':'2026-01-17T14:30:05Z'},'payload':{'track_id':'emitter-01','class':'a-h-G','geo':{'lat':43.49,'lon':-112.04,'alt_m':1500,'error_ellipse_m':{'semi_major':150.0,'semi_minor':80.0,'orientation_deg':45.0}},'valid_for_ms':60000}}; print(zmeta_to_cot(ev))" — observe…`

**Verification panel:** CONFIRMED; CONFIRMED; CONFIRMED. CONFIRMED: Independently reproduced at HEAD 7eaea97: zmeta_to_cot.py:306-307 maps the horizontal ellipse semi_minor into point@le, and the reader's repro emits le="80.0" for an event with no vertical error model. CoT 2.0 le is the linear (HAE/vertical) error while contract §21.2 and the v1.1.0 schema define error_ellipse_m as purely horizontal (orientation from true north; $defs/geo has no vertical-uncertainty field), so the projection fabricates a vertical-accuracy claim — gate 3/4 violated in the certainty-gaining direction. The repo's own SAPIENT egress pre…

### CR-03 (MAJOR) — The 46 open findings are not re-derivable from the tree: three surfaces point to a register that cannot contain them, and the ~35 disposition-introduced defects are recorded nowhere

**Anchor:** `docs/r1_11_full_stack_audit.md:1810` · **Commit:** 8955974 / c54215a / 35f603c · **Found by:** w6-records, x-committruth, x-halfapplied, x-pins (independent convergence)

**Claim under test:** Carried-forward item 2 (audit record :1810-1811): 'Forty-four further findings at MODERATE and below, in docs/r1_11_fix_pass_findings.md.' Handoff resume queue item 4 (:34) repeats it. The register's own header (:9-10) promises 'This file carries all of them, so a later reader can re-derive a disposition rather than take the summary on trust', and the AAR (zmeta_after_action_log.md:15-18) asserts 'every defect, reproduction and fix from a cycle is committed in that cycle's own records.'

**Observed:** docs/r1_11_fix_pass_findings.md was committed once (6adbf9f) and never updated. It contains exactly the 62 round-1/round-2 findings — at most 28 sub-MAJOR round-2 entries — and no round-3 entries. The disposition's own stop table says round 3's attack pass found 47 findings, 35 introduced by round 3's fixes; c54215a's message says '47 findings from the final adversarial pass remain open' (the record says 46 open — the two never reconcile). None of those round-3 findings is individually recorded anywhere in the tree (git grep 'R3-0' over HEAD *.md = zero hits), and the record's 'What is NOT recoverable' section says the run artifacts are gone. Worse, the register's live footer (:1462-1464) still says 'Round 2: open, undispositioned — the fix pass stopped here deliberately rather than opening a third round', which HEAD falsifies: a third round ran (c54215a) and round-2's four MAJORs B-01..B-04 are provably CLOSED (live probes this session). A maintainer working handoff item 4 finds 28 stale claims of unknown per-entry status, not the 44 open ones, and the ~35 introduced-by-round-3 def…

**Evidence:**

```
audit :1810-1811: 'Forty-four further findings at MODERATE and below, in `docs/r1_11_fix_pass_findings.md`'. register :1462-1464: 'Round 1: fully remediated. Round 2: **open, undispositioned** — the fix pass stopped here deliberately rather than opening a third round.' register disposition table :1454-1460: R2 = 4 MAJOR + 15 MODERATE + 6 MINOR + 7 OBSERVATION = at most 28 sub-MAJOR. audit :1771-1774 stop table row: '3 — disposition | 91 findings | 47 | 3 | 35 (74%)'. c54215a message: '47 findings from the final adversarial pass remain open, 35 of them introduced by this disposition' vs audit :1712 'Status: 91 findings dispositioned. 46 open, 2 MAJOR.' git log --oneline --all -- docs/r1_11_fix_pass_findings.md → single commit 6adbf9f. B-01..B-04 closure verified live (probes in coverage), contradicting the register's open-undispositioned status.
```

**Reproduction:** `cd repo; git log --oneline --all -- docs/r1_11_fix_pass_findings.md (one commit); grep -c '^### R' docs/r1_11_fix_pass_findings.md (62); sed -n 1452,1466p docs/r1_11_fix_pass_findings.md (footer denies round 3); git grep -n 'R3-0' HEAD -- '*.md' (empty); sed -n 1803,1815p docs/r1_11_full_stack_audit.md; git log -1 --format=%B c54215a | tail -3; then run the B-01..B-04 probes (e.g. python -c with zmeta_compact.dumps on {'s':{1,2}} → CompactUnrepr…`

**Verification panel:** CONFIRMED; CONFIRMED; CONFIRMED. CONFIRMED: Independently reproduced every load-bearing element at HEAD 7eaea97: (1) docs/r1_11_fix_pass_findings.md has exactly one commit (6adbf9f, predating disposition c54215a), 62 entries, at most 28 sub-MAJOR round-2 entries; (2) its live footer states round 2 is "open, undispositioned" and denies a third round, while c54215a IS a third round that adjudicated B-01..B-04 (B-01 allowlist verified in the c54215a diff and live in zmeta_compact.py); (3) audit :1810-1811 and handoff resume-queue item 4 both point the 44 open sub-MAJOR findings at that register,…

### CR-04 (MODERATE) — Cycle-level 'no governed artifact touched / no reason_code minted' claims are false against the held range's own diffs

**Anchor:** `docs/zmeta_refinement_handoff.md:8`, `docs/r1_11_full_stack_audit.md:1795`, `docs/zmeta_after_action_log.md:92` · **Commit:** 35f603c, b1e5b69, c54215a (claims); 74d92e1, c1eb9d0, 05ad9a8 (the governed diffs) · **Found by:** w1-kernel, w5-release, x-committruth, x-pins (independent convergence)

**Claim under test:** Handoff resume queue :8-9: "The R1-11 cycle is concluded and HELD: 27 commits ahead of origin/main ... No governed artifact was touched; no reason_code minted." Same claim on the standing public AAR (docs/zmeta_after_action_log.md:92-94: "No governed artifact — the locked semantics contract, the schemas, or the policy vocabulary — was modified anywhere in this cycle, and no diagnostic code was minted"), in the audit record (docs/r1_11_full_stack_audit.md:1795-1797 "untouched; no reason_code minted"), and in c54215a's commit message ("No governed artifact modified anywhere in this cycle. No reason_code minted.").

**Observed:** The held range the same sentences define as the cycle (handoff :65-66: "Held range 118f0b9..HEAD — the entire cycle") contains three commits that modified all five governed surfaces: 74d92e1 and c1eb9d0 minted three reason codes (ENCODING_UNSUPPORTED, BEARING_FRAME_UNLABELED, NON_FINITE_CONFIDENCE) into both schema enums, policy/violation-codes.yaml (with severities) and policy/semantics.yaml; 05ad9a8 added §5.3 wording to the LOCKED spec/semantics-contract.md. The same audit document records this at :679-688 ("The three diagnostic codes are the cycle's only vocabulary additions (Class B)") and fresh-audit finding A-29 (:1231-1235) analyses exactly these additions — so the record contradicts itself with the same word, "cycle". The additions were sanctioned Class B (disclosed in the wave commit messages), so the code is fine; the later cycle-summary records are what is false. The false version has already propagated (the session-memory summary of R1-11 states "no governed artifact touched"). Distinct from banked doctrine entry R1-11-13, which covers only the CHANGELOG sentence.

**Evidence:**

```
git log origin/main..HEAD -- spec/semantics-contract.md schema/zmeta-event-1.0.schema.json schema/zmeta-event-1.1.0.schema.json policy/semantics.yaml policy/violation-codes.yaml -> 05ad9a8, c1eb9d0, 74d92e1. git diff origin/main..HEAD -- policy/violation-codes.yaml -> "+ - code: BEARING_FRAME_UNLABELED / severity: warn / + - code: NON_FINITE_CONFIDENCE / severity: fail / + - code: ENCODING_UNSUPPORTED / severity: fail". 74d92e1 message: "Sanctioned Class B diagnostic vocabulary addition ... ENCODING_UNSUPPORTED in both schema reason_code enums, policy/violation-codes.yaml (fail)". vs handoff :8-9, AAR :92-94, audit doc :1795-1797 quoted above.
```

**Reproduction:** `cd repo; git diff origin/main..HEAD -- policy/violation-codes.yaml spec/semantics-contract.md; then read docs/zmeta_refinement_handoff.md:5-9 and docs/zmeta_after_action_log.md:90-98.`

### CR-05 (MODERATE) — MAVLink decoded LINK_STATUS branch: every event it emits is schema-invalid, its docstring's 'never accepted uninterpreted' claim is false on this branch, and the tree twice says the defect is 'recorded separately' when no surviving record contains it

**Anchor:** `adapters/ingress/mavlink/mavlink_to_zmeta_template.py:795` · **Commit:** c54215a · **Found by:** w3-ingress

**Claim under test:** Three claims. (1) Module header :5 maps "SYS_STATUS / BATTERY_STATUS -> SYSTEM_EVENT (LINK_STATUS)" through mavlink_decoded_to_zmeta_system_events. (2) That function's docstring :683-684: "payload.state is never invented on any of the three branches, and it is never accepted uninterpreted either." (3) test_mavlink_ingress.py:1157-1158 says of this branch's schema-shape defect: "it is recorded separately and is out of this class's scope", and docs/r1_11_fix_pass_findings.md:1028 calls it "the separately-recorded shape defect".

**Observed:** (1) The branch emits metrics carrying only the optional rssi/snr/drop_rate keys — never the link_id/latency_ms/packet_loss_pct/throughput_bps the v1.0 schema REQUIRES on LINK_STATUS (schema :1442-1462), and with no metric keys at all it omits `metrics` entirely, which the schema also requires — so 100% of this documented emitter path's output is refused at the gateway. Fail-closed, not laundering, but a whole advertised message family goes dark. (2) `state = msg.get("state") or msg.get("link_state") or "UNKNOWN"` (:795) forwards any truthy carried string verbatim — probe shows payload.state = 'HEALTHY' emitted — with no _normalize_vocabulary_token call, unlike the TASK_ACK and TIME_STATUS branches four lines up; only the gateway's schema enum catches it. The docstring claim is false for this branch. (3) The 'separate record' does not exist: grep for link_id/shape-defect across docs/r1_11_fix_pass_findings.md (62 findings), docs/r1_11_full_stack_audit.md, and docs/zmeta_doctrine_review_log.md finds only the two POINTERS, no entry — it lived in the session-scoped round-2 run artifacts…

**Evidence:**

```
Probe (shipped schema, Draft202012Validator):
  mavlink_decoded_to_zmeta_system_events({'msg_type':'RADIO_STATUS','rssi':200,'snr':20,'drop_rate':0.1,'state':'UP'}, ...) -> payload {'system_type':'LINK_STATUS','state':'UP','metrics':{'rssi':200,'snr':20,'drop_rate':0.1}}; errors ["'link_id' is a required property", "'latency_ms' is a required property", "'packet_loss_pct' is a required property", "'throughput_bps' is a required property"]
  {'msg_type':'RADIO_STATUS','state':'HEALTHY'} -> payload.state 'HEALTHY' (accepted uninterpreted)
  {'msg_type':'RADIO_STATUS'} -> no metrics key; errors ["'metrics' is a required property"]
The only test touching this branch (test_mavlink_ingress.py:1154-1170) deliberately skips VALIDATOR.validate — every other emitter in the file is schema-validated — and the suite is green (228 passed).
```

**Reproduction:** `cd <repo> && python -c "import sys,json; sys.path.insert(0,'.'); from adapters.ingress.mavlink.mavlink_to_zmeta_template import mavlink_decoded_to_zmeta_system_events as f; import jsonschema; s=json.load(open('schema/zmeta-event-1.0.schema.json',encoding='utf-8')); v=jsonschema.Draft202012Validator(s); ev=f({'msg_type':'RADIO_STATUS','rssi':200,'state':'HEALTHY'}, platform_id='u1', producer='mavlink', ts='2025-01-17T15:20:00Z')[0]; print(ev['pay…`

### CR-06 (MODERATE) — MAVLink TASK_ACK: five of the nine advertised verdicts — the negative acks a commander most needs — always emit schema-invalid, because the mirrored vocabulary omitted the conditional reason_code requirement attached to it, and a message-carried reason_code is silently dropped

**Anchor:** `adapters/ingress/mavlink/mavlink_to_zmeta_template.py:754` · **Commit:** c54215a · **Found by:** w3-ingress

**Claim under test:** The mirror comment :49-53 presents _TASK_ACK_STATES as "The v1.0 schema's TASK_ACK state vocabulary, mirrored the same way" with drift being "a schema-refusal at the gateway, never a silent pass"; the function docstring :686-691 says the verdict need only be "message-carried *and* be a member of the v1.0 TASK_ACK vocabulary"; and the test file's own stated principle (:1311-1312) is that unusable acks are "refused at ingress rather than emitted as a schema-invalid event for the gateway to reject".

**Observed:** The schema's TASK_ACK conditional (zmeta-event-1.0.schema.json:1707-1737) requires metrics.reason_code for REJECTED/FAILED/CANCELLED/EXPIRED/DUPLICATE_IGNORED; the template's metrics literal (:754-757) carries only task_id and original_event_id and ignores a msg-carried reason_code entirely — even one that is a legal member of the schema's 12-value TASK_ACK reason_code enum. So every vocabulary-valid negative verdict yields a gateway-refused event (fail-closed: the commander sees a SCHEMA_VIOLATION diagnostic, never the REJECTED ack), and the carried reason_code is silently dropped — the exact silent-drop the refusal paths in this same function were rebuilt to avoid (R2-10). The mirror imported the enum but not the conditional obligation attached to it. The sibling SAPIENT adapter in this same held range implements the conditional correctly: _TASK_ACK_STATE at sapient_to_zmeta.py:102-108 pairs each negative state with its required reason_code ('REJECTED'->'TASK_REJECTED', 'FAILED'->'TASK_FAILED') and writes it at :1318-1322. The pin at test_mavlink_ingress.py:1317-1331 asserts all n…

**Evidence:**

```
Probe (shipped schema): msg {'task_id':'t1','original_event_id':'019c3ef3-...','ack':'REJECTED','reason_code':'SCHEMA_INVALID'} -> payload {'system_type':'TASK_ACK','state':'REJECTED','metrics':{'task_id':'t1','original_event_id':'019c3ef3-...'}}; schema errors ["'reason_code' is a required property"]. Same msg with 'ack':'ACCEPTED' -> errors []. Template :754-757: `metrics = {"task_id": task_id, "original_event_id": original_event_id,}` — no reason_code read anywhere in the branch.
```

**Reproduction:** `cd <repo> && python -c "import sys,json; sys.path.insert(0,'.'); from adapters.ingress.mavlink.mavlink_to_zmeta_template import mavlink_decoded_to_zmeta_system_events as f; import jsonschema; s=json.load(open('schema/zmeta-event-1.0.schema.json',encoding='utf-8')); v=jsonschema.Draft202012Validator(s); ev=f({'task_id':'t1','original_event_id':'019c3ef3-0000-7000-8000-000000000001','ack':'REJECTED','reason_code':'SCHEMA_INVALID'}, platform_id='u1…`

### CR-07 (MODERATE) — The fix-pass register still declares 'Round 2: open, undispositioned' after the disposition pass ran, and neither register carries per-finding open/closed markers — the '44 open sub-MAJOR' set cannot be re-derived from the tree

**Anchor:** `docs/r1_11_fix_pass_findings.md:1462` · **Commit:** 6adbf9f · **Found by:** w3-ingress, w6-records (independent convergence)

**Claim under test:** The register's stated purpose (:7-10) is that "a later reader can re-derive a disposition rather than take the summary on trust", and its Disposition section (:1462-1464) states "Round 1: fully remediated. Round 2: open, undispositioned — the fix pass stopped here deliberately rather than opening a third round." The audit record (docs/r1_11_full_stack_audit.md:1712, :1810-1811) states "91 findings dispositioned. 46 open, 2 MAJOR" and points the maintainer at "Forty-four further findings at MODERATE and below, in docs/r1_11_fix_pass_findings.md".

**Observed:** Cross-wave records observation surfaced by this wave's mandatory dedupe (the adapter code is my surface; this is where its dedupe ground truth lives). git log shows the register was written by 6adbf9f and never touched again — c54215a's disposition pass ("Ten groups, 91 findings handled across both registers") updated the audit record but not the register, so the register's 'Round 2: open, undispositioned' is now false on the tree: R2-01, R2-08, R2-09, R2-10, R2-20 and R2-21 are demonstrably FIXED in the current mavlink template (each now has a named pin in test_mavlink_ingress.py:1191+), while others (e.g. R2-11, R2-12) remain open by design. No per-finding disposition marker exists in either register or anywhere else (grep for R2-20/R2-09/R2-10 across the repo hits only the original headings and test comments), so the audit record's pointer does not resolve: a reader cannot determine WHICH 44 findings are the open ones without re-probing all 62+29 individually — the exact take-the-summary-on-trust failure the register was created to prevent, and the same record-accuracy class as t…

**Evidence:**

```
git log --oneline -- docs/r1_11_fix_pass_findings.md -> only '6adbf9f R1-11: persist the full fix-pass finding register'. Register :1462-1464 quoted above. Current tree: mavlink_to_zmeta_template.py :80 (_TIME_STATUS_STATE_SEVERITY, closes R2-01), :715-719 (carrier-key presence test, closes R2-10), :875-897 (reason_code vocabulary + UP-contradiction refusal, closes R2-20), :788 (_uint8_measurement_or_none on msg rssi, closes R2-09) — all live while the register calls round 2 wholesale 'open, undispositioned'.
```

**Reproduction:** `git -C <repo> log --oneline origin/main..HEAD -- docs/r1_11_fix_pass_findings.md; then compare docs/r1_11_fix_pass_findings.md:1452-1464 against docs/r1_11_full_stack_audit.md:1710-1712 and :1805-1811; grep -n 'R2-20' -r <repo> to confirm no disposition marker exists`

### CR-08 (MODERATE) — MAVLink mission-intent egress stamps priority=MED on commands that carried no priority — a fabricated tasking-priority claim reaching an autonomy consumer clean

**Anchor:** `adapters/egress/mavlink/zmeta_command_to_mission_intent.py:137` · **Commit:** pre-existing at origin/main:68; held range added the 166-line test file (which never pins or flags priority) and rewrote the README, whose example depicts the fabrication unremarked (input has no priority, output shows "priority":"MED") · **Found by:** w4-egress

**Claim under test:** schema (both 1.0 and 1.1.0): CommandPayload.priority is OPTIONAL (`priority?: LOW | MED | HIGH`, contract line 1176) with no declared default — an omitted priority is the absence of a priority claim. The doctrine log's own fabricate-a-sentinel pattern note (R1-11-07/R1-11-08/A-06) states the class rule: an unstated quantity should be omitted, not reported as a value.

**Observed:** Line 137: `"priority": payload.get("priority") or "MED"` — every command without a priority is projected with an explicit priority: MED, which a downstream deconfliction/scheduling node can rank against genuinely-claimed LOW/HIGH commands. The sibling SAPIENT task adapter written to the same contract makes the opposite, honest choice and says why (zmeta_command_to_sapient_task.py:21-23: 'payload.priority is dropped everywhere'). This is a direct hit on the wave question ('does any egress path stamp a default the source event did not carry') and a member of the fabricate-a-sentinel family the doctrine log tracks — but it appears in no register: grep for 'priority' across r1_11_full_stack_audit.md, r1_11_fix_pass_findings.md and zmeta_doctrine_review_log.md returns zero hits, so the pattern note's enumeration of the class is short by one member.

**Evidence:**

```
Live: input {'task_id':'task-1','task_type':'GOTO','valid_for_ms':60000,'requires_deconfliction':True,'target_geo':{'lat':34.0,'lon':-118.0}} (no priority) -> {'task_id': 'task-1', 'task_type': 'GOTO', 'valid_for_ms': 60000, 'priority': 'MED', 'requires_deconfliction': True, 'target_lat': 34.0, 'target_lon': -118.0}. README.md:37/43 shows the same pair (priority-less input, MED output) with no caveat. grep -n priority adapters/egress/mavlink/test_mavlink_intent.py -> no matches.
```

**Reproduction:** `cd repo; python -c "from adapters.egress.mavlink.zmeta_command_to_mission_intent import zmeta_command_to_mission_intent as mi; print(mi({'event':{'event_type':'COMMAND_EVENT'},'payload':{'task_id':'t','task_type':'GOTO','valid_for_ms':1,'requires_deconfliction':True}}))"`

### CR-09 (MODERATE) — SAPIENT detection egress silently ignores a non-dict use_labels — a caller-supplied export prohibition passed as a list is dropped and the detection exports to the coalition feed clean, no refusal, no self-label

**Anchor:** `adapters/egress/sapient/zmeta_state_to_sapient_detection.py:294` · **Commit:** pre-existing at origin/main:225, unchanged in held range; the held-range README addition (line ~100) restates the guarantee ('this egress is never more permissive than the operator's own filter') · **Found by:** w4-egress

**Claim under test:** The module's own doctrine, stated twice in this range: unknown/unadjudicable restriction inputs fail CLOSED — lines 300-304 refuse any risk record whose policy_decision is outside the governed vocabulary ('never export an unadjudicable record clean'), and the held-range README bullet promises the caller's use_labels prohibitions are honored.

**Observed:** Line 294: `caller_records = [use_labels] if isinstance(use_labels, dict) else []` — any non-dict use_labels (the natural mistake is a LIST of label dicts, since event-carried risk_adjudication records are a list) is silently treated as NO restriction. The restriction is neither adjudicated nor refused nor carried as a zmeta.risk self-label; the detection exports clean. That is the fail-open polarity on the one parameter whose whole purpose is restricting the coalition export path, in a function every other arm of which fails closed (unknown decisions refuse, unserializable labels refuse the event, partial geo refuses). test_sapient_egress.py covers dict-shaped use_labels only (lines 345, 438, 752). Not banked: 'use_labels' appears in no register or doctrine entry.

**Evidence:**

```
Live probe: use_labels={'prohibited_uses':['COALITION_EXPORT']} -> None (refused, correct); use_labels=[{'prohibited_uses':['COALITION_EXPORT']}] -> full SapientMessage returned, detection_report carries NO object_info at all — the prohibition vanished without trace.
```

**Reproduction:** `cd repo; python -c "from adapters.egress.sapient.zmeta_state_to_sapient_detection import zmeta_state_to_sapient_detection as det; ev={'event':{'event_type':'STATE_EVENT','event_subtype':'TRACK_STATE','ts':'2026-07-01T00:00:00Z'},'payload':{'track_id':'01HZZZZZZZZZZZZZZZZZZZZZZZ','geo':{'lat':1.0,'lon':2.0,'alt_m':3.0}}}; print(det(ev, node_id='n', use_labels=[{'prohibited_uses':['COALITION_EXPORT']}]))" — returns an exported message instead of N…`

### CR-10 (MODERATE) — SAPIENT task egress kept the recursive dict/list-only _contains_altitude — RecursionError past the documented ValueError/None contract, and blind to altitude keys in non-dict/list containers — while the held range upgraded its MAVLink sibling for exactly these two defects and hardened the surrounding lines of this same file

**Anchor:** `adapters/egress/sapient/zmeta_command_to_sapient_task.py:46` · **Commit:** c54215a edited this file (added _parse_utc TypeError arm, _is_finite_number, the OSError guard) and left _contains_altitude in the pre-range shape; the MAVLink sibling's comment (zmeta_command_to_mission_intent.py:66-72) names the defect being carried here: 'the recursive dict/list version raised RecursionError on deep geometry (a crash where the documented signal is None/ValueError) and never looked inside a Mapping that is not a dict, a tuple, a set or a CBOR tag wrapper' · **Found by:** w4-egress

**Claim under test:** Docstring lines 119-121: the ONLY raise is ValueError for an altitude-carrying target_geo; line 201-202 comment repeats 'the altitude tripwire above remains the only deliberate raise in this projection'. The guard's stated purpose (lines 31-39) is contract-7.8 defence in depth kept 'in sync' with the gateway validator's coverage.

**Observed:** Lines 46-60 are a plain recursion over dict/list only. Two consequences, both demonstrated: (1) a deeply nested target_geo raises RecursionError out of the public entry point — a third exception class the documented contract does not name, the identical guard-shape defect this cycle recorded twice (A-04, A-10) and fixed twice; (2) an altitude key carried inside a tuple/set/non-dict Mapping is invisible to the tripwire, so the command projects without the deliberate loud refusal (nothing leaks to the wire — the Location is built field-by-field — so this half is a silent-tripwire-miss, not a laundering). Neither shape is gate-clean (target_geo is strict geo2d), so exposure is embedders, same population as the banked A-10. Not banked: R2-07 enumerated only the explicit-stack _has_non_finite walkers (jreap/klv/mavlink/sapient-ingress), all now fixed; this recursive guard was not in its list and appears in no register (only mention of this file is V2-06, about non-string ts).

**Evidence:**

```
Live: GOTO command with target_geo nested 100k deep -> 'SAPIENT task deep target_geo RAISED: RecursionError'. _contains_altitude({'lat':1.0,'lon':2.0,'meta':({'alt_m':500},)}) -> False, while the MAVLink sibling's guard on the identical value -> True.
```

**Reproduction:** `cd repo; python -c "from adapters.egress.sapient.zmeta_command_to_sapient_task import _contains_altitude; print(_contains_altitude({'meta': ({'alt_m': 500},)}))" -> False; deep-nesting probe: build d['nest']=... 100000 deep inside target_geo and call zmeta_command_to_sapient_task -> RecursionError`

### CR-11 (MODERATE) — CoT precisionlocation stamps geopointsrc="GPS" altsrc="GPS" unconditionally — fabricated source-provenance labels on positions that may be RF-triangulated fusion products

**Anchor:** `adapters/egress/cot/zmeta_to_cot.py:371` · **Commit:** pre-existing at origin/main; unchanged in held range; undocumented — no README/mapping-table row and no register entry mentions geopointsrc/altsrc (grep across docs/ and adapters/egress/cot/README.md: zero hits outside SVG art) · **Found by:** w4-egress

**Claim under test:** Gate 3: provenance stays explicit and honest; gate 4: a projection never gains certainty (here, a provenance pedigree) its source lacked. The adapter's own header (lines 7-10) and README lean on 'never an invented accuracy figure' as the design position for this exact element's siblings (ce/le).

**Observed:** Lines 370-374 hard-code `geopointsrc="GPS" altsrc="GPS"` into every precisionlocation element whenever an error ellipse is present. ZMeta events carry no field asserting the position was GPS-derived; the repo's flagship use case (docs/img/b5-triangulation, the kraken LOB-fusion pipeline) produces exactly the ellipse-carrying tracks this branch fires on, and their positions are triangulated estimates, not GPS fixes. TAK consumers surface geopointsrc as the position-source pedigree, so a fused RF estimate arrives wearing a GPS provenance badge — laundered pedigree in a structured, machine-read attribute. The README example output (producer 'fusion-engine') demonstrates it directly.

**Evidence:**

```
Live output for the README's fusion-engine example event: `<precisionlocation geopointsrc="GPS" altsrc="GPS" ellipse_major="150.0" ellipse_minor="80.0" ellipse_angle="45.0" />`. No ZMeta input field feeds either attribute — grep geopointsrc adapters/egress/cot/zmeta_to_cot.py shows the literal only.
```

**Reproduction:** `Same reproduction command as the ce/le finding; observe the precisionlocation line`

### CR-12 (MODERATE) — New non-vacuity pin fails in the default shallow/tagless CI checkout — pushing the held range turns CI red

**Anchor:** `gateway/tests/test_release_signing.py:217` · **Commit:** c54215a · **Found by:** w5-release

**Claim under test:** The pin `test_published_release_tags_sees_this_repository_tags` (added with the A-23 guard) intends `assert tags is None or "v1.1.16" in tags` to tolerate degraded checkouts, modelling them as None; the sibling test's own docstring (gateway/tests/test_published_checksums_immutable.py:9-12) documents CI as 'a shallow or tagless checkout (e.g. default CI fetch-depth 1)' and handles it gracefully.

**Observed:** In a tagless checkout `git tag -l v*` succeeds with empty output, so `_published_release_tags()` returns `set()`, not None — the assertion fails with `AssertionError: set()`. `.github/workflows/ci.yml:15` uses `actions/checkout@v6` with default settings (shallow, --no-tags) and `:113` runs `python -m pytest -q gateway/tests adapters`, which includes this test. The local battery is green only because the maintainer's clone has all 23 tags; the first push of the held range fails CI. No record mentions this; the closeout claims battery green without the CI caveat.

**Evidence:**

```
Tagless clone of HEAD: `tags: 0`, then pytest: `>       assert tags is None or "v1.1.16" in tags, tags  /  E       AssertionError: set()  /  FAILED gateway/tests/test_release_signing.py::test_published_release_tags_sees_this_repository_tags` — 1 failed, 18 deselected.
```

**Reproduction:** `git clone --no-tags --single-branch "file:///C:/Users/User/Desktop/General/Requirements Documents/Future Ideas/Z-ISR/ZMeta/zmeta-spec" /tmp/ci-sim && cd /tmp/ci-sim && python -m pytest -q gateway/tests/test_release_signing.py -k published_release_tags_sees`

### CR-13 (MODERATE) — Three current-state record surfaces still freeze the cycle at 6ea9888 'pending a fresh audit' — falsified by ~15k lines of later code, and the CHANGELOG omits the six-blocker fixes entirely

**Anchor:** `CHANGELOG.md:7`, `docs/zmeta_refinement_handoff.md:67` · **Commit:** 1c78a85 / c54215a · **Found by:** w6-records, x-halfapplied (independent convergence)

**Claim under test:** CHANGELOG [Unreleased] HOLD block (:5-8): 'The R1-11 cycle below is complete and frozen pending a fresh full-stack audit... last code commit 6ea9888.' Worklog Current Resume Note (:7-11): same, plus 'anything after it is records only.' Handoff body (:64-71): same text plus 'NEXT: the fresh audit.'

**Observed:** The fresh audit ran (02cb688), then two major CODE commits landed: 1c78a85 (30 files, +8054/−268 — the six blocker fixes incl. the kernel-wide non-finite value gate) and c54215a (60 files, +7176/−436 — B-01..B-04, the compact allowlist rewrite that changes wire refusal behavior). ~19.4k of the range's +24,355 inserted lines postdate the fresh audit's anchor (origin/main..eb41794 = +4920). Both c54215a and 7eaea97 edited these very files (c54215a touched CHANGELOG and the worklog resume note; 7eaea97 edited the handoff) yet left the frozen-at-6ea9888 claims in place — the half-applied record-update shape the interruption ledger warns about, applied to records instead of code. Consequence beyond staleness: the CHANGELOG [Unreleased] section carries only three bullets (original audit + waves, V-pass 1, V-pass 2) and NO entry for the fresh audit, the six-blocker fix pass, or the disposition; the recorded cut procedure (audit :1386 'Convert the CHANGELOG [Unreleased] HOLD block to a 1.1.17 heading') would ship release notes omitting the cycle's most safety-relevant fixes. The handoff is…

**Evidence:**

```
CHANGELOG.md:5-8: '> **HOLD (2026-07-22).** The R1-11 cycle below is complete and frozen / > pending a fresh full-stack audit... (`118f0b9`..`HEAD`, last code commit `6ea9888`)'. docs/zmeta_refinement_worklog.md:10: 'last code commit `6ea9888`, anything after it is records only'. docs/zmeta_refinement_handoff.md:64-70: 'COMPLETE and FROZEN pending a fresh full-stack audit... NEXT: the fresh audit'. git show --shortstat 1c78a85 → 30 files, +8054/−268; c54215a → 60 files, +7176/−436. awk over CHANGELOG [Unreleased] top-level bullets → exactly 3 (audit, pass 1, pass 2); grep 'fresh audit|blockers|02cb688|1c78a85' in CHANGELOG → only the stale HOLD header. Post-eb41794 commits touching CHANGELOG: only c54215a, and its hunk is a one-sentence R1-11-13 rescope.
```

**Reproduction:** `grep -n 'last code commit' CHANGELOG.md docs/zmeta_refinement_worklog.md; grep -n 'COMPLETE and FROZEN|NEXT: the fresh' docs/zmeta_refinement_handoff.md; git show --shortstat --format= 1c78a85 c54215a; git diff --shortstat origin/main..eb41794 vs origin/main..HEAD; awk '/^## \[Unreleased\]/{f=1} /^## \[1\.1\.16\]/{f=0} f && /^- /' CHANGELOG.md`

### CR-14 (MODERATE) — Round-1 MAJOR count: the audit record says 8 in three places; the register itemizes and totals 10

**Anchor:** `docs/r1_11_full_stack_audit.md:1419`, `docs/r1_11_full_stack_audit.md:1773` · **Commit:** a3c4c51 · **Found by:** w6-records, x-committruth (independent convergence)

**Claim under test:** Audit record :1419 'returned **30 residual findings, 8 MAJOR**'; :1466 'Round 1: 6 fixes gave 30 residuals / 8 MAJOR'; :1773 round table '| 1 — fix waves | 6 blockers | 30 | 8 | 2 fixes laundered |' (repeated by 8955974).

**Observed:** docs/r1_11_fix_pass_findings.md itemizes ten round-1 MAJOR findings — R1-01 through R1-10 all carry '(MAJOR)' in their headings — and its own disposition table (:1456) records '| MAJOR | 10 | 4 |'. The two records disagree today. No reading reconciles them: if the table's MAJOR column excluded the round's own introduced findings ('2 fixes laundered'), the round-2 row would have to say 1, not 4 (3 of round 2's 4 MAJOR are marked INTRODUCED). One of the two documents understates or overstates the round-1 MAJOR mass by 2 — on the exact quantity ('severity is converging') the stop-at-three-rounds argument rests on.

**Evidence:**

```
grep -n '^### R1-' docs/r1_11_fix_pass_findings.md -> R1-01..R1-10 all '(MAJOR)', R1-11..21 MODERATE, R1-22..25 MINOR, R1-26..30 OBSERVATION; docs/r1_11_fix_pass_findings.md:1456 '| MAJOR | 10 | 4 |'; docs/r1_11_full_stack_audit.md:1419, :1466, :1773 quoted; git log -S '30 residual findings, 8 MAJOR' -> a3c4c51 sole source, never corrected.
```

**Reproduction:** `grep -n '^### R1-' docs/r1_11_fix_pass_findings.md | sed 's/ —.*//'; sed -n '1454,1460p' docs/r1_11_fix_pass_findings.md; grep -n '8 MAJOR' docs/r1_11_full_stack_audit.md.`

### CR-15 (MODERATE) — 'Fourteen of the thirty-two are introduced-by-remediation' contradicts the 18 stated 40 lines earlier, the round table, and the register

**Anchor:** `docs/r1_11_full_stack_audit.md:1492` · **Commit:** a3c4c51 · **Found by:** w6-records, x-committruth (independent convergence)

**Claim under test:** :1491-1493: 'Twenty-eight further findings at MODERATE and below are recorded in the run artifacts. **Fourteen of the thirty-two are introduced-by-remediation**, which is the number that should drive the next decision.'

**Observed:** The same section says at :1451-1452 'the final read-only pass returned **32 findings, 4 MAJOR, of which 18 were introduced by the remediation itself**'; the disposition table :1774 says '18 (56%)'; the register (:810-811) says '32 findings, **18 of them introduced**... That ratio is the number that should drive the next decision' and carries exactly 18 entries marked 'INTRODUCED BY REMEDIATION' (3 MAJOR + 9 MODERATE + 4 MINOR + 2 OBSERVATION). No reading yields 14: total introduced is 18, and introduced-at-sub-MAJOR is 15. The wrong figure sits on the sentence that explicitly names itself the decision driver, and it was never corrected by f610751-class count sweeps (which predate a3c4c51) or any later commit.

**Evidence:**

```
grep -c 'INTRODUCED BY REMEDIATION' docs/r1_11_fix_pass_findings.md -> 18; docs/r1_11_full_stack_audit.md:1451, :1492, :1774 quoted; docs/r1_11_fix_pass_findings.md:810-811 quoted; git log -S 'Fourteen of the thirty-two' -> a3c4c51, no later correction.
```

**Reproduction:** `grep -n 'Fourteen of the thirty-two\|18 were introduced\|18 of them introduced\|18 (56%)' docs/r1_11_full_stack_audit.md docs/r1_11_fix_pass_findings.md; grep -c 'INTRODUCED BY REMEDIATION' docs/r1_11_fix_pass_findings.md.`

### CR-16 (MODERATE) — Arm 3 of the new trigger-polarity pin is vacuous — it passes identically on the reverted tree because the profile-H required-fields gate refuses first, never the source-identity trigger it names

**Anchor:** `gateway/tests/test_external_state_promotion.py:193` · **Commit:** c54215a · **Found by:** x-pins

**Claim under test:** test_unhashable_risk_tokens_trip_their_trigger_instead_of_being_admitted's docstring says 'Asserting only ok is False is ... vacuous: it passes on the reverted tree. Both arms below assert the specific refusal', and its arm 3 (:193-202) is labeled 'the source-identity trigger, same polarity bug'. The disposition record (r1_11_full_stack_audit.md:1764-1767) says the initially-vacuous pin 'was rewritten to assert the specific refusal', and c54215a's message says 'Both halves are now pinned ... three trigger sites, all enumerated.'

**Observed:** Arm 3's input (lineage_status=["EXTERNAL_SOURCE"], source_event_uid="", profile H) never reaches the source-identity trigger at validators.py:1456. On the FIXED tree it is refused by the required-fields presence check at validators.py:1400 (message 'external STATE_EVENT promotion metadata missing required fields' — profile H requires source_event_uid, and "" is blank), which already yields missing=['source_event_uid']. Reverting the trigger to the pre-fix fail-open polarity (TypeError -> False) changes nothing for this input: same gate, same message, same details, so both of arm 3's assertions (assertFalse(ok) + 'source_event_uid' in details['missing']) still pass — the exact 'a DIFFERENT gate refused' shape standing discipline 5 names. The delta the pin cannot see: in a no-constraint deployment (empty lineage allowlist, source_event_uid not in the profile's required_fields — the same legal-deployment shape arm 2 uses for the loop trigger), the reverted tree ADMITS the unhashable lineage_status clean while the fixed tree refuses via the :1456 trigger ('requires source event identity…

**Evidence:**

```
Live probe (scratchpad, repo untouched), shipped validators loaded, _risk_trigger_matches monkeypatched to the pre-fix TypeError->False body: FIXED tree arm3 input -> ok=False msg='external STATE_EVENT promotion metadata missing required fields' missing=['source_event_uid']; REVERTED tree arm3 input -> identical output; arm 3's assertions STILL PASS. No-constraint config (allowed_lineage_status_by_profile.H=[], source_event_uid/freshness_ms removed from required_fields H), same unhashable lineage_status: reverted tree -> ok=True, no violations (ADMITTED); fixed tree -> ok=False msg='external STATE_EVENT promotion requires source event identity'. Shipped policy confirms profile H required_fields includes source_event_uid and source_event_uid_required_statuses=['EXTERNAL_SOURCE'].
```

**Reproduction:** `python <scratchpad>/probe_arm3.py from the repo root (loads gateway/src/validators.py, monkeypatches validators._risk_trigger_matches in memory to 'except TypeError: return False', runs arm 3's exact event both ways, then the no-constraint variant both ways)`

### CR-17 (MODERATE) — c54215a commit message claims 'Seven allowlist sites' — the tree has six, at the commit and at HEAD

**Anchor:** `gateway/src/validators.py:1026` · **Commit:** c54215a · **Found by:** x-halfapplied

**Claim under test:** c54215a message (also the A-14 polarity-fix summary): '_risk_trigger_matches is a separate function precisely so the polarity is visible at the call site. Seven allowlist sites, three trigger sites, all enumerated.'

**Observed:** _allowlist_contains has exactly SIX call sites, all in _validate_external_state_promotion (validators.py:1425 origin_kind, :1443 lineage_status, :1516 loop_status, :1538 policy_id, :1551 projection_id, :1564 confidence_basis); repo-wide grep finds no seventh. _risk_trigger_matches has three (:1456, :1482, :1484) — that half is correct, and it is the only count the record file repeats (audit :1751 'three risk/trigger sites'). Counted at the commit itself (git grep on c54215a's blob: same six) — so the message was false when written, not staled later. No unguarded raw `in <set>` membership test on promotion metadata remains (state_category uses scalar !=, trust_ref uses str() prefix), so no code layer is missing — the defect is confined to the message. 'Commit-message-to-diff truth' is one of this cycle's own eleven audit lenses; a future auditor enumerating the guard from the message will hunt a seventh site that never existed or suspect one was lost.

**Evidence:**

```
git grep -n '_allowlist_contains(' HEAD -- '*.py' → def at :1026, docstring ref at :1058, call sites :1425, :1443, :1516, :1538, :1551, :1564 (six). git show c54215a:gateway/src/validators.py | grep -n → identical six + three trigger sites. git log -1 --format=%B c54215a: 'Seven allowlist sites, three trigger sites, all enumerated.' The enumeration pin (test_policy_shape_fail_closed.py:1237-1252) derives sites from AST, so it cannot catch the prose count.
```

**Reproduction:** `git log -1 --format=%B c54215a | grep -i 'seven allowlist'; git grep -n '_allowlist_contains(' HEAD -- '*.py' | grep -v 'def _allowlist_contains' | grep -v 'caller asks' (six call sites); git grep -n '_risk_trigger_matches(' HEAD -- '*.py' | grep -v def (three)`

### CR-18 (MINOR) — Decimal non-finite confidence is reported under the generic SCHEMA_INVALID, not NON_FINITE_CONFIDENCE — the confidence path loses its specific diagnostic exactly for the wire shape _is_non_finite_number was widened to catch

**Anchor:** `gateway/src/validators.py:540` · **Commit:** c54215a / 74d92e1 · **Found by:** w2-runtime

**Claim under test:** The non-finite gate's own comments and the audit record promise that the two confidence paths keep the specific NON_FINITE_CONFIDENCE code while every other non-finite value falls to SCHEMA_INVALID. validators.py:529-532 '_find_non_finite_confidence ... the two confidence sites keep their own, more specific diagnostic'; validators.py:3020-3022 'only the reported code is path sensitive, so the confidence fields keep their more specific NON_FINITE_CONFIDENCE'; validators.py:3148-3150 'reports NON_FINITE_CONFIDENCE for exactly these two paths and SCHEMA_INVALID everywhere else'; docs/r1_11_full_stack_audit.md:1341 'NaN and inf at both confidence and payload.claim.confidence -> NON_FINITE_CONFI…

**Observed:** _find_non_finite_confidence (line 540) tests `isinstance(conf_value, float) and not math.isfinite(conf_value)` — float-ONLY — while the gate driver _find_non_finite uses _is_non_finite_number, which deliberately ALSO handles Decimal (validators.py:326-330). A CBOR tag-5 bigfloat with a NaN/Inf mantissa decodes (under cbor2) into Decimal('NaN')/Decimal('Infinity') — the exact case _is_non_finite_number's docstring at 321-325 cites as the reason Decimal is handled. So a Decimal non-finite AT event.confidence or payload.claim.confidence trips _find_non_finite (event is refused, fail-closed, correct) but _find_non_finite_confidence returns None, so it is reported as SCHEMA_INVALID rather than NON_FINITE_CONFIDENCE. The event is still refused with fail severity and details.field still names the exact path, so this is diagnostic-granularity only, not laundering — but it contradicts the three comments and the audit line above, and an operator filtering reason_code==NON_FINITE_CONFIDENCE to catch dishonest-confidence producers silently misses the Decimal case, bucketing it under the broad S…

**Evidence:**

```
Repro on shipped schema+policy, real Profile-L TRACK_STATE, validate_semantics(ev, policy['semantics']):
  confidence=float NaN    -> [('NON_FINITE_CONFIDENCE', {'field': 'confidence'})]
  confidence=Decimal NaN  -> [('SCHEMA_INVALID', {'field': 'confidence'})]
  confidence=float Inf    -> [('NON_FINITE_CONFIDENCE', {'field': 'confidence'})]
  confidence=Decimal Inf  -> [('SCHEMA_INVALID', {'field': 'confidence'})]
  payload.claim.confidence=Decimal NaN -> [('SCHEMA_INVALID', {'field': 'payload.claim.confidence'})]
validators.py:540 `if isinstance(conf_value, float) and not math.isfinite(conf_value):` vs validators.py:326-330 (_is_non_finite_number handles float AND Decimal).
```

**Reproduction:** `cd repo; python: sys.path.insert(0,'gateway/src'); import validators as V; from decimal import Decimal; validator=V.load_schema('schema/zmeta-event-1.0.schema.json'); policy=V.load_policy('policy'); ev = <any schema-valid STATE_EVENT>; ev['confidence']=Decimal('NaN'); print(V.validate_semantics(ev, policy['semantics'])[1]) -> [('SCHEMA_INVALID', {'field':'confidence'})]; set ev['confidence']=float('nan') -> NON_FINITE_CONFIDENCE.`

### CR-19 (MINOR) — RegistrationStore: duplicate mode_name declarations resolve last-wins instead of conflict-poisoning — order-dependent, and the broken-then-sane ordering erases the unresolved flag

**Anchor:** `adapters/ingress/sapient/registration_state.py:215` · **Commit:** c54215a · **Found by:** w3-ingress

**Claim under test:** Module docstring :13-14: "unknown or conflicting declarations are never resolved by guessing", and _merge (:128-133) implements exactly that for units/velocity/error declarations in the same ingest loop: "Conflicting redeclaration poisons the key; lookups then return None."

**Observed:** The modes map does not get the _merge treatment: `modes[mode_name] = {...}` at :215 silently overwrites on a duplicate mode_name within one registration. The two orderings of the same conflicting message produce opposite dispositions — broken-then-sane yields latency 500.0 / unresolved False (the unresolvable declaration vanishes and the node publishes the tighter bound with no degradation), sane-then-broken yields latency None / unresolved True. A conflicting declaration is resolved by guessing (last wins), against the module's own stated rule and against the poison convention applied to declared_units/velocity_factors/geometric_error in the same function. Requires a malformed registration (duplicate mode names), and the escape direction exists in only one ordering — hence MINOR. Not banked: no register/doctrine entry covers mode redeclaration; the test file has no duplicate-mode case.

**Evidence:**

```
Probe:
  ingest one registration with mode_definition [broken(NaN latency), sane(0.5s)] both named 'surveillance' -> max_latency_ms 500.0, latency_unresolved False
  same two entries reversed -> max_latency_ms None, latency_unresolved True
Code: :211-225 `if isinstance(mode_name, str) and mode_name: ... modes[mode_name] = {...}` — plain assignment, no conflict check, five lines above the _merge calls that poison.
```

**Reproduction:** `cd <repo> && python -c "import sys; sys.path.insert(0,'.'); from adapters.ingress.sapient.registration_state import RegistrationStore; reg=lambda m:{'node_id':'n1','registration':{'mode_definition':m}}; b={'mode_name':'s','maximum_latency':{'value':float('nan'),'units':'TIME_UNITS_SECONDS'}}; g={'mode_name':'s','maximum_latency':{'value':0.5,'units':'TIME_UNITS_SECONDS'}}; s1=RegistrationStore(); s1.ingest(reg([b,g])); print(s1.max_latency_ms('n…`

### CR-20 (MINOR) — Doctrine log entry R1-11-08 anchors zmeta_to_cot.py:235-237/268-270 — lines that match no committed tree in the held range; the code it names sits at 338-341/369-375 at HEAD

**Anchor:** `docs/zmeta_doctrine_review_log.md:252` · **Commit:** a3c4c51 committed the entry already stale: at that commit the sites were at 299-300/332-333 (verified via git show), at origin/main 194-195/227-228, at HEAD 338-341/369-375; the c54215a insertions (+_stale_time) moved them again and the log was not re-anchored · **Found by:** w4-egress

**Claim under test:** The entry states the zero-default sites are at 'zmeta_to_cot.py:235-237, 268-270', and the playbook's per-wave contract plus the standing 'resume from the tree' rule make file:line anchors in cycle records load-bearing for whoever adjudicates the 21 open tensions.

**Observed:** At HEAD, lines 235-237 are inside the non-finite guard's comment block and 268-270 are the missing-ts refusal comment — a maintainer following the anchor lands in unrelated prose. The quoted expression (`error_ellipse.get("semi_major", 0)`) remains greppable, so the entry is recoverable, but this is a fresh instance of the record-anchor-drift class the cycle itself carries as the open A-13 MAJOR (different record, different mechanism: line drift from same-range insertions rather than a moving ref). The anchors were verifiably wrong at the moment the record was committed, not merely aged.

**Evidence:**

```
docs/zmeta_doctrine_review_log.md:252: '`zmeta_to_cot.py:235-237, 268-270` use `error_ellipse.get("semi_major", 0)`'. git show a3c4c51:adapters/egress/cot/zmeta_to_cot.py | grep -n semi_major -> 299-300, 332-333. Current tree: grep -n 'semi_major' adapters/egress/cot/zmeta_to_cot.py -> 339, 372 (code sites).
```

**Reproduction:** `sed -n '235,237p;268,270p' adapters/egress/cot/zmeta_to_cot.py (comment text, no code); git show a3c4c51:adapters/egress/cot/zmeta_to_cot.py | grep -n 'semi_major.*0'`

### CR-21 (MINOR) — JREAP egress emits lat/lon as null for a present-but-partial geo, while its docstring and the held-range README refusal table say 'missing geo' is refused

**Anchor:** `adapters/egress/jreap/zmeta_state_to_jreap_track_json.py:123` · **Commit:** check is pre-existing; the refusal table asserting it is held-range (README.md lines 17-23, added in this range) · **Found by:** w4-egress

**Claim under test:** Docstring lines 107-110 and the new README table row: 'Not a STATE_EVENT/TRACK_STATE, or missing track_id/geo/ts/valid_for_ms | refused'. The module's stated posture (README heading added this range) is 'fail closed, never substitute'.

**Observed:** Line 123 tests only truthiness (`not geo`), so geo={'lat': 1.0} — present but lacking lon — passes the gate and the built track carries 'lon': None (and 'hae_m': None) to the tactical-track consumer. Nulls are not fabricated values, so this is a claim-vs-code precision gap rather than laundering; it is also unreachable through the kernel gate (schema geo requires lat/lon/alt_m), but JREAP has no gateway call site at all — its entire caller population is embedders reading exactly this docstring, the same exposure argument the cycle's own A-10 used. The CoT sibling refuses this shape explicitly (zmeta_to_cot.py:214: lat/lon is None -> None).

**Evidence:**

```
Live: event with geo={'lat': 1.0} -> {'track_id': 'T1', 'lat': 1.0, 'lon': None, 'hae_m': None, 'timestamp': '2026-07-01T00:00:00Z', 'stale_time': '2026-07-01T00:01:00Z', 'track_type': 'UNKNOWN'} — a track dict with a null longitude, not a refusal.
```

**Reproduction:** `cd repo; python -c "from adapters.egress.jreap.zmeta_state_to_jreap_track_json import zmeta_state_to_jreap_track_json as j; print(j({'event':{'event_type':'STATE_EVENT','event_subtype':'TRACK_STATE','ts':'2026-07-01T00:00:00Z'},'payload':{'track_id':'T1','geo':{'lat':1.0},'valid_for_ms':60000}}))"`

### CR-22 (MINOR) — The A-23 checksum-rewrite guard's degraded-mode contract is false: a tagless/shallow checkout yields set(), not None, so it silently treats a published version as unpublished

**Anchor:** `release/sign_release_artifacts.py:27` · **Commit:** c54215a · **Found by:** w5-release

**Claim under test:** `_published_release_tags` docstring (:27-28): 'None means the question could not be answered (no git, shallow/tagless checkout) - the caller must say so rather than treat an unverifiable state as verified'; the new test's comment (gateway/tests/test_release_signing.py:194-196) repeats it: 'in a tagless/shallow checkout the tool cannot tell whether the version is published. It proceeds ... but it says so'.

**Observed:** In a tagless checkout git is present and `git tag -l v*` returns rc 0 with empty output, so the function returns `set()` — None is reachable only when git itself is absent or errors. `_refuse_if_published` then evaluates `version in set()` as an authoritative 'not published' and proceeds with NO refusal and NO 'overwritten unverified' warning (:128 never fires) — i.e. in exactly the environment both docstrings name, a bare `--write-checksums` would silently rewrite SHA256SUMS_v1.1.16.txt, and the immutability pytest backstop is also degraded to its corpus floor there. The test models the case only by monkeypatching the function to return None, so the suite never observes the real tagless behaviour. Exposure is low (nothing in CI or any script calls the destructive path; the checklist runs in the maintainer's full clone; A-23's other mitigations hold), and the sibling non-vacuity pin coincidentally fails loudly in tagless CI (finding 1). Distinct from banked A-23 ('no guard existed'): this is the guard added FOR A-23 misdescribing its own failure mode.

**Evidence:**

```
Probe with ROOT pointed at a freshly-initialized tagless repo containing release/SHA256SUMS_v1.1.16.txt: `tagless checkout _published_release_tags() -> set()` and `refusal raised: NO; warning printed: ''`. Contrast the real repo: `v1.1.16: refused -> refusing to rewrite SHA256SUMS_v1.1.16.txt: ...`.
```

**Reproduction:** `mkdir t && cd t && git init -q . && mkdir release && echo x > release/SHA256SUMS_v1.1.16.txt; then in python: load release/sign_release_artifacts.py via importlib, set module ROOT to the t dir, call _published_release_tags() (returns set(), not None) and _refuse_if_published(t/'release', 'v1.1.16') (returns silently, no warning on stdout)`

### CR-23 (MINOR) — Handoff resume queue freezes '27 commits ahead' against the moving held range — stale in its own commit, and invisible to the new A-13 guard

**Anchor:** `docs/zmeta_refinement_handoff.md:5` · **Commit:** 35f603c · **Found by:** w6-records, x-committruth, x-halfapplied, x-pins (independent convergence)

**Claim under test:** Resume queue opening line (:5): 'The R1-11 cycle is concluded and HELD: 27 commits ahead of origin/main'.

**Observed:** The count was stale the moment its own commit landed (git rev-list --count origin/main..35f603c = 28; the 27 measured the pre-commit tree at 98bff42) and is 30 at HEAD. This is a live recurrence of the banked A-13 class (frozen totals attributed to a moving ref — 'the fifth recurrence' per the fresh audit) at a NEW site, in the same file whose later text (:88-90) explains 'The range keeps growing, so no total is frozen here (A-13...)'. The 2026-07-26 refresh commit 7eaea97 edited this same file (doctrine counts 20→21) and left the commit count untouched. The new guard written for the A-13 class (test_records_claim_currency.py:83, _DIFF_TOTAL = r'\+\d{3,}\s*/...') matches only '+NNNN / -NNN' diff totals, so a commit-count claim is structurally outside its reach — the guard is blind to this family member. Distinct from the banked open MAJOR (the half-anchored eb41794 diff figures): different line, different claim shape, unguarded.

**Evidence:**

```
docs/zmeta_refinement_handoff.md:5: '27 commits ahead of `origin/main`'. git rev-list --count origin/main..98bff42 = 27; ..35f603c = 28; ..HEAD = 30. Same file :88-90: 'The range keeps growing, so no total is frozen here (A-13: the figure that used to sit on this line was falsified by the commit that wrote it, twice over).' Guard scope: gateway/tests/test_records_claim_currency.py:83 _DIFF_TOTAL regex — no commit-count pattern; pytest is green with the stale 27 present (1200+1021 passed this session).
```

**Reproduction:** `grep -n '27 commits ahead' docs/zmeta_refinement_handoff.md; git rev-list --count origin/main..35f603c; git rev-list --count origin/main..HEAD; python -m pytest gateway/tests/test_records_claim_currency.py -q (green with the stale count present)`

### CR-24 (MINOR) — After-action log upgrades the six blockers to 'six MAJOR blockers'; the audit record grades one of them MODERATE

**Anchor:** `docs/zmeta_after_action_log.md:35` · **Commit:** b1e5b69 · **Found by:** w6-records

**Claim under test:** 'A fresh full-stack audit of that held work found **six MAJOR blockers** it had missed — ... and a MAVLink altitude fabrication'.

**Observed:** The fresh audit's own findings grade A-01..A-05 MAJOR and A-06 — the MAVLink altitude fabrication the AAR sentence itself names — '(MODERATE, honesty/fielded safety)' (docs/r1_11_full_stack_audit.md:1086). Its blocker table (:1361-1376) lists six BLOCKERS without asserting six MAJORs, and every other record says 'six blockers' or 'six release-blocking defects'. The AAR is the standing public artifact contributors read; it overstates the severity mix of the cycle's headline result by one grade on one finding.

**Evidence:**

```
docs/zmeta_after_action_log.md:35-39 quoted (names 'a MAVLink altitude fabrication' among the 'six MAJOR blockers'); docs/r1_11_full_stack_audit.md:1086 'A-06 (MODERATE, honesty/fielded safety): The MAVLink state template zero-fills a missing altitude...'; :1408 'Maintainer disposition on the fresh audit: fix all six blockers' (no MAJOR claim); :1046 '28 findings survived... Numbered in severity order' with the MAJOR section ending at A-05.
```

**Reproduction:** `grep -n 'six MAJOR blockers' docs/zmeta_after_action_log.md; grep -n 'A-06 (MODERATE' docs/r1_11_full_stack_audit.md.`

### CR-25 (MINOR) — Fresh-audit record says '28 findings survived' but enumerates 30 (A-01..A-30), and no stated count reconciles the disposition's '91 findings'

**Anchor:** `docs/r1_11_full_stack_audit.md:1046` · **Commit:** 02cb688 / 8955974 · **Found by:** x-committruth, x-halfapplied (independent convergence)

**Claim under test:** Audit record :973: '35 candidates were killed. 28 survived.' and :1046: '28 findings survived three-lens refutation. Numbered in severity order.'

**Observed:** The findings section then enumerates exactly 30 entries, A-01..A-30 (5 MAJOR, 7 MODERATE, 15 MINOR, 3 OBSERVATION), with no note reconciling 30 listed vs 28 survived (plausibly A-28 aggregates the six UNPINNED Step-0 rows and A-30 is the critic pass's own coverage measurement — but the text never says which two are outside the count). The downstream disposition arithmetic then fails on every reading: 'Ten groups, 91 findings handled across both registers' (c54215a; audit :1712) reconciles with the 62-finding register neither via 28 (62+28=90) nor 30 (62+30=92); no surface derives 91. This cycle pinned a 'finding-count ground truth' table (checklist item 5) precisely because count drift recurred four times during closeout, and the 7eaea97 refresh caught the same class in the doctrine log (20 vs 21) — this is the remaining unreconciled count set.

**Evidence:**

```
sed -n 1044,1046p: '28 findings survived three-lens refutation.' grep -o 'A-[0-9]* (MAJOR|MODERATE|MINOR|OBSERVATION' over :1044-1245 → 30 distinct entries A-01..A-30 (verified count = 30). :973: '35 candidates were killed. 28 survived.' :1712: '91 findings dispositioned. 46 open, 2 MAJOR.' c54215a message: '91 findings handled across both registers' and separately '47 ... remain open' (vs the record's 46). Register total = 62 (grep -c '^### R').
```

**Reproduction:** `awk 'NR>=1044 && NR<=1245' docs/r1_11_full_stack_audit.md | grep -c '^- \*\*A-' (30); grep -n '28 survived|28 findings survived|91 findings' docs/r1_11_full_stack_audit.md; grep -c '^### R' docs/r1_11_fix_pass_findings.md (62)`

### CR-26 (MINOR) — Public playbook states the operational cost figure the AAR says is redacted to the private companion

**Anchor:** `docs/zmeta_audit_playbook.md:17` · **Commit:** b1e5b69 · **Found by:** x-committruth

**Claim under test:** AAR (docs/zmeta_after_action_log.md:14-15): "Operational cost figures and internal strategy are kept in a private companion copy"; the AAR entry reports cost only "in shape (not in raw figures)". b1e5b69's message repeats: "Operational cost figures and strategy stay in a private companion."

**Observed:** docs/zmeta_audit_playbook.md:17-18, committed in the same b1e5b69, publishes the raw figure: "it also spent about thirteen continuous hours". The redaction rule and the figure it redacts landed in the same commit, one file apart. (Aligned concern: the standing collaboration rule to keep operational/strategy detail out of public repo files.)

**Evidence:**

```
playbook :17: "survived multiple prior cycles — but it also spent about thirteen continuous hours"; AAR :14-15 quoted; AAR entry's cost section is deliberately figure-free ("What it cost, in shape").
```

**Reproduction:** `Read docs/zmeta_audit_playbook.md:15-20 next to docs/zmeta_after_action_log.md:8-20.`

### CR-27 (MINOR) — The doctrine log carries the same tension twice as unlinked OPEN entries (R1-11-14 and R1-11-19), and the renumber pass that touched exactly this collision left the duplicate content unflagged

**Anchor:** `docs/zmeta_doctrine_review_log.md:488` · **Commit:** 7eaea97 · **Found by:** x-pins

**Claim under test:** 7eaea97 ('renumber the addendum to 15-21, closing the R1-11-14 collision') and the addendum note (:404-407) present the renumber as exposing 'a duplicate R1-11-14 hiding one entry', giving 'twenty-one entries, not ... twenty'; the disposition State and the resume queue item 2 direct the maintainer to 'adjudicate the 21 doctrine-log entries'.

**Observed:** First-pass R1-11-14 (:332, '`--strict` makes a *tolerated* warn unrepresentable in the corpus', gates 3/7) and addendum R1-11-19 (:488, '`--strict` makes a tolerated warn unrepresentable', gates 2/3-vs-7) record the SAME tension — same mechanism (validate_examples.py promotes warns to failures under the mandated --strict --require-all), same surface (the teaching corpus cannot show a deliberately tolerated warn), same open question. The addendum intro discloses generically that 'several are the same tension arriving from a new direction', and other repeats are cross-linked (R1-11-18 says 'Adjudicate with R1-11-02 and R1-11-03'; the resume queue clusters 02/03/18 and 09/15/16) — but 14/19 are linked nowhere: not in either entry body, not in the clusters, not by the renumber commit whose whole subject was entry 14. Consequence: 21 entries hold 20 distinct tensions, and the lifecycle's recurrence counter (d77ad9e: third recurrence forces a terminal status) is fragmented — the --strict tension has already recurred twice within one cycle but each entry shows one occurrence, so the forcin…

**Evidence:**

```
docs/zmeta_doctrine_review_log.md:332-372 (R1-11-14: 'no shipped example can ever demonstrate the case the contract says is tolerated', raised from A-21) vs :488-499 (R1-11-19: 'a condition the standard deliberately tolerates as a warning cannot be shown in an example ... No change made'); :404-407 (renumber note claiming the collision hid 'one entry'); :554-569 (lifecycle recurrence rule adopted in d77ad9e); grep shows no cross-reference between 14 and 19 in either body or in docs/zmeta_refinement_handoff.md item 2.
```

**Reproduction:** `Read docs/zmeta_doctrine_review_log.md:332-372 beside :488-499; grep -n 'R1-11-14\|R1-11-19' docs/zmeta_doctrine_review_log.md docs/zmeta_refinement_handoff.md and observe no line links the two`

### CR-28 (OBSERVATION) — _wire_safe_details residue-(2) justification 'not JSON-encodable at all, so a wrapper in details makes the encode fail loudly' is incomplete — cbor2.dumps encodes a CBORTag-carried NaN straight onto the CBOR wire; the safety rests on unreachability, not on loud failure

**Anchor:** `gateway/src/gateway.py:1723` · **Commit:** c54215a · **Found by:** w2-runtime

**Claim under test:** gateway.py:1720-1725 argues that leaving a cbor2.CBORTag untouched in violation details is safe because 'it is not JSON-encodable at all, so a wrapper in details makes the encode fail loudly rather than shipping a laundered value. Loud failure is the acceptable end state.' _convert (1766) sanitizes non-finite floats/Decimals and dict/list/tuple/set/frozenset/Mapping/AbstractSet, but deliberately does NOT descend into a .tag/.value wrapper.

**Observed:** The 'fails loudly' reasoning is JSON-specific and false for the two binary output encodings the gateway supports. On a cbor2-only install _encode_cbor calls cbor2.dumps, which encodes a CBORTag carrying a NaN and round-trips it back to a non-finite value (bytes produced, no exception). So IF a CBORTag ever reached details, output_encoding=cbor would ship the NaN, not fail. Separately, a FINITE Decimal (Decimal('1.5'), also a cbor2 tag-5 decode) is left untouched by _convert (not non-finite, not a container); on json output json.dumps raises TypeError, which _encode_outgoing_or_diagnostic (gateway.py:1209) does NOT catch (only _COMPACT_UNREPRESENTABLE), so it escapes to the receive-loop backstop as an INTERNAL_ERROR drop that abandons the remaining outgoing events in that datagram — the same sibling-abandonment shape as the banked R2-05. I could NOT demonstrate a CBORTag or raw Decimal actually reaching details: the non-finite gate refuses any event containing a CBORTag-with-NaN before downstream echoing, and the pre-gate validators (schema/role/profile echo only paths/strings; valid…

**Evidence:**

```
import cbor2, gateway as G, math; d={'reason_code':'X','est':cbor2.CBORTag(1234,[float('nan')])}; out=G._wire_safe_details(d) -> out['est'] is still CBORTag(1234,[nan]); cbor2.dumps(out) -> SUCCEEDS (26 bytes); cbor2.loads(...)['est'].value[0] is nan (non-finite True); G._encode_cbor(out) -> TypeError only because zmeta_cbor is installed here (the fallback cbor2.dumps path does not raise). gateway.py:1723 'it is not JSON-encodable at all, so a wrapper in details makes the encode fail loudly'; _encode_outgoing_or_diagnostic at gateway.py:1207-1236 catches only _COMPACT_UNREPRESENTABLE.
```

**Reproduction:** `python: sys.path.insert(0,'gateway/src'); import gateway as G, cbor2, math; out=G._wire_safe_details({'m':cbor2.CBORTag(258,[float('nan')])}); print(type(out['m']).__name__); print(cbor2.dumps(out)); print(cbor2.loads(cbor2.dumps(out))['m'])`

### CR-29 (OBSERVATION) — Playbook adoption is recorded without an adopter, 43 minutes after being declared pending the maintainer's sign-off

**Anchor:** `docs/zmeta_audit_playbook.md:8` · **Commit:** b1e5b69 22:09 -> 98bff42 22:52 (2026-07-22) · **Found by:** x-committruth

**Claim under test:** b1e5b69's message: "Both docs are DRAFTS pending the maintainer's sign-off on the wave partition, the cadence trigger model, the introduction-rate cap, and the per-wave severity floor." 98bff42 (43 minutes later): "Lifts the draft markers. The R1-11 after-action decisions are now in force." Playbook :8: "Adopted 2026-07-22 from the R1-11 after-action review."

**Observed:** No surface in the tree records WHO adopted: the playbook attributes adoption to "the R1-11 after-action review" (a process, not a decider), 98bff42's message names no maintainer, and the worklog carries no adoption entry — in a record set that otherwise consistently attributes decisions ("Maintainer disposition on the fresh audit: fix all six blockers" :1408; "Maintainer direction was to ..." c54215a). The four sign-off items reappear at :195-197 recast as "watch-items, not open questions". A maintainer approval given live in-session cannot be ruled out from the tree — flagged only because the adoption record, as written, does not carry it, and this playbook now governs the audit process (this refresh runs under it).

**Evidence:**

```
git log timestamps: b1e5b69 2026-07-22 22:09:41, 98bff42 2026-07-22 22:52:38; playbook :8 and :186-193 quoted; grep -i 'adopt' docs/zmeta_refinement_worklog.md -> no R1-11 adoption entry.
```

**Reproduction:** `git log --format='%h %ci %s' -2 98bff42; read docs/zmeta_audit_playbook.md:8-11 and the Status section; search the tree for a maintainer adoption record.`

### CR-30 (OBSERVATION) — Positive assurance: the half-applied multi-layer hunt found no missing CODE layer — every claimed layer located and probed in the current tree

**Anchor:** `docs/r1_11_closure_probe.py:1` · **Commit:** 1c78a85 / c54215a · **Found by:** x-halfapplied

**Claim under test:** The cycle's records claim: six blockers closed (probe 17/17), B-01..B-04 fixed, V2-01 two layers, V2-03 seven sinks, V2-12 four docs + completeness pin, V2-13 three layers, A-01 extended to four egress adapters, all four confidence clamps NaN-guarded, battery 1200+1021 / gate exit 0 / examples 51/51.

**Observed:** All verified against the CURRENT tree, most by live execution. Closure probe: 17/17 CLOSED. pytest: 1200 passed + 1021 subtests, exactly as recorded. Kernel gate all flags exit 0 (bad-events 29, harness 40); examples 51/51 strict. B-01: compact refuses set/Decimal/10**400/bytes/int-key/bool-key on BOTH backends, passes honest values. B-02: four timing_freshness mangles each lint loud. B-03: unusable declared latency now yields UNKNOWN/UNSYNCED/est_error_ms 60000 (wider, not narrower). B-04: vocabulary + severity ordering with strip/casefold, non-strings refused without str() coercion (R2-08's coercion deleted as claimed). R1-06: NaN confidence → SYSTEM_EVENT refusal, and all four clamp sites carry non-finite guards. V2-01: codec conversion (zmeta_compact.py:657-724) + scoped receive-loop backstop (gateway.py:2370-2519, recvfrom outside) both present. V2-03: 7/7 VENDOR_EXTENSION_KEY sinks wrapped at point of use. V2-12: 4 docs pinned + completeness scan. V2-13: builder --release-notes + RELEASE_PACKAGE_NOTES_PLACEHOLDER + checklist step. A-01 egress: non-finite guards present in cot/…

**Evidence:**

```
python docs/r1_11_closure_probe.py → 17x CLOSED, TOTAL VERDICTS: 17. python -m pytest -q → '1200 passed, 1021 subtests passed in 32.95s'. tools/validate_conformance.py all flags → exit 0. tools/validate_examples.py --strict --require-all → 51/51. Probe outputs quoted in coverage (B-01 REFUSED x12 cells, B-02 lint=1 issue per mangle, B-03 est_error_ms 505/60000/60000, R1-06 'SYSTEM_EVENT SCHEMA_VIOLATION confidence = None').
```

**Reproduction:** `python docs/r1_11_closure_probe.py; python -m pytest -q; python tools/validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative --precision-policy --release-manifest --release-package --bad-events --adapter-harness; python tools/validate_examples.py --strict --require-all`

---

## Refuted (recorded so the negative is not re-derived)

- (w4-egress) Blast-radius annotation on the BANKED _parse_utc MAJOR (not a re-report): the raise class includes a Windows OSError arm the disposition proved and fixed in the two SAPIENT twins but left in CoT/JREAP, plus an in-gateway consequence the carried-forw… — refuter: The reproductions run exactly as claimed (verified live on this Windows tree: OSError [Errno 22] from both CoT and JREAP on ts='1969-12-31T23:59:59'; AttributeError on ts=12345; c54215a added the OSError arm + rationale only to the two SAPIENT twins while touching zmeta_to_cot.py in the same commit). But the finding's load-bearing premise — that the naive pre-epoch ts is "gate-clean for the same…

## Coverage and known gaps (the completeness critic)

Coverage of the CODE surfaces is genuinely strong: every changed production module was read in full by at least one reader (gateway.py, validators.py sectionally, zmeta_compact.py, zmeta_cbor.py, all 6 egress adapter modules, the ingress mavlink/sapient/time_utils modules, all 11 tools/*, release/*, conformance/*, and all four governed files verified to the byte), with live probes and the full battery re-run by four independent readers. Records surfaces were read near-exhaustively by three readers. All 12 post-eb41794 commits are named in at least one coverage line. The systematic hole is the NEW TEST MASS: the post-eb41794 commits (1c78a85 + c54215a, the exact weighted scope) added ~7,822 lines to test files, and the pin-quality/vacuous-pin lens (x-pins) deep-read well under 1,000 of them. test_policy_shape_fail_closed.py (+1,796, the single largest new file in the weighted range) had zero readers at any depth; test_compact_mapping_spec_sync.py (+516) and test_encoding_cli_refusals.py (+142), both born in c54215a — the commit confirmed to have introduced ~35 defects — were never opened; the five egress adapter test files (+1,014 combined in the weighted range) were grep-only, despite four confirmed egress fabrication MAJORs living in exactly the modules they pin. Given a confirmed nonzero base rate of vacuous pins (the trigger-polarity Arm-3 finding), unread test code in a range whose introduction rate hit 74% is the one place a material miss is likely. Secondary gaps: gateway/README.md +29 (landed in fix-pass 1c78a85, post-eb41794) claimed by nobody, in a cycle with a confirmed recurring stale-claim class; and a tail of ~10 small pre-eb41794 doc/config files (TRADEMARK.md, adapters/AUTHORING.md +36/-12, adapters/README.md, mapping-packs README + mapping.yaml, four docs/ teaching pages) with zero coverage lines — mitigated because they pre-date eb41794 and were inside the dispositioned fresh audit 02cb688, but formally uncovered in this re-read.

Gaps, in the critic's priority order — these are the candidate surface for the
next scoped wave, not open findings:

- **gateway/tests/test_policy_shape_fail_closed.py — +1,796 lines across 1c78a85 and c54215a (post-eb41794, weighted scope); no reader opened it at any depth (w2 explicitly deferred gateway/tests, x-pins does not list it, x-halfapplied read only the validators.py lint layers it pins).**
  It is the single largest new file in the weighted range and pins the policy fail-closed behavior that several banked MAJORs depend on. The confirmed Arm-3 vacuous-pin finding proves this range produces pins that pass on the reverted tree; nobody applied that lens to the biggest pin surface, half of which was written by c54215a — the commit confirm…
- **Five egress adapter test files — test_zmeta_to_cot.py (+326), test_sapient_egress.py (+351 total, +248 post-eb41794), test_mavlink_intent.py (+166), test_jreap_projection.py (+136), test_klv_egress.py (+116), all touched by 1c78a85/c54215a — read only by grep (w4's self-declared limit); no vacuous-pin or lock-in read.**
  Four confirmed MAJOR fabrications live in exactly these modules (CoT le vertical-certainty projection, CoT geopointsrc/altsrc=GPS stamps, MAVLink priority=MED minting, SAPIENT use_labels fail-open). Nobody checked whether the new tests assert the fabricated output as EXPECTED — if they do, the defects are now test-enforced and any future fix will…
- **gateway/tests/test_compact_mapping_spec_sync.py (+516) and test_encoding_cli_refusals.py (+142), both created entirely by c54215a — zero readers.**
  Both were minted by the disposition commit itself, the commit with the highest confirmed self-introduction count in the cycle, and test_compact_mapping_spec_sync.py enforces spec-to-code sync for the compact mapping — a surface where the doctrine log banks normative-addition tensions (R1-11-02/03/18). A sync test that mirrors the code rather than…
- **gateway/README.md — +29 lines added by fix-pass commit 1c78a85 (post-eb41794); no coverage line claims it (w2 read gateway/src only, w6's surface was docs/ records).**
  The cycle has a confirmed recurring claim-currency defect class (stale HOLD banners, the A-13 '27 commits' recurrences, false 'no governed artifact touched' claims). A teaching README amended mid-fix-pass and never re-read against the post-disposition tree is precisely where that class recurs, and it is the one post-eb41794 prose surface with zero…
- **gateway/src/validators.py held diff (+1,689/-59 across 5 commits incl. 1c78a85 and c54215a): coverage is a union of named section ranges (w2: ~300-505, 528-542, 718-765, 1026-1078, 1208-1375, 1420-1574, 2190-2247, 2782-2945, 3001-3265; x-pins: 1025-1160, 1400-1540; x-halfapplied: 2031-2341) — no reader claims full-hunk coverage of the file's diff, and the file is 3,952 lines.**
  The 'resume from the tree' rule exists because committed fixes can be half-applied; sectional reads verify the claimed layers but cannot see an unclaimed hunk. Roughly the ranges 1575-2030 and 2342-2780 (plus anything before line 300) were never named by anyone, so any c54215a edit landing there was seen by zero cold readers.
- **Partially-read large post-eb41794 test files: test_gateway_runtime_guards.py (+1,455; x-pins read two test groups, rest via commit diff inventory only), test_non_finite_value_scoped.py (+922; new tests seen 'via diff'), test_compact_fail_closed.py (+804; two classes read), test_governed_doc_claims.py (+345; 'structure' only).**
  Together with the zero-coverage files above, deep-read pin-quality coverage of the ~7,822 post-eb41794 test lines is well under 15%. The battery passing (verified four times) proves the pins are green, not that they are non-vacuous or pinning honest behavior — the two failure modes this range has already confirmed instances of.
- **Pre-eb41794 files with zero coverage in this re-read: TRADEMARK.md (6ea9888), adapters/AUTHORING.md (+36/-12, 05ad9a8), adapters/README.md (+8/-1), adapters/mapping-packs/README.md (+11/-1), adapters/mapping-packs/sapient-bsi-flex-335/mapping.yaml (±2, 88b527e), docs/zmeta_correlation_pattern.md, docs/zmeta_mqtt_binding_guidance.md, docs/zmeta_vocabulary_crosswalk.md (±1 each, 6ea9888), docs/zmet…**
  Low priority — all pre-date eb41794 and sat inside the dispositioned fresh audit 02cb688 — but the whole range was declared in scope and these files appear in no coverage line at all. adapters/AUTHORING.md is the material one: 36 changed lines on the external-adapter teaching surface, wave-7 'doc currency' edits whose claims were never re-checked…
- **Claim-class nobody swept: historical battery figures embedded in held commit messages (e.g. 1c78a85's '1004 passed + 858 subtests', and equivalents in 6ea9888/07921e6/c54215a) were never reproduced against their own trees — x-committruth explicitly declared this undone; only the HEAD-state figures (1200+1021) were verified.**
  The cycle's confirmed defect pattern is exactly numeric self-contradiction in its own records (8-vs-10 MAJORs, 14-vs-18 introduced, 28-vs-30 findings, 'seven allowlist sites' vs six, impossible '44 in the register' pointer). Commit messages are permanent record surfaces in the same class; per-commit checkouts would settle whether the pattern exten…
- **Self-declared w3/w5 partials never backfilled by another reader: adapters/ingress/sapient/sapient_to_zmeta.py detection/geo/signal mapping internals (grep-level only) and test_sapient_ingress.py end-to-end (+1,422 in range; helpers and latency sweeps only); gateway/tests/test_release_manifest.py (+82) and test_release_package.py (+101) beyond spot-reads.**
  Mostly mitigated — R2-11/R2-12 are banked open-by-design in the sapient mapping area, and w5 executed the manifest/package builders both ways — but the confirmed negative-maximum_latency narrowing came from precisely the sapient region that was only skimmed, suggesting that region's remaining internals may hold more members of the same sign/launde…

## Per-reader coverage statements

- **w1-kernel**: READ: full `git diff origin/main..HEAD` hunks for every file under spec/, schema/, policy/ (11 files) plus AGENTS.md; the four governed files at HEAD (schema/zmeta-event-1.0.schema.json, schema/zmeta-event-1.1.0.schema.json enum context; policy/violation-codes.yaml head+hunk; policy/semantics.yaml:90-110); schema/zmeta-event.schema.json in full (confirmed pure $ref dispatcher, no third enum site); spec/semantics-contract.md heading map (confirmed section 5.3 = lines 717-749, hunk at 725-731, exactly +6/-1); per-file `git log origin/main..HEAD` for all governed files (touchers: 74d92e1, c1eb9d0, 05ad9a8, 33230af — all before eb41794; nothing after eb41794 touched schema/policy-YAML/contract)…
- **w2-runtime**: WAVE W2 — GATEWAY RUNTIME, Gate 3 (no laundering) + fail-closed lens. Cold re-read of the held range with attention weighted after eb41794 (fix pass 1c78a85 and disposition c54215a, which are the only two commits after eb41794 that touch the wave-2 runtime surface per `git diff --stat eb41794..HEAD -- gateway/src zmeta_compact.py zmeta_cbor.py`).

READ IN FULL: gateway/src/gateway.py (all 2532 lines — the non-finite marker/_wire_safe_details boundary, build_violation/warning/duplicate builders, process_message ingress ladder, the main-loop egress ordering stamp→strip→degrade→validate_outgoing_event→encode, _encode_outgoing_or_diagnostic fallback ladder, _send_datagram/_check_datagram_size o…
- **w3-ingress**: WAVE W3 — INGRESS ADAPTERS, cold re-read at HEAD 7eaea97 (30 commits held, origin/main..HEAD). Enumerated the surface with `git diff --stat origin/main..HEAD -- adapters/ingress`: cot (README + template + tests), jreap (README + template + tests), mavlink (README 125 / template 653 / tests 1237 lines changed), sapient (README, registration_state.py, sapient_to_zmeta.py, test_sapient_ingress.py +1422), signalhunter (template + tests), time_utils.py. READ IN FULL from the current tree (not diffs): adapters/ingress/mavlink/mavlink_to_zmeta_template.py (all 1005 lines), adapters/ingress/mavlink/README.md, adapters/ingress/sapient/registration_state.py (all 406 lines), adapters/ingress/sapient/R…
- **w4-egress**: Read in full at HEAD (7eaea97): adapters/egress/cot/zmeta_to_cot.py (445 ln), adapters/egress/jreap/zmeta_state_to_jreap_track_json.py (152 ln), adapters/egress/klv/zmeta_to_klv_tagdict_template.py (99 ln), adapters/egress/mavlink/zmeta_command_to_mission_intent.py (157 ln), adapters/egress/sapient/zmeta_state_to_sapient_detection.py (425 ln), adapters/egress/sapient/zmeta_command_to_sapient_task.py (225 ln); all five egress READMEs plus their origin/main..HEAD diffs; gateway/src/gateway.py receive loop (2280-2524), _cot_skip_reason (1378-1392) and metrics cot_skipped plumbing; schema defs geo/geo2d/error_ellipse/CommandPayload.priority in both 1.0 and 1.1.0 schemas; contract sections 21.2…
- **w5-release**: WAVE W5 (release & tooling), cold re-read of origin/main..HEAD (30 commits, HEAD 7eaea97), read-only; all probe artifacts written to the session scratchpad; `git status` clean at end. HARD INVARIANT VERIFIED FIRST: `git diff origin/main..HEAD -- release/SHA256SUMS_v1.1.16.txt` is empty (0 bytes) — published checksums untouched. READ (diff + current tree): tools/build_release_manifest.py, tools/validate_release_manifest.py, tools/build_release_package.py, tools/validate_release_package.py, release/sign_release_artifacts.py, tools/{convert_encoding,lint_policy_risk_modes,measure_packet_size,replay,udp_sender,validate_adapter_conformance}.py, tools/README.md, tools/check_adapter.py (fixture-li…
- **w6-records**: READ (full or near-full): docs/zmeta_after_action_log.md, docs/zmeta_audit_playbook.md, docs/zmeta_doctrine_review_log.md (all 21 entries), docs/zmeta_refinement_handoff.md (all 891 lines), docs/zmeta_refinement_worklog.md (resume note, lines 1-140), docs/r1_11_fix_pass_findings.md (preamble, R1-01..R1-16 in detail, all 62 headings enumerated, Round-2 preamble, Disposition table), docs/r1_11_full_stack_audit.md (Verdict, original findings tables R11-01..25, HOLD state, fresh-audit sections 967-1402 complete incl. Step 0 map, A-01..A-30, refuted list, lens table, positive assurance, release readiness, fix-pass 1403-1511, records pass 1511-1710, disposition pass 1710-1816), CHANGELOG.md [Unre…
- **x-committruth**: READ: all 30 commit messages in origin/main..HEAD (09118b3..7eaea97) with full bodies; name-status/diffs for 74d92e1, c1eb9d0, 05ad9a8, 1c78a85 (via 02cb688..1c78a85), c54215a, and every post-c54215a records commit (path-level verification of every "records only" claim — all check out). Read in the CURRENT tree: docs/zmeta_doctrine_review_log.md (complete, 21 entries verified = 14 + 7, statuses match "all OPEN or HELD"), docs/zmeta_audit_playbook.md (complete), docs/zmeta_after_action_log.md (complete), docs/zmeta_refinement_handoff.md (resume queue + HOLD sections), docs/r1_11_fix_pass_findings.md (header, all 62 finding headings, disposition table), docs/r1_11_full_stack_audit.md (structu…
- **x-pins**: COLD RE-READ of held range origin/main..HEAD (30 commits, HEAD 7eaea97), weighted to post-eb41794 work as directed. READ: all 30 commit messages plus per-commit inspection of 74d92e1/c1eb9d0/05ad9a8 (the governed-file diffs), 1c78a85, c54215a (full message + stat), 8955974, and the five records commits after it via the current tree. Records read: docs/r1_11_full_stack_audit.md (Verdict, HOLD state, validation inventory incl. the governed-surfaces table, fresh-audit findings A-01..A-16 in full and A-17..A-29 summaries, fix-pass and disposition sections in full); docs/r1_11_fix_pass_findings.md (all 62 headings, R1-01..R1-16 bodies, disposition trailer); docs/zmeta_doctrine_review_log.md (bot…
- **x-halfapplied**: READ: all 30 held commits origin/main..HEAD (7eaea97 tip), messages + key diffs for post-eb41794 commits (02cb688, 1c78a85, a3c4c51, 6adbf9f, 4f071df, c54215a, 8955974, b1e5b69, 98bff42, 35f603c, d77ad9e, 7eaea97). Records read: docs/r1_11_full_stack_audit.md (verdict, verification pass 1+2, interruption ledger, Step 0 map, fresh-audit findings A-01..A-30, fix-pass, disposition, carried-forward), docs/r1_11_fix_pass_findings.md (all 62 headers, R1-01..R1-16 full text, disposition footer), docs/zmeta_doctrine_review_log.md (all 21 entries + lifecycle), docs/zmeta_after_action_log.md (full), docs/zmeta_audit_playbook.md (full), docs/zmeta_refinement_handoff.md, docs/zmeta_refinement_worklog.m…


---

## Appendix — health-wave verifier register candidates (2026-07-27)

Banked by the fix wave's attackers and the independent completion verifier.
All below the fix floor or deferred with reason; none is silently dropped.
The wave itself is recorded in the worklog and CHANGELOG (commits
`25bb5fa`/`ede9bb6`/`dcabcc8`/`151adb6`).

- **VW-01 (MODERATE)** `gateway/src/validators.py:545,573` — `_parse_utc_z`
  parses gate-clean naive shapes without refusal; `_should_replace_timing_status`
  then raises TypeError on mixed naive/aware `_event_ts` values, and the
  freshness subtraction has the same arm. Function-level confirmed; full-loop
  reachability plausible (likely contained by the per-datagram last-resort
  except — crash becomes a dropped datagram). The same class the health wave
  closed in four adapters, at the kernel's own door. Candidate next wave.
- **VW-02 (MODERATE)** both SAPIENT egress modules — a non-dict `payload` or
  non-dict `event` block raises AttributeError past the documented contracts
  (the detection docstring promises "never raises"). Same shape as the fixed
  `target_geo` member, one level up.
- **VW-03 (MODERATE, deferred with reason)** — member-level restriction shapes
  fail open in `_normalized_uses`: `{"prohibited_uses": [("COALITION_EXPORT",)]}`
  or `[b"COALITION_EXPORT"]` coerce to never-matching tokens and export clean.
  Deliberately mirrored from `tools/filter_risk.py` `_list_values`, so the fix
  must move BOTH surfaces together (doctrine H1-06).
- **VW-04 (MINOR)** ingress templates (`cot`, `jreap`) `_compute_valid_for_ms`
  — mixed naive/aware start/stale raises TypeError.
- **VW-05 (MINOR)** vocabulary-lint blind spots — rebindings inside `if`/`try`
  bodies and tuple-target assignments are invisible to the top-level AST scan;
  an AugAssign followed by a clean literal rebinding over-refuses.
- **VW-06 (MINOR)** mavlink ingress — a message-carried non-string `link_id`
  is replaced by the adapter default identity (a carried identity dropped
  silently); a blank-string `reason_code` refuses as out-of-vocabulary instead
  of reading as absent, diverging from the blank-state rule four lines away.
- **VW-07 (OBSERVATION)** mavlink ingress — wrong-typed carried link
  measurements (`latency_ms='42'`/`True`) pass the None-only presence guard
  and emit schema-invalid for the gateway to refuse; TASK_ACK `task_id`/
  `original_event_id` emit verbatim (integer task_id → schema-invalid).
  Fail-closed downstream, but a loud ingress refusal would match the branch's
  own rule.
- **VW-08 (OBSERVATION)** mavlink egress pin pair cannot distinguish
  `is not None` gating from truthiness gating — a regression to `if priority:`
  would silently drop present-but-falsy priorities with both pins green.
- **VW-09 (OBSERVATION)** JREAP `_stale_time` int() coercion accepts bytes
  `valid_for_ms` (schema-blocked; embedder-reachable only).
- **CR-22 (MINOR, still open)** `release/sign_release_artifacts.py:27` — the
  A-23 guard's degraded-mode contract: tagless/shallow checkout yields
  `set()`, not None, silently treating a published version as unpublished.
  The CR-12 pin rework covers the test side; the tool-side contract remains.

Governed-wave (2026-07-27) attack residuals, banked the same way:

- **VW-10 (MINOR)** `zmeta_compact.decode_event` admits bytes values (the
  wire model needs them for UUID transport), so stray bytes in a non-UUID
  slot survive decode as Python bytes — refused later by any JSON
  serializer downstream (fail-closed, but far from the seam).
- **VW-11 (OBSERVATION, documented in spec)** on the interpreting cbor2
  fallback, a tag that collapses into an in-model value before the mapping
  can see it (tag 2 around a SMALL integer) is undetectable post-decode —
  stated as a residual in the new spec section rather than hidden.
- **VW-12 (OBSERVATION)** TIME_STATUS enum follow-ons: the vocabulary is a
  dual-dialect union (sync trio + link-style trio) — a future consolidation
  is a Class B candidate; `UNKNOWN` is excluded by the derivation rule while
  both status siblings include it; the mavlink `_TIME_STATUS_STATE_SYNONYMS`
  map's TARGETS are not lint-covered (the lint checks declared vocabularies).
- **VW-13 (OBSERVATION)** `decode_event` now refuses shared-but-acyclic
  PYTHON input from direct in-process callers (sharing is treated as the
  tag-28/29 footprint, which a tree decode cannot produce). Correct for
  every current caller; a future in-process caller passing a legitimately
  shared tree must deep-copy first.

Kernel-residuals wave (2026-07-27, post-v1.1.17) closures and residue:

- **VW-01 CLOSED** — the validators' naive-timestamp arm: `_parse_utc_z`
  refuses naive parses (its documented cannot-parse signal), `_format_utc_z`
  refuses naive datetimes, and — after the attack pass caught the first fix
  routing naive statuses into a silent fail-open arm — `record_timing` now
  refuses to record a TIME_STATUS whose own ts cannot be ordered, keeping
  the source on the existing loud MISSING disposition. This also closed the
  pre-existing arm where any gate-clean-but-unparseable recorded status made
  the freshness gate silently fail-open for that source.
- **VW-14 (MODERATE, banked)** — two siblings of the same shape remain: the
  EVENT-side ts arm still passes freshness silently (`(True, [])`) when the
  event's own ts is unparseable — a loud diagnostic wants a reason-code
  decision (R1-11-01 family, governed-adjacent); and schema strictness for
  `ts` is environment-dependent (jsonschema's `date-time` format is a no-op
  without the optional `rfc3339-validator` package — the same
  behavior-depends-on-installed-backend class as the cbor2 lesson). The
  candidate fix is the anchored RFC3339 pattern already in-repo as
  `zmeta_compact._UTC_TS_RE`, but tightening `utcDateTime` is a governed
  schema decision.
- **VW-15 (MODERATE, banked)** — H1-07 siblings: the `auto` and `compact`
  envelope branches still call bare `_decode_cbor` (no pre-decode depth
  bound on cbor2-only installs before the scan/decode_event run);
  resource-bound knobs (max_bytes/items) differ across backends inside the
  fixed seam; the zmeta_cbor-present/zmeta_compact-absent install combo
  shifts non-finite refusal downstream to semantics; and the repo now holds
  three inconsistent naive-datetime doctrines (validators refuse,
  `adapters/ingress/time_utils` stamps UTC, the compact encoder refuses) —
  unify deliberately in a scoped wave.

Command-loop pair (2026-07-27, post-v1.1.17) attack residuals:

- **VW-16 (OBSERVATION, documented in policy)** — command-evidence
  flood-eviction: under the reference `unresolved_parent_mode: warn`, an
  automation flooding >4096 distinct events can evict a command-prohibited
  parent from the bounded evidence index, downgrading its citation from
  REJECT to unresolved-WARN. Documented as the mode tradeoff in
  `policy/command-evidence.yaml`; strict deployments set `reject`.
- **VW-17 (banked wants, doctrine H1-08)** — wanted-but-not-minted reason
  codes for the two new refusal conditions (evidence-prohibited-for-command,
  evidence-required-but-absent), currently riding LINEAGE_MISMATCH /
  LINEAGE_PARENT_UNRESOLVED honestly; the TASK_ACK vocabulary cannot name an
  evidence refusal (rides the documented force_schema_violation shape); and
  `risk_dimension: lineage` reuse pending the R1-11-10 boundary question.
  Also: a command-evidence corpus example awaits the strict-warn
  representability decision (doctrine R1-11-14/19), and
  `policy/lineage.yaml` `allowed_parent_event_types` has no COMMAND_EVENT
  entry (the command-type check lives in command-evidence policy only).
