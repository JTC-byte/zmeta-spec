# ZMeta Adapter Authoring Guide

Status: current-main advisory (Class A). Non-normative: if anything here
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
decoders. The CoT/KLV/JREAP ingress templates take pre-parsed dicts, and
literal raw IQ support is recorded future work. (Egress differs:
`adapters/egress/cot/` is a real CoT v2.0 XML encoder.) Link raw captures
with `payload.data_ref` pointer metadata (semantics contract Appendix A).
Never carry raw payload data in-event.

## 2. Choose The Layer

Emit at the layer that describes what your input is, never the layer you wish
it were
(contract 4.4: no layer may collapse into another). Full mapping table:
`adapters/README.md`. Nearest reference implementation to copy:

| Your input | Emit | Start from |
| --- | --- | --- |
| RF DoA / bearing solution | `OBSERVATION_EVENT` (RF) | `ingress/kraken/` |
| RF peak freq/power scalar | `OBSERVATION_EVENT` (RF) | `ingress/moth/` |
| PSD sweep captures | `OBSERVATION_EVENT` (RF) | `ingress/signalhunter/` |
| Cooperative-broadcast decoded telemetry (ADS-B, AIS, rtl_433-class decoders) | `OBSERVATION_EVENT` (NETWORK) | `ingress/adsb/`, `ingress/ais/` |
| Decoded EO/IR metadata | `OBSERVATION_EVENT` (EO) | `ingress/klv/` |
| Classifier/detector claims | `INFERENCE_EVENT` | `ingress/eo-cv/` |
| Multi-layer vendor reports (fact + opinion in one message) | split: `OBSERVATION_EVENT` + per-claim `INFERENCE_EVENT` | `ingress/sapient/` |
| Registration/capability-declared formats (units codex, node types) | per node type; refuse unregistered nodes rather than fabricate a modality | `ingress/sapient/` (RegistrationStore) |
| Track association you compute | `FUSION_EVENT` | `examples/` chains |
| Platform telemetry (own asset) | `STATE_EVENT` + promotion | `ingress/mavlink/` |
| External tactical tracks | `STATE_EVENT` + promotion | `ingress/cot/`, `ingress/jreap/` |
| Mission cueing (egress) | `COMMAND_EVENT` -> intent | `egress/mavlink/`, `egress/sapient/` |
| Operator display (egress) | `STATE_EVENT` -> format | `egress/cot/` |
| Coalition/enclave export (egress) | `STATE_EVENT` -> external standard, risk-labeled, fail-closed | `egress/sapient/` |
| Health / timing / acks | `SYSTEM_EVENT` | `ingress/mavlink/` |

External-promotion metadata is caller-owned end-to-end: `loop_status` (the
reflection-check verdict) must arrive message-carried or caller-supplied and
is NEVER defaulted by an adapter. The check is a verification the adapter
does not perform, so stamping its verdict would fabricate evidence (contract
4.5.1; ratified in the SAPIENT pack and enforced by every promotion
template). Promotion dicts are allowlisted to the enumerated promotion
vocabulary; raw measurements or unenumerated keys refuse the promotion.

Worked full chains to pattern-match against:
`examples/zmeta-examples-1.0.jsonl` (RF) and
`examples/zmeta-eo-chain-examples.jsonl` (EO) each show
`OBSERVATION_EVENT -> INFERENCE_EVENT -> FUSION_EVENT -> STATE_EVENT` with
genuine chained `lineage.based_on` ids.

Which lineage pattern to copy: `lineage.transform` stamps a translation or
promotion step. An adapter converting a native message records
`translate:<schema_id>@<adapter_version>`, external-state promotion records
`promote:*`. Native ZMeta producers emitting original observations perform
no such step and carry no transform (an original reading with no ZMeta
parent omits `lineage` entirely). That is why the RF chain's events carry
only genuine `based_on` links while the EO chain's INFERENCE event, produced
by the eo-cv translator from a native detection, carries `transform` too.
The harness defaults `require_lineage_transform: true` because adapter
output normally IS a translation step; a fixture legitimately sets it
`false` only for original observations that omit lineage.

Worked exercise: `adapters/ingress/example-vendor/` is a complete small
adapter implementing the `adapters/mapping-packs/example-vendor-pack`
declarative mapping to this guide's requirements. Build your own against the
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
   `data_ref(s)`, enforced recursively. **COMMAND carries no altitude**
   (contract 7.8), requires `requires_deconfliction: true`, a TTL
   (`valid_for_ms`), and an idempotent `task_id`.
