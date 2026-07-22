# ZMeta Release Signing And Attestation

This document defines the formal release packaging framework for ZMeta
releases. It builds on the structured release manifest and hash policy without
changing ZMeta event semantics.

Release signatures and attestations do not create ZMeta semantics and do not
make future vocabulary valid.

No private keys, credentials, tokens, certificates, or signing secrets are
stored in this repository.

## Purpose

The release manifest identifies the governed ZMeta baseline. Formal release
packaging identifies the distributed package around that baseline: release
notes, checksums, optional detached signatures, attestation evidence, and
verification instructions.

Release packaging supports auditability, rollback, and consumer verification.
It does not alter schema validation, policy enforcement, extension registry
status, conformance classes, adapter behavior, gateway runtime behavior, or
encoding behavior.

## Relationship To The Release Manifest

`release/zmeta-release-manifest.yaml` remains the source of release baseline
hashes. It records:

- semantic contract hash;
- schema bundle hash;
- policy bundle hash;
- extension registry hash;
- conformance class manifest hash;
- projection, encoding-negative, precision, and encoding projection hashes;
- release bundle hash;
- release manifest hash.

Formal release packaging wraps that manifest. It may copy hashes from the
manifest into an attestation, but it must not recompute different semantics or
reinterpret the baseline.

## Relationship To Semantics And Schemas

The semantic contract is authoritative. Schemas, policies, registries,
conformance classes, adapters, encodings, and release packaging preserve or
reference the contract; they do not replace it.

Release packaging must not:

- change `spec/semantics-contract.md`;
- change JSON schemas;
- add event vocabulary;
- make reserved or proposed extension registry entries valid;
- promote experimental v1.1.0 concepts;
- change validator or gateway behavior by default.

## Release Package Contents

A formal release package should include:

- release notes;
- the structured release manifest;
- checksum file for package artifacts;
- attestation/provenance statement;
- optional detached signatures generated outside normal validation;
- verification instructions;
- any release assets selected by the release task.

The S1-12B tooling supports no-signature package construction and template
validation. Real signatures and tags require an explicit future release task.

## Release States

Recommended release states:

- `reference_hardening_baseline`: reproducible baseline, not a formal tag.
- `release_candidate`: candidate package prepared for final verification.
- `formal_release`: final signed/tagged release package.
- `superseded`: valid historically but replaced by a newer release.
- `revoked`: withdrawn because release integrity or authenticity failed.

## Tag Naming Guidance

Recommended tag patterns:

- `zmeta-v1.0.0-rc.1`
- `zmeta-v1.0.0`
- `zmeta-v1.1.0-exp.1`

Tags should point to clean commits and match explicit release manifest
metadata. S1-12B tooling must not create a real git tag.

## Checksums

Package checksums use SHA-256 over raw artifact bytes. Checksum files use this
format:

```text
<64 hex sha256>  <package-relative-path>
```

Checksums prove artifact integrity. They do not authenticate the release
authority unless the checksum file itself is verified through a trusted
signature or channel.

## Detached Signatures

The default packaging mode is no-signature. The release package may reference
expected detached signature artifact names, but normal validation does not
require GPG, cosign, minisign, or any signing tool.

Future formal release tasks may produce detached signatures over:

- the release manifest;
- the checksum file;
- selected release assets.

The signing identity and verification material must be published through an
approved release channel.

## Attestation Model

Release attestations should include:

- attestation version;
- release ID and state;
- git commit, tag, and branch;
- release manifest hash;
- release bundle hash;
- category hashes copied from the release manifest;
- commands run;
- test summary;
- build environment summary;
- signer identity placeholder;
- signature artifact references;
- known open issues;
- limitations and notes.

Attestation proves release process evidence. It does not prove event truth or
producer truth.

## Verification Workflow

Consumers should be able to:

1. Verify signature artifacts when a formal release includes them.
2. Verify SHA-256 checksums for package artifacts.
3. Validate the release manifest.
4. Validate release package metadata and attestation hashes.
5. Compare expected category hashes.
6. Run conformance checks when source and test dependencies are available.

## No-Secret Repository Policy

Release package tooling must reject obvious private-key or secret material in
package paths. Filename and content checks are conservative and are not a
substitute for organizational secret scanning, but they prevent accidental
release package contamination.

Private release keys, signing tokens, certificates with private material, CI
secrets, and credentials must remain outside this repository.

## Relationship To The Future-Branch Roadmap

`spec/future-branch-roadmap.yaml` is the machine-readable roadmap for future
versioned semantic branches; D-003 was closed once that artifact existed. A
signed release cannot make future branch candidates valid. Versioned semantic
adoption still requires schema, policy, adapter/gateway, encoding, conformance,
release, and audit coverage.

## Relationship To D-004

D-004 was removed from ZMeta scope. Release packaging must stay limited to the
ZMeta standard and governed release artifacts. It must not reintroduce
out-of-scope organizational artifact systems.

## D-012 Closure Path

- S1-12A planned formal release packaging.
- S1-12B implements package docs, templates, tooling, validation, and tests.
- S1-12C audits implementation behavior. D-012 should close only after the
  package framework is verified and no tags, real signatures, keys, or secrets
  are introduced accidentally.
