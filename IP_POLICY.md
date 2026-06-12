# ZMeta IP And Open Specification Policy

Status: current-main advisory governance.

This document records the ZMeta project's open specification intent and
contributor hygiene expectations. It is not legal advice, a patent opinion, a
trademark registration, or a standards-body patent policy. Before major
industry publication, formal standardization, trademark filing, contributor
license agreement adoption, or any patent covenant, consult qualified counsel.

## Intent

ZMeta is intended to remain an open, implementation-neutral specification and
reference stack for resilient ISR metadata interoperability.

The project goal is broad interoperable implementation, not vendor capture.
Reference code, schemas, tools, examples, and documentation are licensed under
Apache License 2.0 unless a file says otherwise. The project uses release
manifests, conformance fixtures, and public governance records to make the
open baseline citable and auditable.

## Apache 2.0 Baseline

Apache 2.0 remains the project license baseline. It provides permissive
copyright rights and an express contributor patent grant for covered
contributions. It also says that intentionally submitted contributions are
licensed under Apache 2.0 unless the contributor explicitly states otherwise.

Apache 2.0 does not by itself create a full standards-body patent commitment
for every independent implementation of the specification, bind people who
never contribute to the repository, or grant trademark rights beyond ordinary
descriptive use. ZMeta therefore uses separate governance, contribution,
conformance, and trademark guidance to reduce ambiguity around industry
sharing.

## Contributor Authority

Contributors must submit only material they have authority to contribute.

Do not submit:

- confidential or restricted information;
- employer-owned or customer-owned material without authority;
- export-controlled material;
- third-party proprietary schemas, mappings, captures, or field dictionaries;
- NDA-only meeting notes or unpublished roadmaps from another organization;
- private keys, credentials, tokens, certificates with private material, or
  signing secrets.

If a discussion item should not become a project contribution, mark it
conspicuously as `Not a Contribution` before sharing it with maintainers.

## Specification Contributions

Normative or governed surfaces need extra review because they can affect
interoperability and public claims. This includes:

- `spec/semantics-contract.md`;
- schemas and version dispatch;
- policy YAML and risk semantics;
- compact/protobuf/encoding projections;
- conformance classes and fixtures;
- extension registry entries;
- release manifests, claims, checksums, signatures, and attestation material;
- producer authority, command safety, lineage, timing, confidence, profile
  projection, and accepted-risk semantics.

Contributors proposing those changes must follow `AGENTS.md`,
`CONTRIBUTING.md`, and `docs/zmeta_change_governance.md`.

## Public Feedback And Industry Sharing

For industry conversations, meetings, and larger feedback circles:

- share public repository links, tagged releases, release notes, and published
  defensive-publication material;
- prefer citing a specific tag, manifest hash, and conformance baseline;
- avoid privately disclosing unpublished roadmap concepts, future vocabulary,
  or proprietary deployment mappings before they are published or covered by
  an appropriate agreement;
- record material feedback as public issues or pull requests when possible;
- treat private meeting feedback as advisory until the contributor authority
  and contribution status are clear.

The safest public posture is to discuss ZMeta through already-published release
material and the defensive publication. That gives reviewers useful context
without handing out unpublished extension concepts in private channels.

## Defensive Publication

`docs/zmeta_defensive_publication.md` describes the public ZMeta architecture
in patent-searchable technical language. It is intended to make the open
baseline easier to cite as public prior art and to reduce ambiguity about the
project's open architecture intent.

The defensive publication does not replace legal review, a patent search, a
patent filing decision, or formal standards adoption.

## Conformance And Naming

Apache 2.0 permits broad implementation and commercialization of the licensed
work. It does not create a right to make false claims that a private dialect is
upstream ZMeta.

Use `CONFORMANCE.md` and `TRADEMARK.md` to distinguish:

- ZMeta-conformant implementation;
- ZMeta-compatible implementation;
- ZMeta-derived work;
- private dialect or fork;
- experimental extension.

Claims of compatibility or conformance should cite a tagged release, manifest
hashes, schema/policy baseline, and validation evidence.
