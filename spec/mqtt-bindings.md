# MQTT bindings — transport conventions for ZMeta on pub/sub brokers

**Status:** Proposed for v1.2.0. **Advisory, not normative.** Adopters
running ZMeta over a different transport (raw UDP, gRPC, Kafka) can
ignore this entire document.

## Purpose

The ZMeta envelope is transport-agnostic. When ZMeta is carried over
MQTT (the most common pub/sub broker in tactical / ISR deployments),
adopters consistently re-invent four conventions: topic shape,
retain/tombstone semantics, snapshot vs delta semantics, and subtype
naming. This document codifies what production deployments have
converged on, so the next adopter doesn't have to.

None of the recommendations here change the envelope schema, dispatch
rules, or any normative spec text. They are transport-binding
conventions.

## Topic shape

Recommended topic shape:

```
<event_type_root>/<event_subtype>/<id>
```

Where:

- `<event_type_root>` is the **lowercased `event_type` with the trailing
  `_EVENT` removed**:

  | `event_type` | `event_type_root` |
  |---|---|
  | `OBSERVATION_EVENT` | `observation` |
  | `INFERENCE_EVENT` | `inference` |
  | `FUSION_EVENT` | `fusion` |
  | `STATE_EVENT` | `state` |
  | `COMMAND_EVENT` | `command` |
  | `SYSTEM_EVENT` | `system` |

- `<event_subtype>` is the value of `event.event_subtype` verbatim
  (snake_case lowercase recommended; see "Subtype naming guidance"
  below).

- `<id>` is whatever identifier the publisher wants subscribers to wildcard
  over. Common choices: the entity id (asset, sensor, track), the
  correlation_id once correlated, or a synthetic per-source id.

### Examples

```
observation/ais_track/366998310
observation/eo_detection/eo-track-77
inference/bond_assigned/tactical-cop.fusion-engine
inference/classification/fused-1d4e7b2a
fusion/multi_source_track/fused-1d4e7b2a
state/asset/havoc-boat-12
state/lora_nodedb/node2
command/asset_task/havoc-boat-12
system/heartbeat/autonomy-engine
```

### Why this shape

1. **Predictable from the envelope alone.** A subscriber that knows
   `(event_type, event_subtype, id)` can compute the topic without
   consulting a registry.
2. **Wildcard-friendly.** `observation/+/+` matches all observations;
   `+/asset/<id>` matches all events about a specific asset;
   `state/+/<aor-id>` matches every state event scoped to one AOR.
3. **Avoids the 'event_id in topic' antipattern.** Topic identifiers
   should index entities (long-lived) not events (one-shot). Using
   `event_id` would explode the retained-topic count and prevent
   meaningful tombstoning.

## Retain semantics

ZMeta does not prescribe retain behavior. The recommended convention
on MQTT:

| Event type root | Retain? | Rationale |
|---|---|---|
| `state/` | **YES** | Late subscribers need current state on subscribe. |
| `inference/` | usually | Inferences with TTL or replacement semantics — retain. |
| `fusion/` | usually | Fused tracks are state-like for downstream consumers. |
| `observation/` | usually NOT | Observations are momentary; retain would create stale data. |
| `command/` | usually NOT | Commands are one-shot. |
| `system/heartbeat/` | YES with short keepalive | Subscribers detect liveness on subscribe. |

Snapshot events (`event.payload_cardinality == "snapshot"`) SHOULD always
be retained. Their semantics depend on it.

## Tombstone semantics

When an entity is decommissioned (asset destroyed, sensor unplugged,
service shut down cleanly), the publisher SHOULD emit an **empty
retained payload** on the same topic:

```
mosquitto_pub -h <broker> -t 'state/asset/havoc-boat-12' -r -n
```

This:

1. Removes the entity from the broker's retained-message store, so
   subsequent subscribers don't see a stale state.
2. Allows the entity store on each consumer to recognize "this thing
   went away" and remove the corresponding entity from displays,
   indexes, and downstream computations.

**Consumers MUST honor this convention.** Subscribers receiving a
zero-byte payload on a topic under `state/+/+`, `fusion/+/+`,
`inference/+/+` (where retained) interpret it as a removal directive.

## Snapshot semantics on MQTT

`event.payload_cardinality == "snapshot"` defines wholesale replacement
of the prior snapshot at the same retained-slot key. On MQTT:

- The publisher SHOULD use `retain=true`.
- Consumers replace their entire local view of that key — no merge,
  no delta.
- Snapshot publishers SHOULD also emit a tombstone (empty retained
  payload) on shutdown if there's any possibility a stale snapshot
  would otherwise stick around.

## Subtype naming guidance

Five conventions for assigning `event.event_subtype` values, derived
from production deployments:

1. **Use snake_case, lowercase.** `ais_track`, not `AISTrack` or
   `ais-track`.

2. **Be domain-specific.** `ais_track` not just `track`. The subtype
   tells the receiver what to do with the payload.

3. **Match the verb to the event_type.**

   - OBSERVATION subtypes describe what was observed: `ais_track`,
     `eo_detection`, `rf_spectrum_sweep`.
   - STATE subtypes describe what the entity is: `asset`,
     `comms_node`, `task_definition`.
   - COMMAND subtypes are imperatives: `asset_task`, `transport_control`,
     `send_text`.
   - INFERENCE subtypes describe the inference: `classification`,
     `bond_assigned`, `geofence_alert`.

4. **For snapshots, suffix with the singular's plural noun.**
   `lora_nodedb` (the LoRa node database), `ingestor_fleet`,
   `stream_routing`. Makes it obvious from the name that
   `payload.entries[]` is present.

5. **Avoid embedding versions in the subtype string.** Schema evolution
   belongs in `event.payload_schema_uri` (see `spec/payload-typing.md`),
   not in the subtype.

A seed catalog of common subtypes from production deployments is in
`spec/subtype-registry-seed.md`.

## Reserved / legacy paths to avoid

Several early ZMeta deployments published on non-ZMeta-shaped topics
(`tracks/`, `sensors/`, `commands/` — note the trailing 's', `tasks/`,
`assets/`, `comms/`, `status/`, `config/`, `mesh/...`).

Post-v1.2 adopters publishing on those paths SHOULD migrate to the
`<event_type_root>/...` shape. Bridges that have to consume both
should treat the legacy paths as separate input adapters and
republish under the v1.2 convention.

## What this doc does NOT cover

- **Authentication & authorization.** Out of scope for the ZMeta spec;
  defer to deployment-specific MQTT broker config.
- **QoS guidance.** Most deployments use QoS 1 universally; QoS 2 only
  for irreplaceable retained snapshots. Not normative.
- **Topic-level rate limits, partitioning, sharding.** Broker-specific.
- **Other transports.** UDP and Kafka have very different binding
  conventions; this document explicitly scopes itself to MQTT.

## Compatibility

Nothing in this document changes the wire format, schema, or dispatch
rules. A v1.1 publisher that emits on any topic shape, with any retain
behavior, with any subtype string, continues to produce schema-valid
ZMeta. This is binding guidance, not a validation surface.
