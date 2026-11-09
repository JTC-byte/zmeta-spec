## ZMeta to TAK Protocol Version 1 Egress Adapter (Reference)

Overview: see `adapters/README.md`.

TAK Protocol Version 1 is the binary wire form of Cursor-on-Target that TAK
clients and servers exchange on mesh (multicast UDP) and stream (TCP, TLS)
connections: the CoT event as a protobuf `TakMessage`, with the typed parts of
`<detail>` in typed fields and the rest of `<detail>` as XML text in
`xmlDetail`. This adapter encodes the CoT XML that the CoT egress projection
(`adapters/egress/cot/`) produces, under either of its profiles, and frames it
for mesh or stream. It is a wire step, not a second projection: the semantics,
every refusal and both profiles are the CoT adapter's, and this module adds
the encoding, the framing, and a refusal of whatever the encoding cannot carry
without loss.

Input: ZMeta `STATE_EVENT`/`TRACK_STATE` (through `zmeta_to_cot`), or CoT 2.0
XML directly.
Output: TAK Protocol Version 1 bytes, mesh framed by default.

Status: Reference. The encoding was checked byte for byte against the
MIT-licensed `takproto` package (3.0.1) for the known-answer event, and
`takproto` parses the adapter's output of a declared 2-D vessel with no field
mismatch; the recce of 2026-11-03 parsed the same shape back for 809 fielded
and 1,680 live-derived events. No TAK Server or client has been driven with the
bytes from this repository, and the adapter does not open connections. The
adapter is not among the required surfaces of the `ZMETA-COT-PROJECTION`
conformance class, whose surfaces are the CoT XML projection and ingress.

### Usage

```python
from adapters.egress.tak_protocol.zmeta_to_tak_protocol import (
    zmeta_to_tak_protocol, cot_xml_to_tak_message, frame_mesh, frame_stream,
    read_tak_message, validate_framing,
)

cot_config = {"how": "m-f"}                       # the CoT adapter's configuration, passed through
frame = zmeta_to_tak_protocol(state_event, cot_config=cot_config)                    # mesh: bf 01 bf + message
frame = zmeta_to_tak_protocol(state_event, cot_config=cot_config, framing="stream") # bf + varint length + message
message = zmeta_to_tak_protocol(state_event, cot_config=cot_config, framing="none") # the bare TakMessage

message = cot_xml_to_tak_message(cot_xml)         # encode CoT XML from any source, unframed
fields = read_tak_message(frame)                  # a dict of the fields present, for inspection
```

`validate_framing(framing)` returns the name or raises `ValueError`; a gateway
calls it when it reads its configuration, as it calls `validate_cot_config`.
`zmeta_to_tak_protocol` returns `None` for an unknown framing, for every
refusal of the CoT projection, and for an encoding refusal; a caller that
passes a `refusal` dict reads the CoT adapter's `cds` reasons there and
`TAK_PROTOCOL_UNREPRESENTABLE` when the encoding, not the projection, refused.

No protobuf package is used. The encoder is written against the schema below
in the canonical proto3 form: fields in field-number order, a scalar equal to
its default (an empty string, 0, 0.0) written as absent. `takControl` is not
written; it belongs to the connection, not the event.

### The schema this adapter encodes

From the TAK Protocol Version 1 `.proto` files published in the ATAK-CIV
repository; the field numbers were checked against the `takproto` package's
descriptors on 2026-11-09.

| Message | Fields |
|---|---|
| `TakMessage` | `takControl` 1 (not written), `cotEvent` 2 |
| `CotEvent` | `type` 1, `access` 2, `qos` 3, `opex` 4, `uid` 5 (strings); `sendTime` 6, `startTime` 7, `staleTime` 8 (uint64, milliseconds since the epoch); `how` 9 (string); `lat` 10, `lon` 11, `hae` 12, `ce` 13, `le` 14 (doubles); `detail` 15 |
| `Detail` | `xmlDetail` 1 (string); `contact` 2; `group` 3; `precisionLocation` 4; `status` 5; `takv` 6; `track` 7 |
| `Contact` | `endpoint` 1, `callsign` 2 |
| `Group` | `name` 1, `role` 2 (the CoT element is `__group`) |
| `PrecisionLocation` | `geopointsrc` 1, `altsrc` 2 |
| `Status` | `battery` 1 (uint32) |
| `Takv` | `device` 1, `platform` 2, `os` 3, `version` 4 |
| `Track` | `speed` 1, `course` 2 (doubles) |

