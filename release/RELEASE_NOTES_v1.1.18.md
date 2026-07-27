# ZMeta v1.1.18 Release Notes

Release date: 2026-07-27
Release type: event-readiness cut — deployment verification, the bladeRF
reference adapter, the UxS command-loop pair, and post-release hardening

## Summary

v1.1.18 is the deployment-readiness release. Where v1.1.17 hardened the
semantics, this one makes the stack demonstrably deployable: a working
reference adapter for real RF capture data, verified containers on both
x86 and ARM64, a two-node quickstart from sensor edge to COP, and the
command-evidence gate that makes operator-built retasking automations
auditable.

Everything in it was fixed reproduce-first, adversarially attacked at
landing, and then re-reviewed cold as a range before this cut — that
final review found and closed 13 further verified findings, including
three the per-wave attacks had missed.

The locked v1.0 kernel is unchanged. No schema, event vocabulary, or
`reason_code` was added in this release.

## Fielded-safety and honesty hardening

- **The naive-timestamp class is closed at the gateway's own door.** A
  schema-clean but offset-less `ts` (e.g. `"1969-12-31Z"`, which
  satisfies the pattern yet parses without a UTC offset) could raise out
  of the timing path or be silently reinterpreted as host-local time.
  It now refuses at the parse seam — and a TIME_STATUS whose own
  timestamp cannot be ordered is no longer recorded at all, closing a
  pre-existing arm where such a status made the freshness gate silently
  pass for that source.
- **The plain-`cbor` envelope now enforces the same fail-closed value
  model as the compact envelope**, on both codec backends, with a probed
  pre-decode depth bound. Tagged, value-shared, over-deep, and
  non-finite-bearing datagrams refuse identically regardless of which
  CBOR library an install happens to have.
- **A post-release crash class fixed:** the compact encode path handed
  hostile-depth structures to the backend before refusing, which could
  abort the producer process on C-extension installs. The declared
  nesting maximum is now enforced before any backend runs.

## The command loop (operator retasking automations)

- **New `policy/command-evidence.yaml` + gateway enforcement.** A
  COMMAND_EVENT can cite the fusion/inference parents that motivated it
  through existing lineage vocabulary, and the gateway checks those
  citations against what it actually saw upstream: an unknown or evicted
  parent, a parent type that cannot motivate a command, or a parent whose
  risk labels prohibit command basis each take an explicit, filterable
  disposition. **A quarantined or degraded track can no longer silently
  become the basis of a retasking order.**
- Defaults are permissive by design — a human operator's direct tasking
  needs no cited parent — with a `require_evidence` knob for deployments
  gating automations. Recorded evidence labels are **sticky**: a re-sent
  copy of an already-seen event cannot erase a prohibition the gateway
  already observed.
- **`docs/zmeta_track_lifecycle_pattern.md`** expresses track
  new/active/stale/lost/merged/split/retired and the "command-grade
  track" criteria entirely in current vocabulary. No lifecycle
  vocabulary was minted; the roadmap candidate stays `reserved` with its
  evidence legs recorded honestly.

## Deployment and adapter authoring

- **`adapters/ingress/bladerf/`** — the reference ingress adapter for the
  merged edge-comms bladeRF mapping pack, reproducing both real-capture
  fixture pairs exactly. Authored along the documented
  `adapters/AUTHORING.md` path in ~13 minutes of measured wall-clock
  (~25 minutes including independent adversarial verification), which is
  the repository's receipt for the one-sitting adapter claim.
- **`docs/zmeta_two_node_quickstart.md`** — sensor edge (host or
  Raspberry Pi) to COP in two stock containers, with the port topology,
  the five-minute wire check, the startup-hash match rule, and a
  field-debugging cheat-sheet that reads each honesty signal as the
  system working.
- **Container verification**: the stock compose files were run on x86 and
  on ARM64 under emulation; dependencies resolve, the gateway processes
  the example corpus cleanly, and the schema/policy/semantics/contract
  hashes are byte-identical across architectures.
- **`cot.config` pass-through**: deployments can now assert their
  position-source pedigree (`geopointsrc`/`altsrc`/`how`) so TAK receives
  `<precisionlocation>` ellipse detail. Unasserted stays omitted — the
  projection still never stamps a pedigree it cannot prove.
- **New advisory lint** `tools/lint_adapter_vocabularies.py` holds
  adapter vocabulary mirrors to the governed schema enums.

## Compatibility

- v1.0 and v1.1.0 producers/consumers: no change. Nothing in this release
  narrows an existing event's validity.
- Gateway operators: the command-evidence block is new and optional —
  an absent `policy/command-evidence.yaml` is a legal deployment, and
  the shipped defaults do not refuse anything previously accepted.
- Compact and plain-CBOR wire peers: datagrams that previously decoded
  differently depending on the installed CBOR library now refuse
  identically with explicit diagnostics.

## Verification

Full kernel-protection conformance (all flags) exit 0; strict examples
51/51; pytest **1420 passed + 1070 subtests**; adapter harness 48/48;
policy risk-mode lint, adapter-vocabulary lint, and future-roadmap
validator all clean; Profile L packet check max 150/240 bytes. Verify
assets with `SHA256SUMS_v1.1.18.txt`, the release manifest, and the
release package checksum file.

## Signing

Checksums-only, consistent with v1.1.5 through v1.1.17. No detached
signatures are attached unless the maintainer adds them at publish.
