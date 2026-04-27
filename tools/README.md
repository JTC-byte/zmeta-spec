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

CBOR/compact require `cbor2` or the built-in `zmeta_cbor` fallback. Protobuf
uses the experimental pure-Python `zmeta_proto` projection.

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

### Validate All Examples

```
python tools/validate_examples.py
python tools/validate_examples.py --strict
```

### Conformance Pack

```
python tools/validate_conformance.py --strict
```

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
