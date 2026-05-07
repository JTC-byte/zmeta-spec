# Encoding Negative Validation Fixtures

This directory contains must-fail fixtures for compact CBOR and protobuf
encoding paths. Encodings are wire projections only. A compact or protobuf
packet has no independent semantic authority; it must decode to canonical ZMeta
JSON and then pass the same schema, policy, projection, extension-registry, and
conformance expectations as JSON input.

Run the suite:

```powershell
python tools\validate_encoding_negative.py --compact conformance\encoding-negative\compact-must-fail.jsonl --protobuf conformance\encoding-negative\protobuf-must-fail.jsonl --gateway conformance\encoding-negative\gateway-must-fail.jsonl
```

or through opt-in conformance:

```powershell
python tools\validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative
```

Default strict conformance does not run this suite unless `--encoding-negative`
is passed.

## Fixture Wrapper

Each fixture is a JSON object on one line with:

- `name`
- `description`
- `encoding`: `compact`, `proto`, or `auto`
- `category`: `decode_invalid`, `schema_invalid_after_decode`,
  `policy_invalid_after_decode`, `projection_invalid_after_decode`, or
  `gateway_cli_invalid_after_decode`
- `input_kind`: `hex`, `base64`, `event_json`, `projection_pair`, or
  `generated`
- `bytes_hex` or `bytes_b64` for small malformed binary cases
- `event` for generated semantic invalid cases
- `source` and `projected` for projection pair cases
- `context` for policy/event-store preload context
- `expected_stage`
- `expect_code`
- `expect_message_contains`
- `notes`

Short malformed bytes are stored as hex. Schema, policy, and projection
negative cases keep canonical event JSON visible and let the validator encode
the bytes at runtime. No committed binary blobs are required for this suite.

## Failure Stages

- `decode`: malformed or unsupported binary cannot decode safely.
- `schema`: decoded JSON is not valid for the selected version/profile.
- `policy`: decoded JSON is schema-valid but fails policy.
- `projection`: decoded source/projected pair violates projection preservation.
- `gateway_cli`: gateway or conversion/validation paths reject invalid decoded
  input instead of accepting it as operational output.

## Stable Failure Codes

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

`ENCODE_NEGATIVE_GATEWAY_ACCEPTED_INVALID` and
`ENCODE_NEGATIVE_CONVERT_ACCEPTED_INVALID` are guardrail codes used when a path
unexpectedly accepts invalid decoded data. Normal fixture expectations should
prefer the underlying decode/schema/policy/projection code.

## Policy Context

`context.jsonl` provides named preload event-store context for policy cases such
as lineage parent type mismatch. The context is a fixture harness input only and
does not change schemas or event vocabulary.
