# Enrichment Results With Existing Vocabulary - The Receipt And Association Pattern

Status: advisory pattern guide (Docs/advisory change class, non-normative).
Current release context: ZMeta v1.1.27.

This document describes how a deployment carries the result of looking up an
observed identifier in an information source outside its own sensors (a
registry row, a listing, a catalogue entry) as ZMeta events, using only
existing vocabulary. It defines no new event types, no new subtypes, no
envelope fields, and no schema or policy changes. Nothing in this document
changes validation or dispatch behavior. Where this document conflicts with a
governed source, defer to the authority order: `spec/semantics-contract.md`
(v1.0 Locked, normative), then the canonical schemas under `schema/` and the
policy pack under `policy/`, then `docs/zmeta_change_governance.md`.

The pattern was worked out in November 2026 as rulings on one deployment's
design for such lookups. That deployment had not run the design when this was
written, so the pattern rests on the contract's text and on no fielded
evidence. One instance does not meet the promotion bar for new vocabulary,
which is why the pattern uses none. The registry records two names the design
reached for: `OSINT`, rejected as an event kind or modality, and
`COLLECT_EXTERNAL_RECORDS`, reserved as a possible future task type.

## 1. The Operational Need

A sensor reports an identifier that the observed thing declares about itself:
a vessel's identification number, an aircraft address, a call sign. An
operator wants what outside sources say about that identifier, with three
things kept visible:

- which source said it, and when it was retrieved;
- how the match was made, and how far it can be relied on;
- what the result may and may not be used for.

## 2. What The Result Is, And What It Is Not

The result is a claim about an observed entity, made by an analytics
producer. The contract places such a claim in the opinion layer: an
INFERENCE_EVENT is "What an algorithm or analyst-derived process claims"
(Section 4.4), and it "represents algorithmic or analytic claims derived from
one or more observations" (Section 7.5). Identity signals of this kind "are
claims or fused beliefs, not raw truth" (Section 17).

The result is not any of the following.

- It is not the record. ZMeta is not "A video or raw data container"
  (Section 1). The record as retrieved stays in the deployment's own store,
  and an event points to it.
- It is not an observation of the record's content. An OBSERVATION_EVENT
  "represents raw sensor-derived facts" (Section 7.4), and what a source says
  about a vessel is not a measurement of the vessel.
- It is not state, and it never changes state. An event is never modified
  once emitted (Section 4.2), and "Model claims MUST NOT create track
  identity" (Section 4.4).
- It is not authored by an operator interface. "Operator interfaces such as
  TAK do not author or modify ZMeta events" (Section 4.5). The producer is
  the component that retrieves and matches.
- It is not a command. The request to look something up is the asking
  system's own call. COMMAND_EVENT is bound to cueing and tasking through the
  deconfliction path (Sections 7.8 and 15).

## 3. The Result Pair

Each source answers each query with two events.

**The receipt** is an OBSERVATION_EVENT with modality NETWORK, under
`zmeta_version` 1.1.0, whose feature contract requires `protocol`. It records
that a retrieval happened:

- `event.ts` is the instant of the retrieval.
- `payload.features` carries `protocol` and may carry `payload_size_bytes`.
- `payload.data_ref` points to the stored record and carries its hash as
  `sha256:` followed by 64 hexadecimal characters (Section 21.3). A data
  reference must "point to retained artifacts or derived vectors" and must not
  "contain raw payload data" (Section 9.3).
- It carries no record content and no query text.

**The claim** is an INFERENCE_EVENT with `inference_type` ASSOCIATION. Its
`lineage.based_on` names the receipt and, where one exists, the observation
that reported the identifier. An inference "MUST reference upstream
observations through lineage" (Section 7.5), and the receipt is what gives a
lookup with no sensor observation behind it a lawful parent.

The claim's payload also carries two members that both schemas require.
`model` names the matching process: "It MUST include `payload.model.name`
and `payload.model.version`" (Section 7.5). `based_on` lists parent
identifiers, and the reference lineage policy refuses one that is not also
in `lineage.based_on`.

The claim's `event.ts` follows Section 5.1, under which an INFERENCE_EVENT
carries "the observation time of the primary input or inputs": the time of
the observation that reported the identifier where there is one, and the
receipt's time otherwise.

## 4. The Claim Members

`payload.claim` is an open object (Section 7.5). A deployment's member names
are its own, and they are documented and namespaced so that no consumer
mistakes them for portable vocabulary, as Section 3.3 asks of local labels and
Section 20.3 asks of vendor extensions. Members that a lookup needs:

- the basis of the match (an exact identifier, a name, a similarity score);
- for each reported field, which source reported it;
- the source's own status for the record and the source's own dates, as the
  source states them;
