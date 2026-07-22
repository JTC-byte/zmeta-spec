## ZMeta State to JREAP Track (Reference)

Overview: see `adapters/README.md`.

This adapter produces a minimal JSON "tactical track" projection for a downstream
JREAP gateway. It is NOT a Link-16/JREAP encoder.

Input: ZMeta STATE_EVENT/TRACK_STATE
Output: minimal tactical track JSON

Notes:
- This is a lossy projection: ZMeta input requires confidence and lineage for
  STATE_EVENT, but the downstream tactical track JSON may omit lineage and may
  carry confidence only when the receiving gateway supports it.
- A program-of-record JREAP gateway handles real formatting and transport.

### Refusals (`None`) — fail closed, never substitute

| Condition | Disposition |
|-----------|-------------|
| Not a `STATE_EVENT` / `TRACK_STATE`, or missing `track_id`/`geo`/`ts`/`valid_for_ms` | refused |
| Non-finite (`NaN`/`inf`) number anywhere in the projected track | refused — a consumer would plot a symbol at a non-position, and the JSON handed to it would not be RFC 8259 |
| `time + valid_for_ms` not representable as a datetime | refused — `payload.valid_for_ms` is `{"type": "integer", "minimum": 1}` with no upper bound, so the kernel forwards windows the `datetime` module cannot express (`10**400` ms, `10**15` ms, or an ordinary 300 000 ms window on `ts="9999-12-31T23:59:59Z"`) |

The refusal is a refusal, not a repair: nothing is emitted with a substituted
`stale_time`, because a freshness bound the event never claimed is exactly the
kind of clean-looking value a consumer cannot filter on.

The non-finite walk covers containers by abstract type (`Mapping`, `Set`,
`Sequence`, CBOR tag wrappers, `Decimal`), not just `dict`/`list`, and carries
a seen-set so a cyclic structure — reachable via CBOR value-sharing tags on a
`cbor2`-only install — terminates instead of hanging the egress path.

### Smoke test

```
python - <<'PY'
from adapters.egress.jreap.zmeta_state_to_jreap_track_json import zmeta_state_to_jreap_track_json

event = {
  "event": {"event_type": "STATE_EVENT", "event_subtype": "TRACK_STATE", "ts": "2025-01-17T15:20:00Z"},
  "payload": {
    "track_id": "track-1",
    "geo": {"lat": 34.0, "lon": -118.0, "alt_m": 120.0},
    "valid_for_ms": 1000
  },
  "confidence": 0.8
}
print(zmeta_state_to_jreap_track_json(event))
PY
```
