# S1-10A - Companion Artifact Roadmap Plan

Date: 2026-05-07

## Summary

This plan defines the companion artifact roadmap for D-004. Companion
artifacts are non-event records that support adoption, certification,
transition, replay, data-rights governance, DevSecOps evidence, training, and
lessons learned. They are outside the ZMeta event envelope.

The semantic contract remains authoritative. ZMeta events carry operational
semantics. Companion artifacts can reference events, schemas, release manifests,
hashes, adapters, conformance classes, and replay files, but they do not create
event semantics, do not make future vocabulary valid, and do not weaken the
core event model.

S1-10A is plan-only. No schemas, policy files, validators, gateway runtime,
adapters, codecs, release tooling, conformance class definitions, extension
registry entries, or event vocabulary were changed.

## A. Current Companion Artifact Landscape

The repository already contains several surfaces that imply companion artifacts
without defining a durable companion artifact model:

- Adapter docs and templates under `adapters/` describe native-to-ZMeta and
  ZMeta-to-native mappings. They are useful implementation guidance, but they
  are not machine-readable adapter manifests.
- Mapping packs under `adapters/mapping-packs/` provide vendor-specific
  mapping examples. They are close to adapter companion artifacts, but they do
  not yet share a common artifact record model.
- `tools/replay.py` can replay JSONL events over UDP using JSON, CBOR, compact,
  or protobuf encoding. The repo has JSONL examples and conformance fixtures,
  but it does not yet have replay bundle manifests that identify scenario
  purpose, timing model, expected results, hashes, or release constraints.
- `conformance/` contains core must-pass/must-fail fixtures, profile projection
  fixtures, encoding-negative fixtures, profile precision fixtures, class
  manifests, and example claims. These are strong conformance artifacts, but
  they are not packaged as reusable test evidence bundles.
- `release/zmeta-release-manifest.yaml` provides a governed baseline for core
  ZMeta stack artifacts. It intentionally excludes future companion artifacts
  unless a later release explicitly lists them.
- `spec/extension-registry.yaml` reserves companion artifact names such as
  `ADAPTER_MANIFEST`, `REPLAY_BUNDLE_MANIFEST`, `VENDOR_SCORECARD`,
  `DATA_RIGHTS_PROFILE`, `DEVSECOPS_EVIDENCE_BUNDLE`,
  `LESSONS_LEARNED_GRAPH`, and `TTP_TRAINING_PACKAGE`. These entries are
  reserved companion concepts, not current event vocabulary.
- `spec/semantics-contract.md` explicitly warns that data-rights, DevSecOps,
  TTP, lessons-learned material, replay bundle manifests, model cards, SBOMs,
  and package attestations should remain companion artifacts unless a future
  governed event-level reference is approved.
- Release asset tooling under `release/` supports checksums, release notes,
  bundles, and signatures. Formal release tag/signature/attestation packaging
  remains D-012.

What remains undefined:

- a human-readable companion artifact specification;
- a machine-readable artifact type registry;
- common artifact record fields and status rules;
- example companion artifacts;
- a companion artifact validator;
- optional conformance runner integration;
- a strategy for capability package indexes and future release-manifest
  inclusion.

## B. Problem Statement

ZMeta needs companion artifacts because operational adoption requires more than
valid events and schemas. A unit, vendor, program office, or sprint team needs
to know what adapter was used, what native format was mapped, what tests passed,
what replay data supports validation, what data rights apply, what supply-chain
evidence exists, what model generated outputs, what limitations remain, and
what training or transition material accompanies the capability.

These records should not be placed into core event payloads. Embedding them in
events would:

- bloat operational event packets and harm Profile L/M/H behavior;
- confuse event semantics with certification artifacts;
- mix operational data with acquisition, data-rights, and IP metadata;
- make event consumers parse artifacts they should be able to ignore;
- risk treating vendor scorecards or DevSecOps evidence as operational truth;
- lose adapter provenance when docs drift from implementations;
- prevent replay bundles from being reused as scenario evidence;
- make future events depend on uncontrolled external files;
- make future vocabulary appear valid before versioned adoption.

Companion artifacts solve this by remaining adjacent, hashable, auditable, and
referenceable without becoming event semantics.

## C. Companion Artifact Principles

- Companion artifacts are outside the core ZMeta event envelope.
- Companion artifacts do not create event semantics.
- Companion artifacts do not make future vocabulary valid.
- Companion artifacts may reference ZMeta events, schemas, release manifests,
  hashes, conformance classes, extension registry entries, adapters, and replay
  bundles.
