# Examples

JSONL example sets used for validation and interoperability testing.

Common files:
- `zmeta-examples-1.0.jsonl` core v1.0 examples
- `zmeta-profile-L-examples.jsonl`
- `zmeta-profile-M-examples.jsonl`
- `zmeta-profile-H-examples.jsonl`
- `zmeta-command-examples.jsonl` (COMMAND_EVENT + TASK_ACK lifecycle)

Notes:
- Some examples include optional `payload.data_ref` to illustrate lightweight links
  to locally stored raw data or vectorized artifacts (see Appendix A in
  `spec/semantics-contract.md`).
