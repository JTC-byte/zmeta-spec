# ZMeta v1.1.27 Release Notes

## Summary

This release carries sixteen merges on `develop` since v1.1.26, cut whole on
2026-10-27. The semantic contract gains the definition of `last_seen_ts` on
a FUSION_EVENT, a field section 7.6 listed and no text defined, and its
section 22 class table names the conformance manifest's gateway class. The
reference CoT egress is hardened on four counts, the reference gateway's
shipped edge configs stop enabling failure modes the gateway never read, a
strict command posture ships as two opt-in policy variants with a tool that
assembles them, two registry waves record upstream asks without making any
vocabulary valid, and the records waves of October book the doctrine
tensions and guidance gaps for the maintainer.

The locked kernel's anchored surfaces: both schemas are byte-identical to
v1.1.26, pinned by their own guards, and the reference `policy/` directory
is unchanged. The semantic contract file changes for the first time since
v1.1.20, so the release manifest's `semantic_contract_hash` and the
reference gateway's startup `contract_hash` move with this release.
Governed artifacts changed, relative to v1.1.26, as the release manifest
classifies them: `configs/policy-variants/command-evidence.strict.yaml`,
`configs/policy-variants/routing.command-origin.yaml`,
`conformance/must-pass.jsonl`, `spec/extension-registry.yaml` and
`spec/semantics-contract.md`. The future-branch roadmap, four FUSION
examples and the conformance example claims changed with them.

## The semantic contract

- **Section 7.6 defines `last_seen_ts`**, as a contract 2.1 patch adopted on
  the maintainer's concurrence of 2026-10-27: "`last_seen_ts`: the
  `event.ts` of the latest contributing observation the fused estimate
  rests on; it is never later than the fusion's own `event.ts`." The
  sentence writes down what the reference track projector emits for
  observations arriving in `event.ts` order. Four shipped FUSION examples
  (profile-M, examples-1.0, profile-H, eo-chain) and one must-pass
  conformance vector disagreed with it and are corrected to their member
  observation's `event.ts`; the correlation example and the v1.1 example
  already agreed. The v1.0 lock-baseline anchor on the contract text moved
  with a dated note, its negative control seen failing first. No validator
  reads the relation yet; that check, with its own failing control, is
  booked in the handoff.
- **Section 22's class table names `ZMETA-GATEWAY-REFERENCE`**, the class id
  the conformance manifest defines and the claims validator accepts; a claim
  written from the old table name was refused. No semantics change.

## The reference CoT egress

