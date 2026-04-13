# Adapters Overview

Reference adapters demonstrate how to translate between ZMeta and external systems.
They are intentionally minimal and may be lossy.

- Ingress adapters: `adapters/ingress/`
- Mapping packs: `adapters/mapping-packs/`
- Egress projections: `adapters/egress/` (CoT, MissionIntent, JREAP)

## Ingress Adapters

| Adapter | Input | ZMeta Output | Status |
|---------|-------|--------------|--------|
| [MAVLink](ingress/mavlink/) | MAVLink v2 telemetry (GLOBAL_POSITION_INT, ATTITUDE, SYS_STATUS, etc.) | STATE_EVENT, SYSTEM_EVENT | Production |
| [KrakenSDR](ingress/kraken/) | KrakenSDR DOA CSV / HTTP / JSON replay | OBSERVATION_EVENT (RF LOB) | Production |
| [Moth](ingress/moth/) | Moth serial CSV/JSON, MAVLink TUNNEL, custom dialect | OBSERVATION_EVENT (RF LOB) | Production |
| [SignalHunter](ingress/signalhunter/) | SignalHunter .bin PSD captures | OBSERVATION_EVENT (RF LOB, gradient) | Production |
| [EO-CV](ingress/eo-cv/) | CV inference service JSON detections | OBSERVATION_EVENT (EO) | Production |
| [CoT](ingress/cot/) | Cursor-on-Target XML | (template) | Template |
| [KLV](ingress/klv/) | MISB KLV metadata | (template) | Template |

Each adapter implements the standard `detect()` / `translate()` / `validate()`
pattern described in `ingress/template/README.md`.
