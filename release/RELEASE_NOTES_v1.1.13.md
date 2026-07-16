# ZMeta v1.1.13 Release Notes

Release date: 2026-07-16
Release type: onboarding and machine-checked refusal patch (adapter
authoring guide, worked exercise adapter, one-command validation ladder,
EO full-chain corpus, structured intake templates, adapter-harness refusal
fixtures)

## Summary

ZMeta v1.1.13 makes the standard deliberately easy to build against — for
human developers and for AI coding agents — without loosening anything.
It ships the consolidated adapter authoring guide (`adapters/AUTHORING.md`),
a complete worked exercise adapter implementing the example-vendor mapping
pack, a one-command wrapper for the tool-based validation-ladder steps, a
worked EO full-chain example corpus, structured GitHub intake templates for
the external-PRs-are-field-telemetry doctrine, and — the release's
enforcement centerpiece — adapter-harness **refusal fixtures**: the harness
can now machine-pin fail-closed behavior (`expect.event_count: 0`) the same
way `must-pass` fixtures pin emission.

The authoring guide and worked adapter were hardened by a full external
red-team review before merge; the review's lessons are institutionalized in
the guide itself (schema minimums are per-subtype; four review-proven agent
failure modes) and mechanically encoded as the refusal fixtures in this
release.

It adds no schema changes and no event vocabulary; nothing new becomes
valid under `zmeta_version: "1.0"` or `"1.1.0"`. The locked v1.0 kernel is
unchanged. No adapter emission behavior changed in this release; the
example-vendor exercise adapter is new reference code.

## Major Work Completed

### Adapter authoring path (advisory docs + reference code)

- `adapters/AUTHORING.md`: single consolidated authoring entry point —
  orientation, the decoded-input floor, layer choice, the ten
  anti-fabrication non-negotiables with contract cites, the exact
  validation command ladder, a formal adapter-harness fixture-key
  reference, producer-authority notes, definition-of-done, and AI-agent
  guardrails including four review-proven failure modes.
- `adapters/ingress/example-vendor/`: worked exercise adapter implementing
  the `example-vendor-pack` declarative mapping to the guide's
  requirements — fail-closed refusal of readings missing any
  schema-required RF feature, all-or-nothing canonical geo, omit-or-refuse
  lineage with `translate:` transform, visible degraded timing, UUIDv7
  identity, no confidence on OBSERVATION. 12 colocated tests.
- `tools/check_adapter.py`: one-command wrapper for the tool-based ladder
  steps (fixture lint, `validate.py --strict`, `check_compat.py` with the
  target defaulted from the release manifest, adapter harness, optional
  kernel gate). Pure delegation to the governed validators plus a strictly
  additive advisory fixture lint; fails on empty input instead of passing
  vacuously.
- `examples/zmeta-eo-chain-examples.jsonl`: worked EO
  `OBSERVATION -> INFERENCE -> FUSION -> STATE` chain with genuine chained
  lineage, policy-allowed producers, a local `data_ref` video pointer, and
  the eo-cv reference adapter's exact dialect (`claim.bbox` corner format,
  `translate:eo-cv-detection@1.1.0`). Strict example corpus 47 -> 51.

### Adapter-harness refusal fixtures (Class B, maintainer-directed)

- `tools/validate_adapter_conformance.py` gains `expect.event_count`: an
  exact pin on how many events a fixture callable returns. A mismatch is
  `ADAPTER_EVENT_COUNT_MISMATCH`; a non-integer or negative value is a
  fixture error. `event_count: 0` with `result: "events"` pins fail-closed
  refusal.
- `conformance/adapter-harness/must-pass.jsonl` grows 11 -> 15: an
  example-vendor emission fixture (field mapping, visible `UNSYNCED`
  degraded-timing fallback, lineage omit-not-fabricate pinned via
  `forbidden_paths`) plus one refusal fixture per schema-required RF input
  field (`bandwidth_hz`, `center_freq_hz`, `power_dbm`).
- `conformance/adapter-harness/fixture.schema.json` learns `event_count`,
  and `gateway/tests/test_fixture_schema_sync.py` pins the advisory lint
  schema to the harness's actual fixture surface so future harness keys
  cannot silently become false lint failures.

### Intake, first contact, and retention

- GitHub issue templates (adapter authoring friction, semantic ambiguity
  report, deployment field report — labeled `adapter-authoring`,
  `semantic-ambiguity`, `field-telemetry`) and a PR template carrying the
  change-class/validation/no-secrets checklist.
- README restructured for first contact: What Is/Is Not first, a
  "See It Work In Ten Minutes" runnable proof path, persona-based
  "Start Here By Role", and "ZMeta In The Field" deployment provenance.
- `docs/README.md` guidance-vs-process index; worklog sections
  S0-01..R1-05 archived verbatim to
  `docs/zmeta_refinement_worklog_archive.md`; `RELEASE_CHECKLIST.md` gains
  standing doc-currency and retention-pass items (exercised for the first
  time by this release, and already improved by it: the doc-currency item
  now also names the release-manifest `release_id`/`release_date` test
  pins).

## Validation

Full command list and results in `release/VALIDATION_REPORT_v1.1.13.md`.
Highlights: full kernel gate green (projection 37, extension registry 61,
conformance classes 34/2, encoding-negative 50, precision 32, bad-events
23, adapter harness **15**); strict examples 51/51; compat sweep of all
nine example corpora against `--target v1.1.13` clean; full pytest
483 passed + 110 subtests, zero failures; gateway self-tests (H, gateway
config, edge config) ok; workflow end-to-end (H and M) and live gateway
(H, and L/compact) runs ok; containerized gateway (compose) started,
verified contract hashes, and forwarded replayed traffic with zero
violations; packet-size check within Profile L limits; release artifact
builds, checksum generation and verification, and `git diff --check`.

## Release Assets

Expected release assets:

- `zmeta-v1.1.13-dist.zip`
- `zmeta-edge-v1.1.13.zip`
- `zmeta-gateway-v1.1.13.zip`
- `zmeta-release-package-v1.1.13.zip`
- `zmeta-release-manifest.yaml`
- `RELEASE_NOTES_v1.1.13.md`
- `VALIDATION_REPORT_v1.1.13.md`
- `SHA256SUMS_v1.1.13.txt`

No detached `.asc` signatures are attached unless the release authority
signs the artifacts with an approved external signing process. No private
keys, credentials, tokens, certificates, or signing secrets are stored in
this repository.

## Upgrade Notes

- No schema or vocabulary changes: producers and consumers pinned to
  v1.1.12 (or the locked v1.0 kernel) need no changes.
- Adapter authors: start at `adapters/AUTHORING.md`; run the ladder with
  `python tools/check_adapter.py --events <yours>.jsonl --fixtures
  <yours>.jsonl`. Ship refusal fixtures (`event_count: 0`) for every
  schema-required input field your adapter consumes — the example-vendor
  fixtures are the worked pattern.
- Existing fixture files are unaffected: `event_count` is optional and no
  existing fixture key changed meaning. The advisory fixture lint schema
  accepts old fixtures unchanged.
- `tools/check_compat.py` gains the `v1.1.13` target; CI and
  `tools/check_adapter.py`'s manifest-derived default target re-baseline
  to it.
- Deployments using release or contract hash gates should update expected
  hashes from the v1.1.13 release manifest.
