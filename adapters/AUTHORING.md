# ZMeta Adapter Authoring Guide

Status: current-main advisory (Class A). Non-normative — if anything here
conflicts with `spec/semantics-contract.md`, the canonical schemas, or
`policy/`, those win (authority stack: `docs/zmeta_change_governance.md`).

Audience: a human developer or an AI coding agent building a NEW adapter
against a pinned ZMeta release. This page consolidates the operational path
that is otherwise spread across `adapters/README.md`,
`adapters/ingress/template/README.md`, `conformance/README.md`, and
`tools/README.md`. It adds no new rules; section 9 additionally carries
review-derived authoring lessons.

## 0. Orient

- Pin a tagged release (`git checkout vX.Y.Z`). Do not build against a moving
  `main`.
- Read, in order: `adapters/README.md` (semantic mapping rules, frame
  assertions, anti-fabrication), `adapters/ingress/template/README.md`
  (required functions and behavior), then the semantics-contract sections for
  your event family: 3.4 adapter/gateway enforcement, 4.4 layer separation,
  4.5/4.5.1 producer authority and external promotion, 4.8 lineage, 6
  units/geodesy/bearings/timestamps, 7.1 envelope confidence rules, 7.3
  subtypes, 7.7 STATE prohibitions, 7.8 COMMAND safety.
- Install: `python -m pip install -r requirements.txt` (tests:
  `requirements-dev.txt`). Run everything from the repository root; adapters
  use package imports (`PYTHONPATH=.`). Direct execution from inside an
  adapter subdirectory is not supported.

## 1. Know ZMeta's Input Floor

Ingress adapters consume decoded, structured sensor or protocol output:
detections, DoA solutions, PSD sweeps, decoded telemetry dicts, parsed track
reports. The DSP, decoder, or inference stage that produces those runs
upstream of ZMeta. On the ingress side this repository intentionally ships
no raw-IQ, SigMF, or pcap handling and no CoT-XML, MISB 4609, or Link-16
decoders — the CoT/KLV/JREAP ingress templates take pre-parsed dicts, and
literal raw IQ support is recorded future work. (Egress differs:
`adapters/egress/cot/` is a real CoT v2.0 XML encoder.) Link raw captures
with `payload.data_ref` pointer metadata (semantics contract Appendix A) —
never carry raw payload data in-event.

## 2. Choose The Layer

Emit at the layer of what your input IS, never the layer you wish it were
(contract 4.4: no layer may collapse into another). Full mapping table:
`adapters/README.md`. Nearest reference implementation to copy:

| Your input | Emit | Start from |
| --- | --- | --- |
| RF DoA / bearing solution | `OBSERVATION_EVENT` (RF) | `ingress/kraken/` |
| RF peak freq/power scalar | `OBSERVATION_EVENT` (RF) | `ingress/moth/` |
| PSD sweep captures | `OBSERVATION_EVENT` (RF) | `ingress/signalhunter/` |
| Decoded EO/IR metadata | `OBSERVATION_EVENT` (EO) | `ingress/klv/` |
| Classifier/detector claims | `INFERENCE_EVENT` | `ingress/eo-cv/` |
| Track association you compute | `FUSION_EVENT` | `examples/` chains |
| Platform telemetry (own asset) | `STATE_EVENT` + promotion | `ingress/mavlink/` |
| External tactical tracks | `STATE_EVENT` + promotion | `ingress/cot/`, `ingress/jreap/` |
| Mission cueing (egress) | `COMMAND_EVENT` -> intent | `egress/mavlink/` |
| Operator display (egress) | `STATE_EVENT` -> format | `egress/cot/` |
| Health / timing / acks | `SYSTEM_EVENT` | `ingress/mavlink/` |

Worked full chains to pattern-match against:
`examples/zmeta-examples-1.0.jsonl` (RF) and
`examples/zmeta-eo-chain-examples.jsonl` (EO) each show
`OBSERVATION_EVENT -> INFERENCE_EVENT -> FUSION_EVENT -> STATE_EVENT` with
genuine chained `lineage.based_on` ids.

Worked exercise: `adapters/ingress/example-vendor/` is a complete small
adapter implementing the `adapters/mapping-packs/example-vendor-pack`
declarative mapping to this guide's requirements — build your own against the
same pack first if you want a known-good diff.

## 3. The Non-Negotiables

1. **Never fabricate lineage** (contract 4.8). An original observation with no
   ZMeta parent omits `lineage` entirely. Families whose lineage is mandatory
   (INFERENCE/FUSION/STATE) refuse to emit rather than invent a parent id.
