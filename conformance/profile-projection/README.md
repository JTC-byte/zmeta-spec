# Profile Projection Fixtures

This directory contains source/projected fixture pairs for Profile Projection
Preservation conformance.

Run:

```bash
python tools/validate_projection.py --catalog conformance/profile_projection_field_catalog.yaml --must-pass conformance/profile-projection/must-pass.jsonl --must-fail conformance/profile-projection/must-fail.jsonl
```

Each JSONL line is a wrapper, not a ZMeta event:

```json
{
  "name": "h-to-l-state-projection-pass",
  "description": "Profile L projection preserves identity, source, track, and lineage.",
  "source_profile": "H",
  "target_profile": "L",
  "source": {},
  "projected": {},
  "expect": "pass"
}
```

Fields:

- `name`: stable case identifier.
- `description`: human-readable purpose.
- `source_profile`: profile used to validate the source event.
- `target_profile`: profile used to validate the projected event.
- `source`: higher-fidelity ZMeta event.
- `projected`: lower-profile ZMeta event, or `null` for legal export omission.
- `expect`: `pass` or `fail`.
- `expect_code`: required for `must-fail.jsonl`.
- `context`: optional inline ZMeta events, such as `TIME_STATUS`.
- `roundtrip`: optional list containing `compact` or `proto`; the validator
  encodes and decodes `projected`, then validates the decoded JSON.
- `allowed_omission_reason`: required when `projected` is `null`.

If an event type is illegal in the target profile, the fixture must use
`"projected": null` with an explicit omission reason, or a separately authored
event with a new `event_id` outside same-event projection preservation.
Projection fixtures must not rewrite an observation or inference into state with
the same `event_id`.

Compact CBOR and protobuf are encoding projections only. The decoded JSON is
the authoritative validation input.

## Failure Codes

Projection validator failure codes are stable strings so fixtures and tests can
assert exact reasons:

- `PROJECTION_EVENT_ID_CHANGED`
- `PROJECTION_VERSION_CHANGED`
- `PROJECTION_EVENT_TS_CHANGED`
- `PROJECTION_EVENT_TYPE_CHANGED`
- `PROJECTION_EVENT_SUBTYPE_CHANGED`
- `PROJECTION_SOURCE_CHANGED`
- `PROJECTION_SOURCE_REWRITTEN`
- `PROJECTION_TRACK_ID_CHANGED`
- `PROJECTION_LINEAGE_REMOVED`
- `PROJECTION_LINEAGE_CHANGED`
- `PROJECTION_TRANSFORM_REMOVED`
- `PROJECTION_CONFIDENCE_INCREASE`
- `PROJECTION_TTL_INCREASE`
- `PROJECTION_PRECISION_INCREASE`
- `PROJECTION_UNIT_CHANGED`
- `PROJECTION_REQUIRED_FIELD_REMOVED`
- `PROJECTION_PROHIBITED_FIELD_ADDED`
- `PROJECTION_SEMANTIC_LAYER_COLLAPSE`
- `PROJECTION_PROFILE_ILLEGAL_EVENT`
- `PROJECTION_UNDECLARED_OPTIONAL_OMISSION`
- `PROJECTION_ENCODING_DECODE_INVALID`
- `PROJECTION_SCHEMA_INVALID_SOURCE`
- `PROJECTION_SCHEMA_INVALID_PROJECTED`
- `PROJECTION_POLICY_INVALID_SOURCE`
- `PROJECTION_POLICY_INVALID_PROJECTED`
- `PROJECTION_FIELD_CHANGED`

`PROJECTION_FIELD_CHANGED` is a fallback for catalog equality drift where no
more specific invariant code applies. Specific identity, source, lineage,
confidence, TTL, precision, unit, profile, schema, policy, and encoding checks
run separately and retain their specific codes.
