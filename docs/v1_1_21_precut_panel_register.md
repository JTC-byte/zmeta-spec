# v1.1.21 Pre-Cut Panel Register

Process record. Six lenses ran over the whole v1.1.21 wave (every commit
after `b31c1de`) as one surface: governed coherence, mint runtime
behavior, A1-01 adapter honesty, records accuracy, release surfaces, and
test vacuity. One adversarial verifier per finding, instructed to refute
and defaulting to refuted when evidence did not reproduce. Twenty-nine
agents ran; 23 raw findings resolved to 3 refuted with evidence and 20
confirmed, deduplicating to 12 distinct defects (the handoff item was
found independently by five lenses, which is its own datum on how visible
it was). Every FIXED disposition below landed in the cut-prep commit that
carries this register.

| # | Finding | Severity | Disposition |
|---|---|---|---|
| 1 | Handoff release block half-updated: the wave bumped the machine-pinned "Use tag" literal and left the prose asserting v1.1.20 unpublished and v1.1.19 the release to clone, both false since 2026-08-03 (found by five lenses) | MAJOR | FIXED. Prose corrected; the block's own process note now records this as the second instance of the prose-beside-a-pinned-literal blind spot |
| 2 | POWER_REFERENCE registry entry cited `test_schema_version_discrimination.py` as a fixture with zero `power_reference` coverage in it, the repo's named vacuous-evidence class | MODERATE | FIXED. Three version-discrimination pins added (tokens pass on 1.1.0, undeclared token refused on 1.1.0, v1.0 carries the key as free-form with the boundary stated); the citation is now content-backed |
| 3 | `policy/command-evidence.yaml` header still documented the pre-mint reason codes an operator would configure against | MODERATE | FIXED. Header names the minted codes, their history, and the v1.0 wire fallback |
| 4 | The CHANGELOG claim that `--validate` was "proven to refuse a required-field strip" had no in-repo proof artifact; the proof was a session act (P2-D1 class, found by two lenses) | MODERATE | FIXED. Red and green CLI pins added to `test_encoding_cli_refusals.py`; the claim now cites them |
| 5 | README Integration Notes section still titled and scoped v1.1.20 at the v1.1.21 identity, unpinned by the currency suite | MODERATE | FIXED. v1.1.21 integration notes written |
| 6 | Live-test checklist pre-flight step 1 pinned the v1.1.20 tag and checksum file while the same file's header claims v1.1.21 | MODERATE | FIXED. The step is version-generic via `release/README.md` |
| 7 | POWER_REFERENCE enters `experimental` while the registry's Promotion Evidence Requirements make independence a necessary condition for that standing | MINOR | RECORDED, not smoothed. The A1-01 closure carries the pressure sentence: the clause was written for promotion from reserved or proposed and did not anticipate direct-to-experimental creation; the scope question belongs to the registry's next revision |
| 8 | Doctrine log overclaimed "no fielded v1.0 consumer sees a byte it did not see before"; `diagnostic_code` is a new metrics member | MINOR | FIXED. The claim now separates unchanged `reason_code` values from the one new, schema-legal, ignorable member |
| 9 | CHANGELOG B1 enumeration omitted the eo-cv adapter's labeled-hybrid convention | MINOR | FIXED |
| 10 | Makefile budget gloss derived 237 while naming 236 | MINOR | FIXED. Structural bound and vendor-documented figure are now separate statements |
| 11 | Two wave commit subjects (`665174d`, `a65d593`) use the aphoristic cadence the documentation-voice standard bars for subjects | MINOR | BANKED. The commits are local unpushed history; rewording mid-stack was judged riskier than the defect. Recorded here so the standard's count stays honest; the maintainer may reword before push |
| 12 | `CallSitePolicyCoverage` still accepts `force_schema_violation=True` alone at `build_violation_event` call sites, though `policy=` is now load-bearing for the minted-code wire fallback | MINOR | BANKED. Queued hardening: require `policy=` at build sites reachable by minted codes, so a future call site cannot silently skip the fallback |

The three refuted findings and the full finding-by-finding verifier
reasoning are in the session's workflow record; refutations were accepted
only with evidence reproduced against the tree.