- Companion artifacts must be versioned, hashable, and auditable.
- Companion artifacts should use stable IDs where lifecycle tracking matters.
- Companion artifacts should be safe to ignore by event consumers.
- Companion artifacts should support transition, certification, reuse, replay,
  sustainment, and vendor-neutral comparison.
- Companion artifacts should remain vendor-neutral unless an artifact type is
  intentionally vendor-scoped, such as a vendor scorecard.
- Companion artifacts should support FORGE capability packages without turning
  ZMeta into an acquisition metadata schema.

## D. Companion Artifact Taxonomy

Required artifact families:

- `adapter_manifest`: adapter identity, native format, mapping behavior,
  validation evidence, and limitations.
- `replay_bundle_manifest`: scenario identity, event files, timing model,
  expected validation results, hashes, and release constraints.
- `test_evidence_bundle`: commands run, results, conditions, claims, and
  transition recommendation.
- `vendor_scorecard`: vendor-neutral capability, conformance, rights,
  DevSecOps, transition, and sustainment evidence.
- `data_rights_profile`: government purpose rights, limited rights, open-source
  licensing, model/API rights, and transition implications.
- `devsecops_evidence_bundle`: SBOM, scans, signing metadata, provenance,
  build inputs, and hardening notes.
- `model_card_or_ai_assurance_card`: model identity, intended use, metrics,
  known failure modes, replay/red-team evidence, and confidence behavior.
- `ttp_training_package`: operator audience, procedures, degraded-mode
  guidance, display interpretation, quick references, exercises, and
  evaluation checklists.
- `lessons_learned_graph`: issue, root cause, mitigation, owner, recurrence,
  references, and related artifact IDs.
- `transition_package_manifest`: bill of materials, architecture, adapters,
  replay bundles, evidence, rights, training, sustainment, and handoff
  checklist.
- `deployment_policy_profile`: deployment-selected policy variants, authority
  settings, timing/freshness posture, profile precision overrides, and
  operational constraints.
- `release_attestation_reference`: reference to release manifest, formal
  release checksums/signatures, and post-release claim attestations. D-012
  remains the formal signing/tagging task.

Optional artifact families:

- `sensor_onboarding_manifest`
- `gateway_deployment_manifest`
- `coalition_export_package`
- `operator_display_mapping`
- `exercise_validation_package`
- `capability_package_index`

## E. Common Artifact Record Model

Most companion artifacts should use a common top-level shape:

- `artifact_id`: stable repo-scoped ID, URN, or UUID-style ID.
- `artifact_type`: one registered artifact family.
- `display_name`: human-readable name.
- `version`: artifact version.
- `status`: one status from the artifact status model.
- `owner`: person, team, program, vendor, or maintainer.
- `date_created`: creation date.
- `date_updated`: last update date.
- `zmeta_versions`: related ZMeta versions.
- `related_release_manifest`: release manifest path or hash.
- `related_semantic_contract_hash`: narrow semantic contract hash.
- `related_schema_bundle_hash`: schema baseline hash.
- `related_policy_bundle_hash`: policy baseline hash.
- `related_conformance_classes`: class IDs the artifact supports or references.
- `related_extension_registry_entries`: registry names when relevant.
- `related_adapters`: adapter names or manifest IDs.
- `related_event_ids`: optional event IDs when an artifact references specific
  events.
- `related_replay_bundles`: replay bundle IDs.
- `artifact_hash`: hash of the artifact record or bundle.
- `source_files`: files covered by the artifact.
- `limitations`: known limitations.
- `security_release_notes`: security, release, or handling notes.
- `classification_or_release_marking_placeholder`: placeholder only; not a
  current ZMeta event marking.
- `review_state`: review status, reviewer, or decision.
- `references`: URIs, file paths, standards, or supporting docs.
- `notes`: free text.

Artifact-specific fields should be required only where useful. For example,
`related_event_ids` is optional for an adapter manifest but likely important for
a test evidence bundle or replay bundle.

## F. Artifact Status Model

Recommended statuses:

- `draft`: work in progress and not transition evidence.
- `experimental`: used for exploration or sprint evidence only.
- `validated`: reviewed and tested enough to support capability evidence.
- `transition_ready`: suitable for handoff, adoption, or sustainment planning.
- `superseded`: replaced by a newer artifact but retained for audit.
- `deprecated`: discouraged for new use but retained for compatibility.
- `archived`: retained for historical audit only.
- `rejected`: explicitly not accepted as evidence or current guidance.

