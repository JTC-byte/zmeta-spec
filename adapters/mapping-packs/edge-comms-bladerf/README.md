# Edge-comms bladeRF mapping pack

Example corpus for adapter authors: two real `rf_detection` records from an
edge-comms bladeRF / ROS2 EW flight blackbox, paired with schema-valid ZMeta
v1.0 RF `OBSERVATION_EVENT` expected outputs.

## Provenance

| Field | Value |
| --- | --- |
| Source archive | Z-ISR `flight-artifacts-2026-05-14_v22rfpayload-edge-comms` |
| Recording | `edge-comms-believer-data/recordings/2026-05-14_130201/blackbox_141233.jsonl` |
| Native category | `rf_detection` |
| Sensor | bladeRF EW (`sensor_hw: bladerf`, `zmeta_sensor_id: bladerf_ew`) |

These are structured detections (freq, power, SNR, bearing metadata), not raw
IQ. They are enough for authors to validate a translator against governed
ZMeta shape and honesty rules.

## Cases

| Case | Native product | Center freq | Notes |
| --- | --- | --- | --- |
| `tests/case-01-vhf-orbit/` | `sdr/orbit_spectrum` | 138.2 MHz | `bearing_source: none`; canonical bearing omitted |
| `tests/case-02-cband-fft/` | `spectrum_fft` | 5.2475 GHz | `bearing_source: heading_at_peak`; native bearing kept in features; canonical bearing omitted (no frame assertion, see below) |

Sensor geo on this flight was unavailable (null or null-island). Expected
events omit `payload.geo` and set `quality.geo_status: UNAVAILABLE` rather
than inventing coordinates (contract 6.8).

Canonical bearing is omitted in BOTH cases (maintainer review, PR #7):
the native bearing is heading-derived (uas heading plus a fixed antenna
offset) and the source's `heading_source: "interpolated"` names a
sampling method rather than a reference frame, and nothing in the capture
asserts true north. Per contract 6.4 and `adapters/AUTHORING.md` rule 2 the
values travel as `features.native_bearing_deg` /
`features.native_bearing_error_deg` (the raw error bound declares no
statistical metric, so no `quality.measurement_error` is claimed). A
deployment that can assert its heading reference may emit
`payload.bearing` with `quality.bearing_frame: TRUE_NORTH` +
`quality.heading_source`, mirroring the kraken reference adapter.

Two native conventions worth knowing: case-02's `bandwidth_hz: 7500.0`
is the FFT bin width (`sample_rate_hz / fft_size`), a resolution
artifact the source reports rather than a measured emitter bandwidth;
and `features.timestamp_source` preserves whether `event.ts` came from
embedded telemetry (case-02) or adapter receive time (case-01, where the
degraded 60 s `est_error_ms` bound covers that path).

Original detections have no ZMeta parent, so expected events omit `lineage`
(contract 4.8). See `mapping.yaml` for the transform stamp to use when real
parent ids are available.

## How to use

1. Read `tests/<case>/input.json` as the native detection payload.
2. Implement `detect` / `translate` / `validate` per `adapters/AUTHORING.md`.
3. Diff your translator output against `tests/<case>/expected.json` (ignore
   generated `event_id` if you mint new UUIDv7s at runtime).

Reference implementation: `adapters/ingress/bladerf/` carries out this
mapping as runnable adapter code (colocated tests reproduce both expected
outputs exactly; harness fixtures are the `bladerf-` entries in
`conformance/adapter-harness/must-pass.jsonl`). Diff your own adapter
against it the way `adapters/ingress/example-vendor/` pairs with its pack.
4. Validate expected events:

```powershell
python tools\validate.py --file adapters\mapping-packs\edge-comms-bladerf\tests\case-01-vhf-orbit\expected.json --profile H
python tools\validate.py --file adapters\mapping-packs\edge-comms-bladerf\tests\case-02-cband-fft\expected.json --profile H
```

`platform_id` is deployment-supplied; fixtures use `uav-believer-01-bladerf`
from the flight identity. Expected events use producer `rf-sensor-bladerf`
(matches the reference `rf-sensor-*` producer-authority pattern).
