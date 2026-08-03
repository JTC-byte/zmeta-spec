## ZMeta to SAPIENT (BSI Flex 335 v2.0) Egress (Reference)

Overview: see `adapters/README.md`. Ingress counterpart:
`adapters/ingress/sapient/`.

Two projections into proto3-JSON-shaped SapientMessage dicts (snake_case).
Neither is a protobuf wire encoder; a downstream SAPIENT transport encodes
the dicts (consistent with the JREAP/KLV egress projections). Both stamp the
envelope `timestamp` from the event's own `event.ts`, never the wall clock.

- `zmeta_command_to_sapient_task.py`: COMMAND_EVENT -> Task
- `zmeta_state_to_sapient_detection.py`: STATE_EVENT/TRACK_STATE -> DetectionReport

### ULID discipline

Stock SAPIENT middleware validates SapientMessage ids as ULIDs (proto
`is_ulid`; Apex `strictIdFormat`, on by default, rejects violations,
verified live against Apex v4.2.0). Shared helpers live in
`ulid_util.py`; ULID timestamp components always come from the event's
own time, never a wall-clock read.

| Id | Contract |
| --- | --- |
| `report_id` | Adapter-derived: fresh ULID per report, 48-bit timestamp component = the event's own `event.ts` (ms). |
| `object_id` | Caller-owned identity. A ULID `track_id` passes through unchanged; otherwise the caller's `object_map` (track_id -> SAPIENT ULID) must resolve it or the event is refused. A mapped value that is not itself a ULID is refused. The adapter never mints a fresh identity per report, because object identity continuity is deployment state. |
| `task_id` | Caller-owned idempotency key: must already be a ULID or the event is refused. SAPIENT-bridged command producers mint ULID task_ids; the adapter never rewrites the key, because a derived id would break idempotent re-issue across the bridge and TaskAck correlation. |

### Command projection (COMMAND_EVENT -> Task)

Command safety rules (semantics contract 7.8) dominate this projection:

- Only deconflicted commands cross: `requires_deconfliction: true` or the
  event is refused (returns None).
- `task_id` must be a ULID (ULID discipline above) or the event is
  refused.
- Only three task types have an honest SAPIENT `Task.Command` verb:

  | ZMeta task_type | SAPIENT command | Notes |
  | --- | --- | --- |
  | `GOTO` | `move_to` | One 2D `Location` (`x`=lon, `y`=lat, `LAT_LNG_DEG_M`, `WGS84_E`). `z` is never populated. |
  | `TRACK_TARGET` | `follow` | `follow_object_id` resolved through the caller's `track_to_object` map; an unmapped target is refused, never fabricated. |
  | `CHANGE_SENSOR_MODE` | `mode_change` | `payload.sensor_mode` string as-is. |

- Everything else (`ORBIT`, `HOLD`, `SEARCH_BOX`, `LOITER`, `SCAN_RF`,
  `RETURN_TO_BASE`, `LAND`) returns None, which is documented residue. SAPIENT
  region tasking and discrete thresholds cannot carry their semantics
  without reinterpreting what the receiving node is asked to do, and this
  adapter never emits region/threshold commands.
