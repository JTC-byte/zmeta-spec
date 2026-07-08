# ZMeta v1.1.11 Release Notes

Release date: 2026-07-07
Release type: field-driven adoption guidance patch (advisory docs, extension
registry governance, correlation examples, anti-laundering fixtures)

## Summary

ZMeta v1.1.11 harvests the requirements surfaced by a live at-scale deployment
(upstream PR #4, a v1.2.0 proposal that was reviewed, found kernel-breaking,
and not merged) and re-derives them from the locked kernel outward. It adds
advisory adoption guidance, extension-registry governance entries, a runnable
correlation example corpus, and two anti-laundering conformance fixtures.

It adds no schema changes, no policy-behavior changes, and no event
vocabulary; nothing new becomes valid under `zmeta_version: "1.0"` or
`"1.1.0"`. The locked v1.0 kernel is unchanged. Existing producers and
consumers are unaffected.

## Major Work Completed

### Advisory Adoption Guidance (non-normative)

- `docs/zmeta_mqtt_binding_guidance.md` — transport-binding conventions for
  ZMeta over MQTT: a topic shape built from the locked vocabulary
  (`<event_type_root>/<event_subtype>/<entity-scoped-id>`), retain guidance
  with explicit honesty rules (retained state is stale data with a timestamp;
  freshness is judged from `event.ts`, `valid_for_ms`, and timing context),
  tombstones as broker hygiene only (never an authoritative removal
  directive), transport-independent command governance, and
  legacy-topic-as-ingress-adapter guidance.
- `docs/zmeta_vocabulary_crosswalk.md` — a dictionary-to-alphabet table
  mapping common deployment concepts (external tracks, detections,
  classifications, geofence alerts, command acks, fleet snapshots,
  heartbeats) onto canonical locked vocabulary, with the enforcement
  surfaces that back each mapping.
- `docs/zmeta_correlation_pattern.md` — cross-sensor correlation expressed
  entirely in existing v1.0 vocabulary: FUSION_EVENT creates the stable
  identity, INFERENCE_EVENT/ASSOCIATION carries bond assignment and
  dissolution (including the atomic-split invariant credited to the upstream
  deployment), and a `payload.extensions.correlation_hint` extension echoes
  fused identity with reference-only, non-reserved keys.

### Extension Registry Governance (governed baseline)

Four new entries in `spec/extension-registry.yaml` (registry entries make no
new vocabulary valid):

- `CORRELATION_HINT` (proposed, fusion_extension, `optional_omission`
  projection) — standardizes the correlation-hint extension name and its
  reference-not-assertion semantics.
- `DATA_REF_MEDIA_METADATA` (proposed, data_evidence,
  `future_branch_required`) — records the media-typing need (RFC-6838
  content type, expiry, descriptor metadata) as a future enrichment of the
  single existing `data_ref` mechanism rather than a parallel convention.
- `AGGREGATE_STATE_SNAPSHOT` (reserved, state_extension,
  `future_branch_required`) — reserves the bulk-snapshot container concept;
  bulk late-join sync is served today by per-entity retained STATE events.
- `PAYLOAD_SCHEMA_URI` (rejected) — records, with rationale, that
  envelope-level external payload schema pointers reintroduce the N-by-N
  problem; the underlying need is served at ingress by adapter mapping
  packs.

### Examples And Conformance

- `examples/zmeta-correlation-pattern-examples.jsonl` — seven runnable
  Profile H events in pure locked v1.0 vocabulary demonstrating the full
  correlation flow: uncorrelated observations, fusion identity creation,
  ASSOCIATION BOND_ASSIGNED, an observation carrying the correlation hint, a
  TRACK_STATE projection, and an atomic-split BOND_DISSOLVED. Registered in
  `tools/validate_examples.py`.
- Two new `conformance/bad-events/must-fail.jsonl` fixtures (corpus total
  23) proving the correlation hint cannot launder `confidence` or `track_id`
  into an observation payload at any nesting depth
  (`OBSERVATION_HAS_IDENTITY`).

### Post-Publication Alignment (carried in this release)

- Current-facing documentation, tool examples, the CI compatibility target,
  and the compatibility CLI test were aligned with the published v1.1.10
  release and then advanced to the v1.1.11 baseline; `tools/check_compat.py`
  gains the `v1.1.11` target. The v1.1.10 publication (tag, GitHub release,
  checksums-only status) is recorded in the handoff/worklog.

## Upstream PR #4 Disposition

The proposals in upstream PR #4 were empirically verified to break the locked
kernel (a v1.2.0 dispatcher arm that accepts `zmeta_version: "1.1.0"` and
drops every locked invariant) and the PR was not merged; the full review with
evidence is posted on the PR. The legitimate fielded needs it surfaced are
addressed in this release as described above, and the remaining candidates
(data_ref media enrichment, aggregate snapshots, first-class correlation
identity) are recorded in the extension registry for the D-003 versioned
semantic branch roadmap.

## Issue Status At Release

- D-003: OPEN - ROADMAP PLANNED for future versioned semantic branch work,
  now additionally informed by the PR #4 field requirements.

## Validation Summary

The release was validated with release manifest and package validation,
strict examples (47 events across 8 corpora), full kernel conformance
(projection, registry, conformance class, encoding-negative,
precision-policy, release-manifest, release-package, bad-event, and adapter
validators), full pytest (444 passed, 110 subtests), gateway self-tests
(Profile H, gateway config, edge config), migration compatibility checks for
all example corpora against `--target v1.1.11`, release artifact builds,
checksum generation and verification, and `git diff --check`.

See `release/VALIDATION_REPORT_v1.1.11.md` for command details.

## Release Assets

Expected release assets:

- `zmeta-v1.1.11-dist.zip`
- `zmeta-edge-v1.1.11.zip`
- `zmeta-gateway-v1.1.11.zip`
- `zmeta-release-package-v1.1.11.zip`
- `zmeta-release-manifest.yaml`
- `RELEASE_NOTES_v1.1.11.md`
- `VALIDATION_REPORT_v1.1.11.md`
- `SHA256SUMS_v1.1.11.txt`

No detached `.asc` signatures are attached unless the release authority signs
the artifacts with an approved external signing process. This release is
published checksums-only, consistent with v1.1.5 through v1.1.10. No private
keys, credentials, tokens, certificates, or signing secrets are stored in
this repository.

## Upgrade Notes

- No event payload, schema, or policy-behavior changes: producers and
  consumers pinned to v1.1.10 (or the locked v1.0 kernel) need no changes.
- Deployments carrying a deployment-local correlation echo on observations
  should adopt the documented `payload.extensions.correlation_hint` key
  shape (`fused_track_ref`, `fusion_revision`, `association_ref`,
  `assigned_by`) and must not place `confidence`, `track_id`, or other
  reserved keys inside it — the recursive observation denylist rejects that
  at any nesting depth (two new fixtures pin this behavior).
- MQTT deployments should review `docs/zmeta_mqtt_binding_guidance.md`,
  especially the retained-state freshness rules and the
  tombstones-are-not-removal-directives rule.
- Deployments using release or contract hash gates should update expected
  hashes from the v1.1.11 release manifest.
