# ZMeta v1.1.22 Release Notes

## Summary

This release fixes an altitude-datum defect in the MAVLink ingress, sweeps the
same defect class across every other adapter surface and fixes what the sweep
confirmed, corrects three places where the stack claimed more than its
evidence supported, and lands the no-decision fixes from an apparatus-wide
audit of the check and governance machinery. The locked kernel does not move:
`schema/*.json`, `policy/*.yaml` and `spec/semantics-contract.md` are
byte-identical to v1.1.21. Three governed artifacts changed: the core
conformance corpus gained twelve negative timestamp vectors and the four
A1-02 dimensionality vectors, and the adapter-harness fixtures moved to the
datum-qualified altitude keys the swept adapters now require.

The work was seeded by an independent technical review comparing ZMeta against
CoT, MISB ST 0601, STANAG 4676, OGC/ISO OMS, W3C PROV, Sparkplug B, MAVLink,
ASTERIX, C2PA and CloudEvents. Most of what shipped here is not what that
review found. It is what verifying the review's claims against the tree turned
up, which is recorded as doctrine cycle C1.

## The altitude datum: MSL is not HAE

The MAVLink ingress template published `GLOBAL_POSITION_INT.alt`, which MAVLink
defines as height above mean sea level, into `payload.geo.alt_m`, which
semantic contract 6.2 reserves for Height Above Ellipsoid. The template's own
docstring described the input as "metres AMSL" and wrote it unconverted. No
geoid model ships here, so contract 6.2's two lawful options were convert or
omit canonical geo, and neither was taken.

The two datums are now separated at the decode boundary.
`GLOBAL_POSITION_INT.alt` decodes to `alt_msl_m` and can never reach canonical
geo. `GPS_RAW_INT.alt_ellipsoid`, which MAVLink defines as height above the
WGS-84 ellipsoid, decodes to `alt_hae_m` and is the only value admitted to
`payload.geo.alt_m`. When a bridge supplies both, HAE wins.

When only MSL is available the horizontal fix is still real, so the position is
published as the declared 2-D form of doctrine A1-02: `geo.dimensionality:
"2D"`, no `alt_m`, `quality.geo_status: VERTICAL_UNAVAILABLE`, under a forced
`zmeta_version: "1.1.0"` stamp, with the reported value preserved as
non-canonical `quality.mavlink_alt_msl_m`. The legacy `alt_m` input key is read
as MSL, so an existing caller degrades to the honest form rather than
continuing to publish a wrong-datum claim.

This was the third appearance of the class. The July 2026 audit found it in a
fielded stack, the ADS-B ingress was then hardened to refuse it at the source
and says so on its face, and this template carried the identical defect
unfixed in the same repository. The occurrence rule forced a terminal status
on sight.

The general lesson is recorded because it is reusable: every anti-fabrication
guard in this stack keys on absence, and a wrong-datum value is present,
finite, in range and plausible, so it passes all of them. Naming the datum at
the ingest boundary is the guard that works.

## The class, swept

A fix proves its instance; it does not prove the class is gone. The MAVLink
defect was the third appearance of this class, so the remaining twelve adapter
surfaces (ingress, egress, command, and projector) were swept against the same
standard, with every finding adversarially verified through three independent
lenses: does the source format define the field as the claimed datum, does the
value actually reach the claimed destination, and does any existing guard
already catch it. The sweep produced 21 findings; 20 were confirmed by at
least two of three lenses and fixed here, 1 was refuted (the claimed value is
schema-invalid before any datum gate, which removes it from a class whose
danger is that its values pass schema validation). Doctrine entry C1-12
carries the full record.

The confirmed defects, all fixed to the same boundary-naming pattern:

- **KLV ingress** read a generic decoded `alt_m` straight into canonical
  `alt_m`, while MISB ST 0601's dominant altitude tags (15, 25, 42) are MSL.
  The decode boundary now names the datum: only `alt_hae_m` (Tags 75/78)
  reaches canonical geo; MSL and legacy unqualified values degrade to the
  declared 2-D form with the vertical preserved under `quality.klv_alt_msl_m`
  or `quality.klv_alt_unspecified_datum_m`. The README carries the tag-to-key
  table and names the sensor-position referent.
