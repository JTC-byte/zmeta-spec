# S1-05 Encoding Negative Validation Plan

Status: COMPLETE
Date: 2026-05-07
Scope: Plan only. No schemas, validators, codecs, gateway runtime, adapters,
extension registry artifacts, conformance class manifests, semantic contract
text, examples, conformance fixtures, release hashes, or event vocabulary were
changed.

## A. Current Encoding Validation Landscape

ZMeta currently treats JSON as the canonical semantic object. Binary encodings
are transport projections that must decode back to canonical JSON before normal
validation.

Current coverage:

- JSON validation is handled by `tools/validate.py`, `tools/validate_conformance.py`,
  `gateway/src/validators.py`, the canonical dispatcher schema, version-specific
  schemas, and policy YAML files.
- Core conformance fixtures in `conformance/must-pass.jsonl` and
  `conformance/must-fail.jsonl` exercise schema, policy, profile/event-type
  legality, lineage, timing, command governance, and v1.0/v1.1.0 version
  boundaries.
- CBOR is tested as a deterministic binary representation of the same JSON
  event in `gateway/tests/test_encoding_roundtrip.py`.
- Compact CBOR is documented as a Profile L wire-level mapping in
  `spec/compact-binary-mapping.md`. `zmeta_compact.py` expands compact packets
  to canonical JSON before gateway validation.
- Compact decoder coverage already includes roundtrip behavior, deterministic
  built-in CBOR preference, CBOR bound propagation, and unsupported
  `compact_version` rejection.
- Protobuf is documented as an experimental encoding projection in
  `spec/protobuf-encoding.md` and `schema/proto/zmeta_event_v1.proto`.
  `zmeta_proto.py` decodes a typed envelope plus canonical JSON payload bytes.
- Protobuf decoder coverage already includes roundtrip behavior, malformed
  varints, unsupported wire types, invalid field number 0, truncated fields,
  oversized messages, oversized payload JSON, excessive decoded JSON depth, and
  invalid UTF-8 string fields.
- `gateway/src/gateway.py` supports explicit `--input-encoding` values
  `json`, `cbor`, `compact`, `proto`, and `auto`. It decodes first, then runs
  the schema/policy gateway pipeline.
- `tools/convert_encoding.py` converts between JSON, CBOR, compact, and proto.
  It decodes and re-encodes events, but it is not currently a schema or policy
  validator.
- S1-02B/S1-02C added profile projection fixtures where compact/protobuf decoded
  JSON is schema-valid but projection-invalid. Those cases prove encoded form
  cannot override projection preservation.
- S1-04B/S1-04C created conformance classes for `ZMETA-COMPACT-CBOR` and
  `ZMETA-PROTOBUF-PROJECTION`, but broader encoding-negative evidence is still
  deferred under D-007.

Remaining uncovered areas:

- There is no dedicated encoding-negative fixture suite for compact or protobuf.
- Gateway and CLI paths do not yet have broad tests proving decoded
  schema-invalid, policy-invalid, or profile-illegal events are rejected after
  binary decode.
- `tools/convert_encoding.py` decode errors are covered only indirectly by
  focused tests; it does not assert semantic validation after conversion.
- Projection-invalid decoded compact/protobuf cases exist, but there are not yet
  broad invalid-after-decode tests for profile legality, lineage, command
  safety, source authority, extension-registry leakage, and future vocabulary.

## B. Problem Statement

Roundtrip tests prove that valid events can survive encoding and decoding. They
do not prove that invalid encoded events are rejected after decode.

Negative validation is required because:

- encoded invalid events could decode and be accepted by gateway or CLI paths;
- compact Profile L could carry illegal event types or missing lineage;
- protobuf payload JSON could contain schema-invalid or policy-invalid events;
- malformed binary could exercise unsafe parser behavior;
- unknown compact versions could be misinterpreted as current Profile L packets;
- invalid UUID bytes or timestamp encodings could become valid-looking strings;
- v1.1.0 vocabulary could leak into `zmeta_version: "1.0"` through encoding
  paths;
- gateway and CLI paths could behave differently from direct JSON validation;
- encoded packets could bypass projection preservation or conformance-class
  expectations.

The central rule for S1-05B should be: binary decode is necessary but never
sufficient. The decoded JSON event must still pass the same schema, policy,
projection, extension-registry, and conformance expectations as any JSON event.

