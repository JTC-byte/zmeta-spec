# docs/ Index

This directory mixes two kinds of documents. This index says which is which
so newcomers read guidance, not process history.

## Guidance (read these)

Advisory, current-facing documents for users of the standard:

- `zmeta_professional_overview.md` — the narrative overview of what ZMeta is,
  how the stack fits together, and the operating model. Start here when
  evaluating.
- `zmeta_mqtt_binding_guidance.md` — carrying ZMeta over MQTT honestly
  (topic shape, retain/tombstone, command traffic).
- `zmeta_vocabulary_crosswalk.md` — mapping common deployment concepts onto
  the locked vocabulary.
- `zmeta_correlation_pattern.md` — cross-sensor correlation using existing
  vocabulary.
- `zmeta_contract_to_stack_crosswalk.md` — where each contract rule is
  implemented and tested in the reference stack.
- `zmeta_change_governance.md` — the change process for humans and AI agents
  (governed; manifest-hashed).
- `zmeta_defensive_publication.md` — public prior-art posture (governed;
  manifest-hashed).

## Process records (history and audit)

Maintainer working artifacts. Useful for reconstructing why a decision was
made; not required reading for using the standard:

- `zmeta_refinement_worklog.md` — task-by-task work record (recent sessions
  in the Current Resume Note; completed task sections archived to
  `zmeta_refinement_worklog_archive.md`).
- `zmeta_refinement_handoff.md` — the quick resume point for the current
  refinement effort.
- `zmeta_semantic_contract_lockdown_audit.md` and the dated `s1_*.md` /
  `r1_*.md` files — per-task plan/audit/release records referenced from the
  worklog and, in a few cases, from `conformance/conformance_classes.yaml`
  evidence entries.
- `diagrams/`, `img/` — supporting assets.
