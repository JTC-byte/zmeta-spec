# Event Signing: What the Closed Schema Requires

Status: design note, advisory, non-normative (Docs/advisory change class). It
scopes the versioned branch behind roadmap candidate `event-signing-anti-replay`
and registry entries `EVENT_SIGNATURE` and `KEY_IDENTITY` (proposed) and
`ANTI_REPLAY_NONCE` (reserved). It decides nothing. Whether the candidate's
tripwire has fired is the maintainer's decision (handoff Tier 2 item 6;
doctrine U1-02). Written 2026-10-01 on the maintainer's go of 2026-09-30.

## 1. The constraint

Both schema lanes, `schema/zmeta-event-1.0.schema.json` and
`schema/zmeta-event-1.1.0.schema.json`, set `additionalProperties: false` on
the event root, `$defs/event`, `$defs/source` and `$defs/lineage`. The root
admits exactly `zmeta_version`, `event`, `source`, `profile`, `payload`,
`confidence` and `lineage`. Doctrine C1-06 records the consequence: per-event
signing cannot be met in the outer rings.

The open places are inside the payload: `payload.extensions` on every event
type, and the payload object itself on every type except COMMAND_EVENT,
whose payload is closed. Each is the wrong home for a signature. Contract
Section 20.3 forbids an extension from overriding trust or authority
boundaries, an extension is safe to ignore by definition, a gateway may
strip optional members under `strip_optional_fields`, Section 20.4 makes
nothing normative because a schema happens to accept it, and Section 4.11
lets a vendor extend a payload but never alter the envelope. A
signature carried there is a hint a consumer may lawfully drop, and it
would sit inside the bytes it signs.

A signature with normative force therefore lives in a new member that a
later schema version adds to the closed root, or outside the event, in an
envelope or a sidecar event.

## 2. Questions every carrier must answer first

### 2.1 The signed bytes

A signature verifies only if the verifier can reproduce the signed bytes.
Doctrine C1-07 records that the two shipped CBOR backends emit different
bytes for the same value (`fb405e000000000000` against `f95780` for `120.0`),
that the determinism clause in `spec/compact-binary-mapping.md` is
SHOULD-level, and that cross-encoding equality is defined as object
equality. The reference gateway also converts between JSON, CBOR and the
compact mapping. A signature over the wire bytes therefore verifies only at
the hop that produced them.

The branch must define a canonical form, computed from the event object and
independent of the wire encoding, over which signatures are made and
checked. Roadmap candidate `canonical-byte-form` holds that decision, and
`event-signing-anti-replay` lists it in `depends_on` (doctrine U1-02,
decided 2026-10-01).

### 2.2 The signed view

A signature over the whole event breaks at the first reference gateway,
because the gateway legitimately changes it:

- it stamps `event.t_receive` and `event.t_publish` when `stamp_timing`
  applies (`gateway/src/gateway.py`, the forwarding loop);
- it sets the root `profile` when `stamp_profile` applies;
- it removes configured optional members under `strip_optional_fields`;
- contract Section 3.3 lets it, and for some decisions requires it, to add
  a compact self-label in a policy-scoped extension on an admitted event;
  the reference gateway appends `payload.extensions.risk_adjudication`.

Contract Section 4.2 lists what a gateway must not change: `event.ts`,
`event_id`, `event_type`, `event_subtype`, `source`, `payload.track_id`,
lineage, and payload meaning. The signed view follows from the two lists: the
members the source authored, with gateway stamps and gateway-authored
policy-scoped extensions excluded by rule. The branch must also decide how a
strippable member is treated: a gateway must either leave signed members in
place or strip only members outside the signed view. The same subset is what
an admission boundary compares when it checks that a forwarded event was not
altered. Contract Section 16.2 already lists this among what signing
semantics must define: whether gateway-added metadata is inside or outside
the signed semantic event.

### 2.3 Key identity

