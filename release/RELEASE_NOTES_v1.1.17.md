# ZMeta v1.1.17 Release Notes

Release date: 2026-07-27
Release type: full-cycle audit and hardening cut (the R1-11 fresh
full-stack audit, its fix and disposition passes, the fresh-eyes cold
re-read, the health fix wave, and two maintainer-adjudicated governed
waves)

## Summary

ZMeta v1.1.17 is the largest honesty-hardening release since the v1.0
lock, and the first cut produced under the audit-wave cadence
(`docs/zmeta_audit_playbook.md`). Every change in it went through the
same discipline: reproduce first, red-first pins, an adversarial attack
pass on every fix set, and independent verification — the process
records are in the repository (`docs/r1_11_full_stack_audit.md`,
`docs/r1_11_cold_reread_findings.md`, `docs/zmeta_doctrine_review_log.md`).

The locked v1.0 kernel is unchanged. The v1.1.0 experimental schema
takes one approved Class B constraint (below). Three additive
`reason_code` enum entries landed early in the cycle; no other event
vocabulary changed.

## Fielded-safety fixes (also present in v1.1.16 and earlier)

- **SAPIENT ingress latency honesty.** A registration declaring a
  negative `maximum_latency` could *narrow* `est_error_ms` — an
  uncertainty bound tightened by malformed wire input. Strictly-negative
  declarations are now unresolvable (conservative floor + explicit
  diagnostics), and a latency declared under an unusable mode name can
  no longer vanish silently.
- **CoT egress no longer fabricates certainty.** The horizontal ellipse
  `semi_minor` was projected into `point@le` — a vertical-error claim
  the event never made; `le` now carries the unknown convention.
  `geopointsrc`/`altsrc`/`how` pedigrees are emitted only when the
  deployment asserts them — never a hardcoded `"GPS"`/`"m-g"`.
- **The gate-clean timestamp class is closed everywhere it lived.** A
  schema-clean but unparseable or offset-less `ts` (e.g. `"1969-12-31Z"`,
  which satisfies the schema's `Z$` pattern yet parses naive) crashed
  CoT/JREAP egress or was silently reinterpreted as host-local time.
  CoT, JREAP, and both SAPIENT egress modules now refuse per their
  documented contracts.

## Command-path fixes (operator retasking flows)

- MAVLink ingress: the decoded `LINK_STATUS` branch and all nine
  advertised `TASK_ACK` verdicts now emit schema-valid events; carried
  reason codes are preserved, never silently dropped; uninterpretable
  states refuse loudly. The five negative acks — the ones a commander
  most needs — previously always emitted schema-invalid.
- MAVLink mission-intent egress no longer fabricates `priority=MED` on
  commands that carried no priority.
- SAPIENT egress: caller-supplied export prohibitions fail closed at
  every container level; `target_geo` shape errors follow the
  documented `ValueError`/`None` contract; deep or exotic containers
  can no longer crash the altitude tripwire.

## Governed changes (maintainer-adjudicated 2026-07-27)

- **Compact mapping fail-closed clause** (`spec/compact-binary-mapping.md`,
  new normative section): the mapping accepts only the canonical JSON
  value model. All CBOR tags are refused at decode and named (tags
  28/29 value-sharing explicitly — the 11-byte datagram that meant two
  different things on two conforming installs now refuses identically
  on both backends); a declared nesting maximum (64) and a declared
  expansion bound (2^20 nodes, refusal never materializes the
  expansion) are enforced. Every clause claim is pinned to the code by
  the spec-sync suite.
- **`TIME_STATUS.state` enum (Class B, v1.1.0 only)**: the branch now
  constrains `payload.state` (`LOCKED`/`HOLDOVER`/`UNSYNCED`/`UP`/
  `DEGRADED`/`DOWN`) like its siblings, so a self-contradicting timing
  event is visible to the kernel. v1.0 is untouched and pinned
  byte-identical.
- **Governed-vocabulary boundary defined**: governed = the event model
  (schema enums, reason codes, policy vocabulary, wire semantics);
  operator-visible tokens outside it are outer-ring, with mirrors of
  governed enums required to stay subsets — enforced by the new
  advisory `tools/lint_adapter_vocabularies.py`.

## Process and records

- The audit-wave cadence, severity floor, one-third introduction-rate
  cap, and standing disciplines are adopted
  (`docs/zmeta_audit_playbook.md`); the doctrine review log gained its
  first terminal entries and a lifecycle.
- The cold re-read record (`docs/r1_11_cold_reread_findings.md`)
  documents 30 confirmed findings and their dispositions, including
  honest corrections to this cycle's own records.
- Deferred, recorded, and open by design: the register candidates in
  the cold re-read record's appendix (VW-01..13) and the open doctrine
  tensions (15 R1-11 entries plus H1-01..07).

## Compatibility

- v1.0 producers/consumers: no change.
- v1.1.0 `TIME_STATUS` producers: `payload.state`, previously a free
  string, is now enum-constrained (Class B). Producers emitting values
  outside the vocabulary must map or omit.
- Compact-wire peers: tagged, value-shared, over-deep, or
  over-expanding datagrams that previously decoded differently per
  backend now refuse identically with explicit diagnostics.
- Three `reason_code` enum entries added earlier in the cycle are
  additive.

## Verification

Battery at cut: full kernel-protection conformance (all flags) exit 0;
strict examples 51/51; pytest 1284 passed + 1051 subtests; adapter
vocabulary lint clean. Verify assets with `SHA256SUMS_v1.1.17.txt`, the
release manifest, and the release package checksum file.

## Signing

Checksums-only, consistent with v1.1.5 through v1.1.16; no detached
signatures are attached unless the maintainer adds them at publish.
Signing remains the maintainer's external process.
