# ZMeta Release Hash Policy

This document defines the reference contract-hash and release-manifest hash
model for the hardened ZMeta baseline.

The semantic contract remains authoritative. Schemas, policies, registries,
conformance classes, projection catalogs, encoding fixtures, precision policy,
examples, gateways, adapters, and tools preserve the contract; they do not
replace it.

The semantic contract hash does not make implementation artifacts normative. It
identifies the normative semantic baseline.

The release manifest hash does not create semantics or make future vocabulary
valid. It identifies a reproducible bundle of approved artifacts.

## Purpose

Hash gates are governance controls. They let a deployment, release bundle, or
claim file say exactly which reviewed baseline it used. They must be stable
enough to reproduce and narrow enough that a single value does not hide what
changed.

ZMeta therefore separates:

- a narrow semantic contract hash for `spec/semantics-contract.md`;
- category hashes for schemas, policy, registry, class, conformance, precision,
  and encoding projection artifacts;
- a release bundle hash for the governed artifact set;
- a release manifest hash for the manifest content itself.

## Contract Hash Scope

`contract_hash` in release claims is the narrow semantic contract hash. It is
not a bundle hash and it is not a validator, schema, policy, gateway, adapter,
or test hash.

The legacy gateway hash helper still computes gateway-compatible `schema_hash`,
`policy_hash`, `semantics_hash`, and combined `contract_hash` values for the
existing `require_*_hash` startup gates. That behavior is preserved for backward
compatibility. Release manifests use explicit category hashes instead of
overloading that combined gateway value.

## Hash Taxonomy

Release manifests use these SHA-256 categories:

- `semantic_contract_hash`: narrow single-file group hash for
  `spec/semantics-contract.md`.
- `schema_bundle_hash`: dispatcher, v1.0, and experimental v1.1.0 JSON schemas.
- `policy_bundle_hash`: release-included policy YAML, including reference
  precision policy and policy variants.
- `extension_registry_hash`: machine-readable extension registry.
- `conformance_class_manifest_hash`: machine-readable conformance class
  manifest.
- `profile_projection_catalog_hash`: projection field catalog and
  source/projected fixtures.
- `encoding_negative_suite_hash`: compact/protobuf/gateway invalid-after-decode
  fixtures.
- `profile_precision_policy_hash`: precision policy and profile-precision
  fixtures.
- `encoding_projection_specs_hash`: compact CBOR and protobuf projection specs,
  protobuf `.proto`, and reference codec source.
- `release_bundle_hash`: deterministic hash over the listed artifact groups.
- `release_manifest_hash`: deterministic hash over the manifest with its own
  hash field set to `null`.

Protobuf is classified as an experimental encoding projection. It is not part
of the locked v1.0 semantic contract hash. Protobuf-encoded events must decode
to canonical ZMeta JSON before normal schema, policy, projection, registry,
conformance, and precision checks apply.

## Artifact Classification

The reference manifest at `release/zmeta-release-manifest.yaml` classifies
artifacts into these groups:

- `semantic_contract`: `spec/semantics-contract.md`.
- `schema_bundle`: `schema/zmeta-event.schema.json`,
  `schema/zmeta-event-1.0.schema.json`, and
  `schema/zmeta-event-1.1.0.schema.json`.
- `policy_bundle`: `policy/*.yaml` and release-included
  `configs/policy-variants/*.yaml`.
- `extension_registry`: `spec/extension-registry.yaml`.
- `conformance_classes`: `conformance/conformance_classes.yaml`.
- `core_conformance`: core `must-pass` and `must-fail` JSONL fixtures.
- `profile_projection`: profile projection catalog and JSONL fixtures.
- `encoding_negative`: compact/protobuf/gateway negative JSONL fixtures.
- `profile_precision`: `policy/profile-precision.yaml` and profile precision
  JSONL fixtures.
- `encoding_projection_specs`: compact/protobuf specs, protobuf `.proto`, and
  codec source.
- `release_tools`: contract hash, manifest builder, and manifest validator
  tools.
