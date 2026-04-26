## Tools

### UDP receiver

```
python tools/udp_receiver.py
```

### UDP sender

```
python tools/udp_sender.py --file examples/zmeta-command-examples.jsonl
```

### Run gateway

```
python tools/run_gateway.py --profile H
```

### Replay JSONL over UDP

```
python tools/replay.py --file examples/zmeta-command-examples.jsonl --delay-ms 200
```

CBOR/compact variants:

```
python tools/udp_sender.py --file examples/zmeta-command-examples.jsonl --encoding cbor
python tools/udp_receiver.py --encoding auto
python tools/replay.py --file examples/zmeta-profile-L-examples.jsonl --encoding cbor
python tools/test_gateway_live.py --profile L --encoding cbor --input-encoding cbor
python tools/test_gateway_live.py --profile L --encoding compact --input-encoding compact
python tools/replay.py --file examples/zmeta-profile-L-examples.jsonl --encoding compact
python tools/udp_sender.py --file examples/zmeta-profile-L-examples.jsonl --encoding compact
python tools/udp_receiver.py --encoding compact
```

CBOR/compact require `cbor2` or the built-in `zmeta_cbor` fallback.

### Validate JSON or JSONL

```
python tools/validate.py --file examples/zmeta-command-examples.jsonl --profile H
```

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
