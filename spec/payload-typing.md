# Payload typing — `event.payload_schema_uri` and `event.payload_cardinality`

**Status:** Proposed for v1.2.0. Two backward-compatible additive envelope fields.

Both fields let receivers reason about the payload's shape *without ZMeta
itself prescribing what's in it*. They are advisory hints; consumers MAY
use them and MUST tolerate their absence.

## `event.payload_schema_uri`

**Optional string, format URI.** Names the schema the `payload` object
conforms to. ZMeta does NOT host payload schemas; this field merely
identifies them so receivers can validate, route, or render appropriately.

### Example

```json
{
  "zmeta_version": "1.2.0",
  "event": {
    "event_type": "STATE_EVENT",
    "event_subtype": "asset",
    "ts": "2026-06-05T15:30:00Z",
    "payload_schema_uri": "https://developer.anduril.com/schemas/lattice/entity/v4.8.1.json"
  },
  "source": { "platform_id": "example.publisher.autonomy" },
  "payload": { /* Lattice Entity */ }
}
```

### Observed URI conventions

Not normative — these are observed conventions in early adoption.
Producers and consumers should coordinate via these or document their own.

| Domain | URI prefix | Notes |
|---|---|---|
| Anduril Lattice SDK | `https://developer.anduril.com/schemas/lattice/` | Entity, Task, Sensor, Health |
| NIEM | `https://release.niem.gov/niem/` | DoD/IC interop schema |
| OGC | `https://schemas.opengis.net/` | Geospatial — KML, GML, SensorML |
| Project-internal | `urn:<project>:<subtype>:<version>` | When no public registry applies |

### Receiver behavior

A consumer that recognizes the URI MAY validate `payload` against the
referenced schema.

A consumer that does NOT recognize the URI MUST ignore the field (treat
as if absent) and still process the payload best-effort. The hint is
never authoritative for routing or filtering decisions.

## `event.payload_cardinality`

**Optional enum, defaults to `"single"`.** Declares whether the payload
describes one entity or a snapshot of many.

| Value | Meaning |
|---|---|
| `"single"` (default) | Payload describes exactly one entity or observation. |
| `"snapshot"` | Payload contains `entries: [...]` — a complete snapshot replacing any prior snapshot for the same `(event_type, event_subtype, source.platform_id)` retained slot. |

### Snapshot example

```json
{
  "zmeta_version": "1.2.0",
  "event": {
    "event_type": "STATE_EVENT",
    "event_subtype": "lora_nodedb",
    "ts": "2026-06-05T15:30:00Z",
    "payload_cardinality": "snapshot"
  },
  "source": { "platform_id": "node.lora-bridge" },
  "payload": {
    "entries": [
      { "id": "node-001", "user": "alice", "hw": "RAK4630" },
      { "id": "node-002", "user": "bob",   "hw": "T-Beam" }
    ]
  }
}
```

### Receiver behavior

When `payload_cardinality == "snapshot"`:
- Validators MUST require `payload.entries` to exist as an array.
- Consumers treat each new event as wholesale-replacing the prior
  snapshot for the same retained-slot key. No delta semantics.
- On MQTT specifically, snapshot events SHOULD be retained with
  `retain=true` so late subscribers receive current state immediately
  on subscribe.

When `payload_cardinality == "single"` (or absent):
- Payload is one entity. `entries` MAY still be present and meaningful
  in the domain schema, but consumers don't get to assume snapshot
  semantics.

## Why both at the envelope, not in `payload.*`

Receivers route, retain, and validate based on these hints. Pulling them
out of the payload's interior into the envelope lets a transport adapter
(broker, gateway, ATAK bridge) reason about them without parsing the
domain payload.

## Compatibility with v1.1

Both fields are optional. A v1.1 sender produces messages with neither
field present; a v1.2 receiver treats those as `payload_schema_uri = null`
and `payload_cardinality = "single"`. No interoperability impact.

## Examples

See `examples/zmeta-v1.2-examples.jsonl`, line 4
(`snapshot-cardinality`).
