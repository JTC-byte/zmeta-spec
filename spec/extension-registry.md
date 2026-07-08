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
- Strip vendor, edge, or risk-relevant extension labels during profile
  projection so degraded data appears cleaner than it is.

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

## Projection And Risk Fields

Every registry entry declares how it behaves under profile projection:

`not_applicable`
: The entry does not define payload content whose projection behavior needs a
  registry rule.

`preserve`
: If present, the field or concept must be preserved exactly across profile
  projection.

`preserve_or_compact`
: The field or concept may be compacted for lower profiles, but policy-relevant
  labels, handles, or decision codes must remain present and equivalent.

`optional_omission`
: The entry may be omitted during projection when omission does not change
  event meaning or hide material risk.

`prohibited`
: The entry must not appear in the governed profile or event context.

`future_branch_required`
: Projection behavior is intentionally undecided until an approved version
  branch defines schema, policy, and conformance fixtures.

Entries also declare:

- `risk_relevant`: whether the concept can affect trust, safety, privacy,
  display, fusion, routing, command basis, autonomy, export, TTL, confidence, or
  other operational policy decisions.
- `must_preserve_when_used_for_policy`: whether consumers must preserve the
  field whenever policy uses it. Such entries cannot be marked
  `ignorable_by_default`.
- `security_privacy_notes`: security, privacy, or misuse considerations.
- `fixture_references`: positive or negative conformance fixtures that exercise
  implemented behavior.

Risk-relevant implemented entries must include security/privacy notes and
fixture references. Risk-relevant entries must not use `optional_omission` or
`not_applicable` projection behavior.

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
- Profile projection behavior.
- Risk relevance and preservation requirements.
- Security/privacy notes.
- Fixture references for implemented behavior.
- Conformance class impact.
- Migration guidance.
- Release/security review where applicable.
- Documentation.
- Test command coverage.

If a surface is not applicable, the record must say so explicitly. Missing
coverage is not equivalent to `not_applicable`.

## Promotion Evidence Requirements

Adoption Requirements above define the surface completeness a record needs.
Status promotion also requires field evidence. A concept does not enter a
named version branch because its record is tidy; it enters because fielded
reality demonstrated the need.

To move from `reserved` or `proposed` to `experimental` in a named version
branch, the record must document both of the following in its rationale,
notes, or referenced evidence:

1. **Independent demonstrated need.** At least two independent
   implementations or deployments — not derived from the same codebase,
   vendor, or organization — demonstrating the same need. A single
   deployment's need is served in place by namespaced extensions, policy,
   profiles, adapter mappings, or advisory binding guidance; the registry
   entry holds the name so later promotion stays collision-safe.
2. **A concrete failure condition.** At least one documented failure
   condition from `spec/semantics-contract.md` Section 2.6 (Core Semantic
   Change Threshold) — divergent interpretation between compliant
   implementations, silent meaning laundering, degraded data masquerading as
   clean state, unauditable command basis, or projection hiding material
   degradation — that policy, configuration, profiles, adapter mappings, and
   namespaced extensions cannot solve.

External contributions are treated as field telemetry: harvest the
requirement, re-derive the solution from the locked kernel outward, and do
not merge dialect surfaces. Declined concepts receive a `rejected` entry with
rationale so the decision is durable and is not re-litigated.

Meeting the evidence bar is necessary, not sufficient. Promotion still
requires an approved version branch, the full adoption surface list above,
and an explicit maintainer adoption decision.

Candidate-level evidence, dependencies, and promotion tripwires are tracked
in the machine-readable future-branch roadmap
(`spec/future-branch-roadmap.yaml`, governed by
`spec/future-branch-roadmap.md`).

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
