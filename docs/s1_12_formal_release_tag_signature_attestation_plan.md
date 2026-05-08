# S1-12A - Formal Release Tag / Signature / Attestation Plan

Date: 2026-05-07

## Summary

This plan defines the D-012 formal release packaging path for ZMeta. It does
not create tags, generate signatures, add keys, change schemas, change
validators, change gateway runtime behavior, change policy behavior, or make
future vocabulary valid.

The semantic contract remains authoritative. Release signatures and
attestations are governance artifacts. They authenticate and document a named
release package; they do not create event semantics or approve future
vocabulary.

## A. Current Release Packaging Landscape

The current stack already has several release-governance surfaces:

- `spec/release-hash-policy.md` defines the narrow semantic contract hash,
  broader release manifest hash model, canonicalization rules, and deployment
  gate guidance.
- `release/zmeta-release-manifest.yaml` is the reproducible reference
  hardening-baseline manifest. It records category hashes, artifact hashes,
  `release_bundle_hash`, and `release_manifest_hash`.
- `tools/build_release_manifest.py` builds the reference manifest and supports
  explicit release metadata for formal releases.
- `tools/validate_release_manifest.py` validates manifest shape, artifact
  existence, file hashes, group hashes, bundle hash, and self hash.
- `tools/compute_contract_hash.py` remains gateway-compatible and prints
  schema, policy, semantic, and combined contract hashes for existing runtime
  gates.
- `release/build_release_bundle.py` and `release/build_mvp_packages.py` build
  existing distribution zips.
- `release/sign_release_artifacts.py` generates and verifies `SHA256SUMS` and
  detached PGP signatures for historical release assets.
- `release/README.md` and `RELEASE_CHECKLIST.md` already document checksum and
  detached signature steps for release assets.
- Example conformance claims record the narrow semantic `contract_hash` and
  release category hashes while omitting `release_manifest_hash` to avoid
  claim/manifest circularity.

D-012 remains open because those pieces do not yet define a single formal
release procedure that ties tags, the structured release manifest, checksums,
signatures, attestation, clean-checkout verification, and evidence retention
together.

## B. Problem Statement

The S1-09 reference manifest is necessary but not sufficient for formal
distribution. It proves the governed artifact baseline, but it does not prove
that a named release was tagged, packaged, signed, verified, and retained under
a deliberate release process.

Risks to address:

- unsigned or partially signed release assets;
- release manifests distributed without signature verification;
- stale checksum files after asset rebuilds;
- unclear distinction between a reference baseline and a formal release;
- release candidates built from local or uncommitted files;
- key handling mistakes;
- signatures being misread as semantic approval for experimental or reserved
  vocabulary.

Formal packaging must close those release-authenticity gaps without changing
the ZMeta semantic model.

## C. Release Artifact Model

A formal ZMeta release package should contain or reference:

- a clean release commit;
- a release tag;
- `release/zmeta-release-manifest.yaml` generated with explicit release
  metadata;
- `release_manifest_hash`;
- `release_bundle_hash`;
- `SHA256SUMS_<version>.txt` or a successor checksum file;
- detached signature over the checksum file;
- detached signature over the release manifest;
- release notes;
- validation or test result summary;
- conformance command summary;
- provenance/attestation statement;
- optional source archive hash;
- optional distribution zip hashes;
- optional container or image digest references if future packaging includes
  images.

The release manifest remains the governed ZMeta artifact baseline. The checksum
file covers distributed assets. Signatures authenticate the manifest and
checksum file. Attestation documents the release process evidence.

## D. Release State Model

Recommended release states:

- `reference_hardening_baseline`: reproducible baseline for the hardened stack;
  may be validated and used for development gates, but is not a formal tagged
  release.
- `release_candidate`: clean candidate package prepared for final verification;
  may be tagged with an RC tag and signed if maintainers want candidate
  distribution.
- `formal_release`: final named release with clean commit, final manifest,
  checksums, signatures, notes, validation evidence, and verification
  instructions.
- `superseded`: still valid historically, but replaced by a newer release.
- `revoked`: withdrawn because a release integrity, authenticity, or baseline
  error was discovered.

Deployment gates may accept `reference_hardening_baseline` for development and
test environments. Operational release gates should prefer `formal_release`
once D-012 is implemented and audited.

## E. Tagging Strategy

Recommended tag names:

- `zmeta-v1.0.0-rc.1`
- `zmeta-v1.0.0`
- `zmeta-v1.1.0-exp.1`

Rules:

- Tags should point only to clean commits.
- Release candidate tags should be clearly marked and may be superseded by a
  later candidate or final release.
- Final release tags should match the release manifest metadata and release
  notes.
- v1.0 release tags must not adopt v1.1.0 experimental vocabulary unless a
  future release decision explicitly changes the version baseline.
- v1.1.0 remains experimental unless a future versioned branch decision and
  release process promote it.
- S1-12A creates no tags.

## F. Signing Strategy

Candidate approaches:

- GPG-signed tags and detached signatures over artifacts.
- Minisign-style detached signatures over release artifacts.
- Sigstore/cosign keyless or key-backed signatures.
- Organization-managed signing service.
- Offline release signing ceremony.

The conservative S1-12B default should be:

- detached signatures over the structured release manifest;
- detached signatures over the checksum file;
- no private keys in the repository;
- signer identity and verification material documented out of band;
- verification commands documented with the release package.

The existing `release/sign_release_artifacts.py` already supports detached PGP
signature workflows for release assets. S1-12B should either extend that
pattern to the structured release manifest or add a small package-level wrapper
around it. It should not require a final signing tool decision if maintainers
want to keep GPG and Sigstore options open.

## G. Attestation / Provenance Model

