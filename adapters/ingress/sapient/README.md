## SAPIENT (BSI Flex 335 v2.0) Ingress Adapter

Translates SAPIENT `SapientMessage` dicts (protobuf-JSON) into ZMeta events,
un-collapsing SAPIENT's fused fact/opinion `DetectionReport` into the ZMeta
layer model. Part of the `sapient-bsi-flex-335` mapping pack
(schema_id `vendor:sapient_bsi335:v2`, target wire truth: BSI Flex 335 v2.0
protos). Status: Reference.

### Input model

One `SapientMessage` as a Python dict decoded from protobuf-JSON. Both
lowerCamelCase and snake_case keys are accepted (all keys are normalized to
snake_case recursively; values — including enum strings — are untouched).
Enum values must be proto value-name strings (long form
`LOCATION_DATUM_WGS84_E` or short form `WGS84_E`); integer enum encodings
are not decoded and resolve as unknown (fail closed).

Envelope requirements (whole-message refusal when violated):

- `timestamp` (RFC3339 string or protobuf `{seconds, nanos}` dict) —
  missing/unparseable refuses the message.
- `node_id` — null/missing refuses the message; identity is never
  fabricated.
- Exactly one known `content` oneof branch must be present.

### Event families

| SAPIENT content | ZMeta output | zmeta_version |
|---|---|---|
| `detection_report` (sensor node) | 0..1 `OBSERVATION_EVENT` + 0..n `INFERENCE_EVENT` (classification / behaviour / detection-existence claim) | 1.0 |
| `detection_report` (fusion node) | `STATE_EVENT` / `TRACK_STATE` via the contract 4.5.1 external-promotion gate | 1.0 |
| `status_report` | `SYSTEM_EVENT` / `SENSOR_STATUS` + 0..1 `PLATFORM_STATUS` (only when `power` is present) | 1.1.0 |
| `alert` | `INFERENCE_EVENT` / `ANOMALY` | 1.0 |
| `task_ack` | `SYSTEM_EVENT` / `TASK_ACK` | 1.0 |
| `error` | `SYSTEM_EVENT` / `SCHEMA_VIOLATION` | 1.0 |
| `registration` | no events — feeds the caller's `RegistrationStore` | — |
| `registration_ack`, `alert_ack` | no events (ack loops terminate here) | — |
| `task` | no events — SAPIENT→`COMMAND_EVENT` ingress is **out of scope** in v1 (command safety: `requires_deconfliction` cannot be fabricated by an adapter; see `AGENTS.md` command-safety limits) | — |

Detection event order: observation first, then classification inferences
(input order), behaviour inferences, and the detection-existence claim last.

### Registration doctrine (the units codex)

SAPIENT declares units, error statistics, model identity, latency bounds,
and taxonomy out-of-band in `Registration`; detections then carry bare
numbers. ZMeta forbids unit inference (contract 6.7), so registration
capture is a first-class pack component: feed every `Registration` to a
`RegistrationStore` (directly via `store.ingest(msg)` or by passing the
store to `translate()`, which ingests registration content itself) and pass
that store to every `translate()` call.

What the store resolves — and what its absence costs:

| Declaration | Enables | Without it |
|---|---|---|
| `node_definition` node types | Observation modality (CAMERA→EO, ACOUSTIC→ACOUSTIC, CYBER→NETWORK) and fusion-node detection | No modality: no observation |
| signal-category units (`centre_frequency`/`start_frequency`/`stop_frequency` in Hz/MHz/GHz, `amplitude` in dBm) | Canonical RF features | Whole `signal` block extension-only; no RF observation |
| `config_data` manufacturer/model (+`software_version`, else `"unknown"`) | `payload.model` for inference events | No inference events (model identity is never fabricated, contract 7.5); native classification stays in the vendor extension |
| `maximum_latency` per mode | `est_error_ms` timing widen | Never declared: no widen (only the fallback bound). Declared but **unresolvable**: degraded timing, see below — never a silent no-widen |
| `velocity_type` ENU units (m/s or km/h) | `features.velocity_enu_mps` | `enu_velocity` extension-only |
| `geometric_error` "Standard Deviation" in metres | `quality.measurement_error` from `x/y/z_error` | Errors stay raw in the vendor extension |

Conflicting redeclarations across modes poison the key to "unresolvable"
(never first-wins). Unknown `Duration` units yield `None`, never a guessed
scale.

