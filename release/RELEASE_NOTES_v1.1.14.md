# ZMeta v1.1.14 Release Notes

Release date: 2026-07-17
Release type: audit-driven honesty hardening patch (R1-10 full stack
audit and its fix-every-finding pass: reference-adapter fabrication
class closed, prose-only honesty invariants machine-encoded, checking
machinery made falsifiable, doc currency machine-pinned)

## Summary

ZMeta v1.1.14 is the product of the R1-10 full stack audit — five audit
lenses derived from the v1.1.13 red-team AAR, every finding
independently adversarially verified — followed by a
fix-every-finding pass and a post-fix verification audit that re-ran
every original audit probe against the fixed tree.

The audit's verdict: the locked kernel and the governance apparatus
held; the defect mass sat in the outer rings, concentrated in the
reference adapters that the authoring guide routes authors to. This
release closes that class end-to-end: the reference RF/EO ingress
adapters now refuse or omit instead of inventing values, the CoT egress
reference renders unknowns honestly by default, honesty invariants that
lived only in prose are machine-checked, and the checking machinery
itself fails loudly where it previously passed vacuously.

The locked v1.0 kernel's semantics are unchanged. The diagnostic
vocabulary widens by four governed codes in both schemas' SYSTEM_EVENT
`reason_code` enums (Class B, the sanctioned additive pattern, now
stated explicitly in contract section 2.1); the v1.1 quality `$def`
gains additive `bearing_frame`/`heading_source` constraints; no event
vocabulary changes and nothing new becomes valid under
`zmeta_version: "1.0"`.

## Major Work Completed

### Reference-adapter honesty pass (audit findings A1-A4)

- example-vendor: null `platform_id`/`sensor_id` are refused uniformly;
  the string-coercion identity laundering path is gone.
- eo-cv: confidence is refused when absent, null, or non-numeric (the
  null-confidence crash path is gone); claim geo is all-or-nothing per
  contract 6.8 (missing altitude omits geo entirely with
  `geo_source: "unavailable"`).
- kraken/moth JSON-replay paths: missing `center_freq_hz`/`power_dbm`
  refuse; missing bearing error omits `angular_error_deg` and
  `quality.measurement_error` (never invents an error bound); moth's
  `geo.alt_m` zero-fill (a contract 6.8 MUST violation) is fixed. The
  receiver-class `bandwidth_hz: 0.0` sentinel is documented in the
  kraken, moth, and signalhunter READMEs.
- CoT egress: unknown accuracy and unknown altitude render as CoT's
  `9999999.0` unknown convention; event time is authoritative by
  default (`use_wall_clock` is an explicit replay-display opt-in per
  contract 9.5); events missing `event.ts` are refused outside
  wall-clock mode; confidence is appended to remarks whenever present;
  the schema-invalid `geo.ce`/`geo.le`/`ce_display_m` dialect rungs are
  removed and the README example validates.

### Machine-encoded honesty invariants (audit findings A5-A7, B1, B4)

- `quality.bearing_frame` (exactly `TRUE_NORTH`) and
  `quality.heading_source` (string) are enforced by a version-agnostic
  semantics check — the lock-compatible route covering v1.0 producers,
  whose only frame-provenance channel this is — and by enum in the v1.1
  schema. New codes `INVALID_QUALITY_BEARING_FRAME` /
  `INVALID_QUALITY_HEADING_SOURCE`.
- INFERENCE fused-state laundering closed: `members` and
  `estimated_state` join `track_id` in the recursive denylist (contract
  7.5); nested smuggling fails `INFERENCE_HAS_FUSION_STATE`.
- Canonical geo at (0,0) draws the warn-severity
  `GEO_ZERO_FILL_SUSPECTED` diagnostic (null-island ambiguity makes
  warn the honest ceiling), and the warning diagnostic itself is
  schema-valid end-to-end.
