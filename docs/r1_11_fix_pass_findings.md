# R1-11 Fix-Pass Finding Register

**Advisory / non-normative.** The complete finding set from the two
adversarial rounds of the R1-11 fix pass, recorded here because the run
artifacts that produced them are session-scoped and do not survive.

## Status — 2026-07-27

- **The round-3 (disposition-pass attack) findings are NOT in this file and
  never were** (cold re-read CR-03): they survive only as counts in the cycle
  record. Maintainer decision 2026-07-27: that loss is recorded as **final** —
  no reconstruction round; the defects re-derive from the tree through the
  playbook's scoped waves, which is also why the stop-at-three decision stands.
- **The `_parse_utc` carried-forward MAJOR is CLOSED as a class** (health wave
  `25bb5fa`/`ede9bb6`): CoT, JREAP, and the SAPIENT egress twins refuse
  gate-clean unparseable and NAIVE timestamps per their documented contracts.
  The `A-13` anchor MAJOR remains open (records wave).
- **Cold re-read findings fixed by the health wave** (`25bb5fa`/`ede9bb6`/
  `dcabcc8`): CR-01, CR-02, CR-05, CR-06, CR-08, CR-09, CR-10, CR-11, CR-12,
  CR-16, plus the unblocked R2-30 skip-reason token and the R1-11-16
  vocabulary lint. Verifier-surfaced register candidates from the wave are
  logged in the cold re-read record's companions and the doctrine log's H1
  section.

`docs/r1_11_full_stack_audit.md` carries the audit itself, the fix-pass
narrative and the four MAJOR findings carried forward. This file carries
**all of them**, so a later reader can re-derive a disposition rather than
take the summary on trust. Every entry below was produced by an agent that
was read-only at the time and had to demonstrate its claim at `file:line`.

**Treat these as claims, not as established findings.** They have not been
through the three-lens adversarial refutation the audit findings went
through. Reproduce before acting.

---

## Round 1 — attack on the six blocker fixes

30 findings against the guards written to close A-01..A-06, found on a
fully green tree (pytest 896 + 716 subtests at that point). **All were
remediated in round 2** — they are recorded for provenance, and because the
remediation of several is itself now under a round-2 finding.

### R1-01 (MAJOR) — decode_gps_raw_int launders MAVLink's documented UINT8_MAX "satellites unknown" sentinel into a 255-satellite measurement — the fourth member of the sentinel family the wave enumerated and declared closed

**Location:** `adapters/ingress/mavlink/mavlink_to_zmeta_template.py:370`

**Claim:** The wave's own sentinel rule ("a MAVLink 'not sent' sentinel must never become a measurement") was applied to three of the four sentinels this module touches — `hdg == 65535` (line 324), `voltage_battery == 65535` (line 387), `battery_remaining == -1` (line 390) — and not to the fourth. MAVLink common.xml defines GPS_RAW_INT.satellites_visible as uint8_t, "Number of satellites visible. If unknown, set to UINT8_MAX". `decode_gps_raw_int` at :370-372 tests only `is not None`, so 255 passes straight through into `payload.quality.satellites_visible` as a sensor reading — and it is laundering in the confidence-inflating direction (255 reads as an exceptional fix). The sibling decoder immediately below it, rewritten in the same wave, does exactly the check that is missing here.

**Evidence:**

```
mavlink_to_zmeta_template.py:370-372 `satellites_visible = msg_dict.get("satellites_visible"); if satellites_visible is not None: decoded["satellites_visible"] = satellites_visible` versus the sibling at :387 `if voltage_mv is not None and voltage_mv != 65535:`. Live probe through the documented decode->translate pipeline: quality = {'gps_fix_type': 3, 'satellites_visible': 255, 'geo_status': 'AVAILABLE'}; schema True; validate_semantics (True, []); validate_producer_authority (True, []). The pin at test_mavlink_ingress.py:644-651 (`test_decode_gps_raw_int_omits_unreported_fix_quality`) exercises only `{}`, `{fix_type:3}` and `{fix_type:0, satellites_visible:0}` — it never presents the sentinel, so it passes while the sentinel leaks. adapters/ingress/mavlink/README.md:130-133 documents the sentinel rule for decode_sys_status only and README.md:120-121 asserts the whole-file property this falsifies: "Nothing this adapter emits is a value the telemetry did not carry."
```

**Reproduction:** cd <repo> && python -c "import sys; sys.path.insert(0,'.')
from adapters.ingress.mavlink.mavlink_to_zmeta_template import *
st = decode_global_position_int({'lat':340500000,'lon':-1182400000,'alt':412500,'hdg':65535})
st.update(decode_gps_raw_int({'fix_type':3,'satellites_visible':255}))
st['based_on']=['019c2b5c-c053-70e1-b6aa-340000000001']; st['loop_status']='CHECKED_NOT_REFLECTION'
ev = translate_platform_state(st, platform_id='uas-1', ts='2025-01-17T15:20:00Z')
print(ev['payload']['quality'])
print('sibling handles its sentinel:', decode_sys_status({'voltage_battery':65535}))"
-> {'gps_fix_type': 3, 'satellites_visible': 255, 'geo_status': 'AVAILABLE'}
-> sibling handles its sentinel: {}

### R1-02 (MAJOR) — translate_link_status still hard-codes payload.state = "UP" — the top-level link-health claim, in the same dict literal as the three metrics the wave just promoted to required parameters

**Location:** `adapters/ingress/mavlink/mavlink_to_zmeta_template.py:535`

**Claim:** The wave's stated purpose for this function is "link health is never fabricated" (its own ValueError text at :503-506). It promoted latency_ms/packet_loss_pct/throughput_bps out of the payload literal into required parameters — and left `"state": "UP"` behind in that same literal, five lines below, still hard-coded with no parameter. `state` is the LINK_STATUS field a consumer reads first, and the v1.0 schema explicitly offers UP/DEGRADED/DOWN/UNKNOWN, so "UNKNOWN" was available. A caller who now honestly supplies 92% packet loss and 5000 ms latency still emits an event asserting the link is UP; a caller who has no health data at all gets a ValueError for the metrics but could never have expressed anything but UP. The class was scoped to "a numeric the telemetry never reported", and the non-numeric member sitting inside the fixed dict escaped on that technicality — and the new provenance guard (`_invented_numerics`, test file :427-467) walks only int/float leaves, so it is blind to it by construction.

**Evidence:**

```
mavlink_to_zmeta_template.py:533-537 `"payload": {"system_type": "LINK_STATUS", "state": "UP", "metrics": metrics}` — `state` is not in the signature at :471-484. schema/zmeta-event-1.0.schema.json $defs/SystemPayload allOf LINK_STATUS branch constrains state to enum [UP, DEGRADED, DOWN, UNKNOWN]. Probe output: payload = {'system_type':'LINK_STATUS','state':'UP','metrics':{'link_id':'edge-comms-uas-1','active_link':'unknown','latency_ms':5000.0,'packet_loss_pct':92.0,'throughput_bps':0}}; jsonschema validate OK; validate_semantics (True, []). Not one of the five new link_status pins (test_mavlink_ingress.py:667-720) asserts anything about payload.state.
```

**Reproduction:** cd <repo> && python -c "import sys; sys.path.insert(0,'.')
from adapters.ingress.mavlink.mavlink_to_zmeta_template import translate_link_status
import json
l = translate_link_status(platform_id='uas-1', latency_ms=5000.0, packet_loss_pct=92.0, throughput_bps=0, ts='2025-01-17T15:20:00Z')
print(json.dumps(l['payload']))"
-> {"system_type": "LINK_STATUS", "state": "UP", "metrics": {..., "latency_ms": 5000.0, "packet_loss_pct": 92.0, "throughput_bps": 0}}
(a dying link reported as UP; schema-valid, semantics-clean)

### R1-03 (MAJOR) — The fix launders `est_error_ms`: a node declaring an unusable `maximum_latency` now yields a NARROWER uncertainty bound than a node declaring a sane one, contradicting the comment added in the same commit

**Location:** `adapters/ingress/sapient/registration_state.py:107`

**Claim:** `duration_ms` now returns None for a non-finite scaled duration, which makes `RegistrationStore.max_latency_ms()` return None, which makes `_timing` skip the widen entirely. The event then ships the caller's un-widened `est_error_ms` with no marker anywhere that a declared latency was read and discarded. `_timing`'s own comment added in this same diff (sapient_to_zmeta.py:323-331) says: "falling back to the un-widened value would UNDERSTATE it — the one thing an uncertainty field must never do". `duration_ms` performs exactly that fallback on `_timing`'s behalf, one module over. Before the fix this input produced `est_error_ms = inf` — broken, but detectable, and the new backstop would refuse it outright. The fix replaced a detectable condition with a value indistinguishable from a healthy node, which is the laundering direction.

**Evidence:**

```
Caller supplies good timing (`{'time_source':'GPS_PPS','sync_state':'LOCKED','est_error_ms':5.0}`); only the node's DECLARED maximum_latency varies:
  0.5 s (sane)   est_error_ms = 505.0   validate -> pass
  1e308 s        est_error_ms =   5.0   validate -> pass
  NaN            est_error_ms =   5.0   validate -> pass
The worse the declaration, the cleaner the event. No marker: `json.dumps(event).lower().count('latency') == 0`, and the vendor extension keys are ['detection_confidence','native_behaviour','native_classification','object_id','report_id'] — the discarded declaration is recorded nowhere. Neither the adapter's `validate()` nor the kernel can see it, because 5.0 is a perfectly legal value.
The author disclosed this under "ALSO FOUND, NOT FIXED" as identical to the pre-existing unknown-units case (confirmed: unknown units also yields 5.0). The part not disclosed is that the fix newly routed a numeric, finite-looking wire declaration into that laundering path, and that the alternative it displaced was total refusal (0 events), not a worse number.
```

**Reproduction:** python -c "import sys;sys.path.insert(0,'.');import importlib.util,adapters.ingress.sapient.sapient_to_zmeta as s2z;spec=importlib.util.spec_from_file_location('t','adapters/ingress/sapient/test_sapient_ingress.py');T=importlib.util.module_from_spec(spec);spec.loader.exec_module(T);tq={'time_source':'GPS_PPS','sync_state':'LOCKED','est_error_ms':5.0}\nfor v,tag in ((0.5,'0.5s'),(1e308,'1e308s'),(float('nan'),'NaN')):\n    ev=s2z.translate(T._detection_msg(),s2z.SCHEMA_ID,registration=T._store(T._latency_registration_msg(v)),timing_quality=dict(tq))[0];print(tag,ev['payload']['timing_quality'],s2z.validate(ev)[0])"
# 0.5s   est_error_ms=505.0 pass
# 1e308s est_error_ms=  5.0 pass
# NaN    est_error_ms=  5.0 pass

### R1-04 (MAJOR) — The A-02 pin is vacuous: `_assert_clean` is satisfied by an empty event list, so 7 of 13 parametrized cases pass with the fix they name reverted — the whole `registration_state.duration_ms` member has zero coverage

**Location:** `adapters/ingress/sapient/test_sapient_ingress.py:1576`

**Claim:** `_assert_clean(events, label)` is `for event in events: <assert>`. When `translate()` returns `[]` the loop body never executes and the function asserts nothing. Reverting a per-field guard does not make poison escape — it makes the emit-boundary backstop refuse the *whole event*, so the list goes empty and the test still passes. The oracle is scoped to the emitted set rather than to the disposition, which is structurally the same mis-scoping as A-02 itself (guard the operand, not the product): a guard that is blind precisely where the thing it checks changes shape.

**Evidence:**

```
Revert-simulation via a pytest plugin that patches only the module attribute (global lookup, so all internal call sites see it):
  REVERT=finite   (`s2z._finite = lambda v: v`, backstop + sub_class guard left intact)
     -> 93 passed, 1 failed. The ONLY failure is `test_non_finite_bearing_product_never_stamps_true_north`.
     All 13 `_NON_FINITE_CASES` pass.
  REVERT=duration (`registration_state.duration_ms` finiteness check removed, everything else intact)
     -> 94 passed, 0 failed. Both of its named pins — "declared maximum_latency overflows the est_error_ms widen" and "declared maximum_latency is NaN" — pass.
Emitted-event counts per parametrized case, fixed tree vs each revert (probe: adapters/ingress/sapient/test_sapient_ingress.py::_NON_FINITE_CASES driven directly):
  case                                                      FIX  ~fin  ~dur
  centre_frequency MHz scaling overflows                      0     0     0
  band-edge difference overflows between two finite edges     4     0     4
  TRUE-datum azimuth radians->degrees overflows               1     0     1
  MAGNETIC-datum native azimuth/elevation overflow            1     0     1
  range km->m scaling overflows                               1     0     1
  declared maximum_latency overflows (store rebuilt)          4     4     0
  declared maximum_latency is NaN (store rebuilt)             4     4     0
  status report power level and fov are non-finite            2     2     2
The delta the tests cannot see is 4 events vs 0 events, i.e. the difference between "the detection is emitted with an honest partial disposition" and "the node's entire report disappears silently". Three cases (centre_frequency, promotion freshness, caller est_error_ms) emit zero events even on the FIXED tree, so their assertion body never runs in the passing baseline either.
```

**Reproduction:** cd <repo>
# plugin file (scratchpad), pytest_configure: `from adapters.ingress.sapient import sapient_to_zmeta as s2z; s2z._finite = lambda v: v`
REVERT=finite   PYTHONPATH="<scratchpad>;." python -m pytest adapters/ingress/sapient/test_sapient_ingress.py -q -p atk_revert   # 93 passed, 1 failed
# plugin variant replacing registration_state.duration_ms with the pre-fix body (no math.isfinite(scaled))
REVERT=duration PYTHONPATH="<scratchpad>;." python -m pytest adapters/ingress/sapient/test_sapient_ingress.py -q -p atk_revert   # 94 passed, 0 failed
# behavioural delta the tests miss:
python -c "import sys;sys.path.insert(0,'.');import importlib.util,adapters.ingress.sapient.sapient_to_zmeta as s2z,adapters.ingress.sapient.registration_state as rs;spec=importlib.util.spec_from_file_location('t','adapters/ingress/sapient/test_sapient_ingress.py');T=importlib.util.module_from_spec(spec);spec.loader.exec_module(T);print(len(s2z.translate(T._detection_msg(),s2z.SCHEMA_ID,registration=T._store(T._latency_registration_msg(1e308)))))"   # 4 with the fix, 0 without

### R1-05 (MAJOR) — `test_non_finite_rf_product_leaves_the_signal_block_as_provenance` never executes the code it claims to pin — the registration it uses declares no signal units, so the frequency arithmetic is unreachable

**Location:** `adapters/ingress/sapient/test_sapient_ingress.py:1774`