Claimability and usage meaning:

- `draft` and `experimental` artifacts are not transition evidence.
- `validated` artifacts may support sprint evidence.
- `transition_ready` artifacts may support handoff or operational adoption.
- `superseded`, `deprecated`, and `archived` artifacts remain auditable but
  should not support new deployments without explicit review.
- `rejected` artifacts must not be used as adoption evidence.

## G. Proposed Artifact Paths

Recommended future structure:

- Human-readable spec: `spec/companion-artifacts.md`
- Machine-readable artifact type registry:
  `companion-artifacts/companion_artifact_types.yaml`
- Adapter manifests: `companion-artifacts/adapter-manifests/`
- Replay bundle manifests: `companion-artifacts/replay-bundles/`
- Test evidence bundles: `companion-artifacts/test-evidence/`
- Vendor scorecards: `companion-artifacts/vendor-scorecards/`
- Data-rights profiles: `companion-artifacts/data-rights/`
- DevSecOps evidence bundles: `companion-artifacts/devsecops-evidence/`
- Model / AI assurance cards: `companion-artifacts/model-cards/`
- TTP / training packages: `companion-artifacts/ttp-training/`
- Lessons-learned graphs: `companion-artifacts/lessons-learned/`
- Transition package manifests: `companion-artifacts/transition-packages/`
- Deployment policy profiles:
  `companion-artifacts/deployment-policy-profiles/`
- Release attestation references:
  `companion-artifacts/release-attestations/`
- Optional capability package indexes:
  `companion-artifacts/capability-packages/`
- Validator: `tools/validate_companion_artifacts.py`
- Tests: `gateway/tests/test_companion_artifacts.py`

The `companion-artifacts/` root is recommended because it keeps these records
separate from `conformance/`, `policy/`, `schema/`, and `release/` while making
their non-event role explicit.

## H. Adapter Manifest Plan

An adapter manifest should capture:

- adapter name;
- adapter version;
- direction: `ingress`, `egress`, or `bidirectional`;
- native format;
- native format version;
- mapped ZMeta event types and subtypes;
- semantic layer mapping;
- field mapping table path;
- unit normalization rules;
- timestamp mapping rules;
- confidence and quality mapping rules;
- lineage behavior;
- profile behavior;
- prohibited field checks;
- conformance tests;
- limitations;
- data-rights or vendor constraints;
- release notes.

Adapter manifests prevent future documentation drift by making the mapping
contract explicit, testable, and versioned. The MAVLink README cleanup showed
why this matters: adapter docs must not teach implementers to place raw
telemetry into STATE_EVENT `payload.features.*`. A manifest can record that
MAVLink platform telemetry maps to state-safe fields, quality metadata,
SYSTEM_EVENT status, OBSERVATION_EVENT where a true supported observation
modality exists, and lineage.

## I. Replay Bundle Manifest Plan

A replay bundle manifest should capture:

- replay bundle ID;
- scenario name;
- event files;
- event count;
- ZMeta versions;
- schema and policy baseline;
- related release manifest/hash;
- timing model;
- source environment;
- synthetic, live, or mixed label;
- red-team injection label;
- expected validation commands;
- expected pass/fail outcomes;
- hash of replay files;
- privacy and release constraints;
- AAR or training use;
- model evaluation use.

Replay labels and scenario identity remain companion artifacts unless a future
versioned event branch adopts replay metadata. Replayed events must not become
indistinguishable from live operational data in operator systems unless replay
mode is explicit outside the event stream.

## J. Test Evidence Bundle Plan

A test evidence bundle should capture:

- tested capability;
- test date;
- release manifest hash;
- conformance classes claimed;
- commands run;
- test results;
- operator feedback summary;
- field conditions;
- limitations;
- risk assumptions;
- artifacts produced;
- transition recommendation.

This bundle should point to raw test outputs or summaries without requiring the
core conformance claim file to carry every test artifact inline.

## K. Vendor Scorecard Plan

A vendor-neutral scorecard should capture:

- vendor and product;
- sprint or use case;
- access license terms;
- APIs/SDKs used;
- adapter burden;
- semantic conformance;
- data rights;
- DevSecOps evidence;
- operator utility;
- transition risk;
- lock-in risk;
- cost and sustainment assumptions;
- evidence sources.

