# ZMeta v1.0.2 Release Notes

## Highlights
- Added a full step-by-step installation guide for bundle-based edge/gateway installs,
  including prerequisites, config references, verification, and troubleshooting.
- Added deployment helpers and configs for edge/gateway installs (Docker Compose + config templates).
- Added an end-to-end workflow test for Profile H/M/L with optional COMMAND/SYSTEM expectations.

## Semantics and Policy
- Enforced producer allowlists for INFERENCE/FUSION/STATE/COMMAND event types.
- Added TASK_ACK required-field enforcement.
- Clarified MVP producer roles and removed `swarmint` as a ZMeta producer.

## Documentation
- Expanded `spec/installation-guide.md` and `spec/quickstart.md` for no-context readers.
- Updated `deploy/README.md` with prerequisites, behavior, and port-collision notes.
- Added a "Start Here" section to the root `README.md`.

## Tools
- New `tools/test_workflow_end_to_end.py` to validate sensor->ZMeta->gateway->CoT workflows.

## Tests
- Schema lint via Draft202012Validator.
- `tools/validate.py` for examples across profiles.
- `pytest -q gateway/tests adapters` (passes; pytest cache warning on Windows due to permissions).

## Known Issues
- Docker engine verification pending (requires virtualization + WSL2 on Windows).
