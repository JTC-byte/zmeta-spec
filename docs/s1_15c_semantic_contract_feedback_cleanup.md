# S1-15C Semantic Contract Feedback Cleanup

Date: 2026-06-08

## Purpose

S1-15C applies feedback on the S1-15A/S1-15B risk-governance update. The goal is
to align the semantic contract text, conformance classes, claims, and crosswalk
with the stack behavior already implemented in S1-15B.

This pass does not add runtime behavior or promote future vocabulary.

## Changes Made

- Revised Section 3.3 so material accepted-risk events MUST carry compact
  self-labels or policy references when diagnostics may not travel.
- Clarified that degradation effects must respect event-type confidence rules.
  Events that prohibit top-level confidence must use diagnostics, use limits,
  TTL/routing limits, quality metadata where valid, or future approved fields.
- Strengthened operator/deployment override requirements for material,
  command-related, trust-related, promotion-related, safety-related, and
  external-boundary policy softening.
- Added governed-vocabulary guidance for risk dimensions, policy decisions,
  reason codes, and allowed/prohibited use labels.
- Revised Section 4.5.1 to acknowledge the lineage gap when external reports
  have no ZMeta parent event, while keeping `OBSERVATION_EVENT/NETWORK_REPORT`
  as future-only vocabulary.
- Revised Section 7.9 to identify future `POLICY_ADJUDICATION` or
  `POLICY_DIAGNOSTIC` as cleaner policy diagnostic vocabulary while preserving
  SCHEMA_VIOLATION as the v1.0 compatibility envelope.
- Revised Section 14 so CoT/TAK ingress is external report evidence unless
  active promotion policy authorizes `STATE_EVENT` promotion under Section
  4.5.1.
- Updated conformance class text and machine-readable class records for:
  `ZMETA-POLICY-ADJUDICATION`, `ZMETA-EXTERNAL-PROMOTION`,
  `ZMETA-RISK-FILTERING`, and future `ZMETA-PROJECTION-ORIGIN`.
- Updated the example reference gateway claim to include the new implemented
  risk-governance classes.
- Updated the implementation mapping, change log, and crosswalk rows so
  implementers see the new risk/promotion/filtering surfaces.

## Future-Only Items Preserved

The following remain future branch work and are not valid v1.0 vocabulary:

- `OBSERVATION_EVENT/NETWORK_REPORT` or equivalent external-report evidence
  subtype.
- `SYSTEM_EVENT/POLICY_ADJUDICATION` or equivalent clearer policy diagnostic
  subtype.
- Projection-origin/instance metadata such as `projection_id`,
  `source_event_id`, `projection_policy_id`, and projection reason/status fields.

## Verification

Verification commands are recorded in `docs/zmeta_refinement_worklog.md`.
