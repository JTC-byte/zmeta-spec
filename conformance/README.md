# Conformance Pack

> **`--conformance-classes` is a repository-side check, not a bundle-side one.**
> `conformance_classes.yaml` cites maintainer process records under `docs/` as
> its evidence entries — that is what conformance-class evidence *is*, a link
> back to the audit that established the class. Release bundles deliberately
> ship the governance documents but not the process-record archive, so running
> `validate_conformance.py --conformance-classes` from inside an unpacked
> bundle reports `CONFORMANCE_PATH_MISSING` for those references. That is
> expected and is not a defect in the bundle or in the corpus.
>
> **From an edge or gateway bundle, every other flag passes** — measured, all
> ten: `--strict`, `--profile-projection`, `--extension-registry`,
> `--encoding-negative`, `--precision-policy`, `--release-manifest`,
> `--release-package`, `--bad-events`, `--adapter-harness` exit 0;
> `--conformance-classes` is the only one that does not.
>
> **From the dist bundle, `validate_conformance.py` does not run at all.** It
> imports the reference gateway at module load and dist carries no `gateway/`.
> dist is the specification distribution; its `BUNDLE_NOTES.md` says so and
> lists the affected tools, generated from the tools themselves. `tools/validate_release_manifest.py` does run
> there, and verifies the hash manifest dist ships.

This folder contains a regression corpus for the canonical
version-discriminated schema plus policy pack:

- `must-pass.jsonl`: events that must validate against schema + policy.
- `must-fail.jsonl`: events that must fail with the specified `expect_code`.
- `profile_projection_field_catalog.yaml`: sidecar field catalog for profile
  projection preservation checks.
- `profile-projection/`: source/projected fixture pairs that prove H/M/L
  thinning preserves event meaning.
- `conformance_classes.yaml`: machine-readable conformance class manifest.
- `claims/`: example implementation claim files for the class manifest.
- `encoding-negative/`: compact/protobuf invalid-after-decode fixture suites.
- `bad-events/`: semantic bad-event fixtures for dishonest or unsafe events
  that must not be treated as clean data.
- `adapter-harness/`: fixture-driven adapter output checks for schema/policy
  validity, layer separation, UTC-Z timestamps, lineage, and external promotion.
- `profile-precision/`: source/projected fixtures for Profile L/M/H precision
  ceilings, utility floors, and conservative quantization.
- `../spec/extension-registry.yaml`: spec-owned machine-readable extension
  registry consumed by optional registry validation.
- `../policy/profile-precision.yaml`: reference conformance default precision
  policy for profile/export validation.
- `../release/zmeta-release-manifest.yaml`: reference hardening-baseline release
  manifest for governed artifact hashes.
- `../release/RELEASE_NOTES_TEMPLATE.md`,
  `../release/ATTESTATION_TEMPLATE.yaml`, and
  `../release/RELEASE_PACKAGE_README.md`: formal release package templates.

The conformance pack protects the ZMeta kernel; it is not an exhaustive mission
ontology or a promise that every sensor, platform, adapter variant, policy, or
edge case has been certified. Mission-specific behavior belongs in policy
packs, deployment configuration, adapters, profiles, extension branches,
operator views, or mission plugins unless it exposes a concrete semantic
ambiguity, implementation failure, or safety/audit gap.

Use:

```
python tools/validate_conformance.py --strict
```

The core fixtures include external promotion checks: schema-valid CoT/JREAP/
MAVLink-style `STATE_EVENT`s from marked external ingress producers must carry
valid `payload.extensions.external_promotion` evidence or fail producer
authority as `PRODUCER_NOT_ALLOWED` under the default reference `reject` mode.
Deployments may tune local enforcement to `warn`, `degrade`, or `quarantine`,
but those modes must preserve diagnostics and visible trust/TTL effects rather
than silently accepting incomplete promotion evidence.

Risk-adjudication fixtures prove that soft acceptance remains filterable. A
warning/degraded diagnostic may pass when it carries `risk_dimension`,
`policy_mode`, `policy_decision`, governed `reason_code`, use limits, and any
applied effects. This lets deployments accept degraded data under edge
conditions while consumers can still reject, warn, quarantine, or filter by
explicit labels.

Consumer-side risk filtering is available through:

```
python tools/filter_risk.py --input gateway-output.jsonl --preset display
python tools/filter_risk.py --input gateway-output.jsonl --preset command --fail-on-drop
```

The filter consumes existing labels only. It does not alter source events,
policy decisions, schemas, or semantic validity.

Policy risk-mode linting is available through:

```
python tools/lint_policy_risk_modes.py
```

The lint flags material timing, lineage, external-promotion, command, trust, or
safety checks configured to `ignore`. The only reference-policy ignore exception
is Profile L unresolved parent lineage, where profile thinning may intentionally
leave parent events unavailable on the link.

Profile projection preservation is opt-in for the conformance runner:

