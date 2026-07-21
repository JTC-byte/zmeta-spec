# ZMeta Refinement Handoff Notes

Status date: 2026-07-17

Current release: **v1.1.14** (R1-10, 2026-07-17) — the audit-driven
honesty hardening cut: the R1-10 full stack audit, its
fix-every-finding pass (reference-adapter fabrication class closed,
prose-only honesty invariants machine-encoded, checking machinery made
falsifiable, four governed diagnostic codes added to both schemas'
reason_code enums as Class B), and the post-fix verification audit,
released per RELEASE_CHECKLIST. Checksums-only; signing remains the
maintainer's external process. Details in the worklog R1-10 entries and
`release/RELEASE_NOTES_v1.1.14.md`. The queued v1.1.0
adoption-decision session remains the next substantive work item.

This note is the quick resume point for the current ZMeta refinement effort. Recent session records and the deferred issue register are in `docs/zmeta_refinement_worklog.md`; completed task sections S0-01..R1-05 are archived verbatim in `docs/zmeta_refinement_worklog_archive.md`.

## Current Position

The semantic contract has been audited, rewritten, and crosswalked against the current implementation stack. The locked v1.0 baseline was verified, and no S1-01B targeted schema implementation task is currently needed. Profile projection preservation has been implemented and audited as sidecar conformance tooling without changing v1.0 schema or event vocabulary. The extension registry has been implemented and audited. The conformance class manifest and claim model have been implemented and audited without changing schemas or making new vocabulary valid. Encoding-negative validation has been implemented and audited for compact CBOR and protobuf invalid-after-decode paths. Profile precision and quantization policy has been implemented and audited as a reference conformance default. The D-011 `TAKEOFF` crosswalk cleanup is complete. The D-001 MAVLink ingress README state payload drift cleanup is complete. S1-09A planned the contract hash and release hash follow-up for D-002, S1-09B implemented the reference release hash policy, manifest, builder, validator, claim hash updates, and optional conformance integration, and S1-09C audited that implementation and closed D-002. S1-10P removed FORGE-derived organizational artifact scope from the ZMeta baseline. S1-10B was stopped before commit, no stopped implementation files remain, and D-004 is closed as removed from ZMeta scope. S1-11A planned the D-003 future versioned semantic branch roadmap and left D-003 open as roadmap-planned. S1-12A planned formal release tag, signature, checksum, and attestation packaging for D-012, S1-12B implemented the release packaging framework without creating real tags/signatures/keys/secrets or semantic drift, and S1-12C audited it and closed D-012. R1-01 published `v1.1.5` from commit `d4d406b43a705ca5b7a314e1d5388c3ca39c750a` with release notes, validation report, release manifest, release package zip, edge/gateway/source bundles, and checksum manifest. S1-13A audited the stack for semantic conformance and stale files, corrected the live compatibility checker/CI target to `v1.1.5`, added explicit v1.0/v1.1.0 observation extension boundary tests, and closed D-009 without changing schemas, policy, adapters, encodings, the semantic contract, or event vocabulary. S1-14 implemented external projection promotion hardening so CoT/JREAP/MAVLink ingress state must carry policy-scoped promotion evidence before becoming authoritative ZMeta state, with operator-tunable reject/warn/degrade/quarantine modes that preserve diagnostics and bandwidth discipline. S1-15A added the risk adjudication semantic baseline: locked/tunable/advisory rule classes, bounded policy actions, filterable risk diagnostics, and operator override constraints. S1-15B conformed the stack to that baseline across policy use limits, validator diagnostics, gateway runtime degradation labels, conformance fixtures, tests, schemas, and docs. S1-15C cleaned up feedback on the contract text, conformance classes, claims, crosswalk, and future-only boundaries. S1-16A added the semantic bad-event corpus and shared adapter harness, promoted generic adapter and CoT projection conformance evidence, and kept broader sensor-adapter certification as planned future work. S1-16B added the kernel-protection doctrine: ZMeta is complete without becoming exhaustive, future core changes must clear a concrete need threshold, and `FUTURE_EXTENSION` remains non-claimable until versioned adoption. S1-17A audited the tracked stack against that doctrine, added full kernel-protection conformance to CI and Makefile, and clarified policy/config tunability boundaries. S1-18A added consumer-side risk filter tooling so operators can choose display, fusion, command, autonomy, AAR, or audit intake posture using existing risk labels without mutating events. S1-18B completed an end-to-end stack and runtime audit, hardened direct CoT egress so malformed state payloads carrying raw observation/evidence fields fail closed, and confirmed the full local validation/runtime/package sweep passes. R1-02 published `v1.1.6` from commit `a42f1b1d538cf2f2318a81203f28d7c656c22ce8`. P1-01 addressed partner feedback by adding post-v1.1.6 integration guidance for external-promotion metadata, clarifying that `trust_ref` is policy-scoped evidence rather than proof of authenticity, strengthening consumer responsibilities for accepted-risk labels, and adding `tools/lint_policy_risk_modes.py` with tests to flag unsafe `ignore` settings on material risk. P1-02 added machine-checkable profile-projection preservation for `payload.extensions.risk_adjudication` and compact `payload.extensions.external_promotion` evidence, strengthened extension registry entry metadata for projection/risk/security/fixture behavior, and rebuilt the current-main release manifest plus example claim hashes. P1-03 added `AGENTS.md` and `docs/zmeta_change_governance.md` as the formal human/AI agent change process, linked them from README/release surfaces, and added governed `process_governance_hash` release-manifest coverage plus downstream clone compatibility limits. R1-03 audited the stack for stale current-release references, ignored local build residue, tracked-source secret risk, and generated artifact residue, then prepared v1.1.7 as the current formal patch release without changing schemas, event vocabulary, or the locked v1.0 semantic kernel. P1-04 (branch `worktree-bearing-frame-fixes`, dated 2026-06-11) closed the bearing reference-frame ambiguity: semantics-contract section 6.4 now normatively requires canonical `payload.bearing.az_deg` to be degrees true north with a convert-or-omit rule for sensor-native frames; the v1.1.0 schema gained an optional `bearing.frame` marker with single-value enum `["TRUE_NORTH"]` (v1.0 untouched and still rejecting the key); the extension registry gained the experimental `BEARING_FRAME` entry; the bad-event corpus gained `observation-bearing-frame-mislabeled` (total 10); the adapter harness gained a value-pinning `expected_values` mechanism (1e-6 numeric tolerance, distinct missing/mismatch codes, boolean pins never match numbers) with the kraken rotation math pinned and a no-heading convert-or-omit fixture (total 9); the Kraken adapter (1.1.0) gained platform-heading compensation and stopped fabricating CSV SNR; the Moth adapter (1.1.0) stopped fabricating omnidirectional bearings; SignalHunter (1.0.1) asserts `TRUE_NORTH`/`GPS_COURSE` provenance for geodesically constructed gradient LOBs; the MAVLink adapter (1.1.0) omits unknown headings (`hdg=65535`/absent) and refuses null-island `(0, 0)` TRACK_STATE fabrication; and the gateway gained opt-in `warn_datagram_bytes` oversize-datagram observability plus a decision-preserving rate-limiter stale-window purge. P1-04 also recorded two verified deferred findings, D-013 and D-014; S1-19 closed them on current `main` with governed timing negative-age diagnostics and compact unknown-integer-key rejection.

