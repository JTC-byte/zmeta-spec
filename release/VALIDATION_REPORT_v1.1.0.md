# ZMeta v1.1.0 Validation Report

Release: v1.1.0

## Scope

This validation pass covers the full v1.1.0 stack:

- Canonical version-discriminated JSON Schema
- Version-specific v1.0 and v1.1.0 schema wrappers
- Locked v1.0 semantic contract and governed v1.1.0 extension semantics
- Policy packs for semantics, profiles, routing, producer authority, timing
  freshness, lineage, and violation codes
- Gateway validator implementation
- Adapter tests
- Valid and invalid conformance fixtures
- Runnable examples
- Compatibility normalizer tooling

## Technical Checks

- v1.1.0-only vocabulary is not valid under `zmeta_version: "1.0"`.
- v1.1.0 preserves v1.0 invariants and only extends governed vocabulary.
- `event_subtype` matches the payload discriminator.
- Profile L rejects raw observations, inference, and fusion exports.
- Inference events cannot carry `track_id`, `members`, or `estimated_state`.
- State events cannot carry raw sensor features, measurements, modality, event
  windows, or raw data references.
- Command events cannot carry altitude or vertical-control fields.
- Timestamp fields require UTC `Z` serialization.
- RF observation windows require paired `t_start` / `t_end`; RF midpoint is
  checked semantically.
- Canonical `geo` is strict WGS-84 lat/lon plus HAE `alt_m`; v1.1.0 allows
  controlled `error_ellipse_m`.
- `quality.measurement_error` uses explicit value/unit/metric fields.
- SENSOR_STATUS and PLATFORM_STATUS reject contradictory or missing health data.
- Producer authority, lineage, timing freshness, deduplication, and routing rules
  are enforced outside JSON Schema where stream/deployment context is required.

## Test Results

- Targeted invariant tests: 152 passed, 106 subtests passed
- Full gateway tests: 167 passed, 106 subtests passed
- Adapter tests: 19 passed
- Schema Draft 2020-12 lint: ok
- Strict examples: 40 passed
- Strict conformance: ok
- v1.1.0 examples via `tools/validate.py`: 13 passed
- End-to-end workflows: H, M, and L passed
- Python compile checks: passed
- `git diff --check`: no whitespace errors; Git reported line-ending warnings
  for existing CRLF conversion behavior.

## Contract Hashes

- `schema_hash=3f5f615c1539043f48a612a225421176aace9b3fb3a2507ea43dc31fe5bf1023`
- `policy_hash=70d8dc2b21641e44772e96c28989aa2a93211c2fba1e4c992ea12c8374bb1b16`
- `semantics_hash=bdc3c31e5c206cb667899d06aebf6576a43502af400f6f1e0e15ded65ada367b`
- `contract_hash=4fa2f874f17f15e9af1424672563c3fad32e6dc5a62efda4fa9f692f8f186833`

## Compatibility Mode

Compatibility normalization remains non-normative and opt-in. Strict schema and
conformance validation reject version aliases and legacy fields unless an adapter
normalizes them before validation.

Supported opt-in normalizations:

- `zmeta_version: "1.1"` to `"1.1.0"`
- `endurance_remaining_sec` to `endurance_remaining_ms`
- EO `features.bbox` to `features.roi_px` only when explicitly asserted as ROI
  metadata

The normalizer records a sidecar change report and does not rewrite immutable
identity, time, source, lineage, event type/subtype, or track identity fields.

## Residual Risks

- Runtime lineage parent-type validation can only prove relationships when the
  local event store contains the parent event. Profile L unresolved lineage is
  intentionally tolerated.
- Producer authority policy is deployment-specific; fielded deployments should
  narrow the reference producer patterns to local identities.
- The v1.1.0 schema remains a governed extension while v1.0 remains the locked
  normative semantic contract.