9. **Units and geodesy** (contract 6): WGS-84, meters HAE, degrees true
   north, m/s, UTC RFC3339 `Z` timestamps. Under the locked v1.0 kernel,
   canonical geo is all-or-nothing: omit missing values rather than
   zero-filling them (no `(0,0,0)` sentinels), and a position with no usable
   altitude cannot become canonical `geo` at all. The v1.1.0 branch adds a
   declared-dimensionality exception (contract 21.8, doctrine A1-02): `geo`
   may carry an explicit `dimensionality: "2D"`, which prohibits `alt_m`
   entirely and pairs with `quality.geo_status: VERTICAL_UNAVAILABLE`; absent
   `dimensionality` still means `"3D"` and still requires `alt_m`. Use the
   declared-2D form for a source whose horizontal fix is real and exact with
   no geometric vertical to assert (a surface vessel, a barometric-only
   aircraft), never zero or a geoid guess. See `adapters/ingress/adsb/README.md`
   and `adapters/ingress/ais/README.md` for worked implementations.
10. **Schema minimums are per-subtype.** The locked schema defines required
    feature sets per event family and modality (for example, RF observation
    features require `center_freq_hz`, `bandwidth_hz`, AND `power_dbm`).
    Read your subtype's schema block before deciding any input field is
    optional. Requiredness comes from the schema, never from what a sample
    input happens to carry. A reading missing a required field is refused,
    not emitted schema-invalid.

Two declared-sentinel conventions to keep distinct from fabrication:
receiver-class RF sensors that physically cannot measure emitter bandwidth
satisfy the schema-required RF feature set with the documented
`bandwidth_hz: 0.0` sentinel (the kraken, moth, and signalhunter READMEs
document it), and FFT-derived detections that measure an analysis window
rather than emitter bandwidth may report the documented FFT-bin-width
convention (the edge-comms-bladerf pack documents it). Both are declared
sentinels: fixed, documented, consumer-visible conventions rather than invented
measurements. Any adapter using one must document it in its own README.
A frame-unlabeled native bearing is the mirror case: never promote it to
canonical `payload.bearing` with a minted `TRUE_NORTH` assertion the
producer did not make. Keep it in explicitly named
`features.native_bearing_*` fields until a producer frame assertion exists
(the edge-comms-bladerf pack models this demotion). Inventing measurement
values (default bearings, error bounds, power levels, positions) remains
prohibited by rules 3, 9, and 10.

## Residue Classes A Zero-Shot Author Should Assume

The rules above get violated in the same handful of concrete shapes often
enough that this repository's own fix history is worth reading as a
checklist, not just as background. Each item below cost a real fix here;
check your adapter against it before calling it done.

- **Message-type-scoped sentinels.** A wire format's own "value not
  reported" encoding is not missing data, and it is not a value to carry
  either; it is a fact about the field, and it can differ by message type
  within the same format. AIS message type 27 packs speed and course into
  narrower fields with their own not-available encodings (`63` kt, `511`
  degrees), distinct from every other position-report type's (`102.3` kt,
  `360.0` degrees). `ingress/ais/ais_to_zmeta.py` reads `POSITION_REPORT_TYPES`
  next to `SOG_NOT_AVAILABLE` / `TYPE27_SOG_NOT_AVAILABLE` for this reason.
  Read the standard's not-available table for each message type your adapter
  accepts, next to the code path that accepts that type, not once for the
  format as a whole.
- **Epoch-floor plus calendar validation on every time channel.** A number
  under a field named `timestamp` is epoch seconds only if it is plausibly
  epoch seconds. `ingress/ais/ais_to_zmeta.py`'s `EPOCH_FLOOR_S` (2000-01-01)
  refuses values below it rather than dating an event near 1970-01-01,
  because some other quantity (AIS's own second-of-minute field is the live
  example) leaked in under that name. A fixed-width digit string is not a
  validated timestamp either: the same adapter's `rxtime` path requires the
  fourteen digits to parse as a real calendar moment (`datetime.strptime`)
  before they are reformatted as one, so a value like month `88` refuses the
  message instead of producing a UTC-Z string the schema would accept.
- **Stream-shape honesty.** A `translate_stream`-style entry point that
  accepts "an iterable of records" must work on a generator, and must raise,
  not silently iterate wrong, on the inputs that look like iterables by
  accident: a single record dict (iterates as its keys) and a string
  (iterates as its characters). `ingress/ais/ais_to_zmeta.py`'s
  `translate_stream` is the pattern: zero events from a miswired call must
  never look identical to zero events from a genuinely empty stream.
- **Per-field physical bounds.** A decoded value outside the range the
  sending field can physically encode is not a claim the standard makes, it
  is corruption, and it is dropped rather than carried as fact. AIS speed
  over ground is bounded `0` to `102.2` kt (`62` kt for the six-bit message-27
  field), course `0` to `359.9` degrees, heading `0` to `359` degrees; values
  outside those ranges are refused even when they are not one of the
  standard's own not-available sentinels.