A release attestation should record:

- release ID;
- release state;
- git commit;
- branch;
- tag name;
- release manifest path;
- `release_manifest_hash`;
- `release_bundle_hash`;
- `semantic_contract_hash`;
- `schema_bundle_hash`;
- `policy_bundle_hash`;
- `extension_registry_hash`;
- `conformance_class_manifest_hash`;
- projection, encoding-negative, precision-policy, and encoding projection
  hashes;
- commands run;
- test result summary;
- build environment summary;
- signer identity placeholder;
- known limitations;
- known open issues, including D-003 while it remains roadmap-planned and D-012
  until release packaging is audited.

Attestation proves release process evidence. It does not prove event truth,
sensor truth, producer behavior, or future vocabulary validity.

## H. Key Management and Secret Handling

Rules:

- No private keys in the repository.
- No credentials, tokens, certificates with private material, or signing
  secrets in the repository.
- No test private keys committed unless they are clearly fake fixtures and the
  tests prove they cannot be mistaken for release authority.
- Signing keys are controlled by the release authority, not by the schema or
  validator code.
- Verification keys or identities must be published through an approved stable
  channel.
- Key rotation and revocation must be documented before formal release use.
- CI secrets must not be printed, logged, or committed.
- Local developer signatures are not official release signatures unless the
  release authority explicitly designates them.

## I. Formal Release Workflow

Future S1-12B workflow:

1. Start from a clean working tree.
2. Confirm the release commit and intended version.
3. Run the full conformance and pytest suite.
4. Build the release manifest with explicit release metadata.
5. Validate the release manifest.
6. Build distribution assets, if any are part of the release.
7. Generate the checksum file.
8. Generate release notes.
9. Generate the attestation/provenance statement.
10. Sign the release manifest and checksum file.
11. Optionally create a signed git tag.
12. Verify signatures, checksums, and manifest hashes from a clean checkout.
13. Preserve release evidence and update worklog/handoff.

The workflow should fail if the working tree is dirty, required artifacts are
missing, the manifest does not validate, checksums are stale, signatures do not
verify, or expected tests fail.

## J. Verification Workflow

A release consumer should be able to:

1. Obtain release notes, release manifest, checksum file, signatures, and
   release assets from the published release channel.
2. Verify the signature over the checksum file.
3. Verify the signature over the release manifest.
4. Verify SHA-256 checksums for release assets.
5. Run `python tools/validate_release_manifest.py --manifest
   release/zmeta-release-manifest.yaml` from a source checkout.
6. Compare expected semantic, schema, policy, registry, conformance, projection,
   precision, encoding, and release hashes.
7. Run conformance validation where source and test dependencies are available.

Verification should be explicit. Default strict conformance should not silently
become a release package verifier.

## K. Tooling Plan for S1-12B

Likely future files:

- `spec/release-signing-attestation.md`
- `release/RELEASE_NOTES_TEMPLATE.md`
- `release/ATTESTATION_TEMPLATE.yaml`
- `tools/build_release_package.py`
- `tools/validate_release_package.py`
- `gateway/tests/test_release_package.py`
- optional focused updates to `tools/build_release_manifest.py`
- optional focused updates to `tools/validate_release_manifest.py`
- optional focused updates to `release/sign_release_artifacts.py`
- optional docs updates in `spec/README.md` and `conformance/README.md`
- worklog and handoff updates

S1-12B should prefer wrapper tooling over changing existing manifest semantics.
The structured release manifest should remain the source of governed baseline
hashes; package tooling should add release-state, checksum, signature, and
attestation validation around it.

## L. Test Strategy for S1-12B

Planned tests:

- release package builder dry-run succeeds without signing keys;
- checksum generation is deterministic;
- missing release artifact fails;
- tampered artifact fails checksum verification;
- tampered manifest fails manifest hash validation;
- bad or missing signature fails package validation, using mocked or fixture
  signatures without real secrets;
- release package validation works from a temporary clean-checkout-style tree;
- no private key or secret material is committed;
- release manifest validation still passes;
- default strict conformance remains unchanged;
- full conformance and pytest suites pass.

Tests should not require real signing keys or network access.

## M. Relationship to D-003

D-003 tracks future versioned semantic branches. Signing a release does not make
future concepts valid. Any future branch must still pass through semantic,
schema, policy, adapter/gateway, encoding, conformance, release/hash, and audit
gates before becoming valid in a named version.

The v1.1.0 branch remains experimental unless a future release decision changes
that status.

## N. Relationship to D-004

D-004 was removed from ZMeta scope by S1-10P. Formal release packaging must not
reintroduce broad external organizational artifacts. Release evidence stays
limited to the ZMeta standard, its governed implementation surfaces, release
assets, and verification material.

## O. D-012 Closure Strategy

- S1-12A: plan only; D-012 remains open.
- S1-12B: implement formal release package specification, templates, builder,
  validator, tests, and docs; mark D-012 implemented pending audit.
- S1-12C: audit reproducibility, signatures, checksum behavior, attestation
  content, clean-checkout verification, no-secret checks, docs, and tests. Close
  D-012 only if release packaging is verified end to end.

## P. Risks and Open Questions

- Final signing tool choice remains open: GPG, minisign, Sigstore/cosign, or a
  managed release signing service.
- Whether final release tags must be GPG-signed remains open.
- Whether signing runs manually, in CI, or through an offline ceremony remains
  open.
- Signing authority and key rotation ownership must be assigned before formal
  release use.
- Public verification material publication path remains open.
- Private or restricted releases may require a separate release channel and
  verification workflow.
- Formal release packaging can be implemented now, but actual signatures and
  final tags should wait for a real release candidate decision.