- **JREAP ingress** carried the pre-fix legacy-key fallback: `alt_m` from the
  decoded track dict, unconverted, in a domain where native track altitudes
  are typically barometric or MSL. The fallback now degrades to 2-D with the
  value preserved as `quality.jreap_alt_unlabeled_datum_m`, and the README
  states the HAE obligation on `hae_m`.
- **CoT ingress** promoted `point@hae = 9999999.0`, CoT's documented
  unknown-altitude convention and the exact sentinel this repository's own
  egress emits, as a real nine-million-metre HAE claim (`alt_m` is unbounded
  in the locked schema, so nothing downstream refused it). The sentinel now
  degrades to 2-D, the egress sibling's `<geo_dimensionality>` detail marker
  is read so a declared-2D track round-trips, and a "2D" marker beside a real
  altitude refuses as the coherence contradiction it is.
- **bladerf** mapped `sensor_alt_m`, a datum-unverified UAS-telemetry
  altitude, to canonical geo, and its own test pinned the pass-through. A
  real fix now emits the declared 2-D form with the native value under
  `features.native_sensor_alt_m` (the same demotion its frame-unlabeled
  bearing already got), and only a deployment-asserted `sensor_alt_hae_m`
  regains 3-D. The mapping pack documents the disposition.
- **EO-CV** laundered its documented flight-controller fallback: `sensor_geo`
  is described as an FC GPS position, whose global-position altitude MAVLink
  defines as MSL, and it flowed wholesale into `claim.geo`. Both the FC
  fallback and the detection's datum-free `altitude` key now degrade to 2-D
  with the values preserved under datum-named quality keys; `alt_hae_m` and
  `altitude_hae_m` are the canonical paths. Geo is also built field-by-field,
  so extra caller keys no longer ride into the claim.
- **moth and kraken** accepted caller sensor positions with no datum
  obligation stated anywhere on their surfaces, in adapters that already
  demand frame evidence for a bearing before making a canonical claim. The
  vertical now gets the same rule on every translate path: `alt_hae_m` or the
  2-D degrade.
- **MAVLink command egress** deep-copied `risk_adjudication` records into the
  MissionIntent output under `allow_flagged=True` without the altitude walk,
  so an altitude key inside a record could exit despite contract 7.8's
  whole-payload prohibition. The walk now covers the whole built mission.
- **SAPIENT ingress** emitted an `omitted_reason` tag (`UNITS_UNSPECIFIED`)
  that its own mapping-pack documentation spelled
  `COORDINATE_SYSTEM_UNSPECIFIED`, so a consumer filtering on the documented
  tag never matched. The code now emits the documented tag, pinned.
- **The teaching surfaces** taught the defect: the example-vendor exemplar's
  input key was literally `alt_m`, mapped to canonical on name similarity;
  the authoring guide's residue-class checklist omitted the
  wrong-datum-through-a-plausible-value shape; the template README stated
  "meters HAE" as an output property with no ingest-side rule. The exemplar's
  key is now `alt_hae_m` across the pack and adapter, AUTHORING.md carries a
  fifth residue class naming the lesson, and the template README states the
  decode-boundary obligation.

Two surfaces came back clean with evidence: signalhunter (emits no altitude
anywhere, by explicit refusal) and the SAPIENT location path (datum-aware in
both directions, with the command-egress altitude guard verified to fire
rather than assumed).

## Three claims the evidence did not support

**The v1.1.20 notes credited a runtime layer that no-ops.** They stated the
X1-01 closure landed "at both lawful layers", with a gateway window counting an
implausible `ts` on every `zmeta_version`. The window returned before comparing
anything when the timestamp could not be parsed, which is exactly the malformed
class the locked v1.0 lane still admits, so a v1.0 event carrying
`ts="garbageZ"` passed schema validation clean and produced no runtime signal
at all. The gateway now records its existing `EVENT_TS_IMPLAUSIBLE` warning
with `direction: "unparseable"` and no delta. No new violation code was minted;
the occurrence rule reserves governed vocabulary for a third instance, and an
unparseable timestamp is honestly implausible. The published v1.1.20 notes are
not rewritten. The correction is in `docs/release_notes_errata.md`.

