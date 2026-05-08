# S1-09C - Contract Hash / Release Hash Post-Implementation Audit

Date: 2026-05-07

## Summary

S1-09C audited the S1-09B release hash implementation and made one small
cleanup fix for reproducibility. The original S1-09B manifest stamped the
current git commit by default, so rebuilding after the S1-09B checkpoint commit
changed `git_commit` and therefore `release_manifest_hash`. S1-09C fixed the
reference manifest path by using stable default placeholders for `git_commit`
and `branch`; formal release generation can still pass explicit metadata with
`--git-commit` and `--branch`.

The audit verifies that `contract_hash` remains narrow in release claims, the
structured release manifest carries the broader governed baseline, and hashes
remain governance artifacts only. No schema, semantic contract, extension
registry, gateway runtime, codec, adapter, or event-vocabulary changes were
made.

## Files Inspected

- S1-09B diff at commit `8abbdba`
- `docs/s1_09_contract_release_hash_plan.md`
- `spec/release-hash-policy.md`
- `release/zmeta-release-manifest.yaml`
- `tools/build_release_manifest.py`
- `tools/validate_release_manifest.py`
- `tools/compute_contract_hash.py`
- `gateway/tests/test_release_manifest.py`
- `tools/validate_conformance.py`
- `conformance/claims/example-reference-gateway.yaml`
- `conformance/claims/example-core-producer.yaml`
- `conformance/conformance_classes.yaml`
- `spec/conformance-classes.md`
- `spec/README.md`
- `conformance/README.md`
- `docs/zmeta_refinement_worklog.md`
- `docs/zmeta_refinement_handoff.md`
- `spec/semantics-contract.md`
- `spec/versioning.md`
- schema files under `schema/`
- policy YAML under `policy/` and `configs/policy-variants/`
- `spec/extension-registry.md`
- `spec/extension-registry.yaml`
- profile projection, encoding-negative, and profile-precision fixtures
- compact/protobuf specs and codec files
- release asset tooling under `release/`
- gateway hash gate code in `gateway/src/gateway.py`

## Files Changed During S1-09C

- `docs/s1_09c_contract_release_hash_audit.md`
- `docs/zmeta_refinement_worklog.md`
- `docs/zmeta_refinement_handoff.md`
- `gateway/tests/test_release_manifest.py`
- `release/zmeta-release-manifest.yaml`
- `spec/release-hash-policy.md`
- `tools/build_release_manifest.py`

## Drift Checks

- Schema drift: none. The dispatcher, v1.0, and v1.1.0 JSON schemas were not
  changed.
- Semantic contract drift: none. `spec/semantics-contract.md` was not changed.
- Extension registry drift: none. `spec/extension-registry.yaml` was not
  changed.
- Conformance class manifest validity: valid after S1-09C cleanup.
- New vocabulary: none. No v1.1.0 concept was promoted under v1.0, and no
  future/reserved registry concept became valid vocabulary.

## Release Hash Policy Review

`spec/release-hash-policy.md` correctly states that:

- the semantic contract hash is narrow and semantic;
- the release manifest hash is broader and identifies a governed artifact
  baseline;
- hashes do not create semantics or make future vocabulary valid;
- protobuf remains an experimental encoding projection;
- LF-normalized text hashing and raw binary hashing are the canonicalization
  rules;
- advisory plans and audits are excluded unless a future release explicitly
  lists them;
- D-004 companion artifacts should use a later companion manifest or explicit
  future release group.

S1-09C added clarification that formal tagged-release signatures and
attestations are tracked separately as D-012.

## Release Manifest Review

`release/zmeta-release-manifest.yaml` includes the required top-level fields:

- `manifest_version`
- `release_id`
- `release_name`
- `release_status`
- `release_date`
- `zmeta_versions`
- `hash_algorithm`
- `hash_canonicalization`
- category hashes
- `release_bundle_hash`
- `release_manifest_hash`
- `artifact_hashes`
- `artifact_groups`
- `tool_versions`
- `git_commit`
- `branch`
- `generated_by`
- `notes`
- `known_open_issues`
- `experimental_surfaces`
- `future_surfaces_not_valid`

`release_status` is `reference_hardening_baseline`. The manifest states it is
not a formal tagged release. Future and reserved surfaces are listed as not
valid vocabulary.

## Artifact Group Review

The manifest contains the expected artifact groups:

- `semantic_contract`
- `schema_bundle`
- `policy_bundle`
- `extension_registry`
- `conformance_classes`
- `core_conformance`
- `profile_projection`
- `encoding_negative`
- `profile_precision`
- `encoding_projection_specs`
- `claims`
- `release_policy`
- `release_tools`
- `conformance_tools`

The release manifest itself is not included in `release_bundle_hash`. Claim
files include category hashes but intentionally omit a concrete
`release_manifest_hash` value to avoid claim/manifest circularity.

## Canonicalization And Reproducibility Review