2. **Convert or omit reference frames** (contract 6.4). Canonical bearings and
   headings are degrees true north. Without a real heading reference, keep the
   native value in an explicitly named non-canonical field and omit the
   canonical one.
3. **Never fabricate quality metrics.** Omit `quality.snr_db` rather than
   derive it from RSSI; omit bearings for omnidirectional sensors rather than
   invent one with huge error.
4. **`calibration_state` defaults `UNCALIBRATED`.** Assert
   `CALIBRATED`/`DEGRADED` only when the deployment can substantiate it.
5. **Degraded timing stays visible** (contract 5.3).
   `coerce_timing_quality()`'s `UNKNOWN`/`UNSYNCED` fallback is deliberately
   degraded; replace it with source GPS/NTP/PTP metadata when available, never
   with an invented clean value.
6. **External state needs promotion evidence** (contract 4.5.1). CoT, JREAP,
   MAVLink, or vendor-COP ingress emitting `STATE_EVENT` must attach
   `payload.extensions.external_promotion` and a `promote:*` lineage
   transform, or reference policy rejects it. Confidence never increases just
   because an external system reported the track.
7. **Envelope confidence rules** (contract 7.1): `confidence` is required for
   INFERENCE/FUSION/STATE and prohibited for OBSERVATION/COMMAND/SYSTEM.
8. **STATE carries no raw artifacts** (contract 7.7): no `features`,
   `raw_features`, `modality`, `measurement(s)`, `t_start`/`t_end`,
   `data_ref(s)` — enforced recursively. **COMMAND carries no altitude**
   (contract 7.8), requires `requires_deconfliction: true`, a TTL
   (`valid_for_ms`), and an idempotent `task_id`.
9. **Units and geodesy** (contract 6): WGS-84, meters HAE, degrees true
   north, m/s, UTC RFC3339 `Z` timestamps. Canonical geo is all-or-nothing;
   omit missing values — never zero-fill (no `(0,0,0)` sentinels).
10. **Schema minimums are per-subtype.** The locked schema defines required
    feature sets per event family and modality (for example, RF observation
    features require `center_freq_hz`, `bandwidth_hz`, AND `power_dbm`).
    Read your subtype's schema block before deciding any input field is
    optional — requiredness comes from the schema, never from what a sample
    input happens to carry. A reading missing a required field is refused,
    not emitted schema-invalid.

## 4. Build

- Copy `adapters/ingress/template/adapter_template.py` (or the nearest
  reference from the table) and implement `detect(input_bytes) -> schema_id`,
  `translate(input_obj, schema_id) -> list[dict]`,
  `validate(zmeta_event) -> (pass|warn|fail, violations)`.
- Declare an `ADAPTER_VERSION`. When translating with real parents, set
  `lineage.transform = "translate:<schema_id>@<adapter_version>"`.
- Normalize timestamps with `adapters.ingress.time_utils.normalize_utc_z()` /
  `epoch_ms_to_utc_z()`; expose per-event `payload.timing_quality` or periodic
  `TIME_STATUS`.
- Fail closed. Return nothing on ambiguous or unmappable input and emit a
  `SYSTEM_EVENT`/`SCHEMA_VIOLATION` diagnostic for deterministic failures.
- Vendor quirks belong in adapter-local code, a mapping pack
  (`adapters/mapping-packs/` — declarative documentation plus test samples;
  no runtime engine executes `mapping.yaml`), or namespaced payload
  extensions. They must not alter event meaning, units, lineage, authority,
  or command safety.

## 5. Validate — The Ladder

Run from the repository root, narrowest first:

```
# 1. Your colocated unit tests
python -m pytest adapters/ingress/<your-adapter> -q

# 2. Schema + policy validation of emitted events
python tools/validate.py --file <your-events>.jsonl --profile H --strict

# 3. Migration / semantic-honesty pre-check
python tools/check_compat.py <your-events>.jsonl --target <pinned-release>

# 4. Harness fixtures that call your adapter and pin its outputs
python tools/validate_adapter_conformance.py --fixtures <your-fixtures>.jsonl

# 5. Full kernel gate (prove nothing else regressed)
python tools/validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative --precision-policy --release-manifest --release-package --bad-events --adapter-harness
```

Non-Python adapters: steps 2-3 validate your emitted JSONL regardless of
implementation language; the harness (step 4) requires a Python-importable
callable, so wrap or skip it and lean on steps 2-3 plus your own tests.

One-command wrapper: `python tools/check_adapter.py --events <out>.jsonl
--fixtures <fixtures>.jsonl [--kernel-gate]` runs the tool-based steps 2-4
for you (and prints each underlying command as it goes). Your colocated
pytest (step 1) still runs separately, and the kernel gate (step 5) runs
only with `--kernel-gate`. The governed validators remain the authority.

