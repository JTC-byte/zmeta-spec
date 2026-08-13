# Track Lifecycle With Existing Vocabulary - The Command-Grade Track Pattern

Status: advisory pattern guide (Docs/advisory change class, non-normative).
Current release context: ZMeta v1.1.23.

This document describes how a fielded deployment answers the track lifecycle
questions -- is this track new, active, stale, lost, merged, split, retired,
and above all **is this track command-grade evidence right now?** -- using
only locked ZMeta v1.0 vocabulary plus the v1.1.x additive surfaces that
already exist. It defines no new event types, no new subtypes, no envelope
fields, and no schema or policy changes. Nothing in this document changes
validation or dispatch behavior. Where this document conflicts with a
governed source, defer to the authority order: `spec/semantics-contract.md`
(v1.0 Locked, normative), then the canonical schemas under `schema/` and the
policy pack under `policy/`, then `docs/zmeta_change_governance.md`.

Dedicated track-lifecycle vocabulary (`TRACK_NEW`, `TRACK_ACTIVE`,
`TRACK_STALE`, `TRACK_LOST`, `TRACK_MERGED`, `TRACK_SPLIT`, `TRACK_RETIRED`)
exists in `spec/extension-registry.yaml` **with status `reserved`**, and the
`track-lifecycle` candidate in `spec/future-branch-roadmap.yaml` is likewise
reserved with an explicit tripwire: promotion evidence must show lifecycle
needs that exceed what the advisory patterns already express. Per the
registry rules, a reserved name is not valid vocabulary and confers nothing.
This document is the current-vocabulary expression that promotion evidence
must be measured against -- it exists precisely so that the reserved names
are not needed for today's fielding decisions, the same way
`docs/zmeta_correlation_pattern.md` expressed cross-sensor correlation
without new vocabulary.

## 1. The Operational Need

A deployment moving from "display the tracks" to "let one platform retask
another off a track" needs answers, per track, at decision time:

- **Which lifecycle stage is this track in?** New, actively updated, going
  stale, effectively lost, replaced by a merge or split, or permanently
  retired.
- **Is this track safe to command against?** A track that is fine to render
  on an operator display may be entirely unfit as the evidence basis for
  tasking a platform. Display tolerates staleness and degraded labels;
  command tolerates neither.

The locked contract already defines the lifecycle *meanings* (contract
Section 13.3) without dedicated machine-readable lifecycle events -- and it
turns out none are needed to answer either question. Every stage below is
computable by a consumer from events and labels that already flow.

## 2. New and Active: Fusion Identity Plus a Fresh TTL

A track is **new** when a fusion-authorized producer emits the initial
FUSION_EVENT / TRACK_FUSION minting its `payload.track_id` (contract
Sections 4.5, 7.6, 13.1, 13.3). Identity creation is covered end-to-end by
the correlation pattern (`docs/zmeta_correlation_pattern.md`, Section 2):
the fused `track_id` is the stable cross-sensor identity, and bond
assignment to contributing sensors travels as INFERENCE_EVENT / ASSOCIATION
claims (its Section 3).

A track is **active** while the fusion node keeps emitting FUSION_EVENT and
STATE_EVENT updates for the same `track_id` (contract 13.3) and the latest
STATE_EVENT / TRACK_STATE is inside its own validity window. TRACK_STATE
carries a mandatory `payload.valid_for_ms` TTL (contract 7.7); an active
track is simply one whose latest state satisfies:

```text
now < event.ts + payload.valid_for_ms
```

with `event.ts` being the semantic validity time, never receive or delivery
time (contract 5.1-5.2).

## 3. Stale: TTL Arithmetic Plus Timing-Freshness Labels

**Stale is a consumer-side computation, not an event.** Nothing in the
stream announces staleness; the consumer derives it, per contract 13.3
(inputs older than a configured threshold; confidence and TTL must decay)
and the retained-message honesty rules of the MQTT binding guidance
(`docs/zmeta_mqtt_binding_guidance.md`): a delivered or retained state is
stale data with a timestamp, never current truth.

Two independent signals feed the computation:

1. **TTL arithmetic.** `event.ts + payload.valid_for_ms` against current
   time. Lapsed means expired: usable for history and AAR, MUST NOT be
   rendered or used as current state.
2. **Timing-quality honesty labels.** Freshness of the *clock* behind the
   timestamps, judged from per-event `payload.timing_quality` or the
   source's latest SYSTEM_EVENT / TIME_STATUS (contract 5.3), under
   `policy/timing-freshness.yaml` (per-profile `max_timing_status_age_ms`,
   negative-age tolerance). When the gateway finds timing context missing,
   stale, or unsynced, the disposition follows the policy mode -- the
   reference defaults differ by code (`TIMING_STATUS_MISSING` is
   `mode: reject` in the reference pack; the age/stale arms default to
   warn/degrade labels). Refused or labeled, never silently dropped,
   under the existing governed reason codes (`policy/violation-codes.yaml`):
   `TIMING_STATUS_MISSING`, `TIMING_STATUS_STALE`,
   `TIMING_STATUS_AGE_NEGATIVE`, `TIMING_STATUS_UNSYNCED`. Warn/degrade
   outcomes ride the event as `payload.extensions.risk_adjudication`
   records (risk dimension `timing`), carrying the policy's `use_limits` --
   and both the warn and degrade limit sets in the reference policy
   prohibit `COMMAND_BASIS` and `AUTONOMY_TASKING` outright.

