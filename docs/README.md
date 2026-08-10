# docs/ Index

This directory mixes two kinds of documents. This index says which is which
so newcomers read guidance rather than process history.

## Guidance (read these)

Advisory, current-facing documents for users of the standard:

- `zmeta_professional_overview.md`: the narrative overview of what ZMeta is,
  how the stack fits together, and the operating model. Start here when
  evaluating.
- `zmeta_two_node_quickstart.md`: sensor-edge to COP in two gateway
  containers (edge/Pi ingress → compact wire → GCS egress), with the
  honesty-signal cheat-sheet for field debugging.
- `zmeta_mqtt_binding_guidance.md`: carrying ZMeta over MQTT honestly
  (topic shape, retain/tombstone, command traffic).
- `zmeta_vocabulary_crosswalk.md`: mapping common deployment concepts onto
  the locked vocabulary.
- `zmeta_correlation_pattern.md`: cross-sensor correlation using existing
  vocabulary.
- `zmeta_track_lifecycle_pattern.md`: track lifecycle and command-grade
  track adjudication using existing vocabulary.
- `zmeta_contract_to_stack_crosswalk.md`: where each contract rule is
  implemented and tested in the reference stack.
- `zmeta_change_governance.md`: the change process for humans and AI agents
  (governed; manifest-hashed).
- `zmeta_defensive_publication.md`: public prior-art posture (governed;
  manifest-hashed).
- `zmeta_audit_playbook.md`: how audit cycles are run (wave scoping, the
  rule set with per-cycle scoring, sustains and changes).

## Process records (history and audit)

Maintainer working artifacts. Useful for reconstructing why a decision was
made, and not required reading for using the standard:

- `zmeta_refinement_worklog.md`: task-by-task work record (recent sessions
  in the Current Resume Note; completed task sections archived to
  `zmeta_refinement_worklog_archive.md`).
- `zmeta_refinement_handoff.md`: the quick resume point for the current
  refinement effort.
- `zmeta_semantic_contract_lockdown_audit.md` and the dated `s1_*.md` /
  `r1_*.md` files: per-task plan/audit/release records referenced from the
  worklog and, in a few cases, from `conformance/conformance_classes.yaml`
  evidence entries.
- `v*_precut_panel_register.md`: the per-cut pre-release panel record,
  findings and fixes with standalone verification commands, frozen to the
  cut it reviewed.
- `zmeta_doctrine_review_log.md`: the standing pressure log on the guiding
  documents. Entries are point-in-time by design; the log's own "How to
  read this log" header governs interpretation, and status lines are
  authoritative.
- `zmeta_after_action_log.md`: the standing after-action record across
  audit cycles (public half; the private half lives outside the repo).
- `zmeta_live_test_checklist.md`: the staging checklist for the SITL and
  live-fire gates; retires into the playbook once those gates have run.
- `release_checksum_errata.md` and `release_notes_errata.md`: corrections
  to published release records, which are never rewritten in place.
- `diagrams/`, `img/`: supporting assets.
