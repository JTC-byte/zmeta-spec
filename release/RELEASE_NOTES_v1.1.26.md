# ZMeta v1.1.26 Release Notes

## Summary

This release carries five units of work since v1.1.25. The reference CoT
egress adapter gains a `cds` profile, the shape one partner's cross-domain
guard passed into a higher enclave on 2026-09-29, selectable by name. Three
changes a downstream ecosystem's research pass asked for land in the same
adapter and the reference gateway: a track's class becomes its CoT type only
when it parses as one; the gateway's own diagnostic identity is a setting;
and the gateway's outgoing self-check no longer destroys its own diagnostics
on the 1.1.0 lane. The integration line's held content ships with them: two
experimental 1.1.0 acoustic markers and a linear-pressure level form minted
from a live hydrophone, the validation guidance system with the F1
field-evidence adjudications, the ontology reference and its generated
figure system, the branching rule, and the open-specification notice set.

The locked kernel's anchored surfaces do not move: the semantic contract
file and the v1.0 schema are byte-identical to v1.1.25, pinned by their own
guards, and the policy pack is unchanged. Governed artifacts changed,
relative to v1.1.25, as the release manifest classifies them:
`schema/zmeta-event-1.1.0.schema.json` and `spec/extension-registry.yaml`.
The registry's Markdown, the field dictionary, the future-branch roadmap
(future-only, not current vocabulary) and the advisory `schema/README.md`
changed with them.

## The CoT egress: the cds profile

`cot_config["profile"]` selects `standard`, the adapter's own output,
unchanged and pinned by a test that freezes its bytes, or `cds`: the
standard projection reduced to the four detail children `contact`, `track`,
`remarks` and `precisionlocation`, with `how` required as a deployment
claim, `remarks` replaced by one fixed-template line of at most 200
characters whose honesty markers (`affiliation not asserted`, the
confidence, `2-D fix, altitude not asserted` for a declared 2-D geo) always
survive the cut, no http(s) link anywhere in the event, point attributes in
plain decimal notation, and `stale` set to the projection time plus a fixed
window of 120 s unless the deployment sets `stale_window_s`. An event older
than `max_age_s` at projection (default: the window), or whose type asserts
an affiliation, is refused rather than sent, and the uncertainty-circle
wrapper refuses under the profile. The reference gateway validates the
profile when it reads `cot.config` and exits on one it cannot run, so a
`cds` config without a `how` token stops the gateway at startup.

What the evidence is: one deployment, one partner's guard, one day. The
deployment reported that under an earlier shape the partner saw its tracks
on the partner's federation hub and the guard did not pass them, and that
after a fixed stale window and the link rule went live together the guard
passed everything; neither change was tested alone, so the profile carries
both under one name. Nothing in this release claims that another guard
passes this shape. Doctrine log cycle F3 records the tensions: a redaction
done by an adapter (contract 18.3), the 2-D declaration carried as words,
`stale` as a fixed window against contract section 14's rule that a
projection preserves `valid_for_ms` as stale behavior (open with the
maintainer), `how` as a deployment claim, the n=1 evidence bar, and the
refusal of asserted affiliations. The export audit metadata of contract
18.3 is not in the packet and remains future vocabulary.

## The CoT egress: class and type

`payload.class` is a free string in both schema versions, and a producer may
carry an entity label there. The adapter had used any class verbatim as the
CoT `type`, so a label reached TAK as an invalid type. A class that parses as
a CoT atom type is used unchanged; any other class goes out as `a-u-G`, which
claims no affiliation, with the label in `remarks` as one quoted token. A
configured `default_type` is held to the same grammar.

## The reference gateway

- **Diagnostic identity is a setting.** The producer name and node role the
  gateway stamps on the diagnostics it mints are `gateway_producer` and
  `gateway_node_role`, with the historical `zmeta-gateway` and `GATEWAY` as
  defaults, so a gateway deployed as an admission boundary can name itself
  on its own evidence. A configured identity is checked against the loaded
  policy at startup.
