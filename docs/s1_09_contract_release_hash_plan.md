# S1-09A - Contract Hash / Release Hash Follow-Up Plan

Date: 2026-05-07

Status: plan only. No hashes were recomputed, no release manifest was
implemented, and no schemas, validators, policy files, gateway runtime behavior,
codecs, adapters, conformance fixtures, conformance class manifests, extension
registry artifacts, semantic contract text, or event vocabulary were changed.

## A. Current Hash / Release Landscape

Current hash-related tooling and references:

- `tools/compute_contract_hash.py` is a thin wrapper around
  `gateway.src.gateway.compute_contract_hash`. It currently computes:
  - `schema_hash` from one schema file, defaulting to
    `schema/zmeta-event-1.0.schema.json`;
  - `policy_hash` from all files under the active `policy/` directory;
  - `semantics_hash` from `spec/semantics-contract.md`;
  - `contract_hash` as a combined hash of the schema, policy, and semantic
    contract hashes.
- `gateway/src/gateway.py` contains the underlying hash helpers. It hashes file
  contents with path names, hashes directories in stable path order, prints hash
  values on gateway startup, can stamp `contract_hash` into generated gateway
  system events, and can gate startup with `require_schema_hash`,
  `require_policy_hash`, and `require_contract_hash`.
- `configs/*.json`, `gateway/config/gateway-config.example.json`,
  `configs/README.md`, `gateway/README.md`, `README.md`, and `tools/README.md`
  document the current startup gate and hash recomputation workflow.
- `release/build_release_bundle.py` creates release zip artifacts and a plain
  `MANIFEST.txt` inside `release/dist`. That manifest is a file list, not a
  semantic release manifest.
- `release/sign_release_artifacts.py` writes and verifies
  `SHA256SUMS_<version>.txt` for release zip assets, release notes, and
  validation reports, and can produce detached signatures. This proves asset
  integrity and publisher authenticity, but it does not classify the semantic,
  schema, policy, registry, conformance, encoding, or precision baselines.
- Existing release notes and validation reports record historic
  `contract_hash` values.
- `conformance/claims/example-reference-gateway.yaml` and
  `conformance/claims/example-core-producer.yaml` currently use
  `contract_hash: pending_D-002`.
- `docs/zmeta_refinement_worklog.md` and
  `docs/zmeta_refinement_handoff.md` keep D-002 open because the hardened
  semantic contract and supporting conformance/governance artifacts need an
  intentional hash update path.

What remains undefined:

- Which files make up the release-grade semantic, schema, policy, registry,
  conformance, encoding, and precision baselines.
- Which hashes are narrow governance hashes versus broad release bundle hashes.
- Whether hash tooling should use raw committed bytes, normalized line endings,
  or canonical YAML/JSON serialization.
- Where a machine-readable release manifest should live.
- How conformance claims should reference actual release hashes once D-002 is
  resolved.
- How deployment gates should use a manifest without overloading
  `contract_hash`.

## B. Problem Statement

The stack needs a deliberate release-hash process now because the normative
baseline and supporting evidence changed materially during hardening:

- `spec/semantics-contract.md` was rewritten and hardened.
- Schemas remained locked, but release consumers still need to know exactly
  which dispatcher, v1.0, v1.1.0, and protobuf projection schemas were released.
- The policy pack controls runtime role, profile, timing, lineage, producer
  authority, routing, precision, and violation behavior.
- The extension registry now governs future vocabulary without making that
  vocabulary valid.
- The conformance class manifest now governs precise implementation claims.
- Projection preservation, encoding-negative validation, and precision-policy
  artifacts now define important profile and encoding evidence.
- Deployments using `require_contract_hash`, release validation, or claim files
  need reproducible proof that a release uses the intended baseline.

Hash governance must be deliberate. A casual hash update can hide semantic
drift, while stale hashes can cause correct hardened deployments to fail
startup gates.

## C. Hash Taxonomy

S1-09B should separate hash categories instead of using one overloaded value.

Recommended categories:

- `semantic_contract_hash`: narrow hash for `spec/semantics-contract.md`.
- `schema_bundle_hash`: dispatcher, locked v1.0 schema, experimental v1.1.0
  schema, and optional schema README metadata if release policy includes it.
- `policy_bundle_hash`: release-included policy YAML files under `policy/`,
  including `policy/profile-precision.yaml`.
- `extension_registry_hash`: `spec/extension-registry.yaml` and, optionally,
  the human-readable registry doc as a separate artifact hash.
- `conformance_class_manifest_hash`: `conformance/conformance_classes.yaml`.
- `profile_projection_catalog_hash`: projection field catalog plus projection
  must-pass/must-fail/context fixtures.
