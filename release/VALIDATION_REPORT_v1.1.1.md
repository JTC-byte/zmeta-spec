# ZMeta v1.1.1 Validation Report

Release: v1.1.1

## Scope

This validation pass covers the v1.1.1 reference implementation and package
artifacts:

- Canonical version-discriminated JSON Schema
- Version-specific v1.0 and v1.1.0 schema wrappers
- Locked v1.0 semantic contract and governed v1.1.0 extension semantics
- Policy packs for semantics, profiles, routing, producer authority, timing
  freshness, lineage, and violation codes
- Gateway validator implementation
- Ingress and egress adapter tests
- Protobuf, CBOR, compact CBOR, and JSON encoding paths
- Valid and invalid conformance fixtures
- Runnable examples
- Release checksum/signature helper tooling

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
- Ingress adapters normalize UTC offsets to UTC `Z` output.
- Adapter operational events carry explicit timing quality or can be backed by a
  matching recent `TIME_STATUS`.
- RF observation windows require paired `t_start` / `t_end`; RF midpoint is
  checked semantically.
- Producer authority, lineage, timing freshness, deduplication, routing, and CoT
  skip metrics are enforced outside JSON Schema where stream/deployment context
  is required.
- Protobuf decoding rejects oversized inputs, invalid field numbers, overly deep
  JSON payloads, and unsupported wire types.

## Test Results

- Adapter and gateway pytest suite: 207 passed
- Strict examples: 40 passed
- Strict conformance: ok
- Release signing helper tests: passed
- Python compile checks: passed
- `git diff --check`: no whitespace errors; Git reported line-ending warnings
  for existing CRLF conversion behavior.

## Contract Hashes

- `schema_hash=3f5f615c1539043f48a612a225421176aace9b3fb3a2507ea43dc31fe5bf1023`
- `policy_hash=70d8dc2b21641e44772e96c28989aa2a93211c2fba1e4c992ea12c8374bb1b16`
- `semantics_hash=bdc3c31e5c206cb667899d06aebf6576a43502af400f6f1e0e15ded65ada367b`
- `contract_hash=4fa2f874f17f15e9af1424672563c3fad32e6dc5a62efda4fa9f692f8f186833`

## Residual Risks

- Runtime lineage parent-type validation can only prove relationships when the
  local event store contains the parent event.
- Producer authority policy is deployment-specific; fielded deployments should
  narrow the reference producer patterns to authenticated local identities.
- Fallback adapter timing quality is intentionally conservative
  (`UNKNOWN`/`UNSYNCED`) unless deployments supply stronger source timing.
- Detached release signatures require a local signing key; checksum verification
  alone proves integrity, not authenticity.
