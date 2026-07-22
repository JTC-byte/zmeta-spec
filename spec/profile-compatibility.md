# Profile Compatibility Matrix

This page summarizes **which event types are allowed per profile**, recommended
wire encodings, and reference producer allowlists. The authoritative rules live in:
- `policy/profiles.yaml`
- `policy/roles.yaml`
- `policy/producer-authority.yaml`
- `policy/lineage.yaml`
- `policy/timing-freshness.yaml`
- `policy/routing.yaml`

## Profile vs Event Types

| Profile | Allowed Event Types |
| --- | --- |
| L | STATE_EVENT, SYSTEM_EVENT, COMMAND_EVENT |
| M | STATE_EVENT, FUSION_EVENT, SYSTEM_EVENT, COMMAND_EVENT, OBSERVATION_EVENT |
| H | OBSERVATION_EVENT, INFERENCE_EVENT, FUSION_EVENT, STATE_EVENT, COMMAND_EVENT, SYSTEM_EVENT |

## Recommended Encodings (Wire)

| Profile | Recommended Encoding | Notes |
| --- | --- | --- |
| L | `compact` | Smallest wire format; intended for bandwidth-constrained links. |
| M | `cbor` or `proto` | CBOR reduces size with simple tooling; protobuf is useful for typed gateway/service links. |
| H | `json`, `cbor`, or `proto` | JSON is best for debug/audit; protobuf is useful for service integration. |

## Encoding Compatibility

| Encoding | Status | Primary Use |
| --- | --- | --- |
| `json` / JSONL | Canonical reference | Human-readable interchange, examples, audit, broad tooling. |
| `cbor` | Reference encoding | Binary event transport where semantic payload shape remains unchanged. |
| `compact` | Profile L reference encoding | CBOR integer-key mapping for constrained links. |
| `proto` | Experimental encoding | Typed envelope projection for services, queues, and gRPC-style integration. |

All encodings must decode to a value-identical ZMeta JSON event and pass the
same schema and policy validation. Encoding choice does not change event
semantics. "Value-identical" is not "byte-identical": an encoding may declare
representation normalizations that change how a value is written without
changing what it means — the compact mapping declares exactly two (UUID hex
case, since UUIDs travel as 16 raw bytes and RFC 4122 is case-insensitive, and
timestamp formatting at its declared millisecond resolution). Those are
enumerated in `spec/compact-binary-mapping.md` Scope; an encoding MUST NOT
normalize anything it has not declared, and refusing a declared normalization
is itself a defect. Where an encoding cannot represent an event losslessly
(the compact mapping encodes locked-v1.0 events only), the encoder MUST refuse
rather than reduce — same Scope section.

## Projection Preservation

Profile H/M/L thinning is checked as a conformance layer in addition to
single-event schema and policy validation. A lower-profile event that claims to
be a same-event projection must preserve event identity, event time, source
identity, semantic layer, track identity, lineage, units, timing semantics,
confidence monotonicity, TTL monotonicity, and cataloged optional omission
rules.

The machine-readable field catalog is:

```text
conformance/profile_projection_field_catalog.yaml
```

The source/projected fixture suite is:

```text
conformance/profile-projection/
```

Run it directly:

```bash
python tools/validate_projection.py --catalog conformance/profile_projection_field_catalog.yaml --must-pass conformance/profile-projection/must-pass.jsonl --must-fail conformance/profile-projection/must-fail.jsonl
```

Or include it explicitly with conformance validation:

```bash
python tools/validate_conformance.py --strict --profile-projection
```

This does not change the v1.0 schema and does not add projection metadata to
v1.0 events. Future projection metadata remains a versioned candidate.

## External Promotion Metadata

External ingress from CoT/TAK, JREAP-style gateways, MAVLink, or vendor COPs is
not a same-event profile projection. It is a boundary promotion decision.

Reference policy requires external `STATE_EVENT` producers to carry
policy-scoped promotion evidence under `payload.extensions.external_promotion`
before their events are accepted as authoritative ZMeta state. Profile H carries
full audit detail; Profile M carries compact policy/trust/projection references;
Profile L may carry only minimal handles and status codes.

This metadata does not authorize raw observation fields in `STATE_EVENT`, does
not replace `lineage.based_on`, and does not turn external systems into ZMeta
semantic authority by schema shape alone.

## Profile Precision Policy

Profile L/M/H precision and quantization behavior is checked as a separate
profile/export policy layer. The human-readable policy is:

```text
spec/profile-precision-policy.md
```

The reference conformance default policy is:

```text
policy/profile-precision.yaml
```

Run it directly:

```bash
python tools/validate_precision_policy.py --policy policy/profile-precision.yaml --must-pass conformance/profile-precision/must-pass.jsonl --must-fail conformance/profile-precision/must-fail.jsonl
```

Or include it explicitly with conformance validation:

```bash
python tools/validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative --precision-policy
```

Precision policy does not create semantics and does not change profile/event
legality. It constrains how already-valid events may be conservatively exported
with lower fidelity. The reference defaults require mission review; deployments
may later override them through reviewed policy. Source event identity,
event time, source identity, track identity, lineage, discriminator fields, and
units remain immutable.

## Reference Producer Allowlists

Reference producer authority rules are maintained in
`policy/producer-authority.yaml`. They are deployment policy, not a semantic
requirement to use the example producer names. Command-authorized producers must
also be explicitly allowlisted in `policy/routing.yaml` and must satisfy the
command routing and deconfliction rules in the active policy pack.

## Node Role Constraints (Policy)

| Node Role | Allowed Event Types |
| --- | --- |
| EDGE | OBSERVATION_EVENT, SYSTEM_EVENT |
| GATEWAY | OBSERVATION_EVENT, INFERENCE_EVENT, FUSION_EVENT, STATE_EVENT, COMMAND_EVENT, SYSTEM_EVENT |
| APEX | FUSION_EVENT, STATE_EVENT, SYSTEM_EVENT |
| DMZ | SYSTEM_EVENT, STATE_EVENT |
| CLOUD | SYSTEM_EVENT, STATE_EVENT |

Use this matrix for quick compatibility checks; always defer to the policy
files for enforcement and release decisions.
