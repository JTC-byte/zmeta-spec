# ZMeta v1.1.12 Release Notes

Release date: 2026-07-08
Release type: governance and honesty closeout patch (promotion evidence bar,
future-branch roadmap artifact, adapter lineage honesty, gateway send-failure
containment, claims-vs-reality documentation)

## Summary

ZMeta v1.1.12 closes out the stack for maintenance mode. It encodes the
contribution-intake doctrine into governed process (a promotion evidence bar
for extension-registry status transitions), implements the long-planned
S1-11B machine-readable future-branch roadmap with recorded field evidence
and promotion tripwires, removes the last fielded-honesty defect in the
reference stack (ingress adapters fabricating `lineage.based_on` with random
UUIDs), contains the gateway's only known crash risk (unhandled OSError on
oversize UDP sends), and aligns documentation with implementation reality
(mapping packs, honesty-primitive enforcement home).

It adds no schema changes and no event vocabulary; nothing new becomes valid
under `zmeta_version: "1.0"` or `"1.1.0"`. The locked v1.0 kernel is
unchanged. Reference adapter behavior changes are honesty corrections
described under Upgrade Notes.

## Major Work Completed

### Promotion Evidence Bar (governed process)

- `spec/extension-registry.md` gains a "Promotion Evidence Requirements"
  section: moving a `reserved`/`proposed` concept into a named version
  branch now requires (1) at least two independent implementations or
  deployments demonstrating the need and (2) at least one documented
  failure condition from semantic contract Section 2.6 that policy,
  configuration, profiles, adapter mappings, and namespaced extensions
  cannot solve. Single-deployment needs are served in place by the outer
  rings; declined concepts receive durable `rejected` records.
- `docs/zmeta_change_governance.md` Class D requirements reference the
  evidence bar, so versioned-branch work cannot start without it.

### S1-11B Future-Branch Roadmap Artifact (governed baseline)

- `spec/future-branch-roadmap.yaml` — machine-readable roadmap for D-003:
  18 candidates with status, priority, dependencies, required adoption
  surfaces, recorded promotion evidence, and explicit tripwires; plus 3
  recorded rejection/defer decisions (payload_schema_uri, aggregate
  snapshot as proposed, FORGE organizational scope). The upstream PR #4
  candidates (first-class correlation identity, data_ref media metadata,
  aggregate state snapshot) carry their n=1 field evidence and the
  conditions that would justify future promotion. The artifact makes no
  concept valid.
- `spec/future-branch-roadmap.md` — governance companion defining fields,
  authority limits, and usage.
- `tools/validate_future_roadmap.py` — standalone validator: structure,
  status/priority vocabulary, unique ids, dependency resolution,
  registry cross-references, tripwire coverage, and a status-leakage check
  (a roadmap candidate cannot claim experimental/adopted standing while its
  registry names remain reserved/proposed). Covered by
  `gateway/tests/test_future_roadmap_validation.py`.
- The release manifest gains a `future_branch_roadmap` artifact group
  (groups 18 -> 19, artifacts 67 -> 70).

### Adapter Lineage Honesty (runtime/reference)

Six ingress adapters previously fabricated `lineage.based_on` with a fresh
random UUIDv7 on every event — provenance that looked traceable but dangled.
All fabrication is removed; parent ids are never invented:

- kraken (1.2.0), moth (1.2.0), signalhunter (1.1.0), and the KLV template
  (0.2.0): OBSERVATION_EVENT output omits `lineage` by default (original
  observations have no ZMeta parent; envelope lineage is optional for
  observations). Callers with real upstream artifact events can pass
  `based_on=[...]` to emit true lineage with the translation transform.
- mavlink template (1.2.0): STATE_EVENT lineage is mandatory (contract 4.8)
  and must be real — the state dict must carry `based_on` or
  `source_zmeta_event_id`, otherwise the translator refuses to emit
  (the same convert-or-refuse rule as position handling). SYSTEM_EVENT
  builders omit lineage unless the caller supplies parents.
- eo-cv (1.1.0): INFERENCE_EVENT requires real input-observation lineage
  (contract 4.8/11.3) — the adapter uses an explicit `parent_event_ids`
  argument or a schema-valid UUIDv7 `source_event_id` from the detection,
  and refuses to emit otherwise. Non-UUID upstream handles are preserved in
  the claim but cannot launder into lineage.
- The adapter-harness fixture suite was updated to pin the honest behavior
  (lineage forbidden on default observation outputs, real parents pinned on
  promotion/inference outputs) and gains a caller-supplied-lineage fixture
  (total 11). New `adapters/ingress/eo-cv/test_eo_cv_ingress.py` covers the
  refusal and precedence paths. The ingress template README rule that
  previously mandated a lineage transform unconditionally now states the
  never-fabricate rule.

