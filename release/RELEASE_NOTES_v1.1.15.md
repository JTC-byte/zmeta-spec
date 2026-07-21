# ZMeta v1.1.15 Release Notes

Release date: 2026-07-21
Release type: SAPIENT bridge (BSI Flex 335 v2.0 mapping pack and
reference adapters, wire-validated end-to-end against the official
Dstl Apex middleware)

## Summary

ZMeta v1.1.15 ships the SAPIENT bridge: a declarative mapping pack and
reference ingress/egress adapters for BSI Flex 335 v2.0 — SAPIENT, the
UK MOD counter-sUAS standard and NATO C-UAS standard (STANREC 4869).
This is the first ZMeta mapping pack targeting a nationally
standardized external format, and the first whose wire compatibility
was validated end-to-end against the counterparty's official tooling:
every egress message parses strictly into Dstl's own generated
protobuf classes and passes the official Apex validator clean, every
official-built ingress message translates to schema-valid ZMeta
events, and a live Apex-SAPIENT-Middleware v4.2.0 instance accepted
the adapter's traffic with no error records and no Error replies.

SAPIENT fuses measurement, classification, track identity, and fusion
association in one DetectionReport message; the ingress adapter
demonstrates ZMeta's layer separation doing real work by splitting
each report into an OBSERVATION_EVENT plus per-claim INFERENCE_EVENTs
with registration-derived model identity, and by gating fusion-node
output through the external-promotion machinery with caller-owned
loop status. The locked v1.0 kernel's semantics are unchanged; the
only governed policy change is one additive producer-authority block.

## Major Work Completed

### SAPIENT mapping pack (`adapters/mapping-packs/sapient-bsi-flex-335/`)

- Declarative field maps, enum tables, and the
  registration-declared-units doctrine (schema_id
  `vendor:sapient_bsi335:v2`, targeting BSI Flex 335 v2.0).
- Canonical-geo eligibility matrix (ellipsoid datum + explicit
  altitude only), refusal matrix, and a documented out-of-scope
  surface: SAPIENT Task ingress (command-safety boundary), effector
  arming, the AlertAck operator loop, protobuf wire encoding, and UTM
  conversion.

### SAPIENT ingress (`adapters/ingress/sapient/`)

- DetectionReport → OBSERVATION_EVENT + per-claim INFERENCE_EVENTs;
  fusion-node DetectionReports → STATE_EVENT only under caller
  `external_promotion` metadata with caller-owned `loop_status` (the
  adapter never asserts a reflection check it did not perform).
- StatusReport → SENSOR_STATUS / PLATFORM_STATUS (v1.1.0 branch);
  TaskAck → TASK_ACK with refusal when the issued-command correlation
  is unresolvable; Error → SCHEMA_VIOLATION.
- RegistrationStore as the units-and-error codex: signal and velocity
  values reach canonical fields only through registration-resolved
  units; unregistered nodes refuse detection translation (refusal over
  fabricated modality). Send-time envelope timestamps widen
  `est_error_ms` by the registered per-mode `maximum_latency`, with a
  conservative cross-mode fallback for unknown mode names.

### SAPIENT egress (`adapters/egress/sapient/`)

- COMMAND_EVENT → Task for GOTO / TRACK_TARGET / CHANGE_SENSOR_MODE
  only; altitude is structurally excluded from projected locations;
  all other task types refuse.
- STATE_EVENT → DetectionReport with `zmeta.risk` /
  `zmeta.timing_quality` object_info self-labels (label-not-launder)
  and export refusal for quarantined/rejected events and
  prohibited-use paths.
- SAPIENT ULID id discipline (found by the end-to-end validation,
  fixed pre-release): `report_id` is a canonical ULID whose 48-bit
  timestamp is the event's own `event.ts` (never translate-time wall
  clock); `object_id` passes through only valid ULID track ids or
  resolves via the caller-owned `object_map`; Task `task_id` must be a
  valid ULID — the adapter never rewrites the idempotency key.

### End-to-end wire validation (official Dstl tooling)

- Apex-SAPIENT-Middleware v4.2.0 (commit 0c8591a), its shipped BSI
  Flex 335 v2.0 pb2 modules and validator, stock strict configuration:
  egress strict-parse + byte round-trip + validator clean; ingress
  zero findings across both protobuf-JSON key spellings; live loop
  accepted Registration (acknowledged) and egress DetectionReports
  as-is. Recorded honestly as not exercised: the C# BSI Flex 335 v2
  test harness (no .NET SDK on the validation host) and multi-node
  Apex routing. Details in the pack README Validation section.

### Conformance and policy

- 12 new adapter-harness fixtures (must-pass corpus 27 → 39) covering
  the promotion path and the refusal register (missing lineage,
  zero-fill geo, unregistered node, missing envelope timestamp, null
  node identity, unresolvable task correlation, model-less alert).
- One additive `sapient-ingress` producer-authority policy block
  mirroring the cot-ingress external-promotion constraints
  (PROMOTE-SAPIENT-STATE-V1).

## Compatibility

- No event-vocabulary or schema changes; nothing new becomes valid
  under `zmeta_version: "1.0"` or `"1.1.0"`.
- The producer-authority reference policy gains the `sapient-ingress`
  block (additive; existing producers unchanged). Deployments using
  release or contract hash gates should update expected hashes from
  the v1.1.15 release manifest.
- SAPIENT-bridged deployments: command producers must mint ULID
  `task_id` values, and native ZMeta track ids exported to SAPIENT
  require a caller-owned `object_map` — see the egress README ULID
  discipline section.

## Validation

The full command battery and results are in
`release/VALIDATION_REPORT_v1.1.15.md`. Headline: full kernel gate
green with all flags (bad-events 27, adapter harness 39), strict
examples 51/51, full pytest suite green with zero failures, and the
end-to-end Apex wire validation described above.

## Assets and Verification

Assets: `zmeta-v1.1.15-dist.zip`, `zmeta-edge-v1.1.15.zip`,
`zmeta-gateway-v1.1.15.zip`, `zmeta-release-package-v1.1.15.zip`,
`zmeta-release-manifest.yaml`, `RELEASE_NOTES_v1.1.15.md`,
`VALIDATION_REPORT_v1.1.15.md`, `SHA256SUMS_v1.1.15.txt`.

Verify asset integrity:

```bash
sha256sum -c SHA256SUMS_v1.1.15.txt
# or, from a repo checkout:
python release/sign_release_artifacts.py --version v1.1.15 --verify-checksums
```

`SHA256SUMS_v1.1.15.txt` is written with LF line endings, so plain
`sha256sum -c` works on Linux checkouts.

Signing decision: this is a checksums-only release — no detached
signatures are attached. Signature generation remains the maintainer's
external release-authority process.
