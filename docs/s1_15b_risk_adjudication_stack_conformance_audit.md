# S1-15B Risk Adjudication Stack Conformance Audit

Date: 2026-06-08

## Result

The stack now conforms to the S1-15A risk adjudication semantic baseline:

- Locked interoperability surfaces remain strict: schema shape, event families,
  version dispatch, UUID/timestamp rules, command safety, lineage presence,
  unit explicitness, and layer separation.
- Tunable operational behavior is explicit and filterable: timing freshness,
  lineage soft warnings, external promotion, and gateway runtime degradation now
  carry `risk_dimension`, `policy_mode`, `policy_decision`, policy reference,
  allowed/prohibited uses, and applied effects where data is still accepted.
- Bandwidth efficiency is preserved: the changes use existing diagnostics and
  compact event-side labels instead of duplicating source payloads.
- No tracked rogue/stale files were found. Local generated/cache artifacts are
  ignored by `.gitignore` and are not part of the live repository contract.

## Semantic Rule Split

The audit used the S1-15A rule split:

- Locked: formatting, schema validity, discriminator consistency, event layer
  separation, version boundaries, command safety, required confidence/lineage,
  and raw-feature/state separation.
- Tunable: timing freshness response, unresolved-lineage handling, external
  promotion response, warning strictness, runtime failure-mode degradation, and
  profile-local operational thresholds.
- Advisory: local notes, release history, future roadmap docs, deployment
  examples, and generated release artifacts.

Tunable behavior may accept degraded data, but it must not hide that acceptance.

## Folder Audit

### Root

- `.github/workflows/ci.yml`: retained as live CI surface from S1-13A; no new
  risk-adjudication logic needed.
- `.gitignore`: already excludes `LOCAL_NOTES.md`, `.gitconfig-local`,
  `__pycache__/`, pytest scratch directories, release zips, smoke outputs, and
  local package artifacts.
- `README.md`, `CHANGELOG.md`, `RELEASE_CHECKLIST.md`, `Makefile`,
  `requirements*.txt`, `pytest.ini`, `LICENSE`: retained; no semantic drift
  found for risk adjudication.
- `zmeta_cbor.py`, `zmeta_compact.py`, `zmeta_proto.py`, `zmeta_uuid.py`:
  encoding/identity helpers. No change required because risk labels ride in
  ordinary event JSON/extension fields and compact unknown metric keys are
  preserved.
- Ignored local files/directories observed: `LOCAL_NOTES.md`, `.gitconfig-local`,
  `.tmp`, `.pytest_work`, `pytest-cache-files-*`, `__pycache__/`, and generated
  release zips. These are expected local state, not tracked stack artifacts.

### `adapters/`

- Ingress CoT/JREAP/MAVLink adapters already implement S1-14 external promotion
  metadata and tests. No payload duplication was added.
- `adapters/ingress/template/README.md` now tells adapter authors to emit
  diagnostic warnings/failures with risk labels when soft acceptance is used.
- Other ingress adapters (`eo-cv`, `kraken`, `klv`, `moth`, `signalhunter`) and
  egress adapters (`cot`, `jreap`, `klv`, `mavlink`) remain valid because they
  preserve semantic layers and do not own risk-adjudication policy.
- Mapping-pack files remain examples of deterministic translation; no stale
  semantic override found.

### `configs/`

- Edge configs remain deployment examples. They expose operational controls such
  as `failure_modes`, strict validation, stripping optional fields, and encoding
  selection.
- `configs/README.md` now clarifies that runtime degradation must leave risk
  labels on accepted events.
- Policy variants remain local override examples and are not the reference
  contract baseline.

### `conformance/`

- `conformance/must-pass.jsonl` now includes a passing warning diagnostic with
  risk labels for `TIMING_STATUS_UNSYNCED`.
- Existing external-promotion negative fixtures remain valid: invalid promoted
  external state still fails by default.
- Projection, precision, encoding-negative, class, and claim fixtures remain
  sidecar conformance surfaces; no schema/vocabulary loosening was found.
- `conformance/README.md` now documents filterable soft-acceptance fixtures.

### `deploy/`

- Docker Compose deployment wrappers have no semantic-contract logic. No
  risk-adjudication edits required.

### `docs/`

