# ZMeta Profile Precision Policy

Status: Reference conformance default

This document defines how Profile H/M/L exports may reduce numeric precision
without changing ZMeta meaning. Precision policy is a profile/export policy
layer. It is not a schema change, not a transport semantic, not a release
policy, not a trust policy, not an emergency mode, and not UI policy.

Precision policy does not create semantics. It constrains how already-valid
ZMeta events may be conservatively projected into lower-fidelity profiles.

If a precision change would alter meaning, change units, remove required
lineage, hide uncertainty, or make an event operationally misleading, the event
must not be exported as a same-event profile projection.

## Authority

`spec/semantics-contract.md` remains authoritative. Profiles thin exported data;
they do not reinterpret it. Same-event profile projection remains governed by
the projection preservation rules in `spec/profile-projection-field-catalog.md`
and `conformance/profile_projection_field_catalog.yaml`.

The machine-readable reference policy is:

```text
policy/profile-precision.yaml
```

Validate the policy and fixtures with:

```bash
python tools/validate_precision_policy.py --policy policy/profile-precision.yaml --must-pass conformance/profile-precision/must-pass.jsonl --must-fail conformance/profile-precision/must-fail.jsonl
```

The conformance runner can invoke this explicitly:

```bash
python tools/validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative --precision-policy
```

Default strict conformance does not run precision-policy validation unless
`--precision-policy` is present.

## Reference Defaults

The YAML policy values are `reference_conformance_default` values and require
mission review. They exist to make precision behavior testable and repeatable in
the reference stack. They are not final operational values for every deployment.

Mission-specific overrides may later select different grid sizes, field
ceilings, utility floors, or rejection behavior. Overrides must remain
conservative: they cannot increase confidence, TTL, precision, or implied
certainty; they cannot change units or identity; and they cannot hide degraded
quality.

## Immutable Paths

Precision policy never quantizes or rewrites source-authored identity,
authority, lineage, event time, semantic-layer, or discriminator paths. These
paths are preserved exactly:

- `zmeta_version`
- `event.event_id`
- `event.event_type`
- `event.event_subtype`
- `event.ts`
- `source.platform_id`
- `source.node_role`
- `source.producer`
- `lineage.based_on`
- `lineage.transform`
- `payload.track_id`
- `payload.modality`
- `payload.inference_type`
- `payload.task_type`
- `payload.system_type`

Changing any of these fields is either a projection failure or a new ZMeta event
with new identity and lineage. It is not precision reduction.

## Conservative Rounding

Field-specific direction matters:

- Confidence may be preserved or rounded down, never increased.
- `payload.valid_for_ms` may be preserved or shortened, never increased.
- Error bounds and timing uncertainty are rounded up, never down.
- Units remain unchanged. `_m`, `_mps`, `_hz`, `_dbm`, `_deg`, and `_ms` fields
  keep their source units.
- Geospatial values use deterministic coarse representation. Quantization must
  not imply more accuracy than the source.
- RF values preserve measurement meaning and cannot be moved outside the
  allowed policy tolerance.
- Required fields are never removed for packet-size reasons.

## Utility Floors

Precision ceilings limit maximum detail. Utility floors prevent over-thinning.

Profile L STATE_EVENT projections must remain operationally useful: source,
event identity, track identity, confidence, TTL, timing exposure, lineage, and
position semantics stay intact. If geo precision falls below the reference
utility floor and the source was precise enough to meet it, the projection is
rejected.

COMMAND_EVENT target geometry uses a stricter utility floor than display state.
If command target precision cannot satisfy the command floor, the event should
be rejected or omitted rather than exported as a misleading same-event
projection.

When the source itself is less precise than the reference utility floor, the
projected event must not invent precision. A fixture or policy context must
explicitly acknowledge source-limited precision.

## Packet Budget

Packet-size pressure cannot strip required semantic fields. Exporters should:

1. Validate the source event.
2. Select the target profile.
3. Omit only cataloged optional fields.
4. Apply conservative precision policy.
5. Revalidate projection preservation and precision policy.
6. Measure packet size.
7. Reject or omit the event if the packet budget still cannot be met without
   corrupting required semantics.

Compact CBOR and protobuf may consume precision-policy output, but they do not
define precision policy. Encodings remain wire projections that decode to
canonical JSON before validation.

## Gateway And Exporter Guidance

Gateways and exporters should apply precision policy only during an explicit
export step. The source event in the event store remains immutable. A projection
that preserves event identity can only make allowed, conservative changes. Any
change to meaning, layer, units, source, lineage, track identity, or command
safety requires a new event and appropriate lineage.

S1-06B implements conformance validation, policy artifacts, and fixtures. It
does not change gateway runtime export behavior and does not add schema fields.
