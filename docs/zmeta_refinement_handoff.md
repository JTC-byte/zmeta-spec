# ZMeta Refinement Handoff Notes

Status date: 2026-07-07

This note is the quick resume point for the current ZMeta refinement effort. The full task history and deferred issue register are in `docs/zmeta_refinement_worklog.md`.

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
- The P1-04 bearing reference-frame integrity pass and P1-04R review fixes are
  adopted on `main` for v1.1.8. Schema 1.1.0 gained the optional
  `bearing.frame` marker; the locked v1.0 schema is untouched.
- Moth tunnel/replay and MAVLink `hdg` values no longer emit canonical
  bearing/heading fields unless callers explicitly assert `TRUE_NORTH`;
  unasserted native values remain auditable under explicitly named
  non-canonical fields.
- Use tag `v1.1.10` for current formal release assets/checksums. Use tag
  `v1.1.9` for the previous documentation-freshness release baseline.
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

- Release URL: <https://github.com/JTC-byte/zmeta-spec/releases/tag/v1.1.10>
- Tag: `v1.1.10` (annotated, on release commit `6ce4f29`)
- Release commit: `6ce4f29` - `Release v1.1.10: fielded-safety enforcement`.
- GitHub CI: passed for the pushed v1.1.10 release commit.
- Previous release: `v1.1.9` (tag `56c19f4`); its published assets, checksums,
  and release records are unchanged.
- Signature status: v1.1.10 release artifacts are published checksums-only,
  consistent with v1.1.5 through v1.1.9. Use `SHA256SUMS_v1.1.10.txt`, the
  structured release manifest, and the release package checksum file for
  integrity verification. Detached signatures remain an optional
  release-authority step.

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
| `release/RELEASE_NOTES_v1.1.7.md` | Published v1.1.7 release notes. |
| `release/VALIDATION_REPORT_v1.1.7.md` | Published v1.1.7 validation report. |
| `release/SHA256SUMS_v1.1.7.txt` | Published v1.1.7 checksum manifest for standard release assets. |
| `release/RELEASE_NOTES_v1.1.8.md` | Published v1.1.8 release notes. |
| `release/VALIDATION_REPORT_v1.1.8.md` | Published v1.1.8 validation report. |
| `release/SHA256SUMS_v1.1.8.txt` | Published v1.1.8 checksum manifest for standard release assets. |
| `release/RELEASE_NOTES_v1.1.9.md` | Published v1.1.9 release notes. |
| `release/VALIDATION_REPORT_v1.1.9.md` | Published v1.1.9 validation report. |
| `release/SHA256SUMS_v1.1.9.txt` | Published v1.1.9 checksum manifest for standard release assets. |
| `tools/lint_policy_risk_modes.py` | Policy lint for unsafe `ignore` settings on material risk. |
| `docs/zmeta_refinement_worklog.md` | Running worklog, completed work items, pending work items, and deferred issue register. |

## Completed Recently