A consumer treating a track as merely "stale but displayable" is exercising
exactly the honesty split the labels encode: warn/degrade-labeled state
remains allowed for `DISPLAY`, `LOCAL_AWARENESS`, and `ALERTING`, while its
command-basis use is already prohibited by the label it carries.

## 4. Lost and Retired: TTL Expiry and Broker Hygiene

A track is **lost** when observations exceed the configured age threshold:
state emission stops, or continues explicitly stale/low-confidence until TTL
expires (contract 13.3, with the confidence-decay drivers of 13.4). A track
is **retired** when its `track_id` will never be used again -- and reuse is
forbidden unconditionally after loss, merge, split, or retirement (contract
13.1).

There is no removal event to wait for, and none may be invented. Semantic
expiry is conveyed in-band by TTL lapse; the MQTT binding guidance
(`docs/zmeta_mqtt_binding_guidance.md`, "Tombstones Are Broker Hygiene, Not
Semantics") already governs the transport side: publishers SHOULD clear a
retained `state/TRACK_STATE/<track_id>` slot with a zero-byte retained
payload when they permanently stop publishing it, and consumers MUST NOT
read that tombstone as an entity-removal directive. The safe interpretation
is only "no retained snapshot is available." Lost/retired transitions
belong in local AAR and operator logs (contract 13.3), never in mutated
events and never in transport state.

## 5. Merged and Split: Already Solved, Cited Not Restated

Merge and split are covered by the correlation pattern's **atomic split
invariant** (`docs/zmeta_correlation_pattern.md`, Section 4), composing with
contract 13.3: new FUSION_EVENTs mint the replacement identities with
lineage to the prior history, the old `track_id` is never reused, and one
BOND_DISSOLVED ASSOCIATION event carries both the dissolved bonds and their
replacements so no consumer ever observes an intermediate state. This
document adds nothing to it; consult that section directly.

## 6. Command-Grade: The Load-Bearing Question

Everything above feeds one adjudication. **A track is command-grade
evidence only when all four of the following hold at decision time:**

**(a) Fresh.** The latest TRACK_STATE is inside `event.ts +
payload.valid_for_ms`, and the applicable timing-freshness signals are
clean -- no `TIMING_STATUS_MISSING` / `TIMING_STATUS_STALE` /
`TIMING_STATUS_AGE_NEGATIVE` / `TIMING_STATUS_UNSYNCED` label riding the
evidence chain. An expired or timing-suspect track can inform a human
picture; it cannot motivate a machine command.

**(b) Its risk labels do not prohibit command use.** The S1-15 risk
adjudication model is the enforcement surface: labels at
`payload.extensions.risk_adjudication` carry `policy_decision`,
`allowed_uses`, and `prohibited_uses`, and the operator-side filter
`tools/filter_risk.py` ships the exact postures:

- the `command` preset: `max_risk=clean`, requires every risk record to
  explicitly allow `COMMAND_BASIS`;
- the `autonomy` preset: `max_risk=clean`, requires `AUTONOMY_TASKING`.

Under these presets any event carrying a `WARN_ACCEPT`, `DEGRADED_ACCEPT`,
or `QUARANTINE_ACCEPT` decision is excluded from the command path, and a
PRESENT risk record must explicitly allow the required use (relaxable
per-record with `--permit-unlabeled-use`). Be precise about the default
boundary: an event carrying **no** `risk_adjudication` records at all
passes both presets -- labels are attached only when a policy had
something to say, and no shipped knob excludes wholly-unlabeled events.
A deployment that wants *labeled-only* command evidence enforces that at
the automation, or via the command-evidence check
(`policy/command-evidence.yaml`), which consults the labels the gateway
recorded for the cited parents. The reference policies that attach
warn/degrade labels (`policy/timing-freshness.yaml`, `policy/lineage.yaml`,
`policy/producer-authority.yaml` -- including its external-promotion
arms) list `COMMAND_BASIS` and `AUTONOMY_TASKING` under `prohibited_uses`,
so degraded evidence self-excludes: honesty labels attached at ingest
become command refusals at use time, with no new mechanism.

**(c) Confidence above the deployment's threshold.** Top-level `confidence`
is mandatory on STATE_EVENT and FUSION_EVENT (contract 8.1) and must already
account for input quality, timing, lineage, freshness, and fusion stability
(contract 8.3). The kernel deliberately standardizes the *honesty* of the
number, not a universal cut line: the command-basis confidence floor is
deployment policy/configuration. What the pattern requires is that the
floor exists, is written down, and is applied to the value as labeled --
never to a re-inflated one (projection must not increase confidence,
contract 8.4).

**(d) The commanding node cites it.** A command motivated by a track must
carry the evidentiary chain: the motivating inference/fusion events cited
as lineage parents, gateway-checked for resolvability, parent-type sanity,
and upstream `use_limits` -- reusing the existing governed codes
`LINEAGE_PARENT_UNRESOLVED` and `LINEAGE_PARENT_TYPE_INVALID`
(`policy/violation-codes.yaml`). The reference enforcement for this check
is `policy/command-evidence.yaml` (introduced in the same work cycle as
this document): its purpose is exactly the command-evidence lineage check
-- commands that claim machine evidence must cite it, and the cited
evidence must itself have been command-usable. A bare operator-originated
command with no cited parents remains legitimate; the check binds commands
that claim evidence, it does not manufacture a citation requirement for
human judgment. Consult that policy file and its tests for the normative
enforcement details rather than this summary.

Conditions (a)-(c) are consumer/filter-side and work today with shipped
tooling. Condition (d) is the gateway-side check named in the fielding gate
below.

## 7. The Fielding Gate

The maintainer's decision path for the UxS command loop (recorded
2026-07-17, `docs/zmeta_refinement_worklog.md`), preserved here in intent:

