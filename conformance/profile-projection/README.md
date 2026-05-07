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