## 6. Harness Fixture Format

`tools/validate_adapter_conformance.py` fixtures are JSONL, one object per
line (worked examples: `conformance/adapter-harness/must-pass.jsonl`). An
advisory JSON Schema for fixture lines lives at
`conformance/adapter-harness/fixture.schema.json`; `tools/check_adapter.py
--fixtures` lints against it before running the harness, catching key typos
early:

| Key | Meaning |
| --- | --- |
| `name` | Fixture label used in output (default `line-<n>`). |
| `module` | Repo-relative path to the adapter module to load. |
| `callable` | Function name to call. |
| `args` / `kwargs` | Arguments passed to the callable. |
| `result` | `"event"` (default, one dict) or `"events"` (list of dicts). |
| `profile` | Validation profile (default `"H"`). |
| `expect` | Expectation object (below). For `result: "events"`, an `expect.events` list applies per-index expectations. |

`expect` keys:

| Key | Meaning |
| --- | --- |
| `event_type` / `event_subtype` | Exact envelope match. |
| `source_producer` | Exact `source.producer` match. |
| `required_paths` / `forbidden_paths` | Dotted paths that must / must not resolve. |
| `expected_values` | Dotted path -> exact value pins. Numeric tolerance 1e-6; booleans never match non-booleans; a missing path is its own failure. |
| `utc_z_paths` | Paths that must be UTC `Z` timestamps (default `["event.ts"]`). |
| `require_lineage_transform` | Default `true` for non-SYSTEM events; set `false` for original observations that legitimately omit lineage. |
| `lineage_transform_prefix` | Required prefix for `lineage.transform` (for example `promote:`). |
| `allow_degraded_timing` | Default `false`: an `UNSYNCED` fallback fails unless explicitly allowed. |
| `requires_external_promotion` / `external_promotion_required_keys` | Assert promotion evidence for external-state projections. |

## 7. Producer Authority Is Deployment Policy

Schema validity is not authorization. Your `source.producer` and
`source.node_role` must be allowed for the family you emit
(`policy/roles.yaml`, `policy/producer-authority.yaml`). The reference
producer names are examples — deployments narrow them to local ids. External
tactical ingress producers additionally carry the per-producer
`external_state_promotion` requirements in that file.

## 8. Definition Of Done

- The validation ladder is green, including the full kernel gate.
- Your fixtures pin the semantics that matter (frame conversion math, omitted
  fields, refusal cases), not just happy-path presence.
- Conformance claims use the vocabulary in `CONFORMANCE.md` and cite the
  pinned release tag plus hashes (`python tools/compute_contract_hash.py`).
- Local/downstream adapters need no upstream changelog/worklog updates
  (`docs/zmeta_change_governance.md`, downstream clone limits). Contributing
  the adapter upstream is a Class C change: reference README table row,
  colocated tests, harness fixtures, and changelog/worklog/handoff entries
  together.

## 9. Notes For AI Agents

- Decide from the contract text in this pinned checkout, not from memory or
  training priors. When this guide and the contract disagree, the contract
  wins.
- When a semantic mapping is ambiguous, refuse to emit and record the open
  question; never guess a mapping to make output appear.
- Do not redefine locked surfaces (event vocabulary, version dispatch,
  required fields, units, lineage/confidence meaning, promotion evidence,
  command safety) — see `AGENTS.md` downstream-clone rules. Local changes to
  those surfaces create a private dialect.
- Work from the repository root; keep adapters importable as packages; run
  the ladder exactly as written before claiming the adapter is done.

Four failure modes proven by this guide's first external review pass
(2026-07-16) — each escaped an author whose schema validation was green:

- **Author from primaries, not summaries.** When your artifact mirrors or
  cites a file (a reference adapter, a schema block), open that file and
  diff against it. Conventions like a bounding-box coordinate format live in
  docstrings that secondhand summaries drop, and schema validation cannot
  catch dialect drift in free-form fields.
- **Prove fail-closed claims with refusing inputs.** For every field the
  schema requires, write the test where it is missing and assert refusal —
  one per required field, not one sampled field. Green-path validation
  alone let a teaching adapter emit schema-invalid events on the exact rule
  it taught.
- **Run this guide as a checklist against your own adapter** before calling
  it done. An exemplar that violates the rule it teaches fails review.
- **Record validation evidence exactly.** Name the command and target you
  actually ran, invoked in a state where it can fail — a diff check is
  `git diff --check <base>...HEAD`, not a bare clean-worktree check that
  can never trip. A false validation claim in a commit message is an
  evidence-integrity defect, not a formatting nit.
