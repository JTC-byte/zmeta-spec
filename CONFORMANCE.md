# ZMeta Conformance And Compatibility

Status: current-main advisory governance.

This document defines how to describe implementations, forks, extensions, and
claims around ZMeta. It supports interoperability without preventing local
integration or commercial implementation.

## Terms

**ZMeta-conformant** means an implementation validates against a specific
tagged ZMeta release and satisfies the claimed conformance classes, schema,
policy, projection, encoding, and fixture evidence for that release.

**ZMeta-compatible** means an implementation can consume or emit valid ZMeta
events for a specified release without changing the meaning of governed ZMeta
surfaces. Compatibility claims should still cite validation evidence.

**ZMeta-derived** means a work is based on ZMeta material but may not preserve
full compatibility. Derived work is allowed under the license, but it should
not be described as upstream ZMeta unless it satisfies conformance.

**Private dialect** means a downstream variant that changes core semantics,
schemas, event vocabulary, version dispatch, risk semantics, projection
behavior, producer authority, or command safety without upstream governance.
Private dialects may be useful locally, but they are not upstream-compatible
ZMeta.

**Experimental extension** means a version-scoped, registry-tracked extension
that is documented as proposed or experimental and does not become valid under
the locked v1.0 branch unless a versioned governance process explicitly adopts
it.

## Conformance Claims

A useful conformance claim should include:

- ZMeta release tag;
- release manifest hash or release bundle hash;
- schema bundle hash;
- policy bundle hash;
- semantic contract hash;
- claimed conformance classes;
- validation command output or CI link;
- implementation version and commit;
- any unsupported profiles, encodings, event families, or adapters.

Example claim files live in `conformance/claims/`.

## Compatibility Boundaries

Do not claim upstream compatibility if the implementation redefines:

- event family separation;
- `zmeta_version` dispatch;
- event type or subtype vocabulary;
- required schema fields;
- timing quality, lineage, confidence, units, geodesy, or TTL meaning;
- profile projection and precision rules;
- producer authority and external-promotion evidence;
- accepted-risk labels, use limits, or policy decisions;
- command safety, authority, or deconfliction semantics.

Use adapter mappings, policy variants, profiles, namespaced extensions, or
local application logic before changing core semantics.

## Labels

Recommended language:

- "Implements ZMeta vX.Y.Z for Profile L STATE_EVENT and SYSTEM_EVENT."
- "ZMeta-compatible adapter for release vX.Y.Z."
- "Private ZMeta-derived dialect; not upstream-compatible."
- "Experimental extension pending upstream governance."

Avoid language that implies endorsement, certification, or standards-body
approval unless that process has actually occurred.

## Conformance Is Not A Warranty

Conformance means the implementation passed the stated validation evidence for
the stated release and scope. It is not a warranty of operational suitability,
security, exportability, mission approval, or legal clearance.