## Start From A Mapping Pack, Not A Blank File

For a new vendor format, check `adapters/mapping-packs/` before writing a new
adapter module from this guide's text alone. A mapping pack is a declarative
description of the vendor translation (`mapping.yaml`, optional
`enums.yaml`/`units.yaml`, and a `tests/` corpus of real input plus expected
ZMeta output) reviewed against a real vendor format rather than left implicit
in adapter code. `edge-comms-bladerf/` ships real flight-blackbox RF
detections; `sapient-bsi-flex-335/` is validated against the official Dstl
Apex tooling. Both pair with a runnable reference adapter (`ingress/bladerf/`,
`ingress/sapient/`) a new author can diff against. `example-vendor-pack` plus
`ingress/example-vendor/` is the smaller, structural teaching pair, built to
mirror this guide section by section.

Building against an existing pack, or writing a new one alongside a thin
adapter, is the field-proven lane: the pack's `tests/` corpus is conformance
evidence an adapter can be checked against, not just this guide's prose.

Writing an adapter from this guide's text alone, with no mapping pack behind
it, is the fallback for a format nothing here already covers. Every rule in
this guide still applies; there is simply no existing pack or reference
implementation to diff against, so lean harder on the validation ladder
(section 5) and on one refusal fixture per required field (section 9) to
catch what a missing second set of eyes would otherwise catch.

## 4. Build

- Copy `adapters/ingress/template/adapter_template.py` (or the nearest
  reference from the table) and implement your translation entry point(s):
  one or more `translate_<subject>` functions named for what they accept
  (`translate_aircraft`, `translate_message`, `translate_stream`,
  `translate_csv_row`, and so on; there is no single required name), each
  returning `list[dict]` of ZMeta events for one input, or refusing with
  `[]`/`None`. `detect(input_bytes) -> schema_id` is optional dispatch
  plumbing for a caller that must identify the format from raw bytes before
  it can pick the right entry point; reference adapters whose caller already
  knows the schema (`ingress/adsb/`, `ingress/ais/`) skip it. A local
  `validate(zmeta_event)` function is an optional convenience some adapters
  ship; the canonical validator (ladder step 2 below) is authoritative
  regardless of whether your adapter also carries one.
- Declare an `ADAPTER_VERSION`. When translating with real parents, set
  `lineage.transform = "translate:<schema_id>@<adapter_version>"`.
- Normalize timestamps with `adapters.ingress.time_utils.normalize_utc_z()` /
  `epoch_ms_to_utc_z()`; expose per-event `payload.timing_quality` or periodic
  `TIME_STATUS`.