Scorecards support decision evidence. They do not guarantee follow-on awards,
do not create ZMeta conformance by themselves, and should not be embedded in
events.

## L. Data Rights / IP Profile Plan

A data-rights profile should capture:

- government purpose rights;
- limited rights;
- proprietary restrictions;
- open-source licenses;
- training data rights;
- model weight rights;
- adapter reuse rights;
- API dependency risks;
- export and release restrictions;
- transition implications.

This profile should be reviewed by appropriate legal or program stakeholders
before it is used as transition evidence.

## M. DevSecOps Evidence Bundle Plan

A DevSecOps evidence bundle should capture:

- SBOM;
- vulnerability scan results;
- container digest;
- signing metadata;
- build provenance;
- dependency lock files;
- static analysis results;
- runtime hardening notes;
- accreditation/RMF assumptions;
- rollback plan;
- known vulnerabilities and mitigations.

Where practical, S1-10B should align with external SBOM formats rather than
inventing a deep SBOM schema inside ZMeta.

## N. Model Card / AI Assurance Card Plan

A model card or AI assurance card should capture:

- model name and version;
- model family;
- training data summary;
- intended use;
- prohibited use;
- input modality;
- output event mapping;
- performance metrics;
- known failure modes;
- drift monitoring plan;
- replay tests passed;
- red-team results;
- lineage requirements;
- confidence behavior.

This does not add AI provenance fields to current v1.0 events. Current v1.0
INFERENCE_EVENT model name/version and lineage remain the event-level
semantics. Broader model assurance remains a companion artifact or future
versioned branch.

## O. TTP / Training Package Plan

A TTP or training package should capture:

- operator audience;
- supported use case;
- setup steps;
- operating procedures;
- degraded-mode guidance;
- display interpretation;
- confidence and lineage interpretation;
- safety, legal, and cyber assumptions;
- quick reference cards;
- exercise scripts;
- evaluation checklist.

Training packages should help operators use ZMeta outputs correctly without
turning training content into event semantics.

## P. Lessons-Learned Graph Plan

Lessons should be captured outside the event stream using fields such as:

- lesson ID;
- related sprint;
- related capability package;
- related artifact IDs;
- observed issue;
- root cause;
- fix or mitigation;
- status;
- owner;
- recurrence indicator;
- related conformance class or policy;
- references.

This avoids turning ZMeta events into a knowledge graph while preserving
traceability across sprints, fixes, and evidence packages.

## Q. Transition Package Manifest Plan

A transition package manifest should capture:

- problem statement;
- capability summary;
- architecture;
- bill of materials;
- adapter manifests;
- replay bundles;
- test evidence;
- DevSecOps evidence;
- data-rights profile;
- training/TTP package;
- sustainment owner;
- procurement language;
- risks and limitations;
- handoff checklist.

Transition packages should assemble companion artifacts into an adoption-ready
package without changing event schemas or conformance class semantics.

## R. Relationship to Release Manifest / D-002

The release manifest governs the approved ZMeta stack baseline: semantic
contract, schemas, policies, registry, conformance classes, projection
fixtures, encoding-negative fixtures, precision policy, encoding specs, release
policy, tools, and claims.

Companion artifacts may reference release manifest hashes. They should be
hashable and may be included in future capability package manifests. They
should not automatically change the core release bundle hash unless a release
intentionally selects them as release artifacts.

D-002 is closed. Formal tag/signature/attestation packaging remains D-012.

## S. Relationship to Extension Registry / D-003

The extension registry governs future vocabulary. Companion artifacts do not
make future vocabulary valid. They may document candidate future work, evidence,
or adoption context, but they cannot implement event fields or subtypes.

Future event references to companion artifact IDs require a versioned branch
with schema, policy, adapter/gateway, encoding, documentation, and conformance
coverage. That work remains under D-003.

## T. Relationship to FORGE Capability Packages

Companion artifacts support FORGE-style capability outputs by organizing:

- standards references;
- adapters and mapping manifests;
- replay and test assets;
- transition package manifests;
- vendor bench evidence;
- DevSecOps and data-rights evidence;
- training and TTP;
- lessons learned.

The goal is to help a capability move from sprint evidence to transition
package without bloating ZMeta events or encoding acquisition metadata into
operational payloads.

## U. Validator / Tooling Plan

S1-10B should implement `tools/validate_companion_artifacts.py`.

The validator should:

