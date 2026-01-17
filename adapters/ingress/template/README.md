## Ingress Adapter Template

Purpose: convert external payloads into ZMeta v1.0.

### Required functions

- `detect(input_bytes)` -> schema_id
- `translate(input_obj, schema_id)` -> list[dict] of ZMeta events
- `validate(zmeta_event)` -> (pass|warn|fail, violations)

### Required behavior

- Must call schema validation using `schema/zmeta-event-1.0.schema.json`.
- Must emit SYSTEM_EVENT/SCHEMA_VIOLATION on deterministic failure (no guessing).
- Must set `lineage.transform = "translate:<schema_id>@<adapter_version>"`.
- Must apply Units & Geodesy rules (WGS-84, meters HAE, degrees, meters/sec).