Framing: `mesh` is the three bytes `bf 01 bf` then the message; `stream` is
`bf`, the message length as a base-128 varint, then the message; `none` is
the bare message.

### Mapping

| CoT XML | TAK Protocol field | Notes |
|---|---|---|
| `event@version` | none | Must be `2.0`, the CoT this schema encodes; any other value, or no version, refuses |
| `event@type`, `@uid` | `type`, `uid` | Required; an empty value refuses |
| `event@access`, `@qos`, `@opex`, `@how` | `access`, `qos`, `opex`, `how` | Carried when present. An empty value refuses: proto3 writes no field for an empty string, so it would read back as absent, and a claim that cannot be told from no claim is not sent |
| `event@time`, `@start`, `@stale` | `sendTime`, `startTime`, `staleTime` | Milliseconds since the epoch, floored; see "What the encoding changes" |
| `point@lat`, `@lon`, `@hae`, `@ce`, `@le` | `lat`, `lon`, `hae`, `ce`, `le` | All five required, as CoT requires them; each must be a finite decimal; `9999999.0`, the CoT unknown-value convention the CoT adapter writes, passes through as that number |
| `detail/contact`, `__group`, `precisionlocation`, `status`, `takv`, `track` | the typed field, or `xmlDetail` | Typed only when the typed message carries the element whole; see the next table |
| every other `detail` child | `xmlDetail` | Serialized as XML text, in document order, concatenated without whitespace |
| any other attribute of `event` or `point`, any other child of `event` | none | Refused; the schema has no field, and the adapter drops nothing in silence |

The typed route. A typed child goes to its typed field only when the typed
message can carry the element whole: every attribute has a typed field, no
attribute is empty, and the element has no text and no child elements.
Otherwise the element travels whole in `xmlDetail`, like every other child, so
a reader that rebuilds `<detail>` from `xmlDetail` sees it as it was written.
The rule exists because the CoT projection writes
`<precisionlocation geopointsrc="…" ellipse_major="…" ellipse_minor="…"
ellipse_angle="…" />` when a position source is configured, and the typed
`PrecisionLocation` message holds `geopointsrc` and `altsrc` only. A typed
carrier would drop the ellipse, the one place the projection carries the
uncertainty's shape rather than its circular bound. A consumer that reads only
the typed `precisionLocation` field sees nothing for such an event; a consumer
that reads `xmlDetail` sees the element whole. The `takproto` package types the
element and drops the ellipse attributes; this adapter does not follow it there.

| Element as the CoT projection writes it | Carrier |
|---|---|
| `<contact callsign="…" />` | typed `contact.callsign` |
| `<__group name="…" role="…" />` (friendly types) | typed `group` |
| `<track course="…" speed="…" />` | typed `track`; `course`, `speed` as doubles |
| `<precisionlocation geopointsrc="…" altsrc="…" />` (no ellipse) | typed `precisionLocation` |
| `<precisionlocation geopointsrc="…" ellipse_major="…" … />` | `xmlDetail`, whole |
| `<remarks>…</remarks>`, `<labels_on …/>`, `<usericon …/>`, `<geo_dimensionality …/>`, `<circle …/>` | `xmlDetail` |
| a typed element with an attribute the message lacks (`<contact callsign="…" phone="…" />`), an empty attribute, text, or children | `xmlDetail`, whole |
| a typed element whose numeric attribute is not a number (`course="east"`, `battery="-1"`, `battery` above 2^32 - 1) | refused |
| two elements of one typed kind | refused; the field holds one, and choosing would drop the other |

### Refusals (`None`): fail closed, never substitute, never drop in silence

| Condition | Disposition |
|---|---|
| Not a `STATE_EVENT`, or anything the CoT projection refuses (missing geo or `track_id`, a non-finite number, a lapsed `cds` validity, and the rest of its table) | refused; inherited |
| Unknown `framing` | refused; `validate_framing` raises at configuration time |
| XML that does not parse, an empty string, a non-string | refused |
| A root element other than `event`; a `version` other than `2.0` | refused |
| A comment or processing instruction anywhere in the document | refused rather than dropped; the parser keeps them so the adapter can see them |
| An attribute of `event` or `point` the schema has no field for; a child of `event` other than `point` and `detail` | refused |
| Text directly inside `event` or `detail`, other than whitespace | refused; the schema has no carrier for it |
| A missing `point`, a missing point attribute, a point value that is not a finite decimal (`nan`, `inf`, `north`) | refused |
| A missing or unparseable `time`, `start` or `stale`; an instant without an offset; an instant before 1970 (no uint64) | refused |
| An empty `access`, `qos`, `opex` or `how`; an empty `type` or `uid` | refused; see the mapping table |
| A typed child whose numeric attribute is not a number; two elements of one typed kind | refused; see the typed route |

