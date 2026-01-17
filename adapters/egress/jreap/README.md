## ZMeta State to JREAP Track (Reference)

This adapter produces a minimal JSON "tactical track" projection for a downstream
JREAP gateway. It is NOT a Link-16/JREAP encoder.

Input: ZMeta STATE_EVENT/TRACK_STATE
Output: minimal tactical track JSON

Notes:
- This is a lossy projection: lineage dropped, confidence optional, limited taxonomy.
- A program-of-record JREAP gateway handles real formatting and transport.

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
