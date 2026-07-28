# R1-11 Full Stack Audit — 2026-07-21

Class: Docs/advisory (audit record). Non-normative. Audited tree: `main` at
`09118b3` (v1.1.16 + P1-09 residue). This document is the complete findings
record for the R1-11 stack audit; the worklog R1-11 entry summarizes it and
records the maintainer disposition.

## Method

- **Charter.** Maintainer decision 2026-07-21: a FULL fresh stack audit — not
  a scoped one — run safely in a fresh session before any queued backlog.
  Staged inputs (handoff Next Work Queue item 1): the R1-10 flagged residuals,
  the R1-10 second-glance register, the P1-07 second-glance additions, and the
  new-since-R1-10 surface (SAPIENT pack + v1.1.15 artifacts; P1-08
  edge-comms-bladerf pack + review fixes; the bearing_frame presence gap).
- **Lenses.** Seven independent finder passes: (1) SAPIENT pack code honesty
  (the largest new surface — build-verified and Apex-validated, but never
  audited by this process); (2) bladerf pack + external-fixture adversarial
  discipline + harness expressiveness (lane lesson: external fixtures need the
  same adversarial walk as code); (3) staged residuals + second-glance
  register status; (4) R1-10 fix regression + 2026-07-01 fielded-safety
  defect regression; (5) release/publication + governed-artifact integrity +
  commit-truth over 2a1e9ce..09118b3; (6) doc currency/retention + teaching
  surfaces; (7) fresh-eyes core sweep (encodings, gateway diagnostic
  coherence, checking-machinery vacuity siblings, policy lint, configs/CI).
- **Process.** Green baseline established first (full kernel gate, strict
  examples, full pytest, `git diff --check` — all clean). The seven finder
  passes ran independently, then **every substantive finding was
  adversarially verified by an independent skeptic pass instructed to refute
  it** — live probes through the real validator chain, evidence anchors
  re-read at HEAD, the governance record searched for documented deferrals.
  DOC/OBSERVATION items were batch-verified item-by-item (all held). A
  completeness critic then compared coverage against the charter; its two
  real gaps were closed by direct orchestrator probes (recorded below). In
  total: 7 finders, 16 adversarial verifiers, 1 batch checker, 1 dedup, 1
  critic. The audit was read-only: no repository file was modified; all probe
  artifacts were built outside the tree.
- **Baseline evidence.** `python tools/validate_conformance.py --strict
  --profile-projection --extension-registry --conformance-classes
  --encoding-negative --precision-policy --release-manifest --release-package
  --bad-events --adapter-harness` → `conformance ok` (projection 37, registry
  61, classes 34/claims 2, encoding 50, precision 32, bad-events 27, harness
  39). `python tools/validate_examples.py --strict --require-all` → 51/51.
  `python -m pytest -q` → **687 passed + 172 subtests, zero failures**.
  `git diff --check` clean, tree clean.

## Verdict

The kernel held, again: the locked v1.0 schema is byte-stable since v1.1.10
modulo the four sanctioned diagnostic enum additions, every R1-10 fix and
every 2026-07-01 fielded-safety fix re-verified by fresh probes (54
command-altitude probes, 36 STATE layer-collapse probes, 8 promotion-tamper
probes, full adapter refusal matrices — all still refuse), release integrity
for v1.1.15/v1.1.16 verified down to cryptographic asset digests, and —
unlike R1-10 — **every numeric claim in all ten commits of the stretch
reproduced exactly** (the commit-truth discipline is working).

The headline defect is new in kind: **the compact codec is an
honesty-destroying encoder on a live reference path** (R11-01, the cycle's
only MAJOR). It silently relabels v1.1.0 events as locked-v1.0 and destroys
the `geo.error_ellipse_m` uncertainty label, converting a would-be-loud
schema failure into a clean pass — a laundering bypass of the very gate the
default gateway enforces on the JSON path (witnessed live, both directions).
The remaining defect mass repeats two known patterns on new surfaces: R1-10
defect classes surviving as siblings where the fix was pinned to one exemplar
(the `str()`-coercion class on TaskAck, the self-asserted loop_status default
in three templates, harness vacuity shapes, currency pins that cover one line
of a document), and enforcement gaps arriving with new governed surfaces
faster than their negative machine coverage (the sapient-ingress policy
block, NaN confidence, fail-open egress risk sets).

Adversarial verification changed severity in only two of sixteen findings
(one upgrade, one same-severity reclassification; zero refuted, zero
downgraded) — versus seven of sixteen in R1-10. The difference: finder
prompts required refutation-first and governance-record consultation at find
time, so the false-alarm mass was removed before verification.

## Findings — MAJOR (verified by live probe, survived adversarial refutation)

| ID | Finding | Evidence anchors |
|----|---------|------------------|
| R11-01 | The compact codec silently rewrites `zmeta_version` to `"1.0"` (no wire key exists; decode unconditionally stamps it) and destroys `geo.error_ellipse_m` (GEO_KEYS copies only lat/lon/alt_m) — while its docstring claims "lossless" and `spec/profile-compatibility.md` guarantees "encoding choice does not change event semantics". 13/13 shipped v1.1 examples relabel on round-trip; 7/13 then validate CLEAN under the locked v1.0 label (the exact outcome AGENTS.md prohibits); the laundered STATE is byte-indistinguishable in validator output from the original. **Live-witnessed on the wire (orchestrator probes):** the default gateway (locked v1.0 schema, `gateway.py:1009`) correctly REFUSES the honest JSON 1.1.0 STATE (`SCHEMA_VIOLATION: error_ellipse_m unexpected`) yet ACCEPTS the identical event compact-encoded — forwarding clean `"1.0"` JSON, ellipse destroyed, zero diagnostics; a 1.1.0-enabled gateway (`--schema-path` umbrella) forwards the STATE but its compact egress (applied at `gateway.py:1860`, after egress validation) destroys ellipse+version on the wire un-rechecked. The destroyed field is load-bearing (CoT egress derives CE/LE from it). Verifier confirmed and strengthened: keeping the ellipse under the `"1.0"` label fails loudly, proving the field destruction is precisely what converts loud failure into clean pass. Contrast: zmeta_proto round-trips 51/51 examples byte-identically including version; compact CBOR is byte-faithful for the whole v1.0 surface (38/38). | `zmeta_compact.py:4-5,27-35,86-90,347,622-627`; `spec/profile-compatibility.md:16,24,37-38`; `spec/compact-binary-mapping.md:201`; `gateway/src/gateway.py:770-773,785-792,812-815,1009,1860`; `AGENTS.md:29-30`; `spec/semantics-contract.md` §3.4/§3.5 |

## Findings — MODERATE

| ID | Finding | Evidence anchors |
|----|---------|------------------|
| R11-02 | SAPIENT state egress fails OPEN on any `policy_decision` outside the exact governed set: refusal only for {QUARANTINE_ACCEPT, REJECTED}, self-label only for {WARN_ACCEPT, DEGRADED_ACCEPT}; any other decision (contract §3.3 explicitly permits local labels) exports a clean DetectionReport with the risk record vanished — while `tools/filter_risk.py` maps the same unknown decision to max rank and BLOCKS it. A locally-quarantined record the operator's own tooling stops is laundered clean to the coalition feed. Probed: `SITE_QUARANTINE` and `IGNORED` both exported with no self-label. | `adapters/egress/sapient/zmeta_state_to_sapient_detection.py:30-33,38,227-233,280-288`; `tools/filter_risk.py:7-13,142-143`; `spec/semantics-contract.md:301-308,332-335` |
| R11-03 | TaskAck egress fabricates the `original_event_id` correlation as the literal string `'None'` when the caller's task_index maps the task_id to a null value (guards key presence only, then `str()`-coerces) — the exact R1-10 A1 fabrication class on a new surface, contradicting the docstring/README "never fabricated" guarantee; schema-valid, passes the version-aware validate(). The colocated test covers only the key-absent case. | `adapters/ingress/sapient/sapient_to_zmeta.py:917-924,931,935`; `adapters/ingress/sapient/README.md:151`; `docs/r1_10_full_stack_audit.md:59` |
| R11-04 | NaN confidence from the SAPIENT wire is emitted as canonical confidence and vacuously passes validate(): `_is_number()` accepts `float('nan')`, and jsonschema min/max comparisons are no-ops against NaN (1.5/27/inf are all correctly rejected — the gap is NaN-specific). Same vacuity on the fusion-promotion STATE path. `json.dumps` then emits bare `NaN` (invalid RFC-8259): Python-tolerant consumers carry it silently, strict parsers reject the whole event. | `adapters/ingress/sapient/sapient_to_zmeta.py:112-113,465,612,635,651,693,1098-1120`; `spec/semantics-contract.md` §8.1 |
| R11-05 | The new sapient-ingress promotion policy block has zero negative machine coverage: `required` defaults to not-required in the validator, so deleting the sub-block, typoing its key, or flipping `required:false` silently disables SAPIENT external-state enforcement with every gate green (whole-entry deletion fails closed; sub-block mangling does not). Policy lint checks modes only; both bad-events external-state fixtures pin cot-ingress; the promotion pytest suite pins cot-ingress; the harness promotion expectation checks event shape, never policy. The cot-ingress fixture convention existed and was not extended to the new governed block. Probed: three mangle variants, all silent-pass. | `policy/producer-authority.yaml:297-309`; `gateway/src/validators.py:532-533,754-755,1225-1251`; `tools/validate_adapter_conformance.py:195-202`; `conformance/bad-events/must-fail.jsonl`; `gateway/tests/test_external_promotion.py:46,179` |
| R11-06 | signalhunter consumes a GPS no-lock `(0,0)` .bin header position as a real fix: a no-lock header followed by a mid-file lock yields a canonical `bearing.az_deg` computed as the geodesic from null island to the first real fix (probe: az 307.49°, displacement 12,574 km), asserted `TRUE_NORTH`/`GPS_COURSE`, passing schema + semantics + strict-H with zero warnings (the zero-fill warn covers only `payload.geo`/`claim.geo`; this event carries no geo). **Worse than the recorded residual**, which scoped the exposure to `sensor_position_2d` pass-through. Contract §6.8's sentinel rule violated in reverse: the sentinel treated as valid evidence OF position. | `adapters/ingress/signalhunter/signalhunter_to_zmeta.py:76-88,272-273,314-331,352,376-383`; `gateway/src/validators.py:1653-1673`; `spec/semantics-contract.md:922-923`; `adapters/AUTHORING.md:95-97,132-135` |
| R11-07 | The self-asserted promotion `loop_status: CHECKED_NOT_REFLECTION` default — the pattern the P1-07 SAPIENT honesty fix removed and the ratified doctrine calls "never self-asserted" — exists in THREE ingress templates (cot:92, jreap:84, mavlink:201); the register records only cot. Each stamps the reflection-check verdict precisely when no check occurred; none of the three documents the conditionality. The three must-pass harness fixtures pass messages WITHOUT loop_status while requiring the key with no value pin — the kernel gate's 39/39 green machine-blesses the fabricated default. | `adapters/ingress/cot/cot_to_zmeta_template.py:92`; `adapters/ingress/jreap/jreap_track_to_zmeta_template.py:84`; `adapters/ingress/mavlink/mavlink_to_zmeta_template.py:201`; `conformance/adapter-harness/must-pass.jsonl:8-10`; `spec/semantics-contract.md:540-543,556-558`; `CHANGELOG.md:62` |
| R11-08 | Harness vacuous pass, `events`-kind sibling of the fixed A7: a `result:"events"` fixture with rich expectations but no `event_count` and no `expect.events` passes with ALL expectations unevaluated when the adapter returns `[]` (implicit count applies to the single-event kind only; the schema requires `event_count` only via the `events`-key dependent trigger). Probed: refusal-triggering fixture with four expectation families → PASS, exit 0, lints clean. Defeats the harness README's own "rather than pass vacuously" guarantee for exactly the external-fixture-author population. | `tools/validate_adapter_conformance.py:304-309,311-318,330-337`; `conformance/adapter-harness/fixture.schema.json:49-60`; `conformance/adapter-harness/README.md:33-51` |
| R11-09 | The shipped harness corpus is never lint-gated: unknown expect keys are silent no-ops (dict `.get()` reads), and the `fixture.schema.json` lint that catches them runs only on the author-opt-in `check_adapter` path — not in the kernel gate, not in CI, not in pytest. Probed: `forbidden_paths` typoed to `forbidden_path` naming a present path → full gate green; the correctly-spelled key fails the fixture, so the typo converts an intended prohibition into a no-op. All 39 shipped fixtures lint clean today; the exposure is governed edits (12 sapient fixtures entered this cycle; bladeRF fixtures are queued). | `tools/validate_adapter_conformance.py:220-262`; `tools/validate_conformance.py:317-329`; `gateway/tests/test_fixture_schema_sync.py:32-58`; `conformance/adapter-harness/README.md:19-22` |
| R11-10 | Every published formal-release manifest v1.1.13→v1.1.16 carries placeholder provenance (`git_commit: explicit_release_input_required`) and the builder's unconditional note "Reference hardening-baseline manifest, not a formal tagged release" directly alongside `release_status: formal_release` — contrary to the release-hash-policy MUST ("Formal release generation must pass explicit --git-commit…"), with zero enforcement (validator passes the placeholder clean; the release package inherits it). The placeholder DEFAULT is governed (S1-09C), but that decision is scoped to committed reference manifests and reasserts the formal-release MUST it is now violating. | `spec/release-hash-policy.md:166-173`; `release/zmeta-release-manifest.yaml:4,465,469-470`; `tools/build_release_manifest.py:20,370-376,456`; `tools/build_release_package.py:206-207`; `release/VALIDATION_REPORT_v1.1.15.md:30`; `release/VALIDATION_REPORT_v1.1.16.md:31` |
| R11-11 | The professional overview body still instructs adopters to "Pin to a release, currently v1.1.9 for the formal baseline" (and "ZMeta v1.1.9 intentionally does not claim everything") — 7 releases stale, pre-dating the v1.1.10 fielded-safety enforcement — while the machine-pinned header says v1.1.16. Survived the R1-10 dedicated doc sweep and four release doc-currency passes because both the checklist item and `test_release_currency` pin only the header line. A teaching-surface instruction steering new deployments onto a pre-safety-hardening tag. | `docs/zmeta_professional_overview.md:4,911,943`; `gateway/tests/test_release_currency.py:58-59`; `RELEASE_CHECKLIST.md:36-51` |
| R11-14 | Every published manifest since 2026-07-08 asserts "D-003 OPEN" although the register closed D-003 by maintainer decision on 2026-07-08 (`known_open_issues` is hardcoded in the manifest builder). **Upgraded MINOR→MODERATE by verification:** the same hardcoded string also ships via the release-package builder into `ATTESTATION_TEMPLATE.yaml`, every per-release package attestation, and each packaged RELEASE_NOTES "Known Open Issues" section — four post-closure releases publish a false register status in multiple governed, hash-pinned artifacts. | `tools/build_release_manifest.py:380-382`; `release/zmeta-release-manifest.yaml:474-475`; `tools/build_release_package.py:128-133`; `release/ATTESTATION_TEMPLATE.yaml:31-32`; `docs/zmeta_refinement_worklog.md:725-728,928-960` |

## Findings — MINOR

| ID | Finding | Disposition context |
|----|---------|---------------------|
| R11-12 | Fusion promotion blind-merges all caller promotion keys into `external_promotion` (`promotion_meta.update(...)`), admitting raw-feature injection (`signal_snapshot`) contra contract §4.5.1/§7.7, and the docstring's "mirrors the CoT template contract" overstates (the CoT template builds from a fixed key set). **Reclassified by verification (same severity):** the finder's authority-claim half was wrong — the gateway external-promotion policy DOES backstop `state_category` at Profile H; the surviving defect is the unenumerated-key/raw-feature injection surface plus the misdescription, with the gateway backstop bounding the exposure. The caller-supplied-promotion design itself is documented (P1-07). | `adapters/ingress/sapient/sapient_to_zmeta.py:702-703,715`; `adapters/ingress/cot/cot_to_zmeta_template.py:84-101`; `gateway/src/validators.py:808-948`; `spec/semantics-contract.md:559-560` |
| R11-13 | The v1.1 teaching corpus carries the stack's only two unlabeled canonical bearings (repo-wide scan: exactly 2 hits, both `examples/zmeta-v1.1-examples.jsonl` lines 3/5), violating the contract §6.4 SHOULD the corpus exists to model; line 5 even names producer `kraken-sdr`, whose reference adapter always stamps frame provenance. No examples corpus demonstrates `bearing.frame` or `quality.bearing_frame` at all. These two lines are also the complete would-warn set for the R11-21 warn-check candidate. | `examples/zmeta-v1.1-examples.jsonl:3,5`; `spec/semantics-contract.md:867-888` |
| R11-15 | The handoff regressed to multi-generation version self-contradiction within two cycles of the R1-10 fix of the same class: header v1.1.14; "Use tag v1.1.15" (the only line P1-07 bumped); release-target section v1.1.14/"previous v1.1.13"; Verification State pinned at the v1.1.13 record. The v1.1.16 release commit never touched the file despite the RELEASE_CHECKLIST item naming it. The currency test's deliberate handoff exclusion covers rolling-narrative text, not the current-release pointers readers are routed to. | `docs/zmeta_refinement_handoff.md:3-5,186-187,231-241,308,335-336,711-721`; `RELEASE_CHECKLIST.md:35` |
| R11-16 | P1-09 regenerated the in-repo manifest under the v1.1.16 identity without the explicit published-checksum divergence record the R1-10 precedent established (probed: HEAD manifest hash ≠ the immutable `SHA256SUMS_v1.1.16.txt` pin; the release notes' own documented verification command now exits 1 on main with no governance line explaining it). AGENTS.md pre-adjudicates that main may lawfully diverge from published pins; the missing piece is the explicit record. | `docs/zmeta_refinement_worklog.md:68-69,407-411`; `release/SHA256SUMS_v1.1.16.txt:1`; `AGENTS.md:130-132` |

## Findings — DOC (all directly verified)

- R11-17 — `spec/installation-guide.md:222` worked command still pins
  `--version 1.1.11` while adjacent lines 221/223/224 were updated to v1.1.16
  in the same passes; last touched at the v1.1.11 cut; the currency test
  checks only the guide's baseline line.
- R11-18 — `README.md:463-465` bundle-builder examples pinned at v1.1.13 for
  three consecutive releases while sibling line 462 is bumped every cycle;
  outside both the checklist enumeration and the machine pin.
- R11-19 — `adapters/AUTHORING.md` pre-dates both new mapping packs (zero
  references to sapient/bladerf/registration) and teaches none of the
  patterns they introduced: registration-store units codex,
  refuse-when-unregistered, caller-owned promotion metadata (the ratified
  P1-07 doctrine — the guide still routes authors to the CoT template that
  self-asserts it, per R11-07), split fact/opinion reports, the second
  documented bandwidth-sentinel flavor (FFT-bin-width), and the harness
  JSON-only kwargs limit. The packs follow the guide; the guide no longer
  covers the packs.

## Second-glance register (OBSERVATION; below the findings bar)

- R11-20 — SAPIENT egress projection functions raise
  (`ValueError`/`TypeError`) on malformed ts / non-numeric numerics instead
  of the documented return-None refusal (only the altitude tripwire is a
  documented deliberate raise). Exposure bounded: egress consumes
  schema-valid gateway events.
- R11-21 — STATUS-CONFIRM + characterization of the recorded warn-check
  candidate: canonical bearing with no frame provenance passes every machine
  gate at HEAD (`validators.py:1622` fires only on key presence). Achievable
  shape: a version-aware WARN mirroring the zero-fill heuristic directly
  below it — v1.0 warn on `payload.bearing.az_deg` without
  `quality.bearing_frame` (§6.4 tolerates legacy-unlabeled, so warn is the
  ceiling); v1.1.0 warn on `bearing.frame` absent (direct SHOULD). Corpus
  impact: exactly the two R11-13 events. Implementation trap: the new warn
  code must enter BOTH schema `reason_code` enums (the R1-10
  GEO_ZERO_FILL_SUSPECTED lesson).
- R11-22 — STATUS-CONFIRM of the governed P1-07 accepted deviation:
  registration-dependent sapient harness fixtures remain structurally
  inexpressible (probed: a JSON-dict registration kwarg fails loud with
  `ADAPTER_CALL_FAILED`, not a silent pass); coverage lives in the colocated
  tests; the module-level entry point remains queued (handoff item 1a).
- R11-23 — Second-glance candidate: the locked schema requires
  `last_sync_ts` even for never-synced clocks; the reference convention
  (`time_utils.coerce_timing_quality`) stamps event ts, faithfully mirrored
  by the bladerf fixtures. The honest-reading rule — `last_sync_ts` is
  meaningful only when `sync_state != UNSYNCED` — is currently stated
  nowhere. Not fixable without touching the locked schema; a contract/README
  advisory line is the outer-ring shape.
- R11-24 — **Maintainer-attention inventory (not a defect)**, per the P1-08
  disclosure note: the edge-comms-bladerf pack publishes (1) the internal
  archive name with project prefix (`Z-ISR flight-artifacts-2026-05-14_...`,
  pack README:11); (2) the internal recording path with flight date +
  per-second timestamps (README:12); (3) platform identity
  `uav-believer-01-bladerf` (README:67 + both fixtures); (4) sensor identity
  `bladerf_ew`; (5) detection frequencies with millisecond UTC timestamps
  (138.2 MHz @ 14:12:33.876Z; 5.2475 GHz @ 14:12:34.404Z) + native ids
  embedding epoch-ms and frequency. NOT disclosed: coordinates (correctly
  refused), operator identities, mission context. Softer echoes propagate to
  CHANGELOG, v1.1.16 release notes, mapping-packs README, pack.json, and
  README.md. Scrub caveat: all of it is already in git history and in the
  published v1.1.16 assets — scrubbing main would not retract publication.
- R11-25 — Small teaching-surface residues: `adapters/README.md:114` copy-me
  block pins `--target v1.1.8` (functional, eight releases aged); the worklog
  resume-note top bullet was not refreshed by P1-09; `mapping-packs/README`
  never names the sapient pack and its contents list marks `enums.yaml`
  optional but not `units.yaml`; the adapters/README ingress-table Status
  vocabulary gained an unlegended fourth value ("Reference").

## Completeness critic — gaps and closures

- **B3 regression orphan** (no lens dispositioned the R1-10 checksum-depth
  fix): closed by orchestrator probe — the fix is machine-pinned by a
  12-test family including `test_verify_checksums_rejects_empty_checksum_file`,
  `..._rejects_partial_coverage`, `test_package_checksums_reject_empty_file`,
  and `..._require_coverage_of_artifact_list`, all passing at HEAD. B3 HOLDS.
- **R11-01 "live" wording** (finder probes were codec/CLI-level): closed by
  orchestrator live-gateway probes — three legs witnessed at process level
  over UDP (default-gateway refusal of honest JSON 1.1.0; default-gateway
  acceptance + laundering of the same event compact-encoded; 1.1.0-enabled
  gateway compact-egress destruction after validation). LIVE CONFIRMED, and
  the probe surfaced the sharper gate-bypass asymmetry recorded in R11-01.
- Third critic item (no evidence of an independent refutation pass) was a
  sequencing artifact: the verification stage ran after the coverage
  statements were written; 16 adversarial verifiers executed.

## Refuted / not defects

- Zero findings were refuted outright this cycle (see Verdict for why the
  false-alarm mass was low). One exposure framing was corrected: R11-12's
  authority-claim half (the gateway DOES backstop `state_category`); the
  finding survives on its raw-feature-injection half at the same severity.
- The default gateway's refusal of JSON v1.1.0 events (surfaced by the
  R11-01 live probes) is not a defect: the locked-v1.0 default schema is
  deliberate; it is what makes the compact bypass a gate bypass.
- `.tmp/review-pr-2` worktree: leaks into no gate (manifest 0 `.tmp` entries,
  bundle sources explicit, pytest excludes, gitignored). Keep-or-prune
  remains a maintainer call, unchanged.
- Published-checksum immutability: zero modifications to any
  `SHA256SUMS_*.txt` since 2026-07-16 (git history probe) — the un-pinned
  surface has not been exploited (the pytest pin remains a candidate).

## Positive assurance (witnessed, not assumed)

- **R1-10 fix regression: 100% hold.** A1-A4 adapter/CoT honesty (38/38
  example-vendor probes; eo-cv null-confidence refusal without the pre-fix
  crash; kraken/moth no-default refusals; CoT 9999999.0 conventions,
  wall-clock off, missing-ts refusal), A5 bearing-frame enforcement at both
  layers (MAGNETIC rejected, live CLI witnessed), A6 strip guard
  (segment-wise, lookalike sibling allowed, config load fails fast, ordering
  strip→egress-validation correct), A7 single-event vacuity guards, B1
  recursion denylist, B2 empty-input floors (six tools fail closed), B3
  checksum floors, B4 zero-fill warn end-to-end including its own diagnostic
  validating against the locked schema.
- **2026-07-01 fielded-safety regression: 100% hold.** 54/54
  command-altitude spellings×shapes rejected; 36/36 STATE layer-collapse
  probes rejected; 8/8 promotion evidence-tamper variants rejected with the
  intact baseline accepted; calibration defaults UNCALIBRATED everywhere.
- **Release integrity, cryptographically witnessed:** all 16 v1.1.15+v1.1.16
  GH asset digests match the in-repo SHA256SUMS lines exactly; both SUMS
  files written once at their release commits, never modified; v1.1.16
  marked Latest, 8 assets each, CI green on every push head and both tag
  refs; claims/contract-hash sync non-vacuous (tampered claim fails,
  witnessed); locked v1.0 schema diff v1.1.10..HEAD = exactly the four
  sanctioned enum additions.
- **Commit-truth: every checkable numeric claim in all ten commits
  reproduced** (fixture counts, test counts, manifest group/artifact counts,
  release-notes numerics re-run live: compat 9/9, packet-size max 150/240,
  presets 6, roadmap candidates 18).
- **Codec contrast surfaces:** zmeta_proto 51/51 byte-identical round-trips
  preserving version; compact CBOR byte-faithful across the whole v1.0
  surface including adversarial unicode/extension/numeric probes; the
  33-code diagnostic emission set is enum-complete in all four registries
  (programmatic set-difference empty — no GEO_ZERO_FILL siblings).
- **SAPIENT pack honesty spine held under 20+ adversarial probes:** egress
  quarantine/prohibited-use refusals real; ULID minting event-ts-derived
  (never wall clock), range-checked; envelope identity/ts refusals fail
  closed; RegistrationStore conflict-poisoning conservative; fusion
  promotion gate refuses on every missing leg; geo all-or-nothing both
  directions; command egress altitude exclusion holds at depth including
  extension-key leak probes; bearing frame provenance honest
  (native-features for non-TRUE frames); amplitude/units discipline refuses
  mislabeled RF.
- **bladerf pack (external corpus) walked field-by-field:** every expected
  value traces to input or documented convention; review fixes
  self-consistent (zero canonical-bearing/1_SIGMA remnants); both fixtures
  pass strict H; geo refusal honest including zero-island; producer matches
  the committed authority pattern.
- Zero pytest skip/xfail markers in gateway/tests; working tree byte-clean
  after every lens pass (read-only compliance verified).

## Maintainer disposition (2026-07-21)

