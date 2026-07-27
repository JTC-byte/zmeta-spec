# ZMeta Change Governance

Status: current-main process baseline.

This document defines how humans and AI agents should propose, implement,
validate, document, and publish changes to the ZMeta specification and reference
stack.

The goal is to keep ZMeta both strict and adaptable:

- strict where semantic truth, interoperability, safety, and auditability depend
  on stable meaning;
- adaptable through policy, profiles, adapters, extension governance, and
  release-pinned implementation baselines.

## Authority Stack

Use this order when resolving conflicts:

1. `spec/semantics-contract.md`
2. canonical schemas in `schema/`
3. policy YAML in `policy/`
4. machine-readable governance artifacts:
   - `spec/extension-registry.yaml`
   - `conformance/conformance_classes.yaml`
   - `conformance/profile_projection_field_catalog.yaml`
   - release manifest and package metadata
   - IP, contribution, conformance, trademark, and defensive-publication
     governance docs
5. validators and tests in `tools/` and `gateway/tests/`
6. README, examples, adapters, deployment docs, worklogs, and handoff notes

The semantic contract is the primary authority. Reference gateway, adapter, and
tool behavior must preserve it; they do not redefine it.

## Left And Right Limits

Humans and agents may:

- clarify docs without changing validation behavior;
- add conformance fixtures that enforce existing contract rules;
- add policy/config variants that stay within locked semantics;
- add adapter mappings that preserve event-family separation and lineage;
- add extension registry entries as reserved/proposed governance records;
- improve validators, tests, packaging, and release tooling when behavior is
  documented and validated.

Humans and agents must not, without explicit maintainer approval:

- make new event vocabulary valid;
- make v1.1.0 or future concepts valid under `zmeta_version: "1.0"`;
- weaken UUIDv7, timestamp, timing-quality, lineage, confidence, unit, geodesy,
  command-safety, or profile-projection invariants;
- move raw observation or evidence fields into `STATE_EVENT`;
- silently strip accepted-risk labels, use limits, or external-promotion
  evidence during profile projection;
- change release tags, published checksums, detached signatures, or uploaded
  release assets;
- commit secrets, private keys, signing material, credentials, generated cache
  directories, or local release smoke outputs.

When in doubt, preserve the kernel and add policy/config/adapter/registry
surface area rather than changing core semantics.

## IP, Conformance, And Industry Sharing

ZMeta is intended to remain an open, implementation-neutral specification and
reference stack. The repository's Apache License 2.0 baseline remains in
`LICENSE`; project-specific contributor authority, conformance, naming, and
public-sharing posture is documented in:

- `IP_POLICY.md`
- `CONTRIBUTING.md`
- `CONFORMANCE.md`
- `TRADEMARK.md`
- `docs/zmeta_defensive_publication.md`

These documents do not create legal advice, a trademark registration, a patent
opinion, or a standards-body patent commitment. They make the project posture
explicit so public feedback can happen through published material rather than
private disclosure of unpublished roadmap concepts.

For industry meetings and broader socialization:

- cite a public tag, release notes, validation report, release manifest hash,
  conformance evidence, and defensive-publication text;
- avoid privately disclosing unpublished future vocabulary, roadmap concepts,
  or deployment-specific mappings unless covered by an appropriate agreement;
- record substantive feedback as public issues or pull requests when possible;
- require contributor authority before accepting normative or governed changes.

## Downstream Clone And Integration Limits

ZMeta supports three common operating modes:

- **Upstream maintainers and collaborators** change this source-of-truth stack
  through branches, review, validation, documentation, and release governance.
- **Downstream clone users** consume a tagged release or current `main` locally
  to integrate ZMeta into their own systems.
- **Downstream forks** intentionally change ZMeta semantics, schemas, policy, or
  validation behavior for a separate ecosystem.

Downstream clone users may build local adapters, gateways, policy variants,
views, storage mappings, deployment configuration, and private notes around a
pinned ZMeta release. Those local integration files do not need upstream
changelog, worklog, handoff, or release-manifest updates unless the user is
proposing an upstream contribution or publishing a forked ZMeta baseline.

For ecosystem interoperability, downstream users should not redefine core
semantic surfaces in place. This includes event type/subtype vocabulary,
`zmeta_version` dispatch, required schema fields, unit/geodesy/timing rules,
lineage and confidence meaning, profile projection behavior, risk labels,
external-promotion evidence, producer authority, command safety, and
deconfliction semantics.