### What the encoding changes

| Change | Why it is accepted |
|---|---|
| Times are milliseconds. The CoT projection writes microseconds; the microseconds are dropped, never rounded up | `stale` is never later than the event's claim (contract 4.2: a projection may lower a validity, never raise it); `time` and `start` move by less than one millisecond and never forward |
| `lat`, `lon`, `hae`, `ce`, `le`, `course`, `speed` become float64 | A decimal with more digits than a double holds is rounded to the nearest double; the XML carried the text. The CoT projection writes Python floats, which round-trip exactly |
| A scalar equal to its default is absent on the wire (a coordinate of exactly 0.0, a time at the epoch) | proto3 defines absent as the default, so a reader recovers the same value; the adapter requires the five point attributes, so absence never means "not sent" here |
| The whitespace between detail children is dropped | Formatting, not content |
| The typed children lose their position among the other children | A reader rebuilds `<detail>` from the typed fields and `xmlDetail` separately; CoT gives the children no order |
| `event@version` is not carried | The schema is CoT 2.0; the adapter requires that value |
| `takControl` is not written | A connection negotiation (protocol version range, contact uid), not part of the event; a transport that needs it writes it |

Everything the CoT projection itself loses or changes (confidence in
`remarks`, lineage and timing quality absent, the ellipse reduced to `ce`) is
the CoT adapter's register, unchanged by this encoding.

### The reader

`read_tak_message(data)` reads a mesh frame, a stream frame or a bare message
into a dict of the fields present, nested as the schema nests them
(`{"cotEvent": {"type": …, "detail": {"xmlDetail": …, "contact": {…}}}}`). It
raises `ValueError` for a frame or message the schema does not describe: a
truncated or oversized stream frame, trailing bytes after one, an unknown
field number, a known field with the wrong wire type, a repeated field, a
truncated field, a string that is not UTF-8. That is the rule the repository's
own decoders apply (`DECODE_AMBIGUOUS`, 2026-11-02): a decode that would have
to choose is not a decode. The reader is for tests and inspection; it is not
the proof of the encoder.

### Verification

The tests (`test_tak_protocol_egress.py`) were written before the module and
failed at collection; after the module they pass. What they prove and how:

- A known-answer test holds the expected bytes for one small CoT event,
  computed in the test file from the field numbers and an independent varint
  writer, so the encoder's own tables are not the oracle. Three mutants of the
  encoder were each run against the suite on 2026-11-09 and each failed it:
  the `uid` field number moved (3 failures), the times rounded instead of
  floored (1), the typed route's attribute check removed (2).
- The reader round-trips the known message on both framings, and has its own
  negative controls: an unknown field, a wrong wire type, a truncated stream
  frame each raise.
- Two tests cross-check against `takproto` and run only when the environment
  variable `TAK_PROTO_SITE` names a directory holding `takproto` and
  `google.protobuf`: the mesh and stream bytes for the known event are
  identical to `takproto.xml2proto`'s, and `takproto.parse_mesh` reads the
  adapter's output of a declared 2-D vessel with every checked field equal.
  The repository vendors neither package; without the variable the two tests
  are skipped and say so.
- The shared adapter harness (`tools/validate_adapter_conformance.py`) checks
  emitted ZMeta events, so it does not apply to an egress that emits bytes;
  the colocated tests are the adapter's fixtures, as for the other egress
  adapters.

```
python -m pytest -q adapters/egress/tak_protocol
TAK_PROTO_SITE=<dir holding takproto> python -m pytest -q adapters/egress/tak_protocol
```

### Source

The TAK Protocol Version 1 schema: the `.proto` files in the ATAK-CIV
repository (`commoncommo/core/impl/protobuf/`). The CoT projection it encodes:
`adapters/egress/cot/`. The recce that ranked this adapter first among the
egress candidates and measured the round trips: the repository's private
session record of 2026-11-03.
