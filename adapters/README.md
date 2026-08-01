# Adapters Overview

Reference adapters demonstrate how to translate between ZMeta and external systems.
They are intentionally minimal and may be lossy.

- Ingress adapters: `adapters/ingress/`
- Mapping packs: `adapters/mapping-packs/`
- Egress projections: `adapters/egress/` (CoT, MissionIntent, JREAP, KLV, SAPIENT)
- Projectors: `adapters/projector/` (ZMeta in, ZMeta out)

Building a new adapter? Start with the step-by-step authoring guide:
`adapters/AUTHORING.md`.

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
| [CoT](ingress/cot/) | Cursor-on-Target XML | STATE_EVENT (promotion) | Template |
| [JREAP](ingress/jreap/) | Decoded JREAP/Link-style track dicts | STATE_EVENT (promotion) | Template |
| [KLV](ingress/klv/) | MISB KLV metadata | OBSERVATION_EVENT (EO) | Template |
| [SAPIENT](ingress/sapient/) | BSI Flex 335 v2.0 SapientMessage dicts (protobuf-JSON) | OBSERVATION_EVENT, INFERENCE_EVENT, STATE_EVENT (promotion), SYSTEM_EVENT | Reference |
| [bladeRF EW](ingress/bladerf/) | edge-comms bladeRF / ROS2 EW `rf_detection` JSON (`edge-comms-bladerf` pack) | OBSERVATION_EVENT (RF) | Reference |
| [ADS-B](ingress/adsb/) | `dump1090` / `readsb` `aircraft.json` (RTL-SDR, any decoder `adsbcot` supports) | OBSERVATION_EVENT (NETWORK) | Reference |
| [AIS](ingress/ais/) | Decoded AIS position reports (AIS-catcher JSON, same RTL-SDR dongle) | OBSERVATION_EVENT (NETWORK) | Reference |
| [Example-vendor](ingress/example-vendor/) | `example-vendor-pack` RF JSON | OBSERVATION_EVENT (RF) | Worked exercise |

## Projectors

ZMeta in, ZMeta out. Neither ingress nor egress: these sit between an adapter
and a consumer and change what an event *is*, not what format it is in.

| Projector | Input | Emits | Status |
|---|---|---|---|
| [Track](projector/track/) | `OBSERVATION_EVENT` whose subject broadcasts an identity (ADS-B `icao24`, AIS `mmsi`) | `FUSION_EVENT` + `STATE_EVENT` | Reference |

Why this category exists: CoT projects `STATE_EVENT` only, so an ingress adapter
alone puts ZMeta on the wire and nothing on a COP. Where identity must be
inferred that gap is a real tracker and stays consumer-side by design. Where the
subject broadcasts its own identity it is not, and the track projector closes it.

Status legend: **Production**: exercised against real sensor data.
**Template**: copy-me starting point, structurally complete.
**Reference**: complete implementation validated against the external
standard's official tooling or a mapping pack's real-capture corpus, not
yet fielded against live hardware.
**Worked exercise**: teaching implementation paired with the authoring
guide.

Real raw→ZMeta corpus for adapter authors (bladeRF edge-comms detections):
[`mapping-packs/edge-comms-bladerf/`](mapping-packs/edge-comms-bladerf/);
its reference implementation is [`ingress/bladerf/`](ingress/bladerf/).

Each adapter ships documented entry points plus colocated tests, and its
output is checked by the canonical validator; `ingress/template/README.md`
describes the convention. Entry-point names follow the input's shape
(`translate_message`, `translate_snapshot`, `translate_stream`) rather than
a fixed function trio.

Representative adapter outputs are checked by the shared conformance harness:

```
python tools/validate_adapter_conformance.py --fixtures conformance/adapter-harness/must-pass.jsonl
```

The harness validates schema/policy output, semantic layer separation, UTC-Z
timestamp normalization, adapter lineage transforms, declared fallback timing,
and external promotion evidence for CoT/JREAP/MAVLink state projections.

Ingress adapters normalize timestamp inputs to the schema-required UTC `Z`
format before emission. Operational events also carry explicit fallback
`payload.timing_quality` when the source stream does not provide a better timing
authority; deployments with GPS/NTP/PTP timing should supply those stronger
values or emit `TIME_STATUS` from the same source tuple.

Fallback timing is intentionally degraded timing. `time_source: UNKNOWN` and
`sync_state: UNSYNCED` prove that timing quality was exposed, but operators and
fusion consumers should treat it as a bridge until source-provided GPS/NTP/PTP
timing or periodic `TIME_STATUS` is available.

## Frame Assertions And Anti-Fabrication

Canonical bearings and headings are degrees true north. Adapters must convert
sensor-native frames before canonical emission or preserve native values under
explicitly named non-canonical fields.

For v1.1.8 and later:

- Moth tunnel/replay callers must pass `bearing_frame="TRUE_NORTH"` before
  those bearings are emitted as canonical `payload.bearing`.
- MAVLink platform-state callers must pass `heading_frame="TRUE_NORTH"` before
  `GLOBAL_POSITION_INT.hdg` is emitted as canonical `payload.heading_deg`.
- Kraken callers must provide `platform_heading_deg` before array-relative DOA
  is converted to canonical `payload.bearing`.
- Kraken CSV input does not provide a noise floor; `quality.snr_db` is omitted
  instead of fabricated from RSSI.

Frame markers and heading-source fields are provenance assertions by the
producer or adapter configuration. They are not signatures, credentials,
calibration proofs, or independent verification that a true-north assertion is
correct. Treat them as inputs to trust and deployment policy, not as proof.

External tactical track ingress is also an authority boundary. The CoT, JREAP,
and MAVLink state templates and the SAPIENT fusion-node ingress emit
policy-scoped `payload.extensions.external_promotion` metadata and `promote:*`
lineage transforms so reference producer-authority policy can distinguish
promoted external reports from native ZMeta state. Schema validity alone is not
promotion authority. The `trust_ref` value is an asserted policy reference for
promotion adjudication, not a signature, credential, or standalone proof of
authenticity.

Adapter modules use package-style imports from the repository root, including
`from adapters.ingress.time_utils import ...`. Run tests and integration scripts
from the repo root, or install/add the repo root on `PYTHONPATH`, so shared
adapter helpers resolve consistently. Direct execution from an adapter
subdirectory is not the supported invocation style.

Supported invocation patterns:

```
python -m pytest adapters
python tools/check_compat.py examples/zmeta-v1.1-examples.jsonl --target v1.1.19
PYTHONPATH=. python adapters/ingress/<adapter>/<script>.py
```

Avoid `cd adapters/ingress/<adapter>` followed by direct script execution unless
the script explicitly adjusts imports; that bypasses the repository root package
context used by shared helpers.