If a downstream clone changes those surfaces, it becomes a private dialect or
fork. That is allowed operationally, but it must not be represented as
upstream-compatible ZMeta unless it is versioned, documented, covered by
conformance evidence, and released through an equivalent governance process.
Prefer adapter mappings, deployment policy, profile selection, namespaced
extensions, or local application logic before changing the core contract.

## Change Classes

### Class A: Advisory Documentation

Examples:

- README wording
- installation or deployment notes
- explanatory docs
- local handoff/worklog updates

Requirements:

- update `CHANGELOG.md` when the change is user-visible;
- update `docs/zmeta_refinement_handoff.md` when future agents need the new
  context;
- run at least `git diff --check`;
- run focused tests only if docs include commands, paths, or validation claims.

### Class B: Governed Baseline

Examples:

- semantic contract
- schema files
- policy YAML
- extension registry
- conformance class manifest
- profile projection catalog
- conformance fixtures
- validators
- release manifest builder/validator
- example claim hashes

Requirements:

- update docs explaining the changed rule;
- update conformance fixtures and focused tests;
- regenerate `release/zmeta-release-manifest.yaml` when any manifest-listed
  artifact changes;
- update example claim hashes when the release manifest builder requires it;
- update `CHANGELOG.md`, worklog, and handoff;
- run full kernel conformance and relevant focused tests.

### Class C: Runtime Or Reference Implementation

Examples:

- gateway validation behavior
- adapter translation behavior
- compact/protobuf/CBOR codecs
- runtime tools
- risk filters

Requirements:

- prove the change with focused tests;
- update the relevant adapter/tool/gateway docs;
- ensure runtime behavior does not become semantic authority unless the
  contract, schema, policy, and conformance surfaces also change;
- run focused pytest plus full kernel conformance;
- run full pytest before handoff when feasible.

### Class D: Versioned Semantic Branch

Examples:

- new event type or subtype
- new required field
- profile model changes
- stable extension promotion
- breaking schema behavior

Requirements:

- start with a plan-only document;
- record the candidate in the extension registry as reserved/proposed before
  implementation;
- meet the promotion evidence bar in `spec/extension-registry.md` —
  independent demonstrated need from at least two implementations plus a
  documented semantic-contract Section 2.6 failure condition — before moving
  a candidate into a named version branch;
- identify version target and compatibility impact;
- update schema, policy, adapters/gateway, encoding, conformance, docs, release
  manifest, and claims together;
- keep future vocabulary invalid until the versioned branch is complete and
  approved;
- require human maintainer approval before release publication.

### Class E: Release Publication

Examples:

- release notes
- validation reports
- release zips
- release package
- checksums
- detached signatures
- tags
- GitHub release upload

Requirements:

- start from a clean intended worktree except approved release outputs;
- run the full release checklist;
- generate release manifest with explicit release metadata;
- build and validate source, edge, gateway, and release package artifacts;
- generate and verify `SHA256SUMS_<version>.txt`;
- attach signatures only through an approved release signing process;
- do not rewrite published release checksums for post-release current-main
  changes;
- tag and publish only when the release authority explicitly requests it.

## Documentation Matrix

Use this matrix for every change:

| Changed Surface | Required Documentation |
| --- | --- |
| Semantic contract | `spec/semantics-contract.md`, `CHANGELOG.md`, worklog, handoff |
| Schema | schema README, conformance fixtures, validation report when releasing |
| Policy YAML | `policy/README.md`, focused tests, risk/adjudication docs when relevant |
| Extension registry | `spec/extension-registry.md`, registry validator tests |
| Profile projection | `spec/profile-projection-field-catalog.md`, projection fixtures/tests |
| Conformance classes | `spec/conformance-classes.md`, claim files, class validator tests |
| Gateway/adapters | local README, focused tests, conformance evidence if semantics matter |
| Tools | `tools/README.md`, tests, release manifest if governed |
| Release process | `release/README.md`, `RELEASE_CHECKLIST.md`, release notes/report |
| Agent/process guidance | `AGENTS.md`, this document, release manifest governance group |
| IP/conformance/name-use posture | `IP_POLICY.md`, `CONTRIBUTING.md`, `CONFORMANCE.md`, `TRADEMARK.md`, `docs/zmeta_defensive_publication.md`, release manifest governance group |

`LOCAL_NOTES.md` may be used for private workspace memory, but durable state
belongs in tracked docs.

## Versioning Rules

Use `spec/versioning.md` as the source of truth.

- Patch: clarifications, fixes, docs, validator hardening that preserves
  existing valid payloads.
- Minor: backward-compatible extensions, new optional fields, experimental
  encoding projections, or version-scoped vocabulary.
- Major: required-field changes, removed fields, semantic reinterpretation, or
  compatibility-breaking validation changes.

