# ZMeta Refinement Worklog

## Current Resume Note

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
- **2026-08-13 (RF zero-fill adjudication and mint, v1.1.25).** The
  focused session handoff item 19 was booked for, run the day it was
  booked, with three maintainer adjudications recorded in X2-04: mint
  now, as completion of the zero-fill laundering class the geo code
  established, rather than holding a single field instance against the
  occurrence rule; the paired predicate, re-adjudicated after the
  pre-cut verification pass measured that the first-draft
  bandwidth-alone trigger would have failed the documented
  receiver-class sentinel on five adapter families under strict mode
  (kraken, moth, signalhunter, sapient, and the experimental adsb
  power path). The pair predicate: bandwidth_hz and power_dbm both
  exactly 0.0 triggers, and only the pair, because no shipped adapter
  emits a power sentinel, the pair is the exact fabrication shape the
  field evidence measured, and it scopes the check to the RF family
  without a modality gate. The third adjudication was the v1.0
  wire fallback to GEO_ZERO_FILL_SUSPECTED with its cross-family
  overload recorded deliberately. The severity question answered itself
  during grounding: the locked contract states the zero-fill
  prohibition for geospatial data only (6.8), so warn is the ceiling by
  construction, and the generalized form is recorded as
  versioned-semantic-branch material rather than minted. Shipped
  surfaces: the violation registry, the semantics allowed-code list,
  the validator heuristic walking the same three feature containers as
  its geo analogue (payload, claim, estimated_state, per the R1-11
  A-16 lesson), the 1.1.0 schema lane's reason-code enum, the
  documented v1.0 wire fallback with the minted code native in
  metrics.diagnostic_code, two bad-event corpus warn vectors (the
  corpus's first warn-severity entries, one at payload level and one
  under an inference claim), and an eight-case unit suite including the
  sanctioned-sentinel non-trigger, the one-milliwatt non-trigger, the
  estimated_state container (the A-16 blind spot, proven in-repo per
  P2-D1), the negative-zero and integer-zero pair shapes, and the
  wire-shaped junk paths. The v1.0 byte-anchor guard fired mid-mint on a first draft
  that touched the locked lane's enum and forced the documented
  post-lock path, which is the lock defending its own bytes in real
  time. Field evidence credit: Barrett Downs (Torch). The corpus
  vectors are synthesized fresh; the motivating events live in a
  private, not-for-publication bundle.
- **2026-08-13 (lockdown completion: the remaining menu executes).** Four
  items close the lockdown list. The containerized gateway wire path was
  verified live at v1.1.24 (container boots with the release's contract
  hashes; a valid event round-trips the container boundary with its
  event_id intact; a profile-mismatched event yields a wire-visible
  SCHEMA_VIOLATION diagnostic), clearing the Docker known-limits item both
  2026-08-13 validation reports disclosed; the result is recorded in the
  live-test checklist's deployment section. The battery command literal is
  single-sourced (apparatus lever 1): the six documents that define the
  governed battery now state the same four commands, adding the roadmap
  validator everywhere and the examples validator where it was omitted,
  and `gateway/tests/test_battery_single_source.py` holds the canon and
  checks the omission direction the old flag-existence check could not.
  Three of the six documents (AGENTS.md, CONTRIBUTING.md, and the change
  governance doc) are hashed in the manifest's process_governance group,
  so the release manifest was regenerated under the published v1.1.24
  identity per the post-release rule in AGENTS.md; published checksums
  are untouched and the divergence reconciles at the next cut. The
  worklog retention pass moved the resume-note entries from 2026-08-03
  back through the v1.1.9 era to the archive verbatim (2,079 lines); the
  live note keeps the current release family, and the entry-coverage
  floor in the changelog guard was re-derived to match, with the rule
  stated that retention never archives the newest entry. Branch hygiene:
  the merged review/pr2-frame-fixes branch and its stale worktree are
  deleted (content contained in main); backup-pre-scrub is kept pending
  an explicit maintainer call, because it is an unmerged snapshot and
  deleting it is irreversible.
