# ZMeta v1.1.24 Release Notes

## Summary

This release is the health-and-hygiene wave that closes out the PR #8
field-verification cycle and relocks the stack for field feedback. The
locked kernel does not move: the semantic contract, the schemas, policy
data, the extension registry, the conformance corpora and the encoding
projections are byte-identical to v1.1.23. The changes are tooling
diagnostics, one shared adapter-helper fix, standing test guards, and
process records. Every item traces to a defect the field-verification
exchange surfaced, either in the stack or in the apparatus that guards it.

## What changed for tool users

- **The validate CLI reports actionable diagnostics.** `tools/validate.py`
  selects the schema lane from the event's declared `zmeta_version` and
  prints every violation with its location when the defect is below the
  document root. Previously it validated the version-discriminated union
  and printed one top-level message, so a nested enum defect printed as
  the whole event dict followed by "is not valid under any of the given
  schemas" while the gateway reported the branch diagnostic for the same
  event. Events declaring no known lane still validate against the union,
  with a hint naming the supported lanes. Exit codes and accept/reject
  behavior are unchanged; `tools/check_adapter.py` inherits the
  improvement, and `CONTRIBUTING.md` and the mapping-packs README now
  point adapter authors at it.

## What changed for adapter deployments

- **`coerce_timing_quality()` degrades invalid supplied timing tokens.**
  A supplied `time_source` or `sync_state` outside the schema vocabulary
  previously survived translation and failed schema validation far from
  its cause, the failure mode an external field pass demonstrated on the
  ADS-B fixture. After a whitespace-and-case fold, an unknown
  `time_source` now becomes `UNKNOWN`, an unknown `sync_state` becomes
  `UNSYNCED`, each independently, and the error bound widens to at least
  the unsynced default whenever either degrades. Non-string wire values
  degrade instead of crashing. A timing claim whose `est_error_ms` is
  poisoned (wrong type, non-finite, or negative) is never partially
  repaired: it passes through whole so schema validation or an adapter's
  own refusal gate rejects the event, preserving SAPIENT's pinned rule
  that degradation never substitutes a clean value for a poisoned one.
  Deployments supplying valid tokens see no change.

## New standing guards

- The example conformance claims' `release_hashes` are asserted against
  the release manifest beside them, the reader whose absence let stale
  claims ship in every published v1.1.22 bundle (doctrine X2-01, CHANGED).
- The changelog guard derives its worked-on date from the newest dated
  worklog entry heading, and a top resume note that disagrees with it is
  a hard failure whose message teaches the convention, instead of the
  silent skip that failed an external contributor (doctrine X2-03,
  CHANGED).
- The release-completeness gate requires the tracked signature trio for
  the signed regimes (v1.1.2 through v1.1.4, and v1.1.23 onward); a
  checksums-only release after the baseline requires an in-code exemption
  naming the release authority and date (doctrine X2-02 addendum).
- Author-facing prose that names vocabulary tokens beside a checked enum
  slot is verified against the schema enums. On its first run the guard
  caught two further live instances of the exact defect that motivated
  it.
- Both repo-wide markdown scans share one snapshot-tree exclusion list,
  with the stale-worktree reproduction pinned in-repo.

## Process and publish-path hardening

- `.gitattributes` pins the release integrity artifacts against
  line-ending smudge, and the release checklist gains the
  no-branch-switch-after-signing and verify-as-published steps that the
  v1.1.23 upload incident proved necessary.
- An RF zero-fill policy check is booked as a governed proposal (handoff
  item 19, with credit to Barrett Downs, Torch) rather than minted inside
  this wave; the predicate needs adjudication because `power_dbm` 0.0 is
  a physically legitimate value.
- The wave was adversarially verified before this cut. The pass found two
  blocking regressions in the wave's own first draft (an unhashable-value
  crash surface and a NaN bound riding the degrade into a schema-clean
  event); both are fixed and pinned by tests, and the full account is in
  the worklog entry and `VALIDATION_REPORT_v1.1.24.md`.

## Compatibility

No schema, policy, or wire changes. An implementation passing v1.1.22
conformance passes v1.1.24 unchanged. `tools/check_compat.py` accepts
`--target v1.1.24`.

## Signing

Signed release. The release authority, Justin Carr (Incept.IO), directed
this signed cut on 2026-08-13 with the Incept.IO ZMeta release signing key
`A3B150AF2A0E1CA413C4B7F112BE81F54654B96E`, continuing the signing
practice resumed at v1.1.23. Verify the assets against
`SHA256SUMS_v1.1.24.txt` and its detached signature:

```
sha256sum -c SHA256SUMS_v1.1.24.txt
gpg --verify SHA256SUMS_v1.1.24.txt.asc SHA256SUMS_v1.1.24.txt
```

The public key ships in the repository as
`release/ZMETA_RELEASE_SIGNING_KEY_v1.1.2.asc` (same key, v1.1.2 through
v1.1.4 and v1.1.23 onward).