Current stack status:

- S1-24 (2026-07-03) prepared the v1.1.10 fielded-safety enforcement release on
  current `main`, aligning policy and reference enforcement with the
  already-normative semantics contract §7.7/§7.8. No schema or v1.0/v1.1.0
  vocabulary change; tightened enforcement rejects events that were always
  contract-violating.
  - Command altitude: `command_event.payload_must_not_contain` now carries the
    full §7.8 set (bare `alt` retained as a superset); `COMMAND_EVENT` altitude
    is refused at any nesting depth (payload/target_geo/geometry/extensions).
    The egress MAVLink command→mission-intent altitude guard was aligned to the
    same set.
  - STATE laundering: the STATE branch in `gateway/src/validators.py` now
    recurses via `_find_forbidden_key` (case-insensitive, reports
    `{field, path}`) like its sibling branches and enforces the full §7.7
    raw-artifact list; deep-nested raw features/measurements/observation
    timestamps/data-refs no longer launder into a STATE projection.
  - Adapter honesty: Kraken and Moth no longer hardcode
    `quality.calibration_state: CALIBRATED`; it is now a keyword parameter
    defaulting to the conservative `UNCALIBRATED`, asserted otherwise only when
    a deployment substantiates it. SignalHunter was already honest.
  - Hardening from adversarial verification: the semantic forbidden-key check
    (`_find_forbidden_key`) and the egress MAVLink altitude guard now
    strip+casefold keys before matching, closing a whitespace-/case-padding
    bypass of the exact-name denylists across all four event families. The
    residual — arbitrarily *renamed* raw content/altitude in free-form objects
    (e.g. `z_m`) — is the inherent limit of a name denylist (closed schemas +
    producer conformance are the mitigation, not denylist growth).
  - Coverage/validation: eleven new deep-nested (schema-valid) bad-event
    fixtures in `conformance/bad-events/must-fail.jsonl` (total 21) plus two
    direct `validate_semantics` unit tests; enforcement was adversarially
    verified with 100+ empirical bypass attempts. The release manifest and
    example claims were regenerated for `zmeta-v1.1.10` (2026-07-03). The full
    kernel gate (incl. `--release-manifest --release-package --bad-events
    --adapter-harness`) and pytest (`444 passed`, 110 subtests) are green.
  - R1-06: the release authority published `v1.1.10` on 2026-07-04: annotated
    tag `v1.1.10` on release commit `6ce4f29`, GitHub release with all seven
    expected assets plus `SHA256SUMS_v1.1.10.txt`, GitHub CI green for the
    pushed release commit. Published checksums-only, consistent with v1.1.5
    through v1.1.9; detached signatures remain an optional release-authority
    step. Published v1.1.9 assets/checksums are unchanged.
  - Post-publication alignment (2026-07-07): current-facing docs, tool
    examples, the CI compatibility target, and the compatibility CLI test were
    aligned with the published `v1.1.10` release (README, installation guide,
    tools README, professional overview header, `.github/workflows/ci.yml`,
    `gateway/tests/test_check_compat_cli.py`). No published release assets,
    manifests, checksums, tags, or signatures were changed.
- S1-25 (2026-07-07) prepared the v1.1.11 field-driven adoption-guidance
  release on current `main`, harvesting upstream PR #4 (a v1.2.0 proposal
  from a live at-scale deployment; reviewed, found kernel-breaking, and NOT
  merged — review posted on the PR with empirical evidence).
  - Advisory docs (Class A): `docs/zmeta_mqtt_binding_guidance.md`,
    `docs/zmeta_vocabulary_crosswalk.md`, and
    `docs/zmeta_correlation_pattern.md` re-derive the PR's fielded needs from
    the locked kernel outward — locked-vocabulary MQTT topic shapes with
    retain/tombstone honesty rules, a dictionary-to-alphabet concept
    crosswalk, and cross-sensor correlation expressed entirely in existing
    v1.0 vocabulary (FUSION identity + INFERENCE/ASSOCIATION bonds with the
    atomic-split invariant credited to the PR).
  - Governed baseline (Class B): four extension-registry entries —
    `CORRELATION_HINT` (proposed), `DATA_REF_MEDIA_METADATA` (proposed,
    future branch), `AGGREGATE_STATE_SNAPSHOT` (reserved),
    `PAYLOAD_SCHEMA_URI` (rejected with rationale so the concept is not
    re-litigated). No new vocabulary becomes valid.
  - Examples/conformance: `examples/zmeta-correlation-pattern-examples.jsonl`
    (7 events, Profile H, registered in `tools/validate_examples.py`) and two
    bad-event fixtures (corpus total 23) proving the correlation hint cannot
    launder `confidence`/`track_id` into observation payloads.
  - Intake doctrine applied (standing): external PRs are field telemetry —
    harvest requirements, re-derive from the kernel outward, never merge
    dialect surfaces, record rejections in the registry, credit contributors,
    and compare our implementation against the contributor's revisions.
  - R1-07: `v1.1.11` was published on 2026-07-08 with explicit release-authority
    direction: annotated tag `v1.1.11` on release commit `922f0ca`, GitHub
    release with all eight expected assets including `SHA256SUMS_v1.1.11.txt`,
    CI green for the pushed release commit. Published checksums-only,
    consistent with v1.1.5 through v1.1.10; detached signatures remain an
    optional release-authority step. Published v1.1.10-and-earlier
    assets/checksums are unchanged.
