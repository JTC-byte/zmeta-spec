# Changelog

## [Unreleased]

- 2026-07-27 (post-cut) — `dd5def7`: post-cut sweep of the edits made
  during interruption-affected stretches; two cosmetic defects closed (a
  stranded parenthesis in this file's v1.1.18 entry, a stray lint
  directive in `gateway/src/validators.py`), manifest and claims
  regenerated. The published v1.1.18 assets carry the pre-sweep bytes;
  the fix rolls forward from main per the released-assets rule.
- 2026-07-27 (closeout) — records closeout: after-action entry for the
  cycle, doctrine-log archival sweep (eight terminal entries) and three
  recurrence-threshold decisions put to the maintainer, playbook rule
  scoring, handoff restructure and retention pass, and the
  finding-record dispositions.
- 2026-07-27 (post-closeout) — README front matter and structure
  (`a8fcc7b`, `4cb3f3c`). It now leads with the value proposition — the
  adapt-once thesis, the "ZMeta at a glance" graphic, five reasons to care,
  the semantic-pipeline diagram, and the encoding-size chart — with a direct
  pointer to `docs/zmeta_professional_overview.md` for evaluators. All three
  visuals already existed in `docs/img/` and were reachable only from deep
  inside that overview; none was newly drawn or duplicated. Reordered to
  pitch → field evidence → what it is/isn't → design goals → the ten-minute
  proof → role routing → reference, and the two duplicate quickstart blocks
  merged into one. Six historical per-release Integration Notes sections
  (v1.1.11–v1.1.16) moved verbatim into this file under **Historical
  Integration Notes** — they were 39% of the README and sat between the pitch
  and every piece of reference material. Net 598 → 395 lines with nothing
  lost. Also documents the one-time Windows fix
  (`git config --global core.longpaths true`): a clone into an already-deep
  directory can fail checkout on the 260-character path limit, which reads as
  a broken repository rather than a local setting. Verified alongside it that
  a fresh clone of `main` runs clean for a new user (1420 tests, gate exit 0,
  manifest validates, examples 51/51) — so no clone-a-tag instruction is
  needed for ordinary use; the tag matters only for byte-exact verification
  against published assets.

## [1.1.18] - 2026-07-27

> The event-readiness cut: everything published in v1.1.17 plus the
> post-release hardening, the bladeRF reference adapter, the deployment
> verification and quickstart, the UxS command-loop pair, and the
> pre-cut review's 13 closed findings. Checksums-only, consistent with
> v1.1.5 onward.


- 2026-07-27 (post-v1.1.17) — two CI hotfixes on the release commit, both
  platform-dependent and invisible to a local run whose `cbor2` resolves
  pure-Python: `8175aa7` makes the compact encode path enforce the declared
  nesting maximum **before any backend encoder runs** (a C-extension backend
  recurses on sender-controlled depth and aborted the process where the
  pure-Python backends raise catchably — shipped gateway/edge bundles were
  unaffected, since they bundle and prefer `zmeta_cbor`), and `1fb6fa3` makes
  the v1.0 byte-identity pin EOL-agnostic (it hashed raw checkout bytes, which
  differ under autocrlf, so it held on exactly one platform).
- 2026-07-27 — deployment verification and the CoT pedigree knob (`bbc40e2`):
  the stock compose files were built and run on x86-64 and on ARM64 under
  emulation — dependencies resolve, the gateway processes the example corpus
  with zero violations, and the schema/policy/semantics/contract hashes are
  byte-identical across architectures. The gateway config's `cot.config` block
  now passes deployment-asserted projection knobs (`geopointsrc`/`altsrc`/
  `how`, team names, error defaults) through to the CoT projection; previously
  the serve loop called it bare, so **no deployment could ever assert a
  position pedigree** and the `<precisionlocation>` ellipse detail was
  unreachable. Unasserted still means omitted. Adds
  `docs/zmeta_two_node_quickstart.md` (sensor edge to COP in two stock
  containers, with the honesty-signal field-debugging cheat-sheet).
- 2026-07-27 (pre-cut) — a fresh-eyes review of the whole post-v1.1.17 range
  found 13 verified findings, all closed before the cut; three had survived
  their own per-wave adversarial attacks. Closed here: a re-sent copy of an
  already-seen event could **erase a recorded command prohibition** (recorded
  evidence labels are now sticky — unioned, never downgraded — and an
  unreadable risk shape blocks citation rather than reading as unlabeled); the
  command-evidence policy block had no key-name or value-type lint, so a
  one-character typo reverted a knob to its permissive default with every lint
  green; the bladeRF non-finite screen missed the bearing-demotion and metadata
  arms; the two-node quickstart documented a wire path that could not work
  (the edge forwards to 5556 while the GCS gateway listens on 5555); CoT
  team-name config values could crash the projection; and three records claims
  were corrected.
- 2026-07-27 (post-v1.1.17, later) — bladeRF reference ingress adapter
  (`adapters/ingress/bladerf/`, commit `71f8e18` plus this registration
  follow-up): the merged `edge-comms-bladerf` mapping pack now has its
  runnable reference implementation, authored along the documented
  `adapters/AUTHORING.md` path as the repo's timed receipt that the
  guide takes a new RF sensor from recorded output to a verified
  adapter in one sitting (**~13 min zero-shot authoring by external
  wall-clock, ~25 min for the full verified cycle**; the ~40 min figure
  some records first carried was the authoring agent's own effort
  estimate, superseded by the measured receipt; independent adversarial
  attack — verdict CLEAN, one value-honesty finding — hardened and
  pinned same-sitting), and pinned to the pack's two
  real-capture fixture pairs (colocated tests reproduce both
  `expected.json` outputs exactly, modulo the runtime-minted UUIDv7).
  Honesty decisions carried as the pack governs: the frame-unlabeled
  heading-derived bearing is demoted to `features.native_bearing_*` in
  BOTH cases (contract 6.4 mirror case — no minted `TRUE_NORTH`), null /
  null-island sensor positions refuse canonical geo with
  `geo_status: UNAVAILABLE` (contract 6.8), the `spectrum_fft`
  bin-width `bandwidth_hz` declared sentinel is documented in the
  adapter README, no `quality.measurement_error` is minted from the raw
  error bound, degraded timing stays visible, lineage is omit-or-stamp.
  Fail-closed beyond the happy path: `timestamp_ms` is the only
  `event.ts` authority (the paired `timestamp` rendering never rescues a
  missing mapped source), unparseable/boolean timestamps, missing
  required RF features, and a missing/null `platform_id` all refuse
  rather than crash or coerce, non-dict `metadata` degrades honestly,
  caller lineage ids and supplied timing pass through uncoerced. Eight
  `bladerf-` harness fixtures (two emission pins incl. product
  separation both directions, one caller-lineage transform pin, five
  refusals — one per schema-required input). Non-finite values are
  screened at the boundary per the attack finding (NaN/inf SNR refuses
  the event; a non-finite coordinate refuses geo), red-first pinned.
  This follow-up completes the Class C upstream set the commit
  deferred: `adapters/README.md` table row (+ Reference legend widened
  to real-capture corpora), pack README cross-link, manifest/claims
  regenerated under the current identity (the documented next-cut
  re-baseline pattern), and these records. Battery at completion:
  kernel gate all flags exit 0, examples 51/51, adapter harness 48/48,
  pytest 1377 + 1060 subtests, `check_compat --target v1.1.17`
  0 failures (2 deliberate degraded-timing warnings).
- 2026-07-27 (post-v1.1.17, latest) — the UxS command-loop pair
  (maintainer-directed; the GCS-tasking prerequisite from the 2026-07-17
  fielding roadmap). NEW `policy/command-evidence.yaml` + gateway
  enforcement: a COMMAND_EVENT citing motivating INFERENCE/FUSION/STATE
  parents via existing `lineage.based_on` is checked against what the
  gateway saw upstream — unknown/evicted parent → LINEAGE_PARENT_UNRESOLVED
  (tunable), non-motivating parent type → LINEAGE_PARENT_TYPE_INVALID,
  and a parent whose recorded `risk_adjudication` prohibits
  COMMAND_BASIS/AUTONOMY_TASKING → LINEAGE_MISMATCH naming the parent,
  the blocking uses, and the upstream reason codes: a quarantined or
  degraded track can no longer silently become the basis of a retasking
  order, and automation commands are auditable back to their evidence.
  Zero minted vocabulary; bounded evidence index (4096, eviction =
  unresolved, flood tradeoff documented in the policy file); bare
  operator commands stay legal by default with a strict
  `require_evidence` knob for gated automations; policy risk-mode and
  document-structure lints cover the new block; refusals ride the
  documented schema-valid SCHEMA_VIOLATION shape (a pre-existing
  strict-mode escalation hole got the same guard in passing).
  `docs/zmeta_track_lifecycle_pattern.md` (advisory) expresses track
  new/active/stale/lost/merged/split/retired and the load-bearing
  "command-grade track" criteria entirely in current vocabulary — NO
  lifecycle vocabulary minted (the roadmap candidate stays reserved; its
  evidence fields now record the 2026-07-17 deployment as tripwire leg
  n=1 with the second leg awaited) — plus the fielding-gate ladder:
  display now; GCS tasking behind the evidence check + a SITL
  end-to-end pass; P2P retasking additionally behind authenticated
  transport and lifecycle promotion. Doctrine H1-08 banked (wanted
  evidence codes ride lineage codes pending the R1-11-01/-10 pattern).
  Battery: pytest 1410 + 1070 subtests, kernel gate all flags exit 0.
- 2026-07-27 (post-v1.1.17) — kernel-adjacent residuals closed, each
  red-first pinned and adversarially attacked: the validators'
  naive-timestamp arm (gate-clean naive shapes now refuse at the parse
  seam; an unorderable TIME_STATUS is never recorded, so its source
  keeps the loud MISSING disposition instead of a silent clean pass —
  closing a pre-existing fail-open the attack pass surfaced), and the
  plain-`cbor` envelope ingress (the same fail-closed value-model scan
  as the compact envelope, on both backends, with a probed pre-decode
  depth bound — doctrine H1-07 → CHANGED). Two legacy pins updated to
  the 2026-07-27 clause semantics; residual siblings banked as
  VW-14/VW-15.

## [1.1.17] - 2026-07-27

> **PUBLISHED 2026-07-27** with explicit maintainer direction after review:
> annotated tag `v1.1.17` on release commit `7302073`, main pushed, GitHub
> release with all eight assets, checksums-only. *(This blockquote was
> written at cut time and said "HELD for maintainer review"; the dated
> correction is kept rather than the sentence rewritten.)* This release carries the entire held
> R1-11 cycle and its resume work: the pre-audit waves (bullet list at
> the end of this section), the fresh full-stack audit and six-blocker
> fix pass, the disposition pass, the 2026-07-26 cold re-read, the
> 2026-07-27 health fix wave, and the 2026-07-27 governed waves. The
> in-repo manifest divergence (A-12) is resolved by this cut's new
> identity; published `SHA256SUMS_v1.1.16.txt` is unchanged. Signing:
> checksums-only unless the maintainer attaches signatures at publish.