A `detection_report` with **no registration at all** is fully refused:
no node type (no modality), no units (no canonical RF), no model (no
inference) — nothing can be honestly emitted.

### Timing (send-time widen)

The one mandatory SAPIENT timestamp is message **send** time, so `event.ts`
inherits the unmeasured capture→send gap. Every payload-bearing operational
event carries `payload.timing_quality`:
`coerce_timing_quality()` supplies the deliberately degraded
`UNKNOWN`/`UNSYNCED` fallback, then `est_error_ms` is widened by the
registration-declared `maximum_latency` — **including when the caller
supplies its own `timing_quality`** — because that latency is real even
with a good clock. `active_mode` scopes the widen to one mode's
declaration; when `None` — or when the name matches no declared mode with
a resolvable latency — the maximum across declared modes applies
(conservative: a mismatched mode name never shrinks the claimed error).

**An unresolvable declaration is not the same as no declaration.** A node
that declared a `maximum_latency` this adapter cannot resolve — unknown
`Duration` units, a `NaN`/`Infinity` value, a value whose millisecond
scaling overflows, or an integer with no float64 form — has told us its
capture→send gap is bounded and left us unable to say by what. Skipping
the widen and shipping the caller's bound unchanged would make that node
publish a *tighter* `est_error_ms` than a node with a sane declaration
(measured before this was closed: `0.5 s` declared → `505.0`, `NaN`
declared → `5.0`). The worse the input, the cleaner the event — laundering.

So an unresolvable declaration degrades the event instead: `time_source`
`UNKNOWN`, `sync_state` `UNSYNCED`, and `est_error_ms` the **wider** of the
caller's own bound and the module's unknown-clock fallback. The event is
still emitted — one malformed mode declaration must not zero every event
from that node forever — but its timing is explicitly untrustworthy and
filterable, and consumers read `est_error_ms` together with `sync_state`
(contract 5.3), never as a standalone bound. A caller `est_error_ms` that
is *already* non-finite is left alone and refused whole at the emit
boundary; it is never replaced with a clean default.

`RegistrationStore.latency_unresolved(node_id, mode=None)` exposes this
state directly, because `max_latency_ms()` returns `None` for both "never
declared" and "declared, unusable" and a caller reading only that cannot
tell the quiet node from the broken one.

### Geo, bearings, signal, velocity

- **Canonical geo is all-or-nothing** (contract 6.8): emitted only for a
  `Location` with `LAT_LNG_DEG_M`/`LAT_LNG_RAD_M` coordinates (radians
  converted), the `WGS84_E` ellipsoid datum, an explicit `z`, in-range
  values, and a non-`(0,0)` position (`(0,0)` is zero-fill suspect).
  Anything else omits geo entirely; the raw native `location` is preserved
  under the vendor extension with an `omitted_reason` tag
  (`GEOID_DATUM`, `NO_ALTITUDE`, `UTM_UNSUPPORTED`, `ZERO_FILL_SUSPECT`,
  `UNITS_UNSPECIFIED`, `DATUM_UNSPECIFIED`, `COORDS_MISSING`,
  `RANGE_INVALID`).
- **Canonical bearing only for TRUE north** (contract 6.4):
  `RANGE_BEARING_DATUM_TRUE` maps to `payload.bearing.az_deg`
  (+`el_deg`) with `quality.bearing_frame: "TRUE_NORTH"`.
  MAGNETIC/GRID/PLATFORM bearings stay in explicitly named
  `features.bearing_native_deg` / `features.bearing_native_datum`
  (+`features.bearing_native_el_deg`). `range` converts to
  `features.range_m` per the self-describing coordinate system (km→m).
  Unspecified units/datum keep the raw `range_bearing` extension-only.
- **Signal**: canonical RF features only when the registration codex
  resolves `centre_frequency` to Hz/MHz/GHz **and** `amplitude` to dBm.
  Amplitude with non-dBm or unknown units is **never** mapped to
  `power_dbm`. `bandwidth_hz` is stop−start when both edges resolve;
  otherwise the declared `0.0` "not measured" sentinel (same convention as
  the kraken/moth/signalhunter adapters — a documented consumer-visible
  marker, not an invented measurement). Canonical features map from the
  **first** `signal[]` entry only; additional entries (further emitters)
  are preserved verbatim as `signal_additional` in the vendor extension,
  never dropped.
