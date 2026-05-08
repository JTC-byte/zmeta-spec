# ZMeta Extension Registry

The ZMeta extension registry is the durable governance surface for future
semantic vocabulary. It records names, status, ownership, version branches,
collision rules, implementation surfaces, and conformance expectations before
future concepts become operational vocabulary.

The registry supports ZMeta evolution without weakening the locked v1.0
semantic foundation. It is a planning and governance artifact, not a shortcut
around versioned adoption.

## Authority

The semantic contract remains authoritative. The registry indexes current
experimental extensions and future candidates, but it does not replace
`spec/semantics-contract.md`, JSON Schema, policy packs, gateway behavior,
encoding guidance, examples, or conformance tests.

Required rule:

> The registry does not make a concept valid. Validity requires an approved
> version branch and the associated schema, policy, adapter/gateway, encoding,
> documentation, and conformance coverage.

Reserved or proposed registry entries are not valid event vocabulary.
Producers must not emit them as current ZMeta vocabulary, and consumers must not
treat them as schema-valid semantics just because they appear in the registry.

v1.1.0 concepts remain experimental unless explicitly promoted by a later
release or adoption decision.

## Why A Registry Exists

Prose-only reservation is not enough once future extension work starts landing.
Without a registry, implementation work can accidentally:

- Reuse a reserved name.
- Add future vocabulary to v1.0.
- Blur v1.1.0 experimental vocabulary with adopted vocabulary.
- Let vendor extensions redefine core semantics.
- Add fields without schema, policy, gateway, encoding, or conformance coverage.
- Hide required meaning in ignorable-looking payload extensions.
- Treat examples or adapters as semantic authority.

The registry keeps future work branch-scoped and testable.

## Machine-Readable Registry

The machine-readable registry is:

```text
spec/extension-registry.yaml
```

Validate it with:

```bash
python tools/validate_extension_registry.py --registry spec/extension-registry.yaml
```

The conformance runner can invoke registry validation explicitly:

```bash
python tools/validate_conformance.py --strict --extension-registry
```

Default strict conformance does not run registry validation unless the
`--extension-registry` flag is present.

## Status Definitions

`reserved`
: Name held for future consideration. It is not valid event vocabulary.

`proposed`
: Concept has an initial rationale and review path. It is not valid event
  vocabulary.

`experimental`
: Valid only in the named version branch where current schemas, policy, and
  conformance already support it. Current v1.1.0 entries use this status.

`adopted`
: Valid in a named version branch and covered by the required implementation
  surfaces.

`deprecated`
: Previously valid but discouraged for new producers. Migration guidance is
  required.

`rejected`
: Reviewed and explicitly rejected. Producers must not emit it as valid
  vocabulary.

`superseded`
: Replaced by another registry entry. The replacement must be named.

## Category Definitions

The current category set is:

- `observation_modality`
- `observation_feature_contract`
- `inference_type`
- `fusion_extension`
- `state_extension`
- `command_task_type`
- `system_status_type`
- `profile_export_control`
- `trust_integrity`
- `coalition_release`
- `ai_model_provenance`
- `pnt_integrity`
- `replay_test`
- `adapter_vendor_namespace`
- `encoding_projection`
- `conformance_class`
- `track_lifecycle`
- `data_evidence`
- `operator_display`

Categories describe the semantic area governed by the record. They do not make
the record valid vocabulary.

## Collision And Namespace Rules

Extension records must obey these rules:

- No extension may collide with v1.0 names.
- No extension may collide with v1.1.0 names unless it is the same registered
  concept in the same version lineage.
- Vendor/private extensions must use a namespaced key such as
  `vendor.<owner>.<name>` or another approved prefix.
- Vendor/private extensions must be safe to ignore unless a versioned subtype
  contract makes them required.
- No extension may alter the ZMeta envelope.
- No extension may collapse observation, inference, fusion, state, command, or
  system layers.
- No extension may redefine units, geodesy, timing, lineage, confidence,
  profile behavior, event identity, or authority boundaries.
- No extension may become valid without schema, policy, and conformance review
  when it changes structure or runtime behavior.

Free-form payload and `extensions` objects remain compatibility surfaces. They
are not a path to unregistered core-looking semantics.

## Adoption Requirements

An extension cannot move to `adopted` until the record identifies:

- Semantic definition.
- Approved version branch.
- Schema shape if structural.
- Policy rules if contextual.
- Adapter/gateway requirements.
- Encoding notes if wire behavior changes.
- Positive fixtures.
- Negative fixtures.
- Conformance class impact.
- Migration guidance.
- Release/security review where applicable.
- Documentation.
- Test command coverage.

If a surface is not applicable, the record must say so explicitly. Missing
coverage is not equivalent to `not_applicable`.

## How Future Prompts Should Use The Registry

Future schema, policy, adapter, gateway, encoding, and conformance prompts
should:

1. Check `spec/extension-registry.yaml` before introducing vocabulary.
2. Add or update registry entries before implementation when a name is new.
3. Keep `reserved` and `proposed` entries invalid.
4. Move an entry to `experimental` only when a named version branch supports it.
5. Move an entry to `adopted` only after all required adoption surfaces exist.
6. Add positive and negative conformance tests for every structural extension.
7. Update encoding notes when compact, CBOR, protobuf, or another wire mapping
   changes.

The registry should be validated in CI or release checks with the explicit
registry validator command.
