# ZMeta Specification (v1.0)

## Overview
- ZMeta is a transport-agnostic, event-based metadata standard for resilient ISR.
- Designed to survive degraded and denied environments.
- Separates observation, inference, fusion, state, and command semantics.

## What ZMeta Is
- A semantic contract
- A JSON schema
- A policy-driven enforcement model
- A reference gateway and adapters

## What ZMeta Is Not
- Not a transport
- Not a C2 system
- Not a video container
- Not a replacement for MISB

## Design Goals
- Honesty under uncertainty
- Graceful degradation
- Operator trust
- Interoperability across vendors and transports

## Repository Structure
- `spec/` Core specification and normative text.
- `schema/` JSON schema definitions for ZMeta artifacts.
- `examples/` Sample payloads and usage patterns.
- `policy/` Policy language and enforcement guidance.
- `gateway/` Reference gateway implementation and tests.
- `adapters/` Ingress and egress adapter patterns and templates.
- `tools/` Utilities for validation and development workflows.

## Adapters

Reference adapters show how to translate between ZMeta and external systems.
See `adapters/README.md` for ingress templates, mapping packs, and egress projections.

## Tools

Quick helpers for local validation and UDP replay:

```
python tools/run_gateway.py --profile H
python tools/udp_receiver.py
python tools/udp_sender.py --file examples/zmeta-command-examples.jsonl
python tools/replay.py --file examples/zmeta-command-examples.jsonl --delay-ms 200
python tools/validate.py --file examples/zmeta-command-examples.jsonl --profile H
python tools/test_gateway_live.py
```

`tools/test_gateway_live.py` exercises live UDP forwarding, COMMAND dedupe, and CoT emission.

Makefile targets run the same commands with `python` directly; ensure dependencies are installed
(`python -m pip install -r gateway/requirements.txt -r requirements-dev.txt`).

## Versioning
- v1.0.x = clarifications and fixes
- v1.1+ = backward-compatible extensions
- v2.0 = breaking changes

See `spec/versioning.md` for the full policy.

## Quickstart

Prereqs: Python 3.11+ and Docker.

Install runtime dependencies:
```
python -m pip install -r requirements.txt
```

Optional (tests/dev tools):
```
python -m pip install -r requirements-dev.txt
```

Windows Docker note: Docker Desktop requires virtualization + WSL2 enabled. If Docker is not available, run the gateway directly with Python.

See `spec/quickstart.md` for a runnable gateway + UDP replay walkthrough.

## Installation and Packaging

See `spec/installation-guide.md` for a deterministic install guide, gateway wizard,
and mapping pack installs for drone and sensor configs.

Note on timing metadata: `event.t_publish` (emit time) and `event.t_receive`
(ingest time) are optional fields used for latency debugging and AAR.

## Normative vs Reference

Normative (contract): `spec/semantics-contract.md`, `schema/zmeta-event-1.0.schema.json`, `policy/*.yaml`
Normative also includes: `spec/versioning.md`
Reference: `gateway/*`, `tools/*`, `adapters/*`, `examples/*`

Normative files define compliance. Reference components exist to accelerate adoption.
