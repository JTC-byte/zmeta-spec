# ZMeta v1.0.4 Release Notes

## Release Summary

ZMeta v1.0.4 is a contract-alignment and reference-stack hardening release. It
locks the repository around the updated v1.0 semantic contract, closes drift
between the contract, schema, policy, examples, conformance corpus, adapters,
gateway runtime, configs, tooling, CI, and release packaging.

The normative contract remains v1.0. The v1.1.0 schema and examples remain an
experimental compatibility extension and must preserve the locked v1.0 semantic
boundaries.

## Highlights

- Enforced UUIDv7 event identity and stricter observation/inference/state
  semantic separation across schema, policy, adapters, and validators.
- Made timing quality metadata mandatory for operational events across Profiles
  L/M/H, either per event or via prior `TIME_STATUS` from the same source.
- Added validator and gateway support for profile mismatch detection,
  timing-status enforcement, event deduplication, command deduplication, and
  TASK_ACK deduplication.
- Included the semantic contract in the gateway contract hash so schema/policy
  drift and normative-text drift are detected together.
- Updated Profile L behavior to preserve required timing, confidence, and
  lineage fields while still supporting compact encoding and optional-field
  thinning.
- Refreshed release bundles and CI so future releases validate v1.0 and
  experimental v1.1 examples before packaging.

## Normative Contract Alignment

- Added and implemented the UUIDv7 event identity requirement:
  - All `event.event_id` values are expected to be UUIDv7.
  - Legacy IDs should be regenerated at adapter boundaries and preserved only in
    payload-scoped provenance fields when traceability is needed.
- Made timing quality metadata a practical validation requirement:
  - Required fields: `time_source`, `sync_state`, `est_error_ms`,
    `last_sync_ts`.
  - Operational events may carry timing quality directly under
    `payload.timing_quality`, `payload.quality.timing_quality`, or
    `payload.quality`.
  - A source may instead emit `SYSTEM_EVENT` / `TIME_STATUS`; later events from
    the same `(platform_id, producer, node_role)` satisfy timing exposure.
- Clarified observation boundaries:
  - OBSERVATION_EVENT payloads and features must not contain track identity,
    classification labels, class names, or confidence fields.
  - Semantic labels and model confidence belong in INFERENCE_EVENT.
- Clarified confidence semantics:
  - `confidence` is required for INFERENCE/FUSION/STATE.
  - `confidence` is prohibited for OBSERVATION/COMMAND/SYSTEM.
- Preserved track continuity and deduplication semantics in validation tooling
  and examples.

## Schema and Policy Changes

- Updated `schema/zmeta-event-1.0.schema.json`:
  - Forbids `track_id`, `entity_class`, `classification`, `class_name`,
    `label`, and `confidence` under observation payloads and observation
    feature dictionaries.
- Updated `schema/zmeta-event-1.1.0.schema.json`:
  - Keeps EO/IR features as raw sensor facts only.
  - Moves semantic class/confidence handling out of observation features.
  - Keeps v1.1.0 marked as experimental in documentation.
- Updated `policy/semantics.yaml`:
  - Adds mandatory timing quality rules.
  - Extends observation forbidden fields.
  - Adds allowed schema-violation reason codes for profile, timing, event
    duplicate, and TASK_ACK duplicate conditions.
- Updated `policy/violation-codes.yaml`:
  - Adds `PROFILE_MISMATCH`, `TIMING_STATUS_MISSING`, `EVENT_DUPLICATE`,
    `TASK_DUPLICATE`, and `TASK_ACK_DUPLICATE`.
- Updated `policy/routing.yaml`:
  - Adds explicit producer allowlists for the reference ingress adapters,
    fusion engine, and gateway-generated system events.

## Gateway Runtime Changes

- Added `ValidationState` to track:
  - Timing sources and latest timing metrics.
  - Seen event IDs.
  - Seen command task IDs.
  - Seen TASK_ACK state-transition keys.
- Added timing-quality enforcement to live gateway processing.
- Added silent duplicate-drop behavior for repeated non-command `event_id`
  values.
- Kept COMMAND_EVENT dedupe anchored on `payload.task_id`; duplicates emit
  `TASK_ACK` with `DUPLICATE_IGNORED` and `TASK_DUPLICATE`.
- Added TASK_ACK dedupe by `task_id + original_event_id + state`.
- Added profile mismatch enforcement when an event's top-level `profile` differs
  from the active export/validation profile.
- Added outgoing-event revalidation after gateway transforms such as profile
  stamping, timing stamping, optional-field stripping, and failure-mode
  degradation.
- Added timing-loss failure-mode degradation for STATE_EVENT confidence when
  latest source timing is `UNSYNCED`.
- Changed default timing stamps to apply across Profiles L/M/H.
- Stopped stripping `payload.quality` by default so timing quality and
  observation quality metadata are not accidentally removed.