1. **Display loop: fieldable now.** Sensor-to-COP display of fused tracks
   requires nothing beyond the shipped stack; staleness and degraded labels
   are display-tolerable because they are visible and filterable.
2. **GCS-originated tasking gates on two things:** the command-evidence
   lineage check -- commands citing their motivating inference/fusion
   parents, gateway-checked against upstream `use_limits`
   (`policy/command-evidence.yaml`) -- plus a SITL end-to-end pass of the
   full collect -> fuse -> command -> TASK_ACK loop before any live
   platform is tasked.
3. **Platform-to-platform retasking additionally gates on:** authenticated
   transport (a deployment-side obligation -- transport bindings carry no
   semantics, contract 4.6, and the kernel does not currently define signing
   or key identity), and promotion of the track-lifecycle branch once its
   evidence bar is met. That promotion is explicitly **not now**: the
   roadmap tripwire demands evidence of lifecycle needs beyond this pattern
   and the correlation pattern, and the awaited second independent evidence
   leg has not yet landed (see the `track-lifecycle` candidate's
   `promotion_evidence` in `spec/future-branch-roadmap.yaml`).

The ordering is the honesty model working as designed: each ring of the
loop is gated on the enforcement that makes its failure modes loud, and no
ring waits on vocabulary it does not need.

## Lifecycle At A Glance

| Stage | How it is expressed today | Grounding |
|---|---|---|
| New | Initial FUSION_EVENT / TRACK_FUSION mints `track_id`; bonds via ASSOCIATION | Contract 4.5, 7.6, 13.3; correlation pattern Sections 2-3 |
| Active | Continued FUSION/STATE updates; latest TRACK_STATE inside `valid_for_ms` | Contract 7.7, 13.3 |
| Stale | Consumer computes `event.ts + valid_for_ms` vs now; timing labels (`TIMING_STATUS_*`) ride the event | Contract 5.3, 13.3; `policy/timing-freshness.yaml` |
| Lost | Age threshold exceeded; emission stops or stays explicitly stale until TTL expiry | Contract 13.3, 13.4 |
| Retired | `track_id` never reused; retained-slot tombstone is broker hygiene only | Contract 13.1; MQTT binding guidance |
| Merged / Split | New fusion identities with lineage; atomic BOND_DISSOLVED notification | Contract 13.3; correlation pattern Section 4 |
| Command-grade | Fresh + labels permit `COMMAND_BASIS` / `AUTONOMY_TASKING` + confidence over deployment floor + cited per command-evidence check | Contract 8.1, 8.3; `tools/filter_risk.py`; `policy/command-evidence.yaml` |

## 8. What This Pattern Does Not Do

- **No new vocabulary, no promotion.** The `TRACK_*` registry names stay
  `reserved` and invalid; the roadmap candidate stays `reserved`. This
  document *raises* the promotion bar by demonstrating how much of the
  lifecycle current vocabulary already carries -- future evidence must
  exceed it (contract 24.4 keeps lifecycle subtypes future work).
- **No lifecycle state field.** There is no `track_status` payload
  convention here, deliberately. A lifecycle stage asserted by a producer
  is a claim that goes stale the moment link conditions change; a stage
  computed by the consumer from `event.ts`, `valid_for_ms`, and the label
  stream is always exactly as current as the consumer's own clock. Stamping
  it into events would also collide with reserved registry names.
- **No transport semantics.** Retained slots, tombstones, and QoS remain
  broker mechanics per the MQTT binding guidance; nothing here derives
  lifecycle truth from transport state.
- **No relaxation of command governance.** Producer authority,
  `requires_deconfliction`, `task_id` idempotency, command TTL, and the
  altitude prohibition (contract 7.8, 15) all apply unchanged; command-grade
  adjudication is a *further* restriction on evidence, never a bypass.
- **No mutation.** Every transition is expressed by new append-only events
  or by consumer-side computation; old events are never edited (contract
  4.2, 13.3).
