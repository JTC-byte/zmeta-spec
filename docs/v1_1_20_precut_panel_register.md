# v1.1.20 Pre-Cut Panel Register

Docs/advisory. Non-normative. The finding-by-finding record of the
whole-range fresh-eyes review that gated the v1.1.20 cut, with the fix
applied to each confirmed finding and a standalone verification command per
entry. A session with no other context can re-run every check in this file
from a clean checkout.

**How the review ran (2026-08-03).** Range `v1.1.19..869af74` (45 commits,
106 files, ~10.3k inserted lines) read as one surface at release stakes,
per the audit playbook's cut tier. Eight independent cold-reader lenses
(governed-surface integrity, honesty/laundering, doc-vs-tree, cross-wave
joins, test-mass honesty, downstream-consumer reading, first-run stranger,
records honesty), then dedup/triage against the MAJOR/MODERATE fix floor,
then one adversarial verifier per floor-passing finding, instructed to
refute. 23 agents. Result: 19 raw findings, 14 verified, 8 confirmed, 4
downgraded but real, 2 refuted, 3 minors. The fix wave landed the
MAJOR/MODERATE set red-first; below-floor items are recorded here and
deliberately not fixed.

**To re-verify everything at once:** run the kernel gates and battery,

```
python tools/validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative --precision-policy --release-manifest --release-package --bad-events --adapter-harness
python tools/validate_examples.py --strict --require-all
python -m pytest -q
```

then the per-entry commands below for the specific claims.

## Confirmed and fixed

### TV-02 (MAJOR): adopted extensions claimed projection preservation no conformance corpus tested

The registry adopts ERROR_ELLIPSE_M (`preserve_or_compact`) and
GEO_DIMENSIONALITY (`preserve`) with security notes warning that silent
loss during profile projection would launder 2-D-only data into an
apparent full fix. Pre-fix, nothing enforced those claims:
`policy/profile-precision.yaml` never mentioned the fields,
`tools/validate_precision_policy.py` required `payload.geo.alt_m` on every
STATE_EVENT with no A1-02 branch (a lawful declared-2D state failed the
validator), and no fixture exercised thinning of the new fields. The fix
wave then found a second instance of the same class one call-stack layer
deeper: `tools/validate_projection.py` carries its own independent
unconditional `alt_m` requirement, which `compare_precision` delegates to,
so the first fix alone left a declared-2D state still failing.

**Fix.** `policy/profile-precision.yaml`: `zmeta_versions` extended to
1.1.0; `payload.geo.dimensionality` and `payload.quality.geo_status` added
to `immutable_paths`; new `preserve_or_compact_paths` for
`payload.geo.error_ellipse_m` with precision ceilings at M and L. The
load-bearing A1-02 conditional lives in `tools/validate_projection.py`,
whose required-fields check demands presence in the projected event:
`alt_m` is required unless the event declares `dimensionality: "2D"`, so
stripping the declaration re-imposes the requirement and a projector
cannot escape by removing both. The fix wave first added the same
conditional to `tools/validate_precision_policy.py`; the attack pass
proved that copy inert either way it resolved (its single consumer flags a
path only when present in the source and removed, and a declared-2D source
never carries `alt_m`), so the unconditional listing there was restored
with a comment stating the removal semantics. Nine fixtures pin the
enforcement (six from the fix wave, three landed with the escalation fix):
declared-2D and ellipse-bearing states surviving projection at M and L as
must-pass; stripping the declaration, the token, or the ellipse, the
2D-with-`alt_m` contradiction, and the strip-both-declaration-and-`alt_m`
shape as must-fail. `spec/extension-registry.yaml` `fixture_references`
for both entries now point at fixtures that actually exercise projection
loss.

**Verify.**

```
python tools/validate_precision_policy.py
python tools/validate_projection.py
```

Expect `profile precision policy ok total=41` and `projection conformance
ok total=37`. Red re-proof: revert the STATE_EVENT conditional in
`tools/validate_projection.py` (the one load-bearing copy) and the
`v1-1-0-declared-2d-preserved-*` fixtures fail with a
REQUIRED_FIELD_REMOVED code; delete `payload.geo.dimensionality` from a
projected fixture and PRECISION_POLICY_IMMUTABLE_CHANGED fires.