## C. Negative Validation Categories

### 1. Decode-Level Rejection

Required malformed or unsafe input cases:

- malformed CBOR;
- malformed compact CBOR;
- unsupported `compact_version`;
- invalid compact map shape;
- invalid compact enum values;
- invalid UUID byte length;
- malformed protobuf wire data;
- unsupported protobuf wire type;
- invalid protobuf field number 0;
- oversized protobuf message;
- excessive payload JSON size;
- excessive payload JSON nesting;
- invalid UTF-8 in protobuf payload JSON.

Expected result: decode-level failure before schema or policy validation.

### 2. Decoded Schema-Invalid Rejection

Required decoded-event cases:

- UUIDv4 `event.event_id`;
- timestamp without trailing `Z`;
- `OBSERVATION_EVENT` with top-level `confidence`;
- `INFERENCE_EVENT` missing `confidence`;
- `INFERENCE_EVENT` missing lineage;
- `STATE_EVENT` missing lineage;
- `STATE_EVENT` containing raw observation fields;
- `COMMAND_EVENT` containing altitude-like fields;
- Profile L carrying `OBSERVATION_EVENT`;
- Profile L carrying `FUSION_EVENT`;
- Profile M carrying `INFERENCE_EVENT`;
- v1.1.0-only `SENSOR_STATUS` with `zmeta_version: "1.0"`;
- future/reserved vocabulary such as `RADAR`, `PNT_STATUS`, `UAS_IDENTITY`, or
  `EMERGENCY_L0_PROFILE`.

Expected result: decode succeeds, then canonical schema/profile validation
fails.

### 3. Decoded Policy-Invalid Rejection

Required policy-context cases:

- producer unauthorized for event type;
- command origin not authorized;
- command deconfliction missing where policy requires it;
- lineage parent type mismatch;
- unresolved lineage rejected under M/H where policy context requires
  rejection;
- stale timing status rejected or warned according to policy;
- timing quality missing when policy requires exposure;
- RF window midpoint mismatch.

Expected result: decode and schema validation may succeed, then policy
validation fails or emits the documented warning/error behavior.

### 4. Decoded Projection-Invalid Rejection

Required source/projected pair cases:

- compact/protobuf decoded JSON is schema-valid but projection-invalid;
- confidence increase;
- TTL increase;
- precision increase;
- unit change;
- source rewrite;
- track ID rewrite;
- lineage deletion;
- same-ID observation-to-state collapse;
- same-ID inference-to-state collapse.

Expected result: decoded JSON is compared by the projection validator as the
semantic object. Raw bytes have no projection authority.

### 5. Gateway/CLI Path Rejection

Required runtime/tool path cases:

- invalid compact input rejected through the gateway path;
- invalid protobuf input rejected through the gateway path;
- invalid compact input rejected through conversion/validation tool paths;
- invalid protobuf input rejected through conversion/validation tool paths;
- `auto` input detection does not treat protobuf/compact bytes as valid JSON or
  an unrelated encoding;
- output paths do not silently emit schema-invalid canonical JSON as if it were
  validated.

Expected result: explicit failures, diagnostic rejection events, or nonzero CLI
exit codes, depending on the path under test.

## D. Fixture Strategy

S1-05B should prefer readable JSONL fixture wrappers with generated binary bytes
for semantic cases and short inline bytes for parser cases. This avoids opaque
binary files while keeping failures deterministic.

Recommended directory:

```text
conformance/encoding-negative/
```

Recommended files:

- `conformance/encoding-negative/README.md`
- `conformance/encoding-negative/compact-must-fail.jsonl`
- `conformance/encoding-negative/protobuf-must-fail.jsonl`
- `conformance/encoding-negative/gateway-must-fail.jsonl`
- `conformance/encoding-negative/context.jsonl`

Recommended wrapper fields:

- `name`
- `description`
- `encoding`: `compact`, `proto`, `cbor`, or `auto`
- `case_type`: `decode`, `schema`, `policy`, `projection`, `gateway`, or `tool`
- `input_format`: `hex`, `base64`, `event`, `projection_pair`, or `generated`
- `input_hex` or `input_base64` for short malformed binary inputs
- `event` for decoded semantic failures that should be encoded at test time
- `source` and `projected` for projection pair cases
- `target_profile` when profile legality or projection is involved
- `context` for policy/event-store state
- `expected_stage`
- `expect_code`
- `expect_message_contains`
- `notes`

