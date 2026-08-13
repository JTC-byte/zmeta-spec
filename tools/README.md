## Tools

### UDP receiver

```
python tools/udp_receiver.py
```

### UDP sender

```
python tools/udp_sender.py --file examples/zmeta-command-examples.jsonl
```

For JSONL files, `udp_sender.py` sends each non-empty line as a separate UDP
datagram.

### Run gateway

```
python tools/run_gateway.py --profile H
```

### Replay JSONL over UDP

```
python tools/replay.py --file examples/zmeta-command-examples.jsonl --delay-ms 200
```

`--loop` re-sends each event exactly as written, including its `event_id`. A
gateway deduplicates on `event_id`, so only the first pass forwards and every
later pass is counted under `duplicates` and dropped. That makes `--loop`
useful for exercising the dedupe path and unsuitable as a load generator:
measured 2026-07-30, cycling a six-event corpus at 200 events/s delivered 17%
of what was sent, and the shortfall was dedupe rather than capacity. A load
generator must mint a fresh `event_id` per event, as a real producer does.

### Convert Encodings

```
python tools/convert_encoding.py --from json --to proto --input event.json --output event.pb
python tools/convert_encoding.py --from proto --to json --input event.pb --output event.json
python tools/convert_encoding.py --from json --to compact --input event.json --output event.zmc
python tools/convert_encoding.py --from auto --to json --input event.zmc --output event.json
```

The conversion tool handles one ZMeta event per invocation. For JSONL input, use
`--allow-jsonl-first` to convert the first non-empty line.

Binary encoding variants:

```
python tools/udp_sender.py --file examples/zmeta-command-examples.jsonl --encoding cbor
python tools/udp_receiver.py --encoding auto
python tools/replay.py --file examples/zmeta-profile-L-examples.jsonl --encoding cbor
python tools/test_gateway_live.py --profile L --encoding cbor --input-encoding cbor
python tools/test_gateway_live.py --profile L --encoding compact --input-encoding compact
python tools/replay.py --file examples/zmeta-profile-L-examples.jsonl --encoding compact
python tools/udp_sender.py --file examples/zmeta-profile-L-examples.jsonl --encoding compact
python tools/udp_receiver.py --encoding compact
python tools/udp_sender.py --file examples/encoding-roundtrip.jsonl --encoding proto
python tools/udp_receiver.py --encoding proto
python tools/replay.py --file examples/encoding-roundtrip.jsonl --encoding proto
python tools/test_gateway_live.py --profile H --encoding proto --input-encoding proto --no-cot
```

CBOR/compact use the built-in deterministic `zmeta_cbor` decoder when
available, with default message, item, container, and nesting limits for
untrusted input. Protobuf uses the experimental pure-Python `zmeta_proto`
projection.

### Compatibility Normalize

```
python tools/compat_normalize.py --input legacy-event.json --output normalized-event.json --report normalize-report.json --allow-version-alias
python tools/compat_normalize.py --input legacy-status.json --output normalized-status.json --report normalize-report.json --convert-endurance-seconds
python tools/compat_normalize.py --input legacy-eo.json --output normalized-eo.json --report normalize-report.json --assume-eo-bbox-roi
```

The compatibility normalizer is non-normative and opt-in. It runs before schema
validation for adapter migration workflows, records every change in a sidecar
report, and leaves strict validation/conformance unchanged. It will not rewrite
immutable event identity, timestamps, event type/subtype, source, lineage, or
track identity. Ambiguous EO `bbox` input is rejected unless the caller
explicitly asserts it is ROI metadata with `--assume-eo-bbox-roi`.

### Validate JSON or JSONL

```
python tools/validate.py --file examples/zmeta-command-examples.jsonl --profile H
```

`validate.py`, `validate_examples.py`, and `validate_conformance.py` use the
canonical version-discriminated schema. Version aliases and legacy fields must
be normalized before validation with `compat_normalize.py` if compatibility mode
is intentionally enabled.

### Check Migration Compatibility

```
python tools/check_compat.py legacy-events.jsonl --target v1.1.24
python tools/check_compat.py legacy-events.jsonl --profile L --policy-dir policy
python tools/check_compat.py legacy-events.jsonl --json
```

`check_compat.py` is migration-oriented. It reports timestamp format issues,
subtype vocabulary mismatches, v1.1-only vocabulary used without
`zmeta_version: "1.1.0"`, missing or degraded timing quality, producer-authority
misses, profile violations, and CoT projection blockers as separate categories.
Use it before strict validation when integrating older producers.

### Filter Accepted-Risk Streams

```
python tools/filter_risk.py --input gateway-output.jsonl --preset display
python tools/filter_risk.py --input gateway-output.jsonl --preset fusion --dropped-output dropped.jsonl
python tools/filter_risk.py --input gateway-output.jsonl --preset command --fail-on-drop
python tools/filter_risk.py --list-presets
```

`filter_risk.py` reads JSONL ZMeta events, evaluates existing
`payload.extensions.risk_adjudication` labels and same-stream
`SYSTEM_EVENT/SCHEMA_VIOLATION` diagnostic metrics, then writes passing events
unchanged. It does not rewrite events, change policy decisions, or make risky
data clean.

Presets are convenience defaults:

- `display`: allows data explicitly usable for display/local awareness, including
  quarantined display paths.
- `fusion`: allows clean or warning-labeled data explicitly usable as
  `FUSION_INPUT`.
- `state`: allows clean or warning-labeled data explicitly usable as
  `STATE_UPDATE`.
- `command`: allows only clean data for `COMMAND_BASIS`.
- `autonomy`: allows only clean data for `AUTONOMY_TASKING`.
- `aar`: allows data usable for after-action review, including quarantine/AAR
  paths.