- `encoding_negative_suite_hash`: compact/protobuf/gateway encoding-negative
  JSONL fixtures and README.
- `profile_precision_policy_hash`: precision policy YAML plus precision
  must-pass/must-fail/context fixtures.
- `encoding_projection_specs_hash`: compact CBOR and protobuf specs, protobuf
  `.proto`, and codec implementations if the release manifest includes code
  evidence.
- `release_manifest_hash`: hash of the generated machine-readable release
  manifest excluding its own hash field or using a documented self-hash
  convention.
- `release_bundle_hash`: broad hash of the approved release artifact surface or
  the release zip assets, separate from semantic contract meaning.

Clarifications:

- `semantic_contract_hash` should stay narrow and stable. It should not include
  validators, examples, release notes, or generated outputs.
- `release_bundle_hash` can include the full approved release surface and is
  expected to change more often.
- Protobuf remains experimental projection support. Its schema and codec should
  be included under an encoding projection hash, not treated as v1.0 semantic
  authority.
- Future companion artifacts under D-004 should get a companion manifest later
  rather than bloating core event hashes.

## D. Normative vs Supporting Artifact Classification

Recommended classification for release hashing:

### Normative semantic baseline

Hash:

- `spec/semantics-contract.md`
- `spec/versioning.md`, if S1-09B confirms it is release-normative rather than
  advisory version guidance.

Do not mix this hash with implementation code or conformance fixtures.

### Schema baseline

Hash:

- `schema/zmeta-event.schema.json`
- `schema/zmeta-event-1.0.schema.json`
- `schema/zmeta-event-1.1.0.schema.json`

Classify separately:

- `schema/proto/zmeta_event_v1.proto` as an experimental encoding projection
  schema, not v1.0 semantic authority.
- `schema/README.md` as explanatory release documentation unless maintainers
  decide schema README guidance is part of the release baseline.

### Policy baseline

Hash:

- `policy/*.yaml`, including `policy/profile-precision.yaml`.

Handle separately:

- `configs/policy-variants/*.yaml` should not alter the reference policy hash
  unless explicitly included in a deployment or release variant manifest.

### Governance / vocabulary baseline

Hash:

- `spec/extension-registry.yaml`
- `conformance/conformance_classes.yaml`

Optionally include human-readable docs as artifact hashes:

- `spec/extension-registry.md`
- `spec/conformance-classes.md`

### Conformance evidence baseline

Hash:

- `conformance/must-pass.jsonl`
- `conformance/must-fail.jsonl`
- `conformance/profile_projection_field_catalog.yaml`
- `conformance/profile-projection/*.jsonl`
- `conformance/encoding-negative/*.jsonl`
- `conformance/profile-precision/*.jsonl`
- example claim files, if the release manifest intends to publish example
  claim baselines.

Do not treat example claim files as proof of a release unless their commit and
hash placeholders have been replaced.

### Encoding projection baseline

Hash:

- `spec/compact-binary-mapping.md`
- `spec/protobuf-encoding.md`
- `schema/proto/zmeta_event_v1.proto`
- `zmeta_compact.py`
- `zmeta_cbor.py`
- `zmeta_proto.py`

Keep this category separate from `semantic_contract_hash`.

### Advisory documentation

Usually do not include in narrow semantic, schema, or policy hashes:

- S1 audit documents and plans.
- `docs/zmeta_refinement_handoff.md`
- historical release notes and validation reports.
- white papers, backlog docs, handoff notes, and issue registers.

These can be included in a broad `release_bundle_hash` or as named
`artifact_hashes` when a release wants full reproducibility.

## E. Canonicalization Rules

Recommended S1-09B default:

- Use SHA-256.
- Hash UTF-8 text files as bytes from the committed checkout.
- Preserve stable path ordering by sorted POSIX-style repo-relative paths.
- Include the repo-relative path and file bytes in bundle hashes so identical
  content at different paths does not collide.
- Exclude `.git`, caches, virtual environments, `__pycache__`, build outputs,
  local temp files, generated reports, and release zip outputs unless the
  manifest explicitly defines an asset hash.
- Do not include timestamps that change between runs in any computed bundle
  hash. Release dates belong in manifest metadata, not in an input hash set
  unless intentionally included.
- Avoid canonical YAML/JSON serialization for the first implementation because
  comments, ordering, and formatting are part of reviewed release artifacts.
- Document line-ending behavior explicitly.

Windows / CRLF handling:

- Conservative option: hash raw committed file bytes after normal git checkout
  normalization. This mirrors what deployment files actually contain.
