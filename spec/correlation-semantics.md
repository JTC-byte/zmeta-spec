# Correlation semantics — `event.correlation`

**Status:** Proposed for v1.2.0. Backward-compatible additive field.

## Purpose

When multiple sensors observe the same real-world entity (a single vessel
seen by AIS *and* radar *and* an EO camera), receivers need a way to
identify those observations as being about the same thing without each
adopter inventing a private convention.

`event.correlation` is the envelope-level slot for that identity. A
fusion engine assigns a stable `correlation_id` to the entity; every
contributing sensor then carries it on subsequent observations of that
entity.

## Field reference

The `event.correlation` object is **optional**. When absent, the event
has not yet been correlated (or correlation is not applicable). All
fields inside the object are optional except as noted.

| Field | Type | Required | Description |
|---|---|---|---|
| `correlation_id` | string | yes (within the object) | Stable identifier for the real-world entity. Assigned by the fusion engine; persists across sensor handoffs. |
| `primary_alias` | `{scheme, value}` | no | Most-specific known identifier (e.g., MMSI preferred over ICAO24 preferred over an internal track id). |
| `aliases` | array of `{scheme, value}` | no | All known aliases across schemes. |
| `confidence` | float in [0,1] | no | Fusion engine's confidence in the correlation. |
| `fusion_revision` | integer ≥ 0 | no | Bumps every time the set of bonded contributors changes. Allows consumers to detect re-bondings without comparing full alias lists. |

## Relationship to existing v1.1 surfaces

`event.correlation` is **not lineage**. v1.1's lineage tracks the
provenance chain of a single event through pipeline transforms.
`event.correlation` is the cross-sensor identity for the *entity* being
observed, independent of any single event's pipeline history.

`event.correlation` is **not a producer-authority assertion**. The
correlation_id says "these observations are about the same thing." It
does not assert authority over the entity. Producer authority remains
in the v1.1 fields (`source.platform_id`, `extensions.external_promotion`,
etc.).

## Wire encoding

In `zmeta_json` and `zmeta_cbor`, the field rides as a nested object at
`event.correlation`.

In `zmeta_proto`, `event.correlation.correlation_id` is **lifted to a
top-level scalar (`ZmetaEvent.correlation_id`, field 8)** so brokers and
gateways can filter by fused identity without unmarshalling
`payload_json`. The full `event.correlation` object (with aliases and
revision) is recovered by JSON-parsing `payload_json`. See
`spec/protobuf-encoding.md` for details.

## Lifecycle pattern

A typical fusion pipeline:

1. Sensor publishes raw observation with no `event.correlation` set.
   The fusion engine consumes it and either bonds it to an existing
   `correlation_id` or mints a new one.
2. Fusion engine publishes a `bond_assigned` INFERENCE_EVENT subtype
   (see `docs/v1.2-event-types-conventions.md`) on a per-sensor topic
   telling the sensor its local track was bonded.
3. Sensor updates its in-memory `local_track_id → correlation_id` map
   and includes `event.correlation` on every subsequent observation
   for that local_track_id.
4. If fusion later splits the bond (realizes the entity was actually
   two distinct things), it publishes `bond_dissolved` carrying both
   the dissolved bonds and the replacement bonds in a single event
   (atomic-split semantics).

## Compatibility with v1.1

A v1.1 sender produces messages with no `event.correlation` field.
A v1.2 receiver treats those as un-correlated and processes them
otherwise unchanged.

A v1.2 sender producing `event.correlation` on a message routed through
a v1.1-only consumer: the consumer sees an unknown field at
`event.correlation` and (per `additionalProperties: true` in v1.1's
event object) ignores it. No validation failure.

For the proto encoding specifically, a v1.1 receiver decoding a v1.2
proto message: field 8 (`correlation_id`) is treated as an unknown
field by proto3 and silently dropped. The v1.2 event is still recovered
from `payload_json`.

## Example

See `examples/zmeta-v1.2-examples.jsonl`, line 1
(`observation-with-correlation`).
