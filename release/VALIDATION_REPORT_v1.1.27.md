# ZMeta v1.1.27 Validation Report

## Scope

What this report covers: the reference implementation, the conformance
corpora, the governed artifacts, and the release packaging for v1.1.27, as
validated on the working tree at the cut.

What it does not cover: any claim about the fielded behavior of downstream
stacks beyond what the adapter README states for the `cds` CoT profile (one
deployment, one partner's guard, one day, and a stale cap that guard has not
seen), the relation the new section 7.6 sentence states, which no validator
reads yet, and any live exercise of the command path. Those remain gated on
the SITL exercise recorded in `docs/zmeta_live_test_checklist.md`.

## Validation executed at the cut (2026-10-27, local)

The merge the cut rests on, dcf3428 (`exp/last-seen-ts-7-6` into
`develop`), was re-verified first on the tree as pushed: the kernel gate's
eleven `RELEASE_MANIFEST_*` lines and nothing else (the release-pin band,
red by design until this cut), examples 51 of 51, the lock baseline 5 of 5,
the full battery 13 failed (`test_release_manifest.py` 3,
`test_release_package.py` 10, the release-pin set), 2011 passed, 1 skipped,
and `git diff --check` clean.

Full test battery on the cut tree:
`python -m pytest -q`
Result, run before the checksums and the signatures existed: 2 failed, 2019
passed, 4 skipped, 1269 subtests passed, in 64 s. The two failures are the
two completeness checks in `test_release_artifact_completeness.py`, each
naming exactly the five tracked artifacts not yet made at that run (this
report, `SHA256SUMS_v1.1.27.txt` and the three detached signatures): the
gate seen failing for the right reason before it is asked to pass. The four
skips: the changelog guard's two post-release idle states (the worklog
activity date equals the release date), the release-package test that waits
for a built package directory (built after this run; see Release package
below), and the
public CoT event schema test (the schema is not vendored; it passed with
`COT_EVENT_XSD` set, see below). The battery run with the signed artifact
set in place is recorded in the worklog's publication entry, because the
checksums hash this report.

Kernel protection gates:
`python tools/validate_conformance.py --kernel-gate`
Result: exit 0 after the release manifest was rebuilt. Projection
conformance 37, extension registry 68 entries, conformance classes 34 with
2 claims, encoding negative 50, profile precision policy 41, bad-event
corpus 36, adapter conformance 53, core conformance pass=21 fail=42. Before
the rebuild the gate read the eleven release-manifest mismatch lines of the
recorded band (the registry, the roadmap, the contract and the must-pass
vector, their groups, the two top-level hashes and the bundle hash) and
nothing else.

Examples:
`python tools/validate_examples.py --strict --require-all`
Result: overall total=51 passed=51 failed=0 warnings=0.

Roadmap:
`python tools/validate_future_roadmap.py`
Result: ok, candidates=22, rejected_or_deferred=3.

Release manifest:
`python tools/validate_release_manifest.py`
Result: ok, groups=20, artifacts=86, rebuilt with `--update-claims` after
the governed baseline was written from the v1.1.26 manifest and before the
notes and this report were written. The generated governance sentence names
the two policy variants, `conformance/must-pass.jsonl`,
`spec/extension-registry.yaml` and `spec/semantics-contract.md`, and the
README carries it verbatim.

Release package:
`python tools/build_release_package.py --manifest
release/zmeta-release-manifest.yaml --output-dir release/package-v1.1.27
--release-id zmeta-v1.1.27 --release-state formal_release --no-signatures
--allow-dirty --clean-output --release-notes release/RELEASE_NOTES_v1.1.27.md`,
then `python tools/validate_release_package.py --manifest
release/zmeta-release-manifest.yaml --package-dir release/package-v1.1.27`
and the same validator with `--templates-only`.
Result: ok in both modes, rebuilt after the review's wording fixes to the
notes. With the package directory present, `test_release_package.py` and
`test_release_manifest.py` read 45 passed.

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
Result: 29 passed after the doc-currency pass, including the release-focus
governance sentence check.

Live runtime harnesses (adapter and gateway code changed in this cut):
`python tools/test_gateway_live.py` and
`python tools/test_workflow_end_to_end.py`
Result: both exit 0. The live gateway forwarded the command, the duplicate
acknowledgement and the state event and emitted CoT; the end-to-end
workflow forwarded all four event types and emitted CoT.