- the licence or terms the source attaches, as text;
- the query, as a hash or a pointer to the stored query and never as text.

The claim never carries `track_id`, `members` or `estimated_state`. Section
7.5 prohibits them in an inference payload and in its claim.

## 5. Confidence

Top-level `confidence` is required on the claim. It "is not truth. It is a
bounded machine-readable estimate of how safe" the event "is for downstream
use under the producer's documented assumptions" (Section 8.1).

A similarity score is therefore not a confidence, and it stays a claim
member. An exact match on an identifier is not a confidence of 1.0 either,
because the identifier is the entity's own report about itself. That second
sentence is the reading the rulings took; the contract does not state it.

The producer documents its formula. Section 8.6 says producers "SHOULD
document confidence formulas in operational runbooks or non-semantic
metadata".

## 6. Limits On Use

Whether a result may feed fusion, update state or cross a boundary is
deployment policy at the consumer that admits it. Section 3.3 gives the
vocabulary. A `quarantine` decision forwards "only into a restricted policy
path, local display, AAR, or other bounded consumer set". The decision names
allowed and prohibited uses from the common labels, for example DISPLAY,
LOCAL_AWARENESS and AAR_ONLY allowed, and FUSION_INPUT, STATE_UPDATE,
COALITION_EXPORT, COMMAND_BASIS and AUTONOMY_TASKING prohibited.

"Soft acceptance MUST NOT make risky data look clean" (Section 3.3). The
decision has to be filterable through the accepted event, through a
diagnostic event keyed by `original_event_id`, or both.

No governed reason code exists yet for a use limit that follows from the
class of the source. The codes are booked, and each waits for a real result
to serve as its fixture.

## 7. Producers, Timing And Profiles

- **Authority.** "AI and analytics modules may emit INFERENCE_EVENT"
  (Section 4.5). A component that both retrieves and matches performs two
  functions, the receipt and the claim, and "Separate producer identities
  SHOULD be used when one software stack performs multiple roles". Producer
  allowlists are deployment policy. The reference
  `policy/producer-authority.yaml` admits a producer for an event type only
  by a listed name or pattern, so a deployment lists its retrieving and
  matching producers in its own policy.
- **Timing quality.** "A node MUST expose timing quality either per event or
  periodically through SYSTEM_EVENT / TIME_STATUS" (Section 5.3). Per-event
  `payload.timing_quality` suits a producer that emits rarely.
- **Profiles.** Profile L prohibits INFERENCE_EVENT export (Section 10.1),
  and "Profile M does not export INFERENCE_EVENT unless a future
  schema/profile branch explicitly allows selected inference export"
  (Section 10.2). A result reaches a consumer on a Profile H or unprofiled
  route.

## 8. What Is Not An Event

- The request, a preview of what a request would return, and a cancellation.
- A source being unavailable, capped or out of trial. That is the retrieving
  component's health. It belongs in a local log, or in a SYSTEM_EVENT of
  subtype SENSOR_STATUS under `zmeta_version` 1.1.0, and never in
  SCHEMA_VIOLATION.
- A prose summary of several results. It is a rendering by the consumer. A
  summarising producer's own claim is an INFERENCE_EVENT whose lineage cites
  observations; the results it was composed from cannot be its lineage
  parents under the reference lineage policy. The doctrine log records that
  tension as F9-01.

## 9. Held Or Late Results

A result that waits at a boundary before release keeps its time. `event.ts`
"does not represent publish time, transmit time, or receive time" (Section
5.1), and no gateway may change it (Section 4.2). Receipt and publish stamps
may be added, and they show the wait.

On resume, results dedupe by `event_id` (Section 13.2).

A late result that policy degrades may take a lower `confidence` at
admission. Section 4.2 lets a projection of the same event "Conservatively
lower `confidence` or `valid_for_ms`" and keep its `event_id`. Section 4.5.1,
in its enforcement list for external promotion, states a condition for a
reduction "applied at admission under a declared degrade or quarantine
mode": it keeps the `event_id` "provided the policy-scoped record on the
accepted event names the mode and carries the values it replaced. A
reduction whose record lacks either is a replacement and requires a new
event." The rulings applied that condition to a late result as well. That
is a reading: the sentence sits in the section on external promotion, and
no text extends it to every admission.

## 10. Replay And Display

A result triggered by replayed or fixture data is replay-derived. Replay
tools "must not make replayed data indistinguishable from live operational
data in operator systems unless the operator has explicitly selected replay
mode" (Section 9.5).

A result is not an operator track. "Only STATE_EVENT / TRACK_STATE projects
to operator track CoT in v1.0" (Section 14). A consumer shows a result as an
annotation on the entity it concerns, with its source and its limits on use.