**Claim:** The test is the only dedicated pin for family-1 member 1 (`_freq_hz`'s `float(value) * factor`). It passes `registration=_store(_camera_registration_msg())` at :1788, and that fixture is explicitly "WITHOUT declared signal units" (test_sapient_ingress.py:96-97). `_canonical_rf_features` returns None on its first line (`if not signals or not isinstance(signals[0], dict) or not signal_units`) before `_freq_hz` — and therefore `_finite` — is ever reached. Both of the test's assertions are then trivially true for a reason unrelated to the fix: `payload["features"]` is the empty dict, and the signal block falls into vendor provenance because units are unresolvable, exactly as it did before the fix.

**Evidence:**

```
Instrumented `_finite` to log every call during that test's exact `translate()`:
  signal_units declared by that registration: {}
  _finite call count during that test's translate(): 1  ->  [10.0]      # the azimuth, not a frequency
  events: 1
  features: {}
So `assert "center_freq_hz" not in payload["features"]` passes against an empty features dict, and `assert payload["extensions"]["vendor.sapient"]["signal"][0]["centre_frequency"] == 1e308` passes because unresolved units — not the overflow guard — sent the signal block to the vendor extension. Corroborated by the revert run: with `s2z._finite` reverted to identity this test still passes (it is not among the failures in the REVERT=finite run above).
```

**Reproduction:** python -c "import sys;sys.path.insert(0,'.');import importlib.util,adapters.ingress.sapient.sapient_to_zmeta as s2z;spec=importlib.util.spec_from_file_location('t','adapters/ingress/sapient/test_sapient_ingress.py');T=importlib.util.module_from_spec(spec);spec.loader.exec_module(T);store=T._store(T._camera_registration_msg());print('signal_units=',store.signal_units(T.NODE));calls=[];o=s2z._finite;s2z._finite=lambda v:(calls.append(v),o(v))[1];ev=s2z.translate(T._detection_msg(signal=[{'amplitude':-57.0,'centre_frequency':1e308}],range_bearing={'azimuth':10.0,'coordinate_system':'RANGE_BEARING_COORDINATE_SYSTEM_DEGREES_M','datum':'RANGE_BEARING_DATUM_TRUE'}),s2z.SCHEMA_ID,registration=store);s2z._finite=o;print('_finite calls=',calls);print('features=',ev[0]['payload']['features'])"
# -> signal_units= {} ; _finite calls= [10.0] ; features= {}

### R1-06 (MAJOR) — NaN confidence is laundered to 1.0 (maximum confidence) and forwarded — the mutation runs upstream of the new gate

**Location:** `gateway/src/validators.py:565`

**Claim:** `apply_timing_freshness_degradation` clamps confidence with `max(0.0, min(1.0, confidence / factor))` (validators.py:565). `min(1.0, nan)` returns 1.0 in Python, so a NaN confidence is rewritten to **1.0 — maximum confidence** — and the STATE_EVENT is forwarded. The new value-scoped gate never sees it: `process_message` calls this mutation at gateway.py:1661 and only reaches `validate_semantics` at gateway.py:1691. jsonschema lets NaN past `maximum: 1` vacuously (which is the whole premise of A-01), so this is the one confidence value that survives to the clamp: +inf and -inf are caught by the schema, NaN is not. The forwarded event even carries a risk record asserting `"effects": {"confidence_reduction_factor": 2.0}` — it claims its confidence was halved when it was in fact fabricated from a value that carried no claim at all, and raised to certainty. This is the exact field the pre-existing NON_FINITE_CONFIDENCE guard was written to protect, and the author's class statement (2) "BOTH KERNEL GATES ... One change closes both" is false for the ingress gate: there is a mutation in front of it. The author's own pin is blind by construction — every test in gateway/tests/test_non_finite_value_scoped.py calls `process_message` without `timing_state`, so the entire `if timing_state is not None:` block at gateway.py:1652-1679 is skipped in all 15 tests.

**Evidence:**

```
Live probe, shipped schema + shipped policy with only `timing_freshness.mode: degrade` (a documented operator mode: policy/README.md:74-79, docs/s1_14_external_projection_promotion_contract.md:37), `strict_validation=False` (the gateway default, gateway.py:1203):
  confidence in = nan          -> emitted 2  STATE_EVENT confidence out = 1.0   <-- FORWARDED
  confidence in = +inf         -> emitted 1  SYSTEM_EVENT (refused by schema maximum)
  confidence in = -inf         -> emitted 1  SYSTEM_EVENT (refused by schema minimum)
  confidence in = control 0.62 -> emitted 2  STATE_EVENT confidence out = 0.31
And with `missing_mode: degrade` instead of `mode: degrade`, identical result. The forwarded event's `payload.extensions.risk_adjudication[0]` reads `{"policy_decision": "DEGRADED_ACCEPT", "effects": {"confidence_reduction_factor": 2.0}}`. `strict_validation=True` refuses; the default False does not.
Same clamp, same family, three more sites: validators.py:774 `_reduce_confidence`, validators.py:782 `_cap_confidence` (both post-gate, so currently unreachable with NaN), and gateway.py:1112 `_apply_failure_mode_degradation`, which sits at gateway.py:2035 *before* the egress gate at gateway.py:2041 — the identical ordering error on the egress side.
```

**Reproduction:** python - <<'PY'
import importlib.util, json, copy
from pathlib import Path
ROOT=Path('.').resolve()
def load(n,r):
    s=importlib.util.spec_from_file_location(n,ROOT/r); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
validators=load('v','gateway/src/validators.py'); gateway=load('g','gateway/src/gateway.py')
policy=validators.load_policy(ROOT/'policy')
validator=validators.load_schema(ROOT/'schema'/'zmeta-event-1.0.schema.json')
ev={'zmeta_version':'1.0',
 'event':{'event_id':'019c2b5c-c047-73ea-8f1a-302b9d9c0aa4','event_type':'STATE_EVENT','event_subtype':'TRACK_STATE','ts':'2025-01-17T14:40:00Z'},
 'source':{'platform_id':'lora-node-01','node_role':'GATEWAY','producer':'sensorops'},
 'profile':'L','payload':{'track_id':'track-l-001','geo':{'lat':34.0001,'lon':-118.0001,'alt_m':100.0},'valid_for_ms':1000},
 'confidence':float('nan'),'lineage':{'based_on':['019c2b5c-c047-73ea-8f1a-302e4b7b0aa4']}}
p=copy.deepcopy(policy); p['timing_freshness']['mode']='degrade'
out=gateway.process_message(json.dumps(ev).encode(),validator,p,'L',{},'json',
     timing_state=validators.ValidationState(),strict_validation=False)
for e in out:
    print(e['event']['event_type'], 'confidence =', repr(e.get('confidence')))
PY
# -> STATE_EVENT confidence = 1.0

### R1-07 (MAJOR) — The new routing lint silently skips the exact mangle it targets, one container up: `routing:` bare/scalar → CLI exit 0 while every event crashes; `routng:` typo → CLI exit 0 and the routing allowlist fails OPEN

**Location:** `gateway/src/validators.py:1774`

**Claim:** `lint_routing_producer_enforcement_structure` — the function added specifically to close the routing member of the A-05 family — begins `routing = policy.get("routing"); if not isinstance(routing, dict): return issues` (validators.py:1773-1775). That is a silent early-return on precisely the bare-key / wrong-type mangle the function exists to catch, applied to the block that HOLDS the key. `validate_routing` has no dict guard on `routing_policy` (validators.py:2857-2861), so the same input raises on every event. The author's own design note says the fix must 'not be quieter than the AttributeError it replaces' — they applied that rule to `routing.producer_enforcement` (validators.py:1794-1800) and not to `routing` itself. Worse, `load_policy` line 135 does `routing_cfg.get("routing", {})`, so a typo in the file's top-level key silently yields `{}` and the whole routing policy evaporates — while the producer-authority twin of that typo IS caught, because line 136 falls back to the whole document. The claim 'Zero green-light cells remain in the producer-authority + routing-enforcement key space' is false at the root of the routing half.

**Evidence:**

```
Shipped `tools/lint_policy_risk_modes.py` CLI on scratch copies of `policy/` (repo untouched), then the shipped enforcement on the same tree:
  policy/routing.yaml truncated to `routing:`
    CLI exit=0  stdout='policy risk mode lint ok'  stderr=''
    validate_routing, ALL four probes -> RAISED AttributeError: 'NoneType' object has no attribute 'get'
    end-to-end gateway.process_message (schema-valid profile-H STATE_EVENT, registered producer `fusion-engine`):
      RAW AttributeError: 'NoneType' object has no attribute 'get'  <- 100% outage, backstop reports INTERNAL_ERROR and names no policy problem
  policy/routing.yaml top key -> scalar (`routing: producers`)
    CLI exit=0 'policy risk mode lint ok'  ->  AttributeError on every event
  policy/routing.yaml top key typoed `routng:`  (policy['routing'] becomes {})
    CLI exit=0 'policy risk mode lint ok'
    cot-ingress INFERENCE_EVENT: shipped ok=False ['EVENT_TYPE_NOT_ALLOWED_FOR_ROLE']  ->  ok=True []   <- FAIL OPEN
  ASYMMETRY, same one-word mangle in the sibling file:
    producer-authority.yaml `producer_authorityy:` -> CLI exit=1, two named diagnostics
    routing.yaml            `routng:`              -> CLI exit=0, 'policy risk mode lint ok'
  Calling only the two structure lints (no CLI): 0 issues for routing=None / 'producers' / ['x'] / 7.
```

**Reproduction:** python "C:\\Users\\User\\AppData\\Local\\Temp\\claude\\C--Users-User-Desktop-General-Requirements-Documents-Future-Ideas-Z-ISR-ZMeta-zmeta-spec\\7f5e13b1-40a9-4010-a3e1-17156d83755b\\scratchpad\\atk_root.py"  (CLI + enforcement, all four routing-root mangles)
python "...\\scratchpad\\atk_a05_e2e.py"  (end-to-end through gateway.process_message)
python "...\\scratchpad\\atk_fp.py"  (the producer-authority vs routing typo asymmetry)

### R1-08 (MAJOR) — `routing.producers.<p>.*` got no shape table and no lint, while the structurally identical `producer_authority.producers.<p>.*` did — the same fail-open cell the author lists as fixed, unfixed on the other half of the family

**Location:** `gateway/src/validators.py:1533`

**Claim:** `_ROUTING_PRODUCER_ENFORCEMENT_SHAPES` (validators.py:1533) declares exactly one key. But `validate_routing` reads a second producer-entry vocabulary with the identical `_list_values` collapse-to-no-constraint semantics: `rule.get("allowed_event_types")` / `allowed_event_subtypes` / `forbidden_event_types` at validators.py:2894-2902, plus the `routing.producers.<p>` entry itself. The author declared `_PRODUCER_ENTRY_SHAPES` for exactly these three key names on the producer-authority side (validators.py:1478-1482) and their own fail-open inventory names `producers.<p>.allowed_event_types = null` as a closed cell. It is closed on one side of a two-member family only — which is this repo's stated recurring failure mode, reproduced inside the change written to end it. The completeness pin cannot see it either: `ShapeTableCompletenessTest.SCOPES["validate_routing"]` (gateway/tests/test_policy_shape_fail_closed.py:546-548) declares only the local name `enforcement`, so the `rule.get(...)` reads in validate_routing's matching loop are invisible to the AST scan whose stated job is to prove the tables cover what enforcement reads.

**Evidence:**

```
Shipped CLI on scratch copies of policy/, then shipped enforcement:
  routing.producers.torch.allowed_event_types: <bare key>
    CLI exit=0 'policy risk mode lint ok'
    torch OBSERVATION_EVENT: shipped ok=False ['EVENT_TYPE_NOT_ALLOWED_FOR_ROLE']  ->  ok=True []   <- FAIL OPEN
  routing.producers.torch: <bare key>
    CLI exit=0 'policy risk mode lint ok'
    torch OBSERVATION_EVENT: ok=False ['EVENT_TYPE_NOT_ALLOWED_FOR_ROLE']  ->  ok=True []   <- FAIL OPEN
  Direct lint comparison of the two twins:
    producer_authority.producers.rf-sensor.allowed_event_types = null
      -> ['producer_authority.producers.rf-sensor.allowed_event_types']   (caught)
    routing.producers.torch.allowed_event_types = null
      -> []                                                              (green)
```

**Reproduction:** python "C:\\Users\\User\\AppData\\Local\\Temp\\claude\\C--Users-User-Desktop-General-Requirements-Documents-Future-Ideas-Z-ISR-ZMeta-zmeta-spec\\7f5e13b1-40a9-4010-a3e1-17156d83755b\\scratchpad\\atk_routing_producers.py"
Twin comparison (one-liner, read-only):
python -c "import importlib.util,copy;from pathlib import Path;R=Path(r'<repo>');v=importlib.util.spec_from_file_location('v',R/'gateway/src/validators.py');m=importlib.util.module_from_spec(v);v.loader.exec_module(m);P=m.load_policy(R/'policy');a=copy.deepcopy(P);a['producer_authority']['producers']['rf-sensor']['allowed_event_types']=None;b=copy.deepcopy(P);b['routing']['producers']['torch']['allowed_event_types']=None;print([i['path'] for i in m.lint_producer_authority_structure(a)]);print([i['path'] for i in m.lint_producer_authority_structure(b)+m.lint_routing_producer_enforcement_structure(b)])"

### R1-09 (MAJOR) — The new AST structural pin counts `else:` / `finally:` / `except:` bodies as INSIDE the guard, so it passes on a source where the recursive walk provably escapes

**Location:** `gateway/tests/test_compact_fail_closed.py:594`

**Claim:** `test_no_recursive_walk_runs_outside_the_fail_closed_guard` computes the set of "guarded" calls as `inside = {id(n) for n in ast.walk(tries[0]) if isinstance(n, ast.Call)}` (line 594). `ast.walk` over an `ast.Try` node visits `body`, `handlers`, `orelse` AND `finalbody`. Only `body` is protected by the except clauses. Code in an `else:` or `finally:` clause, or inside an except handler, is semantically OUTSIDE the guard — an exception raised there propagates raw — yet the pin classifies it as inside. The pin's entire stated purpose (its own docstring, line 536-547) is "nothing that can RecursionError may sit in front of the try that converts RecursionError into a refusal", and it cannot see the single most idiomatic way a future editor moves that code: `try/except/else` is the standard Python refactor for exactly this shape (a trailing statement after a try). This is the doctrine case named in the task — a fresh pin blind to the exact defect class it was written to prevent.

**Evidence:**

```
Re-ran the pin's algorithm verbatim against mutated sources of zmeta_compact.py.
  HEAD-as-fixed:                                    recursive=['_semantic_difference'] exposed=[] -> PIN PASSES
  MUT-1 `_semantic_difference` moved to `else:`:    recursive=['_semantic_difference'] exposed=[] -> PIN PASSES
  MUT-2 `_semantic_difference` moved to `finally:`: recursive=['_semantic_difference'] exposed=[] -> PIN PASSES
MUT-1 is not cosmetic. Building both sources as live modules and forcing `_semantic_difference` to raise RecursionError:
  HEAD (call in try body):                REFUSED -> "compact cannot serialize this event (RecursionError: ..."
  MUT-1 (call in `else:` of same try):    RAW RecursionError: maximum recursion depth exceeded   <-- escapes the guard
So a source the pin certifies as A-04-clean reproduces A-04's exact failure signature (raw RecursionError out of the public `dumps()` API, which in gateway._encode_outgoing_or_diagnostic is not in `_COMPACT_UNREPRESENTABLE` and drops the datagram).
Two secondary blind spots in the same test, found by the same reading:
- `funcs` (line ~575) and the nested-def vacuity guard (line ~617) both filter on `ast.FunctionDef` only. `ast.AsyncFunctionDef` is NOT a subclass, so an async def is excluded from both sides of the equality check — the vacuity guard cannot fire on it and the recursion scan cannot see it. (No async defs exist in the module today.)
- Because `_find_unencodable_int` is now iterative it is no longer a member of `recursive`, so the pin's live coverage is exactly one function, `_semantic_difference`. Moving `_find_unencodable_int`'s call back outside the try would not fail this pin.
```

**Reproduction:** python - <<'PY'
import ast, pathlib, types, json, copy
real = pathlib.Path('zmeta_compact.py').read_text(encoding='utf-8')
old = '''        difference = _semantic_difference(event, restored)\n    except CompactUnrepresentableError:\n        raise\n'''
new = '''    except CompactUnrepresentableError:\n        raise\n'''
# (full mutation moves the _semantic_difference line below the handlers into `else:`)
# then re-run the pin body from test_no_recursive_walk_runs_outside_the_fail_closed_guard
# on the mutated source -> exposed == [] -> pin PASSES
# and exec the mutated source as a module with _semantic_difference monkeypatched to
# raise RecursionError -> dumps() raises RAW RecursionError instead of CompactUnrepresentableError
PY
# (exact script used is reproduced in full in the finding evidence; it needs no repo edits)

### R1-10 (MAJOR) — Backend-dependent representability at nesting depth ~61-398 survives untouched: a cbor2-only install emits a "clean" compact packet that a conforming zmeta_cbor consumer cannot decode — and the fix's new comment asserts the opposite

**Location:** `zmeta_compact.py:501`

**Claim:** The fix added the comment "Representability must not depend on which CBOR library is installed." (zmeta_compact.py:501) and a new backend-parity pin. Both are true only for the crash-vs-refusal half of the problem. The encode-vs-refuse half is still wide open: with `zmeta_cbor` present, `_decode_cbor` bounds nesting at DEFAULT_MAX_DEPTH=64 (zmeta_cbor.py:20) so `_verified_compact_bytes` REFUSES from depth ~61 up; with only cbor2 (a configuration zmeta_compact.py:36-44 explicitly supports, and which the fix's own new test at test_compact_fail_closed.py:488 exercises by setting `zmeta_compact.zmeta_cbor = None`), cbor2's ceiling is 400, so depths ~61-398 ENCODE clean. `verify_representable()` — the function whose contract is "refuse any event the compact mapping cannot round-trip losslessly" (zmeta_compact.py:579) — returns silently, and gateway/src/gateway.py:949 forwards the datagram with no diagnostic. A conforming zmeta_cbor-backed consumer then cannot read it at all. This is the identical failure mode the module docstring (lines 19-25) says the in-mapping integer-range check exists to prevent, applied to the depth axis instead of the integer axis. The author disclosed deferring a mapping-level nesting limit as "escalation 2", which is a legitimate governance call — but the new comment at :501 states the property as achieved, and the new both-backends pin is written at a depth that structurally cannot see the gap.

**Evidence:**

```
Shipped Profile-L v1.0 event from examples/encoding-roundtrip.jsonl, `payload.extensions.vendor` = N-deep dict chain, sys.getrecursionlimit()==1000:
  depth  60  zmeta_cbor=ENCODED(472B)  cbor2=ENCODED(466B)  consumer(zmeta_cbor)=OK
  depth  64  zmeta_cbor=REFUSED        cbor2=ENCODED(478B)  consumer(zmeta_cbor)=ValueError: CBOR nesting exceeds max_depth
  depth  65  zmeta_cbor=REFUSED        cbor2=ENCODED(481B)  consumer(zmeta_cbor)=ValueError: CBOR nesting exceeds max_depth
  depth 100  zmeta_cbor=REFUSED        cbor2=ENCODED(586B)  consumer(zmeta_cbor)=ValueError: CBOR nesting exceeds max_depth
  depth 300  zmeta_cbor=REFUSED        cbor2=ENCODED(1186B) consumer(zmeta_cbor)=ValueError: CBOR nesting exceeds max_depth
  depth 399  zmeta_cbor=REFUSED        cbor2=REFUSED
End-to-end through gateway._encode_outgoing_or_diagnostic (--output-encoding compact, profile H), cbor2-only install:
  depth  65: forwarded=True  481B  reason_code=None            consumer(zmeta_cbor): ValueError: CBOR nesting exceeds max_depth
  depth 300: forwarded=True 1186B  reason_code=None            consumer(zmeta_cbor): ValueError: CBOR nesting exceeds max_depth
  depth 398: forwarded=True  342B  reason_code=ENCODING_UNSUPPORTED   consumer(zmeta_cbor): DECODED
The new pin cannot see this. `test_nesting_beyond_decode_depth_refuses_instead_of_raising` (test_compact_fail_closed.py:463) loops `self._both_cbor_backends()` but only at `depth = _hostile_depth()` == 100_000 (line 471), where both backends happen to refuse. Running that test's exact assertion at depth 300 instead:
  (a) backend=zmeta_cbor depth=300 -> refused
  (a) backend=cbor2     depth=300 -> NO REFUSAL  (assertRaises would FAIL)
The old pre-fix version of this test used depth 300 but only on the default backend, so no coverage was lost — but the new both-backends framing reads as parity assurance it does not provide. `test_backend_native_codec_errors_become_refusals` (line 488) uses depth 500, also above the window.
```

**Reproduction:** python - <<'PY'
import json, copy, zmeta_compact
ev = next(json.loads(l) for l in open('examples/encoding-roundtrip.jsonl', encoding='utf-8')
          if l.strip() and json.loads(l).get('zmeta_version') == '1.0')
def deep(d):
    r = c = {}
    for _ in range(d):
        n = {}; c['d'] = n; c = n
    return r
e = copy.deepcopy(ev)
e.setdefault('payload', {}).setdefault('extensions', {})['vendor'] = deep(300)
orig = zmeta_compact.zmeta_cbor
zmeta_compact.zmeta_cbor = None            # supported cbor2-only install
blob = zmeta_compact.dumps(e)              # NO refusal
zmeta_compact.zmeta_cbor = orig
print(len(blob), 'bytes accepted by verify_representable')
zmeta_compact.loads(blob)                  # ValueError: CBOR nesting exceeds max_depth
PY

### R1-11 (MODERATE) — mavlink_decoded_to_zmeta_system_events fabricates payload.state = "SYNCED" while the metrics block in the same payload says sync_state = "UNSYNCED" — and this is the function the new docstrings cite twice as the honest convention

**Location:** `adapters/ingress/mavlink/mavlink_to_zmeta_template.py:436`

**Claim:** `state = msg.get("state") or "SYNCED"` asserts a locked clock for a SYSTEM_TIME message that said nothing about sync, one line before :439 conservatively defaults `metrics["sync_state"]` to "UNSYNCED". The emitted event therefore contradicts itself, and the sibling `translate_time_status` maps that exact same sync_state to state="DEGRADED" (:595) — so the module now derives two opposite verdicts from identical input. The A-06 wave cited this function by name as the model to follow (docstrings at :492 and :566: "the same rule mavlink_decoded_to_zmeta_system_events applies to TIME_STATUS") without checking that the function's own categorical default is a fabrication of the same kind it was being cited against. The related TASK_ACK default `or "RECEIVED"` at :418 is the same shape.

**Evidence:**

```
Probe: mavlink_decoded_to_zmeta_system_events({'time_usec':1700000000000000,'est_error_ms':3.5,'last_sync_ts':'2025-01-17T15:19:00Z'}, ...) -> payload {'system_type':'TIME_STATUS','state':'SYNCED','metrics':{'time_source':'UNKNOWN','sync_state':'UNSYNCED','est_error_ms':3.5,...}}; jsonschema OK; validate_semantics (True, []). Same telemetry through translate_time_status(est_error_ms=1.0, last_sync_ts=...) -> payload state 'DEGRADED'. The TIME_STATUS branch of $defs/SystemPayload does not enum-constrain `state`, so nothing downstream catches the contradiction.
```

**Reproduction:** cd <repo> && python -c "import sys,json; sys.path.insert(0,'.')
from adapters.ingress.mavlink.mavlink_to_zmeta_template import mavlink_decoded_to_zmeta_system_events, translate_time_status
print(json.dumps(mavlink_decoded_to_zmeta_system_events({'time_usec':1700000000000000,'est_error_ms':3.5,'last_sync_ts':'2025-01-17T15:19:00Z'}, platform_id='uas-1', producer='mavlink-adapter', ts='2025-01-17T15:20:00Z')[0]['payload']))
print(json.dumps(translate_time_status(platform_id='uas-1', est_error_ms=1.0, last_sync_ts='2025-01-17T15:19:00Z', ts='2025-01-17T15:20:00Z')['payload']))"
-> state 'SYNCED' with sync_state 'UNSYNCED'
-> state 'DEGRADED' with sync_state 'UNSYNCED'

### R1-12 (MODERATE) — The family-wide provenance guard's constant allowlist is value-scoped, not path-scoped: a brand-new fabricated numeric equal to 30000 escapes BOTH sweeps and all 40 tests

**Location:** `adapters/ingress/mavlink/test_mavlink_ingress.py:481`

**Claim:** The guard exists specifically to catch "a newly added default in a field no per-field assertion above names" (its own comment at :472-476). It compares emitted numbers against a set of bare values, so allowlisting 30000 once whitelists the literal 30000 at EVERY path in the event, forever. 30000 is not an arbitrary number — it is this module's own house constant, used twice already (payload.valid_for_ms :264 and external_promotion.freshness_ms :233), and is exactly the value a future author would reach for when defaulting any new duration field (stale_after_ms, hold_ms, timeout_ms, a fabricated est_error_ms). It appears in both allowlists (:481-485 and :533), so unlike 0.2 — which the min-input sweep also misses but the fully-populated sweep catches, because the two allowlists differ — a 30000 fabrication is invisible to the entire pin set. Revert-simulation proof below: the module fabricates a new `payload.stale_after_ms: 30000` that no telemetry carried, and 40/40 tests pass.

**Evidence:**

```
test_mavlink_ingress.py:481-485 `declared_constants = {30000, 0.2, 60000}` and :533 `declared_constants = {30000, 0.8}`; `_invented_numerics` at :461-462 `if node not in reported and node not in declared_constants: invented.append(...)` — membership is by value only, the path string built at :455-459 is used solely for the failure message and never constrains anything. Mutation harness result: MUTATION=new_field_30000 -> 40 passed, pytest_rc=0. Control mutations that the guard DOES catch: heading_90 -> 1 failed, sats_8 -> 3 failed, speed_zero -> 3 failed, new_quality_0p2 -> 1 failed.
```

**Reproduction:** Read-only in-memory revert simulation (no repo file touched). Harness at <scratchpad>/mutate.py loads mavlink_to_zmeta_template.py, string-replaces the source, installs the mutant into sys.modules under the real name, and runs the pin file.
  python <scratchpad>/mutate.py new_field_30000
Mutation applied: after `"valid_for_ms": 30000,` (template :264) insert `"stale_after_ms": 30000,` — a numeric the telemetry never carried.
Result: `40 passed  MUTATION=new_field_30000 pytest_rc=0`
Contrast: `python <scratchpad>/mutate.py new_quality_0p2` (same fabrication with value 0.2) -> `1 failed, 39 passed` — caught only because 0.2 is absent from the SECOND test's allowlist.

### R1-13 (MODERATE) — The provenance guard is type-scoped to int/float, so a fabricated number emitted as a string escapes entirely — and the module's own idiom is str()-wrapped defaults

**Location:** `adapters/ingress/mavlink/test_mavlink_ingress.py:460`

**Claim:** `_invented_numerics` classifies a leaf as checkable only via `isinstance(node, (int, float))` (:444 in the input collector, :460 in the event walker). Any fabricated value that is a string — including a stringified number — is invisible. This is not hypothetical for this file: the promotion block at template :225-232 wraps every one of its defaults in `str(...)`, that is the house idiom here; and the CoT egress this finding's own impact chain runs through emits altitude as the string `hae="0.0"`. The same type-scoping is what makes the guard structurally unable to see the two live categorical fabrications reported above (`state: "UP"` at template :535 and `state: "SYNCED"` at :436) — a guard written to enforce "nothing this adapter emits is a value the telemetry did not carry" cannot see two values the adapter emits that the telemetry did not carry.

**Evidence:**

```
test_mavlink_ingress.py:444-445 and :460-462 — both walkers fall through to `elif isinstance(node, (int, float))`, everything else is silently dropped. Mutation result: MUTATION=alt_string_zero -> 40 passed, pytest_rc=0. README.md:120-121 states the property the guard is meant to enforce in whole-adapter terms ("Nothing this adapter emits is a value the telemetry did not carry"), which is broader than what the guard can check.
```

**Reproduction:** python <scratchpad>/mutate.py alt_string_zero
Mutation applied to translate_platform_state: emit `quality["reported_alt_agl_m"] = "0.0"` — a fabricated altitude-above-ground claim the telemetry never made, written as a string.
Result: `40 passed  MUTATION=alt_string_zero pytest_rc=0`
(Identical fabrication written as the float 0.0 is caught: `python <scratchpad>/mutate.py new_quality_0p2` style mutations fail the sweep.)

### R1-14 (MODERATE) — Wire data still crashes `translate()` and `RegistrationStore.ingest()`: a legal JSON integer literal too large for float64 raises OverflowError inside the guard line itself — the arm of the overflow family the author's sweep never injected

**Location:** `adapters/ingress/sapient/sapient_to_zmeta.py:120`

**Claim:** `_is_number` ends with `math.isfinite(value)`, which raises `OverflowError: int too large to convert to float` for a Python int outside float64 range. `json.loads` produces exactly such an int from a plain integer literal, so a 400-digit number anywhere in a DetectionReport aborts `translate()` instead of refusing. The same shape is on the line `duration_ms` just rewrote (registration_state.py:107, `scaled = float(value) * factor`), where the new `math.isfinite(scaled)` on the next line is never reached — so a single Registration with `maximum_latency: {SECONDS, 10**400}` takes down `RegistrationStore.ingest()` for that store. This violates the module's own stated discipline at sapient_to_zmeta.py:270 — "wire data must never crash the ingest loop (fail closed)" — which is the exact line the A-02 audit report cited as the module's threat model (docs/r1_11_full_stack_audit.md:1022). `_envelope_ts` illustrates the inconsistency in one function: it wraps `datetime.fromtimestamp` in `except (OverflowError, OSError, ValueError)` at :271-275, but its own `_is_number(seconds)` at :266 raises before the try. The author's adversarial sweep injected only NaN/+inf/-inf/1e308/-1e308 — all floats — so it is blind by construction to the finite-but-unrepresentable arm of the same magnitude family the guard is about.

**Evidence:**

```
Sweep of 10**400 and -10**400 at every leaf of a rich DetectionReport (multi-signal, range_bearing with per-axis errors, enu_velocity, nested sub_class), 33 leaves each:
  huge int 10**400        crashes=18  leaks=0  ok=15
  neg huge int -10**400   crashes=18  leaks=0  ok=15
  proto3 JSON "NaN"       crashes= 0  leaks=0  ok=33
  proto3 JSON "Infinity"  crashes= 0  leaks=0  ok=33
First crash traceback (leaf $.detection_report.location.x):
  sapient_to_zmeta.py:120, in _is_number -> `and math.isfinite(value)` -> OverflowError: int too large to convert to float
Registration side:
  registration_state.py:107, in duration_ms -> `scaled = float(value) * factor` -> OverflowError, raised from RegistrationStore.ingest()
And `detect()` accepts the message first, so the adapter claims the input and then throws:
  detect({'timestamp':{'seconds':10**400,...}}) -> 'vendor:sapient_bsi335:v2'
  translate(same)                               -> OverflowError at sapient_to_zmeta.py:120
```

**Reproduction:** python -c "import sys,json;sys.path.insert(0,'.');import adapters.ingress.sapient.sapient_to_zmeta as s2z;raw={'timestamp':{'seconds':10**400,'nanos':0},'nodeId':'n','detectionReport':{'reportId':1}};print('detect:',s2z.detect(json.dumps(raw).encode()));s2z.translate(raw,s2z.SCHEMA_ID)"
# detect: vendor:sapient_bsi335:v2
# OverflowError: int too large to convert to float  (sapient_to_zmeta.py:120)
python -c "import sys;sys.path.insert(0,'.');import importlib.util,adapters.ingress.sapient.sapient_to_zmeta as s2z;spec=importlib.util.spec_from_file_location('t','adapters/ingress/sapient/test_sapient_ingress.py');T=importlib.util.module_from_spec(spec);spec.loader.exec_module(T);T._store(T._latency_registration_msg(10**400))"
# OverflowError: int too large to convert to float  (registration_state.py:107)

### R1-15 (MODERATE) — The new backstop escalates a vendor pass-through problem into total loss of the detection, against the module's own vendor-block doctrine — one weird key silently turns 4 events into 0

**Location:** `adapters/ingress/sapient/sapient_to_zmeta.py:216`

**Claim:** `_drop_non_finite` (:145-165) states the module's rule for vendor blocks: "Applied to verbatim vendor blocks only — canonical fields refuse via _is_number instead... Dropping the key is the honest shape". It strips non-finite VALUES but not non-finite KEYS. Rather than closing that gap where the doctrine lives, the fix added an emit-boundary refusal that discards the whole event and cascades to every inference citing it. The result is that a defect confined to a provenance blob now destroys canonical data the adapter successfully resolved — geo, bearing, RF features, classification inferences — with no exception, no diagnostic and no marker; `translate()` simply returns `[]`, which the caller cannot distinguish from "the sensor reported nothing". The author's own pin (`test_refusing_a_parent_refuses_its_dependents_too`, :1850) asserts `events == []` and calls that the desired outcome. Reachability is thin (not producible from protobuf-JSON; the author cites CBOR-derived dicts), which is why this is MODERATE — but the in-class fix is at `_drop_non_finite`, not at the emit boundary.

**Evidence:**

```
Same DetectionReport, only the vendor `track_info` blob changed:
  clean detection         -> 4 events: OBSERVATION_EVENT/RF, INFERENCE_EVENT/CLASSIFICATION, INFERENCE_EVENT/BEHAVIOR, INFERENCE_EVENT/CLASSIFICATION
  + non-finite VENDOR key -> 0 events (silently, no exception)
And the layer that is supposed to handle it does not:
  _drop_non_finite({'track_info': [{nan: 'x', 'ok': 1.0}]})  ->  {'track_info': [{nan: 'x', 'ok': 1.0}]}
The cascade logic itself is sound: I checked the fixed-point loop at :239-258 for the ordering and multi-parent cases and for the `refused_ids = newly_refused` replacement (safe — any event citing an earlier-round id is removed in that round), and REVERT=cascade correctly fails the dedicated test. The defect is the disposition, not the cascade.
```

**Reproduction:** python -c "import sys;sys.path.insert(0,'.');import importlib.util,adapters.ingress.sapient.sapient_to_zmeta as s2z;spec=importlib.util.spec_from_file_location('t','adapters/ingress/sapient/test_sapient_ingress.py');T=importlib.util.module_from_spec(spec);spec.loader.exec_module(T);m=T._detection_msg();print('clean ->',len(s2z.translate(m,s2z.SCHEMA_ID,registration=T._store(T._rf_registration_msg()))));m2=T._detection_msg();m2['detection_report']['track_info']=[{float('nan'):'x','ok':1.0}];print('poisoned vendor key ->',len(s2z.translate(m2,s2z.SCHEMA_ID,registration=T._store(T._rf_registration_msg()))));print(s2z._drop_non_finite({'track_info':[{float('nan'):'x','ok':1.0}]}))"
# clean -> 4 ; poisoned vendor key -> 0 ; {'track_info': [{nan: 'x', 'ok': 1.0}]}

### R1-16 (MODERATE) — The one-shot warning latch burns before delivery is confirmed: under the fix's own primary failure mode (full disk / closed pipe) the operator gets ZERO warnings for the entire run

**Location:** `gateway/src/gateway.py:557`

**Claim:** `MetricsLogger.write` sets `self._warned = True` (gateway.py:557) *before* calling `_warn_stderr(...)`, and discards the boolean `_warn_stderr` already returns for exactly this purpose (gateway.py:237/239). `GatewayMetrics._print` has the identical bug at gateway.py:343. If the very first sink failure coincides with an unusable stderr, the latch is spent on an undelivered message and no warning is ever emitted again, even after stderr recovers. The coincidence is not exotic - it is the correlated case: the docstring and gateway/README.md name 'full disk' and 'closed pipe' as the primary causes, and both of those take out the metrics JSONL and a file-redirected or piped stderr at the same instant (same filesystem under ENOSPC; the same broken pipe under `gateway.py 2>&1 | consumer`). This is the doctrine's 'shares machinery with the thing it checks': the sole report channel fails for the same root cause as the sink it reports on, and the guard has no retry. The pin is blind to it by construction - test_gateway_runtime_guards.py:457 `test_backstop_helper_survives_a_broken_stderr` asserts only `metrics.window['drops'] == 1`, i.e. that nothing raises; it never asserts the operator ever learns anything. In-class one-line remedy, no new vocabulary: `self._warned = _warn_stderr(...)` (and `self._console_warned = _warn_stderr(...)`), which retries on the next failure until the report actually lands.

**Evidence:**

```
Real `MetricsLogger` + real `_warn_stderr`, ENOSPC on both the log path and stderr for the first record only, then stderr restored:
    write_failures = 1001
    warnings ever delivered = 0
    stderr output for the rest of the run = ''
Same latch defect on the console sink (gateway.py:343), stderr broken only for the first `maybe_log`:
    _console_warned latch: True
    console_failures: 11
    warnings EVER delivered: 0
```

**Reproduction:** python - <<'EOF'
import importlib.util, io, contextlib, tempfile
from pathlib import Path
sp=importlib.util.spec_from_file_location('gw', Path.cwd()/'gateway'/'src'/'gateway.py')
gw=importlib.util.module_from_spec(sp); sp.loader.exec_module(gw)
class Full(io.TextIOBase):
    def write(self,_t): raise OSError(28, "No space left on device")
tmp=Path(tempfile.mkdtemp()); (tmp/"logs").write_text("x",encoding="utf-8")
lg=gw.MetricsLogger(tmp/"logs"/"metrics.jsonl")
with contextlib.redirect_stderr(Full()):          # disk full: log sink AND stderr both fail
    lg.write({"type":"violation","code":"SCHEMA_INVALID"})
after=io.StringIO()
with contextlib.redirect_stderr(after):           # disk freed, stderr usable again
    for i in range(1000): lg.write({"type":"violation","code":"SCHEMA_INVALID","n":i})
print("write_failures =", lg.write_failures)
print("warnings ever delivered =", after.getvalue().count("metrics log sink"))
EOF

### R1-17 (MODERATE) — After the single warning the degradation is silent, unquantified and unmarked: write_failures/console_failures have no output surface anywhere in the repo, yet the warning text tells the operator to consult them

**Location:** `gateway/src/gateway.py:562`

**Claim:** The shipped warning ends '...further sink failures are not repeated (see write_failures)' (gateway.py:562) and '(see console_failures)' (gateway.py:348). A repo-wide grep shows `write_failures` and `console_failures` are assigned at gateway.py:503/555 and 257/341 and read nowhere except the tests - they are absent from `maybe_log`'s periodic stdout summary (gateway.py:414-493), from the `metrics` JSONL record, and from every doc. The message points the operator at a counter that has no output surface. The consequence is the class the fix was written to satisfy, inverted: `MetricsLogger` keeps retrying, so a sink that fails and recovers leaves an *unmarked gap* in the JSONL - the file reads as continuous - while the periodic summary an operator actually watches reports the full in-memory totals and shows no sign of loss. README.md:480 directs the operator to that very file ('Verify metrics and drops in logs'). Rule 5: a refusal must be honest, filterable and carry a reason the consumer can act on; after datagram #1 this is silence. Two further inconsistencies in the same message: it asserts 'metrics logging is degraded for the rest of this run', which contradicts both its own docstring ('Writes keep being attempted, so the sink recovers on its own') and the observed behaviour below - records resumed after recovery. Emitting the two counters on the existing stdout summary line (alongside `send_failures`) needs no governed reason_code and is strictly in-class; the author's vocabulary note only ruled out an in-band diagnostic bucket, not this.

**Evidence:**

```
Real `MetricsLogger`/`GatewayMetrics`, sink healthy -> dies for 200 records -> recovers:
    records in metrics.jsonl: ['e1', 'e2', 'e203', 'e204']
    lost silently          : 200
    logger.write_failures  : 200 (never printed anywhere)
    stderr lines           : 1
    --- operator stdout summary ---
    metrics interval=1s recv=0 ... drops=0 violations=204 warnings=0 duplicates=0
    metrics violation_codes=SCHEMA_INVALID:204
    summary mentions write_failures: False
    jsonl mentions a gap marker    : False
A consumer reading metrics.jsonl sees four contiguous violation records and no marker; the summary says 204. Also note e203/e204 landed, disproving 'degraded for the rest of this run'.
    $ grep -rn 'write_failures\|console_failures' --include=*.py --include=*.md --include=*.yaml .
    gateway/src/gateway.py:257,341,348,503,555,562   (assignment + its own message text)
    gateway/tests/test_gateway_runtime_guards.py:318,340,391
    (no other reader; not in maybe_log, not in any doc)
```

**Reproduction:** Run the phase probe: build a MetricsLogger on a live path, record two violations, replace the parent directory with a regular file, record 200 more, restore the directory and the saved file, record two more, then `maybe_log()`. Inspect metrics.jsonl (4 records, no gap marker), `logger.write_failures` (200, never emitted), and the stdout summary (violations=204, no loss indication).

### R1-18 (MODERATE) — The gateway's own refusal event still ships a raw NaN — `validate_timing_quality` echoes event-derived floats and runs before the gate

**Location:** `gateway/src/validators.py:1981`

**Claim:** The author's stated sub-case (5) — "semantic checks that echo the offending value into `details` fed a NaN into `payload.metrics` of the SYSTEM_EVENT ... Closed by ordering the gate first" — is closed only *within* `validate_semantics`. `validate_timing_quality` runs at gateway.py:1653, ahead of `validate_semantics` at gateway.py:1691, and its HOLDOVER-monotonic check copies `float(metrics.get('est_error_ms'))` verbatim into violation details as `current_est_error_ms` (validators.py:1965, :1981). `build_violation_event` merges details into `payload.metrics` (gateway.py:1456), and `process_message` returns that diagnostic at gateway.py:1670-1677 without ever reaching the gate. The emitted refusal fails `json.dumps(..., allow_nan=False)` — the gateway's own diagnostic is not RFC 8259, which is the precise harm A-01 names. NaN also defeats the check's own logic: `current_error >= previous_error` is False for NaN, so a NaN est_error_ms is reported as a *decrease* in holdover error.

**Evidence:**

```
Live probe, shipped schema, shipped policy except `timing_freshness.holdover_est_error_monotonic.mode: reject` (`_timing_mode`-style validation at validators.py:1971-1973 accepts exactly {warn, reject}; shipped default is warn):
  mode=reject strict=False -> emitted 1
    SYSTEM_EVENT SCHEMA_VIOLATION {"reason_code": "TIMING_STATUS_HOLDOVER_NON_MONOTONIC", ..., "previous_est_error_ms": 50.0, "current_est_error_ms": NaN, ...}
    *** LAUNDERED / NON-RFC8259: Out of range float values are not JSON compliant: nan
  mode=reject strict=True  -> identical
  mode=warn (shipped)      -> clean: the warning is discarded and validate_semantics returns {"field": "payload.metrics.est_error_ms"}
Schema is not a backstop: `est_error_ms` is `{"type": "number", "minimum": 0}` and NaN passes both vacuously. The pin cannot see this either — no test in gateway/tests/test_non_finite_value_scoped.py passes `timing_state`.
```

**Reproduction:** Record a prior TIME_STATUS with sync_state=HOLDOVER, est_error_ms=50.0 into a ValidationState, set policy `timing_freshness.holdover_est_error_monotonic.mode: reject`, then process a second TIME_STATUS from the same source with `payload.metrics.est_error_ms = float('nan')`, time_source GPS_PPS. `json.dumps(out[0], allow_nan=False)` raises `ValueError: Out of range float values are not JSON compliant: nan`.

### R1-19 (MODERATE) — `_find_non_finite` does not traverse sets — a CBOR tag-258 set carrying NaN passes the whole kernel and reaches the CBOR wire

**Location:** `gateway/src/validators.py:361`

**Claim:** The container dispatch is `isinstance(current, dict)` / `elif isinstance(current, (list, tuple))` (validators.py:356, :361). `set` and `frozenset` are neither, so their members are never enqueued and never checked. This is reachable: `_decode_cbor` falls back to `cbor2.loads` when `zmeta_cbor` is absent (gateway.py:881-885, a branch `_require_cbor` at :841 explicitly supports), and cbor2 decodes CBOR tag 258 into a Python `set`. The author's completeness claim (8) is about the *leaf* type (`isinstance(x, float)` covers bool/int/CBOR float16-32-64/bignum/Decimal) and never enumerates the *container* types the traversal dispatches on — which is the same shape of omission as the field list A-01 names, moved one level up. It also contradicts the guard's own stated threat model, since the float-map-key case it does handle is reachable only from the same exotic-CBOR direction. All four new adapter guards share the omission verbatim: adapters/egress/klv/zmeta_to_klv_tagdict_template.py:17, adapters/egress/jreap/zmeta_state_to_jreap_track_json.py:18, adapters/egress/mavlink/zmeta_command_to_mission_intent.py:49.

**Evidence:**

```
Live probe on the cbor2 backend (`gateway.zmeta_cbor = None`), shipped schema and policy, shipped Profile-L TRACK_STATE with `payload.extensions['acme.telemetry'].samples = CBORTag(258, [1.0, nan])`:
  decoded samples: <class 'set'> {1.0, nan}
  _find_non_finite -> None
  emitted: [('STATE_EVENT', 'TRACK_STATE')]          <-- FORWARDED, strict_validation=True
  *** cbor wire carries: {1.0, nan}  non-finite present: True
By encoding: the CBOR wire carries the NaN, while JSON egress raises TypeError into the A-03 backstop and drops — i.e. whether the event is refused is decided by the operator's encoding, which is the sentence A-01 is built on. Adapter guards, same input shape:
  klv     _has_non_finite({'a': {nan}}) -> False   (list control: True)
  jreap   _has_non_finite({'a': {nan}}) -> False   (list control: True)
  mavlink _has_non_finite({'a': {nan}}) -> False   (list control: True)
  klv tagdict for a set-valued feature -> {..., 'features': {'samples': {1.0, nan}}}
Honest scope: `zmeta_cbor.py` is a repo file, so an in-repo gateway uses the preferred backend (which decodes tag 258 to a list and is caught). This is the shipped cbor2 fallback branch, which the audit itself already treats as a live divergence surface (docs/r1_11_full_stack_audit.md:1063).
```

**Reproduction:** python - <<'PY'
import importlib.util, cbor2, math
from pathlib import Path
ROOT=Path('.').resolve()
def load(n,r):
    s=importlib.util.spec_from_file_location(n,ROOT/r); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
v=load('v','gateway/src/validators.py'); g=load('g','gateway/src/gateway.py')
g.zmeta_cbor=None
print(v._find_non_finite({'a': {float('nan')}}))     # -> None  (list control returns a path)
PY

### R1-20 (MODERATE) — The list-entry check validates that entries are strings but not that they are event types — a one-character typo in `require_match_for_event_types` lints green and forwards the unregistered producer's track as clean authoritative state

**Location:** `gateway/src/validators.py:1578`

**Claim:** `_shape_problem`'s list branch (validators.py:1570-1581) rejects a list entry only when it is `not isinstance(item, str) or not item.strip()`, and its own diagnostic text explains why: a non-string entry 'is stringified into a token that can never match, silently dropping it from this check'. A *string* entry that can never match — `STATE_EVEN`, `state_event` — has the identical effect and is not checked, at either half of the fix (`_require_match_types` at validators.py:604-635 accepts any all-string list). The outcome is exactly A-05(b), the authorization bypass the guard was written for, reachable by deleting one character. The event-type vocabulary is a closed enum already in `schema/zmeta-event-1.0.schema.json`, and this same lint already validates closed vocabularies for key NAMES (`_PRODUCER_AUTHORITY_TOP_KEYS` etc.), so the value-side check is available without minting anything.

**Evidence:**

```
Shipped CLI on a scratch policy/ with one character changed in producer-authority.yaml:
  `- STATE_EVENT` -> `- STATE_EVEN`
    CLI exit=0 'policy risk mode lint ok'
    validate_producer_authority(totally-unregistered-node, STATE_EVENT): (True, [])
    shipped policy, same event:  (False, [PRODUCER_NOT_ALLOWED])
  `- STATE_EVENT` -> `- state_event`  : identical result
  End-to-end through the real gateway.process_message (schema-valid profile-H STATE_EVENT from `totally-unregistered-node`):
    shipped        -> forwarded=1 SYSTEM_EVENT/SCHEMA_VIOLATION reason=PRODUCER_NOT_ALLOWED
    typo'd entry   -> forwarded=1 STATE_EVENT/TRACK_STATE reason=None   <- the unregistered producer's track forwarded as clean authoritative state
    lowercase entry-> forwarded=1 STATE_EVENT/TRACK_STATE reason=None
  Generalised by an independent mutation sweep over both policy trees: the only lint-green cell that flips a shipped refusal into ok=True in the producer-authority half is `require_match_for_event_types` set to a well-shaped list of non-matching tokens.
```

**Reproduction:** python "C:\\Users\\User\\AppData\\Local\\Temp\\claude\\C--Users-User-Desktop-General-Requirements-Documents-Future-Ideas-Z-ISR-ZMeta-zmeta-spec\\7f5e13b1-40a9-4010-a3e1-17156d83755b\\scratchpad\\atk_a05_1.py"   (section F3: CLI + enforcement)
python "...\\scratchpad\\atk_a05_e2e.py"    (F3 rows, end-to-end)
python "...\\scratchpad\\atk_sweep.py"      (independent enumeration; the cell appears as FAIL-OPEN)

### R1-21 (MODERATE) — The iterative rewrite of _find_unencodable_int traded a crash for a non-terminating loop on self-referential structures — the exact trade its own docstring forbids

**Location:** `zmeta_compact.py:466`

**Claim:** The rewritten `_find_unencodable_int` (zmeta_compact.py:466-484) walks with an explicit stack and has no visited-set and no bound of any kind. On a structure containing a reference cycle it never terminates: every pop re-pushes the same node with one more link appended to the parent-linked path chain, so it spins forever while the heap grows without limit. The pre-fix recursive version terminated on the same input with RecursionError — and since the fix ALSO moved this call inside the try (line 553), the recursive version at HEAD would have produced a governed CompactUnrepresentableError refusal. The rewrite is the only reason that input no longer refuses. The function's own docstring, line 464, says "trading a crash for a hang is not a refusal"; the author's self-attack checked only linear depth (100k in 0.03s), which cannot expose aliasing. All four new pins build acyclic chains only, so nothing in the suite sees it.

**Evidence:**

```
Self-referential dict `d = {}; d['self'] = d`, run on a 3-second watchdog thread:
  cyclic dict, OLD recursive scan  -> RecursionError      (at HEAD's placement this would be a refusal)
  cyclic dict, NEW iterative scan  -> TIMEOUT -- did not terminate in 3s
Bounded replay of the exact loop body from zmeta_compact.py:467-483:
  400000 iterations in 1.17s, still 1 pending, traced heap 44.0 MB and rising -- no termination condition
Reachability, stated honestly: `json.loads` cannot construct a cycle, so this is NOT reachable from the gateway's JSON/CBOR/compact ingress path — the A-04 wire scenario is unaffected. It is reachable only from a Python caller that hands `dumps()`/`verify_representable()` a caller-constructed aliased object graph. Live in-repo callers of that API surface: gateway/src/gateway.py:775 and :949, tools/replay.py:75, tools/udp_sender.py:67, tools/convert_encoding.py:110, tools/measure_packet_size.py:67, tools/test_gateway_live.py:149-150, adapters that build events in Python. A hang in a sensor-side receive loop is a worse outcome than the crash it replaced (no diagnostic, no exit, no filterable reason), which is why the docstring rules it out. A fix is one line — an `id()`-keyed seen-set on containers, or a node budget — but I am read-only this phase.
Separately verified NOT a defect: a 40,000-case differential of the old recursive scan against the new iterative one over randomly generated structures (dicts, lists, bools, floats, NaN, str, bytes, tuples, sets, None, and every CBOR range boundary) produced 0 mismatches in result AND in path text. The rewrite is faithful on all acyclic input, and the traversal-order/path pin at test_compact_fail_closed.py:640 does constrain pre-order.
```

**Reproduction:** python - <<'PY'
import threading, zmeta_compact
d = {}; d['self'] = d
res = {}
def run():
    try:
        zmeta_compact._find_unencodable_int(d); res['r'] = 'returned'
    except RecursionError:
        res['r'] = 'RecursionError'
t = threading.Thread(target=run, daemon=True); t.start(); t.join(3)
print(res.get('r', 'TIMEOUT -- did not terminate'))
PY

### R1-22 (MINOR) — The CoT guard is field-scoped — the one new guard that reproduces the structural pattern A-01 names, and its list is already incomplete

**Location:** `adapters/egress/cot/zmeta_to_cot.py:136`

**Claim:** Every other guard in this change is value-scoped, on the author's own stated rationale that "a candidate list of numeric fields only closes the fields someone thought of". `zmeta_to_cot` is then given a candidate list of exactly nine plus three fields (`cot_numbers`, zmeta_to_cot.py:136-154) — the same construction as the `[confidence, payload.claim.confidence]` list A-01 was filed against. The list is already missing a member of its own kind: `cot_config['default_valid_for_ms']` (read at :175) feeds `timedelta(milliseconds=valid_for_ms)` at :177 and becomes the CoT `stale` attribute, yet only the *other* two config-supplied numbers (`default_ce`, `default_le`) are checked. The new docstring at :102-105 promises the adapter returns None for "any non-finite (NaN/inf) number that would become a CoT attribute"; for this one it raises instead. Not a laundering (it fails loud) and gateway-unreachable (gateway.py:2100 calls `zmeta_to_cot(outgoing)` with no config), but it is a demonstrable member the list forgot, in a guard whose author rejected lists as the root cause.

**Evidence:**

```
default_valid_for_ms=nan -> RAISED ValueError cannot convert float NaN to integer
  default_valid_for_ms=inf -> RAISED OverflowError cannot convert float infinity to integer
  clean                    -> <event version="2.0" type="a-u-G" uid="t1" ...
Contained by the per-datagram `except Exception` at gateway.py:2134, so it cannot take the receive loop down.
```

**Reproduction:** python - <<'PY'
import importlib.util
from pathlib import Path
ROOT=Path('.').resolve()
s=importlib.util.spec_from_file_location('cot',ROOT/'adapters/egress/cot/zmeta_to_cot.py')
cot=importlib.util.module_from_spec(s); s.loader.exec_module(cot)
ev={'event':{'event_type':'STATE_EVENT','ts':'2025-01-17T14:40:00Z'},
    'payload':{'track_id':'t1','geo':{'lat':34.0,'lon':-118.0,'alt_m':10.0}}}
cot.zmeta_to_cot(ev, cot_config={'default_valid_for_ms': float('nan')})
PY
# -> ValueError: cannot convert float NaN to integer  (docstring promises None)

### R1-23 (MINOR) — battery_voltage zero-handling is asymmetric between the two functions the wave edited: translate_platform_state drops 0 V, translate_link_status publishes it as a measurement

**Location:** `adapters/ingress/mavlink/mavlink_to_zmeta_template.py:514`

**Claim:** `translate_platform_state` treats a 0 V battery as not-a-measurement and drops it (`if battery_v is not None and battery_v > 0`, :199). `translate_link_status`, rewritten in the same wave for the same reason, uses bare `is not None` (:514) and publishes 0.0. Because 0.0 was that parameter's OLD default meaning "unknown", any existing caller migrated forward that still passes `battery_voltage=0.0` now emits a flat-battery measurement where it previously emitted the same value as an acknowledged placeholder. `decode_sys_status` feeds exactly that value: `voltage_battery: 0` is not the UINT16_MAX sentinel, so it decodes to `battery_voltage: 0.0` and passes straight into translate_link_status. Same asymmetry on `rc_rssi` (0 dBm emitted). Not a regression — the old code always emitted 0.0 — but the wave unified the sentinel rule across four other sites and left this one split.

**Evidence:**

```
template :199 `if battery_v is not None and battery_v > 0:` vs :514 `if battery_voltage is not None:` (and :518 `if rc_rssi is not None:`, no bound). Probe: translate_link_status(..., battery_voltage=0.0, rc_rssi=0) -> metrics {'battery_voltage': 0.0, 'rc_rssi': 0}; the same 0.0 through translate_platform_state -> quality {'geo_status': 'STALE'} (dropped). decode_sys_status({'voltage_battery':0,'battery_remaining':0}) -> {'battery_voltage': 0.0, 'battery_remaining_pct': 0}. No pin covers battery_voltage=0.0 on either function.
```

**Reproduction:** cd <repo> && python -c "import sys; sys.path.insert(0,'.')
from adapters.ingress.mavlink.mavlink_to_zmeta_template import *
print(translate_link_status(platform_id='u1', latency_ms=1.0, packet_loss_pct=0.0, throughput_bps=1, battery_voltage=0.0, rc_rssi=0, ts='2025-01-17T15:20:00Z')['payload']['metrics'])
st={'lat':34.0,'lon':-118.0,'alt_m':100.0,'battery_voltage':0.0,'based_on':['019c2b5c-c053-70e1-b6aa-340000000001'],'loop_status':'CHECKED_NOT_REFLECTION'}
print(translate_platform_state(st, platform_id='u1', ts='2025-01-17T15:20:00Z')['payload']['quality'])
print(decode_sys_status({'voltage_battery':0,'battery_remaining':0}))"
-> link:  {..., 'battery_voltage': 0.0, 'rc_rssi': 0}
-> state: {'geo_status': 'STALE'}          (same 0.0 dropped)
-> decode: {'battery_voltage': 0.0, 'battery_remaining_pct': 0}

### R1-24 (MINOR) — _warn_stderr violates its own documented contract when sys.stderr is None: it returns True and injects the warning into stdout, the machine-readable metrics channel

**Location:** `gateway/src/gateway.py:236`

**Claim:** `_warn_stderr` (gateway.py:225-239) documents 'If stderr itself is gone it returns False rather than raising'. When `sys.stderr is None` - pythonw.exe, a windowed/frozen build, or a detached Windows service, all plausible for an at-the-sensor Windows edge deployment - `print(message, file=None)` falls back to `sys.stdout` per CPython semantics. The function therefore (a) returns True, falsely reporting delivery, and (b) writes a free-text `WARNING: ...` line into stdout, which is the gateway's structured `metrics ...` summary channel that operators and log shippers parse. Combined with finding 1 this is the worst variant: the latch burns on a 'successful' send that went to the wrong stream. Every degradation handler added by this fix routes through `_warn_stderr`, so all three sinks inherit it, as does `_send_datagram`'s no-metrics fallback at gateway.py:629. `sys.stderr is None` is not covered by any test - the pins use `_BrokenStream`, whose `write` raises, which is a different branch.

**Evidence:**

```
>>> print('warning-line', file=None)   # captured on a redirected stdout
    captured on stdout when file=None: 'warning-line\n'
    === _warn_stderr with sys.stderr = None ===
      _warn_stderr returned: True  (docstring: 'if stderr itself is gone it returns False')
      where the warning actually went (stdout, the machine-readable metrics channel):
        'WARNING: metrics log sink unavailable (...)\n'
```

**Reproduction:** python - <<'EOF'
import importlib.util, io, sys, contextlib
from pathlib import Path
sp=importlib.util.spec_from_file_location('gw', Path.cwd()/'gateway'/'src'/'gateway.py')
gw=importlib.util.module_from_spec(sp); sp.loader.exec_module(gw)
buf=io.StringIO(); real=sys.stderr; sys.stderr=None
try:
    with contextlib.redirect_stdout(buf):
        rv=gw._warn_stderr('WARNING: metrics log sink unavailable (...)')
finally:
    sys.stderr=real
print('returned:', rv, '| landed on stdout:', repr(buf.getvalue()))
EOF

### R1-25 (MINOR) — The AST pin inspects only _verified_compact_bytes, so a recursive pre-scan added to the public dumps()/verify_representable() entry points — A-04's exact topology one frame up — is invisible to it

**Location:** `gateway/tests/test_compact_fail_closed.py:596`

**Claim:** The `unguarded` set (line 596-603) is built only from calls appearing lexically inside `funcs["_verified_compact_bytes"]`. The public egress API is `dumps()` (zmeta_compact.py:590) and `verify_representable()` (zmeta_compact.py:578); the fail-closed guarantee the test names is a property of those, not of the private helper. A-04 was "a recursive pre-scan sits in front of the try that converts its exception" — the same defect placed one frame up, in `dumps()`, is outside the pin's window entirely. The author's self-attack asserts the opposite ("Recursion introduced in a new helper called from OUTSIDE the try in _verified_compact_bytes IS caught"), which is true but does not cover the callers of _verified_compact_bytes.

**Evidence:**

```
Ran the pin's algorithm verbatim on a source with a recursive walk inserted into the public entry point:
  MUT-3  dumps() = `_semantic_difference(event, event); return _verified_compact_bytes(event)`
         -> recursive=['_semantic_difference'] exposed=[] -> PIN PASSES
A RecursionError from that call reaches the caller raw; gateway/src/gateway.py:976 catches only `_COMPACT_UNREPRESENTABLE`, so the datagram is dropped as INTERNAL_ERROR with nothing forwarded — byte-for-byte the A-04 outcome the pin exists to prevent.
This is latent, not live: no such call exists at HEAD. Reported because it is a stated-but-unmet property of a guard whose whole value is future-proofing, and because it is cheap to close (root the `unguarded` walk at `dumps` and `verify_representable`, not at `_verified_compact_bytes`).
```

**Reproduction:** Same harness as finding 1; substitute
  mut3 = real.replace(
      'def dumps(event: Dict[str, Any]) -> bytes:\n    return _verified_compact_bytes(event)',
      'def dumps(event: Dict[str, Any]) -> bytes:\n    _semantic_difference(event, event)\n    return _verified_compact_bytes(event)')
and re-run the pin body -> exposed == [] -> PIN PASSES.

### R1-26 (OBSERVATION) — decode_attitude's new omission semantics carry a stale accumulated attitude forward as current, the opposite of decode_global_position_int's clobber-with-None in the same wave

**Location:** `adapters/ingress/mavlink/mavlink_to_zmeta_template.py:344`

**Claim:** The two decoders rewritten in the same wave chose opposite missing-value semantics, and the docstrings justify both. decode_global_position_int returns explicit `None` for an absent alt/vx/vy/vz (:320-323), so in the README's documented `state.update(decode_...)` accumulation pattern a message missing altitude clobbers a good prior value and the event refuses. decode_attitude omits the key instead and its docstring at :344-345 sells that as a feature — "Omitted keys also leave any previously accumulated value in the caller's state dict intact" — which means an ATTITUDE message that drops an axis leaves the previous roll in the state dict and it is emitted into payload.quality.roll_deg as a current reading with no per-field staleness marker. That is stale-carried-forward rather than fabricated, and MAVLink ATTITUDE always populates all three axes in practice, so the branch is unlikely to fire in the field — but it is a deliberate design choice made inside an anti-laundering wave that the wave did not adjudicate against the clobber choice made in the sibling function.

**Evidence:**

```
template :320-323 (alt/vx/vy/vz -> None, clobbering) vs :347-354 (roll/pitch/yaw -> key omitted, non-clobbering); docstring rationale at :342-345. README.md:88 documents the accumulating `state.update(decode_global_position_int(...))` pattern that makes the difference observable. No test covers a second decode call overwriting an accumulated state dict.
```

**Reproduction:** cd <repo> && python -c "import sys; sys.path.insert(0,'.')
from adapters.ingress.mavlink.mavlink_to_zmeta_template import *
state = {}
state.update(decode_attitude({'roll':0.5,'pitch':0.1,'yaw':3.0}))   # t=0, real reading
state.update(decode_attitude({'pitch':0.1,'yaw':3.0}))              # t=10s, roll not reported
print('roll survives as current:', state['roll_deg'])
state2 = {'alt_m': 412.5}
state2.update(decode_global_position_int({'lat':340000000,'lon':-1180000000}))
print('alt clobbered to:', state2['alt_m'])"
-> roll survives as current: 28.6478...
-> alt clobbered to: None

### R1-27 (OBSERVATION) — The rewritten AST scan has a dead arm, and the headline A-02(a) fix (the canonical `claim.sub_class` refusal) is unpinned because it is observationally identical to the backstop

**Location:** `adapters/ingress/sapient/test_sapient_ingress.py:1141`

**Claim:** Two smaller points on the same guard. (1) The regex-to-AST rewrite added an `ast.Assign`/`ast.Subscript` arm for `target[VENDOR_EXTENSION_KEY] = ...`, but all seven vendor-extension sites in the module are dict literals (:643, :763, :961, :1034, :1060, :1174, :1208). That arm matches nothing and has never been exercised, so it is itself unreviewed code doing no work; the scan also remains blind to a site written with the string literal "vendor.sapient" instead of the constant, which the `>= 6` floor would not catch. (2) `test_non_finite_claim_refuses_only_that_inference` (:1797) does not pin the `sub_class` refusal: with the claim-site check removed the poisoned inference is built and then dropped by the emit-boundary backstop, producing a byte-identical event list. The two dispositions are indistinguishable, so no behavioural test can pin that line — worth recording so it is not mistaken for covered.

**Evidence:**

```
REVERT=subclass (a frame-aware stub that returns False only when `_has_non_finite` is called from `_translate_detection`, leaving the backstop and `validate()` intact) -> 94 passed, 0 failed, including `test_non_finite_claim_refuses_only_that_inference`.
grep -n VENDOR_EXTENSION_KEY adapters/ingress/sapient/sapient_to_zmeta.py -> 58 (the constant) + 7 sites, every one of the form `{VENDOR_EXTENSION_KEY: _drop_non_finite(...)}`; zero subscript assignments.
```

**Reproduction:** REVERT=subclass PYTHONPATH="<scratchpad>;." python -m pytest adapters/ingress/sapient/test_sapient_ingress.py -q -p atk_revert   # 94 passed
grep -n "VENDOR_EXTENSION_KEY" adapters/ingress/sapient/sapient_to_zmeta.py   # 8 hits, all dict-literal form

### R1-28 (OBSERVATION) — `producer_authority:` mangled to null/scalar/list turns the entire authority gate off; the two structure lints are silent and the CLI's non-zero exit is an unhandled traceback from older code, not a diagnostic

**Location:** `gateway/src/validators.py:1620`

**Claim:** `lint_producer_authority_structure` has the same silent early-return at the container level (validators.py:1620) as the routing lint does at validators.py:1774, and `validate_producer_authority` returns `(True, [])` for a non-dict `authority_policy` (validators.py:2735). The CLI does exit 1 — but only because the pre-existing `lint_policy_risk_modes` crashes at validators.py:1332 with `AttributeError: 'NoneType' object has no attribute 'get'` and prints a Python traceback with no path, no reason_code and no message. The operator gets a broken tool, not a policy refusal, and the exit code is accidental: if that older function is ever hardened, this becomes a silent green light on a total authorization bypass. The author disclaimed this one as pre-existing and out of scope, which is defensible; I record it because it is the same root-level blind spot as the routing finding and its current 'safe' behaviour is load-bearing on an unrelated crash.

**Evidence:**

```
policy/producer-authority.yaml replaced with `producer_authority:`
  CLI exit=1, stdout='' , stderr=traceback ending
    File "gateway/src/validators.py", line 1332, in lint_policy_risk_modes
      promotion = producer_authority.get("external_state_promotion", {})
    AttributeError: 'NoneType' object has no attribute 'get'
  lint_producer_authority_structure + lint_routing_producer_enforcement_structure -> 0 issues
  validate_producer_authority(totally-unregistered-node, STATE_EVENT) -> (True, [])
  Same for `producer_authority: enabled` (scalar), `producer_authority: [enabled]` (list), and int.
```

**Reproduction:** python "C:\\Users\\User\\AppData\\Local\\Temp\\claude\\C--Users-User-Desktop-General-Requirements-Documents-Future-Ideas-Z-ISR-ZMeta-zmeta-spec\\7f5e13b1-40a9-4010-a3e1-17156d83755b\\scratchpad\\atk_a05_2.py"  (CLI stdout/stderr)
python "...\\scratchpad\\atk_a05_1.py"  (section F2)

### R1-29 (OBSERVATION) — The new loop test patches the stdlib socket.socket process-wide and its replacement raises IndexError on a third socket creation

**Location:** `gateway/tests/test_gateway_runtime_guards.py:524`

**Claim:** `mock.patch.object(gateway.socket, "socket", lambda *a, **k: sockets.pop(0))` mutates the real stdlib module - `gateway.socket is socket` is True, since gateway.py does a plain `import socket`. For the duration of `gateway.main()` every socket creation anywhere in the process returns a `_LoopSocket`, and the third one raises `IndexError: pop from empty list` rather than anything diagnosable. It is safe today (pytest.ini sets only `-p no:cacheprovider`, no xdist, and main() creates exactly two sockets at gateway.py:1904/1906), so this is a latent hazard, not a live failure: adding pytest-xdist, a background thread, or a third socket in main() turns it into an opaque IndexError inside an unrelated test. Patching `gateway.socket` with a namespace object, or making the lambda raise a named AssertionError when exhausted, removes it without touching the pin's coverage.

**Evidence:**

```
>>> gateway.socket is socket
    True
    # pytest.ini: addopts = -p no:cacheprovider   (no -n / no xdist)
    # gateway.py:1904  sock_in  = socket.socket(...)
    # gateway.py:1906  sock_out = socket.socket(...)   -> exactly 2 today
```

**Reproduction:** Load gateway.py by path and evaluate `gateway.socket is socket`; then read test_gateway_runtime_guards.py:520-528 and note `sockets` holds exactly two elements with no exhaustion guard.

### R1-30 (OBSERVATION) — The pin is real but its perimeter is `validate_semantics`; it cannot observe anything upstream of the gate

**Location:** `gateway/tests/test_non_finite_value_scoped.py:234`

**Claim:** I revert-proved the pin three independent ways and it holds for what it covers. What it cannot see: `_process` (:234) and `test_severity_downgrade_cannot_reopen_the_hole` (:311) both call `process_message` without `timing_state`, so `gateway.py:1652-1679` — `validate_timing_quality` and `apply_timing_freshness_degradation`, the two pieces of code that handle event-derived floats *ahead* of the gate — are skipped in all 15 tests. `NonFiniteHelperTest` exercises dict and list only, never a set. The author's stdlib-verdict design (`json.dumps(allow_nan=False)` on a decoded round-trip rather than a repo encoder) is genuinely non-blind and correctly avoids the A-19 trap; the blindness is in the *reachability* perimeter, not the oracle.

**Evidence:**

```
Revert simulations against the working tree, running the pin's own 15 tests:
  BASELINE (fix in place)                     run=15 failures=0  errors=0
  R1: _find_non_finite forced to return None  run=15 failures=42 errors=6   (48 distinct cells)
  R2: severity='fail' override removed        run=15 failures=2   (lat, confidence)
  R3: gate physically moved below the frame
      checks (text-transformed copy of
      validators.py loaded in its place)      run=15 errors=6
      -> test_diagnostic_never_echoes_the_offending_value, all 6 cells
R3 confirms the ordering claim is genuinely pinned: validators.py:2213-2236 `return`s immediately, so a NaN quality.bearing_frame really would ship `"value": NaN` if the gate moved. Full battery on the working tree: `python -m pytest -q` -> 896 passed, 716 subtests passed.
```

**Reproduction:** Load gateway/tests/test_non_finite_value_scoped.py by path, set `module.validators._find_non_finite = lambda v: None` (and the same on the `validators` module `gateway` imported from), run `unittest.defaultTestLoader.loadTestsFromModule` -> 42 failures / 6 errors. Restore -> 0. For R3, copy validators.py, move the block starting `# Contract 8.1 value honesty, first gate.` to just before `# Contract 6.8 zero-fill heuristic`, load the copy and rebind `module.validators` and `module.gateway.validate_semantics` -> 6 errors, all in test_diagnostic_never_echoes_the_offending_value.

---

## Round 2 — attack on the remediation

32 findings, **18 of them introduced by the remediation
itself**. That ratio is the number that should drive the next decision: the
remediation closed 30 residuals and created 18 findings doing it.

Findings marked **INTRODUCED** were created by the round-2 remediation and
did not exist before it. They are the highest-value entries here — each one
is a fix that traded one problem for another, and several are trade-offs a
maintainer should adjudicate rather than defects to be mechanically closed.

The four MAJOR entries are carried in the audit document as B-01..B-04.

### R2-01 (MAJOR) — **INTRODUCED BY REMEDIATION** — The TIME_STATUS carried-verdict guard whitelists two literals, not a vocabulary: 'LOCKED', 'NOMINAL' and even 'UP ' (one trailing space) override an UNSYNCED metrics block — and this pass is what shipped the guarantee that they cannot

**Location:** `adapters/ingress/mavlink/mavlink_to_zmeta_template.py:60`

**Claim:** The pass-through of an arbitrary carried state predates this pass (`msg.get("state") or "SYNCED"`); what this pass introduces is the *guarantee* that it cannot happen, in three places, while closing only two exemplars. `_time_status_payload_state` (:59-62) returns `derived` only when `str(carried_state).upper()` is exactly "UP" or "SYNCED"; every other truthy value is returned verbatim. So the honest-sounding docstring at :53-57 ("A message-carried state is honoured only when it is *more* conservative than the derived verdict ... an optimistic 'UP'/'SYNCED' label never overrides an UNSYNCED metrics block. The event therefore never contradicts itself"), the identical claim now published in adapters/ingress/mavlink/README.md:163-165, and the pin named test_mavlink_time_status_never_launders_a_carried_degraded_verdict all assert an invariant the code does not enforce. The comparison is a two-element literal tuple, not an ordering and not a vocabulary — there is no notion of 'more conservative' anywhere in the function. 'LOCKED' is not a hypothetical label: it is this module's own sync vocabulary (_normalize_sync_state, :34-41), exactly what a bridge author reusing the module's terms would put in `state`. 'UP ' with a trailing space is the targeted exemplar itself escaping on a whitespace character, and renders as 'UP' in every UI. Contrast the sibling emitter fixed in this same pass: translate_link_status (:596-601) *does* validate `state` against a declared vocabulary (_LINK_STATUS_STATES, :27) and refuses out-of-vocabulary values. The same treatment was available here and was not applied — and it is available without a governed change, because the v1.0 schema leaves TIME_STATUS payload.state unconstrained (schema/zmeta-event-1.0.schema.json $defs/SystemPayload: only the TASK_ACK and LINK_STATUS branches enum-constrain `state`), so nothing downstream catches the contradiction either. No test in the file covers any carried value outside {UP, SYNCED, DOWN}; the file is 50/50 green with the defect live.

**Evidence:**

```
Direct helper, sync_state='UNSYNCED' (derived verdict = 'DEGRADED'):
  carried='UP'      -> 'DEGRADED'   (exemplar closed)
  carried='SYNCED'  -> 'DEGRADED'   (exemplar closed)
  carried='UP '     -> 'UP '        <-- escapes on one space
  carried=' UP'     -> ' UP'
  carried='LOCKED'  -> 'LOCKED'
  carried='NOMINAL' -> 'NOMINAL'
  carried='OK'/'GOOD'/'HEALTHY'/'TRUE' -> verbatim
End to end through mavlink_decoded_to_zmeta_system_events (msg carries no sync_state, so metrics.sync_state='UNSYNCED'), shipped schema + shipped policy:
  carried='UP '     -> payload.state='UP '     sync_state='UNSYNCED' | SCHEMA-OK | validate_semantics (True, [])
  carried='LOCKED'  -> payload.state='LOCKED'  sync_state='UNSYNCED' | SCHEMA-OK | (True, [])
  carried='NOMINAL' -> payload.state='NOMINAL' sync_state='UNSYNCED' | SCHEMA-OK | (True, [])
  carried='GOOD'    -> payload.state='GOOD'    sync_state='UNSYNCED' | SCHEMA-OK | (True, [])
  carried='Synced'  -> payload.state='DEGRADED'                       (case-folded exemplar, closed)
pytest adapters/ingress/mavlink/test_mavlink_ingress.py -q -> 50 passed, with every line above live.
```

### R2-02 (MAJOR) — **INTRODUCED BY REMEDIATION** — The (c) degradation DISCARDS the resolvable cross-mode latency the store still holds, so adding a broken mode NARROWS the node's published est_error_ms — the exact laundering (c) exists to close, at a different point

**Location:** `adapters/ingress/sapient/sapient_to_zmeta.py:388`

**Claim:** `_timing`'s new degraded branch (:363-388) `return timing` BEFORE the widen at :389-400, so it throws away `registration.max_latency_ms(node_id, mode=active_mode)` even when that call still returns a real, resolvable bound. `latency_unresolved` is deliberately true whenever ANY mode's declaration is broken and the active mode is not a named-and-resolvable one (registration_state.py:349-355) — but `max_latency_ms` under exactly the same scoping still returns the cross-mode maximum over the modes that DID resolve (registration_state.py:320-325). The degraded branch substitutes `max(caller, 60000)` for `caller + that resolvable bound`. Whenever `caller + resolvable_max > max(caller, 60000)` the result is NARROWER than the un-degraded computation on the same store, with no compensating label change. On the module's own default path — no caller `timing_quality`, so `coerce_timing_quality` seats est_error_ms at DEFAULT_UNSYNCED_ERROR_MS = 60000 and the labels are ALREADY UNKNOWN/UNSYNCED — the condition holds for ANY resolvable latency > 0 ms. This falsifies the invariant the remediation states in three places: README ('a broken declaration must never yield a tighter est_error_ms than a sane one'), the docstring at :351-359, and the pin's own header at test_sapient_ingress.py:2067-2074. It is also a strict regression against the pre-remediation tree: HEAD's `_timing` (git show HEAD:adapters/ingress/sapient/sapient_to_zmeta.py, the widen-only body) produces the wider number for the identical input. CLASS, not exemplar: it fires for every unresolvable reason (NaN, unknown units, huge int) and every multi-mode node, because the deleted term is the widen itself, not any particular declaration.

**Evidence:**

```
End-to-end through the public API, no caller timing_quality, node type CAMERA, detection unchanged. Node A declares one mode 'scan' maximum_latency 0.5 s. Node B declares the SAME 'scan' 0.5 s PLUS a second mode 'sweep' whose maximum_latency is unresolvable. No active_mode named.
  store.max_latency_ms(node) on B  = 500.0 ms   (still resolvable, still held)
  A (scan only)   -> {"time_source":"UNKNOWN","sync_state":"UNSYNCED","est_error_ms":60500.0}
  B (scan+broken) -> {"time_source":"UNKNOWN","sync_state":"UNSYNCED","est_error_ms":60000.0}
  NARROWER: True.  sync_state identical in both -> zero compensating loudness.
Same result with the second mode broken by unknown units (TIME_UNITS_FORTNIGHTS) and by a 10**400 value: 60000.0 in all three. So it is the branch, not the exemplar.
Regression vs the pre-remediation tree, identical two-mode input, `_timing` body taken verbatim from `git show HEAD`:
  caller none (default 60000): BEFORE 60500.0 UNKNOWN/UNSYNCED -> AFTER 60000.0 UNKNOWN/UNSYNCED   NARROWED
  caller LOCKED 59900 ms     : BEFORE 60400.0 GPS_PPS/LOCKED  -> AFTER 60000.0 UNKNOWN/UNSYNCED   NARROWED
  caller LOCKED 5 ms         : BEFORE 505.0                   -> AFTER 60000.0                    widened (fine)
Why no pin sees it: `test_unresolvable_declared_latency_never_narrows_est_error_ms` (:2093) compares the broken event against a DIFFERENT registration (single sane mode, 0.5 s -> 505.0) and against the caller's own bound (:2095). It never compares against the same store's own surviving resolvable bound, and its magnitudes (505.0, 5.0) sit below 60000 so the inequality is satisfied by the sentinel alone. `test_a_resolvable_active_mode_is_not_degraded_by_another_broken_mode` (:2120) builds the two-mode store and asserts `latency_unresolved(NODE) is True` at :2134 — the exact narrowing case — then only translates with active_mode='scan' (:2136-2141), so the mode=None disposition is asserted at the store and never at the event. Full SAPIENT file: 118 passed with this defect live.
In-class fix, no governed artifact touched: in the degraded branch fold the surviving bound in rather than dropping it, e.g. `bound = max(caller, DEFAULT_UNSYNCED_ERROR_MS); latency = registration.max_latency_ms(node_id, mode=active_mode); if latency is not None: bound = max(bound, caller + latency)`. Labels stay UNKNOWN/UNSYNCED. Pin it with the two-node comparison above (A=60500 vs B must be >= 60500), which is what the current monotonicity pin cannot express.
```

### R2-03 (MAJOR) — **INTRODUCED BY REMEDIATION** — The remediation traded a loud lint failure for a silent pass on a mangled `timing_freshness` block — the timing-freshness gate is now fully disabled at runtime with zero signal anywhere

**Location:** `gateway/src/validators.py:1546`

**Claim:** `lint_policy_risk_modes` now reads every block through the new `_mapping_or_empty` (validators.py:1532, applied at :1546, :1619, :1630, :1668, :1669). For `producer_authority` this is safe — `lint_producer_authority_structure` reports the destroyed block. For `timing_freshness` there is NO structure lint, so the coercion silently substitutes a clean `{}` for a destroyed block and the lint says nothing. Before the remediation the same input aborted the shipped CLI with an AttributeError traceback (exit 1); the operator saw *something*. After it the CLI prints `policy risk mode lint ok` and exits 0. Meanwhile `_timing_freshness_enabled` (validators.py:582) returns False for a non-mapping block, so `validate_timing_quality` returns `True, []` at :2543 and the entire stale/negative-age/holdover gate is off. The result is a fail-open authorization-adjacent control with no diagnostic at deployment time and none at runtime — the exact 'quieter defect' trade the previous two waves were faulted for, applied to a different block. The lint is the operator-facing pre-deployment check documented in README.md:312, spec/installation-guide.md:70, configs/README.md:44, conformance/README.md:72 and docs/zmeta_change_governance.md:326, so the silence lands on the documented workflow. `lineage` (:1630) is the same shape but was already silent pre-remediation, so it is pre-existing, not introduced. The in-class fix is either to emit a structural diagnostic for the coerced block or to coerce only where a structure lint speaks.

**Evidence:**

```
PRE (scratchpad copy of validators.py as of the adversarial pass, 06:35) vs CURRENT, same shipped policy with one block replaced:
  timing_freshness = None       PRE: RAISED AttributeError   CUR: issues=0 SILENT-PASS
  timing_freshness = 'garbage'  PRE: RAISED AttributeError   CUR: issues=0 SILENT-PASS
  timing_freshness = ['x']      PRE: RAISED AttributeError   CUR: issues=0 SILENT-PASS
  timing_freshness = 5          PRE: RAISED AttributeError   CUR: issues=0 SILENT-PASS
  producer_authority = None     PRE: RAISED AttributeError   CUR: issues=1 ['producer_authority']   (correct)
Shipped CLI on scratch copies of policy/ (repo untouched):
  policy/timing-freshness.yaml truncated to `timing_freshness:`  -> exit=0  stdout='policy risk mode lint ok'
  policy/timing-freshness.yaml -> `timing_freshness: garbage`    -> exit=0  stdout='policy risk mode lint ok'
  control, policy/routing.yaml truncated to `routing:`           -> exit=1  FAIL path=routing (the remediation's own case, working)
Runtime, shipped semantics + a TIME_STATUS one hour older than the event (node-level timing path, per-event timing removed):
  shipped timing_freshness            -> ok=False codes=['TIMING_STATUS_STALE'] severity=['fail']
  timing_freshness = None             -> ok=True  codes=[]
  timing_freshness = 'garbage'        -> ok=True  codes=[]
End-to-end through gateway.process_message on a shipped v1.1 STATE_EVENT with policy/timing-freshness.yaml truncated to `timing_freshness:`: 2 events emitted, the STATE_EVENT forwarded, no policy_error anywhere.
```

### R2-04 (MAJOR) — The mapping-limit scan still descends only dict/list, so a set-carried oversized integer leaves compact egress as a CBOR bignum and two conforming consumers decode it differently

**Location:** `zmeta_compact.py:525`

**Claim:** The remediation rewrote _find_unencodable_int twice and left its container dispatch at `if not isinstance(current, (dict, list)): continue` (zmeta_compact.py:525). Its sibling walk in the SAME uncommitted change set was widened to Mapping/AbstractSet/Sequence/CBORTag precisely because cbor2 -- the backend gateway._decode_cbor:1017-1021 explicitly falls back to -- decodes CBOR tag 258 into a `set`, a map key into a frozendict, and an unknown tag into a CBORTag (gateway/src/validators.py:343-384). Anything inside those three shapes is invisible to the compact scan. The round-trip guard cannot catch it either, because cbor2 encodes and decodes the bignum self-consistently, so _semantic_difference sees no difference. The result is the exact sentence the fix's own comment asserts is false at zmeta_compact.py:501 ("Representability must not depend on which CBOR library is installed"): with zmeta_cbor installed the event is REFUSED, with cbor2 only it is ENCODED CLEAN -- and the emitted packet is then decoded to two different values by two conforming consumers, silently, with no diagnostic. This is a distinct instance from the separately-assigned depth ~61-398 backend-parity residual (that one is nesting depth; this one is container type, and this one silently ALTERS a value rather than failing to decode).

**Evidence:**

```
573-byte CBOR datagram, vendor blob = {"s": {2**70}} (tag 258 carrying a bignum), cbor2-only install, strict_validation=True, profile L (matched):
  gateway.process_message      -> 1 event, vendor = {'s': {1180591620717411303424}}
  compact egress               -> 303 bytes, reason_code = None   (NO diagnostic, NO refusal)
  packet carries CBOR tag 258  -> True
  packet carries CBOR tag 2 (bignum) -> True
The same 303-byte packet, read by the two supported consumers:
  zmeta_compact.loads (cbor2)      -> vendor = {'s': {1180591620717411303424}}      (int, in a set)
  zmeta_compact.loads (zmeta_cbor) -> vendor = {'s': [b'@\x00\x00\x00\x00\x00\x00\x00\x00']}   (LIST of raw BYTES)
One conforming consumer sees an integer, the other sees a byte blob, neither errors. Direct through the public API (no gateway) is identical: zmeta_compact.dumps -> 303 bytes.
Backend-dependence of the refusal, same input:
  zmeta_cbor installed: CompactUnrepresentableError (TypeError: unsupported type for CBOR encoding: set)
  cbor2 only:           ENCODED 303B
The same gap makes the remediation's NEW cycle refusal incomplete. `_find_unencodable_int` returns None for a cycle mediated by a tuple, so it falls to the backend and produces exactly the two-reasons-for-one-event the docstring says it prevents:
  zmeta_cbor: "compact cannot serialize this event (RecursionError: maximum recursion depth exceeded)"
  cbor2 only: "compact cannot serialize this event (CBOREncodeValueError: cyclic data structure detected)"
```

### R2-05 (MODERATE) — CoT: the "raw exception instead of the documented None" class is closed for floats only — a schema-valid huge integer literal in payload.valid_for_ms still raises OverflowError out of the adapter on an event the kernel FORWARDS

**Location:** `adapters/egress/cot/zmeta_to_cot.py:241`

**Claim:** The remediation's own comment at zmeta_to_cot.py:196-200 names "cot_config.default_valid_for_ms, which escaped as a raw ValueError / OverflowError rather than the documented None" as one of the three things the value-scoped rewrite closes, and the README hunk repeats it. Only the float/NaN half is closed. `_is_non_finite` (:79-87) deliberately never converts a Python int (correct — math.isfinite() on a huge int raises), and nothing else covers the int arm, so `timedelta(milliseconds=valid_for_ms)` at :241 still raises OverflowError straight out of a function whose documented failure signal is None. This is not introduced by the remediation, but the class the remediation declares closed is not closed, and the new pin `test_zmeta_to_cot_guard_does_not_convert_huge_ints` (test_zmeta_to_cot.py:664) gives false assurance for it: it probes 10**400 through `payload.source_summary`, which is stringified into <remarks> and never arithmetic, so it asserts `is not None` on the one path where a huge int is harmless.

**Evidence:**

```
Live end-to-end through the shipped kernel then the shipped adapter, Profile-L TRACK_STATE, strict_validation=True. schema/zmeta-event-1.0.schema.json declares TrackStatePayload.valid_for_ms as {"type":"integer","minimum":1} with NO maximum, so the value is a legal JSON integer literal and schema-valid:
  control clean                    kernel -> [('STATE_EVENT', None)]   cot -> XML ok
  valid_for_ms = 10**400           kernel -> [('STATE_EVENT', None)]   cot -> RAISED OverflowError: Python int too large to convert to C int
  error_ellipse semi_major=10**400 kernel -> [('SYSTEM_EVENT','SCHEMA_INVALID')]  (kernel catches this one)
  source_summary=[10**400]         kernel -> [('SYSTEM_EVENT','SCHEMA_INVALID')]  (kernel catches this one)
Direct-caller sweep (adapter only), same base event:
  payload.valid_for_ms = 10**400            -> RAISED OverflowError
  cot_config.default_valid_for_ms = 10**400 -> RAISED OverflowError
  cot_config.default_valid_for_ms = nan     -> None (refused)   <- the half that IS closed
  payload.heading_deg = 10**400             -> RAISED OverflowError (schema bounds this one to 0..360)
  error_ellipse_m.semi_major = 10**400      -> RAISED OverflowError
  zmeta_to_cot_uncertainty_circle(radius_m=10**400) -> RAISED OverflowError (float() at :389; the except clause catches only TypeError/ValueError, and OverflowError is an ArithmeticError)
Consequence in the gateway: gateway.py forwards the canonical event first (:2329) and calls zmeta_to_cot(outgoing) after (:2341), so the OverflowError escapes to the per-datagram `except Exception` backstop at :2372 — the operator gets a generic backstop drop and any remaining outgoing events in that datagram's loop are abandoned, instead of the counted, reason-tagged `cot_skipped` record the guard's comment (:191-192) promises.
```

### R2-06 (MODERATE) — **INTRODUCED BY REMEDIATION** — The CoT Decimal non-finite branch is load-bearing but completely unpinned: deleting it leaves 33/33 CoT tests green while putting <point lat="NaN"> on the TAK wire

**Location:** `adapters/egress/cot/zmeta_to_cot.py:85`

**Claim:** Fix (d) added a Decimal arm to `_is_non_finite` (zmeta_to_cot.py:85-86) and the author's summary lists Decimal coverage as part of the change. The CoT test file contains zero occurrences of `Decimal` — grep -c Decimal adapters/egress/cot/test_zmeta_to_cot.py == 0 — so that branch is invisible to the suite. It is not a redundant branch: it is the only thing stopping a cbor2 tag-5 Decimal('NaN') from rendering as a CoT attribute. This is the shape the brief names: a test the author did not watch fail is not a pin, and here there is no test at all. The kernel twin IS pinned (`test_decimal_nan_is_a_non_finite_leaf`, which I confirmed fails 4x on revert); only the CoT copy ships unpinned, and the author's "what my pins cannot see" section does not name it.

**Evidence:**

```
Revert-simulation in a scratch mirror (repo untouched, source restored and byte-compared afterwards). Removing exactly the two Decimal lines from adapters/egress/cot/zmeta_to_cot.py:85-86:
  c_decimal_leaf   rc=0   33 passed in 0.05s      <- ZERO pins fail
Contrast, same harness, other arms of the same fix:
  c_whole_guard          rc=1  8 failed
  c_container_walk       rc=1  1 failed
  c_extensions_exclusion rc=1  1 failed
  c_circle_radius        rc=1  1 failed
  c_non_payload_walk     rc=1  1 failed
  c_seen_set             rc=99 HUNG (45s)
What the unpinned branch is holding back — same event, HEAD vs the reverted branch:
  HEAD:      payload.heading_deg=Decimal('NaN') -> None (refused)
             payload.geo.lat   =Decimal('NaN')  -> None (refused)
             confidence        =Decimal('Infinity') -> None (refused)
  REVERTED:  payload.heading_deg -> XML: <track course="NaN" speed="0.0" />
             payload.geo.lat     -> XML: <point lat="NaN" lon="2.0" hae="10.0" le="9999999.0" ce="9999999.0" />
             confidence          -> XML: <remarks>confidence=Infinity</remarks>
That is precisely the A-01(d) defect — an ordinary ATAK marker at a position that is not a position — reachable again by a one-line edit no test would object to.
```

### R2-07 (MODERATE) — The termination class was closed in three walkers and left open in four more of the identical idiom, all in this same uncommitted change set

**Location:** `adapters/egress/jreap/zmeta_state_to_jreap_track_json.py:5`

**Claim:** The remediation states "Termination, in all three walkers of the class." Enumerated independently from the code, the class -- explicit-stack walks over sender-controlled event structure with no visited set -- has at least seven members in this tree. Three were fixed here (zmeta_compact._find_unencodable_int, validators._find_forbidden_key, validators._find_non_finite) and one more, adapters/egress/cot/zmeta_to_cot.py:90, already carries the seen-set with the same justification written out, so the pattern was known and applied selectively. Four still spin forever: adapters/egress/jreap/zmeta_state_to_jreap_track_json.py:5, adapters/egress/klv/zmeta_to_klv_tagdict_template.py:4, adapters/egress/mavlink/zmeta_command_to_mission_intent.py:34, adapters/ingress/sapient/sapient_to_zmeta.py:221. All four carry the same comment the residual was written against -- "Iterative so sender-controlled nesting is a memory cost, never a RecursionError" -- which is the exact crash-for-hang trade, and the MAVLink one documents its own reachability ("geometry is copied verbatim from the payload, so a vertex deep inside it is reachable"). The three egress adapters receive a ZMeta event that on a cbor2-only install can come off the wire cyclic or share-amplified; the SAPIENT one is JSON-fed so cycles are not wire-reachable there, but the walk is still unbounded on shared structure a caller can build. These files were all touched by this same change set, so they go to the maintainer together.

**Evidence:**

```
Each walker called directly with a 5s watchdog. Cyclic dict `d = {}; d['self'] = d`:
  cot     _has_non_finite(cycle)   -> False in 0.000s        (has the seen-set)
  jreap   _has_non_finite(cycle)   -> DID NOT TERMINATE in 5s
  klv     _has_non_finite(cycle)   -> DID NOT TERMINATE in 5s
  mavlink _has_non_finite(cycle)   -> DID NOT TERMINATE in 5s
  sapient _has_non_finite(cycle)   -> DID NOT TERMINATE in 5s
Shared acyclic DAG, 2**30 distinct paths (the structure a ~900-byte cbor2 value-sharing datagram decodes into):
  cot     -> False in 0.000s
  jreap   -> DID NOT TERMINATE in 5s
  klv     -> DID NOT TERMINATE in 5s
  mavlink -> DID NOT TERMINATE in 5s
  sapient -> DID NOT TERMINATE in 5s
```

### R2-08 (MODERATE) — **INTRODUCED BY REMEDIATION** — The new str() coercion in _time_status_payload_state converts three previously schema-REFUSED non-string verdicts into schema-valid payload.state — a more permissive error path introduced by the fix

**Location:** `adapters/ingress/mavlink/mavlink_to_zmeta_template.py:61`

**Claim:** `return str(carried_state)` (:61) is new in this pass. The pre-fix line was `state = msg.get("state") or "SYNCED"`, which passed a non-string carried verdict through unchanged, so the emitted event failed `payload.state: {type: string}` and was refused loudly at the gateway as SCHEMA_INVALID. After the fix the same input is stringified and validates. The result is that a bridge putting a raw MAVLink numeric code, or a boolean, in `state` now produces a clean, schema-valid, semantics-clean TIME_STATUS whose payload.state reads '1' / 'True' / '3.5' over an UNSYNCED metrics block — an event a consumer cannot interpret and the gateway will not refuse. This is exactly the 'closed a defect by introducing a quieter one' pattern: the loud refusal was the correct disposition for an uninterpretable verdict, and the coercion silences it. The coercion buys nothing the fix needed: every intended carried verdict is already a string.

**Evidence:**

```
Live probe, shipped schema, msg={'msg_type':'SYSTEM_TIME','state':<carried>,'est_error_ms':1.0,'last_sync_ts':'2025-01-17T15:19:00Z'} (no sync_state -> metrics.sync_state='UNSYNCED'):
  carried=1     -> NEW payload.state='1'    SCHEMA-OK | OLD (pre-fix passthrough) 1    SCHEMA-FAIL: 1 is not of type 'string'
  carried=True  -> NEW payload.state='True' SCHEMA-OK | OLD True  SCHEMA-FAIL: True is not of type 'string'
  carried=3.5   -> NEW payload.state='3.5'  SCHEMA-OK | OLD 3.5   SCHEMA-FAIL: 3.5 is not of type 'string'
validate_semantics returns (True, []) on all three of the NEW events.
```

### R2-09 (MODERATE) — The UINT8_MAX 'invalid/unknown' sentinel family was declared enumerated and closed, but rc_rssi = 255 is still emitted as a measurement — by translate_link_status, the function edited in this same pass

**Location:** `adapters/ingress/mavlink/mavlink_to_zmeta_template.py:613`

**Claim:** The pass states the family as 'the four sentinels this module touches' (hdg 65535, voltage_battery 65535, battery_remaining -1, satellites_visible 255) and closes the fourth. Enumerated independently from MAVLink common.xml rather than from the code, the family has more members with the identical uint8 'Values: [0-254], UINT8_MAX: invalid/unknown' documentation, and two of them are emitted here unguarded: (1) `rc_rssi` in translate_link_status (:613-614) — the RC_CHANNELS/RC_CHANNELS_RAW rssi field, whose 255 means invalid/unknown — is emitted whenever it `is not None`, with no sentinel test, in the very function this pass rewrote and in the very block where `battery_pct >= 0` (:611) *does* drop its sentinel; and (2) the catch-all LINK_STATUS branch (:524-525) copies `msg['rssi']` verbatim, the RADIO_STATUS rssi field with the same UINT8_MAX convention. The author's own argument for the satellites fix applies verbatim: 255 on a 0-254 scale reads downstream as the strongest signal ever observed, i.e. the sentinel becomes the best possible measurement. The remediation's two-sided reasoning ('a state dict can be assembled by any bridge') applies too — rc_rssi is a caller kwarg with no decoder in front of it, so this is the *only* side. Neither value is covered by any test: the file's only rc_rssi assertions are absence and -70 (test_mavlink_ingress.py:834, :847-854), and the provenance sweep cannot see it because a carried 255 traces to an input by construction. Closing this needs no governed change — a module-level guard mirroring the satellites_visible one at :226.

**Evidence:**

```
Live probe, shipped schema + policy:
  translate_link_status(platform_id='uav-1', latency_ms=1.0, packet_loss_pct=0.0, throughput_bps=1000, rc_rssi=255)
    -> metrics {'link_id':'edge-comms-uav-1','active_link':'unknown','latency_ms':1.0,'packet_loss_pct':0.0,'throughput_bps':1000,'rc_rssi':255}
    -> SCHEMA-OK | validate_semantics (True, [])
  mavlink_decoded_to_zmeta_system_events({'msg_type':'RADIO_STATUS','rssi':255}, ...)
    -> payload {'system_type':'LINK_STATUS','state':'UNKNOWN','metrics':{'rssi':255}}
    (this one is refused on the separately-recorded shape defect, 'link_id' is a required property, so the sentinel is masked rather than caught)
Compare the guarded sibling three lines up, same call: battery_pct=-1 -> 'battery_remaining_pct' absent.
grep of the test file: the only rc_rssi cases are `assert "rc_rssi" not in metrics` (:834) and `rc_rssi=-70` (:847).
```

*(Editor note 2026-07-27: the "separately-recorded shape defect"
parenthetical in the evidence above pointed at a record that never existed —
cold re-read CR-05, claim 3. The shape defect itself is now fixed: the
decoded LINK_STATUS branch refuses-or-emits-valid, commit `ede9bb6`.)*

### R2-10 (MODERATE) — **INTRODUCED BY REMEDIATION** — The new TASK_ACK refusal uses truthiness as a presence test, so it discards a carried ack code of 0 — MAV_MISSION_ACCEPTED / MAV_RESULT_ACCEPTED — and reports a cause that is false

**Location:** `adapters/ingress/mavlink/mavlink_to_zmeta_template.py:489`

**Claim:** `state = msg.get("state") or msg.get("mission_state") or msg.get("ack")` (:474) collapses every falsy carried value to None, and the new guard `if not state: raise ValueError("TASK_ACK requires a message-carried ack state; an acknowledgement verdict is never fabricated")` (:489-493) then refuses. In MAVLink both acceptance codes are the integer 0 (MAV_MISSION_ACCEPTED = 0 in MISSION_ACK.type, MAV_RESULT_ACCEPTED = 0 in COMMAND_ACK.result), so a bridge forwarding the raw code — the natural reading of the `ack` carrier key — loses precisely the *successful* acknowledgements, while REJECTED/FAILED (non-zero) keep emitting. The branch is entered (`"ack" in msg` at :473), so this is not a fall-through to another handler; the acknowledgement is destroyed. Two separate problems: the message the operator gets is factually wrong (the message *did* carry a verdict), and the refusal is disproportionate in exactly the direction the honesty doctrine warns about — good data discarded. It is introduced here: pre-fix the same input emitted (as 'RECEIVED'). The pin encodes the wrong equivalence, declaring `ack: ""` to be 'the same non-answer, not a RECEIVED' (test_mavlink_ingress.py, task_ack pin) — true for the empty string, false for 0. The in-class fix is a presence test (`if not any(k in msg for k in ("state","mission_state","ack"))`) plus a distinct refusal for a carrier that is present but unmappable; no vocabulary change is needed.

**Evidence:**

```
Live probe, mavlink_decoded_to_zmeta_system_events(msg, platform_id='uav-1', producer='mavlink', ts=...):
  {'msg_type':'MISSION_ACK','task_id':'t1','original_event_id':'019c3ef3-...','ack': 0}
    -> RAISED ValueError: TASK_ACK requires a message-carried ack state; an acknowledgement verdict is never fabricated
  {'... ,'mission_state': 0}
    -> RAISED ValueError: (same)
  {'... ,'ack': 'ACCEPTED'}  -> state='ACCEPTED' | SCHEMA-OK | (True, [])
  {'... ,'ack': 1}           -> state=1          | SCHEMA-FAIL: 1 is not of type 'string'
So the falsy integer is the one carried verdict that is destroyed rather than emitted or refused for a stated reason; 1 (MAV_MISSION_ERROR) survives to a loud gateway refusal.
Pre-fix behaviour on the same input: `state = ... or "RECEIVED"` -> emitted.
```

### R2-11 (MODERATE) — **INTRODUCED BY REMEDIATION** — (d)'s huge-int refusal in `_range_bearing_map` DELETES the datum: no canonical field, no vendor provenance, no not-fully-carried marker — contradicting the comment (d) added one function above

**Location:** `adapters/ingress/sapient/sapient_to_zmeta.py:496`

**Claim:** `_is_number` now returns False for a Python int with no float64 form (:120-135), and its new comment at :131-134 states the disposition: 'it refuses here and stays verbatim in the vendor provenance block like every other unmappable value'. The README refusal matrix repeats it ('the raw block is preserved as provenance'). `_range_bearing_map` does not implement that. Its three operand gates — `if _is_number(rng)` (:496), `if _is_number(azimuth)` (:506), `if _is_number(elevation)` (:517) — take the FALSE branch silently: none of them sets `fully_carried = False`, so :793 never writes `vendor_ext['range_bearing']` and the declared value disappears from the event entirely. The float twin of the same value takes the `_finite`-is-None branch, which DOES set `fully_carried = False`, and is preserved. Before (d) these inputs raised OverflowError inside `_is_number`, so no event was produced at all; the silent-deletion behaviour for numeric-looking wire values is what (d) newly created. (The missing marker on the not-a-number branch is pre-existing for e.g. a string range — (d) routed a numeric wire shape into it while asserting the opposite disposition.)

**Evidence:**

```
CAMERA registration, TRUE-datum DEGREES_M range_bearing {range:100.0, azimuth:10.0, elevation:5.0}, one leaf replaced by 10**400 at a time. All four events emitted, validate() == pass in every row:
  leaf poisoned          features            bearing                    range_bearing kept as provenance
  range = 10**400        {}                  {az_deg:10.0, el_deg:5.0}  False   <- range vanished
  azimuth = 10**400      {range_m: 100.0}    null                       False   <- azimuth vanished
  elevation = 10**400    {range_m: 100.0}    {az_deg: 10.0}             False   <- elevation vanished
  range = 1e308 (float)  {}                  {az_deg:10.0, el_deg:5.0}  True    <- preserved, as documented
Full-message sweep (every numeric leaf, 10**400 and 1e308, CAMERA+signal-units registration) confirms the class is exactly these three gates: location.x/y/z, detection_confidence, signal.amplitude, signal.centre_frequency, classification/behaviour confidences, sub_class.level and enu_velocity.east_rate/north_rate all PRESERVE the raw value in the vendor block; only range_bearing.range/azimuth/elevation are GONE.
Why the (d) pin cannot see it: `test_an_integer_with_no_float64_form_refuses_instead_of_crashing` (:2191) sweeps `_leaf_paths(_detection_msg())`, and `_detection_msg()` (:146-171) carries no `range_bearing` key at all — the three gates are never reached by any of its 8 rows. The pin also asserts only no-crash plus `_assert_clean`, never provenance preservation, so it would pass even if range_bearing were in the fixture.
In-class fix, no governed artifact touched: set `fully_carried = False` on the else side of each of the three `_is_number` gates in `_range_bearing_map`, which makes :793 preserve the raw block exactly as the float-overflow twin already does. Pin with the four-row table above (huge-int and float twin must have the same provenance disposition).
```

### R2-12 (MODERATE) — An unresolvable band edge writes the declared 'not measured' bandwidth sentinel AND deletes the raw signal block — a cleaner value substituted for data the producer did declare

**Location:** `adapters/ingress/sapient/sapient_to_zmeta.py:597`

**Claim:** When `centre_frequency` resolves but a band edge does not — overflowing product (`_finite(stop_hz - start_hz)` at :596, or `_freq_hz` overflowing at :573) or unresolvable edge units — `features['bandwidth_hz']` is set to BANDWIDTH_SENTINEL_HZ = 0.0, which the module documents as 'not measured'. But because `rf_features` is not None, :779 (`if signals and rf_features is None: vendor_ext['signal'] = signals`) does not preserve the signal block, and no not-fully-carried marker exists on this path. The event therefore asserts 'bandwidth not measured' for a producer that DID declare start_frequency and stop_frequency, and destroys the declaration that would let a consumer see otherwise. This departs from the module's own doctrine one field over ('unresolved units leave the whole signal block extension-only', :551-555) and from the README row that promises 'the raw block is preserved as provenance' for non-finite arithmetic products. Pre-existing at HEAD (HEAD wrote inf into bandwidth_hz and deleted the edges just the same); the A-02 wave changed the value written but not the deletion, and the new disposition table now blesses it.

**Evidence:**

```
Row 2 of the new `_NON_FINITE_CASES` table (test_sapient_ingress.py:1663-1671), run verbatim: signal [{amplitude:-57.0, centre_frequency:433.0, start_frequency:-1e308, stop_frequency:1e308}] with band edges declared in Hz.
  features    : {"center_freq_hz": 433.0, "power_dbm": -57.0, "bandwidth_hz": 0.0, ...}
  vendor keys : ['detection_confidence','native_behaviour','native_classification','object_id','report_id']
  'start_frequency' anywhere in the event : False
  '1e+308'         anywhere in the event : False
The leaf sweep shows the same deletion for signal.start_frequency and signal.stop_frequency at BOTH 10**400 and 1e308 (GONE in all four rows), while signal.centre_frequency is PRESERVED at both — because a refused centre makes `rf_features` None and re-enables :779.
The pin row asserts `len(events) == 4` and `_assert_clean`, so it certifies this disposition as correct rather than catching it.
In-class fix, no governed artifact touched: preserve the signal block (or a `signal_unmapped` sibling) when a requested band edge was present on the wire but did not resolve — the same asymmetry `_range_bearing_map` already expresses with `fully_carried`.
```

### R2-13 (MODERATE) — The CBOR value-sharing amplification is relocated, not closed: an 833-byte datagram now clears ingress in 1.3 ms and produces a 352 MB egress payload

**Location:** `gateway/src/gateway.py:1112`

**Claim:** The remediation claims the seen-set "closes a second door the residual did not name -- CBOR value sharing can make a few hundred wire bytes expand into exponentially many paths; a 2**64-path shared DAG now costs 65 container visits instead of 2**64." That is true of the three walkers and false of the datagram. The shared structure is not collapsed, only walked once; process_message forwards the event with sharing intact, and the very next stage -- _encode_message at gateway/src/gateway.py:1112 -- has no memo, so the expansion happens there instead. The two pins that cover this (test_shared_but_acyclic_structure_is_not_refused_as_a_cycle, test_shared_structure_costs_linear_work_not_exponential) call the private walkers directly and therefore cannot see it. This is a relocation, not a regression -- before the fix the same datagram exploded at _find_forbidden_key -- but the closure claim overstates, and the new location is arguably nastier: the pre-fix failure was an unbounded loop, this one materializes a multi-hundred-megabyte string and hands it to sendto.

**Evidence:**

```
cbor2 value_sharing datagram -> gateway.process_message (cbor2-only install, strict_validation=True, profile matched) -> gateway._encode_message(out[0], "json"), each stage timed:
  2**18 paths,  767B datagram: ingress 3.9ms -> json egress   5,505,660 B in 0.06s
  2**20 paths,  789B datagram: ingress 1.3ms -> json egress  22,020,732 B in 0.23s
  2**22 paths,  811B datagram: ingress 1.2ms -> json egress  88,081,020 B in 0.87s
  2**24 paths,  833B datagram: ingress 1.3ms -> json egress 352,322,172 B in 3.53s
4x per added level; 833 B in -> 352 MB out is ~420,000x amplification. A 899-byte datagram is 2**30 paths (~22 GB). Compact egress is the same shape and refuses only after paying the cost: zmeta_compact.dumps at 2**20 took 2.74s to refuse, at 2**22 it had not returned in 6s. Meanwhile the three fixed walkers on the identical structure at 2**64 paths: 0.000s each.
```

### R2-14 (MODERATE) — **INTRODUCED BY REMEDIATION** — _log_sink_failures substitutes a clean 0 for an unknown counter, regressing the cumulative write_failures_total from a previously-reported 200 to 0 and silencing the whole sink_degraded surface while the sink is still dead

**Location:** `gateway/src/gateway.py:467`

**Claim:** The defensive read the author added (`except Exception: return 0, 0`, gateway.py:467, and the sibling `if total < 0: return 0, 0` at :469) does not degrade to "unknown" — it degrades to "zero losses". The pair is consumed verbatim by both new surfaces: the console line's print condition at gateway.py:542 (`if console_delta or log_delta or self.console_failures or log_total`) and the machine-readable record fields at gateway.py:571-573 (`"write_failures": window["log_write_failures"], "write_failures_total": log_total`). Consequences, all demonstrated: (1) the cumulative total is not monotone — it reads 200, then 0, then 250 — so any delta-based collector sees a counter reset and either drops or double-counts; (2) the `metrics sink_degraded` line, the surface this remediation exists to add, disappears entirely for that interval, restoring exactly the silent degradation residual (b) named; (3) the JSONL record unconditionally asserts `write_failures_total: 0` — a positive claim of a healthy sink — at the moment the gateway knows least. The honest shape is available with zero vocabulary change: return the last known total (`self._log_failures_seen`, already tracked at gateway.py:471) so the counter can never go backwards, and/or omit the fields rather than emitting a fabricated 0. The docstring at gateway.py:451-459 claims "the console channel then says nothing it cannot support" — but the log record channel does say it, unconditionally, so the code contradicts its own stated contract. This is the constraint-5 pattern: a cleaner value silently substituted for a degraded one, on the very channel the remediation added to make degradation visible.

**Evidence:**

```
Live probe against the current tree, real GatewayMetrics with an operator-supplied logger whose write_failures read is transiently unavailable (the exact shape the new except branch was written for, and the one its own pin at test_gateway_runtime_guards.py:705 constructs):
  interval 1 (counter readable, 200 records genuinely lost)
    console: 'metrics sink_degraded console_failures=0 write_failures=200 console_failures_total=0 write_failures_total=200'
    record : {'write_failures': 200, 'write_failures_total': 200}
  interval 2 (counter read raises; sink still dead, still 200 lost)
    console: []                      <-- sink_degraded line GONE
    record : {'write_failures': 0, 'write_failures_total': 0}   <-- asserts a healthy sink
  interval 3 (counter readable again, 250 lost)
    console: '... write_failures=50 ... write_failures_total=250'
Unpinned, proven by mutation in an isolated scratch copy of the tree: changing gateway.py:467 to `return 0, 999999` (a blatantly fabricated total) -> 42 passed, 29 subtests passed, rc=0. The pin that reaches this line, test_gateway_runtime_guards.py:705 test_reading_the_counter_off_a_hostile_logger_is_not_an_outage, asserts only that maybe_log does not raise and that 'metrics interval=' was printed; it makes no assertion about any reported count, so it actively blesses whatever value the except branch invents.
Second, more ordinary instance of the same class: an operator-supplied sink with no write_failures attribute at all (getattr default 0 at gateway.py:461). Probe: sink lost 51 of 51 records; gateway printed no sink_degraded line and handed that same sink a record reading {'write_failures': 0, 'write_failures_total': 0}.
```

### R2-15 (MODERATE) — **INTRODUCED BY REMEDIATION** — Retrying the warning until delivered reintroduces the warning storm the one-shot latch exists to prevent — 1000 warnings / 473,000 bytes on stderr — and the author's stated justification that 'zero bytes are produced by definition' is false for the exact stream shape their own test double models

**Location:** `gateway/src/gateway.py:692`

**Claim:** The remediation changed both latches to `self._warned = _warn_stderr(...)` (gateway.py:692) and `self._console_warned = _warn_stderr(...)` (gateway.py:380), so the warning is re-attempted on every failed write until one is delivered. The stated new failure mode says this 'can never storm, because zero bytes are produced by definition (a stderr that delivers latches immediately and never fires again)'. That is only true when the failure surfaces at write. The flush half of the fix (gateway.py:256-258) exists precisely because the failure often surfaces at flush instead — and in that case `print()` HAS already written the bytes into the stream, `_warn_stderr` returns False anyway, the latch stays open, and the next failed write prints the whole ~473-byte warning again. Bytes are produced, unboundedly, once per failed metrics write on the datagram path. The pre-remediation code produced exactly one. The two halves of the fix therefore contradict each other: the flush check is what makes the retry loop reachable on a stream that accepts writes. This is not laundering and no event data is affected — it is a resource/noise regression confined to the already-degraded path, but 'one warning per datagram on a full disk is its own outage' is the module's own stated reason for the one-shot design (gateway.py:648-651), so the remediation partially undoes the property it preserved elsewhere. A proportionate in-class fix exists that does not have the defect the author correctly rejected (a retry CAP, which would silently stop reporting recovery): bound the retry in TIME rather than in count — re-attempt at most once per metrics interval — which still lands a warning whenever stderr comes back, at O(1) lines per interval instead of O(1) per record.

**Evidence:**

```
Both probes run against the current tree with the real MetricsLogger.
(1) stderr whose write() accepts and flush() raises — byte-for-byte the semantics of the author's own _FlushFailsStream at gateway/tests/test_gateway_runtime_guards.py:475-497:
    1000 logger.write() calls -> write_failures=1000, latch=False,
    bytes actually written to stderr = 473000, warning lines = 1000
  The pin that uses this stream, test_gateway_runtime_guards.py:563 test_a_queued_warning_is_not_a_delivered_warning, issues only 2 writes, so it can never observe the flood it enables.
(2) realistic full-disk stderr — io.TextIOWrapper(line_buffering=True) over io.BufferedWriter(8192) over a raw object that raises OSError(ENOSPC) on every write, i.e. `gateway 2> /path/on/a/full/disk`:
    2000 logger.write() calls -> write_failures=2000, latch=False,
    failed raw write(2) attempts against the dead fd = 2000
  Pre-remediation (latch set on attempt) this number was 1.
The latch/delivery fix itself is sound and non-vacuous: reverting it (self._warned = True + bare call) fails 3 tests, and reverting only the flush half fails test_a_queued_warning_is_not_a_delivered_warning. The finding is the unbounded retry the fix enables, not the fix's premise.
```

### R2-16 (MODERATE) — The in-band gap marker is written through the rotating sink, so log rotation between the marker and the record it precedes separates them — and with metrics_log_backups<=0 destroys the marker outright, leaving exactly the contiguous-looking pair the marker exists to prevent

**Location:** `gateway/src/gateway.py:671`

**Claim:** MetricsLogger.write emits the marker with `self._write(...)` at gateway.py:673-682 and then the real record with `self._write(record)` at :684. `_write` (gateway.py:619-623) re-runs `_rotate_if_needed()` on every call, so the two are not atomic with respect to rotation. When the file crosses max_bytes on the marker's own append, the record that follows the gap starts a NEW file and the marker stays behind in the previous one. A live-tail consumer — the consumer the README at gateway/README.md:165-168 addresses ('a consumer reads the gap instead of seeing two records that look contiguous') — sees the post-gap record with no marker at all. With `backups <= 0` the rotation branch at gateway.py:608-610 truncates in place (`self.path.write_text("")`), and the marker is not merely relocated but erased: it exists nowhere on disk. `max(0, int(backups))` at gateway.py:591 makes 0 a reachable operator setting. This is not a regression (there was no marker before) but the class it targets is not closed: the loss-marking surface is defeated by the module's own rotation, and it is defeated silently. In-class fixes that need no vocabulary change: write the marker and the record through a single _write call (one open, both lines), or re-emit the marker after a rotation that occurred while _pending_gap was being flushed.

**Evidence:**

```
Live probe against the current tree, MetricsLogger(max_bytes=200), 1 healthy record, 3 lost, then recovery:
  backups=3  live metrics.jsonl = ['violation']            <-- post-gap record alone
             metrics.jsonl.1     = ['violation','metrics_sink_gap']
             marker present somewhere on disk: True (but not in the live file)
  backups=0  live metrics.jsonl = ['violation']            <-- post-gap record alone
             marker present ANYWHERE on disk: False        <-- marker destroyed
The pin, gateway/tests/test_gateway_runtime_guards.py:650 test_lost_records_are_marked_in_band_when_the_sink_recovers, constructs `gateway.MetricsLogger(self.path)` with the default max_bytes of 5_000_000 (gateway.py:83) and writes ~200 short records, so it never crosses a rotation boundary and structurally cannot observe this. Its assertion `self.assertEqual(['violation','metrics_sink_gap','violation'], kinds)` is read off a single file.
```

### R2-17 (MODERATE) — **INTRODUCED BY REMEDIATION** — An unknown token anywhere in a producer rule now refuses that producer wholesale, including events the surviving entries explicitly authorize and events the broken key never governed

**Location:** `gateway/src/validators.py:951`

**Claim:** `_producer_rule_policy_error` returns a policy error for any entry outside the schema-derived event_type vocabulary (:951-957), and `validate_routing` / `validate_producer_authority` turn that into a refusal of every event from that producer (:3533-3546, :3362-3375). For `allowed_event_types` the check is largely redundant (an unknown token already fails closed by itself), so the whole runtime behavior change lands on the two cases where the old behavior was benign: (a) `forbidden_event_types` carrying a token no event can carry, which was an inert no-op and is now a total refusal of that producer's traffic; (b) a partially-typoed `allowed_event_types`, where the surviving correct entries used to keep working. This is the author's declared proportionality judgement ('scoped to the producer whose rule is broken... the adjudication is no longer trustworthy for it') and the direction is fail-closed, so it is not laundering — but it does discard good data on configs that previously worked, and constraint 5 makes that a maintainer decision rather than an implementer one. The gap is worth naming precisely because the author's own summary presents the runtime change as closing a fail-open, and for `allowed_event_types` it does not.

**Evidence:**

```
Shipped policy, one key changed, same event (torch INFERENCE_EVENT/CLASSIFICATION, which the shipped policy admits):
  routing.producers.torch.forbidden_event_types = ['VENDOR_ONLY_EVENT']   CUR: refused   PRE: admitted
  routing.producers.torch.forbidden_event_types = ['COMMAND_EVEN']        CUR: refused   PRE: admitted
(the first token is inert by construction — it names nothing the kernel can emit — and the rule it sits in never governed INFERENCE_EVENT.)
The partially-typoed allowed list is the author's own pin, test_routing_allowed_event_types: `['STATE_EVEN', 'FUSION_EVENT']` with a FUSION_EVENT event, asserted refused. FUSION_EVENT is named correctly and unambiguously in the surviving entry.
```

### R2-18 (MODERATE) — **INTRODUCED BY REMEDIATION** — `test_risk_mode_lint_survives_a_mangled_block` pins the wrong property (it asserts only 'does not raise') and one third of it is vacuous

**Location:** `gateway/tests/test_policy_shape_fail_closed.py:895`

**Claim:** The pin's body is a bare call — `validators.lint_policy_risk_modes(policy)` at :904 — with no assertion on the result. It therefore certifies 'the lint did not traceback' as sufficient and actively locks in the silence documented in the previous finding: for `timing_freshness` the correct post-condition ('a destroyed block is REPORTED') is never asserted, and the pin passes precisely because nothing is reported. Second, the `lineage` arm is vacuous: reverting `_mapping_or_empty` to the identity function (in-memory patch of the module attribute, so every internal call site sees it) fails only the `producer_authority` and `timing_freshness` sub-cases. The 5 `lineage` sub-tests pass with the fix reverted, because a mangled `lineage` block never raised in the first place — measured directly against the pre-remediation module. 5 of the pin's 15 subtests exercise no code path the change touches.

**Evidence:**

```
Revert-simulation, in-memory (no source edited, so the .pyc staleness trap the author flagged cannot apply), run with PYTHONDONTWRITEBYTECODE=1 and -B:
  ATK3_REVERT=none              -> 59 passed, 400 subtests passed
  ATK3_REVERT=mapping_or_empty  -> 10 failed, 59 passed, 390 subtests passed
     SUBFAILED(block='producer_authority', bad=None|'SOME_VALUE'|7|['a']|True)   x5
     SUBFAILED(block='timing_freshness',   bad=None|'SOME_VALUE'|7|['a']|True)   x5
     (no SUBFAILED for block='lineage' — all 5 pass with the fix reverted)
Corroborated against the pre-remediation module directly:
  PRE lineage=None:      issues=0   (did not raise)
  PRE lineage=['a']:     issues=0   (did not raise)
  PRE timing_freshness=None: RAISED AttributeError
All other new pins are non-vacuous — verified by seven further reverts, each watched failing:
  unknown_tokens ->18 failed (EventTypeVocabularyFailsClosedTest); bogus_vocab ->47 failed (incl. test_real_event_types_stay_green, refuting the tautology hypothesis); doc_lint ->2 failed; rule_policy_error ->22 failed; routing_lint_silent ->5 failed (test_routing_block); authority_lint_silent ->5 failed (test_producer_authority_block).
```

### R2-19 (MODERATE) — **INTRODUCED BY REMEDIATION** — The new cycle refusal tells the operator to switch to json/cbor/proto, and all three provably fail on the same event -- into an uncounted-to-the-consumer INTERNAL_ERROR drop

**Location:** `zmeta_compact.py:533`

**Claim:** The remediation's new refusal ends "...use a version-preserving encoding (json/cbor/proto)" (zmeta_compact.py:529-534). That tail is correct on the pre-existing bignum branch -- JSON really can carry 2**70 -- and it was copied onto a branch where it is false: a reference cycle has no encoding in ANY of the three. The text is not internal; it ships verbatim to the consumer as details={"error": error} in the forwarded ENCODING_UNSUPPORTED diagnostic (gateway/src/gateway.py:1128). Acting on the advice makes things strictly worse: json/cbor raise ValueError/CBOREncodeValueError, which are NOT in _COMPACT_UNREPRESENTABLE (gateway.py:988), so nothing is forwarded at all -- the receive-loop backstop at gateway.py:2375 records an INTERNAL_ERROR drop and the consumer sees silence where compact at least gave it a governed refusal. The remediation's own write-up names that downgrade as an accepted new failure mode; it does not name that its new refusal text actively steers the operator into it. This is a free-text change inside an existing CompactUnrepresentableError, so correcting it needs no schema, policy or violation-code change.

**Evidence:**

```
Measured on the same self-referential vendor blob:
  json.dumps                   ValueError: Circular reference detected
  cbor2.dumps(canonical=True)  CBOREncodeValueError: cyclic data structure detected
  cbor2.dumps(default)         CBOREncodeValueError: cyclic data structure detected
  zmeta_cbor.dumps             RecursionError: maximum recursion depth exceeded
What the operator is actually handed (gateway._encode_outgoing_or_diagnostic, output_encoding=compact):
  reason_code: ENCODING_UNSUPPORTED
  error: "compact cannot encode $.payload.extensions.vendor.self: the structure refers back to itself, and a reference cycle has no finite CBOR encoding; use a version-preserving encoding (json/cbor/proto)"
And what following that advice produces, same event, same helper:
  output_encoding=compact -> ok: 383-byte diagnostic forwarded
  output_encoding=json    -> raises ValueError: Circular reference detected   (escapes _COMPACT_UNREPRESENTABLE -> receive-loop backstop -> INTERNAL_ERROR drop, nothing forwarded)
  output_encoding=cbor    -> raises CBOREncodeValueError: cyclic data structure detected   (same)
```

### R2-20 (MINOR) — **INTRODUCED BY REMEDIATION** — The new reason_code parameter is checked for presence but never for vocabulary or consistency: the newly reachable DEGRADED path can still emit schema-invalid events, and reason_code is accepted under state='UP'

**Location:** `adapters/ingress/mavlink/mavlink_to_zmeta_template.py:615`

**Claim:** The stated rationale for adding `reason_code` is 'the honest degraded path emits a schema-valid event instead of an invalid one'. Only presence is enforced (:598-601). The value is copied into metrics unchecked (:615-616), while the sibling guard three lines above (:596-601) validates `state` against the declared _LINK_STATUS_STATES vocabulary and refuses. The v1.0 schema enum-constrains metrics.reason_code to twelve codes, so a DEGRADED with an out-of-vocabulary reason still emits schema-invalid — on a path that did not exist before this pass (state was hard-coded 'UP', so DEGRADED/DOWN were unreachable). Second asymmetry: `reason_code` is stamped regardless of state, so state='UP' with reason_code='JAMMED' emits and validates — a self-contradicting LINK_STATUS, the same shape as the TIME_STATUS contradiction this pass was written to remove. Both are closable in-module with a literal code tuple mirroring the schema (the pattern already used for _LINK_STATUS_STATES at :27) or, if duplicating the vocabulary is unwanted, by restricting reason_code to the DEGRADED/DOWN branch and letting the gateway adjudicate the code.

**Evidence:**

```
Live probe, shipped schema:
  translate_link_status(..., state='DEGRADED', reason_code='NOT_A_CODE')
    -> SCHEMA-FAIL: 'NOT_A_CODE' is not one of ['LINK_LOSS','LOW_RSSI','HIGH_LATENCY','HIGH_PACKET_LOSS','LOW_THROUGHPUT','INTERFERENCE','JAMMED','BACKHAUL_DOWN','NO_ROUTE','CONFIG_ERROR','POWER_SAVE','UNKNOWN_CAUSE']
    (no ValueError from the adapter; the event is built and returned)
  translate_link_status(..., state='UP',      reason_code='JAMMED') -> SCHEMA-OK | validate_semantics (True, [])
  translate_link_status(..., state='UNKNOWN', reason_code='JAMMED') -> SCHEMA-OK | (True, [])
  translate_link_status(..., state='GREEN')  -> ValueError (state vocabulary IS enforced)
test_mavlink_link_status_refuses_unusable_verdicts covers only the state vocabulary and the missing-reason_code case.
```

### R2-21 (MINOR) — The comment justifying the new two-sided satellites guard asserts the battery sentinels are already guarded on both sides; the translator-side voltage guard is `> 0` and passes the UINT16_MAX sentinel through as a 65.535 V measurement

**Location:** `adapters/ingress/mavlink/mavlink_to_zmeta_template.py:241`

**Claim:** The new comment at :221-225 grounds the repeated satellites guard in 'the same way the battery sentinels below are guarded on both sides'. Only one of the two is. `battery_pct >= 0` (:244) does drop the -1 sentinel translator-side. `battery_v is not None and battery_v > 0` (:241) drops a fabricated 0.0 V but not 65.535 V — the UINT16_MAX 'voltage not sent by autopilot' sentinel after the /1000 conversion, which is exactly what the pre-fix decoder in this same module performed (`msg_dict.get("voltage_battery", 0) / 1000.0`, now corrected at :288-290). Any fielded bridge copied from the pre-fix template therefore hands the translator 65.535 and the translator publishes it as a battery measurement. The premise the comment relies on — 'a state dict can be assembled by any MAVLink bridge' — is what makes this reachable; the same argument that justified repeating the satellites guard applies unrepeated to voltage. Same gap in translate_link_status (:606-607: `if battery_voltage is not None`), which has no decoder in front of it at all.

**Evidence:**

```
Live probe, shipped schema + policy:
  translate_platform_state({lat:34.0, lon:-118.0, alt_m:100.0, gps_fix_type:3, battery_voltage:65.535, battery_remaining_pct:-1, ...})
    -> payload.quality = {'battery_voltage': 65.535, 'geo_status': 'AVAILABLE', 'gps_fix_type': 3}
       (the -1 sentinel is correctly dropped; the 65.535 V sentinel is published)
  translate_link_status(..., battery_voltage=65.535) -> metrics['battery_voltage'] = 65.535 | SCHEMA-OK
```

### R2-22 (MINOR) — **INTRODUCED BY REMEDIATION** — _wire_safe_details reproduces, inside the same remediation, the two blindnesses the kernel walk was widened to remove: it does not sanitize non-finite Mapping KEYS, and it dispatches on concrete container types only

**Location:** `gateway/src/gateway.py:1650`

**Claim:** Fix (b) is placed at the builder boundary and its docstring claims "it closes the class for every validator, present and future" (gateway.py:1607-1609). It does not. (1) `for key, value in original.items(): target[key] = _convert(value)` (:1663) converts values only — a non-finite Mapping KEY survives verbatim, and `json.dumps` then launders a NaN key into the STRING "NaN". That is the exact laundering the sibling kernel walk cites as its stated reason for walking map keys (`_child_entries` docstring, validators.py:~380: "a CBOR producer can send a float map key - which json.dumps would launder into the string 'NaN'"). (2) `_convert` dispatches on `isinstance(value, (dict, list, tuple, set, frozenset))` (:1650), i.e. concrete types — the same dict/list-only mistake fix (c) removed from `_find_non_finite` one file over. A non-dict `Mapping` (cbor2.frozendict) or a `.tag`/`.value` wrapper passes through with its non-finite intact. I could NOT demonstrate reachability through the shipped pipeline: every validator upstream of the value-honesty gate puts string-keyed scalars in details (validate_schema :2366 strings; validate_role :2387/:2398 schema-constrained strings; validate_timing_quality :2513-2520 floats/strings plus YAML policy blobs), and inside validate_semantics the gate returns first. The finding is the "present and future" claim: the one detail site that already echoes an arbitrary event-derived object (validators.py:2755 `"value": quality.get("bearing_frame")`) is safe today only because of an ordering the author explicitly declined to change.

**Evidence:**

```
Direct probes against the shipped gateway._wire_safe_details:
  P1 non-finite dict KEY
    in : {'field': 'payload.metrics.est_error_ms', 'histogram': {nan: 3}}
    out: {'field': 'payload.metrics.est_error_ms', 'histogram': {nan: 3}}   key type 'float', isnan True
    json.dumps(out, allow_nan=False) -> ValueError: Out of range float values are not JSON compliant: nan
    json.dumps(out)                  -> {"field": "...", "histogram": {"NaN": 3}}   <- laundered to a string
  P2 non-dict Mapping value
    in : {'vendor': FrozenMapping({'x': nan})}
    out: {'vendor': FrozenMapping({'x': nan})}   still a Mapping, raw nan preserved
  P2b real cbor2 frozendict as a map key
    in : {'decoded': {frozendict({'a': nan}): 1}}
    out: unchanged; surviving key type 'frozendict'
  P3 tag wrapper
    in : {'blob': Tag(1234, [nan])}
    out: {'blob': Tag(1234, [nan])}   .value still non-finite
  P4 control (what the sanitizer DOES cover)
    {'d': Decimal('NaN'), 'i': Decimal('-Infinity')} -> {'d': '<non-finite:nan>', 'i': '<non-finite:-inf>'}
The scalar/dict/list half is genuinely load-bearing: reverting _wire_safe_details to identity fails 4 pins (r_details_sanitizer rc=1, 4 failed).
```

### R2-23 (MINOR) — **INTRODUCED BY REMEDIATION** — The widened cycle protection is unpinned for every container the widening added — narrowing the seen-set marker back to (dict, list, tuple) leaves BOTH new suites 100% green

**Location:** `gateway/src/validators.py:333`

**Claim:** The author's second-order risk section states that widening the dispatch could have reopened the remote-hang defect and reports it pinned. What is pinned is the dict/list case only. `validators._is_traversable` (:333-340) decides which nodes get an id() in the seen-set; both cycle pins — `NonFiniteContainerCoverageTest::test_container_walks_still_terminate_on_a_cycle` (test_non_finite_value_scoped.py:465) and `test_zmeta_to_cot_guard_terminates_on_a_cyclic_payload` (test_zmeta_to_cot.py:646) — build their cycles out of a self-referential dict and a self-referential list, both of which stay traversable under any narrowing. So the cycle protection added for Mapping / Set / tag-wrapper containers has no pin: a future edit that narrows the marker condition back to concrete types restores the hang for those shapes and no test objects. HEAD itself is correct here; this is a pin gap in new code, not a live defect.

**Evidence:**

```
Revert-simulation, scratch mirror, sources restored afterwards:
  r_traversable      (validators._is_traversable narrowed to (dict,list,tuple) only)
                     rc=0   32 passed, 111 subtests passed
  c_mapping_branch   (CoT _has_non_finite seen-set condition narrowed to (dict,list,tuple))
                     rc=0   33 passed
Both are silent. The load-bearing half is proven separately — removing the seen-set entirely does hang:
  r_seen_nonfinite   rc=99  HUNG (no termination in 45s)
  c_seen_set         rc=99  HUNG (45s)
So the pins prove "a seen-set exists for dicts and lists", not "the widened container set is cycle-safe".
```

### R2-24 (MINOR) — **INTRODUCED BY REMEDIATION** — The new document lint fails a comment-only or empty `producer-authority.yaml` — the same deployment the same function deliberately skips when the file is absent — while adding no coverage that file did not already have

**Location:** `gateway/src/validators.py:2299`

**Claim:** `lint_policy_document_structure` skips a file that does not exist (:2320-2325, comment: 'An absent document is the documented "no policy of this kind" deployment'), but reports `<file>#<wrapper>` when the file exists and lacks the wrapper key. `load_policy` (validators.py:117-120, 139) makes those two cases byte-identical in memory: an absent file and an empty/comment-only file both yield `producer_authority = {}`. So a deployment shipping a commented-out producer-authority.yaml stub now gets a FAIL that the same deployment with the file deleted does not. Second, for producer-authority.yaml specifically the check adds nothing: `load_policy`'s fallback for that file is the WHOLE document, so a `producr_authority:` typo already surfaced pre-remediation as `producer_authority.producr_authority` from the existing unknown-key lint. The genuine new coverage is routing.yaml only, where the fallback is `{}`. Impact is currently masked by a PRE-EXISTING false positive on the same configs (`producer_authority.producers must be a mapping` when `producers` is simply absent — present in the pre-remediation module too, correctly disclosed by the author as not introduced), which already makes the CLI exit 1; if that pre-existing one is fixed this inconsistency becomes operator-visible.

**Evidence:**

```
Shipped CLI on scratch copies of policy/:
  producer-authority.yaml = '# no producer-authority policy in this deployment'
     exit=1, 2 FAILs: producer_authority.producers  AND  producer-authority.yaml#producer_authority
     PRE issues for the same dir: ['producer_authority.producers']   (only the pre-existing one)
  producer-authority.yaml ABSENT
     exit=1, 1 FAIL: producer_authority.producers   (document lint correctly silent)
Coverage overlap, `producr_authority:` typo:
  CUR in-memory lint: ['producer_authority.producr_authority', 'producer_authority.producers']
  CUR document lint : ['producer-authority.yaml#producer_authority']
  PRE in-memory lint: ['producer_authority.producr_authority', 'producer_authority.producers']   <- already caught before the remediation
`routng:` typo in routing.yaml:
  CUR in-memory routing lint: []      CUR document lint: ['routing.yaml#routing']   <- the real new coverage
```

### R2-25 (MINOR) — Only the log-sink half of the window-vs-cumulative distinction is pinned: mutations that restate the running console total as the per-window count pass all 42 tests, including the two pins written for the console counter

**Location:** `gateway/tests/test_gateway_runtime_guards.py:758`

**Claim:** test_sink_failure_counters_reach_both_operator_surfaces (test:727) pins the windowed property for the LOG sink only — it runs a second interval and asserts `second['write_failures'] == 0` while `write_failures_total` stays 200 (test:754-756). The console counter has two dedicated pins (test_console_losses_are_reported_on_the_channel_that_still_works at test:758, and the class guard at test:771) and neither of them distinguishes the window value from the cumulative one: test:768-769 asserts only `record['console_failures'] > 0` and `metrics.console_failures == record['console_failures_total']`, and the class guard checks name presence, not value. So the exact defect the log half is pinned against — a running total restated as a per-window count, which makes an operator read a long-past outage as an ongoing one every interval forever — is unguarded on the console half. The code today is correct at gateway.py:541 and :570; the pin is what is asymmetric, and the residual being remediated (b) was itself a 'this counter has no honest surface' finding, so the surface's honesty properties are the thing that most needs pinning.

**Evidence:**

```
Mutation harness on an isolated scratch copy of the tree, running gateway/tests/test_gateway_runtime_guards.py in full:
  M2  gateway.py:570  '"console_failures": window["console_failures"]' -> 'self.console_failures'
        -> 42 passed, 29 subtests passed, rc=0   *** UNPINNED ***
  M3  gateway.py:541  'console_delta = window["console_failures"]' -> 'console_delta = self.console_failures'
        -> 42 passed, 29 subtests passed, rc=0   *** UNPINNED ***
Control: the structurally identical mutation on the log-sink half is caught —
  G   gateway.py:470-472  'delta = max(0, total - self._log_failures_seen) ...' -> 'return total, total'
        -> 1 failed (test_sink_failure_counters_reach_both_operator_surfaces), rc=1
```

### R2-26 (OBSERVATION) — **INTRODUCED BY REMEDIATION** — The SYNCED -> LOCKED normalization added to the decoded path converts a previously schema-refused event into a clean state='UP' driven by an arbitrary bridge string

**Location:** `adapters/ingress/mavlink/mavlink_to_zmeta_template.py:505`

**Claim:** `metrics["sync_state"] = _normalize_sync_state(msg.get("sync_state") or "UNSYNCED")` (:505) is new. Before it, a message carrying sync_state='SYNCED' emitted 'SYNCED', which is outside the schema's [LOCKED, HOLDOVER, UNSYNCED] enum, so the gateway refused the event loudly. After it, the same message validates and — through the shared derivation — emits payload.state='UP', the most confident timing verdict the field has, from an unvalidated string in bridge input. The author disclosed this and the equivalence was already declared in translate_time_status, so I am not calling it laundering; I am recording it because it is the one direction-of-travel in this pass that makes an event cleaner than it was, and it compounds with the carried-state finding above (the same unvalidated field now drives both metrics.sync_state and payload.state). Only the exact literal 'SYNCED' is promoted; every other unknown label still fails the enum loudly, which is what keeps the blast radius small.

**Evidence:**

```
Live probe, msg={'msg_type':'SYSTEM_TIME','sync_state':'SYNCED','est_error_ms':3.5,'last_sync_ts':'2025-01-17T15:19:00Z'}:
  NEW: payload.state='UP'  metrics.sync_state='LOCKED'  | SCHEMA-OK | validate_semantics (True, [])
  OLD (verbatim passthrough, same event otherwise): SCHEMA-FAIL: 'SYNCED' is not one of ['LOCKED','HOLDOVER','UNSYNCED']
```

### R2-27 (OBSERVATION) — The repaired provenance sweep is structurally blind to the carried-verdict half of the class it was extended to cover: a carried value is 'reported' by construction, so a laundered payload.state traces to an input and passes

**Location:** `adapters/ingress/mavlink/test_mavlink_ingress.py:460`

**Claim:** The sweep's acceptance rule is `if (type(node).__name__, node) in reported: return`, where `reported` is every scalar in the inputs including the message dict. Any verdict the caller supplied is therefore accepted at any path, unconditionally. That is correct as *provenance* — the value did come from the input — but it means the sweep cannot see the defect the two extended pins are named for: `payload.state = 'NOMINAL'` / `'LOCKED'` / `'UP '` under an UNSYNCED metrics block all trace to `msg['state']` and pass, as does reason_code='JAMMED' under state='UP'. The remaining fabrication class the sweep does close is real (the author's six mutations verify it), but the README claim it now backs — 'every scalar this adapter emits is either a value the telemetry carried or a constant declared' — is satisfied by a carried value placed in a field it contradicts, which is the more dangerous half. The sweep is a provenance oracle; consistency between payload.state and its own metrics block needs a separate assertion, and only two such assertions exist (emitters_agree, never_launders), both scoped to the {UP, SYNCED, DOWN} exemplars. Secondary, smaller: the sweep only walks leaves that are present, so it never checks that a declared path still *exists* — for the four schema-validated events VALIDATOR.validate covers required fields, but the catch-all LINK_STATUS case is deliberately not schema-validated, so a dropped field there is invisible to both.

**Evidence:**

```
Reading _undeclared_leaves (test_mavlink_ingress.py:460-486) plus the live probe: the sweep and every other test in the file pass (50 passed) while mavlink_decoded_to_zmeta_system_events emits payload.state='UP ' and 'LOCKED' and 'NOMINAL' over metrics.sync_state='UNSYNCED', and translate_link_status emits state='UP' with metrics.reason_code='JAMMED'. No mutation is required to demonstrate it — the defects are live on the tree the sweep is green on.
```

### R2-28 (OBSERVATION) — (e) closes a shape the documented wire format cannot produce: a non-finite dict KEY is unreachable from protobuf-JSON, so the 'four events became zero' exposure it repairs is not a fielded one

**Location:** `adapters/ingress/sapient/sapient_to_zmeta.py:193`

**Claim:** The new key rule in `_drop_non_finite_inner` (:193-200) triggers only on `isinstance(key, float)`. The module's stated input is protobuf-JSON dicts (module docstring; `snake_keys` normalisation), and neither `json.loads` nor protobuf's MessageToDict can produce a float dict key — RFC-8259 object member names are always strings, and proto3 map keys may not be floating point. The fix is harmless defence-in-depth and it does close a genuine asymmetry with the value rule, but the residual's headline ('one weird key silently turns 4 events into 0') and its pin both construct the shape in Python, so the maintainer should not weight it as a fielded fix. Stated so the disposition is not over-credited; no change recommended.

**Evidence:**

```
`test_a_non_finite_vendor_key_drops_its_entry_and_keeps_the_detection` (test_sapient_ingress.py:2242-2271) builds the poison with Python literals — `msg['detection_report']['track_info'] = [{float('nan'): 'dropped', 'ok': 1.0}, ...]` at :2252-2260. Every other pin in the file routes through `json.loads(json.dumps(base))` (e.g. :2214, :1970), which cannot carry a float key. The remaining non-finite VALUE cases (proto3 JSON 'NaN'/'Infinity') are wire-reachable and are unaffected by this change; `test_a_non_finite_vendor_value_still_drops_and_a_list_still_drops_whole` (:2274-2286) still pins them, and the emit-boundary backstop at :2289-2302 still covers canonical sites.
```

### R2-29 (OBSERVATION) — **INTRODUCED BY REMEDIATION** — window['log_write_failures'] is the only counter in GatewayMetrics that bypasses _bump, so self.total['log_write_failures'] is dead and permanently 0

**Location:** `gateway/src/gateway.py:487`

**Claim:** Every other window counter is incremented through `_bump` (gateway.py:316-318), which updates both `self.window` and `self.total`. The new key added at gateway.py:487 is incremented directly on the window dict, so the corresponding slot in `self.total` — allocated by `_new_window()` at gateway.py:302 — stays 0 for the life of the process. Harmless today because `self.total` is never read out anywhere (grep: only written, at gateway.py:277/318/322), but it is a latent trap: the next author who surfaces `self.total` (the natural way to add the run-total view this change already wants) will get a silent zero for log-sink losses specifically, which is the same 'counter with no honest value' shape residual (b) was about. The console counter next to it does go through _bump (gateway.py:378).

**Evidence:**

```
gateway/src/gateway.py:487 `window["log_write_failures"] += log_delta` versus gateway/src/gateway.py:378 `self._bump("console_failures", 1)`. `grep -n 'self\.total\|\.total\[' gateway/src/gateway.py` returns only lines 277, 318, 322 — all writes, no reads.
```

### R2-30 (OBSERVATION) — The CoT refusal the remediation calls "counted and reason-tagged" is bucketed under the pre-existing generic UNCONVERTIBLE — _cot_skip_reason was not extended

**Location:** `gateway/src/gateway.py:1295`

**Claim:** The proportionality argument for fix (d) rests on the refusal staying "loud and filterable": zmeta_to_cot.py:191-192 and the README hunk both say the gateway buckets it as "a counted, reason-tagged cot_skipped record". `_cot_skip_reason` (gateway.py:1281-1295) was not touched, so an event refused for a non-finite value returns the catch-all "UNCONVERTIBLE" — the same bucket every other unclassified skip already uses. The operator can count the skips but cannot filter a value-honesty refusal apart from any other unconvertible event. Adding a reason string here is adapter-local and needs no governed vocabulary (cot_skipped reasons are gateway-internal, not policy/violation-codes.yaml), so this is a gap the author could close in-ring; I am flagging it rather than claiming a defect because the kernel refuses such an event before CoT is reached in the gateway path, which makes the bucket nearly unreachable in practice.

**Evidence:**

```
gateway/src/gateway.py:1281-1295 `_cot_skip_reason` returns only PAYLOAD_INVALID / MISSING_TRACK_ID / MISSING_GEO / UNCONVERTIBLE; no non-finite arm was added. The caller at :2363-2371 records whatever it returns. A non-finite STATE_EVENT has track_id and geo present, so it falls through to "UNCONVERTIBLE".
```

### R2-31 (OBSERVATION) — Termination of both ingress walks now rests on an unpinned two-function invariant, and neither function is named by any test

**Location:** `gateway/src/validators.py:333`

**Claim:** After this remediation both validators walks terminate only because every value _child_entries (validators.py:343) yields children for is also a value _is_traversable (validators.py:333) returns True for -- that is what gets it into the seen-set. The invariant holds today across every shape I probed, but it is implicit, it is split across two functions written for a different purpose (container coverage, not termination), and a repo-wide grep shows no test references either name. Widening _child_entries to one more decoded type without also widening _is_traversable silently reopens the unbounded walk with the whole suite green -- which is the same shape as the original defect: a guard defeated by code shipped alongside it. Worth a one-line agreement assertion over a probe table, alongside the termination pins that already exist.

**Evidence:**

```
Agreement probe over 15 shapes, current tree -- no live divergence:
  str/bytes/bytearray/int/float/None -> traversable=False, children=[]
  dict/list/tuple/set/frozenset/range/frozendict/CBORTag/memoryview -> traversable=True, children non-empty
Coverage: `grep -rn "_is_traversable\|_child_entries" --include=*.py gateway/tests adapters` returns nothing.
```

### R2-32 (OBSERVATION) — The runtime half of the entry-vocabulary check no-ops silently whenever schema/ is not a sibling of gateway/src; only the deployment-time half announces that it could not run

**Location:** `gateway/src/validators.py:825`

**Claim:** `_KERNEL_SCHEMA_DIR` is fixed at `Path(__file__).resolve().parents[2] / "schema"` (:769). When that directory is not present — a gateway packaged or containerized without the sibling schema tree — `_event_vocabulary` returns an empty frozenset and `_unknown_event_tokens` returns `[]` with an explicit 'report nothing here' comment (:825-829). The lint half handles this correctly and loudly (`_shape_problem` emits 'this check did not run', measured as 44 issues). The runtime half does not: `_require_match_types` and `_producer_rule_policy_error` simply stop checking, with no marker. Not a regression — no vocabulary check existed before — but it means residual (c)'s runtime closure is packaging-dependent and degrades silently in exactly the deployment where the lint also cannot have run. Secondary: `_EVENT_VOCABULARY_CACHE` (:770, :818) caches the empty result permanently, so a first call made before schema/ is reachable disables the check for the life of the process.

**Evidence:**

```
Same module, `_KERNEL_SCHEMA_DIR` repointed at a nonexistent directory and the cache cleared, shipped policy with `require_match_for_event_types = ['STATE_EVEN']`, event from `totally-unregistered-node`:
  schema dir present:  refused, PRODUCER_NOT_ALLOWED, details carry policy_error=True
  schema dir missing:  vocabulary=[]  ->  ADMITTED (True, [])
  lint on the same policy with the dir missing: 44 issues, each 'entries could not be checked: the event_type vocabulary could not be derived from schema/*.schema.json, so this check did not run'
```

---

## Disposition

| | Round 1 | Round 2 |
|---|---|---|
| MAJOR | 10 | 4 |
| MODERATE | 11 | 15 |
| MINOR | 4 | 6 |
| OBSERVATION | 5 | 7 |
| **Total** | **30** | **32** |

Round 1: fully remediated. Round 2: **dispositioned 2026-07-22** by the
disposition pass (`c54215a`) — this line previously read "open,
undispositioned", which that pass falsified without updating it (cold
re-read CR-07). The disposition's own attack round was not persisted
per-finding; see the Status block at the top of this file.