**Escalation recorded, not fixed:**
`conformance/profile_projection_field_catalog.yaml` stays scoped
`zmeta_versions: ["1.0"]`. Its rule matching has no per-version axis (the
key is documentation, read by no code path), so extending it to v1.1.0
means restructuring its version model: a maintainer-scoped follow-up, not
a cut item. The precision-layer fixtures above exercise the projection
validator through `compare_precision`'s delegation, so both registry
claims are enforced today.

### TV-04 (MAJOR): CoT egress launders declared-2D into the unknown-accuracy sentinel

The A1-02 egress sweep spec named jreap and klv; CoT, a third STATE_EVENT
egress with the identical all-or-nothing geo gate, was never swept. A
declared-2D state and the historical ambiguous absent-altitude case both
rendered `hae="9999999.0"`, indistinguishable to a TAK operator from a
failed altitude sensor.

**Fix.** `adapters/egress/cot/zmeta_to_cot.py`: `_projected_hae()` mirrors
JREAP's `_projected_altitude()` logic under CoT's constraint that
`point@hae` is a required numeric attribute with no null convention. The
wire sentinel stays (byte-compatible for existing consumers); a declared-2D
geo now also emits a structured `<geo_dimensionality value="2D" ...>`
detail element carrying the `geo_status` token when present, never
fabricated. The ambiguous no-token case emits no marker and is
byte-identical to before. The 2-D-with-`alt_m` contradiction refuses at
the adapter boundary, as SAPIENT already did. Documented in the adapter
README's disposition table; five new tests, the distinguishability pin
demonstrated red pre-fix.

**Verify.**

```
python -m pytest adapters/egress/cot/ -q
```

Expect 59 passed. The load-bearing test asserts a declared-2D event's
output differs from an ambiguous absent-alt event's output; pre-fix they
were identical.

### TV-09 (MODERATE): the gateway emitted a diagnostic its own validation refuses

`build_violation_event()` routed PROFILE_MISMATCH on a COMMAND_EVENT into
a TASK_ACK whose reason-code enum does not include PROFILE_MISMATCH; the
outgoing self-check then replaced the gateway's own diagnostic with a
generic SCHEMA_INVALID whose `original_event_id` was the internal
never-transmitted TASK_ACK's UUID. Exactly one record reached the wire,
but with the true reason code lost and correlation to the rejected command
broken. The path had zero test coverage.

**Fix.** `gateway/src/gateway.py`: `build_violation_event` accepts the
loaded policy and derives TASK_ACK legality from
`task_ack_allowed_reason_codes` itself; every non-TASK_ACK-legal reason
code routes to the SYSTEM_EVENT/SCHEMA_VIOLATION shape carrying the true
reason code and the rejected input's real `original_event_id`. The attack
pass then found the class still open at a twelfth call site (the main
loop's outgoing self-check rebuild, which omitted `policy=` and so fell
back to the pre-fix logic byte-for-byte); that site now passes the policy,
and an AST call-site enumeration test pins the class at the source level:
every `build_violation_event()` call in gateway.py must pass `policy=` or
`force_schema_violation=True`. A sweep test separately asserts every
reason code the gateway can stamp produces a diagnostic that passes
`validate_outgoing_event`. The locked v1.0 schema and
`policy/semantics.yaml` are untouched.

**Verify.**

```
python -m pytest gateway/tests/test_violation_event_self_validity.py gateway/tests/test_operator_debuggability.py -q
```

Expect 17 passed. The three original pins and the call-site enumeration
pin each demonstrated red on their pre-fix tree.

### TV-11 (MAJOR): the worklog sized the pre-cut panel at half its real range

The Current Resume Note said "roughly twenty-three commits since v1.1.19";
the range held 44 at writing, 45 at panel time. This is the sizing
statement for the exact review the playbook mandates before tagging.

**Fix.** Dated correction marker in place in
`docs/zmeta_refinement_worklog.md`; the panel was scoped to the measured
range, not the sentence.

**Verify.** `git log --oneline v1.1.19.. | wc -l`, and the marker:
`grep -n "Corrected 2026-08-03, found by the panel" docs/zmeta_refinement_worklog.md`

### TV-05 (MODERATE): the worklog claimed sibling egress suites had coverage they never had

