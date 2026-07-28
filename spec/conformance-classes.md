# ZMeta Conformance Classes

ZMeta conformance classes describe which already-defined ZMeta surfaces an
implementation satisfies. They make implementation claims precise and
repeatable, so a producer, gateway, adapter, encoding tool, or reference stack
does not need to rely on vague statements such as "ZMeta compliant."

Conformance classes do not create semantics. They state which already-defined
semantic, schema, policy, adapter, gateway, encoding, and conformance surfaces an
implementation satisfies.

They also preserve the core contract's completeness-without-exhaustiveness
boundary. A class can prove support for a defined ZMeta surface, but it cannot
turn mission-specific behavior into core semantics or certify every possible
sensor, platform, adapter variant, policy, workflow, operator role, or edge
case.

## Authority

The semantic contract remains authoritative. Conformance classes organize
evidence against the contract; they do not replace `spec/semantics-contract.md`,
schemas, policy packs, gateway behavior, adapter rules, encoding guidance,
extension registry decisions, examples, or conformance fixtures.

A conformance class cannot make future vocabulary valid. Future or reserved
semantic concepts are `FUTURE_EXTENSION` material until adopted through an
approved version branch and the associated schema, policy, adapter/gateway,
encoding, documentation, and conformance coverage.

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
adapter layer separation, encoding decoded validation, governed extension
adoption, and semantic bad-event rejection. Class claims keep those surfaces
separate and auditable.

Without class claims:

- schema-only support can be mistaken for full semantic support;
- profile support can be claimed without projection preservation;
- compact or protobuf support can be claimed without decoded JSON validation;
- adapter support can be claimed without shared harness evidence;
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
: The class depends on future vocabulary or a future version branch and is not
  claimable by current implementations.

`deprecated`
: The class was previously claimable but is discouraged or superseded.

Classes with status `future`, `reserved`, or `planned` cannot be claimed by
current implementation claim files.

## Claim Model

A claim records the implementation, versions, claimed classes, class-level
evidence, commands run, results, schema and policy versions, registry/catalog
versions, commit hash, contract hash state, owner, limitations, and exceptions.

A conformance claim is not valid unless the required tests for the claimed class
pass. That validity condition is an attestation model: the claimant attests
that the required commands ran and passed. The claims validator
(`tools/validate_conformance_classes.py`) checks claim structure, class
claimability, and the required-command strings recorded for each claimed
class, and, with `--verify-contract-hash`, the recorded contract hash
against the release manifest. It does not execute the tests itself.
Captured test-output artifacts and execution-verified claims are Future Work
(see below).

Claims must include dependency closure directly. For example, a claim for
`ZMETA-PROJECTION-PRESERVATION` must also claim `ZMETA-PROFILE-L`,
`ZMETA-PROFILE-M`, and `ZMETA-PROFILE-H`, plus their dependencies.

S1-09B claim files record `contract_hash` as the narrow
`semantic_contract_hash` from `release/zmeta-release-manifest.yaml`. Broader
release evidence belongs in category hashes and the release manifest, not in an
overloaded contract hash. Example claims do not require `release_manifest_hash`
because the claim files are themselves included in the reference manifest and a
formal tagged release may handle that circularity through post-release
attestations.

## Dependency Model

Dependencies are machine-readable in `conformance/conformance_classes.yaml`.
Examples:

- `ZMETA-V1-0-SCHEMA` depends on `ZMETA-CORE`.
- `ZMETA-POLICY-BASELINE` depends on `ZMETA-CORE` and
  `ZMETA-V1-0-SCHEMA`.
- `ZMETA-PROJECTION-PRESERVATION` depends on the three profile classes and the
  projection fixture suite, now with profile precision policy evidence for
  conservative export behavior.
- `ZMETA-COMPACT-CBOR` depends on Profile L and decoded canonical JSON
  validation, including encoding-negative invalid-after-decode fixtures.
- `ZMETA-PROTOBUF-PROJECTION` depends on core semantics and decoded canonical
  JSON validation, including encoding-negative invalid-after-decode fixtures.
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

This keeps future-extension work visible without letting it blur into current
interoperability claims.

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

Profile L/M/H and projection preservation claims include the profile precision
policy validator where relevant. That evidence proves conservative rounding,
utility-floor, immutable-field, and packet-budget guardrails for same-event
profile exports. The policy values are reference conformance defaults that
require mission review; they do not change schemas or create event vocabulary.

## Initial Class Families

Current baseline classes cover core semantics, version dispatch, v1.0 schema,
v1.1.0 experimental support, policy, command governance, timing quality,
lineage, risk adjudication, external projection promotion, risk filtering,
Profile L/M/H, projection preservation, extension registry validation, compact
CBOR, protobuf projection, generic adapter conformance, CoT projection, and the
reference gateway.

These classes protect the ZMeta kernel. They are not a mission ontology and do
not require the core contract to enumerate every deployment-specific workflow.

Risk-governance classes do not loosen schemas. They prove that tunable policy
responses remain bounded, labeled, diagnostic, and filterable, and that external
tactical-track ingress cannot become authoritative ZMeta state without explicit
promotion evidence.

`ZMETA-ADAPTER` is fixture-driven. It validates representative adapter outputs
for schema/policy validity, layer separation, UTC-Z time normalization, adapter
lineage transforms, declared degraded timing, and external-promotion evidence.
It is not a promise that every possible native message variant for every
adapter has been exhaustively covered.

Future and reserved classes cover broader sensor-adapter certification, AI
provenance, coalition export, mesh trust, replay, UAS identity, PNT integrity,
data nutrition, compute elasticity, emergency/L0, cross-domain export, and
vendor extensions. Those classes are not claimable today.

## Future Work

Later work can decide whether implemented classes should be promoted to
externally active certification classes, whether claims need captured
test-output artifacts, and whether formal tagged releases should publish
post-release claim attestations that include `release_manifest_hash`.
