# Config Templates

These configs are intended to be edited and used directly by the edge/gateway services.

- `edge-config.json` - Profile L edge relay (forward-only, no CoT emission).
- `edge-config-profile-L-lean.json` - Optional lean Profile L preset (compact + optional-field stripping).
- `gateway-config.json` - Gateway validator + CoT emission.
- `gateway-config-strict.json` - Strict validation preset (warnings treated as failures).

When to use the lean Profile L config:
- Use `edge-config-profile-L-lean.json` for bandwidth-constrained links where size budgets matter.
- Use `edge-config.json` when you want full Profile L fidelity (e.g., keep confidence/lineage/data_ref).

Notes:
- `schema_path` and `policy_dir` are resolved relative to the config file location.
- Replace `GATEWAY_HOST` in `edge-config.json` with the actual gateway IP/hostname.
- MVP roles: `sensorops` runs comms + edge export; `torch` runs gateway fusion/retasking.
- Debug/optimization controls:
  - `stamp_profile` and `stamp_profile_profiles` control when `profile` is stamped.
  - `stamp_timing` and `stamp_timing_profiles` control gateway `t_receive`/`t_publish` stamps.
  - `strip_optional_fields` and `strip_optional_fields_profiles` remove optional fields
    for bandwidth efficiency.
  - `strict_validation` treats warnings as failures (no forward).
  - `emit_metrics` and `metrics_interval_sec` control periodic gateway metrics logs.
  - `rate_limit_per_sec` drops packets above the configured receive rate.
  - `rate_limit_producer_per_sec` drops packets per producer above the configured rate.
  - `metrics_log_path`, `metrics_log_max_bytes`, `metrics_log_backups` enable JSONL metrics logs.
  - `stamp_contract_hash` adds schema/policy hashes to gateway‑generated system events.
  - `require_schema_hash`, `require_policy_hash`, `require_contract_hash` gate startup on expected hashes.
- Encoding controls:
  - `input_encoding`: `json`, `cbor`, `compact`, or `auto`.
  - `output_encoding`: `json`, `cbor`, or `compact`.
  - `compact` is a CBOR-based integer-key mapping for Profile L links.
  - CBOR requires `cbor2` or the built-in `zmeta_cbor` fallback.

Contract hash utility:

```
python tools/compute_contract_hash.py
```

## Profile L Lean Preset (Optional)

If you need Profile L STATE_EVENT packets under ~200 bytes, use compact encoding
and omit non-essential optional fields at the producer. Gateway stripping only
reduces outbound size, not the inbound link payload.

Suggested preset snippet (apply on the producer/edge that emits Profile L):

```
{
  "profile": "L",
  "output_encoding": "compact",
  "strip_optional_fields": [
    "source.sensor_id",
    "source.sw_version",
    "payload.data_ref",
    "payload.data_refs",
    "payload.quality",
    "payload.source_summary",
    "payload.heading_deg",
    "payload.speed_mps",
    "payload.class",
    "confidence",
    "lineage"
  ],
  "strip_optional_fields_profiles": ["L"]
}
```

Gating rules:
- Keep all required schema fields (event block + core payload fields).
- Only strip `payload.data_ref(s)` if you do not rely on out-of-band retrieval.
- Keep `confidence`/`lineage` if needed for AAR or fusion traceability.
