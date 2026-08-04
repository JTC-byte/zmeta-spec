# ZMeta v1.1.20 Validation Report

Release date: 2026-08-03
Release target: `v1.1.20`

## Scope

This report covers the ZMeta v1.1.20 release: every commit after the
published `v1.1.19` tag, landed as a phased campaign against a ten-axis
readiness audit. The count is deliberately not asserted here; it is
derivable (`git rev-list --count v1.1.19..v1.1.20`), and a frozen
document asserting a number that each correcting commit changes is the
exact moving-fact class this cut's own review panel flagged. Governed waves (the A1-02 declared-dimensionality form,
the ERROR_ELLIPSE_M promotion, the X1-01 timestamp closure, the v1.0 lock
restoration), the SAPIENT boundary fix wave the interop run demanded, a
validation phase, a documentation refresh, and the cut itself, which ran
its own whole-range review before this report was authored.

The locked v1.0 kernel is unchanged. Governed artifacts changed relative
to `zmeta-v1.1.19`: `conformance/adapter-harness/must-pass.jsonl`,
`conformance/bad-events/must-fail.jsonl`,
`conformance/profile-precision/must-fail.jsonl`,
`conformance/profile-precision/must-pass.jsonl`,
`policy/producer-authority.yaml`, `policy/profile-precision.yaml`,
`schema/zmeta-event-1.1.0.schema.json`, `spec/compact-binary-mapping.md`,
`spec/extension-registry.yaml`, `spec/semantics-contract.md`.

## Validation executed at the cut (2026-08-03, local)

- Full kernel-protection conformance, all flags: exit 0.
- Strict examples corpus: 51/51 passed, 0 warnings.
- Full pytest suite at the prepared tree: **1726 passed + 1081 subtests**
  (v1.1.19 cut: 1477 + 1070), with exactly one red,
  `test_release_artifact_completeness`, red by design until this report
  and the checksums exist. The post-artifact re-run and its exit code are
  recorded in the cut commit message, since this report is hashed by the
  checksums and cannot describe what happens after they are written.
- Adapter conformance harness: 53/53.
- Profile precision policy: 41 fixtures ok. Profile projection: 37 ok.
- `tools/export_policy_json.py --check`: ok, 11 files.
- `tools/validate_extension_registry.py`: ok, 62 entries.
- Release manifest validated; release package validated in package mode
  (`--package-dir`) and all checksummed assets verified with
  `sha256sum -c` before any tag, per the ordering rule the v1.1.19 cut
  paid to learn.
- GitHub CI: green on every pushed commit in this range except the
  mid-cut checkpoint push, which failed on exactly the one by-design
  completeness test naming this report's own absence. That red is the
  machine stating the cut was incomplete, which was true when it ran.

## Validation executed during the campaign (phase 3, 2026-08-03)

Four read-only streams ran against the mid-campaign tree, results in the
worklog and session archive:

- **SAPIENT interop:** the full chain (ADS-B ingress, track projection,
  SAPIENT egress, TCP wire framing) was accepted by an independent
  pure-Java BSI Flex 335 v2 harness, including the z-less 2-D
  DetectionReport. This is the first acceptance of a ZMeta projection by
  an implementation not written in this repository. The run found three
  boundary defects, all fixed and pinned in this release.
- **Retask chain:** 24/24 on both fielded workflow shapes (photo
  metadata to command, and multi-LOB fusion to ellipse to command)
  against the fail-closed MAVLink translator.
- **Simulations:** two-node and throughput harnesses re-run on the fixed
  stack; throughput consistent with the ~422 events/s single-gateway
  datum. Replayed historical corpora trip the new ts-plausibility warning
  by design; simulations set the horizon to 0.
- **Containers:** the rewritten deploy README followed verbatim delivered
  events off-host, closing the readiness audit's containers blocker.

## Verification method statement

The pre-cut review of this range was independent of its authors, closing
the gap the v1.1.19 report disclosed about itself. It ran as a
whole-range fresh-eyes panel: eight cold lenses over all commits since
v1.1.19 as one surface, deduplication against the MAJOR/MODERATE fix
floor, and one adversarial verifier per surviving finding, instructed to
refute and defaulting to refuted when evidence did not reproduce.
Nineteen raw findings resolved to eight confirmed, four downgraded but
real, two refuted with evidence, three minors. One refutation re-ran the
full battery in a worktree at the disputed commit and reproduced the
recorded count exactly, vindicating the checkpoint record it challenged.

The fix wave landed red-first, and an adversarial attack pass on the fix
wave itself then found four defects in the fixes, all fixed before
commit, including one instance of the lesson-applied-once class occurring
inside the wave that was fixing other instances of it. The
finding-by-finding record with a standalone verification command per
entry is `docs/v1_1_20_precut_panel_register.md`.

Every code fix in this range was demonstrated red before it was fixed.
Where a claim enumerates, it is generated: the governance sentence, the
checksum errata table, the Profile L size table, the release artifact
completeness set.

## Known limits of this validation

- **The `event.ts` structural pattern lands on the v1.1.0 branch only.**
  The locked v1.0 schema does not gain it, by design; v1.0 consumers rely
  on the gateway's warn-only plausibility window and on egress refusal,
  as before. The v1.1.19 known-limit entry is otherwise closed.
- **The profile-projection field catalog stays v1.0-scoped.** Its rule
  matching has no per-version axis; extending it to the v1.1.0 fields is
  a maintainer-scoped follow-up recorded in the panel register. The
  precision-policy layer enforces the adopted extensions' thinning claims
  today, through the projection validator it delegates to.
- The SAPIENT interop acceptance was performed in phase 3 and is recorded
  as a process record; the Java harness is not part of this repository
  and the cut's own battery does not re-run it.
- Real-hardware Raspberry Pi throughput is not measured. The ~422
  events/s datum is x86, one gateway, Profile H.
- TAK/COP display validation against live tooling has not been performed
  for the new `<geo_dimensionality>` detail element; it is exercised by
  tests and documented, not yet by a fielded TAK client.
- The SITL end-to-end gate preceding live GCS-originated tasking has not
  been run. The retask chain validation above is repository-side.
- Alphabet gaps A1-01 (power reference declaration) and A1-03
  (translation provenance) remain open by design, awaiting field
  evidence. A1-02 is closed by this release.
- Recorded, unresolved: the wave-2 records disagree 1704 versus 1706 on
  one battery count (register, below-floor list); kraken's `bandwidth_hz`
  keeps its documented non-finite carve-out.

## Signing decision

Checksums-only, consistent with v1.1.5 through v1.1.19. The signer now
normalizes line endings before hashing text assets, so this release's
checksums are correct at source; `docs/release_checksum_errata.md` covers
the fifteen earlier tags. No detached signatures are attached unless the
maintainer adds them at publish.
