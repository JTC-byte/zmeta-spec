# ZMeta v1.1.21 Validation Report

Release date: 2026-08-09
Release target: `v1.1.21`

## Scope

This report covers the ZMeta v1.1.21 release: every commit after the
published `v1.1.20` tag. The count is deliberately not asserted here; it
is derivable (`git rev-list --count v1.1.20..v1.1.21`), per the
moving-fact rule the v1.1.20 report adopted. The wave landed as four
adjudicated units (a records pass, the R1-11-01 Class B reason-code mint
with the v1.1.21 identity opening, the A1-01 power-reference experimental
split, and doctrine cycle B1) followed by a pre-cut panel fix wave and
this cut.

The locked v1.0 kernel is unchanged: `git diff v1.1.20..HEAD` over
`schema/zmeta-event-1.0.schema.json` and the locked contract sections is
empty, and the byte-identity anchors in
`gateway/tests/test_v1_lock_baseline.py` hold. Governed artifacts changed
relative to `zmeta-v1.1.20`: `policy/semantics.yaml`,
`policy/violation-codes.yaml`, `schema/zmeta-event-1.1.0.schema.json`,
`spec/compact-binary-mapping.md`, `spec/extension-registry.yaml`.

## Validation executed at the cut (2026-08-09, local)

- Full kernel-protection conformance, all flags: exit 0, including the
  extension-registry gate over the new POWER_REFERENCE entry.
- Strict examples corpus: 51/51 passed, 0 warnings.
- Full pytest suite at the prepared tree: the count and its exit code
  are recorded in the cut-prep commit message, since this report is
  hashed by the checksums and cannot describe the run that happens after
  they are written. At the last pre-artifact run the suite was 1730
  passed + 1093 subtests with exactly one red,
  `test_release_artifact_completeness`, red by design until this report
  and the checksums exist.
- Adapter conformance harness: 53/53. Profile precision policy: 41
  fixtures ok.
- Release manifest validated; checksummed assets verified with
  `sha256sum -c` and with the signer's own `--verify-checksums` before
  any tag, per the both-ways ordering rule the v1.1.20 cut established.

## Verification method statement

The pre-cut review ran as a six-lens fresh-eyes panel over the whole
wave as one surface (governed coherence, mint runtime behavior, A1-01
adapter honesty, records accuracy, release surfaces, test vacuity), with
one adversarial verifier per finding instructed to refute and defaulting
to refuted when evidence did not reproduce. Twenty-nine agents ran; 23
raw findings resolved to 3 refuted with evidence and 20 confirmed,
deduplicating to 12 distinct defects. The finding-by-finding record with
dispositions is `docs/v1_1_21_precut_panel_register.md`; ten were fixed
in the cut-prep commit and two are banked on the register with their
reasons. The panel's strongest catch was a half-updated release pointer
in the handoff asserting the previous release was unpublished, found
independently by five of the six lenses.

Where a claim enumerates, it is generated: the governance sentence in
the README release-focus bullet, the release-currency surface set, and
the artifact completeness set are all machine-checked against the
manifest.

## Known limits of this validation

- The A1-01 experiment ships mechanism, not evidence. Whether any
  consumer needs a declared power reference is exactly the open field
  question (checklist A1-01), and the registry entry records that the
  in-repo implementations are same-origin. Promotion requires
  independent evidence that does not exist yet.
- The diagnostic-first fallback is exercised by the reason-code sweeps
  and end-to-end pins; no fielded v1.0 consumer has yet been observed
  reading `metrics.diagnostic_code`. The member is additive and
  ignorable by construction.
- Banked from the panel, on the register: two wave commit subjects use
  the barred aphoristic cadence (local history, maintainer may reword
  before push); the `CallSitePolicyCoverage` lint does not yet require
  `policy=` at build sites where the fallback is load-bearing.
- The B1-01 geo-referent gap is recorded, not fixed: the normative
  sentence and the sensor-position adapters' conformance wait for a
  scheduled wave, and until then a line-of-bearing adapter's `geo` is
  the sensor, as the entry states.
- The SITL end-to-end gate and the fielded TAK render check for
  `<geo_dimensionality>` remain outstanding from v1.1.20's known
  limits, unchanged by this release.

## Signing decision

Checksums-only, consistent with v1.1.5 through v1.1.20. No detached
signatures are attached unless the maintainer adds them at publish.