The fix-wave entry said the SAPIENT suites' new real-gateway-validator
coverage mirrors "what mavlink/jreap/cot already had". No cot, jreap,
mavlink, or klv egress test loads the gateway validators; all four
exercise the pure conversion function only.

**Fix.** Dated correction marker in place in
`docs/zmeta_refinement_worklog.md`. The sibling coverage sweep stays on
the non-blocking queue.

**Verify.**
`grep -rn "gateway_validators\|_assert_gateway_valid" adapters/egress/*/test_*.py`
returns hits only under `sapient/`.

### TV-07 (MODERATE): release verification docs never mentioned the checksum errata

`release/README.md`'s verification walkthrough and
`RELEASE_CHECKLIST.md`'s checksum items sent a verifier of any of the 15
affected older tags into an unexplained mismatch.

**Fix.** Both files now point pre-v1.1.20 tag verifiers at
`docs/release_checksum_errata.md` and state that published files were
never rewritten.

**Verify.** `grep -n "errata" release/README.md RELEASE_CHECKLIST.md`

### TV-10 (MODERATE): a first-contact README command failed 100%

`README.md`'s Tools quick-reference ran `validate.py` with `--profile H`
against `examples/zmeta-command-examples.jsonl`, authored entirely at
profile L: total=4 passed=0 failed=5 for every fresh reader.

**Fix.** The command now reads `--profile L`.

**Verify.**

```
python tools/validate.py --file examples/zmeta-command-examples.jsonl --profile L
```

Expect total=4 passed=4.

### TV-14 (originally MODERATE, downgraded MINOR on verification): checkpoint hygiene claim

The checkpoint's "no stray worktrees, branches or containers" is literally
false (`backup-pre-scrub` local branch, `.tmp/review-pr-2` worktree), but
the worktree is disclosed and tracked in three other places and the branch
is an inert month-old local. Recorded here; the checkpoint prose stands as
written per the process-record rule. Both artifacts are maintainer
keep-or-prune calls, listed in the cut checkpoint.

## Downgraded and fixed

### TV-03 (MODERATE): README Integration Notes were the previous release's

The section kept the v1.1.19 heading and body at a v1.1.20 tree, opening
with "No schema, policy data, or event-vocabulary changed in this
release", contradicted twelve lines above. **Fix:** retitled and rewritten
for v1.1.20 from the CHANGELOG: the one breaking change
(producer-authority wildcard removal, with migration guidance), the
MAVLink fail-closed default, the opt-in v1.1.0 geo fields, the warn-only
ts window, the formerly-accepted-now-refused list, the errata pointer. The
displaced v1.1.19 section is archived verbatim under CHANGELOG's [1.1.19]
entry instead of repeating the recorded v1.1.17 loss. **Verify:**
`grep -n "v1.1.20 Integration Notes" README.md` and
`grep -n "archived verbatim from the README" CHANGELOG.md`

### TV-06 (MODERATE): the release focus omitted the only breaking change

**Fix:** the README release-focus bullet names the producer-authority
wildcard removal as the release's one breaking change. The generated
governance sentence is untouched. **Verify:**
`grep -n "one breaking change" README.md`, and
`python -m pytest gateway/tests/test_release_currency.py -q` stays green.

### TV-01 (MINOR, fixed as a floor exception): wrong contract citation in a shipping governed artifact

The v1.1.0 schema's `utcDateTime` `$comment` and `gateway/README.md` cited
contract 5.7 (holdover monotonicity) as the authority for runtime ts
plausibility. The correct authority is 3.1's "Actual time-source
accuracy" in the cannot-enforce list, verified against the contract text
before the swap. Two-line citation fix, zero behavior. **Verify:**
`grep -n "contract 3.1" schema/zmeta-event-1.1.0.schema.json gateway/README.md`

### TV-09 companion note

TV-08 and TV-13 were refuted (below); TV-09's fix above is the only
gateway-code change from the panel.

## Refuted on verification

- **TV-08** claimed the MAVLink fail-closed default is "undocumented,
  unlabeled". The adapter README documents it exhaustively (guards table,
  dedicated section, opt-in example), CHANGELOG describes it, and four
  tests pin it. The README-narration gap it pointed at is real and covered
  by the TV-03/TV-06 fixes.
