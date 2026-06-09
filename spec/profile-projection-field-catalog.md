# Profile Projection Field Catalog

This document explains the Profile Projection Preservation conformance layer for
ZMeta v1.0. The machine-readable catalog is:

```text
conformance/profile_projection_field_catalog.yaml
```

The catalog classifies how fields may behave when a Profile H/M event is thinned
to Profile M/L, or when a lower-profile export is checked against a higher
fidelity source event.

## Projection Preservation

Profile thinning is projection, not reinterpretation. A same-event projection
may remove optional fields, reduce numeric precision, lower confidence, shorten
TTL, or omit non-exported parent events while preserving lineage references.

A projection must not change:

- `event.event_id`
- `event.ts`
- `event.event_type`
- `event.event_subtype`
- source-authored identity fields
- track identity
- lineage references
- units or coordinate semantics
- payload discriminator meaning
- semantic layer

If a transform changes meaning, authorship, track identity, semantic layer, or
source-authored truth, it is not a same-event profile projection. It must be a
new ZMeta event with its own `event.event_id` and appropriate lineage.

## Allowed Changes

The current v1.0 projection catalog permits these conservative changes when the
field rule allows them:

- Optional field omission.
- Numeric precision reduction.
- Confidence preservation or reduction.
- `payload.valid_for_ms` preservation or reduction.
- Gateway export metadata such as `event.t_receive` or `event.t_publish`.
- Omission of whole events that are illegal in the target profile, provided the
  fixture records an explicit omission reason instead of rewriting the event.

## Prohibited Changes

Projection conformance rejects clean-looking but semantically corrupted events,
including:

- Confidence increases.
- TTL increases.
- Precision increases or invented coordinates.
- Unit renames or silent rescaling.
- Source identity rewrites.
- Track ID rewrites.
- Event type or subtype rewrites.
- Lineage deletion.
- Raw observation fields inserted into `STATE_EVENT`.
- Command altitude-like fields.
- Hidden defaults that change event meaning.
- Profile-incompatible events emitted as if they were valid projections.

## Catalog Shape

Each catalog rule contains:

- `path`: dotted field path, optionally using `*`.
- `event_types`: event types the rule applies to, or `*`.
- `profiles`: target profiles the rule applies to.
- `status`: one or more projection classifications.
- `comparison`: how source and projected values are compared.
- `notes`: short rationale.

The catalog is a conformance aid. It does not replace JSON Schema and does not
add v1.0 event fields.

## Precision Policy Boundary

The projection catalog defines whether a field may be preserved, omitted,
lowered, shortened, or reduced in precision. It does not define profile-specific
precision ceilings, utility floors, quantization steps, or conservative rounding
directions.

Those rules live in the profile precision policy layer:

```text
spec/profile-precision-policy.md
policy/profile-precision.yaml
conformance/profile-precision/
```

Run the precision policy validator with:

```bash
python tools/validate_precision_policy.py --policy policy/profile-precision.yaml --must-pass conformance/profile-precision/must-pass.jsonl --must-fail conformance/profile-precision/must-fail.jsonl
```

Precision policy validation still depends on projection preservation: a
projection that violates identity, source, lineage, units, semantic layer,
confidence monotonicity, or TTL monotonicity cannot become valid merely because
its numeric rounding matches the policy.

## Fixture Pairs

Projection fixtures are wrappers, not ZMeta events. A fixture contains a source
event, a projected event or `null`, a target profile, and the expected result.

```json
{
  "name": "h-to-l-state-projection-pass",
  "description": "Profile L state projection preserves identity and lineage.",
  "source_profile": "H",
  "target_profile": "L",
  "source": { "zmeta_version": "1.0" },
  "projected": { "zmeta_version": "1.0" },
  "expect": "pass"
}
```

When an event type is illegal in the target profile, the fixture may use:

```json
{
  "projected": null,
  "allowed_omission_reason": "OBSERVATION_EVENT is not legal in Profile L"
}
```

That represents a legal export omission. It does not authorize rewriting an
observation or inference into state with the same `event_id`.

## Encoding Equivalence

Compact CBOR and protobuf are encoding projections only. A fixture may ask the
validator to round-trip a projected event through `compact` or `proto`; the
decoded JSON is then checked against schema, policy, and projection rules.

The decoded JSON remains authoritative. Raw compact or protobuf bytes are never
semantic authority.

## Not A Schema Change

This work intentionally leaves `schema/zmeta-event-1.0.schema.json` unchanged.
Projection preservation compares pairs of events and catches semantic drift that
single-event JSON Schema validation cannot see.

Future projection metadata remains a versioned candidate. It is not implemented
inside v1.0 events.

Policy-scoped external promotion evidence, such as
`payload.extensions.external_promotion` on a promoted external `STATE_EVENT`, is
not same-event profile projection metadata. It records why an external report or
lossy adapter projection was allowed to become a new ZMeta state event. It must
not be used to rewrite a source event while preserving `event.event_id`.