- Added `semantics_hash` to contract hashing and gateway-generated
  hash-stamped system events.

## Adapter Changes

- EO-CV ingress now emits INFERENCE_EVENT rather than OBSERVATION_EVENT for
  detector classifications and confidence.
- MOTH, Kraken, and SignalHunter ingress adapters no longer emit fake
  `(0,0,0)` geo when sensor position is unavailable; they omit `geo` and expose
  quality/provenance fields instead.
- MOTH observation confidence is now stored as sensor quality metadata rather
  than top-level event confidence.
- MAVLink platform state now emits STATE_EVENT from a gateway-authorized role,
  stores platform health details under `payload.quality`, and uses stable
  platform track IDs.
- MAVLink TIME_STATUS now emits the required timing metrics, including
  `last_sync_ts`, and normalizes `SYNCED` to `LOCKED`.
- CoT egress no longer invents a UUID fallback when a STATE_EVENT has no
  `track_id`; it omits CoT output instead.
- Compact decoding now restores `requires_deconfliction: true` for compact
  COMMAND_EVENT payloads where the field is omitted by the mapping.

## Examples, Conformance, and Configs

- Updated all v1.0 examples to include required timing exposure.
- Added Profile L `TIME_STATUS` ordering where periodic timing is used instead
  of per-event timing.
- Updated conformance pass/fail corpus for timing status, profile mismatch, and
  stricter observation identity failures.
- Kept Profile L compact examples under the 240-byte packet budget.
- Updated edge/gateway config templates:
  - Profile L timing stamps are enabled.
  - `payload.quality` is no longer stripped.
  - Failure-mode defaults are present in edge configs.
  - Gateway example config paths resolve correctly from `gateway/config/`.
- Updated `tools/gateway_wizard.py` defaults for repo-root generated configs.

## Tooling and CI

- `tools/validate.py` now exits nonzero on validation failure.
- `tools/validate_examples.py` and `tools/validate_conformance.py` enforce
  timing quality and dedupe behavior.
- `tools/udp_sender.py` now sends JSONL files one event per datagram instead of
  treating the whole file as one payload.
- `tools/compute_contract_hash.py` now includes the semantic contract hash.
- CI now:
  - Lints both v1.0 and experimental v1.1.0 schemas.
  - Validates examples in strict mode.
  - Validates experimental v1.1 examples against the v1.1.0 schema.
  - Runs conformance, contract hashing, packet-size checks, gateway self-test,
    and pytest.
- Pytest config now disables the cache provider to avoid Windows restricted
  filesystem cache warnings.

## Release Assets

Attach the following assets to the GitHub release:

- `zmeta-v1.0.4-dist.zip` - normative/reference distribution with schema,
  semantic contract, policy, examples, core docs, changelog, and release notes.
- `zmeta-edge-v1.0.4.zip` - edge deployment bundle.
- `zmeta-gateway-v1.0.4.zip` - gateway deployment bundle.
- `RELEASE_NOTES_v1.0.4.md` - this release note document.
- `SHA256SUMS_v1.0.4.txt` - checksums for release zip assets.

## Validation Performed

- `python -m py_compile ...`
- `python tools/validate_examples.py --strict --require-all`
- `python tools/validate_conformance.py --strict`
- Draft 2020-12 schema lint for v1.0 and experimental v1.1.0 schemas.
- Experimental v1.1 examples validated against `zmeta-event-1.1.0.schema.json`.
- `python tools/measure_packet_size.py --file examples/zmeta-profile-L-examples.jsonl --encodings compact --max-bytes 240 --summary-only`
- `python tools/compute_contract_hash.py`
- `python -m pytest -q gateway/tests adapters`
- Gateway self-tests for default, gateway, edge, strict, and example configs.
- Live UDP workflow tests for Profiles H, M, L, COMMAND/SYSTEM dedupe, CoT
  output, and compact Profile L input.
- Docker Compose config rendering for edge, gateway, and standalone gateway
  compose files.
- `release/build_mvp_packages.py`
- `release/build_release_bundle.py`

## Known Limits

- Full Docker image build/run verification was not performed in this Windows
  workspace. Compose config rendering passed, but container startup still
  depends on local Docker Desktop/WSL2 availability and access to Docker
  credentials.
- v1.1.0 remains experimental. Do not treat v1.1.0-only enums or fields as part
  of the locked normative v1.0 contract.

## Upgrade Guidance

- Refresh gateway configs if they still strip `payload.quality`.
- Update producers/adapters so operational events expose timing quality directly
  or via periodic `TIME_STATUS`.
- Stop emitting semantic labels, class names, confidence, or track IDs from
  OBSERVATION_EVENT payloads.
- Recompute `require_contract_hash` values after upgrading:

```bash
python tools/compute_contract_hash.py
```

Current v1.0.4 combined contract hash:

```text
5da36892d8a0b3fa0100a56159646828dd07c5f1324973d67f60bf822704d09f
```