Recorded direction: **fix the findings and work down the list.** The R11-24
bladerf disclosure inventory is cleared as-is ("the bladerf stuff is good" —
no scrubbing). The fix pass runs in dependency-ordered waves with disjoint
file ownership and a full-gate commit at each boundary (the R1-10 pattern):
(1) R11-01 compact fail-closed (encoder refusal + gateway ENCODING_UNSUPPORTED
diagnostic + spec scope, incl. the sanctioned Class B diagnostic-code
addition to both schema enums); (2) SAPIENT adapter honesty (R11-02, -03,
-04, -12, -20); (3) signalhunter no-lock + the three-template loop_status
defaults (R11-06, -07); (4) checking machinery (R11-05, -08, -09 + the
SHA256SUMS immutability pytest pin); (5) machine-encoded semantics (R11-13
example fixes, then the R11-21 bearing-frame warn-check + non-finite
confidence check — second Class B code batch); (6) release machinery
(R11-10, -14, -16); (7) doc currency + teaching surfaces (R11-11, -15, -17,
-18, -19, -23 advisory, -25); (8) governed regeneration, post-fix
verification audit, release-cut decision. R11-22 stands as the governed
deferral (registration entry point stays queued, handoff item 1a). The
worklog fix-pass entries record execution.

## Cycle outcome (2026-07-21)

The disposition was executed in full: seven dependency-ordered waves,
committed at wave boundaries with the full kernel gate, strict examples,
and full pytest green at every boundary (`74d92e1` compact fail-closed;
`88b527e` SAPIENT honesty; `e3203ad` signalhunter/templates; `545fe0b`
checking machinery; `c1eb9d0` semantics + Class B warn batch; `33230af`
release machinery; `05ad9a8` doc currency/teaching). Findings closed:
R11-01 through R11-21 and R11-23/R11-25 (R11-22 governed deferral;
R11-24 cleared by the maintainer). Three discoveries made DURING the fix
pass, each pinned by test: the audit's NaN probes had not reached the
`native_classification` verbatim block (the wave-2 test caught NaN
surviving there and poisoning RFC-8259 serialization of the whole event);
`validate_release_package` machine-enforced the stale "D-003 OPEN" claim
("known_open_issues must include D-003"), the root cause of R11-14's
four-release survival; and the compact self-check surfaced the honest
`.000Z` timestamp-normalization refusal case. Enforcement growth across
the cycle: pytest 687+172 → 742+237, bad-events 27 → 29, adapter harness
39 → 40 (now self-linted in the gate), four governed diagnostic codes
(ENCODING_UNSUPPORTED, BEARING_FRAME_UNLABELED, NON_FINITE_CONFIDENCE,
POLICY_PRODUCER_AUTHORITY_STRUCTURE — the last policy-lint-side only),
two validator formal-status codes, and currency pins over the body/
worked-command surfaces that had escaped one-line pins. Per the AGENTS.md
divergence rule this pass added: the fix-pass regens leave current main
diverged from the published v1.1.16 SHA256SUMS manifest/package pins
(published checksums immutable; resolution is the next release cut). The
post-fix verification audit and the release-cut decision follow; its
outcome is recorded in the worklog.

## Post-fix verification pass 1 (2026-07-21, `d955cd0`)

The R1-10 lesson held again: **the fix pass is itself an audit surface.**
Verification found three defects that wave 1 introduced or caused, all
reproduced before fixing and all pinned by test.

- **V1-01 (MAJOR, crash — introduced by the fix).** The wave-1 recovery
  path wrapped only the FIRST `_encode_message`; the re-encode of the
  `ENCODING_UNSUPPORTED` diagnostic was unguarded. The diagnostic copies
  the original's `event_id` into `metrics.original_event_id`, so when the
  unrepresentable value IS the `event_id`, the diagnostic inherits the
  defect and the second encode raises. `main()` caught only
  `KeyboardInterrupt`, so one packet could terminate a compact-output
  gateway for every producer behind it. Fixed by
  `_encode_outgoing_or_diagnostic`, a fallback ladder ending at the
  documented `UNKNOWN` correlation sentinel (no caller-controlled
  content), then a recorded drop. Proven live.
- **V1-02 (MODERATE, laundering — introduced by the fix).**
  `verify_representable` compared `decode_event(encode_event(event))`, an
  in-memory key remap that PRESERVES OBJECT IDENTITY. Python container
  equality short-circuits on identity, so a value not equal to itself
  (NaN) passed verification and the wire carried a payload with no
  canonical JSON form (RFC 8259). Verification now runs through the real
  serialization boundary (encode to bytes → decode → compare); non-finite
  floats refuse by name.
- **V1-03 (MODERATE, over-refusal — caused by the fix).** The byte-wise
  comparison refused SCHEMA-VALID events: the `uuid` pattern admits
  uppercase hex and `utcDateTime` admits fractional seconds. Both
  `edge-comms-bladeRF` real-capture fixtures — this repo's own v1.1.16
  corpus — were refused by compact egress because `.876Z` decodes as
  `.876000Z`, the same instant. Wave 1's tests used only whole-second
  timestamps, so nothing caught it. The comparison now recognizes exactly
  the two normalizations the mapping declares (UUID hex case per RFC 4122;
  timestamp formatting at the declared millisecond resolution) and nothing
  more. One wave-1 assertion deliberately flipped: `.000Z` was pinned as a
  refusal and is now a declared normalization, with the sub-millisecond
  case replacing it as the honest refusal pin.

## Post-fix verification pass 2 (2026-07-22)

A full seven-slice verification audit over the fixed stack (24 agents,
every finding adversarially refuted before acceptance) opened the pass;
a second nine-lens sweep over the resulting fixes (85 agents, every
finding adversarially refuted before acceptance; 29 survived, 46 were
refuted) plus direct probing of each new guard extended it. Fourteen
findings closed: **2 MAJOR** (V2-01, a process-killing crash class;
V2-09, a cross-backend laundering/interop hole), **7 MODERATE**, and
**5 MINOR**. Note that a *second* crash class, V2-02, sits at MODERATE —
the cycle-level "two MAJOR crash classes" counts V2-01 alongside
pass 1's V1-01, not V2-02.

**Most of these were found by attacking the fixes, not the original
code.** A structural pin caught a sixth vendor-block sink the audit's
own "five ingress paths" framing had missed (V2-03). Stress-testing the
new promotion lint caught it repeating the very blind spot it was
written to close (V2-04). The replacement currency guard was found
broken against the exact regression shape it targeted (V2-07). And the
pass-1 crash fix's own docstring claim turned out to be false on the
non-reference CBOR backend, which exposed V2-09 — the most serious
finding in the cycle, because the round-trip self-check is
backend-symmetric and structurally cannot see a divergence that only
manifests on the *receiving* node.

The lesson generalizes past "verify after fixing": **a new guard is
itself unreviewed code, and a self-check that uses the same machinery
on both sides cannot detect a defect in that machinery.** Write the pin,
then attack the pin — and ask what the check is blind to by
construction.

- **V2-01 (MAJOR, crash — partially introduced by the pass-1 fix).** The
  recovery ladder catches exactly `CompactUnrepresentableError`, but the
  codec itself can raise on SCHEMA-VALID input: `OverflowError` for an
  integer ≥ 2**64 (no CBOR unsigned major type without bignum tags),
  `ValueError` for extension nesting past the CBOR decode depth (a
  conforming compact CONSUMER could not decode it either), and
  `OSError`/`RecursionError` at the edges. Each escaped the ladder and
  terminated the process; the nesting path was added by pass 1's real
  serialization decode. Fixed at two layers: the codec converts its own
  encode/decode failures into `CompactUnrepresentableError`, so they
  become honest `ENCODING_UNSUPPORTED` diagnostics; and the receive loop
  gained a last-resort per-datagram backstop that records a drop and keeps
  serving. **The backstop is deliberately scoped, and the scope is
  pinned by test:** `recvfrom` stays OUTSIDE it (a dead listener socket
  must still terminate, not hot-loop), and `except Exception` does not
  catch `BaseException` — operator interrupts and the `SystemExit` that
  `_require_cbor`/`_require_compact`/`_require_proto` raise for an
  unusable configuration still stop the process rather than degrading
  into an infinite drop loop. Resilience must not become concealment.
- **V2-02 (MODERATE, crash).** `_find_forbidden_key` recursed, tying the
  process stack to sender-controlled nesting depth: deeply nested but
  schema-valid JSON killed the gateway at INGRESS, before egress, on any
  encoding. Now an iterative breadth-first traversal (`deque`); the
  shallowest forbidden key is still reported first.
- **V2-03 (MODERATE, laundering).** The R11-04 non-finite drop ran on only
  1 of 5 SAPIENT ingress paths, so NaN still rode a verbatim vendor block
  onto a non-RFC-8259 wire from status, alert, task_ack, and error.
  Applied on every path — and then a structural pin written to stop the
  guard drifting found that **"five ingress paths" was itself
  undercounted: there are six vendor-block sinks.** The PLATFORM_STATUS
  event passes the raw SAPIENT `power` block through verbatim, so a
  non-finite field inside it (e.g. `voltage`) reached the wire even
  though the canonical `battery_pct` derived from the same block was
  `_is_number`-guarded. The audit's own framing had missed it; the test
  caught it. All six sinks now apply the guard **at the point of use**
  rather than once earlier in the function — the detection path
  previously dropped first and then assigned `vendor_ext["colour"]`,
  which was safe only because that value is string-guarded, and which
  any later mutation would have silently defeated. The point-of-use
  invariant is pinned by a source-level test.
  **Fixing this also surfaced a second hole in the same helper** (the
  R11-04 → wave-2 → here pattern, three cycles deep now):
  dropping a bare non-finite LIST ELEMENT silently re-indexed positional
  numeric arrays, so `[1.0, NaN, 3.0]` would arrive as a clean
  two-element array indistinguishable from a genuine one. A non-finite
  element now drops the containing key — an absent key is honestly
  absent, a silently shortened array is not. Lists of objects are
  unaffected (every element preserved and cleaned in place, no index
  moves). Not reachable with any current SAPIENT fixture or proto field;
  closed as a latent hazard because vendor blocks are verbatim
  pass-through and the next vendor is unknown.
- **V2-04 (MODERATE, enforcement).** The R11-05 structural lint covered
  only per-producer promotion rules, not the GLOBAL
  `external_state_promotion` block where most enforcement keys live — a
  typo there silently reverted that gate to its `.get()` default while
  both lints stayed green, the exact R11-05 failure mode one block over.
  The lint now covers the global block and its
  `degrade`/`quarantine`/`use_limits` sub-blocks. It additionally flags
  per-producer overrides of global-only keys as the silent no-ops they
  are: `_PROMOTION_RULE_KEYS` was narrowed to exactly the six keys
  enforcement reads per rule (`required`, `mode`, `mode_by_profile`,
  `approved_policy_ids`, `allowed_projection_ids`,
  `allowed_confidence_basis`), verified against
  `_external_promotion_rules` / `_promotion_mode` / `_union_rule_values`.
  An operator writing `always_reject_loop_risk: false` on a producer was
  changing nothing and the lint blessed it. **Stress-testing the new lint
  against malformed shapes then caught it committing the same sin:** it
  skipped `degrade`/`quarantine`/`use_limits` sub-blocks that were
  present but of the wrong TYPE, and a non-mapping there is read with
  `.get()` and silently reverts the action to its built-in default —
  exactly the blind spot the lint exists to close. Mistyped sub-blocks
  now fail; absence stays legal.
- **V2-05 (MINOR, over-refusal).** Compact epoch-ms conversion routed
  through float seconds: `int(dt.timestamp() * 1000)` landed one
  millisecond off for a date-banded fraction of schema-valid timestamps
  (480 of 8000 in the sweep), so the round-trip check refused honest
  events; out-of-range instants raised `OSError` on Windows instead of
  refusing. Now exact `timedelta` integer arithmetic, pinned by a sweep
  across four date bands including pre-1970.
- **V2-06 (MINOR, honesty).** A non-string `ts` raised `AttributeError`
  past the documented `None`-refusal contract in both SAPIENT egress
  adapters (R11-20 residue). Separately, `record_drop("encoding_unsupported")`
  was the only lowercase entry in an otherwise `SCREAMING_SNAKE`
  `drop_reasons` vocabulary — `drop_reasons` keys are the operator's
  filter surface, so one outlier hides that bucket. Both fixed; the
  vocabulary is now pinned by a source-level test.
- **V2-07 (MINOR, checking machinery).** The overview currency guard was
  phrasing-specific: it matched the single literal `currently vX.Y.Z`, so
  the reworded-but-equally-stale forms (`as of today, v1.1.9`, `pin to
  release v1.1.14`, `we are on v1.1.15`) passed it clean — a guard that
  catches only the sentence the last regression happened to use. Replaced
  with a phrasing-independent check: the overview body may name the
  current release and the semantic branches, never a superseded published
  release (derived from `release/RELEASE_NOTES_v*.md`, with `v1.1.0`
  excluded because it is both a release tag and the experimental schema
  branch). **The first cut of the replacement was itself wrong** — its
  lookahead `(?![\d.])`, written to stop `v1.1.1` matching inside
  `v1.1.16`, also rejected any version ending a sentence, which is
  precisely the `...currently v1.1.9.` shape it existed to catch. The
  matcher now carries its own both-directions self-test.
- **V2-08 (MINOR, release machinery).** `release/RELEASE_NOTES_TEMPLATE.md`
  still shipped the retired "D-003 remains roadmap-planned" line into
  every packaged release note, four releases after the maintainers closed
  D-003 at the v1.1.12 cut. R11-14 fixed the *validator* that
  machine-enforced the claim but not the *template* that emitted it — the
  same claim had two producers. The section now instructs authors to read
  the register rather than carry a previous release's list forward.

- **V2-09 (MAJOR, laundering / interop).** Compact representability depended
  on **which CBOR library happened to be installed.** The mapping's integer
  limit was left to the backend, and the two supported backends disagree:
  `zmeta_cbor` refuses an integer outside `[-(2**64), 2**64-1]` (correct —
  CBOR major types 0/1 cannot carry it and this mapping defines no bignum
  tag), while `cbor2` silently encodes it as a bignum tag — **which a
  `zmeta_cbor` consumer then decodes as raw BYTES, not an integer.** Two
  conforming ZMeta nodes would disagree about what the same event means
  based on a local install detail, which is precisely the interoperability
  failure this format exists to prevent. The round-trip self-check could not
  see it because verification is backend-symmetric: the same library encodes
  and decodes, so the corruption only appears on the *other* node. The codec
  now enforces the range itself, before encoding, identically on every
  backend; the boundary is pinned exactly (`2**64-1` and `-(2**64)` still
  encode) and both regression tests run against both backends.
- **V2-10 (MODERATE, honesty).** `_same_instant` compared two values that had
  already been truncated identically — `datetime.fromisoformat` cuts at
  microseconds — so it could not see loss below that. A 100-nanosecond
  instant (`.8760001Z`) compared equal to its millisecond round-trip, and the
  codec silently dropped precision while its own docstring claimed "a
  truncated sub-millisecond instant is a different instant and is refused."
  The original's resolution is now checked directly, with `.876000Z`
  (millisecond written long-hand) still accepted.
- **V2-11 (MINOR, crash).** `_format_ts` is reached from the PUBLIC decode
  path (`loads`/`decode_event`) on a sender-controlled epoch-ms value, which
  sits outside the encode-side guard, so a hostile wire value crashed the
  consumer with a raw `OverflowError`. Decode now fails closed like every
  other invalid compact input.
- **V2-12 (MODERATE, checking machinery).** Four docs carry the identical
  machine-pinned `Current release context: ZMeta <version>.` header, but only
  the overview was guarded — **the other three sat five releases stale**
  (v1.1.11 at a v1.1.16 baseline). A guard that covers one member of a family
  does not protect the family. All four are pinned now, plus a test asserting
  the pinned list still names every doc carrying the header, so a new one
  cannot silently escape.
- **V2-13 (MODERATE, release machinery).** `build_release_package.py` copied
  `RELEASE_NOTES_TEMPLATE.md` verbatim into the package as its
  `RELEASE_NOTES.md`, and nothing read that file's content. So the published
  v1.1.16 package ships notes titled "ZMeta Release Notes Template", every
  provenance field the literal `explicit_release_input_required`, closing
  with "This template is an example" — beside metadata declaring
  `release_state: formal_release`. The real notes exist as
  `release/RELEASE_NOTES_v1.1.16.md` and never entered the package; four
  releases shipped this way. This is the R11-10 self-describes-as-non-formal
  shape one artifact over, and it is the channel the V2-08 template fix flows
  into. The builder gained `--release-notes`, the validator gained
  `RELEASE_PACKAGE_NOTES_PLACEHOLDER` (fails only for `formal_release` — a
  release candidate may legitimately still carry the template), and
  RELEASE_CHECKLIST gained the step. Published checksums are untouched; the
  fix takes effect at the next cut.
- **V2-14 (MODERATE, doc currency).** `spec/release-signing-attestation.md`
  asserted "D-003 remains the roadmap for future versioned semantic
  branches" — a governed, manifest-hash-pinned artifact, validated on every
  release, asserting live status for a register item the maintainers closed
  at the v1.1.12 cut. Wave 6's R11-14 sweep retired that claim everywhere it
  was *produced* but missed this static assertion. Also re-baselined: the
  `zmeta_change_governance.md` worked command (v1.1.9), TRADEMARK naming
  examples (v1.1.8), the `sign_release_artifacts.py` help example, and the
  compat CLI test's "current release target" — the last now derived from the
  manifest rather than pinned, so it cannot go stale again.
  Deliberately left alone: `adapters/README.md`'s "For v1.1.8 and later"
  is a correct historical boundary; re-baselining it would falsely narrow
  the rule.

**Live re-probe at close.** A real gateway process (profile H, JSON in /
compact out) was driven with each poison class: a 2**64 integer, a
300-deep extension nest, and a 20k-deep raw JSON bomb. Every one
produced an honest in-band diagnostic (`ENCODING_UNSUPPORTED` /
`SCHEMA_INVALID`) instead of terminating the process; an
uppercase-UUID + millisecond-timestamp event forwarded normally
(the V1-03 over-refusal class, closed); and ordinary `STATE_EVENT`
traffic still flowed afterwards. Process alive throughout.

*Reproducing it.* The probe was a throwaway script and is not in the
tree, so the method is recorded here rather than the file — deliberately,
since adding tooling would change the artifact under audit. Start the
gateway on loopback with `--profile H --input-encoding json
--output-encoding compact --no-emit-cot --no-metrics --no-stamp-timing`;
bind a UDP receiver on the forward port. Three setup facts cost real time
to rediscover and are worth having up front: **event ids must be UUIDv7**
(the schema pattern pins version 7 — a `uuid4` fails validation),
**profile H refuses `STATE_EVENT`s until timing is established** (send a
`SYSTEM_EVENT`/`TIME_STATUS` first or everything returns
`TIMING_STATUS_MISSING`), and **`STATE_EVENT` requires a resolvable
lineage parent** (an invented one returns `LINEAGE_PARENT_UNRESOLVED`) —
so the cleanest carrier for the normalization case is a `TIME_STATUS`
event with an uppercase `event_id` and a millisecond `ts`. Producer must
be one the policy authorizes (e.g. `fusion-engine`). Then send, per
datagram, checking process liveness and draining all replies between
sends: a `2**64` integer in `payload.extensions`, a ~300-deep extension
nest, a ~20k-deep raw JSON array bomb (larger overruns the UDP datagram
limit), the uppercase-UUID + millisecond-`ts` event, and finally an
ordinary event to confirm the gateway still serves.

**Validation at close:** kernel gate green all flags (bad-events 29,
harness 40), examples 51/51 strict, policy risk-mode lint ok, packet
size compact max=150 of 240 (unchanged), full pytest 785 passed + 316
subtests, `git diff --check` clean. Governed regeneration: manifest +
claims under the v1.1.16 identity, so the AGENTS.md divergence record
above continues to apply.

**Process note carried forward.** Across R1-10, the R1-11 fix pass, and
both verification passes, a fix has introduced or exposed the next
defect more than a dozen times. The verification pass is not ceremony —
it produced most of this cycle's real findings, and it should remain
mandatory after any pass that touches honesty-critical paths. Two
sharper forms of the lesson came out of pass 2, both worth carrying:
**a new guard is itself unreviewed code** (several findings came from
attacking freshly written pins, and two of those pins were reproducing
the exact defect class they had just been written to prevent), and **a
self-check that runs the same machinery on both sides is blind to
defects in that machinery** (V2-09: the compact round-trip check
encodes and decodes with the same CBOR library, so a backend divergence
that corrupts data only on the receiving node was invisible to it by
construction). Write the pin, then attack the pin — and ask what the
check cannot see.

## HOLD state (2026-07-22) — frozen pending a fresh full audit

**Status: WORK COMPLETE, HELD.** The R1-11 cycle is finished and
committed. It is deliberately **not** published: a fresh full-stack
audit runs before any release cut, and this section is the input to
that audit.

| | |
| --- | --- |
| Held range | `118f0b9`..`HEAD` — every commit of the R1-11 cycle, none pushed |
| Last code commit | `6ea9888` (verification pass 2); commits after it are records only |
| Working tree | clean; `git diff --check` clean |
| Remote | `origin/main` unchanged; nothing pushed, tagged, or signed |
| Battery at freeze | kernel gate all flags (bad-events 29, harness 40), examples 51/51 strict, policy risk-mode lint ok, compact packet max=150/240 unchanged, pytest **785 + 316 subtests** |
| Release decision | OPEN — maintainer's call (v1.1.17 recommended) |

Verify the held set live rather than trusting a number frozen into prose
(a hardcoded count goes stale the moment another record commit lands —
the very defect class item 5 of the audit checklist targets):

```bash
git log --oneline origin/main..HEAD
```

Nothing in this cycle has reached a consumer. The published v1.1.16
assets and their `SHA256SUMS` are untouched and remain the only thing
downstream verifiers see.

### Commit ledger

| Commit | Time | Content |
| --- | --- | --- |
| `118f0b9` | 07-21 19:15 | Audit findings record (disposition pending) |
| `74d92e1` | 21:41 | Fix wave 1 — compact fails closed (R11-01 MAJOR) |
| `88b527e` | 21:49 | Fix wave 2 — SAPIENT adapter honesty |
| `e3203ad` | 21:57 | Fix wave 3 — signalhunter no-lock + template loop_status |
| `545fe0b` | 22:06 | Fix wave 4 — checking machinery |
| `c1eb9d0` | 22:10 | Fix wave 5 — machine-encoded semantics |
| `33230af` | 22:16 | Fix wave 6 — release machinery honesty |
| `05ad9a8` | 22:21 | Fix wave 7 — doc currency + teaching surfaces |
| `07921e6` | 22:23 | Fix pass closeout (CHANGELOG, worklog, cycle outcome) |
| `d955cd0` | 22:55 | Verification pass 1 (V1-01..V1-03) |
| `6ea9888` | 07-22 01:09 | Verification pass 2 (V2-01..V2-14) |

`6ea9888` is the last commit that changes code. Anything after it in
`origin/main..HEAD` is records only — this closeout and any subsequent
correction to it. Those are deliberately not listed by hash: a ledger row
naming its own commit cannot be written correctly, and the live
`git log` is the honest source for them.

## What was touched — validation inventory

The audit validates against the diff, so this is the map of it.
**Measure the surface; do not read it out of this prose.** The range grows
every time another record or fix commit lands, so any total frozen here is
false by the time it is read — that is the defect class checklist item 5
exists to catch, and A-13 caught it here for the fifth time. Run:

```bash
git diff --shortstat origin/main..HEAD     # total surface, live
git diff --stat origin/main..HEAD          # per-file surface
git diff --name-only origin/main..HEAD     # file list
git log --oneline --reverse origin/main..HEAD -- <path>   # per-file history
```

Every count that remains in this section is a **historical measurement
anchored to `eb41794`** — the commit the fresh audit froze at — not a claim
about `HEAD`. The anchor is immutable, so those numbers stay true:
`git diff --shortstat 09118b3..eb41794` → 77 files, +4920 / −392, over
18 commits. Reproduce with `git diff --shortstat 09118b3..eb41794` (09118b3 = origin/main at measurement; the literal base survives the push that will move `origin/main` — A-13 closure 2026-07-27).

### Governed surfaces — check these first

Highest authority, smallest diffs, so they are cheap to verify exhaustively.

| Surface | Commits | Exactly what changed |
| --- | --- | --- |
| `schema/zmeta-event-1.0.schema.json`, `schema/zmeta-event-1.1.0.schema.json` | `74d92e1`, `c1eb9d0` | **Additive only:** three `reason_code` enum entries in each — `ENCODING_UNSUPPORTED`, `BEARING_FRAME_UNLABELED`, `NON_FINITE_CONFIDENCE`. No field, type, or event-vocabulary change. |
| `policy/violation-codes.yaml` | `74d92e1`, `c1eb9d0` | Same three codes with severities (`fail`, `warn`, `fail`). |
| `policy/semantics.yaml` | `74d92e1`, `c1eb9d0` | Same three codes listed. |
| `spec/semantics-contract.md` (**v1.0 LOCKED**) | `05ad9a8` | **+6 / −1 lines, §5.3 only.** Adds the rule that `last_sync_ts` is a synchronization claim only when `sync_state` is not `UNSYNCED`. Clarifies how to *read* an existing required field; adds no field and changes no vocabulary. |
| `AGENTS.md` | `33230af` | +6 lines: the post-release manifest-divergence recording rule. |

The three diagnostic codes are the cycle's only vocabulary additions
(Class B). Verify they are additive in both schemas, that severities
agree across `policy/` and `schema/`, and that nothing else in these
files moved.

### Code surfaces

File counts below are `git diff --name-only 09118b3..eb41794 -- <area>`
at the audit anchor.

| Area | Files | Commits | Why touched |
| --- | --- | --- | --- |
| `zmeta_compact.py` | 1 | `74d92e1`, `d955cd0`, `6ea9888` | Encode-side refusal, then verification through real serialization, then codec-internal failure conversion + exact epoch-ms arithmetic + backend-independent integer range. |
| `gateway/src/gateway.py` | 1 | `74d92e1`, `d955cd0`, `6ea9888` | `ENCODING_UNSUPPORTED` diagnostic, then the recovery ladder, then the receive-loop backstop. |
| `gateway/src/validators.py` | 1 | `545fe0b`, `c1eb9d0`, `6ea9888` | Producer-authority structural lint, bearing-frame/non-finite checks, then iterative denylist traversal + global-block lint. |
| `adapters/ingress/sapient/`, `adapters/egress/sapient/` | 7 | `88b527e`, `6ea9888` | Adapter honesty fixes, then non-finite handling on all vendor sinks + non-string `ts` guards. |
| `adapters/ingress/{cot,jreap,mavlink,signalhunter}/` | ~11 | `e3203ad` | `loop_status` self-assertion removed from three templates; signalhunter no-lock geo. |
| `tools/` (7 files) | 7 | `545fe0b`, `33230af`, `6ea9888` | Harness lint, release manifest/package builders and validators. |
| `release/` machinery | 4 | `33230af`, `6ea9888` | Formal-status honesty, notes-template handling, signing help text. |

### Test surfaces

New and extended tests are the cycle's largest single block
(pytest 687 → 785). Files: `test_compact_fail_closed.py`,
`test_gateway_runtime_guards.py`, `test_policy_risk_mode_lint.py`,
`test_release_currency.py`, `test_release_package.py`,
`test_release_manifest.py`, `test_bearing_frame_warn.py`,
`test_external_state_promotion.py`, `test_published_checksums_immutable.py`,
`test_bad_event_corpus.py`, plus the SAPIENT/CoT/JREAP/MAVLink/signalhunter
adapter suites. Per Step 0, each of these should end up mapped to the
finding it pins.

### Regenerated artifacts (not hand-edited)

`release/zmeta-release-manifest.yaml` (8 commits) and
`conformance/claims/example-*.yaml` (8 commits each) are **outputs of
`tools/build_release_manifest.py --update-claims`**, regenerated after
every code change. Their churn count is high and carries no independent
meaning — verify by regenerating and diffing, not by reading:

```bash
python tools/build_release_manifest.py --release-id zmeta-v1.1.16 \
  --release-name "ZMeta v1.1.16" --release-status formal_release \
  --release-date 2026-07-21 --branch main --update-claims
git diff --stat   # expect: no change
```

### Records

