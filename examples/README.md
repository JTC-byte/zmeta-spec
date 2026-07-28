# Examples

JSONL example sets used for validation and interoperability testing.

Common files:
- `zmeta-examples-1.0.jsonl` core v1.0 examples
- `zmeta-profile-L-examples.jsonl`
- `zmeta-profile-M-examples.jsonl`
- `zmeta-profile-H-examples.jsonl`
- `zmeta-command-examples.jsonl` (COMMAND_EVENT + TASK_ACK lifecycle)
- `zmeta-v1.1-examples.jsonl` proposed v1.1.0 extension examples
- `encoding-roundtrip.jsonl` (golden corpus for CBOR/compact/protobuf round-trip tests)
- `zmeta-eo-chain-examples.jsonl` worked EO full chain
  (`OBSERVATION_EVENT -> INFERENCE_EVENT -> FUSION_EVENT -> STATE_EVENT` with
  genuine chained `lineage.based_on` ids; companion to the RF chain in the
  core examples; see `adapters/AUTHORING.md`)

Core examples show the intended event flow:
- RF measurements are `OBSERVATION_EVENT`.
- Classifier output derived from observations is `INFERENCE_EVENT`.
- Track identity is created by `FUSION_EVENT`.
- Operator-facing projection is `STATE_EVENT`.
- Profile L exports compact state/system/command events.
- Deconflicted mission cueing uses `COMMAND_EVENT`.
- Timing and link health use `SYSTEM_EVENT`.

v1.1.0 examples cover SENSOR_STATUS, PLATFORM_STATUS, `data_ref`,
`data_refs`, `error_ellipse_m`, and task-specific command payloads. These are
extension examples and do not loosen v1.0 semantics.

Notes:
- Some examples include optional `payload.data_ref` to illustrate lightweight links
  to locally stored raw data or vectorized artifacts (see Appendix A in
  `spec/semantics-contract.md`).
- TASK_ACK examples include required `metrics.task_id` and `metrics.original_event_id`;
  failure states require `metrics.reason_code` (see `spec/semantics-contract.md`).
- Invalid examples are intentionally kept in `conformance/must-fail.jsonl` so
  runnable example files stay validation-clean.