- **Velocity**: `enu_velocity` × the registration ENU factor →
  `features.velocity_enu_mps` `{east, north[, up]}`; `up` only when
  `up_rate` units were declared. Unknown factor keeps the raw block
  extension-only.

### Observation-emission matrix

An observation is emitted only when an honest modality exists:

| Node situation | Observation |
|---|---|
| Canonical RF feature triple resolvable (any node type) | `RF` |
| CAMERA | `EO` |
| ACOUSTIC | `ACOUSTIC` |
| CYBER | `NETWORK` |
| RADAR / LIDAR / SEISMIC / CHEMICAL / other, without a resolvable signal block | **none** — documented degradation until the queued RADAR-family v1.x feature contracts land; inference events still emit if model identity and caller lineage exist |
| Unregistered node | **none** |

### Refusal matrix (fail closed, never fabricate)

| Condition | Behavior |
|---|---|
| Missing/unparseable envelope `timestamp` | whole message refused (`[]`) |
| Null/missing `node_id` | whole message refused |
| Detection with no registration | refused (no modality, units, or model) |
| Signal units unresolved | signal extension-only; no canonical RF features |
| Amplitude not declared dBm | never `power_dbm`; no RF observation |
| Geo ineligible (datum/units/z/zero-fill/range) | geo omitted; raw + reason in extension |
| Non-TRUE bearing datum | no canonical bearing; named native features |
| Classification/behaviour entry without confidence | that entry refused (inference confidence is required, contract 8.1); raw entry stays in the vendor extension |
| No model identity | no inference events; native claims extension-only |
| No observation emitted and no caller `based_on` | no inference events (mandatory lineage is never invented, contract 4.8) |
| Alert without model / confidence / caller `based_on` | refused |
| Fusion-node detection without `promotion` kwarg | refused — never silently downgraded to an observation |
| Promotion without caller-supplied `promotion["loop_status"]` | refused — the reflection check is a verification the adapter never performs, so its verdict is never self-asserted |
| Promotion without caller `based_on`, `detection_confidence`, or full canonical geo | refused |
| Promotion dict carrying any key outside the enumerated promotion vocabulary | refused — promotion metadata never smuggles raw measurements or unenumerated keys into STATE (contract 4.5.1) |
| `task_index` entry present but null/empty | refused — the TaskAck correlation is never fabricated (no `str(None)` coercion) |
| Non-finite (NaN/inf) value on the wire | refused at the guard (canonical fields) or omitted from native pass-through blocks — never emitted |
| Non-finite arithmetic PRODUCT from finite operands (unit scaling, radians->degrees, band-edge difference, latency widen) | that canonical field is not written and the raw block is preserved as provenance; guarding the operand is not enough, since `value * 1e6` and `math.degrees()` overflow to inf near the float64 ceiling and `inf % 360.0` is NaN |
| Non-finite anywhere inside the canonical `claim` (e.g. a vendor `sub_class` taxonomy) | that inference entry refused — `claim` is canonical, so the vendor pass-through drop rule does not apply; the raw entry stays in `native_classification` |
| Registration `Duration` whose scaled value is non-finite | treated as an unresolvable declaration (`None`), same as unknown units — never a non-finite `est_error_ms` on every event from that node |
| Registration `maximum_latency` that is unresolvable for ANY reason | the event's timing degrades to `UNKNOWN`/`UNSYNCED` with the **wider** of the caller's bound and the unknown-clock fallback — a broken declaration must never yield a tighter `est_error_ms` than a sane one (see Timing above) |
| Integer literal with no float64 form (e.g. a 400-digit number) anywhere on the wire | that field refuses like any other unmappable value; `translate()` and `RegistrationStore.ingest()` never raise — `math.isfinite` raises `OverflowError` on such an int, and wire data must never crash the ingest loop |
| Non-finite dict KEY inside a verbatim vendor block | that entry is dropped from the provenance block; the event and every canonical field it resolved are still emitted — a defect confined to a pass-through blob never destroys the geo, bearing, RF features or classification around it |
| Any non-finite surviving to the emit boundary | that event refused, and the refusal CASCADES to events citing it as `based_on` — a dependent must never assert lineage to an event that was not emitted (contract 4.8) |
| TaskAck with unresolvable `task_id` (no `task_index` entry) | refused — the `original_event_id` correlation is never fabricated |
| TaskAck `TASK_STATUS_UNSPECIFIED` | refused |
| StatusReport `power` mapping to no metrics | no `PLATFORM_STATUS` (never padded) |
| Non-TRUE / non-degrees field-of-view cone | `fov_deg` omitted; raw cone extension-only |
| SAPIENT `task` content | no events (out of scope v1) |