| Work Item | Status | Output |
| --- | --- | --- |
| S0-01 Semantic Contract Lockdown Audit | COMPLETE | `docs/zmeta_semantic_contract_lockdown_audit.md` |
| S0-02 Semantic Contract Rewrite and Hardening | COMPLETE | `spec/semantics-contract.md` |
| S0-03 Contract-to-Stack Crosswalk | COMPLETE | `docs/zmeta_contract_to_stack_crosswalk.md` |
| S1-01A v1.0 Baseline Verification | COMPLETE | `docs/s1_01_v1_baseline_verification_plan.md` |
| S1-02A Profile Projection Preservation Plan | COMPLETE | `docs/s1_02_profile_projection_preservation_plan.md` |
| S1-02B Profile Projection Preservation Implementation | COMPLETE | `conformance/profile_projection_field_catalog.yaml`, `tools/validate_projection.py`, `conformance/profile-projection/` |
| S1-02C Profile Projection Preservation Audit | COMPLETE | `docs/s1_02c_projection_preservation_audit.md` |
| S1-03A Extension Registry Plan Only | COMPLETE | `docs/s1_03_extension_registry_plan.md` |
| S1-03B Extension Registry Implementation | COMPLETE | `spec/extension-registry.md`, `spec/extension-registry.yaml`, `tools/validate_extension_registry.py` |
| S1-03C Extension Registry Audit | COMPLETE | `docs/s1_03c_extension_registry_audit.md` |
| S1-04A Conformance Class Manifest Plan Only | COMPLETE | `docs/s1_04_conformance_class_manifest_plan.md` |
| S1-04B Conformance Class Manifest Implementation | COMPLETE | `spec/conformance-classes.md`, `conformance/conformance_classes.yaml`, `tools/validate_conformance_classes.py` |
| S1-04C Conformance Class Manifest Audit | COMPLETE | `docs/s1_04c_conformance_class_manifest_audit.md` |
| S1-05A Encoding Negative Validation Plan Only | COMPLETE | `docs/s1_05_encoding_negative_validation_plan.md` |
| S1-05B Encoding Negative Validation Implementation | COMPLETE | `conformance/encoding-negative/`, `tools/validate_encoding_negative.py`, focused encoding-negative tests |
| S1-05C Encoding Negative Validation Audit | COMPLETE | `docs/s1_05c_encoding_negative_validation_audit.md` |
| S1-06A Profile Precision / Quantization Policy Floors Plan Only | COMPLETE | `docs/s1_06_profile_precision_quantization_policy_plan.md` |
| S1-06B Profile Precision / Quantization Policy Floors Implementation | COMPLETE | `spec/profile-precision-policy.md`, `policy/profile-precision.yaml`, `conformance/profile-precision/`, `tools/validate_precision_policy.py` |
| S1-06C Profile Precision / Quantization Policy Floors Audit | COMPLETE | `docs/s1_06c_profile_precision_quantization_policy_audit.md` |
| S1-07A Crosswalk TAKEOFF Mention Cleanup | COMPLETE | `docs/s1_07a_takeoff_crosswalk_cleanup.md` |
| S1-08A MAVLink Adapter README State Payload Drift Cleanup | COMPLETE | `docs/s1_08a_mavlink_state_payload_drift_cleanup.md` |
| S1-09A Contract Hash / Release Hash Follow-Up Plan Only | COMPLETE | `docs/s1_09_contract_release_hash_plan.md` |
| S1-09B Contract Hash / Release Hash Implementation | COMPLETE | `spec/release-hash-policy.md`, `release/zmeta-release-manifest.yaml`, `tools/build_release_manifest.py`, `tools/validate_release_manifest.py` |
| S1-09C Contract Hash / Release Hash Audit | COMPLETE | `docs/s1_09c_contract_release_hash_audit.md` |
| S1-10A Out-of-Scope Artifact Roadmap Plan Only | SUPERSEDED / CANCELLED | deleted during S1-10P |
| S1-10P Purge FORGE-Derived Scope Contamination | COMPLETE | `docs/s1_10p_forge_scope_purge.md` |
| S1-11A Future Versioned Semantic Branch Roadmap Plan Only | COMPLETE | `docs/s1_11_future_versioned_semantic_branch_roadmap_plan.md` |
| S1-12A Formal Release Tag / Signature / Attestation Plan Only | COMPLETE | `docs/s1_12_formal_release_tag_signature_attestation_plan.md` |
| S1-12B Formal Release Tag / Signature / Attestation Packaging Implementation | COMPLETE | `spec/release-signing-attestation.md`, `tools/build_release_package.py`, `tools/validate_release_package.py` |
| S1-12C Formal Release Tag / Signature / Attestation Packaging Audit | COMPLETE | `docs/s1_12c_formal_release_packaging_audit.md` |
| R1-01 v1.1.5 Release Publication | COMPLETE | <https://github.com/JTC-byte/zmeta-spec/releases/tag/v1.1.5> |
| S1-13A Stack Conformance And Stale File Audit | COMPLETE | `docs/s1_13a_stack_conformance_and_stale_file_audit.md` |
| S1-14 External Projection Promotion Contract | COMPLETE | `docs/s1_14_external_projection_promotion_contract.md`, `policy/producer-authority.yaml`, `gateway/src/validators.py` |
| S1-15B Risk Adjudication Stack Conformance Pass | COMPLETE | `docs/s1_15b_risk_adjudication_stack_conformance_audit.md`, `gateway/src/validators.py`, `gateway/src/gateway.py`, `policy/*.yaml`, `conformance/must-pass.jsonl` |
| S1-15C Semantic Contract Feedback Cleanup | COMPLETE | `docs/s1_15c_semantic_contract_feedback_cleanup.md`, `spec/semantics-contract.md`, `conformance/conformance_classes.yaml` |
| S1-16A Bad-Event Corpus And Adapter Harness | COMPLETE | `docs/s1_16a_bad_event_adapter_harness.md`, `conformance/bad-events/`, `conformance/adapter-harness/`, `tools/validate_bad_events.py`, `tools/validate_adapter_conformance.py` |
| S1-16B Kernel Protection Contract Alignment | COMPLETE | `docs/s1_16b_kernel_protection_contract_alignment.md`, `spec/semantics-contract.md`, `spec/conformance-classes.md`, `conformance/conformance_classes.yaml` |
| S1-17A Kernel Protection Stack Audit | COMPLETE | `docs/s1_17a_kernel_protection_stack_audit.md`, `.github/workflows/ci.yml`, `Makefile`, `policy/README.md`, `configs/policy-variants/README.md` |
| S1-18A Operator Risk Filter Tooling | COMPLETE | `docs/s1_18a_operator_risk_filter_tooling.md`, `tools/filter_risk.py`, `gateway/tests/test_risk_filter_cli.py` |
| S1-18B End-to-End Stack and Runtime Audit | COMPLETE | `docs/s1_18b_end_to_end_stack_runtime_audit.md`, `adapters/egress/cot/zmeta_to_cot.py`, `.gitignore` |
| R1-02 v1.1.6 Release Publication | COMPLETE | <https://github.com/JTC-byte/zmeta-spec/releases/tag/v1.1.6> |
| P1-01 Post-v1.1.6 Partner Feedback Cleanup | COMPLETE | `README.md`, `tools/lint_policy_risk_modes.py`, `gateway/tests/test_policy_risk_mode_lint.py` |
| P1-02 Post-v1.1.6 Projection And Registry Hardening | COMPLETE | `conformance/profile_projection_field_catalog.yaml`, `conformance/profile-projection/`, `tools/validate_projection.py`, `spec/extension-registry.yaml`, `tools/validate_extension_registry.py` |
| P1-03 Human And AI Agent Change Governance | COMPLETE | `AGENTS.md`, `docs/zmeta_change_governance.md`, `tools/build_release_manifest.py`, `tools/validate_release_manifest.py`, downstream clone compatibility guidance |
| R1-03 v1.1.7 Stack Audit And Release | COMPLETE | `docs/r1_03_v1_1_7_stack_audit_release.md`, `release/RELEASE_NOTES_v1.1.7.md`, `release/VALIDATION_REPORT_v1.1.7.md`, `release/SHA256SUMS_v1.1.7.txt` |
| P1-04 Bearing Reference-Frame Integrity Pass | COMPLETE (adopted on `main`) | `spec/semantics-contract.md` 6.4, `schema/zmeta-event-1.1.0.schema.json`, `spec/extension-registry.yaml`, `conformance/bad-events/`, `conformance/adapter-harness/`, `tools/validate_adapter_conformance.py`, kraken/moth/signalhunter/mavlink adapters, `gateway/src/gateway.py` |
| R1-04 v1.1.8 Bearing-Frame Integrity Release | COMPLETE | `docs/r1_04_v1_1_8_bearing_frame_release.md`, `release/RELEASE_NOTES_v1.1.8.md`, `release/VALIDATION_REPORT_v1.1.8.md`, `release/SHA256SUMS_v1.1.8.txt` |
| R1-04A v1.1.8 Post-Release Reference Cleanup | COMPLETE | `README.md`, `.github/workflows/ci.yml`, `tools/README.md`, `docs/zmeta_professional_overview.md`, `gateway/tests/test_check_compat_cli.py`, current handoff/worklog notes |
| S1-22 Final Baseline Audit And Closeout Notes | COMPLETE | `CHANGELOG.md`, `docs/zmeta_refinement_worklog.md`, `docs/zmeta_refinement_handoff.md`, local `LOCAL_NOTES.md`; final audit closeout commit `c814d95` |
| S1-23 README-Linked Documentation Freshness Audit | COMPLETE | `spec/installation-guide.md`, `CHANGELOG.md`, `docs/zmeta_refinement_worklog.md`, `docs/zmeta_refinement_handoff.md`, local `LOCAL_NOTES.md` |
| R1-05 v1.1.9 Documentation Freshness Release | COMPLETE | `release/RELEASE_NOTES_v1.1.9.md`, `release/VALIDATION_REPORT_v1.1.9.md`, `release/SHA256SUMS_v1.1.9.txt`, `release/zmeta-release-manifest.yaml` |

