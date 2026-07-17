# R1-10 Full Stack Audit — 2026-07-16

Class: Docs/advisory (audit record). Non-normative. Audited tree: `main` at
`b826445` (v1.1.13). This document is the complete findings record for the
R1-10 stack audit; the worklog R1-10 entry summarizes it and records the
maintainer disposition.

## Method

- **Lenses.** The audit applied the R1-09 AAR lessons as lenses: (1) teaching
  artifacts as the highest-leverage defect surface, (2) load-bearing
  conventions living only in prose vs machine-pinned enforcement,
  (3) validation evidence that can actually fail (vacuous-pass hunting),
  (4) doc currency/retention after the v1.1.13 cycle, plus (5) a regression
  check of the 2026-07-01 adversarial-audit defect list and governed-artifact
  integrity.
- **Process.** Green baseline established first (full kernel gate, pytest,
  `git diff --check` — all clean). Five independent finder passes (one per
  lens), then **every substantive finding was adversarially verified by an
  independent skeptic pass instructed to refute it** — live probes through
  the real validator chain, exit codes checked, in-repo documentation
  searched for evidence of intentional/deferred behavior. Findings below
  carry post-verification severity, which in several cases is *lower* than
  the finder's initial rating because the governance record documented the
  limitation. The audit was read-only: no repository file was modified; all
  probe artifacts were built outside the tree.
- **Baseline evidence.** `python tools/validate_conformance.py --strict
  --profile-projection --extension-registry --conformance-classes
  --encoding-negative --precision-policy --release-manifest --release-package
  --bad-events --adapter-harness` → `conformance ok` (harness 15, bad-events
  23, encoding 50, precision 32). `python -m pytest -q` → 485 passed +
  110 subtests, zero failures. `git diff --check` clean.

## Verdict

The kernel and the governance apparatus held. The 2026-07-01 fielded-safety
defects (command-altitude smuggling, STATE layer-collapse laundering,
hardcoded calibration labels) are **fixed and verified by fresh probes** on
current main. The release-manifest hash gates detect real tampering
(witnessed). The locked v1.0 schema is byte-stable since v1.1.10, and its two
post-lock diagnostic `reason_code` enum additions were sanctioned, documented,
maintainer-authored Class B changes. Every machine-pinned release surface
(CI compat target, test pins, manifest, checksums, labels, templates) was
correct at v1.1.13.

The defect mass sits in the outer rings, clustered exactly where the R1-09
AAR predicted: **the reference adapters that the authoring guide routes
authors to still carry unfixed instances of the same fabrication class that
v1.1.13 fixed — with machine-checked refusal — on example-vendor only.**
Secondary clusters: latent honesty gaps that no machine check covers
(quality frame labels, geo zero-fill, runtime strip of risk labels), empty
input/coverage vacuities in the checking machinery, and a doc-currency
defect class that is 100% prose-side (all machine-pinned surfaces held).

## Findings — MAJOR (verified by live probe, survived adversarial refutation)

