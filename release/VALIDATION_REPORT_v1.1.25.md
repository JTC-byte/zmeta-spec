# ZMeta v1.1.25 Validation Report

## Scope

What this report covers: the reference implementation, the conformance
corpora, the governed artifacts, and the release packaging for v1.1.25, as
validated on the working tree at the cut.

What it does not cover: any claim about the fielded behavior of downstream
stacks, and any live exercise of the command path. Those remain gated on the
SITL exercise recorded in `docs/zmeta_live_test_checklist.md`.

## Validation executed at the cut (2026-08-13, local)

Full test battery:
`python -m pytest -q`
Result: 1836 passed, 2 skipped, 1109 subtests passed, run with every
release artifact in place so the completeness gate's signature requirement
was exercised live. The two skips are the changelog guard's post-release
idle states (worklog activity date equals the release date).

Kernel protection gates:
`python tools/validate_conformance.py --kernel-gate`
Result: exit 0. Projection conformance 37, extension registry 63 entries,
conformance classes 34 with 2 claims, encoding negative 50, profile precision
policy 41, bad-event corpus 36 (grown by the two RF zero-fill warn vectors,
the corpus's first warn-severity entries), adapter conformance 53, core
conformance pass=21 fail=42.

Examples:
`python tools/validate_examples.py --strict --require-all`
Result: overall total=51 passed=51 failed=0 warnings=0.

Roadmap:
`python tools/validate_future_roadmap.py`
Result: ok, candidates=19, rejected_or_deferred=3.

Release manifest:
`python tools/validate_release_manifest.py`
Result: ok, groups=20, artifacts=84, rebuilt with `--update-claims` after
the doc-currency pass settled; the claims release-hashes gate passed
against the rebuilt pair.

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
release-focus governance sentence check, which for this release reports
the governed delta rather than byte-identity.

Live runtime harnesses (first firing of the runtime-code checklist step):
`python tools/test_gateway_live.py` and
`python tools/test_workflow_end_to_end.py`
Result: both exit 0. The live gateway forwarded all four event types and
emitted CoT; the end-to-end workflow completed.

Gateway Docker build and run (re-run because runtime code changed):
`docker compose -f deploy/gateway/docker-compose.yml up`
Result: pass, with the mint exercised through the container boundary. A
valid event forwarded with its event_id intact; an RF pair-zero event
forwarded (accepted, not dropped) and the gateway emitted the warning
diagnostic on the wire with `reason_code: GEO_ZERO_FILL_SUSPECTED` (the
documented v1.0 fallback) and `diagnostic_code: RF_ZERO_FILL_SUSPECTED`.

Contract hash:
`python tools/compute_contract_hash.py`
Result: the combined contract hash CHANGED at this cut, as expected and
for the first time since the v1.0 lock's current hash chain: the policy
bundle is a governed input to it and `policy/violation-codes.yaml` and
`policy/semantics.yaml` moved with the mint. The semantic contract file
itself is byte-identical to every release since the lock, as is the v1.0
schema, both pinned by their own guards.

## Verification method statement

This release is a governed Class B vocabulary mint, so the verification
burden sat on the mint's semantics, not only its mechanics. Verified
mechanically, before the cut:

- **Two adversarial passes, both load-bearing.** The first pass (two-lens,
  after the initial implementation) found that the first-draft predicate
  (bandwidth-alone) collided with the repository's own documented
  receiver-class sentinel and would have turned five adapter families'
  sanctioned output into strict-mode failures; the maintainer
  re-adjudicated to the paired predicate. The second pass verified the
  revised design empirically: twelve real-adapter sentinel emissions
  produce zero RF_ZERO_FILL_SUSPECTED violations under strict mode, the
  counterfactual first-draft predicate trips five families on the same
  inputs, and the field signature is caught at all three feature
  containers.
- **The lock defended itself.** A first draft added the code to the locked
  v1.0 schema enum; the byte-anchor guard rejected it, forcing the
  documented post-lock path (native in the 1.1.0 enum, the documented
  v1.0 wire fallback, carve-outs in the registry sweeps). The v1.0 schema
  in this release is byte-identical to its anchor.
- **The wire fallback proven end to end.** build_warning_event with policy
  produces a self-valid v1.0 diagnostic carrying the fallback reason_code,
  the native code in metrics.diagnostic_code, and the offending path; the
  same was demonstrated through a running container.
- **Guard non-vacuity.** The corpus runner's warn arm was mutation-tested
  (a doctored expect_severity is rejected); the eight-case unit suite
  pins both trigger arms, both sanctioned non-triggers, all three
  containers, the negative-zero and integer-zero shapes, and the
  wire-shaped junk paths.

## Known limits of this validation

The RF zero-fill predicate is exact-pair equality by design. A mapping
that fabricates non-zero placeholder values, or zero-fills only one of
the pair while fabricating the other, is not labeled by this heuristic;
the honest-omission rule and schema requirements remain the primary
control, and the generalized contract clause is recorded as
versioned-semantic-branch material in doctrine entry X2-04.

The locked v1.0 lane still accepts any string ending in `Z` as `event.ts`,
per doctrine X1-01, unchanged from v1.1.24.

## Signing decision

Signed release. The release authority, Justin Carr (Incept.IO), directed
this signed cut on 2026-08-13 with the Incept.IO ZMeta release signing key
`A3B150AF2A0E1CA413C4B7F112BE81F54654B96E`, continuing the practice
resumed at v1.1.23. Key existence was re-derived at this cut with the gpg
binary the signing tooling resolves. Detached signatures are generated for
`SHA256SUMS_v1.1.25.txt` and every release asset, and verified after
generation; the completeness gate enforces the tracked signature trio
mechanically.
