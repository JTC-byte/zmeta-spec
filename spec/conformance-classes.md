# ZMeta Conformance Classes

ZMeta conformance classes describe which already-defined ZMeta surfaces an
implementation satisfies. They make implementation claims precise and
repeatable, so a producer, gateway, adapter, encoding tool, or reference stack
does not need to rely on vague statements such as "ZMeta compliant."

Conformance classes do not create semantics. They state which already-defined
semantic, schema, policy, adapter, gateway, encoding, and conformance surfaces an
implementation satisfies.

## Authority

The semantic contract remains authoritative. Conformance classes organize
evidence against the contract; they do not replace `spec/semantics-contract.md`,
schemas, policy packs, gateway behavior, adapter rules, encoding guidance,
extension registry decisions, examples, or conformance fixtures.

A conformance class cannot make future vocabulary valid. Future or reserved
semantic concepts must first be adopted through an approved version branch and
the associated schema, policy, adapter/gateway, encoding, documentation, and
conformance coverage.

v1.0 remains locked and normative. v1.1.0 remains experimental unless promoted
by a separate version/release decision.

## Machine-Readable Manifest

The machine-readable manifest is:

```text
conformance/conformance_classes.yaml
```

Validate the manifest with:

```bash
python tools/validate_conformance_classes.py --manifest conformance/conformance_classes.yaml
```

Validate the example implementation claims with:

```bash
python tools/validate_conformance_classes.py --manifest conformance/conformance_classes.yaml --claims conformance/claims/example-reference-gateway.yaml conformance/claims/example-core-producer.yaml
```

The conformance runner can invoke class validation explicitly:

```bash
python tools/validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes
```

Default strict conformance does not run class validation unless
`--conformance-classes` is present.

## Why Classes Exist

Schema validation is necessary but not sufficient. ZMeta also depends on
version dispatch, policy checks, profile legality, projection preservation,
adapter layer separation, encoding decoded validation, and governed extension
adoption. Class claims keep those surfaces separate and auditable.

Without class claims:

- schema-only support can be mistaken for full semantic support;
- profile support can be claimed without projection preservation;
- compact or protobuf support can be claimed without decoded JSON validation;
- adapter support can be claimed without layer-separation tests;
- future concepts can be claimed before registry and version approval;
- vendors can claim compliance without evidence, commands, versions, hashes, or
  limitations.

## Class Status Definitions

`implemented`
: The current repo provides enough manifest, fixtures, commands, and tests to
  support the class.

`partially_implemented`
: Some surfaces exist, but the class is not yet complete enough for a full
  claim. A claim may only record partial support when evidence is explicit.

`planned`
: The implementation path is known, but the class is not claimable.

`reserved`
: The class name is held for future governance and is not claimable.

`future`
: The class depends on future vocabulary, a future version branch, or companion
  artifacts and is not claimable by current implementations.

`deprecated`
: The class was previously claimable but is discouraged or superseded.

Classes with status `future`, `reserved`, or `planned` cannot be claimed by
current implementation claim files.

## Claim Model

A claim records the implementation, versions, claimed classes, class-level
evidence, commands run, results, schema and policy versions, registry/catalog
versions, commit hash, contract hash state, owner, limitations, and exceptions.

A conformance claim is not valid unless the required tests for the claimed class
pass.

Claims must include dependency closure directly. For example, a claim for
`ZMETA-PROJECTION-PRESERVATION` must also claim `ZMETA-PROFILE-L`,
`ZMETA-PROFILE-M`, and `ZMETA-PROFILE-H`, plus their dependencies.

Because D-002 remains open, claim files may record `contract_hash:
pending_D-002`. Release-grade claims should replace that placeholder with the
approved contract/release hash set.

## Dependency Model

Dependencies are machine-readable in `conformance/conformance_classes.yaml`.
Examples:

- `ZMETA-V1-0-SCHEMA` depends on `ZMETA-CORE`.
- `ZMETA-POLICY-BASELINE` depends on `ZMETA-CORE` and
  `ZMETA-V1-0-SCHEMA`.
- `ZMETA-PROJECTION-PRESERVATION` depends on the three profile classes and the
  projection fixture suite.
- `ZMETA-COMPACT-CBOR` depends on Profile L and decoded canonical JSON
  validation.
- `ZMETA-PROTOBUF-PROJECTION` depends on core semantics and decoded canonical
  JSON validation.
- `ZMETA-EXTENSION-REGISTRY` depends on the registry artifacts, validator, and
  schema leakage tests.

The class validator rejects unknown dependencies and dependency cycles.

## Relationship To The Extension Registry

The extension registry governs vocabulary lifecycle. The conformance class
manifest governs implementation claims and evidence.

A registry entry may be reserved, proposed, or experimental before a class is
claimable. A class cannot make registry-reserved vocabulary valid. Future
classes may depend on registry entries, but those classes cannot become
claimable until the registry status, version branch, schemas, policy,
adapter/gateway behavior, encoding guidance, documentation, and tests support
the claim.

## Evidence Requirements

Each class record identifies:

- relevant contract sections;
- schema, policy, gateway, adapter, and encoding surfaces;
- fixture files;
- required test commands;
- dependencies and exclusions;
- allowed claimant implementation types;
- evidence fields required in claim files;
- current repo support;
- registry dependencies where applicable.

The required commands in the manifest are the evidence contract for a class. A
claim file must record those commands as passed for every claimed class.

## Initial Class Families

Current baseline classes cover core semantics, version dispatch, v1.0 schema,
v1.1.0 experimental support, policy, command governance, timing quality,
lineage, Profile L/M/H, projection preservation, extension registry validation,
compact CBOR, protobuf projection, and the reference gateway.

`ZMETA-COT-PROJECTION` is recorded as partially implemented because current CoT
tests cover key ingress/egress behavior, but the repo does not yet provide a
shared adapter conformance harness.

Future and reserved classes cover generic adapters, sensor adapters, AI
provenance, coalition export, mesh trust, replay, UAS identity, PNT integrity,
data nutrition, compute elasticity, emergency/L0, cross-domain export, and
vendor extensions. Those classes are not claimable today.

## Future Work

S1-04C should audit the manifest, validator, claim examples, documentation, and
test coverage. Later work can decide whether implemented classes should be
promoted to externally active certification classes, whether claims need
captured test-output artifacts, and how release hashes from D-002 should be
recorded.
