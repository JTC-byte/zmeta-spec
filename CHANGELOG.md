# Changelog

## [Unreleased]
- TBD

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