- Docs are intentional audit artifacts and should remain tracked because ZMeta
  treats auditability as part of the project philosophy.
- This S1-15B document records the folder-level and file-level conformance pass.
- Running handoff/worklog files will point to this audit after validation.

### `examples/`

- Example event JSONL files remain schema/policy examples. No new example event
  was required because conformance already carries the new risk-diagnostic
  fixture.

### `gateway/`

- `gateway/src/validators.py` is the primary conformance surface. It now
  normalizes risk details for timing, lineage, and external promotion decisions.
- `apply_timing_freshness_degradation()` and
  `apply_external_promotion_policy_action()` now stamp accepted events with
  `payload.extensions.risk_adjudication` when confidence/TTL changes are
  applied.
- `gateway/src/gateway.py` now stamps runtime timing-loss degradation with the
  governed `TIMING_STATUS_UNSYNCED` risk record instead of silently lowering
  confidence.
- Focused tests were added/updated for timing freshness, lineage semantics,
  external promotion, and gateway smoke behavior.
- `gateway/README.md` now documents warning diagnostics and event-side risk
  labels for soft acceptance.

### `policy/`

- `policy/timing-freshness.yaml` now declares `use_limits` for warn/degrade
  timing decisions.
- `policy/lineage.yaml` now declares `use_limits` for lineage warnings.
- `policy/producer-authority.yaml` now declares `use_limits` for warn, degrade,
  and quarantine external-promotion decisions.
- `policy/semantics.yaml`, `policy/violation-codes.yaml`, and both versioned
  schemas now include `TIMING_STATUS_UNSYNCED` as governed diagnostic
  vocabulary.
- `policy/README.md` now explains use limits and the requirement that soft
  acceptance remain labeled.

### `release/`

- Release notes, checksum manifests, signing templates, package templates, and
  historical release files remain intentional tracked release history.
- `release/zmeta-release-manifest.yaml` must be regenerated after governed
  schema/policy/conformance/doc changes.
- Ignored release zips and smoke bundles remain local generated artifacts.

### `schema/`

- v1.0 and v1.1.0 schemas were only updated to admit the new governed
  `TIMING_STATUS_UNSYNCED` diagnostic reason code.
- No event family, subtype, payload structure, or future vocabulary was made
  valid by this pass.

### `source-docs/`

- Source document storage is retained as provenance/audit context. It is not a
  live validation surface and did not need conformance edits.

### `spec/`

- `spec/semantics-contract.md` already contains the S1-15A risk adjudication
  baseline and remained the authority for this pass.
- Encoding specs, release hash policy, extension registry, conformance class,
  projection, and precision docs do not need new semantics for this task.

### `tools/`

- Validation and build tools remain the enforcement/audit harness. No runtime
  risk semantics were moved into tools.
- Release manifest validation and contract hash computation must be rerun after
  this pass because schema/policy/conformance/docs changed.

## File-Level Change Summary

- `gateway/src/validators.py`: added shared risk detail/adjudication helpers;
  wired timing, lineage, and external promotion warnings/degradation to them.
- `gateway/src/gateway.py`: labeled runtime timing-loss degradation.
- `policy/timing-freshness.yaml`, `policy/lineage.yaml`,
  `policy/producer-authority.yaml`: added use-limit policy labels.
- `policy/semantics.yaml`, `policy/violation-codes.yaml`,
  `schema/zmeta-event-1.0.schema.json`, `schema/zmeta-event-1.1.0.schema.json`:
  added governed `TIMING_STATUS_UNSYNCED` diagnostic vocabulary.
- `gateway/tests/test_timing_freshness.py`,
  `gateway/tests/test_external_state_promotion.py`,
  `gateway/tests/test_lineage_semantics.py`,
  `gateway/tests/test_gateway_smoke.py`: asserted risk labels/effects.
- `conformance/must-pass.jsonl`, `conformance/README.md`: added and documented
  a filterable risk diagnostic fixture.
- `policy/README.md`, `gateway/README.md`, `configs/README.md`,
  `adapters/ingress/template/README.md`: documented operator-tunable behavior
  without silent semantic bypass.

## Remaining Posture

No new deferred issue is needed from this pass. The stack still separates
current governed vocabulary from future trust/quarantine/lifecycle concepts:
quarantine is a policy action today, not a schema-level domain state.
