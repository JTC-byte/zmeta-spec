# SAPIENT (BSI Flex 335 v2.0) Mapping Pack

Status: reference. `schema_id: vendor:sapient_bsi335:v2`,
`pack_slug: sapient-bsi-flex-335`, version 1.0.0.

This pack is the *declarative description plus test evidence* for
translating SAPIENT — the UK's BSI Flex 335 autonomous-sensor interface,
v2.0 protobuf definitions — to and from ZMeta v1.x. Per
`adapters/mapping-packs/README.md` no runtime engine executes
`mapping.yaml`: the runnable translation lives in
`adapters/ingress/sapient/` and `adapters/egress/sapient/`, and this
pack's `tests/` samples plus the shared harness fixtures are the evidence
that those adapters implement the pack faithfully.

Inputs are SapientMessage dicts in protobuf-JSON form; both
lowerCamelCase and snake_case key spellings are accepted and normalized
to snake_case before mapping. This pack targets **BSI Flex 335 v2.0**
messages only. Withdrawn v7 artifacts (four of five velocity frames,
feet/MPH units, SYSTEM_TAMPER) are not mapped.

One SAPIENT DetectionReport fuses fact and opinion in a single message;
ZMeta forbids that collapse (contract 4.4). The heart of this pack is the
un-collapse: one report becomes 0..1 `OBSERVATION_EVENT` (measured
facts), 0..n `INFERENCE_EVENT` (classification/behaviour opinions with
model identity and confidence), or — for fusion nodes — one gated
`STATE_EVENT` promotion. `object_id` rides none of these as identity: it
is a sensor-local, NON-authoritative correlation hint preserved in the
vendor extension (`track_id` is fusion-node authority; the sole
exception is the promoted-external-state path, where the external track
id is carried as such).

## Registration-state doctrine

SAPIENT puts semantics out-of-band: signal and velocity units, error
statistics, mode latencies, model identity, and the class taxonomy live
in the `Registration` message, not on each report. The pack therefore
treats registration capture as a first-class component
(`adapters/ingress/sapient/registration_state.py`):

- `Registration` / `RegistrationAck` / `AlertAck` produce **no events**.
  Registration feeds the per-node RegistrationStore only.
- Registration-declared units (`units.yaml`) gate canonical mapping of
  `signal[]` and `enu_velocity`. **No captured registration means no
  canonical mapping** — those blocks are preserved verbatim in the
  vendor extension and the canonical features are omitted, never guessed
  (contract 6.7).
- Inference events require the registration model identity
  (`"<manufacturer> <model>"` + `software_version`; contract 7.5). No
  registration means no inference events. The native classification and
  behaviour lists are always preserved verbatim in the observation's
  vendor extension (under `native_classification` /
  `native_behaviour` — the literal key `classification` is
  schema-denylisted on observations); on the no-model path that
  extension residue is their only carrier.
- Location and range-bearing coordinates are self-describing on the wire
  (inline `coordinate_system`/`datum`), so the registration join governs
  their statistical labeling (`GeometricError` std-dev gate for
  `quality.measurement_error`), not their admissibility.

**Timing doctrine.** The one mandatory SAPIENT timestamp is *send* time,
not capture time. `event.ts` inherits that unmeasured latency, so the
adapter widens `timing_quality.est_error_ms` by the registration
`maximum_latency` for the node (mode-conservative maximum when the
active mode is unknown) — including on caller-supplied timing quality.
The default fallback remains the deliberately degraded
`UNKNOWN`/`UNSYNCED` from `coerce_timing_quality()`; SAPIENT carries no
timing-quality content of its own, so nothing ever maps to a clean sync
state.

## Canonical-geo eligibility matrix

Canonical `geo` is emitted only when ALL of the following hold
(contract 6.1/6.2/6.8 — all-or-nothing, WGS-84, meters HAE):

| Condition | Eligible | Otherwise |
| --- | --- | --- |
| `coordinate_system` | `LAT_LNG_DEG_M`, or `LAT_LNG_RAD_M` (radians converted to degrees) | `UTM_M` / unspecified: extension-only, `omitted_reason` `UTM_UNSUPPORTED` / `COORDINATE_SYSTEM_UNSPECIFIED` |
| `datum` | `WGS84_E` (ellipsoid = HAE) | `WGS84_G` geoid: extension-only, `omitted_reason` `GEOID_DATUM`; unspecified: extension-only, `omitted_reason` `DATUM_UNSPECIFIED` |
| altitude | explicit `z` present | extension-only, `omitted_reason` `NO_ALTITUDE` — never zero-filled |
| zero-fill | `(lat, lon) != (0, 0)` | extension-only, `omitted_reason` `ZERO_FILL_SUSPECT` |

