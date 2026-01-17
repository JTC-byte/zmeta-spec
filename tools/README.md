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

### Validate JSON or JSONL

```
python tools/validate.py --file examples/zmeta-command-examples.jsonl --profile H
```
