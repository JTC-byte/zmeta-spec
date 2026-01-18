## ZMeta to CoT (Reference)

Overview: see `adapters/README.md`.

This is a reference egress adapter that converts ZMeta STATE_EVENT/Track State
into CoT XML for interoperability.

Notes:
- CoT type taxonomy is configurable later; the adapter uses a placeholder by default.
- The conversion is intentionally lossy (e.g., lineage is dropped).
- Uncertainty rings are optional; radius can be derived from confidence or future pos_err_m.
