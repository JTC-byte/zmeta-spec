# Specification

Normative specification and supporting guidance.

Key documents:
- `semantics-contract.md` canonical semantic contract (normative)
- `versioning.md` versioning and compatibility policy
- `extension-registry.md` human-readable extension registry governance
- `extension-registry.yaml` machine-readable extension registry
- `conformance-classes.md` human-readable conformance class and claim model
- `release-hash-policy.md` contract/release hash taxonomy and manifest policy
- `profile-compatibility.md` profile compatibility matrix and producer allowlists
- `profile-projection-field-catalog.md` profile projection preservation catalog guide
- `profile-precision-policy.md` profile precision and quantization policy guide
- `field-dictionary.md` UI-focused field dictionary
- `quickstart.md` runnable reference workflow (if present)
- `installation-guide.md` packaging and deterministic install guidance
- `compact-binary-mapping.md` optional compact CBOR mapping for Profile L links
- `protobuf-encoding.md` experimental protobuf transport projection

Validate the extension registry explicitly:

```bash
python tools/validate_extension_registry.py --registry spec/extension-registry.yaml
```

The registry does not make reserved or proposed concepts valid event
vocabulary. Future concepts require versioned adoption with schema, policy,
adapter/gateway, encoding, documentation, and conformance coverage.

Validate the conformance class manifest explicitly:

```bash
python tools/validate_conformance_classes.py --manifest conformance/conformance_classes.yaml
python tools/validate_conformance_classes.py --manifest conformance/conformance_classes.yaml --claims conformance/claims/example-reference-gateway.yaml conformance/claims/example-core-producer.yaml
```

Conformance classes do not create semantics or make future vocabulary valid.
They organize claims about already-defined semantic, schema, policy, adapter,
gateway, encoding, and conformance surfaces. v1.1.0 remains experimental unless
a later release decision promotes it.

Validate the reference profile precision policy explicitly:

```bash
python tools/validate_precision_policy.py --policy policy/profile-precision.yaml --must-pass conformance/profile-precision/must-pass.jsonl --must-fail conformance/profile-precision/must-fail.jsonl
```

Profile precision policy constrains conservative Profile L/M/H export
projection. It is not a schema change, release policy, trust policy, emergency
mode, UI policy, or transport semantic. The reference defaults require mission
review, and compact/protobuf encodings remain wire projections that must decode
to canonical JSON before validation.

Build and validate the reference release manifest explicitly:

```bash
python tools/build_release_manifest.py --output release/zmeta-release-manifest.yaml
python tools/validate_release_manifest.py --manifest release/zmeta-release-manifest.yaml
python tools/validate_conformance.py --strict --release-manifest
```

`contract_hash` remains narrow in the release claim model: it identifies the
semantic contract baseline. The release manifest records broader schema,
policy, registry, conformance, projection, encoding-negative, precision-policy,
encoding projection, tool, and claim hashes without making those implementation
surfaces semantic authority.
