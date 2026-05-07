# ZMeta Refinement Handoff Notes

Status date: 2026-05-07

This note is the quick resume point for the current ZMeta refinement effort. The full task history and deferred issue register are in `docs/zmeta_refinement_worklog.md`.

## Current Position

The semantic contract has been audited, rewritten, and crosswalked against the current implementation stack. The locked v1.0 baseline was verified, and no S1-01B targeted schema implementation task is currently needed. Profile projection preservation has been implemented and audited as sidecar conformance tooling without changing v1.0 schema or event vocabulary. S1-03B implemented the extension registry, and S1-03C audited it without changing schemas or making new vocabulary valid.

The next active implementation item is:

**S1-04A - Conformance Class Manifest Plan Only**

## Key Docs

| Document | Purpose |
| --- | --- |
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

## Current Decisions

- The semantic contract is authoritative; implementation surfaces must preserve it.
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
- D-011 remains open. S1-03C added a validator/test guard so `TAKEOFF` cannot
  appear in current schema vocabulary unnoticed, but the crosswalk typo still
  needs a narrow docs cleanup.

## Next Work Queue

1. **S1-04A - Conformance Class Manifest Plan Only**
   - Plan machine-readable conformance class claims and test selectors.
   - Do not implement conformance class artifacts yet.

2. **Human decisions before later registry promotion**
   - Whether v1.1.0 concepts remain `experimental` or any should be promoted.
   - Whether registry validation should remain opt-in or become part of strict
     conformance after the format stabilizes.
   - How to represent vendor/private namespaces and classified/restricted names.
   - Whether companion artifacts stay as a registry category or split into a
     separate manifest later.
   - Whether to clean the crosswalk `TAKEOFF` typo in the next narrow docs
     cleanup task or leave it deferred.

3. **Deferred issue cleanup**
   - D-007 Encoding Negative Validation Gap remains partially covered, not closed.
   - D-008 Conformance Class Manifest Missing.
   - D-009 v1.0/v1.1 Observation Extension Boundary Needs Explicit Tests.
   - D-010 Profile Precision / Quantization Policy Floors.
   - D-011 Crosswalk TAKEOFF Mention Cleanup.

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
- Do not recompute release/contract hashes until the stack-hardening branch is intentionally ready.
- Do not make v1.1.0 or future concepts valid under `zmeta_version: "1.0"`.
- Keep profile projection checks pairwise and external to v1.0 event payloads.
- Keep registry work plan-first and branch-scoped. A registry entry alone does
  not make vocabulary valid.
- Document any newly discovered issues in the deferred issue register in `docs/zmeta_refinement_worklog.md`.

## Verification State

Most recent validation after S1-03C:

```powershell
python tools\validate_extension_registry.py --registry spec\extension-registry.yaml
python tools\validate_conformance.py --strict
python tools\validate_conformance.py --strict --profile-projection
python tools\validate_conformance.py --strict --profile-projection --extension-registry
python -m pytest -q gateway\tests\test_extension_registry.py
python -m pytest
git diff --check
```

Result: validation passed through full pytest.
Focused extension registry tests: `12 passed`. Full pytest result: `254 passed`.
`git diff --check` passed with CRLF conversion warnings only.
