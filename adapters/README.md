# Adapters Overview

Reference adapters demonstrate how to translate between ZMeta and external systems.
They are intentionally minimal and may be lossy.

- Ingress adapters: `adapters/ingress/`
- Mapping packs: `adapters/mapping-packs/`
- Egress projections: `adapters/egress/` (CoT, MissionIntent, JREAP)

## Semantic Mapping Rules

Adapters must preserve ZMeta layer separation:

| Native output | ZMeta event type | Notes |
|---|---|---|
| Raw sensor measurement, packet metadata, RF bearing, EO/IR/ACOUSTIC/NETWORK facts | OBSERVATION_EVENT | Do not add classification, track identity, or fused state. |
| Classifier, detector, anomaly, behavior, or association output | INFERENCE_EVENT | Include confidence and lineage; do not emit `track_id`. |
| Track association, track creation, or multi-source fusion | FUSION_EVENT | Fusion nodes assign and preserve `track_id`. |
| Operator-facing display/state projection | STATE_EVENT | Keep compact; do not include raw sensor features. |
| Mission cueing or retasking | COMMAND_EVENT | Must pass through deconfliction and must not specify altitude. |
| Timing, link, health, schema violation, or task acknowledgement | SYSTEM_EVENT | Use the matching `event_subtype` / payload discriminator. |

Native producer quirks belong in adapter-local code, mapping packs, or
namespaced payload extensions that downstream consumers can ignore. They must
not alter event meaning, units, lineage, authority boundaries, profile behavior,
or command safety.

## Ingress Adapters

| Adapter | Input | ZMeta Output | Status |
|---------|-------|--------------|--------|
| [MAVLink](ingress/mavlink/) | MAVLink v2 telemetry (GLOBAL_POSITION_INT, ATTITUDE, SYS_STATUS, etc.) | STATE_EVENT, SYSTEM_EVENT | Production |
| [KrakenSDR](ingress/kraken/) | KrakenSDR DOA CSV / HTTP / JSON replay | OBSERVATION_EVENT (RF LOB) | Production |
| [Moth](ingress/moth/) | Moth serial CSV/JSON, MAVLink TUNNEL, custom dialect | OBSERVATION_EVENT (RF LOB) | Production |
| [SignalHunter](ingress/signalhunter/) | SignalHunter .bin PSD captures | OBSERVATION_EVENT (RF LOB, gradient) | Production |
| [EO-CV](ingress/eo-cv/) | CV inference service JSON detections | INFERENCE_EVENT (CLASSIFICATION) | Production |
| [CoT](ingress/cot/) | Cursor-on-Target XML | (template) | Template |
| [KLV](ingress/klv/) | MISB KLV metadata | (template) | Template |

Each adapter implements the standard `detect()` / `translate()` / `validate()`
pattern described in `ingress/template/README.md`.

Ingress adapters normalize timestamp inputs to the schema-required UTC `Z`
format before emission. Operational events also carry explicit fallback
`payload.timing_quality` when the source stream does not provide a better timing
authority; deployments with GPS/NTP/PTP timing should supply those stronger
values or emit `TIME_STATUS` from the same source tuple.

Fallback timing is intentionally degraded timing. `time_source: UNKNOWN` and
`sync_state: UNSYNCED` prove that timing quality was exposed, but operators and
fusion consumers should treat it as a bridge until source-provided GPS/NTP/PTP
timing or periodic `TIME_STATUS` is available.

Adapter modules use package-style imports from the repository root, including
`from adapters.ingress.time_utils import ...`. Run tests and integration scripts
from the repo root, or install/add the repo root on `PYTHONPATH`, so shared
adapter helpers resolve consistently. Direct execution from an adapter
subdirectory is not the supported invocation style.

Supported invocation patterns:

```
python -m pytest adapters
python tools/check_compat.py examples/zmeta-v1.1-examples.jsonl --target v1.1.4
PYTHONPATH=. python adapters/ingress/<adapter>/<script>.py
```

Avoid `cd adapters/ingress/<adapter>` followed by direct script execution unless
the script explicitly adjusts imports; that bypasses the repository root package
context used by shared helpers.
