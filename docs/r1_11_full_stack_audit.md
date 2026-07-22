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
