# S1-05C Encoding Negative Validation Audit

Status: COMPLETE
Date: 2026-05-07
Scope: Post-implementation audit of S1-05B. No schemas, semantic contract text,
extension registry artifacts, codecs, gateway runtime behavior, adapters,
policy files, release hashes, or event vocabulary were changed.

## Summary

S1-05B implemented encoding-negative validation for compact CBOR and protobuf
invalid-after-decode paths. The implementation added fixture suites under
`conformance/encoding-negative/`, a standalone validator CLI, focused pytest
coverage, optional `tools/validate_conformance.py --encoding-negative`
integration, documentation updates, and strengthened conformance-class evidence
for `ZMETA-COMPACT-CBOR` and `ZMETA-PROTOBUF-PROJECTION`.

This audit confirms the implementation preserves the central encoding rule:
compact CBOR and protobuf are wire projections only. They do not carry
independent semantic authority. Decoded canonical JSON remains the object that
schema, profile, policy, projection, gateway, extension-registry, and
conformance-class checks evaluate.

## Files Inspected

- S1-05B commit diff: `367969a`
- `docs/s1_05_encoding_negative_validation_plan.md`
- `tools/validate_encoding_negative.py`
- `conformance/encoding-negative/README.md`
- `conformance/encoding-negative/context.jsonl`
- `conformance/encoding-negative/compact-must-fail.jsonl`
- `conformance/encoding-negative/protobuf-must-fail.jsonl`
- `conformance/encoding-negative/gateway-must-fail.jsonl`
- `gateway/tests/test_encoding_negative_validation.py`
- `gateway/tests/test_compact_negative_decode.py`
- `gateway/tests/test_protobuf_negative_decode.py`
- `tools/validate_conformance.py`
- `tools/convert_encoding.py`
- `zmeta_compact.py`
- `zmeta_cbor.py`
- `zmeta_proto.py`
- `gateway/src/gateway.py`
- `gateway/src/validators.py`
- `spec/compact-binary-mapping.md`
- `spec/protobuf-encoding.md`
- `spec/semantics-contract.md`
- `schema/README.md`
- `schema/zmeta-event.schema.json`
- `schema/zmeta-event-1.0.schema.json`
- `schema/zmeta-event-1.1.0.schema.json`
- `schema/proto/zmeta_event_v1.proto`
- `policy/*.yaml`
- `tools/validate.py`
- `tools/validate_projection.py`
- `tools/validate_extension_registry.py`
- `tools/validate_conformance_classes.py`
- `conformance/conformance_classes.yaml`
- `conformance/claims/example-reference-gateway.yaml`
- `conformance/claims/example-core-producer.yaml`
- `spec/conformance-classes.md`
- `spec/extension-registry.md`
- `spec/extension-registry.yaml`
- `conformance/README.md`
- `docs/zmeta_refinement_worklog.md`
- `docs/zmeta_refinement_handoff.md`
- `docs/s1_02c_projection_preservation_audit.md`
- `docs/s1_03c_extension_registry_audit.md`
- `docs/s1_04c_conformance_class_manifest_audit.md`
- Existing encoding, gateway, and conformance tests under `gateway/tests/`

## Files Changed During S1-05C

- Created `docs/s1_05c_encoding_negative_validation_audit.md`
- Updated `docs/zmeta_refinement_worklog.md`
- Updated `docs/zmeta_refinement_handoff.md`

No validator, fixture, schema, policy, codec, gateway runtime, adapter, or
conformance manifest logic was changed during the audit.

## Drift Checks

Schema drift: none. The following files remain unchanged during S1-05B/S1-05C:

- `schema/zmeta-event.schema.json`
- `schema/zmeta-event-1.0.schema.json`
- `schema/zmeta-event-1.1.0.schema.json`

Semantic contract drift: none. `spec/semantics-contract.md` remains unchanged.

Extension registry drift: none. `spec/extension-registry.yaml` and
`spec/extension-registry.md` remain unchanged.

