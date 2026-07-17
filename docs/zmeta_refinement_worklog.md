# ZMeta Refinement Worklog

## Current Resume Note

- Last updated: 2026-07-17
- Quick handoff: `docs/zmeta_refinement_handoff.md`
- Current state (2026-07-17): the R1-10 stack audit, the maintainer-
  directed fix-every-finding pass, the post-fix verification audit,
  AND the v1.1.14 release cut are COMPLETE (entries below; findings
  record in `docs/r1_10_full_stack_audit.md`). The cut resolved the
  previously recorded SHA256SUMS_v1.1.13 manifest-entry divergence
  (`SHA256SUMS_v1.1.14.txt` pins the regenerated manifest). Open
  maintainer decision: whether a fresh full-stack audit beyond the
  completed fix-verification audit runs before the queued backlog
  resumes. Queued behind that: the v1.1.0 adoption-decision session,
  the five deferred P1-06 maintainer decisions, PR #4 status, and
  signing. See the handoff Next Work Queue.
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
  context). Publication note: appended below after tag push, GitHub
  release creation, and CI confirmation.
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
