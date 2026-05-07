# Profile Precision Fixtures

This directory contains source/projected fixture pairs for the reference
Profile H/M/L precision policy in `policy/profile-precision.yaml`.

Precision policy is an export/conformance layer. It does not add schema fields,
does not create event vocabulary, and does not change the semantic authority of
the decoded canonical ZMeta JSON event.

Run the suite directly:

```bash
python tools/validate_precision_policy.py --policy policy/profile-precision.yaml --must-pass conformance/profile-precision/must-pass.jsonl --must-fail conformance/profile-precision/must-fail.jsonl
```

Or opt into it through the conformance runner:

```bash
python tools/validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative --precision-policy
```

## Fixture Shape

Each JSONL row is a wrapper, not a ZMeta event. Supported fields:

- `name`
- `description`
- `source_profile`
- `target_profile`
- `policy`
- `source`
- `projected`
- `expect`
- `expect_code`
- `expect_message_contains`
- `roundtrip`
- `packet_budget`
- `notes`

The validator first treats `source` and `projected` as canonical ZMeta JSON and
then checks projection preservation plus profile precision policy. Compact or
protobuf roundtrip requests are decoded back to canonical JSON before checks.

## Stable Failure Codes

- `PRECISION_POLICY_SCHEMA_INVALID_SOURCE`
- `PRECISION_POLICY_SCHEMA_INVALID_PROJECTED`
- `PRECISION_POLICY_POLICY_INVALID_SOURCE`
- `PRECISION_POLICY_POLICY_INVALID_PROJECTED`
- `PRECISION_POLICY_PROJECTION_INVALID`
- `PRECISION_POLICY_IMMUTABLE_CHANGED`
- `PRECISION_POLICY_UNIT_CHANGED`
- `PRECISION_POLICY_PRECISION_INCREASE`
- `PRECISION_POLICY_CONFIDENCE_INCREASE`
- `PRECISION_POLICY_CONFIDENCE_ROUNDING_INVALID`
- `PRECISION_POLICY_TTL_INCREASE`
- `PRECISION_POLICY_TTL_ROUNDING_INVALID`
- `PRECISION_POLICY_ERROR_BOUND_DECREASE`
- `PRECISION_POLICY_ERROR_BOUND_ROUNDING_INVALID`
- `PRECISION_POLICY_UTILITY_FLOOR_VIOLATION`
- `PRECISION_POLICY_COMMAND_GEOMETRY_TOO_COARSE`
- `PRECISION_POLICY_RF_QUANTIZATION_INVALID`
- `PRECISION_POLICY_REQUIRED_FIELD_REMOVED`
- `PRECISION_POLICY_OPTIONAL_OMISSION_NOT_ALLOWED`
- `PRECISION_POLICY_HIDDEN_DEFAULT`
- `PRECISION_POLICY_PACKET_BUDGET_STRIPPED_REQUIRED`
- `PRECISION_POLICY_SOURCE_LIMITED_PRECISION_UNDECLARED`

## Boundaries

Reference defaults require mission review before operational use. Packet budget
pressure can remove only cataloged optional fields and cannot strip required
identity, source, lineage, timing, confidence, track identity, task identity, or
payload discriminator fields.
