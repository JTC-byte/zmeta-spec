# ZMeta Versioning

## Semantic version rules

- 1.0.x: clarifications and fixes (no semantic changes)
- 1.1+: backward-compatible extensions
- 2.0: breaking changes

## Backward compatibility expectations

- Minor and patch releases must not invalidate existing 1.x payloads.
- Optional fields may be added; required fields may not be removed or redefined.

## Deprecation policy

- Deprecated fields remain supported for at least one minor release cycle.
- Removal occurs only in a major version bump.

## Vendor guidance

- Pin schema and policy to a tagged release (e.g., v1.0.0), not the main branch.

## Component Versioning (Schema vs Policy vs Mapping)

- `zmeta_version` tracks **schema + semantics**. Bump when fields or meanings change.
- `policy/` updates can tighten or loosen enforcement without changing the schema.
  Policy changes must be documented in `CHANGELOG.md` and reviewed during release.
- `compact_version` (in `spec/compact-binary-mapping.md`) tracks the compact wire mapping.
  Bump when integer key maps or enum mappings change.

Recommended change handling:
- **Patch**: Clarifications and docs only, no rule changes.
- **Minor**: Backward‑compatible additions (new optional fields, new enums).
- **Major**: Breaking changes (required fields, removed fields, semantics shifts).

When `compact_version` changes, gateways should be updated before producers
so they can decode both versions during a transition.