- Fail closed. Return `[]`/`None` on ambiguous or unmappable input rather
  than emitting a schema-invalid event. Building and emitting the
  `SYSTEM_EVENT`/`SCHEMA_VIOLATION` diagnostic for that refusal is caller-side
  (the gateway, a wrapping ingest script, or the harness): a `translate_*`
  entry point's own fail-closed return is what signals the refusal, not a
  self-constructed diagnostic. (`ingress/sapient/`'s `_translate_error` is a
  different case: it translates the vendor's own self-reported error message
  into this same ZMeta vocabulary, which is ordinary translation work, not a
  diagnostic about this adapter's refusal.)
- Vendor quirks belong in adapter-local code, a mapping pack
  (`adapters/mapping-packs/`: declarative documentation plus test samples;
  no runtime engine executes `mapping.yaml`), or namespaced payload
  extensions. They must not alter event meaning, units, lineage, authority,
  or command safety.

## 5. Validate: The Ladder

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
line (worked examples: `conformance/adapter-harness/must-pass.jsonl`). The
JSON Schema for fixture lines lives at
`conformance/adapter-harness/fixture.schema.json`; the harness lints every
fixture line against it before execution (an unknown expectation key is a
caught typo, not a silent no-op), and `tools/check_adapter.py --fixtures`
runs the same lint at author time. `result: "events"` fixtures require an
`event_count` pin. Without one, a refusing adapter returning `[]` would
satisfy every expectation vacuously. Fixture `args`/`kwargs` are JSON only:
adapters whose entry points take constructed objects (e.g. the SAPIENT
`RegistrationStore`) cannot exercise those paths through the harness.
Cover them in colocated pytest instead and say so in the pack README:

| Key | Meaning |
| --- | --- |
| `name` | Fixture label used in output (default `line-<n>`). |
| `module` | Repo-relative path to the adapter module to load. |
| `callable` | Function name to call. |
| `args` / `kwargs` | Arguments passed to the callable. |
| `result` | `"event"` (default, one dict) or `"events"` (list of dicts). |
| `profile` | Validation profile (default `"H"`). |
| `expect` | Expectation object (below). For `result: "events"`, an `expect.events` list applies per-index expectations; `expect.events` requires `event_count`, and surplus entries beyond the returned events fail (`ADAPTER_EXPECTATION_SURPLUS`). |

`expect` keys:

| Key | Meaning |
| --- | --- |
| `event_type` / `event_subtype` | Exact envelope match. |
| `source_producer` | Exact `source.producer` match. |
| `required_paths` / `forbidden_paths` | Dotted paths that must / must not resolve. |
| `expected_values` | Dotted path -> exact value pins. Numeric tolerance 1e-6; booleans never match non-booleans; a missing path is its own failure. |
| `event_count` | Exact number of events the callable must return. REQUIRED alongside `expect.events`; applies to both result kinds. `0` pins a fail-closed refusal the way the other keys pin emission: a `result: "events"` callable must return `[]`, and a single-event callable registers refusal by returning `None` (counted as zero events). A `result: "event"` fixture without `event_count` implicitly expects exactly one event. Write one refusal fixture per schema-required input field. |
| `utc_z_paths` | Paths that must be UTC `Z` timestamps (default `["event.ts"]`). |
| `require_lineage_transform` | Default `true` for non-SYSTEM events; set `false` for original observations that legitimately omit lineage. |
| `lineage_transform_prefix` | Required prefix for `lineage.transform` (for example `promote:`). |
| `allow_degraded_timing` | Default `false`: an `UNSYNCED` fallback fails unless explicitly allowed. |
| `requires_external_promotion` / `external_promotion_required_keys` | Assert promotion evidence for external-state projections. |

## 7. Producer Authority Is Deployment Policy

Schema validity is not authorization. Your `source.producer` and
`source.node_role` must be allowed for the family you emit
(`policy/roles.yaml`, `policy/producer-authority.yaml`). The reference
producer names are examples, and deployments narrow them to local ids. External
tactical ingress producers additionally carry the per-producer
`external_state_promotion` requirements in that file.

Name your producer to match a reference wildcard. If you do not, ladder steps
2-4 fail with `PRODUCER_NOT_ALLOWED` before any semantic check runs. The
policy pack is governed and hash-pinned, so editing it in a clone is exactly
what `AGENTS.md` tells you not to do; renaming your producer is the supported
move. The reference patterns:

| Pattern | For |
|---|---|
| `rf-sensor-*` | RF detection / DoA / spectrum |
| `eo-sensor-*`, `eo-cv-*` | EO/IR imagers and CV detectors |
| `acoustic-sensor-*` | acoustic |
| `packet-analyzer-*` | comms/packet analysis |
| `classifier-*`, `detector-*` | inference producers |
| `fusion-*` | fusion producers |
| `mavlink-*` | MAVLink bridges |

There is no state-projector wildcard. A producer that emits an authoritative
`STATE_EVENT` names itself explicitly in the policy and chooses its evidence
requirements there, because an unnamed authoritative track is an injection
path. The reference track projector runs as `fusion-*`.

`acme-doa` fails and `rf-sensor-acme` passes, with nothing else changed.
Note that `adapters/ingress/example-vendor/` is individually allowlisted in the
reference policy, so the worked example passes where a new adapter under a new
name will not. Do not read its success as proof your naming is fine.

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
  command safety). See `AGENTS.md` downstream-clone rules. Local changes to
  those surfaces create a private dialect.
- Work from the repository root; keep adapters importable as packages; run
  the ladder exactly as written before claiming the adapter is done.

Four failure modes proven by this guide's first external review pass
(2026-07-16). Each escaped an author whose schema validation was green:

- **Author from primaries, not summaries.** When your artifact mirrors or
  cites a file (a reference adapter, a schema block), open that file and
  diff against it. Conventions like a bounding-box coordinate format live in
  docstrings that secondhand summaries drop, and schema validation cannot
  catch dialect drift in free-form fields.
- **Prove fail-closed claims with refusing inputs.** For every field the
  schema requires, write the test where it is missing and assert refusal,
  one per required field rather than one sampled field. Green-path validation
  alone let a teaching adapter emit schema-invalid events on the exact rule
  it taught.
- **Run this guide as a checklist against your own adapter** before calling
  it done. An exemplar that violates the rule it teaches fails review.
- **Record validation evidence exactly.** Name the command and target you
  actually ran, invoked in a state where it can fail. A diff check is
  `git diff --check <base>...HEAD`, not a bare clean-worktree check that
  can never trip. A false validation claim in a commit message is an
  evidence-integrity defect, not a formatting nit.
