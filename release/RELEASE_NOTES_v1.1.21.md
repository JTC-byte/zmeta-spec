# ZMeta v1.1.21 Release Notes

Release date: 2026-08-09
Release type: governed maintenance cut — three reason codes are minted
under a diagnostic-first wire posture, the power-reference experiment
opens on the v1.1.0 branch, and the record catches up to what v1.1.20
shipped

## Summary

v1.1.21 is a small governed cut with one vocabulary decision at its
center. The reuse-vs-mint question the doctrine log had been counting
reached its forced occurrence threshold, and the maintainer adjudicated
the mint: `NON_FINITE_VALUE` and the command-evidence pair
`COMMAND_EVIDENCE_UNRESOLVED` / `COMMAND_EVIDENCE_PROHIBITED` enter the
governed diagnostic vocabulary as one Class B batch. The locked v1.0
kernel is byte-untouched: the wire posture is diagnostic-first, meaning a
v1.0-stamped diagnostic keeps its documented legacy `reason_code` and
carries the minted code in a new `metrics.diagnostic_code` member, while
the gateway's JSONL diagnostics and the 1.1.0 schema enum carry the
minted codes natively. An operator can finally filter non-finite refusals
and command-evidence refusals apart from the broad codes they used to
ride, and no fielded v1.0 consumer sees a changed `reason_code` value.

The release also opens the A1-01 experiment: `features.power_reference`
on the v1.1.0 branch lets an uncalibrated SDR declare what its
`power_dbm` number means (`DBM_ABSOLUTE`, `DBFS`, `DB_RELATIVE`), and the
ADS-B reference adapter emits either form behind an explicit flag. The
registry entry states on its face that the in-repo implementations are
same-origin and do not meet the independence bar: this is the experiment
that gathers consumer evidence, not a promotion.

Doctrine cycle B1 puts a real gap on the public record: the contract
never states whose position observation `geo` is, and the shipped
adapters split four ways answering it themselves. The entry carries the
full evidence table and the maintainer's disposition (normative sentence
in a later wave, with adapter conformance work).

Governed artifacts changed in this release, relative to zmeta-v1.1.20:
policy/semantics.yaml, policy/violation-codes.yaml,
schema/zmeta-event-1.1.0.schema.json, spec/compact-binary-mapping.md,
spec/extension-registry.yaml. The locked v1.0 kernel is unchanged.

## The reason-code mint, diagnostic-first

The three codes enter `policy/violation-codes.yaml`, the
`schema_violation_allowed_reason_codes` list, and the 1.1.0 schema's
SCHEMA_VIOLATION enum. The locked v1.0 enum cannot grow, and every wire
diagnostic the gateway builds is stamped v1.0, so a minted code in
`reason_code` would make the gateway's own diagnostic schema-invalid.
The resolution is a policy-data fallback map
(`schema_violation_v1_0_wire_fallback`): on the wire, `NON_FINITE_VALUE`
rides `SCHEMA_INVALID`, `COMMAND_EVIDENCE_UNRESOLVED` rides
`LINEAGE_PARENT_UNRESOLVED`, and `COMMAND_EVIDENCE_PROHIBITED` rides
`LINEAGE_MISMATCH`, each with `metrics.diagnostic_code` naming the
specific condition. The require-evidence refusal (citations absent under
a strict knob) keeps `LINEAGE_MISMATCH` deliberately: it is a
policy-strictness refusal outside the adjudicated pair, and the record
says so. Test pins moved red-first across the non-finite family, the
command-evidence family, the risk-mode lint, and the reason-code sweeps,
and the end-to-end pins assert the fallback pair on the wire.

## The power-reference experiment

Contract 7.4 makes `power_dbm` a required RF minimum feature, and nearly
every fielded SDR reports uncalibrated relative power. The discriminator
is the alphabet-shaped fix the A1-01 entry recommended: constrain the
meaning, not the source. With `power_reference` declared, a dBFS value
in `power_dbm` is no longer laundering, because the claim travels with
the number. The ADS-B adapter's `rf_power_reference=True` emits the RF
form for exactly the entries that carry `rssi`, with the documented
`bandwidth_hz: 0.0` not-measured sentinel and a forced 1.1.0 stamp;
entries without `rssi` keep the NETWORK form, and default output is
byte-for-byte unchanged. The fielded kraken adapter is deliberately
untouched.

## Records, errata, and tooling honesty

Two doctrine entries whose fixes landed in v1.1.20 move to terminal
(SIM1-05, R1-11-08), R1-11-07 records its fourth class survival, and the
A1-02 promotion record gains a post-cut erratum: its "two independent
implementations" citation does not meet the registry's independence
definition, and the promotion rests on the maintainer adjudication and
the readiness audit's maritime finding. `docs/release_notes_errata.md`
is new and carries one entry: the published v1.1.20 release notes
describe the reversed lock-restoration state as final, and every
correcting claim in the erratum is generated from the tree. Published
files stay exactly as published.

`tools/measure_packet_size.py` gains `--validate`: events are checked
against the schema their own version stamp names before any byte is
counted, the refusal is pinned red in-repo, and the Makefile and CI
packet gates run it at the documented 236-byte reference bearer budget.
`spec/compact-binary-mapping.md` records the measured fact that decimal
quantization saves zero bytes under the fixed-width reference float
encoding: precision reduction is an honesty lever, not a size lever.

## Verification

The wave closed under a six-lens fresh-eyes panel with one adversarial
verifier per finding; the finding-by-finding record with dispositions is
`docs/v1_1_21_precut_panel_register.md`. Full battery, kernel gates, and
the examples corpus are recorded in `VALIDATION_REPORT_v1.1.21.md`.

## Integration notes

See the README's "v1.1.21 Integration Notes" section. The short form: no
breaking changes; one new, ignorable metrics member on refusal
diagnostics; an opt-in experimental RF declaration; a validating packet
gate.

## Checksums

Checksums-only, consistent with v1.1.5 through v1.1.20. The signer
normalizes line endings before hashing text assets, so this release's
checksums are correct at source. `docs/release_checksum_errata.md`
covers the fifteen affected earlier tags.
