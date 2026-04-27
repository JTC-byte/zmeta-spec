# ZMeta v1.0.5 Release Notes

## Release Summary

ZMeta v1.0.5 is a semantic-contract hardening patch. It does not introduce new
schema fields, policy rules, or gateway runtime behavior. Instead, it tightens
the normative language around edge cases discovered during the final v1.0
contract review, especially immutability, profile/export projections, timing
freshness, lineage authority, and future extensibility.

Because `spec/semantics-contract.md` participates in the combined contract hash,
this release intentionally updates the semantic and combined contract hashes.

## What Changed

### Immutability and Export Projections

- Clarified that source-authored semantic content is immutable.
- Explicitly prohibited gateways/exporters from changing `event.ts`,
  `event.event_id`, `event.event_type`, `event.event_subtype`, `source`,
  `track_id`, lineage, or payload meaning to "fix" an event.
- Clarified that profile exports may be projections of the same event when they:
  - add non-semantic export metadata such as `profile`, `event.t_receive`, or
    gateway-supplied `event.t_publish`;
  - omit optional fields for bandwidth;
  - reduce numeric precision;
  - conservatively lower `confidence` or `valid_for_ms` to reflect export-path
    degradation.
- Clarified that any semantic payload change, reinterpretation, correction,
  source-field replacement, confidence increase, TTL increase, precision
  increase, or specificity increase requires a new `event_id` and lineage.

### UUIDv7 Timestamp Semantics

- Clarified that UUIDv7 timestamp bits represent identity-generation time only.
- Confirmed that `event.ts` remains authoritative for capture, observation, or
  validity time.
- Prohibited consumers from using UUIDv7 timestamp bits as a substitute for
  `event.ts` and timing quality metadata.

### Authority Boundaries

- Clarified that authority is assigned to logical functions and producer
  identities, not merely physical hardware location or deployment tier.
- Clarified that one physical node may host multiple logical functions, but each
  function must emit only authorized event types.
- Removed named example producers from normative tasking language.

### Lineage Authority

- Clarified that envelope `lineage.based_on` is the authoritative audit lineage.
- Clarified that payload-local provenance fields such as `payload.based_on` are
  permitted for claim-specific convenience.
- Required payload-local references to be equal to or a subset of envelope
  lineage when both are present.

### Timing Quality Freshness

- Added freshness expectations for periodic `SYSTEM_EVENT` / `TIME_STATUS`
  reporting.
- Recommended that producers document their timing-report cadence.
- Recommended deployment-defined `max_timing_status_age_ms` values.
- Clarified that consumers must not treat periodic timing status as valid
  indefinitely.
- Clarified that stale/unknown timing should degrade confidence, gate
  time-correlated fusion, or raise local timing warnings according to deployment
  policy.

### Confidence and Observation Quality

- Changed degraded-timing confidence wording from strictly proportional reduction
  to documented reduction or capping policy.
- Clarified that OBSERVATION_EVENT may use measurement-quality fields such as
  `payload.quality.sensor_confidence`, `payload.quality.snr_db`, or
  `payload.quality.quality_score` when they describe measurement quality rather
  than semantic belief.

### System Event Extensibility

- Clarified that no additional `system_type` values are permitted in v1.0.
- Clarified that operational degradation, merge/split, platform health, or sensor
  health events must use v1.0-supported system types, local/operator logs, or a
  future schema/profile that explicitly defines those event types.

### Deduplication and Track Lifecycle

- Generalized event-id deduplication beyond FUSION_EVENT / STATE_EVENT to
  OBSERVATION_EVENT, INFERENCE_EVENT, FUSION_EVENT, STATE_EVENT, and ordinary
  SYSTEM_EVENTs unless a more specific idempotency rule applies.
- Clarified that v1.0 does not define dedicated machine-readable `MERGE` or
  `SPLIT` system event types.
- Clarified that merge/split relationships are represented through new
  FUSION_EVENTs, lineage, and local AAR/operator logs unless a future schema
  version explicitly defines dedicated lifecycle events.

## Compatibility

- No JSON Schema changes.
- No policy YAML changes.
- No gateway runtime changes.
- No adapter changes.
- Existing v1.0.4-valid payloads remain valid under v1.0.5.
- The combined contract hash changes because the normative semantic contract text
  changed.

## Contract Hashes

```text
schema_hash=d1c815e120238f500892039b56cc9d4f2b00c2abfd8744c393b13f64664c2ace
policy_hash=c90784fdae753bd59c2c9b10d3e637e6e75026e77e74bf6e711c59361bb4e2bd
semantics_hash=48a2b0661c707e4af9fafaa0c8ffe1cdedabca5e2c038f6f805dad726ed811cc
contract_hash=da7dac6a03f548b72fdb62717ceedff9667d3b5e195303e53756299cbbd68681
```

## Release Assets

Attach the following assets to the GitHub release:

- `zmeta-v1.0.5-dist.zip` - normative/reference distribution with schema,
  semantic contract, policy, examples, core docs, changelog, and release notes.
- `zmeta-edge-v1.0.5.zip` - edge deployment bundle.
- `zmeta-gateway-v1.0.5.zip` - gateway deployment bundle.
- `RELEASE_NOTES_v1.0.5.md` - this release note document.
- `SHA256SUMS_v1.0.5.txt` - checksums for release zip assets.

## Validation Performed

- `python tools/validate_examples.py --strict --require-all`
- `python tools/validate_conformance.py --strict`
- `python -m pytest -q gateway/tests adapters`
- `python tools/compute_contract_hash.py`
- `python tools/measure_packet_size.py --file examples/zmeta-profile-L-examples.jsonl --encodings compact --max-bytes 240 --summary-only`
- `python gateway/src/gateway.py --profile H --self-test`
- `python release/build_mvp_packages.py`
- `python release/build_release_bundle.py`

## Upgrade Guidance

- Recompute and update any configured `require_contract_hash` values.
- No schema, policy, producer, adapter, or gateway code changes are required if
  already compatible with v1.0.4.
