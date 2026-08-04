# ZMeta v1.1.20 Release Notes

Release date: 2026-08-03
Release type: audit-closure cut — a horizontal-only position becomes sayable
end to end, the v1.0 lock is restored to its adjudicated baseline, and the
release checksums are correct at source for the first time

## Summary

v1.1.20 is the largest release since the repository locked its kernel. It
closes the gaps a ten-axis readiness audit found, and it carries the first
acceptance of a ZMeta projection by an implementation nobody in this
repository wrote.

The headline is doctrine A1-02: a real position with no vertical, every AIS
vessel and every barometric-only aircraft, can now be said honestly instead
of being refused or padded. A v1.1.0 event may declare
`geo.dimensionality: "2D"` with `quality.geo_status: VERTICAL_UNAVAILABLE`,
and the whole reference stack carries the declaration: AIS and
barometric-only ADS-B ingress emit it, the track projector produces 2-D
tracks from it, and every egress adapter now knows dimensionality exists.
The maintainer's adjudication rides with the normative text: a large share
of real traffic will never have vertical data, denying good pings for data
they will never have is the wrong failure, and the label tells the operator
why the position is 2-D so the go/no-go stays theirs.

The same push restored the locked v1.0 schema to its adjudicated 2026-05-07
lockdown-audit baseline after a forensic pass proved a later release had
added vocabulary into it, fixed the release signer defect that made
published checksums wrong across fifteen tags, and survived the heaviest
review of the cycle: a whole-range fresh-eyes panel over every commit since
v1.1.19, adversarially verified, whose finding-by-finding record ships in
this tree.

Governed artifacts changed in this release, relative to zmeta-v1.1.19:
conformance/adapter-harness/must-pass.jsonl,
conformance/bad-events/must-fail.jsonl,
conformance/profile-precision/must-fail.jsonl,
conformance/profile-precision/must-pass.jsonl,
policy/producer-authority.yaml, policy/profile-precision.yaml,
schema/zmeta-event-1.1.0.schema.json, spec/compact-binary-mapping.md,
spec/extension-registry.yaml, spec/semantics-contract.md.
The locked v1.0 kernel is unchanged.

## A position with no vertical, end to end

The v1.1.0 schema gains the declared-dimensionality form: optional
`geo.dimensionality` ("2D"/"3D", absent means 3D so the existing corpus is
untouched), the `VERTICAL_UNAVAILABLE` token, and four coherence arms that
make lying about the shape a schema refusal: a 2D declaration paired with
`alt_m`, the token beside a 3-D geo, `UNAVAILABLE` beside any present geo,
and the estimated-state arm the wave-2 attack pass forced. Contract
sections 21.1 and 21.8 carry the normative text. Writers stamp
`zmeta_version: "1.1.0"` conditionally, only on events that use the form,
so the version field declares the contract each event genuinely exercises.

Every egress adapter now handles the declared 2-D form deliberately, each
within its own protocol's constraints:

- **JREAP** exports an honest `hae_m: null` for a declared 2-D geo and
  refuses the ambiguous no-token shape instead of exporting an assumed
  dimensionality.
- **SAPIENT** emits a DetectionReport without a `z` key, resting on a
  verified proto fact (the dstl Location message marks x and y mandatory
  and z optional) and confirmed on the wire by an independent Java
  harness accepting the z-less detection.
- **KLV** already carried the geo byte-for-byte and is pinned so it stays
  that way.
- **CoT** keeps the wire-required `hae` sentinel for TAK compatibility and
  pairs it with a structured `<geo_dimensionality>` detail element, so a
  consumer can tell declared-no-vertical from unknown-vertical. This
  adapter was scoped out of the original sweep; the pre-cut panel caught
  it, which is what the panel is for.

`ERROR_ELLIPSE_M` is promoted from experimental to adopted in the
extension registry, with the formal `semi_major`/`semi_minor`/
`orientation_deg` spellings. The ADS-B adapter's NACp-derived ellipse
moves to its lawful location under the conditional 1.1.0 stamp, and CoT
egress no longer fabricates zero-valued ellipse members when the source
carried none. Because an adopted extension's claims must be enforced, not
asserted, `policy/profile-precision.yaml` and the projection validators
now catch a profile projector that strips the declaration, the token, or
the ellipse, with nine fixtures pinning the thinning behavior.

## The first independent-implementation acceptance

The SAPIENT interop run sent real ADS-B-derived traffic through the full
chain — ingress, track projection, egress, wire framing — into an
independent pure-Java BSI Flex 335 v2 harness, which answered VALID. That
acceptance is the release's strongest evidence that the projection layer
speaks a dialect someone else's code recognizes, and the run also earned
its keep by finding three boundary defects, all fixed and pinned here: the
ingress vendor extension carried an observation-denylist key name
verbatim, INFERENCE_EVENTs stamped a node role policy forbids, and no
egress adapter knew dimensionality existed (the finding that became the
sweep above).

## The lock has a birth certificate, and the schema matches it

A gate-inventory pass found the locked v1.0 schema did not match the tree
the lockdown audit had adjudicated: the v1.1.0 release had added a subtype
vocabulary into it, and the historical corpus had later been edited around
the breach. The restoration removes the block, embeds the historical
record verbatim in a test that proves all three facts (the record
validates under restored v1.0, the vocabulary still binds under 1.1.0, the
block is gone), and re-pins the byte-identity anchor at the restored
bytes. The contract now carries the lock's provenance note: the 2026-05-07
lockdown audit is the lock. Moving either anchor is an on-record
adjudication by construction.