- `audit`: passes clean, accepted-risk, quarantine, and rejected diagnostic
  events for audit review.

Operators can tune behavior with flags such as `--max-risk`, `--require-use`,
`--allow-dimension`, `--deny-dimension`, `--allow-decision`, and
`--deny-decision`.

### Lint Policy Risk Modes

```
python tools/lint_policy_risk_modes.py
```

`lint_policy_risk_modes.py` flags policy settings that use `ignore` for
material timing, lineage, external-promotion, command, trust, or safety risk.
The reference policy only allows `ignore` for the Profile L unresolved-parent
case, where profile thinning may intentionally leave parent events unavailable
on the link.

It also runs the structural checks on the authorization policy: key names and
value types across `producer_authority` and the whole `routing` block, the
blocks themselves, the entries of every event-type list against the vocabulary
derived from `schema/*.schema.json`, and each document's top-level wrapper key
(which `load_policy` would otherwise unwrap into a permissive default). See
`policy/README.md` for what each check catches and what stays legal.

### Validate All Examples

```
python tools/validate_examples.py
python tools/validate_examples.py --strict
```

### Conformance Pack

```
python tools/validate_conformance.py --strict
python tools/validate_conformance.py --kernel-gate
```

The optional flags validate governed support surfaces without changing default
strict validation. Use the full command above before publishing a release.

Additional focused conformance validators:

```
python tools/validate_bad_events.py --must-fail conformance/bad-events/must-fail.jsonl
python tools/validate_adapter_conformance.py --fixtures conformance/adapter-harness/must-pass.jsonl
```

`validate_bad_events.py` proves dishonest or unsafe semantic examples are not
accepted as clean data. `validate_adapter_conformance.py` calls representative
adapter functions and checks their ZMeta outputs for schema/policy validity,
layer separation, UTC-Z timestamps, lineage, promotion evidence, and exact
output values pinned by per-fixture `expected_values` maps (numeric values
compare within a 1e-6 absolute tolerance; a boolean never matches a
non-boolean, so a `true` pin cannot be satisfied by `1`/`1.0` output).

### Check An Adapter (One Command)

```
python tools/check_adapter.py --events my-adapter-output.jsonl
python tools/check_adapter.py --fixtures my-fixtures.jsonl
python tools/check_adapter.py --events out.jsonl --fixtures f.jsonl --kernel-gate
```

`check_adapter.py` is an advisory wrapper that runs the tool-based steps of
the `adapters/AUTHORING.md` validation ladder in one command: fixture lint
against `conformance/adapter-harness/fixture.schema.json`, `validate.py
--strict`, `check_compat.py` (target defaulting to the release manifest's
release id), the adapter harness, and optionally the full kernel gate.
Colocated adapter pytest (ladder step 1) still runs separately. The governed
validators it delegates to remain the authority; the built-in fixture lint
and empty-input guard are strictly additive (they can add failures, never
mask one). Each underlying command is printed as it runs, and empty events
or fixture files fail rather than passing vacuously.

### Measure packet sizes

```
python tools/measure_packet_size.py --file examples/zmeta-profile-L-examples.jsonl
python tools/measure_packet_size.py --file examples/zmeta-profile-L-examples.jsonl --event-type STATE_EVENT --event-subtype TRACK_STATE
python tools/measure_packet_size.py --file examples/zmeta-profile-L-examples.jsonl --strip payload.data_ref --strip payload.source_summary --strip payload.heading_deg --strip payload.speed_mps
python tools/measure_packet_size.py --file examples/zmeta-profile-L-examples.jsonl --encodings compact --max-bytes 250 --summary-only
```

### Contract Hash

```
python tools/compute_contract_hash.py
```

The reported policy hash covers the active `policy/` directory. Policy examples
under `configs/policy-variants/` are deployment overlays until copied into the
active policy directory. After adopting a variant, recompute hashes and update
any `require_policy_hash` or `require_contract_hash` gate in the deployment
config. Because the current utility hashes the whole active policy directory,
keep deployment-local notes and draft overlays outside `policy/` unless changing
the deployment hash is intentional.

### Release Manifest And Package

```
python tools/build_release_manifest.py --output release/zmeta-release-manifest.yaml
python tools/validate_release_manifest.py --manifest release/zmeta-release-manifest.yaml
python tools/build_release_package.py --manifest release/zmeta-release-manifest.yaml --output-dir release/package-v1.1.24 --release-id zmeta-v1.1.24 --release-state formal_release --no-signatures --release-notes release/RELEASE_NOTES_v1.1.24.md
python tools/validate_release_package.py --manifest release/zmeta-release-manifest.yaml --package-dir release/package-v1.1.24
python tools/validate_release_package.py --manifest release/zmeta-release-manifest.yaml --templates-only
```

Release package tooling is no-signature by default. It does not create git
tags, call signing tools, or store keys/secrets in the repository.

### Deployment simulation

`tools/sim/` holds harnesses that stand up real gateway nodes and push real
traffic through them: `two_node.py` for the wire path and `throughput.py` for
capacity. They answer questions the validators here cannot, because a schema
check cannot tell you that a containerized node is delivering its output to a
loopback nothing can read. See `tools/sim/README.md` for how to run them and
for the rule that keeps them separable. The harnesses are repository
tooling and are not included in the release bundles; run them from a
repository clone.

Everything else on this page defines or enforces the standard. The simulation
harnesses do not, and nothing governed may depend on them. That separation is
asserted by `gateway/tests/test_sim_boundary.py`, so the harnesses stay
extractable into their own repository if they outgrow this one.
