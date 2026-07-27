# ZMeta v1.1.17 Validation Report

Release date: 2026-07-27
Release target: `v1.1.17`

## Scope

This report covers the ZMeta v1.1.17 release: the entire held R1-11
cycle — the pre-audit hardening waves, the fresh full-stack audit and
its six-blocker fix pass, two post-fix verification passes, the
disposition pass, the 2026-07-26 fresh-eyes cold re-read (30 confirmed
findings, recorded), the 2026-07-27 health fix wave (3 MAJORs + 8
MODERATEs closed, every fix red-first pinned and adversarially
attacked), and the 2026-07-27 maintainer-adjudicated governed waves
(compact fail-closed clause; TIME_STATUS.state Class B enum, v1.1.0
only). The locked v1.0 kernel is unchanged and pinned byte-identical
by test.

## Validation executed at the cut (2026-07-27, local)

- Full kernel-protection conformance, all flags
  (`tools/validate_conformance.py --strict --profile-projection
  --extension-registry --conformance-classes --encoding-negative
  --precision-policy --release-manifest --release-package --bad-events
  --adapter-harness`): exit 0. Groups: encoding-negative 50, precision
  32, bad-events 30, adapter harness 40, extension registry 61 entries.
- Strict examples corpus (`tools/validate_examples.py --strict
  --require-all`): 51/51 passed, 0 warnings.
- Full pytest suite: **1284 passed + 1051 subtests** (cycle start:
  785 + 316). Includes the release-currency, records-claim-currency,
  release-manifest/package, risk-filter-preset, and packet-size suites.
- Adapter vocabulary lint (`tools/lint_adapter_vocabularies.py`): ok
  (five registered mirrors against both published schemas).
- Release manifest rebuilt under the v1.1.17 identity with explicit
  `--branch` provenance and `--update-claims`; validated by
  `tools/validate_release_manifest.py` inside the conformance run.
  This cut resolves the documented in-repo divergence (A-12) that
  existed while fix-pass commits regenerated the manifest under the
  v1.1.16 identity; published `SHA256SUMS_v1.1.16.txt` is untouched.
- Release package built in no-signature mode with the real v1.1.17
  release notes and validated; SHA256SUMS_v1.1.17.txt generated and
  verified (see the checksum file beside this report).

## Verification method statement

Every code fix in this release was reproduced before it was fixed,
pinned red-first (the failing run captured before the fix), and the
fix set was adversarially attacked by an independent pass before its
wave closed; candidate MAJOR findings faced multi-lens refutation
panels. Introduced-defect rate across the final waves: one finding at
MODERATE-or-above for the entire health batch, fixed the same day —
far under the playbook's one-third cap.

## Known limits of this validation

- GitHub CI for the release commit runs only after the maintainer
  pushes; it was green for the last pushed commit and the CI
  compatibility target has been re-baselined to v1.1.17 in this cut.
- The gateway Docker build/run was not exercised in this cut's local
  environment (Windows host); the Dockerfile and compose config are
  unchanged this cycle.
- Live-enclave SAPIENT validation against the official C# BSI Flex 335
  harness and multi-node Apex routing remain not-exercised (recorded in
  the pack README since v1.1.15).
- Open-by-design items are recorded, not hidden: the cold re-read
  appendix (VW-01..13 register candidates) and the doctrine review
  log's open tensions (15 R1-11 entries, H1-01..07).

## Signing decision

Checksums-only, consistent with v1.1.5 through v1.1.16. No detached
signatures are attached unless the maintainer adds them at publish.