Policy changes may alter enforcement posture without changing schema version,
but material policy behavior must be documented, tested, and release-hashed.

Profile projection or extension-registry changes usually do not bump
`zmeta_version` by themselves unless they make new event payload vocabulary
valid.

## Standard Workflows

### Pre-Change Orientation

Run:

```powershell
git status --short --branch
git log --oneline --decorate -n 10
```

Read:

- `AGENTS.md`
- this document
- `docs/zmeta_refinement_handoff.md`
- relevant `spec/`, `policy/`, `conformance/`, or `release/` docs

Do not overwrite unrelated user changes. If the worktree is dirty, work with
the existing changes or ask before changing overlapping files.

### Implementation

1. Identify the change class.
2. Update the narrowest required source files.
3. Add or update machine-checkable fixtures.
4. Add or update tests.
5. Update docs and changelog.
6. Regenerate release manifest and claim hashes if governed artifacts changed.
7. Run validation.
8. Update worklog and handoff with exact commands and results.

### Validation Gate

Minimum gate for governed changes:

```powershell
python tools\validate_release_manifest.py --manifest release\zmeta-release-manifest.yaml
python tools\validate_release_package.py --manifest release\zmeta-release-manifest.yaml --templates-only
python tools\validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative --precision-policy --release-manifest --release-package --bad-events --adapter-harness
python -m pytest -q
git diff --check
```

Run additional focused validators when touched:

```powershell
python tools\validate_projection.py --catalog conformance\profile_projection_field_catalog.yaml --must-pass conformance\profile-projection\must-pass.jsonl --must-fail conformance\profile-projection\must-fail.jsonl --quiet
python tools\validate_extension_registry.py --registry spec\extension-registry.yaml
python tools\validate_conformance_classes.py --manifest conformance\conformance_classes.yaml --claims conformance\claims\example-reference-gateway.yaml conformance\claims\example-core-producer.yaml
python tools\lint_policy_risk_modes.py
```

If a required validation cannot run, record why and whether the failure is
environmental, dependency-related, or a real defect.

### Manifest And Claims

When manifest-listed artifacts change, rebuild with explicit metadata for the
current release baseline:

```powershell
python tools\build_release_manifest.py --release-id zmeta-v1.1.17 --release-name "ZMeta v1.1.17" --release-status formal_release --release-date 2026-07-27 --branch main --update-claims
python tools\validate_release_manifest.py --manifest release\zmeta-release-manifest.yaml
```

For a new formal release, replace the metadata with the intended release ID,
date, commit, and branch.

Do not regenerate historical `SHA256SUMS_<version>.txt` unless performing an
explicit release publication or correction approved by the release authority.

## Release Publication Workflow

1. Confirm release scope and target version.
2. Confirm no unrelated worktree changes are included.
3. Run the validation gate.
4. Build release manifest with explicit release metadata.
5. Build source, edge, and gateway bundles.
6. Build formal release package metadata in no-signature mode.
7. Validate package output.
8. Generate and verify checksums.
9. Generate detached signatures only when an approved signing key/process is
   available.
10. Update release notes, validation report, changelog, worklog, and handoff.
11. Commit release artifacts selected for the repo.
12. Tag the release only after human approval.
13. Upload assets to GitHub Release only after human approval.
14. Confirm GitHub CI passes for the release commit/tag.

Post-release current-main changes must clearly say whether they modify only
current `main` or also require a new published release.

## Human And Agent Responsibilities

Humans decide:

- whether a semantic branch should exist;
- whether a change is acceptable policy for the project;
- release version numbers and publication timing;
- signing identity and release authority;
- whether to accept compatibility risk;
- whether a future/reserved concept becomes experimental or adopted.

Agents may:

- inspect and summarize repo state;
- implement scoped changes;
- add tests and conformance fixtures;
- update docs, changelog, worklog, handoff, and release manifest;
- run validators and tests;
- prepare release artifacts when explicitly asked.

Agents must stop or ask when:

- a requested change would redefine locked semantics;
- release publication, signing, tagging, or pushing is implied but not explicit;
- secrets or private signing material appear in scope;
- local changes from another actor overlap and cannot be safely merged;
- validation exposes a real semantic or compatibility failure outside the
  requested scope.

## Commit And Handoff Standard

Each commit or handoff should state:

- change class;
- affected surfaces;
- semantic/schema/policy/runtime/release impact;
- validation commands and results;
- whether public release assets changed;
- any open risk, skipped check, or future work.

Keep commit scope narrow. Do not bundle unrelated refactors, generated caches,
or old local release smoke output with governed changes.