## Current Decisions

- The semantic contract is authoritative; implementation surfaces must preserve it.
- Humans and AI agents should follow `AGENTS.md` and
  `docs/zmeta_change_governance.md` before changing governed artifacts.
- Downstream clone users can integrate locally around pinned releases, but
  schema, vocabulary, version-dispatch, projection, risk, or command-authority
  changes are private dialect/fork work unless governed, versioned, documented,
  and backed by conformance evidence.
- Current formal release is `v1.1.9`; latest integration baseline is current `main`.
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

- Outgoing UDP payloads larger than roughly 65507 bytes raise an unhandled
  `OSError` in the gateway main loop (crash risk). The `warn_datagram_bytes`
  guard added in P1-04 is observability only and does not change send
  behavior; whether to catch/drop/truncate is a future hardening decision.
- Several ingress adapters fabricate `lineage.based_on` with a fresh random
  UUIDv7 (pre-existing behavior, out of scope for P1-04); candidate for a
  future lineage-policy pass.
- Bearing frame provenance is still producer/configuration asserted. The
  `TRUE_NORTH` marker and `quality.heading_source` make the assertion auditable
  and reject unsupported labels, but they do not prove calibration,
  authenticity, or frame correctness. Treat deeper verification as future
  trust/PNT/integrity work rather than a current release blocker.