## Published checksums were wrong, and now they are not

`sign_release_artifacts.py` hashed text assets without line-ending
normalization, so a clean LF checkout of an unchanged file could fail its
published checksum. Sixteen checksum entries across fifteen published tags
were wrong; `docs/release_checksum_errata.md` is generated from the tags
themselves and records every affected entry with its corrected value.
Published files were never rewritten, consistent with the immutability
rule. The signer now normalizes before hashing, so v1.1.20's checksums are
correct at source, and `release/README.md` and the release checklist point
anyone verifying an older tag at the errata first.

## Timestamps: the structural gap is closed where it lawfully can be

`event.ts` was unconstrained beyond a trailing `Z`, recorded as a known
limit of the v1.1.19 validation. The closure lands at both lawful layers:
the v1.1.0 `utcDateTime` pattern now enforces structural calendar shape
(year 1970-2999, month 01-12, day 01-31, and so on), and the gateway gains
a warn-only plausibility window (`ts_plausibility_horizon_ms`, default 24
hours, 0 disables) that counts an implausible `ts` with direction, delta
and horizon in the details, on every `zmeta_version`. It never rejects.
The locked v1.0 schema does not gain the pattern; replayed historical
corpora trip the warning by design, so simulations should set the horizon
to 0.

## New reference components

- **AIS ingress** (`adapters/ingress/ais/`): the second cooperative-
  broadcast adapter and the total case for A1-02, since a vessel has no
  meaningful altitude ever. It refuses message 27's not-available
  sentinels as motion data, out-of-range speed and course as corruption,
  and unparseable receive times instead of borrowing another clock.
- **Track projector** (`adapters/projector/track/`): a third adapter
  category, ZMeta in and ZMeta out, closing the observation-to-track gap
  for sources whose subjects broadcast an identity. It is fusion, not
  external promotion: the operator asserts confidence, lineage cites
  members, and an unnamed producer can no longer assert an authoritative
  track (see Breaking below).
- **Simulation harnesses** (`tools/sim/`): the two-node and throughput
  reps used to validate the stack, committed behind a structural boundary
  test that fails if anything governed ever imports them.
- **Container delivery fixes**: the shipped compose files could not
  deliver events off-host (container-loopback defaults, a port
  collision); the deploy README's override path is rewritten and was
  live-tested by its own fixer.

## Command safety

- **Breaking: `policy/producer-authority.yaml` drops the
  `state-projector-*` wildcard.** It let any glob-matching producer emit
  authoritative STATE_EVENTs with no named identity and no promotion
  evidence, and no reference component used it. A deployment that relied
  on it adds a named producer stanza, the shape
  `configs/policy-variants/producer-authority.strict.yaml` already uses.
- **The MAVLink command translator fails closed on risk-flagged
  commands.** A COMMAND_EVENT carrying gateway risk-adjudication records
  refuses to translate by default; the explicit `allow_flagged` opt-in
  stamps the records into the MissionIntent, so a soft-flagged command
  cannot become a clean intent silently.
- **The gateway never emits a diagnostic its own validation refuses.**
  Reason-code legality for TASK_ACK diagnostics is derived from policy at
  every call site, so a refused command's diagnostic reaches the wire
  schema-valid, carrying the true reason code and the real
  `original_event_id`. Found by the pre-cut panel, closed as a class with
  a call-site enumeration pin.

## How this cut was reviewed

The pre-cut review ran as an independent whole-range panel: eight cold
lenses over all commits since v1.1.19 as one surface, findings
deduplicated, each surviving finding handed to an adversarial verifier
instructed to refute it, then a fix wave, then an attack pass on the fix
wave that found and fixed four defects in the fixes themselves. The
finding-by-finding record, including what was refuted and what is
deliberately deferred, ships at `docs/v1_1_20_precut_panel_register.md`
with a standalone verification command per entry. The v1.1.19 report
recorded that its pre-cut review was author-run; this one was not.

## Also in this release

- Gateway operator debuggability: violation metrics carry details instead
  of bare codes, TIME_STATUS feeds clock-health counters, CoT egress state
  is visible at startup, and truncation is counted.
- RF ingress hardening: ADS-B gains a geometric-altitude plausibility
  band and epoch floor; kraken, moth and signalhunter screen non-finite
  values (a NaN bearing flipped 180 degrees before this).
- JREAP gains the loss-notes register its siblings had, closing the
  asymmetry where it silently dropped what CoT projects and SAPIENT
  documents dropping.
- The adapter authoring guide teaches the residue classes real reviews
  keep finding, adds the broadcast-source row, and steers authors to the
  mapping-pack route the field has proven.
- The v1.1.19 Integration Notes are archived verbatim in `CHANGELOG.md`
  instead of being overwritten and lost.

## Compatibility

- `tools/check_compat.py` gains the `v1.1.20` target.
- Current-facing documents re-baseline to the v1.1.20 release manifest.
- The one breaking change is the producer-authority wildcard removal
  above. Everything else previously valid remains valid: the v1.1.0 geo
  forms are opt-in, absent-dimensionality v1.0 events behave exactly as
  before, and the new gateway timestamp window warns without rejecting.