New vocabulary check: no new event vocabulary became valid. v1.1.0 concepts were
not promoted, v1.1.0 vocabulary is still rejected under `zmeta_version: "1.0"`,
and reserved/future concepts remain invalid current vocabulary.

## Fixture Format Review

`conformance/encoding-negative/README.md` documents the wrapper fields required
by the S1-05B prompt:

- `name`
- `description`
- `encoding`
- `category`
- `input_kind`
- `bytes_hex`
- `bytes_b64`
- `event`
- `source`
- `projected`
- `context`
- `expected_stage`
- `expect_code`
- `expect_message_contains`
- `notes`

The suite uses deterministic JSONL fixtures. Short parser-level malformed inputs
are stored as hex. Schema, policy, projection, and gateway cases keep canonical
event JSON visible and generate encoded bytes at runtime. No large binary blobs
were added.

Fixture counts:

- Total: 49
- Compact: 20
- Protobuf: 21
- Gateway/CLI: 8

Categories:

- `decode_invalid`
- `schema_invalid_after_decode`
- `policy_invalid_after_decode`
- `projection_invalid_after_decode`
- `gateway_cli_invalid_after_decode`

## Validator Behavior Review

`tools/validate_encoding_negative.py` satisfies the expected behavior:

- Loads compact, protobuf, and gateway JSONL fixture files.
- Fails if required fixture files are missing.
- Materializes bytes from hex, base64, generated compact/protobuf events, and
  projection pairs.
- Decodes compact/protobuf where applicable.
- Validates decoded events through canonical schema/profile checks.
- Validates policy-invalid cases through existing policy validators and fixture
  context.
- Validates projection-invalid pairs through the existing projection validator
  after round-trip decode.
- Maps failures to stable expected stages and reason codes.
- Rejects unexpected passes and unexpected failure code/stage mismatches.
- Returns nonzero on unexpected results.
- Supports `--quiet`.
- Treats decoded canonical JSON as the semantic object and never treats raw
  compact/protobuf bytes as semantic authority.

The validator uses stable guardrail codes for unexpected accepted invalid input:
`ENCODE_NEGATIVE_GATEWAY_ACCEPTED_INVALID` and
`ENCODE_NEGATIVE_CONVERT_ACCEPTED_INVALID`. Normal fixtures use more specific
decode/schema/policy/projection codes.

## Failure Code Review

All required S1-05B failure codes are present and used:

- `ENCODE_NEGATIVE_MALFORMED_CBOR`
- `ENCODE_NEGATIVE_MALFORMED_COMPACT`
- `ENCODE_NEGATIVE_UNSUPPORTED_COMPACT_VERSION`
- `ENCODE_NEGATIVE_INVALID_COMPACT_SHAPE`
- `ENCODE_NEGATIVE_INVALID_COMPACT_ENUM`
- `ENCODE_NEGATIVE_INVALID_UUID_BYTES`
- `ENCODE_NEGATIVE_MALFORMED_PROTOBUF`
- `ENCODE_NEGATIVE_UNSUPPORTED_PROTOBUF_WIRE_TYPE`
- `ENCODE_NEGATIVE_INVALID_PROTOBUF_FIELD`
- `ENCODE_NEGATIVE_PROTOBUF_OVERSIZE`
- `ENCODE_NEGATIVE_PAYLOAD_JSON_OVERSIZE`
- `ENCODE_NEGATIVE_PAYLOAD_JSON_TOO_DEEP`
- `ENCODE_NEGATIVE_INVALID_UTF8`
- `ENCODE_NEGATIVE_PAYLOAD_NOT_OBJECT`
- `ENCODE_NEGATIVE_SCHEMA_INVALID_DECODED`
- `ENCODE_NEGATIVE_POLICY_INVALID_DECODED`
- `ENCODE_NEGATIVE_PROJECTION_INVALID_DECODED`
- `ENCODE_NEGATIVE_RESERVED_VOCAB_LEAK`
- `ENCODE_NEGATIVE_V1_1_LEAK_TO_V1_0`
- `ENCODE_NEGATIVE_GATEWAY_ACCEPTED_INVALID`
- `ENCODE_NEGATIVE_CONVERT_ACCEPTED_INVALID`