Gateway Docker build and run (runtime code changed):
`docker compose -f deploy/gateway/docker-compose.yml up`
Result: pass. The container (python:3.13-slim over the working tree)
started and printed the same four hashes as the host (contract_hash
8dd996f160f3da07969a95d3f5e2ee60f486b4aab1c43a6b347bac17377da8dd). For one
shipped v1.0 STATE_EVENT sent to the published port it forwarded the event
to the host with `profile` stamped, emitted its CoT projection to the host's
CoT port, and beside the event forwarded one warning diagnostic,
`LINEAGE_PARENT_UNRESOLVED` (WARN_ACCEPT, the documented policy, because
the probe's lineage parent was unknown to a fresh gateway). Its metrics line
read recv=1 fwd=2 cot=1 drops=0 violations=0 warnings=2, the second warning
being `EVENT_TS_IMPLAUSIBLE` because the shipped example's `event.ts` of
2025 lies beyond the gateway's one-day plausibility horizon. Both are the
response the documented policy calls for.

CoT egress profile, beyond the battery:
`COT_EVENT_XSD=<copy of MITRE Event-PUBLIC.xsd> python -m pytest -q
adapters/egress/cot/test_cot_cds_profile.py -k PublicSchema`
Result: passed, 4 subtests (the schema is not vendored, so the battery
reports this test as skipped).

Contract hash:
`python tools/compute_contract_hash.py`
Result: contract_hash
`8dd996f160f3da07969a95d3f5e2ee60f486b4aab1c43a6b347bac17377da8dd`, moved
from v1.1.26's `ea6fe42c85d9147957c7859917f2405cf0908ddee28ed38ba7da08d4ddac5d76`
because its semantics input, the semantic contract file, changed (the
section 22 class table row of 2026-10-07 and the 7.6 definition of
2026-10-27); its schema and policy inputs are the locked v1.0 schema and
the reference policy pack, both byte-identical to v1.1.26. The experimental
1.1.0 schema is byte-identical to v1.1.26 as well. The release manifest's
`policy_bundle_hash` moved because the two policy variants under
`configs/policy-variants/` are manifest-listed in that group; no file under
`policy/` changed.

## Verification method statement

This release carries a Class B contract change (the 7.6 `last_seen_ts`
definition as a contract 2.1 patch, and the section 22 class table row),
Class B registry and roadmap records, Class C adapter and gateway changes
(the `cds` stale cap, the standard profile's XML hardening, the `how` shape
check, the position and name guards, the failure-modes honesty fix, the
policy-variant assembly tool) and the records waves of October. Verified
mechanically before the cut:

- **The 7.6 definition went through two review legs at its tip.** An
  independent Opus 5.5 review read the branch cold and ran the reference
  projector itself, a late-arrival case included; a Sonnet 5.5 factual pass
  checked 65 record claims and contradicted none. The lock-baseline anchor
  moved only after its negative control was seen failing (the anchor test
  red with the sentence in and the anchor unmoved, then green). The
  must-pass vector's correction grew the kernel gate's expected red by
  exactly its two lines until this cut's manifest rebuild cleared them.
- **The projection guards carry a red demonstration.** Fourteen tests were
  run first against `develop` d1a503d, where the guards did not exist:
  twelve failed and the two boundary cases passed as the positive control;
  every example STATE_EVENT projected byte for byte the same under both
  profiles; an independent review with a seeded off-by-one in a control
  copy of the adapter found it.
- **The standard CoT profile is frozen by a test**, and its bytes still
  match after the hardening, the `how` shape check and the guards.
- **The `cds` cap and the command posture were reviewed before their
  merges**, the command wave by independent agents and the five unreleased
  waves of 2026-10-01 by a scope check of three independent reviews against
  the North Star, the design gates, the governance, the contract and the
  registry rules, which found none widening the kernel; the policy
  variants are pinned to the file each replaces and run through the
  gateway pipeline with the reference policy as the control.
- **The failure-modes honesty fix pins the shipped configs** to the set
  the gateway reads.
- **The locked surfaces did not move except as recorded.** The v1.0 schema
  is byte-identical to every release since v1.1.17, pinned by its anchor
  guard; the contract anchor moved twice since v1.1.26, each time under the
  maintainer's go with a dated note.
- **The completeness gate was seen failing** for the five missing artifacts
  before the signed set existed.

## Known limits of this validation

The `cds` profile's evidence is n=1, and the stale cap this release adds
(doctrine F3-03, decided on a delegated go) has not been seen by the
partner's guard; a consumer that re-pins confirms the shape with the far
side first.

No validator reads the 7.6 relation between a FUSION_EVENT's
`last_seen_ts` and its members' times; two inline test fixtures still carry
the old relation, and the reference projector stamps a late-arriving
observation's time rather than the latest member's. The relation check,
with its own failing control, is booked in the handoff for the next records
pass, together with `tools/validation_guidance.yaml`'s contract line
citations past the 7.6 insertion point, which the two inserted lines
shifted (its header accepts drift).

The two held gateway fixes (the command dedupe window against contract 13.2
and the unbounded validation state) are not in this release.

The locked v1.0 lane still accepts any string ending in `Z` as `event.ts`,
per doctrine X1-01, unchanged from v1.1.26.

## Signing decision

Signed release. The release authority, Justin Carr (Incept.IO), directed
this signed cut on 2026-10-27 with the Incept.IO ZMeta release signing key
`A3B150AF2A0E1CA413C4B7F112BE81F54654B96E`, continuing the practice resumed
at v1.1.23. Key existence was re-derived at this cut with the gpg binary the
signing tooling resolves from PowerShell (GnuPG 2.5.17, the Gpg4win
install), after a gpg-agent restart; the first secret-key listing after
the restart returned nothing and the second listed the key, and the second
is the one recorded. The Git-bundled gpg on the same machine resolves an empty keyring
and is not used. Detached signatures are generated for
`SHA256SUMS_v1.1.27.txt` and every release asset, and verified after
generation; the completeness gate enforces the tracked signature trio
mechanically.