- **The `cds` profile's `stale` never exceeds the event's own validity
  claim** (doctrine F3-03, on the maintainer's go of 2026-09-30): `stale` is
  the earlier of `ts` + `valid_for_ms` and the projection time plus the
  window, so the window caps a claim and never extends it. A claim that has
  lapsed at projection is refused, or sent with its past `stale` when the
  deployment sets `lapsed_validity` to `send_stale`. The gateway counts the
  profile's two refusals as `VALIDITY_LAPSED` and `AFFILIATION_ASSERTED`
  instead of `UNCONVERTIBLE`. No option passes an asserted affiliation
  (F3-05); the roadmap records the 2026-09-29 guard validation as evidence,
  n=1 (F3-04). The partner's guard has not seen the capped shape.
- **The standard profile refuses values XML cannot carry honestly**: a
  control character or lone surrogate in an identity attribute refuses the
  event (it is replaced in `remarks`); a point value must be a finite
  number, a Decimal or wholly numeric text; an output that does not parse
  to a point and a detail is refused; a non-numeric or negative accuracy
  default is a configuration error under every profile.
- **A configured `how` must have the shape of a CoT how token**; any other
  value is a configuration error under every profile, so the gateway
  refuses to start. An absent `how` is still omitted, and the adapter README
  now states that the default output is therefore not schema-valid CoT; the
  default itself stays with the maintainer (doctrine H1-05).
- **An impossible position or an unbounded name is refused rather than
  projected**: a `lat` beyond 90 degrees or a `lon` beyond 180 refuses the
  event (an exact comparison, so a Decimal or numeric text a hair past the
  bound is refused too), and a callsign or uid longer than `max_name_chars`
  (default 256, a deployment default) refuses rather than cuts.

Output for well-formed input is unchanged, byte for byte, under the
standard profile, whose frozen-bytes fixture still matches; under `cds` the
one change to well-formed output is the stale cap above.

## The reference gateway and its configs

- **The shipped edge configs carry only the failure modes the gateway
  reads.** `configs/edge-config.json` and the profile-L lean config enabled
  `observation_timeout`, `deconfliction_offline` and `fusion_instability`,
  which the gateway never read; they now carry `timing_loss` only, the
  gateway warns at startup for any other failure mode or member, and a
  test pins the shipped configs to the implemented set (doctrine E1-05).
- **A strict command posture ships as two policy variants.**
  `command-evidence.strict.yaml` requires every COMMAND_EVENT to cite its
  evidence and refuses an unresolvable citation;
  `routing.command-origin.yaml` lets the automation producers originate
  only SCAN_RF and CHANGE_SENSOR_MODE while the human-origin producer keeps
  every task type. `tools/assemble_policy_dir.py` builds a deployment policy
  directory from the reference plus the selected variants, replaces only
  the tunable files, lints the result and prints the hashes to pin. The
  reference `policy/` directory is unchanged; the manifest's policy bundle
  hash moves because the variants are manifest-listed (doctrine E1-01,
  E1-02).

## Registry and roadmap

`DIALECT_LABEL` and `SEARCH_PATTERN` are proposed; `RAW_DATA_ABSENT_STATUS`
records destroyed-with-receipt as a candidate ninth evidence state; roadmap
candidates `dialect-label` and `canonical-byte-form` open,
`raw-data-absent-evidence-status` records one deployment's crypto-shred
model as its first evidence, short of the bar, and
`event-signing-anti-replay` now depends on `canonical-byte-form`. `docs/zmeta_event_signing_design_note.md`
scopes the signing branch. The registry holds 68 entries, 11 of them
proposed; the roadmap holds 22 candidates. No entry changes status and no
vocabulary becomes valid. Doctrine U1-02 and the F3 decisions carry the
status DECIDED (delegated) until the maintainer reviews them.

## Records

The records waves since v1.1.26 book, for the maintainer, doctrine entries
E1-01 to E1-05, F4-01 to F4-04, F5-01, U1-01 and U1-02, new evidence under
H1-05, guidance gaps (a) through (af), two
reference-gateway behaviors brought forward with measurements (the command
dedupe window against contract 13.2, held as a fix on a branch, and the
unbounded validation state), and corrections to the `translate:` lineage
claim, the crosswalk's `geofence_alert` row and the adapter index. The
lesson of the 2026-10-01 answer rounds is recorded: an answer about the
standard quotes the text it rests on and is checked by an independent reader
before it is relied on.

## Compatibility

No v1.0 wire change: both schemas are byte-identical to v1.1.26 and the
reference policy pack is unchanged, so every event that validated before
validates now. A FUSION_EVENT whose `last_seen_ts` is not its latest
contributing observation's `event.ts` is out of conformance with 7.6 as now
written; no validator reads the relation yet. Four reference-adapter and
gateway behaviors change for existing deployments: the `cds` output for any
track whose remaining validity at projection is shorter than the window
(`stale` becomes the earlier of the two); the projection's refusals above,
which apply under both profiles (the position and name guards and the `how`
shape check run before the profile branch; a forbidden character in an
identity attribute, a non-numeric point value and a malformed `how` were
already refused under `cds` since v1.1.26), where a malformed `how` or
accuracy default in a config now stops the gateway at startup; the shipped
edge configs; and the
`VALIDITY_LAPSED` and `AFFILIATION_ASSERTED` counters. The manifest's
`semantic_contract_hash` and the gateway's startup `contract_hash` move; a
deployment that sets `require_contract_hash` recomputes it when it re-pins,
and a conformance claim written against v1.1.26 keeps that tag's hash until
it re-pins. `tools/check_compat.py` accepts `--target v1.1.27`.

## Signing

Signed release. The release authority, Justin Carr (Incept.IO), directed
this signed cut on 2026-10-27 with the Incept.IO ZMeta release signing key
`A3B150AF2A0E1CA413C4B7F112BE81F54654B96E`. Verify the assets against
`SHA256SUMS_v1.1.27.txt` and its detached signature:

```
sha256sum -c SHA256SUMS_v1.1.27.txt
gpg --import ZMETA_RELEASE_SIGNING_KEY_v1.1.27.asc
gpg --verify SHA256SUMS_v1.1.27.txt.asc SHA256SUMS_v1.1.27.txt
```

The public key ships in the repository as
`release/ZMETA_RELEASE_SIGNING_KEY_v1.1.27.asc` (the same key, v1.1.2 through
v1.1.4 and v1.1.23 onward).