- 2026-07-27 — Governed waves per the maintainer adjudication (`40be64a`,
  `2a00ef2`, `7027a55`): `spec/compact-binary-mapping.md` gains the
  normative fail-closed value-model clause — no CBOR tags (28/29 named;
  the 11-byte two-meanings exhibit now refuses identically on both
  backends), a declared nesting maximum (64), and a declared expansion
  bound (2^20 nodes, refusal never materializes the expansion) — with
  spec-sync pins for every claim (doctrine R1-11-02/03/18 → CHANGED).
  `schema/zmeta-event-1.1.0.schema.json` TIME_STATUS branch now
  enum-constrains `payload.state` (LOCKED/HOLDOVER/UNSYNCED/UP/DEGRADED/
  DOWN) like its siblings — the B-04 self-contradiction is schema-visible;
  v1.0 untouched and pinned byte-identical; new bad-event fixture (corpus
  30); vocabulary lint covers the mirror (doctrine R1-11-15 → MINTED).
  Manifest/claims regenerated (v1.1.16 identity, explicit provenance).
- 2026-07-27 — R1-11 health fix wave (`25bb5fa`, `ede9bb6`, `dcabcc8`):
  fielded-safety and command-path fixes from the cold re-read record, every
  fix red-first pinned and adversarially attacked. SAPIENT ingress: a
  negative declared latency can no longer narrow `est_error_ms`, and a
  latency declared under an unusable mode_name never silently drops. CoT
  egress no longer fabricates vertical certainty (`semi_minor`→`le`), GPS
  source pedigrees, or a hardcoded `how="m-g"` — all config-asserted or
  omitted. The gate-clean-timestamp crash/localization class is closed
  across CoT, JREAP, and both SAPIENT egress twins (unparseable AND naive
  shapes refuse; nothing localizes silently). MAVLink ingress: LINK_STATUS
  and all nine TASK_ACK verdicts emit schema-valid, carried reason codes
  are never silently dropped, uninterpretable states refuse. MAVLink
  mission intent no longer fabricates `priority=MED`. SAPIENT egress
  export prohibitions fail closed one container down; `target_geo` shape
  errors follow the documented contract. The trigger-polarity pin's third
  arm is no longer vacuous; the release-signing pin runs meaningfully in
  tagless CI and no longer leaks residue on Windows. New advisory
  `tools/lint_adapter_vocabularies.py` holds adapter vocabulary mirrors to
  the governed schema enums. `_cot_skip_reason` names value-honesty
  refusals `NON_FINITE_VALUE`, scoped to exclude tolerated extensions
  (outer-ring token per the 2026-07-27 vocabulary-boundary adjudication).
  Doctrine log: six entries adjudicated with the maintainer (09/16
  CHANGED; 02/03/15/18 DECIDED), six new H1 tensions banked. Battery:
  pytest 1262 + 1021 subtests, kernel gate all flags, examples 51/51.
- 2026-07-26 — R1-11 resume P1, records only (`7eaea97`, `e524c8c`): the
  doctrine-log disposition addendum renumbered 15–21, closing a
  duplicate-ID collision at R1-11-14 (the log holds 21 entries; every
  prior count of 20 was a miscount caused by the collision); the
  fresh-eyes cold re-read of the held range recorded **30 confirmed
  findings** in `docs/r1_11_cold_reread_findings.md` — two code MAJORs
  also present in published v1.1.16 (SAPIENT negative-latency narrowing,
  CoT `semi_minor`→`point@le` vertical-certainty fabrication), one
  records-integrity MAJOR (the round-3 findings were never persisted),
  and 27 further — recorded, not fixed; the handoff resume surface was
  corrected (live-measure directive replacing a twice-stale frozen count,
  honestly-scoped governed-change claim, CR-03 caveat on the P4 queue
  item).