The builder and validator use SHA-256. Text files are decoded as UTF-8 and have
CRLF/CR normalized to LF before hashing. Binary files are hashed as raw bytes.
Paths are repo-relative and sorted lexicographically for group hashes.

`release_manifest_hash` is computed with `release_manifest_hash` set to `null`.
`release_bundle_hash` is computed from artifact group hashes and excludes
`release/zmeta-release-manifest.yaml`.

Reproducibility finding and fix:

- Finding: rebuilding the S1-09B manifest after the checkpoint commit changed
  `git_commit` from the pre-checkpoint commit to `8abbdba`, which changed
  `release_manifest_hash`.
- Fix: S1-09C changed the builder defaults so committed reference manifests use
  stable `git_commit` and `branch` placeholders. Formal release generation must
  pass explicit metadata.
- Verification: after the fix, rebuilding the manifest twice produced an
  identical file hash.

## Builder Behavior Review

`tools/build_release_manifest.py`:

- computes file, group, release bundle, and release manifest hashes;
- validates required artifacts while building;
- fails on missing required artifact paths;
- supports `--output`, release metadata flags, `--dry-run`, and claim update
  flags;
- uses stable default metadata for committed reference manifests;
- does not rewrite schemas, contract text, registry entries, runtime gateway
  behavior, codecs, adapters, conformance classes, or event examples.

## Validator Behavior Review

`tools/validate_release_manifest.py`:

- loads YAML;
- verifies required fields and groups;
- verifies listed artifact files exist;
- recomputes file hashes, group hashes, category hashes,
  `release_bundle_hash`, and `release_manifest_hash`;
- fails on missing artifacts and hash mismatches;
- rejects circular inclusion of `release/zmeta-release-manifest.yaml`;
- supports `--quiet`;
- uses the same canonicalization logic as the builder.

## `compute_contract_hash.py` Compatibility Review

`tools/compute_contract_hash.py` remains unchanged. It still prints the existing
gateway-compatible `schema_hash`, `policy_hash`, `semantics_hash`, and combined
`contract_hash` values. Release tooling does not redefine the gateway startup
gate behavior.

The documentation distinguishes the release claim `contract_hash` from the
legacy gateway combined contract hash: release claims use the narrow semantic
contract hash, while the gateway helper remains backward-compatible.

## Conformance Claim Integration Review

The example claims no longer use `pending_D-002` for the semantic contract
hash. Both claims include the actual `semantic_contract_hash` value under
`contract_hash` and list the other release category hashes under
`release_hashes`.

The claims intentionally set `release_manifest_hash` to
`omitted_to_avoid_claim_manifest_circularity`, because the reference manifest
includes the claim files. This is documented in the claims, conformance docs,
and release hash policy.

The core producer claim remains narrower than the reference gateway claim and
does not claim profile, projection, gateway, adapter, compact, or protobuf
support.

## Conformance Runner Integration Review

`tools/validate_conformance.py --release-manifest` is opt-in. Default
`--strict` behavior is unchanged. The release manifest flag can run with
projection, extension registry, conformance class, encoding-negative, and
precision-policy flags. Missing or invalid manifests are not silently skipped.

## Test Coverage Review

`gateway/tests/test_release_manifest.py` covers:

- manifest existence;
- YAML load;
- required top-level fields;
- required artifact groups;
- builder determinism;
- stable default reference metadata;
- current manifest validation;
- missing artifact failure;
- file hash mismatch failure;
- group hash mismatch failure;
- release bundle hash mismatch failure;
- release manifest self-hash mismatch failure;
- file ordering determinism;
- LF normalization determinism;
- unchanged default strict conformance;
- optional `--release-manifest` conformance success.

## Verification

S1-09C verification passed:

- release manifest validation: `release manifest ok groups=14 artifacts=49`;
- manifest rebuild idempotence check: unchanged file hash after immediate
  rebuild;
- gateway-compatible hash helper: schema, policy, semantics, and combined
  contract hashes printed successfully;
- strict conformance and all optional conformance suites passed;
- projection validator: `projection conformance ok total=33`;
- extension registry validator: `extension registry ok entries=63`;
- conformance class validator: `conformance classes ok classes=30 claims=2`;
- encoding-negative validator: `encoding negative ok total=49`;
- precision-policy validator: `profile precision policy ok total=32`;
- focused release-manifest pytest: `16 passed`;
- full pytest: `322 passed`.

## D-002 Closure Recommendation

D-002 can close. The reference hardening-baseline release manifest exists,
validates, rebuilds reproducibly, and no longer depends on `pending_D-002` in
the semantic contract hash fields. Formal tagged-release signatures and
post-release attestations remain useful, but they are release packaging work,
not a blocker for the reference release hash baseline.

## Remaining Issue Status

- D-002: CLOSED.
- D-003: OPEN.
- D-004: OPEN.
- D-012: OPEN - Formal Release Tag, Signature, and Attestation Packaging.

## Recommended Next Work Item

S1-10A - Companion Artifact Roadmap Plan Only.
