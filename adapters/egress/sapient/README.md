## ZMeta to SAPIENT (BSI Flex 335 v2.0) Egress (Reference)

Overview: see `adapters/README.md`. Ingress counterpart:
`adapters/ingress/sapient/`.

Two projections into proto3-JSON-shaped SapientMessage dicts (snake_case).
Neither is a protobuf wire encoder — a downstream SAPIENT transport encodes
the dicts (consistent with the JREAP/KLV egress projections). Both stamp the
envelope `timestamp` from the event's own `event.ts`, never the wall clock.

- `zmeta_command_to_sapient_task.py`: COMMAND_EVENT -> Task
- `zmeta_state_to_sapient_detection.py`: STATE_EVENT/TRACK_STATE -> DetectionReport

### Command projection (COMMAND_EVENT -> Task)

Command safety rules (semantics contract 7.8) dominate this projection:

- Only deconflicted commands cross: `requires_deconfliction: true` or the
  event is refused (returns None).
- Only three task types have an honest SAPIENT `Task.Command` verb:

  | ZMeta task_type | SAPIENT command | Notes |
  | --- | --- | --- |
  | `GOTO` | `move_to` | One 2D `Location` (`x`=lon, `y`=lat, `LAT_LNG_DEG_M`, `WGS84_E`). `z` is never populated. |
  | `TRACK_TARGET` | `follow` | `follow_object_id` resolved through the caller's `track_to_object` map; an unmapped target is refused, never fabricated. |
  | `CHANGE_SENSOR_MODE` | `mode_change` | `payload.sensor_mode` string as-is. |

- Everything else (`ORBIT`, `HOLD`, `SEARCH_BOX`, `LOITER`, `SCAN_RF`,
  `RETURN_TO_BASE`, `LAND`) returns None — documented residue. SAPIENT
  region tasking and discrete thresholds cannot carry their semantics
  without reinterpreting what the receiving node is asked to do, and this
  adapter never emits region/threshold commands.
- Altitude never crosses. A `target_geo` carrying an altitude field raises
  `ValueError` (mirroring the MAVLink mission-intent guard), and the output
  `Location` is built field-by-field from lat/lon only, so
  altitude-adjacent keys hiding in `extensions` cannot leak.
- `task_end_time` = `event.ts` + `payload.valid_for_ms` (the ZMeta TTL is
  the only honest task bound available).
- `destination_id` is a required caller kwarg — a SAPIENT task without a
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

Refusals (returns None):

- Wrong event type/subtype, missing `event.ts`, missing `track_id`.
- Partial geo: `lat`, `lon`, and `alt_m` must all be present — SAPIENT `z`
  is an explicit claim and the location oneof is mandatory, so a partial
  position cannot cross without inventing an axis (contract 6.8).
- `payload.extensions.risk_adjudication` containing a `QUARANTINE_ACCEPT`
  or `REJECTED` decision — quarantine bounds the consumer set and a
  coalition SAPIENT feed is outside it (contract 3.3).
- Any risk record — or the caller-supplied `use_labels` dict — whose
  `prohibited_uses` include the export path, or whose `allowed_uses` grant
  list omits it (`export_use` kwarg, default `COALITION_EXPORT` from the
  contract 3.3 use-label vocabulary). Adjudication matches
  `tools/filter_risk.py` semantics.

Honesty self-labels (label, don't launder — contract 3.3): a soft-accepted
event exports WITH its context attached as `object_info` entries:

| `object_info.type` | Attached when | `value` |
| --- | --- | --- |
| `zmeta.risk` | Any `WARN_ACCEPT`/`DEGRADED_ACCEPT` record, or caller `use_labels` carrying use restrictions | Compact JSON list of the use-constraining record fields |
| `zmeta.timing_quality` | `payload.timing_quality.sync_state` != `LOCKED` | Compact JSON of the full timing_quality object |

Stock SAPIENT DMMs ignore unknown `object_info` types, so the labels are
safe-to-ignore for consumers that cannot read them and filterable for those
that can. They are a projection of ZMeta's honesty context, not new
SAPIENT vocabulary.

ENU velocity: emitted only when both `heading_deg` and `speed_mps` are
present (`east_rate`/`north_rate` decomposed from the true-north heading,
contract 6.4). `up_rate` is always omitted — ZMeta TrackStatePayload
carries no climb rate and an absent optional field is SAPIENT's honest
"unknown". No fabricated up-rate, ever.

State lossiness (`SAPIENT_EGRESS_LOSS_NOTES` in
`zmeta_state_to_sapient_detection.py` is the machine-readable register):

| ZMeta concern | Disposition |
| --- | --- |
| `lineage` | Dropped; DetectionReport has no lineage carrier. |
| `payload.timing_quality` | Only surfaces as the `zmeta.timing_quality` self-label when degraded; a clean LOCKED claim does not export. |
| `risk_adjudication` | Warn/degrade records travel only as the `zmeta.risk` self-label; quarantined/rejected events are refused. |
| `payload.valid_for_ms` | Dropped; DetectionReport has no TTL/stale field — SAPIENT consumers apply their own aging. |
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
    "task_id": "task-1",
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
    "track_id": "trk-9",
    "geo": {"lat": 34.0, "lon": -118.0, "alt_m": 120.0},
    "class": "UAV",
    "valid_for_ms": 5000
  },
  "confidence": 0.8
}
print(zmeta_state_to_sapient_detection(state, node_id="0f2c8b4e-9f1d-4e6a-8a3b-1c5d7e9f0a2b"))
PY
```
