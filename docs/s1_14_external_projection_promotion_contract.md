# S1-14 External Projection Promotion Contract

Status: implemented reference policy hardening.

## Purpose

External tactical formats can carry lossy track projections that look like clean
state after adapter translation. S1-14 hardens the boundary where CoT/TAK,
JREAP-style, MAVLink, or vendor COP track reports re-enter ZMeta.

The core rule is:

> A lossy adapter projection or external tactical report must not become
> authoritative ZMeta `STATE_EVENT` unless promotion policy, freshness, lineage
> status, confidence basis, trust reference, and loop/reflection status are
> explicit and valid.

## Implemented Boundary

The reference producer-authority policy now marks CoT, JREAP, and MAVLink state
ingress producers as external promotion sources. They may still emit
`STATE_EVENT`, but only when `payload.extensions.external_promotion` satisfies
the active policy.

The validator enforces this as producer authority, not schema shape. A
schema-valid external state event without valid promotion evidence fails with
`PRODUCER_NOT_ALLOWED`.

## Operator-Tunable Enforcement

The reference policy defaults to `mode: reject`. Edge deployments may change
`producer_authority.external_state_promotion.mode` when operational conditions
require a looser response without bypassing semantics:

- `reject`: drop the promoted state and emit a rejection diagnostic.
- `warn`: forward the state unchanged and emit a warning diagnostic.
- `degrade`: forward the state, emit a warning diagnostic, reduce confidence,
  shorten `payload.valid_for_ms`, and stamp the policy decision in
  `payload.extensions.external_promotion`.
- `quarantine`: forward the state, emit a warning diagnostic, cap confidence,
  cap `payload.valid_for_ms`, and stamp a policy-scoped quarantine decision in
  `payload.extensions.external_promotion`.

Deployments may scope this response with `mode_by_profile` or with a specific
producer rule's `external_state_promotion.mode` when one feed/link needs looser
behavior than the rest of the system.

Loop/reflection risk remains hard-rejected by default through
`always_reject_loop_risk: true`. Operators can deliberately soften that guardrail
only by changing policy, and the resulting event still carries a diagnostic.
This keeps emergency flexibility explicit and auditable.

## Profile Behavior

Profile H carries full audit detail:

- promotion policy id
- projection id
- origin kind
- trust reference
- lineage status
- confidence basis
- source event identity
- freshness
- loop/reflection status

Profile M carries compact policy/trust/projection/confidence references.

Profile L carries only compact handles and status codes:

- state category
- promotion policy id
- trust reference
- lineage status
- loop/reflection status

This keeps the bandwidth property intact. Promotion evidence is not raw data,
does not expand lineage ancestry, and does not require full audit blocks on
Profile L links. Degrade and quarantine mode annotations are compact policy
decisions, not raw evidence replay or expanded provenance.

## Not Changed

- No new event type.
- No schema branch change.
- No new top-level event field.
- No change to v1.0/v1.1.0 version discrimination.
- No promotion of future trust/signing/quarantine vocabulary; quarantine mode is
  a policy-scoped decision stamp, not a new schema-level trust state.
- No same-event profile projection metadata.

## Remaining Future Work

S1-14 does not implement cryptographic trust, signed route provenance, AI
confidence decomposition, coalition release policy, or full loop graph
resolution. Those remain future versioned/policy work. This change creates the
policy hook that prevents external lossy state from being accepted silently
while those larger controls are still out of scope.