Recommended storage rules:

- Use hex strings for short malformed CBOR/protobuf bytes.
- Use generated-at-test-time bytes for schema-invalid and policy-invalid events
  so the decoded event remains visible and reviewable.
- Use base64 only when bytes are long enough that hex is noisy.
- Avoid committed binary blobs unless a future interoperability fixture requires
  exact bytes from an external encoder.
- Keep oversized/depth tests small and deterministic by setting low decoder
  limits in test fixtures instead of storing huge payloads.

## E. Validator / Test Harness Strategy

S1-05B should implement a combination:

- standalone CLI: `tools/validate_encoding_negative.py`;
- optional conformance runner flag: `--encoding-negative`;
- focused pytest coverage for compact, protobuf, gateway, and CLI paths.

The standalone CLI should be authoritative for JSONL fixture execution:

```powershell
python tools\validate_encoding_negative.py --fixtures conformance\encoding-negative
```

Suggested explicit mode:

```powershell
python tools\validate_encoding_negative.py `
  --compact conformance\encoding-negative\compact-must-fail.jsonl `
  --protobuf conformance\encoding-negative\protobuf-must-fail.jsonl `
  --gateway conformance\encoding-negative\gateway-must-fail.jsonl
```

The CLI should:

- load JSONL fixtures;
- materialize binary inputs from hex/base64 or generated event encoding;
- run the appropriate decoder;
- run canonical schema/policy validation after successful decode;
- run projection validation for pair fixtures;
- return deterministic reason codes;
- fail nonzero when a must-fail fixture unexpectedly passes or fails at the
  wrong stage.

Focused tests should cover low-level decoder behavior directly and gateway/CLI
behavior at process or API boundaries. The conformance runner should remain
stable by default and run encoding-negative validation only when
`--encoding-negative` is passed.

## F. Gateway Path Coverage

S1-05B should test both explicit and automatic input handling:

- compact input to `Gateway.process_message` or the gateway CLI with
  `input_encoding="compact"`;
- protobuf input with `input_encoding="proto"`;
- `auto` detection for compact bytes, protobuf bytes, malformed bytes, and
  bytes that resemble neither JSON nor CBOR/proto;
- `tools/convert_encoding.py --from compact --to json` for invalid compact
  decode behavior;
- `tools/convert_encoding.py --from proto --to json` for invalid protobuf
  decode behavior;
- paired validation that any JSON emitted by conversion is then rejected by
  `tools/validate.py` when the decoded event is semantically invalid;
- gateway failure reporting for decode failures versus schema/policy failures.

Important distinction:

- `tools/convert_encoding.py` should not be treated as a semantic validator
  unless S1-05B explicitly adds a validation mode.
- A conversion that decodes invalid semantics and emits JSON may be acceptable
  only if the next validation stage rejects that JSON and docs/tests make that
  boundary explicit.

## G. Compact CBOR Negative Test Plan

Compact-specific negative cases:

- malformed CBOR payload;
- top-level CBOR value is not a map;
- compact map missing required top-level keys;
- unknown `compact_version`;
- unsupported event type enum;
- unsupported event subtype enum;
- unsupported profile enum;
- invalid UUID byte length for `event.event_id`;
- timestamp value that expands to invalid or non-UTC semantic time if feasible;
- missing required `event`, `source`, or `payload` maps after expansion;
- missing required `STATE_EVENT` confidence;
- missing required `STATE_EVENT` lineage;
- Profile L compact packet carrying `OBSERVATION_EVENT`;
- Profile L compact packet carrying `FUSION_EVENT`;
- compact `COMMAND_EVENT` that expands to altitude-like command fields;
- compact decoded JSON that is schema-valid but projection-invalid.

Expected failure stages:

- malformed or unsupported wire structure: decode stage;
- invalid expanded event shape: schema/profile stage;
- unauthorized or contextual issue: policy stage;
- source/projected semantic drift: projection stage.

Compact enum behavior needs special attention. Current compact decoding may
preserve unknown enum values as integers or strings for later schema rejection.
S1-05B should assert the expected failure stage for each current behavior rather
than silently changing codec semantics.

## H. Protobuf Negative Test Plan

Protobuf-specific negative cases:

- malformed protobuf wire bytes;
- invalid field number 0;
- unsupported wire type;
- oversized message;
- oversized payload JSON;
- excessive payload JSON nesting;
- invalid UTF-8 payload JSON;
- payload JSON is not an object;
- decoded JSON missing required envelope fields;
- decoded JSON with UUIDv4;
- decoded JSON with wrong or unsupported `zmeta_version`;
- decoded JSON containing v1.1.0-only vocabulary under `zmeta_version: "1.0"`;
- decoded JSON containing future/reserved vocabulary under any current version;
- decoded JSON that is schema-valid but policy-invalid;
- decoded JSON that is schema-valid but projection-invalid.

Expected failure stages:

- malformed wire or invalid payload bytes: decode stage;
- missing or malformed canonical event: schema/profile stage;
- contextual violations: policy stage;
- same-event thinning drift: projection stage.

S1-05B should keep protobuf bounds small in tests by overriding decoder limits
instead of committing large blobs.

## I. Policy and Context Plan

Some negative fixtures require policy or event-store context. The fixture wrapper
should support a `context` object or a named record from
`conformance/encoding-negative/context.jsonl`.

Context needs:

- producer authority by `source.producer`, `source.node_role`, and event type;
- command authorization and deconfliction expectations;
- lineage parent availability and parent event type;
- timing status freshness and fallback `TIME_STATUS` exposure;
- RF observation window start/end/midpoint consistency;
- profile routing/export policy.

Policy-context fixtures should not make schemas deployment-specific. They should
load the existing baseline policy YAML files and add only local test context
needed to exercise gateway/validator behavior.

## J. Projection Preservation Interaction

Encoded projection fixtures must decode to canonical JSON first. Projection
comparison then operates on the decoded source/projected events using
`tools/validate_projection.py` or shared projection validator logic.

Required principle:

> Encoded form is never the semantic object. Compact and protobuf bytes are
> transport forms whose decoded JSON must preserve event identity, source
> identity, semantic layer, track identity, lineage, units, timing semantics,
> confidence monotonicity, TTL monotonicity, and allowed omission rules.

S1-05B should reuse S1-02 failure codes where possible for projection-invalid
decoded events.

## K. Extension Registry Interaction

Encoded packets cannot make reserved or proposed vocabulary valid. After decode,
future names remain invalid unless the selected `zmeta_version` and schema
branch already support them.

S1-05B should include targeted negative decoded cases for high-risk names:

- `RADAR`
- `LIDAR`
- `PNT_STATUS`
- `MODEL_STATUS`
- `TRUST_STATUS`
- `UAS_IDENTITY`
- `RELEASE_LABEL`
- `EMERGENCY_L0_PROFILE`
- `TAKEOFF`

The extension registry validator remains a governance check. Encoding-negative
tests should prove that decoded event validation also rejects future vocabulary
at current schema/policy boundaries.

## L. Conformance Class Interaction

S1-05A does not modify `conformance/conformance_classes.yaml`.

S1-05B should recommend one of two follow-up changes:

1. Add encoding-negative required test commands to existing
   `ZMETA-COMPACT-CBOR` and `ZMETA-PROTOBUF-PROJECTION` class records.
2. Add a separate class such as `ZMETA-ENCODING-NEGATIVE-VALIDATION` for stacks
   that prove invalid-after-decode rejection across compact/protobuf/gateway/CLI
   paths.

Preferred governance direction:

- keep compact/protobuf classes responsible for decoded canonical JSON
  validation;
- add a separate class only if maintainers want encoding-negative coverage to be
  independently claimable across multiple codecs and gateway implementations.

Any manifest change should wait for S1-05B or a later conformance-class update.

## M. Implementation Plan for S1-05B

Recommended file-by-file implementation:

- `conformance/encoding-negative/README.md`
  - Document fixture wrapper format, failure stages, expected reason codes, and
    binary byte storage rules.
- `conformance/encoding-negative/compact-must-fail.jsonl`
  - Compact decode-level, schema-invalid, profile-illegal, policy-invalid, and
    projection-invalid cases.
- `conformance/encoding-negative/protobuf-must-fail.jsonl`
  - Protobuf wire, payload JSON, schema-invalid, policy-invalid, and
    projection-invalid cases.
- `conformance/encoding-negative/gateway-must-fail.jsonl`
  - Gateway and CLI path cases for explicit and auto input encodings.
- `conformance/encoding-negative/context.jsonl`
  - Named policy/event-store contexts for authority, lineage, timing, and
    command deconfliction cases.
- `tools/validate_encoding_negative.py`
  - Standalone validator for negative encoding fixture suites.
- `gateway/tests/test_encoding_negative_validation.py`
  - End-to-end fixture validator tests and conformance runner integration.
- `gateway/tests/test_compact_negative_decode.py`
  - Compact decoder and expanded-event rejection tests.
- `gateway/tests/test_protobuf_negative_decode.py`
  - Protobuf wire/payload/decode rejection tests.
- `tools/validate_conformance.py`
  - Add optional `--encoding-negative` flag only.
- `spec/compact-binary-mapping.md`
  - Add a short reference to the negative fixture suite and decoded validation
    boundary.
- `spec/protobuf-encoding.md`
  - Add a short reference to the negative fixture suite and decoded validation
    boundary.
- `conformance/README.md`
  - Add command documentation for encoding-negative validation.
- `docs/zmeta_refinement_worklog.md`
  - Mark S1-05B status and update D-007.
- `docs/zmeta_refinement_handoff.md`
  - Record S1-05B results and next audit item.

If S1-05B can cover the gateway path using existing gateway APIs rather than
subprocess execution, prefer direct tests for determinism and speed. Keep CLI
tests for the standalone validator and conversion tool boundaries.

## N. Acceptance Criteria for S1-05B

Implementation acceptance criteria:

- strict conformance still passes;
- projection conformance still passes;
- extension registry conformance still passes;
- conformance class validation still passes;
- encoding-negative validator passes the must-fail fixture suites;
- invalid compact bytes fail at the expected stage/reason;
- invalid protobuf bytes fail at the expected stage/reason;
- decoded schema-invalid events fail canonical validation;
- decoded policy-invalid events fail or warn according to documented policy;
- decoded projection-invalid events fail projection validation;
- gateway/CLI paths cannot emit schema-invalid JSON as accepted operational
  events;
- `tools/convert_encoding.py` behavior is documented as decode/convert only
  unless a validation mode is explicitly added;
- no schemas changed;
- semantic contract unchanged;
- extension registry unchanged except optional docs references;
- conformance class manifest unchanged unless S1-05B explicitly updates class
  evidence;
- no new event vocabulary became valid.

Required verification commands for S1-05B should include:

```powershell
python tools\validate_encoding_negative.py --fixtures conformance\encoding-negative
python tools\validate_conformance.py --strict
python tools\validate_conformance.py --strict --profile-projection
python tools\validate_conformance.py --strict --profile-projection --extension-registry
python tools\validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes
python tools\validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative
python -m pytest -q gateway\tests\test_encoding_negative_validation.py gateway\tests\test_compact_negative_decode.py gateway\tests\test_protobuf_negative_decode.py
python -m pytest
git diff --check
```

## O. Risks and Open Questions

Human decisions before S1-05B:

- Whether malformed binary fixtures should be stored as hex, base64, or generated
  dynamically. Recommendation: hex for short parser cases, generated events for
  semantic cases.
- Whether to add `ZMETA-ENCODING-NEGATIVE-VALIDATION` as a new conformance class
  or fold the tests into existing compact/protobuf classes.
- Whether encoding-negative validation should ever become part of default
  `--strict`. Recommendation: keep opt-in until the suite stabilizes.
- How much gateway path coverage is required versus direct codec tests.
- Whether `auto` detection behavior is stable enough for exhaustive negative
  tests, given protobuf has no magic prefix.
- Which policy-invalid binary tests need event-store context versus direct
  policy validator context.
- How to keep protobuf oversize/depth tests small and deterministic.
- Whether unknown compact enum values should be rejected at decode or preserved
  for schema rejection. Recommendation: document and test current behavior first;
  change codec behavior only in a separate implementation decision.

## Recommended Next Work Item

Proceed to S1-05B - Encoding Negative Validation Implementation.

Keep D-007 open until S1-05B implements the suite and S1-05C audits the result.
