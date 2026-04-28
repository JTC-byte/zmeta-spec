# ZMeta v1.1.3 Validation Report

Release: v1.1.3

## Scope

This validation pass covers the v1.1.3 CI compatibility patch:

- Gateway CBOR encode/decode preference order
- Compact CBOR encode/decode preference order
- GitHub Actions Node.js 24 opt-in
- Canonical schema, policy, examples, and conformance fixtures
- Release checksum/signature helper tooling

## Technical Checks

- Gateway CBOR encode/decode prefers `zmeta_cbor` when both `zmeta_cbor` and
  `cbor2` are importable.
- Compact CBOR encode/decode prefers `zmeta_cbor` when both implementations are
  importable.
- The gateway self-test validates examples, the conformance pack, CBOR,
  compact CBOR, and protobuf round trips.
- CI opts JavaScript actions into Node.js 24 with
  `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24=true`.

## Test Results

- Targeted gateway and encoding tests: 30 passed
- Adapter and gateway pytest suite: 220 passed
- Gateway self-test: ok
- Strict examples: 40 passed
- Strict conformance: ok
- Migration compatibility checks for `examples/*.jsonl`: 0 issues
- Release checksum/signature verification: passed
- `git diff --check`: no whitespace errors; Git reported line-ending warnings
  for existing CRLF conversion behavior.

## Contract Hashes

- `schema_hash=3f5f615c1539043f48a612a225421176aace9b3fb3a2507ea43dc31fe5bf1023`
- `policy_hash=70d8dc2b21641e44772e96c28989aa2a93211c2fba1e4c992ea12c8374bb1b16`
- `semantics_hash=bdc3c31e5c206cb667899d06aebf6576a43502af400f6f1e0e15ded65ada367b`
- `contract_hash=4fa2f874f17f15e9af1424672563c3fad32e6dc5a62efda4fa9f692f8f186833`

## Residual Risks

- GitHub-hosted runner warnings can change as GitHub migrates default runtimes;
  this release opts into the runtime GitHub announced for the current
  deprecation path.
- Detached release signatures prove authenticity only if users independently
  trust the documented public key/fingerprint.
