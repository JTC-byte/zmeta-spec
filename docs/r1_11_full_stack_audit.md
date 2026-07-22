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

## Execution continuity — interruptions and recovery

This cycle was executed across **four sessions broken by usage limits**,
plus a mid-cycle model switch and one full chat reset. That is recorded
here in detail because interrupted work is a defect surface in its own
right, and because the fresh audit should target it (checklist below).

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

Until that audit runs and the maintainer takes the release decision,
this cycle stays local and unpublished.