Fixtures use specific codes where practical. Generic accepted-invalid codes are
reserved for harness failures and are not used to hide normal expected failure
causes.

## Compact Coverage Review

Compact fixtures cover:

- malformed CBOR;
- unsupported compact version;
- invalid compact map shape;
- invalid event type enum;
- invalid event subtype enum;
- invalid profile enum;
- invalid UUID byte length;
- missing required top-level maps;
- missing required STATE_EVENT fields;
- Profile L carrying OBSERVATION_EVENT;
- Profile L carrying FUSION_EVENT;
- STATE_EVENT missing confidence;
- STATE_EVENT missing lineage;
- command altitude-like field after expansion;
- decoded UUIDv4 event identity;
- decoded non-UTC timestamp;
- decoded reserved RADAR vocabulary under v1.0;
- producer-authority policy failure;
- lineage parent type mismatch policy failure;
- compact decoded projection-invalid confidence increase.

Unknown compact enum behavior is tested against the current codec design:
unknown values survive decode and fail canonical schema/profile validation rather
than becoming new vocabulary.

## Protobuf Coverage Review

Protobuf fixtures cover:

- malformed wire bytes;
- invalid field number 0;
- unsupported wire type;
- oversized message;
- oversized payload JSON;
- excessive payload JSON nesting;
- invalid UTF-8 payload JSON;
- payload JSON not object;
- decoded JSON missing required envelope fields;
- decoded UUIDv4 event identity;
- decoded timestamp lacking trailing `Z`;
- wrong `zmeta_version`;
- v1.1-only `SENSOR_STATUS` under `zmeta_version: "1.0"`;
- reserved/future vocabulary: RADAR, PNT_STATUS, UAS_IDENTITY, and
  EMERGENCY_L0_PROFILE;
- producer-authority policy failure;
- command-origin policy failure;
- lineage parent type mismatch policy failure;
- protobuf decoded projection-invalid TTL increase.

The size/depth fixtures use small deterministic payloads and low decode limits
instead of large committed binary blobs.

## Policy-Invalid Coverage Review

Stable policy-invalid-after-decode coverage includes:

- producer unauthorized for event type;
- command origin unauthorized;
- lineage parent type mismatch.

The S1-05A plan also listed command deconfliction, unresolved lineage rejection
under M/H context, stale timing status warning/rejection, and RF window midpoint
mismatch as possible policy-context cases. Those are not added in S1-05B because
the implemented cases already prove the encoding-negative harness routes decoded
events through policy validation, while the remaining examples are policy-surface
expansions rather than encoding-layer bypass risks. They can be added later if
maintainers want more policy-specific fixture breadth.

## Projection-Invalid Coverage Review

Encoding-negative projection fixtures include:

- compact decoded schema-valid but projection-invalid confidence increase;
- protobuf decoded schema-valid but projection-invalid TTL increase.

Broader projection invariants, including precision increase, unit change, source
rewrite, track ID rewrite, lineage deletion, same-ID observation-to-state
collapse, and same-ID inference-to-state collapse, remain covered by the S1-02
projection preservation suite. S1-05B correctly focuses on proving encoded input
is decoded to canonical JSON before projection validation. It does not duplicate
the full S1-02 invariant matrix for every encoding.

## Gateway and CLI Coverage Review

Gateway/CLI fixtures cover:

- explicit compact gateway rejection;
- explicit protobuf gateway rejection;
- policy-invalid compact gateway rejection;
- policy-invalid protobuf gateway rejection;
- conversion-path rejection for malformed compact bytes;
- conversion output followed by canonical rejection for protobuf schema-invalid
  decoded JSON;
- stable auto-detection rejection for compact bytes;
- stable auto-detection rejection for protobuf bytes.