- **2026-08-13 (apparatus retire-or-keep decisions, first-contact guidance).**
  The maintainer adopted the full recommendation set for the apparatus
  audit's retire-on-condition and maintainer-call items, and the
  executable ones landed the same day. Retired or consolidated: the
  one-test packaging module folded into the release-package suite; the
  r1_11 closure probe archived out of docs/ (playbook citation updated,
  the frozen records untouched). Curated: deployment bundles exclude the
  simulation harnesses and the demo wizard, the dist bundle excludes the
  harnesses and keeps the wizard as onboarding, pinned at the builders'
  ignore seam; the wholesale-docs concern from the audit was measured
  already-solved (the PC-09 file-by-file listing ships the declared
  seven-file process-governance set, of which exactly two live under
  docs/, rather than the whole docs/ tree). Re-wired: the two live runtime harnesses become
  a named checklist step for runtime-code cuts. Declared: the s1_*/r1_*
  records are frozen with their evidence-pointer guarantee, and the
  records-currency guard documents its r1_11 coupling in place. Kept with
  recorded reasons: the governed baseline (load-bearing since the
  baseline-before-bump rule), the public worklog archive, the live-test
  checklist (the exercise it stages has not run), and the sim import
  boundary, whose drafted retirement condition inverted once curation
  landed: with sim out of every bundle, the guard is the only in-repo
  detector of a governed import that would break shipped bundles while
  the repo battery stays green. The compat module pair closed as no-twin
  (CLI wraps library, both referenced). Separately, the authoring guide
  gained a first-contact section teaching the two failure classes the
  external replay measured, and the slot-token guard now checks
  event_subtype and event_type vocabulary on lines naming those slots.
- Last updated: 2026-08-13 (fix wave; guards landed; v1.1.24 cut)
- **2026-08-13 (fix wave: the queued guards land, the stack relocks).**
  The post-merge fix wave, all outer-ring: no schema, policy, contract, or
  corpus file moves. Landed: the validate CLI lane fix with its guard
  tests (the CLI had diverged from the gateway's lane validation and was
  the one surface losing branch diagnostics); the timing-helper degrade
  fix with helper-level and adapter-level tests, closing the PR #8 open
  finding per the maintainer's contract decision (degrade, widen the
  bound, document that the invalid token is not preserved); the claims
  release-hashes currency gate (X2-01 CHANGED); the changelog-guard
  mechanism fix (X2-03 CHANGED, worked-on date from entries, loud sentinel
  mismatch); the signing-continuity extension to the completeness gate
  with attributed-exemption escape; the slot-scoped doc-token guard, which
  caught two further live instances of the GPS prose defect in
  adapters/README.md on its first run; the shared snapshot-exclusion
  module unifying both markdown walkers, with the stale-worktree
  reproduction pinned in-repo (the P2-D1 artifact the carve-out lacked);
  check_adapter discoverability lines in CONTRIBUTING.md and the
  mapping-packs README; and the publish-path CRLF hardening
  (.gitattributes plus two checklist steps) from the v1.1.23 upload
  incident. The RF zero-fill check is deliberately not minted: it is
  booked as handoff item 19 with its design caveat, because the predicate
  needs adjudication that a fix wave should not decide in its own
  momentum. The pre-cut adversarial pass then caught two blocking
  regressions in the wave's own first draft and both were fixed before
  the cut: the degrade guard crashed on unhashable wire values (the A-14
  class the repo had already named), and a NaN error bound rode the
  degrade into a schema-clean event that the previous code's schema gate
  had rejected, a laundering regression in exactly the direction design
  gate 3 forbids. The NaN fix itself then collided with SAPIENT's pinned
  refusal contract (degradation never substitutes a clean value for a
  poisoned one) and the battery adjudicated: the shipped mechanism passes
  a claim with a poisoned bound through untouched for downstream refusal
  instead of partially cleaning it, which also restores the pre-wave
  schema rejection. The same pass corrected a false historical claim in the
  completeness gate's comment (v1.1.2 through v1.1.4 track all three
  signatures, so they are now a checked signed regime), widened the
  worklog-entry regex to the em-dash heading form it had missed, pinned
  the claims gate to an exact key set after a deletion probe walked past
  its floor, and scoped the snapshot prefix rules to directories. The
  wave's own guards were verified by mutation before the cut: every
  reverted fix kills its test.
