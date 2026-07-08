# Cross-Sensor Correlation With Existing Vocabulary - The Association Bond Pattern

Status: advisory pattern guide (Docs/advisory change class, non-normative).
Current release context: ZMeta v1.1.11.

This document describes how to solve fielded cross-sensor correlation --
stable entity identity assigned by a fusion engine, propagated to the sensors
that contribute to it, surviving handoffs, with split/merge notification --
using only locked ZMeta v1.0 vocabulary. It defines no new event types, no
new subtypes, no envelope fields, and no schema or policy changes. Nothing in
this document changes validation or dispatch behavior. Where this document
conflicts with a governed source, defer to the authority order:
`spec/semantics-contract.md` (v1.0 Locked, normative), then the canonical
schemas under `schema/` and the policy pack under `policy/`, then
`docs/zmeta_change_governance.md`.

The field conventions harvested here were observed in a fielded multi-sensor
deployment contributed through upstream PR #4
(https://github.com/JTC-byte/zmeta-spec/pull/4). That PR proposed new
envelope vocabulary to carry them; this document re-derives the same
operational needs from the locked kernel outward and shows they compose from
existing primitives. Crediting the source is not an endorsement of the PR's
proposed schema changes.

The headline claim, demonstrated end-to-end by the runnable example stream in
`examples/zmeta-correlation-pattern-examples.jsonl` (validated by
`tools/validate_examples.py` at Profile H against the unchanged v1.0 schema
and policy pack): **cross-sensor correlation identity needs no new
vocabulary.**

## 1. The Operational Need

A deployment running many heterogeneous sensors against the same physical
entities needs:

- A stable identity for "the real-world thing," independent of which sensor
  is currently observing it.
- That identity assigned by exactly one authority (a fusion engine), not
  invented per-sensor.
- A way to tell each contributing sensor "your local track N is entity X" so
  its subsequent products can be grouped by entity without re-running
  association downstream.
- Identity that survives sensor handoffs: when the RF sensor loses the
  entity and an EO sensor picks it up, consumers still see one entity.
- Split and merge notification with no observable intermediate state: a
  consumer must never see "the bond is gone" without simultaneously seeing
  what replaced it.

ZMeta already contains every primitive this requires. The locked pipeline
`OBSERVATION_EVENT -> INFERENCE_EVENT -> FUSION_EVENT -> STATE_EVENT` places
each piece of the pattern at exactly one semantic layer, and the policy
denylists actively prevent the shortcuts that would corrupt it.

## 2. Identity Creation: FUSION_EVENT / TRACK_FUSION

The fused `payload.track_id` **is** the stable cross-sensor correlation
identifier. No parallel identity field is needed.

Contract grounding (all locked v1.0):

- FUSION_EVENT with `event_subtype: TRACK_FUSION` is the only place track
  identity is created (contract 4.5, 7.6). Only fusion-authorized producers
  may create `track_id`; the reference producer-authority policy authorizes
  producers such as `fusion-*`, `fusion-engine`, and the reference
  multi-role producer `torch` (`policy/producer-authority.yaml`).
- `payload.members` lists the contributing ZMeta events as UUIDv7
  references (contract 4.3), and envelope `lineage.based_on` is mandatory.
- Top-level `confidence` is mandatory and expresses how safe the fused
  continuity claim is for downstream use (contract 8.1, 8.3).
- `track_id` persists unchanged across subsequent events for the same
  track, is globally unique, and is never reused after loss, merge, split,
  or retirement (contract 7.6, 13.1). Those properties are exactly what a
  "stable correlation id" requires -- they were locked in v1.0.

Alias sets -- external identifier schemes such as MMSI or ICAO24, or
sensor-local handles -- may ride in the fusion (or state) payload as
non-reserved-key fields. The fusion and state payload schemas accept
additional properties, so a convention such as:

```json
"aliases": [
  { "scheme": "MMSI", "value": "366998310" },
  { "scheme": "internal", "value": "rf-local-42" }
]
```

is schema-valid today with no changes, provided no reserved or denylisted
key name is used. Aliases are descriptive payload content, not identity:
`payload.track_id` remains the identity.

**External tactical tracks are not a side door.** AIS, ADS-B, Link-16-style
feeds, CoT/TAK tracks, and vendor COP reports are lossy external reports,
not sensor observations. When such a report enters ZMeta as state, it MUST
go through the contract 4.5.1 external-promotion path: a new event with new
identity, policy-scoped promotion evidence at
`payload.extensions.external_promotion` (per
`policy/producer-authority.yaml`), and a `promote:<adapter>:<policy>`
lineage transform -- never directly, and never as a fusion identity source
without that evidence. A reflected ZMeta projection re-entering through an
external gateway is rejected as loop risk by default. Nothing in this
correlation pattern relaxes that boundary.

## 3. Bond Notification: INFERENCE_EVENT / ASSOCIATION

"These local sensor tracks belong to fused identity X" is an associative
claim derived from observations -- which is precisely what the locked
ASSOCIATION inference subtype exists for. The bond notification is an
INFERENCE_EVENT with `event.event_subtype: ASSOCIATION` and
`payload.inference_type: ASSOCIATION` (the envelope subtype and payload
discriminator must match exactly, contract 7.3).

The claim convention:

- `payload.claim.association` is `"BOND_ASSIGNED"` or `"BOND_DISSOLVED"`.
- `payload.claim.sensor_ref` names the sensor platform whose local tracks
  the bonds refer to. How the event is fanned out to that sensor (topics,
  queues, retained messages) is a transport binding and carries no
  semantics (contract 4.6).
- `payload.claim.bonds[]` entries carry:
  - `local_track_ref` -- the sensor's own continuity handle. This is
    payload-scoped provenance in the sense of contract 9.2 ("source object
    IDs"); it is deployment-local and asserts nothing across sensors.
  - `fused_track_ref` -- a **reference** to the fusion-created identity.
    The key name `track_id` is policy-banned on inference payloads
    (`policy/semantics.yaml`, `inference_event.payload_must_not_contain`),
    and the schema additionally pins `payload.track_id`, `payload.members`,
    and `payload.estimated_state` (and the same keys inside `claim`) to
    invalid. That ban is not an obstacle to work around -- it is the
    design: an inference may point at identity, it may never assert or
    mint it. Reference, not assertion.
  - `fusion_revision` -- an integer that bumps each time the fused
    identity's bonded membership changes, so consumers can order
    re-bondings without diffing alias or member sets.
- Top-level `confidence` is mandatory on INFERENCE_EVENT and here expresses
  association strength -- the fusion engine's estimate of how safe it is to
  treat the local track and the fused identity as the same entity.
- `payload.model.name` / `payload.model.version` identify the association
  process (contract 11.1), and `payload.based_on` plus envelope
  `lineage.based_on` reference the contributing observation events. Note
  that the reference lineage policy (`policy/lineage.yaml`) types
  INFERENCE_EVENT lineage parents as OBSERVATION_EVENT only, with
  parent-type mismatch set to reject: the bond notification's lineage
  points at the observational evidence for the association, while the
  fused identity itself is referenced by value inside the claim
  (`fused_track_ref`). Payload `based_on` must be equal to or a subset of
  envelope lineage (contract 4.8).

A sensor receiving BOND_ASSIGNED updates its private
`local_track_ref -> fused_track_ref` map. Nothing about the sensor's own
emission authority changes: it still emits OBSERVATION_EVENTs only.

## 4. The Atomic Split Invariant

This is the strongest piece of design harvested from PR #4, and it is worth
adopting verbatim: **a single BOND_DISSOLVED ASSOCIATION event carries both
the dissolved bonds and the replacement bonds, so consumers never observe an
intermediate state.**

- `payload.claim.dissolved[]` entries carry `local_track_ref` and
  `former_fused_track_ref`.
- `payload.claim.new_bonds[]` entries carry `local_track_ref`,
  `fused_track_ref`, and `fusion_revision`, and may be empty when the
  dissolution leaves a local track unbonded (it then re-bonds, or not, as
  if cold-started).

Because ZMeta events are append-only (contract 4.2), the transition is one
immutable event: there is no window in which a consumer has seen the
dissolution but not its consequences, and no event is ever mutated to
express the change.

The invariant composes cleanly with locked track lifecycle rules (contract
13.3): a split means the fusion engine emits new FUSION_EVENTs minting
distinct replacement `track_id` values with lineage to the original
history, and the original `track_id` is never reused. The BOND_DISSOLVED
event is the sensor-facing notification of that transition, not the
transition itself -- fusion events remain the identity authority. A merge is
the mirror image: the retired identity's bonds dissolve and the new bonds
point at the surviving canonical identity, again in one event.

## 5. The Correlation Hint: payload.extensions.correlation_hint

Producers that want to echo the fused identity on subsequent events -- so
downstream consumers can group products by entity without joining against
the association stream -- may use a namespaced payload extension:

```json
"extensions": {
  "correlation_hint": {
    "fused_track_ref": "track-cor-001",
    "fusion_revision": 1,
    "association_ref": "019f3f51-36f7-7737-9287-725353e11ccb",
    "assigned_by": "torch"
  }
}
```

The hint carries only non-reserved reference keys:

- `fused_track_ref` -- the fused identity being echoed.
- `fusion_revision` -- the revision under which the bond was assigned.
- `association_ref` -- the `event_id` (UUIDv7) of the authoritative
  ASSOCIATION event that assigned the bond.
- `assigned_by` -- the producer identity of the assigning fusion function.

The hint MUST NOT carry `confidence`, `track_id`, `classification`, or any
other key on the observation denylist (`policy/semantics.yaml`:
`track_id`, `entity_class`, `classification`, `label`, `class_name`,
`confidence`). This is enforced, not just requested: the semantic validator
applies the denylist recursively at every nesting depth, normalizing keys
(strip plus casefold) before comparison, so `Confidence`, `" track_id"`, or
a denylisted key buried three objects deep inside `extensions` all fail
validation. Two negative fixtures in `conformance/bad-events/must-fail.jsonl`
(`observation-correlation-hint-confidence-laundering` and
`observation-correlation-hint-track-id-nested`) prove exactly that.

By design, this forces the hint to point at the authoritative event instead
of restating its claims. If a consumer needs the association strength, it
resolves `association_ref` and reads the ASSOCIATION event's mandatory
confidence; the strength never travels on an observation, where top-level
and nested confidence are prohibited.

Consumers MUST NOT treat the hint as track authority, identity, confidence,
or lineage. The authoritative chain is always: FUSION_EVENT identity
creation, INFERENCE_EVENT ASSOCIATION bonds, and envelope
`lineage.based_on`. A hint is a grouping convenience; any fusion, state,
export, or command-basis decision must resolve the authoritative events.

A `CORRELATION_HINT` entry (status `proposed`, category `fusion_extension`)
exists in `spec/extension-registry.yaml` to standardize the name, allowed
event types, and profile projection behavior (`optional_omission` -- valid
only because the hint is barred from authority decisions). Per the registry
rules, a proposed entry is not valid vocabulary and confers nothing; until
the maintainer adopts it, `correlation_hint` is a deployment-local
namespaced extension that is safe to ignore by contract (4.11), and
deployments wanting strict collision safety may carry it under a vendor
namespace such as `vendor.<owner>.correlation_hint`.

## 6. Worked Example

The full runnable stream is `examples/zmeta-correlation-pattern-examples.jsonl`
(one event per line; excerpts below are pretty-printed for readability). It
validates at Profile H with the unchanged v1.0 schema and policy pack via
`python tools/validate_examples.py`. All ids are UUIDv7, all timestamps are
UTC-Z, and every payload carries `timing_quality` per the reference policy.

**Step 1 -- uncorrelated observations.** Two RF sensors measure the same
emitter. No identity anywhere: observation payloads cannot carry it.

```json
{
  "zmeta_version": "1.0",
  "event": {
    "event_id": "019f3f51-36f7-7737-9287-7250783fc090",
    "event_type": "OBSERVATION_EVENT",
    "event_subtype": "RF",
    "ts": "2026-07-07T12:00:00Z"
  },
  "source": {
    "platform_id": "sensor-node-01",
    "node_role": "EDGE",
    "producer": "rf-sensor"
  },
  "profile": "H",
  "payload": {
    "modality": "RF",
    "features": {
      "center_freq_hz": 433920000,
      "bandwidth_hz": 250000,
      "power_dbm": -47.5
    },
    "geo": { "lat": 34.0522, "lon": -118.2437, "alt_m": 118.0 },
    "timing_quality": {
      "time_source": "GPS_PPS",
      "sync_state": "LOCKED",
      "est_error_ms": 1,
      "last_sync_ts": "2026-07-07T11:59:59Z"
    }
  }
}
```

A second observation (`...72513a5ec344`) from `sensor-node-02` follows one
second later.

**Step 2 -- fusion creates the correlation identity.** The fusion-authorized
producer mints `track_id`, lists both observations as members, and carries
mandatory confidence and lineage.

```json
{
  "zmeta_version": "1.0",
  "event": {
    "event_id": "019f3f51-36f7-7737-9287-725246071ad2",
    "event_type": "FUSION_EVENT",
    "event_subtype": "TRACK_FUSION",
    "ts": "2026-07-07T12:00:02Z"
  },
  "source": {
    "platform_id": "fusion-node-01",
    "node_role": "GATEWAY",
    "producer": "torch"
  },
  "profile": "H",
  "payload": {
    "track_id": "track-cor-001",
    "members": [
      "019f3f51-36f7-7737-9287-7250783fc090",
      "019f3f51-36f7-7737-9287-72513a5ec344"
    ],
    "stability": 0.64,
    "last_seen_ts": "2026-07-07T12:00:01Z",
    "timing_quality": {
      "time_source": "GPS_PPS",
      "sync_state": "LOCKED",
      "est_error_ms": 1,
      "last_sync_ts": "2026-07-07T11:59:59Z"
    }
  },
  "confidence": 0.78,
  "lineage": {
    "based_on": [
      "019f3f51-36f7-7737-9287-7250783fc090",
      "019f3f51-36f7-7737-9287-72513a5ec344"
    ]
  }
}
```

Alias sets (Section 2) would ride here as additional non-reserved payload
keys; the minimal runnable example omits them.

**Step 3 -- bond assignment.** The fusion engine tells `sensor-node-01` that
its local track `rf-local-42` is bonded to `track-cor-001`. Confidence is
the association strength; lineage references the observational evidence.

```json
{
  "zmeta_version": "1.0",
  "event": {
    "event_id": "019f3f51-36f7-7737-9287-725353e11ccb",
    "event_type": "INFERENCE_EVENT",
    "event_subtype": "ASSOCIATION",
    "ts": "2026-07-07T12:00:03Z"
  },
  "source": {
    "platform_id": "fusion-node-01",
    "node_role": "GATEWAY",
    "producer": "torch"
  },
  "profile": "H",
  "payload": {
    "inference_type": "ASSOCIATION",
    "claim": {
      "association": "BOND_ASSIGNED",
      "sensor_ref": "sensor-node-01",
      "bonds": [
        {
          "local_track_ref": "rf-local-42",
          "fused_track_ref": "track-cor-001",
          "fusion_revision": 1
        }
      ]
    },
    "model": { "name": "association-engine", "version": "1.0.0" },
    "based_on": [
      "019f3f51-36f7-7737-9287-7250783fc090",
      "019f3f51-36f7-7737-9287-72513a5ec344"
    ],
    "timing_quality": {
      "time_source": "GPS_PPS",
      "sync_state": "LOCKED",
      "est_error_ms": 1,
      "last_sync_ts": "2026-07-07T11:59:59Z"
    }
  },
  "confidence": 0.87,
  "lineage": {
    "based_on": [
      "019f3f51-36f7-7737-9287-7250783fc090",
      "019f3f51-36f7-7737-9287-72513a5ec344"
    ]
  }
}
```

**Step 4 -- subsequent observation carrying the hint.** The sensor's next
observation echoes the fused identity through the extension. Still no
confidence, no `track_id`, no classification anywhere in the payload -- the
hint points at the authoritative ASSOCIATION event instead.

```json
{
  "zmeta_version": "1.0",
  "event": {
    "event_id": "019f3f51-36f7-7737-9287-7254aa87f1bb",
    "event_type": "OBSERVATION_EVENT",
    "event_subtype": "RF",
    "ts": "2026-07-07T12:00:04Z"
  },
  "source": {
    "platform_id": "sensor-node-01",
    "node_role": "EDGE",
    "producer": "rf-sensor"
  },
  "profile": "H",
  "payload": {
    "modality": "RF",
    "features": {
      "center_freq_hz": 433920000,
      "bandwidth_hz": 250000,
      "power_dbm": -46.8
    },
    "geo": { "lat": 34.0525, "lon": -118.2431, "alt_m": 119.0 },
    "extensions": {
      "correlation_hint": {
        "fused_track_ref": "track-cor-001",
        "fusion_revision": 1,
        "association_ref": "019f3f51-36f7-7737-9287-725353e11ccb",
        "assigned_by": "torch"
      }
    },
    "timing_quality": {
      "time_source": "GPS_PPS",
      "sync_state": "LOCKED",
      "est_error_ms": 1,
      "last_sync_ts": "2026-07-07T11:59:59Z"
    }
  }
}
```

The example file also carries a STATE_EVENT / TRACK_STATE projection of
`track-cor-001` (`...72559f10ffc7`) -- the operator-facing surface where the
fused identity reaches every profile.

**Step 5 -- atomic split.** The fusion engine determines the bond was wrong
(two distinct entities). One BOND_DISSOLVED event carries both the
dissolution and the replacement bond; `track-cor-001` is never reused for
the re-bonded local track.

```json
{
  "zmeta_version": "1.0",
  "event": {
    "event_id": "019f3f51-36f7-7737-9287-72560601cbbe",
    "event_type": "INFERENCE_EVENT",
    "event_subtype": "ASSOCIATION",
    "ts": "2026-07-07T12:00:06Z"
  },
  "source": {
    "platform_id": "fusion-node-01",
    "node_role": "GATEWAY",
    "producer": "torch"
  },
  "profile": "H",
  "payload": {
    "inference_type": "ASSOCIATION",
    "claim": {
      "association": "BOND_DISSOLVED",
      "sensor_ref": "sensor-node-01",
      "dissolved": [
        {
          "local_track_ref": "rf-local-42",
          "former_fused_track_ref": "track-cor-001"
        }
      ],
      "new_bonds": [
        {
          "local_track_ref": "rf-local-42",
          "fused_track_ref": "track-cor-002",
          "fusion_revision": 1
        }
      ]
    },
    "model": { "name": "association-engine", "version": "1.0.0" },
    "based_on": ["019f3f51-36f7-7737-9287-7254aa87f1bb"],
    "timing_quality": {
      "time_source": "GPS_PPS",
      "sync_state": "LOCKED",
      "est_error_ms": 1,
      "last_sync_ts": "2026-07-07T11:59:59Z"
    }
  },
  "confidence": 0.81,
  "lineage": { "based_on": ["019f3f51-36f7-7737-9287-7254aa87f1bb"] }
}
```

In a full stream, the replacement identity `track-cor-002` is minted by its
own FUSION_EVENT with lineage back to the original history (contract 13.3)
before or alongside this notification; the minimal example file keeps the
stream short.

## Conventions At A Glance

| Convention | Where it lives | Grounding |
|---|---|---|
| Correlation identity | `FUSION_EVENT` / `TRACK_FUSION` `payload.track_id` | Contract 4.5, 7.6, 13.1 (locked) |
| Alias sets | Non-reserved payload keys on fusion/state, e.g. `aliases[] {scheme, value}` | Schema additional properties; contract 9.2 |
| Bond assigned / dissolved | `INFERENCE_EVENT` / `ASSOCIATION`; `claim.association`, `claim.sensor_ref`, `claim.bonds[]` | Contract 7.3, 7.5 (locked subtype) |
| Bond entry fields | `local_track_ref`, `fused_track_ref`, `fusion_revision`; dissolved entries use `former_fused_track_ref` | Advisory convention (this doc) |
| Association strength | Mandatory top-level `confidence` on the ASSOCIATION event | Contract 8.1 (locked) |
| Atomic split | One BOND_DISSOLVED event carrying `dissolved[]` + `new_bonds[]` | Advisory convention; composes with contract 4.2, 13.3 |
| Identity echo | `payload.extensions.correlation_hint` (`fused_track_ref`, `fusion_revision`, `association_ref`, `assigned_by`) | Proposed `CORRELATION_HINT` registry entry; contract 4.11 |
| External tracks | 4.5.1 promotion path only (`payload.extensions.external_promotion`, `promote:*` transform) | Contract 4.5.1 (locked); `policy/producer-authority.yaml` |

## 7. What This Pattern Does Not Do

- **No envelope or vocabulary changes.** Every event above is plain locked
  v1.0 vocabulary; validation and dispatch are untouched. There is no
  `correlation` envelope object, no free-form subtypes, and no version
  bump.
- **No confidence on observations, ever.** Association strength lives on
  the ASSOCIATION event, where confidence is mandatory. The recursive,
  key-normalized denylist rejects any attempt to smuggle it (or identity,
  or classification) into an observation payload or its extensions, at any
  nesting depth.
- **No identity creation outside fusion authority.** Sensors never mint
  fused identity, inference producers never mint `track_id`, and a hint
  never creates identity. Only fusion-authorized producers create tracks,
  and split/merge never reuses an id.
- **Hints never survive into authority decisions.** A consumer making
  fusion, state, export, or command-basis decisions must resolve the
  authoritative FUSION and ASSOCIATION events through lineage. The hint is
  a grouping convenience with `optional_omission` projection behavior:
  under profile thinning it may be dropped without changing any event's
  meaning. Note also that INFERENCE_EVENTs do not export under Profiles L
  or M at all -- constrained-link consumers see the fused identity where
  they always have, in STATE_EVENT `track_id`.
- **No transport semantics.** Topic shapes, retained messages, tombstones,
  and QoS are transport bindings; contract 4.6 keeps them non-semantic and
  out of scope here.
- **No side door for external tracks.** External tactical reports still
  enter only through the 4.5.1 promotion path with explicit evidence.

The pattern is the alphabet doing its job: fusion creates identity,
inference claims association, observations stay honest facts, state
projects belief, and policy enforces the boundaries in between. Nothing new
was needed -- which is the interoperability guarantee working as designed.