- Portable option: normalize text line endings to LF inside the hash tool.
- Recommendation: S1-09B should choose one behavior, expose it in
  `spec/release-hash-policy.md`, and test it. If the repo continues to surface
  CRLF warnings on Windows, prefer explicit LF normalization for text artifacts
  and raw-byte hashing for binary release assets.

## F. Proposed Release Manifest Model

Recommended path:

```text
release/zmeta-release-manifest.yaml
```

Rationale: the repo already uses `release/` for release notes, validation
reports, release bundle builders, checksum manifests, signatures, and release
assets. Keeping the machine-readable manifest there avoids treating it as a
schema or semantic contract file while still making it part of release
governance.

Recommended manifest fields:

```yaml
manifest_version: 1
release_id: zmeta-v1.1.5-hardened-candidate
release_name: ZMeta Hardened Baseline
release_date: "YYYY-MM-DD"
zmeta_versions:
  normative: ["1.0"]
  experimental: ["1.1.0"]
semantic_contract_hash: sha256:<hex>
schema_bundle_hash: sha256:<hex>
policy_bundle_hash: sha256:<hex>
extension_registry_hash: sha256:<hex>
conformance_class_manifest_hash: sha256:<hex>
profile_projection_catalog_hash: sha256:<hex>
encoding_negative_suite_hash: sha256:<hex>
profile_precision_policy_hash: sha256:<hex>
encoding_projection_specs_hash: sha256:<hex>
release_manifest_hash: sha256:<hex>
release_bundle_hash: sha256:<hex>
artifact_hashes:
  - path: spec/semantics-contract.md
    category: semantic_contract
    sha256: <hex>
tool_versions:
  python: <version>
  hash_tool: tools/build_release_manifest.py
git_commit: <commit>
branch: <branch>
generated_by: <user-or-tool>
notes: []
known_open_issues:
  - D-003
  - D-004
experimental_surfaces:
  - schema/zmeta-event-1.1.0.schema.json
  - schema/proto/zmeta_event_v1.proto
future_surfaces_not_valid:
  - reserved and proposed extension registry entries
```

The manifest must state that hashes are governance artifacts. They do not
redefine semantics, validate future vocabulary, or change runtime validation
behavior.

## G. Release Hash Tooling Plan

Preferred S1-09B implementation:

- Keep `tools/compute_contract_hash.py` focused on the current narrow gateway
  contract hash workflow, unless a small compatibility note or output addition
  is necessary.
- Add `spec/release-hash-policy.md` to define taxonomy, artifact sets,
  canonicalization, line-ending behavior, manifest fields, and gate semantics.
- Add `tools/build_release_manifest.py` to compute category hashes and write
  `release/zmeta-release-manifest.yaml`.
- Add `tools/validate_release_manifest.py` to load the manifest, recompute
  hashes, fail on missing files or mismatches, and validate category
  classification.
- Add focused tests under `gateway/tests/test_release_manifest.py` or
  `gateway/tests/test_release_hash_policy.py`.
- Update release docs, conformance docs, and claim guidance to reference the new
  manifest.

Do not overload `contract_hash` to mean the entire repo. The existing gateway
startup gate should continue to work for schema/policy/semantics until a
separate deployment manifest gate is explicitly added.

## H. Gateway / Deployment Hash Gate Plan

Current gateway behavior:

- Computes schema, policy, semantic-contract, and combined contract hashes at
  startup.
- Prints the hashes.
- Supports `--require-schema-hash`, `--require-policy-hash`, and
  `--require-contract-hash`.
- Can stamp the combined contract hash into generated gateway system events and
  metrics logs.

Recommended deployment model:

- Minimum production gate: require `semantic_contract_hash`, `schema_bundle_hash`
  or current `schema_hash`, and `policy_bundle_hash` or current `policy_hash`.
- Release-aware gate: validate `release/zmeta-release-manifest.yaml` out of
  band before gateway startup, then configure the existing gateway hash gates
  from the manifest values.
- Optional strict release gate: a future gateway/deployment wrapper can require
  `release_manifest_hash`, `extension_registry_hash`,
  `conformance_class_manifest_hash`, and policy/conformance suite hashes before
  accepting a deployment.
- Dev/test mode: allow disabled gates, but print the computed hashes and warn
  when expected hashes are absent.
- Failure reporting: mismatches should name the category, expected hash, actual
  hash, and likely file group.

Claim files should reference the release baseline they were tested against.
They should not depend on a broad release bundle hash alone.

## I. Conformance Claim Integration

S1-09B should plan claim updates but should only write release-grade values when
the release manifest exists and validates.