- Last updated: 2026-08-13 (PR #8 merged; record corrections; v1.1.23 cut)
- **2026-08-13 (PR #8 merged; record corrections).** The force-pushed branch
  was re-reviewed end to end: the three accepted commits are byte-identical
  to the first review, the withdrawn registration left zero residue across
  policy, claims, manifest, and export surfaces, and the full battery
  reproduced the contributor's reported tallies exactly. Merged as
  `36345fb`. The held proposal's disposition is logged in the doctrine
  pressure log (cycle X2): withdrawn by the contributor after review; the
  discoverability need it identified is queued for an in-house,
  non-governed solution with credit to Barrett Downs. This commit also
  completes the record for the 2026-08-12 errata wave, which landed without
  its changelog entry or worklog note (a maintainer-side instance of X2-03,
  caught by the second review's merge probe), applies wording corrections
  to the merged entries, and restores the 2026-08-10 resume-note line the
  merged docs commit removed.
- Last updated: 2026-08-11 (external verification follow-up; three drift fixes)
- **2026-08-11 (external verification, documentation consistency).** A field
  verification pass found four defects; the three documentation and
  scan-consistency fixes accepted from it are recorded here.
  The governed-document profile scan included stale repository copies under
  `.claude/worktrees/`; that snapshot path is now excluded with the other
  non-current trees. The sibling repo-wide markdown walker in
  `test_records_claim_currency.py` carries the same exposure; the
  shared-exclusion fix is queued. The profile-projection README omitted
  `PROJECTION_POLICY_RISK_LABEL_REMOVED` and
  `PROJECTION_EXTERNAL_PROMOTION_EVIDENCE_REMOVED` from the failure-code list
  it presents as the stable reference, and the SAPIENT README named
  `UNITS_UNSPECIFIED` where the adapter emits
  `COORDINATE_SYSTEM_UNSPECIFIED`. Both README fixes add set-equality tests
  against their implementation sources, so missing, extra, and misspelled
  entries fail together. The review initially asked for a record of four fixes.
  Maintainer review held the fourth proposal because its runtime diagnostic is
  intentionally outside policy severity machinery; the branch now contains
  and records the three accepted fixes.
- Last updated: 2026-08-10 (v1.1.22 cut prepared; doctrine cycle C1)
- **2026-08-10 (external review, fix wave, v1.1.22 prepared).** An
  independent technical review compared ZMeta against ten standards without
  raw-byte access to the normative files. Its own findings were roughly a
  third accurate: correct that no per-event integrity exists and that
  covariance and sequence primitives are absent, wrong on the UUIDv7 version
  nibble, schema-level laundering guards, deduplication and deterministic
  CBOR, and stale on 2-D geo, the `event.ts` pattern and the v1.1.21 code
  mint. Every claim was verified against the tree with file and line before
  anything was acted on, and most of what shipped came from that verification
  rather than from the review. Landed: the MAVLink altitude-datum fix (MSL
  was being published as canonical HAE, the third appearance of a class ADS-B
  already refuses at the source), a gateway diagnostic for an unparseable
  `event.ts` that had been passing schema-clean and silent on the locked v1.0
  lane, twelve malformed-timestamp conformance vectors the governed corpora
  never carried, removal of a format checker that validated nothing at a
  dozen call sites, a roadmap home for cooperative-mesh gap detection, and
  the return of `validate_future_roadmap.py` to the gate battery. Doctrine
  cycle C1 opens with eleven entries, six left open with their evidence.
  The kernel does not move: schemas, policy and the contract are
  byte-identical, and the only governed artifact that changed is the
  conformance corpus. Battery 1757 passed with zero failures, kernel gates
  exit 0, examples 51/51. v1.1.22 is cut and unpublished: notes, report,
  manifest and verified checksums exist; tag, signing and upload remain the
  maintainer's. The prioritized backlog this left is the top section of
  `docs/zmeta_refinement_handoff.md`.
- Last updated: 2026-08-03 (session closeout; repo enters maintenance mode)
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
