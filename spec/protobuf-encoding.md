# ZMeta Protobuf Encoding (Experimental)

This document defines an optional protobuf wire projection for ZMeta events.
It is an **experimental encoding**, not a new semantic authority.

Authoritative compliance still comes from:
- `spec/semantics-contract.md`
- `schema/zmeta-event-1.0.schema.json`
- `policy/*.yaml`

## Purpose

Protobuf is useful for service-to-service links, gateway/adaptor integration,
queues, and gRPC-style transports where generated types and compact binary
messages improve interoperability.

Use protobuf when:
- Profile M/H bandwidth matters, but the link is not as constrained as Profile L.
- Producers and consumers benefit from generated envelope types.
- Events are moving across internal services, queues, or gateway pipelines.

Use JSON/JSONL when human inspection, audit logs, or broad tooling compatibility
matter most. Use compact CBOR for Profile L packet budgets.

## Schema Location

The experimental protobuf schema is:

```text
schema/proto/zmeta_event_v1.proto
```

The reference pure-Python codec is:

```text
zmeta_proto.py
```

## Projection Rules

A protobuf-encoded ZMeta event MUST decode to a canonical ZMeta JSON envelope
before semantic validation.

Rules:
- Protobuf does not relax JSON Schema or policy requirements.
- `event_id` remains a UUIDv7 string in the protobuf projection.
- `event.ts` remains the authoritative event time.
- `confidence` is encoded only when present.
- `profile` is encoded only when present.
- Payload is carried as canonical UTF-8 JSON bytes in `payload_json`.
- Consumers MUST validate the decoded JSON event using the normal schema and
  policy pack before applying state, dedupe, command handling, or fusion logic.

The v1 experimental schema intentionally types the stable envelope while keeping
payload flexible. Future schema versions may add typed payload messages once the
field numbers and cross-profile payload shapes are stable.

## Semantic Equivalence

An event is semantically equivalent across JSON, CBOR, compact CBOR, and protobuf
when decoding yields the same ZMeta JSON object for all contract-relevant fields.
Map ordering and protobuf field ordering are not semantic.

Profile projection preservation tests may round-trip projected events through
protobuf and then validate the decoded JSON against schema, policy, and
source/projected projection rules. Protobuf remains an encoding projection; the
decoded JSON event is the validation authority.

Encoding-negative fixtures in `conformance/encoding-negative/` exercise
malformed protobuf wire data and schema-, policy-, projection-, gateway-, and
CLI-invalid decoded JSON. These tests prove protobuf cannot bypass canonical
validation.

Transport metadata outside the event, such as UDP source address or queue topic,
is not part of semantic equivalence.

## Gateway Use

The reference gateway accepts:

```bash
python gateway/src/gateway.py --input-encoding proto --output-encoding json
```

It can also emit protobuf:

```bash
python gateway/src/gateway.py --input-encoding json --output-encoding proto
```

`auto` input detection can decode JSON, CBOR/compact, and protobuf in common
cases, but protobuf does not include a wire-level magic prefix. Prefer explicit
`--input-encoding proto` for production protobuf links.

## Decoder Bounds

The reference `zmeta_proto.loads` decoder enforces default bounds before schema
validation:
- message size: 1 MiB
- length-delimited field size: 512 KiB
- payload JSON size: 512 KiB
- payload JSON nesting depth: 64
- decoded protobuf message nesting depth: 8

Unsupported wire types and invalid field number 0 are rejected. Deployments with
stricter link budgets should pass lower `loads(..., max_*)` values at trust
boundaries.

## Tooling

Measure size:

```bash
python tools/measure_packet_size.py --file examples/encoding-roundtrip.jsonl --encodings json,cbor,compact,proto
```

Convert between encodings:

```bash
python tools/convert_encoding.py --from json --to proto --input event.json --output event.pb
python tools/convert_encoding.py --from proto --to json --input event.pb --output event.json
```

Send and receive UDP:

```bash
python tools/udp_sender.py --file examples/encoding-roundtrip.jsonl --encoding proto
python tools/udp_receiver.py --encoding proto
```

Replay:

```bash
python tools/replay.py --file examples/encoding-roundtrip.jsonl --encoding proto
```

## Versioning

This protobuf schema is experimental and is not included in the locked v1.0
contract hash. Breaking changes are possible until protobuf encoding is promoted
to a normative or stable reference encoding in a future release.

Once promoted, field numbers must be treated as permanent and compatibility
rules must reserve removed fields instead of reusing them.