- `conformance_tools`: conformance validator tools.
- `claims`: example reference gateway and core producer claims.
- `release_policy`: this human-readable release hash policy.

Advisory audit documents, handoff notes, historical release notes, generated
reports, local caches, release zip assets, signatures, and checksums are not
included in the reference release bundle hash unless a future release explicitly
lists them as release artifacts.

Future companion artifacts under D-004 should use a companion manifest or an
explicit future release-manifest group. They should not be silently folded into
the semantic contract hash.

## Canonicalization Rules

Hashing uses SHA-256.

Text files are decoded as UTF-8, CRLF and CR line endings are normalized to LF,
and then the normalized UTF-8 bytes are hashed. This avoids Windows/CRLF
instability while keeping reviewed text content intact.

Binary files are hashed as raw bytes.

File hashes are `sha256` over canonicalized file bytes.

Group hashes are `sha256` over entries in lexicographic repo-relative path
order:

```text
relative/path
sha256:<file_hash>
```

with a trailing newline after each value.

`release_bundle_hash` is `sha256` over sorted group hash entries:

```text
group_name
sha256:<group_hash>
```

`release/zmeta-release-manifest.yaml` is excluded from `release_bundle_hash` to
avoid self-reference. `release_manifest_hash` is computed over canonical YAML
manifest content with `release_manifest_hash` set to `null`.

Volatile timestamps, local temp files, `.git`, caches, virtual environments,
build outputs, and generated release zip assets are excluded unless explicitly
listed by a release task.

## Manifest Build And Validation

Build the reference manifest with:

```bash
python tools/build_release_manifest.py --output release/zmeta-release-manifest.yaml
```

Validate it with:

```bash
python tools/validate_release_manifest.py --manifest release/zmeta-release-manifest.yaml
```

The builder writes a reference hardening-baseline manifest, not a formal tagged
release. It uses fixed release metadata by default, including stable
`git_commit` and `branch` placeholders, so rebuilding the committed reference
manifest after a checkpoint commit does not change the manifest only because
the repo head moved. Formal release generation must pass explicit
`--git-commit`, `--branch`, `--release-id`, and related metadata. The manifest
validator recomputes every file hash, group hash, `release_bundle_hash`, and
`release_manifest_hash`, and fails on missing artifacts or mismatches.

## Deployment And Gateway Gate Guidance

Existing gateway startup gates remain available:

- `require_schema_hash`
- `require_policy_hash`
- `require_contract_hash`

Those gates are not changed by this policy. They remain useful for current
runtime compatibility checks.

Release-aware deployments should validate the structured release manifest before
startup, then decide which category hashes must match the deployment profile.
Production deployments should at minimum verify semantic contract, schema, and
policy baselines. Stricter deployment wrappers may also require registry,
conformance class, profile projection, encoding-negative, profile precision, and
encoding projection hashes.

Failures should report the category, expected hash, actual hash, and affected
artifact path or group.

## Conformance Claims

Example claims record `contract_hash` as the narrow
`semantic_contract_hash`. They may also record category hashes that identify the
release baseline used by their evidence.

Example claims do not include `release_manifest_hash` as a required claim field
in the S1-09B reference baseline because claim files are themselves included in
the manifest. A formal tagged release may solve that circularity through
post-release attestations or by excluding claims from the release bundle hash.

Conformance claims do not prove a release by themselves. A valid claim requires
the required class commands to pass and must remain tied to the manifest,
commit, limitations, and release process used for that claim.

## Exclusions

The release hash system does not:

- change schemas;
- change validators or gateway behavior by default;
- make v1.1.0 concepts adopted;
- make reserved or proposed extension registry entries valid;
- create future conformance classes;
- make protobuf semantic authority;
- replace asset-level checksums or signatures.

Release asset checksums and signatures remain separate publisher and artifact
integrity controls. D-012 tracks formal tagged-release signature and
attestation packaging outside the S1-09 reference hardening-baseline manifest.