`docs/r1_11_full_stack_audit.md`, `docs/zmeta_refinement_worklog.md`,
`CHANGELOG.md`, `docs/zmeta_refinement_handoff.md`, plus `README.md`,
`RELEASE_CHECKLIST.md`, `TRADEMARK.md`, `adapters/AUTHORING.md` and the
doc-currency re-baselines. High churn because they were rewritten across
resumed sessions — which is why checklist item 5 targets them.

Per-record commit counts are deliberately **not** frozen here: they are the
fastest-moving number in the range (every correction to a record increments
its own count, so the figure is stale the instant it is written — the
original of this paragraph was wrong on three of its four counts). Measure
them:

```bash
for f in docs/r1_11_full_stack_audit.md docs/zmeta_refinement_worklog.md \
         CHANGELOG.md docs/zmeta_refinement_handoff.md; do
  printf '%s %s\n' "$f" "$(git log --oneline origin/main..HEAD -- "$f" | wc -l)"
done
```

At the audit anchor `eb41794` they were 11 / 8 / 5 / 6 respectively.

## Execution continuity — interruptions and recovery

This cycle was executed across **four sessions broken by usage limits**,
plus a mid-cycle model switch and one full chat reset. That is recorded
here in detail because interrupted work is a defect surface in its own
right, and because the fresh audit should target it (checklist below).

### Order of events

Read top to bottom; **▲ marks where a session ended involuntarily.**

| When | Event | State left behind |
| --- | --- | --- |
| 07-21 19:15 | Audit record committed `118f0b9` | Clean; disposition pending |
| | Maintainer disposition: "fix them and work down that list" | — |
| 21:41–22:21 | Fix waves 1–7 (`74d92e1`..`05ad9a8`), full battery at each wave boundary | Clean at every boundary |
| 22:23 | Fix-pass closeout `07921e6` | Clean |
| | Post-fix verification audit launched | — |
| ▲ | **Usage limit — audit killed with 1 of 6 slices done** | Clean tree; one slice's findings unread |
| | Resume: read the surviving slice, reproduce both defects, find a third while fixing | — |
| 22:55 | Verification pass 1 `d955cd0` | Clean |
| | Full 7-slice verification audit run to completion (24 agents) | Findings reported |
| | Began V2-01 fix — a **two-layer** change (codec, then gateway) | — |
| ▲ | **Usage limit mid-edit** | ⚠ **`zmeta_compact.py` modified, uncommitted, layer 2 missing** |
| ▲ | Safeguards flag routine requests; model switched Fable 5 → Opus 4.8 (×2), one request blocked | No repo change |
| ▲ | **Maintainer reset the chat entirely** | ⚠ Same partial edit; **zero in-context memory** |
| | Resume: state rebuilt from `git status` + working diff + records; partial fix found and completed | — |
| 07-22 01:09 | Verification pass 2 `6ea9888` | Clean — last code commit |
| 07-22 | Closeout records (HOLD, ledger, Step 0, count corrections) | Clean; **held** |

The two ⚠ rows are the whole reason for checklist item 1: for that
span, the repository contained a fix that looked finished and was not.

**Interruption 1 — post-fix verification audit killed mid-run.** After
`07921e6`, the first post-fix verification audit was cut off with **1
of 6 slices complete**. That single surviving slice had already found
two defects the fix pass itself introduced. On resume the slice result
was re-read rather than re-run, both defects were independently
reproduced before being fixed, and a third (the over-refusal, V1-03)
was found while fixing them. Closed as `d955cd0`.
*Residue risk: none — the interruption fell between a completed commit
and a not-yet-started edit.*

**Interruption 2 — usage limit mid-edit, leaving a PARTIAL fix.** The
full seven-slice verification audit then ran to completion (24 agents,
~42 min, zero errors) and reported its findings. Work began on the
V2-01 crash-class fix, which is a **two-layer** fix: (a) the codec
converts its own serialization failures into
`CompactUnrepresentableError`, and (b) the gateway receive loop gains a
last-resort backstop. The session was cut off **after layer (a) and
before layer (b)**, leaving one uncommitted, half-applied change in
`zmeta_compact.py`.
***This is the dangerous class.*** A partial fix looks like a finished
one: the codec change alone is syntactically complete, passes its own
import, and reads as deliberate. It was caught only because the resuming
session began by reading `git status` and the actual working diff
instead of trusting the narrative of what had been done. **Resume from
the tree, never from the transcript.**

**Interruption 3 — model switch and blocked requests.** Mid-cycle,
automated safeguards flagged several routine requests on this
(defensive, ISR-interoperability) codebase, switching the model
Fable 5 → Opus 4.8 twice and blocking one request outright. No repo
state was changed by these events, but they fragmented the working
context.

**Interruption 4 — full chat reset.** The maintainer reset the
conversation entirely after repeated spurious flags. The recovering
session therefore had **no in-context memory of the work at all** — it
reconstructed state solely from the repository (git log, working diff,
the audit record, the worklog) plus the prior transcript supplied as
data. Everything from `6ea9888` was produced under that reconstruction.

### What the interruptions could have left, and what was checked

| Risk | Check performed | Result |
| --- | --- | --- |
| Half-applied multi-layer fix | Read full working diff before any new edit | Found — V2-01 layer (b) missing; completed |
| Edits applied but untested | Full battery re-run after every change set | Green at each point |
| Findings silently dropped across sessions | Re-derived the finding list from the completed audit output, not from memory | All accounted for; V2-01..V2-08 then extended to V2-14 |
| Stale counts in records after resumed work | Re-measured pytest/gate/packet numbers at freeze | Records match measurement |
| Encoding corruption from tooling across sessions | UTF-8 + mojibake scan on every edited doc | Clean, no BOM |
| Manifest drift from partial regeneration | Regenerated and re-validated after every code change | Gate exit 0 |

### What is NOT recoverable

Stated plainly so the audit does not hunt for evidence that no longer
exists. The audit and sweep ran as multi-agent workflows whose per-agent
transcripts live in session-scoped storage and are **gone** — the
findings, verdicts, and refutation reasoning survive only as summarized
into this record. Likewise the live-probe script (method recorded above).
**Practical consequence: this record is the sole surviving evidence for
the V1/V2 findings, and it was written by the same author as the fixes.**
An auditor should therefore re-derive the findings from the code rather
than confirm them from this document — treat the V1/V2 sections as
claims to be tested, not as findings already established.

### Step 0 (do this FIRST): build the finding → code → test map

**This does not exist and should be the audit's first deliverable.** The
V1/V2 sections describe each fix in prose but never name the code
location that implements it or the test that pins it. Every other item
below is slower and less trustworthy without that map, and item 1 is
close to unanswerable without it — which matters because item 1 covers
the risk the interruptions actually created.

Build one row per finding, **17 rows: `V1-01`..`V1-03` and
`V2-01`..`V2-14`** (contiguous — a gap means a finding was lost between
sessions, which is itself the item-1 defect):

| Finding | Claimed fix | Code location(s) | Pinning test(s) | Verified |
| --- | --- | --- | --- | --- |

Rules that make the map worth building:

- **Derive it from the code, not from this record.** Read the finding,
  then go find the implementation yourself. A row copied out of the
  prose above proves only that the prose is self-consistent — and per
  "What is NOT recoverable", this record is the sole surviving evidence
  and shares an author with the fixes.
- **Multi-layer fixes get one row per layer.** These are where an
  interruption can leave half a fix looking whole: **V2-01** (codec
  conversion *and* gateway receive-loop backstop), **V2-03** (all six
  vendor-block sinks *and* the point-of-use invariant *and* the
  positional-array rule), **V2-04** (global block *and* per-producer
  no-op detection *and* mistyped sub-blocks), **V2-12** (all four
  release-context docs *and* the completeness check), **V2-13**
  (builder option *and* validator diagnostic *and* checklist step).
  A row is complete only when every layer is located.
- **An empty "pinning test" cell is a finding.** It means the fix is
  real but unguarded, and the next interruption or refactor can silently
  undo it. Record it rather than filling the cell with the nearest
  plausible test.
- **A row you cannot fill at all is the item-1 defect**, not a
  documentation gap — treat it as a live finding and reproduce the
  original defect to confirm.

Once the map exists, items 1–6 become checks against it rather than
open-ended reading.

### Targeted checklist for the fresh audit

Given the above, the re-audit should not merely repeat the R1-11 method.
It should specifically attack:

1. **Partial-application residue.** Every fix claimed in `V1-*`/`V2-*`
   should be verified present *in the code*, not just in the record —
   with particular attention to the multi-layer fixes enumerated in
   Step 0, where an interruption can leave half a fix looking whole
   (this is exactly what interruption 2 did). Work from the Step 0 map;
   any row that cannot be filled is a finding.
2. **Commit-truth across the interrupted boundaries.** Every commit in
   `origin/main..HEAD` should reproduce its message's claims, especially
   `d955cd0` and `6ea9888`, which were authored on either side of the
   resets.
3. **The new guards themselves.** This cycle demonstrated twice that a
   fresh pin can reproduce the defect it targets. Every guard added in
   V2 is unreviewed-by-anyone-but-its-author code: the promotion lint,
   the currency-guard matcher and its family check, the drop-reason
   vocabulary pin, the vendor-sink point-of-use pin, the release-notes
   placeholder validator, the backend-parametrized compact tests.
4. **Blind-by-construction checks.** V2-09 was invisible to the compact
   round-trip check because that check uses one library on both sides.
   Ask the same question of every other self-check in the stack: what
   can it not see because both sides share machinery?
5. **Counts and claims in the records.** The CHANGELOG, worklog,
   handoff, and this record were all edited during resumed sessions;
   their stated numbers, commit hashes, and finding IDs should be
   re-verified against reality. This item has already caught four real
   errors in this closeout — two stale commit counts, a wrong MAJOR
   tally, and a pass-2 summary left over from before the second sweep —
   so treat it as high-yield, not bookkeeping. Ground truth as measured
   at freeze, for checking against:

   | | MAJOR | MODERATE | MINOR | Total |
   | --- | --- | --- | --- | --- |
   | Pass 1 (`V1-*`) | 1 | 2 | 0 | **3** |
   | Pass 2 (`V2-*`) | 2 | 7 | 5 | **14** |
   | | | | | **17** |

   Cycle-level MAJORs are **four**: `R11-01` (honesty, from the original
   audit), `V1-01` and `V2-01` (the two crash classes), `V2-09`
   (cross-backend laundering). Note `V2-02` is a *third* crash class at
   MODERATE — a claim of "two MAJOR crash classes" is about severity,
   not about how many crash classes exist. Regenerate any of these with:

   ```bash
   grep -oE "^- \*\*V[12]-[0-9]+ \((MAJOR|MODERATE|MINOR)" docs/r1_11_full_stack_audit.md
   ```
