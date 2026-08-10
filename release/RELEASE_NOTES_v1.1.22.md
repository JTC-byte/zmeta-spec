# ZMeta v1.1.22 Release Notes

## Summary

This release fixes an altitude-datum defect in the MAVLink ingress and corrects
three places where the stack claimed more than its evidence supported. The
locked kernel does not move: `schema/*.json`, `policy/*.yaml` and
`spec/semantics-contract.md` are byte-identical to v1.1.21. The only governed
artifact that changed is the conformance corpus, which gained twelve negative
vectors.

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

Doctrine cycle C1 opens with eleven entries, five of them minted or decided
here and six left open with their evidence, including covariance for fusion
uncertainty and float-width canonicalization as decision-due.

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

## Verification

Full battery: 1756 passed, 2 skipped, 1105 subtests passed.

Kernel gates exit 0:
`python tools/validate_conformance.py --strict --profile-projection
--extension-registry --conformance-classes --encoding-negative
--precision-policy --release-manifest --release-package --bad-events
--adapter-harness`

Examples 51/51 under `--strict --require-all`. Roadmap validator ok at 19
candidates. Conformance corpus at pass=20 fail=39.

The MAVLink change was verified end to end rather than at the unit boundary: a
2-D event projected through CoT egress emits `hae="9999999.0"`, the documented
unknown-altitude sentinel, rather than a fabricated zero, and the
`VERTICAL_UNAVAILABLE` token travels in the detail.

## Integration notes

One behavior change, scoped to MAVLink ingress. A deployment whose bridge
supplies only `GLOBAL_POSITION_INT.alt` moves from a 3-D position stamped `1.0`
to a declared 2-D position stamped `1.1.0`. The horizontal fix is unchanged. To
keep a canonical vertical, supply `GPS_RAW_INT.alt_ellipsoid`.

An unparseable `event.ts` now produces one additional warn-only metrics record.
Forwarding behavior is unchanged; the check never rejects an event.

No schema, policy or wire changes. An implementation already passing v1.1.21
conformance passes v1.1.22 unless it accepted a malformed timestamp on the
v1.1.0 lane, which the schema already rejected.

## Checksums

`SHA256SUMS_v1.1.22.txt` accompanies this release. Checksums only, per the
recorded signing decision.
