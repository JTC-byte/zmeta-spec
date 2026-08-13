# ZMeta v1.1.23 Release Notes

## Summary

This release lands the first fully external fix wave in the project's
history, completes the records the previous release left owed, and is the
first signed release since v1.1.4. The locked kernel does not move: the
semantic contract, the schemas, policy data, the extension registry, the
conformance corpora and the encoding projections are byte-identical to
v1.1.22. No adapter changed behavior. The changes are documentation, test
guards, and process records.

## The external contribution

PR #8 (Barrett Downs, Torch) delivered three fixes found during a field
verification pass against published v1.1.22, run on real ISR sensor
material:

- **The SAPIENT adapter README now documents the omission reason the
  adapter emits.** The adapter has emitted `COORDINATE_SYSTEM_UNSPECIFIED`
  since v1.1.22; the README said `UNITS_UNSPECIFIED`, so a consumer
  filtering on the documented tag never matched. The README now matches the
  code.
- **The profile-projection README's Failure Codes list is complete.** It
  presented itself as the exact-string reference for
  `tools/validate_projection.py` while listing 26 of the 28 implemented
  codes. `PROJECTION_POLICY_RISK_LABEL_REMOVED` and
  `PROJECTION_EXTERNAL_PROMOTION_EVIDENCE_REMOVED` are now listed; both
  were already implemented and exercised by the must-fail corpus.
- **The governed-document profile scan excludes stale repository
  snapshots.** A git worktree checked out under `.claude/worktrees/`
  carries its own copy of the repository's documents, which can drift and
  fail the scan for reasons unrelated to the current tree. The path joins
  the existing exclusion list.

Each fix carries a set-equality guard test, so a missing, extra, or
misspelled entry fails the suite rather than waiting for the next reader.
The guards were mutation-tested during review: six probes (wrong value,
deleted value, bogus added value, on each side) were each killed by the
matching test.

A fourth proposal, registering the metrics-only `EVENT_TS_IMPLAUSIBLE`
diagnostic in the severity registry, was held by maintainer review and
withdrawn by the contributor: the code's absence from the registry is a
recorded design decision, and registering it under `severity: warn` would
have given one registry code a different meaning than the other sixty. The
need it identified is real and is queued for an in-house solution on a
non-governed surface. The doctrine pressure log (cycle X2) records the
full disposition. The contribution-intake outcome is the designed one: the
fixes merged unchanged, the dialect-risk proposal was harvested for its
need rather than merged, and the contributor's review response tightened
the record further.

## Records completed

The 2026-08-12 errata wave reached main and develop without its own
changelog entry or worklog note, and the changelog guard stayed silent
because its sentinel skip condition was still satisfied. The second review
of PR #8 caught the interaction with a merge probe: merging the
contributor's honest sentinel bump would have turned the guard green over
a record missing two days of maintainer work. The record is now complete,
the instance is booked on doctrine log X2-03 (second occurrence, first on
the maintainer side), and the guard-mechanism fix remains queued.

This release also carries the v1.1.22 example-claims correction at source:
`conformance/claims/example-*.yaml` were refreshed by the same manifest
build that produced the release identity, under the checklist step the
errata wave added. The published v1.1.22 assets remain as shipped; their
erratum is recorded on the v1.1.22 release page and in
`docs/release_claims_errata.md`.

## Signing resumed

Sixteen releases, v1.1.5 through v1.1.22, shipped checksums-only while
citing a signing decision that was never made (doctrine pressure log
X2-02). This release closes that chain. The release authority, Justin
Carr (Incept.IO), decided on 2026-08-12 to resume signing with the
original Incept.IO ZMeta release signing key, chosen for verifier
continuity with signed v1.1.2 through v1.1.4:

- Key: `A3B150AF2A0E1CA413C4B7F112BE81F54654B96E` (ed25519, created
  2026-04-28, expires 2028-04-27). The public half ships with this release
  and matches the `ZMETA_RELEASE_SIGNING_KEY_*.asc` files tracked in
  `release/` since v1.1.2.
- Key existence was re-derived at this cut with the gpg binary the signing
  tooling resolves, which lists exactly this one secret key.
- Detached signatures accompany `SHA256SUMS_v1.1.23.txt` and every release
  asset.

## Verification

Full battery, kernel gate, and examples run at the cut; exact tallies and
method are in `VALIDATION_REPORT_v1.1.23.md`. The claims that carry this
release's weight were verified mechanically rather than asserted: the
byte-identical kernel claim is pinned by the regenerated governed baseline
and the release-focus currency test, the force-push residue check found
zero occurrences of the withdrawn registration across the merged range,
and the changelog guard was probed on the merged tree in both its passing
and its honestly-corrected failing configuration before the record was
completed.

## Integration notes

- No behavior changes for producers or consumers. No schema, policy, or
  wire changes. An implementation passing v1.1.22 conformance passes
  v1.1.23 unchanged.
- A consumer filtering SAPIENT omission reasons on the old undocumented
  `UNITS_UNSPECIFIED` README spelling never matched and should filter on
  `COORDINATE_SYSTEM_UNSPECIFIED`, which the adapter has emitted since
  v1.1.22 and the README now documents.
- Consumers enumerating projection failure codes from the projection
  README gain the two codes it omitted.

## Checksums and signatures

`SHA256SUMS_v1.1.23.txt` accompanies this release, with detached PGP
signatures for the checksum file and every asset, made with the Incept.IO
ZMeta release signing key named above. Verify the checksums, then verify
the signature against the shipped public key.