6. **Scope creep in the doc-currency sweep.** Several stale literals
   were re-baselined and one (`adapters/README.md` "For v1.1.8 and
   later") was deliberately left as a correct historical boundary. That
   judgement should be re-checked, along with whether any re-baseline
   falsified a genuinely historical statement.
7. **Allocate at least one lens by CLAIM DENSITY, not diff size.**
   Added from A-30, which measured the fresh audit's own coverage: lens
   allocation concentrated on the ~15 largest diffs, and eleven changed
   surfaces — mostly small doc and data files (`examples/*.jsonl`, six
   adapter READMEs, `spec/release-hash-policy.md`,
   `spec/profile-compatibility.md`, a mapping pack, a template) — had
   their **diffs read by no lens** until the critic pass. Four findings
   (A-09, A-10's false claim, A-20, A-21) lived there. A small diff is
   where a *claim* gets added that the code does not keep, and a claim
   costs one line to write and a full probe to falsify. Rank the changed
   file list by assertions-per-line, not by insertions, and give the top
   of that list a dedicated lens.

Until that audit runs and the maintainer takes the release decision,
this cycle stays local and unpublished.

---

## Fresh full-stack audit (2026-07-22) — the held range re-audited

### 1. Method and what it could not see

This audit ran against the working tree at `eb41794` with `origin/main` at `09118b3` — 18 held commits, `git diff --shortstat 09118b3..eb41794` = 77 files, +4920 / −392, nothing pushed, tagged, or signed. (The anchor is written as `eb41794`, not `HEAD`, on purpose: `HEAD` has moved since, so a `HEAD`-relative figure would misdescribe what this audit actually read.) It ran read-only: no file was created, edited, or deleted; no git write command, no manifest or package builder was executed.

Eleven independent lenses were run over the range, each with a distinct surface: partial-application residue; commit-message-to-diff truth; the promotion/policy lint; the vocabulary and non-finite sinks; the release and compact guards; the doc-currency guards; the record counts and validation inventory; blind-by-construction self-checks; the locked semantics contract; the schema/policy governed surfaces; the three core modules (`zmeta_compact.py`, `gateway/src/gateway.py`, `gateway/src/validators.py`); the adapters; the tools/release machinery; the test suite's own quality; and the seven design gates. Every candidate finding was then put through three-lens adversarial refutation, where a refuter's default was "not a defect" and the burden sat on the finder. **35 candidates were killed. 28 survived.** The refuted list in section 4 is not decoration — it is the bar.

The governing evidence rule was that `docs/r1_11_full_stack_audit.md` is a claim set, not evidence. Every conclusion below is anchored in code read at a line, a diff hunk, a live probe, or a test run. Where a lens's only support was that the document agrees with itself, the candidate was dropped.

**What this audit could not see, stated as plainly as it demands of its predecessor:**

- **It never established that the pre-fix defects were real.** No lens checked out `118f0b9^` or any wave parent to confirm that the 25 claimed R11-xx defects existed before their fixes. Checking out a held commit is a git write. The audit therefore cannot distinguish a fix that closed a real defect from machinery built for a non-problem — which is exactly the judgement the over-optimization question needed. Two pre-states (`88b527e`, `d955cd0`) were read via `git show <sha>:<path>`, which is the extent of the pre-state evidence.
- **It could not run the writing tools.** `tools/build_release_manifest.py`, `tools/build_release_package.py`, `release/build_release_bundle.py`, `release/build_mvp_packages.py`, and `release/sign_release_artifacts.py --write-checksums` were read, not run. The "regenerating is a true no-op" claim was tested by re-implementing the builder's pure hashing functions in memory (all 70 artifact hashes, all 19 group hashes, the bundle hash and the manifest hash reproduce exactly), which covers every hash and path list but would not catch a hand edit confined to a non-hash field that happens to match builder output.
- **It could not re-run the historical numbers.** Per-wave pytest counts asserted in six commit messages (694+226, 753+284, 742+237) were not reproduced; only the HEAD figure was measured, and it matches. The closing live UDP probe recorded at `docs/r1_11_full_stack_audit.md:549-577` is not reproducible — `3bc37c7` deliberately recorded the method in prose rather than committing the script. Substitute in-process probes were used instead, and one of the record's three probe results turns out to be install- and depth-dependent (see A-04).
- **It could not test process claims.** The V1/V2 per-agent transcripts are gone. Agent counts, refutation counts, and the narrative of how the original audit ran are unfalsifiable. They were used for nothing.
- **Live-fleet behaviour is out of reach.** No real SAPIENT DMM, no ATAK client, no non-Python JSON decoder was available. Findings that turn on a remote consumer's behaviour (A-01's CoT `lat="nan"`, A-11's `NaN`-in-a-string label) rest on RFC 8259 and on the repo's own stated threat model, not on an observed rejection.
- **Depth and recursion thresholds are interpreter-specific.** A-04's ~990-level threshold is `sys.getrecursionlimit() == 1000` on CPython 3.14/Windows. Raising the limit moves the threshold; it does not close the gap, because the guard is bypassed rather than bounded.
- **Coverage was risk-weighted, not uniform.** The large code diffs were read whole. Four surfaces had their diffs read by no lens until the critic pass: `examples/zmeta-v1.1-examples.jsonl`, several adapter READMEs, `spec/release-hash-policy.md`, and `spec/profile-compatibility.md`. Four findings live in that set. That is the honest measure of what a diff-size-weighted allocation misses.
- **One structural blind spot the audit shares with the suite it audited:** five lenses cited "full kernel gate green, all flags" as assurance for the release machinery. `tools/validate_conformance.py:295-299` invokes the package validator with `templates_only=True`, and `validate_release_package.py:384-385` returns before the notes check in that mode. A green kernel gate is not evidence about the release-package layer at all.

**Gates run at HEAD, all green:** the full kernel gate with all nine flags (projection 37, extension registry 61, conformance classes 34 / claims 2, encoding-negative 50, precision 32, bad-events 29, adapter harness 40, conformance pass=20/fail=27); `validate_examples.py --strict --require-all` 51/51; `python -m pytest -q` **785 passed + 316 subtests**, reproducing the recorded ground truth exactly; `git diff --check origin/main..HEAD` clean; working tree clean; `validate_release_manifest.py` ok (19 groups, 70 artifacts); gateway `--self-test`, `tools/test_workflow_end_to_end.py`, and `tools/test_gateway_live.py` on both the JSON and compact/Profile-L paths all exit 0. Every finding below is present in that green tree. That is the point.

---

### 2. Step 0 — the finding → code → test map

Derived from code. 41 rows. Non-PRESENT rows are flagged and carried into A-28.

| Finding (layer) | Status | Code anchor | Pinning test | Note |
|---|---|---|---|---|
| V1-01 L1 — compact-egress recovery ladder | **PRESENT** | `gateway/src/gateway.py:830-875`; sole call site `:1933-1939` | `test_compact_fail_closed.py:253, 282, 321, 344` | Four tests incl. a mock-forced sentinel rung. Docstring at `:839-840` is false — both rungs pass `details={"error": error}` carrying caller-derived paths. Behaviour still fail-closed. |
| V1-01 L2 — receive-loop drop-and-continue on `None` payload | **UNPINNED** | `gateway/src/gateway.py:1940-1949` | *incidental only* — `test_gateway_runtime_guards.py:255` counts `record_drop` literals `>= 4` | No test drives the branch. Goes slack the moment a fifth `record_drop` lands anywhere. |
| V1-02 L1 — verification through the real serialization boundary | **PRESENT** | `zmeta_compact.py:504-506, 467-490, 523-536` | `test_compact_fail_closed.py:440` (deep nesting) | Pin is thinner than claimed. The NaN test does **not** pin it (verified: the explicit non-finite guard fires regardless). Between `d955cd0` and `6ea9888` this layer shipped unguarded. |
| V1-02 L2 — explicit non-finite refusal by path name | **PRESENT** | `zmeta_compact.py:406-411, 412-414` | `test_compact_fail_closed.py:226, 240, 246` | Linkage confirmed by executing the reverted comparison shape. |
| V1-02 L3 — normative MUST in the mapping spec | **UNPINNED** | `spec/compact-binary-mapping.md:22-26, 44-46` | **NONE** | Only toolchain reference is the checksum list at `build_release_manifest.py:221`. Currency pin, not content pin. |
| V1-03 L1 — declared-normalization equivalence | **PRESENT** | `zmeta_compact.py:325-337, 340-376, 415-420` | `test_compact_fail_closed.py:183, 194, 206, 220, 451, 464` | Honesty direction checked: cannot launder. `_same_instant` requires the ORIGINAL to carry no sub-ms precision. |
| V1-03 L2 — normative declaration of the two normalizations | **UNPINNED** | `spec/compact-binary-mapping.md:28-38, 39-47, 49-52` | **NONE** | Table and code agree today; nothing holds them together in either direction. An undeclared-but-implemented normalization is the laundering this fix exists to prevent. |
| V2-01 LA — codec converts its own failures | **PRESENT** | `zmeta_compact.py:467-521, 504-513, 314, 1097-1112`; `gateway.py:820, 722-725` | `test_compact_fail_closed.py:440, 471` | Pre-fix behaviour reproduced: bare `ValueError`/`OverflowError` from the backends confirmed. |
| V2-01 LB — receive-loop backstop | **PRESENT** | `gateway.py:1850-1863, 2006-2014, 1841-1849` | `test_gateway_runtime_guards.py:221, 232, 305` | Source-string pins only; no behavioural test drives `main()` with a poison datagram. Both scope tests locate the region by the literal comment `# Receive-loop backstop`. The third test in the class (`:240`) is a pure-Python tautology and pins nothing. |
| V2-02 — iterative BFS in `_find_forbidden_key` | **PRESENT** | `validators.py:305-325, 3`; call sites `:1926, 1972, 1997, 2026` | `test_gateway_runtime_guards.py:277, 291` | Correct. Residual: `path + [key_str]` per node ⇒ O(depth²); measured 100k depth = 3.4 s, ~10k (UDP-bounded) ≈ 34 ms/datagram. |
| V2-03 LA — non-finite drop at every vendor sink | **PRESENT** | `sapient_to_zmeta.py:520, 640, 827, 900, 926, 1040, 1074, 113-121` | `test_sapient_ingress.py:1024, 994, 1105` | **Seven** sinks, not six. All guarded. Promotion sink `:827` has structural cover only; the pin's regex matches dict-literal form only. |
| V2-03 LB — point-of-use invariant | **PRESENT** | `sapient_to_zmeta.py:606-610, 624, 640` | `test_sapient_ingress.py:1105` | Confirmed against the intermediate tree (`88b527e` had one early call at line 583). |
| V2-03 LC — positional-array rule | **PRESENT** | `sapient_to_zmeta.py:124, 127-146, 149-170` | `test_sapient_ingress.py:1122` | Pre-fix laundering shape (filtering comprehension that re-indexed) read in `88b527e`, not trusted. |
| V2-04 L1 — global promotion block linted | **PRESENT** | `validators.py:1301-1327, 1362-1375`; `lint_policy_risk_modes.py:35` | `test_policy_risk_mode_lint.py:161, 188, 102` | All 18 global keys re-derived from enforcement; none unread, none missing. |
| V2-04 L2 — per-producer no-op detection | **PRESENT** | `validators.py:1286-1300, 1451-1463` | `test_policy_risk_mode_lint.py:232, 145, 116` | Six-key set re-derived from `_external_promotion_rules`, `_promotion_mode`, `_union_rule_values`. Exactly right. |
| V2-04 L3 — mistyped `degrade`/`quarantine`/`use_limits` fail | **PRESENT** | `validators.py:1376-1398, 1399-1428` | `test_policy_risk_mode_lint.py:199, 226, 172` | Implemented and pinned, but stops short of the safety keys — see A-07. |
| V2-05 — exact integer epoch-ms both directions | **PRESENT** | `zmeta_compact.py:1070-1077, 1080-1094, 1097-1110` | `test_compact_fail_closed.py:485, 492, 503` | Original defect reproduced: the old float expression disagrees on 120 of 2000 sweep values. |
| V2-06 L1 — non-string `ts` refused (state egress) | **PRESENT** | `zmeta_state_to_sapient_detection.py:107-114, 271-274` | `test_sapient_egress.py:544` | — |
| V2-06 L2 — non-string `ts` refused (command egress) | **PRESENT** | `zmeta_command_to_sapient_task.py:63-70, 197-201` | `test_sapient_egress.py:544` | One test, two independent pins. |
| V2-06 L3 — `drop_reasons` SCREAMING_SNAKE | **PRESENT** | `gateway.py:1943-1948, 301-307, 1468, 1846, 2008` | `test_gateway_runtime_guards.py:250, 255` | No lowercase residue anywhere in the canonical tree. |
| V2-07 LA — phrasing-independent overview currency guard | **PRESENT** | `test_release_currency.py:241, 250-257, 296-313` | `test_release_currency.py:260, 296` | Matcher non-vacuous (19 real superseded versions). Coverage gap: v1.0.0/v1.0.1 have no notes file, so claims naming them are invisible. |
| V2-07 LB — corrected `_NOT_LONGER_VERSION` lookahead | **PRESENT** | `test_release_currency.py:243-247, 270, 306` | `test_release_currency.py:260-294` | Pin proved by revert-simulation: restoring `(?![\d.])` makes the self-test fail. |
| V2-08 — release-notes template "Known Open Issues" | **UNPINNED** | `release/RELEASE_NOTES_TEMPLATE.md:36-44` | **NONE** | Fix correct. Every consumer checked: existence-only. Re-adding the retired D-003 line leaves the suite green and ships the false claim. `test_release_manifest.py:104` pins the manifest, the *other* producer — it is the plausible neighbour, not the pin. |
| V2-09 LA — codec CBOR 64-bit integer range | **PRESENT** | `zmeta_compact.py:435-436, 439-457, 497-502, 460-464`; `gateway.py:819-823` | `test_compact_fail_closed.py:~410, ~430`, backend helper `~392` | Verified three ways incl. revert-simulation (6 subtest failures across both backends). Cross-backend divergence reproduced live. |
| V2-09 LB — normative refusal list in the mapping spec | **ABSENT** | `spec/compact-binary-mapping.md:39-48, 57-60, 228-240` | **NONE** | The integer bound is stated nowhere in the governed spec. **Refuted 3/3 as a defect** (see §4) — the mapping's Encoding Rules define no bignum representation, so silence is not permission. Carried here as a documentation gap for the maintainer, not a finding. |
| V2-10 — sub-ms resolution checked on the ORIGINAL string | **PRESENT** | `zmeta_compact.py:350-356, 359-376, 418, 12-16` | `test_compact_fail_closed.py:451-462, 464-469` | Reversion reproduced against live code; schema pattern is `Z$` only, so 7-digit fractions are schema-valid and the defect was reachable. |
| V2-11 — decode-side epoch-ms fails closed | **PRESENT** | `zmeta_compact.py:1097-1111, 1105`; call sites `:660, 662, 664, 815, 1010` | `test_compact_fail_closed.py:471-478` | Reversion reproduced. Residual: the pin calls private `_format_ts` rather than driving `loads()` with a hostile packet. |
| V2-12 L1 — `zmeta_correlation_pattern.md` re-baselined | **PRESENT** | `docs/zmeta_correlation_pattern.md:4` | `test_release_currency.py:113-124` | Pre-state confirmed via `git show origin/main:` — the doc was genuinely unguarded before the range. |
| V2-12 L2 — `zmeta_mqtt_binding_guidance.md` | **PRESENT** | `:4` | `test_release_currency.py:113-124` | — |
| V2-12 L3 — `zmeta_vocabulary_crosswalk.md` | **PRESENT** | `:4` | `test_release_currency.py:113-124` | — |
| V2-12 L4 — `zmeta_professional_overview.md` (already guarded) | **PRESENT** | `:4` (unchanged across the range) | `test_release_currency.py:150-156` and `:113-124` | Two independent pins. No edit needed; recorded for exhaustiveness. |
| V2-12 L5 — family pin extended to all four | **PRESENT** | `test_release_currency.py:100-111, 113-124, 41-48` | *is itself the test* | Manifest-derived expected value; iterates the whole tuple. |
| V2-12 L6 — completeness check on carriers | **PRESENT** | `test_release_currency.py:126-134, 136-148` | *is itself the test* | Position-based matcher correct against the tree. Scope limits (docs/ only, first 10 lines) are real but fail **safe** — see §4. |
| V2-13 L1 — builder `--release-notes` option | **PRESENT** | `build_release_package.py:181, 255-256, 276-284, 303` | `test_release_package.py:199` | Python API only. The argparse wiring is unguarded; the documented release command is a CLI invocation. |
| V2-13 L2 — `RELEASE_PACKAGE_NOTES_PLACEHOLDER` | **PRESENT** | `validate_release_package.py:335-340, 342-375, 395` | `test_release_package.py:157, 178` | Reproduced against the shipped artifact: `release/package-v1.1.16` really does carry the template beside `release_state: formal_release`. Fires only on explicit `--package-dir`. |
| V2-13 L3 — checklist step | **UNPINNED** | `RELEASE_CHECKLIST.md:31-37` | **NONE** | Repo-wide grep for `RELEASE_CHECKLIST` across `*.py` returns zero hits. |
| V2-14 LA — `release-signing-attestation.md` D-003 retraction | **UNPINNED** | `spec/release-signing-attestation.md:164-170` | **NONE** | `validate_templates` checks existence + secrets only. Manifest hash detects an *unregenerated* edit, not a *stale claim*. |
| V2-14 LB — `zmeta_change_governance.md` worked command | **UNPINNED** | `docs/zmeta_change_governance.md:338` | **NONE** | Currency suite pins worked commands in exactly two files; this is neither. |
| V2-14 LC — `TRADEMARK.md` naming examples | **UNPINNED** | `TRADEMARK.md:22, 24` | **NONE** | Illustrative examples; re-baselining created a recurring obligation the record declined to create for `adapters/README.md`. Treated inconsistently. |
| V2-14 LD — `sign_release_artifacts.py --version` help | **UNPINNED** | `release/sign_release_artifacts.py:231` | **NONE** | Decorative `e.g.` whose own default is already manifest-derived. |
| V2-14 LE — compat CLI target manifest-derived | **UNPINNED** | `test_check_compat_cli.py:117-128, 139` | **NONE** | Real improvement, reversible with no signal: `check_compat.py` TARGETS still lists `v1.1.14`, so a revert to the literal still passes. |

**Summary:** 34 PRESENT, 6 UNPINNED, 1 ABSENT. Every UNPINNED row is correct in the tree today; none reproduces a failure now. Together they are A-28. The one ABSENT row survived refutation as a documentation observation, not a defect.

---

### 3. Findings

28 findings survived three-lens refutation. *(Correction 2026-07-27, cold re-read CR-25: the numbered list below runs A-01..A-30 — thirty entries; treat the enumeration, not this count, as ground truth. No stated count reconciles the disposition's “91 findings” input either.)* Numbered in severity order.

#### MAJOR

- **A-01 (MAJOR, honesty/laundering):** Non-finite floats are laundered through the canonical kernel onto the JSON wire and into CoT/TAK egress.
  **Location:** `gateway/src/validators.py:1913` (the only `math.isfinite` in `gateway/src`), `gateway/src/gateway.py:816`, `adapters/egress/cot/zmeta_to_cot.py:256`.
  **Evidence:** The new guard is field-scoped, not value-scoped: its candidate list is exactly `[confidence, payload.claim.confidence]`. Its own stated rationale — that jsonschema min/max comparisons are vacuous against NaN (`validators.py:1900-1903`) — applies verbatim to `payload.geo.lat`/`lon`, which carry `minimum`/`maximum` at `schema/zmeta-event-1.0.schema.json:658-662`. Live probe on HEAD: a STATE_EVENT with `geo.lat = NaN`, `geo.lon = NaN`, `alt_m = Infinity` returns `validate_schema → (True, [])`, `validate_semantics → (True, [])`, `validate_outgoing_event → []`, and is forwarded as `TRACK_STATE`, not a diagnostic. `_encode_message(ev, 'json')` then emits `"geo":{"lat":NaN,"lon":NaN,"alt_m":Infinity}`; `_encode_message(ev, 'cbor')` emits 362 bytes with no refusal; only `compact` refuses. `zmeta_to_cot` produces `<point lat="nan" lon="-118.2435" hae="inf" le="9999999.0" ce="9999999.0" />`. Ingress is symmetrically open — `json.loads` at `gateway.py:774, 789, 810` has no `parse_constant`, and the CBOR path produces non-finite from float16/32/64 (`zmeta_cbor.py:271-282`). Confirmed field-scoping by re-running with NaN in `confidence`: `NON_FINITE_CONFIDENCE` fires correctly.
  **Reproduction:** Take the shipped Profile-L TRACK_STATE example, replace `payload.geo.lat` with the literal token `NaN` and `alt_m` with `Infinity` in the JSON text, call `gateway.process_message(raw, schema, policy, 'L', {}, 'json', strict_validation=True)`. The event is returned, not refused. `gateway._encode_message(out[0], 'json')` contains `"lat":NaN`. Both the full kernel gate and `pytest gateway/tests/test_compact_fail_closed.py gateway/tests/test_encoding_roundtrip.py -q` pass green with this present.
  **Impact:** Two failures from one datagram. (1) Fielded safety — ATAK receives `lat="nan" hae="inf"`, a position that is not a position, delivered with no uncertainty label, no violation code, and no filterable marker, rendered to an operator as an ordinary track. Design gate 3, at the sharp end. (2) Interoperability — `NaN`/`Infinity` are not RFC 8259, so Go `encoding/json`, Rust `serde_json`, Jackson and browser `JSON.parse` hard-reject the whole datagram while Python consumers silently accept a NaN coordinate; the track vanishes with no ZMeta diagnostic explaining why. Whether the event is refused today is decided by which output encoding the operator configured, not by the semantics. **This is pre-existing, not introduced by the held range** — but `CHANGELOG.md:53` and the new `NON_FINITE_CONFIDENCE` vocabulary present the non-finite-on-the-wire class as closed, and it is closed only for compact egress and one field. The fix is a value-scoped traversal in `validate_semantics` reusing the iterative pattern now in `_find_forbidden_key`, not another per-field allowlist.
  *Reported independently by four lenses (item1, item4, governed-schema-policy, code-core). One refutation vote, cast on scope framing rather than on the mechanism; the probe was reproduced by three separate lenses.*

- **A-02 (MAJOR, honesty/laundering):** SAPIENT ingress puts NaN/Infinity into canonical `claim`, `features` and `bearing` — contradicting a CHANGELOG claim that ships with the cut.
  **Location:** `adapters/ingress/sapient/sapient_to_zmeta.py:678` (claim), `:397`, `:415`, `:354` (arithmetic products).
  **Evidence:** Two independent holes. (a) `claim["sub_class"] = entry["sub_class"]` copies a vendor structure verbatim into the CANONICAL field `payload.claim.sub_class` with neither `_is_number` nor `_drop_non_finite`; the guard was applied only to the seven `VENDOR_EXTENSION_KEY` sinks, and the pinning test `test_every_vendor_block_is_dropped_at_point_of_use` regexes only `VENDOR_EXTENSION_KEY:\s*`, so it cannot see this site. Live: a DetectionReport whose `classification[].sub_class[].confidence` is NaN emits an INFERENCE_EVENT/CLASSIFICATION with `claim: {..., 'sub_class': [{'confidence': nan}]}`, `validate()` returns `pass`, and `json.dumps(e, allow_nan=False)` raises. The sibling OBSERVATION_EVENT in the same call serializes cleanly — its copy went through `_drop_non_finite` at `:640` — which isolates `:678`. (b) `_is_number` is applied to the OPERAND, never the PRODUCT: `float(value) * factor` (`:397`), `stop_hz - start_hz` (`:415`), `math.degrees(...) % 360.0` (`:354`) each overflow to `inf`, and `inf % 360.0` is NaN. With `centre_frequency: 1e308` in MHz, `translate()` emits `payload.features == {'center_freq_hz': inf, 'bandwidth_hz': inf, ...}`; `validate()` → `('pass', [])`; gateway `validate_schema` → 0 errors; `validate_semantics` → `(True, [])`. With `azimuth: 1e308` radians, `payload.bearing == {'az_deg': nan}` while `quality.bearing_frame = 'TRUE_NORTH'` is still stamped at `:628` and `BEARING_FRAME_UNLABELED` does not fire.
  **Reproduction:** Load `adapters/ingress/sapient/test_sapient_ingress.py` helpers; `translate(_detection_msg(signal=[{'amplitude': -57.0, 'centre_frequency': 1e308, 'start_frequency': -1e308, 'stop_frequency': 1e308}]), SCHEMA_ID, registration=_store(_rf_registration_msg()))` → `features.center_freq_hz == inf`, `validate()` == `('pass', [])`, `json.dumps(obs, allow_nan=False)` → `ValueError: inf`. `python -m pytest adapters -q` → 269 passed, so nothing in the suite covers either hole.
  **Impact:** A canonical `bearing.az_deg` of NaN asserted as TRUE_NORTH is a geolocation claim that validates clean at schema and semantics — design gate 3. A NaN inside `payload.claim` is a non-claim presented as adjudicable evidence in the field consumers read to decide what the X on the map is — design gate 2. Neither event has an RFC-8259 wire form. Reachability for (b) requires wire values near the float64 ceiling, i.e. a corrupt or hostile producer — which is precisely the threat model the module states for itself at `:112-116` ("NaN/inf from the wire") and `:181-182` ("wire data must never crash the ingest loop (fail closed)"). Release-relevant beyond the code: `CHANGELOG.md:37-38` asserts of this range that "non-finite numbers refuse at every canonical guard", and that sentence ships with the cut.

- **A-03 (MAJOR, availability/fail-closed):** The receive-loop backstop's own handler re-enters the failing metrics sink; one datagram terminates the gateway.
  **Location:** `gateway/src/gateway.py:2008` (handler), `:464-468` (`MetricsLogger.write`), `:2022-2025` (`__main__` wrapper).
  **Evidence:** The backstop comment at `:1850-1862` states that no datagram "may terminate the gateway for every producer behind it." The handler at `:2006-2014` calls `metrics.record_drop("INTERNAL_ERROR")` and `metrics.maybe_log()`; `record_drop` reaches `_log_event` (`:293-299`) which calls `MetricsLogger.write` — unguarded `Path.mkdir` + append. When the metrics sink is what failed inside the `try`, the identical exception is raised from inside the `except` and is caught by nothing. The `__main__` wrapper catches only `KeyboardInterrupt`.
  **Reproduction:** Start the gateway with `--metrics-log-path` under a path whose parent is a regular file, then send one malformed datagram. Observed end to end: `process_message` → `metrics.record_violation('SCHEMA_INVALID')` → `MetricsLogger.write` → `Path.mkdir` → `FileExistsError`; the backstop catches it; then `File gateway.py, line 2008, in main / metrics.record_drop("INTERNAL_ERROR")` raises the same `FileExistsError` uncaught. `subprocess.wait()` returns 1 within seconds of the first datagram.
  **Impact:** The single guarantee the backstop was added to provide does not hold once the observability sink degrades — which is exactly when an edge node is already under stress (disk full, read-only remount, log directory removed, permissions changed). The failure is silent to operators, because the log they would read is the broken one, and it takes out translation for the whole node rather than one producer. Fix: wrap `MetricsLogger.write` so I/O failure degrades to a one-shot stderr warning, and never call back into metrics from inside the backstop's handler.
  *One refutation vote, on the contrivance of the filesystem state. The re-entry is structural, not contrived: every real cause of a failing log sink produces it on the next violation, drop, warning, oversize datagram, send failure, or timing-quality record.*

- **A-04 (MAJOR, fail-closed/honesty):** Compact egress raises a raw `RecursionError` instead of refusing — a recursive pre-check sits in front of the guard added in the same commit to catch it, and the range's own new normative spec text asserts the guarantee.
  **Location:** `zmeta_compact.py:497` (call site), `:439-455` (recursion), `:504` (guard opens), `:509` (`except` naming `RecursionError`), `:514` (`_semantic_difference`, also recursive, also outside).
  **Evidence:** `6ea9888` added both the recursive `_find_unencodable_int` (V2-09) and the `try/except` that converts `RecursionError` into `CompactUnrepresentableError` (V2-01) — and placed the former before the latter. Direct probe on HEAD: a v1.0 STATE_EVENT with `payload.extensions.vendor` nested 300 and 900 deep returns `CompactUnrepresentableError('CBOR nesting exceeds max_depth')`; at 1000+ it raises `RecursionError: maximum recursion depth exceeded`, traceback terminating in `File zmeta_compact.py, line 449, in _find_unencodable_int  [Previous line repeated 994 more times]`. Isolation proof: monkeypatching `_find_unencodable_int = lambda v, path='$': None` and re-running at depth 3000 yields `CompactUnrepresentableError: compact cannot serialize this event (RecursionError: ...)` — i.e. the guard would work. The escape is not caught downstream: `gateway.py:722-725` `_COMPACT_UNREPRESENTABLE` lists only `CompactUnrepresentableError`. The module docstring at `:476-486` promises the opposite by name, citing extension nesting as its example. `spec/compact-binary-mapping.md`, added in this range, now normatively requires refusal with `CompactUnrepresentableError`. The existing regression test pins depth **300** — above `zmeta_cbor`'s `max_depth` 64 but far below the ~990 needed to reach the pre-check; the sibling guard test for `_find_forbidden_key` uses 100,000.
  **Reproduction:** `zmeta_compact.dumps(ev)` with 1500 levels of `payload.extensions.vendor` → `RAW RecursionError`. `json.loads` accepts 3000-deep input and an 11 KB datagram fits well under the 65507-byte UDP limit, so this reaches the gateway over the ordinary JSON wire. Live gateway run (`--profile H --output-encoding compact`): the shallow unrepresentable event (`2**70` in extensions) correctly produced a forwarded `ENCODING_UNSUPPORTED` diagnostic; the deep-nesting event produced **nothing** forwarded and `WARNING: datagram dropped after unexpected RecursionError` on stderr, counted as `INTERNAL_ERROR`.
  **Impact:** (1) Honesty — the downstream consumer receives silence instead of the governed `ENCODING_UNSUPPORTED` refusal every other unrepresentable event produces, and an operator filtering `drop_reasons` for encoding refusals never sees this bucket. Resilience becoming concealment, which is exactly what the backstop scope tests were written to prevent. (2) Fail-closed contract — any caller of the documented public API that handles only `CompactUnrepresentableError`, which is what the module *and the new normative spec text* tell them to handle, crashes instead: `tools/convert_encoding.py:110`, `tools/measure_packet_size.py:67`, and any third-party encoder. Cutting v1.1.17 would publish a normative guarantee the reference implementation does not keep. Fix is mechanical: move both pre-checks inside the existing `try` (or make `_find_unencodable_int` iterative as `_find_forbidden_key` already is) and re-pin the test above `sys.getrecursionlimit()`.
  *This also falsifies one of the three results in the record's closing live re-probe (`docs/r1_11_full_stack_audit.md:549-552`), which reports the 300-deep nest producing an honest in-band diagnostic. It does — at 300. The probe was run below the interpreter limit.*

- **A-05 (MAJOR, authorization/availability):** `require_match_for_event_types` receives no lint validation at all — a bare YAML key drops 100% of traffic, a scalar silently opens the gateway to unregistered producers.
  **Location:** `gateway/src/validators.py:2374-2378` (unguarded iteration), `:1280-1282, 1356-1360` (lint checks names only), `:2380-2389` (the refusal that can no longer fire).
  **Evidence:** `validate_producer_authority` builds the require-match set by iterating `authority_policy.get("require_match_for_event_types", [])` with no type guard; `lint_producer_authority_structure` diffs only the top-level key *names* against `_PRODUCER_AUTHORITY_TOP_KEYS` and never inspects this key's value. Two scratchpad copies of `policy/`, each one line from the shipped file: **(a)** the six list items removed, leaving a bare key — `python tools/lint_policy_risk_modes.py --policy-dir <copy>` → `policy risk mode lint ok`, exit 0; `load_policy` yields `None`; `validate_producer_authority` on any event raises `TypeError: 'NoneType' object is not iterable`. **(b)** `require_match_for_event_types: STATE_EVENT` — lint exit 0; a schema-valid STATE_EVENT from producer `totally-unregistered-node`, matching no pattern under `producers:`, returns `(True, [])`. The same event against the shipped policy returns `(False, [PRODUCER_NOT_ALLOWED])`.
  **Reproduction:** As above, verbatim, against a copy of `policy/`. No repo file was touched.
  **Impact:** Case (a) is a silent total outage no gate detects: the lint is clean, the policy loads, the gateway binds, and every producer behind it goes dark — the receive-loop backstop at `gateway.py:2006` converts the `TypeError` into an `INTERNAL_ERROR` drop naming no policy problem. Case (b) is an authorization bypass: the require-match backstop is the only control between an unregistered or spoofed producer and the six event types the shipped policy lists (OBSERVATION/INFERENCE/FUSION/STATE/COMMAND/SYSTEM), and one scalar disables it for all six while the lint reports the policy healthy. The structure lint was added in this very range because "a typoed key or a deleted promotion sub-block silently disables enforcement while every gate stays green" (`validators.py:1276-1279`) — this key sits inside the block that lint guards and receives no value validation whatsoever.
  *One refutation vote, arguing the mangles are implausible operator errors. The counter is that the lint's own stated purpose is to catch implausible-looking YAML mistakes, and it catches strictly weaker ones today.*

#### MODERATE

- **A-06 (MODERATE, honesty/fielded safety):** The MAVLink state template zero-fills a missing altitude into canonical geo and labels it AVAILABLE — a contract 6.8 MUST violation, in the class this same cycle closed in two sibling adapters.
  **Location:** `adapters/ingress/mavlink/mavlink_to_zmeta_template.py:135` (`alt_m = _get("alt_m", 0.0)`), `:144` (`speed_mps` default), `:158` (written into `payload.geo`), `:244` (`speed_mps` written unconditionally).
  **Evidence:** `spec/semantics-contract.md:924` is an explicit MUST the other way: "If any of `lat`, `lon`, or `alt_m` is missing, omit geo entirely. Missing values MUST be omitted, not zero-filled," and `:928` "Adapters MUST NOT emit zero-filled geospatial data to satisfy schema shape." Live probe: `translate_platform_state({'lat': 34.05, 'lon': -118.24, 'gps_fix_type': 3, ...})` with no `alt_m` prints `{'lat': 34.05, 'lon': -118.24, 'alt_m': 0.0} 0.0 AVAILABLE 0.8`. The event passes jsonschema, `validate_producer_authority → (True, [])`, and `validate_semantics → (True, [])` at profile H. The contract-6.8 warn heuristic at `validators.py:1854-1874` fires only when BOTH `lat == 0.0` and `lon == 0.0`, so a real position with a fabricated altitude raises nothing — and that block's own comment at `:1851-1853` asserts "The same ambiguity is handled at ingress by the MAVLink adapter's refuse-to-fabricate rule." The adapter refuses null-island lat/lon (`:153-156`) but not the altitude. This is the only surviving `alt_m` zero-fill default in `adapters/`: `git grep 'get("alt_m"'` shows cot/jreap/klv/sapient using plain `.get()` with `None` handling. The held range removed exactly this shape from signalhunter (`e3203ad`, with the comment "a fabricated 0.0 — even an unconsumed one — is the zero-fill class") and R1-10 closed it in moth (`moth_to_zmeta.py:441` now requires lat AND lon AND alt_m) — and `e3203ad` edited this very file without touching line 135.
  **Reproduction:** Call `translate_platform_state()` with any state dict omitting `alt_m` — a GPS_RAW_INT-only feed, or a decoder that drops altitude when the MAVLink alt field is flagged invalid, both documented as optional inputs by the module docstring at `:96-107`.
  **Impact:** An airborne UxS reporting no altitude is projected to every consumer as being at exactly 0 m, labelled AVAILABLE at confidence 0.8, passing every gate with no warning. Downstream CoT/SAPIENT egress re-projects that `0.0` as a concrete altitude claim — the CoT unknown-value `9999999.0` convention triggers only when `alt_m` is `None`, which it never is here. Deconfliction, terrain masking and 3D fusion all consume the fabricated axis. Fielded-safety class, in a template the repo presents as production-ready, and the exact class this cycle closed twice elsewhere. The same line also defaults `speed_mps` to 0.0, asserting "stationary" for a platform whose speed was never reported.
  *One refutation vote. The structural half was independently re-verified read-only: line 135 is `alt_m = _get("alt_m", 0.0)`, and the comment at `:136-142` explains at length why heading is NOT defaulted, in the same breath as altitude being defaulted.*

- **A-07 (MODERATE, honesty/laundering):** The promotion structure lint checks key NAMES but not value TYPES, so one plausible YAML edit disables the promotion evidence gate with lint, pytest and the bad-events corpus all green.
  **Location:** `gateway/src/validators.py:1370` (the name check), `:1376-1378` (the stated rationale), `:1379-1428` (the three type-checked sub-blocks), `:798-800` (the silently-defaulting read).
  **Evidence:** The lint type-checks exactly `degrade`, `quarantine`, `use_limits`, on the rationale stated at `:1376-1378`: "A sub-block of the wrong TYPE is the same failure as a typo: the enforcement reads it with `.get()` and falls back to its built-in default, so it must fail the lint rather than be skipped over." That rule is applied only to the three keys controlling how much to SOFTEN an event and to none of the keys that decide whether it is REFUSED. Ran the SHIPPED gate on a copy of `policy/` whose only edit flattens `required_fields_by_profile` from a per-profile map into one flat list: `python tools/lint_policy_risk_modes.py --policy-dir <copy>` → `policy risk mode lint ok`, exit 0. Against that policy, `validate_producer_authority` on a schema-valid STATE_EVENT from `cot-ingress` carrying `external_promotion = {"state_category": "PROMOTED_EXTERNAL_STATE"}` and nothing else returns `(True, [])` — accepted with no `trust_ref`, no `lineage_status`, no `loop_status`, no `source_event_uid`, no `freshness_ms`, no `confidence_basis`. The same event against the shipped policy returns `PRODUCER_NOT_ALLOWED` with all nine missing. All four `conformance/bad-events/must-fail.jsonl` external-state cases still fail as expected, so the corpus is not a tripwire either.
  **Reproduction:** `cp -r policy/ <scratch>`; replace the `required_fields_by_profile` L/M/H map with a flat list of the same field names; run the lint (exit 0) and then `validate_producer_authority` on the minimal promotion event (returns `(True, [])`).
  **Impact:** Fail-OPEN, in the direction that matters. A single plausible YAML edit — writing a flat list where a by-profile mapping is expected — turns an external CoT/JREAP/MAVLink/SAPIENT track into an authoritative ZMeta STATE_EVENT with no trust anchor, no lineage status, no reflection verdict and no freshness bound, while the deployment-time lint the repo's own docs point operators at (`README.md:312`, `policy/README.md:86`, `configs/README.md:44`, `spec/installation-guide.md:70`) prints "ok". Design gate 3: externally-promoted data is made to look clean and the operator gets a green light saying so.
  **Scope, honestly bounded:** a broader version of this claim was **refuted 2/3** and the refutation is load-bearing. Of 14 keys probed, 13 leave the event REJECTED when mistyped — `_list_values` coerces a stray string into a one-element allowlist, which *tightens*; `enabled`, `always_reject_loop_risk`, `metadata_path` and `required_state_category` all fail closed; and several are booleans or strings by design, where a mapping type-check would be incoherent. Omitting the key entirely, or writing `required_fields_by_profile: {}`, is design-legal and lints green on purpose (`test_policy_risk_mode_lint.py:226-230`). What survives is narrower and real: the three mapping-shaped keys (`required_fields_by_profile` `:798`, `allowed_lineage_status_by_profile` `:833`, `max_freshness_ms_by_profile` `:970`) revert to `{}` on a wrong-typed value, and the flat-list mistake is a plausible operator error that fails open with a green lint. That is outer-ring lint hardening (design gate 6), not a defect in the shipped policy — which enforces correctly, with `_profile_for_event` defaulting to the strictest profile H.

- **A-08 (MODERATE, interoperability):** The CBOR decoder silently strips tags, maps `undefined` to null and coerces simple values to ints, and the normative mapping spec states no rule — so one compact packet means different things on two implementations.
  **Location:** `zmeta_cbor.py:184-186` (tag transparency), `:265-266` (`undefined` → None), `:267-269` (simple value → int); `zmeta_compact.py:618-624` (`_decode_cbor` prefers `zmeta_cbor`).
  **Evidence:** `_decode` treats CBOR major type 6 as transparent — reads the tag number, discards it, returns the tagged item. A standards-conforming library does none of these three things. `cbor2` is installed alongside, so the divergence is directly demonstrable: `zmeta_cbor.loads(bytes.fromhex('c24105'))` → `b'\x05'` while `cbor2.loads` → `5`; `c101` → `1` vs `datetime(1970,1,1,0,0,1,tzinfo=utc)`; `f820` → `32` vs `CBORSimpleValue(32)`. End-to-end: take the shipped Profile-L TRACK_STATE, encode compact, replace the `valid_for_ms` value bytes with the tag-2 bignum encoding of 1000 (`c2 42 03 e8`) — `zmeta_compact.decode_event(zmeta_cbor.loads(wire))` yields `valid_for_ms = b'\x03\xe8'` and `validate_schema` → `ok=False`, while `decode_event(cbor2.loads(wire))` yields `1000` and `ok=True`. Same bytes; one node rejects the event, the other accepts it as fully valid. `spec/compact-binary-mapping.md` contains zero occurrences of "tag", "simple value", "undefined" or "bignum", so its MUST-be-refused enumeration at `:39-48` gives an independent implementer no rule. `zmeta_compact.py:19-25` states the governing invariant explicitly — "Two conforming nodes must never disagree about what an event means" — and enforces it on the encode side by hard-coding the CBOR 64-bit range rather than delegating to the backend. The decode side has no counterpart.
  **Reproduction:** `python -c "import zmeta_cbor, cbor2; b=bytes.fromhex('c24105'); print(repr(zmeta_cbor.loads(b)), repr(cbor2.loads(b)))"` → `b'\x05' 5`.
  **Impact:** The compact mapping's stated reason for existing is that a packet means one thing everywhere. A nonconforming or hostile sender can craft a Profile-L packet that a `zmeta_cbor` gateway drops as schema-invalid and a standards-library gateway forwards as a valid track, or vice versa — a silent partition of the fleet, invisible to every gate. **Scope, honestly bounded:** a related MAJOR framing was **refuted 2/3**. The reference stack ships `zmeta_cbor` and prefers it, so two copies of the reference gateway never disagree; on every *typed kernel* field the schema catches the type mismatch and the gateway emits an honest `SCHEMA_INVALID`; the only case where both backends accept with different values is inside `payload.extensions.*`, which the schema declares `additionalProperties: true` — namespaced vendor space the kernel deliberately does not interpret. So this bites third-party implementations built from the spec, which is the population the standard exists to serve, and it does not launder any kernel semantic. Per design gate 6 the remedy is a documentation-of-an-existing-rule change to a governed `spec/` artifact plus optional decoder strictness — **escalate to the maintainer, do not treat as ready.**

- **A-09 (MODERATE, release integrity):** A `formal_release` manifest passes validation while carrying the reference-baseline `release_id`, `release_name` and `release_date` — and the new spec text says the validator prevents exactly this.
  **Location:** `tools/validate_release_manifest.py:128-152` (the coherence block), `spec/release-hash-policy.md:172, 181-183` (the claim).
  **Evidence:** The R11-10 coherence block added in this range checks two things: that `branch` is not the placeholder, and that the `notes` list does not contain the literal "not a formal tagged release". The identity fields are never checked against `release_status`, so a manifest declaring `release_status: formal_release` while calling itself `zmeta-reference-hardening-baseline-2026-05-07` / "ZMeta Reference Hardening Baseline" / dated `2026-05-07` validates with zero issues. The notes check is additionally incapable of firing on builder output: `tools/build_release_manifest.py:377-385` derives that sentence from `release_status` with a ternary, so the two can never disagree, and any hand edit to `notes` already breaks `release_manifest_hash`, which the same validator recomputes. `spec/release-hash-policy.md:181-183`, new in this range, states: "A formal-release manifest must not carry the placeholder branch and must not self-describe as a non-formal reference baseline — the manifest validator enforces both." Only the branch half is enforced.
  **Reproduction:** Read `validate_release_manifest.py:128-152` against `build_release_manifest.py:16-19` (`DEFAULT_RELEASE_ID = "zmeta-reference-hardening-baseline-2026-05-07"`) and `:377-385`. A cut passing `--release-status formal_release --branch main` but omitting `--release-id`/`--release-date` produces a clean-validating manifest naming the wrong release.
  **Impact:** The one thing R11-10 was raised to prevent — a governed, hash-pinned, signed release artifact making a false claim about which release it is — is half closed, and the new spec text tells the maintainer it is fully closed. The omission class is exactly the one the paragraph warns about. Downstream consumers reading `release_id` to pin a version get the baseline slug and a release date two and a half months stale. Adding the identity checks is a three-line change in the same block; the currently-shipped `notes` check adds no detection capability the hash pin does not already provide.

- **A-10 (MODERATE, fail-closed contract):** SAPIENT state egress raises `ValueError` out of the projection on a pre-1970 `event.ts`, breaking the None contract the same range documented.
  **Location:** `adapters/egress/sapient/zmeta_state_to_sapient_detection.py:271-274` (the guard), `:277` (the unguarded next statement), `adapters/egress/sapient/ulid_util.py:31-32`.
  **Evidence:** The refusal guard added for the `ts` class wraps only `_parse_utc`: `except (ValueError, TypeError): return None`. The very next statement, `ulid_from_ts_ms(round(time_dt.timestamp() * 1000))`, is outside it, and `ulid_from_ts_ms` raises `ValueError('ts_ms out of the 48-bit ULID timestamp range')` for any negative epoch-ms (`if not 0 <= ts_ms < 1 << 48`). A schema-valid, semantics-clean STATE_EVENT/TRACK_STATE whose `event.ts` predates 1970 therefore raises out of the public entry point. `adapters/egress/sapient/README.md:86-88`, added in this same range, asserts the opposite: "Malformed fields (unparseable `ts`, ...) — refused per the None contract, never raised and never projected", and the function's own comment at `:267-270` repeats it.
  **Reproduction:** Call `zmeta_state_to_sapient_detection` with a valid TRACK_STATE whose `event.ts` is `1969-12-31T23:59:59.500Z` — a schema-valid instant the compact codec's own test family (`test_compact_fail_closed.py:503`) treats as in-scope.
  **Impact:** Pre-epoch timestamps are the canonical bad-clock symptom on unsynced edge nodes. There is no gateway backstop here — this adapter is not called from the receive loop, so exposure is to embedders (the fielded praesens stack, conformance tooling, any caller following the adapter README), which are told to handle a `None` return and get an unhandled traceback. The failure lands precisely on the degraded-timing events whose export honesty this adapter exists to preserve. This is the identical guard-placed-in-front-of-the-raising-call shape as A-04 — the cycle's own recorded residue lesson, in a second file.

- **A-11 (MODERATE, honesty across the projection boundary):** SAPIENT egress emits a literal `NaN` inside the `zmeta.timing_quality` honesty label — the one channel that carries degraded-timing honesty across the coalition boundary.
  **Location:** `adapters/egress/sapient/zmeta_state_to_sapient_detection.py:347` (the `json.dumps`), `:344` (the `sync_state != 'LOCKED'` condition).
  **Evidence:** The same fix wave added `_is_finite_number` to three sinks in this file — geo `:248`, confidence `:296`, heading/speed `:309` — and left the `zmeta.timing_quality` object_info self-label a verbatim `json.dumps(timing_quality, ...)` with Python's default `allow_nan=True`. Ran the real adapter: a STATE_EVENT/TRACK_STATE with finite geo, ULID track_id, and `payload.timing_quality = {time_source: NTP, sync_state: HOLDOVER, est_error_ms: nan, last_sync_ts: ...}` is clean on the ZMeta side (`iter_errors` → none; `validate_semantics` → `(True, [])`, because the R11-04 guard covers only `confidence` and `payload.claim.confidence`). The adapter then returns a message whose `detection_report.object_info` is `[{'type': 'zmeta.timing_quality', 'value': '{"est_error_ms":NaN,"last_sync_ts":"...","sync_state":"HOLDOVER","time_source":"NTP"}'}]`. `json.dumps(out, allow_nan=False)` on the whole message **succeeds** — the NaN is escaped inside a string — while strict re-parse of the label value raises on the constant. The sibling label built six lines earlier shows the asymmetry: `zmeta.risk` at `:337-341` dumps records built by `_risk_label_entry` (`:163-169`), which copies only the six string/list keys in `_RISK_LABEL_KEYS` and `str()`-coerces the lists, so no float can enter it. The timing label alone is a verbatim pass-through of an event sub-object. The new egress test `test_state_non_finite_values_refuse` covers heading, geo and confidence only; the ingress point-of-use pin reads `sapient_to_zmeta.py` and does not see egress at all.
  **Reproduction:** As above; `out['detection_report']['object_info'][0]['value']` → `{"est_error_ms":NaN,...}`; `json.dumps(out, allow_nan=False)` succeeds; `json.loads(value, parse_constant=lambda c: 1/0)` blows up.
  **Impact:** The `sync_state != 'LOCKED'` condition means this label exists only when timing IS degraded — the exact events the channel exists to keep honest. A strict SAPIENT consumer rejects or drops the label and sees a detection with no degradation notice: silent laundering across a lossy projection, design gates 3 and 4. A Python-tolerant consumer carries NaN forward. Because the corruption is string-internal, neither the outer `allow_nan=False` idiom used throughout the ingress tests nor the ingress point-of-use pin can detect it.

- **A-12 (MODERATE, release-state divergence):** The manifest at HEAD identifies as `zmeta-v1.1.16` while carrying regenerated hashes that diverge from the published v1.1.16 assets — the cut must resolve this.
  **Location:** `release/zmeta-release-manifest.yaml:1-6`; recorded at `docs/zmeta_refinement_worklog.md:46-52, 286-292`; pre-adjudicated at `AGENTS.md:130-138`.
  **Evidence:** The manifest at HEAD declares `release_id: zmeta-v1.1.16`, `release_status: formal_release`, `release_date: '2026-07-21'` while its content hashes were regenerated twice since publication — once on `origin/main` (by P1-09) and again across the held range. Three distinct manifest states now exist under one identity. `python release/sign_release_artifacts.py --version v1.1.16 --verify-checksums` exits 1 on exactly one line: `zmeta-release-manifest.yaml expected 96c4e51a… got f19396d5…`. The published pin corresponds to the v1.1.16 **tag blob** with CRLF endings (sha256 of `git show v1.1.16:release/zmeta-release-manifest.yaml` normalized to CRLF == `96c4e51a…`), confirming the pin was computed over the tagged manifest. The other six pinned assets (all four zips, the release notes, the validation report) still verify clean, so anyone verifying the *published GitHub assets* is unaffected; only in-repo verification of the manifest breaks. The in-repo `release/package-v1.1.16/` directory has ALSO been regenerated: it is gitignored (`.gitignore:223`), so `git diff` over it is vacuous, but unzipping the published `zmeta-release-package-v1.1.16.zip` and comparing byte-for-byte shows 3 of 4 files differ (ATTESTATION.yaml, SHA256SUMS.txt, zmeta-release-package.yaml), with seven category hashes changed and `known_open_issues` moved from "D-003 OPEN" to `[]`. The zip itself is stale but intact — `release/sign_release_artifacts.py:69-81` never overwrites an existing zip by design.
  **Reproduction:** `python release/sign_release_artifacts.py --version v1.1.16 --verify-checksums` → exit 1, one mismatch line.
  **Impact:** This is lawfully pre-adjudicated (`AGENTS.md:130-135` states the divergence is expected and "resolution is the next release cut") and correctly recorded, so it is not a governance breach — but it is the state the release decision must clear, and nothing in the tree yet performs the resolution. Resolution requires a genuine cut, not an edit: rebuild the manifest under a NEW identity, author `release/RELEASE_NOTES_v1.1.17.md`, convert the CHANGELOG `[Unreleased]` HOLD block, run the doc-currency pass, build the package **with** `--release-notes`, and re-validate against the real package directory. `release/SHA256SUMS_v1.1.16.txt` must **never** be rewritten; the divergence resolves by publishing a NEW `SHA256SUMS_v1.1.17.txt`, and `gateway/tests/test_published_checksums_immutable.py` now enforces that. See §7.

#### MINOR

- **A-13 (MINOR, record accuracy):** The change inventory added by the final closeout commit states a diff size and commit counts that the same commit falsified — the fifth recurrence of the class checklist item 5 exists to catch.
  **Location:** `docs/r1_11_full_stack_audit.md:655`, `:687`, `:721-723`; copies at `docs/zmeta_refinement_handoff.md:39` and `docs/zmeta_refinement_worklog.md:24`.
  **Evidence:** Line 655 pins the surface as "77 files, +4802 / −392 across origin/main..HEAD". Measured: `git diff --shortstat origin/main..HEAD` → **77 files changed, 4920 insertions(+), 392 deletions(-)**. `git diff --shortstat origin/main..aefafc7` → 4802 — i.e. the figure was measured before `eb41794` (+123/−5) landed, and `eb41794` is the commit that wrote it. `git log -S"4802"` names `eb41794` as the sole introducing commit for all three copies. Per-file commit counts: `docs/r1_11_full_stack_audit.md` = 11 (line 721 says 10), `zmeta_refinement_worklog.md` = 8 (says 7), `zmeta_refinement_handoff.md` = 6 (says 5); CHANGELOG = 5, correct. `git diff --name-only origin/main..HEAD -- adapters/ingress/sapient adapters/egress/sapient` lists 7 files; line 687 says 6. `eb41794`'s own message asserts "Verified before committing: the 77/+4802/-392 figure." The file count (77), the deletion count (−392), the regenerated-artifact counts (manifest 8, each claims file 8) and the pytest ground truth (785 + 316) all reproduce exactly.
  **Reproduction:** `git diff --shortstat origin/main..HEAD; git diff --shortstat origin/main..aefafc7; git log --oneline origin/main..HEAD -- docs/r1_11_full_stack_audit.md | wc -l`.
  **Impact:** The section explicitly tells the fresh auditor "The audit validates against the diff, so this is the map of it" and supplies the command. An auditor running that command gets a 118-line insertion mismatch and must rule out a smuggled change before proceeding. This is the third recurrence *within the held range alone* of the class that `8d64cb6` ("The closeout commit immediately falsified its own count") and `3bc37c7` ("the same defect class a third time") were written to eliminate, and it defeats the self-verifying-range discipline `8d64cb6` introduced. Three sections earlier the same document warns against exactly this at `:618-620`, then hardcodes the count anyway. The structural fix is to derive the number at read time from `git diff --shortstat` rather than freeze it into prose.

- **A-14 (MINOR, crash class in a public API):** Unhashable promotion metadata values crash `validate_producer_authority` with an unhandled `TypeError`, and the repo's own SAPIENT ingress adapter can emit the crashing shape.
  **Location:** `gateway/src/validators.py:826` (`origin_kind`), `:840` (`lineage_status`), `:874` and `:907` (`loop_status`), `:925` (`promotion_policy_id`), `:934` (`projection_id`), `:943` (`confidence_basis`).
  **Evidence:** `_validate_external_state_promotion` tests producer-controlled metadata values for membership in Python sets. `payload.extensions` is free-form in both schemas (`additionalProperties: true`, no type constraint on `external_promotion` or its members), so any of these values may legally be a list or a dict, and `<list> not in <set>` raises `TypeError: unhashable type`. The guard produces no violation — it raises out of the public API. Seven schema-valid STATE_EVENTs from `cot-ingress`, each identical to the passing reference promotion except one metadata value wrapped in a list (or a dict for `loop_status`): `validate_schema` → `True` for all seven; `validate_producer_authority` → `TypeError` for all seven. In-repo path: `sapient_to_zmeta.py:750` type-checks only `loop_status` and name-checks the remaining caller keys at `:771-784` without validating their types, then merges them verbatim at `:796`. Calling the shipped adapter's `translate()` with `promotion={"loop_status": "CHECKED_NOT_REFLECTION", "origin_kind": ["EXTERNAL_REPORT"]}` emits a STATE_EVENT that passes `validate_schema` and then raises at `validators.py:826`.
  **Reproduction:** Build the reference `cot-ingress` promotion event from `gateway/tests/test_external_state_promotion.py::promotion_metadata`, set `metadata["origin_kind"] = ["EXTERNAL_REPORT"]`, confirm `validate_schema → (True, [])`, then `validate_producer_authority(...)` → `TypeError: unhashable type: 'list'`.
  **Impact:** Inside the reference gateway the receive-loop backstop contains it, so the process survives — but the datagram is dropped as `INTERNAL_ERROR` instead of producing the honest `PRODUCER_NOT_ALLOWED` violation event. The operator sees a gateway bug rather than a refused promotion, which is the wrong diagnostic for a promotion refusal and hides the laundering attempt. Any caller of the public `validate_producer_authority` API outside that backstop — conformance tooling, embedders such as the fielded praesens stack — gets the raw traceback. This is the crash class R1-11 verification pass 2 closed twice elsewhere (`_find_forbidden_key` recursion, `sendto` OSError), surviving inside the promotion guard itself.

- **A-15 (MINOR, lint correctness / inverted message):** The structure lint rejects `allowed_event_subtypes` — a producer-entry key the enforcement reads and honours — with a message that tells the operator to delete a control that is in force.
  **Location:** `gateway/src/validators.py:1283-1285` (`_PRODUCER_ENTRY_KEYS`), `:1440-1444` (the flagging loop), `:2406-2409` and `:2439-2451` (the enforcement that reads and honours the key).
  **Evidence:** `validate_producer_authority` reads `rule.get("allowed_event_subtypes")` and enforces it ("event_subtype not authorized for producer"). `_PRODUCER_ENTRY_KEYS` lists only `{allowed_event_types, forbidden_event_types, external_state_promotion}`, so the producer-entry loop flags `allowed_event_subtypes` as "unknown producer entry key: a typo here silently disables enforcement" — the opposite of the truth. Added `allowed_event_subtypes: [TRACK_STATE]` to the `cot-ingress` entry of a scratchpad copy: `python tools/lint_policy_risk_modes.py --policy-dir <copy>` → `FAIL code=POLICY_PRODUCER_AUTHORITY_STRUCTURE path=producer_authority.producers.cot-ingress.allowed_event_subtypes ... unknown producer entry key`, exit 1. With the same policy in memory, a STATE_EVENT from `cot-ingress` with `event_subtype="OTHER_SUBTYPE"` is refused with "event_subtype not authorized for producer" — the key demonstrably works. `policy/README.md:38` documents `allowed_event_subtypes` as established producer-rule vocabulary (for `routing.yaml`), so an operator mirroring it into `producer-authority.yaml` is following the repo's own documented shape.
  **Reproduction:** As above, against a copy of `policy/`.
  **Impact:** The lint fails a legal, working policy and tells the operator the control is a typo that "silently disables enforcement". The remedy the message prescribes — delete the key — removes a subtype restriction that was actually in force, so the lint actively converts a correct configuration into a weaker one. It also proves the allowlist was derived from the promotion code path rather than from the full set of keys `validate_producer_authority` reads, which is the same drift the lint exists to detect.

- **A-16 (MINOR, diagnostic coverage):** `BEARING_FRAME_UNLABELED` is blind to `payload.estimated_state.bearing`, the fused-bearing path the check matters most for.
  **Location:** `gateway/src/validators.py:1884` (`bearing = payload.get("bearing")`), `:1883-1899` (the check), `:1855-1858` (the adjacent geo check, which does walk two paths).
  **Evidence:** Both schemas declare a second canonical bearing at `$defs/FusionPayload/properties/estimated_state/properties/bearing`, the same `$ref: "#/$defs/bearing"` with the same optional `frame` key (verified by loading both schemas). Live probe against `schema/zmeta-event.schema.json` + `policy/`: a v1.0 FUSION_EVENT with `payload.estimated_state.bearing = {"az_deg": 137.0}` → schema errors 0, `sem_ok=True`, violations `[]`; the byte-identical bearing at `payload.bearing` → `[('BEARING_FRAME_UNLABELED', 'warn')]`. Same result on the v1.1.0 corpus. INFERENCE_EVENT is unaffected (its `estimated_state` is already rejected by `INFERENCE_HAS_FUSION_STATE`), so FUSION_EVENT is the live surface. `gateway/tests/test_bearing_frame_warn.py` contains no occurrence of `estimated_state` or `FUSION`, so the gap is untested. The same blind spot exists in `GEO_ZERO_FILL_SUSPECTED`, which covers `payload.geo` and `payload.claim.geo` but not `payload.estimated_state.geo`.
  **Reproduction:** Take the FUSION_EVENT from `examples/zmeta-v1.1-examples.jsonl`, set `payload.estimated_state.bearing = {'az_deg': 45.0}`, run `validate_semantics` — only `LINEAGE_PARENT_UNRESOLVED`. Move the identical bearing to `payload.bearing` — `BEARING_FRAME_UNLABELED` appears.
  **Impact:** The check exists to make the assertively-labeled vs legacy-unlabeled distinction machine-visible and filterable (design gate 3). For fused tracks — the promoted, downstream-consumed state estimate, furthest from the sensor that knew the frame, and the one a consumer is most likely to act on — the distinction stays invisible, and the check's *presence* on observations makes its absence on fusion read as an assertion that the fused bearing WAS labeled. Impact is capped: no adapter and not the reference CoT egress reads `estimated_state` (grep over `gateway/src/gateway.py` and `adapters/egress/`), so this is a diagnostic-coverage gap rather than a live mislabel in a shipped projection. Not a regression — the check is new — but it ships incomplete relative to the schema surface it claims to cover. Fix: iterate bearing candidates the way the geo checks iterate geo candidates, and report the actual path rather than the hardcoded `'payload.bearing'` string at `:1895`.

- **A-17 (MINOR, stale worked command):** V2-13's fix breaks the build-then-validate sequence documented in the installation guide and README; only `RELEASE_CHECKLIST` was updated.
  **Location:** `spec/installation-guide.md:222-223`, `README.md:464`; the fix at `RELEASE_CHECKLIST.md:31-37`.
  **Evidence:** The installation guide presents a paired build-then-validate sequence under "local verification". After V2-13, running it exactly as written cannot succeed: the build command passes `--release-state formal_release` but not `--release-notes`, so `tools/build_release_package.py:255` copies the unpopulated template as the package's `RELEASE_NOTES.md`, and the very next line's validator rejects it. Witnessed live against the existing template-notes package (read-only, no build run): `python tools/validate_release_package.py --manifest release/zmeta-release-manifest.yaml --package-dir release/package-v1.1.16` → `FAIL RELEASE_PACKAGE_NOTES_PLACEHOLDER item=release\package-v1.1.16\RELEASE_NOTES.md: formal_release package ships the unpopulated release-notes template (found 'explicit_release_input_required')`, EXIT=1. Not masked by the kernel gate: `tools/validate_conformance.py:295-299` calls the package validator with `templates_only=True` and `validate_release_package.py:384-385` returns before the notes check in that mode.
  **Reproduction:** `sed -n '219,225p' spec/installation-guide.md` (the pair, no `--release-notes`); `grep -n 'release-notes' RELEASE_CHECKLIST.md` (the step, on the other surface); then the validator command above.
  **Impact:** A maintainer following the governed installation guide's verification block at release time hits a hard failure with no in-doc explanation. The authoritative `RELEASE_CHECKLIST` does carry the step, so the release itself is guided correctly — this is a stale teaching surface, not a release-integrity hole. Same shape as R11-17/R11-18 (worked commands escaping the currency pins), newly re-created by this cycle's own fix. Fix: append `--release-notes release/RELEASE_NOTES_v<version>.md` to both surfaces.

- **A-18 (MINOR, doc currency regression):** The handoff currency rewrite converted a labelled-historical validation record into a present-tense claim the repo's own release reports contradict.
  **Location:** `docs/zmeta_refinement_handoff.md:772-774`, with the affected block at `:777-798` and results at `:808, 812`.
  **Evidence:** Before (`git show 118f0b9~1:docs/zmeta_refinement_handoff.md`): "Validation for the S1-26 v1.1.12 release preparation on `main` (2026-07-08, Windows, Python — **historical; superseded by the v1.1.13 record above**)". After: "Validation command inventory (run per release; version literals track the release being cut — shown as recorded for the v1.1.12 preparation and **unchanged in shape since**)". That claim is false: the block contains `python tools\validate_future_roadmap.py` (`:782`), which `release/VALIDATION_REPORT_v1.1.16.md` does NOT contain, and lacks `tools/compute_contract_hash.py` and `tools/validate_conformance_classes.py --verify-contract-hash`, both of which the v1.1.16 report DOES contain (the latter twice). `for f in VALIDATION_REPORT_v1.1.13..16; do grep -c validate_future_roadmap $f; grep -c compute_contract_hash $f; done` → 1/0, 1/1, 1/1, 0/2 — the command set changed at v1.1.14 and again at v1.1.16. The results lines below (`465 passed, 110 subtests`; `total=47 passed=47`) are v1.1.12-era and now sit under a header that no longer says "historical"; HEAD is 785 tests / 51 examples.
  **Reproduction:** The grep loop above.
  **Impact:** An agent or maintainer resuming from the handoff and treating the block as the per-release inventory would omit the contract-hash gate that the actual v1.1.16 cut ran — precisely the gate that moved in this cycle when `semantics-contract.md` §5.3 changed. Blast radius is low (the block sits one scroll below a paragraph naming `VALIDATION_REPORT_v1.1.16.md` as authoritative), but a doc-currency sweep replaced a true statement with a false one, which is the failure mode the sweep exists to prevent.

- **A-19 (MINOR, validator completeness):** Package metadata validation compares only 4 of the 7 hash fields the builder writes into it.
  **Location:** `tools/validate_release_package.py:309` (the literal 4-tuple), `tools/build_release_package.py:153-171` (seven fields emitted), `validate_release_package.py:49-61` (`HASH_FIELDS`, eleven, used for the attestation only).
  **Evidence:** `_validate_metadata` iterates `release_manifest_hash`, `release_bundle_hash`, `semantic_contract_hash`, `schema_bundle_hash`. `package_metadata()` also emits `policy_bundle_hash`, `extension_registry_hash` and `conformance_class_manifest_hash`, which are never compared to anything. The attestation check at `:201-209` does cover them, but for `ATTESTATION.yaml` only; a consumer reading `zmeta-release-package.yaml` gets three unverified integrity claims. `_validate_checksums` only proves the file's bytes match its own listed digest, so a wrong value stays consistent once the checksum file is regenerated.
  **Reproduction:** *(structurally confirmed by two lenses; the mutation step was not executed under the read-only mandate.)* In any built package, set `policy_bundle_hash` to `sha256:` + 64 zeros, regenerate `SHA256SUMS.txt` over the three artifacts (the same refresh `gateway/tests/test_release_package.py:52-63` performs), then run the validator: zero issues, exit 0.
  **Impact:** The builder can emit — or a post-build edit can introduce — a package that misdescribes the policy bundle, extension registry, or conformance class manifest it claims to pin, and the validator reports it clean. Bounded, because `ATTESTATION.yaml` ships alongside and IS fully checked, so a divergence between the two files would surface there; but the package metadata file is the one a consumer is most likely to read alone. Fix: reuse `HASH_FIELDS` for both, intersected with the keys the builder writes.
  *One refutation vote. The structural half was independently re-verified read-only.*

- **A-20 (MINOR, doc/code mismatch):** An adapter README row added in this range claims non-finite confidence is never emitted; the shipped adapter emits it in `payload.claim.sub_class`.
  **Location:** `adapters/ingress/sapient/README.md` (the non-finite row); the contradicting code at `sapient_to_zmeta.py:678`.
  **Evidence:** The row reads "Non-finite (NaN/inf) confidence on the wire | refused at the guard (canonical fields) or omitted from native pass-through blocks — **never emitted**". That is false for `payload.claim.sub_class` (see A-02a). The point-of-use pin that guards the vendor blocks (`test_sapient_ingress.py:1112-1126`) regexes only `VENDOR_EXTENSION_KEY:` sites and cannot see this one; the adapter's own `validate()` returns `pass`.
  **Reproduction:** The A-02 probe.
  **Impact:** An adapter README is the surface an integrator consults to decide whether they must add their own non-finite guard downstream. This row tells them the adapter already handles it, on the one field where it does not. The doc claim was added in the same commit family as the guard it overstates, so the range shipped a stronger assurance than the code delivers.

- **A-21 (MINOR, teaching-corpus doctrine):** The v1.1 example corpus was given minted TRUE_NORTH frame provenance to silence a warn introduced in the same commit; the commit's stated justification is falsifiable, and the range's own AUTHORING rule forbids the pattern.
  **Location:** `examples/zmeta-v1.1-examples.jsonl` (the two edited bearings, commit `c1eb9d0`); the rule at `adapters/AUTHORING.md:147-151` (commit `05ad9a8`); the reference adapter at `adapters/ingress/kraken/kraken_to_zmeta.py:35`.
  **Evidence:** `c1eb9d0` introduced `BEARING_FRAME_UNLABELED` (warn) and, in the same commit, edited the only two unlabeled canonical bearings in the shipped corpus so the warn stops firing. Because `tools/validate_examples.py:131-133` converts warnings into failures under `--strict`, and `--strict --require-all` is part of the mandated kernel gate, a check whose documented severity ceiling is warn ("contract 6.4 tolerates legacy-unlabeled v1.0 bearings") acts as a hard gate on the corpus — so the corpus was changed to assert provenance rather than to demonstrate the tolerated legacy case. The commit message justifies the RF edit as "matching the reference adapter it names" (kraken-sdr). That is falsifiable: the kraken adapter emits `quality.bearing_frame = TRUE_NORTH` only on the compensated branch and, on every event unconditionally, emits `features.doa_array_relative_deg` — the array-relative raw angle that is the honesty anchor of the whole convert-or-omit rule. The edited example carries the compensated-branch labels and no `doa_array_relative_deg` at all. It also gains `quality.heading_source: "GPS_COURSE"` for a static ground sensor that reports no heading and no speed. `05ad9a8`, later in the same range, adds the opposite rule to `adapters/AUTHORING.md:147-151`: "never promote it to canonical `payload.bearing` with a minted `TRUE_NORTH` assertion the producer did not make."
  **Reproduction:** Read the `c1eb9d0` diff of `examples/zmeta-v1.1-examples.jsonl` against `adapters/ingress/kraken/kraken_to_zmeta.py:35` and `adapters/AUTHORING.md:147-151`.
  **Impact:** No runtime failure today, which is why this is MINOR — the cost is doctrinal and lands on adopters. The example corpus is the surface `AUTHORING.md` tells adapter authors to pattern-match against, and it now teaches that a bare `bearing_frame: TRUE_NORTH` + `heading_source: GPS_COURSE` stamp satisfies contract 6.4, without the array-relative provenance the reference adapter keeps and without a producer that could have made either assertion. That is the demotion rule the same range wrote down, inverted in the corpus. Secondary and more structural: because `--strict` promotes warnings to failures, no shipped example can ever demonstrate the legacy-unlabeled bearing contract 6.4 explicitly tolerates, so the warn's documented tolerance is unrepresentable in the teaching corpus, and the only pressure the gate applies is toward stamping a label.

- **A-22 (MINOR, gate 1 / wire cost):** `BEARING_FRAME_UNLABELED` consumes a locked-schema enum entry and a per-event wire diagnostic to publish a fact the consumer already holds, with no operator suppression path.
  **Location:** `gateway/src/validators.py:1890-1899` (emission); `schema/zmeta-event-1.0.schema.json:1590` and `zmeta-event-1.1.0.schema.json:1729` (the closed enum); `gateway/src/gateway.py:1694-1705` (`build_warning_event` materializes it on the wire).
  **Evidence:** The condition — a canonical bearing with no `frame` and no `quality.bearing_frame` — is fully derivable by a consumer from the accompanying event, which it already has. The diagnostic doubles the wire traffic for any producer emitting legacy-unlabeled bearings, and the vocabulary is `warn`, which the reference gateway materializes as a SYSTEM_EVENT alongside the original. There is no `metrics_only` severity: `policy/violation-codes.yaml` uses only `fail`/`warn`, so an operator cannot quiet the code without an undefined value, and `_resolve_severity` correctly fails closed on garbage. The other two new codes are structurally forced: `ENCODING_UNSUPPORTED` reports a wire-level condition no existing code names (using `SCHEMA_INVALID` would misattribute the fault to the producer, since the event IS schema-valid), and `NON_FINITE_CONFIDENCE` reports a value jsonschema cannot see. Neither could be composed from the existing 56-entry vocabulary. This one could have been a metrics counter plus a consumer-side filter.
  **Reproduction:** Emit any legacy-unlabeled v1.0 bearing through the gateway and observe two wire events where one carries all the information.
  **Impact:** Design gate 1, at the margin. This is a genuinely marginal call, not a clear violation: the identical shape already ships as `GEO_ZERO_FILL_SUSPECTED` (an unprovable heuristic at `warn`, materialized on the wire, equally consumer-derivable), which is a real precedent, and the enum entry is *forced* once the decision to materialize warns is taken, because `policy/semantics.yaml:99-101` gates `schema_violation_allowed_reason_codes` and the gateway validates its own diagnostics. Recorded so the maintainer makes the call deliberately rather than by momentum. **This is not a reason to hold the range.** The broader version of this argument — that the warn architecture as a whole is over-costly — was **refuted 3/3**, because it applies equally to twelve codes already shipped on `origin/main`.

- **A-23 (MINOR, hardening):** `write_checksums` has no immutability guard and defaults to the already-published version.
  **Location:** `release/sign_release_artifacts.py:93` (`open(..., "w")`), `:21-32` (`default_version_tag()` resolving `release_id` → `v1.1.16`), `:234` (the argparse help).
  **Evidence:** `write_checksums` opens `SHA256SUMS_{version}.txt` in `"w"` with no existence check; `default_version_tag()` resolves the manifest's `release_id` to the already-published `v1.1.16`; all seven artifacts exist, so the write would succeed.
  **Reproduction:** Not executed (write). Read at the cited lines.
  **Impact:** Small, genuine ergonomic sharp edge — the tool does not refuse when the resolved version already has a release tag, so a maintainer in the post-release window relies on `git status` and the pytest gate to catch a mistyped invocation. **Severity is capped by three real controls, which is why the MAJOR framing was refuted 2/3:** `gateway/tests/test_published_checksums_immutable.py` byte-compares every `SHA256SUMS_v*.txt` against its own tag blob and is part of the mandated pytest gate (it passes; `git diff --stat v1.1.16 HEAD -- release/SHA256SUMS_v1.1.16.txt` is empty); the no-flag invocation exits 1 with "choose at least one action"; and nothing in CI or any Makefile calls the destructive path. The file is git-tracked and tagged, so a rewrite is a visible working-tree modification, revertable, and caught before commit. Also note the range *improved* this area: `545fe0b` added the immutability test.

- **A-24 (MINOR, honesty on the safe side):** `tools/measure_packet_size.py` aborts with a raw traceback on any v1.1.0 corpus; the sibling CLI got the graceful handling in the same cycle and this did not.
  **Location:** `tools/measure_packet_size.py:67`; the sibling fix at `tools/convert_encoding.py:161-163`; the same gap at `tools/replay.py:75`.
  **Evidence:** `_size_compact` calls `zmeta_compact.dumps()` unguarded. Since wave 1 that call refuses any non-1.0 event, so `python tools/measure_packet_size.py --file examples/zmeta-v1.1-examples.jsonl --summary-only` exits 1 with a traceback through `measure_packet_size.py:67 → zmeta_compact.py:536 → :493`, `CompactUnrepresentableError: compact encodes zmeta_version '1.0' events only, got '1.1.0'`. The v1.0 corpus still works (`COMPACT min=248 avg=351.0 max=457`). Every governed invocation (`.github/workflows/ci.yml:93`, `Makefile:28`, every VALIDATION_REPORT) targets `examples/zmeta-profile-L-examples.jsonl`, which is all v1.0 — so no gate or release step is affected.
  **Reproduction:** The command above; `EXIT=1`.
  **Impact:** Cosmetic and fail-closed — the pre-fix behaviour (reporting a compact byte count for an event compact cannot honestly carry) was the dishonest one. Recorded only because it is a measured, anchored inconsistency with a fix the same cycle applied one file over; a two-line `except CompactUnrepresentableError → SystemExit` closes it.

- **A-25 (MINOR, currency guard reach):** The superseded-release matcher only recognises `v`-prefixed lowercase versions, and its own self-test never tries the bare form the repo uses elsewhere.
  **Location:** `gateway/tests/test_release_currency.py:241` (`_SEMANTIC_BRANCH_LITERALS`), `:243-247` (`_NOT_LONGER_VERSION`), `:296-313` (the guard), `:189` (`_stale_version_literals`, which does use `v?`).
  **Evidence:** `re.escape('v1.1.9') + _NOT_LONGER_VERSION` does not match bare `1.1.9` or `V1.1.9`. `README.md:463` and `spec/installation-guide.md:222` both use the bare form (`--version 1.1.16`) — though those sit inside narrowly-scoped blocks already covered by the `v?` helper. Additionally, tags `v1.0.0` and `v1.0.1` have no `release/RELEASE_NOTES_v*.md` file, so `superseded_release_versions()` never enumerates them and a stale claim naming them is invisible to this guard.
  **Reproduction:** Load the test module and evaluate the matcher against `"introduced in 1.1.9"` — no match.
  **Impact:** A defense-in-depth documentation guard with a narrower reach than its assertion message implies. **Severity is capped and the widening is not obviously correct**, which is why the broader framing was **refuted 3/3**: the `v` prefix is the discriminator separating a release pin from the many non-release dotted triples in these docs (`4.5.1` as a contract section number, 12 occurrences family-wide; `translate:kraken@1.0.0` as a vendor semver; `1.1.0` inside schema filenames). Widening would false-positive on `Section 1.1.2` in the very docs it guards. Recorded as a known bound, not as a fix to apply.

- **A-26 (MINOR, guard message vs behaviour):** The published-checksum immutability test's failure message overclaims relative to the floor it enforces.
  **Location:** `gateway/tests/test_published_checksums_immutable.py:32-35` (`glob` + `>= 6` floor + the message), `:37-38` (the derivable tag set, already computed), `:47` (the per-file tag comparison).
  **Evidence:** The compared set is derived from `ROOT.glob("release/SHA256SUMS_v*.txt")` (19 files present), and the only cardinality assertion is a literal floor of 6 — so 13 files could be removed with the message reading "published checksum corpus shrank - investigate". Reproduced by monkeypatching `Path.glob` in a scratchpad runner so the module saw only 6 survivors: the test passed with 13 files simulated as deleted.
  **Reproduction:** As above (no repo file touched).
  **Impact:** A test-message nit with no reachable consequence, which is why the defect framing was **refuted 3/3**. The published pin does not live in the working tree — it lives in the annotated tag (`git show v1.1.16:release/SHA256SUMS_v1.1.16.txt` resolves regardless), and the test itself reads from the tag at `:47`. `AGENTS.md:131-138` prohibits *rewriting*, not removal, and removal destroys no published evidence. The floor is documented at `:9-12` as the tagless/shallow-checkout degradation path, and deriving the expected set from tags while dropping the floor would make the test fully vacuous in exactly that environment. `git log --diff-filter=D` shows no published checksum file has ever been removed across 23 releases. Recorded because the message and the behaviour disagree and the fix is one line using values the test already computes.

- **A-27 (MINOR, coverage):** The R11-14 builder fix has no direct test, and one validator negative branch is unexercised.
  **Location:** `tools/build_release_manifest.py:395` (`"known_open_issues": list(known_open_issues or [])`), `:480-482, 507, 521` (the `--known-open-issue` flag); `tools/validate_release_package.py:214-223` (the mirror check).
  **Evidence:** No test asserts on `build_manifest_data()['known_open_issues']` and no test references the flag; the only builder-output tests are `test_release_manifest.py:78-79` (determinism, both sides change identically) and `:85` (git_commit/branch only). `validate_release_manifest.py:49` is presence-only. The mirror check's negative branch is unexercised: `validate_release_package` returns at `:385-386` under `templates_only`, before `_validate_attestation` at `:396`, so `test_release_package_templates_validate` never reaches it, and the only reaching test builds the attestation from the same manifest, making the comparison tautological.
  **Reproduction:** Grep for `known_open_issues` across `gateway/tests/` and `tools/`.
  **Impact:** Defense-in-depth only, which is why the MODERATE framing was **refuted 3/3**: the harm scenario ("a regeneration silently reintroduces a false open-issue claim") is blocked by `gateway/tests/test_release_manifest.py:104`, which loads `release/zmeta-release-manifest.yaml` — the builder's `DEFAULT_OUTPUT` and the path the documented release command writes — and asserts `known_open_issues == []` unconditionally. Downstream is covered transitively: `build_attestation` sources the field from the manifest only, and the mirror check enforces equality. A test-hygiene backlog item.

#### OBSERVATION

- **A-28 (OBSERVATION, coverage):** Six layers of the cycle's own fix set have no test guarding them, so a silent revert would leave the whole suite green.
  **Location:** the six UNPINNED rows and one ABSENT row of the Step 0 map — `gateway/src/gateway.py:1940-1949`; `spec/compact-binary-mapping.md:22-52`; `release/RELEASE_NOTES_TEMPLATE.md:36-44`; `RELEASE_CHECKLIST.md:31-37`; `spec/release-signing-attestation.md:164-170`; the re-baselined literals in `docs/zmeta_change_governance.md:338`, `TRADEMARK.md:22,24`, `release/sign_release_artifacts.py:231`, and `gateway/tests/test_check_compat_cli.py:139`.
  **Evidence:** Established row by row in the Step 0 map, each by grepping every consumer and test surface. The two that matter most: (a) deleting the `if payload is None` branch and adding any unrelated `record_drop` call leaves the whole suite green, and the datagram then reaches `_check_datagram_size(len(None))` → `TypeError`, which the A-03 backstop converts into a drop recorded as `INTERNAL_ERROR` — no crash, but the operator-facing drop reason silently changes from the honest `ENCODING_UNSUPPORTED` to a generic one; (b) the mapping spec's Scope and normalization-table sections are guarded only by the manifest hash, which is a *currency* pin — delete the section, regenerate the manifest, and the suite is green, while nothing in either direction holds the declared normalization table and the codec's `_semantic_difference` set together.
  **Reproduction:** Per row, in the Step 0 map.
  **Impact:** None today — every one of these layers is correct in the tree at HEAD. It bounds what a green suite proves at the cut: the release battery does not demonstrate that the compact fail-closed boundary is normatively stated, that the honest `ENCODING_UNSUPPORTED` drop reason survives a refactor, or that the release-notes template stays free of retired register claims. Item (b) matters most for the standard, because `spec/compact-binary-mapping.md` is the artifact a third-party implementer reads.

- **A-29 (OBSERVATION, mixed-fleet compatibility):** The three new reason codes are rejected as schema-invalid by any consumer still on the published v1.1.16 schema, and nothing in the held range states it.
  **Location:** `schema/zmeta-event-1.0.schema.json:1590-1592`, `schema/zmeta-event-1.1.0.schema.json:1729-1731`, `policy/violation-codes.yaml:44-49`, `policy/semantics.yaml:100-102`.
  **Evidence:** `reason_code` is a CLOSED enum in the SYSTEM_EVENT metrics block. Verified exhaustively: flattening both schemas at `origin/main` and at HEAD into complete JSON-pointer maps and set-differencing gives **0 pointers removed, exactly 3 added**, all under the `reason_code` enum, every other pointer identical in value; enum arrays 52→55 and 54→57 with `set(old) - set(new)` empty and relative order preserved. `git show origin/main:schema/zmeta-event-1.0.schema.json | grep ENCODING_UNSUPPORTED` returns nothing, so a v1.1.17 gateway emitting that diagnostic produces an event a v1.1.16-pinned consumer rejects. Ordinal safety confirmed: the only integer encoding of reason codes is `REASON_CODE_MAP` at `zmeta_compact.py:246-288`, hand-assigned 1..41 and untouched by the range, with `_map_enum` passing unmapped strings through verbatim — a compact-encoded `ENCODING_UNSUPPORTED` diagnostic round-trips intact. TASK_ACK reason codes were deliberately not widened, pinned by `test_reason_codes.py:171-174`.
  **Reproduction:** Validate a v1.1.17 `ENCODING_UNSUPPORTED` diagnostic against `git show v1.1.16:schema/zmeta-event-1.0.schema.json`.
  **Impact:** **No code defect and no gate breach.** This is the sanctioned Class B additive pattern, pre-authorized at `spec/semantics-contract.md:112-115` — text that shipped at v1.1.14 and is *not* part of this diff, so the cycle follows a precedent rather than writing its own permission slip — and the failure direction is safe (an old consumer discards a diagnostic about an already-rejected event; it never misreads mission data). Recorded because the consequence is stated nowhere in the held range's records, and the v1.1.14 precedent established a Compatibility bullet in the release notes for exactly this case. `release/RELEASE_NOTES_v1.1.17.md` does not exist yet; it **must** carry that bullet, or a mixed-version fleet sees the honest new refusal diagnostics as schema violations — the interoperability promise failing on the very events added to make refusals honest.
  *A stronger version of this — that a forward-compatibility MUST should be added to `spec/profile-compatibility.md` — was **refuted 3/3**: the proposed text would contradict `semantics-contract.md:1315` and the reference validator's deliberate fail-closed rejection of unknown codes.*

- **A-30 (OBSERVATION, audit coverage):** Four changed surfaces had their diffs read by no lens until the critic pass, and four findings live there.
  **Location:** `docs/r1_11_full_stack_audit.md:654-655` (the inventory presenting the 77-file surface as the audit map).
  **Evidence:** Of the 77 changed files, these had their DIFF read by no lens: `examples/zmeta-v1.1-examples.jsonl` (three lenses read it as a probe data source; none looked at what changed — A-21 is here); `adapters/mapping-packs/README.md`; `gateway/tests/test_bad_event_corpus.py`; `adapters/egress/sapient/README.md` (A-10's false claim is here); `adapters/ingress/{cot,jreap,sapient}/README.md` (A-20 is here — the design-gates lens asserted generically that "each adapter README documents the requirement explicitly" without reading them); `adapters/ingress/mavlink/README.md`; `spec/release-hash-policy.md` (one lens read `:155-185` for a different question; the +20/−8 diff was never audited — A-09 is here); `spec/profile-compatibility.md`; `adapters/mapping-packs/sapient-bsi-flex-335/mapping.yaml` (presence-checked only); `release/ATTESTATION_TEMPLATE.yaml` (presence-checked); and the three docs whose only checked change was the one-line release-context header.
  **Impact:** The lens allocation concentrated on the ~15 files with the largest diffs. The small-diff doc and data files are where a claim can be added that the code does not keep, and four of the findings above are exactly that shape. Any future audit of this repo should allocate at least one lens by *claim density* rather than by diff size.

---

### 4. Refuted / not defects

35 candidates were killed. This section is load-bearing: it is the measure of the bar, and several of the refutations changed the shape of findings that survived.

**Killed on the code being correct as designed:**

- *"Formal-release manifest mutated in place under the published v1.1.16 identity; nothing pins it to its tag."* — Refuted 3/3. The published bytes ARE pinned: `release/SHA256SUMS_v1.1.16.txt:5` records the sha256 of the CRLF form of `git show v1.1.16:release/zmeta-release-manifest.yaml`, and that file is byte-compared against its own tag by `test_published_checksums_immutable.py`. The behaviour is the repo's explicit governed procedure (`docs/zmeta_change_governance.md:333-343`), and the implied remedy is impossible — a frozen manifest plus the range's legitimate spec/policy edits would hard-fail `validate_release_manifest`'s recompute pass. `origin/main` already carried the divergence. What survives is A-12: the *resolution obligation*, not a defect.
- *"Reference codec refuses out-of-64-bit integers the mapping spec never says to refuse."* — Refuted 3/3. Conflates silence with permission. The Encoding Rules (`spec/compact-binary-mapping.md:78-230`) enumerate every value representation the mapping defines and define no bignum tag, so an integer carriable only by tag 2/3 is outside the representable set by construction. The MUST-refuse list at `:39` is explicitly non-exhaustive ("including:") and enumerates *loss* classes; an out-of-range integer round-trips value-identically under cbor2, which is precisely why the check lives in the codec rather than the round-trip verifier. Adding an explicit bound to the spec would help a third-party implementer — an OBSERVATION-grade enhancement requiring maintainer escalation, not a release blocker.
- *"6ea9888 rewrites a normative encoding-equivalence rule in `spec/profile-compatibility.md` with no mention in the commit message."* — Refuted 3/3, on four grounds. Wrong commit (`git show 6ea9888 --format="" -- spec/compact-binary-mapping.md` is empty; the substantive change landed in `d955cd0`). Wrong document class (`profile-compatibility.md:1-11` self-declares as a summary deferring to the authoritative page, and the hunk defers twice). The records DO carry it — the evidence grepped for "value-identical" and missed "value-identity" in `CHANGELOG.md:26-32`, the worklog, and the audit record; `6ea9888`'s own message declares the correction at line 188-190. And the governance citation misfires (`profile-compatibility.md` is not in the Class B enumeration).
- *"Promotion-lint type-checking landed for 3 of 9 silently-defaulting global keys."* — Refuted 2/3 as MAJOR, and the refutation reshaped A-07. The headline mechanism ("a single-character typo silently disables the gate") is false — misspellings ARE caught at `validators.py:1370-1375` with a regression test. 13 of the 14 enumerated keys leave the event REJECTED when mistyped; `_list_values` coercion *tightens*; `enabled`/`always_reject_loop_risk` are booleans and `metadata_path`/`required_state_category` strings by design. The 3-of-9 selection is a principled boundary (only those three have a closed sub-key vocabulary the lint enumerates). Decisively, the same permissive outcome is reachable through a design-sanctioned, lint-legal configuration — omitting the key, or `{}` — pinned at `test_policy_risk_mode_lint.py:226-230`, so the structural lint was never the control guaranteeing promoted state carries provenance. A-07 carries only the narrow surviving residue.
- *"CBOR cross-backend decode divergence is unfixed on the ingress path (MAJOR)."* — Refuted 2/3, reshaping A-08. The audit record and CHANGELOG scope V2-09 explicitly and only to encode-side representability; neither claims decode-side closure, so the misrepresentation charge fails. No ZMeta compact producer can emit a tagged frame. On every typed kernel field the schema errors and the gateway emits an honest `SCHEMA_INVALID`; the only both-accept-differently case is inside `payload.extensions.*`, declared `additionalProperties: true`. A-08 carries the surviving interop and spec-silence points at MODERATE.
- *"Compact representability is still install-dependent for nesting depth, message size, item and container size."* — Refuted 2/3. Those four are receive-side DoS knobs, self-declared as such at `zmeta_cbor.py:6-8` and settable per call, not mapping limits. Direction of correctness inverts: a 300-deep extension round-trips value-identically, so the cbor2 configuration is the spec-conformant one and zmeta_cbor *over*-refuses. The failure is loud and fail-closed at the receiver, unlike V2-09's silent bignum-to-bytes. Both test claims in the finding were wrong (the cited test is the V2-01 crash-class test, and 26 of 28 tests in the file do not use the backend helper).
- *"SAPIENT egress exports a PROMOTED_EXTERNAL_STATE as a first-party detection with no provenance self-label."* — Refuted 3/3. Contract §4.5.1 itself distinguishes degrade/quarantine promotions from "a clean promoted state"; the marking obligation attaches to INVALID promotion, and that path is fully wired (QUARANTINE_ACCEPT/REJECTED refuses the export, pinned at `test_sapient_egress.py:305-312`). The drop is the documented uniform disposition across the whole egress family — the module drops all lineage including the `promote:*` transform, with an explicit note. And the proposed fix is self-refuting: the repo's own README states stock DMMs ignore unknown `object_info` types.
- *"CoT egress carries confidence and source_summary only in free-text `<remarks>` (gate 5)."* — Refuted 3/3. `spec/semantics-contract.md:1830-1839` permits full *omission* of confidence at CoT egress; the adapter does strictly better. CoT v2.0 has no standard detail element for a classification-confidence scalar, so inventing one would mint a private dialect (gates 1 and 6). Gate 5 forbids free-text being the *source*; here the structured source is the canonical event and remarks is the rendered projection — exactly the prescribed relationship. Positional uncertainty *is* already structured (`error_ellipse_m` → ce/le/precisionlocation). `git log origin/main..HEAD -- adapters/egress/cot/` is empty: untouched by the range.
- *"CoT and JREAP egress raise on a malformed `event.ts`, contradicting their documented None contract."* — Refuted 3/3. The docstrings state a *closed enumeration* of refusal conditions, not a universal promise, and `adapters/egress/cot/README.md:6-9` states the input precondition outright. Every probe input is schema-invalid, so it cannot reach the parse. The only in-repo caller validates first and replaces the event with a SYSTEM_EVENT diagnostic carrying a fresh `ts`. `zmeta_state_to_jreap_track_json` has no non-test caller anywhere.
  *(Correction 2026-07-27: this refutation is falsified. Its premise — "every
  probe input is schema-invalid, so it cannot reach the parse" — was wrong:
  Z$-satisfying shapes like `"1969-12-31Z"` are gate-clean yet parse NAIVE,
  so the crash class was live, including an OSError arm on Windows and a
  silent host-local reinterpretation arm. The disposition correctly banked it
  as an open MAJOR; it is now CLOSED as a class across CoT, JREAP, and the
  SAPIENT egress twins — health wave commits `25bb5fa`/`ede9bb6`.)*
- *"SAPIENT command egress does not ULID-validate `follow_object_id`."* — Refuted 3/3. The premise (that it is an is_ulid-marked SapientMessage id) is unverifiable — no SAPIENT proto in this tree — and contradicted by the repo's live-verified record: `ulid_util.py:3-5`, the egress README table and the pack README all enumerate exactly three ULID-validated fields, and the 2026-07-21 Apex v4.2.0 end-to-end run with strict `ParseDict` found and fixed exactly the ULID gaps that were real. `node_id` and `destination_id` are also caller-supplied and unchecked, and the pack's own published smoke test supplies UUIDs.
- *"Notes-template guard keys on a free CLI string, never cross-checked against the manifest's `release_status`."* — Refuted 3/3. `spec/release-signing-attestation.md:75-81` enumerates five legitimate release states; the conditional is the specified design. The proposed cross-check would break every documented non-formal build (`--release-state audit_runtime_sweep`, dry-run/RC packages), fail the repo's own passing test, and force an audit package to self-label `formal_release` — the laundering gate 3 forbids.
- *"Formal-release attestations still self-describe as 'Template only'."* — Refuted 3/3. The statement is TRUE: `signature_mode: none`, and six fields are still `explicit_release_input_required`. The error direction *inverts* gate 3 — over-disclosure, not laundering. The governed spec sanctions the shape (`:70-71`, `:109-111`, `:122-138` list "limitations and notes" as first-class attestation contents). Identical text back to `release/package-v1.1.8`, nine releases.
- *"Release-notes placeholder validator accepts an empty or headings-only RELEASE_NOTES.md."* — Refuted 3/3. The code matches its own documented contract ("must not ship the notes *template*"), and `RELEASE_CHECKLIST.md`'s guarantee is carried by the human step, with the validator sentence explicitly scoped by "Without it". The default path IS caught; the uncovered set requires a maintainer to author a stub, point `--release-notes` at it, publish notes never read, and falsely tick a separate checklist item. Any heuristic strong enough to catch "headings only" would risk refusing legitimately terse notes — the repo's own accepted fixture is three lines. Gate 7 argues directly against growing this into a prose-quality checker.
- *"Non-UTF-8 release notes crash the package validator."* — Refuted 2/3. All 21 `read_text` calls across `tools/*.py` are unguarded; the metadata YAML load crashes *earlier* in the same run. The builder always writes the package notes as UTF-8, so the invoked hazard lands in the builder, not the validator. The only residual path is hand-replacing a file inside a built package — itself an integrity violation `SHA256SUMS.txt` exists to catch.
- *"Release-package checksum coverage is measured against the builder's declaration, not the directory."* — Refuted 3/3. The offered scenario fails LOUDLY: the validator reads the attestation and checksum file by hardcoded name, so a non-default `--attestation-output` or `--checksum-file` produces hash mismatches, not silence. Formal packages are built into fresh per-version directories. And the distributed artifact is the zip, which is hashed and signed over the *whole* directory — stray files are inside the envelope, the opposite of the claimed impact. The proposed fix would reject the spec-sanctioned shape (detached signatures the builder never declares).
- *"Conformance claims' `release_hashes` are never cross-checked against the manifest."* — Refuted 3/3. The offered evidence is false: reconstructing all 20 commits shows the claims IN SYNC with the manifest at every single one, including `origin/main`'s tip. The claim files are in the manifest's hash-pinned `claims` group, so in-repo tampering fails the kernel gate loudly. The reproduction requires regenerating *without* `--update-claims`, which the only documented command includes, and a bare regeneration resets `release_id` and fails the pins. Making the check unconditional would break every honest third-party claim made against a prior release — which is why `--verify-contract-hash` is opt-in by design.
- *"Release-manifest validation recomputes with the builder's own functions and never re-derives the artefact set."* — Refuted 3/3. The finding concedes it is an observation. `builder.artifact_groups(ROOT)` was run: 19 groups, zero path-set divergence, and a full rebuild reproduces the shipped bundle hash. The reproduction manufactures its precondition and omits the mandated rebuild, which the glob-driven `policy_bundle` group absorbs automatically. An independent hashing path already exists and is gated (`SHA256SUMS.txt`, plain `hashlib` over raw bytes, recomputed by `validate_release_package`).
- *"Published-checksum immutability gate cannot see a deleted checksum file."* — Refuted 2/3, becoming A-26. The published record is the tag, which survives working-tree deletion; deletion is not the prohibited act; the recommended fix would make the gate vacuous in a tagless checkout, the exact environment the docstring calls out; and no checksum file has ever been removed in 23 releases.
- *"Tautological test: `test_interrupts_and_config_failures_still_propagate` exercises no gateway code."* — Refuted 2/3. The method has no docstring and self-labels as a mirror via an inline comment, so the "false confidence" premise collapses; the exact mutation the finding proposes fails the *sibling* test at `:232`; and the premise it documents is load-bearing, since `_require_compact`/`_require_proto` raise `SystemExit` from inside the guarded region.
- *"The R11-14 builder fix has no test."* — Refuted 3/3, becoming A-27 (see above).
- *"Drop-reason vocabulary pin covers membership but not severity."* — Refuted 3/3. The mechanism is real but the drift channel is gated: `policy/violation-codes.yaml` is hash-pinned in the manifest (`:178-181`), recomputed by `validate_release_manifest` on every run and asserted by `test_release_manifest.py:91` in plain pytest. Measured: the file hashes to the manifest value today, and the `fail`→`warn` mutation hashes differently and fails the artifact check. The offered reproduction (`cp -r policy /tmp/p`) is precisely the step that routes around the gate.
- *"Compact encoder refuses microsecond-precision timestamps outright."* — Refuted 3/3. The refusal is intentional, normative and discoverable — `spec/compact-binary-mapping.md` names this exact case with an example, `CHANGELOG.md` records it, and two tests pin it. The contract reading is wrong (§6.6 caps no resolution; the ms rule governs durations and deltas). The proposed remedy is the pre-fix laundering bug, verified: `origin/main`'s codec encodes and returns an instant 456 µs off the observation. The caller already converts the refusal into a counted, filterable `ENCODING_UNSUPPORTED`. A scan of every corpus file found zero timestamps with more than three fractional digits. The producer-side interaction (SAPIENT's `_envelope_ts` emits microseconds) is real and worth a release-note line; the fix is producer-side quantization or a non-compact encoding.

**Killed on the finding describing a coverage boundary rather than a defect:**

- *"README H1 carries an unguarded current-release claim."* — Refuted 2/3. No present defect (the H1 names v1.1.16); the docstring inconsistency alleged is false; and `git log -L 1,1:README.md` shows the H1 bumped in the same commit as the release for **18 consecutive releases** with zero misses. The evidence offered to prove human discipline unreliable demonstrates a perfect record.
- *"CI compatibility target hardcodes the current release."* — Refuted 3/3, and the mechanism does not exist: `args.target` is used at exactly one place, a JSON payload label, and is never passed to any check. Empirically, running every corpus at `--target v1.1.1`, `v1.1.8` and `v1.1.16` produces byte-identical transcripts. CI does not pass `--json`, so the one consumer is never reached. The genuine (different) nit is that a flag documented as "Release target to check against" affects nothing.
- *"Governance-doc worked command was hand-fixed and still has no pin."* — Refuted 3/3. Lines 342-343 immediately below instruct replacement at the point of use; and a v1.1.17 cut regenerated under the v1.1.16 identity fails `test_release_manifest.py:60-62` plus every currency check, before any publication step.
- *"Family-completeness derivation is bounded by two hardcoded assumptions."* — Refuted 2/3. The central claim is false for the cited precedent: the assertion is set-equality in BOTH directions, so a buried header drops a carrier and the test fails **loudly** (simulated and verified). The line window is documented with its rationale at `:127-131`. And the recommended repo-wide walk returns five carriers including `.tmp/review-pr-2/...` — a snapshot tree CLAUDE.md instructs auditors to ignore. The `docs/` glob is what keeps them out.
- *"Doc-currency guard forbids stating any true historical release fact."* — Refuted 3/3. The recommendation would reopen half the observed defect: `git diff` shows the pre-fix body carried TWO stale claims, and the second ("ZMeta v1.1.9 intentionally does not claim everything") is caught by *neither* the header pin nor the 'currently' guard. The blocklist is glob-derived and grows with zero per-release edits. `README.md` carries `## v1.1.13 Integration Notes` untouched, so provenance is not suppressed anywhere.
- *"New currency guard bans historically correct statements in the overview."* — Refuted 3/3, same ground, plus: the doc's only release-tag mention is the pinned header, so the reproduction requires inventing three sentences not in the repo, and CHANGELOG is the canonical home for version provenance.
- *"Superseded matcher only recognises v-prefixed versions."* — Refuted 3/3, becoming A-25 (see above).
- *"Currency sweep left `build_mvp_packages.py`'s `--version` help seven releases stale."* — Refuted 3/3. The same-commit premise is false (`git show --stat 05ad9a8` does not list the sibling file; that bump landed in `6ea9888`); the help strings are not byte-identical; wave 7's closure claim is explicitly scoped to the two Markdown worked-command blocks; and an argparse `e.g.` on a flag whose default is manifest-derived is not a currency surface.

**Killed on being an argument about git metadata or an advisory document, not the code:**

- *"R11-05's evidence anchor cites a test file that has never existed."* — Refuted 3/3. True but inert: the cited line numbers are correct at the audited baseline and resolve to the exact content claimed; the same document names the file correctly at `:699`; and the claimed impact requires violating Step 0's own instruction to derive rows from code. A single-token typo in an advisory document with no machine consumer.
- *"6ea9888's message carries a retracted 'three MAJOR / eleven' tally."* — Refuted 2/3. Already retracted *inside* the range by `f610751`, which quotes the phrase verbatim; git log is reverse-chronological, so a reviewer reads the retraction first. The erroneous summary is contradicted eight lines below itself by its own itemized list. The offered reproduction does not reproduce (basic grep treats `|` literally). The only remedy would erase the recorded mistake and orphan its retraction — worse under the honesty gate.
- *"Six vendor-block sinks claimed; there are seven."* — Refuted 2/3. The finding misidentifies its own uncounted site (naming `:520`, which IS the alert path the record counts), and "six" is coherent under the unit the record uses (five dispatch paths plus the power block; `:827` is a branch, not a path). The pin's `>= 6` is an anti-deletion floor, not an equality pin, and the load-bearing assertion `assert not unguarded` is count-independent. The count remark survives only inside the Step 0 map, where it belongs.
- *"New normative provenance justification names a carrier that carries no commit."* — Refuted 3/3. The publication record IS the worklog entry (`docs/zmeta_refinement_worklog.md:376`, naming `f8951ee`, matching the tag); the finding grepped release assets instead. The alleged propagation into the manifest does not exist (`grep -n "all of which pin"` matches only the one spec line). And the "relaxed MUST" was already violated in practice — the published v1.1.16 formal manifest carries `git_commit: explicit_release_input_required`.
- *"Recorded divergence overstates its scope: only the manifest diverges, not the package."* — Refuted 3/3, and the *opposite* is true. The evidence was vacuous (`release/package*/` is gitignored, so a git diff over it is always empty), and unzipping the published zip shows 3 of 4 package files differ. Adopting the finding would delete a true warning.

**Killed on the design gates:**

- *"BEARING_FRAME_UNLABELED emits a per-event wire diagnostic with no suppression path."* — Refuted 3/3. Every symptom reproduces identically on `GEO_ZERO_FILL_SUSPECTED`, which shipped on `origin/main`; the two functions blamed are byte-identical to `origin/main`; and the 'ignore' evidence is a misread (an arbitrary garbage severity value produces the same result, because 'ignore' is not in the violation-severity vocabulary at all). A-22 carries the narrower gate-1 remark.
- *"The diagnostic names a remedy that is schema-invalid under v1.0."* — Refuted 2/3. `spec/semantics-contract.md:888-890` says verbatim that the quality-scoped mechanism "is the only frame provenance available to v1.0-emitting producers" — the message cites contract 6.4, and the section answers the version question directly. The string is a condition report matching the file's house convention, the harm runs fail-closed, and a producer who guesses wrong gets an immediate `SCHEMA_INVALID`.
- *"No documented consumer obligation to tolerate unknown reason codes."* — Refuted 2/3. The offered grep returns zero hits as written; a correct search surfaces `spec/compact-binary-mapping.md:229` ("Unknown reason codes may be transmitted as strings and are preserved"), pre-existing at `origin/main`. `semantics-contract.md:1315-1316` binds conformance to the *active* vocabulary, and `spec/versioning.md:45` classifies new enums as backward-compatible. Zero delta to the held range.
- *"Three new reason codes are unreadable by v1.1.16, and no compatibility statement exists."* — Refuted 3/3 as a defect. `spec/semantics-contract.md:110-115` states the Class B authorization verbatim, pre-existing on `origin/main`. The proposed remediation ("consumers MUST pass through unknown codes") would contradict the locked contract's MUST at `:1315` and the reference validator's deliberate rejection at `validators.py:2081-2091, 2151, 2230` — creating a governance defect rather than closing one. A-29 carries the surviving release-notes obligation.

---

### 5. Checklist disposition

| Checklist item | What was checked | Verdict |
|---|---|---|
| **Step 0 — finding → code → test map** | All 41 layers located in code by reading the implementation, then the pinning test identified by executing revert-simulations rather than by name-matching. Every non-PRESENT row grepped across every consumer and test surface. | **DONE, and it earned its keep.** 34 PRESENT / 6 UNPINNED / 1 ABSENT. The map corrected the record's sink count (seven, not six), disproved the assumed pin for V1-02 L1 (the NaN test does not pin it; the deep-nesting test does, and only since pass 2), and identified two tests that pin nothing (`test_gateway_runtime_guards.py:240` is a pure-Python tautology; `:255` pins a count threshold, not the behaviour). All six UNPINNED rows are correct in the tree; they are A-28. |
| **1 — partial-application residue** | Working tree clean (`git status --porcelain` empty), so no uncommitted half-applied edit. AST self-recursion scan across `gateway/src/` returned zero self-recursive functions. All multi-layer fixes (V2-01, V2-03, V2-04, V2-12, V2-13) confirmed to have every layer present. `loop_status` family confirmed complete across all four promotion-emitting adapters. Both SAPIENT egress `ts` guards present; cot/jreap siblings checked and correctly excluded. | **FOUND, and it is the headline.** A-04 is committed partial application of the worst kind: two fixes in the *same commit* (`6ea9888`) where V2-09's new recursive scan was placed in front of V2-01's new `RecursionError` guard, defeating it for the exact input class the guard names. A-10 is the same shape in a second file. A clean working tree is orthogonal to this defect class — the lesson for the next cycle. |
| **2 — commit-message truth** | All 18 commits read message-then-diff. Every file in every `--stat` accounted for. Finding-ID attribution cross-checked against the record's tables. Corpus growth claims verified against `origin/main` by `git show` (bad-events 27→29, harness 39→40). Test-count claims verified where reproducible. | **CLEAN on correspondence, one gap on justification.** Every described change is present; no fix is attributed to a wrong ID; no unrelated change is smuggled. The one file not accounted for by its message (`spec/profile-compatibility.md` in `6ea9888`) was **refuted 3/3** — the records do carry it, under different wording. But correspondence is a completeness check on the message, not a correctness check on the change: the one commit-message *justification* independently tested (`c1eb9d0`'s "matching the reference adapter it names") is **false** — A-21. That is a non-trivial base rate for ~25 such claims, none of the rest tested. |
| **3 — promotion lint / vocabulary / sinks / release guards / currency guards** | Five sub-lenses. Promotion lint: every key set re-derived from enforcement, then eight wrong-typed shapes and two mangled-value shapes probed against the shipped CLI. Vocabulary: mutation harness drifting one surface at a time. Sinks: enumerated from source, all seven ingress and all four egress. Release/compact guards: backend parametrization instrumented; the notes validator run against the real shipped package. Currency: matcher driven against an attack battery. | **FOUND: A-05, A-07, A-14, A-15, A-11, A-17, A-09.** Also confirmed sound: all 18 global promotion keys read by enforcement and none unread; the six per-rule keys exactly right; `_both_cbor_backends` genuinely swaps and both backends are installed; the vocabulary pin catches membership drift on all three surfaces; the currency matcher is correct in both directions and non-vacuous (19 real superseded versions). |
| **4 — blind-by-construction self-checks** | Every self-check, round-trip, validator and gate enumerated and asked what it cannot see because both sides share machinery. Encoding-negative blindness quantified. | **FOUND: A-01, A-08, A-19.** Quantified: 20 of 21 compact fixtures and 10 of 21 protobuf fixtures are materialised by the repo's own encoder, so no fixture can express a tag, a simple value, `undefined`, a float16, or a non-finite double. `test_wire_output_is_always_canonical_json_serializable` round-trips through `zmeta_compact.dumps`, which refuses non-finite input — its `allow_nan=False` assertion is unfalsifiable. Two false-positive candidates in this lane (conformance-claims cross-check, manifest self-recompute) were **refuted 3/3 each**. |
| **5 — record counts and validation inventory** | The full battery reproduced at HEAD. Range, ledger, finding-ID contiguity, severity tallies, governed-surface diffs, and regenerated artifacts all measured independently. The manifest rebuilt in memory. | **FOUND: A-13.** Everything else reconciles exactly: 18 commits, hash-for-hash and minute-for-minute against the ledger; V1-01..V1-03 and V2-01..V2-14 contiguous with no gaps; severity tallies (V1 1/2/0=3, V2 2/7/5=14) match the recorded ground truth bullet-by-bullet; corpus counts, file count (77), deletion count (−392), regenerated-artifact counts (8/8/8) and pytest (785+316) all reproduce. Only the insertion count is wrong, in all three records, written by the commit that falsified it. |
| **6 — doc-currency scope** | Every version-literal change outside the new records classified individually: 11 correctly re-baselined (each verified executable-shape or manifest-derived), 1 correctly left stale (`adapters/README.md:86`, verified against the `## [1.1.8]` CHANGELOG section, whose four bullets are exactly the rule underneath it), historical audits correctly untouched. | **FOUND: A-18 (a framing falsification, not a literal one) and A-24.** The judgement call at `adapters/README.md:86` was re-checked and **confirmed correct** — re-baselining would falsely narrow a rule that has bound adapters for eight releases. No re-baseline falsified a historical statement except A-18. Two further candidates in this lane were refuted 3/3. |
| **Governed surface — `spec/semantics-contract.md` (v1.0 LOCKED)** | `git show 05ad9a8 --stat` confirms exactly 1 file, +6/−1, one hunk at @@ -725,7 +725,12 @@, entirely inside §5.3 (lines 717-749). No field, type, or requirement changed. The new claim verified true against `adapters/ingress/time_utils.py:61-65` and the shipped bladeRF fixture. Read §2.1-2.6, §3.x, §5.x, §6.x and §24 for contradictions — none. Conformance delta: producer conformance unchanged (descriptive, not a MUST); consumer conformance tightened, which §2.1 explicitly permits. All five §2.1 prohibitions cleared. Verified the reference stack does not itself violate the new MUST. sha256 over LF-normalized bytes matches `release/zmeta-release-manifest.yaml:240` exactly. | **CLEAN.** A §2.6-threshold clarification, correctly classified and correctly regenerated. Gate 6 offers no alternative — the field is schema-required with a `utcDateTime` type in both branches, so no policy, profile, or adapter surface can resolve the ambiguity. |
| **Governed surfaces — schemas and policy** | Both schemas flattened at `origin/main` and at HEAD into complete JSON-pointer maps and set-differenced: **0 removed, exactly 3 added**, all under the `reason_code` enum, every other pointer identical. Ordinal safety confirmed against `REASON_CODE_MAP` (untouched). Severity single-sourcing confirmed structurally (`policy/violation-codes.yaml` is the only carrier; `validators.py:124-140` the only loader). All three codes gate-1 tested against their nearest existing neighbours. All three live-probed end to end. | **CLEAN, with A-22 and A-29 recorded.** Strictly additive, ordinal-safe, single-sourced, defensible on gate 1, authorized by pre-existing contract text, and all three genuinely emitted and reachable. `A-22` is a marginal gate-1 call on one of the three, not a violation. `A-29` is a release-notes obligation, not a defect. |
| **Governed surface — release manifest and conformance claims** | Manifest re-derived in memory: all 70 artifact hashes, all 19 group hashes, `release_bundle_hash` and `release_manifest_hash` reproduce exactly; declared group path lists set-identical to `artifact_groups()`. Both claims files confirmed byte-identical to a `yaml.safe_dump(sort_keys=False, ...)` round-trip of their own content, with all 12 `release_hashes` plus `contract_hash` matching the manifest and the circularity sentinel intact. | **CLEAN as regeneration output; A-09 and A-12 on the validator and the identity.** No hand edits detected. The formal-status coherence checks are non-trivially satisfiable (the `--branch` default is the placeholder), but the identity half is missing — A-09. The published-vs-in-tree divergence is lawful, recorded, and must be resolved by a cut — A-12. |
| **Design gates 1-7** | Every change classified against each gate. Vocabulary growth, producer-completeness, honesty trades, over-optimization, minimality of the three codes, and private-dialect risk all assessed. | **SOUND.** No event type, subtype, or payload field was added. Nothing laundered — every refusal in this cycle got *harder*. Two more-permissive paths (the receive-loop backstop, the vendor-block non-finite strip) are both defensible as written. One over-optimization cluster identified in wave 7's doc-currency machinery, but the specific findings drawn from it were **refuted 3/3** (the blocklist is glob-derived and costs nothing per release; the recommendation would reopen half the observed defect). Two private-dialect risks: A-29 (acceptable, sanctioned Class B) and the cot/jreap `loop_status` requirement (acceptable — the alternative is an adapter stamping a verdict for a check it never ran, a direct gate 3 violation). |

---

### 6. Positive assurance (witnessed, not assumed)

Only things an agent actually ran or read at a line. Nothing here is inferred from the record.

**Gates and suites, executed at HEAD:**
- Full kernel gate, all nine flags: `python tools/validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative --precision-policy --release-manifest --release-package --bad-events --adapter-harness` — exit 0. Subsystem counts: profile projection 37, extension registry 61, conformance classes 34 / claims 2, encoding-negative 50, precision policy 32, bad-event corpus 29, adapter conformance 40, conformance pass=20/fail=27.
- `python tools/validate_examples.py --strict --require-all` — 51/51, exit 0.
- `python -m pytest -q` — **785 passed, 316 subtests passed**, 0 failures. Reproduces the recorded ground truth exactly.
- `python tools/validate_release_manifest.py` — `release manifest ok groups=19 artifacts=70`.
- `python tools/lint_policy_risk_modes.py` on the shipped `policy/` — `policy risk mode lint ok`, and `lint_producer_authority_structure` returns `[]` against both `policy/` and `configs/policy-variants/producer-authority.strict.yaml` (no false positive on any legitimate in-repo policy shape).
- `python tools/validate_conformance_classes.py --claims --verify-contract-hash` — claims `contract_hash` `fca9cd74` matches the manifest's `semantic_contract_hash`.
- Gateway `--profile H --self-test`, `tools/test_workflow_end_to_end.py`, and `tools/test_gateway_live.py` on both the JSON and compact/Profile-L paths — all exit 0, tree still clean afterward.
- `git diff --check origin/main..HEAD` — clean. Working tree clean before and after every probe.

**Fixes witnessed working, by live probe rather than by reading:**
- **Compact fail-closed** (`R11-01`/V1-02/V1-03/V2-05/V2-10): v1.1.0 event → REFUSED; NaN → REFUSED naming the exact path; uppercase UUID → ACCEPTED, decoding to canonical lowercase; `.876Z`, `.876000Z`, `.000Z` → ACCEPTED (the over-refusal that broke both bladeRF real-capture fixtures is closed, and the wave-1 assertion was correctly flipped); `.8765Z` and `.8760001Z` → REFUSED (sub-microsecond loss now visible, which a parsed-value comparison cannot see); pre-1970, year-0001 and year-9999 instants exact through `timedelta` arithmetic.
- **Integer range** (V2-09): `2**64` and `-(2**64)-1` REFUSED; `2**64-1` and `-(2**64)` ACCEPTED — identically under both backends with `zmeta_compact.zmeta_cbor` forced to `None`. Revert-simulation (monkeypatching `_find_unencodable_int` to return `None`) produces 6 subtest failures across both backends, proving the pin.
- **Recovery ladder** (V1-01/V2-01): driven directly through `gateway._encode_outgoing_or_diagnostic`. Poisoned version, NaN, `2**70` integer and 500-deep nest all produce a `SCHEMA_VIOLATION`/`ENCODING_UNSUPPORTED` diagnostic carrying `metrics.original_event_id`; an event whose *event_id itself* is unencodable (lone surrogate) correctly falls through to the `UNKNOWN` sentinel rung — the V1-01 poisoned-diagnostic class, closed. On a **live gateway over real UDP** (`--profile H --output-encoding compact`), a `2**70` integer in extensions produced a forwarded compact-encoded diagnostic carrying `reason_code: ENCODING_UNSUPPORTED` and the original event_id, while a clean event forwarded normally.
- **Decode-side fail-closed** (V2-11): hostile epoch-ms at `2**63`, `-(2**63)`, `10**18`, `10**15`, the exact `datetime.max` ms (accepted) and one past the `timedelta` limit — all refused as `CompactUnrepresentableError`, none escaping; it is a `ValueError` subclass so it propagates through `loads()` as an ordinary invalid-input refusal.
- **Iterative BFS** (V2-02): `_find_forbidden_key` walks a 100,000-deep structure cleanly and returns the shallowest match with a correct path. AST self-recursion scan across `gateway/src/gateway.py` and `validators.py` returns **zero** self-recursive functions — the sender-controlled-depth class is closed on the ingress traversal.
- **Backstop scoping** (V2-01 LB): `recvfrom` is genuinely outside the guard, so a dead listener socket still terminates rather than hot-looping; `except Exception` does not catch `SystemExit`, so `_require_cbor`/`_require_compact`/`_require_proto` still stop the process, nor `KeyboardInterrupt`.
- **Validator checks** (R11-21/R11-04): canonical bearing without frame → `BEARING_FRAME_UNLABELED` at `warn`, event still valid; either `bearing.frame` or `quality.bearing_frame` silences it; NaN and inf at both `confidence` and `payload.claim.confidence` → `NON_FINITE_CONFIDENCE`, `fail`.
- **Harness hardening** (R11-08/R11-09): a typo'd `forbidden_path` key and an `events`-kind fixture with no `event_count`, both built from real shipped fixtures, now fail with `ADAPTER_FIXTURE_INVALID`; the unmodified fixture still passes. `validate_adapter_conformance.py:352-386` genuinely loads `conformance/adapter-harness/fixture.schema.json` and lints every fixture line before execution.
- **Promotion enforcement** (against the shipped policy): correct refusal witnessed for metadata absent; metadata not a dict; every per-profile required field missing at L/M/H; `state_category` wrong or merely case-shifted; `origin_kind` outside the allowlist; `lineage_status` `UNRESOLVED_PROFILED` at H; blank `source_event_uid` when `lineage_status` is `EXTERNAL_SOURCE`; `trust_ref` without an approved prefix; `loop_status` `REFLECTION_DETECTED` (including the `always_reject_loop_risk` hard stop surviving global `mode=warn`, and softening only when explicitly set false); self-citation in `lineage.based_on`; non-promotion lineage transform; unapproved `promotion_policy_id`/`projection_id`/`confidence_basis`; `freshness_ms` negative, non-numeric, or over the profile max. Producer matching is case-insensitive and whitespace-tolerant and fails closed on a homoglyph producer. `degrade` and `quarantine` stamp honest `policy_mode`/`policy_decision`/`reason_code` plus a risk record with `allowed_uses`/`prohibited_uses`, and reduce/cap confidence and `valid_for_ms` as configured.
- **SAPIENT fixes** (R11-02/-03/-12/-20, V2-03/V2-06): unknown/local/missing `policy_decision` refuses, matching `tools/filter_risk.py` `DECISION_RANKS` key-for-key; TaskAck refuses a null correlation instead of `str(None)`; fusion promotion allowlists caller keys and refuses on any unenumerated key; `_drop_non_finite` applied at all **seven** vendor sinks including the PLATFORM_STATUS `power` block, with the positional-array rule correct on all three branches; non-string `ts` guards present in both egress adapters.
- **signalhunter** (R11-06/-07): `_plausible_fix` rejects (0,0), non-finite, non-numeric and out-of-range values, gating the header seed, every mid-file GPS fix and the per-peak gradient sample — so no bearing, no `displacement_m` and no `quality.sensor_position_2d` can derive from a sentinel. Loss-of-lock after a good fix does not fabricate. The fabricated `alt_m: 0.0` is gone. The self-asserted `CHECKED_NOT_REFLECTION` default is gone from all three templates (cot/jreap raise, mavlink returns None).
- **Currency guards** (V2-07/V2-12): matcher driven against an attack battery — catches a version ending a sentence, in table cells, headings, parentheses, hyphenated ranges, URLs and file paths, with multiple per line; correctly refuses `v1.1.1` inside `v1.1.16`, inside backticks, and `v1.1.10` inside `v1.1.100`. Revert-simulation with the broken first cut `(?![\d.])` fails the self-test. All four release-context carriers enumerated repo-wide and confirmed complete at v1.1.16. `test_release_currency.py` 14/14.
- **`RELEASE_PACKAGE_NOTES_PLACEHOLDER`** reproduced against the actual shipped artifact: `release/package-v1.1.16/RELEASE_NOTES.md` line 1 is `# ZMeta Release Notes Template` beside `release_state: formal_release`, and the validator emits the FAIL with exit 1.
- **`test_published_checksums_immutable.py`** verified non-vacuous with tags present: it really does byte-compare each `SHA256SUMS_v*.txt` against its own tag blob, and `git diff --stat v1.1.16 HEAD -- release/SHA256SUMS_v1.1.16.txt` is empty.

**Test-surface quality, checked directly:**
- Zero `skipif` / `importorskip` / `pytest.skip` / `SkipTest` anywhere under `gateway/tests` or `adapters`. The one conditional-vacuity case is honestly documented AND carries an explicit anti-vacuity assert.
- No `pytest.raises(Exception)` / `assertRaises(Exception)` in the new suites; every raises-assertion names a specific type.
- Count-floor assertions (`>= 13` v1.1 examples, `>= 30` v1.0 events, `>= 3` mapping packs, `>= 6` checksum files, `>= 4` `record_drop` sites, `>= 6` vendor sites) each sit on top of a real per-member assertion inside the loop — anti-shrink tripwires, not substitutes for coverage.
- Decisive revert-checks executed rather than reasoned about, for the epoch-ms sweep, the oversized-int guard, the sub-microsecond truncation guard, the non-finite guard, the uppercase-UUID normalization, the out-of-platform-epoch guard, the currency matcher lookahead, and the cot/jreap/mavlink `loop_status` refusals. Each fails on revert.

**Release limits respected throughout:** `git diff origin/main..HEAD --name-status -- release/` shows only `zmeta-release-manifest.yaml`, two templates and `sign_release_artifacts.py` changed. Every published `release/SHA256SUMS_v*.txt`, `RELEASE_NOTES_*` and `VALIDATION_REPORT_*` is untouched. No tag, no push, no signature.

---

### 7. Release readiness

**Judgement: HOLD the range. Do not cut v1.1.17 as it stands.**

Six defects reproduced from the code — not from the record — would ship a fielded-safety or laundering failure to a consumer, and three of them falsify claims the range's own CHANGELOG and its new normative spec text make.

**Blockers (would ship the defect to a consumer):**

| ID | Anchor | Why it blocks |
|---|---|---|
| A-01 | `validators.py:1913`, `gateway.py:816`, `zmeta_to_cot.py:256` | ATAK receives `<point lat="nan" hae="inf">`; the gateway emits non-RFC-8259 JSON that Go/Rust/Jackson reject outright. Fielded safety + hard interop break. |
| A-02 | `sapient_to_zmeta.py:678, 397, 415, 354` | `bearing.az_deg = nan` stamped TRUE_NORTH; NaN inside `payload.claim`. And `CHANGELOG.md:37-38` asserts this class closed. |
| A-03 | `gateway.py:2008` | One datagram terminates the gateway for every producer behind it once the metrics sink degrades — the single guarantee the backstop exists to provide. |
| A-04 | `zmeta_compact.py:497` | Raw `RecursionError` escapes the fail-closed guard; the range publishes normative text asserting it cannot. Silent `INTERNAL_ERROR` drop where the design requires an honest, filterable refusal. |
| A-05 | `validators.py:2374` | One scalar in `require_match_for_event_types` accepts unregistered producers on all six event types; one bare key drops 100% of traffic. Lint says `ok`, exit 0, in both cases. |
| A-06 | `mavlink_to_zmeta_template.py:135` | Fabricated 0 m MSL labelled AVAILABLE at confidence 0.8, passing every gate — an explicit contract 6.8 MUST violation, in the class this cycle closed twice elsewhere. |

All six are narrow, mechanical fixes that stay in the outer rings or in reference-implementation code: a value-scoped finiteness traversal in `validate_semantics` (reusing the iterative pattern now in `_find_forbidden_key`); guarding the derived values in the SAPIENT adapter; making MAVLink refuse rather than fabricate; moving two pre-checks inside an existing `try`; wrapping `MetricsLogger.write`; type-validating one policy key. **None requires a kernel or vocabulary change.**

**Fix next cycle (real, anchored, not cut-gating):** A-07 (promotion lint name-not-type gap), A-08 (CBOR decoder divergence + the spec silence behind it — escalate under gate 6), A-09 (formal-status identity checks), A-10 (SAPIENT egress pre-1970 raise), A-11 (timing_quality NaN), A-13 (record counts), A-14 (unhashable metadata TypeError), A-15 (lint inversion), A-16 (`estimated_state` bearing blindness), A-17 (installation-guide/README command pair), A-18 (handoff currency regression), A-19 (4-of-7 package hash check), A-20 (adapter README claim), A-21 (teaching-corpus doctrine — a maintainer judgement about what the corpus may assert), A-24 (`measure_packet_size`), plus the hygiene items A-23, A-25, A-26, A-27 and the coverage gaps in A-28.

**Manifest / checksum divergence state (A-12):** three distinct manifest states now exist under the single identity `zmeta-v1.1.16` — the tag blob, `origin/main`, and HEAD. `sign_release_artifacts.py --verify-checksums` exits 1 on exactly one line (the manifest); the other six pinned assets verify clean, so anyone verifying the **published GitHub assets** is unaffected. The in-repo `release/package-v1.1.16/` has also been regenerated (3 of 4 files differ from the published zip), while the zip itself is stale but intact because `_ensure_package_zip` never overwrites. The divergence is lawfully pre-adjudicated at `AGENTS.md:130-135` and recorded at `docs/zmeta_refinement_worklog.md:46-52`. **It is not a governance breach, but it is the state the cut must clear**, and nothing in the tree yet performs the resolution. Resolution requires a genuine cut under a new identity — never an edit to `SHA256SUMS_v1.1.16.txt`, which must never be rewritten; the divergence resolves by publishing a **new** `SHA256SUMS_v1.1.17.txt`, and `gateway/tests/test_published_checksums_immutable.py` now enforces that.

**Agent-permissible cut steps** (after the blockers are fixed and the battery re-run):
1. Rebuild the manifest under a NEW identity: `build_release_manifest.py --release-id zmeta-v1.1.17 --release-name "ZMeta v1.1.17" --release-status formal_release --release-date <date> --branch main --update-claims`.
2. Author `release/RELEASE_NOTES_v1.1.17.md` **including a Compatibility section naming the three added `reason_code` entries** (A-29 — the v1.1.14 precedent).
3. Convert the CHANGELOG `[Unreleased]` HOLD block to a `1.1.17` heading.
4. Run the doc-currency pass `RELEASE_CHECKLIST` enumerates: README current-release line and bundle-builder commands, installation guide, professional overview, `release/README.md`, `check_compat.py` TARGETS += v1.1.17, `test_release_manifest.py` `release_id`/`release_date` pins, `sign_release_artifacts.py` VERSION default. `gateway/tests/test_release_currency.py` machine-checks six of those and will fail pytest on any stale one.
5. Build the package **with** `--release-notes release/RELEASE_NOTES_v1.1.17.md`, and validate against the **real package directory** — not the `templates_only` path the kernel gate uses, which returns before the notes check.
6. Build the three bundles; run the full battery; record `VALIDATION_REPORT_v1.1.17.md`; update worklog and handoff; run the retention pass.

**Maintainer only, per `AGENTS.md` Release Limits — an agent must never perform these:** creating the tag; pushing any branch or tag; generating or verifying detached signatures; uploading the GitHub release; and writing or altering any `release/SHA256SUMS_v*.txt`.

**What remains unverified at a cut, even after the blockers are fixed:**
- That the 25 claimed pre-fix defects were real. No lens established the pre-state; this audit tested the tree, not the history.
- The write-side behaviour of every release builder. All were read, none were run.
- The historical per-wave pytest and gate numbers, and the record's closing live UDP probe — the latter is unreproducible by construction, and one of its three results (A-04) is now known to be depth-dependent.
- Live-fleet behaviour: no ATAK client, no SAPIENT DMM, no non-Python JSON decoder was available. A-01's and A-11's consumer-side impact rests on RFC 8259 and the repo's own stated threat model.
- Whether the release-package layer works at all under the mandated gate, since `validate_conformance.py` runs it in `templates_only` mode. Every "kernel gate green" assurance in this audit and in the record is silent about that layer.

**Recommendation.** Fix A-01 through A-06, re-run the full battery, and run one more verification pass over those fixes specifically — this cycle's own carry-forward lesson, demonstrated a dozen times over and again in A-04, is that a fix introduces or exposes the next defect. Then cut. Cutting now would publish a release whose headline claim is honesty-class closure while `lat="nan"` reaches ATAK.
---

## Fix pass — two adversarial rounds (2026-07-22)

**Status: SIX BLOCKERS CLOSED, FOUR MAJOR FINDINGS OPEN. Still held; not ready
to cut.**

Maintainer disposition on the fresh audit: fix all six blockers. What follows
is what actually happened, including what it cost.

### Round 1 — six fix waves, then attack the pins

A-01..A-06 were fixed serially, each wave required to reproduce the defect
before fixing it, close the class rather than the exemplar, and prove its pin
by revert-simulation. All six reproduced exactly as the audit described. Every
wave left the battery green.

A read-only adversarial pass then attacked all six new guards and returned
**30 residual findings, 8 MAJOR** *(correction 2026-07-27, cold re-read CR-14: the register itemizes **ten** round-1 MAJORs, R1-01..R1-10)*, against a tree that was fully green
(pytest 896 + 716 subtests at that point). Three shapes, all of them ones this
repository has already recorded about itself:

- **Two fixes closed a defect by introducing a quieter one.** `duration_ms`
  returning `None` on an unusable declared latency made a node declaring
  `maximum_latency: NaN` publish a *narrower* uncertainty bound (`est_error_ms`
  5.0) than one declaring 0.5 s (505.0) - the worse the input, the cleaner the
  event, with the discarded declaration recorded nowhere. Separately, a new
  emit-boundary backstop turned one non-finite key in a vendor blob into total
  loss: 4 good events to 0, discarding geo, bearing and classification the
  adapter had resolved correctly.
- **A new guard reproduced its own target defect class, twice more.** The new
  routing lint opened with a silent early return on precisely the bare-key
  mangle it existed to catch (`routing:` truncated gave lint `ok`, exit 0, then
  a raw `AttributeError` on every event - 100% outage). The new AST structural
  pin walked `ast.Try` with `ast.walk`, which descends `orelse` and
  `finalbody`, so a recursive call moved into `else:` counted as *inside* the
  guard while the refusal reverted to a raw crash.
- **Pins that pinned nothing.** `_assert_clean(events, ...)` is
  `for event in events: assert ...` - an empty list asserts nothing, so
  reverting a guard made the backstop refuse the whole event and the test still
  passed. All 13 non-finite cases passed with the fix reverted. A second test
  never reached the code it claimed to pin at all.

Plus one the audit had not found: **NaN confidence laundered to 1.0**.
`min(1.0, nan)` returns `1.0` in Python, and that clamp runs upstream of the
new gate - degraded data emerging as maximally trustworthy.

### Round 2 — remediation, then a final attack

All 30 residuals were remediated (six serial groups), and the final read-only
pass returned **32 findings, 4 MAJOR, of which 18 were introduced by the
remediation itself**.

Round 2 also **escalated** the severity of a residual rather than closing it
quietly. The claim that the non-terminating walker was reachable only from a
Python caller was refuted: `cbor2` honours CBOR value-sharing tags 28/29 on
decode, and `gateway._decode_cbor` falls back to `cbor2` whenever `zmeta_cbor`
is absent - a supported configuration. Measured: a **586-byte datagram**
produced a real reference cycle at ingress and hung `_find_forbidden_key` and
`_find_non_finite` ahead of every semantic check. That is an unauthenticated
remote hang of the receive loop, found and closed in this round, and it was in
no audit finding.

### Why the pass stopped here

Round 1: 6 fixes gave 30 residuals / 8 MAJOR *(ten by the register's own itemization — CR-14 correction 2026-07-27; the corrected count only strengthens this section's argument)*. Round 2: 6 remediations gave 32
findings / 4 MAJOR. Severity is converging; **count is not.**

The decisive signal is not the arithmetic but the *character* of what remains.
The surviving findings are increasingly **design trade-off questions rather
than defects** - is discarding a datum better than laundering it? is a warning
storm worse than silence? is refusing a whole detection proportionate to one
bad vendor key? Several round-2 "introduced" findings are exactly that shape:
a remediation trading one honesty problem for another, where which trade is
correct is a maintainer judgement, not a derivable fact.

Design gate 7 applies to the fix loop itself. A third round would spend
maintainer trust to buy diminishing severity reduction while continuing to
generate new trade-offs at the same rate. **The honest move is to stop and
hand over the state.**

### Open findings carried forward — 4 MAJOR

| ID | Anchor | Introduced? | Summary |
|---|---|---|---|
| B-01 | `zmeta_compact.py:525` | no | The mapping-limit scan descends only dict/list, so a **set**-carried oversized integer still leaves compact egress as a CBOR bignum - two conforming nodes disagree. Same class as V2-09, one container type over. |
| B-02 | `gateway/src/validators.py:1546` | **yes** | The remediation traded a loud lint failure for a **silent pass** on a mangled `timing_freshness` block - the timing-freshness gate is now fully disabled with the lint green. |
| B-03 | `adapters/ingress/sapient/sapient_to_zmeta.py:388` | **yes** | The degraded branch returns before the widen and **discards the resolvable cross-mode latency the store still holds**, so adding a broken mode NARROWS the node's published error. The same laundering shape the remediation was written to close, one branch over. |
| B-04 | `adapters/ingress/mavlink/mavlink_to_zmeta_template.py:60` | **yes** | The TIME_STATUS carried-verdict guard whitelists two literals rather than a vocabulary - `LOCKED`, `NOMINAL`, and even `UP ` with one trailing space override the derived verdict. |

Twenty-eight further findings at MODERATE and below are recorded in the run
artifacts. **Fourteen of the thirty-two are introduced-by-remediation** *(correction 2026-07-27, cold re-read CR-15: the register's own classification and the round table both count **eighteen**)*, which
is the number that should drive the next decision.

### State at hand-over

- Battery green: kernel gate all flags exit 0 (bad-events 29, harness 40),
  examples 51/51 strict, **pytest 1004 passed + 858 subtests** (baseline
  785 + 316).
- Working tree clean; nothing pushed, tagged, or signed.
- **No governed artifact was modified anywhere in the fix pass.**
  `spec/semantics-contract.md`, `schema/*.json`, `policy/violation-codes.yaml`
  and `policy/semantics.yaml` are untouched. No `reason_code` was minted. All
  thirteen governed collisions are recorded in
  `docs/zmeta_doctrine_review_log.md` for separate adjudication.
- The release decision remains **HOLD**, and the manifest/checksum divergence
  (A-12) is still unresolved - it resolves only through a genuine cut.

---

## Records, docs-currency and teaching-corpus pass (2026-07-22)

Scope: `docs/`, non-normative `spec/*.md`, `CHANGELOG.md`, `README.md`,
`examples/`. No governed artifact touched; no `reason_code`, enum entry,
field or type minted.

### Closed

- **A-13 (record accuracy) — FIXED AT THE CLASS LEVEL, and the class is
  wider than the finding said.** Re-measured: the range has grown well past
  the frozen figure. At the audit anchor,
  `git diff --shortstat 09118b3..eb41794` = 77 files, +4920 / −392;
  the same command against `HEAD` reports more, and the working tree more
  again. Keeping the number correct is not achievable — every
  record commit falsifies it, which is exactly why this recurred five times.
  So the frozen totals were **removed**, not corrected: each of the four
  sites now either tells the reader to run `git diff --shortstat`, or states
  the figure as the output of a named command against the **immutable
  anchor** `eb41794`. Same treatment for the per-record commit counts (which
  were wrong on three of four) and the `origin/main..HEAD` attribution in
  §1 of the fresh audit. One genuinely-wrong static count was corrected in
  place: the SAPIENT code-surface row said 6 files, `git diff --name-only`
  says 7.
- **A-17 (stale worked command) — FIXED, family enumerated.** The finding
  named two surfaces; grepping every markdown surface for
  `build_release_package.py` found **four** carrying a `formal_release`
  build with no `--release-notes`: `README.md:464`,
  `spec/installation-guide.md:223`, `release/README.md:25` and
  `tools/README.md:236`. All four now pass it, and README and the
  installation guide say *why* (without it the builder copies
  `RELEASE_NOTES_TEMPLATE.md` and the validator on the next line refuses
  with `RELEASE_PACKAGE_NOTES_PLACEHOLDER`). Historical
  `release/VALIDATION_REPORT_v*.md` commands and the v1.1.12 inventory in
  the handoff were **deliberately left alone** — they record what was run.
  Proven A/B against the shipped code: with `--release-notes` the built
  `RELEASE_NOTES.md` is `# ZMeta v1.1.16 Release Notes` and the validator
  returns no issues; without it, `# ZMeta Release Notes Template` and
  `['RELEASE_PACKAGE_NOTES_PLACEHOLDER']`.
- **A-18 (doc-currency regression) — FIXED by restoring the label, not by
  reverting the sweep.** A literal revert was evaluated and rejected: the
  pre-sweep text said "superseded by the v1.1.13 record above", and the
  v1.1.13 record was pruned from this rolling brief in the same period, so
  reverting would have restored a *dangling* pointer in place of a false
  claim. The block is now labelled historical again and points at
  `release/VALIDATION_REPORT_v1.1.16.md`, with the measured divergence
  (roadmap validator dropped at v1.1.16; contract-hash gates added at
  v1.1.14) stated inline and a one-line reproduction command.
- **R1-11-13 (CHANGELOG scope) — NARROWED.** The non-finite claim now
  carries its scope inside the sentence instead of inheriting it from the
  heading, and cites the doctrine-log entry.
- **A-21 (teaching corpus) — HALF CLOSED, HALF ESCALATED.** See below.
- **A-30 (audit coverage) — RECORDED** as item 7 of the targeted checklist,
  where the next audit will actually read it.

### No change needed

- **A-22 (`BEARING_FRAME_UNLABELED` gate 1).** Confirmed as recorded, and
  the disposition is **no change**. Three independent reasons. (a) The
  remedy is unavailable to this pass and to any agent: removing the code
  means editing `schema/*.json` and `policy/violation-codes.yaml`, both
  governed Class B. (b) The remedy is not obviously right even for the
  maintainer — the audit's own analysis shows the enum entry is *forced*
  once the decision to materialize warns on the wire is taken
  (`policy/semantics.yaml` gates `schema_violation_allowed_reason_codes`
  and the gateway validates its own diagnostics), and the identical shape
  already ships as `GEO_ZERO_FILL_SUSPECTED` on `origin/main`. (c) The
  broader "warn architecture is over-costly" version was already refuted
  3/3 in this record. Acting on a marginal gate-1 call by deleting shipped
  vocabulary would be the more expensive mistake. Left for the maintainer,
  as the audit intended.
- **A-24 (`measure_packet_size.py` traceback).** **Already closed by the
  tools pass** — re-run at HEAD,
  `python tools/measure_packet_size.py --file examples/zmeta-v1.1-examples.jsonl --summary-only`
  now exits 1 with `measurement refused for OBSERVATION_EVENT/EO: compact
  encodes zmeta_version '1.0' events only, got '1.1.0'` and no traceback.
  No documentation surface promised the old behaviour, so nothing to
  re-baseline here.

### A-21 — what was fixed and what was escalated

The finding has two halves and they resolve differently.

**Falsifiable half — fixed.** `c1eb9d0`'s message justifies the RF edit as
"matching the reference adapter it names", and it did not:
`adapters/ingress/kraken/kraken_to_zmeta.py:35` emits
`features.doa_array_relative_deg` on **every** event unconditionally, and
sets `bearing` + `quality.bearing_frame` + `quality.heading_source` only on
the compensated branch. The example carried the compensated labels and no
array-relative angle at all — so an example stamped
`producer: "kraken-sdr"` depicted a shape that producer cannot emit. The
example now carries `features.doa_array_relative_deg: 45.2`, consistent
with the labelled `bearing.az_deg: 135.2` under a 90° platform heading.
That is a record-accuracy fix of the same class as A-13 and A-18, and
doctrine settles it: an example attributed to a named producer must be a
shape that producer emits, and gate 3 wants the provenance anchor
travelling with the promoted bearing.

*The demotion alternative was considered and rejected:* removing
`payload.bearing` entirely and keeping only the raw angle (the
`AUTHORING.md:147-151` uncompensated pattern) is also honest, and would also
keep the gate green — but the corpus already contains a bearingless
`kraken-sdr` RF event one line down, so demoting this one would leave the
corpus with **two** uncompensated examples and **zero** showing what a
correctly-provenanced compensated bearing looks like. Completing the shape
teaches more and loses nothing.

*Not adopted from the finding:* the characterisation of the RF example as
"a static ground sensor" is **not established** — `sensor-01` carries
`geo.alt_m: 1500.0` and no motion fields either way, and `GPS_COURSE` is one
of the heading-source labels the kraken adapter's own docstring lists
(`kraken_to_zmeta.py:106`). `heading_source` was therefore left alone rather
than churned on an unsupported reading.

**Doctrinal half — escalated, not guessed.** Because `--strict` promotes
warnings to failures and is part of the mandated gate, no shipped example
can demonstrate the legacy-unlabeled bearing that contract §6.4 explicitly
*tolerates*. The only pressure the gate can apply to the corpus is toward
stamping a label. Every available fix lands in `tools/validate_examples.py`
or in new corpus/gate wiring — a change to the mandated release gate's
semantics, which is a maintainer call under gate 6. Logged as
**`docs/zmeta_doctrine_review_log.md` R1-11-14**.

### Pin

`gateway/tests/test_records_claim_currency.py` (new, 7 tests) pins the three
classes rather than the exemplars:

| Test | Class | Family it sweeps |
|---|---|---|
| `test_record_diff_totals_are_not_attributed_to_a_moving_ref` | A-13 | every markdown surface; a total mentioning `HEAD` must carry a commit anchor |
| `test_anchored_diff_totals_still_measure_what_they_claim` | A-13 | every `git diff --shortstat origin/main..<sha>` figure, re-measured against git (4 sites) |
| `test_documented_formal_package_builds_pass_release_notes` | A-17 | every documented `formal_release` build command (4 sites); older-release commands skipped as history |
| `test_handoff_validation_inventory_labelled_historical_while_it_diverges` | A-18 | the handoff inventory vs the newest `VALIDATION_REPORT_v*.md` tool set |

Plus three detector self-tests that assert each oracle **fires** on the
exact defective text, so none can pass by matching nothing. Every check
carries a non-vacuity floor first.

**Revert-simulated, watched fail, restored** — individually, on every family
member: all four A-17 surfaces (4/4 FAIL on revert), all three A-13 record
surfaces (3/3 FAIL), the A-18 label (FAIL), and a stale figure injected at
each of the three anchored-total sites (3/3 FAIL). One revert-simulation
found a real hole while it ran: the A-17 oracle was line-scoped, and the
prose I had added to `README.md` mentioning `--release-notes` satisfied it
while the command on the same line was still broken. The matcher now
captures the command, terminating at a backtick.

**What the pins cannot see** (stated, not hidden):

- The A-13 anchoring check proves a total is *anchored*, and the correctness
  check only re-measures totals presented as the output of a named
  `git diff --shortstat origin/main..<sha>` command. A wrong figure written
  in free prose next to a commit id is not re-measured. A broader matcher
  was implemented and **withdrawn**: it false-positived on a legitimate
  `git show <sha> --stat` figure and on A-13's own quotation of the wrong
  number it documents. A pin that cries wolf on a correct record is worse
  than one with a stated blind spot.
- The A-13 check treats any 7+ hex token on the line as an anchor. A bogus
  anchor would satisfy it.
- The A-17 check reads markdown only. No non-markdown surface currently
  carries the command (grepped across `*.yml`, `Makefile`, `*.ps1`, `*.sh`,
  `*.toml`), but a future CI step would be invisible. It also does not check
  that the referenced notes file exists.
- The A-18 check extracts tool names with the **same regex on both sides**
  — the handoff block and the validation report. A tool family that regex
  cannot see is invisible in both, so the divergence set would be empty for
  the wrong reason. This is the shared-machinery blind spot checklist item 4
  names, in my own pin. The non-vacuity floor (>= 5 tools parsed from the
  block) bounds it but does not remove it.
- All four checks are keyword/shape checks on prose. None can tell a true
  claim from a false one in general; they enforce *form* (anchored, flagged,
  complete) because form is what the five recurrences actually broke.

### For the maintainer / other groups

- The **cut-time** items in this scope stay open by construction: A-29's
  Compatibility bullet needs `release/RELEASE_NOTES_v1.1.17.md`, which does
  not exist yet, and A-12 resolves only through a genuine cut.
- `docs/zmeta_refinement_handoff.md` still carries `465 passed, 110
  subtests` and `total=47 passed=47` beneath the v1.1.12 inventory. Those
  are now explicitly labelled v1.1.12-era and not current; they are correct
  as history and were not re-baselined.
- `tools/README.md` and `release/README.md` were edited (one line each) to
  close the A-17 family. They are documentation, but they sit outside the
  records scope — flagging it so it is not a surprise.
- **New failure mode introduced, stated:** the A-17 fix adds a
  `release/RELEASE_NOTES_v1.1.16.md` literal to four surfaces. For
  `README.md` and `spec/installation-guide.md` that literal is machine-
  guarded (`test_release_currency.py` fails pytest on a stale one) and
  `release/README.md` uses the `<version>` placeholder, so neither can
  silently stale. `tools/README.md` is **not** machine-guarded — but it
  already carried two literals of the same vintage on the same line
  (`package-v1.1.16`, `zmeta-v1.1.16`), so this adds a third instance of an
  existing exposure rather than a new class, and `RELEASE_CHECKLIST.md`'s
  doc-currency step already enumerates "tools README examples". Recorded
  rather than fixed by widening the currency guard, which is another
  group's file.
---

## Disposition pass (2026-07-22) — and why the fixing stops here

**Status: 91 findings dispositioned. 46 open, 2 MAJOR. Still HOLD.**

Maintainer direction: adjudicate `B-01`..`B-04` on whichever of fix-or-revert
is cleaner and more permanent, work everything else per doctrine, and list
whatever doctrine cannot resolve. Ten groups, serial.

### What the pass actually produced

The best result was not volume. **`B-01` was closed one level up from where it
was reported.** The finding named a set-carried oversized integer; driving the
public API with everything the two supported backends can emit showed the class
is the entire non-JSON value model — sets, frozensets, `Decimal`, `datetime`,
`UUID`, `Pattern`, `IPv4Address`, `CBORTag`, simple values, `undefined`,
`complex`, `bytes`, and every non-string map key, several accepted on *both*
backends.

The remedy the finding proposed — widen the container dispatch — provably does
not close it: a plain `{"s": {1,2}}` with no oversized integer still refuses
under `zmeta_cbor` and encodes clean under `cbor2`, because the divergence is
the container's *existence*, not its contents. The rule is now an **allowlist
of the canonical JSON value model** folded into the existing walk. A blocklist
must be re-derived every time a backend learns a new tag; an allowlist refuses
the unknown by construction.

No new normative text was needed: `spec/compact-binary-mapping.md` already
requires refusing anything that would not expand back to a value-identical
canonical envelope. Non-finite floats were simply the one member of that class
the code enforced. **The round-trip check was structurally blind to all of it**
— both sides of the comparison hold the same non-JSON object, so `==` is
satisfied and nothing looks lost.

Revert was evaluated on every finding a previous round introduced, and taken
where it was the right instrument: the SAPIENT uncertainty-widen *control flow*
was reverted and re-derived rather than patched, and the MAVLink `str()`
coercion was deleted rather than fixed.

### The fail-open this pass introduced, and closed

Attacking the above found it. The unhashable-input guard added for `A-14` was
reused at three **risk/trigger** sites where its polarity inverts. At an
allowlist site the caller asks `not contains(...)`, so answering `False` on
`TypeError` refuses — fail closed. At a trigger site the caller asks directly,
so `False` means the risk did not fire and the event is **forwarded**.

Measured, with `allowed_loop_statuses` emptied — the documented "no constraint"
reading, and a legal deployment — a promotion carrying
`loop_status: ["REFLECTION_DETECTED"]` was **admitted**, `always_reject_loop_risk`
included. Under the shipped policy a neighbouring allowlist happens to catch
the same token, so there it degrades to a wrong diagnostic rather than an
admit. Severity is therefore **conditional on configuration**, and the record
says so rather than claiming the worse reading.

The first pin written for it was **itself vacuous** — `assertFalse(ok)` passes
on the reverted tree, because a different gate refuses — and was rewritten to
assert the specific refusal. Recorded because it is the same defect this cycle
has now found in four separate pins, including one written to catch it.

### Why the fixing stops here

| Round | Input | Attack pass found | MAJOR | Introduced by the round itself |
|---|---|---|---|---|
| 1 — fix waves | 6 blockers | 30 | 8 | 2 fixes laundered |
| 2 — remediation | 30 residuals | 32 | 4 | 18 (56%) |
| 3 — disposition | 91 findings | 47 | 3 | **35 (74%)** |

Severity is converging. **Volume is not, and the introduction rate is rising** —
56% to 74%. A fourth round would, on this trend, spend more than it returns.

The trend is not the whole argument, though, and the character of what remains
matters more. The surviving findings are increasingly **trade-off questions
rather than defects**: is discarding a datum better than laundering it, is a
warning storm worse than silence, is refusing a whole detection proportionate
to one malformed vendor key. Those have no derivable answer — they are
maintainer judgements, and an agent resolving them by momentum is precisely
what the governance apparatus exists to prevent.

Design gate 7 binds the fix loop as much as the kernel. **Stopping is the
doctrinally correct action, not a concession.**

### State

- Battery: kernel gate all flags exit 0, examples 51/51 strict, **pytest 1200
  passed + 1021 subtests** (cycle start: 785 + 316). Manifest regenerated.
- **No governed artifact modified anywhere in this cycle.**
  *(CR-04 correction 2026-07-27: true of the fix and disposition passes only — the cycle's earlier waves DID mint three additive `reason_code` enum entries in schema/policy and +6/−1 in contract §5.3, as this record's own "What was touched" inventory states. The claim below is scoped to the passes.)*
  `spec/semantics-contract.md`, `schema/*.json`, `policy/violation-codes.yaml`
  and `policy/semantics.yaml` are untouched; no `reason_code` minted.
- Twenty-one doctrine review log entries across two passes, all OPEN or HELD,
  none decided inside a fix wave. (Recorded as twenty until 2026-07-26, when
  renumbering the addendum exposed a duplicate R1-11-14 hiding one entry.)
- Working tree clean. Nothing pushed, tagged, or signed.

### Carried forward for the maintainer

1. **Two MAJOR open.** `_parse_utc` still raises out of CoT and JREAP on a
   gate-clean `ts` (a "no change needed" verdict resting on a `FormatChecker`
   that is not installed — the verdict, not the code, was the defect); and the
   `A-13` record anchor is only half-anchored, because `origin/main` is a
   moving ref, so the replacement figures go stale exactly as the originals did.
   *(Update 2026-07-27: the `_parse_utc` MAJOR is CLOSED as a class — CoT,
   JREAP, and the SAPIENT egress twins now refuse gate-clean unparseable AND
   naive timestamps per their documented contracts; commits
   `25bb5fa`/`ede9bb6`, every pin red-first verified.)*
   *(Further update 2026-07-27, closeout: **`A-13` is also CLOSED** — the
   records wave `ae42a4d` re-anchored every frozen diff figure to the literal
   base `09118b3` and extended the anchored-totals pin to verify literal-base
   ranges. The pin then fired as designed the moment the push moved
   `origin/main`, catching three remaining unanchored sites. Both
   carried-forward MAJORs are closed.)*
2. **Forty-four further findings** at MODERATE and below, in
   `docs/r1_11_fix_pass_findings.md`. *(Update 2026-07-27: cold re-read CR-03
   established these are NOT itemized in that register — it ends at round 2,
   and the round-3 per-finding detail was never persisted. Maintainer
   decision 2026-07-27: the loss is recorded as final; the set re-derives
   from the tree through the playbook's scoped waves. See the register's
   Status block.)*
3. **Twenty-one doctrine entries** in `docs/zmeta_doctrine_review_log.md`. The
   highest-leverage is not a kernel question: **"governed" has no defined
   boundary**, and it is now parking otherwise-mechanical fixes.
4. **Deferred to the cut:** `A-12` (manifest divergence) and `A-29` (the
   Compatibility bullet naming the three added reason codes).
   *(Closed 2026-07-27: both resolved at the v1.1.17 cut (`7302073`) — the
   manifest was rebuilt under the new identity with explicit provenance, and
   the release notes carry the Compatibility section. Note the pattern rather
   than the instance: post-release commits regenerate the in-repo manifest
   under the current identity, so the divergence re-accrues and is resolved
   again at each cut. It re-accrued after v1.1.18 via the post-cut sweep
   `dd5def7` and will resolve at the next cut.)*
