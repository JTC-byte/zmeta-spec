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
- Declared 2-D geo (doctrine A1-02) projects honestly: a `payload.geo` with
  `dimensionality: "2D"` (a real, exact horizontal fix with no geometric
  vertical to assert, ever — every AIS vessel, a barometric-only aircraft)
  produces `hae_m: null`, never a fabricated altitude. This adapter has no
  all-or-nothing altitude wall the way the SAPIENT egress once did (fixed
  2026-08, first independent SAPIENT interop run, MAJOR): it reads
  `alt_m` directly and always projected a 2-D fix rather than dropping it.
  What it did lack, until the same sweep tightened it, is telling a genuine
  2-D declaration apart from the schema-invalid shape a real gateway would
  already reject — `alt_m` absent with no explicit `"2D"` token — which
  produced the identical `hae_m: null` track. Only the explicit token earns
  the no-altitude disposition now; the untelled-apart shape refuses (see the
  table below), and a `"2D"` token paired with a present `alt_m` refuses too
  (schema-incoherent — two claims that cannot both be true).

### Refusals (`None`): fail closed, never substitute

| Condition | Disposition |
|-----------|-------------|
| Not a `STATE_EVENT` / `TRACK_STATE`, or missing `track_id`/`geo`/`ts`/`valid_for_ms` | refused |
| `alt_m` absent and `geo.dimensionality` is not `"2D"` | refused; the ambiguous case (unmeasured vs. nonexistent vertical), schema-invalid upstream, so a real gateway never hands it to this egress |
| `geo.dimensionality: "2D"` together with a present `alt_m` | refused; schema-incoherent, never picks one claim to believe |
| `event.ts` unparseable or not UTC-convertible (non-string, calendar/clock-invalid, or a naive pre-1970 instant the platform rejects) | refused; on the locked v1.0 branch the schema's `utcDateTime` enforces only a trailing `Z` (`format: date-time` is advisory without an RFC 3339 checker); the v1.1.0 branch tightens the pattern to structural calendar shape instead (year/month/day/hour/minute/second ranges, doctrine X1-01), but neither is a full calendar validator, so `"2026-02-30T00:00:00Z"` still arrives gate-clean on both branches; the timestamp keys both `timestamp` and `stale_time`, and a substituted instant would be a freshness claim the event never made |
| Non-finite (`NaN`/`inf`) number anywhere in the projected track | refused; a consumer would plot a symbol at coordinates that are not a position, and the JSON handed to it would not be RFC 8259 |
| `time + valid_for_ms` not representable as a datetime | refused; `payload.valid_for_ms` is `{"type": "integer", "minimum": 1}` with no upper bound, so the kernel forwards windows the `datetime` module cannot express (`10**400` ms, `10**15` ms, or an ordinary 300 000 ms window on `ts="9999-12-31T23:59:59Z"`) |

A refusal is not a repair: nothing is emitted with a substituted
`stale_time`, because a freshness bound the event never claimed is exactly the
kind of clean-looking value a consumer cannot filter on.

The non-finite walk covers containers by abstract type (`Mapping`, `Set`,
`Sequence`, CBOR tag wrappers, `Decimal`), not just `dict`/`list`, and carries
a seen-set so a cyclic structure, reachable via CBOR value-sharing tags on a
`cbor2`-only install, terminates instead of hanging the egress path.

### Loss notes

This projection is lossy beyond the refusals above: several STATE_EVENT
concerns have no carrier in the minimal tactical track JSON at all, and are
silently absent rather than refused (`JREAP_EGRESS_LOSS_NOTES` in
`zmeta_state_to_jreap_track_json.py` is the machine-readable register):

| ZMeta concern | Disposition |
| --- | --- |
| `geo.error_ellipse_m` | Dropped; the minimal tactical track JSON has no uncertainty carrier. The CoT egress projects the same field; the SAPIENT egress documents dropping it in its own register. |
| `lineage` | Dropped; no lineage carrier. Recover provenance through the originating ZMeta event. |
| `payload.timing_quality` | Dropped; no timing carrier. |
| `payload.source_summary`, `heading_deg`, `speed_mps`, `callsign` | Dropped; this adapter projects only `track_id`, position, altitude, timestamp, stale time, track type, and confidence. |
| `payload.extensions` | Dropped; not re-exported across an external boundary. |

ZMeta remains the source of truth; this projection is one-directional in
authority and a re-import of it is never equal to the original (semantics
contract 4.5.1). What the adapter emits is unchanged; this section only
documents what was already true.

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