Recommended future claim fields:

- `contract_hash`: actual `semantic_contract_hash` or current gateway combined
  contract hash, whichever policy names explicitly.
- `release_manifest_hash`.
- `schema_bundle_hash`.
- `policy_bundle_hash`.
- `extension_registry_hash`.
- `conformance_class_manifest_hash`.
- `profile_projection_catalog_hash`.
- `encoding_negative_suite_hash`.
- `profile_precision_policy_hash`.

Example claims should move away from `pending_D-002` only when S1-09B or a
release-specific task creates and validates the actual hash values.

## J. Test and Validation Strategy

S1-09B should add deterministic tests for:

- Hash tool computes the same category hash across repeated runs.
- Stable file ordering means input enumeration order does not change the hash.
- Missing artifact fails manifest build or validation.
- Modified artifact changes the relevant category hash.
- Release manifest validation passes for current artifact hashes.
- Manifest validation fails on an intentional mismatch.
- Line-ending behavior is documented and tested where feasible.
- Experimental protobuf artifacts are classified as encoding projections, not
  v1.0 semantic authority.
- Default `tools/validate_conformance.py --strict` remains unchanged.
- Release validation is explicit and opt-in.

Validation commands after S1-09B should include all existing strict and optional
conformance suites plus the new manifest validator.

## K. S1-09B Implementation Plan

Recommended file-by-file plan:

- `spec/release-hash-policy.md`: human-readable policy for hash categories,
  artifact classification, canonicalization, manifest fields, and deployment
  gate semantics.
- `release/zmeta-release-manifest.yaml`: generated or checked-in manifest for
  the hardened baseline. It should contain no unstable generation timestamp in
  hash inputs.
- `tools/build_release_manifest.py`: computes artifact and category hashes and
  writes the manifest.
- `tools/validate_release_manifest.py`: validates manifest shape and recomputes
  category hashes.
- `tools/compute_contract_hash.py`: leave focused on gateway-compatible
  schema/policy/semantic contract hashes; update only if needed for terminology
  alignment.
- `gateway/tests/test_release_manifest.py`: tests deterministic hashing,
  missing file rejection, mismatch rejection, and manifest validation.
- `conformance/claims/example-reference-gateway.yaml`: update hash placeholders
  only after manifest values exist.
- `conformance/claims/example-core-producer.yaml`: same as above, with narrower
  claim scope.
- `spec/conformance-classes.md`: add release-hash reference only if claim
  guidance needs clarification.
- `conformance/README.md`, `spec/README.md`, `release/README.md`: document
  manifest build/validation commands.
- `docs/zmeta_refinement_worklog.md` and
  `docs/zmeta_refinement_handoff.md`: mark S1-09B implemented pending audit and
  add S1-09C.

If maintainers want an even narrower implementation, S1-09B can defer claim
updates until S1-09C audit confirms the manifest design.

## L. S1-09B Acceptance Criteria

S1-09B should be accepted only if:

- No schemas changed.
- The semantic contract is unchanged except that hashes are computed from it.
- Extension registry contents are unchanged.
- No new event vocabulary becomes valid.
- `spec/release-hash-policy.md` exists.
- `release/zmeta-release-manifest.yaml` exists and validates.
- Hash tooling exists and is deterministic.
- Manifest validation fails on missing files and hash mismatches.
- Line-ending behavior is documented.
- Existing strict conformance passes.
- Projection, extension registry, conformance classes, encoding-negative, and
  precision-policy optional suites pass.
- Conformance claims no longer use `pending_D-002` if the implementation scope
  includes claim updates.
- D-002 remains implemented pending S1-09C audit, not closed in S1-09B.

## M. Risks and Open Questions

- Should hashes use raw checkout bytes or normalized text with LF line endings?
- Should YAML/JSON be canonicalized or hashed exactly as reviewed?
- Should protobuf experimental artifacts be included in the core release
  manifest, an optional encoding group, or both?
- Should validator and tool source files be included in `release_bundle_hash`
  or only in release zip checksums?
- Should release manifests include test result summaries or only references to
  validation reports?
- Should manifests include git commit hashes alone, artifact hashes alone, or
  both? Recommendation: both.
- How should classified or local policy variants be represented without
  changing the public reference `policy_bundle_hash`?
- How should future D-004 companion artifacts get stable IDs and manifest
  hashes?
- Can D-002 close with a reference release manifest, or only after a tagged
  release publishes the manifest, checksums, signatures, and validation report?
- Should deployment wrappers eventually enforce `release_manifest_hash`, or
  should the reference gateway remain limited to schema/policy/contract gates?