- R1-11 full stack audit (findings record
  `docs/r1_11_full_stack_audit.md`: 1 MAJOR, 11 MODERATE, 4 MINOR,
  3 DOC, 6 second-glance items; every substantive finding adversarially
  verified, zero refuted) and its maintainer-directed fix pass, executed
  in seven waves:
  - Compact encoding fails closed (R11-01 MAJOR): `zmeta_compact.dumps`
    refuses any event it cannot round-trip without changing meaning
    (previously it silently relabeled v1.1.0 events as locked-v1.0 and
    destroyed `geo.error_ellipse_m` — a live-witnessed laundering bypass
    of the default gateway schema gate); the gateway replaces an
    unrepresentable outgoing event with an in-band `ENCODING_UNSUPPORTED`
    diagnostic; the compact spec gains the fail-closed Scope section.
    The equivalence is value-identity, not byte-identity: the mapping
    declares exactly two representation normalizations (UUID hex case,
    since UUIDs travel as 16 raw bytes and RFC 4122 is case-insensitive;
    and timestamp formatting at the declared millisecond resolution).
    Refusing those is itself a failure mode — see the verification passes
    below, where a byte-wise check was found rejecting this repo's own
    real-capture fixtures.
  - SAPIENT adapter honesty (R11-02/-03/-04/-12/-20): state egress fails
    closed on unknown/local `policy_decision` labels (filter_risk
    parity) and keeps use restrictions visible on accepted records;
    TaskAck refuses null correlations instead of fabricating "None";
    **in this adapter family** non-finite numbers refuse at every
    canonical guard and are dropped from its native pass-through blocks
    (scoped deliberately — the sentence is true of the SAPIENT ingress and
    egress paths this bullet covers, and was read repo-wide as a stack-wide
    guarantee it never made; the kernel-wide non-finite gate is a separate,
    later item — see `docs/zmeta_doctrine_review_log.md` R1-11-13); fusion
    promotion allowlists caller keys; egress projections honor their
    documented None-refusal.
  - signalhunter GPS no-lock (R11-06): a (0, 0) header never seeds the
    gradient tracker (previously produced a null-island geodesic
    asserted TRUE_NORTH passing strict-H clean); fabricated dead
    `alt_m: 0.0` removed from GPS-fill frames.
  - Promotion verdict honesty (R11-07): the self-asserted `loop_status`
    default is removed from the cot/jreap/mavlink templates — the
    reflection verdict must arrive message-carried (contract 4.5.1).
  - Checking machinery (R11-05/-08/-09): the harness lints its own
    corpus (typo'd expectation keys fail instead of no-op), events-kind
    fixtures require a count pin, and the sapient-ingress promotion
    policy block gains bad-events, pytest, and structural-lint negative
    coverage; published-checksum immutability gains a pytest pin.
  - Governed diagnostic vocabulary (Class B, both schema `reason_code`
    enums + policy): `ENCODING_UNSUPPORTED` (fail),
    `BEARING_FRAME_UNLABELED` (warn — the recorded R1-11 candidate:
    canonical bearings without frame provenance are now
    machine-visible), `NON_FINITE_CONFIDENCE` (fail).
  - Release machinery honesty (R11-10/-14/-16): formal manifests no
    longer self-describe as non-formal and must carry a real branch
    (validator-enforced); the stale hardcoded "D-003 OPEN" register
    claim is retired everywhere it was produced INCLUDING the package
    validator that machine-enforced it; release-hash-policy states the
    achievable commit-provenance rule; AGENTS.md records the
    post-release manifest-divergence rule.
  - Doc currency + teaching (R11-11/-15/-17/-18/-19/-23/-25): stale
    version claims fixed and machine-pinned (overview body, handoff,
    worked commands); AUTHORING.md teaches the sapient/bladerf pack
    patterns; contract 5.3 states the `last_sync_ts`/`sync_state`
    honest-reading rule; the two teaching examples with unlabeled
    bearings now model both frame-provenance channels.
  - Corpora and enforcement growth: bad-events 27 -> 29, adapter
    harness 39 -> 40 (all fixtures now schema-linted in the gate),
    pytest 687 -> 742 (+237 subtests).
- R1-11 post-fix verification, pass 1 (`d955cd0`) — the fix pass is
  itself an audit surface (the R1-10 lesson), and this one found three
  defects the wave-1 fix had introduced or caused:
  - (MAJOR, crash) The wave-1 recovery path guarded only the first
    encode; the re-encode of the `ENCODING_UNSUPPORTED` diagnostic was
    unguarded, and because the diagnostic copies the original's
    `event_id` into `original_event_id`, an event whose `event_id` was
    the unrepresentable part poisoned its own diagnostic. `main()`
    caught only `KeyboardInterrupt`, so one packet could terminate a
    compact-output gateway for every producer behind it. Replaced with
    a fallback ladder ending at the documented `UNKNOWN` correlation
    sentinel, then a recorded drop.
  - (MODERATE, laundering) `verify_representable` compared an in-memory
    key remap, which preserves object identity; Python container
    equality short-circuits on identity, so NaN — not equal to itself —
    passed verification and reached the wire with no canonical JSON
    form (RFC 8259). Verification now runs through the real
    serialization boundary, and non-finite floats refuse by name.
  - (MODERATE, over-refusal) The byte-wise comparison rejected
    schema-valid events: the `uuid` pattern admits uppercase hex and
    `utcDateTime` admits fractional seconds, so both
    `edge-comms-bladeRF` real-capture fixtures — this repo's own
    v1.1.16 corpus — were refused by compact egress over pure
    formatting. The comparison now recognizes exactly the two
    normalizations the mapping declares and nothing more; genuine loss
    (truncated sub-millisecond instants, non-finite floats, dropped
    fields, version relabeling, bool-vs-numeric) stays refused and
    pinned.
- R1-11 post-fix verification, pass 2 — a full seven-slice audit over
  the fixed stack plus a second sweep over the resulting fixes, every
  finding adversarially verified. 14 findings closed: 2 MAJOR (a
  process-killing crash class and a cross-backend laundering/interop
  hole), 7 MODERATE, 5 MINOR:
  - (MAJOR, crash) The recovery ladder handled only
    `CompactUnrepresentableError`, but the codec itself could raise
    `OverflowError` (an integer >= 2**64), `ValueError` (extension
    nesting past the CBOR decode depth a conforming consumer could
    read), or `OSError`/`RecursionError` on schema-valid input — each
    escaping the ladder and terminating the process. The codec now
    surfaces its own serialization failures as
    `CompactUnrepresentableError`, so they become honest
    `ENCODING_UNSUPPORTED` diagnostics; and the gateway receive loop
    gained a last-resort per-datagram backstop that records a drop and
    keeps serving. The backstop is deliberately scoped: `recvfrom`
    stays outside it, so a dead listener still terminates rather than
    hot-looping, and `except Exception` never catches the `SystemExit`
    that reports an unusable configuration.
  - (MODERATE, crash) `_find_forbidden_key` recursed, tying the process
    stack to sender-controlled nesting depth: a deeply nested but
    schema-valid payload killed the gateway at ingress, before egress,
    on any encoding. The denylist walk is now an iterative
    breadth-first traversal.
  - (MODERATE, laundering) The R11-04 non-finite drop ran on only one
    of five SAPIENT ingress paths, so NaN still rode a verbatim vendor
    block onto a non-RFC-8259 wire from status, alert, task_ack, and
    error. Applied on every path — and a structural pin written to stop
    the guard drifting then showed that "five paths" was undercounted:
    there are six vendor-block sinks. The PLATFORM_STATUS event passes
    the raw SAPIENT `power` block through verbatim, so a non-finite
    field inside it reached the wire even though the `battery_pct`
    derived from the same block was guarded. All six now apply the
    guard at the point of use rather than once earlier in the function,
    an invariant the pin enforces. Fixing this surfaced a second hole in
    the same helper: dropping a bare non-finite *list element* silently
    re-indexed positional numeric arrays, so `[1.0, NaN, 3.0]` would
    arrive as a clean two-element array that no consumer could
    distinguish from a genuine one. A non-finite element now drops the
    containing key instead — an absent key is honestly absent, a
    silently shortened array is not. Lists of objects are unaffected.
  - (MODERATE, enforcement) The R11-05 structural lint covered only
    per-producer promotion rules, not the global
    `external_state_promotion` block where most enforcement keys
    actually live — a typo there silently reverted that gate to its
    `.get()` default while both lints stayed green. The lint now covers
    the global block and its `degrade`/`quarantine`/`use_limits`
    sub-blocks, and additionally flags per-producer overrides of
    global-only keys as the silent no-ops they are (an operator writing
    `always_reject_loop_risk: false` on a producer was changing
    nothing). Stress-testing the new lint then caught it committing the
    same sin — it skipped present-but-mistyped `degrade`/`quarantine`/
    `use_limits` sub-blocks, which are read with `.get()` and silently
    revert to built-in defaults; those now fail the lint, while absence
    stays legal.
  - (MINOR, over-refusal) Compact epoch-ms conversion routed through
    float seconds, so `int(dt.timestamp() * 1000)` landed one
    millisecond off for a date-banded fraction of schema-valid
    timestamps and the round-trip check refused them; out-of-range
    instants raised `OSError` on Windows instead of refusing. Now exact
    `timedelta` integer arithmetic.
  - (MINOR, honesty) A non-string `ts` raised `AttributeError` past the
    documented `None`-refusal contract in both SAPIENT egress
    adapters; and the compact-egress drop reason was the only
    lowercase entry in an otherwise `SCREAMING_SNAKE` `drop_reasons`
    vocabulary, hiding that bucket from an operator's filter. Both
    fixed and pinned.
  - (MINOR, checking machinery) The overview currency guard matched one
    literal phrasing (`currently vX.Y.Z`), so equally stale rewordings
    passed clean — a guard shaped around the sentence the last
    regression happened to use. Replaced with a phrasing-independent
    rule: the overview body may name the current release and the
    semantic branches, never a superseded published release. The first
    cut of the replacement was itself wrong (its lookahead rejected any
    version ending a sentence — the very shape it targeted), so the
    matcher now carries a both-directions self-test.
  - Release machinery: `release/RELEASE_NOTES_TEMPLATE.md` still
    shipped the retired "D-003 remains roadmap-planned" line into
    every packaged release note, four releases after the maintainers
    closed D-003. R11-14 had fixed the validator that machine-enforced
    the claim but not the template that emitted it; the section now
    instructs authors to read the register instead of carrying a
    previous release's list forward.
  - (MAJOR, laundering/interop) Compact representability depended on
    which CBOR library happened to be installed. The mapping's integer
    limit was left to the backend, and the backends disagree:
    `zmeta_cbor` refuses an integer outside `[-(2**64), 2**64-1]`
    (correct — CBOR major types 0/1 cannot carry it and this mapping
    defines no bignum tag), while `cbor2` silently encodes it as a
    bignum tag that a `zmeta_cbor` consumer then decodes as raw BYTES.
    Two conforming nodes would disagree about what the same event means
    based on a local install detail. The round-trip self-check could not
    catch it because it is backend-symmetric — the same library encodes
    and decodes, so the corruption appears only on the receiving node.
    The codec now enforces the range itself, identically on every
    backend, with the boundary pinned exactly and both regression tests
    run against both backends.
  - (MODERATE, honesty) `_same_instant` compared two values already
    truncated identically at microseconds, so it could not see loss
    below that: a 100-nanosecond instant compared equal to its
    millisecond round-trip while the codec claimed to refuse truncation.
    The original's resolution is now checked directly.
  - (MINOR, crash) `_format_ts` is reached from the public decode path
    on a sender-controlled epoch-ms value, outside the encode-side
    guard, so a hostile wire value crashed the consumer with a raw
    `OverflowError`. Decode now fails closed.
  - (MODERATE, checking machinery) Four docs carry the identical
    machine-pinned "Current release context" header but only the
    overview was guarded, so the other three sat five releases stale.
    All four are pinned now, plus a test asserting the pinned list still
    names every doc carrying the header.
  - (MODERATE, release machinery) `build_release_package.py` copied the
    notes template verbatim into each package as its `RELEASE_NOTES.md`,
    and nothing read that file's content — so the published v1.1.16
    package ships notes titled "ZMeta Release Notes Template" with
    placeholder provenance beside metadata declaring `formal_release`,
    while the real notes never entered the package. The builder gained
    `--release-notes`, the validator gained
    `RELEASE_PACKAGE_NOTES_PLACEHOLDER` (formal releases only — a
    candidate may still carry the template), and the checklist gained
    the step. Published checksums untouched; effective at the next cut.
  - (MODERATE, doc currency) `spec/release-signing-attestation.md` — a
    manifest-hash-pinned artifact validated on every release — still
    asserted "D-003 remains the roadmap" for a register item closed at
    the v1.1.12 cut. Also re-baselined: the change-governance worked
    command, TRADEMARK naming examples, the signing help example, and
    the compat CLI test's "current release target", the last now derived
    from the manifest so it cannot go stale again.
  - Enforcement growth across both verification passes: pytest
    742 (+237 subtests) -> 785 (+316 subtests).

## [1.1.16] - 2026-07-21
- External contribution (PR #7, bkershner-torch): mapping pack
  `adapters/mapping-packs/edge-comms-bladerf/` — two real bladeRF /
  ROS2 EW `rf_detection` captures from the 2026-05-14 edge-comms
  flight blackbox paired with schema-valid ZMeta v1.0 RF
  `OBSERVATION_EVENT` expected outputs: the first external real-capture
  corpus, and a second independent RF telemetry source alongside the
  maintainer deployments. The contribution's honesty handling was
  strong as submitted (null/zero-island geo omitted with
  `geo_status: UNAVAILABLE`, no-DOA case omits canonical bearing,
  repo-exact degraded timing fallback, no fabricated lineage).
- Maintainer review fixes applied on merge (adversarial review, PR #7):
  case-02's heading-derived bearing (uas heading + fixed antenna
  offset, no frame assertion in the capture) is demoted from canonical
  `payload.bearing` to `features.native_bearing_deg` per contract 6.4
  and AUTHORING rule 2 — the pack now documents the frame-provenance
  route (`quality.bearing_frame`/`heading_source`) for deployments that
  can assert it; the undocumented `1_SIGMA` measurement-error claim is
  dropped (raw bound kept as `features.native_bearing_error_deg`);
  `features.timestamp_source` preserves receive-time vs
  embedded-telemetry timestamp provenance; `mapping.yaml` is reconciled
  with the fixtures (conditional bearing rules, missing entries); the
  FFT-bin-width `bandwidth_hz` convention is documented.

## [1.1.15] - 2026-07-21
- End-to-end wire validation against official Dstl tooling
  (Apex-SAPIENT-Middleware v4.2.0, shipped BSI Flex 335 v2.0 pb2 modules
  and validator, stock strict configuration): egress dicts parse
  strictly into the official protobuf classes and pass the Apex
  validator clean; official-built ingress messages translate to
  schema-valid ZMeta events with zero findings; a live Apex instance
  accepted Registration and egress DetectionReports with no error
  records and no Error replies. The C# BSI Flex 335 v2 test harness and
  multi-node routing were not exercised (recorded in the pack README).
- SAPIENT egress ULID discipline (found by that validation, fixed
  pre-release): DetectionReport `report_id` is now a canonical ULID
  whose 48-bit timestamp is the event's own `event.ts` (never
  translate-time wall clock; new stdlib-only
  `adapters/egress/sapient/ulid_util.py`); `object_id` passes through
  only valid ULID `track_id` values or resolves via the caller-owned
  `object_map` (else refuses); Task `task_id` must be a valid ULID
  (else refuses) — SAPIENT-bridged command producers mint ULID task
  ids, preserving idempotent re-issue and TaskAck correlation across
  the bridge. Nothing id-invalid reaches the wire.
- SAPIENT (BSI Flex 335 v2.0) mapping pack and reference adapters — the
  first mapping pack targeting a nationally standardized external format
  (UK MOD C-sUAS standard; NATO C-UAS standard per STANREC 4869):
  - `adapters/mapping-packs/sapient-bsi-flex-335/` (schema_id
    `vendor:sapient_bsi335:v2`): declarative field maps, enum tables,
    the registration-declared-units doctrine, canonical-geo eligibility
    matrix, refusal matrix, and documented out-of-scope surface (SAPIENT
    Task ingress/command-safety, effector arming, AlertAck loop, protobuf
    wire encoding, UTM conversion).
  - `adapters/ingress/sapient/`: SapientMessage (protobuf-JSON dict)
    ingress. DetectionReport splits into OBSERVATION_EVENT plus
    per-claim INFERENCE_EVENTs with registration-derived model identity
    (layer separation demonstrated on a format that fuses fact and
    opinion in one message); fusion-node reports promote to STATE_EVENT
    only under caller-supplied `external_promotion` metadata including a
    caller-owned `loop_status` (never self-asserted); StatusReport maps
    to SENSOR_STATUS/PLATFORM_STATUS (1.1.0 branch); TaskAck maps to
    TASK_ACK with refusal when the issued-command correlation is
    unresolvable; Error maps to SCHEMA_VIOLATION. Registration is the
    units-and-error codex: signal/velocity values reach canonical fields
    only via registration-resolved units; unregistered nodes refuse
    detection translation outright (refusal over fabricated modality).
    Send-time timestamps widen `est_error_ms` by the registration's
    declared per-mode `maximum_latency` (conservative cross-mode maximum
    when the active mode is unknown).
  - `adapters/egress/sapient/`: COMMAND_EVENT→Task projection
    (GOTO/TRACK_TARGET/CHANGE_SENSOR_MODE only; altitude structurally
    excluded; everything else refuses) and STATE_EVENT→DetectionReport
    projection with `zmeta.risk`/`zmeta.timing_quality` object_info
    self-labels (label-not-launder), quarantine/rejected/prohibited-use
    export refusal per contract 3.3.
  - 12 adapter-harness fixtures (promotion happy path + refusal register:
    missing lineage, zero-fill geo, unregistered node, missing envelope
    timestamp, null node identity, unresolvable task correlation,
    model-less alert), `sapient-ingress` producer-authority policy block
    mirroring the cot-ingress promotion constraints, and 110 colocated
    adapter tests. Release manifest regenerated (policy_bundle and
    adapter_conformance categories) under the v1.1.14 release identity.

## [1.1.14] - 2026-07-17
- Intake funnel completed (maintainer decision): blank GitHub issues are
  disabled and a fourth minimal template, "General question or report"
  (labeled `question`), catches everything the three structured templates
  don't fit — all intake now arrives labeled.
- Release-flow reconciliation from the v1.1.13 retrospective:
  `release/sign_release_artifacts.py --write-checksums` now builds the
  missing `zmeta-release-package-<version>.zip` from the package directory
  automatically (never overwriting an existing zip; the governed
  `tools/build_release_package.py` is untouched), pinned by two new tests;
  `RELEASE_CHECKLIST.md` documents that behavior, marks the detached-
  signature items as signed-releases-only with an explicit
  signing-decision line, and adds the `sign_release_artifacts.py`
  `VERSION` default to the doc-currency pass.
- R1-10 full stack audit recorded (docs/advisory):
  `docs/r1_10_full_stack_audit.md` is the complete findings record — method
  (R1-09 AAR lessons as lenses; every substantive finding adversarially
  verified by independent live-probe skeptic passes), verified-green
  baseline, tiered findings with evidence anchors, refuted items, the
  positive-assurance record, and the maintainer disposition (fix every
  finding, then a follow-up audit). Summarized in the worklog R1-10 entry.
- R1-10 fixes — reference-adapter honesty pass (Class C reference code,
  colocated tests, adapter READMEs; audit A1-A4, C4, plus two found
  in-pass; no governed artifact touched):
  - example-vendor refuses null `platform_id`/`sensor_id` uniformly across
    all six signature keys; the `str()` identity coercion is removed so
    wrong-typed identity genuinely reaches schema validation (A1).
  - eo-cv refuses absent, null, or non-numeric confidence (the null
    TypeError crash path is gone); claim geo is all-or-nothing per contract
    6.8 (missing altitude omits geo entirely, `geo_source` "unavailable";
    the falsy-0.0 legitimate-altitude mishandling fixed); the README's
    stale `(0,0,0)` tier is corrected (A2).
  - kraken JSON-path fabricated defaults removed: missing `center_freq_hz`
    or `power_dbm` refuses; missing `bearing_error_deg` omits
    `angular_error_deg` and `quality.measurement_error` instead of
    inventing 15.0/`1_SIGMA` (A3).
  - moth JSON-replay missing `center_hz`/`rssi_dbm` refuses; geo is
    all-or-nothing (the `alt_m` 0.0 zero-fill — a live contract 6.8 MUST
    violation — is gone); TRUE_NORTH-mode missing `bearing_error_deg`
    omits the error fields instead of inventing 10.0/`1_SIGMA` (found
    in-pass) (A3).
  - The receiver-class `bandwidth_hz: 0.0` sentinel (receivers physically
    cannot measure emitter bandwidth) is now documented in the moth and
    signalhunter READMEs, mirroring kraken's convention; the kraken README
    covers both input paths.
  - The ingress template's copy-me docstring teaches conditional lineage
    (real parents only; never fabricate `based_on`) — the last residual of
    the v1.1.12 lineage-honesty class (C4).
  - CoT egress honest defaults (A4): `default_ce`/`default_le` default to
    CoT's 9999999.0 unknown-value convention (never invented 15/10 m
    accuracy); `use_wall_clock` defaults False (event-authoritative time;
    wall clock is an explicit replay-display opt-in per contract 9.5);
    confidence is appended to remarks whenever present (no longer dropped
    when `source_summary` exists); the schema-invalid
    `geo.ce`/`geo.le`/`geo.ce_display_m` ladder rungs are removed; the
    README example is corrected to validate against the dispatcher schema.
    The reference gateway's `--emit-cot` path inherits the honest defaults.