- load the artifact type registry;
- validate example artifacts;
- validate required fields by artifact type;
- validate known status values;
- validate referenced release manifests where present;
- validate referenced conformance classes where present;
- validate referenced extension registry entries where present;
- validate artifact hashes where present;
- fail missing required fields;
- fail unknown artifact types;
- fail invalid status values;
- fail references that treat future vocabulary as current;
- support `--quiet`.

Optional integration:

```powershell
python tools\validate_conformance.py --strict --companion-artifacts
```

The integration should be opt-in. Default strict conformance should remain
unchanged.

## V. Example Artifact Set for S1-10B

S1-10B should keep the initial example set small:

- one example adapter manifest, preferably CoT or MAVLink;
- one example replay bundle manifest;
- one example test evidence bundle;
- one example data-rights profile;
- one example DevSecOps evidence bundle;
- one example transition package manifest.

Examples should be minimal, clearly labeled as examples/reference templates,
and not treated as operational certifications.

## W. Conformance Class Impact

S1-10A should not add a new conformance class.

S1-10B may either:

- leave conformance classes unchanged and treat companion artifact validation as
  optional adoption evidence; or
- add a class such as `ZMETA-COMPANION-ARTIFACTS` only if the specification,
  artifact type registry, examples, validator, and tests are implemented cleanly
  and the class manifest can validate without reopening D-008.

Preferred approach: do not add a class until S1-10B proves the artifacts and
validator are stable.

## X. S1-10B Implementation Plan

Likely S1-10B files:

- `spec/companion-artifacts.md`
- `companion-artifacts/companion_artifact_types.yaml`
- `companion-artifacts/adapter-manifests/example-cot-ingress.yaml`
- `companion-artifacts/replay-bundles/example-replay-bundle.yaml`
- `companion-artifacts/test-evidence/example-test-evidence.yaml`
- `companion-artifacts/data-rights/example-data-rights-profile.yaml`
- `companion-artifacts/devsecops-evidence/example-devsecops-evidence.yaml`
- `companion-artifacts/transition-packages/example-transition-package.yaml`
- `tools/validate_companion_artifacts.py`
- `gateway/tests/test_companion_artifacts.py`
- `tools/validate_conformance.py`
- `spec/README.md`
- `conformance/README.md`
- `docs/zmeta_refinement_worklog.md`
- `docs/zmeta_refinement_handoff.md`

Optional if the initial scope remains small:

- `companion-artifacts/vendor-scorecards/example-vendor-scorecard.yaml`
- `companion-artifacts/model-cards/example-model-card.yaml`
- `companion-artifacts/ttp-training/example-training-package.yaml`
- `companion-artifacts/lessons-learned/example-lessons-learned.yaml`
- `companion-artifacts/deployment-policy-profiles/example-deployment-policy-profile.yaml`
- `companion-artifacts/capability-packages/example-capability-package-index.yaml`

S1-10B should avoid touching event schemas, policy enforcement, gateways,
codecs, and adapter runtime behavior unless a tiny documentation reference is
needed.

## Y. S1-10B Acceptance Criteria

S1-10B should be accepted only if:

- no schemas changed;
- semantic contract unchanged;
- extension registry unchanged;
- no new event vocabulary;
- companion artifact spec exists;
- machine-readable artifact type registry exists;
- example artifacts exist;
- validator exists;
- validator passes valid examples;
- validator fails invalid examples in tests;
- optional conformance flag works if implemented;
- release manifest remains valid;
- conformance claims remain valid;
- companion artifacts remain outside the core event envelope;
- D-004 remains implemented pending S1-10C audit, not closed in S1-10B.

## Z. Risks and Open Questions

- Should companion artifact IDs be globally unique UUIDs, URNs, or repo-scoped
  IDs?
- Should companion artifacts be included in future release manifests or separate
  capability package manifests?
- Do classified or restricted artifacts require a private companion manifest?
- Do vendor scorecards create procurement sensitivity that requires a separate
  handling model?
- Do data-rights profiles require legal review before any `validated` or
  `transition_ready` status?
- Should DevSecOps evidence follow external SBOM standards such as SPDX or
  CycloneDX rather than a ZMeta-specific structure?
- Should replay bundles be signed under D-012?
- Should lessons-learned graphs be machine-readable in S1-10B or deferred?
- Do companion artifacts need their own conformance class, or should they remain
  optional adoption evidence?
- Should capability packages get their own manifest hash that references, but
  does not change, the core release manifest hash?

## Recommended Next Work Item

S1-10B - Companion Artifact Roadmap Implementation.
