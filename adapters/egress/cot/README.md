## ZMeta to CoT (Reference)

Overview: see `adapters/README.md`.

This is a reference egress adapter that converts ZMeta STATE_EVENT/Track State
into CoT XML for interoperability.

Notes:
- CoT type taxonomy is configurable later; the adapter uses a placeholder by default.
- The conversion is intentionally lossy (e.g., lineage is dropped).
- Uncertainty rings are optional; radius can be derived from confidence or future pos_err_m.

### Mapping Sanity (Reference)

- Only `STATE_EVENT` with subtype `TRACK_STATE` is mapped.
- `event.ts` -> CoT `time`/`start`.
- `payload.valid_for_ms` -> CoT `stale` (time + valid_for_ms).
- `payload.track_id` -> CoT `uid`.
- `payload.class` -> CoT `type` (falls back to default).
- `payload.geo.lat/lon/alt_m` -> CoT `point` (`lat`, `lon`, `hae`).
- `confidence` and `payload.source_summary` -> CoT `<detail><remarks>`.
