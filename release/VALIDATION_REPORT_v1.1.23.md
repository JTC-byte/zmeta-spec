# ZMeta v1.1.23 Validation Report

## Scope

What this report covers: the reference implementation, the conformance
corpora, the governed artifacts, and the release packaging for v1.1.23, as
validated on the working tree at the cut.

What it does not cover: any claim about the fielded behavior of downstream
stacks, and any live exercise of the command path. Those remain gated on the
SITL exercise recorded in `docs/zmeta_live_test_checklist.md`.

## Validation executed at the cut (2026-08-13, local)

Full test battery:
`python -m pytest -q`
Result: 1789 passed, 2 skipped, 1105 subtests passed. The two skips are the
changelog guard's post-release idle state (worklog sentinel equals the
release date), the same state v1.1.22 shipped with.

Kernel protection gates:
`python tools/validate_conformance.py --kernel-gate`
Result: exit 0. Projection conformance 37, extension registry 63 entries,
conformance classes 34 with 2 claims, encoding negative 50, profile precision
policy 41, bad-event corpus 34, adapter conformance 53, core conformance
pass=21 fail=42.

Examples:
`python tools/validate_examples.py --strict --require-all`
Result: overall total=51 passed=51 failed=0 warnings=0.

Roadmap:
`python tools/validate_future_roadmap.py`
Result: ok, candidates=19, rejected_or_deferred=3.

Release manifest:
`python tools/validate_release_manifest.py`
Result: ok, groups=20, artifacts=84, built with `--update-claims` in the
same run per the hardened checklist, so the example claims'
`release_hashes` match the manifest they sit beside.

Consumer risk-filter presets:
`python -m pytest -q gateway/tests/test_risk_filter_cli.py`
Result: 6 passed.

Profile L packet size:
`python tools/measure_packet_size.py --file
examples/zmeta-profile-L-examples.jsonl --encodings compact,proto
--max-bytes 236 --max-bytes-encoding compact --summary-only --validate`
Result: pass; compact min=98 avg=116.0 max=150, proto min=271 avg=287.0
max=301.

Doc currency:
`python -m pytest -q gateway/tests/test_release_currency.py`
Result: 29 passed after the doc-currency pass, including the
release-focus governance sentence check against the regenerated governed
baseline.

Contract hash:
`python tools/compute_contract_hash.py`
Result: schema, policy, semantics and combined contract hashes computed and
unchanged from v1.1.22, which is the expected outcome for a release whose
governed artifacts are byte-identical to its predecessor.

## Verification method statement

The claims that carry this release's weight are about records and about the
absence of change, and absence is the class this project has repeatedly
failed to verify by reading prose. Each was demonstrated mechanically:

- **Byte-identical kernel.** The governed baseline was regenerated from the
  v1.1.22 manifest before the version bump, and the release-focus currency
  test asserts the generated no-governed-change sentence against that
  baseline rather than against hand-written prose. The manifest diff at the
  cut shows the semantic contract, schema, policy, registry, corpora and
  encoding group hashes unchanged from v1.1.22.
- **Force-push residue.** The merged range `6530724..36345fb` was diffed
  file-by-file and grepped for the withdrawn registration: zero occurrences
  of `EVENT_TS_IMPLAUSIBLE` in the range, zero changes under `policy/`,
  `conformance/claims/`, `release/`, `schema/`, or either wire-emittability
  sweep the withdrawn commit had carved out.
- **Guard tests non-vacuous.** The three fixes' set-equality guards were
  mutation-tested during review: six probes (wrong value, deleted value,
  bogus added value, on each side) were each killed by the matching test.
- **Changelog guard probed in both directions.** On a detached merge probe
  of the PR against develop, the guard passed with the contributor's
  sentinel and was then shown failing under an honestly-corrected sentinel
  with the maintainer wave still unrecorded, which is the state the
  companion record commit repaired before this cut. The guard runs
  un-skipped and green on the completed record, and idles post-release by
  design.
- **Package state.** The release package was built with
  `--release-state formal_release` and the real release notes, and
  validated in package mode before tagging, closing both v1.1.22 packaging
  traps.

## Known limits of this validation

The gateway Docker build-and-run item was not executed at this cut: the
Docker daemon was not running on the cut machine. No shipped file in this
release differs in a way a container build would exercise (documentation,
test guards, and records only); the item should run at the next cut that
changes runtime code.

The repo-wide markdown walker in `test_records_claim_currency.py` retains
the stale-worktree exposure that PR #8 fixed in the profile-claims walker;
the shared-exclusion fix is queued, and the exposure is documented in the
worklog entry for the wave.

The timing-quality helper finding reported on PR #8 (a supplied invalid
enum value survives `coerce_timing_quality()` and fails schema validation
far from its cause) is confirmed, flagged, and deliberately not fixed here:
whether a present-but-invalid value is rejected or degraded is a contract
decision, and it is queued for adjudication rather than resolved inside a
release wave.

The locked v1.0 lane still accepts any string ending in `Z` as `event.ts`,
per doctrine X1-01, unchanged from v1.1.22.

## Signing decision

Signed release. The release authority, Justin Carr (Incept.IO), decided on
2026-08-12 to resume signing with the original Incept.IO ZMeta release
signing key `A3B150AF2A0E1CA413C4B7F112BE81F54654B96E` (ed25519, created
2026-04-28, expires 2028-04-27), chosen for verifier continuity with signed
v1.1.2 through v1.1.4, and directed this signed cut on 2026-08-13. Key
existence was re-derived at this cut with the gpg binary the signing
tooling resolves, which lists exactly this one secret key. Detached
signatures are generated for `SHA256SUMS_v1.1.23.txt` and every release
asset, and verified after generation. This ends the checksums-only chain
recorded in doctrine pressure log X2-02.