- **Diagnostics survive the 1.1.0 lane.** Every diagnostic the gateway mints
  is stamped `zmeta_version: "1.0"`. Its outgoing self-check had validated
  that diagnostic against the schema the gateway was launched with, so on
  the 1.1.0 lane every refusal reached the wire content-free and every
  warning on an accepted event reached it as a refusal. The self-check now
  validates a minted diagnostic against the schema its own declared version
  selects (contract 2.4) and a forwarded producer event against the lane;
  the gateway exits at startup if the schema its diagnostics declare is
  missing. The TV-09 pins run on the v1.0 lane, the 1.1.0 lane and the
  dispatching schema.

## The 1.1.0 acoustic lane (experimental)

`features.level_reference` (SPL_RE_20UPA, SPL_RE_1UPA, DBFS, DB_RELATIVE)
and `timing_quality.est_error_basis` (MEASURED, DECLARED_BOUND,
CONVENTION_DEFAULT, UNRESOLVED) join the 1.1.0 lane as experimental
registry entries ACOUSTIC_LEVEL_REFERENCE and TIMING_ERROR_BASIS, minted
from a live hydrophone capture whose honest form validated only by
laundering dBFS into `spl_db`. The ACOUSTIC arm accepts a level in either of
two forms, `spl_db` or `pressure_pa` with `pressure_statistic`, so a domain
that publishes calibrated pressure can emit without manufacturing a decibel
(registry ACOUSTIC_PRESSURE_LEVEL, experimental). Every shipped 1.1.0 event
stays valid; the promotion bar is stated as not met for every entry; the
locked v1.0 schema is byte-identical and rejects the new keys by its own
closure. The reference launcher gains `--schema-path` so the documented
path can run the 1.1.0 lane or select by version.

## Validation guidance, the ontology reference, and the repository's terms

`tools/validation_guidance.yaml` carries advisory remediation text for every
violation code, printed by `tools/validate.py` under each violation; verdict
output is identical with guidance on and off, by test. Doctrine cycle F1
records the field-evidence adjudications behind it. `docs/zmeta_ontology_reference.md`
is a status-marked map of every concept in the standard with nine
data-driven figures generated from the manifests. The branching rule is in
`docs/zmeta_change_governance.md`. A root `NOTICE`, `CITATION.cff` and the
README's opening paragraph state the open-specification terms.

## Compatibility

No v1.0 wire changes: every event that validated before validates now, and
the semantic contract hash for the default v1.0 lane is unchanged. The 1.1.0
lane is additive on the experimental branch, with one relaxation (the
ACOUSTIC level may take either form). Two adapter and gateway behaviors
change for existing deployments: a producer that stores a label in
`payload.class` now reaches TAK as `a-u-G` with the label in `remarks`
rather than as an invalid type, and a consumer of a gateway on the 1.1.0
lane now receives the gateway's v1.0 diagnostics beside 1.1.0 events, so it
selects each event's schema by `zmeta_version`, as the dispatching schema
does. New gateway settings are optional and default to the previous
behavior. `tools/check_compat.py` accepts `--target v1.1.26`.

## Signing

Signed release. The release authority, Justin Carr (Incept.IO), directed
this signed cut on 2026-09-29 with the Incept.IO ZMeta release signing key
`A3B150AF2A0E1CA413C4B7F112BE81F54654B96E`. Verify the assets against
`SHA256SUMS_v1.1.26.txt` and its detached signature:

```
sha256sum -c SHA256SUMS_v1.1.26.txt
gpg --import ZMETA_RELEASE_SIGNING_KEY_v1.1.26.asc
gpg --verify SHA256SUMS_v1.1.26.txt.asc SHA256SUMS_v1.1.26.txt
```

The public key ships in the repository as
`release/ZMETA_RELEASE_SIGNING_KEY_v1.1.26.asc` (the same key, v1.1.2 through
v1.1.4 and v1.1.23 onward).