- R1-10 fixes — falsifiable checking machinery and release currency (B2,
  B3, C1/C6 residues):
  - Empty-input floors: all eight JSONL gate tools now exit nonzero when a
    fixture/input file parses to zero entries; `validate_conformance`'s
    success line prints counts; a registered examples corpus that exists
    but holds zero events fails under `--strict`/`--require-all`.
  - Checksum coverage: `sign_release_artifacts.py --verify-checksums` fails
    on zero valid lines (GNU `sha256sum -c` parity) and on any expected
    artifact present on disk but unlisted; future checksum files are
    written LF so plain `sha256sum -c` works on Linux (published
    `SHA256SUMS_*.txt` untouched); `validate_release_package` ties package
    checksum lines to the package artifact list the same way.
  - Stale-default class killed: `check_compat`'s default target and both
    bundle builders' version constants now derive from the release manifest
    `release_id` (`--version`/`--target` overrides kept).
  - New `gateway/tests/test_release_currency.py` pins README, installation
    guide, professional overview, `release/README.md`, CHANGELOG, and
    `check_compat` `TARGETS` against the manifest `release_id` — the
    machine encoding for the audit's all-prose doc-currency defect class.
    The three stale docs it pins are fixed (installation guide and
    professional overview to v1.1.13; `release/README.md` rewritten with
    version placeholders, a pinned current-release line, and the auto-built
    package-zip flow — the hand-`Compress-Archive` step contradicting
    RELEASE_CHECKLIST is gone).
  - Claims validator: dead `PLACEHOLDER_HASHES` removed, stale
    `pending_D-002` text fixed, and off-by-default `--verify-contract-hash`
    cross-checks claim `contract_hash` against the manifest's recorded
    value.
  - Projection defense-in-depth: `COMMAND_ALTITUDE_KEYS` in
    `tools/validate_projection.py` aligned to the full contract 7.8 set
    with strip+casefold normalization (drift since v1.1.7).
  - Kernel-gate wiring: the mandated local gate command in `AGENTS.md` and
    `CLAUDE.md` gains the examples gate (`validate_examples --strict
    --require-all`); RELEASE_CHECKLIST names the exact command; a pytest
    shim shells it so pytest covers the teaching corpus.
- R1-10 fixes — machine-encoded honesty checks and harness refusal register
  (audit A5-A7, B1, B4, A6). Class B surfaces, changed in lockstep: both
  schemas' `reason_code` enums (additive diagnostic widening, the
  sanctioned governed pattern), the v1.1 schema's quality `$def` (additive
  constraints; the locked v1.0 schema untouched beyond the shared
  diagnostic enum), policy files, and conformance fixtures:
  - A5 quality frame provenance: the v1.1 quality `$def` gains additive
    `bearing_frame` (enum `TRUE_NORTH`) and `heading_source` (string)
    properties; a version-agnostic `validate_semantics` check — the
    lock-compatible route for v1.0 events, whose only frame-provenance
    channel this is — fails `INVALID_QUALITY_BEARING_FRAME` /
    `INVALID_QUALITY_HEADING_SOURCE`; two bad-event corpus entries pin
    `MAGNETIC` under both versions.
  - B1 INFERENCE laundering completion:
    `inference_event.payload_must_not_contain` now carries the full
    contract 7.5 set (`members`, `estimated_state` join `track_id`); nested
    hits fail the new `INFERENCE_HAS_FUSION_STATE`; two corpus entries pin
    deep-nested smuggling (the recursive treatment STATE/COMMAND received
    at v1.1.10, which the INFERENCE branch never got).
  - B4 zero-fill heuristic: canonical geo at (0,0) now warns
    `GEO_ZERO_FILL_SUSPECTED` (warn-only — null island is a legitimate
    coordinate, so warn is the honest ceiling; contract 6.8 cited at the
    check).
  - A6 protected strip paths: gateway config loading rejects
    `strip_optional_fields` entries under
    `payload.extensions.risk_adjudication`/`external_promotion` at startup
    (fail-fast, citing the governance no-laundering rule); the projection
    field catalog's `never_mutable` declaration now has a runtime guard,
    not just the offline corpus check. configs/README documents the
    protected paths.
  - A7 harness refusal register: a `None` return from a `result: "event"`
    callable registers honest refusal (`event_count: 0` pins it; unpinned
    single-event fixtures implicitly expect exactly one event); surplus
    `expect.events` entries beyond the returned count now fail the new
    `ADAPTER_EXPECTATION_SURPLUS`; `fixture.schema.json` requires
    `event_count` alongside `expect.events` and the sync test pins it.
  - Refusal-fixture rollout: 12 fixtures land (adapter-harness corpus
    15 -> 27) — null identity (example-vendor), missing/null confidence +
    geo-omit (eo-cv), missing freq/power + error-omit (kraken), missing
    freq/power + geo-omit + TRUE_NORTH error-omit (moth); every refusal
    fixture negative-probed. Bad-event corpus 23 -> 27.
  - Diagnostic vocabulary: `INFERENCE_HAS_FUSION_STATE`,
    `INVALID_QUALITY_BEARING_FRAME`, and `INVALID_QUALITY_HEADING_SOURCE`
    join `schema_violation_allowed_reason_codes` and both schemas'
    `reason_code` enums in lockstep; the warn-only zero-fill code stays out
    of the rejection vocabulary. `policy/semantics.yaml`'s command comment
    now points at the v1.1.10 Known Enforcement Limitation so the
    documented synonym residual is not re-raised.