**The conformance corpora carried no malformed-timestamp vectors.** Every
record in both must-fail corpora was parsed against the v1.1.0 structural
pattern and exactly one had a non-conforming `event.ts`, the UTC-offset form
that even the weak `Z$` pattern rejects, while the contract-to-stack crosswalk
marked the requirement "Enforced" and cited that corpus as its evidence.
Twelve v1.1.0-stamped vectors were added covering a garbage string, a bare `Z`,
an out-of-range year, an impossible month and an impossible hour among others.
No v1.0-stamped equivalents were added, because the locked schema deliberately
accepts them and a fixture asserting otherwise would misstate the lane;
`conformance/README.md` records that asymmetry.

**A format checker validated nothing at a dozen call sites.**
`format_checker=FormatChecker()` was passed at the gateway's central validator
factory, the adapter template new adapters are copied from, and ten test
harnesses. `jsonschema` registers no `date-time` checker without a separate RFC
3339 package that this repository does not declare, and `date-time` is the only
format assertion in the ZMeta schemas, so removal is behavior-neutral and
`pattern` was and remains the gate.

## Records, roadmap, and tooling

Doctrine cycle C1 closes this release at twelve entries, five of them minted
or decided here and seven left open with their evidence, including covariance
for fusion uncertainty and float-width canonicalization as decision-due.
C1-12 records the class-sweep lesson itself: the apparatus verified that each
fix was done, and nothing verified a fix was done everywhere it applied,
which is why this class needed three appearances before a sweep ran.

The doctrine log now opens with a "How to read this log" section, the C1-09
remedy: entries are point-in-time records, the status marker on a heading is
the authoritative current state, and reading the open entries as a defect
inventory systematically overstates what is broken. Two external reviews in
ten days made exactly that misreading.

The vocabulary crosswalk gained a W3C PROV section, asked for by both of
those reviews: `lineage.based_on[]` to `prov:wasDerivedFrom`,
`lineage.transform` to a `prov:Activity` label, with the non-goals stated.

Cooperative-mesh gap detection gained its own roadmap candidate. Sequence
counters had been booked only under adversarial mesh trust, whose tripwire
fires on a trust boundary, so a cooperating node losing events on a degraded
link had no roadmap home and never would have. The repository already measures
the consequence in the two-node quickstart.

`tools/validate_future_roadmap.py` is back in the gate battery. It existed from
v1.1.13 and was dropped from the per-release command set at v1.1.16, so the
governed artifact that records what ZMeta has deliberately not built was the
one surface no gate read.

The ADS-B adapter's `ImportError` fallback no longer aliases `uuid4` to the
name `uuid7`; it raises with a message naming the RFC 9562 requirement.

Four current-facing documents stopped under-disclosing: the schema README now
splits the two branches on timestamp enforcement, the README and professional
overview carry the qualifier the normative documents attach to cross-encoding
equality, the field dictionary documents `geo.dimensionality`, and the CoT
egress README no longer suggests that installing a format checker closes a gap
it cannot close. Each of these invited a specific misreading in the external
review, which is the evidence they were unclear rather than merely terse.

## Apparatus hardening

An audit of the verification and governance apparatus itself (114 items,
each answering what it guards, whether it is the sole guard, whether an
adopter needs it, and what retires it, argued against a documented record of
twenty real catches) found the check inventory sound and the growth
mechanics broken. The fixes that needed no maintainer decision land here:

- The full kernel protection gate has one named form,
  `python tools/validate_conformance.py --kernel-gate`. The flag list lives
  in one place in the tool, an equivalence test pins the alias to the
  historical ten-flag invocation, and the current-facing documents now
  quote the alias, so the gate's definition stops being a hand-copied
  moving fact. Frozen process records keep the historical command verbatim.