## Next Work Queue

1. **No active required ZMeta work**
   - The current stack is closed for the downstream integration baseline.
   - Optional follow-ups remain future work only when real sensor data,
     versioned semantic branch approval, or release-authority signing inputs
     exist.
   - S1-11B remains an optional future artifact, not an active blocker.

2. **Human decisions for future hardening**
   - Exact candidate precision defaults by profile and field family.
   - Whether precision values are global defaults or mission/profile
     configurable.
   - Whether Profile L has one universal precision policy or multiple mission
     policies.
   - Whether coordinate quantization is decimal-place-based, grid-based, or
     uncertainty/CEP-based.
   - Whether confidence rounding floors to fixed decimals or configured buckets.
   - Whether command geometry precision policy is stricter than STATE_EVENT
     display policy.
   - Whether RF quantization varies by modality, sensor resolution, band, or
     mission.
   - Whether precision policy is enforced in gateway exports, conformance only,
     or both.
   - Whether current class statuses should be `implemented` or `active`.
   - Whether claim files should require captured test output artifacts or only
     command/result summaries.
   - Whether future formal releases should publish detached signatures after an
     approved release signing key/process exists.
   - Whether future formal tagged releases should publish post-release claim
     attestations that include release_manifest_hash.
   - How broad the next adapter-harness expansion should be before claiming
     sensor-adapter certification.
   - Whether v1.1.0 concepts remain `experimental` or any should be promoted.
   - Whether registry validation should remain opt-in or become part of strict
     conformance after the format stabilizes.
   - How to represent vendor/private namespaces and classified/restricted names.
   - Whether encoding-negative fixtures should store malformed bytes as hex,
     base64, or generated-at-test-time inputs.
   - Whether to add a future `ZMETA-ENCODING-NEGATIVE-VALIDATION` class or fold
     the suite into existing compact/protobuf classes.
   - Whether `--encoding-negative` should remain opt-in indefinitely or later
     join strict release conformance.
   - Whether `--precision-policy` should remain opt-in indefinitely or later
     join strict release conformance.
   - Whether to implement S1-11B or keep the future-branch roadmap as
     documentation only.

3. **Deferred issue cleanup**
   - D-001 MAVLink Adapter README State Payload Drift is closed.
   - D-002 Contract Hash / Release Hash Follow-Up is closed.
   - D-003 Future Semantics Require Versioned Implementation Branches is
     `OPEN - ROADMAP PLANNED`.
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

4. **Later versioned semantic branches**
   - Markings/releasability.
   - Integrity, signing, anti-replay, mesh trust, and quarantine.
   - MODEL_STATUS / assurance and drift monitoring.
   - UAS identity and behavioral trust.
   - Track lifecycle extensions.
   - Coalition export and cross-domain guard metadata.
   - Compute status and degraded runtime behavior.

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

Most recent validation for the final current-main baseline audit on `main`
(2026-06-12, Windows, Python, final pushed audit commit `c814d95`; validation
was originally performed across the `beffed3` guidance cleanup and the
subsequent `c814d95` closeout-note commit):