- R1-10 fixes — doc-currency and retention sweep (C5/C6/C8 documentation
  residues plus the audit's doc-currency list): handoff re-baselined to
  v1.1.13 (release-target section, current-release pointers,
  version-generic release-file rows, resolved S1-26 follow-ups, queue
  renumbering, verification-state retention prune to one historical block
  plus a v1.1.13 pointer); worklog stale present-tense claims rephrased as
  historical session records; `adapters/AUTHORING.md` reconciled to the
  harness contract (`event_count` required alongside `expect.events`,
  surplus expectations fail, refusal register for both result kinds) and
  now teaches the receiver-bandwidth sentinel convention and when
  `lineage.transform` applies; adapters README names the harness-pinned
  CoT/KLV template outputs; mapping-pack slug convention reconciled to the
  shipped `example-vendor-pack` exemplar; `policy/routing.yaml` comments
  and `policy/README.md` state that v1.0 enforcement flattens the
  `command_event` keys into origin gating (C5);
  `spec/conformance-classes.md` clarifies the claim model as attestation —
  the validator checks structure/claimability/required-command strings, it
  does not execute tests (C6); the README v1.1.11 historical hash-gate
  line is version-neutral so it never needs per-release edits; the
  RELEASE_CHECKLIST doc-currency item names the professional overview and
  the release-currency test.
- Contract wording clarifications (Class B, maintainer-directed):
  section 2.1's affirmative allowance extended to additive
  diagnostic-vocabulary widening (C3); section 5.7 holdover
  `est_error_ms` "must not decrease" (C7). Release manifest and
  conformance-claims regenerated with full-gate revalidation (release
  identity preserved: zmeta-v1.1.13).
- Post-fix-pass verification audit (six adversarial slices over the
  completed pass; every original audit probe re-run at HEAD) and its
  fixes: `GEO_ZERO_FILL_SUSPECTED` added to both schemas' SYSTEM_EVENT
  `reason_code` enums and the policy allowed list (Class B — the warn
  code's diagnostic was itself schema-invalid and the gateway destroyed
  its own zero-fill warning before egress; proven live, now passing),
  plus an inverse-coverage test asserting every governed violation code
  is emittable as a schema-valid diagnostic; CoT egress `point@hae` now
  uses the 9999999.0 unknown convention when `alt_m` is absent (sibling
  of the fixed ce/le class) and refuses events missing `event.ts`
  outside wall-clock mode; `sign_release_artifacts.py` default version
  is manifest-derived (last of the stale-default class);
  `--verify-contract-hash` with zero claims now fails instead of
  verifying nothing. Recorded, maintainer decision pending: the
  regenerated in-repo manifest diverges from the manifest entry pinned
  in the published `SHA256SUMS_v1.1.13.txt` (published checksums are
  immutable; resolution is the next release cut or an explicit
  accepted-divergence record).

## [1.1.13] - 2026-07-16
- Adapter-harness refusal fixtures (Class B, maintainer-directed — the
  machine-encoding follow-up from the authoring-guide red-team AAR):
  - `tools/validate_adapter_conformance.py` gains the `expect.event_count`
    fixture key — an exact pin on how many events the fixture callable
    returns. `event_count: 0` with `result: "events"` pins a fail-closed
    refusal the same way the existing keys pin emission. A non-integer or
    negative value is a fixture error; a count mismatch is
    `ADAPTER_EVENT_COUNT_MISMATCH`.
  - `conformance/adapter-harness/must-pass.jsonl` grows 11 -> 15: an
    example-vendor emission fixture (pinning the pack's field mapping,
    the visible `UNSYNCED` degraded-timing fallback, and lineage
    omit-not-fabricate via `forbidden_paths`) plus one refusal fixture per
    schema-required RF input field (`bandwidth_hz`, `center_freq_hz`,
    `power_dbm`) — the worked exercise now demonstrates ladder step 4.
  - `conformance/adapter-harness/fixture.schema.json` learns `event_count`
    (result-level, allowed alongside `events`), and a new
    `gateway/tests/test_fixture_schema_sync.py` pins the lint schema to the
    harness's actual fixture surface so future harness keys cannot silently
    turn into false lint failures.
  - Fixture-key reference updated in `adapters/AUTHORING.md` §6 and the
    harness README. Release manifest and example claims regenerated for
    `zmeta-v1.1.13`; `tools/check_compat.py` gains the `v1.1.13` target and
    CI/compat tests re-baseline to it.
- Authoring-guide hardening from its first external review (red-team) pass:
  new `adapters/AUTHORING.md` §3 rule that schema minimums are per-subtype
  (requiredness comes from the schema, never from sample inputs) and four
  review-proven failure-mode lessons for AI agents in §9
  (primaries-not-summaries, refusal tests per required field,
  guide-as-checklist, exact evidence commands); AAR record in the worklog.
- Onboarding batch (docs/advisory + reference; no schema, policy, vocabulary,
  or validation-behavior change):
  - README restructured for first contact: What Is/Is Not moved above the
    release notes, a new "See It Work In Ten Minutes" runnable proof path, a
    persona-based "Start Here By Role" section, and a new "ZMeta In The
    Field" section recording that the Production reference adapters are
    extracted from fielded EO/CV and RF deployments.
  - New worked exercise `adapters/ingress/example-vendor/`: a complete small
    ingress adapter implementing the `example-vendor-pack` declarative
    mapping to the `adapters/AUTHORING.md` requirements — including
    fail-closed refusal of readings missing the schema's required RF
    features (`bandwidth_hz` included) and no gateway-owned `profile` stamp
    — with 12 colocated tests including a structural match against the
    pack's input/expected fixture pair. Listed in the adapters README table
    (which also gains the previously missing JREAP row).
  - New `tools/check_adapter.py`: advisory one-command wrapper for the
    tool-based steps of the authoring-guide validation ladder (fixture lint,
    `validate.py --strict`, `check_compat.py`, adapter harness, optional
    kernel gate); delegates to the governed validators, prints each
    underlying command, and fails on empty events/fixture input instead of
    passing vacuously.
  - New `conformance/adapter-harness/fixture.schema.json`: advisory JSON
    Schema for harness fixture lines (typo guard; all existing fixtures lint
    clean).
  - New GitHub issue templates (adapter authoring friction, semantic
    ambiguity report, deployment field report) and a PR template carrying
    the change-class/validation/no-secrets checklist — structured intake for
    the external-PRs-are-field-telemetry doctrine.
  - New `docs/README.md` index separating advisory guidance from maintainer
    process records; completed worklog task sections S0-01 through R1-05
    archived verbatim to `docs/zmeta_refinement_worklog_archive.md` (active
    worklog 2.7k -> ~0.5k lines); `RELEASE_CHECKLIST.md` gains standing
    doc-currency and retention-pass items so current-facing docs re-baseline
    at every release.
- Adapter authoring guide (docs/advisory): new `adapters/AUTHORING.md` — a
  single consolidated entry point for humans and AI agents building a new
  adapter against a pinned release (orientation, input floor, layer choice,
  the anti-fabrication non-negotiables, the exact validation command ladder,
  a formal adapter-harness fixture-key reference, producer-authority notes,
  and definition-of-done). Consolidates guidance previously spread across
  `adapters/README.md`, the ingress template README, `conformance/README.md`,
  and `tools/README.md`; adds no new rules and changes no validation
  behavior. Linked from `adapters/README.md`.
- Examples: new `examples/zmeta-eo-chain-examples.jsonl` — a worked EO full
  chain (`OBSERVATION_EVENT -> INFERENCE_EVENT -> FUSION_EVENT ->
  STATE_EVENT`, genuine chained `lineage.based_on`, policy-allowed producers,
  local `data_ref` video pointer, no raw features on STATE) as the EO
  companion to the core RF chain; registered in `tools/validate_examples.py`
  and the examples README.
- Recorded the v1.1.12 publication (R1-08: pushed tag/commit `e5a88b1`,
  GitHub release with all eight assets, marked Latest, checksums-only) and
  aligned current-facing docs, the CI compatibility target, and the
  compatibility CLI test with the published `v1.1.12` release.
- Closed D-003 by maintainer decision: the S1-11B future-branch roadmap
  artifact, the extension registry, and the promotion evidence bar now
  track future versioned-branch work individually. The deferred issue
  register is fully closed (D-001 through D-014).

## [1.1.12] - 2026-07-08
- Governance (governed docs): `spec/extension-registry.md` gains a
  "Promotion Evidence Requirements" section — promoting a reserved/proposed
  concept into a named version branch now requires at least two independent
  implementations demonstrating the need plus a documented semantic-contract
  Section 2.6 failure condition that policy, config, profiles, adapter
  mappings, and namespaced extensions cannot solve; the change-governance
  Class D checklist references the bar. Encodes the
  external-PRs-are-field-telemetry intake doctrine into governed process.
- S1-11B (governed baseline): new machine-readable future-branch roadmap —
  `spec/future-branch-roadmap.yaml` (18 candidates with status, priority,
  dependencies, required adoption surfaces, recorded field evidence, and
  promotion tripwires; 3 recorded rejection/defer decisions) plus
  `spec/future-branch-roadmap.md` governance companion,
  `tools/validate_future_roadmap.py` (structure, vocabulary, dependency and
  registry cross-reference resolution, tripwire coverage, and a
  status-leakage check), focused tests, and a new `future_branch_roadmap`
  release-manifest group (groups=19, artifacts=70). The roadmap makes no
  concept valid. The S1-11A Section M condition for closing D-003 is now
  met; closure is recommended and awaits the maintainer.
- Adapter lineage honesty (runtime/reference): kraken (1.2.0), moth (1.2.0),
  signalhunter (1.1.0), KLV template (0.2.0), MAVLink template (1.2.0), and
  eo-cv (1.1.0) no longer fabricate `lineage.based_on` with fresh random
  UUIDv7 values. Observation and system outputs omit lineage unless the
  caller supplies real parent ids (`based_on=[...]`); mandatory-lineage
  events refuse to emit instead of inventing parents (MAVLink STATE requires
  `based_on`/`source_zmeta_event_id`; eo-cv INFERENCE requires
  `parent_event_ids` or a schema-valid UUIDv7 `source_event_id`, which now
  feeds real lineage instead of being dropped). Adapter-harness fixtures pin
  the honest behavior (one new caller-supplied-lineage fixture; total 11);
  new eo-cv ingress tests; the ingress template README lineage rule is now
  "never fabricate — omit or refuse".
- Gateway send-failure containment (runtime): outgoing UDP sends are routed
  through `_send_datagram`, which catches `OSError` (e.g. payloads above the
  ~65507-byte UDP limit), drops that datagram with new `send_failure`
  metrics/log diagnostics, and keeps the main loop alive; forwarded/CoT
  counters only increment on actual sends. Previously an oversize payload
  terminated the gateway process. Covered by new tests including a
  real-socket oversize proof.
- Documentation honesty (advisory): `adapters/mapping-packs/README.md`
  states that packs are declarative descriptions plus test evidence — no
  runtime engine executes `mapping.yaml`;
  `docs/zmeta_professional_overview.md` documents that
  `risk_adjudication`/`external_promotion` are deliberately enforced by
  policy + conformance above the locked schema kernel, with schema-level
  standing parked as an evidence-gated roadmap candidate.
- Process closeout: the handoff's open-ended human-decision list is resolved
  to recorded standing defaults, leaving two genuinely open maintainer
  decisions (release-signing process, v1.1.0 adopted-vs-experimental).
  `tools/check_compat.py` gains the `v1.1.12` target; release manifest and
  example claims regenerated for `zmeta-v1.1.12`.

## [1.1.11] - 2026-07-07
- Field-driven adoption guidance harvested from a live at-scale deployment
  (upstream PR #4, reviewed and not merged): three new advisory docs —
  `docs/zmeta_mqtt_binding_guidance.md` (MQTT topic shape using locked
  vocabulary, retain/tombstone honesty rules, transport-independent command
  governance), `docs/zmeta_vocabulary_crosswalk.md` (mapping common
  deployment concepts such as ais_track, geofence_alert, heartbeat, and
  fleet snapshots onto canonical vocabulary), and
  `docs/zmeta_correlation_pattern.md` (cross-sensor correlation with
  existing v1.0 vocabulary: FUSION identity, INFERENCE/ASSOCIATION bond
  assignment/dissolution with atomic-split semantics, and the
  `correlation_hint` payload extension). Advisory only; no validation or
  dispatch changes.
- Extension registry (governed): added `CORRELATION_HINT` (proposed,
  fusion_extension, optional_omission projection), `DATA_REF_MEDIA_METADATA`
  (proposed, data_evidence, future_branch_required),
  `AGGREGATE_STATE_SNAPSHOT` (reserved, state_extension,
  future_branch_required), and `PAYLOAD_SCHEMA_URI` (rejected, with
  rationale: envelope-level external payload schema pointers reintroduce the
  N-by-N problem; the need is served by adapter mapping packs). Registry
  entries make no new vocabulary valid.
- Examples: new `examples/zmeta-correlation-pattern-examples.jsonl` (7
  events, Profile H, pure locked v1.0 vocabulary) demonstrating the full
  correlation flow — uncorrelated observations, fusion identity creation,
  ASSOCIATION BOND_ASSIGNED, an observation carrying
  `payload.extensions.correlation_hint`, a TRACK_STATE projection, and an
  atomic-split BOND_DISSOLVED; registered in `tools/validate_examples.py`.
- Conformance: two new `conformance/bad-events/must-fail.jsonl` fixtures
  (corpus total 23) proving the correlation hint cannot launder `confidence`
  or `track_id` into an observation payload at any nesting depth
  (`OBSERVATION_HAS_IDENTITY`).
- Aligned post-release current-facing documentation, tool examples, the CI
  compatibility target, and the compatibility CLI test with the published
  `v1.1.10` release, and recorded the v1.1.10 publication (tag, GitHub
  release, checksums-only status) in the handoff/worklog. Current-facing
  surfaces now reference `v1.1.11`; `tools/check_compat.py` gains the
  `v1.1.11` target. Historical release records and published checksums for
  prior versions remain unchanged.

## [1.1.10] - 2026-07-03
- Command-altitude enforcement hardened: `policy/semantics.yaml`
  `command_event.payload_must_not_contain` expanded from `[alt, alt_m,
  altitude]` to the full contract §7.8 altitude set (adds `altitude_m`,
  `alt_hae_m`, `alt_msl_m`, `agl_m`, `target_alt_m`, `target_altitude`; bare
  `alt` retained as a defensive superset). `COMMAND_EVENT` must not specify
  altitude at any nesting depth in payload, `target_geo`, `geometry`, or
  `extensions`; vertical deconfliction remains with the receiving autonomy.
- STATE laundering enforcement hardened: `state_event.payload_must_not_contain`
  expanded from `[features, raw_features]` to the full contract §7.7 set (adds
  `modality`, `measurement`, `measurements`, `t_start`, `t_end`, `data_ref`,
  `data_refs`), and the STATE semantic check in `gateway/src/validators.py` now
  recurses via `_find_forbidden_key` (case-insensitive, reporting
  `{field, path}`) like the observation/inference/command branches. Nested raw
  features, measurements, observation timestamps, and raw-artifact pointers can
  no longer launder into a STATE projection.
- Adapter calibration honesty: the Kraken and Moth reference adapters no longer
  hardcode `calibration_state: CALIBRATED`. `calibration_state` is now a keyword
  parameter defaulting to the conservative, honest `UNCALIBRATED` (enum
  `CALIBRATED`/`UNCALIBRATED`/`DEGRADED`), so `CALIBRATED`/`DEGRADED` are
  asserted only when a deployment substantiates them — mirroring the existing
  `platform_heading_deg` convert-or-config pattern. SignalHunter was already
  honest.
- Egress MAVLink command guard aligned: the altitude guard in
  `adapters/egress/mavlink/zmeta_command_to_mission_intent.py` expanded from
  `{alt, alt_m, altitude}` to the full §7.8 set, so the command→mission-intent
  projection refuses altitude at any nesting depth.
- Denylist key normalization: the semantic forbidden-key check
  (`_find_forbidden_key`) and the egress MAVLink altitude guard now strip and
  casefold keys before matching, so whitespace- or case-padded copies of a
  reserved name (e.g. `"features "`, `"alt_hae_m "`) can no longer evade the
  STATE/command denylists that the schema pins only for the exact bytes. The
  remaining residual — arbitrarily *renamed* raw content or altitude (e.g.
  `z_m`) in free-form objects — is the inherent limit of a name denylist;
  closed payload schemas plus producer conformance, not denylist growth, are
  the mitigation.
- Conformance: added eleven `conformance/bad-events/must-fail.jsonl` fixtures
  exercising deep-nested (schema-valid) STATE laundering across every §7.7
  category, case-insensitive and whitespace-padded evasion, and command altitude
  nested in `extensions` across §7.8 field names; added direct
  `validate_semantics` unit tests asserting the new `{field, path}` STATE detail
  shape. Enforcement was adversarially verified (100+ empirical bypass attempts).
- These changes align policy and reference enforcement with the
  already-normative semantics contract §7.7/§7.8; they add no schema or locked
  v1.0/v1.1.0 vocabulary. Tightened enforcement rejects events that were always
  contract-violating.

## [1.1.9] - 2026-06-18
- Refreshed the README-linked documentation surface after the v1.1.8 closeout:
  `spec/installation-guide.md` now points new installs at the maintained
  `configs/` templates, documents Docker/mapping-pack/validation boundaries,
  and the handoff/worklog no longer treat the pre-closeout `beffed3` cleanup
  commit as the latest pushed integration baseline.
- Clarified v1.1.8 current-main upgrade guidance for Moth tunnel/replay
  bearings, MAVLink headings, Kraken heading compensation, and Kraken CSV SNR
  omission. The docs now also state explicitly that `bearing.frame`,
  `quality.bearing_frame`, and `quality.heading_source` are producer
  assertions/provenance, not proof of calibration, authenticity, or correctness.
- Added advisory industry-sharing and open-specification posture docs:
  `IP_POLICY.md`, `CONTRIBUTING.md`, `CONFORMANCE.md`, `TRADEMARK.md`, and
  `docs/zmeta_defensive_publication.md`. These clarify Apache-2.0 baseline
  limits, contributor authority, private dialects, conformance claims, ZMeta
  name use, and public defensive-publication guidance without changing schemas,
  policy behavior, event vocabulary, or the locked v1.0 kernel.
- Closed D-013 by adding `TIMING_STATUS_AGE_NEGATIVE`, profile-specific
  `max_negative_age_ms`, default warn-mode policy handling, risk-adjudication
  support, schema/policy diagnostic vocabulary coverage, and tests/conformance
  for event timestamps that predate the latest applicable TIME_STATUS beyond
  tolerance.
- Closed D-014 by specifying that unknown compact integer keys are rejected at
  decode, preserving string extension keys, adding decoder enforcement, and
  extending encoding-negative fixtures for the unknown-key path.
- Aligned post-release current-facing documentation, tool examples, CI
  compatibility target, and the compatibility CLI test with the published
  `v1.1.8` release after the stack audit. Historical `v1.1.7` release records
  and published checksums remain unchanged.
- Corrected two remaining current-facing audit references: the adapter
  compatibility example and the change-governance manifest rebuild example now
  target the `v1.1.8` baseline.
- Recorded final baseline audit closeout in the handoff/worklog and refreshed
  local workspace notes. The audit confirmed full local validation, runtime
  smoke checks, package/bundle build validation, Docker Compose config
  rendering, clean GitHub queue, and green CI for the pushed current-main
  closeout commit.

## [1.1.8] - 2026-06-12
- Added a machine-checkable bearing reference-frame marker: optional
  `payload.bearing.frame` with single-value enum `["TRUE_NORTH"]` in the
  v1.1.0 schema, a normative semantics-contract section 6.4 (canonical
  bearings SHALL be degrees true north; sensor-native frames convert or omit;
  `quality.bearing_frame`/`quality.heading_source` provenance path for v1.0
  producers), and an experimental `BEARING_FRAME` extension-registry entry.
  The locked v1.0 schema is untouched and still rejects the `frame` key.
- Enforced the bearing reference-frame contract in governed conformance
  corpora: new `observation-bearing-frame-mislabeled` bad-event entry (corpus
  total 10) and an adapter-harness `expected_values` mechanism that pins exact
  output values per fixture (1e-6 numeric tolerance, distinct
  missing/mismatch codes, boolean pins never match numeric output). The
  kraken fixture now pins the rotation math, a no-heading fixture proves
  convert-or-omit, and Moth/MAVLink fixtures pin unknown-frame omission
  behavior (harness total 10).
- Hardened the Kraken adapter (1.1.0): optional platform-heading compensation
  emits true-north `bearing.az_deg` as `(doa + heading + offset) % 360` with
  frame/heading-source provenance, omits the canonical bearing when no heading
  is supplied, always preserves raw DOA in
  `features.doa_array_relative_deg`, and no longer fabricates CSV
  `quality.snr_db` from RSSI.
- Hardened the Moth adapter (1.1.0): serial and custom-MAVLink omnidirectional
  detections no longer fabricate a `bearing.az_deg 0.0` /
  `angular_error_deg 180.0` placeholder, JSON replay no longer invents a
  bearing when the input carries none, and tunnel/replay measured bearings
  emit canonical `payload.bearing` only when the caller explicitly asserts
  `bearing_frame="TRUE_NORTH"`; otherwise raw unknown-frame bearings are
  preserved under explicit `features.bearing_frame_unknown_*` keys.
- Audited remaining bearing/heading producers: SignalHunter (1.0.1) gradient
  LOBs now assert `TRUE_NORTH`/`GPS_COURSE` provenance (true north by
  geodesic construction); the MAVLink adapter (1.1.0) omits
  `payload.heading_deg` when `hdg` is 65535 (unknown), absent, or present
  without explicit `heading_frame="TRUE_NORTH"` instead of emitting an invalid
  or fabricated canonical heading, while preserving unasserted values under
  `payload.quality.mavlink_hdg_frame_unknown_deg`; CoT egress frame behavior is
  documented; eo-cv, CoT ingress, and JREAP have no bearing/heading exposure.
- Added runtime fabrication and resource guards: MAVLink platform state
  refuses null-island `(0, 0)` TRACK_STATE fabrication when position is
  absent or pre-fix, the gateway gained an opt-in `warn_datagram_bytes`
  oversize-datagram observability setting (default off, send behavior
  unchanged), and the producer rate limiter purges stale windows without
  changing accept/reject decisions.
- Regenerated the release manifest and example claim hashes for the governed
  changes. No event vocabulary became valid under `zmeta_version: "1.0"`.
- Added `docs/zmeta_professional_overview.md`, an advisory overview for
  engineers, operators, and leadership covering ZMeta purpose, architecture,
  schemas, adapters, gateway deployment, profiles, encodings, data governance,
  AI provenance, and RF-to-tasking workflows.

## [1.1.7] - 2026-06-10
- Added formal human/AI agent change governance through `AGENTS.md` and
  `docs/zmeta_change_governance.md`, including change classes, documentation
  requirements, validation gates, release limits, and publication workflow.
- Added downstream clone guidance distinguishing local integration freedom from
  compatibility-breaking private ZMeta dialect or fork changes.
- Added governed `process_governance_hash` release-manifest coverage for
  process guidance.
- Added a release audit record for stale/current-release references, ignored
  local build residue, generated artifact handling, and tracked-source secret
  scans.
- Added machine-checkable profile-projection preservation rules and fixtures for
  `payload.extensions.risk_adjudication` and
  `payload.extensions.external_promotion`, preventing lower-profile exports
  from stripping accepted-risk labels or compact external-promotion evidence.
- Strengthened the extension registry contract with validated projection
  behavior, risk relevance, policy-preservation, security/privacy, and fixture
  reference fields.
- Added post-v1.1.6 integration guidance for external state promotion metadata,
  `trust_ref` limits, and consumer responsibility for accepted-risk labels.
- Added `tools/lint_policy_risk_modes.py` to flag unsafe `ignore` settings on
  material timing, lineage, external-promotion, command, trust, or safety risk.

## [1.1.6] - 2026-06-09
- Added the semantic risk-adjudication baseline: locked, tunable, advisory, and
  future-extension rule classes with bounded reject, warn, degrade, quarantine,
  and ignore behavior.
- Added explicit operator-side accepted-risk filtering with display, fusion,
  state, command, autonomy, AAR, and audit presets.
- Added semantic bad-event fixtures and a shared adapter conformance harness.
- Added kernel-protection doctrine and full kernel-protection validation across
  projection, registry, conformance classes, encoding negatives, precision
  policy, release manifest/package, bad-event corpus, and adapter harness.
- Hardened direct CoT egress so malformed state payloads carrying raw
  observation/evidence fields fail closed.
- Completed an end-to-end stack and runtime audit covering examples,
  compatibility, gateway self-tests, live UDP workflows, Profile L packet size,
  release/package smoke tests, and containerized SDR-derived RF workflow checks.
- Preserved v1.0/v1.1.0 version isolation; no future vocabulary became valid
  and literal raw IQ support remains future work pending real sensor samples.

## [1.1.5] - 2026-05-07
- Hardened the ZMeta semantic-governance baseline through S0/S1 audits covering
  contract lockdown, contract-to-stack alignment, release hashing, and formal
  release packaging.
- Added structured release manifest hashing with category hashes, release bundle
  hash, release manifest hash, builder, validator, tests, and conformance
  integration.
- Added formal release package documentation, templates, package builder,
  package validator, no-secret checks, release-package tests, and optional
  conformance integration.
- Added or audited profile projection preservation, extension registry
  validation, conformance class manifests and claims, encoding-negative
  validation, and profile precision policy validation.
- Preserved strict `zmeta_version` dispatch and v1.0/v1.1.0 vocabulary
  isolation; no new event vocabulary became valid.
- Removed out-of-scope organizational artifact language from active ZMeta scope;
  D-004 is closed as removed from the ZMeta baseline.
- Added the D-003 future versioned semantic branch roadmap while keeping future
  concepts invalid until adopted through versioned implementation and audit.

## [1.1.4]
- Fixed edge/gateway release bundles so downloaded packages include
  `conformance/` and `release/sign_release_artifacts.py`, allowing bundle-local
  gateway self-tests and release-signing tests to run.
- Added regression coverage for release bundle self-test dependencies.

## [1.1.3]
- Fixed GitHub Actions gateway self-test failure by preferring the built-in
  deterministic CBOR encoder/decoder when available, keeping `cbor2` as a
  fallback.
- Added regression coverage for gateway and compact CBOR behavior when `cbor2`
  is present.
- Opted CI into Node.js 24 JavaScript actions to address the hosted runner
  Node.js 20 deprecation warning.

## [1.1.2]
- Added `tools/check_compat.py` for migration-oriented JSON/JSONL diagnostics.
- Added malformed protobuf decoder regression tests for varints, length fields,
  truncated fixed fields, invalid UTF-8, and random byte samples.
- Added gateway timing-quality metrics that distinguish source-provided timing
  from degraded `UNKNOWN`/`UNSYNCED` fallback timing.
- Clarified deployment policy variant hash behavior, adapter invocation style,
  degraded fallback timing interpretation, and release verification instructions.
- Hardened release signing helper GPG discovery for Gpg4win installs and
  signature refreshes.

## [1.1.1]
- Normalized ingress adapter timestamps to the strict UTC trailing-Z schema form.
- Added explicit fallback timing quality to ingress adapter operational events.
- Hardened protobuf decoding with message, field, payload, JSON-depth, and nested-message bounds.
- Added optional strict producer-authority and Profile L timing-degrade policy variants.
- Added CoT skip metrics so unpublishable state events are visible at the gateway boundary.
- Added release checksum/signature helper tooling and refreshed release checklist guidance.
- Tightened pytest collection to ignore generated release/cache directories.

## [1.1.0]
- Added experimental protobuf transport projection with schema, pure-Python codec,
  gateway/tool support, docs, and round-trip tests.
- Added a single-event encoding conversion CLI for JSON, CBOR, compact CBOR, and
  protobuf.
- Hardened CBOR output to use deterministic/canonical map ordering.
- Updated encoding compatibility guidance for JSON, CBOR, compact CBOR, and protobuf.
- Added a canonical version-discriminated JSON schema and tightened v1.1.0
  validation so v1.1-only vocabulary cannot validate under `zmeta_version: "1.0"`.
- Added v1.1.0 semantic extension governance, reserved uncontracted observation
  modalities, and enforced minimum validation for expanded task types.
- Defined `event_subtype` as a normative semantic discriminator and enforced
  subtype/payload discriminator consistency across v1.0 and v1.1.0 schemas.
- Enforced claimed Profile L/M/H export event-type rules in the schemas while
  keeping `profile` optional.
- Prohibited inference payloads and claims from carrying track/fusion authority
  fields (`track_id`, `members`, `estimated_state`).
- Prohibited STATE_EVENT payloads from carrying raw observation features,
  measurements, modalities, timestamps, or raw data references.
- Hardened COMMAND_EVENT payloads against altitude/vertical-control fields and
  moved arbitrary command metadata behind `payload.extensions`.
- Added task-specific COMMAND_EVENT validation for GOTO, ORBIT, HOLD,
  SEARCH_BOX, RETURN_TO_BASE, LAND, LOITER, SCAN_RF, TRACK_TARGET, and
  CHANGE_SENSOR_MODE.
- Added strict UTC-Z timestamp validation across envelope, payload, data
  reference, command, fusion, and timing-status timestamp fields.
- Enforced paired observation windows and RF window midpoint semantic
  validation.
- Tightened geodesy, speed, quality-unit, EO/ACOUSTIC observation, data reference,
  SENSOR_STATUS, and PLATFORM_STATUS semantics.
- Added producer-authority, timing-freshness, and lineage policy packs with
  runtime validators and focused tests.
- Expanded violation reason codes while keeping TASK_ACK reason codes
  task-specific.
- Added conformance fixtures for valid and invalid hardened-schema behavior.
- Added non-normative compatibility normalizer tooling for opt-in adapter-side
  migration from selected legacy wire forms.
- Updated README, adapter guidance, examples, and validation tools to use the
  canonical version-discriminated schema.

## [1.0.5]
- Clarified immutable source-authored events versus profile/export projections.
- Clarified UUIDv7 timestamp bits as identity-generation time, not event time.
- Added TIME_STATUS freshness guidance and stale timing behavior.
- Clarified authoritative envelope lineage versus payload-local provenance.
- Tightened authority-boundary, observation-quality, deduplication, system-event extensibility, confidence-degradation, and merge/split lifecycle wording.

## [1.0.4]
- Added UUIDv7 event identity requirements and aligned schema validation.
- Made timing quality metadata mandatory across all profiles.
- Added normative track persistence, deduplication, and edge failure-mode configuration guidance.
- Clarified confidence semantics and Profile L compact stripping rules.
- Aligned schema, policy, validators, adapters, configs, examples, conformance tests, and CI with the locked semantic contract.
- Added timing-quality enforcement, profile mismatch checks, event/TASK_ACK dedupe checks, and semantic-contract hashing in the reference gateway tooling.

## [1.0.3]
- Added compact binary mapping for Profile L plus reference CBOR/compact encoders and size tooling.
- Expanded schema/policy to cover Observation/Inference/Fusion payloads and SystemEvent requirements.
- Enhanced gateway with JSON/CBOR/compact I/O, strict validation, rate limiting/metrics logs,
  contract-hash gating, and COMMAND_EVENT dedupe.
- Added conformance pack, example validators, and encoding roundtrip examples/tests.
- Added new documentation for compact mapping, field dictionary, profile compatibility, and refreshed specs.
- Fixed MAVLink TASK_ACK ingress to require original_event_id in metrics.
- Set pytest cache to repo-local path to avoid teardown hangs in restricted environments.

## [1.0.2]
- Expanded installation docs with bundle-based step-by-step guidance, prerequisites,
  config references, verification, and troubleshooting.
- Added deployment helpers and configs for edge/gateway installs (Docker Compose + config templates).
- Added end-to-end workflow test tooling with profile variants.
- Tightened routing policy and validator enforcement (producer allowlists, TASK_ACK required fields).
- Updated semantics contract and examples for operating model, lineage, and data_ref guidance.
- Release artifacts refreshed; obsolete Compose `version` removed.

## [1.0.1]
- Added optional timing fields (`t_publish`, `t_receive`) to schema and docs.
- Clarified observation quality vs confidence; tightened role/profile guidance.
- Updated policy/routing enforcement and producer rules; EDGE role restricted to observation + system.
- Added live gateway UDP test tool and Makefile target; expanded README/quickstart instructions.

## [1.0.0]
- Initial public release of the ZMeta specification

---

## Historical Integration Notes

Per-release integration guidance, moved verbatim from `README.md` at the
2026-07-27 closeout so the README leads with what the standard is rather than
with release archaeology. Current-release notes stay in `README.md`.

### v1.1.16 Integration Notes

- Corpus for RF adapter authors:
  `adapters/mapping-packs/edge-comms-bladerf/` pairs two real bladeRF
  detections with expected ZMeta output, demonstrating the refusal
  doctrine on real data — geo omitted for null and zero-island sensor
  positions (`geo_status: UNAVAILABLE`), canonical bearing omitted in
  both cases because the native bearing is heading-derived with no
  producer frame assertion (values travel as
  `features.native_bearing_deg`/`native_bearing_error_deg`), degraded
  timing fallback carried explicitly, no fabricated lineage. Its
  reference implementation shipped in v1.1.18 as
  `adapters/ingress/bladerf/`.
- The pack README documents the frame-provenance route
  (`quality.bearing_frame: TRUE_NORTH` + `quality.heading_source`) for
  deployments that can assert their heading reference, mirroring the
  kraken reference adapter.

### v1.1.15 Integration Notes

- New mapping pack `adapters/mapping-packs/sapient-bsi-flex-335/`
  (schema_id `vendor:sapient_bsi335:v2`) plus reference adapters:
  `adapters/ingress/sapient/` translates SapientMessage protobuf-JSON
  dicts (DetectionReport → OBSERVATION + per-claim INFERENCE with
  registration-derived model identity; fusion-node reports → STATE
  promotion under caller-owned `external_promotion` metadata;
  StatusReport → SENSOR_STATUS/PLATFORM_STATUS on the 1.1.0 branch;
  TaskAck → TASK_ACK; Error → SCHEMA_VIOLATION), and
  `adapters/egress/sapient/` projects COMMAND_EVENT → Task
  (GOTO/TRACK_TARGET/CHANGE_SENSOR_MODE only; altitude structurally
  excluded) and STATE_EVENT → DetectionReport with
  `zmeta.risk`/`zmeta.timing_quality` self-labels.
- Registration capture is the units-and-error codex: signal and
  velocity values reach canonical fields only through
  registration-resolved units; unregistered nodes refuse detection
  translation. Send-time timestamps widen `est_error_ms` by the
  registered per-mode `maximum_latency`.
- SAPIENT id discipline on egress: DetectionReport `report_id` is a
  ULID minted from the event's own timestamp; `object_id` and Task
  `task_id` are validated ULIDs (caller-owned `object_map` for native
  track ids; SAPIENT-bridged command producers mint ULID task ids).
- SAPIENT Task ingress (external DMMs tasking ZMeta platforms) is
  deliberately out of scope for this release (command-safety boundary).
- `tools/check_compat.py` gains the `v1.1.15` target; the compat target
  and current-facing docs re-baseline to the v1.1.15 release manifest.

### v1.1.14 Integration Notes

- Reference ingress adapters now refuse input they previously translated
  with invented values: null `platform_id`/`sensor_id` (example-vendor),
  absent/null/non-numeric confidence (eo-cv), missing
  `center_freq_hz`/`power_dbm` on the kraken/moth JSON-replay paths.
  Canonical geo is all-or-nothing per contract 6.8 (missing altitude
  omits geo entirely — no more `alt_m: 0.0` fill), and optional error
  bounds are omitted when unmeasured, never defaulted. `bandwidth_hz:
  0.0` from receiver-class RF sensors is a documented sentinel (kraken,
  moth, and signalhunter READMEs).
- CoT egress display defaults changed: unknown accuracy and unknown
  altitude render as CoT's `9999999.0` unknown convention (previously
  invented 15 m/10 m and 0 m); event time is authoritative by default
  (`use_wall_clock` is now an explicit replay-display opt-in); events
  missing `event.ts` are refused outside wall-clock mode; confidence is
  appended to remarks whenever present.
- New governed diagnostic codes in both schemas' SYSTEM_EVENT
  `reason_code` enums: `INFERENCE_HAS_FUSION_STATE`,
  `INVALID_QUALITY_BEARING_FRAME`, `INVALID_QUALITY_HEADING_SOURCE`,
  `GEO_ZERO_FILL_SUSPECTED` (warn). `quality.bearing_frame` /
  `quality.heading_source` are now enforced at the semantics layer for
  both versions (and by enum in the v1.1 schema); nested
  `members`/`estimated_state` in INFERENCE payloads are rejected
  recursively; canonical geo at (0,0) draws a warn-severity diagnostic.
- Adapter-harness fixtures are stricter: `expect.events` requires
  `event_count`, surplus expectations fail
  (`ADAPTER_EXPECTATION_SURPLUS`), and a `None` return from a
  `result: "event"` callable registers refusal (`event_count: 0`).
  Must-pass corpus 15 -> 27; bad-events corpus 23 -> 27. Third-party
  fixtures pinning per-event expectations without `event_count` must add
  it.
- Gateway configs that list `payload.extensions.risk_adjudication` or
  `payload.extensions.external_promotion` under `strip_optional_fields`
  are rejected at startup (accepted-risk labels and promotion evidence
  stay filterable downstream).
- The validation tools fail on empty input instead of passing vacuously;
  checksum verification cross-checks coverage against the artifact list;
  new `SHA256SUMS` files are LF so plain `sha256sum -c` works on Linux.
- `tools/check_compat.py` gains the `v1.1.14` target; the compat target
  defaults in `check_adapter.py`, `check_compat.py`, the bundle
  builders, and `sign_release_artifacts.py` all derive from the release
  manifest now.
- Deployments using release or contract hash gates should update expected
  hashes from the v1.1.14 release manifest (the semantic contract carries
  two Class B wording clarifications: section 2.1 diagnostic-vocabulary
  widening; section 5.7 holdover "must not decrease").

### v1.1.13 Integration Notes

- New adapter-authoring entry point: `adapters/AUTHORING.md` (orientation,
  input floor, layer choice, the anti-fabrication non-negotiables, the
  validation command ladder, the fixture-key reference, and review-proven
  AI-agent failure modes), a worked exercise adapter at
  `adapters/ingress/example-vendor/`, and `tools/check_adapter.py` — a
  one-command wrapper for the tool-based ladder steps that fails on empty
  input instead of passing vacuously.
- The adapter harness can now pin refusal: `expect.event_count` asserts
  exactly how many events a fixture callable returns, and `event_count: 0`
  machine-checks fail-closed behavior. The must-pass corpus grows 11 -> 15
  with one refusal fixture per schema-required RF input field; new adapters
  should ship refusal fixtures the same way.
- New worked EO full chain in `examples/zmeta-eo-chain-examples.jsonl`
  (strict example corpus 47 -> 51) mirroring the eo-cv reference adapter's
  dialect (`claim.bbox` corner format, `translate:` lineage transform).
- Structured intake is live: GitHub issue templates for adapter-authoring
  friction, semantic ambiguity, and deployment field reports (labeled
  `adapter-authoring`, `semantic-ambiguity`, `field-telemetry`), plus a PR
  template carrying the change-class/validation checklist.
- `tools/check_compat.py` gains the `v1.1.13` target; CI and
  `tools/check_adapter.py`'s manifest-derived default re-baseline to it.
- Deployments using release or contract hash gates should update expected
  hashes from the v1.1.13 release manifest.

### v1.1.12 Integration Notes

- Reference ingress adapters no longer fabricate `lineage.based_on`:
  observation and system outputs omit `lineage` unless the caller supplies
  real parent event ids (`based_on=[...]`), and mandatory-lineage events
  refuse to emit instead of inventing parents (the MAVLink state translator
  requires `based_on` or `source_zmeta_event_id`; the eo-cv inference
  translator requires `parent_event_ids` or a schema-valid UUIDv7
  `source_event_id`). Integrations that assumed lineage presence on these
  outputs were consuming fabricated ids; pass real provenance instead.
- The reference gateway now survives oversize outgoing UDP payloads: the
  datagram is dropped with an explicit `send_failure` metric/diagnostic
  instead of terminating the process. Nothing is truncated or retried.
- Extension-registry status promotion now has an evidence bar (two or more
  independent implementations plus a documented semantic-contract Section
  2.6 failure condition); candidate-level evidence and promotion tripwires
  live in `spec/future-branch-roadmap.yaml`.
- Mapping packs are declarative descriptions plus test evidence; no runtime
  engine executes `mapping.yaml` — see `adapters/mapping-packs/README.md`.

### v1.1.11 Integration Notes

- New advisory adoption guidance (non-normative, no validation changes):
  `docs/zmeta_mqtt_binding_guidance.md` (topic shape, retain/tombstone honesty,
  command traffic over MQTT), `docs/zmeta_vocabulary_crosswalk.md` (mapping
  common deployment concepts onto the locked vocabulary), and
  `docs/zmeta_correlation_pattern.md` (cross-sensor correlation with existing
  vocabulary — fusion identity, ASSOCIATION bonds, and the proposed
  `correlation_hint` extension), with runnable examples in
  `examples/zmeta-correlation-pattern-examples.jsonl`.
- The extension registry gains `CORRELATION_HINT` (proposed),
  `DATA_REF_MEDIA_METADATA` (proposed), `AGGREGATE_STATE_SNAPSHOT`
  (reserved), and `PAYLOAD_SCHEMA_URI` (rejected). Registry entries do not
  make new vocabulary valid; reserved/proposed/rejected concepts remain
  invalid under v1.0 and v1.1.0.
- Carried forward from v1.1.10: producers that emitted altitude on a `COMMAND_EVENT` under any contract
  section 7.8 field name, or that nested raw observation fields
  (`features`, `modality`, `measurement`, `t_start`/`t_end`,
  `data_ref`/`data_refs`, ...) inside a `STATE_EVENT` payload, were already
  violating the contract and are now rejected: the reference enforcement
  recurses to any nesting depth and normalizes whitespace-/case-padded key
  names. Move altitude out of commands (the receiving autonomy owns vertical
  deconfliction) and keep STATE projections raw-free, using
  `lineage.based_on` for traceability.
- The Kraken and Moth reference adapters now default
  `quality.calibration_state` to `UNCALIBRATED`. Pass
  `calibration_state="CALIBRATED"` (or `"DEGRADED"`) explicitly only when the
  deployment can substantiate it.
- Deployments using release or contract hash gates should update expected
  hashes from the current release manifest
  (`release/zmeta-release-manifest.yaml` at the pinned tag).
- Downstream clone users should pin to a tagged release and integrate through
  adapters, policy/config, profiles, and namespaced extensions. Local changes to
  core schema, event vocabulary, version dispatch, risk semantics, projection
  behavior, or command authority create a private dialect unless governed and
  versioned. See `AGENTS.md` and `docs/zmeta_change_governance.md`.
- Custom CoT/JREAP/MAVLink and other external-track ingress adapters that emit
  authoritative `STATE_EVENT` output must attach valid
  `payload.extensions.external_promotion` metadata and a `promote:*` lineage
  transform, or the reference producer-authority policy rejects the event.
- `external_promotion.trust_ref` is a policy reference used for promotion
  adjudication. It is not a signature, credential, or standalone proof of
  authenticity.
- Adapter callers that previously consumed Moth tunnel/replay bearings or
  MAVLink headings as canonical must now pass explicit
  `bearing_frame="TRUE_NORTH"` or `heading_frame="TRUE_NORTH"` only when
  deployment configuration actually guarantees that frame. Otherwise those
  native values remain in explicitly named non-canonical fields. Kraken emits
  no canonical bearing without platform heading compensation, and the Kraken
  CSV path no longer fabricates `quality.snr_db` from RSSI.
- `bearing.frame`, `quality.bearing_frame`, and `quality.heading_source` are
  producer assertions and provenance. They make frame handling auditable and
  catch unsupported labels, but they are not a signature, credential, sensor
  calibration proof, or independent verification that the producer's
  `TRUE_NORTH` assertion is correct.
- Downstream consumers must honor `allowed_uses`, `prohibited_uses`, and
  `policy_decision` labels, or run an equivalent filter such as
  `tools/filter_risk.py`; a validated degraded or quarantined event is not clean
  for fusion, state update, command basis, or autonomy by default.
- Use `python tools/lint_policy_risk_modes.py` before deployment to catch
  material risk checks configured to `ignore`.