A producer name is a declaration, not proof (doctrine E1-02). The
`KEY_IDENTITY` concept binds a verification key to `source.producer` and
`source.platform_id`. Key distribution, rotation and revocation are
deployment policy. A key identifier travelling with the event has the same
carrier problem as the signature, so it belongs in the same carrier.

### 2.4 Replay

`event.event_id` is time-ordered and `event.ts` is present, so a verifier can
bound replay with an acceptance window on `ts` and a per-key set of recently
seen identifiers. `ANTI_REPLAY_NONCE` stays reserved for links where that is
not enough. A legitimate replay, such as an after-action review, carries its
original signature and a replay label (contract Section 9.5); a verifier must
not present it as live.

### 2.5 Outcome and reporting

The branch decides what a gateway does with a missing, invalid,
unknown-key or replayed signature, with the dispositions this repository
uses elsewhere (reject, warn, degrade, quarantine, never a silent pass;
contract Section 16.2 names quarantine, warning, rejection and trust
downgrade for failed or missing signatures) and new violation
codes minted through the registry. Profile L has size budgets, and a
signature plus a key identifier adds tens of bytes to every event; the
branch measures that on the Profile L examples before choosing a carrier.

## 3. The three carriers

| Carrier | Change to the event schema | Across re-encoding | Across gateway changes | Main cost |
|---|---|---|---|---|
| Envelope: a signed container around the event (COSE_Sign1 for CBOR and the compact mapping, JWS for JSON) | None; a framing specification and gateway support | Only with a canonical form (2.1) | Only with a signed view (2.2) | Every hop must carry the envelope; egress projections drop it, as design gate 4 expects |
| Sidecar: a SYSTEM_EVENT keyed by the signed event's `event_id` | A new SYSTEM_EVENT subtype in a versioned branch | Only with a canonical form | Only with a signed view | The pair can be separated or reordered, so a consumer holds the event as unverified until its sidecar arrives; one more message per event on constrained links |
| Member: a new root member in a later schema version | Opens the closed root in a versioned branch | Only with a canonical form | Only with a signed view, which must exclude the member itself | Every consumer of the new version must parse it |

## 4. Recommended order

This is the repository's recommendation for the branch, not a decision. It
follows the split the handoff already records for this work (Tier 3 item
9): canonicalization normative in the specification, an optional signature
member on a versioned schema branch, and keys, algorithms, trust anchors
and failure behavior in policy, adopting COSE and JWS wholesale and writing
no cryptography.

1. Decide C1-07: the canonical form, at minimum float width and whether the
   determinism clause becomes MUST-level. It is the cheapest step and every
   carrier needs it.
2. Write the signed view as contract text in the branch (2.2).
3. Add the optional signature member on a versioned schema branch, its
   value a COSE or JWS structure over the canonical form of the signed view.
   The member travels with the event through every hop and adds no framing
   layer to standardize, which is why the recorded split prefers it to the
   envelope and the sidecar. Measure Profile L.
4. Bring `KEY_IDENTITY`, `EVENT_SIGNATURE` and the verification codes through
   the registry with the branch's implementation as evidence; keys,
   algorithms, trust anchors and failure behavior go in policy.
5. Keep the envelope and the sidecar as recorded alternatives. An envelope
   needs no schema change, so a deployment that needs per-event
   authenticity before the branch lands can frame its own traffic that way,
   as deployment configuration outside the event model.

Promotion needs what the registry's bar asks of any candidate: two
independent implementations or deployments from different organizations
(doctrine U1-02 confirms that one organization counts once) and a documented
failure condition, such as an altered event or an unauditable command basis
accepted across a trust boundary.

## 5. Out of scope

Transport security (TLS, DTLS, a WireGuard tunnel) authenticates a link, not
an event, and is deployment configuration available today. Signing proves who
authored an event and that it was not altered; it does not make the content
true. A signed event from a compromised or mistaken producer is authentic and
wrong, and the honesty labels on it still apply.
