# ZMeta v1.1.18 Validation Report

Release date: 2026-07-27
Release target: `v1.1.18`

## Scope

This report covers the ZMeta v1.1.18 release: the nine commits after the
published v1.1.17 tag — two post-release CI hotfixes (the compact encode
depth guard preceding the backends; the EOL-agnostic v1.0 byte-identity
pin), the kernel-adjacent residual wave (VW-01 naive-timestamp seam and
H1-07 plain-`cbor` envelope), the bladeRF reference ingress adapter and
its registration set, the deployment verification plus `cot.config`
pass-through and two-node quickstart, and the UxS command-loop pair
(command-evidence gate and track-lifecycle groundwork) — followed by a
bounded four-lens pre-cut review of that whole range and its fixes.

The locked v1.0 kernel is unchanged. No schema file, event vocabulary, or
`reason_code` was added in this release.

## Validation executed at the cut (2026-07-27, local)

- Full kernel-protection conformance, all flags: exit 0.
- Strict examples corpus: 51/51 passed, 0 warnings.
- Full pytest suite: **1420 passed + 1070 subtests** (v1.1.17 cut:
  1284 + 1051).
- Adapter conformance harness: 48/48 (includes the 8 new `bladerf-`
  fixtures).
- `tools/lint_policy_risk_modes.py`: ok — now covering the new
  command-evidence block, including the key-name and value-type lint
  added by the pre-cut review.
- `tools/lint_adapter_vocabularies.py`: ok.
- `tools/validate_future_roadmap.py`: ok (candidates=18,
  rejected_or_deferred=3).
- Profile L packet-size check: max 150 bytes against the 240-byte budget.
- Release manifest rebuilt under the v1.1.18 identity with explicit
  `--branch` provenance and `--update-claims`; validated inside the
  conformance run. This cut resolves the in-repo manifest divergence that
  accumulated while post-release commits regenerated under the v1.1.17
  identity; published `SHA256SUMS_v1.1.17.txt` is untouched.
- Release package built in no-signature mode with the real v1.1.18
  release notes and validated; `SHA256SUMS_v1.1.18.txt` generated and
  verified.

## Deployment verification (new this release)

The gateway container was built and run from the stock compose files on
two architectures: x86-64 natively and ARM64 under QEMU emulation (the
Raspberry Pi rehearsal). On both, dependencies resolved from wheels, the
gateway bound and processed the example corpus with zero violations, and
the four startup hash lines (schema, policy, semantics, contract) were
byte-identical across architectures. The platform-divergence test pins
were additionally run inside the ARM64 container: 98 passed + 232
subtests, with one environmental failure only (a test requiring a
writable scratch directory under the deliberately read-only deployment
mount).

## Verification method statement

Every code change in this release was reproduced before it was fixed,
pinned red-first, and adversarially attacked by an independent pass
before its wave closed. The whole range was then re-reviewed cold by four
lenses at release stakes, with every candidate finding independently
verified before it was believed: 13 confirmed, 0 refuted, all closed
before this cut. Three of those thirteen — a re-send that could erase a
recorded command prohibition, a typo-fails-open gap in the new policy
block, and non-finite values reaching two bladeRF feature arms — were
missed by the per-wave attacks and caught only by the cold range read.

## Known limits of this validation

- GitHub CI for the release commit runs only after the maintainer pushes;
  it was green for every pushed commit in this range, and the CI
  compatibility target is re-baselined to v1.1.18 in this cut.
- Real-hardware Raspberry Pi throughput is not measured; emulation
  verifies build, dependency resolution, startup, and semantics only.
- TAK/COP display validation against live tooling has not been performed;
  the `cot.config` pedigree knob that enables `<precisionlocation>`
  detail is shipped and pinned but exercised only by tests.
- SAPIENT live-enclave validation against the official C# BSI Flex 335
  harness and multi-node Apex routing remain not-exercised (recorded
  since v1.1.15).
- The SITL end-to-end gate that precedes live GCS-originated tasking has
  not been run; the command-evidence check is its repo-side prerequisite,
  not a substitute for it.
- Open-by-design items are recorded, not hidden: the cold re-read
  appendix (VW-01..17) and the doctrine review log's open tensions
  (R1-11 entries plus H1-01..08).

## Signing decision

Checksums-only, consistent with v1.1.5 through v1.1.17. No detached
signatures are attached unless the maintainer adds them at publish.
