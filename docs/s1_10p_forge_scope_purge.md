# S1-10P - FORGE Scope Purge

Date: 2026-05-07

## Summary

S1-10P removes out-of-scope organizational artifact language from the ZMeta
baseline. The stopped S1-10B implementation was not committed, and its
generated files were rolled back before this purge.

ZMeta remains a semantic data standard for ISR interoperability,
bandwidth-aware profiles, lineage, adapters, encodings, validation,
conformance, and release baselines.

## Removed

- Deleted the superseded S1-10A broad artifact roadmap.
- Removed the contaminated semantic-contract boundary text and section.
- Removed broad non-ZMeta reserved entries from the extension registry.
- Removed the obsolete registry category used only by those entries.
- Updated release/hash policy and manifest metadata so D-004 is no longer an
  active ZMeta baseline issue.
- Updated worklog and handoff to mark S1-10B stopped before commit and D-004
  closed as removed from ZMeta scope.

## Why

The removed scope belongs outside the ZMeta standard. Keeping it in ZMeta would
blur the boundary between event semantics and external program artifacts.

## Files Changed

- `spec/semantics-contract.md`
- `spec/extension-registry.yaml`
- `spec/extension-registry.md`
- `spec/conformance-classes.md`
- `spec/release-hash-policy.md`
- `tools/build_release_manifest.py`
- `release/zmeta-release-manifest.yaml`
- `conformance/claims/example-reference-gateway.yaml`
- `conformance/claims/example-core-producer.yaml`
- `docs/zmeta_refinement_worklog.md`
- `docs/zmeta_refinement_handoff.md`
- `docs/s1_03_extension_registry_plan.md`
- `docs/s1_03c_extension_registry_audit.md`
- `docs/s1_04c_conformance_class_manifest_audit.md`
- `docs/s1_09_contract_release_hash_plan.md`
- `docs/s1_09c_contract_release_hash_audit.md`
- `docs/s1_10_companion_artifact_roadmap_plan.md` (deleted)
- `docs/zmeta_contract_to_stack_crosswalk.md`
- `gateway/tests/test_extension_registry.py`

## Verification

Validation and full pytest were run as recorded in the final S1-10P result.

Remaining open issues:

- D-003 - Future versioned semantic branches.
- D-012 - Formal release tag, signature, and attestation packaging.