An ineligible location is preserved verbatim (native dict plus the
`omitted_reason` tag) under `payload.extensions."vendor.sapient"`, and
observations assert `quality.geo_status` (`AVAILABLE`/`UNAVAILABLE`,
contract 21.1 vocabulary) so the geo omission stays visible.

Bearings follow contract 6.4: only `RANGE_BEARING_DATUM_TRUE` becomes
canonical `payload.bearing` (+ `quality.bearing_frame: "TRUE_NORTH"`).
Magnetic/grid/platform datums — grid being SAPIENT's recommended default,
so conversion debt is the *common* case — stay in explicitly named
non-canonical `features.bearing_native_deg` / `bearing_native_el_deg` /
`bearing_native_datum` fields.

## Refusal matrix

Fail closed, never fabricate (contract 3.4). "Refuse" means no event is
emitted for that message (or that entry is skipped); nothing is ever
defaulted into validity.

| Input condition | Disposition |
| --- | --- |
| Envelope `timestamp` missing or unparseable | refuse all events |
| `node_id` null or missing | refuse all events (identity is never fabricated) |
| Detection from node with no eligible modality and no resolvable signal | no observation (documented degradation); inference events still emitted when model identity is known |
| Signal units unresolved (no/other registration declaration) | no canonical RF features; whole signal block to vendor extension; subtype falls back to the node-type table |
| Multiple `signal[]` entries with resolvable units | canonical RF features from `signal[0]` only; `signal[1..]` preserved verbatim as `signal_additional` in the vendor extension (additional emitters are never dropped) |
| Geo ineligible (matrix above) | no canonical geo; raw location + `omitted_reason` to vendor extension |
| Bearing datum not TRUE | no canonical bearing; `bearing_native_*` features |
| No registration model identity | no inference events (natives preserved in vendor extension) |
| Classification/behaviour entry without confidence | that entry refused (contract 8.1) |
| Fusion-node detection without caller `promotion` evidence | refuse (contract 4.5.1 — never silently downgraded to observation) |
| Fusion-node `promotion` without caller `loop_status` | refuse (the reflection check is the caller's verification; the adapter never self-asserts its verdict) |
| Fusion-node detection without `detection_confidence` or eligible geo | refuse promotion (STATE requires confidence and geo; never invented, never increased) |
| Alert without model identity, confidence, or caller `based_on` parents | refuse (InferencePayload requires model, confidence, and real parent lineage) |
| TaskAck `task_id` not resolvable via caller `task_index` | refuse (`original_event_id` correlation is never fabricated) |
| TaskAck `TASK_STATUS_UNSPECIFIED` | refuse |
| Egress: COMMAND_EVENT without `requires_deconfliction: true` | return None |
| Egress: COMMAND task type with no honest SAPIENT verb (ORBIT/HOLD/SEARCH_BOX/LOITER/SCAN_RF/RETURN_TO_BASE/LAND) | return None (documented residue) |
| Egress: TRACK_TARGET without a `track_to_object` mapping | return None |
| Egress: Task `task_id` not a ULID | return None (the idempotency key is minted by the SAPIENT-bridged command producer; the adapter never rewrites it — a derived id would break idempotent re-issue and TaskAck correlation) |
| Egress: STATE `track_id` not a ULID and not resolved by the caller's `object_map` to a valid ULID | return None (`object_id` is caller-owned identity continuity — deployment state; the adapter never mints a fresh identity per report) |
| Egress: STATE quarantined, or `prohibited_uses` covering the export path | return None; exportable warn/degrade events are labeled via `object_info` self-labels instead (label-don't-launder) |

Altitude never crosses into SAPIENT Task locations (contract 7.8), and
egress envelope timestamps are always the ZMeta `event.ts` — a
translate-time wall clock would be a fabricated timestamp. Egress
SapientMessage ids are ULIDs (proto `is_ulid`; Apex `strictIdFormat`,
on by default, rejects violations — verified live against Apex v4.2.0):
`report_id` is adapter-derived with its 48-bit timestamp component
sourced from `event.ts` (never the wall clock); `object_id` and
`task_id` are caller-owned per the refusal rows above.

One declared sentinel is not a refusal: SAPIENT `Error` echoes the
offending packet, not a ZMeta event id, so the emitted
`SYSTEM_EVENT`/`SCHEMA_VIOLATION` carries the gateway's documented
`original_event_id: "UNKNOWN"` sentinel (`gateway/src/gateway.py`
precedent) rather than a synthesized correlation id.

## Out of scope (v1 of this pack)

- **Task ingress** (SAPIENT Task -> COMMAND_EVENT): command-safety
  surface; requires a deconfliction-authorized producer path that this
  pack does not claim.
- **Effector arming / kinetic and DEW node command paths** (KINETIC,
  LDEW, RFDEW, JAMMER): out of scope per the contract's bounded-tasking
  posture (4.10); those node types still degrade honestly on ingress.
- **AlertAck loop**: terminated at the adapter; no events.
- **Protobuf wire encoding**: adapters exchange protobuf-JSON dicts;
  real wire encoding/transport belongs to a SAPIENT middleware
  (consistent with the JREAP/KLV egress posture).
- **UTM coordinate conversion**: `UTM_M` locations are extension-only.

## Escalated branch evidence (recorded, not implemented)

Three items from the SAPIENT field diff are evidence for version-branch
candidates. They are escalated to the maintainer per the change process
and deliberately NOT solved in this pack:

1. **RADAR-family modality feature contracts** (queued roadmap item):
   ZMeta v1.x has no RADAR/LIDAR/SEISMIC observation modality, so raw
   observations from those archetypal SAPIENT node types degrade to
   inference/vendor-extension content. Degraded fidelity, not a blocked
   adapter.
2. **Track-lifecycle vocabulary** (reserved roadmap candidate): SAPIENT
   contributes a persistent `object_id` plus a free-text `state` ("e.g.
   object lost") — real but thin evidence; preserved as
   `vendor.sapient.state` residue meanwhile.
3. **Tasking verbs**: LOOK_AT pointing cues, multi-waypoint patrol,
   detection/classification threshold and report-rate tuning have no
   honest COMMAND_EVENT mapping; egress returns None for unmappable
   types rather than approximating.

## Tests

`tests/input.json` holds two SapientMessages: `registration` (ingested
into the RegistrationStore first) and `detection` (passed to
`translate()` with that store). `tests/expected.json` is the returned
event list for the detection happy path: one RF observation with
registration-resolved signal units plus one classification inference
with registration model identity.

Following the `example-vendor-pack` convention, the expected file pins
the *stable mapped fields* only:

- `event.event_id` values are fixed UUIDv7-shaped placeholders (the
  adapter mints fresh ids per emission); the inference `based_on` /
  `lineage.based_on` reference the observation's placeholder id and are
  equally dynamic at runtime.
- `payload.timing_quality` is a contract obligation added by the
  adapter, not part of the declarative mapping, and is omitted here. On
  real output it carries the degraded fallback widened by the
  registration `maximum_latency` (+500 ms for this fixture's node).

## Validation

From the repository root:

```
python -m pytest adapters/ingress/sapient adapters/egress/sapient -q
python tools/validate_adapter_conformance.py --fixtures conformance/adapter-harness/must-pass.jsonl
```

then the full ladder in `adapters/AUTHORING.md` section 5.

End-to-end wire validation against the official Dstl tooling was run on
2026-07-21 (Apex-SAPIENT-Middleware v4.2.0, commit 0c8591a, its shipped
BSI Flex 335 v2.0 `*_pb2` modules and validator, stock strict
configuration, Python 3.11 + protobuf 4.25.1):

- Egress: every produced Task and DetectionReport dict parses strictly
  (`ParseDict`, unknown fields disallowed) into the official
  `SapientMessage` classes, byte round-trips exactly, and passes the
  Apex validator clean, including ULID id checks and the
  `zmeta.risk`/`zmeta.timing_quality` object_info self-labels.
- Ingress: Registration, DetectionReport, StatusReport, TaskAck, and
  Error messages built via the official pb2 classes (Apex-validator
  clean, both camelCase and proto-field-name JSON spellings) translate
  to schema-valid ZMeta events with correct units, layer splits,
  timing widen, and refusal behavior. Zero findings.
- Live loop: a local Apex v4.2.0 instance accepted Registration
  (acknowledged) and egress DetectionReports as-is — stored with no
  error records and no SAPIENT Error replies.

Not exercised, recorded honestly: the C# BSI Flex 335 v2 test harness
(no .NET SDK on the validation host) and multi-node Apex routing. Those
remain open integration targets for a live SAPIENT enclave.