```powershell
python tools\validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative --precision-policy --release-manifest --release-package --bad-events --adapter-harness
python tools\validate_examples.py --strict --require-all
python tools\validate_release_manifest.py --manifest release\zmeta-release-manifest.yaml
python tools\validate_release_package.py --manifest release\zmeta-release-manifest.yaml --templates-only
python tools\lint_policy_risk_modes.py
python tools\check_compat.py examples\zmeta-v1.1-examples.jsonl --target v1.1.8
python tools\measure_packet_size.py --file examples\zmeta-profile-L-examples.jsonl --encodings compact --max-bytes 240 --summary-only
python -m pytest -q
python tools\test_workflow_end_to_end.py
python tools\test_workflow_end_to_end.py --profile M
python tools\test_workflow_end_to_end.py --profile L --listen-port 5655 --forward-port 5656 --cot-port 5657
python tools\test_workflow_end_to_end.py --profile M --expect COMMAND_EVENT,SYSTEM_EVENT --listen-port 5665 --forward-port 5666 --cot-port 5667
python tools\test_gateway_live.py --listen-port 5675 --forward-port 5676 --cot-port 5677
python tools\test_gateway_live.py --profile L --encoding cbor --input-encoding cbor --listen-port 5685 --forward-port 5686 --cot-port 5687
python tools\test_gateway_live.py --profile L --encoding compact --input-encoding compact --listen-port 5695 --forward-port 5696 --cot-port 5697
python tools\test_gateway_live.py --profile H --encoding proto --input-encoding proto --no-cot --listen-port 5705 --forward-port 5706 --cot-port 5707
python tools\build_release_package.py --manifest release\zmeta-release-manifest.yaml --output-dir .tmp\audit-package-v1.1.8-20260612 --release-id zmeta-v1.1.8 --release-state current-main-audit --no-signatures --allow-dirty
python tools\validate_release_package.py --manifest release\zmeta-release-manifest.yaml --package-dir .tmp\audit-package-v1.1.8-20260612
python release\build_release_bundle.py --version 1.1.8
python release\build_mvp_packages.py --version v1.1.8
python tools\compute_contract_hash.py
python tools\validate_projection.py --catalog conformance\profile_projection_field_catalog.yaml --must-pass conformance\profile-projection\must-pass.jsonl --must-fail conformance\profile-projection\must-fail.jsonl --quiet
python tools\validate_extension_registry.py --registry spec\extension-registry.yaml
python tools\validate_conformance_classes.py --manifest conformance\conformance_classes.yaml --claims conformance\claims\example-reference-gateway.yaml conformance\claims\example-core-producer.yaml
python tools\validate_bad_events.py --must-fail conformance\bad-events\must-fail.jsonl
python tools\validate_adapter_conformance.py --fixtures conformance\adapter-harness\must-pass.jsonl
python tools\validate_encoding_negative.py --fixtures conformance\encoding-negative
python tools\validate_precision_policy.py --policy policy\profile-precision.yaml --must-pass conformance\profile-precision\must-pass.jsonl --must-fail conformance\profile-precision\must-fail.jsonl
python tools\validate.py --file examples\zmeta-command-examples.jsonl --profile L --strict
docker compose -f deploy\gateway\docker-compose.yml config
docker compose -f deploy\edge\docker-compose.yml config
docker compose -f gateway\docker-compose.yml config
gh pr list --repo JTC-byte/zmeta-spec --state open --limit 20
gh issue list --repo JTC-byte/zmeta-spec --state open --limit 20
git diff --check
```

Full kernel conformance result: `projection conformance ok total=37`,
`extension registry ok entries=57`, `conformance classes ok classes=34
claims=2`, `encoding negative ok total=50`, `profile precision policy ok
total=32`, `bad-event corpus ok total=10`, `adapter conformance ok total=10`,
`conformance ok`.
Examples result: `overall total=40 passed=40 failed=0 warnings=0`.
Release manifest result: `release manifest ok groups=18 artifacts=67`.
Release package result: `release package ok mode=templates` and
`release package ok mode=package` for the throwaway `.tmp` audit package.
Policy lint result: `policy risk mode lint ok`.
Compatibility result: `issues=0 failed=0 warnings=0` for the v1.1 example
stream against target `v1.1.8`.
Packet-size result: compact Profile L `max=150` under the 240-byte check.
Full pytest result: `442 passed, 110 subtests passed`.
End-to-end and live gateway results: Profile H/M/L, command/system, JSON, CBOR,
compact, and proto paths passed. One attempted parallel workflow run failed
only because multiple tests bound the same localhost UDP ports; sequential
reruns on unique ports passed. Docker Compose rendered all three configs
successfully with local `C:\Users\User\.docker\config.json` access warnings
only. GitHub PR and issue list checks returned no open items. GitHub CI passed
for pushed commit `c814d95` as run `27447655568`. Final local status was clean
against `origin/main`.

