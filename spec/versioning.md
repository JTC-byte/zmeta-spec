# ZMeta Versioning

## Semantic Version Rules

- 1.0.x: clarifications and fixes (no semantic changes)
- 1.1+: backward-compatible extensions
- 2.0: breaking changes

## Backward Compatibility Expectations

- Minor and patch releases must not invalidate existing 1.x payloads.
- Optional fields may be added; required fields may not be removed or redefined.
- A payload that violates a core semantic invariant, such as a non-UUIDv7
  `event_id`, is not considered compliant for compatibility purposes.

## Deprecation Policy

- Deprecated fields remain supported for at least one minor release cycle.
- Removal occurs only in a major version bump.

## Vendor Guidance

- Pin schema and policy to a tagged release, not the main branch.
- Prefer adapters, policy/config, profiles, and namespaced extensions for local
  integration. A local change to schema, event vocabulary, version dispatch, or
  semantic meaning is a private dialect unless it is versioned, documented,
  covered by conformance evidence, and released through governance.

## Component Versioning

- `zmeta_version` tracks **schema + semantics**. Bump when fields or meanings change.
- Normative schemas require exact `zmeta_version` values. Compatibility aliases
  such as `1.1` must be normalized by adapters before schema validation, not
  accepted inside the canonical schema.
- `policy/` updates can tighten or loosen enforcement without changing the schema.
  Policy changes must be documented in `CHANGELOG.md` and reviewed during release.
- `compact_version` (in `spec/compact-binary-mapping.md`) tracks the compact CBOR
  wire mapping. Bump when integer key maps or enum mappings change.
- Protobuf field numbers in `schema/proto/zmeta_event_v1.proto` are experimental
  until protobuf encoding is promoted to stable/reference status. Once promoted,
  field numbers must not be reused.

Recommended change handling:
- **Patch**: Clarifications and docs only, no rule changes.
- **Minor**: Backward-compatible additions (new optional fields, new enums, new
  experimental encoding projections).
- **Major**: Breaking changes (required fields, removed fields, semantics shifts).

When `compact_version` changes, gateways should be updated before producers so
they can decode both versions during a transition.