### Gateway Send-Failure Containment (runtime)

- `gateway/src/gateway.py` no longer crashes on oversize outgoing UDP
  payloads: both send paths route through `_send_datagram`, which catches
  `OSError` (for example the ~65507-byte UDP limit), drops that datagram,
  and records an explicit `send_failure` diagnostic (counter, per-kind map,
  and metrics-log record). Nothing is truncated or retried, no event is
  silently altered, and forwarded/CoT counters only increment on actual
  sends. Covered by new tests including a real-socket oversize proof.

### Claims-vs-Reality Documentation (advisory)

- `adapters/mapping-packs/README.md` states plainly that a mapping pack is a
  declarative description plus test evidence: no runtime engine executes
  `mapping.yaml`; translation runs in adapter code and the pack's samples
  are the conformance evidence. (Egress READMEs already carry honest
  not-a-wire-format labels.)
- `docs/zmeta_professional_overview.md` gains "Where these primitives are
  enforced": `risk_adjudication` / `external_promotion` deliberately live
  above the locked schema kernel, enforced by policy packs, validators,
  projection preservation, and conformance gates — deployments needing the
  guarantee must run policy validation, not schema validation alone.
  Schema-level standing is parked as an evidence-gated roadmap candidate.

### Process Closeout

- The handoff's open-ended "human decisions for future hardening" list is
  resolved to recorded standing defaults (reference behavior stands unless
  field evidence or an evidence-bar tripwire forces a revisit), leaving two
  genuinely open maintainer decisions: the release-signing process (in
  progress) and whether v1.1.0 is ever adopted as baseline.
- `tools/check_compat.py` gains the `v1.1.12` target.

## Issue Status At Release

- D-003: OPEN - ROADMAP PLANNED. With the S1-11B machine-readable roadmap
  artifact now implemented, the S1-11A Section M closure condition is met;
  closing D-003 is recommended and awaits the maintainer's decision.

## Validation Summary

The release was validated with release manifest and package validation,
strict examples (47 events across 8 corpora), full kernel conformance
(projection, registry, conformance class, encoding-negative,
precision-policy, release-manifest, release-package, bad-event, and adapter
validators), the future-branch roadmap validator, full pytest (465 passed,
110 subtests), gateway self-tests (Profile H, gateway config, edge config),
end-to-end workflow tests (Profiles H and M), live gateway tests (JSON and
compact encodings with CoT output), migration compatibility checks for all
example corpora against `--target v1.1.12`, packet-size checks, release
artifact builds, checksum generation and verification, and
`git diff --check`.

See `release/VALIDATION_REPORT_v1.1.12.md` for command details.

## Release Assets

Expected release assets:

- `zmeta-v1.1.12-dist.zip`
- `zmeta-edge-v1.1.12.zip`
- `zmeta-gateway-v1.1.12.zip`
- `zmeta-release-package-v1.1.12.zip`
- `zmeta-release-manifest.yaml`
- `RELEASE_NOTES_v1.1.12.md`
- `VALIDATION_REPORT_v1.1.12.md`
- `SHA256SUMS_v1.1.12.txt`

No detached `.asc` signatures are attached unless the release authority signs
the artifacts with an approved external signing process. No private keys,
credentials, tokens, certificates, or signing secrets are stored in this
repository.

## Upgrade Notes

- No schema or vocabulary changes: producers and consumers pinned to
  v1.1.11 (or the locked v1.0 kernel) need no changes.
- Integrations that call the reference ingress adapters directly should
  review the lineage behavior change:
  - Observation adapters (kraken/moth/signalhunter/klv) no longer emit a
    fabricated `lineage` block. Consumers that assumed lineage presence on
    these outputs were consuming fabricated ids; pass real parent ids via
    `based_on=[...]` if true lineage exists.
  - `translate_platform_state` (mavlink) and `translate` (eo-cv) now refuse
    to emit without a real lineage parent (`based_on` /
    `source_zmeta_event_id` / `parent_event_ids` / UUIDv7
    `source_event_id`). Callers must supply real provenance; this is the
    contract-mandated behavior for STATE and INFERENCE events.
- Gateway operators gain `send_failures` metrics; a datagram that exceeds
  the UDP limit is now dropped with a diagnostic instead of terminating the
  gateway process. Consider `warn_datagram_bytes` to see oversize warnings
  before the send boundary.
- Deployments using release or contract hash gates should update expected
  hashes from the v1.1.12 release manifest.
