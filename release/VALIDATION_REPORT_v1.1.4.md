# ZMeta v1.1.4 Validation Report

Release: v1.1.4

## Scope

This validation pass covers the v1.1.4 release-packaging patch:

- Edge/gateway release bundle contents
- Bundle-local gateway self-test behavior
- Bundle-local gateway/adapters test collection
- Canonical schema, policy, examples, conformance fixtures, and release signing

## Technical Checks

- Edge and gateway bundles include `conformance/`.
- Edge and gateway bundles include `release/sign_release_artifacts.py`.
- Edge and gateway bundles retain `VERSION.txt` set to `v1.1.4`.
- Bundle-local gateway self-tests validate examples, conformance, CBOR, compact
  CBOR, and protobuf round trips.

## Test Results

- Repository adapter and gateway pytest suite: 221 passed
- Targeted release-packaging regression test: passed
- Repository gateway self-test: ok
- Strict examples: 40 passed
- Strict conformance: ok
- Migration compatibility checks for `examples/*.jsonl`: 0 issues
- Downloaded edge bundle self-test: ok
- Downloaded gateway bundle self-test: ok
- Downloaded edge bundle tests: passed
- Downloaded gateway bundle tests: passed
- Release checksum/signature verification: passed
- `git diff --check`: no whitespace errors; Git reported line-ending warnings
  for existing CRLF conversion behavior.

## Contract Hashes

- `schema_hash=3f5f615c1539043f48a612a225421176aace9b3fb3a2507ea43dc31fe5bf1023`
- `policy_hash=70d8dc2b21641e44772e96c28989aa2a93211c2fba1e4c992ea12c8374bb1b16`
- `semantics_hash=bdc3c31e5c206cb667899d06aebf6576a43502af400f6f1e0e15ded65ada367b`
- `contract_hash=4fa2f874f17f15e9af1424672563c3fad32e6dc5a62efda4fa9f692f8f186833`

## Residual Risks

- Docker Desktop/WSL2 runtime verification remains a separate operational check.
- Detached release signatures prove authenticity only if users independently
  trust the documented public key/fingerprint.
