# ZMeta v1.0.3 Release Notes

## Highlights
- Added compact binary mapping for Profile L (CBOR + integer keys) with reference encoders and size tooling.
- Expanded the reference gateway with JSON/CBOR/compact I/O, strict validation, rate limiting,
  metrics logs, and contract-hash gating.
- Added a conformance pack and validation tooling plus encoding roundtrip examples.
- Fixed MAVLink TASK_ACK ingress to require original_event_id in metrics.
- Set pytest cache to a repo-local path to avoid teardown hangs in restricted environments.

## Semantics and Policy
- Expanded the v1.0 schema for Observation/Inference/Fusion payloads and SystemEvent requirements
  (TIME_STATUS, LINK_STATUS, TASK_ACK, SCHEMA_VIOLATION).
- Added violation codes and semantic checks for task acknowledgements, link status, and schema violations.
- Tightened command-event rules (requires deconfliction, altitude prohibition) and task dedupe semantics.

## Documentation
- Added `spec/compact-binary-mapping.md`, `spec/field-dictionary.md`, and `spec/profile-compatibility.md`.
- Updated the semantics contract with time sync and units/geodesy guidance.
- Added config template documentation and refreshed spec/quickstart references.

## Tools
- New `tools/gateway_wizard.py`, `tools/compute_contract_hash.py`, `tools/measure_packet_size.py`,
  `tools/validate_examples.py`, and `tools/validate_conformance.py`.
- Added CBOR/compact support to UDP sender/receiver/replay tools.

## Tests
- Added encoding roundtrip tests and CoT egress validation.
- Added conformance pack must-pass/must-fail cases.

## Known Issues
- Gateway Docker verification not run in this release (requires virtualization + WSL2 on Windows).