- The conformance corpus now covers declared-2D geo (doctrine A1-02): a
  must-pass vector generated through the real AIS adapter, and three
  must-fail vectors pinning the coherence arms. An independent
  implementation can now verify the feature from the corpus alone, which
  it previously could not.
- The release tooling closes the two traps behind this release's own
  packaging defect: the documented package build names
  `--release-state formal_release`, a test refuses a built package whose
  self-description disagrees with the manifest, and the checksum step
  refuses a package zip staler than its package directory rather than
  silently checksumming it.
- Smaller alignments: the Makefile packet-size target matches CI's flag
  form, the docs index is complete again (its process-records section is
  machine-parsed and freezes what it lists), the records-currency guard
  ignores the gitignored private-records folder, and the audit playbook's
  never-fired one-third introduction cap is reclassified to a written
  backstop per its own watch item.

The audit's remaining output is maintainer decisions, recorded on the
backlog, not code.

## Verification

Full battery: 1787 passed, 2 skipped, 1105 subtests passed.

Kernel gates exit 0:
`python tools/validate_conformance.py --strict --profile-projection
--extension-registry --conformance-classes --encoding-negative
--precision-policy --release-manifest --release-package --bad-events
--adapter-harness`

Examples 51/51 under `--strict --require-all`. Roadmap validator ok at 19
candidates. Conformance corpus at pass=21 fail=42.

The MAVLink change was verified end to end rather than at the unit boundary: a
2-D event projected through CoT egress emits `hae="9999999.0"`, the documented
unknown-altitude sentinel, rather than a fabricated zero, and the
`VERTICAL_UNAVAILABLE` token travels in the detail.

The sweep fixes carry per-surface regression tests, including the mirror of
that path: CoT XML carrying the sentinel and the `<geo_dimensionality>`
marker is re-promoted as a declared 2-D track rather than a nine-million-
metre altitude claim, pinned across the actual wire format.

## Integration notes

The behavior changes share one shape, on every swept surface: an altitude the
adapter cannot prove is WGS-84 HAE no longer becomes canonical `alt_m`. A
deployment feeding a legacy or datum-unqualified altitude key moves from a
3-D position stamped `1.0` to a declared 2-D position stamped `1.1.0`, with
the horizontal fix unchanged and the reported vertical preserved under a
datum-named non-canonical key. To keep a canonical vertical, supply the
datum-qualified key: `GPS_RAW_INT.alt_ellipsoid` (MAVLink), `alt_hae_m` (KLV
decoded dicts, JREAP via `hae_m`, moth/kraken/eo-cv `sensor_geo`, the
example-vendor input), `altitude_hae_m` (EO-CV detections), or
`sensor_alt_hae_m` (bladerf).

Three sharper edges. The CoT ingress now refuses a `<geo_dimensionality
value="2D">` marker beside a real `point@hae` (the coherence contradiction)
and degrades the 9999999.0 unknown-altitude sentinel instead of promoting it
as a real altitude. The MAVLink command egress raises on an altitude key
inside a `risk_adjudication` record even under `allow_flagged=True`, where it
previously projected it. The SAPIENT ingress `omitted_reason` tag for an
unspecified coordinate system is now the documented
`COORDINATE_SYSTEM_UNSPECIFIED` string; a consumer that matched on the old
undocumented `UNITS_UNSPECIFIED` spelling should update.

An unparseable `event.ts` now produces one additional warn-only metrics record.
Forwarding behavior is unchanged; the check never rejects an event.

No schema, policy or wire changes. An implementation already passing v1.1.21
conformance passes v1.1.22 unless it accepted a malformed timestamp on the
v1.1.0 lane, which the schema already rejected, or it fed a datum-unqualified
altitude to a swept adapter, which now degrades honestly instead of
publishing it.

## Checksums

`SHA256SUMS_v1.1.22.txt` accompanies this release. Checksums only, per the
recorded signing decision.