- Gateway configs that strip `payload.extensions.risk_adjudication` or
  `external_promotion` are rejected at startup — accepted-risk labels
  and promotion evidence stay filterable downstream.
- The adapter harness registers refusal for single-event callables
  (`None` + `event_count: 0`), fails surplus per-event expectations
  (`ADAPTER_EXPECTATION_SURPLUS`), and requires `event_count` alongside
  `expect.events`. Refusal fixtures rolled out across the reference
  adapters: must-pass corpus 15 -> 27; bad-events corpus 23 -> 27.

### Falsifiable checking machinery (audit findings B2, B3)

- All eight JSONL gate tools exit nonzero on empty input instead of
  passing vacuously; `validate_conformance` prints counted results; an
  empty registered examples corpus fails the strict gate.
- Checksum verification fails on zero valid lines and on
  expected-but-unlisted artifacts; new `SHA256SUMS` files are written
  LF so plain `sha256sum -c` works on Linux.
- Stale-default class killed: `check_compat.py`, both bundle builders,
  and `sign_release_artifacts.py` derive their version defaults from
  the release manifest.
- New `gateway/tests/test_release_currency.py` pins the enumerated
  current-facing doc surfaces against the manifest `release_id`; an
  inverse-coverage test pins that every governed violation code is
  emittable as a schema-valid diagnostic.

### Contract clarifications (Class B, audit findings C3, C7)

- Section 2.1 states explicitly that additive governed
  diagnostic-vocabulary widening (SYSTEM_EVENT `reason_code` entries
  mirroring `policy/violation-codes.yaml`) is a governed Class B
  change, not a lock violation.
- Section 5.7 holdover wording is now "must not decrease" (conservative
  quantized upper bound; consecutive equal values valid), matching the
  adjudicated-correct validator behavior.

### Records

- `docs/r1_10_full_stack_audit.md` is the complete audit findings
  record (tiered findings with evidence anchors, refuted items, the
  positive-assurance record, and the fix disposition).
- The worklog R1-10 entries record the audit, the fix pass, the
  post-fix verification audit, and the commit-evidence corrections.

## Compatibility

- No event-vocabulary changes; nothing new becomes valid under
  `zmeta_version: "1.0"` beyond the four governed diagnostic
  `reason_code` entries (diagnostic vocabulary, not event vocabulary).
- Consumers of the reference adapters: input that previously produced
  events with fabricated values now refuses or omits — see the v1.1.14
  Integration Notes in the README for the exact matrix.
- Third-party harness fixtures that pin per-event expectations without
  `event_count` must add it (the fixture lint and harness both enforce
  this now).
- Deployments using release or contract hash gates should update
  expected hashes from the v1.1.14 release manifest.

## Validation

The full command battery and results are in
`release/VALIDATION_REPORT_v1.1.14.md`. Headline: full kernel gate
green with all flags (bad-events 27, adapter harness 27), strict
examples 51/51, full pytest 570 passed + 172 subtests with zero
failures, conformance claims verified including the recorded contract
hash, workflow/live/self-test/packet-size/Docker checks green.

## Assets and Verification

Assets: `zmeta-v1.1.14-dist.zip`, `zmeta-edge-v1.1.14.zip`,
`zmeta-gateway-v1.1.14.zip`, `zmeta-release-package-v1.1.14.zip`,
`zmeta-release-manifest.yaml`, `RELEASE_NOTES_v1.1.14.md`,
`VALIDATION_REPORT_v1.1.14.md`, `SHA256SUMS_v1.1.14.txt`.

Verify asset integrity:

```bash
sha256sum -c SHA256SUMS_v1.1.14.txt
# or, from a repo checkout:
python release/sign_release_artifacts.py --version v1.1.14 --verify-checksums
```

`SHA256SUMS_v1.1.14.txt` is written with LF line endings, so plain
`sha256sum -c` works on Linux checkouts.

Signing decision: this is a checksums-only release — no detached
signatures are attached. Signature generation remains the maintainer's
external release-authority process.
