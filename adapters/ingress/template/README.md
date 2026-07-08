## Ingress Adapter Template

Overview: see `adapters/README.md`.

Purpose: convert external payloads into ZMeta v1.0.

### Required functions

- `detect(input_bytes)` -> schema_id
- `translate(input_obj, schema_id)` -> list[dict] of ZMeta events
- `validate(zmeta_event)` -> (pass|warn|fail, violations)

### Required behavior

- Must call schema validation using `schema/zmeta-event-1.0.schema.json`.
- Must emit SYSTEM_EVENT/SCHEMA_VIOLATION on deterministic failures or warning
  diagnostics, with risk labels when policy soft-accepts degraded data.
- Must emit `lineage` only when real parent ZMeta event ids exist (for
  example, caller-supplied `based_on`). When lineage is emitted, set
  `lineage.transform = "translate:<schema_id>@<adapter_version>"`. Never
  fabricate `lineage.based_on` values: an original observation with no ZMeta
  parent omits lineage entirely, and event families whose lineage is
  mandatory (INFERENCE/FUSION/STATE, contract 4.8) must refuse to emit
  rather than invent a parent id.
- Must apply Units & Geodesy rules (WGS-84, meters HAE, degrees, meters/sec).
- Must normalize timestamps with shared helpers such as
  `adapters.ingress.time_utils.normalize_utc_z()` or `epoch_ms_to_utc_z()`.
- Must expose timing quality per event or through periodic `TIME_STATUS`.
  `coerce_timing_quality()` provides a conservative `UNKNOWN`/`UNSYNCED`
  fallback, but that fallback is degraded timing and should be replaced by
  source-provided GPS/NTP/PTP metadata when available.

### Invocation style

Run adapters as importable modules from the repository root, or make the repo
root available on `PYTHONPATH`. Shared helpers use package imports such as
`from adapters.ingress.time_utils import ...`; direct execution from inside an
adapter subdirectory can fail because Python will not see the repository root.
