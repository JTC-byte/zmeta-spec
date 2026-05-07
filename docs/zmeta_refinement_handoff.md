# ZMeta Refinement Handoff Notes

Status date: 2026-05-07

This note is the quick resume point for the current ZMeta refinement effort. The full task history and deferred issue register are in `docs/zmeta_refinement_worklog.md`.

## Current Position

The semantic contract has been audited, rewritten, and crosswalked against the current implementation stack. The locked v1.0 baseline was verified, and no S1-01B targeted schema implementation task is currently needed.

The next active implementation item is:

**S1-02B - Profile Projection Preservation Field Catalog and Conformance Suite Implementation**

Start from `docs/s1_02_profile_projection_preservation_plan.md`.

## Key Docs

| Document | Purpose |
| --- | --- |
| `spec/semantics-contract.md` | Authoritative hardened semantic contract. Schemas, policy packs, adapters, encodings, examples, gateways, and conformance tests must preserve it. |
| `docs/zmeta_semantic_contract_lockdown_audit.md` | S0-01 audit of the prior contract against intended ZMeta roles, implementation surfaces, and future ISR/edge AI/coalition/mesh trust needs. |
| `docs/zmeta_contract_to_stack_crosswalk.md` | S0-03 contract-to-implementation crosswalk and prioritized implementation backlog. |
| `docs/s1_01_v1_baseline_verification_plan.md` | S1-01A v1.0 baseline verification. Confirms current v1.0 schema/policy coverage and states S1-01B is not needed. |
| `docs/s1_02_profile_projection_preservation_plan.md` | S1-02A plan for profile projection invariants, field catalog, fixture format, positive/negative conformance cases, and S1-02B file-by-file implementation. |
| `docs/zmeta_refinement_worklog.md` | Running worklog, completed work items, pending work items, and deferred issue register. |

## Completed Recently

| Work Item | Status | Output |
| --- | --- | --- |
| S0-01 Semantic Contract Lockdown Audit | COMPLETE | `docs/zmeta_semantic_contract_lockdown_audit.md` |
| S0-02 Semantic Contract Rewrite and Hardening | COMPLETE | `spec/semantics-contract.md` |
| S0-03 Contract-to-Stack Crosswalk | COMPLETE | `docs/zmeta_contract_to_stack_crosswalk.md` |
| S1-01A v1.0 Baseline Verification | COMPLETE | `docs/s1_01_v1_baseline_verification_plan.md` |
| S1-02A Profile Projection Preservation Plan | COMPLETE | `docs/s1_02_profile_projection_preservation_plan.md` |

## Current Decisions

- The semantic contract is authoritative; implementation surfaces must preserve it.
- v1.0 remains locked.
- Do not add v1.1.0 or future concepts to v1.0.
- S1-01A found no schema-enforceable v1.0 gap requiring S1-01B.
- Profile projection preservation is the current P0 implementation gap.
- Profile preservation should be proven with a sidecar field catalog and source/projected conformance pairs, not by adding projection metadata to v1.0 events.
- Compact Profile L and protobuf remain encoding projections; both must decode to canonical JSON before schema, policy, and projection checks.

## Next Work Queue

1. **S1-02B - Profile Projection Preservation Field Catalog and Conformance Suite Implementation**
   - Add `conformance/profile_projection_field_catalog.yaml`.
   - Add source/projected fixture format under `conformance/profile-projection/`.
   - Add `tools/validate_projection.py` or equivalent projection conformance runner.
   - Add positive and negative projection fixtures.
   - Add gateway/tool tests for event ID, source, track ID, lineage, confidence, TTL, precision, units, and prohibited rewrites.
   - Add compact/protobuf decoded-equivalence tests.

2. **Deferred issue cleanup after S1-02B**
   - D-006 Extension Registry Artifact Missing.
   - D-007 Encoding Negative Validation Gap.
   - D-008 Conformance Class Manifest Missing.
   - D-009 v1.0/v1.1 Observation Extension Boundary Needs Explicit Tests.

3. **Later versioned semantic branches**
   - Markings/releasability.
   - Integrity, signing, anti-replay, mesh trust, and quarantine.
   - MODEL_STATUS / assurance and drift monitoring.
   - UAS identity and behavioral trust.
   - Track lifecycle extensions.
   - Coalition export and cross-domain guard metadata.
   - Compute status and degraded runtime behavior.

## Guardrails for Next Prompt

- Do not change schemas unless the prompt explicitly moves into a schema implementation item.
- Do not recompute release/contract hashes until the stack-hardening branch is intentionally ready.
- Do not make v1.1.0 or future concepts valid under `zmeta_version: "1.0"`.
- Keep profile projection checks pairwise and external to v1.0 event payloads.
- Document any newly discovered issues in the deferred issue register in `docs/zmeta_refinement_worklog.md`.

## Verification State

Most recent validation run during S1-01A:

```powershell
python tools\validate_conformance.py --strict
```

Result: `conformance ok`.

S1-02A was documentation-only. No implementation tests were run for S1-02A.
