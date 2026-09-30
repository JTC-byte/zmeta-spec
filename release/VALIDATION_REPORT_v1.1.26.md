# ZMeta v1.1.26 Validation Report

## Scope

What this report covers: the reference implementation, the conformance
corpora, the governed artifacts, and the release packaging for v1.1.26, as
validated on the working tree at the cut.

What it does not cover: any claim about the fielded behavior of downstream
stacks beyond what the adapter README states for the `cds` CoT profile (one
deployment, one partner's guard, one day), and any live exercise of the
command path. Those remain gated on the SITL exercise recorded in
`docs/zmeta_live_test_checklist.md`.

## Validation executed at the cut (2026-09-29, local)

Full test battery:
`python -m pytest -q`
Result: 1961 passed, 3 skipped, 1224 subtests passed. The three skips are the
public CoT event schema test (the schema is not vendored; it passed with
`COT_EVENT_XSD` set, see below) and the changelog guard's two post-release
idle states (worklog activity date equals the release date). The run was
made with every release artifact in place so the
completeness gate's signature requirement was exercised live.

Kernel protection gates:
`python tools/validate_conformance.py --kernel-gate`
Result: exit 0. Projection conformance 37, extension registry 66 entries,
conformance classes 34 with 2 claims, encoding negative 50, profile precision
policy 41, bad-event corpus 36, adapter conformance 53, core
conformance pass=21 fail=42.

Examples:
`python tools/validate_examples.py --strict --require-all`
Result: overall total=51 passed=51 failed=0 warnings=0.

Roadmap:
`python tools/validate_future_roadmap.py`
Result: ok, candidates=20, rejected_or_deferred=3.

Release manifest:
`python tools/validate_release_manifest.py`
Result: ok, groups=20, artifacts=84, rebuilt with `--update-claims` after the doc-currency
pass settled; the claims release-hashes gate passed against the rebuilt
pair.

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
governance sentence check, which for this release reports the governed
delta rather than byte-identity.

Live runtime harnesses (runtime code changed in this cut):
`python tools/test_gateway_live.py` and
`python tools/test_workflow_end_to_end.py`
Result: both exit 0. The live gateway forwarded the command, the duplicate
acknowledgement and the state event and emitted CoT; the end-to-end
workflow forwarded all four event types and emitted CoT.

Gateway Docker build and run (runtime code changed):
`docker compose -f deploy/gateway/docker-compose.yml up`
Result: pass. The container (python:3.13-slim over the working tree) started, printed
the same contract hashes as the host, and for one valid v1.0 STATE_EVENT sent
to the published port forwarded the event to the host with `profile` stamped,
emitted its CoT projection to the host's CoT port, and beside the event
forwarded a `LINEAGE_PARENT_UNRESOLVED` warning diagnostic (WARN_ACCEPT, the
documented policy) because the probe's lineage parent was unknown to a fresh
gateway: the honest response, not a defect.

CoT egress profile, beyond the battery:
`COT_EVENT_XSD=<copy of MITRE Event-PUBLIC.xsd> python -m pytest -q
adapters/egress/cot/test_cot_cds_profile.py -k PublicSchema`
Result: passed (the schema is not vendored, so the battery reports this
test as skipped). A mutation check over fifty-four behavior-changing
mutants of the profile, the validator and the circle wrapper killed every
one; the check is a session script, so its result is recorded here and in
the worklog rather than shipped.

Contract hash:
`python tools/compute_contract_hash.py`
Result: the combined contract hash is unchanged from v1.1.25
(`ea6fe42c85d9147957c7859917f2405cf0908ddee28ed38ba7da08d4ddac5d76`), as expected:
its three inputs, the locked v1.0 schema, the policy bundle and the semantic
contract file, did not move. The experimental 1.1.0 schema is not an input to
it; the release manifest's schema-bundle hash moved with that file. The semantic contract file and the v1.0 schema are
byte-identical to v1.1.25, both pinned by their own guards, and the policy
pack is unchanged.

## Verification method statement

This release carries a Class C adapter and gateway change (the `cds` CoT
profile, the CoT type parse, the gateway identity setting, the gateway's
diagnostics on the 1.1.0 lane) and the integration line's held governed
content (the experimental 1.1.0 acoustic entries, the validation guidance,
the ontology reference). Verified mechanically, before the cut:

- **The cds profile went through two adversarial refutation rounds.** The
  first (fourteen readers) confirmed fourteen findings against the draft
  and the profile was rewritten to the validated deployment's fixed
  template with the honesty markers first. The second (four readers: the
  adapter code, test vacuity, the documents against the code, and the
  gateway run as a process) reproduced thirteen adapter defects, four
  vacuous tests, five test gaps, eleven document errors and one gateway
  fail-open, all closed before the merge. Each round's findings are in
  the worklog entry of 2026-09-29.
- **The standard CoT profile is frozen by a test**, and the second round's
  randomised comparison of twenty thousand events under eight configs
  matched the pre-profile module byte for byte.
- **The gateway's fail-loud on a mistyped `cot` block was demonstrated on
  the running process**, with a control showing the same config reaching
  the socket bind under a valid profile.
- **The lane diagnostics change carries TV-09 pins** on the v1.0 lane, the
  1.1.0 lane and the dispatching schema, each with a red demonstration in
  the tree.
- **The lock defended itself.** The v1.0 schema and the semantic contract
  file are byte-identical to every release since the lock, as their anchor
  guards pin.

## Known limits of this validation

The `cds` profile's evidence is n=1: one deployment, one partner's guard,
one day, with the stale window and the link rule applied together and
neither tested alone. The adapter README states this; doctrine log cycle
F3 records the open tensions, including F3-03 against contract section 14
(`valid_for_ms` does not reach the packet under the profile).

The 1.1.0 acoustic entries ship experimental with the promotion bar stated
as not met.

The locked v1.0 lane still accepts any string ending in `Z` as `event.ts`,
per doctrine X1-01, unchanged from v1.1.25.

## Signing decision

Signed release. The release authority, Justin Carr (Incept.IO), directed
this signed cut on 2026-09-29 with the Incept.IO ZMeta release signing key
`A3B150AF2A0E1CA413C4B7F112BE81F54654B96E`, continuing the practice
resumed at v1.1.23. Key existence was re-derived at this cut with the gpg
binary the signing tooling resolves from PowerShell (Gpg4win), after a
gpg-agent restart; the Git-bundled gpg on the same machine resolves an
empty keyring and is not used. Detached signatures are generated for
`SHA256SUMS_v1.1.26.txt` and every release asset, and verified after
generation; the completeness gate enforces the tracked signature trio
mechanically.