- S1-26 (2026-07-08) prepared the v1.1.12 governance and honesty closeout
  release on current `main`, working the full relock-gap list per explicit
  maintainer direction. No schema or v1.0/v1.1.0 vocabulary change.
  - Promotion evidence bar (governed docs): `spec/extension-registry.md`
    "Promotion Evidence Requirements" — reserved/proposed concepts enter a
    named version branch only with two or more independent implementations
    demonstrating the need plus a documented contract Section 2.6 failure
    condition the outer rings cannot solve; referenced from the
    change-governance Class D checklist. Encodes the intake doctrine
    (external PRs are field telemetry) into governed process.
  - S1-11B implemented (governed baseline): `spec/future-branch-roadmap.yaml`
    and `.md` — 18 candidates with status, priority, dependencies, required
    surfaces, recorded evidence, and promotion tripwires (including the
    PR #4 tranche-3 candidates and honesty-primitive schema standing), plus
    3 recorded rejection/defer decisions; validated by
    `tools/validate_future_roadmap.py` (registry cross-references, tripwire
    coverage, status-leakage check) with focused tests; new
    `future_branch_roadmap` release-manifest group (groups=19,
    artifacts=70). D-003's closure condition was met; closure was
    recommended and the maintainer closed D-003 at the v1.1.12 cut.
  - Lineage honesty (runtime/reference): kraken/moth/signalhunter/klv/
    mavlink/eo-cv no longer fabricate `lineage.based_on` with random
    UUIDv7s. Observation/system outputs omit lineage unless callers pass
    real `based_on`; mandatory-lineage events refuse to emit without real
    parents (mavlink STATE: `based_on`/`source_zmeta_event_id`; eo-cv
    INFERENCE: `parent_event_ids` or UUIDv7 `source_event_id`). Adapter
    versions bumped; harness fixtures pin the honest behavior (total 11);
    new eo-cv test file; ingress template README states the never-fabricate
    rule (omit or refuse).
  - Gateway containment (runtime): `_send_datagram` catches OSError on the
    two UDP send paths (oversize ~65507-byte payloads previously crashed the
    main loop), drops the datagram with new `send_failure`
    metrics/diagnostics, and counts forwarded/CoT only on actual sends;
    real-socket oversize test included.
  - Documentation honesty (advisory): mapping packs documented as
    declarative descriptions plus test evidence (no runtime engine executes
    `mapping.yaml`); professional overview documents policy + conformance as
    the deliberate enforcement home for `risk_adjudication`/
    `external_promotion`, with schema standing parked as an evidence-gated
    roadmap candidate.
  - Process closeout: the open-ended human-decision list in this handoff is
    resolved to standing defaults (see Next Work Queue); genuinely open:
    release-signing process (maintainer generating a signature, 2026-07-08)
    and v1.1.0 adopted-vs-experimental status.
  - Validation: full kernel gate, roadmap validator, strict examples
    (47/47), policy lint, pytest (465 passed, 110 subtests), workflow
    end-to-end (H/M), live gateway (JSON/compact), gateway self-tests,
    check_compat `v1.1.12` for all eight corpora, packet-size max=150/240,
    release package validation, and verified `SHA256SUMS_v1.1.12.txt`.
  - R1-08: `v1.1.12` was published on 2026-07-08 with explicit
    release-authority direction: `main` and the annotated tag pushed
    (release commit `e5a88b1`), GitHub CI green, GitHub release with all
    eight assets, marked Latest, checksums-only (the maintainer is standing
    up the signing process for the next release). Post-publication
    alignment moved current-facing docs, the CI compatibility target, and
    the compatibility CLI test to `v1.1.12`, and D-003 was closed by
    maintainer decision — the deferred issue register is now fully closed.
- P1-06 (2026-07-15) added the onboarding batch on current `main` (Class A +
  Class C reference; no governed-artifact change): README first-contact
  restructure (ten-minute proof, Start Here By Role, ZMeta In The Field),
  the `adapters/ingress/example-vendor/` worked exercise, the
  `tools/check_adapter.py` one-command ladder wrapper plus advisory harness
  fixture schema, GitHub issue/PR templates, the `docs/README.md`
  guidance-vs-process index, worklog retention (S0-01..R1-05 archived to
  `docs/zmeta_refinement_worklog_archive.md`), and standing RELEASE_CHECKLIST
  doc-currency/retention items. Maintainer decisions deferred: naming the
  fielded deployments in ZMeta In The Field; the MAVLink template-file
  rename; RF golden sample pairs (need sanitized field captures); the
  physical docs/process/ move; a mechanical conformance-claim generator.
  Details in the worklog Current Resume Note.
- P1-05 (2026-07-15) added adapter-author onboarding consolidation on current
  `main` (Class A; no schema, policy, vocabulary, or validation-behavior
  change): `adapters/AUTHORING.md` as the single consolidated authoring entry
  point for humans and AI agents (linked from `adapters/README.md`), plus the
  worked EO full-chain corpus `examples/zmeta-eo-chain-examples.jsonl`
  registered in `tools/validate_examples.py` (strict examples corpus is now
  51 events). Driven by external-adopter demand; details in the worklog
  Current Resume Note.
- The P1-04 bearing reference-frame integrity pass and P1-04R review fixes are
  adopted on `main` for v1.1.8. Schema 1.1.0 gained the optional
  `bearing.frame` marker; the locked v1.0 schema is untouched.
- Moth tunnel/replay and MAVLink `hdg` values no longer emit canonical
  bearing/heading fields unless callers explicitly assert `TRUE_NORTH`;
  unasserted native values remain auditable under explicitly named
  non-canonical fields.
- Use tag `v1.1.15` for current formal release assets/checksums. Use tag
  `v1.1.14` for the previous audit-driven honesty-hardening baseline.
- Use current `main` for the latest integration baseline with bearing-frame
  integrity, policy-risk linting, projection preservation for risk/promotion
  extensions, stricter extension registry metadata, formal human/AI agent
  change governance, downstream clone interoperability limits, and
  stale-release-reference audit cleanup.
- Post-release cleanup commit `9fc526e` is pushed to `origin/main`; it aligned
  current-facing docs, tools examples, CI compatibility target, and the
  compatibility CLI test with `v1.1.8`. No published v1.1.8 release assets,
  manifests, checksums, tags, or signatures were changed.
- Final baseline audit cleanup aligned two remaining current-facing guidance
  examples with `v1.1.8`: the adapter `check_compat` command and the
  change-governance manifest rebuild command. Published
  `SHA256SUMS_v1.1.8.txt` and release assets remain unchanged.
- Final baseline audit closeout is pushed at `c814d95` on `origin/main`
  (`beffed3` was the preceding guidance-cleanup commit).
  The full local validation suite, focused validators, workflow/live gateway
  smoke tests, package/bundle build checks, Docker Compose config rendering,
  GitHub PR/issue queue check, and GitHub CI passed. The tracked worktree is
  clean; only ignored local cache/build residue remains.
- S1-23 refreshed the README-linked documentation surface on 2026-06-18. The
  tracked Markdown/TXT link audit found no broken relative links, `git
  ls-files --others --exclude-standard` returned no rogue untracked files, and
  `spec/installation-guide.md` now points new installs at the maintained
  `configs/` templates while keeping release-publication boundaries explicit.
- R1-05 publishes the post-v1.1.8 current-main documentation freshness,
  governance hygiene, timing/compact follow-up, and release-process cleanup as
  `v1.1.9`. Historical `v1.1.8` release notes, validation report, assets, and
  checksums remain preserved.
- D-013 (timing-freshness negative-age clamp) and D-014 (compact codec
  unknown integer payload keys) are closed on current `main`. The stack now
  labels out-of-tolerance negative TIME_STATUS age with
  `TIMING_STATUS_AGE_NEGATIVE` and rejects unknown compact integer keys at
  decode instead of degrading them to strings.
- Current `main` also adds advisory industry-sharing posture docs:
  `IP_POLICY.md`, `CONTRIBUTING.md`, `CONFORMANCE.md`, `TRADEMARK.md`, and
  `docs/zmeta_defensive_publication.md`. These docs clarify Apache-2.0
  baseline limits, contributor authority, conformance/private dialect claims,
  ZMeta name use, and public defensive-publication posture without changing
  schemas, policy behavior, event vocabulary, or the locked v1.0 kernel.
- Future work is optional and should be driven by real sensor captures, a versioned semantic branch decision, release-authority signing process, formal legal review, or standards-body adoption.

Current release target:

- Release URL: <https://github.com/JTC-byte/zmeta-spec/releases/tag/v1.1.14>
- Tag: `v1.1.14` (annotated, on the R1-10 release commit; the commit
  SHA, CI status, and asset list are recorded in the worklog R1-10
  publication note).
- Previous release: `v1.1.13` (tag on `1117bc6`); its published assets,
  checksums, and release records are unchanged.
- Signature status: v1.1.14 is published checksums-only per the
  maintainer's signing decision, consistent with v1.1.5 through
  v1.1.13; signing remains the maintainer's external process. Use
  `SHA256SUMS_<version>.txt`, the structured release manifest, and the
  release package checksum file for integrity verification.

## Key Docs

| Document | Purpose |
| --- | --- |
| `AGENTS.md` | Root quick-start guide for human maintainers and AI agents working in this governed repository. |
| `docs/zmeta_change_governance.md` | Formal change process, authority order, left/right limits, documentation matrix, validation gates, and release publication workflow. |
| `IP_POLICY.md` | Advisory open-specification, contributor authority, and industry-sharing posture. |
| `CONTRIBUTING.md` | Contribution license, authority, sign-off, semantic-boundary, and validation expectations. |
| `CONFORMANCE.md` | Definitions for ZMeta-conformant, compatible, derived, private dialect, and experimental extension claims. |
| `TRADEMARK.md` | Advisory name-use guidance for ZMeta compatibility and conformance statements. |
| `docs/zmeta_defensive_publication.md` | Public technical disclosure intended to make the open ZMeta architecture easier to cite and socialize. |
| `docs/zmeta_professional_overview.md` | Advisory overview for engineers, operators, and leadership explaining ZMeta purpose, architecture, profiles, governance, provenance, and enabled workflows. |
| `spec/semantics-contract.md` | Authoritative hardened semantic contract. Schemas, policy packs, adapters, encodings, examples, gateways, and conformance tests must preserve it. |
| `docs/zmeta_semantic_contract_lockdown_audit.md` | S0-01 audit of the prior contract against intended ZMeta roles, implementation surfaces, and future ISR/edge AI/coalition/mesh trust needs. |
| `docs/zmeta_contract_to_stack_crosswalk.md` | S0-03 contract-to-implementation crosswalk and prioritized implementation backlog. |
| `docs/s1_01_v1_baseline_verification_plan.md` | S1-01A v1.0 baseline verification. Confirms current v1.0 schema/policy coverage and states S1-01B is not needed. |
| `docs/s1_02_profile_projection_preservation_plan.md` | S1-02A plan for profile projection invariants, field catalog, fixture format, positive/negative conformance cases, and S1-02B file-by-file implementation. |
| `spec/profile-projection-field-catalog.md` | Human-readable guide to the profile projection field catalog and fixture semantics. |
| `conformance/profile_projection_field_catalog.yaml` | Machine-readable projection field catalog. |
| `conformance/profile-projection/` | Source/projected projection fixture suite. |
| `docs/s1_03_extension_registry_plan.md` | S1-03A plan for extension registry artifacts, statuses, categories, collision rules, adoption requirements, and validation. |
| `spec/extension-registry.md` | Human-readable extension registry governance, status definitions, collision rules, and adoption requirements. |
| `spec/extension-registry.yaml` | Machine-readable extension registry. Existing v1.1.0 entries are experimental; future entries are reserved/proposed. |
| `docs/s1_03c_extension_registry_audit.md` | S1-03C audit confirming extension registry implementation, validation behavior, and version-boundary protection. |
| `spec/future-branch-roadmap.md` | Governance companion for the S1-11B machine-readable future-branch roadmap: authority limits, field definitions, and usage. |
| `spec/future-branch-roadmap.yaml` | Machine-readable D-003 roadmap: candidates with status, dependencies, required surfaces, recorded evidence, promotion tripwires, and rejection/defer decisions. Not a vocabulary source. |
| `tools/validate_future_roadmap.py` | Standalone validator for the future-branch roadmap (structure, registry cross-references, tripwire coverage, status-leakage check). |
| `docs/s1_04_conformance_class_manifest_plan.md` | S1-04A plan for conformance class artifacts, claim model, dependencies, validation, and implementation path. |
| `spec/conformance-classes.md` | Human-readable conformance class and claim model. |
| `conformance/conformance_classes.yaml` | Machine-readable conformance class manifest. |
| `conformance/claims/` | Example implementation claim files for reference gateway and core producer. |
| `docs/s1_04c_conformance_class_manifest_audit.md` | S1-04C audit confirming conformance class implementation, claim validation, and no schema/contract/registry drift. |
| `docs/s1_05_encoding_negative_validation_plan.md` | S1-05A plan for compact/protobuf invalid-after-decode fixtures, validator tooling, gateway/CLI negative coverage, and D-007 closure path. |
| `conformance/encoding-negative/` | S1-05B compact/protobuf/gateway invalid-after-decode fixture suites. |
| `docs/s1_05c_encoding_negative_validation_audit.md` | S1-05C audit confirming encoding-negative validation coverage and closing D-007. |
| `docs/s1_06_profile_precision_quantization_policy_plan.md` | S1-06A plan for profile precision ceilings, utility floors, conservative rounding, packet-budget interaction, and S1-06B implementation. |
| `spec/profile-precision-policy.md` | Human-readable profile precision and quantization policy guide. |
| `policy/profile-precision.yaml` | Reference conformance default precision policy; requires mission review. |
| `conformance/profile-precision/` | Source/projected precision policy fixture suite. |
| `docs/s1_06c_profile_precision_quantization_policy_audit.md` | S1-06C audit confirming profile precision policy implementation and closing D-010. |
| `docs/s1_07a_takeoff_crosswalk_cleanup.md` | S1-07A cleanup note confirming the crosswalk typo was removed and `TAKEOFF` remains invalid current vocabulary. |
| `docs/s1_08a_mavlink_state_payload_drift_cleanup.md` | S1-08A cleanup note confirming MAVLink STATE_EVENT documentation no longer maps raw telemetry into `payload.features.*`. |
| `docs/s1_09_contract_release_hash_plan.md` | S1-09A plan for contract hash taxonomy, release manifest structure, deployment gates, claim integration, and S1-09B implementation. |
| `spec/release-hash-policy.md` | S1-09B release hash policy for narrow semantic contract hashes, broader release manifests, canonicalization, and deployment/claim guidance. |
| `release/zmeta-release-manifest.yaml` | Reference hardening-baseline manifest with governed artifact hashes. |
| `docs/s1_09c_contract_release_hash_audit.md` | S1-09C audit confirming release hash reproducibility, claim integration, and D-002 closure. |
| `docs/s1_10p_forge_scope_purge.md` | S1-10P cleanup note removing out-of-scope organizational artifact scope from the ZMeta baseline. |
| `docs/s1_11_future_versioned_semantic_branch_roadmap_plan.md` | S1-11A roadmap for future versioned semantic branches under D-003. |
| `docs/s1_12_formal_release_tag_signature_attestation_plan.md` | S1-12A plan for formal release tag, checksum, signature, attestation, and verification packaging under D-012. |
| `docs/s1_12c_formal_release_packaging_audit.md` | S1-12C audit closing D-012 after verifying release packaging support. |
| `docs/s1_13a_stack_conformance_and_stale_file_audit.md` | S1-13A audit confirming stack conformance, stale-file posture, v1.1.5 compatibility target alignment, and D-009 closure. |
| `docs/s1_14_external_projection_promotion_contract.md` | S1-14 implementation note for external projection promotion policy, profile behavior, and bandwidth guardrails. |
| `docs/s1_15b_risk_adjudication_stack_conformance_audit.md` | S1-15B folder-by-folder audit confirming policy, gateway, conformance, tests, and docs emit filterable accepted-risk semantics. |
| `docs/s1_15c_semantic_contract_feedback_cleanup.md` | S1-15C cleanup note for semantic-contract feedback on CoT promotion, self-labels, overrides, diagnostics, conformance classes, and future-only boundaries. |
| `docs/s1_16a_bad_event_adapter_harness.md` | S1-16A implementation note for semantic bad-event fixtures and the shared adapter conformance harness. |
| `docs/s1_16b_kernel_protection_contract_alignment.md` | S1-16B alignment note for completeness without exhaustiveness, the core semantic change threshold, and future-extension non-claimability. |
| `docs/s1_17a_kernel_protection_stack_audit.md` | S1-17A stack audit confirming live tracked surfaces conform to kernel-protection doctrine and wiring full kernel conformance into CI/local release flow. |
| `docs/s1_18a_operator_risk_filter_tooling.md` | S1-18A implementation note for consumer-side accepted-risk filtering and operator posture presets. |
| `docs/s1_18b_end_to_end_stack_runtime_audit.md` | S1-18B audit note for folder-by-folder semantic conformance, runtime workflow sweep, package smoke tests, and CoT egress hardening. |
| `docs/r1_03_v1_1_7_stack_audit_release.md` | R1-03 audit and release note for v1.1.7 stale-reference, generated-residue, secret-scan, and release-package cleanup. |
| `docs/r1_04_v1_1_8_bearing_frame_release.md` | R1-04 audit and release note for v1.1.8 bearing-frame integrity, adapter hardening, and release publication. |
| `conformance/bad-events/` | Semantic bad-event fixture suite for dishonest or unsafe events that must not be treated as clean data. |
| `conformance/adapter-harness/` | Shared fixture-driven adapter output harness for schema/policy validity, layer separation, lineage, timing, and external promotion. |
| `spec/release-signing-attestation.md` | S1-12B release signing, attestation, no-secret, and verification framework. |
| `release/RELEASE_PACKAGE_README.md` | S1-12B release package template guidance. |
| `release/RELEASE_NOTES_v<version>.md` | Published release notes, one file per formal release (v1.1.7 onward; the "Current release target" section above names the current version). |
| `release/VALIDATION_REPORT_v<version>.md` | Published validation report, one file per formal release. |
| `release/SHA256SUMS_v<version>.txt` | Published checksum manifest for each formal release's standard assets. |
| `tools/lint_policy_risk_modes.py` | Policy lint for unsafe `ignore` settings on material risk. |
| `docs/zmeta_refinement_worklog.md` | Running worklog: Current Resume Note (recent sessions), pending work items, and the deferred issue register. |
| `docs/zmeta_refinement_worklog_archive.md` | Completed task sections S0-01..R1-05, archived verbatim per the release-checklist retention pass. |

## Completed Recently

Completed work items S0-01 through R1-05 (contract lockdown, projection
preservation, registry, conformance classes, encoding-negative, precision
policy, release hashing/packaging, risk adjudication, bad-event corpus and
adapter harness, bearing-frame integrity, and the v1.1.5-v1.1.9 releases)
are recorded verbatim, one section each, in
`docs/zmeta_refinement_worklog_archive.md`. Later sessions (S1-24 onward)
are summarized in "Current stack status" above and in the worklog Current
Resume Note.

## Current Decisions

- The semantic contract is authoritative; implementation surfaces must preserve it.
- Humans and AI agents should follow `AGENTS.md` and
  `docs/zmeta_change_governance.md` before changing governed artifacts.
- Downstream clone users can integrate locally around pinned releases, but
  schema, vocabulary, version-dispatch, projection, risk, or command-authority
  changes are private dialect/fork work unless governed, versioned, documented,
  and backed by conformance evidence.
- Current formal release is `v1.1.14`; latest integration baseline is
  current `main`.
- v1.0 remains locked.
- Do not add v1.1.0 or future concepts to v1.0.
- S1-01A found no schema-enforceable v1.0 gap requiring S1-01B.
- Profile projection preservation is now covered by a sidecar field catalog and source/projected conformance pairs.
- Compact Profile L and protobuf remain encoding projections; both must decode to canonical JSON before schema, policy, and projection checks.
- Existing strict conformance remains stable by default. Projection checks are explicit via `tools/validate_projection.py` or `tools/validate_conformance.py --strict --profile-projection`.
- The extension registry should be implemented as spec-owned artifacts:
  `spec/extension-registry.md` and `spec/extension-registry.yaml`.
- Existing v1.1.0 extension concepts should remain `experimental` by default
  until a version/release decision promotes them.
- Reserved/proposed concepts are not valid event vocabulary.
- Registry validation is standalone and opt-in through
  `tools/validate_extension_registry.py` or
  `tools/validate_conformance.py --strict --extension-registry`.
- D-006 is closed after S1-03C verified the registry implementation.
- D-011 is closed. S1-07A removed the erroneous crosswalk `TAKEOFF`
  current-vocabulary reference while preserving the validator/test guard proving
  `TAKEOFF` remains invalid.
- Conformance classes organize implementation claims and required evidence.
  They do not create semantics or make future classes claimable.
- Conformance class validation is standalone and opt-in through
  `tools/validate_conformance_classes.py` or
  `tools/validate_conformance.py --strict --conformance-classes`.
- `ZMETA-ADAPTER` and `ZMETA-COT-PROJECTION` are now implemented with shared
  adapter-harness evidence. Broader `ZMETA-SENSOR-ADAPTER` certification remains
  planned until more native-message variants are covered.
- ZMeta is complete enough to prevent semantic corruption without becoming an
  exhaustive mission ontology. Mission-specific behavior belongs in policy
  packs, deployment configuration, adapters, profiles, extension branches,
  operator views, or mission plugins unless a concrete ambiguity, failure, or
  safety/audit gap requires core contract work.
- Contract and policy rules are classified as `LOCKED`, `TUNABLE`, `ADVISORY`,
  or `FUTURE_EXTENSION`. Future-extension concepts are visible for governance
  but remain non-claimable until versioned schema/policy/adapter/encoding and
  conformance evidence exists.
- CI and `make validate-kernel` run the full kernel-protection conformance path:
  profile projection, extension registry, conformance classes,
  encoding-negative, precision policy, release manifest/package, bad-event
  corpus, and adapter harness.
- `tools/filter_risk.py` lets consumers filter JSONL streams by existing
  `risk_adjudication` and diagnostic labels. Presets include `display`,
  `fusion`, `state`, `command`, `autonomy`, `aar`, and `audit`; the tool passes
  accepted events unchanged and can emit dropped-event reasons to a sidecar.
- Profile projection treats `payload.extensions.risk_adjudication` as
  preserved policy/use-limit evidence when present. Profile L/M/H projections
  must not strip accepted-risk labels in ways that make degraded data appear
  clean.
- Profile projection requires compact
  `payload.extensions.external_promotion` evidence to preserve policy ID,
  trust reference, lineage status, and loop/reflection status while allowing
  Profile L to omit selected H-only audit detail when producer-authority policy
  still validates the projected event.
- Extension registry entries declare and validate
  `profile_projection_behavior`, `risk_relevant`,
  `must_preserve_when_used_for_policy`, `security_privacy_notes`, and
  `fixture_references` so future vendor or edge extensions cannot hide
  policy-relevant behavior behind ignorable metadata.
- Example claim files now use the narrow semantic `contract_hash` from
  `release/zmeta-release-manifest.yaml` and record broader category hashes under
  `release_hashes`. `release_manifest_hash` is omitted from claims to avoid
  circularity because the reference manifest includes the claim files.
- S1-04C verified the conformance class implementation. D-008 is closed.
- S1-05A planned encoding-negative validation only. Compact/protobuf remain
  wire projections, and S1-05B should prove invalid decoded compact/protobuf
  events cannot bypass schema, policy, projection, gateway, CLI, registry, or
  conformance expectations.
- S1-05B implemented encoding-negative validation as an opt-in suite. Default
  `--strict` remains unchanged. The compact/protobuf classes now include
  encoding-negative evidence, but no new conformance class was added.
- S1-05C verified encoding-negative validation. D-007 is closed. Remaining
  policy-specific examples from S1-05A are optional future breadth, not an
  encoding-layer bypass gap.
- S1-06B implemented the reference conformance default precision policy,
  precision fixture suite, validator, focused tests, optional
  `--precision-policy` conformance flag, and profile/projection class evidence
  updates.
- S1-06C audited precision policy quality, conservative rounding, utility
  floors, validator behavior, fixture coverage, packet-budget guardrails,
  projection interaction, conformance integration, and docs. D-010 is closed.
- Precision policy is profile/export policy, not schema, release policy, trust
  policy, emergency mode, UI policy, or transport semantics. Reference defaults
  require mission review.
- D-001 is closed. MAVLink ingress README guidance now prohibits STATE_EVENT
  raw `payload.features.*` and points telemetry into state-safe fields,
  `payload.quality`, SYSTEM_EVENT status, OBSERVATION_EVENT where appropriate,
  and lineage. Implementation inspection found no MAVLink STATE_EVENT
  raw-feature emission, so no D-012 follow-up was added.
- S1-09C verified the reference release hash system and closed D-002. It keeps
  `tools/compute_contract_hash.py` focused on the existing gateway-compatible
  schema/policy/semantic hash workflow, while `release/zmeta-release-manifest.yaml`
  records broader governed baseline hashes. Committed reference manifests use
  stable placeholder git metadata by default; formal release generation must
  pass explicit metadata. Formal tagged-release signatures and post-release
  attestations are tracked separately as D-012.
- S1-10P removed out-of-scope organizational artifact content from the ZMeta
  baseline. ZMeta remains focused on event semantics, profiles, adapters,
  encodings, validation, conformance, and release baselines.
- D-004 is closed as `CLOSED - REMOVED FROM ZMETA SCOPE`.
- S1-11A established a plan-only roadmap for future versioned semantic
  branches. D-003 remains `OPEN - ROADMAP PLANNED`; no future branch was
  implemented or approved.
- S1-12A established a plan-only path for formal release tags, checksums,
  detached signatures, release attestations, key-handling guardrails, and
  consumer verification. It made no tags, signatures, keys, schemas, release
  manifests, validators, runtime code, or vocabulary changes.
- S1-12B implemented the release package framework. The builder supports
  dry-run/no-signature mode and explicit package writes; the validator supports
  template-only and package-output validation, checksum checks, attestation hash
  checks, and no-secret checks.
- S1-12C audited the release package framework, verified template/package
  validation, no-secret behavior, release manifest integration, optional
  conformance integration, and absence of real tags/signatures/keys/secrets or
  semantic drift. D-012 is closed.
- R1-01 published the validated `v1.1.5` GitHub release and pushed `main` and
  the annotated `v1.1.5` tag. The release includes source, edge, gateway, release
  package, release manifest, release notes, validation report, and checksum
  assets. No `.asc` signatures were attached because no approved local signing
  key was available.
- S1-13A corrected stale live `v1.1.4` compatibility-checker and CI targets to
  `v1.1.5`, verified ignored local artifacts are expected generated/local state,
  and closed D-009 with explicit boundary tests for v1.0 generic observation
  extensions versus v1.1.0 formal contracts.
- S1-14 treats external tactical state ingress as a promotion boundary.
  CoT/JREAP/MAVLink state producers remain allowed only when
  `payload.extensions.external_promotion` satisfies producer-authority policy;
  Profile L may carry compact handles only, preserving bandwidth efficiency.
  The reference policy rejects invalid promotion by default, but operators can
  tune the response to warn, degrade, or quarantine while retaining explicit
  diagnostics and confidence/TTL effects.
- S1-15A establishes risk adjudication as the semantic model for configurable
  operational behavior: locked interoperability rules stay strict, tunable
  runtime rules may use reject/warn/degrade/quarantine/ignore within bounds, and
  soft acceptance must remain filterable through labels or correlated
  diagnostics. Policy can also declare allowed/prohibited operational uses, such
  as display-only, AAR-only, blocked-from-fusion, or blocked-from-command-basis.
- S1-15B implements that baseline in the live stack. Timing, lineage, external
  promotion, and runtime timing-loss degradation now produce explicit risk
  labels and use limits when accepted under soft policy.
- S1-15C aligns the contract text and conformance classes with that behavior:
  lossy CoT/TAK ingress now defers to external promotion, material risk labels
  are mandatory when diagnostics may not travel, and projection-origin,
  network-report parent evidence, and policy-adjudication subtypes remain
  future-only.
- S1-18B verified the tracked stack end to end against the semantic contract
  and local runtime workflows. Direct CoT egress now rejects malformed
  `STATE_EVENT` payloads that still carry raw observation/evidence fields,
  matching the layer-separation rule already enforced by gateway validation.
- P1-04 makes canonical bearings true north by contract (section 6.4):
  sensor-native frames must convert (with a heading source) or omit the
  canonical bearing while preserving the raw measurement in `features`.
  `bearing.frame` is an optional v1.1.0 marker with single-value enum
  `["TRUE_NORTH"]`; `BEARING_FRAME` is experimental in the registry; v1.0
  producers carry `quality.bearing_frame`/`quality.heading_source`
  provenance instead. Adapters must not fabricate bearings, SNR, headings,
  or positions; refuse-to-emit/omit is the schema-legal response to
  unavailable data. Moth tunnel/replay and MAVLink `hdg` inputs now require
  explicit `TRUE_NORTH` assertions before emitting canonical bearing/heading
  fields; otherwise the native values are retained only under explicitly named
  non-canonical fields.
- The adapter harness can pin exact output values per fixture through
  `expected_values` (1e-6 numeric tolerance, distinct
  `ADAPTER_EXPECTED_VALUE_MISSING`/`MISMATCH` codes, and a boolean type
  guard so a boolean pin never matches numeric output).

## Resolved Recent Findings

- **D-013 (timing freshness)**: closed on current `main`. Negative event age
  against the latest applicable TIME_STATUS is no longer clamped to zero.
  `policy/timing-freshness.yaml` now defines profile-specific
  `max_negative_age_ms` and default `negative_age_mode: warn`; validators emit
  `TIMING_STATUS_AGE_NEGATIVE` with timing risk labels when the tolerance is
  exceeded. Deployments may tune the mode to reject or degrade.
- **D-014 (compact codec)**: closed on current `main`. Compact v1 decoders now
  reject unknown integer keys in governed compact maps instead of converting
  them to decimal string keys. String extension keys remain preserved.

Follow-up notes (candidates for future hardening decisions, not register
entries):

- RESOLVED in v1.1.12 (S1-26 gateway containment): oversize outgoing UDP
  payloads (roughly 65507+ bytes) no longer raise an unhandled `OSError` in
  the gateway main loop — `_send_datagram` catches OSError, drops the
  datagram with explicit `send_failure` metrics/diagnostics, and counts
  forwarded/CoT only on actual sends.
- RESOLVED in v1.1.12 (S1-26 lineage honesty): ingress adapters no longer
  fabricate `lineage.based_on` with fresh random UUIDv7s — observation and
  system outputs omit lineage unless callers pass real parents, and
  mandatory-lineage events refuse to emit without them.
- Bearing frame provenance is still producer/configuration asserted. The
  `TRUE_NORTH` marker and `quality.heading_source` make the assertion auditable
  and reject unsupported labels, but they do not prove calibration,
  authenticity, or frame correctness. Treat deeper verification as future
  trust/PNT/integrity work rather than a current release blocker.

## Next Work Queue

1. **Maintainer decision pending: next-audit scope (R1-10 audit + fix
   pass + verification + v1.1.14 release COMPLETE, 2026-07-17)**
   - The R1-10 full stack audit, the fix-every-finding pass, the
     post-fix verification audit, and the v1.1.14 release cut are all
     COMPLETE — findings record in `docs/r1_10_full_stack_audit.md`,
     closeout and release records in the worklog R1-10 entries. The
     maintainer-directed cut resolved the previously recorded
     SHA256SUMS_v1.1.13 manifest-entry divergence
     (`SHA256SUMS_v1.1.14.txt` pins the regenerated manifest).
   - Open decision: whether a fresh full-stack audit (beyond the
     completed fix-verification audit) runs before the backlog
     resumes. Flagged residuals for that audit are listed in the
     worklog fix-pass entry (signalhunter replay-timestamp and
     sensor-position observations).
   - 2026-07-20 update: the maintainer directed the SAPIENT lane
     (comparison + P1-07 mapping pack, complete — worklog P1-07 entry)
     without closing this decision; it remains open. P1-07 added
     follow-up candidates to the queue: the CoT-template loop_status
     default sync (second-glance item a), the harness
     registration-object entry point (item b), and the SAPIENT
     branch-evidence items (item c) which feed the v1.1.0 adoption
     session and the future-branch roadmap rather than immediate work.
   - Everything below this item is queued behind that decision.

2. **Queued: v1.1.0 adoption decision (all fourteen concepts)**
   - Maintainer direction (2026-07-08): build the per-concept evidence
     worksheet (repo-side evidence for all fourteen experimental v1.1.0
     registry concepts, field-side evidence supplied by the maintainer)
     and make the adopt-vs-stay-experimental decision for every concept in
     that same session — no prolonging.
   - Evidence standard: the promotion evidence bar in
     `spec/extension-registry.md` (two or more independent implementations
     demonstrating the need plus a documented semantic-contract Section 2.6
     failure condition). Candidate telemetry: the maintainer's fielded
     deployment plus the upstream PR #4 deployment; check PR #4 for
     contributor revisions before deciding.
   - Expected shape for concepts that clear the bar: registry status
     changes (`experimental` -> `adopted`), conformance-class and doc
     updates, one release; no schema file changes. Expanded command-task
     concepts stay experimental absent fielded command-loop evidence.
   - Aside from that queued session, the stack is closed for the downstream
     integration baseline: S1-11B is implemented, the deferred issue
     register is fully closed, and remaining follow-ups activate only on
     real sensor data, an evidence-bar tripwire, or release-authority
     signing inputs.

3. **Standing defaults (recorded 2026-07-08 by maintainer direction)**
   The former open-ended "human decisions for future hardening" list is
   resolved to standing defaults: the shipped reference behavior stands
   unless field evidence or a promotion-evidence-bar tripwire
   (`spec/extension-registry.md`, `spec/future-branch-roadmap.yaml`) forces a
   revisit. Specifically:
   - Precision policy reference defaults (values, profile scoping,
     quantization basis, confidence rounding, command-vs-display strictness,
     RF variation) stand as reference conformance defaults requiring mission
     review; enforcement stays in conformance, not gateway exports.
   - Opt-in conformance flags (`--encoding-negative`, `--precision-policy`,
     `--extension-registry`) remain opt-in for downstream users; CI and
     `make validate-kernel` already run the full kernel path, which is the
     gate that protects releases.
   - Conformance class statuses stay `implemented`; claim files keep
     command/result summaries without captured-output artifacts.
   - Encoding-negative fixtures keep their current byte-storage format; no
     separate `ZMETA-ENCODING-NEGATIVE-VALIDATION` class — evidence stays
     folded into the compact/protobuf classes.
   - Vendor/private namespaces keep the `vendor.<owner>.<name>` convention;
     classified/restricted name representation is deferred to the
     future-branch roadmap.
   - Adapter-harness breadth grows only with real sensor captures; broader
     `ZMETA-SENSOR-ADAPTER` certification stays planned until then.
   - S1-11B is implemented (`spec/future-branch-roadmap.yaml` +
     `tools/validate_future_roadmap.py`); that decision is closed.

4. **Genuinely open maintainer decisions**
   - Release signing: releases since v1.1.5 are checksums-only. The release
     authority is standing up a signature (in progress 2026-07-08); whether
     future formal releases publish detached signatures and post-release
     claim attestations (including `release_manifest_hash`) follows from
     that process.
   - Whether v1.1.0 remains permanently `experimental` or is adopted as a
     baseline (open question from the future-branch roadmap, Section N).

5. **Deferred issue cleanup**
   - D-001 MAVLink Adapter README State Payload Drift is closed.
   - D-002 Contract Hash / Release Hash Follow-Up is closed.
   - D-003 Future Semantics Require Versioned Implementation Branches is
     closed (2026-07-08, maintainer decision after S1-11B): the
     future-branch roadmap artifact, extension registry, and promotion
     evidence bar now track future branch work individually. The deferred
     issue register is fully closed.
   - D-007 Encoding Negative Validation Gap is closed.
   - D-008 Conformance Class Manifest Missing is closed.
   - D-004 is closed as removed from ZMeta scope by S1-10P.
   - D-009 v1.0/v1.1 Observation Extension Boundary Needs Explicit Tests is closed.
   - D-010 Profile Precision / Quantization Policy Floors is closed.
   - D-011 Crosswalk TAKEOFF Mention Cleanup is closed.
   - D-012 Formal Release Tag, Signature, and Attestation Packaging is
     closed.
   - D-013 Timing-Freshness Negative-Age Clamp is closed.
   - D-014 Compact Codec Unknown Integer Payload Keys is closed.

6. **Later versioned semantic branches**
   - Markings/releasability.
   - Integrity, signing, anti-replay, mesh trust, and quarantine.
   - MODEL_STATUS / assurance and drift monitoring.
   - UAS identity and behavioral trust.
   - Track lifecycle extensions.
   - Coalition export and cross-domain guard metadata.
   - Compute status and degraded runtime behavior.

7. **P1-06 deferred maintainer decisions (recorded 2026-07-15; queued so
   they do not age out of prose)**
   - Name and link the fielded deployments in the README "ZMeta In The
     Field" section, or keep it generic (disclosure/positioning call).
   - RF golden sample pairs: sanitized real captures (Kraken DOA CSV window,
     Moth serial lines, small SignalHunter PSD `.bin`) plus expected ZMeta
     output as `samples/` input->expected pairs for the RF adapters —
     requires maintainer-supplied sanitized field data.
   - `mavlink_to_zmeta_template.py` rename to match its Production status —
     Class B follow-up (governed `must-pass.jsonl` + `conformance_classes`
     references + release-manifest regeneration).
   - Physical `docs/process/` move for the dated s1_*/r1_* records —
     optional; blocked-ish on 5 governed references in
     `conformance/conformance_classes.yaml`; the `docs/README.md` index
     covers the need for now.
   - Mechanical conformance-claim generator (`tools/make_claim.py`) —
     touches claim governance; follow-up if wanted.

## Guardrails for Next Prompt

- Do not change schemas unless the prompt explicitly moves into a schema implementation item.
- Do not recompute formal release/tag hashes until a release packaging task explicitly asks for it.
- Do not make v1.1.0 or future concepts valid under `zmeta_version: "1.0"`.
- Keep profile projection checks pairwise and external to v1.0 event payloads.
- Keep registry work plan-first and branch-scoped. A registry entry alone does
  not make vocabulary valid.
- Keep conformance class work evidence-driven. A class record alone does not
  prove an implementation claim.
- Document any newly discovered issues in the deferred issue register in `docs/zmeta_refinement_worklog.md`.

## Verification State

Most recent validation: the v1.1.13 (R1-09) release validation record lives
in `release/VALIDATION_REPORT_v1.1.13.md` and the worklog R1-09 entry
(`docs/zmeta_refinement_worklog.md`). The single block below is retained as
the most recent full command inventory recorded in this handoff; older
validation generations were pruned from this rolling brief and live in git
history.

Validation for the S1-26 v1.1.12 release preparation on `main` (2026-07-08,
Windows, Python — historical; superseded by the v1.1.13 record above):

```powershell
python tools\build_release_manifest.py --release-id zmeta-v1.1.12 --release-name "ZMeta v1.1.12" --release-status formal_release --release-date 2026-07-08 --branch main --update-claims
python tools\validate_release_manifest.py --manifest release\zmeta-release-manifest.yaml
python tools\validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative --precision-policy --release-manifest --release-package --bad-events --adapter-harness
python tools\validate_examples.py --strict --require-all
python tools\lint_policy_risk_modes.py
python tools\validate_future_roadmap.py
python -m pytest -q
python tools\test_workflow_end_to_end.py
python tools\test_workflow_end_to_end.py --profile M --listen-port 5665 --forward-port 5666 --cot-port 5667
python tools\test_gateway_live.py --listen-port 5675 --forward-port 5676 --cot-port 5677
python tools\test_gateway_live.py --profile L --encoding compact --input-encoding compact --listen-port 5695 --forward-port 5696 --cot-port 5697
python gateway\src\gateway.py --profile H --self-test
python gateway\src\gateway.py --config configs\gateway-config.json --self-test
python gateway\src\gateway.py --config configs\edge-config.json --self-test
python tools\check_compat.py --target v1.1.12 --strict <each examples\*.jsonl>
python tools\measure_packet_size.py --file examples\zmeta-profile-L-examples.jsonl --encodings compact --max-bytes 240 --summary-only
python release\build_mvp_packages.py --version v1.1.12
python release\build_release_bundle.py --version 1.1.12
python tools\build_release_package.py --manifest release\zmeta-release-manifest.yaml --output-dir release\package-v1.1.12 --release-id zmeta-v1.1.12 --release-state formal_release --no-signatures --allow-dirty --clean-output
python tools\validate_release_package.py --manifest release\zmeta-release-manifest.yaml --package-dir release\package-v1.1.12
python release\sign_release_artifacts.py --version v1.1.12 --write-checksums --verify-checksums
git diff --check
```

Full kernel conformance result: `projection conformance ok total=37`,
`extension registry ok entries=61`, `conformance classes ok classes=34
claims=2`, `encoding negative ok total=50`, `profile precision policy ok
total=32`, `bad-event corpus ok total=23`, `adapter conformance ok
total=11`, `conformance ok`.
Roadmap result: `future-branch roadmap ok candidates=18
rejected_or_deferred=3`.
Examples result: `overall total=47 passed=47 failed=0 warnings=0`.
Policy lint result: `policy risk mode lint ok`.
Release manifest result: `release manifest ok groups=19 artifacts=70`.
Release package result: `release package ok mode=package`.
Full pytest result: `465 passed, 110 subtests passed`.
Workflow/live gateway results: Profile H/M end-to-end and JSON/compact live
paths passed with CoT wire output; gateway self-tests passed for Profile H,
gateway config, and edge config.
Compatibility result: `issues=0 failed=0 warnings=0` for all eight example
corpora against target `v1.1.12`.
Packet-size result: compact Profile L `min=98 avg=116.0 max=150` under the
240-byte check.
Checksum result: `checksums ok: SHA256SUMS_v1.1.12.txt`.
Docker Compose config rendering was not re-exercised this session (deploy
YAML unchanged since the last validated baseline).
