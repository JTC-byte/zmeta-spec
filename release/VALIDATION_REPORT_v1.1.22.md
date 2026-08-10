# ZMeta v1.1.22 Validation Report

## Scope

What this report covers: the reference implementation, the conformance
corpora, the governed artifacts, and the release packaging for v1.1.22, as
validated on the working tree at the cut.

What it does not cover: any claim about the fielded behavior of downstream
stacks, and any live exercise of the command path. Those remain gated on the
SITL exercise recorded in `docs/zmeta_live_test_checklist.md`.

## Validation executed at the cut (2026-08-10, local)

Full test battery:
`python -m pytest -q`
Result: 1787 passed, 2 skipped, 1105 subtests passed.

Kernel protection gates:
`python tools/validate_conformance.py --kernel-gate`
(the single named form of the full gate, introduced this release; an
equivalence test pins it to the historical ten-flag invocation)
Result: exit 0. Projection conformance 37, extension registry 63 entries,
conformance classes 34 with 2 claims, encoding negative 50, profile precision
policy 41, bad-event corpus 34, adapter conformance 53, core conformance
pass=21 fail=42.

Examples:
`python tools/validate_examples.py --strict --require-all`
Result: overall total=51 passed=51 failed=0 warnings=0.

Roadmap:
`python tools/validate_future_roadmap.py`
Result: ok, candidates=19, rejected_or_deferred=3.

Contract hash:
`python tools/compute_contract_hash.py`
Result: schema, policy, semantics and combined contract hashes computed. The
kernel inputs are byte-identical to v1.1.21, which is the expected outcome for
a release that changes no schema, policy or contract file.

## Verification method statement

Three claims in this release are about the absence of a behavior, and absence
is the class this project has repeatedly failed to verify by reading code. Each
was therefore demonstrated against the shipped modules rather than asserted
from the source:

- The gateway's unparseable-timestamp arm was exercised directly, confirming
  that `garbageZ` and a bare `Z` previously produced zero warnings while a
  well-formed out-of-horizon value produced one. The fix is pinned by tests
  covering eight values.
- The vacuous format checker was confirmed empirically:
  `'date-time' in FormatChecker().checkers` is `False` and
  `FormatChecker().conforms('garbageZ', 'date-time')` returns `True` on this
  stack. A repository-wide search established that `date-time` is the only
  format assertion in the ZMeta schemas, which is what makes removal
  behavior-neutral rather than merely harmless.
- Each of the twelve new conformance vectors was validated in isolation against
  the v1.1.0 schema to confirm it fails at exactly one path, `event/ts`, from
  exactly one keyword, `pattern`, so no vector passes for a second reason.

The MAVLink datum fix was verified through the full ingest-to-egress path
rather than at the translator boundary. A decoder that mislabels a datum
defeats a translator-only guard, so the pin runs through both halves as a
deployment does, and the resulting 2-D event was projected through CoT egress
to confirm it emits the documented unknown-altitude sentinel rather than a
fabricated zero.

The class sweep that followed was verified rather than trusted: each of the
twelve surface audits produced findings with file-and-line evidence, and
every finding was then adversarially checked by three independent verifiers
with distinct lenses (does the source format define the field as the claimed
datum; does the value reach the claimed destination on a traced code path,
executed where practical; does any existing test, validator, policy rule or
gateway check already catch it). A finding needed at least two of three
confirmations to enter the fix wave: 20 of 21 did, and the one refutation
was accepted and recorded rather than fixed, because its refuting lenses
showed the claimed value is rejected by schema validation before any datum
gate, which removes it from the class. Each fix carries per-surface
regression tests, including a CoT egress-to-ingress round trip across the
wire format for the declared-2D case.

## Known limits of this validation

The locked v1.0 lane still accepts any string ending in `Z` as `event.ts`. This
is deliberate and adjudicated under doctrine X1-01: narrowing it would move the
lock hash anchor. The residual is now disclosed in `schema/README.md` and
warned at runtime rather than passing silently, but it is not closed at the
schema layer and will not be.

The conformance corpus gains timestamp-shape coverage on the v1.1.0 lane only,
for the same reason. An independent implementation validating v1.0 traffic
receives no corpus signal on timestamp shape, because there is no shape to
enforce there.

The altitude-datum sweep covered every adapter surface in this repository,
and its scope boundary is the repository: a downstream decoder feeding the
KLV or JREAP templates, or a caller wiring positions into the sensor_geo
interfaces, can still mislabel a datum upstream of the boundary these fixes
name. The documentation on each surface now states the caller's obligation,
which is the strongest guard available without executing the caller. The
sweep's non-altitude secondary observations (the same laundered-plausible-
value shape on headings, power references, and course-vs-heading) are
recorded and triaged in the backlog, deliberately unfixed here because the
wave's charter was the altitude class.

Cross-encoding equality is verified as object and value equality, not as byte
identity. Two conforming CBOR backends in this repository emit different bytes
for the same event, which is recorded as doctrine C1-07 and is decision-due.
No feature in this release depends on byte identity.

## Signing decision

Checksums only, consistent with the recorded decision for prior releases.
`SHA256SUMS_v1.1.22.txt` is generated and verified in both directions.
Detached signatures are generated only under an approved signing key and
process, which is a maintainer action and was not performed here.