The audit confirms invalid decoded JSON is not accepted as operational gateway
output. `tools/convert_encoding.py` remains a decode/convert tool rather than a
semantic validator; S1-05B tests document and enforce the boundary by validating
converted decoded JSON through canonical validation when semantics are invalid.

## Conformance Integration Review

`tools/validate_conformance.py --encoding-negative` is opt-in. Default
`python tools/validate_conformance.py --strict` behavior remains unchanged.

The encoding-negative flag can run independently of conformance-class validation
and also combines successfully with:

- `--profile-projection`
- `--extension-registry`
- `--conformance-classes`

Missing fixture files are not silently skipped because the standalone validator
opens required fixture paths explicitly and raises on missing paths.

## Conformance-Class Impact Review

S1-05B strengthened existing class evidence rather than adding a new class:

- `ZMETA-COMPACT-CBOR` now references compact encoding-negative fixtures and
  the encoding-negative validator command.
- `ZMETA-PROTOBUF-PROJECTION` now references protobuf encoding-negative fixtures
  and the encoding-negative validator command.
- `conformance/claims/example-reference-gateway.yaml` records the new test
  evidence for claimed compact/protobuf classes.
- `conformance/claims/example-core-producer.yaml` does not overclaim encoding,
  gateway, adapter, or projection classes.

The conformance-class validator passes for both the manifest and the example
claims. D-008 remains closed.

## Documentation Review

The updated docs state that compact/protobuf remain encoding projections only,
decoded canonical JSON remains authoritative, encoding-negative validation is
opt-in, and no schemas or vocabulary changed:

- `conformance/README.md`
- `spec/compact-binary-mapping.md`
- `spec/protobuf-encoding.md`
- `spec/conformance-classes.md`
- `docs/zmeta_refinement_worklog.md`
- `docs/zmeta_refinement_handoff.md`

## Verification

Required commands passed:

```powershell
python tools\validate_encoding_negative.py --compact conformance\encoding-negative\compact-must-fail.jsonl --protobuf conformance\encoding-negative\protobuf-must-fail.jsonl --gateway conformance\encoding-negative\gateway-must-fail.jsonl
python tools\validate_conformance.py --strict
python tools\validate_conformance.py --strict --profile-projection
python tools\validate_conformance.py --strict --profile-projection --extension-registry
python tools\validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes
python tools\validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative
python tools\validate_conformance_classes.py --manifest conformance\conformance_classes.yaml
python tools\validate_conformance_classes.py --manifest conformance\conformance_classes.yaml --claims conformance\claims\example-reference-gateway.yaml conformance\claims\example-core-producer.yaml
python -m pytest -q gateway\tests\test_encoding_negative_validation.py gateway\tests\test_compact_negative_decode.py gateway\tests\test_protobuf_negative_decode.py
python -m pytest
git diff --check
```

Results:

- Encoding-negative validator: `encoding negative ok total=49`
- Focused encoding-negative pytest: `22 passed`
- Full pytest: `295 passed`
- `git diff --check`: passed with CRLF conversion warnings only

## D-007 Closure Recommendation

D-007 can be closed. The remaining encoding-layer hardening gap is addressed:
compact/protobuf decode failures, decoded schema-invalid events, stable
policy-invalid events, decoded projection-invalid pairs, and gateway/CLI
invalid-after-decode paths are covered by deterministic fixtures, a standalone
validator, focused tests, and opt-in conformance integration.

The remaining policy examples not implemented in S1-05B are not blockers for
D-007 closure because they are additional policy-surface breadth, not evidence
that encoded data can bypass canonical validation.

## Remaining Open Issues

- D-010 remains open: Profile Precision / Quantization Policy Floors.
- D-011 remains open: Crosswalk TAKEOFF Mention Cleanup.
- D-002 remains open: Contract Hash / Release Hash Follow-Up.
- D-003 and D-004 remain open for future versioned semantics and companion
  artifacts.

## Recommended Next Work Item

Proceed to S1-06A - Profile Precision / Quantization Policy Floors Plan Only.
