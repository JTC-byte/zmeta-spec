# ZMeta v1.1.24 Validation Report

## Scope

What this report covers: the reference implementation, the conformance
corpora, the governed artifacts, and the release packaging for v1.1.24, as
validated on the working tree at the cut.

What it does not cover: any claim about the fielded behavior of downstream
stacks, and any live exercise of the command path. Those remain gated on the
SITL exercise recorded in `docs/zmeta_live_test_checklist.md`.

## Validation executed at the cut (2026-08-13, local)

Full test battery:
`python -m pytest -q`
Result: 1822 passed, 2 skipped, 1105 subtests passed, run with every
release artifact in place so the completeness gate's new signature
requirement was exercised live and green. The two skips are the
changelog guard's post-release idle states (worklog activity date equals
the release date), the same class every release since the guard landed
has shipped with.

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
Result: ok, groups=20, artifacts=84, rebuilt with `--update-claims` after
the doc-currency pass settled, so the example claims' `release_hashes`
match the manifest they sit beside; the new
`test_claims_release_hashes_currency.py` gate asserts the same equality
mechanically and passed against the rebuilt pair.

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
unchanged from v1.1.23, which is the expected outcome for a release whose
governed artifacts are byte-identical to its predecessor.

## Verification method statement

This wave's changes are guards and a shared-helper behavior fix, so the
verification burden sat on two questions: do the new guards actually catch
the states they exist for, and did the helper fix introduce anything the
old code did not have. Both were answered mechanically, before the cut:

- **Adversarial pass on the wave itself.** A four-lens verification fleet
  attacked the uncommitted wave (code correctness, guard vacuity, mutation
  kills, record accuracy). It found two blocking regressions in the wave's
  own first draft: the degrade guard crashed on unhashable wire values,
  and a NaN error bound rode the enum degrade into a schema-clean event
  that the pre-wave schema gate had rejected. Both were fixed and pinned
  by tests before this cut, and the battery adjudicated the NaN fix's
  collision with SAPIENT's refusal contract toward poisoned-bound
  pass-through.
- **Mutation kills.** Reverting the helper degrade kills five tests across
  two files; restoring the CLI's first-violation-only print kills two of
  the diagnostic guard tests; removing the worktrees exclusion from the
  shared module kills its pin. Each revert was executed in a scratch
  worktree and each kill observed.
- **Guard non-vacuity.** Every new guard carries an in-file red
  demonstration: the claims gate doctors a stale hash and sees it named,
  the changelog guard reproduces the contributor-boundary state that
  silenced its predecessor, the completeness gate removes each required
  artifact in turn including the signature trio, the slot-token guard
  runs against the exact pre-fix authoring text, and the snapshot module
  pins the stale-worktree shape in-repo.
- **Behavior non-regression.** All nine example corpora produce
  byte-identical accept/reject/warning tallies against the pre-wave HEAD;
  the grep over every fixture and corpus found no in-repo input whose
  translation changes under the helper fix.
- **Package state.** The release package was built with
  `--release-state formal_release` and the real release notes, and
  validated in package mode before tagging.

## Known limits of this validation

The gateway Docker build-and-run item was not executed at this cut: the
Docker daemon was not running on the cut machine. No shipped file in this
release differs in a way a container build would exercise (tooling
diagnostics, test guards, documentation, and one adapter-helper fix whose
suites run in the battery); the item should run at the next cut that
changes gateway runtime code.

The slot-token guard is lexical and line-scoped: cross-slot laundering on
a line naming two slots, lowercase misuse, and continuation-line tokens
pass it, as its known-limits paragraph documents.

The changelog guard remains blind when both record surfaces lag together,
as its docstring documents; the sentinel-mismatch failure and
entry-derived date close the contributor-boundary instance only.

The locked v1.0 lane still accepts any string ending in `Z` as `event.ts`,
per doctrine X1-01, unchanged from v1.1.23.

## Signing decision

Signed release. The release authority, Justin Carr (Incept.IO), directed
this signed cut on 2026-08-13, continuing the 2026-08-12 decision to sign
with the original Incept.IO ZMeta release signing key
`A3B150AF2A0E1CA413C4B7F112BE81F54654B96E` (ed25519, created 2026-04-28,
expires 2028-04-27). Key existence was re-derived at this cut with the gpg
binary the signing tooling resolves. Detached signatures are generated for
`SHA256SUMS_v1.1.24.txt` and every release asset, and verified after
generation. From this release the completeness gate enforces the tracked
signature trio mechanically.
