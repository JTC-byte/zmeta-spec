# ZMeta v1.1.19 Validation Report

Release date: 2026-07-28
Release target: `v1.1.19`

## Scope

This report covers the ZMeta v1.1.19 release: the 29 commits after the
published `v1.1.18` tag. Three groups.

The prepared cut itself: `export/policy/*.json` as a verbatim JSON projection
of the governed policy, the ADS-B ingress adapter, the field-readiness fixes a
first-run review found, packaging so every hashed artifact ships in every
bundle, and a content-currency guard rebuilt after the first design was
defeated twice.

A documentation voice pass across 40 current-facing files, prose only. No
structure, ordering, facts, claims or code changed. Verified by a structural
invariant check comparing every touched file against its pre-pass state:
headings, tables, code fences, links and inline-code spans identical except for
seven intentional heading rewordings, and zero broken links. Governed and
manifest-hashed files were computed and excluded rather than judged by eye; of
the 43 files changed since the prepare baseline, none is hashed in the manifest.

The records work: cycle X1 in the doctrine review log, and this report plus
`SHA256SUMS_v1.1.19.txt`, whose absence is described below.

The locked v1.0 kernel is unchanged. Governed artifacts changed relative to
`zmeta-v1.1.18`: `conformance/adapter-harness/must-pass.jsonl`. No schema file
or event vocabulary was added.

## Validation executed at the cut (2026-07-28, local)

- Full kernel-protection conformance, all flags: exit 0.
- Strict examples corpus: 51/51 passed, 0 warnings.
- Full pytest suite: **1474 passed + 1070 subtests** (v1.1.18 cut: 1420 + 1070).
- Adapter conformance harness: 51/51.
- `tools/lint_policy_risk_modes.py`: ok.
- `tools/lint_adapter_vocabularies.py`: ok.
- `tools/validate_future_roadmap.py`: ok (candidates=18, rejected_or_deferred=3).
- `tools/export_policy_json.py --check`: ok, 11 files.
- Release manifest validated; release package validated in templates mode.
- GitHub CI green on every pushed commit in this range.

## Cross-platform contract-hash agreement (limit removed this release)

The v1.1.18 report could not close this. It is closed here, without the
hardware pair its checklist item assumed was required. `compute_contract_hash.py`
run on Windows and in CI on ubuntu over the same tree produce byte-identical
values across all four hashes, confirmed by reading the CI job log rather than
by re-deriving locally:

```
schema_hash=729899113cba00455a74720eccb2decfee8f86ea2c95454f33031dc925f2896f
policy_hash=29686cb3adb9b7d124186da4aeda586cf98b381fdb9aa4847a409f50215654b5
semantics_hash=31fe2eb89655c8b4cb4430a45ce701b314f2f117217792ad5f82872babb43cb4
contract_hash=3cafdd2705704b5dc5b1dc9efbb2e4840c40e1ff1f8437cb6f29ddd53c63e795
```

The checklist item had conflated two questions: whether the hash is
platform-stable, which this answers, and whether a deployment pair is
configured consistently, which was never a hash question.

## Verification method statement

The pre-cut review of the prepared range was run by its own author, and the
commit preparing this cut said so rather than claiming independence. Six
independent panels then ran at closeout and found the worst defects in the
range: a headline guard that did not work, a silent-corruption hash bug that
passed every green gate, and a documented two-node path that delivered zero
events. All were long-standing; the hash defect dated to the repository's first
day. The first-run lens, the one an author is least likely to run, found the
worst of them.

A cross-repo exchange with the fielded consumer of this standard then produced
two findings against their deployment and one against this kernel, each
reproduced independently on both sides before being recorded.

Every code change in this range was reproduced before it was fixed and pinned
red-first. Where a claim enumerated something, it was generated rather than
written: the release-focus governance sentence, the dist bundle's tool list.

## This report and its checksums were themselves missing, and nothing caught it

Recorded because the failure is the kind this report exists to surface. `v1.1.19`
was prepared, manifest-validated, package-validated, battery-green and CI-green
while `VALIDATION_REPORT_v1.1.19.md` and `SHA256SUMS_v1.1.19.txt` did not exist.
Every release from `v1.1.0` onward ships all three artifacts; this one shipped
one. The handoff meanwhile asserted that only tag, sign and upload remained,
written by an earlier session and never re-derived.

The completeness rule lived only as manual checkboxes in `RELEASE_CHECKLIST.md`,
so it was a claim about process rather than a check on the tree.
`gateway/tests/test_release_artifact_completeness.py` now generates the required
set and asserts it, for the current release and for every release since the
convention began at `v1.1.0`. It was demonstrated red against the tree that
motivated it, naming both missing files, and it carries a paired non-vacuity
test that removes each required artifact in turn from a synthetic tree.

## Known limits of this validation

- **`event.ts` is not constrained by the kernel** beyond a trailing `Z`
  (doctrine log X1-01, open). `utcDateTime` declares `format: date-time`, which
  is annotation-only under JSON Schema 2020-12, so `pattern: "Z$"` is the whole
  constraint: `garbageZ`, a bare `Z`, `2026-13-01T00:00:00Z` and
  `2025-02-29T00:00:00Z` all validate. The mitigation named in the CoT and JREAP
  adapter READMEs, an installed `FormatChecker`, does not work as shipped:
  `jsonschema` registers no `date-time` checker without the optional
  `rfc3339-validator` package, which this repository does not declare, and an
  unregistered format silently conforms. Egress adapters refuse such events, so
  projections are protected; a consumer that validates and then reads `ts` for
  freshness or ordering is not. Recorded and escalated rather than fixed:
  there is no observed failure, and enforcement would newly reject events that
  validate today, which must ride a release deliberately rather than be added
  to a prepared one.
- Real-hardware Raspberry Pi throughput is not measured. Build, dependency
  resolution, startup and semantics are verified under ARM64 emulation.
- TAK/COP display validation against live tooling has not been performed. The
  `cot.config` pedigree knob is shipped and pinned but exercised only by tests.
- SAPIENT multi-node Apex routing and the C# BSI Flex 335 harness remain
  not-exercised. Single-node Apex v4.2.0 validation was performed at v1.1.15.
- The SITL end-to-end gate preceding live GCS-originated tasking has not been
  run. The command-evidence check is its repository-side prerequisite, not a
  substitute.
- Three alphabet gaps found by the ADS-B adapter (doctrine log A1-01/02/03)
  are open by design, awaiting field evidence rather than argument.
- Open-by-design items are recorded, not hidden: the doctrine review log's open
  tensions, and `docs/zmeta_live_test_checklist.md` for the questions a live
  deployment answers.

## Signing decision

Checksums-only, consistent with v1.1.5 through v1.1.18. No detached signatures
are attached unless the maintainer adds them at publish.