- **TV-13** claimed the checkpoint's hand-verified battery count (1720)
  was wrong because HEAD reproduces 1717. The verifier re-ran pytest in a
  worktree at the checkpoint commit itself: exactly 1720 passed, zero
  failed, zero skipped. The three-test delta is fully explained by the
  v1.1.20 identity flip (the completeness test moving pass-to-fail by
  design, two changelog-currency tests moving pass-to-skip). The
  checkpoint record is accurate; the finder's method (test-file-only diff)
  could not see outcome changes driven by non-test files.

## Recorded, deliberately not fixed (below the floor)

- **TV-12:** handoff says Wave 2 landed at battery 1704, worklog says
  1706, same wave, same subtest count. Which is wrong is undetermined
  (resolving it needs a worktree pytest at the wave tip); both are frozen
  process records. Noted here so the discrepancy is on the record.
- **MIN-01:** a SAPIENT egress comment attributes the 2D+`alt_m`
  exclusion to "coherence arm 1"; the rule lives in `$defs/geo`'s unnamed
  `allOf`. Comment-only, behavior correct.
- **MIN-02:** `test_disabled_by_default_zero_never_flags_a_stale_event`
  passes `ts_plausibility_horizon_ms=0` explicitly, so the name overclaims
  "by default"; the actual default is pinned by a different test in the
  same file. Test correct, name misleading.
- **MIN-03:** a doctrine-log entry records a maintainer decision dated
  2026-08-02 while its commit is authored 2026-08-01; plausibly an
  out-of-band-communication artifact, uncorroborated by any commit.
- **CHANGELOG rename reference:** the 2026-08-02 entry cites
  `gateway/tests/test_v1_lock_restoration.py`, renamed in-range to
  `test_v1_lock_baseline.py`. Historical entry, superseding entry already
  carries its own correction marker.

## Attack pass on the fix wave

Per the standing rule that every fix round both closes and creates, an
independent adversarial agent attacked the combined fix diff. It found
four defects, all fixed before commit; the first two defeated claims this
register originally made, and the register text above was corrected to
match.

- **MAJOR:** the TV-09 class was closed at the call sites inside
  `process_message()` and open at the main-loop outgoing self-check
  rebuild, which reproduced the pre-fix defect exactly. Fixed
  (`policy=policy` at that site) and pinned by the call-site enumeration
  test. Verify: `python -m pytest gateway/tests/test_violation_event_self_validity.py -q`
  expects 4 passed.
- **MAJOR:** the TV-02 conditional added to
  `tools/validate_precision_policy.py` was dead code (proven by
  revert-probe: fixtures pass with it reverted, fail only when the
  `validate_projection.py` copy is reverted). The inert edit was removed,
  the unconditional listing restored with a comment stating the removal
  semantics, and this register's "either validator" red-proof claim
  corrected.
- **MODERATE:** the TV-04 CoT change made `tools/check_compat.py`'s
  CoT-projection warning false (it claimed a STATE_EVENT without `alt_m`
  "will skip"; the adapter skips only on missing lat/lon and otherwise
  renders the sentinel). The check now warns "will skip" only for missing
  lat/lon and advises the ambiguous no-token case to declare `"2D"` when
  the vertical genuinely does not exist. Verify: run
  `python tools/check_compat.py` on a declared-2D STATE fixture with
  `--target v1.1.20`; no cot_projection warning fires.
- **MINOR:** the TV-01 citation fix covered the two named surfaces and
  missed four sibling instances of the same §5.7 miscite
  (`gateway/src/gateway.py` twice, two test docstrings). All four now cite
  3.1. This is the lesson-written-once-applied-once class occurring inside
  the wave that was fixing other instances of it; recorded for the AAR.
  Verify: `grep -rn "contract 5.7\|Contract 5.7" gateway/ schema/` returns
  nothing.

## Panel blind spots, stated by the lenses themselves

CI status was not checked (no network); the SAPIENT Java-harness
acceptance claim is unverifiable from repo contents and was treated as a
process record; `tools/sim/*` was not traced for honesty properties;
kraken's `bandwidth_hz` keeps its documented non-finite carve-out;
Docker-dependent paths were skipped by the first-run lens; 14 of 16
errata rows were spot-checked at 2. The full coverage notes are in the
session archive.
