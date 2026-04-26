# Changelog

## [Unreleased]
- Added UUIDv7 event identity requirements and aligned schema validation.
- Made timing quality metadata mandatory across all profiles.
- Added normative track persistence, deduplication, and edge failure-mode configuration guidance.
- Clarified confidence semantics and Profile L compact stripping rules.

## [1.0.3]
- Added compact binary mapping for Profile L plus reference CBOR/compact encoders and size tooling.
- Expanded schema/policy to cover Observation/Inference/Fusion payloads and SystemEvent requirements.
- Enhanced gateway with JSON/CBOR/compact I/O, strict validation, rate limiting/metrics logs,
  contract-hash gating, and COMMAND_EVENT dedupe.
- Added conformance pack, example validators, and encoding roundtrip examples/tests.
- Added new documentation for compact mapping, field dictionary, profile compatibility, and refreshed specs.
- Fixed MAVLink TASK_ACK ingress to require original_event_id in metrics.
- Set pytest cache to repo-local path to avoid teardown hangs in restricted environments.

## [1.0.2]
- Expanded installation docs with bundle-based step-by-step guidance, prerequisites,
  config references, verification, and troubleshooting.
- Added deployment helpers and configs for edge/gateway installs (Docker Compose + config templates).
- Added end-to-end workflow test tooling with profile variants.
- Tightened routing policy and validator enforcement (producer allowlists, TASK_ACK required fields).
- Updated semantics contract and examples for operating model, lineage, and data_ref guidance.
- Release artifacts refreshed; obsolete Compose `version` removed.

## [1.0.1]
- Added optional timing fields (`t_publish`, `t_receive`) to schema and docs.
- Clarified observation quality vs confidence; tightened role/profile guidance.
- Updated policy/routing enforcement and producer rules; EDGE role restricted to observation + system.
- Added live gateway UDP test tool and Makefile target; expanded README/quickstart instructions.

## [1.0.0]
- Initial public release of the ZMeta specification
