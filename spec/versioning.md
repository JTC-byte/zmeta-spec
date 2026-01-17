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
