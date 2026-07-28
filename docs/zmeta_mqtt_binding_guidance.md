# ZMeta Over MQTT - Advisory Transport Binding Guidance

Status: advisory transport-binding guidance (Docs/advisory change class).
Current release context: ZMeta v1.1.19.

This document is **non-normative**. It defines no new event vocabulary, changes
no schema, no validation rule, no policy default, and no version dispatch
behavior. Where anything here appears to conflict with a governed source, the
governed source wins in the authority order from
`docs/zmeta_change_governance.md`: `spec/semantics-contract.md` (v1.0 Locked),
then the canonical schemas under `schema/` and the policy pack under `policy/`.

## Purpose and Scope

ZMeta is transport-agnostic by contract. Section 4.6 of the semantic contract
is explicit: transport choice carries no semantic meaning, and identical events
flowing over different transports remain semantically identical. Nothing about
MQTT changes what a ZMeta event means.

At the same time, MQTT is a common carrier for ZMeta in fielded pub/sub
deployments, and every deployment ends up answering the same transport
questions: how to shape topics, what to retain, what a cleared retained slot
means, and how command traffic behaves on a broker. This document codifies one
consistent set of answers so adopters do not re-invent them incompatibly.

The field conventions described here were observed in an external deployment
running ZMeta at scale and reported in
[PR #4](https://github.com/JTC-byte/zmeta-spec/pull/4). This document
re-derives those conventions from the locked kernel outward; citing the PR
credits the operational experience, not the PR's proposed vocabulary, which is
not part of ZMeta.

Two framing rules govern everything below:

1. **The envelope is authoritative; the topic is a routing convenience.**
   Consumers derive meaning from `event.event_type`, `event.event_subtype`,
   and the validated payload, never from the topic string. If a topic and its
   envelope disagree, the envelope wins and the message should be treated as
   suspect.
2. **Broker mechanics never relax kernel semantics.** Retained messages, QoS
   levels, and retained-slot clearing are delivery behaviors. They do not
   extend TTLs, refresh timestamps, upgrade confidence, or convey entity
   lifecycle.

## Topic Shape

Recommended topic shape:

```text
<event_type_root>/<event_subtype>/<entity-scoped-id>
```

Where:

- `<event_type_root>` is the lowercased `event.event_type` with the trailing
  `_EVENT` removed.
- `<event_subtype>` is the **locked** `event.event_subtype` value, verbatim.
  Subtypes are a governed enum per event type (contract Section 7.3); the
  topic segment simply repeats the envelope value. It never introduces new
  vocabulary.
- `<entity-scoped-id>` is a long-lived identifier appropriate to the event
  family (see below), not the per-message `event.event_id`.

| event_type | event_type_root | Locked event_subtype values |
|---|---|---|
| OBSERVATION_EVENT | `observation` | `RF`, `EO`, `IR`, `ACOUSTIC`, `NETWORK` |
| INFERENCE_EVENT | `inference` | `CLASSIFICATION`, `ASSOCIATION`, `ANOMALY`, `BEHAVIOR` |
| FUSION_EVENT | `fusion` | `TRACK_FUSION` |
| STATE_EVENT | `state` | `TRACK_STATE` |
| COMMAND_EVENT | `command` | `GOTO`, `ORBIT`, `HOLD`, `SEARCH_BOX`; v1.1.0 additionally defines `RETURN_TO_BASE`, `LAND`, `LOITER`, `SCAN_RF`, `TRACK_TARGET`, `CHANGE_SENSOR_MODE` |
| SYSTEM_EVENT | `system` | `LINK_STATUS`, `TIME_STATUS`, `SCHEMA_VIOLATION`, `TASK_ACK`; v1.1.0 additionally defines `SENSOR_STATUS`, `PLATFORM_STATUS` |

The v1.1.0-only subtypes are valid only for events declaring
`zmeta_version: "1.1.0"` (contract Sections 2.2, 21.5-21.7). Producers MUST
NOT use free-form subtypes on the wire or in topics; a topic segment that is
not a locked subtype value describes a non-conformant event.

Example topics:

```text
observation/RF/kraken-01
observation/EO/eo-mast-02
inference/CLASSIFICATION/rf-classifier-01
inference/ASSOCIATION/assoc-engine-01
fusion/TRACK_FUSION/<track_id>
state/TRACK_STATE/<track_id>
command/GOTO/<platform_id>
system/TIME_STATUS/<platform_id>
system/TASK_ACK/<platform_id>
```

Deployments MAY prepend site- or enclave-scoped prefix segments (for example
`site-a/state/TRACK_STATE/<track_id>`). Prefixes are deployment configuration
and carry no semantics.

### Choosing the entity-scoped identifier

- `observation/*`: the producing sensor or platform identifier
  (`source.sensor_id` or `source.platform_id`). Never a track identifier:
  observation payloads prohibit track identity, and only fusion-authorized
  producers create `track_id` (contract Sections 7.4, 7.6, 13.1). Do not use
  the topic to smuggle an identity claim the payload is forbidden to carry.
- `inference/*`: the producing model/analytic service identifier. Same rule:
  no track identity.
- `fusion/*` and `state/*`: the fusion-assigned `payload.track_id`.
- `command/*`: the tasked platform identifier.
- `system/*`: the reporting platform identifier.

Identifier segments should avoid MQTT-reserved characters (`+`, `#`, `/`) and
whitespace.

### Why this shape

- **Wildcard subscriptions fall out of the hierarchy.** `observation/+/+`
  subscribes to all observations; `observation/RF/+` to all RF observations;
  `state/TRACK_STATE/+` to every operator-facing track; `+/+/<id>` to
  everything about one entity or producer.
- **Entity-scoped ids keep topics long-lived.** `event.event_id` is unique per
  message; putting it in the topic creates one topic per event, defeats
  wildcard planning, explodes the broker's retained-message store, and makes
  retained-slot hygiene impossible. Topics should index entities and
  producers, which persist; events are the payloads that flow through them.
- **The topic is computable from the envelope alone**, so any conformant
  publisher and subscriber agree on placement without a side registry.

## Retain Guidance by Event Family

MQTT `retain` stores the last message on a topic and replays it to new
subscribers. That is a delivery convenience for late joiners. It is **not** a
statement of freshness, and it never relaxes ZMeta timing-quality or TTL
semantics.

### STATE_EVENT (`state/TRACK_STATE/<track_id>`) - retain, with honesty rules

Retaining state serves late joiners: a subscriber that connects mid-mission
immediately receives the last published state for each track. This is the
strongest case for `retain=true`.

The honesty rules are not optional:

- A retained event is **stale data with a timestamp, never current truth**.
  The broker replays it at subscribe time, but its validity is anchored to
  `event.ts`, not to delivery time.
- Consumers MUST judge freshness from `event.ts` plus `payload.valid_for_ms`
  (the mandatory TTL on TRACK_STATE, contract Sections 7.7 and 14) and from
  applicable timing context (per-event `timing_quality` or the source's latest
  SYSTEM_EVENT / TIME_STATUS, Section 5.3) before treating a retained state as
  current.
- A retained state whose `valid_for_ms` has lapsed is expired. It may inform
  history and AAR; it MUST NOT be rendered or used as current state, and
  stale-track handling (confidence and TTL decay, STALE/LOST behavior,
  contract Sections 13.3-13.4) applies exactly as if the event had arrived
  live.
- Retention MUST NOT be used to extend TTL, refresh timestamps, or launder a
  degraded track into a clean-looking one. Republishing old state with a new
  `event.ts` is laundering, not retention.

### OBSERVATION_EVENT - do not retain

Observations are momentary measured facts anchored to capture time. Replaying
the last observation to a late joiner presents a past measurement as if it
were fresh input. Late joiners needing history should use an AAR/replay store,
not the broker's retained slot.

### INFERENCE_EVENT and FUSION_EVENT - do not retain by default

Inferences are claims about specific upstream observations
(`lineage.based_on`); replaying the last claim out of its temporal context
invites treating an old claim as a current one. Fusion events feed
fusion-aware consumers that need the stream, not the last sample. Deployments
that retain these anyway inherit the same honesty rules as retained state:
freshness is judged from `event.ts` and timing context, never from delivery.

### COMMAND_EVENT - never retain

Commands are one-shot, TTL-bound directives, idempotent and deduplicated by
`payload.task_id` (contract Sections 7.8, 13.2). A retained command replayed
to a late subscriber is a replay hazard: at best it is rejected as expired
(`valid_for_ms`) or as a duplicate; at worst a non-conformant consumer
executes stale tasking. See "Command Traffic Over MQTT" below.

### SYSTEM_EVENT - retain selectively, short refresh

Retaining the latest `system/TIME_STATUS/<platform_id>` and
`system/LINK_STATUS/...` gives late joiners immediate timing and link context,
which directly supports the freshness judgments above. The contract's own
limit applies: consumers MUST NOT treat a periodic TIME_STATUS as valid
indefinitely (Section 5.3). A stale retained TIME_STATUS means timing quality
is unknown or stale, and consumers degrade, gate, warn, or reject per
deployment policy (`policy/timing-freshness.yaml`). Diagnostic events such as
SCHEMA_VIOLATION and TASK_ACK should not be retained.

## Tombstones Are Broker Hygiene, Not Semantics

MQTT clears a retained slot when a publisher sends a zero-byte retained
payload to the topic. Publishers SHOULD do this when they permanently stop
publishing an entity's topic, so late joiners do not receive an abandoned
snapshot.

That is the entire meaning of a tombstone in this binding: **broker hygiene**.

- An empty retained payload is not a ZMeta event. It has no envelope, no
  `event_id`, no `ts`, no source identity, no lineage, and cannot pass
  validation. It carries no semantic content and cannot be audited.
- Consumers MUST NOT treat a tombstone as an authoritative entity-removal
  directive. Removing a track from displays, fusion input, or downstream
  computation because a broker slot went empty is deriving semantic truth from
  transport state.
- Semantic removal and expiry are conveyed in-band: TTL lapse
  (`payload.valid_for_ms`) expires state, and stale/lost/retired handling
  follows contract Sections 13.3-13.4 (confidence and TTL decay, state
  emission stopping, merge/split via new fusion events with lineage).
- Dedicated track lifecycle event subtypes are future-reserved (contract
  Section 24.4). Do not invent removal, drop, or lifecycle subtypes to ride
  alongside tombstones, and do not overload SCHEMA_VIOLATION as a lifecycle
  signal (Section 7.9 prohibits that reuse).

The safe consumer interpretation of a tombstone is "no retained snapshot is
available on this topic", and nothing more.

## Command Traffic Over MQTT

Command governance is transport-independent. Putting COMMAND_EVENT on a broker
changes none of it (contract Sections 4.10, 7.8, 15):

- **Producer authority still applies.** Only command-authorized or
  deconfliction-authorized producers may emit COMMAND_EVENT; AI and analytics
  producers SHALL NOT directly command platforms. Broker ACLs are a useful
  defense-in-depth layer but do not replace producer-authority policy.
- **`requires_deconfliction: true` still applies.** A schema-valid command on
  the right topic is not thereby deconflicted.
- **Idempotency and dedupe by `payload.task_id` still apply.** Broker
  redelivery (QoS 1) is safe precisely because duplicate commands MUST NOT be
  forwarded for execution a second time.
- **TTL still applies.** `valid_for_ms` bounds every command; expired commands
  are rejected, not executed late.
- **The altitude prohibition still applies.** The reference policy enforces
  the altitude denylist recursively with key normalization, so altitude keys
  cannot be smuggled through `geometry`, `extensions`, or nested objects, nor
  past the check via case or whitespace variants.
- **TASK_ACK closes the loop.** Command lifecycle is audited through
  SYSTEM_EVENT / TASK_ACK (for example on `system/TASK_ACK/<platform_id>`),
  deduplicated by task id, original event id, and state.

Binding recommendations: publish commands with `retain=false` and QoS 1. No
retained command should ever exist on the broker; QoS 1 gives at-least-once
delivery, and task-id idempotency makes redelivery harmless.

## QoS Notes (Advisory)

QoS affects delivery probability and duplication, never meaning.

- **QoS 0**: acceptable for high-rate observation streams on healthy links
  where individual losses are tolerable. Loss is a transport fact; do not
  re-emit lost content under a new `event_id`.
- **QoS 1**: a sound default for state, fusion, inference, command, and system
  traffic. Redelivery duplicates are safe because dedupe keys are governed
  (`event_id` generally; `task_id` for commands; the TASK_ACK triple for
  acks).
- **QoS 2**: rarely warranted. Governed dedupe already provides effective
  exactly-once semantics at the consumer, and QoS 2 handshakes are expensive
  on constrained links.

## Legacy and Non-ZMeta Topic Paths

Brokers in real deployments also carry non-ZMeta traffic: vendor telemetry,
CoT-over-MQTT bridges, autopilot streams, and legacy flat hierarchies.
Fielded deployments report `tracks/`, `sensors/`, `commands/`, `tasks/`, and
`status/` trees (upstream PR #4 telemetry). Treat every such path as a
**separate ingress adapter boundary**, never as an alternate ZMeta dialect,
and do not mint new ZMeta traffic under those legacy roots:

- An adapter consumes the legacy topic, normalizes timestamps and units,
  generates ZMeta event identity, records its `lineage.transform`, rejects
  ambiguous input, and republishes canonical events under the canonical topic
  shape (contract Section 3.4; ZMETA-ADAPTER conformance class).
- External tactical tracks MUST NOT be mapped directly onto
  `state/TRACK_STATE/...`. They enter through the external projection
  promotion path of contract Section 4.5.1: explicit promotion evidence at
  `payload.extensions.external_promotion` (see
  `policy/producer-authority.yaml`), a `promote:<adapter>:<policy>` lineage
  transform, and freshness, confidence-basis, trust, and loop/reflection
  checks under active policy. A reflected ZMeta projection returning through a
  lossy path is never re-promoted as if it were the original.
- Migrating a publisher from a legacy topic to the canonical shape is a
  non-semantic transport change; the events themselves are unchanged.

## What This Document Does Not Cover

- Authentication, authorization, broker ACLs, and TLS configuration.
- Broker tuning, bridging, high availability, shared subscriptions, and
  session persistence.
- Payload encoding selection (JSON, compact binary, protobuf); see the
  governed encoding documents under `spec/`.
- Bindings for other transports (UDP, Kafka, files, queues). Per contract
  Section 4.6 they carry the same events with the same meaning; their binding
  conventions differ and are out of scope here.