| ID | Finding | Evidence anchors |
|----|---------|------------------|
| A1 | The worked exercise coerces null `platform_id`/`sensor_id` to the literal string `"None"` (fabricated identity, schema-valid, passes the full ladder) while its docstring claims "refusal covers missing and null required values". Null `ts`/feature values ARE refused, so the gap is field-specific, not a design line. | `adapters/ingress/example-vendor/example_vendor_to_zmeta.py:75-78` (claim), `:90-94` (RF-only None-check), `:129,:132` (`str()` coercion) |
| A2 | eo-cv (the designated INFERENCE exemplar) fabricates envelope `confidence: 0.0` when the detection carries no confidence (docstring declares it required; default `confidence_floor=0.0` passes the fabricated value). `confidence: null` crashes `translate()` with TypeError instead of refusing. eo-cv also zero-fills `alt_m` via `altitude or 0.0` — a live contract §6.8 MUST violation — and its README still documents a `(0,0,0)` emission tier the code no longer implements. | `adapters/ingress/eo-cv/eo_cv_to_zmeta.py:12-14,89,135-136,161,250`; `adapters/ingress/eo-cv/README.md:37` |
| A3 | The kraken and moth JSON-replay paths silently invent schema-required RF measurement values on missing input: kraken defaults `bearing_error_deg` 15.0 (also laundered into `quality.measurement_error` as `1_SIGMA`), `power_dbm` −80.0, `center_freq_hz` 0.0, `bandwidth_hz` 0.0; moth defaults `center_freq_hz` 0.0, `bandwidth_hz` 0.0, `power_dbm` −100.0. All resulting events pass `tools/validate.py --profile H --strict`. Undocumented anywhere. moth additionally zero-fills `geo.alt_m` (`sensor_pos.get('alt_m', 0.0)`) — a direct contract §6.8 MUST violation ("If any of lat, lon, or alt_m is missing, omit geo entirely… MUST be omitted, not zero-filled"). Separately, the hardware-path `bandwidth_hz: 0.0` sentinel (kraken CSV, moth serial, signalhunter) is a *documented* convention in the kraken README only — receiver-class sensors physically cannot measure emitter bandwidth — and is undocumented in moth/signalhunter. | `adapters/ingress/kraken/kraken_to_zmeta.py:159,231-234`; `adapters/ingress/kraken/README.md:50`; `adapters/ingress/moth/moth_to_zmeta.py:174,358,411-416,421-423`; `adapters/ingress/signalhunter/signalhunter_to_zmeta.py:355`; `spec/semantics-contract.md:909-918` |
| A4 | The CoT egress reference (operator-display exemplar, live on the gateway `--emit-cot` path) fabricates accuracy and freshness by default: `default_ce=15.0`/`default_le=10.0` stamped when the event carries no uncertainty (CoT's own unknown-value convention, 9999999.0, appears nowhere in the repo), and `use_wall_clock` defaults True so event time is re-stamped to now (stale/replay tracks render fresh) — while the colocated test suite pins wall-clock *off*, so the shipped default path is untested. The README usage example fails validation (`zmeta_version "1.0"` with 1.1-only `geo.error_ellipse_m`), and the `geo.ce`/`geo.le`/`geo.ce_display_m` resolution-ladder rungs are dead code for any schema-valid event (dialect residue). Contract anchors: §4.7/§12.2 prohibit inventing precision; §9.5 restricts wall-clock freshness to explicit replay selection; §14's display-convenience list does not include accuracy defaults. Confidence-only-in-remarks is contract-tolerated (§14), but the conditionality is inconsistent (dropped entirely when `source_summary` present). | `adapters/egress/cot/zmeta_to_cot.py:97-99,125-126,137-138,159-161`; `adapters/egress/cot/README.md:21,39,76-92`; `adapters/egress/cot/test_zmeta_to_cot.py:14`; `gateway/src/gateway.py:1853` |
| A5 | `quality.bearing_frame` / `quality.heading_source` carry a normative value constraint (contract §6.4: `bearing_frame` permits exactly `TRUE_NORTH`; this is the **only** frame-provenance channel for v1.0 producers) that no layer machine-checks: v1.0 `quality` is a bare object, the v1.1 quality `$def` has `additionalProperties: true` and no such properties, and no policy/validator check exists. `quality.bearing_frame: "MAGNETIC"` (and non-string values) pass the full chain clean under both versions, while the v1.1 `bearing.frame` twin correctly rejects. The contract calls quality free-form, so this is an unenforced rule rather than a contradiction — but a mislabeled magnetic bearing consumed as true north is silent geolocation corruption, and the repo's own precedent treats the identical defect class on `bearing.frame` as a must-fail corpus entry. | `schema/zmeta-event-1.0.schema.json:933-935`; `schema/zmeta-event-1.1.0.schema.json:760-803`; `spec/semantics-contract.md:869-883` |
| A6 | A single deployment-config line silently defeats the no-laundering guarantee at runtime: `_strip_optional_fields` pops any dotted path with no protected-path list, so `payload.extensions.risk_adjudication` — declared `never_mutable` by the projection field catalog and protected by the offline projection corpus (`PROJECTION_POLICY_RISK_LABEL_REMOVED`) — can be stripped after policy actions append it and before egress validation, with zero diagnostics. Promotion evidence has an egress backstop (`PRODUCER_NOT_ALLOWED` re-catch, witnessed); risk adjudication has none. All five shipped configs and the wizard are clean, so the defect is latent, not live. | `gateway/src/gateway.py:793-807,1033-1039,1797-1810`; `conformance/profile_projection_field_catalog.yaml:168-173`; `docs/zmeta_change_governance.md:55-56` |
| A7 | Adapter harness: `expect.events` entries at indexes ≥ the returned event count are silently never evaluated, and `event_count` is optional — a fixture with an impossible surplus expectation passes both the harness and the `check_adapter` fixture lint (probed). Without an `event_count` pin, an adapter that stops emitting later events keeps passing. Shipped corpus unaffected (the one `expect.events` fixture pins `event_count: 1`); the exposed population is external fixture authors — the audience the v1.1.13 refusal work targets. | `tools/validate_adapter_conformance.py:292-295`; `conformance/adapter-harness/fixture.schema.json:49-59` |

## Findings — MODERATE

| ID | Finding | Evidence anchors |
|----|---------|------------------|
| B1 | INFERENCE nested-laundering residue: `estimated_state` and `members` are blocked only at `payload` top level and directly under `claim` (schema `false` properties); the recursive semantic backstop's policy denylist contains only `track_id`, so `claim.details.estimated_state`, `vendor_blob.members`, etc. pass clean (probed, parents preloaded). Contract §7.5 uses the same "MUST NOT contain" wording the v1.1.10 pass interpreted recursively for STATE §7.7 and COMMAND §7.8 — the INFERENCE branch was never expanded, with no documented decision. Corpora contain no colliding events; the fix is policy-only. | `policy/semantics.yaml:11-13`; `gateway/src/validators.py:1657-1670`; `spec/semantics-contract.md:1073-1075` |
| B2 | All eight JSONL gate tools exit 0 on empty fixture files with no minimum-count floor (all probed), and `validate_conformance.py` prints `conformance ok` with no counts. Defense-in-depth bounds the exposure: the main CI kernel-gate step includes `--release-manifest`, which hash-pins all 18 `conformance/**` fixtures, so truncation there fails CI. The genuinely unprotected surface is `examples/*.jsonl`: not manifest-pinned (documented deliberate scoping), no count floor, `--require-all` fails only on *missing* files — a truncated-but-individually-valid examples corpus passes every gate including CI. `validate_examples` is also absent from the mandated local kernel-gate command and from pytest. | `tools/validate_examples.py:147-167`; `.github/workflows/ci.yml:47-49,79-85`; `AGENTS.md:113-118`; `spec/release-hash-policy.md:75-108` |
| B3 | `sign_release_artifacts.py --verify-checksums` verifies only the lines present in the SHA256SUMS file — an empty file and a 1-of-7-line file both pass (probed; strictly weaker than GNU `sha256sum -c`, which errors on zero valid lines). The generation step makes a partial file unproducible on the documented release path, so the residual exposure is post-generation tamper and the consumer-facing standalone verify command the README recommends. The same list-only pattern exists in `tools/validate_release_package.py::_validate_checksums`. | `release/sign_release_artifacts.py:81-103`; `tools/validate_release_package.py:216-242` |
| B4 | A `(0,0,0)` zero-filled canonical geo — prohibited twice by contract §6.8 and AUTHORING rule 9 — validates completely clean on OBSERVATION/STATE/FUSION (probed). A hard check is semantically impossible (genuine null-island coordinates exist), so the achievable ceiling is a warn-severity heuristic, which the stack lacks. The eo-cv `alt_m` zero-fill (A2) is live proof the missing check has already admitted drift. | `spec/semantics-contract.md:914-918`; `adapters/AUTHORING.md:104-106` |

## Findings — MINOR (verified; includes items downgraded by the governance record)

| ID | Finding | Disposition context |
|----|---------|---------------------|
| C1 | Command-altitude synonyms (`climb_to_m`, `flight_level`) pass the enumerated denylist — **documented** v1.1.10 "Known Enforcement Limitation" with an explicit accepted-risk rationale and mitigation doctrine (closed payload schemas + producer conformance + allowlist egress, all verified working). Surviving residue: `COMMAND_ALTITUDE_KEYS` in `tools/validate_projection.py:82-89` predates the v1.1.10 expansion and omits `alt_hae_m`/`alt_msl_m`/`target_alt_m` (redundant defense-in-depth, but drifted); a pointer from `policy/semantics.yaml`'s command comment to the documented limitation would prevent re-raising. | `release/RELEASE_NOTES_v1.1.10.md:64-72` |
| C2 | `track_id` lifecycle rules have zero machine coverage (reuse probed clean) — an explicitly **governed deferral**: schema do-not-add decision on record, enforcement surface assigned to fusion services, reserved `TRACK_*` lifecycle vocabulary, roadmap branch with promotion tripwires. Producer-side conformance gap, tracked; not a gateway defect. | `docs/s1_01_v1_baseline_verification_plan.md:71,91`; `spec/future-branch-roadmap.yaml:187-206` |
| C3 | The locked v1.0 schema file received two post-lock additive diagnostic `reason_code` enum entries — both sanctioned, documented, maintainer-authored Class B changes applied to both schemas in lockstep; the lock is defined over semantic invariants, not bytes. Residue: contract §2.1's affirmative allowance list doesn't explicitly cover additive diagnostic-vocabulary widening — a one-line clarification closes the question. | `spec/semantics-contract.md:104-116,1289-1292,1305-1306` |
| C4 | `adapters/ingress/template/adapter_template.py:26` docstring commands **unconditional** `lineage.transform` while schema lineage requires `based_on` (minItems 1) — obeying it literally on parentless readings forces fabricating parent UUIDs. The three surrounding docs state the conditional rule correctly; the copy-me `.py` file is the last residual of the v1.1.12 lineage-honesty class (its README was fixed then; the docstring was missed). | `adapters/ingress/template/adapter_template.py:26` |
| C5 | `policy/routing.yaml`'s `must_pass_through`/`required_origin` key names overstate enforcement — `_is_comms_producer` flattens all three keys into one origin allowlist (probed), and per-event transit verification is architecturally impossible in v1.0 (no route metadata). The normative contract only requires origin gating, which IS enforced — naming/documentation defect only. | `policy/routing.yaml:6-7`; `gateway/src/validators.py:2144-2155` |
| C6 | The conformance-claims validator is structure-only (fabricated hashes/self-declared results validate — probed), which matches the documented claim model ("claims are attestations"; execution-verification is explicitly Future Work). Residue: `spec/conformance-classes.md:112` is misreadable as machine-verified; `PLACEHOLDER_HASHES` is a dead constant and the `pending_D-002` error text is stale; cross-checking claim `contract_hash` against the release manifest is a cheap available hardening. | `tools/validate_conformance_classes.py:87,469-493` |
| C7 | Contract §5.7 says holdover `est_error_ms` "must monotonically increase" while the validator (correctly, for a quantized upper bound) accepts equality and warns on decrease per governed policy — a wording clarification ("must not decrease"), not an enforcement defect. | `spec/semantics-contract.md:775-778`; `gateway/src/validators.py:1431` |
| C8 | Teaching-surface nits: `adapters/README.md` ingress table lists CoT/KLV outputs as "(template)" though harness fixtures pin STATE_EVENT/OBSERVATION_EVENT; mapping-pack README slug convention (`vendor__acme_rf__v1`) contradicts the shipped `example-vendor-pack` exemplar; the two worked example chains model `lineage.transform`-present vs -absent without teaching when each applies (translation steps vs native producers). | `adapters/README.md:40,42`; `adapters/mapping-packs/README.md` |

## Findings — doc currency and retention (all directly verified)

- `spec/installation-guide.md:4,221-224` — stale at v1.1.12. This surface is
  **named in the RELEASE_CHECKLIST doc-currency item** and was missed by the
  release-time pass (the item's second confirmed miss, after the test-pin
  miss pytest caught during the v1.1.13 cut).
- `release/README.md:19-47` — worked release procedure pinned at v1.1.11,
  including a hand-`Compress-Archive` step that **contradicts the reconciled
  checklist rule** ("built automatically… never by hand", RELEASE_CHECKLIST
  as amended in `b2f477e`).
- `docs/zmeta_professional_overview.md:4` — "Current release context:
  ZMeta v1.1.12."
- `docs/zmeta_refinement_handoff.md` — internally contradicts itself: header
  says v1.1.13 but lines ~184-185, ~229-242, and ~390 still describe v1.1.12
  as current; Key Docs rows mark v1.1.12 release files "publication pending"
  (published 2026-07-08); the Resolved-Recent-Findings follow-ups still list
  the UDP oversize OSError and adapter lineage fabrication as open although
  v1.1.12 fixed both; four generations of Verification State blocks retained
  ("Most recent validation" label now false); Next Work Queue has duplicate
  item numbering.
- `tools/check_compat.py:93` — CLI default target `"v1.1.10"` (three releases
  stale; the checklist item requires extending `TARGETS` but not the default).
- `release/build_mvp_packages.py:5` (`VERSION_TAG = "v1.1.12"`) and
  `release/build_release_bundle.py:5` (`VERSION = "1.1.12"`) — same stale
  script-default class as the `sign_release_artifacts.py` default the AAR
  caught and fixed; these two siblings were not enumerated.
- `docs/zmeta_refinement_worklog.md:265,320` — stale present-tense claims
  ("Current next work item…", "Current decision: v1.1.10 is the current
  formal release target") inside the rolling resume note.
- `SHA256SUMS_*.txt` files carry CRLF line endings; plain `sha256sum -c`
  on Linux fails on every entry (hashes are correct; the repo's own verifier
  handles it). Affects the published verification instructions for Linux
  consumers.
- Pattern: **every machine-pinned currency surface was correct; every defect
  lives in prose** — the natural machine encoding is a currency test that
  fails when enumerated current-facing surfaces disagree with the manifest
  `release_id`.

## Refuted / not defects

- Holdover equality acceptance (see C7) — refuted as a code defect; the
  implementation is arguably more correct than a strict-increase reading.
- Examples corpora absent from the release manifest — documented deliberate
  scoping in `spec/release-hash-policy.md`, not an oversight (the residual
  gap is the missing count floor, B2).
- "CI does not gate examples" — false; CI runs
  `validate_examples.py --strict --require-all` on every push/PR. The gap is
  the *local* mandated gate and truncation (not deletion) coverage.
- Checksum coverage as a release-flow hole — the generator makes partial
  files unproducible on the documented path (residual is standalone/consumer
  verification, B3).

## Positive assurance (witnessed, not assumed)

- 2026-07-01 defect regression: command-altitude smuggling — all 9 policy
  spellings × placement × depth × case variants rejected (32 probes), plus
  the MAVLink egress guard independently rejects all variants; STATE
  layer-collapse — all 9 §7.7 keys rejected at every nesting shape (14
  probes); calibration hardcodes — all ingress adapters now default
  UNCALIBRATED or derive labels from source (verified per adapter).
- External-promotion enforcement is real: six evidence-tamper probes all
  rejected (`PRODUCER_NOT_ALLOWED`), intact baseline accepted.
- Release-manifest gate detects artifact tampering (`ARTIFACT_HASH_MISMATCH`
  + `SELF_HASH_MISMATCH` witnessed); checksum tamper and missing-artifact
  detection witnessed; refusal fixtures fail when refusal is removed
  (witnessed); 11 gate families positively witnessed failing on real
  violations.
- Governed-artifact integrity: manifest verification green for
  zmeta-v1.1.13 (70 artifacts); v1.1 schema changes across v1.1.0→v1.1.13
  are additive/optional only; locked v1.0 schema byte-stable since v1.1.10.
- Zero pytest skip/skipif/xfail markers in gateway/tests; no swallowed
  assertions found.

## Maintainer disposition (2026-07-16)

Recorded direction: **fix every audit finding, then run a follow-up audit.**
The fix pass covers, in dependency order: (1) the reference-adapter honesty
pass (A1-A3, C4, C8 — code fixes plus refusal-fixture rollout, superseding
and expanding the previously queued rollout item; includes documenting the
receiver-bandwidth sentinel convention in the moth/signalhunter READMEs to
match kraken); (2) CoT egress honest defaults (A4 — wall-clock off by
default, unknown-value accuracy convention, README/example corrections);
(3) the machine-encoding batch (A5 additive v1.1 quality constraints +
version-agnostic semantics check + corpus entries; A6 protected-path strip
guard; A7 fixture-schema `event_count` requirement + harness surplus-expect
check; B1 policy denylist completion; B2 empty-input floors + examples gate
wiring; B3 checksum coverage cross-check; B4 zero-fill warn heuristic; C1
projection key-set alignment; release-currency test); (4) contract wording
clarifications (C3 §2.1, C7 §5.7 — permitted under §2.1's own clarification
allowance, Class B handling with manifest regeneration); (5) the doc-currency
and retention sweep (all items above, plus C5/C6 documentation residues);
(6) governed-artifact regeneration (release manifest + conformance claims)
and full-gate revalidation. The v1.1.0 adoption-decision session, the five
deferred P1-06 maintainer decisions, PR #4 status, and release signing remain
queued behind the fix pass and the follow-up audit.