Earlier validation for the P1-04R review fixes on branch
`review/pr2-frame-fixes` (2026-06-12, Windows, Python):

```powershell
python -m pytest -q adapters\ingress\moth\test_moth_ingress.py adapters\ingress\mavlink\test_mavlink_ingress.py
python tools\validate_adapter_conformance.py --quiet
python tools\build_release_manifest.py --release-id zmeta-v1.1.7 --release-name "ZMeta v1.1.7" --release-status formal_release --release-date 2026-06-10 --branch main --update-claims
python tools\validate_release_manifest.py --manifest release\zmeta-release-manifest.yaml
python tools\validate_release_package.py --manifest release\zmeta-release-manifest.yaml --templates-only
python tools\validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative --precision-policy --release-manifest --release-package --bad-events --adapter-harness
python -m pytest -q
git diff --check
```

Focused adapter pytest result: `29 passed`.
Adapter harness result: `adapter conformance ok total=10`.
Release manifest result: `release manifest ok groups=18 artifacts=62`.
Release package template result: `release package ok mode=templates`.
Full kernel conformance result: `projection conformance ok total=37`,
`extension registry ok entries=57`, `conformance classes ok classes=34
claims=2`, `encoding negative ok total=49`, `profile precision policy ok
total=32`, `bad-event corpus ok total=10`, `adapter conformance ok total=10`,
`conformance ok`.
Full pytest result: `435 passed, 108 subtests passed`.
Whitespace check result: clean with normal Windows LF-to-CRLF working-copy
warnings.

Earlier validation for the P1-04 bearing reference-frame pass on branch
`worktree-bearing-frame-fixes` (2026-06-11, macOS, Python 3.12):

```bash
python3.12 tools/build_release_manifest.py --release-id zmeta-v1.1.7 --release-name "ZMeta v1.1.7" --release-status formal_release --release-date 2026-06-10 --branch main --update-claims
python3.12 tools/validate_release_manifest.py --manifest release/zmeta-release-manifest.yaml
python3.12 tools/validate_release_package.py --manifest release/zmeta-release-manifest.yaml --templates-only
python3.12 tools/validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative --precision-policy --release-manifest --release-package --bad-events --adapter-harness
python3.12 -m pytest -q
git diff --check
```

Release manifest result: `release manifest ok groups=18 artifacts=62`.
Release package template result: `release package ok mode=templates`.
Full kernel conformance result: `projection conformance ok total=37`,
`extension registry ok entries=57`, `conformance classes ok classes=34
claims=2`, `encoding negative ok total=49`, `profile precision policy ok
total=32`, `bad-event corpus ok total=10`, `adapter conformance ok total=9`,
`conformance ok`.
Full pytest result: `430 passed, 108 subtests passed`.
Whitespace check result: passed.

Earlier validation for the v1.1.7 stack audit and release:

```powershell
python tools\validate_release_manifest.py --manifest release\zmeta-release-manifest.yaml
python tools\validate_release_package.py --manifest release\zmeta-release-manifest.yaml --templates-only
python tools\validate_examples.py --strict --require-all
python tools\validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative --precision-policy --release-manifest --release-package --bad-events --adapter-harness
python -m pytest -q
python tools\validate_release_package.py --manifest release\zmeta-release-manifest.yaml --package-dir release\package-v1.1.7
python release\sign_release_artifacts.py --version v1.1.7 --write-checksums --verify-checksums
git diff --check
```

Release manifest result: `release manifest ok groups=18 artifacts=62`.
Release package template result: `release package ok mode=templates`.
Examples result: `overall total=40 passed=40 failed=0 warnings=0`.
Full kernel conformance result: `projection conformance ok total=37`,
`extension registry ok entries=56`, `conformance classes ok classes=34
claims=2`, `encoding negative ok total=49`, `profile precision policy ok
total=32`, `bad-event corpus ok total=9`, `adapter conformance ok total=8`,
`conformance ok`.
Full pytest result: `375 passed, 108 subtests passed`.
Release package output result: `release package ok mode=package`.
Release checksum result: `checksums ok: SHA256SUMS_v1.1.7.txt`.
Runtime workflow, live gateway, packet-size, compatibility, focused validator,
policy-risk lint, and Docker Compose config checks are recorded in
`release/VALIDATION_REPORT_v1.1.7.md`.
Whitespace check result: passed with normal Windows CRLF conversion warnings.