```
python tools/validate_conformance.py --strict --profile-projection
```

It can also be run directly:

```
python tools/validate_projection.py --catalog conformance/profile_projection_field_catalog.yaml --must-pass conformance/profile-projection/must-pass.jsonl --must-fail conformance/profile-projection/must-fail.jsonl
```

Extension registry validation is also opt-in:

```
python tools/validate_extension_registry.py --registry spec/extension-registry.yaml
python tools/validate_conformance.py --strict --extension-registry
python tools/validate_conformance.py --strict --profile-projection --extension-registry
```

The registry does not make reserved or proposed concepts valid event
vocabulary. v1.1.0 registry entries remain experimental until explicitly
promoted by a later version/release decision.

Conformance class validation is opt-in:

```
python tools/validate_conformance_classes.py --manifest conformance/conformance_classes.yaml
python tools/validate_conformance_classes.py --manifest conformance/conformance_classes.yaml --claims conformance/claims/example-reference-gateway.yaml conformance/claims/example-core-producer.yaml
python tools/validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes
```

Class records and claim files do not make future vocabulary valid. They state
which existing semantic, schema, policy, adapter, gateway, encoding, and
conformance surfaces an implementation satisfies. Future, reserved, and planned
classes are `FUTURE_EXTENSION` material and are not claimable by current
implementation claim files.

Encoding-negative validation is opt-in:

```
python tools/validate_encoding_negative.py --compact conformance/encoding-negative/compact-must-fail.jsonl --protobuf conformance/encoding-negative/protobuf-must-fail.jsonl --gateway conformance/encoding-negative/gateway-must-fail.jsonl
python tools/validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative
```

Compact CBOR and protobuf remain encoding projections only. The negative suite
decodes wire inputs to canonical JSON and then proves invalid decoded events fail
schema, policy, projection, gateway/CLI, or conversion-plus-validation checks.
It does not change schemas and does not make new vocabulary valid.

Profile precision policy validation is opt-in:

```
python tools/validate_precision_policy.py --policy policy/profile-precision.yaml --must-pass conformance/profile-precision/must-pass.jsonl --must-fail conformance/profile-precision/must-fail.jsonl
python tools/validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative --precision-policy
```

Precision policy is profile/export policy, not JSON Schema, release policy,
trust policy, emergency mode, UI policy, or transport semantics. The reference
defaults in `policy/profile-precision.yaml` are `reference_conformance_default`
values with `requires_mission_review: true`. They prove conservative
quantization behavior without making new event vocabulary valid.

Release manifest validation is opt-in:

```
python tools/build_release_manifest.py --output release/zmeta-release-manifest.yaml
python tools/validate_release_manifest.py --manifest release/zmeta-release-manifest.yaml
python tools/validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative --precision-policy --release-manifest
```

Example claims use `contract_hash` for the narrow semantic contract hash and
record broader release category hashes under `release_hashes`. They omit
`release_manifest_hash` in S1-09B because the reference manifest includes the
claim files; a formal tagged release may publish post-release attestations if it
needs claim-level manifest hashes.

Release package validation is opt-in and template-only by default:

```
python tools/build_release_package.py --manifest release/zmeta-release-manifest.yaml --output-dir release/package --dry-run --no-signatures
python tools/validate_release_package.py --manifest release/zmeta-release-manifest.yaml --templates-only
python tools/validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative --precision-policy --release-manifest --release-package
```

The release package framework does not create tags, generate signatures, store
keys or secrets, change validation behavior, or make future vocabulary valid.

Semantic bad-event validation is opt-in:

```
python tools/validate_bad_events.py --must-fail conformance/bad-events/must-fail.jsonl
python tools/validate_conformance.py --strict --bad-events
```

The bad-event corpus is intentionally small and high-signal. It proves that
layer collapse, missing promotion evidence, loop/reflection risk, bad
diagnostics, payload lineage overreach, and missing timing quality are rejected
or explicitly surfaced with the expected governed code.

Adapter harness validation is opt-in:

```
python tools/validate_adapter_conformance.py --fixtures conformance/adapter-harness/must-pass.jsonl
python tools/validate_conformance.py --strict --adapter-harness
```

The adapter harness validates representative adapter outputs without forcing a
single adapter API. Fixtures call adapter functions, then check canonical
schema/policy validity, layer separation, UTC-Z timestamps, adapter lineage,
fallback degraded timing declarations, and external-promotion evidence for
lossy/external state projections.

Full kernel-protection conformance runs every current optional guard:

```
python tools/validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative --precision-policy --release-manifest --release-package --bad-events --adapter-harness
```

This is the recommended pre-release and CI-grade stack check. It proves the
reference stack preserves the locked kernel, keeps future/reserved/planned
concepts non-claimable, validates encodings after decode, protects profile
projection, and checks representative adapter and semantic bad-event evidence.