- Altitude never crosses. A `target_geo` carrying an altitude field, at
  any depth, in any decoded container (a Mapping that is not a dict, a
  tuple, a set, a CBOR tag wrapper's `.value`), raises `ValueError`
  (mirroring the MAVLink mission-intent guard), and the output `Location`
  is built field-by-field from lat/lon only, so altitude-adjacent keys
  hiding in `extensions` cannot leak. The walk is iterative with a
  seen-set: sender-controlled nesting is a memory cost, never a
  `RecursionError` past the documented `ValueError`/None contract, and a
  cyclic (CBOR value-sharing) structure terminates instead of hanging.
- `task_end_time` = `event.ts` + `payload.valid_for_ms` (the ZMeta TTL is
  the only honest task bound available).
- `destination_id` is a required caller kwarg; a SAPIENT task without a
  destination node is undeliverable.

Command lossiness:

| ZMeta concern | Disposition |
| --- | --- |
| `payload.priority` | Dropped. SAPIENT Task has no priority field; it is not smuggled through free-text. |
| `payload.valid_from_ts` | Dropped; only the end bound (`task_end_time`) has a SAPIENT carrier. |
| `payload.timing_quality` | Dropped; Task has no timing-quality carrier. |
| `payload.extensions` | Dropped; vendor extension content is not re-exported across an external boundary. |
| `lineage` | Dropped; recover provenance through the originating ZMeta event. |

### State projection (STATE_EVENT/TRACK_STATE -> DetectionReport)

Declared 2-D geo (doctrine A1-02) exports honestly, without a fabricated
altitude: a STATE whose `payload.geo` declares `dimensionality: "2D"` (a
real, exact horizontal fix with no geometric vertical to assert, ever —
every AIS vessel, a barometric-only aircraft) projects a `Location` with
`x`/`y`/`coordinate_system`/`datum` and no `z` key. This matches the BSI
Flex 335 v2.0 proto (`sapient_msg/bsi_flex_335_v2_0/location.proto`): `x`
and `y` are `is_mandatory: true`, `z` carries no such marker anywhere in
the message, so an x-y position with no z is a wire-legal `Location`, not
an unrepresentable one. Fixed 2026-08 (first independent SAPIENT interop
run, MAJOR): before this, the geo gate was all-or-nothing (`lat` AND `lon`
AND `alt_m` all required), so every declared 2-D STATE silently returned
`None` — invisible to a SAPIENT consumer, no counter, no log, no loss note.

Refusals (returns None):

- Wrong event type/subtype, missing `event.ts`, missing `track_id`.
- `track_id` not a ULID and not resolved by the caller's `object_map` to
  a valid SAPIENT object ULID (ULID discipline above).
- Non-finite `lat`/`lon`. An incomplete geo that is missing `alt_m` and is
  not declared two-dimensional (`geo.dimensionality: "2D"`, doctrine
  A1-02): the ambiguous case where the vertical is unmeasured rather than
  nonexistent, and the adapter never invents the missing axis (contract
  6.8). A `"2D"` geo that also carries an `alt_m` (schema-incoherent — two
  claims that cannot both be true).
- `payload.extensions.risk_adjudication` containing a `QUARANTINE_ACCEPT`
  or `REJECTED` decision. Quarantine bounds the consumer set and a
  coalition SAPIENT feed is outside it (contract 3.3).
- Any risk record whose `policy_decision` is outside the governed
  vocabulary (`tools/filter_risk.py` DECISION_RANKS), including
  deployment-local labels contract 3.3 permits, or missing entirely.
  `filter_risk` ranks unknowns as `REJECTED` (fail closed) and this
  egress is never more permissive than the operator's own filter.
- Malformed fields (unparseable `ts`, non-finite or non-numeric
  coordinates, heading/speed, or confidence), refused per the None
  contract, never raised and never projected. "Non-finite" includes an
  integer too large for a float64: it has no form a SAPIENT float field
  can carry.
- An `event.ts` that parses but predates 1970. `report_id` is a ULID whose
  48-bit timestamp component is the event's own time, and that component
  cannot represent a negative epoch, so a pre-epoch instant (the
  canonical bad-clock symptom on an unsynced edge node) is refused rather
  than clamped to zero or backfilled from the wall clock, either of which
  would fabricate a time the event does not have. The upper bound is
  unreachable: 2^48 ms runs to year 10889.
- A non-finite or unserializable value inside an honesty self-label
  (`zmeta.risk`, `zmeta.timing_quality`); see below.
- Any risk record, or the caller-supplied `use_labels` dict, whose
  `prohibited_uses` include the export path, or whose `allowed_uses` grant
  list omits it (`export_use` kwarg, default `COALITION_EXPORT` from the
  contract 3.3 use-label vocabulary). Adjudication matches
  `tools/filter_risk.py` semantics.
- A `use_labels` argument that is not the documented dict shape (the
  natural mistake is a list of label dicts, since event-carried
  `risk_adjudication` records are a list). An export restriction the
  adapter cannot adjudicate fails closed like every other unadjudicable
  restriction here. A refusal is recoverable; a silently dropped
  prohibition is not.

Honesty self-labels (label rather than launder, contract 3.3): a soft-accepted
event exports WITH its context attached as `object_info` entries:

| `object_info.type` | Attached when | `value` |
| --- | --- | --- |
| `zmeta.risk` | Any `WARN_ACCEPT`/`DEGRADED_ACCEPT` record, any accepted record (e.g. `IGNORED`) carrying use restrictions, or caller `use_labels` carrying use restrictions | Compact JSON list of the use-constraining record fields |
| `zmeta.timing_quality` | `payload.timing_quality.sync_state` != `LOCKED` | Compact JSON of the full timing_quality object |

Stock SAPIENT DMMs ignore unknown `object_info` types, so the labels are
safe-to-ignore for consumers that cannot read them and filterable for those
that can. They are a projection of ZMeta's honesty context, not new
SAPIENT vocabulary.

Both label values are serialized with `allow_nan=False`. Python's default
would emit the bare tokens `NaN`/`Infinity`, which are not JSON
(RFC 8259 §6), and because a label rides as JSON *inside* a JSON string,
an outer `json.dumps(message, allow_nan=False)` over the whole message
cannot see them. If a label cannot be serialized honestly the **event is
refused**, not the label: `zmeta.timing_quality` is attached only when
`sync_state` != `LOCKED`, so it exists solely on the events whose
degradation it reports. Dropping it, or omitting just the corrupt
`est_error_ms` that contract §5.3/§5.9 says MUST NOT be omitted, would
export a detection with no degradation notice, which is precisely the
laundering the labels exist to prevent. ZMeta remains the source of truth;
only this lossy projection refuses.

ENU velocity: emitted only when both `heading_deg` and `speed_mps` are
present (`east_rate`/`north_rate` decomposed from the true-north heading,
contract 6.4). `up_rate` is always omitted, because ZMeta TrackStatePayload
carries no climb rate and an absent optional field is SAPIENT's honest
"unknown". An up-rate is never fabricated.

State lossiness (`SAPIENT_EGRESS_LOSS_NOTES` in
`zmeta_state_to_sapient_detection.py` is the machine-readable register):

| ZMeta concern | Disposition |
| --- | --- |
| `lineage` | Dropped; DetectionReport has no lineage carrier. |
| `payload.timing_quality` | Only surfaces as the `zmeta.timing_quality` self-label when degraded; a clean LOCKED claim does not export. |
| `risk_adjudication` | Warn/degrade records travel only as the `zmeta.risk` self-label; quarantined/rejected events are refused. |
| `payload.valid_for_ms` | Dropped; DetectionReport has no TTL/stale field; SAPIENT consumers apply their own aging. |
| `payload.source_summary` | Dropped. |
| `geo.error_ellipse_m` | Dropped; per-axis `x/y/z_error` scalars cannot carry an oriented ellipse honestly. |
| `payload.stability`, `payload.last_seen_ts` | Dropped. |
| `payload.extensions` (other) | Dropped; not re-exported across an external boundary. |

ZMeta remains the source of truth; these projections are one-directional in
authority and a re-import of either is never equal to the original
(contract 4.5.1).

### Smoke test

```
python - <<'PY'
from adapters.egress.sapient.zmeta_command_to_sapient_task import zmeta_command_to_sapient_task
from adapters.egress.sapient.zmeta_state_to_sapient_detection import zmeta_state_to_sapient_detection

command = {
  "event": {"event_type": "COMMAND_EVENT", "event_subtype": "GOTO", "ts": "2026-07-17T12:00:00Z"},
  "payload": {
    "task_id": "01ARZ3NDEKTSV4RRFFQ69G5FAV",
    "task_type": "GOTO",
    "target_geo": {"lat": 34.0, "lon": -118.0},
    "valid_for_ms": 600000,
    "requires_deconfliction": True
  }
}
print(zmeta_command_to_sapient_task(
    command,
    node_id="0f2c8b4e-9f1d-4e6a-8a3b-1c5d7e9f0a2b",
    destination_id="7a1b3c5d-2e4f-4a6b-8c0d-9e1f3a5b7c9d",
))

state = {
  "event": {"event_type": "STATE_EVENT", "event_subtype": "TRACK_STATE", "ts": "2026-07-17T12:00:00Z"},
  "payload": {
    "track_id": "01BX5ZZKBKACTAV9WEVGEMMVRZ",
    "geo": {"lat": 34.0, "lon": -118.0, "alt_m": 120.0},
    "class": "UAV",
    "valid_for_ms": 5000
  },
  "confidence": 0.8
}
print(zmeta_state_to_sapient_detection(state, node_id="0f2c8b4e-9f1d-4e6a-8a3b-1c5d7e9f0a2b"))
PY
```

## Track identity: `object_map` is required for non-ULID track ids

`object_id` is caller-owned identity. A `track_id` that is already a ULID passes
through unchanged; anything else must resolve through `object_map` to a
caller-owned SAPIENT ULID, or the event is refused and no detection is emitted.

That refusal is deliberate. Minting a fresh identity per report would shred
track continuity on the SAPIENT side, where `object_id` is what makes successive
reports the same object.

It has a practical consequence worth stating, because it is not obvious until an
export silently produces nothing: identifiers from `adapters/projector/track` are
broadcast-shaped by design (`icao24-a1b2c3`, `mmsi-366123456`), so a deployment
bridging those tracks to SAPIENT owns and supplies the mapping.

```python
zmeta_state_to_sapient_detection(
    state, node_id=NODE_UUID,
    object_map={"icao24-a1b2c3": "01JQ0000000000000000000001"})
```

## What a SAPIENT consumer does not receive

`SAPIENT_EGRESS_LOSS_NOTES` in the module enumerates the ZMeta fields this
projection drops and why. One thing it does not enumerate, because the register
tracks dropped ZMeta fields rather than unfilled SAPIENT ones: **this projection
emits `classification[].confidence` and never `detection_confidence`.** A ZMeta
event carries a single `confidence`, and projecting it into both slots would
assert a detection-existence claim the event never made.