`Error` content maps to `SCHEMA_VIOLATION` with
`metrics.original_event_id: "UNKNOWN"` — the documented gateway sentinel
(`gateway/src/gateway.py`) for an unknowable original id; a synthesized
correlation id is forbidden.

### Fusion-node promotion (contract 4.5.1)

A detection from a fusion node (per registration `NODE_TYPE_FUSION_NODE`,
or per the `promotion` kwarg when the node is not known as a sensor)
promotes to `STATE_EVENT`/`TRACK_STATE` only with: caller-supplied
`promotion` evidence metadata (reference policy
`PROMOTE-SAPIENT-STATE-V1`) **including an explicit `loop_status`** — the
reflection check is the caller's verification, never self-asserted by the
adapter (this gateway's own SAPIENT egress makes a fusion node
re-reporting an exported track a live reflection scenario) — caller
`based_on` lineage, an explicit `detection_confidence` (used as-is, never
increased), and full canonical geo. `track_id` is the SAPIENT `object_id` (permitted external track id in
promoted state), `lineage.transform` is
`promote:sapient@<version>:<policy_id>`, and the payload's vendor block
carries compact native ids only — STATE never carries raw sensor features
(contract 7.7). Registration knowledge wins: a registered non-fusion
sensor node splits normally even when a `promotion` dict is supplied.

### Vendor extension block

Every payload-bearing event carries
`payload.extensions["vendor.sapient"]` with the native ids/fields actually
present (absent keys omitted): `report_id`, `object_id` (a
NON-authoritative correlation hint — never a `track_id`), `task_id`,
`state`, `id`, `detection_confidence`, `prediction_location`,
`associated_detection`, `derived_detection`, `associated_file`,
`track_info`, `object_info`, plus unmappable blocks (`signal`,
`signal_additional` — entries past the first when canonical RF features
were mapped from `signal[0]` — `enu_velocity`, `location`,
`range_bearing`, `node_location`, `coverage`, `obscuration`). Native classification/behaviour lists are preserved as
`native_classification` / `native_behaviour` — deliberately renamed so the
observation denylist names (`confidence`, `classification`, `track_id`,
`entity_class`, `label`) never appear as extension keys. Extensions are
safe to ignore: nothing load-bearing lives only in the vendor block.

### StatusReport mapping

`SENSOR_STATUS` (1.1.0): `system` OK→`ACTIVE`, WARNING/ERROR→`DEGRADED`,
GOODBYE→`OFFLINE`, unset→`UNKNOWN`; an
INTERNAL_FAULT/EXTERNAL_FAULT/NOT_DETECTING status entry degrades
ACTIVE/UNKNOWN to `DEGRADED`. `metrics.sensor_id` is the node_id,
`metrics.mode` the mode string, and `metrics.fov_deg` only from a
TRUE-datum range-bearing cone with a degrees-family horizontal extent.
`PLATFORM_STATUS` (1.1.0) only when `power` is present: `level`→
`battery_pct`, MAINS→`EXTERNAL_POWER`,
INTERNAL/EXTERNAL_BATTERY→`BATTERY` (other sources omitted),
POWERSTATUS_FAULT→state `WARNING`, OK→`NOMINAL`, unset→`UNKNOWN`.

### Invocation

Run from the repository root (package imports; see `adapters/README.md`):

```python
from adapters.ingress.sapient.registration_state import RegistrationStore
from adapters.ingress.sapient.sapient_to_zmeta import SCHEMA_ID, translate, validate

store = RegistrationStore()
translate(registration_msg, SCHEMA_ID, registration=store)  # feeds the store

events = translate(
    detection_msg,
    SCHEMA_ID,
    registration=store,
    active_mode="scan",                     # scopes the timing widen
    based_on=["<parent-uuid7>"],            # only real ZMeta parent ids
    task_index={"<sapient-task-id>": "<command-event-uuid7>"},
)
for event in events:
    status, violations = validate(event)    # version-aware: 1.0 / 1.1.0
```

Tests:

```
python -m pytest adapters/ingress/sapient -q
```
