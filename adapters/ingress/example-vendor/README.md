# Example-Vendor Ingress Adapter (Worked Exercise)

Status: reference / teaching. This is the runnable answer key for the
authoring guide (`adapters/AUTHORING.md`): it implements the declarative
`adapters/mapping-packs/example-vendor-pack` mapping as real adapter code.
Per `adapters/mapping-packs/README.md`, no runtime engine executes
`mapping.yaml`; the pack describes the field mapping; hand-written adapter
code like this carries it out.

Input (schema_id `vendor:example_rf:v1`): a flat JSON RF reading:
`{platform_id, sensor_id, ts, lat, lon, alt_hae_m, center_freq_hz, bandwidth_hz,
power_dbm}`. Output: one `OBSERVATION_EVENT` / `RF`.

## What to learn from the diff against the pack fixture

The pack's `tests/expected.json` shows only the field mapping. The adapter
adds the semantic obligations the contract puts on every producer, which is
exactly the gap a new author must close:

- contract-required `payload.timing_quality`, using the deliberately degraded
  `coerce_timing_quality()` fallback unless the caller supplies real
  GPS/NTP/PTP metadata;
- a fresh UUIDv7 `event_id` per emission;
- fail-closed refusal (empty list) on missing required keys (including
  `bandwidth_hz`, which the RF minimum feature set (contract 7.4) requires)
  or an unparseable timestamp; never a guessed default, never a
  schema-invalid emission;
- no `profile` stamp: profile is gateway-added export metadata
  (contract 3.4), so the adapter leaves it to the gateway like the
  production references do;
- all-or-nothing canonical geo (contract 6.8): geo is omitted entirely when
  any of `lat`/`lon`/`alt_hae_m` is missing, never zero-filled;
- omit-or-refuse lineage (contract 4.8): no `lineage` block unless the caller
  supplies real parent ids, in which case
  `lineage.transform = "translate:<schema_id>@<adapter_version>"`;
- no `confidence` on `OBSERVATION_EVENT` (contract 7.1).

## Run

From the repository root:

```
python -m pytest adapters/ingress/example-vendor -q
```

Follow the same ladder for your own adapter; see `adapters/AUTHORING.md`.
